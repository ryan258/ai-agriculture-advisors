"""Local operations. Verification and live checks run only by explicit invocation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from lib.engine.config import PROJECT_ROOT, Settings, get_settings

CONTROL = PROJECT_ROOT / ".local-state" / "instance.json"


def data_directory() -> Path:
    path = Path(os.getenv("CHROMADB_PATH", ".chromadb")).expanduser()
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _require_stopped() -> None:
    if listening(Settings._integer("PORT", "8123")):
        raise ValueError(
            "Stop the app before backing up. A live Chroma directory was not copied."
        )
    if CONTROL.exists():
        record = json.loads(CONTROL.read_text())
        if _pid_alive(record["pid"]):
            raise ValueError(
                "The recorded process is still present or stopping. Confirm it has stopped before backup; no process was changed."
            )


def identity(port: int) -> dict:
    try:
        with urlopen(f"http://127.0.0.1:{port}/local-status", timeout=1) as response:
            return json.load(response)
    except (OSError, ValueError):
        return {}


def start(offline: bool = False) -> None:
    if offline:
        os.environ["ALLOW_MISSING_API_KEY"] = "true"
        get_settings.cache_clear()
    settings = get_settings()
    if listening(settings.port):
        raise ValueError(
            f"Port {settings.port} is already in use. Run ./advisors status; the existing process was not changed."
        )
    CONTROL.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    nonce = uuid.uuid4().hex
    log = CONTROL.parent / "app.log"
    with log.open("ab") as output:
        log.chmod(0o600)
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(settings.port),
                "--no-access-log",
            ],
            cwd=PROJECT_ROOT,
            env={**os.environ, "AI_ADVISORS_INSTANCE": nonce},
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    CONTROL.write_text(
        json.dumps({"pid": process.pid, "port": settings.port, "instance": nonce})
    )
    CONTROL.chmod(0o600)
    for _ in range(20):
        if identity(settings.port).get("instance") == nonce:
            print(
                f"AI Advisors: http://localhost:{settings.port}. Stop: ./advisors stop"
            )
            return
        if process.poll() is not None:
            raise ValueError(
                "Startup failed. Run ./advisors doctor and inspect .local-state/app.log."
            )
        time.sleep(0.2)
    raise ValueError(
        "Startup is not confirmed yet. Use ./advisors status and inspect .local-state/app.log before starting another process."
    )


def status() -> None:
    port = Settings._integer("PORT", "8123")
    current = identity(port)
    if current.get("application") == "AI Advisors":
        print(
            f"Running at http://localhost:{port}; PID {current['pid']}; version {current['version']}."
        )
    else:
        print(
            "Stopped."
            if not listening(port)
            else "The configured port is occupied by an unrecognized process."
        )


def stop() -> None:
    if not CONTROL.exists():
        raise ValueError(
            "No managed process record. Stop a previously started terminal uvicorn with Ctrl-C; no unrelated process was signaled."
        )
    record = json.loads(CONTROL.read_text())
    current = identity(record["port"])
    if (
        current.get("pid") != record["pid"]
        or current.get("instance") != record["instance"]
    ):
        raise ValueError("Process identity was not confirmed. No process was signaled.")
    os.kill(record["pid"], signal.SIGTERM)
    for _ in range(25):
        if not _pid_alive(record["pid"]):
            CONTROL.unlink(missing_ok=True)
            print(
                "Stopped. Interrupted working calls remain available for deliberate recovery."
            )
            return
        time.sleep(0.2)
    print(
        "Stop requested; the process is still stopping. Check status before backup. No force-kill was sent."
    )


def doctor(live: bool = False) -> int:
    print("Local diagnostics; keys and submitted content are not printed.")
    failed = False
    try:
        Settings.from_env()
        print("Configuration: valid")
    except (ValueError, TypeError) as error:
        print(f"Configuration needs attention: {error}")
        failed = True
    for package in ("fastapi", "chromadb", "httpx", "jinja2"):
        try:
            print(f"{package}: {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"Missing {package}; run uv sync --locked")
            failed = True
    if live and not failed:
        import asyncio
        from lib.engine.llm_client import LLMClient

        async def trial() -> None:
            client = LLMClient()
            try:
                await client.generate(
                    "Reply with OK.", "You are a connectivity check. Return only OK."
                )
            finally:
                await client.close()

        try:
            asyncio.run(trial())
            print(
                "One live request returned usable text; answer quality is not established."
            )
        except Exception as error:
            print(f"Live check failed ({type(error).__name__}); no automatic retry.")
            failed = True
    elif not live:
        print(
            "No provider request made. A deliberate live check is ./advisors doctor --live"
        )
    return int(failed)


def backup(destination: Path | None = None) -> Path:
    _require_stopped()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = (
        destination
        or PROJECT_ROOT / ".local-backups" / f"advisors-{stamp}-{uuid.uuid4().hex[:6]}"
    ).resolve()
    root = data_directory()
    if root == PROJECT_ROOT or target == root or root in target.parents:
        raise ValueError("Choose a backup destination outside the history directory.")
    if root.exists() and any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError(
            "History contains a symlink. Inspect it before making a portable backup."
        )
    target.mkdir(mode=0o700, parents=True, exist_ok=False)
    if root.exists():
        shutil.copytree(root, target / "history")
    if (PROJECT_ROOT / ".env").exists():
        shutil.copy2(PROJECT_ROOT / ".env", target / "private.env")
        (target / "private.env").chmod(0o600)
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=PROJECT_ROOT,
        )
        .decode()
        .split("\0")
    )
    with tarfile.open(target / "source.tar", "w") as archive:
        for relative in paths:
            source = PROJECT_ROOT / relative
            if (
                relative
                and source.is_file()
                and not source.is_symlink()
                and root not in source.parents
                and target not in source.parents
                and relative != ".env"
            ):
                archive.add(source, arcname=relative, recursive=False)
    files = {
        str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in target.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    versions = {}
    for name in ("chromadb", "fastapi", "httpx", "jinja2"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unavailable"
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "format": 1,
                "created_at": stamp,
                "files": files,
                "application_version": "2.1.0",
                "record_schema": 3,
                "python_version": sys.version.split()[0],
                "packages": versions,
                "sqlite_version": sqlite3.sqlite_version,
                "browser_drafts_included": False,
            },
            indent=2,
        )
    )
    print(
        f"Private stopped-app backup: {target}. It may contain credentials. Browser drafts are not included."
    )
    return target


def restore(snapshot: Path, destination: Path) -> None:
    snapshot = snapshot.resolve()
    if destination.exists():
        raise ValueError(
            "Choose a new restore directory. Existing data is never overlaid."
        )
    if any(p.is_symlink() for p in snapshot.rglob("*")):
        raise ValueError(
            "Snapshot contains symlinks; inspect it manually before restoring."
        )
    manifest = json.loads((snapshot / "manifest.json").read_text())
    if manifest.get("format") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("Unsupported backup manifest")
    actual = {
        str(path.relative_to(snapshot))
        for path in snapshot.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if "source.tar" not in manifest["files"] or actual != set(manifest["files"]):
        raise ValueError(
            "Snapshot file inventory does not match its manifest. Nothing was restored."
        )
    for name, digest in manifest["files"].items():
        if (
            Path(name).is_absolute()
            or ".." in Path(name).parts
            or hashlib.sha256((snapshot / name).read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Snapshot integrity failed. Nothing was restored.")
    with tarfile.open(snapshot / "source.tar") as archive:
        members = archive.getmembers()
        if any(
            not (m.isfile() or m.isdir())
            or Path(m.name).is_absolute()
            or ".." in Path(m.name).parts
            for m in members
        ):
            raise ValueError("Unsafe source archive member. Nothing was restored.")
        destination.mkdir(mode=0o700, parents=True)
        archive.extractall(destination / "source", filter="data")
    if (snapshot / "history").is_dir():
        shutil.copytree(snapshot / "history", destination / "history")
    if (snapshot / "private.env").exists():
        shutil.copy2(snapshot / "private.env", destination / "private.env")
        (destination / "private.env").chmod(0o600)
    print(
        f"Restored into {destination}. Inspect the new location before any deliberate production replacement."
    )


def check(target: str | None = None) -> int:
    with tempfile.TemporaryDirectory(prefix="advisors-owner-check-") as temporary:
        env = {
            **os.environ,
            "CHROMADB_PATH": str(Path(temporary) / "history"),
            "ALLOW_MISSING_API_KEY": "true",
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_API_URL": "https://api.test.invalid/v1/chat/completions",
            "OPENROUTER_MODEL": "test-model",
            "OPENROUTER_SYNTHESIS_MODEL": "",
            "MAX_OUTPUT_TOKENS": "1800",
            "MAX_RUN_CALLS": "32",
            "MAX_RUN_SECONDS": "600",
            "MAX_PROMPT_CHARS": "120000",
            "MAX_RUN_ATTEMPTS": "3",
        }
        node = shutil.which("node")
        bundled_node = Path.home() / ".hermes" / "node" / "bin" / "node"
        if not node and bundled_node.is_file():
            node = str(bundled_node)
        if not node:
            print("Node unavailable; headless JavaScript verification remains pending.")
            return 1
        commands = [
            [sys.executable, "-m", "pytest", "-q", *([target] if target else [])],
            [
                sys.executable,
                "-m",
                "mypy",
                "--follow-imports=silent",
                "lib/contracts.py",
                "lib/engine",
                "lib/storage",
                "lib/services/run_service.py",
                "lib/services/record_export.py",
                "lib/services/workbench_service.py",
            ],
            [
                node,
                "--test",
                "tests/test_workspace_controls.cjs",
                "tests/test_note_drafts.cjs",
                "tests/test_retry_countdown.cjs",
            ],
        ]
        for command in commands:
            print("Running:", " ".join(command), flush=True)
            result = subprocess.call(command, cwd=PROJECT_ROOT, env=env)
            if result:
                return result
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Advisors local operations")
    parser.add_argument(
        "command",
        choices=("start", "stop", "status", "doctor", "backup", "restore", "check"),
    )
    parser.add_argument("snapshot", nargs="?", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--target",
        metavar="PYTEST_NODE",
        help="Select one pytest file or node for check; typing and JavaScript gates still run",
    )
    args = parser.parse_args()
    if args.target is not None and args.command != "check":
        parser.error("--target is only available with check")
    try:
        if args.command == "start":
            start(args.offline)
        elif args.command == "status":
            status()
        elif args.command == "stop":
            stop()
        elif args.command == "doctor":
            return doctor(args.live)
        elif args.command == "backup":
            backup(args.destination)
        elif args.command == "restore":
            if args.snapshot is None or args.destination is None:
                raise ValueError(
                    "Restore requires a snapshot and --destination NEW_DIRECTORY"
                )
            restore(args.snapshot, args.destination)
        elif args.command == "check":
            return check(args.target)
        return 0
    except (ValueError, OSError) as error:
        print(f"Could not complete {args.command}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
