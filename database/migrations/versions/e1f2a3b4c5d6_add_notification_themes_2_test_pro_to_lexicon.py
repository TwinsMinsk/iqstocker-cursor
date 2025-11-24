"""add_notification_themes_2_test_pro_to_lexicon

Revision ID: e1f2a3b4c5d6
Revises: d9e8f7a6b5c4
Create Date: 2025-11-24 12:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd9e8f7a6b5c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notification_themes_2_test_pro message to lexicon_entries table."""
    
    # Получаем connection для выполнения сырых SQL запросов
    connection = op.get_bind()
    
    # Текст сообщения
    message_text = """⛔️

Ты получил последнюю подборку тем на тестовом тарифе.

Дальше - выбор за тобой.

Ждать неделю или перейти на PRO / ULTRA прямо сейчас.

Важно - после смены тарифа лимиты мгновенно обновятся - и ты сразу же сможешь запросить новую подборку тем. По сути, это +1 дополнительная неделя и +1 подборка.

Не откладывай решение.

Переходи на PRO или ULTRA сейчас - чтобы не потерять IQ Радар и получить новую подборку тем уже сегодня."""
    
    # Ключ сообщения
    key = 'notification_themes_2_test_pro'
    category = 'LEXICON_RU'
    
    # Проверяем, существует ли уже такая запись
    result = connection.execute(
        sa.text("""
            SELECT key FROM lexicon_entries 
            WHERE key = :key AND category = :category
            LIMIT 1
        """),
        {"key": key, "category": category}
    )
    
    existing = result.fetchone()
    
    if not existing:
        # Вставляем новую запись
        connection.execute(
            sa.text("""
                INSERT INTO lexicon_entries (key, value, category, created_at, updated_at)
                VALUES (:key, :value, :category, :created_at, :updated_at)
            """),
            {
                "key": key,
                "value": message_text,
                "category": category,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        )
        print(f"✅ Added {key} to lexicon_entries (category: {category})")
    else:
        print(f"ℹ️ {key} already exists in lexicon_entries")


def downgrade() -> None:
    """Remove notification_themes_2_test_pro message from lexicon_entries table."""
    
    connection = op.get_bind()
    
    connection.execute(
        sa.text("""
            DELETE FROM lexicon_entries 
            WHERE key = :key AND category = :category
        """),
        {"key": "notification_themes_2_test_pro", "category": "LEXICON_RU"}
    )
    
    print("✅ Removed notification_themes_2_test_pro from lexicon_entries")

