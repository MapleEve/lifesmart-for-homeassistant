# LifeSmart IoT Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
![GitHub License](https://img.shields.io/github/license/MapleEve/lifesmart-for-homeassistant)
[![version](https://img.shields.io/github/manifest-json/v/MapleEve/lifesmart-for-homeassistant?filename=custom_components%2Flifesmart%2Fmanifest.json)](https://github.com/MapleEve/lifesmart-for-homeassistant/releases/latest)
[![stars](https://img.shields.io/github/stars/MapleEve/lifesmart-for-homeassistant)](https://github.com/MapleEve/lifesmart-for-homeassistant/stargazers)
[![issues](https://img.shields.io/github/issues/MapleEve/lifesmart-for-homeassistant)](https://github.com/MapleEve/lifesmart-for-homeassistant/issues)
![haasfestworkflow](https://github.com/MapleEve/lifesmart-for-homeassistant/actions/workflows/haas-vali.yml/badge.svg)
![hacsworkflow](https://github.com/MapleEve/lifesmart-for-homeassistant/actions/workflows/hacs-vali.yml/badge.svg)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FMapleEve%2Flifesmart-for-homeassistant.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FMapleEve%2Flifesmart-for-homeassistant?ref=badge_shield)

> 中文版可以查看 [中文说明](./README_CN.md).

---

## Overview

LifeSmart for Home Assistant integrates LifeSmart smart home devices with Home Assistant. It supports both Cloud and
Local modes, automatic device discovery, and advanced automation via Home Assistant services. The integration supports a
wide range of LifeSmart devices, including switches, sensors, locks, controllers, SPOT devices, and cameras.
Installation and updates are available via HACS.

---

## Core Features

- **Dual Connection Modes**: Cloud and Local modes (choose between LifeSmart API or local Hub)
- **Comprehensive Device Support**: Switches, sensors, locks, controllers, sockets, curtain motors, lights, SPOT,
  cameras
- **Advanced Services**: Send IR keys (including A/C), trigger LifeSmart scenes, momentary switch press
- **Multi-region Support**: China, North America, Europe, Japan, Asia Pacific, Global Auto
- **Bilingual Interface**: English/Chinese UI support
- **Robust Testing**: 704+ comprehensive tests ensuring reliability
- **Version Compatibility**: Home Assistant 2023.6.3+ with automated compatibility layers

### Recent Major Improvements (August 2025)

- **🔧 Compatibility Layer**: Added comprehensive compatibility support for Home Assistant versions 2023.6.3 to 2025.1.4+
- **🧪 Enhanced Testing**: Completely rewritten compatibility tests with 14 dedicated test cases
- **🏗️ Code Architecture**: Major refactoring - unified client interfaces, split local/OAPI
  clients ([#66](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/66))
- **🐛 Bug Fixes**: Fixed OAPI scene activation and deletion by
  name ([#73](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/73))
- **🐛 Local Mode Fixes**: Fixed device state updates in Local
  Mode ([#65](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/65))
- **⚡ Performance**: Replaced lists with sets for faster
  lookups ([#55](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/55))
- **🛠️ Developer Experience**: Added comprehensive PR templates and automated PR summaries
- **📊 Code Quality**: Integrated Black code formatter and Flake8 linting with line-length 88
- **🏷️ License Compliance**: Added FOSSA license scanning and
  badges ([#60](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/60))

---

## Installation

### Install via HACS

1. In Home Assistant, go to HACS > Integrations > Search for "LifeSmart for Home Assistant".
2. Click "Install".
3. After installation, click "Add Integration" and search for "LifeSmart".

[![Add via HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MapleEve&repository=lifesmart-for-homeassistant&category=integration)
[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=lifesmart)

---

## 🆘 Troubleshooting

If you encounter any issues with the integration, check our comprehensive troubleshooting guide:

📖 **[Troubleshooting Guide](./troubleshooting.md)** - Solutions for common problems

The guide covers:

- Connection issues (cloud & local modes)
- Device problems (unavailable, not updating)
- Performance optimization
- How to generate diagnostics data for issue reports

---

## Initialization

### Prerequisites

- Cloud mode: Register a new application on the [LifeSmart Open Platform](http://www.ilifesmart.com/open/login) to
  obtain your App Key and App Token. Log in to the LifeSmart mobile app to get your User ID.
- Local mode: Obtain your LifeSmart Hub's local IP, port (default 8888), username (default admin), and password (default
  admin).

### Setup Steps

#### Cloud Mode

1. Select "Cloud" as the connection method.
2. Enter your App Key, App Token, User ID, select your region, and choose authentication (token or password).
3. If using password authentication, enter your LifeSmart app password to allow Home Assistant to refresh your token
   automatically.

#### Local Mode

1. Select "Local" as the connection method.
2. Enter your Hub's IP address, port (default 8888), username (default admin), and password (default admin).

---

## Usage

### Home Assistant Services

- Send IR Keys: Send IR commands to remote devices (e.g., TVs, A/Cs).
- Send A/C Keys: Send IR commands with power, mode, temperature, wind, and swing options to air conditioners.
- Trigger Scene: Activate a LifeSmart scene by specifying the hub and scene ID.
- Press Switch: Perform a momentary press on a switch entity for a specified duration.

Example service call (YAML):

```yaml
service: lifesmart.send_ir_keys
data:
  agt: "_xXXXXXXXXXXXXXXXXX"
  me: "sl_spot_xxxxxxxx"
  ai: "AI_IR_xxxx_xxxxxxxx"
  category: "tv"
  brand: "custom"
  keys: [ "power" ]
```

---

## Supported Devices

Supports a wide range of LifeSmart devices, including but not limited to:

Switches: SL_MC_ND1, SL_MC_ND2, SL_MC_ND3, SL_NATURE, SL_P_SW, SL_S, SL_SF_IF1, SL_SF_IF2, SL_SF_IF3, SL_SF_RC, SL_SPWM,
SL_SW_CP1, SL_SW_CP2, SL_SW_CP3, SL_SW_DM1, SL_SW_FE1, SL_SW_FE2, SL_SW_IF1, SL_SW_IF2, SL_SW_IF3, SL_SW_MJ1, SL_SW_MJ2,
SL_SW_MJ3, SL_SW_ND1, SL_SW_ND2, SL_SW_ND3, SL_SW_RC, SL_SW_RC1, SL_SW_RC2, SL_SW_RC3, SL_SW_NS1, SL_SW_NS2, SL_SW_NS3,
V_IND_S

Locks: SL_LK_LS, SL_LK_GTM, SL_LK_AG, SL_LK_SG, SL_LK_YL, SL_P_BDLK, OD_JIUWANLI_LOCK1

Controllers: SL_P, SL_JEMA

Sockets/Plugs: SL_OE_DE, SL_OE_3C, SL_OL_W, OD_WE_OT1, SL_OL, SL_OL_3C, SL_OL_DE, SL_OL_UK, SL_OL_UL

Curtain Motors: SL_SW_WIN, SL_CN_IF, SL_CN_FE, SL_DOOYA, SL_P_V2

Lights: SL_LI_RGBW, SL_CT_RGBW, SL_SC_RGB, OD_WE_QUAN, SL_LI_WW, SL_LI_GD1, SL_LI_UG1, MSL_IRCTL, OD_WE_IRCTL, SL_SPOT,
SL_P_IR

Sensors: SL_SC_G, SL_SC_BG, SL_SC_MHW, SL_SC_CM, SL_SC_BM, SL_P_RM, SL_SC_THL, SL_SC_BE, SL_SC_CQ, SL_SC_CA, SL_SC_B1,
SL_SC_WA, SL_SC_CH, SL_SC_CP, ELIQ_EM, SL_P_A, SL_DF_GG, SL_DF_MM, SL_DF_SR, SL_DF_BB, SL_SC_CN

SPOT Devices: MSL_IRCTL, OD_WE_IRCTL, SL_SPOT, SL_P_IR, SL_P_IR_V2

Cameras: LSCAM:LSICAMGOS1, LSCAM:LSICAMEZ2

For a full and up-to-date list, see
the [supported devices section in the codebase](https://github.com/MapleEve/lifesmart-for-homeassistant/blob/main/custom_components/lifesmart/const.py).

---

## Compatibility & Testing

### Home Assistant Version Support

This integration is thoroughly tested across multiple Home Assistant versions using conda environments:

| Environment       | Python  | Home Assistant | pytest | pytest-ha-custom | aiohttp | Test Status         |
|-------------------|---------|----------------|--------|------------------|---------|---------------------|
| **Environment 1** | 3.11.13 | **2023.6.0**   | 7.3.1  | 0.13.36          | 3.8.4   | ✅ **704/704 tests** |
| **Environment 2** | 3.12.11 | **2024.2.0**   | 7.4.4  | 0.13.99          | 3.9.3   | ✅ **704/704 tests** |
| **Environment 3** | 3.13.5  | **2024.12.0**  | 8.3.3  | 0.13.190         | 3.11.9  | ✅ **704/704 tests** |
| **Current**       | 3.13.5  | **2025.8.0b1** | 8.4.1  | 0.13.266         | 3.12.15 | ✅ **704/704 tests** |

### Test Infrastructure

- **Conda Environments**: Pre-configured conda environments for each HA version
- **Automated Testing**: Local CI script (`.testing/test_ci_locally.sh`) with interactive interface
- **Comprehensive Coverage**: 704+ unit tests with 14 dedicated compatibility tests
- **CI/CD Pipeline**: Automated testing across multiple Python and Home Assistant versions

### Compatibility Features

- **Automatic Version Detection**: Seamlessly adapts to different Home Assistant and aiohttp versions
- **WebSocket Timeout Handling**: Supports both legacy float timeouts and modern ClientWSTimeout objects
- **Climate Entity Features**: Provides backward compatibility for TURN_ON/TURN_OFF attributes
- **Service Call Compatibility**: Handles both legacy and modern Home Assistant service call constructors

### Code Quality Standards

- **Black Code Formatting**: Consistent code style with 88 character line length
- **Flake8 Linting**: Comprehensive code quality checks
- **Comprehensive Testing**: 667+ unit tests with 14 dedicated compatibility tests
- **CI/CD Pipeline**: Automated testing across multiple Python and Home Assistant versions

---

## Development & Contributing

### Development Setup

```bash
# Clone the repository
git clone https://github.com/MapleEve/lifesmart-HACS-for-hass.git
cd lifesmart-HACS-for-hass

# Set up conda environments for testing (recommended)
# Install conda/anaconda first, then create test environments:
conda create -n ci-test-ha2023.6.0-py3.11 python=3.11
conda create -n ci-test-ha2024.2.0-py3.12 python=3.12
conda create -n ci-test-ha2024.12.0-py3.13 python=3.13
conda create -n ci-test-ha-latest-py3.13 python=3.13

# Install dependencies for each environment (example for HA 2023.6.0):
conda activate ci-test-ha2023.6.0-py3.11
pip install "pytest>=7.2.1,<8.0.0" "pytest-homeassistant-custom-component==0.13.36"
pip install pytest-asyncio pytest-cov flake8 black

# Or use traditional venv setup
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install black flake8 pytest
```

### Testing

The project uses a comprehensive testing script that works with conda environments:

```bash
# Run the interactive testing script
./.testing/test_ci_locally.sh

# Available options:
# 1) ci-test-ha2023.6.0-py3.11  (HA 2023.6.0 + Python 3.11)
# 2) ci-test-ha2024.2.0-py3.12  (HA 2024.2.0 + Python 3.12)  
# 3) ci-test-ha2024.12.0-py3.13 (HA 2024.12.0 + Python 3.13)
# 4) ci-test-ha-latest-py3.13   (HA latest + Python 3.13)
# 5) Full CI matrix test (all environments)

# Run tests in specific environment
conda activate ci-test-ha2023.6.0-py3.11
./.testing/test_ci_locally.sh --current

# Run tests for all environments
./.testing/test_ci_locally.sh --all
```

### Code Quality

```bash
# Format code with Black (line length 88)
black custom_components/lifesmart/ --line-length 88

# Run linting
flake8 custom_components/lifesmart/

# Run tests
pytest custom_components/lifesmart/tests/

# Format code
black custom_components/lifesmart/

# Check code quality
flake8 custom_components/lifesmart/
```

### Contributing Guidelines

- Follow the existing code style (Black formatting, 88 char lines)
- Add comprehensive tests for new features
- Update documentation for user-facing changes
- Use conventional commit messages
- Reference relevant issues in pull requests

For detailed contributing guidelines, see our [PR template](.github/PULL_REQUEST_TEMPLATE.md).

---

## Diagrams

**Example Configuration Screenshots**

![Example Configuration](./docs/example-configuration.png)
![Example Image](./docs/example-image.png)
![Example Image 2](./docs/example-image-2.png)
![Example Image 3](./docs/example-image-3.png)
![Example Image 4](./docs/example-image-4.png)

## License

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FMapleEve%2Flifesmart-for-homeassistant.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FMapleEve%2Flifesmart-for-homeassistant?ref=badge_large)