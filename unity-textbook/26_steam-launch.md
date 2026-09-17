# 26. Steam 출시 실전 — Steamworks·스토어 페이지·SteamPipe

> **이 장에서 배울 것**
> - Steamworks 가입부터 출시 버튼까지의 행정 절차와 소요 기간을 역산해 일정표를 만들 수 있다
> - 캡슐 이미지·짧은 설명·태그·트레일러로 구성된 스토어 페이지를 목적에 맞게 작성한다
> - 가격·지역 가격·출시 할인·얼리 액세스 여부를 근거를 들어 결정할 수 있다
> - Steamworks.NET 으로 초기화·업적·Steam Cloud·오버레이를 연동하고, 모바일 빌드에서는 제외되게 구현한다
> - steamcmd 와 app_build VDF 로 빌드를 업로드하고 브랜치로 테스트 배포를 한다
>
> **선수 장**: 10, 19, 21, 25 · **예상 시간**: 5~6시간 (행정 대기 시간 제외) · **코인 러시 진행**: Steam 업적 10개, Steam 계정별 Steam Cloud 세이브, 완성된 스토어 페이지 문안과 D-180 ~ D+30 출시 체크리스트

> ⚠️ 이 장의 금액·기간·이미지 규격·수수료는 2026년 기준으로 알려진 내용이며 Valve 정책에 따라 바뀔 수 있습니다. 실제 제출 전에는 반드시 Steamworks 문서(partner.steamgames.com/doc)에서 현재 값을 확인하세요.

## 왜 필요한가

25장까지 코인 러시는 "게임"으로서는 거의 완성됐습니다. 그런데 Steam 에 올리려고 하면 이런 일이 벌어집니다.

```
D-14  "이제 스토어 페이지 만들어야지" → 캡슐 이미지가 없음 → 외주 견적 2주
D-10  세금 인터뷰에서 영문 주소·계좌 SWIFT 코드를 몰라 중단
D-7   스토어 페이지 검토 제출 → 반려(캡슐에 리뷰 인용 문구가 들어감) → 재제출
D-3   "Coming Soon 은 최소 2주 공개돼야 출시 가능" 규칙을 처음 알게 됨
D-0   출시 불가. 게다가 위시리스트 0 → 출시일 알림을 받을 사람도 0
```

Steam 출시는 버튼 하나가 아니라 **수개월 전부터 시작되는 행정 + 마케팅 + 기술 작업의 묶음**입니다. 웹 배포로 치면 "도메인 등록 → 사업자 인증 → 결제 PG 심사 → 랜딩 페이지 → CI 배포"를 한꺼번에 하는 것과 비슷합니다. 이 장은 그 전체를 역산 가능한 체크리스트로 바꾸고, 필요한 코드(업적·클라우드·오버레이·빌드 업로드)를 코인 러시에 붙입니다.

## 개념

### Steamworks 가입과 Steam Direct

Steam 에 게임을 내려면 Steamworks(파트너 사이트)에 가입하고 **Steam Direct 수수료**를 내야 합니다.

| 항목 | 내용 (2026년 기준, 변경 가능) |
|---|---|
| 앱 등록비 | 앱(게임) 하나당 **$100** |
| 환급 | 해당 앱의 조정 총매출이 **$1,000** 에 도달하면 이후 정산에서 환급 |
| 기본 수수료 | 매출의 30% (누적 매출이 매우 커지면 구간별로 낮아짐 — 인디에겐 30%로 계산) |
| 신규 파트너 대기 | 첫 앱은 등록비 결제 후 일정 기간이 지나야 출시 가능 (현재 기간은 Steamworks 문서 확인) |
| 필요한 정보 | 법적 이름(개인 또는 사업자), 주소, 은행 계좌, 세금 정보, 본인 확인 |

가입 절차는 다음 순서입니다.

1. Steam 계정으로 partner.steamgames.com 에 로그인해 **Steamworks 가입**을 시작합니다.
2. 이용 계약(Steam Distribution Agreement)에 동의합니다. 개인으로 할지 사업자로 할지 이 단계에서 이름을 정하게 되므로 [28장](./28_business-law-tax-kr.md)의 사업자 등록 판단을 먼저 해두는 것이 좋습니다.
3. **은행 정보**: 은행명, 계좌번호, SWIFT(BIC) 코드, 은행 주소를 영문으로 입력합니다. 외화 입금이 되는 계좌인지 은행에 미리 물어보세요.
4. **세금 인터뷰**: 미국 세법상 비미국인임을 신고하는 절차입니다. 개인은 보통 W-8BEN, 법인은 W-8BEN-E 양식이 온라인으로 작성됩니다. 한국 거주자는 한미 조세조약 적용을 주장할 수 있고 이 경우 원천징수율이 달라집니다(구체 세율 판단은 28장과 세무사).
5. **본인 확인**과 **Steam Direct 결제**($100)를 합니다.
6. 앱 ID 가 발급되면 스토어 페이지와 빌드 작업을 시작할 수 있습니다.

> 대기 기간이 있으므로 **가입은 출시 6개월 전**에 끝내는 것을 권장합니다. 가입 자체는 무료로 몇 시간이지만, 은행·세금 정보 검증에서 막히면 며칠씩 걸립니다.

### 스토어 페이지 구성 요소

스토어 페이지는 **"이 게임이 무엇이고 왜 사야 하는가"를 3초, 30초, 3분 단위로 답하는 문서**입니다.

```
[검색 결과·추천 목록]  ── 캡슐 이미지 + 이름 + 가격        (0.5초: 클릭할까?)
        │
[스토어 페이지 상단]   ── 트레일러 자동재생 + 스크린샷 + 짧은 설명 + 태그   (3~30초: 내 취향인가?)
        │
[스크롤 아래]          ── 긴 설명(GIF 포함) + 시스템 사양 + 리뷰           (3분: 살 만한가?)
        │
[위시리스트 버튼]      ── 출시 전 목표 행동
```

**캡슐 이미지**는 노출 위치마다 규격이 다릅니다. 2024년에 규격이 개편됐으니 아래는 개념 이해용이며, 업로드 화면의 최신 규격을 따르세요.

| 에셋 | 대략적 규격 | 쓰이는 곳 | 핵심 |
|---|---|---|---|
| Header Capsule | 920×430 | 스토어 페이지 상단, 추천 목록 | 로고가 읽혀야 함 |
| Small Capsule | 462×174 | 검색 결과, 작은 목록 | 로고만 크게. 작게 줄여도 읽혀야 함 |
| Main Capsule | 1232×706 | 스토어 첫 화면 대형 노출 | 분위기 + 로고 |
| Vertical Capsule | 748×896 | 세일 페이지 등 세로 배치 | 세로 구도 별도 설계 |
| Library Capsule | 600×900 | 사용자 라이브러리 | 책 표지처럼 |
| Library Hero / Logo | 3840×1240 / 로고 PNG | 라이브러리 상세 | 히어로에 글자 넣지 않기 |
| Page Background | 선택 | 스토어 배경 | 은은하게 |

규칙 몇 가지는 반드시 기억하세요. 캡슐에는 **게임 이름(로고) 외의 문구**(리뷰 인용, "할인!", 수상 내역 등)를 넣지 않는 것이 원칙이며 검토에서 반려됩니다. 캡슐의 그림은 게임의 실제 분위기와 맞아야 합니다.

**짧은 설명(Short Description)** 은 헤더 오른쪽의 몇 줄입니다. 글자 수 제한이 있으니(대략 300자 안팎, 입력 화면 확인) 장르·핵심 동사·차별점을 한 번에 담습니다.

**긴 설명(About This Game)** 은 BBCode 형식으로 제목·목록·이미지(GIF)를 넣을 수 있습니다. 텍스트 덩어리보다 "짧은 문단 → GIF → 특징 목록" 반복이 잘 읽힙니다.

**스크린샷**은 최소 5장 이상을 요구하며 1920×1080 이상 16:9 권장입니다. 첫 4장이 상단에 보이므로 가장 강한 장면을 앞에 둡니다. 메뉴 화면·아트 콘셉트·로고 이미지는 스크린샷으로 올리지 않습니다(실제 게임 화면이어야 함).

**트레일러**는 페이지에 들어오면 자동 재생되는 첫 영상입니다. 첫 5초에 게임플레이를 보여줍니다(27장에서 샷 리스트를 만듭니다).

**태그**는 개발자가 여러 개(최대 20개 내외)를 순서대로 지정하며, 앞쪽 태그일수록 비중이 큽니다. Steam 추천 알고리즘은 태그로 "이 게임을 좋아할 사람"을 찾으므로 **정확한 장르 태그 → 하위 장르 → 분위기·특징** 순으로 넣습니다. "Indie", "Casual" 같은 넓은 태그를 맨 앞에 두면 비슷한 게임을 좋아하는 사람에게 노출되지 않습니다.

### Coming Soon 페이지와 위시리스트

Steam 에서 **위시리스트는 판매의 선행 지표**입니다. 위시리스트에 담은 사용자는 출시·할인 때 이메일과 알림을 받습니다.

```
Coming Soon 공개 ──► 위시리스트 누적 ──► 출시일 알림 ──► 첫 주 판매·플레이 ──► 추가 추천 노출
     (일찍)            (수개월)            (자동)          (리뷰 발생)            (보장 아님)
```

순서를 정확히 구분하세요. Valve 문서에 따르면 위시리스트는 "인기 출시 예정" 탭 같은 일부 영역을 빼면 **알고리즘 노출 요인이 아니고**, 노출을 받기 위한 최소 위시리스트 수도 없습니다. 위시리스트의 힘은 **출시·할인 알림으로 첫 구매자를 데려오는 것**입니다. 정식 출시작은 기본적으로 신규 출시 대기열에 노출되고, 그 뒤 추천 영역에 뜨는지는 사용자 취향·플레이·판매 반응에 달려 있습니다. 리뷰 점수는 "복합적(40%)" 이상이면 알고리즘 노출 요인이 아니며, 주로 **구매를 망설이는 사람의 판단 근거**로 작용합니다.

- Coming Soon 페이지는 **출시 수개월~1년 전**에 공개하는 것이 일반적입니다. 공개가 늦을수록 위시리스트를 모을 시간이 줄어듭니다.
- 스토어 페이지는 출시 전에 **최소 2주 이상 Coming Soon 상태로 공개**되어 있어야 출시할 수 있습니다.
- 스토어 페이지와 빌드는 각각 Valve 의 **검토**를 받습니다. 검토에는 영업일 기준 며칠이 걸리고 반려되면 다시 기다려야 하므로, **페이지는 공개 희망일 3~4주 전, 빌드는 출시 희망일 1개월 전**에 제출할 여유를 두세요.

