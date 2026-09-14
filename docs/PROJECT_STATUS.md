# M4 Linux 项目状态

最后更新：2026-09-14

## 最新实机状态

2026-09-14 10:57 UTC：新布局的 m1n1 持久化安装及实际重启验收已通过。用户完成 128GB macOS 安装并创建 sequencer 卷所有者，系统/数据卷恢复默认 Macintosh HD 命名；原生系统仍 Full Security。独立 4GB stub 在配对 1TR 中完成 csrutil、kmutil 和 bputil -s，策略为 Permissive、SIP customized 7f、SSV disabled。重启后 USB 1209:316d 枚举，Mac16,12/J713/EL2，UART NOP 和 proxy NOP 均通过。当前为 Running proxy；尚未启动 Linux 或验证新的 SPTM guest。剩余约 1.9TB 为空闲空间，不是已格式化 Linux 分区。详细固定 UUID、哈希、策略和坑点见 M1N1_RESUME_20260914.md。以下为历史状态，不代表当前布局或阻塞。

2026-09-14 Linux-only 分区及 stub 文件准备已完成：4 GB APFS stub、1 GB EFI、1990083952640 字节 Linux GPT 分区（尚未格式化），原 iSC/System Recovery 保留。25G83 资源经逐文件哈希验证，固定 m1n1 已放到新 System/m1n1/boot.bin。用户澄清 Restore 后未配置/创建账号；新卷 bputil -g 实测退出 8：no admin users authorized for recovery，无法建立 ACM context。尚未关闭 SIP、没有有效新 LocalPolicy、未完成 kmutil、未重启。详见 LINUX_ONLY_20260914.md；以下为历史记录。

2026-09-14用户明确要求直接移除现有macOS容器，已通过Recovery root SSH执行`diskutil apfs deleteContainer disk3`，正常exit0。执行前核对Mac16,12/主ECID、目标物理分区UUID561BD502-558F-48EA-A915-92CBDF35ECC0、容器UUID C97410CD-F973-4282-8E6F-85A9C0970B21及1995218165760字节大小；删除包含System/Data/Preboot/配对Recovery/Update/VM的整个日常macOS容器，空间现为约2TB未分配。当前运行的Recovery来自ramfile镜像，删除后SSH重连成功。iSC disk0s1（524288000字节、UUID3DEC5A4D-2326-42C9-BA96-11F889C3C9E6）及System Recovery disk0s3（5368664064字节、UUID BFF7DCE8-D66B-43D1-8E06-40B23050FF5C）删除前后UUID/大小一致。原macOS已不存在；尚未新建Linux分区或可启动m1n1 stub，不把释放空间称Linux安装完成。继续保持当前Recovery会话，后续从未分配空间构建调试布局；M1资源未删除。日志raw/remove-macos-20260914/{delete,verify}.log，分别SHA256 f6560e10666915c4cf4e08bcc30988b8934e4405ea7a49429921f9fea2131e4c、94696cdea17db0ba50dd0d1e7be3ef6976c4c1c286f02f7777909c7a87f416be。

2026-09-14 Recovery SSH重连成功：从本机HTTP日志识别下载来源172.24.5.124，使用root、公钥id_ed25519及已知临时hostkey校验登录。M1 HTTP现为172.24.5.185:8000；Recovery为26.6.2/25G83，Mac16,12，主ECID0xA10A426B9001C/CPID8132/BDID2c匹配。bputil只读显示one true recoveryOS、Paired、Pairing Integrity Valid，Full Security/SIP Enabled/coih absent。新disk0布局为524.3MB iSC、1995218165760字节macOS APFS物理分区disk0s2（容器disk3，约24.5GB已用）、5.4GB System Recovery；旧Linux Bootstrap已不在分区列表。新APFS容器UUID C97410CD-F973-4282-8E6F-85A9C0970B21，卷组UUID 7614465E-E21A-43A3-AA98-88FB69F01EAD。本轮仅SSH登录与只读身份/分区/策略检查，没有缩容、删除或修改启动策略；后续Linux工作从此新基线开始。

2026-09-14用户确认全盘Restore后已进入正常macOS桌面，原生桌面启动恢复成功；独立正常重启验收尚未记录。用户要求之后只关注Linux并允许彻底删除M4日常macOS。记录该目标/授权，但当前没有本机Linux独立启动验收，删除macOS不自动产生可用Linux；必须区分日常macOS卷与iSC/System Recovery/实验启动stub所需Apple启动组件。后续先重新连接恢复后的系统、核对新分区/身份/固件基线，再实施Linux引导及空间迁移。此前恢复前的磁盘标识不可复用，M1备份/项目不在删除范围。本轮未删除分区。

2026-09-14最新更正及结果：用户澄清此前换口后完成的是Revive（修复），之后仍无限重启；随后改用Restore（抹盘恢复），现明确确认“现在抹盘恢复完成”。记录为用户确认全盘Restore完成，新的原生启动结果尚待反馈。此前把Revive后的bootloop写成“官方完整抹盘后仍重启”的判断已撤回，不能据此提高硬件故障结论。下一步验收设置助理/激活、正常桌面及正常重启，再恢复实验工作；此次完成日志尚未取得，旧4042文件仍只代表最早失败。M1备份和项目资源保留。下方有关完整Restore后bootloop的文字为已被用户纠正的历史判断。

2026-09-14用户最新明确确认：换至M4远离MagSafe的接口、普通数据线、Finder Restore已完成，但M4仍无限重启。当前结论为用户确认官方恢复完成，原生启动修复失败；不是仍在等待固件更新。换口后完成日志尚未取得，现有Downloads/MacUpdater.log仍为换口前4042记录，不能用于说明新恢复的最终状态或启动错误。后续优先获取这次完成的MacUpdater日志及恢复后的panic/iBoot启动证据；不能再把接口问题解释成全部bootloop根因，不能把恢复前Bootstrap卷UUID/rpnh候选直接套用到恢复后实例。官方完整恢复后仍重启提高硬件/固件启动故障调查优先级，但尚不足以判SSD/主板损坏。当前M1没有Apple USB目标和恢复进程；本轮不重复刷机或修改启动配置。

