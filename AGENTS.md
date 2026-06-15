# Codex Project Rules

- 처음부터 새로 만들지 않는다.
- 기존 pfc_in_drawing_request_tool에서 최소 변경으로 수정한다.
- 기존 PySide6, SQLite, Excel Import/Export 구조를 유지한다.
- 기존 DB 데이터를 삭제하지 않는다.
- Schema 변경 시 migration과 기존 파일 호환성을 고려한다.
- 수정 후 전체 pytest를 실행한다.
- 실제 회사 PDF, Excel, pfcproj 데이터는 Git에 올리지 않는다.
