# Drawing Request & Revision Control Tool

## Quick Start for Windows Users

Double-click `launch_app.bat`.

On the first run, the launcher automatically creates `.venv`, installs packages from `requirements.txt`, performs the safe startup sync, and opens the desktop app. Users do not need to type the setup commands manually.

If Python 3 is not installed, the launcher shows a message with the Python download link. After installing Python 3, run `launch_app.bat` again.

## Team Sync Manager 사용법

Team Sync 기능은 성윤의 `sungyoon-codex` 브랜치와 학석의 `hakseok-claude` 브랜치를 안전하게 관리하고, 검증이 끝난 변경만 GitHub `main`에 통합합니다. 도면 PDF, Excel, CSV, `.pfcproj`, `.env`, 가상환경은 Commit 대상에서 차단됩니다.

### 최초 설정

1. `launch_and_sync.bat` 또는 `launch_app.bat`를 실행합니다.
2. 최초 실행 창에서 `성윤 / sungyoon-codex / Codex` 또는 `학석 / hakseok-claude / Claude Code`를 선택합니다.
3. 설정은 프로젝트 루트의 `.team_profile.local.json`에 저장됩니다. 이 파일은 PC별 설정이며 GitHub에는 올라가지 않습니다.
4. 설정을 바꾸려면 프로그램 메뉴의 `Team Sync > 개발자 프로필 / 자동 동기화 설정`을 사용합니다.

기본값은 `자동 확인 ON`, `자동 반영 OFF`입니다. 앱은 5분마다 `git fetch origin`으로 새 Main을 확인합니다. 자동 반영을 켜더라도 로컬 수정사항이 있으면 병합하지 않고 알림만 표시합니다.

### Team Sync 화면

프로그램 메뉴에서 `Team Sync > Team Sync Manager`를 선택합니다.

- `최신 Main 확인`: GitHub main의 최신 Commit과 업데이트 유무를 확인합니다.
- `Main 변경사항 반영`: 작업 폴더가 깨끗할 때만 `origin/main`을 개인 브랜치에 병합합니다.
- `내 작업 업로드`: 전체 pytest 실행 후 안전한 소스만 Commit하고 개인 브랜치에 Push합니다.
- `내 작업 Main 통합`: 로컬 수정사항이 있으면 별도 업로드 없이 민감자료 검사와 pytest 후 자동 Commit합니다. 이어서 최신 main 선행 병합, 재검사, Push, PR 생성, GitHub Actions 검사를 거쳐 merge commit 방식으로 통합합니다.
- `통합 상태 확인`: 최신 main과 현재 개인 브랜치 상태를 다시 확인합니다.
- `GitHub 저장소 열기`: 현재 origin 저장소를 브라우저로 엽니다.

### 팀원별 작업 순서

성윤:

1. 프로필에서 `성윤 / sungyoon-codex`를 선택합니다.
2. `launch_and_sync.bat`로 앱을 실행합니다.
3. Codex에서 수정하고 `launch_app.bat`로 확인합니다.
4. 준비되면 `integrate_my_work.bat` 또는 `내 작업 Main 통합`을 실행합니다.
5. 아직 Main에 합치지 않고 개인 브랜치에만 보관하려면 `publish_my_work.bat` 또는 `내 작업 업로드`를 사용합니다.

학석:

1. 프로필에서 `학석 / hakseok-claude`를 선택합니다.
2. `launch_and_sync.bat`로 앱을 실행합니다.
3. Claude Code에서 수정하고 `launch_app.bat`로 확인합니다.
4. 준비되면 `integrate_my_work.bat` 또는 `내 작업 Main 통합`을 실행합니다.
5. 아직 Main에 합치지 않고 개인 브랜치에만 보관하려면 `publish_my_work.bat` 또는 `내 작업 업로드`를 사용합니다.

### 보조 배치 파일

- `launch_and_sync.bat`: 프로필 브랜치를 준비하고 안전하게 Main을 반영한 뒤 앱을 실행합니다.
- `publish_my_work.bat`: pytest, 민감자료 검사, Commit, 개인 브랜치 Push를 수행합니다. main에는 직접 Push하지 않습니다.
- `integrate_my_work.bat`: GitHub PR과 Actions 검사를 이용해 개인 브랜치를 main에 통합합니다.
- `sync_from_main.bat`: 로컬 변경이 없을 때만 Main을 병합하고 requirements 설치 및 pytest를 수행합니다.
- `start_sungyoon_work.bat`, `start_hakseok_work.bat`: 해당 개발자의 프로필과 개인 브랜치로 전환한 뒤 앱을 실행합니다.

### GitHub CLI 최초 로그인

Main 통합 기능은 GitHub CLI가 필요합니다.

```powershell
winget install --id GitHub.cli
gh auth login
gh auth status
```

`gh auth login`에서 `GitHub.com`, `HTTPS`, `Login with a web browser`를 선택하고 브라우저 인증을 완료합니다.

### 충돌 또는 검사 실패 시

