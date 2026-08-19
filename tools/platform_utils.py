from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 17836
EXPECTED_API_REVISION = 4


def system_name() -> str:
    return platform.system().lower()


def runtime_dir() -> Path:
    system = system_name()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "OmniIconVault" / "cache"
    if system == "darwin":
        return Path.home() / "Library" / "Caches" / "OmniIconVault"
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "omni-icon-vault"


def cli_bin_dir() -> Path:
    if system_name() == "windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "OmniIconVault" / "bin"
    return Path.home() / ".local" / "bin"


def font_dir() -> Path:
    system = system_name()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Microsoft" / "Windows" / "Fonts"
    if system == "darwin":
        return Path.home() / "Library" / "Fonts"
    return Path.home() / ".local" / "share" / "fonts" / "omni-icon-vault"


def app_url(port: int = DEFAULT_PORT) -> str:
    return f"http://localhost:{port}"


def health(port: int = DEFAULT_PORT, timeout: float = 0.8) -> dict | None:
    try:
        with urllib.request.urlopen(f"{app_url(port)}/api/health", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data if data.get("ok") else None
    except Exception:
        return None


def health_is_compatible(data: dict | None) -> bool:
    """True only when the running API process supports this checkout's protocol.

    VERSION alone is not sufficient because a long-running Python process can read a
    newly-written VERSION file while still executing old server code.
    """
    if not data or not data.get("ok"):
        return False
    try:
        return int(data.get("apiRevision", 0)) >= EXPECTED_API_REVISION
    except (TypeError, ValueError):
        return False




def _process_command(pid: int) -> str:
    """Best-effort command line lookup for a process owned by this user."""
    if pid <= 0:
        return ""
    system = system_name()
    try:
        if system == "linux":
            raw = Path(f"/proc/{pid}/cmdline").read_bytes()
            return raw.replace(b"\x00", b" ").decode("utf-8", "replace").strip()
        if system == "windows":
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if ps:
                cmd = [ps, "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=2, check=False)
                return (r.stdout or "").strip()
        # macOS and portable POSIX fallback.
        r = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True, timeout=2, check=False)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def _looks_like_omni_server_command(command: str) -> bool:
    c = (command or "").replace('\\', '/').lower()
    return "omni_server.py" in c and ("omni-icon-vault" in c or "omniiconvault" in c)


def _listener_pids(port: int) -> list[int]:
    """Return PIDs listening on a TCP port without killing anything."""
    found: set[int] = set()
    system = system_name()
    try:
        if system in ("linux", "darwin") and shutil.which("lsof"):
            r = subprocess.run(
                ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                capture_output=True, text=True, timeout=2, check=False,
            )
            for token in (r.stdout or "").split():
                if token.isdigit():
                    found.add(int(token))
        if system == "linux" and not found and shutil.which("ss"):
            r = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True, timeout=2, check=False)
            for line in (r.stdout or "").splitlines():
                if f":{port}" not in line:
                    continue
                for match in __import__('re').finditer(r"pid=(\d+)", line):
                    found.add(int(match.group(1)))
        if system == "windows":
            r = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=3, check=False)
            for line in (r.stdout or "").splitlines():
                parts = line.split()
                if len(parts) < 5 or parts[0].upper() != "TCP" or parts[3].upper() != "LISTENING":
                    continue
                local = parts[1]
                if local.rsplit(':', 1)[-1] == str(port) and parts[-1].isdigit():
                    found.add(int(parts[-1]))
    except Exception:
        pass
    return sorted(found)


def _terminate_omni_pid(pid: int, wait: float = 2.0) -> bool:
    """Terminate only a process whose command line identifies it as Omni."""
    command = _process_command(pid)
    if not _looks_like_omni_server_command(command):
        return False
    try:
        if system_name() == "windows":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return True
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return True
    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return True
        time.sleep(0.05)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    return True


def _python_for_background() -> str:
    if system_name() == "windows":
        p = Path(sys.executable)
        pythonw = p.with_name("pythonw.exe")
        if pythonw.exists():
            return str(pythonw)
    return sys.executable


