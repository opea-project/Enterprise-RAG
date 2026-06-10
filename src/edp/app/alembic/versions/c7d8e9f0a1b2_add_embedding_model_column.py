"""Add embedding_model column

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add embedding_model column to track which embedding model was used for each file/link
    op.add_column('files', sa.Column('embedding_model', sa.String(), nullable=True))
    op.add_column('links', sa.Column('embedding_model', sa.String(), nullable=True))
    # Create index for efficient querying
    op.create_index('ix_files_embedding_model', 'files', ['embedding_model'], unique=False)
    op.create_index('ix_links_embedding_model', 'links', ['embedding_model'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_links_embedding_model', table_name='links')
    op.drop_index('ix_files_embedding_model', table_name='files')
    op.drop_column('links', 'embedding_model')
    op.drop_column('files', 'embedding_model')
