import asyncio
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from cache import CACHE, CACHE_TTL
from models import CourseEvent

COURSE_NAMES: dict[str, str] = {
    # Engineering
    "mca-aec1-course": "MCA Approved Engine Course 1 (AEC1)",
    "mca-approved-engine-course-2-aec2": "MCA Approved Engine Course 2 (AEC2)",
    # BST
    "stcw-course-basic-safety-training": "STCW Basic Safety Training",
    "stcw-refresher-training-updated-proficiency-in-fire-and-pst": "STCW Refresher Training / Updated Proficiency in Fire and PST",
    "stcw-personal-survival-techniques-pst": "STCW Personal Survival Techniques (PST)",
    "stcw-fire-prevention-and-fire-fighting-fpff": "STCW Fire Prevention and Fire Fighting (FPFF)",
    "stcw-elementary-first-aid-efa": "STCW Elementary First Aid (EFA)",
    "stcw-personal-safety-and-social-responsibility-pssr": "STCW Personal Safety and Social Responsibility (PSSR)",
    "stcw-proficiency-in-security-awareness-psa": "STCW Proficiency in Security Awareness (PSA)",
    # AFF
    "stcw-advanced-firefighting": "STCW Advanced Firefighting",
    "stcw-updated-advanced-firefighting": "STCW Updated Advanced Firefighting",
    # Medical
    "proficiency-in-medical-first-aid-4-day-course-stcw": "Proficiency In Medical First Aid 4-Day Course (STCW)",
    "proficiency-in-medical-care-5-day-stcw": "Proficiency in Medical Care 5-Day (STCW)",
    "stcw-medical-care-on-board-refresher": "STCW Medical Care On Board- Refresher",
    # Security
    "stcw-proficiency-in-designated-security-duties-pdsd": "STCW Proficiency In Designated Security Duties (PDSD)",
    # Crowd & Crisis Management
    "stcw-crowd-management": "STCW Crowd Management",
    "stcw-crisis-management-and-human-behaviour": "STCW Crisis Management and Human Behaviour",
    # Deck
    "efficient-deckhand-edh": "Efficient Deckhand (EDH)",
}


async def scrape_course_events(slug: str, client: httpx.AsyncClient) -> list[CourseEvent]:
    cached_at, cached_events = CACHE.get(slug, (None, None))
    if cached_at and datetime.now() - cached_at < CACHE_TTL:
        return cached_events

    course_name = COURSE_NAMES.get(slug, slug)

    response = await client.get(f"https://seascopemaritimetraining.com/courses/{slug}/", timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    events: list[CourseEvent] = []

    for row in soup.select("table.seascope-course-dates-table tbody tr"):
        cells = row.find_all("td")
        location = cells[0].text.strip()
        start = datetime.strptime(cells[1].text, "%d %B %Y").date()
        end = datetime.strptime(cells[2].text, "%d %B %Y").date()

        events.append(
            CourseEvent(
                course_slug=slug,
                course_name=course_name,
                start=start,
                end=end,
                location=location,
            )
        )

    # CACHE[slug] = (datetime.now(), events)
    return events


async def fetch_events_for_courses(slugs: list[str]) -> list[CourseEvent]:
    if not slugs:
        return []

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[scrape_course_events(slug, client) for slug in slugs])
    # Preserve input order across the merged list.
    return [event for events in results for event in events]
