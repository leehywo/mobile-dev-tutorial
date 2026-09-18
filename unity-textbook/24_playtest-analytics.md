# 24. 플레이테스트와 애널리틱스

> **이 장에서 배울 것**
> - 플레이테스트의 종류와 진행 규칙(설명·도움 금지, Think-aloud)을 설명하고 5인 테스트 계획서를 작성한다
> - 피드백을 "증상"과 "처방"으로 나누어 해석한다
> - "무엇을 알고 싶은가"에서 출발해 이벤트 사양(이름·파라미터·네이밍 규칙)을 설계한다
> - SDK 없이도 동작하는 `Analytics` 정적 래퍼와 로컬 JSONL 로거를 구현하고, 23장까지의 실제 코드에 이벤트를 심어 사망 분포·선택 비율·순차 퍼널을 집계한다
> - 세션·날짜·판의 정의를 정하고 퍼널과 리텐션(D1/D7)을 정의대로 계산하며, 동의·철회·삭제 흐름을 구현한다
> - **"몇 판째에 새로움이 끝나는가"**(콘텐츠 고갈)와 **빌드 다양성**을 재는 이벤트·지표를 설계하고 집계 코드를 만든다
> - 증상 → 진단 → 수정 → **재측정**까지 한 바퀴를 돌려, 바뀐 것과 **바뀌지 않은 것**을 함께 기록한다
>
> **선수 장**: 10, 21, 22, 23 · **예상 시간**: 8~9시간 (실제 테스트 진행 시간 제외) · **코인 러시 진행**: 이벤트 로그(로컬 JSONL, 판 단위 `run_id`), 이벤트 사양 표, 로그 집계 에디터 도구, 신규 경험·빌드 다양성 지표, 5인 플레이테스트 계획서와 분석 보고서, 0.4.2 수정 후 재측정 보고서

## 왜 필요한가

23장의 시뮬레이터는 "기준 가정에서 클리어율 29%, 초보 가정이면 0%, 숙련 가정이면 59%"라고 말합니다. 어느 가정이 사람에 가까운지는 시뮬레이터 스스로 알 수 없습니다. 그 밖에도 시뮬레이터가 절대 알려주지 못하는 것들이 있습니다.

```
- 사람은 레벨업 창의 설명을 읽는가? 아니면 제일 왼쪽을 누르는가?
- 코인 제단을 "보기는" 하는가? 봤다면 왜 안 샀는가?
- 3분에 죽은 사람이 "한 판 더"를 누르는가, 게임을 끄는가?
- 조작이 불편하다는 사람은 무엇이 불편한가?
- 4판째에도 처음 보는 것이 남아 있는가, 아니면 다 본 게임을 반복하고 있는가?
- 매 판 다른 빌드로 노는가, 늘 같은 세 장을 고르는가?
```

그리고 개발자 본인은 이 질문에 답할 수 없는 유일한 사람입니다. 규칙을 모두 알고, 어디서 적이 나오는지 외우고 있으니까요. 이 장은 두 도구를 만듭니다. **사람을 관찰하는 플레이테스트**(왜 그렇게 하는가)와 **행동을 세는 애널리틱스**(얼마나 많이 그렇게 하는가)입니다. 둘은 서로의 빈틈을 채웁니다.

## 개념

### 플레이테스트의 종류

| 종류 | 대상 | 규모 | 알 수 있는 것 | 모르는 것 | 코인 러시 시점 |
|---|---|---|---|---|---|
| 자기 테스트 | 개발자 | 1명 | 버그, 명백한 수치 오류 | 첫인상, 이해도 | 매일 |
| 지인 테스트 | 친구·가족 | 2~5명 | 치명적인 이해 불가 지점 | 진짜 재미 (예의상 칭찬함) | 그레이박스 직후 |
| 낯선 타깃 테스트 | 장르를 좋아하는 모르는 사람 | 5~10명 | 첫 10분 경험, 이탈 지점, 진짜 반응 | 통계적 경향 | 버티컬 슬라이스 |
| 대규모 테스트 | 공개 모집 | 수십~수천 명 | 지표(리텐션·퍼널), 밸런스 분포 | "왜"의 맥락 | 데모·Steam Playtest |

사용성 연구 분야에서 자주 인용되는 경험칙은 **"소수(약 5명)로 주요 문제 대부분을 찾는다"**입니다. 같은 사람을 15명 한 번에 부르는 것보다 5명씩 세 번(테스트 → 수정 → 테스트)이 낫습니다.

### 진행 규칙

```
1. 설명하지 않는다    "이동만 하면 돼요"도 금지. 스토어 페이지 수준의 한 문장만 허용
2. 도와주지 않는다    막혀도 기다린다. 막힌 지점이 곧 데이터
3. 변명하지 않는다    "아 그거 아직 안 만든 거예요" 금지
4. 말하며 플레이 요청 (Think-aloud) "생각나는 걸 전부 소리 내서 말해주세요"
5. 녹화한다          화면 + 음성 (+ 가능하면 얼굴·손). 동의를 받고
6. 질문은 끝나고     플레이 중 질문은 행동을 바꾼다. 침묵이 길면 "지금 무슨 생각하세요?"만
```

Think-aloud는 어색해서 사람들이 곧 말을 멈춥니다. 시작 전에 "이 컵을 보고 생각나는 걸 말해보세요" 같은 연습을 30초 시키면 훨씬 잘 됩니다.

### 관찰 기록 템플릿

진행자는 **플레이어가 아니라 행동**을 기록합니다. 해석은 나중에 합니다.

```
테스터 ID: P3   날짜: 2026-10-02   빌드: 0.4.1   기기: PC/패드
┌───────┬──────────────────────────────┬───────────────────────┬──────┐
│ 시각   │ 관찰한 행동 (사실)              │ 발화 (그대로 인용)       │ 태그  │
├───────┼──────────────────────────────┼───────────────────────┼──────┤
│ 00:12 │ 3초간 움직이지 않음              │ "공격 버튼이 뭐지?"       │ 온보딩 │
│ 02:05 │ 제단 옆을 지나감, 멈추지 않음      │ (없음)                  │ 제단  │
│ 03:01 │ 엘리트 등장 후 벽 쪽으로 도망       │ "헐 뭐야 저거"           │ 난이도 │
└───────┴──────────────────────────────┴───────────────────────┴──────┘
```

태그를 미리 정해두면(온보딩, 조작, 난이도, 제단, 레벨업, UI, 버그) 5명의 기록을 합칠 때 빠릅니다.

### 설문: 무엇을 어떻게 묻는가

플레이 직후 5분 설문을 합니다. 닫힌 질문(척도)과 열린 질문을 섞되, **유도하지 않는** 문장으로 씁니다.

| 나쁜 질문 | 문제 | 좋은 질문 |
|---|---|---|
| "제단 기능 재밌었죠?" | 유도, 예/아니오 | "게임에서 기억나는 결정이 있다면 무엇이었나요?" |
| "조작이 불편했나요?" | 부정 암시 | "조작에서 원하는 대로 안 된 순간이 있었나요? 언제였나요?" |
| "뭘 추가하면 좋을까요?" | 처방을 요구 (플레이어는 설계자가 아님) | "가장 답답했던 순간은 언제였나요?" |

코인 러시 설문(완성본은 실습 6단계)에는 다음 두 질문을 항상 넣습니다.

- **"이 게임을 친구에게 추천할 가능성은 0~10점 중 몇 점인가요? 이유는?"** — 순추천지수(NPS)에서 쓰는 형식입니다. 5명으로 점수를 통계 내는 의미는 없고, **이유**를 듣는 것이 목적입니다.
- **"지금 한 판 더 하실래요?"** — 설문 마지막에 실제로 묻고, 행동(정말 하는지)을 기록합니다. 말보다 행동이 정직합니다.

### 피드백 해석: 증상 vs 처방

플레이어의 말은 **증상 보고**로는 정확하지만 **처방**으로는 대개 틀립니다.

| 플레이어의 말 | 증상 (믿을 것) | 플레이어의 처방 (의심할 것) | 설계자의 가능한 처방 |
|---|---|---|---|
| "적이 너무 세요, 약하게 해주세요" | 특정 시점에 무력감 | 적 약화 | 그 시점 직전의 성장 부족 → 경험치 곡선, 또는 위협 예고 부족 |
| "공격 버튼 넣어주세요" | 통제감 부족 | 수동 공격 | 자동 공격의 피드백(타격음·숫자)이 약함 → 16장 연출 |
| "제단 필요 없는 것 같아요" | 제단의 가치를 못 느낌 | 제단 삭제 | 가격·효과가 안 보임(UI), 또는 이월 가치 설명 부족 |
| "맵이 좁아요" | 답답함, 반복감 | 맵 확장 | 적 구성 단조로움, 이동 동기 부족 |

규칙: **"여러 명이 같은 증상을 말하면 문제는 확실히 있다. 처방은 내가 정한다."**

### 테스트 배포 채널

| 채널 | 플랫폼 | 특징 | 주의 (정책은 바뀔 수 있으니 공식 문서 확인) |
|---|---|---|---|
| Steam Playtest | PC | 본 게임과 연결된 별도 무료 앱. 참가 신청자 중 인원을 조절해 입장 | 스토어 페이지가 있어야 함. 대규모 테스트에 적합 |
| itch.io | PC·웹 | 비공개·제한 공개 페이지, 다운로드 키 배포 | 빠르고 무료. 지인·커뮤니티 테스트에 적합 |
| TestFlight | iOS | 내부 테스터(팀원, 최대 100명), 외부 테스터(최대 10,000명, 베타 심사 필요) | 빌드 유효기간 90일 |
| Google Play 내부 테스트 | Android | 최대 100명, 심사 없이 빠르게 배포 | 개인 개발자 신규 계정은 프로덕션 출시 전 비공개 테스트 요건(일정 인원·기간)이 있음 |

### 애널리틱스: 질문에서 이벤트로

애널리틱스의 가장 흔한 실패는 "일단 다 로그로 남기자"입니다. 쌓인 데이터는 많은데 답할 수 있는 질문이 없습니다. 순서를 거꾸로 합니다.

```
① 알고 싶은 질문     "플레이어는 주로 언제, 무엇에 죽는가?"
② 필요한 측정값     사망 시각, 사망 원인, 그때 레벨
③ 이벤트 설계       run_end { duration_s, cause, level }
④ 판단 기준 (미리)  "한 분에 사망 30% 이상이 몰리면 웨이브 조정"
```

④를 미리 정하는 이유는 21장 그레이박스와 같습니다. 데이터를 본 뒤 기준을 정하면 무엇이든 해석할 수 있습니다. 또한 **이벤트는 출시 전에 심어야 합니다.** 나중에 추가하면 과거 데이터는 영원히 없습니다.

### 이벤트 네이밍 규칙

여러 분석 서비스의 제약(이름 길이, 허용 문자)을 동시에 만족하도록 **보수적인 규칙**을 정합니다.

```
- 소문자 snake_case, 영문자로 시작, 영문·숫자·밑줄만, 40자 이하
- 형식: 대상_동작 (과거형 대신 명사형)       run_start, run_end, upgrade_purchase
- 파라미터 이름도 같은 규칙, 단위는 접미사     duration_s, price_coins
- 이벤트 이름에 값을 넣지 않는다              level_up_12 (X) → level_up { level: 12 } (O)
- 한 번 출시한 이름은 바꾸지 않는다           바꾸면 과거 데이터와 끊긴다. 새 이름 + 기존 병행
- 공통 필드는 래퍼가 자동으로 붙인다          ts, session_id, user_id, app_version, platform
```

Firebase 등 각 서비스에는 예약어, 이벤트당 파라미터 수 같은 추가 제한이 있으니 연동할 서비스의 공식 문서를 확인하세요.

### 퍼널과 리텐션

**퍼널**은 순서가 있는 단계에서, **같은 사용자가 이전 단계를 거친 뒤** 다음 단계에 도달한 비율입니다. 단계별 이벤트 수를 따로 세서 나열한 것은 퍼널이 아닙니다(단계를 건너뛴 사용자, 순서가 뒤바뀐 기록이 섞입니다). 계산 규칙은 세 가지입니다.

```
1. 사용자별로 이벤트를 시각순 정렬하고, 단계 k는 단계 k-1이 일어난 "이후"의 기록만 인정한다
2. 모든 단계를 "첫 실행 후 관측 기간(예: 7일) 안"으로 제한하고, 관측 기간을 다 채우지 못한 신규 사용자는 제외한다
3. 순서가 강제되지 않는 행동(예: 영구 강화 구매)은 순차 단계에 넣지 말고 "분기"로 따로 센다
```

코인 러시의 첫 실행 퍼널 예시입니다(가상 수치, 관측 기간 7일).

| 단계 | 이벤트 (조건) | 도달 사용자 | 첫 단계 대비 | 직전 단계 대비 |
|---|---|---|---|---|
| 1. 첫 실행 | `session_start` (first_open) | 1,000 | 100% | — |
| 2. 첫 판 시작 | `run_start` (run_index=1) | 920 | 92% | 92% |
| 3. 첫 레벨업 선택 | `level_up` (run_index=1) | 880 | 88% | 96% |
| 4. 첫 판 종료 | `run_end` (run_index=1) | 850 | 85% | 97% |
| 5. 두 번째 판 시작 | `run_start` (run_index=2) | 620 | 62% | **73%** |
| 분기: 4 이후 영구 강화 구매 | `upgrade_purchase` | 510 / 850 | — | 60% |

"직전 단계 대비"에서 가장 크게 떨어지는 곳(4 → 5, 73%)이 가장 먼저 볼 곳입니다. 분기를 함께 보면 원인 가설이 좁혀집니다. 첫 판 종료자 중 영구 강화를 산 사람이 60%라면 "결과 화면에서 강화 화면으로 가는 길이 안 보이는가", "강화를 산 사람과 안 산 사람의 두 번째 판 시작률이 다른가"를 이어서 봅니다. 영구 강화를 순차 단계 5로 두면 강화를 사지 않고 바로 두 번째 판을 시작한 사람이 퍼널에서 사라져 이탈로 잘못 보입니다.

