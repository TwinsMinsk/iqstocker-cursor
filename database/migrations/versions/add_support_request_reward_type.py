"""Add SUPPORT_REQUEST to reward_type_enum

Revision ID: add_support_request
Revises: a1b2c3d4e5f6
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_support_request'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем новое значение в enum, если его еще нет
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'support_request' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'reward_type_enum')
            ) THEN
                ALTER TYPE reward_type_enum ADD VALUE 'support_request';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Удаление значения из enum в PostgreSQL не поддерживается напрямую
    # Можно только пересоздать enum, но это требует удаления всех зависимых объектов
    # Поэтому оставляем пустым - откат не поддерживается
    pass

