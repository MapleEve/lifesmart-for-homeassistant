### 准备步骤：
---

1. 请根据您所在的国家，确认您所在区域对应的 LifeSmart
   服务器，必须使用 ` API 授权后返回的地址`。[查看详细的区域服务器列表](./docs/api-regions.md)。 WebSocket
   URL地址的选择，必须根据⽤户授权成功后返回的 svrrgnid 保持⼀致，否则不会 正常⼯作，WebSocket 不⽀持跨区使⽤。

2. 在 LifeSmart 开放平台上创建一个新应用，以便获取应用密钥（`app key`
   ）和应用令牌（`app token`）。[访问申请页面](http://www.ilifesmart.com/open/login)（注意：该链接不是 HTTS 连接，请检查浏览器地址栏是否使用
   HTTP 访问）。

3. 使用您的 LifeSmart 账户登录上一步创建的应用，授权第三方应用访问，从而获取用户令牌（`user token`）。请确保您使用的 API
   地址与您所在的区域相匹配。

**第 3 步的 Python代码在本说明的最底部**

**特别提示：LifeSmart 开放平台的默认应用不会包含锁设备的类型信息。如需此功能，需联系 LifeSmart 官方获取授权。**

获取锁授权的方式写在本说明的最底部

### 插件如何运作：
---

- 该插件需要联网。在首次加载插件时，它会调用 LifeSmart API 来获取所有设备信息，并在 Home Assistant 中进行设置。之后，插件将通过
  websocket 从 LifeSmart 获取设备更新信息。目前，Home Assistant 与 LifeSmart 集线器之间没有直接通信。
