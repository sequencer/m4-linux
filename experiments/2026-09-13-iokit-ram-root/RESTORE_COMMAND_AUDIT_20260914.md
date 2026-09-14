# 成功DFU与当前Erase命令对照（2026-09-14）

## 结论

### 04:20–04:22硬件对照已完成：matched-tty仍失败

第四次干净Erase调用已实际运行，而非仅通过包装测试。04:20:48 Port核对后主ECID0xA10A426B9001C于04:20:52.354以DFU连接；显式Erase variant、原cache、单debug、真实PTY全部生效，工具fd0/fd1均`/dev/pts/9`，AI输入已授权YES后04:21:10.707继续。组件与TSS通过，04:21:13.858发送1363655字节iBSS，04:21:23.914同一10秒无断开报错，04:21:24 exit1。没有iBEC/restored/StartRestore/RestoreFinished，也没有完成SSD抹除。

被动USB记录外层f014→1881；host内核04:20:52.006断开Port、04:20:52.129新增主设备，到04:21:55.481才断开主设备。04:21:55开始的原始只读irecovery查询exit255，04:22无Apple目标，不能验收本次内部模式/boot-stage或把晚断开当作执行成功。恢复与等待会话已结束，没有自动重试；仅限时被动监听仍在。日志SHA与全部时序在DFU_ERASE_20260914.md最新段。

这次实测排除了“补上显式variant/cache/单debug/真实TTY即可成功”的充分性，但不是Erase/Upgrade与物理连接状态的完全A/B。旧成功使用Upgrade且原guard拒绝Erase，个性化ticket未做等同性验收；不能断言Erase本身为根因、M1不可用或文件损坏。固定`dfu.c`只在组件发送返回成功后等待断开事件，`Possibly invalid iBSS`是模式等待的通用提示，不是镜像校验结论。当前不追加恢复协议补丁、扩大timeout或跳过断开检查；下一次上传需要不同可记录条件或新的传输/目标运行证据，不重复未改变条件的命令。

下面04:17等待及04:00冻结描述属于当时历史状态，不代表第四次仍待触发。

### 04:17用户明确要求再次重试：对齐profile已就绪

只修改scripts/wait-for-dfu-erase.sh的调用包装，新增第四参数matched-tty；原diagnostic默认参数及无补丁upstream/原始库/IPSW、完整目标核对和单实例限制保留。matched-tty固定一次--debug、Customer Erase Install、原revive-cache，不加plain-progress；通过Nix util-linux script保留子进程stdin/stdout真实PTY，将stdout/PTY全文留私有raw。上游Erase提示将由AI核对后输入已授权的YES，不使用no-input/ignore-errors或恢复协议补丁。

Bash语法/git diff --check、非法profile拒绝、非TTY matched调用拒绝均通过；离线子进程test -t0/test -t1在stdout重定向情况下实测通过，无设备指令。该包装测试不等于已验证设备Erase成功。

04:17:01等待器真实启动：session30994/PID1168847，最多1800秒至约04:47:01，raw/dfu-erase-20260914-matched-1；被动USB事件session46167/PID1168840，单独raw/dfu-erase-20260914-matched-1-usb-events.log，不抢接口、不上传。此前原始查询旧1881通路Unable to connect且设备随后不再枚举；04:17:11等待器存活但尚无device.txt/restore.log/restore.pty，未执行第四次上传，已提示用户按键DFU。

实际调用：nix develop --command bash scripts/wait-for-dfu-erase.sh --authorized-erase experiments/2026-09-13-iokit-ram-root/raw/dfu-erase-20260914-matched-1 1800 matched-tty；必须使用具有交互stdin的执行会话。下文04:00冻结与未启动描述属于历史审计状态。

用户要求检查命令，因为此前同一台M1确实完成过DFU恢复。此提醒正确：不能跳过已成功记录的逐项对照，直接认定Linux主机不可用、要求换主机，或用不变条件下反复按键代替分析。本轮暂停上传，没有第四次恢复进程。

