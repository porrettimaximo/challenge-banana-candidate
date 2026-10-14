import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { deflateRawSync } from 'node:zlib';
import { createHash } from 'node:crypto';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let workspaceRoot = projectRoot;
while (path.basename(path.dirname(workspaceRoot)) === path.basename(projectRoot))
  workspaceRoot = path.dirname(workspaceRoot);
const argIndex = process.argv.indexOf('--output');
if (argIndex >= 0 && (!process.argv[argIndex + 1] || process.argv[argIndex + 1].startsWith('--')))
  throw new Error('--output requires a filename.');
const output = path.resolve(argIndex >= 0 ? process.argv[argIndex + 1]
  : path.join(workspaceRoot, 'delivery', 'banana-bank-maximo-porretti.zip'));
const relativeOutput = path.relative(projectRoot, output);
if (!relativeOutput.startsWith(`..${path.sep}`) && !path.isAbsolute(relativeOutput))
  throw new Error('Write the archive outside the project source root to prevent recursive packaging.');

const excludedDirectories = new Set(['node_modules', '.next', '.data', '.git', 'tmp', '.tmp',
  'test-results', 'artifacts', 'package-output', 'delivery', 'coverage']);
function* files(root, relative = '') {
  for (const entry of fs.readdirSync(root, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const filename = path.join(root, entry.name);
    const name = relative ? `${relative}/${entry.name}` : entry.name;
    if (entry.isSymbolicLink()) continue;
    if (entry.isDirectory()) {
      if (!excludedDirectories.has(entry.name)) yield* files(filename, name);
    } else if (entry.isFile() && !(entry.name.startsWith('.env') && entry.name !== '.env.example') &&
      !entry.name.endsWith('.zip') && !entry.name.endsWith('.tsbuildinfo') && !entry.name.endsWith('.log'))
      yield { filename, name };
  }
}
const crcTable = Array.from({ length: 256 }, (_, value) => {
  for (let i = 0; i < 8; i++) value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
  return value >>> 0;
});
function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}
const rootName = 'banana-bank-maximo-porretti';
const localRecords = [];
const centralRecords = [];
let offset = 0;
const inventory = [];
const credentials = [ /\bsk-[A-Za-z0-9_-]{24,}\b/,
  /\b(?:ghp_|github_pat_)[A-Za-z0-9_]{24,}\b/,
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/ ];
for (const { filename, name } of files(projectRoot)) {
  const data = fs.readFileSync(filename);
  if (/\.(?:[cm]?[jt]sx?|jsonl?|md|txt|toml|ya?ml|example|html|css|csv)$/i.test(name) &&
      credentials.some((pattern) => pattern.test(data.toString('utf8'))))
    throw new Error(`Credential pattern detected in ${name}; archive was not written. No values were printed.`);
  const encodedName = Buffer.from(`${rootName}/${name}`, 'utf8');
  const compressed = deflateRawSync(data, { level: 6 });
  const crc = crc32(data);
  if (data.length > 0xffffffff || compressed.length > 0xffffffff || offset > 0xffffffff || encodedName.length > 65535)
    throw new Error('Archive exceeds classic ZIP limits.');
  const modified = fs.statSync(filename).mtime;
  const dosTime = (modified.getUTCHours() << 11) | (modified.getUTCMinutes() << 5) | (modified.getUTCSeconds() >> 1);
  const dosDate = ((Math.max(1980, modified.getUTCFullYear()) - 1980) << 9) |
    ((modified.getUTCMonth() + 1) << 5) | modified.getUTCDate();
  const local = Buffer.alloc(30);
  local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(20, 4);
  local.writeUInt16LE(0x800, 6); local.writeUInt16LE(8, 8);
  local.writeUInt16LE(dosTime, 10); local.writeUInt16LE(dosDate, 12);
  local.writeUInt32LE(crc, 14); local.writeUInt32LE(compressed.length, 18);
  local.writeUInt32LE(data.length, 22); local.writeUInt16LE(encodedName.length, 26);
  localRecords.push(local, encodedName, compressed);
  const central = Buffer.alloc(46);
  central.writeUInt32LE(0x02014b50, 0); central.writeUInt16LE(20, 4); central.writeUInt16LE(20, 6);
  central.writeUInt16LE(0x800, 8); central.writeUInt16LE(8, 10);
  central.writeUInt16LE(dosTime, 12); central.writeUInt16LE(dosDate, 14);
  central.writeUInt32LE(crc, 16); central.writeUInt32LE(compressed.length, 20);
  central.writeUInt32LE(data.length, 24); central.writeUInt16LE(encodedName.length, 28);
  central.writeUInt32LE(offset, 42); centralRecords.push(central, encodedName);
  offset += local.length + encodedName.length + compressed.length;
  inventory.push({ file: name, bytes: data.length, sha256: createHash('sha256').update(data).digest('hex') });
}
if (inventory.length > 65535) throw new Error('Too many ZIP entries.');
const centralSize = centralRecords.reduce((sum, item) => sum + item.length, 0);
const end = Buffer.alloc(22);
end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(inventory.length, 8);
end.writeUInt16LE(inventory.length, 10); end.writeUInt32LE(centralSize, 12); end.writeUInt32LE(offset, 16);
fs.mkdirSync(path.dirname(output), { recursive: true });
const archive = Buffer.concat([...localRecords, ...centralRecords, end]);
fs.writeFileSync(output, archive);
fs.writeFileSync(`${output}.manifest.json`, `${JSON.stringify({ packagedAt: new Date().toISOString(),
  archive: path.basename(output), bytes: archive.length, sha256: createHash('sha256').update(archive).digest('hex'),
  root: rootName, excludedDirectories: [...excludedDirectories], files: inventory }, null, 2)}\n`);
console.log(`Packaged ${inventory.length} files, ${archive.length} bytes.`);
console.log(output);
