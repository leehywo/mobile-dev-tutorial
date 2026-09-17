# 22. 난이도 곡선과 웨이브 디자인

> **이 장에서 배울 것**
> - 몰입(Flow) 채널과 긴장-이완 리듬으로 좋은 난이도 곡선의 조건을 설명할 수 있다
> - 플레이어 파워 곡선과 적 위협 곡선을 같은 단위(HP/초)로 놓고 교차 설계한다
> - 시간대별 스폰 규칙을 담는 `WaveData`(ScriptableObject)를 설계하고, `EnemySpawner`가 이를 읽게 구현한다
> - 공정한 죽음(예고·가독성)과 새 요소 소개 4단계를 웨이브 표에 반영한다
> - 위협 곡선 계산 도구와 시간 빨리감기 치트로 10분짜리 설계를 몇 분 안에 검증한다
>
> **선수 장**: 03, 05, 12, 17, 19 (20장을 했다면 웨이브 편집기와 함께 쓸 수 있음), 21 · **예상 시간**: 5~6시간 · **코인 러시 진행**: 분 단위로 설계된 10분 웨이브, 코인 제단 시각과 가격 근거, 엘리트·보스 예고, 보스 컷신 연결, 위협 곡선 CSV, 디버그 치트

## 왜 필요한가

지금 코인 러시의 `EnemySpawner`는 대략 이런 모양일 것입니다(05·12장).

```csharp
timer += Time.deltaTime;
if (timer >= spawnInterval)
{
    timer = 0f;
    spawnInterval = Mathf.Max(0.1f, spawnInterval * 0.98f); // 점점 빠르게
    Spawn(enemyPrefab);
}
```

"점점 빨라진다"는 단순한 규칙으로 10분을 채우면 세 가지 문제가 생깁니다.

1. **단조롭다.** 1분의 경험과 7분의 경험이 "적이 더 많다" 말고는 같습니다. 21장에서 정한 기둥 1(30초마다 결정)을 만족하지 못합니다.
2. **곡선이 어디서 터질지 모른다.** `0.98`을 매 스폰마다 곱하면 간격이 지수적으로 줄어듭니다. 어느 순간 플레이어 성장보다 빨라지는데, 그 시각을 코드를 읽어서는 알 수 없습니다.
3. **조정하려면 코드를 고쳐야 한다.** 숫자 하나 바꾸려고 컴파일을 기다리고, 10분을 직접 플레이해야 결과를 봅니다.

이 장에서는 난이도를 **데이터(웨이브 표)**로 바꾸고, 표를 **플레이어 파워와 비교해 계산**하고, 계산이 맞는지 **빨리감기로 확인**하는 흐름을 만듭니다.

## 개념

### 몰입(Flow) 채널

심리학자 미하이 칙센트미하이(Mihaly Csikszentmihalyi)가 설명한 몰입 상태는 **과제의 난이도와 사람의 실력이 균형을 이룰 때** 생깁니다. 게임 디자인에서는 보통 이렇게 그립니다.

```
 난이도
  ▲
  │                         ╱  불안 (너무 어려움)
  │                      ╱
  │           ░░░░░░░░╱░░░░░░░
  │        ░░░░░░░╱░░░░░░░░░       ← 몰입 채널
  │     ░░░░░░╱░░░░░░░░░
  │  ░░░░░╱░░░░░░░░░               지루함 (너무 쉬움)
  │    ╱
  └──────────────────────────────▶ 플레이어 실력(파워)
```

- 채널은 **대각선**입니다. 플레이어가 강해지면(서바이버라이크에서는 레벨업) 난이도도 올라가야 채널 안에 머뭅니다.
- 채널은 **폭이 있습니다.** 채널 안에서 위아래로 오가는 것은 괜찮고, 오히려 필요합니다. 계속 채널 한가운데에만 있으면 그것도 단조롭습니다.

### 난이도 곡선의 유형

| 유형 | 모양 | 장점 | 단점 | 어울리는 곳 |
|---|---|---|---|---|
| 선형 | `╱` | 예측 가능, 계산 쉬움 | 단조로움, 긴장-이완 없음 | 짧은 퍼즐, 튜토리얼 |
| 계단 | `_┌─┘┌─┘` | 새 구간마다 "새 국면" 체감 | 계단 직후 갑자기 어려움 | 스테이지제 게임, 분 단위 웨이브 |
| 톱니 | `╱│╱│╱│` | 긴장→해소 반복, 성취감 | 설계·검증 품이 많음 | 보스 사이클, 서바이버라이크 |

서바이버라이크에 맞는 것은 **"우상향하는 톱니"** 입니다. 전체 추세는 올라가지만, 엘리트나 보스 같은 **정점** 직후에는 잠깐 **이완**을 줍니다.

```
 위협
  ▲                                              ▲ 보스
  │                               ▲ 엘리트×2   ╱│
  │                ▲ 엘리트       ╱│        ╱╱  │
  │               ╱│         ╱╱╱  │ ╲  ╱╱╱      │
  │          ╱╱╱╱  │ ╲  ╱╱╱╱       └──          │
  │     ╱╱╱╱       └──                          │
  │╱╱╱╱                                          │
  └──────┬──────┬──────┬──────┬──────┬──────┬───▶ 시간(분)
         1      3      4      6      7      9  10
```

### 긴장-이완 리듬

긴장만 계속되면 피로해지고, 피로한 플레이어는 이탈합니다. 이완 구간이 하는 일은 다음과 같습니다.

- **보상을 체감할 시간**: 방금 얻은 강화로 적을 쓸어버리는 "파워 판타지" 순간
- **결정할 시간**: 코인 러시에서는 코인 제단(21장)이 2분마다 나옵니다. 제단은 이완 구간에 두어야 고민할 여유가 생깁니다.
- **다음 긴장의 대비 효과**: 조용한 30초 뒤의 경고음이 더 크게 들립니다.

코인 러시의 리듬 규칙은 다음과 같이 정합니다.

```
- 큰 정점(엘리트·보스) 직후 30~60초는 스폰율을 낮춘다
- 제단(2:00, 4:00, 6:00, 8:00)이 정점과 겹치면 정점 처리 뒤로 민다 → 6:00 제단은 6:30
- 새 적은 이완 구간에 소개한다 (다음 절의 4단계)
```

### 웨이브가 코인 제단의 결정을 만든다

21장 기획서의 훅은 "코인 = 경험치이자 화폐, **판 안 제단에서 쓸지 판 밖 영구 강화를 위해 모을지**의 결정"입니다. 웨이브는 이 결정의 무게를 정하는 쪽입니다. 같은 제단이라도 언제 열리고, 그때 지갑에 얼마가 있고, 다음에 무엇이 오는지에 따라 고민이 되기도 하고 뻔해지기도 합니다.

| 웨이브가 정하는 것 | 결정에 미치는 영향 | 코인 러시 배치 |
|---|---|---|
| 제단 **다음**에 오는 정점 | "지금 사면 다음 위기를 넘긴다"는 소비 동기 | 2:00 제단 → 3:00 엘리트, 8:00 제단 → 9:00 보스 |
| 제단 **직전**의 긴장 | 체력이 깎인 상태에서 도착하면 소비 쪽으로 기움 → 상황마다 답이 달라짐 | 4:00 제단은 3분 엘리트 뒤, 6:30 제단은 6분 엘리트 2마리 뒤 |
| 제단까지의 코인 공급 | 지갑이 가격보다 적으면 결정 자체가 없음 | 아래 표로 확인 |
| 이완 구간 | 가격·효과를 읽을 여유 | 제단은 모두 이완 또는 정점 직후에 둔다 |

그래서 제단도 웨이브 표의 **이벤트**로 관리합니다(3단계의 `WaveEventType.Shrine`). 시각을 바꿀 때 엘리트·보스와의 간격이 같은 표에서 보입니다.

가격은 코인 공급에서 역산합니다. 2단계 웨이브 표로 "모든 적을 처치하고 떨어진 코인의 60%를 주웠을 때" 제단 시각의 지갑을 계산하면 다음과 같습니다. 모든 적을 처치한다는 가정이라 **상한**이고, 실제 값은 23장 시뮬레이터로 확인합니다.

| 제단 | 누적 코인 공급 (상한, 수집 60%, 사지 않음) | 21장 그레이박스 가격 (100×n) | 조정 가격 (50×n) |
|---|---|---|---|
| 2:00 | 72 | 100 — **살 수 없음** | 50 |
| 4:00 | 194 | 200 — 살 수 없음 | 100 |
| 6:30 | 455 | 300 | 150 |
| 8:00 | 606 | 400 | 200 |
| 판 끝 (10:00) | 1,006 | 합계 1,000 | 합계 500 |

