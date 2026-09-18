#!/usr/bin/env python3
"""코인 러시 재무 사례 계산 원본 (29·34·39·40장)

목적
  교과서 29·34·39·40장에 나오는 코인 러시(가상 사례)의 재무 수치를 한 파일에서 계산한다.
  장별 Markdown 에 숫자를 손으로 복사하면 장 사이에서 기간·비용 정의·입금 조건이 어긋나므로,
  모든 가정은 아래 "가정" 블록 한 곳에만 두고 표·본문 수치는 이 계산 결과를 옮겨 적는다.
  모든 수치는 교재용 가상값이며 세무·재무 자문이 아니다.

실행
  python3 unity-textbook/data/coin_rush_model.py            # 장별 수치·표 출력
  python3 unity-textbook/data/coin_rush_model.py --rows     # 40장 스트레스 시나리오 월별 표까지 전부 출력
  python3 unity-textbook/data/coin_rush_model.py --check    # 불변조건 + 본문 대조 검사 (실패 시 exit 1)

--check 의 검사 범위
  대상 장 : **29·34·39·40장 뿐이다.** 35장·README·그 밖의 장은 검사하지 않는다
            (35장의 보간·게이트 수치와 README 의 경로 안내는 이 스크립트가 보증하지 않는다).
  검사 1 — 불변조건(본문과 무관하게 모델 자체를 검사):
            ① 기간 정의: 40장 현금흐름은 M~M+23 정확히 24행, 34장 표는 M-2~M+9 정확히 12행
            ② 합계 = 부분합: 시나리오 합계 행, 게임 사업 현금 손익 항등식, 시간표 월 합계
            ③ 생활비 배분: 게임 부담 + 계약 부담 + 저축 인출 = 생활비 합계, 각 항 ≥ 0,
               게임 부담 ≤ 생활비 합계 (게임 사업 적자는 배분에서 분리)
            ④ 잔액 규칙과 판정: 시나리오별 최저 잔액·최저 시점을 독립 재계산하고,
               A1/A2/B/C1/C2 판정을 잔액·손익 규칙으로 다시 매겨 SCENARIO_VERDICT 와 대조
            ⑤ 입금 규칙: 지급 보류가 걸린 달은 입금 0, Direct 환급은 도달 달의 다음 달
            ⑥ 시간표: 월별 게임 시간 합계 = 가용 시간, H2 출시 전 시간·달력 상한 판정
  검사 2 — 본문 대조(값마다 **기대 위치**를 지정):
            (장 파일, 절 제목, 행 정규식) 으로 좁힌 문맥 **안에서만** 값을 찾는다.
            같은 값이 다른 절에 있어도 통과하지 않는다. 손익·잔액은 **부호를 포함**해
            본문 표기(음수는 U+2212 '−')와 그대로 대조하므로 흑자/적자가 뒤집히면 잡힌다.
  장별 검사 대상 값:
            29장 — 30일 정산 폭포 각 단계, 장당 순수입, 현금·시간 손익(부호 포함), 손익분기 2종
            34장 — 생활비 역산 3값, 장당 입금액·민감도 5종, 손익분기 3종, 생계 후보작 필요량과
                   유지보수 시간, 현금흐름 표 기간 합계·월별 잔액, M+3 판정 입력, 7단계 실측 재계산,
                   평균의 곱 예시 3종($12.50 / $11.25 / 매출액 가중 $12.50)
            39장 — 12개월 시나리오 합계·장당·필요량, 유지보수 예산표(월 14h·연 184h·비용·비율·문턱)
            40장 — 24개월 시간표 합계와 시나리오별 출시 전 시간·버퍼, 현금흐름 합계 행과 M+6·M+23 잔액,
                   스트레스 5종의 최저 잔액·말 잔액·게임 손익(±부호)·H2 판매, 생활비 부담표,
                   종료 판정 문서의 필요량·궤도·판정 입력, 연습 문제의 $6.99 대안
  검사하지 않는 것 : 스프레드시트 수식 자체, 코드 예제, 장별 서술의 논리.

규칙
  1. 수치를 바꿀 땐 여기(가정 블록)에서 바꾼다. Markdown 을 먼저 고치지 않는다.
     파생 상수(유지보수 시간·월 개발시간·시나리오 설정 등)는 공통 가정에서 계산되므로
     공통 가정 하나를 바꾸면 29·34·39·40장 파생값이 모두 함께 움직인다.
  2. 실행 결과를 보고 해당 장의 표·본문·연습 해설·요약을 고친다.
  3. --check 가 통과할 때까지 장 본문을 맞춘다. 새 사례 수치를 본문에 넣으면 CHECKS 에도 추가한다.
  4. 반올림 규칙: 손익분기 판매량은 올림(그만큼 팔아야 회수), "약 N장" 근사는 반올림.
     원화 입금액은 '판매량 × 반올림한 장당 입금액'(스프레드시트 수식과 같은 방식).
     장당 입금액은 **폭포 끝에서 한 번만** 반올림한다(2,548 × 7.99/4.99 처럼 두 번 반올림하지 않는다).

용어
  M          = 코인 러시(CR) 출시 달. M+n 은 n개월 뒤.
  판매 발생월 = 판매가 일어난 달. 입금은 다음 달(Steam 월 정산).
  조정 총매출 = 총매출 − 환불·차지백 − 가격 포함 세금 (Steam Direct 환급 기준에 쓰는 값).
  게임 사업 현금 손익 = **M~M+23 창 안의 현금 잉여**. CR 출시 전 지출(M-2·M-1 180만 원)은 창 밖이므로
               두 작품의 전체 투자 회수 손익이 아니다.
"""
import math
import os
import re
import sys

# ════════════════════════════════════════════════════════════════════
# 가정 — 수치를 바꿀 땐 여기만 고친다
# ════════════════════════════════════════════════════════════════════

# ── 공통 ──
WAGE = 30_000                     # 시간 기회비용(원/h). 병행 React 계약직 세전 시급 가정 (34장)
FX_PLAN = 1_400                   # 계획용 환율(원/$)
BANK_FEE_PLAN = 0.01              # 은행 환전·수수료 (계획)
TAX_RESERVE = 0.15                # 입금액 중 세금 적립률 (34장)
EMERGENCY_FLOOR = 6_000_000       # 비상금 기준 (34장 연습 3, 40장 C2)
MIN_RUNWAY_MONTHS = 3             # C2 판정의 계약 없는 런웨이 하한 (40장)

# ── Steam 규칙 (공식 문서 기준, 34장 표) ──
VALVE_SHARE = 0.30
US_SALES_SHARE = 0.35             # 미국 매출 비중 (가정)
US_WITHHOLDING = 0.10             # 한미 조세조약 사용료 상한 적용 가정
DIRECT_FEE_USD = 100
DIRECT_FEE_KRW = 140_000          # $100 × 1,400 (계획용)
DIRECT_RECOUP_AGR_USD = 1_000     # 조정 총매출 $1,000 도달 후 환급
PAYOUT_MIN_USD = 100              # 월 지급액 $100 미만은 지급 보류 후 다음 달에 합산

# ── 코인 러시(H1) 개발 실적 (29장 포스트모템) ──
CR_PRICE = 4.99
CR_HOURS = 445                    # 출시 전 총작업시간 (마케팅·행정 포함)
CR_WEEKS = 26
CR_EXTERNAL = 2_100_000           # 외부 현금 비용 (Steam Direct $100 포함)

# ── 29장 30일 정산 (가상 실적) ──
D30_UNITS = 610
D30_GROSS_USD = 2_380             # 세금 포함·환불 전
D30_REFUND_RATE = 0.07
D30_TAX_RATE = 0.09               # 환불 차감 후 매출 대비
D30_WIRE_FEE_USD = 15
D30_FX = 1_350
D30_DIRECT_REFUND_KRW = 135_000

# ── 34장 02_장당 (출시 전 계획 가정) ──
PLAN_REGION_RATIO = 0.85          # 할인 전 지역 정가의 판매량 가중 평균 ÷ USD 정가 (계획용 추정)
PLAN_DISCOUNT = 0.25              # 평균 할인율 (계획용 추정)
PLAN_REFUND_RATE = 0.07           # 환불·차지백 ÷ 총매출
PLAN_TAX_RATE = 0.08              # 가격 포함 세금 ÷ 환불 차감 후 매출 (순차 정의)

# ── 34장 7단계: M~M+2 첫 3개월 정산서 (가상 실측) ──
M3_UNITS = 610 + 180 + 120
M3_GROSS_USD = 3_465              # M 2,380 + M+1 655 + M+2 430
M3_REFUND_USD = 217
M3_TAX_USD = 292
M3_US_SHARE = 0.30
M3_FX = 1_372

# ── 34장 1단계: 생활비 역산 ──
LIVING_MONTH = 2_100_000
INSURANCE_MONTH = 300_000
SAVINGS_MONTH = 150_000
BASIC_DEDUCTION = 1_500_000
ANNUAL_EXPENSES = 4_800_000

# ── 39장 5단계 유지보수 예산표 (연 시간) — 34·39·40장 유지보수 가정의 유일한 출처 ──
MAINT_ROUTINE_HOURS = {           # 매달 반복되는 활성 운영 (연 시간)
    "리뷰·문의·Discord 대응": 72,
    "크래시 리포트 확인·버그 수정": 48,
    "세일 등록·공지 작성·지역 가격 점검": 24,
    "월간 리포트 저장·입금·세무 자료": 24,
}
MAINT_REBUILD_RESERVE = 16        # 연 1회 필수 재빌드 예비 (보안·SDK·OS)
MAINT_HOURS_PER_YEAR_PLAN = sum(MAINT_ROUTINE_HOURS.values()) + MAINT_REBUILD_RESERVE   # 184h/년
MAINT_ACTIVE_HOURS_MONTH = sum(MAINT_ROUTINE_HOURS.values()) // 12                      # 월 14h
MAINT_PLAN_YEARS = 2              # 34장 3-1단계: 출시 후 24개월분

# ── 34장 3-1단계: 생계 후보작 (착수 전 계획) ──
NEXT_GAME_FUND = 1_500_000        # 월 250,000 × 6개월

