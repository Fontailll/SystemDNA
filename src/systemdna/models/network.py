from pydantic import BaseModel, Field


class NetworkInterface(BaseModel):
    name: str = Field(...)
    mac_address: str | None = Field(default=None)
    ipv4: list[str] = Field(default_factory=list)
    ipv6: list[str] = Field(default_factory=list)
    mtu: int | None = Field(default=None)
    is_up: bool = Field(default=False)


class ListeningPort(BaseModel):
    protocol: str = Field(...)
    port: int = Field(...)
    address: str = Field(...)
    pid: int | None = Field(default=None)
    process: str | None = Field(default=None)


class RouteInfo(BaseModel):
    destination: str = Field(...)
    gateway: str = Field(...)
    netmask: str = Field(...)
    interface: str = Field(...)


class NetworkInfo(BaseModel):
    hostname: str = Field(...)
    domain_name: str | None = Field(default=None)
    dns_servers: list[str] = Field(default_factory=list)
    interfaces: list[NetworkInterface] = Field(default_factory=list)
    listening_ports: list[ListeningPort] = Field(default_factory=list)
    routes: list[RouteInfo] = Field(default_factory=list)
