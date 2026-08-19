from dataclasses import dataclass
from datetime import date



@dataclass
class CourseEvent:
    course_slug: str
    course_name: str
    start: date
    end: date
    location: str | None = None
    status: str | None = None
