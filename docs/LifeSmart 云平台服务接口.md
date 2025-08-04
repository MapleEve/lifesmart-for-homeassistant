LifeSmart 云平台服务接口(v1.38)

<table><tr><td>版本</td><td>修订日期</td><td>修订人</td><td>修订内容</td></tr><tr><td>1.0</td><td>2015/10/20</td><td>Alexcheng</td><td></td></tr><tr><td>1.01</td><td>2015/10/28</td><td>AlexCheng</td><td>修改返回信息。返回字段status修改为code，其值 为错误代码。增加错误码列表</td></tr><tr><td>1.02</td><td>2015/11/4</td><td>AlexCheng</td><td>修改签名串例子中的错误格式</td></tr><tr><td>1.03</td><td>2015/11/9</td><td>Alexcheng</td><td>1：添加灯带/灯泡颜色控制 2：添加入墙开关控制 3：添加新增／删除智慧设备接口 4：添加注册用户接口</td></tr><tr><td>1.04</td><td>2015/11/19</td><td>Lewis Li</td><td>1. 修改EpGetAll/EpSet/EpGet范例 2．添加EpAdd/EpRemove接口范例 3．细化注册用户接口 4.添加灯带动态设置</td></tr><tr><td>1.05</td><td>2016/10/26</td><td>xiao Ye</td><td>1.添加Epsset， SceneGet， Sceneset接口；</td></tr><tr><td>1.06</td><td>2016/11/3</td><td>xiao Ye</td><td>1. 添加unregisterUser接口;</td></tr><tr><td>1.07</td><td>2017/1/10</td><td>Alexcheng</td><td>1：支持状态更新；2：支持多终端访问</td></tr><tr><td>1.08</td><td>2017/4/5</td><td>AlexCheng</td><td>支持多区域访问</td></tr><tr><td>1.10</td><td>2017/10/09</td><td>Jon Fan/ Pretty Ju</td><td>第二版整理</td></tr><tr><td>1.11</td><td>2018/04/20</td><td>Jon Fan</td><td>添加webSocket事件详细说明</td></tr><tr><td>1.12</td><td>2018/09/20 2018/10/08</td><td>Jon Fan Jon Fan</td><td>添加EpAdd扩展参数说明/ 添加EpSet扩展参数说明 修正文档描述不合理的部分 添加EpUpgradeAgt，EpRebootAgt,</td></tr><tr><td></td><td></td><td></td><td>设备属性增加lHeart，lDbm说明； 增加设备模型说明； EpSet增加修改Ep/Io名称的说明；</td></tr><tr><td>1.14</td><td>2018/11/25</td><td>Jon Fan</td><td>增加EpSearchsmart，EpAddsmart接□</td></tr></table>

<table><tr><td>1.15</td><td>2018/12/05</td><td>Jon Fan</td><td>增加EpCmd，EpGetAgtState接口说明，以及修 改EpGetAll接口描述，增加agt_self以及智慧设 备的描述。</td></tr><tr><td>1.16</td><td>2018/12/12</td><td>Jon Fan</td><td>WebSocket增加aI事件通知描述</td></tr><tr><td>1.17</td><td>2019/01/24</td><td>Jon Fan</td><td>增加设备/AI的ext_loc属性说明</td></tr><tr><td>1.18</td><td>2019/02/14</td><td>Jon Fan</td><td>增加EpGetAttrs(获取设备扩展属性)接□</td></tr><tr><td>1.19</td><td>2019/03/01</td><td>Jon Fan</td><td>增加EpSet接口修改智慧中心名称说明 增加EpTestRssi(测试射频设备信号强度)接口</td></tr><tr><td>1.20</td><td>2019/06/03</td><td>Jon Fan</td><td>增加EpGet/EpGetAll接口返回的设备Io属性里面v 值的说明。增加授权返回的svrrgnid属性说明。 增加EpBatchset接口</td></tr><tr><td>1.21</td><td>2019/10/18</td><td>Jon Fan</td><td>增加EpSearchIDev，EpAddIDev接口说明</td></tr><tr><td>1.22</td><td>2019/12/30</td><td>Jon Fan</td><td>增加EpMaintotaFiles， EpMaintOtaTasks接□ 说明</td></tr><tr><td>1.23</td><td>2020/01/07</td><td>Jon Fan</td><td>增加EpMaintAgtRM接口说明</td></tr><tr><td>1.24</td><td>2020/03/11</td><td>Jon Fan</td><td>增加EpSetVar接口说明</td></tr><tr><td></td><td></td><td></td><td>EpUpgradeAgt接口增加HTTP升级方式说明</td></tr><tr><td>1.25</td><td>2020/04/08</td><td>Jon Fan</td><td>增加EpConfigAgt接口说明</td></tr><tr><td>1.26</td><td>2020/04/21</td><td>Jon Fan</td><td>设备模型增加ful1Cls描述</td></tr><tr><td>1.27</td><td>2020/07/01</td><td>Jon Fan</td><td>EpConfigAgt接口增加timezone设置</td></tr><tr><td></td><td></td><td></td><td>EpCmd接口增加云视户外摄像头声光警报设置</td></tr><tr><td>1.28</td><td>2021/06/10</td><td></td><td>更新附录1</td></tr><tr><td>1.29</td><td>2021/07/14</td><td>Jon Fan</td><td>&quot;设备模型说明”增加新属性说明</td></tr><tr><td>1.30</td><td>2022/02/08</td><td>Jon Fan</td><td>EpConfigAgt接口增加nIF配置</td></tr><tr><td>1.31</td><td>2022/03/02</td><td>Jon Fan</td><td>EpConfigAgt接口文档重新整理并增加本地互联接 口说明</td></tr><tr><td>1.32</td><td>2022/06/23</td><td>Pretty Ju</td><td>去掉Headers[&quot;X-LS-SVRRGNID&quot;]；更新附录1和 附录2；细节描述优化；</td></tr><tr><td>1.33</td><td>2022/07/27</td><td>Jon Fan</td><td>EpConfigAgt接口增加resetRfModule配置</td></tr><tr><td>1.34</td><td>2022/08/02</td><td>Pretty Ju</td><td>增加NatureCtl接口说明</td></tr><tr><td>1.35</td><td>2022/10/22</td><td>Jon Fan</td><td></td></tr><tr><td></td><td></td><td></td><td>EpMaintOtaFiles、EpMaintOtaTasks接□增加 扩展指令说明</td></tr></table>

<table><tr><td>1.36</td><td>2023/02/08</td><td>Jon Fan</td><td>WebSocket事件增加elog说明</td></tr><tr><td>1.37</td><td>2023/06/26</td><td>Jon Fan</td><td>EpConfigAgt接口增加operExSv配置</td></tr><tr><td>1.38</td><td>2023/08/22</td><td>Jon Fan</td><td>增加EpMaintCartFiles接口说明</td></tr></table>

![](images/8440021fa280ff6718ff725551ddfd9b54f1f94a678015e0785edce3498e877a.jpg)

# 1.介 … .6

…

2.注册智能应用… ….  
3.智能应用获取用户授权. ..73.1.请求URL地. ..73.2.请求参数 ..3.3. 授权过程… .3.4. usertoken更新…… ..10  
4.智能应用AP. ..134.1. HTTPS请求数据格式规范.4.1.1.URL. .134.1.2.请求 Body JSON格式… ..134.1.4.应答JSON格式..
..154.2.安全策略. ..154.2.1.签名算法. … ..164.2.2.签名范例…4.3.错误码…4.4.设备模型说明.… ..194.5. 接口定义… …
..2.4.5.1.EpAddAgt 增加智慧中心……… ..224.5.2.EpDeleteAgt 删除智慧中心4.5.4.EpAdd 添加设备…… ….4.5.5.EpRemove
删除设备..4……4.5.8.EpSet 控制设备……404.5.9.EpsSet 控制多个设备……4.5.10.SceneGet 获取场景 … ….54.5.11.SceneSet
触发场景…… … ….474.5.12.EpUpgradeAgt 升级智慧中心…4.5.13.EpRebootAgt 重启智慧中心. ….4.5.14.EpGetAgtLatestVersion
获取智慧中心最新版本…4.5.15.EpSearchSmart 获取智慧中心搜索到的附近智慧设备4.5.16.EpAddSmart
把搜索到的附近智慧设备添加到智慧中心……….604.5.17.EpGetAgtState 获取智慧中心状态 …4.5.18.EpCmd 控制设备(高级命令)….
….44.5.19.EpSetVar 控制设备(低级命令). ….4.5.20.EpGetAttrs 获取设备扩展属性. ….0

4.5.21.EpTestRssi 测试射频设备信号强度. ..72  
4.5.22.EpBatchSet 批量快速设置多个设备属性. .  
4.5.23.EpSearchIDev 获取智慧中心搜索到的附近IP网络设备…….79  
4.5.24.EpAddIDev把搜索到的附近IP网络设备添加到智慧中心…….1  
4.5.25.EpMaintOtaFiles 查看或维护智慧中心上的OTA文件列表…….5  
4.5.26.EpMaintOtaTasks 查看或维护智慧中心上的OTA任务列表…….89  
4.5.27.EpMaintAgtRM 备份或恢复智慧中心上的配置.. ..92  
4.5.28.EpMaintCartFiles 查看或维护智慧中心上的Cart文件列表…….96  
4.5.29.EpConfigAgt 设置智慧中心配置 ..99  
4.5.30.NatureCtl 设置Nature面板首页按键等配置 ..108  
5.设备属性定义 115  
6.发现协议… 115  
7.状态接收…… … ….116  
7.1.流程… ….7  
7.2.URL..  
7.3. WebSocket认证 .118  
7.3.1.JSON请求数据格式. …18  
7.3.2.范例… …18  
7.4. WebSocket认证用户移除… ….120  
7.4.1.JSON请求数据格式  
7.4.2.范例… ….120  
7.5.事件格式. ..121  
7.6.事件数据信息. ..121  
8.智能应用用户API. ..132  
8.1.注册用户. …  
8.1.1.JSON请求数据格式 ..33  
8.1.2.范例..  
8.2.删除用. … …..5  
8.2.1.JSN请求据格式…135  
8.2.2.范例.  
附录1国家域名缩写以及服务提供映射. ..137  
附录2服务代号及地址对应表.. .141

# 1.介绍

LifeSmart云平台对外提供智慧设备的添加、查找、状态查询以及控制等服务。第三方应用通过HTTPS连接接入云平台，就可完成对智慧设备的操作与管理。同时，为了连接安全，所有请求请务必遵循云平台的签名规则。 - -

# 1.1接口使用流程

第三方应用使用云平台服务之前，需要先向LifeSmart注册智能应用，获得唯一的 appkey
和apptoken，然后第三方应用需由用户授权获取设备的访问控制权限才能提供服务。如果该用户没有注册LifeSmart账号，则可以通过云平台的用户注册接口注册用户并完成自动授权，得到
userid 和usertoken以及过期时间expiredtime。 -

![](images/d6945ce00e83642eddde9ba05cf95d5748d09e67aff841e82cae880072e0b478.jpg)

# 2.注册智能应用

智能应用需要使用LifeSmart云平台的服务，必须先在LifeSmart云平台注册，获取appkey和apptoken，注册成功后将获取到如下信息：

<table><tr><td>名称</td><td>备注</td></tr><tr><td>appkey</td><td>应用的key，每个应用必须申请一个属于自己的唯一的key</td></tr><tr><td>apptoken</td><td>应用的token，请妥善保管好该token，不要泄漏</td></tr></table>

Note:注册方式请与LifeSmart公司联系或通过LifeSmart开放平台自主注册并申请第三方应用。

# 3.智能应用获取用户授权

# 3.1.请求URL地址

https://api.ilifesmart.com/app/   
auth.authorize?id $\equiv$ \*\*\*&appkey $=$ \*\*\*&time $: =$ \*\*\*&auth_callback $\equiv$ \*\*\*&did $\equiv$
\*\*\*&sign   
=\*\*\*&lang $=$ zh

# 3.2.请求参数

<table><tr><td>参数名</td><td>类型</td><td>备注</td></tr><tr><td>id</td><td>int</td><td>消息id，标识这条消息，调用成功后将原样返回</td></tr><tr><td>appkey</td><td>string</td><td>智能应用申请时获得的appkey</td></tr><tr><td>time</td><td>int</td><td>UTC时间戳，自1970年1月1日起计算的时间，单位为秒</td></tr><tr><td>auth_callback</td><td>string</td><td>授权成功后回调的URL</td></tr><tr><td>sign</td><td>string</td><td>签名值，签名算法见注解</td></tr><tr><td>did</td><td>string</td><td>(可选)终端唯一id，当有多终端的时候用于区分终端</td></tr><tr><td>lang</td><td>string</td><td>显示语言类型，当前支持zh,en,jp，默认为zh</td></tr></table>

# Note:

time：时间戳，如果请求的时间与云服务平台时间相差5分钟以上，则该请求无效。

did：终端设备id，用于标识当前使用设备。如果需要支持多终端访问时，则需要传递该参数，否则不需要传递该参数。【若授权的时候包含did值，则后续的apr调用在使用授权获取的token的时候，其参数system.dia的值必须等于授权的时候填写的dia值】

sign：签名，生成算法如下：

a)
签名原始串：appkey-\*\*&authcallbac\*\*\*&did-\*\*\*&time-\*\*\*&apptoken=\*\*\*签名原始字符串除apptoken外其他字段按照字母顺序排序生成，如果有did，则进行签名，否则不填入)  
b) 将"签名原始串"进行MD5编码，并转化为32位的16进制小写字符串，作为签名值sign。  
c) 注意：lang不放入签名原始串，即不需要签名。  
d) MD5算法必须正确，可用下面字符串进行对比验证：

签名原始串：

appkey $=$ 1111111111&auth_callback $\cdot ^ { = }$ http://1ocalhost:8080/CallBack.ashx&time $= 1$
445307713&apptoken $\underline { { \underline { { \mathbf { \Pi } } } } } =$
ABCDEFGHIKJLMJOBPOOFPDFDA签名值sign应该为：0972888fac34d1d151e4433c9dc7a102

请求uRL服务地址 api.ilifesmart.com 并不是唯一，若明确为其它区域的应用，可以直接使用其它区域的uRL地址，例如一个欧洲区域的应用，可以直接使用
api.eur.ilifesmart.com 服务地址，当前也可以仍l旧使用 api.ilifesmart.com 服务地址完成应用授权，但之后的apr调用必须使用授权返回的svrurl做为服务地址。
■

具体服务地址列表请参考附录2服务代号及地址对应表

# 3.3.授权过程

输入上面URL后，出现如下界面：

![](images/0c47416b0780a56de4f6db6e1bb4e90fd8fa5529f5b5bf0b400fa7843faebbca.jpg)

输入用户名和密码，验证通过之后跳转到如下页面：

![](images/77bed661b39f0d7b402d2fcf967efb4a031506391c4137a4c841d82ca1110941.jpg)

点击授权之后页面跳转到URL提供的 auth_callback 的URL链接，URL中带有userid和usertoken等参数。智能应用端需要能读取到URL中的usertoken等内容，执行后续操作。

授权成功返回范例： "code":"success" "userid":"YOuR_UsERID",

"usertoken": "YOuR_ToKEN", "expiredtime"：YOuR_ExPIRED_TIME, "rgn":"usER_RGN", "svrurl":"uSER_SERVERURL", "svrrgnid":"
UsER_SEVER_RGNID"

⚫ 授权失败返回范例： "code":"error", "message":"ERR_MESSAGE"

<table><tr><td>属性名</td><td>类型</td><td>描述</td></tr><tr><td>id</td><td>int</td><td>消息id号，为授权URL时传入数据</td></tr><tr><td>userid</td><td>string</td><td>用户id</td></tr><tr><td>usertoken</td><td>string</td><td>用户授权roken</td></tr><tr><td>expiredtime</td><td>int</td><td>Token失效过期时间，UTC时间戳，自1970年1月1日起计算的时 间，单位为秒</td></tr><tr><td>svrurl</td><td>string</td><td>API服务地址。我们支持多区域多服务，不同用户的数据分布在 不同的服务上面，该服务URL确定操作该用户数据需要访问的服 务地址，调用API操作用户数据的时候请务必以该属性返回的 URL地址为准，否则可能不能正确访问用户数据。</td></tr><tr><td>svrrgnid</td><td>string</td><td>用户所在区域ID，例如 &quot;GS&quot;，由于支持多区域，不同用户的 所在区域可能会不同，该属性标识用户当前所在区域。</td></tr></table>

# 3.4.usertoken更新

usertoken必须在失效时间之前更新，否则就必须重新进行用户授权。

a）令牌刷新地址：用户所在 svrurl $^ +$
/auth.refreshtoken例如：用户A授权成功后所获得的svrurl $=$ "https://api.ilifesmart.com/app/",那么用户a的令牌刷新地址为：https://api.ilifesmart.com/app/auth.refreshtoken

b）HTTP请求为POST方式，内容为JSON格式

c）请求参数：

<table><tr><td>参数名</td><td>类型</td><td>备注</td></tr><tr><td>id</td><td>int</td><td>消息id号，调用成功后将原样返回</td></tr><tr><td>appkey</td><td>string</td><td>智能应用申请时获得的appkey</td></tr></table>

<table><tr><td>time</td><td>int</td><td>UTC时间戳，自1970年1月1日起计算的时间，单位为秒</td></tr><tr><td>userid</td><td>string</td><td>获取授权时得到的用户id</td></tr><tr><td>did</td><td>string</td><td>(可选)终端唯一id</td></tr><tr><td>sign</td><td>string</td><td>签名值，签名算法见注解</td></tr></table>

d)签名原始串：appkey=\*\*\*&did $= \star \star \star$ &time $=$ \*\*\*&userid=\*\*\*&apptoken $\displaystyle . =$
\*\*\*&usertoken=\*\*\*●(签名原始字符串除apptoken和usertoken外其他字段按照字母顺序排序生成)• usertoken为授权时获取的usertoken

e)签名算法与授权一样f）调用成功后返回如下信息（JSON格式）：

<table><tr><td>属性名</td><td>类型</td><td>描述</td></tr><tr><td>id</td><td>int</td><td>消息id号，为授权请求时传入的数据</td></tr><tr><td>code</td><td>string</td><td>0：成功；其他：错误码</td></tr><tr><td>message</td><td>string</td><td>如果code等于o，则为空，否则返回错误信息</td></tr><tr><td>userid</td><td>string</td><td>用户id</td></tr><tr><td>usertoken</td><td>string</td><td>用户授权roken</td></tr><tr><td>expiredtime</td><td>int</td><td>Token失效过期时间，UTC时间戳，自1970年1月1日起计算的时 间，单位为秒</td></tr></table>

g）范例如下：

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

⚫ 请求信息：

"appkey":"AppkEY_xxxxxxxx" "time"：1445307713, "userid": "1111111', "sign":"sIGN_xxxxxxxx", "id':12345

⚫ 签名原始字符串为：

appkey $\mathbf { \equiv } = \mathbf { \equiv }$ APPKEY_xxxxxxxx&time $: =$ 1445307713&userid $\cdot ^ { = }$
1111111&apptoken ${ \bf \Phi } . = { \bf \Phi } .$ APPTOKE
N_xxxxxxxx&usertoken $\underline { { \underline { { \mathbf { \Pi } } } } } =$ USERTOKEN_XXXXXXXX

# • 回复信息：

"code": 0,   
"message":"",   
"id"：12345，   
"userid": "1111111",   
"usertoken":"NEW_USERTOKEN_YYYYYYYY",   
"expiredtime": 1445955713

# 4.智能应用API

# 4.1.HTTPS请求数据格式规范

# 4.1.1.URL

请求协议：HTTPS  
请求方法：POST  
请求URL：请务必使用授权接口返回的服务器地址（svrurl字段）作为用户对应的服务地址具体服务地址列表请参考附录2服务代号及地址对应表(
请务必使用授权接口返回的svrrgnid匹配对应的webSocket服务uRL)

# 4.1.2.请求 Body JSON格式

<table><tr><td>id</td><td></td><td>消息序列号</td></tr><tr><td rowspan="7">system</td><td>ver</td><td>Protocol version</td></tr><tr><td>lang</td><td>Ianguage</td></tr><tr><td>userid</td><td>user id</td></tr><tr><td>appkey</td><td>appkey</td></tr><tr><td>did</td><td>(可选)终端唯一id，如果在授权时填写， 则此处必须填入相同id</td></tr><tr><td>time</td><td>UTC时间戳，自1970年1月1日起计算的时 间，单位为秒</td></tr><tr><td>sign</td><td>签名值</td></tr><tr><td>method</td><td></td><td>API request method name</td></tr><tr><td>params</td><td>&lt;attr&gt;:&lt;va1&gt; &lt;attr&gt;:&lt;val&gt;</td><td>方法使用的参数集合</td></tr></table>

请求字段释义如下：

system :

ver：版本号现是1.0• lang：默认值是"en"，持"en"，"zh"userid：授权时获取的userid

• appkey：智能应用注册时获取的appkey  
•
did：设备终端唯一id。如果需要多终端支持时，则必须填入。如果授权时填写该参数，则此时必须传入该参数，并且值要与授权时候填写的值相同  
⚫ time：请求时的时间戳(UTC)，零时区时间  
• sign：签名值，服务端用作签名校验。签名算法见：4.2.1

method：目前支持的命令方式如下：

<table><tr><td>方法名称</td><td>URL后缀信息</td><td>描述</td></tr><tr><td>EpAddAgt</td><td>api.EpAddAgt</td><td>添加智慧设备</td></tr><tr><td>EpDeleteAgt</td><td>api.EpDeleteAgt</td><td>删除智慧设备</td></tr><tr><td>EpGetAllAgts</td><td>api.EpGetAllAgts</td><td>查询所有的智慧中心</td></tr><tr><td>EpAdd</td><td>api.EpAdd</td><td>添加子设备</td></tr><tr><td>EpRemove</td><td>api.EpRemove</td><td>删除子设备</td></tr><tr><td>Epsearchsmart</td><td>api.Epsearchsmart</td><td>获取智慧中心搜索到的附近其它智慧设备</td></tr><tr><td>EpAddsmart</td><td>api.EpAddsmart</td><td>把搜索到的附近智慧设备添加到智慧中心</td></tr><tr><td>EpSearchIDev</td><td>api.EpSearchIDev</td><td>获取智慧中心搜索到的附近IP网络设备</td></tr><tr><td>EpAddIDev</td><td>api.BpBader</td><td>把搜索到的附近IP网络设备添加到智慧中心</td></tr><tr><td>EpGetAl1</td><td>api.EpGetAl1</td><td>查询该账户下授权给该App的所有智慧设备信 息。若该App没有摄像头权限则返回的设备列表 中不包括摄像头。</td></tr><tr><td>EpGet</td><td>api.EpGet</td><td>获取单个设备信息</td></tr><tr><td>Epset</td><td>api.Epset</td><td>控制单个设备</td></tr><tr><td>Epsset</td><td>api.Epsset</td><td>控制多个设备</td></tr><tr><td>EpCmd</td><td>api.Epcmd</td><td>控制单个设备(高级命令)</td></tr><tr><td>EpSetVar</td><td>api.Epsetvar</td><td>控制单个设备 (低级命令)</td></tr><tr><td>EpBatchset</td><td>api.EpBatchset</td><td>批量快速设置多个设备属性</td></tr><tr><td>EpGetAttrs</td><td>api.EpGetAttrs</td><td>获取设备扩展属性</td></tr><tr><td>EpTestRssi</td><td>api.EpTestRssi</td><td>测试射频设备信息强度</td></tr><tr><td>EpUpgradeAgt</td><td>api.EpupgradeAgt</td><td>升级智慧中心</td></tr><tr><td>EpRebootAgt</td><td>api.EpRebootAgt</td><td>重启智慧中心</td></tr></table>

<table><tr><td>EpGetAgtLatest version</td><td>api.EpGetAgtLates tversion</td><td>获取智慧中心最新版本号</td></tr><tr><td>EpGetAgtstate</td><td>api.EpGetAgtState</td><td>获取智慧设备状态</td></tr><tr><td>EpMaintOtaFile S</td><td>api.EpMaintOtaFil es</td><td>查看或维护智慧中心上的OTA文件列表</td></tr><tr><td>EpMaintOtaTask</td><td>api. EpMaintOtaTas</td><td>查看或维护智慧中心上的OTA任务列表</td></tr><tr><td>EpMaintAgtRM</td><td>api.EpMaintAgtRM</td><td>备份恢复智慧中心的配置，包括子设备以及AI的 所有配置数据</td></tr><tr><td>EpConfigAgt</td><td>api.EpConfigAgt</td><td>设置智慧中心配置，如是否允许本地登录、修改</td></tr><tr><td>SceneGet</td><td>api.SceneGet</td><td>获取场景</td></tr><tr><td>Sceneset</td><td>api.Sceneset</td><td>触发场景</td></tr><tr><td>RegisterUser</td><td>auth.RegisterUser</td><td>注册新用戶</td></tr><tr><td>Unregisteruser</td><td>auth.Unregisterus er</td><td>移除用户的授权，注意：该接口不会删除用户， 只会回收授权。</td></tr></table>

params: 命令使用的参数

• ATTR_NAME：属性名称，详见《智慧设备属性定义》⚫ ATTR_VALUE：属性值，详见《智慧设备属性定义》

# 4.1.4.应答JSON格式

<table><tr><td>应答字段</td><td>描述</td></tr><tr><td>id</td><td>消息id号，与请求的消息id号相同</td></tr><tr><td>code</td><td>成功：0；错误：详见4.3错误码</td></tr><tr><td>message</td><td>如果code等于o即成功，则返回结果信息；否则返回错误文本信息</td></tr></table>

# 4.2.安全策略

为保障与云平台间的通讯安全，本协议要求所有通过 HTTPS 交互的请求必须携带请求源的签名信息，签名值作为 sign 存储在 HTTPS 请求的
system 参数集合中。

云平台首先会检查 HTTPS 请求中携带的 time 时间戳信息，如果与云平台系统时间差异大于 5
分钟，则视为无效的请求包，返回错误码。在时间戳检查正常的情况下，按照云平台统一的算法校验sign 签名值，只有当签名值一致时，才接收
HTTPS 请求。

