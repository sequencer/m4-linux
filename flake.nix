{
  description = "Reproducible M4 Apple Silicon Linux bring-up workspace";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    rust-overlay.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, rust-overlay }:
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
                cp -r proxyclient $out/share/m1n1-sptm/
              '';
            };
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
