# 研究讨论记录

## 2022：SPRR/GXF 不是完整 virtualization

IRC 中曾出现 SPRR/GXF emulation 实现，但 Asahi 维护者指出这只能改变问题，不能提供合理的 SPRR/GXF virtualization；即使 CPU 侧完成，GPU/AGX 仍是主要障碍。

参考：`catirclogs-asahi/asahi-dev/2022-03-03.txt`。

## 2024：SPTM 进入 M4 启动链

IRC 确认 M4 的启动链依赖 SPTM，并讨论了 GL2/EL2/GL1/EL1/GL0 的分层。M1–M3 与 M4 的差别不是简单的版本开关：M4 上页表、GXF 和系统寄存器的限制会影响整个 hypervisor 设计。

参考：`catirclogs-asahi/asahi-dev/2024-07-14.txt`。

## 2026-02：确认 M4 不能直接复用 M1–M3 hypervisor

`sven` 和 `chaos_princess` 讨论了 Apple 文档与实际机器差异：M2/M3 仍可通过旧 macOS 版本避开部分 SPTM，而 M4 的 SPTM 更难虚拟化。结论是不能把两者称为相同问题。

参考：`catirclogs-asahi/asahi-dev/2026-02-10.txt`。

## 2026-05 至 07：HLE SPTM bring-up

StanfordAppliedCyber 的实验路线逐步覆盖：

1. XNU `genter` 到 hypercall 的转换。
2. SPTM handoff 和 runtime endpoint 模拟。
3. PMGR/SPMI、timer、cache/TLB 和 GXF 特殊指令。
4. commpage、SME/sysreg 和稳定性修复。
5. 不包含 SPTM emulator 的 upstreamable hypervisor 分支。

最重要的限制是：实验成功并不自动产生可发布的 clean-room SPTM 实现，也不等于 Linux 能直接使用这套页表模型。

参考：

- `catirclogs-asahi/asahi-dev/2026-05-10.txt`
- `catirclogs-asahi/asahi-dev/2026-05-19.txt`
- `catirclogs-asahi/asahi-dev/2026-05-28.txt`
- `catirclogs-asahi/asahi-dev/2026-06-20.txt`
- `catirclogs-asahi/asahi-dev/2026-06-23.txt`
- `catirclogs-asahi/asahi-re/2026-07-03.txt`
- `catirclogs-asahi/asahi-dev/2026-07-09.txt`

## 2026-07：SPTM guest 和 Linux 的区别

`dj` 成功让 custom kernelcache 稳定通过 SPTM handoff。随后 IRC 明确指出：在 SPTM 下运行 m1n1 对研究 XNU 有用，但 Linux 仍需要重新设计内存管理；Linux 不能假设自己拥有普通 ARM64 的页表控制权。

参考：`catirclogs-asahi/asahi-re/2026-07-21.txt`、`2026-07-22.txt`。

## 2026-09-08：Exclave guest trace

`unoloxia` 成功启动 cL4/ExclaveOS secondary guest，并完成基础 Tightbeam/online/ping-pong 交互；XNU 到 SK RingGate 的后续 handoff 仍然卡住。

参考：`catirclogs-asahi/asahi-dev/2026-09-08.txt`。

## 工作假设

当前采用以下可证伪假设：

1. 最小 Linux 不需要完整 ExclaveOS，但启动 shim 必须正确处理 SPTM 对 Exclave 状态的要求。
2. SPTM 的关键接口可以通过公开 XNU 头文件、公开 IPSW 分析和输入/输出实验重建。
3. M4 Air 的第一目标应是 headless Linux，不应把 GPU 作为 boot blocker。
4. 每个 SoC/firmware generation 需要自己的固定版本和回归测试，不追求一个未经验证的 universal binary。