# ── 34장 4단계 / 40장 3단계 현금흐름 ──
CONTRACT_INCOME = 2_400_000
CF_LIVING = 2_300_000
CF_DEV = 250_000
CF34_START = 12_300_000           # M-2 시작 잔액
CF34_PRELAUNCH_OUTS = {-2: 1_200_000, -1: 600_000, 0: 300_000}
CF34_FIRST_MONTH = -2             # 34장 표 시작 월
CF34_LAST_MONTH = 9               # 34장 표 끝 월
# CR 월 판매 가정 곡선 (M ~ M+23). 34장 표는 M~M+9, 40장 표는 전체
CR_CURVE = [610, 180, 120, 260, 90, 80, 200, 70, 60, 240,
            50, 45, 150, 40, 35, 150, 35, 30, 120, 30, 25, 140, 25, 20]
CR_SALE_MONTHS = {3: "여름 세일", 6: "가을 세일", 9: "겨울 세일", 12: "봄 세일",
                  15: "여름 세일", 18: "가을 세일", 21: "겨울 세일"}

# ── 40장: 두 번째 작품 H2 「랜턴 런」 ──
MONTHS_24 = 24                    # 40장 창: M ~ M+23
H2_PRICE = 7.99
H2_CURVE = [700, 150, 220, 90, 70, 200, 60, 50]   # 출시 달부터
H2_LAUNCH = 16
H2_OUTSOURCE = 3_000_000          # 지원금으로 집행
H2_DIRECT_PAY_MONTH = 9
GRANTS = {11: 1_000_000, 13: 1_000_000, 15: 1_000_000}
CF40_START = 10_200_000           # M-1 말
H2_PRELAUNCH_CAP_FACTOR = 1.5

# ── 40장 2단계 작업시간표 가정 ──
GAME_HOURS_MONTH = 80             # 주 20h × 48주 ÷ 12
CONTRACT_HOURS_MONTH = 104        # 주 3일 × 8h × 52주 ÷ 12
ADMIN_HOURS_MONTH = 8             # 행정·재무
ADMIN_LAUNCH_HOURS = 10           # 출시 직후 2개월은 행정도 늘어남
REST_WEEK_HOURS = 20              # M+1 분기 휴식 주
H2_DEV_HOURS_MONTH = GAME_HOURS_MONTH - MAINT_ACTIVE_HOURS_MONTH - ADMIN_HOURS_MONTH   # 월 58h
H1_LAUNCH_OPS_HOURS = 60          # M: H1 출시 달 운영
H1_REST_OPS_HOURS = 40            # M+1: 휴식 주
H1_REST_H2_HOURS = 10
PROTO_MONTHS = (2, 3, 4, 5)       # 프로토타입 3개 · 35장 게이트
PROTO_OPS_HOURS = 30
PROTO_H2_HOURS = 30
PROTO_BUFFER_HOURS = 12
LAUNCH_BUFFER_HOURS = 10          # M 의 버퍼
NEXT_FEST_BUFFER = 24             # 출시 1개월 전(Next Fest) 지연 흡수 버퍼
H2_LAUNCH_OPS_HOURS = 6           # H2 출시 달의 기존작 운영
POSTLAUNCH_BUFFER = 18            # H2 출시 다음 달 핫픽스 버퍼
H2_MAINT_HOURS_MONTH = 16         # H2 출시 후 유지보수
REBUILD_MONTHS = (11, 23)         # 필수 재빌드 예비를 넣은 달
JOB_SEARCH_HOURS = 20             # 계약 중단 시나리오의 구직 시간/월
JOB_SEARCH_LEAD = 3               # 계약 만료 몇 개월 전부터 구직하는가

# ── 40장 4단계 스트레스 테스트 설정 (시간표와 현금표가 같은 설정을 쓴다) ──
S1_MULT = 0.3                     # 흥행 실패 배수
S2_DELAY_MONTHS = 3               # 출시 지연 개월
S2_EXTRA_OUTSOURCE = 500_000      # 지연 중 추가 외주비
S2_EXTRA_OUTS_MONTH = H2_LAUNCH + 1
S3_CONTRACT_OFF = tuple(range(H2_LAUNCH - 1, H2_LAUNCH + 2))   # (15, 16, 17)
SCENARIOS = {
    "기준": dict(),
    "S1": dict(h2_mult=S1_MULT),
    "S2": dict(launch=H2_LAUNCH + S2_DELAY_MONTHS,
               extra_outs={S2_EXTRA_OUTS_MONTH: S2_EXTRA_OUTSOURCE}),
    "S3": dict(contract_off=S3_CONTRACT_OFF),
    "S4": dict(h2_mult=S1_MULT, contract_off=S3_CONTRACT_OFF),
    "S5": dict(launch=H2_LAUNCH + S2_DELAY_MONTHS,
               extra_outs={S2_EXTRA_OUTS_MONTH: S2_EXTRA_OUTSOURCE},
               contract_off=S3_CONTRACT_OFF),
}
SCENARIO_VERDICT = {"기준": "B", "S1": "C1", "S2": "B", "S3": "B", "S4": "C2", "S5": "C2"}

# ── 39장 ($7.99 가격 인상 시나리오, 운영 계획용 어림) ──
Y39_UNITS = [610, 380, 150, 260, 230, 80, 200, 210, 120, 60, 55, 170]
Y39_NET_USD = [2196, 1140, 480, 806, 713, 312, 620, 630, 384, 234, 215, 510]
Y39_WAGE = 40_000

MINUS = "−"   # 본문 표기의 음수 기호

# ════════════════════════════════════════════════════════════════════
# 계산
# ════════════════════════════════════════════════════════════════════


def ceil(x):
    return math.ceil(x - 1e-9)


def fmt(n):
    return f"{n:,}"


def won(v, suffix=""):
    """본문 표기와 같은 부호 붙은 금액 문자열 (음수는 U+2212)."""
    v = int(round(v))
    return (MINUS if v < 0 else "") + f"{abs(v):,}" + suffix


def won_pm(v, suffix=""):
    """표에서 흑자/적자를 +/− 로 함께 적는 칸용 (부호가 뒤집히면 검사가 잡는다)."""
    v = int(round(v))
    return (MINUS if v < 0 else "+") + f"{abs(v):,}" + suffix


def unit_usd(price, *, region=PLAN_REGION_RATIO, discount=PLAN_DISCOUNT,
             refund=PLAN_REFUND_RATE, tax=PLAN_TAX_RATE, us_share=US_SALES_SHARE):
    """장당 달러 지급액 (원천징수 후). 계획용 순차 곱."""
    asp = price * region * (1 - discount)        # 평균 판매단가 (세금 포함·환불 전)
    agr = asp * (1 - refund) * (1 - tax)         # 조정 총매출
    return asp, agr, agr * (1 - VALVE_SHARE) * (1 - us_share * US_WITHHOLDING)


def unit_krw(price, fx=FX_PLAN, bank=BANK_FEE_PLAN, **kw):
    return unit_usd(price, **kw)[2] * fx * (1 - bank)


R = {}  # 장별 결과 저장


def ch29():
    r = {}
    gross = D30_GROSS_USD
    refund = round(gross * D30_REFUND_RATE)
    after_refund = gross - refund
    tax = round(after_refund * D30_TAX_RATE)
    net = after_refund - tax
    valve = round(net * VALVE_SHARE)
    after_valve = net - valve
    wh = round(after_valve * US_SALES_SHARE * US_WITHHOLDING)
    after_wh = after_valve - wh
    usd_final = after_wh - D30_WIRE_FEE_USD
    krw = usd_final * D30_FX
    per = round(krw / D30_UNITS)
    units_ex_refund = D30_UNITS - round(D30_UNITS * D30_REFUND_RATE)
    time_cost = CR_HOURS * WAGE
    cash_pl = krw + D30_DIRECT_REFUND_KRW - CR_EXTERNAL
    be_cash = ceil((CR_EXTERNAL - D30_DIRECT_REFUND_KRW) / per)
    be_time = ceil((CR_EXTERNAL - D30_DIRECT_REFUND_KRW + time_cost) / per)
    r.update(gross=gross, refund=refund, after_refund=after_refund, tax=tax, net=net, valve=valve,
             after_valve=after_valve, wh=wh, after_wh=after_wh, usd_final=usd_final, krw=krw, per=per,
             asp=round(gross / D30_UNITS, 2), per_ex_refund=round(krw / units_ex_refund),
             units_ex_refund=units_ex_refund, list_krw=int(CR_PRICE * D30_FX + 0.5),
             time_cost=time_cost, cash_pl=cash_pl, time_pl=cash_pl - time_cost,
             be_cash=be_cash, be_time=be_time,
             pct_cash=round(100 * D30_UNITS / be_cash), pct_time=round(100 * D30_UNITS / be_time))
    R[29] = r
    return r


def tax_kr(x):
    if x <= 14_000_000:
        t = x * 0.06
    elif x <= 50_000_000:
        t = x * 0.15 - 1_260_000
    elif x <= 88_000_000:
        t = x * 0.24 - 5_760_000
    elif x <= 150_000_000:
        t = x * 0.35 - 15_440_000
    else:
        t = x * 0.38 - 19_940_000
    return 1.1 * max(0, t)


