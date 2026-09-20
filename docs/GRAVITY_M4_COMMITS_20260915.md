# GravityLinux gravity-m4 提交清单 — 2026-09-15

## 固定快照和计数口径

查询 head：9807df349e5c8903f81a25c24c1fc72a523d2e10，最新提交作者时间 2026-09-15T04:53:15Z。不是永远有效的分支总数。

GitHub compare 验证 b39c4d031b5a3cc6ead603987966f5a48af4bd28..head：ahead 42 / behind 0 / returned 42。42 个均为单父提交，无 merge。b39c4d 是前一个 Asahi bits/500-backports 合并边界；它是本次“顶部扩展栈”的明确统计基点，不声称整个分支只有42提交。

分类：
- 36 个直接 M4 功能/平台提交：21 GPU + 4 NVMe（含binding/DT/mini启用）+ 3 DCP/HDMI/debug + 1 KVM + 7 其余平台（最小DT/SMC/USB/PCIe/pwrctrl/Wi-Fi电源）。
- 3 个 SMC gp00 GPIO 依赖提交：计入 M4 相关依赖时为39。
- 3 个通用配套（supplier诊断、Rust构建检查、Broadcom BT命令）：完整顶部栈为42。
- 作者：Niklas Sheth13，Cody Ho13，Yureka Lilian10，Janne Grunau4，Sasha Finkelstein2。
- 这些是作者字段统计，不等同于独立原创数；有cherry-pick、集成说明和AI辅助标注。

与当前 Asahi tag 96fa2b9c825bd42c3ea4dc8c8adb6182e5016f51 比较：分叉，Gravity侧758、Asahi侧28，共同祖先25c76bea853d0db65b51fb4697a47cbfd9e35e76。758包含通用Linux/Asahi历史，不能报作758个M4补丁。
与Gravity master比较：5523 ahead/35574 behind，也不能报作M4补丁数。顶部历史含Linux7.1.13；不是简单在我们7.1.8上加42个互相独立补丁。

## 逐提交清单（新→旧）