### 데모와 Steam Next Fest

Steam Next Fest 는 **연 3회**(보통 2월, 6월, 10월) 열리는 무료 데모 축제입니다. 출시 전 게임만 참가할 수 있고, 한 게임이 참가할 수 있는 횟수에 제한이 있으니 **가장 준비된 시점**에 한 번 쓰는 것이 좋습니다.

- **데모**: 별도 앱 ID 로 만드는 무료 체험판으로 본편 페이지에 연결됩니다. Next Fest 참가와 위시리스트 전환에 씁니다.
- **Playtest**: 신청자에게 접근 권한을 주는 테스트 앱입니다. 출시 전 대규모 테스트([24장](./24_playtest-analytics.md))에 씁니다.
- **얼리 액세스**: 미완성 상태로 유료 출시한 뒤 업데이트합니다(아래 판단 기준).

데모는 "게임의 1/3 을 잘라주기"가 아니라 **가장 재미있는 15~30분을 끝에서 끊어 위시리스트로 유도**하는 설계입니다. 데모 끝 화면에 "위시리스트에 추가" 버튼(오버레이로 스토어 열기)을 넣습니다.

Next Fest 등록 신청 마감은 행사 수개월 전이니 Steamworks 의 이벤트 페이지에서 일정을 확인하세요.

### 가격 책정

가격은 느낌이 아니라 **비교군**으로 정합니다.

1. 태그·플레이 시간·그래픽 수준이 비슷한 게임 5~10개를 SteamDB 등에서 찾습니다.
2. 그 게임들의 **출시 당시 가격**(현재 할인가가 아님)과 리뷰 수를 표로 정리합니다.
3. 내 게임의 콘텐츠 분량(플레이 시간, 캐릭터 수)이 비교군 중 어디쯤인지 위치를 정합니다.
4. 기준 통화(USD)로 가격을 정하고 Steamworks 의 **지역 가격 추천값(Recommended Pricing)** 을 적용합니다. 추천값은 각 지역 구매력을 반영하며, 특별한 이유가 없다면 그대로 쓰는 것이 안전합니다.
5. 출시 할인(Launch Discount)을 정합니다. 할인율 상한·할인 사이 쿨다운 같은 규칙이 있으니 Steamworks 의 할인 문서를 확인합니다.

너무 싸게 매기면 "품질이 낮다"는 신호가 되고 이후 세일 여지도 사라집니다. 너무 비싸면 비교군 대비 콘텐츠 부족 리뷰가 달립니다.

### 얼리 액세스 판단

얼리 액세스가 맞는 경우는 **코어 루프가 이미 재미있고 수 시간 플레이 가능하며**, 로그라이크·샌드박스처럼 커뮤니티 피드백으로 콘텐츠를 늘리는 구조이고, 1~2년 업데이트와 공개 로드맵을 감당할 재정·멘탈이 있을 때입니다. 코어 루프가 검증되지 않았거나, 한 번 깨면 끝나는 스토리 중심 구조이거나, "돈이 급해서" 미완성으로 파는 경우는 맞지 않습니다.

노출 규칙과 판매 기대를 구분하세요. Valve 는 얼리 액세스를 끝내고 정식 출시하면 **처음 정식 출시하는 게임과 같은 출시 노출 지침**이 적용된다고 밝힙니다. 노출 기회 자체가 사라지지는 않습니다. 다만 얼리 액세스 기간에 살 사람이 이미 샀다면 1.0 에서 판매가 크게 뛰지 않을 수 있고, Valve 도 결과는 게임에 따라 크게 다르다고 설명합니다. 얼리 액세스 출시 첫 주의 리뷰·환불도 1.0 까지 페이지에 남습니다. 3~6개월짜리 작은 게임은 업데이트 로드맵을 1~2년 유지할 이유가 없으므로 보통 정식 출시가 맞습니다.

### 리뷰 시스템

Steam 은 사용자 리뷰의 긍정 비율과 리뷰 수로 요약 등급을 표시합니다. 리뷰가 **10개 미만이면 등급 대신 리뷰 수만** 보이고, 수가 늘어야 "매우 긍정적" 같은 상위 등급이 붙습니다.

예를 들어 긍정 80% 이상이라도 리뷰가 10~49개면 "Positive", 50~499개면 "Very Positive", 95% 이상에 500개 이상이면 "Overwhelmingly Positive" 처럼 리뷰 수 구간이 등급 상한을 정합니다. 70%대는 "Mostly Positive", 40~69%는 "Mixed" 입니다.

(구간 규칙은 Valve 가 바꿀 수 있습니다.) 실무적 결론은 두 가지입니다. **첫 주에 리뷰 10개를 넘기는 것**이 첫 목표이고, 초기 부정 리뷰의 원인(크래시, 해상도, 조작)은 **48시간 안에 핫픽스**해야 합니다. 개발자는 리뷰에 공개 답변을 달 수 있습니다. Steam 은 구매 후 14일 이내·플레이 2시간 미만이면 환불을 받아주므로, 첫 2시간 경험이 특히 중요합니다.

### 출시 후 세일 캘린더

Steam 은 매년 계절 세일(봄·여름·가을·겨울)과 테마 축제(장르별 Fest)를 엽니다. 참가 신청은 Steamworks 의 **마케팅 → 할인 / 이벤트** 메뉴에서 하며, 정확한 날짜는 매년 Valve 가 공지합니다.

할인 사이에는 쿨다운 기간이 있어 아무 때나 세일할 수 없습니다. 연간 캘린더를 먼저 그리고 "대형 업데이트 직후 세일"처럼 묶으면 효과가 커집니다.

### Steamworks.NET 과 초기화

Steamworks SDK 는 C++ 라이브러리입니다. Unity 에서는 오픈소스 C# 래퍼인 **Steamworks.NET** 이 가장 널리 쓰입니다.

- 설치: Package Manager → `+` → **Install package from git URL** → `https://github.com/rlabrecque/Steamworks.NET.git?path=/com.rlabrecque.steamworks.net#2025.164.1`
  - 이 장의 코드는 **Steamworks.NET 2025.164.1 (Steamworks SDK 1.64)** 기준입니다. `#` 뒤 태그를 빼면 설치할 때마다 최신 커밋이 들어와 API 가 달라질 수 있으니 반드시 태그를 붙입니다. 더 새 버전으로 올릴 때는 릴리스 노트를 읽고 이 장의 코드를 다시 컴파일해 확인합니다.
- 프로젝트 루트(Assets 옆)에 `steam_appid.txt` 파일을 만들고 앱 ID 숫자만 적습니다. 에디터·개발 빌드가 Steam 없이 실행될 때 이 앱 ID 를 쓰게 합니다. **출시 빌드에는 포함하지 않습니다.**
- 테스트 중에는 Steam 클라이언트가 실행 중이고 해당 앱을 소유한 계정으로 로그인되어 있어야 합니다. 앱 ID 가 없다면 Valve 의 예제 앱 ID `480`(Spacewar)으로 연습할 수 있습니다.

초기화의 핵심 API 는 네 개입니다.

| API | 역할 | JS 비유 |
|---|---|---|
| `SteamAPI.RestartAppIfNecessary(appId)` | Steam 밖에서 exe 를 직접 실행하면 Steam 을 통해 재실행 | 로그인 안 됐으면 로그인 페이지로 리다이렉트 |
| `SteamAPI.Init()` | Steam 클라이언트와 연결. 실패하면 false | SDK `init()` |
| `SteamAPI.RunCallbacks()` | 비동기 결과(콜백)를 메인 스레드로 전달. 매 프레임 호출 | 이벤트 루프 틱 |
| `SteamAPI.Shutdown()` | 종료 시 정리 | `dispose()` |

코인 러시의 1차 출시는 Steam 유료판이고, 모바일 무료판은 출시 뒤 별도 확장 트랙입니다([25장](./25_monetization.md)). 그래도 같은 프로젝트에서 모바일 빌드를 만들 수 있어야 하므로, Steamworks 코드는 **데스크톱 플랫폼에서만 컴파일**되게 해야 합니다. Steamworks.NET 은 내부적으로 `DISABLESTEAMWORKS` 심볼을 쓰는데, 우리 스크립트도 파일 맨 위에서 같은 조건으로 정의합니다.

### 업적(Achievements)과 통계(Stats)

업적은 Steamworks 관리 화면(App Admin → Stats & Achievements)에서 **API 이름**(예: `ACH_FIRST_RUN`)·표시 이름·설명·아이콘(달성/미달성)을 등록하고, **Publish** 해야 클라이언트에서 쓸 수 있습니다.

- `SetAchievement` 만 부르면 팝업이 뜨지 않고 저장도 확정되지 않습니다. **`StoreStats` 를 반드시 호출**하되, 매 프레임 부르지 말고 판 종료·업적 달성 시점에만 부릅니다. Valve 문서는 호출 빈도가 "초 단위가 아니라 분 단위"여야 하며 제한(rate limit)이 걸릴 수 있다고 안내합니다.
- `StoreStats` 가 `false` 를 반환하면 **아무것도 서버로 전송되지 않은 것**입니다. 성공(`true`)도 "요청을 보냈다"는 뜻일 뿐이고, 실제 결과는 `UserStatsStored_t` 콜백의 `m_eResult` 로 옵니다. 그래서 "보낼 변경이 남았는가"를 결과 콜백을 받을 때까지 지우지 않고, 실패하면 간격을 두고 다시 시도해야 합니다. `SetStat`·`SetAchievement` 도 이름이 틀렸거나 Publish 되지 않았거나 타입이 다르면 `false` 를 반환합니다.
- "적 1000마리 처치"처럼 누적 값이 필요한 업적은 **통계(Stat)** 를 정의하고 `SetStat` 으로 올립니다. 관리 화면에서 업적을 통계에 연결하면 값이 기준을 넘을 때 자동 달성됩니다.
- `SteamUserStats.RequestCurrentStats()` 는 공식 문서에서 폐기(deprecated)됐습니다. Steam 클라이언트가 게임 실행 전에 통계·업적을 불러오므로, 이 장이 고정한 버전에서는 호출하지 않습니다(오래된 예제 코드에 있어도 따라 넣지 마세요).
- 테스트 중 초기화는 `SteamUserStats.ResetAllStats(true)` 로 합니다(개발 계정에서만).

### Steam Cloud — Auto-Cloud vs API

