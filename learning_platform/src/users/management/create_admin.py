"""
Create Admin User — Management command.

Usage:
    python -m src.users.management.create_admin \\
        --email admin@example.com \\
        --password Admin1234! \\
        [--display-name "Super Admin"]

Idempotent: if the email already exists, prints a warning and exits.
Connects to the real database configured in .env / environment variables.
"""

import argparse
import asyncio
import sys


async def create_admin(email: str, password: str, display_name: str) -> None:
    """Create an admin user in the database."""
    from src.auth.security import hash_password
    from src.core.database import async_session_factory
    from src.users.models import User, UserRole
    from src.users.service import UserService

    async with async_session_factory() as session:
        user_service = UserService(session)

        # Check if user already exists
        existing = await user_service.get_by_email(email)
        if existing:
            if existing.role == UserRole.ADMIN:
                print(f"⚠️  Admin user '{email}' already exists. No action taken.")
            else:
                print(
                    f"⚠️  User '{email}' already exists with role '{existing.role}'. "
                    f"Update their role via SQLAdmin or the database directly."
                )
            return

        # Hash password and create user
        hashed = await hash_password(password)
        user = User(
            email=email,
            password=hashed,
            display_name=display_name,
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.commit()

        print(f"✅ Admin user created successfully!")
        print(f"   Email:        {email}")
        print(f"   Display Name: {display_name}")
        print(f"   Role:         admin")
        print(f"   ID:           {user.id}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create an admin user for the Learning Platform.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.users.management.create_admin \\
      --email admin@example.com \\
      --password Admin1234!

  python -m src.users.management.create_admin \\
      --email admin@example.com \\
      --password Admin1234! \\
      --display-name "Super Admin"
        """,
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address for the admin user",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Password for the admin user (will be hashed with bcrypt)",
    )
    parser.add_argument(
        "--display-name",
        default="Admin",
        help="Display name for the admin user (default: 'Admin')",
    )

    args = parser.parse_args()

    # Validate password length
    if len(args.password) < 8:
        print("❌ Error: Password must be at least 8 characters long.")
        sys.exit(1)

    asyncio.run(create_admin(args.email, args.password, args.display_name))


if __name__ == "__main__":
    main()