그레이박스 가격은 첫 두 제단에서 상한으로도 살 수 없어 "모으기"만 남습니다. 네 제단을 모두 사면 판 전체 코인이 사라지므로 저축과의 경쟁도 성립하지 않습니다. 가격을 50×n으로 낮추면 모든 제단에서 결정이 가능하고, 다 사도 절반가량이 남습니다. 이 수치(`shrineBasePrice = 50`)는 23장에서 시뮬레이터로 다시 검증합니다. 반대로 스폰율을 올리면 코인 공급도 올라 지갑이 가격을 크게 넘어서므로, **스폰율을 바꿀 때는 이 표도 함께 다시 계산**합니다.

### 서바이버라이크의 시간 기반 난이도

서바이버라이크는 플레이어의 위치나 진행도가 아니라 **경과 시간**이 난이도를 결정합니다. 조절 손잡이(knob)는 다섯 개입니다.

| 손잡이 | 효과 | 주의 |
|---|---|---|
| 스폰율 (마리/초) | 들어오는 적의 양 | 올리면 코인(경험치·제단 지갑)도 늘어 파워와 구매력이 같이 오름 |
| 최대 동시 수 | 화면 혼잡도, 성능 상한 | 상한에 막히면 스폰율을 올려도 효과 없음 |
| 적 구성 (종류·가중치) | 위협의 "질" — 빠른 적, 단단한 적 | 새 종류는 새 행동을 요구 |
| 체력 배율 | 같은 적이 더 오래 버팀 | 코인은 늘지 않으므로 파워 성장 둔화 |
| 이벤트 (엘리트·보스·떼) | 톱니의 정점 | 반드시 예고 |

특히 **스폰율과 체력 배율의 차이**를 기억하세요. 둘 다 "초당 들어오는 적 HP"를 늘리지만, 스폰율은 코인(= 경험치)도 늘리고 체력 배율은 늘리지 않습니다. 후반에 플레이어가 너무 빨리 성장한다면 스폰율 대신 체력 배율을 올리는 것이 한 방법입니다.

### 파워 곡선 vs 위협 곡선: 같은 단위로 놓기

"어렵다/쉽다"를 계산하려면 플레이어와 적을 같은 단위로 표현해야 합니다. 가장 간단한 공통 단위는 **HP/초**입니다.

```
위협(들어오는 HP/초) = 스폰율 × 평균 적 체력 × 체력 배율
평균 적 체력 = Σ(적 체력 × 가중치) ÷ Σ(가중치)

유효 DPS(처리하는 HP/초) = 무기 피해 × (1 / 쿨다운) × 투사체 수 × 명중 효율
명중 효율 = 빗나감·오버킬(이미 죽을 적에게 들어간 피해)을 뺀 비율. 예시로 0.8
```

그리고 두 값의 비율을 봅니다.

```
위협 비율 = 위협 ÷ 예상 유효 DPS

  < 0.6   이완 — 적이 쌓이지 않고 금방 정리됨
  0.6~0.9 몰입 — 적이 조금씩 쌓였다 정리되기를 반복
  > 1.0   긴장 — 적이 계속 쌓임. 짧게(정점)만 허용
```

위협이 DPS를 넘는 동안 화면에 적이 **누적**됩니다. 누적이 곧 피격 위험이므로, 위협 비율 1.0 이상은 톱니의 정점에서만 짧게 씁니다.

### DPS 요구치 계산 예

코인 러시의 시작 무기(예시 수치): 피해 10, 쿨다운 1.0초, 투사체 1개.

```
시작 유효 DPS = 10 × (1/1.0) × 1 × 0.8 = 8 HP/초
```

0~1분 구간이 슬라임(체력 10)만 초당 0.8마리라면 위협은 `0.8 × 10 × 1.0 = 8 HP/초`, 비율은 1.0입니다. 시작부터 긴장 구간이라는 뜻이지만, 첫 레벨업이 수 초 안에 오므로 바로 0.7 근처로 내려갑니다. 이런 식으로 **분마다 "그 시각의 예상 파워"를 가정**하고 위협을 맞춥니다.

예상 파워는 처음엔 가정일 수밖에 없습니다. "3분에 레벨 10쯤, 강화 하나당 평균 +12%" 같은 가정으로 시작하고, 23장의 시뮬레이터로 가정 자체를 검증합니다.

### 공정한 죽음: 예고와 가독성

플레이어가 죽음을 받아들이는지는 **"내가 뭘 잘못했는지 아는가"**에 달려 있습니다.

| 불공정하게 느끼는 죽음 | 공정하게 만드는 장치 |
|---|---|
| 화면 밖에서 빠른 적이 갑자기 나타나 즉사 | 스폰은 화면 밖 일정 거리에서, 빠른 적은 첫 등장 시 소수로 |
| 보스가 플레이어 바로 옆에 스폰 | 보스는 3~5초 전 경고 문구 + 등장 방향 표시 |
| 적 수백 마리에 가려 투사체가 안 보임 | 적 투사체는 밝은 색·외곽선(14·15장), 플레이어 위 레이어 |
| 무엇에 맞아 죽었는지 모름 | 결과 화면에 사망 원인(적 종류) 표시 — 24장 `run_end.cause`로도 기록 |
| 피격 판정이 스프라이트보다 큼 | 플레이어 피격 콜라이더는 스프라이트보다 작게 (07장) |

### 동적 난이도 조절(DDA)의 장단

동적 난이도 조절(Dynamic Difficulty Adjustment)은 플레이어 상태를 보고 난이도를 실시간으로 바꾸는 기법입니다. 예를 들어 "체력이 30% 이하면 스폰율 ×0.7".

| 장점 | 단점 |
|---|---|
| 실력 편차가 큰 대중에게 이탈 감소 | 들키면 성취감이 사라짐 ("봐준 거였어?") |
| 한 번의 설계로 넓은 실력대 커버 | 잘하는 플레이어 역차별·악용, 재현이 어려워 밸런스 검증 곤란 |

코인 러시의 결정은 다음과 같습니다.

```
- 숨겨진 DDA는 쓰지 않는다 (기둥: 공정한 결정)
- 대신 난이도 조절을 "플레이어가 보이는 선택"으로 준다
  → 영구 강화(23장), 코인 제단 구매(23장), 추후 난이도 선택
    (부활 광고는 모바일 확장판에서만, 25장)
- 예외: 성능 보호용 최대 동시 수 상한은 DDA가 아니라 기술 제약으로 유지
```

### 새 요소 소개 4단계

닌텐도 게임 디자인에서 자주 언급되는 기승전결식 소개 방법입니다. 새 적이나 새 규칙을 한 번에 던지지 않고 네 단계로 소개합니다.

| 단계 | 뜻 | 코인 러시의 박쥐(빠른 적) 예 |
|---|---|---|
| 도입 | 안전한 상황에서 단독으로 보여줌 | 1:00, 슬라임 사이에 박쥐가 소수 섞여 등장 |
| 연습 | 반복하며 익힘 | 1~3분, 구성 비율 30~40% |
| 변형 | 비틀어서 새 대응을 요구 | 4:30, 박쥐 떼 24마리가 원형으로 포위 |
| 조합 | 다른 요소와 섞어 시험 | 6:00 이후, 느린 골렘이 길을 막는 사이 박쥐가 파고듦 |

## 실습: 코인 러시에 적용하기

### 1단계: 적 데이터 정리

03장에서 만든 `EnemyData` 에셋의 수치를 다음과 같이 맞춥니다. **모두 예시 수치**이며 23장에서 시뮬레이터로 조정합니다.

| 에셋 | maxHp | moveSpeed | contactDamage | coinDrop | 역할 |
|---|---|---|---|---|---|
| Enemy_Slime | 10 | 1.5 | 5 | 1 | 기본, 느리고 약함 |
| Enemy_Bat | 6 | 3.0 | 4 | 1 | 빠름, 회피 강요 |
| Enemy_Skeleton | 30 | 1.8 | 8 | 2 | 중간 |
| Enemy_Golem | 120 | 1.0 | 15 | 6 | 느린 탱커, 길 막기 |
| Enemy_EliteKnight | 400 | 2.0 | 20 | 30 | 엘리트 (3:00, 6:00) |
| Enemy_KingGolem | 3000 | 1.2 | 30 | 300 | 보스 (9:00) |

> 이 장의 코드는 03장 `EnemyData`의 필드 `maxHp`, `contactDamage`, `coinDrop`, `prefab`(GameObject)을 그대로 씁니다. 03장에서 이름을 다르게 지었다면 코드 쪽 이름만 맞추세요.

### 2단계: 10분 웨이브 표 (완성본)

스프레드시트에 먼저 표를 만들고 계산 열을 채운 뒤 에셋으로 옮깁니다. 계산 열(평균 체력, 위협)은 수식입니다. 예상 유효 DPS는 "분이 끝날 무렵 평범한 플레이어의 DPS"를 가정한 값입니다.

