"""Task scheduler for automated notifications and maintenance."""

import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.notifications.notification_manager import get_notification_manager
from core.notifications.themes_notifications import notify_new_period_themes, send_theme_limit_burn_reminders
# notify_weekly_themes - удалено, функция не используется
from core.admin.calendar_manager import CalendarManager
from core.theme_settings import check_and_burn_unused_theme_limits
from core.monitoring.resource_monitor import ResourceMonitor
from database.models import CalendarEntry, User, Limits, SubscriptionType
from sqlalchemy import select
from config.database import AsyncSessionLocal
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Task scheduler for automated bot maintenance."""
    
    def __init__(self, bot=None):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.notification_manager = get_notification_manager(bot)
        self.resource_monitor = ResourceMonitor()
    
    def start(self):
        """Start the scheduler."""
        
        # Daily check for expired TEST_PRO subscriptions (at 00:00 UTC)
        self.scheduler.add_job(
            self.check_expired_subscriptions,
            CronTrigger(hour=0, minute=0),
            id='check_expired_subscriptions',
            name='Check expired TEST_PRO subscriptions'
        )
        
        # Weekly themes notifications (every Monday at 09:00 UTC) - УДАЛЕНО, функция не используется
        # self.scheduler.add_job(
        #     self.send_weekly_themes_notifications,
        #     CronTrigger(day_of_week=0, hour=9, minute=0),
        #     id='weekly_themes_notifications',
        #     name='Send weekly themes notifications'
        # )
        
        # УДАЛЕНО: Monthly marketing notifications - функция отключена
        # self.scheduler.add_job(
        #     self.send_marketing_notifications,
        #     CronTrigger(day=1, hour=10, minute=0),
        #     id='monthly_marketing_notifications',
        #     name='Send monthly marketing notifications'
        # )
        
        # Daily TEST_PRO expiration notifications (at 12:00 UTC)
        self.scheduler.add_job(
            self.send_test_pro_expiring_notifications,
            CronTrigger(hour=12, minute=0),
            id='test_pro_expiring_notifications',
            name='Send TEST_PRO expiration notifications'
        )

        # Daily reminder for weekly themes availability (at 12:00 UTC)
        self.scheduler.add_job(
            self.send_daily_weekly_themes_notify,
            CronTrigger(hour=12, minute=0),
            id='daily_weekly_themes_notify',
            name='Send daily weekly-themes availability notifications'
        )
        
        # Monthly calendar generation (25th day of month at 12:00 UTC)
        self.scheduler.add_job(
            self.create_monthly_calendar,
            CronTrigger(day=25, hour=12, minute=0),
            id='create_monthly_calendar',
            name='Create next month calendar'
        )
        
        # Daily burn unused theme limits (at 01:00 UTC)
        self.scheduler.add_job(
            self.burn_unused_theme_limits,
            CronTrigger(hour=1, minute=0),
            id='burn_unused_theme_limits',
            name='Burn unused theme limits daily'
        )
        
        # Daily theme limit burn reminders - 3 days before (at 10:00 UTC)
        self.scheduler.add_job(
            self.send_theme_limit_burn_reminders_3_days,
            CronTrigger(hour=10, minute=0),
            id='theme_limit_burn_reminder_3_days',
            name='Send 3-day theme limit burn reminders'
        )
        
        # Daily theme limit burn reminders - 1 day before (at 11:00 UTC)
        self.scheduler.add_job(
            self.send_theme_limit_burn_reminders_1_day,
            CronTrigger(hour=11, minute=0),
            id='theme_limit_burn_reminder_1_day',
            name='Send 1-day theme limit burn reminders'
        )
        
        # Мониторинг ресурсов каждые 5 минут
        self.scheduler.add_job(
            self.monitor_resources,
            IntervalTrigger(minutes=5),
            id='resource_monitoring',
            name='Resource monitoring'
        )
        
        # Daily VIP group access check (at 03:00 UTC)
        self.scheduler.add_job(
            self.check_vip_group_access,
            CronTrigger(hour=3, minute=0),
            id='vip_group_access_check',
            name='Check VIP group members access'
        )
        
        # Start the scheduler
        self.scheduler.start()
        print("Task scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        print("Task scheduler stopped")
    
    async def check_expired_subscriptions(self):
        """Check and convert expired TEST_PRO subscriptions."""
        print("Checking expired TEST_PRO subscriptions...")
        async with AsyncSessionLocal() as session:
            try:
                converted_count = await self.notification_manager.check_and_convert_expired_test_pro(session)
                print(f"Converted {converted_count} expired subscriptions")
            except Exception as e:
                print(f"Error checking expired subscriptions: {e}")
    
    # УДАЛЕНО: Старая функция, не используется
    # async def send_weekly_themes_notifications(self):
    #     """Send weekly themes notifications."""
    #     print("Sending weekly themes notifications...")
    #     async with AsyncSessionLocal() as session:
    #         try:
    #             sent_count = await self.notification_manager.send_weekly_themes_notifications(session)
    #             print(f"Sent {sent_count} weekly themes notifications")
    #         except Exception as e:
    #             print(f"Error sending weekly themes notifications: {e}")
    
    # УДАЛЕНО: Функция отправки маркетинговых уведомлений отключена
    # async def send_marketing_notifications(self):
    #     """Send monthly marketing notifications."""
    #     print("Sending monthly marketing notifications...")
    #     async with AsyncSessionLocal() as session:
    #         try:
    #             sent_count = await self.notification_manager.send_marketing_notifications(session)
    #             print(f"Sent {sent_count} marketing notifications")
    #         except Exception as e:
    #             print(f"Error sending marketing notifications: {e}")
    
    async def send_test_pro_expiring_notifications(self):
        """Send TEST_PRO expiration notifications."""
        print("Sending TEST_PRO expiration notifications...")
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await self.notification_manager.send_test_pro_expiring_notifications(session)
                print(f"Sent {sent_count} TEST_PRO expiration notifications")
            except Exception as e:
                print(f"Error sending TEST_PRO expiration notifications: {e}")
    
    async def send_daily_weekly_themes_notify(self):
        """Send daily reminder about new themes period availability."""
        print("Sending daily new themes period notifications...")
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await notify_new_period_themes(self.bot, session)
                print(f"Sent {sent_count} new themes period notifications")
            except Exception as e:
                print(f"Error sending daily new themes period notifications: {e}")
    
    async def create_monthly_calendar(self):
        """Create calendar for next month automatically."""
        print("Creating monthly calendar...")
        
        # Calculate next month
        now = datetime.now(timezone.utc)
        next_month = now.month % 12 + 1
        next_year = now.year + (1 if next_month == 1 else 0)
        
        calendar_manager = CalendarManager()
        
        try:
            # Check if calendar already exists
            existing = calendar_manager.get_calendar_entry(next_month, next_year)
            
            if not existing:
                # Generate calendar with AI (fallback to template if AI fails)
                entry = await calendar_manager.generate_calendar_for_month(
                    next_month, next_year, use_ai=True
                )
                
                calendar_manager.db.add(entry)
                calendar_manager.db.commit()
                
                print(f"Created calendar for {next_month}/{next_year} (source: {entry.source})")
            else:
                print(f"Calendar for {next_month}/{next_year} already exists")
                
        except Exception as e:
            print(f"Error creating monthly calendar: {e}")
        finally:
            calendar_manager.db.close()
    
    def add_custom_job(self, func, trigger, job_id: str, name: str = None):
        """Add a custom job to the scheduler."""
        self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            name=name or job_id
        )
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            print(f"Removed job: {job_id}")
        except Exception as e:
            print(f"Error removing job {job_id}: {e}")
    
    async def burn_unused_theme_limits(self):
        """Burn unused theme limits for users who didn't request themes within 7 days."""
        print("Burning unused theme limits...")
        async with AsyncSessionLocal() as session:
            try:
                # Get all users with active subscriptions
                stmt = select(User, Limits).join(Limits).where(
                    User.subscription_type.in_([
                        SubscriptionType.TEST_PRO,
                        SubscriptionType.PRO,
                        SubscriptionType.ULTRA,
                        SubscriptionType.FREE
                    ])
                )
                result = await session.execute(stmt)
                
                burned_count = 0
                users_with_burned_limits = []
                for user, limits in result.all():
                    if await check_and_burn_unused_theme_limits(session, user, limits):
                        burned_count += 1
                        users_with_burned_limits.append((user, limits))
                
                await session.commit()
                
                # Invalidate cache for users whose limits were updated
                if users_with_burned_limits:
                    from core.cache.user_cache import get_user_cache_service
                    cache_service = get_user_cache_service()
                    for user, limits in users_with_burned_limits:
                        await cache_service.invalidate_limits(user.id)
                
                logger.info(f"Burned unused theme limits for {burned_count} users")
                print(f"Burned unused theme limits for {burned_count} users")
                
            except Exception as e:
                logger.error(f"Error burning unused theme limits: {e}")
                print(f"Error burning unused theme limits: {e}")
                await session.rollback()
    
    async def send_theme_limit_burn_reminders_3_days(self):
        """Send reminders 3 days before theme limit burn."""
        print("Sending 3-day theme limit burn reminders...")
        if not self.bot:
            print("Bot not available for sending reminders")
            return
        
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await send_theme_limit_burn_reminders(self.bot, session, days_before=3)
                print(f"Sent {sent_count} 3-day theme limit burn reminders")
            except Exception as e:
                logger.error(f"Error sending 3-day reminders: {e}")
                print(f"Error sending 3-day reminders: {e}")
    
    async def send_theme_limit_burn_reminders_1_day(self):
        """Send reminders 1 day before theme limit burn."""
        print("Sending 1-day theme limit burn reminders...")
        if not self.bot:
            print("Bot not available for sending reminders")
            return
        
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await send_theme_limit_burn_reminders(self.bot, session, days_before=1)
                print(f"Sent {sent_count} 1-day theme limit burn reminders")
            except Exception as e:
                logger.error(f"Error sending 1-day reminders: {e}")
                print(f"Error sending 1-day reminders: {e}")
    
    async def check_vip_group_access(self):
        """Check VIP group members access and remove those without access."""
        print("Checking VIP group members access...")
        if not self.bot:
            print("Bot not available for VIP group check")
            return
        
        from core.notifications.vip_group_checker import check_vip_group_members
        
        async with AsyncSessionLocal() as session:
            try:
                stats = await check_vip_group_members(self.bot, session)
                print(
                    f"VIP group check completed: checked={stats['checked']}, "
                    f"in_group={stats['in_group']}, removed={stats['removed']}, "
                    f"errors={stats['errors']}"
                )
            except Exception as e:
                logger.error(f"Error checking VIP group access: {e}")
                print(f"Error checking VIP group access: {e}")
    
    async def monitor_resources(self):
        """Мониторинг использования ресурсов."""
        try:
            self.resource_monitor.log_current_usage()
        except Exception as e:
            logger.error(f"Error monitoring resources: {e}")
    
    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        print("Scheduled jobs:")
        for job in jobs:
            print(f"  - {job.id}: {job.name} (next run: {job.next_run_time})")


# Global scheduler instance
scheduler = None

def get_scheduler(bot=None) -> TaskScheduler:
    """Get global scheduler instance."""
    global scheduler
    if scheduler is None:
        scheduler = TaskScheduler(bot)
    return scheduler