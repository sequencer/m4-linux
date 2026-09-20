# 再次 DFU 后保留 macOS 的独立 stub 安装

## 13:26 硬重启后再次循环：转入 NVRAM / 原生启动取证

用户要求补缺失资源重跑后，已在M1制作64MiB FAT资源盘、三个官方IM4P与既有25G83 IM4M组合的IMG4，新增可选资源分区和extra-bootargs。该ticket在本轮guest中的接受性未验证。代码/资源均仅在host，新guest未启动、文件未上传；启动脚本报告路径尚不存在。Nix新增dosfstools/mtools，GPT范围和Python语法检查通过，项目源码已另备份，无新增hash。

旧guest通过hv.reboot执行整机watchdog硬复位，13:26:29断开后m1n1串口未回来，用户报告循环与support.apple.com/mac/restore。没有再次刷机或修改恢复变量。现已停止启动等待器，原80574会话结束。不要将本文以下阶段的“guest运行中”当当前状态。

离线取证有实质新证据：本轮guest保留真实QSPI/NOR/anvram节点及服务，HV默认OFF为硬件直通；固定内核AppleARMNORNVRAM::write与eraseBank可到NOR操作。已导出启动前NVV3 proxy 64KiB，bank11/16、generation124，读取到active auto-boot=true、boot-command=fsboot、新stub boot-volume。尚缺故障后变量/写入trace。iBoot失败分支自身也会保存恢复变量，不能由事后recover-system倒推一定由guest写入。完整证据、地址、基线和假设边界见 ../../docs/NVRAM_GUEST_INCIDENT_20260914.md。

## 13:20 UTC：固件资源默认路径落实，保留 guest 等待外置输入

本地 BaseSystem dyld cache 的实际反汇编进一步确认：AppleFirmwareUpdateController::createFWAssetInfoInternal（0x1a1e3bb2c）在没有 fwAssetDirectory 覆盖时调用 MSUDataAccessor::copyPathForPersonalizedData:error:，参数 type=0，然后追加 FUD。该类型模板是 `[preboot][bootobjectspath]/usr/standalone/firmware`；实际默认目录因此是所选 Preboot + chosen.boot-objects-path + `/usr/standalone/firmware/FUD`。findFWAssetFromTag（0x1a1e35d3c）枚举目录、读取文件、解析 IMG4 payload type，与请求 tag 比较；不是按猜测的固定 ipdf/mtfw/mtpf 文件名打开。

MSUDataAccessor resolver（0x19c55c278）读取 IODeviceTree:/chosen 的 boot-objects-path，先对 `/System/Volumes/iSCPreboot` 加该路径调用 access；ENOENT 时退到 `/System/Volumes/Preboot`。所以只说“没有普通 Preboot”不足以排除 iSC 路径。本次另将 M1 本地 current-isc/isc.raw 的 volume 0（iSCPreboot，83EB3F50-D96E-4B10-8401-F4AB6F734A1E）只读挂载检查：stub UUID 目录下只有 LocalPolicy，没有 boot 目录，更没有对应 FUD。根盘自带 FUD 仅 MultiUpdater/MultiUpdater.efi。guest 启动输入里的默认固件资源目录缺失已得到离线证据；但还没有用户态本次具体 open/枚举错误，仍不能排除 FWDirectory 覆盖或服务未启动等额外问题。

补充现场读取：AppleHIDTransportBootloaderRTBuddy 的 vtable 为 0xfffffe00080a5270，当前对象 0xfffffe2303f91000，+0xe0 确实指向 mtp-transport 下载器 0xfffffe29d24398e0，+0x108/+0x10c 为 0/0（状态字段/timeout 毫秒）。不能将其解释为已经进入 state=1 的 firmware wait 锁死。通过 _proc_best_name 的反汇编读取 proc+0x5dd、最多33字节，PID115 是 com.apple.MobileAsset.DownloadSe，PID165 是 com.apple.MobileSoftwareUpdate.C；不能将先前截断的 com.apple.Mobile 误报为 FUD updater。完整进程枚举仍未验证。

