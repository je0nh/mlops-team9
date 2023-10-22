from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from api_traffic import TrafficProcessor
from api_pollution import PollutionProcessor
from kafka_producer import KafkaProducerWrapper
from airflow.models import Variable


import time

# Airflow DAG 정의
default_args = {
    'owner': 'team09_airflow',
    'start_date': datetime(2023, 10, 11),
    'retries': 1,
    'provide_context': True,
}

dag = DAG(
    'xcom-test2',
    default_args=default_args,
    schedule_interval="30 0,2,4,6,8,10,12,14,16,18,20,22 * * *",  # 홀수 시의 30분마다 실행
    catchup=False,
)

# 대기 데이터 api 호출
def run_api_pollution():
    print("run_api_pollution")
    p = PollutionProcessor()
    pd = p.load_pollution_data()
    return pd

# 받은 데이터 카프카 토픽 전송
def send_to_topic(**context):
    kafka_topic_name = 'kfk-pollution'
    data = context['task_instance'].xcom_pull(task_ids='call_api_pollution')
    kafka_producer_instance = KafkaProducerWrapper(topic=kafka_topic_name, data=data)
    kafka_producer_instance.send_data_to_kafka()

# 태스크 정의
call_api_pollution = PythonOperator(
    task_id='call_api_pollution',
    python_callable=run_api_pollution,
    dag=dag,
    provide_context=True
)

send_topic = PythonOperator(
    task_id='send_to_topic',
    python_callable=send_to_topic,
    dag=dag,
)

# 작업 간의 관계 설정
call_api_pollution >> send_topic
