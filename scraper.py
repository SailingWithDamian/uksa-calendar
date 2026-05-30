import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx
from bs4 import BeautifulSoup

_CACHE: dict[str, tuple[datetime, list["CourseEvent"]]] = {}
_CACHE_TTL = timedelta(hours=24)

COURSE_NAMES: dict[str, str] = {
    # STCW Safety Training
    "elementary-first-aid": "Elementary First Aid Course (STCW A-VI/1-3)",
    "personal-survival-techniques": "Personal Survival Techniques (STCW A-VI/1-1)",
    "proficiency-for-persons-in-charge-of-medical-care-on-board-ship": "Proficiency in Medical Care (STCW)",
    "proficiency-in-medical-first-aid": "Proficiency in Medical First Aid (A-VI/4-1)",
    "stcw-basic-training": "STCW Basic Safety Training Course",
    "stcw-basic-safety-training-update": "STCW Basic Safety Training Update",
    # Engineering
    "mca-approved-engineer-course": "MCA Approved Engine Certificate 1 (AEC1) Course",
    "mca-approved-engineer-course-2": "MCA Approved Engine Certificate 2 (AEC2) Course",
    "small-vessel-engineering-workshop-skills": "Small Vessel Workshop Skills Training",
    # Radio Communication
    "gmdss-general-operators-certificate-goc": "GMDSS General Operators Certificate (GOC)",
    # Leadership & Management
    "human-element-leadership-and-management-management-level": "Human Element, Leadership and Management (Management Level)",
    "human-element-leadership-and-management-operational": "Human Element, Leadership and Management (Operational Level)",
    # Security
    "ships-security-officer": "ISPS Ships Security Officer (SSO)",
    "proficiency-in-designated-security-duties-pdsd": "Proficiency in Designated Security Duties PDSD (STCW A-VI/6-2)",
    # Master (Code Vessels <200gt / OOW <500gt)
    "orals-preparation-master-200gt-oow-500gt": "Orals Preparation (Master <200gt) OOW (Yachts less than 500gt)",
    "small-ships-electronic-charting-systems-and-bridge-watchkeeping": "Small Ships Electronic Charting Systems and Bridge Watchkeeping",
    "small-ships-radar-and-meteorology": "Small Ships Radar and Meteorology",
    "workboat-operations-course-master-workboat-500gt": "Workboat Operations Course (Master Workboat <500GT)",
    # OOW (Yachts <3000gt)
    "efficient-deck-hand": "Efficient Deck Hand (EDH)",
    "electronic-chart-display-and-information-systems": "Electronic Chart Display and Information Systems (ECDIS)",
    "general-ship-knowledge-oow-yachts": "General Ship Knowledge (OOW Yachts)",
    "navigation-and-radar-oow-yachts": "Navigation and Radar (OOW Yachts) Course",
    "orals-preparation-master-yachts-less-than-500gt-3000gt": "Orals Preparation Officer of the Watch (Yachts less than 3000gt)",
    "proficiency-in-survival-craft-and-rescue-boats-other-than-fast-rescue-boats-restricted": "Proficiency in Survival Craft and Rescue Boats Other Than Fast Rescue Boats (Restricted)",
    # Chief Mate (Yachts <3000gt)
    "advanced-fire-fighting": "Advanced Fire Fighting (STCW A-VI/4-1)",
    # Master (Yachts <500gt/3000gt)
    "business-and-law-master-yachts": "Business and Law (Master Yachts)",
    "celestial-navigation-refresher-and-exam": "Celestial Navigation Refresher and Exam",
    "navigation-arpa-and-radar-simulator-master-yachts": "Navigation, Radar and ARPA Simulator (Master Yachts)",
    "seamanship-and-meteorology-master-yachts": "Seamanship and Meteorology (Master Yachts)",
    "stability-master-yachts": "Stability (Master Yachts) Course",
    # Workboat
    "small-workboat-stability-course": "Small Workboat Stability Course",
}


@dataclass
class CourseEvent:
    course_slug: str
    course_name: str
    start: date
    end: date
    status: str | None


async def scrape_course_events(slug: str, client: httpx.AsyncClient) -> list[CourseEvent]:
    cached_at, cached_events = _CACHE.get(slug, (None, None))
    if cached_at and datetime.now() - cached_at < _CACHE_TTL:
        return cached_events

    course_name = COURSE_NAMES.get(slug, slug)

    response = await client.get(f"https://uksa.org/course/{slug}/", timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    events: list[CourseEvent] = []

    for row in soup.select("table tbody tr"):
        cells = row.find_all("td")

        start_date, end_date = cells[0].find("strong").text.split(" → ", 2)
        start = datetime.strptime(start_date, "%d %b %Y").date()
        end = datetime.strptime(end_date, "%d %b %Y").date()

        pill = cells[0].find("span", class_="pill")
        status = pill.get_text(strip=True) if pill else None

        if status == "Sold out":
            continue

        events.append(
            CourseEvent(
                course_slug=slug,
                course_name=course_name,
                start=start,
                end=end,
                status=status,
            )
        )

    _CACHE[slug] = (datetime.now(), events)
    return events


async def fetch_events_for_courses(slugs: list[str]) -> list[CourseEvent]:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[scrape_course_events(slug, client) for slug in slugs])
    # Preserve input order across the merged list.
    return [event for events in results for event in events]
