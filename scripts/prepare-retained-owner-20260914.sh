#!/bin/sh
set -eu

mount_path() {
    diskutil info -plist "$1" | plutil -extract MountPoint raw -o - -
}

[ "$(sysctl -n hw.model)" = Mac16,12 ]
source_mount=$(mount_path E37174ED-4371-4BA3-B783-368C544244C8)
target_mount=$(mount_path A0D1E0E5-0AE5-42C7-9FFA-872DF997C904)
[ "$source_mount" != "$target_mount" ]
[ "$target_mount" = /Volumes/Preboot ]
source_admin="$source_mount/742D07D7-4C78-4BAB-B4E1-D6F3B239A2D8/var/db/AdminUserRecoveryInfo.plist"
target_group="$target_mount/530FE39B-6AE3-47D0-9168-29F1A7EE2763"
target_admin="$target_group/var/db/AdminUserRecoveryInfo.plist"
test -s "$source_admin"
test ! -e "$target_admin"
[ "$(plutil -extract ProductBuildVersion raw -o - "$target_group/restore/BuildManifest.plist")" = 25G83 ]
test -f '/Volumes/M4 Linux Bootstrap/restore/BuildManifest.plist'
mkdir -p "$(dirname "$target_admin")"
cp -p "$source_admin" "$target_admin"
[ "$(cksum < "$source_admin")" = "$(cksum < "$target_admin")" ]
chflags schg "$target_admin"
sync
echo 'Copied current owner recovery metadata only; no old LocalPolicy or iSC restored.'