取证文件在 raw/hid-offline/：fw-asset-directory-disassembly.txt、preboot-resolver-disassembly.txt、find-firmware-tag-disassembly.txt、personalized-firmware-path.txt、msu-path-strings.txt、current-iscpreboot-stub-tree.txt。现场新增 process-names-long.json、bootloader-status.json。没有修改 guest 内存内容、文件系统或启动配置；临时硬件断点全部清除，guest 已 cont。

当前只有 HV 调试入口，没有 guest shell/SSH，内建输入无法用。下一项最低扰动的现场实验需要人接外置 USB 键盘/鼠标：保留现有调试线不动，使用另一空闲 Type-C 口，不重启。IORegistry 确认 usb-drd1、hs/ss port 和 hpm1 仍存在，但这不等于外设热插拔已验证。通过该输入进入 guest 用户态后，才能直接观察固件目录/错误并进行针对性加载；如外置输入同样失败，再决定下一轮启动资源补齐，不预先强制重启或恢复。

## 13:14 UTC：现场确认三个输入固件下载器未完成

继续保留同一 guest，不重启。只读挂载 M1 本地 Recovery APFS 文件到 ~/.cache/m4-basesystem-ro，检查 BaseSystem 内的 MobileAccessoryUpdater 资源。GenericKextUpdaterService 的 sandbox profile 明确列出 /private/preboot、boot-objects-path、AHTLoaderName、Image Tag、Need FUD Download 和 AppleFirmwareUpdateUserClient；这证明该服务设计包含这些访问，单独不能证明本次具体 open 失败。

离线反汇编确认 AppleHIDTransportBootloader → AIDImageDownloader → AppleFirmwareUpdateKext::initWithData，后者设置 AppleFirmwareUpdateUserClient 和下载回调。对 loadFirmware（0xfffffe0009263cdc）及 AIDImageDownloader::beginFirmwareDownload（0xfffffe000958c8f8）设置十核硬件断点，约两分钟窗口无命中；随后逐一删除，所有断点槽为空。不据此推断启动早期从未请求。

getRegistryRoot 的固定内核指令确认全局指针在 0xfffffe000c658488。本轮重新读取根对象并使用原 guest-ioreg.py，得到 1425 条记录、一条 Unmapped registry address，limit_reached=false；不是完整无误的 ioreg。结果 raw/guest-current-isc-1/ioreg.json，不复用旧 guest 对象地址。MTP 的 ASC、RTBuddy、DockChannel、Hibernator 已绑定，不能称驱动根本没接管。

三个对象的 vtable 均为 0xfffffe00080eb290，即 AIDImageDownloader 的 __ZTV + 16。属性类型也逐项读回：AHTLoaderName 为 OSSymbol，LoadingGroup/Image Tag/Need FUD Download 为 OSNumber（不是 OSString，也不是 kOSBoolean 指针）。按固定内核 OSNumber 方法读取 +16 数值；isDownloadComplete 的反汇编明确读取对象 +0x180 的 bit0。

| loader | image tag | LoadingGroup | Need FUD Download | isDownloadComplete |
| --- | --- | --- | --- | --- |
| stm | ipdf | 0 | 1 | false |
| multi-touch | mtfw | 0 | 1 | false |
| mtp-transport | mtpf | 1 | 1 | false |

现场原始字段、类型头和解释分别保存在 aid-status-raw.json、mtp-vtables.json、aid-status.json。这已将候选收窄为实际存在的输入固件下载未完成；与 IRQ_MASK=0、RX_COUNT=0x408 的重复读回一致，但尚未取得用户态文件错误，不能直接宣称缺 Preboot 是唯一根因。这里的 download 是固件向设备加载流程，不等于一定在联网下载。每次采集后 cont，未消费 FIFO、未写输入设备寄存器、未修改磁盘或重新计算 hash。

## 输入等待继续定位：CPU 栈和 Preboot 资源缺口

同一 HV 会话采样十核栈，保存 raw/guest-current-isc-1/cpu-stacks.json；多核 ELR 在 0xfffffe000b921ffc–0xfffffe000b92201c。固定内核离线反汇编确认此处是 PMC 寄存器读取，返回链经过公共内核路径，并非已识别的 MTP 阻塞调用栈。不能据此判定全机死锁或输入驱动锁住。每次结束 cont，未重启。

