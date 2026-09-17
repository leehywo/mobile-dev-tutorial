"""unity-indie-roadmap.md → hmini 허브용 학습 페이지(단일 HTML).

허브(`~/Dev/hmini-dash`)는 `/p/unity-roadmap` 을 열 때마다 이 스크립트를 돌리고
`tools/dash/unity_roadmap.html` 을 읽어 내보낸다. 원본은 md 하나뿐이다 — 문서를 고치면
화면이 따라온다. md 가 안 바뀌었으면 다시 만들지 않는다.

화면 구성:
  · PART 단위 칩 네비(스크롤 연동)
  · 절(h2)마다 "완료" 체크 — 진도는 그 브라우저의 localStorage 에 남는다(폰·맥 따로)
  · 폰 가독성: viewport 메타, 표는 카드로 쌓고 코드블록은 접는다

실행: python3 tools/dash/render.py
"""
from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "unity-indie-roadmap.md"
OUT = HERE / "unity_roadmap.html"
GITHUB = "https://github.com/leehywo/mobile-dev-tutorial/blob/main/"

CSS = r"""
:root{
  --ground:#F4F5F7; --surface:#FFFFFF; --ink:#181B22; --muted:#626A78;
  --line:#E0E3EA; --accent:#4B5BD6; --accent-soft:#E9EBFB; --accent-ink:#3441A8;
  --done:#1E9E6A; --code-bg:#EEF0F5;
  --shadow:0 1px 2px rgba(20,24,40,.04),0 8px 28px rgba(20,24,40,.06);
  --sans:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",Pretendard,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --ground:#0E1016; --surface:#161922; --ink:#E6E8EF; --muted:#8C93A3;
  --line:#262A36; --accent:#8C98F5; --accent-soft:#1F2340; --accent-ink:#AEB6FA;
  --done:#35C98B; --code-bg:#1B1E29;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.3);}}

*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16.5px;line-height:1.78;-webkit-font-smoothing:antialiased;word-break:keep-all}

nav{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--ground) 88%,transparent);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.nav-in{max-width:52rem;margin:0 auto;display:flex;gap:6px;overflow-x:auto;
  padding:10px 16px;scrollbar-width:none;align-items:center}
.nav-in::-webkit-scrollbar{display:none}
nav a{flex:none;font-size:13px;font-weight:650;color:var(--muted);
  text-decoration:none;padding:5px 10px;border-radius:6px;border:1px solid transparent}
nav a:hover{color:var(--ink);border-color:var(--line);background:var(--surface)}
nav a.active{color:#fff;background:var(--accent);border-color:var(--accent)}
@media (prefers-color-scheme:dark){nav a.active{color:var(--ground)}}
nav .prog{flex:none;font-family:var(--mono);font-size:12px;color:var(--done);
  font-weight:700;padding-right:6px}
section.ch{scroll-margin-top:60px}
section.ch h2{scroll-margin-top:64px}

header.hero{max-width:52rem;margin:0 auto;padding:56px 20px 32px}
.hero .eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 14px}
.hero h1{font-size:clamp(28px,6vw,42px);line-height:1.18;margin:0;font-weight:800;
  letter-spacing:-.03em;text-wrap:balance}
.hero .intro{color:var(--muted);margin-top:14px}
.hero .intro p{margin:.5em 0}
.bar{margin-top:22px;height:8px;border-radius:99px;background:var(--line);overflow:hidden}
.bar i{display:block;height:100%;width:0;background:var(--done);transition:width .3s}
.bar-label{font-family:var(--mono);font-size:12.5px;color:var(--muted);margin-top:8px;
  display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.bar-label button{font:inherit;color:var(--muted);background:none;border:0;padding:0;
  text-decoration:underline;cursor:pointer}

main{max-width:52rem;margin:0 auto;padding:0 20px 90px}
section.ch{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:clamp(22px,4.5vw,44px);margin-top:26px;box-shadow:var(--shadow);overflow-wrap:break-word}
.ch-label{font-family:var(--mono);font-size:12px;letter-spacing:.16em;font-weight:700;
  color:var(--accent);text-transform:uppercase;margin:0 0 4px}
section.ch>h1{font-size:clamp(22px,4vw,29px);line-height:1.25;margin:0 0 6px;
  font-weight:800;letter-spacing:-.02em;text-wrap:balance}
section.ch h2{font-size:20px;font-weight:800;letter-spacing:-.01em;margin:2.2em 0 .6em;
  padding-top:1.1em;border-top:1px solid var(--line);display:flex;gap:10px;align-items:flex-start}
section.ch h2 .t{flex:1}
section.ch h3{font-size:16.5px;font-weight:700;margin:1.8em 0 .5em;color:var(--accent-ink)}
label.done{flex:none;display:inline-flex;align-items:center;gap:6px;font-size:13px;
  font-weight:650;color:var(--muted);border:1px solid var(--line);border-radius:99px;
  padding:3px 11px 3px 8px;cursor:pointer;user-select:none;margin-top:2px;white-space:nowrap}
label.done input{accent-color:var(--done);width:16px;height:16px;margin:0}
label.done:has(input:checked){color:var(--done);border-color:color-mix(in srgb,var(--done) 45%,transparent);
  background:color-mix(in srgb,var(--done) 10%,transparent)}
h2.is-done .t{color:var(--muted)}

p{margin:.85em 0}
strong{font-weight:750}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}
ul,ol{padding-left:1.35em;margin:.8em 0}
li{margin:.3em 0}
li::marker{color:var(--accent)}
blockquote{margin:1.2em 0;padding:14px 18px;border-left:3px solid var(--accent);
  background:var(--accent-soft);border-radius:0 10px 10px 0;font-size:15.5px}
blockquote p{margin:.4em 0}

code{font-family:var(--mono);font-size:.86em;background:var(--code-bg);padding:.15em .4em;border-radius:5px}
pre{background:var(--code-bg);border:1px solid var(--line);border-radius:10px;
  padding:14px 16px;overflow-x:auto;line-height:1.65;margin:1.1em 0}
pre code{background:none;padding:0;font-size:13.5px}

.tbl{overflow-x:auto;margin:1.2em 0;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14.5px;min-width:480px}
th{font-size:12.5px;color:var(--muted);text-align:left;padding:10px 14px;
  border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--ground) 55%,transparent)}
td{padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}

footer{max-width:52rem;margin:0 auto;padding:34px 20px;color:var(--muted);font-size:13px;font-family:var(--mono)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ── 폰: 가로 스크롤 없애기. 이 블록은 CSS 맨 끝에 있어야 한다(뒤 선언에 덮이지 않게) ── */
@media (max-width:760px){
  html,body{font-size:18px}
  main{padding:0 10px 80px}
  header.hero{padding:36px 14px 22px}
  section.ch{padding:18px 14px}
  section.ch h2{font-size:1.25rem;flex-wrap:wrap}
  blockquote{font-size:17px}
  pre{overflow-x:visible;padding:12px 13px}
  pre code{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px;
    display:block;padding-left:1.4em;text-indent:-1.4em}
  .tbl{overflow-x:visible;border:0;border-radius:0}
  .tbl table{min-width:0;display:block}
  .tbl thead{display:none}
  .tbl tbody{display:block}
  .tbl tr{display:block;background:color-mix(in srgb,var(--ground) 55%,transparent);
    border:1px solid var(--line);border-radius:10px;padding:6px 12px;margin-bottom:9px}
  .tbl td{display:grid;grid-template-columns:minmax(5.5em,32%) 1fr;gap:10px;
    padding:5px 0;border-bottom:1px solid var(--line);font-size:16px}
  .tbl tr td:last-child{border-bottom:0}
  .tbl td:first-child{display:block;font-weight:700;font-size:17px;padding:2px 0 7px}
  .tbl td:first-child::before{display:none}
  .tbl td::before{content:attr(data-label);color:var(--muted);font-weight:700;
    font-size:13px;line-height:1.6;overflow-wrap:anywhere}
  .tbl td:empty{display:none}
  nav a{font-size:14px}
}
"""

