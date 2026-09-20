#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_static.py
회귀 절차 0단계 — 화면을 띄우기 전에 잡을 수 있는 것들

▣ 왜 필요한가
   Streamlit 화면 코드는 import 가 하나만 빠져도 그 화면이 통째로
   트레이스백이 된다. 그런데 이건 그 화면을 실제로 렌더링해봐야 드러난다.
   py_compile 은 문법만 보므로 잡지 못한다 — 실제로 GOLD·BRAND 와
   render_html 두 번을 이렇게 놓쳤다.

   pyflakes 는 '정의되지 않은 이름'을 소스만 읽고 찾아준다. 브라우저를 띄우는
   모바일 QA(docs/qa_mobile.py)보다 훨씬 빠르므로 맨 앞에 둔다.

▣ 무엇을 오류로 볼 것인가
   미사용 import 까지 오류로 잡으면 경고가 쌓여 아무도 안 보게 된다.
   런타임에 앱을 깨뜨리는 것만 FAIL 로 두고, 나머지는 WARN 으로 센다.
     FAIL : 문법 오류 · 정의되지 않은 이름 · import 실패
     WARN : 미사용 import · 빈 f-string 등

사용법:  python3 scripts/check_static.py
종료 코드: 0 = 통과, 1 = FAIL 있음
"""

import importlib
import io
import os
import pathlib
import py_compile
import subprocess
import sys
import warnings

BASE = pathlib.Path(__file__).resolve().parent.parent

# scripts/ 에서 실행되므로 저장소 루트를 경로에 넣어야 views·services 가 보인다
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

# pyflakes 메시지 중 앱을 실제로 깨뜨리는 것들
FATAL_PATTERNS = (
    "undefined name",
    "undefined local",
    "syntax error",
    "invalid syntax",
)

# 검사에서 제외 — 실행 스크립트라 import 시 부수효과가 있다
SKIP_IMPORT = {"app", "scripts.check_static", "docs.qa_mobile", "scripts.fetch_mascot"}


def tracked_py_files() -> list:
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=BASE,
                         capture_output=True, text=True, check=True)
    return [BASE / f for f in out.stdout.split() if f]


def check_compile(files) -> list:
    fails = []
    for f in files:
        try:
            py_compile.compile(str(f), doraise=True, quiet=1)
        except py_compile.PyCompileError as exc:
            fails.append(f"{f.relative_to(BASE)}: {exc.msg.strip()}")
    return fails


def check_pyflakes(files) -> tuple[list, list]:
    """
    (치명, 경고) 로 갈라서 돌려준다.

    pyflakes 가 없으면 stdout 이 비고 returncode 만 1 이라, 그냥 두면
    '경고 0건 통과'처럼 보인다. 검사를 안 돌린 것과 통과한 것은 다르므로
    설치 여부를 먼저 확인하고 없으면 치명으로 올린다.
    """
    probe = subprocess.run([sys.executable, "-c", "import pyflakes"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        return (["pyflakes 가 설치돼 있지 않아 정적 검사를 돌리지 못했습니다 — "
                 "pip install -r requirements-dev.txt"], [])

    proc = subprocess.run([sys.executable, "-m", "pyflakes", *map(str, files)],
                          cwd=BASE, capture_output=True, text=True)

    fatal, warn = [], []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        rel = line.replace(str(BASE) + os.sep, "")
        (fatal if any(p in line.lower() for p in FATAL_PATTERNS) else warn).append(rel)
    return fatal, warn


def check_imports(files) -> list:
    """모듈을 실제로 import 해 import 시점 오류를 잡는다."""
    fails = []
    for f in files:
        rel = f.relative_to(BASE)
        mod = str(rel)[:-3].replace(os.sep, ".")
        if mod.endswith(".__init__"):
            mod = mod[:-9]
        if mod in SKIP_IMPORT or not mod:
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Streamlit 의 bare-mode 경고가 출력을 덮지 않도록 잠시 묶어둔다
                err = sys.stderr
                sys.stderr = io.StringIO()
                try:
                    importlib.import_module(mod)
                finally:
                    sys.stderr = err
        except Exception as exc:
            fails.append(f"{rel}: {type(exc).__name__}: {exc}")
    return fails


def main() -> int:
    files = tracked_py_files()
    print(f"검사 대상 {len(files)}개 파일\n")

    compile_fails = check_compile(files)
    fatal, warn = check_pyflakes(files)
    import_fails = check_imports(files)

    print(f"{'문법(py_compile)':<22} {'FAIL ' + str(len(compile_fails)) if compile_fails else 'OK'}")
    print(f"{'정의되지 않은 이름':<22} {'FAIL ' + str(len(fatal)) if fatal else 'OK'}")
    print(f"{'모듈 import':<22} {'FAIL ' + str(len(import_fails)) if import_fails else 'OK'}")
    print(f"{'경고(미사용 import 등)':<22} {len(warn)}건")

    for title, rows in (("문법 오류", compile_fails),
                        ("정의되지 않은 이름", fatal),
                        ("import 실패", import_fails)):
        if rows:
            print(f"\n[{title}]")
            for r in rows:
                print("  ", r)

    if warn:
        print("\n[경고]")
        for w in warn:
            print("  ", w)

    failed = len(compile_fails) + len(fatal) + len(import_fails)
    print("\n" + ("통과" if not failed else f"실패 {failed}건 — 고치고 다시 돌려주세요"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
