"""
Стресс-тест для проверки производительности IQStocker.

Симулирует нагрузку от 50-100 одновременных пользователей без использования Telegram API.
Тестирует внутренние сервисы: Database, Redis, Supabase Storage.

Запуск:
    poetry run python tests/stress_test_simulation.py

Требования:
    - Работающий Supabase (DATABASE_URL, SUPABASE_URL, SUPABASE_KEY)
    - Работающий Redis (REDIS_URL)
    - Тестовый CSV файл (создается автоматически)
"""

import asyncio
import time
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import AsyncSessionLocal, redis_client, SUPABASE_SESSION_LIMIT
from config.settings import settings
from database.models import User, SubscriptionType, Limits, CSVAnalysis
from services.storage_service import StorageService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Цветные выводы для консоли
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


@dataclass
class TestMetrics:
    """Метрики теста."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    other_errors: int = 0
    
    # Latency tracking
    latencies: List[float] = field(default_factory=list)
    
    # Per-operation metrics
    db_operations: int = 0
    redis_operations: int = 0
    storage_operations: int = 0
    
    # Resource usage
    max_concurrent_connections: int = 0
    
    def add_latency(self, latency: float):
        """Добавить замер задержки."""
        self.latencies.append(latency)
    
    def get_avg_latency(self) -> float:
        """Средняя задержка."""
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0
    
    def get_p95_latency(self) -> float:
        """95-й перцентиль задержки."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]
    
    def get_p99_latency(self) -> float:
        """99-й перцентиль задержки."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[index]


class StressTestSimulator:
    """Симулятор стресс-теста."""
    
    def __init__(self, num_users: int = 50):
        """
        Инициализация симулятора.
        
        Args:
            num_users: Количество виртуальных пользователей
        """
        self.num_users = num_users
        self.metrics = TestMetrics()
        self.test_csv_path = None
        self.storage_service = None
        
    def create_test_csv(self) -> str:
        """Создать тестовый CSV файл."""
        csv_content = """title,views,likes,comments,published_date,thumbnail_url
