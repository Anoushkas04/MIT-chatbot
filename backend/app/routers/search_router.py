from typing import Optional, List, Dict, Any
from fastapi import APIRouter
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/api/search", tags=["10. Global Intelligent Search"])


GLOBAL_KNOWLEDGE_INDEX = [
    {
        "id": "srch_doc_01",
        "title": "Academic Calendar 2026-27 (Official MAHE Circular)",
        "category": "University Documents",
        "source_type": "official",
        "badge": "🟢 Official Document",
        "snippet": "Mid-Semester theory examinations for Even Semester begin on March 16, 2026 and conclude on March 23, 2026.",
        "link_target": "Academic Calendar 26-27 (1).pdf",
        "relevance": 0.96,
    },
    {
        "id": "srch_doc_02",
        "title": "B.Tech Common Counseling 2026 Cutoff Ranks Round 2",
        "category": "Academic Information",
        "source_type": "official",
        "badge": "🟢 Official Document",
        "snippet": "Computer Science & Engg (CSE) closing rank for Round 2 is 1,420. Data Science closing rank is 2,850.",
        "link_target": "BTech_Common_Counseling_2026_Cutoff_Rank_Round_2.pdf",
        "relevance": 0.92,
    },
    {
        "id": "srch_doc_03",
        "title": "Faculty Cabins & Office Directory (AB5)",
        "category": "University Documents",
        "source_type": "official",
        "badge": "🟢 Official Document",
        "snippet": "Dr. Radhika M. Pai: AB5 3rd Floor Room 304. Dr. Somanath: AB5 2nd Floor Room 212.",
        "link_target": "manipal_sce_faculty_cabins.csv",
        "relevance": 0.89,
    },
    {
        "id": "srch_comm_01",
        "title": "Which mess do students prefer in Block 13 & Block 16?",
        "category": "Community Posts",
        "source_type": "community",
        "badge": "🟡 Community Insight",
        "snippet": "FC-1 Ground Floor North Indian Mess 2 has best Paneer Butter Masala & Parathas on Tuesdays. 94% Student Agreement (126 responses).",
        "link_target": "Hostel & Mess",
        "relevance": 0.95,
    },
    {
        "id": "srch_comm_02",
        "title": "Where is the best place to print lab assignments fast in AB5?",
        "category": "Community Posts",
        "source_type": "community",
        "badge": "🟡 Community Insight",
        "snippet": "AB5 Basement Xerox Shop near canteen is fastest (₹1/pg). Emailing PDFs beforehand avoids queues.",
        "link_target": "Facilities & Printing",
        "relevance": 0.91,
    },
    {
        "id": "srch_faq_01",
        "title": "What is the official minimum attendance requirement for labs & lectures?",
        "category": "FAQs",
        "source_type": "official",
        "badge": "🟢 Official Policy",
        "snippet": "MAHE regulations mandate minimum 75% attendance in theory lectures and lab viva sessions to qualify for end-sem hall tickets.",
        "link_target": "MAHE Academic Ordinance",
        "relevance": 0.94,
    },
    {
        "id": "srch_evt_01",
        "title": "Revels 2026 MAHE Cultural Fest Registration",
        "category": "Events",
        "source_type": "official",
        "badge": "🟢 Official Event",
        "snippet": "Annual MAHE Cultural Fest Revels 2026 begins April 10. Online pass registration opens March 28 on MAHE Portal.",
        "link_target": "Campus Events",
        "relevance": 0.88,
    },
    {
        "id": "srch_notif_01",
        "title": "Course Registration Add/Drop Deadline Notice",
        "category": "Notifications",
        "source_type": "official",
        "badge": "🔔 Priority Alert",
        "snippet": "Course registration portal closes tomorrow at 5:00 PM for Even Semester course additions.",
        "link_target": "Notification Drawer",
        "relevance": 0.93,
    },
]


@router.get("", summary="Execute global multi-domain search with dual knowledge partition")
def perform_search(q: Optional[str] = None, category: Optional[str] = "all"):
    if not q or not q.strip():
        return {
            "query": "",
            "total_results": len(GLOBAL_KNOWLEDGE_INDEX),
            "official_count": len([i for i in GLOBAL_KNOWLEDGE_INDEX if i["source_type"] == "official"]),
            "community_count": len([i for i in GLOBAL_KNOWLEDGE_INDEX if i["source_type"] == "community"]),
            "results": GLOBAL_KNOWLEDGE_INDEX,
        }

    query_lower = q.lower().strip()
    filtered = []

    for item in GLOBAL_KNOWLEDGE_INDEX:
        match = (
            query_lower in item["title"].lower()
            or query_lower in item["snippet"].lower()
            or query_lower in item["category"].lower()
        )
        if match:
            if category and category.lower() != "all":
                if category.lower() == "official" and item["source_type"] != "official":
                    continue
                if category.lower() == "community" and item["source_type"] != "community":
                    continue
                if category.lower() not in ["official", "community"] and category.lower() not in item["category"].lower():
                    continue
            filtered.append(item)

    return {
        "query": q,
        "total_results": len(filtered),
        "official_count": len([i for i in filtered if i["source_type"] == "official"]),
        "community_count": len([i for i in filtered if i["source_type"] == "community"]),
        "results": filtered,
    }
