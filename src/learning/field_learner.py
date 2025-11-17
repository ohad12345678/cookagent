"""
Field Learner Module - מודול ללמידת שדות חדשים מפידבק משתמשים
"""
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class FieldLearner:
    """
    לומד שדות חדשים מתיקוני משתמשים ומשפר דפוסי חילוץ
    """

    def __init__(self, db_session):
        self.db = db_session
        self.confidence_threshold = 0.7
        self.hebrew_translations = {
            "bonus": ["בונוס", "פרמיה", "מענק"],
            "overtime": ["שעות נוספות", 'ש"נ', "נוספות"],
            "travel": ["נסיעות", "דמי נסיעה", "החזר נסיעות"],
            "meals": ["ארוחות", "דמי אוכל", "סעודות"],
            "phone": ["טלפון", "סלולר", "תקשורת"],
            "clothing": ["ביגוד", "דמי ביגוד"],
            "vacation": ["חופשה", "ימי חופש", "פדיון חופשה"],
            "sick_leave": ["מחלה", "ימי מחלה", "דמי מחלה"],
            "pension": ["פנסיה", "קרן פנסיה", "הפרשה לפנסיה"],
            "education_fund": ["קרן השתלמות", "השתלמות"],
            "car": ["רכב", "אחזקת רכב", "דמי רכב"]
        }

    def learn_new_field(self, field_name: str, field_value: Any,
                       context: str, payslip_text: str) -> Dict:
        """
        למד שדה חדש מתיקון משתמש

        Args:
            field_name: שם השדה
            field_value: הערך הנכון
            context: טקסט סביב השדה
            payslip_text: הטקסט המלא של התלוש
        """
        print(f"[FieldLearner] Learning new field: {field_name} = {field_value}")

        # 1. חלץ דפוסים מהקונטקסט
        patterns = self._extract_patterns(field_name, field_value, context, payslip_text)

        # 2. זהה את סוג השדה
        field_type = self._infer_field_type(field_value)

        # 3. סווג את השדה
        category = self._categorize_field(field_name)

        # 4. שמור או עדכן הגדרת שדה
        from backend.app.database import SessionLocal
        db = SessionLocal()

        try:
            # בדוק אם השדה קיים
            existing = db.execute(
                "SELECT * FROM field_definitions WHERE field_name = :name",
                {"name": field_name}
            ).fetchone()

            if existing:
                # עדכן שדה קיים
                new_patterns = self._merge_patterns(
                    json.loads(existing['extraction_patterns']) if existing['extraction_patterns'] else [],
                    patterns
                )

                db.execute("""
                    UPDATE field_definitions
                    SET extraction_patterns = :patterns,
                        occurrence_count = occurrence_count + 1,
                        last_seen = NOW(),
                        confidence_score = LEAST(confidence_score + 0.1, 1.0),
                        active = CASE WHEN confidence_score > 0.7 THEN TRUE ELSE FALSE END
                    WHERE field_name = :name
                """, {
                    "patterns": json.dumps(new_patterns),
                    "name": field_name
                })
            else:
                # צור שדה חדש
                db.execute("""
                    INSERT INTO field_definitions
                    (field_name, field_type, field_category, extraction_patterns,
                     learned_from_feedback, confidence_score, active)
                    VALUES (:name, :type, :category, :patterns, TRUE, 0.5, FALSE)
                """, {
                    "name": field_name,
                    "type": field_type,
                    "category": category,
                    "patterns": json.dumps(patterns)
                })

            db.commit()

            # רשום בהיסטוריית למידה
            db.execute("""
                INSERT INTO learning_history (learning_type, after_state, triggered_by)
                VALUES ('field', :state, 'user_feedback')
            """, {
                "state": json.dumps({
                    "field_name": field_name,
                    "field_value": str(field_value),
                    "patterns_count": len(patterns)
                })
            })
            db.commit()

            return {
                "success": True,
                "field_name": field_name,
                "field_type": field_type,
                "category": category,
                "patterns_learned": len(patterns),
                "confidence": 0.5 if not existing else min(float(existing['confidence_score']) + 0.1, 1.0)
            }

        finally:
            db.close()

    def _extract_patterns(self, field_name: str, value: Any,
                         context: str, full_text: str) -> List[Dict]:
        """
        חלץ דפוסי regex מהקונטקסט
        """
        patterns = []
        value_str = str(value).replace(",", "")

        # Pattern 1: תווית ואחריה ערך
        label_variations = self._generate_label_variations(field_name)
        for label in label_variations:
            patterns.append({
                "type": "label_value",
                "regex": f"{label}[:\\s]+([\\d,]+\\.?\\d*)",
                "confidence": 0.8,
                "example": f"{label}: {value}"
            })

        # Pattern 2: עברית הפוכה (נפוץ ב-PDFs)
        reversed_labels = [label[::-1] for label in label_variations]
        for rev_label in reversed_labels:
            patterns.append({
                "type": "reversed_hebrew",
                "regex": f"([\\d,]+\\.?\\d*)\\s+{rev_label}",
                "confidence": 0.6,
                "example": f"{value} {rev_label}"
            })

        # Pattern 3: מבוסס קונטקסט
        if value_str in context:
            idx = context.find(value_str)
            before = context[max(0, idx-30):idx].strip()
            after = context[idx+len(value_str):idx+len(value_str)+30].strip()

            if before:
                patterns.append({
                    "type": "context_before",
                    "regex": f"{re.escape(before[-20:])}\\s*([\\d,]+\\.?\\d*)",
                    "confidence": 0.7,
                    "context": before
                })

        # Pattern 4: מיקום בטבלה (אם יש מבנה טבלאי)
        if "|" in context or "\t" in context:
            patterns.append({
                "type": "table_structure",
                "regex": f"\\|?\\s*{field_name}\\s*\\|?\\s*([\\d,]+\\.?\\d*)\\s*\\|?",
                "confidence": 0.5
            })

        return patterns

    def _generate_label_variations(self, field_name: str) -> List[str]:
        """
        יצר וריאציות של שם השדה
        """
        variations = [field_name]

        # הוסף תרגומים לעברית
        field_lower = field_name.lower()
        for eng, heb_list in self.hebrew_translations.items():
            if eng in field_lower or field_lower in eng:
                variations.extend(heb_list)

        # הוסף וריאציות נפוצות
        if "_" in field_name:
            variations.append(field_name.replace("_", " "))
            variations.append(field_name.replace("_", "-"))

        return list(set(variations))

    def _infer_field_type(self, value: Any) -> str:
        """
        הסק את סוג השדה מהערך
        """
        if value is None:
            return "text"

        value_str = str(value)

        # בדוק אם זה מספר
        try:
            float(value_str.replace(",", ""))
            if "." in value_str:
                return "currency"
            return "number"
        except:
            pass

        # בדוק אם זה תאריך
        if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', value_str):
            return "date"
        if re.match(r'^\d{1,2}/\d{4}$', value_str):
            return "month_year"

        # אחרת זה טקסט
        return "text"

    def _categorize_field(self, field_name: str) -> str:
        """
        סווג שדה לקטגוריה
        """
        field_lower = field_name.lower()

        keywords = {
            "employee": ["name", "id", "department", "position", "שם", "מחלקה", "תפקיד"],
            "salary": ["salary", "wage", "base", "gross", "net", "משכורת", "ברוטו", "נטו", "בסיס"],
            "deduction": ["tax", "deduction", "insurance", "מס", "ניכוי", "ביטוח"],
            "addition": ["bonus", "overtime", "allowance", "בונוס", "נוספות", "תוספת"],
            "tax": ["tax", "bituach", "health", "מס", "ביטוח", "בריאות"],
            "time": ["hours", "days", "vacation", "שעות", "ימים", "חופשה"]
        }

        for category, words in keywords.items():
            if any(word in field_lower for word in words):
                return category

        return "other"

    def _merge_patterns(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """
        מזג דפוסים קיימים עם חדשים
        """
        # שמור את הדפוסים הקיימים
        merged = existing.copy()

        # הוסף דפוסים חדשים שלא קיימים
        existing_regexes = {p.get('regex') for p in existing}
        for pattern in new:
            if pattern.get('regex') not in existing_regexes:
                merged.append(pattern)

        # מיין לפי confidence
        merged.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        # החזר רק את 10 הטובים ביותר
        return merged[:10]