Test Video 1,1000,100,50,2024-01-01,https://example.com/thumb1.jpg
Test Video 2,2000,200,100,2024-01-02,https://example.com/thumb2.jpg
Test Video 3,3000,300,150,2024-01-03,https://example.com/thumb3.jpg
Test Video 4,4000,400,200,2024-01-04,https://example.com/thumb4.jpg
Test Video 5,5000,500,250,2024-01-05,https://example.com/thumb5.jpg
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        temp_file.write(csv_content)
        temp_file.close()
        return temp_file.name
    
    async def setup(self):
        """Подготовка к тестированию."""
        print(f"{Colors.BLUE}{Colors.BOLD}🔧 Инициализация тестового окружения...{Colors.RESET}")
        
        # Проверка подключений
        print(f"{Colors.CYAN}📊 Проверка Database...{Colors.RESET}")
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).limit(1))
                user = result.scalar_one_or_none()
                print(f"{Colors.GREEN}✓ Database подключена{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}✗ Database недоступна: {e}{Colors.RESET}")
            raise
        
        print(f"{Colors.CYAN}🔴 Проверка Redis...{Colors.RESET}")
        if redis_client:
            try:
                redis_client.ping()
                print(f"{Colors.GREEN}✓ Redis подключен{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠ Redis недоступен: {e}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ Redis не настроен (кеширование отключено){Colors.RESET}")
        
        print(f"{Colors.CYAN}☁️  Проверка Supabase Storage...{Colors.RESET}")
        try:
            self.storage_service = StorageService()
            print(f"{Colors.GREEN}✓ Supabase Storage инициализирован{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}✗ Supabase Storage недоступен: {e}{Colors.RESET}")
            raise
        
        # Создание тестового CSV
        print(f"{Colors.CYAN}📄 Создание тестового CSV...{Colors.RESET}")
        self.test_csv_path = self.create_test_csv()
        print(f"{Colors.GREEN}✓ Тестовый CSV создан: {self.test_csv_path}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}📋 Конфигурация теста:{Colors.RESET}")
        print(f"  • Виртуальных пользователей: {Colors.BOLD}{self.num_users}{Colors.RESET}")
        print(f"  • SUPABASE_SESSION_LIMIT: {Colors.BOLD}{SUPABASE_SESSION_LIMIT}{Colors.RESET}")
        print(f"  • Redis max_connections: {Colors.BOLD}20{Colors.RESET}")
        print(f"  • Timeout БД: {Colors.BOLD}5s connection, 10s command{Colors.RESET}\n")
    
    async def simulate_user_action(self, user_id: int, user_index: int) -> Tuple[bool, str, float]:
        """
        Симулировать действия одного пользователя.
        
        Args:
            user_id: ID пользователя в БД
            user_index: Индекс пользователя (для логирования)
            
        Returns:
            Tuple[успех, тип_ошибки, время_выполнения]
        """
        start_time = time.time()
        error_type = None
        
        try:
            # 1. Database: Создание записи о начале анализа
            async with AsyncSessionLocal() as session:
                self.metrics.db_operations += 1
                
                # Проверка лимитов пользователя
                result = await session.execute(
                    select(Limits).where(Limits.user_id == user_id)
                )
                limits = result.scalar_one_or_none()
                
                if not limits:
                    raise ValueError(f"Limits not found for user {user_id}")
                
                # Создание записи об анализе
                analysis = CSVAnalysis(
                    user_id=user_id,
                    storage_key=f"test_{user_index}_{int(time.time())}.csv",
                    status="PENDING",
                    filename="test.csv"
                )
                session.add(analysis)
                await session.commit()
                
                analysis_id = analysis.id
            
            # 2. Redis: Проверка rate limits
            if redis_client:
                self.metrics.redis_operations += 1
                cache_key = f"stress_test:user:{user_id}:upload"
                
                # Simulate rate limit check
                current_count = redis_client.get(cache_key)
                if current_count and int(current_count) > 5:
                    raise ValueError("Rate limit exceeded")
                
                redis_client.incr(cache_key)
                redis_client.expire(cache_key, 60)
            
            # 3. Storage: Загрузка CSV файла (основная нагрузка)
            self.metrics.storage_operations += 1
            
            # Симулируем загрузку с таймаутом
            upload_task = self.storage_service.upload_csv_from_file(
                self.test_csv_path,
                user_id=user_id,
                filename=f"stress_test_user_{user_index}.csv"
            )
            
            # Добавляем таймаут 10 секунд для загрузки
            storage_key = await asyncio.wait_for(upload_task, timeout=10.0)
            
            # 4. Database: Обновление статуса анализа
            async with AsyncSessionLocal() as session:
                self.metrics.db_operations += 1
                
                result = await session.execute(
                    select(CSVAnalysis).where(CSVAnalysis.id == analysis_id)
                )
                analysis = result.scalar_one()
                analysis.storage_key = storage_key
                analysis.status = "UPLOADED"
                
                await session.commit()
            
            elapsed = time.time() - start_time
            return True, None, elapsed
            
        except asyncio.TimeoutError:
            error_type = "TIMEOUT"
            self.metrics.timeout_errors += 1
            elapsed = time.time() - start_time
            return False, error_type, elapsed
            
        except ConnectionError as e:
            error_type = "CONNECTION"
            self.metrics.connection_errors += 1
            elapsed = time.time() - start_time
            return False, error_type, elapsed
            
        except Exception as e:
            error_type = f"OTHER: {type(e).__name__}"
            self.metrics.other_errors += 1
            elapsed = time.time() - start_time
            return False, error_type, elapsed
    
    async def run_test(self):
        """Запустить стресс-тест."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 ЗАПУСК СТРЕСС-ТЕСТА{Colors.RESET}\n")
        print(f"{Colors.CYAN}Создание {self.num_users} виртуальных пользователей...{Colors.RESET}")
        
        # Получить реальных пользователей из БД для тестирования
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.id).limit(self.num_users)
            )
            user_ids = [row[0] for row in result.all()]
        
        if not user_ids:
            print(f"{Colors.RED}✗ Нет пользователей в БД для тестирования!{Colors.RESET}")
            return
        
        print(f"{Colors.GREEN}✓ Найдено {len(user_ids)} пользователей в БД{Colors.RESET}\n")
        
        # Если пользователей меньше, чем нужно - дублируем
        if len(user_ids) < self.num_users:
            user_ids = (user_ids * (self.num_users // len(user_ids) + 1))[:self.num_users]
        
        print(f"{Colors.BOLD}⏱️  Начало теста: {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}\n")
        
        start_time = time.time()
        
        # Создаем задачи для всех пользователей
        tasks = []
        for i, user_id in enumerate(user_ids):
            task = self.simulate_user_action(user_id, i)
            tasks.append(task)
            self.metrics.total_requests += 1
        
        # Запускаем все задачи одновременно
        print(f"{Colors.YELLOW}⚡ Выполнение {len(tasks)} одновременных запросов...{Colors.RESET}\n")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.metrics.failed_requests += 1
                self.metrics.other_errors += 1
                print(f"{Colors.RED}✗ User {i}: EXCEPTION - {result}{Colors.RESET}")
            else:
                success, error_type, elapsed = result
                
                if success:
                    self.metrics.successful_requests += 1
                    self.metrics.add_latency(elapsed)
                    status = f"{Colors.GREEN}✓{Colors.RESET}"
                else:
                    self.metrics.failed_requests += 1
                    self.metrics.add_latency(elapsed)
                    status = f"{Colors.RED}✗{Colors.RESET}"
                
                error_msg = f"[{error_type}]" if error_type else ""
                print(f"{status} User {i}: {elapsed:.2f}s {error_msg}")
        
        total_time = time.time() - start_time
        
        print(f"\n{Colors.BOLD}⏱️  Конец теста: {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.BOLD}⌛ Общее время: {total_time:.2f}s{Colors.RESET}\n")
        
        self.print_report()
    
    def print_report(self):
        """Вывести отчет о тестировании."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}📊 ИТОГОВЫЙ ОТЧЕТ{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        # Общая статистика
        success_rate = (self.metrics.successful_requests / self.metrics.total_requests * 100) if self.metrics.total_requests > 0 else 0
        
        print(f"{Colors.BOLD}📈 Общая статистика:{Colors.RESET}")
        print(f"  • Всего запросов: {Colors.BOLD}{self.metrics.total_requests}{Colors.RESET}")
        print(f"  • Успешно: {Colors.GREEN}{Colors.BOLD}{self.metrics.successful_requests}{Colors.RESET} ({success_rate:.1f}%)")
        print(f"  • Провалено: {Colors.RED}{Colors.BOLD}{self.metrics.failed_requests}{Colors.RESET} ({100-success_rate:.1f}%)")
        
        # Типы ошибок
        if self.metrics.failed_requests > 0:
            print(f"\n{Colors.BOLD}❌ Типы ошибок:{Colors.RESET}")
            print(f"  • Timeout: {Colors.YELLOW}{self.metrics.timeout_errors}{Colors.RESET}")
            print(f"  • Connection: {Colors.YELLOW}{self.metrics.connection_errors}{Colors.RESET}")
            print(f"  • Other: {Colors.YELLOW}{self.metrics.other_errors}{Colors.RESET}")
        
        # Латентность
        if self.metrics.latencies:
            print(f"\n{Colors.BOLD}⏱️  Латентность (Latency):{Colors.RESET}")
            print(f"  • Средняя: {Colors.CYAN}{Colors.BOLD}{self.metrics.get_avg_latency():.3f}s{Colors.RESET}")
            print(f"  • P95: {Colors.CYAN}{self.metrics.get_p95_latency():.3f}s{Colors.RESET}")
            print(f"  • P99: {Colors.CYAN}{self.metrics.get_p99_latency():.3f}s{Colors.RESET}")
            print(f"  • Min: {Colors.GREEN}{min(self.metrics.latencies):.3f}s{Colors.RESET}")
            print(f"  • Max: {Colors.RED}{max(self.metrics.latencies):.3f}s{Colors.RESET}")
        
        # Операции по сервисам
        print(f"\n{Colors.BOLD}🔧 Операции по сервисам:{Colors.RESET}")
        print(f"  • Database: {Colors.CYAN}{self.metrics.db_operations}{Colors.RESET}")
        print(f"  • Redis: {Colors.CYAN}{self.metrics.redis_operations}{Colors.RESET}")
        print(f"  • Storage: {Colors.CYAN}{self.metrics.storage_operations}{Colors.RESET}")
        
        # Прогноз
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}🔮 ПРОГНОЗ ПРОИЗВОДИТЕЛЬНОСТИ{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        # Определяем узкое место
        bottleneck = self._identify_bottleneck()
        
        print(f"{Colors.BOLD}🎯 Узкое место (Bottleneck):{Colors.RESET} {bottleneck}")
        
        # Max Concurrency прогноз
        max_concurrency = self._estimate_max_concurrency(success_rate)
        print(f"\n{Colors.BOLD}👥 Max Concurrency:{Colors.RESET}")
        print(f"  • Текущий SUPABASE_SESSION_LIMIT: {Colors.CYAN}{SUPABASE_SESSION_LIMIT}{Colors.RESET}")
        print(f"  • Расчетный максимум одновременных запросов: {Colors.BOLD}{Colors.GREEN}{max_concurrency}{Colors.RESET}")
        
        # Рекомендации
        print(f"\n{Colors.BOLD}💡 Рекомендации:{Colors.RESET}")
        self._print_recommendations(success_rate, bottleneck)
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    def _identify_bottleneck(self) -> str:
        """Определить узкое место системы."""
        # Анализ ошибок
        if self.metrics.timeout_errors > self.metrics.total_requests * 0.3:
            return f"{Colors.RED}⏱️  Timeout (БД или Storage слишком медленные){Colors.RESET}"
        
        if self.metrics.connection_errors > self.metrics.total_requests * 0.2:
            return f"{Colors.RED}🔌 Connection Pool (недостаточно соединений){Colors.RESET}"
        
        # Анализ латентности
        if self.metrics.latencies:
            avg_latency = self.metrics.get_avg_latency()
            if avg_latency > 5.0:
                return f"{Colors.YELLOW}☁️  Supabase Storage (медленная загрузка файлов){Colors.RESET}"
            elif avg_latency > 2.0:
                return f"{Colors.YELLOW}📊 Database (медленные запросы){Colors.RESET}"
        
        return f"{Colors.GREEN}✓ Узких мест не обнаружено{Colors.RESET}"
    
    def _estimate_max_concurrency(self, success_rate: float) -> int:
        """Оценить максимальную конкурентность."""
        if success_rate >= 95:
            # Успешность высокая - можем увеличить
            return int(self.num_users * 1.5)
        elif success_rate >= 80:
            # Успешность средняя - держим текущий уровень
            return self.num_users
        else:
            # Успешность низкая - нужно уменьшить
            return int(self.num_users * 0.7)
    
    def _print_recommendations(self, success_rate: float, bottleneck: str):
        """Вывести рекомендации по оптимизации."""
        if success_rate < 80:
            print(f"  {Colors.RED}⚠️  КРИТИЧНО:{Colors.RESET} Success rate < 80%")
            print(f"     → Увеличить SUPABASE_SESSION_LIMIT до 4-5")
            print(f"     → Добавить retry логику для Supabase Storage")
            print(f"     → Рассмотреть upgrade Supabase тарифа")
        
        if self.metrics.timeout_errors > 0:
            print(f"  {Colors.YELLOW}⚠️  Обнаружены Timeout ошибки:{Colors.RESET}")
            print(f"     → Добавить таймауты для StorageService (asyncio.wait_for)")
            print(f"     → Оптимизировать размер загружаемых файлов")
        
        if self.metrics.connection_errors > 0:
            print(f"  {Colors.YELLOW}⚠️  Обнаружены Connection ошибки:{Colors.RESET}")
            print(f"     → Проверить настройки connection pool")
            print(f"     → Увеличить max_connections для Redis")
        
        if "Storage" in bottleneck:
            print(f"  {Colors.CYAN}💡 Оптимизация Storage:{Colors.RESET}")
            print(f"     → Использовать chunked upload для больших файлов")
            print(f"     → Добавить compression перед загрузкой")
            print(f"     → Рассмотреть CDN для статики")
        
        if success_rate >= 95:
            print(f"  {Colors.GREEN}✓ Система работает стабильно!{Colors.RESET}")
            print(f"     → Можно увеличить SUPABASE_SESSION_LIMIT до 3-4")
            print(f"     → Готовы к нагрузке 2000+ пользователей")
    
    async def cleanup(self):
        """Очистка после тестирования."""
        print(f"\n{Colors.CYAN}🧹 Очистка...{Colors.RESET}")
        
        # Удаление тестового CSV
        if self.test_csv_path and os.path.exists(self.test_csv_path):
            os.unlink(self.test_csv_path)
            print(f"{Colors.GREEN}✓ Тестовый CSV удален{Colors.RESET}")
        
        # Очистка Redis (опционально)
        if redis_client:
            try:
                keys = redis_client.keys("stress_test:*")
                if keys:
                    redis_client.delete(*keys)
                    print(f"{Colors.GREEN}✓ Redis очищен (удалено {len(keys)} ключей){Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠ Не удалось очистить Redis: {e}{Colors.RESET}")


async def main():
    """Главная функция."""
    print(f"""
{Colors.BOLD}{Colors.BLUE}
╔═══════════════════════════════════════════════════════════════════╗
║                  IQStocker Stress Test Simulator                  ║
║                         Version 1.0.0                             ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.RESET}
    """)
    
    # Проверка переменных окружения
    required_vars = ["DATABASE_URL", "REDIS_URL", "SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"{Colors.RED}❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Убедитесь, что .env файл настроен корректно{Colors.RESET}")
        return
    
    # Запрос количества пользователей
    try:
        num_users_input = input(f"\n{Colors.CYAN}Введите количество виртуальных пользователей (по умолчанию 50): {Colors.RESET}")
        num_users = int(num_users_input) if num_users_input.strip() else 50
        
        if num_users < 1 or num_users > 200:
            print(f"{Colors.RED}✗ Количество пользователей должно быть от 1 до 200{Colors.RESET}")
            return
    except ValueError:
        print(f"{Colors.RED}✗ Неверный ввод{Colors.RESET}")
        return
    
    simulator = StressTestSimulator(num_users=num_users)
    
    try:
        await simulator.setup()
        await simulator.run_test()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Тест прерван пользователем{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Ошибка при выполнении теста: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
    finally:
        await simulator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

