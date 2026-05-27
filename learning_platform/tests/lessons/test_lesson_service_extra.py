import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.lessons.service import LessonService

@pytest.mark.asyncio
async def test_count_by_course(async_session: AsyncSession):
    service = LessonService(async_session)
    course_id = uuid.uuid4()
    
    count = await service.count_by_course(course_id)
    assert count == 0
