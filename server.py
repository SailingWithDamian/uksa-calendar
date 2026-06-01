import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from ics_generator import build_calendar
from scraper import COURSE_NAMES, fetch_events_for_courses

app = FastAPI()

GROUPS: dict[str, list[str]] = {
    "approved-engineer": [
        "mca-approved-engineer-course",
        "mca-approved-engineer-course-2",
    ],
}

_config_path = os.path.join(os.path.dirname(__file__), "uksa-calendar.json")
if os.path.exists(_config_path):
    with open(_config_path) as _f:
        _config = json.load(_f)
    GROUPS.update(_config.get("groups", {}))

VALID_COURSES = set(COURSE_NAMES.keys())


async def calendar_response(course_slugs: list[str], calendar_name: str = "UKSA Courses") -> Response:
    events = await fetch_events_for_courses(course_slugs)
    ics_bytes = build_calendar(events, calendar_name=calendar_name)
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="uksa-courses.ics"'},
    )


@app.get("/course/{slug}")
async def single_course(slug: str):
    if slug not in VALID_COURSES:
        raise HTTPException(status_code=404, detail=f"Unknown course slug: {slug!r}")
    return await calendar_response([slug], calendar_name=f"UKSA - {COURSE_NAMES[slug]}")


@app.get("/group/{slug}")
async def course_group(slug: str):
    if slug not in GROUPS:
        raise HTTPException(status_code=404, detail=f"Unknown group slug: {slug!r}")
    course_slugs = GROUPS[slug]
    return await calendar_response(course_slugs, calendar_name=f"Group {slug}")