从已保存 guest.adt.bin 离线解析确认 boot-uuid=E93D361D-43AC-47A0-8DDA-A5D235BACC77（RAM Recovery），但 apfs-preboot-uuid=530FE39B-6AE3-47D0-9168-29F1A7EE2763，boot-objects-path 仍为该 stub 的 /530FE39B-6AE3-47D0-9168-29F1A7EE2763/boot/E3EC22D7… 路径。当前 RAM GPT 仅根盘+iSC，不含 stub Preboot，且 ANS 节点已移除。因此启动资源路径指向未呈现的 Preboot 是实际配置缺口。chosen/memory-map 没有以 MTP/Input/Multitouch/Firmware 命名的属性；这仅是名称检查，不证明输入固件从所有其他渠道都不可用。

缺 Preboot 是否阻塞 MTP 固件加载仍待确认：内核可见 boot-objects-path、Need FUD Download、AHTLoaderName 和 firmware-loading-error 字符串，但字符串存在不等于现场命中。未盲改 UUID、未注入旧 Preboot、未补写 guest 磁盘。下一步应定位 firmware loader 的实际取文件路径/请求返回，而不是凭当前线索宣称根因已修好。

控制台 pitfall：HV shell 的 exec 名称被 ProxyUtils.exec 覆盖，是汇编执行入口，不是 Python builtin。首次 Python 多行采样误入汇编器，编译失败，未执行 target 指令；改为 builtins.exec 后采样完成。不要再直接使用裸 exec 执行 Python。

## 新 iSC guest：图形界面与输入调试

用户要求后，以 --skip-file-hashes、16GiB/10核/graphics 运行原 launcher，使用 current-25G83 内核/Recovery 和本轮备份 current-isc/isc.raw。旧输入未复用。bless 后默认启动改为 Bootstrap；实际重启、RAM 上传、guest secondary 启动和 BaseSystem adapter 成功。用户确认 Options 界面持续转圈，触控板及 Tab 无响应。HV 会话仍保留，未自动重启/刷机。

现场控制台读回 16384 字节，主要是早期日志；没有据此判定 guest 停在早期。进程读取确认 launchd、hidd PID96、WindowServer PID76、RecoveryOS Agent PID131、Boot Picker PID155 等存在，完整枚举未验证；报告 raw/guest-current-isc-1/processes.json。每次采集后 cont 恢复 guest，没有运行 IORegistry 对象解码。

本次按 live ADT 获取 MTP base=0x394600000、Dock IRQ=0x394b14000、FIFO=0x394b30000。仅状态读取得 CPU_CONTROL=0x10、CPU_STATUS=0x6c、INBOX/OUTBOX_CTRL=0x20001、IRQ_MASK/FLAG=0、TX_FREE=0x800、RX_COUNT=0x408，保存 mtp-status.json。未读取 RX_DATA 或写 IRQ_MASK，未实例化会设置 IRQ_MASK 的 DockChannel 类。

短时（至少10秒）ASYNC 跟踪 guest 对 Dock IRQ 0x1000、FIFO/config/data 0x8000、MTP mailbox 0x1000 的访问；页表更新确认跟踪生效，期间没有输出 MMIO 访问事件。随后删除三处 PrintTracer，cont 后页表恢复。再次读回 IRQ_MASK=0、RX_COUNT=0x408。这支持“当前采样期间输入传输未被消费”，不证明从开机起驱动从未访问、不证明 IRQ 丢失或全机死锁。旧 iSC 更换后现象依旧，固件加载/transport 初始化等待仍是候选；缺实际驱动调用栈与固件请求错误，不能声称根因已确定。

## 12:29 UTC：当前资源重建完成

重建后的独立 SHA256SUMS 复核完成，71 项全部 OK（含完整 IPSW），退出 0；日志 raw/current-assets-verify.log。Python 语法检查与 guest 入口拒绝检查通过，git diff --check 通过。该验收仅证明本地文件一致性，不证明 guest 安全或新设备 iSC 已采集。

