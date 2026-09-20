# m4-linux 项目 Skill

- GravityLinux/gravity-m4 head9807df349e5c审计：顶部Asahi合并b39c4d→head共42个单父提交；直接M4 36（GPU21），加SMC GPIO依赖39，全部配套42。与当前Asahi7.1.8分叉ahead758/behind28不能当M4数量。877c574大DCP提交已带nowfxt；8178b0ad是T8132 NVMe IO queue寄存器支持；GPU/SSD board启用主要为J773g而非J713。详见GRAVITY_M4_COMMITS_20260915.md含全部commit链接。未应用/构建/启动，GPU测试仅作者声明，不当本机验收。

- 2026-09-15 Linux patch 审计：详见 LINUX_PATCH_AUDIT_20260915.md。实际候选来自 Asahi tag asahi-7.1.8-1 加九个额外 patch，多为 M1 DP-alt；不是项目独立 Linux package。已定位最小 T8132 DT fbf2e630、AIC3 1f0cf051、idle=nop 13e700ef 和 Sven NVMe 固件修复系列（已包含，不能再笼统称缺失）。J713 无 NVMe/USB/PCIe 完整 DT，NVMe/DART 等为模块而 RAM 根没带模块；cpuidle 白名单不含 T8132，WFxT override 仍缺。精确 SMP 修复未闭环。不连接/启动目标；前轮只检查到 ttyACM 不存在，没有上传或重启。

- Linux 路线最新状态：用户要求先核对参考，live boot 暂停；只在 M1 构建了 Nix RAM initramfs 和未验证 loader，未上传 Image/DTB/initrd、未 prepare/handoff、未重启/Recovery。详见 LINUX_BOOT_REFERENCES_20260914.md。候选 7.1.8 有 J713 DT 和 idle=nop，但无 arm64.nowfxt override，delay 仍用 WFIT；cpuidle.off=1 不能替代 idle=nop。先对齐参考补丁再实验，不将脚本草稿当已验证入口。原生 Linux 无需先跑 SPTM/XNU；ACM1 仅 HV VUART，direct boot 后 ACM 消失不能单独判失败，earlycon=efifb 也不保证适用于本机 30bpp/FDT 启动。

- 15:22:30最新实机验收：本轮083C641C stub持久化m1n1已启动，双USB串口/串号M49KYH65C9，UART NOP与proxy NOP均ok，等待器exit0已结束；结果raw/post-erase-m1n1/proxy-check.json。控制台EL2、32GiB、mBoot18000.161.10，MCC/cpufreq unsupported仍存在、无Linux payload。保持proxy待命，无guest/内核上传/重启，不复用旧iSC；此结果不是Linux/SPTM guest支持验收。

- 最新083C641C stub安装已完成：配对1TR实测后csrutil disable、kmutil raw/entry2048/VA0与bputil-c-a-s均exit0，Permissive/sip0=7f/sip1/2/3=1/coih445A4EE6…、Paired/Valid。bless恢复原Macintosh HD默认，读回2D4EFB69；已正常关机，待用户物理选择M4 Linux Bootstrap→继续。900秒单次代理等待器仅检查同串号双端口并NOP，45秒检查上限；预定raw/post-erase-m1n1/proxy-check.json尚待结果，不说已启动m1n1。无guest，未hash，原生变更后重启待验收。

- 15:14后SSH恢复，当前owner元数据已复制到新083C641C stub；bputil-g成功Reduced/Valid/coih absent，bless成功且boot-volume指新stub。当前Recovery对stub仍Not Paired，未kmutil。已告知并发送sync; shutdown-h，等待用户物理长按进入新stub配对1TR后重启ssh.sh，再核对Paired才能继续。断线不是已证实崩溃；未重做分区/stage，后续安装完恢复macOS默认启动。

- 最新重装断点：post-erase-m1n1/stage.txt实机exit0，固定Nix boot.bin和25G83资源已部署，未hash。随后owner复制和bputil-g两次SSH均TCP超时，未执行；15:08:14USB断开，ping仍通而22不通，未主动重启。尚未生成stub策略/bless/kmutil/代理验收。先恢复Recovery SSH，按新083C641C卷组继续owner与配对，禁止重跑缩容/建卷/stage。详见M1N1_POST_ERASE_20260914.md。

- 新m1n1重装正在进行，当前状态转见M1N1_POST_ERASE_20260914.md：原macOS缩至128GB，fsck退出0；新4GB stub容器35889682/卷组083C641C-7DBA-44D7-9C86-7925CE0050DE，另1GB EFI、余下未分配。未动iSC/系统Recovery。使用固定25G83公共资源和Nix m1n1，stage新增显式UUID及--skip-file-hashes；不跑旧固定UUID脚本、不复用旧个性化状态、不启动guest。部署/策略/配对/代理验收分开报告。

- 15:02按用户明确授权已对新macOS卷组2D4EFB69执行csrutil disable与bputil -c -a -s -v，所有者交互认证成功、两命令exit0。复读SIP disabled/Authenticated Root disabled/Permissive/sip0=7f/sip1/2/3=1，Paired/Integrity Valid、coih absent。未分区、kmutil或重启；不是所有硬件安全关闭，也不是guest防brick修复。证据raw/post-erase-recovery-145831/security-after.txt。交互ssh必须exec tty=true，只有ssh -tt但host stdin关闭无法回答提示；旧等待确认进程已终止后重开，本轮无遗留交互任务。

- 14:58新Recovery SSH已实测：root@172.24.5.124、26.6.2/25G83、ECID匹配、Paired one true recoveryOS/Integrity Valid。新主容器EFE517FC、卷组2D4EFB69-013E-4618-997E-3AFDB3F1E2E5；sequencer UID501/UUID0A98877A-4388-469D-8D3C-99CDBAD24C43为Volume Owner，AppleSetupDone存在。全盘仍原厂布局，无stub/Linux；Full/SIP/SSV/CTRR开启、coih absent。本次只读，未分区/改策略/启动guest。证据raw/post-erase-recovery-145831/state.txt，旧UUID全部不套用；不再要求用户重做账户。

- 用户随后进入抹盘后的新Recovery：记录Recovery入口可达，但未确认备用模式；主机见05ac:1905，172.24.5.185:8000的ssh.sh及临时host key均HTTP200。新Recovery需重新启动sshd，不能沿用旧会话/旧磁盘UUID，也不能据USB枚举称SSH已连通。先只读获取当前系统/卷/所有者，再决定安装步骤。

- 最新用户验收：针对完整Erase后的设置界面/原生启动询问，用户确认“成功了”。本轮Linux DFU完整恢复及恢复后启动已获确认，覆盖下方等待验收状态；账户配置、重复重启、普通/备用Recovery尚未单独验收。保留25G83+firmware-kis-trace-tools显式Erase成功基线，不归因于日志修复、不自动重跑guest、不回放旧iSC/LocalPolicy。

- 14:49:48本轮Linux完整Erase已DONE/restore_exit=0，日志raw/linux-dfu-erase-143802/；14:50确认恢复/usbmon进程和锁均已清理，USB仅root hubs，等待用户原生设置助理/稳定启动验收，不自动m1n1/guest。此次iBSS也完整status512后真实切换；不可再称Linux未完成过Erase。exec外层exit1来自本机bash_logout的set-u未定义变量，非刷机失败；以后长任务login=false。旧UUID/iSC/LocalPolicy失效，不回放。尚未证明旧失败根因或日志补丁具有修复作用。

- 14:38：Upgrade 实际14:35:43 DONE/restore_exit=0，但用户反馈原生仍失败并要求抹盘。14:37第一次Erase因旧usbmon锁未启动；root0600 pid文件不可读让cleanup卡在wait，核对后只杀旧cat，非恢复进程。新capture由用户预建pid文件并关闭继承fd9。14:38:02已核对Port身份，运行单次显式--erase/Customer Erase Install (IPSW)，raw/linux-dfu-erase-143802/，会话91030；尚无完成验收。M1备份不动，旧iSC不回放。

- 14:33 新实机覆盖“无 DFU”：Port 身份核对后单次 firmware-kis-trace-tools 显式 Customer Upgrade Install (IPSW)，无 erase。iBSS BOOT_IMG 完整回复 size4/status512 后约1.7秒真实断开，iBEC/恢复内核成功，RestoreOS身份通过并进入固件更新。status非零不能直接判错误。尚无最终退出/原生验收；Update与旧Erase、日志时序、设备状态差异未控制，不能称已找到根因。日志 raw/linux-dfu-upgrade-143305/，恢复会话5876；结束必须更新状态，不自动重复或转Erase。

- 14:30 Linux DFU 再次排查：USB 仍只有 root hubs，未上传/恢复。新增独立 firmware-kis-trace-tools（上游 idevicerestore + 仅三处 KIS stderr 的 libirecovery），Nix 构建及 ldd/derivation 检查通过，不继承旧 strict/guard/流程补丁。BOOT_IMG 回复需完整长度和成功传输才可解读，失败时零初始化 status 不是设备成功。120 秒 usbmon/udev 是一次被动采集，不是刷机等待器；设备回来后重新采集再实验。不使用仍含 hash 的旧 erase wrapper，不称日志补丁已修复故障。见 DFU_HOST_DIFFERENTIAL_20260914.md 最新节。

- 本次 restore 故障的修复顺序见 NVRAM_GUEST_INCIDENT_20260914.md“修复决策”：原生入口先取证并选择 Macintosh HD；只有 firmware Recovery 时先读 iBoot，历史 setenv PIPE 不当成可写；仅 DFU 时采用已成功的 Finder host，Revive 后按实际结果决定是否 Restore。最新探测 USB 无 M4、最后已知 SSH 超时，未实施修复。64KiB 启动前 proxy 不是整 NOR 备份，不回刷。正常 guest 关机也会同步持久状态，不能当作 NVRAM 隔离。不得把缺输入固件与本轮 restore 根因混为一谈。

