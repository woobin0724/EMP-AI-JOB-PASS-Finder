# -*- coding: utf-8 -*-
"""
views/admin_data.py
[Phase A-2] 기업 마스터 데이터 수동 입력 화면

▣ 왜 관리자 화면인가
   데이터는 스크래핑하지 않고 팀이 직접 조사해 넣는다. 그런데 사람이
   company_showcase.py 를 직접 고치면 (1) 파이썬 문법 사고가 나고
   (2) 출처가 기록되지 않는다. 그래서 필드가 정해진 폼으로 받고,
   출처 URL·조사자·조사일을 필수로 요구한다.

▣ Streamlit Cloud 주의
   여기서 저장하면 data/curated_companies.json 에 쓰이지만, Community Cloud 는
   재배포 시 파일시스템이 초기화된다. 그래서 'JSON 내려받기'로 파일을 받아
   저장소에 커밋하는 것까지가 한 사이클이다. 화면 상단에 그 안내를 띄운다.
"""

import csv
import io
import json

import streamlit as st

from core import session as ss
from data.company_showcase import COMPANY_CATEGORIES
from services import api_registry as reg
from services import curated
from ui.components import back_to_hub, render_html, section_title, topbar
from ui.theme import BRAND, CARD_BORDER, GREEN, MUTED, TEXT


def _widget(key: str, label: str, kind: str, required: bool, value):
    """필드 종류에 맞는 입력 위젯 하나를 그린다."""
    tag = f"{label} *" if required else label
    wkey = f"cur_{key}"

    if kind == "choice":
        options = {"size_tag": curated.SIZE_TAGS,
                   "category": [c for c in COMPANY_CATEGORIES if c != "전체"],
                   "source_type": curated.SOURCE_TYPES}[key]
        idx = options.index(value) if value in options else 0
        return st.selectbox(tag, options, index=idx, key=wkey)
    if kind == "area":
        return st.text_area(tag, value=value or "", height=80, key=wkey)
    if kind == "list":
        raw = st.text_input(tag, value=", ".join(value or []), key=wkey,
                            placeholder="쉼표로 구분해 입력")
        return [s.strip() for s in raw.split(",") if s.strip()]
    if kind == "lines":
        raw = st.text_area(tag, value="\n".join(value or []), height=90, key=wkey,
                           placeholder="한 줄에 하나씩")
        return [s.strip() for s in raw.splitlines() if s.strip()]
    if kind in ("number", "int"):
        lo, hi, default = curated.BOUNDS[key]
        cast = int if kind == "int" else float
        current = cast(value) if value not in (None, "") else cast(default)
        current = min(max(current, cast(lo)), cast(hi))   # 범위 밖 값이 들어와도 안전
        return st.number_input(
            tag, min_value=cast(lo), max_value=cast(hi), value=current,
            step=cast(1) if kind == "int" else 0.1,
            format=None if kind == "int" else "%.1f", key=wkey,
        )
    if kind == "date":
        return st.text_input(tag, value=value or "", key=wkey, placeholder="YYYY-MM-DD")
    return st.text_input(tag, value=value or "", key=wkey)


def _form(rows: list[dict]) -> None:
    editing_id = st.session_state.get("curated_editing", "")
    base = next((r for r in rows if r.get("id") == editing_id), None) if editing_id else None
    base = dict(base) if base else curated.blank_row()

    if editing_id:
        st.info(f"'{base.get('name', editing_id)}' 를 수정하고 있습니다.")

    groups = [
        ("기본 정보", ["id", "name", "size_tag", "field_tag", "category", "description", "hire_dept"]),
        ("채용 요건", ["required_certs", "required_skills", "ideal_talent",
                       "exam_keywords", "interview_questions"]),
        ("참고 정보", ["overall_rating", "benefit_short", "pros", "cons",
                       "avg_applicant_grade", "avg_applicant_certs"]),
        ("출처 (검증용)", ["source_url", "source_type", "checked_by", "checked_at"]),
    ]
    spec = {k: (lbl, kind, req) for k, lbl, kind, req in curated.FIELDS}
    row = {}

    for title, keys in groups:
        st.markdown(f"#### {title}")
        cols = st.columns(2)
        for i, key in enumerate(keys):
            label, kind, required = spec[key]
            with cols[i % 2]:
                row[key] = _widget(key, label, kind, required, base.get(key))

    save_col, cancel_col = st.columns([1, 1])
    with save_col:
        if st.button("저장", type="primary", use_container_width=True, key="cur_save"):
            errors = curated.validate(row, rows, editing_id)
            if errors:
                for e in errors:
                    st.error(e)
            else:
                curated.upsert(row, editing_id)
                st.session_state.pop("curated_editing", None)
                # 폼 위젯 값을 비워 다음 입력이 이전 값을 물고 오지 않게 한다
                for k in list(st.session_state):
                    if k.startswith("cur_"):
                        del st.session_state[k]
                st.success(f"'{row['name']}' 을(를) 저장했습니다.")
                st.rerun()
    with cancel_col:
        if editing_id and st.button("수정 취소", use_container_width=True, key="cur_cancel"):
            st.session_state.pop("curated_editing", None)
            for k in list(st.session_state):
                if k.startswith("cur_"):
                    del st.session_state[k]
            st.rerun()


