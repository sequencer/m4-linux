# idevicerestore 修改审计（2026-09-14）

## 审计后新增：无补丁Erase基线实际对照

03:41:41用户要求直接抹盘后的干净基线真实启动--erase，Port接力、主身份、25G83 Erase identity/组件/TSS成功；03:41:48经KIS发送iBSS，03:41:58等待断开10秒失败exit1，未到restored/StartRestore，尚未完成抹盘或原生修复。使用前述upstream binary/original libirecovery，未改C源码或使用ignore-errors。该结果表明模式切换失败可以在无项目补丁下发生，不能简单全归diagnostic；仍不是原生bootloop根因证明，也不是正常USB/KIS内部状态的完整A/B。详情与日志SHA在DFU_ERASE_20260914.md。本审计下文冻结描述为03:26历史，不代表目前未执行任何基线尝试。

## 结论与操作冻结

用户质疑反复修改恢复工具是否引入问题。此质疑成立：此前没有先执行一条零项目补丁基线，将流程实验、控制传输取证和正式修复交织，增加了故障变量。不能把修改版的错误都归给设备，也不能无证据断言全部原生bootloop由这些补丁造成。

03:26开始暂停上传与恢复。主动idevicerestore/kisd/DFU等待器均已停止；03:23的新等待器没有发现候选设备、未上传，随后被TERM停止。尚有03:21启动的1800秒被动udev记录，它不发送命令。用户03:24明确允许抹盘，授权已记录，但截至本审计未执行Erase/完整Restore，也没有新建或运行抹盘工具；审计期间不自动恢复该操作。

## 实际使用的三个包不能混同

| 包 | 当前store | 项目改动 | 实际库 |
| --- | --- | --- | --- |
| firmware-upstream-tools | /nix/store/a6p6a74jfnm1nacbzkmq91p17wy2pb4h-idevicerestore-1.0.0-unstable-2026-09-07 | 新建基线，直接pkgs.idevicerestore，patches和postPatch均为空 | 原始libirecovery，2g1pmkp7v2y3mcyzgnavdk7sr6ykg7l7 |
| firmware-revive-tools | /nix/store/ljz8vilifisqgz8rscl8fg7325pgvsnk-idevicerestore-1.0.0-unstable-2026-09-07 | 14行postPatch，仅主ECID及Update/拒Erase检查 | 同一原始libirecovery |
| firmware-diagnostic-tools | /nix/store/73q786l3xiqfn11d4mdhmv939ym3s0z2-idevicerestore-1.0.0-unstable-2026-09-07 | 含guard共64行postPatch，修改流程、保存、重签、超时查询 | 修改的strict libirecovery，520xpjvs4f00qasb149migdv2pncw2fp |

三个idevicerestore的src均为/nix/store/wv4ldykq2hmg91z959d9qcgz57ashswp-source，同一版本。原始与strict libirecovery的src均为/nix/store/q33665a53ivv5p8kskvrlc7nyrh9l06n-source；前者postPatch为空，后者12行。CLI显示相同版本号不代表执行相同代码；必须核对store路径、二进制哈希、ldd和derivation。

实机记录的第三次完整非抹盘Revive用的是firmware-revive-tools，不是strict诊断版。这不代表修复成功；它返回DONE但用户原生Recovery仍失败。晚些时候诊断版的失败不能直接倒推该次完整Revive执行了诊断补丁。

二进制SHA256：

| 工具 | SHA256 |
| --- | --- |
| upstream | 4c6febb6a5a5f9cef7df149965fd3a7a97af60d8926bc2b6a299cce15225701b |
| revive guard | 7ba8ee37038183f9e806f1ddabd727cf87153fdd88c8798368882333557682bd |
| current diagnostic | bdc61643ec4c44fd76b94000670deddad666bbe52752a3f28afa419dc0f14df5 |

Nix derivation完整取证放在ignored raw：idevicerestore-20260914-audit-derivations.json、libirecovery-20260914-audit-derivations.json。基线drv为ywd09xxj7nd1xianqazsikv46j1qjx8q，guard为gdd1wfr24m00kls8480hfrg2rs5l3cfi，当前diagnostic为75fzww3py57q14cmnkc8m4s19ms64948。没有删掉旧store或日志，便于复核。

## 确实引入的差异及风险

### 1. Recovery复用DFU Stage1准备不是上游正常路径

曾把macOS MODE_RECOVERY加--no-restore导入DFU准备，并在dfu.c跳过初始mode检查。这依赖现场为合适Stage1/Remote状态，未严格验收；实机后来是Local boot，固定iBSS的lpolrestore handler明确拒绝Local。此前这类尝试没有完成restored启动。

此流程实验已撤回。当前诊断包改为拒绝初始Recovery；但它仍不是上游包，不能拿它当干净对照。这是恢复阶段选择问题，不等于已证明磁盘LPOL签名坏了。

