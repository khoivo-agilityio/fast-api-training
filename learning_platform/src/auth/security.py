"""
Password Hashing — bcrypt (async, non-blocking).

passlib's bcrypt wrapper is incompatible with bcrypt >= 4.1.
Using bcrypt directly avoids this issue (see gotchas.md #1).

These functions use run_in_executor to offload CPU-bound bcrypt operations
to a thread pool, preventing event loop blocking during password hashing
(~100ms per call). This addresses code review Issue #2:
"Should apply async to these functions?"

Answer: Yes — but simply adding `async def` without offloading is wrong.
bcrypt is CPU-bound, so we use asyncio.get_running_loop().run_in_executor()
to run the blocking work in a thread pool.
"""

import asyncio
import functools

import bcrypt


async def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt (non-blocking).

    Offloads the CPU-bound bcrypt work to a thread pool executor
    so the async event loop is not blocked (~100ms per hash).
    """
    loop = asyncio.get_running_loop()
    hashed = await loop.run_in_executor(
        None,
        functools.partial(
            bcrypt.hashpw,
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ),
    )
    return hashed.decode("utf-8")


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash (non-blocking).

    Offloads to a thread pool executor to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(
            bcrypt.checkpw,
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        ),
    )