- 13:26之后重要更新：用户要求补资源重跑，已本地准备RAM FAT盘与serial=3/-s入口，但尚未上传或启动。旧guest中hv.reboot执行整机WDT硬复位后ACM未返回，用户报告循环及restore URL；不是新资源导致。当前guest会话已结束，不再说cont运行中。新iSC、无旧错误指针读取仍出现该现象，不能将旧副本/错误解码当唯一根因。离线确认保存guest ADT和ioreg保留qspi→spinor→anvram（QSPI0x3ad118000，NOR分区0x700000+0x100000），HV OFF映射是直通；AppleARMNORNVRAM::write在0xfffffe0008aca630可调用NOR写。RAM根不隔离真实NVRAM。启动前proxy基线65536字节、bank11/16、generation124，已解析active boot-command=fsboot/auto-boot=true/boot-volume新stub；没有故障后差异，不宣称具体变量被改。iBoot失败处理自身也会写恢复变量，必须区分原因与结果。调查见docs/NVRAM_GUEST_INCIDENT_20260914.md，不清NVRAM或刷机替代取证。

- 13:20 补充：默认FUD资源路径已由本轮dyld反汇编落实为 `[preboot][bootobjectspath]/usr/standalone/firmware/FUD`；resolver先检查iSCPreboot对应boot路径，ENOENT才退普通Preboot。当前iSC只读副本volume0的stub目录仅LocalPolicy、无boot，RAM根+iSC没有默认所需FUD资源；尚缺本次用户态具体错误/是否使用FWDirectory覆盖的证据。RTBuddy bootloader +0xe0指向mtp下载器，状态/timeout=0/0，不是已证实state=1死锁。长进程名读proc+0x5dd最多33字节，Mobile前缀不能当FUD进程。当前guest已cont且临时断点清空，最小人工步骤为在空闲Type-C接外置USB键盘/鼠标，不拔调试线、不重启；usb-drd1节点存在但外设输入尚未验证。

- 2026-09-14 13:14 更新覆盖下方“本轮未读 IORegistry”的旧阶段描述：同一 guest 原脚本遍历得到1425条、一条unmapped；固定 getRegistryRoot 全局0xfffffe000c658488。三个 AIDImageDownloader 的 vtable=__ZTV+16，类型确认后读取 stm/ipdf、multi-touch/mtfw、mtp-transport/mtpf：Need FUD Download(OSNumber)=1，isDownloadComplete(+0x180 bit0)=false。LoadingGroup同样是OSNumber，绝不可当OSString指针；AHTLoaderName此处实际为OSSymbol。已确认输入固件加载未完成，不只是猜测IRQ。用户态GenericKextUpdaterService profile包含/private/preboot和boot-objects-path，但本次具体文件错误尚未拿到。短时loadFirmware/beginFirmwareDownload硬件断点无命中后已清除，guest已cont；不重启、不hash、不消费FIFO。证据见本轮实验README与ignored raw/guest-current-isc-1/aid-status.json。

- 同一新 iSC guest 继续调试：十核栈主要落在固定内核 PMC 读取/公共路径，不是已识别的 MTP 阻塞栈。保存的 guest ADT 根 UUID 指 RAM Recovery，但 apfs-preboot-uuid/boot-objects-path 仍指 Bootstrap；RAM GPT 只有根+iSC，没有该 Preboot，是资源呈现缺口，尚未证实为输入固件加载的实际失败路径。不要盲改 UUID 或称确定根因。HV shell 中 exec 是汇编接口，Python 多行必须 builtins.exec；本次误用在 host 汇编阶段失败，之后正确采样并 cont，未重启。

- 新 iSC guest 输入现场已复测：真实进程列表含 WindowServer/hidd/Boot Picker，Options 转圈但 Tab/触控板无响应。MTP/Dock 状态 IRQ_MASK=0、RX_COUNT=0x408；短时 ASYNC 跟踪 IRQ/FIFO/mailbox 未见 guest 访问，之后已删除 tracer 并 cont。不是据旧现场推断；不消费 RX_DATA，不实例化会写 IRQ_MASK 的 DockChannel。下一步需定位固件请求或 transport 初始化等待，尚不能断言中断丢失或设备树缺失。本轮没有运行 IORegistry 解码、没有重启。

- 本轮新 iSC guest 已实际执行，用户确认 Options 图形界面，但鼠标无法移动；键盘尚未确认。host guest 进程仍在，当前 console 无新 panic，但不能据进程存活断言 guest 无死锁。新 iSC 没有自动解决输入问题，不能将输入失效全归旧 iSC；此前 MTP 寄存器/ioreg 结果是旧实验，不能套作本轮实时状态。此次只查本地日志，未读取 IORegistry、未消费 FIFO、未重启。

- 用户明确要求新资源启动 guest 后，本轮已从 Recovery bless Bootstrap 并 reboot，实际返回 m1n1。现运行原 launcher，新增 --skip-file-hashes 遵从不再计算 hash 的要求；内核/root 的 digest 字段此模式取既有清单，report.file_hashes_verified_this_run=false，新 iSC 无 digest。使用 current-25G83 目录和 /home/sequencer/m4-linux-backups/20260914-clean-123915/current-isc/isc.raw，非旧 iSC。16GiB/10核/graphics，日志 experiments/2026-09-14-reinstall-retained/raw/guest-current-isc-1/。默认启动已改为 Bootstrap，不再称 macOS 默认。移除新守卫不表示旧风险已解决；上传与 guest 实际开始分开判断，不并发连接串口、不自动重刷。

- 最新：用户要求不再 hash、不做防御性开发。本轮 macOS 已实际启动，随后 SSH 确认 macOS Paired 1TR。只读 dd /dev/rdisk0s1（当次 UUID 2935ACB5-2A69-4996-942A-87B29BC17A2F）复制到 /home/sequencer/m4-linux-backups/20260914-clean-123915/current-isc/isc.raw，524288000 字节，传输退出 0。manifest 无 sha256，未验证原子快照；不是旧副本，也不是全盘备份。既有 guest launcher 的 --isc-manifest 仍要求 sha256，不能称此清单可直接供原脚本启动。没有启动 guest 或修改 target；保持 Recovery 会话。

- 最新用户要求覆盖此前推进计划：撤回防御性开发，专注干净备份。guest_memory 新增模块、进程/panic 读取接口改造、IORegistry 入口封锁、run-recovery-guest 新增无条件退出均已撤回；下文关于这些改造的文字仅是历史。保留原有版本/哈希检查、更新后的 25G83 资源和事故记录，不追加策略框架、不擅自启动 guest。备份须复制实际文件而非仅 symlink；不得把本机文件备份称为 M4 全盘可恢复镜像。

- 离线隔离审计见 GUEST_ISOLATION_AUDIT.md：固定 HV.init 将 arm-io ranges 注册为 OFF，pt_update 的 OFF 实际 map_hw 恒等直通，不是禁访问。删除 ANS ADT 节点不是 stage-2 deny。新增 guest_memory.GuardedReader，显式 VA/PA 白名单、kernel hash、分页全请求预检、精确长度、预算、失败锁死；进程/console 诊断必须注入 reader，无默认 live 范围。IORegistry 因缺可靠 OSObject 类型 profile 入口封锁。旧 APFS BRK 写入及上游 HV 仍未完成隔离审计，launcher 不解锁。22 项离线检查和额外失败锁死验证通过不代表硬件异常可恢复。此次未触碰 target。

- 当前资源统一入口改为 docs/CURRENT_BOOT_ASSETS.md 与 artifacts/current-25G83-post-restore-20260914/manifest.json；从固定 25G83 官方输入重新解包内核/转换 Recovery，旧实验目录仅历史。实测 result 最初仍为 d617ceee… 的原 PR 构建，尽管 stub 安装的是 779c9ac3…；prepare-current-assets 校验拒绝后重新 nix build .#m1n1-sptm，result 已对齐 779c9ac3…。不要只看包名/PR commit 判断本地补丁是否匹配。manifest 明确 current_isc_capture=null；绝不自动带入旧 iSC 或 restore staging 的旧 update-plan。run-recovery-guest.py 的 main 现直接退出，prepare-only 也封锁，防止历史命令再运行；资产更新不是解除隔离门槛或防 brick 保证。

- 2026-09-14 12:25 UTC 本轮新安装 m1n1 已实机验收：物理选择启动后 USB ttyACM0/1、UART NOP/proxy NOP 均成功，EL2，32GiB，mBoot-18000.161.10。结果在 experiments/2026-09-14-reinstall-retained/raw/m1n1-proxy-check.json，等待器退出 0，代理无人占用。MCC/cpufreq unsupported 和 No valid payload found 仍存在，不等于 Linux 支持。没有运行 guest，旧 guest 路径仍暂停；原生 macOS 和备用 Recovery 验收尚待进行。Nix bash 本次无 compgen，等待设备用 test 再校验 USB 身份。

- 本轮 m1n1 启动验收已安排：安装文件/策略再次核对通过，不重复 kmutil；保留 macOS 默认启动，正常关机后由用户在启动选项选择 M4 Linux Bootstrap → Continue。Nix 下 900 秒 USB 等待器只执行一次 UART/proxy NOP，不运行 guest。未见实际成功 JSON 前不得称本轮代理验收通过；等待器过期应先核对进程，不声称一直监听。

