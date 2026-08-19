#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from platform_utils import cli_bin_dir, ensure_windows_user_path, font_dir, refresh_fonts, start_server, system_name
from version import version

CACHE = ROOT / "cache"
VENDOR = ROOT / "vendor"
STATE = ROOT / ".omni-install-state.json"
UA = f"Omni-Icon-Vault/{version()} (+https://github.com/)"


def log(msg: str = "") -> None:
    print(msg, flush=True)


def load_sources() -> dict:
    return json.loads((ROOT / "sources.json").read_text("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(out: Path, urls: list[str], required: bool, expected_sha: str | None = None) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.is_file() and out.stat().st_size > 0:
        if expected_sha and sha256_file(out).lower() != expected_sha.lower():
            log(f"Cached checksum mismatch; redownloading {out.name}")
            out.unlink()
        else:
            log(f"Using cached {out.name}")
            return True
    last_error = None
    for url in urls:
        part = out.with_suffix(out.suffix + ".part")
        try:
            if part.exists():
                part.unlink()
            log(f"Downloading {out.name}")
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=45) as r, part.open("wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                read = 0
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    read += len(chunk)
                    if total and read % (8 * 1024 * 1024) < len(chunk):
                        print(f"  {read / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} MiB", flush=True)
            if expected_sha and sha256_file(part).lower() != expected_sha.lower():
                raise RuntimeError("SHA-256 mismatch")
            part.replace(out)
            return True
        except Exception as e:
            last_error = e
            try:
                part.unlink(missing_ok=True)
            except OSError:
                pass
    if required:
        raise RuntimeError(f"Required download failed for {out.name}: {last_error}")
    log(f"WARN: optional source unavailable ({out.name}): {last_error}")
    return False


def _safe_member(dest: Path, member: str) -> bool:
    target = (dest / member).resolve()
    try:
        target.relative_to(dest.resolve())
        return True
    except ValueError:
        return False


def extract_archive(archive: Path, target: Path, kind: str) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="omni-extract-", dir=str(ROOT)))
    try:
        if kind == "zip":
            with zipfile.ZipFile(archive) as zf:
                bad = [n for n in zf.namelist() if not _safe_member(tmp, n)]
                if bad:
                    raise RuntimeError(f"Unsafe ZIP member: {bad[0]}")
                zf.extractall(tmp)
        elif kind == "tar.xz":
            with tarfile.open(archive, "r:xz") as tf:
                members = tf.getmembers()
                bad = [m.name for m in members if not _safe_member(tmp, m.name)]
                if bad:
                    raise RuntimeError(f"Unsafe tar member: {bad[0]}")
                # Avoid special files / links from upstream archives.
                members = [m for m in members if m.isfile() or m.isdir()]
                tf.extractall(tmp, members=members)
        else:
            raise RuntimeError(f"Unsupported archive type: {kind}")

        children = list(tmp.iterdir())
        source = children[0] if len(children) == 1 and children[0].is_dir() else tmp
        shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            dst = target / child.name
            if child.is_dir():
                shutil.copytree(child, dst)
            else:
                shutil.copy2(child, dst)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def harvest_license(source_id: str, target: Path) -> None:
    out = ROOT / "licenses" / "upstream" / source_id
    out.mkdir(parents=True, exist_ok=True)
    candidates = []
    for pattern in ("LICENSE*", "COPYING*", "NOTICE*", "OFL*.txt"):
        candidates.extend(target.glob(pattern))
        candidates.extend(target.glob(f"*/{pattern}"))
    count = 0
    seen = set()
    for p in candidates:
        if not p.is_file() or p.stat().st_size > 1024 * 1024:
            continue
        key = p.name.lower()
        if key in seen:
            continue
        seen.add(key)
        shutil.copy2(p, out / p.name)
        count += 1
        if count >= 6:
            break


