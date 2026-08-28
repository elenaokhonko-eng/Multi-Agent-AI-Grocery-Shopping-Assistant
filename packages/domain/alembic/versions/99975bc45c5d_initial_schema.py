"""Superseded by 0001_canonical_schema"""
from typing import Sequence, Union
from alembic import op

revision: str = '99975bc45c5d'
down_revision: Union[str, Sequence[str], None] = '0001_canonical_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
