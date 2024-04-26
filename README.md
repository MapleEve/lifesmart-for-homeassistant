# # LifeSmart IoT for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

使用说明
====
让 Home Assistant 支持 Lifesmart 设备的 HACS 插件

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
  websocket 从 LifeSmart 获取设备更新信息。目前，Home Assistant 与 LifeSmart 中枢之间没有直接通信。

### 安装指南：
---

### 手动安装方法

不建议使用手动安装方法，因为它需要手动更新插件，且可能与最新的 Home Assistant 版本不兼容。

```yaml
lifesmart:
  appkey: # 你应用的 appkey
  apptoken: # 你应用的 apptoken
  usertoken: # 你获取到的 usertoken
  userid: # 你获取到的 userid
  url:  # 你使用的 api 地址，建议使用 api.cn0.ilifesmart.com 或者 api.cn2.ilifesmart.com
```

### 推荐使用 HACS 安装自定义仓库

1. 进入 HACS > 集成 > 点击右上角的三个点 > 选择自定义仓库。

2. 在自定义仓库对话框中输入以下信息：

仓库地址：`https://github.com/MapleEve/lifesmart-HACS-for-hass`

类别选择：`集成`

3. 点击添加按钮。

4. 通过添加集成进行设置。

使用 HACS 可以方便您在新版本发布后及时更新。

当插件足够稳定后，我将把它加入 HACS 默认仓库列表，并计划将来将其纳入 Home Assistant 官方集成。

示例配置：
---
![示例配置屏幕截图](./docs/example-configuration.png)
![示例图片](./docs/example-image.png)
![示例图片 4](./docs/example-image-4.png)
![示例图片 2](./docs/example-image-2.png)
![示例图片 3](./docs/example-image-3.png)

支持的设备列表：
---
由于代码重构和更新，可能会有旧设备从支持列表中移除，移除的旧设备加上了~~删除线~~。

- 开关
- 智能门锁信息反馈
- 智能插座
- 动态传感器、门传感器、环境传感器、甲醛/气体传感器
- 照明：目前仅支持超级碗夜灯
- 通用遥控器
- 窗帘电机（目前仅支持 Duya 电机）
- 空调控制面板

支持设备详细列表

开关：
| 型号 | 备注 |
| ------ | ------ |
| OD_WE_OT1 | |
| SL_MC_ND1 | |
| SL_MC_ND2 | |
| SL_MC_ND3 | |
| SL_NATURE | |
| SL_OL | |
| SL_OL_3C | |
| SL_OL_DE | |
| SL_OL_UK | |
| SL_OL_UL | |
| SL_OL_W | |
| SL_P_SW | |
| SL_S | |
| SL_SF_IF1 | |
| SL_SF_IF2 | |
| SL_SF_IF3 | |
| SL_SF_RC | |
| SL_SPWM | |
| SL_SW_CP1 | |
| SL_SW_CP2 | |
| SL_SW_CP3 | |
| SL_SW_DM1 | |
| SL_SW_FE1 | |
| SL_SW_FE2 | |
| SL_SW_IF1 | |
| SL_SW_IF2 | |
| SL_SW_IF3 | |
| SL_SW_MJ1 | 经过真实设备测试 |
| SL_SW_MJ2 | 经过真实设备测试 |
| SL_SW_MJ3 | |
| SL_SW_ND1 | |
| SL_SW_ND2 | |
| SL_SW_ND3 | |
| SL_SW_NS3 | |
| SL_SW_RC | |
| SL_SW_RC1 | |
| SL_SW_RC2 | |
| SL_SW_RC3 | |
| SL_SW_NS1 | |
| SL_SW_NS2 | |
| SL_SW_NS3 | |
| V_IND_S | |

门锁：
| 型号 | 备注 |
| ------ | ------ |
| SL_LK_LS | 经过真实设备测试 |
| SL_LK_GTM | |
| SL_LK_AG | |
| SL_LK_SG | |
| SL_LK_YL | 经过真实设备测试 |
| SL_P_BDLK | |
| OD_JIUWANLI_LOCK1 | |

通用控制器：
| 型号 | 备注 |
| ------ | ------ |
| SL_P | 经过真实设备测试 |

智能插座：
| 型号 | 备注 |
| ------ | ------ |
| SL_OE_DE | 支持计量，经过真实设备测试 |
| SL_OE_3C | 支持计量 |
| SL_OL_W | 支持计量 |
| OD_WE_OT1 | |
| ~~SL_OL_UL~~ | |
| ~~SL_OL_UK~~ | |
| ~~SL_OL_THE~~ | |
| ~~SL_OL_3C~~ | |
| ~~SL_O~~L | |

该项目是基于以下项目整合而来：
---

- [@MapleEve 我本人的重构原始项目](https://github.com/MapleEve/hass-lifesmart)
- [@skyzhishui 提供的 custom_components](https://github.com/skyzhishui/custom_components)
- [@Blankdlh 提供的 hass-lifesmart](https://github.com/Blankdlh/hass-lifesmart)
- [@iKew 的重构](https://github.com/iKaew)
- [@likso 提供的 hass-lifesmart](https://github.com/likso/hass-lifesmart)

如何获取 User Token 和 User ID
---
通过iLifeSmart后台的小工具拼接appkey,apptoken,回调地址、时间戳、did（可以为空）并在页面里面生成sign来访问用户页面进行授权
[访问小工具页面](http://www.ilifesmart.com/open/login#/open/document/tool)
点击“获取用户授权签名验证”然后参考下面 Python 脚本拼接，或者直接执行 Python 脚本

``` python
import time
import hashlib
tick = int(time.time())
appkey = "你的应用 APPKEY"
callbackurl = "http://localhost"
apptoken = "你的应用 APPK TOKEN"
sdata = "appkey=" + appkey
sdata += "&auth_callback=" + callbackurl
sdata += "&time=" + str(tick)
sdata += "&apptoken=" + apptoken
sign = hashlib.md5(sdata.encode(encoding='UTF-8')).hexdigest()
url = "https://api.ilifesmart.com/app/auth.authorize?id=001&"
url += "&appkey=" + appkey
url += "&time=" + str(tick)
url += "&auth_callback=" + callbackurl
url += "&sign=" + sign
url += "&lang=zh"
print(url)
```

脚本运行之后会打印一个地址，浏览器访问这个地址，用你的 Lifesmart APP 帐号密码登录即可从浏览器跳转到空页面 URI 中获取到
User ID、User Token、Token 过期时间、和优选的 API 域名地址 ** 必须使用这个区域，否则 Websocket 请求有问题 **

## 注意：每次通过这个方法授权得到的 User Token 有效期为一年，你需要在到期前重新构建方法获取新的 Token

后面会考虑用用户名和密码模式，不过用户名和密码模式不是很稳定


如何获取门锁设备的授权
---

1. 请使用应用的注册邮箱相同发邮件联系 LifeSmart 的官方邮箱 service(at)ilifesmart.com
2. 注明需要修改的应用名称，应用 AppKey，或者在应用详情的 URI 地址内提供应用的 AppID
3. 说明需要增加的权限 `DoorLock` 和 `DoorLock Control`

你就可以在近期收到回复，回复中会告诉你应用增加了权限

```text
亲爱的用户:
开发平台于 XXXX-XX-XX XX:XX:XX 收到消息:
您的应用(XXXXXXXXX)于 XXXX-XX-XX XX:XX:XX：Basic；DoorLock；DoorLock Control；通过
请及时前往平台进行处理。

此致
LifeSmart研发团队
```