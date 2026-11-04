"""Connections and private messages between registered students.

Requests stay pending until the other student accepts. Messages can only be sent
between accepted connections, and a block (either way) stops both. Reports about a
chat still never include its messages (see users_router.report_user).
"""
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_

from app import models, safety
from app.database import SessionLocal
from app.routers.auth_router import get_current_user
from app.routers.community_v2 import _relative

router = APIRouter(prefix="/api/network", tags=["6. Student Network & Safety"])
messages_router = APIRouter(prefix="/api/messages", tags=["6. Student Network & Safety"])

MAX_MESSAGE = 2000


def _summary(u: models.User) -> dict:
    # Public profile fields only, like /api/users/search.
    return {
        "id": u.id,
        "name": u.name,
        "department": u.department or "",
        "semester": u.semester or "",
        "academic_year": u.academic_year or "",
        "interests": [i.strip() for i in (u.interests or "").split(",") if i.strip()],
    }


def _pair(a: str, b: str):
    return or_(
        and_(models.Connection.requester_id == a, models.Connection.addressee_id == b),
        and_(models.Connection.requester_id == b, models.Connection.addressee_id == a),
    )


def _blocked_either_way(db, a: str, b: str) -> bool:
    return (
        db.query(models.UserBlock)
        .filter(
            or_(
                and_(models.UserBlock.blocker_id == a, models.UserBlock.blocked_id == b),
                and_(models.UserBlock.blocker_id == b, models.UserBlock.blocked_id == a),
            )
        )
        .first()
        is not None
    )


def _other_student(db, me: models.User, user_id: str) -> models.User:
    if user_id == me.id:
        raise HTTPException(status_code=400, detail="That's you.")
    other = (
        db.query(models.User)
        .filter(models.User.id == user_id, models.User.role != "admin", models.User.status == "active")
        .first()
    )
    if not other:
        raise HTTPException(status_code=404, detail="This student isn't available.")
    return other


def _connected(db, a: str, b: str) -> bool:
    return db.query(models.Connection).filter(_pair(a, b), models.Connection.status == "accepted").first() is not None


