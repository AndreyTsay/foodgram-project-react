# Foodgram social network 
Recipes from all over the world

___

## INTRODUCTION
A social network for sharing delicious recipes!

___

## PROJECT DESCRIPTION

The Foodgram project allows users to share cooking recipes by posting them on a shared blog. The functionality for unauthorized users is limited to viewing all recipes and detailed information about each one. It can be expanded by registering a user on the site. The functionality for authorized users is much more extensive. In addition to the above, they can: create recipes, view the pages of recipe authors and subscribe to them, add recipes to the favorites list and to the shopping list with the ability to download the resulting list as a separate file.
___

## TECH

[Python] - backend target language

[Django Rest Framework] - Python toolkit for building Web APIs

[JavaScript] - frontend target language

[React] - JavaScript library for building user interfaces

[Ubuntu] - open source operating system based on Linux

[Nginx] - HTTP and reverse proxy server

___

## DEPLOYMENT

### Perform the following steps on your remote server!
**Obtain a domain name**

**Set up a remote server with Ubuntu**

##### Launching a project from images from Docker pub #####
To start, you need to create a project folder, for example, kittygram, and go to it:

mkdir foodgram
cd foodgram
In the project folder, download the docker-composer.production.yml file and run it:

sudo docker compose -f docker-compose.production.yml up
Images will be downloaded, containers will be created and enabled, volumes and networks will be created.```

Clone the "foodgram" repository and navigate to it

```
git clone git@github.com:AndreyTsay/foodgram-project-react.git
```

Create the .env file and fill up according the .env.excample file

```
touch .env
nano .env

POSTGRES_DB=<name_of_database>
POSTGRES_USER=<database_username>
POSTGRES_PASSWORD=<database_password>
DB_NAME=kittygram
DB_HOST=db
DB_PORT=5432
# SECRET_KEY=<your_secret_key>
# DEBUG=<you_private_settings>
# ALLOWED_HOSTS=<you.ip>
```
Create an admin (superuser)

```
python manage.py createsuperuser
```
#####  Executing a startup:

sudo docker compose -f docker-compose.yml up

##### After launch: Migrations, statistics collection

After the launch, it is necessary to collect statistics and migrate the backend. Frontend statistics are collected during container startup, after which it stops.
```
sudo docker compose -f [file name-docker-compose.yml] exec backend python manage.py migrate

sudo docker compose -f [file name-docker-compose.yml] exec backend python manage.py collectstatic

sudo docker compose -f [file name-docker-compose.yml] exec backend cp -r /app/collected_static/. /static/static/
```
And then the project is available on:

http://localhost:9000/
#### Stopping the Containers
In the window where Ctrl+ was launchedWith or in another window:

sudo docker compose -f docker-compose.yml down

## Author

**Created by Andrey Tsay, according to the methodological data of Yandex Practicum**
