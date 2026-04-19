"""Optional pager support for logslice output."""

import os
import shutil
import subprocess
import sys
from typing import Iterable


DEFAULT_PAGER = "less"
PAGER_ENV_VAR = "LOGSLICE_PAGER"


def get_pager() -> str | None:
    """Return pager command from env or default, None if not available."""
    pager = os.environ.get(PAGER_ENV_VAR) or os.environ.get("PAGER") or DEFAULT_PAGER
    if shutil.which(pager.split()[0]):
        return pager
    return None


def should_use_pager(force: bool = False, no_pager: bool = False) -> bool:
    """Determine whether to pipe output through a pager."""
    if no_pager:
        return False
    if force:
        return True
    return sys.stdout.isatty()


def pipe_to_pager(lines: Iterable[str], pager_cmd: str | None = None) -> None:
    """Write lines through a pager process."""
    cmd = pager_cmd or get_pager()
    if cmd is None:
        for line in lines:
            print(line)
        return

    env = os.environ.copy()
    # Ensure less doesn't require user to press q for short output
    if "less" in cmd and "LESS" not in env:
        env["LESS"] = "-RFX"

    try:
        proc = subprocess.Popen(
            cmd.split(),
            stdin=subprocess.PIPE,
            text=True,
            env=env,
        )
        assert proc.stdin is not None
        try:
            for line in lines:
                proc.stdin.write(line + "\n")
        except BrokenPipeError:
            pass
        finally:
            proc.stdin.close()
        proc.wait()
    except FileNotFoundError:
        for line in lines:
            print(line)
