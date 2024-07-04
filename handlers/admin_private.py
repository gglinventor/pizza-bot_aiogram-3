from aiogram import F, Bot, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_filter import ChatTypeFilter, Is_Administrator
from keyboards.inline_kb import simpe_inline_keyboard
from keyboards.reply_kb import simple_keyboard
from database.orm_query import orm_update_banner, orm_get_info_pages, orm_get_banner, orm_add_product, orm_get_product, orm_get_products, orm_update_product, orm_delete_product, orm_add_question, orm_get_question, orm_get_questions, orm_update_question, orm_delete_question


admin_private_router = Router()
admin_private_router.message.filter(ChatTypeFilter(['private']), Is_Administrator())


################# Микро FSM для загрузки (изменения) баннеров ############################

class AddBanner(StatesGroup):
    name = State()
    image = State()
    description = State()
    
    
@admin_private_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.answer('Выберите название баннера', reply_markup=simpe_inline_keyboard(buttons={page.name: f'banner_{page.name}' for page in await orm_get_info_pages(session)}, sizes=(2,2,2)))
    await state.set_state(AddBanner.name)
    
    
@admin_private_router.message(StateFilter('*'), Command('отмена', 'Отмена'))
@admin_private_router.message(StateFilter('*'), F.text.casefold() == 'отмена')
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_replace:
        AddProduct.product_for_replace = None
    elif AddQuestion.question_for_replace:
        AddQuestion.question_for_replace = None

    await state.clear()
    await message.answer('Действия отменены', reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))


@admin_private_router.callback_query(AddBanner.name, F.data.startswith('banner_'))
async def add_banner_name(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    banner_name = callback.data.split('_')[-1]
    banner = await orm_get_banner(session, banner_name)
    await state.update_data(id=banner.id)
    await state.update_data(name=banner_name)
    await callback.message.answer('Отправьте фотографию баннера', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddBanner.image)


@admin_private_router.message(AddBanner.image, F.photo)
async def add_banner_image(message: types.Message, state: FSMContext):
    await state.update_data(image=message.photo[-1].file_id)
    await message.answer('Отправьте описание баннера')
    await state.set_state(AddBanner.description)


@admin_private_router.message(AddBanner.description, F.text)
async def add_banner_description(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(description=message.text)
    
    data = await state.get_data()    
    await orm_update_banner(session, data['name'], data)
    await message.answer(text=f'Баннер <strong>{data["name"]}</strong> добавлен (изменён)', reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))    

    await state.clear()
    
   
######################################### НАЧАЛО РАБОТЫ С АДМИНКОЙ #########################################

################# FSM для добавления/изменения/удаления товаров ############################################

class AddProduct(StatesGroup):
    image = State()
    name = State()
    info = State()
    price = State()
    valute = State()
    category = State()
    comment = State()

    product_for_replace = None
    
    texts = {'AddProduct:image': 'Отправьте заново картинку',
             'AddProduct:name': 'Введите заново название',
             'AddProduct:info': 'Введите заново описание',
             'AddProduct:price': 'Введите заново цену (без валюты)',
             'AddProduct:valute': 'Выберите заново валюту',
             'AddProduct:category': 'Выберите заново категорию товара',
             'AddProduct:comment': 'Введите заново комментарий',
        }

@admin_private_router.message(Command('admin_go'))
async def admin_command_go(message: types.Message, bot: Bot):
    await message.answer(f'Здравствуйте @{message.from_user.username}', reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))
    keyboard = None
    if message.from_user.id not in bot.not_instruction:
        keyboard = simpe_inline_keyboard(buttons={'Инструкция':'instruction',}, sizes=(1,))
    await message.answer('Выберите действие', reply_markup=keyboard)