2026-09-14最新用户反馈：Finder Restore、普通数据线原先报4042；更换M4端到远离MagSafe的Type-C口后，“正在等待更新固件”。记录为正确DFU口下恢复流程有进展，尚未验收完成/原生启动。换口前MacUpdater.log已完整解析并私有raw留档：25G83、端口ECID匹配，日志本地16:27:27 Port阶段成功并断开，16:37:27等足10分钟仍未接受主DFU接力，4042/elapsed603秒，无主ECID/iBSS/iBEC/restored/StartRestore。不同于M1主DFU已通过后的iBSS超时；不能因阶段Update反驳用户明确Finder Restore。接口选择现为优先实机线索，不再盲刷/改协议；等待Finder完成和原生设置/桌面验收。本轮无本地恢复/USB操作，旧04:17监听已过期。详见experiments/2026-09-13-iokit-ram-root/MACUPDATER_20260914.md。

2026-09-14 04:24–04:30 UTC用户询问修复思路，本轮仅只读检查/源码与上游研究，无第五次上传、VDM或M1重启，仍无Apple USB目标。新增docs/DFU_REPAIR_PLAN_20260914.md：区分native panicmedic与DFU iBSS切换故障；纯Nix优先实际验收M4远MagSafe DFU口/普通数据线并增加usbmon，M1内核支持模块且模块存在、尚未加载/抓包。标准初始Recovery直接iBEC入口可避开iBSS，但不会补DFU Stage1 LPOL/固件准备，本M4未验证、Local Stage1不能默认接受。以修好为优先的备选是macOS14+ Finder完整Restore；M1仍有57.7G APFS/Recovery分区不证明可启动完整macOS，不擅自重启/抹host。GitHub HEAD均与固定工具源一致；#737实际提议3→4分钟且未合并，当前master5分钟是不同于iBSS10秒的阶段；#165仅macOS IOKit。KIS boot-img回复校验是可取证候选而非确证根因，不立即源码patch。被动USB1168840于04:28仍在，Erase等待与恢复已结束。

2026-09-14 04:20–04:22 UTC用户确认进入后，matched-1已真实执行第四次干净Erase尝试：04:20:48 Port身份核对，04:20:52主ECID0xA10A426B9001C以DFU接力；明确Customer Erase Install、原cache、一次debug、真实PTY（工具fd0/fd1均/dev/pts/9），04:21:10输入已授权YES。组件检查/TSS通过，04:21:13.858发送1363655字节iBSS，04:21:23.914仍10秒未断开，04:21:24 exit1，等待器30994/1168847与恢复进程均结束，无自动重试。没有iBEC/restored/StartRestore/RestoreFinished，未完成SSD抹除或原生修复。被动USB确认Port f014→1881，内核到04:21:55.481才实际断开；04:21:55原始只读查询exit255/Unable to connect，04:22:20无Apple目标，不能验收本次iBSS执行或Recovery内部模式。该结果否定“补回variant/cache/一次debug/TTY即可修好”的充分性，不证明镜像损坏、M1不支持或设备硬件故障。仅被动USB记录1168840仍在，M1备份目录存在但不代表完整。日志/哈希及边界见DFU_ERASE_20260914.md与RESTORE_COMMAND_AUDIT_20260914.md。

2026-09-14 04:17 UTC用户要求再次重试，脚本新增matched-tty调用包装，未改idevicerestore/libirecovery源码：单debug、显式Erase variant、原cache、真实子进程PTY；default diagnostic参数保留。语法/diff、非法profile/非TTY拒绝以及离线子进程stdin/stdout TTY测试通过。等待器session30994/PID1168847于04:17:01启动，最多至04:47:01，raw/dfu-erase-20260914-matched-1；被动USB46167/1168840保存实际PRODUCT事件。旧1881原始查询失败后当前无Apple目标，04:17:11等待器存活、尚无第四次上传；已提示键盘DFU，不能称为抹盘正在刷写或修复完成。详见RESTORE_COMMAND_AUDIT_20260914.md。

2026-09-14 03:56–04:00 UTC用户要求核查命令、指出同一M1曾成功DFU。已冻结上传并从sudo journal取得真实成功argv：端口ECID相同，显式Upgrade variant/cache、一次debug、真实TTY；当前Erase选中正确identity、同固定源/原始库/IPSW，但profile未完全复刻。重要纠正：成功一次debug不会打开libirecovery日志，无KIS字样不能证明普通DFU；只确认旧iBSS后有实际USB断开并进入Recovery。22:10同variant/cache/TTY也曾同样超时，不能直接认定漏参数为根因。离线Manifest验证两identity的iBSS/iBEC全entry相等、OS ZIP_STORED；仍不保证个性化签名相同。第三次clean-3-dfu03:54:47已尝试、03:55:05同iBSS超时exit1，无StartRestore/抹盘完成；当前无恢复/等待/调试进程。详见RESTORE_COMMAND_AUDIT_20260914.md，已记待验证的对齐profile，不再默认以换主机或反复按键代替核查。

2026-09-14 03:49–03:51 UTC重新插拔并再次键盘进入后，clean-2已真实执行同一无补丁Erase尝试：Port与主身份/Erase identity/TSS成功，03:49:40 iBSS发送，03:49:50同一10秒断开超时exit1，仍未到iBEC/restored/StartRestore，没有完成全固件重刷或SSD抹除。等待器54816/1150179已结束，不再存活。后续原始kisd配置errno71，25秒控制台0字节；03:51:27用户中断后停止本次PID1156742，无恢复/调试残留。用户只确认重新插拔，未确认换线；不将重复KIS或配置错误直接定为根因，不再要求不变条件下盲刷。详细DFU_ERASE_20260914.md。

2026-09-14 03:47 UTC用户确认重新插拔，M1内核确有USB设备/总线重建，但03:47:29仍无Apple目标，clean-2等待器1150179存活、第二次Restore未触发。已提示插拔不等于DFU，需键盘进入；不发送VDM，不因总线事件声称PD模式已清除或原生修复。

2026-09-14 03:45:16 UTC为两端拔线/普通数据线/仅键盘DFU的连接条件对照，新干净单次等待器session54816/PID1150179已启动，raw/dfu-erase-20260914-clean-2，最多至约04:15:16；03:46:20尚无Apple USB目标，未进行第二次上传。用户是否完成换线待反馈，不认定已重置PD。独立上游排查确认KIS本来受支持，Port→KIS可正常，1881不能直接判插错；#737修的是后续Restore-mode等待，#165仅macOS IOKit lifetime，均不是当前Linux iBSS10秒故障的已知修复。没有继续修改协议源码。

