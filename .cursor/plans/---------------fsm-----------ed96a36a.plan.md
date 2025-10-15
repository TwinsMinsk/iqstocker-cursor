<!-- ed96a36a-46a8-4e67-bdbd-3a6755490225 ec37a377-be1c-4ed8-99d1-4536fda84fe8 -->
# Обновление последовательности приветственных сообщений

## Обзор изменений

Заменить текущую последовательность из 4 сообщений (start_message_1, start_message_2, start_message_3, bot_description) на новую последовательность из 2 сообщений с интерактивной навигацией для просмотра инструкции по загрузке CSV.

## Ключевые файлы

- `bot/handlers/start.py` - хендлер команды /start (строки 73-95)
- `bot/lexicon/lexicon_ru.py` - словарь сообщений (строки 9-26)

## Детальный план реализации

### 1. Добавление новых текстов в lexicon_ru.py

**Файл:** `bot/lexicon/lexicon_ru.py`

**Добавить новые ключи:**

```python
'how_to_start_info': "<b>Как начать пользоваться ботом</b> 🤖\n\n"
                     "1️⃣ <b>Загрузи CSV с Adobe Stock за выбранный месяц.</b>\n"
                     "<i>(Бот работает только с ежемесячными данными. Данные за неделю/квартал и т.д. будут давать искаженные показатели)</i>\n\n"
                     "2️⃣ <b>После этого выбери раздел в меню, с которым хочешь работать.</b>\n\n"
                     "3️⃣ <b>Далее бот выдаст результат:</b> аналитику с пояснениями, список тем, календарь или рекомендации — в зависимости от выбранного раздела.",

'upload_csv_call_to_action': "Чтобы начать, прикрепи CSV за месяц 👇",

'csv_instruction_message': "📄 <b>Как правильно выгрузить CSV?</b>\n\n"
                            "1. Зайдите в ваш личный кабинет на <b>Adobe Stock Contributor</b>.\n"
                            "2. Перейдите в раздел <b>«Панель мониторинга»</b>.\n"
                            "3. В блоке <b>«Продажи»</b> найдите кнопку <b>«Загрузить CSV»</b>.\n"
                            "4. Выберите <b>один календарный месяц</b> (например, с 1 по 30 сентября). Бот не сможет корректно обработать данные за неделю, квартал или другой период.\n"
                            "5. Нажмите «Создать отчет» и скачайте готовый файл.\n\n"
                            "Готово! Теперь просто отправьте этот файл в чат со мной.",
```

**Добавить новые кнопки в LEXICON_COMMANDS_RU:**

```python
'instruction_button': '📄 Инструкция',
'back_button': '⬅️ Назад',
```

### 2. Обновление функции send_welcome_sequence

**Файл:** `bot/handlers/start.py`, строки 73-95

**Текущий код:**

```python
async def send_welcome_sequence(message: Message):
    """Send step-by-step welcome messages."""
    
    # Step 1: First message
    await message.answer(LEXICON_RU['start_message_1'])
    await asyncio.sleep(1.5)
    
    # Step 2: Second message
    await message.answer(LEXICON_RU['start_message_2'])
    await asyncio.sleep(1.5)
    
    # Step 3: Third message
    await message.answer(LEXICON_RU['start_message_3'])
    
    # Step 4: Final message with description and analytics button
    analytics_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['do_analytics'], callback_data="analytics_start")]
    ])
    
    await message.answer(
        LEXICON_RU['bot_description'],
        reply_markup=analytics_keyboard
    )
```

**Новый код:**

```python
async def send_welcome_sequence(message: Message):
    """Send welcome messages with instruction button."""
    
    # Step 1: Информационное сообщение
    await message.answer(LEXICON_RU['how_to_start_info'])
    
    # Step 2: Призыв к действию с кнопкой инструкции
    instruction_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['instruction_button'], 
            callback_data="show_csv_instruction"
        )]
    ])
    
    await message.answer(
        LEXICON_RU['upload_csv_call_to_action'],
        reply_markup=instruction_keyboard
    )
```

