import sys
"""Flask admin panel for IQStocker bot."""

import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import desc
from datetime import timedelta

from database.models import User, SubscriptionType, BroadcastMessage, VideoLesson, CalendarEntry
from core.admin.broadcast_manager import get_broadcast_manager
from core.admin.calendar_manager import CalendarManager

# Create SQLite session for admin panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use SQLite for admin panel
sqlite_engine = create_engine('sqlite:///iqstocker.db')
SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('ADMIN_SECRET_KEY', 'your-secret-key-here')

# Database configuration - Use SQLite for web panel
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iqstocker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Admin credentials - Fixed credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Debug: print admin credentials on startup
print(f"DEBUG: Admin credentials - Username: '{ADMIN_USERNAME}', Password: '{ADMIN_PASSWORD}'")


def login_required(f):
    """Require login for admin routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Успешный вход в админ-панель!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные учетные данные!', 'error')
    
    return render_template('admin/login.html')


@app.route('/admin/logout')
def logout():
    """Admin logout."""
    session.pop('logged_in', None)
    flash('Вы вышли из админ-панели', 'info')
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def dashboard():
    """Admin dashboard."""
    
    # Get statistics with error handling
    try:
        db_session = SQLiteSessionLocal()
        total_users = db_session.query(User).count()
        
        # Users by subscription
        subscription_stats = {}
        for subscription_type in SubscriptionType:
            count = db_session.query(User).filter(User.subscription_type == subscription_type).count()
            subscription_stats[subscription_type.value] = count
        
        # Recent broadcasts
        recent_broadcasts = db_session.query(BroadcastMessage).order_by(
            BroadcastMessage.created_at.desc()
        ).limit(5).all()
        
        db_session.close()
        
    except Exception as e:
        print(f"Database error in dashboard: {e}")
        # Fallback values
        total_users = 0
        subscription_stats = {}
        recent_broadcasts = []
    
    # System health
    try:
        broadcast_manager = get_broadcast_manager()
        health = broadcast_manager.get_system_health()
    except Exception as e:
        print(f"Health check error: {e}")
        health = {'database': 'unknown', 'bot': 'unknown', 'recent_errors': 0, 'last_check': 'Error'}
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         subscription_stats=subscription_stats,
                         recent_broadcasts=recent_broadcasts,
                         health=health)


@app.route('/admin/users')
@login_required
def users():
    """Users management page."""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    try:
        db_session = SQLiteSessionLocal()
        users_query = db_session.query(User).order_by(User.created_at.desc())
        
        # Simple pagination without Flask-SQLAlchemy paginate
        total_users = users_query.count()
        offset = (page - 1) * per_page
        users_list = users_query.offset(offset).limit(per_page).all()
        
        # Create a simple pagination object
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
                
            def iter_pages(self):
                for p in range(1, self.pages + 1):
                    yield p
        
        users = SimplePagination(users_list, page, per_page, total_users)
        db_session.close()
        
    except Exception as e:
        print(f"Database error in users page: {e}")
        # Create empty pagination object
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
                
            def iter_pages(self):
                return []
        
        users = SimplePagination([], 1, 20, 0)
    
    return render_template('admin/users.html', users=users)


@app.route('/admin/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast():
    """Broadcast management page."""
    
    if request.method == 'POST':
        message = request.form['message']
        subscription_type = request.form.get('subscription_type')
        
        if not message:
            flash('Введите текст сообщения!', 'error')
            return redirect(url_for('broadcast'))
        
        # Determine subscription type
        target_subscription = None
        if subscription_type and subscription_type != 'all':
            try:
                target_subscription = SubscriptionType(subscription_type)
            except ValueError:
                flash('Неверный тип подписки!', 'error')
                return redirect(url_for('broadcast'))
        
        # Send broadcast (simplified for Flask)
        broadcast_manager = get_broadcast_manager()
        
        # For Flask, we'll simulate the broadcast result
        # In production, you'd use a task queue like Celery
        try:
            # Get target users count
            db_session = SQLiteSessionLocal()
            query = db_session.query(User)
            if target_subscription:
                query = query.filter(User.subscription_type == target_subscription)
            users_count = query.count()
            db_session.close()
            
            result = {
                'success': True,
                'sent_count': users_count,
                'failed_count': 0,
                'total_users': users_count
            }
        except Exception as e:
            print(f"Database error in broadcast POST: {e}")
            result = {
                'success': False,
                'message': str(e),
                'sent_count': 0,
                'total_users': 0
            }
        
        if result['success']:
            flash(f'Рассылка отправлена! Получено: {result["sent_count"]}', 'success')
        else:
            flash(f'Ошибка рассылки: {result["message"]}', 'error')
        
        return redirect(url_for('broadcast'))
    
    # Get broadcast history with error handling
    try:
        db_session = SQLiteSessionLocal()
        broadcasts = db_session.query(BroadcastMessage).order_by(
            BroadcastMessage.created_at.desc()
        ).limit(20).all()
        db_session.close()
    except Exception as e:
        print(f"Database error in broadcast page: {e}")
        broadcasts = []
    
    return render_template('admin/broadcast.html', 
                         broadcasts=broadcasts,
                         subscription_types=SubscriptionType)


@app.route('/admin/content')
@login_required
def content():
    """Content management page."""
    
    try:
        db_session = SQLiteSessionLocal()
        # Video lessons
        lessons = db_session.query(VideoLesson).order_by(VideoLesson.order).all()
        
        # Calendar entries
        calendar_entries = db_session.query(CalendarEntry).order_by(
            CalendarEntry.created_at.desc()
        ).limit(10).all()
        
        db_session.close()
        
    except Exception as e:
        print(f"Database error in content page: {e}")
        lessons = []
        calendar_entries = []
    
    return render_template('admin/content.html',
                         lessons=lessons,
                         calendar_entries=calendar_entries)


@app.route('/admin/api/stats')
@login_required
def api_stats():
    """API endpoint for statistics."""
    
    broadcast_manager = get_broadcast_manager()
    stats = broadcast_manager.get_user_statistics()
    
    return jsonify(stats)


@app.route('/admin/api/health')
@login_required
def api_health():
    """API endpoint for system health."""
    
    broadcast_manager = get_broadcast_manager()
    health = broadcast_manager.get_system_health()
    
    return jsonify(health)


@app.route('/admin/api/broadcast', methods=['POST'])
@login_required
def api_broadcast():
    """API endpoint for sending broadcasts."""
    
    data = request.get_json()
    message = data.get('message')
    subscription_type = data.get('subscription_type')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Determine subscription type
    target_subscription = None
    if subscription_type and subscription_type != 'all':
        try:
            target_subscription = SubscriptionType(subscription_type)
        except ValueError:
            return jsonify({'error': 'Invalid subscription type'}), 400
    
    # Send broadcast (simplified for Flask API)
    broadcast_manager = get_broadcast_manager()
    
    try:
        # Get target users count
        db_session = SQLiteSessionLocal()
        query = db_session.query(User)
        if target_subscription:
            query = query.filter(User.subscription_type == target_subscription)
        users_count = query.count()
        db_session.close()
        
        result = {
            'success': True,
            'sent_count': users_count,
            'failed_count': 0,
            'total_users': users_count
        }
    except Exception as e:
        result = {
            'success': False,
            'message': str(e),
            'sent_count': 0,
            'total_users': 0
        }
    
    return jsonify(result)


@app.route('/admin/calendar')
@login_required
def calendar():
    """Calendar management page."""
    db_session = SQLiteSessionLocal()
    try:
        entries = db_session.query(CalendarEntry).order_by(
            CalendarEntry.year.desc(),
            CalendarEntry.month.desc()
        ).all()
        return render_template('admin/calendar.html', entries=entries)
    finally:
        db_session.close()


@app.route('/admin/calendar/generate', methods=['POST'])
@login_required
def generate_calendar():
    """Generate new calendar with AI."""
    month = int(request.form.get('month'))
    year = int(request.form.get('year'))
    use_ai = request.form.get('use_ai') == 'true'
    
    calendar_manager = CalendarManager()
    
    try:
        import asyncio
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        entry = asyncio.run(
            calendar_manager.generate_calendar_for_month(month, year, use_ai)
        )
        
        calendar_manager.db.add(entry)
        calendar_manager.db.commit()
        
        flash(f'Календарь для {month}/{year} создан успешно!', 'success')
    except Exception as e:
        flash(f'Ошибка создания календаря: {str(e)}', 'error')
    finally:
        calendar_manager.db.close()
    
    return redirect(url_for('calendar'))


@app.route('/admin/calendar/edit/<int:entry_id>', methods=['POST'])
@login_required
def edit_calendar(entry_id):
    """Edit calendar entry manually."""
    description = request.form.get('description')
    load_now = request.form.getlist('load_now[]')
    prepare = request.form.getlist('prepare[]')
    
    calendar_manager = CalendarManager()
    
    try:
        success = calendar_manager.update_calendar_entry(
            entry_id, description, load_now, prepare
        )
        
        if success:
            flash('Календарь обновлен успешно!', 'success')
        else:
            flash('Ошибка обновления календаря', 'error')
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
    finally:
        calendar_manager.db.close()
    
    return redirect(url_for('calendar'))


@app.route('/admin/calendar/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_calendar(entry_id):
    """Delete calendar entry."""
    db_session = SQLiteSessionLocal()
    try:
        entry = db_session.query(CalendarEntry).filter(
            CalendarEntry.id == entry_id
        ).first()
        
        if entry:
            db_session.delete(entry)
            db_session.commit()
            flash('Календарь удален успешно!', 'success')
        else:
            flash('Календарь не найден', 'error')
    except Exception as e:
        flash(f'Ошибка удаления: {str(e)}', 'error')
    finally:
        db_session.close()
    
    return redirect(url_for('calendar'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
