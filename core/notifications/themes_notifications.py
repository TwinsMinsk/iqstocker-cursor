"""Weekly themes notification job."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import logging

from config.database import AsyncSessionLocal
from database.models import User, ThemeRequest, SubscriptionType, Limits
from bot.lexicon import LEXICON_RU
from core.theme_settings import get_theme_cooldown_days_for_session
from core.lexicon.service import LexiconService
from core.notifications.notification_utils import create_main_menu_button_keyboard

logger = logging.getLogger(__name__)


async def notify_new_period_themes(bot: Bot, session: AsyncSession) -> int:
    """
    Отправляет уведомления пользователям о начале нового 7-дневного периода,
    в котором они снова могут запросить темы.
    
    Логика:
    - Определяет текущий период на основе current_tariff_started_at
    - Проверяет, что мы находимся в начале нового периода (первые 15 минут)
    - Проверяет, что уведомление еще не было отправлено для этого периода
    - Проверяет, что у пользователя есть доступные лимиты
    - Отправляет уведомление пользователям, у которых начался новый период
    """
    sent = 0
    try:
        # Получаем всех пользователей с активными тарифами и лимитами
        stmt = select(User, Limits).join(Limits).where(
            User.subscription_type.in_([
                SubscriptionType.TEST_PRO,
                SubscriptionType.PRO,
                SubscriptionType.ULTRA,
                SubscriptionType.FREE
            ])
        )
        result = await session.execute(stmt)
        users_with_limits = result.all()
        
        now = datetime.now(timezone.utc)
        logger.info(f"Checking new period notifications for {len(users_with_limits)} users")
        
        for user, limits in users_with_limits:
            try:
                # Пропускаем пользователей без current_tariff_started_at
                if not limits.current_tariff_started_at:
                    continue
                
                # Пропускаем пользователей без доступных лимитов
                if limits.themes_remaining <= 0:
                    continue
                
                # Получаем кулдаун для пользователя
                cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
                tariff_start_time = limits.current_tariff_started_at
                
                # Приводим к timezone-aware
                if tariff_start_time.tzinfo is None:
                    tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
                
                # Вычисляем время с начала тарифа
                time_diff = now - tariff_start_time
                
                # Определяем текущий период (0, 1, 2, 3...)
                current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
                
                # Пропускаем период 0 (первые 7 дней)
                if current_period <= 0:
                    continue
                
                # Проверяем, не отправляли ли уже уведомление для этого периода
                if limits.last_period_notified == current_period:
                    continue
                
                # Вычисляем начало текущего периода
                current_period_start = tariff_start_time + timedelta(days=current_period * cooldown_days)
                time_in_current_period = now - current_period_start
                
                # Проверяем минимальную задержку (1 минута от начала периода, чтобы избежать гонок)
                if time_in_current_period < timedelta(minutes=1):
                    continue
                
                # Проверяем, что мы в начале нового периода (первые 15 минут)
                # Это гарантирует, что уведомление отправится только один раз
                if time_in_current_period > timedelta(minutes=15):
                    continue
                
                # Получаем текст уведомления из лексикона
                message_text = None
                try:
                    lexicon_service = LexiconService()
                    message_text = await lexicon_service.get_value_async(
                        'new_themes_period_notification',
                        'LEXICON_RU',
                        session
                    )
                except Exception as e:
                    logger.warning(f"Failed to get message from LexiconService: {e}")
                
                # Fallback to static lexicon
                if not message_text:
                    message_text = LEXICON_RU.get('new_themes_period_notification', "")
                
                if not message_text:
                    logger.warning("Message key 'new_themes_period_notification' not found in lexicon")
                    continue
                
                # Создаем клавиатуру с кнопкой "Назад в меню"
                keyboard = create_main_menu_button_keyboard(user.subscription_type)
                
                # Отправляем уведомление
                try:
                    await bot.send_message(
                        user.telegram_id,
                        message_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                    
                    # Обновляем last_period_notified после успешной отправки
                    limits.last_period_notified = current_period
                    session.add(limits)
                    await session.commit()
                    
                    sent += 1
                    
                    logger.info(
                        f"Sent new period notification to user {user.id} "
                        f"(telegram_id={user.telegram_id}, "
                        f"current_period={current_period}, "
                        f"period_start={current_period_start.strftime('%Y-%m-%d %H:%M:%S UTC')}, "
                        f"time_since_start={time_in_current_period.total_seconds() / 60:.1f} minutes)"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user.id}: {e}")
                    await session.rollback()
                    
            except Exception as e:
                logger.error(f"Error processing user {user.id} for new period notification: {e}")
                continue
        
        logger.info(f"Sent {sent} new period theme notifications")
        return sent
        
    except Exception as e:
        logger.error(f"Error in notify_new_period_themes: {e}")
        return 0


# УДАЛЕНО: Старая функция, не используется. Вместо неё используется notify_new_period_themes
# async def notify_weekly_themes(bot: Bot, session: AsyncSession) -> int:
#     """Send notifications to users who can request new themes after 7-day cooldown."""
#     sent = 0
#     try:
#         stmt = select(User)
#         result = await session.execute(stmt)
#         users = result.scalars().all()
#         now = datetime.now(timezone.utc)
#         
#         logger.info(f"Starting weekly themes notification check for {len(users)} users")
#         
#         for user in users:
#             try:
#                 # Get the most recent theme request
#                 stmt = select(ThemeRequest).filter(
#                     ThemeRequest.user_id == user.id
#                 ).order_by(desc(ThemeRequest.created_at)).limit(1)
#                 result = await session.execute(stmt)
#                 last_request = result.scalar_one_or_none()
#                 
#                 if not last_request:
#                     # User has never requested themes - skip notification
#                     continue
#                 
#                 # Ensure timezone-aware datetime
#                 if last_request.created_at.tzinfo is None:
#                     last_request_time = last_request.created_at.replace(tzinfo=timezone.utc)
#                 else:
#                     last_request_time = last_request.created_at
#                 
#                 # Calculate time difference
#                 time_diff = now - last_request_time
#                 
#                 # Check if exactly 7 days have passed (with 1-hour tolerance to avoid multiple notifications)
#                 if timedelta(days=7) <= time_diff < timedelta(days=7, hours=1):
#                     text = LEXICON_RU['new_themes_notification']
#                     
#                     try:
#                         await bot.send_message(user.telegram_id, text, parse_mode="HTML")
#                         sent += 1
#                         
#                         logger.info(
#                             f"Sending 7-day notification to user {user.id} "
#                             f"(last_request_date={last_request_time.strftime('%Y-%m-%d %H:%M:%S UTC')})"
#                         )
#                         
#                     except Exception as e:
#                         logger.error(f"Failed to send notification to user {user.id}: {e}")
#                         
#             except Exception as e:
#                 logger.error(f"Error processing user {user.id}: {e}")
#                 continue
#         
#         logger.info(f"Sent {sent} weekly themes notifications")
#         return sent
#         
#     except Exception as e:
#         logger.error(f"Error in notify_weekly_themes: {e}")
#         return 0


async def send_theme_limit_burn_reminders(bot: Bot, session: AsyncSession, days_before: int) -> int:
    """
    Отправляет уведомления пользователям о скором сгорании лимитов тем.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
        session: AsyncSession для работы с БД
        days_before: За сколько дней до сгорания отправлять уведомление (3 или 1)
    
    Returns:
        int: Количество отправленных уведомлений
    """
    sent = 0
    
    try:
        # Получаем всех пользователей с активными тарифами и лимитами
        stmt = select(User, Limits).join(Limits).where(
            User.subscription_type.in_([
                SubscriptionType.TEST_PRO,
                SubscriptionType.PRO,
                SubscriptionType.ULTRA,
                SubscriptionType.FREE
            ])
        )
        result = await session.execute(stmt)
        users_with_limits = result.all()
        
        now = datetime.now(timezone.utc)
        
        logger.info(f"Checking theme limit burn reminders for {len(users_with_limits)} users (days_before={days_before})")
        
        for user, limits in users_with_limits:
            try:
                # Проверяем, что у пользователя есть current_tariff_started_at
                if not limits.current_tariff_started_at:
                    continue
                
                # Получаем кулдаун для пользователя
                cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
                tariff_start_time = limits.current_tariff_started_at
                
                # Приводим к timezone-aware
                if tariff_start_time.tzinfo is None:
                    tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
                
                # Вычисляем, сколько дней прошло с начала тарифа
                time_diff = now - tariff_start_time
                days_passed = time_diff.days
                
                # Вычисляем, сколько дней осталось до сгорания лимита
                days_until_burn = cooldown_days - days_passed
                
                # Проверяем, нужно ли отправить уведомление
                if days_until_burn == days_before:
                    # Проверяем, был ли уже запрос тем за этот период
                    theme_request_query = select(ThemeRequest).where(
                        ThemeRequest.user_id == user.id,
                        ThemeRequest.status == "ISSUED",
                        ThemeRequest.created_at >= limits.current_tariff_started_at
                    ).order_by(desc(ThemeRequest.created_at)).limit(1)
                    
                    theme_request_result = await session.execute(theme_request_query)
                    last_request = theme_request_result.scalar_one_or_none()
                    
                    # Если уже был запрос тем - не отправляем уведомление
                    if last_request:
                        continue
                    
                    # Проверяем, что у пользователя еще есть лимиты
                    if limits.themes_total <= 0:
                        continue
                    
                    # Определяем ключ сообщения
                    if days_before == 3:
                        message_key = 'themes_limit_burn_reminder_3_days'
                    elif days_before == 1:
                        message_key = 'themes_limit_burn_reminder_1_day'
                    else:
                        continue
                    
                    # Получаем текст сообщения из лексикона (сначала из БД, потом fallback)
                    message_text = None
                    try:
                        lexicon_service = LexiconService()
                        message_text = await lexicon_service.get_value_async(
                            message_key, 
                            'LEXICON_RU', 
                            session
                        )
                    except Exception as e:
                        logger.warning(f"Failed to get message from LexiconService: {e}")
                    
                    # Fallback to static lexicon
                    if not message_text:
                        message_text = LEXICON_RU.get(message_key, "")
                    
                    if not message_text:
                        logger.warning(f"Message key {message_key} not found in lexicon")
                        continue
                    
                    # Создаем клавиатуру с кнопкой "Назад в меню"
                    keyboard = create_main_menu_button_keyboard(user.subscription_type)
                    
                    # Отправляем уведомление
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            message_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                        sent += 1
                        
                        logger.info(
                            f"Sent {days_before}-day reminder to user {user.id} "
                            f"(telegram_id={user.telegram_id}, "
                            f"tariff_started={tariff_start_time.strftime('%Y-%m-%d')}, "
                            f"days_passed={days_passed}, days_until_burn={days_until_burn})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send reminder to user {user.id}: {e}")
                        
            except Exception as e:
                logger.error(f"Error processing user {user.id} for reminders: {e}")
                continue
        
        logger.info(f"Sent {sent} theme limit burn reminders (days_before={days_before})")
        return sent
        
    except Exception as e:
        logger.error(f"Error in send_theme_limit_burn_reminders: {e}")
        return 0


