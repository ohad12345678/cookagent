"""
Knowledge Base - מאגר ידע דינמי שלומד מ-feedback
שומר patterns, כללים, ו-corrections שהמשתמש מספק
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings


class KnowledgeBase:
    """
    מאגר ידע שמתעדכן מ-feedback
    משתמש ב-ChromaDB לאחסון וקטורי של patterns
    """

    def __init__(self, base_path: str = "data/knowledge_base"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # קבצי ידע
        self.rules_file = self.base_path / "validation_rules.json"
        self.patterns_file = self.base_path / "learned_patterns.json"
        self.corrections_file = self.base_path / "corrections_history.json"

        # טען ידע קיים או צור חדש
        self.validation_rules = self._load_json(self.rules_file, self._default_rules())
        self.learned_patterns = self._load_json(self.patterns_file, {"patterns": []})
        self.corrections_history = self._load_json(self.corrections_file, {"corrections": []})

        # Vector DB לחיפוש סמנטי של patterns
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=str(self.base_path / "chroma_db"),
            anonymized_telemetry=False
        ))

        try:
            self.collection = self.chroma_client.get_collection("payslip_patterns")
        except:
            self.collection = self.chroma_client.create_collection(
                name="payslip_patterns",
                metadata={"description": "Learned patterns from payslip analysis"}
            )

    def _default_rules(self) -> Dict:
        """כללי בסיס לולידציה"""
        return {
            "salary_rules": {
                "minimum_wage": 5300,  # שכר מינימום 2024
                "max_monthly_salary": 100000,  # סף סביר עליון
                "overtime_multiplier": [1.25, 1.5, 2.0]  # שעות נוספות
            },
            "tax_rules": {
                "min_tax_rate": 0.0,
                "max_tax_rate": 0.50,  # 50% מקסימום
                "bituach_leumi_rate": 0.12,  # ביטוח לאומי
                "bituach_briut_rate": 0.05   # ביטוח בריאות
            },
            "deduction_rules": {
                "pension_min": 0.0,
                "pension_max": 0.075,  # 7.5% פנסיה
                "allowed_deductions": ["pension", "health_insurance", "tax", "bituach_leumi"]
            },
            "ignored_issues": [],  # בעיות שהמשתמש אמר להתעלם
            "false_positives": []  # דברים שזוהו כשגיאה אבל לא
        }

    def _load_json(self, filepath: Path, default: Dict) -> Dict:
        """טען JSON או החזר ברירת מחדל"""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save_json(self, filepath: Path, data: Dict):
        """שמור JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_feedback(self,
                     feedback_type: str,
                     context: Dict[str, Any],
                     user_feedback: str,
                     correction: Optional[Dict] = None):
        """
        הוסף feedback מהמשתמש

        Args:
            feedback_type: "false_positive", "missing_issue", "pattern", "rule_update"
            context: ההקשר (תלוש, ממצא וכו')
            user_feedback: מה המשתמש אמר
            correction: התיקון המבוקש
        """
        timestamp = datetime.now().isoformat()

        feedback_entry = {
            "timestamp": timestamp,
            "type": feedback_type,
            "context": context,
            "user_feedback": user_feedback,
            "correction": correction
        }

        # שמור בהיסטוריה
        self.corrections_history["corrections"].append(feedback_entry)
        self._save_json(self.corrections_file, self.corrections_history)

        # עדכן את הכללים בהתאם
        if feedback_type == "false_positive":
            self._handle_false_positive(context, user_feedback)
        elif feedback_type == "missing_issue":
            self._handle_missing_issue(context, user_feedback)
        elif feedback_type == "pattern":
            self._handle_pattern_learning(context, user_feedback)
        elif feedback_type == "rule_update":
            self._handle_rule_update(context, correction)

        # הוסף ל-vector DB
        self.collection.add(
            documents=[user_feedback],
            metadatas=[{"type": feedback_type, "timestamp": timestamp}],
            ids=[f"feedback_{timestamp}"]
        )

    def _handle_false_positive(self, context: Dict, feedback: str):
        """טפל בזיהוי מוטעה - דבר שזוהה כשגיאה אבל לא"""
        issue_pattern = context.get("issue_description", "")
        if issue_pattern:
            self.validation_rules["false_positives"].append({
                "pattern": issue_pattern,
                "reason": feedback,
                "added": datetime.now().isoformat()
            })
            self._save_json(self.rules_file, self.validation_rules)

    def _handle_missing_issue(self, context: Dict, feedback: str):
        """טפל בבעיה שלא זוהתה אבל צריכה הייתה"""
        new_pattern = {
            "description": feedback,
            "context": context,
            "severity": "medium",
            "added": datetime.now().isoformat()
        }
        self.learned_patterns["patterns"].append(new_pattern)
        self._save_json(self.patterns_file, self.learned_patterns)

    def _handle_pattern_learning(self, context: Dict, feedback: str):
        """למד pattern חדש"""
        pattern = {
            "pattern": feedback,
            "example": context,
            "learned_from": "user_feedback",
            "timestamp": datetime.now().isoformat()
        }
        self.learned_patterns["patterns"].append(pattern)
        self._save_json(self.patterns_file, self.learned_patterns)

    def _handle_rule_update(self, context: Dict, correction: Dict):
        """עדכן כלל קיים"""
        if correction:
            # עדכן את הכללים בהתאם לתיקון
            rule_path = correction.get("rule_path", [])
            new_value = correction.get("new_value")

            if rule_path and new_value is not None:
                current = self.validation_rules
                for key in rule_path[:-1]:
                    current = current.setdefault(key, {})
                current[rule_path[-1]] = new_value
                self._save_json(self.rules_file, self.validation_rules)

    def should_ignore_issue(self, issue_description: str) -> bool:
        """בדוק אם צריך להתעלם מבעיה לפי learning"""
        # בדוק false positives
        for fp in self.validation_rules.get("false_positives", []):
            if fp["pattern"].lower() in issue_description.lower():
                return True

        # בדוק ignored issues
        for ignored in self.validation_rules.get("ignored_issues", []):
            if ignored.lower() in issue_description.lower():
                return True

        return False

    def find_similar_patterns(self, query: str, n_results: int = 5) -> List[Dict]:
        """חפש patterns דומים באמצעות vector search"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            if results and results['documents']:
                return [
                    {
                        "feedback": doc,
                        "metadata": meta
                    }
                    for doc, meta in zip(results['documents'][0], results['metadatas'][0])
                ]
        except:
            pass

        return []

    def get_learning_summary(self) -> Dict[str, Any]:
        """קבל סיכום של מה שנלמד"""
        return {
            "total_corrections": len(self.corrections_history["corrections"]),
            "false_positives_learned": len(self.validation_rules.get("false_positives", [])),
            "patterns_learned": len(self.learned_patterns["patterns"]),
            "ignored_issues": len(self.validation_rules.get("ignored_issues", [])),
            "last_update": self.corrections_history["corrections"][-1]["timestamp"]
                          if self.corrections_history["corrections"] else None
        }

    def get_validation_rules(self) -> Dict:
        """החזר את כללי הולידציה הנוכחיים"""
        return self.validation_rules

    def get_learned_patterns(self) -> List[Dict]:
        """החזר patterns שנלמדו"""
        return self.learned_patterns["patterns"]
