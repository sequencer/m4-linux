# 25G83 实机 SPTM HLE guest 实验

日期：2026-09-13。目标：Mac16,12 / J713 / t8132，32GB M4 Air。控制机：Asahi M1，依赖由 Nix 管理。

## 最新：APFS 直接 RAM 根盘分类诊断

### 本次回退与 SSV 修改门槛（21:18 UTC）

启动验收进一步完成：21:22:13 Recovery普通reboot后直接出现1209:316d及ttyACM0，fresh HV.init/NOP和timer同值写读回0xf通过；再由m1n1执行NOP/P_REBOOT，21:22:36又直接回到m1n1，重复preflight通过。这证明修正策略后的两次无guest启动链可用，不证明先前guest panic导致的回退根因已全部解决，也不证明guest运行后USB/重启稳定。新BaseSystem adapter实验已使用新日志路径启动，仍保持System auth blob和snapshot不变、移除guest SSD。

21:21 UTC后续：用户物理长按进入one true recoveryOS/Paired/Pairing Integrity Valid；对Bootstrap执行同一bputil -s命令，交互认证后退出0。两次策略显示SSV Disabled/sip1=1，coih/nsih未变，lpnh更新76A87952810466E7611B530561F1F7203A18BE38A92AFAEC21FFF115C7AA20A53FBDBF86AD2F5E7FAC354A8166BD49DA。原安装SSV仍Enabled、Data仍Locked/unmounted。已保存独立readback，执行sync/reboot开始验证直接返回m1n1；未重装、未清NVRAM。此处仅证明策略修改成功，启动稳定性和guest图形界面尚需实测。

Recovery SSH已实际连通，25G83日志再次为ssv-seal-broken。nvram boot-volume和bless --getBoot均指向Bootstrap；System UUID C497C0B2...，Sealed No、无snapshot，LocalPolicy仍SSV Enabled/sip1 absent、coih/nsih未变。原Data仍Locked/Not Mounted，用量86151307264bytes，没有解锁或写入。fsck完整日志解释此前result=65为已写挂载容器使用了不兼容检查模式，要求-l；这不是损坏证明。新ResetCounter为reset count=1、boot failure count=0、target_off_restart，不能沿用旧boot failure计数。

仅对Bootstrap执行bputil -s -v DE77783E-D9C0-4695-8BE1-EBE0D3015748；交互所有者认证通过，但命令退出255、错误11。统一BootPolicy日志明确为bootpolicy_update_local_policy_boolean_tag: exit: AP boot mode (11)。读回策略仍SSV Enabled且nsih/coih未变。需要正常关机后物理进入1TR；不能在自动普通Recovery反复尝试或用-n/-g重建全部策略。SSV配置不一致是必须处理的启动前提，但尚未通过对照证明关闭它可消除所有回退。证据目录experiments/2026-09-13-recovery-seal/。

后续用户确认 watchdog 重启再次进入原生 Recovery，并报告 UI 提示“OS的当前实例与Apple预期的实例不符，请重新安装macOS”。这是当前回退的直接 UI 证据，与前次 ssv-seal-broken 日志相容，但本次日志尚未采集，不能断言具体失败卷或 guest panic 到固件回退的因果链。SSH 当前22端口拒绝连接。应先采集本次 recoveryos/fsck/ResetCounter 和按UUID区分两套安装的策略、seal、启动目标，再修复独立 Bootstrap；不直接重装原 macOS。历史 fsck_apfs 有 result=65，需要完整错误上下文，不能忽略或直接等同Data损坏。

用户重新进入 m1n1 后，proxy/timer preflight 通过；同一 25G83 KC、16GiB、10核、移除 guest SSD 控制器的 RAM 根盘实验再次到达 APFS。新 `--inspect-apfs-root` 在 `0xfffffe000b443a6c` 放置一次性 BRK，命中后恢复原指令 `0xb9406be8` 和缓存。初版 hook 错用不存在的 `sp_el1` 属性，触发 host 异常并进入可交互 HV shell；已修正为 `context.sp`，本次状态由 shell 手动保存，不能宣称修正版已在下一轮验收。

现场：EL1t 的活动栈是 `context.sp[0]`，不是 regs[31]；w23=1、[SP+0x68]=0、already_rooted=0。该处 ORN 是 `w8 OR NOT w23`，不能误读成 OR。仅将 guest already_rooted 置1再继续，仍出现 `The global payload bytes pointer is NULL @apfs_vfsops.c:2893`，所以单改该变量不足以进入 BaseSystem 根挂载。

