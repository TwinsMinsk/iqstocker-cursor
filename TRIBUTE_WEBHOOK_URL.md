# Tribute Webhook URL

## Важная информация для настройки

После деплоя проекта на Railway, необходимо указать следующий URL в настройках Tribute:

### Webhook URL для Tribute:

```
https://your-project-name.up.railway.app/webhook/tribute
```

**Пример:**
```
https://web-production-84a0.up.railway.app/webhook/tribute
```

### Где указать:

1. Войдите в панель автора Tribute
2. Перейдите в настройки вашего проекта/бота
3. Найдите раздел "Webhooks" или "Вебхуки"
4. Укажите URL выше в поле для вебхуков
5. Сохраните настройки

### Проверка работы:

После настройки, Tribute будет отправлять вебхуки на этот URL. Проверить, что эндпоинт работает, можно:

1. GET запрос: `https://your-project.up.railway.app/webhook/tribute`
   - Должен вернуть: `{"status": "ok", "message": "Tribute webhook endpoint is active"}`

2. POST запросы от Tribute будут автоматически обрабатываться при оплате

### Переменные окружения:

Убедитесь, что в Railway установлены следующие переменные:

- `PAYMENT_TRIBUTE_API_KEY` - API ключ из панели Tribute (для проверки подписи)
- `PAYMENT_TRIBUTE_PRO_LINK` - Ссылка на PRO подписку из Tribute
- `PAYMENT_TRIBUTE_ULTRA_LINK` - Ссылка на ULTRA подписку из Tribute
- `PAYMENT_WEBHOOK_URL` - URL вебхука (указан выше)

