# iBoot 控制协议实测（22:50–22:56 UTC）

## 现场与只读对照

用户确认仍为 restore 网页后，直接连接本机固件 Recovery，读取到 `Local boot`、`Microkernel iBootStage1 for j713`、`mBoot-18000.161.10`。保存的965字节控制台 SHA256 为 `3fc73ebbde403e0d1dc4d7ddb54e115a201abe78d8bd6508eaeddccb8e654de1`。

新增 `scripts/query-iboot-diagnostics.py`，默认只向固定主ECID目标发送允许列表中的 `getenv` 查询并收集控制台；校验 CPID8132/BDID2c/主ECID和Recovery模式，禁止默认发送启动或写命令。所有原始输出在忽略的raw目录，输出目录权限0700。

第一次调用库的 `irecv_getenv`：状态0但所有值为空。改用原始USB控制传输后发现：在 `irecv_receive` 之前没有问题，先收控制台却会使随后查询全部返回libusb IO错误-1。库的receive会切换interface1/alt1，再切回interface0；该时序与查询失败有关，本轮仅证明对照结果，不宣称已定位内核或固件中的完整机制。

先查询、后收控制台的实测结果：

| 查询 | 发送结果 | 接收结果 | 值 |
| --- | --- | --- | --- |
| boot-stage | 18/18字节 | 2字节 | 1 |
| build-version | 21/21字节 | 19字节 | mBoot-18000.161.10 |
| auto-boot | 17/17字节 | 6字节 | false |
| boot-command | 20/20字节 | 7字节 | fsboot |
| boot-args | -9 | 未接收 | 无有效值 |
| recovery-mode | -9 | 未接收 | 无有效值 |
| saved-debug-info | -9 | 未接收 | 无有效值 |

libusb的-9是PIPE，不能与libirecovery自己的错误码-9混淆。后3个查询失败不能写成“变量确实为空”或“获得了SavedDebugInfo”。

## 恢复自动启动与尝试原生启动

此前工具准备阶段确实执行 `setenv auto-boot false`/`saveenv`；本次读回false，是必须清理的实验状态，但原初启动失败发生在这轮临时加载之前，不能全部归因于它。

显式运行：

```sh
sudo -n nix develop --command timeout 40s python scripts/query-iboot-diagnostics.py \
  --restore-autoboot-and-fsboot \
  --output experiments/2026-09-13-iokit-ram-root/raw/iboot-autoboot-repair-1
```

实测 `setenv auto-boot true`返回22/22字节，`saveenv`返回8/8字节；随后 `fsboot`返回PIPE -9。末次nonce变化，稍后USB目标消失，Recovery SSH No route to host。不能根据命令已发送断言自动启动状态持久化成功或原生启动修复；尚未完成重连后的读回。后续脚本已增加saveenv后读回true的前置验收及失败时保留诊断，避免无验收就继续启动。

此过程未发送Erase/StartRestore，未重复完整Revive或iBSS上传；确实修改了启动变量，不能称为零写入。当前没有后台恢复加载/监听进程，等待设备重新出现和屏幕反馈后才能继续硬件操作。

## 主机工具补丁与因果边界

- 固定上游libirecovery的 `irecv_send_command_raw`忽略USB控制传输返回值，`irecv_getenv`/`irecv_getret`也忽略响应读取错误，造成状态0并不代表传输成功。新增Nix包 `dfu-command-diagnostic-tools`保留并报告实际命令/响应错误；`firmware-diagnostic-tools`改为链接它。构建成功，主ECID及Update/禁止Erase守卫在产物中仍存在。该版尚无设备重新连入后的加载实测。
- 发现nonce变化时原DFU路径只重签AP票据，LocalPolicy仍可绑定旧nonce和旧AP票据哈希。诊断包已在AP重签后同步重签LocalPolicy及RecoveryOS root ticket。独立只读审查确认缺陷，但已检查的此前失败日志没有触发该分支，不能称为这些失败的已证实根因。
- 曾怀疑goto缺锁；进一步对照确认nonce段原本unlocked，固件上传前已有锁，goto前加锁反而会double-lock。该尝试已撤回，包含它的中间构建从未运行在设备上。

验证：Nix构建完成；脚本AST语法检查通过；`git diff --check`通过。尚未有原生Recovery或实验guest GUI成功证据。

## 重连读回与后续观察（22:56–22:58 UTC）

设备重新枚举1281后，只读查询 `raw/iboot-after-autoboot-repair-2/manifest.json`取得 `auto-boot=true`（发送17字节、接收5字节），说明当前重连实例确实读回true，不再仅有命令发送证据。与此同时 `boot-command`变为 `recover-system`（发送20字节、接收15字节），不能把该状态描述为正常系统已启动，也不能推断具体BootPolicy根因。

新strict诊断loader45312发现设备阶段超时exit1，`raw/temporary-restore-strict-control-1.{log,stdout}`无任何组件上传；尚未完成新库控制命令传输的实机加载验证。随后60秒只查询、禁用console接口切换的监听15129退出1，没有取得新的稳定1281查询。曾短暂观察05ac:1905，稍后再次断开，主机仍有ATCPHY pipehandler lock及端口控制器重建事件。没有USB网络接口或可用Recovery SSH证据，不能把1905解释为GUI或恢复完成。

当前所有主动加载/监听进程已结束，没有再次改回auto-bootfalse；实际屏幕状态及稳定控制连接仍需确认。