방식은 두 가지입니다. **Auto-Cloud** 는 App Admin → Steam Cloud 에서 할당량과 **루트 경로 + 하위 폴더 + 파일 패턴**만 지정하면 코드 변경 없이 동기화되므로 [10장](./10_save-system.md)처럼 로컬 JSON 파일로 저장하는 게임에 맞습니다. **Remote Storage API** 는 `SteamRemoteStorage.FileWrite/FileRead` 를 직접 호출해 저장 시점을 제어하고 싶을 때 씁니다.

Unity 의 `Application.persistentDataPath` 는 Windows 에서 `%USERPROFILE%\AppData\LocalLow\<회사명>\<제품명>` 입니다. Auto-Cloud 에서 Windows 루트를 **AppData LocalLow** 계열로 고르고 하위 경로를 `<회사명>/<제품명>/{64BitSteamID}`, 패턴을 `*.json` 으로 지정합니다.

여기서 `{64BitSteamID}` 가 중요합니다. 한 PC·한 OS 계정에서 **Steam 계정만 바꿔 로그인**하는 경우(가족·형제)가 흔합니다. 10장 `SaveSystem` 은 `persistentDataPath` 바로 아래 `save.json` 하나를 쓰므로, 그대로 두면 B 계정이 A 계정의 진행도를 읽고 덮어쓰며, 그 파일이 B 의 클라우드로 올라갑니다. Valve 문서도 여러 사용자가 한 기기를 쓰는 경우를 위해 경로에 `{64BitSteamID}` 같은 사용자 변수를 쓰도록 안내합니다. 그래서 7단계에서 **Steam 초기화 → SteamID 로 세이브 폴더 결정 → 세이브 로드** 순서가 되도록 10장 `SaveSystem` 을 조금 고칩니다. macOS·Linux 는 경로가 다르므로 **Root Overrides** 로 매핑합니다(선택지 이름은 설정 화면에서 확인). Auto-Cloud 는 게임이 **시작되기 전에 내려받고 종료 후에 올리므로**, 게임 실행 중 저장 파일을 새로 읽는 구조가 아니면 추가 작업이 없습니다.

충돌 시(두 PC 에서 따로 플레이) Steam 이 사용자에게 어느 쪽을 쓸지 묻습니다. 10장의 `version` 필드가 있으니 오래된 세이브가 선택돼도 마이그레이션으로 읽을 수 있습니다.

### 오버레이

Shift+Tab 오버레이는 Steam 이 게임 렌더링 위에 그리는 UI 입니다. 게임에서 할 일은 세 가지입니다.

1. 오버레이가 열리면 **게임을 일시정지**합니다(`GameOverlayActivated_t` 콜백). 레벨업 선택 창처럼 이미 멈춘 화면에서는 일시정지를 겹쳐 걸지 않습니다.
2. 데모에서 "위시리스트 추가" 버튼이 **오버레이로 스토어 페이지를 열게** 합니다(`SteamFriends.ActivateGameOverlayToStore`).
3. 외부 링크(디스코드, 설문)는 `SteamFriends.ActivateGameOverlayToWebPage` 로 엽니다. 브라우저를 띄워 창을 빠져나가는 것보다 이탈이 적습니다.

### Steam Deck 대응

Steam Deck 호환성 검토 결과는 **Verified / Playable / Unsupported / Unknown** 으로 표시되며, Verified 는 Deck 사용자에게 노출상 이점이 있습니다. Valve 의 주요 검토 항목은 다음과 같습니다.

- **입력**: 모든 기능이 게임패드로 가능해야 합니다([08장](./08_input-system.md) 액션 맵). 첫 실행 화면부터 마우스가 필요 없어야 하고, 패드 사용 중엔 패드 버튼 아이콘을 표시합니다.
- **화면(필수)**: Steam Deck 이 지원하는 해상도로 실행돼야 하며, Valve 는 **1280×800(권장)** 또는 **1280×720** 을 제시합니다. 16:9 게임을 1280×720 으로 위아래 여백과 함께 보여줘도 그 자체로 부적합은 아닙니다.
- **화면(이 교재의 품질 기준)**: 코인 러시는 16:10 에서 UI 를 화면 끝까지 앵커로 배치해 여백 없이 보이게 합니다([11장](./11_ui.md) 앵커). 필수 조건이 아니라 7인치 화면을 넓게 쓰기 위한 선택입니다.
- **성능(필수)**: 기본 설정 그대로 플레이 가능한 프레임이 나와야 하며, Steam Deck 기준은 **800p 에서 30fps** 입니다. 코인 러시는 18장에서 정한 목표 프레임을 유지하되, 적이 가장 많은 구간이 Deck 에서 30fps 아래로 떨어지지 않는지 실기기로 확인합니다.
- **가독성**: 공식 기준은 1280×800 에서 가장 작은 글자가 **9픽셀 이상**이고, 가능하면 12픽셀을 권장합니다. 값은 바뀔 수 있으니 호환성 문서에서 확인합니다.
- **시스템**: 텍스트 입력이 있다면 가상 키보드 호출, 실행 시 호환성 경고·런처 없음.

코드에서 Deck 여부는 `SteamUtils.IsSteamRunningOnSteamDeck()` 로 확인할 수 있습니다. 다만 "Deck 이면 다르게"보다 **"게임패드 입력이면 패드 UI, 16:10 이면 그에 맞는 레이아웃"** 처럼 조건 자체로 분기하는 편이 다른 휴대 PC 에서도 동작합니다.

### SteamPipe — 빌드 업로드

SteamPipe 는 Steam 의 콘텐츠 배포 시스템입니다. 구조를 먼저 이해하세요.

```
App (앱 ID 3xxxxx0)                ← 스토어 상품 하나
 └─ Depot (3xxxxx1: Windows 빌드)  ← 파일 묶음. OS·언어별로 나눌 수 있음
 └─ Depot (3xxxxx2: macOS 빌드)
Build  = 특정 시점에 업로드한 Depot 들의 스냅샷 (빌드 ID)
Branch = 어떤 Build 를 누구에게 줄지 가리키는 포인터
         default(모든 구매자) / beta(비밀번호) / 내부 테스트용
```

웹 배포로 치면 Depot 은 아티팩트, Build 는 릴리스, Branch 는 "production / staging 에 어떤 릴리스를 연결할지"입니다.

업로드 도구는 Steamworks SDK 의 `tools/ContentBuilder` 안에 있는 **steamcmd** 입니다. 빌드 스크립트(VDF)를 넘겨 실행합니다.

```
steamcmd +login <빌드계정> +run_app_build <app_build VDF 의 절대 경로> +quit
```

- 빌드 업로드 전용 Steam 계정을 따로 만들고 Steamworks 에서 최소 권한만 주는 것을 권장합니다. 첫 로그인 때 Steam Guard 코드가 필요합니다.
- VDF 의 `SetLive` 로 업로드 직후 특정 브랜치에 적용할 수 있습니다. 단 **default 브랜치 적용은 보안상 Steamworks 웹사이트에서 직접** 하도록 되어 있으니, 스크립트는 `beta` 같은 브랜치에만 올리고 확인 후 웹에서 default 로 옮깁니다.

## 실습: 코인 러시에 적용하기

### 1단계 — 스토어 페이지 문안 완성본

아래는 코인 러시의 실제 제출용 문안입니다. 내용은 [21장](./21_core-loop-gdd.md) 1페이지 기획서(정본)의 훅과 v1.0 스코프(맵 1 · 적 4 + 엘리트 1 + 보스 1 · 무기 6 · 패시브 10 · 캐릭터 3 · 영구 강화 3종 × 10레벨 · 제단 강화 8종)를 그대로 옮긴 것입니다. 스토어 페이지에는 **출시 빌드에 실제로 들어간 기능만** 적어야 하므로(Valve 검토 기준), 기획서와 문안이 어긋나면 문안이 아니라 둘 중 틀린 쪽을 먼저 고칩니다. 자기 게임에 맞춰 같은 구조로 쓰세요.

**게임 이름**: Coin Rush (한국어 표기: 코인 러시)

**짧은 설명 — 영어** (27장에서 고른 훅 문장 A 를 첫 문장으로)

```
A survivor-like where every coin is both XP and savings. Spend it at altars to survive this run,
or bank it for permanent upgrades. Your weapons fire on their own — you move, collect, and decide.
```

**짧은 설명 — 한국어**

```
코인이 곧 경험치이자 저축인 서바이버라이크. 제단에서 써서 이번 판을 버틸까, 모아서 영구 강화를 살까?
공격은 자동, 당신은 움직이고 줍고 결정합니다. 한 판은 10분.
```

**긴 설명 — 영어 (BBCode)**

```
[h2]Spend it now, or save it for later?[/h2]
Coin Rush is a bite-sized survivor-like. Move to dodge, walk over coins to level up, and let your
weapons do the shooting. Every two minutes a Coin Altar appears — pay coins for a powerful upgrade
right now, or walk past it and carry every coin you keep into permanent upgrades for the next run.

[img]{STEAM_APP_IMAGE}/extras/rush_gif_01.gif[/img]

[h2]Build your run[/h2]
[list]
[*] 6 weapons and 10 passive upgrades — choose one of three every level
[*] 8 altar upgrades that tempt you to spend the coins you were saving
[*] 3 characters and 3 permanent upgrades with 10 levels each
[*] One map, four enemy types, an elite and a boss in a 10-minute run
[*] 10 Steam Achievements, Steam Cloud saves, full controller support and a Steam Deck friendly UI
[/list]
```

**긴 설명 — 한국어**: 영어 구조를 그대로 번역하되, 한국어 스토어 페이지는 Steamworks 스토어 페이지 편집의 언어 선택에서 **따로 입력**해야 한국어 사용자에게 보입니다.

**태그 (우선순위 순)**: ① Bullet Heaven(가장 정확한 장르명) ② Roguelite(영구 강화) ③ Action Roguelike(인접 장르) ④ Top-Down ⑤ 2D ⑥ Pixel Graphics(실제 스타일에 맞게) ⑦ Replay Value ⑧ Controller(Deck·패드 사용자) ⑨ Casual(10분 세션) ⑩ Indie(넓은 태그는 뒤로). 태그 이름은 Steam 태그 목록에 실제로 있는 것을 고릅니다.

**스크린샷 순서**: ① 8분대 적 300마리 + 무기 5개(장르와 쾌감을 한 장에) ② 코인 제단 앞 — 지갑 코인과 제단 가격이 함께 보이는 장면(훅) ③ 레벨업 3택1 창 ④ 보스 등장 ⑤ 판 종료 정산·영구 강화 메뉴 ⑥ 캐릭터 3종 선택.

