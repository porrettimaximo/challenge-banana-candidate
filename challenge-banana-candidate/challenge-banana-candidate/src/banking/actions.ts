import { z } from 'zod';
import { appDb } from '../db';
import { HttpError } from '../auth';
import { person } from '../people';
import { authorizeTransfer } from './authorization';
import { dispatchTransfer, UnknownTransferError } from './dispatch';
import { randomUUID } from 'node:crypto';
import { recordEvent } from '../telemetry';
import type { ActionResult, ToolContext } from '../types';
export const transferSchema = z
  .object({
    fromAccountId: z.string().min(1),
    toAccountId: z.string().min(1),
    amountCents: z.number().int().positive().max(10000000),
    concept: z.string().max(200),
  })
  .strict();
export async function transferMoney(ctx: ToolContext, args: unknown): Promise<ActionResult> {
  if (person(ctx.userId)?.role !== 'customer')
    throw new HttpError(403, 'A customer account is required.');
  const input = transferSchema.parse(args),
    db = appDb();
  db.transaction(() => {
    const previous = db
      .prepare('SELECT user_id,payload FROM intents WHERE id=?')
      .get(ctx.intentId) as { user_id: string; payload: string } | undefined;
    if (previous && (previous.user_id !== ctx.userId || previous.payload !== JSON.stringify(input)))
      throw new HttpError(409, 'This intent belongs to a different payload.');
    db.prepare('INSERT OR IGNORE INTO intents VALUES(?,?,?,?,?,?,?,?,?,?)').run(
      ctx.intentId,
      ctx.userId,
      ctx.conversationId,
      ctx.runId,
      JSON.stringify(input),
      'created',
      null,
      null,
      null,
      new Date().toISOString(),
    );
  })();
  const permission = await authorizeTransfer(ctx, input);
  if (permission) {
    recordEvent(ctx, 'transfer.proposed', { ...permission, input });
    return permission;
  }
  const claim = db.transaction(() => {
    const approval = db
      .prepare('SELECT consumed_at,expires_at FROM approvals WHERE id=?')
      .get(ctx.approvalId) as { consumed_at: string | null; expires_at: string };
    const now = new Date().toISOString();
    if (!approval.consumed_at && approval.expires_at <= now)
      throw new HttpError(410, 'This proposal expired. Request a new proposal.');
    const intent = db
      .prepare('SELECT bank_reference FROM intents WHERE id=?')
      .get(ctx.intentId) as { bank_reference: string | null };
    const reference = intent.bank_reference || randomUUID();
    db.prepare('UPDATE approvals SET consumed_at=COALESCE(consumed_at,?) WHERE id=?').run(
      now,
      ctx.approvalId,
    );
    db.prepare(
      "UPDATE intents SET status=CASE WHEN status='completed' THEN status ELSE ? END,bank_reference=? WHERE id=?",
    ).run('processing', reference, ctx.intentId);
    return { reference, existingReference: !!intent.bank_reference };
  })();
  recordEvent(ctx, 'transfer.confirmed', {
    approvalId: ctx.approvalId,
    input,
    reference: claim.reference,
  });
  recordEvent(ctx, 'transfer.started', {
    status: 'processing',
    input,
    intentId: ctx.intentId,
    reference: claim.reference,
  });
  try {
    const operation = await dispatchTransfer(ctx, input, claim.reference, claim.existingReference);
    db.prepare('UPDATE intents SET status=?,operation_id=?,error=NULL WHERE id=?').run(
      'completed',
      operation.id,
      ctx.intentId,
    );
    recordEvent(ctx, 'transfer.completed', {
      status: 'completed',
      operation,
      intentId: ctx.intentId,
    });
    return { status: 'completed', operation, intentId: ctx.intentId };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Transfer error';
    const status = e instanceof UnknownTransferError ? 'unknown' : 'failed';
    db.prepare("UPDATE intents SET status=?,error=? WHERE id=? AND status!='completed'").run(
      status,
      message,
      ctx.intentId,
    );
    recordEvent(ctx, `transfer.${status}`, {
      status,
      error: message,
      intentId: ctx.intentId,
    });
    return { status, error: message, intentId: ctx.intentId, reference: claim.reference };
  }
}
