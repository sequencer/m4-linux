# Linux DFU 成功后的 m1n1 重装

## 15:22:30 UTC：持久化 m1n1 启动及 USB 代理验收通过

用户物理选择新stub后，单次等待器触发并退出0。`experiments/2026-09-14-reinstall-retained/raw/post-erase-m1n1/proxy-check.json`记录串号M49KYH65C9、/dev/ttyACM0、uart_nop=ok、proxy_nop=ok；这是本轮新安装的实际结果，不是旧记录。

启动控制台确认Mac16,12/J713/CPID8132、Running in EL2、实际内存0x800000000（32GiB）、OS/System FW mBoot-18000.161.10，最后Running proxy。仍报告MCC unsupported mcc,t8132、cpufreq unsupported，以及No valid payload found；尚未提供Linux payload，不能把代理验收当作Linux或SPTM guest运行成功。

本轮没有启动guest、上传内核、读取旧iSC或再次重启。保持目标在m1n1代理待命；等待器已结束，不继续宣称后台监听中。物理选择前已恢复macOS默认启动，但启动后没有再次读取NVRAM，不推断选择动作是否改变默认值。原生macOS缩容/策略变更后及备用Recovery的独立回归仍待验收。

## 15:20 后：m1n1 启动对象已安装，等待代理启动验收

用户再次启动SSH后，实际确认新stub为Paired one true recoveryOS / Integrity Valid。通过交互菜单选择M4 Linux Bootstrap，csrutil disable成功；执行以下命令并经当前sequencer所有者认证，返回installing boot object / done，exit0：

```sh
kmutil configure-boot -c "/Volumes/M4 Linux Bootstrap/m1n1/boot.bin" \
  --raw --entry-point 2048 --lowest-virtual-address 0 \
  -v "/Volumes/M4 Linux Bootstrap"
bputil -c -a -s -v 083C641C-7DBA-44D7-9C86-7925CE0050DE
```

复读stub策略Permissive、sip0=7f、sip1/2/3=1、coih为445A4EE6F250B1386BB427F9E37E74FE61CCD96E343A09CC19644986D9BFFEDCF9173F2C6708B5C747B911DFFE5334B1，Paired/Valid；这只是读取策略字段，没有另算hash。Macintosh HD仍为Permissive、coih absent，两套SIP disabled。

bless --setBoot --mount "/Volumes/Macintosh HD" --user sequencer成功，boot-volume读回末段2D4EFB69，恢复原生默认启动；证据installed-policy.txt。随后已告知用户并正常shutdown-h。用户需长按电源进入启动选项，选择M4 Linux Bootstrap→继续，而非Options。

M1启动一次900秒等待器，识别两个1209:316d/串号M49KYH65C9端口后执行一次m1n1-check.py（45秒上限），结果预定为proxy-check.json；未实际生成成功结果前不得称USB代理已验收。只NOP检查、不上传guest或Linux。缩容/策略变更后的原生重启仍需独立验收。

## 15:15 后：连接恢复，策略生成，等待物理进入 stub 配对 Recovery

用户确认仍在Recovery，15:14:47同IP公钥SSH恢复；此前断开原因未确定，不记为重启/崩溃。继续复制本轮原生Preboot的AdminUserRecoveryInfo.plist到新stub，设置schg，成功；Bootable true，boot.bin1589248字节。没有重做分区或stage。

以本轮sequencer所有者交互认证执行 `bputil -g -v 083C641C-7DBA-44D7-9C86-7925CE0050DE`，退出0；新策略Reduced、Integrity Valid、coih absent，当前macOS Recovery对stub为Not Paired。执行 `bless --setBoot --mount "/Volumes/M4 Linux Bootstrap" --user sequencer` 成功；nvram读回boot-volume末段为新stub卷组083C641C。证据owner-stage-resumed.txt与pre-pairing-policy.txt。

为进入新stub配对1TR，已告知用户并通过SSH发送 `sync; shutdown -h now`；必须由用户物理长按电源进入启动选项，再选Options，若出现恢复安装目标则选M4 Linux Bootstrap。重新启动SSH后先核对bputil的Paired与Valid，再执行stub的csrutil/kmutil；目前尚未安装自定义启动对象、未运行m1n1/guest。最终安装后计划恢复macOS默认启动。

## 最新：文件部署完成，SSH 中断，尚未安装启动对象

stage脚本实机退出0，stage.txt确认新group/container与25G83、file_hashes_verified_this_run=false。boot.bin已由固定Nix构建覆盖；System/Preboot/Recovery资源已放置、APFS bootable flag已设置。没有计算hash。

随后两次SSH（当前所有者恢复元数据复制、bputil -g）均在TCP连接阶段超时，未执行远端命令；owner-stage.txt为空。15:08:14本机内核记录目标USB断开，之后lsusb只有root hubs。172.24.5.124仍回应ping但22端口再次超时，不足以判断目标已重启、崩溃或仅网络/sshd中断。本次没有发出重启/关机命令。

