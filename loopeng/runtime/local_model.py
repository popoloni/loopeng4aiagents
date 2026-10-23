"""Portable, standard-library setup and bounded launcher for pinned llama.cpp."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[2]
REVISION = "0756e83fc1529e207af783782905bc98a8ef0770"
MODEL_REVISION = "a9a60d009fa7ff9606305047c2bf77ac25dbec49"
MODEL_NAME = "Qwen3-4B-Q4_K_M.gguf"
MODEL_SHA256 = "7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5"
MODEL_BYTES = 2497280256
ARTIFACTS = {
    "DarwinARM64": ("llama-b11799-bin-macos-arm64.tar.gz", "51c3471c9212b41e51a6696c0b966628fa45d625385fdb024c4483e8d3154dca", 16136376),
    "Linuxx64": ("llama-b11799-bin-ubuntu-x64.tar.gz", "4920c65448350c28f8ce7b35eec91566807e0f111c25a0df2d5fc12a1ed1716a", 22300522),
}


def host_target() -> str:
    pair = (platform.system(), platform.machine().lower())
    if pair == ("Darwin", "arm64"):
        return "DarwinARM64"
    if pair in (("Linux", "x86_64"), ("Linux", "amd64")):
        return "Linuxx64"
    raise ValueError(f"Unsupported native host: {pair}")


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return stream_hash(stream)


def stream_hash(stream) -> str:
    digest = hashlib.sha256()
    while block := stream.read(1024 * 1024):
        digest.update(block)
    return digest.hexdigest()


def check_hash(path: Path, expected: str, size: int) -> None:
    if not path.is_file() or path.stat().st_size != size or sha256(path) != expected:
        raise ValueError(f"Artifact size/hash mismatch: {path}")


def external_path(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path == REPO or path.is_relative_to(REPO) or REPO.is_relative_to(path):
        raise ValueError("Output must be outside, and not an ancestor of, the repository")
    return path


def fresh_directory(path: Path) -> Path:
    # Reject symlinks even when they point outside the repository.
    absolute = path.expanduser().absolute()
    if any(p.is_symlink() for p in (absolute, *absolute.parents)):
        raise ValueError("Output paths must not contain symlinks")
    path = external_path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def download(url: str, destination: Path, expected: str, size: int) -> None:
    """No resume or overwrite; failed partials remain for inspection."""
    partial = destination.with_suffix(destination.suffix + ".partial")
    if destination.exists():
        raise FileExistsError(destination)
    count = 0
    with urllib.request.urlopen(url, timeout=60) as response, partial.open("xb") as out:
        while block := response.read(1024 * 1024):
            count += len(block)
            if count > size:
                raise ValueError("Download exceeds pinned size")
            out.write(block)
    check_hash(partial, expected, size)
    partial.rename(destination)


def archive_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    names: set[str] = set()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "llama-b11799":
            raise ValueError("Unsafe archive path")
        if member.name in names or not (member.isdir() or member.isfile() or member.issym()):
            raise ValueError("Unsupported or duplicate archive member")
        names.add(member.name)
        if member.issym():
            # The pinned releases use only same-directory library symlinks.
            link = PurePosixPath(member.linkname)
            if link.is_absolute() or len(link.parts) != 1 or member.linkname in ("", ".", ".."):
                raise ValueError("Unsafe archive link")
    links = {PurePosixPath(m.name) for m in members if m.issym()}
    if any(any(parent in links for parent in PurePosixPath(m.name).parents) for m in members):
        raise ValueError("Archive member nested beneath symlink")
    return members


def runtime_archive(runtime: Path, target: str) -> Path:
    name, digest, size = ARTIFACTS[target]
    archive = runtime / name
    if not archive.exists():
        archive = runtime / "downloads" / name
    check_hash(archive, digest, size)
    return archive


def verify_runtime(runtime: Path, model: Path, target: str) -> Path:
    """Compare every extracted file/link with the pinned archive, including libraries."""
    archive = runtime_archive(runtime, target)
    tree_root = runtime if (runtime / "llama-b11799").exists() else runtime / "llama_cpp"
    with tarfile.open(archive, "r:gz") as bundle:
        members = archive_members(bundle)
        for member in members:
            path = tree_root / member.name
            if member.issym():
                if not path.is_symlink() or os.readlink(path) != member.linkname:
                    raise ValueError(f"Runtime link mismatch: {path}")
            elif path.is_symlink():
                raise ValueError(f"Unexpected runtime symlink: {path}")
            elif member.isdir():
                if not path.is_dir():
                    raise ValueError(f"Missing runtime directory: {path}")
            else:
                stream = bundle.extractfile(member)
                if stream is None or not path.is_file() or sha256(path) != stream_hash(stream):
                    raise ValueError(f"Runtime file mismatch: {path}")
        expected = {m.name.rstrip("/") for m in members}
        actual = {p.relative_to(tree_root).as_posix() for p in (tree_root / "llama-b11799").rglob("*")}
        if actual - expected:
            raise ValueError("Unexpected files in runtime library directory")
    check_hash(model, MODEL_SHA256, MODEL_BYTES)
    binary = tree_root / "llama-b11799/llama-server"
    if not os.access(binary, os.X_OK):
        raise ValueError("Server is not executable")
    return binary


def setup(runtime: Path, target: str, archive: Path | None, model: Path | None, allow_download: bool) -> None:
    if (archive is None or model is None) and not allow_download:
        raise ValueError("Supply --archive and --model, or explicitly --allow-download")
    name, digest, size = ARTIFACTS[target]
    if archive is not None:
        check_hash(archive, digest, size)
    if model is not None:
        model = model.expanduser().resolve(strict=True)
        check_hash(model, MODEL_SHA256, MODEL_BYTES)
    runtime = fresh_directory(runtime)
    write_json(runtime / "setup.json", {"status": "started", "target": target})
    try:
        if archive is None:
            download(f"https://github.com/ggml-org/llama.cpp/releases/download/b11799/{name}", runtime / name, digest, size)
        else:
            shutil.copyfile(archive, runtime / name)
        runtime_archive(runtime, target)
        with tarfile.open(runtime / name, "r:gz") as bundle:
            members = archive_members(bundle)
            # Manually extract only regular files/directories and validated local links.
            for member in members:
                path = runtime / member.name
                path.parent.mkdir(parents=True, exist_ok=True)
                if member.isdir():
                    path.mkdir(exist_ok=True)
                elif member.isfile():
                    stream = bundle.extractfile(member)
                    if stream is None:
                        raise ValueError("Missing archive data")
                    with path.open("xb") as output:
                        shutil.copyfileobj(stream, output)
                    path.chmod(member.mode & 0o755)
            for member in members:
                if member.issym():
                    (runtime / member.name).symlink_to(member.linkname)
        if model is None:
            model = runtime / MODEL_NAME
            download(f"https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/{MODEL_REVISION}/{MODEL_NAME}", model, MODEL_SHA256, MODEL_BYTES)
        verify_runtime(runtime, model, target)
        write_json(runtime / "setup.json", {"status": "verified", "target": target, "model": str(model), "revision": REVISION})
    except Exception as exc:
        write_json(runtime / "setup.json", {"status": "failed", "error_type": type(exc).__name__})
        raise


def server_command(binary: Path, model: Path, port: int, metal: bool) -> list[str]:
    return [str(binary), "--model", str(model), "--alias", "loopeng-qwen3-4b",
            "--host", "127.0.0.1", "--port", str(port), "--ctx-size", "16384",
            "--parallel", "1", "--threads", "6", "--threads-batch", "6",
            "--n-gpu-layers", "99" if metal else "0", "--batch-size", "256",
            "--ubatch-size", "128", "--cache-type-k", "q8_0", "--cache-type-v", "q8_0",
            "--flash-attn", "on", "--jinja", "--reasoning", "off", "--no-repack",
            "--no-warmup", "--no-context-shift", "--n-predict", "3072", "--no-agent",
            "--no-ui-mcp-proxy", "--no-webui", "--cache-ram", "0", "--ctx-checkpoints", "0"]


def serve(runtime: Path, model: Path, evidence: Path, port: int, metal: bool,
          max_seconds: int, startup_seconds: int, grace: int) -> int:
    target = host_target()
    if metal and target != "DarwinARM64":
        raise ValueError("--metal requires native Darwin ARM64")
    if not 1 <= port <= 65535 or min(max_seconds, startup_seconds, grace) < 1:
        raise ValueError("Port and time budgets must be positive and valid")
    runtime, model = runtime.resolve(), model.resolve()
    binary = verify_runtime(runtime, model, target)
    with socket.socket() as probe:
        # Ignore closed connections in TIME_WAIT, while still rejecting a listener.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", port))
    evidence = fresh_directory(evidence)
    command = server_command(binary, model, port, metal)
    receipt = {"command": command, "target": target, "model_sha256": MODEL_SHA256,
               "server_sha256": sha256(binary), "ready": False}
    process = None
    stopped = False
    started = time.monotonic()
    previous = {}

    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.signal(sig, stop)
        with (evidence / "stdout.txt").open("xb") as out, (evidence / "stderr.txt").open("xb") as err:
            process = subprocess.Popen(command, cwd=runtime, stdout=out, stderr=err,
                                       env={"PATH": os.defpath, "LANG": "C", "TZ": "UTC"})
            receipt["pid"] = process.pid
            write_json(evidence / "START.json", receipt)
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while process.poll() is None and not stopped:
                elapsed = time.monotonic() - started
                if elapsed >= max_seconds:
                    receipt["stop_reason"] = "runtime_limit"
                    break
                if not receipt["ready"]:
                    if elapsed >= startup_seconds:
                        raise TimeoutError("Server health deadline exceeded; inspect stderr.txt")
                    try:
                        with opener.open(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                            receipt["ready"] = response.status == 200
                        if receipt["ready"]:
                            write_json(evidence / "READY.json", receipt)
                            print(f"READY http://127.0.0.1:{port}/v1/chat/completions", flush=True)
                    except OSError:
                        pass
                time.sleep(0.2)
            if stopped:
                receipt["stop_reason"] = "signal"
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=grace)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=grace)
                    receipt["forced_kill"] = True
            receipt["exit_code"] = process.returncode
        receipt["elapsed_seconds"] = time.monotonic() - started
        write_json(evidence / "FINISH.json", receipt)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return 0 if receipt["ready"] and (stopped or receipt.get("stop_reason") == "runtime_limit") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("pins", help="print pinned artifact identities; no network or writes")
    prepare = commands.add_parser("setup")
    prepare.add_argument("--runtime", type=Path, required=True)
    prepare.add_argument("--target", choices=ARTIFACTS, default=None)
    prepare.add_argument("--archive", type=Path)
    prepare.add_argument("--model", type=Path)
    prepare.add_argument("--allow-download", action="store_true")
    for name in ("preflight", "serve"):
        sub = commands.add_parser(name)
        sub.add_argument("--runtime", type=Path, required=True)
        sub.add_argument("--model", type=Path, required=True)
        if name == "serve":
            sub.add_argument("--evidence", type=Path, required=True)
            sub.add_argument("--port", type=int, default=18080)
            sub.add_argument("--metal", action="store_true")
            sub.add_argument("--max-seconds", type=int, default=2400)
            sub.add_argument("--startup-seconds", type=int, default=120)
            sub.add_argument("--grace", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        if args.action == "pins":
            print(json.dumps({"runtimes": ARTIFACTS, "revision": REVISION, "model_revision": MODEL_REVISION,
                              "model": MODEL_NAME, "model_sha256": MODEL_SHA256, "model_bytes": MODEL_BYTES}, indent=2))
        elif args.action == "setup":
            setup(args.runtime, args.target or host_target(), args.archive, args.model, args.allow_download)
        elif args.action == "preflight":
            print(verify_runtime(args.runtime.resolve(), args.model.resolve(), host_target()))
        else:
            return serve(args.runtime, args.model, args.evidence, args.port, args.metal,
                         args.max_seconds, args.startup_seconds, args.grace)
    except (OSError, ValueError, tarfile.TarError) as exc:
        print(f"Local runtime failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
