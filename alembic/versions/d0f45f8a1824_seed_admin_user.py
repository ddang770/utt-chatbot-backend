"""seed admin user

Revision ID: d0f45f8a1824
Revises: 69b2271d1176
Create Date: 2025-09-15 20:58:27.928416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.auth.util import get_password_hash

# revision identifiers, used by Alembic.
revision: str = 'd0f45f8a1824'
down_revision: Union[str, Sequence[str], None] = '69b2271d1176'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

admins = sa.table(
    "admins",
    sa.column("username", sa.String),
    sa.column("email", sa.String),
    sa.column("password", sa.String),
)

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        admins.insert().values(
            username="Dang Nguyen",
            email="admin@example.com",
            password=get_password_hash("123456")
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(admins.delete().where(admins.c.email == "admin@example.com"))
