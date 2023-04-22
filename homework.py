from dotenv import load_dotenv
from http import HTTPStatus
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
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for token_name, token in tokens.items():
        if not token:
            logger.critical(f'Не определёно значение токена {token_name}!')
            return False
    return True


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Cообщение отправлено: <<<{message}>>>')
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Выполнение запроса к серверу."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        raise error(f'Ошибка при запросе к основному API.')
    if response.status_code != HTTPStatus.OK:
        logger.error(
            f'Запрашиваемый сервер API недоступен по адресу: {response.url}\n'
            f'Статус-код: {response.status_code}\n'
            f'Контент ответа: {response.text}\n'
            f'Заголовки ответа: {response.headers}'
        )
        raise requests.exceptions.HTTPError(
            'Запрашиваемый сервер API недоступен.'
            )
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие данных документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API представлен не в виде словаря.')
    current_date = response.get('current_date')
    if current_date is None:
        raise KeyError('В ответе API нет данных с текущим временем.')
    elif not isinstance(current_date, int):
        raise ValueError('Текущее время не соответствует формату UNIX-time.')
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError('В ответе API нет данных с домашними работами.')
    elif not isinstance(homeworks, list):
        raise TypeError('В ответе API работы представлены не в виде списка.')
    return current_date, homeworks


def parse_status(homework):
    """Получение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError('В ответе API отсутствует имя домашней работы.')
    status = homework.get('status')
    if not status:
        raise KeyError('В ответе API отсутствует статус домашней работы.')
    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        raise KeyError('Неизвестный статус домашней работы.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Работа программы будет принудительно завершена!')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    sent_messages = []
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
            if message not in sent_messages:
                send_message(bot, message)
                sent_messages.append(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
