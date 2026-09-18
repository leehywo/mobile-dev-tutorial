# 23. 밸런싱과 경제 설계

> **이 장에서 배울 것**
> - 선형·다항·지수 성장 공식의 차이를 설명하고, 경험치 요구량 곡선을 표로 설계한다
> - 업그레이드 선택지의 가치를 "DPS 증가율"로 비교해 정답이 뻔한 선택을 찾아낸다
> - 강화 규칙을 순수 C# 한 곳에 두고 **실제 게임과 시뮬레이터가 같은 규칙**을 쓰게 구현한다 (레벨업·코인 제단·영구 강화 3종)
> - 메타 재화의 Source/Sink, 한 판당 기대 획득량, 영구 강화 비용 곡선을 "몇 판 만에 무엇을" 목표에서 역산한다
> - 몬테카를로 시뮬레이터(`BalanceSimulator`)로 1000판을 돌려 생존 시간 분포를 얻고, 가정의 범위를 밝힌 채 수치를 조정한다
> - 업그레이드 조합이 실제로 **다른 플레이 방식**을 만드는지 빌드 프로파일 시뮬레이션으로 판정하고, 지배 선택지를 찾아 수치를 고친다
> - 영구 강화가 다 차는 시점(**콘텐츠 고갈**)과 목표 공백을 측정해 비용 곡선·해금 순서로 고친다
>
> **선수 장**: 03, 04, 10, 11, 21, 22 · **예상 시간**: 9~11시간 · **코인 러시 진행**: 레벨업 선택이 실제로 무기·체력에 적용됨, 코인 제단(판 안 소비)과 영구 강화 3종(판 밖 저축)이 동작함, `ProgressionData` 에셋, 에디터에서 1000판을 몇 초 만에 돌리는 밸런스 시뮬레이터, 조정 전후 기록, 빌드 프로파일 15종 비교표와 지배 선택지 수정 전후 기록, 콘텐츠 고갈 판 수와 목표 공백 측정

## 왜 필요한가

22장에서 10분 웨이브 표와 제단 시각을 만들었습니다. 그런데 지금 코인 러시에는 세 가지 구멍이 있습니다.

```
- 11장 LevelUpState.OnChosen은 "효과 적용은 23장에서"라며 로그만 찍는다 → 레벨업해도 강해지지 않는다
- 22장 제단 이벤트는 경고만 띄운다 → 판 안에서 코인을 쓸 곳이 없다
- 10장 영구 강화는 최대 체력 1종뿐, 비용은 감으로 정한 50×(L+1) → 21장 기획서(3종 × 10레벨)와 다르다
```

그리고 숫자에 대한 질문이 쌓였습니다.

```
- 평범한 플레이어가 10분을 버틸 확률은 몇 %인가? 죽는다면 주로 몇 분에 죽는가?
- 한 판에 코인을 평균 몇 개 이월하는가? 영구 강화를 다 사려면 몇 판이 필요한가?
- 제단에서 코인을 쓰는 전략과 모으는 전략 중 한쪽이 압도적인가?
- 강화 7종을 넣었는데 플레이어는 정말 다른 빌드로 노는가, 아니면 늘 같은 것만 고르는가?
- 영구 강화를 다 사는 데 몇 판이 걸리고, 다 산 뒤에는 무엇을 목표로 하는가?
```

직접 플레이해서 답하려면 한 판에 10분, 10판이면 100분입니다. 게다가 개발자는 게임을 가장 잘하는 사람이라 결과가 쉬운 쪽으로 치우칩니다. 이 장은 강화 규칙을 **실제 게임에 연결**하고, 같은 규칙으로 **시뮬레이터가 1000판을 몇 초 만에** 돌리게 한 뒤, 분포를 보고 조정합니다. 웹 개발로 치면 비즈니스 로직을 순수 함수로 분리해 앱과 부하 테스트 도구가 함께 쓰게 하는 것과 같습니다.

## 개념

### 스프레드시트 설계의 세 시트

밸런스 스프레드시트는 세 종류의 시트로 나눕니다. 섞이면 "어디를 고쳐야 하는지"를 잃어버립니다.

| 시트 | 내용 | 규칙 |
|---|---|---|
| 파라미터 | 손으로 정하는 숫자 (기본 피해 10, 성장 지수 1.6 …) | 여기만 수정한다. 셀에 이름을 붙인다 |
| 계산 | 공식으로 파생되는 표 (레벨별 요구량, 누적량 …) | 숫자를 직접 입력하지 않는다. 전부 수식 |
| 출력 | 그래프, 목표 대비 비교 | 판단용. 시뮬레이터 결과도 여기에 붙인다 |

게임 쪽 진실의 원천은 ScriptableObject 에셋입니다(22장). 스프레드시트는 **파라미터를 탐색하는 곳**이고, 확정된 파라미터만 에셋에 옮깁니다.

### 성장 공식 세 가지

레벨 L에서 다음 레벨까지 필요한 경험치(또는 비용)를 만드는 대표 공식입니다.

| 공식 | 식 (예시 계수) | L=1 | L=5 | L=10 | L=20 | L=30 | 특징 |
|---|---|---|---|---|---|---|---|
| 선형 | `5 + 3(L-1)` | 5 | 17 | 32 | 62 | 92 | 후반이 너무 쉬워짐 |
| 다항 (지수 1.6) | `5 + (L-1)^1.6` | 5 | 14 | 39 | 116 | 224 | 완만하게 가팔라짐 |
| 다항 (지수 2) | `5 + (L-1)^2` | 5 | 21 | 86 | 366 | 846 | 중반부터 급격 |
| 지수 (11장) | `5 × 1.25^(L-1)` | 5 | 12 | 37 | 347 | 3,231 | 초반 완만, 후반 폭발 |

고르는 기준은 **"획득량이 어떻게 증가하는가"와 짝을 맞추는 것**입니다.

- 서바이버라이크는 시간에 따라 적이 늘어 **코인 획득 속도도 오릅니다.** 요구량이 선형이면 후반에 레벨업이 폭주하고, 지수이면 후반에 레벨업이 멈춥니다. 보통 다항(지수 1.3~2)이 맞습니다.
- 영구 강화 비용은 한 판당 획득량이 크게 늘지 않으므로 **지수**를 씁니다. 지수는 "초반 몇 개는 금방, 마지막 몇 개는 오래"라는 목표를 만들기 쉽습니다.

### 업그레이드 가치 비교: 선택당 DPS 증가율

레벨업 3택1이 의미 있는 결정이 되려면 **선택지끼리 가치가 비슷하거나, 상황에 따라 순위가 바뀌어야** 합니다. 코인 러시의 공격 계열 강화(예시 수치)를 DPS 증가율로 비교합니다.

```
DPS = 기본 피해 × 피해 배율 × 공격 속도 배율 × 투사체 수 × 명중 효율

+피해     : 피해 배율 += 0.25   (합연산)
+공격 속도 : 공격 속도 배율 × 1.15 (곱연산)
+투사체   : 투사체 수 += 1      (최대 5)
```

| 현재 상태 | +피해 | +공격 속도 | +투사체 |
|---|---|---|---|
| 초반: 피해 1.0, 투사체 1 | 1.25/1.0 = **+25%** | **+15%** | 2/1 = **+100%** |
| 중반: 피해 1.5, 투사체 2 | 1.75/1.5 = **+16.7%** | **+15%** | 3/2 = **+50%** |
| 후반: 피해 2.5, 투사체 4 | 2.75/2.5 = **+10%** | **+15%** | 5/4 = **+25%** |
| 투사체 최대(5) | 피해 3.0 기준 +8.3% | **+15%** | 선택 불가 |

이 표에서 세 가지를 읽습니다.

1. **투사체가 항상 최고입니다.** 초반 +100%는 다른 선택을 무의미하게 만듭니다. 대응: 최대치(5)를 두고, 투사체 한 발의 가치 자체를 낮추거나(투사체당 피해 감소), 첫 등장 레벨을 늦춥니다.
2. **합연산 강화는 쌓일수록 가치가 떨어지고**, 곱연산 강화는 일정합니다. 그래서 후반에는 공격 속도가 피해보다 좋아집니다. 이 "순위 역전"은 좋은 현상입니다 — 상황에 따라 답이 바뀌는 선택이니까요.
3. 생존 계열(최대 체력, 재생, 방어)은 DPS로 비교할 수 없습니다. 이것들은 시뮬레이터로 **생존 시간에 미치는 영향**을 봐야 합니다.

### 빌드 다양성과 지배 전략

**빌드**는 한 판이 끝났을 때의 강화 구성입니다. 숫자로는 강화 7종의 스택 수를 늘어놓은 **벡터**입니다.

```
P1의 3판째: [피해 2, 공속 1, 투사체 4, 체력 0, 재생 0, 자석 1, 방어 0]
P1의 4판째: [피해 1, 공속 2, 투사체 4, 체력 0, 재생 0, 자석 0, 방어 1]
```

두 판의 빌드가 늘 이렇게 비슷하면, 선택지가 7종이어도 플레이어가 겪는 게임은 한 가지입니다. 21장이 적은 "다시 켜는 이유"는 대부분 **다음 판은 다르게 풀린다**는 기대에서 오므로, 빌드가 수렴하면 재방문 이유가 먼저 마릅니다.

**지배 전략**은 상황과 무관하게 항상 최적인 선택입니다. 3택1에 지배 선택지가 하나 섞이면 그 레벨업은 사실상 **1택**이 되고, 남은 두 장은 화면 장식이 됩니다. 이 장에서는 네 가지 신호로 판정합니다. **기준값은 코인 러시에서 쓰려고 정한 것이고 장르·게임마다 달라야 합니다.**

| 신호 | 측정 | 판정 기준 (코인 러시) | 어디서 재는가 |
|---|---|---|---|
| **결과 지배** | 한 종류만 우선하는 프로파일끼리 클리어율·생존 중앙값·이월 코인 비교 | 1위가 2위를 **클리어율 10%p 이상** 앞서면 지배 | 시뮬레이터 (11단계) |
| **사문화** | 어떤 종류를 우선한 프로파일의 클리어율 | 균등 프로파일의 **1/3 미만**이면 "고르면 손해" | 시뮬레이터 (11단계) |
| **선택 편중** | 제시됐을 때 고른 비율(조건부 선택률) | **70% 이상**이면 사실상 1택 | 실플레이 로그 (24장) |
| **빌드 수렴** | 같은 사람의 서로 다른 판 빌드 벡터 코사인 유사도 중앙값 | **0.85 이상**이면 매 판 같은 게임 | 실플레이 로그 (24장) |

코사인 유사도는 두 벡터가 이루는 각도로 방향이 얼마나 같은지를 재는 값입니다(1이면 구성 비율이 같음, 0이면 겹치는 강화가 없음). 총 스택 수가 달라도(짧게 죽은 판과 클리어한 판) **구성 비율**만 비교하므로 빌드 비교에 알맞습니다.

```
유사도(a, b) = Σ(aᵢ × bᵢ) / (√Σaᵢ² × √Σbᵢ²)
```

앞의 DPS 증가율 표는 **한 선택의 값**만 보여줍니다. 지배 여부는 그 선택을 계속 쌓았을 때의 **결과**로 판정해야 합니다. 값이 커도 상한(투사체 5개)에 금방 닿으면 지배가 아니고, 값이 작아도 생존을 늘려 수집량까지 늘리면 지배가 될 수 있습니다. 그래서 11단계에서 프로파일별로 1000판씩 돌립니다.

시뮬레이터가 답할 수 있는 것과 없는 것도 갈립니다. **"어떤 빌드가 강한가"는 시뮬레이터가**, **"사람이 실제로 무엇을 고르는가"는 24장 로그가** 답합니다. 봇의 선택 비율은 우리가 가중치로 정한 값이므로 선택 편중의 증거가 될 수 없습니다.

### 하나의 규칙, 두 실행기

위 표의 `+0.25`, `×1.15`가 스프레드시트, 시뮬레이터, 실제 게임에 **따로** 적혀 있으면 반드시 어긋납니다. 가장 흔한 사고는 "시뮬레이터에서만 강해지는" 것입니다. 시뮬레이터 `switch`에는 강화 효과가 있는데 게임의 레벨업은 로그만 찍고 있으면, 시뮬레이터가 말하는 클리어율은 존재하지 않는 게임의 클리어율입니다.

```
            UpgradeRules.cs (순수 C#: 강화 종류, 효과 수치, 성장 공식)
               ▲                                  ▲
   PlayerStats (MonoBehaviour)            BalanceSimulator (에디터 메뉴)
   · 레벨업 선택 → Apply                  · 랜덤 봇 선택 → Apply
   · 제단 구매   → Apply(stacks)          · 제단 정책    → Apply(stacks)
   · 영구 강화 레벨 → 생성자              · 영구 강화 레벨 → 생성자
   · 무기·체력·자석이 값을 읽음           · DPS·피격 모델이 값을 읽음
```

규칙 파일은 `UnityEngine`을 참조하지 않으므로 에디터 메뉴에서도, 콘솔 프로젝트에서도 돌아갑니다. 강화 종류를 추가할 때(21장 스코프의 제단 강화 8종까지 늘릴 때) `UpgradeKind`와 `CombatStats.Apply`를 고치면 게임과 시뮬레이터가 **동시에** 바뀝니다.

### 메타 경제: Source와 Sink

재화 경제는 **들어오는 곳(Source)**과 **나가는 곳(Sink)**으로 그립니다.

```
         Source (생산)                         Sink (소모)
   ┌──────────────────────┐              ┌──────────────────────────┐
   │ 적 처치 코인 드롭      │──┐       ┌──▶│ 판 안: 코인 제단 (소멸)     │
   │ 엘리트·보스 드롭       │  │       │   └──────────────────────────┘
   │ 클리어 보너스 ×1.5    │  ▼       │   ┌──────────────────────────┐
   └──────────────────────┘ [지갑] ────┼──▶│ 판 밖: 영구 강화 3종 (지수)  │
                                       │   └──────────────────────────┘
   (모바일 확장판만: 보상형 광고 ×2, 25장)   └──▶│ 판 밖: 캐릭터 해금 (고정가)  │
                                           └──────────────────────────┘
```

원칙은 두 가지입니다.

- **Sink가 Source보다 먼저 바닥나면 인플레이션**입니다. 영구 강화를 다 사고 나면 코인이 쌓이기만 하고 가치가 0이 됩니다. 그 순간 "코인을 모을까 쓸까"라는 코인 러시의 핵심 긴장도 사라집니다.
- **한 판당 이월 기대값**을 기준 단위로 삼습니다. 모든 가격을 "몇 판어치"로 말할 수 있어야 합니다.

```
한 판당 이월 기대값 = Σ(분 m에 사망할 확률 × 그때 지갑) + P(클리어) × 클리어 시 지갑 × 1.5
지갑 = 주운 코인 − 제단에서 쓴 코인
```

이 확률 분포를 손으로 구하기는 어렵습니다. 그래서 시뮬레이터가 필요합니다.

### 목표에서 역산하기: "몇 판 만에 무엇을"

비용을 먼저 정하지 말고 **플레이어 경험 목표**를 먼저 적은 뒤 거꾸로 계산합니다. 코인 러시의 목표(예시)입니다. 시뮬레이터를 돌리기 **전에** 적어 둡니다.

| 목표 | 판 수 | 플레이 시간 (1판 ≈ 10분) | 이유 |
|---|---|---|---|
| 첫 영구 강화 구매 | 1판 | 10분 | 첫 판 끝에 "성장"을 반드시 경험 |
| 첫 클리어 (기준 가정) | 2~4판 | 20~40분 | 첫 세션 안에 성취 |
| 세 강화 모두 5레벨 | 약 8판 | 약 1시간 반 | 두 번째 세션 목표 |
| 세 강화 모두 10레벨 | 40~50판 | 7~8시간 | 저가 게임의 적정 플레이 시간 가정 |

지수 비용 `cost(L) = 기본가 × 성장률^(L-1)`에서 기본가는 "첫 판 이월량보다 작게", 성장률은 "마지막 레벨 도달 판 수"에 맞춰 조정합니다. 최종 확인은 역시 시뮬레이터로 합니다(실습 9단계).

### 인플레이션과 파워 크립

- **인플레이션**: 재화가 가치를 잃는 현상입니다. 코인 러시에서는 영구 강화가 끝난 뒤 발생합니다. 대응은 새 Sink(캐릭터 해금, 외형), 획득량 상한, 혹은 "최대 이후 코인은 점수로 전환" 같은 설계입니다.
- **파워 크립**: 업데이트마다 새 무기·캐릭터가 기존 것보다 강해지는 현상입니다. 새 콘텐츠는 **더 강하게가 아니라 다르게** 만들고, 추가할 때마다 시뮬레이터를 다시 돌려 클리어율 변화를 기록합니다.

### 콘텐츠 고갈: 목표가 사라지는 판

인플레이션의 짝은 **콘텐츠 고갈**입니다. 재화가 남는 것이 인플레이션이라면, 고갈은 **살 것이 없어지는 것**입니다. 코인 러시에는 새 콘텐츠를 계속 만들 인력이 없으므로(21장 스코프), 있는 것으로 목표가 얼마나 오래 유지되는지를 미리 재 둡니다. 세 가지를 봅니다.

| 지표 | 정의 | 코인 러시 목표 |
|---|---|---|
| **고갈 판 수** | 영구 강화 3종이 모두 최대 레벨이 되어 살 것이 하나도 남지 않는 판 번호 | 40~50판 (역산 목표와 같음) |
| **최대 목표 공백** | 무언가를 산 판과 그다음으로 산 판 사이의 **최대 간격(판)**. 첫 구매까지의 거리도 한 번의 간격으로 센다 | 5판 이하 (1세션 ≈ 3판, 두 세션 가까이 아무 변화가 없으면 목표가 사라진 것으로 본다) |
| **고갈 후 잉여** | 고갈 이후 쌓이기만 하는 코인 | 0 (출시 전에 다음 Sink를 준비) |

고치는 레버는 셋이고, **비용이 싼 순서**로 씁니다.

1. **비용 곡선 재배분** — 총액은 비슷하게 두고 성장률을 낮추면서 기본가를 올리면, 마지막 몇 레벨의 한 걸음이 작아져 목표 공백이 줄어듭니다. 에셋 숫자 두 개만 바꾸므로 가장 쌉니다.
2. **해금 순서** — 3종을 처음부터 다 열지 않고 순서대로 엽니다. "다음에 뭘 살까" 외에 "다음에 뭐가 열릴까"라는 목표가 생기지만, 초반에 세 강화를 모두 체감하는 시점이 뒤로 밀립니다.
3. **새 Sink 추가** — 캐릭터 해금·외형처럼 만들 것이 생깁니다. 가장 비싸므로 1·2로 목표 구간에 들어가지 않을 때만 씁니다(연습 4).

