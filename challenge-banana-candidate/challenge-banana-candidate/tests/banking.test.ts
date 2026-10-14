import test, { after, before } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'banana-banking-'));
const socket = net.createServer();
await new Promise<void>((resolve) => socket.listen(0, '127.0.0.1', resolve));
const port = (socket.address() as net.AddressInfo).port;
await new Promise<void>((resolve) => socket.close(() => resolve()));
process.env.DATA_DIR = temp;
process.env.BANK_DATA_DIR = temp;
process.env.BANK_PORT = String(port);
process.env.BANK_URL = `http://127.0.0.1:${port}`;
process.env.BANK_TIMEOUT_MS = '150';
const { transferMoney } = await import('../src/banking/actions');
const { appDb, closeAppDb } = await import('../src/db');
const { config } = await import('../src/config');
const bank = spawn(process.execPath, ['--import', 'tsx', 'simulator/server.ts'], {
  cwd: process.cwd(),
  env: process.env,
  stdio: 'pipe',
});
let bankLog = '';
bank.stdout.on('data', (chunk) => {
  bankLog += chunk;
});
bank.stderr.on('data', (chunk) => {
  bankLog += chunk;
});
before(async () => {
  for (let i = 0; i < 100; i++) {
    try {
      if ((await fetch(`${config.bankUrl}/health`)).ok) return;
    } catch (error) {
      if (i === 99) bankLog += String(error) + ' url=' + config.bankUrl;
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`Bank did not start: ${bankLog}`);
});
after(async () => {
  const exited = new Promise<void>((resolve) => bank.once('exit', () => resolve()));
  bank.kill();
  await exited;
  closeAppDb();
  fs.rmSync(temp, { recursive: true, force: true });
});
const input = {
  fromAccountId: 'acc-lucia',
  toAccountId: 'acc-bruno',
  amountCents: 1000,
  concept: 'HTTP integration',
};
const ctx = () => ({
  userId: 'lucia',
  conversationId: null,
  runId: randomUUID(),
  intentId: randomUUID(),
});
async function admin(route: string, body?: unknown) {
  const response = await fetch(`${config.bankUrl}/admin/${route}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { authorization: `Bearer ${config.adminSecret}`, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  assert.equal(response.status, 200);
  return response.json();
}
async function reset(profile = 'normal') {
  await admin('reset', {});
  await admin('scenario', { profile });
  appDb().exec('DELETE FROM approvals; DELETE FROM intents; DELETE FROM events;');
}
async function proposal(context = ctx(), payload = input) {
  const result = await transferMoney(context, payload);
  assert.equal(result.status, 'requires_confirmation');
  return { ...context, approvalId: (result.approval as { id: string }).id };
}
const effects = async () =>
  (await admin('snapshot')).operations.filter((op: any) => op.concept === input.concept);

test('proposal requires explicit review, expiry, payload and actor binding', async () => {
  await reset();
  const context = ctx();
  const approved = await proposal(context);
  assert.equal((await effects()).length, 0);
  assert.equal((await proposal(context)).approvalId, approved.approvalId);
  await assert.rejects(
    () => transferMoney(approved, { ...input, amountCents: 1200 }),
    /different payload/,
  );
  await assert.rejects(
    () => transferMoney({ ...approved, userId: 'bruno' }, input),
    /different payload/,
  );
  await assert.rejects(() => transferMoney({ ...ctx(), userId: 'marta' }, input), /customer/);
  await assert.rejects(
    () => transferMoney({ ...ctx(), userId: 'bruno' }, input),
    /does not belong/,
  );
  appDb()
    .prepare('UPDATE approvals SET expires_at=? WHERE id=?')
    .run('2000-01-01T00:00:00.000Z', approved.approvalId);
  await assert.rejects(() => transferMoney(approved, input), /expired/);
  assert.equal((await effects()).length, 0);
});
test('concurrent confirmations, repeated confirmation and process restart preserve one effect', async () => {
  await reset();
  const approved = await proposal();
  const results = await Promise.all(
    Array.from({ length: 5 }, () => transferMoney(approved, input)),
  );
  assert.ok(results.every((result) => result.status === 'completed'));
  assert.equal(new Set(results.map((result) => (result.operation as any).id)).size, 1);
  closeAppDb();
  const replay = await transferMoney(approved, input);
  assert.equal(replay.status, 'completed');
  assert.equal((await effects()).length, 1);
  const other = await proposal();
  assert.equal((await transferMoney(other, input)).status, 'completed');
  assert.equal((await effects()).length, 2);
});
for (const profile of ['reject-before', 'lost-response', 'slow-response', 'read-unavailable']) {
  test(`HTTP ${profile}: stable reference and verified outcome`, async () => {
    await reset(profile);
    const approved = await proposal();
    const result = await transferMoney(approved, input);
    assert.equal(result.status, profile === 'read-unavailable' ? 'unknown' : 'completed');
    const firstReference = (
      appDb().prepare('SELECT bank_reference FROM intents WHERE id=?').get(approved.intentId) as any
    ).bank_reference;
    assert.equal((await transferMoney(approved, input)).status, 'completed');
    assert.equal(
      (
        appDb()
          .prepare('SELECT bank_reference FROM intents WHERE id=?')
          .get(approved.intentId) as any
      ).bank_reference,
      firstReference,
    );
    const operations = await effects();
    assert.equal(operations.length, 1);
    assert.equal(operations[0].reference, firstReference);
  });
}
test('a verified bank rejection reports failure and preserves balances', async () => {
  await reset();
  const before = await admin('snapshot');
  const payload = { ...input, amountCents: 10000000 };
  const approved = await proposal(ctx(), payload);
  assert.equal((await transferMoney(approved, payload)).status, 'failed');
  const after = await admin('snapshot');
  assert.deepEqual(after.accounts, before.accounts);
  assert.equal((await effects()).length, 0);
});
test('public action and confirm HTTP handlers require session identity and replay safely', async () => {
  await reset('lost-response');
  const { POST } = await import('../app/api/[...path]/route');
  const { sessionToken } = await import('../src/auth');
  async function post(route: string[], body: unknown = {}, userId = 'lucia') {
    return POST(
      new Request(`http://localhost/api/${route.join('/')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          cookie: `banana_actor=${sessionToken(userId)}`,
        },
        body: JSON.stringify(body),
      }),
      { params: Promise.resolve({ path: route }) },
    );
  }
  const response = await post(['actions'], {
    name: 'transfer_money',
    arguments: input,
    intentId: randomUUID(),
  });
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.status, 'requires_confirmation');
  assert.equal((await effects()).length, 0);
  assert.equal((await post(['approvals', result.approval.id, 'confirm'], {}, 'bruno')).status, 404);
  const confirmed = await post(['approvals', result.approval.id, 'confirm']);
  assert.equal(confirmed.status, 200);
  const completed = await confirmed.json();
  assert.equal(completed.status, 'completed');
  const replay = await (await post(['approvals', result.approval.id, 'confirm'])).json();
  assert.equal(replay.operation.id, completed.operation.id);
  assert.equal((await effects()).length, 1);
});
test('unknown confirmation survives dashboard reload and reconciles using its consumed approval', async () => {
  await reset('read-unavailable');
  const { GET, POST } = await import('../app/api/[...path]/route');
  const { sessionToken } = await import('../src/auth');
  const headers = {
    'Content-Type': 'application/json',
    cookie: `banana_actor=${sessionToken('lucia')}`,
  };
  const context = ctx();
  const proposed = await POST(
    new Request('http://localhost/api/actions', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: 'transfer_money',
        arguments: input,
        intentId: context.intentId,
      }),
    }),
    { params: Promise.resolve({ path: ['actions'] }) },
  );
  const { approval } = await proposed.json();
  const confirm = () =>
    POST(
      new Request(`http://localhost/api/approvals/${approval.id}/confirm`, {
        method: 'POST',
        headers,
        body: '{}',
      }),
      { params: Promise.resolve({ path: ['approvals', approval.id, 'confirm'] }) },
    );
  const result = await (await confirm()).json();
  assert.equal(result.status, 'unknown');
  const dashboard = async () =>
    (
      await GET(new Request('http://localhost/api/dashboard', { headers }), {
        params: Promise.resolve({ path: ['dashboard'] }),
      })
    ).json();
  closeAppDb();
  const pending = (await dashboard()).pendingTransfers;
  assert.equal(pending.length, 1);
  assert.equal(pending[0].id, context.intentId);
  assert.equal(pending[0].bank_reference, result.reference);
  assert.equal(pending[0].approvalId, approval.id);
  assert.deepEqual(pending[0].payload, input);
  assert.equal((await (await confirm()).json()).status, 'completed');
  assert.deepEqual((await dashboard()).pendingTransfers, []);
  assert.equal((await effects()).length, 1);
});
