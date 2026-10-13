"""Server-side citation resolution.

The LLM only ever sees `unit_id`s. Display strings and deep links are derived
here from the stored location, so the model can never emit (or fabricate) a
page, slide or timestamp.
"""

from app.domain.types import Location


def _fmt_timestamp(total_s: float) -> str:
    total = max(0, int(total_s))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def display_string(location: Location, source_title: str) -> str:
    kind = location.kind()
    if kind == "page" and location.page is not None:
        return f"{source_title} · p. {location.page}"
    if kind == "slide" and location.slide is not None:
        return f"{source_title} · slide {location.slide}"
    assert location.t_start_s is not None
    return f"{source_title} · {_fmt_timestamp(location.t_start_s)}"


def deep_link(location: Location) -> str:
    kind = location.kind()
    base = f"/source/{location.source_id}"
    if kind == "page" and location.page is not None:
        return f"{base}?page={location.page}"
    if kind == "slide" and location.slide is not None:
        return f"{base}?slide={location.slide}"
    assert location.t_start_s is not None
    return f"{base}?t={int(location.t_start_s)}"
