import {CANVAS_HEIGHT, CANVAS_WIDTH} from './layout';

export const COMPOSITION = {
  width: CANVAS_WIDTH,
  height: CANVAS_HEIGHT,
  fps: 12,
  durationInFrames: 42,
} as const;

export const SECTIONS = [
  {slug: 'hero', accent: '#18d3a4', icon: 'LS'},
  {slug: 'overview', accent: '#4ec9ff', icon: 'OV'},
  {slug: 'features', accent: '#ffd166', icon: 'FX'},
  {slug: 'installation', accent: '#ff8a4c', icon: 'HC'},
  {slug: 'initialization', accent: '#9df871', icon: 'IN'},
  {slug: 'usage', accent: '#9bbcff', icon: 'IR'},
  {slug: 'devices', accent: '#ff73a8', icon: 'DV'},
  {slug: 'compatibility', accent: '#b28dff', icon: 'QA'},
  {slug: 'contributing', accent: '#78f6ff', icon: 'PR'},
] as const;

export type SectionSlug = (typeof SECTIONS)[number]['slug'];

type SectionCopy = {
  kicker: string;
  title: string;
  body: string;
  stats: string[];
  callout: string;
};

type LocaleCopy = {
  id: string;
  folder: string;
  language: string;
  brandLine: string;
  sections: Record<SectionSlug, SectionCopy>;
};

