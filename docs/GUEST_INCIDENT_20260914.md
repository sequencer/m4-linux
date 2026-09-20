# Guest 后无法进入 Recovery：复盘与未决因果

## 确认事实

1. guest 前，新 stub 已在配对 1TR 完成 m1n1 安装、SIP/SSV 策略修改和默认启动选择，普通重启进入 EL2 proxy，NOP 成功。macOS 策略仍 Full。没有完成这个新布局的 macOS→stub→正常/备用 Recovery 多路径回归测试。
2. guest 使用 25G83 BaseSystem、16GiB/10 核和抹盘前的 iSC RAM 副本，删除 ans 节点，但仍允许多种实际外设交互。这不是完整设备虚拟化或持久状态隔离。旧 iSC 与当前 SEP/所有权状态一致性没有验证。
3. guest 已创建 launchd/WindowServer/Boot Picker 等进程。IORegistry 显示 MTP/RTBuddy/DockChannel/HID transport 驱动绑定，不是只有残留屏幕或内核初期。
4. 交互解析 LoadingGroup 时，错误地把数值对象作为 OSString。日志记录对象 +0x10 内容为零；readstr 经 readptr(address+16) 再 hv_translate 后直接 readmem，没有检查类型、空指针或翻译失败。它不再是限定 guest RAM 的安全读取，可能触发 target 异常。
5. 紧接着 UartChecksumError（sentinel 0x30303020），随后 EIO/USB 失联，用户报告循环启动且普通/备用 Recovery 失败。未捕获完整 target ESR/FAR/异常栈，不能声称已精确证明读 PA 0 的具体故障路径或某个持久对象损坏。
6. 后续本地 DFU Erase 在 iBSS 切换超时；这是后发生的救援故障，不能解释它之前的 Recovery 故障。用户提供的 MacUpdater-3.log 证明一次同 build Erase 成功，但日志时区及其与本轮故障的时间关系未确认。

## 必须承担的错误

- 将“删除 ans / RAM-only 根盘”表达成过强的安全边界；没隔离 SEP、NVRAM 等路径就不能保证后续原生启动不受影响。没有直接执行磁盘写入命令，不等于 guest 不会触发持久状态变化。
- 已知上轮相似 guest 后出现原生启动故障，仍在未隔离根因、未建立可靠回退验收前重跑历史方案。
- 使用抹盘前 iSC 副本而未排除其安全状态错配；告知风险不是技术上的隔离措施。
- 把重要内存解析放在未验证的交互 helper，缺类型和地址守卫；守卫只在部分脚本中实现，却没有覆盖实际执行路径。
- 没有提前建立异常前后全机启动状态对照及 target 异常留存，失联后缺失最关键证据。

## 未解决的因果

错误读取是失联前的直接可疑触发点，但一次 volatile memory fault 不足以解释为什么完全关机后两种 Recovery 均失效。需区分默认 stub 重启/自动恢复策略、guest 对真实协处理器及持久状态的影响、旧 iSC 错配、Apple 启动失败计数等假设。当前没有证据证明 Recovery 镜像被覆盖、SEP 被破坏或硬件损坏，也不能把 SIP disabled 当作确定根因。

## 恢复后的硬性门槛

- 暂停现有 run-recovery-guest 路径，不以“再试一次”替代根因隔离。
- 先验收 macOS、正常 Recovery、备用 Recovery；将安全原生系统设为默认启动，实验入口与救援入口分开。
- 从新恢复状态获取新的只读基线，旧 iSC 仅做离线研究，不再次给 live guest。
- 所有诊断统一强类型、白名单、分段 VA→PA 校验，拒绝空地址/未知类型/非预期 RAM，先做离线负向测试。target 端另需验证内存读异常能可靠返回错误，不能仅依赖 Python 异常。
- 在下一次 guest 前审计实际外设映射和可持久化调用路径；无法证明隔离时明确不允许该路径自动运行。
- 有限、单变量实验，先准备异常证据捕获；失联即停止，不盲目重签策略或反复 DFU。
