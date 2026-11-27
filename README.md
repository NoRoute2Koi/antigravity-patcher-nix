# antigravity-patcher-nix

Nix / NixOS and Home Manager adaptation of Antigravity Patcher using a pure Python patcher script.

## Features

- Nixpkgs overlay patching:
  - `pkgs.antigravity-cli` (`agy`) with eligibility/auth gates bypassed and auto-updater neutralized
  - `pkgs.antigravity-ide` (and `pkgs.antigravity` alias), including Electron `main.js` and `language_server` (when present)
  - `pkgs.vscode-extensions.antigravity-patched` (`Google.google-antigravity` v1.13.0)
- Home Manager module (`homeManagerModules.default`) for integrating with `programs.antigravity`, `programs.antigravity-cli`, and VS Code / VSCodium.
- Standalone `./patch-vsix.sh` script to download and patch the VS Code extension `.vsix` directly from the repository directory.

## Flake Usage

### 1. Apply the Overlay

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    antigravity-patcher.url = "github:NoRoute2Koi/antigravity-patcher-nix";
  };

  outputs = { nixpkgs, inputs, ... }: {
    # Add to nixpkgs.overlays in NixOS or Home Manager:
    # nixpkgs.overlays = [ inputs.antigravity-patcher.overlays.default ];
  };
}
```

### 2. Home Manager Configuration

```nix
{ pkgs, inputs, ... }:
{
  imports = [
    inputs.antigravity-patcher.homeManagerModules.default
  ];

  nixpkgs.overlays = [
    inputs.antigravity-patcher.overlays.default
  ];

  programs.antigravity = {
    enable = true;
    package = pkgs.antigravity-ide;
  };

  programs.antigravity-cli = {
    enable = true;
    package = pkgs.antigravity-cli;
  };

  programs.antigravity-patcher = {
    enable = true;
    linkGeminiBinary = true;
    clearIdeCaches = true;
  };

  programs.vscodium.profiles.default.extensions = [
    pkgs.vscode-extensions.antigravity-patched
  ];
}
```

### Module Options (`programs.antigravity-patcher`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable` | bool | `false` | Enables Home Manager integration. |
| `cliPackage` | package or null | `programs.antigravity-cli.package` or `pkgs.antigravity-cli` | Patched CLI package linked to `~/.gemini/bin/agy`. |
| `linkGeminiBinary` | bool | `true` | Links `~/.gemini/bin/agy` to the patched `agy` binary. |
| `clearIdeCaches` | bool | `true` | Clears stale Electron/V8 caches when `programs.antigravity.package` changes. |

## Standalone VSIX Patcher

To download and patch `Google.google-antigravity` (`1.13.0`) as a `.vsix` file in the current directory:

```bash
./patch-vsix.sh
```

Or specify a custom output path:

```bash
./patch-vsix.sh ./my-patched.vsix
```

Required tools (`curl`, `unzip`, `zip`, `python3`) are provided via `shell.nix`:

```bash
nix-shell --run ./patch-vsix.sh
```

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