def ch34():
    r = {}
    # 1단계 생활비 역산
    after_tax_need = (LIVING_MONTH + INSURANCE_MONTH + SAVINGS_MONTH) * 12
    x = after_tax_need
    for _ in range(100):
        x = after_tax_need + tax_kr(x - BASIC_DEDUCTION)
    income_need = int(round(x, -4))
    revenue_need = income_need + ANNUAL_EXPENSES
    r.update(after_tax_need=after_tax_need, income_tax=income_need - after_tax_need,
             income_need=income_need, revenue_need=revenue_need)

    # 2단계 장당 (계획)
    asp, agr, usd = unit_usd(CR_PRICE)
    krw = unit_krw(CR_PRICE)
    U = round(krw)
    steps = []
    v = CR_PRICE; steps.append(("정가", v))
    v = asp; steps.append(("평균 판매단가", v))
    v = v * (1 - PLAN_REFUND_RATE); steps.append(("환불 후", v))
    v = v * (1 - PLAN_TAX_RATE); steps.append(("세금 후(조정 총매출)", v))
    v = v * (1 - VALVE_SHARE); steps.append(("배분 후", v))
    v = v * (1 - US_SALES_SHARE * US_WITHHOLDING); steps.append(("원천징수 후", v))
    v = v * FX_PLAN; steps.append(("환율", v))
    v = v * (1 - BANK_FEE_PLAN); steps.append(("은행 후", v))
    r.update(U=U, U_exact=krw, asp=asp, agr=agr, usd=usd, steps=steps,
             usd_ratio=round(100 * usd / CR_PRICE, 1))
    # 평균의 곱 경고 예시 (연습 4 해설과 같은 예)
    r["avg_example_true"] = 10 * 1.0 + 5 * 0.5            # 실제 총매출 $12.50
    r["avg_example_wrong"] = 2 * 10 * 0.75 * 0.75         # 산술평균 할인율로 분해 $11.25
    r["avg_example_weighted"] = 2 * 10 * 0.75 * (1 - 2.5 / 15)   # 매출액 가중이면 다시 $12.50
    # 민감도
    r["sens"] = {
        "fx_low": round(unit_krw(CR_PRICE, fx=1_260)),
        "fx_high": round(unit_krw(CR_PRICE, fx=1_540)),
        "wh_all": round(unit_krw(CR_PRICE, us_share=1.0)),
        "disc40": round(unit_krw(CR_PRICE, discount=0.40)),
        "p699": round(unit_krw(6.99)),
    }
    r["direct_recoup_units"] = ceil(DIRECT_RECOUP_AGR_USD / agr)

    # 3단계 손익분기 (Direct 환급은 보수적으로 차감하지 않음)
    labor = CR_HOURS * WAGE
    r.update(be_cash=ceil(CR_EXTERNAL / U), labor=labor, labor_total=CR_EXTERNAL + labor,
             be_labor=ceil((CR_EXTERNAL + labor) / U), be_life=int(round(revenue_need / U, -2)),
             d30_pct_cash=round(100 * 610 / ceil(CR_EXTERNAL / U)),
             d30_pct_labor=round(100 * 610 / ceil((CR_EXTERNAL + labor) / U)))

    # 3-1단계 생계 후보작 (착수 전 계획: 39장 유지보수 예산 × 2년)
    maint_h = MAINT_HOURS_PER_YEAR_PLAN * MAINT_PLAN_YEARS
    total = CR_EXTERNAL + labor + maint_h * WAGE + NEXT_GAME_FUND
    need = round(total / U)
    r.update(maint_h=maint_h, maint_cost=maint_h * WAGE, cand_total=total, cand_need=need,
             cand_monthly=round(need / 24), rev_lo=round(need / 60), rev_hi=round(need / 20))
    sales10 = sum(CR_CURVE[:10])
    sales12 = sum(CR_CURVE[:12])
    r.update(sales10=sales10, sales12=sales12, pct10=round(100 * sales10 / need),
             pct12=round(100 * sales12 / need), sales12x2=2 * sales12,
             pct12x2=round(100 * 2 * sales12 / need))

    # 4단계 현금흐름 (M-2 ~ M+9)
    rows = []
    bal = CF34_START
    cum_agr = 0.0
    refund_month = None
    for m in range(CF34_FIRST_MONTH, CF34_LAST_MONTH + 1):
        sales = CR_CURVE[m] if m >= 0 else 0
        dep = CR_CURVE[m - 1] * U if m >= 1 else 0
        direct = DIRECT_FEE_KRW if (refund_month is not None and m == refund_month + 1) else 0
        # 34장 표 기간에는 CR 월 지급액이 모두 $100 이상 (보류 없음) — 아래에서 확인
        if m >= 1:
            assert CR_CURVE[m - 1] * usd >= PAYOUT_MIN_USD
        if m >= 0 and refund_month is None:
            cum_agr += sales * agr
            if cum_agr >= DIRECT_RECOUP_AGR_USD:
                refund_month = m
        outs = -CF34_PRELAUNCH_OUTS.get(m, 0)
        tax = -round(TAX_RESERVE * (dep + direct))
        net = CONTRACT_INCOME + dep + direct - CF_LIVING - CF_DEV + outs + tax
        bal += net
        rows.append((m, sales, dep, direct, outs, tax, net, bal))
    r["cf_rows"] = rows
    in_window_dep = sum(x[2] for x in rows)
    r.update(cf_dep=in_window_dep, cf_dep_units=sum(CR_CURVE[:9]),
             cf_outside_units=CR_CURVE[9], cf_outside_dep=CR_CURVE[9] * U,
             cf_tax=-sum(x[5] for x in rows), cf_end=rows[-1][-1],
             cf_bal_m3=[x for x in rows if x[0] == 3][0][-1],
             prelaunch_outside=sum(v for k, v in CF34_PRELAUNCH_OUTS.items() if k < 0))
    # 6단계 판정 (M+3)
    rec3 = [x[2] for x in rows if x[0] in (1, 2, 3)]
    avg3 = round(sum(rec3) / 3)
    ft_month = LIVING_MONTH + INSURANCE_MONTH + CF_DEV
    r.update(dec_avg3=avg3, dec_runway=round(r["cf_bal_m3"] / ft_month, 1),
             dec_ref_runway=round(r["cf_bal_m3"] / (ft_month - avg3), 1),
             dec_cum3=sum(rec3) + DIRECT_FEE_KRW, half_need=revenue_need // 2,
             ft_month=ft_month, savings_goal=ft_month * 12)

    # 7단계 첫 3개월 정산서 (가상 실측) — 실제 평균 판매단가 방식
    m3_asp = M3_GROSS_USD / M3_UNITS
    m3_net = M3_GROSS_USD - M3_REFUND_USD - M3_TAX_USD
    m3_after_valve = m3_net * (1 - VALVE_SHARE)
    m3_wh = m3_after_valve * M3_US_SHARE * US_WITHHOLDING
    m3_usd = m3_after_valve - m3_wh
    m3_krw = m3_usd * M3_FX * (1 - BANK_FEE_PLAN)
    U3 = round(m3_krw / M3_UNITS)
    r.update(m3_asp=m3_asp, m3_asp_ratio=round(100 * m3_asp / CR_PRICE), m3_net=m3_net,
             m3_refund_pct=round(100 * M3_REFUND_USD / M3_GROSS_USD, 1),
             m3_tax_pct=round(100 * M3_TAX_USD / (M3_GROSS_USD - M3_REFUND_USD), 1),
             m3_after_valve=round(m3_after_valve), m3_wh=round(m3_wh), m3_usd=round(m3_usd),
             m3_krw=int(round(m3_krw, -3)), U3=U3, U3_pct=round(100 * (U3 - U) / U),
             m3_be_cash=ceil(CR_EXTERNAL / U3), m3_be_labor=ceil((CR_EXTERNAL + labor) / U3),
             m3_be_life=int(round(revenue_need / U3, -2)), m3_cand=round(total / U3))
    R[34] = r
    return r


def payout_usd_per_unit(price):
    return unit_usd(price)[2]


# ────────────────────────────────────────────────────────────────────
# 40장 2단계 — 시나리오별 24개월 작업시간표
# ────────────────────────────────────────────────────────────────────

def hours_scenario(launch=H2_LAUNCH, contract_off=(), **_ignored):
    """시나리오 설정(출시 월·계약 중단)으로 24개월 시간표를 만들고 상한을 판정한다.

    현금 시나리오와 **같은 설정 딕셔너리**를 받으므로, 현금표가 통과해도 시간표가
    상한을 넘으면 여기서 드러난다(reapproval=True).
    """
    dev = H2_DEV_HOURS_MONTH
    rows = []
    for m in range(MONTHS_24):
        job = 0
        if m == 0:                      # H1 출시 달
            cr, h2, admin, buf = H1_LAUNCH_OPS_HOURS, 0, ADMIN_LAUNCH_HOURS, LAUNCH_BUFFER_HOURS
        elif m == 1:                    # 휴식 주가 든 달 (게임 60h)
            cr, h2, admin, buf = H1_REST_OPS_HOURS, H1_REST_H2_HOURS, ADMIN_LAUNCH_HOURS, 0
        elif m in PROTO_MONTHS:         # 프로토타입 3개 · 35장 게이트
            cr, h2, admin, buf = PROTO_OPS_HOURS, PROTO_H2_HOURS, ADMIN_HOURS_MONTH, PROTO_BUFFER_HOURS
        elif m < launch - 1:            # H2 제작 달
            cr, h2, admin, buf = MAINT_ACTIVE_HOURS_MONTH, dev, ADMIN_HOURS_MONTH, 0
        elif m == launch - 1:           # Next Fest · 지연 흡수 버퍼
            cr, h2, admin, buf = (MAINT_ACTIVE_HOURS_MONTH, dev - NEXT_FEST_BUFFER,
                                  ADMIN_HOURS_MONTH, NEXT_FEST_BUFFER)
        elif m == launch:               # H2 출시 달 (버퍼 0)
            cr = H2_LAUNCH_OPS_HOURS
            admin, buf = ADMIN_HOURS_MONTH, 0
            h2 = GAME_HOURS_MONTH - cr - admin
        elif m == launch + 1:           # 핫픽스·30일 운영
            cr, h2, admin, buf = (MAINT_ACTIVE_HOURS_MONTH, dev - POSTLAUNCH_BUFFER,
                                  ADMIN_HOURS_MONTH, POSTLAUNCH_BUFFER)
        else:                           # H2 유지보수 + 다음 가설
            cr, h2, admin, buf = (MAINT_ACTIVE_HOURS_MONTH, H2_MAINT_HOURS_MONTH,
                                  ADMIN_HOURS_MONTH, dev - H2_MAINT_HOURS_MONTH)
        if m in REBUILD_MONTHS:         # 필수 재빌드 예비는 버퍼 → 없으면 H2 개발에서
            cr += MAINT_REBUILD_RESERVE
            if buf >= MAINT_REBUILD_RESERVE:
                buf -= MAINT_REBUILD_RESERVE
            else:
                h2 -= MAINT_REBUILD_RESERVE
        contract = 0 if m in contract_off else CONTRACT_HOURS_MONTH
        rows.append(dict(m=m, contract=contract, cr=cr, h2=h2, admin=admin, job=job, buf=buf))

    # 구직 시간: 계약 만료 3개월 전부터는 게임 시간(버퍼 → H2)에서, 계약이 끊긴 달은 비게 된 계약 시간에서
    cut = 0
    if contract_off:
        first = min(contract_off)
        for m in range(max(0, first - JOB_SEARCH_LEAD), first):
            need = JOB_SEARCH_HOURS
            take = min(rows[m]["buf"], need)
            rows[m]["buf"] -= take
            need -= take
            rows[m]["h2"] -= need
            cut += need
            rows[m]["job"] = JOB_SEARCH_HOURS
        for m in contract_off:
            rows[m]["job"] = JOB_SEARCH_HOURS

    for x in rows:
        x["game"] = x["cr"] + x["h2"] + x["admin"] + x["buf"]
        # 계약이 도는 달의 구직 시간은 게임 예산 안에서 빼 오고, 계약이 끊긴 달은 비게 된 계약 시간에서 온다
        x["budget"] = x["game"] + (x["job"] if x["contract"] else 0)
    tot = {k: sum(x[k] for x in rows)
           for k in ("contract", "cr", "h2", "admin", "job", "buf", "game", "budget")}

    h2_pre = sum(x["h2"] for x in rows if x["m"] < launch)
    used_before_plan = sum(x["h2"] for x in rows if x["m"] < 6)
    cap_h = int(round(CR_HOURS * H2_PRELAUNCH_CAP_FACTOR, -1))     # 667.5 → 670h
    remain = cap_h - used_before_plan
    cal_cap = ceil(remain / dev)
    cal_cap_last = 5 + cal_cap                                     # 계획 시점 M+6 부터
    acc, fill_m = 0, None
    for x in rows:
        if x["m"] < 6:
            continue
        acc += x["h2"]
        if fill_m is None and acc >= remain:
            fill_m = x["m"]
    within_time = h2_pre <= cap_h
    within_cal = launch <= cal_cap_last + 1
    return dict(rows=rows, tot=tot, launch=launch, h2_pre=h2_pre, job_cut=cut,
                used_before_plan=used_before_plan, cap_h=cap_h, remain=remain,
                cal_cap_exact=round(remain / dev, 1), cal_cap=cal_cap, cal_cap_last=cal_cap_last,
                fill_m=fill_m, cal_from_start=round(cap_h / dev, 1),
                within_time=within_time, within_cal=within_cal,
                reapproval=not (within_time and within_cal),
                contract_off=tuple(contract_off))