@admin_private_router.callback_query(F.data.startswith('instruction'))
async def instruction(callback: types.CallbackQuery):
    await callback.message.answer('Инструкция для администраторов:\n\nЕсли вы хотите взаимодействовать с меню, нажмите кнопку "Добавить/Изменить меню"\nДалее вы сможете добавить товар кнопкой "Добавить товар". Внимательно следуйте указаниям бота! Для отмены ввода отправьте сообщение "отмена", а вернуться на один шаг назад можно при помощи сообщения "назад"\nЧтобы изменить или удалить товар, нажмите кнопку "Ассортимент" и, выбрав категорию товара, нажав на нужную кнопку, можете изменить товар (тут также работают сообщения "отмена" и "назад") или удалить его\n\nЕсли хотите взаимодействовать с частыми вопросами, нажмите кнопку "Добавить/Изменить частые вопросы". Тут работает всё также, как и в меню, но нет сообщения "назад"\n\nЕсли хотите изменить или добавить баннеры (разницы нет, так как баннеры по умолчанию есть, их нельзя удалить, лишь можно только изменить) нажмите кнопку "Добавить/Изменить баннер". Далее выберите нужный баннер нажав на соответствующую кнопку:\nmain - первая (главная) страница инлайн-меню\nabout - страница "О нас"\npayment - страница "Оплата"\nshipping - страница "Доставка"\ncatalog - страница с категориями товаров\ncart - страница корзины, в которой ничего нет\nquestion - страница "Вопросы"\nanswer - страница с ответом на вопрос (текст этого баннера не учитывается, но ввести его нужно)\n\nЕсли хотите увидеть прочие настройки, нажмите кнопку "Прочее"\nЧтобы изменить категории, нажмите кнопку "Названия категорий". Выберите нужную категорию и измените её название (работает только сообщение "отмена")\nЧтобы увидеть прочие настройки, нажмите кнопку "Настройки" и нажимайте на нужные вам кнопки')
    await callback.answer()
    

@admin_private_router.message(F.text == 'Добавить/Изменить меню')
async def start_menu(message: types.Message):
    await message.answer('Выберите тип взаимодействия', reply_markup=simple_keyboard(buttons=['Добавить товар', 'Ассортимент'], sizes=(1,1)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))


@admin_private_router.message(F.text == 'Ассортимент')
async def assortment(message: types.Message, bot: Bot):
    await message.answer('Выберите категорию', reply_markup=simpe_inline_keyboard(buttons={category: f'category_{bot.food_category.index(category) + 1}' for category in bot.food_category}, sizes=(1, 2)))
    

