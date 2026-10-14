import { bankRequest } from './client';
import { randomUUID } from 'node:crypto';
import { appDb } from '../db';
import { HttpError } from '../auth';
import type { Account, ActionResult, ToolContext, TransferInput } from '../types';
export async function authorizeTransfer(
  ctx: ToolContext,
  input: TransferInput,
): Promise<ActionResult | null> {
  const accounts = await bankRequest<Account[]>(ctx.userId, '/v1/accounts');
  if (!accounts.some((a) => a.id === input.fromAccountId))
    throw new HttpError(403, 'This account does not belong to this person.');
  if (input.fromAccountId === input.toAccountId)
    throw new HttpError(400, 'Source and destination must differ.');
  const db = appDb(),
    payload = JSON.stringify(input);
  if (ctx.approvalId) {
    const approval = db.prepare('SELECT * FROM approvals WHERE id=?').get(ctx.approvalId) as
      | {
          user_id: string;
          intent_id: string;
          payload: string;
          expires_at: string;
          consumed_at: string | null;
        }
      | undefined;
    if (
      !approval ||
      approval.user_id !== ctx.userId ||
      approval.intent_id !== ctx.intentId ||
      approval.payload !== payload
    )
      throw new HttpError(403, 'This proposal does not authorize this transfer.');
    if (!approval.consumed_at && approval.expires_at <= new Date().toISOString())
      throw new HttpError(410, 'This proposal expired. Request a new proposal.');
    return null;
  }
  const approval = db.transaction(() => {
    const now = new Date().toISOString();
    const existing = db
      .prepare(
        'SELECT id,payload,expires_at FROM approvals WHERE user_id=? AND intent_id=? AND consumed_at IS NULL AND expires_at>? ORDER BY expires_at DESC LIMIT 1',
      )
      .get(ctx.userId, ctx.intentId, now) as
      { id: string; payload: string; expires_at: string } | undefined;
    if (existing) return existing;
    const id = randomUUID(),
      expires_at = new Date(Date.now() + 10 * 60 * 1000).toISOString();
    db.prepare('INSERT INTO approvals VALUES(?,?,?,?,?,NULL)').run(
      id,
      ctx.userId,
      ctx.intentId,
      payload,
      expires_at,
    );
    db.prepare('UPDATE intents SET status=? WHERE id=? AND bank_reference IS NULL').run(
      'requires_confirmation',
      ctx.intentId,
    );
    return { id, payload, expires_at };
  })();
  return {
    status: 'requires_confirmation',
    intentId: ctx.intentId,
    approval: {
      id: approval.id,
      payload: JSON.parse(approval.payload),
      expiresAt: approval.expires_at,
    },
  };
}
