# 2026-09-14 重装后 Recovery guest 图形对照

## 本轮观察

### IORegistry 绑定证据与本轮中断

用户随后重新明确授权本地 DFU 完整抹盘。11:24:39 UTC 固定 25G83 IPSW 全文件 SHA-256 校验通过；原版 upstream idevicerestore matched-tty 单次等待器核对 Mac16,12/j713ap、Port ECID 后触发。Port DFU 控制器阶段成功，选择 Customer Erase Install (IPSW)，已按授权输入 YES；取得 SHSH、上传 iBSS 完成后仍报 Device did not disconnect / Unable to place device into recovery mode from DFU mode。尚未到 iBEC/restored/完整写盘，不称为已抹盘恢复成功。没有改恢复协议，没有自动重试。原始证据在 ../2026-09-13-iokit-ram-root/raw/dfu-erase-20260914-post-guest-1/。

后续用户明确反馈反复重启、无法进入 Recovery，不能再把本轮称为安全退出或当前 guest 正在运行。11:22 UTC 被动 sysfs 检查仅有 M1 USB root hubs，无 M4 枚举；无 run-recovery-guest/idevicerestore/kisd/irecovery 进程。当前没有诊断/恢复连接，未发送固件或再次修改策略。保留原生与 fallback Recovery 人工进入、必要时官方 DFU Revive 的救援路线；旧 Restore 授权不作为本轮自动抹盘的理由。

通过 getRegistryRoot、getPropertyTable、getChildSetReference、OSDictionary/OSArray/OSString 方法的实机反汇编解析对象布局，再只读遍历 IOService plane，获得 1506 条记录、其中一条解析错误；不是完整无误的 ioreg 替代。raw/ioreg.json 证明 AppleASCWrapV6、RTBuddy(MTP)、AppleDockChannel 和 AppleHIDTransportHibernator 已绑定。transport 下另有 AppleHIDTransportDeviceUserClient、AppleHIDTransportBootloaderUserClient，以及 AppleFirmwareUpdateUserClient。固件加载对象包含 AHTLoaderName、LoadingGroup、Need FUD Download 等属性；已解码一个 AHTLoaderName 为 stm，尚未解码 Need FUD Download 的布尔值。因此不能继续笼统称驱动完全未接管，也不能仅凭属性名认定正在联网下载。

随后交互检查把 LoadingGroup 数值对象错误地交给字符串解码，未检查其内容指针及 hv_translate 结果就执行 readmem，出现 UartChecksumError，接着串口 EIO、USB 消失。时间顺序与该诊断错误相邻，但尚未取得目标异常日志确认具体复位路径。不是已确认的 guest 输入驱动崩溃，更不是故意执行重启。已退出失效的 host 会话 56081，停止继续读写；初次重连未发现 m1n1 USB。

必须修正诊断流程：按对象类型解码属性；所有字符串数据地址先验非零和可翻译，禁止把未知类型当字符串或将失败翻译的 0 交给物理 readmem。持久磁盘/策略没有在本轮被主动修改；不能据此保证所有真实外设无副作用。后续需重新确认目标屏幕及代理是否恢复，不自动 DFU 或刷写。

### 无本机输入的 HV 检查

可复用进程检查器已在 live HV 验证：读取 98 个记录，因 head_or_invalid_record 停止，结果 raw/processes-checked.json；不把 98 称为确定的全系统进程总数。对 dockchannel-mtp 六段寄存器加入 ASYNC 访问追踪，恢复 guest 后观察 30 秒，无访问事件输出。随后移除 PrintTracer 并 cont。此窗口没有观察到该通道驱动的寄存器访问，不证明启动早期从未访问，也不单凭它确定固件或中断根因。

用户报告键盘/触控板均无响应。通过同一 HV 会话切换全部 10 个 CPU 并读取堆栈成功；多栈含 thread_block 邻近地址，但稀疏符号不能精确命名全部帧，不能据此断言全机死锁。