prepare-current-assets.py 对固定 25G83 IPSW/官方 J713 资源/派生产物校验，首次在 m1n1 hash 守卫拒绝：result 仍指向 d617ceee… 原版，而实机是 779c9ac3… optional-ANS。没有创建成功资源目录、没有连接 target 或放宽 hash。重新 nix build .#m1n1-sptm 后 result=/nix/store/26pj1nn35yxzx0i4s7qrx4c8s4x7lmp6-m1n1-sptm-pr-1-7e43bb1，hash 与实机匹配。

随后重建成功、退出 0，新目录 artifacts/current-25G83-post-restore-20260914。内核从官方 IM4P 重新解包为 f42ad6f5…；Recovery 从官方解密 DMG 重新转换、提取为 bda0c53d…，1574961152 字节。没有沿用旧 raw 根盘或 iSC。CURRENT_ASSETS.json 是本次文件清单快照，二进制本体仍 ignored，不等于提交/备份。

旧 run-recovery-guest.py 在 main 入口无条件停止；Nix 下语法检查通过，负向运行退出 1 并给出隔离原因，未访问串口。旧证据文件保留不改名不覆盖，旧内核文档标记历史，README 指向新资源入口。当前设备 iSC/个性化状态尚未重新采集，不声称所有设备状态已更新；此次全为 M1 离线操作，M4 留在 m1n1。

## 12:25 UTC：本轮 m1n1 实机代理验收通过

用户在启动选项选择后反馈看到 m1n1。M1 等待器于 2026-09-14T12:25:07.582164+00:00 完成一次检测，退出 0；raw/m1n1-proxy-check.json 记录 /dev/ttyACM0、串号 M49KYH65C9、uart_nop=ok、proxy_nop=ok、linux_boot_verified=false。两个串口 ttyACM0/1 均已枚举，检测进程已结束，不再占用代理。

启动输出确认 Mac16,12 / J713 / chip 0x8132 / Running in EL2；实际内存 mem_size_act=0x800000000（32GiB），OS/System FW 均 mBoot-18000.161.10。屏幕 framebuffer 2560×1664，MMU/cache、AIC3 和 USB 初始化后进入 Running proxy。

仍有 MCC Unsupported version:mcc,t8132、cpufreq Chip 0x8132 is unsupported，以及 Unknown payload magic 5b41464b / No valid payload found；后续代理握手成功，因此这次并未停在这些提示上。不把它们当作 Linux 驱动已支持，也不把代理可用扩大为 Linux 或 SPTM guest 可启动。

没有运行 guest、上传内核或再次重启；本轮确认的是新安装的持久化 m1n1 可以被物理选择启动并经 USB 调试。原生 macOS 缩容和策略修改后的桌面重启验收、备用 Recovery 验收仍待进行。物理选择前默认启动为 macOS；未在 m1n1 下重新读取当前默认变量，不声称选择后一定未变化。

Host pitfall：首个等待器使用 compgen，但本次 Nix bash 不提供该命令；已中止该进程（退出 130），改为 test -e /dev/ttyACM0 后再用 pyserial 校验 VID/PID/串号。只有后一个等待器成功，不将旧进程称作仍存活。

## 安装后首次代理启动验收：等待物理选择

用户要求继续安装 m1n1 后，再次读回新 stub：Bootable true、Permissive、sip0=7f、sip1/2/3=1、原 coih 8D45D8B4… 存在。SSH 读回 boot.bin SHA256 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4，与固定 Nix 构建一致；没有重复运行 kmutil 或修改策略。

保留默认 boot-volume 为 Macintosh HD，已发送 sync; shutdown -h now。用户需长按电源进入启动选项，选择 M4 Linux Bootstrap → Continue（不是 Options）。M1 启动限时 900 秒检测，在仅有同一串号的两个 1209:316d 串口时执行一次 scripts/m1n1-check.py，记录 raw/m1n1-proxy-check.json。Nix 提供 Python/pyserial，sudo 显式传递 PYTHONPATH；不启动 guest、不上传 payload、不操作 DFU。等待器启动不是代理成功，须以后续实际 JSON/退出状态为准。

## 12:21 UTC：原生 macOS 安全策略修改完成

用户再次启动 SSH 后，确认 Macintosh HD 卷组 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8 为 Paired / one true recoveryOS / Valid，ECID 和当前所有者匹配。本次 csrutil disable 交互选择 Macintosh HD，认证成功、退出 0。随后执行：

