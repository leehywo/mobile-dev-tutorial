"""unity-textbook/*.md → hmini 허브용 교과서 페이지(단일 HTML, 챕터 단위 화면 전환).

허브 slug `unity-textbook`. 원본은 `unity-textbook/NN_*.md` 40장(5부) + `00_README.md`(목차 표).
장을 고치면 다음에 열 때 다시 만들어진다.

화면:
  · 홈(#home) — 부별 챕터 카드. 카드 부제는 README 목차 표의 "코인 러시에 생기는 것" 열
  · 챕터(#chNN) — 한 번에 한 장만 보인다. 끝에 "이 장 완료" + 이전/다음
  · 완료 기록은 그 브라우저 localStorage(장 번호 기준)

실행: python3 tools/dash/render_textbook.py [--force]
"""
from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

import markdown

from render import CSS as BASE_CSS, GITHUB, label_cells

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "unity-textbook"
OUT = HERE / "unity_textbook.html"

EXTRA_CSS = r"""
.top{max-width:52rem;margin:0 auto;display:flex;align-items:center;gap:10px;padding:10px 16px}
.top a.home{flex:none;font-weight:700;font-size:14px;text-decoration:none;color:var(--accent);
  border:1px solid color-mix(in srgb,var(--accent) 35%,transparent);border-radius:8px;padding:4px 10px}
.top .cur{flex:1;min-width:0;font-size:14px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top .pct{flex:none;font-family:var(--mono);font-size:12.5px;font-weight:700;color:var(--done)}
.view[hidden]{display:none!important}
.part{margin-top:30px}
.part h2{font-size:15px;letter-spacing:.04em;color:var(--muted);margin:0 0 10px;font-weight:750}
.cards{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
a.card{display:block;text-decoration:none;color:inherit;background:var(--surface);border:1px solid var(--line);
  border-radius:12px;padding:12px 14px;box-shadow:var(--shadow);position:relative}
a.card:hover{border-color:var(--accent)}
a.card .n{font-family:var(--mono);font-size:12px;font-weight:700;color:var(--accent)}
a.card .t{display:block;font-weight:750;line-height:1.4;margin:2px 0 4px;padding-right:22px}
a.card .s{display:block;font-size:13.5px;color:var(--muted);line-height:1.5}
a.card.done{border-color:color-mix(in srgb,var(--done) 45%,transparent)}
a.card.done::after{content:"✓";position:absolute;top:10px;right:12px;color:var(--done);font-weight:800}
a.card.missing{opacity:.5;pointer-events:none}
.howto{margin-top:26px}
section.ch h2{display:block}
details{margin:.8em 0 1.2em;border:1px solid var(--line);border-radius:10px;padding:0 14px;
  background:color-mix(in srgb,var(--ground) 50%,transparent)}
details>summary{cursor:pointer;font-weight:700;font-size:14.5px;color:var(--accent-ink);padding:9px 0;list-style-position:inside}
details[open]{padding-bottom:6px}
details[open]>summary{border-bottom:1px solid var(--line);margin-bottom:6px}
.chfoot{margin-top:34px;padding-top:20px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:14px}
.chfoot .finish{align-self:flex-start;font:inherit;font-weight:750;font-size:15px;cursor:pointer;
  border-radius:10px;padding:9px 16px;border:1px solid var(--done);color:var(--done);background:transparent}
.chfoot .finish.on{background:var(--done);color:#fff}
.pager{display:flex;gap:10px;justify-content:space-between;flex-wrap:wrap}
.pager a{flex:1 1 200px;text-decoration:none;border:1px solid var(--line);border-radius:10px;padding:9px 13px;
  color:var(--ink);background:var(--surface)}
.pager a small{display:block;color:var(--muted);font-size:12px}
.pager a.next{text-align:right}
.pager a:hover{border-color:var(--accent)}
"""