### 몬테카를로 시뮬레이션과 그 한계

몬테카를로 시뮬레이션은 **무작위 요소가 있는 과정을 수없이 반복 실행해 결과의 분포를 얻는 방법**입니다. 레벨업 선택지가 무작위이므로 평균 한 줄로는 부족합니다.

```
평균 생존 7분  ─┬─ 모두 7분 근처에서 죽는다      → 7분에 벽이 있다
               └─ 절반은 3분, 절반은 클리어      → 운에 따라 극단적이다
```

두 경우는 평균이 같아도 전혀 다른 게임입니다. 그래서 **분 단위 사망 히스토그램**을 봅니다.

시뮬레이터는 게임을 그대로 돌리지 않고 **모델**을 돌립니다. 코인 러시 모델의 가정은 다음과 같습니다.

```
- 1초 단위. 매초 WaveData의 실제 구간 경계로 그 시각의 구간을 찾는다
- 일반 적은 개체가 아니라 "적체 HP"로 다룬다. 적체는 구간의 maxAlive × 평균 체력을 넘지 않는다
  (넘친 스폰은 버림 — 22장 스포너 규칙과 같음)
- 엘리트·보스·떼는 개체별 남은 체력·접촉 피해·코인을 따로 추적한다
- 피해 분배: 남은 체력 비율대로 일반 적과 이벤트 적에게 나뉜다
- 피격: 화면 일반 적 수가 회피 한계를 넘은 만큼 + 살아 있는 이벤트 적마다 접촉 확률
- 레벨업·제단: CombatStats 규칙으로 적용. 선택은 "랜덤 봇"이 무작위로
```

22장 10단계가 넣은 폭탄충·주술사는 **위치가 있어야 성립하는 메커닉**이라 이 모델에 그대로 들어가지 않습니다. 둘 다 "통계적 부담"으로 낮춰 근사하고, 근사 방식과 잃어버린 것을 함께 적어 둡니다.

| 22장의 메커닉 | 시뮬레이터 근사 | 잃어버린 것 |
|---|---|---|
| 폭탄충: 죽은 자리에서 0.8초 뒤 반경 2.5에 18 피해 | **죽은 폭탄충 수 × 18 × `blastHitChance`**(기본 0.08)를 그 초의 피해에 더한다. 구간의 폭탄충 가중치 비율로 "죽은 수 중 몇 마리가 폭탄충인지"를 나눈다 | "무리를 뒤에 끌면 반드시 등 뒤에서 터진다"는 위치 규칙. 모델에서는 선회하든 도주하든 같은 확률이다 |
| 주술사: 살아 있는 동안 반경 4에 이동속도 ×0.6 장판 | 살아 있는 주술사 수만큼 **회피 한계(`dodgeCapacity`)를 낮춘다**(마리당 5%, 최대 40% — 22장의 "겹쳐도 가장 강한 하나" 상한과 같은 값) | 장판의 **위치**. 진행 방향 앞을 막는 것과 지나간 자리에 깔리는 것이 모델에서는 같다 |

그래서 **이 시뮬레이터로는 22장 9단계의 단조 지수를 잴 수 없습니다.** 단조 지수는 "어떤 대응으로 통과되는가"를 묻는데 이 모델에는 대응이 없습니다. 22장은 사람이 직접 12판을 돌려 그것을 쟀고, 이 장은 그 결과로 확정된 웨이브 표를 **입력으로 받아** 수치를 조정합니다. 두 도구가 답하는 질문이 다릅니다.

모델은 틀립니다. 위치, 이동, 무기 범위를 무시했고, **명중 효율·회피 한계·수집률·접촉 확률·폭발 적중률은 임의로 정한 계수**입니다. 랜덤 봇은 강화 선택만 무작위일 뿐, 이 계수들 때문에 사람보다 잘 피할 수도 못 피할 수도 있습니다. 그래서 결과는 "실제 난이도의 상한"도 "하한"도 아니고 **특정 가정 아래의 비교 모델**입니다. 쓰는 법은 두 가지입니다.

1. **같은 가정 안에서 상대 비교**: "경험치 곡선을 바꾸면 클리어율이 오르는가"의 방향과 크기.
2. **가정의 폭을 함께 보고**: 기준 가정 외에 초보·숙련 가정 시나리오를 나란히 돌려 결론이 뒤집히는지 봅니다. 계수는 24장 플레이테스트의 실제 사망 시각·수집량으로 보정하기 전까지 **탐색용 가설**입니다. 폭발 적중률은 22장 11단계 절차 C의 "2:00~4:00 폭발 사망 건수"로 보정할 수 있는 몇 안 되는 계수입니다.

## 실습: 코인 러시에 적용하기

### 1단계: 경험치 요구량 표

스프레드시트 계산 시트에 1~30레벨 표를 만듭니다. 아래는 일부 행입니다. "필요"는 L에서 L+1로 가는 데 필요한 코인, "누적"은 L+1 도달까지의 합입니다. 초안은 **11장 정본 `5×1.25^(L-1)`**, 조정안은 다항 지수 1.6입니다(조정 근거는 8단계). **예시 수치**입니다.

| L | 초안 필요 `5×1.25^(L-1)` | 초안 누적 | 조정 필요 `5+(L-1)^1.6` | 조정 누적 |
|---|---|---|---|---|
| 1 | 5 | 5 | 5 | 5 |
| 2 | 6 | 11 | 6 | 11 |
| 3 | 8 | 19 | 8 | 19 |
| 5 | 12 | 41 | 14 | 44 |
| 8 | 24 | 99 | 27 | 112 |
| 10 | 37 | 166 | 39 | 184 |
| 12 | 58 | 271 | 51 | 280 |
| 14 | 91 | 435 | 66 | 404 |
| 16 | 142 | 691 | 81 | 558 |
| 18 | 222 | 1,091 | 98 | 745 |
| 20 | 347 | 1,716 | 116 | 968 |
| 25 | 1,059 | 5,276 | 167 | 1,698 |
| 30 | 3,231 | 16,137 | 224 | 2,700 |

22장 **10단계 수정 후** 웨이브 표의 `coins_per_min`을 모두 더하면 약 1,390개, 이벤트 드롭(2:05 폭탄충 6, 엘리트 30·60, 4:05·5:20 주술사 5·15, 박쥐 떼 24, 7:30 폭탄충 포위 30, 보스 300)이 450개입니다. 수집률 60%면 **모든 적을 처치했을 때** 약 1,100개이고, 이는 22장 10-8 제단 표의 판 끝 상한 1,102와 같은 값입니다. 초안 곡선은 누적 1,100 부근이 레벨 18이고, 레벨 14부터 한 단계에 90개 이상이 필요해 후반 성장이 막힙니다. 실제로는 모든 적을 처치하지 못하므로 더 낮은 레벨에서 멈출 것입니다. 표만 봐도 의심이 가지만, 확신은 시뮬레이터로 얻습니다.

한 가지 더 볼 것이 있습니다. 조정안은 **L4~L10 구간에서 초안보다 조금 더 비쌉니다**(예: L5 14 대 12). 곡선을 바꾸면 모든 구간이 같은 방향으로 바뀌지 않으므로, 결과도 분 단위로 봐야 합니다.

### 2단계: 영구 강화 비용 표

21장 기획서대로 **영구 강화는 3종 × 10레벨**입니다. 공격력(+10% 피해/레벨), 최대 체력(+10/레벨), 수집 범위(+10%/레벨)에 같은 곡선 `cost(L) = 기본가 × 1.5^(L-1)`을 10 단위로 반올림해 씁니다. 표의 L은 **구매할 레벨**입니다. 현재 3레벨인 강화의 다음 가격은 `cost(4)`입니다.

| 구매 레벨 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 초안 기본가 200 | 200 | 300 | 450 | 680 | 1,010 | 1,520 | 2,280 | 3,420 | 5,130 | 7,690 |
| 초안 누적 | 200 | 500 | 950 | 1,630 | 2,640 | 4,160 | 6,440 | 9,860 | 14,990 | 22,680 |
| 채택 기본가 300 | 300 | 450 | 680 | 1,010 | 1,520 | 2,280 | 3,420 | 5,130 | 7,690 | 11,530 |
| 채택 누적 | 300 | 750 | 1,430 | 2,440 | 3,960 | 6,240 | 9,660 | 14,790 | 22,480 | 34,010 |

세 종류를 모두 최대로 올리면 채택안 기준 102,030 코인입니다. 한 판 이월이 800 안팎이라면 120판이 넘어 보이지만, 영구 강화가 쌓일수록 이월량도 늘어나니 실제로는 훨씬 적습니다. 정확한 판 수는 10단계에서 시뮬레이터로 확인합니다(채택 기본가 300은 그 결과로 정해진 값입니다). 13단계에서 이 곡선을 한 번 더 재배분합니다.

### 3단계: 공유 규칙 — UpgradeRules.cs

강화 종류, 효과 수치, 성장 공식을 한 파일에 둡니다. `UnityEngine`을 쓰지 않는 순수 C#입니다. 파일: `Assets/_CoinRush/Scripts/Balance/UpgradeRules.cs`

```csharp
using System;

/// <summary>레벨업·제단에서 고르는 강화의 종류. 에셋(UpgradeData)과 시뮬레이터가 함께 쓴다.</summary>
public enum UpgradeKind { Damage, AttackSpeed, Projectile, MaxHp, Regen, Magnet, Armor }

public enum XpCurve { Exponential, Polynomial }

/// <summary>판 밖 영구 강화 3종의 세이브 키 (21장 기획서: 영구 강화 3종 × 10레벨)</summary>
public static class MetaUpgradeIds
{
    public const string Damage = "damage";   // +10% 피해 / 레벨
    public const string MaxHp = "maxHp";     // +10 최대 체력 / 레벨 (10장 키 그대로)
    public const string Magnet = "magnet";   // +10% 수집 범위 / 레벨
    public static readonly string[] All = { Damage, MaxHp, Magnet };

    public static string Label(string id) => id switch
    {
        Damage => "공격력", MaxHp => "최대 체력", Magnet => "수집 범위", _ => id
    };
}

/// <summary>성장 공식. ProgressionData(에셋)와 SimConfig(시뮬레이터)가 같은 함수를 부른다.</summary>
public static class ProgressionRules
{
    /// <summary>레벨 level에서 level+1로 가는 데 필요한 코인</summary>
    public static int XpToNext(XpCurve curve, float xpBase, float xpGrowth, float xpScale, float xpPower, int level) =>
        (int)Math.Round(curve == XpCurve.Exponential
            ? xpBase * Math.Pow(xpGrowth, level - 1)                 // 11장: 5 × 1.25^(L-1)
            : xpBase + xpScale * Math.Pow(level - 1, xpPower));      // 5 + (L-1)^p

    /// <summary>nextLevel(1부터)을 "구매하는" 비용. 현재 레벨이 L이면 UpgradeCost(L + 1).</summary>
    public static int UpgradeCost(int baseCost, float growth, int nextLevel) =>
        (int)Math.Round(baseCost * Math.Pow(growth, nextLevel - 1) / 10.0) * 10;
}

/// <summary>
/// 한 판 동안의 전투 능력치와 강화 규칙. UnityEngine을 쓰지 않는 순수 C#이라
/// 실제 게임(PlayerStats)과 시뮬레이터(BalanceSimulator)가 "같은 규칙"을 공유한다.
/// </summary>
public class CombatStats
{
    public const int MaxProjectiles = 5;
    public const float DamagePerStack = 0.25f;       // 합연산
    public const float AttackSpeedPerStack = 1.15f;  // 곱연산
    public const float MaxHpPerStack = 25f;
    public const float RegenPerStack = 0.5f;         // 초당 회복
    public const float MagnetPerStack = 0.15f;       // 수집 범위 배율 합연산
    public const float ArmorPerStack = 0.92f;        // 받는 피해 곱연산

    public const float MetaDamagePerLevel = 0.1f;
    public const float MetaMaxHpPerLevel = 10f;
    public const float MetaMagnetPerLevel = 0.1f;

    public float DamageMul { get; private set; } = 1f;
    public float AttackRate { get; private set; } = 1f;
    public int Projectiles { get; private set; } = 1;
    public float MaxHpBonus { get; private set; }
    public float RegenPerSecond { get; private set; }
    public float MagnetMul { get; private set; } = 1f;
    public float DamageTakenMul { get; private set; } = 1f;

    public CombatStats(int metaDamageLevel, int metaMaxHpLevel, int metaMagnetLevel)
    {
        DamageMul += MetaDamagePerLevel * metaDamageLevel;
        MaxHpBonus += MetaMaxHpPerLevel * metaMaxHpLevel;
        MagnetMul += MetaMagnetPerLevel * metaMagnetLevel;
    }

    /// <summary>선택지로 제시해도 되는가 (투사체는 최대치가 있다)</summary>
    public bool CanApply(UpgradeKind kind) => kind != UpgradeKind.Projectile || Projectiles < MaxProjectiles;

    public void Apply(UpgradeKind kind, int stacks = 1)
    {
        for (int i = 0; i < stacks; i++)
        {
            switch (kind)
            {
                case UpgradeKind.Damage: DamageMul += DamagePerStack; break;
                case UpgradeKind.AttackSpeed: AttackRate *= AttackSpeedPerStack; break;
                case UpgradeKind.Projectile: if (Projectiles < MaxProjectiles) Projectiles++; break;
                case UpgradeKind.MaxHp: MaxHpBonus += MaxHpPerStack; break;
                case UpgradeKind.Regen: RegenPerSecond += RegenPerStack; break;
                case UpgradeKind.Magnet: MagnetMul += MagnetPerStack; break;
                case UpgradeKind.Armor: DamageTakenMul *= ArmorPerStack; break;
            }
        }
    }

    /// <summary>무기 한 발의 피해 (정수 체력에 맞춰 반올림, 최소 1)</summary>
    public int ShotDamage(int baseDamage) => Math.Max(1, (int)Math.Round(baseDamage * DamageMul));

    public float Cooldown(float baseCooldown) => baseCooldown / AttackRate;

    public int ModifyIncomingDamage(int amount) => Math.Max(1, (int)Math.Round(amount * DamageTakenMul));

    /// <summary>초당 기대 피해 = 한 발 피해 × 초당 발사 수 × 투사체 수 × 명중 효율</summary>
    public float Dps(int baseDamage, float baseCooldown, float hitEfficiency) =>
        ShotDamage(baseDamage) / Cooldown(baseCooldown) * Projectiles * hitEfficiency;
}
```

- `CombatStats`는 한 판의 상태입니다. 판이 시작될 때 영구 강화 레벨로 만들고, 레벨업·제단에서 `Apply`합니다.
- 영구 강화의 "수집 범위"는 게임에서는 코인 자석 반경 배율(`MagnetMul`), 시뮬레이터에서는 수집률(기본 60% × `MagnetMul`, 최대 100%)로 읽습니다. 반경과 수집률의 관계는 모델 가정이므로 24장 실측으로 보정합니다.

### 4단계: ProgressionData 에셋과 앞 장 코드 교체

경험치 곡선, 영구 강화 비용, 제단 가격을 코드 상수에서 에셋으로 옮깁니다. 파일: `Assets/_CoinRush/Scripts/Balance/ProgressionData.cs`

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "ProgressionData", menuName = "Coin Rush/Progression Data")]
public class ProgressionData : ScriptableObject
{
    [Header("경험치: 지수 = xpBase × xpGrowth^(L-1), 다항 = xpBase + xpScale × (L-1)^xpPower")]
    public XpCurve xpCurve = XpCurve.Exponential;
    public float xpBase = 5f;
    public float xpGrowth = 1.25f;
    public float xpScale = 1f;
    public float xpPower = 1.6f;

    [Header("영구 강화 비용: cost(L) = baseCost × growth^(L-1), 10 단위 반올림")]
    public int upgradeBaseCost = 200;
    public float upgradeCostGrowth = 1.5f;
    public int upgradeMaxLevel = 10;

    [Header("코인 제단: 가격 = shrineBasePrice × 몇 번째 제단인지 (22장)")]
    public int shrineBasePrice = 50;
    [Min(1)] public int shrineStacks = 1;

    /// <summary>레벨 level에서 level+1로 가는 데 필요한 코인</summary>
    public int XpToNext(int level) => ProgressionRules.XpToNext(xpCurve, xpBase, xpGrowth, xpScale, xpPower, level);

    /// <summary>nextLevel을 구매하는 비용. 현재 레벨이 L이면 UpgradeCost(L + 1)</summary>
    public int UpgradeCost(int nextLevel) => ProgressionRules.UpgradeCost(upgradeBaseCost, upgradeCostGrowth, nextLevel);

    public int ShrinePrice(int shrineIndex) => shrineBasePrice * shrineIndex;
}
```

`Assets/_CoinRush/Data/`에서 **Create → Coin Rush → Progression Data**로 `Progression` 에셋을 만들고, 먼저 **초안 값**(Xp Curve `Exponential`, Xp Base 5, Xp Growth 1.25 = 11장과 같은 곡선, Upgrade Base Cost 200)으로 둡니다.

**11장 `PlayerExperience` 수정**: `baseRequired`, `growth` 필드를 지우고 에셋 필드를 추가한 뒤 `CalcRequired`를 교체합니다. Player 오브젝트의 `PlayerExperience` Inspector에서 **Progression**에 에셋을 연결합니다.

```csharp
// PlayerExperience.cs (11장) — 필드 교체: baseRequired, growth 삭제 →
[SerializeField] private ProgressionData progression;

// CalcRequired 교체
private int CalcRequired(int level) => progression.XpToNext(level);
```

**10장 `UpgradeShop` 교체**: 1종이던 상점을 3종으로 바꿉니다. 비용 함수에는 **구매할 다음 레벨**(`level + 1`)을 넘깁니다. 10장 `ApplyPermanentUpgrades.cs`는 5단계의 `PlayerStats`가 대신하므로 삭제하고 Player에서 컴포넌트를 뗍니다.

```csharp
using System.Text;
using TMPro;
using UnityEngine;

// Assets/_CoinRush/Scripts/Save/UpgradeShop.cs  (10장 파일 교체 — 영구 강화 3종)
public class UpgradeShop : MonoBehaviour
{
    public const string MaxHpId = MetaUpgradeIds.MaxHp;   // 10장·24장 코드 호환

    [SerializeField] private ProgressionData progression;
    [SerializeField] private TextMeshProUGUI label;

    private void OnEnable() => Refresh();

    // 버튼 OnClick에 연결하고 문자열 인자로 "damage" / "maxHp" / "magnet"을 넣는다
    public void TryBuy(string upgradeId)
    {
        SaveData save = SaveSystem.Load();
        int level = save.GetUpgradeLevel(upgradeId);
        if (level >= progression.upgradeMaxLevel) return;

        int cost = progression.UpgradeCost(level + 1);   // 현재 레벨이 아니라 "살 레벨"
        if (save.coins < cost) return;

        save.coins -= cost;
        save.upgrades[upgradeId] = level + 1;
        SaveSystem.Save(save);                            // 재화 변화는 즉시 저장 (10장, 21장 Must)
        Refresh();
    }