JS = r"""
(function () {
  var KEY = 'unity-roadmap-done-v1';
  var store = {};
  try { store = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
  var boxes = Array.prototype.slice.call(document.querySelectorAll('label.done input'));

  function save() { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} }
  function paint() {
    var n = 0;
    boxes.forEach(function (b) {
      var on = !!store[b.dataset.id];
      b.checked = on;
      b.closest('h2').classList.toggle('is-done', on);
      if (on) n++;
    });
    var pct = boxes.length ? Math.round(n * 100 / boxes.length) : 0;
    document.querySelector('.bar i').style.width = pct + '%';
    document.getElementById('prog-text').textContent = n + ' / ' + boxes.length + ' 절 완료 (' + pct + '%)';
    document.getElementById('nav-prog').textContent = pct + '%';
  }
  boxes.forEach(function (b) {
    b.addEventListener('change', function () {
      if (b.checked) store[b.dataset.id] = 1; else delete store[b.dataset.id];
      save(); paint();
    });
  });
  document.getElementById('reset').addEventListener('click', function () {
    if (!confirm('진도 체크를 모두 지울까요?')) return;
    store = {}; save(); paint();
  });
  paint();

  /* PART 칩 ↔ 스크롤 연동 (hstom 학습 시리즈와 같은 방식: 네비 바로 아래를 지난 마지막 장) */
  var nav = document.querySelector('.nav-in');
  var chips = Array.prototype.slice.call(nav.querySelectorAll('a'));
  var secs = chips.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var cur = -1;
  function sync() {
    var line = nav.parentElement.offsetHeight + 12, idx = 0;
    for (var i = 0; i < secs.length; i++) if (secs[i] && secs[i].getBoundingClientRect().top <= line) idx = i;
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 2) idx = secs.length - 1;
    if (idx === cur) return;
    if (cur >= 0) chips[cur].classList.remove('active');
    cur = idx; chips[idx].classList.add('active');
    var c = chips[idx];
    nav.scrollLeft = Math.max(0, Math.min(c.offsetLeft - (nav.clientWidth - c.offsetWidth) / 2,
                                          nav.scrollWidth - nav.clientWidth));
  }
  addEventListener('scroll', sync, { passive: true });
  addEventListener('resize', sync, { passive: true });
  sync();
})();
"""


