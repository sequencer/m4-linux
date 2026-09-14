#!/bin/sh
set -eu

umask 077
mkdir -p /tmp/m4-ssh
chmod 700 /tmp/m4-ssh
curl -fL https://github.com/sequencer.keys -o /tmp/m4-ssh/authorized_keys.new
test -s /tmp/m4-ssh/authorized_keys.new
mv /tmp/m4-ssh/authorized_keys.new /tmp/m4-ssh/authorized_keys
if [ ! -f /tmp/m4-ssh/host_key ]; then
    curl -f http://172.25.27.108:8000/ssh_host_ed25519_key -o /tmp/m4-ssh/host_key.new
    test -s /tmp/m4-ssh/host_key.new
    mv /tmp/m4-ssh/host_key.new /tmp/m4-ssh/host_key
fi
chmod 600 /tmp/m4-ssh/host_key /tmp/m4-ssh/authorized_keys
exec /usr/sbin/sshd -D -e -f /dev/null \
    -h /tmp/m4-ssh/host_key -p 22 \
    -o UsePAM=no \
    -o PermitRootLogin=prohibit-password \
    -o PubkeyAuthentication=yes \
    -o PasswordAuthentication=no \
    -o KbdInteractiveAuthentication=no \
    -o AuthorizedKeysFile=/tmp/m4-ssh/authorized_keys \
    -o StrictModes=no \
    -o PidFile=/tmp/m4-ssh/sshd.pid
