# M4 上的 SPTM 与 macOS 调试启动

## 结论

M4 Air 上继续实现 m1n1 控制的 macOS 调试启动有实际价值，现有失败不是“SPTM 路径完全不可用”的证据。但目前不能把任何一次实验称为 macOS 启动成功，也不能用关闭更多 SIP 或删除定时器逻辑代替正确的启动环境。

最优先的问题是 **boot firmware 的寄存器解锁前提**。本次 stub 资源为 26.4.1/25E253，而开发者在 IRC 中报告 VM_TMR_FIQ_ENA_EL2 从 26.6 beta 才解锁。其次，当前 Recovery launcher 将 RAM disk 放在 host heap，只补了 stage-2 映射；SPTM HLE 的 guest physmap 不包含该区域。还需确认根盘是 APFS 分区而非整张 GPT 磁盘。

研究建议采用两条并行但不能混称的路线：短期继续固定 PR #1 的 SPTM 高层模拟，争取 RAM-only Darwin shell；长期跟踪 Sven 的 SPRR/GXF 模拟与 Apple 原始 SPTM 加载路径。前者有助于硬件逆向，后者更适合观察真实 SPTM 行为。

## 证据与适用范围

这里区分四种证据：本台实测、离线输入检查、固定源码的静态分析、开发者在公开项目/IRC 中的报告。静态分析所得的下一阶段风险不等于已经在本台触发了第二个 panic；其他机型的成功报告也不直接等于 J713 成功。

本台为 Mac16,12/J713/T8132、32GB RAM、2TB SSD。实验 stub 卷组为 DE77783E-D9C0-4695-8BE1-EBE0D3015748，约 4GB；它提供独立 Recovery 与持久化 m1n1，但没有完整第二套 macOS 桌面。原 macOS 卷组为 B8663CA8-7F9F-4EF7-8947-75F71A14BDA9，原用户 Data 仍保留。

审阅基准为 2026-09-13。以下移动分支均解析为具体提交；不把今天的分支名作为后续实验的唯一身份。

| 项目 | 本次核对的版本 | 状态/作用 |
| --- | --- | --- |
| ADevWithAnIdea/m1n1#1 | 7e43bb1763ff97d661bbddb213596eda9475ae6a | open、Draft；head 未更新；提出者 Niklas Sheth/niklassheth，目标是 Cody Ho/ADevWithAnIdea 的 fork |
| 本项目 m1n1-sptm | 上述 head 加 flake.nix 的 optional-ANS/SART 补丁 | 第二轮 RAM chainload 构建；不是未经修改的 PR 输出 |
| AsahiLinux/m1n1 main | b4654b32941d51afdb77579d63e7cb1aa6c03ecc | 最新提交为 09-10 的 NVMe tracing 名称修正；不包含 PR #643 的完整模拟文件 |
| AsahiLinux/m1n1#643 | 1c98fd09817cede0043d25c95fb540dbd683ef18 | open、非 Draft；实际分支 AsahiLinux/m1n1:hv-sprr，作者 Sven Peter/svenpeter42 |
| AsahiLinux/m1n1#646 | 已合并 | #643 的准备修改，不是完整 SPTM loader |
| Apple 公开 XNU | f6217f891ac0bb64f3d375211650a4c1ff8ca1ea | main 提交日期 2025-10-16；用于解释机制，不等于本次 25E253 二进制的精确源码 |
| jprx/darwin-vm | 28c6d27e401bd60299bbb6c69667deeba669b810 | 09-12 提交；独立 QEMU/Darwin shell 参考 |
| jprx/qemu-sptm | 2867d847d3471560e773120ee50c42dbcbb6d60b | darwin-vm 固定的 submodule；不是 m1n1 的 native MMIO tracing 路线 |

PR 和状态来源见 [^1]、[^2]、[^3]；其余机制在下文分别指向固定源码。

## 三种“用 SPTM 启动”的区别

### Apple 原生启动链

Apple 启动固件识别 XNU 后，会先准备 SPTM 的 guarded execution 环境，再把 XNU 交给它管理。SPTM/TXM 用受保护的执行域处理页表和相关内存操作；XNU 本身不再拥有传统裸机内核假定的全部页表控制权。SPTM 是 XNU 的启动和运行依赖，而不是一个给 kmutil 添加的普通开关。[^4]