    private void Refresh()
    {
        SaveData save = SaveSystem.Load();
        var sb = new StringBuilder();
        sb.Append("코인 ").Append(save.coins).Append('\n');
        foreach (string id in MetaUpgradeIds.All)
        {
            int level = save.GetUpgradeLevel(id);
            sb.Append(MetaUpgradeIds.Label(id)).Append(" Lv.").Append(level).Append('/').Append(progression.upgradeMaxLevel);
            if (level >= progression.upgradeMaxLevel) sb.Append("  (최대)\n");
            else sb.Append("  다음 ").Append(progression.UpgradeCost(level + 1)).Append(" 코인\n");
        }
        label.text = sb.ToString();
    }
}
```

Title 씬의 상점 오브젝트에서 **Progression**을 연결하고, 기존 버튼을 복제해 세 개로 만든 뒤 각 OnClick에 `UpgradeShop.TryBuy`를 고르고 문자열 칸에 `damage`, `maxHp`, `magnet`을 입력합니다. `maxHp`는 10장 v2 세이브의 키와 같으므로 기존 레벨이 그대로 이어집니다.

### 5단계: 실제 게임에 규칙 적용하기

**11장 `UpgradeData`에 필드 추가**: 카드마다 어떤 강화인지 지정합니다.

```csharp
// UpgradeData.cs (11장) — 필드 추가
public UpgradeKind kind;
```

`Assets/_CoinRush/Data/Upgrades/`에 7종 에셋을 만들고(`Upgrade_Damage` … `Upgrade_Armor`) 각각 `Kind`를 지정합니다. 설명 문구는 `CombatStats` 상수와 일치시킵니다(예: "피해 +25%").

**플레이어 능력치 컴포넌트**: 판이 시작될 때 세이브의 영구 강화 레벨로 `CombatStats`를 만들고, 최대 체력과 재생을 `Health`에 반영합니다. 파일: `Assets/_CoinRush/Scripts/Player/PlayerStats.cs`

```csharp
using System;
using UnityEngine;

// Player에 부착 (10장 ApplyPermanentUpgrades 대체)
[RequireComponent(typeof(Health))]
public class PlayerStats : MonoBehaviour
{
    [SerializeField, Min(1)] private int baseMaxHp = 100;   // 시뮬레이터 baseMaxHp와 같은 값

    private Health health;
    private float regenBuffer;

    public CombatStats Stats { get; private set; }
    public float HpRatio => health.Max > 0 ? (float)health.Current / health.Max : 0f;
    public event Action Changed;   // HUD 등이 필요하면 구독

    private int MaxHp => baseMaxHp + Mathf.RoundToInt(Stats.MaxHpBonus);

    private void Awake()
    {
        health = GetComponent<Health>();
        SaveData save = SaveSystem.Load();
        Stats = new CombatStats(save.GetUpgradeLevel(MetaUpgradeIds.Damage),
                                save.GetUpgradeLevel(MetaUpgradeIds.MaxHp),
                                save.GetUpgradeLevel(MetaUpgradeIds.Magnet));
        health.SetMax(MaxHp, refill: true);   // 10장 메서드
    }

    public bool CanApply(UpgradeKind kind) => Stats.CanApply(kind);

    /// <summary>레벨업(stacks 1)과 코인 제단(stacks = ProgressionData.shrineStacks)이 부른다</summary>
    public void Apply(UpgradeKind kind, int stacks = 1)
    {
        int before = health.Max;
        Stats.Apply(kind, stacks);
        int after = MaxHp;
        if (after != before)
        {
            health.SetMax(after, refill: false);
            health.Heal(after - before);      // 늘어난 만큼 현재 체력도 (시뮬레이터와 같은 규칙)
        }
        Changed?.Invoke();
    }

    private void Update()
    {
        if (Stats.RegenPerSecond <= 0f || health.IsDead) return;
        regenBuffer += Stats.RegenPerSecond * Time.deltaTime;   // 레벨업 정지(timeScale 0) 중에는 쌓이지 않음
        if (regenBuffer < 1f) return;
        int amount = Mathf.FloorToInt(regenBuffer);
        regenBuffer -= amount;
        health.Heal(amount);                  // Health는 정수 체력이므로 1 단위로 모아서 회복
    }
}
```

**05·12장 `AutoAimWeapon` 수정**: 필드 하나를 추가하고 `Update`를 교체합니다(`pools`는 12장에서 추가한 `GameplayPools` 필드, `Rotated`는 05장 확장 메서드로 각도 단위는 도).

```csharp
// AutoAimWeapon.cs (05·12장) — 필드 추가
[SerializeField] private PlayerStats stats;
[SerializeField, Range(0f, 45f)] private float spreadAngle = 12f;   // 투사체 사이 각도

// Update 교체
void Update()
{
    cooldownLeft -= Time.deltaTime;
    if (cooldownLeft > 0f) return;
    if (!TryFindTarget(out Vector2 aimDirection)) return;

    CombatStats s = stats.Stats;
    cooldownLeft = s.Cooldown(weapon.cooldown);       // 공격 속도 강화
    int damage = s.ShotDamage(weapon.damage);         // 피해 강화 (영구 공격력 포함)
    int count = s.Projectiles;                        // 투사체 강화
    for (int i = 0; i < count; i++)
    {
        float angle = (i - (count - 1) * 0.5f) * spreadAngle;   // 가운데를 기준으로 부채꼴
        Projectile shot = pools.Projectiles.Spawn(transform.position);
        shot.Launch(aimDirection.Rotated(angle), weapon.projectileSpeed, damage);
    }
}
```

**16장 `CoinMagnet` 수정**: 코인이 생성될 때 받은 플레이어의 자석 배율로 반경을 정합니다. 풀에서 재사용되므로 프리팹 원래 반경을 한 번 기억해 둡니다.

```csharp
// CoinMagnet.cs (16장) — 필드 추가
float baseRadius = -1f;

// SetPlayer 교체
public void SetPlayer(Transform target)
{
    player = target;
    if (baseRadius < 0f) baseRadius = pickupRadius;   // 첫 호출 때 프리팹 값 저장
    float mul = target != null && target.TryGetComponent(out PlayerStats stats) ? stats.Stats.MagnetMul : 1f;
    pickupRadius = baseRadius * mul;
}
```

**07장 `PlayerContactDamage` 수정**: 방어 강화를 받는 피해에 반영합니다.

```csharp
// PlayerContactDamage.cs (07장) — 필드 추가
[SerializeField] private PlayerStats stats;

// OnTriggerStay2D 안의 health.TakeDamage(enemy.Data.contactDamage); 한 줄 교체
health.TakeDamage(stats.Stats.ModifyIncomingDamage(enemy.Data.contactDamage));
```

**11장 `LevelUpState` 수정**: 필드와 생성자 매개변수를 추가하고 `OnChosen`, `PickThree`를 교체합니다(파일 상단에 `using System.Collections.Generic;` 추가). `Enter`·`Exit`는 16·17장에서 고친 그대로 둡니다.

```csharp
// LevelUpState.cs (11장) — 필드 추가
private readonly PlayerStats stats;

// 생성자 교체 (마지막 매개변수 추가)
public LevelUpState(GameStateMachine machine, IGameState playingState,
                    LevelUpPanel panel, UpgradeData[] pool, PlayerStats stats)
{
    this.machine = machine;
    this.playingState = playingState;
    this.panel = panel;
    this.pool = pool;
    this.stats = stats;
}

// OnChosen 교체 — 11장의 "효과 적용은 23장에서"를 실제 적용으로
private void OnChosen(UpgradeData chosen)
{
    stats.Apply(chosen.kind);
    machine.ChangeState(playingState);
}

// PickThree 교체 — 지금 적용할 수 없는 강화(투사체 최대)는 제시하지 않음 (시뮬레이터와 같은 규칙)
private void PickThree()
{
    var candidates = new List<UpgradeData>(pool.Length);
    foreach (UpgradeData u in pool)
        if (u != null && stats.CanApply(u.kind)) candidates.Add(u);

    for (int i = 0; i < picks.Length; i++)   // 부분 Fisher–Yates (06장)
    {
        if (i >= candidates.Count) { picks[i] = null; continue; }
        int j = Random.Range(i, candidates.Count);
        (candidates[i], candidates[j]) = (candidates[j], candidates[i]);
        picks[i] = candidates[i];
    }
}
```

**04장 `GameStateMachine` 수정**: `[SerializeField] private PlayerStats playerStats;` 필드를 추가하고 `Awake`의 생성 줄을 `LevelUp = new LevelUpState(this, Playing, levelUpView, upgradePool, playerStats);`로 바꿉니다.

에디터 연결:

1. Player에 `PlayerStats`를 추가합니다(Base Max Hp 100). `ApplyPermanentUpgrades`는 제거합니다.
2. Player의 `AutoAimWeapon` **Stats**, `PlayerContactDamage` **Stats**에 Player를 드래그합니다.
3. `GameSystems`의 `GameStateMachine` **Player Stats**에 Player, **Upgrade Pool**에 7종 에셋을 넣습니다.

### 6단계: 판 지갑과 코인 제단

**10장 `RunRecorder` 교체**: 지금까지는 "주운 코인 전부"를 이월했습니다. 제단이 생기면 이월하는 것은 **지갑(주운 코인 − 제단에서 쓴 코인)**이고, 클리어하면 ×1.5입니다. 21장 기획서의 "중도 종료해도 지갑 100% 이월"도 여기서 구현합니다. 판의 시작을 한 곳에서만 알리도록 `BeginRun`을 두고, 24·25장이 이 지점을 씁니다.

```csharp
using System;
using UnityEngine;

// Assets/_CoinRush/Scripts/Save/RunRecorder.cs  (10장 파일 교체)
public class RunRecorder : MonoBehaviour
{
    public const float ClearCoinBonus = 1.5f;

    [SerializeField] private IntEventChannel coinCollected;
    [SerializeField] private VoidEventChannel runEnded;       // 04장 Result 상태가 Raise
    [SerializeField] private EnemySpawner spawner;            // 22장 RunTimeCompleted = 클리어
    [SerializeField] private PlayerExperience experience;     // 11장

    public static event Action<RunRecorder> RunStarted;       // 새 판 시작 (한 판에 한 번)
    public static event Action<RunRecorder> RunFinished;      // 정산 직후 (한 판에 한 번)

    public string RunId { get; private set; }
    public bool IsRunning { get; private set; }
    public bool Cleared { get; private set; }
    public string EndReason { get; private set; }             // "death" / "clear" / "quit"
    public float Seconds { get; private set; }
    public int CoinsCollected { get; private set; }
    public int Wallet { get; private set; }
    public int ShrinesOpened { get; private set; }
    public int ShrinePurchases { get; private set; }
    public int Banked { get; private set; }                   // 정산으로 세이브에 더한 코인
    public int Level => experience != null ? experience.Level : 1;

    private bool committed;

    private void OnEnable()
    {
        coinCollected.OnRaised += OnCoinCollected;
        runEnded.OnRaised += CommitFromResult;
        spawner.RunTimeCompleted += OnRunTimeCompleted;
    }

    private void OnDisable()
    {
        coinCollected.OnRaised -= OnCoinCollected;
        runEnded.OnRaised -= CommitFromResult;
        spawner.RunTimeCompleted -= OnRunTimeCompleted;
    }

    /// <summary>04장 GameStateMachine.StartGame에서만 호출. LevelUp → Playing 복귀는 여기를 거치지 않는다.</summary>
    public void BeginRun()
    {
        if (IsRunning || committed) return;   // Game 씬 하나 = 판 하나 (재시작은 09장 씬 재로드)
        IsRunning = true;
        RunId = Guid.NewGuid().ToString("N");
        RunStarted?.Invoke(this);
    }

    private void Update()
    {
        if (IsRunning) Seconds += Time.deltaTime;   // 일시정지·레벨업(timeScale 0) 시간 제외
    }

    private void OnCoinCollected(int amount)
    {
        if (!IsRunning) return;
        CoinsCollected += amount;
        Wallet += amount;
    }

    private void OnRunTimeCompleted() => Cleared = true;

    /// <summary>제단이 열릴 때 호출 → 몇 번째 제단인지 (가격 계산용)</summary>
    public int OpenShrine() => ++ShrinesOpened;

    public bool TrySpend(int price)
    {
        if (!IsRunning || Wallet < price) return false;
        Wallet -= price;
        ShrinePurchases++;
        return true;
    }

    // RunTimeCompleted 구독 순서에 따라 Result 진입이 Cleared 설정보다 먼저 올 수 있으므로 스포너 상태도 확인
    private void CommitFromResult() => Commit(Cleared || spawner.IsCompleted ? "clear" : "death");

    // 판 도중 앱 종료·타이틀 복귀(씬 언로드)도 사망과 같게 정산 — 21장 "언제 끊어도 손해 보지 않는다"
    private void OnApplicationQuit() => Commit("quit");
    private void OnDestroy() => Commit("quit");

    private void Commit(string reason)
    {
        if (!IsRunning || committed) return;   // 결과 이벤트·종료·언로드가 겹쳐도 한 번만
        committed = true;
        IsRunning = false;
        EndReason = reason;
        Cleared = reason == "clear";
        Banked = Mathf.RoundToInt(Wallet * (reason == "clear" ? ClearCoinBonus : 1f));

        SaveData save = SaveSystem.Load();
        save.coins += Banked;
        save.stats.bestSurvivalSeconds = Mathf.Max(save.stats.bestSurvivalSeconds, Seconds);
        save.stats.totalRuns++;
        SaveSystem.Save(save);                 // 재화 변화는 즉시 저장

        RunFinished?.Invoke(this);
    }
}
```

모바일에서 앱이 백그라운드에서 강제 종료되면 `OnApplicationQuit`·`OnDestroy`가 불리지 않아 그 판의 지갑은 사라집니다. Steam 1차 출시에서는 허용 범위로 두고, 모바일 확장 때는 `OnApplicationPause(true)`에서 지갑을 임시 저장하는 방식을 검토합니다.

**04장 `GameStateMachine` 수정**: 판 시작 지점을 하나로 만듭니다.

```csharp
// GameStateMachine.cs (04장) — 필드·프로퍼티 추가
[SerializeField] private RunRecorder runRecorder;
public RunRecorder RunRecorder => runRecorder;

// StartGame 교체
public void StartGame()
{
    if (Current != Title) return;
    runRecorder.BeginRun();     // 새 판의 유일한 시작 지점
    ChangeState(Playing);
}
```

11장 `ResultState.Enter`의 결과 표시 줄을 아래로 바꿉니다. 바로 위의 `RunEnded.Raise()`가 정산을 끝낸 뒤라 `Banked`가 확정되어 있습니다(`ResultView`의 "획득 코인" 문구는 "이월 코인"으로 바꿉니다).

```csharp
// ResultState.Enter (11장) — ResultView.Show 줄 교체
RunRecorder run = machine.RunRecorder;
machine.ResultView.Show(run.Cleared, run.Seconds, run.Banked);
```

**코인 제단**: 22장 스포너가 `Shrine` 이벤트를 시작하면 플레이어 근처에 제단을 세우고, 플레이어가 닿으면 게임을 멈추고 3택1 구매 창을 엽니다. 창에는 가격·지갑과 함께 "모으면 판 끝에 이월"을 보여줍니다(24장 가상 테스트의 교훈). 파일: `Assets/_CoinRush/Scripts/Economy/CoinShrine.cs`

```csharp
using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

/// <summary>24장 기록용 제단 방문 한 번의 요약</summary>
public struct ShrineVisit
{
    public float timeSeconds, hpRatio, dwellSeconds;
    public int shrineIndex, price, walletBefore;
    public bool affordable, purchased;
    public string choice;                 // 구매한 강화 에셋 이름, 안 샀으면 ""
    public string offered;                // 제시된 강화 이름들 (쉼표 구분)
}

public class CoinShrine : MonoBehaviour
{
    [SerializeField] private EnemySpawner spawner;
    [SerializeField] private RunRecorder recorder;
    [SerializeField] private ProgressionData progression;
    [SerializeField] private PlayerStats playerStats;
    [SerializeField] private UpgradeData[] offerPool;           // 레벨업과 같은 7종 에셋
    [SerializeField] private Transform marker;                  // 씬의 노란 사각형 (비활성으로 시작)
    [SerializeField] private float useRadius = 1.2f;
    [SerializeField] private float spawnDistance = 4f;

    [Header("UI (PopupCanvas 아래 패널)")]
    [SerializeField] private GameObject panel;
    [SerializeField] private TMP_Text infoText;
    [SerializeField] private Button[] offerButtons = new Button[3];
    [SerializeField] private TMP_Text[] offerLabels = new TMP_Text[3];
    [SerializeField] private Button keepButton;                 // "모으기"

    public event Action<ShrineVisit> VisitClosed;

    private readonly UpgradeData[] offers = new UpgradeData[3];
    private readonly List<UpgradeData> candidates = new List<UpgradeData>();
    private ShrineVisit visit;
    private float closeAt;
    private bool usedThisShrine;
    private float openedAt;

    private void Awake()
    {
        panel.SetActive(false);
        marker.gameObject.SetActive(false);
        for (int i = 0; i < offerButtons.Length; i++)
        {
            int index = i;                                       // 람다 캡처용 지역 변수
            offerButtons[i].onClick.AddListener(() => Buy(index));
        }
        keepButton.onClick.AddListener(() => Close(purchased: false, chosen: null));
    }

    private void OnEnable() => spawner.EventStarted += OnWaveEvent;

    private void OnDisable()
    {
        spawner.EventStarted -= OnWaveEvent;
        if (panel.activeSelf) GameFeel.ReleasePause(this);      // 창이 열린 채 씬이 닫혀도 정지 해제
    }

    private void OnWaveEvent(WaveEvent e)
    {
        if (e.type != WaveEventType.Shrine || !recorder.IsRunning) return;
        visit = new ShrineVisit { shrineIndex = recorder.OpenShrine() };
        visit.price = progression.ShrinePrice(visit.shrineIndex);

        Vector2 dir = UnityEngine.Random.insideUnitCircle;
        if (dir.sqrMagnitude < 0.01f) dir = Vector2.up;
        marker.position = (Vector2)playerStats.transform.position + dir.normalized * spawnDistance;
        marker.gameObject.SetActive(true);
        closeAt = spawner.Elapsed + e.activeSeconds;             // 21장: 30초 유지
        usedThisShrine = false;
    }

