from mysql.connector import connect, Error
import pandas as pd
import re
import datetime

def _my_execute(query):
    try:
        with connect(
            host='YOUR HOST',
            user='YOUR USER',
            password='YOUR PASSWORD',
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
            connection.commit()
    except Error as e:
        print(e)

def _my_get_simple_data(query):
    try:
        with connect(
            host='YOUR HOST',
            user='YOUR USER',
            password='YOUR PASSWORD',
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
                if data:
                    data = list(map(lambda x: x[0], data))
                else:
                    data = []
        return data
    except Error as e:
        print(e)

def _my_get_data_two_queries(query_col, query):
    try:
        with connect(
            host='YOUR HOST',
            user='YOUR USER',
            password='YOUR PASSWORD',
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query_col)
                columns = [item[0] for item in cursor.fetchall()]
            with connection.cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
        if data:
            data = pd.DataFrame(data, columns=columns)
        else:
            data = pd.DataFrame([[''] * len(columns)], columns=columns)
        data = data.set_index(data.columns[0])
        return data
    except Error as e:
        print(e)

def create_DB():
    file = 'SQL_Scripts/DataBaseCreation.txt'
    with open(file, 'r') as f:
        query = f.read()

    _my_execute(query)

def add_discription_date(date, text):
    query = f'INSERT INTO  mama_doma.dates_menu (date, description) VALUES(\'{date}\', \'{text}\') ' \
            f'ON DUPLICATE KEY UPDATE description=\'{text}\''
    _my_execute(query)

def add_photo(date, file):
    file = file.replace('\\', '\\\\')

    query = f'INSERT INTO  mama_doma.dates_menu (date, foto) VALUES(\'{date}\', LOAD_FILE(\'{file}\')) ' \
            f'ON DUPLICATE KEY UPDATE foto=LOAD_FILE(\'{file}\')'
    _my_execute(query)

def add_permissions(data):
    data = map(lambda x: re.sub('\s+', '', x), data)

    query = 'DELETE FROM mama_doma.special_permissions'
    _my_execute(query)

    for item in data:
        query = f'insert into mama_doma.special_permissions (username_tg) ' \
                f'values(\'{item}\')'
        _my_execute(query)

def add_hello_text(data):
    query = f'INSERT INTO  mama_doma.meta_info (info_type, text) VALUES(\'hello_text\', \'{data}\') ' \
            f'ON DUPLICATE KEY UPDATE text=\'{data}\''
    _my_execute(query)

def get_users():
    query = 'select * from mama_doma.users'
    query_col = "SHOW columns FROM mama_doma.users"
    return _my_get_data_two_queries(query_col, query)

def get_extra_wishes():
    dates = get_actual_dates()
    begin = (dates[0] - datetime.timedelta(days = 3)).strftime("%Y-%m-%d")

    query = f'select * from mama_doma.extra_wishes ' \
            f'where date_recieved >= \'{begin}\''
    query_col = "SHOW columns FROM mama_doma.extra_wishes"
    return _my_get_data_two_queries(query_col, query)

def get_actual_orders():
    dates = get_actual_dates()
    begin, end = dates[0].strftime("%Y-%m-%d"), dates[-1].strftime("%Y-%m-%d")

    query = f'select * from mama_doma.orders ' \
            f'where date <= \'{end}\' and date >= \'{begin}\''
    query_col = "SHOW columns FROM mama_doma.orders"
    return _my_get_data_two_queries(query_col, query)

def get_actual_dates(how_many = 14):
    query = f'select date from mama_doma.dates_menu ' \
            f'order by date desc ' \
            f'limit {how_many}'
    return _my_get_simple_data(query)[::-1]

def get_usernames_tg():
    query = 'select username_tg from mama_doma.users'
    return _my_get_simple_data(query)

def get_hello_message():
    query = 'select text from mama_doma.meta_info ' \
            'where info_type = \'hello_text\''
    return _my_get_simple_data(query)[0]

def get_permissions():
    query = 'select username_tg from mama_doma.special_permissions'
    return _my_get_simple_data(query)

def add_single_extra_wish(date, text, username = 'Имя не указано'):
    query = f'INSERT INTO  mama_doma.extra_wishes (date_recieved, username_tg, text) ' \
            f'VALUES(\'{date}\', \'{username}\', \'{text}\')'
    _my_execute(query)

def get_previous_dates(how_many = 14, actual_days = 14):
    query = f'select date from mama_doma.dates_menu ' \
            f'order by date desc ' \
            f'limit {how_many + actual_days}'
    result = _my_get_simple_data(query)[actual_days:]
    return result[::-1]

def get_day_menu(date):
    query = f'select * from mama_doma.dates_menu ' \
            f'where date = \'{date}\''
    query_col = 'SHOW columns FROM mama_doma.dates_menu'

    result = {}

    try:
        with connect(
            host='YOUR HOST',
            user='YOUR USER',
            password='YOUR PASSWORD',
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query_col)
                columns = map(lambda x: x[0], cursor.fetchall())
            with connection.cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()[0]
        for i, col in enumerate(columns):
            result[col] = data[i]

        filename = f'{date}.png'
        with open(filename, 'wb') as f:
            f.write(result['foto'])

        result['foto'] = filename

        return result

    except Error as e:
        print(e)