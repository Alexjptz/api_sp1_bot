import logging
import os
import time

from pprint import pprint
import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException

load_dotenv()


PRACTICUM_API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BOT = telegram.Bot(token=TELEGRAM_TOKEN)
VERDICTS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку')
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
    except KeyError as e:
        logging.exception('Отсутствует название работы: {}'.format(e))
        return 'Отсутствует название работы.'
    try:
        status = homework['status']
    except KeyError as e:
        logging.exception('Отсутствует статус работы: {}'.format(e))
        return 'Отсутствует статус работы'
    try:
        verdict = VERDICTS[status]
    except KeyError as e:
        logging.exception('Некорректный статус работы: {}'.format(e))
        verdict = 'Не корректный статус работы: {}'.format(homework['status'])
        return verdict
    else:
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp=int(time.time())):
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {
        'from_date': current_timestamp
    }
    empty = {'homework_name': None}
    try:
        homework_statuses = requests.get(
            url=PRACTICUM_API,
            headers=headers,
            params=params
        )
    except RequestException as e:
        logging.exception(
            'Exсeption {} with params: {}, {}'.format(e, headers, params)
        )
        send_message('Сервер не доступен...')
        return empty
    return homework_statuses.json()


def send_message(message):
    return BOT.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0])
                )
            current_timestamp = (new_homework.get('current_date'))
            time.sleep(900)

        except Exception as e:
            logging.exception(f'Бот упал с ошибкой: {e}')
            time.sleep(300)
            continue


if __name__ == '__main__':
    send_message('Я в сети')
    main()