    private void Update()
    {
        if (!marker.gameObject.activeSelf || panel.activeSelf) return;
        if (spawner.Elapsed >= closeAt) { marker.gameObject.SetActive(false); return; }
        if (usedThisShrine) return;

        Vector2 toPlayer = (Vector2)playerStats.transform.position - (Vector2)marker.position;
        if (toPlayer.sqrMagnitude <= useRadius * useRadius) Open();
    }

    private void Open()
    {
        usedThisShrine = true;
        GameFeel.RequestPause(this);                             // 17장 소유자별 정지
        PickOffers();

        visit.timeSeconds = spawner.Elapsed;
        visit.hpRatio = playerStats.HpRatio;
        visit.walletBefore = recorder.Wallet;
        visit.affordable = recorder.Wallet >= visit.price;
        openedAt = Time.unscaledTime;

        infoText.text = $"제단 강화 {visit.price} 코인 (지갑 {recorder.Wallet})\n" +
                        "사면 이번 판에서 강해지고, 모으면 판이 끝날 때 영구 강화 재화로 이월됩니다.";
        for (int i = 0; i < offerButtons.Length; i++)
        {
            bool has = offers[i] != null;
            offerButtons[i].gameObject.SetActive(has);
            if (!has) continue;
            offerLabels[i].text = offers[i].displayName;
            offerButtons[i].interactable = visit.affordable;
        }
        panel.SetActive(true);
        if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(keepButton.gameObject);
    }

    private void PickOffers()
    {
        candidates.Clear();
        foreach (UpgradeData u in offerPool)
            if (u != null && playerStats.CanApply(u.kind)) candidates.Add(u);
        var names = new List<string>(3);
        for (int i = 0; i < offers.Length; i++)
        {
            offers[i] = null;
            if (i >= candidates.Count) continue;
            int j = UnityEngine.Random.Range(i, candidates.Count);
            (candidates[i], candidates[j]) = (candidates[j], candidates[i]);
            offers[i] = candidates[i];
            names.Add(offers[i].name);
        }
        visit.offered = string.Join(",", names);
    }

    private void Buy(int index)
    {
        UpgradeData chosen = offers[index];
        if (chosen == null || !panel.activeSelf || !recorder.TrySpend(visit.price)) return;
        playerStats.Apply(chosen.kind, progression.shrineStacks);   // 시뮬레이터와 같은 stacks
        Close(purchased: true, chosen: chosen);
    }

    private void Close(bool purchased, UpgradeData chosen)
    {
        if (!panel.activeSelf) return;                           // 버튼 연타 방지
        panel.SetActive(false);
        marker.gameObject.SetActive(false);
        GameFeel.ReleasePause(this);

        visit.purchased = purchased;
        visit.choice = chosen != null ? chosen.name : "";
        visit.dwellSeconds = Time.unscaledTime - openedAt;
        VisitClosed?.Invoke(visit);
    }
}
```

에디터 연결:

1. Game 씬에 2D Sprite(Square) `ShrineMarker`를 만들고 노랗게 칠한 뒤 크기 1.5로 **비활성화**합니다. 콜라이더는 필요 없습니다(거리로 판정).
2. 11장 `PopupCanvas` 아래에 `ShrinePanel`(반투명 배경)을 만들고 자식으로 `InfoText`(TMP), 버튼 3개(각각 자식 TMP 텍스트), `Keep` 버튼("모으기")을 둡니다. 패널은 비활성으로 둡니다.
3. `GameSystems` 아래 빈 오브젝트 `CoinShrine`에 컴포넌트를 붙이고 Spawner, Recorder(`RunRecorder`가 붙은 오브젝트), Progression, Player Stats(Player), Offer Pool(7종), Marker, Panel, Info Text, Offer Buttons·Offer Labels 각 3칸, Keep Button을 연결합니다.
4. `RunRecorder`의 **Spawner**, **Experience**(Player), `GameStateMachine`의 **Run Recorder**를 연결합니다.

### 7단계: BalanceSimulator.cs (전체 코드)

게임과 같은 `UpgradeRules.cs`를 씁니다. UnityEngine에 의존하지 않으므로 Unity 에디터 메뉴에서도, `dotnet new console`로 만든 콘솔 프로젝트에 두 파일을 복사해서도 돌릴 수 있습니다(JS: 브라우저 API를 안 쓰는 순수 함수 모듈을 Node에서도 테스트하는 것과 같습니다). 파일: `Assets/_CoinRush/Scripts/Balance/BalanceSimulator.cs`

```csharp
using System;
using System.Collections.Generic;
using System.Text;

public enum ShrinePolicy { Never, Always, WhenHurt }

/// <summary>WaveSegment 하나의 평균값. avgHp는 체력 배율 적용 후.</summary>
public class SimSegment
{
    public int start, end, maxAlive;
    public float spawnsPerSecond, avgHp, avgContact, avgCoin;
    public float bomberShare, wardenShare;    // 22장 역할별 가중치 비율 (0~1)
}

/// <summary>엘리트·보스·떼·도입. 일반 적과 섞지 않고 "개체"로 추적한다.</summary>
public class SimEvent
{
    public int time, count;
    public float hpEach, contact, coinEach;   // hpEach는 배율 적용 후
    public bool blastOnDeath, slowField;      // 22장 폭탄충 / 주술사
}

public class SimConfig
{
    public List<SimSegment> segments = new List<SimSegment>();   // start 오름차순, 빈틈 없이
    public List<SimEvent> events = new List<SimEvent>();         // time 오름차순
    public List<int> shrineTimes = new List<int>();              // 제단이 열리는 초
    public int runSeconds = 600;

    // 플레이어 (22장 시작 무기, 예시 수치)
    public int baseDamage = 10;
    public float baseCooldown = 1f, baseMaxHp = 100f;

    // ── 플레이 능력 가정: 실측(24장)으로 보정할 계수 ──
    public float hitEfficiency = 0.8f;          // 명중 효율
    public float basePickupRate = 0.6f;         // 떨어진 코인 중 줍는 비율
    public float dodgeCapacity = 10f;           // 이만큼의 일반 적까지는 피한다
    public float hitChancePerExcessEnemy = 0.03f;
    public float eventHitChancePerSecond = 0.1f;   // 엘리트·보스 한 마리가 초당 접촉에 성공할 확률

    // ── 22장 10단계 메커닉의 근사 (개념 절 "몬테카를로 시뮬레이션과 그 한계"의 표) ──
    public float blastDamage = 18f;             // BombBlast.damage (22장 11단계 v3)
    public float blastHitChance = 0.08f;        // 폭발 한 번에 맞을 확률 — 위치가 없으므로 확률로 대체
    public float slowPerWarden = 0.05f;         // 주술사 1마리당 회피 한계 감소율
    public float maxSlowPenalty = 0.4f;         // 상한 40% (22장 장판 ×0.6과 같은 폭)

    // 경험치 곡선 (ProgressionData와 같은 공식)
    public XpCurve xpCurve = XpCurve.Exponential;
    public float xpBase = 5f, xpGrowth = 1.25f, xpScale = 1f, xpPower = 1.5f;

    // 코인 제단 (가격 = shrineBasePrice × 몇 번째 제단인지)
    public ShrinePolicy shrinePolicy = ShrinePolicy.Never;
    public int shrineBasePrice = 50, shrineStacks = 1;
    public float clearCoinBonus = 1.5f;

    // 영구 강화 3종 레벨
    public int metaDamageLevel, metaHpLevel, metaMagnetLevel;

    public int XpToNext(int level) => ProgressionRules.XpToNext(xpCurve, xpBase, xpGrowth, xpScale, xpPower, level);

    public SimConfig ShallowCopy() => (SimConfig)MemberwiseClone();
}

public struct RunResult
{
    public int survivedSeconds, level, shrinePurchases;
    public float coinsCollected, coinsBanked;
    public bool cleared;
}

public class SimReport
{
    public string label;
    public int runs;
    public readonly int[] endMinuteHistogram = new int[11];   // [0~9] 해당 분에 사망, [10] 클리어
    public float clearRate, medianSeconds, avgLevel, avgCollected, avgBanked, avgShrine;

    public override string ToString()
    {
        var sb = new StringBuilder();
        sb.AppendLine($"[{label}] {runs}판  클리어 {clearRate:P1}  생존 중앙값 {medianSeconds:0}초  평균 레벨 {avgLevel:0.0}  " +
                      $"평균 수집 {avgCollected:0}  평균 이월 {avgBanked:0}  제단 구매 {avgShrine:0.0}회");
        sb.Append("  분별 사망: ");
        for (int m = 0; m < 10; m++) sb.Append($"{m}분 {endMinuteHistogram[m]} | ");
        sb.Append($"클리어 {endMinuteHistogram[10]}");
        return sb.ToString();
    }
}

public static class BalanceSimulator
{
    private static readonly UpgradeKind[] AllKinds = (UpgradeKind[])Enum.GetValues(typeof(UpgradeKind));

    public static SimReport RunMany(string label, SimConfig c, int runs, int seed)
    {
        var rng = new Random(seed);   // 같은 seed → 같은 결과 (조정 전후 비교가 공정해짐)
        var results = new RunResult[runs];
        for (int i = 0; i < runs; i++) results[i] = SimulateRun(c, rng);
        return Summarize(label, results);
    }

    public static RunResult SimulateRun(SimConfig c, Random rng)
    {
        var stats = new CombatStats(c.metaDamageLevel, c.metaHpLevel, c.metaMagnetLevel);
        float hp = c.baseMaxHp + stats.MaxHpBonus;
        float xp = 0f, wallet = 0f, collected = 0f, normalHp = 0f;
        int level = 1, segIndex = 0, eventIndex = 0, shrineIndex = 0, purchases = 0;
        var eventHp = new List<float>();        // 살아 있는 이벤트 적 개체별 남은 체력
        var eventInfo = new List<SimEvent>();
        var options = new List<UpgradeKind>(AllKinds.Length);

        for (int t = 0; t < c.runSeconds; t++)
        {
            // 매초 실제 구간 경계로 조회 (분 단위 평균을 쓰지 않는다)
            while (segIndex < c.segments.Count - 1 && t >= c.segments[segIndex].end) segIndex++;
            SimSegment s = c.segments[segIndex];
            float pickup = Math.Min(1f, c.basePickupRate * stats.MagnetMul);

            // 1) 유입: 일반 적은 maxAlive를 넘는 만큼 버린다 (22장 스포너와 같은 규칙)
            normalHp = Math.Min(normalHp + s.spawnsPerSecond * s.avgHp, s.maxAlive * s.avgHp);
            while (eventIndex < c.events.Count && c.events[eventIndex].time <= t)
            {
                SimEvent e = c.events[eventIndex++];
                for (int i = 0; i < e.count; i++) { eventHp.Add(e.hpEach); eventInfo.Add(e); }
            }

            // 2) 처치: 자동 조준은 가까운 적부터 쏘므로 남은 체력 비율대로 피해가 나뉜다고 가정
            float blasts = 0f;   // 이 초에 터진 폭탄충 수 (일반 적 처치분 + 이벤트 개체)
            float dps = stats.Dps(c.baseDamage, c.baseCooldown, c.hitEfficiency);
            float eventTotal = 0f;
            foreach (float h in eventHp) eventTotal += h;
            float total = normalHp + eventTotal;
            if (total > 0f)
            {
                float toNormal = dps * normalHp / total;
                float killed = Math.Min(normalHp, toNormal);
                normalHp -= killed;
                float normalKills = killed / s.avgHp;
                blasts += normalKills * s.bomberShare;      // 죽은 일반 적 중 폭탄충 비율만큼 폭발
                float coins = normalKills * s.avgCoin * pickup;

                float toEvents = dps - toNormal;
                for (int i = 0; i < eventHp.Count && toEvents > 0f; )
                {
                    float dealt = Math.Min(eventHp[i], toEvents);
                    eventHp[i] -= dealt; toEvents -= dealt;
                    if (eventHp[i] <= 0f)
                    {
                        coins += eventInfo[i].coinEach * pickup;
                        if (eventInfo[i].blastOnDeath) blasts += 1f;   // 7:30 폭탄충 포위
                        eventHp.RemoveAt(i); eventInfo.RemoveAt(i);
                    }
                    else i++;
                }
                collected += coins; wallet += coins; xp += coins;
            }

            // 3) 피격: 일반 적은 회피 한계를 넘은 수만큼, 이벤트 적은 개체마다, 폭탄충은 터진 수만큼
            float maxHp = c.baseMaxHp + stats.MaxHpBonus;
            float onScreen = normalHp / s.avgHp;

            // 주술사 장판 = 회피 한계 감소 (위치를 모르므로 "살아 있는 수"로만 근사)
            float wardens = onScreen * s.wardenShare;
            foreach (SimEvent e in eventInfo) if (e.slowField) wardens += 1f;
            float dodge = c.dodgeCapacity * (1f - Math.Min(c.maxSlowPenalty, wardens * c.slowPerWarden));

            float taken = Math.Max(0f, onScreen - dodge) * s.avgContact * c.hitChancePerExcessEnemy;
            foreach (SimEvent e in eventInfo) taken += e.contact * c.eventHitChancePerSecond;
            taken += blasts * c.blastDamage * c.blastHitChance;
            hp = Math.Min(maxHp, hp - taken * stats.DamageTakenMul + stats.RegenPerSecond);
            if (hp <= 0f)
                return new RunResult { survivedSeconds = t, level = level, shrinePurchases = purchases,
                                       coinsCollected = collected, coinsBanked = wallet };

            // 4) 레벨업: 제시 가능한 강화 중 무작위 3개 → 랜덤 봇이 무작위 선택
            while (xp >= c.XpToNext(level))
            {
                xp -= c.XpToNext(level);
                level++;
                UpgradeKind pick = PickRandomOffer(stats, options, rng);
                float before = stats.MaxHpBonus;
                stats.Apply(pick);
                hp += stats.MaxHpBonus - before;   // 최대 체력 증가분만큼 현재 체력도 증가
            }

            // 5) 코인 제단: 같은 규칙(가격, 3택1, stacks)으로 구매
            if (shrineIndex < c.shrineTimes.Count && t >= c.shrineTimes[shrineIndex])
            {
                shrineIndex++;
                int price = c.shrineBasePrice * shrineIndex;
                bool want = c.shrinePolicy == ShrinePolicy.Always
                            || (c.shrinePolicy == ShrinePolicy.WhenHurt && hp < maxHp * 0.6f);
                if (want && wallet >= price)
                {
                    wallet -= price;
                    purchases++;
                    UpgradeKind pick = PickRandomOffer(stats, options, rng);
                    float before = stats.MaxHpBonus;
                    stats.Apply(pick, c.shrineStacks);
                    hp += stats.MaxHpBonus - before;
                }
            }
        }

        return new RunResult
        {
            survivedSeconds = c.runSeconds, level = level, shrinePurchases = purchases, cleared = true,
            coinsCollected = collected, coinsBanked = wallet * c.clearCoinBonus
        };
    }

    private static UpgradeKind PickRandomOffer(CombatStats stats, List<UpgradeKind> options, Random rng)
    {
        options.Clear();
        foreach (UpgradeKind k in AllKinds)
            if (stats.CanApply(k)) options.Add(k);
        int offer = Math.Min(3, options.Count);
        for (int i = 0; i < offer; i++)   // 부분 피셔-예이츠: 앞 3칸이 제시된 선택지
        {
            int j = rng.Next(i, options.Count);
            (options[i], options[j]) = (options[j], options[i]);
        }
        return options[rng.Next(offer)];
    }

    /// <summary>영구 강화 3종을 "가장 낮은 것부터" 사 가며 여러 판을 이어 하는 캠페인.</summary>
    /// <returns>index L = 세 강화가 모두 L레벨 이상이 된 판 번호 (도달 못 하면 -1). [0] = 첫 클리어 판.</returns>
    public static int[] SimulateCampaign(SimConfig baseConfig, Func<int, int> upgradeCost,
                                         int maxLevel, int seed, int maxRuns = 400)
    {
        var rng = new Random(seed);
        var reachedAt = new int[maxLevel + 1];
        for (int i = 0; i < reachedAt.Length; i++) reachedAt[i] = -1;

        SimConfig c = baseConfig.ShallowCopy();
        c.metaDamageLevel = c.metaHpLevel = c.metaMagnetLevel = 0;
        float bank = 0f;

        for (int run = 1; run <= maxRuns; run++)
        {
            RunResult r = SimulateRun(c, rng);
            bank += r.coinsBanked;
            if (r.cleared && reachedAt[0] < 0) reachedAt[0] = run;

            while (true)
            {
                int lowest = Math.Min(c.metaDamageLevel, Math.Min(c.metaHpLevel, c.metaMagnetLevel));
                int next = lowest + 1;
                if (next > maxLevel || bank < upgradeCost(next)) break;
                bank -= upgradeCost(next);
                if (c.metaDamageLevel == lowest) c.metaDamageLevel++;
                else if (c.metaHpLevel == lowest) c.metaHpLevel++;
                else c.metaMagnetLevel++;
            }

            int all = Math.Min(c.metaDamageLevel, Math.Min(c.metaHpLevel, c.metaMagnetLevel));
            for (int l = 1; l <= all; l++) if (reachedAt[l] < 0) reachedAt[l] = run;
            if (all >= maxLevel) break;
        }
        return reachedAt;
    }

    private static SimReport Summarize(string label, RunResult[] results)
    {
        var report = new SimReport { label = label, runs = results.Length };
        var seconds = new int[results.Length];
        float levels = 0f, collected = 0f, banked = 0f, shrine = 0f;
        for (int i = 0; i < results.Length; i++)
        {
            RunResult r = results[i];
            seconds[i] = r.survivedSeconds;
            report.endMinuteHistogram[r.cleared ? 10 : Math.Min(9, r.survivedSeconds / 60)]++;
            levels += r.level; collected += r.coinsCollected; banked += r.coinsBanked; shrine += r.shrinePurchases;
        }
        Array.Sort(seconds);
        report.clearRate = report.endMinuteHistogram[10] / (float)results.Length;
        report.medianSeconds = seconds[seconds.Length / 2];
        report.avgLevel = levels / results.Length;
        report.avgCollected = collected / results.Length;
        report.avgBanked = banked / results.Length;
        report.avgShrine = shrine / results.Length;
        return report;
    }
}
```

### 8단계: 에디터 메뉴 러너

`WaveData`와 `ProgressionData` 에셋에서 `SimConfig`를 만들어 여러 시나리오를 한 번에 돌립니다. 파일: `Assets/_CoinRush/Scripts/Editor/BalanceSimulatorMenu.cs`

```csharp
using System.Diagnostics;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

public static class BalanceSimulatorMenu
{
    private const int Runs = 1000, Seed = 42;

