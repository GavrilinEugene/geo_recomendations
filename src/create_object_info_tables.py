import psycopg2
import os
import argparse
import glob

if __name__ == '__main__':
    """
    Обогащение инфраструктурных объетов дополнительными данными, которые нужны в работе
    """
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    parser.add_argument('-port', '--port', default='25432')
    parser.add_argument('-key', '--api_key', default ='demo')
    args = parser.parse_args()

    login = args.login
    password = args.password
    host = args.serv
    port = args.port

    conn = psycopg2.connect(f"host={host} dbname=postgis port={port} user={login} password={password}")
    
    files = glob.glob(os.path.join(os.getcwd(), "src/sql/*.sql"))
    for file in files:
      with open(file, 'r') as f:
        sql = f.read()
        print(f"Загружаем {file} в БД")
        with conn.cursor() as cursor:
          cursor.execute(str(sql))

    conn.close()