把 m1n1 作为 raw boot object 安装，解决的是“启动自定义 payload 并得到 proxy”。它不等于原生 Apple SPTM 已经在 guest 所期待的环境中运行。反过来，强迫启动固件把 m1n1 当 XNU，并不能保证 m1n1 可以继续进行自己的内存管理。[^4]

### PR #1：SPTM HLE

现用 PR 的做法是构造 XNU 预期的 handoff、初始页表、frame metadata 和子系统状态；将 XNU 中的相关指令改为 HVC，再由 EL2 的模拟实现处理调用。这里的 hv_sptm_init 成功，指的是 **本项目采用的 HLE 初始化成功**，不是 Apple 原始 SPTM firmware 启动成功。[^5][^6]

固定代码中，sptm_boot_init 从 guest ADT 的 BootArgs 和 Kernel-mach_header 读取地址，建立 TTBR0/TTBR1，并编程 guest EL12 别名寄存器。sptm_boot_prepare_start 改写 entry 和 x0..x3：x1 指向 bootargs，x2 指向模拟的 bootstrap，secondary 标记放在 x0。这解释了为什么单独给 p.hv_start 一个 kernel entry 并不足够。[^6]

该路径目前是本台最快可继续实验的起点：源码、构建、内核输入和失败日志已经在 M1 项目中。但它只能作为兼容性/调试模型，不能据此研究真实 SPTM 的全部验证规则或把虚构的成功返回当作 Apple 安全语义。[^5]

### PR #643：SPRR/GXF 模拟后运行原始 SPTM

Sven 的公开实现位于 src/hv_sprr.c、src/hv_sprr.h 和 Python hv/sprr.py。Python 把 genter/gexit 和一组 banked/permission sysregs 改为 HVC；C 侧维护 guarded context、shadow 页表及权限状态。固定实现只支持 16K 页表粒度，源码明确排除 Rosetta 的 4K 路径。[^7][^8]

官方进展报告描述了利用此类模拟加载 Apple 原始 SPTM、再运行 XNU 的成果；但 **公开的 PR #643 本身没有给出完整 SPTM/TXM 加载、启动 handoff 和适配 M4 的一键流程**。它的 run_guest.py 仍以单一 Mach-O payload 为主要入口，没有专门的 --sptm/--txm 输入；不应把通用 emulator 等同于完整 loader。[^4][^9]

IRC 07-31 21:57–21:58，Sven 表示公开 PR 已可用于 PPL，而 SPTM bring-up 还需整理，并协调其指导的硕士学生的发表安排。08-28 16:15 他又明确当时该成果只在 M1 工作，接下来才调整到 M4。这样读，官方公告、公开 PR 和当时的 M4 状态并不矛盾。[^10][^11]

## 本次异常到底发生在哪里

第二轮 guest 已经过 optional-ANS 修正，完整 Recovery image 已上传，SPTM HLE 初始化返回，输出 Jumping to entrypoint at 0x10094804000。随后目标在 EL2h 出现异常并自动重启；没有 Darwin banner、Recovery UI 或 guest shell 的验收证据。

| 项目 | 实测值 |
| --- | --- |
| fault PC | 0x100040ea3b8 |
| 相对 m1n1 binary 偏移 | 0x163b8 |
| ESR | 0x02000000；EC=0、IL=1 |
| 指令 | 0xd51df160，msr s3_5_c15_c1_3, x0 |
| 寄存器 | VM_TMR_FIQ_ENA_EL2 |
| 所在路径 | hv_update_fiq 的 guest CNTP 未 pending 分支，重新设置 ENA_P |

保存的反汇编在故障之前显示 mrs 同一寄存器、orr x0,x0,#2，再到失败的 msr。因此本次证据是 **该路径中的读成功、写失败**，而不是该寄存器完全不可访问。故障在 hypervisor 自己执行的 EL2 指令，不是一个可以交给 guest sysreg handler 正常返回的 EL1 trap。[^12]

本次二进制 SHA-256 为 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4；它是 optional-ANS 构建。持久化原始 PR 构建仍为 d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0。目标自动重启后双 NOP 再次通过；本轮研究没有改变这些启动对象。

## 为什么固件比删除 FIQ 写入更优先

