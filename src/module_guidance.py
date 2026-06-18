from __future__ import annotations


MODULE_GUIDANCE: dict[str, str] = {
    "drawing_request_summary": """[Summary 입력 예시]
- Project: HE ICCU OBC PFC IN
- Product: PFC Inductor Assembly
- Customer: 고객사명
- Request Rev: Rev.E
- Request Purpose: 신규 도면 작성 / Rev 변경 / 고객 요청 반영
- Mechanical Team Request: 도면 우측 상단 특성표, BOM, Note 반영 요청
- Key Risk: 하우징 간섭, PCB 체결성, Hi-Pot Risk

작성 포인트:
프로젝트 기본정보와 기구팀에 전달할 핵심 요청사항을 한 줄로 이해되게 정리합니다.""",
    "electrical_spec": """[Electrical Spec 입력 예시]
- Item: Inductance / DCR / Hi-Pot / IR
- Symbol: L / Rdc / ACW / IR
- Condition: 100kHz, 0.1V / 25C / AC 2.5kV 5sec
- Min, Typ, Max: 고객 Spec 기준 입력
- Drawing Text: 도면에 그대로 들어가야 하는 문구
- Critical: Y
- Change Risk: High

작성 포인트:
도면 우측 상단 특성표에 들어가야 하는 전기적 성능 기준을 관리합니다.""",
    "reliability": """[Reliability 입력 예시]
- Test Item: Thermal Shock / Vibration / Hi-Pot
- Standard: 고객 ES/MS 또는 사내 기준
- Condition: -40C~125C, 100 cycle
- Sample Qty: 3EA
- Judgment: 외관 이상 없음, 특성 만족
- Required: Y

작성 포인트:
도면, 승인자료, 신뢰성 시험계획에 반영되어야 하는 조건을 입력합니다.""",
    "esms": """[ESMS 입력 예시]
- Customer Spec: ES/MS
- Clause: Material / Insulation / Reliability
- Requirement: Flame retardant requirement
- Applied Part: Bobbin, Coil
- Drawing Text: PET-GF30 V0
- Evidence: Material Certificate
- Required: Y

작성 포인트:
고객 표준 요구사항과 도면/증빙자료 반영 여부를 관리합니다.""",
    "bom": """[BOM 입력 예시]
- Part Name: Core / Bobbin / Coil / Terminal / Resin
- Material: Sendust / PET-GF30 / Cu Wire
- Spec: V0, Wire diameter, Core grade 등
- Qty: 사용 수량
- Related Spec: DCR, Hi-Pot, Isat 등
- Change Risk: High / Medium / Low

작성 포인트:
재질이나 부품 변경 시 전기특성, 신뢰성, 승인자료 영향을 추적할 수 있게 입력합니다.""",
    "note": """[Note 입력 예시]
- Category: Insulation / Soldering / Measurement / Assembly
- Note Text: 도면 Note에 들어가야 할 문구
- Required: Y
- Drawing Area: Note 영역 / Spec Table / Section View
- Related Risk: Hi-Pot, 절연거리, 조립성

작성 포인트:
기구팀이 도면 Note에 누락 없이 반영해야 하는 필수 문구를 관리합니다.""",
    "drawing_review_checklist": """[Drawing Review Checklist 입력 예시]
- Check Item: DCR Max 값 확인
- Source Sheet: Electrical_Spec
- Expected: Rdc <= 18mOhm
- Drawing Actual: 도면에서 확인한 실제 문구
- Result: PASS / NG / CHECK / MISSING
- Owner: 개발팀 / 기구팀 / 품질팀

작성 포인트:
완성 도면 PDF를 검토하면서 누락, 오기입, Spec 불일치를 기록합니다.""",
    "inspection_standard_db": """[Inspection Standard DB 입력 예시]
- Drawing No.: 1-1
- Inspection Point: 제품 전체 길이
- Item: Dimension
- Symbol: L_Assy_Total
- View: Top View
- Nominal / Upper / Lower: 105.1 / 105.7 / 104.5
- Method / Tool: Distance / V/C
- Confirmed: Y

작성 포인트:
검사기준서 PDF에서 추출한 Draft는 Confirmed=N으로 두고, 사람이 확인한 항목만 Y로 바꿉니다.""",
    "measurement_result_db": """[Measurement Result DB 입력 예시]
- Lot: 양산/시작 Lot 번호
- Sample No.: 1~5
- Inspection No.: 검사기준서 번호
- Symbol: L_Assy_Total
- Measured Value: 실제 측정값
- Result: PASS / NG / CHECK / MISSING
- Inspector: 측정자

작성 포인트:
실제 측정 DATA를 누적해 Revision 변경 시 기존 DATA 재평가에 사용합니다.""",
    "revision_impact": """[Revision Impact 입력 예시]
- Rev: Rev.F
- Changed Item: Terminal Position 변경
- Changed Symbol: POS_Term_BDF
- Before / After: 변경 전후 값
- Impact Area: PCB Assembly, JIG, Customer Housing
- Required Check: PCB Hole, CMM Position, Customer Assembly
- Alarm Level: High
- Status: Open

작성 포인트:
치수, 전기특성, BOM, 재질, Note 변경이 어떤 문서와 부서에 영향을 주는지 정리합니다.""",
    "inspection_revision_impact": """[Inspection Revision Impact 입력 예시]
- Changed Symbol: L_Assy_Total
- Related Inspection No.: 1
- Related Measurement Data: 기존 Lot 측정 DATA 있음
- Old Spec / New Spec: 변경 전후 기준
- Required Action: 검사기준서 수정 및 기존 측정 DATA 재판정
- Alarm Level: High

작성 포인트:
도면 변경이 검사기준서와 기존 측정 DATA에 미치는 영향을 관리합니다.""",
    "change_history": """[Change History 입력 예시]
- Date: 변경일
- User: 변경자
- Rev: Rev.F
- Changed Sheet: Electrical_Spec
- Changed Item: DCR Max
- Before / After: 18mOhm / 20mOhm
- Reason: 고객 요청 또는 내부 개선
- Impact Summary: 온도상승, 효율 영향 검토 필요

작성 포인트:
Revision 변경 이력을 추적할 수 있도록 변경 사유와 영향 요약을 남깁니다.""",
    "raw_ocr_text": """[Raw OCR Text 입력 예시]
- Source File: 검사기준서 PDF 파일명
- Page: 2
- Extracted Text: PDF에서 추출된 원문
- OCR Used: Y / N
- Confidence: OCR 신뢰도
- Confirmed: Y / N

작성 포인트:
PDF/OCR 추출 결과는 Draft입니다. 사람이 확인한 뒤 공식 DB에 반영합니다.""",
}


def module_guidance(table_name: str) -> str:
    return MODULE_GUIDANCE.get(
        table_name,
        "선택한 Module에서 관리할 기준값, 도면 문구, 변경 영향 정보를 입력하세요.",
    )
