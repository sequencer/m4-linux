# M4 原生启动修复路线（2026-09-14）

## 最新验收：全盘Restore完成，等待原生启动结果

用户澄清此前完成的是Revive修复，之后无限重启；随后另行执行Restore抹盘恢复，现已明确确认完成。下方将Revive误记成完整Restore后的bootloop判断已撤回。当前应验收设置助理/激活、正常macOS桌面与正常重启，保留新完成日志及固件/系统build；本次原生结果尚未反馈，不能称仍重启或已完成全部修复。

## 历史判断（操作模式已纠正为Revive）

用户明确确认Finder Restore完成后M4无限重启，覆盖下方“等待更新固件”的历史状态。换口解决了至少一部分恢复通路问题，尚不能解释或解决原生bootloop。下一步取得换口后完成的MacUpdater.log，核对最后恢复结果/实际资源，再取得恢复后启动日志；如果恢复器已经结束，可检查一次长按电源是否能进入启动选项/Recovery。若可进入，优先读取新系统的panic/诊断记录；若仍到启动选项之前就重启，优先早期启动/固件及Apple硬件诊断。现有旧4042日志和恢复前Bootstrap/panicmedic上下文不能替代新的证据。当前不再重复推荐同条件Finder Restore，不能仅凭bootloop判定硬件损坏。

## 最新进展：更换M4接口后正在更新固件

用户确认Finder Restore与普通数据线，旧MacUpdater.log报4042（Port成功后10分钟无主DFU接力）；将M4端换至远离MagSafe的Type-C口后反馈正在等待更新固件。接口选择是目前最直接的实机线索。当前应等待Finder完成并验收原生启动，暂停执行下列调查/替代恢复方案。尚无换口后的完成日志，不能宣称已经修好或旧Linux/iBSS失败全部同因。失败日志、身份、时间线及边界见`../experiments/2026-09-13-iokit-ram-root/MACUPDATER_20260914.md`；以下为此前调查计划。

本轮只做记录复核、源码与上游查询、M1内核/分区只读检查，不执行第五次Restore，不发送VDM，不修改恢复协议，不重启M1。M4全盘Erase授权仍有效，但授权不代表可以省略硬件身份与模式验收。执行状态另见`PROJECT_STATUS.md`。

## 两个问题必须分开

- 原生启动失败：历史1281 Recovery为Local Stage1、panicmedic/reason3，默认及失败卷组指向M4 Linux Bootstrap；rpnh一致性检查是一条静态候选，实际命中分支和两份值仍未知。不是已确认SSD坏，也不能由关闭SIP或清nonce保证修复。
- 救援启动失败：第四次干净Erase已通过Port→主DFU、正确Erase identity与TSS，仍停在发送iBSS后的10秒断开等待。没有到iBEC/restored/StartRestore/完整写盘；必须先打通救援链路，修改APFS布局不能解决这个阶段的问题。

同一M1在09-13 22:15曾完成Update/Revive协议，但原生仍无法正常启动。因此Linux路线并非已证实不可用，旧DONE也并非原生修复成功。04:20真实PTY/显式Erase variant/原cache/单debug对照仍失败，不能继续把漏调用参数当作确定根因。

## 路线一：纯Nix继续，先做连接条件对照与USB取证

这是保持当前M1 Agent在线的优先调查路线，不是不变条件下再次盲刷。

### 连接条件需要实际确认

- M4 Air 2025的DFU口为面对左侧时最右边的Type-C口，即远离MagSafe的那个。用户最早说的是靠近电源的口，此后是否已改正确口尚未独立验收。Port/KIS身份通过不能代替物理端口确认，也不能仅凭1881就断言插错。
- 直连普通USB-C数据/充电线；不能把“雷电线”自动视为Apple建议线缆。Apple明确排除Thunderbolt 3，不是排除所有Thunderbolt代际；当前具体线材与换线动作尚未可靠记录。
- M4用MagSafe供电，其他USB口不接外设；两端拔开后再直连，只用内置键盘进入DFU，不追加软件DFU/debugusb VDM。记录这些动作，不宣称已证明PD状态全部清除。
- M4端保持正确DFU口，M1端可以换另一个Type-C口作为独立主机连接条件对照。不要改变两端接口后还认为是同一变量，也不把动态USB rootbus路径直接等同固定物理端口。

