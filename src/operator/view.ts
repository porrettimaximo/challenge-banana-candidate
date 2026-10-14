import { appDb } from '../db';
import { person } from '../people';
import { HttpError } from '../auth';
import { bankRequest } from '../banking/client';
import { buildCaseCopilot } from './copilot';
import type { Account, Operation } from '../types';
export type CaseMessage = { id: string; role: string; content: string; created_at: string; run_id: string | null };
export type CaseEvent = { id: string; kind: string; data: Record<string, unknown>; created_at: string; run_id: string };
export type CaseIntent = { id: string; status: string; payload: Record<string, unknown>; bank_reference: string | null; operation_id: string | null; error: string | null; created_at: string };
export type CaseEvidence = {
  incident: { id: string; user_id: string; conversation_id: string; summary: string; status: string; created_at: string };
  history: CaseMessage[];
  events: CaseEvent[];
  intents: CaseIntent[];
  bank: { accounts: Account[]; operations: Operation[] } | null;
  bankError: string | null;
  bankObservedAt: string;
  evidenceGaps: string[];
};
function parseRecord(raw: string): Record<string, unknown> {
  try {
    const value = JSON.parse(raw);
    return value !== null && typeof value === 'object' && !Array.isArray(value)
      ? value : { evidenceError: 'Stored evidence is not an object.' };
  } catch { return { evidenceError: 'Stored evidence could not be decoded.' }; }
}
export async function caseDetail(operatorId: string, id: string) {
  if (person(operatorId)?.role !== 'operator') throw new HttpError(403, 'Operator role required.');
  const db = appDb();
  const incident = db.prepare('SELECT * FROM incidents WHERE id=?').get(id) as CaseEvidence['incident'] | undefined;
  if (!incident) throw new HttpError(404, 'Case not found.');
  const history = db.prepare('SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at,rowid')
    .all(incident.conversation_id) as CaseMessage[];
  const events = (db.prepare('SELECT * FROM events WHERE conversation_id=? AND user_id=? ORDER BY created_at,rowid')
    .all(incident.conversation_id, incident.user_id) as (Omit<CaseEvent, 'data'> & { data: string })[])
    .map((event) => ({ ...event, data: parseRecord(event.data) }));
  const intents = (db.prepare('SELECT * FROM intents WHERE conversation_id=? AND user_id=? ORDER BY created_at,rowid')
    .all(incident.conversation_id, incident.user_id) as (Omit<CaseIntent, 'payload'> & { payload: string })[])
    .map((intent) => ({ ...intent, payload: parseRecord(intent.payload) }));
  let bank: CaseEvidence['bank'] = null;
  let bankError: string | null = null;
  try {
    bank = await bankRequest<NonNullable<CaseEvidence['bank']>>(operatorId,
      `/v1/operator/customer?id=${encodeURIComponent(incident.user_id)}`);
  } catch (error) { bankError = error instanceof Error ? error.message : 'Bank evidence unavailable.'; }
  const evidenceGaps: string[] = [];
  if (!history.length) evidenceGaps.push('No conversation messages were recorded.');
  if (!events.length) evidenceGaps.push('No tool events were recorded. Historical bank effects cannot be inferred from the conversation.');
  if (events.some((event) => event.data.evidenceError ||
      (event.kind.startsWith('tool.') && !('arguments' in event.data))))
    evidenceGaps.push('Some historical events lack arguments or readable evidence; their details cannot be reconstructed.');
  if (!intents.length) evidenceGaps.push('No transfer intents were recorded for this conversation.');
  if (!bank) evidenceGaps.push('The bank snapshot is unavailable; transfer outcomes remain unverified.');
  const evidence: CaseEvidence = { incident, history, events, intents, bank, bankError,
    bankObservedAt: new Date().toISOString(), evidenceGaps };
  return {
    ...evidence,
    customer: person(incident.user_id),
    lastMessage: history.at(-1) ?? null,
    copilot: buildCaseCopilot(evidence),
  };
}
