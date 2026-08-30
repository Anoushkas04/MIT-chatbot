import json
import datetime
from typing import List, Dict, Any, Optional
from app.database import SessionLocal
from app import models


def format_relative_countdown(start_dt: datetime.datetime, end_dt: datetime.datetime, now_dt: datetime.datetime) -> Dict[str, Any]:
    """
    Computes precise relative time string, status, and breakdown.
    Rules:
    - > 1 day: 'X days remaining' / 'Begins in X days'
    - 1h..24h: 'Xh Ym remaining' / 'Begins in Xh Ym'
    - < 1h: 'Xm remaining' / 'Begins in Xm'
    - start <= now <= end: 'Happening now'
    - now > end: 'Event ended'
    """
    if start_dt <= now_dt <= end_dt:
        return {
            "status": "HAPPENING_NOW",
            "time_string": "Happening now",
            "countdown_label": "LIVE NOW",
            "seconds_remaining": max(0, int((end_dt - now_dt).total_seconds())),
            "urgency": "high"
        }
    elif now_dt > end_dt:
        return {
            "status": "EXPIRED",
            "time_string": "Event ended",
            "countdown_label": "Ended",
            "seconds_remaining": 0,
            "urgency": "none"
        }
    else:
        diff_sec = int((start_dt - now_dt).total_seconds())
        days = diff_sec // 86400
        hours = (diff_sec % 86400) // 3600
        minutes = (diff_sec % 3600) // 60

        if days >= 2:
            time_str = f"{days} days remaining"
            label = f"Begins in {days} days"
            urgency = "normal"
        elif days == 1:
            time_str = f"1 day remaining ({hours}h {minutes}m)"
            label = f"Tomorrow ({hours}h remaining)"
            urgency = "medium"
        elif hours >= 1:
            time_str = f"{hours}h {minutes}m remaining"
            label = f"Begins in {hours}h {minutes}m"
            urgency = "high"
        else:
            time_str = f"{minutes}m remaining"
            label = f"Begins in {minutes}m"
            urgency = "urgent"

        return {
            "status": "UPCOMING",
            "time_string": time_str,
            "countdown_label": label,
            "seconds_remaining": diff_sec,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "urgency": urgency
        }


def get_canonical_timeline(role: str = "student", department: str = None, academic_year: str = None) -> List[Dict[str, Any]]:
    """
    Canonical Event Timeline Engine.
    Queries database AcademicEvents matching user target audience, department, and academic year.
    Single Source of Truth for both Dashboard Timeline & Notifications.
    """
    db = SessionLocal()
    try:
        now_utc = datetime.datetime.utcnow()
        query = db.query(models.AcademicEvent).filter(models.AcademicEvent.status == "published")

        events = query.all()
        filtered_events = []

        for evt in events:
            # Filter Target Audience
            if evt.target_audience != "all" and role and evt.target_audience.lower() != role.lower():
                continue
            # Filter Department
            if evt.department != "all" and department and evt.department.lower() != department.lower():
                continue
            # Filter Academic Year
            if evt.academic_year != "all" and academic_year and evt.academic_year.lower() != academic_year.lower():
                continue

            countdown_info = format_relative_countdown(evt.start_datetime, evt.end_datetime, now_utc)

            category_icons = {
                "Exams": "📝",
                "Deadlines": "⏳",
                "Academic": "📖",
                "Holidays": "🌴",
                "Clubs": "🏆",
                "Workshops": "🛠️",
                "Hackathons": "💻",
                "Placements": "💼",
                "Financial": "💳",
                "Events": "🎪",
                "General": "📢"
            }

            filtered_events.append({
                "id": evt.id,
                "title": evt.title,
                "description": evt.description or "",
                "category": evt.category,
                "icon": category_icons.get(evt.category, "📢"),
                "start_datetime": evt.start_datetime.isoformat(),
                "end_datetime": evt.end_datetime.isoformat(),
                "formatted_date": evt.start_datetime.strftime("%B %d, %Y (%I:%M %p)"),
                "target_audience": evt.target_audience,
                "department": evt.department,
                "academic_year": evt.academic_year,
                "semester": evt.semester,
                "priority": evt.priority,
                "source": evt.source,
                "status": countdown_info["status"],
                "time_string": countdown_info["time_string"],
                "countdown_label": countdown_info["countdown_label"],
                "seconds_remaining": countdown_info["seconds_remaining"],
                "urgency": countdown_info["urgency"]
            })

        # Sort: HAPPENING_NOW first, then UPCOMING by seconds_remaining, then EXPIRED
        filtered_events.sort(key=lambda x: (
            0 if x["status"] == "HAPPENING_NOW" else (1 if x["status"] == "UPCOMING" else 2),
            x["seconds_remaining"]
        ))

        return filtered_events
    except Exception as e:
        print(f"Error in get_canonical_timeline: {e}")
        return []
    finally:
        db.close()


