# ADevWithAnIdea 公开工作审阅

审阅日期：2026-09-13

## 身份边界

GitHub 账号公开显示为 Cody Ho：

- [GitHub profile](https://github.com/ADevWithAnIdea)
- 本项目不把该账号与任何 IRC 昵称强行对应；目前没有足够公开证据证明两者身份相同。
- 账号约有 16 个公开仓库。与 M4/Linux 直接相关的是 `apple-silicon-re`、`agx-re`、`m1n1` 和 `website`；其余仓库目前没有明确的 M4/SPTM 关联。

## 总体进展

ADevWithAnIdea 的公开工作可以分成三条线：

1. 用 clean-room 文档描述 SPTM/XNU-facing 行为。
2. 在 m1n1 fork 中实现实验性 SPTM HLE 和 M4+/T8132 hypervisor workaround。
3. 逆向 AGX G16/G17，并尝试构造 M4/A18 的 GPU userspace/kernel 原型。

这些工作已经超过纯概念阶段，但不能合并成“完整 M4 MacBook Air Linux 已完成”：

- SPTM emulator PR 仍为 Draft；
- SPTM 文档主要以 T8140/T8142 和特定 firmware 为依据；
- AGX closure board 仍显示大量 ABI、ISA、semantic 和 emitter 工作未完成；
- 网站文章中的 M4 Linux/GPU 成功描述尚缺公开的第三方可复现构建、commit、串口日志和 M4 Air 验证矩阵。

## `apple-silicon-re`

仓库：[ADevWithAnIdea/apple-silicon-re](https://github.com/ADevWithAnIdea/apple-silicon-re)

- 默认分支：`master`
- 约 8 个 commit
- 无公开 issue/PR
- 最新相关提交：[`35130fd`](https://github.com/ADevWithAnIdea/apple-silicon-re/commit/35130fd3faa3b79b78e1994199c7417bafb63a72)，`docs: sptm: update README with Exclave support`，2026-08-17
- `agx-re` 作为 submodule 固定在 [`30e3d6a`](https://github.com/ADevWithAnIdea/agx-re/commit/30e3d6a226a560314cb4f707e227c21c53dcdb23)，不一定是 AGX 仓库当前最新状态。

主要资料：

- [SPTM README](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/README.md)
- [XNU bootstrap](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/xnu_bootstrap.md)
- [DART](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/dart.md)
- [UAT](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/uat.md)
- [NVMe](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/nvme.md)
- [RingGate](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/ringgate.md)

### 资料价值和限制

这些文档自述主要来自 MacBook Neo/T8140、M5/T8142、firmware 26.6/27.0 beta 和 KDK 分析，目标是提供 XNU-facing 的 clean-room functional specification。

可用于：

- 设计 SPTM HLE emulator；
- 理解 XNU bootstrap、domain dispatch 和 endpoint 交互；
- 规划 DART/SART/UAT/NVMe/Exclave/RingGate 适配。

不能直接证明：

- T8132/M4 Air 的所有 endpoint 已被覆盖；
- M4 Air 与 T8140/T8142 的结构和寄存器完全相同；
- 文档可直接替代 M4 Air 实机 trace。

文档仍明确存在的缺口包括 DART relaxed-RW、UAT retype/TLBI、GPU carveout、NVMe packed status table、RETYPE 中 GXF 语义，以及 Exclave/RingGate 的版本差异。

## `m1n1` fork

仓库：[ADevWithAnIdea/m1n1](https://github.com/ADevWithAnIdea/m1n1)

### 分支和提交

- `main`：最新已核实提交 [`fc564ba`](https://github.com/ADevWithAnIdea/m1n1/commit/fc564ba4e4098b79ac5e92a0e54a3c6a2980d984)，2026-08-13，sysreg 整理。
- `PUBLIC_neo_agx_bringup`：提交 [`ffe58c7`](https://github.com/ADevWithAnIdea/m1n1/commit/ffe58c7802376b111f67b3cf45d80a1945db1f90)，2026-08-22，T8140/G17P DRM shim 和 AGX 实验。
- `PR_sptm_hypervisor`：2026-08-22 已删除，不能作为当前工作分支引用。

### PR #1：SPTM Emulator

[ADevWithAnIdea/m1n1#1](https://github.com/ADevWithAnIdea/m1n1/pull/1)

- 标题：`Add SPTM Emulator`
- 状态：Open / Draft
- 创建：2026-08-05；最近可见更新：2026-08-15
- 规模：23 commits，约 50 个文件，`+8055/-394`
- 源：`niklassheth:main`
- 目标：`ADevWithAnIdea:main`

主要内容包括：

- M4+/T8132 sysreg 和 CPU power workaround；
- T8132 DCP 初始化交接；
- guest exception、memory attribute、SMP startup 和 USB controller 处理；
- SPTM HLE emulator；
- commpage、AMX policy 和内存 retype workaround。

维护意见要求：

- 分离 emulator 和 hypervisor scaffolding；
- 解释 Python/C 边界；
- 拆分临时 patch 和上游 patch；
- 修正不准确的 hypervisor 描述；
- 支持固定的 26.6 M4/A18 firmware；
- 添加 Signed-off-by；
- 评估全 C emulator。

结论：PR #1 是最直接的公开 SPTM 研究 patchset，但不是已合并、已验证或 upstream-ready 的完整实现。

### PR #2 和 PR #3

- [PR #2：CTRR-like memory region](https://github.com/ADevWithAnIdea/m1n1/pull/2)：Closed/Merged，2026-08-13。处理约 48 KiB 的 memory read-only 边界，目标是降低 M4+/T8132 secondary CPU 和 XNU guest SMP 的随机失败。
- [PR #3：GPL2 license](https://github.com/ADevWithAnIdea/m1n1/pull/3)：Closed/Merged，2026-08-13，merge commit [`fabcd85`](https://github.com/ADevWithAnIdea/m1n1/commit/fabcd85ddab16f62dc559607aaead49eead297b1)。

## `PUBLIC_neo_agx_bringup`

提交 [`ffe58c7`](https://github.com/ADevWithAnIdea/m1n1/commit/ffe58c7802376b111f67b3cf45d80a1945db1f90) 包含约 329 个文件、约 `+100,795/-67`：

- T8140/G17P DRM shim；
- AGX GPU 实验；
- firmware ABI 文档；
- Python/C/Metal 实验和记录。

它针对 A18 Pro/Apple9/G17P，不是 M4 Air 的 T8132/G16G；不能直接当作 M4 Linux GPU 驱动。参考：[T8140/G17P firmware ABI spec](https://github.com/ADevWithAnIdea/m1n1/blob/PUBLIC_neo_agx_bringup/docs/t8140-g17p-firmware-abi-spec.md)。

## `agx-re`

仓库：[ADevWithAnIdea/agx-re](https://github.com/ADevWithAnIdea/agx-re)

- 默认分支：`master`
- GitHub 页面约 758 个 commit
- 无公开 issue/PR
- 公开活动至少持续到 2026-09-09
- 最新已核实提交：[`c677ff9`](https://github.com/ADevWithAnIdea/agx-re/commit/c677ff970ca9d5ab98770100e790f8a62c60a2a0)，`exp(0248): finish full ordering campaign and bound spill readiness`

该实验提交记录 48 captures、18,496 targets、4,608 controls pass 和 3,080 model-count/partition hashes，但 production、latency 和 allocation gates 仍未通过。

M4 资料：

- [M4 deltas](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/m4-deltas.md)
- [M4 roadmap](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/ROADMAP-M4.md)
- [kernel interface](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/kernel-interface.md)
- [porting guide](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/porting-guide.md)
- [P0/P1 closure board](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/P0-P1-CLOSURE.md)

公开 closure 数据表明：

- geometry：567/571 attained，目标 1053；
- liveness：158/1053；
- semantic map：25/1053；
- canonical recipe：2/166；
- G17P direct revalidation：524/1053；
- 约 559/1053 fields 达到 emitter-grade；
- 约 37/166 instructions 可 emittable；
- 631/631 emitter-grade rows 仍被 promotion checker 阻塞；
- 仅少量 rows 有完整 semantic checks。

仍未完成的方向包括 helper/scratch allocator ABI、shader selection、UAPI leaves、partial render、VDM/CDM/PPP/USC relocation、shader container、stage ABI、tilebuffer/interpolation/sysval，以及完整 kernel/userspace integration。

结论：AGX 资料足以启动 M4 userspace driver 原型，但还不能视为完整、稳定、可 upstream 的 Linux GPU stack。

## 网站文章中的额外声明

文章：[I Came, I Prompted, I Left Part 1: Building a Custom Hypervisor for the MacBook Neo](https://github.com/ADevWithAnIdea/website/blob/master/content/blog/hypervisor-macbook-neo.md)

文章公开声称：

- HLE SPTM 可使 macOS 完成 root mount 并进入 userspace；
- A18 prototype kernel driver 已存在；
- M4 Linux userspace/kernel GPU 原型已可运行部分 compositing、Balatro 和 Quake。

这些内容与仓库中的 AGX/SPTM 研究方向一致，但当前仍缺少：

- 对应公开 commit 和完整构建命令；
- M4 MacBook Air 的机型、firmware 和日志；
- 第三方复现记录；
- 完整 iBoot-to-Linux 链路；
- NVMe、USB、网络、音频、电源和睡眠的完整回归。

因此本项目将其标为“作者公开自述，有配套研究材料支持，但尚未达到可复现完成状态”。

## 与本项目的直接关系

可立即参考：

1. [m1n1 PR #1](https://github.com/ADevWithAnIdea/m1n1/pull/1)：SPTM/HLE 代码和 T8132 workaround。
2. [SPTM 文档](https://github.com/ADevWithAnIdea/apple-silicon-re/tree/master/docs/sptm)：XNU-facing 接口和 endpoint 设计。
3. [M4 AGX deltas](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/m4-deltas.md)：G16G 与 G17P 的差异入口。
4. [P0/P1 closure board](https://github.com/ADevWithAnIdea/agx-re/blob/master/docs/P0-P1-CLOSURE.md)：GPU 尚未完成的具体列表。
5. [T8140/G17P 分支](https://github.com/ADevWithAnIdea/m1n1/commit/ffe58c7802376b111f67b3cf45d80a1945db1f90)：A18/Apple9 的 GPU 实验方法。

必须自行补齐：

- M4 Air/T8132 实机识别和 firmware matrix；
- BootKC/XNU shim 到 Linux 的启动链；
- SPTM-aware Linux MM；
- M4 Air 设备树、NVMe、USB、网络、DCP 和电源；
- G16G kernel/userspace integration；
- 可重复的 Nix 构建、串口日志和失败分类。

## 总结

ADevWithAnIdea 的工作已经提供了一个很有价值的研究起点：SPTM HLE、M4+/T8132 m1n1 改动、Apple9 AGX 逆向和 M4 GPU 差异资料都公开可得。但截至本审阅日期，最重要的未知仍是：能否在原版 M4 MacBook Air 上，用固定 firmware 和公开 commit，完成可重复的 iBoot → SPTM → Linux early boot → userspace 链路。