[Apple线缆/供电/DFU说明](https://support.apple.com/en-us/108900)，[Apple DFU端口表](https://support.apple.com/en-us/120694)。Asahi记录了DFU/hold、DFU USB与Debug USB不同动作及软复位持久标志，但不能将其他机型的PD持久性直接定为本M4故障：[USB-PD文档](https://asahilinux.org/docs/hw/soc/usb-pd/)。

### 下次调用必须增加被动传输证据

本M1内核实测7.1.8，`CONFIG_USB_MON=m`、`CONFIG_DEBUG_FS=y`，debugfs已挂载，匹配内核的usbmon模块存在于`/run/booted-system/kernel-modules/lib/modules/7.1.8/kernel/drivers/usb/mon/usbmon.ko.xz`。本轮未加载模块，usbmon节点尚不存在，不能称已开始抓包。

准备时通过Nix管理工具与模块依赖；若新增采集工具则加入固定flake。开始上传前启动usbmon、被动udev与内核日志记录，按实际发现的bus/设备筛选，处理端口切换造成的重新枚举，不硬编码历史USB1。采集器限时是采集限制，不给实际Restore追加短timeout强杀。

需要回答：

| 传输证据 | 可支持的分支 |
| --- | --- |
| KIS upload的实际完成长度/URB状态异常 | 先修连接/主机或有证据的传输问题，不归为LocalPolicy |
| 最终KIS `BOOT_IMG`（index0x103）的回复异常 | 定位启动触发/回复处理，不能把upload成功当执行成功 |
| AP内部已到Recovery，但外部1881不变 | 调查模式重新发现/事件等待，不强行跳过签名及主身份 |
| 目标报告签名/执行失败 | 才进入个性化ticket、Erase/Upgrade差异与对应错误检查 |
| iBEC/restore kernel成功但restored缺失 | 才调查usbmuxd、NCM、restore服务；不是当前的首要阶段 |

usbmon是HCD接口层观测，不是线上的硬件分析仪；即使URB成功也不能直接排除HCD/PHY问题或证明目标执行成功。[Linux usbmon文档](https://docs.kernel.org/usb/usbmon.html)。

原始KIS库有具体审计点：`irecv_kis_config_write32`中回复size不是4时打印错误后返回此前的`err`，且没有显式检查`rpl.status`或实际接收长度`rplSize`是否足够覆盖字段；`irecv_kis_send_buffer`最后通过它发送BOOT_IMG。它值得抓实际回复验证，但目前没有取得本机异常回复，不是已证实根因，暂不改源码。旧clean1/2/3 stdout未见所查错误特征不排除该候选：size等于4但status异常不触发这条打印，stdout也不能证明覆盖了全部库输出。源：[固定libirecovery](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/src/libirecovery.c#L1094)。

`irecv_get_mode`读的是当前client缓存，不能对同一旧handle反复调用就称“实时内部模式”。fresh KIS open会重新获取内部描述符，外层1881与内部mode应分开记录；原始`irecovery -q`对1881固定显示KIS DFU文本，不能只靠该行证明内部一直在DFU。新开查询仍有USB配置/初始化影响，不是被动监听；不能与idevicerestore/kisd竞争，在恢复退出后另行取证，目标消失或身份/模式不明时停止。源：[固定库模式读取](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/src/libirecovery.c#L4055)，[固定irecovery查询实现](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/tools/irecovery.c)。

## 路线二：已有可用firmware Recovery时，评估标准Recovery入口

不是Recovery GUI/SSH，也不是修改native Recovery让它goto DFU。本机03:53曾出现1281，但当时没有从该入口执行Erase或取得boot-stage；历史更早的1281多为Local Stage1/panicmedic。

固定上游`idevicerestore.c`将初始`MODE_DFU`和`MODE_RECOVERY`分开：前者走`dfu_enter_recovery`发送iBSS；后者直接`recovery_send_ibec`发送iBEC并执行go，正常等待断开/重连，再走Restore。**可绕开当前iBSS等待代码，但它没有自动补齐DFU路径的Stage1 LPOL/固件准备**，不能保证M4的Local Stage1接受该启动。

前置条件：唯一目标、主CPID8132/BDID2c/ECID0xA10A426B9001C与型号通过；内部确为Recovery，尽可能取得有效boot-stage/build/Local或Remote上下文。不能因外层PID1281/1881就认定具备完整恢复前提，更不能以原版对非Stage2仅打印“continuing anyway”作为项目验收通过。

若评估执行，使用无补丁upstream、完整固定IPSW、正确主ECID及明确Customer Erase variant，维持TSS、模式重连与完整Restore流程；不复用只接收1227/f014的现有Erase等待器强行喂1281，也不使用已撤回的diagnostic goto/LPOL补丁。iBEC/go、断开/重连或Stage2验收失败立即停下记录，不继续向未知状态发送恢复资源。**这条标准入口尚未在本M4验证成功。**

源：[初始Recovery分支](https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/idevicerestore.c#L1439)，[iBEC/go](https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/recovery.c#L349)。

## 路线三：以修好为优先，使用macOS Finder的完整Restore

Apple正式路线是macOS14或更高的另一台Mac，通过Finder DFU窗口选择Restore Mac→Restore and Update；不是再做一次非抹盘Revive。使用同样正确的M4口、普通数据线、直连和供电条件。该路线换掉Linux/libusb/本项目恢复工具的不确定性，但不保证硬件无故障，也不保证Apple当前下载资源与固定25G83完全相同。[Apple恢复步骤](https://support.apple.com/en-us/108900)。

本M1只读分区检查仍有57.7GiB APFS Container及5GiB RecoveryOSContainer；**这不证明有可启动的完整macOS14+**。若原macOS确实可启动，它可能临时作为Finder host；否则借另一台Mac。切换本M1会中断当前Nix Agent，不能擅自重启、为救M4抹掉M1/Linux/备份或把M4 Erase授权扩大到host。

若坚持不使用macOS，换一台具有不同USB控制器的Linux host、沿用固定Nix工具/IPSW也是连接/host对照候选。上游M4 Mini #748报告换PC后成功，但卡的是iBEC而非本机iBSS，属于不同设备/阶段的参考，不证明本M1不能恢复：[当事人回复](https://github.com/libimobiledevice/idevicerestore/issues/748#issuecomment-3176112322)。

## 当前不值得继续的操作

- 不再补调用参数或不变条件连续DFU：matched-tty已真实失败。
- 不先清全部NVRAM、iSC、rpnh或重放旧ticket：没有命中分支/值证据，且不能解决当前USB救援验收。
- 不先关闭SIP、改APFS/删除Bootstrap或重新安装SPTM：当前失败未进入macOS/Linux启动阶段。
- 不由晚断开认定扩大10秒timeout即可修复：本轮04:21:55断开后并无可用Recovery，延长等待需要目标模式/执行证据。
- 不套用不相关PR，也不把版本过旧当默认解释：本轮GitHub API核对两个master HEAD均与当前固定源一致，idevicerestore为09-07的60192e9、libirecovery为08-23的95dec3a。

具体PR纠正：[#737](https://github.com/libimobiledevice/idevicerestore/pull/737/files)仅提议后续进入restore-mode的180000→240000ms，已关闭且未合并；固定master的对应等待现为300000ms，不是本次`dfu.c`10000ms。之前笼统说“#737改到5分钟”不准确。[#165](https://github.com/libimobiledevice/libirecovery/pull/165/files)已合并，但只改macOS IOKit引用生命周期，不是Linux iBSS切换修复。

## 验收与日志边界

完整Restore要有restored/StartRestore/RestoreFinished及正常exit；之后还必须看到M4原生Setup Assistant或可用Recovery、完成需要的激活并稳定重启，不再落到restore网址。协议DONE不单独算修好。原生稳定前不装m1n1/SPTM，不立即再缩分区。

所有原始TSS、KIS、usbmon及固件updater日志放ignored raw，目录0700/文件0600；公开文档仅时间、长度、返回码、模式与必要哈希，不公开ticket/nonce内容或其他USB外设数据。M1的`/home/sequencer/liqi_backup`、项目与Apple固定资源不删除，目录存在不代表完整备份。
