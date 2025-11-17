#!/bin/bash

# סקריפט אתחול מערכת ניתוח תלושי שכר
# מטרה: להבטיח שכל השרתים עולים בסדר הנכון

echo "🔄 מאתחל מערכת ניתוח תלושי שכר..."
echo ""

# עצור הכל
echo "1️⃣ עוצר containers קיימים..."
docker-compose down

echo ""
echo "2️⃣ מתחיל DB + Backend..."
docker-compose up -d db backend

echo ""
echo "⏳ ממתין ל-Backend להיות מוכן (30 שניות)..."
sleep 30

echo ""
echo "3️⃣ בודק שה-Backend עובד..."
if curl -s http://localhost:9000/ | grep -q "running"; then
    echo "✅ Backend רץ בהצלחה!"
else
    echo "❌ Backend לא עולה - בודק לוגים:"
    docker-compose logs backend --tail 20
    exit 1
fi

echo ""
echo "4️⃣ מתחיל Frontend..."
docker-compose up -d frontend

echo ""
echo "⏳ ממתין ל-Frontend להיות מוכן (5 שניות)..."
sleep 5

echo ""
echo "5️⃣ בודק שה-Frontend עובד..."
if curl -s http://localhost:8080/ | grep -q "DOCTYPE"; then
    echo "✅ Frontend רץ בהצלחה!"
else
    echo "❌ Frontend לא עולה - בודק לוגים:"
    docker-compose logs frontend --tail 20
    exit 1
fi

echo ""
echo "6️⃣ בודק סטטוס כל ה-containers:"
docker-compose ps

echo ""
echo "✅ המערכת עלתה בהצלחה!"
echo ""
echo "🌐 פתח דפדפן: http://localhost:8080"
echo "📊 API: http://localhost:9000"
echo "🗄️  Database: localhost:5432"
echo ""
echo "📝 לוגים:"
echo "   Backend:  docker-compose logs backend --tail 50 -f"
echo "   Frontend: docker-compose logs frontend --tail 50 -f"
echo ""
echo "🧪 מסמך בדיקה: MORNING_TEST_PLAN.md"
echo ""
