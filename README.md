# 🧠 מערכת ניתוח תלושי שכר - AI Multi-Agent System

מערכת חכמה לניתוח, ולידציה וזיהוי חריגות בתלושי שכר עם יכולות למידה.

## 🎯 תכונות

### 🤖 4 Agents חכמים:
1. **Parser Agent** - קריאת PDF וחילוץ נתונים בעברית
2. **Validator Agent** - בדיקת נכונות חישובים ומיסים
3. **Analyzer Agent** - השוואה לתלושים קודמים וזיהוי חריגות
4. **Reporter Agent** - יצירת דוחות מקיפים

### 🧠 Learning Capability:
- המערכת **לומדת מ-feedback** שלך
- זוכרת מה זה לא שגיאה (false positives)
- מזהה patterns חדשים
- משתפרת עם כל שימוש

### 💾 Database:
- PostgreSQL לשמירת תלושים
- היסטוריה מלאה של ניתוחים
- Feedback tracking

### 🎨 Web Interface:
- ממשק נקי להעלאת PDF
- תצוגת תוצאות בזמן אמת
- היסטוריית תלושים
- סטטיסטיקות

---

## 🚀 התקנה והפעלה

### פיתוח מקומי (Local Development)

#### דרישות מקדימות:
- Docker & Docker Compose
- Anthropic API Key

#### 1. הגדר API Key

צור קובץ `.env` (ראה [.env.example](.env.example)):
```bash
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://payslip_user:payslip_pass@db:5432/payslip_db
```

#### 2. הרץ את המערכת

```bash
# הרצה פשוטה
./start.sh

# או עם docker-compose ישירות
docker-compose up --build
```

#### 3. גש לממשק

פתח דפדפן:
```
http://localhost:8080
```

API מרוץ על:
```
http://localhost:9000
```

---

### 🚂 פריסה ל-Production (Railway)

מדריך מלא ב-[DEPLOYMENT.md](DEPLOYMENT.md)

