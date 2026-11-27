#!/usr/bin/env python3
"""Pure-Python patcher for Antigravity CLI, IDE, Manager, and VS Code extension."""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

UPDATER_URL = b"https://antigravity-cli-auto-updater-974169037036.us-central1.run.app"
DISABLED_URL = b"http://127.0.0.1:9999/disabled-auto-updater-server-url-disabled-block"

IDE_DONE = "resetIsTierGCPTos(),true"
IDE_RE = re.compile(r"(resetIsTierGCPTos\(\),)this\.[A-Za-z_$0-9]+\.isGoogleInternal")

UPSTREAM_INJECT = (
    "{const __primary=options.targetPathOverride||getInstalledTargetPath();"
    "const __candidates=[__primary,"
    "(0,path_1.join)((0,path_1.dirname)(__primary),'antigravity'+((0,path_1.extname)(__primary)||''))];"
    "for(const __p of __candidates){if(__p&&await pathExists(__p)){"
    "outputChannel.appendLine('[INSTALL] Existing binary found at '+__p+'. "
    "Skipping version check and re-download.');return __p;}}}"
)
UPSTREAM_PART1_RE = re.compile(
    r"""(outputChannel\s*\.\s*appendLine\s*\(\s*['"]\[INSTALL\]\s*Checking Antigravity releases[^'"]*['"]\s*\)\s*;?)"""
)
UPSTREAM_PART2_RE = re.compile(
    r"""const\s+isChannelChanged\s*=\s*manifestFetched\s*&&\s*lastInstalledUrl\s*!==\s*releaseBaseUrl\s*;"""
)
MIN_PART1_RE = re.compile(
    r"""(([A-Za-z_$][\w$]*)\.appendLine\(\s*["']\[INSTALL\]\s*Checking Antigravity releases\.\.\.["']\s*\);?)"""
)
MIN_CHANNEL_RE = re.compile(r"""let\s+([A-Za-z_$][\w$]*)=db&&\$c&&a&&!Rl&&!d;""")
MIN_REBUILD_RE = re.compile(
    r"""let\s+([A-Za-z_$][\w$]*)=db&&\$c&&!a&&qc!==void 0&&Kb\(qc,rb\)&&Kb\(rb,qc\)&&Dd!==void 0&&If!==void 0&&!Rl;"""
)
MIN_BC_RE = re.compile(r"""function Bc\(([^)]*)\)\{return ([^}]+)\?a:Ac\(\)\}""")


@dataclass(frozen=True)
class Gate:
    desc: str
    arch: str
    sig: re.Pattern[bytes]
    patched: re.Pattern[bytes]
    offset: int
    fix: bytes
    single: bool = False


def compile_bytes(pattern: bytes) -> re.Pattern[bytes]:
    return re.compile(pattern, re.DOTALL)