> **Steam 페이지에 외부 링크를 넣는 곳**: 설명·이미지에는 웹사이트·Discord 주소를 넣을 수 없습니다(평문 URL, 링크 이미지, QR 코드 포함). Store Page Editor 의 **Basic Info 탭에 있는 링크 전용 필드**를 씁니다(27장 Discord 절).

### 2단계 — 캡슐 이미지 외주 브리프

외주 작가에게 보내는 문서는 "예쁘게 해주세요"가 아니라 **판단 기준을 넘기는 문서**여야 합니다.

```
[코인 러시 캡슐 아트 브리프 v1]

1. 게임 한 줄: 10분 동안 몰려오는 몬스터를 자동 공격으로 쓸어버리는 2D 탑다운 서바이버라이크
2. 전달할 감정: "나 혼자 vs 화면 가득한 적" — 압도적 숫자 + 주인공의 여유
3. 레퍼런스(분위기만 참고, 모방 금지): 첨부 스크린샷 3장(게임 실제 화면), 비교군 캡슐 3개 링크
4. 구도
   - 중앙 하단에 주인공(뒷모습 아님, 정면 3/4), 주변을 둥글게 둘러싼 적 실루엣 20+
   - 상단 1/3 에 로고 "COIN RUSH". 금색 코인이 로고에서 흩날림
   - 색: 어두운 남보라 배경 + 금색 포인트 (게임 팔레트 파일 첨부)
5. 납품물 (각각 별도 구도 조정, 단순 크롭 금지)
   - Header 920×430, Small 462×174(로고 위주), Main 1232×706, Vertical 748×896,
     Library 600×900, Library Hero 3840×1240(글자 없음), 로고 투명 PNG
   - 원본 레이어 파일(PSD) 포함 — 세일·이벤트용 변형 제작에 필요
6. 금지: 로고 외 문구, 게임에 없는 캐릭터·무기, AI 생성 이미지(사용 시 사전 고지 필수)
7. 일정·권리: 러프 3안(5일) → 수정 2회 → 최종(10일). 저작재산권 양도 + 2차적저작물작성권 포함(28장)
8. 검수 기준: Small Capsule 을 실제 크기로 줄였을 때 로고가 읽히는가
```

### 3단계 — 업적 10개 설계

업적은 **튜토리얼 역할(초반) + 목표 제시(중반) + 자랑거리(후반)** 로 분배합니다. 달성률이 전부 0.1% 인 업적은 좌절만 줍니다. 또 **판정 코드를 붙일 이벤트가 이미 있는 조건**만 고릅니다. 표의 10개는 모두 04·10·11·22·23장에 있는 상태 전환·이벤트·세이브 값으로 판정합니다. 캐릭터 해금처럼 아직 코드가 정해지지 않은 조건은 그 기능을 만든 뒤 업적을 추가합니다.

| # | API 이름 | 표시 이름 | 조건 | 종류 | 의도 |
|---|---|---|---|---|---|
| 1 | `ACH_FIRST_RUN` | 첫 발걸음 | 첫 판 종료(생존·사망 무관) | 이벤트 | 거의 모두 달성, 업적 존재 알림 |
| 2 | `ACH_FIRST_LEVELUP` | 선택의 순간 | 첫 레벨업 | 이벤트 | 3택1 시스템 학습 |
| 3 | `ACH_SURVIVE_5` | 반환점 | 한 판에서 5분 생존 | 이벤트 | 중간 목표 |
| 4 | `ACH_SURVIVE_10` | 러시 완주 | 10분 생존(클리어) | 이벤트 | 핵심 목표 |
| 5 | `ACH_KILL_1000` | 천 마리의 적 | 누적 처치 1,000 | 통계 `STAT_KILLS` | 반복 플레이 동기 |
| 6 | `ACH_KILL_10000` | 학살자 | 누적 처치 10,000 | 통계 `STAT_KILLS` | 장기 목표 |
| 7 | `ACH_COINS_5000` | 부자 | 누적 코인 5,000 | 통계 `STAT_COINS` | 메타 진행 연계 |
| 8 | `ACH_FIRST_SHRINE` | 지금 쓴다 | 코인 제단에서 첫 구매 | 이벤트 | 훅의 절반(판 안 소비) 학습 |
| 9 | `ACH_UPGRADE_MAX` | 다음 판을 위해 | 영구 강화 하나를 최대 레벨(10)로 | 이벤트 | 훅의 나머지 절반(저축)의 장기 목표 |
| 10 | `ACH_NO_HIT_3MIN` | 스치지도 마라 | 한 판 시작 후 3분간 무피격 | 이벤트 | 숙련자 도전 |

Steamworks 에서 할 일:

1. App Admin → **Stats & Achievements → Stats** 에서 `STAT_KILLS`, `STAT_COINS` 를 INT 형으로 만들고 **Set By: Client** 로 둡니다.
2. **Achievements** 에서 위 10개를 추가합니다. 5·6·7번은 "Progress Stat" 에 통계를 연결하고 최소/최대값(0 / 1000 등)을 지정합니다.
3. 달성·미달성 아이콘(각 64×64 이상 정사각형)을 올리고 표시 이름을 한국어·영어로 입력합니다.
4. 페이지 상단의 **Publish** 에서 변경 사항을 게시합니다. 게시하지 않으면 코드에서 설정해도 반영되지 않습니다.

### 4단계 — SteamManager 작성

Steamworks.NET 저장소에도 예제 `SteamManager` 가 있지만, 구조를 이해하기 위해 필요한 부분만 직접 씁니다. 초기화 외에 두 가지 일을 더 합니다. ① Steam 계정별 세이브 폴더를 **세이브를 읽기 전에** 정하고(7단계), ② 통계 저장 결과 콜백을 받아 실패 시 재시도하게 합니다(5단계).

`Assets/_CoinRush/Scripts/Platform/SteamManager.cs`

```csharp
// Steamworks.NET 과 같은 조건: 데스크톱이 아니면 Steam 코드를 통째로 제외
#if !(UNITY_STANDALONE_WIN || UNITY_STANDALONE_LINUX || UNITY_STANDALONE_OSX || STEAMWORKS_WIN || STEAMWORKS_LIN_OSX)
#define DISABLESTEAMWORKS
#endif

using UnityEngine;
#if !DISABLESTEAMWORKS
using Steamworks;
#endif

// 같은 씬의 SaveLifecycle(10장) 등 다른 Awake 보다 먼저 실행 → 세이브 폴더를 정한 뒤에 로드되게
[DefaultExecutionOrder(-1000)]
[DisallowMultipleComponent]
public class SteamManager : MonoBehaviour
{
    [SerializeField] private uint appId = 480; // 실제 앱 ID 로 교체 (480 = Valve 예제 앱)

    private static SteamManager instance;

    /// <summary>Steam API 가 정상 초기화되었는가. 모바일·초기화 실패 시 false.</summary>
    public static bool Initialized { get; private set; }

#if !DISABLESTEAMWORKS
    private Callback<UserStatsStored_t> statsStoredCallback;

    private void Awake()
    {
        if (instance != null)
        {
            Destroy(gameObject);
            return;
        }
        instance = this;
        DontDestroyOnLoad(gameObject);

        try
        {
            // Steam 밖에서 exe 를 실행했다면 Steam 을 통해 재실행하고 이 프로세스는 종료
            // (steam_appid.txt 가 있으면 false 를 반환하므로 개발 중에는 재실행되지 않음)
            if (SteamAPI.RestartAppIfNecessary(new AppId_t(appId)))
            {
                Application.Quit();
                return;
            }
        }
        catch (System.DllNotFoundException e)
        {
            Debug.LogError("[Steam] steam_api 라이브러리를 찾을 수 없습니다: " + e);
            Application.Quit();
            return;
        }

        Initialized = SteamAPI.Init();
        if (!Initialized)
        {
            // Steam 클라이언트 미실행, 앱 미소유, steam_appid.txt 누락 등
            Debug.LogWarning("[Steam] SteamAPI.Init 실패 — Steam 기능 없이 계속 실행");
            return;
        }

        // 한 PC 에서 Steam 계정만 바꿔 로그인해도 세이브가 섞이지 않도록 계정별 폴더 사용
        ulong steamId = SteamUser.GetSteamID().m_SteamID;
        SaveSystem.UseUserFolder(steamId.ToString());

        statsStoredCallback = Callback<UserStatsStored_t>.Create(AchievementService.HandleStatsStored);
        Debug.Log($"[Steam] 초기화 성공 (앱 {SteamUtils.GetAppID().m_AppId})");
    }

    private void Update()
    {
        if (!Initialized) return;
        SteamAPI.RunCallbacks();     // 콜백·비동기 결과를 메인 스레드로 받아오는 펌프. 매 프레임 필요.
        AchievementService.Tick();   // 실패한 통계 저장의 재시도 시각 확인
    }

    private void OnDestroy()
    {
        if (instance != this) return;
        instance = null;
        if (!Initialized) return;
        statsStoredCallback?.Dispose();
        statsStoredCallback = null;
        SteamAPI.Shutdown();
        Initialized = false;
    }
#endif
}
```

에디터 조작:

1. [09장](./09_async-scenes.md)의 **Bootstrap 씬**에 빈 오브젝트 `SteamManager` 를 만들고 컴포넌트를 붙입니다. 가장 먼저 로드되는 씬이어야 합니다.
2. Inspector 의 App Id 에 발급받은 앱 ID 를 입력합니다.
3. 프로젝트 루트에 `steam_appid.txt`(내용: 앱 ID 숫자)를 만들고 `.gitignore` 에는 넣지 않습니다(팀원도 필요). 대신 빌드 폴더에 복사되지 않았는지 업로드 전에 확인합니다.
4. 이 파일은 아직 컴파일되지 않습니다. `SaveSystem.UseUserFolder` 는 7단계, `AchievementService` 는 5단계에서 만듭니다. 세 단계를 마친 뒤 Console 에 에러가 없는지 확인하세요.

### 5단계 — 업적 서비스와 게임 이벤트 연결

게임 코드가 Steam 을 직접 알면 모바일 빌드에서 컴파일이 깨지고 테스트도 어렵습니다. 25장의 `AdService` 처럼 **얇은 래퍼**를 둡니다. 이 래퍼는 "아직 서버에 저장되지 않은 변경"을 **결과 콜백을 받을 때까지** 기억하고, 실패하면 60초 뒤 다시 보냅니다.