def prepare_vendor(refresh: bool = False, core_only: bool = False) -> None:
    cfg = load_sources()
    CACHE.mkdir(parents=True, exist_ok=True)
    VENDOR.mkdir(parents=True, exist_ok=True)
    if refresh:
        log("Refresh requested: cached upstream downloads will be replaced.")
        for p in CACHE.iterdir():
            if p.name != ".gitkeep":
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()

    for spec in cfg.get("archives", []):
        if core_only and not spec.get("required"):
            continue
        archive = CACHE / spec["cache"]
        ok = download(archive, spec["urls"], bool(spec.get("required")), spec.get("sha256"))
        if not ok:
            continue
        target = VENDOR / spec["target"]
        log(f"Extracting {spec['id']} -> vendor/{spec['target']}")
        extract_archive(archive, target, spec["type"])
        harvest_license(spec["source"], target)

    for spec in cfg.get("files", []):
        cache = CACHE / spec["cache"]
        ok = download(cache, spec["urls"], bool(spec.get("required")), spec.get("sha256"))
        if not ok:
            continue
        target = VENDOR / spec["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cache, target)


def build_index() -> Counter:
    log("Building searchable icon index...")
    subprocess.run([sys.executable, str(TOOLS / "build-index.py")], cwd=ROOT, check=True)
    data = json.loads((ROOT / "browser" / "icon-data.json").read_text("utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("Generated icon-data.json is invalid")
    counts = Counter(x.get("source", "unknown") for x in data)
    core = ["fontawesome", "bootstrap", "nerdfonts", "material", "tabler"]
    missing = [x for x in core if counts[x] == 0]
    if missing:
        raise RuntimeError("Installation incomplete; zero icons indexed for: " + ", ".join(missing))
    log("\nIndexed icon counts:")
    order = ["fontawesome", "bootstrap", "nerdfonts", "material", "tabler", "simpleicons", "lucide", "heroicons", "phosphor", "iconoir", "ionicons", "octicons", "devicon", "fluent", "favicons", "custom"]
    for src in order:
        if counts[src]:
            log(f"  {src:14} {counts[src]:>8,}")
    log(f"  {'TOTAL':14} {len(data):>8,}")
    return counts


def font_candidates() -> list[Path]:
    result: list[Path] = []
    for base in (VENDOR / "fontawesome-desktop", VENDOR / "nerdfonts"):
        if base.exists():
            result.extend(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in (".ttf", ".otf"))
    material = VENDOR / "material" / "MaterialSymbolsOutlined.ttf"
    if material.exists():
        result.append(material)
    # De-duplicate by file name/content source path.
    seen = set(); out = []
    for p in result:
        key = (p.name.lower(), p.stat().st_size)
        if key not in seen:
            seen.add(key); out.append(p)
    return out


def install_fonts() -> list[str]:
    dest = font_dir()
    dest.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    system = system_name()
    for src in font_candidates():
        dst = dest / src.name
        shutil.copy2(src, dst)
        installed.append(str(dst))
        if system == "windows":
            try:
                import winreg
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts") as key:
                    winreg.SetValueEx(key, f"Omni Icon Vault - {src.stem}", 0, winreg.REG_SZ, str(dst))
            except Exception as e:
                log(f"WARN: Windows font registry update failed for {src.name}: {e}")
    refresh_fonts()
    log(f"Installed/refreshed {len(installed)} local font files in {dest}")
    return installed


def quote_sh(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def install_cli() -> tuple[list[str], bool]:
    d = cli_bin_dir(); d.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    path_modified = False
    if system_name() == "windows":
        cmd = d / "omni-icons.cmd"
        cmd.write_text(f'@echo off\r\n"{sys.executable}" "{ROOT / "omni.py"}" %*\r\n', "utf-8")
        created.append(str(cmd))
        try:
            path_modified = ensure_windows_user_path(d)
        except Exception as e:
            log(f"WARN: could not add {d} to user PATH: {e}")
    else:
        wrapper = d / "omni-icons"
        wrapper.write_text(f"#!/bin/sh\nexec {quote_sh(sys.executable)} {quote_sh(str(ROOT / 'omni.py'))} \"$@\"\n", "utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created.append(str(wrapper))
    log(f"CLI installed: {d}")
    return created, path_modified


def install_linux_integration(autostart: bool) -> list[str]:
    created = []
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    desktop = apps / "omni-icon-vault.desktop"
    desktop.write_text(
        "[Desktop Entry]\nType=Application\nName=Omni Icon Vault\n"
        "Comment=Search icons, brands and favicons for Figma and code\n"
        f'Exec="{sys.executable}" "{ROOT / "omni.py"}" open\n'
        "Icon=applications-graphics\nTerminal=false\nCategories=Graphics;Development;\n",
        "utf-8",
    )
    desktop.chmod(desktop.stat().st_mode | stat.S_IXUSR)
    created.append(str(desktop))

    if autostart:
        config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        service_dir = config / "systemd" / "user"
        systemctl = shutil.which("systemctl")
        installed_service = False
        if systemctl:
            service_dir.mkdir(parents=True, exist_ok=True)
            svc = service_dir / "omni-icon-vault.service"
            svc.write_text(
                "[Unit]\nDescription=Omni Icon Vault local browser and Figma API\n\n"
                "[Service]\nType=simple\n"
                f'ExecStart="{sys.executable}" "{ROOT / "tools" / "omni_server.py"}" --root "{ROOT}" --host 127.0.0.1 --port 17836 --quiet\n'
                "Restart=on-failure\nRestartSec=2\n\n[Install]\nWantedBy=default.target\n",
                "utf-8",
            )
            created.append(str(svc))
            subprocess.run([systemctl, "--user", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            r = subprocess.run([systemctl, "--user", "enable", "--now", "omni-icon-vault.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            installed_service = r.returncode == 0
        if not installed_service:
            autostart_dir = config / "autostart"; autostart_dir.mkdir(parents=True, exist_ok=True)
            entry = autostart_dir / "omni-icon-vault-server.desktop"
            entry.write_text(
                "[Desktop Entry]\nType=Application\nName=Omni Icon Vault Server\n"
                f'Exec="{sys.executable}" "{ROOT / "omni.py"}" start\n'
                "Terminal=false\nX-GNOME-Autostart-enabled=true\n",
                "utf-8",
            )
            created.append(str(entry))
    return created


def install_macos_integration(autostart: bool) -> list[str]:
    created = []
    apps = Path.home() / "Applications"
    bundle = apps / "Omni Icon Vault.app" / "Contents"
    macos = bundle / "MacOS"; macos.mkdir(parents=True, exist_ok=True)
    exe = macos / "OmniIconVault"
    exe.write_text(f"#!/bin/sh\nexec {quote_sh(sys.executable)} {quote_sh(str(ROOT / 'omni.py'))} open\n", "utf-8")
    exe.chmod(0o755)
    plist = bundle / "Info.plist"
    plist.write_text(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
        "<plist version=\"1.0\"><dict>"
        "<key>CFBundleName</key><string>Omni Icon Vault</string>"
        "<key>CFBundleIdentifier</key><string>local.omniiconvault.app</string>"
        f"<key>CFBundleVersion</key><string>{version()}</string>"
        "<key>CFBundleExecutable</key><string>OmniIconVault</string>"
        "</dict></plist>\n",
        "utf-8",
    )
    created.extend([str(exe), str(plist)])
    if autostart:
        launch = Path.home() / "Library" / "LaunchAgents"; launch.mkdir(parents=True, exist_ok=True)
        agent = launch / "local.omniiconvault.server.plist"
        agent.write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
            "<plist version=\"1.0\"><dict>"
            "<key>Label</key><string>local.omniiconvault.server</string>"
            "<key>ProgramArguments</key><array>"
            f"<string>{sys.executable}</string><string>{ROOT / 'tools' / 'omni_server.py'}</string>"
            f"<string>--root</string><string>{ROOT}</string><string>--host</string><string>127.0.0.1</string><string>--port</string><string>17836</string><string>--quiet</string>"
            "</array><key>RunAtLoad</key><true/><key>KeepAlive</key><true/>"
            "</dict></plist>\n",
            "utf-8",
        )
        created.append(str(agent))
        launchctl = shutil.which("launchctl")
        if launchctl:
            subprocess.run([launchctl, "unload", str(agent)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            subprocess.run([launchctl, "load", str(agent)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return created


def install_windows_integration(autostart: bool) -> list[str]:
    created = []
    appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    programs = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    programs.mkdir(parents=True, exist_ok=True)
    launcher = programs / "Omni Icon Vault.cmd"
    launcher.write_text(f'@echo off\r\n"{sys.executable}" "{ROOT / "omni.py"}" open\r\n', "utf-8")
    created.append(str(launcher))
    if autostart:
        startup = programs / "Startup"; startup.mkdir(parents=True, exist_ok=True)
        bg_python = Path(sys.executable).with_name("pythonw.exe")
        py = bg_python if bg_python.exists() else Path(sys.executable)
        entry = startup / "Omni Icon Vault Server.cmd"
        entry.write_text(f'@echo off\r\nstart "" /B "{py}" "{ROOT / "omni.py"}" start\r\n', "utf-8")
        created.append(str(entry))
    return created


def install_integrations(autostart: bool) -> list[str]:
    sysname = system_name()
    if sysname == "windows":
        return install_windows_integration(autostart)
    if sysname == "darwin":
        return install_macos_integration(autostart)
    return install_linux_integration(autostart)


def save_state(created: list[str], fonts: list[str], path_modified: bool) -> None:
    previous = {}
    if STATE.exists():
        try:
            previous = json.loads(STATE.read_text("utf-8"))
        except Exception:
            previous = {}
    merged_created = sorted(set(previous.get("created", [])) | set(created))
    merged_fonts = sorted(set(previous.get("fonts", [])) | set(fonts))
    STATE.write_text(json.dumps({
        "version": version(),
        "root": str(ROOT),
        "platform": platform.platform(),
        "created": merged_created,
        "fonts": merged_fonts,
        "windows_path_modified": bool(previous.get("windows_path_modified")) or path_modified,
        "installed_at": time.time(),
    }, indent=2) + "\n", "utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Install Omni Icon Vault on Windows, macOS or Linux.")
    ap.add_argument("--refresh", action="store_true", help="redownload all pinned upstream assets")
    ap.add_argument("--core-only", action="store_true", help="install only Font Awesome, Nerd Fonts, Bootstrap, Material and Tabler")
    ap.add_argument("--no-fonts", action="store_true", help="do not install local desktop fonts")
    ap.add_argument("--no-integration", action="store_true", help="do not add CLI/menu/startup integration")
    ap.add_argument("--no-autostart", action="store_true", help="install launcher/CLI but not login autostart")
    ap.add_argument("--no-start", action="store_true", help="do not start the local server after installation")
    a = ap.parse_args()

    if sys.version_info < (3, 10):
        raise SystemExit("Omni Icon Vault requires Python 3.10 or newer.")

    log(f"Omni Icon Vault {version()} — cross-platform installer")
    log(f"Platform: {platform.platform()}")
    log(f"Python:   {sys.version.split()[0]} ({sys.executable})\n")

    (ROOT / "favicons").mkdir(exist_ok=True)
    if not (ROOT / "favicons" / "registry.json").exists():
        (ROOT / "favicons" / "registry.json").write_text("[]\n", "utf-8")
    (ROOT / "browser" / "assets" / "favicons").mkdir(parents=True, exist_ok=True)

    prepare_vendor(refresh=a.refresh, core_only=a.core_only)
    build_index()
    fonts = [] if a.no_fonts else install_fonts()
    created: list[str] = []
    path_modified = False
    if not a.no_integration:
        cli_created, path_modified = install_cli()
        created.extend(cli_created)
        created.extend(install_integrations(not a.no_autostart))
    save_state(created, fonts, path_modified)

    if not a.no_start:
        try:
            result = start_server()
            log(f"Local browser/API ready: http://localhost:17836/ ({result['health'].get('icons', 0):,} icons)")
        except Exception as e:
            log(f"WARN: install succeeded, but the local server did not start: {e}")

    log("\n✓ Installation complete")
    log("  Browser:  omni-icons open")
    log("  Search:   omni-icons search camera")
    log("  Favicon:  omni-icons favicon add example.com")
    log(f"  Figma:    import {ROOT / 'figma-plugin' / 'manifest.json'} as a development plugin")
    if system_name() != "windows" and str(cli_bin_dir()) not in os.environ.get("PATH", "").split(os.pathsep):
        log(f"\nNOTE: add {cli_bin_dir()} to PATH, or run: {sys.executable} {ROOT / 'omni.py'}")
    if system_name() == "windows" and path_modified:
        log("\nNOTE: open a new terminal before using the omni-icons command; your user PATH was updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
