import { spawn } from 'node:child_process';

const PORT = process.env.PLAYER_LAB_CHECK_PORT || '5099';
const BASE_URL = `http://127.0.0.1:${PORT}`;

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchWithRetry(pathname) {
  const url = `${BASE_URL}${pathname}`;
  let lastError;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      const response = await fetch(url);
      const body = await response.text();
      return { response, body };
    } catch (error) {
      lastError = error;
      await wait(250);
    }
  }
  throw lastError;
}

function assertIncludes(body, needle, label) {
  if (!body.includes(needle)) {
    throw new Error(`Expected ${label} to include ${JSON.stringify(needle)}`);
  }
}

const child = spawn(process.execPath, ['web/server.mjs'], {
  env: { ...process.env, PORT },
  stdio: ['ignore', 'pipe', 'pipe'],
});

let stdout = '';
let stderr = '';
child.stdout.on('data', chunk => { stdout += chunk.toString(); });
child.stderr.on('data', chunk => { stderr += chunk.toString(); });

try {
  const empty = await fetchWithRetry('/player-lab');
  if (!empty.response.ok) {
    throw new Error(`/player-lab returned ${empty.response.status}`);
  }
  assertIncludes(empty.body, 'Player interpretability lab', 'empty player lab page');
  assertIncludes(empty.body, 'Search for a source-backed WR to view deterministic tags and raw rows.', 'empty player lab page');

  const searched = await fetchWithRetry('/player-lab?name=Chase');
  if (!searched.response.ok) {
    throw new Error(`/player-lab?name=Chase returned ${searched.response.status}`);
  }
  assertIncludes(searched.body, 'Interpretation tags', 'searched player lab page');
  assertIncludes(searched.body, 'Raw/source data preview', 'searched player lab page');
  assertIncludes(searched.body, 'WR', 'searched player lab page');

  console.log('player-lab route smoke check passed');
} finally {
  child.kill('SIGTERM');
  await new Promise(resolve => child.once('exit', resolve));
}

if (stderr.trim()) {
  console.error(stderr.trim());
}
if (!stdout.includes('TIBER-Data Evidence Layer')) {
  throw new Error('Server did not print startup banner');
}