**리텐션 D1/D7**은 가장 많이 쓰는 정의가 다음과 같습니다(서비스마다 세부 정의가 다르니 비교할 때는 같은 정의끼리 비교합니다).

```
Dn 리텐션 = (Day 0에 처음 실행한 사용자 중, 정확히 n일째 날에 한 번 이상 "활동"한 사용자 수)
          ÷ (Day 0에 처음 실행한 사용자 수)
"날"은 보통 사용자 기준 달력 날짜(또는 첫 실행 후 24시간 단위)
```

계산하기 전에 코인 러시의 정의를 고정합니다(2단계 코드가 이대로 구현합니다).

| 용어 | 정의 |
|---|---|
| 활동 | `session_start` 기록 |
| 세션 | 앱 실행, 동의 직후, **30분 이상 백그라운드에 있다가 돌아온 순간** 새로 시작. 앱을 끄지 않고 다음 날 다시 연 모바일 사용자도 활동으로 잡힘 |
| 날 | `session_start`의 `local_date`(기기 현지 달력 날짜). `ts`(UTC) 날짜와 다를 수 있음 |
| 판 | `GameStateMachine.StartGame`에서 시작해 정산에서 끝나는 한 번. 레벨업 복귀·부활은 새 판이 아님. 판 안 이벤트는 같은 `run_id` |

계산 예 (가상 데이터, 10월 1일 첫 실행 코호트 200명):

| 날짜 | 그날 실행한 코호트 사용자 | 리텐션 |
|---|---|---|
| 10/1 (D0) | 200 | 100% |
| 10/2 (D1) | 64 | 64 ÷ 200 = **32%** |
| 10/8 (D7) | 18 | 18 ÷ 200 = **9%** |

D1은 첫인상과 온보딩, D7은 메타 루프(다시 올 이유)의 건강을 보여주는 신호로 주로 읽습니다. Steam 유료 게임에서는 리텐션보다 **플레이 시간 분포와 환불 전 이탈**이 더 중요할 수 있습니다.

### 새로움이 끝나는 지점: 콘텐츠 고갈 지표

23장은 **봇의 지갑**으로 "몇 판째에 살 것이 없어지는가"를 쟀습니다. 사람 쪽에는 그것과 짝이 되는 질문이 있습니다 — **"몇 판째에 볼 것이 없어지는가"**. 서바이버라이크를 다시 켜는 이유는 대개 "다음 판은 다르게 풀린다"는 기대이므로, 이 기대가 언제 마르는지 재지 않으면 "출시 2주 뒤 플레이 시간이 급감했다"를 사후에 알게 됩니다.

세 지표로 봅니다. 앞의 둘은 이 장에서 이벤트를 새로 심어야 하고, 셋째는 23장에서 정의한 지표를 **이미 있는 `level_up`·`shrine_visit` 로그로** 계산합니다.

| 지표 | 정의 | 필요한 이벤트 | 판단 기준 (코인 러시) | 표본 요건 |
|---|---|---|---|---|
| **판 수별 진행률** | n번째 판을 시작한 사용자 중 n+1번째 판을 시작한 비율 | `run_start`(`run_index`) | 어느 한 판에서 **70% 미만**으로 떨어지면 그 판의 경험을 본다 | 수백 명. **대면 테스트로는 못 잰다** |
| **판당 신규 경험 비율** | 그 판에서 처음 본 것의 수 ÷ 그 판까지 누적으로 처음 본 것의 수 | `first_seen`, `run_end`(`new_seen`) | **3판째 20% 미만**이면 새 콘텐츠를 만들기 전에 조합(빌드)으로 새로움을 만들 수 있는지 먼저 본다 | 5명부터 경향이 보임 |
| **빌드 유사도** | 같은 사람의 서로 다른 판 빌드 벡터 코사인 유사도 중앙값 (23장 정의) | `level_up`(`choice`), `shrine_visit`(`purchased`, `choice`) | **0.85 이상**이면 매 판 같은 게임 | 1인당 3판 이상 |

```
판당 신규 경험 비율(판 n) = (판 n에서 처음 본 것의 수) ÷ (판 1..n에서 처음 본 것의 누적 수)
  → 1판은 정의상 항상 100%. 2판째 값이 곧 "첫 판이 새로움의 몇 %를 써 버렸는가"
```

"처음 본 것"의 목록은 미리 정해 둡니다. 코인 러시는 **적 종류(8 — 22장 10단계에서 폭탄충·주술사가 늘어 6종에서 8종이 됐습니다)**, **레벨업·제단 카드 종류(7)**, **영구 강화 레벨(3종 × 10)** 셋입니다. 목록에 없는 것을 나중에 끼워 넣으면 과거 판의 분모가 달라져 비교가 끊깁니다(이벤트 이름을 바꾸지 않는 것과 같은 이유).

**표본의 한계를 미리 적어 둡니다.** 대면 5인 테스트는 진행 시간이 정해져 있어 "몇 판째에 그만두는가"를 볼 수 없습니다. 45분짜리 세션에서 4판을 한 것은 재미의 신호가 아니라 **일정의 결과**입니다. 그래서 판 수별 진행률은 데모·출시 로그에서만 쓰고, 대면 테스트에서는 신규 경험 비율과 빌드 유사도만 봅니다. 데모 단계의 재방문·완주 판정이 35장 게이트 L3이고, 그 숫자를 만드는 것이 여기서 심는 이벤트입니다.

### 서비스 선택과 래퍼

| 서비스 | 특징 | 코인 러시에서 |
|---|---|---|
| Unity Analytics (Unity Gaming Services) | Unity 통합, 대시보드·퍼널 제공 | 모바일판 후보 |
| Firebase Analytics | 모바일에 강함, Remote Config·Crashlytics와 한 묶음 | 모바일판 후보 (25장 Remote Config와 함께) |
| GameAnalytics | 게임 특화 지표, 무료 요금제 | PC·모바일 공통 후보 |
| 로컬 JSONL 파일 | 서버 없음, 플레이테스트용 | 지금 구현 |

어떤 서비스를 고르든 **게임 코드가 SDK를 직접 호출하지 않게** 합니다. 게임 코드는 `Analytics.Track("run_end", ...)`만 부르고, 실제 전송은 백엔드 구현이 맡습니다. SDK를 바꾸거나 둘을 동시에 쓰거나 테스트 중엔 파일로만 남기는 것이 한 줄 변경이 됩니다(JS: 앱이 `track()` 함수만 쓰고 Segment·GA 어댑터를 갈아 끼우는 구조와 같습니다). **SDK별 호출 코드는 버전마다 바뀌므로 각 서비스의 공식 문서를 따르세요.**

### 개인정보와 동의

- 수집 전에 **무엇을 왜 수집하는지 알리고**, 법이 요구하는 경우 **동의**를 받습니다. EU(GDPR)는 필수적이지 않은 분석·광고 목적 처리에 동의를 요구하는 것이 일반적이고, 한국도 개인정보 보호법에 따른 고지·동의 의무가 있습니다(구체 판단은 28장과 전문가 확인).
- **최소 수집**: 코인 러시는 이름·이메일·위치를 수집하지 않습니다. 사용자 ID는 설치 시 만든 무작위 값입니다. 그래도 기기에 고정된 식별자는 개인정보로 볼 수 있으니 고지 대상입니다.
- 스토어 제출 시 **Apple App Privacy 항목, Google Play 데이터 보안 양식**에 수집 내용을 적어야 합니다. 서드파티 SDK가 수집하는 것도 포함입니다.
- 동의 전에는 수집하지 않고, 설정 화면에서 **언제든 철회**할 수 있게 합니다.

## 실습: 코인 러시에 적용하기

### 1단계: 이벤트 사양 표

`Docs/analytics-spec.md`에 먼저 표를 만듭니다. 코드보다 표가 먼저입니다.

| 이벤트 | 발생 시점 | 파라미터 (타입) | 답하려는 질문 | 판단 기준 (예시) |
|---|---|---|---|---|
| `session_start` | 동의 후 앱 시작·동의 직후·30분 이상 백그라운드 후 복귀 | `first_open`(bool), `reason`(string: launch/consent/resume), `local_date`(string) | 리텐션 D1/D7 계산의 기준 | D1 25% 미만이면 온보딩 재검토 |
| `run_start` | 판 시작 (`StartGame`에서만) | `meta_damage_lv`, `meta_hp_lv`, `meta_magnet_lv`(int) | 몇 판째에 이탈하는가 | 2판째 시작률 60% 미만이면 결과 화면 개선 |
| `run_end` | 정산 (사망·클리어·중도 종료) | `duration_s`(float), `cause`(string: 적 에셋 이름/`clear`/`quit`), `level`(int), `coins_collected`(int), `coins_banked`(int), `shrine_purchases`(int), `new_seen`(int: 이 판에서 처음 본 것의 수) | 언제 무엇에 죽는가, 실제 클리어율, 판당 신규 경험 | 한 분에 사망 30% 이상 집중 시 웨이브 조정. 23장 시뮬레이터 계수 보정 |
| `level_up` | 레벨업 선택 완료 | `level`(int), `choice`(string), `offered`(string, 쉼표 구분) | 선택이 한쪽으로 쏠리는가, 판마다 다른 빌드가 나오는가 | 23장 기준: 조건부 선택률 70% 이상 = 사실상 1택 → 그 강화의 **가치** 조정. 빌드 유사도 중앙값 0.85 이상 = 빌드 수렴 |
| `shrine_visit` | 제단 창 닫힘 | `shrine_index`, `price`, `wallet`(int), `affordable`(bool), `hp_ratio`, `dwell_s`(float), `purchased`(bool), `choice`, `offered`(string) | 제단 결정이 상황에 따라 바뀌는가 | 21장 기준: 살 수 있었던 방문에서 구매·모으기를 모두 한 참가자 4/5 미만이면 조정 |
| `upgrade_purchase` | 영구 강화 구매 | `upgrade_id`(string), `new_level`(int), `cost`(int), `bank_after`(int) | 메타 진행 속도가 목표와 맞는가 | 23장 캠페인 예측과 ±50% 이상 차이 시 계수 보정 → 비용 재조정 |
| `tutorial_step` | 온보딩 단계 첫 완료 (설치당 1회) | `step`(int), `step_name`(string: first_move/first_level_up/upgrade_shop_open/first_upgrade_purchase) | 온보딩 어디서 이탈하는가 | 직전 대비 90% 미만 단계 수정 |
| `first_seen` | 미리 정한 목록의 무언가를 **처음** 본 순간 (설치당 항목별 1회) | `kind`(string: enemy/upgrade/unlock), `id`(string: 에셋 이름 또는 `damage_4` 같은 강화 레벨) | 몇 판째에 새로움이 끝나는가 | 3판째 신규 경험 비율 20% 미만이면 빌드 다양성(23장)부터 점검 |

모든 이벤트에는 래퍼가 공통 필드(`ts`, `session_id`, `user_id`, `app_version`, `platform`)를 붙이고, 판 안에서 일어난 이벤트에는 `run_id`, `run_index`, `run_time_s`(판 경과 초)를 추가로 붙입니다.

### 2단계: Analytics 정적 래퍼

세 파일로 나눕니다. 먼저 백엔드 인터페이스입니다. 파일: `Assets/_CoinRush/Scripts/Analytics/IAnalyticsBackend.cs`

```csharp
using System.Collections.Generic;

/// <summary>실제 전송 담당. 파일·Firebase·GameAnalytics 등은 이 인터페이스를 구현한다.</summary>
public interface IAnalyticsBackend
{
    /// <param name="eventName">검증된 이벤트 이름</param>
    /// <param name="props">공통 필드를 포함한 파라미터 (SDK 백엔드용)</param>
    /// <param name="jsonLine">같은 내용을 한 줄 JSON으로 직렬화한 것 (파일 백엔드용)</param>
    void Send(string eventName, IReadOnlyList<KeyValuePair<string, object>> props, string jsonLine);
    void Flush();

    /// <summary>동의 철회: 아직 기록·전송하지 않은 대기 데이터를 버린다</summary>
    void DiscardPending();

    /// <summary>사용자 요청 시 이미 저장·전송한 데이터 삭제 (SDK는 서비스의 삭제 API를 따른다)</summary>
    void DeleteStoredData();
}
```

다음은 래퍼 본체입니다. 판 안에서 일어난 이벤트를 판 단위로 묶기 위해 `run_id`·`run_index`·`run_time_s`를 **공통 필드**로 자동으로 붙이고, 모바일에서 앱을 끄지 않고 다음 날 다시 여는 경우를 위해 **포그라운드 복귀 시 새 세션**을 시작합니다. 파일: `Assets/_CoinRush/Scripts/Analytics/Analytics.cs`

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

public enum AnalyticsConsent { Unknown = -1, Denied = 0, Granted = 1 }

public static class Analytics
{
    private const string ConsentPrefKey = "analytics_consent";
    private const string UserIdPrefKey = "analytics_user_id";
    public const double NewSessionAfterBackgroundSeconds = 30 * 60;   // 30분 이상 백그라운드면 새 세션
    private static readonly Regex NameRule = new Regex("^[a-z][a-z0-9_]{0,39}$");

    private static readonly List<IAnalyticsBackend> backends = new List<IAnalyticsBackend>();
    private static readonly List<KeyValuePair<string, object>> propsBuffer = new List<KeyValuePair<string, object>>(16);
    private static readonly StringBuilder json = new StringBuilder(256);
    private static bool initialized, firstOpenPending;
    private static Func<float> runElapsed;

    public static string UserId { get; private set; }
    public static string SessionId { get; private set; }
    public static string RunId { get; private set; }
    public static int RunIndex { get; private set; }
    public static AnalyticsConsent Consent { get; private set; } = AnalyticsConsent.Unknown;

