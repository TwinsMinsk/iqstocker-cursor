"""add_notification_themes_2_test_pro

Revision ID: d9e8f7a6b5c4
Revises: 4ea7d508414d
Create Date: 2025-11-24 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'd9e8f7a6b5c4'
down_revision: Union[str, None] = '4a021d17deb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notification_themes_2_test_pro message to broadcast_messages table."""
    
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
    
    # Проверяем, существует ли уже такая запись
    result = connection.execute(
        sa.text("""
            SELECT id FROM broadcast_messages 
            WHERE text LIKE :search_text
            LIMIT 1
        """),
        {"search_text": "%последнюю подборку тем на тестовом тарифе%"}
    )
    
    existing = result.fetchone()
    
    if not existing:
        # Вставляем новую запись
        connection.execute(
            sa.text("""
                INSERT INTO broadcast_messages (text, recipients_count, created_at)
                VALUES (:text, 0, :created_at)
            """),
            {
                "text": message_text,
                "created_at": datetime.utcnow()
            }
        )
        print("✅ Added notification_themes_2_test_pro to broadcast_messages")
    else:
        print("ℹ️ notification_themes_2_test_pro already exists in broadcast_messages")


def downgrade() -> None:
    """Remove notification_themes_2_test_pro message from broadcast_messages table."""
    
    connection = op.get_bind()
    
    connection.execute(
        sa.text("""
            DELETE FROM broadcast_messages 
            WHERE text LIKE :search_text
        """),
        {"search_text": "%последнюю подборку тем на тестовом тарифе%"}
    )
    
    print("✅ Removed notification_themes_2_test_pro from broadcast_messages")

