// Read-only conversion of an already completed historical run; no runtime/provider import.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname, relative } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const here = dirname(fileURLToPath(import.meta.url));
const producer = resolve(process.argv[2]);
const hash = b => createHash('sha256').update(b).digest('hex');
const files = new Map();
async function collect(path) {
  path = resolve(path);
  if (files.has(path)) return;
  const data = await readFile(path);
  files.set(path, hash(data));
  for (const match of data.toString().matchAll(/(?:from\s+|import\s*)["'](\.\.?\/[^"']+)["']/g)) {
    await collect(resolve(dirname(path), match[1]));
  }
}
await collect(resolve(producer, 'dist/ocel.js'));
const { exportOcel } = await import(pathToFileURL(resolve(producer, 'dist/ocel.js')).href);
const original = await readFile(resolve(here, 'source/observation-bundle.json'));
const bundle = JSON.parse(original);
const exported = exportOcel(bundle);
assert.equal(exported.document.events.length, bundle.events.length);
for (const [path, digest] of files) assert.equal(hash(await readFile(path)), digest, 'Changed imported module: ' + path);
for (const name of ['src/ocel.ts', 'src/observation.ts', 'package.json', 'pnpm-lock.yaml', 'bun.lock']) {
  const path = resolve(producer, name); files.set(path, hash(await readFile(path)));
}
const git = (...args) => execFileSync('git', ['-C', producer, ...args], { encoding: 'utf8' }).trim();
const record = {
  operation: 'exportOcel on historical immutable bundle only', node: process.version,
  producerCheckoutHead: git('rev-parse', 'HEAD'), sourceBundleSha256: hash(original),
  moduleHashes: Object.fromEntries([...files].map(([p, h]) => [relative(producer, p).replaceAll('\\', '/'), h])),
  scriptSha256: hash(await readFile(fileURLToPath(import.meta.url))),
  sourceRunHistorical: 'See copied start.json and result.json; exporter execution is later and separate',
  metadata: { ...exported, document: undefined },
};
await writeFile(resolve(here, 'export.json'), JSON.stringify(exported, null, 2) + '\n', { flag: 'wx' });
await writeFile(resolve(here, 'actual.ocel.json'), JSON.stringify(exported.document, null, 2) + '\n', { flag: 'wx' });
await writeFile(resolve(here, 'export-record.json'), JSON.stringify(record, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ mapping: exported.mapping, events: exported.document.events.length, objects: exported.document.objects.length, sourceDigest: exported.sourceDigest, digest: exported.digest, moduleCount: files.size }));
