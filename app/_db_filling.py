import asyncio
from datetime import datetime, timedelta

from db.base import get_session
from db.crud import create_user, create_library, create_ban
from faker import Faker
from patisson_request.service_routes import BooksRoute
from patisson_request.graphql.queries import QBook
from config import SelfService
from db.models import User, Library, Ban
from sqlalchemy.future import select
import random

fake = Faker()

async def _create_users(count: int):
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


async def _create_library():
    qbooks = await SelfService.post_request(
        *-BooksRoute.graphql.books(fields=[QBook.id], limit=0) 
    )
    async with get_session() as session:
        users_stmt = await session.execute(select(User.id))
        users = users_stmt.scalars().unique().all()
    
    tasks = []
    for user in users:
        for _ in range(random.randint(1, 10)):
            async with get_session() as session:
                tasks.append(create_library(
                    session, book_id=random.choice(qbooks.body.data.books).id, 
                    user_id=user, status=Library.Status(random.randint(0, 2)))
                                )
    await asyncio.gather(*tasks)
        

async def _create_ban():
    async with get_session() as session:
        users_stmt = await session.execute(select(User.id))
        users = users_stmt.scalars().unique().all()
    
    tasks = []
    for user in random.choices(users, k=int(len(users)/10)):
        async with get_session() as session:
            tasks.append(create_ban(
                session, user_id=user, reason=Ban.Reason(random.randint(0, 0)), 
                comment=fake.text(), end_date=(datetime.now() 
                    + timedelta(days=random.randint(0, 30))))
                         )
    await asyncio.gather(*tasks)
        

async def main(users_count: int):
    await _create_users(count=users_count)
    await _create_library()
    await _create_ban()
    
    
if __name__ == "__main__":
    create_users_count = 100
    asyncio.run(main(
        users_count=create_users_count
    ))