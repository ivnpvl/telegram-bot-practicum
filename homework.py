from dotenv import load_dotenv
import logging
from os import getenv
import requests
import sys
import telegram
import time

load_dotenv()

PRACTICUM_TOKEN = getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия необходимых для работы токенов."""
    if not (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        message = 'Необходимые токены не определены!'
        logger.critical(message)
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Cообщение <<<{message}>>> отправлено.')
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Выполнение запроса к серверу."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        message = f'Ошибка при запросе к основному API: {error}'
        logger.error(message)
        raise error(message)
    if response.status_code != 200:
        message = 'Сервер API недоступен.'
        logger.error(message)
        raise requests.exceptions.HTTPError(message)
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие данных документации."""
    if not isinstance(response, dict):
        message = 'Ответ API представлен не в виде словаря.'
        logger.error(message)
        raise TypeError(message)
    current_date = response.get('current_date')
    if current_date is None:
        message = 'В ответе API нет данных с текущим временем.'
        logger.error(message)
        raise KeyError(message)
    elif not isinstance(current_date, int):
        message = 'Текущее время не соответствует формату UNIX-time.'
        logger.error(message)
        raise ValueError(message)
    homeworks = response.get('homeworks')
    if homeworks is None:
        message = 'В ответе API нет данных с домашними работами.'
        logger.error(message)
        raise KeyError(message)
    elif not isinstance(homeworks, list):
        message = 'В ответе API домашние работы представлены не в виде списка.'
        logger.error(message)
        raise TypeError(message)
    return current_date, homeworks


def parse_status(homework):
    """Получение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        message = 'В ответе API отсутствует имя домашней работы.'
        logger.error(message)
        raise ValueError(message)
    status = homework.get('status')
    if not status:
        message = 'В ответе API отсутствует статус домашней работы.'
        logger.error(message)
        raise ValueError(message)
    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        message = 'Неизвестный статус домашней работы.'
        logger.error(message)
        raise ValueError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    while True:
        try:
            status = get_api_answer(timestamp)
            current_date, homeworks = check_response(status)
            if not homeworks:
                logger.debug('Новых статусов в ответе нет.')
            else:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
            timestamp = current_date
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