| 구간 | 구성 (가중치) | 스폰율 (마리/초) | 최대 동시 | 체력 배율 | 평균 체력 | 위협 (HP/초) | 예상 유효 DPS | 위협 비율 | 리듬 | 이벤트 / 의도 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0:00~1:00 | 슬라임 100 | 0.8 | 30 | 1.00 | 10.0 | 8.0 | 12 | 0.67 | 몰입 | 조작 익히기 |
| 1:00~2:00 | 슬라임 70, 박쥐 30 | 1.2 | 50 | 1.00 | 8.8 | 10.6 | 18 | 0.59 | 이완→몰입 | 박쥐 도입 |
| 2:00~3:00 | 슬라임 50, 박쥐 30, 해골 20 | 1.2 | 60 | 1.00 | 12.8 | 15.4 | 25 | 0.62 | 몰입 | 2:00 제단(50), 해골 도입 |
| 3:00~4:00 | 슬라임 40, 박쥐 40, 해골 20 | 1.2 | 60 | 1.10 | 13.6 | 16.4 | 30 | 0.55 | **정점→이완** | 2:57 경고, 3:00 엘리트 1 |
| 4:00~5:00 | 슬라임 30, 박쥐 30, 해골 40 | 1.5 | 80 | 1.10 | 18.5 | 27.7 | 40 | 0.69 | 몰입 | 4:00 제단(100), 4:30 박쥐 떼(변형) |
| 5:00~6:00 | 슬라임 20, 박쥐 30, 해골 50 | 1.7 | 100 | 1.15 | 21.6 | 36.8 | 50 | 0.74 | 긴장 상승 | 골렘 등장 전 압박 |
| 6:00~7:00 | 해골 50, 박쥐 40, 골렘 10 | 1.2 | 100 | 1.15 | 33.8 | 40.6 | 58 | 0.70 | **정점→이완** | 5:57 경고, 6:00 엘리트 2 → 6:30 제단(150), 골렘 도입 |
| 7:00~8:00 | 해골 50, 박쥐 30, 골렘 20 | 1.2 | 120 | 1.20 | 49.0 | 58.8 | 72 | 0.82 | 긴장 | 골렘+박쥐 조합 |
| 8:00~9:00 | 해골 50, 박쥐 20, 골렘 30 | 1.1 | 150 | 1.20 | 62.6 | 68.9 | 85 | 0.81 | 긴장 | 8:00 제단(200) — 보스 직전 마지막 소비 기회 |
| 9:00~10:00 | 해골 50, 골렘 50 | 0.7 | 120 | 1.20 | 90.0 | 63.0 | 100 | 0.63 | **최종 정점** | 8:55 경고, 9:00 보스 |

이벤트 표도 따로 둡니다.

| 시각 | 종류 | 적 | 수 | 이벤트 체력 배율 | 경고 (초 전) | 경고 문구 |
|---|---|---|---|---|---|---|
| 2:00 | Shrine | — | — | — | 3 | "코인 제단이 열린다" |
| 3:00 | Elite | Enemy_EliteKnight | 1 | 1.0 | 3 | "무언가 다가온다…" |
| 4:00 | Shrine | — | — | — | 3 | "코인 제단이 열린다" |
| 4:30 | Swarm | Enemy_Bat | 24 | 1.0 | 2 | "박쥐 떼!" |
| 6:00 | Elite | Enemy_EliteKnight | 2 | 1.0 | 3 | "기사들이 온다" |
| 6:30 | Shrine | — | — | — | 3 | "코인 제단이 열린다" |
| 8:00 | Shrine | — | — | — | 3 | "마지막 코인 제단 — 보스가 가깝다" |
| 9:00 | Boss | Enemy_KingGolem | 1 | 1.0 | 5 | "코인 골렘왕 출현" |

제단 이벤트의 유지 시간(`activeSeconds`)은 21장 기획서대로 30초입니다. 제단 자체(가격·구매 창)는 23장에서 이 이벤트를 받아 구현합니다.

- **3:00~4:00의 스폰율은 2:00~3:00과 같습니다.** 대신 엘리트(체력 400 × 1.1 = 440)가 한꺼번에 들어옵니다. 엘리트가 정리되면 일반 적의 위협 비율이 0.55로 낮아 이완이 됩니다.
- **6:00~7:00은 스폰율을 1.7에서 1.2로 오히려 낮췄습니다.** 엘리트 2마리 + 골렘 도입이라는 정점을 위한 자리 비우기입니다.
- **9:00~10:00의 스폰율 0.7**은 보스전 동안 일반 적이 보스를 가리지 않게 하려는 것입니다(가독성).
- **최대 동시 수**는 "위협 ÷ 예상 DPS"가 1을 넘을 때 쌓일 수 있는 양의 상한이자 18장에서 정한 성능 예산입니다.

### 3단계: WaveData 구조

20장에서 웨이브 편집기를 만들었다면 그 편집기가 다루는 데이터를 여기서 확정합니다. 필드 이름이 다르다면 이 장의 구조로 맞추세요. 파일: `Assets/_CoinRush/Scripts/Waves/WaveData.cs`

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "WaveData", menuName = "Coin Rush/Wave Data")]
public class WaveData : ScriptableObject
{
    [Min(1f)] public float runDuration = 600f;                          // 이 시각에 도달하면 클리어
    public List<WaveSegment> segments = new List<WaveSegment>();        // startTime 오름차순, 빈틈 없이
    public List<WaveEvent> events = new List<WaveEvent>();              // 엘리트·보스·떼

    public WaveSegment GetSegment(float time)
    {
        foreach (WaveSegment s in segments)
            if (time >= s.startTime && time < s.endTime) return s;
        // runDuration 시각 자체는 마지막 구간으로 취급
        return segments.Count > 0 && time >= segments[segments.Count - 1].endTime - 0.001f
            ? segments[segments.Count - 1] : null;
    }

#if UNITY_EDITOR
    // 에셋을 수정할 때마다 에디터가 호출 → 표를 옮기다 생긴 실수를 바로 경고
    private void OnValidate()
    {
        for (int i = 0; i < segments.Count; i++)
        {
            WaveSegment s = segments[i];
            if (s.endTime <= s.startTime)
                Debug.LogWarning($"[{name}] 구간 {i}: endTime이 startTime보다 커야 합니다.", this);
            if (i > 0 && !Mathf.Approximately(segments[i - 1].endTime, s.startTime))
                Debug.LogWarning($"[{name}] 구간 {i - 1}~{i} 사이에 빈틈 또는 겹침이 있습니다.", this);
            if (s.TotalWeight() <= 0)
                Debug.LogWarning($"[{name}] 구간 {i}: 가중치 합이 0입니다.", this);
        }
    }
#endif
}

[Serializable]
public class WaveSegment
{
    public string label = "0:00~1:00";
    [Min(0f)] public float startTime;
    [Min(0f)] public float endTime = 60f;
    [Min(0f)] public float spawnsPerSecond = 1f;
    [Min(1)] public int maxAlive = 50;
    [Min(0.1f)] public float hpMultiplier = 1f;
    public List<SpawnEntry> entries = new List<SpawnEntry>();

    public int TotalWeight()
    {
        int total = 0;
        foreach (SpawnEntry e in entries)
            if (e.enemy != null) total += e.weight;
        return total;
    }

    // 가중치 무작위 선택 (06장 LootTable과 같은 원리)
    public EnemyData PickEnemy()
    {
        int roll = UnityEngine.Random.Range(0, TotalWeight()); // 합이 0이면 0 반환 → 아래에서 null
        foreach (SpawnEntry e in entries)
        {
            if (e.enemy == null) continue;
            if (roll < e.weight) return e.enemy;
            roll -= e.weight;
        }
        return null;
    }
}

[Serializable]
public class SpawnEntry
{
    public EnemyData enemy;
    [Min(0)] public int weight = 10;
}

// Elite·Boss: 한 방향에서 나란히, Swarm: 원형 포위, Shrine: 적 없음 — 코인 제단 열림 (23장)
// 새 값은 반드시 끝에 추가 (에셋에는 숫자로 저장되므로 순서를 바꾸면 기존 이벤트 종류가 바뀐다)
public enum WaveEventType { Elite, Boss, Swarm, Shrine }

