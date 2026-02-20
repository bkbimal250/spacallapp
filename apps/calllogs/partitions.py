from django.db import connection
from datetime import datetime


def create_month_partition(year, month):
    table_name = f"call_logs_{year}_{month:02d}"

    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year+1}-01-01"
    else:
        end_date = f"{year}-{month+1:02d}-01"

    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name}
    PARTITION OF call_logs
    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
    """

    with connection.cursor() as cursor:
        cursor.execute(sql)
