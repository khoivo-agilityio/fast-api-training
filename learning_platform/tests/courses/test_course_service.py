"""
Tests for courses/service.py — CourseService class.

Covers: CRUD, enrollment, ownership checks, search/filter.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.courses.exceptions import AlreadyEnrolled, CourseNotFound, NotCourseOwner
from src.courses.schemas import CourseCreateRequest, CourseUpdateRequest
from src.courses.service import CourseService
from tests.conftest import create_test_course, create_test_instructor, create_test_user


class TestCourseServiceCreate:
    """Tests for CourseService.create()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        service = CourseService(async_session)
        return service, instructor

    async def test_create_course(self, setup):
        service, instructor = setup
        data = CourseCreateRequest(title="Python 101", description="Learn Python")
        course = await service.create(data, instructor["user"].id)
        assert course.title == "Python 101"
        assert course.description == "Learn Python"
        assert course.instructor_id == instructor["user"].id

    async def test_create_course_no_description(self, setup):
        service, instructor = setup
        data = CourseCreateRequest(title="Minimal Course")
        course = await service.create(data, instructor["user"].id)
        assert course.title == "Minimal Course"
        assert course.description is None


class TestCourseServiceGetById:
    """Tests for CourseService.get_by_id()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        service = CourseService(async_session)
        return service, course

    async def test_get_by_id_found(self, setup):
        service, course = setup
        result = await service.get_by_id(course.id)
        assert result.id == course.id
        assert result.title == "Test Course"

    async def test_get_by_id_not_found(self, setup):
        from uuid import uuid4

        service, _ = setup
        with pytest.raises(CourseNotFound):
            await service.get_by_id(uuid4())


class TestCourseServiceList:
    """Tests for CourseService.list_courses()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        await create_test_course(async_session, instructor["user"].id, title="Course A")
        await create_test_course(async_session, instructor["user"].id, title="Course B")
        service = CourseService(async_session)
        return service, instructor

    async def test_list_all(self, setup):
        service, _ = setup
        items, total = await service.list_courses()
        assert total == 2
        assert len(items) == 2

    async def test_list_with_search(self, setup):
        service, _ = setup
        items, total = await service.list_courses(search="Course A")
        assert total == 1
        assert items[0].title == "Course A"

    async def test_list_with_pagination(self, setup):
        service, _ = setup
        items, total = await service.list_courses(limit=1, offset=0)
        assert len(items) == 1
        assert total == 2


class TestCourseServiceUpdate:
    """Tests for CourseService.update()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        service = CourseService(async_session)
        return service, course, instructor

    async def test_update_by_owner(self, setup):
        service, course, instructor = setup
        data = CourseUpdateRequest(title="Updated Title")
        updated = await service.update(course.id, data, instructor["user"].id, "instructor")
        assert updated.title == "Updated Title"

    async def test_update_by_non_owner(self, setup, async_session):
        service, course, _ = setup
        other = await create_test_instructor(async_session, email="other@example.com")
        data = CourseUpdateRequest(title="Hacked")
        with pytest.raises(NotCourseOwner):
            await service.update(course.id, data, other["user"].id, "instructor")

    async def test_update_by_admin(self, setup, async_session):
        service, course, _ = setup
        admin = await create_test_user(async_session, email="admin@x.com", role="admin")
        data = CourseUpdateRequest(title="Admin Updated")
        updated = await service.update(course.id, data, admin["user"].id, "admin")
        assert updated.title == "Admin Updated"


class TestCourseServiceEnroll:
    """Tests for CourseService.enroll()."""

    @pytest_asyncio.fixture
    async def setup(self, async_session: AsyncSession, mock_redis):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        student = await create_test_user(
            async_session, email="student@example.com", role="student"
        )
        service = CourseService(async_session)
        return service, course, student

    async def test_enroll_success(self, setup):
        service, course, student = setup
        enrollment = await service.enroll(student["user"].id, course.id)
        assert enrollment.user_id == student["user"].id
        assert enrollment.course_id == course.id

    async def test_enroll_duplicate(self, setup):
        service, course, student = setup
        await service.enroll(student["user"].id, course.id)
        with pytest.raises(AlreadyEnrolled):
            await service.enroll(student["user"].id, course.id)

    async def test_enroll_nonexistent_course(self, setup):
        from uuid import uuid4

        service, _, student = setup
        with pytest.raises(CourseNotFound):
            await service.enroll(student["user"].id, uuid4())

    async def test_is_enrolled(self, setup):
        service, course, student = setup
        assert not await service.is_enrolled(student["user"].id, course.id)
        await service.enroll(student["user"].id, course.id)
        assert await service.is_enrolled(student["user"].id, course.id)
