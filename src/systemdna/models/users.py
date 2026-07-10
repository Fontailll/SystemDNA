from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    username: str = Field(...)
    uid: int | None = Field(default=None)
    gid: int | None = Field(default=None)
    groups: list[str] = Field(default_factory=list)
    shell: str | None = Field(default=None)
    home: str | None = Field(default=None)


class GroupInfo(BaseModel):
    name: str = Field(...)
    gid: int | None = Field(default=None)
    members: list[str] = Field(default_factory=list)


class UsersInfo(BaseModel):
    users: list[UserInfo] = Field(default_factory=list)
    groups: list[GroupInfo] = Field(default_factory=list)
    current_user: str = Field(...)
