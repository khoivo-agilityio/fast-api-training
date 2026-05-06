"""
Tests for lessons/service.py — LessonService class.

Covers: CRUD, ordering, not-found errors.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.lessons.exceptions import LessonNotFound
from src.lessons.schemas import LessonCreateRequest, LessonUpdateRequest
from src.lessons.service import LessonService
from tests.conftest import create_test_course, create_test_instructor, create_test_lesson


class TestLessonServiceCreate:
    """Tests for LessonService.create()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        service = LessonService(async_session)
        return service, course

    async def test_create_lesson(self, setup):
        service, course = setup
        data = LessonCreateRequest(
            title="Intro", content="Welcome to the course", order=1
        )
        lesson = await service.create(course.id, data)
        assert lesson.title == "Intro"
        assert lesson.content == "Welcome to the course"
        assert lesson.order == 1
        assert lesson.course_id == course.id


class TestLessonServiceGetById:
    """Tests for LessonService.get_by_id()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        service = LessonService(async_session)
        return service, lesson

    async def test_get_by_id_found(self, setup):
        service, lesson = setup
        result = await service.get_by_id(lesson.id)
        assert result.id == lesson.id

    async def test_get_by_id_not_found(self, setup):
        from uuid import uuid4

        service, _ = setup
        with pytest.raises(LessonNotFound):
            await service.get_by_id(uuid4())


class TestLessonServiceListByCourse:
    """Tests for LessonService.list_by_course()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        await create_test_lesson(async_session, course.id, title="L1", order=2)
        await create_test_lesson(async_session, course.id, title="L2", order=1)
        service = LessonService(async_session)
        return service, course

    async def test_list_ordered(self, setup):
        service, course = setup
        lessons = await service.list_by_course(course.id)
        assert len(lessons) == 2
        assert lessons[0].title == "L2"  # order=1 comes first
        assert lessons[1].title == "L1"  # order=2 comes second


class TestLessonServiceUpdate:
    """Tests for LessonService.update()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        service = LessonService(async_session)
        return service, lesson

    async def test_update_title(self, setup):
        service, lesson = setup
        data = LessonUpdateRequest(title="Updated Title")
        updated = await service.update(lesson.id, data)
        assert updated.title == "Updated Title"
        assert updated.content == lesson.content  # unchanged


class TestLessonServiceDelete:
    """Tests for LessonService.delete()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        service = LessonService(async_session)
        return service, lesson

    async def test_delete_lesson(self, setup):
        service, lesson = setup
        await service.delete(lesson.id)
        with pytest.raises(LessonNotFound):
            await service.get_by_id(lesson.id)
