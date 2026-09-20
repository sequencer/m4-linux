# Guest 隔离审计：离线第一阶段

> 已撤回：用户要求停止防御性改造。本文仅保留审计历史；读取守卫、诊断接口改造、IORegistry 和 launcher 的新增封锁均已撤回，不再是当前代码状态。

2026-09-14，M4 留在已验收的 m1n1 proxy。此次只读 M1 本地源码、修改诊断工具并运行 mock 验证；没有访问 target、上传 payload、运行 HV.init、重启或操作 SSD。

## 固定审计对象

Nix result 指向 `/nix/store/26pj1nn35yxzx0i4s7qrx4c8s4x7lmp6-m1n1-sptm-pr-1-7e43bb1`。其中 `share/m1n1-sptm/proxyclient/m1n1/hv/__init__.py` SHA256 为 `b5e4e0cc54c6f67b8f36c63c4cafcd53ccc5ddf0f21fdddb548c5a087e1c3c3a`。以下行号指这份固定文件，不代表远端最新实现。

## 已确认的隔离缺口

| 本地证据 | 实际语义 | 后果及限制 |
| --- | --- | --- |
| HV.init，1492–1500：遍历 `/arm-io`.ranges，注册 `HW` / TraceMode.OFF | 默认纳入整段真实 MMIO | 删除 ADT 中某设备不等于撤销其硬件访问映射 |
| HV.pt_update，361–362：OFF → map_hw(IPA, IPA, size) | OFF 为直接硬件映射，不是 deny | 不能用 OFF 标记“禁止设备访问” |
| run-recovery-guest.py：先 HV.init，再删除 ans/nvme 节点 | 设备发现与访问权限是不同层 | ANS 不出现在 guest ADT，不证明 SSD/其他持久状态路径不可达 |
| HV.load_raw，1867–1869：RAM-LOW / RAM-HIGH，然后 unmap_carveouts | 映射范围不是 Python allocator 所拥有区域的证明 | 仍需逐段审计 host/guest/固件边界；carveout 排除不等于所有敏感区排除 |
| HV.load_raw，1832、1877–1881：取当前 SEPFW/TrustCache 并 memcpy | guest 还依赖运行时材料，不只使用命令行 kernel/root | 资源清单不能覆盖全部 live 输入；复制 SEPFW 不证明写 SEP 持久存储 |
| HV.readmem，209 起：翻译为零时 break，返回已有字节 | 可静默返回短读 | 调用方必须精确校验长度，不能解析半份结构 |
| 旧 APFS BRK handler | readXX(hv_translate(...)) 与 write8(hv_translate(...)) 无统一守卫 | 即使 IORegistry 修好，旧 launcher 仍不能开放 |

**这证明原方案不是隔离的 RAM-only guest，但不证明此前是哪一个设备/调用导致原生恢复失败。** SEP mailbox、NVRAM 服务、PMGR/reset、DMA/DART/协处理器访问链仍未完整追踪，不能把这些候选路径写成已发生的持久写入。

## 已实施的读取守卫

`scripts/guest_memory.py` 的 GuardedReader 只接受显式 VA 与 PA 半开白名单，绑定固定 kernel SHA，并限制单次读取和累计预算。它不从 bootargs 自动推断“所有 RAM 都安全”，也不提供默认 live 地址范围。

- 拒绝零/负/布尔地址、非法长度、超出 64 位或白名单、超预算请求。
- 按 4KiB（或明确指定 16KiB）分页，先校验整个请求的所有翻译，再开始读取；翻译失败、PA 落出允许 guest RAM、页内偏移不一致均拒绝。
- 严格要求每段返回 bytes 且长度一致，不能把短读当成有效结构。
- 首次失败锁死该 reader，后续请求不再调用翻译/读取，防止错误后继续遍历。
- 只有读接口，没有写入、执行 guest 函数、隐式 PAC 清除或物理地址零回退。

`guest-processes.py` 已改为必须传入该 reader；固定指令校验也通过同一读取路径。`guest_diagnostics.py` 的 console header/buffer 同样通过它读取，避免跨页假设；不再先调用未经本轮审计的原始 panic formatter。缺 reader 时在访问 hypervisor 前拒绝，不自动退回旧 API。

`guest-ioreg.py` 入口暂时拒绝所有解码：没有经过验证的 OSString/OSSymbol/OSNumber/OSDictionary/OSArray 类型识别 profile。按属性名挑选“看起来像字符串”的值不是类型证明。旧实现保留作审计，但不可执行。不会填入猜测的 vtable 或临时调用 guest 的 getMetaClass 方法。

## 离线验证与边界

Nix Python mock 验证 22 项通过，涵盖非法地址/长度、空或异常翻译、MMIO 范围拒绝、页偏移错误、短读、预算、跨页拆分及三个诊断入口缺 profile 的拒绝。第二页翻译失败的案例确认物理读调用次数为零；诊断入口使用一访问即报错的 NoHardware 替身。另验证首次失败后 reader 不再触发回调。

这不是硬件级安全证明：翻译回调本身仍可能有副作用；guest 未暂停时存在页表变化竞争，白名单也必须排除 host RAM、固件 carveout、共享内存和 DMA 可变区。即使 PA 属于 RAM，也需 target 端异常恢复和超时验证。当前没有提供经过实机验证的白名单，因此不要构造宽泛白名单来重新启用诊断。

## 后续门槛与最小实验方向

1. 完成原生 macOS、普通 Recovery、备用 Recovery 的物理回归验收，再只读采集本轮状态。当前 iSC 仍缺失，不使用旧副本。
2. 离线导出最终 stage-2 映射及设备列表，改成默认拒绝；只开放单项有说明的范围。必须同时审计 MMIO、IRQ、DMA 与协处理器固件行为。
3. 第一个可讨论的 live 实验应是无真实设备直通的最小 guest RAM/异常返回测试，不是直接启动完整 Recovery；必须先确定其所需 timer/中断路径及回退方法。
4. 建立 paused-guest 读取前提、异常捕获、host/guest RAM 界限和设备类型 profile，再替换旧 APFS handler 与交互 shell helper。不要开放任意物理读写。
5. 完成上述验收并记录具体实验边界后，才评估解除 launcher 封锁。当前 `run-recovery-guest.py` 保持阻断，更新资源或关 SIP 都不自动满足这些门槛。
