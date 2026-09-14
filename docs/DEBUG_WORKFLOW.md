# 纯 Nix 自动化调试流程

## 原则

每个实验都必须由以下内容组成：

```text
固定 flake.lock
  + m1n1/Linux commit
  + 固件版本
  + DT/ADT 输入
  + 启动命令
  + 原始 serial/DebugUSB log
  + 结构化结果
```

不要只保存“能启动”的截图或口头结论。

## 初始化环境

```sh
cd ~/project/m4-linux
nix develop
nix flake lock
```

在 M1 Asahi 上执行以上命令；不要在 M4 目标机上安装第二套 Python、编译器或调试依赖。构建产物和实验记录均从 M1 生成。

第一次锁定后提交 `flake.lock`。之后禁止在实验中隐式使用系统 Python、系统 `jq` 或未记录版本的交叉工具。

## M1 控制机连接 M4

在 Asahi M1 控制机上，优先使用 Linux DebugUSB/kisd 路径：

```text
M4 Air (DebugUSB) -- USB-C cable --> Asahi M1 (kisd) --> /dev/m1n1 or PTY
```

`tuxvdmtool` 负责在 Apple Silicon 控制机上切换目标机的 DebugUSB 状态，`kisd` 负责暴露 dockchannel UART，m1n1 proxyclient 再使用该设备。第一次连接只做识别和读取，不直接写入目标机启动区域。

M4 的实际连接顺序必须是：先启动 `kisd`，再由 `tuxvdmtool` 发送 `reboot debugusb`。M4 `t8132` 使用 DebugUSB base `0x3c8000000`；成功后通常出现 `/dev/m1n1`，它是指向 kisd PTY 的符号链接，不一定出现 `/dev/ttyACM*`。

```sh
lsusb
ls -l /dev/m1n1 /dev/ttyACM* 2>/dev/null || true
nix develop
```

推荐的可复现命令：

```sh
cd ~/project/m4-linux
sudo nix develop --command kisd --base 0x3c8000000
```

保持上一个命令运行，在第二个终端执行：

```sh
cd ~/project/m4-linux
sudo nix develop --command \
  tuxvdmtool --connector 'Left-back' reboot debugusb
ls -l /dev/m1n1
```

当前硬件实测环境是原版 M4 MacBook Air、macOS 26.4.1、M1 Asahi 控制机；该 macOS 版本已成功进入 DebugUSB。M4 MacBook Air 应使用靠后的 DFU USB-C 口，M1 端使用 `USB-C Left-back` 控制器。

## 已记录的陷阱

- **Nix PATH 陷阱**：`sudo nix develop --command bash -lc '...'` 中的 login shell 可能重置 `PATH`，导致 `kisd`、`tuxvdmtool` 和 `lsusb` 报 `command not found`。优先直接使用 `sudo nix develop --command <tool>`；需要组合命令时使用 `bash -c`，或先解析 Nix store 中工具的绝对路径。
- **启动顺序**：只执行 `tuxvdmtool reboot debugusb` 而没有同时运行 `kisd`，不能验证 dockchannel 是否被接管。必须先启动 `kisd`，再切换目标模式。
- **设备判断**：普通 `05ac:1905`/`cdc_ncm` 只表示 M4 的常规 USB 网络接口，不等于 DebugUSB；`/dev/m1n1` 才是当前 Linux 侧的成功判据。
- **通道≠m1n1**：`/dev/m1n1` 是 kisd 暴露的 DebugUSB dockchannel PTY；它可打开但没有输出时，只能证明 DebugUSB 通道成立，不能证明目标已经加载或运行 m1n1。真正进入 m1n1 还需要固定 commit 的 m1n1 payload、proxyclient 和明确的 tethered/chainload 步骤。
- **DebugUSB 不是 loader**：ADevWithAnIdea/m1n1 PR #1 的 `proxyclient/tools/chainload.py` 先通过 `m1n1.setup` 与已有 m1n1 proxy 握手，再把新 payload 写入目标 RAM；它不能把原版 macOS 目标直接变成 m1n1。PR README 的 `kmutil configure-boot` 路径会修改 M4 的 Preboot/启动配置，必须单独确认后才允许执行。
- **PR Rust 构建**：当前 Nix devShell 的 `cargo/rustc` 已加入，但 Nix 提供的 `rustc-src` 缺少 `library/Cargo.lock`，因此 `make BUILDSTD=1` 仍不能构建 `aarch64-unknown-none-softfloat`。禁止退回到未记录的系统 `rustup`；应补充锁定的 Nix Rust target/source 依赖。
- **串口误判**：M1 自带的 `/dev/ttySAC0`、`/dev/ttySAC2` 不是 M4 DebugUSB 设备，不能代替 `/dev/m1n1`。
- **安全边界**：`reboot debugusb` 只切换 USB 调试模式，不刷写、不擦除磁盘；但会重启 M4，未保存的 macOS 工作可能丢失。不要把 `dfu` 后的恢复/刷写操作混入连接测试。
- **日志保留**：每次连接测试要同时保存 `tuxvdmtool` 输出、`kisd` 输出、`lsusb`、`readlink -f /dev/m1n1` 和目标 macOS/firmware 版本。

