{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShell {
  packages = with pkgs; [
    curl
    nixfmt
    python3
    unzip
    zip
  ];
}
