# M4 MacBook Air 硬件基线

## 已知信息

- 目标：原版 M4 MacBook Air
- 内存：32 GB
- 内置存储：2 TB SSD
- 目标：纯 Nix、可自动化、可复现的 Linux bring-up 和调试

## 控制机决定

本项目使用一台运行 Asahi Linux 的 M1 作为控制机，M4 MacBook Air 作为目标机。

M1 控制机负责：

- 运行 AI Agent 和 Nix flake；
- 构建 m1n1、Linux、DTB 和实验工具；
- 通过 DebugUSB/UART 连接 M4；
- 保存原始日志、trace、firmware metadata 和实验报告；
- 执行可重复的 chainload、shell 和读取类实验。

这条路径是可行的：Asahi 的 `kisd` 支持在 Linux/Asahi 上接入 Apple DebugUSB 的 dockchannel UART，M4/T8132 也已有已验证的 DebugUSB base address。参考：[kisd README](https://github.com/AsahiLinux/kisd/blob/main/README.md)。

所有项目依赖必须进入 `flake.nix` 或项目自己的 Nix derivation。当前 flake 已覆盖交叉编译器、DTB/镜像工具、m1n1 proxyclient 的 Python 依赖、串口工具、USB 诊断工具，以及自定义打包的 `kisd` 和 `tuxvdmtool`；不依赖控制机的系统安装。

M1 控制机不能替代 M4 目标机上的 SPTM；它只能观测目标机通过 USB 暴露出来的接口，不能直接读取 SPTM 内部状态。

## 首次实验必须确认

以下信息不能凭产品名称推断，必须从目标机和启动日志采集：

- 精确 `producttype`、板号和 ADT board configuration
- SoC/codename，预期为 T8132，但必须实测确认
- 当前 macOS、iBoot、BootKC 和 firmware build
- Secure Boot / 1TR / recovery 状态
- DebugUSB 是否可用，以及控制机上的 USB device identity
- UART/debug channel 是否可用
- 内存起始地址、可用内存范围和 SPTM carveout
- NVMe controller/partition layout
- 当前是否保留可恢复的 macOS 和 1TR 入口

## 安全边界

调试初期不要覆盖原有 macOS、Recovery 或 Preboot。每轮实验必须能回到：

1. macOS 正常启动；
2. 1TR/recovery；
3. 已知可用的 m1n1/boot object；
4. 可复现的 firmware 版本。

## 控制机和目标机

纯 Nix 只负责工具链和实验编排，不假设 Apple 专用工具已经存在于 nixpkgs：

- **控制机**：运行 Nix flake、构建 m1n1/Linux、保存日志和生成实验元数据。
- **目标机**：M4 MacBook Air，负责实际 boot、DebugUSB/UART 和硬件验证。
- **恢复机**：建议保留另一台 Apple Silicon Mac 或可进入 DFU/1TR 的恢复路径；是否必需需通过首次 DebugUSB 实验确认。

当前实际分工为：Asahi M1 = 控制机，M4 Air = 目标机；恢复机仍需单独确认。

## AI Agent 权限分层

### 自动允许

- 构建和 hash 校验；
- 读取 `/dev/bus/usb`、`/dev/ttyACM*` 或 kisd 暴露的 PTY；
- 运行 m1n1 proxyclient 的读取、shell 和日志采集命令；
- 创建实验目录和保存原始数据。

### 默认需要显式确认

- 让 M4 重启或进入 DebugUSB/DFU；
- 写入 Preboot、BootKC、NVRAM 或启动策略；
- chainload 未验证的 m1n1；
- 修改目标机分区、固件或恢复状态。

这样 AI Agent 可以直接调试，但不会把一次实验失败扩大成不可恢复的启动损坏。

所有实验记录必须注明控制机、目标机、恢复路径和连接方式。