IRC 08-27 07:05，yuka 指出该寄存器的解锁最早出现在 26.6 beta。08-28 15:15，Sven 准备安装 26.6.2；当天在 M4 Pro 上测试后，16:04–16:05 澄清其与 IPI 寄存器的区别，并确认对应 timer 寄存器 mrs/msr 可工作。该证据支持“可写性依赖启动固件”，但尚不是本台 T8132/J713 的复测。[^11][^13]

本台保存的初始 m1n1 输出明确记录 OS FW/System FW 为 26.4、mBoot-18000.101.7；live chosen ADT 的 stage-one、stage-two 和 system-firmware tag 也相同。stub 的 restore resource build 是 25E253。这里的 26.4 标签来自固定 PR 的 firmware.c 映射；还应保留实际 tag，而不是只保存人类版本号。

同时，本地 BuildManifest.plist 中可见 iBoot-13822.101.1~37 的资源元数据，与 live mBoot tag 并非同一字符串。这说明 **资源清单与实际执行的 boot stage 必须分别记录**；不能据某个文件存在就认定本次已经运行它。下一轮应核对各 stage 的真实来源与哈希，而不强行把标签差异解释成已证明的具体混配错误。

原裸 macOS 与 restore-staged 中已有 25G83 输入，并不证明 stub 从 25G83 启动。RAM chainload 新 m1n1 不会重新执行新 boot firmware 的解锁流程；换 guest kernelcache 也不会解除之前留下的寄存器锁。

因此优先候选是 **完整匹配、实际采用的 J713/T8132 26.6.2 启动资源链**，再按能力验收决定是否运行 guest。并不建议在现有 25E253 目录里把几个同名新版文件覆盖过去，也不建议本轮为了研究直接迁移启动策略。

### 不能用一个全局 feature 布尔值判断

固定 PR 的 features_m4 是静态 CPU feature 描述，没有设置 apple_sysregs_unlocked。它不是逐寄存器探测结果。新版固件即使单独解锁 VM_TMR_FIQ_ENA_EL2，该全局字段仍可能为 false。[^14]

所以两种快捷修正都不合理：把所有 Apple sysregs 标为 unlocked，会使许多真实锁定寄存器进入直通路径；以全局 false 为条件跳过所有 timer routing，则可能在本来能写的固件上丢失中断管理。正确的设计应单独表示 timer routing 能力，并在不满足前提时明确拒绝启动，或采用经过验证的替代模型。

## timer/FIQ 为什么不能简化成几行 NOP

当前 main 和 PR #643 均仍无条件读改写 VM_TMR_FIQ_ENA_EL2，并没有可直接借用的 locked-register fallback。[^15][^16]

该机制不仅是“打开定时器”：它检查 guest architectural CNTP/CNTV 的 pending；pending 时关闭相应硬件 FIQ 路由以避免 level 持续打断 EL2；把 timer、IPI 和 PMC pending 汇总，并通过 HCR.VF 注入 guest。删除整个函数会连其他虚拟 FIQ 来源一起破坏。[^12][^15]

现用 HLE 另外已有软件 Apple KERNEL_CNTV 模型。它保存 CTL/CVAL，处理 TVAL 的有符号 deadline；把 Apple 24MHz 时钟域换算到 architectural CNTFRQ，通过 host CNTP timer 让 EL2 提前醒来。hv_arm_tick 会在编程普通 host tick 后再次 rearm 软件 deadline，避免 tick 覆盖 guest deadline。[^12][^17]

未来若必须兼容旧固件，需要同时证明：guest timer 的 masking、到期唤醒、重新启用、软件 deadline、虚拟 FIQ 和 IPI 不丢失也不形成 storm。仅保留周期 host tick，或只 guard 那四个写入，不足以证明这些性质。当前证据不足以给出正确的几行 fallback，因此本轮不安装这样的补丁。

## 新发现：RAM disk 的 stage-1 可见性

离线检查第二轮日志和已保存输入：

| 区域 | 起点 | 终点，不含 |
| --- | --- | --- |
| guest 物理 RAM | 0x1008e69c000 | 0x107d09a4000 |
| 当前 RAM disk | 0x1000e6b0000 | 0x1006beb8600 |

整份 RAM disk 在 guest phys_base 以下。launcher 的 utils.memalign 在 host proxy heap 分配它，后来添加 RECOVERY-RAMDISK stage-2 映射。这只解决 IPA 到物理 RAM 的访问，不能自动创造 guest kernel 的虚拟地址映射。

