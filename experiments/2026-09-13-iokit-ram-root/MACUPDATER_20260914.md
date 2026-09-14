# Finder Restore：4042与更换M4接口后的进展

## 最新用户反馈（2026-09-14）

用户进一步澄清此前使用的是Revive修复模式，完成后仍无限重启；随后执行Restore抹盘恢复，现确认“现在抹盘恢复完成”。以此纠正下文将前一轮称作完整Restore的记录。当前结论为用户确认全盘抹除恢复完成，尚未验收新系统启动/激活/桌面及正常重启；没有证据说此次Restore后仍bootloop。本文件保存的旧4042日志仍仅属于最早失败尝试，新完成日志待取得。

用户随后明确：“恢复完成 无限重启”。据此更新为Finder Restore已完成（用户确认），M4原生启动仍失败。尚无换口后的完成日志，下面分析的文件是换口前4042，不能代表新Restore失败或说明新bootloop原因。应保存新完成日志并重新采集启动实例状态，不沿用抹盘前的卷组身份或策略错误。下面“正在等待更新固件”是较早反馈。

用户确认使用Finder Restore、普通数据线，原先报错4042；随后更换M4端接口到远离MagSafe的Type-C口，反馈“正在等待更新固件”。目前记录为更换正确DFU口后恢复流程有进展，尚未收到恢复完成日志或原生启动验收。此前“现在好了”经用户补充指正在进行恢复，不能写成完整刷机成功。

这个端口位置符合[Apple的2025及以后MacBook Air DFU口说明](https://support.apple.com/en-us/120694)。接口选择是当前最直接、最有实机依据的解释方向，但缺少本次成功阶段日志，尚不能把之前所有Linux/iBSS超时归结为同一个根因。救援Mac型号/系统版本未记录。

## 原始失败日志

来源：`/home/sequencer/Downloads/Telegram Desktop/MacUpdater.log`，71421字节、1350行。已原样保存在ignored raw的`macupdater-20260914-official-1/MacUpdater.log`，目录0700/文件0600，SHA256为`b0995199928e305ef5d8b8756033c6400c18bc978ccaa9cc95161030dc250a25`。原文件未修改。

日志使用2026-09-14本地时间，未注明时区，不直接换算UTC。客户端AMPDevicesAgent 1.7.0.161、Apple Mobile Device 1860.1.5，软件资源build25G83；端口ECID0x3FC75D711905DDE9与已知目标一致。

| 日志时间 | 原始行号 | 事实 |
| --- | --- | --- |
| 16:27:24.4441 | 13–19 | 记录Chip8132、Board2C、端口ECID及Starting State: Port DFU |
| 16:27:25.2314 | 47 | 选择USBPortController1,USBFirmware |
| 16:27:26.0807 | 64 | 收到端口固件TSS响应 |
| 16:27:27.4741–27.4760 | 1337–1338 | Port DFU succeeded，端口恢复阶段成功 |
| 16:27:27.4765–27.4766 | 1339–1343 | 进入Transitioning，启动10分钟计时器，Port设备断开 |
| 16:37:27.4776–27.4793 | 1344–1350 | Transitioning→Disappeared，status4042，总耗时603秒 |

终止描述：`Gave up waiting for device to transition from Port DFU state to DFU state.`

全文统计：635条DNLOAD请求，GETSTATUS的state5/status0为634条，state6/status0、state7/status0各1条；没有GETSTATUS非零status。没有主ECID0xA10A426B9001C、iBSS/iBEC、restored、StartRestore或RestoreFinished记录。

这份日志卡在端口固件成功之后、主AP DFU接力被恢复器接受之前，比M1四次已取得主DFU身份后卡iBSS的阶段更早。应用日志没有主DFU事件，不等于已证明总线上完全没有任何短暂枚举，需要USB时间线才能判定。端口恢复成功也不代表SSD已抹除。

## 解释边界及pitfall

- 用户已明确Finder Restore，不能凭日志阶段的`requested restore behavior: Update`或Upgrade identity反驳实际操作；同一文件后续也出现Erase identity，但没有最终磁盘Erase执行证据。
- `FormatForAPFS`、`MacOSSwapPerformed`及Restoring是选项/流程状态，不能当作已格式化或已安装的证据。
- board config/serial null及recovery variant警告之后仍完成Port阶段，不能仅凭这些消息确定终止根因。
- Port DFU可见、端口ticket成功、甚至端口固件上传成功，均不足以验收M4物理DFU口与主AP接力。2025Air与早期Air口位不同，应记录实际连接位置。
- Apple官方工具也失败削弱“只有本项目补丁/Linux导致”的解释；用户换口后有进展进一步提高接口/连接路径的调查优先级。此前KIS BOOT_IMG源码候选没有因此得到证实，也不能解释本份尚未到iBSS的日志。

## 当前动作与验收

Finder固件更新进行时保持连接、供电和救援Mac唤醒，等待其完成。当前M1不启动竞争恢复/USB查询，不再要求重复DFU操作。恢复器完成后应验收M4进入设置助理或正常macOS并能稳定重启；若再次失败，保留换口后的新日志，与这份换口前的4042记录比较。原生启动稳定前不继续安装SPTM/m1n1或更改分区。

参考：[Apple恢复步骤](https://support.apple.com/en-us/108900)。本次分析及文档更新没有向M4上传固件，Finder执行进度来自用户反馈。
