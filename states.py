from aiogram.fsm.state import State, StatesGroup

# FSM для создания карточки
class CreateCardStates(StatesGroup):
    waiting_for_front = State()
    waiting_for_back = State()
    waiting_for_group = State()
    waiting_for_photo_id = State()

# FSM для ожидания ввода обратной стороны
class CardState(StatesGroup):
    translate = State()

# FSM для удаления карточки
class CardDelete(StatesGroup):
    delete = State()