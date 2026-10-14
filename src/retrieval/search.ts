import { appDb } from '../db';
import { config, referenceDate } from '../config';
import { documents } from '../ingestion/pipeline';
import { embedTexts } from './embeddings';
import { allChunks } from './store';
import type { Chunk, SearchResult } from '../types';
export function applicableChunk(chunk: Chunk, role: string, date = referenceDate) {
  return (role === 'operator' || chunk.audience === 'public') &&
    chunk.validFrom !== null && chunk.validFrom <= date &&
    (chunk.validTo === null || chunk.validTo >= date);
}
export async function searchDocuments(
  query: string,
  role = 'customer',
  limit = 5,
): Promise<SearchResult[]> {
  const meta = appDb().prepare('SELECT value FROM meta WHERE key=?').get('index-model') as
    { value: string } | undefined;
  if (!meta) throw new Error('No document index. Run npm run setup or npm run ingest.');
  if (meta.value !== config.embeddingModel)
    throw new Error('The model does not match the index. Re-ingest the documents.');
  const [queryVector] = await embedTexts([query]);
  // The bundled index predates complete per-chunk metadata. Repair it from the
  // authoritative local manifest without regenerating embeddings or modifying it.
  const manifest = new Map(documents().map((doc) => [doc.id, doc]));
  return allChunks()
    .map((c) => {
      const doc = manifest.get(c.documentId);
      return doc ? { ...c, title: doc.title, version: doc.version, validFrom: doc.validFrom,
        validTo: doc.validTo, audience: doc.audience } : c;
    })
    .filter((c) => applicableChunk(c, role))
    .map(({ vector, ...c }) => {
      if (vector!.length !== queryVector.length) throw new Error('Incompatible embedding dimensions.');
      const score = vector!.reduce((sum, v, i) => sum + v * queryVector[i], 0);
      return { ...c, score };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
