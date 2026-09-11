PROJECT_INFO = {
    "name": "Trailhead",
    "description": "A simple team project planning tool for student software teams.",
}


def project_summary():
    return f"{PROJECT_INFO['name']}: {PROJECT_INFO['description']}"


def risk_level(open_blockers: int) -> str:
    if open_blockers >= 4:
        return "HIGH"
    if open_blockers >= 2:
        return "MEDIUM"
    return "LOW"
