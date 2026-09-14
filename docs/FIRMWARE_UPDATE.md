# M4 固件升级：25E253 → 25G83

## 2026-09-14：用户改为完整抹盘Restore

用户明确授权删除M4所有内部数据并再次要求直接DFU抹盘修复，覆盖本文历史Revive阶段的禁止Erase要求；不删除M1备份与项目。正式Restore使用无项目补丁的firmware-upstream-tools、原始libirecovery及完整固定Apple25G83 IPSW，修改版留作取证。入口、实际连接状态与验收记录见[DFU_ERASE_20260914.md](../experiments/2026-09-13-iokit-ram-root/DFU_ERASE_20260914.md)。尚未取得DFU连接不能称为已抹盘，DONE不能替代原生启动验收；以下Revive操作及其限制保留为历史时间线，不是本轮Erase命令。

## 2026-09-13 实际状态

### 22:15 第二轮修复结果（不是 guest GUI 完成）

guest RAM-only iSC实验推进到WindowServer后，P_REBOOT后发生循环启动，用户普通/备用Recovery均无法进入并显示support.apple.com/mac/restore。第2次Revive在iBSS模式切换失败exit1；重新物理进入DFU后，第3次（PTY94910）连接restored且确认主ECID/CHIP/BORD，沿Customer Upgrade Install (IPSW)执行非抹盘25G83修复。22:15:45返回DONE、exit0，日志experiments/2026-09-13-iokit-ram-root/raw/dfu-revive-third.log，SHA256=bd12f2f178b0911f85b99260a392d6121da52a5703daab0511c85dabe513df3a。

await_update_appletcon仍result=-1，另有一次USBPortController1,Ticket缺失；不能声称所有固件组件通过。完成后USB无目标，SSH No route to host，Recovery启动、SFR、原Data及Bootstrap策略尚待重新读取。不可直接将此前的SSV/coih和Data状态延用为本次恢复后的验收，不自动重装、不转Erase，先恢复Recovery诊断。

最新启动后验收：optional-ANS m1n1 USB proxy 可用；system/stage-one/stage-two 均实际为 mBoot-18000.161.10。VM_TMR_FIQ_ENA_EL2 原值写入/读回通过，HV.init 成功。后续 16GiB RAM-only guest 已执行 XNU，但停在 ApplePMGR panic，并非完整 macOS 启动；完整内存另触发 HLE 页表池上限。详见 [NEW_FIRMWARE_GUEST_EXPERIMENT.md](NEW_FIRMWARE_GUEST_EXPERIMENT.md)，以下资源安装和策略暂态是历史时间线。

资源安装完成；非抹盘 DFU revive 于 **18:24:13 UTC 返回 DONE / 退出码 0**。Recovery SSH 后已实测 **SFR = 26.6.2 / 25G83**，原 Data UUID/大小/已用字节数仍在且锁定未挂载（不等于逐文件内容校验），stub NSIH/coih 仍旧。已修复旧 Recovery cache symlink 的版本混用，修复后正常启动待复测。目标是 Mac16,12 / J713 / t8132 / board 0x2C，ECID `0xA10A426B9001C`。

最新复测：链接修复后，旧 25E253 Recovery 已成功以 **one true recoveryOS / Paired** 启动。随后在其中 `bputil -g -v DE77783E-D9C0-4695-8BE1-EBE0D3015748 -u liqi` 返回 0，重建新版策略，love=25.7.83.0.0,0，新 NSIH=`E3EC22D725FED7937C03FEA6792DF0284ADD23F4530B4D4D975186E2C6B8E5CFDD0CC21A9A2907E2491C120AAAB3D1F8`，Preboot 和 Recovery 的新 cache/active 已创建。旧 cache link 继续指向保留的旧镜像，新 cache link 指向 canonical 25G83 镜像。

**重建新版 Recovery 策略会使当前旧 Recovery 当场变为 Not Paired**，即使进入时是 Paired；不在旧现场继续强制 kmutil。bputil -g 同时将安全状态重置为 Reduced、SIP Enabled、coih absent，这是暂态，尚未重新安装 optional-ANS m1n1。必须关机后单次长按电源，经 Options 进入新的 25G83 配对 1TR，重新开 SSH，随后关闭 SIP、configure-boot。**此时不要直接正常启动 M4 Linux Bootstrap**：coih 为空，最小 stub 不是完整 macOS。原 Data 复查仍 Locked/未挂载；未自动重启。

