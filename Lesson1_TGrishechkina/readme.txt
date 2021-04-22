1) Я пробовала на убунту запустить uwsgi
Все сначала делала по инструкции, но инструкция не для python3 (а на убунте был именно такой)
Поэтому запросы с python не работали:

sudo apt-get install python-pip

Reading package lists... Done
Building dependency tree
Reading state information... Done
E: Unable to locate package python-pip

и команды для инсталляции получились немного другими:
sudo apt-get install python3-pip

python3 -m pip install uwsgi

sudo apt-get install uwsgi

Все равно при попытке стартовать сервер на 8000 порту выходила ошибка:
uwsgi --http :8000 --wsgi-file fwsgi.py
uwsgi: option '--http' is ambiguous; possibilities: '--http-socket' '--http-socket-modifier1' '--http-socket-modifier2'
'--http11-socket' '--https-socket' '--https-socket-modifier1' '--https-socket-modifier2'
getopt_long() error

python3 -m pip uninstall uwsgi
python3 -m pip install uwsgi

В итоге запустилось так:
uwsgi --http-socket :8000 --plugin python3,http --wsgi-file fwsgi.py

2) через wsgiref запустить получилось, проект на этом репозитории.
Добавила страницы, разметку (надеюсь цвета норм), fronts, сделала получение данных с адресной строки и обработку их.