# LifeSmart IoT Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

使用说明 Instructions
====
让 Home Assistant 支持 Lifesmart 设备的 HACS 插件 Lifesmart devices for Home Assistant

准备步骤 Prerequisites：
---

1. 请根据您所在的国家，确认您所在区域对应的 LifeSmart
   服务器，必须使用 `API 授权后返回的地址`。 WebSocket
   URL地址的选择，必须根据⽤户授权成功后返回的 `svrrgnid` 保持⼀致，否则不会 正常⼯作，WebSocket 不⽀持跨区使⽤。 Find current
   LifeSmart region for your country America, Europe, Asia Pacific, China.

2. 在 LifeSmart 开放平台上创建一个新应用，以便获取应用密钥（`App Key`
   ）和应用令牌（`App Token`）。[访问申请页面](http://www.ilifesmart.com/open/login)（注意：该链接不是 HTTS 连接，请检查浏览器地址栏是否使用
   HTTP 访问）。
   New Application from LifeSmart Open Platform to obtain `App Key` and `App Token`

3. 使用您的 LifeSmart 账户登录上一步创建的应用，授权第三方应用访问，从而获取用户令牌（`User Token`）。请确保您使用的 API
   地址与您所在的区域相匹配。
   Login to application created in previous bullet with LifeSmart user to grant 3rd party application access to
   get `User Token`, please ensure you use the api address with correct region.

**特别提示：LifeSmart
开放平台的默认应用不会包含锁设备的类型信息，若无实体权限则无法生成门锁实体，而只会在门锁有开关动作后生成 **二元传感器**
。如需门锁实体功能，需联系
LifeSmart 官方获取授权。**
**Please note that, by default application from LifeSmart Open Platform won't return you Lock devices type. You have to
contact them to get it granted to your application.**

插件如何运作 How it works：
---

- 该插件需要联网。在首次加载插件时，它会调用 LifeSmart API 来获取所有设备信息，并在 Home Assistant 中进行设置。之后，插件将通过
  websocket 从 LifeSmart 获取设备更新信息。目前，Home Assistant 与 LifeSmart 中枢之间没有直接通信。

支持的设备列表 Supported devices：
---
由于代码重构和更新，可能会有旧设备从支持列表中移除，移除的旧设备加上了~~删除线~~。

- 开关 Switch
- 智能门锁 Door Lock
- 智能插座 Plugs
- 动态传感器、门禁传感器、环境传感器、甲醛/气体传感器 Dynamic Sensor, Door Sensor, Environmental Sensor, Formaldehyde/Gas
  Sensor
- 照明：目前仅支持超级碗夜灯 Super Bowl
- 通用遥控器 IR Remote
- 窗帘电机和窗帘电机的更新状态 Curtain Motor and Curtain Motor Update
- 空调控制面板 Air Conditioner Control Panel