### 最新：新版配对 1TR 和 optional-ANS 安装完成

用户再次启动 SSH 后，`sw_vers` 为 26.6.2 / 25G83，`bputil -d` 为 **one true recoveryOS / Paired / Pairing Integrity Valid**。这次新版 Recovery 启动已实际通过，不是仅更新了资源。

`csrutil disable` 明确选择 **M4 Linux Bootstrap**（此次交互编号 2，编号不可跨启动复用），经 owner 认证返回 0。随后执行：

```sh
kmutil configure-boot \
  --custom-boot-object "/Volumes/M4 Linux Bootstrap/Finish Installation.app/Contents/Resources/boot.bin" \
  --raw --entry-point 2048 --lowest-virtual-address 0 \
  --volume "/Volumes/M4 Linux Bootstrap"
```

owner 认证后返回 `installing boot object... done.` / 退出码 0。复核策略是 Permissive、sip0=7f、CTRR Disabled、Boot Args Filtering Disabled，新 NSIH 不变，coih=`3C1819488DC4CF8762CFEA1F5777CF14D07BE427BFD2D10D7A17B638BC91FCC5AB4FF88630E2FAE753279CC9B9AF5A7A`。原 Data 仍 Locked、未挂载、已用字节数不变。

从新版 Preboot cache 读回实际 CustomKC 到 M1，1592136 字节，SHA-256=`3c02fa38e54354cd12846c9623e90f955a7398588c06dd77686315941db41df1`。其中唯一嵌入的 raw payload 起始 offset 74，1589248 字节，逐字节匹配 Nix optional-ANS m1n1，SHA-256=`779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4`。coih 是启动对象标识，不与 raw SHA-256 混用。

安装和落盘读回验证完成，**尚未自动重启，m1n1 USB proxy / live firmware tags / timer write / guest 仍待验收**。用户现在可以从 Recovery 重启正常进入 M4 Linux Bootstrap，不再处于上面的 coih absent 暂态。原 `m4-firmware-update.json` 是资源安装阶段 journal；最新实际策略及验收状态以 `experiments/2026-09-13-firmware-update/STATUS.json` 和对应 raw 记录为准。

在实验 stub 配对 1TR 中完成：

- 原 System、Preboot、Recovery 三份 tar 已备份到 **M1** 的 `artifacts/backups/2026-09-13-before-25G83/`，SHA256SUMS 和归档遍历检查通过。
- `scripts/prepare-stub-firmware.py` 从固定哈希的完整 Apple 25G83 IPSW 构建更新包。
- `scripts/apply-stub-firmware.py` 校验目标 UUID、4GB 容器、配对状态、包哈希及每个文件哈希后，只更新实验 stub。保留旧 restore、Recovery DMG、boot.bin、系统 plist 和旧 NSIH boot 缓存。
- 新 restore 包含正确的 BootabilityBrain framework（保留 symlink / 可执行权限）、Bootability trustcache、通用 ticket 和 J713 启动资源。System 的 restore symlink 已修正为本次挂载点。
- optional-ANS m1n1 已复制为 stub 的 `boot.bin`，**尚未成功安装为新的 CustomKC/coih**。
- 原 256GB macOS Data 仍为 FileVault Locked、未挂载；没有解锁、擦除或改写原用户数据。

更新包大小 `1642465280`，SHA-256：

```text
a85e25ed69c8445dbf854f1fc9833d5af1cdae756b1e8f305db0c4b3f8f2f580
```

通过 owner 密码认证后执行：

```sh
bputil -g -v DE77783E-D9C0-4695-8BE1-EBE0D3015748 -u liqi
```

Apple 接口返回 `BYErrorDomain Code=105 / SFRUpdateRequired`：

```text
SFR update required to make volume bootable
current=25.5.253.0.0,0
target=25.7.83.0.0,0
```

命令失败，原策略未变：Permissive、sip0=7f、love=25.5.253.0.0,0，NSIH / coih 仍为旧值。`/System/Volumes/iSCPreboot/SFR/current/SystemVersion.plist` 实测仍为 26.4.1 / 25E253。没有自动重启。

资源更新 journal 的 `resources_updated=true`、`policy_updated=false`、`boot_verified=false` 是正确状态；不得把 SystemVersion 的 25G83 或 boot.bin 文件替换当作升级完成。

## 下一步：非抹盘 DFU revive

