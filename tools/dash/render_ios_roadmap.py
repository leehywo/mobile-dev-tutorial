"""ios-indie-roadmap.md → hmini 허브용 학습 페이지(단일 HTML).

render.py(Unity 로드맵)와 같은 화면·같은 규칙을 그대로 쓴다 — 소스 md 와 출력 경로, 제목·진도 저장 키만 다르다.
원본은 md 하나뿐이다(GitHub 에서 보는 md 와 내용이 같다). md 가 안 바뀌었으면 다시 만들지 않는다.

허브 slug `ios-indie-roadmap`. 실행: python3 tools/dash/render_ios_roadmap.py [--force]
"""
from __future__ import annotations

import sys
from pathlib import Path

import render

HERE = Path(__file__).resolve().parent
SRC = render.ROOT / "ios-indie-roadmap.md"
OUT = HERE / "ios_indie_roadmap.html"

# render.build() 가 모듈 전역 SRC 를 읽는다
render.SRC = SRC

PATCH = {
    "<title>Unity 인디 로드맵</title>": "<title>iOS 인디 로드맵</title>",
    "Unity · Indie Game Dev Roadmap": "iOS · Indie App &amp; Game Dev Roadmap",
    "var KEY = 'unity-roadmap-done-v1';": "var KEY = 'ios-indie-roadmap-done-v1';",
    "소스: mobile-dev-tutorial/unity-indie-roadmap.md": "소스: mobile-dev-tutorial/ios-indie-roadmap.md",
}


def build() -> str:
    html = render.build()
    for a, b in PATCH.items():
        assert html.count(a) == 1, f"패치 대상이 정확히 한 번 있어야 함: {a}"
        html = html.replace(a, b)
    return html


def main() -> int:
    if not SRC.exists():
        print(f"소스 없음: {SRC}")
        return 1
    deps = [SRC, Path(__file__), Path(render.__file__)]
    if OUT.exists() and "--force" not in sys.argv and \
            max(d.stat().st_mtime for d in deps) <= OUT.stat().st_mtime:
        print(f"변경 없음 → {OUT}")
        return 0
    OUT.write_text(build(), encoding="utf-8")
    print(f"→ {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
