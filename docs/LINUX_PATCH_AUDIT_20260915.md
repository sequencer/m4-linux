# 当前 Linux / M4 补丁审计（2026-09-15）

## 范围与结论

本次只读核查主机的真实 Nix derivation、源代码、配置及 GitHub 提交历史；没有连接或启动 M4，没有修改内核/loader，没有计算新 hash。上一轮启动检查未发现 `/dev/ttyACM*`，不把 09-14 proxy 验收当作今日实时连接状态。

审计对象是准备使用的 `linux-asahi-7.1.8`，不是 Apple kernelcache，也不是“全世界所有 M4 分支”的穷尽审计。九个额外 patches 已完整枚举；Asahi 基线内部按启动依赖和外设路径核查关键提交。尚未定位公开报告所指多核修复的精确 commit，不声称已经全部闭环。

## 真实构建来源

- 源码：AsahiLinux/linux `asahi-7.1.8-1`，不是 vanilla v7.1.8。
- [发布说明](https://github.com/AsahiLinux/linux/releases/tag/asahi-7.1.8-1)：NVMe macOS 15+ 兼容性修复、idle=nop 等。
- Nix source：`/nix/store/4j4qj317931z732a1nb15qhf5lhz9vbk-source`。
- Nix kernel derivation：`/nix/store/h1n8rdqdfpnf0n1gmj8ijgiqjj6vsd4v-linux-asahi-7.1.8.drv`。
- Image/DTB：`/nix/store/fcvsa2icqlbb3hha99j303p7qrh02xwi-linux-asahi-7.1.8`。
- config：`/nix/store/6fx16rs0ib622iz6hgdmfyvdiym4fc32-linux-asahi-7.1.8-dev/lib/modules/7.1.8/build/.config`。
- 源码下载 derivation `q54hdbbmp920jpa64z4aqzqw4p4hf8av-source.drv` 明确记录 tag URL。
- kernel derivation 记录了下面九个额外 patch 和 Nix 构建处理；不能只复制源 tarball 就声称重现同一内核。
- m4-linux flake 当前只提供 RAM initramfs，没有独立声明这个 Linux kernel package。现有 Image 来自主机 Nix 系统，尚未转成项目自身完整构建入口。

## 九个额外 patch，按实际应用顺序

| # | patch / 作者 | 作用 | 对 J713 首次启动的关系 |
| --- | --- | --- | --- |
| 1 | asahi-dp-alt-tipd-data-status / Janne Grunau，44289ee9 | CD321x 记录 data_status_changed | Type-C 显示链，不是 M4 CPU 启动补丁 |
| 2 | asahi-dp-alt-tipd-drm-oob-hotplug / Janne，02113c7d | 从 CD321x 向 DRM connector 发送 OOB 热插拔事件 | 不会凭空带来 M4 Type-C/DCP 支持 |
| 3 | asahi-dp-alt-oob-init-retry / local | connector 尚未注册时重试 HPD；释放 fwnode 引用；修改 DRM OOB API 返回值 | 主机显示启动时序补丁，涉及共享 DRM API |
| 4 | asahi-dcp-poweroff-swap-timeout / local | DCP poweroff 等 clear-swap 的超时从 50ms 改为 1s并打印超时 | 超时策略调整，不可称为 UAF 根因修复 |
| 5 | 6fc52d7d70bca070a321863e86f46207eeae6f2d / Janne | t8103-jxxx 开启 DP-alt DT hacks | M1 专用，不改变 t8132 |
| 6 | asahi-dp-alt-j313-sio / local | 给 t8103-j313 添加 sio alias | J313 是 M1 Air，不是 J713 |
| 7 | 383d3b670a533e239244b288ffe6f696ba4c29c4 / Janne | M1 ps_atc1_common always-on，绕过 PHY suspend/resume 缺口 | M1 专用 |
| 8 | 7eeff74d22193d0a31753ca524bc31f4535e6ba9 / Adi | ATC PIPEHANDLER lock 超时 1ms→100ms | 共享 PHY 驱动，但当前 J713 没有对应设备链 |
| 9 | randstruct-provide-seed-5.19 / Nix packaging | 构建 seed 输入可复现 | 与 M4 硬件支持无关 |

1/2 是头文件路径适配到此基线后的 patch；patch 自述其代码语义保持原提交。local patch 不擅自归到上游维护者名下。完整实际路径在 `experiments/2026-09-14-linux-ram/raw/kernel-derivation.json` 的 structuredAttrs.patches。

## Asahi 基线内真正相关的提交

### DT、CPU、中断、基础外设

- Yureka Lilian：[fbf2e630](https://github.com/AsahiLinux/linux/commit/fbf2e630a95d1a084220f8dcea54aa85065481bb)，最小 t8132 DT。一次提交包含 Makefile、六个机型 DTS、公共 jxxx、PMGR dtsi、SoC dtsi。当前代码是带 26.6b3 成功说明的版本，不应误称为后来邮件 v3 的逐字相同版本。
- Janne Grunau：[1f0cf051](https://github.com/AsahiLinux/linux/commit/1f0cf05155175849e2f747d26ef1d59e97e280db)，AICv3 IRQ 配置偏移支持，Sven review。t8132 DT 通过 `apple,t8122-aic3` fallback 匹配，驱动里没有 t8132 字符串不代表没支持。
- Yureka：[13e700ef](https://github.com/AsahiLinux/linux/commit/13e700ef0d2286b50a0756036e040d2e71e28de6)，idle=wfi/yield/nop。已经进入本机基线；不会自动改变 delay() 的 WFxT 分支。
- Apple cpuidle 的现有初始化白名单截至 M3，没有 t8132/t604x。CONFIG_ARM_APPLE_CPUIDLE=y 不意味着在 M4 注册深睡驱动。不能将新版报告“driver 接管后保存状态”无条件套到此构建。
- WFxT override 缺失：`arch/arm64/kernel/pi/idreg-override.c` 无 wfxt field/arm64.nowfxt alias；`arch/arm64/lib/delay.c` 在 ARM64_HAS_WFXT 下仍执行 WFIT/WFET。`idle=nop` 与 `cpuidle.off=1` 不能替代该缺项。
- SME 开启，但 arm64.nosme alias 存在；禁用可作为早期参考的实验条件，不是声称硬件永久不支持 SME。
- SMP：spin-table DT 与通用内核启动路径存在；实际 boot CPU 是 P 核 SMP ID 6。m1n1 修正 DT 时必须保留实际 boot MPIDR。尚未定位公开多核修复的唯一精确提交，首轮单核验收不代表解决 SMP。

### NVMe：已包含的固件修复不是“还没做”

以下 Sven Peter 提交都可在本机 tag 的 apple.c 历史中确认：

1. [07133e8a](https://github.com/AsahiLinux/linux/commit/07133e8a2fb8e8c4caa0eef3b3c9bb6b9a395940)：无数据传输时不设置 DMA direction，避免错误的 PRP 检查。
2. [835cbc42](https://github.com/AsahiLinux/linux/commit/835cbc4205acff2f6af7f1b63a69c2b19154aa61)：NVMMU TCB opcode 固定为零，符合新固件要求。
3. [c3d4bb4f](https://github.com/AsahiLinux/linux/commit/c3d4bb4f1caba82170a36ec8a454b71915a8f5ee)：admin queue buffer 按控制器页对齐；依赖 core.c/nvme.h 的 NVME_QUIRK_ADMIN_PAGE_ALIGN 路径，不能只摘 apple.c。
4. [a4f6716c](https://github.com/AsahiLinux/linux/commit/a4f6716c6a69ce98b9850c9ce4ada5be975fe846)：移除 PRP null-check chicken register 写入，新 macOS 15+ 固件访问该寄存器会 SError。
5. [9c02d723](https://github.com/AsahiLinux/linux/commit/9c02d723ef803dd08423fda8f3b89296da051727)：移除时销毁 admin queue，配套资源生命周期处理。

Janne、Nick Chan 对该固件修复系列提供 Tested-by；Nick 的 pre-M1/A11 支持是依赖背景，不应错误描述成 Nick 实现了全部 M4 NVMe。

然而：J713 DT 没有 NVMe、SART/相应映射和协处理器依赖链，CONFIG_NVME_APPLE=m，RAM initramfs 不含模块。因此这个镜像不能靠已经包含上述提交就自动探测 SSD。09-06 IRC 又讨论 >=M4 completion queue/寄存器语义和 entry65，不能把早期固件兼容系列当作所有后续队列问题的完整修复。

## J713 实际设备树和配置矩阵

| 功能 | DT / 配置 | 当前可作何结论 |
| --- | --- | --- |
| CPU | 6E+4P，spin-table | 有描述，需 m1n1 按实际硬件修正 |
| AIC3 | core/event 两段 reg；APPLE_AIC=y | 基础 IRQ 驱动已内建 |
| timer | arm,armv8-timer | 基础时钟事件路径存在 |
| PMGR | 两组控制器及 t8132-pmgr.dtsi；PWRSTATE=y | 提供基本电源域，不等于 DVFS/休眠完整 |
| UART | serial0 enabled，SERIAL_SAMSUNG=y | 物理 UART console；不是 ACM1 |
| framebuffer | loader 填地址/format；simpledrm/fbcon=y | 可以尝试屏幕日志，不是 DCP 驱动/GPU 加速 |
| GPIO | DT 有，PINCTRL_APPLE_GPIO=m | RAM 根没装模块，不保证 probe |
| I2C | 五个控制器均 disabled | 不能把节点存在当设备已启用 |
| 键盘背光 | J713 fpwm1 enabled，PWM_APPLE=m | 没模块不会自动得到背光控制，更不是键盘输入 |
| NVMe/DART | J713 无对应链；NVME_APPLE/APPLE_DART=m | 不具备当前 SSD 启用条件 |
| USB/PCIe | J713 无对应节点链 | 内核有通用驱动也不会自动探测 |
| GPU/DCP | 无完整设备链 | 只能复用启动 framebuffer |
| 内置键盘/触控板 | 无 MTP/SIO 等完整链 | 不能期待交互输入 |
| Wi-Fi/BT/音频/摄像头 | 无 J713 完整描述/固件装载链 | 首轮不具备 |
| NVMe/SEP/PMP/NVRAM 节点 | 最小 J713 DT 中不存在 | 不要按完整 M1 DT 想象一大批必须删除的节点 |

T8132 DTS 还存在 model 中年份写 2024、文件描述为 2025 的文字不一致；它不是启动阻塞，不顺手修改。

## m1n1 与 Linux 补丁不能混算

固定 ADev PR head 7e43bb1763ff97d661bbddb213596eda9475ae6a，flake 额外改动：

- HV Python 中一个 regs[0] 判定由零扩展成 <2^32。
- hv_sptm_init.c 在缺 sart-ans 或 ans 时跳过对应 SPTM 初始化。

这不是 Linux WFxT/NVMe/M4 DT 补丁；首次 native Linux 不需要 SPTM HLE。loader 仍须处理当前 ADT→FDT、initrd、cache flush、DAIF 与 kboot handoff。kboot 的 ISP/USB/PCIe/DAPF 初始化与 Linux DT 是否有那些设备并非完全绑定，不能称 RAM 根保证无硬件副作用。

## 当前分支与缺口

本次 GitHub API 查询 asahi-wip 的 t8132.dtsi 最近历史仍为 fbf2e630；NVMe 最近历史仍包含上述同一系列；override 最近提交列表没有 WFxT 补丁。仅换一个“更新分支”的名字不构成补丁对齐。历史窗口不是对所有其他分支的穷尽否定。

尚待闭环：

1. 在项目 Nix 中声明独立 Linux 构建，固定基线/config/补丁，不继承 M1 显示实验补丁作为 M4 必需条件。
2. 获取并审查 WFxT override 原补丁，将 idle=nop 和 WFxT 一起落实；目前未应用。
3. 确认多核修复的精确分支/提交以及现有 m1n1 secondary handoff 的差异。
4. NVMe 完成 DT、依赖模块/固件、queue register 语义及实机读写验收，不能只回报驱动 commit 已有。
5. 主机自动化可观测性：direct handoff 后 ACM 不继续提供 native console；framebuffer 心跳仅是首轮标记。

保存的 GitHub API 原始证据位于 `experiments/2026-09-15-linux-patch-audit/raw/`，包括 nvme/aic/smp/cpuidle 及当前 asahi-wip 对比。raw 是否进入 Git 取决于 ignore 规则，不声称已提交。
