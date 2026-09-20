#!/bin/sh
set -eu

field() {
    diskutil info -plist "$1" | plutil -extract "$2" raw -o - -
}

[ "$(sysctl -n hw.model)" = Mac16,12 ]
[ "$(sw_vers -buildVersion)" = 25G83 ]
[ "$(field disk0s1 DiskUUID)" = 2935ACB5-2A69-4996-942A-87B29BC17A2F ]
[ "$(field disk0s3 DiskUUID)" = 7EAA30B1-3DD4-417C-AC72-420E041C97AF ]
[ "$(field disk0s2 DiskUUID)" = 3061EB66-E660-4A0F-BC7C-40A8208BA396 ]
[ "$(field disk0s2 TotalSize)" = 1995218165760 ]
[ "$(diskutil apfs list -plist disk3 | plutil -extract Containers.0.APFSContainerUUID raw -o - -)" = D3A4EF6C-BA92-4923-875E-A4D00E89AE29 ]
diskutil apfs resizeContainer disk3 limits
if [ "${1:-}" != --apply ]; then
    echo 'Plan: retain 128 GB macOS; create 4 GB APFS stub and 1 GB unformatted EFI; leave remaining space free.'
    exit 0
fi
diskutil apfs resizeContainer disk3 128g
[ "$(field disk0s2 TotalSize)" = 128000000000 ]
diskutil addPartition disk0s2 APFS 'M4 Linux Bootstrap - Data' 4g
diskutil list internal
diskutil apfs list
echo 'Shrink and stub container created. Resolve new partition identities before adding roles and EFI.'