### 本次已开始执行

M1 的 usbmuxd 已以前台方式运行。USB 检测到 `05ac:f014 / Port DFU`，只读查询确认 Mac16,12 / j713ap。端口控制器 ECID 为 `0x3fc75d711905dde9`，不是主芯片 ECID，因此在 Port DFU 起步时使用这个端口 ECID；工具会在端口断开后重新获取主芯片 ECID。本地 safety patch 已增加主 build identity 处理前必须匹配 `0xA10A426B9001C` 的检查。

实际运行上述工具，参数为端口 ECID、完整 IPSW、明确的 `Customer Upgrade Install (IPSW)`。Port DFU 控制器临时固件阶段内部读取 Erase identity 的 USB 固件信息，不等于向 restored 请求 Erase；主恢复 identity 和行为仍必须是 Upgrade/Update。

日志确认 Port DFU transition 成功，Apple TSS 授权成功，主恢复环境为 `00008132-000A10A426B9001C`、BoardID 44 / ChipID 33074，符合本台 M4。加载的临时恢复 iBoot 为 `mBoot-18000.161.10`，不能提前当作已持久化 SFR 的验收。固件写入及部分控制器更新检查点通过。Ace3 一次 ticket 缺失警告之后对应 `update_ace3` 检查点 result=0，流程继续。

18:24:12 最终返回 `Status: Restore Finished`，18:24:13 `DONE`，进程退出码 0。完整日志 SHA-256 是 `b3facd41851919fd5898004be68b38df021f9861d2c927aff7af32e4b60bcc02`。复查日志另发现 `await_update_appletcon` result=-1、failed to copy response for AppleTCON；该异常没有导致总体恢复失败，但不能声称每个控制器都通过验收。不要基于这个异常自动重复刷写或转为 erase。

恢复结束后 USB 暂时仅见 M1 root hubs，原 Recovery SSH 地址返回 No route to host。原 Data 锁定状态是更新前的核验，更新之后的 Data/SFR/策略必须重新读取。工具成功完成是已验证事实，持久化版本、原用户数据和 macOS guest 启动还未验收。