def scenario(h2_mult=1.0, launch=H2_LAUNCH, contract_off=(), extra_outs=None):
    """40장 24개월(M~M+23) 합산 현금흐름. 지급 보류·Direct 환급 규칙 반영.

    게임 '사업 손익'과 '생활비 배분'은 분리한다. 사업이 적자면 생활비 부담액은 0이고,
    적자는 계약 수입·저축이 메운 것으로 본다(배분액을 음수로 만들지 않는다).
    """
    extra_outs = extra_outs or {}
    U1 = R[34]["U"]
    U2 = round(unit_krw(H2_PRICE))     # 폭포 끝에서 한 번만 반올림 (2,548 × 7.99/4.99 로 두 번 반올림하지 않음)
    usd1 = payout_usd_per_unit(CR_PRICE)
    usd2 = payout_usd_per_unit(H2_PRICE)
    agr1 = unit_usd(CR_PRICE)[1]
    agr2 = unit_usd(H2_PRICE)[1]
    N = MONTHS_24
    h2 = [0] * N
    for i, v in enumerate(H2_CURVE):
        if launch + i < N:
            h2[launch + i] = round(v * h2_mult)
    cum = {"CR": 0.0, "H2": 0.0}
    reached = {"CR": None, "H2": None}
    held = dict(cr=0, h2=0, direct=0, usd=0.0)
    bal = CF40_START
    rows = []
    for m in range(N):
        # 이번 달 지급 대상 (전월 판매 + 환급)
        new_cr = CR_CURVE[m - 1] * U1 if m >= 1 else 0
        new_h2 = h2[m - 1] * U2 if m >= 1 else 0
        new_usd = (CR_CURVE[m - 1] * usd1 + h2[m - 1] * usd2) if m >= 1 else 0.0
        new_direct = 0
        for app in ("CR", "H2"):
            if reached[app] is not None and m == reached[app] + 1:
                new_direct += DIRECT_FEE_KRW
                new_usd += DIRECT_FEE_USD
        pend = dict(cr=held["cr"] + new_cr, h2=held["h2"] + new_h2,
                    direct=held["direct"] + new_direct, usd=held["usd"] + new_usd)
        if m >= 1 and pend["usd"] >= PAYOUT_MIN_USD:
            paid = pend
            held = dict(cr=0, h2=0, direct=0, usd=0.0)
        else:
            paid = dict(cr=0, h2=0, direct=0, usd=0.0)
            held = pend
        # 이번 달 판매로 조정 총매출 누적 → 환급 도달 월 기록
        cum["CR"] += CR_CURVE[m] * agr1
        cum["H2"] += h2[m] * agr2
        for app in ("CR", "H2"):
            if reached[app] is None and cum[app] >= DIRECT_RECOUP_AGR_USD:
                reached[app] = m
        contract = 0 if m in contract_off else CONTRACT_INCOME
        grant = GRANTS.get(m, 0)
        outs = 0
        if m == 0:
            outs -= CF34_PRELAUNCH_OUTS[0]
        if m in GRANTS:
            outs -= GRANTS[m]
        if m == H2_DIRECT_PAY_MONTH:
            outs -= DIRECT_FEE_KRW
        outs -= extra_outs.get(m, 0)
        tax = -round(TAX_RESERVE * (paid["cr"] + paid["h2"] + paid["direct"]))
        net = contract + paid["cr"] + paid["h2"] + paid["direct"] + grant - CF_LIVING - CF_DEV + outs + tax
        bal += net
        held_usd = round(held["usd"])
        rows.append(dict(m=m, cr_sales=CR_CURVE[m], h2_sales=h2[m], contract=contract,
                         cr_dep=paid["cr"], h2_dep=paid["h2"], held_usd=held_usd,
                         direct=paid["direct"], grant=grant, living=-CF_LIVING, dev=-CF_DEV,
                         outs=outs, tax=tax, net=net, bal=bal))
    tot = {k: sum(r[k] for r in rows) for k in
           ("cr_sales", "h2_sales", "contract", "cr_dep", "h2_dep", "direct", "grant",
            "living", "dev", "outs", "tax", "net")}

    # ── 게임 사업 손익 (배분과 분리) ─────────────────────────────
    game_in = tot["cr_dep"] + tot["h2_dep"] + tot["direct"]          # 게임 입금 + 환급
    outs_nongrant = -tot["outs"] - sum(GRANTS.values())              # 지원금이 덮지 않은 외주·등록비
    game_out_nongrant = -tot["tax"] - tot["dev"] + outs_nongrant     # 세금 적립 + 개발·마케팅 + 위
    game_surplus = game_in - game_out_nongrant                       # 지원금이 외주를 덮은 실제 결과
    game_pl = game_in + tot["tax"] + tot["dev"] + tot["outs"]        # 지원금 제외 게임 사업 현금 손익 (M~M+23)

    # ── 생활비 배분 (0 ~ 생활비 상한으로 클램프) ────────────────
    living_total = -tot["living"]
    game_living = min(max(game_surplus, 0), living_total)
    game_deficit = max(-game_surplus, 0)                             # 사업 적자 (생활비 배분과 분리)
    remaining = living_total - game_living
    contract_share = min(tot["contract"], remaining)
    savings_draw = remaining - contract_share
    assert game_living + contract_share + savings_draw == living_total
    assert min(game_living, contract_share, savings_draw) >= 0

    # ── 최근 12개월(M+12~M+23) ──────────────────────────────────
    last12 = [r for r in rows if r["m"] >= 12]
    l12_dep = sum(r["cr_dep"] + r["h2_dep"] + r["direct"] for r in last12)
    l12_tax = -sum(r["tax"] for r in last12)
    l12_dev = -sum(r["dev"] for r in last12)
    l12_outs_nongrant = -sum(r["outs"] for r in last12) - sum(GRANTS[m] for m in GRANTS if m >= 12)
    l12_living = CF_LIVING * 12
    l12_paid_living = min(max(l12_dep - l12_tax - l12_dev - l12_outs_nongrant, 0), l12_living)

    after6 = [r for r in rows if r["m"] >= 6]
    mn = min(after6, key=lambda r: r["bal"])
    below = [r["m"] for r in rows if r["bal"] < EMERGENCY_FLOOR]
    h2_paid_units = tot["h2_dep"] // U2
    runway_end = round(rows[-1]["bal"] / (CF_LIVING + CF_DEV), 1)
    return dict(rows=rows, tot=tot, game_pl=game_pl, game_surplus=game_surplus,
                game_deficit=game_deficit, min_bal=mn["bal"], min_m=mn["m"],
                below=below, end=rows[-1]["bal"], runway_end=runway_end,
                h2_total=sum(h2), h2_paid_units=h2_paid_units, reached=dict(reached),
                l12_dep=l12_dep, l12_tax=l12_tax, l12_paid_living=l12_paid_living,
                l12_pct=round(100 * l12_paid_living / l12_living, 1),
                game_living=game_living, contract_share=contract_share, savings_draw=savings_draw,
                living_total=living_total, U2=U2, outs_nongrant=outs_nongrant,
                launch=launch, contract_off=tuple(contract_off))


def verdict(s, h2_be):
    """40장 개념 절의 판정표를 잔액·손익 규칙으로 다시 매긴다 (수치 조건만).

    A1·A2 의 계획서·적립 같은 비수치 조건은 모델이 판정하지 않으므로, 수치 조건이
    모두 통과하면 'A?(비수치 조건 확인)' 를 돌려준다.
    """
    if s["below"] or s["runway_end"] < MIN_RUNWAY_MONTHS:
        return "C2"
    if s["game_pl"] < 0 or s["h2_total"] < h2_be:
        return "C1"
    if s["l12_dep"] >= R[34]["revenue_need"]:
        return "A2?(비수치 조건 확인)"
    if s["l12_dep"] >= R[34]["half_need"] and s["l12_paid_living"] >= s["living_total"] / 24 * 12 * 0.5:
        return "A1?(비수치 조건 확인)"
    return "B"


def lab(m):
    return "M" if m == 0 else f"M+{m}"


