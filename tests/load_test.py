"""
Нагрузочное тестирование бота с 20 одновременными пользователями.

Запуск:
    poetry run python tests/load_test.py

Требования:
    - Тестовый бот должен быть запущен
    - Нужен BOT_TOKEN для теста
    - Тестовый CSV файл в tests/fixtures/
"""

import asyncio
import logging
import os
import time
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Конфигурация теста
TEST_BOT_TOKEN = os.getenv("TEST_BOT_TOKEN")  # Токен тестового бота
TEST_CHAT_IDS = [
    # Добавь сюда тестовые chat_id (свой Telegram ID)
    # Например: 123456789, 987654321
]
CONCURRENT_USERS = 20  # Количество одновременных пользователей
CSV_FILE_PATH = Path("tests/fixtures/test_report.csv")  # Тестовый CSV


async def simulate_user_upload(bot: Bot, chat_id: int, user_num: int):
    """Симуляция загрузки файла одним пользователем."""
    try:
        start_time = time.time()
        logger.info(f"👤 User {user_num}: Starting upload...")
        
        # 1. Отправка /start
        await bot.send_message(chat_id, "/start")
        await asyncio.sleep(1)
        
        # 2. Отправка команды /analytics
        await bot.send_message(chat_id, "/analytics")
        await asyncio.sleep(1)
        
        # 3. Загрузка CSV файла
        document = FSInputFile(CSV_FILE_PATH)
        await bot.send_document(chat_id, document)
        
        # 4. Ждем обработки (обычно 10-30 секунд)
        # В реальном тесте тут будет callback для проверки статуса
        await asyncio.sleep(35)  # Даем время на обработку
        
        elapsed = time.time() - start_time
        logger.info(f"✅ User {user_num}: Completed in {elapsed:.2f}s")
        
        return {"user": user_num, "status": "success", "time": elapsed}
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ User {user_num}: Failed after {elapsed:.2f}s - {e}")
        return {"user": user_num, "status": "failed", "time": elapsed, "error": str(e)}


async def run_load_test():
    """Запуск нагрузочного теста."""
    if not TEST_BOT_TOKEN:
        logger.error("❌ TEST_BOT_TOKEN not set!")
        return
    
    if not TEST_CHAT_IDS:
        logger.error("❌ TEST_CHAT_IDS is empty! Add your Telegram ID.")
        return
    
    if not CSV_FILE_PATH.exists():
        logger.error(f"❌ CSV file not found: {CSV_FILE_PATH}")
        logger.info("Создай тестовый CSV файл или используй пример из fixtures/")
        return
    
    bot = Bot(token=TEST_BOT_TOKEN)
    
    logger.info(f"🚀 Starting load test: {CONCURRENT_USERS} concurrent users")
    logger.info(f"📊 Using chat_ids: {TEST_CHAT_IDS}")
    logger.info(f"📁 CSV file: {CSV_FILE_PATH}")
    
    start_time = time.time()
    
    # Создаем задачи для всех пользователей
    tasks = []
    for i in range(CONCURRENT_USERS):
        # Распределяем пользователей по chat_id циклически
        chat_id = TEST_CHAT_IDS[i % len(TEST_CHAT_IDS)]
        task = simulate_user_upload(bot, chat_id, i + 1)
        tasks.append(task)
    
    # Запускаем все задачи одновременно
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # Анализ результатов
    success_count = sum(1 for r in results if isinstance(r, dict) and r["status"] == "success")
    failed_count = len(results) - success_count
    avg_time = sum(r["time"] for r in results if isinstance(r, dict)) / len(results)
    
    logger.info("=" * 60)
    logger.info("📊 LOAD TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total users: {CONCURRENT_USERS}")
    logger.info(f"Successful: {success_count} ({success_count/CONCURRENT_USERS*100:.1f}%)")
    logger.info(f"Failed: {failed_count} ({failed_count/CONCURRENT_USERS*100:.1f}%)")
    logger.info(f"Average time per user: {avg_time:.2f}s")
    logger.info(f"Total test duration: {total_time:.2f}s")
    logger.info("=" * 60)
    
    # Проверка критериев успеха
    if success_count >= CONCURRENT_USERS * 0.9:  # 90% success rate
        logger.info("✅ LOAD TEST PASSED! (90%+ success rate)")
    else:
        logger.warning("⚠️ LOAD TEST FAILED! Less than 90% success rate")
    
    await bot.session.close()


async def create_test_csv():
    """Создание тестового CSV файла для нагрузочного теста."""
    csv_dir = Path("tests/fixtures")
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = csv_dir / "test_report.csv"
    
    # Создаем CSV в формате Shutterstock (пример)
    csv_content = """8/1/2024,123456789,On Demand,Editorial,Large,50.00,Contributor Name,Editorial Project
8/2/2024,123456790,On Demand,Image,Medium,25.00,Contributor Name,Commercial Use
8/3/2024,123456791,Subscription,Video,HD,15.00,Contributor Name,Video Project
8/4/2024,123456792,On Demand,Image,Large,30.00,Contributor Name,Commercial Use
8/5/2024,123456793,On Demand,Editorial,Small,10.00,Contributor Name,Editorial Project
"""
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    logger.info(f"✅ Created test CSV: {csv_path}")


if __name__ == "__main__":
    # Раскомментируй, если нужно создать тестовый CSV
    # asyncio.run(create_test_csv())
    
    asyncio.run(run_load_test())
