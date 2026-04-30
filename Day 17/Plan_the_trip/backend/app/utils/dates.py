from datetime import date, datetime, timedelta


def parse_date(value: str | date | None, fallback: date) -> date:
    if isinstance(value, date):
        return value
    if not value:
        return fallback
    return datetime.fromisoformat(str(value)).date()


def date_range(start: str | date | None, end: str | date | None) -> list[date]:
    today = date.today()
    start_date = parse_date(start, today + timedelta(days=14))
    end_date = parse_date(end, start_date + timedelta(days=3))
    if end_date < start_date:
        end_date = start_date
    return [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
