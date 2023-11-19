import asyncio
import logging
import sys
from os import getenv
from typing import Any, Dict, List

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

from utils import (loc_keyboard, age_keyboard, khakas_level_keyboard,
                   prepare_sent_for_translation, skip_change_keyboard, to_correct_keyboard,
                   prepare_photo, prepare_sent_text_for_align, save_translation, save_photo_text,
                   save_user_info, continue_keyboard, skip_organization_keyboard, save_aligned_sents)

TOKEN = getenv("BOT_TOKEN")

form_router = Router()


class Form(StatesGroup):
    name = State()
    location = State()
    age = State()
    khakas_level = State()
    organization = State()

    task_type = State()

    input_sent = State()
    user_sent = State()

    to_correct = State()

    photo_path = State()
    photo = State()
    text_from_photo = State()

    sent1_align = State()
    text2_align = State()
    sent2_align = State()

    available_align = State()
    available_photo = State()
    available_translate = State()


@form_router.message(CommandStart())
@form_router.message(F.text.casefold() == "start")
@form_router.message(Command("register_again"))
@form_router.message(F.text.casefold() == "register_again")
async def command_start(message: Message, state: FSMContext) -> None:
    text = message.text
    await state.clear()
    if text == '/start' or text == 'start':
        await message.answer('Изеннер!\n'
                             'Вас приветствует чат-бот для выполнения заданий в рамках акции '
                             '"Обучаем нейросеть хакасскому языку!".\n\n'
                             'Информация об акции: https://t.me/translate_khakas/5\n'
                             'Подробная инструкция: https://t.me/translate_khakas/6\n\n'
                             'Чат для вопросов: @translate_khakas_chat',
                             disable_web_page_preview=True)
        await message.answer('Перед выполнением заданий пройдите, пожалуйста, короткую регистрацию.',
                             disable_web_page_preview=True)

    await state.set_state(Form.name)
    await message.answer("Как Вас зовут?", reply_markup=ReplyKeyboardRemove(), parse_mode="MarkdownV2")


@form_router.message(Command("help"))
@form_router.message(F.text.casefold() == "help")
async def process_help(message: Message, state: FSMContext) -> None:
    await message.answer('Подробная инструкция: https://t.me/translate_khakas/6\n\n'
                         'Чат для вопросов: @translate_khakas_chat',
                         reply_markup=continue_keyboard,
                         disable_web_page_preview=True)


@form_router.message(Command("change_task_type"))
@form_router.message(F.text.casefold() == "change_task_type")
@form_router.message(F.text.casefold() == "продолжить")
async def process_help1(message: Message, state: FSMContext) -> None:
    await choose_task_type(message=message, state=state)


@form_router.callback_query(F.data == 'change_task_type')
async def process_change_task_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    message = callback_query.message
    await choose_task_type(message=message, state=state)


