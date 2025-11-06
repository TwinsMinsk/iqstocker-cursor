"""Referral program management views."""

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import logging

from config.database import AsyncSessionLocal
from database.models import ReferralReward, RewardType, User

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")
logger = logging.getLogger(__name__)


@router.get("/referral", response_class=HTMLResponse)
async def referral_page(request: Request):
    """Referral program management page."""
    try:
        async with AsyncSessionLocal() as session:
            # Get all referral rewards
            rewards_query = select(ReferralReward).order_by(ReferralReward.reward_id)
            rewards_result = await session.execute(rewards_query)
            rewards = rewards_result.scalars().all()
            
            # Get statistics
            # Total users with referrers
            referrers_query = select(func.count(User.id)).where(User.referrer_id.isnot(None))
            referrers_result = await session.execute(referrers_query)
            total_referrers = referrers_result.scalar() or 0
            
            # Total users with referral balance > 0
            balance_query = select(func.count(User.id)).where(User.referral_balance > 0)
            balance_result = await session.execute(balance_query)
            users_with_balance = balance_result.scalar() or 0
            
            # Total referral balance across all users
            total_balance_query = select(func.sum(User.referral_balance))
            total_balance_result = await session.execute(total_balance_query)
            total_balance = total_balance_result.scalar() or 0
            
            # Users with referrals (users who have referred others)
            referrals_query = select(
                User.id,
                User.telegram_id,
                User.referral_balance,
                func.count(User.id).label('referrals_count')
            ).join(
                User, User.referrer_id == User.id
            ).group_by(User.id).limit(10)
            
            # Get top referrers
            top_referrers_query = select(
                User.id,
                User.telegram_id,
                User.referral_balance,
                func.count(User.id).label('referrals_count')
            ).where(
                User.referrer_id.isnot(None)
            ).group_by(User.referrer_id).order_by(desc('referrals_count')).limit(10)
            
            # This is complex, let's simplify
            # Get users who referred others
            referrer_ids_query = select(User.referrer_id).where(User.referrer_id.isnot(None)).distinct()
            referrer_ids_result = await session.execute(referrer_ids_query)
            referrer_ids = [row[0] for row in referrer_ids_result.fetchall()]
            
            top_referrers = []
            if referrer_ids:
                for referrer_id in referrer_ids[:10]:
                    referrer_query = select(User).where(User.id == referrer_id)
                    referrer_result = await session.execute(referrer_query)
                    referrer = referrer_result.scalar_one_or_none()
                    if referrer:
                        # Count referrals
                        referrals_count_query = select(func.count(User.id)).where(User.referrer_id == referrer_id)
                        referrals_count_result = await session.execute(referrals_count_query)
                        referrals_count = referrals_count_result.scalar() or 0
                        top_referrers.append({
                            'id': referrer.id,
                            'telegram_id': referrer.telegram_id,
                            'referral_balance': referrer.referral_balance or 0,
                            'referrals_count': referrals_count
                        })
            
            # Sort by referrals count
            top_referrers.sort(key=lambda x: x['referrals_count'], reverse=True)
            
            return templates.TemplateResponse(
                "referral.html",
                {
                    "request": request,
                    "rewards": rewards,
                    "stats": {
                        "total_referrers": total_referrers,
                        "users_with_balance": users_with_balance,
                        "total_balance": total_balance or 0,
                    },
                    "top_referrers": top_referrers[:10]
                }
            )
    except Exception as e:
        import traceback
        logger.error(f"Error loading referral page: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/referral/reward/update", response_class=JSONResponse)
async def update_reward(
    reward_id: int = Form(...),
    name: str = Form(...),
    cost: int = Form(...),
    reward_type: str = Form(...),
    value: str = Form(None)
):
    """Update referral reward."""
    try:
        async with AsyncSessionLocal() as session:
            reward = await session.get(ReferralReward, reward_id)
            if not reward:
                raise HTTPException(status_code=404, detail="Reward not found")
            
            reward.name = name
            reward.cost = cost
            reward.reward_type = RewardType[reward_type]
            reward.value = value if value else None
            
            await session.commit()
            
            return JSONResponse({
                "success": True,
                "message": f"Награда {reward_id} успешно обновлена"
            })
    except Exception as e:
        import traceback
        logger.error(f"Error updating reward: {e}\n{traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)

