# Linux 启动参考核对 — 2026-09-14

## 现场边界

用户要求先研究参考如何启动，暂停 live boot。当前最后一次实机验收为 15:22:30 的原生 m1n1 UART/proxy NOP 成功；本轮 Linux Image、DTB、initramfs 尚未上传，没有执行 kboot_prepare_dt/kboot_boot，没有重启或进入 Recovery。

主机已构建 `results/linux-ram-initramfs`（Nix 静态 BusyBox，/init 可执行，只挂载 devtmpfs/proc/sys，输出 marker/心跳）；`scripts/boot-linux-ram.py` 是未实机验证的草稿，不是已复现成功的启动命令。用户不允许重新进入 Recovery；本轮不改变启动策略、磁盘或 iSC。

## 三条不同启动路线

1. 原生 Linux：mBoot → raw m1n1 EL2 → USB proxy 上传 Linux Image、机型 DTB、RAM initramfs → m1n1 修正 FDT → Linux。不要求先启动 SPTM/XNU。
2. Linux HV 调试：外层 m1n1 HV → 内层 m1n1 payload → Linux。USB VUART 可以继续提供 guest console，但原生 SMP 成功与 HV trap WFI 后成功不是同一验收。
3. XNU 逆向：m1n1 HV → SPTM HLE 或真实 SPTM 的 GXF/SPRR 模拟 → XNU。用于观察 Apple 驱动，不是 Linux 启动先决条件。

