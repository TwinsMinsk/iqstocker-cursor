#!/usr/bin/env python3
"""Update referral rewards - delete old and create new ones."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.database import AsyncSessionLocal
from database.models import ReferralReward, RewardType
from sqlalchemy import delete


NEW_REWARDS = [
    {
        'reward_id': 1,
        'name': '1 месяц подписки PRO бесплатно',
        'cost': 2,
        'reward_type': RewardType.SUPPORT_REQUEST,
        'value': None
    },
    {
        'reward_id': 2,
        'name': '1 месяц подписки ULTRA бесплатно',
        'cost': 3,
        'reward_type': RewardType.SUPPORT_REQUEST,
        'value': None
    },
    {
        'reward_id': 3,
        'name': 'Пожизненный доступ в IQ Radar или пожизненный PRO',
        'cost': 5,
        'reward_type': RewardType.SUPPORT_REQUEST,
        'value': None
    },
    {
        'reward_id': 4,
        'name': 'Пожизненный доступ к боту с подпиской ULTRA',
        'cost': 10,
        'reward_type': RewardType.SUPPORT_REQUEST,
        'value': None
    },
]


async def main():
    """Update referral rewards - delete old and create new ones."""
    async with AsyncSessionLocal() as session:
        try:
            # Удаляем все старые награды
            delete_query = delete(ReferralReward)
            result = await session.execute(delete_query)
            deleted_count = result.rowcount
            print(f"🗑️  Удалено старых наград: {deleted_count}")
            
            # Создаем новые награды
            for reward_data in NEW_REWARDS:
                new_reward = ReferralReward(**reward_data)
                session.add(new_reward)
                print(f"✅ Добавлена награда: {reward_data['name']} (ID: {reward_data['reward_id']}, Стоимость: {reward_data['cost']} баллов)")
            
            await session.commit()
            print(f"\n✅ Обновление наград завершено! Всего новых наград: {len(NEW_REWARDS)}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при обновлении наград: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    asyncio.run(main())