def ch40():
    r = {}
    U1 = R[34]["U"]
    S = {k: scenario(**v) for k, v in SCENARIOS.items()}
    H = {k: hours_scenario(**v) for k, v in SCENARIOS.items()}
    B, HB = S["기준"], H["기준"]
    U2 = B["U2"]
    r.update(S=S, H=H, U2=U2)

    # 시간 (기준 시나리오)
    r.update(cr_ops=HB["tot"]["cr"], h2_hours=HB["tot"]["h2"], admin=HB["tot"]["admin"],
             buf=HB["tot"]["buf"], game_total=HB["tot"]["game"], contract_hours=HB["tot"]["contract"],
             cr_ops_early=sum(x["cr"] for x in HB["rows"] if x["m"] < 6),
             cr_ops_late=sum(x["cr"] for x in HB["rows"] if x["m"] >= 6),
             h2_pre=HB["h2_pre"], h2_launch_month=HB["rows"][H2_LAUNCH]["h2"], cap_h=HB["cap_h"],
             h2_used_before_plan=HB["used_before_plan"], remain=HB["remain"],
             cal_cap_exact=HB["cal_cap_exact"], cal_cap=HB["cal_cap"],
             cal_cap_last=HB["cal_cap_last"], fill_m=HB["fill_m"],
             cal_from_start=HB["cal_from_start"])
    # S3 수정 시간표: 구직 시간을 H2 개발에서 가져옴 → 범위 컷
    r.update(s3_h2_month=H["S3"]["rows"][12]["h2"], s3_cut=H["S3"]["job_cut"], s3_h2_pre=H["S3"]["h2_pre"])
    # S2 지연 시간표
    s2_extra_hours = H["S2"]["h2_pre"] - HB["h2_pre"]
    r.update(s2_extra_hours=s2_extra_hours, s2_buf=H["S2"]["tot"]["buf"],
             s2_buf_diff=HB["tot"]["buf"] - H["S2"]["tot"]["buf"])

    # 생계 후보작 필요량
    cr_ops = r["cr_ops"]
    actual_total = CR_EXTERNAL + CR_HOURS * WAGE + cr_ops * WAGE + NEXT_GAME_FUND
    cr_need_plan = R[34]["cand_need"]
    cr_need_actual = round(actual_total / U1)
    # H2 외부 현금 비용: 34장과 같은 정의 — Steam Direct 포함, 환급은 차감하지 않음
    h2_external = H2_OUTSOURCE + DIRECT_FEE_KRW
    h2_total_req = h2_external + HB["h2_pre"] * WAGE + cr_ops * WAGE + NEXT_GAME_FUND
    h2_need = round(h2_total_req / U2)
    s2_external = h2_external + S2_EXTRA_OUTSOURCE
    s2_total = s2_external + H["S2"]["h2_pre"] * WAGE + cr_ops * WAGE + NEXT_GAME_FUND
    U699 = R[34]["sens"]["p699"]
    r.update(cr_actual_total=actual_total, cr_need_plan=cr_need_plan, cr_need_actual=cr_need_actual,
             cr_need_diff=cr_need_actual - cr_need_plan, maint_diff_h=cr_ops - R[34]["maint_h"],
             h2_external=h2_external, h2_req_total=h2_total_req, h2_need=h2_need,
             h2_rev_lo=round(h2_need / 60), h2_rev_hi=round(h2_need / 20),
             s2_external=s2_external, s2_hours=H["S2"]["h2_pre"], s2_total=s2_total,
             s2_need=round(s2_total / U2),
             h2_need_699=round(h2_total_req / U699),
             h2_need_699_diff=round(h2_total_req / U699) - h2_need,
             h2_be=ceil(h2_external / U2))
    cr24 = sum(CR_CURVE)
    cr8 = sum(CR_CURVE[:8]); cr_rest = sum(CR_CURVE[8:])
    h2_8 = B["h2_total"]
    h2_24 = round(h2_8 * (1 + cr_rest / cr8))
    r.update(cr24=cr24, cr8=cr8, cr_rest=cr_rest, cr_ratio=round(cr_rest / cr8, 2), h2_24=h2_24,
             cr24_pct_actual=round(100 * cr24 / cr_need_actual), cr24_pct_plan=round(100 * cr24 / cr_need_plan),
             h2_24_pct=round(100 * h2_24 / h2_need),
             launch_share_h2=round(100 * H2_CURVE[0] / h2_8), launch_share_cr=round(100 * CR_CURVE[0] / cr8),
             h2_vs_cr8=round(100 * h2_8 / cr8))
    # 종료 판정 입력 (기준)
    ft = R[34]["ft_month"]
    r.update(runway_ft=round(B["end"] / ft, 1), runway_nc=B["runway_end"],
             l12_life=CF_LIVING * 12, half_need=R[34]["half_need"],
             l12_vs_half=round(100 * B["l12_dep"] / R[34]["half_need"]),
             grant_hourly=round(B["game_living"] / r["game_total"]))
    r["nogrant_hourly"] = round((B["game_pl"]) / r["game_total"])
    last3 = [x for x in B["rows"] if x["m"] in (21, 22, 23)]
    r["cr_last3_avg"] = round(sum(x["cr_dep"] for x in last3) / 3)
    r["cr_last3"] = [x["cr_dep"] for x in last3]
    r["verdict"] = {k: verdict(S[k], r["h2_be"]) for k in S}
    R[40] = r
    return r


def ch39():
    r = {}
    units = sum(Y39_UNITS)
    usd = sum(Y39_NET_USD)
    krw = usd * FX_PLAN
    per_usd = usd / units
    per_krw = round(per_usd * FX_PLAN)
    rest = usd - Y39_NET_USD[0]
    maint_h = MAINT_HOURS_PER_YEAR_PLAN          # 공통 가정에서 온다 (하드코딩 금지)
    r.update(units=units, usd=usd, krw=krw, monthly=round(krw / 12, -3), per_krw=per_krw,
             need=round(R[34]["cand_total"] / per_krw), units2y=units * 2,
             pess=round(Y39_NET_USD[0] + rest * 0.6), opt=round(Y39_NET_USD[0] + rest * 1.6),
             pess_krw=round((Y39_NET_USD[0] + rest * 0.6) * FX_PLAN, -4),
             opt_krw=round((Y39_NET_USD[0] + rest * 1.6) * FX_PLAN, -4),
             maint_h=maint_h, maint_month=MAINT_ACTIVE_HOURS_MONTH,
             maint_cost=maint_h * Y39_WAGE, maint_pct=round(100 * maint_h * Y39_WAGE / krw),
             mode_threshold=MAINT_ACTIVE_HOURS_MONTH * Y39_WAGE,
             m1_share=round(100 * Y39_UNITS[0] / units))
    R[39] = r
    return r


# ════════════════════════════════════════════════════════════════════
# 출력
# ════════════════════════════════════════════════════════════════════

