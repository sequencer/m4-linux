#!/bin/sh
set -eu

source_preboot=3832D3A5-ACD2-4035-BB69-39F53DADCF3E
target_preboot=95599825-AB91-406C-8363-70A5F2B89DAE
source_group=1E95E303-A64C-414F-9338-4FBD9815230E
target_group=0F4B67C2-B48A-4F7F-B324-B02EB3362E5A

mount_path() {
    diskutil info -plist "$1" | plutil -extract MountPoint raw -o - -
}

source_mount=$(mount_path "$source_preboot")
target_mount=$(mount_path "$target_preboot")
test "$source_mount" != "$target_mount"
source_admin="$source_mount/$source_group/var/db/AdminUserRecoveryInfo.plist"
target_admin="$target_mount/$target_group/var/db/AdminUserRecoveryInfo.plist"
test -s "$source_admin"
test -f "$target_mount/$target_group/restore/BuildManifest.plist"
if test -e "$target_admin"; then
    test "$(cksum < "$source_admin")" = "$(cksum < "$target_admin")"
fi
test "$(plutil -extract ProductBuildVersion raw -o - "$target_mount/$target_group/restore/BuildManifest.plist")" = 25G83
mkdir -p "$(dirname "$target_admin")"
if test ! -e "$target_admin"; then
    cp -p "$source_admin" "$target_admin"
fi
test "$(cksum < "$source_admin")" = "$(cksum < "$target_admin")"
chflags schg "$target_admin"

diskutil unmount "$source_preboot"
diskutil unmount "$target_preboot"
diskutil mount "$target_preboot"
test "$(mount_path "$target_preboot")" = /Volumes/Preboot
test -f "/Volumes/M4 Linux Bootstrap/restore/BuildManifest.plist"
diskutil mount "$source_preboot"
sync
printf '%s\n' 'Owner recovery metadata copied; stub restore link resolves. No policy change performed.'
