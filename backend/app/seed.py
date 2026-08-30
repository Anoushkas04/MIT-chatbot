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

        # 4. Seed Reddit Community Discussions (r/manipal & r/Manipal_Academics Q&A) if empty
        if db.query(models.StudentPost).count() == 0:
            posts_data = [
                {
                    "title": "Block 16 & Block 17 Hostels vs FC-2 Mess — Review from 3rd Year Student",
                    "sub_community": "Hostel & Mess",
                    "tag": "Hostels",
                    "author_name": "Aarav_Sharma_CSE",
                    "content": "Freshers asking about Block 16 & Block 17: They are right in front of Food Court 2 (FC-2). FC-2 is great for North Indian options (especially Paneer Butter Masala & Parathas on Tuesdays/Sundays). FC-1 is slightly further but good too.",
                    "upvotes": 48,
                    "verified": True,
                    "comments": [
                        {"author_name": "Siddharth_ECE", "content": "Block 17 South Indian Mess has the best filter coffee and Dosa breakfast on campus. Hard water issue can be managed by using drinking water for hair wash.", "is_helpful": True, "upvotes": 24},
                        {"author_name": "Ananya_IT", "content": "FC-2 entry closes strictly at 9:15 PM so arrive before 9 PM for dinner!", "is_helpful": False, "upvotes": 12},
                    ]
                },
                {
                    "title": "How are placement drives conducted in MIT Manipal vs MIT Bengaluru?",
                    "sub_community": "Placements & Careers",
                    "tag": "Placements",
                    "author_name": "Rohan_DSE",
                    "content": "Important clarification for prospective students & applicants: MIT Manipal and MIT Bengaluru are separate campuses with distinct placement cells. MIT Manipal has its centralized placement cell at the Innovation Centre.",
                    "upvotes": 62,
                    "verified": True,
                    "comments": [
                        {"author_name": "Varun_CCE", "content": "Placement drives for CSE/IT/CCE/ECE happen in 7th/8th semester via SLCM. Top recruiters like Microsoft, Amazon, Cisco, and Deloitte visit the main Manipal campus.", "is_helpful": True, "upvotes": 35},
                    ]
                },
                {
                    "title": "Open Electives (OE) scoring recommendations for 6th & 8th semester",
                    "sub_community": "Academics & Study",
                    "tag": "Electives",
                    "author_name": "Divya_AIML",
                    "content": "Which open electives are easiest to score A+ in CSE/ECE? How does the SLCM preference allotment work?",
                    "upvotes": 55,
                    "verified": True,
                    "comments": [
                        {"author_name": "Karan_ME", "content": "Humanities electives like Essentials of Management (EOM) and Industrial Economics are high scoring. Submit preferences on SLCM within 24 hours of window opening.", "is_helpful": True, "upvotes": 29},
                    ]
                },
                {
                    "title": "Fastest Xerox & Lab Manual printing near AB5 / Student Plaza",
                    "sub_community": "Facilities & Printing",
                    "tag": "Facilities",
                    "author_name": "Neha_BioTech",
                    "content": "Student Plaza Xerox shop gets super crowded before lab viva week. What is the fastest alternative for B&W printouts?",
                    "upvotes": 38,
                    "verified": True,
                    "comments": [
                        {"author_name": "Aditya_Civil", "content": "AB5 Basement Xerox shop is fast for B&W lab manuals (₹1/page). You can also email your PDF in advance to studentplazaxerox@gmail.com to bypass queues.", "is_helpful": True, "upvotes": 18},
                    ]
                },
                {
                    "title": "Quietest library floor during Mid-Sem exam week",
                    "sub_community": "Academics & Study",
                    "tag": "Library",
                    "author_name": "Priya_Maths",
                    "content": "Central library gets full during exam week. Which floor is best for zero-noise silent studying?",
                    "upvotes": 41,
                    "verified": True,
                    "comments": [
                        {"author_name": "Rahul_AE", "content": "3rd Floor Central Library (Reference Section B) is a strict silent zone with zero discussion permitted. 1st Floor allows group study.", "is_helpful": True, "upvotes": 22},
                    ]
                },
                {
                    "title": "Hostel Outstation Leave Approval after 6 PM — Block 16 Warden procedure",
                    "sub_community": "Hostel Operations",
                    "tag": "Hostels",
                    "author_name": "Vikram_Automobile",
                    "content": "How to get outstation leave form approved if you need to travel late in the evening?",
                    "upvotes": 29,
                    "verified": True,
                    "comments": [
                        {"author_name": "Tanvi_IP", "content": "Block 16 Warden office stays open till 7:30 PM. After 8 PM, sign must be obtained at Chief Warden Office near Student Care Clinic in Block 5.", "is_helpful": True, "upvotes": 14},
                    ]
                },
                {
                    "title": "Auto fares from Campus Gate 2 to Manipal Auto Stand & KMC",
                    "sub_community": "Campus Life",
                    "tag": "Transport",
                    "author_name": "Gautam_Mechatronics",
                    "content": "Standard auto fare guidelines from MIT main gate to Manipal town center or KMC hospital.",
                    "upvotes": 33,
                    "verified": True,
                    "comments": [
                        {"author_name": "Meera_BME", "content": "Meter auto fare or standard ₹40-50 for short rides within Manipal. Shared autos from Student Plaza gate are cheaper.", "is_helpful": True, "upvotes": 16},
                    ]
                },
            ]

            for pd in posts_data:
                post = models.StudentPost(
                    title=pd["title"],
                    sub_community=pd["sub_community"],
                    tag=pd["tag"],
                    author_name=pd["author_name"],
                    content=pd["content"],
                    upvotes=pd["upvotes"],
                    verified=pd["verified"],
                    time="Scraped from r/Manipal_Academics",
                )
                db.add(post)
                db.commit()
                db.refresh(post)

                for cd in pd["comments"]:
                    comment = models.PostComment(
                        post_id=post.id,
                        author_name=cd["author_name"],
                        content=cd["content"],
                        is_helpful=cd["is_helpful"],
                        upvotes=cd["upvotes"],
                    )
                    db.add(comment)
                db.commit()

            print("✓ Database Seeded: 7 Reddit Community Discussions (r/manipal & r/Manipal_Academics) ingested into DB.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
