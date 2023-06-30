# Продуктовый помощник - Foodgram

![Deploy_badge](https://github.com/a-chelnokova/foodgram-project-react/actions/workflows/main.yml/badge.svg)

### Дипломный проект для Яндекс Практикума

На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей,
добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов,
необходимых для приготовления одного или нескольких выбранных блюд.

## Технологии / Tecnhologies:
Python 3.7
Django 3.2
Django REST framework 3.13
Nginx
Docker
Postgres

### Для успешного запуска проекта на сервере:

Cоздайте и активируйте виртуальное окружение:

```
python3.7 -m venv venv
```

```
source venv/bin/activate
```

Установите зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Отредактируйте файл nginx.conf(в строке server_name впишите IP виртуальной машины (сервера))

Подключитесь к своему серверу, установите Docker и Docker-Compose (для Linux):

```
sudo apt install docker.io
```

```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

Скопируйте подготовленные файлы docker-compose.yaml и nginx.conf из вашего проекта на сервер. Для этого существует два способа.

Первый способ: клонировать репозиторий с нужными файлами, переместить их командой mv, удалить всё ненужное

```
rm -rf {название папки}
```

Второй способ:

```
scp docker-compose.yaml <username>@<host>/home/<username>/docker-compose.yaml
sudo mkdir nginx
scp default.conf <username>@<host>/home/<username>/nginx.conf
```

Создайте .env:

```
touch .env
```

В репозитории на Гитхабе добавьте данные в Settings - Secrets - Actions secrets,
на сервере те же данные добавьте в созданный .env:

```
DOCKER_USERNAME - имя пользователя в DockerHub
DOCKER_PASSWORD - пароль пользователя в DockerHub
HOST - ip-адрес сервера
USER - пользователь
SSH_KEY - приватный ssh-ключ (публичный должен быть на сервере)
PASSPHRASE - кодовая фраза для ssh-ключа
DB_ENGINE - django.db.backends.postgresql
DB_HOST - db
DB_PORT - 5432
SECRET_KEY - секретный ключ приложения django (необходимо чтобы были экранированы или отсутствовали скобки)
ALLOWED_HOSTS - список разрешённых адресов
TELEGRAM_TO - id своего телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
TELEGRAM_TOKEN - токен бота (получить токен можно у @BotFather, /token, имя бота)
DB_NAME - postgres (по умолчанию)
POSTGRES_USER - postgres (по умолчанию)
POSTGRES_PASSWORD - postgres (по умолчанию)
```

Если хотите загрузить свои ингредиенты, вам нужно в папке data заменить файл ingredients.json на такой же файл,
но уже с вашими ингредиентами. Они заполняются после выполнения миграции (data migration).

### Документацию проекта можно посмотреть по адресу http://158.160.6.25/api/docs/

### Проект доступен по адресу http://158.160.6.25

### Автор

Гитхаб: https://github.com/a-chelnokova
Почта: achelnokova-00@yandex.ru