Apple 官方区分 [Revive 与 Restore](https://support.apple.com/en-ie/108900)：Revive 不擦除，Restore 擦除。官方支持的控制机是 macOS 14+；本项目 M1 Linux 上使用第三方 libimobiledevice 工具，不能宣称 Linux 是 Apple 官方支持的方式。[NixOS Asahi 维护者文档](https://github.com/zzywysm/nixos-asahi/blob/supreme-asahi-6.12/docs/uefi-standalone.md) 记录了 Linux 非抹盘 Mac revive，但其测试是旧款 Mac mini，不是本台 M4 的成功证明。

Nix 构建已完成：

```sh
cd /home/sequencer/project/m4-linux
nix build .#firmware-revive-tools -o results/firmware-revive-tools
nix build .#dfu-tools -o results/dfu-tools
nix build .#usbmuxd-tools -o results/usbmuxd-tools
```

- idevicerestore：1.0.0-unstable-2026-09-07，源提交 `60192e97f87d1bbab5c493684e0a245b0966363f`。
- libirecovery：1.3.1-unstable-2026-08-23，源提交 `95dec3aa25b1e30654ca107eb971971f6a216520`。`irecovery -a` 确认包含 Mac16,12 / j713ap / 0x2c / 0x8132。
- 本地 Nix patch 在主 build identity 选择后拒绝 `FLAG_ERASE`、缺失 RestoreBehavior 和非 `Update` identity，避免默认身份回退到 Erase 后继续刷写。编译通过，但这不是整个 Apple 恢复协议的数据安全形式化证明。
- 完整 25G83 IPSW 具有 J713 的 `Customer Upgrade Install (IPSW)` / `Update` identity。stub 用的 `macOS Customer` identity 的 RestoreBehavior 是 Erase，**不能直接作为 DFU 主恢复 identity**。
- [固定源 restore.c](https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/restore.c) 设置非 erase Mac 的 `AuthInstallRestoreBehavior=Update`，但也有分区/系统镜像相关选项；不是单纯向几个 SFR 文件拷贝。实际行为与成功仍须现场验证。

### 用户需要手动进入 DFU

1. M1、M4 都接电。M4 用 MagSafe 供电，M1 与 M4 直接以支持数据和充电的 USB-C 线连接。**M4 Air（2025）的 DFU 口是远离 MagSafe、靠近机身前沿的 USB-C 口**，即面对机器左侧接口时最右侧那个口，见 [Apple DFU 口表](https://support.apple.com/en-us/120694)。此前“靠近 MagSafe”的 DFU 指引错误，不能把 debug USB 口与 DFU 口混用。Apple 明确要求不要使用 Thunderbolt 3 线；已有 debug USB 能用不证明该线 DFU 能用。移除其余 M4 USB 外设。
2. 长按 M4 电源约 10 秒，直到关机。
3. 按一下并松开电源，立即同时按住 **左 Control + 左 Option + 右 Shift + 电源**。
4. 四键保持约 10 秒，再松开三个键盘键，**继续按住电源最多 10 秒**。
5. DFU 下 M4 屏幕保持黑屏。M1 Linux 不会出现 Finder；由控制机检查设备。Recovery SSH 会中断，这是预期，不代表擦除。

### 控制机先只读确认

```sh
sudo /home/sequencer/project/m4-linux/results/dfu-tools/bin/irecovery \
  -i 0xA10A426B9001C -q
sudo /home/sequencer/project/m4-linux/results/dfu-tools/bin/irecovery \
  -i 0xA10A426B9001C -m
```

必须确认 ECID、芯片、板号及 DFU 状态符合本台目标，否则停止。2026-09-13 准备完成时查询结果为 `Unable to connect to device`，目标仍在 Recovery，**尚未执行 DFU 写入**。

### 仅现场确认之后执行的非抹盘命令

先确保没有另一个 usbmuxd / 恢复程序占用设备。在一个控制机终端运行 usbmuxd 前台进程：

```sh
sudo /home/sequencer/project/m4-linux/results/usbmuxd-tools/bin/usbmuxd -f -p
```

另一个终端：

```sh
cd /home/sequencer/project/m4-linux
mkdir -p artifacts/apple/25G83/revive-cache
sudo /home/sequencer/project/m4-linux/results/firmware-revive-tools/bin/idevicerestore \
  --ecid 0xA10A426B9001C \
  --variant 'Customer Upgrade Install (IPSW)' \
  --cache-path /home/sequencer/project/m4-linux/artifacts/apple/25G83/revive-cache \
  --logfile /home/sequencer/project/m4-linux/experiments/2026-09-13-firmware-update/raw/dfu-revive.log \
  /home/sequencer/project/m4-linux/artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw
```

不要使用 `--erase`、`--no-input`、`--ignore-errors`，不要使用缩减为单个 macOS Customer identity 的 stub BuildManifest 进行 DFU。失败时保留完整日志，**绝不自动转为 erase**。进入 DFU / 读取设备信息不等于已经获得 Apple TSS 授权或升级成功。

## 升级验收与回到调试

### 恢复完成后的启动失败

#### SSH 后定位到的具体错误与修复

现场 Recovery 是 26.6.2/25G83，bputil 报 `ordinary recoveryOS / Not Paired`，不把它当作实验 stub 的配对 1TR。SFR/current/SystemVersion.plist 已是 25G83。原 Data `B8663CA8-7F9F-4EF7-8947-75F71A14BDA9` 仍为 256GB 容器中的 86151307264 已用字节，FileVault Locked、未挂载；未解锁做逐文件验收。

抓取 `/Library/Logs/DiagnosticReports/panic-full-2026-09-13-182901.5003.panic`。panicString 的直接错误是：

```text
could not validate root hash Authentication error (80)
@apfs_vfsops.c:686
Kernel version: Darwin 25.4.0 / xnu-12377.101.15~1
iBoot version: mBoot-18000.101.7
iBoot Stage 2 version: mBoot-18000.161.10
```

文件外层元数据是新 Recovery 的 25G83 / Darwin 25.6.0；不能将它误读为发生 panic 的内核版本。直接检查证实，旧 NSIH Recovery cache 中的 `arm64eBaseSystem.dmg` 是 symlink：`../../../../../usr/standalone/firmware/arm64eBaseSystem.dmg`。此前 apply 脚本替换了这个 canonical 文件，虽然没有改 cache 目录，却使旧 cache 的引用实际变为新 25G83 镜像；旧 root-hash IMG4/内核仍旧，产生版本混用。**这是本项目资源更新顺序/引用保留的错误，不是原用户 Data 损坏的证据，也不是已确认的 AppleTCON 根因。** 这解释了已捕获的 Recovery root-hash failure；不提前证明解释或解决所有普通系统启动失败。

已执行 `scripts/repair-stub-recovery-link.py --apply`：校验目标 Recovery/container UUID、4GB 容器、设备 ECID、旧 NSIH，以及新旧镜像 SHA-256。将旧 cache symlink 原子改为 `../../../../../usr/standalone/firmware/arm64eBaseSystem-25E253.dmg`，保留原链接为 `.before-root-hash-fix`。旧镜像 SHA-256 `f73e5b13f77e1cea01f573fee958d559b011f72d13602bb5933224bb8abad783` 与 M1 备份 tar 中原镜像相同，修复后再次通过链接读回 SHA 校验。没有更改旧 IMG4、NSIH/coih、全局 SFR 或原 Data。

第一次脚本的 `mount -ur` 只读 remount 被 APFS 拒绝；链接和内容校验已完成，不能据脚本报错说修改没发生，也不能盲目重跑。随后 `diskutil unmount` + `diskutil mount readOnly` 成功，现场确认 Recovery 卷恢复只读挂载，最终结果另存 `raw/recovery-link-repair-final.json`。脚本已改用这套 remount 方式；apply-stub-firmware.py 也已修复未来升级时保留旧 cached symlink 对旧镜像的引用。尚未自动重启，正常配对 Recovery 和 guest 都待复测。

用户确认普通 Recovery 也无法进入。下一项非写入尝试是 **Fallback recoveryOS**：完全关机后，电源短按并松开，立即第二次按住，直到启动选项出现；不同于普通 Recovery 的单次长按，也不同于 DFU 四键组合。入口见 [Apple Boot modes](https://support.apple.com/en-asia/guide/security/sec10869885b/web) 和 [Asahi Partitioning Cheatsheet](https://asahilinux.org/docs/sw/partitioning-cheatsheet/)。先用于诊断和取数据，不能假定它等于实验 stub 的配对 1TR，也不能假定可以执行更改安全策略。如果备用 Recovery 也失败，应回到 DFU 采集/评估非抹盘恢复路径，不自动复用上次刷写命令。M1 usbmuxd 仍运行，USB 查询目前没有目标设备。

用户随后报告反复重启并启动失败。M1 只读检查未见 Apple DFU / Recovery USB 设备，irecovery 无法连接。**整体 revive DONE 不代表正常启动成功**，当前应暂停进一步 bputil/kmutil/guest 实验和重复刷写，优先从长按电源进入 Options/Recovery 收集启动错误、SFR、卷布局和策略。原日志记录了 clear_bootpolicy_nvram、persistent_boot_args、set_boot_command、Recovery restore 等操作；启动选择/策略变化是待检验方向，不是已确认根因。AppleTCON 检查点失败也不能直接认定为启动循环原因。

需要用户先强制关机，再长按电源进入启动选项，选择 Options（不是继续启动 M4 Linux Bootstrap）。如显示 recover volume 选择，先进入原 Macintosh HD 的恢复环境进行只读诊断，不执行重装、磁盘急救或擦除。进入 Recovery 后可用已有 HTTP helper 重新启动临时 SSH；挂载点、IP 和 host key 必须重新核对。

1. revive 完成后按需要恢复启动卷、输入 owner 密码，重新进入实验 stub 的配对 Recovery 并启动 SSH。
2. 实测 SFR 版本；重新解析各卷 UUID 和挂载点，不复用 disk2/disk4 编号。
3. SFR 满足版本条件后，重新执行上面的 bputil 命令，并确认新 NSIH / love。
4. 使用项目 optional-ANS payload 执行 kmutil configure-boot，核验新的 coih；复制 boot.bin 不替代这一操作。
5. 启动 m1n1，保存实际 boot firmware tags；用受保护的 timer 同值写探测验收 VM_TMR_FIQ_ENA_EL2。若仍 fault，停止，不跳过 FIQ routing。
6. 上次上传的 APFS RAM root 已在进入 Recovery 时丢失。每次重新布局、上传并读回 BootArgs、root 和 ADT，再按 Darwin / VM / root mount / launchd / shell 分阶段启动。

原始记录：`experiments/2026-09-13-firmware-update/raw/`。三份备份是实验 stub 的备份，不是原 Data 的全盘备份，也不能代替此前 `~/liqi_backup` 的用户文件备份。