@form_router.message(Form.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    save_user_info(message.from_user.id, message.from_user.username, {'name': message.text})
    await state.set_state(Form.location)
    await message.answer("Из какого Вы города/района?", reply_markup=loc_keyboard)


@form_router.message(Form.location, F.text.casefold() == "другое")
async def process_location_drugoe(message: Message, state: FSMContext) -> None:
    await message.reply("Введите название Вашего населенного пункта:", reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.location)
async def process_location(message: Message, state: FSMContext) -> None:
    await state.update_data(location=message.text)
    save_user_info(message.from_user.id, message.from_user.username, {'location': message.text})
    await state.set_state(Form.organization)
    await message.answer("Введите название Вашей организации:", reply_markup=ReplyKeyboardRemove())
    await message.answer(f"_Например, ХНГИ / ХГУ / Нижне\-Тейская СОШ_",
                         reply_markup=skip_organization_keyboard,
                         parse_mode='MarkdownV2')


@form_router.callback_query(F.data == 'skip_organization')
async def process_skip_organization(callback_query: CallbackQuery, state: FSMContext) -> None:
    message = callback_query.message
    await state.update_data(organization='не указано')
    save_user_info(callback_query.from_user.id, callback_query.from_user.username, {'organization': 'не указано'})
    await state.set_state(Form.age)
    await message.answer(f"Сколько Вам лет?", reply_markup=age_keyboard)


@form_router.message(Form.organization)
async def process_organization(message: Message, state: FSMContext) -> None:
    await state.update_data(organization=message.text)
    save_user_info(message.from_user.id, message.from_user.username, {'organization': message.text})
    await state.set_state(Form.age)
    await message.answer(f"Сколько Вам лет?", reply_markup=age_keyboard)


@form_router.message(Form.age)
async def process_age(message: Message, state: FSMContext) -> None:
    await state.update_data(age=message.text)
    save_user_info(message.from_user.id, message.from_user.username, {'age': message.text})
    await state.set_state(Form.khakas_level)
    await message.answer("Как хорошо Вы знаете хакасский язык?", reply_markup=khakas_level_keyboard)


@form_router.message(Form.khakas_level)
async def process_khakas_level(message: Message, state: FSMContext) -> None:
    await state.update_data(khakas_level=message.text)
    save_user_info(message.from_user.id, message.from_user.username, {'khakas_level': message.text})
    await choose_task_type(message=message, state=state)


async def choose_task_type(message: Message, state: FSMContext) -> None:
    task_types_all = ['Перевод с хакасского языка на русский', 'Набор текста с фотографии',
                      'Поиск перевода в тексте']
    keys = ['available_translate', 'available_photo', 'available_align']
    data = await state.get_data()
    task_types = [x for x, key in zip(task_types_all, keys) if key not in data]

    task_type_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=task_types[i])] for i in range(0, len(task_types))
        ],
        resize_keyboard=True,
    )
    # "Учебники хакасского языка и литературы, Хакасское книжное издательство имени "
    # "В\.М\.Торосова, https://online\.khakbooks\.ru/school\-textbooks/basic\n"
    await message.answer("Доступны следующие типы заданий:\n\n"
                         "*1\.Перевод с хакасского языка на русский*\n"
                         "Статьи, Хакас Республиканың газетазы «Хакас чирі», https://www\.khakaschiry\.ru\n\n"
                         "*2\.Набор текста с фотографии*\n"
                         "Поговорим по\-хакасски\. Русско\-хакасский разговорник\. Субракова О\.В\.\n\n"
                         "*3\.Поиск перевода в тексте*\n"
                         "Новости, Министерство физической культуры и спорта Республики Хакасия, "
                         "https://khakas\-stm19\.ru/news, https://stm19\.ru/news\n\n",
                         disable_web_page_preview=True,
                         parse_mode="MarkdownV2")
    await message.answer("Так как подготовка текстов была полуавтоматической, возможно наличие опечаток.")
    await message.answer("При необходимости можно пропускать задания, нажав кнопку *пропустить*\.",
                         parse_mode='MarkdownV2')
    await state.set_state(Form.task_type)
    await message.answer("*Выберите тип заданий:*", reply_markup=task_type_keyboard, parse_mode='MarkdownV2')


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
    elif task_type == 'Поиск перевода в тексте':
        await align_sent_text(message=message, state=state)
    else:
        await choose_task_type(message=message, state=state)


async def translate_khakas_sent(message: Message, state: FSMContext,
                                from_skip: bool = False, to_correct: bool = False) -> None:
    data = await state.get_data()

    # allow user to correct his answer
    if to_correct:
        input_sent = data['input_sent']
        await state.set_state(Form.user_sent)

        # if user skip, just change sentence
        if from_skip:
            await message.edit_text(f'{input_sent}', reply_markup=skip_change_keyboard)
        else:
            await message.answer('*Переведите с хакасского языка на русский:*', reply_markup=ReplyKeyboardRemove(),
                                 parse_mode='MarkdownV2')
            await message.answer(f'{input_sent}', reply_markup=skip_change_keyboard)
    else:
        input_sent = prepare_sent_for_translation(language='khakas')
        if input_sent is None:
            await state.update_data(available_translate=False)
            await message.answer('*Задания данного типа закончились\.*', parse_mode='MarkdownV2')
            await choose_task_type(message=message, state=state)
        else:
            await state.update_data(input_sent=input_sent)

            await state.set_state(Form.user_sent)

            # if user skip, just change sentence
            if from_skip:
                await message.edit_text(f'{input_sent}', reply_markup=skip_change_keyboard)
            else:
                await message.answer('*Переведите с хакасского языка на русский:*', reply_markup=ReplyKeyboardRemove(),
                                     parse_mode='MarkdownV2')
                await message.answer(f'{input_sent}', reply_markup=skip_change_keyboard)


