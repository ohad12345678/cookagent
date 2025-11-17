"""
Analyzer - מבצע ניתוחים וסכימות על נתונים שParser חילץ
"""
import re
from typing import Dict, Any, Optional, List


def analyze_hours(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzer - מסכם את כל שעות 150% ו-125% מהטקסט המקורי
    Parser חילץ שדות, Analyzer מנתח ומסכם
    """
    # קבל את הטקסט המקורי שParser שמר
    raw_data = parsed_data.get('raw_data', {})
    original_text = raw_data.get('_original_text', '')

    # סכום כל שעות 150%
    hours_150 = sum_hours_150(original_text)

    # סכום כל שעות 125%
    hours_125 = sum_hours_125(original_text)

    # עדכן את hours_breakdown עם הסכימות
    if 'hours_breakdown' not in parsed_data:
        parsed_data['hours_breakdown'] = {}

    parsed_data['hours_breakdown']['hours_150'] = hours_150
    parsed_data['hours_breakdown']['hours_125'] = hours_125

    print(f"[Analyzer] Summed 150% hours: {hours_150}")
    print(f"[Analyzer] Summed 125% hours: {hours_125}")

    return parsed_data


def sum_hours_150(text: str) -> Optional[float]:
    """
    סכום כל שעות 150% מכל השורות מהטקסט המקורי
    תומך בטקסט RTL שבו 150 יכול להופיע כ-051 (הפוך)
    """

    # חפש את כל השורות עם "ש" (שעות) ו-"150" או "051" (RTL הפוך)
    # דוגמאות:
    #   "078 ש %150שבת 30.47 52.50"
    #   "078 ש %051שבת 30.47 52.50" (RTL - 150 הפוך)
    #   "079 ש 150% כפולה 0.18 52.50"
    # Pattern: קוד + "ש" + (רווח אפציונלי) + משהו עם 150/051 + שעות + תעריף
    patterns = [
        r'(\d{3})\s+ש\s*.*?(150|051).*?\s+([\d.]+)\s+[\d.]+',  # תומך ב-150 או 051 (RTL)
    ]

    total = 0.0
    found = False

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                hours = float(match[2])  # השעות הן בקבוצה השלישית עכשיו
                total += hours
                found = True
                print(f"[Analyzer] Found 150% hours: {hours} (pattern: {match[1]})")
            except (ValueError, IndexError):
                continue

    return total if found else None


def sum_hours_125(text: str) -> Optional[float]:
    """
    סכום כל שעות 125% מכל השורות מהטקסט המקורי
    תומך בטקסט RTL שבו 125 יכול להופיע כ-521 (הפוך)
    """

    # חפש את כל השורות עם "ש" (שעות) ו-"125" או "521" (RTL הפוך)
    # דוגמאות:
    #   "077 ש 125% דיווח 3.83 43.75"
    #   "077 ש 521% דיווח 3.83 43.75" (RTL - 125 הפוך)
    # Pattern: קוד + "ש" + (רווח אפציונלי) + משהו עם 125/521 + שעות + תעריף
    patterns = [
        r'(\d{3})\s+ש\s*.*?(125|521).*?\s+([\d.]+)\s+[\d.]+',  # תומך ב-125 או 521 (RTL)
    ]

    total = 0.0
    found = False

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                hours = float(match[2])  # השעות הן בקבוצה השלישית עכשיו
                total += hours
                found = True
                print(f"[Analyzer] Found 125% hours: {hours} (pattern: {match[1]})")
            except (ValueError, IndexError):
                continue

    return total if found else None


def build_analytics_index(payslips: List[Any]) -> Dict[str, Any]:
    """
    בונה אינדקס מקוצר של כל הנתונים מהתלושים
    מטרה: להפחית את כמות ה-tokens שנשלחת לצ'אט בוט מ-30K ל-3K (חיסכון של 90%)

    Args:
        payslips: רשימת אובייקטי Payslip מהדטבייס

    Returns:
        Dict עם אינדקסים מקוצרים:
        - employees: מיפוי מספר עובד -> שם
        - departments: מיפוי מחלקה -> רשימת עובדים
        - latest_data: הנתונים האחרונים של כל עובד (שכר, ימי חופש, וכו')
        - monthly_summary: סיכום לפי חודש
    """

    # אתחול האינדקסים
    employees = {}  # {employee_id: employee_name}
    departments = {}  # {department: [employee_ids]}
    latest_data = {}  # {employee_id: {salary, vacation_days, etc.}}
    monthly_totals = {}  # {period: {total_salary, count, etc.}}

    # עבור על כל התלושים
    for ps in payslips:
        emp_id = ps.employee_id

        # עדכן מיפוי עובדים
        if emp_id and emp_id not in employees:
            employees[emp_id] = ps.employee_name

        # עדכן מיפוי מחלקות
        if ps.department:
            if ps.department not in departments:
                departments[ps.department] = []
            if emp_id and emp_id not in departments[ps.department]:
                departments[ps.department].append(emp_id)

        # עדכן נתונים אחרונים (נניח שהתלושים ממוינים לפי תאריך)
        if emp_id:
            if emp_id not in latest_data:
                latest_data[emp_id] = {}

            # שמור את הנתונים החשובים בלבד (לא את כל parsed_data!)
            latest_data[emp_id] = {
                "name": ps.employee_name,
                "department": ps.department,
                "period": f"{ps.month}/{ps.year}" if ps.month and ps.year else None,
                "salary": {
                    "base": ps.base_salary,
                    "gross": ps.gross_salary,
                    "net": ps.net_salary,
                    "final_payment": ps.final_payment
                },
                "days": {
                    "vacation": ps.vacation_days,
                    "sick": ps.sick_days
                },
                "hours": {
                    "work": ps.work_hours,
                    "overtime": ps.overtime_hours
                }
            }

            # חלץ ניכויים מ-parsed_data אם קיים
            if ps.parsed_data and 'deductions' in ps.parsed_data:
                deductions = ps.parsed_data['deductions']
                latest_data[emp_id]["deductions"] = {
                    "tax": deductions.get('tax_income', 0),
                    "national_insurance": deductions.get('national_insurance', 0),
                    "health_insurance": deductions.get('health_insurance', 0),
                    "pension": deductions.get('pension_employee', 0)
                }

        # עדכן סיכום חודשי
        period = f"{ps.month}/{ps.year}" if ps.month and ps.year else "unknown"
        if period not in monthly_totals:
            monthly_totals[period] = {
                "count": 0,
                "total_salary": 0,
                "total_hours": 0,
                "total_vacation_days": 0
            }

        monthly_totals[period]["count"] += 1
        if ps.final_payment:
            monthly_totals[period]["total_salary"] += ps.final_payment
        if ps.work_hours:
            monthly_totals[period]["total_hours"] += ps.work_hours
        if ps.vacation_days:
            monthly_totals[period]["total_vacation_days"] += ps.vacation_days

    # בנה את האינדקס הסופי
    index = {
        "employees": employees,
        "departments": departments,
        "latest_data": latest_data,
        "monthly_summary": monthly_totals,
        "metadata": {
            "total_employees": len(employees),
            "total_payslips": len(payslips),
            "total_departments": len(departments)
        }
    }

    return index
