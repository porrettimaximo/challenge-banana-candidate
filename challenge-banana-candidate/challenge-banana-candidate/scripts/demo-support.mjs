import fs from 'node:fs';
const base = process.env.APP_URL || 'http://127.0.0.1:3000';
let cookie = '';
async function api(route, body) {
  const response = await fetch(base + '/api/' + route, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', cookie },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const session = response.headers.get('set-cookie');
  if (session) cookie = session.split(';')[0];
  const result = await response.json();
  if (!response.ok) throw new Error(JSON.stringify({ route, status: response.status, result }));
  return result;
}
await api('session', { userId: 'lucia' });
const conversation = await api('conversations', {});
const intentId = crypto.randomUUID();
const proposal = await api('actions', { name: 'transfer_money', intentId, conversationId: conversation.id,
  arguments: { fromAccountId: 'acc-lucia', toAccountId: 'acc-bruno', amountCents: 250, concept: 'Support copilot demonstration' } });
if (proposal.status !== 'requires_confirmation') throw new Error('Proposal missing');
const confirmation = await api('approvals/' + proposal.approval.id + '/confirm', {});
if (confirmation.status !== 'completed') throw new Error('Completion unverified; do not repeat this demonstration');
const incident = await api('actions', { name: 'request_human', conversationId: conversation.id, arguments: {
  summary: 'Please verify the EUR 2.50 support copilot demonstration transfer to Bruno.' } });
await api('session', { userId: 'marta' });
const detail = await api('incidents/' + incident.incidentId);
const briefing = await api('incidents/' + incident.incidentId + '/briefing', {});
const evidence = { demonstratedAt: new Date().toISOString(), conversationId: conversation.id, intentId,
  proposalStatus: proposal.status, confirmationStatus: confirmation.status, reference: confirmation.operation.reference,
  incidentId: incident.incidentId, recordedEvents: detail.events.length, copilot: detail.copilot, briefingMode: briefing.mode,
  note: 'New conversation and operations via public tool HTTP surface; no real model chat was invoked. Running this script again creates a distinct simulated transfer.' };
fs.writeFileSync('submission/demo-evidence.json', JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify({ incidentId: incident.incidentId, recordedEvents: detail.events.length, findings: detail.copilot.findings.map(f => f.code), mode: briefing.mode }));