### 2. strict补丁不只是打印日志，改变了错误语义

[固定libirecovery源](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/src/libirecovery.c)中，irecv_send_command_raw忽略正常控制命令的USB返回值；irecv_send_command_breq外层会容忍IRECV_E_PIPE。项目补丁将任何非预期长度转为IRECV_E_USB_UPLOAD，而不是只记录原始结果。这会改变外层是否继续的结果，且没有针对go/reboot等可能立即切换USB状态的命令做独立基线验收。

因此，strict版可比上游更早退出。它捕获的原始PIPE可以作为传输现象，但错误码和退出阶段可能由补丁放大，不能直接当作固件拒绝或签名错误。getter/ret读取错误补丁同样改变了API结果。观察API忽略底层错误，不等于有依据把全局命令策略改成致命错误。

### 3. --no-restore确实可能改变持久启动状态

[固定dfu.c](https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/dfu.c)先发送LocalPolicy/固件，再setenv auto-boot false、saveenv，之后才发送iBEC。--no-restore直到进入restored后才阻止restore_device。把它当“只读”或“不会影响启动”是错误的。

此前实机确实读到auto-bootfalse；已按保存后读回并在后来多次核对true。此为已确认的人为增加的启动状态变量，但原初bootloop发生在该轮临时加载之前，不能全归因于它。后来跳过saveenv减少持久副作用，同时也再次偏离上游流程；它不是干净恢复基线。

同样，[固定idevicerestore.c](https://github.com/libimobiledevice/idevicerestore/blob/60192e97f87d1bbab5c493684e0a245b0966363f/src/idevicerestore.c)在Port DFU下的--no-action仍会签名、发送Ace3Binary并等待主DFU，不能为了“只读检测”随便运行。

### 4. 重签与超时探针尚未成为已证明的修复

nonce_changed重签补丁有票据绑定的源码理由，但此前已检查的失败日志没有触发该分支，不能说修好了当前故障。新增post-iBSS KIS探针要重开控制接口，不是纯粹被动日志；最新03:20尝试还没到iBSS，该探针没有实测。

另有此前kisd与libirecovery同时访问1881的问题，会引入busy/协议错误。不能同时用它们竞争接口后，将错误直接归为M4硬件问题。Linux libirecovery的set_configuration原本比较当前值，kisd的重复配置问题不能简单套用给它。

## 最新Port DFU超时不能直接归因于这些功能补丁

03:20一次加载取得ticket、发送Ace3Binary、断开后20秒未见主DFU，exit1。失败在上游main的Port DFU段（本地未补丁源码约lines666–870），早于main的guard及DFU/Recovery分流，也早于strict的命令/getenv补丁所作用路径。mode事件监听及端口缓冲传输没有被上述项目补丁修改。

这只能说明当前没有证据证明这些具体功能补丁直接触发了此超时，不是对整个host工具链的排除。没有相同条件的无补丁A/B，不能以工具提示正确端口就认定用户插错，也不能宣布必须抹盘。此次根本未上传iBSS，不能拿SPTM、rpnh或guest panic解释它。

## 已落实的纠正与后续基线

1. Nix新增firmware-upstream-tools直接引用pkgs.idevicerestore，构建成功并核对derivation：patches/postPatch为空；链接原始libirecovery。
2. 默认devShell的idevicerestore从guard版切换到此上游包；command -v与--version已核对，没有偷偷混用修改库。已有dfu-tools也是原始包。
3. 修改版和旧日志仅保留供取证，不继续自动上传；审计本轮没有修改任何恢复协议、固件命令、iSC或目标启动状态。
4. 后续先用明确路径的原始irecovery -q核对模式；完整Restore若执行，将用干净工具、固定IPSW及外部目标核对，不继续叠加C源码流程补丁。用户已允许抹盘，但应事前明确删除范围，并以真实原生启动/GUI验收，不以DONE代替。
5. M1的liqi_backup与项目固件/资源备份保留，本轮只核对用户备份目录存在、约47GiB，不证明逐文件完整。此前Pictures被用户排除，完整Restore将删除M4上的未备份内容；不得宣称已有完整全盘备份。

当前设备修复仍未完成，干净工具基线的构建不是设备恢复验收。

03:31使用原始results/dfu-tools/bin/irecovery -q（root）再次检测，退出255、Unable to connect to device；没有固件上传。证据raw/idevicerestore-baseline-20260914-original-irecovery-query.log。这说明当前检测失败并非strict getter错误语义在起作用，但此时没有可连接设备，仍不构成相同DFU状态的完整恢复A/B。独立只读审计确认上述包/库区分、strict提前退出及03:20功能补丁未命中；未新增设备级根因结论。