AGY_CLI_GATES = [
    Gate(
        "eligibility screen off (x64)",
        "x64",
        compile_bytes(rb"\x48\x85\xc0\x0f\x84.{4}\x80\x78\x08\x00\x0f\x85.{4}"),
        compile_bytes(rb"\x48\x85\xc0\x0f\x84.{4}\x48\x85\xc0\x90\x0f\x85.{4}"),
        9,
        b"\x48\x85\xc0\x90",
    ),
    Gate(
        "eligibility screen off (arm64)",
        "arm64",
        compile_bytes(
            rb".{3}\xb5.{3}\xb4\x01\x20\x40\x39[\x01\x21\x41\x61\x81\xa1\xc1\xe1].[\x00-\x07]\x37.{3}[\x94-\x97]"
            rb"(?:\xe0\x4b\x00\xf9\xe1\x33\x00\xf9\xe2\x43\x00\xf9|\xe0\x4f\x00\xf9\xe1\x33\x00\xf9\xe2\x47\x00\xf9\xe3\x2f\x00\xf9)"
        ),
        compile_bytes(
            rb".{3}\xb5.{3}\xb4\x21\x00\x80\x52[\x01\x21\x41\x61\x81\xa1\xc1\xe1].[\x00-\x07]\x37.{3}[\x94-\x97]"
            rb"(?:\xe0\x4b\x00\xf9\xe1\x33\x00\xf9\xe2\x43\x00\xf9|\xe0\x4f\x00\xf9\xe1\x33\x00\xf9\xe2\x47\x00\xf9\xe3\x2f\x00\xf9)"
        ),
        8,
        b"\x21\x00\x80\x52",
    ),
    Gate(
        "eligibility screen off (arm64, w2)",
        "arm64",
        compile_bytes(
            rb"[\x01\x21\x41\x61\x81\xa1\xc1\xe1].{2}\xb5[\x00\x20\x40\x60\x80\xa0\xc0\xe0].{2}\xb4"
            rb"\x02\x20\x40\x39[\x02\x22\x42\x62\x82\xa2\xc2\xe2].[\x00-\x07]\x37.{3}[\x94-\x97]"
        ),
        compile_bytes(
            rb"[\x01\x21\x41\x61\x81\xa1\xc1\xe1].{2}\xb5[\x00\x20\x40\x60\x80\xa0\xc0\xe0].{2}\xb4"
            rb"\x22\x00\x80\x52[\x02\x22\x42\x62\x82\xa2\xc2\xe2].[\x00-\x07]\x37.{3}[\x94-\x97]"
        ),
        8,
        b"\x22\x00\x80\x52",
    ),
    Gate(
        "eligibility screen off (arm64, w4)",
        "arm64",
        compile_bytes(
            rb"[\x00\x20\x40\x60\x80\xa0\xc0\xe0].{2}\xb4\x04\x20\x40\x39"
            rb"[\x04\x24\x44\x64\x84\xa4\xc4\xe4].[\x00-\x07]\x37\x04\x94\x44\xa9"
        ),
        compile_bytes(
            rb"[\x00\x20\x40\x60\x80\xa0\xc0\xe0].{2}\xb4\x24\x00\x80\x52"
            rb"[\x04\x24\x44\x64\x84\xa4\xc4\xe4].[\x00-\x07]\x37\x04\x94\x44\xa9"
        ),
        4,
        b"\x24\x00\x80\x52",
    ),
]

AUTH_GATES = [
    Gate(
        "hasValidAuth=true (x64)",
        "x64",
        compile_bytes(rb"\x80\x78\x08\x00\x74.\x48\x8b.[\x24].\x48\x89.\x60"),
        compile_bytes(rb"\xc6\x40\x08\x01\x90\x90\x48\x8b.[\x24].\x48\x89.\x60"),
        0,
        b"\xc6\x40\x08\x01\x90\x90",
    ),
    Gate(
        "hasValidAuth=true (arm64)",
        "arm64",
        compile_bytes(rb"\x03\x20\x40\x39[\x03\x23\x43\x63\x83\xa3\xc3\xe3].{2}\x36(?:.{4}){1,2}\x03\x10\x06\xa9"),
        compile_bytes(rb"\x23\x00\x80\x52\x03\x20\x00\x39(?:.{4}){1,2}\x03\x10\x06\xa9"),
        0,
        b"\x23\x00\x80\x52\x03\x20\x00\x39",
    ),
]

PRINT_GATE = Gate(
    "print-mode eligibility (x64)",
    "x64",
    compile_bytes(rb"\x48\x85\xc0\x0f\x85.{4}\x48\x85\xc9\x0f\x84.{4}\x80\x79\x08\x00\x0f\x85.{4}"),
    compile_bytes(rb"\x48\x85\xc0\x0f\x85.{4}\x48\x85\xc9\x0f\x84.{4}\x48\x85\xc9\x90\x0f\x85.{4}"),
    18,
    b"\x48\x85\xc9\x90",
)


def detect_arch(data: bytes) -> str | None:
    if len(data) >= 20 and data[:4] == b"\x7fELF":
        machine = int.from_bytes(data[18:20], "little")
        return {0x3E: "x64", 0xB7: "arm64"}.get(machine)
    if len(data) >= 8 and data[:4] in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"):
        endian = "little" if data[:4] == b"\xcf\xfa\xed\xfe" else "big"
        cputype = int.from_bytes(data[4:8], endian)
        return {0x01000007: "x64", 0x0100000C: "arm64"}.get(cputype)
    return None


