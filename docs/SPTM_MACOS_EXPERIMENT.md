# 从独立 stub 启动 SPTM 路径的 macOS

内核与 Recovery RAM disk 已保存在项目本地。版本、来源、可随 Git 保存的哈希清单及离线重解包步骤见 KERNEL_REPRODUCIBILITY.md；raw/ 被忽略，clone 本身不包含二进制输入。

## 最新研究：先核实固件解锁前提与 RAM root 布局

深入审阅结果见 SPTM_MACOS_RESEARCH.md。本次已确认的现场仍是 HLE 初始化返回后，hv_update_fiq 的 msr 失败；但 IRC 给出了 VM_TMR_FIQ_ENA_EL2 从 26.6 beta 解锁的固件前提，应优先验证匹配的新启动链，不应先删除 FIQ routing。apple_sysregs_unlocked 是静态全局描述，不能代替此寄存器的单独能力验收。

新离线检查还确认 RAMDisk 位于 guest physmap 以下，只加 stage-2 映射不足以满足公开 XNU 的 RAM root 路径；Recovery raw 是带 GPT 的 APFS whole disk，需要另行确认 md0 的分区/root 策略。检查命令为 nix develop --command python3 scripts/inspect-recovery-input.py。本轮研究没有更改持久启动配置或再次启动 guest。

## 第二轮实测：SPTM HLE 初始化通过，EL2 定时器寄存器写入阻断

第二次 guest 已完成：本地 optional-ANS 补丁消除了第一次 BadOffset，日志显示 skipping absent NVMe controller，hv_sptm_init 成功返回，随后显示 Jumping to entrypoint at 0x10094804000。没有 macOS Recovery UI 或 Darwin 启动完成证据，不能报告 macOS 启动成功。

随后 m1n1 报 Exception taken from EL2h，PC 为 0x100040ea3b8，相对 m1n1 base 偏移 0x163b8，ESR 0x02000000，Unhandled exception, rebooting。反汇编该本地构建得到故障指令 0xd51df160：msr s3_5_c15_c1_3, x0；固定 PR 的 sysreg_rev 将其解码为 VM_TMR_FIQ_ENA_EL2。

与 src/hv_exc.c 的 hv_update_fiq 对照：该函数无条件 reg_set/reg_clr SYS_IMP_APL_VM_TMR_FIQ_ENA_EL2，用于 CNTP/CNTV 的 FIQ 路由；没有按 cpu_features->apple_sysregs_unlocked 分支。本台实测该字段 false，在这一写入位置触发 EL2 undefined-instruction 类异常。根因定位针对本次指令和现场，不能泛化为所有 M4 同样失败。

这与 SIP、SSV 或 FileVault 不同：故障发生在 HV 自身操作 Apple 定时器寄存器的路径，继续关闭 macOS 安全策略不能替代固件解锁前提。应先验证匹配固件下此寄存器可写；只有必须支持旧锁定固件时，才研究完整 timer/FIQ 替代路由，而不是直接删掉全部 timer 更新或恢复 SSD 访问。

目标自动重启回未修改的持久化 stub，2026-09-13T16:44:05Z 再次验证 UART NOP 和 proxy NOP 成功。本轮没有更换持久启动对象，没有选择原用户 Data 为 guest 根盘，所有 kernel/RAM disk 加载和修正构建均位于 RAM。当前保持原始 stub proxy，不再盲目重复相同失败路径。

最新失败日志 guest-attempt-2.txt，回滚验收 proxy-after-attempt-2.json；均在 experiments/2026-09-13-sptm-macos/raw。第一轮补丁已保留在 flake.nix；下一轮需要 timer 修正才能超过此次阶段。

故障对应源码：https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/src/hv_exc.c

下文保留各阶段历史记录。

## 资产读取与第一次实际加载

用户再次进入 Recovery 并开 SSH 后，bputil 确认新 stub 为 one true recoveryOS / Paired。此次实验容器为 disk2，原 macOS 为 disk4，按 UUID 核对后才挂载 Preboot 和 Recovery。

已读取到 M1：