- 충돌 파일은 Team Sync 결과창과 CLI에 표시됩니다.
- 프로그램은 충돌을 자동 해결하거나 파일을 덮어쓰지 않습니다.
- 충돌을 직접 해결한 후 `git add <파일>`과 Commit을 수행하고 pytest를 다시 실행합니다.
- GitHub Actions 실패 또는 PR 충돌 시 main 병합은 중단되고 PR 페이지가 열립니다.
- `git reset --hard`, `git clean`, force push는 Team Sync에서 사용하지 않습니다.


개발팀이 기구팀에 전달할 PFC IN 도면 기입 정보를 정리하고, 완성 도면 검토, 검사 기준서 DATA화, 실제 측정 DATA 판정, Revision 영향도 알람을 관리하는 로컬 Desktop Tool입니다.

## 1. Tool 목적

이 Tool은 CAD 자동화 Tool이나 기구팀 모델링 자동화 Tool이 아닙니다.

목적은 다음 업무를 사내 표준 DATA로 관리하는 것입니다.

- 개발 담당자의 도면 작성 요청 정보 정리
- 전기적 특성, 신뢰성, ES/MS, BOM, Note 기입 정보 관리
- 완성 도면 검토 Checklist 생성
- 검사 기준서 PDF의 측정 포인트 후보 DATA화
- 실제 측정 DATA 누적 및 PASS/NG 판정
- Revision 발생 시 전기/치수/BOM/Note/검사 기준/측정 DATA 영향 알람 생성
- 기구팀 전달용 또는 검토/보고용 Excel Package Export

## 2. 회사 도면 제작 Process 반영

1. 개발 담당자가 전기적 특성, 신뢰성, ES/MS, BOM, Note를 작성합니다.
2. 해당 내용을 기구팀에 전달합니다.
3. 기구팀은 CAD로 모델링하고 도면에 치수와 개발팀 전달 내용을 기입합니다.
4. 개발/기구/품질/생산 관련자가 완성 도면을 검토합니다.
5. 누락, 오기입, Spec 불일치, BOM 불일치, Note 누락, 검사 기준 누락을 확인합니다.
6. 검사 기준서가 작성되면 측정 포인트, 기준 치수, Datum, 측정 Tool을 DATA화합니다.
7. 실제 측정 DATA를 누적해 PASS/NG를 판정합니다.
8. Revision 발생 시 관련 항목 영향도를 자동 알람으로 확인합니다.

## 3. Streamlit을 사용하지 않는 이유

이번 버전은 사내 Desktop 업무 Tool 방향입니다.

- 로컬 PC에서 프로젝트 파일을 열고 저장하는 구조가 필요합니다.
- 엑셀처럼 셀을 직접 편집하고 복사/붙여넣기하는 사용성이 중요합니다.
- 프로젝트 내부 상태를 SQLite로 안정적으로 저장해야 합니다.
- 웹 서버를 띄우는 Streamlit 구조보다 PySide6 Desktop App이 업무 흐름에 더 맞습니다.

## 4. Excel을 먼저 열지 않는 이유

Excel은 최종 산출물입니다. 기준 DATA의 원본은 SQLite 프로젝트 파일입니다.

- 사용자는 PySide6 App 안에서 먼저 입력/수정/검토합니다.
- `Save Project`는 `.pfcproj` 또는 `.db` SQLite 파일로 저장합니다.
- `Export Excel`을 누를 때만 기구팀 전달용/검토 보고용 Excel Package를 생성합니다.
- 기존 Excel은 `Import Excel` 기능으로 불러와 내부 Table로 변환합니다.

## 5. SQLite 내부 저장 구조

프로젝트 파일 확장자는 `.pfcproj` 또는 `.db`입니다.

SQLite Table:

1. `drawing_request_summary`
2. `electrical_spec`
3. `reliability`
4. `esms`
5. `bom`
6. `note`
7. `drawing_review_checklist`
8. `inspection_standard_db`
9. `measurement_result_db`
10. `revision_impact`
11. `inspection_revision_impact`
12. `change_history`
13. `raw_ocr_text`

## 6. Excel Export 구조

Export Excel은 아래 Sheet를 생성합니다.

1. `Drawing_Request_Summary`
2. `Electrical_Spec`
3. `Reliability`
4. `ESMS`
5. `BOM`
6. `Note`
7. `Drawing_Review_Checklist`
8. `Inspection_Standard_DB`
9. `Measurement_Result_DB`
10. `Revision_Impact`
11. `Inspection_Revision_Impact`
12. `Change_History`
13. `Raw_OCR_Text`

Excel에는 필터, Freeze Pane, 열 너비 자동 조정, Header 색상, 드롭다운, 조건부 서식을 적용합니다.

색상 기준:

- PASS: 초록색
- NG: 빨간색
- CHECK: 노란색
- MISSING: 주황색
- High: 빨간색
- Medium: 노란색
- Low: 초록색

## 7. Module 설명

