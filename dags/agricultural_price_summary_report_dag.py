from datetime import datetime, timedelta
import sys
import os

# เพิ่ม Path ของ dags เข้าไปในระบบ เพื่อให้ Python ค้นหาโมดูลในโฟลเดอร์ utils เจออย่างแม่นยำ
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2
import logging

default_args = {
    'owner': 'airflow_analytics',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def generate_daily_summary_report(**context):
    """
    ฟังก์ชันวิเคราะห์และสรุปผลข้อมูลราคาสินค้าเกษตรประจำวันจากฐานข้อมูล PostgreSQL
    เช่น การคำนวณราคาเฉลี่ย ราคาสูงสุด และต่ำสุดของสินค้าแต่ละชนิด
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "airflow_db"),
        user=os.getenv("DB_USER", "airflow"),
        password=os.getenv("DB_PASSWORD", "airflow"),
        port=int(os.getenv("DB_PORT", 5432))
    )
    cursor = conn.cursor()
    
    # ตัวอย่างคำสั่ง SQL สำหรับวิเคราะห์ข้อมูลสรุปประจำวัน
    summary_query = """
        SELECT 
            product_name,
            COUNT(*) as total_entries,
            AVG(price_value) as avg_price,
            MAX(price_value) as max_price,
            MIN(price_value) as min_price
        FROM agricultural_prices
        GROUP BY product_name;
    """
    
    cursor.execute(summary_query)
    results = cursor.fetchall()
    
    logging.info("--- Agricultural Price Daily Summary Report ---")
    for row in results:
        prod_name, count, avg_p, max_p, min_p = row
        logging.info(f"Product: {prod_name} | Entries: {count} | Avg: {avg_p:.2f} | Max: {max_p} | Min: {min_p}")

    cursor.close()
    conn.close()
    logging.info("Daily summary report generated successfully.")

with DAG(
    'agricultural_price_summary_report_dag',
    default_args=default_args,
    description='Analytics Pipeline for Generating Daily Agricultural Price Summary Reports',
    schedule_interval='30 6 * * *',  # รันทุกวันเวลา 06:30 น. (หลังจาก ETL หลักเสร็จ)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['analytics', 'agriculture', 'reporting'],
) as dag:

    summary_task = PythonOperator(
        task_id='generate_summary_report_task',
        python_callable=generate_daily_summary_report,
        provide_context=True
    )

    summary_task