```
Unlock / AddStat ──► dirty = true ──► StoreStats() ──true──► inFlight (결과 대기)
                                          │                    │
                                        false              UserStatsStored_t
                                          │                 ├─ OK          → 끝 (그 사이 새 변경이 있으면 다시 전송)
                                          ▼                 ├─ InvalidParam → 재시도 안 함 (값이 규칙 위반, 관리 화면 확인)
                                   dirty 유지, 60초 뒤 재시도 ◄┴─ 그 외 실패
```

`Assets/_CoinRush/Scripts/Platform/AchievementService.cs`

```csharp
#if !(UNITY_STANDALONE_WIN || UNITY_STANDALONE_LINUX || UNITY_STANDALONE_OSX || STEAMWORKS_WIN || STEAMWORKS_LIN_OSX)
#define DISABLESTEAMWORKS
#endif

using UnityEngine;
#if !DISABLESTEAMWORKS
using Steamworks;
#endif

/// <summary>
/// 게임 코드는 이 클래스만 호출한다. 플랫폼별 구현(Steam, 모바일의 Play Games 등)은 내부에서 분기.
/// JS: 결제·분석 SDK 를 직접 import 하지 않고 services/ 래퍼를 거치는 것과 같은 이유.
/// </summary>
public static class AchievementService
{
    public const string FirstRun = "ACH_FIRST_RUN";
    public const string FirstLevelUp = "ACH_FIRST_LEVELUP";
    public const string Survive5 = "ACH_SURVIVE_5";
    public const string Survive10 = "ACH_SURVIVE_10";
    public const string FirstShrine = "ACH_FIRST_SHRINE";
    public const string UpgradeMax = "ACH_UPGRADE_MAX";
    public const string NoHit3Min = "ACH_NO_HIT_3MIN";

    public const string StatKills = "STAT_KILLS";
    public const string StatCoins = "STAT_COINS";

    private const float RetryIntervalSeconds = 60f; // Valve 권장: 저장 요청은 초 단위가 아니라 분 단위로

    private static bool dirty;           // 아직 저장 요청을 보내지 못한 변경이 있는가
    private static bool inFlight;        // 요청을 보냈고 UserStatsStored_t 결과를 기다리는 중
    private static float retryAt = -1f;  // 실패 후 재시도할 시각(unscaled). -1 = 예약 없음

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStatics() { dirty = false; inFlight = false; retryAt = -1f; }

    public static void Unlock(string apiName)
    {
#if !DISABLESTEAMWORKS
        if (!SteamManager.Initialized) return;

        if (SteamUserStats.GetAchievement(apiName, out bool achieved) && achieved)
            return; // 이미 달성 — 불필요한 저장 요청 방지

        if (!SteamUserStats.SetAchievement(apiName))
        {
            Debug.LogWarning($"[Achievement] SetAchievement 실패: {apiName} (Publish 여부·API 이름 확인)");
            return;
        }
        dirty = true;
        RequestStore(); // 업적은 팝업이 바로 떠야 하므로 즉시 요청
#else
        Debug.Log($"[Achievement] (Steam 없음) {apiName}");
#endif
    }

    /// <summary>누적 통계를 amount 만큼 증가. 서버 저장은 Flush 에서 모아서.</summary>
    public static void AddStat(string statName, int amount)
    {
#if !DISABLESTEAMWORKS
        if (!SteamManager.Initialized || amount <= 0) return;

        if (!SteamUserStats.GetStat(statName, out int current))
        {
            Debug.LogWarning($"[Achievement] GetStat 실패: {statName} (이름·INT 형·Publish 확인)");
            return;
        }
        if (!SteamUserStats.SetStat(statName, current + amount))
        {
            Debug.LogWarning($"[Achievement] SetStat 실패: {statName} (이름·INT 형·Publish 확인)");
            return;
        }
        dirty = true;
#endif
    }

    /// <summary>판 종료·앱 종료 시 호출. 모아둔 변경의 저장을 요청.</summary>
    public static void Flush()
    {
#if !DISABLESTEAMWORKS
        if (!SteamManager.Initialized || !dirty) return;
        RequestStore();
#endif
    }

    /// <summary>SteamManager.Update 에서 매 프레임 호출. 예약된 재시도만 처리한다.</summary>
    public static void Tick()
    {
#if !DISABLESTEAMWORKS
        if (retryAt < 0f || Time.unscaledTime < retryAt) return;
        retryAt = -1f;
        if (dirty) RequestStore();
#endif
    }

#if !DISABLESTEAMWORKS
    private static void RequestStore()
    {
        if (inFlight) return; // 결과 콜백에서 dirty 를 보고 다시 보낸다

        if (SteamUserStats.StoreStats())
        {
            dirty = false;
            inFlight = true;
            retryAt = -1f;
        }
        else
        {
            // false = 아무것도 전송되지 않음. 변경 표시는 그대로 두고 나중에 다시 시도
            retryAt = Time.unscaledTime + RetryIntervalSeconds;
            Debug.LogWarning("[Achievement] StoreStats 요청 실패 — 60초 뒤 재시도");
        }
    }

    /// <summary>SteamManager 가 Callback&lt;UserStatsStored_t&gt; 로 등록한다.</summary>
    public static void HandleStatsStored(UserStatsStored_t data)
    {
        if (data.m_nGameID != SteamUtils.GetAppID().m_AppId) return; // 다른 앱의 결과는 무시
        inFlight = false;

        switch (data.m_eResult)
        {
            case EResult.k_EResultOK:
                Debug.Log("[Achievement] 저장 완료");
                if (dirty) RequestStore(); // 결과를 기다리는 사이에 생긴 변경
                break;

            case EResult.k_EResultInvalidParam:
                // 관리 화면의 최소/최대·증가 제한을 어긴 통계가 거부되어 서버 값으로 되돌려짐.
                // 같은 값을 다시 보내도 실패하므로 재시도하지 않는다.
                Debug.LogError("[Achievement] 일부 통계가 규칙 위반으로 거부됨 — Stats 설정(최소/최대/Max Change) 확인");
                break;

            default:
                dirty = true;
                retryAt = Time.unscaledTime + RetryIntervalSeconds;
                Debug.LogWarning($"[Achievement] 저장 실패({data.m_eResult}) — 60초 뒤 재시도");
                break;
        }
    }
#endif
}
```

> Steam 은 게임 종료 시 저장되지 않은 변경을 한 번 더 저장하려고 시도합니다. 그래도 재시도 코드를 두는 이유는 **판 도중 받은 업적 팝업이 즉시 떠야 하고**, 종료 전에 크래시가 나면 그 기회도 없기 때문입니다.

다음은 한 판의 기록을 모아 업적을 판정하는 컴포넌트입니다. 요점은 두 가지입니다.

- **판 시작을 "Playing 상태 진입"으로 판단하면 안 됩니다.** 04장 `PlayingState.Enter()` 는 레벨업 선택 뒤 돌아올 때도 호출되므로(04장 코드 주석 참고), 그때마다 초기화하면 처치 수·시간이 계속 0으로 돌아갑니다. 그래서 **진행 중인 판이 없을 때만** 새 판을 시작합니다.
- 상태 클래스가 트래커를 알게 만들지 않고, 트래커가 **상태 머신·스포너·경험치·코인 채널의 이벤트를 구독**합니다. 앞 장 파일은 이벤트 한 줄씩만 추가합니다.

`Assets/_CoinRush/Scripts/Platform/RunAchievementTracker.cs`

```csharp
using UnityEngine;

/// <summary>
/// 한 판(Run) 동안의 기록을 모아 업적·통계로 보낸다.
/// 새 판 시작 = 진행 중인 판이 없을 때 Playing 진입, 판 종료 = Result 진입.
/// </summary>
public class RunAchievementTracker : MonoBehaviour
{
    [SerializeField] private GameStateMachine machine;           // 04장 (+ StateEntered 이벤트, 아래 A)
    [SerializeField] private EnemySpawner spawner;               // 22장 (+ EnemyKilled 이벤트, 아래 B)
    [SerializeField] private PlayerExperience playerExperience;  // 11장
    [SerializeField] private IntEventChannel coinCollected;      // 03장
    [SerializeField] private ProgressionData progression;        // 23장 — upgradeMaxLevel

    private float runTime;
    private int killsThisRun;
    private int coinsThisRun;
    private bool running;
    private bool survive5Sent;

    public bool IsRunning => running;
    public float RunTime => runTime;

    private void OnEnable()
    {
        machine.StateEntered += OnStateEntered;
        spawner.EnemyKilled += OnEnemyKilled;
        spawner.RunTimeCompleted += OnRunTimeCompleted;
        playerExperience.LeveledUp += OnLeveledUp;
        coinCollected.OnRaised += OnCoinCollected;
    }

    private void OnDisable()
    {
        machine.StateEntered -= OnStateEntered;
        spawner.EnemyKilled -= OnEnemyKilled;
        spawner.RunTimeCompleted -= OnRunTimeCompleted;
        playerExperience.LeveledUp -= OnLeveledUp;
        coinCollected.OnRaised -= OnCoinCollected;
    }

    private void Start()
    {
        // 에디터에서 Game 씬을 바로 Play 해 이미 Playing 인 경우(09장) 대비
        if (!running && machine.Current == machine.Playing) BeginRun();
    }

    private void OnStateEntered(IGameState state)
    {
        // Playing 은 레벨업(·일시정지)에서 돌아올 때도 다시 진입한다 → 진행 중인 판이 없을 때만 새 판
        if (state == machine.Playing && !running) BeginRun();
        else if (state == machine.Result && running) EndRun();
    }

    private void BeginRun()
    {
        runTime = 0f;
        killsThisRun = 0;
        coinsThisRun = 0;
        survive5Sent = false;
        running = true;
        CheckPermanentUpgrades(); // 타이틀에서 산 영구 강화는 다음 판 시작 때 확인
    }

    private void Update()
    {
        if (!running) return;
        runTime += Time.deltaTime; // 레벨업(timeScale 0) 동안은 늘지 않음

        if (!survive5Sent && runTime >= 300f)
        {
            survive5Sent = true;
            AchievementService.Unlock(AchievementService.Survive5);
        }
    }

    private void OnEnemyKilled() { if (running) killsThisRun++; }

    private void OnCoinCollected(int amount) { if (running) coinsThisRun += amount; }

    private void OnLeveledUp(int level) => AchievementService.Unlock(AchievementService.FirstLevelUp);

    // 클리어 판정은 스포너가 한다(22장). Result 진입보다 먼저 오든 나중에 오든 결과가 같도록 바로 해제
    private void OnRunTimeCompleted() => AchievementService.Unlock(AchievementService.Survive10);

    /// <summary>코인 제단에서 구매가 확정됐을 때 호출 (아래 C)</summary>
    public void ReportShrinePurchase()
    {
        if (running) AchievementService.Unlock(AchievementService.FirstShrine);
    }

    private void EndRun()
    {
        running = false;
        Debug.Log($"[RunAchievementTracker] 판 종료 — {runTime:0.0}초, 처치 {killsThisRun}, 코인 {coinsThisRun}");

        AchievementService.Unlock(AchievementService.FirstRun);
        AchievementService.AddStat(AchievementService.StatKills, killsThisRun);
        AchievementService.AddStat(AchievementService.StatCoins, coinsThisRun);
        AchievementService.Flush(); // 통계 기반 업적(1000·10000 처치 등)은 저장 시 서버에서 자동 판정
    }

    private void CheckPermanentUpgrades()
    {
        SaveData save = SaveSystem.Load();              // 10장 v2 — upgrades: 강화 ID → 레벨
        foreach (int level in save.upgrades.Values)
        {
            if (level >= progression.upgradeMaxLevel)
            {
                AchievementService.Unlock(AchievementService.UpgradeMax);
                return;
            }
        }
    }

    private void OnApplicationQuit() => AchievementService.Flush();
}
```

