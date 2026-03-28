from click import UUID
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
# NOTE previous name was 'User' and apparently it is a special name for alembic (alembic created 'user' table incorrectly, with a single column 'user')
class UserDB(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    job_ids: list["LlmJob"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None

class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Video generation job
class LlmJobBase(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    prompt: str = Field(min_length=1, max_length=255)
    job_id: str = Field(default=None, max_length=255)
    file_path: str | None = Field(default=None, max_length=255)
    is_finished: bool = Field(default=False)


# Properties to receive on LLM job creation
class LlmJobCreate(LlmJobBase):
    pass


# Properties to receive on job update
class LlmJobUpdate(LlmJobBase):
    file_path: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    is_finished: bool


# Database model, database table inferred from class name
class LlmJob(LlmJobBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="userdb.id", nullable=False, ondelete="CASCADE"
    )
    owner: UserDB | None = Relationship(back_populates="job_ids")


# Properties to return via API, id is always required
class LlmJobPublic(LlmJobBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class LlmJobsPublic(SQLModel):
    data: list[LlmJobPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str

# Unused
# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

# Unused
# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None

# Unused
class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
