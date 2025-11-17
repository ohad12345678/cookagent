"""
Designer Tools - כלים עבור Designer Agent
"""
from crewai.tools import tool
import requests
import json


@tool("Chart Generator")
def chart_tool(chart_config: dict) -> str:
    """
    יוצר קוד HTML לגרף Chart.js

    Args:
        chart_config: dict עם type, title, labels, datasets

    Returns:
        קוד HTML מוכן להטמעה
    """
    import json
    import hashlib

    try:
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'גרף')
        labels = chart_config.get('labels', [])
        datasets = chart_config.get('datasets', [])

        # Generate unique ID
        chart_id = f"chart_{hashlib.md5(title.encode()).hexdigest()[:8]}"

        html = f"""
<div class="chart-container" style="position: relative; width: 100%; height: 400px; margin: 2rem 0;">
    <canvas id="{chart_id}"></canvas>
</div>

<script>
new Chart(document.getElementById('{chart_id}'), {{
    type: '{chart_type}',
    data: {{
        labels: {json.dumps(labels, ensure_ascii=False)},
        datasets: {json.dumps(datasets, ensure_ascii=False)}
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            title: {{
                display: true,
                text: '{title}'
            }}
        }}
    }}
}});
</script>
"""
        return html.strip()
    except Exception as e:
        return f"<!-- Error creating chart: {e} -->"


@tool("Update Frontend File")
def update_file_tool(file_path: str, content: str) -> str:
    """
    מעדכן קובץ frontend (HTML/CSS/JS)

    Args:
        file_path: שם הקובץ (לדוגמה: "index.html", "styles.css", "app.js")
        content: התוכן החדש של הקובץ

    Returns:
        הודעת הצלחה או שגיאה

    דוגמאות:
        update_file_tool("index.html", "<html>...</html>")
        update_file_tool("styles.css", ".class { color: red; }")
    """
    try:
        # Call the API endpoint
        api_url = "http://backend:9000/api/update-frontend"

        response = requests.post(
            api_url,
            json={
                "file_path": file_path,
                "content": content,
                "backup": True
            },
            timeout=30
        )

        result = response.json()

        if result.get("success"):
            return f"✅ הקובץ {file_path} עודכן בהצלחה! {result.get('message', '')}"
        else:
            return f"❌ שגיאה בעדכון {file_path}: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"❌ שגיאה: {str(e)}"
