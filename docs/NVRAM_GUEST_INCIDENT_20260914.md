# 13:26 guest 硬重启后 restore 界面：NVRAM 调查

## 修复决策（2026-09-14，本次尚未实施）

重新检查时，M1 的 lsusb 仅有两个 root hub，没有 M4；最后已知 Recovery SSH 地址 172.24.5.124:22 超时。这只说明当前未取得可用入口，不证明机器一直处于 DFU 或永久损坏。本次没有发送启动、清变量、刷机或擦盘命令。

修复优先级是恢复原生 Macintosh HD / Recovery 启动，再继续 guest。不要把补齐输入固件当成本次 restore 界面的修复，也不要再用同一未隔离的 guest 验证机器是否恢复。

1. 若原生 Recovery 或 macOS 可进入：先导出当前 nvram -xp、diskutil apfs list、可取得的启动失败日志，再通过原生“启动磁盘”选择 Macintosh HD，使用本轮有效所有者认证。当前预期原生卷组为 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8，操作前以实际枚举为准。一次性恢复命令、失败状态等仅在读回证明其含义和异常后定点处理；不是看到 panicmedic 就一律删除。先验证原生系统重启和 Recovery，不默认启动 Bootstrap。
2. 若仅有 firmware Recovery USB：现有 query-iboot-diagnostics.py 不带任何修复选项读取 boot-stage、boot-volume、boot-command、one-time-boot-command、failure reason/volume、breadcrumbs 等。读变量不等于可写：历史 setenv 曾返回 PIPE/-9。遇到同样拒绝不继续盲试 saveenv 或清理命令；iBoot 返回的环境也不是完整 NOR bank 备份。
3. 若只有 BootROM DFU：不能直接运行 nvram、SSH 或任意 m1n1。临时签名诊断启动尚未在本机验证成功，不应声称是现成无写入修复工具。以恢复可用性为目标时，优先此前实际成功的 macOS Finder host；先完成一次非抹盘 Revive，若仍失败保留该次日志后再决定 Restore。历史 Revive 失败不证明本次必然失败，也没有依据保证 Revive 会重置指定 NVRAM 键。Restore 会抹盘，是后备而非默认动作。官方步骤：https://support.apple.com/en-us/108900 。

不能把启动前 64KiB proxy 原样刷回 NOR：它不是完整 1MiB 多 bank 备份，且旧 boot-volume 指向实验 Bootstrap；只回滚变量也不能保证与当前 SEP/LocalPolicy 状态一致。当前没有证据支持擦除 NOR、清空 NVRAM、重放 iSC 或继续关闭安全措施作为修复。

防止重现的最小研究方向：下一次可运行时针对已定位的 AppleARMNORNVRAM 写/擦除入口取得调用者和内容证据，研究 guest 私有的读写一致 NVRAM。仅打印 QSPI 事务不会阻止写，直接吞掉所有 QSPI 写会同时破坏读命令协议；删除 ADT 节点也不是硬件隔离。该修复尚未实现，不能宣称它单独即可隔离 SEP 等其他持久状态。停止把 hv.reboot 当作正常 guest 退出；正常关机也可能同步 NVRAM，不能用正常关机替代持久状态隔离。

## 本次时间线和排除项

本次使用的是重装后新采集的 iSC 副本及 25G83 资源。guest 已运行到 Options，输入固件下载器未完成。13:26 左右通过现有 HV shell 执行 `hv.reboot()`；console 最后记录 `Hard rebooting the system`。主机内核 13:26:29 记录 USB 断开，随后未见 m1n1 ACM 串口返回。用户报告循环重启，后来显示 support.apple.com/mac/restore。13:28:31–13:28:36 sysfs 短暂观察到本机序列号的 05ac:1905 / Mac；这不是本次 iBoot 错误码或 Recovery GUI 验收。

新准备的 FAT 固件资源盘、IMG4 文件、serial=3/-s 启动方案均未上传、未运行。不能将故障归因于这些新输入。本次也没有重复 LoadingGroup→OSString 的错误解码；这与新 iSC 条件一起说明，旧副本和错误指针读取均不能作为同类故障的唯一解释。

`hv.reboot()` → proxy `P_REBOOT` → `start.S:reboot` → `wdt_reboot`。固定源最后写 watchdog ALARM=0x100000、COUNT=0、CTL=4，是整机硬复位，不是 guest 正常 shutdown，也不是原地重建虚拟机。它是否是唯一原因尚未证明。

## 已证实：真实 NOR NVRAM 没有隔离

本次保存的 guest.adt.bin 含以下完整路径：

```
/arm-io/qspi                         compatible=qspi,qspimc
/arm-io/qspi/spinor                  compatible=nor-flash,spi
/arm-io/qspi/spinor/anvram           compatible=nvram,nor
/arm-io/qspi/spinor/firmware         compatible=iboot,boot
```

QSPI 首个 MMIO 地址为 0x3ad118000，长度0x4000。anvram 的两个32位 reg字段为 offset=0x700000、size=0x100000。本机是 qspi 路径，不能照搬旧 M1 的 spi1 路径。