下一步先恢复Recovery SSH，再核对现场，复制当前AdminUserRecoveryInfo并新建stub策略。尚未bless、kmutil、进入stub配对Recovery或启动代理；不要将文件部署成功称为m1n1安装完成，也不要重跑分区/已经完成的stage步骤。

## 范围

2026-09-14 14:49完整Erase成功、用户确认原生启动后，在新macOS配对1TR中重新安装独立stub。只安装m1n1，不启动macOS guest；当前无Linux内核/驱动安装。原生macOS已按用户授权设为Permissive，SIP/SSV/CTRR/启动参数过滤关闭。

## 本轮布局

- 原生macOS容器：EFE517FC-C64B-426F-B6D7-6F3B5E368494，128000000000字节，卷组2D4EFB69-013E-4618-997E-3AFDB3F1E2E5。
- iSC物理分区：E1287E4C-E723-4430-9B36-1665709384F5，524288000字节；系统Recovery：F6774DEA-C3E3-4CF9-B44A-6BD88F877799，5368664064字节。两者保留。
- 新stub容器：35889682-832A-4C38-B203-CEB519680D69，3999997952字节；物理分区0C1B6A6C-C322-4C03-BBFE-D5656AF8BB5A，本次disk0s5。
- stub卷组/Data：083C641C-7DBA-44D7-9C86-7925CE0050DE；System：E36EC8D5-7560-483B-9B4D-845E60341CA2。
- stub Preboot：83CE4E43-AE9A-4439-9989-E8E273971215；Recovery：1392CDD9-62D3-43EC-AC7C-DB3AE9A54F27。
- 另建1GB EFI分区，暂不格式化，其余留作Linux未分配空间。

缩容期间diskutil自带fsck_apfs退出0、现有卷检查通过。原System基础卷显示Sealed Broken，安全策略修改后尚未重新验收原生启动；不能仅据此判断损坏或认为缩容后已验证正常。

## 执行记录

原始记录：`experiments/2026-09-14-reinstall-retained/raw/post-erase-m1n1/`，layout-1.txt与layout-2.txt为实际分区输出。先前所有retained脚本内的固定UUID属于历史，未直接执行。

```sh
diskutil apfs resizeContainer disk3 128g
diskutil addPartition disk0s2 APFS 'M4 Linux Bootstrap - Data' 4g
diskutil apfs changeVolumeRole disk6s1 D
diskutil apfs addVolume disk6 APFS 'M4 Linux Bootstrap' -role S -groupWith disk6s1
diskutil apfs addVolume disk6 APFS Preboot -role B
diskutil apfs addVolume disk6 APFS Recovery -role R
diskutil addPartition disk0s5 %EFI% %noformat% 1g
```

设备编号仅对本阶段有效，重启后必须重新按UUID定位。

## 资源部署

复用固定Apple 25G83公共资源归档`artifacts/apple/25G83/stub-update.tar`，不用其中旧update-plan作为部署目标。`restore/apticket.j713ap.im4m`由prepare-stub-firmware.py从官方IPSW的`Firmware/Manifests/restore/macOS Customer/`提取，是公共资源，不是旧设备Preboot的个性化票据。旧iSC/LocalPolicy不复制。

boot.bin另外从`result/share/m1n1-sptm/m1n1.bin`传入，覆盖归档中的副本；Nix固定PR提交7e43bb1763ff97d661bbddb213596eda9475ae6a及项目已有补丁。Recovery Python取自Nix固定asahi-installer-archive v0.9.1，配置DYLD_FRAMEWORK_PATH和DYLD_LIBRARY_PATH，不运行官方不支持M4的安装入口。

stage-linux-only-stub.py新增显式group/container参数及skip-file-hashes，不再以历史UUID直接调用CLI；本轮不计算hash。旧Python wrapper调用方式保留。传输及部署尚待实际结果更新，不将文件准备当作kmutil安装完成。

```sh
DYLD_FRAMEWORK_PATH=/tmp/m4-installer/Frameworks \
DYLD_LIBRARY_PATH=/tmp/m4-installer/Frameworks/Python.framework/Versions/Current/lib \
/tmp/m4-installer/Frameworks/Python.framework/Versions/Current/bin/python3 \
  /tmp/m4-installer/stage-linux-only-stub.py \
  --group 083C641C-7DBA-44D7-9C86-7925CE0050DE \
  --container 35889682-832A-4C38-B203-CEB519680D69 --skip-file-hashes
```

后续需要当前所有者恢复元数据、新生成LocalPolicy以及stub配对1TR，不用旧备份替代。暂未设置新默认启动项或执行kmutil。
