# LifeSmart云平台 ZigBee API (v2.4)

| 版本  | 修订日期       | 修订人      | 修订内容                                                                                                                   |
|:----|:-----------|:---------|:-----------------------------------------------------------------------------------------------------------------------|
| 1.0 | 2019/09/20 | Jon Fan  | 初稿                                                                                                                     |
| 1.1 | 2019/10/25 | Jon Fan  |                                                                                                                        |
| 1.2 | 2019/11/20 | Jon Fan  | ZigBeeCtl增加updateNetworkChannel、 Setvalue指令                                                                            |
| 1.3 | 2019/11/22 | Jon Fan  | 增加zigBee设备特定属性-ALM属性描述, ExecuteDoorLockCommand命令新增： 设置/查询/删除门卡用户的指令说明, 修改ExecuteDoorLockcommand指令返回的说明 描述              |
| 1.4 | 2019/12/12 | Jon Fan  | 增加2.6.1 FUKI IO门锁命令描述 增加2.5.5 FUKI IO门锁 ALM0FA0 IO描述                                                                   |
| 1.5 | 2019/12/20 | Jon Fan  | 增加1.3ZigBee设备Io属性列表                                                                                                    |
| 1.6 | 2019/12/30 | Jon Fan  | ZigBeeCtl命令增加startota指令                                                                                                |
| 1.7 | 2020/01/28 | JonFan   | ZigBeeCtl命令增加upgradeModuleFw指令                                                                                         |
| 1.8 | 2020/03/12 | Jon Fan  | ZigBeeCtl命令增加Native指令获取zigBee模块 固件版本的描述                                                                                |
| 1.9 |            | Jon Fan  | 增加返回的 BVMT,BVT1，BVT2,BVT3,CVer属性的描述 ZigBeeCtl.RequestValue指令增加获取LQI与 RSSI的描述； ZigBeeCtl.Native指令增加获取zigBee设备的 固件版本的描述； |
| 2.0 | 2020/04/03 | Jon Fan  | ALM0009调整为只列出DoorLock告警说明 ZigBeeCtl.GetNodeInfo指令增加返回的门锁 信息                                                            |
| 2.1 | 2020/06/30 | Jon Fan  | 增加2.7章节；修改1.3 EVTLO，HISLK属性定义； 修改2.5.5. ALM0FA0告警定义                                                                    |
| 2.2 | 2020/07/15 | Jon Fan  | ZigBeeCtl命令GetNodeTopology指令修改描述                                                                                       |
| 2.3 | 2022/01/16 | Jon Fan  | 增加a属性描述以及zigBee设备列表                                                                                                    |
| 2.4 | 2025/02/24 | PrettyJu | ZigBeeCtl增加setCommand指令                                                                                                |

## 目录