- 2026-09-14 12:21 UTC 最新覆盖：用户进入 Macintosh HD 配对 1TR 后，按明确授权完成原生 macOS csrutil disable 和 bputil -c -a -s -v 742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8，均退出 0。两套安装 csrutil status 均 disabled；两套策略均 Permissive/sip0=7f/sip1/2/3=1，配对完整性 Valid。macOS coih absent，stub 原 coih 保留，默认启动仍 macOS。没有执行 macOS kmutil、清除 iSC/策略、重启或 guest。只能称这些启动安全限制已配置关闭，不能称所有安全机制关闭或此前 bootloop 已修好；仍待原生启动与本轮 m1n1 验收。

- 最新覆盖：新 stub 530FE39B 的配对 1TR 已完成 csrutil disable、kmutil configure-boot 和 bputil -s，Permissive/sip0=7f/sip1/2/3=1，尚无本轮 m1n1 启动验收。默认启动已恢复 Macintosh HD（742D07D7）。用户明确要求原生 macOS 也关闭安全限制；在 stub Recovery 对 Macintosh HD 执行 csrutil disable 被明确拒绝 Not Paired，退出 69，macOS 仍 Full/SIP/SSV/CTRR/参数过滤 Enabled。必须关机、物理长按进入 Macintosh HD 配对 Recovery 后再操作，不重复在错误配对环境尝试；安装列表次序会变，按名称和 UUID 而非固定数字选择。关闭这些选项不是已验证的 bootloop 修复，也不等于清除 SEP/iSC/所有硬件安全。

- 2026-09-14 12:00 UTC 后再次完整 DFU 的新安装记录在 experiments/2026-09-14-reinstall-retained/README.md，覆盖此前所有 UUID/启动验收。已保留 128GB macOS、新建 4GB stub 和 1GB EFI，其余未分配；新 stub 组 530FE39B-6AE3-47D0-9168-29F1A7EE2763 已部署固定资源并新生成 Reduced 策略，尚未 kmutil。bless 暂选 stub 供配对 Recovery；配对安装结束恢复 macOS 默认启动，再物理选择 m1n1 验收。所有者只用本轮系统元数据，绝不恢复旧 iSC/LocalPolicy。保留原系统并非已通过缩容后启动验收。旧 guest 仍暂停。

- 本轮 guest 后普通/备用 Recovery 均失败，现有 run-recovery-guest 路径暂停复用。删除 ans 不构成 SEP/NVRAM/协处理器隔离；不得再使用抹盘前 iSC 副本运行 live guest。先完成正常系统/两种 Recovery 回归验收、统一内存读取安全守卫及持久化路径审计，详见 GUEST_INCIDENT_20260914.md。错误 OSNumber→OSString 读取与失联紧邻，但无法解释持久 bootloop 的完整机制，禁止把推测当根因。

- HV 只读诊断也可能导致 target 异常：2026-09-14 交互解析 IORegistry 时将 LoadingGroup OSNumber 当 OSString，未验 hv_translate 返回值便 readmem，随后 checksum/EIO、USB 丢失。不能把 readmem 当作无风险操作；先解码对象类型，严格拒绝空指针、未映射 VA 和跨页未分段读取。该故障与 guest 输入根因分开记录，禁止失联后自动刷机。完整过程见 experiments/2026-09-14-macos-guest/README.md。

- graphics guest 的 console ring 可长期只保留早期 XNU 日志，不能据其 write_pointer 不变断言未到 userspace。2026-09-14 HV 只读进程结构确认 launchd/WindowServer/Boot Picker 存在；键盘触控板仍不可用。读取输入状态时不要启动独占 MTP 实验脚本或读 RX 数据寄存器，它们会重配硬件或消费 guest 数据。详见 experiments/2026-09-14-macos-guest/README.md。

- 2026-09-14 重装后的独立 stub 已重新完成配对 1TR、csrutil、kmutil 和 bputil -s，普通重启实机 USB/UART/proxy NOP 全通过；见 M1N1_RESUME_20260914.md。这是新布局的验收，不复用旧 UUID。ttyACM 为 root:dialout 0660；Nix Python 通过 sudo 运行需要显式传递 PYTHONPATH，否则 pyserial 不可见。只提升本次检查进程，不全局安装依赖或 chmod 串口。

- 重装创建账号后必须重新检查 Volume Owner 和 Recovery 配对状态。本轮新账号 sequencer 已是 owner，但当前仍 ordinary recoveryOS/Not Paired，stub 无 LocalPolicy；不能复用 liqi 的旧凭据或抹盘前安装验收。多个 Preboot 同名卷的挂载顺序会令 stub 实际挂到 `/Volumes/Preboot 1`，其旧绝对 restore 链接可能失效；按卷 UUID 定位并核对路径。新基线见 M1N1_RESUME_20260914.md。

- 不要直接启动 `/System/Installation/CDIS/Installation Log.app` 来满足“打开实时安装日志”。25G83 实机其 bundle ID 是 `com.apple.install.crashlog`；无参数启动 PID 892 后注册 Installer Crash Catcher，记录 hide progress UI，用户随即看到安装失败，而实际 InstallAssistant/osinstallersetupd/UpdateBrain 仍运行，持续 PREPARING_UPDATE stalled:NO。优先用安装器自身的日志菜单，或终端 tail；不可将该窗口当作底层安装失败并重启/抹盘。本轮仅关闭误开的 PID 892，不终止安装器。

- 本地 IPSW 19.77 GB 不能传入只有约 2.3 GiB 空闲的 Recovery tmpfs 或 4 GB stub。必须先选足够大的持久化资源卷；本轮在空 Linux 范围建立 128 GB 临时 APFS，传输使用 `.partial`，按固定 SHA-256 验证后才改名。资源卷与未来 ASR 目标卷必须分离。详细现场见 LOCAL_IPSW_REINSTALL_20260914.md。

- 未初始化 macOS 的 Linux-only 实验：用户确认 Restore 后未建账号，不能把无凭据归因于删除，更不能把 Apple ID 当成本地卷所有者。新 stub 文件放置和 APFS bootable flag 成功后，bputil -g 仍实测 exit 8/no admin users authorized for recovery。root SSH 不等于 ACM 所有者授权；未验证前不重启、不复用抹盘前凭据、不声称 SIP 已关。现场、资源哈希和新 UUID 见 LINUX_ONLY_20260914.md。
- Recovery 使用安装器 Python 必须同时设置 DYLD_FRAMEWORK_PATH 和 DYLD_LIBRARY_PATH，后者指向 Frameworks/Python.framework/Versions/Current/lib，否则 ctypes 缺少 libffi.dylib。diskutil 添加 Linux GPT 分区可能自动生成 Apple_Boot helper，必须读回真实布局，不假设所有剩余字节均属于 Linux。

## 完整Erase授权与执行入口（2026-09-14）

- 用户重复明确授权删除M4日常macOS容器后，已核对新主身份/分区UUID/容器UUID/精确大小，原版`diskutil apfs deleteContainer disk3`正常成功，释放约2TB。该版本不带newName时直接移除分区、变未分配空间，无需追加eraseDisk或force。先以hdiutil确认当前Recovery为ramfile、根在disk5s1；删除后独立SSH验收仍在，iSC/System Recovery UUID及大小保持不变。容器内部配对Recovery也随容器删除，不能复用之前Paired策略当作未来stub授权。尚无新Linux/m1n1可启动布局，保留当前Recovery会话继续开发；空间释放不等于安装完成。

- Recovery重装后可从ssh.sh HTTP访问记录定位新地址，排除M1自身健康检查请求。本轮M1为172.24.5.185，M4下载来源172.24.5.124，root公钥登录成功；临时hostkey未变，通过旧已知key和HostKeyAlias校验，无需关闭hostkey校验。新系统25G83、Paired 1TR/Pairing Integrity Valid、Full Security；重装后的disk0s2/disk3及新卷组须作为新基线，旧Bootstrap UUID/安全策略不可复用。HTTP脚本内hostkey下载地址需随M1网络变化更新。

- 全盘Restore后用户已确认正常macOS桌面，之后目标是仅Linux且授权删除M4日常macOS。该授权不证明已有可用Linux启动链；实施需先重新核对新系统身份/分区，并区分日常系统卷与必需Apple启动/恢复组件。不要复用恢复前disk编号/卷UUID，也不要把M4抹盘授权应用到M1。正常桌面验收已通过，完整重启测试尚未记录。

- 最新术语/验收更正：用户澄清先前“恢复完成但无限重启”实际是Revive修复完成；之后另外执行Restore并确认“抹盘恢复完成”。应以最新澄清覆盖旧操作分类，撤回“全盘Restore后仍bootloop”及其硬件推断。当前是用户确认全盘Restore完成，尚待设置助理/正常桌面和重启验收；不得将之前Revive后的重启症状套到新Restore实例。保留完成日志与新build/卷状态作为后续可复现基线。

- 最新验收纠正：用户明确Finder Restore已完成，M4仍无限重启。必须区分用户确认恢复完成与原生启动失败；旧MacUpdater4042文件是换口前记录，不冒充完成日志。恢复后原分区/启动卷/nonce状态须重新取证，不能套用旧Bootstrap UUID、panicmedic或rpnh静态候选。下一步收集完成日志和新启动panic/早期固件状态，官方恢复后仍循环可升级硬件诊断优先级，但不能无依据宣称主板/SSD损坏或继续不变条件刷机。

- 最新端口pitfall：用户Finder Restore/普通数据线报4042后，将M4端换到远离MagSafe的Type-C口，反馈正在等待更新固件。2025Air的DFU口与早期Air不同；看到Port DFU、ticket成功或端口固件完成不能替代物理口及主AP接力验收。当前仅流程有进展，不能将“好了”扩大为全盘Restore/原生启动完成。Finder进行时保持连接/供电，不启动竞争USB工具。MacUpdater旧日志Port成功后10分钟未接力，与M1四次已接力后的iBSS超时分开记录；阶段requestedUpdate不推翻用户确认的Finder Restore，Erase identity/FormatForAPFS不证明写盘。详见MACUPDATER_20260914.md，原始日志已ignored raw0700/0600+SHA留档。