@admin_private_router.callback_query(F.data.startswith('category_'))    
async def list_of_products(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    category_id = int(callback.data.split('_')[-1])
    for product in await orm_get_products(session, category_id):
        text = f'<strong>{product.name}</strong>\n{product.info}\nСтоимость: {round(product.price, 2)} {product.valute}'
        if product.comment != None and product.comment != '':
            text += f'\n{product.comment}'
        await callback.message.answer_photo(product.image, caption=text,
            reply_markup=simpe_inline_keyboard(buttons={'Изменить': f'replace_{product.id}', 'Удалить': f'delete_{product.id}'}, sizes=(2,)))    
    
    await callback.answer()
    await callback.message.answer(f'Список товаров категории {bot.food_category[category_id - 1]}')
    

@admin_private_router.callback_query(StateFilter(None), F.data.startswith('replace_'))
async def replace_product(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    product_id = callback.data.split('_')[-1]
    product_for_replace = await orm_get_product(session, int(product_id))
    
    AddProduct.product_for_replace = product_for_replace
    await callback.answer()
    await callback.message.answer('Чтобы оставить прошлые характеристики, введите "."\nОтправьте новую картинку товара', reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(id=AddProduct.product_for_replace.id)
    await state.set_state(AddProduct.image)
    

@admin_private_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split('_')[-1]
    product = await orm_delete_product(session, int(product_id))
    await callback.answer(f'Товар {product.name} удалён')
    await callback.message.answer(f'Товар <strong>{product.name}</strong> удалён')


@admin_private_router.message(F.text == 'Добавить товар')
async def add_product(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await message.answer('Отправьте картинку товара', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddProduct.image)
    next_id = 0
    for num_category in range(len(bot.food_category)):
        result = await orm_get_products(session, num_category + 1)
        next_id += len(result)
    await state.update_data(id=next_id + 1)


@admin_private_router.message(StateFilter('*'), Command('назад', 'Назад'))
@admin_private_router.message(StateFilter('*'), F.text.casefold() == 'назад')
async def back_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AddProduct.image:
        await message.answer('Предыдущего шага нет!')
        return
    
    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f'Вы вернулись к прошлому шагу\n{AddProduct.texts[previous.state]}')
            return
            
        previous = step     


@admin_private_router.message(AddProduct.image, or_f(F.photo, F.text == '.'))
async def add_image(message: types.Message, state: FSMContext):
    if message.text == '.' and AddProduct.product_for_replace:
        await state.update_data(image=AddProduct.product_for_replace.image)
    elif message.text == '.' and AddProduct.product_for_replace == None:
        await message.reply('Отправьте изображение!')
        return
    else:
        await state.update_data(image=message.photo[-1].file_id)
    await message.answer('Введите название товара')
    await state.set_state(AddProduct.name)
    

@admin_private_router.message(AddProduct.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    if message.text == '.' and AddProduct.product_for_replace:
        await state.update_data(name=AddProduct.product_for_replace.name)
    elif message.text == '.' and AddProduct.product_for_replace == None:
        await message.reply('Отправьте название!')
        return
    else:
        await state.update_data(name=message.text)
    await message.answer('Введите описание товара')
    await state.set_state(AddProduct.info)
    

@admin_private_router.message(AddProduct.info, F.text)
async def add_information(message: types.Message, state: FSMContext):
    if message.text == '.' and AddProduct.product_for_replace:
        await state.update_data(info=AddProduct.product_for_replace.info)
    elif message.text == '.' and AddProduct.product_for_replace == None:
        await message.reply('Отправьте описание товара!')
        return
    else:
        await state.update_data(info=message.text)
    await message.answer('Введите цену товара (без валюты)')
    await state.set_state(AddProduct.price)
    
    
@admin_private_router.message(AddProduct.price, F.text)
async def add_price(message: types.Message, state: FSMContext):
    if message.text == '.' and AddProduct.product_for_replace:
        await state.update_data(price=AddProduct.product_for_replace.price)
    elif message.text == '.' and AddProduct.product_for_replace == None:
        await message.reply('Отправьте цену товара!')
        return
    else:
        if {i for i in message.text}.intersection({'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', ','}) != {i for i in message.text}:
            await message.answer('Введите число!\nПример: 159.99')
            return
        
        await state.update_data(price=round(float(message.text.replace(',', '.')), 2))
    await message.answer("Выберите валюту", reply_markup=simpe_inline_keyboard(buttons={'RUB':'valute_RUB', 'USD':'valute_USD', 'BYN':'valute_BYN'}, sizes=(1, 2)))
    await state.set_state(AddProduct.valute)
    

@admin_private_router.callback_query(AddProduct.valute, F.data.startswith('valute_'))
async def add_valute(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await state.update_data(valute=callback.data.split('_')[-1])
    await callback.message.answer('Выберите категорию товара', reply_markup=simpe_inline_keyboard(buttons={category: f'add_category_{bot.food_category.index(category) + 1}' for category in bot.food_category}, sizes=(1, 2)))
    await state.set_state(AddProduct.category)
        

@admin_private_router.callback_query(AddProduct.category, F.data.startswith('add_category_'))
async def add_category(callback: types.CallbackQuery, state: FSMContext , session: AsyncSession):
    await callback.answer()
    await state.update_data(category_id=int(callback.data.split('_')[-1]))
    await callback.message.answer('Введите комментарий\n(не обязательно, если не хотите писать, то отправьте "не хочу")')
    await state.set_state(AddProduct.comment)
    
    
@admin_private_router.message(AddProduct.comment, F.text)
async def add_comment(message: types.Message, session: AsyncSession, state: FSMContext):
    if message.text == '.' and AddProduct.product_for_replace:
        await state.update_data(comment=AddProduct.product_for_replace.comment)
    elif message.text == '.' and AddProduct.product_for_replace == None:
        await message.reply('Отправьте комментарий для товара!')
        return
    elif message.text.lower() == 'не хочу':
        await state.update_data(comment=None)
    elif message.text.lower() != 'не хочу':
        await state.update_data(comment=message.text)

    data = await state.get_data()
    
    if AddProduct.product_for_replace:
        await orm_update_product(session, AddProduct.product_for_replace.id, data)
        text = f'Товар <strong>{AddProduct.product_for_replace.name}</strong> изменён'
    else:
        await orm_add_product(session, data)
        text = f"Товар <strong>{data['name']}</strong> добавлен"
    await message.answer(text=text, reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))
    await state.clear()
    
    AddProduct.product_for_replace = None


################# Микро FSM для добавления/изменения/удаления частых вопросов ############################

class AddQuestion(StatesGroup):
    name = State()
    info = State()
    
    question_for_replace = None
    

@admin_private_router.message(F.text == 'Добавить/Изменить частые вопросы')
async def add_question(message: types.Message):
    await message.answer('Выберите тип взаимодействия', reply_markup=simple_keyboard(buttons=['Добавить вопрос', 'Список вопросов'], sizes=(1,1)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))


@admin_private_router.message(F.text == 'Список вопросов')
async def list_of_question(message: types.Message, session: AsyncSession):
    for question in await orm_get_questions(session):
        await message.answer(f'{question.name}\n\n{question.info}', reply_markup=simpe_inline_keyboard(buttons={'Изменить': f'question_replace_{question.id}', 'Удалить': f'question_delete_{question.id}'}, sizes=(2,)))
    await message.answer('Вот все вопросы ⬆️')


@admin_private_router.callback_query(F.data.startswith('question_replace_'))
async def replace_question(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    question_id = int(callback.data.split('_')[-1])
    question_for_replace = await orm_get_question(session, question_id)
    
    AddQuestion.question_for_replace = question_for_replace
    await callback.answer()
    await callback.message.answer('Чтобы оставить прошлые характеристики, введите "."\nОтправьте название вопроса', reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(id=AddQuestion.question_for_replace.id)
    await state.set_state(AddQuestion.name)


@admin_private_router.callback_query(F.data.startswith('question_delete_'))
async def delete_question(callback: types.CallbackQuery, session: AsyncSession):
    question_id = int(callback.data.split('_')[-1])
    question = await orm_delete_question(session, question_id)
    await callback.answer(f'Вопрос {question.name} удалён')
    await callback.message.answer(f'Вопрос <strong>{question.name}</strong> удалён')


@admin_private_router.message(F.text == 'Добавить вопрос')
async def start_question(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.answer('Введите название вопроса', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddQuestion.name)
    next_id = await orm_get_questions(session)
    await state.update_data(id=len(next_id) + 1)


@admin_private_router.message(AddQuestion.name, F.text)
async def add_question_name(message: types.Message, state: FSMContext):
    if message.text == '.' and AddQuestion.question_for_replace:
        await state.update_data(name=AddQuestion.question_for_replace.name)
    elif message.text == '.' and AddQuestion.question_for_replace == None:
        await message.reply('Отправьте название!')
        return
    else:
        await state.update_data(name=message.text)
    await message.answer('Введите ответ на вопрос')
    await state.set_state(AddQuestion.info)


@admin_private_router.message(AddQuestion.info, F.text)
async def add_question_information(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == '.' and AddQuestion.question_for_replace:
        await state.update_data(info=AddQuestion.question_for_replace.info)
    elif message.text == '.' and AddQuestion.question_for_replace == None:
        await message.reply('Отправьте описание!')
        return
    else:
        await state.update_data(info=message.text)

    data = await state.get_data()
    
    if AddQuestion.question_for_replace:
        await orm_update_question(session, AddQuestion.question_for_replace.id, data)
        text = f'Вопрос <strong>{AddQuestion.question_for_replace.name}</strong> изменён'
    else:
        await orm_add_question(session, data)
        text = f"Вопрос <strong>{data['name']}</strong> добавлен"
    await message.answer(text=text, reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))
    await state.clear()
    
    AddQuestion.question_for_replace = None


################# Прочие возможности ##################################################

@admin_private_router.message(F.text == 'Прочее')
async def choice_settings(message: types.Message):
    await message.answer('Выберите тип взаимодействия', reply_markup=simple_keyboard(buttons=['Названия категорий', 'Настройки'], sizes=(1,1)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))


########### Изменение названий категорий ##########################

class NamesCategories(StatesGroup):
    name = State()


@admin_private_router.message(F.text == 'Названия категорий')
async def names_categories(message: types.Message, bot: Bot):
    await message.answer('Выберите категорию', reply_markup=simpe_inline_keyboard(buttons={category: f'name_category_{bot.food_category.index(category)}' for category in bot.food_category}, sizes=(1,2)))


@admin_private_router.callback_query(F.data.startswith('name_category_'))
async def choice_category(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await callback.message.answer('Отправьте новое название категории', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(NamesCategories.name)
    index = int(callback.data.split('_')[-1])
    await state.update_data(old_name=bot.food_category[index])
    await state.update_data(index=index)


@admin_private_router.message(NamesCategories.name, F.text)
async def replace_name_category(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(name=message.text)
    data = await state.get_data()
    for category in bot.food_category:
        if category == data['old_name']:
            bot.food_category[data['index']] = data['name']
    await message.answer(f'Категория <strong>{data["old_name"]}</strong> переименована', reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))
    await state.clear()


########### Изменение настроек ####################################

@admin_private_router.message(F.text == 'Настройки')
async def settings(message: types.Message):
    await message.answer('Выберите действие', reply_markup=simpe_inline_keyboard(buttons={'Вкл/выкл инструкцию': f'setting_instruction_{message.from_user.id}', }, sizes=(1,)))


@admin_private_router.callback_query(F.data.startswith('setting_instruction_'))
async def on_off_instruction(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    id = int(callback.data.split('_')[-1])
    
    if id not in bot.not_instruction:
        bot.not_instruction.append(id)
    else:
        bot.not_instruction.remove(id)
    await callback.message.answer('Действие выполнено', reply_markup=simple_keyboard(buttons=['Добавить/Изменить меню', 'Добавить/Изменить частые вопросы', 'Добавить/Изменить баннер', 'Прочее'], sizes=(1,1,2)).as_markup(resize_keyboard=True, input_field_placeholder='Что вы хотите сделать?'))
    