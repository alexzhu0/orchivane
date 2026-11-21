/** Actual installed DSH AgentLoop, fake model, no shell, API, key, or sandbox escape. */
import assert from 'node:assert/strict';
import { Context } from '../../npm-runtime/node_modules/@deepseek-ai/cordis/lib/index.js';
import LlmRuntime, { LlmAdapter, createUserMessage } from '../../npm-runtime/node_modules/@deepseek-ai/dsh-llm/lib/index.js';
import AgentRegistry from '../../npm-runtime/node_modules/@deepseek-ai/dsh-agent/lib/index.js';
import AgentLoop from '../../npm-runtime/node_modules/@deepseek-ai/dsh-agent-loop/lib/index.js';
import SessionStore from '../../npm-runtime/node_modules/@deepseek-ai/dsh-session/lib/index.js';
import SessionProjections from '../../npm-runtime/node_modules/@deepseek-ai/dsh-session-projection/lib/index.js';
import SystemPrompt from '../../npm-runtime/node_modules/@deepseek-ai/dsh-system-prompt/lib/index.js';
import Tools, { defineTool } from '../../npm-runtime/node_modules/@deepseek-ai/dsh-tools/lib/index.js';
import * as Study from '../runtime/study-plugin.mjs';

const CHANGE = 'CHANGED: immutable snapshot pagination';
const requests = [], rpcCalls = [], events = [];
const multiple = process.argv.includes('--multiple');
const continueAfterChange = process.argv.includes('--continue');
let acknowledgementSettled = false;
async function bridge(_socket, request) {
  assert.equal(request.token, 'probe-token');
  rpcCalls.push(request);
  if (request.op === 'execute') return { ok: true, stdout: 'checkpoint', stderr: '', exit_code: 0, ...(rpcCalls.filter(call => call.op === 'execute').length === 1 ? { steering: { text: CHANGE } } : {}) };
  if (request.op === 'steered') { await Promise.resolve(); acknowledgementSettled = true; }
  return { ok: true };
}
const ctx = new Context();
class FakeModel extends LlmAdapter {
  async *stream(request) {
    requests.push(request);
    if (requests.length > 1) assert(acknowledgementSettled, 'Model request raced ahead of host steering acknowledgement');
    assert.deepEqual(request.tools.map(tool => tool.name), ['study_bash']);
    const usesTool = requests.length === 1 || continueAfterChange && requests.length === 2;
    const blocks = usesTool
      ? [{ type: 'tool-call', id: 'probe-call-' + requests.length, name: 'study_bash', arguments: '{"command":"checkpoint"}' }]
      : [{ type: 'text', text: 'Handled the changed requirement in the same turn.' }];
    if (multiple && requests.length === 1) blocks.push({ type: 'tool-call', id: 'forbidden-second-call', name: 'study_bash', arguments: '{"command":"must not run"}' });
    for (const [index, block] of blocks.entries()) {
      yield { type: 'block-start', index, blockType: block.type };
      yield { type: 'block-end', index, block };
    }
    yield { type: 'finish', reason: { kind: usesTool ? 'tool-calls' : 'stop' } };
  }
}
try {
  await ctx.plugin(SessionStore);
  await ctx.plugin(SessionProjections);
  await ctx.plugin(SystemPrompt, { includeRuntimeContext: false, includeHarnessIdentity: false });
  await ctx.plugin(Tools);
  await ctx.plugin(LlmRuntime);
  await ctx.plugin(AgentRegistry);
  await ctx.plugin(AgentLoop, { agents: [], maxParallelToolCalls: 1 });
  ctx.llm.registerAdapter(['probe'], new FakeModel());
  // A forbidden tool exists globally; the plugin must remove its schema and deny execution.
  ctx.tools.register(defineTool({ name: 'forbidden_tool', description: 'Must be invisible', parameters: {}, output: { schema: { type: 'string' }, render: () => [] }, async execute() { throw new Error('Forbidden tool ran'); } }));
  await ctx.plugin({ name: 'study-probe', inject: Study.inject, apply: context => Study.install(context, { socketPath: '/unused/probe.sock', token: 'probe-token' }, bridge) });
  ctx.on('session/event', (_session, event) => events.push(event));
  const handle = await ctx.agents.create({ sessionId: 'probe-session', agentOptions: { provider: 'probe', model: 'fake' } });
  handle.agent.followup(createUserMessage({ content: [{ type: 'text', text: 'Implement old pagination.' }], source: { kind: 'user' } }));
  await handle.agent.whenIdle();
  assert.equal(requests.length, continueAfterChange ? 3 : 2, 'Actual DSH model requests must run');
  assert(!JSON.stringify(requests[0].messages).includes(CHANGE), 'Future change leaked into first request');
  const changed = requests[1].messages.find(message => message.role === 'user' && message.content.some(block => block.text === CHANGE));
  assert(changed, 'Second request must contain the logged change as a user message');
  const starts = events.filter(event => event.type === 'step/start');
  assert.deepEqual(starts.map(event => [event.data.turn, event.data.step]), continueAfterChange ? [[1, 1], [1, 2], [1, 3]] : [[1, 1], [1, 2]]);
  assert.equal(events.filter(event => event.type === 'turn/start').length, 1);
  const steered = rpcCalls.find(call => call.op === 'steered');
  assert.equal(changed.id, steered.message_id);
  assert.equal(steered.turn, 1); assert.equal(steered.step, 1);
  assert.equal(events.filter(event => event.type === 'user/message' && event.data.id === steered.message_id).length, 1);
  const ops = ['ready', 'execute', 'steered'];
  if (multiple) ops.push('invalid');
  if (continueAfterChange) ops.push('execute');
  assert.deepEqual(rpcCalls.map(call => call.op), ops);
  assert(events.some(event => event.type === 'agent/inbox/spliced' && event.data.target === 'next-step' && event.data.inserted.some(message => message.id === changed.id)));
  assert(!events.filter(event => event.type === 'tool/result').some(event => JSON.stringify(event.data).includes(CHANGE)), 'Steering leaked into tool-output field');
  const denied = await ctx.tools.execute({ name: 'forbidden_tool', arguments: {}, callId: 'denied-call', agent: handle.agent, signal: new AbortController().signal });
  assert.equal(denied.isError, true);
  await handle.dispose();
  console.log(JSON.stringify({ passed: true, model: 'fake', transport: 'in-memory', actual_dsh_agent_loop: true, turns: 1, steps: requests.length, changed_message_in_next_request: true, tool_inventory: ['study_bash'], forbidden_tool_denied: true, same_batch_followon_blocked: multiple, tool_after_consumption_runs: continueAfterChange }));
} finally {
  await ctx.fiber.dispose();
}
