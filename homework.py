import os
import time
import requests
import logging
import telegram
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt_dt
from dotenv import load_dotenv
from exceptions import APIAnsverWrongData
from exceptions import CheckTokenException
from exceptions import APIAnswerInvalidException


logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'homework.log',
    maxBytes=500000,
    backupCount=5,
    encoding='utf-8'
)
# handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '[%(asctime)s]-[%(name)s]-[%(levelname)s]-%(message)s'
)
handler.setFormatter(formatter)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_BOT')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

PRACTICUM_RETRY_TIME = 600
PRACTICUM_ENDPOINT = (
    'https://practicum.yandex.ru/api/user_api/homework_statuses/'
)
PRACTICUM_HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """
    Отправляет сообщение ботом о домашеней работе.
    В соответствующий чат.
    """
    logger.debug('send_message(): start')
    logger.debug(message)
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Бот отправил сообщение "{message}"')
    except Exception as error:
        logger.error(error)


def send_messages(bot, messages: set, homework_messages: set):
    """Отправка сообщений, что получились при очередном цикле while."""
    logger.debug('send_messages(): start')
    for message in messages.copy():
        try:
            send_message(bot, message)
            logger.debug('сообщение отправлено')
            homework_messages.add(message)
            logger.debug('сообщение сохранено')
        except Exception as error:
            logger.error(error)


def get_api_answer(timestamp):
    """
    Отправляет запрос к ЯндексДомашке.
    Ответ - конвертация из json.
    timestamp - метка времени в формате UnixTime.
    """
    logger.debug('get_api_answer(): start')
    params = {'from_date': timestamp}
    logger.debug(params)
    try:
        response = requests.get(
            PRACTICUM_ENDPOINT,
            headers=PRACTICUM_HEADERS,
            params=params
        )
        logger.debug(response)
        code = response.status_code
        logger.debug(
            f'timestamp - {timestamp}, - {dt_dt.fromtimestamp(timestamp)} '
            f'response status code {code} '
        )

        if code != 200:
            message = (
                f'response status code {code} '
            )
            logger.error(message)
            raise APIAnswerInvalidException(message)

        return response.json()

    except Exception as error:
        message = f"API_error: {error}"
        logger.error(message)
        raise APIAnswerInvalidException(message)


def check_response(response):
    """
    Проверяет ответ от Яндекс домашки на соответствие ожидаемому.
    На входе должен быть Dict.
    """
    logger.debug('check_response(): start')
    logger.debug(response)

    if not isinstance(response, dict):
        message = f'На вход функции подан тип "{type(response)}" вместо "dict"'
        logger.error(message)
        raise TypeError(message)

    logger.debug('response is "dict"')
    homeworks = response.get('homeworks')
    logger.debug(homeworks)

    if not isinstance(homeworks, list):
        message = (
            f'Список домашних работ имеет тип "{type(response)}" '
            'вместо "list"')
        logger.error(message)
        raise TypeError(message)

    logger.debug('homeworks is list')
    logger.info(f'В ответе {len(homeworks)} домашних работ')
    return homeworks


def parse_status(homework):
    """
    Ищем в словаре homework имя домашней работы и её статус.
    На выход выдаём текст для отправки.
    """
    logger.debug('parse_status(): start')
    logger.debug(homework)

    homework_name = homework.get('homework_name')
    logger.debug(homework_name)

    if homework_name is None:
        message = 'homework_name нет в ответе от сервера'
        logger.error(message)
        raise KeyError(message)

    homework_status = homework.get('status')
    logger.debug(homework_status)

    if homework_status is None:
        message = 'homework_status нет в ответе от сервера'
        logger.error(message)
        raise APIAnsverWrongData(message)

    verdict = HOMEWORK_STATUSES.get(homework_status)
    logger.debug(verdict)

    if verdict is None:
        message = 'homework_status в ответе от сервера не опознан'
        logger.error(message)
        raise APIAnsverWrongData(message)

    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logger.debug(message)
    return message


def check_tokens():
    """
    Проверяем наличие переменных окружения.
    Если хоть одна из них None -> False, иначе True.
    """
    logger.debug('check_tokens(): start')
    args = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    result = all(args)
    if not result:
        logger.critical(
            'Отсутствует одна из обязательных переменных. '
            'Программа будет принудительно остановлена.'
        )
    else:
        logger.info('Все переменные окружения присутствуют')

    return result


def main():
    """Основная логика работы бота."""
    logger.debug('main(): start')
    if not check_tokens():
        raise CheckTokenException(
            "Отсутствует одна из обязательных переменных окружения")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    logger.debug('current_timestamp = 0')
    homework_messages = set()
    error_messages_cache = set()
    while True:
        error_messages = set()
        start_while = int(time.time())
        logger.debug(f'while begin - {start_while}')
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
        except Exception as error:
            homeworks = []
            message = f'Сбой в работе программы: {error}'
            error_messages.add(message)

        messages = set()
        for homework in homeworks:
            try:
                message = parse_status(homework)
                messages.add(message)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                error_messages.add(message)

        new_homework_messages = messages.difference(homework_messages)
        new_error_messages = error_messages.difference(error_messages_cache)
        logger.debug(new_homework_messages)
        logger.debug(new_error_messages)

        send_messages(bot, new_homework_messages, homework_messages)
        send_messages(bot, new_error_messages, error_messages_cache)
        logger.debug(homework_messages)
        logger.debug(error_messages_cache)

        current_timestamp = start_while - 60 * 60 * 24
        end_while = int(time.time())
        time.sleep(PRACTICUM_RETRY_TIME - (end_while - start_while))
        logger.debug(f'while end - {int(time.time())}')


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    logger.info('=======START=======')
    main()
