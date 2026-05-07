import {spawnSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
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

mkdirSync(path.join(root, 'stills'), {recursive: true});

for (const locale of locales) {
  for (const slug of slugs) {
    const out = path.join(root, 'stills', `${locale}-${slug}-frame32.png`);
    const result = spawnSync(
      'npx',
      [
        'remotion',
        'still',
        'src/index.tsx',
        `readme-${locale}-${slug}`,
        out,
        '--frame=32',
        '--overwrite',
        '--log=warn',
      ],
      {cwd: root, stdio: 'inherit'},
    );
    if (result.status !== 0) {
      throw new Error(`Still render failed for ${locale}/${slug}`);
    }
  }
}
