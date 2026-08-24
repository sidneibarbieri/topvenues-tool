"""Start Streamlit briefly and verify that its health endpoint responds."""

from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def _available_port() -> int:
    with socket.socket() as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return int(server_socket.getsockname()[1])


def _wait_until_healthy(process: subprocess.Popen[str], port: int) -> bool:
    deadline = time.monotonic() + 30
    health_url = f"http://127.0.0.1:{port}/_stcore/health"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen(health_url, timeout=1) as response:  # noqa: S310
                return response.status == 200
        except (URLError, TimeoutError):
            time.sleep(0.25)
    return False


def main() -> int:
    port = _available_port()
    with tempfile.TemporaryDirectory(prefix="topvenues-streamlit-") as temp_dir:
        log_path = Path(temp_dir) / "streamlit.log"
        with log_path.open("w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "web/app.py",
                    "--server.headless=true",
                    f"--server.port={port}",
                    "--server.fileWatcherType=none",
                    "--browser.gatherUsageStats=false",
                ],
                cwd=ROOT,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )
            healthy = _wait_until_healthy(process, port)
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if not healthy:
            raise RuntimeError(
                "Streamlit did not become healthy.\n" + log_path.read_text(encoding="utf-8")
            )
    print(f"Streamlit health check passed on port {port}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