2026-09-14 03:41–03:43 UTC用户确认进入，干净Erase等待器真实触发：Port身份通过、40555字节Ace3Binary发送、主DFU经KIS接力成功，主ECID/CPID/BDID匹配，固定25G83 Customer Erase Install及组件检查/TSS通过；03:41:48发送1363655字节iBSS，03:41:58等待断开10秒失败exit1。没有进入iBEC/restored/StartRestore，未完成磁盘抹除或修复；发送固件事实不能称为零操作。session46959/PID1144235/1148744均已结束，无自动重试。03:41:57仍1881，内核03:42:40才断开，后续原始irecovery无法连接。干净基线重现切换失败，不能全归因项目补丁，也不能从Possibly invalid iBSS确证镜像无效。原始日志及SHA/时序见experiments/2026-09-13-iokit-ram-root/DFU_ERASE_20260914.md。

2026-09-14 03:38:32 UTC干净完整Erase等待器实际启动，session46959/PID1144235，最多等待1800秒至约04:08:32，ignored raw/dfu-erase-20260914-clean-1，权限0700。03:38:51再次检查仍无Apple USB设备，等待器存活但没有启动idevicerestore、未抹盘；识别通过才会执行一次。Bash语法、参数拒绝及git diff --check通过。原生启动尚未修复。

2026-09-14 03:32–03:36 UTC用户再次明确“直接抹盘DFU彻底修好”，本轮改为完整Erase Restore，允许删除M4全部数据与实验分区，不删除M1约47GiB备份/项目/Apple资源；备份不完整，Pictures此前不复制，已说明删除范围。当前没有Apple USB目标，原始irecovery无法连接；本地Type-C DISC返回TypecController/exit1，软件DFU请求exit0后仍未枚举，不能称为DFU成功或已抹盘。新增单次scripts/wait-for-dfu-erase.sh：固定无补丁上游binary/原始库/IPSW、外部硬件身份核对、独占锁，实际发现DFU后执行正常--erase，无自动重试、无协议源码修改。执行状态与原生启动验收见experiments/2026-09-13-iokit-ram-root/DFU_ERASE_20260914.md；目前尚未修复完成。

2026-09-14 03:26–03:29 UTC用户质疑反复修改idevicerestore是否引入问题，已暂停上传与恢复。此前03:23重新进入后的180秒等待器没有发现DFU、未上传并已停止；用户03:24的抹盘授权仍有效，但未执行Erase/完整Restore。审计确认diagnostic改过流程和错误语义，不是只加日志；--no-restore上游本身可saveenv持久化auto-bootfalse，不能当只读，--no-action在Port DFU也仍发送固件。不能把此类实验失败直接归为设备根因；最新Port接力超时又早于这些具体功能补丁，缺少无补丁A/B不能断言全由修改导致。已Nix构建firmware-upstream-tools（a6p6a74...、同固定源、patches/postPatch为空、原始libirecovery），并切换默认devShell PATH为此基线；修改版保留取证、不再自动上传。详细审计experiments/2026-09-13-iokit-ram-root/IDEVICERESTORE_AUDIT_20260914.md。当前只是干净工具已准备，设备原生Recovery及guest GUI仍未修复。

2026-09-14 03:20–03:21 UTC用户物理按键后，等待器实际识别本机Port DFU（0022/2c813200/0x3fc75d711905dde9、Mac16,12/j713ap），03:20:28自动执行一次临时加载。Apple端口ticket取得，40555字节Ace3Binary发送后03:20:31断开；20秒没有主DFU接力，03:20:51工具exit1，等待会话64242已结束，未发送iBSS/LPOL/iBEC或StartRestore。此处还未到SPTM/XNU，不能算进入可调试的主芯片环境；不能由Port DFU身份认定主DFU线口正确。随后只读irecovery仍无法连接，未自动重试/Revive/Erase。另开1800秒被动USB事件记录raw/dfu-20260914-after-port-handoff-passive.log，供同机线口/链路重建观察；不要求重复DFU按键，没有继续固件上传。完整本次日志在raw/dfu-remote-stage1-20260914-standby-2。

2026-09-14 02:59–03:10 UTC用户确认备用Recovery也无法进入，本轮未要求重复fallback按键。旧600秒udev监听已过期，不能用其空记录判断这次操作。直接从M1内核日志捕获短暂Apple Private NCM，03:04:02/26/48三次读取05ac:1905、product=Mac、本机序列号，连接随后断开；三次只读restored查询均idevice_new=-3，未获得SavedDebugInfo或GUI/SSH。主机ATCPHY仍有pipehandler lock失败及xHCI总线重建，不能单凭这些事件认定M4硬件重启原因。03:02原始USB查询验证auto-boottrue、recover-system、Bootstrap boot-volume、panicmedic与recovery-reason0x3仍存在，但iboot-failure-reason/volume这次PIPE，不能称其重复读回；03:06另读到boot-device=nvme_nand0，不证明NVMe内容或恢复资源检查通过。

固定25G83 iBSS离线解码取得新依据：recover-fallback与recover-system共用boot-device及/recovery前置检查，之后共用/lpol路径，不保证备用启动能绕过故障；lpolrestore handler使用与Local/Remote banner相同谓词拒绝Local。这是固定iBSS的代码事实，不将USB PIPE等同于handler返回值。找到reason3的一条0x99记录获取/一致性失败setter及首次错误锁存；编号已独立复核为rpnh，来自SEP响应与LocalPolicy属性，并非nsih/coih，但两份实际值、当前native实际分支仍未知。已撤回从native Stage1复用DFU准备的goto实验，诊断包明确拒绝初始Recovery，改从已核对DFU加载Remote iBSS。iBSS断开超时时新增只读KIS外部PID/内部模式/序列号查询，仍非零停止，不盲目跳过模式验收。Nix构建成功，Update/禁止Erase守卫保留；新脚本单实例、限时、仅一次--no-restore加载，Port/Main DFU分别核对并传各自ECID。6小时等待会话64242、PID1101004已启动，实际状态见ignored raw/dfu-remote-stage1-20260914-standby-2/watcher.log；尚未上传，不是完整Revive，也不自动转Erase。详见IBOOT_PANICMEDIC_20260914.md，原生Recovery和guest GUI均未恢复验收。

