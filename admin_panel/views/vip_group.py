"""VIP Group whitelist management views for admin panel."""

import csv
import io
import logging
from fastapi import APIRouter, Request, Query, Path, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime

from config.database import AsyncSessionLocal
from database.models.vip_group_whitelist import VIPGroupWhitelist

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/vip-group", response_class=HTMLResponse)
async def vip_group_page(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100)
):
    """VIP Group whitelist management page."""
    async with AsyncSessionLocal() as session:
        # Get total count
        count_query = select(func.count(VIPGroupWhitelist.id))
        count_result = await session.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Pagination
        offset = (page - 1) * per_page
        query = select(VIPGroupWhitelist).order_by(desc(VIPGroupWhitelist.added_at)).offset(offset).limit(per_page)
        
        result = await session.execute(query)
        whitelist_entries = result.scalars().all()
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return templates.TemplateResponse(
            "vip_group.html",
            {
                "request": request,
                "whitelist_entries": whitelist_entries,
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "per_page": per_page
            }
        )


@router.post("/vip-group/import-csv", response_class=JSONResponse)
async def import_csv(
    request: Request,
    file: UploadFile = File(...)
):
    """Import CSV file with whitelist users."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    added_count = 0
    skipped_count = 0
    errors = []
    
    async with AsyncSessionLocal() as session:
        try:
            # Read CSV file
            contents = await file.read()
            csv_text = contents.decode('utf-8-sig')  # Handle BOM
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            
            # Get admin username for added_by field
            admin_username = request.session.get("admin_username", "admin")
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
                try:
                    # Skip empty rows
                    if not row or not any(row.values()):
                        continue
                    
                    # Try to get ID from different possible column names
                    telegram_id = None
                    for col_name in ['ID', 'id', 'telegram_id', 'Telegram ID', 'user_id']:
                        if col_name in row:
                            value = row[col_name]
                            # Handle empty strings, whitespace, None
                            if value and str(value).strip():
                                try:
                                    telegram_id = int(str(value).strip())
                                    break
                                except (ValueError, TypeError):
                                    continue
                    
                    # ID is required - skip if not found
                    if not telegram_id:
                        errors.append(f"Row {row_num}: No valid ID found (skipped)")
                        skipped_count += 1
                        continue
                    
                    # Check if already exists
                    existing_query = select(VIPGroupWhitelist).where(
                        VIPGroupWhitelist.telegram_id == telegram_id
                    )
                    existing_result = await session.execute(existing_query)
                    existing = existing_result.scalar_one_or_none()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Get optional fields - all are optional except ID
                    # Clean and normalize values
                    def clean_value(value):
                        """Clean and normalize CSV value."""
                        if value is None:
                            return None
                        value_str = str(value).strip()
                        return value_str if value_str else None
                    
                    username = clean_value(row.get('Username') or row.get('username'))
                    first_name = clean_value(row.get('First Name') or row.get('first_name'))
                    note = f"Imported from CSV on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # Create whitelist entry - all fields except telegram_id are optional
                    whitelist_entry = VIPGroupWhitelist(
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        note=note,
                        added_by=admin_username
                    )
                    session.add(whitelist_entry)
                    added_count += 1
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    skipped_count += 1
                    logger.error(f"Error processing CSV row {row_num}: {e}", exc_info=True)
            
            await session.commit()
            
            return JSONResponse(content={
                "success": True,
                "added": added_count,
                "skipped": skipped_count,
                "errors": errors[:10],  # Limit errors to first 10
                "message": f"Импорт завершен: добавлено {added_count}, пропущено {skipped_count}"
            })
            
        except Exception as e:
            await session.rollback()
            error_detail = str(e)
            logger.error(f"Error importing CSV: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Ошибка при импорте CSV: {error_detail}",
                    "error": error_detail
                }
            )


@router.post("/vip-group/add", response_class=JSONResponse)
async def add_user(
    request: Request,
    telegram_id: int = Form(...),
    username: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    note: Optional[str] = Form(None)
):
    """Add single user to whitelist."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if already exists
            existing_query = select(VIPGroupWhitelist).where(
                VIPGroupWhitelist.telegram_id == telegram_id
            )
            existing_result = await session.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Пользователь уже в whitelist"}
                )
            
            # Get admin username
            admin_username = request.session.get("admin_username", "admin")
            
            # Create whitelist entry
            whitelist_entry = VIPGroupWhitelist(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                note=note,
                added_by=admin_username
            )
            session.add(whitelist_entry)
            await session.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": f"Пользователь {telegram_id} добавлен в whitelist"
            })
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding user to whitelist: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Ошибка: {str(e)}"}
            )


@router.delete("/vip-group/{telegram_id}", response_class=JSONResponse)
async def remove_user(
    request: Request,
    telegram_id: int = Path(...)
):
    """Remove user from whitelist."""
    async with AsyncSessionLocal() as session:
        try:
            # Find entry
            query = select(VIPGroupWhitelist).where(
                VIPGroupWhitelist.telegram_id == telegram_id
            )
            result = await session.execute(query)
            entry = result.scalar_one_or_none()
            
            if not entry:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "Пользователь не найден в whitelist"}
                )
            
            await session.delete(entry)
            await session.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": f"Пользователь {telegram_id} удален из whitelist"
            })
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error removing user from whitelist: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Ошибка: {str(e)}"}
            )


@router.get("/api/vip-group/stats", response_class=JSONResponse)
async def get_stats(request: Request):
    """Get VIP group whitelist statistics."""
    async with AsyncSessionLocal() as session:
        try:
            # Get total count
            count_query = select(func.count(VIPGroupWhitelist.id))
            count_result = await session.execute(count_query)
            total_count = count_result.scalar() or 0
            
            return JSONResponse(content={
                "total_count": total_count,
                "last_check": "N/A"  # TODO: Store last check time if needed
            })
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )

