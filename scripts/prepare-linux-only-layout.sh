#!/bin/sh
set -eu

[ "$(sysctl -n hw.model)" = Mac16,12 ]
[ "$(diskutil info -plist disk0s1 | plutil -extract DiskUUID raw -o - -)" = 3DEC5A4D-2326-42C9-BA96-11F889C3C9E6 ]
[ "$(diskutil info -plist disk0s3 | plutil -extract DiskUUID raw -o - -)" = BFF7DCE8-D66B-43D1-8E06-40B23050FF5C ]
if diskutil info disk0s2 >/dev/null 2>&1; then
    echo 'Expected empty former macOS partition; refusing to run again.' >&2
    exit 1
fi
diskutil list internal
if [ "${1:-}" != --apply ]; then
    echo 'Plan: 4 GB APFS boot stub, 1 GB EFI, remaining free extent Linux filesystem partition.'
    exit 0
fi
diskutil addPartition disk0s1 APFS 'M4 Linux Bootstrap - Data' 4g
container=$(diskutil info -plist disk0s2 | plutil -extract APFSContainerReference raw -o - -)
data_volume=$(diskutil apfs list -plist "$container" | plutil -extract Containers.0.Volumes.0.DeviceIdentifier raw -o - -)
diskutil apfs changeVolumeRole "$data_volume" D
diskutil apfs addVolume "$container" APFS 'M4 Linux Bootstrap' -role S -groupWith "$data_volume"
diskutil apfs addVolume "$container" APFS Preboot -role B
diskutil apfs addVolume "$container" APFS Recovery -role R
diskutil addPartition disk0s2 %EFI% %noformat% 1g
diskutil list internal
echo 'EFI created unformatted. Resolve its UUID before allocating the remaining Linux extent.'
diskutil apfs listVolumeGroups "$container"
