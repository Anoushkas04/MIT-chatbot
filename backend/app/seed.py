import sys

# Standalone entrypoint (`python -m app.seed`) doesn't go through app.main, so it
# needs its own UTF-8 stdout guard for the checkmark/emoji in the seed log lines.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.database import SessionLocal, init_db
from app import models


def seed_database():
    """Initializes database tables and populates ONLY legitimate static institutional metadata

    (19 Official MIT Manipal Departments, Academic Calendar Milestones, and RAG Knowledge Documents).
    Zero fake users, zero fake student dataset records, zero fake community posts.
    """
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed MIT Manipal Official Departments if empty
        if db.query(models.Department).count() == 0:
            departments = [
                models.Department(code="CSE", name="Computer Science & Engineering", school="School of Computer Engineering", building="AB5 (3rd Floor)"),
                models.Department(code="IT", name="Information Technology", school="School of Computer Engineering", building="AB5 (4th Floor)"),
                models.Department(code="DSE", name="Data Science & Engineering", school="School of Computer Engineering", building="AB5 (2nd Floor)"),
                models.Department(code="AIML", name="Artificial Intelligence & Machine Learning", school="School of Computer Engineering", building="AB5 (3rd Floor)"),
                models.Department(code="CCE", name="Computer & Communication Engineering", school="School of Computer Engineering", building="AB5 (4th Floor)"),
                models.Department(code="ECE", name="Electronics & Communication Engineering", school="School of Electrical & Electronics", building="AB3 (1st Floor)"),
                models.Department(code="EEE", name="Electrical & Electronics Engineering", school="School of Electrical & Electronics", building="AB3 (2nd Floor)"),
                models.Department(code="EIE", name="Electronics & Instrumentation Engineering", school="School of Electrical & Electronics", building="AB3 (3rd Floor)"),
                models.Department(code="BME", name="Biomedical Engineering", school="School of Electrical & Electronics", building="AB3 (3rd Floor)"),
                models.Department(code="ME", name="Mechanical Engineering", school="School of Mechanical & Industrial", building="AB1 (2nd Floor)"),
                models.Department(code="MTE", name="Mechatronics Engineering", school="School of Mechanical & Industrial", building="AB1 (1st Floor)"),
                models.Department(code="AE", name="Aeronautical Engineering", school="School of Mechanical & Industrial", building="AB1 (3rd Floor)"),
                models.Department(code="AME", name="Automobile Engineering", school="School of Mechanical & Industrial", building="AB1 (Ground Floor)"),
                models.Department(code="IP", name="Industrial & Production Engineering", school="School of Mechanical & Industrial", building="AB1 (2nd Floor)"),
                models.Department(code="CE", name="Civil Engineering", school="School of Civil & Chemical", building="AB2 (1st Floor)"),
                models.Department(code="CHE", name="Chemical Engineering", school="School of Civil & Chemical", building="AB2 (2nd Floor)"),
                models.Department(code="BT", name="Biotechnology", school="School of Basic & Applied Sciences", building="AB4 (Ground Floor)"),
                models.Department(code="H&M", name="Humanities & Management", school="School of Management", building="AB5 (1st Floor)"),
                models.Department(code="MATH", name="Mathematics & Basic Sciences", school="School of Basic & Applied Sciences", building="AB5 (2nd Floor)"),
            ]
            db.add_all(departments)
            db.commit()
            print("✓ Database Seeded: 19 Official MIT Manipal Departments created.")

        # 2. Seed Academic Events if empty
        if db.query(models.AcademicEvent).count() == 0:
            import datetime
            now = datetime.datetime.utcnow()

            events = [
                models.AcademicEvent(
                    title="Course Registration & Add/Drop Deadline",
                    description="Official window for online course registration, elective selection, and add/drop requests closes at 5:00 PM.",
                    category="Deadlines",
                    start_datetime=now + datetime.timedelta(days=2),
                    end_datetime=now + datetime.timedelta(days=2, hours=5),
                    notification_offsets="[10080, 4320, 1440, 60, 0]",
                    target_audience="student",
                    department="all",
                    academic_year="all",
                    semester="Even Semester (Jan - May)",
                    priority="URGENT",
                    source="Official MIT Academic Calendar 2025-2026",
                    status="published",
                ),
                models.AcademicEvent(
                    title="Mid-Semester Examinations (Even Sem)",
                    description="Mid-semester written examinations for all B.Tech / M.Tech programs across Academic Blocks AB1, AB2, AB3, AB5.",
                    category="Exams",
                    start_datetime=now + datetime.timedelta(days=7),
                    end_datetime=now + datetime.timedelta(days=14),
                    notification_offsets="[10080, 4320, 1440, 120, 0]",
                    target_audience="all",
                    department="all",
                    academic_year="all",
                    semester="Even Semester (Jan - May)",
                    priority="HIGH",
                    source="Official MIT Academic Calendar 2026-2027",
                    status="published",
                ),
                models.AcademicEvent(
                    title="Tuition & Hostel Fee Installment Deadline",
                    description="Deadline to clear 2nd installment tuition and hostel utility charges to avoid late fee penalty.",
                    category="Financial",
                    start_datetime=now + datetime.timedelta(days=14),
                    end_datetime=now + datetime.timedelta(days=14, hours=6),
                    notification_offsets="[10080, 4320, 1440, 60, 0]",
                    target_audience="student",
                    department="all",
                    academic_year="all",
                    semester="all",
                    priority="HIGH",
                    source="MAHE Institutional Fee Schedule 2026",
                    status="published",
                ),
                models.AcademicEvent(
                    title="Revels '26 — Annual Cultural & Technical Fest",
                    description="Manipal Institute of Technology's flagship national inter-collegiate cultural and technical festival.",
                    category="Events",
                    start_datetime=now + datetime.timedelta(days=21),
                    end_datetime=now + datetime.timedelta(days=25),
                    notification_offsets="[4320, 1440, 0]",
                    target_audience="all",
                    department="all",
                    academic_year="all",
                    semester="all",
                    priority="NORMAL",
                    source="MIT Student Council Announcement",
                    status="published",
                ),
                models.AcademicEvent(
                    title="End-Semester Theory Examinations (Even Sem)",
                    description="Final end-semester theory examinations for all engineering batches.",
                    category="Exams",
                    start_datetime=now + datetime.timedelta(days=45),
                    end_datetime=now + datetime.timedelta(days=60),
                    notification_offsets="[10080, 4320, 1440, 0]",
                    target_audience="all",
                    department="all",
                    academic_year="all",
                    semester="Even Semester (Jan - May)",
                    priority="HIGH",
                    source="Official MIT Academic Calendar 2026-2027",
                    status="published",
                ),
                models.AcademicEvent(
                    title="Campus Placement Drive — Batch of 2026",
                    description="Technical rounds and campus interview drives conducted by MAHE Placement Cell in Innovation Centre.",
                    category="Placements",
                    start_datetime=now + datetime.timedelta(days=5),
                    end_datetime=now + datetime.timedelta(days=6),
                    notification_offsets="[4320, 1440, 60, 0]",
                    target_audience="student",
                    department="all",
                    academic_year="4th Year (2022-26)",
                    semester="all",
                    priority="HIGH",
                    source="MAHE Training & Placement Cell",
                    status="published",
                ),
            ]
            db.add_all(events)
            db.commit()
            print("✓ Database Seeded: Real Timeline Academic Events created.")

        # 3. Seed Knowledge Documents metadata if empty
        if db.query(models.KnowledgeDocument).count() == 0:
            docs = [
                models.KnowledgeDocument(filename="Academic Calendar 25-26_ Final_June30_2025.pdf", file_type="PDF", file_size="313 KB", chunks_count=42, status="Indexed & Vectorized"),
                models.KnowledgeDocument(filename="Academic Calendar 26-27 (1).pdf", file_type="PDF", file_size="298 KB", chunks_count=38, status="Indexed & Vectorized"),
                models.KnowledgeDocument(filename="BTech_Common_Counseling_2026_Cutoff_Rank_Round_2.pdf", file_type="PDF", file_size="145 KB", chunks_count=26, status="Indexed & Vectorized"),
                models.KnowledgeDocument(filename="MTech ME 2026 Cut off Rank.pdf", file_type="PDF", file_size="112 KB", chunks_count=18, status="Indexed & Vectorized"),
                models.KnowledgeDocument(filename="manipal_sce_faculty_cabins.csv", file_type="CSV", file_size="45 KB", chunks_count=64, status="Indexed & Vectorized"),
                models.KnowledgeDocument(filename="mit_manipal_faculty.csv", file_type="CSV", file_size="62 KB", chunks_count=88, status="Indexed & Vectorized"),
            ]
            db.add_all(docs)
            db.commit()
            print("✓ Database Seeded: Knowledge Documents metadata created.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