```sh
bputil -c -a -s -v 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8
```

认证后退出 0。未用 -n/-g 强制重建，未向 macOS 安装自定义启动对象。

- csrutil status 对 Macintosh HD 与 M4 Linux Bootstrap 均显示 disabled。
- macOS 策略 Permissive；sip0=7f（bputil 标记 Customized），SSV/CTRR/启动参数过滤均 Disabled，sip1/2/3=1。
- macOS coih absent；nsih 更新为 E3EC22D725FED7937C03FEA6792DF0284ADD23F4530B4D4D975186E2C6B8E5CFDD0CC21A9A2907E2491C120AAAB3D1F8；spih 更新为 48529AADC70D40ABEFA0C90B4EE51DA005B8BA2F0A35D521E4A7098ABC180291C5ABE1E4F58EA824CC56D513358FEF95，stng=3。这是工具操作后的实际新策略，不声称所有哈希未变。
- stub 仍为相同 Permissive/sip0=7f/sip1/2/3=1，原 coih 8D45D8B4… 保留，Pairing Integrity Valid；本会话对 stub Not Paired 是配对对象不同，不是完整性损坏。
- 默认 boot-volume 仍指向 Macintosh HD。仅配置策略并 sync；本轮未重启、未启动 guest，尚待重启生效与原生启动验收。

读回日志在 ignored raw/macos-security-disabled.txt。首次 authenticated-root status 因多安装需交互选择未给出状态，不能将菜单当作验收；另以明确选择 Macintosh HD 的命令补查，记录 raw/macos-authenticated-root-status.txt。

这些结果仅涵盖已列出的启动安全设置，并不证明硬件安全、Gatekeeper/TCC 等全部关闭，也不证明此前 bootloop 原因为安全限制。没有删除 iSC、LocalPolicy 或恢复资源。

## 最新：stub 启动对象已安装，等待 macOS 配对 Recovery

用户重新长按进入后，新 stub 为 Paired / one true recoveryOS / Valid。boot.bin SSH 读回 SHA256 再次匹配 779c9ac3…；csrutil disable 明确选择 M4 Linux Bootstrap，kmutil configure-boot 使用 raw/entry-point 2048/lowest-virtual-address 0，返回 installing boot object / done，退出 0。随后 bputil -s 成功；策略 Permissive、sip0=7f（工具显示 Customized）、sip1/2/3=1，coih=8D45D8B43264A698ACB2CF4EDF7809E52BD018238894866671D65CACF643332F8B96C58BC8C1DEA8BAEB2452A3C4037C。原始读回在 raw/installed-policy.txt。尚未启动验证 m1n1，也未运行 guest。

bless 已将默认启动恢复 Macintosh HD，nvram -p 读回末段卷组 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8。用户随后明确要求 macOS 同样关闭安全选项，覆盖先前保留 macOS Full 的意图。在 csrutil 菜单中选择 Macintosh HD 后，命令因当前 Recovery Not Paired 拒绝，退出 69；未发生 macOS 策略降级。再次检查仍 Full，SIP/SSV/CTRR/启动参数过滤 Enabled。下一步正常关机，用户长按电源进入 Macintosh HD 的 Recovery，再核对配对后继续。

重启后物理编号重新排序：stub 改为 disk0s3，System Recovery 改为 disk0s5，UUID 不变。上一阶段脚本不可再次运行。关闭启动限制不等于关闭全部硬件安全，也不是此前 bootloop 的已证实修复；不清除 iSC、策略或恢复文件。

以下为先前准备阶段的历史记录。

2026-09-14 12:00 UTC 后，用户确认再次完整 DFU Restore，进入 Recovery 并启动 SSH。目标 Mac16,12，ECID 0xA10A426B9001C，系统 25G83，SSH 172.24.5.124。

## 已完成

