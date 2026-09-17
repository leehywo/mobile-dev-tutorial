# 23. 밸런싱과 경제 설계

> **이 장에서 배울 것**
> - 선형·다항·지수 성장 공식의 차이를 설명하고, 경험치 요구량 곡선을 표로 설계한다
> - 업그레이드 선택지의 가치를 "DPS 증가율"로 비교해 정답이 뻔한 선택을 찾아낸다
> - 강화 규칙을 순수 C# 한 곳에 두고 **실제 게임과 시뮬레이터가 같은 규칙**을 쓰게 구현한다 (레벨업·코인 제단·영구 강화 3종)
> - 메타 재화의 Source/Sink, 한 판당 기대 획득량, 영구 강화 비용 곡선을 "몇 판 만에 무엇을" 목표에서 역산한다
> - 몬테카를로 시뮬레이터(`BalanceSimulator`)로 1000판을 돌려 생존 시간 분포를 얻고, 가정의 범위를 밝힌 채 수치를 조정한다
>
> **선수 장**: 03, 04, 10, 11, 21, 22 · **예상 시간**: 7~9시간 · **코인 러시 진행**: 레벨업 선택이 실제로 무기·체력에 적용됨, 코인 제단(판 안 소비)과 영구 강화 3종(판 밖 저축)이 동작함, `ProgressionData` 에셋, 에디터에서 1000판을 몇 초 만에 돌리는 밸런스 시뮬레이터, 조정 전후 기록

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

모델은 틀립니다. 위치, 이동, 무기 범위를 무시했고, **명중 효율·회피 한계·수집률·접촉 확률은 임의로 정한 계수**입니다. 랜덤 봇은 강화 선택만 무작위일 뿐, 이 계수들 때문에 사람보다 잘 피할 수도 못 피할 수도 있습니다. 그래서 결과는 "실제 난이도의 상한"도 "하한"도 아니고 **특정 가정 아래의 비교 모델**입니다. 쓰는 법은 두 가지입니다.

1. **같은 가정 안에서 상대 비교**: "경험치 곡선을 바꾸면 클리어율이 오르는가"의 방향과 크기.
2. **가정의 폭을 함께 보고**: 기준 가정 외에 초보·숙련 가정 시나리오를 나란히 돌려 결론이 뒤집히는지 봅니다. 계수는 24장 플레이테스트의 실제 사망 시각·수집량으로 보정하기 전까지 **탐색용 가설**입니다.

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

22장 위협 곡선 CSV의 `coins_per_min`을 모두 더하면 약 1,260개, 이벤트 드롭(엘리트 30·60, 박쥐 떼 24, 보스 300)이 414개입니다. 수집률 60%면 **모든 적을 처치했을 때** 약 1,000개입니다(22장 제단 표의 판 끝 값). 초안 곡선은 누적 1,000 부근이 레벨 18이고, 레벨 14부터 한 단계에 90개 이상이 필요해 후반 성장이 막힙니다. 실제로는 모든 적을 처치하지 못하므로 더 낮은 레벨에서 멈출 것입니다. 표만 봐도 의심이 가지만, 확신은 시뮬레이터로 얻습니다.

한 가지 더 볼 것이 있습니다. 조정안은 **L4~L10 구간에서 초안보다 조금 더 비쌉니다**(예: L5 14 대 12). 곡선을 바꾸면 모든 구간이 같은 방향으로 바뀌지 않으므로, 결과도 분 단위로 봐야 합니다.

### 2단계: 영구 강화 비용 표

21장 기획서대로 **영구 강화는 3종 × 10레벨**입니다. 공격력(+10% 피해/레벨), 최대 체력(+10/레벨), 수집 범위(+10%/레벨)에 같은 곡선 `cost(L) = 기본가 × 1.5^(L-1)`을 10 단위로 반올림해 씁니다. 표의 L은 **구매할 레벨**입니다. 현재 3레벨인 강화의 다음 가격은 `cost(4)`입니다.

