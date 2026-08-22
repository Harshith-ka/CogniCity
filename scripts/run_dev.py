"""Development runner — starts the API server without Docker."""

import subprocess
import sys


def main():
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
