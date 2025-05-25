"""add drone_ids column to hex_grid_cells

Revision ID: 41a0ba4ccbf2
Revises: 1b9ad5dd4063
Create Date: 2025-05-25 11:27:31.633732

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '41a0ba4ccbf2'
down_revision = '1b9ad5dd4063'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('hex_grid_cells', sa.Column('drone_ids', sa.ARRAY(sa.Integer()), nullable=True))


def downgrade() -> None:
    op.drop_column('hex_grid_cells', 'drone_ids') 