panic 后读取保存的 NX/volume 对象：NX+0x166 的虚拟标记为0，NX+0x238 的设备指针为0，volume superblock 的 role=1。结合本版 `_nx_is_virtual` 反汇编，缓存位不置且设备为空会返回 false，因而未进入 `_handle_basesystem_rootmount` 的 BaseSystem auth blob 导入路径。这里证明的是这条分支的分类阻塞，不是所有 APFS 问题已解决；普通 Recovery 使用 root-dmg/imageboot pivot，直接 rd=md0 并未复制该初始化流程。

下一轮可以在新启动中对真正 RAM-backed NX 做受严格版本检查的分类适配，继续执行原 BaseSystem 认证代码；不能在已失败的挂载栈上回退执行，也不能 NOP seal/assert 或凭 root hash 伪造不存在的 snapshot。本次 proxy NOP 仍正常，guest 暂停在 panic，尚未 root mount、launchd 或图形界面。证据见 `experiments/2026-09-13-direct-root/STATUS.json` 和该目录 raw 日志。没有磁盘或 boot policy 写入。

## 重启后的10核对照

### 后续自动Recovery的实机证据（20:59 UTC）

用户报告重启自动进入Recovery。SSH只读采集：25G83 ordinary recoveryOS / Not Paired；recoveryos.log明确 `Recovery Boot Mode is Set: ssv-seal-broken`，ResetCounter boot failure count=1、entry reason Unknown、button reset/sequence timeout。日志说明回退模式，但没有新的内核panic报告可确定最初触发路径；不能把它直接等同于先前guest APFS panic，或宣称数据丢失。

stub策略仍为Permissive/sip0=7f，NSIH/coih与安装时一致，SSV状态仍Enabled。只读挂载独立stub Preboot并下载实际CustomKC，SHA仍为3c02fa...，唯一raw payload位于offset74且与Nix779c9a...逐字节匹配。没有重新configure-boot、改策略、清NVRAM或自动重启。原Data仍Locked/Not Mounted、已用86151307264bytes；原System在Recovery只读挂载且显示Sealed Broken，不能将该状态扩展为Data完整性结论。

重要反证：`diskutil apfs listSnapshots` 对当前BaseSystem和stub System均返回No snapshots。实际stock Recovery参数是 `-rootdmg-ramdisk root-dmg=file:///.../arm64eBaseSystem.dmg`，不是guest的直接 `rd=md0` 路径。因此撤销launcher中以BaseSystem根哈希拼接并改写snapshot名称的未经验证假设：root-auth选项现在仅记录digest/核对payload并实验性调整guest System auth blob，不伪造snapshot存在，也不宣称能独立修复挂载。正常stock Recovery UI不算SPTM HLE guest GUI目标完成。

证据见experiments/2026-09-13-auto-recovery/STATUS.json及raw日志。此Recovery非配对，不能直接重做kmutil/csrutil；先显式选择实验stub启动，若仍自动回退，再采集失败后判断是否需配对1TR调整SSV策略，而不是重装。

用户物理重启后preflight再次通过。保持16GiB和完全相同kernel/root，仅将cpus=1改为cpus=10，实际越过ApplePMGR complex REQUIRE。记录了九个secondary guest启动请求，HV started_cpus列出10个CPU；这不自动等于所有CPU完成XNU online验收。随后进入APFS根挂载路径，panic变为 `The global payload bytes pointer is NULL @apfs_vfsops.c:2893`。尚未进入userspace或图形界面。

PTY交互有效，可获取context、BootArgs、chosen和started_cpus。hv.exit()后观察到逐个CPU退出、All CPUs exited、Python start返回，进程退出码0。**退出guest已验证，不等于USB proxy可供下一次使用。** 后续launcher卡在bootstrap的iodev_whoami写入，PTY中断后没有启动guest。主机USBDEVFS_RESET遇到descriptor error -71 / setup address不响应，tty消失，未恢复proxy；需物理重启，不重复堆积进程。

APFS输入进一步核对：live `/chosen/secure-boot-hashes/base-system-volume-auth-blob` 与官方 `022-22048-093.dmg.aea.root_hash` 的csys IM4P payload逐字节一致（208bytes，root-hash文件SHA `577661fd264e5745736d4d31ff14598c5ad1f7360fad5092f79ac04b7562e8d9`）。因此不能简单说官方Recovery root-hash未下载。guest仍继承普通stub的system-volume-auth-blob和root-snapshot-name（605874...），不是Recovery的1A0E71...根哈希。

