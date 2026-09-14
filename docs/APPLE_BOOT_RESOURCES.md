# Apple 官方 M4 启动资源：26.6.2 / 25G83

## 来源和版本选择

本台目标为 M4 MacBook Air `Mac16,12`，BuildManifest 身份为 `j713ap`，
`ApChipID=0x8132`、`ApBoardID=0x2C`。选择 26.6.2/25G83，是为了准备与原系统版本一致、
并满足 IRC 提到的 26.6 系列固件寄存器解锁前提的资源；下载本身不证明本台机器已经解锁。

- [Apple 官方 macOS IPSW 目录](https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml)。
- [Apple 官方 26.6.2/25G83 UniversalMac IPSW](https://updates.cdn-apple.com/2026SummerFCS/fullrestores/140-75212/A2A24B94-1FC1-45A3-93F7-C51B02AF1F4D/UniversalMac_26.6.2_25G83_Restore.ipsw)。
- 目录查询路径：`MobileDeviceSoftwareVersionsByVersion/1/MobileDeviceSoftwareVersions/Mac16,12/25G83/Restore`。
- IPSW 大小：`19772231540` 字节。
- Apple 目录给出的 SHA-1：`4833c12d9d8d330d47216edbcaaf8cb4b926c99a`。
- Apple CDN `x-amz-meta-digest-sha256`：`885503b7f4b06609e9a512f2befd40f59730640a3f1233e3892d60affdd51c95`。
- 2026-09-13 目录快照 SHA-256：`4259552631d29cbc6d3345e667af0d334cf31fe73b946c5babdda1e0244084da`。
- CDN 的 multipart ETag 不是文件 SHA-256，不能当作整包校验值。

IPSW URL 和哈希已经固定在 `flake.nix`。Apple 目录是可变端点：未来目录更新时，
历史快照的固定哈希会拒绝新内容，不应静默更换哈希。保留当前目录快照与 Nix GC root。

## 下载和提取

在 M1 项目根目录执行：

```sh
cd /home/sequencer/project/m4-linux
bash scripts/download-apple-boot-resources.sh
```

脚本只操作 M1 的项目目录和 Nix store，不访问 M4，不修改分区、SIP、LocalPolicy 或启动对象。
`aria2` 从锁定的 Nixpkgs 提供，16 路 HTTPS 分段下载支持断点续传，并校验固定 SHA-256；
完成后通过 `nix store add --mode flat` 导入，再由固定输出的 Nix derivation 验收并建立 GC root。
提取器再次校验整包 SHA-256、版本、芯片和板号，使用 ZIP CRC 验证读取内容，并生成逐文件 SHA-256。
脚本随后获取固定哈希的 Apple FCS key，解包内核、SPTM、TXM 和 DeviceTree，并在 M1 上使用纯 Go AEA 实现解密 BaseSystem。
这些转换产物最后对照版本化的 `DERIVED_SHA256SUMS` 校验，已有产物不会静默重写。
已有提取目录不会覆盖；脚本会校验其中的 `SHA256SUMS`，提取失败留下的目录应先移走，不能当作完整结果。

也可直接走单连接 Nix 下载：

```sh
nix build .#apple-m4-restore-25G83 \
  --out-link artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw -L
nix develop --command python scripts/extract-apple-boot-resources.py \
  artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw
```

提取器合并 J713 的三个身份：`Customer Erase Install (IPSW)`、
`Customer Upgrade Install (IPSW)`、`macOS Customer`。这只是读取清单，不执行 erase 或 restore。
包含这些身份中除 OS 主镜像、Cryptex 和系统 canonical metadata 以外的路径，
以及 Bootability、版本清单、bootcaches 和该机型通用 ticket（如果归档提供）。
完整 IPSW 保留被排除的大镜像，需要时可再次提取。

## 关键输入路径

以下路径相对于 `artifacts/apple/25G83/j713/`：

| 输入 | 官方归档路径 |
|---|---|
| 内核 IM4P | `kernelcache.release.mac16g` |
| SPTM | `Firmware/sptm.t8132.release.im4p` |
| TXM | `Firmware/txm.macosx.release.im4p` |
| DeviceTree | `Firmware/all_flash/DeviceTree.j713ap.im4p` |
| iBoot | `Firmware/all_flash/iBoot.j713.RELEASE.im4p` |
| LLB | `Firmware/all_flash/LLB.j713.RELEASE.im4p` |
| Recovery BaseSystem | `022-22048-093.dmg.aea` |
| Recovery trust cache | `Firmware/022-22048-093.dmg.aea.trustcache` |
| Erase restore ramdisk | `094-96989-093.dmg` |
| Upgrade restore ramdisk | `094-97199-093.dmg` |

`inventory.json` 记录全部路径、大小、角色和哈希；`SHA256SUMS` 可逐项校验。
BaseSystem 是 AEA 加密容器，不是直接可交给现有 guest launcher 的 raw 根盘。
RestoreRamDisk 是恢复安装环境，不等同于 BaseSystem，也不是普通 macOS 桌面系统。
IM4P 固件与其解包后的裸 payload 不同，转换产物必须另记哈希。

## 后续实验边界

1. 保留旧 25E253 stub 和实验输入，不能用同名文件覆盖。
2. 若解密 BaseSystem，记录 AEA metadata 中的 Apple FCS key URL 和原始响应；只使用 Apple 官方响应，不从第三方密钥表取键。
3. 解密后仍须检查 UDIF/GPT/APFS 几何，构造对齐、guest physmap 可见且有保留边界的 RAM root。
4. SPTM HLE 的 PR #1 不会因为下载了 Apple SPTM/TXM 就自动加载真实 monitor；真实 monitor 路径仍需 loader 集成。
5. 新 KC 和新固件文件尚未更新实际执行的 boot firmware。下一步若要改变持久化固件/启动对象，需单独列出操作和恢复路径，再执行并验收 timer 寄存器读写。

具体阻塞和实验分阶段验收见 `docs/SPTM_MACOS_RESEARCH.md`。
`artifacts/` 被 Git 忽略；Nix 固定 URL/哈希可重建整包，但不能把本地下载称作已经提交或异机备份。

## 下载工具 pitfall

本次 CDN HEAD 未返回 `Accept-Ranges`，但实际带 Range 的 GET 返回了严格匹配的 HTTP 206 / Content-Range。
`ipsw 3.1.673 extract --remote` 因响应头判定不支持 byte ranges 而失败；这是客户端探测限制，
不证明 Apple 不支持分段下载。改用 aria2 下载完整包，再离线提取，不跳过哈希或 TLS 校验。
Nix 的 aria2 为多输出包，二进制使用 `.#apple-download-tools^bin`，不能假定默认输出有 `bin/aria2c`。
`nix build --out-link` 不会覆盖同名普通文件；手工下载的 FCS key 先保留为 `.download`，再将已验收的 Nix 输出链接到脚本所需路径。

## 本次完成与验收

2026-09-13，完整 IPSW 已下载并通过 aria2 SHA-256、Nix 固定输出导入及提取器整包 SHA-256 验收。
58 个 J713 资源共 `1687797483` 字节，全部 ZIP CRC 读取成功，生成后逐文件 `sha256sum -c` 全部通过。
来源响应头、完整 inventory 和 SHA256SUMS 另存于 `experiments/2026-09-13-apple-25G83/`，未被 raw/artifacts 忽略规则排除。

另存的裸 payload 位于 `artifacts/apple/25G83/derived/`：

| 转换产物 | SHA-256 |
|---|---|
| `kernelcache-25G83.macho` | `f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d` |
| `sptm.t8132.bin` | `4319631d0479b7f16fa3f96710b16811d4f51523ce88506122f32986a303bb38` |
| `txm.macosx.bin` | `df750ed7e0cb8f9ceff6e0d78a58b0442668367cdd896d39334b60fa09e67cef` |
| `DeviceTree.j713ap.bin` | `777f10e87056fd658fbff7d3f70541d86d8ce913995950e8113ff0a0e4aa2472` |
| `fcs-key-response.bin` | `6bd1353862950a98a06fdc4a19b94ce596ad71800786a0bee32e543a2b843122` |
| `022-22048-093.dmg` | `eeda386b1fb66a313cadef26e3e7ee06643d4d5ea8b3330a411a118ac7d14ed3` |

内核使用 `scripts/extract-kernelcache.py` 解包，并通过 `_cons_ops`、`_PAGE_SHIFT_CONST` 和 `__TEXT` 符号检查；
解包结果与此前从目标原系统保存的 25G83 Mach-O `cmp` 字节一致。
其余 payload 使用锁定 Nix `ipsw img4 im4p extract ... --output ...` 转换。
转换产物校验记录为 `experiments/2026-09-13-apple-25G83/DERIVED_SHA256SUMS`。

AEA metadata 指定的官方 FCS key URL 为
`https://wkms-public.apple.com/fcs-keys/iH707G4WnpWgYOxDeMRHQUtlbIsfVaeIA86lDBYsT2U=`。
首次下载该响应遇到本机 DNS 解析失败，改用 curl `--doh-url https://dns.google/dns-query` 成功；
DoH 只改变域名解析，内容仍从 Apple HTTPS URL 获取，并保持 TLS 证书校验。
原始 PEM 响应另以固定 URL/SHA-256 的 Nix fetchurl 保存，脚本不使用第三方密钥表。
BaseSystem 已用 `ipsw fw aea --pem ...` 的纯 Go 实现解密，输出 `1562348679` 字节的 UDIF DMG，
尾部 `koly` 验证通过。UDIF 尚未转换成对齐的 guest RAM root，不能直接喂给现有 raw RAMDisk launcher。
本次未访问 M4、未更新实际 boot firmware，也未重跑 guest。