    // 도메인 리로드를 끈 Enter Play Mode 설정에서도 정적 상태가 남지 않게 초기화
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStatics()
    {
        backends.Clear();
        initialized = false;
        ClearRun();
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void Initialize()
    {
        if (initialized) return;
        initialized = true;

        UserId = PlayerPrefs.GetString(UserIdPrefKey, "");
        firstOpenPending = string.IsNullOrEmpty(UserId);
        if (firstOpenPending)
        {
            UserId = Guid.NewGuid().ToString("N");   // 개인 정보가 아닌 무작위 설치 ID
            PlayerPrefs.SetString(UserIdPrefKey, UserId);
            PlayerPrefs.Save();
        }
        Consent = (AnalyticsConsent)PlayerPrefs.GetInt(ConsentPrefKey, (int)AnalyticsConsent.Unknown);

        backends.Add(new JsonlFileBackend(Path.Combine(Application.persistentDataPath, "analytics")));
        // 모바일판에서는 여기서 SDK 백엔드를 추가한다 (예: #if UNITY_ANDROID || UNITY_IOS)

        var host = new GameObject("[Analytics]");
        UnityEngine.Object.DontDestroyOnLoad(host);
        host.AddComponent<AnalyticsLifecycle>();

        StartSession("launch");
    }

    public static void AddBackend(IAnalyticsBackend backend) => backends.Add(backend);

    /// <summary>동의 UI·설정 화면에서 호출.</summary>
    public static void SetConsent(bool granted)
    {
        AnalyticsConsent previous = Consent;
        Consent = granted ? AnalyticsConsent.Granted : AnalyticsConsent.Denied;
        PlayerPrefs.SetInt(ConsentPrefKey, (int)Consent);
        PlayerPrefs.Save();

        if (!granted)
        {
            // 철회: 버퍼에 남은 이벤트를 파일·서버로 내보내지 않고 버린다 → 이후 Flush에도 기록되지 않음
            foreach (IAnalyticsBackend backend in backends) backend.DiscardPending();
            return;
        }
        if (previous != AnalyticsConsent.Granted) StartSession("consent");   // 동의한 순간부터 세션 시작
    }

    /// <summary>설정 화면의 "수집된 기록 삭제" 버튼. 철회와 별개로, 이미 저장된 데이터를 지운다.</summary>
    public static void DeleteStoredData()
    {
        foreach (IAnalyticsBackend backend in backends)
        {
            backend.DiscardPending();
            backend.DeleteStoredData();
        }
    }

    /// <summary>AnalyticsLifecycle이 포그라운드 복귀 때 호출</summary>
    public static void OnResumed(double backgroundSeconds)
    {
        if (backgroundSeconds >= NewSessionAfterBackgroundSeconds) StartSession("resume");
    }

    private static void StartSession(string reason)
    {
        SessionId = Guid.NewGuid().ToString("N");
        if (Consent != AnalyticsConsent.Granted) return;   // 동의 전에는 세션 ID만 준비

        bool firstOpen = firstOpenPending;
        firstOpenPending = false;
        // 리텐션의 "날"은 기기 현지 달력 날짜로 정의 (ts는 UTC이므로 따로 기록)
        Track("session_start", ("first_open", firstOpen), ("reason", reason),
              ("local_date", DateTime.Now.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)));
    }

    /// <summary>판 시작 시 설정 → 이후 모든 이벤트에 run_id, run_index, run_time_s가 붙는다</summary>
    public static void SetRun(string runId, int runIndex, Func<float> elapsedSeconds)
    {
        RunId = runId;
        RunIndex = runIndex;
        runElapsed = elapsedSeconds;
    }

    public static void ClearRun()
    {
        RunId = null;
        RunIndex = 0;
        runElapsed = null;
    }

    public static void Track(string eventName, params (string key, object value)[] props)
    {
        if (Consent != AnalyticsConsent.Granted) return;

        if (!NameRule.IsMatch(eventName))
        {
            Debug.LogError($"[Analytics] 이벤트 이름 규칙 위반: {eventName}");
            return;
        }

        propsBuffer.Clear();
        propsBuffer.Add(new KeyValuePair<string, object>("name", eventName));
        propsBuffer.Add(new KeyValuePair<string, object>("ts", DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture)));
        propsBuffer.Add(new KeyValuePair<string, object>("session_id", SessionId));
        propsBuffer.Add(new KeyValuePair<string, object>("user_id", UserId));
        propsBuffer.Add(new KeyValuePair<string, object>("app_version", Application.version));
        propsBuffer.Add(new KeyValuePair<string, object>("platform", Application.platform.ToString()));
        if (RunId != null)
        {
            propsBuffer.Add(new KeyValuePair<string, object>("run_id", RunId));
            propsBuffer.Add(new KeyValuePair<string, object>("run_index", RunIndex));
            if (runElapsed != null) propsBuffer.Add(new KeyValuePair<string, object>("run_time_s", runElapsed()));
        }
        foreach ((string key, object value) in props)
        {
            if (!NameRule.IsMatch(key)) { Debug.LogError($"[Analytics] {eventName}: 파라미터 이름 규칙 위반 {key}"); continue; }
            propsBuffer.Add(new KeyValuePair<string, object>(key, value));
        }

        json.Clear().Append('{');
        for (int i = 0; i < propsBuffer.Count; i++)
        {
            if (i > 0) json.Append(',');
            AppendString(propsBuffer[i].Key);
            json.Append(':');
            AppendValue(propsBuffer[i].Value);
        }
        json.Append('}');
        string line = json.ToString();

        foreach (IAnalyticsBackend backend in backends)
            backend.Send(eventName, propsBuffer, line);

#if UNITY_EDITOR
        Debug.Log($"[Analytics] {line}");
#endif
    }

    public static void Flush()
    {
        if (Consent != AnalyticsConsent.Granted) return;   // 철회 뒤 종료·백그라운드에서도 기록하지 않음
        foreach (IAnalyticsBackend backend in backends) backend.Flush();
    }

    // ---------- 최소 JSON 직렬화 (JsonUtility는 임의 키-값을 직렬화하지 못한다) ----------

    private static void AppendValue(object value)
    {
        switch (value)
        {
            case null: json.Append("null"); break;
            case bool b: json.Append(b ? "true" : "false"); break;
            case int n: json.Append(n.ToString(CultureInfo.InvariantCulture)); break;
            case long n: json.Append(n.ToString(CultureInfo.InvariantCulture)); break;
            case float f: json.Append(f.ToString("0.###", CultureInfo.InvariantCulture)); break;
            case double d: json.Append(d.ToString("0.###", CultureInfo.InvariantCulture)); break;
            default: AppendString(value.ToString()); break;   // string, enum 등
        }
    }

    private static void AppendString(string s)
    {
        json.Append('"');
        foreach (char c in s)
        {
            switch (c)
            {
                case '"': json.Append("\\\""); break;
                case '\\': json.Append("\\\\"); break;
                case '\n': json.Append("\\n"); break;
                case '\r': json.Append("\\r"); break;
                case '\t': json.Append("\\t"); break;
                default:
                    if (c < 0x20) json.Append("\\u").Append(((int)c).ToString("x4"));
                    else json.Append(c);
                    break;
            }
        }
        json.Append('"');
    }
}
```

몇 가지 설계 이유입니다.

- `Track`은 `params (string key, object value)[]`를 받아 호출이 짧습니다. 값이 `object`라 박싱 할당이 생기지만, 이벤트는 판 시작·종료·레벨업처럼 **드물게** 발생하므로 괜찮습니다. 매 프레임 호출하는 곳에는 쓰지 마세요(02장).
- 소수는 `InvariantCulture`로 씁니다. 기기 언어가 독일어 등이면 `12,5`로 찍혀 JSON이 깨집니다.
- 이벤트 이름 검증에 실패하면 전송하지 않고 에러를 냅니다. 잘못된 이름으로 쌓인 데이터는 나중에 합치기 어렵습니다.
- **세션 정의**: 앱 실행, 동의 직후, **30분 이상 백그라운드에 있다가 돌아온 순간**에 `session_start`를 기록합니다. 모바일 사용자는 앱을 끄지 않고 다음 날 다시 여는 일이 흔해서, 프로세스 시작에만 기록하면 그 재방문이 D1/D7에서 사라집니다.
- **날짜 정의**: `ts`는 UTC, 리텐션 계산용 날짜는 `local_date`(기기 현지 달력 날짜)입니다. 한국 사용자가 오전 8시에 한 플레이는 UTC로는 전날입니다.

### 3단계: 로컬 JSONL 백엔드와 생명주기

JSONL(JSON Lines)은 한 줄에 JSON 객체 하나를 쓰는 형식입니다. 추가 쓰기가 쉽고, 파일이 중간에 잘려도 앞줄은 멀쩡합니다(단, 읽는 쪽이 깨진 마지막 줄을 건너뛰어야 합니다 — 5단계). 파일: `Assets/_CoinRush/Scripts/Analytics/JsonlFileBackend.cs`

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

/// <summary>persistentDataPath/analytics/events_yyyyMMdd.jsonl 에 기록. 플레이테스트용.</summary>
public class JsonlFileBackend : IAnalyticsBackend
{
    private const int FlushThreshold = 20;
    private static readonly UTF8Encoding Utf8NoBom = new UTF8Encoding(false);

    private readonly string directory;
    private readonly StringBuilder pending = new StringBuilder(4096);
    private int pendingCount;

    public JsonlFileBackend(string directory)
    {
        this.directory = directory;
        Directory.CreateDirectory(directory);
    }

    public void Send(string eventName, IReadOnlyList<KeyValuePair<string, object>> props, string jsonLine)
    {
        pending.Append(jsonLine).Append('\n');
        pendingCount++;
        // 판 종료는 곧바로 기록 (직후에 앱이 강제 종료돼도 남도록)
        if (pendingCount >= FlushThreshold || eventName == "run_end") Flush();
    }

    public void Flush()
    {
        if (pendingCount == 0) return;
        string path = Path.Combine(directory, $"events_{DateTime.UtcNow:yyyyMMdd}.jsonl");
        try
        {
            File.AppendAllText(path, pending.ToString(), Utf8NoBom);
        }
        catch (IOException e)
        {
            Debug.LogWarning($"[Analytics] 파일 기록 실패: {e.Message}");
            return;   // 버퍼를 유지해 다음 Flush에서 재시도
        }
        pending.Clear();
        pendingCount = 0;
    }

    public void DiscardPending()
    {
        pending.Clear();
        pendingCount = 0;
    }

    public void DeleteStoredData()
    {
        foreach (string file in Directory.GetFiles(directory, "*.jsonl"))
        {
            try { File.Delete(file); }
            catch (IOException e) { Debug.LogWarning($"[Analytics] 삭제 실패: {e.Message}"); }
        }
    }
}
```

앱이 백그라운드로 가거나 종료될 때 버퍼를 비우고, 돌아올 때 세션을 판단하는 컴포넌트입니다. 파일: `Assets/_CoinRush/Scripts/Analytics/AnalyticsLifecycle.cs`

```csharp
using System;
using UnityEngine;

/// <summary>Analytics가 런타임에 자동 생성. 씬에 직접 배치하지 않는다.</summary>
public class AnalyticsLifecycle : MonoBehaviour
{
    private DateTime backgroundedAtUtc;
    private bool inBackground;

    // 모바일은 종료 이벤트 없이 백그라운드에서 프로세스가 죽는 경우가 많다 → 일시정지 때 기록
    private void OnApplicationPause(bool paused)
    {
        if (paused)
        {
            inBackground = true;
            backgroundedAtUtc = DateTime.UtcNow;
            Analytics.Flush();
            return;
        }
        if (!inBackground) return;   // 시작 직후에 오는 OnApplicationPause(false)는 무시
        inBackground = false;
        Analytics.OnResumed((DateTime.UtcNow - backgroundedAtUtc).TotalSeconds);
    }

    private void OnApplicationQuit() => Analytics.Flush();
}
```

`OnApplicationPause`는 모바일에서 앱이 백그라운드로 가고 돌아올 때 호출됩니다. PC(Steam)에서는 창 포커스 이동에 대해 호출 여부가 설정에 따라 다르므로, PC판 세션은 사실상 "실행 단위"로 읽습니다([MonoBehaviour.OnApplicationPause](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/MonoBehaviour.OnApplicationPause.html)).

### 4단계: 이벤트 심기와 동의 화면

**동의 화면**: 타이틀 씬(04장 Title 상태)에 패널을 하나 만들고 두 버튼에 아래 메서드를 연결합니다. `Analytics.Consent == AnalyticsConsent.Unknown`일 때만 패널을 보여주고, 설정 화면(11장)에는 같은 토글과 "수집된 기록 삭제" 버튼(`Analytics.DeleteStoredData`)을 둡니다.

```csharp
// Assets/_CoinRush/Scripts/UI/AnalyticsConsentPanel.cs
using UnityEngine;

public class AnalyticsConsentPanel : MonoBehaviour
{
    private void Start() => gameObject.SetActive(Analytics.Consent == AnalyticsConsent.Unknown);

    public void OnAccept() { Analytics.SetConsent(true); gameObject.SetActive(false); }   // "동의" 버튼
    public void OnDecline() { Analytics.SetConsent(false); gameObject.SetActive(false); } // "거부" 버튼
}
```

패널 문구 예: "게임 개선을 위해 플레이 기록(판 길이, 사망 원인, 선택한 강화)을 익명으로 수집합니다. 이름·연락처는 수집하지 않으며 설정에서 언제든 끄고, 기기에 저장된 기록을 삭제할 수 있습니다. [동의] [거부]"

**데이터 처리 방침**(`Docs/analytics-spec.md`에 함께 적음): 철회하면 기기의 대기 버퍼는 즉시 버리고 이후 수집·전송을 멈춥니다. 이미 파일로 기록된 데이터는 "기록 삭제"를 누를 때 지웁니다. 플레이테스트에서 회수한 파일은 테스트 종료 후 보관 기간(예: 3개월)을 정해 삭제합니다. SDK로 서버에 보낸 데이터는 해당 서비스의 사용자 데이터 삭제 기능·API로 처리하며, 그 방법을 개인정보 처리방침에 적습니다(28장).

