from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types

def simple_keyboard(*, buttons: list[str], sizes: tuple[int]):
    keyboard = ReplyKeyboardBuilder()
    
    for text in buttons:
        keyboard.add(KeyboardButton(text=text))
        
    return keyboard.adjust(*sizes)
        
'''
keyboard_admin = ReplyKeyboardBuilder().add(
    KeyboardButton(text='Добавить/Изменить меню'),
    KeyboardButton(text='Добавить/Изменить частые вопросы'),
    KeyboardButton(text='Прочее')
)

keyboard_admin_2 = ReplyKeyboardBuilder().add(
    KeyboardButton(text='Добавить товар'),
    KeyboardButton(text='Ассортимент'),
    KeyboardButton(text='До
    бавить/Изменить баннер')
)

keyboard_admin_2.adjust(1, 1, 1)

'''