**קצר:**
1. העלה ל-GitHub
2. צור פרויקט חדש ב-[Railway.app](https://railway.app)
3. הוסף PostgreSQL database
4. הגדר `ANTHROPIC_API_KEY` ב-Environment Variables
5. Deploy!

---

## 📖 שימוש

### העלאת תלוש PDF:

1. פתח את http://localhost:8080
2. גרור PDF או לחץ לבחירה
3. לחץ "העלה ונתח"
4. המתן לתוצאות

### תוצאות שתקבל:

✅ **סיכום**:
- נטו לתשלום
- מספר בעיות שזוהו
- חריגות
- סטטוס כללי

📋 **ולידציה**:
- בדיקת חישובים (ברוטו/נטו)
- בדיקת מיסים (ביטוח לאומי, בריאות)
- קיזוזים (פנסיה וכו')

📊 **ניתוח**:
- השוואה לתלושים קודמים
- זיהוי שינויים משמעותיים
- חריגות בקיזוזים

💡 **המלצות**:
- פעולות מומלצות

---

## 🧠 Learning System

המערכת לומדת מה-feedback שלך!

### דוגמה:

אם המערכת מזהה משהו כ**שגיאה** אבל זה **נורמלי** אצלך:

```python
# בעתיד - דרך הממשק
crew.provide_feedback(
    "false_positive",
    "validator",
    {"issue_description": "Pension rate high"},
    "זה נורמלי בחברה שלנו - יש פנסיה משופרת"
)
```

**המערכת תזכור** ולא תסמן את זה כשגיאה בפעם הבאה!

---

## 📁 מבנה הפרויקט

```
.
├── backend/                  # FastAPI Backend
│   ├── app/
│   │   ├── main.py          # API endpoints
│   │   ├── database.py      # DB models
│   │   └── pdf_parser.py    # PDF parser
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                 # Web UI
│   ├── index.html
│   └── app.js
│
├── src/                      # AI Agents
│   ├── agents/
│   │   ├── parser_agent.py
│   │   ├── validator_agent.py
│   │   ├── analyzer_agent.py
│   │   └── reporter_agent.py
│   ├── learning/
│   │   ├── knowledge_base.py
│   │   └── feedback_collector.py
│   └── payslip_crew.py      # Main orchestrator
│
├── data/                     # Data storage
│   ├── knowledge_base/       # Learning data
│   ├── feedback_history/     # Feedback logs
│   └── payslips/            # Uploaded files
│
├── docker-compose.yml
└── README.md
```

---

## 🔧 API Endpoints

### POST `/api/upload`
העלה ונתח תלוש PDF

**Request:**
```bash
curl -X POST http://localhost:3000/api/upload \
  -F "file=@payslip.pdf"
```

**Response:**
```json
{
  "success": true,
  "payslip_id": 1,
  "result": {
    "parsed_data": {...},
    "validation": {...},
    "analysis": {...},
    "report": {...}
  }
}
```

### GET `/api/payslips`
קבל רשימת תלושים

### GET `/api/payslips/{id}`
קבל תלוש ספציפי

### POST `/api/feedback`
שלח feedback למערכת הלמידה

### GET `/api/stats`
סטטיסטיקות כלליות

### GET `/api/learning/summary`
סיכום למידה

---

## 🗄️ Database Schema

### `payslips`
- פרטי תלוש
- נתונים מפוענחים
- תוצאות ולידציה
- תוצאות ניתוח

### `feedback`
- Feedback מהמשתמש
- סוג ה-feedback
- context ותיקונים

### `learning_patterns`
- Patterns שנלמדו
- כללי ולידציה מעודכנים

---

## 🛑 עצירה

```bash
docker-compose down

# עם מחיקת volumes
docker-compose down -v
```

---

## 🐛 Troubleshooting

### המערכת לא עולה:

1. בדוק שהפורטים פנויים (3000, 5432, 8080)
2. בדוק שיש API Key ב-.env
3. בדוק logs:
   ```bash
   docker-compose logs backend
   docker-compose logs db
   ```

### PDF לא מנותח טוב:

המערכת תומכת בתלושי שכר בעברית.
אם יש בעיות parsing:
1. בדוק שה-PDF קריא (לא סרוק)
2. הוסף patterns ל-`pdf_parser.py`

### Database errors:

```bash
# אתחל מחדש
docker-compose down -v
docker-compose up --build
```

---

## 📝 הערות פיתוח

### הוספת validations:
ערוך [validator_agent.py](src/agents/validator_agent.py)

### שינוי parsing patterns:
ערוך [pdf_parser.py](backend/app/pdf_parser.py)

### התאמת UI:
ערוך [index.html](frontend/index.html) ו-[app.js](frontend/app.js)

---

## 🎓 איך המערכת לומדת?

1. **Knowledge Base** - ChromaDB + JSON files
2. **Feedback Collector** - מעבד feedback ומעדכן
3. **Continuous Improvement** - כל analysis מוסיף לידע

---

## 📊 דוגמה לתלוש

```json
{
  "employee_name": "יוסי כהן",
  "employee_id": "123456789",
  "month": "11",
  "year": "2024",
  "base_salary": 15000,
  "gross_salary": 17000,
  "net_salary": 9985,
  "pension": 1125,
  "tax": 3000,
  "bituach_leumi": 2040
}
```

---

## 🤝 תרומה

רוצה להוסיף features?
1. Fork הפרויקט
2. צור branch חדש
3. שלח Pull Request

---

## 📄 רישיון

MIT License

---

## 💬 תמיכה

שאלות? בעיות?
פתח issue ב-GitHub

---

**נבנה עם ❤️ באמצעות:**
- FastAPI
- CrewAI
- PostgreSQL
- Docker
- Anthropic Claude
- Railway (Production Deployment)
