import os
import time
import logging

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = 'OAuth ' + os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Работа взята на проверку',
    'approved': (
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    ),
}
REQUEST_HEADERS = {'Authorization': PRAKTIKUM_TOKEN}
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    encoding='utf-8')
logger = logging.getLogger(__name__)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error('Работа не найдена')
        return {}
    verdict = STATUSES.get(homework.get('status'), 'Статус неизвестен')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    logger.info('Запрос на сервер отправлен')
    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL,
            params={'from_date': current_timestamp},
            headers=REQUEST_HEADERS
        )
        logger.info('Ответ с сервера получен')
    except requests.exceptions.RequestException as e:
        logger.error(e, exc_info=True)
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Инициализация бота успешна')
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = parse_homework_status(
                    new_homework.get('homeworks')[0])
                send_message(message, bot_client)
                logger.info(f'Сообщение - {message} - успешно отправлено')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            logger.info('Дата изменена')
            time.sleep(300)

        except Exception as e:
            logger.error(e, exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
