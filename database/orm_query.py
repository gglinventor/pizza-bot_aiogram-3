from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Banner, Product, Question, User, Cart

############### Работа с баннерами ####################################################

async def orm_update_banner(session: AsyncSession, banner_name: str, data: dict):
    query = update(Banner).where(Banner.name == banner_name).values(
        id=int(data['id']),
        name=data['name'],
        image=data['image'],
        description=data['description'],
    )
    await session.execute(query)
    await session.commit()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_banner(session: AsyncSession, banner_name: str):
    query = select(Banner).where(Banner.name == banner_name)
    result = await session.execute(query)
    return result.scalar()


############ Админка: добавить/получить/изменить/удалить товар ########################

async def orm_add_product(session: AsyncSession, data: dict):
    card = Product(
        id=int(data['id']),
        image=data['image'],
        name=data['name'],
        info=data['info'],
        price=float(data['price']),
        valute=data['valute'],
        category_id=int(data['category_id']),
        comment=data['comment'],
    )
    session.add(card)
    await session.commit()  


async def orm_get_product(session: AsyncSession, product_id: int):
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()
    

async def orm_get_products(session: AsyncSession, category_id: int):
    query = select(Product).where(Product.category_id == category_id)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_product(session: AsyncSession, product_id: int, data: dict):
    query_card = update(Product).where(Product.id == product_id).values(
        id=int(data['id']),
        image=data['image'],
        name=data['name'],
        info=data['info'],
        price=float(data['price']),
        valute=data['valute'],
        category_id=int(data['category_id']),
        comment=data['comment'],
    )
    await session.execute(query_card)
    await session.commit()


async def orm_delete_product(session: AsyncSession, product_id: int):
    query_name = select(Product).where(Product.id == product_id)
    query_delete = delete(Product).where(Product.id == product_id)
    
    result = await session.execute(query_name)
    await session.execute(query_delete)
    await session.commit()
    
    return result.scalar()


############### Работа с частыми вопросами ############################################

async def orm_add_question(session: AsyncSession, data: dict):
    question = Question(
        id=int(data['id']),
        name=data['name'],
        info=data['info'],
    )
    session.add(question)
    await session.commit()


async def orm_get_question(session: AsyncSession, question_id: int):
    query = select(Question).where(Question.id == question_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_questions(session: AsyncSession):
    query = select(Question)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_question(session: AsyncSession, question_id: int, data: dict):
    question_query = update(Question).where(Question.id == question_id).values(
        id=int(data['id']),
        name=data['name'],
        info=data['info'], 
    )
    await session.execute(question_query)
    await session.commit()


async def orm_delete_question(session: AsyncSession, question_id: int):
    query_name = select(Question).where(Question.id == question_id)
    query_delete = delete(Question).where(Question.id == question_id)
    
    result = await session.execute(query_name)
    await session.execute(query_delete)
    await session.commit()
    
    return result.scalar()


############### Работа с пользователем ################################################

async def orm_add_user(session: AsyncSession, id: int, user_id: int, username: str, phone: str | None = None):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    
    if result.first() is None:
        session.add(
            User(
                id=id,
                user_id=user_id,
                username=username,
                phone=phone,
                )
            )
        await session.commit()


async def orm_get_users(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()


############### Работа с корзинами ####################################################

async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int, id: int | None = None):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return
    else:
        session.add(
            Cart(
                id=id,
                user_id=user_id,
                product_id=product_id,
                quantity=1
                )
            )
        await session.commit()


async def orm_get_carts(session: AsyncSession):
    query = select(Cart)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_user_carts(session: AsyncSession, user_id: int):
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.product), joinedload(Cart.user))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()
    
async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    result = await session.execute(query)
    result = result.scalar()
    
    if not result:
        return
    elif result.quantity > 1:
        result.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False
    