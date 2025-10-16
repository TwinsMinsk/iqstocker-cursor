web: python bot/main.py
worker: celery -A core.notifications.scheduler worker --loglevel=info
beat: celery -A core.notifications.scheduler beat --loglevel=info
admin: python api/admin_panel.py