export const LOCALES: LocaleCopy[] = [
  {
    id: 'en',
    folder: 'en',
    language: 'English',
    brandLine: 'LifeSmart x Home Assistant',
    sections: {
      hero: {
        kicker: 'Smart home bridge',
        title: 'LifeSmart IoT Integration',
        body: 'Cloud and local LifeSmart devices, discovery, scenes, IR control, and resilient Home Assistant compatibility.',
        stats: ['Cloud + Local', '704+ tests', 'HA 2023.6.3+'],
        callout: 'README-ready animated preview',
      },
      overview: {
        kicker: 'Overview',
        title: 'One integration for the LifeSmart home',
        body: 'Connect hubs, switches, sensors, locks, SPOT devices, cameras, and services through a single Home Assistant workflow.',
        stats: ['Discovery', 'HACS updates', 'Service automation'],
        callout: 'Unified control surface',
      },
      features: {
        kicker: 'Feature map',
        title: 'Dual mode, broad device support',
        body: 'Choose LifeSmart Cloud API or local Hub mode, then automate regions, scenes, IR keys, switches, lights, sockets, and curtains.',
        stats: ['Multi-region', 'Advanced services', 'Device matrix'],
        callout: 'Built for daily automation',
      },
      installation: {
        kicker: 'Install path',
        title: 'Add through HACS in minutes',
        body: 'Search LifeSmart for Home Assistant, install the integration, restart Home Assistant, then start the configuration flow.',
        stats: ['HACS default', 'One-click add', 'Fast updates'],
        callout: 'Clear install path',
      },
      initialization: {
        kicker: 'Setup',
        title: 'Cloud credentials or local Hub',
        body: 'Use App Key, App Token, user identity, and region for Cloud mode, or local IP, port, username, and password for Hub mode.',
        stats: ['Token login', 'Password refresh', 'Local TCP'],
        callout: 'Two connection profiles',
      },
      usage: {
        kicker: 'Services',
        title: 'IR, scenes, and momentary switch control',
        body: 'Send IR and A/C commands, trigger LifeSmart scenes, and press switch entities directly from Home Assistant service calls.',
        stats: ['send_ir_keys', 'send_ac_key', 'scene trigger'],
        callout: 'Automation-first services',
      },
      devices: {
        kicker: 'Device support',
        title: 'Switches, sensors, locks, lights, SPOT',
        body: 'A wide LifeSmart catalog is mapped into Home Assistant entities with consistent platform behavior and state updates.',
        stats: ['Switches', 'Curtains', 'Cameras'],
        callout: 'Catalog-scale coverage',
      },
      compatibility: {
        kicker: 'Compatibility',
        title: 'Validated across Home Assistant versions',
        body: 'Compatibility layers cover WebSocket timeouts, climate features, service call constructors, and multiple Python baselines.',
        stats: ['2023.6.0', '2024.12.0', '2026.05'],
        callout: '704/704 test signal',
      },
      contributing: {
        kicker: 'Contributing',
        title: 'Structured development workflow',
        body: 'Clone the repository, use isolated environments, keep formatting consistent, and add tests for user-facing changes.',
        stats: ['Black', 'Flake8', 'PR template'],
        callout: 'Ready for maintainers',
      },
    },
  },
  {
    id: 'zh-CN',
    folder: 'zh-CN',
    language: '简体中文',
    brandLine: 'LifeSmart x Home Assistant',
    sections: {
      hero: {
        kicker: '智能家居桥接',
        title: 'LifeSmart 智能家居',
        body: '连接云端与本地设备，支持自动发现、场景、红外控制与 Home Assistant 兼容层。',
        stats: ['云端 + 本地', '704+ 测试', 'HA 2023.6.3+'],
        callout: 'README 动态预览',
      },
      overview: {
        kicker: '概述',
        title: '全屋设备统一接入',
        body: '统一接入 Hub、开关、传感器、门锁、SPOT、摄像头与服务，形成清晰工作流。',
        stats: ['自动发现', 'HACS 更新', '服务自动化'],
        callout: '统一控制入口',
      },
      features: {
        kicker: '功能图谱',
        title: '双模式连接',
        body: '选择云 API 或本地 Hub，管理区域、场景、红外键码、开关、灯光、插座与窗帘。',
        stats: ['多区域', '高级服务', '设备矩阵'],
        callout: '面向日常自动化',
      },
      installation: {
        kicker: '安装路径',
        title: '通过 HACS 快速添加',
        body: '搜索 LifeSmart for Home Assistant，安装后重启 Home Assistant，再进入添加集成流程。',
        stats: ['HACS 默认', '一键添加', '快速更新'],
        callout: '安装路径清晰',
      },
      initialization: {
        kicker: '初始化',
        title: '云端或本地 Hub',
        body: '云端填写 App Key、Token、用户与区域；本地填写 Hub IP、端口、用户名与密码。',
        stats: ['Token 登录', '密码刷新', '本地 TCP'],
        callout: '两类连接配置',
      },
      usage: {
        kicker: '服务调用',
        title: '红外与场景控制',
        body: '通过 Home Assistant 服务发送红外和空调键码，触发场景，或执行开关瞬时按压。',
        stats: ['红外键码', '空调控制', '场景触发'],
        callout: '自动化优先',
      },
      devices: {
        kicker: '设备支持',
        title: '设备类型覆盖',
        body: '设备目录映射到 Home Assistant 实体，并保持一致的平台行为和状态更新。',
        stats: ['开关', '窗帘', '摄像头'],
        callout: '目录级覆盖',
      },
      compatibility: {
        kicker: '兼容性',
        title: '多版本兼容验证',
        body: '兼容层覆盖 WebSocket 超时、气候实体、服务调用构造，以及多 Python 基线。',
        stats: ['2023.6.0', '2024.12.0', '2026.05'],
        callout: '704/704 测试信号',
      },
      contributing: {
        kicker: '开发贡献',
        title: '结构化开发流程',
        body: '克隆仓库，使用隔离环境，保持格式一致，并为面向用户的变更补充测试。',
        stats: ['Black', 'Flake8', 'PR 模板'],
        callout: '便于维护者接手',
      },
    },
  },
  {
    id: 'ja',
    folder: 'ja',
    language: '日本語',
    brandLine: 'LifeSmart x Home Assistant',
    sections: {
      hero: {
        kicker: 'スマートホーム連携',
        title: 'LifeSmart IoT 連携',
        body: 'クラウドとローカルのデバイス、検出、シーン、IR 制御、Home Assistant 互換性をまとめます。',
        stats: ['Cloud + Local', '704+ tests', 'HA 2023.6.3+'],
        callout: 'README 用アニメーション',
      },
      overview: {
        kicker: '概要',
        title: '全デバイスを一元管理',
        body: 'Hub、スイッチ、センサー、ロック、SPOT、カメラ、サービスを一つの流れに統合します。',
        stats: ['自動検出', 'HACS 更新', 'サービス自動化'],
        callout: '統一された操作面',
      },
      features: {
        kicker: '機能',
        title: '二つの接続モード',
        body: 'Cloud API またはローカル Hub で、地域、シーン、IR、スイッチ、照明、カーテンを扱えます。',
        stats: ['複数地域', '高度なサービス', 'デバイス一覧'],
        callout: '日常自動化向け',
      },
      installation: {
        kicker: 'インストール',
        title: 'HACS ですばやく追加',
        body: 'LifeSmart for Home Assistant を検索し、インストール後に再起動して追加フローを開始します。',
        stats: ['HACS default', 'ワンクリック', '簡単更新'],
        callout: '明確な導入手順',
      },
      initialization: {
        kicker: '初期設定',
        title: 'クラウドまたは Hub',
        body: 'Cloud は App Key、Token、ユーザー、地域を使い、Local は Hub IP、ポート、ログイン情報を使います。',
        stats: ['Token login', 'Password refresh', 'Local TCP'],
        callout: '二つの接続設定',
      },
      usage: {
        kicker: 'サービス',
        title: 'IR とシーン制御',
        body: 'Home Assistant から IR、エアコン操作、LifeSmart シーン起動、スイッチ押下を実行できます。',
        stats: ['IR keys', 'A/C control', 'Scene trigger'],
        callout: '自動化優先',
      },
      devices: {
        kicker: 'デバイス',
        title: '幅広いデバイス対応',
        body: 'LifeSmart カタログを Home Assistant エンティティへ対応付け、状態更新を一貫させます。',
        stats: ['Switches', 'Curtains', 'Cameras'],
        callout: 'カタログ規模の対応',
      },
      compatibility: {
        kicker: '互換性',
        title: '複数バージョン検証',
        body: 'WebSocket、気候エンティティ、サービス呼び出し、Python 基準を互換レイヤーで吸収します。',
        stats: ['2023.6.0', '2024.12.0', '2026.05'],
        callout: '704/704 のテスト信号',
      },
      contributing: {
        kicker: 'コントリビューション',
        title: '開発フローを整備',
        body: '隔離環境を使い、形式を保ち、ユーザー向け変更にはテストを追加します。',
        stats: ['Black', 'Flake8', 'PR template'],
        callout: '保守者が扱いやすい',
      },
    },
  },
  {
    id: 'ko',
    folder: 'ko',
    language: '한국어',
    brandLine: 'LifeSmart x Home Assistant',
    sections: {
      hero: {
        kicker: '스마트 홈 브리지',
        title: 'LifeSmart IoT 통합',
        body: '클라우드와 로컬 LifeSmart 기기, 자동 발견, 장면, IR 제어, Home Assistant 호환성을 연결합니다.',
        stats: ['Cloud + Local', '704+ tests', 'HA 2023.6.3+'],
        callout: 'README용 애니메이션',
      },
      overview: {
        kicker: '개요',
        title: '홈 기기 통합 관리',
        body: 'Hub, 스위치, 센서, 잠금장치, SPOT, 카메라, 서비스를 하나의 워크플로로 묶습니다.',
        stats: ['자동 발견', 'HACS 업데이트', '서비스 자동화'],
        callout: '통합 제어 화면',
      },
      features: {
        kicker: '기능 지도',
        title: '두 가지 연결 모드',
        body: 'Cloud API 또는 로컬 Hub로 지역, 장면, IR 키, 스위치, 조명, 커튼을 자동화합니다.',
        stats: ['다중 지역', '고급 서비스', '기기 매트릭스'],
        callout: '일상 자동화용',
      },
      installation: {
        kicker: '설치',
        title: 'HACS로 빠르게 추가',
        body: 'LifeSmart for Home Assistant를 검색해 설치하고 재시작한 뒤 통합 추가 흐름을 시작합니다.',
        stats: ['HACS 기본', '원클릭 추가', '빠른 업데이트'],
        callout: '명확한 설치 경로',
      },
      initialization: {
        kicker: '초기 설정',
        title: '클라우드 또는 로컬 Hub',
        body: 'Cloud는 App Key, Token, 사용자와 지역을 쓰고 Local은 Hub IP와 로그인 정보를 씁니다.',
        stats: ['Token login', 'Password refresh', 'Local TCP'],
        callout: '두 가지 연결 프로필',
      },
      usage: {
        kicker: '서비스',
        title: 'IR·장면 제어',
        body: 'Home Assistant 서비스에서 IR, 에어컨 명령, LifeSmart 장면 실행, 스위치 누름을 처리합니다.',
        stats: ['IR keys', 'A/C control', 'Scene trigger'],
        callout: '자동화 중심 서비스',
      },
      devices: {
        kicker: '기기 지원',
        title: '폭넓은 기기 지원',
        body: 'LifeSmart 카탈로그를 Home Assistant 엔티티로 매핑해 상태 업데이트를 일관되게 제공합니다.',
        stats: ['Switches', 'Curtains', 'Cameras'],
        callout: '카탈로그 규모 지원',
      },
      compatibility: {
        kicker: '호환성',
        title: '다중 버전 검증',
        body: 'WebSocket, climate 기능, 서비스 호출, Python 기준을 호환성 계층으로 처리합니다.',
        stats: ['2023.6.0', '2024.12.0', '2026.05'],
        callout: '704/704 테스트 신호',
      },
      contributing: {
        kicker: '개발 기여',
        title: '구조화된 개발 흐름',
        body: '격리 환경을 사용하고 형식을 유지하며 사용자 변경에는 테스트를 추가합니다.',
        stats: ['Black', 'Flake8', 'PR template'],
        callout: '유지보수자 친화적',
      },
    },
  },
  {
    id: 'ru',
    folder: 'ru',
    language: 'Русский',
    brandLine: 'LifeSmart x Home Assistant',
    sections: {
      hero: {
        kicker: 'Мост умного дома',
        title: 'Интеграция LifeSmart',
        body: 'Объединяет облачные и локальные устройства, обнаружение, сцены, IR-команды и совместимость Home Assistant.',
        stats: ['Cloud + Local', '704+ tests', 'HA 2023.6.3+'],
        callout: 'Анимация для README',
      },
      overview: {
        kicker: 'Обзор',
        title: 'Единый дом LifeSmart',
        body: 'Hub, выключатели, сенсоры, замки, SPOT, камеры и сервисы подключаются в единый поток Home Assistant.',
        stats: ['Автообнаружение', 'HACS updates', 'Автоматизация'],
        callout: 'Единая панель',
      },
      features: {
        kicker: 'Функции',
        title: 'Два режима подключения',
        body: 'Выбирайте Cloud API или локальный Hub и автоматизируйте регионы, сцены, IR, выключатели, свет, розетки и шторы.',
        stats: ['Регионы', 'Сервисы', 'Матрица устройств'],
        callout: 'Для ежедневной автоматизации',
      },
      installation: {
        kicker: 'Установка',
        title: 'Быстро через HACS',
        body: 'Найдите LifeSmart for Home Assistant, установите интеграцию, перезапустите Home Assistant и запустите настройку.',
        stats: ['HACS default', 'Один клик', 'Быстрые обновления'],
        callout: 'Понятный путь установки',
      },
      initialization: {
        kicker: 'Настройка',
        title: 'Облако или локальный Hub',
        body: 'Для Cloud укажите App Key, App Token, пользователя и регион; для Local укажите IP Hub, порт, логин и пароль.',
        stats: ['Token login', 'Password refresh', 'Local TCP'],
        callout: 'Два профиля подключения',
      },
      usage: {
        kicker: 'Сервисы',
        title: 'IR и сцены',
        body: 'Сервисы Home Assistant отправляют IR и A/C команды, запускают сцены LifeSmart и выполняют нажатие выключателя.',
        stats: ['IR keys', 'A/C control', 'Scene trigger'],
        callout: 'Сервисы для автоматизации',
      },
      devices: {
        kicker: 'Устройства',
        title: 'Поддержка устройств',
        body: 'Каталог LifeSmart сопоставляется с сущностями Home Assistant с единым поведением платформ и обновлением состояний.',
        stats: ['Switches', 'Curtains', 'Cameras'],
        callout: 'Покрытие каталога',
      },
      compatibility: {
        kicker: 'Совместимость',
        title: 'Проверка версий HA',
        body: 'Слои совместимости покрывают WebSocket timeout, climate features, service calls и несколько баз Python.',
        stats: ['2023.6.0', '2024.12.0', '2026.05'],
        callout: 'Сигнал тестов 704/704',
      },
      contributing: {
        kicker: 'Вклад',
        title: 'Процесс разработки',
        body: 'Клонируйте репозиторий, используйте изолированные окружения, сохраняйте формат и добавляйте тесты.',
        stats: ['Black', 'Flake8', 'PR template'],
        callout: 'Удобно для поддержки',
      },
    },
  },
];

export const getSection = (slug: SectionSlug) => {
  const section = SECTIONS.find((item) => item.slug === slug);
  if (!section) {
    throw new Error(`Unknown section: ${slug}`);
  }
  return section;
};

export const getLocale = (id: string) => {
  const locale = LOCALES.find((item) => item.id === id);
  if (!locale) {
    throw new Error(`Unknown locale: ${id}`);
  }
  return locale;
};
