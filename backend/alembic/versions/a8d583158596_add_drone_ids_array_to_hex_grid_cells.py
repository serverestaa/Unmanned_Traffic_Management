"""add drone_ids array to hex_grid_cells

Revision ID: a8d583158596
Revises: 147cacf5f564
Create Date: 2025-05-25 11:20:52.879248

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a8d583158596'
down_revision = '147cacf5f564'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only keep the relevant changes for hex_grid_cells and current_drone_positions
    op.create_index('idx_current_pos_hex_cell_status', 'current_drone_positions', ['hex_cell_id', 'status'], unique=False)
    op.create_index(op.f('ix_current_drone_positions_hex_cell_id'), 'current_drone_positions', ['hex_cell_id'], unique=False)
    op.add_column('hex_grid_cells', sa.Column('drones_count', sa.Integer(), nullable=True))
    op.add_column('hex_grid_cells', sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.create_index('idx_hex_grid_cell_geometry', 'hex_grid_cells', ['geometry'], unique=False, postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('idx_hex_grid_cell_geometry', table_name='hex_grid_cells', postgresql_using='gist')
    op.drop_column('hex_grid_cells', 'last_updated')
    op.drop_column('hex_grid_cells', 'drones_count')
    op.drop_index(op.f('ix_current_drone_positions_hex_cell_id'), table_name='current_drone_positions')
    op.drop_index('idx_current_pos_hex_cell_status', table_name='current_drone_positions') 