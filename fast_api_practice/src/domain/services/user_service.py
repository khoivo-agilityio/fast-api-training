from src.core.security import hash_password
from src.domain.entities.user import UserEntity
from src.domain.exceptions import ConflictError, DomainValidationError, NotFoundError
from src.domain.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_profile(self, user_id: int) -> UserEntity | None:
        return await self._user_repo.get_by_id(user_id)

    async def list_users(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[UserEntity], int]:
        items = await self._user_repo.list_all(limit=limit, offset=offset)
        total = await self._user_repo.count_all()
        return items, total

    async def update_profile(
        self,
        user_id: int,
        *,
        full_name: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> UserEntity:
        fields: dict = {}
        if full_name is not None:
            fields["full_name"] = full_name
        if email is not None:
            existing = await self._user_repo.get_by_email(email)
            if existing and existing.id != user_id:
                raise ConflictError("Email already in use")
            fields["email"] = email
        if password is not None:
            fields["hashed_password"] = hash_password(password)
        if not fields:
            raise DomainValidationError("No fields to update")
        user = await self._user_repo.update(user_id, **fields)
        if user is None:
            raise NotFoundError("User not found")
        return user
