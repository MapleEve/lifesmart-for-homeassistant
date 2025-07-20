# LifeSmart IoT Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
![GitHub License](https://img.shields.io/github/license/MapleEve/lifesmart-for-homeassistant)
[![version](https://img.shields.io/github/manifest-json/v/MapleEve/lifesmart-for-homeassistant?filename=custom_components%2Flifesmart%2Fmanifest.json)](https://github.com/MapleEve/lifesmart-for-homeassistant/releases/latest)
[![stars](https://img.shields.io/github/stars/MapleEve/lifesmart-for-homeassistant)](https://github.com/MapleEve/lifesmart-for-homeassistant/stargazers)
[![issues](https://img.shields.io/github/issues/MapleEve/lifesmart-for-homeassistant)](https://github.com/MapleEve/lifesmart-for-homeassistant/issues)
![haasfestworkflow](https://github.com/MapleEve/lifesmart-for-homeassistant/actions/workflows/haas-vali.yml/badge.svg)
![hacsworkflow](https://github.com/MapleEve/lifesmart-for-homeassistant/actions/workflows/hacs-vali.yml/badge.svg)

# LifeSmart for Home Assistant

> 中文版可以查看 [中文说明](./README_CN.md).

---

## Overview

LifeSmart for Home Assistant integrates LifeSmart smart home devices with Home Assistant. It supports both Cloud and
Local modes, automatic device discovery, and advanced automation via Home Assistant services. The integration supports a
wide range of LifeSmart devices, including switches, sensors, locks, controllers, SPOT devices, and cameras.
Installation and updates are available via HACS.

---

## Features

- Cloud and Local modes (choose between LifeSmart API or local Hub)
- Device discovery and broad device support (switches, sensors, locks, controllers, sockets, curtain motors, lights,
  SPOT, cameras)
- Home Assistant services: send IR keys (including A/C), trigger LifeSmart scenes, momentary switch press
- Multi-region support: China, North America, Europe, Japan, Asia Pacific, Global Auto
- Bilingual UI (English/Chinese)
- Recent improvements: device registration, SSL WebSocket, error handling, code structure

---

## Installation

### Install via HACS

1. In Home Assistant, go to HACS > Integrations > Search for "LifeSmart for Home Assistant".
2. Click "Install".
3. After installation, click "Add Integration" and search for "LifeSmart".

[![Add via HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MapleEve&repository=lifesmart-for-homeassistant&category=integration)
[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=lifesmart)

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

## Diagrams

Below are example diagrams and screenshots referenced in the documentation. Please ensure these images exist in the
repository or update as needed.

**LifeSmart Server Regions**

![LifeSmart Server Regions](./docs/region-server.png)

**Example Configuration Screenshots**

![Example Configuration](./docs/example-configuration.png)
![Example Image](./docs/example-image.png)
![Example Image 2](./docs/example-image-2.png)
![Example Image 3](./docs/example-image-3.png)
![Example Image 4](./docs/example-image-4.png)