    [MenuItem("Coin Rush/Balance/Run Simulator (1000 runs)")]
    private static void Run()
    {
        var wave = (WaveData)Selection.activeObject;
        ProgressionData prog = FindAsset<ProgressionData>();
        if (prog == null) { Debug.LogError("ProgressionData 에셋이 없습니다."); return; }

        SimConfig baseConfig = BuildConfig(wave, prog);
        var watch = Stopwatch.StartNew();
        var log = new StringBuilder();

        log.AppendLine(BalanceSimulator.RunMany("기준 가정 (제단 안 삼)", baseConfig, Runs, Seed).ToString());

        SimConfig always = baseConfig.ShallowCopy();
        always.shrinePolicy = ShrinePolicy.Always;
        log.AppendLine(BalanceSimulator.RunMany("제단 항상 삼", always, Runs, Seed).ToString());

        SimConfig hurt = baseConfig.ShallowCopy();
        hurt.shrinePolicy = ShrinePolicy.WhenHurt;
        log.AppendLine(BalanceSimulator.RunMany("체력 60% 미만일 때만 삼", hurt, Runs, Seed).ToString());

        foreach (int meta in new[] { 1, 3, 5, 10 })
        {
            SimConfig m = baseConfig.ShallowCopy();
            m.metaDamageLevel = m.metaHpLevel = m.metaMagnetLevel = meta;
            log.AppendLine(BalanceSimulator.RunMany($"영구 강화 3종 {meta}레벨", m, Runs, Seed).ToString());
        }

        // 가정의 폭: 계수만 바꾼 초보·숙련 시나리오 (24장 실측으로 보정하기 전까지는 탐색용)
        SimConfig novice = baseConfig.ShallowCopy();
        novice.hitEfficiency = 0.65f; novice.dodgeCapacity = 6f; novice.basePickupRate = 0.5f;
        log.AppendLine(BalanceSimulator.RunMany("초보 가정", novice, Runs, Seed).ToString());
        SimConfig skilled = baseConfig.ShallowCopy();
        skilled.hitEfficiency = 0.9f; skilled.dodgeCapacity = 16f; skilled.basePickupRate = 0.7f;
        log.AppendLine(BalanceSimulator.RunMany("숙련 가정", skilled, Runs, Seed).ToString());

        int[] reached = BalanceSimulator.SimulateCampaign(baseConfig, prog.UpgradeCost, prog.upgradeMaxLevel, Seed);
        log.AppendLine($"[캠페인 seed {Seed}] 첫 클리어 {reached[0]}판 | 3종 1레벨 {reached[1]}판 | 3레벨 {reached[3]}판 | " +
                       $"5레벨 {reached[5]}판 | {prog.upgradeMaxLevel}레벨 {reached[prog.upgradeMaxLevel]}판");
        log.AppendLine($"소요 {watch.ElapsedMilliseconds} ms");

        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Balance"));
        Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, $"sim_{System.DateTime.Now:yyyyMMdd_HHmmss}.txt"), log.ToString(), Encoding.UTF8);
        Debug.Log(log.ToString());
    }

    [MenuItem("Coin Rush/Balance/Run Simulator (1000 runs)", true)]
    private static bool Validate() => Selection.activeObject is WaveData;

    public static SimConfig BuildConfig(WaveData wave, ProgressionData prog)
    {
        var c = new SimConfig
        {
            runSeconds = Mathf.RoundToInt(wave.runDuration),
            xpCurve = prog.xpCurve, xpBase = prog.xpBase, xpGrowth = prog.xpGrowth,
            xpScale = prog.xpScale, xpPower = prog.xpPower,
            shrineBasePrice = prog.shrineBasePrice, shrineStacks = prog.shrineStacks
        };

        // 분 단위 평균이 아니라 WaveData의 실제 구간 경계를 그대로 옮긴다 (30초 구간도 정확)
        foreach (WaveSegment seg in wave.segments)
        {
            var s = new SimSegment
            {
                start = Mathf.RoundToInt(seg.startTime), end = Mathf.RoundToInt(seg.endTime),
                spawnsPerSecond = seg.spawnsPerSecond, maxAlive = seg.maxAlive
            };
            float total = seg.TotalWeight();
            foreach (SpawnEntry e in seg.entries)
            {
                if (e.enemy == null || total <= 0f) continue;
                float w = e.weight / total;
                s.avgHp += e.enemy.maxHp * w;
                s.avgContact += e.enemy.contactDamage * w;
                s.avgCoin += e.enemy.coinDrop * w;
                if (Explodes(e.enemy)) s.bomberShare += w;                        // 22장 폭탄충
                if (e.enemy.role == EnemyRole.Zoner) s.wardenShare += w;          // 22장 주술사
            }
            s.avgHp *= seg.hpMultiplier;
            c.segments.Add(s);
        }

        foreach (WaveEvent e in wave.events)
        {
            if (e.type == WaveEventType.Shrine) { c.shrineTimes.Add(Mathf.RoundToInt(e.time)); continue; }
            if (e.enemy == null) continue;   // Elite·Boss·Swarm·Introduce 모두 같은 규칙으로 개체 추적
            float segMul = wave.GetSegment(e.time)?.hpMultiplier ?? 1f;
            c.events.Add(new SimEvent
            {
                time = Mathf.RoundToInt(e.time), count = e.count,
                hpEach = e.enemy.maxHp * segMul * e.hpMultiplier,
                contact = e.enemy.contactDamage, coinEach = e.enemy.coinDrop,
                blastOnDeath = Explodes(e.enemy), slowField = e.enemy.role == EnemyRole.Zoner
            });
        }
        c.events.Sort((a, b) => a.time.CompareTo(b.time));
        c.shrineTimes.Sort();
        return c;
    }

    /// <summary>폭발은 프리팹의 ExploderOnDeath가 정한다 (22장 10-2) — 에셋을 진실의 원천으로 유지</summary>
    private static bool Explodes(EnemyData enemy) =>
        enemy.prefab != null && enemy.prefab.GetComponent<ExploderOnDeath>() != null;

    private static T FindAsset<T>() where T : Object
    {
        string[] guids = AssetDatabase.FindAssets($"t:{typeof(T).Name}");
        return guids.Length == 0 ? null : AssetDatabase.LoadAssetAtPath<T>(AssetDatabase.GUIDToAssetPath(guids[0]));
    }
}
```

`WaveSegment`는 `UnityEngine.Object`가 아닌 일반 클래스라서 `?.`와 `??`를 안전하게 쓸 수 있습니다(Unity 오브젝트에는 쓰지 마세요 — 기초 트랙 PART 5 지뢰 3번). 22장 연습 문제처럼 9:30에 보너스 러시 구간을 새로 만들면, 시뮬레이터도 9:00이 아니라 9:30부터 그 구간을 적용합니다.

폭발 여부를 `EnemyRole`이 아니라 **프리팹의 `ExploderOnDeath` 유무**로 판단하는 것에 주의하세요. 22장에서 폭탄충·엘리트·보스가 모두 `Priority`이므로 역할만으로는 구분되지 않고, "죽을 때 터지는가"는 역할이 아니라 프리팹 구성입니다. 나중에 터지는 적을 하나 더 만들어도 시뮬레이터 코드는 그대로입니다.

### 9단계: 실행하고 해석하고 조정하기

1. Project 창에서 `Wave_Stage1`을 선택하고 **Coin Rush → Balance → Run Simulator** 를 실행합니다.
2. Console과 `Balance/sim_*.txt`에 결과가 나옵니다. 보통 몇 초 안에 끝납니다.

**조정 목표 (돌리기 전에 `Docs/balance-log.md`에 적음, 기준 가정·강화 0·제단 안 삼)**: 클리어율 20~35%, 어느 한 분에 사망 25% 이하, 생존 중앙값 6~9분, 한 판 평균 이월 600~900.

아래는 필자가 이 장의 코드와 **22장 10단계 수정 후 웨이브 표**로 돌린 **실행 결과**입니다(지면을 줄이려고 0인 칸은 생략). 22장 9~11단계를 거치지 않은 옛 표로 돌리면 수치가 다르게 나옵니다. .NET 런타임에 따라 난수 구현이 달라 수치가 몇 %p 달라질 수 있으니 경향만 비교하세요.

**조정 전 (22장 수정 후 웨이브 표 + 11장 지수 경험치)**

```
[기준 가정] 1000판  클리어 6.3%  생존 중앙값 378초  평균 레벨 14.5  평균 수집 553  평균 이월 585
  분별 사망: 2분 29 | 3분 273 | 4분 90 | 5분 25 | 6분 210 | 7분 97 | 8분 12 | 9분 201 | 클리어 63
```

해석:

- **3분(27.3%), 6분(21.0%), 9분(20.1%)에 사망이 몰립니다.** 각각 엘리트 1, 엘리트 2, 보스 등장 시각입니다. 2분(2.9%)은 22장이 새로 넣은 2:05 폭탄충 도입 직후입니다.
- 평균 레벨 14.5 — 1단계 표에서 초안 곡선이 가팔라지기 시작하는 곳입니다. 성장이 막혀 이벤트 적을 뚫을 화력이 부족합니다.
- 원인 후보가 둘(경험치 곡선, 이벤트 체력)이므로 **한 번에 하나씩** 바꿉니다. 둘을 동시에 바꾸면 어느 쪽이 효과였는지 모릅니다.

**조정 1: 경험치 곡선 지수 1.25 → 다항 1.6** (`ProgressionData`의 Xp Curve `Polynomial`, Xp Power 1.6만 수정)

```
[기준 가정] 클리어 24.5%  생존 중앙값 379초  평균 레벨 15.7  평균 수집 596  평균 이월 734
  분별 사망: 2분 42 | 3분 276 | 4분 98 | 5분 19 | 6분 154 | 7분 69 | 8분 11 | 9분 86 | 클리어 245
```

- 클리어율이 3.9배가 되고 9분 사망이 절반 아래로 줄었습니다(201 → 86). 후반 성장 곡선이 주원인 중 하나였습니다.
- 하지만 **3분 사망은 줄지 않았고**(273 → 276) **2분 사망은 오히려 늘었습니다**(29 → 42). 1단계 표에서 본 대로 조정안은 L4~L10 구간이 초안보다 조금 비싸 초반 성장이 느려졌기 때문입니다. 곡선 변경은 구간마다 효과가 다릅니다. 3분 벽은 경험치만으로는 해결되지 않습니다.

**조정 2: 엘리트 이벤트 체력 배율 1.0 → 0.6 (3:00, 6:00)** (`WaveData`의 이벤트 두 줄만 수정)

```
[기준 가정] 클리어 28.4%  생존 중앙값 430초  평균 레벨 16.5  평균 수집 669  평균 이월 829
  분별 사망: 2분 43 | 3분 239 | 4분 72 | 5분 30 | 6분 109 | 7분 72 | 8분 16 | 9분 135 | 클리어 284
```

**여기서 스폰율은 건드리지 않습니다.** 22장 10-8이 경고한 대로 스폰율을 바꾸면 코인 공급이 바뀌어 제단 지갑 상한 표를 다시 계산해야 하고, 구성 가중치를 바꾸면 10-7의 R1·R2 검사가 경계값(70%)에서 바로 깨집니다. 엘리트 **이벤트**의 체력 배율은 구간 위협 곡선에도, 코인 공급 총량에도 영향을 주지 않는(엘리트 한 마리의 코인 30개는 그대로) 가장 좁은 레버입니다.

조정 전후를 한 표로 정리해 `Docs/balance-log.md`에 남깁니다.

| 지표 | 조정 전 | 조정 1 (경험치) | 조정 2 (+엘리트 체력) | 목표 |
|---|---|---|---|---|
| 클리어율 | 6.3% | 24.5% | 28.4% | 20~35% |
| 생존 중앙값 | 378초 | 379초 | 430초 | 360~540초 |
| 3분 사망 비율 | **27.3%** | **27.6%** | 23.9% | 25% 이하 |
| 6분 사망 비율 | 21.0% | 15.4% | 10.9% | 25% 이하 |
| 9분(보스) 사망 비율 | 20.1% | 8.6% | 13.5% | 25% 이하 |
| 평균 레벨 | 14.5 | 15.7 | 16.5 | — |
| 한 판 평균 이월 코인 | 585 | 734 | 829 | 600~900 |

조정 2에서 모든 목표를 통과했습니다. 여기서 멈추고 "기준 가정"이 사람과 맞는지 24장에서 확인합니다.

**가정의 폭** — 같은 실행의 초보·숙련 시나리오입니다. 22장 메커닉이 들어왔으므로 **폭발 적중률도 함께** 움직입니다(초보는 예고 원을 늦게 본다는 가정).

| 시나리오 (명중, 회피, 수집, 폭발 적중) | 클리어율 | 생존 중앙값 | 평균 이월 | 사망이 가장 몰린 분 |
|---|---|---|---|---|
| 초보 가정 (0.65, 6, 0.5, 0.15) | 0.1% | 184초 | 181 | 2분 42.1% |
| **기준 가정** (0.8, 10, 0.6, 0.08) | 28.4% | 430초 | 829 | 3분 23.9% |
| 숙련 가정 (0.9, 16, 0.7, 0.04) | 59.7% | 600초 | 1,479 | 4분 10.3% |

폭이 매우 넓습니다. 계수 조합에 따라 "아무도 못 깨는 게임"부터 "절반 넘게 깨는 게임"까지 나옵니다. 이벤트 적 접촉 확률(`eventHitChancePerSecond`) 하나만 0.10에서 0.15로 올려도 기준 가정 클리어율이 28.4%에서 5.5%로 떨어지고, 폭발 적중률만 0.08에서 0.12로 올려도 24.8%가 됩니다. 그래서 이 표의 결론은 "조정 2가 맞다"가 아니라 **"경험치 곡선과 엘리트 체력의 방향은 모든 가정에서 같은 쪽으로 움직인다, 절대 난이도는 아직 모른다"**입니다. 24장에서 테스터의 실제 사망 시각 분포를 얻으면 세 시나리오 중 어느 쪽에 가까운지 보고 계수를 보정합니다. 참고로 22장 11단계의 자기 테스트 클리어율은 v3에서 **33%(4/12)**였습니다. 표본이 12판뿐이라 계수를 맞출 수는 없지만, 기준 가정(28.4%)과 같은 자릿수라는 점은 확인해 둘 만합니다.

### 10단계: 경제 검증 — 제단 전략과 영구 강화

같은 실행 결과의 나머지 시나리오입니다(조정 2, 기준 가정).

| 시나리오 | 클리어율 | 생존 중앙값 | 평균 이월 코인 | 제단 구매 |
|---|---|---|---|---|
| 제단 안 삼 (기본) | 28.4% | 430초 | 829 | 0회 |
| 제단 항상 삼 | 56.9% | 600초 | 770 | 3.1회 |
| 체력 60% 미만일 때만 삼 | 37.0% | 473초 | 843 | 0.6회 |
| 영구 강화 3종 1레벨 | 44.6% | 584초 | 1,178 | — |
| 영구 강화 3종 3레벨 | 66.1% | 600초 | 1,697 | — |
| 영구 강화 3종 5레벨 | 77.4% | 600초 | 2,071 | — |
| 영구 강화 3종 10레벨 | 89.9% | 600초 | 2,415 | — |

- **제단 긴장이 살아 있습니다.** 항상 사면 클리어율이 2배지만 이월 코인이 7% 줄어듭니다. 어느 쪽도 모든 지표에서 우세하지 않습니다. 다만 22장 수정으로 코인 공급이 약 10% 늘어 **차이가 얇아졌습니다**(옛 표에서는 −19%였습니다). 가격 50×n을 유지하면서 긴장을 되살리려면 제단 가격보다 강화 효과 쪽을 먼저 보게 됩니다 — 12단계 수정 뒤에 다시 잽니다.
- 처음에는 제단 강화를 **2단계**(`shrineStacks = 2`)로 줬습니다. 그때 결과는 "항상 삼: 클리어 66.8%, 이월 969"로, 사는 쪽이 **클리어율도 이월도 높았습니다**(안 삼: 28.4%, 829). 더 오래 살아 더 많이 줍기 때문입니다. 항상 사는 것이 정답이면 21장의 차별점이 무너지므로 1단계로 낮췄습니다. 이런 역전은 표 계산으로는 보이지 않고, 생존과 수집이 얽힌 시뮬레이션에서 드러납니다.
- 영구 강화가 쌓일수록 클리어율과 이월이 함께 오릅니다. 이것이 메타 루프의 가속감입니다. 다만 1레벨만으로 클리어율이 28% → 45%로 크게 뜁니다. 첫 강화의 체감은 좋지만, 24장에서 "두 번째 판이 너무 쉬워졌다"는 반응이 나오는지 함께 봅니다.
- 봇의 "체력 60% 미만일 때만" 정책은 거의 사지 않았고(0.6회), 그런데도 클리어율(37.0%)과 이월(843)이 안 사는 쪽보다 둘 다 높습니다. **봇의 정책이 사람의 판단보다 유리해 보이는 것은 모델의 한계**입니다 — 봇은 체력이 떨어진 바로 그 순간에 제단이 열려 있는지를 공짜로 압니다. 21장이 원하는 "상황에 따라 선택이 바뀌는" 사람의 행동은 24장 관찰의 몫입니다.

캠페인 시뮬레이션(가장 낮은 강화부터 구매)으로 역산 목표를 확인합니다. 메뉴는 seed 하나의 결과만 보여주므로, 아래 표는 seed 0~99로 100번 돌린 중앙값입니다.

| 목표 | 역산 목표 | 기본가 200 (초안) | 기본가 250 | 기본가 300 (채택) |
|---|---|---|---|---|
| 첫 클리어 | 2~4판 | 2판 | 2판 | 2판 |
| 세 강화 모두 1레벨 | 1~2판 | 1판 | 2판 | 2판 |
| 세 강화 모두 3레벨 | — | 3판 | 4판 | 4판 |
| 세 강화 모두 5레벨 | 약 8판 | 6판 | 7판 | 8판 |
| 세 강화 모두 10레벨 | 40~50판 | 32판 | 40판 | 47판 |

초안은 끝까지 너무 빨라 약 5시간 만에 Sink가 바닥납니다. 22장 수정으로 코인 공급이 늘었기 때문에 **옛 표에서 적당했던 250도 이제 40판으로 하단에 붙습니다.** 기본가를 300으로 올려 목표 구간 가운데에 넣었습니다(`ProgressionData.upgradeBaseCost`). **웨이브를 고치면 경제 표가 낡습니다** — 22장이 10-8에서 제단 지갑 표를 다시 계산한 것과 같은 이유입니다. 이 판 수는 **기준 가정**의 결과이므로, 24장의 `upgrade_purchase` 이벤트로 실제 도달 판 수를 확인하고 차이가 크면 계수 보정 → 비용 재조정 순으로 진행합니다.

### 11단계: 빌드 프로파일 시뮬레이션

지금까지 봇은 3택1을 **균등 무작위**로 골랐습니다. 그래서 결과는 "평균적인 빌드"의 성적이고, "투사체만 고르는 사람"이 어떻게 되는지는 모릅니다. 봇에 **성향**을 주면 그 성향의 결과 분포를 얻습니다.

`BuildProfile`은 강화 종류마다 상대 가중치를 갖고, 3택1이 만들어지면 그 세 장의 가중치에 비례해 하나를 뽑습니다. 가중치가 모두 같으면 기존 랜덤 봇과 **완전히 같은 동작**이고(기본값 `null`), 한 종류만 12배로 올리면 "제시되면 거의 항상 고르는" 플레이어, 0으로 두면 **금지(ablation) 실험**이 됩니다. 파일: `Assets/_CoinRush/Scripts/Balance/BuildProfile.cs`

```csharp
using System;
using System.Collections.Generic;

