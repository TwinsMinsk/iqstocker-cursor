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
        
        # Answer callback if provided
        if callback:
            await callback.answer()
            
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Message was not modified")
            if callback:
                await callback.answer()
        elif "message to edit not found" in str(e).lower():
            logger.warning("Message to edit not found, sending new message")
            await target_message.answer(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
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