JS = r"""
(function () {
  var KEY = 'unity-textbook-done-v1', store = {};
  try { store = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} }
  var views = Array.prototype.slice.call(document.querySelectorAll('.view'));
  var total = document.querySelectorAll('a.card:not(.missing)').length;

  function paint() {
    var n = 0;
    document.querySelectorAll('a.card').forEach(function (c) {
      var on = !!store[c.dataset.ch]; c.classList.toggle('done', on); if (on) n++;
    });
    document.querySelectorAll('.finish').forEach(function (b) {
      var on = !!store[b.dataset.ch];
      b.classList.toggle('on', on);
      b.textContent = on ? '✓ 이 장 완료함' : '이 장 완료로 표시';
    });
    var pct = total ? Math.round(n * 100 / total) : 0;
    document.querySelector('.top .pct').textContent = n + '/' + total + ' · ' + pct + '%';
    var bar = document.querySelector('.bar i'); if (bar) bar.style.width = pct + '%';
    var t = document.getElementById('prog-text'); if (t) t.textContent = n + ' / ' + total + ' 장 완료 (' + pct + '%)';
  }
  document.querySelectorAll('.finish').forEach(function (b) {
    b.addEventListener('click', function () {
      if (store[b.dataset.ch]) delete store[b.dataset.ch]; else store[b.dataset.ch] = 1;
      save(); paint();
    });
  });
  var reset = document.getElementById('reset');
  if (reset) reset.addEventListener('click', function () {
    if (!confirm('완료 기록을 모두 지울까요?')) return; store = {}; save(); paint();
  });

  function route() {
    var id = (location.hash || '#home').slice(1).split('/')[0];
    var target = document.getElementById(id);
    if (!target || !target.classList.contains('view')) { id = 'home'; target = document.getElementById('home'); }
    views.forEach(function (v) { v.hidden = v !== target; });
    document.querySelector('.top .cur').textContent = target.dataset.title || '';
    document.title = (id === 'home' ? '' : target.dataset.title + ' · ') + 'Unity 인디 교과서';
    try { localStorage.setItem(KEY + '-last', id); } catch (e) {}
    window.scrollTo(0, 0);
  }
  addEventListener('hashchange', route);
  if (!location.hash) {
    var last = null; try { last = localStorage.getItem(KEY + '-last'); } catch (e) {}
    var cont = document.getElementById('continue');
    if (last && last !== 'home' && document.getElementById(last) && cont) {
      cont.hidden = false; cont.href = '#' + last;
      cont.querySelector('b').textContent = document.getElementById(last).dataset.title;
    }
  }
  route(); paint();
})();
"""

PART_NAMES = {"1부": "1부 — 무너지지 않는 코드", "2부": "2부 — 보기 좋게, 빠르게",
              "3부": "3부 — 재미를 설계하기", "4부": "4부 — 팔고, 버티기",
              "5부": "5부 — 먹고살기 위한 보강"}


def readme_rows() -> list[tuple[str, str, str, str]]:
    """README 목차 표에서 (부, 장번호, 제목, 코인러시 산출물)."""
    rows, part = [], ""
    for line in (SRC / "00_README.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (\d부)", line)
        if m:
            part = m.group(1)
        m = re.match(r"^\|\s*(\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", line)
        if m and part:
            rows.append((part, m.group(1), m.group(2), m.group(3)))
    return rows


def convert(md: str) -> str:
    # details 안의 마크다운도 변환되게 md_in_html 을 켠다
    md = re.sub(r"<details>", '<details markdown="1">', md)
    html = markdown.markdown(md, extensions=["tables", "fenced_code", "md_in_html"])
    html = re.sub(r'href="\./(\d{2})_[^"]+\.md(#[^"]*)?"', r'href="#ch\1"', html)
    html = html.replace('href="./00_README.md"', 'href="#home"')
    html = re.sub(r'href="\.\./([^"#]+\.md)(#[^"]*)?"',
                  lambda m: f'href="{GITHUB}{m.group(1)}{m.group(2) or ""}" target="_blank" rel="noopener"',
                  html)
    return label_cells(html)


