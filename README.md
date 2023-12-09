Telegram bot practicum
======================

Бот выполняет запросы к внешнему API Яндекс.Практикума и проверяет статус сданной домашней работы.

Реализовано логгирование. О возможных ошибках исполнения бот также уведомляет в телеграм сообщениях.

Технологии
----------
python-telegram-bot==13.7

Установка
---------
- загрузите проект с гитхаба
  ```git clone git@github.com:ivnpvl/telegram-bot-practicum.git```
- создайте виртуальное окружение и установите зависимости
  ```
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- запустите main.py
  ```python3 main.py```

  Автор
  -----

  Иван Павлов, ivnpvl@mail.ru