### 3. Создание хендлера для кнопки "Инструкция"

**Файл:** `bot/handlers/start.py`

**Добавить новый хендлер после функции handle_existing_user:**

```python
@router.callback_query(F.data == "show_csv_instruction")
async def show_csv_instruction_callback(callback: CallbackQuery):
    """Show CSV instruction."""
    
    # Клавиатура с кнопкой "Назад"
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_button'], 
            callback_data="back_to_upload_prompt"
        )]
    ])
    
    # Редактируем сообщение
    await callback.message.edit_text(
        text=LEXICON_RU['csv_instruction_message'],
        reply_markup=back_keyboard
    )
    
    await callback.answer()
```

### 4. Создание хендлера для кнопки "Назад"

**Файл:** `bot/handlers/start.py`

**Добавить новый хендлер:**

```python
@router.callback_query(F.data == "back_to_upload_prompt")
async def back_to_upload_prompt_callback(callback: CallbackQuery):
    """Return to upload CSV prompt."""
    
    # Клавиатура с кнопкой "Инструкция"
    instruction_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['instruction_button'], 
            callback_data="show_csv_instruction"
        )]
    ])
    
    # Редактируем сообщение обратно
    await callback.message.edit_text(
        text=LEXICON_RU['upload_csv_call_to_action'],
        reply_markup=instruction_keyboard
    )
    
    await callback.answer()
```

### 5. Удаление старых неиспользуемых ключей

**Файл:** `bot/lexicon/lexicon_ru.py`

**Удалить следующие ключи после тестирования:**

- `start_message_1`
- `start_message_2`
- `start_message_3`
- `bot_description` (если он больше не используется в других местах)

**Важно:** Перед удалением `bot_description` нужно проверить, не используется ли он в других частях кода.

### 6. Добавление импорта CallbackQuery

**Файл:** `bot/handlers/start.py`, строка 5

**Текущий импорт:**

```python
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
```

**Обновленный импорт:**

```python
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
```

## Технические детали

**Структура новой последовательности:**

1. **Первое сообщение** - информация о том, как начать работу (3 шага)
2. **Второе сообщение** - призыв загрузить CSV с кнопкой "Инструкция"
3. **При нажатии "Инструкция"** - редактирование сообщения с детальной инструкцией и кнопкой "Назад"
4. **При нажатии "Назад"** - возврат к призыву загрузить CSV

**Преимущества нового подхода:**

- Меньше сообщений в чате (2 вместо 4)
- Интерактивная навигация без загромождения чата
- Детальная инструкция доступна по требованию
- Горизонтальная навигация через редактирование сообщений

**Callback data:**

- `show_csv_instruction` - показать инструкцию
- `back_to_upload_prompt` - вернуться к призыву загрузить CSV

## Результат

После реализации новый пользователь увидит:

1. ✅ Информационное сообщение о том, как начать работу
2. ✅ Призыв загрузить CSV с кнопкой "Инструкция"
3. ✅ Возможность посмотреть детальную инструкцию без загромождения чата
4. ✅ Удобную навигацию между сообщениями

Старые пользователи продолжат видеть приветствие "С возвращением" без изменений.

### To-dos

- [ ] Модифицировать handle_csv_upload: сохранить message_id первого вопроса в state
- [ ] Обновить handle_portfolio_size: удаление сообщения пользователя + редактирование вопроса через bot.edit_message_text()
- [ ] Обновить handle_upload_limit: аналогично с редактированием сообщения
- [ ] Обновить handle_monthly_uploads: аналогично с редактированием сообщения
- [ ] Обновить handle_profit_margin: редактирование с добавлением InlineKeyboardMarkup
- [ ] Обновить handle_content_type_text: использовать bot.edit_message_text() для финального сообщения
- [ ] Протестировать полный flow FSM с горизонтальной навигацией