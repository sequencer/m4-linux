# M4 的独立 macOS 与 m1n1 调试环境

## 当前方案：最小 stub，不安装第二套完整 macOS

用户已明确撤回临时完整 macOS 安装路线。2026-09-13 已实际创建最小实验 stub，并将独立容器缩到约 4GB。16:23 UTC 已完成配对 Recovery 安装并实际重启进入独立 m1n1 EL2，UART 和 proxy NOP 均成功；Linux 未启动。下文“必须在 M4 屏幕上完成”的完整 macOS 安装步骤仅保留为历史方案，不再执行。最新验收见 docs/MINIMAL_STUB.md。

## 2026-09-13 用户确定的目标

- M1 Asahi 主机是控制机，所有工具依赖由 Nix 管理。
- M4 Air 是目标机：Mac16,12 / J713 / T8132，32GB RAM，2TB SSD。
- macOS APFS 容器目标大小由用户改为 256GB（256000000000 字节）；其余可用空间留给独立 m1n1/Linux 环境。
- 用户在 M4 本机进入恢复环境、下载临时 SSH host key 和控制机公钥、手动启动 sshd。
- 控制机随后通过 SSH 检查和配置目标机。

## 已实测的启动链

在配对的 1TR 恢复环境中，先通过 bputil 将目标卷组切换到 Reduced Security，再执行：

```sh
kmutil configure-boot -c /tmp/m1n1-sptm.bin --raw --entry-point 2048 --lowest-virtual-address 0 -v "/Volumes/Macintosh HD"
```

安装返回 done，策略出现 coih，Security Mode 为 Permissive。重启后 M4 在 EL2 运行 m1n1，M1 枚举出 USB 1209:316d 和两个 ttyACM 设备。UART NOP 和 proxy NOP 握手成功。

当前自定义对象安装在现有 Macintosh HD 上，还没有独立实验启动卷。这不能作为最终布局；需要恢复 macOS 的启动路径，将 m1n1 放入独立、可认证的启动卷组。

固定构建为 PR #1 提交 7e43bb1763ff97d661bbddb213596eda9475ae6a，二进制 SHA-256：

```text
d617ceeea5b34d7b1a44c64751574e937fdda3dcc1f1368b05f69965f0dd62b0
```

## 恢复 SSH

控制机 HTTP 服务绑定 172.25.27.108:8000，目录是 /home/sequencer/.cache/m4-recovery-http。此目录仅放临时服务器 host key 和当前 M1 的公开登录密钥，不能放控制机私钥。

目标端文件位于 /tmp/m4-ssh。此前公钥被拒绝的原因是 /tmp 的父目录权限；临时 sshd 使用 StrictModes=no。认证使用当前控制机 /home/sequencer/.ssh/id_ed25519，不能误用另行生成的 m4-recovery 私钥。

## 进行顺序及验收

### 现场更新

恢复 SSH 已重新登录成功。遗漏 UsePAM=no 时，客户端日志显示服务器接受公钥，但签名认证之后连接关闭；加入该参数后恢复正常。

用户明确要求清空整个废纸篓，已执行。废纸篓中包含此前误建并移入废纸篓的 42GiB liqi_backup；APFS clone 共享块使实际容器占用仅减少约 17.6GB。之后磁盘占用约 124.3GB，resize limits 给出最小 134.5GB、推荐 145.2GB。用户据此将目标改为 256GB。

已成功执行 diskutil apfs resizeContainer disk3 256000000000，APFS 检查退出码为 0，最终返回 Finished APFS operation。复核 disk0s2 / disk3 容量为精确的 256000000000 字节，中间产生约 1.739TB 空闲空间；disk0s1 的 ISC 和 disk0s3 的系统 Recovery 保留。原 Macintosh HD / Data 卷组 UUID 未变化。剩余空间尚未建立实验 APFS、EFI 或 Linux 分区。

