from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from typing import List, Optional
from datetime import date

from app.database import get_db
from app import models

router = APIRouter()

@router.get("/data", response_model=dict)
def search_data(
    q: Optional[str] = Query(None, description="Текст для поиска"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    category: Optional[str] = Query(None, description="Категория/Кухня"),
    author_id: Optional[int] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    print(f"DEBUG SEARCH: Searching for '{q}' in models.Recipe") #
    query = db.query(models.Recipe)

    # 2. Полнотекстовый поиск (по title и description)
    if q:
        search_filter = or_(
            models.Recipe.title.ilike(f"%{q}%"),
            models.Recipe.description.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)

    # 3. Фильтрация по дате
    if date_from:
        query = query.filter(models.Recipe.created_at >= date_from)
    if date_to:
        query = query.filter(models.Recipe.created_at <= date_to)

    # 4. Фильтрация по категории (если передана)
    if category:
        query = query.filter(models.Recipe.category.ilike(f"%{category}%"))

    # 5. Сортировка
    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Recipe, sort_by)))
    else:
        query = query.order_by(asc(getattr(models.Recipe, sort_by)))

    # 6. Пагинация
    total = query.count()
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()

    data_list = []
    for item in results:
        data_list.append({
            "id": item.id,
            "name": item.title, 
            "description": item.description,
            "created_at": item.created_at,
            "category": item.category,
            "cooking_time": item.cooking_time
        })

    return {
        "data": data_list,
        "total": total,
        "page": page,
        "limit": limit
    }