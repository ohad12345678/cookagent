"""
Parser Improver Module - מודול לשיפור ה-PDF parser מפידבק
"""
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class ParserImprover:
    """
    משפר את יכולות ה-PDF parsing בהתבסס על תיקוני משתמשים
    """

    def __init__(self, pdf_parser, db_session):
        self.parser = pdf_parser
        self.db = db_session

    def learn_from_correction(self, payslip_id: int, field_name: str,
                             correct_value: Any, original_value: Any) -> Dict:
        """
        למד מתיקון של שדה בודד

        Args:
            payslip_id: מזהה התלוש
            field_name: שם השדה שתוקן
            correct_value: הערך הנכון
            original_value: הערך השגוי המקורי
        """
        from backend.app.database import SessionLocal
        db = SessionLocal()

        try:
            # קבל את התלוש והטקסט הגולמי
            payslip = db.execute(
                "SELECT * FROM payslips WHERE id = :id",
                {"id": payslip_id}
            ).fetchone()

            if not payslip:
                return {"success": False, "error": "Payslip not found"}

            raw_text = payslip['raw_text'] if payslip['raw_text'] else ""

            # מצא היכן הערך הנכון מופיע בטקסט
            value_locations = self._find_value_in_text(str(correct_value), raw_text)

            patterns_added = 0
            for location in value_locations[:3]:  # רק 3 הראשונים
                # חלץ קונטקסט
                context = self._extract_context(raw_text, location, window=50)

                # צור דפוס משופר
                new_pattern = self._generate_pattern(
                    field_name, correct_value, context
                )

                if new_pattern:
                    # שמור דפוס ב-DB
                    self._store_parsing_pattern(new_pattern, db)
                    patterns_added += 1

            # עדכן את הדפוסים של ה-Parser (אם הוא נטען)
            if hasattr(self.parser, 'patterns') and field_name in self.parser.patterns:
                if new_pattern and new_pattern['regex']:
                    self.parser.patterns[field_name].insert(0, new_pattern['regex'])

            # רשום את הלמידה
            db.execute("""
                INSERT INTO learning_history (learning_type, after_state, triggered_by)
                VALUES ('parser_correction', :state, 'user_feedback')
            """, {
                "state": json.dumps({
                    "payslip_id": payslip_id,
                    "field_name": field_name,
                    "original": str(original_value),
                    "corrected": str(correct_value),
                    "patterns_learned": patterns_added
                })
            })
            db.commit()

            return {
                "success": True,
                "patterns_learned": patterns_added,
                "field": field_name
            }

        finally:
            db.close()

    def improve_splitting(self, file_path: str, user_correction: Dict) -> Dict:
        """
        למד פיצול טוב יותר של תלושים מתיקוני משתמש

        Args:
            file_path: נתיב הקובץ
            user_correction: {
                "detected_count": מספר שזוהה,
                "actual_count": מספר אמיתי,
                "split_points": נקודות פיצול,
                "split_method": שיטת פיצול
            }
        """
        from backend.app.database import SessionLocal
        db = SessionLocal()

        try:
            # קרא את הטקסט
            text = self.parser.extract_text(file_path) if hasattr(self.parser, 'extract_text') else ""

            detected = user_correction["detected_count"]
            actual = user_correction["actual_count"]

            patterns_learned = []

            if actual > detected:
                # החמצנו תלושים - למד מפרידים חדשים
                split_points = user_correction.get("split_points", [])

                for point in split_points[:5]:  # רק 5 ראשונים
                    # חלץ דפוס בנקודת הפיצול
                    context = text[max(0, point-100):min(len(text), point+100)]
                    separator_pattern = self._extract_separator_pattern(context)

                    if separator_pattern:
                        # שמור כדפוס פיצול חדש
                        pattern_data = {
                            "pattern_type": "payslip_separator",
                            "regex": separator_pattern,
                            "description": f"Splits {actual} payslips",
                            "confidence": 0.7
                        }
                        self._store_parsing_pattern(pattern_data, db)
                        patterns_learned.append(separator_pattern)

            elif actual < detected:
                # פיצלנו יותר מדי - סמן דפוסים כפחות אמינים
                self._downgrade_split_patterns(detected, actual, db)

            # שמור רשומת שיפור
            db.execute("""
                INSERT INTO split_improvements
                (original_file_path, detected_payslip_count, actual_payslip_count,
                 split_method, user_corrections, learned_patterns)
                VALUES (:path, :detected, :actual, :method, :corrections, :patterns)
            """, {
                "path": file_path,
                "detected": detected,
                "actual": actual,
                "method": user_correction.get("split_method", "unknown"),
                "corrections": json.dumps(user_correction),
                "patterns": json.dumps(patterns_learned)
            })
            db.commit()

            return {
                "success": True,
                "patterns_learned": len(patterns_learned),
                "improvement": f"From {detected} to {actual} payslips"
            }

        finally:
            db.close()

    def _find_value_in_text(self, value: str, text: str) -> List[int]:
        """
        מצא את כל המיקומים שבהם הערך מופיע בטקסט
        """
        locations = []
        search_str = str(value).replace(",", "")

        # חפש את הערך כפי שהוא
        start = 0
        while True:
            idx = text.find(search_str, start)
            if idx == -1:
                break
            locations.append(idx)
            start = idx + 1

        # חפש גם עם פסיקים
        if "." in search_str:
            search_with_comma = search_str.replace(".", ",")
            start = 0
            while True:
                idx = text.find(search_with_comma, start)
                if idx == -1:
                    break
                locations.append(idx)
                start = idx + 1

        return locations

    def _extract_context(self, text: str, position: int, window: int = 50) -> str:
        """
        חלץ קונטקסט סביב מיקום
        """
        start = max(0, position - window)
        end = min(len(text), position + window + len(str(position)))
        return text[start:end]

    def _generate_pattern(self, field_name: str, value: Any, context: str) -> Dict:
        """
        צור דפוס regex מהקונטקסט
        """
        value_str = str(value).replace(",", "")

        # מצא את מיקום הערך בקונטקסט
        idx = context.find(value_str)
        if idx == -1:
            return None

        # חלץ טקסט לפני ואחרי
        before = context[:idx].strip()[-30:]
        after = context[idx+len(value_str):].strip()[:30]

        # נקה וצור דפוס
        before_clean = re.escape(before[-15:]) if len(before) > 15 else ""
        after_clean = re.escape(after[:15]) if len(after) > 15 else ""

        # דפוס גנרי למספר
        number_pattern = r"([\d,]+\.?\d*)"

        regex = f"{before_clean}\\s*{number_pattern}"
        if after_clean:
            regex += f"\\s*{after_clean}"

        return {
            "field_name": field_name,
            "pattern_type": "field_extraction",
            "regex": regex,
            "confidence": 0.8,
            "learned_from": "user_correction",
            "description": f"Pattern for {field_name}"
        }

    def _store_parsing_pattern(self, pattern: Dict, db) -> None:
        """
        שמור דפוס במסד הנתונים
        """
        db.execute("""
            INSERT INTO parsing_patterns
            (pattern_type, pattern_regex, pattern_description, field_name,
             confidence_score, created_from_feedback, active)
            VALUES (:type, :regex, :desc, :field, :conf, TRUE, :active)
        """, {
            "type": pattern.get("pattern_type", "field_extraction"),
            "regex": pattern.get("regex", ""),
            "desc": pattern.get("description", ""),
            "field": pattern.get("field_name"),
            "conf": pattern.get("confidence", 0.7),
            "active": pattern.get("confidence", 0.7) > 0.6
        })
        db.commit()

    def _extract_separator_pattern(self, context: str) -> Optional[str]:
        """
        חלץ דפוס שמציין גבול בין תלושים
        """
        # דפוסים נפוצים למפרידים
        patterns = [
            r"מספר העובד",
            r"דבועה רפסמ",  # מספר עובד הפוך
            r"שם העובד",
            r"דבועה םש",  # שם העובד הפוך
            r"תלוש שכר",
            r"רכש שולת",  # תלוש שכר הפוך
            r"Payslip",
            r"-{5,}",  # לפחות 5 מקפים
            r"={5,}",  # לפחות 5 שווים
            r"_{5,}",  # לפחות 5 קווים תחתונים
            r"Page \d+",  # מספר עמוד
        ]

        for pattern in patterns:
            if re.search(pattern, context):
                # מצאנו דפוס מפריד
                return pattern

        # נסה למצוא דפוס כללי יותר
        if "מספר" in context or "עובד" in context:
            return r".{0,50}(מספר|עובד).{0,50}"

        return None

    def _downgrade_split_patterns(self, detected: int, actual: int, db) -> None:
        """
        הורד דירוג של דפוסי פיצול שגורמים לפיצול-יתר
        """
        # הורד confidence של דפוסים פעילים
        db.execute("""
            UPDATE parsing_patterns
            SET confidence_score = confidence_score * 0.8,
                failure_count = failure_count + 1,
                active = CASE WHEN confidence_score * 0.8 < 0.5 THEN FALSE ELSE active END
            WHERE pattern_type = 'payslip_separator'
              AND active = TRUE
        """)
        db.commit()