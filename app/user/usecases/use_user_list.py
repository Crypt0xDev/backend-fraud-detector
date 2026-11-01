from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.user.user_entity import User
from app.user.user_schema import DELETED, SchemaResponse, UserPageOut


def execute(db: Session, page: int, page_size: int) -> UserPageOut:
    query = select(User).where(User.state != DELETED)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    # Los roles en una sola consulta, no una por usuario
    users = db.scalars(query.options(selectinload(User.roles)).order_by(User.created_at.asc(), User.username.asc()).offset((page - 1) * page_size).limit(page_size)).all()
    return UserPageOut(
        items=[SchemaResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )
