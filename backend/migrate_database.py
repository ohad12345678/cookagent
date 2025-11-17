"""
Database Migration Script
מעדכן את המסד נתונים עם השדות החדשים ומעתיק נתונים מ-parsed_data
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, get_db, Payslip, Employee, engine
from sqlalchemy import text

def run_migration():
    """הרצת migration"""
    print("🔄 Starting database migration...")

    # Step 1: Add new columns to payslips table
    print("\n📊 Step 1: Adding new columns to payslips table...")

    with engine.connect() as conn:
        try:
            # Check if columns exist (PostgreSQL syntax)
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'payslips'
            """))
            existing_columns = {row[0] for row in result}

            columns_to_add = {
                'final_payment': 'DOUBLE PRECISION',
                'work_hours': 'DOUBLE PRECISION',
                'overtime_hours': 'DOUBLE PRECISION',
                'vacation_days': 'DOUBLE PRECISION',
                'sick_days': 'DOUBLE PRECISION'
            }

            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    print(f"  ➕ Adding column: {col_name}")
                    conn.execute(text(f"ALTER TABLE payslips ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                else:
                    print(f"  ✓ Column already exists: {col_name}")

        except Exception as e:
            print(f"❌ Error adding columns: {e}")
            return False

    # Step 2: Create employees table if not exists
    print("\n👥 Step 2: Creating employees table...")
    try:
        init_db()  # This creates all tables including employees
        print("✓ Employees table created/verified")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

    # Step 3: Update existing payslips with data from parsed_data
    print("\n🔄 Step 3: Updating existing payslips from parsed_data...")

    db = next(get_db())
    try:
        payslips = db.query(Payslip).all()
        print(f"Found {len(payslips)} payslips to update")

        updated_count = 0
        for payslip in payslips:
            if payslip.parsed_data:
                updated = False

                # Extract data from parsed_data
                salary = payslip.parsed_data.get('salary', {})

                if salary.get('final_payment') and not payslip.final_payment:
                    payslip.final_payment = salary['final_payment']
                    updated = True

                if payslip.parsed_data.get('work_hours') and not payslip.work_hours:
                    payslip.work_hours = payslip.parsed_data['work_hours']
                    updated = True

                if payslip.parsed_data.get('overtime_hours') and not payslip.overtime_hours:
                    payslip.overtime_hours = payslip.parsed_data['overtime_hours']
                    updated = True

                if payslip.parsed_data.get('vacation_days') and not payslip.vacation_days:
                    payslip.vacation_days = payslip.parsed_data['vacation_days']
                    updated = True

                if payslip.parsed_data.get('sick_days') and not payslip.sick_days:
                    payslip.sick_days = payslip.parsed_data['sick_days']
                    updated = True

                # Update employee info
                employee_data = payslip.parsed_data.get('employee', {})
                if employee_data.get('name') and not payslip.employee_name:
                    payslip.employee_name = employee_data['name']
                    updated = True

                if employee_data.get('department') and not payslip.department:
                    payslip.department = employee_data['department']
                    updated = True

                # Update salary fields
                if salary.get('gross') and not payslip.gross_salary:
                    payslip.gross_salary = salary['gross']
                    updated = True

                if salary.get('base') and not payslip.base_salary:
                    payslip.base_salary = salary['base']
                    updated = True

                if updated:
                    updated_count += 1

        db.commit()
        print(f"✅ Updated {updated_count} payslips successfully")

    except Exception as e:
        print(f"❌ Error updating payslips: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    # Step 4: Create employee records from payslips
    print("\n👤 Step 4: Creating employee records...")

    db = next(get_db())
    try:
        payslips = db.query(Payslip).all()

        # Get unique employee IDs
        employee_map = {}
        for payslip in payslips:
            emp_id = payslip.employee_id
            if emp_id and emp_id not in employee_map:
                # Get name from parsed_data or use "לא זוהה"
                emp_name = None
                if payslip.parsed_data:
                    employee_data = payslip.parsed_data.get('employee', {})
                    emp_name = employee_data.get('name')

                if not emp_name:
                    emp_name = payslip.employee_name or f"עובד {emp_id}"

                department = payslip.department
                if not department and payslip.parsed_data:
                    employee_data = payslip.parsed_data.get('employee', {})
                    department = employee_data.get('department')

                employee_map[emp_id] = {
                    'name': emp_name,
                    'department': department
                }

        # Create employee records
        created_count = 0
        for emp_id, emp_data in employee_map.items():
            # Check if employee already exists
            existing = db.query(Employee).filter(Employee.employee_id == emp_id).first()
            if not existing:
                employee = Employee(
                    employee_id=emp_id,
                    employee_name=emp_data['name'],
                    department=emp_data['department']
                )
                db.add(employee)
                created_count += 1
                print(f"  ➕ Created employee: {emp_id} - {emp_data['name']}")

        db.commit()
        print(f"✅ Created {created_count} employee records")

    except Exception as e:
        print(f"❌ Error creating employees: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    print("\n✅ Migration completed successfully!")
    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