def code_bounds(data: bytes) -> tuple[int, int]:
    size = len(data)
    if size >= 64 and data[:4] == b"\x7fELF" and data[4] == 2:
        shoff = int.from_bytes(data[40:48], "little")
        shentsize = int.from_bytes(data[58:60], "little")
        shnum = int.from_bytes(data[60:62], "little")
        if 0 < shoff < size and shnum > 0 and shoff + shnum * shentsize <= size:
            min_s, max_s = size, 0
            for i in range(shnum):
                off = shoff + i * shentsize
                s_type = int.from_bytes(data[off + 4 : off + 8], "little")
                s_flags = int.from_bytes(data[off + 8 : off + 16], "little")
                s_off = int.from_bytes(data[off + 24 : off + 32], "little")
                s_sz = int.from_bytes(data[off + 32 : off + 40], "little")
                if s_type == 1 and (s_flags & 4) and s_sz > 0 and s_off < size:
                    min_s = min(min_s, s_off)
                    max_s = max(max_s, min(size, s_off + s_sz))
            if max_s > min_s:
                return min_s, max_s
    return 0, size


def find_gate(data: bytes, gate: Gate, bounds: tuple[int, int]) -> tuple[str, list[int]] | None:
    start, end = bounds
    for span_start, span_end in ((start, end), (0, len(data))) if (start, end) != (0, len(data)) else ((0, len(data)),):
        view = memoryview(data)[span_start:span_end]
        patched = [span_start + m.start() + gate.offset for m in gate.patched.finditer(view)]
        if patched:
            return "patched", patched
        unpatched = [span_start + m.start() + gate.offset for m in gate.sig.finditer(view)]
        if unpatched:
            if gate.single and len(unpatched) > 1:
                raise RuntimeError(f"gate '{gate.desc}' signature is not unique")
            return "unpatched", unpatched
    return None


def resolve_multigate(data: bytes, gates: list[Gate], arch: str | None, bounds: tuple[int, int]) -> tuple[str, int, Gate]:
    ordered = [g for g in gates if arch is None or g.arch == arch] + [g for g in gates if arch is not None and g.arch != arch]
    for gate in ordered:
        res = find_gate(data, gate, bounds)
        if res is not None:
            status, offsets = res
            return status, offsets[0], gate
    raise RuntimeError("no matching gate signature found")


def apply_binary_patches(buf: bytearray, patches: list[tuple[int, bytes]]) -> None:
    for off, fix in patches:
        if off + len(fix) > len(buf):
            raise RuntimeError(f"patch offset {off} exceeds file length")
        buf[off : off + len(fix)] = fix


def patch_agy(path: Path, lock_update: bool) -> None:
    buf = bytearray(path.read_bytes())
    arch = detect_arch(buf)
    bounds = code_bounds(buf)
    patches: list[tuple[int, bytes]] = []

    s1, off1, g1 = resolve_multigate(buf, AGY_CLI_GATES, arch, bounds)
    if s1 == "unpatched":
        patches.append((off1, g1.fix))

    try:
        s2, off2, g2 = resolve_multigate(buf, AUTH_GATES, arch, bounds)
        if s2 == "unpatched":
            patches.append((off2, g2.fix))
    except RuntimeError:
        pass

    if arch == "x64":
        res3 = find_gate(buf, PRINT_GATE, bounds)
        if res3 is not None and res3[0] == "unpatched":
            for off in res3[1]:
                patches.append((off, PRINT_GATE.fix))

    if lock_update:
        assert len(UPDATER_URL) == len(DISABLED_URL)
        idx = buf.find(UPDATER_URL)
        if idx != -1:
            patches.append((idx, DISABLED_URL))

    if patches:
        apply_binary_patches(buf, patches)
        path.write_bytes(buf)

    # Verify final state
    s1_after, _, _ = resolve_multigate(buf, AGY_CLI_GATES, arch, bounds)
    if s1_after != "patched":
        raise RuntimeError(f"AGY patch verification failed: {path}")
    print(f"[+] AGY patched: {path}")