固定 HLE 代码只将 bootargs.phys_base..phys_base+mem_size 建为线性 physmap；当前 RAM disk 不在这一区间。[^6]

公开 XNU 的 IOFindBSDRoot 读取 ADT RAMDisk，把首地址经 ml_static_ptovirt 转换，并以虚拟内存模式注册 mdev。arm64 的 ml_static_ptovirt 又调用 phystokv。由此推断，仅有 stage-2 映射不足以满足这条根盘路径；本次尚未执行到该处，且需用匹配的 25E253/25G83 二进制进一步确认。[^18][^19]

公开版本的 phystokv 先尝试 ptov_table，未找到特殊 alias 时会对低于 gPhysBase 的物理地址直接 panic；不会自动补映射。尚无证据证明本次存在覆盖 host heap 的特殊 alias。这个来源将问题从一般的“可能访问不到”收紧为高可信的后续 blocker，但仍不能伪称已在本台观察到此 panic。[^23]

### 下一版内存布局必须满足的条件

RAM disk 应放在 guest 可通过预期 stage-1 地址访问、并明确保留的物理范围内，不能与 kernel、ADT、TrustCache、SEPFW、bootargs、HLE aux allocator 或 XNU free RAM 重叠。固定 HLE 在 top_of_kernel_data 后分配 64MiB aux，再提升该边界；新布局必须把 RAM disk 保留边界与 aux 分配顺序一起处理。[^6]

不应简单把 phys_base 向下扩大到 host heap：那可能把 m1n1/proxy 状态也交给 XNU allocator。也不能只抬高 Python 的 top_of_kernel_data 而不重写实际 guest BootArgs；该结构此前已经序列化上传，C 侧使用的是目标 RAM 中的版本。

建议在 guest image 的保留区域安排 root image，采用受校验的布局计算；上传前验证所有区间不相交，上传后读取 BootArgs/ADT 做一致性检查。为减少风险，下一轮先单核、无 guest SSD，再扩展到多核。

## 新发现：GPT whole disk 不等于 rd=md0 根卷

对 recovery-25E253.raw 的离线 GPT CRC 校验全部通过。镜像共有 1568704000 字节，只有一个 APFS partition：

- type GUID：7c3457ef-0000-11aa-aa11-00306543ecac。
- LBA 34..3063841；起点 17408 字节，大小 1568669696 字节。
- 分区起点的 APFS NXSB 存在，block size 为 4096。
- 整张磁盘起点没有 APFS NXSB，因为前面是 partitioning metadata。

公开 XNU 对 rd=md0 的处理会直接选择 mdevlookup(0) 得到的 block device；没有在该分支中为 launcher 自动挑选 GPT 的 APFS 子分区。因此“完整 Recovery 虚拟磁盘已上传”不等于“md0 已指向可直接挂载的 Recovery 文件系统”。这是明确的布局不一致风险，不是已经观察到的本台 APFS mount panic。[^18]

下一轮应核实准确 root 策略：是直接提供 APFS container 分区作为 RAMDisk，还是让专门的 block-device/partition 层暴露子分区。还需要列出该 container 的 volume UUID/role、可挂载 root、seal/root-auth 要求和 userspace 文件；仅看到 NXSB 不能保证 launchd 可启动。

还有一个不能忽略的对齐陷阱：分区起点 0x4400 不是 4KiB 对齐。不能只把原 RAMDisk address 加 0x4400、缩短 size；公开 XNU 注册 memdev 时的 >>12 会丢掉低 0x400，实际设备起点会提前 1024 字节。应复制分区数据到新的 16KiB 对齐 guest 保留区域，而不是原位改指针。[^18]

该分区的 NX block count 为 382976，4096 × 382976 恰好等于分区大小。公共 VFS mountroot 把 md0 vnode 交给 filesystem，没有替 launcher 实现 GPT 切片；但 AppleAPFS 私有 mountroot 是否有其他特例，仍需匹配二进制/隔离实验确定。[^24]

不能把 UDIF .dmg 本身直接当未经解码的 RAMDisk，也不能把文件名带 raw 就当作单卷文件系统。当前保存的原始 whole disk 必须保留；任何分区提取都应另写产物、记录 offset/length/SHA-256，并确认工具只读取这个本地文件，而非 /dev/disk0。

## Recovery、Darwin shell 与桌面分别验收