/// <summary>
/// 빌드 성향: 3택1에서 각 강화를 고를 상대 가중치. 0이면 그 강화는 고르지 않는다.
/// UnityEngine을 쓰지 않는 순수 C#이라 시뮬레이터와 게임(추천 카드 표시 등)이 함께 쓸 수 있다.
/// </summary>
public class BuildProfile
{
    public static readonly UpgradeKind[] AllKinds = (UpgradeKind[])Enum.GetValues(typeof(UpgradeKind));

    public readonly string label;
    private readonly float[] weights = new float[AllKinds.Length];

    public BuildProfile(string label, float defaultWeight = 1f)
    {
        this.label = label;
        for (int i = 0; i < weights.Length; i++) weights[i] = defaultWeight;
    }

    public BuildProfile Prefer(UpgradeKind kind, float weight)
    {
        weights[(int)kind] = weight;
        return this;
    }

    public float Weight(UpgradeKind kind) => weights[(int)kind];

    public static BuildProfile Uniform() => new BuildProfile("균등 (랜덤 봇)");

    /// <summary>한 종류만 12배로 선호 = "제시되면 거의 항상 고른다"</summary>
    public static BuildProfile Single(UpgradeKind kind) => new BuildProfile($"{kind} 우선").Prefer(kind, 12f);

    /// <summary>한 종류를 아예 고르지 않는다 = 그 강화를 뺐을 때의 결과를 본다</summary>
    public static BuildProfile Ban(UpgradeKind kind) => new BuildProfile($"{kind} 금지").Prefer(kind, 0f);

    /// <summary>빌드 벡터 두 개의 코사인 유사도. 1이면 구성 비율이 같다.</summary>
    public static float Similarity(int[] a, int[] b)
    {
        double dot = 0, na = 0, nb = 0;
        for (int i = 0; i < a.Length && i < b.Length; i++)
        {
            dot += (double)a[i] * b[i];
            na += (double)a[i] * a[i];
            nb += (double)b[i] * b[i];
        }
        if (na <= 0 || nb <= 0) return 0f;
        return (float)(dot / (Math.Sqrt(na) * Math.Sqrt(nb)));
    }

    /// <summary>빌드 벡터 목록에서 무작위 쌍 pairs개를 뽑아 유사도 중앙값을 구한다 (seed 고정).</summary>
    public static float MedianSimilarity(List<int[]> builds, int pairs, int seed)
    {
        if (builds.Count < 2) return 0f;
        var rng = new Random(seed);
        var values = new List<float>(pairs);
        for (int i = 0; i < pairs; i++)
        {
            int a = rng.Next(builds.Count);
            int b = rng.Next(builds.Count - 1);
            if (b >= a) b++;                       // 같은 판끼리 비교하지 않는다
            values.Add(Similarity(builds[a], builds[b]));
        }
        values.Sort();
        return values[values.Count / 2];
    }
}
```

**7단계 `BalanceSimulator.cs` 교체**: 프로파일을 받고, 판마다 빌드 벡터와 "제시된 횟수"를 남깁니다. 제시 횟수는 조건부 선택률의 분모이자 24장 로그와 맞대 볼 값입니다.

```csharp
// SimConfig — 필드 추가
public BuildProfile profile;              // null이면 균등 무작위 (기존 랜덤 봇과 동일)

// RunResult — 필드 추가
public int[] buildPicks, buildOffers;     // 강화별 선택 스택 수 / 제시된 횟수

// SimReport — 필드와 메서드 추가
public readonly int[] chosen = new int[BuildProfile.AllKinds.Length];
public readonly int[] offered = new int[BuildProfile.AllKinds.Length];
public float medianBuildSimilarity;

public string BuildLines()
{
    int total = 0;
    foreach (int n in chosen) total += n;
    if (total == 0) return "  (빌드 기록 없음)";
    var sb = new StringBuilder("  빌드 유사도 중앙값 ").Append(medianBuildSimilarity.ToString("0.00"));
    for (int k = 0; k < chosen.Length; k++)
        sb.Append($" | {(UpgradeKind)k} 점유 {chosen[k] / (float)total:P0}·조건부 " +
                  $"{(offered[k] > 0 ? chosen[k] / (float)offered[k] : 0f):P0}");
    return sb.ToString();
}

// BalanceSimulator — private static readonly AllKinds 줄을 지우고 BuildProfile.AllKinds를 쓴다
```

`SimulateRun` 안의 다섯 곳을 교체합니다.

```csharp
// ① 지역 변수 선언 (options 줄 교체)
var options = new List<UpgradeKind>(BuildProfile.AllKinds.Length);
var picks = new int[BuildProfile.AllKinds.Length];    // 이 판의 빌드 벡터
var offers = new int[BuildProfile.AllKinds.Length];   // 이 판에 제시된 횟수

// ② 사망 return 교체
if (hp <= 0f)
    return new RunResult { survivedSeconds = t, level = level, shrinePurchases = purchases,
                           coinsCollected = collected, coinsBanked = wallet,
                           buildPicks = picks, buildOffers = offers };

// ③ 레벨업 블록의 선택 두 줄 교체
UpgradeKind pick = PickOffer(stats, options, rng, c.profile, offers);
float before = stats.MaxHpBonus;
stats.Apply(pick);
picks[(int)pick]++;

// ④ 제단 블록의 선택 두 줄 교체
UpgradeKind pick = PickOffer(stats, options, rng, c.profile, offers);
float before = stats.MaxHpBonus;
stats.Apply(pick, c.shrineStacks);
picks[(int)pick] += c.shrineStacks;

// ⑤ 클리어 return 교체
return new RunResult
{
    survivedSeconds = c.runSeconds, level = level, shrinePurchases = purchases, cleared = true,
    coinsCollected = collected, coinsBanked = wallet * c.clearCoinBonus,
    buildPicks = picks, buildOffers = offers
};
```

`PickRandomOffer`를 아래 `PickOffer`로 교체합니다. **제시지를 만드는 규칙(부분 피셔-예이츠, 최대 3장, `CanApply`)은 그대로**이고 고르는 방법만 가중치로 바뀝니다.

```csharp
/// <summary>3택1을 만들고 프로파일 가중치로 하나를 고른다. profile이 null이면 균등 무작위.</summary>
private static UpgradeKind PickOffer(CombatStats stats, List<UpgradeKind> options, Random rng,
                                     BuildProfile profile, int[] offeredCount)
{
    options.Clear();
    foreach (UpgradeKind k in BuildProfile.AllKinds)
        if (stats.CanApply(k)) options.Add(k);
    int offer = Math.Min(3, options.Count);
    for (int i = 0; i < offer; i++)   // 부분 피셔-예이츠: 앞 offer칸이 제시된 선택지
    {
        int j = rng.Next(i, options.Count);
        (options[i], options[j]) = (options[j], options[i]);
    }
    for (int i = 0; i < offer; i++) offeredCount[(int)options[i]]++;

    if (profile == null) return options[rng.Next(offer)];

    float total = 0f;
    for (int i = 0; i < offer; i++) total += profile.Weight(options[i]);
    if (total <= 0f) return options[rng.Next(offer)];   // 세 장 모두 가중치 0이면 균등으로

    float roll = (float)rng.NextDouble() * total;
    float acc = 0f;
    for (int i = 0; i < offer; i++)
    {
        acc += profile.Weight(options[i]);
        if (roll < acc) return options[i];
    }
    return options[offer - 1];
}
```

`Summarize`에도 빌드 집계를 더합니다. 기존 줄은 그대로 두고 세 곳만 넣습니다.

```csharp
// (1) seconds 선언 옆에 추가
var builds = new List<int[]>(results.Length);

// (2) for 루프 끝(shrine += ... 다음 줄)에 추가
if (r.buildPicks != null)
{
    int stacks = 0;
    for (int k = 0; k < r.buildPicks.Length; k++)
    {
        report.chosen[k] += r.buildPicks[k];
        report.offered[k] += r.buildOffers[k];
        stacks += r.buildPicks[k];
    }
    if (stacks > 0) builds.Add(r.buildPicks);
}

// (3) return report; 바로 위에 추가 — 쌍과 seed를 고정해야 재실행 결과가 같다
report.medianBuildSimilarity = BuildProfile.MedianSimilarity(builds, 300, 7);
```

**8단계 메뉴에 항목 추가**: 균등 1개 + 단일 우선 7개 + 금지 7개, 모두 15개 프로파일을 한 번에 돌립니다.

```csharp
// BalanceSimulatorMenu.cs (8단계) — 메서드 추가 (파일 상단에 using System.Collections.Generic; 추가)
[MenuItem("Coin Rush/Balance/Run Build Profiles (15 x 1000 runs)")]
private static void RunProfiles()
{
    var wave = (WaveData)Selection.activeObject;
    ProgressionData prog = FindAsset<ProgressionData>();
    if (prog == null) { Debug.LogError("ProgressionData 에셋이 없습니다."); return; }

    SimConfig baseConfig = BuildConfig(wave, prog);
    var profiles = new List<BuildProfile> { BuildProfile.Uniform() };
    foreach (UpgradeKind k in BuildProfile.AllKinds) profiles.Add(BuildProfile.Single(k));
    foreach (UpgradeKind k in BuildProfile.AllKinds) profiles.Add(BuildProfile.Ban(k));

    var log = new StringBuilder();
    foreach (BuildProfile p in profiles)
    {
        SimConfig c = baseConfig.ShallowCopy();      // segments·events는 읽기만 하므로 공유해도 안전
        c.profile = p;
        SimReport r = BalanceSimulator.RunMany(p.label, c, Runs, Seed);
        log.AppendLine(r.ToString()).AppendLine(r.BuildLines());
    }
    // 파일 저장은 8단계 Run()의 마지막 세 줄과 같다 (파일명만 profiles_로)
    Debug.Log(log.ToString());
}

[MenuItem("Coin Rush/Balance/Run Build Profiles (15 x 1000 runs)", true)]
private static bool ValidateProfiles() => Selection.activeObject is WaveData;
```

### 12단계: 지배 선택지 찾아 고치기

**설정**: 9단계 조정 2 상태(22장 10단계 수정 후 웨이브 표 + 다항 1.6 + 엘리트 체력 배율 0.6), 프로파일마다 **1000판, seed 42**, 제단 안 삼, 영구 강화 0레벨. 아래 수치는 이 설정으로 돌린 결과입니다. 런타임의 난수·부동소수 구현에 따라 0.5%p 안팎은 달라질 수 있으니 순서와 크기를 보세요.

**진단 1 — 단일 우선 프로파일 8종**

| 프로파일 | 클리어율 | 생존 중앙값 | 평균 이월 | 평균 레벨 |
|---|---|---|---|---|
| 균등 (랜덤 봇) | 28.4% | 430초 | 829 | 16.5 |
| 피해 우선 | 24.2% | 382초 | 788 | 16.4 |
| 공격 속도 우선 | 25.6% | 365초 | 770 | 15.9 |
| **투사체 우선** | **64.1%** | **600초** | **1,396** | 20.7 |
| 최대 체력 우선 | 5.8% | 272초 | 418 | 13.1 |
| 재생 우선 | 12.6% | 288초 | 503 | 13.8 |
| 자석 우선 | 4.4% | 270초 | 528 | 14.5 |
| 방어 우선 | 4.3% | 259초 | 376 | 12.7 |

- **결과 지배 — 위반.** 투사체 우선이 2위(공격 속도 25.6%)를 **38.5%p** 앞섭니다. 기준은 10%p입니다. 게다가 투사체는 최대 5개에서 막히므로 전체 선택의 19.3%밖에 차지하지 못하는데도 이 차이가 납니다. **한 장만 제대로 고르면 클리어율이 2.3배**가 된다는 뜻이고, 이런 선택지가 3택1에 섞이면 나머지 두 장은 볼 이유가 없습니다.
- **사문화 — 위반.** 균등의 1/3은 9.5%입니다. 최대 체력(5.8), 자석(4.4), 방어(4.3)이 미달입니다. 재생(12.6)은 통과입니다 — 22장이 넣은 폭탄충 폭발이 "한 번에 크게 깎는" 피해라 회복의 값이 올라갔기 때문입니다.

**진단 2 — 금지(ablation) 실험**: 균등 프로파일에서 한 종류만 빼면 결과가 어떻게 변하는가. 3택1은 7종에서 뽑으므로 **평균 이하인 강화는 무엇이든 빼면 결과가 좋아집니다.** 7종이면 셋쯤은 평균 이하일 수밖에 없으므로, "+"의 유무가 아니라 **크기**를 봅니다. 이 교재 기준은 **+20%p 이상이면 선택지가 아니라 벌칙**(3택1의 한 칸을 차지해 쓸 만한 카드를 밀어냄)입니다.

| 금지한 강화 | 클리어율 | 균등(28.4%) 대비 | 읽기 |
|---|---|---|---|
| 투사체 | 0.0% | **−28.4%p** | 이 한 종류가 화력 전체를 지탱한다 |
| 재생 | 0.0% | **−28.4%p** | 지탱한다 (폭발 피해를 되돌릴 유일한 수단) |
| 피해 | 6.8% | −21.6%p | 지탱한다 |
| 공격 속도 | 20.3% | −8.1%p | 조금 지탱한다 |
| 자석 | 41.4% | +13.0%p | 평균 이하 (기준 미만) |
| 최대 체력 | 47.1% | +18.7%p | 평균 이하, 경계 |
| 방어 | 51.2% | **+22.8%p** | **벌칙** |

빌드 유사도 중앙값은 균등 0.73, 투사체 우선 0.81입니다. 투사체 우선은 이미 수렴 기준(0.85)에 가깝습니다.

**두 진단이 어긋나 보이는 곳이 있습니다.** 재생은 금지하면 −28.4%p(필요함)인데 재생만 우선하면 12.6%로 균등(28.4%)의 절반도 안 됩니다. 모순이 아니라 **"없으면 안 되지만 그것만으로는 안 되는" 강화**라는 뜻이고, 이런 강화는 그대로 두는 것이 맞습니다. 고칠 대상은 두 진단이 같은 방향을 가리키는 것들입니다 — 투사체(지배), 방어·최대 체력·자석(사문화 + 평균 이하).

**수정 A — 지배 선택지의 가치를 낮춘다** (출현 빈도가 아니라 **가치**를 고칩니다. 빈도만 낮추면 "나오면 무조건 고른다"는 그대로이고, 나오지 않은 판은 그냥 운이 나쁜 판이 됩니다.)

```csharp
// UpgradeRules.cs — CombatStats에 상수와 배율 추가, ShotDamage 교체
public const float ProjectileDamagePenalty = 0.15f;   // 투사체가 1발 늘 때마다 한 발 피해 ×0.85

public float ProjectilePenaltyMul => (float)Math.Pow(1.0 - ProjectileDamagePenalty, Projectiles - 1);

public int ShotDamage(int baseDamage) =>
    Math.Max(1, (int)Math.Round(baseDamage * DamageMul * ProjectilePenaltyMul));
```

이제 투사체 N개의 총 화력은 `N × 0.85^(N-1)`입니다. 1→2발은 +70%, 4→5발은 +6%로 줄어, 후반에는 곱연산인 공격 속도(+15%)가 앞섭니다. 규칙 파일 한 곳을 고쳤으므로 게임의 `AutoAimWeapon`도 같은 순간에 바뀝니다(11장 카드 설명 문구도 "투사체 +1 (한 발 피해 −15%)"로 고칩니다).

| 프로파일 | 수정 전 | **수정 A 후** |
|---|---|---|
| 균등 | 28.4% | **0.0%** |
| 피해 우선 | 24.2% | 0.0% |
| 공격 속도 우선 | 25.6% | 0.1% |
| 투사체 우선 | 64.1% | 0.0% |
| 균등 생존 중앙값 / 이월 | 430초 / 829 | 282초 / 389 |

**지배는 사라졌지만 게임도 같이 죽었습니다.** 금지 실험이 예고한 그대로입니다 — 투사체가 화력 전체를 지탱하고 있었으므로, 그것을 깎으면 9:00 보스(체력 3,600)를 아무도 넘지 못합니다. **지배 선택지를 약화하는 수정은 재보정과 한 묶음**입니다.

**수정 B — 사문화된 선택지를 선택지로 되돌린다** (단일 우선에서 균등의 1/3에 못 미친 자석·최대 체력·방어가 대상입니다. 재생은 통과했지만 계수가 방어·체력과 같은 계열이라 함께 맞춥니다.)

```csharp
// UpgradeRules.cs — CombatStats 상수 교체
public const int MaxMagnetStacks = 3;          // 수집률이 100%에 닿으면 그 뒤 자석은 가치가 0
public const float MaxHpPerStack = 40f;        // 25 → 40
public const float RegenPerStack = 3f;         // 0.5 → 3 (초당 회복)
public const float ArmorPerStack = 0.82f;      // 0.92 → 0.82 (받는 피해 곱연산)

// 필드 추가
public int MagnetStacks { get; private set; }

// CanApply 교체 — 상한에 닿은 강화는 3택1에 넣지 않는다 (게임과 시뮬레이터 공통)
public bool CanApply(UpgradeKind kind) => kind switch
{
    UpgradeKind.Projectile => Projectiles < MaxProjectiles,
    UpgradeKind.Magnet => MagnetStacks < MaxMagnetStacks,
    _ => true
};

// Apply의 Magnet 한 줄 교체
case UpgradeKind.Magnet:
    if (MagnetStacks < MaxMagnetStacks) { MagnetStacks++; MagnetMul += MagnetPerStack; }
    break;
