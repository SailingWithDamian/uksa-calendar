from datetime import timedelta

from icalendar import Calendar, Event

from scraper import CourseEvent


def build_calendar(events: list[CourseEvent], calendar_name: str) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//UKSA Calendar//uksa-calendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", calendar_name)
    cal.add("x-wr-timezone", "Europe/London")

    for course_event in events:
        event = Event()
        event.add(
            "summary",
            (
                f"[{course_event.status}] {course_event.course_name}"
                if course_event.status
                else course_event.course_name
            ),
        )
        event.add("dtstart", course_event.start)
        event.add("dtend", course_event.end + timedelta(days=1))
        event.add(
            "uid",
            (
                f"{course_event.course_slug}-{course_event.start.isoformat()}"
                f"-{course_event.end.isoformat()}@uksa-calendar"
            ),
        )

        cal.add_component(event)

    return cal.to_ical()
