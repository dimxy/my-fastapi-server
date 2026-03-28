import uuid
from typing import Any

from sqlmodel import Field, Session, select
from pydantic import BaseModel, EmailStr

from app.core.security import get_password_hash, verify_password
from app.models import LlmJob, LlmJobCreate, UserBase, UserDB, UserUpdate

def create_user(*, session: Session, user_create: UserBase) -> UserDB:
    db_obj = UserDB.model_validate(user_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def create_oauth_user(*, session: Session, email: EmailStr, is_superuser: bool, is_active: bool) -> uuid.UUID:
    user_create = UserBase(
        email=email,
        is_superuser=is_superuser,
        is_active=is_active,
    )
    db_obj = UserDB.model_validate(user_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj.id

def update_user(*, session: Session, db_user: UserDB, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_user_id(*, session: Session, email: str) -> uuid.UUID | None:
    session_user = get_user_by_email(session=session, email=email)
    if session_user is not None:
        return session_user.id
    return session_user

def get_user_by_email(*, session: Session, email: str) -> UserDB | None:
    statement = select(UserDB).where(UserDB.email == email)
    session_user = session.exec(statement).first()
    return session_user

def create_llm_job(*, session: Session, job_in: LlmJobCreate, owner_id: uuid.UUID) -> LlmJob:
    db_job = LlmJob.model_validate(job_in, update={"owner_id": owner_id})
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job

def get_llm_job(*, session: Session, job_id: str) -> LlmJob | None:
    statement = select(LlmJob).where(LlmJob.job_id == job_id)
    session_user = session.exec(statement).first()
    return session_user

def get_new_id() -> uuid.UUID:
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    return id