| 目标 | 成功证据 | 当前状态 |
| --- | --- | --- |
| m1n1 proxy | UART/proxy 双 NOP，机型/二进制身份正确 | 已在两次失败重启后验收 |
| SPTM HLE handoff | 初始化返回且进入相应 XNU 执行路径 | 初始化返回已有证据；仍发生 EL2 fault |
| XNU 基础启动 | Darwin banner、VM bootstrap、可读 panic/trace | 未验收 |
| RAM root | 正确 root device、挂载 root filesystem | 未验收 |
| Darwin shell | launchd 启动、shell、uname、重复命令 | 未验收；最合理的下一阶段目标 |
| Recovery UI | Recovery userspace 和显示正常 | 未验收，不是 shell 的同义词 |
| 完整 macOS 桌面 | 正确 System/Data/snapshot/cryptex、登录及稳定运行 | 4GB 空 stub 不具备完整系统输入 |

先把 kernel/root/shell 作为独立目标，可以将 DCP/AGX 问题从 early boot 问题中分开。保留 -v、足够大的 msgbuf 和 host/guest trace；不能仅靠屏幕无显示判定 kernel 未启动。

## 哪些公开贡献最值得参考

**Niklas Sheth 与 Cody Ho。** PR #1 提供目前可实际构建的 HLE；固定源码包含 XNU handoff、DART/NVMe/UAT/TXM 等兼容代码。Cody 的 apple-silicon-re 文档主要以 T8140、26.6 beta/KDK 为背景，自述不是真实 SPTM 的完整安全规范；它适合梳理调用，却必须对 T8132 和实际 build 复核。[^1][^5]

**Sven Peter。** PR #643 提供 GXF/SPRR 执行与权限模拟；#646 是已经进入 main 的准备修改。真实 SPTM bring-up 的 handoff/private 整理工作不能从这两个公开 PR 自动补全，需要继续追踪具体 loader 是否公开。[^2][^3][^10]

**Yureka/yuka。** IRC 中给出 timer register 的版本前提，也参与 M4 NVMe、MCC、SMP 和固件问题调查。她在 08-28 提到 26.6.2 的 Linux 无已知 blocker，不意味着 macOS guest 或完整设备支持已经完成；本项目只将其用于选择合理的固件候选。[^11][^13]

**unoloxia。** 09-08 报告 J700 的音频路径无需 Exclaves，并称通过 SPTM emulator 启动 cL4 做 traces；其 XNU 在早期 TXM calls 后、预期 SK RingGate 前仍停滞。这支持“模拟可用于硬件研究”，但没有给本台 J713 的完整启动方案，也没有在该消息提供可直接复现的 commit。不是当前 timer fault 的必要解决依赖。[^20]

**jprx。** darwin-vm 的文档展示 QEMU 上的 Darwin root shell，并列出 T8132/M4 Mac mini、macOS 26.6 的测试组合；明确不是完整 Mac GUI/硬件仿真。其 get_files.sh、run.sh 和 TrustCache 生成方式可用于学习最小 userspace 与真实 SPTM/TXM 输入准备，不应用来证明 native M4 Air 的 DCP/NVMe/USB 行为。[^21][^22]

尤其值得借鉴的是其 SPTM loader 将 RAMDisk 内容放进 guest DRAM 的 bootstrap blob，并相应提升 topOfKernelData；不是把 host heap 指针放入 ADT 后只补 stage-2。QEMU 原样加载所给文件，并不能替本项目的 GPT whole-disk 镜像自动解包或剥离 partition table。[^25]

## 还缺什么资料

| 优先级 | 缺少或待核实的资料 | 用途 |
| --- | --- | --- |
| P0 | J713/T8132 的匹配 26.6.2 BuildIdentity、实际 boot stages、DeviceTree、固件哈希及个性化策略 | 确定解锁前提真的生效，不仅是存有新版文件 |
| P0 | E/P core 分别对 VM_TMR_FIQ_ENA_EL2 的受控读写验收 | 读成功不能代替写成功；测试本身不是只读 |
| P0 | 新 guest 保留内存布局与实际 BootArgs/ADT | 排除 RAM root 不可见及 allocator 覆盖 |
| P0 | root 镜像的 container/volume/snapshot 信息及匹配 userspace | 确定 md0 根盘可挂载、launchd 可运行 |
| P1 | 25G83 handoff struct、SPTM endpoint、TXM record 与 KC patch 覆盖 | 验证 HLE 版本兼容；存在符号不等于 ABI 匹配 |
| P1 | timer deadline、mask/unmask、time stealing、IPI、多核回归 traces | 证明跨过 fault 后中断系统没有隐蔽失效 |
| P1 | Sven 真实 SPTM/TXM loader、EL/GL 重定位、启动 handoff | 使用真实 SPTM 路线，而不只拥有 emulator |
| P2 | 完整专用 macOS System/Data、sealed snapshot、cryptex 和 FileVault 策略 | 桌面启动；与 RAM-only shell 分开 |
| P2 | DCP/GPU/USB/音频 firmware ABI 与 tracer 适配 | 实际硬件逆向；不必全部阻挡第一条 shell |