本次 IORegistry 已有 qspi→spinor→anvram→子服务，以及 options-common/options-system。固定 HV.init 把 arm-io ranges 以 TraceMode.OFF 注册；pt_update 对 OFF 调用 map_hw(IPA,IPA,size)，是实际硬件直通，不是禁访问。launcher 只去除了 ANS/NVMe 和部分显示节点，没有把 QSPI/NOR/NVRAM 虚拟化。

固定25G83内核 AppleARMPlatform 反汇编进一步确认：

| 方法 | 地址 | 已确认行为 |
| --- | --- | --- |
| AppleARMNORNVRAM::write | 0xfffffe0008aca630 | 参数/边界检查后调用底层 NOR 方法 |
| write 中的调用点 | 0xfffffe0008aca698 | 错误日志明确称 _norNFDevice device writeBytes() |
| AppleARMNORNVRAM::eraseBank | 0xfffffe0008abeaa0 | bank index×bank size 后调用底层擦除方法 |
| AppleARMNORFlashDevice::writeBytes | 0xfffffe0008a878dc | NOR 设备写接口 |

因此“只用了 RAM 根盘、没显式写 SSD，所以不会影响下次原生启动”不成立。guest 有真实持久状态写入通道；但本次没有 QSPI 写事务抓包，不能把通道存在升级为已经抓到具体写入。

## guest 前的可用基线

从已保存的启动前 ADT 导出 nvram-proxy-data，共65536字节；nvram-current-bank=11，bank-size=65536，bank-count=16。nvram-raw 属性是整数1，不是一份原始 NOR 镜像。

副本保存在 `/home/sequencer/m4-linux-backups/20260914-resources-rerun/nvram-before-guest/`，权限限制访问，未计算 hash。它是继承的启动前 bank proxy 数据，不是故障后的读回，也不是完整1MiB NVRAM备份。

对照 Apple 公开 IONVRAMV3Handler 的 packed header，解析得到 generation=124；已解析31条记录，停在0x1387，未验证CRC，不宣称完整无误枚举。状态0x7f的相关记录为：

- auto-boot=true。
- boot-command=fsboot。
- boot-volume 末段为本轮 Bootstrap 卷组 530FE39B-6AE3-47D0-9168-29F1A7EE2763。
- namespace=40A0DDD2-77F8-4392-B4A3-1E7304206516。

可据此建立前后对照，但不能在没有故障后数据时声称某键已经改变；未枚举到的键也不能直接宣称不存在。

## 不能混淆原因和结果

离线子任务对25G83 iBoot的部分分支解码指出，iBoot失败处理本身也会写恢复状态：0x100c1a9c2ac附近保留已有recovery-boot-mode，缺失时设置失败原因并写iboot；0x100c1a9c3a8附近选择recover/recover-system，0x100c1a9c3e8调用保存入口。这里是静态分支，不是本次执行跟踪。

所以后续若看到 recovery-boot-mode、boot-command=recover-system 或 panicmedic，必须区分：

1. Recovery guest 在运行期间修改了真实 NVRAM，改变下次启动。
2. 硬重启或其他状态问题导致原生启动失败，iBoot随后写入恢复变量；这些变量是结果。
3. NOR内容/有效bank问题、SEP与RAM iSC状态不一致、恢复资源问题等其他路径。

当前没有证据把第三类定案，也未确认一个独立名为 efienv 的物理位置。精确对象应以本机 anvram 分区、NVV3 bank、变量namespace与具体键名为准；不要笼统把EFI环境、iBoot内存env、NOR变量和LocalPolicy当成同一存储。

凌晨历史实例的reason=3/panicmedic属于旧Bootstrap DE77783E-…，不是这次读回。此前静态reason3的一条路径涉及rpnh，不是已证实的nsih错配；不能拿历史错误码解释本轮。

## 下一项有区分力的证据

- 故障后的NVRAM相关键、有效bank/generation与启动前proxy进行对照；读取优先于清理。
- 同次iBoot的failure reason、failure volume、failboot-breadcrumbs和reset原因，判断变量是故障前写入还是失败处理后的结果。
- 若以后恢复实验，记录 NOR 写/擦除调用及调用者，或使用实际读写模拟的影子NVRAM；单纯删除节点或只记log不等于隔离，直接丢弃所有QSPI写也会破坏读协议。
- SEP/SMC及其他持久通路仍须独立分析。没有具体差异前，不运行nvram -c、不清LocalPolicy、不回写整块NOR。

本次调查未再操作目标机。原始证据位于 `experiments/2026-09-14-reinstall-retained/raw/restore-screen-reverse/` 和 `raw/reboot-incident-1326/`。

参考：[Apple公开IONVRAM实现](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/Kernel/IONVRAM.cpp)、[NVV3格式及写入实现](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/Kernel/IONVRAMV3Handler.cpp)、[Asahi启动变量说明](https://asahilinux.org/docs/fw/nvram/)。公开main用于解释机制，不冒充固定25G83逐字源码；本机地址以本地反汇编为准。
