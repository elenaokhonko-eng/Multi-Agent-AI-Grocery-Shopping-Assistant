"""Superseded by 0001_canonical_schema"""

from collections.abc import Sequence

revision: str = "99975bc45c5d"
down_revision: str | Sequence[str] | None = "0001_canonical_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
