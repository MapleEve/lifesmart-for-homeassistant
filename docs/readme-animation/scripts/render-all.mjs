import {spawnSync} from 'node:child_process';
import {existsSync, mkdirSync, rmSync, statSync} from 'node:fs';
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

const run = (cmd, args) => {
  const result = spawnSync(cmd, args, {cwd: root, stdio: 'inherit'});
  if (result.status !== 0) {
    throw new Error(`${cmd} ${args.join(' ')} failed with ${result.status}`);
  }
};

mkdirSync(path.join(root, 'render'), {recursive: true});

for (const locale of locales) {
  mkdirSync(path.join(repo, 'docs/assets', locale), {recursive: true});
  for (const slug of slugs) {
    const id = `readme-${locale}-${slug}`;
    const mp4 = path.join(root, 'render', `${locale}-${slug}.mp4`);
    const gif = path.join(repo, 'docs/assets', locale, `${slug}.gif`);
    const palette = path.join(root, 'render', `${locale}-${slug}-palette.png`);
    rmSync(mp4, {force: true});
    rmSync(gif, {force: true});
    rmSync(palette, {force: true});

    run('npx', [
      'remotion',
      'render',
      'src/index.tsx',
      id,
      mp4,
      '--codec=h264',
      '--crf=28',
      '--pixel-format=yuv420p',
      '--overwrite',
      '--concurrency=1',
      '--log=warn',
    ]);

    run('ffmpeg', [
      '-y',
      '-loglevel',
      'error',
      '-i',
      mp4,
      '-vf',
      'fps=12,scale=720:404:flags=lanczos,palettegen=max_colors=96:stats_mode=diff',
      '-update',
      '1',
      '-frames:v',
      '1',
      palette,
    ]);
    run('ffmpeg', [
      '-y',
      '-loglevel',
      'error',
      '-i',
      mp4,
      '-i',
      palette,
      '-lavfi',
      'fps=12,scale=720:404:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle',
      '-loop',
      '0',
      gif,
    ]);

    if (!existsSync(gif) || statSync(gif).size === 0) {
      throw new Error(`Missing rendered GIF: ${gif}`);
    }
  }
}
