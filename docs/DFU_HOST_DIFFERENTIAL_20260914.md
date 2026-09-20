# macOS 成功与 Linux iBSS 切换失败的差分路线

## 15:02 UTC：按授权关闭新 macOS 启动安全限制

目标仍为卷组2D4EFB69-013E-4618-997E-3AFDB3F1E2E5，配对1TR内以本轮sequencer所有者交互认证，执行：

```sh
csrutil disable
bputil -c -a -s -v 2D4EFB69-013E-4618-997E-3AFDB3F1E2E5
```

两者退出0。独立复读csrutil status、csrutil authenticated-root status、bputil -d，证据`raw/post-erase-recovery-145831/security-after.txt`：SIP disabled、Authenticated Root disabled、Permissive、sip0=7f、sip1/2/3=1，配对有效，coih absent。尚未重启，下一次启动应用这些设置；没有配置m1n1、修改分区或恢复旧策略。

这是关闭SIP/SSV/内核CTRR/启动参数过滤，并非关闭SEP/Boot ROM等所有安全机制；第三方kext/MDM授权位未另外开启。不将安全降级当作解决guest引发持久故障的措施。字段语义参考：https://support.apple.com/en-ca/guide/security/secc745a0845/web 。

## 14:58 UTC：新系统配对 Recovery 与所有者已实测

公钥 SSH 成功连接 root@172.24.5.124；只读证据保存在 `experiments/2026-09-14-reinstall-retained/raw/post-erase-recovery-145831/state.txt`。当前Recovery为26.6.2/25G83，硬件Mac16,12，bputil确认ECID匹配、one true recoveryOS、Paired、Pairing Integrity Valid。

- 当前主APFS容器 EFE517FC-C64B-426F-B6D7-6F3B5E368494，占据disk0s2约2TB；无Linux/bootstrap分区。disk0s1为524.3MB iSC，disk0s3为5.4GB系统Recovery。
- Macintosh HD System UUID为6F5A48AD-2B32-412B-9D52-1418371BEEF4；卷组UUID为2D4EFB69-013E-4618-997E-3AFDB3F1E2E5（亦为本轮Data UUID）。不要使用旧卷组742D07D7或stub530FE39B。
- .AppleSetupDone存在；本轮账户sequencer/UID501/UUID0A98877A-4388-469D-8D3C-99CDBAD24C43，diskutil确认Volume Owner Yes。无需重新安装系统或在Recovery制造账户。
- 当前Full Security，SIP/SSV/CTRR/启动参数过滤开启，coih absent；尚未安装m1n1。只读取系统状态和账户标识，未读密码凭据，未修改分区、安全策略、NVRAM或启动项。

这补充了账户配置和配对1TR实测，覆盖下方早期等待状态。备用Recovery和重复正常重启仍没有独立验收。

## 用户验收：本轮完整抹盘恢复成功

随后用户报告已进入新的 Recovery，补充本轮恢复后的 Recovery 图形入口验收；未确认是否备用 Recovery，不将两种模式均记为通过。主机随后枚举到05ac:1905，ssh.sh与临时host key下载服务HTTP200；这不是SSH连接或磁盘布局验收，新的UUID/所有者状态需连接后读取。

在告知 Erase 返回 DONE/exit0 并询问是否进入设置界面后，用户回复“成功了”。据此记录本轮恢复后启动成功，不再标为仅协议完成、原生结果未知。用户尚未单独报告完成账户配置、重复正常重启或两种 Recovery 验收，不将这些测试视为已完成。

本轮可用基线为 M1 Linux/Nix 主机、固定25G83完整IPSW、firmware-kis-trace-tools、显式 Customer Erase Install (IPSW)，具体日志见下节。先前 Upgrade 协议成功却未解决用户报告的故障，本轮 Erase 后用户确认成功；这不证明唯一损坏位置，也不证明三条日志改变是旧iBSS问题的根因修复。保持当前干净系统，不自动启动旧guest或恢复旧iSC/LocalPolicy。

