import asyncio
import logging
import sys
from os import getenv
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    CallbackQuery
)

from utils import (loc_keyboard, age_keyboard, khakas_level_keyboard, task_type_keyboard,
                   prepare_sent_for_translation, skip_change_keyboard, to_correct_keyboard,
                   prepare_photo, prepare_sent_text_for_align)

TOKEN = getenv("BOT_TOKEN")

form_router = Router()


class Form(StatesGroup):
    name = State()
    location = State()
    age = State()
    khakas_level = State()
    task_type = State()

    input_sent = State()
    user_sent = State()

    to_correct = State()

    photo = State()
    text_from_photo = State()

    sent1_align = State()
    text2_align = State()
    sent2_align = State()


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        "Привет! Данный бот содержит задания по подготовке корпуса параллельных текстов на хакасском и русском языках. "
        "Перед выполнением заданий пройдите, пожалуйста, короткую регистрацию.")

    await message.answer("Как Вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.location)
    await message.answer(
        f"Приятно познакомиться, {html.quote(message.text)}!\nИз какого Вы города/района?",
        reply_markup=loc_keyboard
    )


@form_router.message(Form.location, F.text.casefold() == "другое")
async def process_location_drugoe(message: Message, state: FSMContext) -> None:
    await message.reply("Введите название Вашего населенного пункта", reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.location)
async def process_location(message: Message, state: FSMContext) -> None:
    await state.update_data(location=message.text)
    await state.set_state(Form.age)
    await message.answer(f"Сколько Вам лет?", reply_markup=age_keyboard)


@form_router.message(Form.age)
async def process_age(message: Message, state: FSMContext) -> None:
    await state.update_data(age=message.text)
    await state.set_state(Form.khakas_level)
    await message.answer(
        "Как хорошо Вы знаете хакасский язык?",
        reply_markup=khakas_level_keyboard,
    )


@form_router.message(Form.khakas_level)
async def process_khakas_level(message: Message, state: FSMContext) -> None:
    await state.update_data(khakas_level=message.text)
    await choose_task_type(message=message, state=state)


async def choose_task_type(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.task_type)
    await message.answer(
        "Выберите тип заданий",
        reply_markup=task_type_keyboard,
    )


@form_router.message(Form.task_type)
async def process_task_type(message: Message, state: FSMContext, to_update: bool = True) -> None:
    if to_update:
        await state.update_data(task_type=message.text)

    data = await state.get_data()

    task_type = data['task_type']
    if task_type == 'Перевод с хакасского языка на русский':
        await translate_khakas_sent(message=message, state=state)
    elif task_type == 'Набор текста с фотографии':
        await type_text_from_photo(message=message, state=state)
    elif task_type == 'Выравнивание текстов на 2-х языках':
        await align_sent_text(message=message, state=state)
    else:
        await choose_task_type(message=message, state=state)


# await message.answer(f"Name: {data['name']}\n"
#                      f"Location: {data['location']}\n"
#                      f"Age: {data['age']}\n"
#                      f"Khakas level: {data['khakas_level']}\n"
#                      f"Current task type: {data['task_type']}")
async def translate_khakas_sent(message: Message, state: FSMContext,
                                from_skip: bool = False, to_correct: bool = False) -> None:
    data = await state.get_data()

    # allow user to correct his answer
    if to_correct:
        input_sent = data['input_sent']
    else:
        input_sent = prepare_sent_for_translation(language='khakas')
        await state.update_data(input_sent=input_sent)

    await state.set_state(Form.user_sent)

    # if user skip, just change sentence
    if from_skip:
        await message.edit_text(f'*{input_sent}*', reply_markup=skip_change_keyboard, parse_mode='MarkdownV2')
    else:
        await message.answer('Переведите с хакасского языка на русский:', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'*{input_sent}*', reply_markup=skip_change_keyboard, parse_mode='MarkdownV2')


async def type_text_from_photo(message: Message, state: FSMContext,
                               from_skip: bool = False, to_correct: bool = False) -> None:
    data = await state.get_data()

    # allow user to correct his answer
    if to_correct:
        photo = data['photo']
    else:
        photo = prepare_photo()
        await state.update_data(photo=photo)

    await state.set_state(Form.text_from_photo)

    # if user skip, just change sentence
    if from_skip:
        # todo: can we edit photo?
        await message.answer('Введите текст с фотографии:', reply_markup=ReplyKeyboardRemove())
        await message.answer_photo(photo, reply_markup=skip_change_keyboard, parse_mode='MarkdownV2')
    else:
        await message.answer('Введите текст с фотографии:', reply_markup=ReplyKeyboardRemove())
        await message.answer_photo(photo, reply_markup=skip_change_keyboard, parse_mode='MarkdownV2')


async def align_sent_text(message: Message, state: FSMContext,
                          from_skip: bool = False, to_correct: bool = False) -> None:
    data = await state.get_data()

    # allow user to correct his answer
    if to_correct:
        sent1_align = data['sent1_align']
        text2_align = data['text2_align']
    else:
        sent1_align, text2_align = prepare_sent_text_for_align()
        await state.update_data(sent1_align=sent1_align, text2_align=text2_align)

    await state.set_state(Form.sent2_align)

    # if user skip, just change sentence
    if from_skip:
        await message.edit_text(f'*{sent1_align}*\n\n\n{text2_align}',
                                reply_markup=skip_change_keyboard, parse_mode='MarkdownV2')
    else:
        await message.answer('Найдите перевод хакасского предложения в тексте:', reply_markup=ReplyKeyboardRemove())
        await message.answer(f'*{sent1_align}*\n\n\n{text2_align}',
                             reply_markup=skip_change_keyboard, parse_mode='MarkdownV2')


@form_router.message(Form.user_sent)
async def process_user_sent(message: Message, state: FSMContext) -> None:
    user_sent = message.text
    data = await state.update_data(user_sent=user_sent)
    input_sent = data['input_sent']

    await state.set_state(Form.to_correct)
    await message.answer(f'Предложение:\n*{input_sent}*\n\nВаш перевод:\n*{user_sent}*',
                         reply_markup=to_correct_keyboard, parse_mode='MarkdownV2')


@form_router.message(Form.text_from_photo)
async def process_text_from_photo(message: Message, state: FSMContext) -> None:
    text_from_photo = message.text
    data = await state.update_data(text_from_photo=text_from_photo)
    photo = data['photo']

    await state.set_state(Form.to_correct)

    await message.answer_photo(photo, caption=f'Ваш ответ:\n*{text_from_photo}*',
                               reply_markup=to_correct_keyboard, parse_mode='MarkdownV2')


@form_router.message(Form.sent2_align)
async def process_user_sent(message: Message, state: FSMContext) -> None:
    sent2_align = message.text
    data = await state.update_data(sent2_align=sent2_align)
    sent1_align = data['sent1_align']

    await state.set_state(Form.to_correct)
    await message.answer(f'Предложение:\n*{sent1_align}*\n\nПеревод:\n*{sent2_align}*',
                         reply_markup=to_correct_keyboard, parse_mode='MarkdownV2')


@form_router.message(Form.to_correct)
async def process_to_correct(message: Message, state: FSMContext) -> None:
    if message.text == 'всё верно':
        await process_task_type(message=message, state=state, to_update=False)
    elif message.text == 'исправить':
        data = await state.get_data()
        task_type = data['task_type']

        if task_type == 'Перевод с хакасского языка на русский':
            await translate_khakas_sent(message=message, state=state, to_correct=True)
        elif task_type == 'Набор текста с фотографии':
            await type_text_from_photo(message=message, state=state, to_correct=True)
        elif task_type == 'Выравнивание текстов на 2-х языках':
            await align_sent_text(message=message, state=state, to_correct=True)
        else:
            await choose_task_type(message=message, state=state)

    else:
        await message.answer('not supported in process_to_correct')


@form_router.callback_query(F.data == 'skip_task')
async def process_skip_task(callback_query: CallbackQuery, state: FSMContext) -> None:
    message = callback_query.message
    data = await state.get_data()

    if 'task_type' not in data:
        await choose_task_type(message=message, state=state)
    else:
        task_type = data['task_type']

        if task_type == 'Перевод с хакасского языка на русский':
            await translate_khakas_sent(message=message, state=state, from_skip=True)
        elif task_type == 'Набор текста с фотографии':
            await type_text_from_photo(message=message, state=state, from_skip=True)
        elif task_type == 'Выравнивание текстов на 2-х языках':
            await align_sent_text(message=message, state=state, from_skip=True)
        else:
            await choose_task_type(message=message, state=state)


@form_router.callback_query(F.data == 'change_task_type')
async def process_change_task_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    message = callback_query.message

    await choose_task_type(message=message, state=state)


async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())