from dotenv import load_dotenv
import json
import logging
import os
import requests
import sys
import telegram
import time

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

def check_tokens():
    '''
    sdsaf
    '''
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
            

def send_message(bot, message):
    '''
    YA docstring
    '''
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')
    else:
        logging.debug(f'Cообщение <<<{message}>>> отправлено.')


def get_api_answer(timestamp):
    '''
    df
    '''
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        raise ConnectionError(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != 200:
        raise ConnectionError('Сервер API не доступен.')
    return response.json()


def check_response(response):
    '''
    sadsaf
    '''
    if not isinstance(response, dict):
        message = 'Ответ API представлен не в виде словаря.'
        logging.error(message)
        raise TypeError(message)
    current_date = response.get('current_date')
    if current_date is None:
        message = 'В ответе API нет данных с текущим временем.'
        logging.error(message)
        raise KeyError(message)
    elif not isinstance(current_date, int):
        message = 'Текущее время не соответствует формату UNIX-time.'
        logging.error(message)
        raise ValueError(message)
    homeworks = response.get('homeworks')
    if homeworks is None:
        message = 'В ответе API нет данных с домашними работами.'
        logging.error(message)
        raise KeyError(message)
    elif not isinstance(homeworks, list):
        message = 'В ответе API домашние работы представлены не в виде списка.'
        logging.error(message)
        raise TypeError(message)
    return current_date, homeworks


def parse_status(homework):
    '''
    dsasafd
    '''
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise ValueError('В ответе API отсутствует имя домашней работы.')
    status = homework.get('status')
    if not status:
        raise ValueError('В ответе API отсутствует статус домашней работы.')
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        print('Заранее неизвестный статус домашней работы.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Необходимые токены не определены!')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    while True:
        try:
            status = get_api_answer(timestamp)
            current_date, homeworks = check_response(status)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            timestamp = current_date
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