新增实验选项 --recovery-root-hash/--recovery-root-hash-sha256，严格验证DER/header/hash与live BaseSystem blob一致，再仅修改guest RAM ADT的system blob和snapshot名称。此路径只完成离线验证，尚未实机执行。BaseSystem是否实际具有按此哈希命名的snapshot尚未证实；raw扫描也未找到com.apple.os.update名称，不能把推导名称当作snapshot存在证明。

还须验证直接把BaseSystem APFS作为初始rd=md0根盘的挂载分类。[Apple XNU imageboot.c](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/imageboot.c)的BaseSystem pivot显式传入KERNEL_MOUNT_BASESYSTEMROOT；同版本APFS反汇编中handle_basesystem_rootmount依赖虚拟容器及already_rooted条件，并选择base-system-volume-auth-blob。普通初始System mount可能没有走该路径，是下一步假设，不以“改一个snapshot名”假称完整修复。在线源码main仅作架构参考，现场地址/行为以25G83反汇编为准。

本轮原始日志、ADT、离线反汇编在 `experiments/2026-09-13-cpu-complex/raw/`，机器可读汇总在同目录父级STATUS.json。后文16GiB单核暂停现场均为历史记录。

## 已验证的进展

持久化 optional-ANS m1n1 已实际启动，USB proxy 可用。读取的 system firmware、iBoot stage one、stage two 均为 `mBoot-18000.161.10`，不是仅下载或安装资源后的版本推断。

`VM_TMR_FIQ_ENA_EL2` 的 MRS、原值 MSR、读回均成功，值为 `0xf`；`HV.init` 和其后的 proxy NOP 成功。旧固件的这个 timer 写入阻塞已解除，但全局 `apple_sysregs_unlocked` 仍为 false，不能据此把所有 Apple 寄存器强制标为解锁。

