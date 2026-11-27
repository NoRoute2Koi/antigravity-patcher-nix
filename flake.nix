{
  description = "Nix / NixOS adaptation of Antigravity Patcher";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      forAllSystems =
        f:
        nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            inherit system;
            pkgs = import nixpkgs {
              inherit system;
              config.allowUnfree = true;
              overlays = [ self.overlays.default ];
            };
          }
        );
    in
    {
      overlays.default = import ./overlays/default.nix;

      homeManagerModules.default = import ./modules/home-manager.nix;

      packages = forAllSystems (
        { pkgs, ... }:
        {
          default = pkgs.antigravity-cli;
          inherit (pkgs)
            antigravity-cli
            antigravity-ide
            ;
          vscode-extension-antigravity-patched = pkgs.vscode-extensions.antigravity-patched;
        }
      );

      devShells = forAllSystems (
        { pkgs, ... }:
        {
          default = import ./shell.nix { inherit pkgs; };
        }
      );
    };
}
