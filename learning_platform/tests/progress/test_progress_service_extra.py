import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.progress.service import ProgressService

@pytest.mark.asyncio
async def test_get_lesson_progress(async_session: AsyncSession):
    service = ProgressService(async_session)
    user_id = uuid.uuid4()
    lesson_id = uuid.uuid4()
    
    progress = await service.get_lesson_progress(user_id, lesson_id)
    assert progress is None

@pytest.mark.asyncio
async def test_list_all(async_session: AsyncSession):
    service = ProgressService(async_session)
    
    items = await service.list_all()
    assert items == []
