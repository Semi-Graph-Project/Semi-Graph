"""Isolated Streamlit processes and Chrome for end-to-end UI tests."""

import os
import shutil
import signal
import socket
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import urlopen

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def browser_type_launch_args():
    args = {"headless": True, "args": ["--no-sandbox"]}
    if shutil.which("google-chrome"):
        args["channel"] = "chrome"
    return args


@contextmanager
def _serve_streamlit(script, log_path, extra_env=None):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = os.environ.copy()
    env.update(extra_env or {})
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(script),
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        url = f"http://127.0.0.1:{port}"
        try:
            deadline = monotonic() + 40
            while monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with urlopen(f"{url}/_stcore/health", timeout=1) as response:
                        if response.status == 200:
                            yield url
                            return
                except (OSError, URLError):
                    sleep(0.2)
            raise RuntimeError(
                f"Streamlit did not start: {log_path.read_text(encoding='utf-8')[-3000:]}"
            )
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)


@pytest.fixture(scope="session")
def start_streamlit():
    return _serve_streamlit


@pytest.fixture(scope="module")
def fake_app_server(start_streamlit, tmp_path_factory):
    directory = tmp_path_factory.mktemp("comparison_ui")
    calls = directory / "calls.jsonl"
    with start_streamlit(
        ROOT / "tests" / "e2e" / "fixture_app.py",
        directory / "streamlit.log",
        {"SEMIGRAPH_E2E_CALL_LOG": str(calls)},
    ) as url:
        yield url, calls