- 修复思路见DFU_REPAIR_PLAN_20260914.md：先分离native panicmedic与DFU handoff，实际验收M4 2025远MagSafe DFU口/普通数据线/仅键盘和M1端连接条件，再增加被动usbmon。host内核USB_MON=m、模块存在不等于已抓包。标准初始Recovery直接iBEC/go可避开iBSS，但不自动补DFU Stage1 LPOL/固件、本M4Local Stage1未验证；不强改当前DFU等待器允许1281，也不复用撤回goto补丁。KIS get_mode是client缓存，fresh信息查询可能初始化/配置USB，不与恢复竞争；boot-img回复长度/状态校验不足只是抓包审计候选，不立刻patch。macOS14+ Finder完整Restore作为修好优先备选，M1保留APFS分区不证明可启动macOS，不擅自重启/改host或扩大M4抹盘授权。
- 04:20 matched-tty第四次干净Erase已真实触发；工具fd0/fd1均PTY、AI已输入YES、显式Erase variant/原cache/单debug均落实，仍于04:21:23 iBSS后10秒无断开失败exit1，没有iBEC/restored/StartRestore/完整写盘。等待会话30994与恢复PID1174039已退出，不再称后台正在刷机或还等硬件。被动USB证实f014→1881，04:21:55才实际断开；同期原始只读查询无法连接，没取得内部Recovery/本次boot-stage。对齐profile不充分，不能继续将漏TTY/cache/variant当确定根因或要求不变条件下再次盲刷。通用Possibly invalid iBSS仅说明等待事件失败，不是文件校验；晚断开与查询接近不证明因果。日志/哈希见DFU_ERASE_20260914.md最新段。
- 04:17 matched-tty已实现为wait-for-dfu-erase.sh第四参数，只改启动包装，原diagnostic默认及目标守卫保留。真实PTY用Nix script创建，单debug/显式Erase variant/原cache；必须交互stdin，拒绝非TTY，AI等上游提示后输入已授权YES。离线test -t0/-t1实测通过不等于硬件profile成功。等待器30994/1168847已启动但未上传；模式观察另用被动udev PRODUCT，不从单debug缺少KIS字样定因。
- 用户指出此前同机成功时，先查sudo journal真实argv，不采用README泛化主ECID示例或直接断言Linux host不行。成功PortECID与当前相同；旧Upgrade/cache/TTY配置在22:10也失败，profile差异不等于根因。当前Erase identity实际正确，两个identity的iBSS/iBEC全entry相等，不能冒称选错文件；个性化签名仍可能不同。
- 关键日志陷阱：固定idevicerestore只有debug_level>1才打开libirecovery日志。成功的一次--debug没有KIS字样不能证明普通DFU；历史外部PID仍未知，只确认实际断开时序。不能把日志可见性差异当传输选择差异。
- 若后续对齐成功profile，用原版upstream配显式Customer Erase variant、原cache、一次debug及真实子进程PTY，不能使用拒绝Erase的guard版，也不能重定向tool stdout后还称真实TTY。Nix util-linux script可在保留TTY时将所有输出写私有raw；已授权的Erase YES由AI核对后输入，不加ignore-errors或协议跳过。示例及未实测声明见RESTORE_COMMAND_AUDIT_20260914.md。
- 第三次clean-3-dfu03:55:05仍同阶段失败，所有加载/等待已退出。03:53曾1281 Recovery但未获得boot-stage、未从Recovery执行Erase；中断/重新DFU可使query open=-1，不能把它当成依赖缺失或有效诊断。04:00仅命令审计，无第四次上传。
- 03:49重新插拔后的clean-2亦iBSS10秒断开超时exit1；两次--erase调用不是两次完整刷机，均无restored/StartRestore/完整写盘完成。第二等待器已结束，03:51中断后本次kisd也已停止。恢复退出后的原始kisd配置errno71、控制台0字节不是此前恢复根因或iBSS无效的证明；用户未确认换普通数据线，不宣称所有线缆条件均排除。
- 用户确认插拔只记录为物理动作反馈；host总线重建不等于DFU已进入或PD/debug状态全部重置。先看实际Apple模式与身份，未触发时明确需要键盘DFU，不以软件VDM补回并破坏当前条件对照。03:47重新插拔后第二次Restore仍未开始。
- KIS是上游支持的正常DFU路线之一，不能以fresh物理DFU仍1881判插错口/坏线/debug残留。连接条件对照必须实际两端拔线/直连/键盘DFU并记录反馈，软件dfu与debugusb动作不同，不直接混称。03:45新单次等待器54816/1150179只是已安排的条件对照，尚未上传，不说失败后仍有自动重试。
- 上游#737提议后续Restore-mode等待3→4分钟，已关闭未合并；固定master对应等待现为5分钟，不是#737已合并到5分钟。#165是已合并的macOS IOKit lifetime；都不解决当前Linux dfu.c iBSS10秒模式超时。找不到相应上游修复时如实记录，不能把不相关PR套入再叠加源码补丁。换连接条件仍失败时保留Apple macOS14+ Finder完整Restore作为支持的替代host路线，不能保证同一固定IPSW版本。
- 03:41干净--erase实测已触发，Port→主DFU via KIS成功，主身份/Erase identity/TSS通过，但iBSS后等待物理断开10秒失败exit1，未到restored/StartRestore。自动等待器已退出，不能继续称为存活或后台修复。此结果不依赖项目diagnostic补丁，但也不能据此排除原始工具链/传输问题或证实iBSS无效；本次未取得新控制台，不复用前次Remote boot作为本次执行证据。
- 用户再次明确要求直接抹盘DFU，覆盖历史禁止Erase，但只授权M4目标内部盘；M1备份、项目和固定固件不得删除。47GiB备份存在不代表完整，Pictures未复制，必须明确删除范围。
- 正式恢复只用firmware-upstream-tools/原始libirecovery与完整固定IPSW，不继续改idevicerestore协议。scripts/wait-for-dfu-erase.sh --authorized-erase使用外部store/SHA/ldd、唯一设备、Main/Port完整身份检查及独占锁；最多等1800秒，只执行一次正常--erase。不是--no-restore诊断路径。
- 非交互是上游isatty选择，明确授权后不重复等待YES；不加--ignore-errors或额外跳过。恢复开始后不加短timeout强杀，失败后保留日志而非自动重刷。Port接力时上游会清空ECID，过程中不接其他Apple恢复设备。
- 本地DISC可以返回TypecController并伴随host重建，软件dfu exit0也可以没有USB目标；都必须验收实际枚举。当前无设备时不能宣布抹盘已开始，也不能靠反复源码补丁替代正确DFU连接。
- 详细执行记录及原生启动验收要求在experiments/2026-09-13-iokit-ram-root/DFU_ERASE_20260914.md。DONE/exit0不代表系统修好，原生启动未稳定前不再次装实验启动项。

## 恢复工具基线与修改审计（2026-09-14 03:26）

- 正式修复与协议实验必须隔离。默认Nix开发环境现在使用firmware-upstream-tools=pkgs.idevicerestore、原始libirecovery；derivation patches/postPatch为空，已核对store路径、SHA256和ldd。guard版仅14行拒绝检查，diagnostic含guard共64行且链接12行修改的strict库；相同CLI版本号不代表同一代码。修改版仅保留取证，不因DFU到来自动重新运行。
- strict把控制传输长度异常转为IRECV_E_USB_UPLOAD，改变了上游外层容忍PIPE的语义；不是只加日志，可能改变退出结果。不得把strict更早失败直接认定为设备策略拒绝，go/reboot等模式切换命令尤其需要干净对照。此前Recovery goto DFU准备流程实验已撤回，无补丁A/B缺失是方法错误，不能继续叠加协议补丁再解释所有错误为设备问题。
- 上游--no-restore仍可setenv auto-bootfalse/saveenv，直到restored才阻止restore_device；--no-action在Port DFU仍签名并发送端口固件。只读检测使用原始irecovery -q及明确的只读接口，不靠旗标名称猜测副作用。曾读到false并修回true是已确认状态变化，但原初bootloop更早发生，不能全归因于这一变化。
- 用户03:24已允许抹盘，先前禁止Erase属于历史约束；但03:26提出工具审计后暂停上传，尚未执行Erase/完整Restore。若继续完整Restore使用干净工具及外部固定目标核对，不移除所有校验或继续C源码魔改。M1备份、项目、固件资源不得删除；47GiB备份存在不证明完整，Pictures此前未备份，必须事前明确目标盘删除范围。
- 完整审计在experiments/2026-09-13-iokit-ram-root/IDEVICERESTORE_AUDIT_20260914.md；基线构建不是设备恢复成功。03:20 Port超时发生在这些功能补丁命中之前，但无干净A/B不能排除host工具链，不把端口提示当用户插错的证明。

## 最新 guest 实验 pitfall（2026-09-14）

- 03:20新DFU等待器已真实触发并结束：本机Port DFU身份通过、端口ticket成功、Ace3Binary发送并断开，但20秒无主DFU接力，exit1。不要将此前6小时等待进程继续描述为活跃；它只执行一次且已退出。未到iBSS，所以新的post-iBSS KIS探针尚未实测，也不能归因为rpnh/SPTM失败。Port DFU可在不正确的主DFU线口枚举，先核对M4 2025 Air远离MagSafe的口并观察换口后的实际模式，不直接认定用户插错或反复按键/刷写。新监听仅被动、限时1800秒，无上传。