[Serializable]
public class WaveEvent
{
    public string label = "Elite 3:00";
    [Min(0f)] public float time = 180f;
    public WaveEventType type = WaveEventType.Elite;
    public EnemyData enemy;                         // Shrine이면 비워 둠
    [Min(1)] public int count = 1;
    [Min(0.1f)] public float hpMultiplier = 1f;   // 구간 체력 배율에 추가로 곱함
    [Min(0f)] public float warningSeconds = 3f;
    public string warningText = "무언가 다가온다…";
    [Min(1f)] public float activeSeconds = 30f;    // Shrine 전용: 제단 유지 시간
}
```

**구간(배경 압력)과 이벤트(톱니의 정점)를 분리**한 것이 핵심입니다. 한 리스트로 섞으면 표로 옮기기도 계산하기도 어렵습니다. `[Serializable]` 일반 클래스라 Inspector에서 리스트로 편집됩니다(JS: JSON 스키마를 TypeScript 타입으로 정의한 것과 비슷).

1. `Assets/_CoinRush/Data/Waves/`에서 우클릭 → **Create → Coin Rush → Wave Data** → 이름 `Wave_Stage1`.
2. `Segments` 10개, `Events` 8개(제단 4 + 엘리트·떼·보스 4)를 2단계 표대로 채웁니다(20장 CSV 임포터가 있다면 그것으로). 20장 편집기 타임라인에서 Shrine은 Elite·Boss가 아닌 색(보라)으로 표시됩니다.
3. Console에 `OnValidate` 경고가 없는지 확인합니다.

### 4단계: Enemy — 체력 배율을 받아 한 번만 초기화

풀에서 꺼낸 적의 최대 체력에 구간·이벤트 배율을 곱해야 합니다. 이때 **초기화를 두 번 하면 안 됩니다.** 12장 `Init`이 기본 체력(예: 엘리트 400)으로 `Health.Initialize`를 부른 뒤 다시 배율(예: 23장의 0.6 → 264)을 적용하면, 체력이 400 → 264로 **줄어드는** `Changed`가 발생합니다. 12장 `Enemy.OnHealthChanged`, 14장 `HitFlash`, 16장 `HitFeedback`은 모두 "체력 감소 = 피격"으로 해석하므로, 생성 순간 136짜리 데미지 숫자·번쩍임·흔들림이 나옵니다.

규칙은 하나입니다. **최종 최대 체력을 계산해 `Initialize`를 한 번만 부르고, 초기화로 생기는 변화는 항상 "증가"가 되게 합니다.** 12장 `Enemy.cs`의 `Init` 메서드를 아래로 교체합니다(12장 필드 `data`, `target`, `pools`, `body`, `health`, `lastHp` 사용. 매개변수 기본값 덕분에 19장 스포너·18장 스트레스 스포너의 `Init(type, player, pools)` 호출도 그대로 컴파일됩니다).

```csharp
// Enemy.cs (12장) — Init 교체
public void Init(EnemyData enemyData, Transform player, GameplayPools gameplayPools, float hpMultiplier = 1f)
{
    data = enemyData;
    target = player;
    pools = gameplayPools;
    body.linearVelocity = Vector2.zero;

    // 지난 생의 lastHp를 0으로 → Initialize가 보내는 Changed는 항상 "증가"라 피해로 처리되지 않음
    lastHp = 0;
    int finalMax = Mathf.Max(1, Mathf.RoundToInt(data.maxHp * hpMultiplier));
    health.Initialize(finalMax);   // 01장 메서드: 최대 체력 설정 + 가득 채움 + Changed 한 번
}
```

`HitFlash`·`HitFeedback`은 `OnEnable`에서 `lastHp = health.Current`로 시작합니다. 프리팹의 `Health` **Max 값이 실제 체력보다 크면** 첫 생성 때 여전히 "감소"로 보이므로, **모든 적 프리팹의 `Health` Max를 1로** 둡니다. 실제 값은 항상 `Init`이 `EnemyData`에서 넣습니다.

반환도 스포너가 맡습니다. 단, 스포너가 `Health.Died`를 직접 구독해 반환하면 `Enemy.OnDied`보다 먼저 실행될 수 있고, 그러면 적이 비활성화(`isSpawned = false`)된 뒤라 코인이 떨어지지 않습니다. 그래서 **적이 드롭 → 사망 연출을 끝낸 뒤 "반환 요청"을 보내고, 스포너는 그 요청만 받아 반환**합니다. `Enemy.cs`에 아래를 추가하고, 14장 디졸브 완료 콜백 안의 `Pool.Release(this);`(14장을 건너뛰었다면 12장 `OnDied`의 것)를 `RequestRelease();`로 바꿉니다.

```csharp
// Enemy.cs 클래스 안에 추가 — 사망 처리가 모두 끝난 뒤 호출
// using System;을 추가하면 Random이 모호해지므로(01장) 전체 이름으로 씀
public event System.Action<Enemy> ReleaseRequested;   // 스포너가 구독

private void RequestRelease()
{
    if (ReleaseRequested != null) ReleaseRequested(this);
    else Pool?.Release(this);                   // 12장 스포너처럼 Pool을 직접 받은 경우
}
```

### 5단계: WaveData를 읽는 EnemySpawner

**19장** `EnemySpawner`(스테이지 로드 후 `Prewarm`, 언로드 때 `ClearPools`, 준비 전에는 스폰하지 않는 `IsReady`)를 아래 파일로 **교체**합니다. 19장 `StageLoader`가 부르는 세 멤버는 이름과 의미를 그대로 유지하고, "언제 무엇을 몇 마리 어디에"를 WaveData가 결정하게 바꿉니다. 파일: `Assets/_CoinRush/Scripts/Enemies/EnemySpawner.cs`

스폰 위치도 바꿉니다. 12·19장처럼 **플레이어 중심** 원 위에서 뽑으면, 17장 Confiner로 카메라가 맵 경계에 막혀 플레이어가 화면 가장자리에 있을 때 반대편 원 위의 점이 **화면 안**에 들어옵니다. 그래서 실제 **카메라 사각형 바깥 테두리**에서 뽑고, 플레이어와의 최소 거리를 따로 검사합니다(직교 카메라 기준).

```
  카메라가 맵 경계에 막힌 경우                 이 장의 방식
  ┌──────────화면──────────┐                  ·  ·  ·  ·  ·  ·  ·   ← 화면 테두리 + margin
  │                     P ●│ ← 플레이어         · ┌────화면────┐ ·
  │   ◯ 플레이어 중심 원이   │                    · │         P ●│ ·
  │   화면 안을 지나감       │                    · └───────────┘ ·
  └────────────────────────┘                    ·  ·  ·  ·  ·  ·  ·
