web                     
├── app                     
│   ├── models                  
│   │    └──model.pkl           
│   └── plot.py             
├── Dockerfile              
├── uwsgi.ini                   
└── requirements.txt                    

Как запустить:
1. Проверить наличие образа ```server_image```  (docker images).
2. Если образа нет, создать : ```docker build -t server_image .```
3. Запустить контейнер на основе образа: ```docker run -it --rm name=server_container -p=80:80 server_image```
4. Протестировать перейдя по ссылке в браузере ```localhost``` или ```http://127.0.0.1/```. Должно вывестись приветствие ```Test message. The server is running!```
5. Запустить скрипт python test/client.py. Вывод:```Status code: 200
Prediction: 14.925283719396463```
6. Посмотреть файловую структуру контейнера: ```docker exec -it server_container bash``` -> перешли в командную строку bash контейнера и вводим: ```#:ls -la```. Далее командой ```cat``` смотрим содержимое всех файлов.
7. Также протестировать работу модели через поднятый веб-сервер NGINX-uWSGI-Flask можно через программу ```Postman```: 
![alt text](./images/image0.png)



В результате выполнения данной команды в терминале вы увидите то же самое сообщение, что и ранее при запуске uWSGI.

Но и это ещё не всё. Как мы уже отметили, на скриншотах, полученных с помощью htop и после запуска uwsgi, видно, что процессов не четыре, а пять. Откуда взялся ещё один? Этот последний процесс является HTTP-роутером, который слушает HTTP-трафик и отправляет его на воркеры (рабочие процессы), то есть он выступает в роли пункта-распределителя.

Однако uWSGI — это не самая оптимальная реализация HTTP-роутера. Она существует скорее для отладки веб-разработчиками, что не является нашей зоной компетенции, поэтому сами авторы uWSGI советуют использовать полноценный веб-сервер. И тут появляется NGINX.
NGINX
NGINX — это веб-сервер, который оптимизирует нагрузку за счёт асинхронной архитектуры, управляемой событиями. Говоря простым языком, архитектура использует одно ядро на один процесс. При этом в одном процессе могут быть сотни тысяч входящих запросов от каждого пользователя. Совместная параллельная обработка позволяет не создавать новые потоки для каждого соединения — это быстро и удобно. Такая высокая производительность делает NGINX самым популярным веб-сервером в мире.

На сегодняшний день NGINX поддерживает протокол uwsgi, что позволяет приложениям WSGI, запущенным на uWSGI, лучше взаимодействовать с NGINX. Благодаря этому развёртывание приложений становится очень простым в настройке, чрезвычайно гибким, функциональным, а также может пользоваться преимуществами поставляемых оптимизаций. Всё это делает сочетание uWSGI + NGINX великолепным вариантом для многих сценариев развёртывания.

Что мы хотим увидеть в итоге?
Мы хотим, чтобы входящие HTTP-запросы, которые поступают на наш сервис, принимал NGINX, так как у него очень высокая производительность. Далее необходимо, чтобы поступающие запросы по протоколу uwsgi передавались на uWSGI, в котором запущены процессы-воркеры, выполняющие обработку запросов на Flask.

![alt text](./images/image.png)

После установки сервер NGINX запускается автоматически. Чтобы проверить, что установка была выполнена успешно, достаточно зайти в браузер и в поисковой строке написать http://localhost (без указания порта)
![alt text](./images/image2.png)

Теперь давайте свяжем uWSGI и NGINX. Чтобы это сделать, нам нужно запустить uWSGI без роутера — место роутера должен занят NGINX, который будет пересылать поступающий трафик, а uWSGI будет слушать трафик прямиком из сокета.

Сокет — это программный интерфейс для взаимодействия между двумя процессами (в нашем случае между NGINX и uWSGI). Можно представить себе сокет как специальный файл в памяти, в который один процесс пишет, а другой из него читает. Тогда наша схема организации взаимодействия между клиентами и веб-приложением будет выглядеть следующим образом:

![alt text](./images/image3.png)

Теперь мы готовы перезапустить uWSGI:

