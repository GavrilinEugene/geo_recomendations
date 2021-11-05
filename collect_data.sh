source venv/bin/activate
echo 'текущий интерпретатор:'
which python3
echo 'выгружаем изохроны:'
python3 src/collect_isochrones.py
echo 'выгружаем данные по инфраструктуре:'
python3 src/collect_data.py -l $1 -p $2 -s $3 -port $4
echo 'создаём таблицы с административным делением в БД'
python3 src/create_adm_tables.py -l $1 -p $2 -s $3 -port $4
echo 'создаём таблицы инфраструктурными объектами'
python3 src/create_object_info_tables.py -l $1 -p $2 -s $3 -port $4
echo 'создаём таблицы инфраструктурными объектами'
python3 src/create_polygons_black_list.py -l $1 -p $2 -s $3 -port $4