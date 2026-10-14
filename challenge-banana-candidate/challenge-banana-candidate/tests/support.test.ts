import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import type { AddressInfo } from 'node:net';
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'banana-support-'));
process.env.DATA_DIR = temp;
process.env.OPENAI_API_KEY = '';
let bankAvailable = true;
let bankActor = '';
const operation = {
  id: 'bank-op', userId: 'lucia', reference: 'original-ref', status: 'completed' as const,
  fromAccountId: 'acc-lucia', toAccountId: 'acc-bruno', amountCents: 1000,
  concept: 'Test', createdAt: '2026-09-24T10:00:00.000Z',
};
const server = http.createServer((req, res) => {
  bankActor = String(req.headers['x-bank-actor']);
  assert.equal(req.method, 'GET');
  assert.equal(req.url, '/v1/operator/customer?id=lucia');
  res.writeHead(bankAvailable ? 200 : 503, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(bankAvailable ? { accounts: [], operations: [operation] }
    : { error: 'Bank unavailable in test.' }));
});
await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
process.env.BANK_URL = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
const { appDb, closeAppDb } = await import('../src/db');
const { caseDetail } = await import('../src/operator/view');
const { buildCaseCopilot, generateCaseBriefing } = await import('../src/operator/copilot');
const { recordEvent } = await import('../src/telemetry');
const { chunkDocument } = await import('../src/ingestion/chunker');
const { applicableChunk, searchDocuments } = await import('../src/retrieval/search');
const { documents } = await import('../src/ingestion/pipeline');
const { knowledgeInstructions } = await import('../src/agent/prompt');
const { replaceChunks } = await import('../src/retrieval/store');
const { config, referenceDate } = await import('../src/config');
const { embeddingKey, vectorBuffer, dimensions } = await import('../src/retrieval/embeddings');
const db = appDb();
const now = '2026-09-24T10:00:00.000Z';
db.prepare('INSERT INTO conversations VALUES(?,?,?,?)').run('conversation', 'lucia', 'Help', now);
db.prepare('INSERT INTO conversations VALUES(?,?,?,?)').run('other', 'bruno', 'Other', now);
db.prepare('INSERT INTO incidents VALUES(?,?,?,?,?,?)').run('case', 'lucia', 'conversation', 'Review transfer', 'open', now);
for (let i = 0; i < 3; i++)
  db.prepare('INSERT INTO messages VALUES(?,?,?,?,?,?)').run(`message-${i}`, 'conversation',
    i % 2 ? 'assistant' : 'user', `Message ${i}`, now, null);
db.prepare('INSERT INTO messages VALUES(?,?,?,?,?,?)').run('private-message', 'other', 'user', 'Other customer', now, null);
const payload = { fromAccountId: operation.fromAccountId, toAccountId: operation.toAccountId,
  amountCents: operation.amountCents, concept: operation.concept };
db.prepare('INSERT INTO intents VALUES(?,?,?,?,?,?,?,?,?,?)').run('intent', 'lucia', 'conversation', 'run',
  JSON.stringify(payload), 'failed', 'original-ref', null, 'Response lost', now);

test('operator case includes ordered history, recorded tool details and read-only bank facts', async () => {
  recordEvent({ userId: 'lucia', conversationId: 'conversation', runId: 'run', intentId: 'intent' },
    'tool.failed', { tool: 'transfer_money', arguments: payload, status: 'failed',
      error: 'Response lost', durationMs: 12 });
  const detail = await caseDetail('marta', 'case');
  assert.equal(bankActor, 'marta');
  assert.deepEqual(detail.history.map((message) => message.id), ['message-0', 'message-1', 'message-2']);
  assert.equal(detail.lastMessage?.id, 'message-2');
  assert.deepEqual(detail.events[0].data.arguments, payload);
  assert.equal(detail.events[0].data.error, 'Response lost');
  assert.equal(detail.events[0].data.intentId, 'intent');
  assert.equal(detail.bank?.operations[0].id, 'bank-op');
  assert.equal(detail.intents[0].id, 'intent');
  assert.ok(detail.copilot.findings.some((finding) => finding.code === 'bank_committed_local_unconfirmed'));
  assert.match(detail.copilot.nextSteps.join(' '), /do not create a new payment/);
  assert.ok(detail.copilot.findings.some((finding) => finding.evidence.includes('bank:operation:bank-op')));
  const fallback = await generateCaseBriefing(detail);
  assert.equal(fallback.mode, 'evidence');
  assert.equal(fallback.briefing, null);
});

test('customer role and unknown case cannot access operator evidence', async () => {
  await assert.rejects(caseDetail('lucia', 'case'), /Operator role/);
  await assert.rejects(caseDetail('marta', 'missing'), /Case not found/);
});

