from pydantic import BaseModel, Field


class FirewallStatus(BaseModel):
    enabled: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    rules_count: int | None = Field(default=None)


class SecurityInfo(BaseModel):
    firewall: FirewallStatus | None = Field(default=None)
    selinux_enforcing: bool | None = Field(default=None)
    apparmor_enforcing: bool | None = Field(default=None)
    kernel_lockdown: str | None = Field(default=None)
    ssh_password_auth: bool | None = Field(default=None)
    ssh_root_login: bool | None = Field(default=None)