| 구매 레벨 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 초안 기본가 200 | 200 | 300 | 450 | 680 | 1,010 | 1,520 | 2,280 | 3,420 | 5,130 | 7,690 |
| 초안 누적 | 200 | 500 | 950 | 1,630 | 2,640 | 4,160 | 6,440 | 9,860 | 14,990 | 22,680 |
| 채택 기본가 250 | 250 | 380 | 560 | 840 | 1,270 | 1,900 | 2,850 | 4,270 | 6,410 | 9,610 |
| 채택 누적 | 250 | 630 | 1,190 | 2,030 | 3,300 | 5,200 | 8,050 | 12,320 | 18,730 | 28,340 |

세 종류를 모두 최대로 올리면 채택안 기준 85,020 코인입니다. 한 판 이월이 1,000 안팎이라면 80판이 넘어 보이지만, 영구 강화가 쌓일수록 이월량도 늘어나니 실제로는 훨씬 적습니다. 정확한 판 수는 9단계에서 시뮬레이터로 확인합니다.

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
}

/// <summary>엘리트·보스·떼. 일반 적과 섞지 않고 "개체"로 추적한다.</summary>
public class SimEvent
{
    public int time, count;
    public float hpEach, contact, coinEach;   // hpEach는 배율 적용 후
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
            float dps = stats.Dps(c.baseDamage, c.baseCooldown, c.hitEfficiency);
            float eventTotal = 0f;
            foreach (float h in eventHp) eventTotal += h;
            float total = normalHp + eventTotal;
            if (total > 0f)
            {
                float toNormal = dps * normalHp / total;
                float killed = Math.Min(normalHp, toNormal);
                normalHp -= killed;
                float coins = killed / s.avgHp * s.avgCoin * pickup;

                float toEvents = dps - toNormal;
                for (int i = 0; i < eventHp.Count && toEvents > 0f; )
                {
                    float dealt = Math.Min(eventHp[i], toEvents);
                    eventHp[i] -= dealt; toEvents -= dealt;
                    if (eventHp[i] <= 0f)
                    {
                        coins += eventInfo[i].coinEach * pickup;
                        eventHp.RemoveAt(i); eventInfo.RemoveAt(i);
                    }
                    else i++;
                }
                collected += coins; wallet += coins; xp += coins;
            }

            // 3) 피격: 일반 적은 회피 한계를 넘은 수만큼, 이벤트 적은 개체마다
            float maxHp = c.baseMaxHp + stats.MaxHpBonus;
            float onScreen = normalHp / s.avgHp;
            float taken = Math.Max(0f, onScreen - c.dodgeCapacity) * s.avgContact * c.hitChancePerExcessEnemy;
            foreach (SimEvent e in eventInfo) taken += e.contact * c.eventHitChancePerSecond;
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
            }
            s.avgHp *= seg.hpMultiplier;
            c.segments.Add(s);
        }

        foreach (WaveEvent e in wave.events)
        {
            if (e.type == WaveEventType.Shrine) { c.shrineTimes.Add(Mathf.RoundToInt(e.time)); continue; }
            if (e.enemy == null) continue;
            float segMul = wave.GetSegment(e.time)?.hpMultiplier ?? 1f;
            c.events.Add(new SimEvent
            {
                time = Mathf.RoundToInt(e.time), count = e.count,
                hpEach = e.enemy.maxHp * segMul * e.hpMultiplier,
                contact = e.enemy.contactDamage, coinEach = e.enemy.coinDrop
            });
        }
        c.events.Sort((a, b) => a.time.CompareTo(b.time));
        c.shrineTimes.Sort();
        return c;
    }

    private static T FindAsset<T>() where T : Object
    {
        string[] guids = AssetDatabase.FindAssets($"t:{typeof(T).Name}");
        return guids.Length == 0 ? null : AssetDatabase.LoadAssetAtPath<T>(AssetDatabase.GUIDToAssetPath(guids[0]));
    }
}
```

`WaveSegment`는 `UnityEngine.Object`가 아닌 일반 클래스라서 `?.`와 `??`를 안전하게 쓸 수 있습니다(Unity 오브젝트에는 쓰지 마세요 — 기초 트랙 PART 5 지뢰 3번). 22장 연습 문제처럼 9:30에 보너스 러시 구간을 새로 만들면, 시뮬레이터도 9:00이 아니라 9:30부터 그 구간을 적용합니다.

### 9단계: 실행하고 해석하고 조정하기

1. Project 창에서 `Wave_Stage1`을 선택하고 **Coin Rush → Balance → Run Simulator** 를 실행합니다.
2. Console과 `Balance/sim_*.txt`에 결과가 나옵니다. 보통 몇 초 안에 끝납니다.

**조정 목표 (돌리기 전에 `Docs/balance-log.md`에 적음, 기준 가정·강화 0·제단 안 삼)**: 클리어율 20~35%, 어느 한 분에 사망 25% 이하, 생존 중앙값 6~9분, 한 판 평균 이월 600~900.

아래는 필자가 이 장의 코드와 22장 웨이브 표로 돌린 **실행 결과**입니다(지면을 줄이려고 0인 칸은 생략). .NET 런타임에 따라 난수 구현이 달라 수치가 몇 %p 달라질 수 있으니 경향만 비교하세요.

**조정 전 (22장 웨이브 표 + 11장 지수 경험치)**

```
[기준 가정] 1000판  클리어 6.8%  생존 중앙값 400초  평균 레벨 14.1  평균 수집 518  평균 이월 549
  분별 사망: 2분 2 | 3분 284 | 4분 95 | 5분 25 | 6분 158 | 7분 99 | 8분 24 | 9분 245 | 클리어 68
