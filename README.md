# m4-linux

M4 Apple Silicon 上的原生 Linux 支持研究与实现。

本仓库的运行环境固定为：**Asahi Linux M1 控制机 + USB 直连 M4 MacBook Air 目标机**。AI Agent、Nix、构建工具和实验编排全部运行在 M1；M4 只负责实际启动和硬件行为。

## 目标

目标是让 M4，首先是 M4 MacBook Air，能够从 Apple 启动链进入可重复的 Linux userspace，并逐步实现：

- SPTM-aware 启动和内存管理
- SMP、UART、NVMe、USB、网络和基础电源管理
- 显示、DCP、音频和输入设备
- AGX GPU 与 Mesa 用户空间
- 可验证的安装、升级和恢复流程

## 当前判断

M4 的主要新问题不是普通设备树适配，而是 SPTM 位于 EL2 之上的 GL2，并拥有页表和部分系统状态。现有 M1–M3 的 m1n1 hypervisor 路径不能直接作为 M4 Linux 启动方案。

当前优先路线：

```text
iBoot / BootKC
    -> 最小 XNU shim 或等价启动对象
    -> SPTM 初始化和 handoff
    -> SPTM-aware Linux MM
    -> UART/headless Linux
    -> 设备和桌面支持
```

## 文档

- [`docs/NEW_FIRMWARE_GUEST_EXPERIMENT.md`](docs/NEW_FIRMWARE_GUEST_EXPERIMENT.md)：新版实机 timer 解锁验收、完整内存 HLE 断言、16GiB XNU/ApplePMGR panic 与 PTY pitfall

- [`docs/FIRMWARE_UPDATE.md`](docs/FIRMWARE_UPDATE.md)：25G83 stub 资源已安装、SFRUpdateRequired 阻塞及非抹盘 DFU revive 流程
- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)：当前状态、人员、证据和缺口
- [`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md)：讨论结论和历史时间线
- [`docs/SOURCES.md`](docs/SOURCES.md)：公开仓库、PR、提交和 IRC 日志索引
- [`docs/HARDWARE.md`](docs/HARDWARE.md)：M1 控制机、M4 目标机和恢复边界
- [`docs/DEBUG_WORKFLOW.md`](docs/DEBUG_WORKFLOW.md)：USB 直连和自动化实验流程
- [`docs/PROJECT_SKILL.md`](docs/PROJECT_SKILL.md)：持续维护的调试 Skill、Pitfall 和安全约束
- [`docs/SPTM_MACOS_RESEARCH.md`](docs/SPTM_MACOS_RESEARCH.md)：macOS 调试启动的两条 SPTM 路线、固件/FIQ 前提、RAM root 缺陷及实验计划
- [`docs/KERNEL_REPRODUCIBILITY.md`](docs/KERNEL_REPRODUCIBILITY.md)：已保存内核/RAM disk 的版本、来源、哈希及 Nix 复现边界
- [`docs/APPLE_BOOT_RESOURCES.md`](docs/APPLE_BOOT_RESOURCES.md)：Apple 官方 26.6.2/25G83 下载、J713 启动资源、哈希和后续转换边界
- [`docs/ALIGNED_RECOVERY_ROOT.md`](docs/ALIGNED_RECOVERY_ROOT.md)：APFS 根盘提取、对齐保留区、实机读回验证与当前固件阻塞

## 原则

- 先记录可复现事实，再记录推断。
- 每个硬件结论都绑定 SoC、机型、固件版本和测试日志。
- 研究代码、验证脚本、可发布实现和不确定实验结果分开。
- 不把“能编译”“能启动 XNU”或“能启动一个 guest”误报为完整 Linux 支持。