- 原 macOS 容器 D3A4EF6C-BA92-4923-875E-A4D00E89AE29 从 1995218165760 缩至 128000000000 字节。diskutil 自带 fsck_apfs 检查退出 0；缩容后约 101GB 空闲。
- 当前 macOS 卷组 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8；账号 sequencer，owner UUID 0500AC47-EA6B-451B-8473-6E7A0460A4AD，Volume Owner Yes。认证成功，密码未存入项目。
- 新 stub 物理分区 disk0s5 / F322BE9F-F630-400D-B965-EB29A87BC3F6，3999997952 字节；容器 FCD42C83-7878-4C61-BE47-322972C988CC；卷组 530FE39B-6AE3-47D0-9168-29F1A7EE2763。
- stub System UUID 2DE4D935-C94A-486D-A338-3D7022C492C4，Preboot A0D1E0E5-0AE5-42C7-9FFA-872DF997C904，Recovery 1E196435-F401-4552-B876-2E4BB8FD3F3F。
- 新 EFI disk0s4 / 5F01B51F-85FC-4959-8AA9-74A7AFCF2D76，999997440 字节，使用 `%EFI% %noformat%` 创建；没有部署 EFI 引导文件。剩余约 1.862TB 保持未分配，供 Linux 后续使用，尚无 Linux 文件系统或系统安装。
- iSC disk0s1 / 2935ACB5-2A69-4996-942A-87B29BC17A2F，524288000 字节；System Recovery disk0s3 / 7EAA30B1-3DD4-417C-AC72-420E041C97AF，5368664064 字节，均保留原位置。
- 固定 stub-update.tar SHA256 a85e25ed69c8445dbf854f1fc9833d5af1cdae756b1e8f305db0c4b3f8f2f580；通过 SSH 流式解包到新 stub Data。目标 Python 校验 SHA256SUMS 全部通过，部署 System/Preboot/Recovery，设置 APFS bootable flag。
- m1n1 payload SHA256 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4。仅文件部署，不等于 kmutil 安装或代理验收。
- Python 来自 Nix 固定 asahi-installer v0.9.1；同时设置 DYLD_LIBRARY_PATH 和 DYLD_FRAMEWORK_PATH。
- 仅复制本轮 macOS Preboot E37174ED-4371-4BA3-B783-368C544244C8 内的 AdminUserRecoveryInfo.plist 到新 stub，校验 cksum 并设置 schg。没有恢复旧 iSC/LocalPolicy/个性化票据。旧归档 update-plan.json 未作为当前配置执行。
- bputil -g 为新卷组生成有效 Reduced 策略，coih absent，SIP/SSV 仍 Enabled；macOS 策略保持 Full。bless --setBoot --mount "/Volumes/M4 Linux Bootstrap" --user sequencer 认证成功，用于下一次进入 stub 配对 Recovery。

## 当前边界和下一步

当前会话是 macOS 的 Paired 1TR，对 stub 则为 Not Paired。尚未执行 csrutil/kmutil/bputil -s，尚未重启验收 m1n1。必须正常关机、用户长按电源进入 Options，进入新 stub 对应 Recovery 并重新启动 SSH，再核对 Paired/Valid 后继续。配对安装结束后恢复 macOS 为日常默认启动，避免实验失败持续落入 stub；物理选项测试 m1n1。

禁止运行旧 run-recovery-guest 路径。不得用旧 iSC，即使其系统版本也为 25G83。原系统基础卷 diskutil 显示 Sealed: Broken，而原启动快照仍在、fsck 通过、策略 SSV Enabled；基础卷状态不能替代启动快照验收，目前未做缩容后原生重启验收，不宣称已验证正常启动。

脚本按阶段、固定新 UUID 防误操作，非通用可重复执行安装器：prepare-retained-macos-layout-20260914.sh、finish-retained-layout-20260914.sh、stage-retained-stub-20260914.py、prepare-retained-owner-20260914.sh。旧 staging 模块仅复用资源部署函数，入口覆盖为新 UUID。原始基线/操作输出在 ignored raw/，未提交；无密码日志。

Pitfall：容器 UUID 应从 diskutil apfs list -plist 获取，diskutil info 的本轮输出无 APFSContainerUUID；最初守卫因此停止，未写盘。新分区 BSD 编号不是物理顺序（stub s5、EFI s4），不能按旧编号定位。boot-volume 可能为命名空间变量，裸 nvram boot-volume 返回缺失不能说明 bless 失败。