```

해석:

- **3분(28.4%)과 9분(24.5%)에 사망이 몰립니다.** 각각 엘리트와 보스 등장 시각입니다. 6분(엘리트 2)도 15.8%입니다.
- 평균 레벨 14.1 — 1단계 표에서 초안 곡선이 가팔라지기 시작하는 곳입니다. 성장이 막혀 이벤트 적을 뚫을 화력이 부족합니다.
- 원인 후보가 둘(경험치 곡선, 이벤트 체력)이므로 **한 번에 하나씩** 바꿉니다. 둘을 동시에 바꾸면 어느 쪽이 효과였는지 모릅니다.

**조정 1: 경험치 곡선 지수 1.25 → 다항 1.6** (`ProgressionData`의 Xp Curve `Polynomial`, Xp Power 1.6만 수정)

```
[기준 가정] 클리어 23.8%  생존 중앙값 394초  평균 레벨 15.0  평균 수집 535  평균 이월 653
  분별 사망: 2분 6 | 3분 313 | 4분 111 | 5분 16 | 6분 107 | 7분 67 | 8분 19 | 9분 123 | 클리어 238
```

- 클리어율이 3.5배가 되고 9분 사망이 절반으로 줄었습니다. 후반 성장 곡선이 주원인 중 하나였습니다.
- 하지만 **3분 사망은 오히려 늘었습니다**(284 → 313). 1단계 표에서 본 대로 조정안은 L4~L10 구간이 초안보다 조금 비싸 초반 성장이 느려졌기 때문입니다. 곡선 변경은 구간마다 효과가 다릅니다. 3분 벽은 경험치만으로는 해결되지 않습니다.

**조정 2: 엘리트 이벤트 체력 배율 1.0 → 0.6 (3:00, 6:00), 3:00~4:00 스폰율 1.2 → 0.9** (`WaveData`만 수정)

```
[기준 가정] 클리어 29.3%  생존 중앙값 451초  평균 레벨 15.9  평균 수집 602  평균 이월 745
  분별 사망: 2분 5 | 3분 208 | 4분 91 | 5분 63 | 6분 93 | 7분 76 | 8분 26 | 9분 145 | 클리어 293
