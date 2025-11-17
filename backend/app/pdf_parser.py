"""
PDF Parser - חילוץ טקסט מתלושי שכר בעברית
"""
import pdfplumber
import PyPDF2
import re
from typing import Dict, Any, Optional


def fix_rtl_text(text: str) -> str:
    """
    מתקן טקסט עברי הפוך שנוצר בגלל בעיות RTL ב-PDF.

    הפונקציה מזהה מילים עבריות הפוכות ומהפכת אותן בחזרה.
    לדוגמה: "הלחמ ןובשח" -> "חשבון מחלה"

    Args:
        text: הטקסט המקורי מה-PDF

    Returns:
        הטקסט המתוקן עם מילים עבריות בכיוון הנכון
    """
    def is_hebrew_char(c: str) -> bool:
        """בדוק אם התו הוא אות עברית"""
        return '\u0590' <= c <= '\u05FF'

    def has_reversed_hebrew(line: str) -> bool:
        """
        בדוק אם השורה מכילה טקסט עברי הפוך.
        סימנים: : לפני או אחרי עברית, או מילים עבריות שמסתיימות באמצע המשפט
        """
        # אם יש : סמוך למילה עברית (לפני או אחרי)
        if re.search(r'[א-ת]+\s*:', line) or re.search(r':[א-ת]+', line):
            return True
        # אם יש הרבה מילים עבריות (ככה נטפל ברוב המקרים)
        hebrew_words = re.findall(r'[א-ת]+', line)
        if len(hebrew_words) >= 2:
            return True
        return False

    def reverse_hebrew_words(line: str) -> str:
        """
        הפוך שורה עברית RTL לפורמט רגיל.
        הגישה: הפוך את כל השורה (סדר מילים + כל מילה), אבל השאר מספרים ותאריכים כפי שהם.
        """
        words = line.split()

        # הפוך את סדר המילים
        words = words[::-1]

        result = []
        for word in words:
            # אם המילה מכילה עברית - הפוך אותה
            if any(is_hebrew_char(c) for c in word):
                result.append(word[::-1])
            else:
                # מספרים, תאריכים, אנגלית - השאר כמו שזה
                result.append(word)

        return ' '.join(result)

    # עבור על כל שורה ותקן
    lines = text.split('\n')
    fixed_lines = []

    for line in lines:
        # אם יש טקסט עברי הפוך - תקן
        if has_reversed_hebrew(line):
            fixed_line = reverse_hebrew_words(line)
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)


