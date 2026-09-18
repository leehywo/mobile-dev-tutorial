# 22. 난이도 곡선과 웨이브 디자인

> **이 장에서 배울 것**
> - 몰입(Flow) 채널과 긴장-이완 리듬으로 좋은 난이도 곡선의 조건을 설명할 수 있다
> - 플레이어 파워 곡선과 적 위협 곡선을 같은 단위(HP/초)로 놓고 교차 설계한다
> - 시간대별 스폰 규칙을 담는 `WaveData`(ScriptableObject)를 설계하고, `EnemySpawner`가 이를 읽게 구현한다
> - 공정한 죽음(예고·가독성)과 새 요소 소개 4단계를 웨이브 표에 반영한다
> - 위협 곡선 계산 도구와 시간 빨리감기 치트로 10분짜리 설계를 몇 분 안에 검증한다
> - 난이도는 올라가는데 플레이어의 대응은 그대로인 **단조 구간**을 지표로 진단한다
> - 적에게 역할을 부여하고 조합·스폰 규칙으로 전술 전환을 강제한 뒤, 같은 방법으로 재측정한다
>
> **선수 장**: 03, 05, 12, 17, 19 (20장을 했다면 웨이브 편집기와 함께 쓸 수 있음), 21 · **예상 시간**: 7~9시간 · **코인 러시 진행**: 분 단위로 설계된 10분 웨이브, 코인 제단 시각과 가격 근거, 엘리트·보스 예고, 보스 컷신 연결, 위협 곡선 CSV, 디버그 치트, 적 역할 표와 단조 진단 기록, 수정 전후 웨이브 표와 재측정 결과

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

그레이박스 가격은 첫 두 제단에서 상한으로도 살 수 없어 "모으기"만 남습니다. 네 제단을 모두 사면 판 전체 코인이 사라지므로 저축과의 경쟁도 성립하지 않습니다. 가격을 50×n으로 낮추면 모든 제단에서 결정이 가능하고, 다 사도 절반가량이 남습니다. 이 수치(`shrineBasePrice = 50`)는 23장에서 시뮬레이터로 다시 검증합니다. 이 표는 **적 구성에서 나온 값**이므로, 10단계에서 구성을 바꾸면 함께 다시 계산합니다(수정 후 값은 10-8에 있습니다). 반대로 스폰율을 올리면 코인 공급도 올라 지갑이 가격을 크게 넘어서므로, **스폰율을 바꿀 때는 이 표도 함께 다시 계산**합니다.

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

### 난이도가 올라도 대응이 그대로면: 단조 구간

여기까지의 손잡이는 전부 **얼마나 어려운가**를 조절합니다. 그런데 플레이어가 지루해하는 이유는 어려움이 모자라서가 아니라 **하는 일이 같아서**인 경우가 더 많습니다. 두 축은 다릅니다.

|  | 대응이 그대로 | 대응이 바뀜 |
|---|---|---|
| **위협이 그대로** | 정체 — "아무 일도 안 일어난다" | 변주 — 좋은 이완 구간 |
| **위협이 오름** | **단조 구간** — "숫자만 커진다" | 상승 — 우리가 원하는 것 |

왼쪽 아래 칸이 위험합니다. 표를 보면 난이도는 분명히 올라가고, 위협 비율도 계산대로 움직이고, 플레이어는 실제로 더 자주 죽습니다. 그런데도 "1분이나 7분이나 똑같다"는 말을 듣습니다. 21장 레퍼런스 해부표의 "피할 것 — 초반 3분의 단조로움"이 가리킨 것이 이 칸이고, 기둥 1("매 30초마다 고민되는 결정이 하나 이상 있다")이 무너지는 곳도 여기입니다.

먼저 **대응**이 무엇인지 이름을 붙여야 측정할 수 있습니다. 코인 러시는 조작이 이동뿐이므로 대응은 주로 이동 경로로 나타나고, 거기에 무기·강화 선택, 제단 결정, 위치 선점이 붙습니다. 이 장에서는 이동 경로 네 가지를 기본 목록으로 씁니다.

| 대응 | 플레이어가 하는 일 | 통하는 상황 |
|---|---|---|
| **선회**(Kite) | 한 방향으로 크게 원을 그리며 적 무리를 뒤로 끌고 다님 | 쫓아오는 적만 있을 때 |
| **도주**(Flee) | 가장 가까운 위협 반대쪽으로 직진, 벽에서만 꺾음 | 적이 느리고 수가 적을 때 |
| **관통**(Punch) | 무리 한가운데를 가로질러 코인·제단으로 감 | 화력이 충분하거나 목표가 안쪽에 있을 때 |
| **고정**(Hold) | 좁은 구역에 머무르며 들어오는 적만 처리 | 주변이 안전하고 회복·읽을 것이 있을 때 |

자기 게임에서는 이 목록이 다릅니다. 먼저 자기가 플레이하며 **실제로 하는 행동**에 이름을 붙이고, 그 목록으로 아래 두 지표를 재세요.

**지표 1 — 단조 지수.** 전술 하나만 고수해서 무피해로 통과되는 시간의 비중입니다.

```
단조 지수 = (어떤 단일 전술 하나로 무피해 통과되는 분 수) ÷ (전체 분 수)

기준 (이 교재의 작업 기준)
  - 단조 지수 ≤ 0.3
  - 그리고 같은 전술 하나로 연속 3분 이상 통과되는 구간이 없을 것
```

두 번째 조건이 실질입니다. 단조 지수가 0.3이어도 그 3분이 연속이면 플레이어는 "3분 동안 같은 것을 했다"고 느낍니다. 반대로 흩어진 3분은 이완 구간으로 읽힙니다.

**지표 2 — 지배 대응 비중.** 한 분 안에서 가장 많이 쓰인 대응이 차지하는 시간 비율입니다.

```
지배 대응 비중(분) = 그 분에서 최빈 대응이 차지한 시간 ÷ 60초
기준: 지배 대응 비중이 70% 이상인 분이 전체의 30%를 넘지 않을 것
```

지표 1은 손으로 재고(9단계 절차 A), 지표 2는 기록으로 잽니다(절차 B). 둘이 어긋나면 지표 1을 믿습니다. 지표 2는 "무엇을 했나"를, 지표 1은 "그것만으로 되나"를 재기 때문입니다.

**단조 자체가 악은 아닙니다.** 0~2분은 조작을 익히는 구간이라 일부러 단조하게 둡니다. 문제는 그 상태가 10분까지 이어지는 것입니다.

### 적의 역할: 대응을 바꾸는 부품

플레이어의 대응을 바꾸는 것은 적의 **수나 체력이 아니라 역할**입니다. 역할은 "이 적이 플레이어에게 어떤 질문을 던지는가"로 정의합니다.

| 역할 | 던지는 질문 | 강제하는 대응 변화 | 코인 러시의 예 | 남용하면 |
|---|---|---|---|---|
| **압박**(Pressure) | 어디로 움직일까 | 선회·도주 | 슬라임, 박쥐, 해골 | 수만 늘어 대응은 그대로 — 단조의 주범 |
| **차단**(Blocker) | 이 길로 갈 수 있나 | 경로 재계획, 우회 | 골렘 | 갇혀서 불공정하게 느껴짐 |
| **처치 우선**(Priority) | 무엇을 먼저 죽일까 / 죽이면 안 되나 | 무리 관리, 거리 조절, 표적 선택 | 엘리트, 보스, 폭탄충(10단계) | 화면이 시끄러워 읽히지 않음 |
| **환경 변화**(Zoner) | 여기 서 있어도 되나 | 위치 선점, 경로 재설계 | 주술사의 둔화 장판(10단계) | 서 있을 곳이 없어 조작이 답답해짐 |

여기서 이 절의 핵심이 나옵니다. **위협 비율을 그대로 두고도 대응은 바꿀 수 있습니다.** 예를 들어 평균 체력이 같은 두 구성을 생각해 보세요.

```
A: 슬라임 50, 박쥐 30, 해골 20   → 평균 체력 (10×50 + 6×30 + 30×20) ÷ 100 = 12.8
B: 슬라임 35, 박쥐 30, 해골 5, 폭탄충(체력 20) 30
                                 → 평균 체력 (10×35 + 6×30 + 30×5 + 20×30) ÷ 100 = 12.8

같은 스폰율이면 위협(HP/초)도 같다. 그러나 A는 선회로 전부 통하고,
B는 "가까이에서 죽이면 터지는 적"이 섞여 선회 꼬리를 직접 위험하게 만든다.
```

난이도 곡선을 다시 그리지 않고도 대응을 바꿀 수 있다는 뜻입니다. 반대로 말하면, **위협 곡선이 예쁘다는 것은 재미의 증거가 아닙니다.**

조합 규칙은 네 개로 충분합니다.

| 규칙 | 내용 | 이유 |
|---|---|---|
| **R1** | 한 구간에서 **한 역할의 가중치 합이 70%를 넘지 않는다** | 한 역할이 지배하면 대응도 하나로 수렴 |
| **R2** | 2:00 이후 모든 구간에 **압박 이외의 역할이 1개 이상** 있다 | 압박만으로는 선회가 항상 정답 |
| **R3** | 새 역할은 **소개 4단계**(도입·연습·변형·조합)를 지키고, 도입은 이완 구간에서 **단독으로** | 역할은 규칙이라 배워야 쓸 수 있음 |
| **R4** | 한 화면에 동시에 살아 있는 "읽어야 하는 예고"는 **2종까지** | 아래 가독성 절 참고 |