> 10번 업적 `ACH_NO_HIT_3MIN`(3분 무피격)은 연습 문제 1에서 직접 추가합니다.

**앞 장 파일 수정 (A·B·C)** — 바뀌는 줄만 보여줍니다.

**A. 04장 `GameStateMachine.cs`** — 이벤트 필드 하나를 추가하고 `ChangeState` 를 아래로 교체합니다.

```csharp
// 필드 영역에 추가 (Current 프로퍼티 아래)
public event System.Action<IGameState> StateEntered;   // Enter 가 끝난 직후 발행

public void ChangeState(IGameState next)
{
    if (next == null || next == Current) return;

    Current?.Exit();
    Current = next;
    currentStateName = next.GetType().Name;
    Current.Enter();
    StateEntered?.Invoke(next);
}
```

**B. 22장 `EnemySpawner.cs`** — 이벤트 선언을 추가하고, `GetPool` 의 `createFunc` 안 구독 줄을 교체합니다. 22장 규칙상 반환 요청은 적이 **죽어서 드롭·사망 연출을 끝낸 뒤에만** 오므로 "처치 1회"로 셉니다. 나중에 화면 밖 적을 정리하는 반환 경로를 추가한다면 그 경로에서는 이 이벤트를 발행하지 마세요.

```csharp
// 다른 event 선언 옆에 추가
public event Action EnemyKilled;               // 적이 죽어 풀로 돌아갈 때 (업적·통계용)

// createFunc 안의 구독 줄 교체
enemy.ReleaseRequested += e => { AliveCount--; pool.Release(e); EnemyKilled?.Invoke(); };
```

**C. 코인 제단 구매 확정 지점** — [24장](./24_playtest-analytics.md)에서 `shrine_visit` 이벤트를 기록하는 코드(제단 창이 닫힐 때)에 한 줄을 붙입니다. 그 스크립트에 `[SerializeField] private RunAchievementTracker runTracker;` 필드를 추가합니다.

```csharp
Analytics.Track("shrine_visit", ("time_s", spawner.Elapsed), ("price", price), ("wallet", wallet), ("purchased", bought));
if (bought) runTracker.ReportShrinePurchase();
```

Inspector 연결:

1. 게임 씬의 `GameSystems` 오브젝트에 `RunAchievementTracker` 를 붙입니다.
2. **Machine** ← `GameSystems`(같은 오브젝트의 `GameStateMachine`), **Spawner** ← `EnemySpawner` 오브젝트, **Player Experience** ← `Player`, **Coin Collected** ← `Assets/_CoinRush/Events/` 의 코인 획득 `IntEventChannel` 에셋(04장 머신의 Coin Collected 와 같은 에셋), **Progression** ← `Assets/_CoinRush/Data/ProgressionData`.
3. 코인 제단 스크립트의 **Run Tracker** 칸에 `GameSystems` 를 드래그합니다.

### 6단계 — 오버레이 일시정지와 위시리스트 버튼

`Assets/_CoinRush/Scripts/Platform/SteamOverlayBridge.cs`

```csharp
#if !(UNITY_STANDALONE_WIN || UNITY_STANDALONE_LINUX || UNITY_STANDALONE_OSX || STEAMWORKS_WIN || STEAMWORKS_LIN_OSX)
#define DISABLESTEAMWORKS
#endif

using System;
using UnityEngine;
using UnityEngine.Events;
#if !DISABLESTEAMWORKS
using Steamworks;
#endif

public class SteamOverlayBridge : MonoBehaviour
{
    [SerializeField] private uint fullGameAppId;         // 데모라면 본편 앱 ID, 본편이면 자기 앱 ID
    [SerializeField] private GameStateMachine machine;   // 게임 씬에서만 연결. 비워 두면 항상 이벤트 발행
    [SerializeField] private UnityEvent overlayOpened;   // 인스펙터에서 08장 PauseController.Pause 연결

#if !DISABLESTEAMWORKS
    private Callback<GameOverlayActivated_t> overlayCallback;

    private void OnEnable()
    {
        if (!SteamManager.Initialized) return;
        overlayCallback = Callback<GameOverlayActivated_t>.Create(OnOverlayActivated);
    }

    private void OnDisable()
    {
        overlayCallback?.Dispose();
        overlayCallback = null;
    }

    private void OnOverlayActivated(GameOverlayActivated_t data)
    {
        // 필드 타입이 SDK 버전에 따라 bool/byte 로 다를 수 있어 Convert 로 처리
        if (!Convert.ToBoolean(data.m_bActive)) return; // 닫힐 때는 자동 재개하지 않음 — 플레이어가 Resume 을 누른다

        // 레벨업·결과·타이틀 화면은 이미 멈춰 있거나 멈출 게임이 없다 → 일시정지를 겹쳐 걸지 않음
        if (machine != null && machine.Current != machine.Playing) return;

        overlayOpened?.Invoke();
    }
#endif

    // UI Button 의 OnClick 에 연결
    public void OpenStorePage()
    {
#if !DISABLESTEAMWORKS
        if (SteamManager.Initialized && SteamUtils.IsOverlayEnabled())
        {
            SteamFriends.ActivateGameOverlayToStore(new AppId_t(fullGameAppId),
                EOverlayToStoreFlag.k_EOverlayToStoreFlag_None);
            return;
        }
#endif
        Application.OpenURL($"https://store.steampowered.com/app/{fullGameAppId}/");
    }
}
```

Inspector 연결:

1. 게임 씬의 `Controls` 오브젝트([08장](./08_input-system.md) 4단계에서 `PauseController` 를 붙인 곳)에 `SteamOverlayBridge` 를 추가합니다.
2. **Machine** ← `GameSystems`. **Overlay Opened** 의 `+` → 오브젝트 칸에 `Controls` → 함수 `PauseController.Pause` 를 고릅니다.
3. 데모 결과 화면의 "위시리스트에 추가" 버튼 OnClick 에 이 오브젝트의 `SteamOverlayBridge.OpenStorePage` 를 연결하고 **Full Game App Id** 에 본편 앱 ID 를 넣습니다.

> 왜 Playing 에서만? 08장 `PauseController.Pause()` 는 `timeScale` 을 0으로, `Resume()` 은 1로 되돌립니다. 레벨업 창(이미 `timeScale` 0)에서 오버레이를 열 때 일시정지를 걸면, 오버레이를 닫고 Resume 을 누르는 순간 레벨업 창이 열린 채로 게임이 다시 움직입니다.

### 7단계 — Steam Cloud(Auto-Cloud)와 계정별 세이브 폴더

**10장 `SaveSystem.cs` 수정** — 파일 맨 위에 `using System.IO;` 를 추가하고, 정적 필드 하나를 추가한 뒤 `ResetStatics` 와 `Store` 두 줄을 아래로 교체하고, `UseUserFolder` 메서드를 추가합니다. 나머지(`Load`·`Save`·`SaveIfDirty` 등)는 그대로입니다.

```csharp
private static string userFolder;   // null 이면 persistentDataPath 바로 아래 (모바일·Steam 미초기화)

[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
private static void ResetStatics() { store = null; current = null; dirty = false; writeBlocked = false; userFolder = null; }

private static SaveFileStore Store => store ??= new SaveFileStore(
    string.IsNullOrEmpty(userFolder)
        ? Application.persistentDataPath
        : Path.Combine(Application.persistentDataPath, userFolder));

/// <summary>세이브를 읽기 전에 호출(SteamManager.Awake). 계정별 하위 폴더를 쓰게 한다.</summary>
public static void UseUserFolder(string folder)
{
    if (userFolder == folder) return;
    if (current != null)
        Debug.LogWarning("[Save] 세이브를 이미 읽은 뒤 사용자 폴더가 바뀌었습니다. SteamManager 가 가장 먼저 실행되는지 확인하세요.");
    userFolder = folder;
    store = null;      // 다음 접근 때 새 경로로 다시 만든다
    current = null;
    dirty = false;
    writeBlocked = false;
}
```

이제 Steam 에서 실행하면 세이브가 `…/CoinRushStudio/CoinRush/76561198xxxxxxxxx/save.json` 에 저장됩니다. **출시 전에 적용**하세요. 이미 출시한 게임에 나중에 넣으면 기존 루트의 `save.json` 이 누구 것인지 코드로 알 수 없으므로, 자동 이관 대신 "기존 세이브 가져오기" 버튼처럼 사용자가 직접 확인하는 절차가 필요합니다.

Steamworks 설정:

1. Player Settings 의 **Company Name** 과 **Product Name** 을 확정합니다(예: `CoinRushStudio` / `CoinRush`). 출시 후 바꾸면 저장 경로가 바뀌어 세이브가 사라진 것처럼 보입니다.
2. Steamworks → App Admin → **Steam Cloud** 에서 사용자당 바이트 할당량(예: 1MB)과 파일 수(예: 10)를 입력합니다.
3. **Auto-Cloud** 에 루트 경로를 추가합니다. Windows: 루트 `WinAppDataLocalLow`, 하위 디렉터리 `CoinRushStudio/CoinRush/{64BitSteamID}`, 패턴 `*.json`, 하위 폴더 포함은 끔. `save.json` 과 10장의 `save.backup.json` 이 올라가고, 쓰는 중인 `save.json.tmp` 는 패턴에 맞지 않아 제외됩니다.
4. macOS·Linux 빌드가 있다면 Root Overrides 로 각 OS 의 `persistentDataPath` 에 대응시킵니다(Root Overrides 를 쓰면 Root OS 를 All OSes 로 둬야 합니다).
5. 저장 후 **Publish** 합니다. Auto-Cloud 는 **게임 실행 시와 종료 시**에 동기화합니다.