class HebrewPayslipPDFParser:
    """
    Parser לתלושי שכר בעברית מ-PDF
    """

    def __init__(self):
        self.patterns = {
            "employee_name": [
                # Pattern 1: שמות לועזיים (1-4 מילים באותיות גדולות) לפני "מחלקה:"
                # דוגמאות: "LI ZHAO מחלקה:", "JOHN DOE SMITH מחלקה:"
                r"([A-Z]+(?:\s+[A-Z]+){0,3})\s+מחלקה:",

                # Pattern 2: שמות עבריים - לוקח את 2 המילים האחרונות לפני "מחלקה:"
                # דוגמאות: "סלע דולב מחלקה:", "אשל עיטם רז מחלקה:" -> "עיטם רז"
                # ה-pattern מחפש מילה עברית, רווח, מילה עברית, רווח, "מחלקה:"
                r"([א-ת]+\s+[א-ת]+)\s+מחלקה:",

                # Pattern 3: Fallback - שדה "שם העובד"
                r"שם העובד[:\s]+([^\n]+)",
                r"שם[:\s]+([^\n]+)",
            ],
            "employee_id": [
                r"מספר העובד:\s*(\d{4,})",  # מספר העובד: 0951
                r"ת\.?ז\.?[:\s]+(\d{9})",
                r"ת\"ז[:\s]+(\d{9})",
                r"מספר זהות[:\s]+(\d{9})",
                r"רפסמ[:\s]*:?\s*(\d{4,})"  # Generic fallback
            ],
            "month": [
                r"לחודש\s+(\d{1,2})/\d{4}",  # Pattern like "לחודש 10/2025"
                r"חודש[:\s]+(\d{1,2})",
                r"תקופה[:\s]+(\d{1,2})[/\-]",
            ],
            "year": [
                r"לחודש\s+\d{1,2}/(\d{4})",  # Year from "לחודש 10/2025"
                r"שנה[:\s]+(\d{4})",
                r"תקופה[:\s]+\d{1,2}[/\-](\d{4})",
                r"/(\d{4})",  # Fallback
            ],
            "base_salary": [
                r"שכר בסיס[:\s]+([\d,]+\.?\d*)",
                r"משכורת בסיס[:\s]+([\d,]+\.?\d*)",
                r"בסיס[:\s]+([\d,]+\.?\d*)"
            ],
            "gross_salary": [
                r"כ\"הס תשלומים\s+([\d,]+\.\d{2})",  # סה"כ תשלומים
                r"ברוטו[:\s]+([\d,]+\.?\d*)",
                r"סה\"כ ברוטו[:\s]+([\d,]+\.?\d*)",
                r"משכורת ברוטו[:\s]+([\d,]+\.?\d*)",
            ],
            "net_salary": [
                r"שכר נטו\s+([\d,]+\.\d{2})",  # שכר נטו
                r"נטו[:\s]+([\d,]+\.?\d*)",
                r"סה\"כ נטו[:\s]+([\d,]+\.?\d*)",
                r"משכורת נטו[:\s]+([\d,]+\.?\d*)",
            ],
            "final_payment": [
                r"לתשלום\s+([\d,]+\.\d{2})",  # לתשלום (אחרי ניכויי רשות)
            ],
            "work_hours": [
                r"שעות עבודה\s+([\d.]+)",
                r"סה\"כ שעות[:\s]+([\d.]+)",
                r"ע\"ש בחברה\s+([\d.]+)",  # Pattern like "ע"ש בחברה 182.0"
            ],
            "tax": [
                r"מס הכנסה\s+([\d,]+\.?\d*)",
                r"מס[:\s]+([\d,]+\.?\d*)",
            ],
            "bituach_leumi": [
                r"ביטוח לאומי[:\s]+([\d,]+\.?\d*)",
                r"ב\.?לאומי\s+([\d,]+\.\d{2})",
                r"ב\.?ל\.?[:\s]+([\d,]+\.?\d*)",
            ],
            "health_insurance": [
                r"ביטוח בריאות[:\s]+([\d,]+\.?\d*)",
                r"ביטוח רפוא\s+([\d,]+\.\d{2})",
                r"בריאות[:\s]+([\d,]+\.?\d*)",
            ],
            "pension": [
                r"פנסיה[:\s]+([\d,]+\.?\d*)",
                r"קרן פנסיה[:\s]+([\d,]+\.?\d*)"
            ],
            "vacation_days": [
                r"ימי חופשה[:\s]+([\d.]+)",
                r"יתרה חדשה\s+([\d.]+)",  # יתרה חדשה (בחשבון חופשה)
                r"חופש[:\s]+([\d.]+)",
                r"יתרת חופש[:\s]+([\d.]+)",
                r"חופש צבור[:\s]+([\d.]+)",
            ],
            "sick_days": [
                r"ימי מחלה[:\s]+([\d.]+)",
                r"מחלה[:\s]+([\d.]+)",
                r"יתרת מחלה[:\s]+([\d.]+)",
                # Pattern for sick days in account section (after "חשבון מחלה")
                r"חשבון מחלה.*?יתרה קודמת\s+([\d.]+)",  # Previous balance
                r"חשבון מחלה.*?יתרה חדשה\s+([\d.]+)",  # New balance (most relevant)
            ],
            "bonus": [
                r"בונוס[:\s]+([\d,]+\.?\d*)",
                r"פרמיה[:\s]+([\d,]+\.?\d*)",
                r"מענק[:\s]+([\d,]+\.?\d*)",
            ],
            "overtime_hours": [
                r"שעות נוספות[:\s]+([\d.]+)",
                r'ש"נ[:\s]+([\d.]+)',
                r"נוספות[:\s]+([\d.]+)",
            ],
            "department": [
                r"מחלקה:\s+(\d{3}\s+[א-ת]+)",  # "מחלקה: 003 במרכנים"
                r"מחלקה[:\s]+(\d+)",  # Just the department number
            ],
            # שדות נוספים מטבלת התשלומים - לא מוצגים בממשק אבל נשמרים ב-DB
            "travel_allowance": [  # 004 נסיעות
                r"004\s+נסיעות\s+[\d.]+\s+[\d.]+\s+([\d,]+\.?\d*)",  # מהעמודה "תעריף"
                r"נסיעות\s+([\d,]+\.?\d*)",
            ],
            "tishrey_bonus": [  # 015 יתרת תשר (בונוס תשרי)
                r"015\s+יתרת תשר\s+[\d.]+\s+([\d,]+\.?\d*)",
                r"יתרת תשר\s+([\d,]+\.?\d*)",
            ],
            "premium": [  # 020 פרמיה
                r"020\s+פרמיה\s+[\d.]+\s+([\d,]+\.?\d*)",
                r"פרמיה\s+([\d,]+\.?\d*)",
            ],
            "base_wage": [  # 063 שכר בר - תופס את המספר האחרון בשורה
                r"063\s+שכר בר\s+[\d.]+\s+[\d.]+\s+([\d,]+\.?\d*)",  # 063 שכר בר 42.68 38.00 1621.84
                r"שכר בר.*?([\d,]+\.\d{2})(?:\s|$)",  # המספר האחרון עם 2 ספרות אחרי נקודה
            ],
            # שדות שעות - לא מוצגים בממשק בסיסי אבל נשמרים
            "regular_hours": [  # שעות רגילות מקוד 063 שכר בר
                r"063\s+שכר בר\s+([\d.]+)",  # המספר הראשון = שעות
            ],
            # Parser רק מחלץ שדות בודדים - לא עושה סכימות!
            # Analyzer יסכום את כל שעות 150% ו-125% מה-raw_data
            "hours_150": [],  # לא בשימוש - Analyzer יחלץ מ-raw_data
            "hours_125": [],  # לא בשימוש - Analyzer יחלץ מ-raw_data
            "saturday_150": [  # 078 ש 150% שבת - הסכום הכספי (לא שעות)
                r"078\s+ש\s+%?\d*שבת\s+[\d.]+\s+[\d.]+\s+([\d,]+\.?\d*)",  # 078 ש %051שבת 30.37 57.00 1731.09
                r"078.*?([\d,]+\.\d{2})(?:\s|$)",  # המספר האחרון בשורה 078
            ],
            "gift_value": [  # 022 שווי מתנות - המספר האחרון
                r"022\s+שווי מתנות(?:.*?\s)([\d,]+\.\d{2})$",  # 022 שווי מתנות ... המספר האחרון
                r"שווי מתנות.*?([\d,]+\.\d{2})$",
            ],
            "severance_extra": [  # 089 פיצויי נוסף
                r"089\s+פיצו[יג]\s+נוסף\s+([\d,]+\.?\d*)",  # תומך גם ב"פיצוג" (טעות כתיב)
                r"פיצו[יג]\s+נוסף\s+([\d,]+\.?\d*)",
            ],
            # === נתונים נוספים מטבלת "נתונים נוספים" ===
            "work_days": [  # ימי עבודה
                r"ימי עבודה\s+(\d+)",
            ],
            "seniority_years": [  # י"ע בחברה (שנות ותק)
                r'י"ע בחברה\s+(\d+)',
                r"שנות ותק\s+(\d+)",
            ],
            "taxable_salary": [  # שכר חייב מס
                r"שכר חייב מס\s+([\d,]+\.?\d*)",
            ],
            "previous_vacation_balance": [  # יתרה קודמת חופש
                r"חשבון חופשה.*?יתרה קודמת\s+([\d.]+)",
            ],
            "vacation_accrued": [  # צבירה ח.ז.
                r"צבירה ח\.ז\.\s+([\d.]+)",
            ],
            "vacation_used": [  # ניצול ח.ז.
                r"ניצול ח\.ז\.\s+([\d.]+)",
            ],
            # === נתונים מצטברים ===
            "cumulative_taxable_salary": [  # שכר חייב מס מצטבר
                r"שכ\.ב\.לאומי\s+([\d,]+\.?\d*)",
            ],
            "cumulative_bituach_leumi": [  # ביטוח לאומי מצטבר
                r"בט\.\s*לאומי\s+([\d,]+\.?\d*)",
            ],
            "cumulative_health_tax": [  # מס בריאות מצטבר
                r"מס בריאות\s+([\d,]+\.?\d*)",
            ],
            # === חשבון מחלה ===
            "previous_sick_balance": [  # יתרה קודמת מחלה
                r"חשבון מחלה.*?יתרה קודמת\s+([\d.]+)",
            ],
            "sick_accrued": [  # צבירה מחלה
                r"חשבון מחלה.*?צבירה.*?\s+([\d.]+)",
            ],
            "sick_used": [  # ניצול מחלה
                r"חשבון מחלה.*?ניצול.*?\s+([\d.]+)",
            ],
            # === מידע בנקאי ===
            "bank": [  # בנק/סניף
                r"בנק:\s+(\d+/\d+)",
            ],
            "account_number": [  # חשבון
                r"חשבון:\s+(\d+)",
            ],
            # === פרטים אישיים נוספים ===
            "id_number": [  # מספר זהות (מלא)
                r"מספר זהות:\s+(\d{9})",
            ],
            "job_basis": [  # בסיס השכר (שעתי/חודשי)
                r"בסיס השכר:\s+([^\n]+)",
            ],
            "seniority_date": [  # ותק מ-
                r"ותק:\s+(\d{2}\.\d{2}\.\d{2})",
            ],
            "start_date": [  # תחילת עבודה
                r"תחילת עבודה:\s+(\d{2}/\d{2}/\d{4})",
            ],
            "address": [  # כתובת עובד
                r"כתובת:\s+([^\n]+)",
            ],
            "marital_status": [  # מצב משפחתי
                r"מצב משפחתי:\s+([^\n]+)",
            ],
            # === שדות מעסיק ===
            "employer_name": [  # שם חברה
                r"חברה\s*:\s*\d+\s*-\s*([^\n]+)",
            ],
            "employer_tax_id": [  # תיק ניכויים מעסיק
                r"תיק ניכויים:\s+(\d+)",
            ],
            "employer_address": [  # כתובת מעסיק
                r"כתובת:\s+([^\n]+?)(?=\s+מספר תאגיד)",
            ],
        }

    def extract_text(self, pdf_path: str) -> str:
        """
        חלץ טקסט מ-PDF ותקן בעיות RTL
        """
        text = ""

        # נסה עם pdfplumber (טוב יותר לעברית)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")

            # נסה עם PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"PyPDF2 also failed: {e}")

        # תקן טקסט הפוך לפני עיבוד
        print("[PDF DEBUG] Applying RTL text fix...")
        text = fix_rtl_text(text)

        return text

    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        נתח PDF של תלוש שכר - תומך במספר תלושים בקובץ אחד
        """
        # חלץ טקסט
        text = self.extract_text(pdf_path)

        if not text:
            return {
                "error": "Could not extract text from PDF",
                "raw_text": ""
            }

        # Debug: הדפס חלק מהטקסט שחולץ
        print(f"[PDF DEBUG] Extracted text length: {len(text)}")

        # בדוק אם יש מספר תלושים
        payslips = self._split_payslips(text)

        if len(payslips) > 1:
            print(f"[PDF DEBUG] Found {len(payslips)} payslips in PDF")

            # נתח כל תלוש בנפרד
            parsed_payslips = []
            for i, payslip_text in enumerate(payslips, 1):
                print(f"[PDF DEBUG] Parsing payslip {i}/{len(payslips)}")
                parsed_data = self._parse_text(payslip_text)

                # Debug
                emp_name = parsed_data.get('employee', {}).get('name')
                emp_id = parsed_data.get('employee', {}).get('id')
                net = parsed_data.get('salary', {}).get('net')
                print(f"  - Employee: {emp_name}, ID: {emp_id}, Net: {net}")

                if emp_id:  # רק אם זוהה מספר עובד
                    parsed_payslips.append(parsed_data)

            return {
                "multiple_payslips": True,
                "payslips": parsed_payslips,
                "count": len(parsed_payslips),
                "raw_text": text[:1000]  # רק חלק מהטקסט
            }
        else:
            # תלוש יחיד
            print(f"[PDF DEBUG] Single payslip detected")
            parsed_data = self._parse_text(text)
            parsed_data["raw_text"] = text[:1000]  # רק חלק מהטקסט

            # Debug: הדפס מה נמצא
            print(f"[PDF DEBUG] Found employee_name: {parsed_data.get('employee', {}).get('name')}")
            print(f"[PDF DEBUG] Found employee_id: {parsed_data.get('employee', {}).get('id')}")
            print(f"[PDF DEBUG] Found net_salary: {parsed_data.get('salary', {}).get('net')}")
            print(f"[PDF DEBUG] Found work_hours: {parsed_data.get('work_hours')}")

            return parsed_data

    def _split_payslips(self, text: str) -> list:
        """
        פצל טקסט למספר תלושים לפי מספר עובד.
        צריך לוודא שכל תלוש כולל גם את כל הקונטקסט - כולל שורות לפני "מספר העובד"
        """
        import re

        # חפש את כל המקומות שבהם מופיע "מספר העובד"
        # הטקסט כבר תוקן ב-RTL אז נחפש בסדר רגיל
        pattern = r'מספר העובד:\s*(\d{4,})'

        matches = list(re.finditer(pattern, text))

        if len(matches) <= 1:
            return [text]  # תלוש יחיד או אין תלושים

        print(f"[PDF DEBUG] Found {len(matches)} employee IDs: {[m.group(1) for m in matches]}")

        # פצל את הטקסט לפי המיקומים של מספרי העובדים
        # אבל נתחיל מהשורה "פרטים אישיים" שלפני כל תלוש
        lines = text.split('\n')
        payslips = []

        for i, match in enumerate(matches):
            # מצא את מיקום ההתחלה של התלוש הזה בשורות
            match_pos = match.start()

            # מצא את השורה שמכילה "מספר העובד"
            current_text = text[:match_pos]
            current_line_num = current_text.count('\n')

            # התחל מ-5 שורות לפני (כדי לתפוס "פרטים אישיים" ושורות קודמות)
            start_line = max(0, current_line_num - 5)

            # הסוף הוא 5 שורות לפני התלוש הבא, או סוף הקובץ
            if i + 1 < len(matches):
                next_match_pos = matches[i + 1].start()
                next_text = text[:next_match_pos]
                next_line_num = next_text.count('\n')
                end_line = max(0, next_line_num - 5)
            else:
                end_line = len(lines)

            payslip_lines = lines[start_line:end_line]
            payslip_text = '\n'.join(payslip_lines)
            payslips.append(payslip_text)

        return payslips

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """
        נתח טקסט של תלוש - משתמש גם בסוכן AI לחילוץ נתונים מורכבים
        """
        result = {}

        # חלץ כל שדה עם patterns רגילים
        for field, patterns in self.patterns.items():
            value = self._extract_field(text, patterns, field_name=field)
            if value:
                result[field] = value
                # DEBUG: הדפס את הערך שנמצא
                if field == "gross_salary":
                    print(f"[DEBUG] Found gross_salary: {value}")

        # תמיד השתמש ב-AI לימי מחלה כי הפורמט מורכב
        # גם אם נמצא משהו עם patterns - נדרוס עם AI
        sick_days = self._extract_sick_days_with_ai(text)
        if sick_days:
            result['sick_days'] = str(sick_days)
            print(f"[AI-Parser] Found sick_days with AI: {sick_days}")

        # שמור את הטקסט המקורי המלא - Analyzer צריך אותו!
        result['_original_text'] = text

        # נרמל לפורמט של המערכת
        normalized = self._normalize_to_system_format(result)

        return normalized

    def _extract_field(self, text: str, patterns: list, field_name: str = None) -> Optional[str]:
        """
        חלץ שדה לפי רשימת patterns
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # נקה רווחים מיותרים
                value = re.sub(r'\s+', ' ', value)
                return value
        return None

    def _to_float(self, value: Optional[str]) -> Optional[float]:
        """
        המר למספר
        """
        if not value:
            return None
        try:
            # הסר פסיקים ו-₪
            clean = value.replace(",", "").replace("₪", "").strip()
            return float(clean)
        except:
            return None

    def _normalize_to_system_format(self, data: Dict) -> Dict[str, Any]:
        """
        המר לפורמט של המערכת - כולל את כל השדות שחולצו
        """
        return {
            "employee": {
                "name": data.get("employee_name"),
                "id": data.get("employee_id"),
                "department": data.get("department"),
                "id_number": data.get("id_number"),  # מספר זהות מלא
                "address": data.get("address"),
                "marital_status": data.get("marital_status"),
                "job_basis": data.get("job_basis"),  # שעתי/חודשי
                "seniority_date": data.get("seniority_date"),  # ותק מ-
                "start_date": data.get("start_date")  # תחילת עבודה
            },
            "employer": {
                "name": data.get("employer_name"),
                "tax_id": data.get("employer_tax_id"),
                "address": data.get("employer_address")
            },
            "period": {
                "month": data.get("month"),
                "year": data.get("year")
            },
            "salary": {
                "base": self._to_float(data.get("base_salary")),
                "gross": self._to_float(data.get("gross_salary")),
                "net": self._to_float(data.get("net_salary")),
                "final_payment": self._to_float(data.get("final_payment")),
                "taxable": self._to_float(data.get("taxable_salary"))  # שכר חייב מס
            },
            "work_hours": self._to_float(data.get("work_hours")),
            "work_days": self._to_float(data.get("work_days")),  # ימי עבודה
            "seniority_years": self._to_float(data.get("seniority_years")),  # שנות ותק
            "overtime_hours": self._to_float(data.get("overtime_hours")),
            "vacation_days": self._to_float(data.get("vacation_days")),
            "sick_days": self._to_float(data.get("sick_days")),
            "deductions": {
                "tax": self._to_float(data.get("tax")),
                "social_security": self._to_float(data.get("bituach_leumi")),
                "health": self._to_float(data.get("health_insurance")),
                "pension": self._to_float(data.get("pension"))
            },
            "additions": {
                "bonus": self._to_float(data.get("bonus")),
                "overtime": self._to_float(data.get("overtime_hours"))
            },
            "taxes": {
                "income_tax": self._to_float(data.get("tax")),
                "bituach_leumi": self._to_float(data.get("bituach_leumi")),
                "health_tax": self._to_float(data.get("health_insurance"))
            },
            # חשבון חופשה מפורט
            "vacation_account": {
                "previous_balance": self._to_float(data.get("previous_vacation_balance")),
                "accrued": self._to_float(data.get("vacation_accrued")),  # צבירה
                "used": self._to_float(data.get("vacation_used")),  # ניצול
                "current_balance": self._to_float(data.get("vacation_days"))  # יתרה חדשה
            },
            # חשבון מחלה מפורט
            "sick_account": {
                "previous_balance": self._to_float(data.get("previous_sick_balance")),
                "accrued": self._to_float(data.get("sick_accrued")),  # צבירה
                "used": self._to_float(data.get("sick_used")),  # ניצול
                "current_balance": self._to_float(data.get("sick_days"))  # יתרה חדשה
            },
            # נתונים מצטברים
            "cumulative": {
                "taxable_salary": self._to_float(data.get("cumulative_taxable_salary")),
                "bituach_leumi": self._to_float(data.get("cumulative_bituach_leumi")),
                "health_tax": self._to_float(data.get("cumulative_health_tax"))
            },
            # מידע בנקאי
            "banking": {
                "bank": data.get("bank"),  # בנק/סניף
                "account_number": data.get("account_number")
            },
            # שדות נוספים - נשמרים ב-DB
            "additional_payments": {
                "travel_allowance": self._to_float(data.get("travel_allowance")),
                "tishrey_bonus": self._to_float(data.get("tishrey_bonus")),
                "premium": self._to_float(data.get("premium")),
                "base_wage": self._to_float(data.get("base_wage")),
                "saturday_150": self._to_float(data.get("saturday_150")),
                "gift_value": self._to_float(data.get("gift_value")),
                "severance_extra": self._to_float(data.get("severance_extra"))
            },
            "hours_breakdown": {
                "regular_hours": self._to_float(data.get("regular_hours")),
                # Parser לא מסכם - רק מחזיר null
                # Analyzer יחלץ ויסכם את כל שעות 150% ו-125% מ-raw_data
                "hours_150": None,
                "hours_125": None
            },
            "raw_data": data  # כל הנתונים הגולמיים כולל _original_text
        }

    def _extract_sick_days_with_ai(self, text: str) -> Optional[float]:
        """
        משתמש בסוכן AI לחילוץ ימי מחלה מהתלוש
        """
        try:
            import os
            from anthropic import Anthropic

            # Check if API key exists
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("[AI-Parser] No ANTHROPIC_API_KEY found, skipping AI extraction")
                return None

            client = Anthropic(api_key=api_key)

            # בנה prompt לסוכן
            prompt = f"""אתה parser חכם לתלושי שכר בעברית.

קרא את התלוש הבא ומצא את הערך של "ימי מחלה" או "יתרה חדשה" בסעיף "חשבון מחלה".

חפש בסעיף "חשבון מחלה" את השדות הבאים:
1. יתרה קודמת
2. צבירה (ח.ז.צ)
3. יתרה חדשה

המספר הכי רלוונטי הוא "יתרה חדשה".

טקסט התלוש:
{text[:2000]}

תשובה: החזר **רק** את המספר של ימי המחלה (יתרה חדשה), בלי שום טקסט נוסף.
אם לא מצאת - החזר "null".

דוגמה: אם יתרת ימי המחלה החדשה היא 75.52, החזר רק: 75.52"""

            # Call Claude
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",  # Haiku 3.5 - fast and cheap for parsing
                max_tokens=50,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            answer = response.content[0].text.strip()
            print(f"[AI-Parser] Claude response for sick_days: {answer}")

            # Try to convert to float
            if answer and answer.lower() not in ['null', 'none', 'לא נמצא']:
                try:
                    return float(answer.replace(',', ''))
                except ValueError:
                    print(f"[AI-Parser] Could not convert '{answer}' to float")
                    return None

            return None

        except Exception as e:
            print(f"[AI-Parser] Error extracting sick_days with AI: {e}")
            return None
