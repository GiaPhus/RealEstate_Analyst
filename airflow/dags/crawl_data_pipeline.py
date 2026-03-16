from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "data-engineer",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email": ['trangiaphu25092003@gmail.com'],
    "email_on_failure": True,
}

with DAG(
    dag_id="realestate_daily_pipeline",
    default_args=default_args,
    description="Daily real estate ingestion pipeline",
    start_date=datetime(2026, 3, 1),
    schedule="@daily",
    catchup=False,
) as dag:


    crawl_listing_daily = BashOperator(
        task_id="crawl_listing_daily",
        bash_command="""
        cd /opt/airflow/project && \
        python crawling/crawl_listing_daily.py
        """
    )


    crawl_detail_new = BashOperator(
        task_id="crawl_detail_new",
        bash_command="""
        cd /opt/airflow/project && \
        python pipeline/run_detail_from_csv.py
        """
    )


    merge_listing_master = BashOperator(
        task_id="merge_listing_master",
        bash_command="""
        cd /opt/airflow/project && \
        python pipeline/merge_listing_master.py
        """
    )


    crawl_listing_daily >> crawl_detail_new >> merge_listing_master