계정 교체 검증(beta 브랜치 빌드로):

1. Steam 계정 A 로 실행 → 한 판 하고 영구 강화 1개 구매 → 종료.
2. 같은 PC 에서 계정 B 로 로그인(B 에게 앱이 있어야 함, 테스트 계정) → 실행 → **새 게임 상태**여야 합니다.
3. `persistentDataPath` 아래에 SteamID 폴더가 두 개 생겼는지 확인합니다.
4. 계정 A 로 다른 PC(또는 A 의 로컬 SteamID 폴더를 지운 뒤)에서 실행 → A 의 강화가 복원되면 성공입니다.

### 8단계 — SteamPipe 로 업로드

SDK 의 `tools/ContentBuilder` 를 `steam-build/` 로 복사해 씁니다. `builder/`(steamcmd), `scripts/`(VDF), `content/windows/`(Unity 빌드 결과), `output/`(로그·캐시) 네 폴더를 사용합니다.

`scripts/app_build_3000000.vdf` (앱 ID 3000000, Windows 디포 3000001 은 예시)

```
"AppBuild"
{
	"AppID" "3000000"
	"Desc" "CoinRush 1.0.3 - hotfix resolution on Steam Deck"
	"ContentRoot" "..\content\"
	"BuildOutput" "..\output\"
	"SetLive" "beta"

	"Depots"
	{
		"3000001"
		{
			"FileMapping"
			{
				"LocalPath" "windows\*"
				"DepotPath" "."
				"recursive" "1"
			}
			"FileExclusion" "*.pdb"
			"FileExclusion" "*_BurstDebugInformation_DoNotShip*"
			"FileExclusion" "steam_appid.txt"
		}
	}
}
```

업로드 순서:

1. Steamworks → SteamPipe → **Depots** 에서 Windows 디포를 확인하고, **Installation → General** 에서 실행 파일(`CoinRush.exe`)과 OS 를 지정한 **Launch Option** 을 만듭니다.
2. SteamPipe → **Builds** 에서 `beta` 브랜치를 만들고 비밀번호를 설정합니다.
3. [19장](./19_addressables-build.md)의 빌드 스크립트로 Windows 빌드를 `content/windows/` 에 출력합니다.
4. 터미널에서 실행합니다.

```
cd steam-build/builder
steamcmd +login coinrush_builder +run_app_build C:\steam-build\scripts\app_build_3000000.vdf +quit
```

5. Builds 페이지에서 새 빌드가 `beta` 에 연결됐는지 확인하고, 테스트 계정의 라이브러리 → 게임 속성 → 베타에서 비밀번호를 넣어 설치·실행합니다.
6. 문제가 없으면 Builds 페이지에서 해당 빌드를 **default 브랜치로 Set Live** 합니다(웹에서만 가능).

### 9단계 — 출시 D-180 ~ D+30 체크리스트

이 표는 **Steam 출시 전용의 표준 역산 일정**입니다. 적용 조건은 "Coming Soon 페이지를 출시 5개월 전에 열 수 있을 만큼 게임(캡슐·실제 게임플레이 스크린샷)이 준비됐고, 출시 전 Next Fest 에 한 번 참가한다"입니다. 교재에 나오는 다른 일정 예시와의 관계는 다음과 같습니다.

| 일정 예시 | 무엇을 위한 일정인가 | 이 표와의 관계 |
|---|---|---|
| [21장](./21_core-loop-gdd.md) 24주 마일스톤 | 코인 러시 v1.0 **개발** 계획 (부업, 주 15~20시간) | 출시일(24주차)을 D-0 으로 놓으면 D-180 은 개발 시작 약 2주 전입니다 → 가입·세금 인터뷰를 개발 시작 전에 끝냅니다. 21장은 Coming Soon 을 **14주차(D-70)** 에 엽니다. 그래서 D-150 행은 D-70 으로 밀리고, D-100~D-60 의 Next Fest 는 출시 전 참가 가능한 회차가 있을 때만 합니다. 위시리스트를 모을 기간이 짧다는 위험은 29장 게이트 3 이 판단합니다 |
| [29장](./29_scope-postmortem.md) 킬 기준·예산 | 21장 24주 계획의 게이트와 시간 예산 | 이 표의 행정·스토어 작업 시간을 29장 예산에서 **기능보다 먼저** 공제합니다 |
| [30장](./30_capstone.md) 12주 캡스톤 | 자기 게임의 **첫 출시 경험** (코인 러시 v1.0 보다 작은 범위) | 12주 안에는 이 표를 다 넣을 수 없습니다. 30장은 가입(1주차)·페이지 제출(7주차)·빌드 검토(10주차)만 남기고, 위시리스트 축적은 목표에서 뺍니다 |

| 시점 | 할 일 | 참고 장 |
|---|---|---|
| D-180 | Steamworks 가입·결제·세금·은행 인터뷰, 비교군 조사표·가격 가설·태그 초안 | 27, 28 |
| D-150 | 캡슐 브리프 발주, 실제 게임플레이 스크린샷 5장 이상 준비, 페이지 검토 제출(공개 희망일 7영업일 이상 전) → **Coming Soon 공개**, 위시리스트 주간 기록 시작 | 27 |
| D-120 | 데모 범위 확정(첫 10분 + 위시리스트 버튼), Deck 1280×800·패드 조작 점검 | 08, 11, 29 |
| D-100 | Next Fest 참가 신청(마감일 확인), 데모 앱 생성·검토 제출 | — |
| D-90 | 최종 캡슐·트레일러 교체, 한국어·영어 페이지 동시 점검 | 27 |
| D-90~60 | Next Fest 참가, 스트리머에게 데모 안내(공개 데모는 키 불필요) | 27 |
| D-60 | 업적·통계 Publish, Auto-Cloud 설정, beta 브랜치 내부 테스트 | 이 장 |
| D-45 | 출시일·가격·출시 할인율 확정, 지역 가격 추천값 적용 | — |
| D-30 | **출시 빌드 검토 제출**(Release 체크리스트 전부 완료), 출시 전 플레이용 스트리머·언론 키는 **Release State Override** 키로 요청·외부 계정에서 설치 확인 후 메일 | 27 |
| D-14 | Coming Soon 2주 이상 공개 상태 재확인, 출시 공지 초안 | — |
| D-7 | 크래시 리포트·애널리틱스 정상 수집 확인, 핫픽스 브랜치 준비 | 24 |
| D-1 | 빌드 default Set Live 대기 상태 확인, 오프라인 일정 비우기 | — |
| D-0 | 출시 버튼 → 스토어 확인 → SNS·Discord·뉴스레터 공지 | — |
| D+1~3 | 리뷰 전부 읽기, 크래시·해상도 문제 48시간 내 핫픽스 | 18 |
| D+7 | 첫 주 지표 기록(판매, 환불률, 위시리스트 전환, 리뷰 수) | 29 |
| D+14 | 첫 패치노트 공지(Steam 이벤트) — 재노출 | — |
| D+30 | 세일 캘린더 확정, 30일 회고 작성 | 29 |

### 확인하기

검사를 **에디터에서 확인할 것**과 **Steam 으로 실행한 빌드에서만 확인할 것**으로 나눕니다. Steam 오버레이는 렌더러가 초기화되기 전에 주입돼야 하는데, 에디터에서는 스크립트가 그 뒤에 실행되므로 오버레이가 동작하지 않을 수 있습니다(Steamworks.NET FAQ). 에디터에서 오버레이가 안 보이는 것은 실패가 아닙니다.

**에디터 (Steam 클라이언트 실행 + `steam_appid.txt`)**

- Console 에 `[Steam] 초기화 성공` 이 찍히고 `SteamAPI.Init 실패` 경고가 없습니다. `persistentDataPath` 아래에 SteamID 숫자 폴더가 생기고 그 안에 `save.json` 이 저장됩니다.
- 레벨업을 두 번 이상 한 뒤 사망하면 `[RunAchievementTracker] 판 종료 — …초, 처치 N, 코인 M` 이 **한 번만** 찍히고, 시간·처치 수가 레벨업 때 0으로 돌아가지 않은 누적값입니다. 이어서 `[Achievement] 저장 완료` 가 찍힙니다.
- Steam 클라이언트의 해당 게임 **업적 페이지**(라이브러리 → 게임 → 업적)에서 "첫 발걸음"·"선택의 순간"이 달성으로 표시됩니다. 다시 테스트하려면 `SteamUserStats.ResetAllStats(true)` 를 임시 버튼으로 호출합니다.
- 인터넷을 끊고 한 판을 끝내면 저장 실패 경고와 "60초 뒤 재시도"가 찍히고, 다시 연결하면 재시도 후 `저장 완료` 가 찍힙니다.
- Android 로 플랫폼을 바꿔도 컴파일 에러 없이 빌드되고, 로그에 `(Steam 없음)` 메시지만 찍힙니다.

**beta 브랜치로 설치해 Steam 에서 실행한 standalone 빌드**

- 실행 직후 화면 구석에 Steam 오버레이 안내 알림이 뜨고, 업적을 달성하면 그 자리에서 팝업이 뜹니다(종료 후에야 뜨면 `RunCallbacks`·`StoreStats` 호출을 확인).
- 플레이 중 Shift+Tab 으로 오버레이를 열면 일시정지 패널이 뜹니다. **레벨업 선택 창이 열린 상태**에서 Shift+Tab 을 열고 닫으면 일시정지 패널이 뜨지 않고, 레벨업 창에서 카드를 고르면 정상적으로 게임이 재개됩니다.
- 7단계의 계정 교체 검증 4개 항목을 통과합니다.

## 흔한 실수