**이벤트 호출 위치**: 23장까지 만든 코드에 실제로 연결합니다. 판 단위 정보는 23장 `RunRecorder`가 이미 가지고 있으므로, 새로 필요한 것은 사망 원인 기록 한 줄과 호출 지점뿐입니다.

① **사망 원인**: 23장 `RunRecorder`에 프로퍼티를 추가하고, 07장 `PlayerContactDamage`가 피해를 주기 직전에 가해자 에셋 이름을 남깁니다.

```csharp
// RunRecorder.cs (23장) — 프로퍼티 추가
public string LastDamageSource { get; set; }   // 마지막으로 플레이어에게 피해를 준 EnemyData 에셋 이름

// PlayerContactDamage.cs (07·23장) — 필드 추가
[SerializeField] private RunRecorder recorder;

// OnTriggerStay2D 안, health.TakeDamage(...) 바로 위에 추가
if (recorder != null) recorder.LastDamageSource = enemy.Data.name;
```

② **판 시작·종료**: 23장 `RunRecorder`의 정적 이벤트를 구독합니다. `RunStarted`는 `GameStateMachine.StartGame`에서만 발생하므로 레벨업 복귀(Playing 재진입)나 25장 부활로는 `run_start`가 다시 찍히지 않습니다. 씬 오브젝트가 아닌 정적 클래스에서 구독하므로, 판 도중 타이틀로 나가 Game 씬이 언로드되는 순간의 `run_end`(cause `quit`)도 놓치지 않습니다. 파일: `Assets/_CoinRush/Scripts/Analytics/RunAnalytics.cs`

```csharp
using UnityEngine;

public static class RunAnalytics
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void Register()
    {
        RunRecorder.RunStarted -= OnRunStarted;   // 도메인 리로드를 끈 경우 중복 구독 방지
        RunRecorder.RunFinished -= OnRunFinished;
        RunRecorder.RunStarted += OnRunStarted;
        RunRecorder.RunFinished += OnRunFinished;
    }

    private static void OnRunStarted(RunRecorder run)
    {
        SaveData save = SaveSystem.Load();
        int runIndex = save.stats.totalRuns + 1;           // 정산 전이므로 +1 (중도 종료도 1판으로 셈)
        Analytics.SetRun(run.RunId, runIndex, () => run != null ? run.Seconds : 0f);
        Analytics.Track("run_start",
            ("meta_damage_lv", save.GetUpgradeLevel(MetaUpgradeIds.Damage)),
            ("meta_hp_lv", save.GetUpgradeLevel(MetaUpgradeIds.MaxHp)),
            ("meta_magnet_lv", save.GetUpgradeLevel(MetaUpgradeIds.Magnet)));
    }

    private static void OnRunFinished(RunRecorder run)
    {
        // death면 마지막 가해자, 아니면 "clear" / "quit"
        string cause = run.EndReason == "death" && !string.IsNullOrEmpty(run.LastDamageSource)
            ? run.LastDamageSource : run.EndReason;
        Analytics.Track("run_end",
            ("duration_s", run.Seconds),
            ("cause", cause),
            ("level", run.Level),
            ("coins_collected", run.CoinsCollected),
            ("coins_banked", run.Banked),
            ("shrine_purchases", run.ShrinePurchases));
        Analytics.ClearRun();
    }
}
```

③ **레벨업 선택**: 04장 `GameStateMachine`에 `public PlayerExperience Experience => playerExperience;`를 추가하고(필드는 11장), 23장에서 고친 `LevelUpState.OnChosen`을 아래로 교체합니다.

```csharp
// LevelUpState.cs (11·23장) — OnChosen 교체
private void OnChosen(UpgradeData chosen)
{
    var offered = new System.Collections.Generic.List<string>(picks.Length);
    foreach (UpgradeData p in picks) if (p != null) offered.Add(p.name);   // 제시된 카드 (에셋 이름)

    stats.Apply(chosen.kind);
    Analytics.Track("level_up",
        ("level", machine.Experience.Level),
        ("choice", chosen.name),
        ("offered", string.Join(",", offered)));
    TutorialSteps.Complete(2, "first_level_up");
    machine.ChangeState(playingState);
}
```

④ **제단 방문**: 23장 `CoinShrine.VisitClosed`를 구독하는 작은 컴포넌트를 `CoinShrine`과 같은 오브젝트에 붙입니다. 판정에 필요한 "살 수 있었나(`affordable`)"와 체력 비율을 함께 남깁니다(21장 성공 기준의 분모).

```csharp
// Assets/_CoinRush/Scripts/Analytics/ShrineAnalytics.cs
using UnityEngine;

[RequireComponent(typeof(CoinShrine))]
public class ShrineAnalytics : MonoBehaviour
{
    private CoinShrine shrine;

    private void Awake() => shrine = GetComponent<CoinShrine>();
    private void OnEnable() => shrine.VisitClosed += OnVisitClosed;
    private void OnDisable() => shrine.VisitClosed -= OnVisitClosed;

    private void OnVisitClosed(ShrineVisit v)
    {
        Analytics.Track("shrine_visit",
            ("shrine_index", v.shrineIndex), ("price", v.price), ("wallet", v.walletBefore),
            ("affordable", v.affordable), ("hp_ratio", v.hpRatio), ("dwell_s", v.dwellSeconds),
            ("purchased", v.purchased), ("choice", v.choice), ("offered", v.offered));
    }
}
```

⑤ **영구 강화 구매와 온보딩 단계**: 온보딩 단계는 설치당 한 번만 기록하는 도우미로 남깁니다. 파일: `Assets/_CoinRush/Scripts/Analytics/TutorialSteps.cs`

```csharp
using UnityEngine;

public static class TutorialSteps
{
    /// <summary>1 first_move · 2 first_level_up · 3 upgrade_shop_open · 4 first_upgrade_purchase</summary>
    public static void Complete(int step, string stepName)
    {
        if (Analytics.Consent != AnalyticsConsent.Granted) return;   // 동의 전 완료는 기록하지 않고 다음 기회에
        string key = "tutorial_step_done_" + step;
        if (PlayerPrefs.GetInt(key, 0) == 1) return;                 // 설치당 한 번
        PlayerPrefs.SetInt(key, 1);
        PlayerPrefs.Save();
        Analytics.Track("tutorial_step", ("step", step), ("step_name", stepName));
    }
}
```

```csharp
// UpgradeShop.cs (23장) — OnEnable 교체
private void OnEnable()
{
    Refresh();
    TutorialSteps.Complete(3, "upgrade_shop_open");
}

// UpgradeShop.TryBuy — SaveSystem.Save(save); 다음 줄에 추가
Analytics.Track("upgrade_purchase", ("upgrade_id", upgradeId), ("new_level", level + 1),
                ("cost", cost), ("bank_after", save.coins));
TutorialSteps.Complete(4, "first_upgrade_purchase");
```

```csharp
// PlayerMover.cs (08장) — 필드 추가
private bool movedOnce;

// Update 끝에 추가 (MoveInput은 04장부터 쓰던 프로퍼티)
if (!movedOnce && MoveInput.sqrMagnitude > 0.01f)
{
    movedOnce = true;
    TutorialSteps.Complete(1, "first_move");
}
```

⑥ **처음 본 것**: 콘텐츠 고갈 지표의 원자료입니다. 온보딩 단계와 달리 **항목마다** 설치당 한 번 기록하고, 판마다 개수를 세어 `run_end`에 싣습니다. 스폰될 때마다 불리므로 이번 실행에서 이미 확인한 키는 메모리에서 거릅니다. 파일: `Assets/_CoinRush/Scripts/Analytics/FirstSeen.cs`

```csharp
using System.Collections.Generic;
using UnityEngine;

/// <summary>미리 정한 목록(적·강화 카드·영구 강화 레벨)에서 "처음 본 것"을 설치당 한 번 기록한다.</summary>
public static class FirstSeen
{
    private static readonly HashSet<string> checkedThisSession = new HashSet<string>();

    /// <summary>이번 판에서 처음 본 것의 수 (run_end의 new_seen)</summary>
    public static int CountThisRun { get; private set; }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStatics()
    {
        checkedThisSession.Clear();
        CountThisRun = 0;
    }

    public static void BeginRun() => CountThisRun = 0;

    /// <param name="kind">enemy / upgrade / unlock</param>
    /// <param name="id">에셋 이름 또는 "damage_4" 같은 영구 강화 레벨</param>
    public static void Report(string kind, string id)
    {
        if (Analytics.Consent != AnalyticsConsent.Granted || string.IsNullOrEmpty(id)) return;

        string key = "seen_" + kind + "_" + id;
        if (!checkedThisSession.Add(key)) return;      // 이번 실행에서 이미 확인함 (PlayerPrefs 접근을 줄인다)
        if (PlayerPrefs.GetInt(key, 0) == 1) return;   // 이전 실행에서 이미 봤음

        PlayerPrefs.SetInt(key, 1);
        PlayerPrefs.Save();
        CountThisRun++;
        Analytics.Track("first_seen", ("kind", kind), ("id", id));
    }
}
```

세 곳에 한 줄씩 넣습니다. **"처음 겪은" 시점이 아니라 "처음 화면에 보인" 시점**으로 통일합니다(카드는 제시될 때, 적은 스폰될 때).

```csharp
// EnemySpawner.cs (22장) — 적을 스폰해 Init한 직후
FirstSeen.Report("enemy", data.name);

// LevelUpState.cs (11·23장) — PickThree 끝에 추가
foreach (UpgradeData p in picks) if (p != null) FirstSeen.Report("upgrade", p.name);

// CoinShrine.cs (23장) — PickOffers의 names.Add(offers[i].name); 다음 줄
FirstSeen.Report("upgrade", offers[i].name);

// UpgradeShop.cs (23장) — TryBuy의 Analytics.Track("upgrade_purchase", ...) 다음 줄
FirstSeen.Report("unlock", $"{upgradeId}_{level + 1}");
```

`RunAnalytics`(②)도 두 줄 고칩니다.

```csharp
// OnRunStarted의 Analytics.SetRun(...) 다음 줄
FirstSeen.BeginRun();

// OnRunFinished의 Analytics.Track("run_end", ...) 마지막 파라미터로 추가
("new_seen", FirstSeen.CountThisRun));
```

에디터 연결: Player의 `PlayerContactDamage` **Recorder**에 `RunRecorder` 오브젝트를 드래그하고, `CoinShrine` 오브젝트에 `ShrineAnalytics`를 추가합니다. `RunAnalytics`·`TutorialSteps`·`FirstSeen`은 정적 클래스라 씬에 둘 것이 없습니다.

### 5단계: 로그 집계 에디터 도구

테스터들에게 받은 `.jsonl` 파일을 한 폴더에 모아 집계합니다. Windows는 `%userprofile%\AppData\LocalLow\<회사>\<제품>\analytics`, macOS는 `~/Library/Application Support/<회사>/<제품>/analytics`가 기본 위치입니다(`Application.persistentDataPath` 문서 참고). 강제 종료로 마지막 줄이 잘린 파일도 섞여 오므로 **줄 단위로 파싱 오류를 격리**합니다. 파일: `Assets/_CoinRush/Scripts/Editor/AnalyticsLocalReport.cs`

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

public static class AnalyticsLocalReport
{
    // 순차 퍼널의 관측 기간: 첫 실행 후 이 시간 안에 일어난 단계만 인정.
    // 대면 플레이테스트는 2시간, 출시 후 데이터는 7일(168) 같은 값으로 바꾼다.
    private const double FunnelWindowHours = 2;

    // JsonUtility는 클래스에 없는 키는 무시하고, 없는 필드는 기본값으로 둔다 → 모든 이벤트를 한 클래스로 읽는다
    [Serializable]
    public class Row
    {
        public string name, ts, user_id, session_id, run_id, local_date, cause, choice, offered, upgrade_id, kind, id;
        public float duration_s, hp_ratio;
        public int run_index, level, coins_banked, step, price, wallet, new_seen;
        public bool first_open, purchased, affordable;
        [NonSerialized] public DateTime time;
    }

