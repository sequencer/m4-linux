# 2026-09-14 Linux-only stub 准备

用户确认此次 Restore 后没有配置 macOS、没有创建账号。不能把缺少所有者凭据断言为删除容器造成，也不能把 Apple ID 登录和本地管理员/卷所有者混为一谈。

在 root@172.24.5.124 的 25G83 RAM Recovery 中实际完成：

- 4 GB APFS stub，容器 AC02838C-5B6E-4B30-8BE1-C73937F42460，卷组 0F4B67C2-B48A-4F7F-B324-B02EB3362E5A；System/Data/Preboot/Recovery 四卷。
- 999997440 字节 EFI 分区，UUID B4B16301-9191-4810-96A1-12DD3EC04F3A，未格式化。
- 1990083952640 字节 Linux Filesystem 分区，UUID EC26EDE8-57A3-4AF7-B303-B198E5DC98EA，未格式化。
- diskutil 添加 Linux GPT 类型时额外生成约 134.2 MB Apple_Boot 分区；不是 Linux 安装完成的标志，没有删除它。
- 原 iSC 和 System Recovery 保留，未更改默认启动项，未重启。

首次布局使用 scripts/prepare-linux-only-layout.sh --apply。EFI 后剩余空间通过核对 EFI UUID 后执行 `diskutil addPartition disk0s5 %0FC63DAF-8483-4772-8E79-3D69D8477DE4% %noformat% 0` 分配。设备编号仅为当时现场，不可在重启后照抄。

将 Nix 固定资源生成的 artifacts/apple/25G83/stub-update.tar 传到新 Data/staging；源归档 SHA-256 为 a85e25ed69c8445dbf854f1fc9833d5af1cdae756b1e8f305db0c4b3f8f2f580。scripts/stage-linux-only-stub.py 按 SHA256SUMS 在 M4 校验全部资源，再放入新卷组。没有执行旧 apply-stub-firmware.py 或复用其旧目标 UUID。旧归档 update-plan.json 仅作历史材料，不代表新安装策略。

System 上的 `/Volumes/M4 Linux Bootstrap/m1n1/boot.bin` SHA-256 为 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4。25G83 restore 和匹配 Recovery 镜像已放置，APFS bootable flag 已设置；这些都不等于 LocalPolicy 个性化或 kmutil 安装成功。

## 当前明确阻碍

实际执行 `bputil -g -v 0F4B67C2-B48A-4F7F-B324-B02EB3362E5A </dev/null` 返回退出码 8：

```text
bputil: no admin users authorized for recovery
Failed to create ACM context with provided username and password
```

没有提示可以免凭据创建新策略。此前新卷 `bputil -d` 也明确无 LocalPolicy。不能声称 SIP 已关闭、Permissive 已生效或 m1n1 已可启动。没有执行反复策略重建、复制旧抹盘前的管理员信息或重启。

下一步必须建立有效的本地所有者认证来源，或找到并验证 Apple 未初始化设备的等价授权流程。仅有 Recovery root SSH 不满足此条件。若没有可验证的无完整 macOS 路径，临时创建本地管理员再迁移到 stub 是待评估替代方案，不得自动声称必须再次全盘 Restore。

## Recovery Python pitfall

从 Nix 固定 asahi-installer v0.9.1 提取 Frameworks 后，必须同时设置 DYLD_FRAMEWORK_PATH 为解包目录/Frameworks，以及 DYLD_LIBRARY_PATH 为 Frameworks/Python.framework/Versions/Current/lib。只设前者可以打印 Python 版本，但 ctypes 因找不到 libffi.dylib 失败。两者设置后脚本实机退出 0。未修改 Recovery 系统库。
