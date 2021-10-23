import pickle
from h3 import h3
import pandas as pd
import csv
from io import StringIO

def load_pickle(file_path):
    try:
        with open(file_path, 'rb') as handle:
            return pickle.load(handle)
    except Exception as e:
        print(str(e))
        
def save_pickle(obj, filepath): 
    with open(filepath, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def flatten_json(nested_json, exclude=['']):
    """Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
            exclude: Keys to exclude from output.
        Returns:
            The flattened json object if successful, None otherwise.
    """
    out = {}

    def flatten(x, name='', exclude=exclude):
        if type(x) is dict:
            for a in x:
                if a not in exclude: flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out

def make_h3_index(df, lat, lon, resolution):
    """ create h3 index column based on lat, lon and resolution
        : param df: pandas df
        : param lat: latitude column name
        : param lon: longitude column name
        : param resolution: uber h3 resolution
    """
    scales = [resolution] * len(df)
    return list(map(h3.geo_to_h3, df[lat], df[lon], scales))    


def psql_insert_copy(table, conn, keys, data_iter):
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)

def wkb_hexer(line):
    """string -> postgis geometry hex"""
    return line.wkb_hex


def drop_table(engine, table_name):
    try:
        c = engine.connect()
        c.execute(f"drop table {table_name}")
    except:
        pass

       