```

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Pool;

public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private WaveData waveData;
    [SerializeField] private Transform player;
    [SerializeField] private GameplayPools gameplayPools;   // 12장 — 적이 코인·데미지 숫자를 꺼낼 때 사용

    [Header("스폰 위치")]
    [SerializeField] private float spawnMargin = 1.5f;       // 화면 테두리 밖 여유 (월드 단위)
    [SerializeField] private float minPlayerDistance = 6f;   // 플레이어와의 최소 거리
    [SerializeField] private Collider2D mapBounds;           // 17장 CameraBounds. 엘리트·보스는 맵 안에서만

    [Header("풀")]
    [SerializeField] private int prewarmPerEnemy = 32;
    [SerializeField] private int poolMaxSizePerEnemy = 400;

    [Header("보스 연출 (17장)")]
    [SerializeField] private VoidEventChannel bossSpawnRequested;

    public event Action<WaveEvent> EventWarning;   // 이벤트 warningSeconds 전 (HUD 경고)
    public event Action<WaveEvent> EventStarted;   // 이벤트 적이 스폰된 순간 / 제단이 열린 순간
    public event Action RunTimeCompleted;          // runDuration 도달 (클리어)
    public event Action EnemyKilled;               // 적이 죽어 풀로 돌아갈 때 (26장 업적·통계용)

    public float Elapsed { get; private set; }
    public int AliveCount { get; private set; }
    public Enemy LastBoss { get; private set; }    // 17장 컷신이 카메라를 맞출 대상
    public bool IsReady { get; private set; }      // 19장: Prewarm 전·ClearPools 후에는 false
    public bool IsCompleted => completed;          // runDuration 도달 여부 (이벤트 구독 순서와 무관하게 확인용)

    private readonly Dictionary<EnemyData, ObjectPool<Enemy>> pools = new Dictionary<EnemyData, ObjectPool<Enemy>>();
    private readonly List<WaveEvent> byStartTime = new List<WaveEvent>();     // 등장 시각순
    private readonly List<WaveEvent> byWarningTime = new List<WaveEvent>();   // 경고 시각(time - warningSeconds)순
    private Camera cam;
    private float spawnBudget;   // 소수점 스폰을 누적하는 "예산"
    private int nextWarningIndex, nextEventIndex;
    private bool completed;

    private static float WarningTime(WaveEvent e) => e.time - e.warningSeconds;

    private void Awake()
    {
        cam = Camera.main;
        byStartTime.AddRange(waveData.events);
        byStartTime.Sort((a, b) => a.time.CompareTo(b.time));
        // 경고 길이가 이벤트마다 다르므로 따로 정렬 (180초·3초 경고 뒤에 181초·10초 경고가 올 수 있다)
        byWarningTime.AddRange(waveData.events);
        byWarningTime.Sort((a, b) => WarningTime(a).CompareTo(WarningTime(b)));
    }

    // ---------- 19장 StageLoader가 부르는 멤버 ----------

    public void Prewarm(IReadOnlyList<EnemyData> datas)
    {
        foreach (EnemyData data in datas)
        {
            ObjectPool<Enemy> pool = GetPool(data);
            if (pool.CountAll > 0) continue;   // 이미 만든 풀
            var temp = ListPool<Enemy>.Get();
            for (int i = 0; i < prewarmPerEnemy; i++) temp.Add(pool.Get());   // 생성만 (비활성 상태)
            foreach (Enemy e in temp) pool.Release(e);
            ListPool<Enemy>.Release(temp);
        }
        IsReady = true;   // 웨이브에만 있고 스테이지 목록에 없는 적은 첫 스폰 때 풀을 만든다
    }

    public void ClearPools()
    {
        IsReady = false;                                         // 먼저 스폰을 멈춤
        foreach (ObjectPool<Enemy> pool in pools.Values) pool.Clear();   // 반납된 인스턴스 파괴
        pools.Clear();
        foreach (Transform child in transform) Destroy(child.gameObject);   // 필드에 나와 있던 적도 제거
        AliveCount = 0;
        spawnBudget = 0f;
        LastBoss = null;
    }

    // ---------- 진행 ----------

    private void Update()
    {
        if (!IsReady || completed) return;
        float dt = Time.deltaTime;   // LevelUp 상태에서 timeScale = 0이면 시간도 멈춘다
        Elapsed += dt;
        TickEvents();
        TickSegment(dt);
        if (Elapsed >= waveData.runDuration)
        {
            completed = true;
            RunTimeCompleted?.Invoke();
        }
    }

    private void TickSegment(float dt)
    {
        WaveSegment seg = waveData.GetSegment(Elapsed);
        if (seg == null) return;

        // 초당 1.2마리 → 매 프레임 1.2 * dt씩 예산이 쌓이고, 1 이상이면 1마리 스폰
        spawnBudget += seg.spawnsPerSecond * dt;
        while (spawnBudget >= 1f)
        {
            spawnBudget -= 1f;
            if (AliveCount >= seg.maxAlive)
            {
                spawnBudget = 0f;   // 상한에 막힌 예산은 버린다 (나중에 몰아서 쏟아지지 않게)
                break;
            }
            EnemyData data = seg.PickEnemy();
            if (data != null) SpawnEnemy(data, seg.hpMultiplier, PickSpawnPoint(mustBeInsideMap: false));
        }
    }

    private void TickEvents()
    {
        while (nextWarningIndex < byWarningTime.Count && Elapsed >= WarningTime(byWarningTime[nextWarningIndex]))
        {
            WaveEvent warned = byWarningTime[nextWarningIndex];
            nextWarningIndex++;   // 주의: ?.Invoke(list[i++])로 쓰면 구독자가 없을 때 i++가 실행되지 않는다
            EventWarning?.Invoke(warned);
        }

        while (nextEventIndex < byStartTime.Count && Elapsed >= byStartTime[nextEventIndex].time)
        {
            WaveEvent started = byStartTime[nextEventIndex];
            nextEventIndex++;
            StartEvent(started);
        }
    }

    private void StartEvent(WaveEvent e)
    {
        if (e.type == WaveEventType.Shrine)
        {
            EventStarted?.Invoke(e);   // 적 없음. 23장 CoinShrine이 받아서 제단을 연다
            return;
        }
        if (e.enemy == null) return;

        WaveSegment seg = waveData.GetSegment(e.time);
        float hpMul = (seg != null ? seg.hpMultiplier : 1f) * e.hpMultiplier;

        if (e.type == WaveEventType.Swarm)
        {
            // 카메라 중심 원: 반지름이 화면 대각선 절반 + margin이라 원 전체가 화면 밖
            Vector2 center = cam.transform.position;
            float radius = HalfDiagonal() + spawnMargin;
            for (int i = 0; i < e.count; i++)
            {
                float angle = i * Mathf.PI * 2f / e.count;
                SpawnEnemy(e.enemy, hpMul, center + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * radius);
            }
        }
        else
        {
            // 엘리트·보스는 맵 안 한 지점에서 나란히 → 플레이어가 방향을 읽을 수 있다
            Vector2 anchor = PickSpawnPoint(mustBeInsideMap: true);
            Vector2 dir = anchor - (Vector2)player.position;
            dir = dir.sqrMagnitude > 0.0001f ? dir.normalized : Vector2.right;
            Vector2 side = new Vector2(-dir.y, dir.x);
            for (int i = 0; i < e.count; i++)
            {
                Enemy spawned = SpawnEnemy(e.enemy, hpMul, anchor + side * ((i - (e.count - 1) * 0.5f) * 1.5f));
                if (e.type == WaveEventType.Boss && i == 0) LastBoss = spawned;
            }
        }

        EventStarted?.Invoke(e);
        if (e.type == WaveEventType.Boss && bossSpawnRequested != null)
            bossSpawnRequested.Raise();   // 17장 BossIntroCutscene 재생 (LastBoss를 이미 설정한 뒤)
    }

    private Enemy SpawnEnemy(EnemyData data, float hpMultiplier, Vector2 position)
    {
        Enemy enemy = GetPool(data).Spawn(position);                // 12장 PoolUtil.Spawn: 위치 설정 → SetActive(true)
        enemy.Init(data, player, gameplayPools, hpMultiplier);      // 4단계: 배율 포함 한 번에 초기화
        AliveCount++;
        return enemy;
    }

    private ObjectPool<Enemy> GetPool(EnemyData data)
    {
        if (pools.TryGetValue(data, out ObjectPool<Enemy> existing)) return existing;

        ObjectPool<Enemy> pool = null;
        pool = new ObjectPool<Enemy>(
            createFunc: () =>
            {
                GameObject go = Instantiate(data.prefab, transform);
                go.SetActive(false);                           // 활성화는 위치를 옮긴 뒤 (12장 흔한 실수 4)
                Enemy enemy = go.GetComponent<Enemy>();
                // 인스턴스를 만들 때 딱 한 번 구독 → 재사용해도 중복 구독이 생기지 않는다
                // 반환 요청은 사망·드롭·연출이 끝난 뒤에만 오므로 "처치 1회"로 센다
                enemy.ReleaseRequested += e => { AliveCount--; pool.Release(e); EnemyKilled?.Invoke(); };
                return enemy;
            },
            actionOnGet: null,                                 // 활성화는 PoolUtil.Spawn(12장)에서
            actionOnRelease: enemy => enemy.gameObject.SetActive(false),
            actionOnDestroy: enemy => { if (enemy != null) Destroy(enemy.gameObject); },
            collectionCheck: false, defaultCapacity: prewarmPerEnemy, maxSize: poolMaxSizePerEnemy);
        pools.Add(data, pool);
        return pool;
    }

    /// <summary>화면 사각형을 spawnMargin만큼 키운 테두리 위에서, 플레이어와 충분히 먼 점을 고른다.</summary>
    private Vector2 PickSpawnPoint(bool mustBeInsideMap)
    {
        Vector2 center = cam.transform.position;
        float halfH = cam.orthographicSize + spawnMargin;
        float halfW = cam.orthographicSize * cam.aspect + spawnMargin;
        Vector2 point = center + Vector2.up * halfH;

        for (int attempt = 0; attempt < 12; attempt++)
        {
            // 둘레 길이에 비례해 변을 고르므로 가로로 긴 화면에서도 고르게 분포
            float d = UnityEngine.Random.value * 4f * (halfW + halfH);
            if (d < 2f * halfW) point = new Vector2(center.x - halfW + d, center.y + halfH);                     // 위
            else if ((d -= 2f * halfW) < 2f * halfW) point = new Vector2(center.x - halfW + d, center.y - halfH); // 아래
            else if ((d -= 2f * halfW) < 2f * halfH) point = new Vector2(center.x - halfW, center.y - halfH + d); // 왼쪽
            else point = new Vector2(center.x + halfW, center.y - halfH + (d - 2f * halfH));                     // 오른쪽

            bool farEnough = ((Vector2)player.position - point).sqrMagnitude >= minPlayerDistance * minPlayerDistance;
            bool inMap = !mustBeInsideMap || mapBounds == null || mapBounds.OverlapPoint(point);
            if (farEnough && inMap) return point;
        }
        // 맵이 화면보다 작아 조건을 못 맞춘 경우: 맵 안으로 당긴다 (보이는 곳일 수 있으므로 경고로 보완)
        return mustBeInsideMap && mapBounds != null ? mapBounds.ClosestPoint(point) : point;
    }

    private float HalfDiagonal()
    {
        float halfH = cam.orthographicSize;
        float halfW = halfH * cam.aspect;
        return Mathf.Sqrt(halfW * halfW + halfH * halfH);
    }

    // ---------- 디버그용 ----------

    /// <summary>시간을 건너뛴다. 건너뛴 구간의 경고·이벤트는 발동하지 않는다.</summary>
    public void SkipTime(float seconds)
    {
        Elapsed = Mathf.Min(Elapsed + seconds, waveData.runDuration - 0.01f);
        while (nextWarningIndex < byWarningTime.Count && WarningTime(byWarningTime[nextWarningIndex]) <= Elapsed)
            nextWarningIndex++;
        while (nextEventIndex < byStartTime.Count && byStartTime[nextEventIndex].time <= Elapsed)
            nextEventIndex++;
    }

    /// <summary>다음 경고 직전으로 이동 (엘리트·보스·제단 바로 테스트)</summary>
    public void SkipToNextEvent(float secondsBeforeWarning = 1f)
    {
        if (nextWarningIndex >= byWarningTime.Count) return;
        float target = WarningTime(byWarningTime[nextWarningIndex]) - secondsBeforeWarning;
        if (target > Elapsed) SkipTime(target - Elapsed);
    }
}
```

