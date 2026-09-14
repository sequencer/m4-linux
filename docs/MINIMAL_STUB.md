# J713 最小实验启动 stub

## 最新验收：独立 m1n1 启动成功

2026-09-13T16:23:00Z，用户完成新 stub 的配对 Recovery 第二阶段后，M1 已通过 SSH 实际复核：one true recoveryOS、Paired、Pairing Integrity Valid；新卷 SIP disabled、Permissive、Kernel CTRR Disabled、Boot Args Filtering Disabled；coih 为 47B7ABB3D02B066DEFE91D9910C8A1D652556ACCD9AE1330BA12865CA35868D71027768931BE228F1C23049CC844A8FB，.IAPhysicalMedia 已改名为 IAPhysicalMedia-disabled.plist。

通过 SSH 读取 boot.bin，在 M1 计算 SHA-256，匹配固定构建 d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0。确认命名空间 boot-volume 指向新卷组后，M1 执行 sync; reboot。

重启实测成功：1209:316d Generic m1n1 uartproxy unknown，/dev/ttyACM0，串号 M49KYH65C9；日志明确 Model Mac16,12、Target J713、Chip 0x8132、Running in EL2，OS/System FW 为 26.4 mBoot-18000.101.7，实际内存 0x800000000。scripts/m1n1-check.py 的 UART NOP 和 proxy NOP 均成功。目前保持在 Running proxy 状态。

最小 stub 的独立恢复启动与独立 m1n1 启动已验收，原 macOS 正常启动仍未独立验收，Linux 尚未启动。原始输出为 experiments/2026-09-13-minimal-stub/raw/paired-installed.txt、native-proxy-output.txt、native-proxy-check.json。

限制：日志仍显示 MCC Unsupported version:mcc,t8132、cpufreq Chip 0x8132 unsupported、Unknown payload magic 5b41464b、No valid payload found。尚未提供 Linux payload，不能把此次成功描述为 SPTM guest、Linux 内核、GPU 或完整驱动支持成功。Unknown payload 的来源尚未定位。

重要 pitfall：重启后 BSD 磁盘编号重新分配，实验容器变为 disk1、实验分区变为 disk0s3，原系统容器变为 disk4。下文 disk6/disk0s5 是首次准备时的标识，不可用于后续操作；必须按容器和卷组 UUID 重新解析。prepare-minimal-stub.py 的固定初次现场分区断言会拒绝重编号后的现场，不直接重跑它。

以下记录首次准备与配对前状态，已由上述验收更新。

## 2026-09-13 实际执行结果

未安装第二套完整 macOS。仅在新建实验容器中创建 System、Data、Preboot、Recovery 卷组，放入启动资源、所有者恢复信息、Recovery 镜像和固定 m1n1 构建。不复制原 LocalPolicy，也不复制原卷按 ECID 个性化的 apticket。

- 原 macOS：disk0s2/disk3，256GB，用户数据保留。
- 实验 stub：disk0s5/disk6，3999997952 字节，约 4GB。
- 新卷组 UUID：DE77783E-D9C0-4695-8BE1-EBE0D3015748。
- System：disk6s2，M4 Linux Bootstrap，约 1.7MB。
- Data：disk6s1，M4 Linux Bootstrap - Data，约 37KB。
- Preboot：disk6s3，约 143MB。
- Recovery：disk6s4，约 1.6GB；不是完整 macOS 用户空间。
- bputil -g 对新卷组成功；新 LocalPolicy 配对完整性 Valid，Reduced Security。
- bless --setBoot --device /dev/disk6s2 --user liqi 成功。
- 已读取带命名空间的 boot-volume NVRAM，确认默认启动卷组为新 stub。
- 缩容 APFS 检查返回 0，Finished APFS operation；原 ISC、系统 Recovery 和 256GB 容器保留。

新 stub 的 SIP 目前尚未关闭；原 Macintosh HD 的 SIP 已关闭。新卷的最后安装阶段将在其配对 Recovery 中关闭 SIP，再安装 m1n1。

## 已确认的实际阻碍

从原 macOS 的 Recovery 对新 stub 执行 kmutil configure-boot，完成所有者认证后返回退出码 71：

```text
Boot policy error: Error setting permissive security tag: code pairing (17)
```

bputil 同时明确显示当前 Recovery 对新卷是 Not Paired。因此不能把文件准备、LocalPolicy 创建或设置默认启动项称为 m1n1 安装成功。下一步必须实际启动新卷的配对 1TR。

## 新配对 Recovery 的进入方式