| # | 提交 | 作者 | 分类 | 标题 |
| --- | --- | --- | --- | --- |
| 1 | [9807df349e5c](https://github.com/GravityLinux/linux/commit/9807df349e5c8903f81a25c24c1fc72a523d2e10) | Niklas Sheth | M4 GPU | drm/asahi: release M4 buffer backing after VM unmap |
| 2 | [7c3d0bb604fe](https://github.com/GravityLinux/linux/commit/7c3d0bb604fe641d62577bd6276e50e5b3cc7754) | Niklas Sheth | M4 GPU | drm/asahi: report the M4 GPU revision from hardware |
| 3 | [1ab42a3a62f6](https://github.com/GravityLinux/linux/commit/1ab42a3a62f629b08cb874bf19f49a990e8c764b) | Niklas Sheth | M4 GPU | drm/asahi: handle M4 firmware counter rollover |
| 4 | [11b95e898731](https://github.com/GravityLinux/linux/commit/11b95e898731a2a17971db899b1fa88002430bc7) | Niklas Sheth | M4 GPU | drm/asahi: share software floating point with the M4 driver |
| 5 | [3a2ad760d731](https://github.com/GravityLinux/linux/commit/3a2ad760d7316813f37c0ddc653ef783827f855b) | Niklas Sheth | M4 GPU | drm/asahi: wire M4 GPU into the T8132 desktop platform |
| 6 | [2a8d511f64ea](https://github.com/GravityLinux/linux/commit/2a8d511f64eaf70aa1099ac352e4a9e95d8418e5) | Niklas Sheth | M4 GPU | drm/asahi: report pending M4 work on unowned firmware events |
| 7 | [63e8a1d7268c](https://github.com/GravityLinux/linux/commit/63e8a1d7268ca75c32b9bde543d3b4f6e59d6a75) | Niklas Sheth | M4 GPU | drm/asahi: retire M4 GEM mappings when handles close |
| 8 | [c41b69fe9a3a](https://github.com/GravityLinux/linux/commit/c41b69fe9a3a6cdd9efe7697efa69a40eba17c83) | Niklas Sheth | M4 GPU | drm/asahi: adapt M4 to the desktop kernel |
| 9 | [d3ed57579b19](https://github.com/GravityLinux/linux/commit/d3ed57579b19fbcc4a1d35da9d89194e8505016a) | Cody Ho | M4 GPU | drm/asahi: enable native M4 render scheduling and share completion stamps |
| 10 | [eb68e9220f87](https://github.com/GravityLinux/linux/commit/eb68e9220f87a6208c7581a50f88373973fccf15) | Cody Ho | M4 GPU | drm/asahi: reuse M4 Work and scratch after notifier retirement |
| 11 | [74e2713772ee](https://github.com/GravityLinux/linux/commit/74e2713772ee4fa90e47551741276a4e0aa9cd6a) | Cody Ho | M4 GPU | drm/asahi: index M4 memory and queue pending cache cleans |
| 12 | [038dab903d3e](https://github.com/GravityLinux/linux/commit/038dab903d3ee943199d6b87830aa53df23b889f) | Cody Ho | M4 GPU | drm/asahi: queue M4 dependencies in firmware and share compute roots |
| 13 | [4f7fe10829db](https://github.com/GravityLinux/linux/commit/4f7fe10829db4fb7d0a2601d7981b8b929b9dbf7) | Cody Ho | M4 GPU | drm/asahi: batch M4 submissions and scope mapping synchronization |
| 14 | [037892793e68](https://github.com/GravityLinux/linux/commit/037892793e680ef6783f2a12352fb687a0cdb33c) | Cody Ho | M4 GPU | drm/asahi: pipeline M4 engines with independent resource admission |
| 15 | [dc55a9529787](https://github.com/GravityLinux/linux/commit/dc55a9529787b79a5dce587e5bb19e8a418ca0d8) | Cody Ho | M4 GPU | drm/asahi: retire M4 work on firmware notifications |
| 16 | [6e3b4af97495](https://github.com/GravityLinux/linux/commit/6e3b4af97495528e9a838444ea5008b0e5b013f2) | Cody Ho | M4 GPU | drm/asahi: give M4 userspace queues independent firmware queues |
| 17 | [542c48f2d6c8](https://github.com/GravityLinux/linux/commit/542c48f2d6c84d0cdb64769e5c8ff4932ed0624f) | Cody Ho | M4 GPU | drm/asahi: pipeline M4 firmware submissions and retire completions asynchronously |
| 18 | [2338f7c84c46](https://github.com/GravityLinux/linux/commit/2338f7c84c461fc91b37dc728ae8a01379ab9339) | Cody Ho | M4 GPU | drm/asahi: enable local-indirect compute on M4 |
| 19 | [e1a4f50d0fe3](https://github.com/GravityLinux/linux/commit/e1a4f50d0fe3ffcb62c2807a8a87e9fd278080c9) | Cody Ho | M4 GPU | drm/asahi: batch M4 memory publication and clean only dirty pages |
| 20 | [47140964b7f3](https://github.com/GravityLinux/linux/commit/47140964b7f3249a852a82c86b58bd7e7c17b143) | Cody Ho | M4 GPU | drm/asahi: simplify M4 validation and firmware encoders |
| 21 | [bd25d194b0a2](https://github.com/GravityLinux/linux/commit/bd25d194b0a295a75692a0e6caed3793603b9e65) | Cody Ho | M4 GPU | drm/asahi: add asynchronous M4 GPU prototype driver |
| 22 | [b8d4a99bfec8](https://github.com/GravityLinux/linux/commit/b8d4a99bfec8046c99f2e391ab804d6677bcae44) | Niklas Sheth | M4 平台/驱动 | arm64: dts: apple: enable the T8132 Mac mini SSD |
| 23 | [5964a02f1446](https://github.com/GravityLinux/linux/commit/5964a02f144628ae1840a083ce683e4cc2926854) | Niklas Sheth | M4 平台/驱动 | KVM: arm64: Add Apple M4 Donan to broken SEIS workaround |
| 24 | [c23269c95cbd](https://github.com/GravityLinux/linux/commit/c23269c95cbdcb9f05dc6844c1d71b233a42dd8f) | Niklas Sheth | M4 平台/驱动 | drm/apple: add writable DPTX HPD debug control |
| 25 | [49045c3465d2](https://github.com/GravityLinux/linux/commit/49045c3465d21bec855666831e927edf4b3da1cf) | Niklas Sheth | M4 平台/驱动 | drm/apple: bring up T8132 HDMI audio |
| 26 | [877c574dfa4f](https://github.com/GravityLinux/linux/commit/877c574dfa4f31434129b05da6d907abfb21bbef) | Niklas Sheth | M4 平台/驱动 | drm/apple: bring up T8132 DCP hotplug |
| 27 | [79b86cbb4473](https://github.com/GravityLinux/linux/commit/79b86cbb447349043f626b43d03027556c28c840) | Yureka Lilian | M4 平台/驱动 | arm64: dts: apple: t8132: Add NVMe nodes |
| 28 | [8178b0adc214](https://github.com/GravityLinux/linux/commit/8178b0adc2143b3ba2d77c788f19e45a4c9a3ede) | Yureka Lilian | M4 平台/驱动 | nvme: apple: add t8132 (M4) ANS2 NVMe support |
| 29 | [6d5a5c6cbc14](https://github.com/GravityLinux/linux/commit/6d5a5c6cbc14d23cf595183ff81286d7fac31ddc) | Yureka Lilian | M4 平台/驱动 | dt-bindings: nvme: Add apple,t8132-nvme-ans2 compatible |
| 30 | [bdafece9eddb](https://github.com/GravityLinux/linux/commit/bdafece9eddb4f6c107448f85671f5bec6baadf9) | Yureka Lilian | M4 平台/驱动 | t8132 wifi pwren |
| 31 | [de08843902c4](https://github.com/GravityLinux/linux/commit/de08843902c40706ae6ef57e910aef7e80fadc0d) | Yureka Lilian | M4 平台/驱动 | PCI: apple: Integrate pwrctrl API |
| 32 | [42efdd3e653f](https://github.com/GravityLinux/linux/commit/42efdd3e653f6eaf839f9d3cb06ac24af28aa359) | Yureka Lilian | M4 平台/驱动 | PCI/pwrctrl: Export per-device APIs |
| 33 | [9edf52c13ea3](https://github.com/GravityLinux/linux/commit/9edf52c13ea3957e2cf949120e0dc257facea49e) | Yureka Lilian | M4 平台/驱动 | t8132 pcie |
| 34 | [840ac90252e2](https://github.com/GravityLinux/linux/commit/840ac90252e2ef1962c318fbd567efcf29031661) | Yureka Lilian | M4 平台/驱动 | dts: apple: t8132: Add usb/atcphy nodes |
| 35 | [be925f37d4ef](https://github.com/GravityLinux/linux/commit/be925f37d4ef327166b8a94f7303aa038c40b8e5) | Yureka Lilian | M4 平台/驱动 | t8132 smc |
| 36 | [cd5f25a0e4b6](https://github.com/GravityLinux/linux/commit/cd5f25a0e4b68ac8bc3a731a312bb1b7f75dfca3) | Yureka Lilian | M4 平台/驱动 | arm64: dts: apple: Add minimal t8132 (M4) device trees |
| 37 | [3988dac1664c](https://github.com/GravityLinux/linux/commit/3988dac1664c05fa7c8310fcad8eee10428b5f43) | Janne Grunau | SMC GPIO 依赖 | mfd: macsmc: Add second gpio subdevice for 'gp00' keys |
| 38 | [f33138368c9b](https://github.com/GravityLinux/linux/commit/f33138368c9b8c492752d3fcec48ef1dc8b5dbe0) | Janne Grunau | SMC GPIO 依赖 | gpio: gpio-macsmc: Support 'gp00' GPIO keys |
| 39 | [ab76ccfdd0d0](https://github.com/GravityLinux/linux/commit/ab76ccfdd0d0e043b55395b460fa560a32c702a3) | Janne Grunau | SMC GPIO 依赖 | dt-bindings: gpio: apple,smc: Add compatible for 'gp00' keys |
| 40 | [1dd2baabb260](https://github.com/GravityLinux/linux/commit/1dd2baabb26053063c9f41b3c43d2335a596cdf2) | Janne Grunau | 通用配套 | driver-core: Add error message to device_links_missing_supplier WARN() |
| 41 | [2948f58636c5](https://github.com/GravityLinux/linux/commit/2948f58636c55c711369f96542c8a1f2c617291b) | Sasha Finkelstein | 通用配套 | Fail the build on RUST=y and RUST_IS_AVAILABLE=n |
| 42 | [83a128c3aa11](https://github.com/GravityLinux/linux/commit/83a128c3aa112449fc27a6b4b83bb040727a9902) | Sasha Finkelstein | 通用配套 | Bluetooth: Add Broadcom channel priority commands |

## 对当前项目最重要的差异

1. 877c574dfa4f 的DCP hotplug大提交包含 arm64.nowfxt：idreg-override.c 添加wfxt字段及alias。本次读取原diff及head源码已确认，不能继续称该分支缺这个功能。此提交4199添加/233删除，涉及DCP26.6、RTKit、DT、PHY、USB、dockchannel early UART等，不能按标题只当显示小修复。
2. 8178b0adc214：Yureka实现T8132 ANS2，Sven review。IO queue需要额外MMIO注册；create cq/sq的qsize被忽略，0x1210寄存器负责IO queue大小。这是我们前次尚未定位的M4专用队列支持，不是重复老的macOS15固件修复。
3. NVMe还需要6d5a5c6cbc14 binding、79b86cbb4473 DT；b8d4a99bfec8只在j773g启用SSD，不自动启用J713。
4. cd5f25a0e4b6虽与本机最小DT同标题，但不是可直接去重：补L1 cache/J713年份，ps_ans always-on，并禁用锁定display power-domain节点。提交注明不保持ANS会三分钟后重启，这是作者经验，未在我们M4上独立验证，也不能作为此前Recovery故障根因。
5. 5964a02f1446是KVM Donan E/P核broken-SEIS workaround，涉及MIDR、TDIR探测、VGIC陷入；不等于native SMP启动修复。
6. bd25d194b0a2开始GPU Rust原型：8654添加/3删除；之后总共21个GPU提交包含队列、缓存发布、render/compute、completion、GEM/UAT生命周期和desktop集成。作者提交信息声称做过构建/字节对比/M4硬件检查，本次只核查源码与提交信息，未独立验证运行。
7. 3a2ad760d731将GPU DTS接入j773g Mac mini，不是J713。J713仍包括公共t8132/jxxx，不能说毫无公共改进，但该机器文件没有GPU dtsi接入。Mini的HDMI、音频、SSD、GPU启用不能直接照搬Air。
8. GPU集成提交明确描述probe-only default；有GPU提交不等于默认提供完整可用桌面加速。还需匹配用户态UAPI、配置、固件和启动器。
9. idle=nop在head已存在；不把它额外计为顶部42中的独立新增commit。未来做逐patch移植必须按文件/依赖审查，而不是仅按标题计数。

## 证据与边界

- [分支页面](https://github.com/GravityLinux/linux/commits/gravity-m4/)
- [固定扩展栈比较](https://github.com/GravityLinux/linux/compare/b39c4d031b5a3cc6ead603987966f5a48af4bd28...9807df349e5c8903f81a25c24c1fc72a523d2e10)
- [与当前Asahi基线比较](https://github.com/GravityLinux/linux/compare/96fa2b9c825bd42c3ea4dc8c8adb6182e5016f51...9807df349e5c8903f81a25c24c1fc72a523d2e10)

42个提交元数据/parent计数已核查；NVMe、最小DT、DCP大提交、KVM、GPU原型、GPU平台接入、SSD启用的详细diff/文件列表已重点核查。不是42个提交每一行都完成正确性审计。本次未应用、构建、启动或写入M4。