- [1. 概述](#1-概述)
    - [1.1 设备模型说明](#11-设备模型说明)
    - [1.2 ZigBee设备规格](#12-zigbee设备规格)
    - [1.3 ZigBee设备IO属性列表](#13-zigbee设备io属性列表)
- [2. 接口(Interface)](#2-接口interface)
    - [2.1 控制ZigBee设备(ZigBeeCtl)](#21-控制zigbee设备zigbeectl)
        - [2.1.1 请求定义](#211-请求定义)
        - [2.1.2 范例](#212-范例)
        - [2.1.3 动作(act)定义](#213-动作act定义)
    - [2.2 添加ZigBee设备(EpAdd)扩展说明](#22-添加zigbee设备epadd扩展说明)
        - [2.2.1 请求定义](#221-请求定义)
        - [2.2.2 扩展参数(optarg)说明](#222-扩展参数optarg说明)
        - [2.2.3 范例](#223-范例)
    - [2.3 移除ZigBee设备(EpRemove)扩展说明](#23-移除zigbee设备epremove扩展说明)
        - [2.3.1 请求定义](#231-请求定义)
        - [2.3.2 扩展参数(optarg)说明](#232-扩展参数optarg说明)
        - [2.3.3 范例](#233-范例)
    - [2.4 获取设备属性(EpGet/EpGetAll)扩展说明](#24-获取设备属性epgetepgetall扩展说明)
    - [2.5 Zigbee设备特定属性说明](#25-zigbee设备特定属性说明)
        - [2.5.1 ALM0001系列告警](#251-alm0001系列告警)
        - [2.5.2 ALM0009系列告警](#252-alm0009系列告警)
        - [2.5.3 门锁ALM告警](#253-门锁alm告警)
        - [2.5.4 动态/门禁感应器ALM告警](#254-动态门禁感应器alm告警)
        - [2.5.5 ALM0FA0系列告警](#255-alm0fa0系列告警)
        - [2.5.6 动态/门禁感应器ALM_T告警](#256-动态门禁感应器alm_t告警)
        - [2.5.7 A警报](#257-a警报)
    - [2.6 Zigbee设备特定指令说明](#26-zigbee设备特定指令说明)
        - [2.6.1 FUKI IO Smart DoorLock](#261-fuki-io-smart-doorlock)
    - [2.7 Zigbee设备特定常量定义](#27-zigbee设备特定常量定义)
        - [2.7.1 DoorLock](#271-doorlock)
- [3. ZigBee设备列表](#3-zigbee设备列表)

## 1.概述

该文档是LifeSmart云平台 ZigBee
API服务接口的说明文档。它是做为LifeSmart云平台服务接口文档的扩充，有关基本概念，例如API调用的签名等我们已经在LifeSmart云平台服务接口文档作出说明，本文档将不再描述。因此需要先参考并结合《LifeSmart云平台服务接口》文档才能完整获悉。

ZigBee设备的添加与删除仍旧使用 EpAdd 与 EpRemove 接口，请参考《LifeSmart云平台服务接口》中 EpAdd 与 EpRemove
接口说明部分，不过完成ZigBee设备的添加与删除需要提供扩展参数，扩展参数说明部分我们将在本文档中描述。

符合LifeSmart设备规范的ZigBee设备，我们已经把ZigBee设备的属性映射到LifeSmart的设备属性，因此可以直接使用OpenAPI的EpGet/EpSet系列接口进行查询/控制，只有特殊的、非LifeSmart设备规范兼容的ZigBee设备，或者额外扩展功能才需要使用ZigBee专用命令。

可以使用的LifeSmart云平台ZigBee API有:

| API 说明                 | 描述              |
|:-----------------------|:----------------|
| api.ZigBeeCtl          | 执行ZigBee设备相关操作  |
| api.EpAdd 扩展说明         | 关于如何添加 ZigBee设备 |
| api.EpRemove 扩展说明      | 关于如何删除ZigBee设备  |
| api.EpGet/EpGetAll扩展说明 | 关于ZigBee扩展属性    |

## 1.1 设备模型说明

为了方便阐述该API，这里我们对LifeSmart的设备模型做个简要的说明，对一些术语作出说明。

我们以EpGet请求获取的数据为例：

```json
{
  "name": "Smart Switch",
  "agt": "A3EAAABtAEwQRzM0Njg5NA",
  "me": "2d11",
  "devtype": "SL_SW_IF3",
  "stat": 1,
  "data": {
    "L1": {"type": 129, "val": 1,"name": "Living"},
    "L2": {"type": 128, "val": 0,"name": "Study"},
    "L3": {"type": 129, "val": 1,"name": "Kid"},
  },
}
```

我们定义如下模型：

• 智慧中心(Agt)： "A3EAAABtAEwQRzM0Njg5NA"• 设备(EP)： "2d11"，它标识设备，它是一个 SL_SW_IF3 类型的三联开关
• 设备属性(IO口)： 设备的属性，可以用于读取状态，控制行为，L1、L2、L3它们都是设备的IO口，当然对于只读的IO口例如温度传感器，则只能读取状态，不能控制。
• 管理对象(MO)： 泛指以上设备的总称，也可以包括AI对象，即MO可以是智慧中心，也可以是设备或者IO口，AI等。

## 1.2 ZigBee设备规格

ZigBee设备规格(devtype)：

ZigBee设备在LifeSmart设备体系中规格有如下两种类型：

1. ZG#MODEL_NAME
2. ZGAAAABBBBCCCC

示例：ZG#SAMSUNG
SDS_365p#在获取到ModelName的情况下，将显示ModelName。ModelName的最大可显示长度是17个字符，若超过17个字符，则将显示截断前16个字符 + '#'
，最后的'#'标识该ModelName是截断的。

示例：ZG11520104000A

在获取不到ModelName的情况下，将显示原始编码类型，具体定义如下：

• AAAA: ManufacturerCode，厂商编码 例如 1152为 Door Lock厂商
• BBBB: Profile Id 例如 0104为 ZigBee Home Automation
• CCCC: Device Id, 例如 000A为 Door Lock

### ZigBee设备IO的命名规则

ZigBee设备的设备属性(IO口)都已经映射到LifeSmart的设备模型，只是由于ZigBee设备可能会有多路(endpoint)
相同设备属性，因此ZigBee设备的设备属性命名是 “IOn” ，其n指示第几路(endpoint)，例如 "O1" 指示第一路开关，"O2"
指示第二路开关。因此具体设备属性规格参考需要去除掉n，例如想要查询 "O1" 这个设备属性的具体规格，需要参考 "O"
设备属性规格定义，设备属性规格定义请参考《LifeSmart智慧设备规格属性说明》。

## 1.3 ZigBee设备IO属性列表

基于 ZigBee设备IO的命名规则 说明，ZigBee设备的设备属性(IO口)命名为 “IOn” ，除去后面n指示的第几路(endpoint)
，“IO”为通用的IO属性，下表列举了ZigBee设备当前使用的设备IO属性列表。

| IO属性名   | IO属性说明             | 读/写 | 描述                                                                                                                                                                                                                                              |
|:--------|:-------------------|:----|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A       | 警报                 | R   | 设备警报，`val`值非0指示存在警报，警报时告警属性，一般有设备原始的ALM属性推导而出。例如ZigBee感应器，只要关注A警报属性，若`val=1`则标识存在警报，而无需关注原始的ALM特定值。                                                                                                                                             |
| ALM     | 告警                 | R   | 设备告警，`val`值非0指示存在告警，具体告警信息请参考特定ZigBee设备的描述。                                                                                                                                                                                                     |
| ALM0001 | ALM0001系列告警        | R   | ALM0001系列告警是电池电量类告警，具体告警请参考ZigBee设备特定属性说明。                                                                                                                                                                                                      |
| ALM0009 | ALM0009系列告警        | R   | ALM0009系列告警是ZigBee设备专用告警类，具体告警请参考ZigBee设备特定属性说明。                                                                                                                                                                                                |
| ALM0FA0 | ALM0FA0系列告警        | R   | ALM0FA0系列告警是FUKI IO门锁类告警，具体告警请参考ZigBee设备特定属性说明。                                                                                                                                                                                                 |
| ALM_T   | 防撬告警               | R   | `val`值定义如下：`0`：无告警；`1`：有告警                                                                                                                                                                                                                      |
| AXS     | 震动状态               | R   | `val`值定义如下：`0`：无震动；非`0`：震动                                                                                                                                                                                                                      |
| B       | 按键状态               | R   | `val`值定义如下：`0`:未按下按键；`1`:按下按键                                                                                                                                                                                                                   |
| EE      | 甲醛浓度               | R   | `val`值表示甲醛浓度原始值，实际值等于原始值/1000（单位:ug/m3）                                                                                                                                                                                                         |
| EE      | 电量Energy           | R   | 为累计用电量，值为浮点数，单位为度(kwh)。注意：其值类型为IEEE 754浮点数的32位整数布局。例如1024913643表示的是浮点值：0.03685085 具体请参考：《Lifesmart 智慧设备规格属性说明》- Io值浮点类型说明                                                                                                                       |
| EE      | 功率Power            | R   | 为当前负载功率，值为浮点数，单位为w。注意：其值类型为IEEE 754浮点数的32位整数布局。例如1024913643表示的是浮点值：0.03685085 具体请参考：《LifeSmart 智慧设备规格属性说明》- Io值浮点类型说明                                                                                                                           |
| EVTLO   | 开锁状态               | R   | `type%2==1`表示打开；`type%2==0`表示关闭；`val`值定义如下：`0xAABBCCCC`。AA表示 Operation Event Source，具体参见：2.7.1.1；BB表示 Operation Event Code，具体参见：2.7.1.2；CCCC表示用户编号；                                                                                             |
| G       | 门磁吸合感应             | R   | `val`值定义如下：`0`：门磁没有吸合，门处于打开；`1`：门磁吸合，门处于关闭                                                                                                                                                                                                      |
| H       | 湿度 Humidity        | R   | `val`值表示原始湿度值，它是湿度值*10，也即实际湿度值=原始湿度值/10(%)                                                                                                                                                                                                      |
| HISLK   | 最近一次开锁信息           | R   | `type%2==1`表示打开；`type%2==0`表示关闭；`val`值定义如下：`0xAABBCCCC`。AA表示 Operation Event Source，具体参见：2.7.1.1；BB表示 Operation Event Code，具体参见：2.7.1.2；CCCC表示用户编号；                                                                                             |
| L       | 开关                 | RW  | 状态：`type%2==1`,表示打开(忽略`val`值);`type%2==0`,表示关闭(忽略`val`值)；控制：打开，则下发：`type=0x81,val=1`；关闭，则下发：`type=0x80,val=0`;                                                                                                                                  |
| M       | 移动侦测 Motion Detect | R   | `val`值定义如下：`0`：没有检测到移动；非`0`:有检测到移动                                                                                                                                                                                                              |
| O       | 插座开关               | RW  | 状态：`type%2==1`,表示打开(忽略`val`值);`type%2==0`,表示关闭(忽略`val`值)；控制：打开，则下发：`type=0x81,val=1`；关闭，则下发：`type=0x80,val=0`;                                                                                                                                  |
| PM      | PM2.5浓度            | R   | `val`值表示PM2.5值 (单位：ug/m³)                                                                                                                                                                                                                       |
| PM(1)   | PM1浓度              | R   | `val`值表示PM1值 (单位：ug/m³)                                                                                                                                                                                                                         |
| PM(10)  | PM10浓度             | R   | `val`值表示PM10值 (单位：ug/m³)                                                                                                                                                                                                                        |
| RGB     | RGB三原色             | RW  | 状态：`type%2==1`表示打开;`type%2==0`表示关闭;`val`值为颜色值，大小4个字节，定义如下:`bit0~bit7:Blue` `bit8~bit15: Green` `bit16~bit23:Red` `bit24~bit31:0x00`；控制：开灯：`type=0x81;val=1`；关灯：`type=0x80;val=0`; 开灯并设置颜色或动态值：`type=0xff;val=颜色值`；关灯并设置颜色值:`type=0xfe;val=颜色值`； |
| T       | 温度 Temperature     | R   | `val`值表示原始温度值，它是温度值*10，也即实际温度值=原始温度值/10(单位：℃)                                                                                                                                                                                                   |
| V       | 电压                 | R   | `val`值表示原始电压值，它是实际电压值*10，也即实际电压值=原始电压值/10(单位：V) `val`有效值为16位(2bytes)                                                                                                                                                                            |
| WW      | 亮度色温               | RW  | 值越小则色温表现为暖光；值越大则色温表现为冷光；`val`有效值为16位，则设置的最大色温值为65535；设置色温，则下发：`type=0xcf,val=色温值`                                                                                                                                                               |
| Z       | 照度                 | R   | `val`值表示光照值                                                                                                                                                                                                                                     |
| tD      | 目标位置               | W   | 完全打开，则下发：`type=0xCF,val=100`；完全关闭，则下发：`type=0xCF,val=0`; 开到百分比，则下发：`type=0xCF,val=百分比值`；停止窗帘，则下发：`type=0xCE,val=0x80`;                                                                                                                          |

## 2.接口(Interface)

## 2.1 控制ZigBee设备(ZigBeeCtl)

### 2.1.1 请求定义

| Type                | Definition       | Must | Description                                       |
|:--------------------|:-----------------|:-----|:--------------------------------------------------|
| Interface Name      | ZigBeeCtl        |      | 执行ZigBee设备相关操作                                    |
| Partial URL         | api.ZigBeeCtl    | Y    |                                                   |
| Data Format         | application/json | Y    |                                                   |
| Request Type        | HTTP POST        | Y    | 请求类型                                              |
| **Request Content** | **`id`**         | Y    | 消息id号                                             |
|                     | **`method`**     | Y    | ZigBeeCtl                                         |
|                     | **`system`**     |      | *系统级参数对象*                                         |
|                     | `ver`            | Y    | 1.0                                               |
|                     | `lang`           | Y    | en                                                |
|                     | `sign`           | Y    | 签名值                                               |
|                     | `userid`         | Y    | User ID                                           |
|                     | `appkey`         | Y    | appkey                                            |
|                     | `did`            | O    | (可选)终端唯一id。如果在授权时填入了，此处必须填入相同id                   |
|                     | `time`           | Y    | UTC时间戳, 自1970年1月1日起计算的时间, 单位为秒                    |
|                     | **`params`**     |      | *业务级参数对象*                                         |
|                     | `agt`            | Y    | 欲执行操作的智慧中心Id                                      |
|                     | `act`            | Y    | 动作名称                                              |
|                     | `actargs`        | O    | (可选)动作参数, 若操作不需参数则可不提供, 若提供则数据类型必须是JSON对象的序列化字符串。 |

### 2.1.2 范例

我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
did为DID_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

请求地址：svrurl + PartialURL(svrurl以实际用户所在区域SvcURL为准)，例如：

https://{your-region-api-service}/app/api.ZigBeeCtl

### 请求信息：

```json
{
  "id":10014,
  "method":"ZigBeeCtl",
  "system":{
    "ver":"1.0",
    "lang":"zh",
    "sign":"SIGN_XXXXXXXX",
    "userid":"1111111",
    "appkey":"APPKEY_XXXXXXXX",
    "did":"DID_XXXXXXXX",
    "time":1541398596
  },
  "params":{
    "agt":"A3MAAABPADIQRzUwNTE5Mw",
    "act":"ListNodes"
  }
}
```

签名原始字符串为：

```
method:ZigBeeCtl,act:ListNodes,agt:A3MAAABPADIQRzUwNTE5Mw,time:1501151764,userid:111111,usertoken:USERTOKEN_XXXXXXXX,appkey:APPKEY_XXXXXXXX,apptoken:APPTOKEN_XXXXXXXX
```

### 回复信息：

若执行成功则返回：

```json
{
  "id":10014,
  "code":0,
  "message":{
    "homeid": 21463,
    "0": {
      "_added": true,
      "ExPainId": "F1D2F902559772D2",
      "Ieee": "00158D000150919D",
      "Value": {}
    },
    "14537": {
      "Ieee": "00158D0001DC5C28",
      "name": "lumi.plug",
      "manufacturerCode": 4447,
      "AllocateAddress": 1,
      "SecurityCapability": 0,
      "RxOnSleeping": 1,
      "DeviceType": 1,
      "ExPainId": "",
      "profile_id": 260,
      "PowerSource": 1,
      "AlternatePANCoordinator": 0,
      "Value": [
        {
          "writeOnly": false,
          "genre": 6,
          "id": "0006_1",
          "pollIntensity": 0,
          "units": "",
          "index": 0,
          "readOnly": false,
          "instance": 1,
          "type": "Unsigned_24",
          "label": "Basic"
        }
      ],
      "_added": true
    }
  }
}
```

### 若失败则返回：

```json
{
  "id":10014,
  "code": "ErrCode",
  "message": "ErrMessage"
}
```

### 2.1.3 动作(act)定义

当前支持的act有如下：

| 动作(act)                | 动作参数(actargs)                                       | 描述                          |
|:-----------------------|:----------------------------------------------------|:----------------------------|
| ListNodes              | -                                                   | 列出智慧中心当前ZigBee设备集合          |
| GetNodeInfo            | {me或idx}                                            | 获取ZigBee设备节点信息              |
| SoftReboot             | -                                                   | 软重启智慧中心ZigBee模块             |
| Reset                  | -                                                   | 重置ZigBee模块                  |
| CancelCommand          | -                                                   | 取消正在执行的ZigBee命令             |
| GetNodeRSSI            | {me或idx}                                            | 查看ZigBee设备/网关的信号强度          |
| GetNodeTopology        | {me或idx, Topology_start}                            | 查看ZigBee设备/网关拓扑图            |
| RequestValue           | {me或idx, zcl, endpoint, attributeId}                | 查看ZigBee设备特定zcl下相关属性        |
| RefreshNodeInfo        | {me或idx}                                            | 刷新ZigBee设备所有相关簇的相关属性        |
| ExecuteDoorLockCommand | {me或idx, zcl, endpoint, command, command_data}      | 设置/查询/删除ZigBee门锁密码          |
| UpdateNetworkChannel   | {channel}                                           | 修改ZigBee网络信道                |
| SetValue               | {me或idx, zcl, endpoint, attributeId, attributeData} | 设置ZigBee设备特定zcl下相关属性        |
| SetCommand             | {me或idx, zcl, endpoint, commandData}                | 设置ZigBee设备特定zcl下相关命令        |
| StartOta               | {key}                                               | 升级某一类别的ZigBee设备的固件          |
| UpgradeModuleFW        | {bin, url}                                          | 升级智慧中心ZigBee模块的固件           |
| Native                 | {cmd, proc, ...}                                    | 高级命令，将直接使用动作参数设置命令，为将来扩展使用。 |

说明：关于如何指明具体ZigBee设备，可以使用参数me或idx，两者指明一个即可。  
其me为api.EpGetAll返回的设备的me属性，例如"6df0"，类型为string。  
其idx为api.ZigBeeCtl.ListNodes命令返回数据结构的key属性（需要把字符串类型转换为数字类型，具体见ListNodes描述），例如 1
，类型为number。

其idx也为api.EpGetAll方法返回的Ep数据的zg_nodeid属性。

### ListNodes

列出智慧中心当前ZigBee设备集合，此列表也将包含智慧中心ZigBee模块网关本身。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ListNodes"
}
```

返回的数据是JSON对象结构。KEY指示ZigBee设备的nodeId(idx)属性

• 0为ZigBee网关的nodeId，因此"0" KEY特指ZigBee网关的节点信息；  
• 其它数字类型字符串是ZigBee子设备的nodeId(idx)，例如示例中的 “14537”，其值指示该ZigBee设备的节点信息；  
• "homeid"是特殊的KEY，指示ZigBee网络的PanID，例如2.1.2示例中的 21463；

详细参数请参考2.1.2示例。

需要注意的是 ListNodes返回的key是字符串类型(String)，但Node的idx是数字类型(number)
，在执行其它act例如：GetNodeInfo、IsFailedNode等若需要传递idx属性，则idx需要为number类型，可以把ListNodes返回的key转换成数字做为idx。

### GetNodeInfo

获取ZigBee设备节点信息。该命令需要actargs参数提供me或idx属性，指示是哪个ZigBee节点。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "GetNodeInfo",
  "actargs": "{\"me\": \"6df0\"}"
}
```

返回的数据该ZigBee节点的相关规格以及属性的集合。具体参数的含义需要参考ZigBee标准。Response示例：

```json
{
  "code": 0,   
  "message": {
    "Ieee": "000D6F000FE6E4E4", 
    "name": "On/Off_Plug", 
    "manufacturerCode": 4401, 
    "AllocateAddress": 1, 
    "SecurityCapability": 0, 
    "RxOnSleeping": 1, 
    "DeviceType": 1, 
    "ExPainId": "", 
    "profile_id": 260, 
    "PowerSource": 1, 
    "AlternatePANCoordinator": 0, 
    "LastLQI": 0, 
    "LastRSSI": 0, 
    "Model_name": "SZ-ESW02N iJPZ3", 
    "Manu_name": "Sercomm Corp.", 
    "Hwver": 16, 
    "Applver": 18, 
    "Value": {
      "writeOnly": false, 
      "genre": 6, 
      "id": "0006_1", 
      "pollIntensity": 0, 
      "label": "Basic", 
      "readOnly": false, 
      "units": "", 
      "index": 0, 
      "type": "BOOL_8", 
      "instance": 1, 
      "value": 0, 
      "default": 0
    }, 
    "_added": true
  }
}
```

• Ieee: 标识ZigBee设备的唯一标识码   
• name 标识ZigBee设备名称   
• manufacturerCode 标识生产商编码   
• manu_name 标识生产商名称   
• Model_name 标识设备模型名称   
• Hwver 标识设备硬件版本   
• LastRSSI/LastLQI 标识设备最近一次信号RSSI/LQI   
• BVMT Battery Voltage Min Threshold   
• BVT1 Battery Voltage Threshold1   
• BVT2 Battery Voltage Threshold 2   
• BVT3 Battery Voltage Threshold 3   
• CVer Current File Version   
• Value 标识ZigBee设备 IOs 信息，可以直接参考EpGet/EpGetAll方法返回的设备data信息   
• IOLHver IO 门锁 leader 硬件版本号   
• IOLFver IO 门锁 leader 固件版本号   
• IODHver IO 门锁 门锁 硬件版本号   
• IODFver IO 门锁 门锁 硬件版本号   
• IOBHver IO 门锁 BLE 硬件版本号   
• IOBFver IO 门锁 BLE 硬件版本号   
• IOtype IO 门锁 型号   
• IOserial IO 门锁 序列号   
• IOBLEmac IO 门锁 BLE MAC   
• BtLevP 电池电量百分比

### SoftReboot

软重启智慧中心ZigBee模块。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "SoftReboot"
}
```

若执行成功则Response将返回：

```json
{
  "code": 0,
  "message": "Success"
}
```

### Reset

重置智慧中心ZigBee模块。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "Reset"
}
```

若执行成功则Response将返回：

```json
{
  "code": 0,
  "message": "success"
}
```

注意：该操作会清除ZigBee模块网关的所有数据，请谨慎调用。

### CancelCommand

取消正在执行的ZigBee命令。

主要用在添加/删除ZigBee设备的过程中。由于添加/删除操作会进行设备对码，耗时会比较久，若想中途取消操作则可以执行CancelCommand命令。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "CancelCommand"
}
```

若执行成功则Response将返回：

```json
{
  "code": 0,
  "message": "success"
}
```

### GetNodeRSSI

获取ZigBee设备/网关的信号强度/背噪强度。  
该接口对ZigBee设备返回的是信号强度，对ZigBee网关返回的是背噪强度。

#### 获取ZigBee设备的信号强度

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "GetNodeRSSI",
  "actargs": "{\"me\": \"6df0\"}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0, 
  "message": -12.34509803921569
}
```

#### 获取ZigBee网关的背噪强度

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "GetNodeRSSI",
  "actargs": "{\"me\": 0}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0, 
  "message": -100
}
```

提示：如何指明是ZigBee网关，设置me属性 `= 0` ， 注意是Number类型0，而非字符串 `"0"` ；

注意：ZigBee设备返回的是信号强度，其值越接近0表示信号强度越好。  
注意：ZigBee网关返回的是背噪强度，其值越接近0表示背噪越强，信号越差。

### GetNodeTopology

获取ZigBee设备/网关拓扑图。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "GetNodeTopology",
  "actargs": "{\"me\": \"6df0\", \"Topology_start\": 0}"
}
```

Topology_start 指明拓扑起始跳数，在拓扑网络很复杂的时候，可以略过前面的拓扑，直接查看后面的拓扑图。

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "place": 3,
    "count": 5,
    "node_tab": [
      {
        "Device_Type": 0,
        "meid": "",
        "nodeid": 0,
        "Relationship": 0
      },
      {
        "Device_Type": 2,
        "meid": "8015",
        "nodeid": 22284,
        "Relationship": 1
      },
      {
        "Device_Type": 2,
        "meid": "8017",
        "nodeid": 10639,
        "Relationship": 1
      }
    ]
  }
}
```

node_tab 为发现的路由表，其参数说明如下：

• Device_Type: 指示设备类型，0:Coordinator; 1:Router; 2:End Device• Relationship: 指示节点关系，0:父节点; 1:子节点; 2:
兄弟节点• meid: 指示LifeSmart节点Id，等于""指示为网关节点• nodeid: 指示ZigBee节点的nodeid

| 提示            | 说明                               |
|:--------------|:---------------------------------|
| 如何指明是ZigBee网关 | nodeid属性=0，注意是Number类型0，而非字符串"0" |

### RequestValue

查看ZigBee设备特定zcl下相关属性。

其参数如下：

• zcl: 特定zcl  
• endpoint: 特定endpoint  
• attributeId: 指明需要设置的属性ID

例如刷新一个Lock设备的用户密码配置列表，可以下发如下命令：

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "RequestValue",
  "actargs": "{\"me\":\"6df0\", \"zcl\": 0x0000 , \"endpoint\": 1, \"attributeId\": 0x0005}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "zcl": 0,
    "state": 0,
    "addr_id": 5,
    "data": [108, 117, 109, 105, 46, 112, 108, 117, 103]
  }
}
```

注意：ZigBee设备如果符合LifeSmart设备规范，将可以直接使用api.EpSet命令控制。而且对于符合LifeSmart设备规范的设备，我们建议使用api.EpSet命令进行控制,并且使用api.EpGet系列接口获取设备属性值，关于api.Ep系列命令请参考《LifeSmart云平台服务接口》。

RequestValue指令可以获取ZigBee设备的相应属性，常见的属性获取列举如下：

#### 1. 获取ZigBee设备LQI属性

Request参数示例：

```json
{
  "agt": "THE_AGT",
  "act": "RequestValue",
  "actargs": "{\"me\": \"THE_ME\", \"zcl\": 0x0b05, \"endpoint\": 1, \"attributeId\": 0x011c}"
}
```

#### 若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "state": 0,
    "addr_id": 284,
    "data": [254],
    "zcl": 2821
  }
}
```

#### 2. 获取ZigBee设备RSSI属性

Request参数示例：

```json
{
  "agt": "THE_AGT",
  "act": "RequestValue",
  "actargs": "{\"me\": \"THE_ME\", \"zcl\": 0x0b05, \"endpoint\": 1, \"attributeId\": 0x011d}"
}
```

#### 若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "state": 0,
    "addr_id": 285,
    "data": [242],
    "zcl": 2821
  }
}
```

### RefreshNodeInfo

刷新ZigBee设备所有簇的相关属性。主要用于批量刷新ZigBee设备的相关簇的属性。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "RefreshNodeInfo",
  "actargs": "{\"me\": \"6e04\"}"
}
```

若执行成功则Response将返回：

```json
{
  "code": 0,
  "message": "Success"
}
```

提示：若 `me = "all"` ，则刷新该ZigBee网关下所有ZigBee设备的包含的簇的信息。

### ExecuteDoorLockCommand

该指令根据command属性不同，可以设置/查询/删除 ZigBee门锁的密码用户和门卡用户

#### 1. 设置门锁密码用户

设置门锁密码用户，其参数如下：

• zcl: `0x0101`   
• endpoint: `1`   
• command: `5` 指明是设置门锁密码用户   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 257, \"endpoint\": 1, \"command\": 5, \"command_data\": [0x29, 0, 5, 0x28, 1, 0x30, 0, 0x10, 4, 0x10, 0x32, 0x10, 0x32, 0x10, 0x32, 0x10, 0x34]}"
}
```

command_data参数说明：

‣ `0x29, 0, 5` : 指明需要操作的UserId，5表示UserId是5。DoorLock的UserId范围在`[1~254]`
，但具体可以填写的值需要参考门锁说明书，例如有些门锁限定范围是 `[1~240]` 。  
‣ `0x28,1`: 指明UserStatus，1表示启用；3表示禁用；`0x30,0`: 指明UserType，其定义如下：0 Unrestricted User（默认）；1 Year Day
Schedule User；2 Week Day Schedule User ；- 3 Master User；- 4 Non Access User

‣ `0x10,4`: 指明pin_code长度，4表示其长度为4位。

‣ 0x10, 0x32, `0x10` , `0x32` , `0x10` , `0x32` , `0x10` , `0x34` : 指明4位pin_codeASCII码值，其格式为 `0x10`
,ASCII_Value, 0x10,ASCII_Value,...，如果pin_code长度为N，则会有N组 `0x10` , ASCII_Value。

#### 若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "cmd": 5,
    "data_len": 1,
    "data": [0]
  }
}
```

若执行失败，则返回的data为:[3]，其3指示错误码。其错误定义如下：

0: Success   
1: General failure   
2: Memory full   
3: Duplicate Code error

注意：如果原先userId指定的用户已经有设置，则必须先执行ExecuteDoorLockCommand{command `= 7` }
删除掉该用户，然后再执行ExecuteDoorLockCommand{command `= 5` } 设置用户，否则会返回错误。

#### 2. 查询门锁密码用户

一次只能查询一个密码用户的设置信息，必须提供UserID，其参数如下：

• zcl: `0x0101`   
• endpoint: `1`   
• command: `6` 指明是查询门锁密码用户   
• command_data: `[0x29,0,5]`

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 257, \"endpoint\": 1, \"command\": 6, \"command_data\": [0x29, 0, 5]}"
}
```

command_data参数说明：

`0x29` ,0,5: 指明需要操作的UserId，5表示UserId是5。DoorLock的UserId范围请参考 设置门锁密码用户 说明。

若执行成功则Response如下：

```json
{
  "code": 0,   
  "message": {
    "cmd": 6, 
    "data_len": 9, 
    "data": [5,0,1,0,4,255,255,255,255]
  }
}
```

若查询的门锁用户不存在，则返回的data如下:[5,0,0,255,0]，指明userId `= 5` 不存在配置。

#### 3. 删除门锁密码用户

删除门锁密码用户，其参数如下：

• zcl: `0x0101`   
• endpoint: `1`   
• command: `7` 指明是删除门锁密码用户   
• command_data: `[0x29,0,5]`

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 257, \"endpoint\": 1, \"command\": 7, \"command_data\": [0x29, 0, 5]}"
}
```

command_data参数说明：

`0x29, 0, 5` : 指明需要操作的UserId，5表示UserId是5。DoorLock的UserId范围请参考 设置门锁密码用户 说明。

#### 若执行成功则Response如下：

```json
{
  "code": 0, 
  "message": {
    "cmd": 7, 
    "data_len": 1, 
    "data": [0]
  }
}
```

#### 4. 设置门锁门卡用户

设置门锁门卡用户，其参数如下：

• zcl: `0x0101`   
• endpoint: `1`   
• command: `0x16` 指明是设置门锁门卡用户   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 257, \"endpoint\": 1, \"command\": 22, \"command_data\": [0x29, 0, 0xF4, 0x28, 1, 0x30, 0, 0x10 , 4, 0x10 , 0x32, 0x10, 0x32, 0x10, 0x32, 0x10 , 0x34]}"
}
```

command_data参数说明：

‣ 0x29,0,0xF4: 指明需要操作的UserId， `0xF4` 表示UserId是0xF4。DoorLock的UserId范围在 `[1~254]`
，但具体可以填写的值需要参考门锁说明书，例如有些门锁限定范围是 `[242~250]` 。

‣ `0x28, 1` : 指明UserStatus，1表示启用；3表示禁用；  
‣ `0x30, 0` : 指明UserType，其定义如下：- 0 Unrestricted User（默认）；- 1 Year Day Schedule User；- 2 Week Day Schedule
User ；- 3 Master User；- 4 Non Access User  
‣ `0x10, 4` : 指明门卡ID长度，4表示其长度为4位。  
‣ `0x10` , `0x32` , `0x10` , `0x32` , `0x10` , `0x32` , `0x10` , `0x34` : 指明4位门卡ID的ASCII码值，其格式为 `0x10`
,ASCII_Value, 0x10,ASCII_Value,...，如果pin_code长度为N，则会有N组 `0x10` , ASCII_Value。

#### 若执行成功则Response如下：

```json
{
  "code": 0,   
  "message": {
    "cmd": 0x16, 
    "data_len": 1, 
    "data": [0]
  }
}
```

若执行失败，则返回的data为:[3]，其3指示错误码。其错误定义如下：

0: Success   
1: General failure   
2: Memory full   
3: Duplicate Code error

注意：如果原先userId指定的用户已经有设置，则必须先执行ExecuteDoorLockCommand{command `= 0x18`}
删除掉该用户，然后再执行ExecuteDoorLockCommand{command `= 0x16`} 设置用户，否则会返回错误。

#### 5. 查询门锁门卡用户

一次只能查询一个门卡用户的设置信息，必须提供UserID，其参数如下：

• zcl: `0x0101`   
• endpoint: `1`   
• command: `0x17` 指明是查询门锁门卡用户   
• command_data: `[0x29,0,0xF4]`

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 257, \"endpoint\": 1, \"command\": 23, \"command_data\": [0x29, 0, 0xF4]}"
}
```

command_data参数说明：

0x29,0,0xF4: 指明需要操作的UserId，0xF4表示UserId是0xF4。DoorLock的UserId范围请参考 设置门锁门卡用户 说明。

若执行成功则Response如下：

```json
{
  "code": 0,   
  "message": {
    "cmd": 0x17, 
    "data_len": 9, 
    "data": [0xF4,0,1,0,4,255,255,255,255]
  }
}
```

若查询的门锁用户不存在，则返回的data如下:[0xF4,0,0,255,0]，指明userId=0xF4不存在配置。

#### 6. 删除门锁门卡用户

删除门锁门卡用户，其参数如下：

• zcl: `0x0101`   
• endpoint: `1`   
• command: `0x18` 指明是删除门锁门卡用户   
• command_data: `[0x29,0,0xF4]`

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 257, \"endpoint\": 1, \"command\": 24, \"command_data\": [0x29, 0, 0xF4]}"
}
```

command_data参数说明：

`0x29, 0, 0xF4` : 指明需要操作的UserId，0xF4表示UserId是0xF4。DoorLock的UserId范围请参考 设置门锁门卡用户 说明。

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "cmd": 7,
    "data_len": 1,
    "data": [0]
  }
}
```

### UpdateNetworkChannel

修改ZigBee网络信道。

其参数如下：

• channel: 想要设置的ZigBee网络信道，推荐通道为: 11, 15, 20, 25

例如想要切换ZigBee网络信道至20，可以下发如下命令：  
Request参数示例：

```json
{
  "agt": "AGT",
  "act": "UpdateNetworkChannel",
  "actargs": {"channel": 20}
}
```

若执行成功则Response如下：

`{"code": 0, "message": "success"}`

#### 注意：

切换ZigBee网络的信道会导致网络下所有的设备重新连接，若无必要，请不要随意切换ZigBee网络的信道。并且选择ZigBee网络的信道也需要慎重考虑与环境网络，例如Wi-Fi网络的冲突。请优先使用我们推荐的信道
11, 15, 20, 25。

提示：如何查询当前ZigBee网络信道  
可以调用ZigBeeCtl请求，参数为：

```json
{
  "agt": "AGT",
  "act": "Native",
  "actargs": "{\"cmd\": \"ctl\", \"proc\": \"get_network_state\"}"
}
```

若执行成功，则Response如下：

```json
{
  "code": 0,
  "message": "nodeId : 0; PinId : 52775; Channel : 20"
}
```

Channel指示当前的网络信道。

### SetValue

设置ZigBee设备特定zcl下相关属性。其参数如下：

• zcl: 特定zcl  
• endpoint: 特定endpoint  
• attributeId: 指明需要设置的属性ID  
• attributeData: 指明需要设置的属性数值

#### 设置电池类设备的低电压门限，参数选择如下：

• zcl: 固定为 `0x0001` • endpoint: 固定为 1• attributeId: 可选值有如下：

• BatteryVoltageMinThreshold 0x0036  
• BatteryVoltageThreshold1 0x0037  
• BatteryVoltageThreshold2 0x0038  
• BatteryVoltageThreshold3 0x0039

• attributeData: 为2个bytes值，第一个byte固定为 `0x20` ，第二个byte为需要设置的低电压门限值，其值是电压值，例如 `0x13`
指明其电压值为 `1.9v` ，当电压低于1.9v就会触发越限。

例如设置ZigBee设备的低电压门限，可以下发如下命令：

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "SetValue",
  "actargs": "{\"me\": \"6df0\", \"zcl\": 0x0001, \"endpoint\": 1, \"attributeId\": 0x0037, \"attributeData\": [0x20, 0x13]}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": "success"
}
```

### SetCommand

设置ZigBee设备特定zcl下相关命令。其参数如下：

• zcl: 特定zcl  
• endpoint: 特定endpoint  
• commandData: 指明需要设置的命令数值

例如设置ZigBee人体存在感应器的指示灯开关（开），可以下发如下命令：

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "SetCommand",
  "actargs": "{\"me\": \"59ff\", \"zcl\": 0xef00, \"endpoint\": 1, \"commandData\": [0x21,0x00,0x00,0x21,0x01,0x6B,0x21,0x01,0x00,0x20,0x01]}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": "success"
}
```

注意：SetCommand 设置的ZigBee设备命令，可以通过使用基本API文档中的 EpGetAttrs 接口获取下发的命令的值，在 EpGetAttrs
接口的返回信息中我们用 `P_xxx` 来表示对应命令的当前值。

通过 SetCommand 下发的命令值，不一定全部都可以在 EpGetAttrs 中获取对应的下发命令值，具体根据 EpGetAttrs 实际返回值为准。

SetCommand 命令根据设备的类型进行下发参考：

| 设备类型（cls）   | 命令名    | 动作参数(actargs)                                                                                                                                                          | P_xx  |
|:------------|:-------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------|
| **人体存在感应器** | 检测微动状态 | zcl: `0xef00`, endpoint: 1, commandData: 打开： `[0x21,0x00,0x00,0x21,0x01,0x6E,0x21,0x01,0x00,0x20,0x01]` 关闭： `[0x21,0x00,0x00,0x21,0x01,0x6E,0x21,0x01,0x00,0x20,0x00]` | P_JOG |
|             | 检查存在状态 | zcl: `0xef00`, endpoint: 1, commandData: 打开： `[0x21,0x00,0x00,0x21,0x01,0x6F,0x21,0x01,0x00,0x20,0x01]` 关闭： `[0x21,0x00,0x00,0x21,0x01,0x6F,0x21,0x01,0x00,0x20,0x00]` | P_PSE |
|             | 指示灯开关  | zcl: `0xef00`, endpoint: 1, commandData: 打开： `[0x21,0x00,0x00,0x21,0x01,0x6B,0x21,0x01,0x00,0x20,0x01]` 关闭： `[0x21,0x00,0x00,0x21,0x01,0x6B,0x21,0x01,0x00,0x20,0x00]` | P_LED |

| 设备类型（cls）      | 命令名       | 动作参数(actargs)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | P_xx  |
|:---------------|:----------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------|
| **ZG#TS06012** | 灵敏度设置     | zcl: `0xef00`, endpoint: 1, commandData: 灵敏度设置范围为0-100%，delta=10 默认值（设置40%）：`[0x21,0x00,0x00,0x21,0x02,0x02,0x21,0x04,0x00,0x23,0x28,0x00,0x00,0x00]` 设置需要将以上默认数组值中按数组索引从0算起的第10个索引值设置为你需要设置的值。如设置为50%，则下发commandData：`[0x21,0x00,0x00,0x21,0x02,0x02,0x21,0x04,0x00,0x23,0x32,0x00,0x00,0x00]`                                                                                                                                                                                                                                                                                                    | P_SES |
|                | 动态持续时间(秒) | zcl: `0xef00`, endpoint: 1, commandData: 设置30s： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x00]` 设置1min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x01]` 设置2min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x02]` 设置3min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x03]` 设置5min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x04]` 设置10min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x05]` 设置20min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x06]` 设置30min： `[0x21,0x00,0x00,0x21,0x04,0x6A,0x21,0x01,0x00,0x20,0x07]` | P_DT  |
|                | 照度补偿系数    | zcl: `0xef00`, endpoint: 1, commandData: 照度补偿系数范围为1-10倍，delta=1 默认值（设置4倍）：`[0x21,0x00,0x00,0x21,0x02,0x70,0x21,0x04,0x00,0x23,0x04,0x00,0x00,0x00]` 设置需要将以上默认数组值中按数组索引从0算起的第10个索引值设置为你需要设置的值。如设置为1倍，则下发commandData：`[0x21,0x00,0x00,0x21,0x02,0x70,0x21,0x04,0x00,0x23,0x01,0x00,0x00,0x00]`                                                                                                                                                                                                                                                                                                       | P_LXC |

| 设备类型（cls）      | 命令名    | 动作参数(actargs)                                                                                                                                             | P_xx  |
|:---------------|:-------|:----------------------------------------------------------------------------------------------------------------------------------------------------------|:------|
| **ZG#TS06012** | 照度差值设置 | zcl: `0xef00`, endpoint: 1, commandData: 照度差值范围为10-100Lux，delta=10 默认值（设置10Lux）：`[0x21,0x00,0x00,0x21,0x02,0x66,0x21,0x04,0x00,0x23,0x0A,0x00,0x00,0x00]` | P_LXD |

### StartOta

升级同一类别的ZigBee设备的固件版本。

其参数如下：

• key: 指明ZigBee设备需要升级到的特定的固件版本key

有关key定义请参考： api.EpMaintOtaFiles 接口描述有关升级状态的查询请参考： api.EpMaintOtaTasks 接口描述

升级命令下发指令如下：   
Request参数示例：

```json
{
  "agt": "AGT",
  "act": "StartOta",
  "actargs": "{\"key\": \"FL01_ZG10370104_00000002\"}"
}
```

#### 若执行成功则Response如下：

```json
{
  "code": 0,
  "message": "success"
}
```

注意：该接口现在支持升级特定ZigBee设备的固件版本。

若需要升级特定ZigBee设备，除了提供key参数之外，还需要提供 me参数。并且key的格式必须为"FL01_ZG_IO_INNER_XXXXXXXX" 或者为"
FL01_ZG_IO_OUTER_XXXXXXXX"，XXXXXXX为特定版本数字。

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "StartOta",
  "actargs": "{\"key\": \"FL01_ZG_IO_INNER_00100200\", \"me\": \"3700\"}"
}
```

### UpgradeModuleFW

升级智慧中心ZigBee模块固件版本。

其参数如下：

• bin: 提供ZigBee模块的固件的内容，其内容为固件的原始内容的Base64编码• url: 指明ZigBee模块的固件的URL地址

#### 提示：

bin与url参数必须提供一个，若提供了bin则优先采用bin提供的固件内容，否则将依据url指明的地址下载固件内容。

升级命令下发指令如下：

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "UpgradeModuleFW",
  "actargs": "{\"url\": \"http://www.ilifesmart.com/upgrade/LSZG01AGT/LSZG01AGTv0.1.0.6.bin\"}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": "success"
}
```

### Native

Native为高级指令，它可以完成如下的功能的执行：

#### 1. 获取智慧中心ZigBee模块固件版本

其参数如下：   
cmd: "ctl"   
proc: "get_network_version"   
查询命令下发指令如下：   
Request参数示例：

```json
{
  "agt": "THE_AGT",
  "act": "Native",
  "actargs": "{\"cmd\": \"ctl\", \"proc\": \"get_network_version\"}"
}
```}

若执行成功则Response如下：

```json
{
  "code": 0, 
  "message": "LSZG01AGT:0.1.0.7"
}
```

#### 2. 获取ZigBee设备固件版本

其参数如下：   
cmd: "ctl"   
proc: "RequestValue"   
me: "THE_ME"   
zcl: 0x0019,   
endpoint: 1,   
attributeId: 0x0002,   
toServer: 1

查询命令下发指令如下：

Request参数示例：

```json
{
  "agt": "THE_AGT",
  "act": "Native",
  "actargs": "{\"cmd\": \"ctl\", \"proc\": \"RequestValue\", \"me\": \"THE_ME\", \"zcl\": 25, \"endpoint\": 1, \"attributeId\": 2, \"toServer\": 1}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": {
    "state": 0,
    "addr_id": 2,
    "data": [0, 0, 0, 36],
    "zcl": 25
  }
}
```

返回的message.data便是需要查询的ZigBee设备的固件版本号。

#### 3. 通知设备OTA升级

其参数如下：   
cmd: "ctl"   
proc: "OtaImageNotify"   
me: "THE_ME" 需要填写实际的ZigBee设备的me属性   
manufacturer_code: 4451,   
image_type: 1,   
newfile_version: 4,

查询命令下发指令如下：

Request参数示例：

```json
{
  "agt": "THE_AGT",
  "act": "Native",
  "actargs": "{\"cmd\": \"ctl\", \"proc\": \"OtaImageNotify\", \"newfile_version\": 4, \"image_type\": 1, \"manufacturer_code\": 4451, \"me\": \"THE_ME\"}"
}
```

若执行成功则Response如下：

```json
{
  "code": 0,
  "message": "success"
}
```

#### 提示：manufacturer_code,image_type,newfile_version参数如何获取？

参考升级的OTA文件，例如OTA文件为"FL01_ZG11630001_00000004"，则其manufacturer_code为0x1163(十进制为4451)
，image_type为0x0001(十进制为1)，newfile_version为0x00000004(十进制为4)。

## 2.2 添加ZigBee设备(EpAdd)扩展说明

我们需要使用EpAdd命令的扩展参数 optarg。

### 2.2.1 请求定义

| Type                | Definition       | Must | Description                                      |
|:--------------------|:-----------------|:-----|:-------------------------------------------------|
| Interface Name      | EpAdd            |      | 添加zigBee设备                                       |
| Partial URL         | api.EpAdd        | Y    |                                                  |
| Data Format         | application/json | Y    |                                                  |
| Request Type        | HTTP POST        | Y    | 请求类型                                             |
| **Request Content** | **system**       |      |                                                  |
|                     | `ver`            | Y    | 1.0                                              |
|                     | `lang`           | Y    | en                                               |
|                     | `sign`           | Y    | 签名值                                              |
|                     | `userid`         | Y    | User ID                                          |
|                     | `appkey`         | Y    | appkey                                           |
|                     | `did`            | O    | (可选)终端唯一id。如果在授权时填入了，此处必须填入相同id                  |
|                     | `time`           | Y    | UTC时间戳，自1970年1月1日起计算的时间，单位为秒                     |
|                     | **method**       | Y    | EpAdd                                            |
|                     | **agt**          | Y    | 添加到的智慧中心Id                                       |
|                     | **params**       |      |                                                  |
|                     | `optarg`         | O    | 添加设备额外参数，这是一个可选的、高级的选项。见后面描述。数据类型是JSON对象的序列化字符串。 |
|                     | **id**           | Y    | 消息id号                                            |

### 2.2.2 扩展参数(optarg)说明

optarg参数是添加设备的额外参数，ZigBee设备需要使用optarg才能完成添加。

#### optarg关于ZigBee设备属性定义如下

"cls":"ZG",   
"exarg":{ "period": the pairing period, unit is seconds, default is 60(s)

• cls: 必须为 "ZG" ，指明待添加的是ZigBee设备。

• period: 指明调用超时时间，number类型，缺省为60秒，最大值为254秒。

注意：添加是耗时操作，HTTP Client调用必须也设置足够的调用超时时间，否则HTTP调用会提早返回超时错误，导致添加ZigBee设备不能成功。

### 2.2.3 范例

#### 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
did为DID_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

请求地址：

svrurl+PartialURL(svrurl以实际用户所在区域SvcURL为准)，例如：

https://{your-region-api-service}/app/api.EpAdd

#### 请求信息：

```json
{
  "id": 10014,
  "method": "EpAdd",
  "system": {
    "ver": "1.0",
    "lang": "zh",
    "sign": "SIGN_XXXXXXXX",
    "userid": "1111111",
    "appkey": "APPKEY_XXXXXXXX",
    "did": "DID_XXXXXXXX",
    "time": 1541398596
  },
  "params": {
    "agt": "A3MAAABPADIQRzUwNTE5Mw",
    "optarg": "{\"cls\": \"ZG\", \"exarg\": {\"period\": 60}}"
  }
}
```

签名原始字符串为：

method:EpAdd,agt:A3MAAABPADIQRzUwNTE5Mw,optarg:`{"cls":"ZG","exarg": {"period":60}}`,time:1501151764,userid:
111111,usertoken:USERTOKEN_XXXXXXXX ,appkey:APPKEY_XXXXXXXX,apptoken:APPTOKEN_XXXXXXXX

回复信息：

若执行成功则返回：

```json
{
  "id": 10014,
  "code": 0,
  "message": {
    "me": "6df0",
    "zg_nodeid": 14537
  }
}
```

若失败则返回：

```json
{
  "id": 10014,
  "code": "ErrCode",
  "message": "ErrMessage"
}
```

zg_nodeid 标识新创建的ZigBee设备的nodeId属性。

## 2.3 移除ZigBee设备(EpRemove)扩展说明

我们需要使用EpRemove命令的扩展参数 optarg。

### 2.3.1 请求定义

| Type                | Definition       | Must | Description                                      |
|:--------------------|:-----------------|:-----|:-------------------------------------------------|
| Interface Name      | EpRemove         |      | 删除设备                                             |
| Partial URL         | api.EpRemove     | Y    |                                                  |
| Data Format         | application/json | Y    |                                                  |
| Request Type        | HTTP POST        | Y    | 请求类型                                             |
| **Request Content** | **system**       |      |                                                  |
|                     | `ver`            | Y    | 1.0                                              |
|                     | `lang`           | Y    | en                                               |
|                     | `sign`           | Y    | 签名值                                              |
|                     | `userid`         | Y    | User ID                                          |
|                     | `appkey`         | Y    | appkey                                           |
|                     | `did`            | O    | (可选)终端唯一id。如果在授权时填入了，此处必须填入相同id                  |
|                     | `time`           | Y    | UTC时间戳，自1970年1月1日起计算的时间，单位为秒                     |
|                     | **method**       | Y    | EpRemove                                         |
|                     | **params**       |      |                                                  |
|                     | `agt`            | Y    | 欲删除设备的智慧中心Id                                     |
|                     | `me`             | Y    | 欲删除设备的me                                         |
|                     | `optarg`         | O    | 删除设备额外参数，这是一个可选的、高级的选项。见后面描述。数据类型是JSON对象的序列化字符串。 |
|                     | **id**           | Y    | 消息id号                                            |

### 2.3.2 扩展参数(optarg)说明

optarg参数是删除设备的额外参数，ZigBee设备需要使用optarg才能完成删除。

#### optarg关于ZigBee设备属性定义如下

• cls: 必须为 "ZG" ，指明待删除的是ZigBee设备。

• period: 指明调用超时时间，number类型，缺省为30秒，最大值为60秒。

注意：添加是耗时操作，HTTP Client调用必须也设置足够的调用超时时间，否则HTTP调用会提早返回超时错误，导致移除ZigBee设备不能成功。

• idx：ZigBee设备的nodeId，若提供了idx则会使用idx属性，否则会使用me属性确定是哪个ZigBee设备。也即是idx属性的优先级高于me属性。关于me与idx请参考
2.1.3 动作(act)定义 部分说明。

### 2.3.3 范例

#### 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
did为DID_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

请求地址：

svrurl+PartialURL(svrurl以实际用户所在区域SvcURL为准)，例如：

https://{your-region-api-service}/app/api.EpRemove

#### 请求信息：

```json
{
  "id": 10014,
  "method": "EpRemove",
  "system": {
    "ver": "1.0",
    "lang": "zh",
    "sign": "SIGN_XXXXXXXX",
    "userid": "1111111",
    "appkey": "APPKEY_XXXXXXXX",
    "did": "DID_XXXXXXXX",
    "time": 1541398596
  },
  "params": {
    "agt": "A3MAAABPADIQRzUwNTE5Mw",
    "me": "6df0",
    "optarg": "{\"cls\": \"ZG\", \"exarg\": {\"period\": 60}}"
  }
}
```

#### 签名原始字符串为：

```
method:EpRemove,agt:A3MAAABPADIQRzUwNTE5Mw,me:6df0,optarg:"{\"cls\":\"ZG\",\"exarg\":{\"period\":60}}",time:1501151764,userid:111111,usertoken:USERTOKEN_XXXXXXXX,appkey:APPKEY_XXXXXXXX,apptoken:APPTOKEN_XXXXXXXX
```

#### 回复信息：

若执行成功则返回：

```json
{
  "id": 10014,
  "code": 0,
  "message": "success"
}
```

若失败则返回：

```json
{
  "id": 10014,
  "code": "ErrCode",
  "message": "ErrMessage"
}
```

## 2.4 获取设备属性(EpGet/EpGetAll)扩展说明

EpGet接口、EpGetAll接口返回的设备与设备列表中，若是ZigBee设备，将会增加："zg_homeid", "zg_nodeid"
标识ZigBee网络PanID以及该节点的ZigBee节点ID。zg_nodeid即时上面文档描述的ZigBee节点的idx，其值为number类型。

#### 例如：

"agt": "AGT_ID",   
"agt_ver": "1.0.72p5",   
"me": "8206",   
"devtype": "ZG04110105000600",   
"name": "Light Dimmer Switch",   
"data": { "L1": { "type": 79, "v": 22, "valts": 1551940803196, "val": 22 }   
"lHeart": 1551940803,   
"stat": 1,   
"zg_homeid": 12596,   
"zg_nodeid": 13619

## 2.5 Zigbee设备特定属性说明

ZigBee设备的属性指的是LifeSmart设备模型里面定义的IO属性。有关LifeSmart设备模型请参考： 1.1 设备模型说明
，ZigBee设备的IO口命名规范请参考： 1.2 ZigBee设备规格 - ZigBee设备IO的命名规则 。

ZigBee设备的属性大部分都可以在LifeSmart已有的设备属性规格里面找到，但也存在一些特殊的，需要额外说明的属性，这些属性我们将在本章节列出来说明。有关常规的属性可以直接参考：
《LifeSmart智慧设备规格属性说明》 。

### 2.5.1 ALM0001系列告警

ALM0001系列告警是电池电量类告警，在ZigBee Cluster定义里面，0x0001特指PowerConfiguration。ALM0001系列告警其IO名称的组成为 "
ALM0001+endpoint" ，例如： "ALM00011"，"ALM00012"。

ALM0001系列告警其Value值定义如下：

| 第Bit位 | Description描述                                                                            |
|:------|:-----------------------------------------------------------------------------------------|
| 0     | BatteryVoltageMinThreshold or BatteryPercentageMinThreshold reached for Battery Source 1 |
| 1     | BatteryVoltageThreshold1 or BatteryPercentageThreshold1 reached for Battery Source 1     |
| 2     | BatteryVoltageThreshold2 or BatteryPercentageThreshold2 reached for Battery Source 1     |
| 3     | BatteryVoltageThreshold3 or BatteryPercentageThreshold3 reached for Battery Source 1     |
| 10    | BatteryVoltageMinThreshold or BatteryPercentageMinThreshold reached for Battery Source 2 |
| 11    | BatteryVoltageThreshold1 or BatteryPercentageThreshold1 reached for Battery Source 2     |
| 12    | BatteryVoltageThreshold2 or BatteryPercentageThreshold2 reached for Battery Source 2     |
| 13    | BatteryVoltageThreshold3 or BatteryPercentageThreshold3 reached for Battery Source 2     |
| 20    | BatteryVoltageMinThreshold or BatteryPercentageMinThreshold reached for Battery Source 3 |
| 21    | BatteryVoltageThreshold1 or BatteryPercentageThreshold1 reached for Battery Source 3     |
| 22    | BatteryVoltageThreshold2 or BatteryPercentageThreshold2 reached for Battery Source 3     |
| 23    | BatteryVoltageThreshold3 or BatteryPercentageThreshold3 reached for Battery Source 3     |
| 30    | Mains power supply lost/unavailable (ie, device is running on battery)                   |

### 2.5.2 ALM0009系列告警

ALM0009系列告警是ZigBee专用告警类告警，在ZigBee Cluster定义里面，0x0009特指Alarm。  
ALM0009系列告警其IO名称的组成为 "ALM0009+endpoint" ，例如： "ALM00091"，"ALM00092"。

ALM0009系列告警的Value值定义如下：

Value组成：DEVICE_CLUSTER(2个bytes) + ALARM_CODE(1个byte)，其中DEVICE_CLUSTER为高位，ALARM_CODE为低位。

• DEVICE_CLUSTER特指发生告警的设备类型，例如门锁类设备，其DEVICE_CLUSTER的值为 "0101"  
• ALARM_CODE 为具体错误码，定义如下：

| Alarm Code                                 | Alarm Condition                                   |
|:-------------------------------------------|:--------------------------------------------------|
| **DoorLock Group (Device_Cluster=0x0101)** |                                                   |
| `0x00`                                     | Deadbolt Jammed                                   |
| `0x01`                                     | Lock Reset to Factory Defaults                    |
| `0x02`                                     | Reserved                                          |
| `0x03`                                     | RF Module Power Cycled                            |
| `0x04`                                     | Tamper Alarm - wrong code entry limit             |
| `0x05`                                     | Tamper Alarm - front escutcheon removed from main |
| `0x06`                                     | Forced Door Open under Door Locked Condition      |

### 2.5.3 门锁ALM告警

门锁告警特指ZigBee门锁设备的告警，ALM告警其IO名称的组成为 "ALM+endpoint" ，例如："ALM1"，"ALM2"。

其Value值定义如下：

| Attribute Bit Number (第Bit位) | Description描述                     |
|:-----------------------------|:----------------------------------|
| 0                            | UnknownOrMfgSpecific              |
| 1                            | LockFailureInvalidPINorID         |
| 2                            | LockFailureInvalidSchedule        |
| 3                            | UnlockFailureInvalidPINorID       |
| 4                            | UnlockFailureInvalidSchedule      |
| 5                            | Non-Access User Operational Event |

注：门锁ALM告警IO仅存在于ZigBee门锁设备下面。

### 2.5.4 动态/门禁感应器ALM告警

ZigBee动态/门禁感应器ALM告警特指ZigBee动态或门禁感应器的告警，ALM告警其IO名称的组成为 "ALM+endpoint" ，例如： "ALM1"，"
ALM2"。

其Value值定义如下：

| Attribute Bit Number (第Bit位) | Meaning             | Values                                                                              |
|:-----------------------------|:--------------------|:------------------------------------------------------------------------------------|
| 0                            | Alarm1              | 1 - opened or alarmed / 0 - closed or not alarmed                                   |
| 1                            | Alarm2              | 1 - opened or alarmed / 0 - closed or not alarmed                                   |
| 2                            | Tamper              | 1 - Tampered / 0 - Not tampered                                                     |
| 3                            | Battery             | 1 - Low battery / 0 - Battery OK                                                    |
| 4                            | Supervision reports | 1 - Reports / 0 - Does not report                                                   |
| 5                            | Restore reports     | 1 - Reports restore / 0 - Does not report restore                                   |
| 6                            | Trouble             | 1 - Trouble/Failure / 0 - OK                                                        |
| 7                            | AC Mains            | 1 - AC/Mains fault / 0 - AC/Mains OK                                                |
| 8                            | Test                | 1 - Sensor is in test mode / 0 - Sensor is in operation mode                        |
| 9                            | Battery Defect      | 1 - Sensor detects a defective battery / 0 - Sensor battery is functioning normally |

注：动态/门禁ALM告警IO仅存在于ZigBee动态/门禁设备下面。

### 2.5.5 ALM0FA0系列告警

ALM0FA0系列告警是FUKI IO门锁类告警。ALM0FA0系列告警其IO名称的组成为"ALM0FA0+endpoint" ，例如： "ALM0FA01"，"ALM0FA02"。

ALM0FA0系列告警其Value值定义如下：  
Value值占用4个Bytes，0xXXYYAABB。 (XX是高位,BB是低位)Byte(XX)表示门锁的开关状态；

- 0x01: OPEN - 0x02: KEEP - 0x03: CLOSE

Byte(YY)表示门磁的吸合状态；- 0x01: 表示开，即没有吸合- 0x02: 表示关，即已经吸合  
当Byte(AA)值为 0~9 时，表示是Master Id，这时候Byte(BB)值表示用户Id；  
当Byte(AA)值为0xff时，表示辅助信息，这时候Byte(BB)值表示特定告警信息，具体定义如下：

| BB告警定义 | Description描述             |
|:-------|:--------------------------|
| `0xF0` | O/C按钮操作 (O/C ボタン操作)       |
| `0xF1` | 拇指转动操作 (サムターン操作)          |
| `0xF2` | 远程控制操作(控制中) (リモコン操作(検討中)) |
| `0xF3` | 远程操作 (リモート操作)             |
| `0xF4` | 主子操作 (メインサブ操作)            |
| `0xF5` | 自动锁定 (自動施錠)               |
| `0xF6` | 通过触摸数字键盘进行锁定 (テンキータッチで施錠) |
| `0xF7` | 认证失败告警 (認証失敗警報)           |
| `0xF8` | 清除告警 (こじあけ警報)             |
| `0xF9` | 低压警报 (低電圧警報)              |
| `0xFA` | 解锁失败 (開錠失敗)               |
| `0xFB` | 保持失败 (Keep 失敗)            |
| `0xFC` | 锁定失败 (施錠失敗)               |
| `0xFE` | 门传感器通知 (ドアセンサー通知)         |
| `0xFF` | 获取状态 (状態取得)               |

### 2.5.6 动态/门禁感应器ALM_T告警

ZigBee动态/门禁感应器ALM_T告警特指ZigBee动态或门禁感应器的防撬告警，ALM_T告警其IO名称的组成为 "ALM_T+endpoint" ，例如： "
ALM_T1"，"ALM_T2"。

其Val值定义如下：

| Val值 | Meaning |
|:-----|:--------|
| 1    | 有防撬告警   |
| 0    | 没有告警    |

注：动态/门禁ALM_T告警IO仅存在于ZigBee动态/门禁设备下面。

### 2.5.7 A警报

A指示警报信息，一般A属性都是由ZigBee设备原始的ALM属性推导而出。  
A警报其IO名称的组成为 "A+endpoint" ，例如： "A1"，"A2"。

其Val值定义如下：

| Val值 | Meaning |
|:-----|:--------|
| 1    | 有警报     |
| 0    | 没有警报    |

注：A警报IO一般存在与ZigBee的感应器设备。

## 2.6 Zigbee设备特定指令说明

2.6.1 FUKI IO Smart DoorLock

### ExecuteDoorLockCommand

该指令根据command属性不同，可以设置/查询/删除 ZigBee门锁的密码用户和门卡用户

#### 1. 设置门锁用户

设置门锁用户，包括密码与IC门卡用户，其参数如下：

• zcl: `0x0fa0`   
• endpoint: `1`   
• command: `0x6031` 指明是设置门锁密码/IC用户   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x06031, \"command_data\": [0x29, 0x00, 0x0b, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x05, 0x04, 0x32, 0x32, 0x32, 0x33]}"
}
```

command_data参数说明：

‣ 0x29 , 0x00 , 0x0b : 指明需要操作的UserId。0x29 : 标识是用户Id数据；0x00 : Master Id，可以为 0x00~0x09 ；0x0b :
用户Id在Master Id为 0x00 时范围为 0x0a~0x63 ；在Master Id为 0x01~0x09 时范围为 0x00~0x63 ；  
‣ 0x00 , 0x00 , 0x00 , 0x00 : 指明有效开始时间，为UTC时间戳，单位秒；  
‣ 0x00 , 0x00 , 0x00 , 0x00 : 指明有效结束时间，为UTC时间戳，单位秒；  
‣ 0x00 , 0x00 : 保留字节；  
‣ 0x01 : 操作类型， 0x01 :新添加； 0x02 :变更；  
‣ 0x05 : 指明认证类型，其定义如下：- 0x01 owner PIN, 认证数据为12bytes；- 0x02 master PIN，认证数据为10bytes；- 0x03 用户IC(
16bytes) + PIN (3bytes)，认证数据19bytes，如果IC不满16字节，需在后面补0；0x04 用户IC(16bytes)
，认证数据16bytes，如果不满16字节，需在后面补0；0x05 用户PIN(8bytes)，可以设置为 4~8 字节。PIN的长度可以通过"数据长度"来设置；-
0x06 一次性 PIN(11bytes)，认证数据11bytes；  
‣ 0x04 : 指明认证数据长度，4表示其长度为4位。  
‣ 0x32 , 0x32 , 0x32 , 0x33 : 认证数据，为ASCII码值。

```json
{
  "code": 0,  
  "message": {
    "cmd": 0x6030,
    "data_len": 3,
    "data": [0x01,0x00,0x0b]
  }
}
```

返回数据说明：  
cmd指示应答，这里为0x6030；  
data为3个byte长度的数据，其值说明如下：

‣ 0x01 : 返回值- 0x01 成功- 0x02 已经完成最大用户录入- 0x03 密码重复(对应同一个master下面重复)- 0x04 卡重复(
对应master下面或者其它master下面已经存在)- 0x0N 其它错误

‣ 0x00 : Master Id  
‣ 0x0b : 用户Id

#### 2. 查询门锁用户

一次只能查询一个门锁用户的设置信息，必须提供UserID，其参数如下：

• zcl: `0x0fa0`   
• endpoint: `1`   
• command: `0x6061` 指明是查询门锁用户   
• command_data: `[0x29,0x00,0x0b]`

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x6061, \"command_data\": [0x29, 0x00, 0x0b]}"
}
```

command_data参数说明：

‣ 0x29, 0x00 , 0x0b : 指明需要操作的UserId。0x29 : 标识是用户Id数据；0x00 : Master Id，可以为 0x00~0x09 ；0x0b : 用户Id在Master
Id为 0x00 时范围为 0x0a~0x63 ；在Master Id为 0x01~0x09 时范围为 0x00~0x63 ；

若执行成功则Response如下：

```json
{
  "code": 0,   
  "message": {
    "cmd": 0x6060, 
    "data_len": 19, 
    "data": [0x01,0x00,0x0b,0,0,0,0,0,0,0,0,0,0,5,4,50,50,50,51]
  }
}
```

#### 返回数据说明：

cmd指示应答，这里为0x6060；data_len指示data数据为19个byte长度的数据，其值说明如下：

‣ 0x01 : 返回值- 0x01 成功- 0x02 Master Id不存在- 0x03 用户Id不存在

‣ 0x00 : Master Id  
‣ 0x0b : 用户Id  
‣ 0x00 , 0x00 , 0x00 , 0x00 : 指明有效开始时间，为UTC时间戳，单位秒；  
‣ 0x00 , 0x00 , 0x00 , 0x00 ; 指明有效结束时间，为UTC时间戳，单位秒；  
‣ 0x00 , 0x00 : 保留字节；  
‣ 5: 指明认证类型，具体值定义请参考 添加门锁用户 说明  
‣ 4: 指明认证数据长度  
‣ `50, 50, 50, 51` : 认证数据(PIN、IC等)

#### 3. 删除门锁用户

删除门锁用户，其参数如下：

• zcl: `0x0fa0`   
• endpoint: `1`   
• command: `0x6041` 指明是删除门锁用户   
• command_data: `[0x29,0x00,0x0b]`

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x6041 , \"command_data\": [0x29, 0x00 , 0x0b]}"
}
```

command_data参数说明：

‣ 0x29 , 0x00 , 0x0b : 指明需要操作的UserId。0x29 : 标识是用户Id数据；0x00 : Master Id，可以为 0x00~0x09 ；0x0b :
用户Id在Master Id为 0x00 时范围为 0x0a~0x63 ；在Master Id为 0x01~0x09 时范围为 0x00~0x63 ；

#### 若执行成功则Response如下：

```json
{
  "code": 0,  
  "message": {
    "cmd": 0x6040,
    "data_len": 3,
    "data": [0x01,0x00,0x0b]
  }
}
```

返回数据说明：  
cmd指示应答，这里为0x6040；  
data为3个byte长度的数据，其值说明如下：  
‣ 0x01 : 返回值- 0x01 删除成功- 0x02 Master Id不存在- 0x03 用户Id不存在  
‣ 0x00 : Master Id  
‣ 0x0b : 用户Id

提示：如果删除用户的时候，如果用户Id设置为0xff，则将会删除该Master下所有的用户。

#### 4. 查询门锁信息

查询门锁信息，其参数如下：

• zcl: `0x0fa0`  
• endpoint: `1`  
• command: `0x6071` 指明是查询门锁信息  
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x6071, \"command_data\": []}"
}
```

#### 若执行成功则Response如下：

```json
{
  "code": 0, 
  "message": {
    "cmd": 0x6070, 
    "data_len": 85, 
    "data": [0,0,0,0,0,1,1,38,0,0,0,0,50,90,0,3,0,105,83,76,45,48, 48,49,0,0,0,0,0,0,0,0,0,0,0,0,0,76,1,0,0,236,212,128,93,52,48,56, 66,49,57,51,51,49,48,48,49,49,51,1,8,0,13,111,0,18,255,70,28,0,0, 0,0,0,0,0,0,0,0,213,184,201,154,28,232]
  }
}
```

### 返回数据说明：

cmd指示应答，这里为0x6070；data_len指示data数据为85个byte长度的数据，其值说明如下：

| 命令Id(Command Id) | 数据长度 (Bytes) | 命令说明                                                                                                                                                                                                                    | 返回示例                                            |
|:-----------------|:-------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------|
| 版本号              | 12Bytes      | 1-2Byte: Leader's Hardware version<br>3-4Byte: Leader's firmware version<br>5-6Byte: Heart version of the lock<br>7-8Byte: Rock firmware version<br>9-10Byte: BLE heart wear version<br>11-12Byte: BLE firmware version | 0,0,0,0,0,1,1,38,0,0,0,0                        |
| 电池电量             | 1Byte        | 1~100百分比                                                                                                                                                                                                                | 50                                              |
| 用户总数             | 2Bytes       | 低位优先                                                                                                                                                                                                                    | 90,0                                            |
| 已经配置的用户数         | 2Bytes       | 低位优先                                                                                                                                                                                                                    | 3,0                                             |
| 型号               | 16Bytes      |                                                                                                                                                                                                                         | 105,83,76,45,48,48,49,0,0,0,0,0,0,0,            |
| 完成设置的遥控数         | 2Bytes       | 低位优先                                                                                                                                                                                                                    | 0,0                                             |
| 完成设置的智能手机数       | 2Bytes       | 低位优先                                                                                                                                                                                                                    | 0,0                                             |
| 操作次数             | 4Bytes       | 开锁关锁次数，不会因为恢复出厂设置而被清除                                                                                                                                                                                                   | 76,1,0,0                                        |
| 初始化时间            | 4Bytes       | 初始化时间不会因为恢复出厂设置而被清除                                                                                                                                                                                                     | 236,212,128,93                                  |
| 序列号(SN)          | 14Bytes      |                                                                                                                                                                                                                         | 52,48,56,66,49,57,51,51,49,48,48,49,49,51       |
| 通信端口信息           | 20Bytes      | 1B: Communication board type (1: Zigbee, 2: WiFi, 3: NB)<br>1B: Length<br>18B: Data contents (Zigbee and Wifi: Mac, NB: IMEI)                                                                                           | 1,8,0,13,111,0,18,255,70,28,0,0,0,0,0,0,0,0,0,0 |
| BLE MAC          | 6Bytes       |                                                                                                                                                                                                                         | 213,184,201,154,28,232                          |

#### 5. 查询门锁历史

查询门锁历史，其参数如下：

• zcl: `0x0fa0`   
● endpoint: `1`   
• command: `0x6081` 指明是查询门锁历史   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x6081, \"command_data\": []}"
}
```

```json
{
  "code": 0, 
  "message": {
    "cmd": 0x6080, 
    "data_len": 50, 
    "data": [6,0,26,108,239,93,5,0,0,0,38,108,239,93,21,0,0,0,45,108,239,93,5,0,0, 0,125,114,239,93,33,0,0,11,140,114,239,93,28,0,0,0,151,114,239,93,1,0, 0,11]
  }
}
```

### 返回数据说明：

cmd指示应答，这里为0x6080；data_len指示data数据为50个byte长度的数据，其值说明如下：

| 命令Id(Command Id) | 数据长度 (Bytes)       | 命令说明                                                                                   | 返回示例                                                                                                   |
|:-----------------|:-------------------|:---------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------|
| 历史数              | 2Bytes             | 从最远的时间开始获取，最多一次可以获取6个历史记录。获取后，删除门锁上对应的历史记录。门锁最多可以保存4000个历史数据，超过部分将会覆盖最远时间的历史数据。注意：低位优先 | 6,0                                                                                                    |
| 历史数据内容           | n*8Bytes (每个历史8字节) | 4B：时间<br>2B：种类信息(参考历史数据一览表)<br>2B：其他信息                                                 | 26,108,239,93,5,0,0,0<br>38,108,239,93,33,0,0,11<br>140,114,239,93,28,0,0,0<br>151,114,239,93,1,0,0,11 |

#### 6. 查询门锁状态

查询门锁状态，其参数如下：

• zcl: `0x0fa0`   
• endpoint: `1`   
• command: `0x6091` 指明是查询门锁状态   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x6091, \"command_data\": []}"
}
```

#### 若执行成功则Response如下：

```json
{
  "code": 0,  
  "message": {
    "cmd": 0x6090,
    "data_len": 2,
    "data": [2,2]
  }
}
```

### 返回数据说明：

cmd指示应答，这里为0x6090；data_len指示data数据为2个byte长度的数据，其值说明如下：

| 命令Id(Command Id) | 数据长度 (Bytes) | 命令说明         | 返回示例 |
|:-----------------|:-------------|:-------------|:-----|
| 锁状态              | 1Byte        | `0x01`: OPEN 

`0x02`: KEEP
`0x03`: CLOSE | 2 |
| 磁石状态 | 1Byte | `0x01`: 开
`0x02`: 关 | 2 |

#### 7. 门锁设置

门锁设置，其参数如下：

• zcl: `0x0fa0`   
• endpoint: `1`   
• command: `0x60a1` 指明是门锁设置   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x060a1, \"command_data\": [237,212,128,93,0x01,0x01,0x03,0x01,0x00,0x00,0x01,0x00,0x00]}"
}
```

command_data参数说明：

‣ 237,212,128,93: 指明锁时间，为UTC时间戳，单位为秒，低位优先  
‣ 0x01 : 指明门把手位置， 0x00 :左； 0x01 :右(默认位置)；  
‣ 0x01 : 指明音量大小， 0x00 :静音； 0x01 :小； 0x02 :中(默认)； 0x03 :大；  
‣ 0x03 : 指明关锁模式， 0x00 :自动-短(默认)； 0x01 :自动-长； 0x02 :手动； 0x03 :开锁一样；  
‣ 0x01 : 指明O/C按钮， 0x00 :无效； 0x01 :有效(默认)；  
‣ 0x00 : 保留字节；  
‣ 0x00 : 指明分体， 0x00 :主体； 0x01 :分体；  
‣ 0x01 : 指明操作有无磁铁感应器， 0x00 :无； 0x01 :有；  
‣ 0x00 : 指明操作锁舌后连续接触设置， 0x00: ON (连续开、默认)；0x01:OFF(连续关)；  
0x00 : 指明电机电压， 0x00: 4.5v (默认)； 0x01: 6v (强力)；

#### 若执行成功则Response如下：

```json
{
  "code": 0,   
  "message": {
    "cmd": 0x60a0, 
    "data_len": 1, 
    "data": [0x01]
  }
}
```

返回数据说明：

cmd指示应答，这里为0x60a0；data为1个byte长度的数据，其值说明如下：

‣ 0x01 : 返回值 - 0x01 成功 - 0x00 失败

#### 8. 获取门锁设置

获取门锁设置，其参数如下：

• zcl: `0x0fa0`   
• endpoint: `1`   
• command: `0x60b1` 指明是获取门锁设置   
• command_data: `[]` 具体数据

Request参数示例：

```json
{
  "agt": "AGT",
  "act": "ExecuteDoorLockCommand",
  "actargs": "{\"me\": \"6e04\", \"zcl\": 0x0fa0, \"endpoint\": 1, \"command\": 0x060b1, \"command_data\": []}"
}
```

#### 若执行成功则Response如下：

```json
{
  "code": 0,  
  "message": {
    "cmd": 0x60b0,
    "data_len": 14,
    "data": [1,237,212,128,93,1,1,3,1,0,0,1,0,0]
  }
}
```

返回数据说明：  
cmd指示应答，这里为0x60b0；  
data_len指示data数据为14个byte长度的数据，其值说明如下：

| 命令Id(Command Id) | 数据长度 (Bytes) | 命令说明                                                       | 返回示例           |
|:-----------------|:-------------|:-----------------------------------------------------------|:---------------|
| 返回值              | 1Byte        | `0x01`:成功                                                  
 `0x02`:失败        | 1            |
| 锁时间              | 4Bytes       | UTC时间，低位优先                                                 | 237,212,128,93 |
| 门把手              | 1Byte        | `0x00`:左                                                   
 `0x01`:右(默认)     | 1            |
| 音量大小             | 1Byte        | `0x00`:静音<br>`0x01`：小<br>`0x02`:中(默认)<br>`0x03`:大          | 1              |
| 关锁模式             | 1Byte        | `0x00`:自动-短(默认)<br>`0x01`：自动-长<br>`0x02`:手动<br>`0x03`:开锁一样 | 3              |
| O/C按钮            | 1Byte        | `0x00`:无效<br>`0x01`:有效(默认)                                 | 1              |
| 保留               | 1Byte        |                                                            | 0              |
| 分体               | 1Byte        | `0x00`:主体(默认)<br>`0x01`：分体                                 | 0              |
| 磁铁感应器            | 1Byte        | `0x00`:无<br>`0x01`: 有(默认)                                  | 1              |
| 操作锁舌后连续接触设置      | 1Byte        | `0x00`: ON(连续开、默认)<br>`0x01`: OFF(连续关)                     | 0              |
| 电机电压             | 1Byte        | `0x00`:4.5V(默认)<br>`0x01`: 6V(强力)                          | 0              |

## 2.7 Zigbee设备特定常量定义

### 2.7.1 DoorLock

#### 2.7.1.1 Operation Event Sources

| Value | Source        |
|:------|:--------------|
| 0x00  | Keypad        |
| 0x01  | RF            |
| 0x02  | Manual        |
| 0x03  | RFID          |
| 0xFF  | Indeterminate |

#### 2.7.1.2 Operation Event Codes

| Value | Operation Event Code              | Keypad | RF | Manual | RFID |
|:------|:----------------------------------|:-------|:---|:-------|:-----|
| 0x00  | UnknownOrMfgSpecific              | A      | A  | A      | A    |
| 0x01  | Lock                              | A      | A  | A      | A    |
| 0x02  | Unlock                            | A      | A  | A      | A    |
| 0x03  | LockFailureInvalidPINorID         | A      | A  |        | A    |
| 0x04  | LockFailureInvalidSchedule        | A      | A  |        | A    |
| 0x05  | UnlockFailureInvalidPINorID       | A      | A  |        | A    |
| 0x06  | UnlockFailureInvalidSchedule      | A      | A  |        | A    |
| 0x07  | OneTouchLock                      |        |    | A      |      |
| 0x08  | KeyLock                           |        |    | A      |      |
| 0x09  | KeyUnlock                         |        |    | A      |      |
| 0x0A  | AutoLock                          |        |    | A      |      |
| 0x0B  | ScheduleLock                      |        |    | A      |      |
| 0x0C  | ScheduleUnlock                    |        |    | A      |      |
| 0x0D  | Manual Lock (Key or Thumbturn)    |        |    | A      |      |
| 0x0E  | Manual Unlock (Key or Thumbturn)  |        |    | A      |      |
| 0x0F  | Non-Access User Operational Event | A      |    |        |      |

## 3.ZigBee设备列表

| 设备名称             | 设备规格           | 设备IO属性              |
|:-----------------|:---------------|:--------------------|
| 光电感烟探测器 (ZigBee) | ZG#MIR-SM100-E | A1：警报标识，val=1标识存在警报 

ALM1：原始告警信息
BAT1：电池电量，val为电量值，范围[0~100]
v1：电压，实际电压=v1.val/10(伏特) |
| 家用燃气探测器 (ZigBee) | ZG#JT-GA102 | A1：警报标识 val=1标识存在警报
ALM1：原始告警信息 |
| 嵌入式空气环境检测仪 (ZigBee) | ZG#PMT300-S-ZTN | T1：温度值，实际温度=T1.val/10(摄氏度)
H1：湿度值，实际湿度=H1.val/10(%)
PM1：PM2.5值， val为值，单位 ug/m³
PM(1)1：PM1.0值val为值，单位ug/m³
PM(10)1：PM10值val为值，单位ug/m3 |
| 人体存在感应器 (ZigBee) | ZG#MIR-HE200 | M1：有无人体存在标识 val=1标识存在
ALM1：原始告警信息
z1：光照度，val值为光照度 |
| C700000202 | ZG#c700000202 | ALM1：原始告警信息
BAT1：电池电量，val为电量值，范围[0~100]
v1：电压，实际电压=v1.val/10(伏特)
EVTLO1：实时开锁信息
HISLK1：最近一次开锁信息 |
| INAHO.Door_Lock | ZG#INAHO.Door_Lock | ALM1：原始告警信息
BAT1：电池电量，val为电量值，范围[0~100]
v1：电压，实际电压=v1.val/10(伏特)
EVTLO1：实时开锁信息
HISLK1：最近一次开锁信息 |
| YMC420D | ZG#YMC420D | ALM1：原始告警信息
BAT1：电池电量，val为电量值，范围[0~100]
v1：电压，实际电压=v1.val/10(伏特)
EVTLO1：实时开锁信息
HISLK1：最近一次开锁信息 |
| 门锁 Tenon Doorlock | ZG#RH8005 | ALM1：原始告警信息
BAT1：电池电量，val为电量值，范围[0~100]
v1：电压，实际电压=v1.val/10(伏特)
EVTLO1：实时开锁信息
HISLK1：最近一次开锁信息 |
| ZigBee美标插座 D0013 (us) | ZG#ZBT-OnOffPlug-D0# | L1：开关
EE1：累计用电量 |
| ZigBee欧标插座 TS0121 (UK) | ZG#TS0121 | O1：开关
EE1：累计用电量 |