为实现上述安全机制，智能应用必须为其管理的设备和应用申请对应的 appkey 及 apptoken，申请方法见 智能应用注册。

# 4.2.1.签名算法

完成签名算法，需要如下两个步骤：

1.收集签名原始串，“签名原始串” $=$ method $^ +$ params参数集合字串(
将所有字段按升序排列后，依次连接所有字段名及对应值 $^ { + + }$ system参数集合中的did字符串(如果有)
+time字串+userid+usertoken $^ +$ appkey $^ +$ apptoken，样式如下： -

"<attr>:<val>, ...,<attr>:<val>, did:<val>, time:<val>, userid:<val>,usert oken:<val>,appkey:<val>,apptoken:<val>"

2.将"签名原始串"进行MD5编码，并转化为32位的16进制小写字符串，作为sign签名值。

# Note:

● 智能应用接入到云平台前必须先到云平台进行注册，申请并获取该应用的appkey和apptoken。●
用户设备如果需要被智能应用管理时，需在该智能应用App上进行授权。智能应用拿到授权token后才能对智能设备进行控制操作。

# 4.2.2.签名范例

请求范例格式如下（JSON）：

"id": 123456,   
"system":   
{ "ver": "1.0", "lang":"en", "userid": "1111111", "did":"DID_xxxxxxxx", "time"：1445307713, "appkey":"APPKEY_xxxxxxxx"   
}，   
"method":"TestMethod",   
"params":   
{ "param1":"12345", "param2":"abcde"   
}

将 params 部分的param1，param2按升序排序，组成无空格字符串，并在字串前加method，最后拼接did、time、userid、usertoken、appkey、apptoken。最后组成的签名原始串如下：

"method:TestMethod, param1 :12345,param2:abcde, did:DID_xxxxxxxx, time:144 5307713,userid:1111i11,usertoken:
abcdefghijklmnopqrstuvwx, appkey:APPKE Y_xxxxxxxX, apptoken:ABCDEFGHIKJLMJOBPOOFPDFDA"

# 签名值即对上述签名原始串计算MD5值，即：

sign ${ \bf \Phi } _ { . } = { \bf \Phi } _ { . }$ MD5 ("method:TestMethod, param1 :12345, param2:abcde, did:
DID_xxxxxxxx , time:1445307713,userid:1111111,usertoken:abcdefghijklmnopqrstuvwx, app key:APPKEY_xxxxxxxX, apptoken:
ABCDEFGHIKJLMJOBPOOFPDFDA")

# 最终sign值为:

2602efca4b1924fb1a7e62b78f2285b2

# Note:

接口请求中经常遇到的错误返回"signerror'，一般原因如下:

• 仔细查看文档原始签名串的生成方式，留意params中参数的拼接字符是否正确；  
● 用户授权获取usertoken时是否传入了did参数，在接口请求时需要将该字段信息保持一致；  
• usertoken无效，即接口传入的usertoken错误或已失效，是否已经进行过令牌刷新操作等；

# 4.3.错误码

<table><tr><td>错误码</td><td>错误信息</td></tr><tr><td>0</td><td>成功 smart</td></tr><tr><td>10001</td><td>请求格式错误</td></tr><tr><td>10002</td><td>Appkey不存在</td></tr><tr><td>10003</td><td>不支持HTTP GET请求</td></tr><tr><td>10004</td><td>签名非法</td></tr><tr><td>10005</td><td>用户没有授权</td></tr><tr><td>10006</td><td>用户授权已经过期</td></tr><tr><td>10007</td><td>非法访问</td></tr><tr><td>10008</td><td>内部错误</td></tr><tr><td>10009</td><td>设置属性失败</td></tr><tr><td>10010</td><td>Method非法</td></tr><tr><td>10011</td><td>操作超时</td></tr><tr><td>10012</td><td>用户名已存在</td></tr><tr><td>10013</td><td>设备没准备好</td></tr><tr><td>10014</td><td>设备已经被其他账户注册</td></tr><tr><td>10015</td><td>权限不够</td></tr><tr><td>10016</td><td>设备不支持该操作</td></tr><tr><td>10017</td><td>数据非法</td></tr><tr><td>10018</td><td>GPS位置非法访问拒绝</td></tr><tr><td>10019</td><td>请求对象不存在</td></tr><tr><td>10020</td><td>设备已经存在账户中</td></tr><tr><td>10022</td><td>请求地址需要重定向</td></tr></table>

# 4.4.设备模型说明

为了方便阐述API，这里我们对LifeSmart的设备模型做个简要的说明，对一些术语作出说明。我们以EpGet/EpGetAll请求获取的数据为例：

"name":"smart Switch",   
"agt"："A3EAAABtAEwQxxxxxxxxxX",   
"me":"2d11",   
"devtype":"sL_Sw_IF3",   
"ful1Cls":"SL_SW_IF3_V2",   
"stat": 1,   
"data":{ "L1":{"type":129,"val":1,"name":"Living"}, "L2":{"type":128,"val":0,"name":"study"}, "L3":{"type":129，"val":1,"
name":"Kid"},   
"ver": "0.1.6.49",   
"1Dbm":-42,   
"lHeart"：1626229661

我们定义如下模型：

·智慧中心(Agt)： "A3EAAABtAEwQXXXXXXXXXX"  
·设备(EP): - $1 2 d 1 1 \prime$ ，它是个 S_SW_IF3 类型的三联开关  
•设备属性(rO口)
：设备的属性，可以用于读取状态，控制行为，1、2、L3它们都是设备的ⅠO口，当然对于只读的ɪO口例如温度传感器，则只能读取状态，不能控制。  
•管理对象(MO)： 泛指以上设备的总称，也可以包括AI对象，即MO可以是智慧中心，也可以是设备或者IO口，AI等。  
•智慧设备(SmartDevice)
：智慧设备是指可以独立工作的设备，例如传统的智慧中心，以及可以独立工作的wi-Fi类单品，例如摄像头，超级碗SPOr等。可独立工作的wi-Fi类单品通过EpSearchSmart，EpAddSmart命令又可以添加到智慧中心下面，这个时候智慧设备将会做为智慧中心下面的一个子设备(
Ep)使用，加入到智慧中心之后，智慧设备将可以与其它设备一起参与到智慧中心的AI配置中。

智慧设备本身都具有agt属性，但加入到智慧中心之后，其身份是做为一个子设备，其自身的agt属性将隐藏，可以通过Ep设备的属性：agt_self来获取其自身的agt属性。

智慧设备加入到智慧中心之后，调用EpGetAllAgts将不会返回。

我们汇总了设备属性定义，如下表：

<table><tr><td>名称</td><td>类型</td><td>描述</td></tr><tr><td>agt</td><td>string</td><td>智慧中心ID</td></tr></table>

<table><tr><td colspan="3"></td></tr><tr><td>名称</td><td>类型</td><td>描述</td></tr><tr><td>agt_ver</td><td>string</td><td>智慧中心版本号</td></tr><tr><td>tmzone</td><td>int32</td><td>智慧中心时区设置</td></tr><tr><td>me</td><td>string</td><td>设备ID(智慧中心下面唯一)</td></tr><tr><td>devtype</td><td>string</td><td>设备类型 (设备规格)</td></tr><tr><td>fullCls</td><td>string</td><td>包含版本号的完整的设备类型，一般它的值等于 devtype+V[n]，v[n]指明其版本号信息，一般情况下使 用devtype即可标识设备类型，在需要区分设备不同版本的 特性的时候才需要用到fullCls。如果设备类型没有版本信 息，则fullCls可能与devtype相同。</td></tr><tr><td>name</td><td>string</td><td>设备名称</td></tr><tr><td>stat</td><td>int32</td><td>设备在线状态， 0:Offline 1:online</td></tr><tr><td>data</td><td>collection /map</td><td>设备下的rO□集合，是一个Map字典集合，键为ɪO□的名称 (idx)，值为Io口的数据</td></tr><tr><td>data[IDx].type data[IDx].val</td><td>int32</td><td>特定IO口的值类型</td></tr><tr><td>data[IDx].v</td><td>int32 float32</td><td>特定IO口的值 特定IO口的友好值 友好值指的是用户容易理解的值。 例如温度：val返回的是235，其友好值v为23.5，指示</td></tr><tr><td>data [IDx] .name</td><td>注意： 明》文档。</td><td>当前温度为23.5摄氏度； ·也可以参考《LifeSmart 智慧设备规格属性说明》文 档，基于type、val值同样可以计算出实际友好值来。 ·调用EpSet系列接口控制设备的时候，仍然需要取val 值，例如设置空调的温度tr为26度，tr的val需设置为 260，具体请参考《LifeSmart 智慧设备规格属性说</td></tr><tr><td>lHeart int32 -</td><td>string 这个属性值)</td><td>特定IO口的名称(注意：如果IO口没有命名过，则不会返回 设备最近一次心跳时间，UTC时间戳，自1970年1月1日起</td></tr><tr><td>1Dbm</td><td>int32</td><td>计算的时间，单位为秒。 设备的dBm值，其值为负值，值越接近o表明信号质量越 好。注意该属性指的是射频类设备的信号强度，Wi-Fi类设</td></tr></table>

<table><tr><td>名称</td><td>类型</td><td>描述</td></tr><tr><td>agt_self</td><td>string</td><td>智慧设备本身的agt属性。如果一个智慧设备（例如摄像 头，超级碗SPOT）被加入到智慧中心下面做为一个设备使 用，则该智慧设备原先的agt属性将会被隐藏，为了显示这 个属性值，将以agtself属性提供。EpGetAll方法里面 将会返回这个属性值若存在的话。 或者一个设备A级联到其它智慧中心下面做为设备B使用，则 设备B将会有agt_self属性，其值指明设备a自己的agt属</td></tr><tr><td>me_self</td><td>string</td><td>性 智慧设备本身的me属性。如果一个智慧设备（例如摄像头， 超级碗SPOT）被加入到智慧中心下面做为一个设备使用， 则该智慧设备原先的me属性将会被隐藏，为了显示这个属性 值，将以me_self属性提供。EpGetAll方法里面将会返回 这个属性值若存在的话。</td></tr><tr><td>ext_loc</td><td>string</td><td>或者一个设备A级联到其它智慧中心下面做为设备B使用，则 设备B将会有meself属性，其值指明设备A原本的me属性 设备扩展属性，第三方应用可以使用该字段存储需要的扩展 属性。注意：该字段最大长度不能超过512字符，且必须为 字符串类型。 该字段为第三方应用专用，LifeSmart应用不需要使用该</td></tr><tr><td>ver</td><td>string</td><td>字段。 设备固件版本号</td></tr></table>

# 4.5.接口定义

# 4.5.1.EpAddAgt 增加智慧中心

# 4.5.1.1.JSON请求数据格式

![](images/84079aa1aa20eedbba2162e7e343a535858bde13b0926bb8910af9dfb6a03c42.jpg)

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpAddAgt</td><td></td><td>增加智慧中心</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpAddAgt</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8"></td><td>ver</td><td></td><td>1.0</td></tr><tr><td></td><td>lang</td><td>Y</td><td>en</td></tr><tr><td></td><td>sign</td><td></td><td>签名值</td></tr><tr><td></td><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>system did</td><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td></td><td></td><td></td><td>(可选)终端唯—id。如果在授 权时填入了，此处必须填入相 同id</td></tr><tr><td></td><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起 计算的时间，单位为秒</td></tr><tr><td colspan="2">method params sn</td><td>Y</td><td>EpAddAgt</td></tr><tr><td rowspan="2"></td><td>-</td><td>Y</td><td></td><td>通过发现协议获取的AGT字段 或智慧中心背部条码</td></tr><tr><td>name id (</td><td></td><td>Y</td><td>智慧中心名称</td></tr><tr><td colspan="2"></td><td>Y</td><td>消息id号</td><td></td></tr></table>

# 4.5.1.2.范例

# ⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

• 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpAddAgt

# • 请求信息：

"id":957,   
"method":"EpAddAgt",   
"params": { "sn":"xxxxxxxx", "name":"xxx"   
}，   
"system":  { "ver":"1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx" "time":1447641115, "sign":"
sIGN_xxxxxxxx"   
}

# 签名原始字符串：

method:EpAddAgt, name:xxx, sn:xxxxxxxx, time:1447641115, userid:1111111, usertoken:UsERToKEN_xxxxxxxx,appkey:
APPKEy_xxxxxxxx, apptoken:APPToKE N_XXXXXXXX

# • 回复信息：

"id": 957,   
"code": 0,   
"message":[ { "agt"："A3EAAABdADQQxxxxxxxxxxx" "name"："我的智慧中心" }

# 4.5.2.EpDeleteAgt 删除智慧中心

# 4.5.2.1.JSON请求数据格式

<table><tr><td colspan="3">Type</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpDeleteAgt</td><td></td><td>删除智慧中心</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpDeleteAgt</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">HTTP POST</td><td></td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey (可选)终端唯—id。如</td></tr><tr><td>time</td><td>Y</td><td>果在授权时填入了，此 处必须填入相同id UTC时间戳，自1970年1月</td></tr><tr><td></td><td></td><td>1日起计算的时间,单位 为秒</td></tr><tr><td>method agt</td><td>Y</td><td>EpDeleteAgt</td></tr><tr><td>params</td><td>Y</td><td>智慧中心</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.2.2.范例

• 我们假定:

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

• 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpDeleteAgt

# • 请求信息：

"id": 957,   
"method": "EpDeleteAgt", "params": { "agt"："A3EAAABdADQQxXxxxxxxxxx"   
}，   
"system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time": 1447641115, "sign":"
sIGN_xxxxxxxx" }

⚫ 签名原始字符串为：

method:EpDeleteAgt, agt:A3EAAABdADQQxxxxxxxxxxx, time:1447641115,useri d:1111111,usertoken:UsERToKEN_xxxxxxxx, appkey:
APPKEY_xxxxxxxx,apptok en:APPTOKEN XXXXXXXX

# • 回复信息：

![](images/64844d0ae081de9afd55be6e2734ef80d3e0180aa1a6cae16895ab0efbbbe792.jpg)

# 4.5.3.EpGetAllAgts 获取所有智慧中心

# 4.5.3.1.JSON请求数据格式

![](images/fae5aa1b3ea02dca631c26172cf971df7b232a5926b71bdf460c55d4f6058284.jpg)

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpGetAllAgts</td><td></td><td>获取所有智慧中心</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpGetAllAgts</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td></td><td>lang</td><td>Y</td><td>en</td></tr><tr><td></td><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td></td><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>system</td><td>appkey did</td><td>O</td><td>appkey</td></tr><tr><td></td><td></td><td></td><td>(可选)终端唯—id。如果在授 权时填入了，此处必须填入相 同id</td></tr><tr><td>time</td><td></td><td>Y</td><td>UTC时间戳，自1970年1月1日起 计算的时间,单位为秒</td></tr><tr><td colspan="2">method</td><td>Y</td><td>EpGetAllAgts</td></tr><tr><td>id</td><td colspan="2"></td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.3.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

⚫ 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpGetAllAgts

# • 请求信息：

{ "id":957, "method":"EpGetAllAgts", "system": { "ver":"i.0", "lang":"en", "userid": "1111111", "appkey":"
APPKEY_xxxxxxxx", "time": 1447641115, "sign":"sIGn_xxxxxxxx" }

⚫ 签名原始字符串为：

method:EpGetAllAgts, time:1447641115, userid:1111111,usertoken:UsERToK EN_xxxxxxxx,appkey:APpkEy_xxxxxxxx,apptoken:
APpToKEN_xxxxxxxx

# • 回复信息：

"id": 957,   
"code": 0,   
"message":[ { "agt"："A3EAAABdADQQxxxxxxxxxxx" "name"："我的智慧中心", "agt_ver": "1.0.33p1", "stat": 1, "tmzone":'8, }   
」

# 4.5.4.EpAdd 添加设备

# 4.5.4.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpAdd</td><td></td><td>添加射频设备</td></tr><tr><td>URL</td><td colspan="2">api.EpAdd</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td rowspan="7">system</td><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User id</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填 入了，此处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起 计算的 时间,单位为秒</td></tr><tr><td></td><td></td><td>EpAdd</td></tr><tr><td rowspan="2">params</td><td>agt</td><td>Y</td><td>智慧中心Id，为EpGetAllAgts返回 时信息</td></tr><tr><td>optarg</td><td>O</td><td>添加设备额外参数，这是一个可选 的、高级的选项。见后面描述。 数据类型是JSON对象的序列化字符 串。</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

说明：射频设备需要添加到智慧中心才能工作，射频设备添加的时候需要对码，使得待添加的设备与智慧中心都进入相应通道，识别匹配到对方才算完成。对码过程有个超时时间，时间定义缺省是20秒，因此需要把握好时间，使得字设备进入对码状态与调用EpAdd命令的时间间隔尽可能的短。

# 4.5.4.2.范例

•
我们假定：appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

请求地址：Svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpAdd

# ● 请求信息：

"id": 829,   
"method":'"EpAdd",   
"system": { "yer": "1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time":1447643442, "sign":"
sIGN_xxxxxxxx"   
}，   
"params": { "agt"："A3EAAABdADQQxxxxxxxxxx"   
}

⚫ 签名原始字符串为：

method:EpAdd, agt:A3EAAABdADQQxxxxxxxxxx, time:1447643442,userid:11111 11,usertoken:uSERToKEN_xxxxxxxx, appkey:
APPKEy_xxxxxxxx, apptoken:APPT OKEN_XXXXXXXX

• 回复信息： "id": 829, "code": 0, "message":{ "me":"271c"

说明：返回message.me属性指明新添加设备的me属性。

# 4.5.4.3.optarg 参数说明

optarg参数是添加设备的额外参数，一般情况下，不使用该参数已经可以很好的工作，但对于有些设备，为了实现灵活的定制，可以使用该参数。  
该参数与设备类型息息相关，不同的设备有不同的参数，如果设备没有额外参数，则将忽略该参数的值。当前可用的额外参数有如下： -

# 多功能(CUBE)环境感应器

optarg $=$ { "cls":"SL_SC_BE", "exarg":{ "humidity_display":1/2/3, "temperature_display":1/2/3 }   
11

humidity display属性用于确定多功能(CUBE)环境感应器液晶屏显示的内容，可以选择湿度、光照、湿度与光照，分别对应值1、2、3。

temperature_display 属性用于确定多功能(CuBE)环境感应器液晶屏对温度显示类别选择，可以选择摄氏温度、华氏温度、摄氏与华氏温度，分别对应值1、2、3。

# 多功能 (CUBE)动态感应器

optarg $=$ { "cls":"SL_SC_BM", "exarg":{ "warning_duration": [6-814] }

warning_duration 属性用于确定检测到移动后的警报持续时间（单位：秒），缺省为秒，可选范围有6-814秒。 -

# 耶鲁门锁模块

optarg $=$ { "cls":"SL_LK_YL", "exarg":{ "enable_remote_unlock":1/0 }

enable_remote_unlock 属性用于确定耶鲁门锁模块是否支持远程开门，可以选择支持、不支持，分别对应值1、0。

# 恆星/辰星/极星开关/开关伴侣系列

添加恒星/星/极星开关/开关伴侣系列必须指明设备规格，否则将不能正确的添加。

同时恒星/辰星/极星开关系列还可以设置工作模式，分别为：速度优先、电量优先。其配置如下：

optarg $=$ { "cls":"sL_MC_ND3_V2", "exarg":{ "mode_selection":"speed" }

cls指明其为极星三联开关；当前恒星/辰星/极星开关系列c1s定义如下：

SL_SW_ND1_V1/SL_SW_ND2_V1/SL_SW_ND3V1恒星/辰星开关1联/2联3联 0 SL MC ND1 V1/SLMC ND2 V1/SL MC ND3 V1恒星/辰星开关伴侣1联/2联/3联
● SL_SW_ND1_V2/SL_SW_ND2_V2/SL_SW_ND3_V2极星开关1联/2联3联 ● SL_MC_ND1_V2/SL_MC_ND2_V2/SL_MCND3_V2极星开关伴侣1联/2联/3联

mode_selection属性指明工作模式，可以选择"speed"、"power"，分别对应速度优先、电量优先，缺省模式为速度优先。 -

# 特殊指明设备

有些设备在对码的时候必须指明类型，以便API接口进行更好的添加操作，因此添加这些设备，请在optarg属性里面指明要添加的设备规格类型。

当前强制需要指明的设备规格有如下：

PSM：PSM系列SL_P_IR: SPOT (MINI)

我们以恒星开关为例，参数内容如下：

optarg $=$ {"cls":"SL_SW_ND1"  
1」

说明：其参数数据格式是JSOΝ对象的序列化字符串，并且要参与方法签名中。

# 4.5.5.EpRemove 删除设备

# 4.5.5.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpRemove</td><td></td><td>删除设备</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpRemove</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td rowspan="7">system</td><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>O</td><td>appkey (可选)终端唯—id。如果在</td></tr><tr><td></td><td></td><td>授权时填入了，此处必须填 入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日 起 计算的时间,单位为秒</td></tr><tr><td colspan="2">method</td><td>Y EpRemove</td></tr><tr><td rowspan="2">params</td><td>agt</td><td>Y</td><td>欲删除设备的agt， EpGetAll返回时信息</td></tr><tr><td rowspan="2">id</td><td rowspan="2">Y</td><td rowspan="2">Y</td><td rowspan="2">欲删除设备me， 为EpGetAll返回时信息</td></tr><tr><td>me</td></tr></table>

# 4.5.5.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

• 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpRemove

# ● 请求信息：

"id":46，   
"method':"EpRemove",   
"system":{ "ver":"i.0", "lang":"en", "userid":  "1111111", "appkey":"APPKEY_xxxxxxxx", "time":1447642457, "sign":"
SIGN_xxxxxxxx"   
}，   
"params":{ "agt"："A3EAAABdADQQxXxxxxxxXX", "me"："2832" }

# ⚫ 签名原始字符串：

method:EpRemove, agt:A3EAAABdADQQxxxxxxxxxX,me:2832, time:1447642457,u serid:1111111,usertoken:
UsERToKEN_xxxxxxxx,appkey:APPkEY_xxxxxxxx, ap ptoken:APPTOKEN_xxxxxxxX

• 回复信息： { "id": 46, "code": o, "message":"success"

# 4.5.6.EpGetAll 获取所有设备信息

# 4.5.6.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td colspan="2">Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpGetAll</td><td></td><td colspan="2">查询该账户下授权给appkey的所有设 备信息。设备信息不包括摄像头信息 (若没有摄像头权限)。</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpGetAll</td><td></td><td colspan="2"></td></tr><tr><td>Content Type</td><td colspan="3">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="3">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8">system</td><td rowspan="8">ver sign</td><td>Y</td><td>1.0</td><td colspan="2"></td></tr><tr><td>lang</td><td>V en</td><td colspan="2"></td></tr><tr><td></td><td>Y 签名值</td><td colspan="2"></td></tr><tr><td>userid appkey</td><td>Y Y</td><td colspan="2">User id</td></tr><tr><td>did</td><td>appkey O</td><td colspan="2">(可选)终端唯一id。如果在授权时</td></tr><tr><td></td><td></td><td colspan="2">填入了，此处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td colspan="2">UTC时间戳，自1970年1月1日起 计算的 时间,单位为秒</td></tr><tr><td colspan="2">method</td><td>Y</td><td colspan="2">EpGetAll</td></tr><tr><td colspan="2" rowspan="2">params id</td><td rowspan="2">degree</td><td rowspan="2">N</td><td rowspan="2">degree：查询返回的详细程度，若不 提供则缺省为2。 0：返回最基本的信息，包括 agt,me, devtype,name,stat</td><td rowspan="2">2：返回agt_ver,lDbm,lHeart</td></tr><tr><td>1：返回data数据 3：返回agt_self Y 消息id号</td></tr></table>

# 4.5.6.2.范例

•
我们假定：appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

• 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpGetAll

# ● 请求信息：

"id":144，   
"method":'"EpGetAl1",   
"system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"：1447396020, "sign":"
SIGN_xxxxxxxx"   
}

签名原始字符串：

method:EpGetAll, time:1447395539, userid:1111111, usertoken:UsERToKEN_x xxxxxxx,appkey:AppkEy_xxxxxxxx,apptoken:
AppTokEn_xxxxxxxx

# • 回复信息：

"id": 144,   
"code": 0,   
"message":[{ "agt"："A3EAAABdADQQxxxxxxxxxx", "me":"2711", "devtype": "sL_Sw_IF2", "name"："流光开关", "stat":1, "
data":{' "L1"：{"type"：129,"val"：1,"name"："客厅"}, "L2"：{"type"：128，"val"：0，"name"："餐厅"}， }， "iDbm"：-35, "lHeart"
：1539143970   
}, { "agt"："AEAAABdADQQxxxxxxxxxx",   
"me":"2713",   
"devtype":"sL_LI_RGBw",   
"name"："智慧灯泡"，   
"ext_loc":"{\"key\":\"Ls\"， \"location\":"HangZhou"}",   
"stat": 1,   
"data": { "RGBw"：{"type"：255,"val"：2147483648}， "DYN":{"type":254,"val": 0}   
}，   
"1Dbm":-46,   
"lHeart"：1539143970

提示：若存在ext_loc属性则将返回ext_loc属性值。

# 4.5.7.EpGet 获取指定设备信息

# 4.5.7.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="3">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="3">Epset</td><td></td><td colspan="2">控制设备</td></tr><tr><td>Partial URL</td><td colspan="3">api.Epset</td><td></td><td colspan="2"></td></tr><tr><td>Content Type</td><td colspan="3">application/json</td><td></td><td colspan="2"></td></tr><tr><td>HTTP Method</td><td colspan="3">POST</td><td></td><td colspan="2"></td></tr><tr><td rowspan="10"></td><td rowspan="10">system</td><td colspan="2">ver</td><td>Y</td><td colspan="2">1.</td></tr><tr><td colspan="2">lang</td><td>Y</td><td colspan="2">en</td></tr><tr><td colspan="2">sign</td><td>Y</td><td colspan="2">签名值</td></tr><tr><td colspan="2">userid</td><td>Y</td><td colspan="2">User id</td></tr><tr><td colspan="2">appkey did</td><td>Y</td><td colspan="2">appkey (可选)终端唯一id。如果在授权时填入</td></tr><tr><td colspan="2">time Y</td><td></td><td colspan="2">了，此处必须填入相同id UTC时间戳，自1970年1月1日起计算的时</td></tr><tr><td colspan="2">agt</td><td>Y Y</td><td colspan="2">间,单位为秒 EpGet</td></tr><tr><td colspan="2"></td><td>Y</td><td colspan="2">欲设置设备的agt，为EpGetAll返回时 信息 欲设置设备me，为EpGetAll返回时信息</td></tr><tr><td colspan="2">…</td><td>Y</td><td></td><td colspan="2">根据不同设备传入不同参数，具体请</td></tr><tr><td colspan="2">tag</td><td></td><td></td><td colspan="2">见&quot;智慧设备设置属性定义&quot;</td></tr><tr><td rowspan="3"></td><td colspan="2">nonvola tile</td><td>N</td><td colspan="2">控制设备的自定义标记串，可以不填写 是否需要掉电后数据不丢失的设置。等于</td></tr><tr><td colspan="2">ult</td><td>bandRes</td><td>支持这个功能。</td><td colspan="2">1表示需要。注意：仅有部分设备的属性 是否在命令执行完之后在回应 (Response)消息里面攜带Io口最新配 置。等于1表示需要。注意：可能存在部</td></tr><tr><td colspan="3">id</td><td></td><td>配置。 Y 消息id号</td><td colspan="2">分设备在执行完之后不支持返回IO口最新</td></tr></table>

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpGet</td><td></td><td>获取设备信息</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpGet</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8"></td><td>ver lang</td><td>Y</td><td>1.0</td></tr><tr><td></td><td>Y Y</td><td>en 签名值</td><td></td></tr><tr><td></td><td>sign</td><td></td><td></td></tr><tr><td></td><td>userid Y appkey</td><td></td><td>User id</td></tr><tr><td>system did</td><td>Y</td><td>appkey</td><td></td></tr><tr><td></td><td></td><td>填入了，此处必须填入相同id</td><td>(可选)终端唯一id。如果在授权时</td></tr><tr><td>time</td><td>Y</td><td></td><td>UTC时间戳，自1970年1月1日起计算的</td></tr><tr><td>method</td><td></td><td></td><td rowspan="2">时间,单位为秒</td></tr><tr><td rowspan="2">params</td><td rowspan="2">agt</td><td>Y</td><td rowspan="2">EpGet 欲查询设备的agt，为EpGetAll返回</td></tr><tr><td>me</td><td>时信息 Y</td></tr><tr><td colspan="3"></td><td>Y</td><td>欲查询设备me，为GetAll返回时信息</td></tr><tr><td colspan="3">Id</td><td></td><td colspan="2">消息id号</td></tr></table>

# 4.5.7.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpGet

• 请求信息：

"id":974,   
"method":'"EpGet",   
"system":{ "ver": "1.0", "lang': "en", "userid": "1111111", "appkey":"AppkEy_xxxxxxxx", "time": 1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params": { "agt":"A3EAAABdADQQxxxxxxxxxx", "me":"2711"   
}

签名原始字符串：

method:EpGet, agt:A3EAAABdADQQxxxxxxxxxX,me:2711, time:1447639497,user id:1111111,usertoken:UsERToKEN_xxxxxxxx, appkey:
APPKEY_xxxxxxxx, appto ken:APPTOKEN_XXXXXXXX

# • 回复信息：

"id":974,   
"code": 0,   
"message":[   
{ "agt"："A3EAAABdADQQxxxxxxxxxx", "me":"2711", "devtype":"SL_Sw_IF2", "name"："流光开关", "stat": 1, "data": {' "Ll"：{"
type"：129,"val"：1,"name"："客厅"}, "L2"：{"type"：128，"val"：0,"name"："餐厅"}, }1 "1Dbm"：-35， "lHeart"：1539143970

# 4.5.8.EpSet 控制设备

# 4.5.8.1.JSON请求数据格式

<table><tr><td rowspan="2">Type Interface Name</td><td colspan="2">Definition</td><td>Must</td><td colspan="2">Description</td></tr><tr><td colspan="2">Epset</td><td></td><td>控制设备</td></tr><tr><td>Partial URL</td><td colspan="2">api.Epset</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="12">system Request Content</td><td rowspan="7"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User id</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did 0</td><td></td><td>(可选)终端唯一id。如果在授权时填入 了，此处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时</td></tr><tr><td colspan="2">method</td><td>Y</td><td>间,单位为秒 EpGet</td></tr><tr><td colspan="2">params</td><td></td><td>设置设备的agt，为EpGetAll返回时</td></tr><tr><td rowspan="3"></td><td>D me</td><td>Y</td><td>欲设置设备me，为EpGetAll返回时信息</td></tr><tr><td></td><td>Y</td><td>根据不同设备传入不同参数，具体请 见&quot;智慧设备设置属性定义&quot;</td></tr><tr><td>bandRes</td><td>O</td><td>是否需要掉电后数据不丢失的设置。等于 1表示需要。注意：仅有部分设备的属性 支持这个功能。 是否在命令执行完之后在回应</td></tr><tr><td></td><td>ult</td><td></td><td>(Response)消息里面携带ro口最新配 置。等于1表示需要。注意：可能存在部 分设备在执行完之后不支持返回IO口最新 配置。</td></tr><tr><td>id</td><td colspan="2"></td><td>Y 消息id号</td><td></td></tr></table>

# 4.5.8.2.范例

•
我们假定：appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

⚫ 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.Epset

# ● 请求信息：

"id": 191,   
"method":' "Epset",   
"system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEy_xxxxxxxx", "time"：1447640772, "sign":"
SIGN_xxxxxxxx"   
}，   
"params":{ "agt"："A3EAAABdADQQRzMONjg5NA", "me"："2832"， "idx": "RGBW", "type": 128, "val"：0， "tag":"m"   
}

签名原始字符串：

method:EpSet, agt:A3EAAABdADQQRzMoNjg5NA,idx:RGBW,me:2832, tag:m, type: 128, val:0, time:1447640772, userid:1ii1111,
usertoken:UsERToKEN_xxxxxxx X,appkey:APPkEy_xxxxxxxx, apptoken:APPToKEN_xxxxxxxx

• 回复信息： "id": 191, "code": 0, "message":"success"

# 提示：如何修改设备、IO口、智慧中心的名称？

EpSet接口支持修改设备、Io口与智慧中心的名称。  
若需要修改设备名称，请指明{agt,me，name}属性；  
若需要修改设备IO口的名称，请指明 $\{ \mathsf { a g t } , \mathsf { m e } , \mathrm { i d } \mathbf { x } , \mathsf { n a m e } \}$
属性。  
若需要修改智慧中心的名称，请指明{agt, $\mathrm { m e } = \cdot$ NULL',name}属性。  
例如{agt="A3EAAABdADQQRzMONjg5NA" $\scriptstyle { m e =" 2 d 3 2 " }$ ,name $=$ "我的插座"说明要把设备2832命名为"
我的插座"；  
例如 $\{ a g t = " A 3 E . A A A B d A D Q Q R z M O N j g 5 N A " , m e = " 2 d 3 3 " , i d s < 1 \}$ ${ \underline { { i } } } d x { = } " L 1 ^ { \prime \prime }$
,name $=$ "客厅灯"说明要把2833这个三联开关的第一路开关命名为"客厅灯"；  
例如 {agt="
A3EAAABdADQQRzMONjg5NA", $\scriptstyle { \mathit { m e } } = { \boldsymbol { \prime } } { \boldsymbol { \prime } } _ { N U L L } , { \boldsymbol { \prime } } { \boldsymbol { \prime } }$
,name $=$ "我的智慧中心"说明要把智慧中心A3EAAABdADQQRzMONjg5NA命名为"我的智慧中心"； -

注意：不是所有的ɪO口命名都有意义，当前主要是多联开关类设备，例如三联流光开关灯有意义。注意：修改智慧中心的名称的时候，me属性必须填写为"
NUL′

提示：如何修改设备的ext_loc属性？

EpSet接口支持修改设备的extloc属性的值。  
若需要修改设备ext_loc值，请指明{agt,me,ext_loc}属性；  
例如{agt="A3EAAABdADQQRzMONjg5NA" $. m e = " 2 d 3 2 "$ 、 extloo $^ { 1 } =$ "{\"key\":/"Ls\",\"location\"："HangZhou"}"
}说明要把设备2832的ext_loc属性修改为"{\"key\":\"Ls\"，\"location\":"HangZhou"}";  
注意：ext_loc属性可以与name属性一起修改，同时指明它们的值即可。

# 4.5.9.EpsSet 控制多个设备

# 4.5.9.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">Epsset</td><td>控制多个设备</td><td></td></tr><tr><td>Partial URL</td><td colspan="3">api.Epsset</td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="3">POST</td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="6">system</td><td>g</td><td>YY</td><td></td></tr><tr><td>sign</td><td></td><td></td></tr><tr><td>userid</td><td>Y Y</td><td>签名值 User ID</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey</td></tr><tr><td>time Y</td><td></td><td>(可选)终端唯一id。如果在授权时填 入了，此处必须填入相同id</td></tr><tr><td></td><td></td><td>UTC时间戳，自1970年1月1日起 计算的 时间,单位为秒</td></tr><tr><td colspan="2">method args</td><td>Y Epsset Y</td><td>欲设置的执行列表，列表中每个内容</td></tr><tr><td rowspan="3">params</td><td></td><td>值给args</td><td>参照EpSet的params参数； 需要将列表转化成JSON格式字符串赋</td></tr><tr><td>nonvolat ile</td><td>O</td><td>是否需要掉电后数据不丢失的设置。 等于1表示需要。注意：仅有部分设备 的属性支持这个功能。</td></tr><tr><td>bandResu O lt</td><td></td><td>是否在命令执行完之后在回 应 (Response)消息里面攜带Io口最新 配置。等于1表示需要。注意：可能存 在部分设备在执行完之后不支持返回 IO口最新配置。</td></tr><tr><td></td><td colspan="2">id Y</td><td>消息id号</td></tr></table>

# 4.5.9.2.范例

# ⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

⚫ 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.Epsset

# • 请求信息：

"id": 191, "method":'"Epsset", "system":{ "ver": "1.0", "lang":"en", "userid": "1i11111", "appkey":"APPKEY_xxxxxxxx", "
time": 1447640772, "sign":"sIGN_xxxxxxxx" }1 "params": { "args":"{{\"val\":65535,\"tag\":\"m\"，\"agt\":\"-
EAAABuADoYRzUyOTc2Mg\"，\"me\":\"0011\"，\"idx\":\"RGBwT"，\"type\":255 },{\"val\":0,\"tag\":\"m\",\"agt\":\"_-
EAAABuADorRzUyOTc2Mg\",\"me\":\"00i1\",\"idx\":\"DYN\",\"type\":128} 」", } }

# 签名原始字符串：

method:Epsset, args:[{"val":65535,"tag":"m","agt":"_-   
EAAABuADoYRzUyOTc2Mg", "me":"0011", "idx":"RGBw","type":255},{"val":0, "tag":"m","agt":"   
EAAABuADoYRzuyOTc2Mg", "me":"0011","idx":"DYN", "type":128}],time:1447 640772,userid:11111i1,usertoken:
UsERToKEN_xxxxxxxx, appkey:APPKEY_xxx xxxxX,apptoken:APPTOKEN xxxxxxxX

# • 回复信息：

{ "id": 191, "code": 0, "message":"success"

# 4.5.10.SceneGet 获取场景

# 4.5.10.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">SceneGet</td><td></td><td>获取场景</td></tr><tr><td>Partial URL</td><td colspan="2">api.SceneGet</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="10">Request Content</td><td rowspan="6">system</td><td>ver</td><td>Y</td><td>0 1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey</td></tr><tr><td></td><td></td><td rowspan="2">(可选)终端唯一id。如果在授权时填入 了，此处必须填入相同id UTC时间戳，自1970年1月1日起计算的时</td></tr><tr><td>time</td><td>Y</td></tr><tr><td>method</td><td></td><td>Y</td><td>SceneGet</td></tr><tr><td>params</td><td>agt</td><td>Y</td><td>欲查询设备的agt</td></tr><tr><td>id</td><td></td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.10.2.范例

⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX, 实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX, 实际需要填写真实数据；

• 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.sceneGet

# • 请求信息：

"id": 974, "method":'"sceneGet", "system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"
APPkEY_xxxxxxxx", "time": 1447639497, "sign":"SIGN_xxxxxxxx" }， "params": { "agt":"AGT_xxxxxxxx", } 1

⚫ 签名原始字符串：

method:SceneGet, agt:AGT_xxxxxxxx, time:1447639497,userid:1111111, user token:usERToKEN_xxxxxxxx,appkey:APPkEY_xxxxxxxx,
apptoken:APPToKEN_xx XXXXXX

# • 回复信息：

"id": 974,   
"code": 0'   
"
message":[ { "id":"aaaaaaaa", "name":"testscene", "desc":"testscenessss" "cls":"scene", }1 { "id":"bbbbbbb", "name":"testscenel", "desc":"testscene2", "cls":"scene", }   
]

# 4.5.11.SceneSet 触发场景

# 4.5.11.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">Sceneset</td><td></td><td>触发场景</td></tr><tr><td>Partial URL</td><td colspan="2">api.sceneset</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="8"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td rowspan="7">system</td><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填 入了，此处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起 计算的 时间,单位为秒</td></tr><tr><td>method</td><td>Y -</td><td>Sceneset</td></tr><tr><td rowspan="4">params</td><td>agt</td><td>Y</td><td>欲查询设备的agt</td></tr><tr><td rowspan="3">id</td><td></td><td>Y</td><td>欲触发场景的id</td></tr><tr><td>type</td><td></td><td>场景需要设置的参数名字</td></tr><tr><td>RGBW</td><td>0</td><td>场景需要设置的参数名字</td></tr><tr><td colspan="3">id -</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.11.2.范例

⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

agt为AGT_XXXXXXXX，实际需要填写真实数据；

• 请求地址：Svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.sceneset

# • 请求信息：

"id": 974,   
"method":'"sceneset",   
"system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEy_xxxxxxxx", "time"：1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params":{ "agt"："AGT_xxxxxxxx", "id":"aaaaaaaa",   
}

签名原始字符串：

method:SceneGet, agt:AGT_xxxxxxxx, id:aaaaaaaa, time:1447639497, userid: 1111111,usertoken:usERTokEN_xxxxxxxx,appkey:
APPKEY_xxxxxxxx,apptoken :APPTOKEN_XXXXXXXX

• 回复信息： { "id": 974, "code": 0, "message":"success"

# 4.5.11.3.说明

场景的cls主要有如下几种，同时执行场景时需要传入相应的参数：

<table><tr><td>cls</td><td>name</td><td>args</td><td>value</td><td>value描述</td><td>desc</td></tr><tr><td>scene</td><td>情景模式</td><td>N/A</td><td>N/A</td><td>N/A$</td><td>-</td></tr><tr><td>groupsw</td><td>一键开关</td><td>args</td><td>type</td><td>0x81:打开 0×80:关闭</td><td>打开或者关闭一组开关/灯 泡</td></tr><tr><td rowspan="2">grouphw</td><td rowspan="2">极速彩灯组</td><td rowspan="2">args</td><td>type</td><td>0x81:打开 0x80:关闭 Oxff：设置颜色并开灯闭，响应速度更快</td><td rowspan="2">设置一组灯泡。此种模式 下以广播方式打开／关</td></tr><tr><td>RGBW</td><td>0xfe:设置颜色并关灯 4byte:WRGB</td></tr><tr><td rowspan="2">grouprgbw</td><td rowspan="2">彩灯组</td><td rowspan="2">args</td><td>type</td><td>0x81:打开 0x80:关闭 0xff:设置颜色并开灯</td><td rowspan="2">打开或者关闭一组开关/灯 泡。</td></tr><tr><td>RGBW</td><td>Oxfe:设置颜色并关灯 4byte:wRGB -</td></tr></table>

# 4.5.12.EpUpgradeAgt 升级智慧中心

# 4.5.12.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpUpgradeAgt</td><td></td><td>升级智慧中心</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpupgradeAgt</td><td></td><td></td></tr><tr><td>Content Type HTTP Method</td><td colspan="2">application/json POST</td><td></td><td></td></tr><tr><td rowspan="20">Request</td><td rowspan="8">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时间,单</td></tr><tr><td colspan="2">method</td><td>位为秒 Y EpupgradeAgt</td><td></td></tr><tr><td rowspan="6">Content</td><td>params agt</td><td>Y</td><td></td><td>欲操作的智慧中心ID</td></tr><tr><td></td><td>httpUrl</td><td>O</td><td>采用HTTP方式升级提供可供下载的固件文件的 URL，注意：固件文件名称必须以.tar·gz 结尾。</td></tr><tr><td></td><td>httpcert ificate</td><td></td><td>采用HTTP方式升级需要的安全摘要证书内容， 如果采用HTTP方式升级，则该证书必须提供。</td></tr><tr><td></td><td>reboot</td><td></td><td>注意：证书内容需要使用标准Base64编码。 是否在升级完成之后自动重启智慧中心 1表示需要，0表示不需要，缺省为1</td></tr><tr><td></td><td>nonResp</td><td></td><td>是否不需要等待智慧中心执行完成，立即返回 1表示需要，0表示不需要，缺省为1</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.12.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据； ■

请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpupgradeAgt

# • 请求信息：

"id": 974,   
"method":'"EpupgradeAgt",   
"system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"： 1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params":{ "agt"："AGT_xxxxxxxx", "reboot": "I",   
}

⚫ 签名原始字符串：

method:EpupgradeAgt, agt:AGT_xxxxxxxx, reboot:1, time:1447639497,userid :1111111, usertoken:UsERToKEN_xxxxxxxX,appkey:
APPKEY_xxxxxxxx, apptoke n:APPTOKEN_XXXXXXXX

• 回复信息： "id": 974, "code": 0, "message":"success"

# 注意：

由于升级操作是比较耗时的操作，跟网络原因也有关系，因此网络环境恶劣其时间可能会需要几分钟，因此该命令缺省(
nonResp $^ { 1 = 1 }$ )将不会等待设备升级完成才返回，而是立即返回。因此需要调用者间隔一段时间调用查询命令例如EpGetAlAgts去查询获取智慧中心的版本号，判断是否已经升级到最新版本。

如果nonResp $^ { * 1 }$ 并且reboot $\mathtt { \mathtt { . 0 } }$ ，则该命令将即返回，但又不会自动重启，因此将无法掌握智慧中心的升级状态，因此最好不要采用这种方式。

如果nonResp $\mathtt { \Pi } = 0$
则表示需要等待智慧中心升级结果，则reboot最好不要等于1，因为智慧中心升级完成之后自动重启，将可能导致回应包无法发送出去。并且在nonResp $\mathtt { \Pi } = 0$
的方式下，由于耗时较长，需要设置HTTP的请求等待时间为较长的时间，例如30OS，否则HTTP请求可能会提早返回超时。

因此，我们推荐的方式有：

nonResp=1, reboot=1：不关注升级结果，命令下下去后，立即返回，缺省式。

nonResp $\mathbf { \mu = 0 }$ , reboot=o:关注升级结果，升级完成之后，需手工调用EpRebootAgt执行重启命令，并且需要设置HTTP请求等待时间为较长的时间。

智慧中心的当前版本号请参考 EpGetAllAgts APl调用返回的智慧中心agt_ver 属性。

# 4.5.13.EpRebootAgt 重启智慧中心

# 4.5.13.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpRebootAgt</td><td></td><td>重启智慧中心</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpRebootAgt</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>0 1.0</td></tr><tr><td>lang sign</td><td>Y</td><td>en</td></tr><tr><td></td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>0</td><td>appkey (可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time</td><td>Y</td><td>处必须填入相同id UTC时间戳，自1970年1月1日起计算的时间,单</td></tr><tr><td></td><td></td><td>位为秒</td></tr><tr><td>method agt</td><td>Y</td><td>EpRebootAgt</td></tr><tr><td>params id</td><td>Y</td><td>欲操作的智慧中心ID</td></tr><tr><td colspan="2">-</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.13.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

• 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpRebootAgt

# • 请求信息：

"id": 974,   
"method":"EpRebootAgt",   
"system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"：1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params": { "agt"："AGT_xxxxxxxX"   
}

⚫ 签名原始字符串：

method:EpRebootAgt, agt:AGT_xxxxxxxx, time:1447639497,userid:1111111,u sertoken:UsERToKEN_xxxxxxxX,appkey:
APPKEr_xxxxxxxx, apptoken:APPToKEN XXXXXXXX

• 回复信息： "id":974, "code": 0, "message":"success"

注意：智慧中心升级之后会自动重启，因此执行EpUpgradeAgt操作，不需要再次调用重启智慧中心操作。

# 4.5.14.EpGetAgtLatestVersion 获取智慧中心最新版本

# 4.5.14.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpGetAgtLatestVe rsion</td><td></td><td>获取智慧中心最新版本</td></tr><tr><td>Partial URI</td><td colspan="2">api.EpGetAgtLate stVersion</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>0 1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>Y 0</td><td>appkey (可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time</td><td>Y</td><td>处必须填入相同id</td></tr><tr><td></td><td></td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td>method</td><td>Y</td><td>EpGetAgtLatestVersion</td></tr><tr><td>params agt</td><td></td><td>欲查询的智慧中心ID</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.14.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

⚫ 请求地址：svrurl+PartialURL，例如：

# • 请求信息：

"id": 974,   
"method":'"EpGetAgtLatestVersion",   
"system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"AppkEy_xxxxxxxx", "time"：1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params": { "agt"："AGT_xxxxxxxx"   
}

# ⚫ 签名原始字符串：

method:EpGetAgtLatestVersion, agt:AGT_xxxxxxxX, time:1447639497,userid :1111111,usertoken:UsERToKEN_xxxxxxxX,appkey:
APPKEY_xxxxxxxX, apptoke n:APPTOKEN XXXXXXXX

• 回复信息： { "id": 974, "code": 0, "message":{ "newestVersion":"NEwEST_VERSION", "stableVersion":"STABLE_VERSION", }

# 返回参数说明：

\*newestVersion当前最新版本。当前发布的最新版本，不强制用户升级，用户自由选择，可以选择升级，也可以选择忽略，一般体验最新的功能或小的Bug修复会更新最新版本。\*
stableVersion当前稳定版本。若当前智慧中心版本号低于稳定版本，则必须提醒用户升级智慧中心版本号，一般有大的功能更新或大的Bug修复将会更新稳定版本。

智慧中心的当前版本号请参考EpGetAllAgts APl调用返回的智慧中心 agt_ver属性。

# 4.5.15.EpSearchSmart 获取智慧中心搜索到的附近智慧设备

# 4.5.15.1.JSON请求数据格式

<table><tr><td colspan="3">Type Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">Epsearchsmart</td><td></td><td>获取智慧中心搜索到的附近其它智慧设备 当需要把其它wi-Fi类智慧设备，例如摄像 头、超级碗加入到智慧中心下面，需要先执行 这个接口，再调用EpAddsmart接口把搜索到 的wi-Fi智慧设备添加到智慧中心下面。</td></tr><tr><td>Partial URL</td><td colspan="2">api.Epsearchsmar t</td><td></td><td></td></tr><tr><td>Content Type HTTP Method</td><td colspan="2">application/json POST</td><td></td><td></td></tr><tr><td></td><td colspan="2"></td><td>Y</td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver lang</td><td>1.0 Y en</td><td></td></tr><tr><td>sign</td><td></td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td>0</td><td>(可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time</td><td>Y</td><td>处必须填入相同id UTC时间戳，自1970年1月1日起计算的时间,单</td></tr><tr><td>method</td><td>Y</td><td>位为秒 EpSearchsmart</td></tr><tr><td>agt -</td><td>Y</td><td>欲查询的智慧中心ID</td></tr><tr><td>mode</td><td>Y</td><td>查询模式，可以填写：&quot;notexist&quot;/&quot;auto&quot; notexist表示仅返回搜索到的还未添加到智 慧中心下面的附近智慧设备；</td></tr><tr><td>id</td><td></td><td>Y</td><td>auto表示返回所有搜索到的附近智慧设备； 消息id号</td></tr></table>

# 4.5.15.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

• 请求地址： -svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.Epsearchsmart

# • 请求信息：

{ "id": 974, "method":"EpSearchsmart", "system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"
APPKEY_xxxxxxxx" "time"：1447639497, "sign":"SIGN_xxxxxxxx" }， "params":{ "agt"："AGT_xxxxxxxx", "mode":"notexist" }

签名原始字符串：

method:EpSearchsmart,agt:AGT_xxxxxxxx,mode:notexist, time:1447639497, userid:1111111,usertoken:UsERToKEN_xxxxxxxX,
appkey:APPKEY_xxxxxxxx,a Pptoken:APPTOKEN_xxxxxxxX

# • 回复信息：

{ "id": 974, "code": 0, "message":[{ "lsid":"_wQBANxPIiTZEAAAAAAAAA", "name":"spoT", "ip": "192.168.1.56", "ttl": 1, "
sn": "dc:4f:22:24:d9:10" }1 { "1sid"："A9cAAEJDMzQwMDJGQTMzOA", "name":"camera", "ip": "192.168.1.224", "ttl": 1 }

# 返回参数说明：

\*lsid 被搜索到的智慧设备的uuID;  
$\star$ name 被搜索到的智慧设置的名称；  
\* ttl 搜索过程的TTL条数，可用户诊断网络；  
\* sn 被搜索到的智慧设置的MAC地址，并非所有的都会返回；

![](images/46f07bdfd1fddaaabcbb2229a646c636de299e07fa17f0046fd3c9cdbdf6e1be.jpg)

# 4.5.16.EpAddSmart 把搜索到的附近智慧设备添加到智慧中心

# 4.5.16.1.JSON请求数据格式

<table><tr><td></td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Type Interface Name</td><td colspan="2">EpAddsmart</td><td></td><td>把搜索到的附近智慧设备添加到智慧中心，需 要先执行EpSearchSmart操作获取搜索到的 附近智慧设备列表，才能执行添加操作。具体</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpAddsmart</td><td></td><td>请参考EpSearchsmart接口说明。</td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td></td><td colspan="2">ver</td><td>Y</td><td>1.0</td></tr><tr><td rowspan="12">Request Content</td><td rowspan="6">system</td><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td>0</td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时间,单 位为秒</td></tr><tr><td colspan="2">method</td><td>Y</td><td>EpAddsmart</td></tr><tr><td colspan="2">agt 1sid ■</td><td>Y</td><td>智慧中心ID</td></tr><tr><td colspan="2">params</td><td>Y</td><td>欲添加的智慧设备的LifeSmartUuID，从 EpSearchSmart接口返回的智慧设备信息中 获取。</td></tr><tr><td colspan="2">ip name</td><td>Y</td><td>欲添加的智慧设备的IP，从EpSearchSmart 接口返回的智慧设备信息中获取。</td></tr><tr><td colspan="2"></td><td>Y</td><td>欲添加的智慧设备的名称，可以自行命名，并 非一定要等于EpSearchSmart接口返回智慧 设备的名称。</td></tr><tr><td colspan="3">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.16.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据； ■

• 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpAddsmart

# • 请求信息：

"id": 974,   
"method":"EpAddsmart",   
"system":{ "ver":"i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"：1447639497, "sign":"
SIGN_xxxxxxxx"   
}，   
"params":{ "agt":"AGT_xxxxxxxx", "lsid"："A9IAAEJDMzQwMDJGMUY3QQ", "ip": "192.168.1.145", "name":"CameraByOpenApi",   
}

签名原始字符串：

method:EpAddsmart, agt:AGT_xxxxxxxx,ip:192.168.1.145, lsid:A9IAAEJDMzQ wMDJGMuY3QQ,name:CameraByōpenApi, time:
1447639497,userid:1111111, user token:UsERToKEN_xxxxxxxx, appkey:APPKEY_xxxxxxxx, apptoken:APPToKEN_xx XXXXXX

• 回复信息： "id": 974, "code": 0, "message":"2d3a"

# 返回参数说明：

若执行成功，message属性标识新添加的智慧设备在智慧中心下的"
me”属性值。若该设备已经存在与智慧中心下面，即已经被添加过，则message仍将返回该设备在智慧中心下的"me”属性值。

# 4.5.17.EpGetAgtState 获取智慧中心状态

# 4.5.17.1.JSON请求数据格式

![](images/965a61c7dee720f70444d00081e83f0b15d069db26700209f4a0914f04d58e8a.jpg)

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpGetAgtState</td><td></td><td>获取智慧中心状态</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpGetAgtState</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey (可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time</td><td>Y</td><td>处必须填入相同id</td></tr><tr><td></td><td></td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td>method</td><td>Y</td><td>EpGetAgtState</td></tr><tr><td>params agt</td><td>Y</td><td>智慧设备ID</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.17.2.范例

# • 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

# 请求地址：

svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpGetAgtstate

# ● 请求信息：

"id": 974,   
"method":'"EpGetAgtState",   
"system": { "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time": 1447639497, "sign":"
sIGn_xxxxxxxx"   
}，   
"params":{ "agt":"AGT_xxxxxxxx"   
}

# 签名原始字符串：

method:EpGetAgtState, agt:AGT_xxxxxxxx, time:1447639497, userid:1111111 ,usertoken:UsERToKEN_xxxxxxxX, appkey:
APPKEy_xxxxxxxx,apptoken:APPTOK EN_XXXXXXXX

# • 回复信息：

"id":974,   
"code": 0'   
"message":{ "state": 2, "agt_ver":' "1.0.68p8", "name"："智慧中心mINIv2"   
}

# 返回参数说明：

智慧设备指拥有独立工作能力的设备，例如智慧中心，MINI智慧中心，以及Wi-Fi类独立工作设备，例如超级碗SPOT，摄像头等。 -

智慧设备有三种状态，其值描述如下：

•0：离线(offline);  
•1：正在初始化(initializing)；  
•2：工作正常(normal)；

正在初始化一般发生在添加智慧设置的过程中，智慧设备已经被添加到账号中，但还没有完成初始化。

# 4.5.18.EpCmd 控制设备(高级命令)

# 4.5.18.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpCmd</td><td></td><td>控制设备(高级命令)</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpCmd</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td></td><td rowspan="5">lang</td><td>ver</td><td>Y Y</td><td>0 1.0</td></tr><tr><td></td><td></td><td>en 签名值 -</td><td></td></tr><tr><td></td><td>sign</td><td>Y Y</td><td></td></tr><tr><td>userid system</td><td></td><td>User</td><td>TD</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey</td><td>(可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td rowspan="8">Request Content</td><td rowspan="3"></td><td></td><td>0</td><td>处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td colspan="2">method</td><td>Y</td><td>EpCmd</td></tr><tr><td rowspan="5">params ■</td><td>agt</td><td>Y</td><td>智慧中心ID</td></tr><tr><td>me</td><td>Y</td><td>设备ID</td></tr><tr><td>cmd</td><td>Y</td><td>命令</td></tr><tr><td>cmdargs</td><td></td><td>命令参数，为JSON格式对象的序列化字符串</td></tr><tr><td>-</td><td>Y</td><td></td></tr><tr><td colspan="2">id</td><td></td><td>消息id号</td></tr></table>

# 4.5.18.2.范例

# • 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据：

sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

• 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.Epcmd

# • 请求信息：

"id":974, "method":"Epcmd", "system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"ApPKEY_xxxxxxxx", "
time": 1447639497, "sign":"sIGN_xxxxxxxx" }， "params": { "agt":"AGT_xxxxxxxx", "me":"2e97", "cmd":"audio", "cmdargs":"
{\'adcmd\":\"play\"，\"id\":5， \"opt\":{\"vol\": 95, \"loop\":2,\"clear\":true}}" } }

# 签名原始字符串：

method:Epcmd, agt:AGT_xxxxxxxx,cmd:audio,cmdargs:{"adcmd": "play", "id":5, "opt":{"voi": 95, "loop": 2, "clear":
true}},me:2e97, time:1447639497,userid:1111111,usertoken:UsERTOKEN_xX xxxxxX,appkey:APPKEY_xxxxxxxX,apptoken:
APPToKEN_xxxxxxxx

• 回复信息： "id": 974, "code": 0, "message":"success"

EpSet命令一般用于控制设备的属性，属性可以是一个或者多个，但缺乏灵活，对于一些复杂的或者特殊的指令可以使用EpCmd，它一般用于复合指令，作用于一个设备，并且设备端还可以对某些指令进行特殊处理，因此功能要比EpSet命令强大。当前EpCmd指令有：

• 报警器播放语音指令;  
• 云视·户外摄像头声光警报;

具体的指令如下：

<table><tr><td>指令Directive</td><td>设备</td><td>Description</td></tr><tr><td>cmd:&quot;audio&quot;, cmdargs: { adcmd:play&quot;, id:5, opt:{ vol: 95, loop: 2, clear: True, led: True, mute: False cmd:&quot;audio&quot;, cmdargs:{ adcmd: &quot;stop&quot;,</td><td>智慧中心 (MINI)设备 云视·户外摄 像头</td><td>用于控制智慧中心(MINI)设备的报警音播放。 cmd参数请务必填写&quot;audio&quot;; cmdargs参数是JOsN对象的序列化字符串。 其内容如下: •adcmd指明动作类型，有如下值： &quot;play&quot;：开启声音播放 &quot;stop&quot;：停止声音播放 若为停止声音播放，则不需要其它参数。 •id指明播放的声音序号，当前一共有7个声音 序号，其值取值为：[1，7]。 •opt是操作选项，对于play动作类型来说, 有如下属性： vol：指明播放的音量，其取值范围为： [50，100]，值越大声音越响。 loop：指明播放的次数。 clear：指明是否清除正在播放的声音, 开启本次新的声音播放，若值为false则原先正在 播放的声音会与新的声音一起播放。 led：是否开启户外摄像头LED闪烁警 报。 mute：是否静音，一般与led一起使用, 若想只开启LED闪烁而没有声音警报，则可以设置 该参数为rrue。 注：led与mute参数是云视·户外摄像头才有的属</td></tr></table>

# 4.5.19.EpSetVar 控制设备(低级命令)

# 4.5.19.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpSetvar</td><td></td><td>控制设备(低级命令)</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpsetVar</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="11">Request Content</td><td rowspan="8">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User 1D</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td>time</td><td></td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td>method</td><td>Y</td><td>EpSetVar</td></tr><tr><td rowspan="5">params -</td><td>agt</td><td>Y</td><td>智慧中心ID</td></tr><tr><td>me</td><td>Y</td><td>设备ID</td></tr><tr><td>$idx</td><td>Y</td><td>索引号Number类型</td></tr><tr><td>cmd</td><td>Y</td><td>命令号 Number类型</td></tr><tr><td>cmddata</td><td>Y</td><td>命令数据，为JSON数组的序列化字符串， JSON数组成员值为Byte类型</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.19.2.范例

• 我们假定：appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；

apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

# • 请求地址：

svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.Epsetvar

# • 请求信息：

"id": 974,   
"method":'"EpSetvar",   
"system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"：1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params":{ "agt"："AGT_xxxxxxxx", "me":"2e97", "idx": 129, "cmd":0， "cmddata'："[0，0，0]"   
}

# 签名原始字符串：

method:Epsetvar, agt:AGT_xxxxxxxx,cmd:0, cmddata:[0, 0, 01,idx:129,me:2e97,time:1447639497, userid:11111i1,usertoken:
UsERToKE N_xxxxxxxx, appkey:APpKEy_xxxxxxxx,apptoken:AppTokEn_xxxxxxxx

# • 回复信息：

{ "id": 974, "code": 0, "message":"success"

EpSetVar命令是低级命令，可以对设备完成一些比较低级别的设置，请严格参考文档描述的指令进行设置，否则设置将不会成功。

当前EpSetVar指令有：

<table><tr><td>指令Directive</td><td>设备</td><td>Description</td></tr><tr><td>idx: 129, cmd：0, cmddata：[0，0，0] 一</td><td>计量插座</td><td>用于清除计量插座的累计用电量。 注意：清零之后直接去查询累计电量仍然存在， 不会马上生效，需要等待下一次变化上报周期到 来才会生效，一般需要等待几分钟。</td></tr></table>

注：

指令Directive只列举idx、cmd、cmddata数据值，agt、me参数请填写具体设备的智慧中心Id与设备Id。

# 4.5.20.EpGetAttrs 获取设备扩展属性

# 4.5.20.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td colspan="2">Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpGetAttrs</td><td></td><td>获取设备扩展属性</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpGetAttrs</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>0 1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User</td></tr><tr><td>appkey did</td><td>Y 0</td><td>appkey (可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time -</td><td></td><td>处必须填入相同id</td></tr><tr><td></td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td>method</td><td>Y Y</td><td>EpGetAttrs</td></tr><tr><td rowspan="2">params</td><td>agt</td><td></td><td>智慧中心ID</td></tr><tr><td>me</td><td>Y</td><td>设备ID</td></tr><tr><td>id</td><td>attrNames</td><td>Y</td><td>属性名称数组，为JSON数组的序列化字符串</td></tr><tr><td colspan="2"></td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.20.2.范例

# ⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

# • 请求地址：

svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpGetAttrs

# • 请求信息：

"id": 974,   
"method":'"EpGetAttrs",   
"system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"： 1447639497, "sign":"
SIGN_xxxxxxxx"   
}，   
"params": { "agt"："AGT_xxxxxxxx", "me"："2e97, "attrNames":"[\"PairCfg\"]"   
}

# ⚫ 签名原始字符串：

method:EpGetAttrs, agt:AGT_xxxxxxxX, attrNames:["PairCfg"],me:2e97, tim e:1447639497,userid:11111i1,usertoken:
UsERToKEN_xxxxxxxx, appkey:APPK EY_xxxxxxxx,apptoken:APPToKEn_xxxxxxxx

# • 回复信息：

"id": 974, "code"… 0, "message":{ "Paircfg":{ "warning_duration": 62 } } 1

该接口可以获取一些设备的扩展属性，当前支持的扩展属性有：

•PairCfg：射频设备对码配置在调用EpAdd接口添加对码设备的时候，可以设置设备扩展属性，例如动态感应器的告警持续时长。这个接□可以用于获取设备添加时设置的相应值。

提示：当前仅支持 CUBE动态感应器(SL_SC_BM)、CUBE环境感应器(SL_SC_BE)、恆星/辰星/极星 获取PairCfg值。具体请参考 添加设备(
EpAdd) 接口 optarg 参数介绍 部分。

# 4.5.21.EpTestRssi 测试射频设备信号强度

# 4.5.21.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpTestRssi</td><td></td><td>测试射频设备信息强度</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpTestRssi</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td></td><td rowspan="5">lang</td><td>ver</td><td>Y Y</td><td>1.0</td></tr><tr><td></td><td></td><td>en 签名值</td><td></td></tr><tr><td></td><td>sign</td><td>Y Y</td><td></td></tr><tr><td>userid system</td><td>Y</td><td>User</td><td>TD</td></tr><tr><td>appkey did</td><td>0</td><td>appkey</td><td>(可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td rowspan="7">Request Content</td><td>time</td><td></td><td></td><td>处必须填入相同id</td></tr><tr><td></td><td></td><td></td><td>UTC时间戳，自1970年1月1日起计算的时间,单 位为秒</td></tr><tr><td rowspan="4">method</td><td>agt</td><td>Y Y</td><td>EpTestRssi 智慧中心ID</td></tr><tr><td>me params</td><td>N</td><td>设备ID，如果设备ID为空，则表示测试智慧中</td></tr><tr><td>args</td><td>N</td><td>心的射频信号强度</td></tr><tr><td></td><td></td><td>扩展属性，为JSON对象的序列化字符串，当前 不需要填写</td></tr><tr><td>id</td><td></td><td>Y</td><td>消息id号</td></tr></table>

该接口获取测试射频设备的信号强度，它仅仅用于现场环境的调试与维护，并非正常使用场景下的接口。

# 4.5.21.2.范例

# • 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据； ■

• 请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpTestRssi

# • 请求信息：

"id": 974,   
"method": "EpTestRssi",   
"system":{ "ver":"i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time":1447639497, "sign":"
sIGN_xxxxxxxx"   
}，   
"params":{ "agt"："AGT_xxxxxxxx", "me"："2e97"   
}

# 签名原始字符串：

method:EpTestRssi, agt:AGT_xxxxxxxx,me:2e97, time:1447639497,userid:11 11111,usertoken:usERToKEN_xxxxxxxx,appkey:
APPKEY_xxxxxxxx, apptoken:A PPTOKEN_XXXXXXXX

# • 回复信息：

"id": 974,   
"code": 0,   
"message":{ "dbm"：{ "back_noise_threshold": -99, "back_noise": -114, "recv": -19, "send": -30 }， "rssi": { "
back_noise_threshold": 70, "back_noise": 40, "recv": 231,

"send": 208 } }

⚫ 返回数据说明：dbm即是分贝毫瓦。其值为负数，越接近-o则表明信号越好。

•dbm.recv:接收方向的射频信号强度，智慧中心 $= = >$ 设备  
•dbm.send:发送方向的射频信号强度，设备 $= = >$ 智慧中心  
•dbm.back_noise：背景噪音，其值越小(越远离-o)则说明背景噪音越小  
·dbm.back_noise_threshold:背噪门限，当back_noise的值大于背噪门限，说明现场环境恶劣，已经影响射频设备正常的通信。

rssi即是接收信号强度指示，其值为正数，越大则表明信号越好。

•rssi.recv:接收向的射频信号强度，智慧中心 $= = >$ 设备  
•rssi.send:发送方向的射频信号强度，设备 $= = >$ 智慧中心  
•rssi.back_noise：背景噪音，其值越小则说明背景噪音越小  
·rssi.back_noise_threshold:背噪门限，当back_noise的值大于背噪门限，说明现场环境恶劣，已经影响射频设备正常的通信。

提示：当执行测试智慧中心信号强度，也即me属性为空的时候，返回的属性为{back_noise"，"back_noise_threshold","
signal}signal属性指明智慧中心当前的射频信号强度。其值越大说明智慧中心射频信号越好。

提示：是否所有的射频设备都支持检测？

只有支持命令下发的射频设备，例如开关、插座才支持射频信号检测，对于主动上报事件的射频设备，例如温湿度感应器、动态感应器等，由于没有命令下发接口，因此不能执行射频信号检测。查看它们的射频信息可以使用EpGetAll/EpGet命令返回的IHeart、IDbm属性。EpGetAll/EpGet命令返回的IDbm数组指示设备侧的dbm.send属性，即设备发送方向的射频信号强度。 - -

# 4.5.22.EpBatchSet 批量快速设置多个设备属性

# 4.5.22.1.JSON请求数据格式

该接口是一个批量操作接口，用于快速设置多个设备的属性。例如一次开启或关闭多个开关/插座/灯光等场景模式的操作。

该接口会在内部进行优化处理，减少设备处理命令的时间，保证让用户拥有良好的体验。并且该接口支持三种不同速度等级的操作，分别应用于不同的场景需求。

<table><tr><td colspan="4">Type Definition</td><td>Mus t</td><td colspan="3">Description</td></tr><tr><td>Interface</td><td colspan="3">EpBatchset</td><td></td><td colspan="2">批量快速设置同一个智慧中心下的设备属性</td></tr><tr><td>Name Partial URL</td><td colspan="3">api.EpBatchset</td><td></td><td colspan="2"></td></tr><tr><td>Content Type HTTP Method</td><td colspan="3">application/json POST</td><td></td><td colspan="2"></td></tr><tr><td rowspan="10">Request Content</td><td rowspan="10">system</td><td colspan="2">ver</td><td>Y</td><td colspan="2">1.0</td></tr><tr><td colspan="2">lang</td><td>Y</td><td colspan="2">en</td></tr><tr><td colspan="2">sign Y</td><td></td><td colspan="2">签名值</td></tr><tr><td colspan="2">userid</td><td>Y</td><td colspan="2">User ID</td></tr><tr><td colspan="2">appkey</td><td>Y appkey</td><td colspan="2"></td></tr><tr><td colspan="2">did</td><td></td><td colspan="2">(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td colspan="2">time</td><td>Y</td><td colspan="2">UTC时间戳，自1970年1月1日起计算的时间,单 位为秒</td></tr><tr><td colspan="2">method agt</td><td>Y</td><td colspan="2">EpBatchSet</td></tr><tr><td colspan="2"></td><td></td><td>Y</td><td colspan="2">智慧中心ID ⅠO属性集合，为JSON数组的序列化字符串。 每条IO属性如下：</td></tr><tr><td rowspan="8"></td><td rowspan="6">params</td><td>ioItems</td><td>Y</td><td colspan="2">{ &quot;me&quot;：&quot;2711&quot;，：标识是哪个设备</td></tr><tr><td></td><td></td><td colspan="2">&quot;idx&quot;：&quot;L1&quot;，：标识设备的Io属性 &quot;type&quot;：0x81，：设置的属性类型 &quot;val&quot;：1：设置的属性值</td></tr><tr><td>speed</td><td>N</td><td colspan="2">速度等级，当前支持三种，分别为： ·o：正常(normal) ·1：快速(fast)</td></tr><tr><td></td><td></td><td colspan="2">·2：极速(extreme) 缺省为0。</td></tr><tr><td></td><td></td><td colspan="2"></td></tr><tr><td>retry</td><td>N</td><td colspan="2">详见后面描述。 重试次数，缺省为2。 在速度为normal、fast方式下才有效。 在由于射频通道拥塞命令执行超时再次尝试的 次数，取值范围为[0，5]。该属性为高级属 性，请谨慎使用。</td></tr></table>

<table><tr><td rowspan="3"></td><td>at</td><td>checkIost N</td><td>是否检查ΙO状态，等于1表示检查ΙO状态。 在速度为normal、fast方式下才有效。 下发命令执行时是否先检查子设备已有的属性 值，若属性值与下发值相等则忽略命令。该属 性为高级属性，请谨慎使用。</td></tr><tr><td>uid</td><td>N</td><td>该次命令的唯一识别码。该参数的作用是用于 标识操作，如果短时间内下发两条相同uid属 性的操作，则第二条操作指令将直接返回EIGN</td></tr><tr><td colspan="2">id</td><td>Y</td><td>错误。这样可以防频繁下发重复指令。 消息id号</td></tr></table>

# 4.5.22.2.范例

# • 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据;  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

# • 请求地址：

svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpBatchset

# • 请求信息：

"id": 974, "method":"EpBatchset", "system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"
APpkEy_xxxxxxxx", "time": 1447639497, "sign":"sIGN_xxxxxxxx" }， "params": { "agt":"AGT_xxxxxxxx", "ioItems":"{{\"me\":
\"2f14\"，\"idx\":\"L2\"，\"type\":129， \"val\":1}，{\"me\": \"2f14\"，\"idx\":\"L1\"， \"type\":129, \"val\":1}，{\"me\":
\"2f14\"，\"idx\":\"L3\"，\"type\":129, \"val\"：1}，{\"me\"：\"2f13\"，\"idx\"：\"L1\"，\"type\"：129,
\"val\"：1}，{\"me\"：\"2f0f\"，\"idx\"：\"L2\"，\"type\"：129, \"val\":1}，{\"me\":\"2f0f\"，\"idx\":\"L1\"，\"type\":129,
\"val\":1}，{\"me\":\"2f0f\"，\"idx\":\"L3\"，\"type\":129,

\"val\"：1}，{\"me\": \"2f50\"， \"idx\":\"L2\"， \"type\"：129,   
\"val\":1}，{\"me\":\"2f50\"，\"idx\":\"L1\"，\"type\":129,   
\"val\":1}，{\"me\":\"2f10\"，\"idx\":\"L2\",\"type\":129,   
\"val\":1}，{\"me\":\"2f10\"，\"idx\":\"L1\"，\"type\":129，   
\"val\":1}，{\"me\":\"2f72\",\"idx\":\"L1\",\"type\":129,   
\"val\":1}，{\"me\":\"2f71\"，\"idx\":\"L2\",\"type\":129,   
\"val\":1}，{\"me\":\"2f71\",\"idx\":\"Li1\",\"type\":129，   
\"va1\":1}，{\"me\":\"8141\"，\"idx\":\"L\"，'\"type\":129，'   
\"val\": 1}]", "speed": 1, "uid":"TEST" }

# ⚫ 签名原始字符串：

method:EpBatchset, agt:AGT_xxxxxxxx,ioItems:[{"me": "2f14", "idx": "L2", "type":129, "val":1}, {"me":"2f14", "idx": "
L1", "type": 129, "val":1}, {"me":"2f14", "idx":"L3", "type":129, "val":1}, {"me":"2f13",'"idx":"L1", "type":129, wval":
1}, {"me":"20f", "type": 129, "val": 1}, {"me":"2f0f", widx":"L3", "type": 129, "val": 1}, {"me": "2f50", "idx": "L2", "
type": 129, wval": 1}, {"me":"2f50","idx":"L1"，"type":129,"val":1}，{"me":"2f10", "idx": "L2", "type": 129, "val":1}, {"
me": "2f10w, widxw: "L1", "type":129,"val":1},{"me":"2f72","idx":"Li","type":129, "val": 1), {"me": "2f71", widx":
wI2w, "type": 129, "val": 1), {"me":"2f71", "idx":"Li", "type":129,"val":1}, {"me":"8141", "idx":"L", "type":129, "val":
1}l, speed:1,uid:TEsT, time:1550748304, userid:1111111, usertoken:UsERTi KEn_xxxxxxxx,appkey:APPKEY_xxxxxxxx, apptoken:
APPToKEN_xxxxxxxx

# • 回复信息：

"id": 974,   
"code": 0,   
"message":{ "failedIoitems":[ { "me":"2f0f", "idx": "L1", "val": 1, "type": 129, "ret": 10013, "retMsg":"ENR" }， { "
me":"2f0f", "idx":"L3", "type": 129, "val": 1, "ret": 10013, "retMsg":"ENR" } 」   
}1

# 返回属性说明：

message.failedIoItems属性指明了执行失败的Items列表，若所有的item都执行成功，则该属性为空。若当前speed处于极速(extreme)
模式，则将不会返回failedIoItems属性。

# 4.5.22.3.speed参数说明

<table><tr><td>参数值</td><td>参数描述</td></tr><tr><td></td><td>0 正常(normal) 为缺省方式。 按照正常方式执行命令，所有命令操作串行执行，并且需要等待上一条命令的反 馈结果之后再继续执行下一条命令。 由于需要等待每一条命令的反馈结果，因此子设备得到执行的时间也会变长，并 且用户感官体验上设备执行时间也长。 特点：【用户体验慢，接口执行时间长，保证准确性】 -</td></tr><tr><td>1</td><td>快速(fast) 先对子设备执行一遍不需要等待反馈结果快速下发，然后再执行一遍需要等待反 馈结果的正常下发。 第一遍保证大部分子设备快速得到执行机会，用户感官体验上会很快， 第二遍保证第一次快速执行过程中失败的命令再次得到执行，确保执行结果的准 确性。 由于执行了两次下发，整体命令执行总耗时最长，但第一遍快速下发很好的保证 了用户体验。</td></tr><tr><td>2</td><td>特点：【用户体验快，接口执行时间最长，保证准确性】 极速(extreme) 直接对子设备执行一遍不需要等待反馈结果的快速下发。 由于仅仅对子设备执行一遍快速下发，因此执行时间将最短。 但在子设备列表比较多的情况下，存在部分子设备执行失败的可能性。但该方式 仍然会保证大部分子设备执行是成功的，并且接口调用耗时最短。 特点：【用户体验快，接口执行时间短，不保证准确性】</td></tr></table>

# 4.5.23.EpSearchIDev 获取智慧中心搜索到的附近IP网络设备

# 4.5.23.1.JSON请求数据格式

<table><tr><td colspan="3">Type Definition EpSearchIDev</td><td>Must</td><td>Description</td></tr><tr><td colspan="3">Interface Name</td><td></td><td>获取智慧中心搜索到的附近其它IP网络设备 当需要把其它wi-Fi类网络设备，例如IP摄像 头加入到智慧中心下面，需要先执行这个接 □，再调用EpAddIDev接口把搜索到的wi-Fi 网络设备添加到智慧中心下面。</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpSearchIDev</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="9">Request</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign Y</td><td></td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey Y</td><td>。</td><td>appkey</td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td></td><td>Y</td><td>位时间戳，自1970年1月1日起 计算的时间,单</td></tr><tr><td>method</td><td>Y Y</td><td>EpSearchIDev</td></tr><tr><td>agt mode ■ params</td><td>Y</td><td>欲查询的智慧中心ID 查询模式，可以填写：&quot;notexist&quot;/&quot;auto&quot;</td></tr><tr><td colspan="2">id</td><td>Y</td><td>慧中心下面的附近网络设备； auto表示返回所有搜索到的附近网络设备； 消息id号</td></tr></table>

# 4.5.23.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

• 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpsearchIDev

# • 请求信息：

{ "id": 974, "method":"EpSearchIDev", "system":{ "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"
APPKEY_xxxxxxxx" "time"：1447639497, "sign":"sIGN_xxxxxxxx" }， "params":{ "agt"："AGT_xxxxxxxx", "mode":"notexist" }

签名原始字符串：

method:EpSearchIDev,agt:AGT_xxxxxxxx,mode:notexist,time:1447639497,u serid:1111111,usertoken:UsERToKEN_xxxxxxxx, appkey:
APPkEY_xxxxxxxx, ap ptoken:APPTOKEN_xxxxxxxX

# • 回复信息：

"id": 974, "code": 0, "message": [{ "uuid":"4d756c74-694d-xxxx-xxxx-xxxxxxxxxxxx", "devid":"
4d756c74-694d-xxxx-xxxx-xxxxxxxxxxxx", "devType":"icontrol:iCamera2", "name":"iCamera2", "host": "192.168.1.222", "
port": 443, "ttl": 0, "auth":"Basic", "defuser":"administrator", "defPwd":"", "
exinfo":"<?xml version $\equiv$ \"1.0\" encoding $=$ \"UTF8\" ?><DeviceInfo version $\displaystyle . =$
\"1.0\"><deviceName>iCamera2F97A2A</ deviceName><deviceID>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</ deviceID><manufacturer>
iControl</manufacturer><model>iCamera2</ model><serialNumber>1612AXN000294</

serialNumber><macAddress>b4:a5:ef:f9:7a:2a</   
macAddress><firmwareVersion>3.0.01.40</   
firmwareVersion><firmwareReleasedDate>Jul 21,2016</   
firmwareReleasedDate><bootVersion>l.l1</   
bootVersion><bootReleasedDate>Jul 21,2016</   
bootReleasedDate><rescueVersion>3.0.01.40</   
rescueVersion><hardwareVersion>l</hardwareVersion><apiVersion>3.3</   
apiVersion></DeviceInfo>", "dhcp":true   
1

# 返回参数说明：

\* uuid 搜索到的网络设备的uuID;  
\* devType搜索到的网络设备的类型；  
$\star$ name搜索到的网络设备的名称；  
\* host搜索到的网络设备的Host地址；  
\* port搜索到的网络设备的主机端口号；  
\* tt1搜索过程的TTL条数，可用户诊断网络；  
\* defUser搜索到的网络设备的缺省登录账号；  
$\star$ defPwd搜索到的网络设备的缺省登录账号密码；  
\*exinfo搜索到的网络设备的扩展信息； -

# 注意：

1.并非所有的设备都会包含exinfo信息，这个与设备类型相关；  
2．若智慧中心刚刚启动或者IΡ设备刚刚加入本地网络中，智慧中心可能还未及时获取到设备的扩展信息，这个时候若获取不到exinfo信息，需要等待片刻再次调用该接口获取搜索信息；3．对于iCamera
设备，若设备的密码已经变更，不再是初始密码，由于没有权限，我们将获取不到设备的扩展信息，这个时候exinfo将为错误信息；  
4．为了保持兼容性，接口并不解析exinfo内容，当前exinfo包含的是查询获取的完整信息，需要使用者自行从中解析出需要关注的信息；  
5．对于不支持扩展信息的设备，exinfo可能为空或者是长度为o的字符串；

# 4.5.24.EpAddIDev 把搜索到的附近IP网络设备添加到智慧中心

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpAddIDev</td><td></td><td>把搜索到的附近IP网络设备添加到智慧中心， 需要先执行EpSearchIDev操作获取搜索到的 附近网络设备列表，才能执行添加操作。具体</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpAddIDev</td><td></td><td>请参考EpSearchIDev接口说明。</td></tr><tr><td>Content Type</td><td colspan="2">application/json POST</td><td></td><td></td></tr><tr><td rowspan="12">HTTP Method Request Content</td><td rowspan="6">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey Y</td><td>appkey</td><td></td></tr><tr><td colspan="2">did</td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td>method</td><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时间,单 位为秒</td></tr><tr><td></td><td>agt</td><td>Y Y</td><td>EpAddIDev</td></tr><tr><td rowspan="8">-</td><td rowspan="8"></td><td></td><td></td><td>智慧中心ID</td></tr><tr><td>uuid</td><td>Y</td><td>欲添加的网络设备的uuID，从EpSearchIDev 接口返回的网络设备信息中获取。</td></tr><tr><td></td><td>Y</td><td>欲添加的网络设备的设备类型，从EpSearch IDev接口返回的网络设备信息中获取。</td></tr><tr><td></td><td>Y</td><td>欲添加的网络设备的Host，从EpSearchIDev</td></tr><tr><td></td><td>Y</td><td>接口返回的络设备信息中获取。 欲添加的网络设备的Port，从EpSearchIDev</td></tr><tr><td>name</td><td>Y</td><td>接口返回的网络设备信息中获取。 欲添加的网络设备的名称，可以自行命名，并</td></tr><tr><td></td><td></td><td>非一定要等于EpSearchIDev接口返回网络设</td></tr><tr><td></td><td></td><td>备的名称。</td></tr></table>

<table><tr><td rowspan="2"></td><td rowspan="2">params</td><td>user O</td><td>号，则可以不填写。</td><td>欲添加的网络设备的登录账号，若用户修改了 登录账号，则这里必须填写修改的登录账号， 否则智慧中心将不能正确连接网络设备。若用 户没有修改登录账号则根据EpSearchIDev接 □返回的信息，填写缺省登录账号 (defUser)，若搜索接口没有返回缺省登录账</td></tr><tr><td>pwd</td><td>O</td><td>欲添加的网络设备的登录密码，若用户修改了 登录密码，则这里必须填写修改的登录密码， 否则智慧中心将不能正确连接网络设备。若用 户没有修改登录密码则根据EpSearchIDev接 口返回的信息，填写缺省登录密码 (defPwd)，若搜索接口没有返回缺省登录密</td></tr><tr><td>id</td><td colspan="2"></td><td>Y</td><td>码，则可以不填写。 消息id号</td></tr></table>

# 4.5.24.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/api.EpAddIDev

# ● 请求信息：

"id": 974,   
"method":"EpAddIDev",   
"system":{ "ver": "1.0", "lang":"en", "userid": "1111111", "appkey": "APPKEY_xxxxxxxx", "time": 1447639497, "sign":"
sIGN_xxxxxxxx"   
}1   
"params":{ "agt"："AGT_xxxxxxxx", "uuid":"4d756c74-694d-xxxx-xxxx-xxxxxxxxxxxx", "devType":"iControl:iCamera2",

"host": "192.168.1.222", "port": 443, "name":"iCamera2BB", "user":"administrator", "pwd":"" }

签名原始字符串：

method:EpAddIDev, agt:AGT_xxxxxxxx, devType:iControl:iCamera2,host:192 .168.1.222,name:icamera2BB,port:443,pwd:,user:
administrator,uuid:4d7 56c74-694d-xxxx-xxxxxxxxxxxxxxxx,time:1447639497,userid:1111111,usertoken:UsERTOKEN_xxxx
xxxX,appkey:APPKEY_xxxxxxxX, apptoken:APPTOKEN_xxxxxxxx

• 回复信息： "id": 974, "code": 0, "message":"2d3a"

# 返回参数说明：

若执行成功，message属性标识新添加的智慧设备在智慧中心下的"
me”属性值。若该设备已经存在与智慧中心下面，即已经被添加过，则message仍将返回该设备在智慧中心下的"me”属性值。

# 4.5.25.EpMaintOtaFiles 查看或维护智慧中心上的OTA文件列表

# 4.5.25.1.JSON请求数据格式

<table><tr><td>Type</td><td>Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td>EpMaintOtaFiles</td><td></td><td>查看或维护智慧中心上可供子设备升级固件版 本使用的OTA文件列表</td></tr><tr><td>Partial URL</td><td>api.EpMaintOtaFi les</td><td></td><td></td></tr><tr><td>Content Type</td><td>application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td>POST</td><td></td><td></td></tr><tr><td rowspan="20"></td><td rowspan="8"></td><td>ver Y</td><td>1.0</td><td></td></tr><tr><td>lang Y</td><td>en</td><td></td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey -</td><td>Y appkey</td><td></td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td></td><td></td><td></td></tr><tr><td>method agt</td><td>Y Y</td><td>EpMaintOtaFiles 智慧中心ID</td></tr><tr><td rowspan="8"></td><td></td><td>Y</td><td>操作指令，类型为字符串，当前可以为如下： ·AddByUrl：告知URL地址，下载oTA文件到</td></tr><tr><td>act ■ -</td><td></td><td>智慧中心；</td></tr><tr><td></td><td></td><td>•AddByBin：直接提供oTA文件的原始数据给 智慧中心； •Query：查询oTA文件信息 •Remove：删除oTA文件 •QueryAvailableEps：查询可以使用该</td></tr></table>

<table><tr><td>Request Content</td><td>params</td><td>actargs</td><td>O</td><td>操作指令参数，数据为JSON对象的序列化字符 串。操作指令参数与操作指令一—对应，定义 如下： •AddByurl：{key，url}，url参数指明可 被下载的oTA文件的地址，url必须为HTTP 或HTTPS协议；key为可选参数，若不提供 key则key为url提供的下载地址中的文件名 称，请谨慎使用key参数，key参数的命名必 须正确，否则升级将可能失败，若无必要， 无需设置key参数，使用缺省名称即可。 •AddByBin: {keY, cont}，key指明该 OTA文件的标识，不同于AddByUrl，这里 key必须提供，不能为空，cont指明oTA文 件内容，为便在JsON中传输，Cont为原始</td></tr><tr><td colspan="4"></td><td>OTA文件的标准Base64编码； •Query：actargs可以不用提供; •Remove：{keys}，keys指明需要移除的 OTa文件，若keys=true则表明删除该智慧 中心下所有的oTA文件，若keys=[&quot;key1&quot;， &quot;key2&quot;]则表示批量删除数组指明的oTA文 件集，若keys=&quot;keyl&quot;则表示删除特定的 OTA文件; • QueryAvailableEps: {keys}, keys指 明需要查询的OTA文件列表，其值为字符串数 组，指明需要查询的OTA文件列表，若不指明 keys则表示查该询智慧中心下所有的oTA文 件。 消息id号</td></tr></table>

# 4.5.25.2.范例

⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpMaintOtaFiles

# • 请求信息：

"id": 974, "method":'"EpMaintOtaFiles", "system":{ "ver":"i.0", "lang":"en", "userid": "1111111", "appkey":"
APPKEY_xxxxxxxx", "time": 1447639497, "sign":"sIGN_xxxxxxxx" }， "params": { "agt"："AGT_xxxxxxxx", "act":"AddByUrl", "
actargs":"{\"url\": \"http://www.ilifesmart.com/upgrade/test/ FL01_03040d10_00000631.ota\"}" } }

# 签名原始字符串：

method:EpMaintOtaFiles,act:AddByurl, actargs:{"url": "http://   
www.ilifesmart.com/upgrade/test/   
FL01_03040d10_0000063i.ota"},agt:AGT_xxxxxxxx,time:1447639497,userid   
:111i111,usertoken:UsERToKEN_xxxxxxxX, appkey:APPKEY_xxxxxxxX, apptoke   
n:APPTOKEN_XXXXXXXX

回复信息： Y "id": 974, "code": 0, "message":"success"

# 提示：

若是查询命令，则返回的OTA文件列表如下所示：  
{ -"code": 0,"message":{"MAXFILELEN"：1048576，指明单个OTA文件允许的最大大小，单位byte"MAXSTORESIZE"
：5242880，指明整个磁盘空间的最大容量，单位byte"files":{"key"："FL01_zG10370104_00000002.ota"，// 标识该oTA文件"size"
：165868//指明该oTA文件的大小}1 ...]  
}

# 提示：

若是QueryAvailableEps命令，则返回的oTa文件列表如下所示：   
{ "code": 0, "message":{ "FL0103580000
00000605.ota"：[/／标识该oTA文件 { "me":"a0db", "ver": "0.1.6.5", "devtype":"sL_LI_ww", "fullCls":"sLLIww V3", "name":"Dimming LEDDriver", "otaVer"："6.5"，//该ora文件版本号 "epVer"："6.4"，//该子设备当前版本号 "supportOta"：true，//该子设备是否支持ora升级 "needota"：true，//该子设备是否需要升级orA "lsid":"AlgAACfu0f7_hDwA w", "rfic":3 } ],

# 4.5.26.EpMaintOtaTasks 查看或维护智慧中心上的OTA任务列表

# 4.5.26.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpMaintOtaTasks</td><td></td><td>查看或维护智慧中心上当前子设备正在执行 OTA升级的任务列表</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpMaintOtaTa sks</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td>Request</td><td rowspan="5">lang</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td></td><td>Y</td><td>en</td><td></td></tr><tr><td>sign</td><td></td><td>Y 签名值</td><td></td></tr><tr><td>userid system</td><td>Y</td><td>User ID</td><td></td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td><td></td></tr><tr><td rowspan="2"></td><td>did</td><td></td><td>处必须填入相同id</td><td>(可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time</td><td>Y</td><td>位为秒</td><td>UTC时间戳，自1970年1月1日起计算的时间，单</td></tr><tr><td>method</td><td colspan="2">agt</td><td>Y</td><td>EpMaintOtaTasks</td></tr><tr><td rowspan="2">-</td><td>act</td><td></td><td>Y Y</td><td>智慧中心ID 操作指令，类型为字符串，当前可以为如下：</td></tr><tr><td></td><td></td><td>·Query：查询oTA任务信息 •Remove：删除已经完成的oTA任务 •Add：新建oTA升级任务</td><td></td></tr></table>

<table><tr><td rowspan="2">Content</td><td rowspan="2">params</td><td rowspan="2">actargs</td><td rowspan="2">O</td><td>操作指令参数，数据为JSON对象的序列化字符 串。操作指令参数与操作指令一一对应，定义 如下： •Query：actargs可以不用提供; •Remove： {key}，key指明需要移除的oTA 任务，若key=true则表明删除该智慧中心下 所有的已经完成的OTA任务，若</td></tr><tr><td>key=[&quot;key1&quot;, &quot;key2&quot;]则表示批量删除 数组指明的已经完成的OTA任务集，若 key=&quot;keyl&quot;则表示删除特定的已经完成的 OTA任务；注意：只能删除已经升级完成的 OTA任务。 •Add：{me，key}，me指明需要升级的子设 备，key指明升级的orA文件。注意：子设备</td></tr><tr><td colspan="2">id</td><td>Y</td><td>可以调用ＥｐMaｉnｔＯｔaＦｉles接口的 QueryAvailableEps指令查询oTa文件支 持的子设备列表。</td></tr></table>

# 4.5.26.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

请求地址：svrurl+PartialURL，例如:

https://api.ilifesmart.com/app/api.EpMaintotaTasks

# • 请求信息：

"id": 974,   
"method":'"EpMaintOtaTasks",   
"system": { "ver": "i.0", "lang":"en", "userid": "1111111",

"appkey": "APPKEy_xxxxxxxx", "time":1447639497, "sign":"sIGN_xxxxxxxx" }， "params": { "agt":"AGT_xxxxxxxx", "act":"
Query" }

⚫ 签名原始字符串：

method:EpMaintotaTasks, act:Query,agt:AGT_xxxxxxxx,time:1447639497,us erid:1111111,usertoken:USERTokEN_xxxxxxxx,appkey:
APPKEY_xxxxxxxx, apP token:APPTOKEN_xxxxxXxX

# • 回复信息：

"id": 974,   
"code": 0,   
"message":{ "ZGB752"：{ "id"："ZGB752", "cur":14158, "size"：165566, "file"："FL01_zG10370104_00000002.ota", "tover"："
\uoōoo\uo000\uōo00\u0002", "sts"：1577443530, "ts"：1577444053 }1.

⚫ 返回数据说明：

id：指示子设备的ld，若为ZigBee设备的ld，其值等于"ZG" $^ +$ zg_nodeid的十六进制表示，若为CoSS子设备，其值为CoSS设备的me属性，它既是Remove参数的key;

cur：指示当前OTA升级任务的进度，若cur等于size则指明升级已经完成；

size：当前OTA文件的总大小;

file：当前OTA文件的文件名；

tover：当前OTA文件的固件版本号；

sts：当前升级任务的开始时间，为UTC时间，单位为秒；

ts：当前升级任务最近一次反馈的时间，为UTC时间，单位为秒；

# 4.5.27.EpMaintAgtRM 备份或恢复智慧中心上的配置

# 4.5.27.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpMaintAgtRM</td><td></td><td>备份或恢复智慧中心的配置，包括子设备以及</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpMaintAgtRM</td><td></td><td>AI所有的配置数据</td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="12"></td><td colspan="2">ver</td><td>Y</td><td>1.0</td></tr><tr><td rowspan="7">system</td><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td></td><td>(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id</td></tr><tr><td>time</td><td></td><td>UTC时间戳，自1970年1月1日起计算的时间，单 位为秒</td></tr><tr><td>method</td><td>Y</td><td>EpMaintAgtRM</td></tr><tr><td rowspan="2"></td><td>agt</td><td>Y</td><td>智慧中心ID</td></tr><tr><td>act</td><td>Y</td><td>操作指令，类型为字符串，当前可以为如下： •backup：备份智慧中心的配置 •restore：恢复智慧中心的配置</td></tr></table>

<table><tr><td>Request Content</td><td>params</td><td>actargs Y</td><td>操作指令参数，数据为JSON对象的序列化字符 串。操作指令参数与操作指令一一对应，定义 如下： •backup：{nids，pwd}，nids参数指明 可。pwd参数指明加密密码，下次执行恢复 码； • restore: {cont, pwd,</td></tr><tr><td>id</td><td>V</td><td>消息id号</td><td>必须提供相同的密码。neednids指明用于 仅恢复部分数据，指明仅需要恢复的模块数 据，一般不需要提供该属性。 -</td></tr></table>

# 4.5.27.2.范例 - Backup

⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

# ⚫ 请求地址：

Svrurl+PartialURL，例如： https://api.ilifesmart.com/app/api.EpMaintAgtRM

# ● 请求信息：

"id":974,   
"method":'"EpMaintAgtRm",   
"system":{ "lang':"en",

"userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time":1447639497, "sign":"SIGN_xxxxxxxx" }， "params":{ "agt"："
AGT_xxxxxxxx", "act":"backup", "actargs":"{\"pwd\":\"ls000o\"}" }

签名原始字符串：

method:EpMaintAgtRM, act:backup,actargs:{"pwd": "ls0000"},agt:AGT_xxxxxxxx, time:1447639497, userid:1111111,usertoken:
UsERToKEN_xxxxxxxx,appkey:APPKEY_xxxxxxxx,apptoken:APPToKEN_xxxxxxxx

# • 回复信息：

"id": 974,   
"code": 0,   
"message":"Q2NfTiRxQB5PLjxfxzlVQ10xLjhPeioiIiA9SBJDUG1......"

返回数据说明：message：即为返回的备份的原始数据，该数据经过加密，不可读取。

# 注意：

备份操作是直接从智慧中心上获取数据的，所以智慧中心必须要在线，若智慧中心不在线则将无法完成备份操作。

# 4.5.27.3.范例 - Restore

# ● 请求信息：

"id": 974,   
"method":"EpMaintAgtRM",   
"system": { "ver": "1.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time"： 1447639497, "sign":"
sIGN_xxxxxxxx"

"params": { "agt":"AGT_xxxxxxxx", "act": "restore", "actargs":"{\"cont\":
\"Q2NfTiRxQB5PLjxfxzlVQ10xLjhPeioiIiA9SBJDUG1......\"，\"pwd\": \"1s0000\"}" } }

签名原始字符串：

method:EpMaintAgtRM, act:restore, actargs:{"cont": "Q2NfTiRxQB5PLjxfXz1VQ10xLjhPeioiIiA9SBJDUG1......","pwd": "1s0000"},
agt:AGT_xxxxxxxx, time:1447639497, userid:1111111, usertoken: UsERToKEN_xxxxxxxX,appkey:APPKEY_xxxxxxxX,apptoken:
APPToKEN_xxxxxxxx

# • 回复信息：

"id": 974,   
"code": 0,   
"message":{ "rets": { "cfg/rf3":true, "cfg/rf6": true, "me':true, "zigbee":true, "cfg/rf5":true }   
}

返回数据说明：message：rets对象指明模块恢复的结果。

注意：执行恢复数据成功之后请务必调用api.EpRebootAgt接口重启智慧中心才能生效。

# 4.5.28.EpMaintCartFiles 查看或维护智慧中心上的Cart文件列表

# 4.5.28.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpMaintCartFiles</td><td></td><td>查看或维护智慧中心上的cart文件列表</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpMaintCartF iles</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td></td><td rowspan="5">lang</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>system</td><td>Y Y</td><td>en</td></tr><tr><td>sign</td><td></td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>Y O</td><td rowspan="2">appkey (可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td colspan="3">time</td></tr><tr><td>method</td><td></td><td>Y</td><td colspan="2">UTC时间戳，自1970年1月1日起计算的时间，单 位为秒 EpMaintCartFiles</td></tr><tr><td rowspan="2"></td><td>agt act</td><td>Y</td><td colspan="2">智慧中心ID</td></tr><tr><td>-</td><td colspan="2">Y</td><td>操作指令，类型为字符串，当前可以为如下： ・AddByUrl：告知uRL地址，下载Cart文件 到智慧中心； ・AddByBin：直接提供Cart文件的原始数据</td></tr><tr><td colspan="2"></td><td colspan="2"></td><td>给智慧中心； •Query：查询cart文件信息 •Remove：删除Cart文件</td></tr></table>

<table><tr><td>Request Content id</td><td>params</td><td>actargs -</td><td>O 操作指令参数，数据为JSON对象的序列化字符 串。操作指令参数与操作指令一一对应，定义 如下： •AddByurl：{key，url}，url参数指明可 •AddByBin: {keY, •Query：actargs可以不用提供; •Remove：{keys}，keys指明需要移除的 Y 消息id号</td></tr></table>

# 4.5.28.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

⚫ 请求地址：

svrurl+PartialURL，例如： https://api.ilifesmart.com/app/api.EpMaintCartFiles • 请求信息： "id"： 974, "method":'"
EpMaintCartFiles",

"system": { "yer": "1.0", "lang": "en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx", "time": 1447639497, "sign":"
sIGN_xxxxxxxx" }， "params": { "agt":"AGT_xxxxxxxx", "act":"AddByUrl", "actargs":"
{\"uri\":\"https://x.cololight.com/mweb/attach/ upload/coloxxtemp/kt6_9AB807.rom\"}" } }

# ⚫ 签名原始字符串：

method:EpMaintCartFiles,act:AddByurl, actargs:{"url": "https://   
x.cololight.com/mweb/attach/upload/coloxxtemp/   
kt6_9AB807.rom"},agt:AGT_xxxxxxxx,time:1447639497,userid:1111111,use   
rtoken:UsERTOKEN_xxxxxxxX,appkey:APPKEY_xxxxxxxx, apptoken:APPTOKEN_X   
XXXXXXX

• 回复信息： "id": 974, "code": 0, "message":"success"

# 提示：

若是查询命令，则返回的Cart文件列表如下所示：  
{"code": 0,"message":{"MAXFILELEN"：1048576，指明单个Cart文件允许的最大大小，单位byte"MAXSTORESIZE"
：5242880，指明整个磁盘空间的最大容量，单位byte"files":[{"key"："kt6_9AB807.rom"，//标识该cart文件"size"
：55462/／指明该Cart文件的大小}1 ..

# 4.5.29.EpConfigAgt 设置智慧中心配置

# 4.5.29.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">EpConfigAgt</td><td></td><td>设置智慧中心的配置，包括是否允许本地登 录、修改本地登录密码等。</td></tr><tr><td>Partial URL</td><td colspan="2">api.EpConfigAgt</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="9">Request Content</td><td rowspan="9">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey (可选)终端唯一id。如果在授权时填入了，此</td></tr><tr><td>time -</td><td></td><td>处必须填入相同id</td></tr><tr><td></td><td>Y</td><td>UTC时间戳，自1970年1月1日起 计算的时间,单位 为秒</td></tr><tr><td>method agt</td><td>Y Y</td><td>EpConfigAgt</td></tr><tr><td rowspan="2">act</td><td>Y</td><td></td><td>智慧中心ID 操作指令，类型为字符串，</td></tr><tr><td>params actargs -</td><td>O</td><td>具体参考4.5.28.2 说明 操作指令参数，为JSON对象的序列化字符串，</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td><td>具体参考4.5.28.2 说明</td></tr></table>

# 4.5.29.2.act与actargs参数列表

<table><tr><td>Function 功能</td><td>act 符串</td><td>actargs 操作指令，为字操作指令参数，为JSON对象的序列 化字符串</td><td>Response 返回结果</td></tr><tr><td>查询是否允许 置</td><td></td><td>不要供参数，可以为nul或空地icy指示本地账号策</td><td>{stat, policy},stat 指示特定的状态，当stat 为&quot;locked&quot;即表明禁 止本地登录，ｓtat为 &quot;normal&quot;则表示允许本 略，当值为&quot;[nolsi]&quot; 表明本地互联必须提供正 确的账号/密码，否则不允 许登录。缺省为&quot;&quot;，表 示允许。</td></tr><tr><td></td><td></td><td>{stat，policy}，stat指明是否 允许本地登录，当stat为 &quot;locked&quot;即表明禁止本地登录， stat为&quot;normal&quot;则表示允许本 地登录； policy指明本地账户策略，当值为 &quot;[nolsi]&quot;表明本地互联必须提供 正确的账号/密码，否则不允许登 录。缺省为&quot;&quot;，表示允许。 {pwd}，Pwd指明本地登录admin账</td><td>&quot;success&quot;</td></tr><tr><td>设置本地登录</td><td>setLocalPwd</td><td>号所使用的密码，本地登录admin账 号缺省密码为admin，可以修改为需 要的密码。注意：pwd需要使用标准 Base64编码，例如假定密码设置 为数有要 求，密码是不可逆的加密方式存储在 智慧中心上 设置的密码不允许查询，密码是不可 逆的加密方式存储在智慧中心上，因</td><td>&quot;success&quot;</td></tr><tr><td>时区</td><td>查询智慧中心queryTimezon e</td><td>此没有queryLocalPwd动作 {}，不需要提供参数，可以为null 或空对象</td><td>{tmzone}，tmzone指明 当前所设置的时区</td></tr></table>

<table><tr><td>Function 功能</td><td>act 符串</td><td>actargs 操作指令，为字操作指令参数，为JSON对象的序列 化字符串</td><td>Response 返回结果</td></tr><tr><td>设置智慧中心setTimezone</td><td></td><td></td><td>&quot;success&quot;</td></tr><tr><td>查询智慧中心 地理位置</td><td>queryLoc</td><td>{}，不需要提供参数，可以为nul1 或空对象；</td><td>{lnglat}，lnglat返回 当前设置的地址位置，其 格式为&quot;lng，lat&quot;的字符 串</td></tr><tr><td>设置智慧中心setLoc 地理位置</td><td></td><td>{lnglat,fullsync},lnglat指 明本需要设置的地理位置，类型为字 符串，格式为&quot;lng，lat&quot;，例如 &quot;120.15507，30.274084&quot;为杭州 市经纬度；fullSync=1表示全量 同步，因为Loc实际上除了存储 lnglat之外还可以存储其它地理位 置信息，如果fullSync=1则不包含 在参数里面的其它键值都会被删除，</td><td>&quot;success&quot;</td></tr><tr><td>查询智慧中心querysys Mac、Ip信息</td><td></td><td>缺省ful1Sync=0; {}，不需要提供参数，可以为null 或空对象；</td><td>明智慧中心当前的IP地址 {${exsvc}:{...},},</td></tr><tr><td>询智慧中心queryExSvg</td><td></td><td>{verbose=1/0}，查询扩展服务， ver示返回每务的 并处于使能状态，缺省 verbose=0;</td><td>返回扩展服务当前的配置 以及状态。例如天气预报 扩展服务配喜：， &quot;appkey&quot;: &quot;×xX&quot;,id &quot;&quot;url&quot;:&quot;YYY&quot; } 1</td></tr><tr><td>配置慧心setEx</td><td></td><td>{svId, args={ },reload=1/0} 配置扩展服务。svcId指明扩展服务 Id，args指明扩展服务配置参数, 指展变更后 reload=1表示需要重新加载立即生 效。具体参考4.5.28.4说明</td><td>&quot;success&quot;</td></tr></table>

<table><tr><td>Function 功能</td><td>act 符串</td><td>actargs 操作指令，为字操作指令参数，为JSON对象的序列 化字符串</td><td>Response 返回结果</td></tr><tr><td>操作智慧中心 扩展服务</td><td>operExSv</td><td>{svId,act,actargs={ }}操作扩 展服务。svcId指明扩展服务Id， act指明操作的指令，值类型为字符 串，actargs指明操作指令的参数, 值类型为对象。具体参考 4.5.28.4说明</td><td>&quot;success&quot;</td></tr><tr><td>查询智慧中心 网络信息</td><td>netInfo</td><td>{ }，不需要提供参数，可以为nul1 或空对象；</td><td>返回网络信息，例如：{ &quot;gateway&quot;:[ &quot;? (192.168.4.1) at 24:fb:65:60:e3:03 [ether] on etho\n&quot; ] } gateway是一个数组，里 面的条目是ARP协议返回的 网关信息，可基于ARP协议 自行解析网关MAC地址。</td></tr><tr><td>询智queryNifCfg</td><td></td><td>{ifn,verbose=1/0}，查询网络 模块配置，verbose=l表示返回详 细的信息，缺省verbose=0。当前 ifn值如下可选: ·&quot;etho&quot;：网卡 &quot;eth1:华为4G Wifi UsB- ·&quot;ppp0&quot;：2g模块 ·&quot;wlan0&quot;:Wi-Fi ·&quot;usbetho&quot;:UsB卡</td><td>{${ifn}:{....}}, 返回查询的ifn当前的配 置，例如：{ &quot;wlan0&quot;:{ &quot;enable&quot;: true, &quot;metric&quot;: 100, &quot;C_NetworkType&quot;: &quot;mode&quot;: &quot;C_WPAPSK&quot;: &quot;12345678&quot;, &quot;C_HWMode&quot;: &quot;PEN&quot; &quot;name&quot;:&quot;wlan0&quot; }</td></tr></table>

<table><tr><td>Function 功能</td><td>act 操作指令，为字 符串</td><td>actargs 操作指令参数，为JSON对象的序列 化字符串</td><td>Response 返回结果</td></tr><tr><td>设置智慧中心 网络模块</td><td>setNifcfg</td><td>{ifn,enable=true/false},使 能/去使能网络模块。当前ifn值如 下可选： ·&quot;ethO&quot;:网卡 ·&quot;ethl&quot;：华为4G wifi USB- dongle ·&quot;ppp0&quot;：2G模块 ·&quot;wlan0&quot;:Wi-Fi ·&quot;usbetho&quot;：UsB网卡 ·&quot;wwanO&quot;：wwAN-4G模块 4G-CAT4 ·&quot;usb0&quot;:4G-CAT1</td><td>&quot;success&quot;</td></tr><tr><td>查询智慧中心 本地互白名 单</td><td>queryLsiwhit</td><td>{}，不需要提供参数，可以为nul1 或空对象。 有关智慧中心本地互联白名单说明请 参考4.5.28.5说明</td><td>返回当前设置的白名单列 表 [{lsid,user, pwd, add r},...] •lsid 为智慧设备的 LSID（一般等同于智慧 设备的agt属性) •user为智慧设备的登 录账号 •pwd为智慧设备的登录 密码</td></tr></table>

<table><tr><td>Function 功能</td><td>act 操作指令，为字 符串</td><td>actargs 操作指令参数，为JSON对象的序列 化字符串</td><td>Response 返回结果</td></tr><tr><td>单</td><td>设智中setsihite ist</td><td>[&#x27;-&#x27;,&#x27;lsid&#x27;], [-1,], [&#x27;+&#x27;, lsid,user, pwd] 设置白名单，支持多条目一起设置。 每个条目为一个JSONArray， •条目第一项为&quot;+&quot;或者 &quot;-&quot;，&quot;+&quot;指示添加白名 单，&quot;-&quot;指示删除白名单; •条目第二项为智慧设备的1sid, 若为删除白名单操作，的第二项值 •条目第三项为智慧设备的登录账 号，只有添加白名单的时候才需 要填写； •条目第三项为智慧设备的登录密 码，只有添加白名单的时候才需 要填写； 提示：Update修改操作与添加操作 参数一样，如果已经存在该lsid的 白名单，则会覆盖该lsid的user、</td><td>[{ret, retMsg}, ...] 返回设置列表项每一项设 置是成功，成功不等 于o，并且retMsg指示具 体的错误信息</td></tr><tr><td>查询智慧中心 本地互联搜索</td><td>queryLsiPoli</td><td>pwd设置。 {}，不需要提供参数，可以为null 或空对象；</td><td>{policy}，policy指示 当前的本地互联策略，其 值可为&quot;whitelist&quot;或 &quot;。 时候只给白名单设备发送 搜索包，否则智慧中心会</td></tr><tr><td>设置智慧中心 策略 模块</td><td>本地互联搜索setLsiPolicy 复位无线射频resetRfModul e</td><td>policy: &#x27;whitelist&#x27; or {}，不需要提供参数，可以为null 或空对象；</td><td>发送组播/广播包。 &quot;success&quot; &quot;success&quot;</td></tr></table>

# 4.5.29.3.范例 - setLocalPermission

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据； ■

请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.EpConfigAgt

# ● 请求信息：

{ "id": 974, "method":"EpConfigAgt", "system": { "ver":"i.0", "lang":"en", "userid": "1111111", "appkey":"
APPKEY_xxxxxxxx", "time"： 1447639497, "sign":"SIGN_xXXXXXXX" }， "params":{ "agt"："AGT_xxxxxxxx", "act":"
setLocalPermission", "actargs":"{\"stat\":\"locked\"}" }

签名原始字符串：

method:EpConfigAgt,act:setLocalPermission,actargs:{"stat": "locked"}, agt:AGT_xxxxxxxx, time:1447639497, userid:1111111,
usertoken: UsERToKEN_xxxxxxxx,appkey:APPKEY_xxxxxxxx,apptoken:APPToKEN_xxxxxxxx

• 回复信息： "id": 974, "code":0, "message":"success"

# 说明：

本地登录，指的是使用LifeSmartApp，在局域网内搜索到智慧中心，然后本地登录该智慧中心，从而进行操作控制。

# 4.5.29.4.智慧中心ExSv扩展服务说明

# ·天气服务

svId: "weather",  
args:{"enable"： True/False 是否使能服务"svt"："stylel"服务类型，当前填写"stylel"即可"url"
：{WEATHER_SERVICE_URL}天气服务URL"appkey"：{APPKEY}天气服务分配的AppKey"apptoken"{APPTOKEN}天气服务分配的AppToken  
} 1  
"reload"：1/0 是否重新加载立即生效

# ·MDNS搜索服务

svId: "lc_mdns",  
args:{"enable"：True/False 是否使能服务  
}1  
"reload"：1/0 是否重新加载立即生效  
动作定义－添加MAC地址act:"Addone"actargs: { ...}mac：String，MAc地址示例：{"act":"Addone","actargs":{"mac":"70886B14673D"}}

# 4.5.29.5.智慧中心本地互联白名单说明

本地互联指的是LifeSmart智慧设备在局域网内的互相通信功能，例如LifeSmart智慧中心可以在局域网内搜索到LifeSmart摄像头，认证通过之后便可在局域网内播放摄像头的实时视频流、设置摄像头的播放参数、控制摄像头的播放行为等；再比如LifeSmart智慧中心具备级联的功能，可以把下级智慧中心下面的子设备、例如NatureMini下面的子设备同步到本智慧中心下面做为子设备，从而查询/控制natureMini下面的子设备。

一般家庭络智慧设备比较少，可以不用设置本地互联白名单。但如果络环境复杂，智慧设备较多，为了使智慧设备相互隔离、减少网络数据广播风暴、确保安全稳定的使用体检则可以使用本地互联白名单功能。一种典型的应用环境为公租屋、民宿酒店，各个房间的智慧设备都处在一个局域网内，相互都可以被搜索到。而这往往会带来如下问题：

现场施工的时候智慧中心搜索局域网内其它智慧设备会搜索到非相关的设备；  
使用没有隔离，通过局域网可以控制/使用非管理域内的智慧设备；  
网络拥塞，智慧中心搜索发起的广播包会在局域网内蔓延；

使用本地互联白名单可以解决如上问题。为方便阐述问题，假定有一个房间，里面有如下LifeSmart智慧设备：智慧中心 Agtl、超能面板
NatureMinil、摄像头Cameral。假定Agtl的agt属性为"Agtl_agt";假定NatureMinil的lsid/agt属性为"NatureMinil_agt"
;假定cameral的lsid/agt属性为"Cameral_agt";

# 调用setLocalPermission指令设置超能面板与摄像头本地访问策略

"agt":"NatureMinil_agt", "act":"setLocalPermission", "actargs":"{\"policy\":\"[nolsi]\"}" "agt":"cameral_agt", "act":"
setLocaipermission", "actargs":"{\"policy\":\"[nolsi]\"}" }

调用setLocalPwd指令设置超能面板与摄像头本地访问密码"123456"

"agt":"NatureMinil_agt", "act":"setLocalPwd", "actargs":"{\"pwd\":\"mTIzNDu2\"}" "agt":"cameral_agt", "act":"
setLocaiPwd", "actargs":"{\"pwd\":\"mTIzNDu2\"}" }

# 调用setLsiWhitelist指令设置相关的智慧设备白名单

"agt": "Agt1_agt", "act": "setLsiwhitelist", "
actargs":"{[\"+\"，\"Naturemini1_agt\"， \"admin\", \"123456\"]，[\"+\"，\"camera1_agt\"，\"admin\"，\"123456\"]]" }

调用setLsiPolicy 指令设置策略为"whitelist"，只给白名单设备下发检索包 "agt": "Agt1_agt", "act":"setLsiPolicy", "actargs":"
{\"policy\": \"whitelist\"}"

# 4.5.30.NatureCtl 设置Nature面板首页按键等配置

# 4.5.30.1.JSON请求数据格式

![](images/46d69b4856f895b907df5d5f9648bcc667eab2ae737ed8c254ef9b78ae68e05d.jpg)

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">NatureCtl</td><td></td><td>设置Nature面板首页按键、快捷设备界面、更 多按键页等配置。</td></tr><tr><td>Partial URL</td><td colspan="2">api.NatureCtl</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="19">Request Content</td><td rowspan="6"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ID</td></tr><tr><td>appkey did</td><td>Y</td><td>appkey</td></tr><tr><td></td><td></td><td rowspan="2">(可选)终端唯一id。如果在授权时填入了，此 处必须填入相同id UTC时间戳，自1970年1月1日起 计算的时间,单位</td></tr><tr><td>time</td><td>Y</td></tr><tr><td>method</td><td></td><td>Y</td><td>为秒 NatureCtl</td></tr><tr><td rowspan="3">params -</td><td>agt</td><td>Y</td><td>智慧中心ID</td></tr><tr><td>act</td><td>Y</td><td>操作指令，类型为字符串， 具体参考4.5.29.2说明</td></tr><tr><td>actargs</td><td>O</td><td>操作指令参数，为JSON对象的序列化字符串， 具体参考4.5.29.2 说明</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 4.5.30.2.act与actargs参数列表

<table><tr><td>Function 功能</td><td>act 操作指令，为字符 串</td><td>actargs 操作指令参数，为JSON对象的序 列化字符串</td><td>Response 返回结果</td></tr><tr><td rowspan="2">基于云端数据 获取当前面板 Favs配置 （快速从云端 缓存数据获 取）</td><td rowspan="2">QueryFavs</td><td rowspan="2">空对象</td><td>{FAV NAME: FAV_√ALUE， ...}, ..} 返回当前查询agt下的 Favs配置。例如： &quot;NM_HOME&quot;:{ / &quot;FAV_b3&quot;: false,</td></tr><tr><td>&quot;icon&quot;: &quot;&quot; &quot;FAV_b2&quot;: false, &quot;FAV_pg1&quot;: &quot;A3EAxxxxxxxxxxxxxx xxx/me/ep/643a&quot;, &quot;FAV_b1&quot;: 不需要供参，可以为n或x/21× &quot;FAV_theme&quot;: &quot;black&quot;, false FAV b4&quot;:</td></tr></table>

<table><tr><td>Function 功能</td><td>act 串</td><td>actargs 操作指令，为字符操作指令参数，为JSON对象的序 列化字符串</td><td>Response 返回结果</td></tr><tr><td>基于面板自身 数据远程获取 当前面板 Favs配置从 面板获取数 据）</td><td>QueryFavsOnAgt</td><td>空对象</td><td>{ FAV_ID: {FAV_NAME : FAV_√ALUE， ·..}，..} 返回当前查询agt下的 Favs配置。例如： { &quot;NM_HOME&quot;:{ &quot;FAV_b3&quot;: false, &#x27;&quot;icon&quot;:&quot;&quot;, &quot;FAV_b2&quot;: &quot;FAV_pPg1&quot;: &quot;A3EAxxxxxxxxxxxxxx xxx/me/ep/643a&quot;, 不需要提供参数，可以为nu1或&quot;A3EAxxxxxxxxxxxx &quot;FAV_b4&quot;: false } 1 常用的配置信息具体参考 4.5.29.4 说明 注意： false,</td></tr><tr><td>设置当前面板</td><td>SetFavs</td><td>{favId, items : {FAV_NAME : FAV_VALUE, ...}} 配置，由name：value键值对组 成，常用的配置信息具体参考 4.5.29.4说明</td><td>的配置。实际以查询的数 据为准。</td></tr></table>

# 4.5.30.3.范例 - SetFavs

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；  
agt为AGT_XXXXXXXX，实际需要填写真实数据；

请求地址：svrurl+PartialURL，例如：

https://api.ilifesmart.com/app/api.NatureCtl

# ● 请求信息：

"id": 974, "method":'"NatureCtl", "system":{ "ver": "i.0", "lang":"en", "userid":"1111111", "appkey":"
APPKEy_xxxxxxxx", "time": 1659345834, "sign":"sIGN_xxxxxxxx" }， "params":{ "agt":"AGT_xxxxxxxx", "act": "setFavs", "
actargs":"{\"favId\":\"Nm_HOmE\"，\"items\":{\"FAV_b3\": \"A3EAxxxxxxxxxxxxxxxx/me/ep/6431\",\"FAV_b2\"：\"NULL\",
\"FAV_theme\":\"black\"}}" } }

# 签名原始字符串：

method:NatureCtl, act:SetFavs, actargs:{"favId":"Nm_HOME", "items":{"FA V_b3":"A3EAxxxxxxxxxxxxxxxx/me/ep/   
6431", "FAV_b2":"NuLL", "FAv_theme":"black"}},agt:AGT_xxxxxxxx, time:16 59345834, userid:1111111, usertoken:
UsERToKEN_xxxxxxxX, appkey:APPKEY_x xxxxxxX,apptoken:APPToKEN_xxxxxxxx

# • 回复信息：

{ "id": 974, "code": 0' "message":"success"   
}

# 4.5.30.4.Nature面板Favld设置说明

本表格描述了NatureMINI系列设备通过FavId定义面板的主题、快捷按键等信息。  
查询中若获取的Fav_Name，若未在本表格中提及，则可以先忽略对应的配置。

<table><tr><td>FavId</td><td>Fav_Name</td><td>Fav_Value</td></tr><tr><td rowspan="7">NM_HOME</td><td>FAV_b1 FAVb2 FAV_b3 FAV_b4</td><td>面板首页的4个位置的配置； Fav Value查询: 值为false时，表示显示空位； 值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5 说明 Fav Value设置:</td></tr><tr><td>FAV_pg1 FAV_Pg2</td><td>值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5说明 面板快捷页面的配置： Fav Value查询: 值为false时，表示显示空位； 值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot; Fav Value设置: 值为“NULL&quot;时，表示清空对应配置，显示空位； 值为对象ID时，表示显示对应的对象，形</td></tr><tr><td>FAV_pg2_enable</td><td>如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5说明 面板快捷页面是否启用FAV_Pg2，默认不启用； 值为false时表示不启用； 值为true时表示启用FAV_Pg2 配置；</td></tr><tr><td>FAV_theme</td><td>设置为“NULL&quot;，表示清空该配置； 面板主题设置，默认为系统默认主题； 当前支持的主题值有： &quot;light&quot;：白昼主题 &quot;black&quot;：暗夜主题 &quot;moon&quot;：红月主题 &quot;cartoon&quot;：卡通主题 设置为“NULL&quot;，表示清空该配置，默认为系统默认主题；</td></tr></table>

<table><tr><td>FavId</td><td>Fav_Name</td><td>Fav_value</td></tr><tr><td rowspan="5"></td><td>FAV_colox_enabl e</td><td>是否使能面板UI自定义。 false表示不使能；true表示使能。</td></tr><tr><td>FAV_cart_ss</td><td>屏保页自自定义uī，值为cart key</td></tr><tr><td>FAV_cart_home</td><td>Home首页自定义ur，值为Cart key</td></tr><tr><td>FAV_cart_scene</td><td>面板首页侧滑第一屏自定义ur，值为cart key</td></tr><tr><td>FAV_cart_scene2</td><td>面板首页侧滑第二屏自定义uI，值为cart key</td></tr><tr><td rowspan="3">NM_SCENE</td><td>FAV_b1 FAVb2 FAVb3 FAV_b4 FAV_ 5 值为&quot;NULL&quot;时，表示清空对应配置，显示空位；</td><td>面板首页侧滑第一屏6个快捷按键页对应的配置； Fav_Value查询： 值为false时，表示显示空位； 值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5说明 Fav_Value设置:</td></tr><tr><td>FAV_enable</td><td>值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5说明 是否启用NM_SCENE，默认启用； 值为false时表示不启用；</td></tr><tr><td>FAV_b1 FAV_b2 FAV_b3 FAV_b4 FAVb5</td><td>值为true时表示启用NM_SCENE配置； 面板首页侧滑第二屏6个快捷按键页对应的配置； Fav_Value查询: 值为false时，表示显示空位； 值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5说明</td></tr><tr><td rowspan="2">NM_SCENE2</td><td>FAV_b6</td><td>Fav Value设置: 值为“NULL&quot;时，表示清空对应配置，显示空位； 值为对象ID时，表示显示对应的对象，形 如：&quot;A3EAxxxxxxxxxxxxxxxx/me/ep/6431&quot;，具体 参考4.5.29.5说明 是否启用NM_SCENE2，默认不启用；</td></tr><tr><td>FAV_enable</td><td>值为false时表示不启用； 值为true时表示启用NM_SCENE2配置； 设置为“NULL&quot;，表示清空该配置；</td></tr></table>

# 4.5.30.5.设备或AI对象ID说明

面板上可以配置的对象类型一般有EP设备、IO设备和AI设备；  
若面板作为智慧中心，则可以将面板下的设备和智能配置到首页上进行控制；  
若面板配置了Wi-Fi，则可以通过本地搜索发现同一个网络下其他智慧中心，将同一网络的智慧中心下的设备和智能配置到首页上进行着控制；  
若配置的对象ID信息不存在或错误，面板界面上有可能显示“未知设备"或其他错误。

# ·EP设备

对象ID规则为："AGT_ID/me/ep/ME_ID"假若需要配置一个窗帘设备：

若窗帘的信息为:   
agt $=$ "A3EAxxxxxxxxxxxxxxxx"，me $=$ "'2202"   
则对象ID配置为：   
"A3EAxxxxxxxxxxxxxxxx/me/ep/2202"

# ·IO设备

对象ID规则为："AGT_ID/me/ep/ME_ID/m/IO_IDX"假若需要配置一个面板的第三路开关：

若开关的信息为：  
agt $=$ "A3EAxxxxxxxxxxxxxxxx", $\mathtt { m e } = " 0 0 0 1 "$ ,idx $\displaystyle =$ "P3"  
则对象ID配置为：  
"A3EAxxxxxxxxxxxxxxxx/me/ep/0001/m/P3"

# ·AI设备

对象ID规则为："AGT_ID/me/ai/Al_ID"假若需要配置一个同络下某智慧中心下的场景A:

若场景的信息为:  
agt $=$ "A3EAxxxxxxxxxxxxxxxx"，me $=$ "4802"，ai $\underline { { \underline { { \mathbf { \Pi } } } } } =$ "
AI_0I_1646821884"  
则对象ID配置为:  
"A3EAxxxxxxxxxxxxxxxx/me/ai/AI_OI_1646821884"

# 5.设备属性定义

OpenAPI接口分为两类，一类是查询设备类，一类是控制设备类；当对设备进行查询接口调用时，返回的数据信息中含有一些通用属性用于描述该设备，见：表5-1-1，另外不同的设备包含的其特有属性，如不同的IO控制口的属性信息说明，请参阅文档：

《LifeSmart智慧设备规格属性说明》  
表5-1-1通用属性说明

<table><tr><td>Attribute</td><td>Type</td><td>RW</td><td>Decription</td></tr><tr><td>devtype/cls</td><td>string</td><td>R</td><td>设备类型</td></tr><tr><td>name</td><td>string</td><td>RW</td><td>设备名称</td></tr><tr><td>agt</td><td>string</td><td>R</td><td>设备所属智慧中心ID号</td></tr><tr><td>me</td><td>string</td><td>R</td><td>设备ID (智慧中心下面唯一)</td></tr><tr><td>stat</td><td>int32</td><td>R</td><td>是否处于在线状态 0:offline 1:online</td></tr><tr><td>data</td><td>array</td><td>R</td><td>设备下的Io控制口的信息</td></tr></table>

当对智慧设备进行控制类接口调用时，请参阅文档：《LifeSmart智慧设备规格属性说明》中对应需要控制的设备规格的属性说明设置控制参数，需要注意的是，其中某些属性没有针对OpenAPI进行开放，且只有标识为RW的属性才具有设置功能。

# 6.发现协议

发现协议定义了在局域网中发现智慧中心等智慧设备的方法。

<table><tr><td>协议</td><td>UDP</td></tr><tr><td>端口号</td><td>12345</td></tr></table>

<table><tr><td>报文类型</td><td>广播报文</td></tr><tr><td>报文内容</td><td>Z-SEARCH*\r\n</td></tr><tr><td rowspan="6">智慧中心/智慧设备 返回格式</td><td>MOD=xxxx\nSN=xxxx\nNAME=xxxx\n</td></tr><tr><td>或者</td></tr><tr><td>MGAMOD=xxxxx\nLSID=xxxxx\nNAME=xxxxx\n 其中xXXx是智慧设备相应的设置值。</td></tr><tr><td>新版本智慧设备也可能会添加新的属性，会以\n/分割，如果不识别可以</td></tr><tr><td>忽略。</td></tr><tr><td>·MGAMOD或MOD为智慧设备类型； •SN或者LSID为智慧设备序列号；</td></tr></table>

# 7.状态接收

第三方应用可以关注设备状态的更改事件。LifeSmart OpenAPl 服务提供以 WebSocket 方式接入，关注设备的状态更改事件。

Note:

⚫ 第一次认证成功后，Socket将保持连接，可以对该连接发送wbAuth和RmAuth接口请求。⚫
wbAuth：WebSocket认证，一次认证一个用户，可以在一个连接多次认证，达到单连接多用户的效果，并且可以持续认证；●
RmAuth：WebSocket认证移除，一次移除一个用户，用户数到零时，连接自动断开；

# 7.1.流程

![](images/ca87885ed49d63dc9030523f0b1f3476729b0eb86a54dcaf32b59b3191a21fcf.jpg)

# 7.2.URI

根据不同的用户账号（LifeSmart用户）所在的服务区域，WebSocket服务需要使用对应的服务地址。svrrgnid 为服务分区标记，在户授权成功后将会返回对应的
svrrgnid信息。根据不同的 svrrgnid 使用以下对应的 WebSocket URL:

<table><tr><td>Service Type</td><td colspan="2">svrrgnid</td><td>URL</td></tr><tr><td rowspan="9">Websocket with ssI</td><td>GS</td><td></td><td>wss://api.ilifesmart.com:8443/wsapp/</td></tr><tr><td>CNO</td><td></td><td>wss://api.cn0.ilifesmart.com:8443/wsapp/</td></tr><tr><td>VIP1</td><td></td><td>wss://api.cn1.ilifesmart.com:8443/wsapp/</td></tr><tr><td>CN2</td><td></td><td>wss://api.cn2.ilifesmart.com:8443/wsapp/</td></tr><tr><td>AME</td><td></td><td>wss://api.us.ilifesmart.com:8443/wsapp/</td></tr><tr><td>EUROPE</td><td>-</td><td>wss://api.eur.ilifesmart.com/wsapp/</td></tr><tr><td>JAP</td><td></td><td>wss://api.jp.ilifesmart.com:8443/wsapp/</td></tr><tr><td>APZ</td><td></td><td>wss://api.apz.ilifesmart.com:8443/wsapp/</td></tr></table>

# 注意：

webSocketURL地址的选择，必须根据用户授权成功后返回的 svrrgnid•保持一致，否则不会正常工作，websocket不支持跨区使用。

# 7.3.Websocket认证

正确连接webSocket后，请第一时间发送认证消息，否则连接会被中断。

# 7.3.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">WbAuth</td><td></td><td>Websocketi认证</td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td rowspan="10">Request Content</td><td rowspan="10">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User ià</td></tr><tr><td>appkey did</td><td>Y 0</td><td>appkey</td></tr><tr><td>time</td><td>V</td><td>(可选)终端唯一id。如果在授权时填 入了，此处必须填入相同id</td></tr><tr><td></td><td></td><td>UTC时间戳，自1970年1月1日起 计算的 时间,单位为秒</td></tr><tr><td>method</td><td>Y</td><td>WbAuth</td></tr><tr><td>id</td><td>Y</td><td>消息id号</td></tr></table>

# 7.3.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

# ● 请求信息：

"id": 957,   
"method":"wbAuth",   
"system":{ "yer": "1.0", "lang": "en", "userid": "1111111",

"appkey": "ApPKEy xxxxxxxx", "time": 1447641115, "sign":"sIGN_xxxxxxxx"

● 签名原始字符串： method:wbAuth, time:1447641115,userid:1111111, usertoken:UsERToKEN_xxx xxxxx, appkey:APpKEy_xxxxxxxx,
apptoken:APPToKEN_xxxxxxxx

回复信息： "id": 957, "code": 0, "message":"success"

# 7.4.WebSocket认证用户移除

# 7.4.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Mus t</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">RmAuth</td><td></td><td>WebSocket认证用户移除</td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>Request Content</td><td rowspan="6"></td><td>ver</td><td>Y</td><td>1.0 0</td></tr><tr><td rowspan="6">system</td><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>User id</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>did</td><td>O</td><td>(可选)终端唯一id。如果在授权时填入 了，此处必须填入相同id</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日起 计算的时间， 单位为秒</td></tr><tr><td colspan="3">method</td><td>Y RmAuth</td></tr><tr><td colspan="2">id</td><td>Y</td><td>消息id号</td></tr></table>

# 7.4.2.范例

⚫ 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

# • 请求信息：

"id": 957,   
"method":"RmAuth",   
"system": { "ver": "i.0", "lang":"en", "userid": "1111111", "appkey":"APPKEY_xxxxxxxx",

"time": 1447641115, "sign":"SIGN_xxxxxxxx"

• 签名原始字符串： method:RmAuth, time:1447641115,userid:1111111, usertoken:UsERTOKEN_xxx xxxxx,appkey:
APPKEY_xxxxxxxx,apptoken:APPToKEN_xxxxxxxx

• 回复信息： { "id": 957, "code": 0, "message":"success"

# 7.5.事件格式

所有事件数据为JSON 编码，其格式如下：

<table><tr><td>id</td><td>消息id号</td></tr><tr><td>type</td><td>事件类型。type=&#x27;io&#x27;表示ro状态数据更新 -</td></tr><tr><td>msg</td><td>事件体。根据不同事件类型进行不同解析</td></tr></table>

# 7.6.事件数据信息

事件内容属性如下：

<table><tr><td>字段名称</td><td>类型</td><td>描述</td></tr><tr><td>userid</td><td>string</td><td>用户ID</td></tr><tr><td>agt</td><td>string</td><td>智慧中心id</td></tr><tr><td rowspan="2">me</td><td rowspan="2">string</td><td>终端设备id</td></tr><tr><td>当为智慧中心级别事件则其值不存在； 当为AI类型事件其值表示的是A的id；</td></tr></table>

<table><tr><td>idx</td><td>string</td><td>终端设备IO指示。根据设备类型不同，其内容不一样。与设备属性的 DevType对应，比如r，O等。 idx=&quot;s&quot;是特殊的类型，需要查看其它属性做进一步的判断。 如果有info字段则需要参考info信息做进一步处理，例如设备添加， 设备删除，设备名称修改，AI添加/删除/变化等特定事件；否则即为 设备/智慧中心上下线。</td></tr><tr><td>devtype</td><td>string</td><td>设备类型 当为智慧中心事件则其值固定为&quot;agt&quot;； 当为AI类型事件则其值固定为&quot;ai&quot;； 注：当devtype等于&#x27;elog&quot;则为特殊的事件，具体内容需要参考事件 体内的elog属性(属性值为对象类型)。</td></tr><tr><td>ful1Cls</td><td>string</td><td>包含设备版本号的完整设备类型</td></tr><tr><td>type</td><td>int32</td><td>终端设备o值类型，含义同设备属性定义，当idx=&quot;s&quot;标识特殊事件 的时候，其值无效</td></tr><tr><td>val</td><td>int32</td><td>终端设备IO值，含义同设备属性定义，当idx=&quot;s&quot;标识特殊事件的时 候，其值无效</td></tr><tr><td></td><td>float</td><td>真实有效值。在idx!=&quot;s&quot;情况下，其值是val值的真实友好值，例如 温度变化事件，val=230，v=23.0，表示温度值是23.0摄氏度，在 idx=&quot;s&quot;情况下，其值是特定的值，具体如下： 设备上线，其值=1；</td></tr><tr><td>ts</td><td>int64</td><td>设备下线，其值=2； 事件发生UTC时间．从1970.1.1到现在的毫秒数</td></tr><tr><td>info</td><td>string</td><td>事件扩展信息，其值有：&quot;add&quot;，&quot;del&quot;，&quot;name&quot;，&quot;ioname&quot;， &quot;full&quot;，&quot;chg&quot;等。 add：标识是设备/智慧中心/AI的添加事件； del：标识是设备/智慧中心/AI的删除事件； name：标识是设备名称修改的事件； ioname：标识是设备Io名称修改的事件; full：标识是智慧中心全量同步的事件； chg：标识是AI的修改事件，包括名称，状态，配置；</td></tr><tr><td>name</td><td>string</td><td>仅在名称修改事件有效，包括设备名称/设备IO名称/AI名称的修改事 件，既info=&quot;name&quot;或info=&quot;ioname&quot;或info=&quot;chg&quot;。指示新的 名称。</td></tr><tr><td>io</td><td>string</td><td>仅在设备Io名称修改事件有效，既info=&quot;ioname&quot;。指示设备的哪个 ⅠO发生名称变更。</td></tr><tr><td>stat</td><td>int32</td><td>仅AI事件有效，标识AI的状态发生变更 stat=0 表示AI处于初始态； stat=3 表示 AI正在运行； stat=4表示AI运行完成；</td></tr></table>

<table><tr><td>cmdlist</td><td>bool</td><td></td><td>仅AI事件有效，为True标识Ar的配置发生变更</td></tr><tr><td>elog</td><td>object</td><td>安防事件内容，具体属性定义如下： -3:RED -2:YELLOW -1:GREEN -O:N/A •cgy：string，事件类别(category) -&quot;sys&quot;: System -&quot;alm&quot;:Alarm -&quot;nty&quot;: Notification •cls：string，事件类型(class) -&quot;arm&quot;：布防操作 -&quot;disarm&quot;：撤防操作 -&quot;home&quot;：在家操作 -&quot;alarm&quot;：告警操作 -&quot;m&quot;：指示触发的是MotionIo -&quot;TR&quot;：指示触发的是TRIO -&quot;A&quot;：指示触发的是ALARMIO -&quot;open&quot;：KeyPad用户开锁 -&quot;add[nfc]&quot;：添加KeyPad NFc卡用户 -&quot;add[key]&quot;：添加KeyPad密码用户 -&quot;auth[admin]&quot;：KeyPad管理员认证 是发起请求相关的设备 -&quot;errlock&quot;：KeyPad输入错误锁定/解锁 -其它IO：指示防区内其它设备IO触发事件 •obj：string，相关涉及对象，具体参考elog场景定义举例 •info：string，&quot;0&quot;通常表示成功，&quot;1&quot;通常表示失败 •lc：string，对应的防区ID，格式为&quot;${AGT}/me/lc&quot;，如果 -&quot;msg&quot;: Message</td><td>•lvl：int32，事件告警级别，值越大级别越高，越应该重视 -&quot;fail&quot;：KeyPad认证失败操作，这时候obj是请求的操作，lc</td></tr></table>

场景定义举例：10变化事件有效字段：userid,agt,me,idx,devtype,type,val,v,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2ad5","idx":"L1",'t ype":129,"val":1,"
devtype":"SL_SW_RC","'ts":1521455567867},"id":1}

例如环境感应器湿度变化事件 {"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"H","ty
pe":95,"val":462,"V":46.2,"devtype":"SL_SC_THL","'ts":1521532876138},"id":1}

# 设备上线事件

有效字段：userid,agt,me,idx $\mathop { }$ "s",devtype,v=1,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"s","de vtype":"SL_SF_IF3","V":1,"
ts":1521532876138},"id":1}

# 设备离线事件

有效字段：userid,agt,me,idx $\mathop { }$ 's",devtype,v=2,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"s","de vtype":"SL_SF_IF3", "V":
2,"ts":1521532876138},"id":1}

# 设备名称修改事件

有效字段：userid,agt,me,idx $\mathop { }$ 's",devtype,info $^ { 1 = }$ 'name",name,ts

{'type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"s","inf o":"name","name":"
NEW_NAME","devtype":"SL_SF_IF3","ts":1521532876138},"id":1}

# 10名称修改事件

有效字段：userid,agt,me,idx="s",devtype,info="ioname",name,io,ts

{'type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"s","inf o":"ioname","name":"
NEW_IO_NAME","io":"L2","devtype":"SL_SF_IF3",'ts":1521532876138},"id":1}

# 设备添加事件

有效字段：userid,agt,me,idx $\equiv$ "s",devtype,info="add",v=0,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"s","inf O":"add","devtype":"
SL_SF_IF3","V":0,"ts":1521532876138},"id":1}

# 设备删除事件

有效字段：userid,agt,me,idx="s",devtype,info $^ { 1 = }$ "de|", V=−1,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"2aca","idx":"s","inf o":"del","devtype":"
SL_SF_IF3","V":-1,"ts":1521532876138},"id":1}

智慧中心添加事件 有效字段：userid,agt,idx $\mathop { }$ "s",devtype="agt",info="add",v=0,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","idx":"s","info":"add","de vtype":"agt","v":0,"'ts":
1521532876138},"id":1}

智慧中心删除事件有效字段：userid,agt,idx $\mathop { }$ "s",devtype $=$ "agt",info $^ { 1 = }$ "del"',V=-1,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjgsNA","idx":"s","info":"del","dev type":"agt","v":-1,"ts":
1521532876138},"id":1}

智慧中心上线事件有效字段：userid,agt,idx="s",devtype $=$ "agt" $\downarrow = \uparrow$ ,ts

{'type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","idx":"s","devtype":"agt", "V":1,"ts":
1521532876138},"id":1

智慧中心离线事件有效字段：userid,agt,idx $\mathop { }$ "s",devtype $=$ "agt" $v = 2$ ts

{'type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjgsNA","idx":"s","devtype":"agt", "V":2,"ts":
1521532876138},"id":1}

智慧中心全量同步事件有效字段：userid,agt,idx $\mathop { }$ "s",devtype $= ^ { \prime }$ 'agt",info $=$ "full",tss

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","idx":"s","info":"full","dev type":"agt","'ts":
1521532876138},"id":1}

# AI添加事件

有效字段：userid,agt,me,idx $\mathop { : = }$ "s",devtype="ai",info="add",v=0,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"Al1544609170","idx ":"s","info":"add","
devtype":"ai","v":0,"'ts":1544609170932},"id":1}

# AI删除事件

有效字段：userid,agt,me,idx $\mathop { }$ "s",devtype="ai",info $=$ "de|", V=−1,ts

{'type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"Al1544609170","idx ":"s","info":"del","
devtype":"ai”,"v":-1,"ts":1544609265325},"id":1]

# AI变化事件-修改名称

有效字段：userid,agt,me,idx="s",devtype="ai",info $= ^ { n }$ chg",name,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"Al1544609170","idx ":"s","info":"chg","
devtype":"ai","name":"NewName","ts":1544609265325},"id":1}

AI变化事件-修改配置 有效字段：userid,agt,me,idx="s",devtype $=$ "ai",info $= ^ { \prime \prime }$ chg",cmdlist,ts

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"Al1544609170","idx ":"s","info":"chg","
devtype":"ai","cmdlist":True,"ts":1544609265325},"id":1}

{"type":"io","msg":{"userid":"10001","agt":"A3EAAABtAEwQRzMoNjg5NA","me":"Al1544609170","idx ":"s","info":"chg","
devtype":"ai","stat":3,"ts":1544609265325},"id":1}

# elog场景定义举例:

# 布防状态下,有安防设备事件产生

elog字段定义:

• cgy="alm",   
·Cls=触发事件的设备IO属性,例如"TR","A","M", $\vert v \vert = 3$ ,   
· info $| = " 0 "$ ,   
•obj $\mid =$ 设备ID,格式为"\${AGT}/me/ep/\${ME_ID}", $\mid { \mathsf { c } } =$ 防区ID,格式为"\${AGT}/me/c"或"
\${AGT}/me/c/sub/\${area_id},没有防区则为"

示例：userid $\mid =$ '7722454", agt $: = \iota$ '
A3QAAABmAFAGRzczXXXXXX", ${ \mathrm { i } } \mathsf { d } \mathsf { x } = { \mathrm { ' } } { \mathsf { s } } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts ${ } _ { 1 } = { }$ 1675662554000, elog $=$ {cgy $" =$ "alm", cls $: =$ TR",
IV $\scriptstyle \left| = 3 \right.$ , info $| = " 0 "$ ,obj $\left| = ^ { \prime } \right.$ 'A3QAAABmAFAGRzczXXXXXX/
me/ep/2722}", $\scriptstyle 1 c = ^ { \prime }$ 'A3QAAABmAFAGRzczXXXXXX/me/lc"}

# 撤防状态下,有安防设备事件产生

elog字段定义:

• cgy $\mathit { \Theta } =$ "nty",   
·cls=触发事件的设备IO属性,例如"TR","A","M" $\vert v \vert = 2$ ,   
· info $\mathbf { \mu } = \mathbf { \mu } ^ { \prime \prime } \mathbf { 0 } ^ { \prime \prime }$ ,   
•obj $\mid =$ 设备ID,格式为"\${AGT}/me/ep/\${ME_ID}, $\mid { \mathsf { c } } =$ 防区ID,格式为"\${AGT}/me/c"或"
\${AGT}/me/lc/sub/\${area_id}",没有防区则为""

示例：userid="7722454", agt="
A3QAAABmAFAGRzczXXXXXX'", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $=$ {cgy $" =$ "nty", cls $: = :$ "TR", $\vert v \vert = 2$ ,
info $| = " 0 "$ , obj="A3QAAABmAFAGRzczXXXXXX/ me/ep/2722", $\vDash$ "A3QAAABmAFAGRzczXXXXXX/me/lc"}

# 有安防设备事件消失

elog字段定义:

• cgy="msg",   
• cls ${ } = { }$ 触发事件的设备IO属性,例如"TR","A","M", $\vert v \vert = 1$ ,   
· info $| = " 0 "$ , -   
•obj $\mid =$ 设备ID,格式为"\${AGT}/me/ep/\${ME_ID}", $\mid { \mathsf { c } } =$ 防区ID,格式为"\${AGT}/me/c"或"
\${AGT}/me/c/sub/\${area_id},没有防区则为"

示例：userid="7722454", agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ , devtype $! =$ "elog",
ts=1675662554000, elog $=$ {cgy="msg", cls $=$ TR", IV $= 1$ , info $| = " 0 "$ , obj="A3QAAABmAFAGRzczXXXXXX/
me/ep/2722", I0 $\left. = \right.$ "A3QAAABmAFAGRzczXXXXXX/me/lc"}

# 布防操作

elog字段定义：

${ \mathsf { c g y } } = " { \mathsf { s y s } } " $   
• cls $= ^ { \prime \prime }$ arm",$\vert v \vert = 0$ ,  
• info $| = " 0 "$ ,  
• obj $\left| = \right|$ ”执行操作的LifeSmart用户 $| \mathsf { D } ^ { \prime }$ $\mid { \mathsf { c } } =$
防区ID,格式为"\${AGT}/me/lc"或"\${AGT}/me/lc/sub/\${area_id}"

示例：userid $= ^ { \prime \prime } 7 7 2 2 4 5 4 ^ { \prime \prime }$ , agt $z ^ { \prime \prime }$
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000,
e $\scriptstyle | 0 9 = \{ \mathbf { C } 9 y = " \mathbf { S } \ y \mathbf { S } ^ { \prime \prime }$ ,
cls ${ } _ { 1 } = { }$ "arm", lv $\mathtt { \mathtt { = 0 } }$ , info $| = " 0 "$ , Obj="
7722454", $\mathbf { \bar { C } } \mathbf { = } ^ { \prime \prime } \mathbf { \bar { A } } 3$
QAAABmAFAGRzczXXXXXX/me/lc"}

# 撤防操作

elog字段定义:

${ \mathsf { c g y } } = " { \mathsf { s y s } } " $ ,   
• cls $=$ "disarm", $\vert v \vert = 0$ ,   
• info $| = " 0 "$ ,   
•obj="执行操作的LifeSmart用户ID", $\mid { \mathsf { c } } =$ 防区ID,格式为"\${AGT}/me/lc"或"
\${AGT}/me/c/sub/\${area_id}”

示例：userid="7722454", agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ , devtype $! =$ "elog",
ts=1675662554000, $\mathsf { e l o g } = \{ \mathsf { C g } \ y = { } ^ { \prime \prime } \mathsf { S } \ y \mathsf { S } ^ { \prime \prime }$ ,
cls="disarm", Iv $\mathtt { \mathtt { = 0 } }$ ,
info $| = " 0 "$ $\scriptstyle 0 \mathsf { b j } = { } ^ { \prime \prime } 7 7 2 2 4 5 4 ^ { \prime \prime }$ Ic="
A3QAAABmAFAGRzczXXXXXX/me/lc"}

# 在家操作

elog字段定义:

${ \mathsf { c g y } } = " { \mathsf { s y s } } " $   
• cls $=$ "home",  
. $\vert v \vert = 0$ ,  
• info $| = " 0 "$   
• obj $\left| = ^ { \prime } \right.$ 执行操作的LifeSmart用户ID",$\mid { \mathsf { c } } =$ 防区ID,格式为"\${AGT}/me/c"
或"\${AGT}/me/c/sub/\${area_id}"

示例：userid $\left| = \right|$ '722454"', agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", t5 ${ } _ { 1 } = { }$
1675662554000, $\mathsf { e l o g } = \{ \mathsf { C g } \ y = { } ^ { \prime \prime } \mathsf { S } \ y \mathsf { S } ^ { \prime \prime }$
cls ${ } _ { 1 } = { }$ "home", Iv $\mathtt { \mathtt { = 0 } }$
info $\scriptstyle \mathbf { \alpha } = \mathbf { \prime \prime } 0 ^ { \prime \prime }$ , Obj="
7722454", $\ l { 1 c = }$ "A3QAAABmAFAGRzczXXXXXX/me/lc"}

# 告警操作

elog字段定义:

• cgy="alm",  
• cls $= ^ { \prime }$ 'alarm",  
. $\vert v \vert = 3$ ,  
• info $| = " 0 "$ ,  
•obj $= ^ { \prime \prime }$ 执行操作的LifeSmart用户ID",$\mid { \mathsf { c } } =$ 防区ID,格式为"\${AGT}/me/lc"或"
\${AGT}/me/lc/sub/\${area_id}"

示例：userid $\mid =$ "7722454", agt $\cdot =$ "
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $\mid =$ {cgy="alm", cls ${ } = { }$ "
alarm", $\vert v \vert = 0$ ,
info $| = " 0 "$ $\scriptstyle { \begin{array} { l } { \scriptstyle = " 7 7 2 2 4 5 4 " } \end{array} } $ , $\ K =$ "
A3QAAABmAFAGRzczXXXXXX/me/lc"}

# 添加KeyPad NFC用户成功

elog字段定义:

• cgy="sys",  
• cls $u = \prime$ 'add[nfc]",$\vert v \vert = 0$ ,  
• info $| = " 0 "$ ,  
•obj="新创建的KeyPad用户ID",  
. $\vert c = ^ { \prime \prime }$ 操作终端和管理账号"

示例：userid $= ^ { \prime \prime } 7 7 2 2 4 5 4 ^ { \prime \prime }$ , agt="A3QAAABmAFAGRzczXXXXXX', idx="s",
devtype $^ { \ast = }$ "elog", ts=1675662554000,
e $\scriptstyle | 0 9 = \{ \mathbf { C } 9 y = " \mathbf { S } \ y \mathbf { S } ^ { \prime \prime }$
,cls $\mathbf { \alpha } _ { 1 } = \mathbf { \alpha } _ { 1 }$ "add[nfc]", lvl=o, info $| = " 0 "$ , Obj="21", Ic="
A3QAAABmAFAGRzczXXXXXX/me/ep/2765[1]"}

# 添加KeyPad NFC用户失败

elog字段定义:

${ \mathsf { c g y } } = " { \mathsf { s y s } } " $ ,   
• cls="add[nfc]", $\vert v \vert = 0$ ,   
• info="1",   
• obj="", $\vert c = ^ { \prime \prime }$ 操作终端和管理账号"

示例：userid="7722454", agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $=$ {cgy="sys",
cls $\mathbf { \alpha } _ { 1 } = \mathbf { \alpha } _ { 1 }$ "add[nfc]", $\vert v \vert = 0$ info $1 = "$ "1",
j="", $\ K =$ 'A3QAAABmAFAGRzczXXXXXX/me/ep/2765[1]"}

# 添加KeyPad 密码用户成功

elog字段定义：${ \mathsf { c g y } } = " { \mathsf { s y s } } " $ • cls $=$ "add[key]",$\vert v \vert = 0$ ,-•
info $| = " 0 "$ •obj $\left| = \right|$ "新创建的KeyPad用户ID",. $\vert c = ^ { \prime \prime }$ 操作终端和管理账号"

示例：userid="7722454", ag $: =$ "
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog",, ts=1675662554000, elog={cgy="sys",
cls $\mathbf { \alpha } _ { 1 } = \mathbf { \alpha } _ { 1 }$ "add[key]", lv $\mathtt { \mathtt { = 0 } }$ ,
info $| = " 0 "$ , obj $= " 2 2 "$ , Ic="A3QAAABmAFAGRzczXXXXXX/me/ep/2765[1]"}

# KeyPad 用户开锁成功

elog字段定义： • cgy="sys", • cls $\mathbf { \mu } = \mathbf { \prime }$ 'open",

・ $\vert v \vert = 0$ ,  
·info $\mathbf { \mu } = \mathbf { \mu } ^ { \prime \prime } \mathbf { 0 } ^ { \prime \prime }$ ,  
•obj $= ^ { \prime \prime }$ 开锁的动作对象，可以是锁设备IO或者情景模式Al',格式为"
ep/\${ME}/m/\${IO_IDX},$\vert c = ^ { \prime \prime }$ 操作终端和KeyPad用户ID"

示例：userid $\mid =$ '7722454", agt $\cdot =$ "
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog",
ts=1675662554000, $\mathsf { e l o g } = \{ \mathsf { C g } \ y = { } ^ { \prime \prime } \mathsf { S } \ y \mathsf { S } ^ { \prime \prime }$
cls $\mathbf { \alpha } _ { 1 } = \mathbf { \alpha } _ { 1 }$ "open", $\vert v \vert = 0$ ,
info $\mathbf { \mu } = \mathbf { \prime \prime 0 ^ { \prime \prime } }$ , obj $=$ "ep/2711/m/P1", $\ l { 1 c = }$ '
A3QAAABmAFAGRzczXXXXXX/me/ep/2765[1]"} -

# KeyPad 用户开锁失败

elog字段定义:

${ \mathsf { c g y } } = " { \mathsf { s y s } } " $   
• cls $= ^ { I }$ 'open",   
・ $\vert v \vert = 0$ ,   
· info $\mathbf { \lambda } = \mathbf { \lambda } ^ { \prime \prime } \mathsf { 1 } ^ { \prime \prime }$ ,   
•obj $= ^ { \prime \prime }$ 开锁的动作对象，可以是锁设备IO或者情景模式Al',格式为"
ep/\${ME}/m/\${IO_IDX}", $\vert c = ^ { \prime \prime }$ 操作终端和KeyPad用户ID"

示例：userid="7722454", agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { X } = " \mathsf { S } ^ { \prime \prime }$ , devtype $! =$ "elog",
ts=1675662554000, $\mathsf { e l o g } = \{ \mathsf { C g } \ y = { } ^ { \prime \prime } \mathsf { S } \ y \mathsf { S } ^ { \prime \prime }$
,cls ${ } _ { 1 } = { }$ "open", $\vert v \vert = 0$ , info="1", obj="ep/2711/m/P1", Ic="
A3QAAABmAFAGRzczXXXXXX/me/ep/2765[1]"}

# KeyPad 认证失败

elog字段定义:

• cgy="nty",   
• cls $=$ "fail",, $\vert v \vert = 2$ ,   
• info $^ { 1 = }$ "EAF",   
•obj $\left| = \prime \prime \right.$ 请求的操作",例如“disarm", $\vert c = ^ { \prime \prime }$ 发起认证的设备"

示例：userid $\mid =$ '7722454", agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog",, ts=1675662554000, elog $=$ (cgy $^ { \prime } { = }$ "nty", cls $: = :$ "
fail",, $\vert v \vert = 2$ , info $| \mathop { = }$ 'EAF", obj $=$ "disarm", $\mid { \mathsf { c } } =$ "
A3QAAABmAFAGRzczXXXXXX/me/ep/2765"}

# KeyPad 认证无权限

elog字段定义:

• cgy="nty",   
• cls $=$ "fail",, $\vert v \vert = 2$ ,   
• info $^ { 1 = }$ "ENP:8"，8指示请求的户ID是8   
• obj $\left| = \prime \prime \right.$ 请求的操作",例如“disarm", $\vert c = ^ { \prime \prime }$ 发起认证的设备"

示例：userid $\left| = \right|$ '7722454", agt="
A3QAAABmAFAGRzczXXXXXX'", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $\mid = \cdot$ (cgy $\mathit { \Theta } =$ "nty", cls $: = :$ "
fail", lv $^ { \circ 2 }$ , info $| \mathop { = }$ "ENP ${ \pmb 8 } ^ { \prime \prime }$ , obj="
disarm", $\ l { 1 c = }$ 'A3QAAABmAFAGRzczXXXXXX/me/ep/2765"}

# elog字段定义:

• cgy="nty",  
• cls $=$ "fai",,$\vert v \vert = 2$ ,  
•info $| \ b = \ b ^ { - 1 }$ "OK:2,ENP:8"，请求的用户ID分别为2和8，其中2成功，8没有权限  
•obj $= ^ { \prime \prime }$ 请求的操作",例如“disarm",$\vert c = ^ { \prime \prime }$ 发起认证的设备"

示例：userid="7722454", agt $\cdot =$ "
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $=$ [cgy $" =$ "nty", cls $: = :$ "fail,, $\vert v \vert = 2$ ,
info $| = \prime \prime$ OK:2,ENP:8", obj="disarm", $\ l { 1 c = }$ "A3QAAABmAFAGRzczXXXXXX/me/ep/2765"}

# KeyPad 管理认证失败

elog字段定义:

•cgy $\mathit { \Theta } =$ "nty",   
• cls ${ } = { }$ "fai",, $\vert v \vert = 2$ ,   
• info $^ { 1 = }$ "EAF"   
• obj="auth[admin]",   
. $\vert c = ^ { \prime \prime }$ 发起认证的设备"

示例：userid $\mid =$ "7722454", agt $\cdot =$ "
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $=$ (cgy $" =$ "nty", cls ${ } _ { 1 } = { }$ "
fail",, $\vert v \vert = 2$ info $| \mathop { = }$ 'EAF", obj="auth[admin]", $\ l { 1 c = }$ "
A3QAAABmAFAGRzczXXXXXX/me/ep/2765"}

# KeyPad 管理认证成功

elog字段定义:

${ \mathsf { c g y } } = " { \mathsf { s y s } } " $ ,  
• cls $u = \prime$ 'auth[admin]",$\vert v \vert = 0$ ,  
• info $| = " 0 "$ ,  
•obj="用户ld,  
. $\vert c = ^ { \prime \prime }$ 发起认证的设备"

示例：userid $\mid =$ '7722454", agt=-"
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $\mid =$ {cgy="sys", cls ${ } _ { 1 } = { }$ '
auth[admin]", $\vert v \vert = 0$ , info $| = " 0 "$ $\mathsf { o b j } = \prime \prime 8 ^ { \prime \prime }$ , lc="
A3QAAABmAFAGRzczXXXXXX/me/ep/2765"}

# KeyPad 输入错误锁定

elog字段定义：

• cgy="nty",   
•cls $= ^ { I }$ "errlock", $\vert v \vert = 2$ ,   
• info $^ { 1 = }$ 锁定的时长，单位是秒   
• obj=", $\vert c = ^ { \prime \prime }$ 发起操作的设备"

示例：userid $\mid =$ '7722454", agt $\cdot =$ "
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i d } \mathsf { x } = " \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", ts=1675662554000, elog $\mid =$ {cgy $^ { \prime } { = }$ "nty", cs ${ } _ { 1 } = { }$ "
errlock", Iv $^ { \circ 2 }$ , info $\mathbf { \mu } = \mathbf { \ " { 3 0 } \prime \prime }$ , Obj=", $\vert c =$ '
A3QAAABmAFAGRzczXXXXXX/me/ep/2765"}

# KeyPad 输入错误解锁

elog字段定义:${ \mathsf { c g y } } = " { \mathsf { s y s } } " $ • cls ${ } = { }$ "errlock",$\vert v \vert = 0$ ,•
info $| = " 0 "$ • obj=",$\vert c = ^ { \prime \prime }$ 发起操作的设备"

示例：userid $\mid =$ "7722454", agt="
A3QAAABmAFAGRzczXXXXXX", $\mathrm { i } \mathrm { d } \mathsf { X } = \mathsf { \Omega } ^ { \prime \prime } \mathsf { S } ^ { \prime \prime }$ ,
devtype $^ { \ast = }$ "elog", t5 ${ } _ { 1 } = { }$ 1675662554000, elog $=$ {cgy="sys", cls ${ } _ { 1 } = { }$ "
errlock", Iv $\mathtt { \mathtt { = 0 } }$ , info $| = " 0 "$ ,
Obj=", $\mathbf { \bar { C } } \mathbf { = } ^ { \prime \prime } \mathbf { \bar { A } } 3$
QAAABmAFAGRzczXXXXXX/me/ep/2765"}

![](images/701230270831984a630a86f657693efbb9fbd319920e3d59c960b16e033c33de.jpg)

# 8.智能应用用户API

(此类接口有限开放，非企业级用户以及没用此需求的不建议使用)

# 8.1.注册用户

如果用户没有LifeSmart账号，第三方应用可以通过此接口创建用户，并自动授权。  
Note:若第三方应用无此权限，则此接口不能使用。

# 8.1.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">RegisterUser</td><td></td><td>用户注册</td></tr><tr><td>Partial URL</td><td colspan="2">auth.RegisterUser</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="10"></td><td rowspan="5"></td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>UserID,固定&quot;10001&quot;</td></tr><tr><td>appkey time</td><td>Y Y</td><td>appkey</td></tr><tr><td>method</td><td></td><td></td><td>UTC时间戳，自1970年1月1日起 计算的时 间,单位为秒</td></tr><tr><td rowspan="5"></td><td>email</td><td>Y</td><td>Registeruser Email，与手机号二选一</td></tr><tr><td>mobile</td><td>。</td><td>手机号，与email二选一</td></tr><tr><td>pwd</td><td>Y</td><td></td></tr><tr><td>nick</td><td>0</td><td>密码</td></tr><tr><td></td><td></td><td>昵称</td></tr><tr><td>id</td><td>rgn</td><td>Y</td><td>用户所在区域 消息id号</td></tr></table>

Note:

rgn为开发者根据实际需求需要填写的参数，表示注册用户所处区域，即所在国家或区域。原则上不可不填写，若不填即默认为中国大陆区(
cn），其它区域参照附录1，rgn填写为国际域名缩写。

RegisterUser方法不涉及对已有用户的操作，故其userid和usertoken使用默认值userid="10001",usertoken="10001". -

RegisterUser的接口请求地址，开发者需要根据传入的rgn找到对应的svrrgnid来使用该方法，参照 附录1 和附录2。

# 8.1.2.范例

• 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

⚫ 请求地址：

BaseURL $^ { + }$ PartialURL,

BaseURL的选择，可能与您申请的应用 appkey 所拥有的区域权限有关，若出现接口错误信息形如：“app not existed"，请检查调用接口使用的
appkey 所有的区域权限（该信息可在开放平台上进行查看）。并参考附录2服务代号及地址对应表调整请求的BaseURL。

BaseURL的选择：具体服务器地址可参照：附录2 服务代号及地址对应表

例如：

https://api.ilifesmart.com/app/auth.Registeruser

# • 请求信息：

"id": 963,   
"method":'"RegisterUser",   
"system":{ "ver": "i.0", "lang":"en", "userid": "10001", "appkey":"APPkEy_xxxxxxxx", "time"： 1447650170, "sign":"
SIGN_xxxxxxxx"   
}，   
"params": { "pwd":"password_xxx", "email":"d@d.com", "nick":"nickname_xxx"   
}

签名原始字符串：

method:Registeruser,email:d@d.com,nick:nickname_xxx,pwd:password_xxx ,time:1447650170,userid:10001,usertoken:
10001,appkey:APPkEY_xxxxxxxx ,apptoken:APPTOKEN xxxxxxxX

# • 回复信息：

"id":963, "code": 0, "userid": "10010", "usertoken":"xxxxxxxx" }

# 8.2.删除用户

第三方应用可以通过此接口删除已授权用户。

Note:

若第三方应用无此权限，则此接口不能使用，并且用户为已授权用户。

# 8.2.1.JSON请求数据格式

<table><tr><td>Type</td><td colspan="2">Definition</td><td>Must</td><td>Description</td></tr><tr><td>Interface Name</td><td colspan="2">UnregisterUser</td><td></td><td>解除用户授权</td></tr><tr><td>Partial URL</td><td colspan="2">auth.Unregisteruser</td><td></td><td></td></tr><tr><td>Content Type</td><td colspan="2">application/json</td><td></td><td></td></tr><tr><td>HTTP Method</td><td colspan="2">POST</td><td></td><td></td></tr><tr><td rowspan="8">Request Content</td><td rowspan="8">system</td><td>ver</td><td>Y</td><td>1.0</td></tr><tr><td>lang</td><td>Y</td><td>en</td></tr><tr><td>sign</td><td>Y</td><td>签名值</td></tr><tr><td>userid</td><td>Y</td><td>user id</td></tr><tr><td>appkey</td><td>Y</td><td>appkey</td></tr><tr><td>time</td><td>Y</td><td>UTC时间戳，自1970年1月1日 起 计算的时间,单位为秒</td></tr><tr><td>method</td><td>Y</td><td>UnregisterUser</td></tr><tr><td colspan="2">params</td><td></td><td></td></tr><tr><td colspan="3">id</td><td>Y</td><td>消息id号</td></tr></table>

# 8.2.2.范例

# • 我们假定：

appkey为APPKEY_XXXXXXXX，实际需要填写真实数据；  
apptoken为APPTOKEN_XXXXXXXX，实际需要填写真实数据；  
userid为USERID_XXXXXXXX，实际需要填写真实数据；  
usertoken为USERTOKEN_XXXXXXXX，实际需要填写真实数据；  
sign为SIGN_XXXXXXXX，实际需要填写真实签名数据；

• 请求地址：svrurl+PartialURL，例如：https://api.ilifesmart.com/app/auth.Unregisteruser

# ● 请求信息：

"id": 963,   
"method":'"unregisteruser",   
"system": { "yer": "1.0", "lang":"en", "userid":"usERID_xxxxxxxx", "appkey"："APPKEy_xxxxxxxx", "time"： 1447650170, "
sign":"SIGN_xxxxxxxx"   
}，   
"params": { }

签名原始字符串：

method:UnregisterUser,time:1447650170,userid:usERID_xxxxxxxx,usertok en:UsERToKEN_xxxxxxxx, appkey:
APPKEY_xxxxxxxx,apptoken:APPTokEN_xxxxx XXX

# • 回复信息：

{ "id": 963, "code": 0, "msg":"success" }

# 附录1国家域名缩写以及服务提供映射

<table><tr><td>国际域</td><td colspan="2">国家或地区</td><td>Countries and Regions</td><td>服务提供地</td><td>服务代号</td></tr><tr><td>ae</td><td colspan="2">阿拉伯联合酋长国</td><td>United Arab Emirates</td><td>America</td><td>AME</td></tr><tr><td>ag</td><td colspan="2">安提瓜和巴布达</td><td>Antigua and Barbuda</td><td>America</td><td>AME</td></tr><tr><td>am</td><td colspan="2">亚美尼亚</td><td>Armenia</td><td>Europe</td><td>EUR</td></tr><tr><td>apz</td><td colspan="2">亚太地区</td><td>Asia Pacific</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>ar</td><td colspan="2">阿根廷</td><td>Argentina</td><td>America</td><td>AME</td></tr><tr><td>at</td><td colspan="2">奥地利</td><td>Austria</td><td>Europe</td><td>EUR</td></tr><tr><td>au</td><td colspan="2">澳大利亚</td><td>Australia</td><td>America</td><td>AME</td></tr><tr><td>bb</td><td colspan="2">巴巴多斯</td><td>Barbados</td><td>America</td><td>AME</td></tr><tr><td>bd</td><td colspan="2">孟加拉国</td><td>Bangladesh</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>be</td><td colspan="2">比利时</td><td>Belgium</td><td>Europe</td><td>EUR</td></tr><tr><td>bg</td><td colspan="2">保加利亚</td><td>Bulgari</td><td>Europe</td><td>EUR</td></tr><tr><td>bh</td><td colspan="2">巴林</td><td>Bahrain</td><td>America</td><td>AME</td></tr><tr><td>bn</td><td colspan="2">文莱</td><td>Brunei</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>bo</td><td colspan="2">玻利维亚</td><td>Bolivia</td><td>America</td><td>AME</td></tr><tr><td>br</td><td colspan="2">巴西</td><td>Brazil</td><td>America</td><td>AME</td></tr><tr><td>bs</td><td colspan="2">巴哈马</td><td>Bahamas</td><td>America</td><td>AME</td></tr><tr><td>by</td><td colspan="2">白俄罗斯</td><td>Belarus</td><td>Europe</td><td>EUR</td></tr><tr><td>bz</td><td colspan="2">伯利兹</td><td>Belize</td><td>America</td><td>AME</td></tr><tr><td>ca</td><td colspan="2">加拿大</td><td>canada</td><td>America</td><td>AME</td></tr><tr><td>ch</td><td colspan="2">瑞士 - -</td><td>Switzerland</td><td>Europe</td><td>EUR</td></tr><tr><td>cl</td><td colspan="2"></td><td>Chile</td><td></td><td>AME</td></tr><tr><td></td><td colspan="2">智利</td><td>China</td><td>America China (old)</td><td>CNO</td></tr><tr><td>cn</td><td colspan="2">中国（旧区）</td><td>Hotel and Corporate</td><td></td><td>IP1</td></tr><tr><td>cn1</td><td colspan="2">酒店和公司用户</td><td>users</td><td>China (special)</td><td></td></tr><tr><td>cn2</td><td colspan="2">中国(新区）</td><td>china</td><td>China (new)</td><td>CN2</td></tr><tr><td>co</td><td colspan="2">哥伦比亚</td><td>Colombia</td><td>America</td><td>AME</td></tr><tr><td>cr</td><td colspan="2">哥斯达黎加</td><td>Costa Rica</td><td>America</td><td>AME</td></tr><tr><td>cY</td><td colspan="2">塞浦路斯</td><td>Cyprus</td><td>Europe</td><td>EUR</td></tr></table>

<table><tr><td>CZ</td><td>捷克</td><td>Czech Republic</td><td>Europe</td><td>EUR</td></tr><tr><td>de</td><td>德国</td><td>Germany</td><td>Europe</td><td>EUR</td></tr><tr><td>dk</td><td>丹麦</td><td>Denmark</td><td>Europe</td><td>EUR</td></tr><tr><td>dm</td><td>多米尼克</td><td>Dominica</td><td>America</td><td>AME</td></tr><tr><td>do</td><td>多米尼加共和国</td><td>Dominica Rep</td><td>America</td><td>AME</td></tr><tr><td>dz</td><td>阿尔及利亚</td><td>Algeria</td><td>America</td><td>AME</td></tr><tr><td>ec</td><td>厄瓜尔多</td><td>Ecuador</td><td>America</td><td>AME</td></tr><tr><td>ee</td><td>爱沙尼亚</td><td>Estonia</td><td>Europe</td><td>EUR</td></tr><tr><td>eg</td><td>埃及</td><td>Egypt</td><td>America</td><td>AME</td></tr><tr><td>es</td><td>西班牙</td><td>Spain</td><td>Europe</td><td>EUR</td></tr><tr><td>et</td><td>埃塞俄比亚</td><td>Ethiopia</td><td>America</td><td>AME</td></tr><tr><td>fi</td><td>芬兰</td><td>Finland</td><td>Europe</td><td>EUR</td></tr><tr><td>fr</td><td>法国</td><td>France</td><td>Europe</td><td>EUR</td></tr><tr><td>gb</td><td>英国</td><td>United Kingdom</td><td>Europe</td><td>EUR</td></tr><tr><td>gd</td><td>格林纳达</td><td>Grenada</td><td>America</td><td>AME</td></tr><tr><td>gh</td><td>加纳</td><td>Ghana</td><td>America</td><td>AME</td></tr><tr><td>gr</td><td>希腊</td><td>Greece</td><td>Europe</td><td>EUR</td></tr><tr><td>gt</td><td>危地马拉</td><td>Guatemala</td><td>America</td><td>AME</td></tr><tr><td>gy</td><td>圭亚那</td><td>Guyana</td><td>America</td><td>AME</td></tr><tr><td>hk</td><td>中国香港</td><td>China. HongKong</td><td>America</td><td>AME</td></tr><tr><td>hn</td><td>洪都拉斯</td><td>Honduras</td><td>America</td><td>AME</td></tr><tr><td>hr</td><td>克罗地亚</td><td>Croatia</td><td>Europe</td><td>EUR</td></tr><tr><td>hu</td><td>匈牙利 -</td><td>Hungary</td><td>Europe</td><td>EUR</td></tr><tr><td>id</td><td>印度尼西亚</td><td>Indonesia</td><td>America</td><td>AME</td></tr><tr><td>ie</td><td>爱尔兰</td><td>Ireland</td><td>Europe</td><td>EUR</td></tr><tr><td>i1</td><td>以色列</td><td>Israel</td><td>America</td><td>AME</td></tr><tr><td>in</td><td>印度</td><td>India</td><td>America</td><td>AME</td></tr><tr><td>iq</td><td>伊拉克</td><td>Republic Of Iraq</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>ir</td><td>伊朗</td><td>Iran</td><td>America</td><td>AME</td></tr><tr><td>is</td><td>冰岛</td><td>Iceland</td><td>Europe</td><td>EUR</td></tr><tr><td>it</td><td>意大利</td><td>taly</td><td>Europe</td><td>EUR</td></tr></table>

<table><tr><td colspan="6"></td></tr><tr><td>jm</td><td>牙买加</td><td>Jamaica</td><td>America</td><td>AME</td><td></td></tr><tr><td>jo</td><td>约旦</td><td>Jordan</td><td>America</td><td>AME</td><td></td></tr><tr><td>jp</td><td>日本</td><td>Japan</td><td>America</td><td></td><td>AME</td></tr><tr><td>ke</td><td>肯尼亚</td><td>Kenya</td><td>America</td><td>AME</td><td></td></tr><tr><td>kh</td><td>柬埔寨</td><td>Cambodia</td><td>America</td><td>AME</td><td></td></tr><tr><td>kr</td><td>韩国</td><td>Korea</td><td>America</td><td>AME -</td><td></td></tr><tr><td>kw</td><td>科威特</td><td>Kuwait</td><td>America</td><td>AME</td><td></td></tr><tr><td>kz</td><td>哈萨克斯坦</td><td>Kazakhstan</td><td>Asia Pacific</td><td>APZ</td><td></td></tr><tr><td>1c</td><td>圣卢西亚</td><td>st.Lucia</td><td>America</td><td>AME</td><td></td></tr><tr><td>1i</td><td>列士敦士登</td><td>Liechtenstein</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>1k</td><td>斯里兰卡</td><td>Sri Lanka</td><td>AsiaPacific</td><td></td><td>APZ</td></tr><tr><td>1t</td><td>立陶宛</td><td>Lithuania</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>1u</td><td>卢森堡</td><td>Luxembourg</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>1v</td><td>拉脱维亚</td><td>Latvia</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>ma</td><td>摩洛哥</td><td>Morocco</td><td>America</td><td></td><td>AME</td></tr><tr><td>md</td><td>摩尔多瓦</td><td>Moldova, Republic of</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>me</td><td>黑山共和国</td><td>Montenegro</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td></td><td></td><td>Macca</td><td></td><td></td><td></td></tr><tr><td></td><td>马其顿</td><td></td><td>Buia Pacific</td><td></td><td></td></tr><tr><td>mn</td><td>蒙古</td><td>Mongolia</td><td>Asia Pacific</td><td></td><td>APZ</td></tr><tr><td>mo</td><td>中国澳门</td><td>China. Macao</td><td>America</td><td></td><td>AME</td></tr><tr><td>mt</td><td>马耳他</td><td>Malta</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>mu</td><td>毛里求斯</td><td>Mauritius</td><td>America</td><td></td><td>AME</td></tr><tr><td>mx</td><td>墨西哥</td><td>Mexico</td><td>America</td><td></td><td>AME</td></tr><tr><td>my</td><td>马来西亚</td><td>Malaysia</td><td>Asia Pacific</td><td></td><td>APZ</td></tr><tr><td>ng</td><td>尼日利亚</td><td></td><td>America</td><td></td><td>AME</td></tr><tr><td>ni</td><td>尼加拉瓜</td><td>Nicaragua</td><td>America</td><td></td><td>AME</td></tr><tr><td>n1</td><td>荷兰</td><td>Netherlands</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>no</td><td>挪威</td><td>Norway</td><td>Europe</td><td></td><td>EUR</td></tr><tr><td>np</td><td>尼泊尔</td><td>Nepal</td><td>Asia Pacific</td><td></td><td>APZ</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>nz</td><td>新西兰</td><td>New Zealand</td><td>America</td><td></td><td>AME</td></tr></table>

<table><tr><td>om</td><td>阿曼</td><td>oman</td><td>America</td><td>AME</td></tr><tr><td>pa</td><td>巴拿马</td><td>Panama</td><td>America</td><td>AME</td></tr><tr><td>pe</td><td>秘鲁</td><td>Peru</td><td>America</td><td>AME</td></tr><tr><td>ph</td><td>菲律宾</td><td>Philippines</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>pk</td><td>巴基斯坦</td><td>Pakistan</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td></td><td>波兰</td><td>Poland</td><td>Europe</td><td>EUR</td></tr><tr><td>pt</td><td>葡萄牙</td><td>Portugal</td><td>Europe</td><td>EUR</td></tr><tr><td></td><td>巴拉圭</td><td>Paraguay</td><td>America</td><td>AME</td></tr><tr><td>qa</td><td>卡塔尔</td><td>Qatar</td><td>America</td><td>AME</td></tr><tr><td>ro</td><td>罗马尼亚</td><td>Romania</td><td>Europe</td><td>EUR</td></tr><tr><td>rs</td><td>塞尔维亚</td><td>Serbia</td><td>Europe</td><td>EUR</td></tr><tr><td>ru</td><td>俄罗斯</td><td>Russia</td><td>Europe</td><td>EUR</td></tr><tr><td>sa</td><td>沙特阿拉伯</td><td>Saudi Arabia</td><td>America</td><td>AME</td></tr><tr><td>se</td><td>瑞典</td><td>Sweden</td><td>Europe</td><td>EUR</td></tr><tr><td>sg</td><td>新加坡</td><td>singapore</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>si</td><td>斯洛文尼亚</td><td>slovenia</td><td>Europe</td><td>EUR</td></tr><tr><td>sk</td><td>斯洛伐克</td><td>slovakia</td><td>Europe</td><td>EUR</td></tr><tr><td>sr</td><td>苏里南</td><td>Suriname</td><td>America</td><td>AME</td></tr><tr><td></td><td>萨尔瓦多</td><td>EI Salvador</td><td>America</td><td>AME</td></tr><tr><td>th</td><td>泰国</td><td>Thailand</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>tr</td><td>土耳其</td><td>Turkey</td><td>Europe</td><td>EUR</td></tr><tr><td></td><td>特立尼达和多巴哥</td><td>Trinidad and Tobago</td><td>America</td><td>AME</td></tr><tr><td>tw</td><td>中国台湾省</td><td>China. Taiwan</td><td>America</td><td>AME</td></tr><tr><td>ua</td><td>乌克兰</td><td>ukraine</td><td>Europe</td><td>EUR</td></tr><tr><td>us</td><td>美国</td><td>United states of America</td><td>America</td><td>AME</td></tr><tr><td>uy</td><td>乌拉圭</td><td>Uruguay</td><td>America</td><td>AME</td></tr><tr><td>ve</td><td>委内瑞拉</td><td>venezuela</td><td>America</td><td>AME</td></tr><tr><td>vn</td><td>越南</td><td>vietnam</td><td>Asia Pacific</td><td>APZ</td></tr><tr><td>za</td><td>南非</td><td>South Africa</td><td>America</td><td>AME</td></tr></table>

# 附录2服务代号及地址对应表

<table><tr><td></td><td>service Typesvrrgnid</td><td>URL</td></tr><tr><td rowspan="8">OpenAPI URL</td><td>GS</td><td>https://api.ilifesmart.com/app/</td></tr><tr><td>CNO</td><td>https://api.cn0.ilifesmart.com/app/</td></tr><tr><td>VIP1</td><td>https://api.cnl.ilifesmart.com/app/</td></tr><tr><td>CN2</td><td>https://api.cn2.ilifesmart.com/app/</td></tr><tr><td>AME</td><td>https://api.us.ilifesmart.com/app/</td></tr><tr><td>EUROPE</td><td>https://api.eur.ilifesmart.com/app/</td></tr><tr><td>JAP</td><td>https://api.jp.ilifesmart.com/app/</td></tr><tr><td>APZ</td><td>https://api.apz.ilifesmart.com/app/</td></tr></table>