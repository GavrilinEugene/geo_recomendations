# Решение задачи [#6 хакатона ](https://leaders2021.innoagency.ru/06/)

## Оглавление:
1. [Сбор данных](#Сбор-данных)
2. [Приложение]( #Приложение)

## Сбор-данных

Для задачи были собраны следующие данные:
-   Инфраструктурные объекты города (/src/collect_data.py)
-   Изохроны пешей доступности для каждой точки из матрицы населения исходных данных задачи (/src/collect_isochrones.py)

Для работы приложения было развёрнута база данных postgis, куда были выгруженные собранные и исходные данные
Пример выгрузки данных (/src/create_adm_tables.py)

Для разворачивания данных, необходимых для запуска оптимизации необходимо выполнить команду
```Bash
./collect_data.sh [login] [password] [host] [port]   
где агрументами являются реквезиты для подключения к БД postgis      
```


## Приложение

Приложение написано на `python3` и использованием библиотеки `dash` для отрисовки рекомендательного сервиса
Для запуска нужно:

```Bash
git clone https://github.com/GavrilinEugene/geo_recomendations.git
cd geo_recomendations
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 application/app.py
```
