import os
import time
import requests
import logging
import telegram
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from exceptions import APIAnsverWrongData
from exceptions import CheckTokenException
from exceptions import APIAnswerInvalidException

logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(asctime)s]-[%(name)s]-[%(levelname)s]-%(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'homework.log',
    maxBytes=50000,
    backupCount=5
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '[%(asctime)s]-[%(name)s]-[%(levelname)s]-%(message)s'
)
handler.setFormatter(formatter)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_BOT')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


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
    logger.debug('send_message start')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Бот отправил сообщение "{message}"')
    except Exception as error:
        logger.error(error)


def get_api_answer(timestamp):
    """
    Отправляет запрос к ЯндексДомашке.
    Ответ - конвертация из json.
    timestamp - метка времени в формате UnixTime.
    """
    logger.debug('get_api_answer start')
    logger.debug(timestamp)
    params = {'from_date': timestamp}
    logger.debug(params)
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )
    code = str(response.status_code)
    logger.info('response status code ' + code)

    if response.status_code != 200:
        raise APIAnswerInvalidException(
            f'Некорректный ответ с сервера, статус код - {code}')
    return response.json()


def check_response(response):
    """
    Проверяет ответ от Яндекс домашки на соответствие ожидаемому.
    На входе должен быть Dict.
    """
    logger.debug('check_response start')
    logger.debug(response)
    if type(response) is dict:
        logger.debug('response is "dict"')
        homeworks = response.get('homeworks')
        logger.debug(homeworks)
        logger.info('В ответе ' + str(len(homeworks)) + ' домашних работ')
    else:
        raise TypeError(
            f'На вход функции подан тип "{type(response)}" вместо "dict"')

    if type(homeworks) is list:
        return homeworks
    else:
        raise TypeError(
            f'Список домашних работ имеет тип "{type(response)}" вместо "list"'
        )


def parse_status(homework):
    """
    Ищем в словаре homework имя домашней работы и её статус.
    На выход выдаём текст для отправки.
    """
    logger.debug('parse_status start')
    logger.debug(homework)

    homework_name = homework.get('homework_name')
    logger.info(homework_name)

    if homework_name is None:
        raise KeyError('Имени домашней работы нет в ответе от сервера')

    homework_status = homework.get('status')
    logger.info(homework_name)

    if homework_status is None:
        raise APIAnsverWrongData(
            'Статуса домашенй работы нет в ответе от сервера')

    verdict = HOMEWORK_STATUSES.get(homework_status)
    logger.info(verdict)

    if verdict is None:
        raise APIAnsverWrongData(
            'Статус домашней работы в ответе от сервера не опознан')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """
    Проверяем наличие переменных окружения.
    Если хоть одна из них None -> False, иначе True.
    """
    logger.debug('check_tokens start')
    args = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for arg, value in args.items():
        if value is None:
            logger.critical(
                f"Отсутствует обязательная переменная окружения: '{arg}' "
                'Программа будет принудительно остановлена.'
            )
            return False
        else:
            logger.debug(f'{arg} присутствует в переменных окружения')
    logger.info('Нужные переменные окружения присутствуют')
    return True


def main():
    """Основная логика работы бота."""
    logger.debug('main start')
    if not check_tokens():
        raise CheckTokenException(
            "Отсутствует одна из обязательных переменных окружения")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # при старте скрипта вычитаем список всех домашек
    current_timestamp = 0
    logger.debug('current_timestamp = 0')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)

            current_timestamp = int(time.time())

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.info('=======START=======')
    main()
