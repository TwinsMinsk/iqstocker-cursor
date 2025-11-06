#!/usr/bin/env python3
"""Initialize referral rewards in database."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.database import AsyncSessionLocal
from database.models import ReferralReward, RewardType


DEFAULT_REWARDS = [
    {
        'reward_id': 1,
        'name': 'Скидка 25% (PRO/ULTRA)',
        'cost': 1,
        'reward_type': RewardType.LINK,
        'value': None
    },
    {
        'reward_id': 2,
        'name': 'Скидка 50% (PRO/ULTRA)',
        'cost': 2,
        'reward_type': RewardType.LINK,
        'value': None
    },
    {
        'reward_id': 3,
        'name': '1 месяц PRO бесплатно',
        'cost': 3,
        'reward_type': RewardType.FREE_PRO,
        'value': None
    },
    {
        'reward_id': 4,
        'name': '1 месяц ULTRA бесплатно',
        'cost': 4,
        'reward_type': RewardType.FREE_ULTRA,
        'value': None
    },
    {
        'reward_id': 5,
        'name': 'Доступ в IQ Radar',
        'cost': 5,
        'reward_type': RewardType.LINK,
        'value': None
    },
]


async def main():
    """Initialize referral rewards in database."""
    async with AsyncSessionLocal() as session:
        try:
            for reward_data in DEFAULT_REWARDS:
                # Check if reward already exists
                existing = await session.get(ReferralReward, reward_data['reward_id'])
                
                if not existing:
                    # Create new reward
                    new_reward = ReferralReward(**reward_data)
                    session.add(new_reward)
                    print(f"✅ Добавлена награда: {reward_data['name']} (ID: {reward_data['reward_id']})")
                else:
                    print(f"⚠️  Награда уже существует: {reward_data['name']} (ID: {reward_data['reward_id']})")
            
            await session.commit()
            print(f"\n✅ Инициализация наград завершена! Всего наград: {len(DEFAULT_REWARDS)}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при инициализации наград: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    asyncio.run(main())