R1·R2는 3단계 `WaveData.OnValidate`에서 자동으로 검사하게 만듭니다(10단계).

### 전술 전환과 가독성은 서로를 잡아먹는다

전술을 바꾸라고 요구할수록 플레이어가 **읽어야 할 것**이 늘어납니다. 앞의 "공정한 죽음" 절이 여기서 다시 걸립니다. 폭발 반경을 모르면 폭탄충은 전술 전환이 아니라 그냥 불공정한 즉사이고, 둔화 장판이 바닥에서 안 보이면 주술사는 "갑자기 느려지는 버그"입니다.

그래서 새 역할에는 세 가지 표시 원칙을 붙입니다.

| 원칙 | 뜻 | 코인 러시 적용 |
|---|---|---|
| **상시 표시** | 항상 켜져 있는 것은 항상 보여야 한다 | 둔화 장판은 바닥에 반투명 원으로 상시 표시(적이 살아 있는 동안 계속) |
| **사전 예고** | 순간에 일어나는 것은 미리 보여야 한다 | 폭발은 죽은 자리에 0.8초 동안 차오르는 예고 원 |
| **한 번에 두 가지** | 동시에 읽을 것은 두 종류까지 (R4) | 9:00 보스 구간에는 폭탄충을 넣지 않는다 — 보스 패턴 + 장판이 이미 두 종류 |

세 번째가 설계 결정입니다. 10단계의 수정판에서 9:00~10:00 구성에 주술사는 남기고 폭탄충은 뺀 이유가 이것입니다. 역할을 더 넣을수록 좋은 것이 아니라, **한 순간에 읽을 수 있는 만큼만** 넣는 것이 좋습니다.

앞 절의 "공정한 죽음" 표에 두 줄을 더합니다.

| 불공정하게 느끼는 죽음 | 공정하게 만드는 장치 |
|---|---|
| 적을 죽였는데 그 자리에서 터져 죽음 | 폭발 반경과 같은 크기의 예고 원 + 도망칠 수 있는 예고 시간(이동속도 × 예고 시간 ≥ 반경) |
| 왜 느려졌는지 모른 채 잡힘 | 장판을 바닥에 상시 표시하고, 장판 밖으로 나가면 즉시 원래 속도로 복귀 |

두 번째 행의 괄호가 검산식입니다. 폭발 반경 2.5, 플레이어 최고 속도 6이라면 예고 시간은 최소 `2.5 ÷ 6 ≈ 0.42초`여야 반경 한가운데에서도 빠져나갈 수 있습니다. 감속·방향 전환을 감안해 **0.8초**로 잡습니다. 예고 시간을 반경보다 먼저 정하면 이 검산을 빠뜨리게 되니, 반경 → 검산 → 예고 시간 순서로 정합니다.

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