- 备用Recovery失败不能再以相同按键循环或重复完整Revive代替诊断。固定25G83 iBSS的fallback与recover-system共用boot-device、/recovery前置检查及/lpol路径；当前boot-device=nvme_nand0只能排除查询时变量为空，不能验收存储或恢复资源。reason3存在首次错误锁存，且只有一条0x99记录检查setter被解析，旧reason不一定属于最近失败；编号确认为rpnh，不是nsih/coih，两份实际值及native命中分支仍未知。Apple所述RemotePolicy与Find My/Activation Lock策略关联，不能混同DFU Remote boot banner或普通ApNonce；不得因发现rpnh比较而盲清iSC/重放旧nonce或认定关闭SIP可解决。固定iBSS文件offset不是当前nativeStage1在线地址，不直接写入或套用为命中分支。
- lpolrestore在固定iBSS内明确拒绝Local、允许Remote继续；USB PIPE与内部handler返回-3仍是不同层次的证据。已撤回从nativeStage1 Recovery复用DFU准备的goto补丁，最新诊断包拒绝初始Recovery，只允许从核对DFU开始。外层1881 KIS保持连接时，工具等待物理disconnect可能看不到内部模式切换；新增超时后的只读PID/模式/serial查询取证，未直接绕过失败。libirecovery在Linux的set_configuration本来就比较当前配置，不将kisd的重复配置缺陷错误套用给它。
- 05ac:1905 Apple Private NCM不是restored服务或GUI的验收。本轮三次短暂NCM均无法idevice_new，未得到HardwareInfo/SavedDebugInfo；ATCPHY锁失败和xHCI总线重建需与目标日志对照，不能单凭host事件定M4重启根因。有限时udev监听会过期，用户隔很久才操作时应重新读内核日志，不能把旧空监听记录当作操作失败证据。
- 自动DFU诊断使用scripts/wait-for-dfu-diagnostics.sh：Nix procps/util-linux提供进程检查和flock，输出只放ignored raw，新目录、独占锁、固定store路径及工具哈希、一次执行、发现/加载超时、失败不重试。Port DFU必须核对端口ECID后用该ECID开始，主DFU用主ECID；transition后工具原有主ECID/Update/禁止Erase守卫仍必须保留。--no-restore跳过StartRestore和saveenv不等于整个准备零写入，端口固件与RAM加载仍可能发生。不要用nohup命令返回0宣称后台存在：本轮首次nohup未持久，改用真实长运行工具会话并核对PID及watcher日志。

- 原生故障查询应先读iboot-failure-reason/iboot-failure-volume/recovery-boot-mode/panicmedic-engaged/boot-volume。本轮故障上下文为Bootstrap panicmedic、reason0x3；文字原因和计数PIPE，不将码3擅自解释为SSV或签名错误。strict工具实测lpolrestore PIPE，旧库的后续iBEC超时可能掩盖更早的命令传输失败。--no-restore不再saveenv以避免实验失败持久化auto-bootfalse；保留默认工具原行为。fallback字符串和静态handler存在不等于变量可写，本轮两种setter均PIPE且停在保存/重启之前。不得扩大为清全部NVRAM或Erase；需要硬件启动请求时使用被动udev记录，不启动竞争USB配置的kisd。原生fallback GUI不算guest GUI完成。

- 本轮实测getenv必须先于irecv_receive：收控制台会切换USB interface/alt，随后原始查询IO -1；先查则boot-stage/auto-boot等有效。库包装函数忽略USB返回值，状态0加空字符串不等于成功。查询器默认只发送getenv允许列表，原始send/receive字节数须留档；libusb -9 PIPE与libirecovery -9 USB_CONFIGURATION不可混淆。恢复auto-boottrue/saveenv命令已发送不等于持久化验收，必须重连读回；fsboot PIPE后设备消失也不是启动成功证据。禁止以旧签名风险或撤回的锁判断宣称本次bootloop根因已确定。

- DebugUSB故障后拔插同一口可能重新枚举1281 Recovery，不能执意用只识别1881的kisd连接。先核对模式和nonce；本轮初始nonce匹配远程iBSS，但后续加载前和末次查询均变化，不能仅凭第一次匹配断言整次实验为同一Remote boot实例。恢复irecovery连接不等于iBEC可启动；此次补齐Stage1后仍超时，需记录实际控制台和重启时序，不能重复套用旧错误文本。

- 提前监听取得Remote boot iBootStage1控制台，证明本轮iBSS已执行；idevicerestore的Possibly invalid iBSS仅是预期模式切换未完成的推测。kisd源码只匹配05ac:1881，busy不能推出误接普通DFU。与恢复工具同时访问DebugUSB可能占用接口；先保存日志、停止竞争owner，再重连。Nix kisd-preserve-configuration避免配置已为1时重复SET_CONFIGURATION，构建和实测打开设备成功但UART仍I/O协议错误，不能称为修复；停止循环重试，优先拔插同一线重建USB端点再取证。

- Port DFU阶段不能用主芯片ECID作为idevicerestore初始--ecid：发现回调会过滤不同ECID，导致Unable to discover device mode，即使irecovery能查询端口设备。应先核对本机端口ECID，再指定该值；上游端口REMOVE回调会清空ECID以发现主芯片，保留切换后的主ECID/Update守卫。本轮端口切换成功但iBSS后失败，短暂DebugUSB配置返回errno71；该错误不是已证明的线材/host/设备固件根因。下一次枚举前启动单一kisd监听，并对照内核断开时间，避免事后连接错过窗口。

- 原生iBootStage1 Recovery不能假设等同于临时iBSS Recovery。实验性firmware-diagnostic-tools仅对已观察Stage1且--no-restore的macOS目标复用LocalPolicy/固件准备，不自动识别所有Recovery阶段。本轮实际boot-stage=1，但准备后iBEC仍不重连；补丁构建通过不等于实机可用。saveenv已写启动变量，--no-restore只保证不进入restore_device/StartRestore，不保证零写入。失败后重新核对设备身份和模式，不能继续调用restored查询器并把连接失败当成诊断结果。

- 靠MagSafe口也可能显示Apple Port DFU并返回Mac16,12，但不代表主芯片DFU走该口。本轮控制器断开后主DFU20s不重连，工具提示正确DFU口；官方前沿口仍是加载Apple临时恢复环境的必要路径。此前为捕获DebugUSB而换口未成功，不据此宣布硬件连接正常。先不重启，换回前沿口核对主DFU，必要时再按键。

- 备用DFU临时环境加载再次iBSS失败，当前无restored诊断结果。kisd在找到设备前已创建/dev/m1n1，不能以节点存在声明连接成功；只依据日志连接状态和实际协议应答。M4物理DFU前沿口与此前DebugUSB靠MagSafe口须区分；切换调试方案时明确换回调试口，不反复刷写。保留一个kisd等待实例，禁止同时启动第二个。

- --no-restore与--no-action不同：前者可加载临时Apple恢复环境、在restore_device前退出；并不等于所有准备步骤均无启动变量写入。当前从Stage1 Recovery加载iBEC失败，未到restored；不能称为只读诊断成功。新只读restored查询器仅调用QueryType/QueryValue HardwareInfo/SavedDebugInfo，不发送StartRestore，先验证主ECID/CHIP/BORD。Type-C dfu命令exit0后20s仍Recovery，必须验收实际USB模式，不宣称已自动DFU。

- Revive最终DONE/exit0但用户仍无法进入Recovery：必须保留失败验收，不反复以工具成功替代系统成功。AppleTCON日志两次ticket成功但FirmwareData未附加，随后response copy失败；当前源通过DeviceGeneratedTags/ResponseTags决定是否附加，完整request需debug_level>1才能观察。该线索未证实为根因，不得盲目删除判断或扩大刷写范围。

- 第二次非抹盘Revive在iBSS后模式切换失败exit1，Port DFU成功与TSS ticket均不能替代restored/DONE验收。实际出现05ac:1881 Debug USB而非预期DFU/Recovery，irecovery不能连接；先重新进入DFU核对再推进，不按Possibly invalid iBSS报错直接断言镜像错误，更不能自动转Erase。失败前已发送端口固件及iBSS，报告不要写“未发生任何写入”。

- 不要将交互guest launcher通过shell管道接tee：PTY Ctrl-C会终止tee及整组进程，丢失HV Python状态。本轮22780退出130，确认owner不存在后NOP可重连，并只读捕获guest ring；这不等于原HV handler已恢复，不能无状态直接p.exit让guest继续。新增--console-log在同一个进程记录，后续直接PTY执行、不加tee。
- WindowServer进程及framebuffer userclient日志是userspace实质进展，但不是可见GUI。HV.set_bootargs遇-v设置video.display=0，本轮BootArgs读回证实；framebuffer仅两种像素值，没有GUI验收。新增--graphics移除-v，必须另测实际渲染和屏幕画面。

- 原生boot-ramdmg-extents的多个extent拼接为同一个逻辑镜像，不会自动生成多个设备。新增GPT将BaseSystem和Apple_APFS_ISC组合，md0单独保留BaseSystem。RAM预留必须覆盖所有extent实体及HLE aux，不得只保留md0长度；GPT逻辑扇区目前512byte，实际HDIX识别仍须实机验证。sgdisk与分区SHA验证仅证明host镜像格式/字节，不证明guest挂载/图形成功。

- Recovery的diskutil info -plist使用WholeDisk=false，不是Whole；采集器原守卫因此正确拒绝但无法开始，已按现场键名修复，并核对DeviceIdentifier、Content、Internal、大小、model及chosen的ECID/CHIP后才读取。
- iSC已只读采集到M1，apfsutil能识别四个预期卷并不等于原子一致性：live采集的Hardware在线/离线占用不同。保留raw采集哈希与plist证据，继续检查checkpoint；不得直接暴露原ANS或声称guest xART已经可用。iSC含设备安全/启动状态，raw、chosen和相关日志保留在ignored raw目录，不发布。

