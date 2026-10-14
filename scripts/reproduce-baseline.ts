/** Run with Node 24 --import tsx. Original extracted ZIP stays under excluded .tmp. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { randomUUID, createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const project = process.cwd();
const baseline = path.resolve(process.argv[2] || '.tmp/baseline/challenge-banana-candidate');
if (!process.argv.includes('--worker')) {
  if (!fs.existsSync(path.join(baseline, 'src/banking/actions.ts')))
    throw new Error('Extract the unmodified supplied ZIP and pass its project directory first.');
  // Node resolves dependencies from the ancestor project's node_modules.
  const results = [];
  for (const source of [baseline, project]) {
    const child = spawn(process.execPath, ['--import', 'tsx', 'scripts/reproduce-baseline.ts', source, '--worker'],
      { cwd: project, env: { ...process.env, ORIGINAL_SOURCE: baseline }, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    child.stdout.on('data', chunk => stdout += chunk);
    child.stderr.on('data', chunk => stderr += chunk);
    const code = await new Promise(resolve => child.once('exit', resolve));
    if (code !== 0) throw new Error(`Reproduction failed: ${stderr}`);
    results.push(JSON.parse(stdout));
  }
  const evidence = {
    recordedAt: new Date().toISOString(),
    originalSource: 'Unmodified supplied ZIP recovered from git HEAD:challenge-banana-candidate.zip',
    originalZipSha256: fs.existsSync('.tmp/baseline-input.zip')
      ? createHash('sha256').update(fs.readFileSync('.tmp/baseline-input.zip')).digest('hex') : null,
    command: 'node --import tsx scripts/reproduce-baseline.ts <extracted-original-project>',
    isolation: 'Separate temporary application/bank databases, ephemeral localhost ports, original simulator, no main data changes.',
    before: results[0], after: results[1],
  };
  fs.writeFileSync('submission/before-after.json', JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence, null, 2));
} else {
  const source = path.resolve(process.argv[2]);
  const fixed = source === project;
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'banana-before-after-'));
  const socket = net.createServer();
  await new Promise<void>(resolve => socket.listen(0, '127.0.0.1', resolve));
  const port = (socket.address() as net.AddressInfo).port;
  await new Promise<void>(resolve => socket.close(() => resolve()));
  Object.assign(process.env, { DATA_DIR: temp, BANK_DATA_DIR: temp, BANK_PORT: String(port),
    BANK_URL: `http://127.0.0.1:${port}`, BANK_TIMEOUT_MS: '1000', OPENAI_API_KEY: '',
    BANK_SERVICE_SECRET: 'banana-local-service', BANK_ADMIN_SECRET: 'banana-local-admin' });
  const { transferMoney } = await import(pathToFileURL(path.join(source, 'src/banking/actions.ts')).href);
  const { closeAppDb } = await import(pathToFileURL(path.join(source, 'src/db.ts')).href);
  const original = process.env.ORIGINAL_SOURCE!;
  const bank = spawn(process.execPath, ['--import', 'tsx', path.join(original, 'simulator/server.ts')],
    { cwd: original, env: process.env, stdio: 'pipe' });
  let log = '';
  bank.stderr!.on('data', chunk => log += chunk);
  bank.stdout!.on('data', chunk => log += chunk);
  async function admin(route: string, body?: unknown) {
    const response = await fetch(`${process.env.BANK_URL}/admin/${route}`, {
      method: body === undefined ? 'GET' : 'POST',
      headers: { authorization: 'Bearer banana-local-admin', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    assert.equal(response.status, 200);
    return response.json();
  }
  const payload = { fromAccountId: 'acc-lucia', toAccountId: 'acc-bruno', amountCents: 1000, concept: 'before-after-evidence' };
  const context = () => ({ userId: 'lucia', conversationId: null, runId: randomUUID(), intentId: randomUUID() });
  const balance = (snapshot: any) => snapshot.accounts.find((account: any) => account.id === 'acc-lucia').balanceCents;
  const count = (snapshot: any) => snapshot.operations.filter((operation: any) => operation.concept === payload.concept).length;
  try {
    let ready = false;
    for (let i = 0; i < 100; i++) {
      try { if ((await fetch(`${process.env.BANK_URL}/health`)).ok) { ready = true; break; } } catch {}
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    if (!ready) throw new Error(`Bank did not start: ${log}`);
    await admin('reset', {}); await admin('scenario', { profile: 'normal' });
    const opening = await admin('snapshot');
    const firstContext = context();
    const proposed = await transferMoney(firstContext, payload);
    const afterProposal = await admin('snapshot');
    const noConfirmation = { returnedStatus: proposed.status, debitCents: balance(opening) - balance(afterProposal), operationCount: count(afterProposal) };
    let confirmation = null;
    if (fixed) {
      assert.equal(noConfirmation.debitCents, 0); assert.equal(noConfirmation.operationCount, 0);
      const confirmed = await transferMoney({ ...firstContext, approvalId: proposed.approval.id }, payload);
      const snapshot = await admin('snapshot');
      confirmation = { returnedStatus: confirmed.status, debitCents: balance(opening) - balance(snapshot), operationCount: count(snapshot) };
    }
    await admin('reset', {}); await admin('scenario', { profile: 'lost-response' });
    const initial = await admin('snapshot');
    let secondContext = context();
    if (fixed) {
      const approval = await transferMoney(secondContext, payload);
      secondContext = { ...secondContext, approvalId: approval.approval.id } as any;
    }
    const lost = await transferMoney(secondContext, payload);
    const snapshot = await admin('snapshot');
    const operations = snapshot.operations.filter((operation: any) => operation.concept === payload.concept);
    const lostResponse = { returnedStatus: lost.status, debitCents: balance(initial) - balance(snapshot),
      operationCount: operations.length, distinctReferences: new Set(operations.map((operation: any) => operation.reference)).size };
    assert.equal(lostResponse.operationCount, fixed ? 1 : 2);
    assert.equal(lostResponse.debitCents, fixed ? 1000 : 2000);
    console.log(JSON.stringify({ noConfirmation, confirmation, lostResponse }));
  } finally {
    const exited = new Promise(resolve => bank.once('exit', resolve));
    bank.kill(); await exited; closeAppDb(); fs.rmSync(temp, { recursive: true, force: true });
  }
}
