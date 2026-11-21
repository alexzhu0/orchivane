/** DSH host extension: one controller-owned shell, plus real next-step steering. */
import net from 'node:net';
import Schema from '../../npm-runtime/node_modules/@deepseek-ai/schemastery/lib/index.mjs';
import { createUserMessage } from '../../npm-runtime/node_modules/@deepseek-ai/dsh-llm/lib/index.js';
import { defineTool } from '../../npm-runtime/node_modules/@deepseek-ai/dsh-tools/lib/index.js';

export const name = 'orchivane-study';
export const inject = ['tools', 'agents'];
export const Config = Schema.object({ socketPath: Schema.string().required(), token: Schema.string().required() });
const MAX_BYTES = 1024 * 1024;

/** One bounded NDJSON request per connection; no shared response/routing state. */
export function exchange(socketPath, request, signal, timeoutMs = 45000) {
  return new Promise((resolve, reject) => {
    signal?.throwIfAborted();
    const socket = net.createConnection({ path: socketPath });
    let buffer = Buffer.alloc(0), settled = false;
    const finish = (error, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      clearTimeout(connectTimer);
      signal?.removeEventListener('abort', abort);
      socket.destroy();
      if (error) reject(error); else resolve(result);
    };
    const abort = () => finish(new Error('study bridge aborted'));
    const timer = setTimeout(() => finish(new Error('study bridge deadline exceeded')), timeoutMs);
    const connectTimer = setTimeout(() => finish(new Error('study bridge connection deadline exceeded')), Math.min(15000, timeoutMs));
    signal?.addEventListener('abort', abort, { once: true });
    socket.once('error', error => finish(error));
    socket.once('connect', () => {
      clearTimeout(connectTimer);
      const payload = JSON.stringify(request) + '\n';
      if (Buffer.byteLength(payload) > MAX_BYTES) return finish(new Error('study bridge request too large'));
      socket.write(payload);
    });
    socket.on('data', chunk => {
      buffer = Buffer.concat([buffer, chunk]);
      if (buffer.length > MAX_BYTES) return finish(new Error('study bridge response too large'));
      const end = buffer.indexOf(10);
      if (end < 0) return;
      try {
        const result = JSON.parse(buffer.subarray(0, end).toString('utf8'));
        if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('invalid study bridge response');
        if (result.ok !== true || result.error) throw new Error(String(result.error || 'study bridge request rejected'));
        finish(null, result);
      } catch (error) { finish(error); }
    });
    socket.once('end', () => finish(new Error('study bridge closed before response')));
  });
}

export function apply(ctx, config) { return install(ctx, config); }

/** Test seam substitutes transport only; production always uses the Unix socket. */
export function install(ctx, config, transport = exchange) {
  const outcomes = new WeakMap();
  const state = new WeakMap();
  const rpc = (request, signal, timeoutMs) => transport(config.socketPath, { ...request, token: config.token }, signal, timeoutMs);
  ctx.tools.register(defineTool({
    name: 'study_bash',
    description: 'Run one bash command in the isolated task directory. Files persist; shell state does not. Use python3 for Python. Submit exactly one tool call per model step. Network and files outside the task and permitted system runtime are unavailable. Keep command output small.',
    parameters: { command: { type: 'string', required: true } },
    output: {
      schema: { type: 'object', additionalProperties: false, properties: {
        stdout: { type: 'string', required: true },
        stderr: { type: 'string', required: true },
        exit_code: { type: 'integer', required: true },
      } },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value) }],
    },
    async execute(args, exec) {
      const current = state.get(exec.agent);
      if (!current) throw new Error('study agent was not initialized');
      const identity = { session_id: String(exec.agent.session.id), call_id: String(exec.callId), turn: current.turn, step: current.step };
      if (current.pending) {
        await rpc({ op: 'invalid', ...identity, reason: 'tool_before_steering_consumed' }, exec.signal, 15000);
        throw new Error('Requirement change must be consumed at the next model step before another tool call');
      }
      const response = await rpc({ op: 'execute', ...identity, command: args.command }, exec.signal);
      if (typeof response.stdout !== 'string' || typeof response.stderr !== 'string' || !Number.isSafeInteger(response.exit_code)) throw new Error('invalid study shell outcome');
      if (response.steering !== undefined) {
        if (typeof response.steering?.text !== 'string' || !response.steering.text) throw new Error('invalid study steering');
        outcomes.set(exec, { text: response.steering.text, identity });
      }
      // Steering is privileged host data, never a canonical tool-output field.
      return { stdout: response.stdout, stderr: response.stderr, exit_code: response.exit_code };
    },
  }));
  // Guard remains authoritative even if a later plugin registers another tool.
  ctx.tools.guard(exec => exec.name === 'study_bash' ? undefined : 'Only study_bash is available in this experiment');
  ctx.on('agent/created', async ({ agent, signal }) => {
    const current = { turn: 0, step: 0, pending: null };
    state.set(agent, current);
    const dispose = agent.ctx.effect(() => {
      agent.ctx.tools.restrict({ allow: ['study_bash'] });
      agent.ctx.on('session/event', (session, event) => {
        if (session !== agent.session) return;
        if (event.type === 'step/start') { current.turn = event.data.turn; current.step = event.data.step; }
        if (event.type === 'user/message' && event.data.id === current.pending) current.pending = null;
      });
      return () => state.delete(agent);
    });
    ctx.effect(() => dispose);
    const tools = agent.ctx.tools.schemas(agent).map(tool => tool.name).sort();
    if (tools.length !== 1 || tools[0] !== 'study_bash') throw new Error('Unexpected model tool inventory');
    await rpc({ op: 'ready', session_id: String(agent.session.id), tools }, signal, 15000);
  });
  ctx.on('tools/post-execute', async (exec, _result, next) => {
    const decision = await next();
    const outcome = outcomes.get(exec);
    if (!outcome) return decision;
    outcomes.delete(exec);
    if (decision.kind !== 'accept') throw new Error('Study checkpoint result was blocked');
    exec.signal.throwIfAborted();
    const message = createUserMessage({ content: [{ type: 'text', text: outcome.text }], source: { kind: 'user' } });
    state.get(exec.agent).pending = message.id;
    exec.agent.steer(message);
    await rpc({ op: 'steered', ...outcome.identity, message_id: String(message.id) }, exec.signal, 15000);
    return decision;
  });
}
