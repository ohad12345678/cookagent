"""
PDF Reader Tool - כלי לקריאת קבצי PDF באמצעות PyPDF2
זוהי דוגמה איך ליצור כלי מותאם אישית ב-CrewAI
"""
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import PyPDF2
from pathlib import Path


class PDFReaderInput(BaseModel):
    """Input schema for PDFReaderTool."""
    file_path: str = Field(..., description="נתיב מלא לקובץ PDF")


class PDFReaderTool(BaseTool):
    name: str = "PDF Reader"
    description: str = (
        "קורא קובץ PDF ומחזיר את כל הטקסט שבו. "
        "שימוש: העבר נתיב מלא לקובץ PDF (למשל: /path/to/payslip.pdf)"
    )
    args_schema: Type[BaseModel] = PDFReaderInput

    def _run(self, file_path: str) -> str:
        """
        קורא קובץ PDF ומחזיר את התוכן

        Args:
            file_path: נתיב לקובץ PDF

        Returns:
            str: הטקסט המלא מכל הדפים ב-PDF
        """
        try:
            pdf_path = Path(file_path)

            if not pdf_path.exists():
                return f"❌ שגיאה: הקובץ {file_path} לא נמצא"

            if not pdf_path.suffix.lower() == '.pdf':
                return f"❌ שגיאה: {file_path} אינו קובץ PDF"

            # פתיחת קובץ PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                # חילוץ טקסט מכל הדפים
                full_text = []
                full_text.append(f"📄 קובץ PDF: {pdf_path.name}")
                full_text.append(f"📊 מספר דפים: {num_pages}\n")
                full_text.append("="*80)

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()

                    full_text.append(f"\n🔖 דף {page_num + 1}/{num_pages}")
                    full_text.append("-"*80)
                    full_text.append(text)
                    full_text.append("-"*80)

                return "\n".join(full_text)

        except Exception as e:
            return f"❌ שגיאה בקריאת PDF: {str(e)}"


# יצירת instance של הכלי
pdf_reader_tool = PDFReaderTool()