    [MenuItem("Coin Rush/Analytics/Local Report...")]
    private static void Run()
    {
        string folder = EditorUtility.OpenFolderPanel("JSONL 폴더 선택", Application.persistentDataPath, "");
        if (string.IsNullOrEmpty(folder)) return;

        var rows = new List<Row>();
        var skipped = new List<string>();
        foreach (string file in Directory.GetFiles(folder, "*.jsonl"))
        {
            int lineNo = 0;
            foreach (string line in File.ReadLines(file))
            {
                lineNo++;
                if (string.IsNullOrWhiteSpace(line)) continue;
                try
                {
                    Row row = JsonUtility.FromJson<Row>(line);
                    if (row == null || string.IsNullOrEmpty(row.name)) throw new FormatException("name 없음");
                    row.time = DateTime.Parse(row.ts, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind);
                    rows.Add(row);
                }
                catch (Exception e) when (e is ArgumentException || e is FormatException)
                {
                    skipped.Add($"{Path.GetFileName(file)}:{lineNo} ({e.GetType().Name})");   // 잘린 줄 등: 제외하고 계속
                }
            }
        }

        var sb = new StringBuilder();
        sb.AppendLine($"이벤트 {rows.Count}개, 사용자 {rows.Select(r => r.user_id).Distinct().Count()}명, 제외한 줄 {skipped.Count}개");
        foreach (string s in skipped.Take(10)) sb.AppendLine($"  제외: {s}");

        // 1) 판 종료: 사망 분 분포 (23장 시뮬레이터 히스토그램과 같은 형식)
        List<Row> ends = rows.Where(r => r.name == "run_end").ToList();
        var histogram = new int[11];
        foreach (Row r in ends.Where(r => r.cause != "quit"))
            histogram[r.cause == "clear" ? 10 : Mathf.Min(9, (int)(r.duration_s / 60f))]++;
        sb.AppendLine($"\n[run_end] {ends.Count}판 (중도 종료 {ends.Count(r => r.cause == "quit")}), " +
                      $"평균 {(ends.Count > 0 ? ends.Average(r => r.duration_s) : 0):0}초, " +
                      $"평균 이월 {(ends.Count > 0 ? ends.Average(r => r.coins_banked) : 0):0}");
        for (int m = 0; m < 10; m++) sb.Append($"{m}분 {histogram[m]} | ");
        sb.AppendLine($"클리어 {histogram[10]}");
        foreach (var g in ends.GroupBy(r => r.cause).OrderByDescending(g => g.Count()))
            sb.AppendLine($"  원인 {g.Key}: {g.Count()}");

        // 2) 레벨업: 제시 빈도, 제시됐을 때 선택률, 전체 선택 중 점유율을 따로 보고
        List<Row> levelUps = rows.Where(r => r.name == "level_up").ToList();
        var offeredCount = new Dictionary<string, int>();
        var chosenCount = new Dictionary<string, int>();
        foreach (Row r in levelUps)
        {
            foreach (string o in (r.offered ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries))
                offeredCount[o] = offeredCount.GetValueOrDefault(o) + 1;
            chosenCount[r.choice] = chosenCount.GetValueOrDefault(r.choice) + 1;
        }
        sb.AppendLine($"\n[level_up] {levelUps.Count}회 — 제시율(레벨업 중 제시) / 조건부 선택률(제시 중 선택) / 점유율(전체 선택 중)");
        sb.AppendLine("  23장 기준: 조건부 선택률 70% 이상 = 3택1이 사실상 1택");
        foreach (var kv in offeredCount.OrderByDescending(kv => chosenCount.GetValueOrDefault(kv.Key)))
        {
            int chosen = chosenCount.GetValueOrDefault(kv.Key);
            sb.AppendLine($"  {kv.Key}: 제시 {kv.Value / (float)levelUps.Count:P0} / 선택 {chosen}/{kv.Value} = {chosen / (float)kv.Value:P0} / 점유 {chosen / (float)levelUps.Count:P0}");
        }

        // 3) 제단: 분모는 "살 수 있었던 방문", 참가자별로 구매·모으기를 모두 했는지 (21장 성공 기준)
        List<Row> affordable = rows.Where(r => r.name == "shrine_visit" && r.affordable).ToList();
        int allVisits = rows.Count(r => r.name == "shrine_visit");
        if (allVisits > 0)
        {
            sb.AppendLine($"\n[shrine_visit] 방문 {allVisits}회 중 살 수 있었던 방문 {affordable.Count}회, " +
                          $"그중 구매율 {(affordable.Count > 0 ? affordable.Count(v => v.purchased) / (float)affordable.Count : 0f):P0}");
            foreach (var user in affordable.GroupBy(v => v.user_id))
            {
                int bought = user.Count(v => v.purchased), kept = user.Count(v => !v.purchased);
                string id = user.Key ?? "?";
                sb.AppendLine($"  {(id.Length > 6 ? id.Substring(0, 6) : id)}: 구매 {bought} / 모으기 {kept}  {(bought > 0 && kept > 0 ? "← 선택이 바뀜" : "")}");
            }
        }

        // 4) 순차 퍼널: 사용자별 시각순, 각 단계는 "이전 단계 이후 + 관측 기간 안"에 일어나야 인정
        AppendOrderedFunnel(sb, rows);

        // 5) 콘텐츠 고갈: 판 수별 진행률과 판당 신규 경험 비율
        AppendContentDepth(sb, rows);

        // 6) 빌드 다양성: 23장에서 정의한 지표를 실제 로그로 (같은 BuildProfile.Similarity를 쓴다)
        AppendBuildDiversity(sb, rows);

        Debug.Log(sb.ToString());
    }

    private static void AppendContentDepth(StringBuilder sb, List<Row> rows)
    {
        // (1) 판 수별 진행률 — 사용자별 "도달한 최대 run_index"만 있으면 계산된다
        var deepest = rows.Where(r => r.name == "run_start" && !string.IsNullOrEmpty(r.user_id))
                          .GroupBy(r => r.user_id)
                          .ToDictionary(g => g.Key, g => g.Max(r => r.run_index));
        sb.AppendLine($"\n[판 수별 진행률] 사용자 {deepest.Count}명 " +
                      "(대면 테스트는 세션 길이가 정해져 있어 이탈로 읽으면 안 됨 — 데모·출시 로그용)");
        int maxIndex = deepest.Count > 0 ? deepest.Values.Max() : 0;
        for (int n = 1; n < Mathf.Min(maxIndex + 1, 11); n++)
        {
            int reached = deepest.Values.Count(m => m >= n);
            int next = deepest.Values.Count(m => m >= n + 1);
            sb.AppendLine($"  {n}판 시작 {reached}명 → {n + 1}판 시작 {next}명 " +
                          $"({(reached > 0 ? next / (float)reached : 0f):P0})");
        }

        // (2) 판당 신규 경험 비율 = 그 판의 new_seen ÷ 그 판까지 누적 new_seen
        var cumulative = new Dictionary<string, int>();
        sb.AppendLine("[판당 신규 경험 비율] 그 판의 first_seen ÷ 그 판까지 누적 (사용자 평균, 1판은 정의상 100%)");
        foreach (var g in rows.Where(r => r.name == "run_end" && r.run_index > 0)
                              .GroupBy(r => r.run_index).OrderBy(g => g.Key))
        {
            var ratios = new List<float>();
            foreach (Row r in g)                      // run_index 오름차순이므로 누적이 순서대로 쌓인다
            {
                string user = r.user_id ?? "?";
                int total = cumulative.GetValueOrDefault(user) + r.new_seen;
                cumulative[user] = total;
                if (total > 0) ratios.Add(r.new_seen / (float)total);
            }
            if (ratios.Count > 0)
                sb.AppendLine($"  {g.Key}판: {ratios.Average():P0}  " +
                              $"(신규 {g.Sum(r => r.new_seen)}개 / {ratios.Count}판)");
        }
    }

    private static void AppendBuildDiversity(StringBuilder sb, List<Row> rows)
    {
        // 한 판의 빌드 = 그 run_id의 level_up 선택 + 제단에서 실제로 산 선택
        var builds = new Dictionary<string, Dictionary<string, int>>();
        var owner = new Dictionary<string, string>();
        foreach (Row r in rows)
        {
            bool counted = r.name == "level_up" || (r.name == "shrine_visit" && r.purchased);
            if (!counted || string.IsNullOrEmpty(r.run_id) || string.IsNullOrEmpty(r.choice)) continue;
            if (!builds.TryGetValue(r.run_id, out Dictionary<string, int> vector))
                builds[r.run_id] = vector = new Dictionary<string, int>();
            vector[r.choice] = vector.GetValueOrDefault(r.choice) + 1;
            owner[r.run_id] = r.user_id ?? "?";
        }

        string[] kinds = builds.Values.SelectMany(v => v.Keys).Distinct().OrderBy(k => k).ToArray();
        var similarities = new List<float>();
        foreach (var user in owner.GroupBy(kv => kv.Value))            // 같은 사람의 판끼리만 비교
        {
            List<int[]> vectors = user.Select(kv => kinds.Select(k => builds[kv.Key].GetValueOrDefault(k)).ToArray())
                                      .ToList();
            for (int i = 0; i < vectors.Count; i++)
                for (int j = i + 1; j < vectors.Count; j++)
                    similarities.Add(BuildProfile.Similarity(vectors[i], vectors[j]));   // 23장 순수 C# 규칙 재사용
        }
        similarities.Sort();

        sb.AppendLine($"\n[빌드 다양성] 빌드가 기록된 판 {builds.Count}개, 같은 사람의 판 쌍 {similarities.Count}개");
        if (similarities.Count == 0) { sb.AppendLine("  1인당 2판 이상이 필요합니다."); return; }
        sb.AppendLine($"  빌드 유사도 중앙값 {similarities[similarities.Count / 2]:0.00} " +
                      "(23장 기준: 0.85 이상이면 매 판 같은 빌드)");
        foreach (var user in owner.GroupBy(kv => kv.Value))
        {
            var totals = new Dictionary<string, int>();
            foreach (var kv in user)
                foreach (var pair in builds[kv.Key])
                    totals[pair.Key] = totals.GetValueOrDefault(pair.Key) + pair.Value;
            string id = user.Key.Length > 6 ? user.Key.Substring(0, 6) : user.Key;
            sb.AppendLine($"  {id}: " + string.Join(", ", totals.OrderByDescending(kv => kv.Value)
                                                                .Select(kv => $"{kv.Key} {kv.Value}")));
        }
    }

    private static void AppendOrderedFunnel(StringBuilder sb, List<Row> rows)
    {
        (string label, Func<Row, bool> match)[] steps =
        {
            ("첫 실행",        r => r.name == "session_start" && r.first_open),
            ("첫 판 시작",     r => r.name == "run_start" && r.run_index == 1),
            ("첫 레벨업 선택", r => r.name == "level_up" && r.run_index == 1),
            ("첫 판 종료",     r => r.name == "run_end" && r.run_index == 1),
            ("두 번째 판 시작", r => r.name == "run_start" && r.run_index == 2),
        };
        var reached = new int[steps.Length];
        int shopBranch = 0, excluded = 0;
        DateTime dataEnd = rows.Count > 0 ? rows.Max(r => r.time) : DateTime.MinValue;
        TimeSpan window = TimeSpan.FromHours(FunnelWindowHours);

        foreach (var user in rows.GroupBy(r => r.user_id))
        {
            List<Row> events = user.OrderBy(r => r.time).ToList();
            Row first = events.FirstOrDefault(steps[0].match);
            if (first == null) continue;                                  // 첫 실행이 로그에 없으면 코호트 밖
            if (first.time + window > dataEnd) { excluded++; continue; }  // 관측 기간을 다 채우지 못한 사용자

            DateTime cursor = first.time, deadline = first.time + window;
            reached[0]++;
            DateTime firstRunEnd = DateTime.MinValue;
            for (int s = 1; s < steps.Length; s++)
            {
                Row hit = events.FirstOrDefault(r => r.time >= cursor && r.time <= deadline && steps[s].match(r));
                if (hit == null) break;
                reached[s]++;
                cursor = hit.time;
                if (s == 3) firstRunEnd = hit.time;
            }
            // 선택 분기: 첫 판 종료 뒤, 관측 기간 안에 영구 강화를 샀는가 (순차 단계가 아님)
            if (firstRunEnd != DateTime.MinValue &&
                events.Any(r => r.name == "upgrade_purchase" && r.time >= firstRunEnd && r.time <= deadline))
                shopBranch++;
        }

        sb.AppendLine($"\n[퍼널] 관측 기간 {FunnelWindowHours}시간, 기간 미달로 제외 {excluded}명");
        for (int s = 0; s < steps.Length; s++)
        {
            string prev = s == 0 ? "—" : (reached[s - 1] > 0 ? (reached[s] / (float)reached[s - 1]).ToString("P0") : "—");
            sb.AppendLine($"  {s + 1}. {steps[s].label}: {reached[s]}명 (직전 대비 {prev})");
        }
        sb.AppendLine($"  분기: 첫 판 종료 후 영구 강화 구매 {shopBranch}/{reached[3]}명");
    }
}
```

`GetValueOrDefault`와 `Split(char, StringSplitOptions)` 오버로드는 Unity 6의 .NET Standard 2.1 API 호환성 수준에서 사용할 수 있습니다. 프로젝트의 Api Compatibility Level을 바꿨다면 확인하세요. 빌드 유사도는 23장 `BuildProfile.Similarity`를 그대로 부릅니다 — **시뮬레이터가 쓰는 정의와 로그 집계가 쓰는 정의가 같아야** 두 결과를 나란히 놓을 수 있습니다(23장 "하나의 규칙, 두 실행기"와 같은 이유).

### 6단계: 5인 플레이테스트 계획서 (완성본)

`Docs/playtest-plan-0.4.md`의 예시입니다.

```
[코인 러시 플레이테스트 계획 — 빌드 0.4 (버티컬 슬라이스)]

목적 (이번 테스트로 답할 질문 3개)
  Q1. 첫 10분 안에 코인 제단의 "쓸까 모을까"를 이해하고 고민하는가?
  Q2. 3:00 엘리트, 6:00 엘리트에서 죽음을 공정하다고 느끼는가?
  Q3. 첫 판 종료 후 영구 강화 화면을 찾아 구매하고, 스스로 다음 판을 시작하는가?

대상
  5명. 서바이버라이크를 1개 이상 5시간 이상 해본 사람. 지인 제외
  모집: 게임 개발 커뮤니티·Discord 공지, 감사 표시로 출시 시 Steam 키

환경
  PC + 패드(3명), 키보드(2명). 빌드 0.4.1, 애널리틱스 동의 후 로컬 JSONL 기록
  화면·음성 녹화 (OBS), 녹화·로그 수집 동의서 서명

진행 (1인당 45분, 동의서에 로그 보관 기간 3개월 명시)
  0~5분    인사, 동의서, Think-aloud 연습 (컵 보고 말하기)
  5~6분    안내 한 문장만: "적을 피해 최대한 오래 살아남는 게임입니다"
  6~36분   자유 플레이 30분 (최소 3판 — 영구 강화가 다음 판에 적용되는 경험 포함). 개입 금지, 관찰 기록
  36~43분  설문 + 인터뷰 (제단 방문 기록을 함께 보며 "여기서는 왜 샀나요/모았나요?")
  43~45분  "한 판 더 하실래요?" → 행동 기록, 로그 파일 회수

설문
  1. 방금 한 게임을 친구에게 한 문장으로 설명한다면?
  2. 가장 기억나는 결정의 순간은? 왜 그렇게 골랐나요?
  3. 코인 제단에서 무엇을 했나요? 그 이유는?
  4. 가장 답답하거나 불공평하다고 느낀 순간은?
  5. 판이 끝난 뒤 무엇을 하고 싶었나요?
  6. 친구에게 추천할 가능성 0~10점, 이유는?

