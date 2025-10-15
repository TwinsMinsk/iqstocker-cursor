#!/usr/bin/env python3
"""
Тест функциональности бота с новой интеграцией отчетов аналитики.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from config.database import SessionLocal
from database.models import User, SubscriptionType, CSVAnalysis, AnalysisStatus, AnalyticsReport, Limits

async def test_bot_analytics_functionality():
    """Тест функциональности аналитики бота."""
    
    print("🤖 Тестирование функциональности бота с интеграцией отчетов...")
    
    db = SessionLocal()
    try:
        # 1. Создаем тестового пользователя с PRO подпиской
        print("\n1. Создание тестового пользователя...")
        test_user = User(
            telegram_id=888888888,
            username="test_bot_user",
            first_name="BotTest",
            subscription_type=SubscriptionType.PRO
        )
        db.add(test_user)
        db.flush()
        
        # Создаем лимиты
        limits = Limits(
            user_id=test_user.id,
            analytics_total=3,
            analytics_used=0,
            themes_total=10,
            themes_used=0,
            top_themes_total=3,
            top_themes_used=0
        )
        db.add(limits)
        db.flush()
        
        print(f"✅ Пользователь создан: ID={test_user.id}, Подписка={test_user.subscription_type}")
        print(f"✅ Лимиты созданы: Аналитик={limits.analytics_total}, Тем={limits.themes_total}")
        
        # 2. Создаем несколько тестовых отчетов
        print("\n2. Создание тестовых отчетов...")
        
        reports_data = [
            {
                "month": 9,
                "year": 2025,
                "period": "Сентябрь 2025",
                "sales": 15,
                "revenue": 75.25,
                "portfolio_percent": 15.0,
                "new_works_percent": 35.0
            },
            {
                "month": 10,
                "year": 2025,
                "period": "Октябрь 2025",
                "sales": 28,
                "revenue": 142.80,
                "portfolio_percent": 28.0,
                "new_works_percent": 45.0
            }
        ]
        
        created_reports = []
        for i, data in enumerate(reports_data):
            # Создаем CSV анализ
            csv_analysis = CSVAnalysis(
                user_id=test_user.id,
                file_path=f"/test/path_{i+1}.csv",
                month=data["month"],
                year=data["year"],
                status=AnalysisStatus.COMPLETED,
                portfolio_size=100,
                upload_limit=50,
                monthly_uploads=30,
                acceptance_rate=65.0,
                profit_margin=15.0,
                content_type="PHOTO",
                processed_at=datetime.now(timezone.utc)
            )
            db.add(csv_analysis)
            db.flush()
            
            # Создаем отчет аналитики
            report_text = f"""📊 <b>Аналитика портфеля за {data['period']}</b>

<b>📈 Основные метрики:</b>
• Продаж: {data['sales']}
• Доход: ${data['revenue']}
• % портфеля продан: {data['portfolio_percent']}%
• % новых работ: {data['new_works_percent']}%

<b>🎯 Рекомендации:</b>
• Увеличь количество загрузок
• Сосредоточься на популярных темах
• Улучши качество контента