```

자석 상한은 수치 조정이 아니라 **낭비 제거**입니다. 수집률은 100%가 상한이므로 네 번째 자석부터는 효과가 0인데, 그 카드가 3택1의 한 칸을 계속 차지하고 있었습니다. 투사체가 5개에서 안 나오는 것과 같은 규칙입니다.

**수정 A + B 후 (같은 설정, 1000판, seed 42)**

| 프로파일 | 수정 전 | **수정 후** | 이월 (전 → 후) |
|---|---|---|---|
| 균등 (랜덤 봇) | 28.4% | **30.0%** | 829 → 774 |
| 피해 우선 | 24.2% | **41.8%** | 788 → 888 |
| 공격 속도 우선 | 25.6% | **40.1%** | 770 → 836 |
| 투사체 우선 | **64.1%** | **45.1%** | 1,396 → 970 |
| 재생 우선 | 12.6% | 22.3% | 503 → 560 |
| 자석 우선 | 4.4% | 25.7% | 528 → 767 |
| 방어 우선 | 4.3% | 10.5% | 376 → 422 |
| 최대 체력 우선 | 5.8% | **2.8%** | 418 → 366 |

- **결과 지배 — 해소.** 1위 투사체(45.1%)와 2위 피해(41.8%)의 차이가 **3.3%p**입니다(38.5%p → 3.3%p). 기준 10%p를 통과합니다. 화력 3종 중 무엇을 우선해도 비슷한 성적이 나오므로, 3택1은 "상황에 따라" 고르는 결정이 됩니다.
- **사문화 — 대부분 해소.** 균등의 1/3은 10.0%입니다. 자석(25.7), 재생(22.3), 방어(10.5, 경계)가 통과합니다.
- **9단계 조정 목표도 통과**합니다: 균등 프로파일 클리어율 30.0%(목표 20~35%), 생존 중앙값 489초(360~540), 한 판 평균 이월 774(600~900), 최다 사망 분 8분 15.0%(25% 이하).
- 사망 분포가 크게 바뀌었습니다. **3분 사망 23.9% → 6.1%**로 거의 사라지고 **7분 7.2% → 14.2%, 8분 1.6% → 15.0%**로 옮겨 갔습니다. 초반 벽이 후반으로 이동한 것이므로, 22장 7:00~9:00 구간을 다음 조정 후보로 적어 둡니다.
- **남은 문제 — 최대 체력은 오히려 나빠졌습니다.** 수정 후 금지 실험에서 최대 체력을 빼면 클리어율이 **+37.6%p**(30.0% → 67.6%)로 오릅니다(수정 전 +18.7%p). 재생·방어를 올린 만큼 최대 체력이 상대적으로 더 밀린 것입니다. 원인 가설: 코인 러시에는 회복 수단이 재생뿐이라 최대 체력 +40은 한 번 쓰고 마는 완충재이고, 다른 강화는 판 내내 복리로 작동합니다. 방어(+17.9%p)와 자석(+14.6%p)은 벌칙 기준(+20%p) 아래로 내려왔습니다.

**보류한 수정안도 기록합니다.** "최대 체력 보너스 1당 초당 0.02 회복"이라는 시너지를 넣어 보았습니다. 최대 체력 우선이 2.8% → 14.2%로 살아났지만, 균등이 50.1%로 난이도 목표(20~35%)를 벗어나고 투사체 우선이 71.6%로 2위(59.9%)를 11.7%p 앞서 다시 지배했습니다. **한 지표를 고치는 수치가 다른 지표를 깨는 것이 정상**이므로, 고친 것과 포기한 것을 같이 남깁니다.

```
Docs/balance-log.md
  2026-10-06  지배 선택지 수정 (22장 웨이브 v3 기준)
    진단: 투사체 우선 64.1% vs 2위 25.6% (기준 10%p 초과) / 방어 금지 +22.8%p (벌칙)
    수정 A: ProjectileDamagePenalty 0.15  → 지배 해소, 그러나 전 프로파일 클리어 0%
    수정 B: MaxHp 25→40, Regen 0.5→3, Armor 0.92→0.82, MaxMagnetStacks 3 신설
    결과: 1위-2위 격차 3.3%p (38.5%p→3.3%p), 균등 30.0% / 489초 / 이월 774 (9단계 목표 전부 통과)
    보류: 체력→재생 시너지 0.02 (최대 체력은 살았으나 균등 50.1%로 목표 이탈)
    다음: 7~8분 사망 29.2%, 최대 체력 금지 +37.6%p → 24장 로그로 사람의 선택을 확인한 뒤 재판단
```

**수정 후 9·10단계 기준선 재측정** — 규칙이 바뀌었으므로 앞 표들은 모두 낡았습니다. 같은 메뉴를 다시 돌려 새 기준선을 기록합니다.

| 시나리오 | 수정 전 | 수정 후 |
|---|---|---|
| 제단 안 삼 (기준) | 28.4% / 이월 829 | 30.0% / 이월 774 |
| 제단 항상 삼 | 56.9% / 이월 770 | 71.1% / 이월 595 |
| 체력 60% 미만일 때만 삼 | 37.0% / 이월 843 | 34.9% / 이월 757 |
| 영구 강화 3종 1레벨 | 44.6% / 이월 1,178 | 49.5% / 이월 1,070 |
| 영구 강화 3종 5레벨 | 77.4% / 이월 2,071 | 91.1% / 이월 1,942 |
| 영구 강화 3종 10레벨 | 89.9% / 이월 2,415 | 97.4% / 이월 2,181 |

**제단의 트레이드오프가 되살아났습니다.** 10단계에서 얇아졌던 차이(클리어 +28.5%p, 이월 −7%)가 이제 **클리어 +41.1%p, 이월 −23%**입니다. 제단 가격이나 22장 코인 공급을 건드리지 않고, 강화 계수만 고쳐서 얻은 결과입니다. 다만 한 판 이월이 전반적으로 줄었으므로 **경제 쪽 목표 판 수가 밀립니다.** 그것을 13단계에서 확인합니다.

**여기까지가 시뮬레이터가 할 수 있는 전부입니다.** 판정한 것은 "이 모델 안에서 어떤 빌드가 강한가"이고, "사람이 제시됐을 때 무엇을 고르는가"와 "고른 뒤 재미있다고 느끼는가"는 답하지 못합니다. 선택 편중·빌드 수렴 두 신호는 24장에서 `level_up`의 조건부 선택률과 판별 빌드 유사도로 측정합니다. 특히 **최대 체력이 벌칙이라는 결론은 모델의 피격 계산에 크게 의존**하므로(9단계 한계), 실제 테스터가 최대 체력을 고르고도 더 오래 버티는지 확인하기 전에는 카드를 빼지 않습니다.

### 13단계: 콘텐츠 고갈 측정과 수정

10단계의 캠페인 시뮬레이션에 **목표 공백**을 함께 기록하면 고갈 지표 세 개를 모두 얻습니다. `SimulateCampaign`이 이미 "판 번호"를 반환하므로, 구매가 일어난 판 번호만 추가로 모으면 됩니다.

```csharp
// BalanceSimulator.cs — SimulateCampaign에 세 곳 추가
// (1) for 루프 밖 선언에 추가
var purchaseRuns = new List<int>();     // 무엇이든 하나라도 산 판 번호

// (2) SimulateRun 호출 다음, while(true) 구매 루프 직전에 추가
int levelsBefore = c.metaDamageLevel + c.metaHpLevel + c.metaMagnetLevel;

// (3) while(true) 구매 루프 바로 뒤에 추가
if (c.metaDamageLevel + c.metaHpLevel + c.metaMagnetLevel > levelsBefore) purchaseRuns.Add(run);

// (4) 최대 목표 공백 — 첫 구매까지의 거리도 한 번의 간격으로 센다
public static int MaxGoalGap(List<int> purchaseRuns)
{
    int gap = 0, previous = 0;
    foreach (int run in purchaseRuns) { gap = Math.Max(gap, run - previous); previous = run; }
    return gap;
}
```

`MaxGoalGap`은 정적 메서드이므로 `SimulateCampaign` 바깥에 둡니다. 반환값을 메뉴 로그 한 줄에 같이 출력하세요.

**측정 (12단계 수정 후 규칙, 10단계에서 채택한 기본가 300·성장 1.5, seed 0~99의 중앙값)**

| 지표 | 값 | 목표 | 판정 |
|---|---|---|---|
| 첫 클리어 | 2판 | 2~4판 | 통과 |
| 세 강화 모두 1레벨 | 2판 | 1~2판 | 통과 |
| 세 강화 모두 5레벨 | 9판 | 약 8판 | 통과 |
| **고갈 판 수** (3종 10레벨) | **52판** | 40~50판 | **미달** |
| **최대 목표 공백** | **6판** | 5판 이하 | **미달** |
| 고갈 후 잉여 | 무한 축적 | 0 | **미달** |

10단계에서 47판으로 맞춰 둔 고갈이 52판으로 밀렸습니다. **12단계가 한 판 이월을 829에서 774로 낮췄기 때문**입니다. 전투 규칙을 고치면 경제 표가 낡습니다 — 22장이 웨이브를 고치고 제단 지갑 표를 다시 계산한 것과 같은 일이 한 장 안에서 또 일어납니다.

레벨별 도달 판을 보면 공백이 어디서 생기는지 바로 보입니다.

| 3종이 모두 L레벨이 되는 판 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 기본가 300 · 성장 1.5 | 2 | 3 | 4 | 6 | 9 | 12 | 17 | 25 | 36 | **52** |
| 직전 레벨에서 걸린 판 | — | 1 | 1 | 2 | 3 | 3 | 5 | 8 | 11 | **16** |

마지막 한 레벨에 16판(약 2시간 40분)이 걸립니다. 그 사이에도 세 강화를 번갈아 사므로 구매 간격의 최댓값은 6판이지만, **"다음 목표가 2시간 반 뒤"라는 상태가 마지막 3분의 1 내내 이어집니다.**

**수정 ① 비용 곡선 재배분** — 1종 누적 총액을 오히려 조금 줄이면서(34,010 → 30,370), 성장률을 낮추고 기본가를 올립니다.

```
ProgressionData: Upgrade Base Cost 300 → 480, Upgrade Cost Growth 1.5 → 1.38
cost(L) = 480 × 1.38^(L-1), 10 단위 반올림
  L1 480 · L2 660 · L3 910 · L4 1,260 · L5 1,740 · L6 2,400 · L7 3,320 · L8 4,580 · L9 6,310 · L10 8,710
