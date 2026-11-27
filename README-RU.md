# antigravity-patcher-nix

Адаптация Antigravity Patcher для Nix / NixOS и Home Manager на базе Python-скрипта патчинга.

## Возможности

- Overlay для `nixpkgs`, предоставляющий пропатченные пакеты:
  - `pkgs.antigravity-cli` (`agy`) со снятыми проверками региона/авторизации и отключенным автообновлением
  - `pkgs.antigravity-ide` (и алиас `pkgs.antigravity`), включая `main.js` и `language_server` (если присутствует)
  - `pkgs.vscode-extensions.antigravity-patched` (`Google.google-antigravity` v1.13.0)
- Модуль Home Manager (`homeManagerModules.default`) для интеграции с `programs.antigravity`, `programs.antigravity-cli` и VS Code / VSCodium.
- Скрипт `./patch-vsix.sh` для скачивания и патчинга `.vsix` расширения VS Code прямо из папки проекта.

## Использование через Flake

### 1. Подключение overlay

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    antigravity-patcher.url = "github:NoRoute2Koi/antigravity-patcher-nix";
  };

  outputs = { nixpkgs, inputs, ... }: {
    # Добавьте в nixpkgs.overlays в NixOS или Home Manager:
    # nixpkgs.overlays = [ inputs.antigravity-patcher.overlays.default ];
  };
}
```

### 2. Конфигурация Home Manager

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

### Опции модуля (`programs.antigravity-patcher`)

| Опция | Тип | По умолчанию | Описание |
|-------|-----|--------------|----------|
| `enable` | bool | `false` | Включает интеграцию патчера в Home Manager. |
| `cliPackage` | package или null | `programs.antigravity-cli.package` или `pkgs.antigravity-cli` | Пропатченный пакет CLI для ссылки `~/.gemini/bin/agy`. |
| `linkGeminiBinary` | bool | `true` | Создает ссылку `~/.gemini/bin/agy` на пропатченный `agy`. |
| `clearIdeCaches` | bool | `true` | Очищает кэш Electron/V8 при смене `programs.antigravity.package`. |

## Автономный патчинг VSIX

Чтобы скачать и пропатчить расширение `Google.google-antigravity` (`1.13.0`) прямо из папки проекта:

```bash
./patch-vsix.sh
```

Или с указанием пути выходного файла:

```bash
./patch-vsix.sh ./my-patched.vsix
```

Необходимые зависимости (`curl`, `unzip`, `zip`, `python3`) описаны в `shell.nix`:

```bash
nix-shell --run ./patch-vsix.sh
```

## Лицензия

Проект распространяется под лицензией GNU General Public License v3.0. Подробности см. в [LICENSE](LICENSE).

