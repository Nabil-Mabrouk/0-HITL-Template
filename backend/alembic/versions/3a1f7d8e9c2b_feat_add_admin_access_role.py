"""feat: add admin access_role

Revision ID: 3a1f7d8e9c2b
Revises: 44907de619b2
Create Date: 2026-03-22 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a1f7d8e9c2b'
down_revision: Union[str, None] = '44907de619b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # On ajoute la valeur 'admin' à l'enum AccessRole
    # Note: ALTER TYPE ADD VALUE ne peut pas être exécuté dans une transaction
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE accessrole ADD VALUE 'admin'")


def downgrade() -> None:
    # PostgreSQL ne supporte pas facilement la suppression d'une valeur d'un ENUM.
    # On peut au moins remettre à 'user' les tutos qui étaient en 'admin'
    op.execute("UPDATE tutorials SET access_role = 'user' WHERE access_role = 'admin'")
