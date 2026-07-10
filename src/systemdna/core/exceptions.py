from __future__ import annotations


class SystemDNAError(Exception):
    def __init__(self, message: str, original: BaseException | None = None) -> None:
        super().__init__(message)
        self.original = original


class CollectorError(SystemDNAError):
    pass


class SnapshotError(SystemDNAError):
    pass


class DiffError(SystemDNAError):
    pass


class DoctorError(SystemDNAError):
    pass


class ExportError(SystemDNAError):
    pass


class StorageError(SystemDNAError):
    pass


class PluginError(SystemDNAError):
    pass


class ConfigError(SystemDNAError):
    pass
