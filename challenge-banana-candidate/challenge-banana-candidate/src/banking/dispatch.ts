import { bankRequest, BankError } from './client';
import type { Operation, ToolContext, TransferInput } from '../types';
export class UnknownTransferError extends Error {}
async function reconcile(ctx: ToolContext, reference: string): Promise<Operation | null> {
  try {
    return await bankRequest<Operation>(
      ctx.userId,
      `/v1/operations/${encodeURIComponent(reference)}`,
    );
  } catch (error) {
    if (error instanceof BankError && error.status === 404) return null;
    throw new UnknownTransferError(
      'The bank could not verify the transfer. Retry this same intent to check its status.',
    );
  }
}
export async function dispatchTransfer(
  ctx: ToolContext,
  input: TransferInput,
  reference: string,
  existingReference: boolean,
): Promise<Operation> {
  if (existingReference) {
    const operation = await reconcile(ctx, reference);
    if (operation) return operation;
  }
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      return await bankRequest<Operation>(ctx.userId, '/v1/transfers', 'POST', {
        ...input,
        reference,
      });
    } catch (e) {
      if (e instanceof BankError && e.status < 500) throw e;
      const operation = await reconcile(ctx, reference);
      if (operation) return operation;
      if (attempt === 1)
        throw new UnknownTransferError(
          'The transfer is not yet verified. Retry this same intent; do not create another transfer.',
        );
    }
  }
  throw new UnknownTransferError('The transfer is not yet verified.');
}
