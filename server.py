import asyncio
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from ics_generator import build_calendar
from models import CourseEvent
import seascope_scraper
import uksa_scraper

app = FastAPI()

GROUPS: dict[str, list[dict[str, str]]] = {
    "approved-engineer": [
        {"slug": "mca-approved-engineer-course", "provider": "uksa"},
        {"slug": "mca-aec1-course", "provider": "seascope"},
        {"slug": "mca-approved-engineer-course-2", "provider": "uksa"},
        {"slug": "mca-approved-engine-course-2-aec2", "provider": "seascope"},
    ],
}

_config_path = os.path.join(os.path.dirname(__file__), "course-calendar.json")
if os.path.exists(_config_path):
    with open(_config_path) as _f:
        _config = json.load(_f)
    GROUPS.update(_config.get("groups", {}))


async def calendar_response(events: list[CourseEvent], calendar_name: str = "Courses") -> Response:
    ics_bytes = build_calendar(events, calendar_name=calendar_name)
    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="courses.ics"'},
    )


@app.get("/course/{provider}/{slug}")
async def single_course(provider: str, slug: str):
    provider_courses, provider_fetch = {
        "seascope": (seascope_scraper.COURSE_NAMES, seascope_scraper.fetch_events_for_courses),
        "uksa": (uksa_scraper.COURSE_NAMES, uksa_scraper.fetch_events_for_courses),
    }.get(provider, (None, None))

    if not provider_courses:
        raise HTTPException(status_code=404, detail=f"Unknown provider slug: {provider!r}")

    if slug not in provider_courses:
        raise HTTPException(status_code=404, detail=f"Unknown course slug: {slug!r}")

    events = await provider_fetch([slug])
    return await calendar_response(events, calendar_name=f"UKSA - {uksa_scraper.COURSE_NAMES[slug]}")


@app.get("/group/{slug}")
async def course_group(slug: str):
    if slug not in GROUPS:
        raise HTTPException(status_code=404, detail=f"Unknown group slug: {slug!r}")

    provider_course_slugs = {"uksa": [], "seascope": []}
    for entry in GROUPS[slug]:
        provider_course_slugs[entry["provider"]].append(entry["slug"])

    provider_events = await asyncio.gather(
        uksa_scraper.fetch_events_for_courses(provider_course_slugs["uksa"]),
        seascope_scraper.fetch_events_for_courses(provider_course_slugs["seascope"]),
    )

    events = [event for events in provider_events for event in events]
    return await calendar_response(events, calendar_name=f"Group {slug}")
