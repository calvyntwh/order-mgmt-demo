"""initial auth schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-08-21
"""

from __future__ import annotations

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Apply the repository SQL initializer to ensure schema parity.
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
    )
    sql_path = os.path.join(repo_root, "infra", "postgres", "init-auth.sql")
    with open(sql_path, encoding="utf-8") as fh:
        sql = fh.read()
    op.execute(sql)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