성공 기준 (테스트 전 확정)
  Q1: 로그상 살 수 있었던 제단 방문에서 구매와 모으기를 각각 한 번 이상 한 참가자 4명 이상 (21장 기준)
      + 선택이 바뀐 참가자 중 3명 이상이 이유를 체력·지갑·다음 판 목표 같은 상황 차이로 설명
      (보조: 살 수 있었던 방문의 전체 구매율 20~80%)
  Q2: 엘리트 사망자 중 "불공평"을 언급한 사람이 절반 미만
  Q3: 5명 중 4명 이상이 도움 없이 영구 강화 1회 구매 + 다음 판 시작
```

### 7단계: 가상 결과 분석 예시

아래는 위 계획으로 테스트했다고 **가정한 가상 결과**와 분석 방식입니다.

**로그 집계 (AnalyticsLocalReport 출력 요약)**

```
이벤트 299개, 사용자 5명, 제외한 줄 1개
  제외: events_20261002.jsonl:58 (ArgumentException)      ← P4 기기 강제 종료로 잘린 마지막 줄
[run_end] 16판 (중도 종료 1), 평균 311초, 평균 이월 402
0분 0 | 1분 1 | 2분 2 | 3분 5 | 4분 1 | 5분 0 | 6분 3 | 7분 1 | 8분 0 | 9분 1 | 클리어 1
  원인 Enemy_EliteKnight: 4 / Enemy_Bomber: 4 / Enemy_Bat: 3 / Enemy_Skeleton: 2 / Enemy_KingGolem: 1 / quit: 1 / clear: 1
[level_up] 71회 — 제시율 / 조건부 선택률 / 점유율
  Upgrade_Projectile: 제시 34% / 선택 21/24 = 88% / 점유 30%
  ...
  Upgrade_Regen: 제시 32% / 선택 2/23 = 9% / 점유 3%
[shrine_visit] 방문 19회 중 살 수 있었던 방문 9회, 그중 구매율 11%
  P1: 구매 0 / 모으기 3    P2: 구매 1 / 모으기 1 ← 선택이 바뀜    P3: 구매 0 / 모으기 2
  P4: 구매 0 / 모으기 1    P5: 구매 0 / 모으기 1
[퍼널] 관측 기간 2시간, 기간 미달로 제외 0명
  1. 첫 실행 5 → 2. 첫 판 시작 5 → 3. 첫 레벨업 선택 5 → 4. 첫 판 종료 5 → 5. 두 번째 판 시작 5
  분기: 첫 판 종료 후 영구 강화 구매 3/5명
[판 수별 진행률] 사용자 5명 (대면 테스트는 세션 길이가 정해져 있어 이탈로 읽으면 안 됨)
  1판 5명 → 2판 5명 (100%) | 2판 5명 → 3판 5명 (100%) | 3판 5명 → 4판 1명 (20%)
[판당 신규 경험 비율] 그 판의 first_seen ÷ 그 판까지 누적 (사용자 평균)
  1판: 100% (신규 57개 / 5판)   2판: 23% (신규 17개 / 5판)
  3판: 12% (신규 10개 / 5판)    4판: 6% (신규 1개 / 1판)
[빌드 다양성] 빌드가 기록된 판 16개, 같은 사람의 판 쌍 13개
  빌드 유사도 중앙값 0.91 (23장 기준: 0.85 이상이면 매 판 같은 빌드)
  P1: Upgrade_Projectile 11, Upgrade_Damage 5, Upgrade_AttackSpeed 3, Upgrade_Magnet 1
  P2: Upgrade_Projectile 9, Upgrade_AttackSpeed 4, Upgrade_Damage 3, Upgrade_MaxHp 1
```

**3판 → 4판의 20%는 이탈이 아닙니다.** 자유 플레이 시간이 30분이라 대부분 3판에서 끝났습니다. 이 줄은 데모·출시 로그에서만 읽습니다(개념 절의 표본 요건).

**관찰 기록 합치기 (태그별 빈도)**

| 태그 | 관찰 요약 | 인원 |
|---|---|---|
| 제단 | 제단을 지나치거나, 멈춰도 가격만 보고 1초 안에 닫음. "비싸네" | 4/5 |
| 난이도 | 3:00 엘리트 "갑자기 뭐가 튀어나왔어" (경고 문구를 못 봄) | 3/5 |
| 난이도 | 2:05 폭탄충을 끌고 다니다 등 뒤에서 폭발. "내가 뭘 잘못한 거지?" (예고 원을 안 봄) | 4/5 |
| 레벨업 | 투사체만 고름. "이게 제일 세 보여서" | 5/5 |
| 메타 | 결과 화면에서 "확인"만 누르고 타이틀로 감. 강화 버튼을 못 찾음 | 2/5 |

**증상 → 원인 가설 → 처방**

| 증상 (근거) | 원인 가설 | 처방 | 검증 방법 |
|---|---|---|---|
| 살 수 있었던 방문에서 선택이 바뀐 참가자 1/5 (기준 4/5 미달), 구매율 11%, "비싸네" 4명 | 창에 강화 이름만 있고 수치·이월 가치가 없어 비교할 근거가 없음 | 카드에 "피해 +25% (이번 판)", 창 하단에 "모으면: 공격력 강화까지 N코인 남음" 표시 | 다음 테스트의 참가자별 선택 변화, 설문 3번 |
| 3:00 사망 5/15판(중도 종료 제외), "갑자기" 3명 | 경고 문구가 화면 상단이라 시선(캐릭터 중심)에서 멀음 | 경고를 캐릭터 근처 + 등장 방향 화살표로 이동, 경고음 추가 | 3분 사망 비율, 설문 4번 |
| 투사체: 제시됐을 때 선택률 88%, 점유율 30% | 23장 DPS 표 예측과 일치 (초반 +100%). 제시되면 거의 항상 고름 = 선택의 가치가 압도적 | **가치 자체를 조정**: 투사체 +1마다 한 발 피해 −15% (`CombatStats` 규칙 수정 → 시뮬레이터 재실행). 출현 빈도만 낮추면 제시됐을 때 항상 고르는 문제는 그대로이므로 쓰지 않음 | 다음 테스트의 **조건부 선택률 60% 이하**, 제시율은 변경 전과 비슷한지 따로 보고 |
| 첫 판 종료 후 영구 강화 구매 3/5 (분기) | 결과 화면 기본 버튼이 "확인"(타이틀행) | 결과 화면 기본 버튼을 "강화하러 가기"로 변경 | 퍼널 분기 비율, `tutorial_step` 3 도달 |
| 빌드 유사도 중앙값 **0.91** (기준 0.85 초과), P1·P2 모두 투사체가 최다 | 지배 선택지 하나가 빌드를 결정 — 23장 프로파일 시뮬레이션의 "투사체 우선 64.1% vs 2위 25.6%"와 같은 방향 | 23장 12단계 수정(투사체 피해 페널티 + 생존 계열 계수 인상 + 자석 상한)을 빌드에 반영 | 다음 테스트의 **빌드 유사도 0.85 미만**, 투사체 조건부 선택률 60% 이하 |
| 2판째 신규 경험 비율 **23%**, 3판째 12% | 첫 판이 새로움의 대부분을 소모. 적 6종·카드 7종이 1판에 거의 다 나옴 | **판단 보류** — 3판째 12%는 기준(20%) 미달이지만, 새 콘텐츠를 만들기 전에 "조합이 달라지면 새롭게 느끼는가"를 먼저 본다(위 행의 수정으로 검증) | 신규 경험 비율은 그대로일 것으로 예상. 대신 설문 5번에서 "다 본 것 같다"는 발화가 줄어드는지 |

**결론 (성공 기준 대비)**

```
Q1 실패 — 선택이 상황에 따라 바뀐 참가자 1/5, 구매율 11%. 제단 UI 정보 부족이 1순위 가설 → 0.4.2에서 수정 후 재테스트
Q2 부분 실패 — 엘리트 사망자 5명 중 3명 "불공평" 언급. 경고 가독성 수정
Q3 실패 — 3/5. 결과 화면 버튼 수정
공통: 3분 사망 5/15판(중도 종료 제외) — 23장 기준 가정의 3분 벽과 방향이 같음. 다만 5명·15판이라
      계수 보정에는 부족 → 사망 시각과 수집량을 누적해 23장 초보/기준/숙련 가정 중 어디에 가까운지 추적
빌드: 유사도 0.91 — 23장 시뮬레이터의 지배 판정과 실플레이가 같은 방향. 12단계 수정을 0.4.2에 반영
새로움: 3판째 신규 경험 12% — 기준 미달이지만 콘텐츠 추가는 보류(위 표)
다음 테스트: 0.4.2, 새로운 5명, 같은 질문 + 같은 기준
```

"Q1 실패"를 보고 제단을 없애지 않았다는 점에 주목하세요. 증상(사지 않음)의 원인 가설이 "제단이 재미없다"가 아니라 "정보가 안 보인다"이고, 그 가설은 싸게 검증할 수 있습니다. 폐기는 UI를 고친 뒤에도 기준에 못 미칠 때 고려합니다.

### 7-1단계: 수정하고 다시 재기 (가상 결과 한 바퀴)

7단계는 해석에서 멈췄습니다. 여기서 **수정 → 재측정**까지 한 바퀴를 돕니다. 한 바퀴를 끝까지 돌기 전에는 "고쳤다"고 말할 수 없습니다. 아래도 모두 **가상 결과**이고, 산식과 표본을 함께 적습니다.

**0.4.2에 들어간 수정 (7단계 처방표에서 그대로)**

| # | 무엇을 | 근거가 된 증상 | 재측정에서 볼 지표 |
|---|---|---|---|
| ① | 제단 카드에 "피해 +25% (이번 판)" 수치, 창 하단에 "모으면: 공격력 강화까지 N코인" 표시 | 살 수 있었던 방문 구매율 11%, "비싸네" 4명 | 참가자별 구매·모으기 전환 4/5, 구매율 20~80% |
| ② | 엘리트 경고를 캐릭터 근처 + 등장 방향 화살표 + 경고음 | 3:00 사망 5/15판, "갑자기" 3명 | 3분 사망 비율, 설문 4번 |
| ③ | 23장 12단계 수정: 투사체 +1마다 한 발 피해 −15%, 최대 체력 25→40, 재생 0.5→3, 방어 0.92→0.82, 자석 스택 상한 3 | 투사체 조건부 선택률 88%, 빌드 유사도 0.91 | 조건부 선택률 60% 이하, 유사도 0.85 미만 |
| ④ | 결과 화면 기본 버튼을 "강화하러 가기"로 | 첫 판 종료 후 강화 구매 3/5 | 퍼널 분기 비율 |

폭탄충 폭발 피해는 여기서 건드리지 않습니다 — 22장 11단계가 이미 v3에서 25 → 18로 낮췄고, 0.4.1 빌드가 그 값으로 측정된 것입니다. 같은 수치를 두 장에서 번갈아 만지면 어느 쪽 결과인지 알 수 없게 됩니다.

**클리어율을 22장과 직접 비교하지 마세요.** 22장 11단계의 33%는 **설계자 본인**이 12판을 돌린 값이고, 여기의 1/16(0.4.1)·2/18(0.4.2)은 **처음 해 보는 사람 5명**의 값입니다. 22장이 클리어율 기준을 "작업 기준"이라고 못 박은 이유가 이것입니다. 두 숫자는 같은 지표가 아니고, 같아지면 오히려 이상합니다.

**③은 한 묶음으로 들어갔습니다.** 시뮬레이터에서는 한 번에 하나씩(수정 A → 수정 B) 확인했지만, 사람에게는 반쯤 깨진 빌드를 쥐여 줄 수 없어 완성된 규칙을 넣었습니다. 그래서 재측정이 말할 수 있는 것은 **"묶음의 효과"**뿐이고, 어느 상수가 얼마나 기여했는지는 시뮬레이터 쪽 기록(`balance-log.md`)으로만 말합니다. 어느 쪽인지 헷갈리지 않게 보고서에 적어 둡니다.

**재측정 (0.4.2, 새 참가자 5명, 18판 — 중도 종료 1, 이벤트 331개, 같은 진행·같은 성공 기준)**

| 지표 | 기준 | 0.4.1 | **0.4.2** | 판정 |
|---|---|---|---|---|
| 살 수 있었던 제단 방문 구매율 | 20~80% | 9회 중 11% | **12회 중 42%** (5/12) | 충족 |
| 구매·모으기를 모두 한 참가자 | 4/5 이상 | 1/5 | **3/5** | 미달 |
| 투사체 **조건부** 선택률 | 60% 이하 | 24회 중 88% | **28회 중 46%** (13/28) | 충족 |
| 투사체 제시율 (건드리지 않은 값) | 변동 없어야 | 71회 중 34% | **83회 중 34%** | 의도대로 |
| 투사체 점유율 | — | 30% | **16%** | — |
| **빌드 유사도 중앙값** | 0.85 미만 | 0.91 | **0.74** | 충족 |
| 3분 사망 | 25% 이하 | 15판 중 5 (33%) | **17판 중 1 (6%)** | 충족 |
| 폭탄충 사망 (2:00~4:00) | — | 15판 중 4 | **17판 중 1** | 22장 v3와 같은 방향 |
| 엘리트 사망자 중 "불공평" 언급 | 절반 미만 | 5명 중 3 | **4명 중 1** | 충족 |
| 첫 판 종료 후 영구 강화 구매 | 4/5 이상 | 3/5 | **5/5** | 충족 |
| 2판째 신규 경험 비율 | — | 23% | **21%** | 변화 없음 |
| 3판째 신규 경험 비율 | 20% 이상 | 12% | **13%** | 여전히 미달 |

**바뀐 것**

- **빌드가 갈라졌습니다.** 유사도 0.91 → 0.74. 참가자 5명의 최다 선택이 투사체 2명, 공격 속도 2명, 피해 1명으로 나뉘었습니다. 23장 시뮬레이션이 예측한 방향(단일 우선 프로파일 1위−2위 격차 38.5%p → 3.3%p)과 같습니다. 다만 **크기까지 맞았다고 말할 수는 없습니다** — 표본이 5명 18판입니다.
- **제단 구매율이 11% → 42%.** 수치를 보여 주는 것만으로 결정이 생겼습니다. 7단계에서 "제단이 재미없다"가 아니라 "정보가 안 보인다"를 가설로 잡은 것이 맞았습니다.
- **3분 벽이 사라졌습니다**(33% → 6%). 경고 수정(②)과 밸런스 수정(③)이 같이 들어갔으므로 어느 쪽 덕인지는 이 데이터로 못 가릅니다. 23장 시뮬레이션에서 ③만으로도 3분 사망이 23.9% → 6.1%로 줄었으니 ③의 기여가 크다고 **추정**만 합니다.

**안 바뀐 것 — 이쪽이 더 중요합니다**

- **Q1은 여전히 실패입니다.** 구매율은 목표 구간에 들어왔지만 "구매와 모으기를 모두 한 참가자"는 3/5로 기준 4/5에 못 미칩니다. 2명은 열두 번 중 한 번도 모으지 않았습니다(둘 다 "보이면 일단 산다"). **보조 지표가 통과했다고 주 기준을 통과로 바꾸지 않습니다.** 0.4.3에서는 "모으기"의 값을 보여 주는 쪽(다음 영구 강화까지 남은 코인 표시)을 더 키워 재테스트합니다.
- **새로움 곡선은 그대로입니다**(2판째 23% → 21%, 3판째 12% → 13%). 당연합니다 — ①~④ 어느 것도 **볼 것을 늘리지 않았습니다.** 빌드가 갈라진 것과 "처음 보는 것이 남아 있는 것"은 다른 축입니다. 다만 설문 5번에서 "다 본 것 같다"는 발화가 2/5 → 0/5로 줄었고, 대신 "다음엔 공속으로 가 봐야지" 같은 **다음 판 계획**이 3/5에서 나왔습니다. 조합이 새로움의 일부를 대신할 수 있다는 신호이지만, 5명으로는 가설입니다.
- **후반 사망이 늘었습니다**(7~8분 1/15 → 4/17). 23장 12단계가 예고한 그대로입니다(시뮬레이션에서 7~8분 사망 8.8% → 29.2%). 22장 11단계도 같은 방향을 봤습니다 — 폭탄충 피해를 낮춰 전반을 살리자 후반(보스·골렘 벽)이 남았습니다. 새로 생긴 증상이므로 다음 사이클의 1순위 후보로 올립니다.

**보고서에 남기는 형식** — 한 바퀴를 돌 때마다 이 네 줄을 씁니다.

```
0.4.2 재측정 (2026-10-16, 새 참가자 5명 / 18판 / 이벤트 331개)
  고침    : 제단 정보(①) → 구매율 11%→42% · 밸런스(③) → 빌드 유사도 0.91→0.74, 투사체 조건부 88%→46%
  못 고침 : Q1 주 기준(구매·모으기 전환) 1/5→3/5, 기준 4/5 미달 — 0.4.3에서 "모으기" 쪽 정보 강화
  안 변함 : 신규 경험 비율 (2판째 23%→21%) — 수정 중 볼 것을 늘린 것이 없으므로 예상대로
  새 증상 : 7~8분 사망 1/15→4/17 (23장 시뮬레이션 7~8분 8.8%→29.2% 예고와 일치) — 다음 사이클 1순위
  주의    : ③은 다섯 상수를 묶어 넣었으므로 상수별 기여는 시뮬레이터 기록으로만 말할 수 있음
