# Revive 后 iBootStage1 现场

## 拔插后 Recovery 控制通路恢复（22:46 UTC）

用户拔插后枚举05ac:1281，`raw/stage1-cable-replug-query.txt`初始主ECID及nonce匹配此前远程iBSS。irecovery shell62995有提示符；未启动仅识别1881的kisd。随后临时加载24128执行LocalPolicy/Stage1准备、boot-stage=1和iBEC上传，22:46:42仍未按预期断开，退出1，没有restored或StartRestore。记录`raw/temporary-restore-remote-stage1-replug.{log,stdout}`。文件名表示实验起点，不保证始终Remote boot：加载中ApNonce已变化，末次查询又变化，不能证明同一启动实例贯穿全程。

末次shell44355没有取得具体错误文本，已退出。此次未重复上传iBSS或完整Revive，没有Erase；准备阶段仍有saveenv。拔插解决了irecovery无法连接这一层，但没有解决iBEC启动。应确认实机屏幕及重启时序，不能据旧Memory image not valid断言此次相同原因。

## 提前监听取得 Remote boot 控制台（22:43 UTC）

`raw/physical-dfu-prelisten-console.txt`2394字节，SHA256 `056329a2f346c8ff62540d2abd7dcca23df46411a8d2cef68277a9ea32752574`。关键内容：

```text
Microkernel iBootStage1 for j713
Remote boot, Board 0x2c (j713ap)/Rev 0x4
BUILD_TAG: mBoot-18000.161.10
aborting autoboot due to remote boot
Entering iBootStage1 recovery mode, starting command prompt
```

主ECID也匹配本机。说明此次上传iBSS实际执行，不可根据恢复工具10秒等待失败认定镜像无效。当前只有远程Stage1，不是recoveryOS或guest GUI。DebugUSB存在，但恢复工具和kisd在过渡期出现接口占用，后续重复设置配置触发主机xHCI endpoint警告；此为控制连接问题线索，不能解释原生系统为何无法启动。

新增Nix `kisd-preserve-configuration`仅在当前配置不是1时设置配置。构建成功，22:45实测能Device opened，但UART仍I/O hardware fault or protocol violation；没有新串口内容。测试监听已停止，不循环重试，不自动复刷。下一步先拔插同一USB口重建端点状态，再重连仍存的远程Stage1。

## 物理 Port DFU 对照（22:39–22:40 UTC）

首次调用的主ECID筛选没有匹配端口ECID，发现阶段退出，未上传。改为先核对并指定本机端口ECID0x3fc75d711905dde9后，工具成功发送Ace3Binary、转入主DFU并通过主ECID/Update守卫。上游`irecv_event_cb`在Port DFU REMOVE时清空ECID，重新发现主芯片；并非去掉主身份安全检查。

会话12430上传iBSS后等待断开失败，22:40:20退出1，没有发送iBEC或StartRestore。随后USB枚举05ac:1881；kisd58441在22:40:24尝试配置时返回errno71，主机内核22:40:29记录设备断开。没有有效串口或SavedDebugInfo。详细证据保留在raw/temporary-restore-physical-dfu-2.log、raw/physical-dfu-debugusb-kisd.log和raw/physical-dfu-host-kernel.txt。单一kisd仍等待下一次枚举；配置错误与设备退出的因果关系未证明，不将其认定为原生启动失败根因。

## Stage1 临时加载对照（22:35 UTC）

未补齐Stage1准备的iBEC加载失败后，irecovery console曾返回`Memory image not valid`。这是临时加载失败证据，不足以解释原生系统为何无法启动。

`flake.nix`新增`firmware-diagnostic-tools`，保留主ECID/Update身份守卫，只在macOS Recovery的`--no-restore`路径复用现有DFU Stage1准备；`nix build .#firmware-diagnostic-tools -o results/firmware-diagnostic-tools`成功。该实验假设现场为此前观察的Stage1，不可泛用于未知Recovery阶段。

实机会话4688日志`raw/temporary-restore-stage1-prepared-2.log`显示`lpolrestore`、`iBoot boot-stage=1`和Stage1固件传输完成，随后iBEC上传后10秒没有断开，22:35:36退出1。没有进入restored，也没有发送StartRestore；准备阶段已`setenv auto-boot false`/`saveenv`，不属于零写入。只读后验保存于`raw/stage1-prepared-post-query.txt`，主ECID匹配且仍Recovery。shell88276已退出，无后台恢复加载进程。下一步需要真正的物理DFU入口来对照临时iBSS路径，不以重复完整Revive代替诊断。

用户确认普通/备用 Recovery 失败后仍显示 support.apple.com/mac/restore。

只读 USB/irecovery 查询：05ac:1281、MODE Recovery、CPID8132、BDID2c、ECID000A10A426B9001C、Mac16,12/j713ap。

PTY86750执行 irecovery -s，启动控制台输出如下关键字段：

```text
Microkernel iBootStage1 for j713
Local boot, Board 0x2c (j713ap)/Rev 0x4
BUILD_TAG: mBoot-18000.161.10
UUID: 5D9E84C0-9B7C-38CB-BCF6-52E7E7FF358E
BUILD_STYLE: RELEASE
Entering iBootStage1 recovery mode, starting command prompt
```

前置日志包含重复标识 `4fbf8fe65e3b7c6:2685`，另见 `:2743`、`:2767`；未解码，不将其解释为某个已知错误码。尝试读取 boot-command、boot-args、auto-boot 无有效输出。没有执行 setenv/saveenv/boot/reset；/exit只退出主机shell，退出码0。

本证据证明目标处于 iBootStage1 的固件恢复模式，不证明根因，也不证明用户数据损坏。AppleTCON恢复响应失败仍是待查线索，不能直接归因。Revive工具DONE与实际recoveryOS启动失败必须同时记录。

固定源 idevicerestore 的 debug_level 在每个 -d 参数累加，level>1才输出完整FirmwareUpdaterData请求。目前一次--debug日志不足以验证请求中的DeviceGeneratedTags/ResponseTags；如后续确有必要再次恢复，应使用双debug采集，而非原样重刷或无条件添加FirmwareData。

## 上游 manifest 路径修正对照

已通过GitHub API取得上游commit d9aa264b673fdd14fc0cb7f7daa1b9127ede4916（restore: honor requested global manifest path）。该变更修复SourceBootObjectV4忽略GlobalManifestPrefix/GlobalManifestSuffix、固定发送AP apticket的问题，不能仅凭标题将它认定为本机故障根因。

本次恢复日志未观察到GlobalManifestPrefix/GlobalManifestSuffix或__GlobalManifest__请求，记录的SourceBootObjectV4发送的是USB/Timer固件、BaseSystem及版本plist。目前不足以将manifest修正应用后重新刷写作为有证据的修复。上游API原始响应保存在ignored raw/global-manifest-commit.json；此次未修改恢复工具或重新刷写。
