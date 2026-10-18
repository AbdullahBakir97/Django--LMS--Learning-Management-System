"""An interview as an iCalendar (RFC 5545) event, so it lands in any calendar app."""

from datetime import UTC, timedelta

from django.conf import settings

from .models import Interview


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _stamp(moment) -> str:
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _fold(line: str) -> str:
    # shortcut: folds by characters, not octets; fine unless a line is mostly non-ASCII
    return "\r\n ".join(line[i : i + 73] for i in range(0, len(line), 73)) or line


def interview_ics(interview: Interview) -> str:
    job = interview.application.job
    end = interview.starts_at + timedelta(minutes=interview.duration_minutes)
    status = "CANCELLED" if interview.status == Interview.Status.CANCELLED else "CONFIRMED"
    host = settings.FRONTEND_URL.split("//")[-1].split("/")[0] or "lms"
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LMS//Interviews//EN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:interview-{interview.id}@{host}",
        f"DTSTAMP:{_stamp(interview.updated_at)}",
        f"DTSTART:{_stamp(interview.starts_at)}",
        f"DTEND:{_stamp(end)}",
        f"SUMMARY:{_escape(f'Interview: {job.title} at {job.company.name}')}",
        f"LOCATION:{_escape(interview.location)}",
        f"DESCRIPTION:{_escape(interview.details)}",
        f"STATUS:{status}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