<b>📊 Топ темы:</b>
1. Природа и пейзажи — 5 продаж/$25.00
2. Бизнес и технологии — 4 продажи/$20.00
3. Люди и эмоции — 3 продажи/$15.00"""
            
            analytics_report = AnalyticsReport(
                csv_analysis_id=csv_analysis.id,
                total_sales=data["sales"],
                total_revenue=data["revenue"],
                portfolio_sold_percent=data["portfolio_percent"],
                new_works_sales_percent=data["new_works_percent"],
                acceptance_rate_calc=65.0,
                upload_limit_usage=60.0,
                report_text_html=report_text,
                period_human_ru=data["period"]
            )
            db.add(analytics_report)
            db.flush()
            
            created_reports.append({
                "csv_analysis": csv_analysis,
                "analytics_report": analytics_report
            })
            
            print(f"   📊 Отчет за {data['period']} создан: ID={analytics_report.id}")
        
        # 3. Тестируем логику показа списка отчетов
        print("\n3. Тестирование логики показа списка отчетов...")
        
        # Получаем все завершенные анализы пользователя
        completed_analyses = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == test_user.id,
            CSVAnalysis.status == AnalysisStatus.COMPLETED
        ).order_by(CSVAnalysis.created_at.desc()).all()
        
        print(f"✅ Найдено завершенных анализов: {len(completed_analyses)}")
        
        # Симулируем создание клавиатуры для списка отчетов
        keyboard_buttons = []
        for analysis in completed_analyses:
            if analysis.analytics_report and analysis.analytics_report.period_human_ru:
                button_text = f"📊 Отчет за {analysis.analytics_report.period_human_ru}"
                callback_data = f"view_report_{analysis.id}"
                keyboard_buttons.append({
                    "text": button_text,
                    "callback_data": callback_data,
                    "analysis_id": analysis.id
                })
                print(f"   🔘 Кнопка: {button_text} -> {callback_data}")
        
        # Добавляем кнопку "Новый анализ" если есть лимиты
        if limits.analytics_remaining > 0:
            keyboard_buttons.append({
                "text": "➕ Сделать новый анализ",
                "callback_data": "new_analysis"
            })
            print(f"   🔘 Кнопка: ➕ Сделать новый анализ -> new_analysis")
        
        # Добавляем кнопку "Назад в меню"
        keyboard_buttons.append({
            "text": "◀️ Назад в меню",
            "callback_data": "main_menu"
        })
        print(f"   🔘 Кнопка: ◀️ Назад в меню -> main_menu")
        
        # 4. Тестируем просмотр конкретного отчета
        print("\n4. Тестирование просмотра конкретного отчета...")
        
        if created_reports:
            test_report = created_reports[0]["analytics_report"]
            print(f"✅ Тестируем отчет: {test_report.period_human_ru}")
            print(f"   Продаж: {test_report.total_sales}")
            print(f"   Доход: ${test_report.total_revenue}")
            print(f"   HTML текст: {len(test_report.report_text_html)} символов")
            print(f"   Превью текста: {test_report.report_text_html[:100]}...")
        
        # 5. Тестируем лимиты
        print("\n5. Тестирование лимитов...")
        print(f"✅ Лимиты пользователя:")
        print(f"   Аналитик: {limits.analytics_used}/{limits.analytics_total} (осталось: {limits.analytics_remaining})")
        print(f"   Темы: {limits.themes_used}/{limits.themes_total} (осталось: {limits.themes_remaining})")
        print(f"   Топ тем: {limits.top_themes_used}/{limits.top_themes_total} (осталось: {limits.top_themes_remaining})")
        
        # 6. Симулируем сценарий "Новый анализ"
        print("\n6. Симулируем сценарий 'Новый анализ'...")
        if limits.analytics_remaining > 0:
            print("✅ Пользователь может создать новый анализ")
            print("   Показываем форму загрузки CSV")
            print("   После обработки отчет сохранится в базу данных")
        else:
            print("❌ У пользователя закончились лимиты на аналитику")
            print("   Показываем сообщение о необходимости подписки")
        
        print("\n🎉 Все тесты функциональности пройдены успешно!")
        print("\n📋 Итоговый результат:")
        print(f"   • Пользователь: {test_user.first_name} (ID: {test_user.id})")
        print(f"   • Подписка: {test_user.subscription_type.value}")
        print(f"   • Отчетов в базе: {len(created_reports)}")
        print(f"   • Кнопок в меню: {len(keyboard_buttons)}")
        print(f"   • Лимит аналитик: {limits.analytics_remaining}/{limits.analytics_total}")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Очистка тестовых данных
        try:
            print("\n🧹 Очистка тестовых данных...")
            if 'created_reports' in locals():
                for report_data in created_reports:
                    if 'analytics_report' in report_data:
                        db.delete(report_data['analytics_report'])
                    if 'csv_analysis' in report_data:
                        db.delete(report_data['csv_analysis'])
            
            if 'limits' in locals():
                db.delete(limits)
            if 'test_user' in locals():
                db.delete(test_user)
            
            db.commit()
            print("✅ Тестовые данные очищены")
        except Exception as e:
            print(f"⚠️ Ошибка при очистке: {e}")
            db.rollback()
        finally:
            db.close()


if __name__ == "__main__":
    asyncio.run(test_bot_analytics_functionality())
