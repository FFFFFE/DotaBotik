import sqlite3
import pandas as pd


def create_connection(db_name):
    conn = sqlite3.connect(db_name)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


def insert_data(conn, table, data):
    try:
        c = conn.cursor()
        c.execute(f"INSERT INTO {table} (match_id, message_id, message_text) VALUES (?, ?, ?)",
                  (data['match_id'], data['message_id'], data['message_text']))
        conn.commit()
    except Exception as e:
        print(e)


def select_data(conn, select_data_sql):
    try:
        return pd.read_sql_query(select_data_sql, conn)
    except Exception as e:
        print(e)

def update_data(conn, update_data_sql):
    try:
        c = conn.cursor()
        c.execute(update_data_sql)
        conn.commit()
    except Exception as e:
        print(e)

def delete_data(conn, delete_data_sql):
    try:
        c = conn.cursor()
        c.execute(delete_data_sql)
        conn.commit()
    except Exception as e:
        print(e)

def close_connection(conn):
    conn.commit()
    conn.close()


# conn = create_connection("database/dota_base.db")

# create_table(conn, 'CREATE TABLE winrate(wins INTEGER, losses INTEGER)')
# insert_data(conn, "INSERT INTO winrate VALUES (111, 83)")

# create_table(conn, 'CREATE TABLE published_matches(match_id INTEGER, message_id INTEGER, message_text TEXT)')

# print(pd.read_sql_query("SELECT * FROM winrate", conn))
# print(select_data(conn, "SELECT * FROM published_matches"))

# close_connection(conn)