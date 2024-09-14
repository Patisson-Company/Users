import asyncio

from db.base import get_session
from db.crud import create_user
from faker import Faker


async def create_users(count: int):
    fake = Faker()
    tasks = []
    for _ in range(count):
        async with get_session() as session:
            tasks.append(create_user(
                session=session,
                username=fake.user_name(),
                password='QweQwe123!',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                about=fake.text(),
                role='_'
            ))
    await asyncio.gather(*tasks)


async def main(users_count: int):
    await create_users(count=users_count)
    
    
if __name__ == "__main__":
    create_users_count = 100
    asyncio.run(main(
        users_count=create_users_count
    ))