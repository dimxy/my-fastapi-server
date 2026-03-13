from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.core.db import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

'''
def get_db_0() -> Session:
    return Session(engine)
'''

SessionDep = Annotated[Session, Depends(get_db)]
