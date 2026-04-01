# Solar Potential API - Backend (คู่มือภาษาไทย)

API สำหรับวิเคราะห์ศักยภาพพลังงานแสงอาทิตย์บนหลังคาอาคารกว่า 107 ล้านหลังทั่วประเทศไทย

## ความสามารถหลัก

- ข้อมูลอาคาร 107,682,789 หลังจาก Google Open Buildings ผ่าน BigQuery
- พยากรณ์อากาศแบบเรียลไทม์ (WxTech 5km global mesh)
- คำนวณพลังงานแสงอาทิตย์แบบฟิสิกส์ (pvlib-python)
- พยากรณ์การผลิตไฟฟ้าตามสภาพอากาศ
- วิเคราะห์ทางการเงิน (ROI, ระยะเวลาคืนทุน)
- คำนวณผลกระทบสิ่งแวดล้อม (ลดการปล่อย CO2)

## เทคโนโลยี

- **Framework**: FastAPI 0.104.1 (Python 3.11)
- **Database**: Google Cloud BigQuery
- **Solar Modeling**: pvlib-python 0.10.3
- **Weather API**: WxTech Global Weather Forecast
- **Deployment**: Google Cloud Run

## การติดตั้งและรัน

### ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### ตั้งค่า Environment Variables

```bash
cp .env.example .env
# แก้ไขไฟล์ .env ใส่ค่าจริง
```

### รัน API

```bash
uvicorn api_bigquery:app --reload --port 8080
```

### เข้าถึง API Documentation

```
http://localhost:8080/docs
```

## API Endpoints

### ข้อมูลอาคาร

- `GET /stats` - สถิติฐานข้อมูล (107M+ อาคาร)
- `GET /stats/distribution` - การกระจายความมั่นใจสำหรับกราฟ
- `GET /buildings/bbox` - ค้นหาอาคารตามพื้นที่
- `GET /buildings/nearby` - ค้นหาอาคารรอบๆ จุด

### วิเคราะห์พลังงานแสงอาทิตย์

- `POST /solar/calculate` - คำนวณศักยภาพพลังงานแสงอาทิตย์
- `GET /solar/forecast` - พยากรณ์การผลิตไฟฟ้าตามสภาพอากาศ

### พยากรณ์อากาศ

- `GET /weather/forecast` - พยากรณ์อากาศแบบเรียลไทม์

## ตัวอย่างการใช้งาน

### ค้นหาอาคารในกรุงเทพฯ

```bash
curl "https://solar-weather-api-715107904640.asia-southeast1.run.app/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=10"
```

### คำนวณศักยภาพพลังงานแสงอาทิตย์

```bash
curl -X POST "https://solar-weather-api-715107904640.asia-southeast1.run.app/solar/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 13.7563,
    "longitude": 100.5018,
    "area_m2": 250,
    "confidence": 0.95
  }'
```

## พารามิเตอร์การคำนวณ (ข้อมูลเฉพาะประเทศไทย)

| พารามิเตอร์ | ค่า | แหล่งอ้างอิง |
|------------|-----|--------------|
| ประสิทธิภาพแผง | 20% | มาตรฐานอุตสาหกรรม monocrystalline |
| ประสิทธิภาพระบบ | 80% | IEA PVPS Thailand 2021 |
| พื้นที่หลังคาใช้งานได้ | 50% | ข้อมูลวิจัย DEDE |
| ต้นทุนติดตั้ง | 25 บาท/Wp | Krungsri Research 2025 |
| ค่าไฟฟ้า | 4.18 บาท/kWh | ERC 2024 |
| CO2 Factor | 0.40 kgCO2/kWh | EPPO/CEIC 2024 |

ทุกพารามิเตอร์มีการอ้างอิงจากแหล่งวิชาการและอุตสาหกรรม ดูรายละเอียดใน `BACKEND.md`

## การ Deploy

### Deploy ไปยัง Google Cloud Run

```bash
gcloud builds submit --config=cloudbuild-bigquery.yaml

gcloud run deploy solar-weather-api \
  --image gcr.io/YOUR_PROJECT/solar-bigquery-api \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=YOUR_PROJECT,WXTECH_API_KEY=YOUR_KEY
```

### ใช้ PowerShell Script

```powershell
./deploy-bigquery-api.ps1
```

## เอกสารประกอบ

- **BACKEND.md** - เอกสาร API แบบละเอียด (ภาษาอังกฤษ)
- **DEPLOYMENT.md** - คู่มือการ Deploy
- **GITHUB_UPLOAD_GUIDE.md** - คู่มือการอัปโหลดไป GitHub
- **/docs** - Swagger UI (เมื่อรัน API)

## การทดสอบ

### ทดสอบการค้นหาอาคาร

```bash
curl "https://solar-weather-api-715107904640.asia-southeast1.run.app/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"
```

### ทดสอบการคำนวณพลังงานแสงอาทิตย์

```bash
curl -X POST "https://solar-weather-api-715107904640.asia-southeast1.run.app/solar/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 13.7563,
    "longitude": 100.5018,
    "area_m2": 250,
    "confidence": 0.95
  }'
```

## ประสิทธิภาพ

- เวลาตอบสนอง: < 600ms
- รองรับ: 1000+ requests/second
- Auto-scaling: 0-10 instances

## แหล่งอ้างอิง

1. IEA PVPS National Survey Report Thailand 2021
2. Krungsri Research - Rooftop Solar Business Models 2025
3. Google Open Buildings Dataset v3
4. pvlib-python Documentation
5. WxTech Global Weather Forecast API

---

**เวอร์ชัน**: 2.1.0  
**อัปเดตล่าสุด**: 30 มีนาคม 2026
