"""
Alembic migration script template.

Ref: docs/Database.md § 4
"""

# Revision identifiers, used by Alembic.
revision: str
down_revision: str | None
branch_labels: str | None
depends_on: str | None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