def _list(rows: list[dict]) -> None:
    if not rows:
        st.caption("아직 입력한 기업이 없습니다. 위 폼에서 첫 기업을 추가해보세요.")
        return

    for r in rows:
        render_html(f"""
        <div class="mjp-card">
            <span class="mjp-tag">{r.get('size_tag','')} · {r.get('category','')}</span>
            <div style="font-size:var(--mjp-h2); font-weight:800; margin-top:8px;">{r.get('name','')}</div>
            <div class="mjp-muted">{r.get('description','')}</div>
            <div class="mjp-muted" style="margin-top:8px;">
                자격증: {', '.join(r.get('required_certs') or []) or '-'} ·
                인재상: {', '.join(r.get('ideal_talent') or []) or '-'}
            </div>
            <div style="margin-top:10px; font-size:var(--mjp-caption); color:{MUTED};">
                출처 {r.get('source_type','')} ·
                <a href="{r.get('source_url','')}" target="_blank"
                   style="color:{BRAND};">{r.get('source_url','')}</a><br>
                {r.get('checked_by','')} · {r.get('checked_at','')}
            </div>
        </div>
        """)
        ecol, dcol, _ = st.columns([1, 1, 3])
        with ecol:
            if st.button("수정", key=f"cur_edit_{r['id']}", use_container_width=True):
                st.session_state["curated_editing"] = r["id"]
                for k in list(st.session_state):
                    if k.startswith("cur_") and not k.startswith("cur_edit_"):
                        del st.session_state[k]
                st.rerun()
        with dcol:
            if st.button("삭제", key=f"cur_del_{r['id']}", use_container_width=True):
                curated.delete(r["id"])
                st.rerun()


def _transfer(rows: list[dict]) -> None:
    st.markdown("#### 파일로 주고받기")
    st.caption("Streamlit Cloud 는 재배포 시 파일이 초기화됩니다. 입력한 데이터는 "
               "JSON 으로 내려받아 저장소의 data/curated_companies.json 에 "
               "커밋해야 영구 보관됩니다.")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "JSON 내려받기 (저장소 커밋용)",
            data=json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="curated_companies.json", mime="application/json",
            use_container_width=True, key="cur_dl_json",
        )
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=[k for k, _, _, _ in curated.FIELDS])
        writer.writeheader()
        writer.writerows(curated.to_csv_rows(rows))
        st.download_button(
            "CSV 내려받기 (스프레드시트 작업용)",
            data=buf.getvalue().encode("utf-8-sig"),
            file_name="curated_companies.csv", mime="text/csv",
            use_container_width=True, key="cur_dl_csv",
        )
    with c2:
        up = st.file_uploader("CSV 올리기 (스프레드시트에서 작업한 결과)",
                              type=["csv"], key="cur_up_csv")
        if up is not None and st.button("올린 CSV 로 덮어쓰기", use_container_width=True,
                                        key="cur_import"):
            text = up.getvalue().decode("utf-8-sig")
            parsed = curated.from_csv_rows(list(csv.DictReader(io.StringIO(text))))
            bad = [(r.get("id") or "(식별자 없음)", curated.validate(r, [], r.get("id", "")))
                   for r in parsed]
            bad = [(i, e) for i, e in bad if e]
            if bad:
                st.error(f"{len(bad)}건에 문제가 있어 저장하지 않았습니다.")
                for ident, errs in bad[:5]:
                    st.caption(f"· {ident}: {'; '.join(errs)}")
            else:
                curated.save(parsed)
                st.success(f"{len(parsed)}건을 불러왔습니다.")
                st.rerun()


def render() -> None:
    topbar()
    back_to_hub()
    section_title("기업 데이터 입력", icon_name="clipboard", sub=
                  "팀이 직접 조사한 기업 정보를 넣는 화면입니다. 스크래핑하지 않고 "
                  "사람이 확인한 값만 들어갑니다 — 그래서 <b>출처 기록이 필수</b>입니다.")

    rows = curated.load()
    st.caption(f"현재 큐레이션 {len(rows)}건 · 코드 마스터 20건과 합쳐 화면에 쓰입니다.")

    tabs = st.tabs(["입력·수정", f"목록 ({len(rows)})", "파일 주고받기", "API 연동 현황"])
    with tabs[0]:
        _form(rows)
    with tabs[1]:
        _list(rows)
    with tabs[2]:
        _transfer(rows)
    with tabs[3]:
        st.markdown("#### 공식 오픈API 연동 준비 현황")
        st.caption("규격(엔드포인트·파라미터)을 확인하고 키를 등록하면 해당 소스가 "
                   "LIVE 로 전환됩니다. 확인 전에는 큐레이션 데이터가 쓰입니다.")
        st.dataframe(reg.summary_rows(), use_container_width=True, hide_index=True)
        for spec in reg.REGISTRY:
            st.caption(f"· {spec.label} — 신청: {spec.portal_url}")
