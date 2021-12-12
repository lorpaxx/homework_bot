class CheckTokenException(Exception):
    """Отсутствует один из параметров в .env."""

    pass


class APIAnswerInvalidException(Exception):
    """Удалённый API ответил не кодом 200."""

    pass


class APIAnsverWrongData(Exception):
    """Удалённый API ответил неверными данными."""

    pass