- **스폰 예산 방식**은 초당 0.7마리 같은 소수점 비율을 프레임레이트와 무관하게 지킵니다. `timer = 0f` 리셋은 넘친 시간이 버려져 실제 스폰율이 낮아집니다.
- **이벤트는 최대 동시 수를 무시합니다.** 보스가 상한 때문에 안 나오면 안 되니까요.
- **경고와 등장은 서로 다른 순서의 목록**을 씁니다. 한 목록을 쓰면 경고가 짧은 이벤트 뒤에 경고가 긴 이벤트가 있을 때 긴 경고가 늦게(등장 3초 전에야) 뜹니다.
- `ReleaseRequested` 구독은 `createFunc`에서 인스턴스당 한 번입니다. `actionOnGet`에서 구독하면 재사용마다 핸들러가 중복됩니다. `Health.Died`를 스포너가 직접 구독하지 않는 이유는 4단계를 보세요.
- 이 스포너는 `WaveData`를 Inspector에서 직접 참조합니다. 19장처럼 적 에셋을 Addressables로 분리했다면 `WaveData`도 같은 그룹에 넣어 스테이지와 함께 로드하는 편이 일관됩니다(그대로 두면 적 에셋이 씬 의존성으로 빌드에 중복 포함될 수 있으니 19장 Analyze 규칙으로 확인).

에디터 작업:

1. `EnemySpawner` 오브젝트의 컴포넌트는 스크립트 교체 후에도 그대로 남습니다. 필드 이름이 바뀐 칸을 다시 연결합니다: **Wave Data** = `Wave_Stage1`, **Player**, **Gameplay Pools** = `Pools`(19장의 `Pools` 칸 값), **Map Bounds** = 17장 `CameraBounds`, **Boss Spawn Requested** = 17장 `BossSpawnRequested` 에셋.
2. 19장 `StageLoader`의 **Spawner** 칸이 여전히 이 오브젝트인지 확인합니다.
3. 04장 `GameStateMachine`(또는 19장 이후의 시작 흐름)에서 `RunTimeCompleted`를 구독해 Result 상태로 전환합니다.

### 5-1단계: 17장 보스 컷신을 웨이브 보스에 연결

17장은 씬에 미리 놓은 `Boss_Golem`을 5분에 `BossTimer`로 등장시켰습니다. 이제 보스는 9:00 웨이브 이벤트가 **풀에서 새로 생성**하고, 스포너가 `LastBoss`를 설정한 뒤 같은 `BossSpawnRequested` 채널을 Raise합니다. 컷신은 씬 보스가 아니라 **방금 생성된 보스**를 비춰야 합니다.

1. 씬의 `BossTimer` 오브젝트를 삭제하고, `GameStateMachine`의 **Gameplay Behaviours** 배열에서 빈 칸(Missing)을 지웁니다. `BossTimer.cs`도 삭제합니다.
2. 씬에 놓았던 `Boss_Golem`을 삭제합니다. 보스 프리팹은 `Enemy_KingGolem`(`EnemyData.prefab`)이 쓰는 것으로, Animator Update Mode를 **Unscaled Time**으로 둡니다(17장과 같은 이유).
3. `BossIntro.playable`을 열어 `Boss_Golem`에 바인딩된 **Animation Track을 삭제**합니다. 풀 보스는 매번 다른 오브젝트라 트랙 바인딩이 유지되지 않습니다. 대신 스포너가 화면 밖 맵 안에 보스를 세우고, 컷신이 카메라를 그 위치로 보냈다가 돌아온 뒤 보스가 걸어 들어옵니다.
4. `CM_Boss`의 Tracking Target은 비워 둡니다(아래 코드가 설정).

17장 `BossIntroCutscene.cs`에서 필드 한 줄과 `Play` 메서드를 교체합니다. 파일 상단에 `using Unity.Cinemachine;`을 추가합니다.

```csharp
// BossIntroCutscene.cs (17장) — 필드 교체: [SerializeField] GameObject boss;  →
[SerializeField] EnemySpawner spawner;          // 22장: 방금 생성한 보스를 알려줌
[SerializeField] CinemachineCamera bossCamera;  // CM_Boss

// Play 교체
public void Play()
{
    if (playing) return;
    Enemy boss = spawner.LastBoss;
    if (boss == null) return;                           // 보스 없이 신호만 온 경우 (디버그 메뉴 등)
    playing = true;
    bossCamera.Target.TrackingTarget = boss.transform;  // 17장 CameraTargetBinder와 같은 API
    bossCamera.PreviousStateIsValid = false;            // 이전 보스 위치에서 끌려오지 않게
    foreach (var b in enableAfterIntro) b.enabled = false;
    GameFeel.RequestPause(this);                        // 17장: 이 컷신 몫의 정지 요청
    director.Play();
}
```

`BossIntro` Inspector에서 **Spawner** = `EnemySpawner`, **Boss Camera** = `CM_Boss`를 연결합니다. 컷신 동안 게임 시간이 멈추므로 보스는 생성 위치에 서 있고, `Finish`가 정지 요청을 해제하면 18장 `EnemyManager`의 `Tick`으로 추적을 시작합니다.

### 6단계: 경고 표시 (공정한 죽음)

파일: `Assets/_CoinRush/Scripts/UI/WaveWarningView.cs`

```csharp
using TMPro;
using UnityEngine;

public class WaveWarningView : MonoBehaviour
{
    [SerializeField] private EnemySpawner spawner;
    [SerializeField] private TextMeshProUGUI label;
    [SerializeField] private float blinkSpeed = 6f;
    private float hideAt;

    private void OnEnable()
    {
        spawner.EventWarning += Show;
        label.gameObject.SetActive(false);
    }

    private void OnDisable() => spawner.EventWarning -= Show;

    private void Show(WaveEvent e)
    {
        label.text = e.warningText;
        label.gameObject.SetActive(true);
        hideAt = spawner.Elapsed + e.warningSeconds + 1f;   // 등장 후 1초까지 유지
    }

    private void Update()
    {
        if (!label.gameObject.activeSelf) return;
        Color c = label.color;   // 알파 0.3~1 왕복 깜빡임
        c.a = Mathf.Lerp(0.3f, 1f, (Mathf.Sin(Time.unscaledTime * blinkSpeed) + 1f) * 0.5f);
        label.color = c;
        if (spawner.Elapsed >= hideAt) label.gameObject.SetActive(false);
    }
}
```

HUD Canvas(11장) 아래에 **UI → Text - TextMeshPro**(`WaveWarning`, 상단 중앙, 크기 48, 빨강)를 만들고, HUD 오브젝트에 `WaveWarningView`를 붙여 연결합니다. 보스 경고에 16장의 화면 흔들림이나 경고음을 `EventWarning` 구독으로 더해도 좋습니다.

### 7단계: 위협 곡선 계산 도구

스프레드시트 수식과 에셋 값이 어긋나는 일을 막기 위해, **에셋에서 직접** 위협 곡선을 계산해 CSV로 뽑는 에디터 메뉴를 만듭니다. 파일: `Assets/_CoinRush/Scripts/Editor/ThreatCurveReport.cs` (`Editor` 폴더 안이라 빌드에 포함되지 않습니다)

```csharp
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

public static class ThreatCurveReport
{
    private const float HitEfficiency = 0.8f;   // 개념 절의 명중 효율 가정
    private const float StepSeconds = 30f;

    [MenuItem("Coin Rush/Balance/Threat Curve Report")]
    private static void Run()
    {
        var wave = (WaveData)Selection.activeObject;
        CultureInfo inv = CultureInfo.InvariantCulture;
        var csv = new StringBuilder("time_s,segment,spawns_per_s,avg_hp,threat_hp_per_s,event_hp,required_dps,coins_per_min\n");

        for (float t = 0f; t < wave.runDuration; t += StepSeconds)
        {
            WaveSegment seg = wave.GetSegment(t);
            if (seg == null) continue;

            float totalWeight = seg.TotalWeight(), avgHp = 0f, avgCoin = 0f;
            foreach (SpawnEntry entry in seg.entries)
            {
                if (entry.enemy == null || totalWeight <= 0f) continue;
                avgHp += entry.enemy.maxHp * entry.weight / totalWeight;
                avgCoin += entry.enemy.coinDrop * entry.weight / totalWeight;
            }
            avgHp *= seg.hpMultiplier;
            float threat = seg.spawnsPerSecond * avgHp;

            float eventHp = 0f;   // 이 30초 창에 시작하는 이벤트의 총 체력
            foreach (WaveEvent e in wave.events)
                if (e.enemy != null && e.time >= t && e.time < t + StepSeconds)
                    eventHp += e.enemy.maxHp * e.count * seg.hpMultiplier * e.hpMultiplier;

            csv.AppendLine(string.Join(",", t.ToString("0", inv), seg.label.Replace(",", " "),
                seg.spawnsPerSecond.ToString("0.00", inv), avgHp.ToString("0.0", inv),
                threat.ToString("0.0", inv), eventHp.ToString("0", inv),
                (threat / HitEfficiency).ToString("0.0", inv),
                (seg.spawnsPerSecond * avgCoin * 60f).ToString("0", inv)));
        }

        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Balance"));
        Directory.CreateDirectory(dir);
        string path = Path.Combine(dir, $"{wave.name}_threat.csv");
        File.WriteAllText(path, csv.ToString(), new UTF8Encoding(true));   // BOM: 엑셀 한글 깨짐 방지
        Debug.Log($"위협 곡선 저장: {path}\n{csv}");
    }

    // 같은 메뉴 경로 + true: WaveData를 선택했을 때만 메뉴 활성화
    [MenuItem("Coin Rush/Balance/Threat Curve Report", true)]
    private static bool Validate() => Selection.activeObject is WaveData;
}
```