- 自动Recovery只读检查报告ssv-seal-broken，CustomKC读回和NSIH/coih仍正确，原Data锁定未挂载。不要将回退模式当作新panic根因或数据损坏证明；当前是ordinary/Not Paired，不直接执行kmutil/csrutil。
- BaseSystem和最小stub System实测No snapshots。已撤销按Recovery根哈希拼接snapshot名称的launcher修改；hash不等于snapshot。stock Recovery实际使用root-dmg/imageboot路径，与直接APFS rd=md0根挂载不同，须修复挂载上下文而非伪造snapshot或NOP验证。

- 用户重启后cpus=10对照越过PMGR检查，进入APFS global payload NULL panic；cpus=1在P boot cluster下的失败已由控制变量证据收窄，不直接伪造cluster或删除断言。
- PTY hv.exit可正常使所有guest CPU退出，但后续proxy仍会卡住。All CPUs exited、hv_start返回和退出码0不能代替post-exit NOP验收；本轮USB reset仍失败，须物理重启。
- BaseSystem官方root-hash的208byte payload已与live BaseSystem auth blob逐字节匹配。System与BaseSystem挂载上下文不能混用；snapshot名称由hash推导不等于该snapshot实际存在。新root-auth选项仅离线通过，未实机验收。

- 后续主机 GDB stdin修复失败，Python913527已退出；协议退出918221未获NOP且最后为D状态/TERM已请求，需要物理重启恢复USB。下文暂停PID是历史现场。不要从GDB批处理退出码0推定函数调用成功；SIGSTOP可打断inferior调用，open可能返回0，不能无条件close替换fd。临时stdin bridge已删除，后续直接使用PTY。

- 实际三个 firmware tags 已为 mBoot-18000.161.10，timer 原值写入和读回通过；全局 apple_sysregs_unlocked 仍 false，不要强制解锁全部寄存器。旧 timer fault 是历史状态。
- 完整内存触发 HLE 1024 张页表池断言；16GiB RAM-only 对照进入 XNU 后 ApplePMGR panic。须分别处理页表池/64MiB aux 预算和 CPU-complex 初始化，不能删除断言假称修复。
- guest 启动必须用 PTY；关闭 stdin 会让 panic shell EOF 循环，write_stdin 无法补救。launcher 已拒绝非交互实际启动，prepare-only 不受此限制。
- 当前 panic 保留，主机 Python913527 SIGSTOP 且仍占串口；SIGUSR2退出未确认，禁止启动另一 proxy。后续重新查 PID/串口所有权，不把暂停当作退出。
- 详见 docs/NEW_FIRMWARE_GUEST_EXPERIMENT.md 和对应 STATUS.json；XNU panic 不等于 root/userspace/Linux 成功。

## 目标

在 Asahi M1 控制机上，以纯 Nix、可复现和可恢复的方式调试原版 M4 MacBook Air，并逐步推进 M4 Linux bring-up。

## 固定环境

- 控制机：运行 Asahi Linux 的 M1。
- 目标机：M4 MacBook Air；原装 macOS 曾为26.4.1，现已更新固件到25G83，原生系统/Recovery启动仍待修复。
- 连接：M4远离MagSafe的前沿官方DFU USB-C口，M1 `USB-C Left-back`；此前靠MagSafe口用于DebugUSB对照，不混淆两种用途。
- M4 DebugUSB：`t8132`，base `0x3c8000000`。
- Linux 入口：`/dev/m1n1`，由 `kisd` 创建并指向 PTY。

## 标准连接动作

1. 在 M1 项目目录中启动：
   ```sh
   sudo nix develop --command kisd --base 0x3c8000000
   ```
2. 另一个终端执行：
   ```sh
   sudo nix develop --command \
     tuxvdmtool --connector 'Left-back' reboot debugusb
   ```
3. 检查节点（仅表示PTY已创建，还需kisd Device opened和实际协议/控制台应答验收）：
   ```sh
   readlink -f /dev/m1n1
   ls -l /dev/m1n1
   ```
4. 后续 m1n1/proxyclient 命令统一使用 `M1N1DEVICE=/dev/m1n1`。

## 必须遵守的 Pitfall

- 不使用会重置 Nix 环境 `PATH` 的嵌套 `bash -lc`；组合命令使用 `bash -c` 或绝对路径。
- `kisd` 必须先启动，否则不能判断 DebugUSB 是否真正建立。
- `/dev/ttySAC0` 是 M1 本机串口，不是 M4 接口。
- `cdc_ncm` 代表普通 USB 网络模式；`/dev/m1n1`存在只代表kisd创建PTY，不代表已接管DebugUSB。
- 连接测试允许重启和切换模式，但禁止未经单独确认的 DFU 恢复、刷写、Preboot/NVRAM/启动策略修改。
- 每次实验记录目标 macOS/firmware 版本，不能只记录机型名称。

## 持续更新规则

- 每次硬件测试后，先把“命令、原始输出、成功判据、失败原因”写入 `docs/DEBUG_WORKFLOW.md` 或实验目录，再更新本 Skill 的稳定规则。
- 暂时性猜测放入 `docs/RESEARCH_LOG.md`，不要直接写成 Skill 事实。
- 新增工具或命令必须进入 `flake.nix`，避免依赖控制机全局安装。
- m1n1、Rust target、rust-src 和 Cargo git/registry 依赖必须通过 flake 锁定；禁止用未记录的 `rustup target add` 或用户目录 Cargo cache 作为构建前提。
- payload 构建、目标机启动配置安装和首次 chainload 必须分成三个实验阶段；前一阶段成功不能推断后一阶段成功。
- 已安装的 m1n1 原生 USB proxy 与 DebugUSB 不同：2026-09-13 在 J713/T8132 上实测 USB 1209:316d，生成 ttyACM0 和 ttyACM1，UART NOP 和 proxy NOP 均成功。原生 proxy 使用实际枚举的 ttyACM 设备，不使用失效的 /dev/m1n1 PTY 链接。
- 恢复 SSH 使用控制机当前 id_ed25519；临时公钥文件放在 /tmp 时，已实测 StrictModes 会因父目录权限拒绝认证，临时服务需要 StrictModes=no。HTTP 目录不能暴露控制机私钥，只提供临时 host key 和登录公钥。
- kmutil configure-boot 需要配对的 1TR；Full Security 下会报必须先进入 Reduced Security。已实测 bputil -g 后 kmutil 成功安装并进入 Permissive Security。目标卷必须明确区分正常 macOS 与独立实验卷。
- 备份必须从 M4 经 SSH 拉取到 M1 的 /home/sequencer/liqi_backup；在 M4 同盘创建副本不能代替独立备份。
- 发现新的失败模式时，添加一个最小复现命令和一个安全回滚/停止条件。
- macOS 与 m1n1 必须有独立的可认证启动卷组。2026-09-13 已为新系统创建 64GB M4 Linux Bootstrap 空卷；创建 APFS 容器不等于安装完成。M4 上游 Asahi 安装器无设备支持，不能仅用 EXPERT 绕过，也不能直接复制旧 LocalPolicy。
- 恢复原 macOS 策略已实测 bputil -f 成功，Full Security 且 coih absent；这仅验证策略恢复，正常 macOS 还须实际重启验收。
- 后续用户要求直接关闭 SIP，已在同一配对 Recovery 执行 csrutil disable 成功。当前旧卷策略为 Permissive，SIP disabled，Kernel CTRR 和 Boot Args Filtering disabled，coih absent；此前 Full Security 仅是历史状态。SSV 和 FileVault 仍启用，新卷策略必须独立配置。
- 任何改变目标机持久状态的动作都必须单独标注风险，并在执行前再次确认。
- 用户已授权在独立实验容器中实验性安装最小 stub，不执行第二套完整 macOS 安装。已生成约 4GB stub，创建新 LocalPolicy 并设置默认启动；原数据容器保持 256GB。当前卡点是 kmutil 的 code pairing (17)，须进入新 stub 配对 1TR 后继续，不能报告 m1n1 已安装成功。
- 磁盘标识不要只按表格序号推断：实验分区实际为 disk0s5，容器 disk6；挂载 Preboot 和 Recovery 重名时实际路径带“ 1”，须从 diskutil info -plist 获取。
- 目标原系统实际读到 26.6.2/25G83，现有恢复资源为 26.4.1/25E253；分别记录版本，不混用同名 firmware。
- 用户无法在 Recovery 粘贴长命令：提供 scripts/recovery-ssh.sh，经 M1 的 HTTP 服务发布为 /ssh.sh，用 curl 下载到 /tmp 后执行。脚本从 https://github.com/sequencer.keys 下载公钥，在目标本地生成临时 host key，前台启动公钥认证 sshd；不重启、不改启动策略、不删除数据。新 host key 必须核对指纹，不能沿用旧 Recovery 主机身份。
- 用户实测此 Recovery 不存在 /usr/bin/ssh-keygen；上述脚本已改为从 M1 HTTP 下载临时 host key，不再生成或调用 ssh-keygen。不要假定 Recovery 提供完整 macOS 命令集。此 host key 仅用于局域网临时 Recovery SSH，不用于长期服务。
- 2026-09-13T16:23:00Z 独立约 4GB stub 完成配对和 kmutil 安装，已实际重启进入 m1n1 EL2；新卷 SIP disabled、Permissive、coih 非空，原生 /dev/ttyACM0 的 UART 和 proxy NOP 成功。此前 code pairing (17) 已通过进入新配对 1TR 解决。Linux 尚未启动，MCC/cpufreq 仍报不支持。
- BSD disk 编号会在重启后改变，本次实验容器由 disk6 变 disk1，实验分区由 disk0s5 变 disk0s3。后续只能按容器 UUID 和卷组 UUID 重新定位，禁止沿用日志中的编号；初次准备脚本固定断言拒绝新现场是安全停止，不应盲目删除断言后重跑。
- 2026-09-13T16:26:04Z M4 实机 HV.init 成功，apple_sysregs_unlocked false，初始化后 UART/proxy NOP 成功；尚未加载 XNU 或执行 hv_sptm_init，不能报告 macOS guest 已启动。stub 的 boot-uuid 是新空卷，macOS guest 必须明确根卷、匹配版本和符号，不能默认使用它启动原系统。
- SPTM guest 资产现在已拉到 M1：匹配 25E253 和 25G83 的 kernelcache 及 25E253 Recovery 原始虚拟磁盘。pyimg4 因 asn1 >=3 被 Nix 标记 broken，改用 Nix lzfse 加严格 IM4P DER 抽取；两版必需符号离线检查通过。初次 guest 使用匹配 Recovery RAM root，并删除 guest ans 节点，不让实验默认挂载原用户 Data。
- 删除 guest ans 后，原 PR 的 SPTM 平台初始化会无条件读取不存在的节点，引发 ADT BadOffset/unwrap panic。已在 Nix postPatch 加缺失 ANS/SART 节点提前返回，并成功 RAM chainload 本地构建 779c9ac3c696210dcbd54c06f1353aa35f095cbd2a899a7da8a7ceacd5a6f2b4。原持久化构建未更换，重启回原始版；是否完成 XNU 启动必须检查第二次 guest 日志，不能把 chainload 成功混称 guest 成功。
- 第二次 SPTM guest 的 hv_sptm_init 成功返回并调用 guest entry，但 hv_update_fiq 写 VM_TMR_FIQ_ENA_EL2 时发生 EL2 异常；故障 PC 相对 0x163b8，指令 d51df160。优先核实后文的固件解锁前提，只有必须支持旧固件时才研究完整 timer/FIQ 替代实现；不能用进一步关闭 SIP 或简单删 timer 逻辑假称修复。未验证 macOS UI/启动完成。自动重启后原始 stub proxy 的双 NOP 再次通过，留存全部原始失败日志。
## 固件更新 pitfall：SFR 与 per-OS 启动资源