尚未找到可确定解释iBSS10秒超时的错误参数。Port ECID正确，Erase identity选择正确，没有误加no-restore/no-action或外层刷写timeout。之前成功与现在的命令确有profile差异，但这些差异不是已验证根因；原成功profile也曾失败一次。

重要修正：不能以成功日志无KIS字样证明普通DFU路线。原成功只有一个--debug，而固定idevicerestore.c仅debug_level>1才打开libirecovery日志；本轮两个--debug才输出KIS信息。历史主芯片外部PID仍未核定，不能冒称当时必为1227。

## 实际成功命令，不采用README的泛化示例

从sudo journal的2026-09-13 22:12:50执行记录取得，TTY=pts/3，PWD为项目根目录：

```sh
sudo -n /home/sequencer/project/m4-linux/results/firmware-revive-tools/bin/idevicerestore \
  --debug \
  --ecid 0x3fc75d711905dde9 \
  --variant 'Customer Upgrade Install (IPSW)' \
  --cache-path /home/sequencer/project/m4-linux/artifacts/apple/25G83/revive-cache \
  --logfile /home/sequencer/project/m4-linux/experiments/2026-09-13-iokit-ram-root/raw/dfu-revive-third.log \
  /home/sequencer/project/m4-linux/artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw
```

这是Update/非抹盘Revive，不是Erase。发送iBSS后22:12:59.586确实断开，22:12:59.988进入Recovery；之后LPOL/lpolrestore、boot-stage1固件、iBEC、boot-stage2、restored通过，22:15:45 DONE/exit0。内核也记录22:12:59 USB1-1设备3移除、设备4重连。原生系统仍启动失败，所以只能称恢复协议完成。

同一套显式Upgrade variant/cache/真实TTY在22:10:56也运行过（没有debug），22:11:14 iBSS10秒断开超时。成功并非这些参数一出现就必然发生。

## 最新失败命令

2026-09-14 03:54:47 sudo journal记录的实际调用，输出写私有raw日志，stdin=/dev/null，没有TTY：

```sh
sudo -n env -u LD_LIBRARY_PATH -u LD_PRELOAD \
  /nix/store/a6p6a74jfnm1nacbzkmq91p17wy2pb4h-idevicerestore-1.0.0-unstable-2026-09-07/bin/idevicerestore \
  --erase --ecid 0x3fc75d711905dde9 --plain-progress --debug --debug \
  --logfile /home/sequencer/project/m4-linux/experiments/2026-09-13-iokit-ram-root/raw/dfu-erase-20260914-clean-3-dfu/restore.log \
  /nix/store/gy1rm7g6m5xv4ba9qjvnjvns3zvb2da9-UniversalMac_26.6.2_25G83_Restore.ipsw
```

03:54:54.895发送1363655字节iBSS，03:55:04.950等待物理断开10秒失败，watcher03:55:05记录exit1。三次clean尝试均停在此阶段，没有iBEC/restored/StartRestore/完整抹盘完成。

## 逐项核查

| 项目 | 成功Update | 当前Erase | 判断 |
| --- | --- | --- | --- |
| 初始ECID | 3fc75d711905dde9 | 同值 | Port DFU正确；不能直接换成主ECID导致初始过滤 |
| 主芯片身份 | 000a10a426b9001c | 同值，8132/2c/j713ap | 三次接力后均核对通过 |
| 恢复模式 | 明确Upgrade/Update | --erase，日志Customer Erase Install | 不同目标所需差异，不是漏Erase；不混用--erase与Upgrade variant |
| variant参数 | 显式指定 | 未显式指定，但实际选中正确Erase | 可显式固定便于复现，不能称已证实选错 |
| cache参数 | 固定revive-cache | 未指定 | 本IPSW的OS ZIP_STORED，无不可seek OS提前解压分支；不能直接归为iBSS失败原因 |
| debug | 一次 | 两次 | 改变日志可见性；不是KIS/普通DFU选择器 |
| plain-progress | 无 | 有 | 进度输出格式，不是跳过或模式命令 |
| TTY | stdin/stdout真实终端 | 无TTY，stdin=/dev/null | 改变交互提示；应作为复现变量控制，尚未证实造成模式失败 |
| binary | ljz... guard版 | a6...原版 | 同固定源；旧版14行只拒绝未知主ECID/non-Update/Erase，不能用于本轮Erase |
| libirecovery | 2g1...原始库 | 同库 | 不是strict诊断库 |
| IPSW | 项目symlink | 其Nix canonical路径 | 同一固定Apple25G83资源，不是另一份裁剪manifest |
| iBSS后事件 | 实际断开/Recovery | 10秒无断开 | 已确认时序差异；根因及历史外部PID仍未知 |