def report():
    a, b, d, c = R[29], R[34], R[40], R[39]
    p = print
    p("=" * 70); p("29장 — 30일 정산 (가상 실적)"); p("=" * 70)
    p(f"총매출 ${a['gross']:,} (평균 실결제가 ${a['asp']}) → 환불 −${a['refund']} → ${a['after_refund']:,}"
      f" → 세금 −${a['tax']} → ${a['net']:,} → Valve −${a['valve']} → ${a['after_valve']:,}"
      f" → 원천징수 −${a['wh']} → ${a['after_wh']:,} → 송금 −$15 → ${a['usd_final']:,}")
    p(f"× {D30_FX} = {fmt(a['krw'])}원, 장당 {fmt(a['per'])}원 (정가 {fmt(a['list_krw'])}원), "
      f"환불 제외 {a['units_ex_refund']}장 기준 {fmt(a['per_ex_refund'])}원")
    p(f"현금 손익 {won(a['cash_pl'])} / 시간 비용 {fmt(a['time_cost'])} / 시간 포함 {won(a['time_pl'])}")
    p(f"손익분기(환급 차감): 현금 {a['be_cash']}장 ({a['pct_cash']}%), 시간 포함 {fmt(a['be_time'])}장 ({a['pct_time']}%)")

    p(); p("=" * 70); p("34장 — 생계 수학"); p("=" * 70)
    p(f"1단계: 연 세후 필요액 {fmt(b['after_tax_need'])}, 세금 {fmt(b['income_tax'])}, "
      f"사업소득 {fmt(b['income_need'])}, 연 필요 매출 {fmt(b['revenue_need'])}")
    p("2단계 장당(계획):")
    for name, v in b["steps"]:
        p(f"   {name:<16} {v:,.3f}")
    p(f"   → 장당 ₩{fmt(b['U'])} (정확값 {b['U_exact']:.4f}), 달러 입금 비율 {b['usd_ratio']}%, "
      f"조정 총매출/장 ${b['agr']:.4f}, Direct 환급 도달 {b['direct_recoup_units']}장")
    p(f"   평균의 곱: 실제 ${b['avg_example_true']:.2f} / 산술평균 할인율 ${b['avg_example_wrong']:.2f} "
      f"/ 매출액 가중 할인율 ${b['avg_example_weighted']:.2f} (가중하면 정확히 재구성)")
    p(f"   민감도: {b['sens']}")
    p(f"3단계: 현금 {b['be_cash']}장, 인건비 {fmt(b['labor'])} → {fmt(b['labor_total'])} → {fmt(b['be_labor'])}장,"
      f" 연 생계 {fmt(int(b['be_life']))}장. 30일 610장 = {b['d30_pct_cash']}% / {b['d30_pct_labor']}%")
    p(f"3-1단계(계획): 유지보수 {b['maint_h']}h = {fmt(b['maint_cost'])}, 합계 {fmt(b['cand_total'])} → "
      f"{fmt(b['cand_need'])}장 (월 {b['cand_monthly']}), 리뷰 {b['rev_lo']}~{b['rev_hi']}")
    p(f"   출시 후 10개월(M~M+9) {fmt(b['sales10'])}장 = {b['pct10']}%, 첫 12판매월 {fmt(b['sales12'])}장 = {b['pct12']}%,"
      f" ×2 {fmt(b['sales12x2'])}장 = {b['pct12x2']}%")
    p("4단계 현금흐름 (M-2~M+9):")
    for m, s, dep, direct, outs, tax, net, bal in b["cf_rows"]:
        p(f"   {('M' + ('' if m == 0 else f'{m:+d}')):<5} 판매 {s:>4}  입금 {fmt(dep):>10}  환급 {fmt(direct):>8}"
          f"  외주 {fmt(outs):>11}  세금 {fmt(tax):>9}  순 {fmt(net):>11}  잔액 {fmt(bal):>11}")
    p(f"   표 기간 입금 {fmt(b['cf_dep'])} (M~M+8 판매 {fmt(b['cf_dep_units'])}장분), 표 밖 {b['cf_outside_units']}장 "
      f"{fmt(b['cf_outside_dep'])}, 세금 적립 {fmt(b['cf_tax'])}, 말 잔액 {fmt(b['cf_end'])}")
    p(f"6단계(M+3): 잔액 {fmt(b['cf_bal_m3'])}, 전업 월 {fmt(b['ft_month'])}, 런웨이 {b['dec_runway']}, "
      f"최근 3개월 평균 {fmt(b['dec_avg3'])}, 참고 런웨이 {b['dec_ref_runway']}, 누적(환급 포함) {fmt(b['dec_cum3'])},"
      f" 50% {fmt(b['half_need'])}, 저축 목표 {fmt(b['savings_goal'])}")
    p(f"7단계 실측(M~M+2): 평균 판매단가 ${b['m3_asp']:.3f} ({b['m3_asp_ratio']}%), 환불 {b['m3_refund_pct']}%, "
      f"세금 {b['m3_tax_pct']}%, Net ${b['m3_net']:,}, 배분 후 ${b['m3_after_valve']:,}, 원천 ${b['m3_wh']}, "
      f"지급 ${b['m3_usd']:,}, 원화 약 {fmt(int(b['m3_krw']))} → 장당 {fmt(b['U3'])} ({b['U3_pct']:+d}%)")
    p(f"   (이 값을 연간 기준에 잘못 넣으면) 현금 {b['m3_be_cash']}, 인건비 {fmt(b['m3_be_labor'])}, "
      f"생계 {fmt(int(b['m3_be_life']))}, 후보작 {fmt(b['m3_cand'])}")

    p(); p("=" * 70); p("39장 — $7.99 가격 인상 시나리오"); p("=" * 70)
    p(f"12개월 {fmt(c['units'])}장, ${fmt(c['usd'])}, {fmt(c['krw'])}원, 월 {fmt(int(c['monthly']))}, "
      f"장당 {fmt(c['per_krw'])}원 → 필요 {fmt(c['need'])}장, 2년 {fmt(c['units2y'])}장; "
      f"비관 ${fmt(c['pess'])}/{fmt(int(c['pess_krw']))} 낙관 ${fmt(c['opt'])}/{fmt(int(c['opt_krw']))}; "
      f"유지보수 {c['maint_h']}h = {fmt(c['maint_cost'])} = {c['maint_pct']}% "
      f"(모드 전환 문턱 월 {fmt(c['mode_threshold'])}); M1 비중 {c['m1_share']}%")

    p(); p("=" * 70); p("40장 — 두 번째 작품과 24개월"); p("=" * 70)
    p(f"시간: CR 운영 {d['cr_ops']} (M~M+5 {d['cr_ops_early']}, M+6~ {d['cr_ops_late']}), H2 {d['h2_hours']}, "
      f"행정 {d['admin']}, 버퍼 {d['buf']}, 게임 {fmt(d['game_total'])}, 계약 {fmt(d['contract_hours'])}")
    p(f"   H2 출시 전 {d['h2_pre']}h (상한 {d['cap_h']}h), M+5까지 사용 {d['h2_used_before_plan']}h, 남은 {d['remain']}h"
      f" ÷ {H2_DEV_HOURS_MONTH}h = {d['cal_cap_exact']} → 달력 상한 {d['cal_cap']}개월 (M+6~{lab(d['cal_cap_last'])}),"
      f" 실제 누적 도달 {lab(d['fill_m'])}; 착수부터 단순 계산 {d['cal_from_start']}개월")
    p(f"   S3: M+12~M+14 H2 {d['s3_h2_month']}h, 범위 컷 {d['s3_cut']}h → 출시 전 {d['s3_h2_pre']}h")
    p(f"   S2: 개발 +{d['s2_extra_hours']}h → 출시 전 {d['s2_hours']}h, 버퍼 {d['buf']} → {d['s2_buf']}"
      f" ({MINUS}{d['s2_buf_diff']}h)")
    p("   시간표 판정: " + ", ".join(
        f"{k}[출시 {lab(v['launch'])} 전 {v['h2_pre']}h "
        f"{'상한 안' if not v['reapproval'] else '상한 초과→재승인'}]" for k, v in d["H"].items()))
    p(f"필요량: CR 계획 {fmt(d['cr_need_plan'])} / 실측 반영 {fmt(d['cr_actual_total'])} → {fmt(d['cr_need_actual'])} "
      f"(+{fmt(d['cr_need_diff'])}, 운영 +{d['maint_diff_h']}h)")
    p(f"   H2: 외부 현금 {fmt(d['h2_external'])}(외주 {fmt(H2_OUTSOURCE)} + Direct {fmt(DIRECT_FEE_KRW)}, 환급 미차감), "
      f"합계 {fmt(d['h2_req_total'])} ÷ {fmt(d['U2'])} = {fmt(d['h2_need'])} (리뷰 {d['h2_rev_lo']}~{d['h2_rev_hi']}),"
      f" $6.99 {fmt(d['h2_need_699'])} (+{fmt(d['h2_need_699_diff'])}), S2 {d['s2_hours']}h {fmt(d['s2_total'])} → {fmt(d['s2_need'])},"
      f" H2 현금 BE {d['h2_be']}")
    p(f"   CR 24개월 {fmt(d['cr24'])} = 실측 기준 {d['cr24_pct_actual']}% (계획 기준 {d['cr24_pct_plan']}%),"
      f" 첫8 {fmt(d['cr8'])} 나머지 {fmt(d['cr_rest'])} 비율 {d['cr_ratio']}, H2 24개월 추정 {fmt(d['h2_24'])} = {d['h2_24_pct']}%")
    p(f"   출시 달 비중 H2 {d['launch_share_h2']}% vs CR {d['launch_share_cr']}%, H2 8개월/CR 8개월 {d['h2_vs_cr8']}%")
    B = d["S"]["기준"]
    p(f"판정 입력: 말 잔액 {fmt(B['end'])}, 전업 런웨이 {d['runway_ft']}, 계약 없는 런웨이 {d['runway_nc']}, "
      f"최근12 입금 {fmt(B['l12_dep'])} 세금 {fmt(B['l12_tax'])} 게임이 낸 생활비 {fmt(B['l12_paid_living'])} ({B['l12_pct']}%),"
      f" 50% 기준 {fmt(d['half_need'])} 대비 {round(100 * B['l12_dep'] / d['half_need'])}%")
    p(f"   CR M+21~M+23 입금 {d['cr_last3']} 평균 {fmt(d['cr_last3_avg'])}")
    hdr = ("월", "CR", "H2", "계약", "CR입금", "H2입금", "보류$", "환급", "지원금", "외주", "세금", "순현금", "잔액")
    for name, s in d["S"].items():
        p(f"\n[{name}] 최저(M+6~) {fmt(s['min_bal'])} ({lab(s['min_m'])}), 600만 하회 {[lab(m) for m in s['below']]}, "
          f"말 {fmt(s['end'])}, 런웨이 {s['runway_end']}, 게임손익 {won(s['game_pl'])}, H2 판매 {s['h2_total']} "
          f"(입금분 {s['h2_paid_units']}), 환급 도달 {s['reached']}, 판정 {d['verdict'][name]}")
        t = s["tot"]
        p(f"   합계: CR입금 {fmt(t['cr_dep'])} H2입금 {fmt(t['h2_dep'])} 환급 {fmt(t['direct'])} 세금 {fmt(t['tax'])}"
          f" 외주 {fmt(t['outs'])} 계약 {fmt(t['contract'])} 순 {fmt(t['net'])}")
        p(f"   생활비 부담: 게임 {fmt(s['game_living'])} ({100 * s['game_living'] / s['living_total']:.1f}%), "
          f"계약 {fmt(s['contract_share'])} ({100 * s['contract_share'] / s['living_total']:.1f}%), "
          f"저축 인출 {fmt(s['savings_draw'])} ({100 * s['savings_draw'] / s['living_total']:.1f}%), "
          f"게임 입금 합 {fmt(t['cr_dep'] + t['h2_dep'] + t['direct'])}"
          + (f", 사업 적자 {fmt(s['game_deficit'])} (배분과 분리)" if s["game_deficit"] else ""))
        if name in ("기준",) or "--rows" in sys.argv:
            p("   | " + " | ".join(hdr) + " |")
            for x in s["rows"]:
                p("   | " + " | ".join([lab(x["m"])] + [fmt(x[k]) for k in
                    ("cr_sales", "h2_sales", "contract", "cr_dep", "h2_dep", "held_usd", "direct", "grant",
                     "outs", "tax", "net", "bal")]) + " |")
        if "--rows" in sys.argv:
            h = d["H"][name]
            p("   시간표 | 월 | 계약 | CR운영 | H2 | 행정 | 구직 | 버퍼 | 게임계 |")
            for x in h["rows"]:
                p("   | " + " | ".join([lab(x["m"])] + [str(x[k]) for k in
                    ("contract", "cr", "h2", "admin", "job", "buf", "game")]) + " |")


# ════════════════════════════════════════════════════════════════════
# --check : 불변조건 + 기대 위치 안에서의 본문 대조
# ════════════════════════════════════════════════════════════════════

CHECK_SCOPE = "29·34·39·40장 (35장·README 는 검사 대상 아님)"


