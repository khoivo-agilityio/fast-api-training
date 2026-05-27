import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.courses.service import CourseService
from src.courses.exceptions import NotEnrolled

@pytest.mark.asyncio
async def test_get_enrolled_course_ids(async_session: AsyncSession):
    service = CourseService(async_session)
    user_id = uuid.uuid4()
    
    # Empty initially
    ids = await service.get_enrolled_course_ids(user_id)
    assert ids == []

@pytest.mark.asyncio
async def test_list_courses_with_instructor_filter(async_session: AsyncSession):
    service = CourseService(async_session)
    instructor_id = uuid.uuid4()
    
    courses, total = await service.list_courses(instructor_id=instructor_id)
    assert total == 0
    assert courses == []

@pytest.mark.asyncio
async def test_check_enrollment_not_enrolled(async_session: AsyncSession):
    service = CourseService(async_session)
    user_id = uuid.uuid4()
    course_id = uuid.uuid4()
    
    with pytest.raises(NotEnrolled):
        await service.check_enrollment(user_id, course_id)