async def type_text_from_photo(message: Message, state: FSMContext,
                               from_skip: bool = False, to_correct: bool = False) -> None:
    data = await state.get_data()

    # allow user to correct his answer
    if to_correct:
        photo = data['photo']
        await state.set_state(Form.text_from_photo)

        # if user skip, just change sentence
        if from_skip:
            await message.answer('Введите текст с фотографии, разделяя примеры *\#*\.\n\n'
                                 'Пример:\n'
                                 '_Доброе утро\! \# Чалахай иртеннең\!\n'
                                 'Что с вами? \# Хайди полдар?\n'
                                 'Мир тесен \# Чир ӱстӱ тарғынах_',
                                 reply_markup=ReplyKeyboardRemove(),
                                 parse_mode='MarkdownV2')
            await message.answer_photo(photo, reply_markup=skip_change_keyboard)
        else:
            await message.answer('Введите текст с фотографии, разделяя примеры *\#*\.\n\n'
                                 'Пример:\n'
                                 '_Доброе утро\! \# Чалахай иртеннең\!\n'
                                 'Что с вами? \# Хайди полдар?\n'
                                 'Мир тесен \# Чир ӱстӱ тарғынах_',
                                 reply_markup=ReplyKeyboardRemove(),
                                 parse_mode='MarkdownV2')
            await message.answer_photo(photo, reply_markup=skip_change_keyboard)
    else:
        photo, path = prepare_photo()
        if path is None:
            await state.update_data(available_photo=False)
            await message.answer('*Задания данного типа закончились\.*', parse_mode='MarkdownV2')
            await choose_task_type(message=message, state=state)
        else:
            await state.update_data(photo=photo, photo_path=path)

            await state.set_state(Form.text_from_photo)

            # if user skip, just change sentence
            if from_skip:
                await message.answer('Введите текст с фотографии, разделяя примеры *\#*\.\n\n'
                                     'Пример:\n'
                                     '_Доброе утро\! \# Чалахай иртеннең\!\n'
                                     'Что с вами? \# Хайди полдар?\n'
                                     'Мир тесен \# Чир ӱстӱ тарғынах_',
                                     reply_markup=ReplyKeyboardRemove(),
                                     parse_mode='MarkdownV2')
                await message.answer_photo(photo, reply_markup=skip_change_keyboard)
            else:
                await message.answer('Введите текст с фотографии, разделяя примеры *\#*\.\n\n'
                                     'Пример:\n'
                                     '_Доброе утро\! \# Чалахай иртеннең\!\n'
                                     'Что с вами? \# Хайди полдар?\n'
                                     'Мир тесен \# Чир ӱстӱ тарғынах_',
                                     reply_markup=ReplyKeyboardRemove(),
                                     parse_mode='MarkdownV2')
                await message.answer_photo(photo, reply_markup=skip_change_keyboard)


