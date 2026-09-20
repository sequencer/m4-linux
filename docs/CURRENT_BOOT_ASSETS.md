# 当前启动资源：25G83 / 本轮 DFU 实例

> 最新更正：按用户要求已撤回新增 guest 启动封锁和读取守卫；下文有关“入口直接退出”的描述是历史，不再生效。资源版本与校验保持不变。manifest 中 guest_execution_allowed=false 是生成时未验收的记录，不再对应启动器强制开关；不要据此声称 guest 已验证安全。

本页覆盖旧文档中的“当前输入”说法；旧 experiments/raw 和旧 UUID 只作历史取证，禁止作为本轮 live guest 输入。当前实机为 Mac16,12 / j713ap / T8132，26.6.2 / 25G83，实际启动固件 mBoot-18000.161.10。这里的“当前”指本台已验收版本，不是 Apple 最新发布版本。

## 唯一当前资源目录

`artifacts/current-25G83-post-restore-20260914/` 由 `scripts/prepare-current-assets.py` 创建。目录存在时脚本拒绝覆盖，避免失败或重跑悄悄替换既有输入。

```sh
nix build .#m1n1-sptm --out-link result
nix develop --command python3 scripts/prepare-current-assets.py
```

脚本对固定 IPSW、J713 官方资源和解包产物按 Git 内已有 SHA256SUMS 校验，核对 BuildManifest 的 25G83，再从官方 kernelcache 重新解包 Mach-O，并从官方 BaseSystem DMG 重新转换 GPT/APFS 根镜像；不从旧实验 raw 复制根盘。

- `official/`：固定 J713 资源集，含 kernelcache、BuildManifest、SPTM/TXM、DeviceTree、iBoot/SEP 等固件及输入设备固件、root hash/trustcache。具体范围以 manifest 文件列表为准。
- `derived/`：已校验的解包 SPTM、TXM、设备树、解密 BaseSystem 等。
- `kernelcache-25G83.macho`：重新解包的内核；SHA256 `f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d`。
- `recovery-25G83.apfs.raw` 及 `.json`：新转换的 Recovery 根盘及几何信息；预期 SHA256 `bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a`。
- `m1n1.bin`：应与实机 optional-ANS payload 的 `779c9ac3…` 一致。
- `restore.ipsw`：完整固定 Apple IPSW，SHA256 `885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95`。官方提取子集不包含完整 macOS 系统镜像和全部 Cryptex；它们仍在完整 IPSW 中，不把 Recovery 资源集称为完整 macOS 安装。

大文件用指向已校验源的 symlink 避免重复存储，源仍可能丢失或变化，因此每次离线使用前重新验证：

```sh
nix develop --command bash -c 'cd artifacts/current-25G83-post-restore-20260914 && sha256sum -c SHA256SUMS'
```

`manifest.json` 标明本轮卷组与固件身份，并明确 `guest_execution_allowed=false`、`current_isc_capture=null`、`personalized_state_included=false`。资源目录受 Git ignore 保护，不能声称二进制已提交或已异机备份。下载来源与 Nix 固定输入见 `scripts/download-apple-boot-resources.sh`、`flake.nix`。

## 不可通过更新版本解决的状态文件

旧 iSC、xART、LocalPolicy、个性化票据、AdminUserRecoveryInfo、旧 APFS UUID、旧 guest 地址和运行时报告全部是历史状态，不自动迁移。本轮 iSC 分区 UUID 为 2935ACB5-2A69-4996-942A-87B29BC17A2F；新 macOS 卷组 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8，stub 530FE39B-6AE3-47D0-9168-29F1A7EE2763。

本次 M4 在 m1n1 proxy，没有通过 guest 读取 SSD 或采集新的 iSC。需要新的设备状态时，应先进入原生 Recovery，用 UUID/ECID/当前策略核对后只读采集；即使采集成功，也不证明 live copy 原子一致，更不自动允许给 guest 使用。

旧 guest 启动器 `scripts/run-recovery-guest.py` 现在在 main 入口直接退出，连 prepare-only 也不允许，不提供绕过参数。这只是该项目入口的防误运行措施，不能阻止直接调用上游 HV 或其他脚本。重新开放须先解决持久状态隔离、内存读取守卫及原生/两种 Recovery 回归门槛，不能仅因哈希一致删除守卫。

之前失败使用的内核已经是 25G83；关键风险包括抹盘前 iSC 与实时设备状态混用、未隔离协处理器/持久路径以及不安全读取。统一文件版本不能保证不再 brick，关闭 SIP 也不是已证实的修复。