def start_server(port: int = DEFAULT_PORT, quiet: bool = True, wait: float = 5.0) -> dict:
    existing = health(port)
    if existing and health_is_compatible(existing):
        return {"started": False, "health": existing, "pid": None}
    if existing:
        # The local static files may already be updated while an older Python server
        # is still alive in memory. Restart it so new API filters actually execute.
        stop_server(port)
        deadline = time.time() + 3.0
        while time.time() < deadline and health(port, timeout=0.2):
            time.sleep(0.1)
        if health(port, timeout=0.2):
            raise RuntimeError(
                "An outdated Omni server is still using the local port. "
                "Run 'omni-icons stop' and try again."
            )

    if not (ROOT / "browser" / "icon-data.json").exists():
        raise RuntimeError("Icon index is missing. Run the installer first.")

    rdir = runtime_dir()
    rdir.mkdir(parents=True, exist_ok=True)
    pid_file = rdir / "server.pid"
    log_file = rdir / "server.log"
    cmd = [
        _python_for_background(),
        str(ROOT / "tools" / "omni_server.py"),
        "--root", str(ROOT),
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    if quiet:
        cmd.append("--quiet")

    log = open(log_file, "ab", buffering=0)
    kwargs: dict = {"cwd": str(ROOT), "stdin": subprocess.DEVNULL, "stdout": log, "stderr": log}
    if system_name() == "windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **kwargs)
    pid_file.write_text(str(proc.pid), "utf-8")

    deadline = time.time() + wait
    while time.time() < deadline:
        h = health(port)
        if h:
            return {"started": True, "health": h, "pid": proc.pid}
        if proc.poll() is not None:
            break
        time.sleep(0.1)
    raise RuntimeError(f"Omni server failed to start. See {log_file}")


def stop_server(port: int = DEFAULT_PORT) -> bool:
    """Stop the local Omni server, including stale processes with lost PID files.

    Safety rule: process discovery may inspect any listener on the configured port,
    but it only terminates a PID when its command line is recognizably Omni.
    """
    stopped = False
    system = system_name()

    # Stop platform-managed autostart first so it cannot immediately respawn.
    if system == "linux" and shutil.which("systemctl"):
        r = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "omni-icon-vault.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            subprocess.run(["systemctl", "--user", "stop", "omni-icon-vault.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            stopped = True
    elif system == "darwin" and shutil.which("launchctl"):
        agent = Path.home() / "Library" / "LaunchAgents" / "local.omniiconvault.server.plist"
        if agent.exists() and health(port, timeout=0.2):
            subprocess.run(["launchctl", "unload", str(agent)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            stopped = True

    # Prefer the current server's self-reported PID when available.
    h = health(port, timeout=0.3)
    if h:
        try:
            pid = int(h.get("pid", 0))
        except (TypeError, ValueError):
            pid = 0
        if pid and _terminate_omni_pid(pid):
            stopped = True

    # Then try our runtime PID file, but never trust it blindly: stale PID files can
    # point at unrelated processes after PID reuse.
    rdir = runtime_dir()
    pid_file = rdir / "server.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text("utf-8").strip())
            if _terminate_omni_pid(pid):
                stopped = True
        except (OSError, ValueError):
            pass
        try:
            pid_file.unlink()
        except OSError:
            pass

    # Recovery path for upgrades from older Omni versions: discover the process that
    # actually owns the port and terminate it only if its command line is Omni.
    if health(port, timeout=0.2):
        for pid in _listener_pids(port):
            if _terminate_omni_pid(pid):
                stopped = True

    for _ in range(40):
        if not health(port, timeout=0.2):
            break
        time.sleep(0.1)
    return stopped


def open_browser(port: int = DEFAULT_PORT) -> str:
    start_server(port)
    url = f"{app_url(port)}/"
    webbrowser.open(url, new=2)
    return url


def clipboard_write(text: str) -> bool:
    if not text:
        return False
    system = system_name()
    if system == "windows" and shutil.which("clip.exe"):
        subprocess.run(["clip.exe"], input=text.encode("utf-16le"), check=True)
        return True
    if system == "darwin" and shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        return True
    for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
        if shutil.which(cmd[0]):
            subprocess.run(cmd, input=text.encode("utf-8"), check=True)
            return True
    return False


def refresh_fonts() -> None:
    system = system_name()
    if system == "linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    elif system == "windows":
        # Notify running apps that the user font collection changed.
        try:
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_ulong()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_FONTCHANGE, 0, 0, SMTO_ABORTIFHUNG, 2000, ctypes.byref(result)
            )
        except Exception:
            pass


def ensure_windows_user_path(directory: Path) -> bool:
    if system_name() != "windows":
        return False
    import winreg
    directory = directory.resolve()
    key_path = r"Environment"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
        try:
            current, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current = ""
        parts = [p for p in current.split(";") if p]
        if any(Path(os.path.expandvars(p)).resolve() == directory for p in parts if p.strip()):
            return False
        new = current.rstrip(";") + (";" if current else "") + str(directory)
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new)
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 2000, ctypes.byref(result)
        )
    except Exception:
        pass
    return True


def remove_windows_user_path(directory: Path) -> bool:
    if system_name() != "windows":
        return False
    import winreg
    directory = directory.resolve()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
        try:
            current, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            return False
        kept = []
        changed = False
        for p in [x for x in current.split(";") if x]:
            try:
                same = Path(os.path.expandvars(p)).resolve() == directory
            except Exception:
                same = False
            if same:
                changed = True
            else:
                kept.append(p)
        if changed:
            winreg.SetValueEx(key, "Path", 0, kind, ";".join(kept))
        return changed
