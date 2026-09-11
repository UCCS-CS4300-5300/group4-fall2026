PROJECT_INFO = {
    "name": "Trailhead",
    "description": "Trailhead helps teams coordinate work and surface blockers.",
}


def project_summary():
    return f"{PROJECT_INFO['name']}: {PROJECT_INFO['description']}"


def risk_level(open_blockers: int) -> str:
    if open_blockers >= 4:
        return "HIGH"
    if open_blockers >= 2:
        return "MEDIUM"
    return "LOW"