```

조정 전후를 한 표로 정리해 `Docs/balance-log.md`에 남깁니다.

| 지표 | 조정 전 | 조정 1 (경험치) | 조정 2 (+엘리트·3분) | 목표 |
|---|---|---|---|---|
| 클리어율 | 6.8% | 23.8% | 29.3% | 20~35% |
| 생존 중앙값 | 400초 | 394초 | 451초 | 360~540초 |
| 3분 사망 비율 | **28.4%** | **31.3%** | 20.8% | 25% 이하 |
| 6분 사망 비율 | 15.8% | 10.7% | 9.3% | 25% 이하 |
| 9분(보스) 사망 비율 | 24.5% | 12.3% | 14.5% | 25% 이하 |
| 평균 레벨 | 14.1 | 15.0 | 15.9 | — |
| 한 판 평균 이월 코인 | 549 | 653 | 745 | 600~900 |

조정 2에서 모든 목표를 통과했습니다. 여기서 멈추고 "기준 가정"이 사람과 맞는지 24장에서 확인합니다.

**가정의 폭** — 같은 실행의 초보·숙련 시나리오입니다.

| 시나리오 (계수) | 클리어율 | 생존 중앙값 | 평균 이월 | 사망이 가장 몰린 분 |
|---|---|---|---|---|
| 초보 가정 (명중 0.65, 회피 6, 수집 0.5) | 0.0% | 235초 | 240 | 2분 34.7% |
| **기준 가정** (0.8, 10, 0.6) | 29.3% | 451초 | 745 | 3분 20.8% |
| 숙련 가정 (0.9, 16, 0.7) | 59.1% | 600초 | 1,259 | 4분 14.0% |

폭이 매우 넓습니다. 계수 조합에 따라 "아무도 못 깨는 게임"부터 "절반 넘게 깨는 게임"까지 나옵니다. 이벤트 적 접촉 확률(`eventHitChancePerSecond`) 하나만 0.10에서 0.15로 올려도 기준 가정 클리어율이 29.3%에서 약 2%로 떨어집니다. 그래서 이 표의 결론은 "조정 2가 맞다"가 아니라 **"경험치 곡선과 엘리트 체력의 방향은 모든 가정에서 같은 쪽으로 움직인다, 절대 난이도는 아직 모른다"**입니다. 24장에서 테스터의 실제 사망 시각 분포를 얻으면 세 시나리오 중 어느 쪽에 가까운지 보고 계수를 보정합니다.

### 10단계: 경제 검증 — 제단 전략과 영구 강화

같은 실행 결과의 나머지 시나리오입니다(조정 2, 기준 가정).

| 시나리오 | 클리어율 | 생존 중앙값 | 평균 이월 코인 | 제단 구매 |
|---|---|---|---|---|
| 제단 안 삼 (기본) | 29.3% | 451초 | 745 | 0회 |
| 제단 항상 삼 | 57.3% | 600초 | 602 | 3.2회 |
| 체력 60% 미만일 때만 삼 | 31.9% | 469초 | 722 | 0.3회 |
| 영구 강화 3종 1레벨 | 45.4% | 588초 | 1,008 | — |
| 영구 강화 3종 3레벨 | 65.4% | 600초 | 1,451 | — |
| 영구 강화 3종 5레벨 | 77.7% | 600초 | 1,799 | — |
| 영구 강화 3종 10레벨 | 88.6% | 600초 | 2,092 | — |

- **제단 긴장이 살아 있습니다.** 항상 사면 클리어율이 약 2배지만 이월 코인이 19% 줄어듭니다. 어느 쪽도 모든 지표에서 우세하지 않습니다.
- 처음에는 제단 강화를 **2단계**(`shrineStacks = 2`)로 줬습니다. 그때 결과는 "항상 삼: 클리어 72.5%, 이월 811"로, 사는 쪽이 **클리어율도 이월도 높았습니다.** 더 오래 살아 더 많이 줍기 때문입니다. 항상 사는 것이 정답이면 21장의 차별점이 무너지므로 1단계로 낮췄습니다. 이런 역전은 표 계산으로는 보이지 않고, 생존과 수집이 얽힌 시뮬레이션에서 드러납니다.
- 영구 강화가 쌓일수록 클리어율과 이월이 함께 오릅니다. 이것이 메타 루프의 가속감입니다. 다만 1레벨만으로 클리어율이 29% → 45%로 크게 뜁니다. 첫 강화의 체감은 좋지만, 24장에서 "두 번째 판이 너무 쉬워졌다"는 반응이 나오는지 함께 봅니다.
- 봇의 "체력 60% 미만일 때만" 정책은 거의 사지 않았습니다(0.3회). 21장이 원하는 "상황에 따라 선택이 바뀌는" 사람의 행동은 봇으로 흉내 낼 수 없으므로 24장 관찰의 몫입니다.

캠페인 시뮬레이션(가장 낮은 강화부터 구매)으로 역산 목표를 확인합니다. 메뉴는 seed 하나의 결과만 보여주므로, 아래 표는 seed 0~99로 100번 돌린 중앙값입니다.

| 목표 | 역산 목표 | 기본가 200 (초안) | 기본가 250 (채택) |
|---|---|---|---|
| 첫 클리어 | 2~4판 | 2판 | 2판 |
| 세 강화 모두 1레벨 | 1~2판 | 1판 | 2판 |
| 세 강화 모두 3레벨 | — | 4판 | 4판 |
| 세 강화 모두 5레벨 | 약 8판 | 7판 | 8판 |
| 세 강화 모두 10레벨 | 40~50판 | 37판 | 46판 |

초안은 끝까지 조금 빨라 약 6시간 만에 Sink가 바닥납니다. 기본가를 250으로 올려 목표 구간에 넣었습니다(`ProgressionData.upgradeBaseCost`). 이 판 수는 **기준 가정**의 결과이므로, 24장의 `upgrade_purchase` 이벤트로 실제 도달 판 수를 확인하고 차이가 크면 계수 보정 → 비용 재조정 순으로 진행합니다.

### 확인하기

- **게임**: Play → 레벨업에서 "투사체 +1"을 고르면 다음 발사부터 투사체가 부채꼴로 2발 나간다. "피해 +25%"를 고르면 데미지 숫자가 10 → 12로 바뀐다(12.5를 `Math.Round`가 짝수 쪽으로 반올림). 투사체를 5개까지 올리면 이후 레벨업·제단에 투사체 카드가 나오지 않는다.
- **제단**: 22장 **F3**로 1:56 근처로 가서 2:00에 노란 제단이 생기는지 보고, 닿으면 게임이 멈추고 "제단 강화 50 코인 (지갑 N)" 창이 뜬다. 지갑이 50 미만이면 강화 버튼이 눌리지 않고 "모으기"만 된다. 구매하면 지갑이 50 줄고 효과가 적용된다. 30초 안에 가지 않으면 제단이 사라진다.
- **정산**: 결과 화면의 이월 코인 = 지갑(클리어면 ×1.5). 판 도중 에디터 Play를 멈춘 뒤 다시 Play하면 타이틀 상점의 코인이 그 판 지갑만큼 늘어 있다.
- **영구 강화**: 상점에서 공격력 1레벨을 사면(가격 250) 다음 판 시작 무기 데미지가 11이 된다. 가격 표시가 "다음 380 코인"으로 바뀐다.
- **시뮬레이터**: 메뉴를 실행하면 Console에 시나리오 9개와 캠페인 1줄, 소요 시간이 출력되고, 같은 설정으로 두 번 실행하면 결과가 **완전히 같다**(고정 seed).
- `Docs/balance-log.md`에 조정 목표, 조정 전후 표, 가정의 폭 표가 있고, 각 조정마다 "무엇을 왜 바꿨는지" 한 줄이 있다.

## 흔한 실수

1. **증상**: 시뮬레이터 클리어율은 오르는데 실제로 해 보면 강화가 체감되지 않는다. → **원인**: 강화 효과가 시뮬레이터에만 있고 게임 코드에는 없음(또는 수치가 따로 적혀 어긋남). → **해결**: 효과 수치와 공식을 `UpgradeRules.cs` 한 곳에 두고 게임(`PlayerStats`)과 시뮬레이터가 같은 `CombatStats.Apply`를 부르게 합니다. 강화 선택 전후 데미지·발사 간격·투사체 수를 Play 중에 직접 확인합니다.
2. **증상**: 조정할 때마다 결과가 들쭉날쭉해서 좋아졌는지 모르겠다. → **원인**: 매번 다른 난수 seed, 혹은 표본이 100판 이하. → **해결**: 비교할 때는 seed를 고정하고 1000판 이상 돌립니다. 결론이 seed에 따라 뒤집히는지 seed 2~3개로 한 번 더 확인합니다.
3. **증상**: 여러 수치를 한꺼번에 바꿨더니 좋아졌지만 이유를 모른다. → **원인**: 변수 동시 변경. → **해결**: 한 번에 하나씩 바꾸고 로그에 기록합니다(9단계의 조정 1 → 조정 2).
4. **증상**: 시뮬레이터 클리어율 29%인데 테스터는 전부 클리어한다(혹은 아무도 못 한다). → **원인**: 모델 계수(명중 효율·회피 한계·수집률·접촉 확률)는 가정이고, 결과는 그 가정에 매우 민감함. → **해결**: 처음부터 초보·숙련 가정을 함께 돌려 폭을 보고, 플레이테스트(24장)의 사망 시각 분포·수집량으로 계수를 보정한 뒤 다시 조정합니다. 보정 전의 절대 수치로 "클리어율 29% 확정" 같은 결론을 내리지 않습니다.
5. **증상**: 제단에서 항상 사는 것(또는 항상 안 사는 것)이 정답이 되었다. → **원인**: 제단 강화가 생존을 늘려 수집량까지 늘리는 효과를 계산에 넣지 않음. → **해결**: 제단 정책별 시나리오로 클리어율과 **이월 코인을 함께** 비교합니다. 한쪽이 두 지표 모두 우세하면 제단 효과·가격을 조정합니다(10단계의 stacks 2 → 1).
6. **증상**: 출시 한 달 뒤 "코인이 쓸 데가 없다"는 리뷰. → **원인**: Sink 고갈(인플레이션). → **해결**: 캠페인 시뮬레이션으로 "모든 강화 완료" 판 수를 미리 확인하고, 그 이후의 Sink(캐릭터·외형·도전 모드 입장료)를 출시 전에 준비합니다.

## 연습 문제

**1. ★☆☆ 업그레이드 가치 계산**
피해 배율 2.0, 공격 속도 배율 1.52, 투사체 3인 상태입니다. +피해, +공격 속도, +투사체 각각의 DPS 증가율을 구하고 가장 좋은 선택을 고르세요.

<details><summary>힌트·해설</summary>

+피해: 2.25 ÷ 2.0 = +12.5%. +공격 속도: 항상 +15%. +투사체: 4 ÷ 3 = +33.3%. 투사체가 가장 좋습니다. 투사체가 최대(5)에 도달하면 곱연산인 공격 속도(+15%)가 합연산 피해(2.0 기준 +12.5%, 이후 더 감소)를 앞섭니다. 이 역전 지점을 알면 "초반엔 투사체, 후반엔 공격 속도"라는 전략이 생기고, 그것이 설계 의도에 맞는지 판단할 수 있습니다. 실제 게임에서 `ShotDamage`는 정수로 반올림하므로(`Math.Round`는 .5를 짝수 쪽으로 보냄) 기본 피해 10에서는 +25%가 한 발 12.5 → 12처럼 표보다 작게 나타난다는 점도 확인해 보세요. 체력이 작은 적을 상대로는 이런 반올림이 "몇 방에 죽는가"를 바꿉니다.

</details>

**2. ★★☆ 초보 가정의 2분 벽 낮추기**
초보 가정에서 2분 사망이 34.7%입니다. 초보 가정의 2분 사망을 20% 이하로 낮추되, 기준 가정의 클리어율은 35%를 넘지 않게 하는 조정을 두 가지 제안하고 시뮬레이터로 확인하세요.

<details><summary>힌트·해설</summary>

2분 벽은 이벤트가 아니라 **일반 적의 누적**(1:00~3:00 스폰율 1.2)과 초반 성장 속도에서 옵니다. 후보: (a) 1:00~2:00 스폰율 1.2 → 1.0, (b) 경험치 곡선의 L2~L6 구간을 완만하게(다항 `xpBase` 5 → 4), (c) 시작 무기 쿨다운 1.0 → 0.9. 하나씩 적용해 초보·기준·숙련 세 줄을 표에 기록합니다. (a)는 코인 공급도 줄이므로 22장 제단 표의 2:00 지갑이 50 아래로 떨어지지 않는지 함께 확인합니다. 초보만 쉽게 하는 조정은 드물기 때문에 "기준 가정 상한"을 같이 두는 것입니다. 초반을 쉽게 하면 중후반 클리어율도 따라 오르는 것이 보통입니다.

</details>

**3. ★★☆ 탐욕 봇 추가**
`SimulateRun`에 전략 매개변수를 추가해, 제시된 3개 중 "현재 상태에서 DPS 증가율이 가장 큰 것"을 고르는 탐욕 봇을 만드세요. 랜덤 봇과 클리어율을 비교하면 무엇을 알 수 있나요?

<details><summary>힌트·해설</summary>

`enum BotStrategy { Random, GreedyDps }`를 `SimConfig`에 넣고, `PickRandomOffer`에서 앞 3칸이 섞인 뒤 각 선택지를 적용했을 때의 DPS를 계산해 최대를 고릅니다. `CombatStats`를 복제할 수 없으므로 `Dps` 계산식에 선택지별 변화를 직접 넣거나, `CombatStats`에 `Clone()`을 추가합니다(규칙 파일에 넣으면 게임에서도 "추천 카드 표시" 같은 기능에 재사용할 수 있습니다). 탐욕 봇이 랜덤 봇보다 크게 앞서면 "선택에 실력 차가 반영된다"는 뜻이라 좋은 신호입니다. 반면 탐욕 봇이 생존 계열을 전혀 안 고르는데도 압도적이라면 생존 강화의 가치가 너무 낮은 것입니다. 단, 두 봇의 차이는 **강화 선택 실력**의 차이일 뿐 조작 실력(회피·수집)은 계수로 따로 정해지므로, 초보·숙련 체감 차이 전체로 읽지 않습니다.

</details>

**4. ★★★ 캐릭터 해금 Sink 설계**
"모든 영구 강화 완료" 이후를 위해 21장 스코프의 캐릭터 3종 중 해금 캐릭터 2종을 추가합니다. 해금 가격, 캐릭터의 시작 능력(`CombatStats`로 표현 가능해야 함), 해금 목표 판 수를 정하고, `SimulateCampaign`을 확장해 "세 강화 10레벨 + 캐릭터 2종" 도달 판 수를 구하세요. 파워 크립이 생기지 않았는지 캐릭터별 클리어율로 검증하세요.

<details><summary>힌트·해설</summary>

캐릭터를 "피해 −20%, 투사체 +1로 시작"처럼 트레이드오프로 설계하면 파워 크립 없이 다양성이 생깁니다. `CombatStats`에 캐릭터 보정을 받는 생성자 오버로드를 추가하면 게임(`PlayerStats`)과 시뮬레이터가 또 같은 규칙을 씁니다. 검증은 같은 영구 강화 레벨에서 캐릭터별 클리어율을 비교해 기본 캐릭터 대비 ±10%p 안쪽인지 봅니다. 해금 가격은 "강화 완료 후 한 판 이월 코인(10레벨 시나리오 약 2,100)"의 5~10배로 시작해 목표 판 수에 맞춥니다. 캠페인 루프에서 강화를 다 산 뒤에만 캐릭터를 사도록 우선순위를 두세요.

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

어느 한쪽이 모든 지표에서 우세하면 안 됩니다. 사면 이번 판 클리어율이 오르고, 모으면 이월 코인이 늘어 다음 판이 강해지는 트레이드오프가 둘 다 체감될 만큼 커야 합니다. 이 장의 결과에서는 항상 사면 클리어율 29% → 57%, 이월 745 → 602로 양쪽 모두 뚜렷한 차이가 있어 결정이 됩니다. 반대로 제단 강화가 2단계였을 때는 사는 쪽이 클리어율(72%)과 이월(811)이 모두 높아 항상 사는 것이 정답이 되었습니다. 생존이 늘면 수집도 늘기 때문에, 이 역전은 반드시 시뮬레이션으로 확인해야 합니다.

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

## 더 읽을거리

- Ian Schreiber & Brenda Romero, 「Game Balance」 (CRC Press) — 성장 곡선, 전이성·비전이성, 경제 설계를 수식과 스프레드시트로 다루는 교재
- Ian Schreiber, "Game Balance Concepts" 온라인 강좌 노트 — 위 책의 전신이 된 무료 강의 자료
- Joris Dormans, 「Game Mechanics: Advanced Game Design」 — Source/Sink 등 재화 흐름을 다이어그램(Machinations)으로 모델링
- Microsoft Learn — System.Random: https://learn.microsoft.com/dotnet/api/system.random
- Unity 매뉴얼 — MenuItem: https://docs.unity3d.com/ScriptReference/MenuItem.html
