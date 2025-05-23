"""change_user_id_to_uuid

Revision ID: 8480bc9116d3
Revises: 
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = '8480bc9116d3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create users_new with a temp old_id column
    op.create_table(
        'users_new',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('old_id', sa.Integer(), nullable=True),  # temp mapping
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String()),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('role', sa.String(), default='pilot'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('email', name='users_email_key')
    )

    # 2. Insert users with mapping
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO users_new (id, old_id, email, full_name, phone, hashed_password, is_active, role, created_at)
        SELECT gen_random_uuid(), id, email, full_name, phone, hashed_password, is_active, role, created_at
        FROM users
    """))

    # 3. Create new UUID columns in related tables
    op.add_column('drones', sa.Column('owner_uuid', UUID(as_uuid=True), nullable=True))
    op.add_column('flight_requests', sa.Column('pilot_uuid', UUID(as_uuid=True), nullable=True))
    op.add_column('flight_requests', sa.Column('approved_by_uuid', UUID(as_uuid=True), nullable=True))
    op.add_column('alerts', sa.Column('resolved_by_uuid', UUID(as_uuid=True), nullable=True))

    # 4. Update related tables using the mapping
    connection.execute(sa.text("""
        UPDATE drones d
        SET owner_uuid = u.id
        FROM users_new u
        WHERE d.owner_id = u.old_id
    """))
    connection.execute(sa.text("""
        UPDATE flight_requests fr
        SET pilot_uuid = u.id
        FROM users_new u
        WHERE fr.pilot_id = u.old_id
    """))
    connection.execute(sa.text("""
        UPDATE flight_requests fr
        SET approved_by_uuid = u.id
        FROM users_new u
        WHERE fr.approved_by = u.old_id
    """))
    connection.execute(sa.text("""
        UPDATE alerts a
        SET resolved_by_uuid = u.id
        FROM users_new u
        WHERE a.resolved_by = u.old_id
    """))

    # 5. Drop old foreign key constraints
    op.drop_constraint('drones_owner_id_fkey', 'drones', type_='foreignkey')
    op.drop_constraint('flight_requests_pilot_id_fkey', 'flight_requests', type_='foreignkey')
    op.drop_constraint('flight_requests_approved_by_fkey', 'flight_requests', type_='foreignkey')
    op.drop_constraint('alerts_resolved_by_fkey', 'alerts', type_='foreignkey')

    # 6. Drop old columns
    op.drop_column('drones', 'owner_id')
    op.drop_column('flight_requests', 'pilot_id')
    op.drop_column('flight_requests', 'approved_by')
    op.drop_column('alerts', 'resolved_by')

    # 7. Rename new columns
    op.alter_column('drones', 'owner_uuid', new_column_name='owner_id')
    op.alter_column('flight_requests', 'pilot_uuid', new_column_name='pilot_id')
    op.alter_column('flight_requests', 'approved_by_uuid', new_column_name='approved_by')
    op.alter_column('alerts', 'resolved_by_uuid', new_column_name='resolved_by')

    # 8. Create new foreign key constraints
    op.create_foreign_key('drones_owner_id_fkey', 'drones', 'users_new', ['owner_id'], ['id'])
    op.create_foreign_key('flight_requests_pilot_id_fkey', 'flight_requests', 'users_new', ['pilot_id'], ['id'])
    op.create_foreign_key('flight_requests_approved_by_fkey', 'flight_requests', 'users_new', ['approved_by'], ['id'])
    op.create_foreign_key('alerts_resolved_by_fkey', 'alerts', 'users_new', ['resolved_by'], ['id'])

    # 9. Drop the old_id column from users_new after all updates
    op.drop_column('users_new', 'old_id')

    # 10. Drop old users table and rename new one
    op.drop_table('users')
    op.rename_table('users_new', 'users')


def downgrade() -> None:
    # This is a complex migration that changes primary keys and foreign keys
    # Downgrading would require recreating all the data with new IDs
    # It's recommended to take a backup before running this migration
    # and restore from backup if downgrade is needed
    pass 