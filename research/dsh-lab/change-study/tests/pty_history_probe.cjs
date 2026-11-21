// Explicit local diagnostic: real PTY, no DSH launch or model/API calls.
// Reads the project's actual overlay; removing +H must fail configured_passed.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {pathToFileURL} = require('node:url');
const lab = path.resolve(__dirname, '../..');
const pty = require(path.join(lab, 'npm-runtime/node_modules/node-pty'));
const python = path.join(lab, '.venv-dsh/bin/python');
const quote = value => "$'" + value.replaceAll('\\', '\\\\').replaceAll("'", "\\'").replaceAll('\r', '\\r').replaceAll('\n', '\\n') + "'";
const shellQuote = value => "'" + value.replaceAll("'", "'\\''") + "'";

async function probe(shellArgs) {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'orchivane-history-probe-'));
  const marker = path.join(cwd, 'completed.txt');
  const command = `${shellQuote(python)} - <<'PY'\nfrom pathlib import Path\nvalue = 7\nPath('completed.txt').write_text(f"{value!r}")\nprint(f"{value!r}")\nPY\n`;
  const wrapped = `printf '%s\\n' __PROBE_START__; eval -- ${quote(command)}; __probe_status=$?; printf '%s%s\\n' __PROBE_END__: "$__probe_status"`;
  return new Promise((resolve, reject) => {
    let terminal, state = 0, output = '', outcome, done = false;
    const timer = setTimeout(() => finish('timeout'), 6000);
    function finish(reason) {
      if (done) return;
      done = true;
      clearTimeout(timer);
      outcome = {
        reason,
        marker_written: fs.existsSync(marker) && fs.readFileSync(marker, 'utf8') === '7',
        end_marker: output.includes('__PROBE_END__:0'),
        history_error: output.includes('event not found'),
      };
      if (terminal) terminal.kill();
      // This command cannot leave child work after a normal marker/history error.
      fs.rmSync(cwd, {recursive: true, force: true});
      resolve(outcome);
    }
    try {
      terminal = pty.spawn('/bin/bash', shellArgs, {
        name: 'xterm', cols: 80, rows: 24, cwd,
        env: {PATH: process.env.PATH, PS1: 'dsh> ', PROMPT_COMMAND: 'printf "\\033]133;D;%s\\007" "$?"; PS1="dsh> "'},
      });
      terminal.onData(chunk => {
        output += chunk;
        if (state === 0 && output.includes('dsh> ')) {
          state = 1; output = ''; terminal.write('stty -echo\r');
        } else if (state === 1 && output.includes('dsh> ')) {
          state = 2; output = ''; terminal.write(wrapped + '\r');
        } else if (state === 2 && output.includes('event not found')) {
          finish('history_expansion');
        } else if (state === 2 && output.includes('__PROBE_END__:0')) {
          finish('completed');
        }
      });
      terminal.onExit(() => finish('shell_exit'));
    } catch (error) {
      clearTimeout(timer);
      fs.rmSync(cwd, {recursive: true, force: true});
      reject(error);
    }
  });
}

(async () => {
  const boot = await import(pathToFileURL(path.join(lab, 'npm-runtime/node_modules/@deepseek-ai/dsh-app-boot/lib/index.js')).href);
  const original = boot.loadOverlayPatches('dsh', path.join(lab, 'npm-runtime/node_modules/@deepseek-ai/dsh-sdk-minimal/cordis.patch.yml'));
  const overlay = boot.loadOverlayPatches('dsh', path.resolve(__dirname, '../shell-history.patch.yml'));
  const warnings = [];
  const rows = boot.composeEntries([original, overlay], warning => warnings.push(warning));
  const row = rows.find(value => value.id === 'terminal-bash');
  const defaults = ['--noprofile', '--norc', '-i'];
  const control = await probe(defaults);
  const configured = await probe(row.config.shellArgs || defaults);
  const report = {control, configured, warnings, configured_passed: configured.marker_written && configured.end_marker && !configured.history_error && warnings.length === 0};
  console.log(JSON.stringify(report));
  process.exitCode = report.configured_passed ? 0 : 1;
})().catch(error => {console.error(error.message); process.exitCode = 1;});