## 14:49:48 UTC：本轮 Linux 完整 Erase 协议成功

`linux-dfu-erase-143802/result.txt` 为 `restore_exit=0`，控制台最终 `Status: Restore Finished` / `DONE`，日志结束时间14:49:48.809。自14:38:02开始约11分47秒。实际完成镜像恢复、Cryptex1 SystemOS（6174015488字节）、BaseSystem（1140850688字节）、固件/系统卷元数据发送、系统卷封印与卸载；不是仅 Port DFU 或 Revive 完成。

本轮 Erase 的 iBSS BOOT_IMG 同样完整回复 size4/status512，随后约1.66秒真实断开，iBEC与RestoreOS成功。没有绕过10秒等待或修改 Apple 固件。这使“本 M1 Linux host 无法做完整 Erase”不再成立，但尚不能解释此前失败、证明日志是修复，或宣布目标原生系统稳定。

14:50检查 idevicerestore、usbmon采集均已结束，锁已释放；USB仅root hubs，目标重启后图形状态需要用户验收。暂不重新安装 m1n1 或运行 guest。旧iSC/LocalPolicy/启动UUID不应套用本轮抹盘后的系统。

外层 exec 显示 exit1 是本机登录 shell `/etc/bash_logout` 在 `set -u` 下读取未定义 `__ETC_BASHLOGOUT_SOURCED`，发生在恢复结果已写为0且抓包正常清理之后；不要误报为 idevicerestore 失败。后续长任务用非 login shell避免这一宿主环境退出问题。日志中仍有可选USBPortController ticket警告，整体返回成功，不能单凭该行断言修复失败。

## 14:38 UTC：Upgrade 完成但原生失败，开始授权 Erase

上一轮 Upgrade 在 14:35:43.074 返回 Restore Finished / DONE，result.txt 记录 restore_exit=0。用户反馈仍然恢复错误、需要抹盘，随后再次进入 DFU。这里是“恢复协议完成但没有修好原生启动”，不是仍卡在 iBSS。日志有 `No 'USBPortController1,Ticket' in TSS response, this might not work`，整体随后完成；尚未证明它是原生失败根因。

14:37:20 首个 Erase 启动尝试被旧抓包持有的锁拒绝，没有上传。根因是 root 创建的 0600 usbmon.pid 对普通用户不可读，EXIT cleanup 无法取得 PID，随后 wait 卡住；实际 idevicerestore 已退出。核对进程树后只终止旧 usbmon cat PID1342799，释放锁，没有杀恢复任务。新一次由用户预建 pid 文件并让抓包关闭 fd9，修正本机清理问题；它不是目标 DFU 协议修复。

14:38:02 再次核对 Port DFU 的产品/CPID/BDID/ECID 后，实际启动单次 `firmware-kis-trace-tools --erase --variant 'Customer Erase Install (IPSW)'`，其余固件、cache、日志环境与本轮 Upgrade 相同。控制台已明确 `This restore will erase all device data.`。授权范围是 M4 内部系统/数据，不触碰 M1 备份。

新日志：`experiments/2026-09-14-reinstall-retained/raw/linux-dfu-erase-143802/`，会话91030，尚待结束和原生验收。失败不自动循环、不重放旧 iSC/LocalPolicy。

## 14:33 UTC：实机 Upgrade 已越过 iBSS，进入 RestoreOS

用户再次确认进入 DFU；实际初始为 Port DFU，CPID 0x0022 / BDID 0x2c813200 / ECID 0x3fc75d711905dde9，产品 Mac16,12 / j713ap。没有竞争恢复进程，取得既有 DFU 锁后进行一次显式 Upgrade，不是 Erase，也不是 --no-restore。

