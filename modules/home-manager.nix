{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.antigravity-patcher;

  idePkg =
    if config.programs.antigravity.enable && config.programs.antigravity.package != null then
      config.programs.antigravity.package
    else
      null;

  configBaseDir =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "${config.home.homeDirectory}/Library/Application Support"
    else
      config.xdg.configHome;

  cacheStampFile = "${config.xdg.cacheHome}/antigravity-patcher/ide-store-path";
in
{
  options.programs.antigravity-patcher = {
    enable = lib.mkEnableOption "Antigravity Patcher Home Manager integration";

    cliPackage = lib.mkOption {
      type = lib.types.nullOr lib.types.package;
      default =
        if config.programs.antigravity-cli.enable then
          config.programs.antigravity-cli.package
        else
          pkgs.antigravity-cli;
      defaultText = lib.literalExpression ''
        if config.programs.antigravity-cli.enable then
          config.programs.antigravity-cli.package
        else
          pkgs.antigravity-cli
      '';
      description = ''
        Patched antigravity-cli package to expose at ~/.gemini/bin/agy
        for the Antigravity VS Code extension.
      '';
    };

    linkGeminiBinary = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Whether to link the patched `agy` binary to `~/.gemini/bin/agy`
        so the VS Code / VSCodium extension uses it without downloading.
      '';
    };

    clearIdeCaches = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Whether to clear stale Electron/V8 caches when `programs.antigravity.package`
        changes, matching upstream patcher behavior.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    home.file = lib.mkIf (cfg.linkGeminiBinary && cfg.cliPackage != null) {
      ".gemini/bin/agy".source = lib.getExe cfg.cliPackage;
    };

    home.activation.antigravityPatcherClearCaches = lib.mkIf (cfg.clearIdeCaches && idePkg != null) (
      lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        stamp_file=${lib.escapeShellArg cacheStampFile}
        current_pkg=${lib.escapeShellArg (toString idePkg)}
        prev_pkg=""
        if [ -f "$stamp_file" ]; then
          prev_pkg="$(cat "$stamp_file")"
        fi
        if [ "$prev_pkg" != "$current_pkg" ]; then
          for app_name in "Antigravity IDE" "antigravity-ide" "Antigravity"; do
            base=${lib.escapeShellArg configBaseDir}/"$app_name"
            for sub in "CachedData" "Code Cache/js" "Code Cache" "Cache" "GPUCache"; do
              if [ -d "$base/$sub" ]; then
                run rm -rf "$base/$sub"
              fi
            done
          done
          run mkdir -p "$(dirname "$stamp_file")"
          printf '%s' "$current_pkg" > "$stamp_file"
        fi
      ''
    );
  };
}
