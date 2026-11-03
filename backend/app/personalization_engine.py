from typing import List, Dict, Any

DEPARTMENT_RECOMMENDATIONS = {
    "Computer Science & Engg": {
        "Senior (3rd/4th Year)": {
            "headline": "Placement Drives & Open Electives (CSE Senior)",
            "resources": [
                {"title": "Microsoft & Amazon Placement Prep Kit", "desc": "Top 5 DSA topics (Graphs, DP, System Design) asked in Manipal campus drives.", "icon": "💼"},
                {"title": "AB5 3rd Floor High-Perf Compute Lab", "desc": "NVIDIA RTX GPUs available for Senior B.Tech Capstone Project work.", "icon": "💻"},
                {"title": "6th/8th Sem Scoring Electives", "desc": "Big Data Analytics & FinTech open electives recommended by seniors.", "icon": "📚"},
            ],
            "quick_prompt": "What DSA topics are asked in Microsoft Manipal campus drives?",
        },
        "Freshman (1st/2nd Year)": {
            "headline": "C Programming & Foundations (CSE Freshman)",
            "resources": [
                {"title": "C Programming Lab Manual (AB5 Basement)", "desc": "Fast B&W printing available at AB5 basement shop.", "icon": "📄"},
                {"title": "3rd Floor Central Library Silent Zone", "desc": "Reference Section B for quiet cramming before mid-sems.", "icon": "🤫"},
                {"title": "FC-1 North Indian Mess 2 Review", "desc": "Top rated mess for Block 13 & 16 CSE hostelers.", "icon": "🍱"},
            ],
            "quick_prompt": "What is the minimum attendance required for CSE theory & labs?",
        },
    },
    "Mechanical Engineering": {
        "Senior (3rd/4th Year)": {
            "headline": "Robotics & Thermal Labs (Mech Senior)",
            "resources": [
                {"title": "Industrial Robotics Lab (AB1)", "desc": "Arduino & Fanuc robotic arm hands-on viva guidelines.", "icon": "⚙️"},
                {"title": "Bosch & Tata Motors Campus Drive Criteria", "desc": "CGPA cutoff: 7.5 minimum with no active backlogs.", "icon": "🏆"},
                {"title": "CAD/CAM Software Access", "desc": "SolidWorks & ANSYS licenses on AB1 CAD lab computers.", "icon": "📐"},
            ],
            "quick_prompt": "What are the eligibility criteria for Bosch campus placement drive?",
        },
        "Freshman (1st/2nd Year)": {
            "headline": "Workshop & Machine Shop Guide (Mech Freshman)",
            "resources": [
                {"title": "Fitting & Fitting Shop Safety Regulations", "desc": "Mandatory leather shoes & apron required in AB1 Mechanical Workshop.", "icon": "👞"},
                {"title": "Engineering Physics Viva Questions", "desc": "Lasers and fiber optics viva questions list by Prof. Nair.", "icon": "🔬"},
                {"title": "Block 17 South Indian Canteen Dosa", "desc": "Breakfast hot spot near AB1 workshop.", "icon": "☕"},
            ],
            "quick_prompt": "What safety gear is required for Mechanical Workshop lab?",
        },
    },
}


def get_personalized_recommendations(department: str = "Computer Science & Engg", academic_year: str = "3rd Year (2023-27)") -> Dict[str, Any]:
    dept_key = department if department in DEPARTMENT_RECOMMENDATIONS else "Computer Science & Engg"
    year_key = "Senior (3rd/4th Year)" if ("3rd" in academic_year or "4th" in academic_year) else "Freshman (1st/2nd Year)"

    data = DEPARTMENT_RECOMMENDATIONS.get(dept_key, {}).get(year_key, DEPARTMENT_RECOMMENDATIONS["Computer Science & Engg"]["Senior (3rd/4th Year)"])

    return {
        "department": dept_key,
        "academic_year": year_key,
        "headline": data["headline"],
        "resources": data["resources"],
        "quick_prompt": data["quick_prompt"],
    }
