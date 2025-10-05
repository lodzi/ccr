import re

def youtube_iframe(url: str) -> str:
    if not url:
        return ""
    patterns = [
        r"(?:v=|vi=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:embed/)([A-Za-z0-9_-]{11})"
    ]
    vid = None
    for p in patterns:
        m = re.search(p, url)
        if m:
            vid = m.group(1); break
    if not vid:
        return ""
    src = f"https://www.youtube.com/embed/{vid}"
    return f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;"><iframe src="{src}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen style="position:absolute;top:0;left:0;width:100%;height:100%;"></iframe></div>'
