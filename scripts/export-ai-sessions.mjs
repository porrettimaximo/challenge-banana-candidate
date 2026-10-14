import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
function argument(name) {
  const index = process.argv.indexOf(name);
  if (index < 0) return undefined;
  if (!process.argv[index + 1] || process.argv[index + 1].startsWith('--'))
    throw new Error(`${name} requires a value.`);
  return process.argv[index + 1];
}
const configPath = path.join(projectRoot, 'submission', 'session-export.json');
const settings = fs.existsSync(configPath) ? JSON.parse(fs.readFileSync(configPath, 'utf8')) : {};
const rootId = argument('--root-session') || settings.rootSessionId || '01a13a97-9f89-7353-88ca-9931b1591f13';
const sessionsRoot = path.resolve(argument('--sessions-dir') ||
  path.join(process.env.CODEX_HOME || path.join(os.homedir(), '.codex'), 'sessions'));
const destination = path.join(projectRoot, 'submission', 'ai-sessions');
function* files(root) {
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const filename = path.join(root, entry.name);
    if (entry.isDirectory()) yield* files(filename);
    else if (entry.isFile() && entry.name.endsWith('.jsonl')) yield filename;
  }
}
function metadata(filename) {
  const handle = fs.openSync(filename, 'r');
  try {
    const buffer = Buffer.alloc(512 * 1024);
    const length = fs.readSync(handle, buffer, 0, buffer.length, 0);
    const text = buffer.subarray(0, length).toString('utf8');
    const end = text.indexOf('\n');
    const record = JSON.parse(end < 0 ? text : text.slice(0, end));
    return record.type === 'session_meta' ? record.payload : null;
  } catch { return null; }
  finally { fs.closeSync(handle); }
}
const sessions = [...files(sessionsRoot)].map((filename) => ({ filename, meta: metadata(filename) }))
  .filter((entry) => entry.meta?.id);
if (!sessions.some((entry) => entry.meta.id === rootId))
  throw new Error(`Root session ${rootId} was not found. Use --root-session or --sessions-dir.`);
const descendants = new Set([rootId]);
for (let changed = true; changed;) {
  changed = false;
  for (const entry of sessions)
    if (descendants.has(entry.meta.parent_thread_id) && !descendants.has(entry.meta.id)) {
      descendants.add(entry.meta.id);
      changed = true;
    }
}
const selected = sessions.filter((entry) => descendants.has(entry.meta.id));
const exported = [];
const skipped = [];
// Fail closed without logging matched credential values. Original bytes are never redacted.
const credentialPatterns = [
  /\bsk-[A-Za-z0-9_-]{24,}\b/,
  /\b(?:ghp_|github_pat_)[A-Za-z0-9_]{24,}\b/,
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
];
fs.mkdirSync(destination, { recursive: true });
const selectedNames = new Set(selected.filter((entry) => entry.meta.source?.subagent?.other !== 'guardian')
  .map((entry) => path.basename(entry.filename)));
for (const entry of fs.readdirSync(destination))
  if (entry.endsWith('.jsonl') && !selectedNames.has(entry))
    throw new Error(`Unexpected session file ${entry} already exists in the export folder. Review it before exporting a different root.`);
for (const { filename, meta } of selected) {
  if (meta.source?.subagent?.other === 'guardian') {
    skipped.push({ id: meta.id, parentThreadId: meta.parent_thread_id, reason: 'Internal approval guardian, not development work.' });
    continue;
  }
  const bytes = fs.readFileSync(filename);
  if (credentialPatterns.some((pattern) => pattern.test(bytes.toString('utf8'))))
    throw new Error(`Credential pattern detected in session ${meta.id}. No values were printed; review before exporting original sessions.`);
  const name = path.basename(filename);
  fs.writeFileSync(path.join(destination, name), bytes);
  exported.push({ file: name, id: meta.id, parentThreadId: meta.parent_thread_id || null,
    agentPath: meta.agent_path || null, role: meta.source?.subagent?.thread_spawn?.agent_role ||
      (meta.id === rootId ? 'orchestrator' : meta.agent_path?.split('/').at(-1) || 'subagent'),
    sourceTimestamp: meta.timestamp || null, modelProvider: meta.model_provider || null,
    bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
}
const manifest = { format: 1, rootSessionId: rootId, exportedAt: new Date().toISOString(),
  note: 'Original JSONL byte snapshots, not rewritten summaries. Active sessions may grow after export; rerun immediately before packaging.',
  sessions: exported.sort((a, b) => a.file.localeCompare(b.file)), skipped };
fs.writeFileSync(path.join(destination, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`Exported ${exported.length} original development sessions; skipped ${skipped.length} internal approval sessions.`);
console.log(`Manifest: ${path.relative(projectRoot, path.join(destination, 'manifest.json'))}`);
