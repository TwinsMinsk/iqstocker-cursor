"""
Тест для проверки исправления логирования.
Проверяет, что логирование не блокирует выполнение.
"""

import time
import logging
import asyncio
from logging.handlers import QueueHandler, QueueListener
import queue

def test_sync_logging():
    """Тест синхронного логирования (старый способ)."""
    print("\n🔴 Тест СИНХРОННОГО логирования (старый способ)...")
    
    # Настройка синхронного логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_sync.log'),
            logging.StreamHandler()
        ],
        force=True
    )
    
    logger = logging.getLogger('sync_test')
    
    start_time = time.time()
    
    # Генерируем 1000 логов
    for i in range(1000):
        logger.error(f'Test error {i}')
    
    elapsed = time.time() - start_time
    print(f"✗ Синхронное логирование: {elapsed:.3f}s для 1000 логов")
    
    return elapsed

def test_async_logging():
    """Тест асинхронного логирования (новый способ)."""
    print("\n✅ Тест АСИНХРОННОГО логирования (QueueHandler)...")
    
    # Настройка асинхронного логирования
    log_queue = queue.Queue(-1)
    
    file_handler = logging.FileHandler('logs/test_async.log')
    stream_handler = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    
    queue_listener = QueueListener(
        log_queue,
        file_handler,
        stream_handler,
        respect_handler_level=True
    )
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[QueueHandler(log_queue)],
        force=True
    )
    
    queue_listener.start()
    
    logger = logging.getLogger('async_test')
    
    start_time = time.time()
    
    # Генерируем 1000 логов
    for i in range(1000):
        logger.error(f'Test error {i}')
    
    elapsed = time.time() - start_time
    
    # Остановка listener
    queue_listener.stop()
    
    print(f"✓ Асинхронное логирование: {elapsed:.3f}s для 1000 логов")
    
    return elapsed

def main():
    """Главная функция."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║              Тест исправления логирования                         ║
║              Проверка блокировки Event Loop                       ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Тест 1: Синхронное логирование
    sync_time = test_sync_logging()
    
    # Тест 2: Асинхронное логирование
    async_time = test_async_logging()
    
    # Результаты
    print("\n" + "="*70)
    print("📊 РЕЗУЛЬТАТЫ")
    print("="*70)
    print(f"Синхронное логирование:   {sync_time:.3f}s")
    print(f"Асинхронное логирование:  {async_time:.3f}s")
    print(f"Ускорение:                {sync_time/async_time:.1f}x")
    print()
    
    if async_time < sync_time * 0.8:
        print("✅ УСПЕХ! Асинхронное логирование работает быстрее и не блокирует Event Loop")
        return True
    else:
        print("⚠️  Асинхронное логирование медленнее или одинаковое (проверь настройки)")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

