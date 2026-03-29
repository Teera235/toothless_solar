# 🌤️ Weather API Integration - Quick Start

ระบบ Solar Panel Detection ได้เพิ่ม Weather API integration แล้ว! ตอนนี้สามารถดู weather forecast และ weather-enhanced solar analysis ได้

## 🚀 การเริ่มต้นใช้งาน

### 1. เริ่ม Backend
```powershell
# ใน folder หลัก
.\start-backend-with-weather.ps1
```

Backend จะรันที่: http://localhost:8080

### 2. ทดสอบ Weather Endpoints
```powershell
# ทดสอบ API endpoints
.\test-weather-endpoints.ps1
```

### 3. เริ่ม Frontend
```bash
cd frontend
npm start
```

Frontend จะรันที่: http://localhost:3000

## 🌟 Features ใหม่

### 1. Weather Forecast Panel
- คลิกปุ่ม "🌤️ Weather" บนแผนที่
- ดู weather forecast สำหรับ location นั้น
- แสดง impact score ต่อ solar generation

### 2. Weather-Enhanced Solar Analysis
- คลิกหลังคาบนแผนที่
- ได้ solar potential + weather forecast
- ดู next 24h generation estimate
- ดู 7-day solar outlook

### 3. API Endpoints ใหม่

#### Weather Forecast
```
GET /weather/forecast?lat=13.7563&lon=100.5018
```

#### Solar Forecast
```
GET /solar/forecast?lat=13.7563&lon=100.5018&system_kwp=5
```

#### Enhanced Solar Calculation
```
POST /solar/calculate
{
  "latitude": 13.7563,
  "longitude": 100.5018,
  "area_m2": 100,
  "confidence": 0.9
}
```

## 📊 ข้อมูลที่ได้

### Weather Data
- **Hourly Forecast:** 72 ชั่วโมง
- **Daily Forecast:** 14 วัน
- **Solar Radiation:** W/m² รายชั่วโมง
- **Temperature, Humidity, Rain:** ครบถ้วน
- **Weather Impact Score:** 0-100

### Solar Analysis
- **Next 24h Generation:** kWh
- **Weather Quality Score:** 0-100
- **7-day Outlook:** Daily generation estimate
- **Weather Impact:** Excellent/Good/Moderate/Poor

## 🔧 Configuration

### Environment Variables
```bash
# backend/.env
WXTECH_API_KEY=your_api_key_here
```

### Frontend Configuration
```javascript
// frontend/.env (optional)
REACT_APP_API_URL=http://localhost:8080
```

## 🧪 การทดสอบ

### 1. ทดสอบ API ตรงๆ
```powershell
# ทดสอบ WxTech API
.\test-weather-api.ps1

# ทดสอบ Backend endpoints
.\test-weather-endpoints.ps1
```

### 2. ทดสอบใน Browser
1. เปิด http://localhost:3000
2. คลิก "🌤️ Weather" button
3. คลิกหลังคาเพื่อดู solar + weather analysis

## 📱 User Experience

### Weather Panel
- **Location:** แสดง lat/lon
- **Impact Summary:** Weather impact level
- **Current Conditions:** Temp, solar radiation, rain
- **Hourly Preview:** Next 12 hours
- **7-Day Outlook:** Daily forecast

### Enhanced Solar Panel
- **Weather Forecast:** Next 24h generation
- **Weather Score:** Quality score
- **Weekly Outlook:** 7-day generation estimate

## 🎯 Use Cases

### 1. Real-time Solar Assessment
- User คลิกหลังคา → ได้ solar potential + weather impact
- ดู next 24h generation forecast
- ประเมิน weather risk

### 2. Weather-aware Planning
- ดู 7-day solar outlook
- วางแผน maintenance ตาม weather
- ประเมิน seasonal performance

### 3. Location Analysis
- เปรียบเทียบ weather impact ระหว่าง location
- หา optimal installation timing
- ประเมิน long-term performance

## 🔍 Troubleshooting

### Backend ไม่เริ่ม
```bash
# ติดตั้ง dependencies
pip install -r backend/requirements.txt

# เช็ค API key
cat backend/.env | grep WXTECH_API_KEY
```

### Weather data ไม่แสดง
1. เช็ค API key ใน .env
2. เช็ค network connection
3. ดู browser console สำหรับ errors

### Frontend ไม่เชื่อมต่อ Backend
1. เช็คว่า backend รันที่ port 8080
2. เช็ค CORS settings
3. เช็ค API_BASE_URL ใน buildingsAPI.js

## 📈 Performance

### Caching Strategy
- Weather data cache 1-3 ชั่วโมง
- Solar calculations cache per building
- API rate limiting: 50 requests/second

### Optimization Tips
- ใช้ weather panel สำหรับ general forecast
- คลิกหลังคาเฉพาะเมื่อต้องการ detailed analysis
- Weather data จะ refresh ทุก 6 ชั่วโมง

## 🌟 Next Steps

1. **Database Integration:** เก็บ weather history
2. **Advanced Analytics:** Weather pattern analysis
3. **Alerts System:** Weather-based notifications
4. **Mobile App:** Weather-enhanced mobile experience

---

**API Key:** ระบบใช้ WxTech 5km Global Weather Forecast API  
**Coverage:** ทั่วโลก, ความละเอียด 5km mesh  
**Update Frequency:** 4 ครั้งต่อวัน