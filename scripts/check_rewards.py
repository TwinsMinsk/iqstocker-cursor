#!/usr/bin/env python3
"""Check rewards in database."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.database import AsyncSessionLocal
from database.models import ReferralReward
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        rewards_query = select(ReferralReward).order_by(ReferralReward.reward_id)
        rewards_result = await session.execute(rewards_query)
        rewards = rewards_result.scalars().all()
        
        print(f"Наград в БД: {len(rewards)}")
        for r in rewards:
            print(f"  ID: {r.reward_id}, Название: {r.name}, Стоимость: {r.cost}, Тип: {r.reward_type.value}")

if __name__ == '__main__':
    asyncio.run(main())