- Summary: 도면 작성 요청 기본 정보
- Electrical Spec: 도면 전기적 특성표
- Reliability: 신뢰성 조건
- ESMS: 고객 ES/MS 요구사항
- BOM: BOM 및 재질/사양
- Note: 도면 Note 문구
- Drawing Review Checklist: 완성 도면 검토 항목
- Inspection Standard DB: 검사 기준서 측정 포인트 DATA
- Measurement Result DB: 실제 측정 DATA 및 PASS/NG 판정
- Revision Impact: Revision 변경 영향도
- Inspection Revision Impact: 검사 기준/측정 DATA 영향도
- Change History: 변경 이력
- Raw OCR Text: PDF 추출 원문

## 8. 설치 방법

```powershell
cd pfc_in_drawing_request_tool
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

참고: Windows의 긴 경로 제한 때문에 전체 `PySide6` 메타 패키지 설치가 실패할 수 있어, 이 프로젝트는 Desktop 실행에 필요한 `PySide6-Essentials`를 사용합니다. 코드에서는 그대로 `PySide6.QtWidgets`, `PySide6.QtCore`, `PySide6.QtGui`를 import합니다.

## 9. PySide6 Desktop 실행 방법

```powershell
python desktop/app.py
```

Toolbar 기능:

- New Project
- Open Project
- Save Project
- Add Project는 왼쪽 Project Modules 패널에서 사용
- Import Excel
- Export Excel
- Parse Inspection PDF
- Validate
- Compare Revision
- Check Measurement Data
- Generate Impact Alarm
- Export Report

왼쪽 Project Modules 패널:

- 왼쪽 패널 제목은 `Project Modules`입니다.
- 그 아래에 `PFC IN Project` 같은 Project가 바로 표시됩니다.
- 여러 Project를 추가할 수 있습니다.
- `Add Project` 버튼으로 새 Project를 추가합니다.
- Project 또는 Module을 더블클릭하거나 우클릭 후 Rename으로 표시 이름을 변경합니다.
- 내부 DB 테이블명은 바뀌지 않고, 화면 표시용 이름만 `module_display_names`에 저장됩니다.

## 10. CLI 실행 방법

```powershell
python main.py create-project --output sample.pfcproj
python main.py create-sample --output sample.pfcproj
python main.py export-excel --project sample.pfcproj --output PFC_IN_Request_Package.xlsx
python main.py import-excel --input PFC_IN_Request_Package.xlsx --output imported_project.pfcproj
python main.py validate --project sample.pfcproj
python main.py compare --old RevA.pfcproj --new RevB.pfcproj --output Rev_Compare_Result.xlsx
python main.py parse-inspection --project sample.pfcproj --pdf Inspection_Standard.pdf
python main.py check-measurement --project sample.pfcproj
```

## 11. 검사 기준서 PDF DATA화 방식

`Parse Inspection PDF`는 PyMuPDF로 PDF 텍스트를 추출합니다.

추출 대상 예:

- `105.1±0.6`
- `3-Ø3.5±0.1`
- `MAX 32.0`
- `MIN 100.5`
- `Ø0.2 | A | B | D`

추출 결과는 Draft입니다. 모든 후보는 `Confirmed=N`으로 저장되며, 사람이 검토한 뒤 `Confirmed=Y`로 승인해야 공식 검사 기준으로 사용합니다.

## 12. Revision 영향도 Rule

대표 Rule:

- Core Size 변경: Inductance, Isat, Core Loss, Temperature 영향
- Gap 변경: Inductance, DC Bias, Isat 영향
- Turn 변경: Inductance, DCR, Copper Loss, Temperature 영향
- Wire 변경: DCR, Current Density, Temperature, Winding Space 영향
- Bobbin Material 변경: Hi-Pot, Insulation, ES/MS, Reliability 영향
- Terminal Position 변경: PCB Assembly, Customer Housing, Fastening 영향
- Assy Size 변경: Customer Housing, Assembly Interference 영향

## 13. OCR 제한사항

OCR 또는 PDF 텍스트 추출은 보조 기능입니다.

- 회사 도면/검사 기준서는 외부 서버/API로 전송하지 않습니다.
- 모든 처리는 로컬 PC에서 수행합니다.
- OCR 결과는 반드시 사람이 확인해야 합니다.
- `Confirmed=Y`가 아닌 검사 기준 후보는 공식 DATA로 사용하지 않습니다.

## 14. 테스트

```powershell
pytest
```

테스트 범위:

- SQLite 프로젝트 생성
- 필수값 누락 검증
- BOM TBD CHECK 검증
- Measurement PASS/NG/MISSING/CHECK 판정
- Impact Rule 매칭
- Revision 비교 결과 생성
- Inspection Confirmed Rule
- Excel Export Sheet/Style 생성
- Import Excel 후 데이터 유지
- Raw OCR Text 저장

## 15. 향후 개발 계획

1. CAD/SolidWorks 연동
2. CMM 측정 DATA 자동 Import
3. 검사 기준서 양식별 Parser 개선
4. 고객사별 ES/MS Rule Template 추가
5. APQP/PPAP 문서 영향도 연결
6. 도면 PDF와 검사 기준서 PDF 자동 비교 기능
7. 완성도면 PDF의 특성표/Note/OCR 영역별 추출 개선