- 新 stub restore 中的 kernelcache.release.mac16g，32027045 字节，匹配 26.4.1/25E253。
- 原 restore-staged 的 kernelcache，匹配 SystemVersion 26.6.2/25G83，供后续比较，没有用于本次 guest。
- 当前 Recovery 的只读虚拟磁盘 /dev/rdisk5，1568704000 字节，作为 RAM disk；不是物理 SSD disk0。读取 dd 正常完成，32.8 秒，不在目标系统复制或解密用户 Data。

Nix 中的 pyimg4 0.8.8 被标记 broken，原因是 asn1 >=3 不兼容，没有强行忽略该标记。改用 Nix 提供的 Apple lzfse CLI，scripts/extract-kernelcache.py 按 IM4P DER 字段抽出 krnl 的 LZFSE payload 后解压，并使用固定 PR 的 MachO 类离线检查符号。

25E253 解包大小 120373248，25G83 为 120504320。两者的 _cons_ops、_PAGE_SHIFT_CONST、__TEXT 均存在。资产哈希保存在 raw/assets.sha256。

已经重启到 stub m1n1 并开始运行 scripts/run-recovery-guest.py：HV 初始化成功，删除 guest ADT 的 ans SSD 控制器节点，使用 rd=md0 和 PR 的锁定寄存器 boot args；25E253 kernelcache 完成 GENTER/sysreg 补丁、RAM 加载、SEPFW/TrustCache/preoslog 复制和 bootargs 设置。正在将完整 Recovery RAM disk 分块上传；该加载阶段不等于 XNU 已运行。

脚本为 guest 在独立 RAM 范围映射 RAM disk，保留 host heap 的其他范围；没有选择原 macOS 的 Data 为 guest 根卷。删除 SSD 节点是本次隔离措施，不应泛称为对恶意 guest 的完整硬件安全沙箱。

本次运行日志：experiments/2026-09-13-sptm-macos/raw/guest-attempt-1.txt。首次 guest 的实际最终结果将追加记录，不预先报告成功。

### 第一次 guest 的失败与本地修正

Recovery RAM disk 全部上传、页表更新与 guest ADT 上传完成后，调用 hv_sptm_init 时发生 Rust panic：src/adt.rs:804，Result::unwrap / BadOffset。随后 USB 断开，脚本退出 1，尚未打印 Jumping to entrypoint，不能报告 XNU 已启动。目标随后重新枚举并回到持久化原始 stub proxy；M1 的 UART 和 proxy NOP 再次通过。

对应代码中 sptm_init_platform 使用 guest ADT，sptm_init_nvme 无条件查找 /arm-io/ans；本次为了隔离 SSD 删除了该节点，查找返回 NotFound=-1，调用 adt_get_property 时把负偏移变为未按 4 字节对齐的指针，ADTNode::from_ptr 返回 BadOffset，随后 unwrap panic。这是与本次现象一致的具体缺陷；复测是否消除该 panic 必须以第二次日志确认。

已在 flake.nix 的 m1n1-sptm postPatch 维护最小本地修改：当 /arm-io/ans 或 /arm-io/sart-ans 路径不存在时，相应初始化函数提前返回。不是删掉 Rust 检查、伪造硬件地址或恢复 guest SSD 访问。固定上游源仍是 PR #1 head；本地 Nix 包现在额外应用该补丁，不能再把它的输出 SHA-256 当作未经修改的 PR 输出。

补丁版本构建成功，SHA-256 为 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4，通过 tools/chainload.py -r 成功在 RAM 中重载，日志确认 Proxy is alive again。结果在 results/m1n1-optional-ans。持久化 boot object 未改变，仍是原始构建 d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0；重启可返回原始版。

第二次 guest 已开始，继续使用匹配 25E253 内核和 RAM disk，并保留 guest ans 隔离。日志为 raw/guest-attempt-2.txt。scripts/run-recovery-guest.py 还保存实际 guest-adt.bin，便于后续离线检查。

原始上游初始化代码：https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/src/hv_sptm_init.c

