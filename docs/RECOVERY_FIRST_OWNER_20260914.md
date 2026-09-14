# Recovery 首个账户与卷所有者调研

结论：没有找到已经验证、适用于 M4/25G83 最小 stub 的纯 Recovery 首个所有者创建步骤。这不等于架构上不可能，也不能据此声称必须再次 DFU Restore。当前实际选择是临时安装 macOS、创建本地管理员，再授权 stub。

## 账户并不等于启动策略所有者

必须区分 Recovery root、普通 Open Directory 管理员、secure token、卷所有者，以及用于签署 LocalPolicy 的 OIK。Apple 明确在出厂/有线 erase-install 的 restore 环境中创建 OIK；普通用户尚未配置，不能推出 OIK 不存在。新 stub 的 `diskutil apfs listUsers` 为空只能证明该卷没有枚举到 crypto users，不能证明整个设备的 OIK 存在性或绑定状态。

来源：[Apple OIK 初始化](https://support.apple.com/en-ie/guide/security/sec1f90fbad1/web)、[Apple secure token 与 volume ownership](https://support.apple.com/en-za/guide/deployment/dep24dbdcf9e/web)。

Apple 开源 `PreloginUserDb.m` 使用 APFSVolumeGetUnlockRecord 获取密钥记录；缺少 KEK 的用户被跳过，owner 属性来自 aks_fv_get_blob_state / aks_fv_state_is_owner，与管理员属性分开。因此仅写入账户、admin 组或恢复用户 plist，不构成已经建立密码学所有权的证据。该源码用于理解架构，不能直接当作 25G83 二进制逐行对应。

[固定 Apple 源码](https://github.com/apple-oss-distributions/Security/blob/db15acbe6a7f257a859ad9a3bb86097bfe0679d9/OSX/authd/PreloginUserDb.m#L849)。

## 有价值但尚未打通的分支

Apple 文档的 Install User 是把已有 OIK 交接给新 OS 的 KEK 流程。不复制普通用户时可以采用空密码，但不是通用空密码管理员，更不等于空 ACM context。尚未找到本机可直接调用、经过验证的首个 Install User 创建 CLI。

[Apple Ownership Handoff](https://support.apple.com/en-ie/guide/security/secc745a0845/web)。

25G83 Recovery 的 dyld cache `.01` 只读字符串检查确有 Install User unlock record 和 prime ownership 相关错误文本。这证明存在相关实现线索，不证明本机走过该分支或已成功交接。没有猜测私有函数原型并调用写入接口。

## 实机工具与限制

- `/usr/bin/dscl` 存在，但不能将普通目录账户创建当作卷所有者创建；本轮未执行账户写入。
- PATH 未找到 sysadminctl/fdesetup；没有通过复制二进制绕过依赖或授权。
- `/usr/sbin/resetpassword` 指向 filevaultRecovery。Apple 文档是已有账户密码恢复，不是无账户首个 owner 的已证实创建方案。
- `/usr/libexec/seputil --help` 没有提供可识别的首个 macOS 管理员创建入口。没有执行 SEP restore、nonce 操作、panic 或测试命令。
- `/usr/bin/bputil` 的只读字符串检查包含 authenticate_recovery_user_for_volume_group 和 no admin users authorized for recovery，与此前真实失败一致；未证明所有其他私有流程同样不可用。
- 删除 `.AppleSetupDone` 不会给当前无完整 macOS 的 stub 凭空生成 Setup Assistant；Apple 也说明 macOS 14 起已有本地用户时删除它不再重新启动设置助理。

[Apple 密码恢复](https://support.apple.com/en-om/102633)、[Apple Setup Assistant](https://support.apple.com/en-au/guide/deployment/depdeff4a547/web)。

## Asahi 实现的边界

安装器要求已有 machine-owner 管理员，拒绝无管理员或只有 `_mbsetupuser` 的情况，并提示先完成 macOS 初始设置。stub.py 复制已有 OS 的 AdminUserRecoveryInfo.plist，后续带现有凭据执行 bputil；没有实现首个 owner 的无 macOS 引导。

[Asahi 主流程](https://github.com/AsahiLinux/asahi-installer/blob/99dff2e968dafcabc2a940865b051e91ffcfafd3/src/main.py)、[stub 实现](https://github.com/AsahiLinux/asahi-installer/blob/99dff2e968dafcabc2a940865b051e91ffcfafd3/src/stub.py)。

后续若继续纯 Recovery 逆向，应先定位匹配版本中所有权状态的只读接口、Install User 初始化调用链及 entitlement，再设计受控实验；不能把修改 plist 后出现用户列表当成 m1n1 授权成功。
