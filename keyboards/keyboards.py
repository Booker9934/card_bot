from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать карточку")],
            [KeyboardButton(text="Начать обучение")],
            [KeyboardButton(text="Показать карты")],
            [KeyboardButton(text="Удалить карточку")]
        ]
    )

def back_info() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Посмотреть обратную сторону", callback_data="watch_back")]
        ]
    )

async def builder_markup(cards):
    """
    Создают клавиатуру из групп
    """

    builder = InlineKeyboardBuilder()
    groups = []

    for card in cards:
        if card.group not in groups:
            groups.append(card.group)
            builder.button(text=f'{card.group}', callback_data=f"Группа {card.group}")

    builder.button(text="Все группы", callback_data='All')
    builder.adjust(1)

    return builder.as_markup()

back_from_groups_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться", callback_data='back')]
    ]
)
