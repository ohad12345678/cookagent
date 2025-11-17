"""
Learning Manager - ניהול למידה עבור כל הסוכנים
שומר את תוצאות עבודת הסוכנים ב-AgentLearning table
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import AgentLearning


class LearningManager:
    """מנהל למידה לכל הסוכנים"""

    def __init__(self, db: Session):
        self.db = db

    def save_agent_execution(
        self,
        agent_name: str,
        task_type: str,
        input_data: Dict[str, Any],
        output_data: Any,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        שומר תוצאות ביצוע משימה של סוכן

        Args:
            agent_name: שם הסוכן (parser, validator, analyzer, designer, chatbot_manager)
            task_type: סוג המשימה (parse, validate, analyze, design, coordinate)
            input_data: הקלט שהסוכן קיבל
            output_data: הפלט שהסוכן החזיר
            success: האם המשימה הצליחה
            metadata: מטא-דאטה נוספת

        Returns:
            ID של הרשומה שנוצרה
        """
        try:
            learning_entry = AgentLearning(
                learning_type=f"{agent_name}_{task_type}",
                context={
                    "agent_name": agent_name,
                    "task_type": task_type,
                    "input_data": input_data,
                    "success": success,
                    "metadata": metadata or {}
                },
                learned_data={
                    "output": str(output_data)[:10000],  # Limit size
                    "timestamp": datetime.utcnow().isoformat()
                },
                confidence=1.0 if success else 0.5,
                times_used=1,
                success_rate=1.0 if success else 0.0,
                active=True
            )

            self.db.add(learning_entry)
            self.db.commit()
            self.db.refresh(learning_entry)

            print(f"[Learning] Saved {agent_name} execution: {task_type} (ID: {learning_entry.id})")
            return learning_entry.id

        except Exception as e:
            print(f"[Learning] Error saving agent execution: {e}")
            self.db.rollback()
            return -1

    def get_agent_history(
        self,
        agent_name: str,
        task_type: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """
        מחזיר היסטוריית למידה של סוכן

        Args:
            agent_name: שם הסוכן
            task_type: סוג משימה (אופציונלי)
            limit: מספר תוצאות מקסימלי

        Returns:
            רשימת ביצועים קודמים
        """
        try:
            query = self.db.query(AgentLearning).filter(
                AgentLearning.active == True
            )

            # Filter by agent
            if task_type:
                query = query.filter(AgentLearning.learning_type == f"{agent_name}_{task_type}")
            else:
                query = query.filter(AgentLearning.learning_type.like(f"{agent_name}_%"))

            # Get recent entries
            results = query.order_by(AgentLearning.timestamp.desc()).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "learning_type": r.learning_type,
                    "context": r.context,
                    "learned_data": r.learned_data,
                    "confidence": r.confidence,
                    "times_used": r.times_used,
                    "success_rate": r.success_rate
                }
                for r in results
            ]

        except Exception as e:
            print(f"[Learning] Error getting agent history: {e}")
            return []

    def update_learning_success(self, learning_id: int, was_successful: bool):
        """
        מעדכן את שיעור ההצלחה של למידה

        Args:
            learning_id: ID של רשומת הלמידה
            was_successful: האם השימוש הצליח
        """
        try:
            learning = self.db.query(AgentLearning).filter(AgentLearning.id == learning_id).first()

            if learning:
                learning.times_used += 1
                total_successes = learning.success_rate * (learning.times_used - 1)
                total_successes += 1 if was_successful else 0
                learning.success_rate = total_successes / learning.times_used

                self.db.commit()
                print(f"[Learning] Updated learning {learning_id}: success_rate={learning.success_rate:.2f}")

        except Exception as e:
            print(f"[Learning] Error updating learning success: {e}")
            self.db.rollback()

    def get_best_practices(self, agent_name: str, task_type: str, limit: int = 5) -> list:
        """
        מחזיר את הביצועים הטובים ביותר (למידה מהצלחות)

        Args:
            agent_name: שם הסוכן
            task_type: סוג המשימה
            limit: מספר דוגמאות

        Returns:
            רשימת ביצועים מוצלחים
        """
        try:
            results = self.db.query(AgentLearning).filter(
                AgentLearning.learning_type == f"{agent_name}_{task_type}",
                AgentLearning.active == True,
                AgentLearning.success_rate >= 0.8  # Only highly successful
            ).order_by(
                AgentLearning.success_rate.desc(),
                AgentLearning.times_used.desc()
            ).limit(limit).all()

            return [
                {
                    "context": r.context,
                    "learned_data": r.learned_data,
                    "success_rate": r.success_rate,
                    "times_used": r.times_used
                }
                for r in results
            ]

        except Exception as e:
            print(f"[Learning] Error getting best practices: {e}")
            return []
