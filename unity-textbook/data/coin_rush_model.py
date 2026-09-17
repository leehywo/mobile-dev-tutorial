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
  python3 unity-textbook/data/coin_rush_model.py --check    # 핵심 수치가 장 본문에 있는지 검사 (누락 시 exit 1)

규칙
  1. 수치를 바꿀 땐 여기(가정 블록)에서 바꾼다. Markdown 을 먼저 고치지 않는다.
  2. 실행 결과를 보고 해당 장의 표·본문·연습 해설·요약을 고친다.
  3. --check 가 통과할 때까지 장 본문을 맞춘다. 새 사례 수치를 본문에 넣으면 CHECKS 에도 추가한다.
  4. 반올림 규칙: 손익분기 판매량은 올림(그만큼 팔아야 회수), "약 N장" 근사는 반올림.
     원화 입금액은 '판매량 × 반올림한 장당 입금액'(스프레드시트 수식과 같은 방식).

용어
  M          = 코인 러시(CR) 출시 달. M+n 은 n개월 뒤.
  판매 발생월 = 판매가 일어난 달. 입금은 다음 달(Steam 월 정산).
  조정 총매출 = 총매출 − 환불·차지백 − 가격 포함 세금 (Steam Direct 환급 기준에 쓰는 값).
"""
import math
import os
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

# ── 34장 3-1단계: 생계 후보작 (착수 전 계획) ──
MAINT_HOURS_PER_YEAR_PLAN = 184   # 39장 유지보수 예산표 (출시 직후 운영 노동 미포함)
NEXT_GAME_FUND = 1_500_000        # 월 250,000 × 6개월

# ── 34장 4단계 / 40장 3단계 현금흐름 ──
CONTRACT_INCOME = 2_400_000
CF_LIVING = 2_300_000
CF_DEV = 250_000
CF34_START = 12_300_000           # M-2 시작 잔액
CF34_PRELAUNCH_OUTS = {-2: 1_200_000, -1: 600_000, 0: 300_000}
# CR 월 판매 가정 곡선 (M ~ M+23). 34장 표는 M~M+9, 40장 표는 전체
CR_CURVE = [610, 180, 120, 260, 90, 80, 200, 70, 60, 240,
            50, 45, 150, 40, 35, 150, 35, 30, 120, 30, 25, 140, 25, 20]
CR_SALE_MONTHS = {3: "여름 세일", 6: "가을 세일", 9: "겨울 세일", 12: "봄 세일",
                  15: "여름 세일", 18: "가을 세일", 21: "겨울 세일"}

# ── 40장: 두 번째 작품 H2 「랜턴 런」 ──
H2_PRICE = 7.99
H2_CURVE = [700, 150, 220, 90, 70, 200, 60, 50]   # 출시 달부터
H2_LAUNCH = 16
H2_OUTSOURCE = 3_000_000          # 지원금으로 집행
H2_DIRECT_PAY_MONTH = 9
GRANTS = {11: 1_000_000, 13: 1_000_000, 15: 1_000_000}
CF40_START = 10_200_000           # M-1 말
H2_PRELAUNCH_CAP_FACTOR = 1.5
GAME_HOURS_MONTH = 80             # 주 20h × 48주 ÷ 12
CONTRACT_HOURS_MONTH = 104
H2_DEV_HOURS_MONTH = 58           # 80 − 기존작 운영 14 − 행정 8 (버퍼 제외)
JOB_SEARCH_HOURS = 20             # S3 구직 시간/월

# 24개월 작업시간표 (CR 운영, H2, 행정, 버퍼·다음 가설)
HOURS = {0: (60, 0, 10, 10), 1: (40, 10, 10, 0)}
for _m in range(2, 6):
    HOURS[_m] = (30, 30, 8, 12)
for _m in range(6, 15):
    HOURS[_m] = (14, 58, 8, 0)
HOURS[11] = (30, 42, 8, 0)
HOURS[15] = (14, 34, 8, 24)
HOURS[16] = (6, 66, 8, 0)
HOURS[17] = (14, 40, 8, 18)
for _m in range(18, 24):
    HOURS[_m] = (14, 16, 8, 42)
HOURS[23] = (30, 16, 8, 26)

# 스트레스 테스트 설정
SCENARIOS = {
    "기준": dict(),
    "S1": dict(h2_mult=0.3),
    "S2": dict(launch=19, extra_outs={17: 500_000}),
    "S3": dict(contract_off=(15, 16, 17)),
    "S4": dict(h2_mult=0.3, contract_off=(15, 16, 17)),
    "S5": dict(launch=19, extra_outs={17: 500_000}, contract_off=(15, 16, 17)),
}
S2_EXTRA_HOURS = 58 * 3
S2_EXTRA_OUTSOURCE = 500_000

# ── 39장 ($7.99 가격 인상 시나리오, 운영 계획용 어림) ──
Y39_UNITS = [610, 380, 150, 260, 230, 80, 200, 210, 120, 60, 55, 170]
Y39_NET_USD = [2196, 1140, 480, 806, 713, 312, 620, 630, 384, 234, 215, 510]
Y39_WAGE = 40_000

# ════════════════════════════════════════════════════════════════════
# 계산
# ════════════════════════════════════════════════════════════════════

def ceil(x):
    return math.ceil(x - 1e-9)


def fmt(n):
    return f"{n:,}"


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
    # 평균의 곱 경고 예시
    r["avg_example_true"] = 10 * 1.0 + 5 * 0.5
    r["avg_example_wrong"] = 2 * 10 * 0.75 * 0.75
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

    # 3-1단계 생계 후보작 (착수 전 계획: 유지보수 184h/년 × 2)
    maint_h = MAINT_HOURS_PER_YEAR_PLAN * 2
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
    for m in range(-2, 10):
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
             cf_bal_m3=[x for x in rows if x[0] == 3][0][-1])
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


def scenario(h2_mult=1.0, launch=H2_LAUNCH, contract_off=(), extra_outs=None):
    """40장 24개월 합산 현금흐름. 지급 보류·Direct 환급 규칙 반영."""
    extra_outs = extra_outs or {}
    U1 = R[34]["U"]
    U2 = round(R[34]["U_exact"] * H2_PRICE / CR_PRICE)
    usd1 = payout_usd_per_unit(CR_PRICE)
    usd2 = payout_usd_per_unit(H2_PRICE)
    agr1 = unit_usd(CR_PRICE)[1]
    agr2 = unit_usd(H2_PRICE)[1]
    N = 24
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
    game_pl = tot["cr_dep"] + tot["h2_dep"] + tot["direct"] + tot["tax"] + tot["dev"] + tot["outs"]
    after6 = [r for r in rows if r["m"] >= 6]
    mn = min(after6, key=lambda r: r["bal"])
    below = [r["m"] for r in rows if r["bal"] < EMERGENCY_FLOOR]
    last12 = [r for r in rows if r["m"] >= 12]
    l12_dep = sum(r["cr_dep"] + r["h2_dep"] + r["direct"] for r in last12)
    l12_tax = -sum(r["tax"] for r in last12)
    l12_dev = -sum(r["dev"] for r in last12)
    l12_outs_nongrant = -sum(r["outs"] for r in last12) - sum(GRANTS[m] for m in GRANTS if m >= 12)
    l12_paid_living = l12_dep - l12_tax - l12_dev - l12_outs_nongrant
    outs_nongrant = -tot["outs"] - sum(GRANTS.values())
    game_living = tot["cr_dep"] + tot["h2_dep"] + tot["direct"] + tot["tax"] + tot["dev"] - outs_nongrant
    living_total = -tot["living"]
    contract_share = min(tot["contract"], living_total - max(game_living, 0))
    savings_draw = living_total - max(game_living, 0) - contract_share
    # H2 창 안 입금 판매량
    h2_paid_units = tot["h2_dep"] // U2
    return dict(rows=rows, tot=tot, game_pl=game_pl, min_bal=mn["bal"], min_m=mn["m"],
                below=below, end=rows[-1]["bal"], runway_end=round(rows[-1]["bal"] / (CF_LIVING + CF_DEV), 1),
                h2_total=sum(h2), h2_paid_units=h2_paid_units, reached=dict(reached),
                l12_dep=l12_dep, l12_tax=l12_tax, l12_paid_living=l12_paid_living,
                l12_pct=round(100 * l12_paid_living / (CF_LIVING * 12), 1),
                game_living=game_living, contract_share=contract_share, savings_draw=savings_draw,
                living_total=living_total, U2=U2, outs_nongrant=outs_nongrant)


def lab(m):
    return "M" if m == 0 else f"M+{m}"


def ch40():
    r = {}
    U1 = R[34]["U"]
    S = {k: scenario(**v) for k, v in SCENARIOS.items()}
    B = S["기준"]
    U2 = B["U2"]
    r.update(S=S, U2=U2)

    # 시간
    cols = list(zip(*[HOURS[m] for m in range(24)]))
    cr_ops, h2_h, admin, buf = [sum(c) for c in cols]
    h2_pre = sum(HOURS[m][1] for m in range(0, H2_LAUNCH))
    h2_used_before_plan = sum(HOURS[m][1] for m in range(0, 6))
    cap_h = int(round(CR_HOURS * H2_PRELAUNCH_CAP_FACTOR, -1))   # 667.5 → 670h
    remain = cap_h - h2_used_before_plan
    cal_cap = ceil(remain / H2_DEV_HOURS_MONTH)
    # 실제 누적으로 남은 시간을 채우는 달
    acc, fill_m = 0, None
    for m in range(6, 24):
        acc += HOURS[m][1]
        if acc >= remain:
            fill_m = m
            break
    r.update(cr_ops=cr_ops, h2_hours=h2_h, admin=admin, buf=buf, game_total=cr_ops + h2_h + admin + buf,
             cr_ops_early=sum(HOURS[m][0] for m in range(0, 6)), cr_ops_late=sum(HOURS[m][0] for m in range(6, 24)),
             h2_pre=h2_pre, h2_launch_month=HOURS[H2_LAUNCH][1], cap_h=cap_h,
             h2_used_before_plan=h2_used_before_plan, remain=remain,
             cal_cap_exact=round(remain / H2_DEV_HOURS_MONTH, 1), cal_cap=cal_cap,
             cal_cap_last=6 + cal_cap - 1, fill_m=fill_m,
             cal_from_start=round(cap_h / H2_DEV_HOURS_MONTH, 1))
    # S3 수정 시간표: M+12~M+14 구직 20h 를 H2 개발에서 가져옴 → 범위 컷
    s3_cut = JOB_SEARCH_HOURS * 3
    r.update(s3_h2_month=HOURS[12][1] - JOB_SEARCH_HOURS, s3_cut=s3_cut, s3_h2_pre=h2_pre - s3_cut)

    # 생계 후보작 필요량
    plan_total = R[34]["cand_total"]
    actual_total = CR_EXTERNAL + CR_HOURS * WAGE + cr_ops * WAGE + NEXT_GAME_FUND
    cr_need_plan = R[34]["cand_need"]
    cr_need_actual = round(actual_total / U1)
    h2_total_req = H2_OUTSOURCE + h2_pre * WAGE + cr_ops * WAGE + NEXT_GAME_FUND
    h2_need = round(h2_total_req / U2)
    s2_total = H2_OUTSOURCE + S2_EXTRA_OUTSOURCE + (h2_pre + S2_EXTRA_HOURS) * WAGE + cr_ops * WAGE + NEXT_GAME_FUND
    U699 = R[34]["sens"]["p699"]
    r.update(cr_actual_total=actual_total, cr_need_plan=cr_need_plan, cr_need_actual=cr_need_actual,
             cr_need_diff=cr_need_actual - cr_need_plan, maint_diff_h=cr_ops - R[34]["maint_h"],
             h2_req_total=h2_total_req, h2_need=h2_need,
             h2_rev_lo=round(h2_need / 60), h2_rev_hi=round(h2_need / 20),
             s2_hours=h2_pre + S2_EXTRA_HOURS, s2_total=s2_total, s2_need=round(s2_total / U2),
             h2_need_699=round(h2_total_req / U699), h2_need_699_diff=round(h2_total_req / U699) - h2_need,
             h2_be=ceil(H2_OUTSOURCE / U2))
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
    r.update(units=units, usd=usd, krw=krw, monthly=round(krw / 12, -3), per_krw=per_krw,
             need=round(R[34]["cand_total"] / per_krw), units2y=units * 2,
             pess=round(Y39_NET_USD[0] + rest * 0.6), opt=round(Y39_NET_USD[0] + rest * 1.6),
             pess_krw=round((Y39_NET_USD[0] + rest * 0.6) * FX_PLAN, -4),
             opt_krw=round((Y39_NET_USD[0] + rest * 1.6) * FX_PLAN, -4),
             maint_cost=184 * Y39_WAGE, maint_pct=round(100 * 184 * Y39_WAGE / krw),
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
    p(f"현금 손익 {fmt(a['cash_pl'])} / 시간 비용 {fmt(a['time_cost'])} / 시간 포함 {fmt(a['time_pl'])}")
    p(f"손익분기(환급 차감): 현금 {a['be_cash']}장 ({a['pct_cash']}%), 시간 포함 {fmt(a['be_time'])}장 ({a['pct_time']}%)")

    p(); p("=" * 70); p("34장 — 생계 수학"); p("=" * 70)
    p(f"1단계: 연 세후 필요액 {fmt(b['after_tax_need'])}, 세금 {fmt(b['income_tax'])}, "
      f"사업소득 {fmt(b['income_need'])}, 연 필요 매출 {fmt(b['revenue_need'])}")
    p("2단계 장당(계획):")
    for name, v in b["steps"]:
        p(f"   {name:<16} {v:,.3f}")
    p(f"   → 장당 ₩{fmt(b['U'])} (정확값 {b['U_exact']:.4f}), 달러 입금 비율 {b['usd_ratio']}%, "
      f"조정 총매출/장 ${b['agr']:.4f}, Direct 환급 도달 {b['direct_recoup_units']}장")
    p(f"   평균의 곱 경고 예: 실제 ${b['avg_example_true']:.2f} vs 분해 곱 ${b['avg_example_wrong']:.2f}")
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
      f"유지보수 {fmt(c['maint_cost'])} = {c['maint_pct']}%; M1 비중 {c['m1_share']}%")

    p(); p("=" * 70); p("40장 — 두 번째 작품과 24개월"); p("=" * 70)
    p(f"시간: CR 운영 {d['cr_ops']} (M~M+5 {d['cr_ops_early']}, M+6~ {d['cr_ops_late']}), H2 {d['h2_hours']}, "
      f"행정 {d['admin']}, 버퍼 {d['buf']}, 게임 {fmt(d['game_total'])}")
    p(f"   H2 출시 전 {d['h2_pre']}h (상한 {d['cap_h']}h), M+5까지 사용 {d['h2_used_before_plan']}h, 남은 {d['remain']}h"
      f" ÷ {H2_DEV_HOURS_MONTH}h = {d['cal_cap_exact']} → 달력 상한 {d['cal_cap']}개월 (M+6~{lab(d['cal_cap_last'])}),"
      f" 실제 누적 도달 {lab(d['fill_m'])}; 착수부터 단순 계산 {d['cal_from_start']}개월")
    p(f"   S3: M+12~M+14 H2 {d['s3_h2_month']}h, 범위 컷 {d['s3_cut']}h → 출시 전 {d['s3_h2_pre']}h")
    p(f"필요량: CR 계획 {fmt(d['cr_need_plan'])} / 실측 반영 {fmt(d['cr_actual_total'])} → {fmt(d['cr_need_actual'])} "
      f"(+{fmt(d['cr_need_diff'])}, 운영 +{d['maint_diff_h']}h)")
    p(f"   H2: {fmt(d['h2_req_total'])} ÷ {fmt(d['U2'])} = {fmt(d['h2_need'])} (리뷰 {d['h2_rev_lo']}~{d['h2_rev_hi']}),"
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
          f"말 {fmt(s['end'])}, 런웨이 {s['runway_end']}, 게임손익 {fmt(s['game_pl'])}, H2 판매 {s['h2_total']} "
          f"(입금분 {s['h2_paid_units']}), 환급 도달 {s['reached']}")
        t = s["tot"]
        p(f"   합계: CR입금 {fmt(t['cr_dep'])} H2입금 {fmt(t['h2_dep'])} 환급 {fmt(t['direct'])} 세금 {fmt(t['tax'])}"
          f" 외주 {fmt(t['outs'])} 계약 {fmt(t['contract'])} 순 {fmt(t['net'])}")
        p(f"   생활비 부담: 게임 {fmt(s['game_living'])} ({100 * s['game_living'] / s['living_total']:.1f}%), "
          f"계약 {fmt(s['contract_share'])} ({100 * s['contract_share'] / s['living_total']:.1f}%), "
          f"저축 인출 {fmt(s['savings_draw'])} ({100 * s['savings_draw'] / s['living_total']:.1f}%), "
          f"게임 입금 합 {fmt(t['cr_dep'] + t['h2_dep'] + t['direct'])}")
        if name in ("기준",) or "--rows" in sys.argv:
            p("   | " + " | ".join(hdr) + " |")
            for x in s["rows"]:
                p("   | " + " | ".join([lab(x["m"])] + [fmt(x[k]) for k in
                    ("cr_sales", "h2_sales", "contract", "cr_dep", "h2_dep", "held_usd", "direct", "grant",
                     "outs", "tax", "net", "bal")]) + " |")


# ════════════════════════════════════════════════════════════════════
# --check : 핵심 수치가 장 본문에 있는지
# ════════════════════════════════════════════════════════════════════

def checks():
    a, b, d, c = R[29], R[34], R[40], R[39]
    S = d["S"]; B = S["기준"]
    n = lambda v: fmt(int(v))
    return {
        "29_scope-postmortem.md": [
            n(a["gross"]), n(a["after_refund"]), n(a["net"]), n(a["after_valve"]), n(a["after_wh"]),
            n(a["usd_final"]), n(a["krw"]), n(a["per"]), n(a["per_ex_refund"]), n(a["list_krw"]),
            n(a["time_cost"]), n(abs(a["cash_pl"])), n(abs(a["time_pl"])), n(a["be_cash"]) + "장",
            n(a["be_time"]) + "장", f"{a['pct_cash']}%", n(CR_HOURS) + "h", n(CR_EXTERNAL),
            n(b["U"]), "coin_rush_model.py",
        ],
        "34_livelihood-math.md": [
            n(b["after_tax_need"]), n(b["income_need"]), n(b["revenue_need"]), "₩" + n(b["U"]),
            f"{b['usd_ratio']}%", n(b["sens"]["fx_low"]), n(b["sens"]["fx_high"]), n(b["sens"]["wh_all"]),
            n(b["sens"]["disc40"]), n(b["sens"]["p699"]), n(b["be_cash"]) + "장", n(b["labor_total"]),
            n(b["be_labor"]) + "장", n(b["be_life"]) + "장", n(b["maint_cost"]), n(b["cand_total"]),
            n(b["cand_need"]) + "장", f"{b['rev_lo']}~{b['rev_hi']}", n(b["sales10"]) + "장",
            n(b["sales12"]) + "장", f"약 {b['pct10']}%", n(b["sales12x2"]) + "장", n(b["cf_dep"]),
            n(b["cf_outside_dep"]), n(b["cf_end"]), n(b["cf_bal_m3"]), n(b["dec_avg3"]), n(b["half_need"]),
            f"${b['m3_asp']:.3f}", n(b["U3"]), n(b["m3_be_cash"]) + "장", n(b["m3_be_labor"]) + "장",
            n(b["m3_be_life"]) + "장", n(b["m3_cand"]) + "장", n(b["direct_recoup_units"]) + "장",
            n(d["cr_need_actual"]), "$12.50", "$11.25", "coin_rush_model.py",
        ],
        "39_after-launch-year.md": [
            n(c["units"]), n(c["usd"]), n(c["per_krw"]), n(c["need"]) + "장", n(c["units2y"]) + "장",
            n(c["pess"]), n(c["opt"]), n(c["maint_cost"]), f"{c['maint_pct']}%", f"{c['m1_share']}%",
            n(b["sales10"]) + "장", n(b["sales12"]) + "장", n(b["cand_need"]), "coin_rush_model.py",
        ],
        "40_second-game-24months.md": [
            n(d["cr_ops"]), n(d["h2_pre"]) + "h", n(d["remain"]) + "h", f"{d['cal_cap']}개월",
            n(d["game_total"]), n(d["cr_actual_total"]), n(d["cr_need_plan"]) + "장",
            n(d["cr_need_actual"]) + "장", n(d["cr_need_diff"]) + "장", n(d["h2_req_total"]),
            n(d["h2_need"]) + "장", f"{d['h2_rev_lo']}~{d['h2_rev_hi']}", n(d["s2_total"]),
            n(d["s2_need"]), n(d["h2_need_699"]), n(d["h2_24"]), f"{d['cr24_pct_actual']}%",
            f"{d['h2_24_pct']}%", n(d["s3_h2_pre"]) + "h", n(b["sales10"]) + "장", n(b["sales12"]) + "장",
            n(B["tot"]["cr_dep"]), n(B["tot"]["h2_dep"]), n(abs(B["tot"]["tax"])), n(B["end"]),
            n(B["tot"]["net"]), n(B["game_pl"]), n(B["game_living"]), n(B["contract_share"]),
            n(B["l12_dep"]), n(B["l12_paid_living"]), f"{B['l12_pct']}%", n(B["min_bal"]),
            *[n(S[k]["end"]) for k in ("S1", "S2", "S3", "S4", "S5")],
            *[n(abs(S[k]["min_bal"])) for k in ("S1", "S2", "S3", "S4", "S5")],
            *[n(abs(S[k]["game_pl"])) for k in ("S1", "S2")],
            n(S["S1"]["tot"]["h2_dep"]), n(abs(S["S1"]["tot"]["tax"])), n(S["S1"]["game_living"]),
            n(S["S4"]["game_living"]), n(S["S4"]["savings_draw"]), n(d["cr_last3_avg"]),
            "coin_rush_model.py",
        ],
    }


def main():
    ch29(); ch34(); ch39(); ch40()
    if "--check" in sys.argv:
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(here)
        missing = []
        total = 0
        for fname, needles in checks().items():
            text = open(os.path.join(root, fname), encoding="utf-8").read()
            for s in needles:
                total += 1
                if s not in text:
                    missing.append((fname, s))
        if missing:
            print(f"누락 {len(missing)}/{total}건:")
            for f, s in missing:
                print(f"  {f}: {s}")
            sys.exit(1)
        print(f"OK — {total}개 수치가 모두 장 본문에 있습니다.")
        return
    report()


if __name__ == "__main__":
    main()