def get_personalized_notifications(user_id: str = "guest", role: str = "student", department: str = None, academic_year: str = None) -> Dict[str, Any]:
    """
    Timeline & Time-Threshold Driven Notification Engine.
    Zero random popups. Evaluates real-time threshold crossings against UserNotificationState.
    """
    db = SessionLocal()
    try:
        now_utc = datetime.datetime.utcnow()
        timeline_events = get_canonical_timeline(role=role, department=department, academic_year=academic_year)

        notifications_list = []
        popup_notification = None
        unread_count = 0

        for evt in timeline_events:
            if evt["status"] == "EXPIRED":
                continue

            event_db_id = evt["id"]
            start_dt = datetime.datetime.fromisoformat(evt["start_datetime"])
            diff_sec = (start_dt - now_utc).total_seconds()
            diff_minutes = int(diff_sec / 60)

            # Read notification offsets from DB event
            try:
                evt_obj = db.query(models.AcademicEvent).filter(models.AcademicEvent.id == event_db_id).first()
                offsets = json.loads(evt_obj.notification_offsets) if evt_obj and evt_obj.notification_offsets else [10080, 4320, 1440, 60, 0]
            except Exception:
                offsets = [10080, 4320, 1440, 60, 0]

            # Find largest offset threshold that has been crossed
            # e.g., if event is in 3 days (4320 mins), offset 10080 (7d) and 4320 (3d) have been crossed
            active_offset = None
            for offset in sorted(offsets, reverse=True):
                if diff_minutes <= offset:
                    active_offset = offset

            if active_offset is not None:
                # Check user state record
                state = db.query(models.UserNotificationState).filter(
                    models.UserNotificationState.user_id == user_id,
                    models.UserNotificationState.event_id == event_db_id,
                    models.UserNotificationState.offset_minutes == active_offset
                ).first()

                if not state:
                    state = models.UserNotificationState(
                        user_id=user_id,
                        event_id=event_db_id,
                        offset_minutes=active_offset,
                        is_read=False,
                        is_dismissed=False,
                        is_popup_dismissed=False
                    )
                    db.add(state)
                    db.commit()
                    db.refresh(state)

                if state.is_dismissed:
                    continue

                if not state.is_read:
                    unread_count += 1

                notif_item = {
                    "state_id": state.id,
                    "event_id": evt["id"],
                    "icon": evt["icon"],
                    "title": f"{evt['title']} — {evt['countdown_label']}",
                    "content": f"{evt['description']} Grounded in official source: {evt['source']}.",
                    "time": evt["time_string"],
                    "category": evt["category"],
                    "priority": f"{evt['priority']} PRIORITY" if evt['priority'] != "NORMAL" else "ACADEMIC ALERT",
                    "type_color": "purple" if evt["priority"] == "URGENT" else ("blue" if evt["priority"] == "HIGH" else "teal"),
                    "source_doc": evt["source"],
                    "read": state.is_read,
                    "dismissed": state.is_dismissed,
                    "seconds_remaining": evt["seconds_remaining"],
                    "formatted_date": evt["formatted_date"]
                }

                notifications_list.append(notif_item)

                # Popup condition: Only if high/urgent priority, popup not yet dismissed, and threshold crossed within recent window
                if not state.is_popup_dismissed and evt["priority"] in ["HIGH", "URGENT"] and not popup_notification:
                    popup_notification = notif_item

        return {
            "unread_count": unread_count,
            "notifications": notifications_list,
            "popup_notification": popup_notification
        }
    except Exception as e:
        print(f"Error in get_personalized_notifications: {e}")
        return {"unread_count": 0, "notifications": [], "popup_notification": None}
    finally:
        db.close()
