import {execFileSync} from 'node:child_process';
import {existsSync, readFileSync, statSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const repo = path.resolve(root, '../..');
const locales = ['en', 'zh-CN', 'ja', 'ko', 'ru'];
const slugs = [
  'hero',
  'overview',
  'features',
  'installation',
  'initialization',
  'usage',
  'devices',
  'compatibility',
  'contributing',
];
const readmes = [
  ['README.md', './docs/assets/en/'],
  ['docs/README.zh-CN.md', './assets/zh-CN/'],
  ['docs/README.ja.md', './assets/ja/'],
  ['docs/README.ko.md', './assets/ko/'],
  ['docs/README.ru.md', './assets/ru/'],
  ['README_CN.md', './docs/assets/zh-CN/'],
];

const failures = [];
const rows = [];

const dimensionOf = (file) => {
  const output = execFileSync('ffprobe', [
    '-v',
    'error',
    '-select_streams',
    'v:0',
    '-show_entries',
    'stream=width,height',
    '-of',
    'csv=s=x:p=0',
    file,
  ])
    .toString()
    .trim();
  return output;
};

const numberConstant = (text, name) => {
  const match = text.match(new RegExp(`export const ${name} = (\\d+);`));
  if (!match) throw new Error(`Missing layout constant ${name}`);
  return Number(match[1]);
};

const layoutText = readFileSync(path.join(root, 'src/layout.ts'), 'utf8');
const layout = Object.fromEntries(
  [
    'CANVAS_WIDTH',
    'CANVAS_HEIGHT',
    'CONTENT_SAFE_MARGIN',
    'LEFT_PANEL_BOTTOM',
    'LEFT_PANEL_ENTER_Y',
    'PREVIEW_TOP',
    'PREVIEW_HEIGHT',
    'CONSTELLATION_BOTTOM',
    'FOOTER_BOTTOM',
    'FOOTER_ENTER_Y',
    'FOOTER_HEIGHT',
  ].map((name) => [name, numberConstant(layoutText, name)]),
);

if (layout.CANVAS_WIDTH !== 720 || layout.CANVAS_HEIGHT !== 404) {
  failures.push(`unexpected canvas ${layout.CANVAS_WIDTH}x${layout.CANVAS_HEIGHT}`);
}
if (layout.LEFT_PANEL_BOTTOM - layout.LEFT_PANEL_ENTER_Y < layout.CONTENT_SAFE_MARGIN) {
  failures.push('left chip row can animate below the bottom safe margin');
}
if (layout.FOOTER_BOTTOM - layout.FOOTER_ENTER_Y < layout.CONTENT_SAFE_MARGIN) {
  failures.push('footer path badge can animate below the bottom safe margin');
}
if (
  layout.PREVIEW_TOP + layout.PREVIEW_HEIGHT >
  layout.CANVAS_HEIGHT - layout.CONTENT_SAFE_MARGIN
) {
  failures.push('preview card/callout exceeds the bottom safe margin');
}
if (layout.CONSTELLATION_BOTTOM < layout.CONTENT_SAFE_MARGIN) {
  failures.push('device constellation exceeds the bottom safe margin');
}

for (const locale of locales) {
  for (const slug of slugs) {
    const source = path.join(root, 'public/source', locale, `${slug}.png`);
    const gif = path.join(repo, 'docs/assets', locale, `${slug}.gif`);
    const oldPng = path.join(repo, 'docs/assets', locale, `${slug}.png`);
    if (!existsSync(source)) failures.push(`missing source copy: ${source}`);
    if (!existsSync(gif)) failures.push(`missing gif: ${gif}`);
    if (existsSync(oldPng)) failures.push(`old final png still exists: ${oldPng}`);
    if (existsSync(gif)) {
      const size = statSync(gif).size;
      const dims = dimensionOf(gif);
      if (dims !== '720x404') failures.push(`bad dimensions ${dims}: ${gif}`);
      if (size > 2_500_000) failures.push(`gif too large ${size}: ${gif}`);
      rows.push(`${locale}/${slug}.gif ${dims} ${(size / 1024).toFixed(1)} KiB`);
    }
    const still = path.join(root, 'stills', `${locale}-${slug}-frame32.png`);
    if (!existsSync(still)) failures.push(`missing QA still: ${still}`);
    if (existsSync(still)) {
      const dims = dimensionOf(still);
      if (dims !== '720x404') failures.push(`bad still dimensions ${dims}: ${still}`);
    }
  }
}

for (const [file, prefix] of readmes) {
  const full = path.join(repo, file);
  const text = readFileSync(full, 'utf8');
  for (const slug of slugs) {
    const ref = `${prefix}${slug}.gif`;
    if (!text.includes(ref)) failures.push(`${file} missing ref ${ref}`);
    const resolved = file.startsWith('docs/')
      ? path.join(repo, 'docs', prefix.replace('./', ''), `${slug}.gif`)
      : path.join(repo, prefix.replace('./', ''), `${slug}.gif`);
    if (!existsSync(resolved)) failures.push(`${file} points to missing file ${resolved}`);
  }
  if (/docs\/example.*\.png/.test(text) || /assets\/.*\.png/.test(text)) {
    failures.push(`${file} still contains old README png refs`);
  }
}

for (const legacy of [
  'example-configuration.png',
  'example-image.png',
  'example-image-2.png',
  'example-image-3.png',
  'example-image-4.png',
]) {
  const target = path.join(repo, legacy.startsWith('docs/') ? legacy : 'docs', legacy);
  if (existsSync(target)) failures.push(`legacy example image still exists: ${target}`);
}

const dataText = readFileSync(path.join(root, 'src/data.ts'), 'utf8');
const longBody = [...dataText.matchAll(/body: '([^']+)'/g)].filter(
  (match) => match[1].length > 150,
);
const longTitle = [...dataText.matchAll(/title: '([^']+)'/g)].filter(
  (match) => match[1].length > 52,
);
if (longBody.length > 0) failures.push(`body text estimate over bound: ${longBody.length}`);
if (longTitle.length > 0) failures.push(`title text estimate over bound: ${longTitle.length}`);

console.log(rows.join('\n'));

if (failures.length > 0) {
  console.error('\nValidation failures:');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log('\nValidation passed.');
