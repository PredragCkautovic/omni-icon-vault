from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def version() -> str:
    try:
        return (ROOT / "VERSION").read_text("utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"
