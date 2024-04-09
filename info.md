LifeSmart 设备的 Home Assistant 集成方案

目前支持的设备类型包括：
- 开关
- 门锁
- 通用控制器（型号 SL_P）
- 超级碗夜灯（型号 SL_LAMP）
- SPOT 系列（型号 SL_SPOT），~~正在开发中~~

如果在使用过程中遇到任何问题，或者有改进的建议，可以到仓库中提出。
如果您对这个集成感到满意，多给我点 STAR，以示鼓励。

### 使用说明
====
让 Home Assistant 支持 Lifesmart 设备的 HACS 插件

### 准备步骤：
---
1. 请根据您所在的国家，确认您所在区域对应的 LifeSmart 服务器，大陆地区默认建议使用 `api.cn0.ilifesmart.com`。

2. 在 LifeSmart 开放平台上创建一个新应用，以便获取应用密钥（`app key`）和应用令牌（`app token`）。[访问申请页面](http://www.ilifesmart.com/open/login)（注意：该链接不是 HTTS 连接，请检查浏览器地址栏是否使用 HTTP 访问）。

3. 使用您的 LifeSmart 账户登录上一步创建的应用，授权第三方应用访问，从而获取用户令牌（`user token`）。请确保您使用的 API 地址与您所在的区域相匹配。

**特别提示：LifeSmart 开放平台的默认应用不会包含锁设备的类型信息。如需此功能，需联系 LifeSmart 官方获取授权。**

### 插件如何运作：
---

- 该插件需要联网。在首次加载插件时，它会调用 LifeSmart API 来获取所有设备信息，并在 Home Assistant 中进行设置。之后，插件将通过 websocket 从 LifeSmart 获取设备更新信息。目前，Home Assistant 与 LifeSmart 集线器之间没有直接通信。
