"""
Healthcheck для Dramatiq воркера.
Этот модуль предоставляет HTTP endpoint для проверки состояния воркера.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import dramatiq
from flask import Flask, jsonify

logger = logging.getLogger(__name__)

# Глобальные переменные для отслеживания состояния
_last_heartbeat = time.time()
_worker_start_time = time.time()
_tasks_processed = 0
_last_task_time = None


def update_heartbeat():
    """Обновляет время последнего heartbeat."""
    global _last_heartbeat, _tasks_processed, _last_task_time
    _last_heartbeat = time.time()
    _tasks_processed += 1
    _last_task_time = time.time()


def get_worker_status() -> Dict[str, Any]:
    """
    Возвращает текущий статус воркера.
    
    Returns:
        Dict с информацией о состоянии воркера
    """
    current_time = time.time()
    uptime = current_time - _worker_start_time
    time_since_heartbeat = current_time - _last_heartbeat
    
    # Считаем воркер здоровым, если heartbeat обновлялся в последние 5 минут
    is_healthy = time_since_heartbeat < 300
    
    status = {
        "status": "healthy" if is_healthy else "unhealthy",
        "uptime_seconds": uptime,
        "uptime_human": str(timedelta(seconds=int(uptime))),
        "last_heartbeat_seconds_ago": time_since_heartbeat,
        "tasks_processed": _tasks_processed,
        "last_task_time": datetime.fromtimestamp(_last_task_time).isoformat() if _last_task_time else None,
        "worker_start_time": datetime.fromtimestamp(_worker_start_time).isoformat(),
        "pid": os.getpid()
    }
    
    # Проверяем наличие брокера
    try:
        broker = dramatiq.get_broker()
        status["broker_type"] = type(broker).__name__
        status["broker_connected"] = True
    except Exception as e:
        status["broker_connected"] = False
        status["broker_error"] = str(e)
    
    return status


# Flask приложение для healthcheck endpoint
app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Healthcheck endpoint."""
    status = get_worker_status()
    
    # Возвращаем 200 если healthy, 503 если unhealthy
    status_code = 200 if status["status"] == "healthy" else 503
    
    return jsonify(status), status_code


@app.route('/ready', methods=['GET'])
def ready():
    """Readiness probe endpoint."""
    status = get_worker_status()
    
    # Воркер готов, если брокер подключен и прошло меньше 5 минут с последнего heartbeat
    is_ready = status.get("broker_connected", False) and status["status"] == "healthy"
    
    status_code = 200 if is_ready else 503
    
    return jsonify({
        "ready": is_ready,
        "broker_connected": status.get("broker_connected", False),
        "worker_status": status["status"]
    }), status_code


@app.route('/metrics', methods=['GET'])
def metrics():
    """Metrics endpoint в формате Prometheus."""
    status = get_worker_status()
    
    metrics_text = f"""# HELP dramatiq_worker_uptime_seconds Worker uptime in seconds
# TYPE dramatiq_worker_uptime_seconds counter
dramatiq_worker_uptime_seconds {status['uptime_seconds']}

# HELP dramatiq_worker_tasks_processed_total Total number of tasks processed
# TYPE dramatiq_worker_tasks_processed_total counter
dramatiq_worker_tasks_processed_total {status['tasks_processed']}

# HELP dramatiq_worker_last_heartbeat_seconds Time since last heartbeat in seconds
# TYPE dramatiq_worker_last_heartbeat_seconds gauge
dramatiq_worker_last_heartbeat_seconds {status['last_heartbeat_seconds_ago']}

# HELP dramatiq_worker_healthy Worker health status (1 = healthy, 0 = unhealthy)
# TYPE dramatiq_worker_healthy gauge
dramatiq_worker_healthy {1 if status['status'] == 'healthy' else 0}

# HELP dramatiq_worker_broker_connected Broker connection status (1 = connected, 0 = disconnected)
# TYPE dramatiq_worker_broker_connected gauge
dramatiq_worker_broker_connected {1 if status.get('broker_connected', False) else 0}
"""
    
    return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}


def start_healthcheck_server(port: int = 8080, host: str = '0.0.0.0'):
    """
    Запускает healthcheck HTTP сервер.
    
    Args:
        port: Порт для HTTP сервера
        host: Хост для прослушивания
    """
    logger.info(f"Starting healthcheck server on {host}:{port}")
    app.run(host=host, port=port, debug=False)


# Middleware для обновления heartbeat при обработке задач
class HeartbeatMiddleware(dramatiq.Middleware):
    """Middleware для обновления heartbeat при обработке задач."""
    
    def after_process_message(self, broker, message, *, result=None, exception=None):
        """Вызывается после обработки сообщения."""
        update_heartbeat()
        
        if exception:
            logger.warning(f"Task {message.message_id} failed with exception: {exception}")
        else:
            logger.debug(f"Task {message.message_id} completed successfully")


if __name__ == "__main__":
    # Для тестирования
    start_healthcheck_server(port=8080)