`Wave_Stage1`을 선택하고 메뉴 **Coin Rush → Balance → Threat Curve Report**를 실행한 뒤, 프로젝트 루트 `Balance/Wave_Stage1_threat.csv`를 스프레드시트로 열어 `threat_hp_per_s`와 예상 DPS를 꺾은선으로 겹쳐 그립니다. `Balance/`는 Assets 밖이라 임포트되지 않고, Git에 커밋하면 조정 전후를 비교할 수 있습니다.

### 8단계: 디버그용 시간 빨리감기 치트

10분을 매번 플레이하면 설계를 검증할 수 없습니다. 파일: `Assets/_CoinRush/Scripts/Debug/DebugTimeCheats.cs`

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>에디터·Development Build 전용. F1: +60초  F2: 배속 순환(1→2→4→8)  F3: 다음 이벤트 직전으로</summary>
public class DebugTimeCheats : MonoBehaviour
{
    [SerializeField] private EnemySpawner spawner;
    [SerializeField] private float[] timeScales = { 1f, 2f, 4f, 8f };
    private int scaleIndex;

    private void Awake()
    {
        // 릴리스 빌드에서는 스스로 제거 (클래스는 남겨 Missing Script 경고를 피함)
        if (!Debug.isDebugBuild) Destroy(this);
    }

    private void Update()
    {
        Keyboard kb = Keyboard.current;
        if (kb == null) return;
        if (kb.f1Key.wasPressedThisFrame) spawner.SkipTime(60f);
        if (kb.f3Key.wasPressedThisFrame) spawner.SkipToNextEvent(1f);
        if (kb.f2Key.wasPressedThisFrame)
        {
            scaleIndex = (scaleIndex + 1) % timeScales.Length;
            Time.timeScale = timeScales[scaleIndex];
        }
    }

