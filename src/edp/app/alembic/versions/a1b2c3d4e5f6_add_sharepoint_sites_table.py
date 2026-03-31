"""Add sharepoint_sites table and site_name column

Revision ID: a1b2c3d4e5f6
Revises: 66ff1cf986bd
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '66ff1cf986bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = reflection.Inspector.from_engine(op.get_bind())
    table_names = inspector.get_table_names()

    if 'sharepoint_sites' not in table_names:
        op.create_table(
            'sharepoint_sites',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, index=True),
            sa.Column('site_url', sa.String(), nullable=False, unique=True, index=True),
            sa.Column('graph_site_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('display_name', sa.String(), nullable=True),
            sa.Column('web_url', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    columns = [col['name'] for col in inspector.get_columns('files')]
    indexes = [idx['name'] for idx in inspector.get_indexes('files')]

    if 'site_name' not in columns:
        op.add_column('files', sa.Column('site_name', sa.String(), nullable=True))

    if 'ix_files_site_name' not in indexes:
        op.create_index(op.f('ix_files_site_name'), 'files', ['site_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_files_site_name'), table_name='files')
    op.drop_column('files', 'site_name')
    op.drop_table('sharepoint_sites')