def split_h1(md: str) -> list[tuple[str, str]]:
    """코드펜스 밖의 `# ` 줄로 자른다. 코드블록 안의 주석 줄에 속지 않기 위해 펜스를 센다."""
    parts: list[tuple[str, list[str]]] = [("", [])]
    fence = False
    for line in md.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if not fence and re.match(r"^# ", line):
            parts.append((line[2:].strip(), []))
        else:
            parts[-1][1].append(line)
    return [(t, "\n".join(b)) for t, b in parts]


def label_cells(html: str) -> str:
    """좁은 화면에서 표를 카드로 쌓기 위해 셀마다 열 제목을 data-label 로 심는다."""
    def one(m):
        table = m.group(0)
        heads = [re.sub(r"<[^>]+>", "", h).strip()
                 for h in re.findall(r"<th[^>]*>(.*?)</th>", table, re.S)]

        def row(rm):
            i = [0]

            def cell(cm):
                lab = heads[i[0]] if i[0] < len(heads) else ""
                i[0] += 1
                return f'<td{cm.group(1)} data-label="{escape(lab)}">{cm.group(2)}</td>'
            return re.sub(r"<td([^>]*)>(.*?)</td>", cell, rm.group(0), flags=re.S)
        return re.sub(r"<tr>.*?</tr>", row, table, flags=re.S)
    html = re.sub(r"<table>.*?</table>", one, html, flags=re.S)
    return html.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")