日志目录：`experiments/2026-09-14-reinstall-retained/raw/linux-dfu-upgrade-143305/`，含 device.txt、restore.log（root 私有）、restore.stdout、usbmon.txt；进程结束后写 result.txt 与 kernel.log。命令使用 `results/firmware-kis-trace-tools/bin/idevicerestore --ecid 0x3fc75d711905dde9 --variant 'Customer Upgrade Install (IPSW)' --plain-progress --debug --cache-path artifacts/apple/25G83/revive-cache --logfile <目录>/restore.log artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw`，环境 LIBIRECOVERY_DEBUG_LEVEL=1 / LIBUSB_DEBUG=4；无 --erase、--ignore-errors 或跳过模式等待。

- 14:33:09 Port DFU 接力成功，KIS 信息回报主芯片 ECID 000A10A426B9001C / CPID8132 / BDID2C。
- 14:33:13.105 发送 iBSS 1363655 字节；BOOT_IMG（portal16/index0x103）TX 16/16、RX 20/20、返回0，size4，**status512（0x200）**。
- 14:33:13.166 等待断开，14:33:14.892 收到断开并继续重连。kernel 同时确认实际 USB disconnect，不是跳过等待的假进展。
- 14:33:16.482 发送 iBEC 1153137 字节；随后成功进入 Recovery，发送恢复固件、ramdisk、SEP 与 kernelcache。
- 14:33:30.729 等待 RestoreOS；实际识别 `00008132-000A10A426B9001C`，读取 BoardID44 / ChipID33074 / UniqueChipID2833046977445916 并启动 Reverse Proxy，随后进入 NAND/FUD/固件更新步骤。

这次**证实 BOOT_IMG 的非零 status512 可伴随正常模式切换**。不能添加 `status != 0` 即拒绝的“修复”，也不能将所有 KIS status 共用一种错误解释。此前 rpl.size 异常仍返回成功的源码缺口，尚未在本次命中。

当前只证明越过旧失败点；Update 与历史 Erase 不同，日志改变时序，设备状态也已变化，没有严格 A/B，不能归因于这三条日志修好了协议。最终恢复退出状态与原生启动验收另记，不因开始更新就宣布 Mac 修复完成。

## 14:30 UTC：Linux 重试准备，尚无 DFU 设备

用户要求再次修复 Linux DFU 恢复。两次 `nix develop --command lsusb` 均仅有两个 Linux root hub，没有 Apple 设备；没有正在运行的 idevicerestore/kisd。没有上传固件或执行 Restore。

新增独立 Nix 输出 `dfu-kis-trace-tools` 与 `firmware-kis-trace-tools`，从原始 pkgs.libirecovery / pkgs.idevicerestore 构建，不继承此前 strict USB 返回值修改、Revive guard 或 DFU 流程补丁。只增加三处 stderr 输出：KIS bulk TX 长度/返回值、RX 长度/返回值、WRITE32 的 index/value/回复长度/size/status。重点是 RSM `0x103` BOOT_IMG。未改变返回值、请求内容、重试、超时或模式切换；额外日志仍可能影响时序，不称完全无扰动。

构建成功，`--help` 可运行，ldd 确认链接到 `/nix/store/yrnkdgidqv7akjanjfs718smnfwmzs70-libirecovery-1.3.1-unstable-2026-08-23/lib/libirecovery-1.0.so.5`。derivation 检查确认 idevicerestore 没有 patches/postPatch，库只有上述三条日志。没有自行计算文件 hash。原 `firmware-upstream-tools` 保持原样。

注意：WRITE32 的 reply 对象原本零初始化。仅在请求成功且收到完整结构时，size/status 才能作为完整设备回复解释；失败时打印的零不证明设备返回成功，rplSize 也可能仍是输入容量。上传 chunk 仍使用原始处理，不新增对未初始化回复字段的读取。

本机已加载 usbmon，并启动一次 120 秒被动 usbmon/udev 采集，目录 `experiments/2026-09-14-reinstall-retained/raw/linux-dfu-retry-1430/`。这个采集不是自动刷机等待器。再次实际恢复前须重新采集，不能用已过期抓包覆盖之后的刷机。

