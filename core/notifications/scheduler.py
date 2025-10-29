"""Task scheduler for automated notifications and maintenance."""

import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.notifications.notification_manager import get_notification_manager
from core.notifications.themes_notifications import notify_weekly_themes
from core.admin.calendar_manager import CalendarManager
from database.models import CalendarEntry
from config.database import AsyncSessionLocal
from config.settings import settings


class TaskScheduler:
    """Task scheduler for automated bot maintenance."""
    
    def __init__(self, bot=None):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.notification_manager = get_notification_manager(bot)
    
    def start(self):
        """Start the scheduler."""
        
        # Daily check for expired TEST_PRO subscriptions (at 00:00 UTC)
        self.scheduler.add_job(
            self.check_expired_subscriptions,
            CronTrigger(hour=0, minute=0),
            id='check_expired_subscriptions',
            name='Check expired TEST_PRO subscriptions'
        )
        
        # Weekly themes notifications (every Monday at 09:00 UTC)
        self.scheduler.add_job(
            self.send_weekly_themes_notifications,
            CronTrigger(day_of_week=0, hour=9, minute=0),
            id='weekly_themes_notifications',
            name='Send weekly themes notifications'
        )
        
        # Monthly marketing notifications (1st day of month at 10:00 UTC)
        self.scheduler.add_job(
            self.send_marketing_notifications,
            CronTrigger(day=1, hour=10, minute=0),
            id='monthly_marketing_notifications',
            name='Send monthly marketing notifications'
        )
        
        # Monthly calendar update notifications (1st day of month at 11:00 UTC)
        self.scheduler.add_job(
            self.send_calendar_update_notifications,
            CronTrigger(day=1, hour=11, minute=0),
            id='monthly_calendar_notifications',
            name='Send monthly calendar update notifications'
        )
        
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
    
    async def send_weekly_themes_notifications(self):
        """Send weekly themes notifications."""
        print("Sending weekly themes notifications...")
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await self.notification_manager.send_weekly_themes_notifications(session)
                print(f"Sent {sent_count} weekly themes notifications")
            except Exception as e:
                print(f"Error sending weekly themes notifications: {e}")
    
    async def send_marketing_notifications(self):
        """Send monthly marketing notifications."""
        print("Sending monthly marketing notifications...")
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await self.notification_manager.send_marketing_notifications(session)
                print(f"Sent {sent_count} marketing notifications")
            except Exception as e:
                print(f"Error sending marketing notifications: {e}")
    
    async def send_calendar_update_notifications(self):
        """Send calendar update notifications."""
        print("Sending calendar update notifications...")
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await self.notification_manager.send_calendar_update_notifications(session)
                print(f"Sent {sent_count} calendar update notifications")
            except Exception as e:
                print(f"Error sending calendar update notifications: {e}")
    
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
        """Send daily reminder about weekly themes availability."""
        print("Sending daily weekly themes availability notifications...")
        async with AsyncSessionLocal() as session:
            try:
                sent_count = await notify_weekly_themes(self.bot, session)
                print(f"Sent {sent_count} weekly themes availability notifications")
            except Exception as e:
                print(f"Error sending daily weekly themes notifications: {e}")
    
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