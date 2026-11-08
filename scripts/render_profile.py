#!/usr/bin/env python3
"""Generate GitHub-safe, live profile graphics from real public contribution data.

Run in GitHub Actions (METRICS_TOKEN and Pillow installed).
SVG is an image, not a script: open the raw SVG for per-day title tooltips.
The GIFs provide light animation because GitHub READMEs disallow scripts/CSS.
"""
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

LOGIN = "antoniusjairus4"
OUT = Path("assets")
OUT.mkdir(exist_ok=True)
INK, PANEL, BORDER = "#0b111a", "#101d2b", "#234457"
TEXT, MUTED = "#e7f6ff", "#8eafc0"
BLUE, CYAN, MINT, VIOLET = "#348de7", "#28c5d5", "#6de8a5", "#af98fc"
LEVELS = {
    "NONE": "#172c3d",
    "FIRST_QUARTILE": "#19517e",
    "SECOND_QUARTILE": "#247fbb",
    "THIRD_QUARTILE": "#1ab9c6",
    "FOURTH_QUARTILE": "#6de8a5",
}
TOKEN = os.environ.get("METRICS_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("METRICS_TOKEN is missing: nothing was overwritten.")


def request_json(url, payload=None):
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/vnd.github+json",
        "User-Agent": "antoniusjairus4-profile-graphics",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    with urlopen(Request(url, data=data, headers=headers), timeout=25) as response:
        return json.load(response)


def calendar_data():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365)
    query = """
    query($login: String!, $start: DateTime!, $end: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $start, to: $end) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    result = request_json(
        "https://api.github.com/graphql",
        {
            "query": query,
            "variables": {
                "login": LOGIN,
                "start": start.isoformat(),
                "end": now.isoformat(),
            },
        },
    )
    if result.get("errors"):
        raise RuntimeError("GitHub contribution query failed: " +
                           str(result["errors"][0].get("message", "unknown error")))
    return result["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def recent_public_events():
    try:
        events = request_json(
            "https://api.github.com/users/" + LOGIN + "/events/public?per_page=100"
        )
    except Exception as err:
        print("Public activity feed unavailable:", type(err).__name__)
        return []
    rows = []
    labels = {
        "PushEvent": "PUSH",
        "PullRequestEvent": "PULL REQUEST",
        "CreateEvent": "NEW REPO / BRANCH",
        "ReleaseEvent": "RELEASE",
        "IssuesEvent": "ISSUE",
    }
    for event in events if isinstance(events, list) else []:
        kind = event.get("type")
        if kind not in labels:
            continue
        repo = (event.get("repo") or {}).get("name", "").split("/")[-1]
        if repo == LOGIN and kind == "PushEvent":
            continue  # Skip profile graphics maintenance commits in the timeline.
        date = (event.get("created_at") or "")[:10]
        if not repo or not date:
            continue
        if rows and rows[-1][:3] == (labels[kind], repo, date):
            continue
        rows.append((labels[kind], repo, date))
        if len(rows) == 5:
            break
    return rows


def svg_start(w, h):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img">',
        '<defs>',
        '<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">'
        '<stop stop-color="#348de7"/><stop offset=".52" stop-color="#28c5d5"/>'
        '<stop offset="1" stop-color="#6de8a5"/></linearGradient>',
        '<radialGradient id="glow"><stop stop-color="#154d6a" stop-opacity=".7"/>'
        '<stop offset="1" stop-color="#0b111a" stop-opacity="0"/></radialGradient>',
        '</defs>',
        f'<rect width="{w}" height="{h}" rx="22" fill="{INK}"/>',
        '<rect x="1" y="1" width="958" height="' +
        str(h-2) + f'" rx="21" fill="none" stroke="{BORDER}"/>',
        '<rect x="26" y="0" width="' + str(w-52) +
        '" height="3" rx="1" fill="url(#edge)"/>',
    ]


def txt(x, y, value, size=19, fill=TEXT, weight=500, anchor="start", spacing=0):
    safe = escape(str(value))
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'fill="{fill}" font-family="Segoe UI,Arial,sans-serif" '
            f'font-size="{size}" font-weight="{weight}" '
            f'letter-spacing="{spacing}">{safe}</text>')


def render_hero():
    p = svg_start(960, 290)
    p += [
        '<circle cx="770" cy="110" r="208" fill="url(#glow)"/>',
        '<path d="M500 238 C660 40 775 40 963 148" fill="none" stroke="#195c78" stroke-width="1"/>',
        '<path d="M520 255 C690 70 808 60 969 175" fill="none" stroke="#22828d" stroke-width="1" opacity=".65"/>',
        '<circle cx="808" cy="139" r="75" stroke="#3baab8" fill="none" opacity=".38"/>',
        '<circle cx="808" cy="139" r="53" stroke="#71ddc0" fill="none" opacity=".28"/>',
        '<path d="M808 51 V226 M723 139 H895" stroke="#3baab8" opacity=".32"/>',
        txt(52, 51, "AJ / DEVELOPMENT CONSOLE", 13, CYAN, 700, spacing=3),
        txt(50, 123, "ANTONIUS", 64, TEXT, 800, spacing=1.5),
        txt(51, 188, "JAIRUS R", 64, MINT, 800, spacing=1.5),
        txt(53, 233, "FULL-STACK  /  CREATIVE ENGINEERING  /  AI + ML", 16, MUTED, 600, spacing=1),
        '<rect x="48" y="259" width="146" height="3" rx="1" fill="url(#edge)"/>',
        txt(811, 147, "A/J", 43, TEXT, 800, anchor="middle"),
        txt(810, 248, "SHIP  •  LEARN  •  REPEAT", 13, CYAN, 700, anchor="middle", spacing=1),
        '</svg>',
    ]
    (OUT / "hero.svg").write_text("\n".join(p), encoding="utf-8")


def render_calendar(calendar, events):
    weeks = calendar["weeks"]
    total = int(calendar.get("totalContributions", 0))
    latest = [d for w in weeks for d in w["contributionDays"]]
    latest = [d for d in latest if d["contributionCount"]]
    active_days = sum(d["contributionCount"] > 0 for w in weeks for d in w["contributionDays"])
    max_day = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0)
    total_events = len(events)
    h = 800
    p = svg_start(960, h)
    p += [
        txt(49, 70, "04 / THE BUILD LOG", 20, CYAN, 700, spacing=2.6),
        txt(49, 116, "Every commit leaves a trace.", 34, TEXT, 750),
        txt(50, 149, "Live contribution intensity  /  updated from GitHub", 17, MUTED),
        '<rect x="48" y="172" width="864" height="96" rx="14" fill="#101e2e" stroke="#1d384b"/>',
        txt(68, 204, "CONTRIBUTIONS / LAST 365 DAYS", 13, MUTED, 700, spacing=1.1),
        txt(67, 246, f"{total:,}", 36, MINT, 750),
        txt(333, 204, "ACTIVE DAYS", 13, MUTED, 700, spacing=1.1),
        txt(333, 244, str(active_days), 31, CYAN, 700),
        txt(555, 204, "BUSIEST DAY", 13, MUTED, 700, spacing=1.1),
        txt(555, 244, str(max_day) + " contributions", 27, BLUE, 700),
        txt(50, 316, "ACTIVITY MAP", 17, TEXT, 700, spacing=1),
        txt(910, 316, "MORE ACTIVITY → BRIGHTER", 12, MUTED, 700, anchor="end", spacing=.5),
    ]
    x0, y0, pitch, cell = 51, 361, 16.25, 11.9
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, name in enumerate(names):
        if i in (0, 2, 4):
            p.append(txt(23, y0 + i*16.25+10, name, 12, MUTED, anchor="middle"))
    months = set()
    for widx, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = datetime.strptime(day["date"], "%Y-%m-%d").date()
            month_id = (date.year, date.month)
            if date.day <= 7 and month_id not in months:
                months.add(month_id)
                p.append(txt(round(x0+widx*pitch, 1), 343,
                             date.strftime("%b"), 13, MUTED, 600))
            row = date.weekday()
            count = int(day.get("contributionCount", 0))
            color = LEVELS.get(day.get("contributionLevel", "NONE"), LEVELS["NONE"])
            x, y = round(x0+widx*pitch, 2), round(y0+row*pitch, 2)
            date_label = date.strftime("%a, %d %b %Y")
            label = f"{date_label}: {count} contribution" + ("" if count == 1 else "s")
            p.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}">'
                     f'<title>{escape(label)}</title></rect>')
    p += [
        txt(51, 501, "Less", 13, MUTED),
    ]
    for j, color in enumerate(LEVELS.values()):
        p.append(f'<rect x="{90+j*21}" y="489" width="13" height="13" rx="2" fill="{color}"/>')
    p += [
        txt(213, 501, "More", 13, MUTED),
        txt(909, 502, "Colors represent contribution ranges, not individual commits.", 12, MUTED, anchor="end"),
        '<path d="M49 527 H912" stroke="#234457"/>',
        txt(49, 560, "RECENT PUBLIC ACTIVITY", 18, TEXT, 700, spacing=1),
        txt(912, 560, f"{total_events} RECENT EVENTS DISPLAYED", 12, MUTED, 600, anchor="end"),
    ]
    if not events:
        p.append(txt(53, 612, "No recent public pushes or pull requests were returned by GitHub.", 17, MUTED))
    else:
        for i, (kind, repo, date) in enumerate(events):
            y = 603 + i*40
            p += [
                f'<circle cx="59" cy="{y-6}" r="4" fill="{[CYAN,BLUE,MINT,VIOLET,CYAN][i]}"/>',
                txt(76, y, kind, 12, [CYAN,BLUE,MINT,VIOLET,CYAN][i], 700, spacing=.7),
                txt(240, y, repo[:34] + ("…" if len(repo)>34 else ""), 16, TEXT, 600),
                txt(904, y, datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y"), 14, MUTED, anchor="end"),
            ]
    p.append('</svg>')
    (OUT / "build-log.svg").write_text("\n".join(p), encoding="utf-8")
    print(f"Calendar updated: {total} contributions, {active_days} active days")


def font(size, bold=False):
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/" + filename, size)


def project_loop():
    frames = []
    labels = ["DESIGN", "DEVELOP", "DEPLOY", "EVOLVE"]
    accent = ["#348de7", "#28c5d5", "#6de8a5", "#af98fc"]
    for tick in range(24):
        im = Image.new("RGB", (960, 136), INK)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((1, 1, 958, 134), radius=17, outline=BORDER, width=2)
        d.text((26, 15), "THE SHIPPING LOOP   //   ALWAYS IN MOTION", fill=MUTED, font=font(13, True))
        active = tick // 6
        for i, label in enumerate(labels):
            x = 25 + i*232
            box = (x, 45, x+207, 115)
            fill = "#142b3d" if i == active else "#10202e"
            d.rounded_rectangle(box, radius=11, fill=fill,
                                outline=accent[i] if active==i else BORDER, width=2)
            d.text((x+21, 64), f"0{i+1}  {label}", font=font(17, True),
                   fill=accent[i] if active==i else "#8eafc0")
            if active == i:
                width = int(190*(tick%6+1)/6)
                d.rounded_rectangle((x+10,106,x+10+width,109),radius=2,fill=accent[i])
        frames.append(im)
    frames[0].save(OUT / "project-loop.gif", save_all=True, append_images=frames[1:],
                   duration=150, loop=0, optimize=True)


def contact_loop():
    frames = []
    for tick in range(24):
        im = Image.new("RGB", (960, 145), INK)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((1,1,958,142),radius=19,outline=BORDER,width=2)
        d.text((32,36),"HAVE AN IDEA WORTH BUILDING?",font=font(25,True),fill=TEXT)
        d.text((33,83),"Web experiences  •  Full-stack products  •  Collaborations",
               font=font(15),fill=MUTED)
        x1, y1, x2, y2 = 698, 39, 922, 108
        d.rounded_rectangle((x1,y1,x2,y2), radius=15, fill="#146876",outline=CYAN,width=2)
        d.text((734,57),"LET'S TALK  >",font=font(21,True),fill="#e7f6ff")
        # Soft moving blue->mint underline; no flashing.
        progress = tick/(len(range(24))-1)
        marker = int((x2-x1-36)*progress)
        d.rounded_rectangle((x1+15+marker,y2-8,x1+29+marker,y2-5),
                            radius=2,fill=MINT)
        frames.append(im)
    frames[0].save(OUT / "contact-loop.gif", save_all=True,
                   append_images=frames[1:], duration=130, loop=0, optimize=True)


def main():
    cal = calendar_data()  # fail safely rather than publish an empty graph
    events = recent_public_events()
    render_hero()
    render_calendar(cal, events)
    project_loop()
    contact_loop()
    print("Created assets/hero.svg, build-log.svg, project-loop.gif and contact-loop.gif")


if __name__ == "__main__":
    main()