原始 Rust ADT 实现：https://github.com/niklassheth/m1n1/blob/7e43bb1763ff97d661bbddb213596eda9475ae6a/rust/src/adt.rs

## 2026-09-13T16:26:04Z 已执行的实机阶段

运行 scripts/sptm-hv-preflight.py，通过固定 PR 构建的原生 USB /dev/ttyACM0，建立 ProxyUtils 和 HV，执行 HV.init，然后再次发送 UART 和 proxy NOP，两次均通过。

实测 chip_id 0x8132，apple_sysregs_unlocked false，HV 初始化成功，其他 9 个 CPU 均显示 Started，HV: Initializing for 42-bit PA range、SME enabled、ECV enabled，注册 27 个 MMIO range。这些是 HV 初始化证据，不是 XNU 或 SPTM emulator guest 已启动的证据；尚未调用 load_macho、hv_sptm_init 或 HV.start。

本阶段修改 RAM、CPU/HV 寄存器及 USB 使用状态，没有执行 NVMe 写入、修改磁盘启动策略或启动 guest。当前 proxy 仍能 NOP；HV 初始化也不能等同于严格只读检查。

原始日志与结果：experiments/2026-09-13-sptm-macos/raw/preflight-output.txt、preflight.json。原始 chosen ADT 含 NVRAM 和机器标识，保留本地，不公开；脚本后续把该数据单独保存到 .adt.txt，避免在报告中重复打印大块内容。

## 代码确认的启动方式

固定 PR 的 proxyclient/tools/run_guest.py 非 raw 路径加载 Mach-O kernelcache；锁定 Apple sysreg 时添加 sptm_hv_boot_args，注册 _cons_ops、_PAGE_SHIFT_CONST、__TEXT 和可选 AMX 符号，HV.start 阶段调用 target hv_sptm_init。它是 XNU 与 SPTM 调用的虚拟化/模拟路径，不是直接重新进入已被替换的 Apple SPTM 启动链。

必需的默认 boot args 包括 -nobsdmgroot、sprr_tpro=0、sprr_tpro_pagers=0、wfi=0、cluster_power=0、processor_exit=0、vm_compressor=0；不能不看匹配版本和根卷就用默认命令开 guest。

## 历史：资产读取前尚缺的输入

M1 本地没有本次目标 kernelcache；此前只拉取了 plist、固定 m1n1 和日志，准备 stub 时 kernelcache 留在 M4 Preboot。当前 ADT 的 boot-uuid、apfs-preboot-uuid 均是新 stub UUID DE77783E-D9C0-4695-8BE1-EBE0D3015748，不能让 XNU 默认从这个空系统卷启动完整 macOS。

下一步需进入新 stub 的 Recovery，并用已提供的 HTTP ssh.sh 恢复 SSH。在不修改文件的前提下读取：

- 新 stub 匹配 26.4.1/25E253 的 restore/kernelcache.release.mac16g、BuildManifest、bootcaches，以及匹配的 Recovery 镜像信息。
- 原 macOS 当前实际使用的系统快照版本、restore 与 restore-staged 的版本及 kernelcache、BootKernelExtensions.kc，不能把原裸 SystemVolume 的 26.6.2 版本直接当作当前启动快照版本。
- 原卷组 UUID、FileVault 与 cryptex 元数据；明确完整 macOS guest 的根卷和兼容资源。

优先进行只使用匹配 Recovery 资源的 XNU 启动实验，避免直接让实验 guest 写入原用户 Data；必须把 Recovery guest 与原 macOS 桌面启动分别报告。完整系统启动需要解决实际系统版本、根卷、FileVault 和 cryptex，并评估如何保持原 Data 不被实验 guest 写入。

读出 kernelcache 后，在 M1 以 Nix 管理的工具解包为 Mach-O，先离线验证上述必需符号是否存在，再进行 RAM 加载与 SPTM guest 启动。缺少符号不能用错误地址硬填。guest 首次启动应保存日志并设定停止判据，发生 panic/USB 掉线时回到已验证的 stub proxy，不重刷 macOS。