> **이 표는 v1(단조 구간 수정 전)입니다.** 이 장 9~11단계에서 이 표를 진단해 고치고, [10-7](#10-7-수정-전후-웨이브-표)의 **수정 후 표(v2)** 가 이후 장이 이어받는 상태가 됩니다. [23장](./23_balancing-economy.md) 시뮬레이션과 [24장](./24_playtest-analytics.md) 지표도 v2 기준입니다. 여기서는 먼저 v1을 만들어 보고, 9단계에서 무엇이 문제였는지 직접 진단합니다.

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

### 9단계: 지금 웨이브가 단조인지 진단하기

2단계 표는 위협 비율이 0.55~0.82 사이를 오가는 예쁜 톱니입니다. 그렇다고 대응이 바뀐다는 보장은 없습니다. 여기서는 **혼자서, 하루 안에** 단조 구간을 찾아내는 세 가지 절차를 돌립니다. 모두 8단계 치트와 스프레드시트만 있으면 됩니다.

> 진단은 **파워 성장을 실제로 거친 상태**에서만 유효합니다. F1(+60초)은 레벨을 건너뛰므로 쓰지 않고, F2 배속만 씁니다(흔한 실수 1).

#### 절차 A — 단일 전술 완주 테스트 (약 60분)

"특정 대응 하나로 얼마나 통과되는가"를 직접 재는 방법입니다.

1. 개념 절의 대응 네 가지(선회·도주·관통·고정) 중 하나를 고르고, **그 전술만 고수**하며 10분 판을 끝까지 갑니다. 어겼으면 그 판은 무효입니다.
2. 분 단위로 **무피해 통과 여부**만 적습니다. 그 분 동안 피격이 한 번이라도 있으면 ✗입니다.
3. 전술마다 3판, 총 12판. 같은 분에서 3판 중 2판 이상 통과면 ✓로 확정합니다.
4. F2로 x2 배속을 켜면 12판이 약 60분입니다. 레벨업 선택은 판마다 같은 순서로 골라 변수를 줄입니다.

아래는 2단계 표(수정 전)를 이 절차로 잰 **가상 결과**입니다. 필자가 표를 설계하며 직접 돌린 기록의 형식이며, 여러분의 값은 조작 숙련도에 따라 달라집니다.

| 분 | 선회 | 도주 | 관통 | 고정 | 통과 전술 수 |
|---|---|---|---|---|---:|
| 0:00~1:00 | ✓ | ✓ | ✓ | ✓ | 4 |
| 1:00~2:00 | ✓ | ✓ | ✓ | ✓ | 4 |
| 2:00~3:00 | ✓ | ✓ | ✗ | ✓ | 3 |
| 3:00~4:00 | ✓ | ✓ | ✗ | ✗ | 2 |
| 4:00~5:00 | ✓ | ✓ | ✗ | ✗ | 2 |
| 5:00~6:00 | ✓ | ✗ | ✗ | ✗ | 1 |
| 6:00~7:00 | ✓ | ✗ | ✗ | ✗ | 1 |
| 7:00~8:00 | ✓ | ✗ | ✗ | ✗ | 1 |
| 8:00~9:00 | ✓ | ✗ | ✗ | ✗ | 1 |
| 9:00~10:00 | ✓ | ✗ | ✗ | ✗ | 1 |
| **전술별 통과 분 수** | **10** | 5 | 2 | 4 | |

```
단조 지수 = 가장 많이 통과한 전술의 분 수 ÷ 전체 분 수 = 10 ÷ 10 = 1.00   (기준 0.3 이하 → 미달)
최장 연속 통과 구간 = 선회, 0:00~10:00 = 10분                              (기준 3분 미만 → 미달)
```

**선회 하나로 10분 전체가 무피해 통과됩니다.** 보스전조차 선회로 넘어갑니다. 위협 비율 표가 아무리 잘 그려져도, 플레이어가 하는 일은 0분이나 9분이나 "원 그리며 돌기"입니다.

#### 절차 B — 대응 분포 기록 (TacticSampler)

절차 A는 "그것만으로 되나"를 재고, 절차 B는 "실제로 무엇을 했나"를 잽니다. 5초 창마다 대응을 하나로 분류해 CSV로 남깁니다. 파일: `Assets/_CoinRush/Scripts/Debug/TacticSampler.cs`

```csharp
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;

/// <summary>에디터·Development Build 전용. windowSeconds마다 플레이어의 "대응"을 하나로 분류해 CSV로 남긴다.</summary>
public class TacticSampler : MonoBehaviour
{
    [SerializeField] private EnemySpawner spawner;
    [SerializeField] private Transform player;
    [SerializeField] private LayerMask enemyLayer;
    [SerializeField, Min(1f)] private float windowSeconds = 5f;

    [Header("분류 기준 — 자기 게임에서는 관찰로 먼저 정한다")]
    [SerializeField] private float nearRadius = 3f;           // "붙어 있다"고 볼 거리
    [SerializeField] private float holdDistanceMeters = 4f;   // 창 이동거리가 이 미만이면 고정
    [SerializeField] private float punchNearAverage = 5f;     // 창 평균 근접 적 수가 이 이상이면 관통
    [SerializeField] private float kiteTurnPerMeter = 0.30f;  // 미터당 누적 회전(rad)이 이 이상이면 선회

    private readonly List<Collider2D> hits = new List<Collider2D>(64);
    private readonly StringBuilder csv = new StringBuilder();
    private ContactFilter2D filter;
    private Vector2 lastPos, lastDir;
    private float windowStart, distance, turn, nearSum;
    private int samples;
    private bool flushed;

    private void Awake()
    {
        if (!Debug.isDebugBuild) { Destroy(this); return; }
        filter = new ContactFilter2D();
        filter.SetLayerMask(enemyLayer);   // 02장: 무할당 물리 조회 오버로드용 필터
        filter.useTriggers = true;
    }

    private void OnEnable()
    {
        csv.Clear();
        csv.Append("window_start_s,minute,distance_m,turn_rad,turn_per_m,near_avg,tactic\n");
        flushed = false;
        lastPos = player.position;
        lastDir = Vector2.zero;
        windowStart = spawner.Elapsed;
        distance = turn = nearSum = 0f;
        samples = 0;
        spawner.RunTimeCompleted += Flush;
    }

    private void OnDisable()
    {
        spawner.RunTimeCompleted -= Flush;
        Flush();   // 사망·중도 종료로 꺼질 때도 저장
    }

    private void FixedUpdate()
    {
        Vector2 pos = player.position;
        Vector2 step = pos - lastPos;
        float len = step.magnitude;
        if (len > 0.01f)
        {
            Vector2 dir = step / len;
            // 이동 방향이 꺾인 각도를 누적 → 원을 그리면 크게, 직진하면 0에 가깝게 쌓인다
            if (lastDir != Vector2.zero) turn += Mathf.Abs(Vector2.SignedAngle(lastDir, dir)) * Mathf.Deg2Rad;
            lastDir = dir;
            distance += len;
        }
        lastPos = pos;
        nearSum += Physics2D.OverlapCircle(pos, nearRadius, filter, hits);
        samples++;

        if (spawner.Elapsed - windowStart >= windowSeconds) CloseWindow();
    }

    private void CloseWindow()
    {
        float nearAvg = samples > 0 ? nearSum / samples : 0f;
        float turnPerM = distance > 0.5f ? turn / distance : 0f;

        // 순서가 규칙이다. 위에서부터 먼저 걸리는 것으로 분류한다.
        string tactic =
            distance < holdDistanceMeters ? "Hold" :
            nearAvg >= punchNearAverage   ? "Punch" :
            turnPerM >= kiteTurnPerMeter  ? "Kite" : "Flee";

        CultureInfo inv = CultureInfo.InvariantCulture;
        csv.AppendLine(string.Join(",",
            windowStart.ToString("0.0", inv), ((int)(windowStart / 60f)).ToString(inv),
            distance.ToString("0.0", inv), turn.ToString("0.00", inv),
            turnPerM.ToString("0.00", inv), nearAvg.ToString("0.0", inv), tactic));

        windowStart = spawner.Elapsed;
        distance = turn = nearSum = 0f;
        samples = 0;
    }

    private void Flush()
    {
        if (flushed) return;
        flushed = true;
        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Balance"));
        Directory.CreateDirectory(dir);
        string path = Path.Combine(dir, $"tactics_{System.DateTime.Now:yyyyMMdd_HHmmss}.csv");
        File.WriteAllText(path, csv.ToString(), new UTF8Encoding(true));
        Debug.Log($"대응 분포 저장: {path}");
    }
}
```

`_DebugCheats` 오브젝트에 붙이고 **Spawner**, **Player**, **Enemy Layer**를 연결합니다. 판이 끝나거나 죽으면 `Balance/tactics_<시각>.csv`가 생깁니다.

집계는 스프레드시트에서 합니다. `minute` 열로 피벗해 각 분의 대응별 창 수를 세면, **가장 큰 값 ÷ 12**(5초 창이므로 분당 12창)가 그 분의 지배 대응 비중입니다. 수정 전 3판 평균의 가상 결과는 다음과 같습니다.

| 분 | Kite | Flee | Punch | Hold | 지배 대응 | 비중 |
|---|---:|---:|---:|---:|---|---:|
| 0 | 11 | 1 | 0 | 0 | Kite | 92% |
| 1 | 10 | 2 | 0 | 0 | Kite | 83% |
| 2 | 9 | 2 | 1 | 0 | Kite | 75% |
| 3 | 9 | 3 | 0 | 0 | Kite | 75% |
| 4 | 10 | 1 | 1 | 0 | Kite | 83% |
| 5 | 11 | 0 | 1 | 0 | Kite | 92% |
| 6 | 10 | 1 | 1 | 0 | Kite | 83% |
| 7 | 11 | 0 | 1 | 0 | Kite | 92% |
| 8 | 10 | 1 | 1 | 0 | Kite | 83% |
| 9 | 11 | 0 | 1 | 0 | Kite | 92% |

```
지배 대응 비중 70% 이상인 분 = 10분 ÷ 10분 = 100%   (기준 30% 이하 → 미달)
10분 내내 지배 대응이 Kite 하나로 동일
```

여러 사람의 대응 분포를 모으려면 이 창 단위 기록을 애널리틱스 이벤트로 올려야 합니다. 이벤트 설계와 수집은 [24장](./24_playtest-analytics.md)에서 다룹니다. 이 장의 CSV는 **혼자 진단할 때**의 도구입니다.

#### 절차 C — 사망 원인 분포 (약 60분)

전술을 고수하지 않고 평소대로 12판을 하고, 판마다 결과 화면의 사망 원인(공정한 죽음 절에서 표시하기로 한 값)과 시각을 적습니다. 수정 전 가상 결과입니다.

| 사망 시각 | 원인 | 판 수 |
|---|---|---:|
| 6:00 | 엘리트 기사 2 | 2 |
| 9:00~9:40 | 코인 골렘왕 | 5 |
| — | 클리어 | 5 |
| **합계** | | **12** |

**6:00 이전의 사망이 0건입니다.** 절차 A·B와 같은 결론을 다른 각도에서 확인해 줍니다. 전반 6분은 "무슨 전술이든 통하고, 죽지도 않는" 구간입니다.

#### 진단: 왜 이렇게 되었나

세 절차의 결론은 하나로 모입니다. 원인을 1단계 적 데이터에 개념 절의 역할 분류를 붙여 보면 바로 보입니다.

| 적 | 역할 | 플레이어에게 요구하는 것 |
|---|---|---|
| 슬라임 | 압박 | 피한다 |
| 박쥐 | 압박 | 더 빨리 피한다 |
| 해골 | 압박 | 더 오래 피한다 |
| 골렘 | 차단 | 피하거나 돌아간다 |
| 엘리트 기사 | 처치 우선 | 피하면서 화력을 모은다 |
| 코인 골렘왕 | 처치 우선 | 피하면서 화력을 모은다 |

**적 6종 중 4종이 같은 역할이고, 나머지 둘도 "쫓아오는 것을 피한다"는 대응을 공유합니다.** 어떤 조합을 만들어도 답은 선회로 수렴합니다. 조합 규칙 R1·R2로 구간별 위반을 세면 이렇습니다.

| 구간 | 압박 역할 가중치 합 | R1 (한 역할 ≤ 70%) | R2 (2:00 이후 압박 외 1개 이상) |
|---|---:|---|---|
| 0:00~2:00 | 100% | 위반 | (2:00 이전이라 해당 없음) |
| 2:00~6:00 | 100% | 위반 | **위반** |
| 6:00~7:00 | 90% | 위반 | 충족 (골렘) |
| 7:00~8:00 | 80% | 위반 | 충족 |
| 8:00~9:00 | 70% | 충족 (경계) | 충족 |
| 9:00~10:00 | 50% | 충족 | 충족 |

수정 방향이 정해집니다. **스폰율이나 체력 배율을 더 올리는 것으로는 아무것도 해결되지 않습니다.** 빠진 역할(처치 우선 중 근접 거부, 환경 변화)을 넣고, 그 역할이 실제로 대응을 바꾸도록 구성과 스폰 위치를 고쳐야 합니다. 이것이 10단계입니다.

### 10단계: 적에게 역할을 주고 웨이브를 고치기

진단이 가리킨 것은 "적이 적다"가 아니라 "역할이 하나뿐이다"였습니다. 그래서 빠진 두 역할을 채웁니다.

| 새 적 | 역할 | 규칙 | 선회를 왜 깨는가 |
|---|---|---|---|
| **폭탄충** (Enemy_Bomber) | 처치 우선 (근접 거부) | 이동이 빠르고, 죽으면 그 자리에서 0.8초 뒤 반경 2.5에 폭발 | 선회는 무리를 **뒤에 붙여 끌고** 다니는 전술이고, 자동 공격은 **가장 가까운 적**을 칩니다. 그래서 선회 중에는 폭탄충이 항상 내 바로 뒤에서 죽습니다. 무리를 흩거나, 폭탄충만 먼저 떼어내 멀리서 처리해야 합니다 |
| **주술사** (Enemy_Warden) | 환경 변화 | 느리고 접촉 피해가 없으며, 살아 있는 동안 자기 주변 반경 4에 둔화 장판(이동속도 ×0.6)을 깝니다 | 선회는 **일정한 원**을 그려야 성립합니다. 진행 방향 앞에 장판이 깔리면 원이 끊기고, 돌아가거나 **무리를 뚫고 들어가 주술사를 먼저 없애는** 선택을 해야 합니다 |

두 적 모두 그레이박스 수준으로 충분합니다. 폭탄충은 빨간 사각형, 주술사는 보라 사각형에 반투명 원 하나면 됩니다(아트는 [31장](./31_art-audio.md)).

#### 10-1. EnemyData에 역할 필드 추가

역할은 데이터입니다. 03장 `EnemyData`에 필드 하나를 더합니다. 파일: `Assets/_CoinRush/Scripts/Data/EnemyRole.cs`

```csharp
// 새 값은 반드시 끝에 추가 (에셋에 숫자로 저장되므로 순서를 바꾸면 기존 적의 역할이 바뀐다)
public enum EnemyRole { Pressure, Blocker, Priority, Zoner }
```

```csharp
// EnemyData.cs (03장) — 필드 추가
[Header("역할 (22장)")]
public EnemyRole role = EnemyRole.Pressure;
```

기존 6종의 역할을 9단계 진단 표대로 채우고, 새 두 종을 추가합니다.

| 에셋 | 역할 | maxHp | moveSpeed | contactDamage | coinDrop | 비고 |
|---|---|---|---|---|---|---|
| Enemy_Slime | Pressure | 10 | 1.5 | 5 | 1 | |
| Enemy_Bat | Pressure | 6 | 3.0 | 4 | 1 | |
| Enemy_Skeleton | Pressure | 30 | 1.8 | 8 | 2 | |
| Enemy_Golem | Blocker | 120 | 1.0 | 15 | 6 | |
| Enemy_EliteKnight | Priority | 400 | 2.0 | 20 | 30 | |
| Enemy_KingGolem | Priority | 3000 | 1.2 | 30 | 300 | |
| **Enemy_Bomber** | **Priority** | **20** | **2.2** | **6** | **3** | 박쥐 다음으로 빠름 — 선회 꼬리에 먼저 도착한다 |
| **Enemy_Warden** | **Zoner** | **80** | **0.9** | **0** | **5** | 접촉 피해 0. 위험한 것은 장판이지 몸이 아니다 |

주술사의 `contactDamage`를 0으로 둔 것은 가독성 결정입니다. 몸으로도 아프고 장판으로도 아프면 플레이어는 무엇에 당했는지 구분할 수 없습니다.

#### 10-2. 폭탄충 — 죽은 자리에 남는 예고와 폭발

폭발은 적보다 오래 살아야 합니다. 적은 죽자마자 연출을 마치고 풀로 돌아가므로(4단계), 폭발은 **별도 오브젝트**로 남깁니다. 파일: `Assets/_CoinRush/Scripts/Enemies/ExploderOnDeath.cs`

```csharp
using UnityEngine;

// 폭탄충 프리팹(Enemy_Bomber가 참조하는 prefab)에 붙인다
[RequireComponent(typeof(Health))]
public class ExploderOnDeath : MonoBehaviour
{
    [SerializeField] private BombBlast blastPrefab;
    private Health health;

    private void Awake() => health = GetComponent<Health>();

    // OnEnable/OnDisable 짝이므로 풀에서 재사용해도 구독이 중복되지 않는다
    private void OnEnable() => health.Died += SpawnBlast;
    private void OnDisable() => health.Died -= SpawnBlast;

    private void SpawnBlast() => Instantiate(blastPrefab, transform.position, Quaternion.identity);
}
```

파일: `Assets/_CoinRush/Scripts/Enemies/BombBlast.cs`

```csharp
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BombBlast : MonoBehaviour
{
    [SerializeField] private float radius = 2.5f;
    [SerializeField] private int damage = 25;
    [SerializeField, Min(0.1f)] private float fuseSeconds = 0.8f;   // 개념 절 검산: 반경 ÷ 플레이어 속도보다 넉넉히
    [SerializeField] private LayerMask playerLayer;
    [SerializeField] private Transform ring;                        // 지름 1인 원 스프라이트 자식

    private readonly List<Collider2D> hits = new List<Collider2D>(4);

    private IEnumerator Start()
    {
        ContactFilter2D filter = new ContactFilter2D();
        filter.SetLayerMask(playerLayer);
        filter.useTriggers = true;

        float t = 0f;
        while (t < fuseSeconds)
        {
            t += Time.deltaTime;   // 레벨업·컷신으로 시간이 멈추면 예고도 멈춘다 (공정)
            ring.localScale = Vector3.one * radius * 2f * Mathf.Lerp(0.35f, 1f, t / fuseSeconds);
            yield return null;
        }

        if (Physics2D.OverlapCircle(transform.position, radius, filter, hits) > 0)
        {
            Health hp = hits[0].GetComponentInParent<Health>();
            if (hp != null) hp.TakeDamage(damage);
        }
        Destroy(gameObject);   // 16장 폭발 연출을 붙인다면 여기서 재생한 뒤 파괴
    }
}
```

`BombBlast` 프리팹은 빈 오브젝트 + 반투명 원 스프라이트 자식(`ring`) 하나면 됩니다. **예고 원의 크기는 실제 반경과 같아야 합니다.** 연출용으로 조금 작게 그리면 "밖에 있었는데 맞았다"가 되고, 그 순간 전술 전환이 아니라 불공정한 죽음이 됩니다.

> 폭발마다 `Instantiate`가 일어납니다. 진단-수정 루프를 빨리 돌리는 것이 목적이라 여기서는 그대로 두고, 동시 폭발이 잦아 프레임이 흔들리면 12장 오브젝트 풀로 옮깁니다(18장 기준으로 측정한 뒤에).

#### 10-3. 주술사 — 둔화 장판

장판은 플레이어의 이동 속도를 건드립니다. 07장 `PlayerMover`에 배율 하나를 추가합니다. 파일 상단에 `using System.Collections.Generic;`을 더합니다.

```csharp
// PlayerMover.cs (07장) — 필드·메서드 추가
private readonly List<float> speedPenalties = new List<float>(4);
public float SpeedMultiplier { get; private set; } = 1f;

public void AddSpeedPenalty(float multiplier)    { speedPenalties.Add(multiplier); RecalcSpeed(); }
public void RemoveSpeedPenalty(float multiplier) { speedPenalties.Remove(multiplier); RecalcSpeed(); }

// 장판이 겹쳐도 가장 강한 하나만 적용한다 — 셋이 겹쳐 0.6³ = 0.216배가 되는 즉사 구간을 막는다
private void RecalcSpeed()
{
    float m = 1f;
    foreach (float p in speedPenalties) m = Mathf.Min(m, p);
    SpeedMultiplier = m;
}
```

`FixedUpdate`의 두 줄을 바꿉니다.

```csharp
// PlayerMover.FixedUpdate (07장) — 두 줄 교체
Vector2 target = input * maxSpeed * SpeedMultiplier;
float rate = maxSpeed * SpeedMultiplier / (accelerating ? accelTime : decelTime);
```

파일: `Assets/_CoinRush/Scripts/Enemies/SlowField.cs`

```csharp
using UnityEngine;

// 주술사 프리팹의 자식에 붙인다. CircleCollider2D(Is Trigger, 반지름 4) + 반투명 원 스프라이트
[RequireComponent(typeof(CircleCollider2D))]
public class SlowField : MonoBehaviour
{
    [SerializeField, Range(0.1f, 1f)] private float speedMultiplier = 0.6f;
    private PlayerMover affected;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (affected != null) return;
        PlayerMover mover = other.GetComponentInParent<PlayerMover>();
        if (mover == null) return;
        affected = mover;
        affected.AddSpeedPenalty(speedMultiplier);
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        if (affected != null && other.GetComponentInParent<PlayerMover>() == affected) Release();
    }

    // 주술사가 죽어 풀로 돌아가면 OnTriggerExit2D는 오지 않는다 → 여기서 반드시 해제
    private void OnDisable() => Release();

    private void Release()
    {
        if (affected == null) return;
        affected.RemoveSpeedPenalty(speedMultiplier);
        affected = null;
    }
}
```

`OnDisable`의 해제가 이 스크립트에서 가장 중요한 줄입니다. 빠뜨리면 주술사를 죽인 순간 플레이어가 **영구히 0.6배 속도**로 남고, 그 증상은 몇 분 뒤 "왜 이렇게 느리지"로 나타나 원인을 찾기 어렵습니다. 장판 스프라이트는 콜라이더 반지름과 같은 크기여야 합니다(가독성 절의 상시 표시).

#### 10-4. 스폰 규칙 — 차단·환경 변화는 "앞"에 놓는다

주술사를 등 뒤에 놓으면 장판은 지나간 자리에만 깔립니다. 경로를 실제로 끊으려면 **플레이어 진행 방향 앞**에 놓아야 합니다. 5단계 `EnemySpawner`에 필드 둘과 메서드 하나를 추가하고, 스폰 한 줄을 바꿉니다.

```csharp
// EnemySpawner.cs (5단계) — 필드 추가
[SerializeField, Range(0f, 1f)] private float aheadDot = 0.5f;   // 진행 방향 ±60° 안
private Rigidbody2D playerBody;

// Awake 안에 한 줄 추가
playerBody = player.GetComponent<Rigidbody2D>();
```

```csharp
// TickSegment의 스폰 한 줄 교체
if (data != null) SpawnEnemy(data, seg.hpMultiplier, PickPointFor(data));
```

```csharp
// EnemySpawner.cs — 메서드 추가
/// <summary>역할에 따라 스폰 위치를 고른다. 차단·환경 변화는 앞에 놓아야 경로를 끊는다.</summary>
private Vector2 PickPointFor(EnemyData data)
{
    return data.role == EnemyRole.Blocker || data.role == EnemyRole.Zoner
        ? PickAheadPoint()
        : PickSpawnPoint(mustBeInsideMap: false);
}

/// <summary>플레이어 진행 방향 앞쪽 테두리 점. 멈춰 있으면 방향이 없으므로 일반 규칙으로 돌아간다.</summary>
private Vector2 PickAheadPoint()
{
    Vector2 heading = playerBody != null ? playerBody.linearVelocity : Vector2.zero;
    if (heading.sqrMagnitude < 0.25f) return PickSpawnPoint(mustBeInsideMap: false);
    heading.Normalize();

    for (int attempt = 0; attempt < 12; attempt++)
    {
        Vector2 point = PickSpawnPoint(mustBeInsideMap: false);
        Vector2 toPoint = point - (Vector2)player.position;
        if (toPoint.sqrMagnitude > 0.0001f && Vector2.Dot(toPoint.normalized, heading) >= aheadDot)
            return point;
    }
    return PickSpawnPoint(mustBeInsideMap: false);   // 맵이 좁아 앞쪽 테두리를 못 찾은 경우
}
```

이벤트에도 도입 단계를 위한 종류를 하나 더합니다. 새 요소를 **단독으로, 보이는 곳에서** 만나게 하는 이벤트입니다.

```csharp
// WaveData.cs (3단계) — enum 끝에 값 추가
public enum WaveEventType { Elite, Boss, Swarm, Shrine, Introduce }
```

```csharp
// EnemySpawner.StartEvent (5단계) — else 분기의 첫 두 줄 교체
// 엘리트·보스는 맵 안 한 지점에서, 도입(Introduce)은 플레이어 진행 방향 앞에서 나란히
Vector2 anchor = e.type == WaveEventType.Introduce
    ? PickAheadPoint()
    : PickSpawnPoint(mustBeInsideMap: true);
```

#### 10-5. 조합 규칙을 에디터가 검사하게

개념 절의 R1·R2는 표를 옮기다 보면 반드시 깨집니다. 3단계 `WaveData`에 검사를 넣습니다.

```csharp
// WaveSegment 안에 메서드 추가
public int WeightOfRole(EnemyRole role)
{
    int total = 0;
    foreach (SpawnEntry e in entries)
        if (e.enemy != null && e.enemy.role == role) total += e.weight;
    return total;
}
```

```csharp
// WaveData.OnValidate — 구간 루프 안, 가중치 합 검사 다음에 추가
int total = s.TotalWeight();
if (total > 0)
{
    // R1: 한 역할이 가중치의 70%를 넘지 않는다
    foreach (EnemyRole role in System.Enum.GetValues(typeof(EnemyRole)))
        if (s.WeightOfRole(role) * 100 > total * 70)
            Debug.LogWarning($"[{name}] 구간 {i}({s.label}): {role} 역할이 가중치의 70%를 넘습니다 (R1).", this);

    // R2: 2:00 이후에는 압박 외 역할이 하나 이상 있어야 한다
    if (s.startTime >= 120f && s.WeightOfRole(EnemyRole.Pressure) == total)
        Debug.LogWarning($"[{name}] 구간 {i}({s.label}): 2:00 이후인데 압박 역할만 있습니다 (R2).", this);
}
```

이제 `Wave_Stage1`을 열면 9단계 진단 표와 똑같은 경고가 Console에 줄줄이 뜹니다. 이것이 수정 전의 상태입니다.

#### 10-6. 새 역할을 소개 4단계에 배치

새 역할은 규칙이라서 **배워야 쓸 수 있습니다**(R3). 개념 절의 4단계 소개를 그대로 적용합니다.

| 역할 | 도입 | 연습 | 변형 | 조합 |
|---|---|---|---|---|
| 폭탄충 | **2:05** 제단 직후 이완 구간에 단독 2마리 | 2:00~4:00 구성 15~20% | **7:30** 폭탄충 10마리 원형 포위 — 뚫으려면 폭발 사이로 나가야 함 | 7:00~ 골렘이 길을 막는 사이 폭탄충이 붙음 |
| 주술사 | **4:05** 단독 1마리 | 4:00~6:00 구성 10% | **5:20** 진행 방향 앞에 3마리 나란히 — 선회 경로를 정면으로 차단 | 8:00~ 골렘 벽 + 장판 |

2단계 이벤트 표에 네 줄을 더합니다.

| 시각 | 종류 | 적 | 수 | 이벤트 체력 배율 | 경고 (초 전) | 경고 문구 |
|---|---|---|---|---|---|---|
| 2:05 | Introduce | Enemy_Bomber | 2 | 1.0 | 2 | "붉은 적은 죽을 때 터진다" |
| 4:05 | Introduce | Enemy_Warden | 1 | 1.0 | 2 | "느려지는 땅을 만드는 적" |
| 5:20 | Introduce | Enemy_Warden | 3 | 1.0 | 3 | "앞을 막는다" |
| 7:30 | Swarm | Enemy_Bomber | 10 | 1.0 | 2 | "폭탄충 포위!" |

R4(동시에 읽을 지속형 표시는 2종까지)도 여기서 검산합니다.

| 시각 | 화면에 동시에 떠 있는 지속형 표시 | 종류 수 | 판정 |
|---|---|---|---|
| 5:20 | 둔화 장판, 폭발 예고 원 | 2 | 통과 |
| 6:00 | 둔화 장판, 폭발 예고 원 (엘리트 경고는 3초 단발이라 제외) | 2 | 통과 |
| 7:30 | 폭발 예고 원(다수), 둔화 장판 | 2 | 통과 |
| 9:00 | 보스 패턴 표식, 둔화 장판 | 2 | 통과 — **그래서 9:00~10:00 구성에서 폭탄충을 뺀다** |

#### 10-7. 수정 전후 웨이브 표

먼저 무엇을 왜 바꿨는지입니다. **위협 비율은 거의 그대로 두고 구성만 바꾼 것**이 요점입니다.

| 구간 | 무엇을 바꿨나 | 위협 비율 전 → 후 | 강제되는 대응 변화 |
|---|---|---|---|
| 0:00~2:00 | 변경 없음 | 0.67 → 0.67 / 0.59 → 0.59 | 없음 (조작 학습 구간, 의도적 단조) |
| 2:00~3:00 | 슬라임 50 → 35, 해골 20 → 5, 폭탄충 30 신설 | 0.62 → 0.61 | 무리를 뒤에 붙여 끌 수 없음 |
| 3:00~4:00 | 슬라임 40 → 25, 박쥐 40 → 25, 폭탄충 30 신설, 스폰율 1.2 → 1.0 | 0.55 → 0.59 | 엘리트를 끌면서 폭탄충 처리 순서를 정해야 함 |
| 4:00~5:00 | 슬라임 30 → 15, 박쥐 30 → 25, 해골 40 → 25, 폭탄충 20·주술사 15 신설, 스폰율 1.5 → 0.95 | 0.69 → 0.69 | 선회 경로가 끊김 — 우회할지 뚫을지 |
| 5:00~6:00 | 슬라임 20 → 10, 박쥐 30 → 25, 해골 50 → 30, 폭탄충 20·주술사 15, 스폰율 1.7 → 1.15 | 0.74 → 0.73 | 5:20 장판 3개가 경로를 정면 차단 |
| 6:00~7:00 | 해골 50 → 40, 박쥐 40 → 30, 폭탄충 10·주술사 10, 스폰율 1.2 → 1.0 | 0.70 → 0.71 | 엘리트 2 + 장판 + 폭발 — 위치를 먼저 잡아야 함 |
| 7:00~8:00 | 해골 50 → 45, 박쥐 30 → 20, 골렘 20 → 15, 폭탄충 10·주술사 10, 스폰율 1.2 → 1.15 | 0.82 → 0.82 | 골렘 벽 + 폭탄충 조합 |
| 8:00~9:00 | 해골 50 → 40, 박쥐 20 → 15, 골렘 30 → 25, 폭탄충 10·주술사 10 | 0.81 → 0.82 | 장판 밖에서 골렘 벽을 상대 |
| 9:00~10:00 | 골렘 50 → 40, 주술사 10 추가(폭탄충은 제외 — R4), 스폰율 0.7 → 0.75 | 0.63 → 0.64 | 보스전 중에도 서 있을 자리를 고름 |

2:00~3:00의 위협은 15.4 HP/초로 **수정 전과 완전히 같습니다**(2단계 표의 0.62는 반올림 표기 차이이고, 정확한 값은 15.36 ÷ 25 = 0.61입니다). 난이도를 손대지 않고 대응만 바꾼 칸이 여기입니다. 4:00~6:00에서 스폰율을 크게 내린 것은 폭탄충·주술사의 **처리 비용**이 체력 이상으로 크기 때문입니다. 마리 수를 그대로 두면 위협 비율이 0.8을 넘어 몰입 구간이 긴장 구간으로 바뀝니다.

수정 후 10분 웨이브 표입니다. 굵은 값이 바뀐 칸입니다.

| 구간 | 구성 (가중치) | 스폰율 | 최대 동시 | 체력 배율 | 평균 체력 | 위협 (HP/초) | 예상 유효 DPS | 위협 비율 | 리듬 | 이벤트 / 의도 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0:00~1:00 | 슬라임 100 | 0.8 | 30 | 1.00 | 10.0 | 8.0 | 12 | 0.67 | 몰입 | 조작 익히기 |
| 1:00~2:00 | 슬라임 70, 박쥐 30 | 1.2 | 50 | 1.00 | 8.8 | 10.6 | 18 | 0.59 | 이완→몰입 | 박쥐 도입 |
| 2:00~3:00 | 슬라임 **35**, 박쥐 30, 해골 **5**, **폭탄충 30** | 1.2 | 60 | 1.00 | 12.8 | 15.4 | 25 | **0.61** | 몰입 | 2:00 제단(50), **2:05 폭탄충 도입** |
| 3:00~4:00 | 슬라임 **25**, 박쥐 **25**, 해골 **20**, **폭탄충 30** | **1.0** | 60 | 1.10 | **17.6** | **17.6** | 30 | **0.59** | 정점→이완 | 2:57 경고, 3:00 엘리트 1 |
| 4:00~5:00 | 슬라임 **15**, 박쥐 **25**, 해골 **25**, **폭탄충 20, 주술사 15** | **0.95** | 80 | 1.10 | **29.2** | **27.7** | 40 | 0.69 | 몰입 | 4:00 제단(100), **4:05 주술사 도입**, 4:30 박쥐 떼 |
| 5:00~6:00 | 슬라임 10, 박쥐 **25**, 해골 **30**, **폭탄충 20, 주술사 15** | **1.15** | 100 | 1.15 | **31.6** | **36.4** | 50 | **0.73** | 긴장 상승 | **5:20 주술사 3마리(변형)** |
| 6:00~7:00 | 해골 40, 박쥐 30, 골렘 10, **폭탄충 10, 주술사 10** | **1.0** | 100 | 1.15 | **41.2** | **41.2** | 58 | **0.71** | 정점→이완 | 5:57 경고, 6:00 엘리트 2 → 6:30 제단(150) |
| 7:00~8:00 | 해골 45, 박쥐 20, 골렘 15, **폭탄충 10, 주술사 10** | **1.15** | 120 | 1.20 | **51.2** | **58.9** | 72 | 0.82 | 긴장 | **7:30 폭탄충 포위(변형)**, 골렘+폭탄충 조합 |
| 8:00~9:00 | 해골 40, 박쥐 15, 골렘 25, **폭탄충 10, 주술사 10** | **1.1** | 150 | 1.20 | **63.5** | **69.8** | 85 | **0.82** | 긴장 | 8:00 제단(200) |
| 9:00~10:00 | 해골 50, 골렘 40, **주술사 10** | **0.75** | 120 | 1.20 | **85.2** | **63.9** | 100 | **0.64** | 최종 정점 | 8:55 경고, 9:00 보스. 폭탄충 없음(R4) |

검산은 개념 절의 식 그대로입니다. 예를 들어 4:00~5:00은 이렇습니다.

```
평균 체력 = (10×15 + 6×25 + 30×25 + 20×20 + 80×15) ÷ 100 × 1.10
          = (150 + 150 + 750 + 400 + 1,200) ÷ 100 × 1.10 = 26.5 × 1.10 = 29.15 → 29.2
위협      = 0.95 × 29.15 = 27.69 → 27.7 HP/초
위협 비율 = 27.69 ÷ 40 = 0.69

평균 코인 = (1×15 + 1×25 + 2×25 + 3×20 + 5×15) ÷ 100 = 2.25 개/마리
코인 공급 = 0.95 × 2.25 = 2.14 개/초
```

R1·R2도 다시 셉니다. 2:00 이후 모든 구간에서 압박 역할 합이 70% 이하이고, 압박 외 역할이 최소 하나 있습니다.

| 구간 | 압박 | 차단 | 처치 우선 | 환경 변화 | R1 | R2 |
|---|---:|---:|---:|---:|---|---|
| 2:00~3:00 | 70 | 0 | 30 | 0 | 충족 (경계) | 충족 |
| 3:00~4:00 | 70 | 0 | 30 | 0 | 충족 (경계) | 충족 |
| 4:00~5:00 | 65 | 0 | 20 | 15 | 충족 | 충족 |
| 5:00~6:00 | 65 | 0 | 20 | 15 | 충족 | 충족 |
| 6:00~7:00 | 70 | 10 | 10 | 10 | 충족 (경계) | 충족 |
| 7:00~8:00 | 65 | 15 | 10 | 10 | 충족 | 충족 |
| 8:00~9:00 | 55 | 25 | 10 | 10 | 충족 | 충족 |
| 9:00~10:00 | 50 | 40 | 0 | 10 | 충족 | 충족 |

세 구간이 정확히 70%에 걸려 있습니다. 경계값은 통과이지만 여유가 없다는 뜻이므로, [23장](./23_balancing-economy.md)에서 수치를 조정하다 슬라임이나 해골 가중치를 조금만 올리면 바로 R1 경고가 뜹니다. 경고가 뜨면 "다시 단조로 돌아가는 중"이라는 신호로 읽으세요.

#### 10-8. 구성을 바꾸면 코인 공급도 바뀐다

개념 절의 제단 지갑 표는 **적 구성에서 나온 값**입니다. 폭탄충(코인 3)과 주술사(코인 5)가 들어가면 공급이 늘어납니다. 같은 식으로 다시 계산합니다.

```
구간 코인 공급(개/초) = 스폰율 × 평균 코인 드롭
누적 공급 = Σ(구간 공급 × 구간 길이) + Σ(그 시각까지의 이벤트 적 코인)
지갑 상한 = 누적 공급 × 0.6   (모든 적을 처치하고 60%를 주웠을 때 — 상한)
```

| 제단 | 수정 전 지갑 상한 | 수정 후 지갑 상한 | 가격 (50×n) | 판정 |
|---|---:|---:|---:|---|
| 2:00 | 72 | 72 | 50 | 살 수 있음 |
| 4:00 | 194 | **230** | 100 | 살 수 있음 |
| 6:30 | 455 | **509** | 150 | 살 수 있음 |
| 8:00 | 606 | **688** | 200 | 살 수 있음 |
| 판 끝 (10:00) | 1,006 | **1,102** | 합계 500 | 네 번 다 사도 602 남음 |

공급이 약 10% 늘었지만 가격 50×n은 그대로 둡니다. 모든 제단에서 "살 수 있다"가 유지되고, 다 사도 절반 이상이 남아 저축과의 경쟁도 유지되기 때문입니다. 이 값은 [23장](./23_balancing-economy.md) 시뮬레이터에서 실제 수집률로 다시 검증합니다. 7단계 CSV를 다시 뽑아 `coins_per_min` 열이 여기 계산과 맞는지 확인하세요.

#### 10-9. 에디터 작업

1. `Enemy_Bomber`, `Enemy_Warden` `EnemyData` 에셋을 만들고 위 표대로 채웁니다. 기존 6종의 `Role`도 채웁니다.
2. 폭탄충 프리팹(빨간 사각형)에 `Enemy`·`Health`·`ExploderOnDeath`를 붙이고 `BombBlast` 프리팹을 연결합니다. **`Health`의 Max는 1로 둡니다**(4단계).
3. 주술사 프리팹(보라 사각형)에 `Enemy`·`Health`와, 자식 오브젝트 `SlowField`(CircleCollider2D Is Trigger 반지름 4 + 같은 크기의 반투명 원 스프라이트)를 붙입니다.
4. `Wave_Stage1`의 Segments 10개를 수정 후 표대로 고치고, Events에 네 줄을 추가합니다(총 12개). Console에 R1·R2 경고가 남아 있지 않아야 합니다.
5. 19장 `StageLoader`의 Prewarm 목록에 새 적 두 종을 추가합니다. 빠뜨리면 첫 스폰 때 풀이 만들어지며 프레임이 튑니다.
6. 7단계 **Threat Curve Report**를 다시 실행해 `threat_hp_per_s` 열이 수정 후 표(8.0, 10.6, 15.4, 17.6, 27.7, 36.4, 41.2, 58.9, 69.8, 63.9)와 맞는지 확인합니다.

### 11단계: 재측정 — 정말 대응이 바뀌었는가

수정했다고 고쳐진 것이 아닙니다. 9단계의 세 절차를 **같은 방법으로** 다시 돌립니다. 21장의 반복 루프와 같은 규칙입니다. 바꾼 것을 되돌릴 수 있게 커밋을 나누고(`wave-v1`, `wave-v2` 태그), 기준은 수정 전에 정한 것을 그대로 씁니다.

#### 2차 측정 (가상 결과)

**절차 A — 단일 전술 완주 테스트**

| 분 | 선회 | 도주 | 관통 | 고정 | 통과 전술 수 |
|---|---|---|---|---|---:|
| 0:00~1:00 | ✓ | ✓ | ✓ | ✓ | 4 |
| 1:00~2:00 | ✓ | ✓ | ✓ | ✓ | 4 |
| 2:00~3:00 | ✗ | ✓ | ✗ | ✗ | 1 |
| 3:00~4:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| 4:00~5:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| 5:00~6:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| 6:00~7:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| 7:00~8:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| 8:00~9:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| 9:00~10:00 | ✗ | ✗ | ✗ | ✗ | 0 |
| **전술별 통과 분 수** | 2 | **3** | 2 | 2 | |

```
단조 지수      = 3 ÷ 10 = 0.30        (기준 0.3 이하 → 충족, 다만 경계)
최장 연속 구간 = 도주, 0:00~3:00 = 3분 (기준 3분 미만 → 미달)
```

선회는 2:00부터 바로 깨졌습니다. 폭탄충이 박쥐 다음으로 빠르고 자동 공격은 가장 가까운 적을 치므로, 무리를 뒤에 붙여 끌면 반드시 등 뒤에서 터집니다. 그런데 **도주가 3분 연속 통과**합니다. 폭탄충은 이동속도 2.2, 플레이어 최고 속도 6이라 직선으로 달아나면 애초에 접근하지 못하고, 맵 경계에 부딪혀 방향을 꺾어야 하는 시점이 3:00 이후에야 옵니다.

**절차 B — 대응 분포** (3판 평균, 분당 12창)

| 분 | Kite | Flee | Punch | Hold | 지배 대응 | 비중 | 수정 전 |
|---|---:|---:|---:|---:|---|---:|---:|
| 0 | 11 | 1 | 0 | 0 | Kite | 92% | 92% |
| 1 | 10 | 2 | 0 | 0 | Kite | 83% | 83% |
| 2 | 3 | 8 | 1 | 0 | Flee | 67% | 75% |
| 3 | 7 | 3 | 2 | 0 | Kite | 58% | 75% |
| 4 | 3 | 2 | 6 | 1 | Punch | 50% | 83% |
| 5 | 6 | 3 | 2 | 1 | Kite | 50% | 92% |
| 6 | 2 | 7 | 3 | 0 | Flee | 58% | 83% |
| 7 | 3 | 2 | 5 | 2 | Punch | 42% | 92% |
| 8 | 6 | 3 | 2 | 1 | Kite | 50% | 83% |
| 9 | 2 | 7 | 2 | 1 | Flee | 58% | 92% |

```
지배 대응 비중 70% 이상인 분 = 2분 ÷ 10분 = 20%   (기준 30% 이하 → 충족)
지배 대응 종류 = Kite / Flee / Punch 세 가지      (수정 전에는 Kite 하나)
```

**절차 C — 사망 원인 분포** (12판)

| 사망 시각 | 원인 | 수정 전 | 수정 후 |
|---|---|---:|---:|
| 2:00~4:00 | 폭탄충 폭발 | 0 | 4 |
| 4:00~8:00 | 장판 안에서 해골·골렘 | 0 | 2 |
| 6:00 | 엘리트 기사 2 | 2 | 0 |
| 7:30 | 폭탄충 포위 | 0 | 1 |
| 9:00~9:40 | 코인 골렘왕 | 5 | 3 |
| — | 클리어 | 5 | **2** |
| **합계** | | **12** | **12** |

#### 2차 판정: 두 가지가 남았다

| 지표 | 수정 전 | 수정 후 | 기준 | 판정 |
|---|---:|---:|---|---|
| 단조 지수 | 1.00 | 0.30 | ≤ 0.30 | 충족 |
| 최장 연속 통과 구간 | 10분 (선회) | 3분 (도주) | < 3분 | **미달** |
| 지배 대응 비중 70% 이상인 분 | 100% | 20% | ≤ 30% | 충족 |
| 지배 대응의 종류 수 | 1 | 3 | — | 개선 |
| 자기 테스트 클리어율 | 5/12 = 42% | **2/12 = 17%** | 30~50% | **미달** |

> 클리어율 30~50%는 이 교재가 정한 **작업 기준**입니다. 설계자는 자기 게임에 가장 숙련되어 있으므로 일반 플레이어보다 높게 나온다는 가정에서 나온 값이고, 실제 플레이어 기준은 [24장](./24_playtest-analytics.md)의 `run_end` 이벤트로 따로 정합니다. 업계 표준값이 아닙니다.

문제가 둘이면 둘을 한꺼번에 고치고 싶어집니다. **하지 않습니다.** 21장의 규칙대로 한 번에 한 건이고, 더 급한 것부터입니다.

| 문제 | 급한가 | 이번에 고치나 |
|---|---|---|
| 클리어율 17% | 게임을 끝까지 볼 수 없다. 이 상태로 남기면 다른 모든 측정이 오염된다 | **예** |
| 도주 3분 연속 통과 | 0:00~3:00은 학습 구간이기도 하다. 지표 하나가 경계에 걸린 상태 | 아니오 — 다음 루프 |

#### 3차 변경 (1건)과 재측정

```
[변경 기록] 웨이브 v3 — 1건

무엇  BombBlast의 damage 25 → 18
어디  BombBlast 프리팹 한 칸 (에셋 1개, 커밋 1개)
가설  폭발이 "피해야 하는 것"에서 "맞으면 끝나는 것"이 되어 클리어율이 무너졌다
      근거: 12판 중 사망 10건 가운데 4건이 2:00~4:00 폭발, 모두 체력 절반 이상에서 즉사

같이 바꾸지 않은 것
  폭발 반경 2.5, 예고 시간 0.8초, 폭탄충 가중치·이동속도, 웨이브 표 전체
  (반경·예고를 함께 줄이면 가독성 검산이 무너지고 원인도 못 가린다)

되돌리기  wave-v2 / wave-v3 태그
재측정    같은 12판, 같은 배속, 절차 A·B·C 전부
```

3차 결과(가상)입니다.

| 지표 | v2 | v3 | 기준 | 판정 |
|---|---:|---:|---|---|
| 자기 테스트 클리어율 | 2/12 = 17% | **4/12 = 33%** | 30~50% | 충족 |
| 단조 지수 | 0.30 | 0.30 | ≤ 0.30 | 충족 |
| 최장 연속 통과 구간 | 3분 | 3분 | < 3분 | 미달 (유지) |
| 지배 대응 비중 70% 이상인 분 | 20% | 20% | ≤ 30% | 충족 |
| 2:00~4:00 폭발 사망 | 4 | 1 | — | — |

피해를 낮췄는데도 단조 지수와 대응 분포가 그대로인 것이 중요합니다. **예고 원을 피하는 행동 자체는 여전히 요구되기 때문**입니다. 전술 전환을 만드는 것은 피해량이 아니라 "이 자리에 있으면 안 된다"는 규칙이라는 뜻입니다. 만약 피해를 낮추자 단조 지수가 함께 올라갔다면, 그것은 폭탄충이 전술이 아니라 피해량으로만 작동하고 있었다는 신호이므로 반경이나 예고 시간을 손봐야 합니다.

#### 남긴 것과 넘기는 것

- **다음 루프 항목**: 도주 0:00~3:00 연속 통과. 후보는 (a) 폭탄충 이동속도 2.2 → 3.2로 올려 직선 도주로 떼어낼 수 없게 하기, (b) 2:00~3:00에 골렘 소수를 넣어 도주 경로를 끊기. 둘 중 하나만, [23장](./23_balancing-economy.md) 시뮬레이터로 위협·코인 영향을 먼저 계산한 뒤 고릅니다.
- **여러 명의 대응 분포**는 이 장의 CSV로는 모을 수 없습니다. 창 단위 기록을 이벤트로 올리는 설계는 [24장](./24_playtest-analytics.md)에서 만듭니다.
- **무기·강화 선택이 한쪽으로 쏠리는 문제**(지배 전략)와 **빌드 다양성**은 웨이브가 아니라 업그레이드 쪽 문제이므로 [23장](./23_balancing-economy.md)에서 다룹니다. 웨이브가 아무리 다양해도 최적 빌드가 하나면 대응은 다시 하나로 수렴합니다.
- **콘텐츠 고갈**(몇 판 만에 다 봤다고 느끼는가)의 지표도 [24장](./24_playtest-analytics.md) 몫입니다.

### 확인하기

1. Play → 스테이지 로드 후 좌상단에 `0:00 x1 alive 0`이 보이고 슬라임만 화면 밖에서 들어오면 성공입니다. 첫 생성된 적에게 데미지 숫자·번쩍임이 뜨지 않아야 합니다(4단계).
2. **맵 모서리 확인**: 플레이어를 맵 네 모서리로 차례로 옮겨 각각 30초씩 서 있습니다. 카메라가 경계에 막힌 상태에서도 적이 **화면 안에서 갑자기 생기지 않고** 항상 화면 테두리 밖에서 걸어 들어와야 합니다. 의심되면 Scene 뷰를 함께 띄워 스폰 순간을 봅니다.
3. **F3** → 1:56 부근으로 이동, "코인 제단이 열린다"가 깜빡입니다(제단 자체는 23장에서 생김). **F3** 한 번 더 → 2:56 부근, "무언가 다가온다…" 뒤 3:00에 엘리트 기사가 한 방향에서 나타납니다.
4. **F3**를 두 번 더 → 4:27 부근, 2초 뒤 박쥐 24마리가 화면 밖 원형으로 포위합니다.
5. **F3**를 반복해 8:54 부근 → 5초 경고 뒤 9:00에 게임이 멈추고 카메라가 **방금 생성된 보스**로 갔다가 돌아온 뒤 재개됩니다. 17장 `BossTimer`에 의한 5분 컷신은 더 이상 나오지 않아야 합니다.
6. **F2**로 x8 → `alive` 수가 각 구간의 최대 동시 수를 넘지 않는지 보고(이벤트 적은 예외), 10:00에 결과 화면이 뜨는지 확인합니다.
7. `Balance/Wave_Stage1_threat.csv`의 `threat_hp_per_s` 값이 2단계 표의 위협 열과 일치합니다(8.0, 10.6, 15.4, 16.4, 27.7, 36.8, 40.6, 58.8, 68.9, 63.0 — 30초 간격이므로 같은 값이 두 번씩). 10단계를 마쳤다면 수정 후 표의 값(8.0, 10.6, 15.4, 17.6, 27.7, 36.4, 41.2, 58.9, 69.8, 63.9)과 맞아야 합니다.
8. 단일 전술 완주 테스트(9단계 절차 A)를 4가지 전술 × 3판으로 돌렸고, **단조 지수와 최장 연속 통과 구간**을 표로 적었습니다. 수정 전 값과 수정 후 값이 둘 다 남아 있습니다.
9. `Balance/tactics_*.csv`를 분 단위로 피벗해 **지배 대응 비중**을 계산했고, 지배 대응이 한 종류가 아닙니다.
10. `Wave_Stage1`을 선택했을 때 Console에 R1·R2 경고가 없습니다. 시험 삼아 한 구간의 슬라임 가중치를 크게 올리면 경고가 다시 뜹니다.
11. 폭탄충을 선회 꼬리에서 죽여 보면 예고 원이 **실제 폭발 반경과 같은 크기**로 나타나고, 주술사를 죽인 뒤 플레이어 속도가 즉시 원래대로 돌아옵니다.

## 흔한 실수

1. **증상**: 치트로 시간을 건너뛰면 적이 너무 약하거나 강하다. → **원인**: 시간은 건너뛰었지만 플레이어 레벨은 0:00 그대로. → **해결**: 건너뛴 시간만큼 경험치를 지급하는 치트를 따로 두거나, 빨리감기(F2)로 실제 성장을 거치며 확인합니다. 난이도 판단은 반드시 성장을 거친 상태에서 합니다.
2. **증상**: 적이 줄어들자마자 한꺼번에 우르르 스폰된다. → **원인**: 최대 동시 수에 막힌 동안 스폰 예산이 계속 쌓임. → **해결**: 상한에 막히면 예산을 0으로 버립니다(5단계 코드).
3. **증상**: 레벨업 창을 닫았더니 배속 치트가 풀렸다, 혹은 레벨업 창에서도 시간이 흐른다. → **원인**: 04장 상태 머신과 치트가 둘 다 `Time.timeScale`을 씀. → **해결**: 상태 머신이 복귀할 때 "1"이 아니라 "일시정지 전 값"으로 되돌리게 하거나, 테스트할 때는 치트 배속을 쓰지 않습니다.
4. **증상**: 적이 죽어도 `AliveCount`가 줄지 않아 스폰이 멈춘다. → **원인**: `Enemy`가 여전히 `Destroy(gameObject)`를 호출해 풀 반환 경로를 거치지 않음, 또는 `Died`가 여러 번 발생. → **해결**: 4단계대로 `Destroy`를 지우고, `Health.TakeDamage`가 이미 죽은 상태(`Current <= 0`)에서는 `Died`를 다시 발생시키지 않는지 확인합니다.
5. **증상**: 적이나 보스가 화면 안, 플레이어 근처에서 생긴다. → **원인**: 플레이어 위치를 중심으로 반지름을 잡았는데 카메라가 맵 경계에 막혀 플레이어가 화면 중심이 아님, 또는 고정 반지름이 카메라 줌·화면 비율과 맞지 않음. → **해결**: 5단계 `PickSpawnPoint`처럼 매번 **실제 카메라 사각형** 바깥에서 뽑고 플레이어 최소 거리를 검사합니다. Cinemachine이 렌즈를 제어한다면 실제 카메라의 `orthographicSize`가 갱신되는지 확인하세요.
6. **증상**: 보스 컷신에서 카메라가 엉뚱한 곳(맵 밖 옛 위치)을 비추거나 컷신이 두 번 나온다. → **원인**: 17장 씬 보스·Animation Track·`BossTimer`가 남아 있음. → **해결**: 5-1단계대로 셋을 지우고, 컷신이 `spawner.LastBoss`를 대상으로 삼는지 확인합니다.

7. **증상**: 적 종류를 잔뜩 늘렸는데도 "1분이나 7분이나 똑같다"는 말을 듣는다. → **원인**: 종류는 늘었지만 **역할**은 하나. 체력과 속도만 다른 압박 적 여덟 종은 압박 한 종과 같습니다. → **해결**: 9단계 절차 A로 단조 지수를 재고, 10단계처럼 빠진 역할을 채웁니다. 판단 기준은 "이 적이 플레이어에게 어떤 질문을 던지는가"입니다.
8. **증상**: 주술사를 죽인 뒤부터 플레이어가 계속 느리다. → **원인**: 풀로 돌아갈 때 `OnTriggerExit2D`가 호출되지 않아 감속이 해제되지 않음. → **해결**: `SlowField.OnDisable`에서 반드시 해제합니다(10-3). 같은 함정이 버프·장판·오라 계열 전부에 있습니다. "들어올 때 켜는 것"은 항상 "꺼질 때 끄는 것"과 짝이어야 합니다.
9. **증상**: 전술 전환을 노리고 새 역할을 셋 넣었더니 "뭐가 뭔지 모르겠다"는 반응이 온다. → **원인**: 한 화면에서 읽어야 할 지속형 표시가 세 종류 이상(R4 위반). 소개 4단계도 건너뜀. → **해결**: 동시에 두 종류까지로 제한하고, 새 역할은 이완 구간에서 단독으로 도입합니다. 9:00 보스 구간에서 폭탄충을 뺀 것이 그 예입니다.

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

**4. ★★★ 단조 구간 진단하고 고치기**
2단계 표의 5:00~6:00 구간만 떼어 봅니다(수정 전: 슬라임 20, 박쥐 30, 해골 50 / 스폰율 1.7 / 체력 배율 1.15 / 예상 DPS 50). (a) 이 구간의 역할 구성을 적고 R1·R2 위반 여부를 판정하세요. (b) **위협 비율을 0.70~0.78 안에 유지하면서** 압박 역할을 70% 이하로 낮추는 구성을 하나 만드세요(폭탄충 체력 20, 주술사 체력 80 사용). (c) 그 구성이 실제로 대응을 바꾸는지 확인할 절차를 한 문단으로 쓰세요.

<details><summary>힌트·해설</summary>

(a) 슬라임·박쥐·해골이 모두 압박이므로 압박 100%입니다. R1(한 역할 70% 이하) 위반, R2(2:00 이후 압박 외 역할 1개 이상) 위반입니다. (b) 예시 답: 슬라임 10, 박쥐 25, 해골 30, 폭탄충 20, 주술사 15. 평균 체력 = (10×10 + 6×25 + 30×30 + 20×20 + 80×15) ÷ 100 = 27.5, ×1.15 = 31.62. 스폰율 1.15면 위협 = 36.4, 비율 = 36.4 ÷ 50 = 0.73으로 범위 안입니다. 압박은 65%로 R1·R2를 모두 만족합니다. 스폰율을 원래의 1.7로 두면 위협이 53.8, 비율이 1.08이 되어 긴장 구간을 넘으므로, **역할을 바꾸면 마리 수는 줄여야 한다**는 것이 이 문제의 핵심입니다. 코인 공급도 1.7 × 1.5 = 2.55에서 1.15 × 2.30 = 2.65로 바뀌므로 제단 지갑 표를 다시 계산합니다. (c) 9단계 절차 A를 이 구간에 대해서만 돌립니다. F3으로 4:50 부근까지 이동한 뒤 선회·도주·관통·고정 각각으로 5:00~6:00을 통과해 보고, 무피해로 통과되는 전술이 하나라도 있으면 아직 단조입니다. 절차 B의 CSV에서 5분 행의 지배 대응 비중이 70% 밑으로 내려갔는지도 함께 봅니다.

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

**5. 위협 곡선이 잘 그려진 웨이브 표가 "재미있다"의 증거가 되지 못하는 이유는 무엇이고, 무엇으로 대신 확인하나요?**

<details><summary>모범 답안</summary>

위협 곡선은 **얼마나 어려운가**만 말해 줍니다. 플레이어가 지루해하는 이유는 대개 어려움이 모자라서가 아니라 하는 일이 같아서입니다. 실제로 평균 체력이 같은 두 구성(슬라임 50·박쥐 30·해골 20과 슬라임 35·박쥐 30·해골 5·폭탄충 30)은 위협이 완전히 같지만, 앞의 것은 선회 하나로 전부 통하고 뒤의 것은 통하지 않습니다. 그래서 두 지표를 따로 잽니다. **단조 지수**(단일 전술 하나로 무피해 통과되는 분 수 ÷ 전체 분 수, 기준 0.3 이하 + 같은 전술로 연속 3분 이상 통과 금지)는 "그것만으로 되나"를, **지배 대응 비중**(분마다 최빈 대응이 차지한 시간 비율, 70% 이상인 분이 전체의 30% 이하)은 "실제로 무엇을 했나"를 잽니다. 둘이 어긋나면 단조 지수를 믿습니다.

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
- 난이도와 대응은 다른 축입니다. 위협이 오르는데 대응이 그대로인 **단조 구간**은 단조 지수(단일 전술 완주 테스트)와 지배 대응 비중(`TacticSampler` CSV)으로 혼자서도 진단할 수 있습니다.
- 대응을 바꾸는 것은 적의 수나 체력이 아니라 **역할**(압박·차단·처치 우선·환경 변화)입니다. 역할은 `EnemyData`의 데이터로 두고, R1(한 역할 70% 이하)·R2(2:00 이후 압박 외 1개 이상)를 `OnValidate`가 검사하게 합니다. 차단·환경 변화는 진행 방향 **앞**에 스폰해야 경로를 끊습니다.
- 전술 전환을 요구할수록 읽을 것이 늘어납니다. 상시 표시·사전 예고(반경 ÷ 이동속도로 검산)·동시 2종 제한(R4)이 공정한 죽음 절과 짝을 이룹니다.
- 고친 뒤에는 **같은 절차로 재측정**합니다. 문제가 둘이면 급한 것 하나만 고치고 되돌릴 수 있게 태그를 남깁니다(21장의 반복 루프와 같은 규칙).

## 더 읽을거리

- Unity 매뉴얼 — ObjectPool: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity 매뉴얼 — ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Jenova Chen, "Flow in Games" (MFA 논문, 2006) — 몰입 채널을 게임 설계에 적용한 대표 자료
- Game Maker's Toolkit, 닌텐도의 레벨 디자인(기승전결 소개) 관련 영상
- Jesse Schell, 「The Art of Game Design」 — 난이도와 흥미 곡선(Interest Curve) 장
