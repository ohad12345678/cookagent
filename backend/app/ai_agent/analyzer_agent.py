"""
Analyzer Agent - סוכן ניתוח נתונים ויצירת KPI דינמי
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
from anthropic import Anthropic


class AnalyzerAgent:
    """סוכן AI לניתוח נתונים ויצירת insights"""

    def __init__(self, db: Session):
        self.db = db
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-haiku-20241022"  # Haiku for fast analysis

    def create_kpi(self, kpi_name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        יוצר KPI חדש באופן דינמי

        Args:
            kpi_name: שם ה-KPI
            description: תיאור מה ה-KPI מודד
            parameters: פרמטרים (metric, aggregation, group_by, etc.)

        Returns:
            התוצאות וההגדרה של ה-KPI
        """
        from app.database import Payslip

        print(f"[Analyzer] Creating KPI: {kpi_name}")
        print(f"[Analyzer] Parameters: {parameters}")

        # Get all payslips
        payslips = self.db.query(Payslip).filter(Payslip.is_valid == True).all()

        # Extract data based on parameters
        metric = parameters.get('metric', 'sick_days')  # Default to sick_days
        aggregation = parameters.get('aggregation', 'average')
        group_by = parameters.get('group_by')  # department, employee, month

        # Organize data
        grouped_data = {}

        for ps in payslips:
            data = ps.parsed_data

            # Get grouping key
            if group_by == 'department':
                key = data.get('employee', {}).get('department', 'לא מוגדר')
            elif group_by == 'employee':
                key = data.get('employee', {}).get('name', 'לא ידוע')
            elif group_by == 'month':
                month = data.get('period', {}).get('month')
                year = data.get('period', {}).get('year')
                key = f"{month}/{year}"
            else:
                key = 'כללי'

            # Get metric value
            if metric == 'sick_days':
                value = data.get('sick_days')
            elif metric == 'vacation_days':
                value = data.get('vacation_days')
            elif metric == 'work_hours':
                value = data.get('work_hours')
            elif metric == 'gross_salary':
                value = data.get('salary', {}).get('gross')
            elif metric == 'net_salary':
                value = data.get('salary', {}).get('net')
            else:
                value = None

            if value is not None:
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(float(value))

        # Calculate aggregation
        results = {}
        for key, values in grouped_data.items():
            if aggregation == 'average':
                results[key] = round(sum(values) / len(values), 2)
            elif aggregation == 'sum':
                results[key] = round(sum(values), 2)
            elif aggregation == 'max':
                results[key] = round(max(values), 2)
            elif aggregation == 'min':
                results[key] = round(min(values), 2)
            elif aggregation == 'count':
                results[key] = len(values)

        # Save KPI definition to DB
        self._save_kpi_definition(kpi_name, description, parameters, results)

        return {
            "kpi_name": kpi_name,
            "description": description,
            "parameters": parameters,
            "results": results,
            "created_at": datetime.utcnow().isoformat()
        }

    def analyze_trend(self, metric: str, period: str = 'monthly') -> Dict[str, Any]:
        """
        מנתח מגמות לאורך זמן

        Args:
            metric: המדד לניתוח (sick_days, work_hours, salary, etc.)
            period: תקופת הניתוח (monthly, quarterly, yearly)

        Returns:
            ניתוח מגמות
        """
        from app.database import Payslip

        print(f"[Analyzer] Analyzing trend for {metric} by {period}")

        payslips = self.db.query(Payslip)\
            .filter(Payslip.is_valid == True)\
            .order_by(Payslip.year, Payslip.month)\
            .all()

        # Group by period
        trend_data = {}

        for ps in payslips:
            data = ps.parsed_data
            month = data.get('period', {}).get('month')
            year = data.get('period', {}).get('year')

            if period == 'monthly':
                key = f"{year}-{month.zfill(2) if month else '00'}"
            elif period == 'quarterly':
                quarter = (int(month) - 1) // 3 + 1 if month else 1
                key = f"{year}-Q{quarter}"
            else:  # yearly
                key = year

            # Get metric value
            if metric == 'sick_days':
                value = data.get('sick_days')
            elif metric == 'vacation_days':
                value = data.get('vacation_days')
            elif metric == 'work_hours':
                value = data.get('work_hours')
            elif metric == 'gross_salary':
                value = data.get('salary', {}).get('gross')
            else:
                value = None

            if value is not None:
                if key not in trend_data:
                    trend_data[key] = []
                trend_data[key].append(float(value))

        # Calculate averages and identify trend
        trend_results = {}
        for key in sorted(trend_data.keys()):
            values = trend_data[key]
            trend_results[key] = {
                "average": round(sum(values) / len(values), 2),
                "count": len(values),
                "total": round(sum(values), 2)
            }

        # Use AI to analyze the trend
        trend_summary = self._analyze_with_ai(metric, trend_results)

        return {
            "metric": metric,
            "period": period,
            "data": trend_results,
            "analysis": trend_summary,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def detect_anomalies(self, metric: str, threshold: float = 2.0) -> Dict[str, Any]:
        """
        מזהה חריגות בנתונים

        Args:
            metric: המדד לבדיקה
            threshold: סף סטיית תקן (default: 2.0)

        Returns:
            רשימת חריגות שזוהו
        """
        from app.database import Payslip
        import statistics

        print(f"[Analyzer] Detecting anomalies in {metric}")

        payslips = self.db.query(Payslip).filter(Payslip.is_valid == True).all()

        # Collect all values
        values = []
        payslip_map = {}  # Map value to payslip info

        for ps in payslips:
            data = ps.parsed_data

            if metric == 'sick_days':
                value = data.get('sick_days')
            elif metric == 'vacation_days':
                value = data.get('vacation_days')
            elif metric == 'work_hours':
                value = data.get('work_hours')
            elif metric == 'gross_salary':
                value = data.get('salary', {}).get('gross')
            else:
                value = None

            if value is not None:
                value = float(value)
                values.append(value)
                payslip_map[value] = {
                    "employee_name": data.get('employee', {}).get('name'),
                    "employee_id": data.get('employee', {}).get('id'),
                    "month": data.get('period', {}).get('month'),
                    "year": data.get('period', {}).get('year')
                }

        if len(values) < 2:
            return {"error": "Not enough data for anomaly detection"}

        # Calculate statistics
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)

        # Find anomalies
        anomalies = []
        for value in values:
            z_score = abs((value - mean) / stdev) if stdev > 0 else 0

            if z_score > threshold:
                anomalies.append({
                    "value": value,
                    "z_score": round(z_score, 2),
                    "deviation": round(value - mean, 2),
                    **payslip_map[value]
                })

        return {
            "metric": metric,
            "threshold": threshold,
            "statistics": {
                "mean": round(mean, 2),
                "stdev": round(stdev, 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2)
            },
            "anomalies_found": len(anomalies),
            "anomalies": sorted(anomalies, key=lambda x: x['z_score'], reverse=True)
        }

    def _analyze_with_ai(self, metric: str, trend_data: Dict) -> str:
        """משתמש ב-AI לניתוח המגמות"""

        prompt = f"""אתה אנליסט נתונים מומחה.

נתון לך ניתוח של {metric} לאורך זמן:

{trend_data}

תן ניתוח קצר (2-3 שורות) של המגמה:
- האם יש עלייה או ירידה?
- האם יש תקופות חריגות?
- מה התובנה העיקרית?

תשובה בעברית, קצרה וממוקדת:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            print(f"[Analyzer] AI analysis error: {e}")
            return "לא ניתן לנתח את המגמה באמצעות AI"

    def _save_kpi_definition(self, name: str, description: str, parameters: Dict, results: Dict):
        """שומר הגדרת KPI ב-DB"""
        from app.database import SavedKPI

        print(f"[Analyzer] Saving KPI definition: {name}")

        try:
            # Check if KPI with this name already exists
            existing_kpi = self.db.query(SavedKPI).filter(SavedKPI.name == name, SavedKPI.active == True).first()

            if existing_kpi:
                # Update existing KPI
                existing_kpi.description = description
                existing_kpi.metric = parameters.get('metric')
                existing_kpi.aggregation = parameters.get('aggregation')
                existing_kpi.group_by = parameters.get('group_by', 'none')
                existing_kpi.results = results
                existing_kpi.updated_at = datetime.utcnow()
                print(f"[Analyzer] Updated existing KPI: {name}")
            else:
                # Create new KPI
                new_kpi = SavedKPI(
                    name=name,
                    description=description,
                    metric=parameters.get('metric'),
                    aggregation=parameters.get('aggregation'),
                    group_by=parameters.get('group_by', 'none'),
                    results=results
                )
                self.db.add(new_kpi)
                print(f"[Analyzer] Created new KPI: {name}")

            self.db.commit()

        except Exception as e:
            print(f"[Analyzer] Error saving KPI: {e}")
            self.db.rollback()