test('historical gaps are disclosed rather than reconstructed from customer claims', async () => {
  db.exec('DELETE FROM events');
  const detail = await caseDetail('pablo', 'case');
  assert.ok(detail.evidenceGaps.some((gap) => /No tool events/.test(gap)));
  recordEvent({ userId: 'lucia', conversationId: 'conversation', runId: 'run', intentId: 'intent' },
    'tool.completed', { tool: 'transfer_money', status: 'completed' });
  const legacy = await caseDetail('pablo', 'case');
  assert.ok(legacy.evidenceGaps.some((gap) => /historical events lack arguments/.test(gap)));
});

test('bank outage preserves case evidence and never claims transfer failure from absence', async () => {
  bankAvailable = false;
  try {
    const detail = await caseDetail('marta', 'case');
    assert.equal(detail.bank, null);
    assert.equal(detail.bankError, 'Bank unavailable in test.');
    assert.equal(detail.history.length, 3);
    assert.ok(detail.copilot.findings.some((finding) => finding.code === 'bank_unavailable'));
    assert.match(detail.copilot.findings.find((finding) => finding.code === 'transfer_unverified')!.message,
      /Absence is not proof of failure/);
  } finally { bankAvailable = true; }
});

test('payload discrepancies and missing bank completion require human reconciliation', async () => {
  const detail = await caseDetail('marta', 'case');
  const mismatch = buildCaseCopilot({ ...detail, intents: [{ ...detail.intents[0],
    payload: { ...payload, amountCents: 9000 } }] });
  assert.equal(mismatch.findings.find((finding) => finding.code === 'payload_mismatch')?.severity, 'critical');
  const missing = buildCaseCopilot({ ...detail, bank: { accounts: [], operations: [] },
    intents: [{ ...detail.intents[0], status: 'completed' }] });
  assert.ok(missing.findings.some((finding) => finding.code === 'local_completed_bank_missing'));
});

test('every chunk retains source metadata and validity controls visibility', () => {
  const document = documents().find((item) => item.audience === 'public' && item.validTo === null)!;
  const chunks = chunkDocument(document, 'A'.repeat(1800));
  assert.equal(chunks.length, 3);
  assert.ok(chunks.every((chunk) => chunk.title === document.title && chunk.version === document.version &&
    chunk.validFrom === document.validFrom && chunk.validTo === document.validTo));
  assert.equal(applicableChunk({ ...chunks[0], audience: 'internal' }, 'customer'), false);
  assert.equal(applicableChunk({ ...chunks[0], audience: 'internal' }, 'operator'), true);
  assert.equal(applicableChunk({ ...chunks[0], validTo: '2026-01-01' }, 'customer'), false);
  assert.equal(applicableChunk({ ...chunks[0], validFrom: '2027-01-01' }, 'customer'), false);
  assert.equal(applicableChunk({ ...chunks[0], validFrom: null }, 'customer'), false);
});

test('retrieval repairs legacy chunk metadata and excludes obsolete and internal customer sources', async () => {
  const docs = documents();
  const current = docs.find((item) => item.audience === 'public' && item.validFrom <= referenceDate && !item.validTo)!;
  const historic = docs.find((item) => item.audience === 'public' && item.validTo && item.validTo < referenceDate)!;
  const internal = docs.find((item) => item.audience === 'internal' && item.validFrom <= referenceDate && !item.validTo)!;
  const vector = Array.from({ length: dimensions }, (_, index) => index === 0 ? 1 : 0);
  replaceChunks([current, historic, internal].map((document, index) => ({
    id: `legacy-${index}`, documentId: document.id, text: 'Legacy excerpt', title: null,
    version: null, validFrom: null, validTo: null, audience: document.audience, vector,
  })), { model: config.embeddingModel, dimensions });
  db.prepare('INSERT INTO embedding_cache VALUES(?,?)').run(embeddingKey('cached-query'), vectorBuffer(vector));
  const result = await searchDocuments('cached-query');
  assert.deepEqual(result.map((source) => source.documentId), [current.id]);
  assert.equal(result[0].version, current.version);
  assert.equal(result[0].title, current.title);
  const operators = await searchDocuments('cached-query', 'operator');
  assert.ok(operators.some((source) => source.documentId === internal.id));
  assert.ok(operators.every((source) => source.documentId !== historic.id));
  assert.match(knowledgeInstructions(result), /Never invent fees/);
  assert.ok(knowledgeInstructions(result).includes(`"validFrom":"${current.validFrom}"`));
});

after(async () => {
  await new Promise<void>((resolve) => server.close(() => resolve()));
  closeAppDb();
  fs.rmSync(temp, { recursive: true, force: true });
});
