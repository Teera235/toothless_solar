# วิธีนำเข้าแบบง่าย (ไม่ต้องใช้ BigQuery)

เนื่องจากมีปัญหา:
- bq command ต้องการ Administrator permission
- Python environment มีปัญหา
- Encoding issues ในไฟล์ .ps1

## วิธีแก้: ใช้ Cloud Console แทน

### ขั้นตอนที่ 1: โหลด CSV → BigQuery ผ่าน Web UI

1. เปิด BigQuery Console: https://console.cloud.google.com/bigquery?project=trim-descent-452802-t2

2. สร้าง Dataset:
   - คลิก project `trim-descent-452802-t2`
   - คลิก "CREATE DATASET"
   - Dataset ID: `openbuildings`
   - Location: `asia-southeast1`
   - คลิก "CREATE DATASET"

3. สร้าง Table และโหลดข้อมูล:
   - คลิกที่ dataset `openbuildings`
   - คลิก "CREATE TABLE"
   - Source: "Google Cloud Storage"
   - Select file: `gs://trim-descent-452802-t2-openbuildings-v3/thailand/*.csv.gz`
   - File format: CSV
   - Table name: `thailand_raw`
   - Schema: "Auto detect"
   - Advanced options:
     - Header rows to skip: 1
     - Write preference: "Write if empty" หรือ "Overwrite table"
   - คลิก "CREATE TABLE"

4. รอให้โหลดเสร็จ (10-30 นาที)

### ขั้นตอนที่ 2: นำเข้า BigQuery → Cloud SQL

เปิด PowerShell ปกติ (ไม่ต้อง Admin):

```powershell
cd C:\Users\User\Downloads\solar-panel-detection-main\solar-panel-detection-main\dataflow
python import_from_bigquery.py
```

หรือถ้า Python มีปัญหา ใช้ Cloud Shell:

1. เปิด Cloud Shell: https://console.cloud.google.com/home/dashboard?project=trim-descent-452802-t2&cloudshell=true

2. Clone repo หรือ upload script:
```bash
# Upload import_from_bigquery.py ไปยัง Cloud Shell
# จากนั้นรัน:
python3 import_from_bigquery.py
```

## ทางเลือกที่ 2: ใช้ Dataflow (แนะนำถ้าข้อมูลเยอะมาก)

1. เปิด Dataflow Console: https://console.cloud.google.com/dataflow?project=trim-descent-452802-t2

2. คลิก "CREATE JOB FROM TEMPLATE"

3. เลือก template: "BigQuery to Cloud SQL"

4. ตั้งค่า:
   - Job name: `import-buildings`
   - BigQuery table: `trim-descent-452802-t2:openbuildings.thailand_raw`
   - Cloud SQL instance: `trim-descent-452802-t2:asia-southeast1:nabha-solar-db`
   - Database: `toothless_solar`
   - Table: `buildings`

5. คลิก "RUN JOB"

## ทางเลือกที่ 3: ใช้ Cloud Run Job

สร้าง Cloud Run Job ที่รัน import script:

```bash
# Build image
gcloud builds submit --tag gcr.io/trim-descent-452802-t2/import-buildings

# Create job
gcloud run jobs create import-buildings \
  --image gcr.io/trim-descent-452802-t2/import-buildings \
  --region asia-southeast1 \
  --memory 8Gi \
  --cpu 2 \
  --max-retries 3 \
  --task-timeout 3600

# Run job
gcloud run jobs execute import-buildings
```

## สรุป

**ง่ายที่สุด:** ใช้ BigQuery Web UI โหลดข้อมูล แล้วรัน Python script

**เร็วที่สุด:** ใช้ Dataflow (แต่ต้องตั้งค่า)

**ยืดหยุ่นที่สุด:** ใช้ Cloud Run Job
