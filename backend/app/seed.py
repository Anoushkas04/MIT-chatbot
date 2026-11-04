import datetime
import sys

# Standalone entrypoint (`python -m app.seed`) doesn't go through app.main, so it
# needs its own UTF-8 stdout guard for the checkmark/emoji in the seed log lines.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import SEED_DEMO_COMMUNITY
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

        # 4. Opt-in demo content for the Community feed (SEED_DEMO_COMMUNITY=1 only).
        if SEED_DEMO_COMMUNITY and db.query(models.CommunityPost).count() == 0:
            _seed_demo_community(db)

    finally:
        db.close()


def _seed_demo_community(db) -> None:
    import json
    from app.demo_community import DEMO_POSTS

    def add_comments(post_id: int, parent_id, items: list) -> None:
        for item in items:
            comment = models.CommunityComment(
                post_id=post_id,
                parent_id=parent_id,
                author_label=item["author"],
                body=item["body"],
                seed_score=item["votes"],
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=item["days_ago"]),
            )
            db.add(comment)
            db.flush()  # need comment.id before seeding its own replies
            add_comments(post_id, comment.id, item.get("replies", []))

    for p in DEMO_POSTS:
        post = models.CommunityPost(
            title=p["title"],
            body=p["body"],
            tags_json=json.dumps(p["tags"]),
            author_label=p["author"],
            seed_score=p["votes"],
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=p["days_ago"]),
        )
        db.add(post)
        db.flush()  # need post.id before seeding its answers
        add_comments(post.id, None, p.get("answers", []))

    db.commit()
    print(f"✓ Database Seeded: {len(DEMO_POSTS)} labelled demo Community questions (SEED_DEMO_COMMUNITY=1).")


if __name__ == "__main__":
    seed_database()
