{
  vscode-utils,
  fetchurl,
  python3,
  antigravity-cli,
  lib,
}:

vscode-utils.buildVscodeMarketplaceExtension {
  mktplcRef = {
    name = "google-antigravity";
    publisher = "google";
    version = "1.13.0";
  };

  vsix = fetchurl {
    url = "https://open-vsx.org/api/Google/google-antigravity/1.13.0/file/Google.google-antigravity-1.13.0.vsix";
    hash = "sha256-t4b7bsG6v9t7LD5ayr2VFINTnSh5I6Y82n4BV7zwRwQ=";
  };

  nativeBuildInputs = [ python3 ];

  postPatch = ''
    python3 ${../../scripts/patch.py} vscode extension.js \
      --fallback-bin "${lib.getExe antigravity-cli}"
  '';

  meta = {
    description = "Patched Google Antigravity VS Code extension";
    homepage = "https://open-vsx.org/extension/Google/google-antigravity";
    license = lib.licenses.unfree;
    platforms = lib.platforms.linux ++ lib.platforms.darwin;
  };
}
