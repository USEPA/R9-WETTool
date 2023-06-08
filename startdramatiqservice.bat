@ECHO OFF
set queues=%1
set v=%2
call .\venv\scripts\activate
call .\venv\scripts\python.exe manage.py rundramatiq --processes 2 --threads 2 -v 2