def invariants():
    """모델 자체의 불변조건. 본문과 무관하게 실패하면 계산이 틀린 것이다."""
    a, b, d, c = R[29], R[34], R[40], R[39]
    fails = []

    def need(cond, msg):
        if not cond:
            fails.append(msg)

    # ① 기간 정의
    need([x[0] for x in b["cf_rows"]] == list(range(CF34_FIRST_MONTH, CF34_LAST_MONTH + 1)),
         "34장 현금흐름표 기간이 M-2~M+9 가 아님")
    for name, s in d["S"].items():
        need([x["m"] for x in s["rows"]] == list(range(MONTHS_24)),
             f"{name}: 40장 현금흐름 기간이 M~M+23 이 아님")
        need(all(s["rows"][m]["h2_sales"] == 0 for m in range(s["launch"])),
             f"{name}: 출시 전 달에 H2 판매가 있음")

    # ② 합계 = 부분합
    for name, s in d["S"].items():
        t = s["tot"]
        for k in ("cr_dep", "h2_dep", "direct", "tax", "outs", "contract", "net"):
            need(t[k] == sum(x[k] for x in s["rows"]), f"{name}: 합계 {k} 가 월별 합과 다름")
        need(s["end"] == CF40_START + t["net"], f"{name}: 말 잔액 ≠ 시작 + 순현금 합")
        ident = (t["cr_dep"] + t["h2_dep"] + t["direct"] + t["tax"] + t["dev"] + t["outs"])
        need(s["game_pl"] == ident, f"{name}: 게임 사업 현금 손익 항등식 불일치")
    need(b["cf_end"] == CF34_START + sum(x[6] for x in b["cf_rows"]), "34장 말 잔액 ≠ 시작 + 순현금 합")

    # ③ 생활비 배분
    for name, s in d["S"].items():
        need(s["game_living"] + s["contract_share"] + s["savings_draw"] == s["living_total"],
             f"{name}: 생활비 배분 합계 ≠ 생활비")
        need(min(s["game_living"], s["contract_share"], s["savings_draw"]) >= 0,
             f"{name}: 생활비 부담액에 음수가 있음")
        need(s["game_living"] <= s["living_total"], f"{name}: 게임 생활비 부담이 생활비를 넘음")
        need(not (s["game_surplus"] < 0 and s["game_living"] > 0),
             f"{name}: 사업 적자인데 게임 생활비 부담이 양수")
    # 극단값에서도 깨지지 않는가 (리뷰가 든 실패 사례)
    for mult in (0.0, 20.0):
        s = scenario(h2_mult=mult)
        need(s["game_living"] + s["contract_share"] + s["savings_draw"] == s["living_total"],
             f"h2_mult={mult}: 생활비 배분 합계 ≠ 생활비")
        need(min(s["game_living"], s["contract_share"], s["savings_draw"]) >= 0,
             f"h2_mult={mult}: 생활비 부담액에 음수가 있음")

    # ④ 잔액 규칙과 판정
    for name, s in d["S"].items():
        after6 = [x for x in s["rows"] if x["m"] >= 6]
        lo = min(x["bal"] for x in after6)
        lo_m = min(x["m"] for x in after6 if x["bal"] == lo)
        need(s["min_bal"] == lo and s["min_m"] == lo_m, f"{name}: 최저 잔액·최저 시점 재계산 불일치")
        need(s["below"] == [x["m"] for x in s["rows"] if x["bal"] < EMERGENCY_FLOOR],
             f"{name}: 비상금 하회 달 목록 불일치")
        need(d["verdict"][name] == SCENARIO_VERDICT[name],
             f"{name}: 판정 {d['verdict'][name]} ≠ 본문 판정 {SCENARIO_VERDICT[name]}")
        if SCENARIO_VERDICT[name] == "C2":
            need(bool(s["below"]) or s["runway_end"] < MIN_RUNWAY_MONTHS,
                 f"{name}: C2 인데 잔액·런웨이 조건 어느 것도 걸리지 않음")
        if SCENARIO_VERDICT[name] in ("B", "A1", "A2"):
            need(not s["below"] and s["game_pl"] >= 0 and s["h2_total"] >= d["h2_be"],
                 f"{name}: B 판정인데 C 조건에 걸림")

    # ⑤ 입금 규칙
    for name, s in d["S"].items():
        for i, x in enumerate(s["rows"]):
            if x["held_usd"] > 0:
                need(x["cr_dep"] == 0 and x["h2_dep"] == 0 and x["direct"] == 0,
                     f"{name} {lab(x['m'])}: 지급 보류 달에 입금이 있음")
        reached_in = [m for m in s["reached"].values() if m is not None and m + 1 < MONTHS_24]
        need(s["tot"]["direct"] == DIRECT_FEE_KRW * len(reached_in),
             f"{name}: Direct 환급 건수가 도달 앱 수와 다름")
        if reached_in:
            first = min(reached_in)
            need(all(s["rows"][k]["direct"] == 0 for k in range(0, first + 1)),
                 f"{name}: 환급이 조정 총매출 $1,000 도달 달 이전에 들어옴")

    # ⑥ 시간표
    for name, h in d["H"].items():
        for x in h["rows"]:
            cap = GAME_HOURS_MONTH - (REST_WEEK_HOURS if x["m"] == 1 else 0)
            need(x["budget"] == cap,
                 f"{name} {lab(x['m'])}: 게임 예산 합계 {x['budget']}h ≠ {cap}h (달력 상한 위반)")
            need(min(x["cr"], x["h2"], x["admin"], x["buf"], x["job"]) >= 0,
                 f"{name} {lab(x['m'])}: 시간표에 음수 칸이 있음")
        need(h["tot"]["budget"] == GAME_HOURS_MONTH * MONTHS_24 - REST_WEEK_HOURS,
             f"{name}: 24개월 게임 예산 합계 불일치")
        need(h["tot"]["contract"] == CONTRACT_HOURS_MONTH * (MONTHS_24 - len(h["contract_off"])),
             f"{name}: 계약 근무 시간 합계 불일치")
        expect_reapproval = name in ("S2", "S5")
        need(h["reapproval"] == expect_reapproval,
             f"{name}: 시간 상한 판정(재승인 필요={h['reapproval']})이 본문 서술과 다름")
        need(h["launch"] == d["S"][name]["launch"], f"{name}: 시간표와 현금표의 출시 월이 다름")
        need(h["contract_off"] == d["S"][name]["contract_off"],
             f"{name}: 시간표와 현금표의 계약 중단 달이 다름")

    # 공통 가정이 파생값으로 이어지는가
    need(b["maint_h"] == MAINT_HOURS_PER_YEAR_PLAN * MAINT_PLAN_YEARS, "34장 유지보수 시간이 공통 가정과 다름")
    need(c["maint_h"] == MAINT_HOURS_PER_YEAR_PLAN, "39장 유지보수 시간이 공통 가정과 다름")
    need(H2_DEV_HOURS_MONTH == GAME_HOURS_MONTH - MAINT_ACTIVE_HOURS_MONTH - ADMIN_HOURS_MONTH,
         "월 가용 개발시간이 공통 가정과 다름")
    need(d["h2_external"] == H2_OUTSOURCE + DIRECT_FEE_KRW, "H2 외부 현금 비용에 Direct 가 빠짐")
    need(abs(b["avg_example_weighted"] - b["avg_example_true"]) < 1e-9,
         "매출액 가중 할인율이 총매출을 재구성하지 못함 (34장 연습 4 해설의 근거)")
    return fails