独立启动 stub 的下一阶段还需实现：检查 AsahiLinux/asahi-installer 当前 main 的 CHIP_MIN_VER 和 DEVICES 后，确认其未包含 T8132 / j713ap，不能直接使用上游安装器或仅打开 EXPERT 来完成 M4 安装。

1. 建立恢复 SSH，核对 bputil 的配对状态、当前磁盘布局、FileVault 状态和恢复系统地址。
2. 读取 resizeContainer limits，根据用户最新选择缩到 256GB；128GB 方案已撤回。不为达到目标大小擅自删除未备份数据。
3. 保留磁盘首端 Apple_APFS_ISC 和末端 Apple_APFS_Recovery；仅调整中间的 macOS 容器及可用空间。
4. 核实适用于 J713 和当前 firmware 的启动 stub 创建流程。独立 m1n1 启动环境需要 APFS OS 卷组、Preboot、恢复环境和本机所有者认证，单建 FAT/ext4 分区不够。普通 Asahi 安装布局只能作为参考，不能假定支持 M4。
5. 在独立卷组安装同一固定 m1n1 构建；启动选择器应能分别进入正常 macOS 和 m1n1。
6. 从 M1 自动发现 USB serial，执行 NOP 握手、chainload RAM 中的实验构建、保存启动日志和实验版本；验证重启后可以重复连接。
7. Linux root 空间留给后续 bring-up。目前只验证了 m1n1 proxy；尚未验证 SPTM emulator guest、Linux 内核或用户空间，不能将分配分区称为完成 Linux 安装。

## 独立安装准备的执行结果

2026-09-13 继续执行安装准备，Recovery SSH 仍可用。

```sh
diskutil addPartition disk0s2 APFS "M4 Linux Bootstrap" 64000000000
bputil -f -v B8663CA8-7F9F-4EF7-8947-75F71A14BDA9
```

两个操作均返回成功。新增分区为 disk0s5，容器 disk6，容器 UUID 为 909274B1-CCC4-47DC-8314-9F00F7AF4885；空卷 disk6s1 的 UUID 为 DE77783E-D9C0-4695-8BE1-EBE0D3015748，名称 M4 Linux Bootstrap。diskutil info 显示 OS Can Be Installed: Yes。剩余未分配空间约 1.675TB；ISC 和末端系统 Recovery 未改变。

64GB 是暂时为独立 macOS 安装及配对 Recovery 留出的启动容器，不是 Linux 根分区。后续转换为 m1n1 实验环境；能否再缩小须根据实际占用重新检查 limits，不能预先保证变为上游旧版 2.5GB stub。

原 Macintosh HD 的策略现在是 Full Security、Pairing Integrity: Valid、coih: absent。原有自定义 m1n1 启动对象不再被策略选用；尚未重启验证正常 macOS。m1n1 二进制仍保存在 M1 的 Nix 构建产物中，独立卷尚未安装它。

Recovery 内未发现 startosinstall 或完整 InstallAssistant。/usr/libexec/installer-core 的用法是工具名加软件包路径，不能把它当成完整 macOS 安装器。采用 Apple 支持的第二卷安装流程，而不是复制旧卷的 LocalPolicy 或强行运行不支持 M4 的 Asahi 安装器。

### 必须在 M4 屏幕上完成的下一步

1. 保持接电和网络连接；不要关闭正在运行的 SSH Terminal 窗口，也不要先重启。
2. 切回恢复环境的主窗口，选择“重新安装 macOS”，点击继续并接受许可。
3. 到安装目标选择页时显示所有磁盘，**只选择 M4 Linux Bootstrap**。不要选择 Macintosh HD，不要抹掉磁盘、Data、ISC 或系统 Recovery。
4. 若安装器未显示新卷或拒绝容量，停在该页面并记录准确错误；不要自行擦除原卷。
5. 确认目标名称后开始安装。此阶段安装器可自动重启；当前 Recovery SSH 会随重启断开，这是预期行为。
6. 新系统首次启动时创建本地管理员 liqi，不迁移原系统用户数据，不需要登录 Apple ID。完成设置后开启“系统设置 → 通用 → 共享 → 远程登录”，允许 liqi 登录。
7. M1 再核对新卷组 UUID 和本机所有者信息。随后选择该新系统作为默认启动盘、关机并长按电源进入它的配对 Recovery；重新启动临时 SSH 后，才对新卷执行 bputil -g 和 kmutil configure-boot。

