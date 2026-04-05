"""create company_status_history table

Revision ID: eff90a3e73c1
Revises: 853a1f55ef78
Create Date: 2026-04-05 06:46:35
"""

from alembic import op
import sqlalchemy as sa
from app.models.company import CompanyStatus

revision = 'eff90a3e73c1'
down_revision = '853a1f55ef78'
branch_labels = None
depends_on = None


def upgrade():
    # 1️⃣ Create ENUM type in DB if it doesn't exist
    sa.Enum(CompanyStatus, name='companystatus').create(op.get_bind(), checkfirst=True)

    # 2️⃣ Create table
    op.create_table(
        'company_status_history',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('company_id', sa.Integer, sa.ForeignKey('companies.company_id'), nullable=False),
        sa.Column('old_status', sa.Enum(CompanyStatus, name='companystatus'), nullable=False),
        sa.Column('new_status', sa.Enum(CompanyStatus, name='companystatus'), nullable=False),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('changed_by', sa.Integer, nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    # Drop table first
    op.drop_table('company_status_history')

    # ⚠ Only drop ENUM if no other table uses it (otherwise remove this)
    op.execute('DROP TYPE IF EXISTS "companystatus"')