def _sections(text):
    """코드 펜스를 존중하며 Markdown 을 (제목, 본문) 으로 쪼갠다."""
    out, head, buf, fence = [], "(문서 머리)", [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and re.match(r"^#{1,6} ", line):
            out.append((head, "\n".join(buf)))
            head, buf = line.lstrip("#").strip(), []
        else:
            buf.append(line)
    out.append((head, "\n".join(buf)))
    return out


def checks():
    """(파일, 절 제목 일부|None, 행 정규식|None, [값...]) — 값은 그 문맥 '안에서만' 찾는다.

    절 제목이 None 이면 파일 전체, 행 정규식이 None 이면 절 전체가 문맥이다.
    같은 값이 다른 절·다른 행에 있어도 통과하지 않는다.
    """
    a, b, d, c = R[29], R[34], R[40], R[39]
    S = d["S"]; B = S["기준"]
    n = lambda v: fmt(int(v))
    P29 = "5단계 — 코인 러시 가상 포스트모템"    # 29장 포스트모템은 통째로 코드 블록이라 행으로 좁힌다
    ST4 = "4단계 — 스트레스 테스트 4종"
    return [
        # ── 29장 (30일 정산·손익) ────────────────────────────────
        ("29_scope-postmortem.md", None, None, ["coin_rush_model.py"]),
        ("29_scope-postmortem.md", P29, r"Steam 리포트 총매출", [n(a["gross"])]),
        ("29_scope-postmortem.md", P29, r"환불 7%", [n(a["after_refund"])]),
        ("29_scope-postmortem.md", P29, r"판매세·VAT", [n(a["net"])]),
        ("29_scope-postmortem.md", P29, r"Valve 수수료 30%", [n(a["after_valve"])]),
        ("29_scope-postmortem.md", P29, r"미국 원천징수", [n(a["after_wh"])]),
        ("29_scope-postmortem.md", P29, r"해외 송금 수수료", [n(a["usd_final"])]),
        ("29_scope-postmortem.md", P29, r"입금일 환율", [n(a["krw"])]),
        ("29_scope-postmortem.md", P29, r"장당 순수입", [n(a["per"]), n(a["list_krw"]), n(a["per_ex_refund"])]),
        ("29_scope-postmortem.md", P29, r"34장의 장당", [n(b["U"])]),
        ("29_scope-postmortem.md", P29, r"^\| 외부 비용", [n(CR_EXTERNAL)]),
        ("29_scope-postmortem.md", P29, r"개발자 시간", [n(a["time_cost"]), n(CR_HOURS) + "h"]),
        ("29_scope-postmortem.md", P29, r"\*\*현금 손익\*\*", [won(a["cash_pl"])]),
        ("29_scope-postmortem.md", P29, r"시간 비용 포함 손익", [won(a["time_pl"])]),
        ("29_scope-postmortem.md", P29, r"현금 기준:", [n(a["be_cash"]) + "장", f"{a['pct_cash']}%"]),
        ("29_scope-postmortem.md", P29, r"시간 비용 포함:", [n(a["be_time"]) + "장"]),

        # ── 34장 ────────────────────────────────────────────────
        ("34_livelihood-math.md", None, None, ["coin_rush_model.py"]),
        ("34_livelihood-math.md", "1단계 — 생활비 역산표", None,
         [n(b["after_tax_need"]), n(b["income_need"]), n(b["revenue_need"])]),
        ("34_livelihood-math.md", "2단계 — 장당 순수입 계산표", None,
         ["₩" + n(b["U"]), f"{b['usd_ratio']}%", n(b["sens"]["fx_low"]), n(b["sens"]["fx_high"]),
          n(b["sens"]["wh_all"]), n(b["sens"]["disc40"]), n(b["sens"]["p699"]),
          f"${b['avg_example_true']:.2f}", f"${b['avg_example_wrong']:.2f}"]),
        ("34_livelihood-math.md", "3단계 — 손익분기표", None,
         [n(b["be_cash"]) + "장", n(b["labor_total"]), n(b["be_labor"]) + "장",
          n(b["be_life"]) + "장", n(b["direct_recoup_units"]) + "장"]),
        ("34_livelihood-math.md", "3-1단계 — 생계 후보작 승인 계산", None,
         [n(b["maint_cost"]), n(b["cand_total"]), n(b["cand_need"]) + "장",
          f"{b['rev_lo']}~{b['rev_hi']}", n(b["sales10"]) + "장", n(b["sales12"]) + "장",
          f"약 {b['pct10']}%", n(b["sales12x2"]) + "장", n(d["cr_need_actual"]),
          f"{MAINT_HOURS_PER_YEAR_PLAN}h/년", f"{b['maint_h']}h"]),
        ("34_livelihood-math.md", "4단계 — 월별 현금흐름표", r"^\| M\+9", [n(b["cf_end"])]),
        ("34_livelihood-math.md", "4단계 — 월별 현금흐름표", r"^\| M\+3", [n(b["cf_bal_m3"])]),
        ("34_livelihood-math.md", "4단계 — 월별 현금흐름표", None,
         [n(b["cf_dep"]), n(b["cf_outside_dep"])]),
        ("34_livelihood-math.md", "6단계 — 전업 전환 판정 문서", None,
         [n(b["cf_bal_m3"]), n(b["dec_avg3"]), n(b["half_need"])]),
        ("34_livelihood-math.md", "7단계 — 첫 3개월 정산 리포트", None,
         [f"${b['m3_asp']:.3f}", n(b["U3"]), n(b["m3_be_cash"]) + "장", n(b["m3_be_labor"]) + "장",
          n(b["m3_be_life"]) + "장", n(b["m3_cand"]) + "장"]),
        ("34_livelihood-math.md", "연습 문제", None, [f"${b['avg_example_weighted']:.2f}"]),

        # ── 39장 ────────────────────────────────────────────────
        ("39_after-launch-year.md", None, None, ["coin_rush_model.py"]),
        ("39_after-launch-year.md", "1단계: 30일 데이터로 12개월 매출 시나리오", None,
         [n(c["units"]), n(c["usd"]), n(c["per_krw"]), n(c["need"]) + "장", n(c["units2y"]) + "장",
          n(c["pess"]), n(c["opt"]), f"{c['m1_share']}%", n(b["sales10"]) + "장",
          n(b["sales12"]) + "장", n(b["cand_need"])]),
        ("39_after-launch-year.md", "5단계: 유지보수 예산표", r"\*\*합계\*\*",
         [f"**{c['maint_month']}**", f"**{c['maint_h']}**", n(c["maint_cost"])]),
        ("39_after-launch-year.md", "5단계: 유지보수 예산표", None,
         [f"{c['maint_pct']}%", n(c["mode_threshold"])]),

        # ── 40장 ────────────────────────────────────────────────
        ("40_second-game-24months.md", None, None, ["coin_rush_model.py"]),
        ("40_second-game-24months.md", "2단계 — 24개월 작업시간표", r"^\| \*\*24개월 합계\*\*",
         [n(d["contract_hours"]), n(d["cr_ops"]), n(d["h2_hours"]), n(d["admin"]), n(d["buf"]),
          n(d["game_total"])]),
        ("40_second-game-24months.md", "2단계 — 24개월 작업시간표", None,
         [n(d["h2_pre"]) + "h", n(d["remain"]) + "h", f"{d['cal_cap']}개월", n(d["s3_h2_pre"]) + "h",
          n(d["s3_cut"]) + "h", n(d["cr_ops"]), f"{d['s3_h2_month']}**"]),
        ("40_second-game-24months.md", "3단계 — 24개월 합산 현금흐름표", r"^\| \*\*합계\*\*",
         [n(B["tot"]["cr_dep"]), n(B["tot"]["h2_dep"]), won(B["tot"]["tax"]), n(B["tot"]["net"]),
          n(d["cr24"]), n(B["h2_total"])]),
        ("40_second-game-24months.md", "3단계 — 24개월 합산 현금흐름표", r"^\| M\+23", [n(B["end"])]),
        ("40_second-game-24months.md", "3단계 — 24개월 합산 현금흐름표", r"^\| M\+6 ", [n(B["min_bal"])]),
        ("40_second-game-24months.md", ST4, r"^\| 기준 ",
         [n(B["min_bal"]), n(B["end"]), won_pm(B["game_pl"]), n(B["h2_total"])]),
        ("40_second-game-24months.md", ST4, r"^\| S1 ",
         [n(S["S1"]["min_bal"]), n(S["S1"]["end"]), won_pm(S["S1"]["game_pl"]),
          n(S["S1"]["h2_total"]), n(d["h2_be"])]),
        ("40_second-game-24months.md", ST4, r"^\| S2 ",
         [n(S["S2"]["min_bal"]), n(S["S2"]["end"]), won_pm(S["S2"]["game_pl"]), n(S["S2"]["h2_total"])]),
        ("40_second-game-24months.md", ST4, r"^\| S3 ",
         [n(S["S3"]["min_bal"]), n(S["S3"]["end"]), won_pm(S["S3"]["game_pl"])]),
        ("40_second-game-24months.md", ST4, r"^\| S4 ",
         [n(S["S4"]["min_bal"]), n(S["S4"]["end"]), won_pm(S["S4"]["game_pl"])]),
        ("40_second-game-24months.md", ST4, r"^ *기준 *=",
         [won_pm(B["game_pl"]), n(abs(B["tot"]["tax"]))]),
        ("40_second-game-24months.md", ST4, r"^ *S1 *=",
         [won_pm(S["S1"]["game_pl"]), n(S["S1"]["tot"]["h2_dep"]), n(abs(S["S1"]["tot"]["tax"]))]),
        ("40_second-game-24months.md", ST4, r"^ *S2 *=",
         [won_pm(S["S2"]["game_pl"]), n(S["S2"]["tot"]["h2_dep"]), n(abs(S["S2"]["tot"]["tax"]))]),
        ("40_second-game-24months.md", ST4, None,
         [n(d["h2_be"]) + "장", n(d["h2_external"]), n(d["s2_hours"]) + "h", n(d["s2_total"]),
          n(d["s2_need"]), n(d["h2_need"]), n(d["s2_extra_hours"]) + "h",
          f"**{d['s2_buf']}h**", n(S["S4"]["min_bal"])]),
        # 2단계 시나리오별 시간표 요약 (현금 설정과 같은 설정으로 계산한 값)
        ("40_second-game-24months.md", "2단계 — 24개월 작업시간표", r"^\| 기준 · S1",
         [n(d["h2_pre"]) + "h", n(d["buf"]) + "h"]),
        ("40_second-game-24months.md", "2단계 — 24개월 작업시간표", r"^\| S2 · S5",
         [n(d["s2_hours"]) + "h", f"**{d['s2_buf']}h**"]),
        ("40_second-game-24months.md", "2단계 — 24개월 작업시간표", r"^\| S3 · S4",
         [n(d["s3_h2_pre"]) + "h", n(d["s3_cut"]) + "h", n(d["buf"]) + "h"]),
        ("40_second-game-24months.md", "5단계 — 수입원 분리와 생활비 부담표", r"^\| 게임 판매 \(CR 입금",
         [n(B["game_living"]), f"{100 * B['game_living'] / B['living_total']:.1f}%",
          n(B["tot"]["cr_dep"]), n(B["tot"]["h2_dep"]), won(B["tot"]["tax"])]),
        ("40_second-game-24months.md", "5단계 — 수입원 분리와 생활비 부담표", r"^\| 외주·계약 \(React",
         [n(B["contract_share"]), f"{100 * B['contract_share'] / B['living_total']:.1f}%"]),
        ("40_second-game-24months.md", "5단계 — 수입원 분리와 생활비 부담표", r"^\| 게임 판매 \(입금",
         [n(S["S4"]["game_living"])]),
        ("40_second-game-24months.md", "5단계 — 수입원 분리와 생활비 부담표", r"^\| \*\*저축 인출\*\*",
         [n(S["S4"]["savings_draw"])]),
        ("40_second-game-24months.md", "5단계 — 수입원 분리와 생활비 부담표", r"참고\) 지원금 제외",
         [won_pm(S["S4"]["game_pl"])]),
        ("40_second-game-24months.md", "5단계 — 수입원 분리와 생활비 부담표", None,
         [n(d["grant_hourly"]), n(B["game_pl"])]),
        ("40_second-game-24months.md", "6단계 — 24개월 종료 판정 문서", None,
         [n(B["end"]), f"{d['runway_ft']}개월", f"{d['runway_nc']}개월", n(B["l12_dep"]),
          n(B["l12_paid_living"]), f"{B['l12_pct']}%", won_pm(B["game_pl"]), n(d["cr_actual_total"]),
          n(d["cr_need_plan"]) + "장", n(d["cr_need_actual"]) + "장", n(d["cr_need_diff"]) + "장",
          n(d["h2_req_total"]), n(d["h2_need"]) + "장", f"{d['h2_rev_lo']}~{d['h2_rev_hi']}",
          n(d["h2_24"]), f"{d['cr24_pct_actual']}%", f"{d['h2_24_pct']}%", n(d["h2_be"]) + "장",
          n(d["half_need"]), n(B["min_bal"]), n(d["cr_last3_avg"])]),
        ("40_second-game-24months.md", "연습 문제", None,
         [n(d["h2_need_699"]) + "장", n(d["h2_need"])]),
        ("40_second-game-24months.md", "셀프 체크", None,
         [f"{100 * B['game_living'] / B['living_total']:.1f}%",
          f"{100 * B['contract_share'] / B['living_total']:.1f}%"]),
    ]


def run_check():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    print(f"검사 범위: {CHECK_SCOPE}")
    print("검사 1 — 불변조건 (기간 정의·합계=부분합·생활비 배분·잔액/판정·입금 규칙·시간표)")
    fails = invariants()
    for f in fails:
        print(f"  ✗ {f}")
    print(f"  {'OK' if not fails else '실패 ' + str(len(fails)) + '건'}")

    print("검사 2 — 본문 대조 (값마다 지정한 절/행 문맥 안에서만 탐색, 부호 포함)")
    cache = {}
    missing, total, byfile = [], 0, {}
    for fname, sec, row, needles in checks():
        if fname not in cache:
            text = open(os.path.join(root, fname), encoding="utf-8").read()
            cache[fname] = (text, _sections(text))
        text, secs = cache[fname]
        if sec is None:
            bodies = [text]
        else:
            bodies = [body for head, body in secs if sec in head]
            if not bodies:
                missing.append((fname, sec, row, f"(절 '{sec}' 을 찾지 못함)"))
                continue
        lines = "\n".join(bodies).splitlines()
        if row:
            lines = [ln for ln in lines if re.search(row, ln)]
            if not lines:
                missing.append((fname, sec, row, "(행 정규식에 맞는 줄이 없음)"))
                continue
        ctx = "\n".join(lines)
        for s in needles:
            total += 1
            byfile[fname] = byfile.get(fname, 0) + 1
            if s not in ctx:
                where = "문맥 밖에 존재" if s in text else "본문에 없음"
                missing.append((fname, sec, row, f"{s}  ← {where}"))
    if missing:
        print(f"  ✗ 불일치 {len(missing)}/{total}건:")
        for f, sec, row, s in missing:
            print(f"    {f} › {sec or '(파일 전체)'}{' › ' + row if row else ''}: {s}")
    else:
        print(f"  OK — {total}개 수치가 지정한 문맥 안에 있습니다 "
              + ", ".join(f"{k.split('_')[0]}장 {v}" for k, v in sorted(byfile.items())))
    if fails or missing:
        sys.exit(1)


def main():
    ch29(); ch34(); ch39(); ch40()
    if "--check" in sys.argv:
        run_check()
        return
    report()


if __name__ == "__main__":
    main()