已经通过 Recovery SSH 执行 sync; shutdown -h now，返回 Shutdown NOW!，等待用户物理长按电源进入新配对 Recovery。

1. 目标机关机，等待约 10 秒。
2. 一次连续长按电源，直到出现“正在载入启动选项”；不要点按后再重新按住。
3. 默认卷已经设置为 M4 Linux Bootstrap。选择“选项 → 继续”进入 Recovery；如果出现恢复目标选择，选择 M4 Linux Bootstrap。
4. 如果出现 Finish Installation 窗口，可以暂不运行，让 M1 经 SSH 执行并记录最后阶段。该 app 的 step2 已加入 csrutil disable，不会安装完整 macOS。
5. 在“实用工具 → 终端”重新配置 SSH，使用 INSTALLATION_PLAN.md 中的完整 curl 和 sshd 命令。Recovery 的 /tmp 不跨重启保留。
6. M1 登录后必须先执行下面的只读核对；只有同时显示 one true recoveryOS 和 Paired 才继续：

```sh
bputil -d -v DE77783E-D9C0-4695-8BE1-EBE0D3015748
diskutil apfs listVolumeGroups
```

如果仍为 Not Paired，停在 Recovery，检查启动卷选择，不重复盲试 kmutil。若新 stub 无法进入 Recovery，保留现场并从启动选项选择原 Macintosh HD 的恢复环境，不执行 DFU 恢复或抹盘。

## 配对后待执行的命令

```sh
csrutil disable
kmutil configure-boot \
  -c "/Volumes/M4 Linux Bootstrap/Finish Installation.app/Contents/Resources/boot.bin" \
  --raw --entry-point 2048 --lowest-virtual-address 0 \
  -v "/Volumes/M4 Linux Bootstrap"
```

csrutil 如要求选择 OS，明确选择 M4 Linux Bootstrap。完成后复核新卷 SIP、Permissive、coih 非空和 m1n1 二进制 SHA-256，再禁用新 stub 的 .IAPhysicalMedia 并重启，验证 1209:316d 原生 USB proxy 和 NOP。原 macOS 启动也须独立验收。上述配对后命令尚未执行成功。

## 资源来源及可复现性

控制机所有新增依赖通过项目 Nix 管理。asahi-installer-archive 固定为官方 v0.9.1 压缩包，SHA-256 SRI 为 sha256-vFu8qdTFfN86QYxStrQCqErm23dt1a1VZA/bXRGe5LA=，只使用其 Recovery Python 和第二阶段资源，不运行其不支持 M4 的 main 安装入口。

启动资源来自目标机原 Preboot 的 restore：26.4.1/25E253，选择 j713ap、board 0x2C、chip 0x8132 的 OTA 身份。原 SystemVersion 实际读取为 26.6.2/25G83，不能把原 macOS 和当前 Recovery 都写成 26.4.1。

脚本 scripts/prepare-minimal-stub.py 固定目标实验容器 UUID、分区、大小和初始卷 UUID；它不是通用安装器。bootcaches 的 bless2 在此版本没有旧安装器假定的 RestoreBundlePath，实验布局使用现有 restore 路径。匹配 Manifest 的本地文件仍缺以下四个，已如实保留缺失记录；bputil 和 bless 本阶段成功不证明首次启动一定成功：

```text
Firmware/all_flash/applelogo@2x~mac-USBc.im4p
Firmware/dcp/t8132dcp_restore.im4p
Firmware/dfu/iBEC.j713.RELEASE.im4p
Firmware/pmc/t8132pmcfw.im4p
```

已复制匹配的 DeviceTree、iBoot、SPTM、TXM、kernelcache、板级外围 firmware、Bootability 和恢复镜像。没有伪造缺失文件，也没有拿 26.6.2 的同名 firmware 混填。若实际启动失败，缺失项与恢复启动日志是下一步定位依据。

固定 m1n1 PR #1 head 为 7e43bb1763ff97d661bbddb213596eda9475ae6a，boot.bin SHA-256 为 d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0。

参考源码：https://github.com/AsahiLinux/asahi-installer/blob/99dff2e968dafcabc2a940865b051e91ffcfafd3/src/stub.py

固定 m1n1：https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/README.md

实验原始输出位于 experiments/2026-09-13-minimal-stub/raw，包含第一次脚本参数顺序失败、修正后成功、缩容和新策略复核，不纳入版本控制。diskutil info 的 -plist 必须位于设备参数之前；其他 APFS 子命令语法不能直接类推。
