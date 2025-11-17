"""
Feedback Collector - אוסף ומעבד feedback מהמשתמש
מעביר למידה לכל הסוכנים
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum


class FeedbackType(Enum):
    """סוגי feedback שניתן לקבל"""
    FALSE_POSITIVE = "false_positive"  # זוהה כשגיאה אבל לא
    MISSING_ISSUE = "missing_issue"    # בעיה לא זוהתה
    PATTERN = "pattern"                 # pattern חדש ללמוד
    RULE_UPDATE = "rule_update"        # עדכון כלל
    REPORT_IMPROVEMENT = "report_improvement"  # שיפור בדוח
    PARSING_ERROR = "parsing_error"    # שגיאה בפרסור


class FeedbackCollector:
    """
    אוסף feedback ומעדכן את הסוכנים
    """

    def __init__(self, knowledge_base, history_path: str = "data/feedback_history"):
        self.knowledge_base = knowledge_base
        self.history_path = Path(history_path)
        self.history_path.mkdir(parents=True, exist_ok=True)

        # קובץ session נוכחי
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.history_path / f"session_{self.session_id}.json"

        self.session_feedback = []

    def collect_feedback(self,
                        feedback_type: FeedbackType,
                        agent_name: str,
                        context: Dict[str, Any],
                        user_input: str,
                        correction: Optional[Dict] = None) -> Dict[str, Any]:
        """
        אסוף feedback מהמשתמש

        Args:
            feedback_type: סוג ה-feedback
            agent_name: שם הסוכן שקיבל feedback
            context: הקשר (תלוש, ממצא וכו')
            user_input: מה המשתמש אמר
            correction: התיקון (אופציונלי)

        Returns:
            תגובה על איך ה-feedback עובד
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": feedback_type.value,
            "agent": agent_name,
            "context": context,
            "user_input": user_input,
            "correction": correction,
            "processed": False
        }

        # הוסף ל-session
        self.session_feedback.append(feedback_entry)
        self._save_session()

        # עבד את ה-feedback
        result = self._process_feedback(feedback_entry)

        # עדכן שעובד
        feedback_entry["processed"] = True
        feedback_entry["processing_result"] = result
        self._save_session()

        return result

    def _process_feedback(self, feedback: Dict) -> Dict[str, Any]:
        """עבד feedback והחל על הסוכנים"""
        feedback_type = FeedbackType(feedback["type"])
        agent = feedback["agent"]
        context = feedback["context"]
        user_input = feedback["user_input"]
        correction = feedback.get("correction")

        result = {
            "status": "processed",
            "updates": [],
            "message": ""
        }

        # טפל לפי סוג
        if feedback_type == FeedbackType.FALSE_POSITIVE:
            self.knowledge_base.add_feedback(
                "false_positive",
                context,
                user_input,
                None
            )
            result["updates"].append(f"{agent} לא יזהה את זה כשגיאה יותר")
            result["message"] = f"✓ למדתי: '{context.get('issue_description', 'זה')}' זה לא שגיאה"

        elif feedback_type == FeedbackType.MISSING_ISSUE:
            self.knowledge_base.add_feedback(
                "missing_issue",
                context,
                user_input,
                None
            )
            result["updates"].append(f"{agent} יחפש את זה בעתיד")
            result["message"] = f"✓ למדתי לחפש: {user_input}"

        elif feedback_type == FeedbackType.PATTERN:
            self.knowledge_base.add_feedback(
                "pattern",
                context,
                user_input,
                None
            )
            result["updates"].append("Pattern חדש נוסף למאגר")
            result["message"] = f"✓ למדתי pattern חדש: {user_input}"

        elif feedback_type == FeedbackType.RULE_UPDATE:
            if correction:
                self.knowledge_base.add_feedback(
                    "rule_update",
                    context,
                    user_input,
                    correction
                )
                result["updates"].append(f"כלל עודכן: {correction.get('rule_path')}")
                result["message"] = f"✓ עדכנתי את הכלל"
            else:
                result["status"] = "error"
                result["message"] = "צריך לספק correction לעדכון כלל"

        elif feedback_type == FeedbackType.REPORT_IMPROVEMENT:
            # שמור feedback על הדוח
            self.knowledge_base.add_feedback(
                "pattern",
                {"report_type": context.get("report_type")},
                user_input,
                None
            )
            result["updates"].append("הדוחות הבאים ישתפרו")
            result["message"] = f"✓ אשתפר בדוחות: {user_input}"

        elif feedback_type == FeedbackType.PARSING_ERROR:
            # שמור feedback על parsing
            self.knowledge_base.add_feedback(
                "pattern",
                context,
                f"Parsing issue: {user_input}",
                correction
            )
            result["updates"].append("Parser ישתפר")
            result["message"] = f"✓ אתקן את ה-parsing"

        return result

    def _save_session(self):
        """שמור session נוכחי"""
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": self.session_id,
                "started": self.session_feedback[0]["timestamp"] if self.session_feedback else None,
                "feedback_count": len(self.session_feedback),
                "feedback": self.session_feedback
            }, f, ensure_ascii=False, indent=2)

    def get_session_summary(self) -> Dict[str, Any]:
        """קבל סיכום session נוכחי"""
        return {
            "session_id": self.session_id,
            "total_feedback": len(self.session_feedback),
            "by_type": self._count_by_type(),
            "by_agent": self._count_by_agent()
        }

    def _count_by_type(self) -> Dict[str, int]:
        """ספור feedback לפי סוג"""
        counts = {}
        for fb in self.session_feedback:
            fb_type = fb["type"]
            counts[fb_type] = counts.get(fb_type, 0) + 1
        return counts

    def _count_by_agent(self) -> Dict[str, int]:
        """ספור feedback לפי סוכן"""
        counts = {}
        for fb in self.session_feedback:
            agent = fb["agent"]
            counts[agent] = counts.get(agent, 0) + 1
        return counts

    def show_learning_history(self, limit: int = 10) -> List[Dict]:
        """הצג היסטוריית למידה אחרונה"""
        return self.session_feedback[-limit:] if self.session_feedback else []

    def suggest_improvements(self) -> List[str]:
        """הצע שיפורים בהתאם ל-feedback שנאסף"""
        suggestions = []

        type_counts = self._count_by_type()

        if type_counts.get("false_positive", 0) > 2:
            suggestions.append("יש הרבה false positives - אולי צריך להרפות את כללי הולידציה")

        if type_counts.get("missing_issue", 0) > 2:
            suggestions.append("יש בעיות שלא מזוהות - אולי צריך חוקים חזקים יותר")

        if type_counts.get("parsing_error", 0) > 1:
            suggestions.append("יש בעיות parsing - אולי צריך לשפר את ה-Parser")

        return suggestions