下一轮：设备重新进入 DFU 后，先用原始 irecovery 查询身份与实际外层 PID；保持单一恢复进程，同时采集 usbmon/kernel/工具 stderr。使用独立日志版观察 iBSS 上传与 BOOT_IMG；若正常回复后不切换，再区分 KIS 内部模式和物理 disconnect，不能现在就跳过上游等待。若传输失败或回复异常，先修对应路径，而不是加长所有 timeout。当前没有可宣布修好的协议补丁。

重建命令：`nix build .#firmware-kis-trace-tools --out-link results/firmware-kis-trace-tools`。旧 `wait-for-dfu-erase.sh` 固定上游 store 路径且主动计算 hash，不能直接用于此次日志版，也没有执行它。

## 已取得成功日志：MacUpdater-3.log

来源 `/home/sequencer/Downloads/Telegram Desktop/MacUpdater-3.log`，SHA-256 `f58b189df8e4135482a2c17aff3d08b6d2d910a0cf068aa72dfd25f460ba41cc`，私有副本 `experiments/2026-09-14-macos-guest/raw/macos-success/MacUpdater-3.log`。以下为日志自身时间，未标注时区，不与 Linux UTC 直接相减，也不据此宣称最新故障已经恢复。

- 开头版本：AMPDevicesAgent 1.7.0.161，Apple Mobile Device 1860.1.5，payload 25G83。多处明确 Customer Erase Install (IPSW)，主 ECID 与 Port ECID 均匹配本 M4。
- 16:58:33.0059 Port DFU succeeded；16:58:34.2596 DFU connected。
- 16:58:38.4780 进入 AMRestorePerformTADRestore；16:58:38.5354 DFU succeeded；16:58:38.5419 断开；16:58:40.4680 Recovery connected。从主 DFU connect 到 Recovery 约 6.21 秒，DFU 完成后至 Recovery 约 1.93 秒。即使 Apple 设置 10 分钟 transition timer，这次实际切换也不依赖长等待。
- 16:58:44.8219 明确发送 iBEC；16:58:46.5293 再次 Recovery connected；16:59:03.1594 RestoreOS connected。
- 17:07:30.9439 完成 recovery_os_restore；17:07:31.0675 完成 populate_isc_preboot_volume；17:07:46.3872 seal_system_volume；17:07:47.4557 create_system_snapshot。
- 17:07:47.5021 Restore completed status 0，Successfully restored (Level 8 attested)，耗时 557 秒。是完整恢复成功日志，不是仅端口更新或 Revive 成功；不替代重启到桌面验收。

### 固件对齐与未知边界

本地固定 IPSW 的 J713 Erase manifest 中 iBSS digest 为 `012d8ab59a425cd32dac41819fb7a6e4d65701fbf64f0c404b1149ef893ee1229b28ff24f070c3db525bff4c637664b9`；iBEC 为 `5a32a5de72d2fccf955c4d524f6396ffcdb40d83de923bb6acc3c92c658de2728268d0e93407306ca64dd38bfc6093e9`。Apple 日志对应项只显示 digest 首尾截断片段，两者均匹配。故 build/variant/板级及组件 digest 可见部分已对齐，但没有 Apple 原 IPSW 全文件 hash、完整 signed IMG4 对照，不能宣称逐字节一致。

本日志没有主 TAD DFU 的底层 bulk 请求/BOOT_IMG 回复或明确 iBSS 发送行。不能把 Port DFU 的 DNLOAD/GETSTATUS 当成主芯片普通 DFU 协议，也不能因没有 iBSS 行就断言 Apple 跳过 iBSS。优先调查 TAD/KIS 对应交互，现有 KIS 回复校验缺口仍仅是候选。

### 其他有价值证据

AppleTCON 初次无 ticket 后成功取得并完成 await_update_appletcon；没有把初始 No ticket found 当成终局失败。Recovery阶段有 SET_INTERFACE 错误且明确 expected, not fatal，以及部分 getenv/可选属性失败，随后整体成功；这些都不是 Linux 更早 iBSS 故障的修复依据。

