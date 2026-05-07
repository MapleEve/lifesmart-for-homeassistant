import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {getLocale, getSection, SectionSlug} from './data';
import {
  CANVAS_HEIGHT,
  CANVAS_WIDTH,
  FRAME_INSET,
  LEFT_PANEL_BOTTOM,
  LEFT_PANEL_ENTER_Y,
  LEFT_PANEL_LEFT,
  LEFT_PANEL_TOP,
  LEFT_PANEL_WIDTH,
  PREVIEW_HEIGHT,
  PREVIEW_RIGHT,
  PREVIEW_TOP,
  PREVIEW_WIDTH,
} from './layout';

type ReadmeAnimationProps = {
  localeId: string;
  sectionSlug: SectionSlug;
};

const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

const clamp = (
  frame: number,
  input: [number, number],
  output: [number, number],
) =>
  interpolate(frame, input, output, {
    easing: easeOut,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const hasDenseScript = (text: string) =>
  /[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/.test(text);

const titleSize = (text: string) => {
  if (hasDenseScript(text)) {
    if (text.length > 20) {
      return 27;
    }
    if (text.length > 15) {
      return 30;
    }
    return 32;
  }
  if (text.length > 42) {
    return 26;
  }
  if (text.length > 34) {
    return 29;
  }
  if (text.length > 26) {
    return 32;
  }
  return 36;
};

const bodySize = (text: string) => {
  if (hasDenseScript(text)) {
    return text.length > 84 ? 14 : 15;
  }
  if (text.length > 126) {
    return 15;
  }
  if (text.length > 96) {
    return 16;
  }
  return 17;
};

const brandFont =
  '"Avenir Next", "SF Pro Display", "PingFang SC", "Hiragino Sans", "Apple SD Gothic Neo", "Noto Sans CJK SC", "Noto Sans JP", "Noto Sans KR", "Arial", sans-serif';

const monoFont = '"SF Mono", "JetBrains Mono", "Menlo", monospace';

export const ReadmeAnimation = ({
  localeId,
  sectionSlug,
}: ReadmeAnimationProps) => {
  const frame = useCurrentFrame();
  const locale = getLocale(localeId);
  const section = getSection(sectionSlug);
  const copy = locale.sections[sectionSlug];
  const denseTitle = hasDenseScript(copy.title);
  const denseBody = hasDenseScript(copy.body);
  const enter = clamp(frame, [0, 18], [0, 1]);
  const second = clamp(frame, [8, 26], [0, 1]);
  const shimmer = clamp(frame, [12, 34], [0, 1]);
  const sourcePath = `source/${locale.id}/${section.slug}.png`;

  return (
    <AbsoluteFill
      style={{
        overflow: 'hidden',
        background:
          'radial-gradient(circle at 20% 15%, #113f39 0, #0f2a35 30%, #0b111d 72%)',
        color: '#f7fffb',
        fontFamily: brandFont,
      }}
    >
      <svg
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        style={{position: 'absolute', inset: 0}}
      >
        <defs>
          <linearGradient id="brandSweep" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor={section.accent} stopOpacity="0.74" />
            <stop offset="52%" stopColor="#6fffe2" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0.08" />
          </linearGradient>
          <pattern id="mesh" width="34" height="34" patternUnits="userSpaceOnUse">
            <path
              d="M 34 0 L 0 0 0 34"
              fill="none"
              stroke="#d9fff3"
              strokeOpacity="0.055"
              strokeWidth="1"
            />
          </pattern>
        </defs>
        <rect width={CANVAS_WIDTH} height={CANVAS_HEIGHT} fill="url(#mesh)" />
        <circle
          cx={120 + shimmer * 34}
          cy={68}
          r={118}
          fill={section.accent}
          opacity="0.14"
        />
        <circle cx="620" cy="340" r="168" fill="#5bd8ff" opacity="0.08" />
        <path
          d="M-40 315 C130 248 184 408 348 312 C502 222 566 260 760 186"
          stroke="url(#brandSweep)"
          strokeWidth="80"
          strokeLinecap="round"
          fill="none"
          opacity="0.27"
        />
      </svg>

      <div
        style={{
          position: 'absolute',
          inset: FRAME_INSET,
          borderRadius: 34,
          outline: '1px solid rgba(255,255,255,0.16)',
          background:
            'linear-gradient(135deg, rgba(255,255,255,0.11), rgba(255,255,255,0.035))',
          boxShadow: '0 28px 72px rgba(0,0,0,0.38)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: LEFT_PANEL_LEFT,
          top: LEFT_PANEL_TOP,
          bottom: LEFT_PANEL_BOTTOM,
          width: LEFT_PANEL_WIDTH,
          display: 'flex',
          flexDirection: 'column',
          transform: `translateY(${(1 - enter) * LEFT_PANEL_ENTER_Y}px)`,
          opacity: enter,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            marginBottom: 18,
            flexShrink: 0,
          }}
        >
          <div
            style={{
              width: 50,
              height: 50,
              borderRadius: 18,
              display: 'grid',
              placeItems: 'center',
              color: '#092015',
              fontFamily: monoFont,
              fontSize: 17,
              fontWeight: 900,
              letterSpacing: -1,
              background: `linear-gradient(135deg, ${section.accent}, #effff9)`,
              boxShadow: `0 0 32px ${section.accent}66`,
            }}
          >
            {section.icon}
          </div>
          <div style={{fontSize: 15, fontWeight: 750}}>{locale.brandLine}</div>
        </div>

        <div
          style={{
            color: section.accent,
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: 2.3,
              textTransform: 'uppercase',
              marginBottom: 8,
            }}
        >
          {copy.kicker}
        </div>
        <div
          style={{
            fontSize: titleSize(copy.title),
            lineHeight: denseTitle ? 1.14 : 1.02,
            letterSpacing: denseTitle ? -0.45 : -1.2,
            fontWeight: 900,
            marginBottom: 12,
            maxWidth: 286,
            wordBreak: denseTitle ? 'keep-all' : 'normal',
            overflowWrap: denseTitle ? 'normal' : 'break-word',
          }}
        >
          {copy.title}
        </div>
        <div
          style={{
            fontSize: bodySize(copy.body),
            lineHeight: denseBody ? 1.42 : 1.3,
            color: 'rgba(247,255,251,0.78)',
            fontWeight: 520,
            maxWidth: 286,
            wordBreak: denseBody ? 'keep-all' : 'normal',
            overflowWrap: 'break-word',
          }}
        >
          {copy.body}
        </div>

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 8,
            marginTop: 'auto',
            paddingTop: 14,
            flexShrink: 0,
          }}
        >
          {copy.stats.map((stat, index) => (
            <div
              key={stat}
              style={{
                padding: '6px 9px',
                borderRadius: 999,
                fontSize: 11,
                lineHeight: 1.2,
                fontWeight: 800,
                whiteSpace: 'nowrap',
                background:
                  index === 0
                    ? `${section.accent}30`
                    : 'rgba(255,255,255,0.09)',
                color: index === 0 ? '#ffffff' : 'rgba(247,255,251,0.82)',
                outline: `1px solid ${
                  index === 0 ? section.accent : 'rgba(255,255,255,0.12)'
                }`,
              }}
            >
              {stat}
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          right: PREVIEW_RIGHT,
          top: PREVIEW_TOP,
          width: PREVIEW_WIDTH,
          height: PREVIEW_HEIGHT,
          borderRadius: 28,
          overflow: 'hidden',
          background: 'rgba(5,13,22,0.62)',
          outline: '1px solid rgba(255,255,255,0.16)',
          transform: `translateX(${(1 - second) * 24}px) scale(${
            0.985 + second * 0.015
          })`,
          opacity: 0.22 + second * 0.78,
          boxShadow: '0 30px 64px rgba(0,0,0,0.44)',
        }}
      >
        <Img
          src={staticFile(sourcePath)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.58,
            filter: 'saturate(1.12) contrast(1.05)',
            transform: `scale(${1.035 - second * 0.015})`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(135deg, rgba(6,22,26,0.05), rgba(6,11,20,0.64))',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 16,
            top: 14,
            display: 'flex',
            gap: 7,
          }}
        >
          {[0, 1, 2].map((item) => (
            <span
              key={item}
              style={{
                width: 8,
                height: 8,
                borderRadius: 99,
                background:
                  item === 0 ? section.accent : 'rgba(255,255,255,0.44)',
              }}
            />
          ))}
        </div>
        <div
          style={{
            position: 'absolute',
            left: 18,
            bottom: 18,
            right: 18,
            borderRadius: 20,
            padding: '13px 15px',
            background: 'rgba(2,10,18,0.72)',
            outline: '1px solid rgba(255,255,255,0.12)',
          }}
        >
          <div
            style={{
              color: section.accent,
              fontSize: 11,
              fontWeight: 850,
              letterSpacing: 1.4,
              marginBottom: 5,
            }}
          >
            {copy.callout}
          </div>
          <div
            style={{
              height: 6,
              borderRadius: 99,
              background: 'rgba(255,255,255,0.14)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${Math.round(42 + shimmer * 58)}%`,
                borderRadius: 99,
                background: `linear-gradient(90deg, ${section.accent}, #ffffff)`,
              }}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
