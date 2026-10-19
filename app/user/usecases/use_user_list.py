from sqlalchemy.orm import Session, selectinload

from app.user.user_entity import User


def execute(
    db: Session, current_user: User, skip: int = 0, limit: int = 50
) -> list[User]:
    # Los roles en una sola consulta, no una por usuario
    return (
        db.query(User)
        .options(selectinload(User.roles))
        .order_by(User.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
