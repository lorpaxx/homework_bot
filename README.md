# Учебный проект Telegram бот-ассистент
## Описание
Учебный проект для отработки навыков работы с **API** в рамках финального задания спринта 7.
Создавался на Python 3.9
## Функционал
Бот раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверять статус отправленной на ревью домашней работы, при обновлении статуса анализирует ответ API и отправлять вам соответствующее уведомление в Telegram.
Бот логирует свою работу и сообщать вам о важных проблемах сообщением в Telegram.
## Технологии в проекте
- Python 3.9
- python-telegram-bot 13.7
## Установка
### Клонировать репозиторий с github:
```
git clone https://github.com/lorpaxx/homework_bot.git
```
### Перейти в склонированный каталог
```
cd homework_bot
```
### Создать и активировать виртуальное окружение, обновить pip
windows
```
python -m venv venv

source venv/Scripts/activate

python -m pip install --upgrade pip
```
linux
```
python3 -m venv venv

source venv/bin/activate

python3 -m pip install --upgrade pip
```
### C помощью pip доустановить остальные необходимые пакеты
```
pip install -r requirements.txt
```
### Заполнит файл .env по аналогии с .env.example

### Запустить бота
```
python homework.py
```
 ## Авторы
 *Александр Бебякин*