def build() -> str:
    rows = readme_rows()
    files = {p.name[:2]: p for p in SRC.glob("[0-9][0-9]_*.md") if p.name[:2] != "00"}
    order = [r[1] for r in rows]

    readme = (SRC / "00_README.md").read_text(encoding="utf-8")
    intro = readme.split("\n", 1)[1].split("## 목차", 1)[0]
    howto = readme.split("## 공부 방법", 1)[1] if "## 공부 방법" in readme else ""

    parts_html, cur_part, cards = [], None, []
    for part, num, title, gets in rows:
        if part != cur_part:
            if cards:
                parts_html.append(f'<div class="part"><h2>{escape(PART_NAMES.get(cur_part, cur_part))}</h2>'
                                  f'<div class="cards">{"".join(cards)}</div></div>')
            cur_part, cards = part, []
        miss = "" if num in files else " missing"
        sub = escape(gets) if num in files else "집필 중"
        cards.append(f'<a class="card{miss}" href="#ch{num}" data-ch="{num}"><span class="n">CHAPTER {num}</span>'
                     f'<span class="t">{escape(title)}</span><span class="s">{sub}</span></a>')
    if cards:
        parts_html.append(f'<div class="part"><h2>{escape(PART_NAMES.get(cur_part, cur_part))}</h2>'
                          f'<div class="cards">{"".join(cards)}</div></div>')

    home = f"""<div class="view" id="home" data-title="목차">
<header class="hero">
  <p class="eyebrow">Unity · Indie Game Dev Textbook</p>
  <h1>Unity 인디 게임 개발 교과서</h1>
  <div class="intro">{convert(intro)}</div>
  <div class="bar"><i></i></div>
  <div class="bar-label"><span id="prog-text"></span><button id="reset" type="button">완료 기록 초기화</button></div>
  <p><a id="continue" class="home" hidden href="#home">이어서 읽기 → <b></b></a></p>
</header>
<main>{''.join(parts_html)}
<section class="ch howto"><p class="ch-label">How to study</p><h1>공부 방법</h1>{convert(howto)}</section>
</main></div>"""

    chapters = []
    avail = [n for n in order if n in files]
    for i, num in enumerate(avail):
        text = files[num].read_text(encoding="utf-8")
        first, _, body = text.partition("\n")
        title = re.sub(r"^#\s*\d{2}\.\s*", "", first).strip()
        prev_n = avail[i - 1] if i > 0 else None
        next_n = avail[i + 1] if i + 1 < len(avail) else None

        def link(n, cls, label):
            if not n:
                return '<span></span>'
            t = re.sub(r"^#\s*\d{2}\.\s*", "", files[n].read_text(encoding="utf-8").partition("\n")[0])
            return f'<a class="{cls}" href="#ch{n}"><small>{label}</small>{n}. {escape(t.split("—")[0].strip())}</a>'
        chapters.append(f"""<div class="view" id="ch{num}" data-title="{num}. {escape(title)}" hidden>
<main><section class="ch"><p class="ch-label">Chapter {num}</p><h1>{escape(title)}</h1>{convert(body)}
<div class="chfoot"><button class="finish" type="button" data-ch="{num}">이 장 완료로 표시</button>
<div class="pager">{link(prev_n, 'prev', '← 이전 장')}{link(next_n, 'next', '다음 장 →')}</div></div>
</section></main></div>""")

    return f"""<!doctype html><html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unity 인디 교과서</title>
<style>{BASE_CSS.split('/* ── 폰:')[0]}{EXTRA_CSS}/* ── 폰:{BASE_CSS.split('/* ── 폰:')[1]}</style></head><body>
<nav><div class="top"><a class="home" href="#home">목차</a><span class="cur"></span><span class="pct"></span></div></nav>
{home}
{''.join(chapters)}
<footer>소스: mobile-dev-tutorial/unity-textbook/*.md · 완료 기록은 이 브라우저에만 저장됩니다</footer>
<script>{JS}</script>
</body></html>
"""


def main() -> int:
    deps = [*SRC.glob("*.md"), Path(__file__), HERE / "render.py"]
    if OUT.exists() and "--force" not in sys.argv and \
            max(d.stat().st_mtime for d in deps) <= OUT.stat().st_mtime:
        print(f"변경 없음 → {OUT}")
        return 0
    OUT.write_text(build(), encoding="utf-8")
    print(f"→ {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