$ uwsgi --ini uwsgi_config.ini
Убедитесь, что в директории /tmp был создан файл socket.sock. Для этого в соседнем терминале выполните команду:

$ ls /tmp/socket.sock

Последний большой шаг — настроить NGINX на передачу приходящих HTTP-запросов в созданный сокет-файл. Для этого нам нужно сначала немного изменить глобальную конфигурацию NGINX, а именно дать ему права на запуск от имени суперпользователя (root). Так NGINX сможет иметь доступ на чтение, изменение и исполнение всех файлов в системе, в том числе для файлов сокетов.
$ sudo nano /etc/nginx/nginx.conf
В этом файле находим строку user и изменяем имя пользователя на root

Формально у NGINX есть только один файл конфигурации — тот, который мы только отредактировали. Теоретически конфигурации для каждого приложения можно было бы прописывать именно в нём. Однако так делать не рекомендуется. Для этого уже существуют папки /etc/nginx/sites-available/ и /etc/nginx/sites-enabled.

Первая просто содержит файлы конфигурации, в каждом из которых находится отдельный виртуальный хост.
Вторая папка содержит ссылки на файлы из sites-available и подключена к основному конфигурационному файлу.

Чтобы составить конфигурацию nginx для нового приложения, мы сначала должны создать файл конфигурации в папке sites-available, а затем создать ссылку на него в папке sites-enabled. В результате таких неочевидных, но очень важных для безопасности манипуляций мы добавим в глобальную конфигурацию работы NGINX конфигурацию, нужную для нашего приложения.

Итак, создадим и откроем на редактирование файл server.conf в папке sites-available:
$ sudo nano /etc/nginx/sites-available/server.conf
server {
    listen 80;
    server_name localhost;
    location / {
        uwsgi_pass unix:/tmp/socket.sock;
        include uwsgi_params;
    }
}

$ sudo ln -s /etc/nginx/sites-available/server.conf /etc/nginx/sites-enabled

Проверим, не было ли обнаружено ошибок при сборке конфигурации. Для этого используется команда nginx с ключом -t (test).

$ sudo nginx -t


**WARNING!!** Удалил мягкую ссылку default -> /etc/nginx/sites-available/default в папке /etc/nginx/sites-enabled, и только после этого NGINX запустился как "роутер" внешних запросов по отношению к процессам на сервере(мы их создали 4 штуки, 5я - сам NGINX).

Момент, который необходимо иметь в виду: когда мы запускаем веб-сервис в контейнере, для тестирования сервера необходимо пользоваться широковещательным адресом (0.0.0.0) — это позволит вам обеспечить доступ к вашему контейнеру. Таким образом, измените в файле server.py следующий код, запускающий сервер:

```if __name__ == '__main__':```            
    ```app.run(host='0.0.0.0', port=5000)```


так как в нашем контейнере будет работать веб-приложение, нам необходимо открыть внешним приложениям доступ к порту, на котором запущено приложение. Это делается с помощью указания ключа --publish или его сокращённой версии -p. В аргументе этой команды указывается диапазон из номеров портов контейнера, которые мы хотим сделать публичными. В нашем приложении мы указали, что нам нужен порт 5000, а значит, диапазон будет выглядеть как 5000:5000. Общий синтаксис команды:

```$ docker run -it --rm --name=server_container -p=5000:5000 flask_image```


Образ ```tiangolo/uwsgi-nginx-flask``` создан на базе ОС Linux, и в нём уже настроено взаимодействие серверов uWSGI и NGINX через сокеты.Файл ./Dockerfile:
```FROM tiangolo/uwsgi-nginx-flask:python3.9 #или укажи версию питона latest```
```docker build -t server_image .```
```docker run -it --rm --name=server_container -p=80:80 server_image```
В соседнем терминале вводим команду чтобы посмотреть файловую структуру запущенного в контейнере приложения:
```docker exec -it server_container bash```
После её выполнения мы попадём в файловую систему, окажемся в рабочей директории нашего контейнера и сможем проанализировать его содержимое. Например, выполним команду ls:
```root@67af457ba3d1:/app# ls```                                           
```__pycache__  main.py  prestart.sh  uwsgi.ini```          


