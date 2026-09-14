# 本地 IPSW 传输与临时 macOS 恢复准备

2026-09-14，用户要求用 M1 已有 IPSW 恢复 macOS，并明确通过 SSH 传到 M4，避免重新下载。

## 源与目标

- M1 源：`artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw`，指向 Nix 固定输出。
- 文件大小：19772231540 字节。
- 固定 SHA-256：885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95。
- M4 SSH：root@172.24.5.124，继续验证已知 hostkey。
- 传输目标：`/Volumes/M4 Install Assets/UniversalMac_26.6.2_25G83_Restore.ipsw.partial`；只有大小、SHA-256 验证成功才改为 `.ipsw`。

## 为什么新增临时容器

当前 Recovery 的 `/tmp` 只有约 2.3 GiB 可用，4 GB stub 也只剩约 2.2 GiB，均放不下 19.77 GB IPSW。不能因为设备有 32 GB 内存就假定 tmpfs 足够大。

执行 `scripts/prepare-temporary-macos.sh --apply`，按 UUID 与大小核对后移除未格式化的 Linux 分区，在该空闲范围内新建 128 GB APFS；没有抹整盘，没有触碰原 iSC、System Recovery、EFI、4 GB stub。原自动生成的 Apple_Boot helper 随这次布局操作已消失，剩余约 1.9 TB 当前是未分配空间，仍预留给 Linux，并非已有文件系统。

- 临时容器：B65F080C-3A35-44D6-B376-ADFCFBDDAB2E，128000000000 字节。
- Physical Store：0ADBD0FB-E1C3-49B2-A2CF-C00D956145A7，当时为 disk0s4。
- 资源卷：1E95E303-A64C-414F-9338-4FBD9815230E，当时为 disk6s1。
- 卷名：M4 Install Assets。

资源卷不是将来的 ASR 抹写目标；恢复 OS 应使用另一个独立卷，避免销毁正在读取的 IPSW。

## 安装边界

25G83 J713 macOS Customer identity 的 OS 是 `094-96884-092.dmg.aea`（10334765056 字节），不是 Recovery BaseSystem。对应 canonical metadata 为 `Firmware/094-96884-092.dmg.aea.mtree`。IPSW 传输完成不等于系统安装完成；还需处理 AEA、系统卷恢复和启动个性化/所有权建立。

Recovery 实机有 `/usr/sbin/asr`；`/usr/libexec/installer-core` 接受 tool-name/package-path，不是直接安装 IPSW 的入口。当前没有执行 ASR 抹写、DFU Restore 或重启。

## 状态

SSH 传输后按用户改变的方案停止，最后观察资源卷占用约 11 GB；整包校验未完成，不能当完整 IPSW 使用。此前宣布的删除 stub/EFI/临时容器及重建 Macintosh HD 尚未执行。之后两次连接 172.24.5.124:22 超时，当前远端磁盘状态需重新核实。

## 当前优先方案：官方安装器复用本地资源

### 10:16–10:17 UTC：用户报告失败窗口，实际安装仍在准备

下载完成，10:14:36 解压成功，10:16:07 OSISUnarchiveMobileSoftwareUpdateOperation 成功，随后进入 OSISPrepareMobileSoftwareUpdateOperation。10:17:20 仍持续 PREPARING_UPDATE/stalled:NO/portionComplete:0.29，尚无最终成功或失败结论。29% 仅为该准备阶段比例，不是整个安装进度。

此前应用户要求“打开日志”，错误地直接启动了 Installation Log.app（PID 892）。10:16:26 其注册 Installer Crash Catcher、调用 hide progress UI；实机 Info.plist 证实 bundle ID com.apple.install.crashlog。用户随后报告失败界面。后台 PID 738/740 仍在，UpdateBrain PID 861 在 10:17 左右 CPU 约 233%，临时容器已被官方安装器创建 System/Data/Preboot/Recovery/VM，原资源卷改名 `M4 Install Assets - Data`。这支持误开的 crashlog 窗口造成误导的判断，但不保证后续安装不会失败。只关闭 PID 892，保留实际安装进程；不得点击失败窗口的重启按钮。

### 用户确认安装后（09:55:54 UTC，最新状态）

用户自行点击最终安装。09:56:18 SSH 只读核实：安装器已启动 OSISDownloadOperation，安装准备目录位于 `/Volumes/M4 Install Assets/macOS Install Data/`，对应 128 GB 临时容器，未选择 4 GB stub。约 108 GiB 可用。没有继续改变分区、注入缓存或手动重启。

重要修正：前一阶段的 MobileAsset ZIP 是资产元数据描述；最终 Required package references 和实际下载日志显示本轮通过产品包路径获取 **InstallAssistant.pkg**，大小 **18384624402** 字节，Version 25.6.83。URL 为 `https://swcdn.apple.com/content/downloads/37/33/140-93587-A_GRFFH93NOL/f944yaqo1cjhh2m0kxrl0zhcpg9yb9qphv/InstallAssistant.pkg`，完整性旁文件为该 URL 加 `.integrityDataV1`（63212 字节），tocDigestChecksum 为 9545b959cab5c536998c45f0fdd4b5d3832dc6f7。不能将此前 18.356 GB ZIP 的 SHA-256 用来校验这个 18.385 GB PKG。