最新现场：25G83 one true recoveryOS / Paired 启动已验收，csrutil disable 明确选择实验 stub 并成功，kmutil configure-boot 安装 optional-ANS raw payload 成功（entry=2048、VA=0）。新 coih=3C1819488DC4CF8762CFEA1F5777CF14D07BE427BFD2D10D7A17B638BC91FCC5AB4FF88630E2FAE753279CC9B9AF5A7A，Permissive/sip0=7f/CTRR与BootArgsFilteringDisabled。Preboot实际CustomKC读回含唯一raw payload，逐字节/哈希匹配Nix构建；原Data仍Locked未挂载。现在coih不再为空，可正常重启实验stub。尚未自动重启，不把安装成功当作USBproxy/timer/guest启动成功。资源安装阶段旧journal不是当前策略状态，最新STATUS.json已更新。

最新复测：恢复旧 cache symlink 后，25E253 配对 1TR 实际启动成功；bputil -g 随后重建 25G83 love/NSIH/cache，退出码0。当前旧 Recovery 立即由 Paired 变 Not Paired，必须再进入新 25G83 配对 1TR，不能缓存之前的 Paired 判定继续安装。bputil -g 重置安全选项，现场暂为 Reduced/SIP Enabled/coih absent；不要正常启动最小 stub，也不要声称 optional-ANS已安装，需新版配对 Recovery 中 csrutil disable + kmutil。新旧Recovery link已分别核对指向新旧镜像，旧镜像仍保留，原Data未挂载。

SSH 后实测 SFR 已为 25G83，当前 Recovery 为 ordinary / Not Paired。原 Data 仍 Locked、未挂载、UUID/已用字节数相同，不等于内容完整校验。捕获 panic 的内层是旧 Darwin 25.4.0，直接错误 could not validate root hash Authentication error (80)；外层报告的 25G83 是收集日志的 Recovery 版本。旧 cache 的 BaseSystem 是相对 symlink，替换 canonical 镜像会让旧 cache 同时改指新镜像，即使目录/NSIH未改；此前“缓存未动所以安全”判断错误。已按 UUID/hash 校验后将旧 cache link 改指保留的 25E253 镜像，旧 SHA 与 M1 备份一致，原链接保留；未来 apply 脚本也已修正。APFS mount -ur 失败发生在修改后，不能盲目重跑；unmount + mount readOnly 后读回成功。启动仍待复测，不能说全部 boot loop 已修复。详见 docs/FIRMWARE_UPDATE.md。

普通 Recovery 不可进入时先尝试 Fallback recoveryOS 的 tap-release-press-and-hold 电源手势（完全关机后短按松开，再立即第二次按住）。官方 Apple boot modes 与 Asahi cheatsheet 已核对；不要与普通单次长按、DFU 四键混用，不假定 fallback 是 stub 配对 1TR。若也失败，回到 DFU 诊断，绝不自动 erase/reflash。

revive 返回 DONE 后用户报告启动循环/失败，正常启动尚未验收。M1 只读查询暂未见 DFU/Recovery USB。优先关机进入 Options/Recovery，只读采集；不要把 AppleTCON -1 直接当作根因，不把清理 NVRAM/修改 boot command 推测当作事实结论，不自动重复 revive、急救、重装或 erase。须先检查实际 SFR、启动卷/策略与失败画面再选择修复路径。

2026-09-13 18:24:13 UTC 非抹盘 DFU revive 已返回 Restore Finished / DONE，退出码 0。Port DFU ECID 0x3fc75d711905dde9 转换后主芯片 0xA10A426B9001C 验证通过，本地 Nix patch 已加入主芯片 ECID 硬性检查。完整日志另含 AppleTCON response checkpoint -1 和一次 Ace3 ticket 缺失；总体成功不等于每个设备都成功，禁止自动 erase/reflash。恢复后旧 SSH 地址不可达，必须重建 Recovery SSH，重新核验持久化 SFR、原 Data、卷 UUID 和配对策略；此后才能 bputil / kmutil。下面的 SFR=25E253、策略未变和 Data Locked 是 revive 前现场，不是恢复后新测。

DFU 口纠正：Apple 官方表明确规定 2025+ MacBook Air 使用面对机器左侧时最右侧 USB-C 口，即远离 MagSafe、靠近前沿的口。此前给用户的“靠近 MagSafe”是错误 DFU 指引，已在 docs/FIRMWARE_UPDATE.md 修正。debug USB 曾经可用不证明该口可用于 DFU。用户尝试失败后，M1 lsusb 仅见 1209:316d m1n1 uartproxy，未见 Apple DFU；Recovery SSH 超时。不能据此说 DFU 或固件升级成功。

2026-09-13 已将完整 25G83 资源安装到独立 stub，M1 上 System/Preboot/Recovery 三份 tar 校验通过，旧资源和旧 NSIH 缓存保留。bputil -g 通过认证后以 BYErrorDomain 105 / SFRUpdateRequired 拒绝：全机 SFR 实测仍是 25E253，目标要求 25G83；策略、NSIH、coih 未变。boot.bin 已换 optional-ANS，不代表 kmutil 安装完成。原 256GB Data 仍 FileVault Locked、未挂载。详见 docs/FIRMWARE_UPDATE.md；不得声称实际固件或 guest 已升级成功，不重复运行有旧版本/备份防重入检查的 apply 脚本。

Bootability 的真实 IPSW 前缀是 BootabilityBundle/Restore/Bootability/，原 58 个核心资源提取不包含这个 bundle。prepare-stub-firmware.py 已补齐 framework symlink/执行权限、trustcache、通用 apticket 与 PlatformSupport；不要混淆核心资源集合与完整可用 restore 集合。Recovery /tmp 仅有 2.5GB tmpfs，不能把整个更新包多份展开到 RAM；大 DMG 应在 Recovery 卷同卷暂存和原子改名。

SFR 更新候选是非抹盘 DFU revive；Nix 版 firmware-revive-tools 已加拒绝 FLAG_ERASE / 非 Update 主 identity 的保护，并构建成功。DFU 必须指定本台 ECID 和完整 IPSW 的 Customer Upgrade Install (IPSW)，不能以 stub 的 macOS Customer/Erase identity 为 DFU 主身份；不得追加 --erase、--no-input 或失败后自动 erase。尚未现场 DFU 更新验收，Linux 第三方实现不等于 Apple 官方 macOS host。进入 DFU 需要用户物理按键，SSH 会断开；不要远端普通 reboot 冒充进入 DFU，不手工覆盖 iSC/SFR/全局 Recovery。

## 内核资产的可复现要求

Apple 26.6.2/25G83 下载与提取统一使用 `scripts/download-apple-boot-resources.sh`，详情见 `docs/APPLE_BOOT_RESOURCES.md`。官方 URL、SHA-256 和 Apple 目录快照固定在 Nix 中；不要把已开始下载称作完整资产。CDN 缺少 Accept-Ranges 会让 ipsw 的 remote 探测失败，即使实际 Range GET 返回 206；使用 aria2 整包下载并离线提取。aria2 的 Nix 二进制在 `.#apple-download-tools^bin`。AEA BaseSystem 不能直接当 raw 根盘，下载新固件不等于更新或解锁本台的实际 boot firmware。

2026-09-13 官方 25G83 整包和 58 个 J713 资源校验已完成；SPTM/TXM/DeviceTree 裸 payload 和内核另存 derived/，内核与目标原系统旧保存件字节一致。Apple FCS 域名在本机普通 DNS 失败，用 HTTPS DoH 解析且保持 Apple TLS 校验后下载成功；PEM 已固定 Nix 哈希，BaseSystem 纯 Go 解密成功，但仍是 UDIF DMG，不是可启动的 raw RAM root。验收清单见 `experiments/2026-09-13-apple-25G83/`，不能把资产准备完成混称 guest/固件更新成功。