## 建议的实验顺序

1. **保持已有可恢复 stub 不变。** 固定当前 HLE、optional-ANS 和所有输入哈希；本轮离线审阅不连接 guest，不刷写启动对象。
2. **准备候选新固件资源。** 先在 Recovery 中只读列举 25G83 的 manifest、bootcaches、DeviceTree、SPTM/TXM 与 Recovery；通过 J713/board 0x2C/chip 0x8132 identity 核对。来源不完整时停止，而不是混填。
3. **单独规划启动链迁移。** 优先另建实验 stub 保留现有回退，而不是覆盖旧 restore；是否能完成个性化、空间和默认启动选择需在具体 Recovery 环境核对。不能拿本报告中的候选步骤当已执行事实。
4. **寄存器能力 preflight。** 不启动 XNU，先受控验证可写性、保存/恢复状态与异常计数，随后检查 proxy。即使写回原值，也属于寄存器写实验；不能宣称完全只读或绝对无副作用。
5. **修正 RAM root 与内存布局。** 补齐 guest stage-1 可见性、保留边界、实际 BootArgs 更新、APFS root 输入身份与 launcher 前置校验。使用单核、保留 guest ANS 隔离。
6. **逐阶段启动并留证据。** 以 Darwin banner → VM bootstrap → root mount → launchd → shell 为里程碑。发生新异常记录 guest ELR 与 host PC、ESR、SPTM dispatch/CPU/context，不进行无限重试。
7. **稳定 shell 后才加设备。** 扩展多核、9P export、MMIO tracing，再分别处理 DCP/AGX 与完整桌面。9P 支持不是现成的可启动 root block device。[^9]

如果无法满足新版 firmware 前提，才进入旧固件完整 timer fallback 的研究；那是一个需要模型和回归的独立实现任务，而不是把 msr 改 NOP 后直接宣布修复。

## 本地可复现检查

以下命令不连接 M4：

```sh
cd /home/sequencer/project/m4-linux
nix develop --command sha256sum -c experiments/2026-09-13-sptm-macos/SHA256SUMS
nix develop --command python3 scripts/inspect-recovery-input.py
```

第二条检查 GPT header/table CRC、APFS partition 起点和保存日志中的 physmap/RAMDisk 包含关系。检查的是已保存输入与第二轮现场，不是目标当前动态状态；输出 guest_boot_verified=false 不代表新的 guest 失败。

本次已实际完成该检查：GPT CRC 正常、分区 NXSB 正常、RAMDisk 不在 HLE physmap 中。输出保存为 raw/recovery-input-audit.json。两个 Mach-O 的重新解包与逐字节比较在 KERNEL_REPRODUCIBILITY.md 中已有验收。

原始现场文件的 SHA-256：

```text
4daadc6cc407f5db68a3385a9ce12cd6386c4275586d7c9ecf654cb4a167c2be  guest-attempt-2.txt
0b8e46933c2fdde73e6994106472705c4c59d790f47ae6a320ad4be1cad68242  guest-adt.bin
d542214fafd18ce57297e4c5e70c490f4ff59df903ad6543985fae974be59678  el2-timer-fault-disassembly.txt
```

这些文件均在 experiments/2026-09-13-sptm-macos/raw/，仍不随 Git clone 自动获得。guest ADT 和原始 preflight 可能包含机器/NVRAM 标识，不通过公共 HTTP helper 分发。

## Sources