2026-09-14 01:19–01:28 UTC新实测取得iboot-failure-reason/recovery-reason0x3、recovery-boot-modepanicmedic、panicmedic-engaged0x1、auxkc-presentfalse；boot-volume与iboot-failure-volume均指已知M4LinuxBootstrap卷组DE77783E，auto-boottrue仍有效。原因码文字查询PIPE，0x3含义未知，不称为已证实SSV/LPOL根因。新strict临时加载在3045字节LPOL后的lpolrestore返回USB PIPE -9即退出1，未到固件/iBEC/restored；旧库忽略错误导致此前阶段误判。诊断路径新增不saveenv，避免持久化关闭auto-boot。离线确认一次性recover-fallback消费路径，但本机one-time和持久boot-command两次setter均PIPE，脚本均停止，未saveenv/reboot，后验状态不变。无Erase/StartRestore/重复完整Revive或分区修改。启动600秒被动udev USB监听80892，等待物理fallback请求；HTTP SSH辅助脚本200。详细证据experiments/2026-09-13-iokit-ram-root/IBOOT_PANICMEDIC_20260914.md，guest GUI目标仍未完成。

22:56–22:58 UTC设备重连后成功读回auto-boottrue，boot-command变为recover-system，Stage1/build-version不变。随后新strict诊断loader45312仅在发现阶段超时exit1，未发送任何组件，不能称为新版加载已验证。60秒--no-console只读等待15129退出1，没有再取得稳定Recovery查询；USB曾短暂1905后断开，M1端口仍反复重建并有pipehandler lock失败。没有GUI/SSH或guest成功证据。全部主动加载/监听已退出，后验auto-boottrue证据已保存，不再反复要求物理DFU盲刷；需用户当前屏幕反馈和稳定连接后继续取证。

22:50–22:56 UTC实际debug取得Local boot Stage1控制台，并新增原始USB返回值查询器。先irecv_receive再getenv会返回IO -1；先查询则有效读出boot-stage1/build-version mBoot-18000.161.10/auto-bootfalse/boot-commandfsboot。原库忽略USB错误，API返回0空值不可作为成功证据。已发送setenv auto-boot true22/22字节、saveenv8/8字节，但fsboot返回PIPE -9，之后nonce变化、USB目标消失，SSH No route to host；重连后的auto-boot持久化读回与启动结果尚未确认。未Erase/StartRestore/重复Revive或iBSS。新增Nix dfu-command-diagnostic-tools使控制传输错误真实上报，诊断loader链接新库；同步修正nonce_changed后LocalPolicy/Recovery root ticket旧签名风险，构建及语法/diff检查通过。独立审查确认此前已检查日志未触发旧签名缺陷，goto不缺锁，错误加锁中间构建从未实机运行且已撤回。详细记录experiments/2026-09-13-iokit-ram-root/IBOOT_CONTROL_DEBUG.md。当前无加载/监听进程，不能声称修复完成或停止回复后仍会自动debug。

22:46 UTC用户拔插同一前沿口后，实际枚举05ac:1281而非1881。只读irecovery可连接，初始主ECID匹配，ApNonce/SepNonce与22:43远程iBSS相同，shell62995有命令提示符并已退出。没有启动kisd抢占Recovery。随后24128使用带Stage1准备的--no-restore加载；实际boot-stage=1，但22:46:42仍iBEC后未断开、退出1，没有restored/StartRestore。注意加载日志中的ApNonce已不同于拔插初查，末次查询又变化且SRNM恢复本机序列号；不能声称整次加载始终保留同一Remote boot实例。shell44355未取得错误文本并已退出；不能把此前Memory image not valid套用到此次。没有重复上传iBSS/完整Revive/Erase，但Stage1准备执行saveenv。当前仍Recovery，暂无后台加载或监听。拔插确实恢复了irecovery控制通路，但未解决iBEC或原生bootloop；下一步须确认实机屏幕并对照重启时序，不继续要求反复DFU盲刷。

22:43–22:45 UTC提前kisd监听并记录PTY的物理DFU对照，加载34961仍在iBSS后退出1，但取得2394字节真实控制台（SHA256 056329a2f346c8ff62540d2abd7dcca23df46411a8d2cef68277a9ea32752574）：Remote boot/本机主ECID/mBoot-18000.161.10，aborting autoboot due to remote boot，Entering iBootStage1 recovery mode。因此iBSS确实执行并进入远程Stage1，工具Possibly invalid iBSS不是确证。kisd短暂Device opened后I/O协议错误；源码只匹配1881，不能把busy当成它误接1227 DFU的证据。内核记录接口已由usbfs占用时重复set config，以及Trying to add endpoint 0x81 without dropping it。已停止旧监听，新增Nix kisd-preserve-configuration（配置已为1时不重复SET_CONFIGURATION），构建通过；实测34401多次Device opened后仍I/O hardware fault or protocol violation，未新增控制台，22:45已停止避免反复重试。设备仍1881，没有StartRestore/完整Revive。本轮应先拔插同一口USB以重建主机端点，再用补丁监听重连；不要求再次刷写或重启M4，不把USB主机协议问题认定为原生bootloop根因。

22:39–22:40 UTC用户再次物理DFU。irecovery确认本机Port DFU ECID0x3fc75d711905dde9。第一次指定主ECID导致发现阶段过滤端口设备，1810退出1、未上传；第二次指定已核对端口ECID，12430成功发送40555字节Ace3Binary并切换主DFU，通过现有主ECID/Update守卫、取得Apple TSS，上传iBSS1363655字节后22:40:20切换失败exit1。没有进入iBEC/restored，没有StartRestore。随后实测05ac:1881 DebugUSB，立即启动kisd58441/PID999899；22:40:24返回failed to set configuration (errno 71)，22:40:29设备断开，没有取得控制台。原始证据raw/temporary-restore-physical-dfu-{1,2}.{log,stdout}、physical-dfu-debugusb-kisd.log、physical-dfu-host-kernel.txt。kisd保持单实例等待下一次枚举，不把/dev/m1n1符号链接当作连接；下一次应先有监听再进行物理DFU/临时加载，区分设备主动退出和USB配置错误，不能由errno71确定原生bootloop根因。

22:35 UTC针对已观察的本机iBootStage1，新增Nix firmware-diagnostic-tools：仅macOS Recovery且FLAG_NO_RESTORE时复用DFU路径的LocalPolicy/Stage1固件准备。Nix构建成功。临时加载4688执行Ap,LocalPolicy/lpolrestore，实际查询boot-stage=1，发送RestoreANS/RestoreDCP等、iBEC；22:35:36仍Device did not disconnect/Possibly invalid iBEC，终止exit1，未进入restored、没有StartRestore。已执行setenv auto-boot false/saveenv及临时恢复boot-args，不能称为零写入。之后只读查询仍本机主ECID/Recovery；shell88276的getenv未返回有效值，已退出。该补丁尚未解决问题，不能把此前Memory image not valid直接认定为原生启动失败根因。需重新物理进入官方前沿口DFU后再区分原生Stage1和临时iBSS路径，不盲目重复完整Revive或转Erase。