核查 docs/KERNEL_REPRODUCIBILITY.md 和 experiments/2026-09-13-sptm-macos/SHA256SUMS。启动实验前先从项目根目录校验全部资产；不得把 raw/ 中被 Git 忽略的文件称为已提交或已备份。更换输入必须另建版本/哈希记录，不能覆盖旧实验输入。区分持久化原始 PR m1n1 与 flake.nix 本地补丁构建；Nix 构建不会自动更新目标启动对象。

## SPTM/macOS 研究后的实验前提

- 原生IOKit RAM镜像已实机把失败推进到iSC/xART，不能继续只改boot UUID：mount-phase-1需iSC分区类型69646961-6700-11AA-AA11-00306543ECAC的xART节点，role5是用户工具内部枚举，对应APFS role0x100，不直接拿5当diskutil role。十次wait_for_node重试后该项失败fatal；Preboot/Update缺失是忽略项。后续应只读采集本台iSC并离线验证后RAM呈现，保持原ANS不暴露，不用M1的iSC冒充M4，也不把live raw复制当作已经一致性验收的快照。
- APFS启动工具可用Nix apfs-fuse在M1只读挂载固定Recovery raw提取；内部根目录在mountpoint/root，不是mountpoint本身。ipsw disass会默认写旁边.a2s，RO挂载上必须指定--cache到raw可写目录。分析后复制二进制到raw并卸载临时FUSE，避免git递归遍历整个BaseSystem。native RAM media候选输入仍为固定Recovery根盘，没有写原Data。

- --ram-root-boot-uuid实机阴性：mount-phase-1仍SIGABRT，lookup_boot_device这次明确查找E93D361D...并ENOENT。因此不能把boot UUID对齐当作解决；md0直接VFS挂载没有可发现的AppleAPFSVolume服务。下一候选--iokit-ram-root：在load_macho地址调整之后为guest chosen添加boot-ramdmg-size=<Q size>、boot-ramdmg-extents=<QQ guest-physical-address,size>，让原生IOFindBSDRoot调用di_root_ramfile发布真实RAM IOMemoryDescriptor，绝不伪造IOMedia/APFS服务。25G83实证要求OSData size8、extents非空且16字节倍数；该候选尚未实机验收，原md0和分类adapter仍保留用于对照。
- Nix postPatch已修复proxy panic选项解码：XNU_PANIC事件中32位小值x0视为options，使用x2/x3；修正非零options=0x2000漏判。新results/m1n1-panic-tools构建成功，m1n1.bin仍为779c9a...，仅host Python改变，不需要重新configure-boot。新增guest_diagnostics.py仅在已固定KC哈希下只读保存panic上下文和console ring，捕获失败不阻塞shell；ring输出标记raw order，不假称跨wrap时间序已重建。

- BaseSystem分类adapter已实机命中并恢复原指令，NX virtual/already_rooted写后读回为1。16GiB/10核guest到达launchd、BaseSystem environment starting、mount/apfs_boot_util；新panic为mount-phase-1 SIGABRT，因chosen.boot_uuid仍是磁盘Bootstrap UUID，而ANS已移除，lookup_boot_device ENOENT。25G83 RAM根卷UUID E93D361D-43AC-47A0-8DDA-A5D235BACC77已在live APFS superblock+0xf0确认。--ram-root-boot-uuid仅修改guest ADT，不改host NVRAM，不把RAM根卷冒充存在Preboot/Data；此选项尚待下一轮验收。
- 新userspace panic来自panic_with_options，context x0=options、x1=caller、x2=format、x3=va_list；旧decode_panic_call假设x0=format导致AssertionError，不表示guest字符串不可读。手动xnutools.decode_panic(hv.u,ctx.regs[2],ctx.regs[3])成功。25G83 console ring writer反汇编给出header VA0xfffffe000c638320，32字节<QIIIIQ>，buffer大小16384；只读dump证明launchd和mount失败，不在panic中执行guest函数或修改文件。

- 2026-09-13用户物理长按后实机为one true recoveryOS/Paired/Pairing Integrity Valid；同一bputil -s -v Bootstrap UUID命令成功退出0，SSV Disabled/sip1=1，coih/nsih原样保留，lpnh变为76A879...。原安装SSV仍Enabled、Data仍Locked/unmounted。该动作修正Bootstrap策略，是否消除自动回退必须用普通重启和guest退出后的重启分别验收，不能仅凭命令成功宣称解决。

- 自动回退 Recovery 中 `bputil -s -v <Bootstrap UUID>` 的2026-09-13实测：所有者认证通过，退出255、Failed to disable Signed System Volume:11；统一日志准确解释为 AP boot mode (11)，不是密码错误。策略读回 sip1 absent/SSV Enabled、nsih/coih 未变。必须正常关机后由用户物理长按进入1TR，再验收配对身份。不要使用 bputil -n/-g 重建策略来绕过该错误，它们可能丢失CustomKC等标签。SSV关闭只针对Bootstrap，不能误操作原FileVault安装。
- 同次 fsck_apfs result=65 的完整上下文是 container mounted with write access; please re-run with -l，不能作为Data损坏证据。当前ResetCounter为reset count=1、boot failure count=0、target_off_restart，与前次boot failure count=1不同，不能复用旧计数解释新回退。

- 从暂停的 guest panic 发出 m1n1 P_REBOOT 可触发实际 watchdog 重启，但2026-09-13实测再次回到原生 Recovery，不能把它当作可自动返回 m1n1 的 reset 方法。用户已确认回退；先采集 Recovery 日志并明确选择 M4 Linux Bootstrap，不循环 reset、不自动清 NVRAM 或修改启动策略。--direct-basesystem-root 分类适配仅实现并通过语法检查，尚未实机验收。

- 25G83 APFS 单次 BRK 检查必须校验 KC SHA 和原指令，命中后恢复指令及缓存。ExcInfo 使用 `sp[0..2]`，EL1t 活动栈在 sp[0]；不存在 sp_el1 属性，regs[31] 也不是活动 SP。当前直接 md0 路径 NX 虚拟标记为0且设备为空，_nx_is_virtual 返回 false；仅设置 already_rooted=1 的实机实验仍 panic。所有私有偏移仅适用于已校验的25G83，不跨版本套用。失败挂载不能回退重演；下一轮需要全新 guest。

- 2026-09-13 对齐 root 已实机准备：25G83 UDIF 转 GPT 后复制唯一 APFS 分区，原 offset 0x4400；新 root 大小 1574961152，SHA-256 bda0c53dfb35ceffe371c1708b2443b9d55f60a70bbcbbcf6470bade2b552e9a。root 位于 guest 物理范围内的 16KiB 对齐地址，并抬高实际 BootArgs 保留边界，在其后规划 64MiB HLE aux；superblock、BootArgs 和最终 ADT 实机读回通过，ANS 删除，proxy 双 NOP 成功。并未启动 guest。详见 docs/ALIGNED_RECOVERY_ROOT.md，地址不能跨重启复用。
- timer 写前提已直接受保护复测：GUARD.SKIP 下 MRS 成功为0xf，但原值 MSR 仍异常；清除保护后 proxy 正常，没有自动重启。新 launcher 启动门槛已拒绝这一现场。live 三个 boot firmware tag 仍为 mBoot-18000.101.7；对齐根盘不会解锁寄存器。先进入配对 Recovery 更新并验收完整启动资源链，不通过跳过 hv_update_fiq 假称 macOS 成功。
- 新 launcher 要求内核 SHA-256、root manifest 和新输出路径；--prepare-only 只上传 RAM 并读回验证，非 prepare-only 会先执行 timer 同值写探测。它不会自动替换持久化 m1n1，仍需 optional-ANS 构建。每次只有一个进程占用 proxy，禁止并行运行上传与 preflight/shell。

- 先阅读 docs/SPTM_MACOS_RESEARCH.md。区分 PR #1 的 SPTM HLE 与 PR #643 的 SPRR/GXF 模拟；后者不自动包含完整 Apple SPTM/TXM loader 或本台 M4 的已验收路径。
- VM_TMR_FIQ_ENA_EL2 的读写能力应单独验收。当前已定位的是读后 msr fault；IRC 的 26.6 beta 解锁报告是候选固件前提，不是本台复测。不得把 apple_sysregs_unlocked=false 当作每个 Apple 寄存器都不可写，也不得强制把 M4 全局标为 unlocked。
- 新 guest KC 或 RAM chainload 不能重演 boot firmware 解锁。固件资源与实际执行的 stage tag 分别记录，不混填旧 restore；当前初始日志为 26.4/mBoot-18000.101.7，原裸 SystemVersion 的 25G83 不证明 stub 使用它。
- RAM root 必须具有 guest stage-1 可见性和保留边界；stage-2 映射不是完整映射。当前 launcher 的 host-heap RAMDisk 不在 HLE physmap 中，不能当作可用根盘继续重复启动。
- whole-GPT raw、APFS partition 和 UDIF 是不同输入。使用 scripts/inspect-recovery-input.py 离线核对；提取 root 产物另存并记录 offset/length/hash，不覆盖原始资产。当前分区 offset 0x4400，不能只把 RAMDisk 指针加此值：XNU memdev 的 >>12 会截断未对齐地址，需复制到对齐的新保留区域。
- 以 Darwin banner、VM bootstrap、root mount、launchd、shell 分阶段验收；不把 Recovery shell、Recovery UI 与完整 macOS 桌面混称。旧固件 timer fallback 未验证，禁止靠跳过 FIQ routing 掩盖问题。
