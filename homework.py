from dotenv import load_dotenv
import logging
import os
import requests
from sys import exit
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


def check_tokens():
    tokens = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID',
    }
    exit_flag = False
    for token, token_name in tokens:
        if not token:
            logging.critical(f'Не указано значение токена {token_name}.')
            # send_message
            exit_flag = True
    if exit_flag:
        logging.critical(f'Работа бота принудительно завершена.')
        exit()
            

def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    try:
        status = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except:
        pass
    return status.json()


def check_response(response):
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
    homework_name = homework.get('homework_name')
    verdict = homework.get('status')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""


    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    send_message(bot, 'Начнём проверку.')

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
            
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
