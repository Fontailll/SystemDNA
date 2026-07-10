from __future__ import annotations

import os
import stat as stat_module
from datetime import datetime
from pathlib import Path

from systemdna.models.configuration import ConfigurationInfo, TrackedFile
from systemdna.utils.hash import hash_file


def _tracked_file_paths() -> list[Path]:
    return [
        Path("/etc/fstab"),
        Path("/etc/hosts"),
        Path("/etc/hostname"),
        Path("/etc/resolv.conf"),
        Path("/etc/ssh/sshd_config"),
        Path("/etc/sudoers"),
        Path("/etc/pacman.conf"),
        Path("/etc/default/grub"),
    ]


def _stat_file(path: Path) -> os.stat_result | None:
    try:
        return path.stat()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _get_file_permissions(path: Path) -> str | None:
    try:
        st = path.stat()
        stat_module.filemode(st.st_mode)
        return oct(stat_module.S_IMODE(st.st_mode))
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _modified_time_str(st: os.stat_result) -> str | None:
    try:
        dt = datetime.fromtimestamp(st.st_mtime)
        return dt.isoformat()
    except (ValueError, OSError):
        return None


def get_tracked_files() -> list[TrackedFile]:
    tracked: list[TrackedFile] = []
    for path in _tracked_file_paths():
        if not path.exists():
            continue
        try:
            file_hash = hash_file(path)
        except (FileNotFoundError, PermissionError, OSError):
            continue
        st = _stat_file(path)
        if st is None:
            continue
        tracked.append(
            TrackedFile(
                path=str(path),
                hash=file_hash,
                size_bytes=st.st_size,
                modified_time=_modified_time_str(st),
                permissions=_get_file_permissions(path),
            )
        )
    return tracked


def get_configuration_info() -> ConfigurationInfo:
    return ConfigurationInfo(tracked_files=get_tracked_files())