恢复过程中明确发送 J713 Multitouch、MtpFirmware、InputDevice 三类镜像。它们可作为后续 guest 固件输入清单，但不能证明 guest 输入失效必由缺这些镜像导致，更不能证明恢复时发送等于 RAM guest runtime 可找到它们。

以下保留成功日志取得前的分析；“尚未取得成功日志/build”现已被本节覆盖。

用户报告 macOS 可成功抹盘。将其作为另一条恢复栈的成功证据，尚未取得本次成功日志/IPSW build，不能声称已完成同固件、同线缆、同操作的严格 A/B。

## 最新 Linux 时间线

来自 post-guest-1 restore.log 和 M1 kernel journal：

- 11:24:39.254 Port DFU connect，ECID 匹配。
- 11:24:42.845 Port disconnect；11:24:43.046 主 ECID 0xa10a426b9001c DFU connect；外层 USB 为 05ac:1881。
- 11:25:20.637 发送 iBSS 1363655 bytes；11:25:20.692 开始等待 disconnect。
- 11:25:30.692 10 秒超时退出 1，未到 iBEC/restored/SSD 完整写盘。
- kernel journal 在该窗口没有 USB disconnect；直到 11:26:46 才见 xHCI controller remove、总线撤销和设备断开。后者原因未确认，不解释为 iBSS 延迟成功。

因此这次不是已证实的“内核已经收到断开，只是 libusb 丢通知”。也不能仅凭未断开分清 boot-image 请求未生效、设备拒绝或固件执行异常。

## 源码具体检查点

本地固定 libirecovery 源 `/nix/store/q33665a53ivv5p8kskvrlc7nyrh9l06n-source/src/libirecovery.c` 的 irecv_kis_config_write32：irecv_kis_request 成功后若 rpl.size != 4，打印错误却 return err，而 err 已为成功；未在该函数独立验证完整回复长度和 status。当前上游也有此结构。这是可确认的错误报告/校验缺口，但本次日志未证明该分支实际触发，不能称它为已找到的恢复根因。

KIS 上传完成后的 DFU_NOTIFY_FINISH 路径调用 KIS_PORTAL_RSM / KIS_INDEX_BOOT_IMG（0x103），随后 idevicerestore 等待模式切换。进度 100% 不足以证明 BootROM 接受并执行了 iBSS。

来源：
- https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/dfu.c
- https://github.com/libimobiledevice/libirecovery/blob/master/src/libirecovery.c
- https://github.com/libimobiledevice/libirecovery/releases （KIS 是受支持的正常传输，不应因 1881 就判插错口）
- https://github.com/libimobiledevice/idevicerestore/issues/748 （Fedora/M4 Mini/iBEC 相似报错，阶段不同，未取得可套用修复）

## 下一轮实验顺序

1. 优先收集 macOS 成功 MacUpdater 日志、所用 build/IPSW 和物理连接条件，不再用换口前的 4042 日志充当成功记录。
2. 如需再测目标，保持干净工具和单设备，先上 Linux usbmon 被动抓包及 kernel/libusb 时间线；必要的诊断补丁只记录 KIS 请求/回复长度、状态及 boot-image 结果，不跳过验证或强行继续。一次 debug 不会开启固定 idevicerestore 的 libirecovery 调试，诊断配置须明确区别于 matched-tty 基线。
3. 同一台 macOS 主机可构建 Nix 管理的同版开源工具作中间对照。它与 Finder 的差异用于分离协议层和 USB backend；不是恢复成功保证。
4. 若相同开源工具只在 M1 Linux 失败，再用另一个 Linux USB host 比较，定位 Asahi USB controller/PHY 与一般 libusb 差异。此前 M1 有一次 Revive DONE，但不是 Erase 成功，不能混用。
5. 暂不加长 timeout、跳过断开、修改 Apple 固件或恢复旧 nonce/LocalPolicy；证据先于协议补丁。

另一个独立任务是解释 guest 后原生/备用 Recovery 失效。macOS 能抹盘不证明 guest 安全：移除 ans 不是 SEP/其他外设的完整隔离，且本轮存在错误物理读。两个问题必须分开追踪。
