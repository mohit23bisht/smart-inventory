"""Add low stock threshold

Revision ID: 1994008255da
Revises: 9ee93bab31ca
Create Date: 2026-08-28 16:37:49.056732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1994008255da'
down_revision: Union[str, Sequence[str], None] = '9ee93bab31ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add a temporary database default so existing
    # products receive a valid threshold.
    op.add_column(
        'products',
        sa.Column(
            'low_stock_threshold',
            sa.Integer(),
            nullable=False,
            server_default='10',
        ),
    )

    # Remove the temporary database default.
    #
    # The Python model already provides default=10
    # for newly created Product objects.
    op.alter_column(
        'products',
        'low_stock_threshold',
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        'products',
        'low_stock_threshold',
    )