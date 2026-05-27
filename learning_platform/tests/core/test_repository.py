import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.repository import BaseRepository
from src.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class DummyModel(Base):
    __tablename__ = "dummy_model"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]

class DummyRepository(BaseRepository[DummyModel]):
    pass

@pytest.mark.asyncio
async def test_repository_get_by_id(async_session: AsyncSession):
    # Ensure table exists
    async with async_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    repo = DummyRepository(DummyModel, async_session)
    dummy = DummyModel(name="test")
    repo.add(dummy)
    await async_session.commit()
    
    fetched = await repo.get_by_id(dummy.id)
    assert fetched is not None
    assert fetched.name == "test"

@pytest.mark.asyncio
async def test_repository_list_all(async_session: AsyncSession):
    repo = DummyRepository(DummyModel, async_session)
    dummy1 = DummyModel(name="test1")
    dummy2 = DummyModel(name="test2")
    repo.add(dummy1)
    repo.add(dummy2)
    await async_session.commit()
    
    all_dummies = await repo.list_all()
    assert len(all_dummies) >= 2

@pytest.mark.asyncio
async def test_repository_delete(async_session: AsyncSession):
    repo = DummyRepository(DummyModel, async_session)
    dummy = DummyModel(name="test_delete")
    repo.add(dummy)
    await async_session.commit()
    
    await repo.delete(dummy)
    await async_session.commit()
    
    fetched = await repo.get_by_id(dummy.id)
    assert fetched is None