@router.get("", summary="My connections, incoming and outgoing requests, and unread message counts")
def my_network(me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = db.query(models.Connection).filter(
            or_(models.Connection.requester_id == me.id, models.Connection.addressee_id == me.id)
        ).all()
        other_ids = {r.addressee_id if r.requester_id == me.id else r.requester_id for r in rows}
        users = {
            u.id: u
            for u in db.query(models.User).filter(models.User.id.in_(other_ids), models.User.status == "active").all()
        } if other_ids else {}
        connections, incoming, outgoing = [], [], []
        for r in rows:
            other = users.get(r.addressee_id if r.requester_id == me.id else r.requester_id)
            if not other:
                continue
            if r.status == "accepted":
                connections.append(_summary(other))
            elif r.addressee_id == me.id:
                incoming.append(_summary(other))
            else:
                outgoing.append(_summary(other))

        unread: dict = {}
        for (sender_id,) in db.query(models.DirectMessage.sender_id).filter(
            models.DirectMessage.recipient_id == me.id, models.DirectMessage.read_at.is_(None)
        ):
            unread[sender_id] = unread.get(sender_id, 0) + 1
        blocked = [b.blocked_id for b in db.query(models.UserBlock).filter(models.UserBlock.blocker_id == me.id)]
        suggested = [_summary(u) for u in _suggestions(db, me, other_ids | set(blocked))]
        return {
            "connections": connections,
            "incoming": incoming,
            "outgoing": outgoing,
            "unread": unread,
            "blocked": blocked,
            "suggested": suggested,
        }
    finally:
        db.close()


MAX_SUGGESTIONS = 12


def _suggestions(db, me: models.User, exclude: set) -> list:
    """Registered students you have no relationship with, sharing your department or interests first."""
    blocked_me = db.query(models.UserBlock.blocker_id).filter(models.UserBlock.blocked_id == me.id)
    candidates = (
        db.query(models.User)
        .filter(
            models.User.id != me.id,
            models.User.role == "student",
            models.User.status == "active",
            models.User.is_suspended.is_(False),
            ~models.User.id.in_(blocked_me),
        )
        .order_by(models.User.name)
        .limit(200)
        .all()
    )
    mine = {i.strip().lower() for i in (me.interests or "").split(",") if i.strip()}

    def score(u: models.User) -> int:
        theirs = {i.strip().lower() for i in (u.interests or "").split(",") if i.strip()}
        same_dept = bool(me.department) and (u.department or "").lower() == me.department.lower()
        return 2 * same_dept + len(mine & theirs)

    ranked = sorted((u for u in candidates if u.id not in exclude), key=score, reverse=True)
    return ranked[:MAX_SUGGESTIONS]


@router.post("/requests/{user_id}", summary="Send a connection request (accepts theirs if they already asked)")
def send_request(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        _other_student(db, me, user_id)
        if _blocked_either_way(db, me.id, user_id):
            raise HTTPException(status_code=403, detail="You can't connect with this student.")
        existing = db.query(models.Connection).filter(_pair(me.id, user_id)).first()
        if existing:
            if existing.status == "accepted":
                return {"status": "connected"}
            if existing.requester_id == me.id:
                return {"status": "pending"}
            # They already asked: requesting back accepts it
            existing.status = "accepted"
            existing.responded_at = datetime.datetime.utcnow()
            db.commit()
            return {"status": "connected"}
        db.add(models.Connection(requester_id=me.id, addressee_id=user_id, status="pending"))
        db.commit()
        return {"status": "pending"}
    finally:
        db.close()


def _incoming_request(db, me: models.User, user_id: str) -> models.Connection:
    row = (
        db.query(models.Connection)
        .filter(
            models.Connection.requester_id == user_id,
            models.Connection.addressee_id == me.id,
            models.Connection.status == "pending",
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="That request is no longer pending.")
    return row


@router.post("/requests/{user_id}/accept", summary="Accept a connection request")
def accept_request(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        row = _incoming_request(db, me, user_id)
        row.status = "accepted"
        row.responded_at = datetime.datetime.utcnow()
        db.commit()
        return {"status": "connected"}
    finally:
        db.close()


@router.post("/requests/{user_id}/decline", summary="Decline a connection request")
def decline_request(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db.delete(_incoming_request(db, me, user_id))
        db.commit()
        return {"status": "declined"}
    finally:
        db.close()


@router.delete("/requests/{user_id}", summary="Withdraw a connection request I sent")
def withdraw_request(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db.query(models.Connection).filter(
            models.Connection.requester_id == me.id,
            models.Connection.addressee_id == user_id,
            models.Connection.status == "pending",
        ).delete()
        db.commit()
        return {"status": "withdrawn"}
    finally:
        db.close()


@router.delete("/connections/{user_id}", summary="Remove a connection")
def remove_connection(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db.query(models.Connection).filter(_pair(me.id, user_id)).delete()
        db.commit()
        return {"status": "removed"}
    finally:
        db.close()


@router.post("/blocks/{user_id}", summary="Block a student: removes the connection and stops requests and messages")
def block_user(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        if user_id == me.id:
            raise HTTPException(status_code=400, detail="That's you.")
        db.query(models.Connection).filter(_pair(me.id, user_id)).delete()
        exists = db.query(models.UserBlock).filter(
            models.UserBlock.blocker_id == me.id, models.UserBlock.blocked_id == user_id
        ).first()
        if not exists:
            db.add(models.UserBlock(blocker_id=me.id, blocked_id=user_id))
        db.commit()
        return {"status": "blocked"}
    finally:
        db.close()


@router.delete("/blocks/{user_id}", summary="Unblock a student")
def unblock_user(user_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db.query(models.UserBlock).filter(
            models.UserBlock.blocker_id == me.id, models.UserBlock.blocked_id == user_id
        ).delete()
        db.commit()
        return {"status": "unblocked"}
    finally:
        db.close()


def _message(m: models.DirectMessage, me_id: str) -> dict:
    return {
        "id": m.id,
        "from": "me" if m.sender_id == me_id else "them",
        "text": m.body,
        "time": _relative(m.created_at),
        "at": m.created_at.isoformat() + "Z",
    }


@messages_router.get("/{user_id}", summary="My conversation with a connection (marks their messages read)")
def get_thread(user_id: str, after: Optional[int] = Query(None, ge=0), me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        if not _connected(db, me.id, user_id):
            raise HTTPException(status_code=403, detail="You can only message your connections.")
        q = db.query(models.DirectMessage).filter(
            or_(
                and_(models.DirectMessage.sender_id == me.id, models.DirectMessage.recipient_id == user_id),
                and_(models.DirectMessage.sender_id == user_id, models.DirectMessage.recipient_id == me.id),
            )
        )
        if after is not None:
            rows = q.filter(models.DirectMessage.id > after).order_by(models.DirectMessage.id).all()
        else:
            rows = list(reversed(q.order_by(models.DirectMessage.id.desc()).limit(200).all()))
        now = datetime.datetime.utcnow()
        for m in rows:
            if m.recipient_id == me.id and m.read_at is None:
                m.read_at = now
        db.commit()
        return {"messages": [_message(m, me.id) for m in rows]}
    finally:
        db.close()


class SendMessage(BaseModel):
    text: str


@messages_router.post("/{user_id}", summary="Send a private message to a connection")
def send_message(user_id: str, req: SendMessage, me: models.User = Depends(get_current_user)):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Write a message first.")
    if len(text) > MAX_MESSAGE:
        raise HTTPException(status_code=400, detail=f"Messages can be up to {MAX_MESSAGE} characters.")
    db = SessionLocal()
    try:
        if safety.active_suspension(db, me.id):
            raise HTTPException(status_code=403, detail="Suspended accounts can't send messages.")
        if _blocked_either_way(db, me.id, user_id) or not _connected(db, me.id, user_id):
            raise HTTPException(status_code=403, detail="You can only message your connections.")
        m = models.DirectMessage(sender_id=me.id, recipient_id=user_id, body=text)
        db.add(m)
        db.commit()
        db.refresh(m)
        return _message(m, me.id)
    finally:
        db.close()
