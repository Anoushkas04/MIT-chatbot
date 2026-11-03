from typing import List, Dict, Any

KNOWLEDGE_STATES = [
    "Official",
    "Community",
    "Pending Verification",
    "Verified",
    "Conflicting",
    "Outdated",
    "Deprecated",
]


def get_verification_pipeline_items() -> List[Dict[str, Any]]:
    """Verification Engine: Manages knowledge lifecycle across 7 states

    and detects discrepancies between official PDF sources and crowdsourced reports.
    """
    return [
        {
            "id": "ver_01",
            "topic": "Block 13 & 16 Mess Closing Timings",
            "state": "Conflicting",
            "state_badge": "⚠️ Conflicting",
            "official_fact": "Official Document (Academic Calendar & Mess Circular): Dinner timings 7:30 PM – 9:30 PM",
            "community_fact": "Student Community Reports (126 responses): Entry gate actually closes at 9:15 PM.",
            "conflict_warning": "⚠️ Conflicting Information: Official document says Mess closes at 9:30 PM, but recent community reports indicate entry closes at 9:15 PM.",
            "last_updated": "2 hours ago",
        },
        {
            "id": "ver_02",
            "topic": "Outstation Hostel Leave Form Signature Location After 5 PM",
            "state": "Pending Verification",
            "state_badge": "⏳ Pending Verification",
            "official_fact": "Official Policy: Hostel warden signature required before 6:00 PM.",
            "community_fact": "Student Reports: Block 16 warden available till 7:30 PM; Chief Warden Office Block 5 after 8 PM.",
            "conflict_warning": "⏳ Pending Verification: Student reports regarding evening warden hours are awaiting chief warden signoff.",
            "last_updated": "5 hours ago",
        },
        {
            "id": "ver_03",
            "topic": "AB5 Fast Lab Assignment Printing Rates",
            "state": "Verified",
            "state_badge": "✓ Verified",
            "official_fact": "Student Plaza & AB5 Basement Xerox: B&W printing ₹1 per page.",
            "community_fact": "Confirmed by 89 student votes.",
            "conflict_warning": None,
            "last_updated": "1 day ago",
        },
        {
            "id": "ver_04",
            "topic": "Library 3rd Floor Quiet Zone Rules",
            "state": "Official",
            "state_badge": "🟢 Official",
            "official_fact": "Central Library Regulation Section B: Absolute silence zone.",
            "community_fact": "100% Student Compliance",
            "conflict_warning": None,
            "last_updated": "3 days ago",
        },
        {
            "id": "ver_05",
            "topic": "Old Mid-Sem Exam Timetable (March 2025)",
            "state": "Deprecated",
            "state_badge": "🚫 Deprecated",
            "official_fact": "Past Academic Year Timetable.",
            "community_fact": "Superseded by Academic Calendar 2026-27.",
            "conflict_warning": "🚫 Deprecated: Historical schedule replaced by current 2026 Academic Calendar.",
            "last_updated": "1 year ago",
        },
    ]
