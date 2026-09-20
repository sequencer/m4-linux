{
  description = "Reproducible M4 Apple Silicon Linux bring-up workspace";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    rust-overlay.inputs.nixpkgs.follows = "nixpkgs";
    m4-linux-modules = {
      url = "path:/nix/store/alqj6q1b3842j734xjm8lb3lji8i412q-linux-m4-7.1.13-modules";
      flake = false;
    };
    m4-linux-dev = {
      url = "path:/nix/store/kg1vifddf9jm3jy71ynd60913i2ihkv7-linux-m4-7.1.13-dev";
      flake = false;
    };
    gravity-bootloader-source = {
      url = "git+https://github.com/GravityLinux/bootloader.git?rev=ff7489ca80ed7d541c54aac23cb2beaaaf4d8766&submodules=1&shallow=1";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, rust-overlay, gravity-bootloader-source, m4-linux-modules, m4-linux-dev }:
    let
      systems = [ "aarch64-darwin" "aarch64-linux" "x86_64-linux" "x86_64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      overlays = [ rust-overlay.overlays.default ];
      pkgsFor = forAllSystems (system: import nixpkgs { inherit system overlays; });
      rustToolchainFor = system: pkgsFor.${system}.rust-bin.stable.latest.default.override {
        extensions = [ "rust-src" ];
        targets = [ "aarch64-unknown-none-softfloat" ];
      };
    in {
      nixosConfigurations.m4-ram = nixpkgs.lib.nixosSystem {
        system = "aarch64-linux";
        specialArgs = {
          kisModule = self.packages.aarch64-linux.kis-tty;
          debugModules = self.packages.aarch64-linux.linux-debug-modules;
        };
        modules = [
          ./nixos/ram-root.nix
          { nixpkgs.pkgs = pkgsFor.aarch64-linux; }
        ];
      };
      packages = forAllSystems (system:
        let
          pkgs = pkgsFor.${system};
          rustToolchain = rustToolchainFor system;
          base = {
            apple-m4-restore-25G83 = pkgs.fetchurl {
              url = "https://updates.cdn-apple.com/2026SummerFCS/fullrestores/140-75212/A2A24B94-1FC1-45A3-93F7-C51B02AF1F4D/UniversalMac_26.6.2_25G83_Restore.ipsw";
              hash = "sha256-iFUDt/SwZgnppRLyvv1A9ZcwZAo/EjPjiS1gr/3VHJU=";
            };
            apple-restore-catalog-20260913 = pkgs.fetchurl {
              url = "https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml";
              sha256 = "4259552631d29cbc6d3345e667af0d334cf31fe73b946c5babdda1e0244084da";
            };
            ipsw-tools = pkgs.ipsw;
            ram-root-tools = pkgs.dmg2img;
            apple-download-tools = pkgs.aria2;
            dfu-tools = pkgs.libirecovery;
            dfu-command-diagnostic-tools = pkgs.libirecovery.overrideAttrs (previous: {
              postPatch = (previous.postPatch or "") + ''
                substituteInPlace src/libirecovery.c \
                  --replace-fail 'irecv_usb_control_transfer(client, 0x40, b_request, 0, 0, (unsigned char*) command, length + 1, USB_TIMEOUT);' 'int transfer_result = irecv_usb_control_transfer(client, 0x40, b_request, 0, 0, (unsigned char*) command, length + 1, USB_TIMEOUT);
                    if (transfer_result != (int)(length + 1)) {
                        fprintf(stderr, "M4 diagnostic: command %s USB result %d, expected %u\\n", command, transfer_result, length + 1);
                        return IRECV_E_USB_UPLOAD;
                    }' \
                  --replace-fail 'irecv_usb_control_transfer(client, 0xC0, 0, 0, 0, (unsigned char*) response, rsize-1, USB_TIMEOUT);' 'int transfer_result = irecv_usb_control_transfer(client, 0xC0, 0, 0, 0, (unsigned char*) response, rsize-1, USB_TIMEOUT);
                    if (transfer_result < 0) {
                        fprintf(stderr, "M4 diagnostic: response USB result %d\\n", transfer_result);
                        free(response);
                        return IRECV_E_USB_STATUS;
                    }'
              '';
            });
            usbmuxd-tools = pkgs.usbmuxd;
            firmware-upstream-tools = pkgs.idevicerestore;
            dfu-kis-trace-tools = pkgs.libirecovery.overrideAttrs (previous: {
              postPatch = (previous.postPatch or "") + ''
                substituteInPlace src/libirecovery.c \
                  --replace-fail 'irecv_error_t err = irecv_usb_bulk_transfer(client, endpoint, (unsigned char *) req, reqSize, &sent, USB_TIMEOUT);' 'irecv_error_t err = irecv_usb_bulk_transfer(client, endpoint, (unsigned char *) req, reqSize, &sent, USB_TIMEOUT);
                    fprintf(stderr, "M4 KIS TX portal=%u index=0x%x requested=%zu sent=%d result=%d\n", req->portal, req->indexLo | ((req->indexHiRplSizeLo & 3) << 8), reqSize, sent, err);' \
                  --replace-fail 'err = irecv_usb_bulk_transfer(client, endpoint | 0x80, (unsigned char *) rpl, *rplSize, &rcvd, USB_TIMEOUT);' 'err = irecv_usb_bulk_transfer(client, endpoint | 0x80, (unsigned char *) rpl, *rplSize, &rcvd, USB_TIMEOUT);
                    fprintf(stderr, "M4 KIS RX portal=%u index=0x%x capacity=%zu received=%d result=%d\n", req->portal, req->indexLo | ((req->indexHiRplSizeLo & 3) << 8), *rplSize, rcvd, err);' \
                  --replace-fail 'err = irecv_kis_request(client, &req.hdr, sizeof(req), &rpl.hdr, &rplSize);' 'err = irecv_kis_request(client, &req.hdr, sizeof(req), &rpl.hdr, &rplSize);
                    fprintf(stderr, "M4 KIS WRITE32 portal=%u index=0x%x value=0x%x result=%d received=%zu expected=%zu size=%u status=%u\n", portal, index, value, err, rplSize, sizeof(rpl), rpl.size, rpl.status);'
              '';
            });
            firmware-kis-trace-tools = pkgs.idevicerestore.override {
              libirecovery = base.dfu-kis-trace-tools;
            };
            firmware-revive-tools = pkgs.idevicerestore.overrideAttrs (previous: {
              postPatch = (previous.postPatch or "") + ''
                substituteInPlace src/idevicerestore.c \
                  --replace-fail 'client->macos_variant = build_manifest_get_build_identity_for_model_with_variant' 'if (client->ecid != UINT64_C(0xA10A426B9001C)) {
                    logger(LL_ERROR, "M4 safety guard: unexpected main-chip ECID\\n");
                    return -1;
                }
                char *restore_behavior = NULL;
                plist_get_string_val(plist_access_path(build_identity, 2, "Info", "RestoreBehavior"), &restore_behavior);
                if ((client->flags & FLAG_ERASE) || !restore_behavior || strcmp(restore_behavior, "Update") != 0) {
                    logger(LL_ERROR, "M4 safety guard: refusing erase or non-Update build identity\\n");
                    free(restore_behavior);
                    return -1;
                }
                free(restore_behavior);
                client->macos_variant = build_manifest_get_build_identity_for_model_with_variant'
              '';
            });
            firmware-diagnostic-tools = (base.firmware-revive-tools.override {
              libirecovery = base.dfu-command-diagnostic-tools;
            }).overrideAttrs (previous: {
              postPatch = (previous.postPatch or "") + ''
                substituteInPlace src/idevicerestore.c \
                  --replace-fail 'if (client->mode == MODE_DFU) {' 'if (client->mode == MODE_RECOVERY && client->macos_variant && (client->flags & FLAG_NO_RESTORE)) {
                    logger(LL_ERROR, "M4 diagnostic: refusing initial Recovery; start from verified DFU for Remote iBSS, not Local boot\n");
                    return -1;
                }
                if (client->mode == MODE_DFU) {'
                substituteInPlace src/dfu.c \
                  --replace-fail 'if (dfu_send_command(client, "saveenv") < 0) {' 'if (!(client->flags & FLAG_NO_RESTORE) && dfu_send_command(client, "saveenv") < 0) {'
                substituteInPlace src/recovery.c \
                  --replace-fail 'recovery_error = irecv_send_command(client->recovery->client, "saveenv");' 'recovery_error = (client->flags & FLAG_NO_RESTORE) ? IRECV_E_SUCCESS : irecv_send_command(client->recovery->client, "saveenv");'
                substituteInPlace src/dfu.c \
                  --replace-fail 'logger(LL_ERROR, "Device did not disconnect. Possibly invalid iBSS. Reset device and try again.\n");' 'if (client->macos_variant && (client->flags & FLAG_NO_RESTORE)) {
                    irecv_client_t diagnostic_probe = NULL;
                    irecv_error_t diagnostic_open = irecv_open_with_ecid(&diagnostic_probe, client->ecid);
                    logger(LL_INFO, "M4 diagnostic: post-iBSS connection probe result=%d\n", diagnostic_open);
                    if (diagnostic_open == IRECV_E_SUCCESS) {
                        const struct irecv_device_info *diagnostic_info = irecv_get_device_info(diagnostic_probe);
                        int diagnostic_mode = 0;
                        irecv_error_t diagnostic_mode_result = irecv_get_mode(diagnostic_probe, &diagnostic_mode);
                        if (diagnostic_info && diagnostic_info->ecid == UINT64_C(0xA10A426B9001C) && diagnostic_info->cpid == 0x8132 && diagnostic_info->bdid == 0x2c) {
                            logger(LL_INFO, "M4 diagnostic: verified post-iBSS USB pid=0x%04x, backend mode=0x%04x, mode result=%d, serial=%s\n", diagnostic_info->pid, diagnostic_mode, diagnostic_mode_result, diagnostic_info->serial_string ? diagnostic_info->serial_string : "unavailable");
                            if (diagnostic_mode_result == IRECV_E_SUCCESS && diagnostic_mode >= IRECV_K_RECOVERY_MODE_1 && diagnostic_mode <= IRECV_K_RECOVERY_MODE_4) {
                                char *diagnostic_stage = NULL;
                                irecv_error_t diagnostic_stage_result = irecv_getenv(diagnostic_probe, "boot-stage", &diagnostic_stage);
                                logger(LL_INFO, "M4 diagnostic: post-iBSS boot-stage result=%d, value=%s\n", diagnostic_stage_result, diagnostic_stage ? diagnostic_stage : "unavailable");
                                free(diagnostic_stage);
                            }
                        } else {
                            logger(LL_ERROR, "M4 diagnostic: post-iBSS hardware identity mismatch; no further queries\n");
                        }
                        irecv_close(diagnostic_probe);
                    }
                }
                logger(LL_ERROR, "Device did not disconnect. Possibly invalid iBSS. Reset device and try again.\n");'
                substituteInPlace src/dfu.c \
                  --replace-fail 'fixup_tss(client->tss);' 'fixup_tss(client->tss);
                    if (client->macos_variant && (client->flags & FLAG_NO_RESTORE)) {
                        plist_free(client->tss_localpolicy);
                        client->tss_localpolicy = NULL;
                        if (get_local_policy_tss_response(client, build_identity, &client->tss_localpolicy) < 0) {
                            logger(LL_ERROR, "M4 diagnostic: nonce-bound LocalPolicy signing failed\\n");
                            return -1;
                        }
                        plist_free(client->tss_recoveryos_root_ticket);
                        client->tss_recoveryos_root_ticket = NULL;
                        if (get_recoveryos_root_ticket_tss_response(client, build_identity, &client->tss_recoveryos_root_ticket) < 0) {
                            logger(LL_ERROR, "M4 diagnostic: nonce-bound RecoveryOS signing failed\\n");
                            return -1;
                        }
                    }'
              '';
            });
            apple-base-system-key-25G83 = pkgs.fetchurl {
              name = "BaseSystem-25G83-fcs-key.pem";
              url = "https://wkms-public.apple.com/fcs-keys/iH707G4WnpWgYOxDeMRHQUtlbIsfVaeIA86lDBYsT2U=";
              sha256 = "6bd1353862950a98a06fdc4a19b94ce596ad71800786a0bee32e543a2b843122";
              curlOptsList = [ "--doh-url" "https://dns.google/dns-query" ];
            };
            asahi-installer-archive = pkgs.fetchurl {
              url = "https://cdn.asahilinux.org/installer/installer-v0.9.1.tar.gz";
              hash = "sha256-vFu8qdTFfN86QYxStrQCqErm23dt1a1VZA/bXRGe5LA=";
            };
            experiment-recorder = pkgs.writeShellApplication {
              name = "m4-experiment-record";
              runtimeInputs = with pkgs; [ coreutils git jq ];
              text = builtins.readFile ./scripts/record-experiment.sh;
            };
          };
          linux = pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
            nixos-rootfs = pkgs.callPackage "${nixpkgs}/nixos/lib/make-squashfs.nix" {
              storeContents = [ self.nixosConfigurations.m4-ram.config.system.build.toplevel ];
              comp = "zstd -Xcompression-level 6";
            };
            nixos-root-initramfs = pkgs.makeInitrd {
              contents = [
                { object = "${pkgs.pkgsStatic.busybox}/bin/busybox"; symlink = "/bin/busybox"; }
                { object = linux.nixos-rootfs; symlink = "/nix-store.squashfs"; }
                { object = "${linux.kis-tty}/lib/modules/7.1.13/extra/apple_kis_tty.ko"; symlink = "/apple_kis_tty.ko"; }
                {
                  object = pkgs.writeScript "m4-nixos-root-init" ''
                    #!/bin/busybox sh
                    /bin/busybox mkdir -p /bin /dev /proc /sys /newroot
                    /bin/busybox --install -s /bin
                    export PATH=/bin
                    mount -t devtmpfs devtmpfs /dev
                    mount -t proc proc /proc
                    mount -t sysfs sysfs /sys
                    insmod /apple_kis_tty.ko || exec sh
                    exec </dev/ttyKIS0 >/dev/ttyKIS0 2>&1
                    stty sane clocal -crtscts
                    mount -t tmpfs -o mode=0755 tmpfs /newroot || exec sh
                    mkdir -p /newroot/nix/store /newroot/dev /newroot/proc /newroot/sys /newroot/run
                    mount -t tmpfs -o mode=0755 tmpfs /newroot/run || exec sh
                    cp -L /nix-store.squashfs /newroot/run/nix-store.squashfs || exec sh
                    mount -t squashfs -o loop,ro,nodev,nosuid /newroot/run/nix-store.squashfs /newroot/nix/store || exec sh
                    mount --move /dev /newroot/dev
                    mount --move /proc /newroot/proc
                    mount --move /sys /newroot/sys
                    exec switch_root /newroot ${builtins.unsafeDiscardStringContext "${self.nixosConfigurations.m4-ram.config.system.build.toplevel}/init"}
                  '';
                  symlink = "/init";
                }
              ];
            };
            kis-tty = pkgs.stdenv.mkDerivation {
              pname = "m4-kis-tty";
              version = "0.1";
              src = ./drivers/kis-tty;
              nativeBuildInputs = [ pkgs.kmod pkgs.autoPatchelfHook ];
              buildInputs = [ pkgs.elfutils pkgs.zlib ];
              hardeningDisable = [ "all" ];
              buildPhase = ''
                cp -r ${m4-linux-dev}/lib/modules/7.1.13 "$TMPDIR/kernel"
                chmod -R u+w "$TMPDIR/kernel"
                autoPatchelf "$TMPDIR/kernel/build/scripts"
                substituteInPlace "$TMPDIR/kernel/build/Makefile" \
                  --replace-fail /nix/store/kg1vifddf9jm3jy71ynd60913i2ihkv7-linux-m4-7.1.13-dev/lib/modules/7.1.13 "$TMPDIR/kernel"
                make -C "$TMPDIR/kernel/build" M=$PWD ARCH=arm64 \
                  PAHOLE_VERSION=131 CONFIG_DEBUG_INFO_BTF_MODULES= modules
              '';
              installPhase = ''
                install -Dm644 apple_kis_tty.ko $out/lib/modules/7.1.13/extra/apple_kis_tty.ko
              '';
            };
            linux-debug-modules = pkgs.makeModulesClosure {
              kernel = {
                name = "linux-m4-7.1.13-modules";
                outPath = m4-linux-modules.outPath;
              };
              firmware = pkgs.runCommand "m4-debug-empty-firmware" { } "mkdir -p $out/lib/firmware";
              rootModules = [ "gpio-macsmc" "pinctrl-apple-gpio" "spmi-apple-controller" "apple-dart" ];
            };
            linux-debug-initramfs = pkgs.makeInitrd {
              contents = [
                { object = "${pkgs.pkgsStatic.busybox}/bin/busybox"; symlink = "/bin/busybox"; }
                { object = "${linux.linux-debug-modules}/lib/modules"; symlink = "/lib/modules"; }
                { object = "${pkgs.kmod}/bin/modprobe"; symlink = "/bin/modprobe"; }
                { object = "${linux.kis-tty}/lib/modules/7.1.13/extra/apple_kis_tty.ko"; symlink = "/apple_kis_tty.ko"; }
                {
                  object = pkgs.writeScript "m4-linux-debug-init" ''
                    #!/bin/busybox sh
                    /bin/busybox mkdir -p /bin /dev /proc /sys /tmp /run /etc /root/.ssh
                    /bin/busybox --install -s /bin
                    export PATH=/bin
                    mount -t devtmpfs devtmpfs /dev
                    mount -t proc proc /proc
                    mount -t sysfs sysfs /sys
                    mkdir -p /dev/pts /sys/kernel/debug
                    mount -t devpts devpts /dev/pts
                    mount -t debugfs debugfs /sys/kernel/debug
                    insmod /apple_kis_tty.ko || exec sh
                    stty -F /dev/ttyKIS0 sane clocal -crtscts
                    export TERM=vt100
                    export PS1='m4# '
                    echo 'ttyKIS0::respawn:/bin/sh -i' > /etc/inittab
                    for module in gpio-macsmc pinctrl-apple-gpio spmi-apple-controller apple-dart; do
                      modprobe "$module" 2>> /run/modules.log
                    done
                    exec /bin/busybox init
                  '';
                  symlink = "/init";
                }
              ];
            };
            linux-ram-initramfs = pkgs.makeInitrd {
              contents = [
                {
                  object = "${pkgs.pkgsStatic.busybox}/bin/busybox";
                  symlink = "/bin/busybox";
                }
                {
                  object = pkgs.writeScript "m4-linux-init" ''
                    #!/bin/busybox sh
                    /bin/busybox mkdir -p /bin /dev /proc /sys /tmp
                    /bin/busybox --install -s /bin
                    export PATH=/bin
                    mount -t devtmpfs devtmpfs /dev
                    mount -t proc proc /proc
                    mount -t sysfs sysfs /sys
                    exec </dev/console >/dev/console 2>&1
                    echo M4_LINUX_RAM_INIT_OK
                    uname -a
                    cat /proc/cmdline
                    cat /proc/meminfo
                    while true; do
                      echo M4_LINUX_RAM_ALIVE
                      cat /proc/uptime
                      sleep 10
                    done
                  '';
                  symlink = "/init";
                }
              ];
            };
            kisd = pkgs.rustPlatform.buildRustPackage {
              pname = "kisd";
              version = "1.1.0";
              src = pkgs.fetchFromGitHub {
                owner = "AsahiLinux";
                repo = "kisd";
                rev = "555c3b0d0e39e8a5ffaaa70d54452f263ac4df21";
                hash = "sha256-02EhiZ9XmkM0sRpsaxMswl3p18Y5xqXHI2vMoxcbPLw=";
              };
              cargoHash = "sha256-InJ0zfR00z8NyRc04ku1FO+jJSJB2eluelAZtlYpJc0=";
            };
            kisd-preserve-configuration = linux.kisd.overrideAttrs (previous: {
              postPatch = (previous.postPatch or "") + ''
                substituteInPlace src/main.rs \
                  --replace-fail 'device.set_configuration(1).await?;' 'if device.active_configuration().map(|configuration| configuration.configuration_value()).ok() != Some(1) {
                    device.set_configuration(1).await?;
                }'
              '';
            });
            tuxvdmtool = pkgs.rustPlatform.buildRustPackage {
              pname = "tuxvdmtool";
              version = "0.2.0";
              src = pkgs.fetchFromGitHub {
                owner = "AsahiLinux";
                repo = "tuxvdmtool";
                rev = "4f3fed6a8c7b6fc6f656efd8df7620b1dbcb30ee";
                hash = "sha256-dpdHSMNHxaTlr8JycvIw347HtMyWbjR0tTbEogg35bE=";
              };
              cargoHash = "sha256-bnBtchG87ya7nlf20Zv3htnZDN5jv29DKY+8nx5CK5o=";
            };
            m1n1-sptm = let
              src = pkgs.fetchFromGitHub {
                owner = "ADevWithAnIdea";
                repo = "m1n1";
                rev = "7e43bb1763ff97d661bbddb213596eda9475ae6a";
                hash = "sha256-fmgn23oUSIVvdvcWwV9u1UGswFmBnP+DM1mqijJHXFw=";
                fetchSubmodules = true;
              };
            in pkgs.stdenv.mkDerivation {
              pname = "m1n1-sptm";
              version = "pr-1-7e43bb1";
              inherit src;
              cargoDeps = pkgs.rustPlatform.fetchCargoVendor {
                src = "${src}/rust";
                hash = "sha256-/2JQ31pMHbNjZsIu2RLCWzNul/qzL1O2+XB3qdOEb2U=";
              };
              nativeBuildInputs = [
                pkgs.cargo
                rustToolchain
                pkgs.rustPlatform.cargoSetupHook
                pkgs.gnumake
              ];
              cargoRoot = "rust";
              postPatch = ''
                substituteInPlace proxyclient/m1n1/hv/__init__.py \
                  --replace-fail 'and not self.ctx.regs[0]' 'and self.ctx.regs[0] < (1 << 32)'
                substituteInPlace src/hv_sptm_init.c \
                  --replace-fail 'int node = adt_path_offset_trace(adt, "/arm-io/sart-ans", path);' 'int node = adt_path_offset_trace(adt, "/arm-io/sart-ans", path); if (node < 0) { printf("SPTM: skipping absent SART controller\\n"); return; }' \
                  --replace-fail 'int ans = adt_path_offset_trace(adt, "/arm-io/ans", ans_path);' 'int ans = adt_path_offset_trace(adt, "/arm-io/ans", ans_path); if (ans < 0) { printf("SPTM: skipping absent NVMe controller\\n"); return; }'
              '';
              buildPhase = ''
                make
              '';
              installPhase = ''
                mkdir -p $out/share/m1n1-sptm
                cp build/m1n1.bin build/m1n1.macho $out/share/m1n1-sptm/
                cp build/m1n1.elf build/m1n1-raw.elf $out/share/m1n1-sptm/
                cp -r proxyclient $out/share/m1n1-sptm/
              '';
            };
            gravity-bootloader = linux.m1n1-sptm.overrideAttrs (_: {
              pname = "gravity-bootloader";
              version = "ff7489c";
              src = gravity-bootloader-source;
              postPatch = "";
              patches = [ (pkgs.writeText "m4-atc-tunables.patch" ''
                diff --git a/src/kboot_atc.c b/src/kboot_atc.c
                --- a/src/kboot_atc.c
                +++ b/src/kboot_atc.c
                @@ -280,1 +280,2 @@
                     {"atc-phy,t8122", -1, NULL, 0},
                +    {"atc-phy,t8132", -1, NULL, 0},
                @@ -370,1 +371,5 @@
                -        adt_getprop(adt, adt_node, tunable_info->adt_name, &tunables_len);
                +        adt_getprop(adt, adt_node, tunable_info->adt_name, &tunables_len);
                +    if (!tunable_adt && adt_is_compatible_at(adt, adt_node, "atc-phy,t8132", 0) &&
                +        strcmp(tunable_info->adt_name, "tunable_ATC0AXI2AF") == 0) {
                +        tunable_adt = adt_getprop(adt, adt_node, "tunable_ATCAXI2AF", &tunables_len);
                +    }
                @@ -446,1 +452,2 @@
                -    if (adt_is_compatible_at(adt, adt_node, "atc-phy,t8122", 0)) {
                +    if (adt_is_compatible_at(adt, adt_node, "atc-phy,t8122", 0) ||
                +        adt_is_compatible_at(adt, adt_node, "atc-phy,t8132", 0)) {
              '') ];
              installPhase = ''
                mkdir -p $out/share/gravity-bootloader
                cp build/m1n1.bin build/m1n1.macho build/m1n1.elf build/m1n1-raw.elf $out/share/gravity-bootloader/
                cp -r proxyclient $out/share/gravity-bootloader/
              '';
            });
          };
        in base // linux // { default = self.packages.${system}.experiment-recorder; }
      );

      devShells = forAllSystems (system: {
        default = pkgsFor.${system}.mkShell {
          packages = with pkgsFor.${system}; [
            binutils
            coreutils
            curl
            cargo
            dtc
            dmg2img
            git
            gdb
            gptfdisk
            gh
            imagemagick
            libirecovery
            ipsw
            jq
            nix
            openssh
            picocom
            python3
            python3Packages.construct
            python3Packages.pyserial
            lzfse
            python3Packages.pyusb
            ripgrep
            sshpass
            usbutils
          ] ++ (if pkgsFor.${system}.stdenv.hostPlatform.isLinux then [
            pkgsFor.${system}.apfs-fuse
            pkgsFor.${system}.dosfstools
            pkgsFor.${system}.mtools
            pkgsFor.${system}.procps
            pkgsFor.${system}.util-linux
            (rustToolchainFor system)
            pkgsFor.${system}.pkgsCross.aarch64-multiplatform.stdenv.cc
            self.packages.${system}.kisd
            self.packages.${system}.tuxvdmtool
            self.packages.${system}.m1n1-sptm
            self.packages.${system}.firmware-upstream-tools
            self.packages.${system}.usbmuxd-tools
          ] else [ ]);
          shellHook = ''
            export M4_LINUX_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
            export M4_EXPERIMENTS="$M4_LINUX_ROOT/experiments"
            mkdir -p "$M4_EXPERIMENTS"
          '';
        };
      });
    };
}