async def align_sent_text(message: Message, state: FSMContext,
                          from_skip: bool = False, to_correct: bool = False) -> None:
    data = await state.get_data()

    # allow user to correct his answer
    if to_correct:
        sent1_align = data['sent1_align']
        text2_align = data['text2_align']
        await state.set_state(Form.sent2_align)

        # if user skip, just change sentence
        if from_skip:
            await message.answer(f'{text2_align}', reply_markup=ReplyKeyboardRemove())
            await message.answer(f'*Найдите перевод данного предложения в тексте из предыдущего сообщения:*',
                                 parse_mode='MarkdownV2')
            await message.answer(f'{sent1_align}', reply_markup=skip_change_keyboard)
        else:
            await message.answer(f'{text2_align}', reply_markup=ReplyKeyboardRemove())
            await message.answer(f'*Найдите перевод данного предложения в тексте из предыдущего сообщения:*',
                                 parse_mode='MarkdownV2')
            await message.answer(f'{sent1_align}', reply_markup=skip_change_keyboard)

    else:
        sent1_align, text2_align = prepare_sent_text_for_align()
        if sent1_align is None:
            await state.update_data(available_align=False)
            await message.answer('*Задания данного типа закончились\.*', parse_mode='MarkdownV2')
            await choose_task_type(message=message, state=state)
        else:
            await state.update_data(sent1_align=sent1_align, text2_align=text2_align)

            await state.set_state(Form.sent2_align)

            # if user skip, just change sentence
            if from_skip:
                await message.answer(f'{text2_align}', reply_markup=ReplyKeyboardRemove())
                await message.answer(f'*Найдите перевод данного предложения в тексте из предыдущего сообщения:*', parse_mode='MarkdownV2')
                await message.answer(f'{sent1_align}', reply_markup=skip_change_keyboard)
            else:
                await message.answer(f'{text2_align}', reply_markup=ReplyKeyboardRemove())
                await message.answer(f'*Найдите перевод данного предложения в тексте из предыдущего сообщения:*', parse_mode='MarkdownV2')
                await message.answer(f'{sent1_align}', reply_markup=skip_change_keyboard)


@form_router.message(Form.user_sent)
async def process_user_sent(message: Message, state: FSMContext) -> None:
    user_sent = message.text
    data = await state.update_data(user_sent=user_sent)
    input_sent = data['input_sent']

    await state.set_state(Form.to_correct)
    await message.answer(f'Предложение:\n{input_sent}\n\nВаш перевод:\n{user_sent}',
                         reply_markup=to_correct_keyboard)


@form_router.message(Form.text_from_photo)
async def process_text_from_photo(message: Message, state: FSMContext) -> None:
    text_from_photo = message.text
    data = await state.update_data(text_from_photo=text_from_photo)
    photo = data['photo']

    await state.set_state(Form.to_correct)
    await message.answer_photo(photo, caption=f'Ваш ответ:\n{text_from_photo}',
                               reply_markup=to_correct_keyboard)


@form_router.message(Form.sent2_align)
async def process_user_sent(message: Message, state: FSMContext) -> None:
    sent2_align = message.text
    data = await state.update_data(sent2_align=sent2_align)
    sent1_align = data['sent1_align']

    await state.set_state(Form.to_correct)
    await message.answer(f'Предложение:\n{sent1_align}\n\nПеревод:\n{sent2_align}',
                         reply_markup=to_correct_keyboard)


@form_router.message(Form.to_correct)
async def process_to_correct(message: Message, state: FSMContext) -> None:
    if message.text == 'исправить':
        data = await state.get_data()
        task_type = data['task_type']

        if task_type == 'Перевод с хакасского языка на русский':
            await translate_khakas_sent(message=message, state=state, to_correct=True)
        elif task_type == 'Набор текста с фотографии':
            await type_text_from_photo(message=message, state=state, to_correct=True)
        elif task_type == 'Поиск перевода в тексте':
            await align_sent_text(message=message, state=state, to_correct=True)
        else:
            await choose_task_type(message=message, state=state)

    else:
        await save_results(message=message, state=state)
        await process_task_type(message=message, state=state, to_update=False)


async def save_results(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_type = data['task_type']
    user_id = message.from_user.id
    user_name = message.from_user.username
    if task_type == 'Перевод с хакасского языка на русский':
        save_translation(user_id, user_name, data['input_sent'], data['user_sent'])
        await message.answer('*Сохранено\!*', parse_mode='MarkdownV2')
    elif task_type == 'Набор текста с фотографии':
        save_photo_text(user_id, user_name, data['photo_path'], data['text_from_photo'])
        await message.answer('*Сохранено\!*', parse_mode='MarkdownV2')
    elif task_type == 'Поиск перевода в тексте':
        save_aligned_sents(user_id, user_name, data['sent1_align'], data['sent2_align'])
        await message.answer('*Сохранено\!*', parse_mode='MarkdownV2')
    else:
        await choose_task_type(message=message, state=state)


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
        elif task_type == 'Поиск перевода в тексте':
            await align_sent_text(message=message, state=state, from_skip=True)
        else:
            await choose_task_type(message=message, state=state)


async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
