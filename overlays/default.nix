final: prev: {
  antigravity-cli = prev.antigravity-cli.overrideAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.python3 ];

    postInstall = (old.postInstall or "") + ''
      python3 ${../scripts/patch.py} agy "$out/bin/agy" --lock-update
    '';
  });

  antigravity-ide = prev.antigravity-ide.overrideAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.python3 ];

    postFixup =
      (old.postFixup or "")
      + (
        if final.stdenv.hostPlatform.isDarwin then
          ''
            app_dir="$out/Applications/Antigravity IDE.app/Contents/Resources/app"
          ''
        else
          ''
            app_dir="$out/lib/antigravity-ide/resources/app"
          ''
      )
      + ''
        python3 ${../scripts/patch.py} ide "$app_dir/out/main.js"

        shopt -s nullglob
        for bin in "$app_dir"/extensions/antigravity/bin/language_server*; do
          case "$bin" in
            *.agybak|*.bak) continue ;;
          esac
          if [ -f "$bin" ]; then
            python3 ${../scripts/patch.py} manager "$bin"
          fi
        done
      '';
  });

  antigravity = final.antigravity-ide;
  antigravity-fhs = final.antigravity-ide.fhs;
  antigravity-fhsWithPackages = final.antigravity-ide.fhsWithPackages;

  vscode-extensions = prev.vscode-extensions // {
    antigravity-patched = final.callPackage ../pkgs/vscode-extension-antigravity { };
  };
}
