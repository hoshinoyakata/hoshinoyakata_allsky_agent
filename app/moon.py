from datetime import datetime, timezone

SYNODIC_MONTH = 29.53058867
KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

def moon_age(now=None):
    now = now or datetime.now(timezone.utc)
    days = (now - KNOWN_NEW_MOON).total_seconds() / 86400.0
    return days % SYNODIC_MONTH

def moon_phase_name(age):
    if age < 1.5: return "新月"
    if age < 7.4: return "上弦へ"
    if age < 9.0: return "上弦"
    if age < 14.8: return "満月へ"
    if age < 16.3: return "満月"
    if age < 22.1: return "下弦へ"
    if age < 23.6: return "下弦"
    return "新月へ"

def moon_info():
    age = moon_age()
    return {"age": round(age, 1), "phase": moon_phase_name(age)}
