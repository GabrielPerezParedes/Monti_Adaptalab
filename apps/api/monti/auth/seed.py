"""Bootstrap first administrator."""
from __future__ import annotations

import os
import sys
from uuid import uuid4

from sqlalchemy import func, select

from ..database import User, connect
from .deps import normalize_login
from .passwords import hash_password


def seed_admin(database_url: str | None = None) -> int:
    login = os.getenv('MONTI_ADMIN_LOGIN', '').strip()
    password = os.getenv('MONTI_ADMIN_PASSWORD', '')
    if not login or not password:
        print('Faltan MONTI_ADMIN_LOGIN y MONTI_ADMIN_PASSWORD.', file=sys.stderr)
        return 2
    if len(password) < 10:
        print('MONTI_ADMIN_PASSWORD debe tener al menos 10 caracteres.', file=sys.stderr)
        return 2

    Session = connect(database_url)
    with Session() as db:
        count = db.scalar(select(func.count()).select_from(User).where(User.role == 'admin')) or 0
        if count > 0:
            print('Bootstrap already done: administrador existente.')
            return 0
        user = User(
            id=str(uuid4()),
            login=normalize_login(login),
            display_name=os.getenv('MONTI_ADMIN_DISPLAY_NAME', 'Administrador MONTI')[:120],
            role='admin',
            password_hash=hash_password(password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f'Administrador inicial creado: {user.login}')
        return 0


def main() -> None:
    raise SystemExit(seed_admin())


if __name__ == '__main__':
    main()
