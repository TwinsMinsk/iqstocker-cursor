"""merge vip_group_removal_notification and e1f2a3b4c5d6

Revision ID: 7a9da5cfdbaa
Revises: vip_group_removal_notification, e1f2a3b4c5d6
Create Date: 2025-11-28 17:02:16.045333

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a9da5cfdbaa'
down_revision = ('vip_group_removal_notification', 'e1f2a3b4c5d6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