22:30 UTC换回靠MagSafe调试口后仍05ac:f014 Port DFU，Type-C reboot debugusb退出0但没有DebugUSB枚举。变更口后的--no-restore+现有kisd listener对照37060终止exit1：端口ECID断开事件已捕获，20s后主芯片DFU没有重连，工具明确提示correct USB port。此失败与前沿口下的iBSS后失败不同，说明端口控制器DFU身份可见不能证明该口支持主芯片DFU传输。调试换口未取得boot日志，不继续盲试；先不重启，请用户将线换回远离MagSafe的官方DFU口，检查主DFU是否已等待在那里，必要时才物理重进DFU。kisd7433已停止，避免后续不同协议接管冲突。

22:28 UTC用户再次DFU后，--no-restore临时环境加载60145在iBSS后切换失败exit1，未进入restored，尚未取得SavedDebugInfo；USB短暂05ac:1881后消失。已启动Nix kisd(PID992288/PTY7433)等待DebugUSB，并通过Left-back reboot debugusb请求重启；Type-C工具57705显示Connected后退出0，但USB仍无目标。/dev/m1n1由kisd在连接前创建，存在不能代替连接验收。当前仍等待设备，未重复完整Revive/Erase。下一步核对并将M4调试连接换回靠近MagSafe的原DebugUSB口（DFU口与调试口不同），保留单一kisd实例。

22:25 UTC实际推进：已从当前iBootStage1 Recovery尝试固定Apple25G83临时恢复环境，参数--no-restore --plain-progress --debug --debug，日志raw/temporary-restore-diagnostic.log。源码确认FLAG_NO_RESTORE在进入restored后、调用restore_device之前退出；此次iBEC上传后等待60s未断开，工具25503终止exit1，未进入restored也未调用修复流程。新scripts/query-restored-diagnostics.py只读查询HardwareInfo/SavedDebugInfo，Nix动态库与API签名检查通过，但当前未进入restored，实机idevice_new=-3，尚未取得诊断plist。尝试Type-C tuxvdmtool Left-back dfu，20s USB观察始终05ac:1281，不能将命令成功当作DFU切换成功。需要用户物理DFU后再次加载临时环境取证，而非重复完整Revive或扩大为Erase。

用户确认最终仍support.apple.com/mac/restore。此次USB05ac:1281与irecovery主ECID/CPID/BORD再次匹配。只读irecovery shell读到本机Local boot的Microkernel iBootStage1，BUILD_TAG=mBoot-18000.161.10，UUID=5D9E84C0-9B7C-38CB-BCF6-52E7E7FF358E，明确Entering iBootStage1 recovery mode, starting command prompt。因此不是进入recoveryOS后SSH未启动；失败处在系统启动之前，尚未解码实际错误。getenv boot-command/boot-args/auto-boot无有效输出，未执行setenv/saveenv/boot/reset；shell86750已/exit退出0。尚无新刷写，不能认定AppleTCON就是根因。进一步确认--debug可重复累加，完整FirmwareUpdaterData request需两次--debug；当前一次debug不足以确定ResponseTags的内容。

Revive DONE后用户确认仍无法进入Recovery。实机USB曾出现05ac:1905 Apple网络模式后断开，SSH No route to host，无m1n1 owner；不能将DONE称为恢复成功。进一步只读对照日志与固定idevicerestore源：AppleTCON两次取得Baobab ticket后均Not adding FirmwareData as it was not requested，随后failed to copy response for AppleTCON。restore.c的_wants_firmware_data仅当Arguments/DeviceGeneratedTags/ResponseTags包含FirmwareData时添加固件。此为host恢复协议响应兼容性的具体待查线索，不是已证明启动根因；当前日志未记录完整Arguments（debug_level>1才输出），不能盲改为无条件附加固件。暂无再次Revive/Restore，先确认用户当前屏幕与失败阶段。

22:15:45 UTC第3次非抹盘Revive返回Status: Restore Finished/DONE，PTY94910终止exit0。完整日志SHA256=bd12f2f178b0911f85b99260a392d6121da52a5703daab0511c85dabe513df3a。恢复系统安装/最终卸载检查点完成，但await_update_appletcon result=-1和一次USBPortController1 ticket缺失仍记录，不能宣称全部控制器通过，不能由DONE推断Recovery正常启动或原Data逐文件完好。结束后USB仅见root hubs，Recovery SSH返回No route to host；启动后策略/Data待检查。用户此前授权继续，无需重复询问非抹盘执行许可；保持禁止Erase/自动Restore。本轮没有修改官方Recovery增加SSH，自动启用SSH仍未实现。

22:13 UTC用户重新进入Port DFU后，第3次非抹盘Revive（工具PTY94910、PID987380，日志raw/dfu-revive-third.log）越过iBSS/iBEC模式切换，连接com.apple.mobile.restored v15；目标00008132-000A10A426B9001C、BoardID44、ChipID33074、UniqueChipID2833046977445916匹配本机。明确选择Customer Upgrade Install (IPSW)/without erasing user data。正在Flashing firmware阶段，此处尚无DONE/退出码，禁止重启/拔线，不把临时恢复环境版本当作持久化验收。此次与上次失败不同，不能以日志短暂停顿重复启动第二个恢复进程。

22:11 UTC用户授权继续非抹盘Revive。工具83621已终止exit1：Port DFU控制器阶段成功，选择Customer Upgrade Install (IPSW)，明确without erasing user data，TSS授权成功，iBSS上传后10s等待模式切换失败，未进入iBEC/restored阶段，更未返回DONE。不能称为修复完成，也不能声称没有任何写入（已发送端口控制器固件及iBSS）；主固件/Recovery持久化修复未获证明。失败后USB曾枚举05ac:1881 Debug USB，irecovery无法连接，随后断开。保留raw/dfu-revive-second.log；需要重新物理进入DFU再核对，不自动转Erase，不扩大为Restore。

用户物理进入DFU后只读确认05ac:f014 / MODE=Port DFU，PRODUCT=Mac16,12/MODEL=j713ap。端口控制器ECID=0x3fc75d711905dde9，与历史本机Port DFU一致，不能误读为主芯片ECID变化；主芯片身份须transition后重新验证。现有usbmuxd进程892341存活，没有idevicerestore进程。固定25G83 IPSW及带主ECID/Update守卫的Nix工具可用；此次尚未执行Revive或任何固件上传，等待明确确认非抹盘修复。

