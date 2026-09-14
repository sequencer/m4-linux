# 原生启动失败取证：panicmedic（2026-09-14）

## 实机重复读回的状态

用户屏幕仍为 support.apple.com/mac/restore。本轮直接查询固定主ECID的1281 Recovery，未重复完整Revive。01:22、01:25、01:27多次原始USB查询取得一致状态：

| 键 | 值 |
| --- | --- |
| boot-stage | 1 |
| build-version | mBoot-18000.161.10 |
| auto-boot | true |
| boot-command | recover-system |
| iboot-failure-reason | 0x3 |
| recovery-reason | 0x3 |
| recovery-boot-mode | panicmedic |
| panicmedic-engaged | 0x1 |
| panicmedic-auxkc-present | false |
| boot-volume | EF57347C-0000-AA11-AA11-00306543ECAC:47EB0117-9289-A34C-8E19-2648BB3E2BCD:DE77783E-D9C0-4695-8BE1-EBE0D3015748 |
| iboot-failure-volume | 与boot-volume相同 |

最后一个UUID为已知实验启动卷组M4 Linux Bootstrap。卷字符串格式为GPT类型UUID、GPT分区UUID、APFS卷组UUID；格式参考[Asahi NVRAM文档](https://asahilinux.org/docs/fw/nvram/)。当前默认启动卷和记录的失败卷均是stub，不应将失败对象误报为原Macintosh HD。此为记录的失败上下文，不证明原系统、SFR或存储硬件均正常。

`iboot-failure-reason-str`、panic计数及timestamps查询返回PIPE，没有取得文字解释或计数。**0x3的枚举含义尚未解码**，不能直接命名为SSV、LocalPolicy或存储错误。guest曾发生panic是背景，但尚未证明guest写入panicmedic标记的具体路径。

证据目录均在忽略的raw内：`iboot-20260914-failure-1`、`iboot-20260914-panicmedic-details-1`、`iboot-20260914-after-fallback-refusal-1`；每个manifest记录发送和接收字节数，不以API状态0代替传输验收。

## 临时加载的真实失败点

更新诊断包后，01:19:56发送3045字节签名LocalPolicy，随后的`lpolrestore`命令返回**libusb PIPE -9**，预期发送12字节。加载84385退出1，未继续到Stage1固件、iBEC或restored，也没有StartRestore。

这证明此次失败早于iBEC；旧库忽略命令控制传输错误，导致此前仍显示后续准备并最终报iBEC超时。PIPE本身不证明签名验证失败、Local boot权限拒绝或具体安全策略原因。之后只读查询仍auto-boottrue、nonce不变。此次没有执行关闭自动启动的命令。

Nix诊断包新增--no-restore路径跳过saveenv，避免未来加载失败又持久化auto-bootfalse；该措施不等于整个加载零写入。旧完整Revive工具保持不变。

## 启动路径的离线分析与写入尝试

从固定Apple25G83资源，用Nix ipsw解压：

| 产物 | SHA256 |
| --- | --- |
| raw/ibss-25G83-diagnostic.bin | 4f341a37e5e0c86021f9ef38ef25216a19b53ff69b5b2d353fe7af2a68e0c443 |
| raw/ibec-25G83-diagnostic.bin | d7b4b66b3fea1e93b7728442f6fcc033d5dd99e366cbf874b20db9046453815f |

iBSS包含lpolrestore命令字符串0x2912dd，不能因PIPE断言根本没有该命令。以下offset均为上述iBSS文件offset，独立只读分析取得：

- 0xf8db0读取one-time-boot-command，0xf8dd4非空优先返回；否则0xf8dd8读取持久boot-command。
- 启动入口0x2e54经0xf8de4/0xf8db0选命令，0x2e84查询分发表。
- recover-fallback表项0x198a00，字符串0x290c06，handler0xce8，表项+0x30值4。
- 0x2f04调用0xf9180，0xf91c4删除一次性变量、0xf91c8保存；随后可能先被0x110af8检查阻止，0x2f48才调用handler。

只针对校验过的本机Stage1、auto-boottrue、recover-system、panicmedic、失败卷为Bootstrap的状态尝试恢复启动路径，未清panic记录或改卷组：

| 尝试 | 实际结果 | 后续动作 |
| --- | --- | --- |
| setenv one-time-boot-command recover-fallback | PIPE -9，预期46字节 | 停止；未saveenv/reboot |
| setenv boot-command recover-fallback | PIPE -9，预期37字节 | 停止；未saveenv/reboot |

证据为`raw/iboot-20260914-fallback-request-1`及`raw/iboot-20260914-persistent-fallback-request-1`。脚本非零退出；某次外层tail返回0不能作为脚本成功证据。后验仍boot-commandrecover-system、auto-boottrue、同一Bootstrap失败卷，未成功切换到fallback。没有Erase/StartRestore或分区修改；不将上传到RAM的LPOL描述为已修改磁盘LocalPolicy。

## 下一步与被动记录

软件变量切换被接口拒绝，下一步需要物理启动请求，而不是再次DFU盲刷。官方[Apple silicon启动模式](https://support.apple.com/en-gb/guide/security/sec10869885b/web)规定，从关机状态双按电源、第二次保持按下进入fallback recoveryOS。这次前置条件已确认auto-boottrue；不能保证已有恢复资源故障不会继续阻止启动。

01:29启动过600秒`udevadm monitor --kernel --property --subsystem-match=usb`，会话80892，输出`raw/fallback-20260914-passive-usb.log`。用户02:59反馈时它已经过期，只有头部，不能据此判断最近操作。它不打开设备接口或发送控制命令，不与恢复启动竞争配置。Recovery SSH辅助脚本HTTP实测200：`http://172.25.27.108:8000/ssh.sh`。如果进入Recovery GUI，先不要安装或抹盘，再启动已有辅助SSH做策略/缓存检查；fallback GUI并不代表实验guest GUI目标完成。

依赖新增binutils到固定Nix开发环境；诊断包Nix构建、脚本AST检查、git diff --check均通过。原Data在这轮没有挂载或逐文件验收，不能宣称其完整性已重新确认。

## 02:59备用Recovery失败后的新实测

用户明确反馈备用Recovery也不能进入。没有再让用户重按fallback，没有完整Revive、Erase或StartRestore。

- 起初主机没有可连接Apple设备，irecovery无法连接；该时刻不能读NVRAM。随后看到1281，本轮非root首次打开返回-3，root重试才获得完整传输记录；单个打开失败不能代替整个启动阶段判断。
- 03:02:39 root只读查询取得boot-stage1、auto-boottrue、boot-commandrecover-system、boot-volume仍为Bootstrap、recovery-boot-modepanicmedic、panicmedic-engaged0x1、recovery-reason0x3。**iboot-failure-reason/volume/str这次均PIPE**，不能将01:22旧值冒充本次读回。证据`raw/iboot-20260914-after-physical-fallback-2/manifest.json`。
- 03:06:44新增getenv boot-device，发送19字节、接收11字节，值nvme_nand0；当前变量非空，不证明设备打开或内容检查成功。证据`raw/iboot-20260914-boot-device-query-1/manifest.json`。
- 本次控制台读取成功调用但无新文本；空缓存不是启动成功或无错误的证明。证据`raw/iboot-20260914-fallback-console-1`。
- 内核在02:59捕获NCM注册、短暂断开及ATCPHY pipehandler lock失败。新120秒sysfs观察于03:03:08–03:05:08运行，03:04:02、03:04:26、03:04:48均观察05ac:1905、product=Mac、匹配本机序列号，再次断开。三次restored只读查询均idevice_new=-3，未取得HardwareInfo/SavedDebugInfo。证据`raw/fallback-20260914-mode-and-service-watch.log`、`raw/fallback-20260914-ncm-query-{1,2,3}.stdout`、`raw/fallback-20260914-host-kernel.log`。主机总线重建与目标OS重启需要独立对照，不能直接定因。

## 更深入的固定iBSS只读解码

以下均属于此前哈希锁定的Apple25G83 raw iBSS，指针基址0x1fc080000，地址为文件offset；**不是已验证的当前nativeStage1在线地址或命中路径**。

| 路径 | 可复核指令/地址 | 已确认边界 |
| --- | --- | --- |
| handler前检查 | 0x2f18调用0x110af8，0x2f1c非零跳0x2f50；0x2f48才call handler | 检查可以先阻止fallback |
| boot-device | 0x11026c，字符串0x285ae5；0x110b3c空值路径跳0x110dac返回-1 | 本机新查询非空，不能声称当前卡在空值分支 |
| recovery资源共用 | 0x110c20–0x110c30将fallback模式4与recover-system模式8分到同一路；0x110cb4调用0x111590，使用/recovery字符串0x28ac26 | 备用启动不是绕过所有恢复资源检查 |
| 共用handler及LPOL | fsboot/recover/recover-fallback/recover-system均handler0xce8；0xd90调用0xbcc，使用/lpol字符串0x285ac9，再调用0x11085c、成功后0x23764 | 具体卷、操作、签名错误尚未解码 |
| reason3 setter | 0x2368c mov w0,#3，0x23690 call0x240d0，0x2369c call0xff010；来自0x23628或0x23670调用0x2455c(0x99,0)失败 | 编号0x99确认为rpnh，有两份记录获取/长度/内容比较；实际值及native命中分支未知，不能唯一断言为rpnh不匹配或SSV/NSIH错误 |
| 首次错误锁存 | 0xff050–0xff060已有错误且w5 bit0为0时跳过更新 | reason3可能是旧上下文，不一定代表最近fallback失败 |
| lpolrestore Local/Remote | 表项0x199a60、handler0x23944；0x23980调用0x28d7c，bit0为0拒绝并返回-3；banner0x271c调用同一谓词，0x2734选择Remote/Local字符串0x285d01/0x285d08 | 固定iBSS的handler拒绝Local、允许Remote继续；USB PIPE不能等同handler返回-3 |

复核命令例：

```sh
nix develop --command objdump -D -b binary -m aarch64 --start-address=0x23944 --stop-address=0x239d4 experiments/2026-09-13-iokit-ram-root/raw/ibss-25G83-diagnostic.bin
```

03:13进一步完成0x99语义解析并独立复核：0x24adc构造w0低半0x6e68，0x24ae0高半0x7270，组合FOURCC为rpnh；0x24ae8设置w2=0x99。nsih/coih分别对应0x9b/0x9f，不是0x99。两份记录的预期值路径为0x243ec→0x241ac→0x176d4，选择器0，取SEP client协议响应的首0x30字节；另一份由0x101d34读取当前boot结构记录，其生产路径为LocalPolicy rpnh属性解析0x247f4→0x24df4→0x101b98。SEP内部如何生成和存储此值、两份本机实际值、检查是否适用于当前native模式仍未验收。取值失败、长度不同或内容不同都可令比较函数非零，不能仅凭reason3宣布哈希不匹配。

Apple对[LocalPolicy字段的定义](https://support.apple.com/en-gb/guide/security/secc745a0845/web)将rpnh称为RemotePolicy Nonce Hash，48字节，与Find My远程策略变化相关。这里的RemotePolicy不应混同iBSS Local/Remote boot来源谓词；也不是此前TSS ApNonce更换重签补丁已经修好的证明。没有更改Find My、Activation Lock、SEP nonce或清理iSC。boot-device getter的0x110294→0xfddf0→0xfdda4→0xfeb6c读取同名iBoot env，getenv handler0xfe79c共用该字典及查找函数但flags不同；不能据此认定值必定来自持久NVRAM。

03:15补充rpnh检查门控，避免误套用：0x23590先验证boot结构字段，0x235fc调用0x102c80并在0x23600检查bit0；该函数验证hobc结构并要求运行时类型不等于hobc，Local/Remote对应关系未知。0x23628检查分类编号1/2/9/11/13（mask0x2a06），0x23670分类3/14（mask0x4008）；分类4/8转去0x9a检查。这里的编号来自0x103130运行时字节或0x23550指定11，**尚未确定枚举语义，不能当作前述boot-command模式编号**。直接调用0x2355c→0x23590未见已辨认的显式Remote判断；不能说rpnh检查Remote专属，也不能说当前Local启动必经此setter。当前启动根因仍需实机Remote临时环境与磁盘策略/资源的独立取证。

## 新诊断路径：只从DFU加载Remote iBSS

撤回此前从native Stage1 Recovery复用DFU准备的goto。最新firmware-diagnostic-tools在初始macOS Recovery加--no-restore时明确拒绝，而不是再次尝试Local状态的lpolrestore。它仍保留原主ECID、Customer Upgrade/Update、禁止Erase守卫及诊断路径不saveenv。

此前Remote iBSS实际执行，但工具报没有disconnect，存在可检验的KIS外层/内部模式不同步假设：[固定libirecovery源](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/src/libirecovery.c)的设备add处理只在USB事件时读KIS内部模式，外层1881不变时可能漏掉变化；[固定idevicerestore源](https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/dfu.c)等待disconnect后才继续。**尚未证明这就是此前超时原因**。

新补丁仅在iBSS断开超时后重开固定主ECID，核对CPID/BDID/ECID后记录外层pid、内部mode、serial；内部已是Recovery时才读boot-stage。随后仍按原失败路径退出，未自动绕过模式检查或继续发送固件。Linux libirecovery的配置函数本来比较current值，不需要套用kisd的配置保留补丁。

Nix构建完成：`/nix/store/73q786l3xiqfn11d4mdhmv939ym3s0z2-idevicerestore-1.0.0-unstable-2026-09-07`；drv75fzww3py57q14cmnkc8m4s19ms64948。binary包含新refusal和probe字符串，也保留禁止Erase/非Update字符串。script AST、bash -n、git diff --check通过；wrapper在没有DFU时1秒负对照退出124，无上传。

`scripts/wait-for-dfu-diagnostics.sh`由Nix管理procps/util-linux依赖，独占flock，fresh ignored raw目录，固定store路径及工具SHA256，最多等待6小时、加载最多900秒且仅一次。Port DFU核对0x3fc75d711905dde9后以该端口ECID开始；Main DFU核对0xA10A426B9001C/8132/2c后以主ECID开始。transition后恢复工具原主ECID守卫再次校验。没有--erase/--no-input，失败不自动Revive/重试；--no-restore不发送StartRestore，不等于准备过程完全零写入（端口控制器固件及RAM加载仍可能发生）。

03:10:41启动等待会话64242、PID1101004，输出`raw/dfu-remote-stage1-20260914-standby-2/watcher.log`，截至03:11核对时等待中、尚无上传。首次nohup没有保持存活，不能算后台启动成功；第一版长期会话42706已停止143、无上传，修正Port ECID后才启动当前版本。等待只识别DFU候选，不在现有1281上反复执行Local加载。6小时期限之后必须重新检查进程，不假设无限后台工作。

需要的唯一物理操作是进入DFU，不再重复备用Recovery。保持M4 2025 Air远离MagSafe的前沿USB-C口；两机供电、其余USB配件移除。关机后短按并松开电源，立即同时按左Control、左Option、右Shift、电源10秒；松开前三键，继续电源最多10秒。目标应黑屏，Linux host以设备身份及日志验收，不期待Finder窗口。参见[Apple按键说明](https://support.apple.com/en-us/108900)、[Apple机型DFU端口表](https://support.apple.com/en-us/120694)。此次是临时环境取证，不再次完整Revive或Restore，不能保证现有启动故障会立即修好。原Data未挂载或重新逐文件核验；最终目标仍是guest GUI，未完成。

## 03:20本次DFU实测：Port成功，主芯片接力失败

03:20:28等待器实际识别Port DFU并核对本机ECID0x3fc75d711905dde9、CPID0022、BDID2c813200、Mac16,12/j713ap，自动开始一次临时加载。03:20:29.159取得Apple USBPortController1 ticket，创建并发送40555字节Ace3Binary；03:20:31.405收到端口设备disconnect。随后20秒没有主DFU接力，03:20:51.405报告Device did not reconnect in DFU mode / Port DFU failed，工具及64242等待会话均exit1。没有自动重试，PID1101004/idevicerestore1133119均已退出。新post-iBSS探针尚未触发，不能称已验收。

证据`raw/dfu-remote-stage1-20260914-standby-2/{device.txt,watcher.log,loader.log,loader.stdout,host-kernel.log}`。内核仅记录03:20:27端口设备、03:20:31断开，随后未见新的主设备；只读irecovery再次无法连接。此处还没有发送iBSS、LPOL、Stage1固件或iBEC，没有restored/StartRestore。不能说完全没有任何写入：已发送端口控制器固件；原Data未挂载或修改，未重新核验其完整性。

下一步只核对线口与接力，不重新完整Revive或无依据重按DFU。Port身份正确并不证明线在主DFU口，需核对M4端确为远离MagSafe的USB-C口；若不是，仅换口、不重启，观察是否恢复主设备枚举。若已经是正确口，需要据新的物理状态继续分析USB链路，不能直接认定插错。03:21另开1800秒udev被动监听，输出`raw/dfu-20260914-after-port-handoff-passive.log`，不打开控制接口或上传组件；超时后不假设持续监听。