1. **업적이 달성되지 않음** → `SetAchievement` 만 호출했거나 Steamworks 에서 Publish 를 안 함 → `StoreStats` 호출 여부와 관리 화면의 "Unpublished changes" 표시를 확인합니다.
2. **출시 빌드를 실행하면 바로 꺼졌다가 Steam 으로 다시 켜짐(또는 안 켜짐)** → `RestartAppIfNecessary` 에 잘못된 앱 ID, 혹은 빌드 폴더에 `steam_appid.txt` 가 남아 다른 앱으로 인식 → 앱 ID 를 확인하고 VDF 의 `FileExclusion` 으로 제외합니다.
3. **모바일 빌드가 `Steamworks` 네임스페이스를 찾지 못해 실패** → Steam 코드에 `DISABLESTEAMWORKS` 조건부 컴파일을 안 함 → 이 장의 파일처럼 파일 맨 위 `#define` 과 `#if` 를 넣습니다. 게임 로직은 래퍼만 호출합니다.
4. **출시일에 "출시 불가" 상태** → Coming Soon 2주 규칙, 빌드 검토 미통과, 출시 체크리스트 미완료 → 빌드 검토는 D-30 에 제출하고 Steamworks 의 Release 체크리스트를 주 1회 봅니다.
5. **클라우드 세이브가 동기화되지 않음** → Auto-Cloud 경로의 회사명·제품명 대소문자 불일치, 하위 디렉터리에 `{64BitSteamID}` 누락(코드는 SteamID 폴더에 쓰는데 설정은 상위 폴더를 봄), 패턴 누락, Publish 누락 → 실제 저장 경로를 로그로 찍어 비교합니다.
6. **레벨업할 때마다 판 기록이 초기화됨** → 판 시작을 Playing 상태 `Enter()` 에서 처리함(레벨업 복귀 때도 호출됨) → 이 장의 트래커처럼 "진행 중인 판이 없을 때만" 새 판을 시작합니다.

## 연습 문제

**1. ★☆☆** `RunAchievementTracker` 에 `ACH_NO_HIT_3MIN`(판 시작 후 3분 동안 한 번도 맞지 않음)을 추가하세요. 플레이어의 `Health.Changed` 이벤트를 쓰되, 체력 회복은 피격으로 치지 않아야 합니다.

<details><summary>힌트·해설</summary>

`[SerializeField] private Health playerHealth;` 와 `private int previousHp; private bool wasHit; private bool noHitSent;` 를 추가합니다. `OnEnable/OnDisable` 에서 `playerHealth.Changed` 를 구독·해제하고, `BeginRun` 끝에 `previousHp = playerHealth.Current; wasHit = false; noHitSent = false;` 를 추가합니다(`BeginRun` 은 새 판에서만 불리므로 레벨업 복귀 때 기록이 지워지지 않습니다). 핸들러 `OnPlayerHealthChanged(int current, int max)` 에서 `if (running && current < previousHp) wasHit = true; previousHp = current;` 로 **이전 값과 비교**합니다(`current < max` 로 판정하면 회복 전 상태와 구분이 안 됩니다). `Update` 에 `if (!noHitSent && !wasHit && runTime >= 180f) { noHitSent = true; AchievementService.Unlock(AchievementService.NoHit3Min); }` 를 넣습니다. 이벤트 인자에 "이전 값"이 없으면 구독자가 직전 상태를 들고 있어야 한다는 점이 핵심입니다.

</details>

**2. ★★☆** 코인 러시와 비교군이 될 Steam 게임 8개를 찾아 표(이름, 출시 가격, 출시 연도, 리뷰 수, 긍정 비율, 평균 플레이 시간, 태그 상위 3개)를 만들고 코인 러시의 가격을 한 문단으로 정당화하세요.

<details><summary>힌트·해설</summary>

SteamDB 의 태그 페이지(예: Bullet Heaven)에서 출시일 기준으로 정렬하고, 너무 큰 히트작(리뷰 수만 단위)은 1~2개만 포함합니다. 출시 가격은 SteamDB 가격 기록에서 확인합니다. 정당화 문단은 "콘텐츠 분량이 비교군 중앙값보다 적으므로 중앙값보다 한 단계 낮은 가격, 출시 할인으로 첫 주 전환 유도" 같은 **비교 기반 문장**이어야 합니다. "싸게 팔면 많이 사겠지"는 근거가 아닙니다.

</details>

**3. ★★★** 자기 게임(또는 코인 러시)의 **데모 설계서**를 쓰세요: 포함 범위, 데모 전용 제한, 끝 화면 흐름, 데모 세이브를 본편으로 이어갈지 여부, Next Fest 기간 중 라이브스트림 계획, 성공 지표(데모 플레이어 수 대비 위시리스트 증가).

<details><summary>힌트·해설</summary>

좋은 데모 설계서는 "무엇을 빼는가"가 명확합니다. 코인 러시 예: 캐릭터 1종(본편 3종), 무기 3종(본편 6종), 제단 강화 4종(본편 8종), 10분 1판, 영구 강화 3레벨까지. 끝 화면은 "클리어/사망 → 본편에서 추가되는 것 3줄 → 위시리스트 버튼(오버레이)". 세이브 이어가기는 구현 비용 대비 효과가 작으면 하지 않는다고 적어도 됩니다. 성공 지표는 Next Fest 전후 1주 위시리스트 증가량을 기준선과 비교하는 형태로 정의하세요.

</details>

## 셀프 체크

**1.** 위시리스트가 왜 Steam 판매의 선행 지표인지, Coming Soon 을 늦게 공개하면 무엇을 잃는지 설명해보세요.

<details><summary>모범 답안</summary>

위시리스트 사용자는 출시·할인 시 알림을 받아 첫 주 구매자가 됩니다. 위시리스트 수 자체는 (인기 출시 예정 같은 일부 영역을 빼면) 알고리즘 노출 요인이 아니지만, 알림으로 생긴 첫 판매·플레이 반응이 신규 출시 기본 노출 이후의 추가 추천에 영향을 줍니다. Coming Soon 을 늦게 공개하면 위시리스트를 쌓을 시간이 줄어 출시일 알림을 받는 사람이 적고, 첫 주 구매자와 리뷰(구매를 망설이는 사람의 판단 근거)가 부족해집니다. 추가 노출은 어떤 경우에도 보장되지 않습니다. 또한 출시 전 최소 공개 기간 규칙 때문에 일정 자체가 밀릴 수 있습니다.

</details>

**2.** `SetAchievement` 와 `StoreStats` 의 차이, 그리고 `StoreStats` 를 매 프레임 호출하면 안 되는 이유를 설명해보세요.

<details><summary>모범 답안</summary>

`SetAchievement` 는 클라이언트 메모리에서 달성 상태를 바꾸는 것이고, `StoreStats` 가 서버 저장을 요청해 결과(`UserStatsStored_t`)와 달성 팝업으로 이어집니다. `StoreStats` 는 호출 빈도 제한이 있어 Valve 가 분 단위 빈도를 권장하므로, 업적 달성이나 판 종료처럼 의미 있는 시점에 모아서 호출합니다. 또 `false` 반환이나 실패 결과가 오면 전송되지 않은 것이므로, 변경 표시를 지우지 않고 간격을 두고 재시도해야 합니다.

</details>

**3.** Auto-Cloud 와 Remote Storage API 중 코인 러시가 Auto-Cloud 를 택한 이유는?

<details><summary>모범 답안</summary>

10장의 `SaveSystem` 이 이미 `persistentDataPath` 에 JSON 파일로 저장하고, 게임 실행 중 외부에서 파일이 바뀔 일이 없으므로 경로 설정만으로 동기화할 수 있기 때문입니다(실행 시·종료 시 동기화). 코드 변경은 한 PC 의 여러 Steam 계정이 세이브를 공유하지 않도록 SteamID 하위 폴더를 쓰게 한 것뿐이고, Auto-Cloud 하위 경로에도 `{64BitSteamID}` 를 넣어 맞춥니다. 저장 시점을 세밀하게 제어하거나 플랫폼 경로에 의존하지 않고 싶을 때 API 방식을 씁니다.

</details>

**4.** App · Depot · Build · Branch 의 관계를 웹 배포 용어에 빗대어 설명해보세요.

<details><summary>모범 답안</summary>

App 은 서비스(상품) 자체, Depot 은 플랫폼별 아티팩트 묶음, Build 는 특정 시점에 업로드한 Depot 스냅샷으로 릴리스에 해당하고, Branch 는 어떤 릴리스를 누구(전체 사용자=default, 테스터=beta)에게 배포할지 가리키는 환경 포인터입니다. 롤백은 Branch 를 이전 Build 로 다시 가리키면 됩니다.

</details>

## 핵심 요약

- Steam 출시는 **D-180 부터 역산**합니다. 가입·세금·페이지 검토·Coming Soon 2주·빌드 검토에 모두 대기 시간이 있습니다.
- Steam Direct 는 앱당 $100, 매출 $1,000 이후 환급. 정책·금액은 바뀔 수 있으니 제출 전 문서를 확인합니다.
- 스토어 페이지는 캡슐(클릭) → 트레일러·짧은 설명·태그(취향 판단) → 긴 설명(구매 결정)의 깔때기입니다. 태그는 정확한 장르부터.
- 위시리스트는 출시 알림으로 첫 구매자를 데려오는 선행 지표입니다(그 수 자체가 알고리즘 노출 요인은 아님). Next Fest 는 연 3회 중 가장 준비된 한 번에 씁니다.
- 가격은 비교군 표로 정하고 지역 가격은 추천값에서 시작합니다. 얼리 액세스는 장기 업데이트 구조일 때만(정식 출시 때 출시 노출 지침은 다시 적용되지만 판매 급증은 보장되지 않음).
- Steam 코드는 `DISABLESTEAMWORKS` 조건부 컴파일 + 얇은 래퍼로 격리합니다. 업적은 `SetAchievement` 뒤 `StoreStats`, 결과 콜백을 받을 때까지 변경을 기억하고 실패하면 재시도합니다. 판 시작은 "진행 중인 판이 없을 때 Playing 진입"으로 판단합니다.
- 기존 파일 세이브는 Auto-Cloud 로 클라우드화하되 **SteamID 별 폴더**(`{64BitSteamID}`)로 계정을 분리합니다. Company/Product Name 은 출시 후 바꾸지 않습니다.
- 오버레이·업적 팝업은 에디터가 아니라 Steam 으로 실행한 빌드에서 검사합니다.
- steamcmd 는 beta 브랜치에만 올리고 default 적용은 웹에서 확인 후 합니다.

## 더 읽을거리

- Steamworks 문서 — https://partner.steamgames.com/doc/home (Store Graphical Assets, Steam Direct, Steam Cloud, SteamPipe, Stats and Achievements 항목)
- Steamworks.NET — https://steamworks.github.io/ 와 GitHub 저장소 rlabrecque/Steamworks.NET
- Steam Deck 호환성 가이드 — https://partner.steamgames.com/doc/steamhardware/compat
- Steam 노출·위시리스트 공식 설명 — https://partner.steamgames.com/doc/marketing/visibility
- How To Market A Game (Chris Zukowski) — https://howtomarketagame.com
- SteamDB — https://steamdb.info (비교군 가격·태그 조사)
