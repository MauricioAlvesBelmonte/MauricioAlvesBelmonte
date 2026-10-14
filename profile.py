"""Gera dark_mode.svg e light_mode.svg do README de perfil.

Uso: python profile.py
Lê ACCESS_TOKEN e GITHUB_TOKEN do ambiente para atualizar os stats do GitHub.
Sem token, ou se a API falhar, mantém os últimos valores salvos em stats.json.
"""
import datetime
import html
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
USER = "MauricioAlvesBelmonte"
CAREER_START = datetime.date(2020, 6, 24)
WIDTH = 58  # largura, em caracteres, de cada linha do card


def uptime(start=CAREER_START):
    t = datetime.date.today()
    y, m, d = t.year - start.year, t.month - start.month, t.day - start.day
    if d < 0:
        m -= 1
        d += 30
    if m < 0:
        y -= 1
        m += 12
    return f"{y} anos, {m} meses, {d} dias"


def graphql(token, query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["user"]


def fetch_stats():
    """Repos vêm do ACCESS_TOKEN (enxerga os privados). Contribuições vêm do
    GITHUB_TOKEN, que vê o mesmo total do perfil público (com as privadas
    anonimizadas); o token fine-grained do dono conta menos que isso."""
    cache = ROOT / "stats.json"
    stats = json.loads(cache.read_text()) if cache.exists() else {"repos": 0, "contributions": 0}
    access, public = os.environ.get("ACCESS_TOKEN"), os.environ.get("GITHUB_TOKEN")
    try:
        if access or public:
            repos = graphql(access or public, "query($login:String!){user(login:$login){repositories(ownerAffiliations:OWNER){totalCount}}}")
            n = repos["repositories"]["totalCount"]
            # Sem ACCESS_TOKEN só os repos públicos aparecem: não deixa o número regredir.
            stats["repos"] = n if access else max(stats["repos"], n)
        if public:
            cal = graphql(public, "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions}}}}")
            stats["contributions"] = cal["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        stats = {k: stats[k] for k in ("repos", "contributions")}
        cache.write_text(json.dumps(stats, indent=1) + "\n")
    except Exception as e:
        print(f"stats: mantendo valores anteriores ({e})")
    return stats


def kv(k, v):
    dots = WIDTH - len(k) - len(v) - 3
    return [("key", k), ("cc", ": " + "." * dots + " "), ("value", v)]


def sec(t):
    return [("text", t + " "), ("cc", "-" * (WIDTH - len(t) - 1))]


def lines(stats):
    return [
        [("text", "mauricio"), ("cc", "@"), ("text", "belmonte "), ("cc", "-" * (WIDTH - 18))],
        kv("OS", "Fedora Linux 44, Windows 11"),
        kv("Uptime", uptime()),
        kv("Host", "SIGE Cloud, BM Menu"),
        kv("Kernel", "Dev C#/.NET · ERP e integrações"),
        kv("IDE", "VS Code, Claude Code, OpenCode"),
        kv("Locale", "Rio Grande do Sul, BR"),
        [],
        kv("Languages.Programming", "C#, Python, TypeScript"),
        kv("Frameworks", "ASP.NET, Angular, React, Svelte, FastAPI"),
        kv("Databases", "MongoDB, PostgreSQL, SQLite"),
        kv("DevOps.AI", "Docker, Actions, Claude, Ollama"),
        kv("Languages.Real", "Português"),
        [],
        sec("Contact"),
        kv("Email", "mauricioabelmonte@gmail.com"),
        kv("LinkedIn", "mauricioabelmonte-dev"),
        kv("Web", "mauriciobelmonte.dev.br"),
        [],
        sec("GitHub Stats"),
        kv("Repos", str(stats["repos"])),
        kv("Contributions (1y)", f"{stats['contributions']:,}"),
    ]


# Paleta do portfolio (mauriciobelmonte.dev.br)
THEMES = {
    "dark": dict(bg="#1c1c1c", text="#ececec", key="#6ea8ff", value="#ececec", cc="#5d5d5d", border="#2b2b2b", prompt="#6ea8ff", muted="#9b9b9b"),
    "light": dict(bg="#ffffff", text="#171717", key="#2e6bff", value="#171717", cc="#a3a19b", border="#e0ded7", prompt="#2e6bff", muted="#66645f"),
}


def svg(theme, logos, info):
    P = THEMES[theme]
    lh, fs, cw = 20, 15, 9.0
    n, step = len(logos), 2.6
    total, on = n * step, 100 / n
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,\'DejaVu Sans Mono\',monospace" width="985" height="550" font-size="{fs}px">',
        f"""<style>
@font-face{{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';font-display:swap;-webkit-size-adjust:109%;size-adjust:109%}}
.key{{fill:{P['key']}}}.value{{fill:{P['value']}}}.cc{{fill:{P['cc']}}}.text{{fill:{P['text']}}}.pr{{fill:{P['prompt']}}}
text,tspan{{white-space:pre}}
.logo{{opacity:0;animation:cyc {total}s infinite}}
@keyframes cyc{{0%{{opacity:0}}{on * 0.08:.2f}%{{opacity:1}}{on * 0.9:.2f}%{{opacity:1}}{on:.2f}%{{opacity:0}}100%{{opacity:0}}}}
.cur{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.logo{{animation:none}}.logo:first-of-type{{opacity:1}}}}
</style>""",
        f'<rect x="0.5" y="0.5" width="984" height="549" fill="{P["bg"]}" stroke="{P["border"]}" rx="15"/>',
    ]
    lx, ly = 22, 50
    for i, logo in enumerate(logos):
        col = logo["color"]
        out.append(f'<g class="logo" style="animation-delay:{i * step:.1f}s;color:{P["text"]}">')
        out.append(f'<text x="{lx}" y="{ly}" fill="{col}">' + "".join(
            f'<tspan x="{lx}" y="{ly + j * lh}">{html.escape(r)}</tspan>' for j, r in enumerate(logo["art"])) + "</text>")
        out.append(f'<text x="{lx}" y="{ly + 20 * lh + 22}"><tspan class="pr">~/daily</tspan><tspan class="cc"> $ </tspan>'
                   f'<tspan class="text">using </tspan><tspan fill="{col}">{html.escape(logo["label"])}</tspan></text>')
        out.append("</g>")
    ix, iy = 410, 30
    out.append(f'<text x="{ix}" y="{iy}" class="text">')
    for j, line in enumerate(info):
        out.append(f'<tspan x="{ix}" y="{iy + j * lh}">' + "".join(
            f'<tspan class="{c}">{html.escape(s)}</tspan>' for c, s in line) + "</tspan>")
    out.append("</text>")
    fy = iy + len(info) * lh + 28
    out.append(f'<line x1="{ix}" x2="{ix + WIDTH * cw}" y1="{fy - 20}" y2="{fy - 20}" stroke="{P["border"]}"/>')
    out.append(f'<text x="{ix}" y="{fy}"><tspan class="pr">❯</tspan><tspan class="text"> git commit -m </tspan>'
               f'<tspan fill="{P['muted']}">"funciona (não sei bem por quê)"</tspan><tspan class="text cur">█</tspan></text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    logos = json.loads((ROOT / "logos.json").read_text())
    info = lines(fetch_stats())
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(svg(theme, logos, info))