用户报告普通/备用Recovery均失败，白苹果进度后进入support.apple.com/mac/restore。只读USB实际枚举05ac:1281，irecovery -q确认本机ECID0xA10A426B9001C/CPID8132/BDID2c/Mac16,12，MODE=Recovery。这是固件恢复协议模式，不是可SSH的recoveryOS，也还不是DFU。已保存raw/restore-screen-device.txt；未上传固件、未执行Revive/Restore、未修改官方Recovery。下一步用户物理进入DFU，再核对身份并评估非抹盘Revive；不得自动转Erase。

本轮末：只读取证后已发m1n1 P_REBOOT准备图形对照，但USB等待循环终止exit1，未重新枚举1209:316d；Recovery SSH也连接超时。不能确定正在启动、回退Recovery或停在哪个屏幕。图形对照尚未启动，需要用户确认屏幕/恢复控制连接。本轮没有新GUI成功证据，不把WindowServer日志当作完成。

21:58 UTC新证据：guest-with-isc上传及BootArgs/ADT读回通过，实际执行BaseSystem adapter；console ring只读重连捕获显示WindowServer[77]已创建、启动多项userspace服务并调用IOMobileFramebufferUserClient。这证明启动越过此前mount-phase-1 fatal所在阶段，但当前ring已覆盖早期挂载日志，不能据此单独宣称xART mount系统调用已逐项验收。GUI仍未证明：BootArgs video.display=0，本轮framebuffer2560x1664/stride10240/depth0x1001e，仅两种像素值；SHA256=341fd5829281f903cd081a3922e8dcc42091dd884696db0dafe921c4111ba8f0。检查时Ctrl-C终止tee管道和Python，PTY22780已退出130；确认无串口owner后重连NOP成功，未重复上传。已修复launcher支持--console-log进程内镜像日志和--graphics移除-v，准备重启后图形对照。证据raw/guest-with-isc-reconnected.console-ring.txt、framebuffer-capture.log及reconnect-after-tee.json。

21:53 UTC：RAM-only iSC GPT准备完成，主备GPT及表CRC由纯Nix sgdisk -v报告No problems found；分区内容完整SHA256与BaseSystem/iSC原件一致，破坏header CRC的负对照被拒绝。launcher新增--isc-image/--isc-manifest，严格检查ECID/CHIP/大小/哈希，用四个physical extents组合prefix、已有BaseSystem、iSC、suffix，总镜像2100318208byte；md0仍仅指向原BaseSystem，额外RAM纳入top_of_kernel_data及64MiB HLE aux边界检查，ANS仍移除。正常远程重启后直接进入m1n1，HV/NOP/timer预检通过。实机PTY实验raw/guest-with-isc.log已开始上传，控制句柄22780；此处只证明准备及上传，尚未证明xART挂载或GUI。

本轮用户启用SSH后，已连接M4的25G83配对1TR，ECID=0xA10A426B9001C、CHIP=0x8132确认。Bootstrap仍Permissive、SSV Disabled/sip1=1，NSIH/coih与已验收值一致；本轮未修改策略、重启或写入目标磁盘。已通过只读dd将524288000byte iSC分区完整采集到M1：experiments/2026-09-13-iokit-ram-root/raw/isc-acquisition-1/isc.raw，SHA256=faa1fe1fb04f0c131f1f9426a0e9c4fca39b157e703fb8f311d8ee2b0a00e599。纯Nix apfsutil离线识别iSCPreboot、xART、Hardware和Recovery四个卷，与在线UUID一致。但在线Hardware占用5754880、离线5615616byte，提示live采集/检查时刻的checkpoint视图存在差异；不能称为原子快照或完整一致性验证。原Data仍FileVault Locked，占用86151307264byte，未读取其文件。下一步继续离线验证并实现RAM-only iSC媒体；尚未对guest呈现该副本，GUI未达到。

21:40 UTC实测：原生boot-ramdmg路径呈现/dev/disk1s1，apfs_boot_util开始按role查找附属卷，之前boot UUID ENOENT未再出现。新fatal依赖是iSC/xART：等待69646961-6700-11AA-AA11-00306543ECAC上的role5节点，10次重试后xART挂载ENOENT并mount-phase-1 SIGABRT。Preboot/Update缺失仅记录忽略；不能把未立即panic误认作GUI进展完成。已纯Nix添加apfs-fuse，只读提取并反汇编启动工具，未发现可直接使用的无磁盘GUI开关；下一步是原生Recovery只读采集iSC并验证后在RAM呈现，不直接放行原SSD。新scripts/collect-recovery-isc.py只读采集工具已准备，尚未执行。图形界面未达到。

21:36 UTC新对照：只修改boot UUID的guest仍在mount-phase-1 SIGABRT，lookup明确查找实际RAM卷E93D361D...并ENOENT；因此UUID错配并非完整根因，缺少可发现AppleAPFSVolume服务是下一阻塞。已定位原生IOFindBSDRoot->di_root_ramfile读取chosen boot-ramdmg-size/extents并发布di-root-ram-file内存描述符，withAddressRanges的task=NULL在本版反汇编中选择physical类型。新--iokit-ram-root实验已启动，尚未验收，保持ANS移除和RAM-only。Nix已构建panic options解码修正host工具，裸m1n1.bin哈希不变；新增只读自动panic/console-ring捕获，不把解码失败误判为guest状态不可读。

21:30 UTC最新：Bootstrap配对1TR内bputil -s成功，SSV Disabled/sip1=1、coih/nsih保留，原安装SSV和Data未修改。两次无guest普通重启以及新guest userspace panic后的P_REBOOT均直接返回m1n1，proxy/timer读写通过。BaseSystem RAM分类adapter已实机通过，guest根挂载后执行launchd和mount/apfs_boot_util；新阻塞为mount-phase-1 SIGABRT，因继承的Bootstrap boot_uuid在移除ANS的guest中不存在。已准备--ram-root-boot-uuid只对齐guest chosen到实际RAM BaseSystem卷UUID；未伪造Preboot/Data或snapshot，下一轮尚待验收。证据见experiments/2026-09-13-recovery-seal/和experiments/2026-09-13-basesystem-adapter/STATUS.json。图形界面仍未达到。下方旧状态是历史。