```

**여기서 만든 지표가 35장 게이트 L2·L3의 재료입니다.** 35장의 L2(첫 판 완주율, 자발적 "한 판 더", 추천 의향 중앙값)는 이 장의 `run_end`·세션 마지막 질문·설문 6번으로, L3(데모 완주율, 7일 안 재방문)은 `run_end`(`cause="clear"`)와 `session_start`(`local_date`)로 계산합니다. 판 수별 진행률은 그때(200명 이상) 비로소 이탈로 읽을 수 있습니다.

### 확인하기

1. Play → 동의 패널이 뜨고 [동의]를 누르면 Console에 `[Analytics] {"name":"session_start",...,"first_open":true,"reason":"consent","local_date":"..."}`가 찍힌다.
2. 한 판에서 레벨업을 여러 번 한 뒤 끝내면, JSONL에 `run_start`는 **한 줄**, `run_end`도 한 줄이고, 그 사이 `level_up`·`shrine_visit`이 모두 같은 `run_id`를 가진다. `run_end`의 `cause`가 마지막으로 맞은 적 에셋 이름이다.
3. 판 도중 타이틀로 나가면 `cause:"quit"`인 `run_end`가 기록된다.
4. 이벤트 이름을 일부러 `RunEnd`로 바꿔 호출하면 에러 로그만 나오고 파일에는 기록되지 않는다.
5. JSONL 파일 끝에 `{"name":"run_en`처럼 잘린 줄을 직접 붙여 넣고 **Local Report...** 를 실행하면 "제외한 줄 1개"와 파일명:줄 번호가 나오고 나머지 집계는 정상 출력된다.
6. **복귀 세션**(모바일 실기기): 앱을 백그라운드로 보낸 뒤 테스트용으로 `NewSessionAfterBackgroundSeconds`를 60으로 줄이고 1분 뒤 돌아오면 `reason:"resume"`인 `session_start`가 새 `session_id`로 기록된다. 확인 후 값을 되돌린다.
7. **철회**: 동의 상태에서 이벤트를 몇 개 발생시켜 버퍼에 남긴 뒤(20개 미만), 설정에서 동의를 끄고 앱을 종료한다. 파일에 **그 이벤트들도, 이후 이벤트도** 추가되지 않는다. "기록 삭제"를 누르면 `analytics` 폴더의 `.jsonl` 파일이 사라진다.
8. **처음 본 것**: 새 프로필(설정 → 기록 삭제 + PlayerPrefs 초기화)로 첫 판을 하면 `first_seen`이 여러 줄 찍히고, **같은 적·같은 카드는 두 번째 판에서 다시 찍히지 않는다.** `run_end`의 `new_seen`이 1판에서 가장 크고 판이 갈수록 줄어든다.
9. **신규 경험 비율**: **Local Report...** 의 `[판당 신규 경험 비율]`에서 **1판이 항상 100%**이고 이후 단조 감소한다(정의상 그래야 한다. 오르면 `new_seen` 집계나 `run_index`가 잘못된 것이다).
10. **빌드 다양성**: 한 판에서 같은 강화만 3번 고르고 다른 판에서 다른 강화만 3번 고르면, `[빌드 다양성]`의 유사도가 0.00에 가깝게 나온다. 같은 강화만 두 판 고르면 1.00이 나온다.

## 흔한 실수

1. **증상**: 테스트 내내 옆에서 "거기서 제단 누르시면 돼요"라고 말했다. → **원인**: 개발자의 설명 본능. → **해결**: 진행 규칙을 인쇄해 두고, 개입하고 싶을 때마다 관찰 기록에 "개입 욕구: 00:00 제단"이라고 적습니다. 그 순간이 곧 발견입니다.
2. **증상**: 테스터 말대로 "적 약화"를 했더니 다음 테스트에서 "지루하다"가 나왔다. → **원인**: 처방을 그대로 적용. → **해결**: 증상(무력감의 시점)만 받아들이고 원인 가설을 세운 뒤 처방은 설계자가 정합니다. 가설과 검증 방법을 표로 남깁니다.
3. **증상**: 출시 후 D7을 보려 했는데 `session_start`가 없어서 계산할 수 없다. → **원인**: 질문 없이 이벤트를 심음. → **해결**: 1단계처럼 "질문 → 판단 기준 → 이벤트" 표를 출시 전에 만들고, 표의 모든 판단 기준이 실제로 계산 가능한지 가짜 데이터로 집계해 봅니다.
4. **증상**: 독일어 기기 테스터의 로그가 집계 도구에서 깨진다. → **원인**: `ToString()`이 기기 로캘의 소수점(쉼표)을 사용. → **해결**: 숫자 직렬화에는 항상 `CultureInfo.InvariantCulture`를 씁니다.
5. **증상**: 모바일 테스트에서 마지막 판 로그가 자주 사라진다. → **원인**: 앱이 백그라운드에서 종료되어 `OnApplicationQuit`이 호출되지 않음. → **해결**: `OnApplicationPause(true)`에서 기록하고, 중요한 이벤트(`run_end`)는 즉시 기록합니다.
6. **증상**: 한 판에 `run_start`가 10개 넘게 찍혀 2판째 시작률이 1,000%로 나온다. → **원인**: "Playing 상태 진입"에서 기록했는데 레벨업 복귀·부활도 Playing에 다시 들어옴. → **해결**: 판 시작은 `GameStateMachine.StartGame` → `RunRecorder.BeginRun` 한 곳에서만 발생시키고, 판 안 이벤트는 `run_id`로 묶습니다.
7. **증상**: 설정에서 수집을 껐는데 종료 직전 이벤트 몇 줄이 파일에 남는다. → **원인**: 철회가 동의 값만 바꾸고 대기 버퍼를 비우지 않아, 종료·백그라운드의 `Flush`가 그대로 기록. → **해결**: 철회 시 모든 백엔드의 `DiscardPending`을 호출하고 `Flush`도 동의 상태를 확인합니다.
8. **증상**: 스토어 심사에서 개인정보 항목이 실제 수집과 다르다고 지적받았다. → **원인**: 서드파티 SDK(분석·광고)가 수집하는 항목을 빠뜨림. → **해결**: 각 SDK 문서의 데이터 수집 목록을 확인해 App Privacy·데이터 보안 양식에 반영합니다.
9. **증상**: 5인 대면 테스트에서 "3판째에 80%가 이탈했다"고 보고서에 썼다. → **원인**: 자유 플레이 시간이 30분이라 대부분 3판에서 **시간이 끝난** 것입니다. 일정이 만든 숫자를 행동으로 읽었습니다. → **해결**: 판 수별 진행률은 세션 길이를 통제하지 않는 표본(데모·출시 로그, 수백 명)에서만 씁니다. 대면 테스트에서는 신규 경험 비율과 빌드 유사도처럼 **세션 길이에 덜 휘둘리는 지표**를 봅니다.
10. **증상**: 수정 후 재측정에서 보조 지표가 통과해 "해결"로 적었는데 다음 테스트에서 같은 문제가 또 나왔다. → **원인**: 성공 기준을 **테스트 전에** 정해 놓고, 통과한 쪽만 골라 읽었습니다(제단 구매율은 통과, 구매·모으기 전환은 미달). → **해결**: 재측정 보고서를 "고침 / 못 고침 / 안 변함 / 새 증상" 네 칸으로 고정합니다. 주 기준이 미달이면 보조 지표가 아무리 좋아도 미달입니다.
11. **증상**: 여러 수정을 한 빌드에 묶어 넣고 "이 수정 덕분에 좋아졌다"고 결론 냈다. → **원인**: 사람 테스트는 한 번에 하나씩 바꾸기 어렵다는 현실 때문에 묶음 배포는 정상이지만, 해석까지 묶으면 안 됩니다. → **해결**: 상수 단위의 기여는 23장 시뮬레이터에서 하나씩 확인해 `balance-log.md`에 남기고, 플레이테스트 보고서에는 **"묶음의 효과"**라고 명시합니다.
12. **증상**: 출시 6개월 뒤 "언제부터 지루해졌는지" 물었는데 답할 데이터가 없다. → **원인**: `first_seen`의 대상 목록을 출시 후에 바꿔 과거 판의 분모가 달라졌습니다. → **해결**: 대상 목록(적·카드·강화 레벨)을 사양 표에 못 박고, 콘텐츠를 추가하면 **목록을 바꾸는 대신 새 `kind`를 추가**해 옛 곡선을 보존합니다.

## 연습 문제

**1. ★☆☆ 이벤트 이름 고치기**
다음 이벤트를 네이밍 규칙에 맞게 고치세요: `LevelUp`, `boss_killed_at_9min`, `purchase-remove-ads`, `run_end` 파라미터 `Duration`(초 단위).

<details><summary>힌트·해설</summary>

`LevelUp` → `level_up` (소문자 snake_case). `boss_killed_at_9min` → `boss_kill { time_s: 540 }` (이름에 값 금지, 단위 접미사). `purchase-remove-ads` → `iap_purchase { product_id: "remove_ads" }` (하이픈 금지, 상품은 파라미터로 — 25장에서 씁니다). `Duration` → `duration_s`. 공통 원칙은 "이름은 적게, 파라미터로 구분"입니다. 이벤트 종류가 적을수록 대시보드와 집계가 단순해집니다.

</details>

**2. ★★☆ D1 리텐션 계산**
다음 `session_start` 기록(사용자, 날짜)으로 10/1 코호트의 D1 리텐션을 구하세요. A: 10/1, 10/2 / B: 10/1 / C: 10/1, 10/3 / D: 10/2, 10/3 / E: 10/1, 10/2, 10/2.

<details><summary>힌트·해설</summary>

10/1에 처음 실행한 사용자는 A, B, C, E (D는 10/2가 첫 실행이므로 10/2 코호트). 이 중 10/2에 실행한 사용자는 A, E. E의 10/2 두 번은 한 명으로 셉니다. D1 = 2 ÷ 4 = 50%. C는 10/3(D2)에 돌아왔지만 D1에는 포함되지 않습니다. 이것이 "정확히 n일째" 정의이며, 서비스에 따라 "n일째 또는 그 이후"(rolling) 정의를 쓰기도 하므로 비교할 때 정의를 맞춰야 합니다.

</details>

**3. ★★☆ D1 계산을 집계 도구에 추가**
`AnalyticsLocalReport`에 `session_start`의 `ts`(UTC ISO 8601)로 사용자별 첫 실행 날짜를 구하고, 코호트별 D1 리텐션을 출력하는 코드를 추가하세요.

<details><summary>힌트·해설</summary>

이미 `Row`에 있는 `local_date`(기기 현지 달력 날짜)를 `DateTime.ParseExact(r.local_date, "yyyy-MM-dd", CultureInfo.InvariantCulture)`로 읽습니다. `ts`(UTC)의 날짜를 쓰면 한국 사용자의 오전 플레이가 전날로 잡혀 D1이 틀어집니다. `session_start`만 골라 `user_id`별로 활동 날짜 집합(`HashSet<DateTime>`)을 만들고, `first_open`이 true인 기록의 날짜를 코호트 날짜로 삼아 `dates.Contains(cohort.AddDays(1))`인 사용자를 셉니다. 코호트 날짜 + 1일이 데이터의 마지막 날짜보다 뒤인 사용자는 아직 D1을 관측할 수 없으므로 분모에서 뺍니다. 모바일에서 앱을 끄지 않고 다음 날 돌아온 사용자도 `reason:"resume"` 세션으로 활동에 포함되는지 확인하세요. 로컬 플레이테스트는 인원이 적어 D1 자체는 의미가 약하지만, 출시 후 서비스 대시보드 수치와 정의가 같은지 검증하는 용도로 쓸 수 있습니다.

</details>

**4. ★★★ 내 게임의 테스트 사이클**
자기 게임(또는 코인 러시)으로 이 장의 전 과정을 수행하세요: 질문 3개 → 이벤트 사양 표 → 래퍼로 이벤트 심기 → 5인 계획서 → 실제 테스트 → 증상/원인/처방/검증 표 → 수정 → 새로운 5명으로 재테스트. 두 번의 결과를 같은 기준으로 비교한 보고서를 쓰세요.

<details><summary>힌트·해설</summary>

가장 어려운 부분은 "새로운 5명"을 구하는 것입니다. 첫 테스트 참가자는 이미 규칙을 알기 때문에 재테스트 대상이 아닙니다. 모집 경로(커뮤니티, 게임잼 동료, itch.io 페이지 댓글)를 2~3개 미리 확보하세요. 보고서에는 기준을 바꾸지 않았다는 것을 명시하고, 기준 자체가 잘못됐다고 판단되면 "기준 변경"을 별도 항목으로 이유와 함께 기록합니다.

</details>

**5. ★★☆ 콘텐츠 고갈 지표 설계**
코인 러시에 캐릭터 2종이 추가됐습니다(23장 연습 4). `first_seen`의 대상 목록을 어떻게 바꿔야 과거 데이터의 신규 경험 곡선이 끊기지 않는지 설명하고, 캐릭터별로 빌드가 갈라지는지 확인할 집계를 설계하세요.

<details><summary>힌트·해설</summary>

기존 `kind`(enemy/upgrade/unlock)의 **정의를 바꾸지 않고** `kind: "character"`를 추가합니다. 옛 세 종류의 분모는 그대로이므로 출시 전 곡선과 출시 후 곡선을 같은 기준으로 이어 붙일 수 있고, 전체 곡선은 세 종류 합과 네 종류 합을 **따로** 그립니다(같은 그래프에 섞으면 캐릭터 추가 시점에 인위적인 반등이 생깁니다). 빌드 비교는 `run_start`에 `character_id` 파라미터를 추가한 뒤 `AppendBuildDiversity`를 캐릭터별로 나눠 돌립니다. 볼 것은 두 가지입니다 — 같은 캐릭터 안의 판 유사도(그 캐릭터가 매 판 같은 빌드를 강요하는가)와 **캐릭터 사이의 유사도**(캐릭터를 바꿔도 같은 빌드가 나오면 캐릭터가 아니라 스킨입니다). 23장 연습 4의 "캐릭터별 클리어율 ±10%p" 기준과 함께 보면 파워 크립과 다양성을 동시에 판정할 수 있습니다.

</details>

**6. ★★★ 재측정 계획서 쓰기**
7-1단계의 "못 고침"(구매·모으기 전환 3/5)을 고치기 위한 0.4.3 수정안 하나와, 그 수정이 성공했는지 판정할 **테스트 전 기준**을 쓰세요. 기준에는 실패 조건(무엇이 나오면 이 가설을 버리는가)도 포함해야 합니다.

<details><summary>힌트·해설</summary>

수정안 예: "제단 창의 '모으기' 버튼 옆에 '이 판을 마치면 +N코인 → 공격력 5레벨까지 M코인 남음'을 상시 표시". 기준 예: (성공) 살 수 있었던 방문에서 구매와 모으기를 각각 한 번 이상 한 참가자 **4/5 이상**, 그중 3명 이상이 체력·지갑·다음 판 목표로 이유를 설명. (실패) 구매율이 20% 미만으로 떨어지거나(정보가 "사지 마라"로 읽힘) 전환 참가자가 여전히 3/5 이하. 실패 조건을 미리 쓰는 이유는 21장 그레이박스·29장 킬 기준과 같습니다 — 결과를 본 뒤 기준을 정하면 무엇이든 "개선"으로 읽을 수 있습니다. 두 번 연속 실패하면 정보 부족 가설을 버리고 **제단 자체의 트레이드오프 크기**(23장 `shrineStacks`·가격)를 다음 가설로 옮깁니다.

</details>

## 셀프 체크

**1. 플레이테스트 중 설명·도움을 금지하는 이유를 설명해보세요.**

<details><summary>모범 답안</summary>

출시 후 플레이어 옆에는 개발자가 없습니다. 테스트에서 설명하거나 도와주면 실제로는 존재하지 않는 조건에서 관찰하게 되어, 가장 중요한 발견인 "혼자서는 막히는 지점"을 지워버립니다. 막혀서 멈춘 시간과 그때의 발화가 곧 개선할 곳의 데이터이므로 기다리고 기록합니다.

</details>

**2. "증상은 믿고 처방은 의심하라"를 예를 들어 설명해보세요.**

<details><summary>모범 답안</summary>

플레이어는 자신이 느낀 불편(증상)은 정확히 보고하지만, 원인을 추론하고 해결책을 제시하는 설계자가 아닙니다. "적이 너무 세요, 약하게 해주세요"에서 믿을 것은 "특정 시점에 무력감을 느꼈다"는 증상입니다. 실제 원인은 직전의 성장 부족이나 위협 예고 부족일 수 있고, 적을 약화하면 다른 구간이 지루해질 수 있습니다. 그래서 증상의 시점과 빈도를 모아 원인 가설을 세우고, 처방과 검증 방법은 설계자가 정합니다.

</details>

**3. 게임 코드가 분석 SDK를 직접 호출하지 않고 `Analytics.Track` 래퍼만 호출하게 한 이유는?**

<details><summary>모범 답안</summary>

SDK를 바꾸거나 여러 서비스에 동시에 보내거나 테스트 중에는 파일로만 기록하는 결정을 게임 코드 수정 없이 백엔드 등록만으로 할 수 있습니다. 또 이름 규칙 검증, 공통 필드 부착, 동의 확인을 한 곳에서 강제할 수 있고, SDK 버전 업데이트로 API가 바뀌어도 수정 범위가 백엔드 구현 하나로 줄어듭니다.

</details>

**4. D1과 D7 리텐션은 각각 게임의 어떤 부분을 주로 반영하나요?**

<details><summary>모범 답안</summary>

D1은 첫 실행 다음 날 돌아온 비율이라 첫인상, 온보딩, 첫 세션의 재미를 주로 반영합니다. D7은 일주일 뒤에도 돌아온 비율이라 메타 루프(영구 강화, 해금 목표)처럼 "다시 올 이유"의 건강을 보여줍니다. 두 수치 모두 정의(정확히 n일째인지, 이후 아무 날인지)와 코호트 기준이 같아야 비교할 수 있습니다.

</details>

**5. 이벤트를 설계할 때 "판단 기준"을 데이터 수집 전에 정해야 하는 이유는?**

<details><summary>모범 답안</summary>

데이터를 본 뒤 기준을 정하면 원하는 결론에 맞춰 해석하게 됩니다. 미리 "한 분에 사망 30% 이상이면 웨이브 조정"처럼 정해두면 결과가 나왔을 때 행동이 자동으로 결정되고, 그 기준을 계산하는 데 필요한 파라미터가 빠졌는지도 수집 전에 확인할 수 있습니다.

</details>

**6. "몇 판째에 새로움이 끝나는가"를 5인 대면 테스트에서 재려고 합니다. 세 지표 중 무엇을 쓰고 무엇을 쓰면 안 되나요?**

<details><summary>모범 답안</summary>

쓸 수 있는 것은 **판당 신규 경험 비율**(그 판의 `first_seen` ÷ 누적)과 **빌드 유사도**입니다. 둘 다 한 사람이 몇 판을 했는지와 비교적 무관하게 "판이 거듭될수록 어떻게 변하는가"를 보여 주기 때문입니다. 쓰면 안 되는 것은 **판 수별 진행률**입니다. 대면 테스트는 자유 플레이 시간이 정해져 있어 3판에서 끝난 것이 재미가 아니라 **일정** 때문이고, 이것을 이탈률로 읽으면 없는 문제를 만들어 냅니다. 판 수별 진행률은 세션 길이를 통제하지 않는 표본(데모·출시 로그, 수백 명)에서만 의미가 있고, 그 값이 35장 게이트 L3의 재방문 판정 재료가 됩니다.

</details>

**7. 수정 후 재측정에서 "안 바뀐 것"을 따로 적는 이유는?**

<details><summary>모범 답안</summary>

바뀐 것만 적으면 모든 사이클이 성공으로 보이고, 실제로는 **다른 축의 문제가 그대로 남아 있다는 정보**를 잃습니다. 코인 러시 0.4.2에서는 빌드 유사도가 0.91 → 0.74로 갈라졌지만 신규 경험 비율(2판째 23% → 21%)은 그대로였습니다. 수정 어느 것도 "볼 것"을 늘리지 않았으니 당연한 결과이고, 이것을 적어 두어야 "조합 다양성"과 "콘텐츠 양"이 다른 축이라는 것을 다음 사이클에서 잊지 않습니다. 또 주 기준이 미달인데 보조 지표가 통과했을 때(구매율 42% 통과, 구매·모으기 전환 3/5 미달) 미달을 명시해야 같은 문제로 세 번째 테스트를 낭비하지 않습니다. 보고서를 "고침 / 못 고침 / 안 변함 / 새 증상" 네 칸으로 고정하면 강제됩니다.

</details>

## 핵심 요약

- 플레이테스트는 "왜", 애널리틱스는 "얼마나"를 알려주며 서로의 빈틈을 채웁니다.
- 5명 정도의 낯선 타깃 테스터를 여러 번 반복하는 것이 효율적이며, 설명·도움 금지, Think-aloud, 녹화가 기본 규칙입니다.
- 설문은 유도하지 않는 열린 질문과 "한 판 더" 같은 행동 관찰을 함께 씁니다. 피드백은 증상과 처방을 나누어 해석합니다.
- 애널리틱스는 질문 → 측정값 → 이벤트 → 판단 기준 순서로 설계하고, 출시 전에 심습니다.
- 이벤트 이름은 소문자 snake_case, 값은 이름이 아닌 파라미터로, 단위는 접미사로 표기하고 출시 후에는 바꾸지 않습니다.
- 퍼널은 사용자별 시각순으로 "이전 단계 이후"만 인정하고 관측 기간을 적용하며, 순서가 강제되지 않는 행동은 분기로 따로 셉니다. 리텐션은 세션·날짜 정의(복귀 세션, 현지 날짜)와 코호트를 맞춰 비교합니다.
- 선택 쏠림은 제시율·조건부 선택률·점유율을 따로 보고, 처방은 "제시 빈도"가 아니라 "선택의 가치"를 조정합니다.
- 콘텐츠 고갈은 **판 수별 진행률 · 판당 신규 경험 비율 · 빌드 유사도** 세 가지로 재고, 표본이 지표를 고릅니다. 세션 길이가 정해진 대면 테스트에서 판 수별 진행률을 이탈로 읽으면 안 됩니다.
- 빌드 다양성의 정의(코사인 유사도)는 23장 `BuildProfile.Similarity`를 그대로 씁니다. 시뮬레이터와 로그 집계가 같은 규칙을 쓸 때만 두 결과를 나란히 놓을 수 있습니다.
- 한 사이클은 증상 → 진단 → 수정 → **재측정**까지입니다. 보고서는 **고침 / 못 고침 / 안 변함 / 새 증상** 네 칸으로 고정하고, 주 기준이 미달이면 보조 지표가 통과해도 미달로 적습니다.
- 사람에게는 수정을 묶어서 배포할 수밖에 없으므로, 상수 단위의 기여는 23장 시뮬레이터 기록으로만 말하고 플레이테스트 보고서에는 "묶음의 효과"라고 밝힙니다.
- 여기서 만든 지표가 35장 게이트 L2(완주율·재방문 행동·추천 의향)와 L3(데모 완주율·7일 재방문)의 계산 재료입니다.
- `Analytics` 정적 래퍼 뒤에 백엔드를 숨기면 로컬 JSONL과 실제 SDK를 자유롭게 바꿀 수 있고, 동의·이름 규칙·공통 필드를 한 곳에서 강제합니다.
- 동의 전에는 수집하지 않고, 최소 수집, 철회 시 대기 데이터 폐기와 이후 수집 중단, 저장 데이터 삭제 방법, 스토어 개인정보 양식 반영을 지킵니다.

## 더 읽을거리

- Nielsen Norman Group, "Why You Only Need to Test with 5 Users": https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/
- Steamworks 문서 — Steam Playtest: https://partner.steamgames.com/doc/features/playtest
- Apple — TestFlight: https://developer.apple.com/testflight/
- Google Play Console 도움말 — 내부 테스트, 비공개 테스트, 공개 테스트 설정
- Unity 매뉴얼 — Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