官方方法：[Tethered Boot](https://asahilinux.org/docs/sw/tethered-boot/)。直接启动使用 `proxyclient/tools/linux.py -b '<args>' Image.gz board.dtb initramfs.cpio.gz`；HV 使用 `tools/run_guest_kernel.sh`。文档中的 M1 Pro DTB、NVMe root 分区不能复制到 J713。我们固定版本的 linux.py 另支持未压缩 Image，但必须显式 `--compression none`，auto 不识别无后缀的 Image。

## 可核实案例

| 时间/人员 | 硬件与方式 | 实际证据及边界 |
| --- | --- | --- |
| 06-21 mischa85 | t6041，原生 Linux | 17:41 报告 framebuffer 上进入 userspace；单核、nohlt、保留 clocks/power domains、内核禁 SME。其 WFE 丢状态说法立即被 Sven 质疑，不能当成已证实根因。 |
| 06-24 yuka / flokli | M4 Pro，chainload kernel | yuka 提供 idle=nop，flokli 运行硬件验证；最小配置成功，扩大配置仍需要单核规避早期崩溃，多核试验成功率不稳定。 |
| 07-01/02 mischa85 | t6041，Linux HV | 16 核成功依赖 HV 捕获 WFI/WFIT；不能引用为 16 核原生成功，07-02 又明确报告原生失败。 |
| 08-11 Yureka Lilian | base M4 / t8132，Mac mini | v3 DT 补丁描述 26.6 固件下单核可靠启动；包含 J713/J715 等 DT，但未由该文字证明 M4 Air 全设备可用。 |
| 08-28 yuka / sven | M4 Pro / t6040 | 14:21 Sven 问 t6040 DT；14:32 yuka 给最小可启动 DT；14:43 明确需要 WFxT override 补丁和 idle=nop arm64.nowfxt。不是 J713 的完整配方。 |

IRC 原始文件在 `/home/sequencer/projects/catirclogs-asahi/asahi-dev/`，上述日期文件及具体时间可定位。06-24 11:12 flokli 明确区分自己的 chainload 测试与 yuka 的实现工作。

参考链接：

- [Yureka t8132 v3 DT](https://lists.infradead.org/pipermail/linux-arm-kernel/2026-August/1160792.html)
- [06-24 初版 idle=nop，IRC 所贴提交](https://cyberchaos.dev/yuka/linux/-/commit/3bf49bf384d90f91503369de26a09380bd88bf77)
- [08-28 t6040 最小树，IRC 所贴提交](https://cyberchaos.dev/yuka/linux/-/commit/3c110f4fff547a110dddb4ed0def29659e2cc9c5)
- [WFxT override 原始邮件入口，IRC 所贴；本次网页正文抓取失败](https://lore.kernel.org/all/20260811-idreg-override-wfxt-v1-1-1c71228d0719@cyberchaos.dev/)

提交链接与邮件链接不代表已将补丁获取、应用或验证。本次已读取 IRC 推荐及本机源码，未完成上述远端提交逐行审计。

较新的[官方 7.2 进展](https://asahilinux.org/2026/08/progress-report-7-2/)报告 Yureka/Sven 已实现 M4/M5 新 NVMe 固件接口，Yureka 还推进 PCIe 枚举并修复多核启动后崩溃。因此不能把 08-11 的单核限制当作所有当前开发分支的最终状态；报告也不意味着本地 7.1.8 自动具备这些改动，或 M4 已可用官方安装器。

07-18 的参考讨论明确使用 linux.py 上传 kernel/initrd，并指出交接 Linux 后 CDC ACM 端口不再工作；该段包含 M5 bringup，不能把其中禁用 DAPF 的临时修改直接当成 M4 Air 必需补丁。同日晚又建议保留 MTP 的 DAPF 项，而不是全部删掉。

## ADev 两个参考的适用范围

- [apple-silicon-re XNU bootstrap](https://github.com/ADevWithAnIdea/apple-silicon-re/blob/master/docs/sptm/xnu_bootstrap.md)：构造页表、handoff 结构、guest EL1 寄存器，再跳 kernelcache 的 _start；SPTM 文档描述将 genter 改为 HVC 并模拟端点。这是 XNU 合约，不是 Linux arm64 Image/FDT 合约。
- [m1n1 PR 1](https://github.com/ADevWithAnIdea/m1n1/pull/1)：项目固定 7e43bb1763ff97d661bbddb213596eda9475ae6a 加现有补丁；有 SPTM 功能不等于其 native Linux kboot 在 J713 已验证。
- [agx-re](https://github.com/ADevWithAnIdea/agx-re)：README 定义为 G16/17 GPU userspace 逆向、live probing。可以辅助后续 GPU 工作，本次没有找到可作为 J713 Linux 从启动到 rootfs 成功证据的配方。
- Sven 的 GXF/SPRR 模拟运行真实 SPTM，与 ADev 的 XNU-facing HLE 不同；两者均不应强加为首次原生 Linux 的前置工作。

## 当前主机候选内核的实际缺项

候选输出 `/nix/store/fcvsa2icqlbb3hha99j303p7qrh02xwi-linux-asahi-7.1.8`，源码 `/nix/store/4j4qj317931z732a1nb15qhf5lhz9vbk-source`，有 `Image` 和 `dtbs/apple/t8132-j713.dtb`。不能使用主机 M1 的 initrd 作为 M4 RAM 根。

- `arch/arm64/kernel/idle.c` 有 idle=nop，但草稿只传 cpuidle.off=1。关闭 cpuidle 框架不等于禁用默认 idle 中的 WFI。
- `arch/arm64/lib/delay.c` 仍会在 ARM64_HAS_WFXT 时执行 WFIT/WFET。
- `arch/arm64/kernel/pi/idreg-override.c` 的 isar2.fields 无 wfxt，aliases 无 arm64.nowfxt。仅追加参数不能获得不存在的 override 支持；应通过 Nix 应用对应补丁/选择确实包含它的内核后重建。
- 本机 CONFIG_ARM64_SME=y；源代码支持 arm64.nosme。早期成功案例禁用了 SME，首轮复现可采用相同限制，但不宣称现阶段所有 M4 内核均必须关闭 SME。
- 16K 页、initrd/gzip、AIC、simpledrm、fbcon、Samsung UART 均已配置；有驱动/DTB 不等于当前硬件已验证。

## Loader 和可观测性纠正

固定 m1n1 源 `/nix/store/vppihl1f21anrvbrw28y25b7zfvc8nvl-source`：

- 原 linux.py 调用 cpufreq_init、smp_start_secondaries，再 prepare DT、上传 kernel、清缓存、DAIF=0xc0、kboot_boot。新草稿跳过前两步；这是差异，不是已证明等效。
- kboot.c 的 dt_set_cpus 保留实际 boot MPIDR，删除未 alive 的其他 CPU，并修正 cpu-map/AIC affinity。当前启动核为 P 核 SMP ID 6，不能误留第一个 E 核而删除实际启动核。
- kboot_prepare_dt 会执行 ISP 等 helper；kboot_boot 还会调用 USB/PCIe/DAPF 初始化。RAM root 不等于整个启动过程没有硬件副作用。不能盲删所有 DT 节点，也不需要添加新防御框架。
- direct handoff 后 m1n1 USB proxy 消失是正常可能结果，不足以证明 Linux 崩溃。现有 ACM1 是 HV VUART，不是原生 Linux USB console。
- console=tty0 使用 framebuffer console；earlycon 默认走 DT stdout-path 的 UART，不会自动转成 ACM。
- earlycon=efifb 也不是任意 framebuffer 通用早期日志开关：本机 drivers/firmware/efi/earlycon.c 依赖 EFI screen_info 且 depth=32；当前 m1n1 framebuffer 是 30bpp，直接 FDT 启动没有自动建立 EFI screen_info 的保证。不能据该参数承诺早期屏幕日志。

## 下一次实验应复现什么

先完成 Nix kernel 的 WFxT override 补丁对齐，明确使用 idle=nop、单核、必要时 arm64.nosme；使用 J713 最小设备树和独立 RAM initramfs，以屏幕上的 M4_LINUX_RAM_INIT_OK/持续心跳作为 userspace 验收。参数、具体 m1n1/Linux 版本、DTB 和实际加载文件路径一并记录，不计算新 hash。

先复现 native Linux，再另行补 USB/network console、多核、NVMe 和其他外设；不为了首次 Linux 启动重新运行 Recovery/XNU/SPTM guest，也不为消除无害的 unsupported 提示盲改硬件初始化。本次止于参考研究与主机准备，未进行这项实验。
