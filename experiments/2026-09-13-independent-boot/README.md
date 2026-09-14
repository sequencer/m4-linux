# 独立启动环境安装准备

目标：M4 Air J713/T8132，Recovery SSH root@172.25.27.133。

执行成功：

```sh
diskutil addPartition disk0s2 APFS "M4 Linux Bootstrap" 64000000000
bputil -f -v B8663CA8-7F9F-4EF7-8947-75F71A14BDA9
```

结果：原 APFS 容器仍为 256GB；新增 disk0s5/disk6 为 64GB；空卷 disk6s1 可作为 macOS 安装目标；原卷组 Full Security、coih absent、配对有效。ISC 与系统 Recovery 保留。原始复核输出在 raw/recovery-after-preparation.txt，本地保留而不纳入版本控制。

尚未完成：第二套 macOS/配对 Recovery 的安装、独立卷的 m1n1 配置、原 macOS 重启验收、Linux 启动。

自动检查脚本通过 Python 编译与 --help 检查；目标仍在 Recovery，无原生 m1n1 串口，因此无设备检查按预期拒绝执行，不能算作实机 NOP 验证。固定构建 SHA-256 仍为 d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0。