代码基线为 [ADevWithAnIdea/m1n1#1](https://github.com/ADevWithAnIdea/m1n1/pull/1)，commit `7e43bb1763ff97d661bbddb213596eda9475ae6a`，加本项目 Nix optional-ANS patch。这里运行的是 SPTM **HLE**，不是已完成 Apple 原生 SPTM handoff 或 Linux MM 的实现。

## 输入和隔离边界

- 25G83 Mach-O kernel：SHA-256 `f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d`。
- 纯 APFS Recovery RAM root：1574961152 bytes，SHA-256 `bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a`。
- 两次启动均删除 guest `ans` 节点；RAM root、BootArgs、最终 ADT 都经实机读回核验。没有在本轮挂载原用户 Data。
- 第二次仅在 RAM 中缩小 guest 声明内存；没有修改持久化启动配置或磁盘分区。这不是完整 32GB 支持。

## 第一次：完整内存失败在 HLE 初始化

HLE 在 `hv_sptm_boot.c:230` 触发：

```text
Assertion failed: 'sptm_boot.page_count < ARRAY_SIZE(sptm_boot.pages)'
```

源码 `SPTM_BOOT_MAX_TABLES=1024`，每张页表 16KiB，映射按页建立；辅助区预算另为 64MiB。现场证明页表池上限被触发，没有证明 XNU 已执行。随后 USB 断开、主机脚本退出，目标重新启动持久化 m1n1。

修复必须同时核算完整内存映射、其他 aliases、frame/external-ref metadata 和辅助区容量，不能只删除断言。精确耗尽发生在哪个映射范围尚未插桩确认。

## 第二次：16GiB 对照进入 XNU，停在 ApplePMGR

`--guest-memory-gib 16` 将本次 BootArgs 的内存声明限制为 17179869184 bytes。HLE 初始化通过，跳转 entry `0x10025e84000`，观察到 PMGR MMIO 和 XNU panic：

```text
HV: SPTM XNU panic owner CPU0 (HV CPU6)
ELR=0xfffffe000c078bdc LR=0xfffffe000b78dac8
ApplePMGR::enableCPUComplex(UInt32, bool):4834
REQUIRE failed: complex < _cpuComplexCount
```

这是本台 M4 上实际执行 XNU 的证据；不是 Darwin banner、root mount、launchd、Recovery shell 或 macOS 桌面成功。Linux 也没有启动。

最终 guest ADT 有 10 个 CPU、两个 cluster（6E+4P），命令行为 `cpus=1`，实际 boot owner 对应 HV CPU6 / P cluster。HV 的 `smp` 默认为 true，不能把问题错误归因于显式关闭 HV SMP。下一步检查 boot CPU、单核参数和 ApplePMGR CPU-complex 初始化的相互作用；目前没有读出 `_cpuComplexCount`，拓扑不一致只是待验证假设，不是确定根因。不要直接 NOP REQUIRE 或伪造 cluster 编号。

## 现场控制 pitfall

第二次主机命令没有 PTY，stdin 已关闭。panic shell 在 EOF 下反复返回并重新打开，导致日志刷屏；`write_stdin` 不能向已关闭的 stdin 注入命令。

已保存首个 panic/回溯。SIGUSR2 退出请求没有确认生效；主机 Python PID `913527` 曾以 SIGSTOP 暂停。后续仅针对 M1 主机进程的 GDB stdin 修复失败：SIGSTOP 打断函数调用，重试时 open 返回 fd0，又被 close，最终原 Python 因 Bad file descriptor 退出。该失败没有修复 guest，也不能把 GDB 批处理退出码0当作每步成功；失败日志已保留。

随后独占串口尝试协议级退出，尚未取得首个 NOP 应答；主机进程 `918221` 收到 TERM 后最后观察为 D 状态。**没有确认 guest 退出或 proxy 恢复，禁止并行打开另一个 proxy。** 需要用户物理重启进入持久化 m1n1，并重新检查 USB及串口所有权。PID 是本次现场信息，后续须重新检查，不能长期硬编码。失败的临时 stdin bridge 已移除，不作为推荐恢复方案。

launcher 已增加非交互启动拒绝检查。后续实际启动须使用 PTY（工具 `tty=true`）；仅上传核验可使用 `--prepare-only`。此次失败现场不会被新脚本检查自动修复。

下一轮控制变量选项已添加：`--guest-cpus 10`，默认仍为1，并将完整命令行与 CPU 请求数写入实验 JSON。这仅准备比较测试，尚未实机验证，也不保证 secondary CPU 路径正确；保留16GiB和相同kernel/root，避免同时改变内存与CPU变量。

最后复核：协议退出进程918221已终止，回溯显示首个NOP卡在serial write，EXIT_GUEST实际未执行。USB仍枚举1209:316d，不等于proxy响应正常；无需等待该进程，须物理重启目标。主机代码编译及diff检查通过。

## 证据与复现边界

### 后续离线定位：实际失败的参数与字段

使用 Nix ipsw 对同一 SHA 的 kernelcache 读取 ApplePMGR symbols 并反汇编，未修改内核。`ApplePMGR::enableCPUComplex` 入口是 `0xfffffe0009835814`，开头读取 `w9 = *(uint32_t *)(x0 + 0x3f158)`，比较 `w1` 与 `w9`，unsigned `b.hs` 跳入已捕获的 cold.1 REQUIRE 路径。因此该版本的 `_cpuComplexCount` 检查字段偏移可以绑定为 `0x3f158`，不应跨版本复用。

回溯中的调用点 `0xfffffe0009c35028` 前明确设置 `w1=1`、`w2=1`，通过虚表调用；结合 enableCPUComplex/cold.1 的回溯，失败请求是启用 complex 1。这将现场条件收窄为 count <=1，但尚未实机读出 count，不能直接断言 count=1或cpus=1就是最终根因。邻近之前的调用请求 complex0；仅靠离线代码不能额外宣称该调用的运行结果。

panic ELR `0xfffffe000c078bdc` 属于内核 panic hook 周围，不是 ApplePMGR 的比较指令；诊断时应使用回溯找到入口/调用点，不能在panic ELR误读参数x0/x1为原方法参数。下一轮可在有上下文的HV shell设置函数入口断点，读取入口x0、w1和对应字段，再验证10核参数是否恢复两个complex。

原始文本保存在 raw/pmgr-symbols.txt、pmgr-enable-entry.txt、pmgr-caller-disassembly.txt、pmgr-platform-caller.txt 和 pmgr-panic-disassembly.txt。所有地址绑定25G83和本次无额外slide的日志，后续通过符号解析核验实际地址。

汇总：`experiments/2026-09-13-new-firmware-guest/STATUS.json`。

原始证据在同目录 `raw/`：`preflight.json`、`preflight-root.log`、`preflight.adt.txt`、`guest-attempt.json/log`、`guest-16g.json/log`、`guest-16g-first-panic.txt`、`guest-topology.txt`。首次非 root preflight 权限失败也保留。raw 文件被 Git 忽略，保存在本机不等于已提交或异机备份。

下一轮在取得独占串口且恢复可控 m1n1 后，使用相同 pinned kernel/root 和 PTY，先验证 CPU-complex 假设，再单独修复完整内存的页表池/辅助区预算。所有物理地址依现场重新计算，不能跨重启照抄。
