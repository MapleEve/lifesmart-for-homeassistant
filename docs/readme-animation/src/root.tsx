import {Composition, Folder} from 'remotion';
import {ReadmeAnimation} from './scene';
import {COMPOSITION, LOCALES, SECTIONS} from './data';

export const RemotionRoot = () => {
  return (
    <>
      {LOCALES.map((locale) => (
        <Folder key={locale.id} name={locale.folder}>
          {SECTIONS.map((section) => (
            <Composition
              key={`${locale.id}-${section.slug}`}
              id={`readme-${locale.id}-${section.slug}`}
              component={ReadmeAnimation}
              durationInFrames={COMPOSITION.durationInFrames}
              fps={COMPOSITION.fps}
              width={COMPOSITION.width}
              height={COMPOSITION.height}
              defaultProps={{
                localeId: locale.id,
                sectionSlug: section.slug,
              }}
            />
          ))}
        </Folder>
      ))}
    </>
  );
};
