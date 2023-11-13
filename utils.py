from aiogram.types import (
    KeyboardButton,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    FSInputFile
)

locations = ['Абакан',
             'Абаза',
             'Саяногорск',
             'Сорск',
             'Черногорск',
             'Алтайский р-он',
             'Аскизский р-он',
             'Бейский р-он',
             'Боградский р-он',
             'Орджоникидзевский р-он',
             'Таштыпский р-он',
             'Ширинский р-он',
             'Усть-Абаканский р-он',
             'Другое']
loc_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=locations[i]),
         KeyboardButton(text=locations[i+1])]
        for i in range(0, len(locations), 2)
    ],
    resize_keyboard=True,
)

ages = ['+14', '14-17', '18-25', '26-35', '36-50', '50+']
age_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=ages[i]), KeyboardButton(text=ages[i+1])] for i in range(0, len(ages), 2)
    ],
    resize_keyboard=True,
)

khakas_levels = ['Свободно', 'Средне', 'Не знаю']
khakas_level_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=khakas_levels[i])] for i in range(0, len(khakas_levels))
    ],
    resize_keyboard=True,
)

task_types = ['Перевод с хакасского языка на русский', 'Набор текста с фотографии', 'Выравнивание текстов на 2-х языках']
task_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=task_types[i])] for i in range(0, len(task_types))
    ],
    resize_keyboard=True,
)

skip_change_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='пропустить', callback_data='skip_task')],
        [InlineKeyboardButton(text='поменять тип заданий', callback_data='change_task_type')],
    ]
)

to_correct_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='всё верно'), KeyboardButton(text='исправить')],
    ],
    resize_keyboard=True,
)


def prepare_sent_for_translation(language):
    import random
    if language == 'khakas':
        sent = 'khakas ' + ''.join(random.choice('asdfghjklpoiuytreqwzxcvbnm1234567890')
                                             for _ in range(5))
    elif language == 'russian':
        sent = 'russian ' + ''.join(random.choice('asdfghjklpoiuytreqwzxcvbnm1234567890')
                                              for _ in range(5))
    else:
        raise ValueError

    return sent


def prepare_sent_text_for_align():
    import random
    sent = 'khakas ' + ''.join(random.choice('asdfghjklpoiuytreqwzxcvbnm1234567890')
                               for _ in range(5))
    text = 'russian ' + ''.join(random.choice('asdfghjklpoiuytreqwzxcvbnm1234567890 ')
                                              for _ in range(40))
    return sent, text



def prepare_photo():
    import random
    from glob import glob

    data_dir = '/home/vasiliy/Downloads/pogovorim_po_khakasski'
    paths = sorted(glob(f'{data_dir}/*/*.jpeg'))  # todo: add other types of images
    path = random.choice(paths)
    photo = FSInputFile(path)
    return photo
