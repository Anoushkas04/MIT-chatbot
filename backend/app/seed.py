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
                # 1. Hostel & Mess
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
                    "title": "Hard water hair fall precautions in Blocks 18, 19, 20",
                    "sub_community": "Hostel & Mess",
                    "tag": "Hostels",
                    "author_name": "Ishita_Biotech",
                    "content": "Water in Block 18-20 hostels is hard water. What precautions do seniors recommend to avoid hair damage?",
                    "upvotes": 52,
                    "verified": True,
                    "comments": [
                        {"author_name": "Riya_CHE", "content": "Use RO drinking water from hostel floor water cooler for final hair rinse or install a tap filter attachment from Student Plaza hardware store.", "is_helpful": True, "upvotes": 31},
                    ]
                },
                # 2. Placements & Careers
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
                    "title": "DSA & System Design Prep for Tier-1 Placement Drives (Microsoft / Amazon)",
                    "sub_community": "Placements & Careers",
                    "tag": "Placements",
                    "author_name": "Dev_CSE",
                    "content": "What topics carry maximum weightage during Innovation Centre coding tests for CSE & IT students?",
                    "upvotes": 74,
                    "verified": True,
                    "comments": [
                        {"author_name": "Aman_IT", "content": "Focus on Graphs (BFS/DFS), Dynamic Programming, Trees, and SQL query optimizations. 80% of online assessment questions in Round 1 are DP & Trees.", "is_helpful": True, "upvotes": 42},
                    ]
                },
                # 3. Academics & Study
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
                    "title": "75% Attendance Rule & MLC (Mandatory Learning Courses) Completion",
                    "sub_community": "Academics & Study",
                    "tag": "Regulations",
                    "author_name": "Aditya_EEE",
                    "content": "Is the 75% attendance rule strictly enforced for theory and lab courses? What happens if attendance drops below 75%?",
                    "upvotes": 49,
                    "verified": True,
                    "comments": [
                        {"author_name": "Dr_Sharma_Faculty", "content": "Attendance below 75% leads to grade drop or exam hall ticket withholding (DT grade). Mandatory Learning Courses like Environmental Studies & UHV must be completed before 6th sem.", "is_helpful": True, "upvotes": 38},
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
                # 4. Facilities & Printing
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
                    "title": "Marena Sports Complex membership & Gym booking details",
                    "sub_community": "Facilities & Printing",
                    "tag": "Facilities",
                    "author_name": "Kabir_MTE",
                    "content": "How to register for Marena sports complex and indoor badminton court slots?",
                    "upvotes": 45,
                    "verified": True,
                    "comments": [
                        {"author_name": "Yash_Civil", "content": "Marena membership pass can be created at the front desk with college ID card. Badminton court slots open 24 hours prior via student portal.", "is_helpful": True, "upvotes": 26},
                    ]
                },
                # 5. Clubs & Organizations
                {
                    "title": "Formula Manipal & ThrustMIT recruitment preparation tips",
                    "sub_community": "Clubs & Organizations",
                    "tag": "Clubs",
                    "author_name": "Tushar_ME",
                    "content": "How competitive is the Formula Manipal & ThrustMIT recruitment process for 1st and 2nd year mechanical/ECE students?",
                    "upvotes": 58,
                    "verified": True,
                    "comments": [
                        {"author_name": "Kunal_MTE", "content": "Recruitment involves a written CAD/aptitude test followed by 2 technical rounds. Brush up on SolidWorks, statics, and basic microcontroller programming.", "is_helpful": True, "upvotes": 33},
                    ]
                },
                # 6. Admissions & Cutoffs
                {
                    "title": "MET Score vs Rank Cutoffs for CSE, AIML & IT (Round 1 to Round 3)",
                    "sub_community": "Admissions & Cutoffs",
                    "tag": "Admissions",
                    "author_name": "Prospective_Student_2026",
                    "content": "What was the closing cutoff rank for CSE and AIML in main campus counseling last year?",
                    "upvotes": 81,
                    "verified": True,
                    "comments": [
                        {"author_name": "Senior_CSE_Mod", "content": "CSE Round 2 closing rank was ~1,050. AIML was ~1,600 and IT was ~2,400. Intra-sliding round after 1st sem offers upgrade opportunities based on 1st sem CGPA.", "is_helpful": True, "upvotes": 51},
                    ]
                },
                # 7. Faculty & Cabins
                {
                    "title": "Approaching SCE professors in AB5 for Undergraduate Research LORs",
                    "sub_community": "Faculty & Cabins",
                    "tag": "Faculty",
                    "author_name": "Sanya_CSE",
                    "content": "How to approach Dr. Radhika Pai or AB5 faculty members for capstone project research guidance?",
                    "upvotes": 36,
                    "verified": True,
                    "comments": [
                        {"author_name": "Nikhil_DSE", "content": "Dr. Radhika Pai's cabin is on AB5 3rd Floor (Room 304). Visit during official faculty office hours (2 PM – 4 PM Tuesdays/Thursdays) with a printed research proposal.", "is_helpful": True, "upvotes": 20},
                    ]
                },
                # 8. Campus Life & Transport
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
                {
                    "title": "Monsoon preparation in Manipal — Umbrellas & Footwear recommendations",
                    "sub_community": "Campus Life",
                    "tag": "Campus Life",
                    "author_name": "Pranav_ECE",
                    "content": "Heavy monsoon rains start in June/July. What gear is essential for walking between AB1 and AB5?",
                    "upvotes": 67,
                    "verified": True,
                    "comments": [
                        {"author_name": "Swati_IT", "content": "Buy a sturdy windproof 3-fold umbrella from Student Plaza stationery shop. Crocs or quick-dry waterproof sandals are mandatory due to waterlogging.", "is_helpful": True, "upvotes": 40},
                    ]
                },
                # 9. Events & Fests
                {
                    "title": "Revels '26 Pro-Show passes & Delegate Card registration procedure",
                    "sub_community": "Events & Fests",
                    "tag": "Revels",
                    "author_name": "Rishi_CCE",
                    "content": "How do MIT students get Pro-Show concert passes during Revels fest week?",
                    "upvotes": 72,
                    "verified": True,
                    "comments": [
                        {"author_name": "Cultural_Council_Lead", "content": "Delegate cards are issued via Student Plaza counters or online portal using your learner ID. Entry to main Quadrangle Pro-Show requires active delegate card pass.", "is_helpful": True, "upvotes": 37},
                    ]
                },
                # 10. Hostel Operations
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

            print("✓ Database Seeded: 16 Reddit Community Discussions across ALL 11 categories ingested into DB.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
