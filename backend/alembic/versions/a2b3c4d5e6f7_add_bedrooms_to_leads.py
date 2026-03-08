"""add_bedrooms_to_leads

Revision ID: a2b3c4d5e6f7
Revises: 1135d9c8dd52
Create Date: 2026-03-07 13:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '1135d9c8dd52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('leads', sa.Column('bedrooms', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('leads', 'bedrooms')
