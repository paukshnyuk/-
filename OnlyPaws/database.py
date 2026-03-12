import psycopg2
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST

def get_db_connection():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, options="-c client_encoding=utf8")

# Вспомогательные функции для БД
def get_user_role(user_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    res = cur.fetchone(); conn.close()
    return res[0] if res else None

def is_subscribed(user_id, cat_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM subscriptions WHERE user_id=%s AND cat_id=%s", (user_id, cat_id))
    exists = cur.fetchone(); conn.close()
    return bool(exists)

def get_likes_count(cat_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM likes WHERE cat_id = %s", (cat_id,))
    count = cur.fetchone()[0]; conn.close()
    return count
