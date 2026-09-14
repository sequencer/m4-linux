# 资料索引

## 本地 IRC 日志

日志仓库：`/home/sequencer/projects/catirclogs-asahi`

重点频道：

- `asahi-dev`：主线开发、m1n1、Linux、设备驱动和平台 bring-up。
- `asahi-re`：SPTM、GXF、iBoot、XNU 和其他逆向细节。

重点日期：

- `2022-03-03`：SPRR/GXF emulation 的早期讨论。
- `2024-07-14`：SPTM 分层和 M4 启动模型。
- `2026-02-10`：M4 与 M2/M3 的 SPTM 差异。
- `2026-05-10`：HLE SPTM 方案、法律隔离和 nested guest 讨论。
- `2026-05-19`、`2026-05-28`：Exclave 开关和接近 userspace 的实验状态。
- `2026-06-20`、`2026-06-23`：稳定性、timer、SPMI 和 cache 问题。
- `2026-07-03`、`2026-07-09`：GXF/RETYPE 和 upstreamable hypervisor。
- `2026-07-21`、`2026-07-22`：SPTM guest、custom KC 和 Linux 页表限制。
- `2026-09-08`：cL4/ExclaveOS secondary guest 和 Tightbeam handoff。

## 公开仓库和 PR

- https://github.com/ADevWithAnIdea/m1n1/pull/1
- https://github.com/ADevWithAnIdea/apple-silicon-re
- https://github.com/ADevWithAnIdea/agx-re
- https://github.com/antiapplefox/m5-linux
- https://github.com/rusch95/asahi_neo
- https://github.com/lily-oc/m4-asahi-installer-checklist
- https://github.com/AsahiLinux/m1n1/pull/675
- [`docs/ADEV_WITH_AN_IDEA.md`](ADEV_WITH_AN_IDEA.md)：ADevWithAnIdea 全部相关公开工作的独立审阅

## 资料使用规则

- IRC 中的个人陈述记录为“实验报告”，不自动视为已验证事实。
- GitHub README 的“能编译”不等于“硬件可启动”。
- 任何可复用实现都必须补充 commit、版本、硬件、日志和失败条件。
- AGX、SPTM 和 XNU-shim 资料分别验证，避免把一个子系统的成功外推到完整 Linux 支持。