20:59 UTC自动Recovery检查：25G83 ordinary/Not Paired，Recovery Boot Mode=ssv-seal-broken。stub CustomKC重新读回逐字节/哈希匹配，Permissive与NSIH/coih不变；原Data仍Locked/未挂载/已用86151307264bytes。未找到新的panic报告，未改启动配置或重启。BaseSystem和stub System均No snapshots，已撤销由Recovery根哈希伪造snapshot名称的实验假设；继续定位guest直接初始根盘与stock root-dmg BaseSystem挂载路径差异。证据见experiments/2026-09-13-auto-recovery/STATUS.json。stock Recovery图形界面不等于HLE guest GUI验收。

最新10核对照（用户重启后）：proxy/timer/HV再次通过；同一16GiB及kernel/root，cpus=10越过ApplePMGR panic，出现九个secondary guest启动请求，随后停在APFS global payload bytes pointer NULL。PTY shell/hv.exit有效，All CPUs exited及主机退出码0已验证；但下一次bootstrap串口写入阻塞，主机USB reset失败并断开。尚未验证root/userspace/GUI，需再物理重启后研究Recovery直接根盘的auth/snapshot/mount分类。官方BaseSystem root-hash payload已确认匹配live BaseSystem auth blob，不能把“缺资源”当作已确定根因。最新证据见experiments/2026-09-13-cpu-complex/STATUS.json；以下控制通道状态为历史记录。

后续控制通道更新：主机 stdin 的 GDB 修复未成功，原 Python913527 已退出；协议级退出未收到 NOP 应答，进程918221最后观察为 D 状态且 TERM 已请求。guest/proxy恢复未验证，需物理重启进入持久化 m1n1，之后检查串口所有权。已添加 --guest-cpus 10 对照参数和命令行记录，尚未实机运行。下段的“主机暂停”描述是此前现场，不是最新主机状态。

最新进展：持久化 optional-ANS m1n1 已启动，USB proxy 和三个实际 boot tags（mBoot-18000.161.10）验收通过；timer 原值写入/读回和 HV.init 成功。完整内存 guest 在 HLE 1024 张页表池上限处断言；RAM-only 16GiB 对照通过 HLE 初始化并实际执行 XNU，随后 ApplePMGR::enableCPUComplex 的 complex < _cpuComplexCount 检查 panic。尚未验证 Darwin banner、root mount、userspace 或 Linux。guest panic 现场保留，主机 Python 暂停并仍占串口，退出/proxy恢复未确认。详见 [NEW_FIRMWARE_GUEST_EXPERIMENT.md](NEW_FIRMWARE_GUEST_EXPERIMENT.md)。本轮未挂载原 Data；以下旧现场按历史记录阅读。

非抹盘 DFU revive 返回成功，Recovery SSH 实测全机 SFR 已升级至 26.6.2/25G83。原 Data 仍存在、锁定未挂载，未逐文件核验。更新后旧 stub Recovery 启动发生 root-hash panic：资源更新让旧 cache symlink 改指新 BaseSystem，而旧内核/root-hash仍旧。已修复该引用并通过备份哈希及现场读回；当前为未配对的普通 Recovery，正常配对 1TR、new NSIH/coih、timer 同值写与 guest 均待复测。完整记录见 [FIRMWARE_UPDATE.md](FIRMWARE_UPDATE.md)，下文早期连接/构建状态为历史记录。

## 目标定义

本项目的“完整支持”不是只进入 m1n1 shell，而是至少满足：

1. M4 MacBook Air 能通过固定、公开、可恢复的启动流程进入 Linux。
2. Linux 能稳定运行多核、页表、NVMe rootfs、USB 输入和网络。
3. 基础显示和音频可用；之后再完成 DCP、AGX GPU、Mesa、休眠和电源管理。
4. 每个功能有对应机型、固件版本、commit 和测试记录。

## 当前结论

- M4 Linux 在架构上可行，但截至本记录日期没有公开证据证明 M4 MacBook Air 已完成 iBoot 到 Linux userspace 的可重复启动。
- M4 的关键阻塞是 SPTM。SPTM 管理页表，普通 Linux EL2 代码不能像 M1–M3 一样直接接管页表。
- 研究型 HLE SPTM 已经被用于启动和追踪 XNU；这证明路径可行，但不等于已有可发布的 Linux 实现。
- 当前最合理的实现方向是 BootKC/XNU shim 加 SPTM-aware Linux MM，而不是简单复制旧 m1n1 hypervisor。

## 当前硬件连接状态

- 2026-09-13：原版 M4 MacBook Air、macOS 26.4.1 已通过 M1 Asahi 控制机进入 DebugUSB。
- 使用 M4 靠后的 DFU USB-C 口、M1 `USB-C Left-back` 控制器，以及 `tuxvdmtool --connector 'Left-back' reboot debugusb`。
- 先启动 `kisd --base 0x3c8000000` 后，成功创建 `/dev/m1n1`，实际指向 kisd 分配的 PTY。
- 这证明当前 M4 的 Linux-side DebugUSB 观测链路可用；尚未证明 m1n1 payload、SPTM handoff 或 Linux boot 可用。
- 2026-09-13：只读打开 `/dev/m1n1` 的 picocom 测试无 console 输出；这是预期的“通道已建立、m1n1 尚未加载”状态，不能把它记为 m1n1 已启动。
- 连接测试中没有刷写、擦除或修改 M4 持久存储。

## ADevWithAnIdea/m1n1 PR #1 尝试

