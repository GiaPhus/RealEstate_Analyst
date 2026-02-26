# RealEstate Data Engineering Stack (Local Dev)

## Tổng quan
Dự án này là **local Data Engineering stack** phục vụ ETL / Analytics cho dữ liệu bất động sản, gồm:

- **MinIO**: object storage (raw / landing)
- **ClickHouse**: data warehouse (OLAP)
- **dbt**: transform & modeling
- **Apache Airflow**: orchestration (schedule, retry, monitor)

Mục tiêu: dựng một pipeline **đơn giản – sạch – đúng bản chất**, dễ debug và đủ để mở rộng.

---

## Kiến trúc tổng thể

```
Raw files / crawl
      ↓
   MinIO (S3)
      ↓
ClickHouse (raw / staging)
      ↓
     dbt (models)
      ↓
 ClickHouse (mart)
      ↑
   Airflow (orchestrate)
```

---

## Cấu trúc thư mục

```
RealEstate_Analyst/
├── airflow/
│   ├── dags/           # DAG Airflow
│   ├── logs/
│   ├── config/
│   │   └── airflow.cfg
│   └── plugins/
│
├── clickhouse_data/
│   ├── ch_data/        # data ClickHouse
│   └── ch_config/      # logs ClickHouse
│
├── dbt/
│   ├── Dockerfile
│   └── realestate/     # dbt project
│       ├── dbt_project.yml
│       ├── models/
│       └── ...
│
├── docker-compose.yaml # toàn bộ stack
├── .env                # env chung
└── README.md
```

---

## Docker Compose Stack

Chạy **tất cả service trong 1 compose**, chung network `de_network`:

- minio
- mc (init bucket)
- clickhouse
- dbt
- postgres (Airflow metadata)
- airflow-apiserver
- airflow-scheduler
- airflow-init

Airflow dùng **LocalExecutor** (không Celery, không Redis) → nhẹ, phù hợp local dev.

---

## Thiết lập & Chạy

### 1. Khởi động stack

```bash
docker compose up -d
docker compose up airflow-init
```

Kiểm tra:

```bash
docker ps
```

---

### 2. Airflow

- UI: http://localhost:8080
- User: `airflow`
- Password: `airflow`

Airflow dùng để:
- gọi dbt
- orchestration pipeline

---

### 3. ClickHouse

- HTTP: http://localhost:8233
- Native: 9010
- Host nội bộ Docker: `clickhouse`

---

### 4. MinIO

- Console: http://localhost:9001
- Bucket mặc định: `warehouse`

---

## dbt Setup (quan trọng)

### Quy tắc bắt buộc

- **dbt project** chạy trong:
  ```
  /usr/app/realestate
  ```
- **profiles.yml** luôn nằm ở:
  ```
  ~/.dbt/profiles.yml  (trong container: /root/.dbt/profiles.yml)
  ```

### profiles.yml (ClickHouse)

```yaml
realestate:
  target: dev
  outputs:
    dev:
      type: clickhouse
      host: clickhouse
      port: 8123
      user: default
      password: changeme
      schema: default
      secure: false
```

> Với ClickHouse: **schema = database** (không khai báo `database` riêng).

### Test dbt

```bash
docker exec -it dbt bash
cd /usr/app/realestate
dbt debug
dbt run
```

---

## Airflow ↔ dbt

Airflow **không cài dbt**, mà gọi dbt thông qua Docker:

```bash
docker exec dbt dbt run --project-dir /usr/app/realestate
```

DAG sẽ dùng `BashOperator` để thực thi lệnh này.

---

## Nguyên tắc thiết kế

- Không Celery cho local dev
- Không gộp logic ETL vào Airflow
- dbt chỉ lo transform
- Airflow chỉ lo orchestration
- ClickHouse là source of truth cho analytics

---

## Trạng thái hiện tại

- [x] MinIO up
- [x] ClickHouse up
- [x] dbt connect ClickHouse
- [x] Airflow UI chạy ổn định
- [ ] DAG dbt run
- [ ] DAG load MinIO → ClickHouse

---

## Bước tiếp theo

1. Viết DAG Airflow chạy `dbt run`
2. Thêm DAG load dữ liệu raw từ MinIO
3. Chia dbt models: staging → mart
4. (Optional) BI tool

---

## Ghi chú

Stack này **không phải production**. Mục tiêu là:
- học đúng bản chất
- dễ debug
- dễ mở rộng

---

Happy hacking 🚀
