"""assignments_status_active_inactive

Revision ID: 19fa2c3881ea
Revises: a7fbfc7391ce
Create Date: 2026-02-17 22:50:18.676366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19fa2c3881ea'
down_revision = 'a7fbfc7391ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename old enum type, create new one, migrate data, drop old type
    op.execute("ALTER TYPE assignmentstatus RENAME TO assignmentstatus_old")
    op.execute("CREATE TYPE assignmentstatus AS ENUM ('active', 'inactive')")
    op.execute("""
        ALTER TABLE assignments
        ALTER COLUMN status DROP DEFAULT
    """)
    op.execute("""
        ALTER TABLE assignments
        ALTER COLUMN status TYPE assignmentstatus
        USING CASE
            WHEN status::text IN ('pending', 'in_progress') THEN 'active'::assignmentstatus
            WHEN status::text = 'completed' THEN 'inactive'::assignmentstatus
            ELSE 'active'::assignmentstatus
        END
    """)
    op.execute("ALTER TABLE assignments ALTER COLUMN status SET DEFAULT 'active'")
    op.execute("DROP TYPE assignmentstatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE assignmentstatus RENAME TO assignmentstatus_old")
    op.execute("CREATE TYPE assignmentstatus AS ENUM ('pending', 'in_progress', 'completed')")
    op.execute("ALTER TABLE assignments ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE assignments
        ALTER COLUMN status TYPE assignmentstatus
        USING CASE
            WHEN status::text = 'active' THEN 'pending'::assignmentstatus
            WHEN status::text = 'inactive' THEN 'completed'::assignmentstatus
            ELSE 'pending'::assignmentstatus
        END
    """)
    op.execute("ALTER TABLE assignments ALTER COLUMN status SET DEFAULT 'pending'")
    op.execute("DROP TYPE assignmentstatus_old")
