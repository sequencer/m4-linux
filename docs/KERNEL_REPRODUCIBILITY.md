# 内核资产与可复现边界

## 已保存的输入

资产实际保存在本项目 experiments/2026-09-13-sptm-macos/raw/，不是仅存在 M4 或 /tmp。

| 文件 | 版本 | 字节数 | 来源/用途 |
| --- | --- | ---: | --- |
| kernelcache.release.mac16g.im4p | 26.4.1 / 25E253 | 32027045 | 新 stub Preboot 的 restore/kernelcache.release.mac16g；本次 guest 输入 |
| kernelcache-25E253.macho | 26.4.1 / 25E253 | 120373248 | 上述 IM4P 解包结果 |
| recovery-25E253.raw | Recovery 26.4.1 / 25E253 | 1568704000 | 本次 Recovery 只读虚拟磁盘完整读取；本次 guest RAM disk |
| kernelcache-25G83.im4p | restore-staged 25G83 | 32061360 | 原 macOS Preboot 的 restore-staged/kernelcache.release.mac16g；仅作比较 |
| kernelcache-25G83.macho | restore-staged 25G83 | 120504320 | 上述 IM4P 解包结果；未用于本次 guest |

机器为 Mac16,12 / J713 / T8132。新 stub 卷组 DE77783E-D9C0-4695-8BE1-EBE0D3015748，原 macOS 卷组 B8663CA8-7F9F-4EF7-8947-75F71A14BDA9。25G83 标签来自原裸 SystemVersion/restore-staged，不证明当前启动的 sealed snapshot 也是该版本。

Recovery raw 来源是当次虚拟 /dev/rdisk5，而非物理 SSD。磁盘编号随启动变化，不可在以后直接照抄该编号；重新采集必须先核对镜像与 UUID。

## 离线校验与重新解包

在 M1 项目根目录执行；这些命令不连接 M4、不写目标磁盘：

```sh
cd /home/sequencer/project/m4-linux
nix develop --command sha256sum -c experiments/2026-09-13-sptm-macos/SHA256SUMS
```

使用锁定的 flake.lock 提供 LZFSE/Python 依赖。解包脚本通过 result 中的固定 PR proxyclient 检查 Mach-O 符号；如果 result 不存在，先构建：

```sh
nix build .#m1n1-sptm --out-link result
nix develop --command bash -eu -c '
  output=$(mktemp -d)
  trap '\''rm -rf "$output"'\'' EXIT
  raw=experiments/2026-09-13-sptm-macos/raw
  python3 scripts/extract-kernelcache.py "$raw/kernelcache.release.mac16g.im4p" "$output/kernelcache-25E253.macho"
  cmp "$raw/kernelcache-25E253.macho" "$output/kernelcache-25E253.macho"
  python3 scripts/extract-kernelcache.py "$raw/kernelcache-25G83.im4p" "$output/kernelcache-25G83.macho"
  cmp "$raw/kernelcache-25G83.macho" "$output/kernelcache-25G83.macho"
'
```

两个 cmp 成功意味着重新解包输出与保存的 Mach-O 逐字节相同。脚本还检查 _cons_ops、_PAGE_SHIFT_CONST、__TEXT。Recovery raw 是采集输入，不是从源码构建的产物；目前未验证由原 UDIF 镜像重新生成它的字节一致性。

## m1n1 构建身份

固定 PR head：7e43bb1763ff97d661bbddb213596eda9475ae6a。当前 flake.nix 另含 optional-ANS/SART 本地补丁：

- 已安装的原始持久化 m1n1 SHA-256：d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0。
- 当前补丁构建 SHA-256：779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4。

```sh
nix build .#m1n1-sptm --out-link results/m1n1-optional-ans
printf '%s  %s\n' 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4 results/m1n1-optional-ans/share/m1n1-sptm/m1n1.bin | sha256sum -c -
```

此构建不安装、不持久化、不启动 guest。实验启动过程及失败现场见 SPTM_MACOS_EXPERIMENT.md。Nix 重用同一构建产物不等于已独立验证无缓存重构建。

## Git 和备份边界

SHA256SUMS、解包脚本、flake.nix/flake.lock 与本文可纳入 Git；raw/ 和 result/results 当前被忽略。因此“保存到项目”不等于“已提交到 Git”，也不等于“已异机备份”。新 clone 单独不能复现，必须另外取得三个原始输入或整份 raw/，放回上述路径并通过哈希校验。未上传这些资产到公共仓库。

内核是 Apple 二进制输入；本项目目前能复现解包和 m1n1 构建配置，不能从公开源码重建字节相同的 Apple kernelcache，也不能保证 guest 已启动成功。
