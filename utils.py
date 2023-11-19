import pandas as pd
import random
import os
import uuid

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
         KeyboardButton(text=locations[i + 1])]
        for i in range(0, len(locations), 2)
    ],
    resize_keyboard=True,
)

continue_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Продолжить')]],
    resize_keyboard=True,
)

skip_organization_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='пропустить', callback_data='skip_organization')],
    ]
)

ages = ['+14', '14-17', '18-25', '26-35', '36-50', '50+']
age_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=ages[i]), KeyboardButton(text=ages[i + 1])] for i in range(0, len(ages), 2)
    ],
    resize_keyboard=True,
)

khakas_levels = ['Свободное владение', 'Бытовой уровень', 'Не знаю']
khakas_level_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=khakas_levels[i])] for i in range(0, len(khakas_levels))
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

obuchaem_neuroset_khakas_data_dir = '/home/vasiliy/projects/obuchaem_neuroset_khakas'
user_info_dir = '/home/vasiliy/projects/obuchaem_neuroset_khakas/users_info'
user_answers_dir = '/home/vasiliy/projects/obuchaem_neuroset_khakas/users_answers'

df_khakas_sents = pd.read_csv(f'{obuchaem_neuroset_khakas_data_dir}/khakas_texts/khakaschiry_sents_min_word_num_5.csv')
khakas_sentences = df_khakas_sents['sentences'].values.tolist()
random.shuffle(khakas_sentences)


def prepare_sent_for_translation(language='khakas'):
    import random
    if language == 'khakas':
        if len(khakas_sentences) > 0:
            sent = khakas_sentences.pop()
        else:
            sent = None
    else:
        sent = 'russian ' + ''.join(random.choice('asdfghjklpoiuytreqwzxcvbnm1234567890')
                                    for _ in range(5))
    print('sents', len(khakas_sentences))
    return sent


df_align = pd.read_csv(f'{obuchaem_neuroset_khakas_data_dir}/align_texts/stm19/khakas_russian_text_pairs.csv')
sents_texts = df_align[['khakas_sentences', 'russian_texts']].values.tolist()
random.shuffle(sents_texts)


def prepare_sent_text_for_align():
    sent, text = sents_texts.pop()
    print('sents_texts', len(sents_texts))

    return sent, text[:4000]


df_photo = pd.read_csv(f'{obuchaem_neuroset_khakas_data_dir}/pogovorim_po_khakasski/photo_path_statistics.csv')
available_paths = df_photo['path'].values.tolist()
random.shuffle(available_paths)


def prepare_photo():
    if len(available_paths) > 0:
        path = available_paths.pop()
        photo = FSInputFile(path)
    else:
        path = None
        photo = None
    print('photo: ', len(available_paths))
    return photo, path


def save_translation(user_id, user_name, sent, translation):
    save_dir = f'{user_answers_dir}/{user_id}###{user_name}/translation'
    os.makedirs(save_dir, exist_ok=True)

    filename = str(uuid.uuid4())
    path = f'{save_dir}/{filename}.csv'

    df = pd.DataFrame({'sent': [sent], 'translation': [translation]})
    df.to_csv(path, index=False)


def save_aligned_sents(user_id, user_name, sent, translation):
    save_dir = f'{user_answers_dir}/{user_id}###{user_name}/translation'
    os.makedirs(save_dir, exist_ok=True)

    filename = str(uuid.uuid4())
    path = f'{save_dir}/{filename}.csv'

    df = pd.DataFrame({'sent': [sent], 'translation': [translation]})
    df.to_csv(path, index=False)


def save_photo_text(user_id, user_name, photo_path, text):
    save_dir = f'{user_answers_dir}/{user_id}###{user_name}/photo_text'
    os.makedirs(save_dir, exist_ok=True)

    filename = str(uuid.uuid4())
    path = f'{save_dir}/{filename}.csv'

    df = pd.DataFrame({'photo_path': [photo_path], 'text': [text]})
    df.to_csv(path, index=False)


def save_user_info(user_id, user_name, info):
    save_dir = f'{user_info_dir}/{user_id}###{user_name}'
    os.makedirs(save_dir, exist_ok=True)
    for key, value in info.items():
        path = f'{save_dir}/{key}.csv'
        df = pd.DataFrame({key: [value]})
        df.to_csv(path, index=False)