```

| 3종이 모두 L레벨이 되는 판 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **기본가 480 · 성장 1.38** | 2 | 4 | 6 | 8 | 11 | 15 | 20 | 26 | 35 | **48** |
| 직전 레벨에서 걸린 판 | — | 2 | 2 | 2 | 3 | 4 | 5 | 6 | 9 | **13** |

| 지표 | 300 · 1.5 | **480 · 1.38** | 목표 |
|---|---|---|---|
| 고갈 판 수 | 52판 | **48판** | 40~50판 |
| 최대 목표 공백 | 6판 | **4판** | 5판 이하 |
| 세 강화 모두 1레벨 | 2판 | 2판 | 1~2판 |
| 첫 클리어 | 2판 | 2판 | 2~4판 |

숫자 두 개로 두 지표가 목표 안에 들어왔습니다. 새로 만든 콘텐츠는 없습니다.

**수정 ② 해금 순서 — 측정했지만 채택하지 않았습니다.** 3종을 처음부터 다 열지 않고 "공격력 3레벨 → 최대 체력 해금", "양쪽 5레벨 → 수집 범위 해금"으로 바꿔 보았습니다.

| 지표 | 480 · 1.38 (동시 해금) | 480 · 1.38 + 순차 해금 |
|---|---|---|
| 고갈 판 수 | 48판 | 49판 |
| 최대 목표 공백 | 4판 | 4판 |
| 세 강화를 모두 1레벨 이상 갖는 판 | 2판 | **10판** |

공백은 같고 고갈은 1판 늦어지지만, **세 강화를 모두 겪는 시점이 2판에서 10판(약 1시간 40분)으로 밀립니다.** 21장이 첫 세션의 성취를 우선하므로 채택하지 않고, "해금 이벤트가 필요해지면 다시 꺼낼 안"으로 `balance-log.md`에 남깁니다. **측정하고 버린 안도 기록**해야 다음에 같은 실험을 반복하지 않습니다.

**고갈 후 잉여는 여기서 못 고칩니다.** 48판(약 8시간)이면 저가 게임의 적정 플레이 시간 가정에는 닿지만, 그 뒤 코인은 쓸 곳이 없습니다. 비용 곡선을 아무리 만져도 "더 늦게 고갈될 뿐"이므로 세 번째 레버(새 Sink)가 필요합니다 — 21장 스코프에 이미 있는 **캐릭터 해금 2종**(연습 4)이 그 자리이고, 24장 `upgrade_purchase` 이벤트로 **실제 도달 판 수**를 확인한 뒤 가격을 정합니다. 시뮬레이터가 말하는 48판은 봇의 이월량(774) 기준이므로, 사람이 더 못 모으면 고갈은 더 늦게 옵니다.

**22장이 남긴 항목과의 관계** — 22장 11단계는 "도주 전술이 0:00~3:00을 연속 통과한다"를 다음 루프로 넘기면서, 후보로 (a) 폭탄충 이동속도 2.2 → 3.2, (b) 2:00~3:00에 골렘 소수 투입을 적었고 **위협·코인 영향을 이 장 시뮬레이터로 먼저 계산하라**고 했습니다. 이 장의 12·13단계는 **강화 쪽 수치만** 고쳤으므로 그 항목은 그대로 열려 있습니다. 둘 중 무엇을 고르든 `BuildConfig`가 에셋에서 다시 읽으므로 코드 수정 없이 9·10·13단계 표를 다시 뽑아 비교하면 됩니다. 다만 (b)는 2:00~3:00의 역할 가중치를 건드려 22장 10-7의 R1 경계값(압박 70%)을 깨므로, 시뮬레이터 결과와 함께 R1·R2 검사를 반드시 같이 보세요.

### 확인하기

- **게임**: Play → 레벨업에서 "투사체 +1"을 고르면 다음 발사부터 투사체가 부채꼴로 2발 나간다. "피해 +25%"를 고르면 데미지 숫자가 10 → 12로 바뀐다(12.5를 `Math.Round`가 짝수 쪽으로 반올림). 투사체를 5개까지 올리면 이후 레벨업·제단에 투사체 카드가 나오지 않는다.
- **제단**: 22장 **F3**로 1:56 근처로 가서 2:00에 노란 제단이 생기는지 보고, 닿으면 게임이 멈추고 "제단 강화 50 코인 (지갑 N)" 창이 뜬다. 지갑이 50 미만이면 강화 버튼이 눌리지 않고 "모으기"만 된다. 구매하면 지갑이 50 줄고 효과가 적용된다. 30초 안에 가지 않으면 제단이 사라진다.
- **정산**: 결과 화면의 이월 코인 = 지갑(클리어면 ×1.5). 판 도중 에디터 Play를 멈춘 뒤 다시 Play하면 타이틀 상점의 코인이 그 판 지갑만큼 늘어 있다.
- **영구 강화**: 상점에서 공격력 1레벨을 사면(10단계 채택가 300) 다음 판 시작 무기 데미지가 11이 된다. 가격 표시가 "다음 450 코인"으로 바뀐다(13단계에서 곡선을 재배분하면 480·660이 된다).
- **시뮬레이터**: 메뉴를 실행하면 Console에 시나리오 9개와 캠페인 1줄, 소요 시간이 출력되고, 같은 설정으로 두 번 실행하면 결과가 **완전히 같다**(고정 seed).
- `Docs/balance-log.md`에 조정 목표, 조정 전후 표, 가정의 폭 표가 있고, 각 조정마다 "무엇을 왜 바꿨는지" 한 줄이 있다.
- **빌드 프로파일**: **Coin Rush → Balance → Run Build Profiles** 를 실행하면 15줄(균등 1 + 단일 우선 7 + 금지 7)이 나오고, "균등 (랜덤 봇)" 줄의 클리어율이 기존 **Run Simulator** 의 "기준 가정" 줄과 **±0.5%p 안에서 일치한다**. 가중치가 모두 1이면 누적 임계값이 1·2·3이 되어 `(int)(NextDouble() × 3)`, 즉 균등 무작위와 같은 식이 되기 때문이다(부동소수 변환 때문에 아주 드물게 한두 판이 갈릴 수 있다).
- **금지 실험**: "Magnet 금지" 줄의 빌드 점유율에서 Magnet이 **0%**이고, 나머지 6종의 점유율 합이 100%다.
- **자석 상한**: Play → 레벨업에서 수집 범위를 3번 고르면 이후 레벨업·제단에 자석 카드가 나오지 않는다(투사체 5개와 같은 규칙).
- **투사체 페널티**: 피해 강화 없이 투사체만 2개로 올리면 데미지 숫자가 10 → **8**로 줄고(10 × 0.85 = 8.5, `Math.Round`가 짝수 쪽으로), 한 번에 두 발이 나가 총 화력은 10 → 16으로 늘어난다.
- `Docs/balance-log.md`에 지배 판정 표, 금지 실험 표, 수정 전후 표, **보류한 수정안**, 콘텐츠 고갈 3지표가 있다.

## 흔한 실수

1. **증상**: 시뮬레이터 클리어율은 오르는데 실제로 해 보면 강화가 체감되지 않는다. → **원인**: 강화 효과가 시뮬레이터에만 있고 게임 코드에는 없음(또는 수치가 따로 적혀 어긋남). → **해결**: 효과 수치와 공식을 `UpgradeRules.cs` 한 곳에 두고 게임(`PlayerStats`)과 시뮬레이터가 같은 `CombatStats.Apply`를 부르게 합니다. 강화 선택 전후 데미지·발사 간격·투사체 수를 Play 중에 직접 확인합니다.
2. **증상**: 조정할 때마다 결과가 들쭉날쭉해서 좋아졌는지 모르겠다. → **원인**: 매번 다른 난수 seed, 혹은 표본이 100판 이하. → **해결**: 비교할 때는 seed를 고정하고 1000판 이상 돌립니다. 결론이 seed에 따라 뒤집히는지 seed 2~3개로 한 번 더 확인합니다.
3. **증상**: 여러 수치를 한꺼번에 바꿨더니 좋아졌지만 이유를 모른다. → **원인**: 변수 동시 변경. → **해결**: 한 번에 하나씩 바꾸고 로그에 기록합니다(9단계의 조정 1 → 조정 2).
4. **증상**: 시뮬레이터 클리어율 29%인데 테스터는 전부 클리어한다(혹은 아무도 못 한다). → **원인**: 모델 계수(명중 효율·회피 한계·수집률·접촉 확률)는 가정이고, 결과는 그 가정에 매우 민감함. → **해결**: 처음부터 초보·숙련 가정을 함께 돌려 폭을 보고, 플레이테스트(24장)의 사망 시각 분포·수집량으로 계수를 보정한 뒤 다시 조정합니다. 보정 전의 절대 수치로 "클리어율 29% 확정" 같은 결론을 내리지 않습니다.
5. **증상**: 제단에서 항상 사는 것(또는 항상 안 사는 것)이 정답이 되었다. → **원인**: 제단 강화가 생존을 늘려 수집량까지 늘리는 효과를 계산에 넣지 않음. → **해결**: 제단 정책별 시나리오로 클리어율과 **이월 코인을 함께** 비교합니다. 한쪽이 두 지표 모두 우세하면 제단 효과·가격을 조정합니다(10단계의 stacks 2 → 1).
6. **증상**: 출시 한 달 뒤 "코인이 쓸 데가 없다"는 리뷰. → **원인**: Sink 고갈(인플레이션). → **해결**: 캠페인 시뮬레이션으로 "모든 강화 완료" 판 수를 미리 확인하고, 그 이후의 Sink(캐릭터·외형·도전 모드 입장료)를 출시 전에 준비합니다.
7. **증상**: 강화 7종의 DPS 증가율을 비슷하게 맞췄는데도 테스터가 항상 같은 것만 고른다. → **원인**: 표의 한 줄은 "지금 한 번"의 값이고, 지배 여부는 **계속 쌓았을 때의 결과**로 정해집니다. 개수 증가(투사체)는 초반 증가율이 압도적이고 생존 계열은 수집량까지 늘리지 못합니다. → **해결**: 11단계처럼 단일 우선 프로파일을 돌려 결과로 판정하고, 출현 빈도가 아니라 **가치 자체**를 고칩니다. 빈도만 낮추면 "나오면 무조건 고른다"는 그대로입니다.
8. **증상**: 지배 선택지를 약화했더니 게임 전체가 클리어 불가가 됐다. → **원인**: 그 선택지가 화력 전체를 지탱하고 있었음(금지 실험에서 −28.4%p). → **해결**: **약화와 재보정을 한 묶음으로** 봅니다. 지배 판정 기준과 9단계 난이도 목표를 **함께** 통과할 때까지가 한 번의 수정이고, 통과할 때마다 9·10단계 기준선 표를 다시 찍습니다.
9. **증상**: 강화를 계속 추가했는데도 "할 게 없다"는 말이 나온다. → **원인**: 선택지 수를 늘렸을 뿐 **목표 공백**을 재지 않음. 다음에 살 것이 6판 뒤면 그 6판은 목표가 없는 판입니다. → **해결**: 고갈 판 수·최대 목표 공백·고갈 후 잉여 세 가지를 캠페인 시뮬레이션에서 함께 출력하고(13단계), 비용 곡선 → 해금 순서 → 새 Sink 순으로 싼 레버부터 씁니다.

## 연습 문제

**1. ★☆☆ 업그레이드 가치 계산**
피해 배율 2.0, 공격 속도 배율 1.52, 투사체 3인 상태입니다. +피해, +공격 속도, +투사체 각각의 DPS 증가율을 구하고 가장 좋은 선택을 고르세요.

<details><summary>힌트·해설</summary>

+피해: 2.25 ÷ 2.0 = +12.5%. +공격 속도: 항상 +15%. +투사체: 4 ÷ 3 = +33.3%. 투사체가 가장 좋습니다. 투사체가 최대(5)에 도달하면 곱연산인 공격 속도(+15%)가 합연산 피해(2.0 기준 +12.5%, 이후 더 감소)를 앞섭니다. 이 역전 지점을 알면 "초반엔 투사체, 후반엔 공격 속도"라는 전략이 생기고, 그것이 설계 의도에 맞는지 판단할 수 있습니다. 실제 게임에서 `ShotDamage`는 정수로 반올림하므로(`Math.Round`는 .5를 짝수 쪽으로 보냄) 기본 피해 10에서는 +25%가 한 발 12.5 → 12처럼 표보다 작게 나타난다는 점도 확인해 보세요. 체력이 작은 적을 상대로는 이런 반올림이 "몇 방에 죽는가"를 바꿉니다.

</details>

**2. ★★☆ 초보 가정의 2분 벽 낮추기**
초보 가정에서 2분 사망이 42.1%입니다. 초보 가정의 2분 사망을 20% 이하로 낮추되, 기준 가정의 클리어율은 35%를 넘지 않게 하는 조정을 두 가지 제안하고 시뮬레이터로 확인하세요.

<details><summary>힌트·해설</summary>

2분 벽의 출처는 둘입니다 — **일반 적의 누적**(1:00~3:00 스폰율 1.2)과 **2:05 폭탄충 도입 2마리의 폭발**입니다. 초보 가정은 폭발 적중률이 0.15라 후자의 비중이 큽니다. 먼저 `blastHitChance`만 기준값 0.08로 되돌려 돌려 보면 둘의 몫이 갈립니다. 후보: (a) 1:00~2:00 스폰율 1.2 → 1.0, (b) 경험치 곡선의 L2~L6 구간을 완만하게(다항 `xpBase` 5 → 4), (c) 시작 무기 쿨다운 1.0 → 0.9. 하나씩 적용해 초보·기준·숙련 세 줄을 표에 기록합니다. (a)는 코인 공급도 줄이므로 22장 10-8 제단 표의 2:00 지갑 상한 72가 가격 50 아래로 떨어지지 않는지 함께 확인합니다. **폭발 피해(`BombBlast.damage` 18)는 후보에 넣지 마세요** — 22장 11단계가 이미 그 값 하나로 클리어율을 맞춘 뒤 넘긴 상태이고, 같은 수치를 두 장에서 번갈아 만지면 원인을 잃습니다. 초보만 쉽게 하는 조정은 드물기 때문에 "기준 가정 상한"을 같이 두는 것입니다. 초반을 쉽게 하면 중후반 클리어율도 따라 오르는 것이 보통입니다.

</details>

**3. ★★☆ 탐욕 봇 추가**
`SimulateRun`에 전략 매개변수를 추가해, 제시된 3개 중 "현재 상태에서 DPS 증가율이 가장 큰 것"을 고르는 탐욕 봇을 만드세요. 랜덤 봇과 클리어율을 비교하면 무엇을 알 수 있나요?

<details><summary>힌트·해설</summary>

11단계에서 선택 정책을 `PickOffer` 한 곳으로 모아 뒀으므로, `BuildProfile`과 나란히 놓을 자리가 이미 있습니다. `enum BotStrategy { Random, GreedyDps }`를 `SimConfig`에 넣고, `PickRandomOffer`에서 앞 3칸이 섞인 뒤 각 선택지를 적용했을 때의 DPS를 계산해 최대를 고릅니다. `CombatStats`를 복제할 수 없으므로 `Dps` 계산식에 선택지별 변화를 직접 넣거나, `CombatStats`에 `Clone()`을 추가합니다(규칙 파일에 넣으면 게임에서도 "추천 카드 표시" 같은 기능에 재사용할 수 있습니다). 탐욕 봇이 랜덤 봇보다 크게 앞서면 "선택에 실력 차가 반영된다"는 뜻이라 좋은 신호입니다. 반면 탐욕 봇이 생존 계열을 전혀 안 고르는데도 압도적이라면 생존 강화의 가치가 너무 낮은 것입니다. 단, 두 봇의 차이는 **강화 선택 실력**의 차이일 뿐 조작 실력(회피·수집)은 계수로 따로 정해지므로, 초보·숙련 체감 차이 전체로 읽지 않습니다.

</details>

**4. ★★★ 캐릭터 해금 Sink 설계**
"모든 영구 강화 완료" 이후를 위해 21장 스코프의 캐릭터 3종 중 해금 캐릭터 2종을 추가합니다. 해금 가격, 캐릭터의 시작 능력(`CombatStats`로 표현 가능해야 함), 해금 목표 판 수를 정하고, `SimulateCampaign`을 확장해 "세 강화 10레벨 + 캐릭터 2종" 도달 판 수를 구하세요. 파워 크립이 생기지 않았는지 캐릭터별 클리어율로 검증하세요.

<details><summary>힌트·해설</summary>

캐릭터를 "피해 −20%, 투사체 +1로 시작"처럼 트레이드오프로 설계하면 파워 크립 없이 다양성이 생깁니다. `CombatStats`에 캐릭터 보정을 받는 생성자 오버로드를 추가하면 게임(`PlayerStats`)과 시뮬레이터가 또 같은 규칙을 씁니다. 검증은 같은 영구 강화 레벨에서 캐릭터별 클리어율을 비교해 기본 캐릭터 대비 ±10%p 안쪽인지 봅니다. 해금 가격은 "강화 완료 후 한 판 이월 코인(12단계 수정 후 10레벨 시나리오 약 2,180)"의 5~10배로 시작해 목표 판 수에 맞춥니다. 캠페인 루프에서 강화를 다 산 뒤에만 캐릭터를 사도록 우선순위를 두세요.

</details>

## 셀프 체크

**1. 경험치 요구량은 다항 공식, 영구 강화 비용은 지수 공식이 어울리는 이유를 설명해보세요.**

<details><summary>모범 답안</summary>

서바이버라이크는 시간이 지날수록 적이 늘어 판 안의 코인 획득 속도가 오르므로, 요구량이 선형이면 후반 레벨업이 폭주하고 지수이면 후반 성장이 멈춥니다(11장 지수 곡선이 레벨 14 부근에서 막힌 이유). 획득 증가와 비슷한 속도로 가팔라지는 다항 공식이 균형을 잡기 쉽습니다. 반면 판 밖의 영구 강화 비용은 한 판당 획득량이 크게 변하지 않는 조건에서 "초반은 금방, 마지막은 오래"라는 장기 목표를 만들어야 하므로 지수 공식이 적합합니다.

</details>

**2. 강화 효과를 시뮬레이터와 게임 코드에 따로 구현하면 어떤 문제가 생기며, 이 장은 어떻게 막았나요?**

<details><summary>모범 답안</summary>

두 구현이 어긋나면 시뮬레이터가 계산한 클리어율·이월량이 실제 게임과 무관해집니다. 극단적으로는 게임에서는 아무 효과가 없는데 시뮬레이터에서만 강해질 수 있습니다. 이 장은 강화 종류·수치·성장 공식을 UnityEngine에 의존하지 않는 `UpgradeRules.cs`에 두고, 게임의 `PlayerStats`와 시뮬레이터가 같은 `CombatStats.Apply`·`ProgressionRules`를 호출하게 했습니다. 제시 조건(`CanApply`)과 제단 `stacks`도 같은 값을 씁니다.

</details>

**3. 시뮬레이터 결과를 평균 하나가 아니라 분 단위 히스토그램으로 봐야 하는 이유는?**

<details><summary>모범 답안</summary>

평균이 같아도 분포는 전혀 다를 수 있습니다. 모두 7분 근처에서 죽는 게임(특정 시각의 벽)과 절반은 3분, 절반은 클리어하는 게임(운에 좌우)은 평균 생존이 같지만 문제와 처방이 다릅니다. 히스토그램에서 사망이 몰린 분을 22장 웨이브 표의 이벤트 시각과 대조하면 원인 후보가 바로 보입니다. 이 장에서도 경험치 조정이 9분 사망은 줄였지만 3분 사망은 늘렸다는 사실은 히스토그램에서만 보였습니다.

</details>

**4. 이 시뮬레이터의 결과를 "실제 난이도의 상한"으로 읽으면 안 되는 이유와, 올바르게 쓰는 방법은?**

<details><summary>모범 답안</summary>

랜덤 봇은 강화 선택만 무작위일 뿐, 명중 효율·회피 한계·수집률·접촉 확률은 임의로 정한 계수라 사람보다 유리할 수도 불리할 수도 있습니다. 실제로 계수만 바꾼 초보·숙련 가정의 클리어율이 0%와 59%로 크게 갈렸습니다. 그래서 결과는 특정 가정 아래의 비교 모델입니다. 같은 가정 안에서 수치 변경의 방향과 크기를 비교하고, 가정의 폭(복수 시나리오)에서 결론이 뒤집히지 않는지 확인하며, 플레이테스트의 사망 시각 분포·수집량으로 계수를 보정한 뒤에야 절대 수치를 판단 근거로 씁니다.

</details>

**5. 제단에서 "사는" 전략과 "모으는" 전략의 시뮬레이션 결과가 어떻게 나와야 코인 러시의 차별점이 유지되나요?**

<details><summary>모범 답안</summary>

어느 한쪽이 모든 지표에서 우세하면 안 됩니다. 사면 이번 판 클리어율이 오르고, 모으면 이월 코인이 늘어 다음 판이 강해지는 트레이드오프가 둘 다 체감될 만큼 커야 합니다. 이 장의 최종 결과(12단계 수정 후)에서는 항상 사면 클리어율 30% → 71%, 이월 774 → 595로 양쪽 모두 뚜렷한 차이가 있어 결정이 됩니다. 반대로 제단 강화가 2단계였을 때는 사는 쪽이 클리어율(66.8%)과 이월(969)이 모두 높아 항상 사는 것이 정답이 되었습니다. 22장이 코인 공급을 약 10% 늘렸을 때 이 차이가 이월 −7%까지 얇아졌다가, 강화 계수를 고치자 −23%로 되살아난 것도 같은 이야기입니다. 생존이 늘면 수집도 늘기 때문에, 이 역전은 반드시 시뮬레이션으로 확인해야 합니다.

</details>

**6. 지배 전략을 판정하는 네 신호 중 시뮬레이터가 답할 수 있는 것과 없는 것을 나누고, 이유를 설명해보세요.**

<details><summary>모범 답안</summary>

시뮬레이터가 답하는 것은 **결과 지배**(단일 우선 프로파일 간 클리어율·생존·이월 차이)와 **사문화**(어떤 계열을 우선하면 균등보다 크게 나빠지는가)입니다. 이것들은 "규칙이 만드는 결과"이므로 모델 안에서 비교할 수 있습니다. 답하지 못하는 것은 **선택 편중**(제시됐을 때 고른 비율)과 **빌드 수렴**(판마다 구성이 얼마나 같은가)입니다. 봇의 선택 비율은 우리가 가중치로 정한 값이라 증거가 될 수 없고, 사람이 무엇을 보고 고르는지(카드 문구, 아이콘, 직전 판의 기억)는 모델에 없습니다. 그래서 앞의 둘은 11·12단계에서, 뒤의 둘은 24장 `level_up` 로그의 조건부 선택률과 판별 빌드 유사도로 잽니다. 두 쪽 결론이 어긋나면(예: 시뮬레이터에서는 약한 강화를 사람들이 계속 고른다) 밸런스가 아니라 **정보 전달의 문제**일 가능성이 큽니다.

</details>

**7. "콘텐츠 고갈"을 재는 세 지표를 쓰고, 고치는 세 레버를 비용이 싼 순서로 설명해보세요.**

<details><summary>모범 답안</summary>

지표는 **고갈 판 수**(영구 강화가 모두 최대가 되어 살 것이 없어지는 판), **최대 목표 공백**(구매와 다음 구매 사이의 최대 간격), **고갈 후 잉여**(그 뒤로 쌓이기만 하는 코인)입니다. 레버는 ① **비용 곡선 재배분**(총액을 유지한 채 성장률을 낮추고 기본가를 올려 마지막 몇 레벨의 한 걸음을 줄임 — 에셋 숫자 두 개), ② **해금 순서**(3종을 순서대로 열어 "다음에 뭐가 열릴까"라는 목표를 추가 — 대신 첫 세션의 체감이 늦어짐), ③ **새 Sink 추가**(캐릭터·외형 — 만들 것이 생기므로 가장 비쌈) 순입니다. 코인 러시는 ①로 목표 공백 6판 → 4판, 고갈 52판 → 48판을 달성했고 ②는 첫 세션 성취를 해쳐 기록만 남겼습니다.

</details>

## 핵심 요약

- 스프레드시트는 파라미터·계산·출력 시트로 나누고, 확정된 파라미터만 ScriptableObject에 옮깁니다.
- 판 안 경험치는 다항(지수 1.3~2), 판 밖 영구 강화 비용은 지수 공식이 어울립니다. 곡선을 바꾸면 구간마다 효과가 다르므로 분 단위로 확인합니다.
- 업그레이드는 선택당 DPS 증가율로 비교합니다. 합연산은 쌓일수록 약해지고 곱연산은 일정해 순위 역전이 생깁니다.
- 강화 규칙과 성장 공식은 순수 C# 한 곳(`UpgradeRules.cs`)에 두고, 실제 게임과 시뮬레이터가 같은 코드를 호출합니다. 레벨업·제단·영구 강화 3종이 모두 이 규칙으로 적용됩니다.
- 메타 경제는 Source/Sink로 그리고, 이월 코인 = 지갑(주운 코인 − 제단 소비) × 클리어 보너스입니다. 모든 가격을 "한 판당 이월"의 배수로 표현하고 "몇 판 만에 무엇을" 목표에서 역산합니다.
- 시뮬레이터는 일반 적(적체 HP, maxAlive 상한)과 이벤트 적(개체)을 분리하고, 매초 실제 구간 경계로 조회합니다. seed를 고정한 채 한 번에 하나씩 조정합니다.
- 결과는 특정 가정의 비교 모델입니다. 초보·숙련 가정을 함께 돌려 폭을 보고, 플레이테스트로 계수를 보정하기 전에는 절대 수치로 결론 내리지 않습니다.
- 제단 정책별로 클리어율과 이월을 함께 비교해 "항상 산다/안 산다"가 정답이 되지 않는지 확인합니다.
- 빌드는 강화 스택 벡터이고, 지배 전략은 **결과 지배·사문화·선택 편중·빌드 수렴** 네 신호로 판정합니다. 앞의 둘은 프로파일 시뮬레이션이, 뒤의 둘은 24장 실플레이 로그가 답합니다.
- 단일 우선 프로파일과 **금지(ablation) 실험**으로 "이 선택지가 빌드를 지탱하는가, 오히려 벌칙인가"를 가릅니다. 빼는 쪽이 결과가 좋아지면 그것은 선택지가 아닙니다.
- 지배 선택지는 출현 빈도가 아니라 **가치**를 고치고, 약화와 난이도 재보정을 한 묶음으로 처리합니다. 고친 것과 **측정하고 버린 안**을 함께 기록합니다.
- 콘텐츠 고갈은 고갈 판 수·최대 목표 공백·고갈 후 잉여로 재고, 비용 곡선 → 해금 순서 → 새 Sink 순으로 싼 레버부터 씁니다.

## 더 읽을거리

- Ian Schreiber & Brenda Romero, 「Game Balance」 (CRC Press) — 성장 곡선, 전이성·비전이성, 경제 설계를 수식과 스프레드시트로 다루는 교재
- Ian Schreiber, "Game Balance Concepts" 온라인 강좌 노트 — 위 책의 전신이 된 무료 강의 자료
- Joris Dormans, 「Game Mechanics: Advanced Game Design」 — Source/Sink 등 재화 흐름을 다이어그램(Machinations)으로 모델링
- Microsoft Learn — System.Random: https://learn.microsoft.com/dotnet/api/system.random
- Unity 매뉴얼 — MenuItem: https://docs.unity3d.com/ScriptReference/MenuItem.html
