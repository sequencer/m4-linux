# 25G83 Recovery RAM root 与启动门槛

## 离线根盘

2026-09-13，在 M1 上将已校验的 Apple 25G83 BaseSystem UDIF 解码成 GPT raw，
校验 GPT header/table CRC，选取唯一 APFS 分区并复制到新的文件起点。
没有挂载或读取 M4 的原 System/Data，也没有修改原始 DMG 或旧 25E253 输入。

| 输入/产物 | 值 |
|---|---|
| 解密 UDIF SHA-256 | `eeda386b1fb66a313cadef26e3e7ee06643d4d5ea8b3330a411a118ac7d14ed3` |
| 解码 GPT raw 大小 | `1574995456` 字节 |
| GPT raw SHA-256 | `75ad9b16a77753db7e8c22be5cdb517491572658da11b06309ab96b7d73ee719` |
| APFS 在 GPT 内的 offset | `17408 = 0x4400` 字节 |
| APFS 大小 | `1574961152` 字节 |
| APFS block size / count | `4096 / 384512`，乘积等于分区大小 |
| 提取 APFS SHA-256 | `bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a` |

新的 `recovery-25G83.apfs.raw` 起点具有 NXSB，不带 GPT，物理上传起点要求 16KiB 对齐。
只改变 ADT 指针加 `0x4400` 会导致 XNU memdev 的页移位丢失 `0x400`，本次使用完整复制避免该问题。
NXSB/geometry 验收不等于 root mount 或 launchd 验收，尚不证明 Recovery userspace 能运行。

依赖通过 `flake.nix` 的 `ram-root-tools` 与 devShell 中的 `dmg2img` 提供。
在项目根目录复现到一个不存在的输出路径：

```sh
nix develop --command python scripts/prepare-recovery-root.py \
  artifacts/apple/25G83/derived/022-22048-093.dmg \
  experiments/2026-09-13-aligned-recovery/raw/recovery-25G83.apfs.raw \
  --source-sha256 eeda386b1fb66a313cadef26e3e7ee06643d4d5ea8b3330a411a118ac7d14ed3
```

已有输出拒绝覆盖；`.whole-disk.raw` 与 `.apfs.json` 同目录保留。

## Launcher 的边界修正

`scripts/run-recovery-guest.py` 不再从 host heap 分配 root。新的布局选择
guest `top_of_kernel_data` 之后的 16KiB 对齐地址，将 root 纳入 guest physmap，
并把实际序列化的 BootArgs `top_of_kernel_data` 提升到 root 保留区末端。
SPTM HLE 随后才在该边界之后分配其 64MiB aux，避免 allocator 覆盖 root。

检查包括：输入内核/root SHA-256，直接 APFS magic，物理范围，carveout 冲突，
ADT 容量，目标 RAM NXSB 头部读回，以及目标 BootArgs 的物理基址、大小和保留末端读回。
每个上传块通过 proxy gzip 解码检查输出长度；不把头部读回称作目标整盘 SHA-256 验证。
guest ANS/NVMe 节点删除，bootargs 使用 `rd=md0` 和 `cpus=1`。

以下命令只准备 RAM，不执行 HLE handoff 或 guest：

```sh
sudo -n nix develop --command python scripts/run-recovery-guest.py \
  artifacts/apple/25G83/derived/kernelcache-25G83.macho \
  experiments/2026-09-13-aligned-recovery/raw/recovery-25G83.apfs.raw \
  --kernel-sha256 f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d \
  --root-manifest experiments/2026-09-13-aligned-recovery/raw/recovery-25G83.apfs.json \
  --output experiments/2026-09-13-aligned-recovery/raw/memory-preparation.json \
  --prepare-only
```

输出路径应为新实验路径。RAM 内容不能跨 reboot 保留，换固件后必须重新计算布局和上传。

### 本台 RAM 准备验收

完整 `1574961152` 字节根盘已实际上传，目标 NXSB 头部、BootArgs 和最终 ADT 全部读回一致，
UART/proxy 双 NOP 通过。`raw/memory-preparation.json` 与非 raw 的同名快照保存结果。

| 区域 | 本次地址，不可跨重启复用 |
|---|---|
| guest 物理范围 | `[0x1001e8a0000, 0x107d09a4000)` |
| APFS RAMDisk | `[0x1002726c000, 0x1008506c000)` |
| 写回的 top_of_kernel_data | `0x1008506c000` |
| 后续 HLE 64MiB aux 规划 | `[0x1008506c000, 0x1008906c000)` |

此时尚未执行 HLE 初始化，aux 是已检查的未来分配范围，不能称作已经建立 XNU stage-1 页表。
内核/root 位于 BootArgs 描述的 guest 物理区域，HLE 未来建立的线性映射可涵盖 root。
最终 ADT 另经实际上传和完整 blob 读回验证，guest ANS 节点已删除。
全程没有执行 guest，原用户卷未由 guest 挂载。

## 本台 timer 前提的实测

17:47:52 UTC，proxy 在异常保护 `GUARD.SKIP` 下执行 EL2 的
`VM_TMR_FIQ_ENA_EL2` 读取和原值写回。
读取 `0xf` 成功；写同一个值仍产生可捕获异常。保护清除后 UART/proxy NOP 成功，
没有启动 guest，也没有像旧实验那样由未保护 EL2 fault 导致自动重启。

live ADT 的 system firmware、iBoot stage-one 和 stage-two 均仍为 `mBoot-18000.101.7`。
下载新固件、解包新 KC 和上传对齐 root 没有改变这个事实。
实际启动请求也经过同一门槛检查并被拒绝，证据为 `raw/start-gate.json`。
不能靠删除 FIQ register 写入或再次关闭 SIP 假称修复。

复测入口：

```sh
sudo -n nix develop --command python scripts/sptm-hv-preflight.py \
  --probe-timer --output experiments/2026-09-13-aligned-recovery/raw/timer-preflight.json
```

这是受保护的硬件写探测，不是只读检查。失败退出码为 2；不会继续 HV.init/start。
每次只允许一个进程占用目标 proxy，不能并行运行上传、preflight 或 shell。

## 必须先处理的下一步

进入实验 stub 的配对 Recovery，先按卷组 UUID 检查 `bputil`、Preboot、Recovery 与实际资源，
备份实验启动目录和当前启动对象；随后制定并执行完整匹配的 25G83 资源更新/个性化步骤。
不是用几个新版 IM4P 覆盖旧文件，也不是写主用户卷或重新安装完整 macOS。
更新后重启，核对实际 stage tags 并复测 timer。只有前提成立才准备 root 并运行 guest。

启动阶段还需要核对匹配的 TrustCache/SEPFW/ADT；当前 RAM-only 准备仍沿用了 live stub 的这些输入，
不能把准备好的新版内核/root 称作完整匹配的新版 boot chain。
同时需 RAM chainload 已保存的 optional-ANS m1n1 或安装相应独立实验构建，
未经修正的原始持久化 PR 会在缺失 ANS 初始化路径失败。

配对 Recovery 的入口见 `docs/MINIMAL_STUB.md`。M1 的临时 HTTP helper 仍在 `172.25.27.108:8000`；
Recovery 终端执行：

```sh
curl -f http://172.25.27.108:8000/ssh.sh -o /tmp/ssh.sh && sh /tmp/ssh.sh
```

不要在 RAM 上传还运行时关机。持久化更新与本次 RAM 实验分开记录，
进入 Recovery 后先确认具体更新范围与恢复路径，再修改实验卷。
