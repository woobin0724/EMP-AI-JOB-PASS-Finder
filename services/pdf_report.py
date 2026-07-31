# -*- coding: utf-8 -*-
"""
services/pdf_report.py
'나만의 취업 성공 리포트' PDF 생성 로직 (reportlab 기반)

Streamlit Cloud는 파일시스템이 재시작 시 초기화되므로, 디스크에 저장하지 않고
메모리(io.BytesIO) 위에서 바로 PDF를 만들어 다운로드 버튼으로 제공한다.

한글 폰트: fonts/NanumGothic.ttf 가 존재하면 사용하고, 없으면 기본 폰트로
대체한다(이 경우 한글이 깨질 수 있음 — 폰트 파일을 프로젝트에 직접 추가해야 함).
"""

import io
import os
import datetime


def _get_font_name(base_dir: str) -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_path = os.path.join(base_dir, "fonts", "NanumGothic.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
        return "NanumGothic"
    return "Helvetica"


def build_success_report_pdf(
    base_dir: str,
    student_name: str,
    company: dict,
    spec_result: dict,
    curriculum: list,
    cover_letter_excerpt: str,
    roadmap_stage_label: str,
) -> bytes:
    """매칭 결과 + 커리큘럼 + 자소서 요약 + 로드맵 진행 상태를 한 장의 PDF로 만든다."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    font_name = _get_font_name(base_dir)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 20 * mm

    def line(text, size=11, gap=7, bold=False):
        nonlocal y
        if y < 20 * mm:
            c.showPage()
            y = height - 20 * mm
        c.setFont(font_name, size)
        c.drawString(20 * mm, y, text)
        y -= gap * mm

    line("AI Job Pass Finder — 나만의 취업 성공 리포트", size=17, gap=12)
    line(f"생성일: {datetime.date.today().isoformat()}", size=9, gap=10)

    line(f"학생 이름: {student_name}", size=12, gap=8)
    line(f"지원 희망 기업: {company['name']} ({company['size_tag']} · {company['field_tag']})", size=12, gap=10)

    line("[취업 등용문 점수]", size=13, gap=8)
    line(f"내신 성취도: {spec_result['grade_score']}점 / 30점", gap=6)
    line(f"자격증 가산점: {spec_result['cert_score']}점 / 40점", gap=6)
    line(f"전공 적합성: {spec_result['fit_score']}점 / 20점", gap=6)
    line(f"인재상 일치도: {spec_result['talent_score']}점 / 10점", gap=6)
    line(f"최종 취업 등용문 점수: {spec_result['final_score']}점 / 100점", size=13, gap=10)

    line("[4주 맞춤 커리큘럼 요약]", size=13, gap=8)
    for wk in curriculum:
        line(f"{wk['week']}주차 - {wk['title']}: {wk['goal']}", size=10, gap=6)

    line("", gap=4)
    line(f"[로드맵 진행 상태] {roadmap_stage_label}", size=12, gap=10)

    line("[자기소개서 초안 요약]", size=13, gap=8)
    excerpt = (cover_letter_excerpt or "")[:300]
    for i in range(0, len(excerpt), 45):
        line(excerpt[i:i + 45], size=9, gap=5)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