日志明确 `Download cache doesn't exist, skipping`，随后 `Started downloading package`，所以实际是官方网络下载，未复用已有 IPSW。安装器自身已取得防睡眠断言。下载开始不代表安装成功；后续须验收首次启动和本地管理员创建，再恢复 m1n1 工作。当前这是对临时卷的官方安装，不是已完成整盘抹除/DFU 恢复。

### 点击继续后的实际资源选择（09:53 UTC）

官方安装器从 catalog 选中 product 140-93587。先下载约 1.52 MB MobileAsset 元数据、181 字节 InstallInfo.plist、约 4.39 MB UpdateBrain.zip 到 `/var/tmp/OSISPredicateUpdateProductTemp`，伴随 `.integrityDataV1` 文件。此处是已实测的准备资源目录，不等于已确认的完整系统包缓存注入接口。

生成的 `Info.plist/MobileAssetProperties` 明确匹配：

- SupportedDeviceModels: J713AP。
- OSVersion: 26.6.2；Build: 25G83。
- _DownloadSize: 18356020461；_UnarchivedSize: 19211279360。
- _Measurement-SHA256: 0b44a71bd6a721f5ddfb46f8dba39b09ee46bf9678a1c3100b978f512acfc07c。
- 同时存在 `_MeasurementAlgorithm: SHA-1`，不能仅凭 SHA256 字段推断安装器全部验签算法。
- __CanUseLocalCacheServer: true。
- 下载对象：https://woolyjumper.sd.apple.com/assets/CheerG/CheerG25G83/com_apple_MobileAsset_MacSoftwareUpdate/60533a8ae8e47c23593a6965d64c1f00a6396cfe.zip 。

日志明确查找 `/var/tmp/OSISPredicateUpdateProductTemp/UpdateBundle.zip` 但不存在，然后加载 UpdateBrain 并到许可证界面。IPSW 的 1527 个 ZIP 成员中未找到该 hash 名称、UpdateBundle 或 InstallAssistant 对象。现有 IPSW 整包大小和 SHA-256 均与请求资源不同，不能改名替换；也没有证明可从 IPSW 逐字节重建目标 ZIP。该本地缓存方案若继续，应使用实际所需的更新 ZIP，或进一步验证安装器支持的解包资源入口，不篡改摘要/签名。

catalog 扫描中出现 cpuFeatures.split/bridge device 等错误，但随后成功筛选出可安装产品并加载 UpdateBrain；不能单凭这些扫描错误断言 M4 不兼容或安装失败。安装器还自动出现 disk3s5/disk6s2 新卷事件，下一次写入前需要重新读取卷角色和 UUID，不能假定它完全不创建辅助卷。本轮未确认安装，也未续传 IPSW。

2026-09-14 09:51–09:52 UTC 重试 SSH 成功。分区布局未变；远端 `.partial` 精确大小 11438948352 字节。install.log 记录 09:49:06 Idle Sleep、09:51:16 键盘唤醒，支持此前超时与睡眠有关，不是已证实 sshd 配置错误。启动限时 1800 秒 `caffeinate -i`（PID 737），没有修改持久化电源设置。

从 Recovery Springboard/Resources/Utilities.plist 确认官方入口为 `/Install macOS Tahoe.app/Contents/MacOS/InstallAssistant -RunInOSIEnv`；该 app 无 Contents/SharedSupport。通过 nohup 启动 PID 738、osinstallersetupd PID 740，仅进入安装器，没有选择安装卷/确认抹写。日志已确认读取 GM Default 的 index-26-15-14-13-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog.gz（swscan.apple.com，642 products）。尚未确认具体系统包 URL/缓存命中，不得把 catalog 加载成功说成 IPSW 已被复用。

用户偏好在 Recovery 中使用官方“重新安装 macOS”流程，并让它复用本地文件。此方案尚未验证，不能把 `.ipsw.partial` 改名或放入猜测的缓存目录后声称安装器会命中。

下一步先恢复 SSH，只读收集安装进程、`/var/log/install.log`、实际 catalog/asset URL、构建号、下载目标路径、预期大小和摘要。仅在本地 IPSW 成员与安装器需要的对象逐字节对应、完整性机制明确后，才设计本地资源复用。相同版本号不保证 InstallAssistant 包、MobileAsset 和 IPSW 的封装可互换；实际索引及验证方式必须由当前安装器取证。

Apple Content Caching 确认支持 macOS 安装器和 Internet Recovery 相关内容，但它是 macOS 的内容缓存服务，不能把当前 Linux M1 的普通 HTTP 服务称为该服务，也没有验证手工导入 IPSW 的方式。[Apple 支持范围](https://support.apple.com/en-gb/102860)。

UnPlugged 是可研究的 Recovery 本地安装实现，输入为 InstallAssistant.pkg 等安装资源，不是任意 IPSW；其文档以 OpenCore/EFI 环境为背景，并警告 Apple Silicon 专用构建可能不工作，不能直接运行其整盘格式化指引或当作 M4 验证结果。[项目说明](https://github.com/corpnewt/UnPlugged)、[实现](https://github.com/corpnewt/UnPlugged/blob/main/UnPlugged.command)。

本轮只查询本地文件、公开文档和连接状态，没有改 M4 分区或启动策略。M1 的 SSH helper HTTP 服务仍返回 200。恢复终端可执行：

```sh
curl -f http://172.24.5.185:8000/ssh.sh -o /tmp/ssh.sh && sh /tmp/ssh.sh
```

命令前台运行 sshd，需保持终端窗口打开。重新连上后先验证真实现场，再继续；不自动重新传输 19.77 GB 整包。
