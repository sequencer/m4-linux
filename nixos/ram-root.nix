{ config, lib, pkgs, modulesPath, kisModule, debugModules, ... }:
{
  imports = [ "${modulesPath}/profiles/minimal.nix" ];

  system.stateVersion = "26.05";
  networking.hostName = "m4-linux";
  networking.useDHCP = false;
  networking.firewall.enable = false;
  networking.wireless.enable = false;
  services.openssh.enable = false;
  services.udisks2.enable = false;
  services.timesyncd.enable = false;
  nix.enable = false;

  boot.kernel.enable = false;
  boot.initrd.enable = false;
  boot.loader.grub.enable = false;
  boot.kernelModules = lib.mkForce [ ];
  boot.kernel.sysctl."kernel.printk" = "1 4 1 7";
  boot.tmp.useTmpfs = true;
  system.modulesTree = [ debugModules kisModule ];
  system.systemBuilderCommands = ''
    ln -s ${config.system.modulesTree} $out/kernel-modules
  '';

  fileSystems."/" = {
    device = "tmpfs";
    fsType = "tmpfs";
    options = [ "mode=0755" ];
  };
  fileSystems."/nix/store" = {
    device = "/run/nix-store.squashfs";
    fsType = "squashfs";
    options = [ "loop" "ro" "nodev" "nosuid" ];
    neededForBoot = true;
  };

  users.mutableUsers = false;
  users.users.root.hashedPassword = "";
  services.getty.autologinUser = null;
  services.getty.helpLine = "KIS RAM system: log in as root (no password). Changes are lost on reboot.";
  systemd.services."serial-getty@ttyKIS0".wantedBy = [ "getty.target" ];
  systemd.services."getty@tty1".wantedBy = [ "getty.target" ];
  systemd.settings.Manager.ShowStatus = false;

  environment.systemPackages = with pkgs; [ nano less procps util-linux kmod ];
}
