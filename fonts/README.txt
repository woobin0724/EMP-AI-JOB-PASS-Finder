fonts/
======

NanumGothic.ttf  — PDF 리포트(가이드 > PDF 다운로드)의 한글 출력용 폰트
OFL.txt          — 위 폰트의 라이선스 원문(SIL Open Font License 1.1).
                   Google Fonts 저장소의 공식 파일 그대로
                   (https://github.com/google/fonts/blob/main/ofl/nanumgothic/OFL.txt, 2026-10-20 받음)
                   — 저작권자 NHN Corporation · Reserved Font Name(Nanum, NanumGothic 등) 문구 포함

NanumGothic.ttf 출처: Google Fonts 공식 배포 서버(fonts.gstatic.com, 2026-10-07 받음),
Version 3.020, 폰트 내부 저작권 문구 "Copyright © 2011 NHN Corporation. All rights reserved.
Font designed by Sandoll Communications Inc."

services/pdf_report.py 가 fonts/NanumGothic.ttf 를 찾아 등록한다.
파일이 없어도 앱은 동작하지만 PDF 의 한글이 네모(□)로 깨진다.

폰트를 다시 받아야 할 때
-------------------------
1) Google Fonts : https://fonts.google.com/specimen/Nanum+Gothic → Get font → Download
   압축을 풀어 NanumGothic-Regular.ttf 를 이 폴더에 NanumGothic.ttf 로 저장
2) 또는 네이버 나눔글꼴 공식 페이지(https://hangeul.naver.com/font)에서 받는다.
라이선스 파일(OFL.txt)도 함께 둔다 — OFL 은 폰트를 다시 배포할 때 라이선스 전문을
같이 두도록 요구한다.