对固定BuildManifest使用Nix Python的zipfile/plistlib比较：Customer Erase和Upgrade的iBSS、iBEC整个Manifest entry均相等，路径及Digest相等；不能称选到了不同iBSS文件。其他Info/Manifest/UniqueBuildID有差异，签名及nonce也可能不同，不能据此说最终个性化payload逐字节相同。

## 后续对齐profile，不等同已验证修复

下一次有新诊断依据时，可固定一个--debug、显式Customer Erase Install、原cache目录及真实TTY，使用无补丁upstream而非拒绝Erase的guard版。固定目标核对仍在执行前进行：唯一恢复候选、Mac16,12/j713ap、CPID/BDID及Main/Port对应ECID。当前没有启动此配置或要求再盲按DFU。

以下是已核对Port DFU后使用的命令profile；Main DFU必须改用主ECID。实际执行前使用全新私有raw目录，不复用旧日志。

```sh
cd /home/sequencer/project/m4-linux
nix develop
test -t 0 || exit 1
output=$PWD/experiments/2026-09-13-iokit-ram-root/raw/dfu-erase-matched-tty
mkdir -m 700 -- "$output"
printf -v restore_command '%q ' sudo -n env -u LD_LIBRARY_PATH -u LD_PRELOAD \
  "$PWD/results/firmware-upstream-tools/bin/idevicerestore" \
  --erase --debug --ecid 0x3fc75d711905dde9 \
  --variant 'Customer Erase Install (IPSW)' \
  --cache-path "$PWD/artifacts/apple/25G83/revive-cache" \
  --logfile "$output/restore.log" \
  "$PWD/artifacts/apple/25G83/UniversalMac_26.6.2_25G83_Restore.ipsw"
script --quiet --return --flush --command "$restore_command" \
  "$output/restore.pty" > "$output/restore.stdout" 2>&1
```

Nix已有util-linux的script创建子进程PTY，即使外层stdout写文件，子进程stdin/stdout仍为TTY；不能直接重定向idevicerestore stdout再声称复现真实TTY。上游会出现Erase YES提示，已获得用户授权，AI可在核对目标和日志后输入YES；不加no-input/ignore-errors、不改恢复协议。通过restore.pty观察提示，原始票据只留私有raw。此profile本轮尚未实测，不保证修复。

进一步需要实时被动USB PRODUCT事件及上传后内部状态证据，区分未执行、仍执行但通路变化及事件时序问题；不能仅凭无KIS日志、Possibly invalid iBSS或换线反馈定因。

## 取证与冻结

原始sudo命令与历史内核时序保存在ignored raw的restore-command-audit-20260914-{success-and-prior-failure,current,success-kernel}.txt。03:53另曾核对本机1281 Recovery，但原始shell未得到boot-stage/build-version；随后用户重新进入Port，诊断query open=-1，未获得报告，也未从Recovery执行Erase，不能称为成功续接远程Stage1。

04:00 UTC核对无idevicerestore/kisd/irecovery或Erase等待器，本轮仅审计、离线Manifest比较与文档更新，无新增上传。三次失败细节另见DFU_ERASE_20260914.md。
