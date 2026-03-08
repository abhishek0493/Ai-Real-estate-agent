"""replace_is_admin_with_role

Revision ID: 1135d9c8dd52
Revises: 5bb0af5956c4
Create Date: 2026-03-06 06:56:12.597805
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1135d9c8dd52'
down_revision: Union[str, None] = '5bb0af5956c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace is_admin boolean with a role string column
    op.add_column('users', sa.Column('role', sa.String(length=20), server_default='AGENT', nullable=False))
    op.drop_column('users', 'is_admin')


def downgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.drop_column('users', 'role')