进一步读取 guest 进程结构，确认 PID 1 launchd、PID 76 WindowServer、PID 132 RecoveryOS Agent、PID 155 Boot Picker，以及多个后台服务。因而撤回仅凭早期 console ring 怀疑用户空间未启动的判断；guest Recovery 用户空间和图形服务已存在，界面交互仍未通过。原始列表在 raw/processes.json。PID 偏移 0x60 由本版 proc_pid 的 ldr w0,[x1,#96] 确认，短进程名偏移 0x5cc 由 proc_name 确认；从 kernproc 的双向列表反向读取，有上限和停止检查，不执行 guest 内核函数。可复用检查器为 scripts/guest-processes.py，返回的名称可能截断，列表完整性未认证。

guest ADT 保留 mtp、dart-mtp、dockchannel-mtp、mtp-aop-mux，以及 keyboard/multi-touch 子节点，不能将输入失效归因为这些节点被删除。依据本地 ASC/dockchannel 寄存器定义，仅读取状态，不读取会消费数据的 RX FIFO：MTP CPU_CONTROL=0x10，CPU_STATUS=0x6c，INBOX/OUTBOX_CTRL=0x20001；dock IRQ mask=0、flags=0，RX_COUNT=0x408（1032 bytes），TX_FREE=0x800。间隔复测相同，另一方向 RX_COUNT=0。说明被观察方向有未消费数据，是输入 transport 初始化/处理链路的线索，尚不是 IRQ 丢失的确定根因。

未运行会复位 MTP/重配 DART 的 experiments/mtp.py，未强制打开 IRQ，未消费 FIFO。每次采集后 cont，guest 继续运行。下一步应追踪驱动是否访问 dockchannel/注册中断，以及固件请求是否因移除 SSD 或旧 iSC 而未满足；不得凭当前寄存器值直接打补丁或称完整 macOS 已可交互。

RAM 输入上传、BootArgs/ADT 读回、SPTM HLE 初始化通过，执行 XNU entry 0x1002645c000，九个 secondary guest 启动请求出现，BaseSystem RAM 分类 adapter 实际应用。用户随后看到 Options 图标和旋转圆圈。这是屏幕显示的用户反馈，不足以证明完整 Recovery 工具界面加载成功，也尚未排除继承的启动图像。

两次主动 HV 中断均能进入 shell，采集后执行 cont 恢复运行，没有重启或丢失控制进程。两次 console ring write_pointer 均为 0xfffffe6fedff81a8，只有早期 XNU/VM 线程日志，尚无本轮 WindowServer 或 launchd 成功证据。graphics 模式下日志可能不完整，不能仅据此断定死锁或正在正常推进。

读回 framebuffer 17039360 bytes，508 种像素值，SHA-256 ecf656f0ae9a6ad345cc4c27d0064198c7c02d86a8b10097e18dcfe6f121ad93，保留 raw/framebuffer.bin。单帧不能证明图像由 guest 新绘制或动画持续推进。当前保持 guest 运行，尚未验收完整 macOS/Recovery UI。

在新 stub 已完成普通重启和 USB/proxy NOP 验收后进行。目标是从 m1n1 SPTM HLE 启动 25G83 Recovery 用户空间，不是直接启动 SSD 上安装的完整 Macintosh HD。

输入使用固定 25G83 Mach-O、已解包 APFS BaseSystem、原厂 Recovery root hash。guest 限制 16GiB/10 核，移除 ans，使用 RAM-only GPT 呈现 BaseSystem 和 iSC，启用 graphics，保留 console-log。这不是完整硬件沙箱，其他外设仍可能与真实硬件交互。

iSC 是 2026-09-13 抹盘前从本机读取的旧副本；其机器标识匹配不等于其策略、xART 或 SEP 状态与重装后匹配。不将它写回 SSD，也不将其当作当前 iSC 备份或一致性快照。

本轮命令（需要已有本地二进制输入；只在空闲的原生 m1n1 proxy 上执行一次）：

```sh
nix develop --command bash -c '
umask 077
mkdir -p experiments/2026-09-14-macos-guest/raw
sudo -n env PYTHONPATH="$PYTHONPATH" "$(command -v python3)" scripts/run-recovery-guest.py \
  artifacts/apple/25G83/derived/kernelcache-25G83.macho \
  experiments/2026-09-13-aligned-recovery/raw/recovery-25G83.apfs.raw \
  --root-manifest experiments/2026-09-13-aligned-recovery/root-manifest.json \
  --kernel-sha256 f42ad6f51d130141095a94b4749d128d648f2be2ac0c291bf492ac1c64e5875d \
  --output experiments/2026-09-14-macos-guest/raw/guest.json \
  --guest-memory-gib 16 --guest-cpus 10 \
  --recovery-root-hash artifacts/apple/25G83/j713/Firmware/022-22048-093.dmg.aea.root_hash \
  --recovery-root-hash-sha256 577661fd264e5745736d4d31ff14598c5ad1f7360fad5092f79ac04b7562e8d9 \
  --inspect-apfs-root --direct-basesystem-root --ram-root-boot-uuid --iokit-ram-root \
  --isc-image experiments/2026-09-13-iokit-ram-root/raw/isc-acquisition-1/isc.raw \
  --isc-manifest experiments/2026-09-13-iokit-ram-root/raw/isc-acquisition-1/manifest.json \
  --console-log experiments/2026-09-14-macos-guest/raw/guest.console.log --graphics
'
```

不通过 tee 包裹交互进程，以免 Ctrl-C 终止宿主 Python 而非进入 HV shell。不启动第二个串口连接与现有会话竞争。
