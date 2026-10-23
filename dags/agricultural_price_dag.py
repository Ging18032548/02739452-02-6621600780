from datetime import datetime, timedelta
import sys
import os

# เพิ่ม Path ของ dags เข้าไปในระบบ เพื่อให้ Python ค้นหาโมดูลในโฟลเดอร์ utils เจออย่างแม่นยำ
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
import psycopg2

from utils.extractors import extract_oae_api, extract_oae_catalog, extract_dit_scraping
from utils.transformers import transform_and_normalize
from utils.quality_checks import validate_data_quality

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def load_to_postgres(**context):
    """ฟังก์ชันโหลดข้อมูลที่ผ่านการตรวจสอบคุณภาพลง PostgreSQL (ทำ UPSERT)"""
    ti = context['task_instance']
    passed_data = ti.xcom_pull(task_ids='quality_check_task')
    
    if not passed_data:
        print("No valid data to load.")
        return

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "airflow_db"),
        user=os.getenv("DB_USER", "airflow"),
        password=os.getenv("DB_PASSWORD", "airflow"),
        port=int(os.getenv("DB_PORT", 5432))
    )
    cursor = conn.cursor()
    
    upsert_query = """
        INSERT INTO agricultural_prices (source_name, product_type, product_name, market_name, reported_date, price_value, unit, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_name, product_name, market_name, reported_date, unit)
        DO UPDATE SET price_value = EXCLUDED.price_value, updated_at = CURRENT_TIMESTAMP;
    """
    
    for item in passed_data:
        cursor.execute(upsert_query, (
            item["source_name"], item["product_type"], item["product_name"],
            item["market_name"], item["reported_date"], item["price_value"],
            item["unit"], item["source_url"]
        ))
    
    conn.commit()
    cursor.close()
    conn.close()

with DAG(
    'agricultural_price_etl_pipeline',
    default_args=default_args,
    description='ETL Pipeline for Agricultural Prices from 3 Sources with TaskGroup & UPSERT',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    # 1. Extraction TaskGroup (ดึงข้อมูลขนานกันจาก 3 แหล่ง)
    with TaskGroup("extraction_task_group") as extraction_tg:
        t1 = PythonOperator(task_id='extract_oae_api', python_callable=extract_oae_api)
        t2 = PythonOperator(task_id='extract_oae_catalog', python_callable=extract_oae_catalog)
        t3 = PythonOperator(task_id='extract_dit_web', python_callable=extract_dit_scraping)

    # 2. Transform & Data Quality Validation Task
    def process_and_validate(**context):
        ti = context['task_instance']
        r1 = ti.xcom_pull(task_ids='extraction_task_group.extract_oae_api') or []
        r2 = ti.xcom_pull(task_ids='extraction_task_group.extract_oae_catalog') or []
        r3 = ti.xcom_pull(task_ids='extraction_task_group.extract_dit_web') or []
        
        combined = r1 + r2 + r3
        transformed = transform_and_normalize(combined)
        passed, rejected = validate_data_quality(transformed)
        return passed

    transform_quality_task = PythonOperator(
        task_id='quality_check_task',
        python_callable=process_and_validate,
        provide_context=True
    )

    # 3. Load Task (บันทึกลง PostgreSQL)
    load_task = PythonOperator(
        task_id='load_postgres_task',
        python_callable=load_to_postgres,
        provide_context=True
    )

    # กำหนดลำดับการทำงานของ DAG
    extraction_tg >> transform_quality_task >> load_task