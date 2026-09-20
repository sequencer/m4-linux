#!/bin/sh
set -eu
[ "$(sysctl -n hw.model)" = Mac16,12 ]
[ "$(diskutil info -plist disk0s5 | plutil -extract DiskUUID raw -o - -)" = F322BE9F-F630-400D-B965-EB29A87BC3F6 ]
[ "$(diskutil apfs list -plist disk6 | plutil -extract Containers.0.APFSContainerUUID raw -o - -)" = FCD42C83-7878-4C61-BE47-322972C988CC ]
[ "$(diskutil apfs list -plist disk6 | plutil -extract Containers.0.Volumes.0.APFSVolumeUUID raw -o - -)" = 530FE39B-6AE3-47D0-9168-29F1A7EE2763 ]
[ "$(diskutil apfs list -plist disk6 | plutil -extract Containers.0.Volumes json -o - - | tr -cd '{' | wc -c | tr -d ' ')" = 1 ]
diskutil apfs changeVolumeRole disk6s1 D
diskutil apfs addVolume disk6 APFS 'M4 Linux Bootstrap' -role S -groupWith disk6s1
diskutil apfs addVolume disk6 APFS Preboot -role B
diskutil apfs addVolume disk6 APFS Recovery -role R
diskutil addPartition disk0s5 %EFI% %noformat% 1g
diskutil list internal
diskutil apfs listVolumeGroups disk6
diskutil apfs list -plist disk6