[^1]: Niklas Sheth，Cody Ho fork 的 [SPTM Emulator PR #1](https://github.com/ADevWithAnIdea/m1n1/pull/1)；本次 API 核对 head 7e43bb1、updated_at 2026-08-15T04:49:47Z。
[^2]: Sven Peter，[SPRR/GXF emulation PR #643](https://github.com/AsahiLinux/m1n1/pull/643)，2026-07-28 提出，head 于 08-30 更新至 1c98fd0。
[^3]: Sven Peter，[准备修改 PR #646](https://github.com/AsahiLinux/m1n1/pull/646)，2026-08-01 合并。
[^4]: Asahi Linux，[Progress Report: Linux 7.2](https://asahilinux.org/2026/08/progress-report-7-2/)，SPTM/GXF 部分；公告不等于所有 loader/M4 适配代码已公开。
[^5]: Cody Ho，[SPTM 文档](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/35130fd3faa3b79b78e1994199c7417bafb63a72/docs/sptm/README.md)，范围与 dispatch ABI。
[^6]: Niklas Sheth，[固定 HLE boot/handoff](https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/src/hv_sptm_boot.c)。
[^7]: Sven Peter，[固定 hv_sprr.c](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/src/hv_sprr.c)。
[^8]: Sven Peter，[固定 Python SPRR patcher](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/proxyclient/m1n1/hv/sprr.py)。
[^9]: Sven Peter，[固定 run_guest.py](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/proxyclient/tools/run_guest.py)。
[^10]: Sven，IRC #asahi-dev 2026-07-31 21:51–21:58；本地 /home/sequencer/projects/catirclogs-asahi/asahi-dev/2026-07-31.txt；[原始日志 URL](https://oftc.catirclogs.org/asahi-dev/2026-07-31.txt)。
[^11]: Sven、yuka，IRC #asahi-dev 2026-08-28 15:14–16:15；本地 asahi-dev/2026-08-28.txt；[原始日志 URL](https://oftc.catirclogs.org/asahi-dev/2026-08-28.txt)。
[^12]: Niklas Sheth，[固定 hv_exc.c](https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/src/hv_exc.c)，hv_update_fiq 与软件 timer；本台原始日志和反汇编见本地可复现检查。
[^13]: yuka，IRC #asahi-dev 2026-08-27 07:05；[原始日志](https://oftc.catirclogs.org/asahi-dev/2026-08-27.txt)，本次通过直接文本读取与本地副本核对。
[^14]: Niklas Sheth，[固定 M4 features](https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/src/chickens.c)，features_m4。
[^15]: Asahi Linux，[固定 main hv_exc.c](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/hv_exc.c)。
[^16]: Sven Peter，[固定 PR #643 hv_exc.c](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/src/hv_exc.c)。
[^17]: Niklas Sheth，[固定 hv.c](https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/src/hv.c)，hv_arm_tick/rearm。
[^18]: Apple，[固定公开 XNU IOKitBSDInit.cpp](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/iokit/bsddev/IOKitBSDInit.cpp)，RAMDisk 与 md root。
[^19]: Apple，[固定公开 XNU machine_routines.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/machine_routines.c)，ml_static_ptovirt。
[^20]: unoloxia，IRC #asahi-dev 2026-09-08 01:38；本地 asahi-dev/2026-09-08.txt；[原始日志 URL](https://oftc.catirclogs.org/asahi-dev/2026-09-08.txt)。
[^21]: jprx，[固定 darwin-vm README](https://github.com/jprx/darwin-vm/blob/28c6d27e401bd60299bbb6c69667deeba669b810/README.md)，用途、限制及测试矩阵。
[^22]: jprx，[固定 get_files.sh](https://github.com/jprx/darwin-vm/blob/28c6d27e401bd60299bbb6c69667deeba669b810/get_files.sh)，firmware/root/TrustCache 准备。
[^23]: Apple，[固定公开 XNU arm_vm_init.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/arm_vm_init.c)，phystokv/ptov_table。
[^24]: Apple，[固定公开 XNU vfs_subr.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/vfs/vfs_subr.c)，vfs_mountroot。
[^25]: jprx，[固定 QEMU SPTM loader](https://github.com/jprx/qemu-sptm/blob/2867d847d3471560e773120ee50c42dbcbb6d60b/hw/arm/xnuboot_sptm.c)，guest RAMDisk 与 bootstrap blob。

IRC 的结论以本地文本为核查依据；部分网页在本次浏览器中不可用，链接记录的是原日志地址，不声称全部已被浏览器打开验证。对私人/尚未公开的 loader、学生代码和 unoloxia 的实现没有补造仓库、branch 或 commit。
