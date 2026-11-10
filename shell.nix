{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: with ps; [ textual textual-image numpy pillow httpx pytest ]))
    pkgs.playerctl
    pkgs.pipewire
  ];
}