Apple 官方第二卷安装说明：https://support.apple.com/en-gb/118282

配对 Recovery 限制：https://support.apple.com/en-mide/guide/security/sec4cf9d63a6/web

### 新卷的配对 Recovery 再开 SSH

Recovery 的 /tmp 内容会在重启后消失。M1 HTTP 服务仍在线且地址未变化时，在新卷的配对 Recovery Terminal 执行：

```sh
mkdir -p /tmp/m4-ssh
curl -f http://172.25.27.108:8000/ssh_host_ed25519_key -o /tmp/m4-ssh/host_key
curl -f http://172.25.27.108:8000/authorized_keys -o /tmp/m4-ssh/authorized_keys
chmod 600 /tmp/m4-ssh/host_key /tmp/m4-ssh/authorized_keys
/usr/sbin/sshd -D -e -f /dev/null \
  -h /tmp/m4-ssh/host_key -p 22 \
  -o UsePAM=no \
  -o PermitRootLogin=prohibit-password \
  -o PubkeyAuthentication=yes \
  -o PasswordAuthentication=no \
  -o KbdInteractiveAuthentication=no \
  -o AuthorizedKeysFile=/tmp/m4-ssh/authorized_keys \
  -o StrictModes=no \
  -o PidFile=/tmp/m4-ssh/sshd.pid
```

最后一条命令在前台持续运行；不要关闭它的 Terminal 窗口。临时 host key 通过局域网明文下载，仅用于此次 Recovery，不作为长期 SSH 身份。HTTP 服务只绑定控制机局域网地址；调试结束后停止服务并清理临时 host key。

### M1 自动检查原生 m1n1 proxy

安装独立 m1n1 并启动后执行：

```sh
cd /home/sequencer/project/m4-linux
nix build .#m1n1-sptm
nix develop --command bash -c 'sudo -n env PYTHONPATH="$PYTHONPATH" "$(command -v python3)" scripts/m1n1-check.py --output experiments/native-proxy-check.json'
```

脚本只发送 UART 和 proxy NOP，不调用 setup、chainload 或写入磁盘。它检查 1209:316d 原生 USB 设备；现在目标仍处于 Recovery，不能宣称此次已经再次验证了 proxy 或 Linux 启动。

## 备份覆盖范围

实际备份在 M1 的 /home/sequencer/liqi_backup，总占用约 47GiB。Desktop 和 Downloads 传输完成；Library 传输返回 code 23，存在受保护文件和同步期间消失的索引文件，且排除了 CloudStorage 和 Application Support/FileProvider。Pictures 按用户要求未备份。这个副本不是完整 macOS 系统恢复镜像。

## 用户要求关闭 SIP 后的最新策略

2026-09-13 用户明确要求不要保留安全限制、直接关闭 SIP。通过当前配对 Recovery SSH 执行 csrutil disable，确认目标为 Macintosh HD，回答 y 并完成所有者认证，退出码 0。

复核结果：csrutil status 为 disabled；bputil 显示 Permissive、sip0: 7f、Kernel CTRR Disabled、Boot Args Filtering Disabled、coih absent。此更新取代此前 Full Security 的状态记录；没有重新安装 m1n1，也没有重启，工具要求重启后对正常系统生效。

Authenticated Root / SSV 仍为 enabled，Data 的 FileVault 为 Yes。SIP 关闭不能表述成所有硬件和启动安全机制都已关闭；没有为关闭 SSV 而擅自启动 FileVault 解密。新 M4 Linux Bootstrap 仍为空卷，之后需要单独认证并配置其安全策略，旧卷 SIP 设置不能假定自动继承。
