"""Admin panel application."""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from config.database import SessionLocal, engine
from database.models import (
    User, Subscription, Limits, CSVAnalysis, AnalyticsReport, 
    TopTheme, ThemeRequest, GlobalTheme, VideoLesson, 
    CalendarEntry, BroadcastMessage, SubscriptionType
)
from core.notifications.sender import NotificationSender

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# Initialize admin
admin = Admin(app, name='IQStocker Admin', template_mode='bootstrap3')


class UserAdmin(ModelView):
    """User admin view."""
    column_list = ['telegram_id', 'username', 'first_name', 'subscription_type', 'subscription_expires_at', 'created_at']
    column_searchable_list = ['telegram_id', 'username', 'first_name']
    column_filters = ['subscription_type', 'created_at']
    form_excluded_columns = ['created_at', 'updated_at']


class SubscriptionAdmin(ModelView):
    """Subscription admin view."""
    column_list = ['user', 'subscription_type', 'started_at', 'expires_at', 'amount', 'discount_percent']
    column_filters = ['subscription_type', 'started_at', 'expires_at']


class LimitsAdmin(ModelView):
    """Limits admin view."""
    column_list = ['user', 'analytics_total', 'analytics_used', 'themes_total', 'themes_used', 'top_themes_total', 'top_themes_used']


class CSVAnalysisAdmin(ModelView):
    """CSV Analysis admin view."""
    column_list = ['user', 'month', 'year', 'portfolio_size', 'status', 'processed_at']
    column_filters = ['status', 'month', 'year']


class VideoLessonAdmin(ModelView):
    """Video Lesson admin view."""
    column_list = ['title', 'description', 'url', 'order', 'is_pro_only', 'created_at']
    form_excluded_columns = ['created_at']


class CalendarEntryAdmin(ModelView):
    """Calendar Entry admin view."""
    column_list = ['month', 'year', 'created_at']
    form_excluded_columns = ['created_at']


class GlobalThemeAdmin(ModelView):
    """Global Theme admin view."""
    column_list = ['theme_name', 'total_sales', 'total_revenue', 'authors_count', 'last_updated']
    column_searchable_list = ['theme_name']


# Add views to admin
admin.add_view(UserAdmin(User, SessionLocal()))
admin.add_view(SubscriptionAdmin(Subscription, SessionLocal()))
admin.add_view(LimitsAdmin(Limits, SessionLocal()))
admin.add_view(CSVAnalysisAdmin(CSVAnalysis, SessionLocal()))
admin.add_view(ModelView(AnalyticsReport, SessionLocal()))
admin.add_view(ModelView(TopTheme, SessionLocal()))
admin.add_view(ModelView(ThemeRequest, SessionLocal()))
admin.add_view(GlobalThemeAdmin(GlobalTheme, SessionLocal()))
admin.add_view(VideoLessonAdmin(VideoLesson, SessionLocal()))
admin.add_view(CalendarEntryAdmin(CalendarEntry, SessionLocal()))
admin.add_view(ModelView(BroadcastMessage, SessionLocal()))


class BroadcastForm(FlaskForm):
    """Form for broadcast messages."""
    message = TextAreaField('Сообщение', validators=[DataRequired()])
    subscription_type = SelectField(
        'Тип подписки',
        choices=[
            ('', 'Все пользователи'),
            ('FREE', 'FREE'),
            ('TEST_PRO', 'TEST_PRO'),
            ('PRO', 'PRO'),
            ('ULTRA', 'ULTRA')
        ]
    )
    submit = SubmitField('Отправить')


class SettingsForm(FlaskForm):
    """Form for system settings."""
    new_works_months = IntegerField('Количество месяцев для "новых работ"', validators=[DataRequired(), NumberRange(min=1, max=12)])
    submit = SubmitField('Сохранить')


@app.route('/')
def index():
    """Admin dashboard."""
    db = SessionLocal()
    try:
        # Get statistics
        total_users = db.query(User).count()
        free_users = db.query(User).filter(User.subscription_type == SubscriptionType.FREE).count()
        test_pro_users = db.query(User).filter(User.subscription_type == SubscriptionType.TEST_PRO).count()
        pro_users = db.query(User).filter(User.subscription_type == SubscriptionType.PRO).count()
        ultra_users = db.query(User).filter(User.subscription_type == SubscriptionType.ULTRA).count()
        
        # Get recent activity
        recent_users = db.query(User).order_by(desc(User.created_at)).limit(10).all()
        recent_analytics = db.query(CSVAnalysis).order_by(desc(CSVAnalysis.created_at)).limit(10).all()
        
        return render_template('admin/index.html',
                             total_users=total_users,
                             free_users=free_users,
                             test_pro_users=test_pro_users,
                             pro_users=pro_users,
                             ultra_users=ultra_users,
                             recent_users=recent_users,
                             recent_analytics=recent_analytics)
    finally:
        db.close()


@app.route('/broadcast', methods=['GET', 'POST'])
def broadcast():
    """Broadcast message form."""
    form = BroadcastForm()
    
    if form.validate_on_submit():
        db = SessionLocal()
        try:
            # Save broadcast message
            broadcast_msg = BroadcastMessage(
                text=form.message.data,
                sent_at=func.now(),
                recipients_count=0  # Will be updated after sending
            )
            db.add(broadcast_msg)
            db.commit()
            
            # Send broadcast
            subscription_type = None
            if form.subscription_type.data:
                subscription_type = SubscriptionType(form.subscription_type.data)
            
            # TODO: Initialize bot instance for sending
            # sender = NotificationSender(bot_instance)
            # sent_count = await sender.send_broadcast(form.message.data, subscription_type)
            
            # Update recipients count
            broadcast_msg.recipients_count = 0  # Placeholder
            db.commit()
            
            flash('Сообщение отправлено!', 'success')
            return redirect(url_for('broadcast'))
            
        except Exception as e:
            flash(f'Ошибка при отправке: {str(e)}', 'error')
        finally:
            db.close()
    
    return render_template('admin/broadcast.html', form=form)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """System settings."""
    form = SettingsForm()
    
    if form.validate_on_submit():
        # TODO: Save settings to database or config
        flash('Настройки сохранены!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('admin/settings.html', form=form)


@app.route('/statistics')
def statistics():
    """Statistics page."""
    db = SessionLocal()
    try:
        # User statistics by subscription type
        user_stats = db.query(
            User.subscription_type,
            func.count(User.id).label('count')
        ).group_by(User.subscription_type).all()
        
        # Analytics statistics
        total_analytics = db.query(CSVAnalysis).count()
        completed_analytics = db.query(CSVAnalysis).filter(CSVAnalysis.status == 'COMPLETED').count()
        
        # Theme statistics
        total_themes = db.query(GlobalTheme).count()
        total_theme_requests = db.query(ThemeRequest).count()
        
        return render_template('admin/statistics.html',
                             user_stats=user_stats,
                             total_analytics=total_analytics,
                             completed_analytics=completed_analytics,
                             total_themes=total_themes,
                             total_theme_requests=total_theme_requests)
    finally:
        db.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)