    private void OnGUI()
    {
        int m = (int)(spawner.Elapsed / 60f), s = (int)(spawner.Elapsed % 60f);
        GUI.Label(new Rect(10, 10, 600, 30), $"{m}:{s:00}  x{Time.timeScale:0}  alive {spawner.AliveCount}  (F1 +60s / F2 speed / F3 next event)");
    }
}
```

빈 오브젝트 `_DebugCheats`에 붙이고 `Spawner`를 연결합니다. 배속 8에서는 물리 스텝이 프레임당 여러 번 돌아 부하가 커지므로 성능 측정 중에는 쓰지 마세요.

### 확인하기

1. Play → 스테이지 로드 후 좌상단에 `0:00 x1 alive 0`이 보이고 슬라임만 화면 밖에서 들어오면 성공입니다. 첫 생성된 적에게 데미지 숫자·번쩍임이 뜨지 않아야 합니다(4단계).
2. **맵 모서리 확인**: 플레이어를 맵 네 모서리로 차례로 옮겨 각각 30초씩 서 있습니다. 카메라가 경계에 막힌 상태에서도 적이 **화면 안에서 갑자기 생기지 않고** 항상 화면 테두리 밖에서 걸어 들어와야 합니다. 의심되면 Scene 뷰를 함께 띄워 스폰 순간을 봅니다.
3. **F3** → 1:56 부근으로 이동, "코인 제단이 열린다"가 깜빡입니다(제단 자체는 23장에서 생김). **F3** 한 번 더 → 2:56 부근, "무언가 다가온다…" 뒤 3:00에 엘리트 기사가 한 방향에서 나타납니다.
4. **F3**를 두 번 더 → 4:27 부근, 2초 뒤 박쥐 24마리가 화면 밖 원형으로 포위합니다.
5. **F3**를 반복해 8:54 부근 → 5초 경고 뒤 9:00에 게임이 멈추고 카메라가 **방금 생성된 보스**로 갔다가 돌아온 뒤 재개됩니다. 17장 `BossTimer`에 의한 5분 컷신은 더 이상 나오지 않아야 합니다.
6. **F2**로 x8 → `alive` 수가 각 구간의 최대 동시 수를 넘지 않는지 보고(이벤트 적은 예외), 10:00에 결과 화면이 뜨는지 확인합니다.
7. `Balance/Wave_Stage1_threat.csv`의 `threat_hp_per_s` 값이 2단계 표의 위협 열과 일치합니다(8.0, 10.6, 15.4, 16.4, 27.7, 36.8, 40.6, 58.8, 68.9, 63.0 — 30초 간격이므로 같은 값이 두 번씩).

## 흔한 실수

1. **증상**: 치트로 시간을 건너뛰면 적이 너무 약하거나 강하다. → **원인**: 시간은 건너뛰었지만 플레이어 레벨은 0:00 그대로. → **해결**: 건너뛴 시간만큼 경험치를 지급하는 치트를 따로 두거나, 빨리감기(F2)로 실제 성장을 거치며 확인합니다. 난이도 판단은 반드시 성장을 거친 상태에서 합니다.
2. **증상**: 적이 줄어들자마자 한꺼번에 우르르 스폰된다. → **원인**: 최대 동시 수에 막힌 동안 스폰 예산이 계속 쌓임. → **해결**: 상한에 막히면 예산을 0으로 버립니다(5단계 코드).
3. **증상**: 레벨업 창을 닫았더니 배속 치트가 풀렸다, 혹은 레벨업 창에서도 시간이 흐른다. → **원인**: 04장 상태 머신과 치트가 둘 다 `Time.timeScale`을 씀. → **해결**: 상태 머신이 복귀할 때 "1"이 아니라 "일시정지 전 값"으로 되돌리게 하거나, 테스트할 때는 치트 배속을 쓰지 않습니다.
4. **증상**: 적이 죽어도 `AliveCount`가 줄지 않아 스폰이 멈춘다. → **원인**: `Enemy`가 여전히 `Destroy(gameObject)`를 호출해 풀 반환 경로를 거치지 않음, 또는 `Died`가 여러 번 발생. → **해결**: 4단계대로 `Destroy`를 지우고, `Health.TakeDamage`가 이미 죽은 상태(`Current <= 0`)에서는 `Died`를 다시 발생시키지 않는지 확인합니다.
5. **증상**: 적이나 보스가 화면 안, 플레이어 근처에서 생긴다. → **원인**: 플레이어 위치를 중심으로 반지름을 잡았는데 카메라가 맵 경계에 막혀 플레이어가 화면 중심이 아님, 또는 고정 반지름이 카메라 줌·화면 비율과 맞지 않음. → **해결**: 5단계 `PickSpawnPoint`처럼 매번 **실제 카메라 사각형** 바깥에서 뽑고 플레이어 최소 거리를 검사합니다. Cinemachine이 렌즈를 제어한다면 실제 카메라의 `orthographicSize`가 갱신되는지 확인하세요.
6. **증상**: 보스 컷신에서 카메라가 엉뚱한 곳(맵 밖 옛 위치)을 비추거나 컷신이 두 번 나온다. → **원인**: 17장 씬 보스·Animation Track·`BossTimer`가 남아 있음. → **해결**: 5-1단계대로 셋을 지우고, 컷신이 `spawner.LastBoss`를 대상으로 삼는지 확인합니다.

## 연습 문제

**1. ★☆☆ 위협 계산**
7:00~8:00 구간의 구성을 "해골 40, 박쥐 20, 골렘 40"으로 바꾸고 스폰율을 1.0으로 낮췄습니다. 체력 배율 1.2일 때 위협(HP/초)과 예상 DPS 72 대비 위협 비율을 계산하세요.

<details><summary>힌트·해설</summary>

평균 체력 = (30×40 + 6×20 + 120×40) ÷ 100 = (1200 + 120 + 4800) ÷ 100 = 61.2. 체력 배율 적용 61.2 × 1.2 = 73.44. 위협 = 1.0 × 73.44 = 73.4 HP/초. 비율 = 73.4 ÷ 72 ≈ 1.02 → 긴장 구간을 넘어 적이 계속 쌓입니다. 스폰율을 낮췄는데도 위협이 원래(58.8)보다 커진 이유는 골렘 비중이 커져 평균 체력이 크게 올랐기 때문입니다.

코인도 같은 방식으로 확인합니다. 평균 코인 = 0.4×2 + 0.2×1 + 0.4×6 = 3.4개/마리, 공급 = 1.0 × 3.4 = **3.4개/초**. 원래는 1.2 × (0.5×2 + 0.3×1 + 0.2×6) = 1.2 × 2.5 = **3.0개/초**였으므로 스폰 수가 줄었는데도 **공급되는 코인은 오히려 늘어납니다**(코인 많은 골렘 비중 증가). 다만 실제로 줍는 양은 처치 능력에 달렸고, 위협 비율이 1을 넘으면 처치하지 못한 골렘의 코인은 들어오지 않으므로 실제 수집량과 파워 성장은 줄 수 있습니다. 공급 증가는 8:00 제단 시점 지갑(개념 절의 표)도 바꾸므로 함께 다시 계산합니다. "구성 변경은 스폰율보다 영향이 크고, 위협과 코인을 따로 계산해야 한다"는 감각을 기르세요.

</details>

**2. ★★☆ 이완 구간 설계**
9:00 보스를 쓰러뜨린 뒤 10:00까지 남은 시간이 너무 지루하다는 피드백이 왔습니다. `WaveData`만 수정해서 해결하는 방법을 두 가지 제안하세요.

<details><summary>힌트·해설</summary>

(1) 9:00~10:00 구간을 둘로 나눠 9:30~10:00에 "보너스 러시" 구간을 만듭니다. 체력 배율을 0.8로 낮추고 슬라임·박쥐 위주로 스폰율을 크게 올려 파워 판타지와 코인 폭발을 주는 방식입니다. (2) 보스를 9:30으로 늦춰 보스 처치와 클리어 시각을 가깝게 붙입니다. 어느 쪽이든 결과 화면 직전의 감정이 "지루함"이 아니라 "해냈다"가 되게 하는 것이 목표입니다. 코드 수정 없이 데이터로 해결할 수 있다는 것이 이 장 구조의 장점입니다.

</details>

**3. ★★★ 두 번째 스테이지 설계**
"밤의 묘지" 스테이지를 설계하세요. 조건: 8분, 새 적 1종(원거리 공격을 하는 해골 궁수) 추가, 4단계 소개 방식을 따를 것, 위협 비율이 1.0을 넘는 구간은 전체 시간의 10% 이하. 웨이브 표, 이벤트 표, `WaveData` 에셋, 위협 곡선 CSV 그래프까지 만드세요.

<details><summary>힌트·해설</summary>

진행 순서: (1) 새 적의 "도입-연습-변형-조합" 시각을 먼저 표에 박아둡니다. 원거리 적은 도입 때 반드시 화면 안에서 공격 예고(조준선)가 보여야 공정합니다. (2) 8분이므로 톱니의 정점은 2~3개면 충분합니다. (3) 예상 DPS 열은 1스테이지 표의 값을 시간 비율로 가져오되, 영구 강화가 쌓인 플레이어가 온다고 가정한다면 1.2~1.5배로 올립니다. (4) 위협 비율 1.0 초과 시간 = 정점 이벤트 직후 적체가 해소되는 시간이므로, 이벤트 체력 ÷ (예상 DPS − 배경 위협)으로 대략 추정합니다. 예: 엘리트 440 HP, DPS 30, 배경 16.4 → 440 ÷ 13.6 ≈ 32초. 이런 정점 세 번이면 약 100초 = 8분의 21%로 조건을 넘으므로 이벤트 체력을 줄이거나 직후 스폰율을 낮춥니다.

</details>

## 셀프 체크

**1. 몰입 채널이 "대각선"이고 "폭이 있다"는 것은 난이도 설계에서 각각 무엇을 뜻하나요?**

<details><summary>모범 답안</summary>

대각선이라는 것은 플레이어가 강해지는 만큼 난이도도 올라가야 몰입이 유지된다는 뜻입니다. 서바이버라이크에서는 레벨업으로 파워가 계속 오르므로 시간 기반으로 위협을 올립니다. 폭이 있다는 것은 채널 안에서 난이도가 오르내려도 된다는 뜻이며, 오히려 긴장(채널 위쪽)과 이완(아래쪽)을 오가는 톱니형 리듬이 한가운데만 유지하는 곡선보다 덜 단조롭습니다.

</details>

**2. 스폰율을 올리는 것과 체력 배율을 올리는 것은 위협을 똑같이 늘려도 결과가 다릅니다. 왜인가요?**

<details><summary>모범 답안</summary>

둘 다 초당 들어오는 적 HP를 늘리지만, 스폰율은 적 수를 늘리므로 드롭되는 코인(= 경험치)도 함께 늘어 플레이어 파워 성장도 빨라집니다. 체력 배율은 코인을 늘리지 않고 처치 시간만 늘리므로 파워 성장은 그대로이고 상대적 난이도만 오릅니다. 그래서 후반에 플레이어가 너무 빨리 강해질 때는 체력 배율, 초반 성장이 너무 느릴 때는 스폰율을 조정 손잡이로 씁니다.

</details>

**3. 위협 비율(위협 ÷ 예상 유효 DPS)이 1.0을 넘으면 화면에서 어떤 일이 일어나고, 왜 짧게만 허용하나요?**

<details><summary>모범 답안</summary>

들어오는 HP가 처리하는 HP보다 많으므로 처치되지 못한 적이 화면에 계속 누적됩니다. 누적된 적 수가 곧 피격 위험이라 시간이 길어질수록 사망 확률이 급격히 오릅니다. 짧게 넘었다가 내려오면 "위기를 넘겼다"는 긴장-해소가 되지만, 길게 유지되면 회복할 방법이 없어 불공정하거나 지치는 경험이 됩니다. 그래서 엘리트·보스 같은 정점에만 쓰고 직후에는 스폰율을 낮춥니다.

</details>

**4. `EnemySpawner`가 타이머 리셋 대신 "스폰 예산"을 누적하는 이유와, 최대 동시 수에 막힌 예산을 버리는 이유를 설명해보세요.**

<details><summary>모범 답안</summary>

타이머를 `0`으로 리셋하면 간격을 넘친 시간(예: 1.0초 간격인데 1.016초에 체크)이 매번 버려져 실제 스폰율이 설정보다 낮아지고 프레임레이트에 따라 달라집니다. 예산에 `spawnsPerSecond × dt`를 누적하고 1씩 빼면 초당 0.7마리 같은 소수점 비율도 정확합니다. 상한에 막힌 동안 예산을 계속 쌓으면, 적이 줄어드는 순간 밀린 예산만큼 한 프레임에 대량 스폰되어 설계에 없는 스파이크가 생기므로 버립니다.

</details>

## 핵심 요약

- 좋은 난이도는 몰입 채널 안에서 우상향하는 톱니 모양이며, 정점(엘리트·보스) 직후에는 이완을 둡니다.
- 서바이버라이크의 난이도 손잡이는 스폰율, 최대 동시 수, 적 구성, 체력 배율, 이벤트 다섯 개입니다. 스폰율은 코인도 늘리고 체력 배율은 늘리지 않습니다.
- 위협(스폰율 × 평균 체력 × 배율)과 유효 DPS를 HP/초로 맞춰 비교하고, 위협 비율 0.6~0.9를 몰입, 1.0 초과를 짧은 정점으로 씁니다.
- 공정한 죽음은 예고(경고 문구·방향), 가독성, 사망 원인 표시, 그리고 **실제 카메라 사각형 밖**에서의 스폰으로 만듭니다.
- 코인 제단은 웨이브 이벤트로 관리하고, 제단 다음의 정점·직전의 긴장·그때까지의 코인 공급으로 "쓸까 모을까"의 무게를 설계합니다. 가격은 코인 공급 표에서 역산합니다.
- 숨겨진 DDA보다 플레이어가 보이는 선택(영구 강화, 부활)으로 난이도 편차를 흡수합니다.
- `WaveData`는 구간(배경 압력)과 이벤트(정점·제단)를 분리하고, `EnemySpawner`는 스폰 예산 방식으로 이를 정확히 재생합니다. 적은 배율을 포함해 한 번만 초기화해야 피격 연출이 오작동하지 않습니다.
- 위협 곡선 CSV와 시간 치트로 10분 설계를 몇 분 안에 검증하되, 파워 성장을 거치지 않은 시간 건너뛰기로 난이도를 판단하지 않습니다.

## 더 읽을거리

- Unity 매뉴얼 — ObjectPool: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity 매뉴얼 — ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Jenova Chen, "Flow in Games" (MFA 논문, 2006) — 몰입 채널을 게임 설계에 적용한 대표 자료
- Game Maker's Toolkit, 닌텐도의 레벨 디자인(기승전결 소개) 관련 영상
- Jesse Schell, 「The Art of Game Design」 — 난이도와 흥미 곡선(Interest Curve) 장
