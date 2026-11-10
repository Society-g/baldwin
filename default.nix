{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "baldwin";
  version = "0.1.0";
  pyproject = true;
  src = pkgs.lib.cleanSource ./.;
  build-system = [ pkgs.python3Packages.setuptools ];
  dependencies = with pkgs.python3Packages; [ textual textual-image numpy pillow ];
  makeWrapperArgs = [ "--prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.playerctl pkgs.pipewire ]}" ];
  doCheck = false;
  meta.mainProgram = "baldwin";
}
