#!/bin/sh
set -eu

[ "$(sysctl -n hw.model)" = Mac16,12 ]
[ "$(diskutil info -plist disk0s4 | plutil -extract DiskUUID raw -o - -)" = EC26EDE8-57A3-4AF7-B303-B198E5DC98EA ]
[ "$(diskutil info -plist disk0s4 | plutil -extract TotalSize raw -o - -)" = 1990083952640 ]
[ "$(diskutil info -plist disk0s5 | plutil -extract DiskUUID raw -o - -)" = B4B16301-9191-4810-96A1-12DD3EC04F3A ]
[ "$(diskutil info -plist disk0s1 | plutil -extract DiskUUID raw -o - -)" = 3DEC5A4D-2326-42C9-BA96-11F889C3C9E6 ]
[ "$(diskutil info -plist disk0s3 | plutil -extract DiskUUID raw -o - -)" = BFF7DCE8-D66B-43D1-8E06-40B23050FF5C ]
if [ "${1:-}" != --apply ]; then
    echo 'Plan: replace the empty Linux extent with 128 GB temporary APFS and remaining Linux space.'
    exit 0
fi
diskutil eraseVolume free free disk0s4
diskutil addPartition disk0s5 APFS 'M4 Install Assets' 128g
diskutil list internal
diskutil apfs list