def patch_manager(path: Path) -> None:
    buf = bytearray(path.read_bytes())
    arch = detect_arch(buf)
    bounds = code_bounds(buf)
    gates = [Gate(g.desc, g.arch, g.sig, g.patched, g.offset, g.fix, single=True) for g in AUTH_GATES]
    status, off, gate = resolve_multigate(buf, gates, arch, bounds)
    if status == "unpatched":
        apply_binary_patches(buf, [(off, gate.fix)])
        path.write_bytes(buf)
    s_after, _, _ = resolve_multigate(buf, gates, arch, bounds)
    if s_after != "patched":
        raise RuntimeError(f"Manager patch verification failed: {path}")
    print(f"[+] Manager patched: {path}")


def patch_ide(path: Path) -> None:
    raw = path.read_text(encoding="utf-8")
    if not (IDE_DONE in raw and not IDE_RE.search(raw)):
        patched = IDE_RE.sub(r"\g<1>true", raw)
        if IDE_DONE not in patched or IDE_RE.search(patched):
            raise RuntimeError(f"IDE patch verification failed: {path}")
        path.write_text(patched, encoding="utf-8")
    print(f"[+] IDE patched: {path}")


def patch_vscode(path: Path, fallback_bin: str | None) -> None:
    raw = path.read_text(encoding="utf-8")
    if UPSTREAM_PART1_RE.search(raw) and UPSTREAM_PART2_RE.search(raw):
        text = raw
        if UPSTREAM_INJECT not in text:
            text = UPSTREAM_PART1_RE.sub(lambda m: m.group(1) + UPSTREAM_INJECT, text, count=1)
        text = UPSTREAM_PART2_RE.sub("const isChannelChanged = false;", text, count=1)
    else:
        m1 = MIN_PART1_RE.search(raw)
        if not m1:
            raise RuntimeError(f"VS Code extension anchor not found in {path}")
        out_var = m1.group(2)
        extra_cand = f",{json.dumps(fallback_bin)}" if fallback_bin else ""
        inject = (
            f"{{const __c=[la,(0,pa.join)((0,pa.dirname)(la),'antigravity'+((0,pa.extname)(la)||'')){extra_cand}];"
            f"for(const __p of __c){{if(__p&&(0,na.existsSync)(__p)){{{out_var}.appendLine("
            f"'[INSTALL] Existing binary found at '+__p+'. Skipping version check and re-download.');return __p;}}}}"
            f"}}"
        )
        text = raw
        if "[INSTALL] Existing binary found at " not in text:
            text = text[: m1.end()] + inject + text[m1.end() :]
        if MIN_CHANNEL_RE.search(text):
            text = MIN_CHANNEL_RE.sub(r"let \1=!1;", text, count=1)
        if MIN_REBUILD_RE.search(text):
            text = MIN_REBUILD_RE.sub(r"let \1=!1;", text, count=1)
        if fallback_bin:
            fb = json.dumps(fallback_bin)
            if not MIN_BC_RE.search(text):
                raise RuntimeError(f"VS Code extension Bc() helper not found in {path}")
            text = MIN_BC_RE.sub(
                lambda m: f"function Bc({m.group(1)}){{const __d=Ac();return {m.group(2)}?a:((0,na.existsSync)(__d)?__d:{fb})}}",
                text,
                count=1,
            )

    if text == raw:
        raise RuntimeError(f"No changes applied to {path}")
    path.write_text(text, encoding="utf-8")
    print(f"[+] VS Code extension patched: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity Python patcher")
    sub = parser.add_subparsers(dest="target", required=True)

    p_agy = sub.add_parser("agy")
    p_agy.add_argument("path", type=Path)
    p_agy.add_argument("--lock-update", action="store_true")

    p_ide = sub.add_parser("ide")
    p_ide.add_argument("path", type=Path)

    p_mgr = sub.add_parser("manager")
    p_mgr.add_argument("path", type=Path)

    p_vs = sub.add_parser("vscode")
    p_vs.add_argument("path", type=Path)
    p_vs.add_argument("--fallback-bin", default=None)

    args = parser.parse_args()
    if args.target == "agy":
        patch_agy(args.path, args.lock_update)
    elif args.target == "ide":
        patch_ide(args.path)
    elif args.target == "manager":
        patch_manager(args.path)
    elif args.target == "vscode":
        patch_vscode(args.path, args.fallback_bin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
