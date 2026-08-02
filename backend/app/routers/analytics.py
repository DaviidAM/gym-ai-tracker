from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    return {
"message": "Analytics endpoint - placeholder",
        "user_id": user_id,
        "note": "Implement with Pandas/Polars after auth is wired"
    }
