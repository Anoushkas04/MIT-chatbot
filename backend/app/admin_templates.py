"""Canned texts admins pick from. Admins can still edit a template before sending it."""

REPLY_TEMPLATES = [
    {
        "key": "feedback_thanks",
        "label": "Thanks for the feedback",
        "text": "Thank you for your feedback! We've shared it with the MITra team and we'll look into it.",
    },
    {
        "key": "complaint_logged",
        "label": "Complaint logged",
        "text": "Thank you for raising this concern. We've logged it and the team will look into it. We'll update this thread once there's progress.",
    },
    {
        "key": "already_answered",
        "label": "Already answered officially",
        "text": "This is covered in the official documents. You can ask MITra in chat for the exact rule and its source, or check the Academic Regulations under Search.",
    },
    {
        "key": "escalated",
        "label": "Escalated to the department",
        "text": "We've forwarded your question to the relevant department. We'll post their answer here as soon as we hear back.",
    },
    {
        "key": "resolved",
        "label": "Marked resolved",
        "text": "This has now been resolved. Thank you for your patience, and let us know here if anything is still unclear.",
    },
    {
        "key": "guidelines_reminder",
        "label": "Community guidelines reminder",
        "text": "A quick reminder to keep the Community respectful and on topic, so everyone can find useful answers.",
    },
]

DELETE_REASONS = ["Inappropriate", "Irrelevant", "Duplicate", "Spam", "Other"]

# Preset warnings for reported accounts. Admins choose one (and may edit it) before sending.
WARNING_TEMPLATES = [
    {
        "key": "general",
        "label": "General warning",
        "text": "We've received reports about how you've been interacting with other students. Please keep your messages respectful. Further reports may lead to a suspension.",
    },
    {
        "key": "harassment",
        "label": "Harassment",
        "text": "Students have reported messages from you as harassment. Harassment isn't allowed on MITra. If this continues, your account will be suspended.",
    },
    {
        "key": "spam",
        "label": "Spam or scams",
        "text": "Your account was reported for sending spam or promotional messages. Please stop sending unsolicited messages, or your account may be suspended.",
    },
    {
        "key": "inappropriate",
        "label": "Inappropriate content",
        "text": "You were reported for sharing inappropriate content. Please keep everything you share appropriate for a campus community.",
    },
    {
        "key": "impersonation",
        "label": "Impersonation",
        "text": "Your account was reported for pretending to be someone else. Please use MITra only as yourself.",
    },
    {
        "key": "final",
        "label": "Final warning",
        "text": "This is a final warning. Any further reports about your behaviour will lead to a suspension of your account.",
    },
]
