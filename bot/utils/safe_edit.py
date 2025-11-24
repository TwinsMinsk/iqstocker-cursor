"""Safe message editing utilities."""

import logging
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


async def safe_edit_message(callback: CallbackQuery = None, message: Message = None, text: str = "", reply_markup=None, parse_mode="HTML"):
    """Safely edit message with error handling."""
    
    # Determine which message to edit
    target_message = None
    if callback:
        target_message = callback.message
    elif message:
        target_message = message
    else:
        raise ValueError("Either callback or message must be provided")
    
    try:
        await target_message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        
        # ✅ ОПТИМИЗАЦИЯ: Не вызываем callback.answer() здесь, так как он уже вызывается 
        # в начале обработчиков для быстрого ответа. Если callback.answer() еще не был вызван,
        # это безопасно - обработчик должен вызвать его сам.
            
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Message was not modified")
            # Не вызываем callback.answer() - должен быть вызван в обработчике
        elif "message to edit not found" in str(e).lower():
            logger.warning("Message to edit not found, sending new message")
            await target_message.answer(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        elif "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning("Callback query expired before edit could be applied")
            # Не вызываем callback.answer() - должен быть вызван в обработчике
        else:
            logger.error(f"Failed to edit message: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error while editing message: {e}")
        raise


async def safe_delete_message(callback: CallbackQuery):
    """Safely delete message with error handling."""
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        if "message to delete not found" in str(e).lower():
            logger.debug("Message to delete not found")
        else:
            logger.error(f"Failed to delete message: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting message: {e}")
        raise


async def safe_edit_message_by_id(bot, chat_id: int, message_id: int, text: str = "", reply_markup=None, parse_mode="HTML"):
    """Safely edit message by message_id with error handling."""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Message was not modified")
        elif "message to edit not found" in str(e).lower():
            logger.warning(f"Message {message_id} to edit not found")
        elif "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning("Query expired before edit could be applied")
        else:
            logger.error(f"Failed to edit message {message_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while editing message {message_id}: {e}")