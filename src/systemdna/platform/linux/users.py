from __future__ import annotations

import getpass
import os
from pathlib import Path

from systemdna.models.users import GroupInfo, UserInfo, UsersInfo


def _parse_passwd(path: Path = Path("/etc/passwd")) -> list[dict[str, str]]:
    users: list[dict[str, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, OSError):
        return users
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(":")
        if len(parts) >= 7:
            users.append({
                "username": parts[0],
                "password": parts[1],
                "uid": parts[2],
                "gid": parts[3],
                "gecos": parts[4],
                "home": parts[5],
                "shell": parts[6],
            })
    return users


def _parse_group(path: Path = Path("/etc/group")) -> list[dict[str, str]]:
    groups: list[dict[str, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, OSError):
        return groups
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(":")
        if len(parts) >= 4:
            groups.append({
                "name": parts[0],
                "password": parts[1],
                "gid": parts[2],
                "members": parts[3],
            })
    return groups


def get_users() -> list[UserInfo]:
    passwd_users = _parse_passwd()
    group_entries = _parse_group()
    user_to_groups: dict[str, list[str]] = {}
    for g in group_entries:
        members_str = g.get("members", "")
        if members_str:
            for member_raw in members_str.split(","):
                member = member_raw.strip()
                if member:
                    user_to_groups.setdefault(member, []).append(g["name"])
    users: list[UserInfo] = []
    for u in passwd_users:
        username = u["username"]
        uid_str = u.get("uid", "")
        gid_str = u.get("gid", "")
        users.append(
            UserInfo(
                username=username,
                uid=int(uid_str) if uid_str.isdigit() else None,
                gid=int(gid_str) if gid_str.isdigit() else None,
                groups=user_to_groups.get(username, []),
                shell=u.get("shell") or None,
                home=u.get("home") or None,
            )
        )
    return users


def get_groups() -> list[GroupInfo]:
    group_entries = _parse_group()
    groups: list[GroupInfo] = []
    for g in group_entries:
        gid_str = g.get("gid", "")
        members_str = g.get("members", "")
        members: list[str] = []
        if members_str:
            members = [m.strip() for m in members_str.split(",") if m.strip()]
        groups.append(
            GroupInfo(
                name=g["name"],
                gid=int(gid_str) if gid_str.isdigit() else None,
                members=members,
            )
        )
    return groups


def get_current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", "unknown")


def get_users_info() -> UsersInfo:
    return UsersInfo(
        users=get_users(),
        groups=get_groups(),
        current_user=get_current_user(),
    )