如果使用 udev 规则，规则和设备权限也必须纳入控制机配置；不要让 AI Agent 依赖临时的 root shell 或用户本地 Python 环境。

## 重要限制

M1 控制机可以编译、传输、采集和自动重试，但不能替代 M4 上的原生 SPTM。原生 macOS/SPTM 运行状态仍然发生在 M4 目标机上；控制机只能通过 DebugUSB/UART、屏幕输出和实验结果进行观测。

## 创建实验目录

```sh
nix run .#experiment-recorder -- sptm-probe "first target boot and SPTM observation"
```

命令会生成：

```text
experiments/<timestamp>-sptm-probe/
  REPORT.md
  metadata.json
  raw/
  build/
```

`raw/` 保存不可变原始日志，`build/` 保存该轮构建产物和 hashes；报告只记录解释和结论。

## 自动化阶段

### Phase 0：只读识别

- 读取目标机型号、SoC、ADT 和 firmware 版本。
- 验证 DebugUSB/UART 连接。
- 不修改启动对象、不写 Preboot。
- 保存完整 handshake 和设备识别数据。

### Phase 1：m1n1 可恢复实验

- 构建固定 commit 的 m1n1。
- 只使用 tethered/chainload 路径。
- 自动保存 proxy 输出、异常寄存器和复位前日志。
- 记录 UART、DebugUSB 和 framebuffer 三种输出是否存在。

### Phase 2：SPTM handoff

- 单独验证 BootKC/XNU shim，不同时引入 Linux MM 改动。
- 记录每一次 `genter/gexit`、endpoint、domain、frame retype 和异常。
- 每个 firmware 版本建立独立实验目录。

### Phase 3：Linux early boot

- 先只启动 UART 和单核。
- 然后启用页表、timer、AIC、SMP、DART 和 NVMe。
- 每次只启用一个新子系统。
- 进入 userspace 前不引入 GPU、DCP 或 Exclave 变量。

## 失败分类

所有失败使用以下标签之一：

- `BOOTKC_REJECTED`
- `SPTM_HANDOFF`
- `GXF_OR_SYSREG`
- `PAGE_TABLE`
- `CACHE_OR_TLB`
- `SECONDARY_CPU`
- `DART_OR_DMA`
- `NVME`
- `USB_OR_DEBUGUSB`
- `DCP_OR_DISPLAY`
- `AGX`
- `POWER_OR_THERMAL`
- `UNKNOWN`

## 第一轮实验目标

第一轮不追求完整 Linux。目标是获得一份可靠的硬件基线：

1. 目标机精确识别；
2. DebugUSB/UART 可复现连接；
3. m1n1 最小 payload 可启动或明确失败点；
4. 保留 macOS/1TR 恢复能力；
5. 所有输出和版本信息进入实验目录。
