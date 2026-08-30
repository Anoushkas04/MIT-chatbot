from typing import Optional
from fastapi import APIRouter

router = APIRouter(prefix="/api/faculty", tags=["4. Faculty & Cabin Directory"])


@router.get("", summary="Search faculty members, cabin locations, and research focus")
def get_faculty(query: Optional[str] = None, dept: Optional[str] = None):
    faculty_list = [
        {"name": "Dr. Somanath S.", "dept": "Computer Science & Engg", "designation": "Professor & Head", "cabin": "AB5-302", "email": "somanath.s@manipal.edu", "research": "AI & Distributed Systems"},
        {"name": "Dr. Radhika M. Pai", "dept": "Computer Science & Engg", "designation": "Professor", "cabin": "AB5-314", "email": "radhika.pai@manipal.edu", "research": "Cloud Computing & Security"},
        {"name": "Dr. Srikanth Prabhu", "dept": "Computer Science & Engg", "designation": "Associate Professor", "cabin": "AB5-308", "email": "srikanth.prabhu@manipal.edu", "research": "Biometrics & Machine Learning"},
        {"name": "Dr. Ashalatha Nayak", "dept": "Computer Science & Engg", "designation": "Professor", "cabin": "AB5-301", "email": "ashalatha.nayak@manipal.edu", "research": "Network Systems"},
        {"name": "Dr. Harish Kumar S.", "dept": "Information Technology", "designation": "Professor & Head", "cabin": "AB5-402", "email": "harish.kumar@manipal.edu", "research": "Cybersecurity & IoT"},
        {"name": "Dr. Smitha N. Pai", "dept": "Information Technology", "designation": "Professor", "cabin": "AB5-410", "email": "smitha.pai@manipal.edu", "research": "Data Science"},
        {"name": "Dr. Niranjan N. Chiplunkar", "dept": "Data Science & CA", "designation": "Professor", "cabin": "AB5-201", "email": "niranjan.c@manipal.edu", "research": "Big Data Analytics"},
        {"name": "Dr. Subramanya Bhat", "dept": "Electronics & Comm Engg", "designation": "Professor & Head", "cabin": "AB3-104", "email": "subramanya.bhat@manipal.edu", "research": "VLSI Design & Embedded Systems"},
        {"name": "Dr. Kumara Shama", "dept": "Electronics & Comm Engg", "designation": "Professor", "cabin": "AB3-112", "email": "kumara.shama@manipal.edu", "research": "Signal Processing"},
        {"name": "Dr. Raviraja Adhikari", "dept": "Mechanical Engineering", "designation": "Professor & Head", "cabin": "AB1-205", "email": "raviraja.adhikari@manipal.edu", "research": "Thermal & Fluid Sciences"},
    ]

    filtered = faculty_list
    if dept and dept != "All":
        filtered = [f for f in filtered if dept.lower() in f["dept"].lower()]
    if query:
        q = query.lower()
        filtered = [
            f for f in filtered
            if q in f["name"].lower() or q in f["cabin"].lower() or q in f["dept"].lower() or q in f["research"].lower()
        ]
    return {"count": len(filtered), "data": filtered}