def convert(md: str, sec_id: str) -> str:
    html = markdown.markdown(md, extensions=["tables", "fenced_code"])
    # 저장소 안의 다른 문서 링크는 허브에 없다 → GitHub 원문으로
    html = re.sub(r'href="\./([^"#]+\.md)(#[^"]*)?"',
                  lambda m: f'href="{GITHUB}{m.group(1)}{m.group(2) or ""}" target="_blank" rel="noopener"',
                  html)
    html = label_cells(html)

    # 절(h2)마다 완료 체크. id 는 제목 앞의 "A-1." 같은 번호가 있으면 그걸, 없으면 순번을 쓴다
    # — 문구를 다듬어도 진도가 날아가지 않게.
    n = [0]

    def h2(m):
        n[0] += 1
        text = m.group(1)
        plain = re.sub(r"<[^>]+>", "", text)
        num = re.match(r"^([A-Z]-\d+)\.", plain)
        did = num.group(1) if num else f"{sec_id}-{n[0]}"
        anchor = f"s-{did}"
        return (f'<h2 id="{anchor}"><span class="t">{text}</span>'
                f'<label class="done"><input type="checkbox" data-id="{did}">완료</label></h2>')
    return re.sub(r"<h2>(.*?)</h2>", h2, html, flags=re.S)


def build() -> str:
    md = SRC.read_text(encoding="utf-8")
    chunks = split_h1(md)
    title = chunks[1][0]
    intro_md = chunks[1][1]
    # 목차는 칩 네비가 대신한다 — 소개 인용문만 남긴다
    intro_md = intro_md.split("## 목차", 1)[0].replace("\n---", "")
    intro_html = markdown.markdown(intro_md)
    intro_html = re.sub(r'href="\./([^"#]+\.md)"',
                        lambda m: f'href="{GITHUB}{m.group(1)}" target="_blank" rel="noopener"', intro_html)

    nav, sections = [], []
    for i, (h1, body) in enumerate(chunks[2:]):
        body = re.sub(r"\n---\s*$", "", body.strip())
        if h1.startswith("PART"):
            code = h1.split(":")[0].strip()          # "PART A"
            label, chip = code, code.replace("PART ", "")
            sub = h1.split(":", 1)[1].strip()
            chip = f"{chip} {sub.split('—')[0].split('(')[0].strip()[:8].strip()}"
            heading = sub
        else:
            label = "부록" if h1.startswith("부록") else "Intro"
            chip = "부록" if label == "부록" else "시작 전에"
            heading = h1.split(":", 1)[1].strip() if ":" in h1 else h1
        sid = f"p{i}"
        nav.append(f'<a href="#{sid}">{escape(chip)}</a>')
        sections.append(f'<section class="ch" id="{sid}"><p class="ch-label">{escape(label)}</p>'
                        f'<h1>{escape(heading)}</h1>{convert(body, sid)}</section>')

    return f"""<!doctype html><html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unity 인디 로드맵</title>
<style>{CSS}</style></head><body>
<nav aria-label="parts"><div class="nav-in"><span class="prog" id="nav-prog">0%</span>{''.join(nav)}</div></nav>
<header class="hero">
  <p class="eyebrow">Unity · Indie Game Dev Roadmap</p>
  <h1>{escape(title)}</h1>
  <div class="intro">{intro_html}</div>
  <div class="bar"><i></i></div>
  <div class="bar-label"><span id="prog-text"></span><button id="reset" type="button">진도 초기화</button></div>
</header>
<main>{''.join(sections)}</main>
<footer>소스: mobile-dev-tutorial/unity-indie-roadmap.md · 진도는 이 브라우저에만 저장됩니다</footer>
<script>{JS}</script>
</body></html>
"""


def main() -> int:
    if not SRC.exists():
        print(f"소스 없음: {SRC}")
        return 1
    deps = [SRC, Path(__file__)]
    if OUT.exists() and "--force" not in sys.argv and \
            max(d.stat().st_mtime for d in deps) <= OUT.stat().st_mtime:
        print(f"변경 없음 → {OUT}")
        return 0
    OUT.write_text(build(), encoding="utf-8")
    print(f"→ {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
