from pydantic import BaseModel, Field


class CpuInfo(BaseModel):
    model: str = Field(...)
    vendor: str = Field(...)
    logical_cores: int = Field(...)
    physical_cores: int | None = Field(default=None)
    clock_speed_mhz: float | None = Field(default=None)


class MemoryInfo(BaseModel):
    total_bytes: int = Field(...)
    available_bytes: int = Field(...)
    used_bytes: int = Field(...)
    percent: float = Field(...)


class DiskInfo(BaseModel):
    device: str = Field(...)
    mount_point: str = Field(...)
    filesystem: str = Field(...)
    total_bytes: int = Field(...)
    used_bytes: int = Field(...)
    free_bytes: int = Field(...)
    percent: float = Field(...)


class SwapInfo(BaseModel):
    total_bytes: int = Field(...)
    used_bytes: int = Field(...)
    free_bytes: int = Field(...)
    percent: float = Field(...)


class HardwareInfo(BaseModel):
    cpu: CpuInfo | None = Field(default=None)
    memory: MemoryInfo | None = Field(default=None)
    swap: SwapInfo | None = Field(default=None)
    disks: list[DiskInfo] = Field(default_factory=list)