- PR head 当前为 `7e43bb1763ff97d661bbddb213596eda9475ae6a`，仍是 Draft，包含 23 个提交；公开页面显示维护者要求拆分 emulator/scaffolding、人工审核注释并重新处理许可证边界。[PR #1](https://github.com/ADevWithAnIdea/m1n1/pull/1)
- 在 M1 Asahi 上，PR 的 C/C++ m1n1 部分已编译；Rust 阶段因 `aarch64-unknown-none-softfloat` target 未安装失败。
- `make BUILDSTD=1` 也因 Nix `rustc-src` 缺少 `library/Cargo.lock` 失败；尚未使用非 Nix `rustup` 绕过。
- PR 的 `proxyclient/tools/chainload.py` 需要目标已经运行 m1n1 proxy，不能通过当前原版 macOS DebugUSB 通道首次加载 m1n1。
- 已将 PR head、Rust target、rust-src 和 Cargo vendor 依赖纳入项目 flake；`nix build .#m1n1-sptm` 已成功生成 `m1n1.bin` 和 `m1n1.macho`。
- 当前 M1 没有 M4 macOS 的 SSH/远程 shell，也没有 M4 的可挂载启动卷；因此尚未执行 PR README 中的 `kmutil configure-boot`。构建产物已具备，安装动作仍需在 M4 macOS/1TR 上完成。
- 因此本轮没有执行 `kmutil configure-boot`、Preboot 写入、DFU 恢复或任何持久启动修改；当前 M4 数据和启动配置未被改动。

## IRC 中的人员和工作

### StanfordAppliedCyber

这是目前最完整的 HLE SPTM bring-up 线索来源：

- 2026-05-10：raw boot 启动 m1n1，在 EL2 运行；把 XNU `genter` 调用导向 hypercall；在 EL1 运行 XNU，并模拟 SPTM handoff/runtime endpoints。
- 2026-05-28：报告接近 userspace，但说明 emulator 属于 tainted，不能直接 upstream；计划用 clean-room 文档重写。
- 2026-06-20/23：通过 timer accounting、SPMI 和 cache/TLB 调试显著降低随机启动失败。
- 2026-07-03：定位 GXF 特殊指令集中在 RETYPE 和 UAT continue endpoints，普通 TLBI/flush 不能替代其语义。
- 2026-07-09：报告不含 SPTM emulator 的 upstreamable hypervisor 已工作，但 commpage、SME/sysreg、硬编码地址和提交拆分仍未完成。

证据：`catirclogs-asahi/asahi-dev/2026-05-10.txt`、`2026-05-28.txt`、`2026-06-20.txt`、`2026-06-23.txt`、`2026-07-09.txt`。

### niklassheth / ADevWithAnIdea

[ADevWithAnIdea/m1n1#1](https://github.com/ADevWithAnIdea/m1n1/pull/1) 是公开的 SPTM emulator PR：

- 当前为 Draft，23 个 commit。
- maintainer 要求人工审核注释、拆分 emulator/scaffolding、调整许可证和解释 Python/C 边界。
- PR 作者表示 Python 只构造初始环境，runtime endpoints 已在 C 中。
- 当前不能视为 upstream-ready 或 M4 Linux 支持完成。

### dj

2026-07-22 报告 custom kernelcache 已能稳定通过 SPTM handoff，下一步是改造 m1n1；没有发现后续公开 Linux handoff 代码。

### unoloxia

2026-09-08 报告：

- J700 的扬声器、3.5mm 输出和内部麦克风阵列已在无 Exclave 的情况下工作。
- cL4/ExclaveOS 可作为 SPTM emulator 下的 secondary guest 启动。
- INFO/ONLINE/Ping/Pong 可用。
- XNU 仍卡在早期 Domain 2 TXM calls，尚未到 Domain 3/Table 0/SK RingGate。

这条线对 Exclave 和 macOS 兼容性有价值，但不是最小 Linux 启动的第一阻塞。

### Asahi 维护者和硬件 bring-up

- `sven`：SPTM/GXF 分层、nested virtualization、XNU-shim 方向和 upstream 边界。
- `jannau`：m1n1、PMGR、DT、DebugUSB、固件和启动流程。
- `yuka`：M4/M4 Pro/M5 的 DebugUSB、PMGR、USB/TB、PHY 和设备差异。
- `chaos_princess`：DART、SPMI、DCP、RTKit 和 Exclave 分析。
- `nicolas17`、`chadmed`、`JamesCalligeros`：XNU、DCP、设备驱动和 Exclave 相关分析。

## 公开参考实现

- [ADevWithAnIdea/apple-silicon-re](https://github.com/ADevWithAnIdea/apple-silicon-re)：clean-room 汇总文档，包含 SPTM 资料和 `agx-re` 子模块。
- [ADevWithAnIdea/agx-re](https://github.com/ADevWithAnIdea/agx-re)：G16/G17 AGX userspace 逆向和 Mesa 研究；不能直接视为 M4 GPU 驱动。
- [antiapplefox/m5-linux](https://github.com/antiapplefox/m5-linux)：公开的 SPTM 静态分析、m1n1 patches、BootKC 脚本和 Linux SPTM scaffold；仓库明确说明尚未 hardware bring-up，Linux MM 仍有大量 TODO。
- [rusch95/asahi_neo](https://github.com/rusch95/asahi_neo)：A18 Pro/M4 类 SPTM 的 XNU-shim 研究；当前仍是 pre-boot research。
- [lily-oc/m4-asahi-installer-checklist](https://github.com/lily-oc/m4-asahi-installer-checklist)：M4 安装和设备支持的验证清单。
- [`docs/ADEV_WITH_AN_IDEA.md`](ADEV_WITH_AN_IDEA.md)：ADevWithAnIdea 的仓库、分支、PR、commit 和 AGX/SPTM 进展审阅。
- [AsahiLinux/m1n1#675](https://github.com/AsahiLinux/m1n1/pull/675)：M4 相关 NVMe DBS 寄存器命名修复，已于 2026-09-10 合并，但不是 SPTM 实现。

## 当前缺口

### P0：启动和内存

- 固定 M4 Air 机型、SoC、ADT 和 firmware matrix。
- 可重复生成并启动 SPTM-aware BootKC/XNU shim。
- 记录完整 SPTM handoff、`genter/gexit`、frame retype、页表和异常 ABI。
- 完成 SPTM-aware Linux MM，而不是只保留 scaffold。
- 明确 secondary CPU 启动、TLB/cache、SError、SME/sysreg 和 watchdog 行为。

### P1：最小可用 Linux

- UART、AIC、timer、SMP。
- DART/IOMMU、NVMe rootfs、USB 键盘/存储、网络。
- SMC、温度、电池、充电和安全的电源状态。
- M4 Air 专用 DT/板级差异。

### P2：桌面和完整硬件

- DCP/framebuffer、DisplayPort/USB-C 显示。
- 音频、麦克风、摄像头、键盘和触控板。
- AGX kernel driver、firmware ABI、内存管理、Mesa 和同步。
- suspend/resume、低功耗和长期稳定性。

## 第一阶段验收标准

先不要追求 GPU。第一阶段只要求：

```text
M4 MacBook Air
  -> 固定 firmware
  -> SPTM handoff
  -> Linux earlycon
  -> 多核 online
  -> NVMe rootfs
  -> SSH 或 USB console
```

每次实验必须保存：机型、SoC、firmware build、BootKC/m1n1 commit、DTB、启动参数、完整 serial log 和失败阶段。
