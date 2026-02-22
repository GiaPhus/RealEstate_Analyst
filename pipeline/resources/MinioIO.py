import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError


import os
import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()


class MinIOClient:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY")
        self.secret_key = os.getenv("MINIO_SECRET_KEY")
        self.bucket = os.getenv("MINIO_BUCKET_NAME", "warehouse")

        if not self.access_key or not self.secret_key:
            raise ValueError("MinIO credentials not found in environment variables")

        if not self.endpoint.startswith("http"):
            self.endpoint = f"http://{self.endpoint}"

        self.s3 = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create bucket if not exists"""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.s3.create_bucket(Bucket=self.bucket)
            print(f"Created bucket: {self.bucket}")

    def upload_json_batch(self, records, source="batdongsan"):
        """Upload list of dicts as JSONL batch"""
        now = datetime.now()

        object_path = (
            f"raw/{source}/"
            f"{now.year}/{now.month:02}/{now.day:02}/"
            f"batch_{int(datetime.timestamp(now))}.json"
        )

        body = "\n".join(
            json.dumps(record, ensure_ascii=False) for record in records
        )

        self.s3.put_object(
            Bucket=self.bucket,
            Key=object_path,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )

        print(f"Uploaded: {object_path}")
        return object_path

    def upload_single_json(self, record, source="batdongsan"):
        """Upload one record per file"""
        now = datetime.now()

        object_path = (
            f"raw/{source}/"
            f"{now.year}/{now.month:02}/{now.day:02}/"
            f"{record.get('listing_id', 'unknown')}.json"
        )

        self.s3.put_object(
            Bucket=self.bucket,
            Key=object_path,
            Body=json.dumps(record, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )

        print(f"Uploaded: {object_path}")
        return object_path