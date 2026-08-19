from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import CourseEvent

CACHE: dict[str, tuple[datetime, list["CourseEvent"]]] = {}
CACHE_TTL = timedelta(hours=24)
