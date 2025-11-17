# 🚀 Deployment Guide - Payslip Analysis System

## סקירה כללית
מערכת ניתוח תלושי שכר עם AI Agents, FastAPI, PostgreSQL, ו-CrewAI.

## דרישות מקדימות

### מקומי (Local Development)
- Docker Desktop
- Git
- קובץ `.env` עם המפתחות הבאים:
  ```
  ANTHROPIC_API_KEY=your_key_here
  DATABASE_URL=postgresql://payslip_user:payslip_pass@db:5432/payslip_db
  ```

### Railway Production
- חשבון Railway.app
- חשבון GitHub
- Anthropic API Key

---

## 📦 הכנה להעלאה ל-GitHub

### 1. בדיקת קבצים רגישים
ודא ש-`.gitignore` מכיל:
```
.env
.env.local
uploads/
data/
.claude/
```

### 2. יצירת קובץ `.env.example`
כבר נוצר: `.env.example` - זה תבנית לקובץ הסביבה

### 3. העלאה ל-GitHub
```bash
# Add all files
git add .

# Commit changes
git commit -m "Prepare application for Railway deployment

- Add production Dockerfile and railway configs
- Create .env.example for environment variables
- Update .gitignore for sensitive files
- Add deployment documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub (you will do this via GitHub Desktop)
# git push origin main
```

---

## 🚂 פריסה ל-Railway

### שלב 1: יצירת פרויקט חדש
1. היכנס ל-[Railway.app](https://railway.app)
2. לחץ על "New Project"
3. בחר "Deploy from GitHub repo"
4. בחר את ה-repository שלך

### שלב 2: הוספת PostgreSQL Database
1. בפרויקט, לחץ על "+ New"
2. בחר "Database" → "PostgreSQL"
3. Railway תיצור אוטומטית database ותוסיף `DATABASE_URL` למשתני סביבה

### שלב 3: הגדרת Environment Variables
בעמוד ה-Settings של השירות, הוסף:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=sk-dummy-key-for-crewai
ENVIRONMENT=production
DEBUG=False
```

**חשוב:** `DATABASE_URL` כבר מוגדר אוטומטית על ידי Railway!

### שלב 4: הגדרת Build Settings
Railway תזהה אוטומטית את `Dockerfile` ו-`Procfile`.

אבל ודא:
- **Build Command**: `docker build -f Dockerfile -t app .`
- **Start Command**: `bash railway-start.sh`

### שלב 5: Deploy!
1. לחץ על "Deploy"
2. Railway יבנה את הפרויקט וידפלוי אותו
3. תקבל URL ציבורי (לדוגמה: `https://your-app.railway.app`)

---

## 🔧 בדיקת הפריסה

### בדיקת Health של API
```bash
curl https://your-app.railway.app/api/health
```

תגובה צפויה:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T..."
}
```

### בדיקת Database
בלוג של Railway, חפש:
```
✓ Database is ready!
✓ Database tables created!
🌐 Starting FastAPI server...
```

---

## 📊 ניטור ו-Logs

### צפייה ב-Logs ב-Railway
1. בדף הפרויקט, לחץ על השירות
2. עבור ל-tab "Deployments"
3. לחץ על הפריסה הפעילה
4. עבור ל-"Logs"

### Logs מקומיים (Docker)
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

---

## 🗄️ Database Schema

הטבלאות שנוצרות אוטומטית:

1. **payslips** - תלושי שכר
2. **employees** - רשימת עובדים
3. **feedback** - משוב מהמשתמש
4. **learning_patterns** - דפוסים שנלמדו
5. **chat_history** - היסטוריית צ'אט
6. **agent_learning** - למידה עצמית של הסוכן
7. **knowledge_insights** - תובנות שנלמדו
8. **saved_kpis** - KPIs שנשמרו

---

## 🔐 אבטחה

### מפתחות API
- **אף פעם לא** להעלות `.env` ל-GitHub
- השתמש ב-Railway Environment Variables עבור production
- שמור על `ANTHROPIC_API_KEY` בסוד

### Database
- Railway מנהלת אוטומטית SSL connections
- `DATABASE_URL` מוצפן
- גיבויים אוטומטיים ב-Railway Pro plan

---

## 🐛 Troubleshooting

### בעיה: "Database connection failed"
**פתרון:**
1. ודא ש-PostgreSQL service רץ ב-Railway
2. בדוק ש-`DATABASE_URL` מוגדר נכון
3. חכה 30 שניות לאחר deploy - Database לוקח זמן להתחיל

### בעיה: "Module not found"
**פתרון:**
1. בדוק שכל ה-dependencies ב-`backend/requirements.txt`
2. Rebuild את הפרויקט ב-Railway

### בעיה: "Port already in use"
**פתרון מקומי:**
```bash
docker-compose down
docker-compose up --build
```

---

## 📚 Structure של הפרויקט

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── database.py          # Database models
│   │   └── routes/              # API routes
│   ├── agents.py                # CrewAI agents
│   ├── tasks.py                 # Agent tasks
│   ├── tools/                   # Agent tools
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── app.js                   # Main application logic
│   ├── styles.css               # Minimalist design system
│   └── templates.js             # Visualization templates
├── Dockerfile                    # Production multi-stage build
├── docker-compose.yml           # Local development
├── railway.json                 # Railway config
├── railway.toml                 # Railway services
├── Procfile                     # Railway start command
├── railway-start.sh             # Railway startup script
├── .env.example                 # Environment template
└── DEPLOYMENT.md               # זה הקובץ!
```

---

## 🎨 Design System

עיצוב מינימליסטי עם:
- **שחור** (#000000) - Borders, text, backgrounds
- **לבן** (#FFFFFF) - Backgrounds, text
- **סגול בהיר** (#A855F7) - Accents, buttons, charts

השראה: Apple HIG, Dropbox, Medium

---

## 🚦 Commands מקומיים

### התחלת המערכת
```bash
./start.sh
# או
docker-compose up --build
```

### עצירת המערכת
```bash
docker-compose down
```

### Restart Services
```bash
./restart_services.sh
```

### גישה ל-Database
```bash
docker exec -it payslip-db psql -U payslip_user -d payslip_db
```

---

## 📞 תמיכה

### רישום בעיות
- GitHub Issues: [Your Repo]/issues
- Railway Support: support.railway.app

### Documentation
- FastAPI: https://fastapi.tiangolo.com
- CrewAI: https://docs.crewai.com
- Railway: https://docs.railway.app

---

## ✅ Checklist לפני Production

- [ ] `.env` **לא** ב-Git
- [ ] `ANTHROPIC_API_KEY` מוגדר ב-Railway
- [ ] PostgreSQL database נוצר ב-Railway
- [ ] `DATABASE_URL` מוגדר אוטומטית
- [ ] Build הצליח ב-Railway
- [ ] `/api/health` מחזיר 200 OK
- [ ] Frontend טוען בלי errors
- [ ] Upload של PDF עובד
- [ ] Chatbot עונה לשאלות
- [ ] Visualizations נוצרים

---

**🎉 בהצלחה עם הפריסה!**
