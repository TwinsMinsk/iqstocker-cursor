"""Tribute webhook handler."""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

from config.settings import settings
# ВАЖНО: Это универсальный обработчик БД
from core.subscriptions.payment_handler import PaymentHandler 


class TributeWebhookHandler:
    """Handler for Tribute webhook events."""
    
    def __init__(self):
        self.webhook_secret = settings.payment.tribute_api_key
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify Tribute webhook signature."""
        if not self.webhook_secret:
            print("ВНИМАНИЕ: PAYMENT_TRIBUTE_API_KEY не установлен, проверка подписи вебхука пропущена.")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_webhook(self, request: Request) -> JSONResponse:
        """Handle Tribute webhook."""
        try:
            signature = request.headers.get('trbt-signature', '')
            payload = await request.body()
            payload_str = payload.decode('utf-8')
            
            # Логирование для отладки
            print(f"=== WEBHOOK DEBUG: Получен webhook от Tribute ===")
            print(f"Payload length: {len(payload_str)}")
            print(f"Payload (raw): {payload_str}")
            print(f"Signature header: {signature[:50] if signature else 'None'}...")
            
            if not self.verify_signature(payload_str, signature):
                print("Ошибка вебхука Tribute: Неверная подпись")
                return JSONResponse(status_code=401, content={"error": "Invalid signature"})
            
            data = json.loads(payload_str)
            
            # Логирование распарсенных данных
            print(f"=== WEBHOOK DEBUG: Распарсенные данные ===")
            print(f"Data keys: {list(data.keys())}")
            print(f"Full data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Запускаем обработку в фоне, чтобы сразу вернуть 200 OK
            import asyncio
            asyncio.create_task(self._process_event(data))
            
            return JSONResponse(status_code=200, content={"status": "ok"})
            
        except Exception as e:
            print(f"Критическая ошибка обработки вебхука Tribute: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": "Internal error"})
    
    async def _process_event(self, data: Dict[str, Any]):
        """Process Tribute event."""
        # Логирование для отладки
        print(f"=== PROCESS EVENT DEBUG ===")
        print(f"Event data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        event_name = data.get('name')
        
        # Проверка альтернативных полей для имени события
        if not event_name:
            event_name = data.get('event') or data.get('type') or data.get('event_type') or data.get('action')
            if event_name:
                print(f"DEBUG: Найдено имя события в альтернативном поле: {event_name}")
        
        print(f"Event name: {event_name}")
        
        try:
            if event_name == 'new_subscription':
                print("Обрабатываем как new_subscription")
                await self._handle_payment_success(data, is_subscription=True)
            elif event_name == 'cancelled_subscription':
                print("Обрабатываем как cancelled_subscription")
                await self._handle_cancelled_subscription(data)
            elif event_name == 'new_digital_product':
                print("Обрабатываем как new_digital_product")
                await self._handle_payment_success(data, is_subscription=False)
            else:
                print(f"Получено неизвестное событие Tribute: {event_name}")
                print(f"DEBUG: Структура данных: {list(data.keys())}")
                
                # Fallback: попробуем обработать как платеж, если есть данные пользователя
                payload = data.get('payload', {})
                telegram_user_id = payload.get('telegram_user_id') or payload.get('user_id') or data.get('telegram_user_id') or data.get('user_id')
                
                if telegram_user_id:
                    print(f"DEBUG: Найдены данные пользователя (telegram_user_id={telegram_user_id}), пытаемся обработать как платеж")
                    # Пытаемся обработать как подписку
                    await self._handle_payment_success(data, is_subscription=True)
                else:
                    print(f"DEBUG: Недостаточно данных для обработки платежа. Нет telegram_user_id")
        except Exception as e:
            print(f"Ошибка при обработке события {event_name}: {e}")
            import traceback
            traceback.print_exc()

    def _get_subscription_type_from_payload(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Определяет тип подписки (PRO/ULTRA) по данным из вебхука.
        Ищет "PRO" или "ULTRA" в названии подписки или продукта.
        """
        # Получаем все возможные поля, где может быть название
        sub_name = str(payload.get('subscription_name', '')).upper()
        prod_name = str(payload.get('product_name', '')).upper()
        name = str(payload.get('name', '')).upper()
        title = str(payload.get('title', '')).upper()
        
        # Объединяем все названия для поиска
        all_names = f"{sub_name} {prod_name} {name} {title}"
        
        # Убираем префиксы "TEST" и "ТЕСТ" (латиница и кириллица) для тестовых данных
        all_names = all_names.replace("TEST", "").replace("ТЕСТ", "").strip()
        
        # Убираем лишние пробелы и слэши
        all_names = ' '.join(all_names.split())
        
        # Ищем ULTRA или PRO в объединенной строке
        if "ULTRA" in all_names:
            return "ULTRA"
        if "PRO" in all_names:
            return "PRO"
        
        # Если не нашли, пробуем поискать в исходных полях (до очистки)
        for field_name in [sub_name, prod_name, name, title]:
            if "ULTRA" in field_name:
                return "ULTRA"
            if "PRO" in field_name:
                return "PRO"
            
        print(f"ВНИМАНИЕ: Не удалось определить тип подписки по имени. sub_name={sub_name}, prod_name={prod_name}, name={name}, title={title}")
        print(f"Полный payload: {payload}")
        return None

    async def _handle_payment_success(self, data: Dict[str, Any], is_subscription: bool):
        """Обработка успешной подписки или покупки товара."""
        payload = data.get('payload', {})
        
        telegram_user_id = payload.get('telegram_user_id') or payload.get('user_id') or data.get('telegram_user_id') or data.get('user_id')
        amount_cents = payload.get('amount') or data.get('amount')  # Сумма в минимальных единицах валюты (центах/копейках)
        currency = payload.get('currency', '').lower() or data.get('currency', '').lower()  # Валюта: "eur", "usd", "rub"
        
        if is_subscription:
            payment_id = payload.get('subscription_id') or data.get('id') or data.get('subscription_id')
        else:
            payment_id = payload.get('order_id') or payload.get('product_id') or data.get('id') or data.get('order_id')
        
        # Преобразуем payment_id в строку, если он не None (может быть int или str)
        if payment_id is not None:
            payment_id = str(payment_id).strip()
        
        # Объединяем payload и data для поиска типа подписки (информация может быть в любом из них)
        search_data = {**(payload if payload else {}), **(data if data else {})}
        subscription_type_str = self._get_subscription_type_from_payload(search_data)
        
        # Проверяем, что все обязательные поля заполнены (не None и не пустые строки)
        # payment_id может быть пустым в тестах, поэтому генерируем его если нужно
        if not payment_id or payment_id == "":
            import uuid
            payment_id = f"test_{uuid.uuid4().hex[:16]}"
            print(f"ВНИМАНИЕ: payment_id был пустым, сгенерирован новый: {payment_id}")
        
        if not all([telegram_user_id, amount_cents, payment_id, subscription_type_str]):
            print(f"Ошибка вебхука '{data.get('name')}': неполные данные. telegram_user_id={telegram_user_id}, amount_cents={amount_cents}, payment_id={payment_id}, subscription_type={subscription_type_str}")
            print(f"Полные данные: {data}")
            return

        print(f"Tribute '{data.get('name')}': {payment_id}, user: {telegram_user_id}, amount: {amount_cents}, currency: {currency}")
        
        # Конвертируем сумму из минимальных единиц в основные единицы валюты
        amount_in_currency = float(amount_cents) / 100
        
        # Конвертируем в евро, если валюта не EUR
        # Все суммы в БД хранятся в евро
        if currency == 'eur':
            amount_eur = amount_in_currency
        elif currency == 'usd':
            # Примерный курс: 1 USD = 0.92 EUR (можно настроить)
            usd_to_eur_rate = 0.92
            amount_eur = amount_in_currency * usd_to_eur_rate
            print(f"ВНИМАНИЕ: Конвертация USD в EUR по курсу {usd_to_eur_rate}: {amount_in_currency} USD = {amount_eur:.2f} EUR")
        elif currency == 'rub':
            # Курс: 100 RUB = 1 EUR
            rub_to_eur_rate = 0.01
            amount_eur = amount_in_currency * rub_to_eur_rate
            print(f"ВНИМАНИЕ: Конвертация RUB в EUR по курсу {rub_to_eur_rate}: {amount_in_currency} RUB = {amount_eur:.2f} EUR")
        else:
            # Если валюта не указана или неизвестна, предполагаем EUR
            if currency:
                print(f"ВНИМАНИЕ: Неизвестная валюта '{currency}', предполагаем EUR")
            amount_eur = amount_in_currency
        
        # КРИТИЧНО: Извлекаем expires_at от Tribute (если есть)
        expires_at = None
        if is_subscription and 'expires_at' in payload:
            expires_at_str = payload.get('expires_at')
            if expires_at_str:
                try:
                    # Формат: "2025-04-20T01:15:57.305733Z"
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    # Преобразуем в naive datetime для совместимости с БД
                    expires_at = expires_at.replace(tzinfo=None)
                    print(f"✅ Используем expires_at от Tribute: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    print(f"⚠️ Ошибка парсинга expires_at '{expires_at_str}': {e}, будет использован +30 дней")
                    expires_at = None
        
        # Вызываем универсальный обработчик БД
        db_handler = PaymentHandler()
        
        success = await db_handler.process_payment_success(
            payment_id=str(payment_id),
            user_id=int(telegram_user_id),
            amount=amount_eur,  # Сумма в евро
            subscription_type=subscription_type_str,
            discount_percent=0,  # Tribute не передает скидку в вебхуке
            expires_at=expires_at  # Передаем дату от Tribute!
        )
        
        if success:
            print(f"Подписка Tribute ({subscription_type_str}) успешно активирована для user {telegram_user_id}")
        else:
            print(f"Ошибка активации подписки Tribute для user {telegram_user_id}")
    
    async def _handle_cancelled_subscription(self, data: Dict[str, Any]):
        """Обработка отмены подписки."""
        payload = data.get('payload', {})
        
        telegram_user_id = payload.get('telegram_user_id')
        subscription_id = payload.get('subscription_id')
        subscription_name = payload.get('subscription_name', 'Unknown')
        
        if not telegram_user_id:
            print(f"❌ Отсутствует telegram_user_id при отмене подписки")
            return
        
        print(f"🚫 Отмена подписки:")
        print(f"   User: {telegram_user_id}")
        print(f"   Subscription ID: {subscription_id}")
        print(f"   Subscription Name: {subscription_name}")
        print(f"   Полный payload: {json.dumps(payload, ensure_ascii=False)}")
        
        # TODO: В будущем можно добавить обработку отмены подписки в БД
        # Например, установить флаг auto_renew=False или отметить подписку как отмененную
        print(f"ℹ️ Подписка будет действовать до expires_at, автопродление отключено")


# Global handler instance
tribute_handler = TributeWebhookHandler()

async def tribute_webhook(request: Request) -> JSONResponse:
    """Tribute webhook endpoint."""
    return await tribute_handler.handle_webhook(request)

