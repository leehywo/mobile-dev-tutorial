# 25. 수익화 구현 — 보상형 광고·IAP·Remote Config

> **이 장에서 배울 것**
> - 수익 모델별 설계 원칙을 설명하고, 코인 러시의 Steam 유료 1차 출시와 모바일 무료판 확장 트랙의 수익 전략·상품 효용을 설계한다
> - 보상형 광고 UX 원칙, eCPM·fill rate·ARPDAU를 계산하고, CPI·LTV·ROAS와 월 손익으로 유료 사용자 확보를 계속할지 판단한다
> - `IAdService`·`IStoreService` 인터페이스 뒤에 SDK를 숨기고, 에디터에서 동작하는 가짜 광고·가짜 스토어로 부활·코인 2배·스타터 팩·복원·재전달 흐름을 끝까지 구현한다
> - 구매 처리 순서(검증 → 중복 확인 → 지급·영속화 → 구매 확인)와 동의(GDPR 광고 게재 방식·ATT)를 설명하고 구현 계약으로 만든다
> - Remote Config와 A/B 테스트의 배정·노출 기록, 보호 지표에 맞는 표본 크기를 정한다
>
> **선수 장**: 04, 09, 10, 11, 21, 23, 24 (기초 트랙 [4-4 인앱 결제](../react-to-unity.md) 참고) · **예상 시간**: 6~8시간 · **코인 러시 진행**: (모바일 확장 트랙) 부활 광고, 결과 화면 코인 2배, 스타터 팩 구매·복원, 조건부 광고 제거 상품, 원격 설정 구조 — 모두 SDK 없이 에디터에서 테스트 가능

## 왜 필요한가

21장 기획서에서 코인 러시의 **1차 출시는 Steam 유료 판매**(광고·추가 과금 없음)로 정했습니다. 모바일 무료판은 Steam 출시 후 판매 반응을 보고 결정하는 **별도 확장 트랙**이고, v1.0 일정과 스코프에는 들어 있지 않습니다. 이 장은 그 확장 트랙을 준비하는 장입니다. Steam판만 출시한다면 이 장의 코드는 연결하지 않아도 되고, 개념 절의 "모델별 설계 원칙"과 "손익 판단"만 읽어도 됩니다.

> **이 장의 범위와 한계**: 이 장은 인터페이스·가짜 서비스·게임 쪽 규칙까지 완성합니다. **실제 광고 SDK·Unity IAP·Remote Config 서비스는 연결하지 않으므로, 이 장을 마친 빌드의 광고·결제 수익은 0입니다.** 실제 연결은 SDK 버전마다 API가 바뀌어 공식 문서를 따라야 하며, 7단계에 버전 고정·구현 대응표·실기기 테스트 절차를 체크리스트로 두었습니다. 모바일 확장을 Go로 결정한 뒤 그 절차를 수행해야 수익이 발생합니다.

모바일 무료판을 준비하며 광고 SDK 샘플 코드를 그대로 붙이면 흔히 이렇게 됩니다.

```csharp
// PlayerController.cs, ResultScreen.cs, ShopPanel.cs ... 곳곳에
SomeAdsSdk.ShowRewarded("revive", (ok) => { ... });   // SDK 타입이 게임 전역에 퍼짐
```

그러면 세 가지가 망가집니다.

1. **에디터에서 테스트할 수 없습니다.** 광고 SDK는 대개 실기기에서만 광고를 보여줍니다. 부활 흐름 하나 확인하려고 매번 빌드해야 합니다.
2. **Steam 판이 오염됩니다.** 같은 코드베이스인데 PC 빌드에 모바일 광고 SDK가 따라 들어가거나 `#if`가 수십 군데 생깁니다.
3. **SDK 교체가 재작성이 됩니다.** 미디에이션을 바꾸거나 SDK 메이저 버전이 바뀌면 게임 코드를 전부 뒤져야 합니다.

더 근본적인 문제는 **설계 없이 광고를 넣는 것**입니다. "죽을 때마다 전면 광고"는 단기 수익을 조금 올리고 리텐션(24장)을 크게 떨어뜨릴 수 있습니다. 그리고 광고 수익 계산이 아무리 좋아 보여도 **사용자를 데려오는 비용**을 넣지 않으면 생계 판단에 쓸 수 없습니다. 이 장은 먼저 설계하고, 손익으로 판단하고, 인터페이스 뒤에 숨긴 뒤, 가짜 구현으로 흐름을 완성합니다.

## 개념

### 수익 모델별 설계 원칙

| 모델 | 돈이 나오는 곳 | 설계 원칙 | 흔한 실패 |
|---|---|---|---|
| 프리미엄 (유료 판매) | 구매 한 번 | 가격에 맞는 완성도·분량. 추가 과금 없음이 신뢰 | 유료 게임에 광고·과금 추가 → 부정 리뷰 |
| F2P + 광고 | 광고 노출 수 × 단가 | 세션 수·세션 길이가 곧 수익. 광고가 리텐션을 해치지 않게 | 전면 광고 남발로 이탈 |
| F2P + IAP | 소수 구매자 | 구매할 가치가 있는 편의·콘텐츠. 페이월로 막지 않기 | 무료 경험이 너무 빈약, 또는 과금 압박 |
| 하이브리드 | 광고 + IAP (+ 광고 제거) | 비구매자는 광고, 구매자는 광고 없는 경험 | 제거할 광고가 없는데 광고 제거를 팜, 또는 보상형까지 없애 손해 |

### 코인 러시의 수익 전략

```
1차 출시 — Steam (PC) : 유료 판매. 광고 없음, IAP 없음. (가격 전략은 26장)
                        25장 코드는 Steam 빌드에서 "제공 안 함"으로 동작

확장 트랙 — 모바일 무료판 : Steam 출시 후 판매·리뷰 반응과 아래 손익 계산으로 Go/No-Go
  보상형 광고   ① 부활: 사망 시 1판 1회, 체력 가득 부활
               ② 코인 2배: 결과 화면에서 이번 판 이월 코인 2배, 1판 1회
  전면 광고     기본 꺼짐. Remote Config로 "3판마다, 최소 3분 간격"을 실험 그룹에서만 켤 수 있게 준비
  IAP          starter_pack (비소모성): 코인 3,000 + 캐릭터 "금고지기" 해금 — 출시 때부터 판매
               remove_ads (비소모성): 전면 광고 제거 — "전면 광고가 켜진 사용자에게만" 노출
```

**상품은 실제 효용이 있을 때만 팝니다.** 기본 설정에서 전면 광고가 꺼져 있으므로, 그 상태의 사용자에게 `remove_ads`를 팔면 사도 경험이 전혀 바뀌지 않습니다. 그래서 `remove_ads`는 원격 설정에서 전면 광고가 켜진 실험 그룹에만 노출하고(4단계 `StoreService.ShouldOfferRemoveAds`), 이미 산 사용자는 이후 어떤 그룹이 되든 전면 광고를 보지 않습니다. 실험 그룹마다 상품의 효용이 달라지면 안 된다는 뜻이기도 합니다. 전면 광고를 전체에 켜지 않기로 결론이 나면 `remove_ads`의 신규 판매도 멈춥니다.

23장의 경제와 연결해 보면, 코인 2배 광고와 스타터 팩은 모두 **Source**를 늘립니다. 23장 캠페인의 "세 강화 10레벨 46판"이 광고를 매번 보는 사람에게는 크게 줄고, 스타터 팩 3,000코인은 채택 비용표로 세 강화 약 3레벨어치(3 × 1,190 = 3,570에 가까움)입니다. 광고·상품 보상의 크기는 반드시 메타 경제 표와 캠페인 시뮬레이터(초기 bank 3,000, `coinsBanked` ×2)에 넣고 다시 계산합니다.

### 보상형 광고 UX 원칙

| 원칙 | 코인 러시 적용 |
|---|---|
| **선택형**: 플레이어가 누를 때만 재생 | 부활 창의 "광고 보고 부활" 버튼. 닫기 버튼이 같은 크기로 보임 |
| **가치 교환이 명확**: 무엇을 받는지 누르기 전에 보여줌 | "광고 시청 → 체력 가득 부활", "이월 코인 745 → 1,490" |
| **자연스러운 멈춤 지점**: 플레이 흐름을 끊지 않음 | 사망 직후, 결과 화면. 전투 중에는 절대 없음 |
| **빈도 제한**: 보상이 경제를 무너뜨리지 않게 | 부활 1판 1회, 코인 2배 1판 1회 — 버튼이 아니라 파사드가 강제 |
| **실패 처리**: 광고가 없을 때(no fill) 조용히 대체 | 준비 안 됐으면 버튼을 숨김. "오류" 팝업 금지 |
| **보상은 끝까지 본 경우에만, 한 번만** | SDK의 "보상 획득" 결과에서만, 콜백이 두 번 와도 한 번 지급 |

### 전면 광고 주의

전면 광고(interstitial)는 플레이어가 선택하지 않은 광고입니다. 수익은 확실하지만 경험을 해치기 쉽습니다.

- **스토어·광고 네트워크 정책**은 예기치 않은 광고, 앱 사용을 방해하는 광고, 실수로 누르게 유도하는 배치를 금지합니다. 게임 플레이 도중 갑자기 뜨는 광고는 정책 위반 소지가 큽니다.
- 쓴다면 **화면 전환 지점**(결과 → 타이틀)에서만, **첫 세션에는 쓰지 않고**, **판 수·시간 간격으로 제한**합니다.
- 광고를 넣은 뒤에는 24장의 D1/D7과 세션 수를 반드시 비교합니다. 광고 수익이 올라도 리텐션 하락으로 총수익이 줄 수 있습니다.

### 광고 미디에이션

미디에이션은 **여러 광고 네트워크를 하나의 SDK로 묶어 노출마다 가장 높은 가격을 내는 네트워크를 고르는** 서비스입니다.

```
게임 ──▶ 미디에이션 SDK ──┬─▶ 네트워크 A 입찰 $6
                          ├─▶ 네트워크 B 입찰 $9   ◀── 낙찰, 광고 표시
                          └─▶ 네트워크 C 응답 없음
```

대표적인 선택지는 Unity LevelPlay, Google AdMob 미디에이션, AppLovin MAX입니다. 가격을 입찰로 정하는 방식(bidding)과 미리 정한 순서대로 요청하는 방식(waterfall)이 있고, 최근에는 입찰 비중이 큽니다. 1인 개발자는 **하나의 미디에이션을 고르고 그 문서대로** 연동합니다. 게임 코드는 `IAdService`만 보므로 나중에 바꿔도 됩니다.

### 광고 지표와 계산

| 지표 | 정의 |
|---|---|
| Impression (노출) | 광고가 실제로 화면에 표시된 횟수. 끝까지 봤는지와 무관 |
| eCPM | 노출 1,000회당 수익. `수익 ÷ 노출 × 1000` |
| Fill rate | 광고 요청 중 광고가 채워진 비율. `채워진 요청 ÷ 전체 요청` |
| Show rate | 광고 버튼을 본 사람 중 실제 시청을 시작한 비율 (게임 쪽 지표) |
| ARPDAU | 일일 활성 사용자 1명당 평균 수익. `일 수익 ÷ DAU` |

eCPM은 국가, 광고 형식, 시기, 네트워크에 따라 크게 달라서 공개된 평균값을 믿고 계획하면 안 됩니다. 아래는 **계산 방법을 보이기 위한 예시 수치**입니다.

```
[예시] DAU 5,000명
  부활 창 표시 12,000회 (DAU당 3판 × 사망 80%) × show rate 25% × fill 90% = 노출 2,700회
  코인 2배 광고 노출 2,300회 (같은 방식) → 보상형 총 노출 5,000회

  eCPM $10 (예시) → 일 광고 수익 = 5,000 × 10 ÷ 1000 = $50
  ARPDAU(광고) = $50 ÷ 5,000 = $0.01

  starter_pack: 신규 사용자 중 구매 0.5% (예시), 일 신규 1,000명, 가격 $4.99, 스토어 수수료 15% 가정
  → 일 IAP 순수익 ≈ 1,000 × 0.005 × 4.99 × 0.85 ≈ $21.2
```

이런 계산의 쓸모는 **어떤 손잡이가 수익에 가장 크게 작용하는지** 보는 데 있습니다. 위 예시에서는 eCPM을 협상할 수 없는 1인 개발자가 움직일 수 있는 것이 DAU(리텐션), 사망 비율(22·23장 난이도), show rate(부활 창 UX)라는 것이 보입니다. 스토어 수수료는 기본 30%이고, 두 스토어 모두 연 매출 100만 달러 이하 구간 등에 15%를 적용하는 프로그램이 있습니다(조건·신청 여부는 각 스토어 정책 확인, 바뀔 수 있음).

### 사용자 확보 비용과 손익: CPI·LTV·ROAS

위 계산은 "DAU 5,000명"을 **주어진 값**으로 시작했습니다. 실제로는 그 사용자를 데려오고 붙잡아 두는 데 돈과 시간이 듭니다. 모바일 무료 게임은 스토어에 올리기만 해서는 설치가 거의 일어나지 않는 경우가 많아, 광고비를 쓰는 유료 확보(UA)를 검토하게 됩니다. 생계 판단에는 다음 지표를 씁니다.

| 지표 | 정의 |
|---|---|
| CPI | 설치 1건당 확보 비용. `광고비 ÷ 유료 설치 수` |
| 코호트 누적 순수익 (LTV) | 같은 날 설치한 사용자 1명이 n일 동안 만든 **개발자 수령액**(스토어 수수료·광고 네트워크 몫 제외) 합계. 기간을 반드시 붙여 말함 (D30 LTV 등) |
| ROAS | `코호트 누적 순수익 ÷ 그 코호트 광고비`. D7 ROAS, D30 ROAS처럼 기간별 |
| 회수 기간 | 누적 순수익이 CPI를 넘는 날 |

**소프트 론칭**은 본 출시 전에 한두 국가에서 작은 예산으로 이 수치를 실측하는 단계입니다. 계산 예(모두 가상 수치)입니다.

```
[소프트 론칭 4주, 한 국가]  광고비 $2,000 → 유료 설치 1,600  → CPI = $1.25
코호트 1인당 누적 순수익:   D1 $0.03 · D7 $0.12 · D30 $0.31 · D90(추세 추정) $0.45
D30 ROAS = 0.31 ÷ 1.25 = 25%     D90 추정 ROAS = 36%   → 90일 안에 회수 못 함
```

월 손익표에는 **운영비와 개발자 시간**까지 넣습니다. 코호트 수익은 90일에 걸쳐 들어오므로 "이달 설치 코호트가 앞으로 벌 돈"으로 계산하고, 입금 시점(스토어·네트워크 정산 지연)과 세금·환율은 29장 현금흐름표에서 따로 다룹니다.

| 항목 (월, 가상) | 유료 확보 포함 | 자연 유입만 |
|---|---|---|
| 신규 설치 | 4,000 (자연 2,400 + 유료 1,600) | 2,400 |
| 코호트 기대 순수익 (× D90 $0.45) | $1,800 | $1,080 |
| 광고비 | −$2,000 | $0 |
| 도구·계정·서버 | −$60 | −$60 |
| 운영·업데이트 시간 (주 10시간 × 4.3주 × 시간 가치 $20) | −$860 | −$860 |
| **코호트 기준 월 손익** | **−$1,120** | **+$160** |

**확장·중단 기준은 소프트 론칭 전에 적어 둡니다**(24장의 판단 기준과 같은 이유).

```
- 유료 확보 시작 조건: D1 ≥ 30%, D7 ≥ 10% (리텐션이 낮으면 광고비는 새는 양동이에 붓는 물)
- 광고비 확대: D30 ROAS ≥ 50%이고 D90 추정 ROAS ≥ 110% → 예산 2배로 4주 재측정
- 유료 확보 중단: D90 추정 ROAS < 70% → 자연 유입만으로 운영
- 모바일판 유지보수 모드: 자연 유입 기준 월 손익이 3개월 연속 음수 → 신규 콘텐츠 중단, 버그 수정만
```

위 가상 사례는 "유료 확보 중단, 자연 유입만"이고, 그마저 운영 시간 가치를 겨우 넘기는 수준입니다. 1인 개발자에게 모바일 무료판은 "만들면 광고 수익이 생긴다"가 아니라, **확보 비용을 넘는 리텐션과 수익을 실측으로 증명해야 하는 사업**입니다. 이것이 1차 출시를 Steam 유료로 둔 이유 중 하나입니다.

### 동의 흐름: GDPR 광고 게재 방식과 ATT

광고 SDK는 기기 식별자 등으로 맞춤 광고를 합니다. 그래서 광고를 요청하기 **전에** 동의를 처리합니다.

```
앱 시작
  │
  ├─ ① 개인정보 동의 (EEA·영국 등, GDPR)
  │     Google 광고를 이 지역 사용자에게 게재하려면 Google 인증 CMP(예: Google UMP) 사용이 요구됨
  │     동의 결과(IAB TCF 목적별 동의)에 따라 게재 방식이 갈린다 — Google 기준:
  │       맞춤 광고    목적 1·3·4 등 여러 목적에 대한 동의가 모두 있을 때
  │       비맞춤 광고  맞춤화에 쓰지는 않지만, 목적 1(기기에 정보 저장·접근) 동의가 여전히 필요
  │                   (빈도 제한 등에 쿠키·식별자 사용)
  │       제한적 광고  목적 1 동의가 없을 때. 개인화와 로컬 식별자를 쓰는 기능을 모두 끈 광고
  │     "거부하면 비맞춤 광고"가 아니다. 무엇을 거부했는지에 따라 비맞춤·제한적·게재 불가가 갈린다
  │
  │     Unity용 UMP(GoogleMobileAds.Ump.Api) 흐름:
  │       ConsentInformation.Update(요청 매개변수, 콜백)          ← 매 실행
  │       → ConsentForm.LoadAndShowConsentFormIfRequired(콜백)   ← 필요할 때만 양식 표시
  │       → ConsentInformation.CanRequestAds()가 true일 때만 광고 SDK 초기화·요청
  │       설정 화면에는 ConsentForm.ShowPrivacyOptionsForm으로 동의 변경 진입점
  │
  ├─ ② iOS 앱 추적 투명성 (ATT)
  │     다른 회사 앱·웹과 연결해 추적하려면 AppTrackingTransparency 권한 요청
  │     Info.plist에 NSUserTrackingUsageDescription 문구 필요
  │
  ├─ ③ 24장 애널리틱스 동의 (자체)
  │
  └─ ④ 광고 SDK 초기화 (동의 결과를 SDK에 전달)
```

UMP의 메서드 이름은 플러그인 버전에 따라 달라질 수 있으니 설치한 버전의 공식 문서를 확인하고, 미디에이션을 쓰면 각 네트워크에 동의를 전달하는 방법도 미디에이션 문서를 따릅니다. 어린이를 대상으로 하거나 어린이가 주 이용자일 수 있는 게임은 맞춤 광고 자체가 제한되니(스토어 가족 정책 등) 별도로 확인하세요.

### IAP: 상품 유형, 구매 처리 순서, 복원

| 유형 | 예 | 특징 |
|---|---|---|
| 소모성 (Consumable) | 코인 1,000개 | 여러 번 구매. 지급 기록은 게임(또는 서버)이 책임 |
| 비소모성 (Non-consumable) | 광고 제거, 스타터 팩 | 한 번 구매, 영구 소유. **복원 가능해야 함** |
| 구독 (Subscription) | 월간 VIP | 기간 갱신, 만료·취소 처리 필요 |

구매 한 건은 스토어와 게임 사이의 **거래**입니다. 게임이 보상을 영구히 기록하기 전에 스토어에 "처리 완료"를 알리면, 저장 실패·앱 종료 한 번으로 돈은 나갔는데 보상은 없는 상태가 됩니다. 반대로 확인을 끝내 보내지 않으면 스토어가 같은 거래를 계속 다시 보내고, 일부 스토어는 일정 기간 뒤 자동 환불합니다. 그래서 순서를 고정합니다.

```
스토어: "거래 T1(상품 starter_pack) 결제됨, 처리 대기"   ← 구매 직후, 또는 다음 실행 때 재전달, 또는 복원
   │
   ① 검증   영수증이 진짜인가 (광고 제거 수준은 기기 내 검증, 재화·서버 데이터는 서버 검증)
   ② 중복   T1을 이미 지급했는가 (세이브의 거래 ID 목록)
   ③ 지급·영속화   보상을 세이브에 넣고 저장 성공까지 확인 (이미 지급했어도 저장은 다시 확인)
   ④ 구매 확인     저장이 성공한 뒤에만 스토어에 확인(confirm/acknowledge)
      └─ 저장 실패 → 확인하지 않고 종료 → 스토어가 다음 실행에 T1을 다시 전달 → ②에서 중복 방지
```

Unity IAP 5.x에서는 `OnPurchasePending` 콜백이 "처리 대기" 거래를 전달하고, 게임이 지급을 끝낸 뒤 `ConfirmPurchase`(대기 주문 객체를 인자로)를 호출합니다. 확인하지 않은 구매는 다음 실행에 다시 전달됩니다([Unity IAP 구매 처리 문서](https://docs.unity.com/en-us/iap/purchases)). 이 장의 `IStoreService` 계약은 이 순서를 그대로 옮긴 것입니다.

- **영수증 검증**: 클라이언트는 조작될 수 있습니다. 광고 제거처럼 피해가 작은 상품은 기기 내 검증으로 시작해도 되지만, 재화처럼 경제에 영향을 주거나 서버 데이터와 연결되는 상품은 **서버 검증**(App Store Server API, Google Play Developer API 등)이 원칙입니다.
- **구매 복원**: 기기를 바꾸거나 재설치한 사용자가 비소모성 상품을 되찾는 기능입니다. iOS는 복원 버튼이 없으면 심사에서 거절될 수 있습니다(기초 트랙 4-4).
- **가격 표시**: 코드에 "₩3,300"을 쓰지 말고 스토어가 돌려준 현지화 가격 문자열을 표시합니다.
- **Unity IAP 버전 주의**: Unity IAP는 5.x에서 초기화·구매 API가 크게 바뀌었습니다. 기초 트랙 4-4의 `IStoreListener` 예제는 이전 방식입니다. **설치한 버전의 공식 문서를 기준으로** 아래 `IStoreService`를 구현하세요.

### Remote Config와 A/B 테스트

**Remote Config**는 앱 업데이트 없이 서버에서 값을 내려받아 게임 설정을 바꾸는 기능입니다(Unity Remote Config, Firebase Remote Config 등). 광고 빈도, 보상 배율, 상품 노출 조건을 코드 상수가 아니라 원격 값으로 두면 문제가 생겼을 때 즉시 끌 수 있습니다.

**A/B 테스트**는 사용자를 무작위로 나눠 한 가지만 다르게 하고 지표를 비교합니다. 설계 순서입니다.

```
1. 가설     "부활 광고를 1판 2회로 늘려도 D1 리텐션은 떨어지지 않고 보상형 노출은 늘어난다"
2. 변경     한 가지만: reviveMaxPerRun 1 → 2
3. 주 지표   사용자당 보상형 노출 수 (끝까지 봤는지와 무관한 "노출" 이벤트로 셈)
   보호 지표 D1 리텐션, 판당 플레이 시간 (이게 나빠지면 주 지표가 좋아도 중단)
4. 배정     사용자 ID 기준으로 고정 배정 (앱을 다시 켜도 같은 그룹), 배정 사실을 이벤트로 기록
5. 기간·표본 보호 지표의 허용 하락폭까지 감지할 수 있게 미리 정하고, 중간에 결과를 보며 멈추지 않는다
```

**표본 크기 감각**: 비율 지표(리텐션, 구매 전환율)에서 차이를 발견하는 데 필요한 그룹당 인원은 대략 다음 경험식으로 어림합니다(유의수준 5%, 검정력 80% 기준의 근사).

```
그룹당 n ≈ 16 × p × (1 − p) ÷ δ²      p = 기준 비율, δ = 발견하고 싶은 차이

D1 리텐션 30% → 3%p 차이  : 16 × 0.3 × 0.7 ÷ 0.03²  ≈ 3,700명 / 그룹
D1 리텐션 30% → 2%p 차이  : 16 × 0.3 × 0.7 ÷ 0.02²  ≈ 8,400명 / 그룹
구매 전환 1.0% → 1.3%     : 16 × 0.01 × 0.99 ÷ 0.003² ≈ 17,600명 / 그룹
```

**표본은 가장 작은 차이를 봐야 하는 지표에 맞춥니다.** "D1이 2%p 이상 떨어지면 중단"이 보호 기준이라면 3%p 감지용 3,700명으로는 그 판단을 할 수 없고 약 8,400명이 필요합니다(비열등성 검정은 한쪽 검정이라 정확한 수는 조금 다르므로, 실제 실험에서는 표본 크기 계산기로 확인). 마지막 줄도 중요한 교훈입니다. **작은 전환율의 작은 차이는 신규 사용자가 적은 인디 게임에서 사실상 검증할 수 없습니다.** 트래픽이 적을 때는 큰 차이가 날 만한 변경만 실험하고, 나머지는 원칙과 정성 테스트(24장)로 판단합니다.

### 한국: 확률형 아이템 정보 공개

코인 러시에는 확률형 아이템이 없습니다. 만약 "코인으로 뽑는 캐릭터 상자"를 유료 재화와 연결해 넣는다면, 한국에서는 개정 게임산업진흥법(2024년 3월 22일 시행, 법 제33조 제2항, 시행령 별표 3의2)에 따라 표시 의무가 생기며, **매체마다 표시할 내용이 다릅니다.**

| 매체 | 표시 내용·방법 (시행령 별표 3의2 요약) |
|---|---|
| 게임물 안 | 확률형 아이템의 종류·종류별 공급 확률 등을 구매·조회·사용 화면에 직접 표시. 화면이 작아 불가피하면 확률이 표시된 홈페이지 화면으로 곧바로 연결 |
| 인터넷 홈페이지 | 같은 정보를 문자열·숫자열로 검색 가능한 형태로 표시 |
| 광고·선전물 | 원칙적으로 **"게임물에 확률형 아이템이 포함되어 있다"는 사실**을 부호·문자·음성·이미지·영상 등으로 표시. 확률 수치 자체가 아님. 배너 광고처럼 크기·형식상 표시가 어려운 불가피한 경우 예외 |

확률 정보를 바꿀 때는 변경 내용과 시점을 미리 게임과 홈페이지에 게시해야 하는 규정도 있습니다. 대상 범위(유상 재화로 직간접적으로 얻는 경우 등)와 세부는 시행령 원문과 게임물관리위원회 안내를 확인하고, 해외 스토어·국가별 규제도 따로 확인하세요(법령은 바뀔 수 있음). 21장 MoSCoW에서 가챠를 Won't로 둔 이유 중 하나입니다.

## 실습: 코인 러시에 적용하기

이 실습의 동작 확인은 **Build Profiles에서 Android(또는 iOS) 플랫폼으로 전환한 에디터**에서 합니다. Windows/Mac(Steam) 플랫폼에서는 5단계 분기에 따라 광고·IAP가 "제공 안 함"으로 동작하는 것이 정상입니다.

### 1단계: 광고·상품 배치표

`Docs/monetization.md`에 먼저 확정합니다. **값은 예시**이며 Remote Config로 바뀔 수 있는 항목에 표시합니다.

| 배치 ID | 형식 | 위치 | 보상/효과 | 빈도 제한 | 원격 조절 | 광고 제거 구매자 |
|---|---|---|---|---|---|---|
| `revive` | 보상형 | 사망 직후 부활 창 | 체력 가득 부활 | 1판 1회 | `reviveEnabled`, `reviveMaxPerRun` | 유지 |
| `double_coins` | 보상형 | 결과 화면 | 이월 코인 ×2 | 1판 1회 | `doubleCoinsEnabled` | 유지 |
| `result_to_title` | 전면 | 결과 → 타이틀 | — | N판마다, 최소 간격 | `interstitialEnabled`(기본 false), `interstitialEveryNRuns`, `interstitialMinSeconds` | **표시 안 함** |

| 상품 ID | 유형 | 내용 | 판매(노출) 조건 | 가격 표시 |
|---|---|---|---|---|
| `starter_pack` | 비소모성 | 코인 3,000 + 캐릭터 "금고지기" 해금 | 소유하지 않은 사용자 | 스토어 현지화 가격 |
| `remove_ads` | 비소모성 | 전면 광고 제거 (보상형 버튼은 유지) | **`interstitialEnabled`가 true인 사용자**이고 소유하지 않음 | 스토어 현지화 가격 |

"광고 제거 구매자에게 보상형은 유지"는 실무에서 자주 쓰는 규칙입니다. 보상형은 플레이어가 원해서 보는 **이득**이므로, 이것까지 없애면 돈을 내고 손해를 보는 셈이 됩니다. 구매 페이지에 "선택형 보상 광고는 계속 이용할 수 있습니다"라고 적어둡니다. 그리고 반대 방향의 규칙도 함께 적습니다. **제거할 전면 광고가 없는 사용자에게는 광고 제거를 팔지 않습니다.**

### 2단계: 광고 인터페이스와 가짜 광고

파일: `Assets/_CoinRush/Scripts/Monetization/IAdService.cs`

```csharp
using System;

public enum AdResult { Rewarded, Skipped, Failed, NotReady }

public static class AdPlacements
{
    public const string Revive = "revive";
    public const string DoubleCoins = "double_coins";
    public const string ResultToTitle = "result_to_title";
}

public interface IAdService
{
    bool IsRewardedReady { get; }
    bool IsInterstitialReady { get; }

    /// <param name="onShown">광고가 화면에 실제로 표시된 순간 (노출). 표시되지 못하면 호출되지 않는다</param>
    /// <param name="onComplete">광고가 닫힌 뒤 결과. 구현은 한 번만 호출해야 한다</param>
    void ShowRewarded(string placement, Action onShown, Action<AdResult> onComplete);
    void ShowInterstitial(string placement, Action onShown, Action onClosed);
}
```

에디터용 가짜 구현입니다. 광고 로딩 지연, 채워지지 않음(no fill), 중간에 닫기, 재생 실패를 모두 흉내 냅니다. 파일: `Assets/_CoinRush/Scripts/Monetization/FakeAdService.cs`

```csharp
using System;
using UnityEngine;

public class FakeAdService : MonoBehaviour, IAdService
{
    [SerializeField, Range(0f, 1f)] private float fillRate = 0.9f;
    [SerializeField] private float loadSeconds = 2f;

    private float rewardedReadyAt, interstitialReadyAt;
    private bool rewardedFilled = true, interstitialFilled = true;
    private string showingPlacement;            // null이면 표시 중 아님
    private bool showingRewarded;
    private Action<AdResult> rewardedCallback;
    private Action interstitialCallback;

    public bool IsRewardedReady => showingPlacement == null && rewardedFilled && Time.unscaledTime >= rewardedReadyAt;
    public bool IsInterstitialReady => showingPlacement == null && interstitialFilled && Time.unscaledTime >= interstitialReadyAt;

    public void ShowRewarded(string placement, Action onShown, Action<AdResult> onComplete)
    {
        if (!IsRewardedReady) { onComplete?.Invoke(AdResult.NotReady); return; }
        showingPlacement = placement; showingRewarded = true; rewardedCallback = onComplete;
        onShown?.Invoke();                                  // 가짜 광고는 요청 즉시 화면에 뜬다
    }

    public void ShowInterstitial(string placement, Action onShown, Action onClosed)
    {
        if (!IsInterstitialReady) { onClosed?.Invoke(); return; }
        showingPlacement = placement; showingRewarded = false; interstitialCallback = onClosed;
        onShown?.Invoke();
    }

    private void OnGUI()
    {
        if (showingPlacement == null) return;
        GUI.Box(new Rect(0, 0, Screen.width, Screen.height), "");
        var area = new Rect(Screen.width * 0.2f, Screen.height * 0.3f, Screen.width * 0.6f, Screen.height * 0.4f);
        GUILayout.BeginArea(area, $"가짜 {(showingRewarded ? "보상형" : "전면")} 광고 — {showingPlacement}", GUI.skin.window);
        if (showingRewarded)
        {
            if (GUILayout.Button("끝까지 시청 (보상 지급)", GUILayout.Height(50))) FinishRewarded(AdResult.Rewarded);
            if (GUILayout.Button("중간에 닫기 (보상 없음)", GUILayout.Height(50))) FinishRewarded(AdResult.Skipped);
            if (GUILayout.Button("재생 실패", GUILayout.Height(50))) FinishRewarded(AdResult.Failed);
        }
        else if (GUILayout.Button("닫기", GUILayout.Height(50)))
        {
            showingPlacement = null;
            ScheduleReload(ref interstitialReadyAt, ref interstitialFilled);
            Action callback = interstitialCallback;
            interstitialCallback = null;
            callback?.Invoke();
        }
        GUILayout.EndArea();
    }

    private void FinishRewarded(AdResult result)
    {
        showingPlacement = null;
        ScheduleReload(ref rewardedReadyAt, ref rewardedFilled);
        Action<AdResult> callback = rewardedCallback;
        rewardedCallback = null;                            // 한 번만 호출
        callback?.Invoke(result);                           // 실제 SDK처럼 콜백은 광고가 닫힌 뒤
    }

    private void ScheduleReload(ref float readyAt, ref bool filled)
    {
        readyAt = Time.unscaledTime + loadSeconds;          // 광고는 한 번 쓰면 다시 로드해야 한다
        filled = UnityEngine.Random.value < fillRate;        // 채워지지 않는 경우도 흉내
        if (!filled) Invoke(nameof(RetryFill), loadSeconds * 2f);
    }

    private void RetryFill() { rewardedFilled = true; interstitialFilled = true; }
}
```

부활 창이 게임을 멈춘 상태에서 광고가 재생되므로 `Time.unscaledTime`을 씁니다(`Invoke` 재시도는 스케일된 시간이라 멈춘 동안 미뤄지는 단순화가 있습니다).

### 3단계: 스토어 인터페이스와 가짜 스토어

개념 절의 구매 처리 순서를 **계약**으로 만듭니다. 스토어는 거래를 `PurchasePending`으로 알리기만 하고, 게임이 지급·저장을 끝낸 뒤 `ConfirmPurchase`를 부를 때까지 그 거래를 "미확정"으로 들고 있다가 다음 실행에 다시 보냅니다. 파일: `Assets/_CoinRush/Scripts/Monetization/IStoreService.cs`

```csharp
using System;

public enum ProductKind { Consumable, NonConsumable, Subscription }
// Pending: 결제 승인 대기(보호자 승인 등), 또는 결제는 됐지만 지급 저장이 실패해 확인을 보류함(다음 실행에 재처리)
public enum PurchaseOutcome { Success, Pending, Cancelled, Failed }

public static class ProductIds
{
    public const string RemoveAds = "remove_ads";
    public const string StarterPack = "starter_pack";
}

/// <summary>스토어가 "결제됨, 처리 대기"로 넘기는 거래 한 건</summary>
public readonly struct PendingPurchase
{
    public readonly string TransactionId;
    public readonly string ProductId;

    public PendingPurchase(string transactionId, string productId)
    {
        TransactionId = transactionId;
        ProductId = productId;
    }
}

public interface IStoreService
{
    /// <summary>
    /// 구매 직후, 미확정 거래의 재전달(다음 실행), 복원에서 발생. 보상 지급은 이 이벤트 한 곳에서만 한다.
    /// 받는 쪽은 검증 → 중복 확인 → 지급·영속화를 끝낸 뒤에만 ConfirmPurchase를 호출해야 한다.
    /// 영속화 실패(SaveSystem.Save가 false)면 ConfirmPurchase를 호출하지 않는다 → 미확정으로 남아 다시 전달된다.
    /// </summary>
    event Action<PendingPurchase> PurchasePending;

    bool IsReady { get; }
    string GetLocalizedPrice(string productId);   // 스토어가 준 현지화 가격 문자열
    bool Owns(string productId);                   // 비소모성·구독 소유 여부
    void Purchase(string productId, Action<PurchaseOutcome> onComplete);
    void ConfirmPurchase(PendingPurchase purchase);   // 이미 확정된 거래(복원분)면 아무 일도 하지 않는다
    void RestorePurchases(Action<bool> onComplete);
}
```

**보상 지급을 `PurchasePending` 한 곳으로 모으는 것**이 핵심입니다. 구매 버튼 콜백에서 코인을 주면, 결제 앱으로 넘어간 사이 게임이 종료됐다가 다음 실행 때 전달되는 거래나 복원에서 보상이 누락됩니다.

가짜 스토어는 미확정 거래를 `PlayerPrefs`에 보관했다가 `Start`에서 다시 보냅니다. "지급 전에 앱 종료" 버튼으로 재전달 경로를 에디터에서 시험할 수 있습니다. 파일: `Assets/_CoinRush/Scripts/Monetization/FakeStoreService.cs`

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

public class FakeStoreService : MonoBehaviour, IStoreService
{
    private const string OwnedKeyPrefix = "fake_store_owned_";       // 값 = 소유를 만든 거래 ID
    private const string UnconfirmedKey = "fake_store_unconfirmed";  // "거래ID|상품ID;거래ID|상품ID"

    private static readonly Dictionary<string, (ProductKind kind, string price)> Catalog =
        new Dictionary<string, (ProductKind, string)>
        {
            { ProductIds.RemoveAds, (ProductKind.NonConsumable, "₩3,300 (가짜)") },
            { ProductIds.StarterPack, (ProductKind.NonConsumable, "₩5,500 (가짜)") },
        };

    public event Action<PendingPurchase> PurchasePending;
    public bool IsReady => true;

    private string pendingProduct;
    private Action<PurchaseOutcome> pendingCallback;

    // 실제 스토어도 앱이 시작되면 확인되지 않은 거래를 다시 전달한다
    private void Start()
    {
        foreach (PendingPurchase p in LoadUnconfirmed()) PurchasePending?.Invoke(p);
    }

    public string GetLocalizedPrice(string productId) =>
        Catalog.TryGetValue(productId, out var p) ? p.price : "";

    public bool Owns(string productId) => PlayerPrefs.HasKey(OwnedKeyPrefix + productId);

    public void Purchase(string productId, Action<PurchaseOutcome> onComplete)
    {
        if (!Catalog.ContainsKey(productId) || pendingProduct != null) { onComplete?.Invoke(PurchaseOutcome.Failed); return; }
        if (Catalog[productId].kind == ProductKind.NonConsumable && Owns(productId))
        {
            onComplete?.Invoke(PurchaseOutcome.Failed);   // 실제 스토어도 이미 소유한 비소모성은 재구매 불가
            return;
        }
        pendingProduct = productId;
        pendingCallback = onComplete;
    }

    public void ConfirmPurchase(PendingPurchase purchase)
    {
        List<PendingPurchase> list = LoadUnconfirmed();
        if (list.RemoveAll(p => p.TransactionId == purchase.TransactionId) > 0) SaveUnconfirmed(list);
    }

    public void RestorePurchases(Action<bool> onComplete)
    {
        foreach (string id in Catalog.Keys)
            if (Catalog[id].kind != ProductKind.Consumable && Owns(id))
                PurchasePending?.Invoke(new PendingPurchase(PlayerPrefs.GetString(OwnedKeyPrefix + id), id));
        onComplete?.Invoke(true);
    }

    private void OnGUI()
    {
        if (pendingProduct == null) return;
        var area = new Rect(Screen.width * 0.2f, Screen.height * 0.25f, Screen.width * 0.6f, Screen.height * 0.5f);
        GUILayout.BeginArea(area, $"가짜 결제 — {pendingProduct} {GetLocalizedPrice(pendingProduct)}", GUI.skin.window);
        if (GUILayout.Button("구매", GUILayout.Height(40))) Complete(PurchaseOutcome.Success, deliverNow: true);
        if (GUILayout.Button("구매 — 지급 전에 앱 종료 흉내 (Play 중지 후 재시작)", GUILayout.Height(40)))
            Complete(PurchaseOutcome.Success, deliverNow: false);
        if (GUILayout.Button("결제 승인 대기", GUILayout.Height(40))) Complete(PurchaseOutcome.Pending, deliverNow: false);
        if (GUILayout.Button("사용자 취소", GUILayout.Height(40))) Complete(PurchaseOutcome.Cancelled, deliverNow: false);
        if (GUILayout.Button("결제 실패", GUILayout.Height(40))) Complete(PurchaseOutcome.Failed, deliverNow: false);
        GUILayout.EndArea();
    }

    private void Complete(PurchaseOutcome outcome, bool deliverNow)
    {
        string id = pendingProduct;
        Action<PurchaseOutcome> callback = pendingCallback;
        pendingProduct = null;
        pendingCallback = null;

        if (outcome == PurchaseOutcome.Success)
        {
            var purchase = new PendingPurchase(Guid.NewGuid().ToString("N"), id);
            if (Catalog[id].kind != ProductKind.Consumable) PlayerPrefs.SetString(OwnedKeyPrefix + id, purchase.TransactionId);
            List<PendingPurchase> list = LoadUnconfirmed();
            list.Add(purchase);
            SaveUnconfirmed(list);                      // 확인 전까지 미확정으로 보관
            if (deliverNow) PurchasePending?.Invoke(purchase);
            if (deliverNow && LoadUnconfirmed().Exists(p => p.TransactionId == purchase.TransactionId))
                outcome = PurchaseOutcome.Pending;     // 수신자가 저장에 실패해 확인하지 않았다
        }
        callback?.Invoke(outcome);
    }

    private static List<PendingPurchase> LoadUnconfirmed()
    {
        var list = new List<PendingPurchase>();
        foreach (string entry in PlayerPrefs.GetString(UnconfirmedKey, "").Split(';'))
        {
            string[] parts = entry.Split('|');
            if (parts.Length == 2) list.Add(new PendingPurchase(parts[0], parts[1]));
        }
        return list;
    }

    private static void SaveUnconfirmed(List<PendingPurchase> list)
    {
        var entries = new List<string>(list.Count);
        foreach (PendingPurchase p in list) entries.Add(p.TransactionId + "|" + p.ProductId);
        PlayerPrefs.SetString(UnconfirmedKey, string.Join(";", entries));
        PlayerPrefs.Save();
    }

    [ContextMenu("가짜 구매 기록 모두 삭제")]
    private void ClearFakePurchases()
    {
        foreach (string id in Catalog.Keys) PlayerPrefs.DeleteKey(OwnedKeyPrefix + id);
        PlayerPrefs.DeleteKey(UnconfirmedKey);
    }
}
```

### 4단계: 정적 파사드 — 규칙은 여기에

게임 코드가 부르는 곳입니다. 빈도 제한, 판 단위 초기화, 광고 제거·상품 노출 규칙, 애널리틱스 기록을 **한 곳에서** 강제합니다. 버튼이 `CanOffer…` 검사를 빠뜨려도 `ShowRewarded` 안에서 다시 검사하므로 한도가 뚫리지 않습니다. 파일: `Assets/_CoinRush/Scripts/Monetization/AdService.cs`

```csharp
using System;
using UnityEngine;

/// <summary>원격으로 조절하는 수익화 설정. 기본값은 "안전한 쪽".</summary>
[Serializable]
public class MonetizationConfig
{
    public bool reviveEnabled = true;
    public int reviveMaxPerRun = 1;
    public bool doubleCoinsEnabled = true;
    public bool interstitialEnabled = false;
    public int interstitialEveryNRuns = 3;
    public float interstitialMinSeconds = 180f;
    public string experimentName = "";          // 비어 있으면 실험 없음
    public string experimentGroup = "control";
}

public static class StoreService
{
    public static IStoreService Current { get; private set; }
    public static void Install(IStoreService service) => Current = service;
    public static bool HasRemoveAds => Current != null && Current.Owns(ProductIds.RemoveAds);

    /// <summary>제거할 전면 광고가 있는 사용자에게만 광고 제거를 판다</summary>
    public static bool ShouldOfferRemoveAds =>
        Current != null && Current.IsReady && AdService.Config.interstitialEnabled && !HasRemoveAds;
}

public static class AdService
{
    public static IAdService Current { get; private set; }
    public static MonetizationConfig Config { get; private set; } = new MonetizationConfig();
    public static string CurrentRunId { get; private set; }

    private static int revivesThisRun;
    private static bool doubledThisRun;
    private static bool showing;                 // 보상형 광고 요청~닫힘 사이
    private static int runsSinceInterstitial;
    private static float lastInterstitialTime = float.NegativeInfinity;

    public static void Install(IAdService service, MonetizationConfig config)
    {
        Current = service;
        Config = config ?? new MonetizationConfig();
    }

    /// <summary>23장 RunRecorder.RunStarted에서만 호출 (5단계 부트스트랩이 구독). 레벨업 복귀·부활로는 초기화되지 않는다.</summary>
    public static void OnRunStarted(string runId)
    {
        CurrentRunId = runId;
        revivesThisRun = 0;
        doubledThisRun = false;
    }

    // 광고 제거 구매자도 보상형은 유지한다 → HasRemoveAds를 검사하지 않는다
    public static bool CanOfferRevive =>
        Current != null && !showing && Config.reviveEnabled && revivesThisRun < Config.reviveMaxPerRun && Current.IsRewardedReady;

    public static bool CanOfferDoubleCoins =>
        Current != null && !showing && Config.doubleCoinsEnabled && !doubledThisRun && Current.IsRewardedReady;

    public static void ShowRewarded(string placement, Action<bool> onFinished)
    {
        bool allowed = placement == AdPlacements.Revive ? CanOfferRevive
                     : placement == AdPlacements.DoubleCoins && CanOfferDoubleCoins;
        if (!allowed) { onFinished?.Invoke(false); return; }

        // 한도를 요청 시점에 먼저 차지 → 콜백이 오기 전에 같은 판에서 다시 요청해도 막힘
        showing = true;
        string runId = CurrentRunId;
        if (placement == AdPlacements.Revive) revivesThisRun++; else doubledThisRun = true;
        Analytics.Track("ad_rewarded_request", ("placement", placement), ("group", Config.experimentGroup));

        bool finished = false;
        Current.ShowRewarded(placement,
            onShown: () => Analytics.Track("ad_impression", ("format", "rewarded"), ("placement", placement),
                                           ("group", Config.experimentGroup)),
            onComplete: result =>
            {
                if (finished) return;                 // SDK가 콜백을 두 번 보내도 한 번만 처리
                finished = true;
                showing = false;
                bool rewarded = result == AdResult.Rewarded;
                if (!rewarded && runId == CurrentRunId)   // 보상이 없으면 같은 판에 한해 기회를 돌려줌
                {
                    if (placement == AdPlacements.Revive) revivesThisRun--; else doubledThisRun = false;
                }
                Analytics.Track("ad_rewarded_end", ("placement", placement), ("result", result.ToString()));
                onFinished?.Invoke(rewarded);
            });
    }

    /// <summary>결과 → 타이틀 전환 시 호출. 조건이 안 맞으면 광고 없이 곧바로 onDone.</summary>
    public static void TryShowInterstitial(string placement, Action onDone)
    {
        runsSinceInterstitial++;
        bool allowed = Current != null
                       && Config.interstitialEnabled
                       && !StoreService.HasRemoveAds
                       && runsSinceInterstitial >= Config.interstitialEveryNRuns
                       && Time.realtimeSinceStartup - lastInterstitialTime >= Config.interstitialMinSeconds
                       && Current.IsInterstitialReady;
        if (!allowed) { onDone?.Invoke(); return; }

        runsSinceInterstitial = 0;
        lastInterstitialTime = Time.realtimeSinceStartup;
        Current.ShowInterstitial(placement,
            onShown: () => Analytics.Track("ad_impression", ("format", "interstitial"), ("placement", placement),
                                           ("group", Config.experimentGroup)),
            onClosed: onDone);
    }
}
```

`realtimeSinceStartup`은 앱 실행 후 시간이라 재시작하면 0부터 다시 셉니다. 즉 "최소 간격"은 세션 안에서만 보장됩니다. 세션을 넘는 제한이 필요하면 마지막 시각을 `PlayerPrefs`에 저장하세요(기기 시계를 과거로 돌린 경우 차이가 음수가 되니 "방금 표시함"으로 취급).

### 5단계: 부트스트랩, 구매 처리, 세이브 v3

**10장 `SaveData`를 v3로 올립니다.** 스타터 팩 지급 여부, 해금 캐릭터, 처리한 거래 ID가 필요합니다. 10장 규칙대로 필드를 추가하고 마이그레이션 단계를 하나 더합니다(10장 연습 문제 2로 이미 v3를 만들었다면 번호를 하나씩 올려 v4로 적용).

```csharp
// SaveData.cs (10장 v2) — 버전 교체, 필드 추가
public const int CurrentVersion = 3;

public bool starterPackGranted;                           // 스타터 팩 코인을 이 세이브에 지급했는가
public List<string> unlockedCharacters = new();           // "vault_keeper" 등
public List<string> grantedTransactions = new();          // 지급·저장을 끝낸 거래 ID (중복 지급 방지)
```

```csharp
// SaveMigrator.cs (10장) — Steps에 { 2, V2ToV3 } 추가, 메서드 추가
// 1.2 (v2 → v3): 수익화 필드 추가. 기존 데이터는 바꾸지 않는다.
private static void V2ToV3(JObject root)
{
    root["starterPackGranted"] ??= false;
    root["unlockedCharacters"] ??= new JArray();
    root["grantedTransactions"] ??= new JArray();
}
```

10장 `SaveMigrationTests`에 v2 샘플(`{"version":2,"coins":120,"upgrades":{"maxHp":1},"stats":{...}}`)을 넣어 v3로 올린 뒤 코인·강화가 유지되고 `grantedTransactions`가 빈 목록인지 확인하는 테스트를 추가합니다.

**부트스트랩**: 첫 씬(09장 부트스트랩 씬)에 둡니다. 플랫폼별로 구현을 고르고, 원격 설정을 적용하고, 판 시작을 구독하고, 구매를 처리합니다. 가짜 서비스는 **에디터 또는 `COINRUSH_FAKE_SERVICES` 정의가 있는 모바일 빌드**에서만 씁니다. `DEVELOPMENT_BUILD`에 묶으면 실기기 개발 빌드에서 실제 SDK를 시험할 길이 없어지기 때문입니다. 파일: `Assets/_CoinRush/Scripts/Monetization/MonetizationBootstrap.cs`

```csharp
using UnityEngine;

public class MonetizationBootstrap : MonoBehaviour
{
    public const int StarterPackCoins = 3000;
    public const string VaultKeeperId = "vault_keeper";

    [Tooltip("원격 설정을 받기 전/실패 시 쓰는 기본값 JSON (MonetizationConfig 필드)")]
    [SerializeField] private TextAsset defaultConfigJson;

    private void Awake()
    {
        DontDestroyOnLoad(gameObject);

        var config = new MonetizationConfig();
        if (defaultConfigJson != null)
            JsonUtility.FromJsonOverwrite(defaultConfigJson.text, config);
        // 원격 값(확장 트랙 7단계): Remote Config 서비스에서 받은 JSON 문자열을 같은 방식으로 덮어쓴다.

#if (UNITY_ANDROID || UNITY_IOS) && (UNITY_EDITOR || COINRUSH_FAKE_SERVICES)
        IAdService ads = gameObject.AddComponent<FakeAdService>();
        IStoreService store = gameObject.AddComponent<FakeStoreService>();
#elif UNITY_ANDROID || UNITY_IOS
        // 모바일 실제 빌드: 7단계 절차로 RealAdService/RealStoreService를 구현해 여기서 생성한다.
        IAdService ads = null;
        IStoreService store = null;
        Debug.LogError("[Monetization] 실제 광고·스토어 구현이 연결되지 않았습니다. 이 빌드의 광고·결제 수익은 0입니다.");
#else
        IAdService ads = null;       // Steam 유료판(1차 출시): 광고·IAP 없음 → 파사드가 모두 "제공 안 함"으로 동작
        IStoreService store = null;
#endif

        AdService.Install(ads, config);
        StoreService.Install(store);
        if (store != null) store.PurchasePending += OnPurchasePending;
        RunRecorder.RunStarted += OnRunStarted;

        if (!string.IsNullOrEmpty(config.experimentName))   // A/B 분석의 분모: 이 사용자가 어느 그룹에 배정됐는가
            Analytics.Track("experiment_assign", ("experiment", config.experimentName), ("group", config.experimentGroup));
    }

    private void OnDestroy() => RunRecorder.RunStarted -= OnRunStarted;

    private static void OnRunStarted(RunRecorder run) => AdService.OnRunStarted(run.RunId);

    /// <summary>상점 UI가 구독해 저장 실패 안내를 띄운다 (인자: 상품 ID)</summary>
    public static event System.Action<string> EntitlementSaveFailed;

    /// <summary>검증 → 중복 확인 → 지급·영속화 → 구매 확인. 구매·재전달·복원이 모두 여기로 온다.</summary>
    private static void OnPurchasePending(PendingPurchase purchase)
    {
        // ① 검증: 실제 구현에서는 영수증을 검증하고, 실패하면 지급도 확인도 하지 않고 기록만 남긴다.
        //    (가짜 스토어는 생략. 재화 상품은 서버 검증이 원칙 — 개념 절)

        SaveData save = SaveSystem.Load();
        bool alreadyGranted = save.grantedTransactions.Contains(purchase.TransactionId);   // ② 중복 확인
        if (!alreadyGranted)
        {
            GrantProduct(save, purchase.ProductId);                                        // ③ 지급
            save.grantedTransactions.Add(purchase.TransactionId);
        }

        if (!SaveSystem.Save(save))                                                        // ③ 영속화
        {
            // 저장 실패: 확인하지 않는다 → 스토어가 다음 실행에 다시 전달 → ②가 중복을 막는다
            Debug.LogWarning($"[Monetization] 저장 실패로 거래 {purchase.TransactionId}를 확인하지 않음");
            Analytics.Track("iap_entitlement_save_failed", ("product_id", purchase.ProductId),
                ("read_only", SaveSystem.IsReadOnly));
            EntitlementSaveFailed?.Invoke(purchase.ProductId);   // 상점 UI: "구매는 완료됐지만 저장하지 못했습니다. 앱을 다시 시작하면 지급됩니다"
            return;
        }

        StoreService.Current.ConfirmPurchase(purchase);                                    // ④ 구매 확인
        Analytics.Track("iap_entitlement", ("product_id", purchase.ProductId), ("redelivered", alreadyGranted));
    }

    private static void GrantProduct(SaveData save, string productId)
    {
        switch (productId)
        {
            case ProductIds.StarterPack:
                if (!save.unlockedCharacters.Contains(VaultKeeperId))
                    save.unlockedCharacters.Add(VaultKeeperId);    // 해금은 복원·재설치 때마다 보장
                if (!save.starterPackGranted)
                {
                    save.coins += StarterPackCoins;                // 코인은 이 세이브에서 한 번만
                    save.starterPackGranted = true;
                }
                break;
            case ProductIds.RemoveAds:
                break;   // 소유 여부의 진실의 원천은 스토어 (StoreService.HasRemoveAds). 세이브에 둘 것 없음
        }
    }
}
```

`Assets/_CoinRush/Data/monetization_default.json`을 만들고 인스펙터에 연결합니다.

```json
{ "reviveEnabled": true, "reviveMaxPerRun": 1, "doubleCoinsEnabled": true, "interstitialEnabled": false, "experimentName": "", "experimentGroup": "control" }
```

- `SaveSystem.Load()`는 캐시된 객체를 돌려주므로 저장에 실패해도 메모리에는 지급이 남아 있습니다. 그래서 `alreadyGranted`가 true여도 **확인 전에 다시 저장을 시도**합니다. 저장이 성공해야만 확인이 나갑니다.
- 재설치하면 로컬 세이브가 사라져 `starterPackGranted`도 사라집니다. 복원 시 캐릭터 해금은 다시 열리고, 이 구현에서는 코인도 새 세이브에 다시 지급됩니다. 계정당 한 번만 코인을 주려면 클라우드 세이브나 서버 기록이 필요하며, 상품 설명과 실제 동작을 일치시킵니다.

**상품 버튼**: 타이틀 씬 상점(23장 `UpgradeShop` 옆)에 둡니다. 판매 조건을 만족할 때만 보이고, 가격은 스토어 문자열을 씁니다. 파일: `Assets/_CoinRush/Scripts/UI/StoreProductButton.cs`

```csharp
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class StoreProductButton : MonoBehaviour
{
    [SerializeField] private string productId = ProductIds.StarterPack;
    [SerializeField] private string title = "스타터 팩 (코인 3,000 + 금고지기)";
    [SerializeField] private GameObject root;   // 버튼 묶음. 이 컴포넌트는 항상 활성인 부모에 붙인다
    [SerializeField] private Button button;
    [SerializeField] private TMP_Text label;

    private void Awake() => button.onClick.AddListener(OnClick);
    private void OnEnable() => Refresh();

    private void Refresh()
    {
        IStoreService store = StoreService.Current;
        bool sellable = store != null && store.IsReady && !store.Owns(productId)
                        && (productId != ProductIds.RemoveAds || StoreService.ShouldOfferRemoveAds);
        root.SetActive(sellable);
        if (!sellable) return;
        label.text = $"{title}  {store.GetLocalizedPrice(productId)}";
        button.interactable = true;
    }

    private void OnClick()
    {
        IStoreService store = StoreService.Current;
        if (store == null || !button.interactable) return;
        button.interactable = false;
        Analytics.Track("iap_click", ("product_id", productId));
        store.Purchase(productId, outcome =>
        {
            Analytics.Track("iap_purchase", ("product_id", productId), ("outcome", outcome.ToString()));
            if (this != null) Refresh();   // 성공이면 소유 → 숨김, 취소·실패·대기면 다시 누를 수 있게
        });
    }
}
```

1. 타이틀 씬 상점 패널에 빈 오브젝트 `StarterPack`(항상 활성)을 만들고 `StoreProductButton`을 붙입니다. 자식 `Root` 아래에 Button과 TMP 텍스트를 두고 Root, Button, Label을 연결합니다.
2. 같은 방식으로 `RemoveAds` 오브젝트를 만들고 Product Id를 `remove_ads`, Title을 "광고 제거 (보상형 광고는 계속 이용 가능)"로 둡니다. 기본 설정에서는 보이지 않는 것이 정상입니다.
3. 11장 설정 화면에 "구매 복원" 버튼을 두고, 스크립트에서 `StoreService.Current?.RestorePurchases(ok => { })`를 호출합니다. `StoreService.Current`는 인터페이스 타입이므로 `?.`를 써도 됩니다.
4. 23장 `UpgradeShop`이 열려 있는 동안 스타터 팩 코인이 들어오면 표시가 바로 바뀌지 않습니다. 상점 패널을 닫았다 열거나, 구매 콜백에서 상점 패널을 다시 활성화합니다.

### 6단계: 부활 창, 코인 2배, 결과 화면 연결

**부활 창**: 광고 요청 중에는 **시청·포기 버튼을 모두 잠급니다.** 포기 버튼이 살아 있으면 포기 → 결과 화면 → 늦게 도착한 광고 보상으로 결과 화면에서 플레이어만 부활하는 사고가 납니다. 콜백은 요청 번호·판 ID·현재 상태를 확인한 뒤 한 번만 처리합니다. 파일: `Assets/_CoinRush/Scripts/UI/RevivePanel.cs`

```csharp
using System;
using UnityEngine;
using UnityEngine.UI;

public class RevivePanel : MonoBehaviour
{
    [SerializeField] private GameObject panelRoot;   // 이 스크립트는 항상 활성인 부모(HUD)에 붙이고, 창은 자식으로
    [SerializeField] private PlayerStateController playerState;   // 04장
    [SerializeField] private float reviveInvulnerableSeconds = 2f;
    [SerializeField] private float adTimeoutSeconds = 60f;        // SDK가 끝내 콜백을 안 주는 경우 대비
    [SerializeField] private Button watchAdButton;
    [SerializeField] private Button giveUpButton;

    private Action onDeclined;
    private string offeredRunId;
    private int requestId;          // 요청마다 증가 → 늦게 온 이전 요청의 콜백을 구분
    private bool waitingForAd;
    private float waitStartedAt;

    private void Awake()
    {
        watchAdButton.onClick.AddListener(OnWatchAd);
        giveUpButton.onClick.AddListener(OnGiveUp);
        panelRoot.SetActive(false);
    }

    /// <summary>플레이어 사망 시 호출. 부활을 제안할 수 없으면 곧바로 onDeclined.</summary>
    public void Offer(Action onDeclined)
    {
        if (panelRoot.activeSelf || !AdService.CanOfferRevive) { onDeclined?.Invoke(); return; }
        this.onDeclined = onDeclined;
        offeredRunId = AdService.CurrentRunId;
        GameFeel.RequestPause(this);                  // 17장 소유자별 정지
        SetButtons(true);
        panelRoot.SetActive(true);
        Analytics.Track("ad_offer", ("placement", AdPlacements.Revive));
    }

    private void OnWatchAd()
    {
        if (!panelRoot.activeSelf || waitingForAd) return;
        waitingForAd = true;
        waitStartedAt = Time.unscaledTime;
        SetButtons(false);                            // 시청·포기 모두 잠금
        int myRequest = ++requestId;

        AdService.ShowRewarded(AdPlacements.Revive, rewarded =>
        {
            if (this == null || myRequest != requestId || !waitingForAd) return;   // 파괴됨·다른 요청·이미 처리됨
            waitingForAd = false;

            bool stillValid = panelRoot.activeSelf
                              && playerState.State == PlayerState.Dead
                              && AdService.CurrentRunId == offeredRunId;
            if (!stillValid) return;                  // 판·상태가 바뀐 뒤 도착한 보상은 무시

            if (!rewarded) { Decline(); return; }
            Close();
            playerState.Revive(reviveInvulnerableSeconds);   // 체력 회복 + Dead → Hurt(무적) → Idle
        });
    }

    private void Update()
    {
        if (!waitingForAd || Time.unscaledTime - waitStartedAt < adTimeoutSeconds) return;
        waitingForAd = false;
        requestId++;                                  // 이후에 오는 콜백은 무시
        Decline();
    }

    private void OnGiveUp()
    {
        if (waitingForAd) return;                     // 잠금이 풀리기 전의 입력(패드 등) 방어
        Decline();
    }

    private void Decline()
    {
        if (!panelRoot.activeSelf) return;
        Close();
        onDeclined?.Invoke();
    }

    private void Close()
    {
        panelRoot.SetActive(false);
        GameFeel.ReleasePause(this);
    }

    private void OnDisable()
    {
        if (panelRoot != null && panelRoot.activeSelf) GameFeel.ReleasePause(this);   // 씬 전환 대비
    }

    private void SetButtons(bool interactable)
    {
        watchAdButton.interactable = interactable;
        giveUpButton.interactable = interactable;
    }
}
```

**04장 `PlayerStateController` 수정**: 04장에서는 Dead 상태가 `deathDelay` 뒤 `GameOver` 채널을 발행하고, 그 채널을 받은 상태 머신이 Result로 넘어가 23장 `RunRecorder`가 정산합니다. 채널을 발행하기 **전에** 부활을 제안해야 정산이 확정되지 않습니다. 또 04장의 Dead는 나가는 전이가 없으므로 복귀 메서드를 따로 둡니다. 필드 두 개, `Awake` 한 줄, Dead 분기, 새 메서드 `Revive`를 추가합니다.

```csharp
// PlayerStateController.cs (04장) — 필드 추가
[SerializeField] private RevivePanel revivePanel;   // 25장. 비워 두면 04장처럼 바로 게임오버 (Steam판)
private Color aliveColor;

// Awake에 추가
aliveColor = sprite.color;

// Update의 Dead 분기 — gameOver.Raise(); 한 줄 교체
if (revivePanel != null) revivePanel.Offer(onDeclined: gameOver.Raise);
else gameOver.Raise();

// 새 메서드 — 광고 보상 콜백에서 호출
public void Revive(float invulnerableSeconds)
{
    if (State != PlayerState.Dead) return;

    health.SetMax(health.Max, refill: true);   // 10장 메서드. Changed가 오지만 Dead라 Hurt 전이는 막힘
    lastHp = health.Current;
    sprite.color = aliveColor;
    for (int i = 0; i < disableOnDeath.Length; i++) disableOnDeath[i].enabled = true;
    mover.CanMove = true;
    gameOverRaised = false;

    // ChangeState는 Dead에서 나가지 못하게 막으므로 직접 Hurt로 진입: 04장 Hurt의 무적·깜빡임 재사용
    State = PlayerState.Hurt;
    stateTimer = hurtDuration - invulnerableSeconds;   // Hurt 종료(stateTimer >= hurtDuration)까지 invulnerableSeconds
    health.Invulnerable = true;
}
```

부활 창이 떠 있는 동안은 게임이 멈춰 적도 멈춰 있습니다. 부활하면 체력이 차고 이동·무기(`disableOnDeath` 목록)가 다시 켜지며, 2초 동안 깜빡이는 무적 뒤 Idle로 돌아가 정상적으로 피해를 받습니다. 부활은 `GameStateMachine.StartGame`을 거치지 않으므로 23장 `RunRecorder`의 판은 이어지고, `run_start`도 다시 찍히지 않습니다(24장).

**코인 2배 버튼**: 결과 화면이 열릴 때 23장 `RunRecorder`의 정산 결과를 받습니다. 보상은 세이브에 바로 더하므로, 광고를 보는 사이 재시작으로 Game 씬이 내려가도 보상이 사라지지 않습니다. 파일: `Assets/_CoinRush/Scripts/UI/DoubleCoinsButton.cs`

```csharp
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class DoubleCoinsButton : MonoBehaviour
{
    [SerializeField] private GameObject root;   // 버튼 묶음 (이 컴포넌트는 항상 활성인 부모에)
    [SerializeField] private Button button;
    [SerializeField] private TextMeshProUGUI label;

    private int bonus;

    private void Awake()
    {
        button.onClick.AddListener(OnClick);
        root.SetActive(false);
    }

    /// <summary>ResultState.Enter에서 정산이 끝난 뒤 호출</summary>
    public void Setup(RunRecorder finishedRun)
    {
        bonus = finishedRun != null ? finishedRun.Banked : 0;   // 2배 = 이월분만큼 한 번 더
        bool canOffer = bonus > 0 && AdService.CanOfferDoubleCoins;
        root.SetActive(canOffer);                                 // 광고가 준비 안 됐으면 조용히 숨김
        if (!canOffer) return;
        label.text = $"광고 보고 이월 코인 {bonus:N0} → {bonus * 2:N0}";
        button.interactable = true;
    }

    private void OnClick()
    {
        if (!button.interactable) return;
        button.interactable = false;
        int amount = bonus;                                       // 콜백 시점이 아니라 누른 시점의 값
        AdService.ShowRewarded(AdPlacements.DoubleCoins, rewarded =>
        {
            if (rewarded)
            {
                SaveData save = SaveSystem.Load();
                save.coins += amount;
                SaveSystem.Save(save);                            // 재화 변화는 즉시 저장 (10장)
            }
            if (this == null) return;                             // 광고 중 씬이 바뀐 경우: 지급만 하고 끝
            if (rewarded) label.text = "코인 2배 획득!";
            else button.interactable = AdService.CanOfferDoubleCoins;
        });
    }
}
```

**결과 화면 연결**: 04장 `GameStateMachine`에 필드와 프로퍼티를 추가하고, 11·23장 `ResultState.Enter`의 결과 표시 다음 줄에 호출을 추가합니다.

```csharp
// GameStateMachine.cs (04장) — 필드·프로퍼티 추가
[SerializeField] private DoubleCoinsButton doubleCoinsButton;   // Steam판은 비워 둠
public DoubleCoinsButton DoubleCoinsButton => doubleCoinsButton;

// ResultState.Enter (11·23장) — machine.ResultView.Show(...) 다음 줄에 추가
if (machine.DoubleCoinsButton != null) machine.DoubleCoinsButton.Setup(machine.RunRecorder);
```

"타이틀로" 버튼에 전면 광고 규칙을 겁니다. 11장 `ResultView`는 09장 채널로 씬을 바꾸므로, 상태 머신을 직접 바꾸지 않고 채널 발행 앞에 광고 판단만 끼웁니다. 재시작도 11장 그대로 09장 `RetryRequested` 채널이 Game 씬을 새로 로드하므로, 새 판은 새 `RunRecorder`·스포너·플레이어로 깨끗하게 시작됩니다.

```csharp
// ResultView.cs (11장) — OnTitle 교체
private void OnTitle()
{
    if (!Consume()) return;
    // 기본 설정(interstitialEnabled: false)에서는 광고 없이 즉시 전환
    AdService.TryShowInterstitial(AdPlacements.ResultToTitle, () => returnToTitleRequested.Raise());
}
```

에디터 연결:

1. HUD Canvas 아래 항상 활성인 `ReviveHost`에 `RevivePanel`을 붙이고, 자식 `RevivePanelRoot`(비활성)에 "광고 보고 부활"·"포기" 버튼을 둡니다. Player의 `PlayerStateController` **Revive Panel**에 `ReviveHost`를 연결합니다.
2. 11장 결과 화면 아래 항상 활성인 `DoubleCoinsHost`에 `DoubleCoinsButton`을 붙이고 자식 `Root`에 버튼·텍스트를 둡니다. `GameStateMachine` **Double Coins Button**에 연결합니다.
3. Bootstrap 씬의 `Managers` 아래 `Monetization` 오브젝트에 `MonetizationBootstrap`을 붙이고 **Default Config Json**을 연결합니다.

### 7단계: A/B 실험 계획서와 실제 SDK 연결 절차

`Docs/experiment-revive-2.md` 예시입니다.

```
실험명     revive_max_2
가설       부활을 1판 2회로 늘리면 사용자당 보상형 노출이 늘고, D1 리텐션은 떨어지지 않는다
그룹       control: reviveMaxPerRun=1 / variant: reviveMaxPerRun=2
           (Remote Config, 사용자 고정 배정 50:50, experimentName=revive_max_2)
배정 기록   experiment_assign {experiment, group} — 분석 분모는 이 이벤트가 있는 신규 사용자
주 지표     사용자당 일 보상형 노출 수 = ad_impression(format=rewarded) 수 ÷ 그룹 사용자 수
           (ad_rewarded_end의 result=Rewarded는 "끝까지 본 수"라 중도 종료 노출이 빠지므로 쓰지 않음)
보호 지표   D1 리텐션 (허용 하락 2%p 이내), 판당 평균 플레이 시간
표본       보호 기준 2%p에 맞춤: D1 30% 기준 → 그룹당 약 8,400명의 신규 사용자
           (3%p 기준 3,700명으로는 2%p 하락을 판단할 수 없음)
기간       일 신규 500명이면 두 그룹 합계 16,800명 → 약 34일. 기간 전 중단 금지 (보호 지표 급락 시 안전 중단만 허용)
결정 규칙   주 지표 개선 + 보호 지표 허용 범위 → variant 채택 / 보호 지표 이탈 → 중단
```

일 신규 500명도 모바일 인디 게임에는 큰 숫자입니다. 개념 절의 손익 사례처럼 유료 확보를 하지 않는다면 이 실험은 몇 달이 걸리므로, 실험 대신 원칙대로 1회로 두고 전후 비교로 모니터링하는 판단이 합리적일 수 있습니다.

**실제 SDK 연결 절차** — 모바일 확장 트랙을 Go로 결정한 뒤 수행합니다. 이 절차를 끝내기 전까지는 수익이 발생하지 않습니다.

```
[버전 고정]
□ 미디에이션 1개, Unity IAP, (선택) Remote Config 패키지를 고르고 Packages/manifest.json에
  정확한 버전 숫자로 고정해 Git 커밋. 사용한 버전의 공식 문서 URL을 Docs/monetization.md에 기록
□ SDK 업그레이드는 별도 브랜치에서 이 체크리스트 전체를 다시 수행한 뒤에만 병합

[구현 대응표 — 게임 코드는 바꾸지 않고 구현 클래스 두 개만 추가]
□ RealAdService : IAdService
    보상형 로드 완료        → IsRewardedReady
    광고 표시 콜백          → onShown
    보상 획득 콜백          → 결과를 Rewarded로 기억, 닫힘 콜백에서 onComplete(Rewarded) 한 번
    보상 없이 닫힘 / 표시 실패 → onComplete(Skipped / Failed)
    SDK 콜백이 메인 스레드가 아닐 수 있으면 메인 스레드로 옮긴 뒤 호출
    로드 실패 시 재시도 간격을 점점 늘리기 (즉시 무한 재요청 금지)
□ RealStoreService : IStoreService  (Unity IAP 5.x 기준, 설치 버전 문서로 이름 확인)
    OnPurchasePending(대기 주문)   → PurchasePending(거래 ID, 상품 ID) — 대기 주문 객체는 ID로 보관
    ConfirmPurchase(PendingPurchase) → 보관한 대기 주문으로 스토어의 ConfirmPurchase 호출
    OnPurchaseDeferred             → Purchase 콜백에 PurchaseOutcome.Pending
    OnPurchaseFailed(취소/실패)     → Cancelled / Failed
    복원(기존 구매 조회)            → 소유 상품마다 PurchasePending (5단계 ②가 중복을 막음)
□ 동의: UMP Update → LoadAndShowConsentFormIfRequired → CanRequestAds()가 true일 때만 광고 SDK 초기화
        iOS는 ATT 요청 순서를 미디에이션 문서대로. 설정 화면에 개인정보 옵션 진입점
□ Remote Config: 받은 JSON을 JsonUtility.FromJsonOverwrite로 덮어쓰고 실패 시 기본값 유지.
  experimentName/experimentGroup은 서비스가 사용자 고정 배정한 값을 그대로 사용
□ 부트스트랩의 #elif UNITY_ANDROID || UNITY_IOS 분기에서 두 구현을 생성

[빌드]
□ 실기기 개발 빌드는 COINRUSH_FAKE_SERVICES 정의 없이 → 실제 구현 경로
□ 테스트 광고 단위·테스트 기기 등록. 개발 중 실제 광고 클릭 금지 (계정 정지 위험)
□ 스토어 콘솔에 상품 등록, 라이선스 테스터(Google)·샌드박스 계정(Apple) 준비
□ Steam 빌드 로그에 모바일 SDK 어셈블리가 포함되지 않았는지 확인

[실기기 테스트 — Android 1대 + iOS 1대 이상]
□ 보상형: 끝까지 시청 / 중간 닫기 / no fill(비행기 모드) → 보상은 끝까지 본 경우에만 1회
□ 부활 광고 표시 중 홈 버튼으로 나갔다 복귀 → 중복 부활·결과 화면 부활 없음
□ 코인 2배 광고 중 "재시작" → 광고 완료 후 코인은 1회만 증가
□ 구매 성공 / 취소 / 결제 대기(승인 후 다음 실행에 지급) / 구매 직후 앱 강제 종료 → 재실행 시 1회만 지급
□ 앱 삭제·재설치 → 복원 버튼으로 캐릭터 해금·광고 제거 복원, 코인 동작이 상품 설명과 일치
□ 스토어 콘솔 주문 내역에서 구매가 "확인(acknowledged)" 상태인지 확인 — 미확인은 자동 환불될 수 있음
□ 동의 거부 시나리오별로 CanRequestAds() 결과와 실제 광고 요청 여부가 일치
□ 스토어 개인정보 양식(App Privacy / 데이터 보안)에 광고·분석·IAP SDK 수집 항목 반영 (28장)
```

### 확인하기

Build Profiles에서 **Android** 플랫폼으로 전환한 뒤 에디터에서 확인합니다.

1. Play → 판 도중 죽으면 게임이 멈추고 부활 창이 뜬다. **광고 보고 부활**을 누르면 **포기 버튼도 함께 비활성**이 되고 가짜 광고 창이 뜬다. **끝까지 시청** → 체력이 가득 찬 채 게임이 재개된다.
2. 같은 판에서 레벨업을 몇 번 한 뒤 다시 죽으면 부활 창 없이 결과 화면으로 간다(레벨업 복귀로 한도가 초기화되지 않음). 새 판에서 첫 부활 때 **중간에 닫기**를 고르면 보상 없이 결과 화면으로 간다.
3. 결과 화면의 "광고 보고 이월 코인 N → 2N" 버튼으로 시청하면 타이틀 상점의 코인이 N만큼 더 늘어 있다. 광고 창이 떠 있는 동안 **재시작**을 눌러도 광고를 끝까지 보면 코인이 한 번만 늘어난다.
4. 타이틀 상점에 스타터 팩 버튼이 보이고 광고 제거 버튼은 **보이지 않는다**(`interstitialEnabled: false`). JSON에서 `interstitialEnabled`를 true로 바꾸면 광고 제거 버튼이 나타난다.
5. 스타터 팩 → 가짜 결제 **구매** → Console에 `iap_entitlement`(redelivered false), 코인 +3,000. 다시 Play해도 코인이 또 늘지 않는다.
6. **재전달**: Play 중 `FakeStoreService` 컨텍스트 메뉴 **가짜 구매 기록 모두 삭제**를 실행하고 Play를 멈춘 뒤 10장 세이브 파일(`save.json`과 백업)을 지워 새 세이브로 시작합니다. 그다음 스타터 팩 → **"구매 — 지급 전에 앱 종료 흉내"** → 코인이 늘지 않은 상태에서 Play 중지 → 다시 Play하면 시작 직후 코인 +3,000과 `iap_entitlement`가 한 번 찍힌다. 한 번 더 Play해도 다시 지급되지 않는다.
7. 설정의 **구매 복원** → `iap_entitlement`(redelivered true)가 찍히지만 코인은 늘지 않는다.
8. Build Profiles를 Windows로 바꾸고 Play하면 부활 창·코인 2배·상품 버튼이 모두 나타나지 않는다(Steam판).

## 흔한 실수

1. **증상**: 가끔 광고를 끝까지 봤는데 보상이 두 번 들어온다. 또는 안 들어온다. → **원인**: "광고 닫힘" 콜백과 "보상 획득" 콜백을 모두 보상 지급에 연결했거나, 닫힘에서만 지급. → **해결**: 보상은 SDK의 보상 획득 신호로만 결정하고, 파사드에서 한 번만 콜백합니다. 가짜 구현에서 Skipped/Failed 경로를 반드시 테스트합니다.
2. **증상**: 부활 광고를 본 뒤 결과 화면에서 캐릭터만 되살아나 움직인다. → **원인**: 광고 요청 중 포기 버튼이 살아 있어 결과로 넘어간 뒤 늦은 보상 콜백이 도착. → **해결**: 요청 중에는 모든 종료 입력을 잠그고, 콜백에서 요청 번호·판 ID·Dead 상태를 확인한 뒤 한 번만 처리합니다.
3. **증상**: 한 판에서 부활을 여러 번 할 수 있다. → **원인**: 부활 한도를 "Playing 상태 진입"에서 초기화해 레벨업 복귀 때마다 0이 됨. → **해결**: 판 시작(`RunRecorder.RunStarted`)에서만 초기화하고, `ShowRewarded` 안에서도 한도를 검사합니다.
4. **증상**: 광고 제거를 산 사용자들이 "사도 달라진 게 없다"며 환불을 요청한다. → **원인**: 전면 광고가 꺼진 구성에서 광고 제거를 판매. → **해결**: 제거할 광고가 있는 사용자(`interstitialEnabled`)에게만 노출하고, 실험 그룹별로 상품 효용을 확인합니다. 반대로 보상형까지 없애면 "손해"라는 리뷰가 나오므로 보상형은 유지합니다.
5. **증상**: 스타터 팩 결제는 됐는데 코인이 없다는 문의가 가끔 온다. → **원인**: 스토어에 구매 확인을 먼저 보내고 저장했는데, 저장 전에 앱이 종료되거나 저장이 실패함. → **해결**: 검증 → 중복 확인 → 지급·저장 성공 → 구매 확인 순서를 지키고, 저장 실패 시 확인하지 않아 재전달되게 합니다.
6. **증상**: 스타터 팩 코인이 재실행할 때마다 들어온다. → **원인**: 재전달·복원 때마다 `PurchasePending`이 오는데 거래 ID·지급 플래그 확인이 없음. → **해결**: 처리한 거래 ID와 `starterPackGranted`를 세이브에 기록하고 확인한 뒤 지급합니다.
7. **증상**: A/B 테스트 3일째 variant가 좋아 보여서 채택했는데 출시 후 지표가 떨어졌다. → **원인**: 표본 부족과 중간 확인 후 조기 중단(우연한 차이를 결과로 착각), 또는 보호 기준보다 큰 차이만 감지하는 표본. → **해결**: 가장 작은 판단 기준(보호 지표 허용폭)에 맞춘 표본 크기·기간·결정 규칙을 실험 전에 문서로 확정하고, 기간 전에는 결론 내지 않습니다.

## 연습 문제

**1. ★☆☆ 지표 계산**
하루 동안 보상형 광고 요청 8,000회, 채워진 요청 7,200회, 노출 7,000회, 광고 수익 $56, DAU 4,000명입니다. fill rate, eCPM, ARPDAU(광고)를 구하세요.

<details><summary>힌트·해설</summary>

fill rate = 7,200 ÷ 8,000 = 90%. eCPM = 56 ÷ 7,000 × 1,000 = $8. ARPDAU = 56 ÷ 4,000 = $0.014. 채워진 요청(7,200)과 노출(7,000)의 차이 200은 광고가 로드됐지만 표시되지 않은 경우입니다(사용자가 버튼을 누르기 전에 떠남, 만료 등). 이 차이가 크면 광고를 너무 일찍 미리 로드하고 있거나 버튼 노출 위치가 나쁜 것일 수 있습니다.

</details>

**2. ★★☆ 코인 2배 광고와 메타 경제**
23장 캠페인에서 "세 강화 모두 10레벨"이 46판이었습니다. 사용자의 절반이 매 판 코인 2배 광고를 본다면 이 사용자들의 도달 판 수는 대략 어떻게 되며, 이것이 문제라면 어떤 조정이 가능한지 두 가지 제안하세요.

<details><summary>힌트·해설</summary>

이월 코인이 2배가 되면 판 수는 절반 가까이(20판대)로 줄어듭니다(강화가 쌓여 획득이 늘어나는 효과가 겹쳐 정확히 절반은 아님 — `SimulateCampaign`의 `bank += r.coinsBanked`를 `2 * r.coinsBanked`로 바꿔 확인). 조정 후보: (a) 2배 대신 +50%로 줄이기, (b) 코인 2배를 하루 N회로 제한(Remote Config), (c) 광고 시청자가 빨리 도달해도 문제없도록 강화 이후 Sink(캐릭터 해금, 23장 연습 4)를 준비. 어느 쪽이든 광고 보상을 경제 표와 시뮬레이터에 포함시키는 것이 핵심입니다. 모바일판에만 광고가 있으므로, Steam판과 모바일판의 메타 진행 속도가 달라진다는 점도 스토어 설명과 업데이트 계획에 반영합니다.

</details>

**3. ★★☆ 소프트 론칭 손익 판단**
소프트 론칭 결과가 CPI $0.90, D1 32%, D7 9%, 코호트 1인당 누적 순수익 D7 $0.10, D30 $0.28입니다. 개념 절의 확장·중단 기준으로 무엇을 결정해야 하나요? D90을 D30의 1.5배로 추정하고, 월 운영 시간 비용 $860, 도구 $60, 자연 유입 월 2,000명일 때 자연 유입만의 코호트 월 손익도 계산하세요.

<details><summary>힌트·해설</summary>

D7 9%로 "유료 확보 시작 조건(D7 ≥ 10%)"을 통과하지 못하므로 광고비 확대 여부를 따지기 전에 **유료 확보를 시작하지 않습니다.** 참고로 D30 ROAS = 0.28 ÷ 0.90 ≈ 31%, D90 추정 = 0.42 ÷ 0.90 ≈ 47%로 중단 기준(70% 미만)에도 걸립니다. 자연 유입만: 2,000 × 0.42 = $840 − 860 − 60 = **−$80**/월. 운영 시간 가치를 조금 밑돌므로 3개월 추세를 보고 유지보수 모드 전환을 검토합니다. 먼저 손댈 곳은 D1→D7 사이의 이탈(메타 루프, 24장 퍼널)이며, 광고 배치 변경보다 리텐션 개선이 손익에 더 크게 작용합니다. 실제 판단에는 세금·환율·정산 지연을 넣은 29장 현금흐름표를 함께 봅니다.

</details>

**4. ★★★ 오퍼 설계와 검증**
세 번째 판이 끝났고 아직 아무것도 구매하지 않은 사용자에게 "스타터 팩"을 한 번 제안하는 기능을 설계·구현하세요. 조건: Remote Config로 켜고 끄기, 24장 이벤트로 제안·구매 전환을 측정, 다크 패턴 금지(가짜 타이머, 닫기 버튼 숨김 없음), 구매는 5단계 처리 순서를 그대로 사용. 전환율 1%의 기준에서 0.5%p 개선을 A/B로 검증하려면 그룹당 몇 명이 필요한지 계산하고, 여러분의 예상 신규 유입으로 가능한지 판단하세요.

<details><summary>힌트·해설</summary>

구현: `MonetizationConfig`에 `starterOfferEnabled`, `starterOfferAfterRuns`를 추가하고, `SaveData`에 `starterOfferShown`을 추가합니다(10장 규칙대로 버전 증가). 결과 화면에서 `save.stats.totalRuns == starterOfferAfterRuns && !StoreService.Current.Owns(ProductIds.StarterPack) && !save.starterOfferShown`일 때 패널을 띄우고 즉시 `starterOfferShown = true`를 저장합니다. 구매 버튼은 `StoreProductButton`을 재사용하면 지급은 `PurchasePending` 한 곳에서 처리됩니다. 이벤트는 `offer_show {offer_id}`, `iap_click`, `iap_purchase {product_id, outcome}`, `iap_entitlement`. 표본: 16 × 0.01 × 0.99 ÷ 0.005² ≈ 6,300명/그룹. 오퍼를 보는 사람은 3판 이상 한 사용자뿐이므로 필요한 신규 설치는 그보다 훨씬 많습니다(3판 도달률이 50%면 약 2배). 일 신규 수백 명 규모라면 수 주~수개월이 걸리므로, 실험 대신 원칙에 맞게 설계하고 전후 비교로 모니터링하는 판단도 합리적입니다.

</details>

## 셀프 체크

**1. 광고·IAP SDK를 인터페이스 뒤에 숨기고 가짜 구현을 만드는 이유를 세 가지 설명하고, 이 방식의 한계도 말해보세요.**

<details><summary>모범 답안</summary>

첫째, 광고 SDK는 실기기에서만 동작하는 경우가 많아 에디터에서 부활·보상·실패·재전달 흐름을 테스트하려면 가짜 구현이 필요합니다. 둘째, Steam 유료판처럼 광고가 없는 플랫폼에서는 구현을 연결하지 않는 것만으로 게임 코드 수정 없이 기능이 사라집니다. 셋째, 미디에이션이나 Unity IAP 버전이 바뀌어도 수정 범위가 구현 클래스 하나로 한정되고, 빈도 제한·상품 노출 규칙·애널리틱스를 파사드 한 곳에서 강제할 수 있습니다. 한계는 가짜 구현이 실제 SDK의 타이밍·스레드·스토어 정책을 완전히 흉내 내지 못한다는 점과, 실제 구현을 연결하고 실기기 테스트를 통과하기 전까지는 수익이 0이라는 점입니다.

</details>

**2. 보상형 광고 요청 중에 왜 포기 버튼까지 잠그고, 콜백에서 무엇을 확인하나요?**

<details><summary>모범 답안</summary>

광고 SDK의 콜백은 광고가 닫힌 뒤 늦게 도착합니다. 포기 버튼이 살아 있으면 플레이어가 포기해 결과 화면·정산으로 넘어간 뒤 보상 콜백이 도착해, 이미 끝난 판에서 플레이어만 부활할 수 있습니다. 그래서 요청 중에는 모든 종료 입력을 잠그고, 콜백에서는 요청 번호가 최신인지, 이미 처리했는지, 창이 아직 열려 있고 플레이어가 Dead인지, 같은 판(`run_id`)인지를 확인한 뒤 한 번만 처리합니다. SDK가 콜백을 끝내 주지 않는 경우를 위해 제한 시간도 둡니다.

</details>

**3. "광고 제거" 상품을 언제 팔고 언제 팔지 말아야 하며, 구매자에게도 보상형 광고를 유지하는 근거는?**

<details><summary>모범 답안</summary>

광고 제거는 제거할 광고(전면 광고)가 실제로 보이는 사용자에게만 팝니다. 기본 설정처럼 전면 광고가 꺼져 있으면 사도 경험이 바뀌지 않으므로 팔면 안 되고, 원격 실험 그룹마다 전면 광고 여부가 다르면 그룹별로 노출 조건을 맞춰야 합니다. 보상형 광고는 플레이어가 원할 때만 보고 부활이나 코인 같은 이득을 얻는 선택지이므로, 광고 제거 구매자에게서 없애면 돈을 내고 기능을 잃는 셈이 됩니다. 그래서 전면 광고에만 적용하고 상품 설명에 명시합니다.

</details>

**4. 구매 보상을 구매 버튼 콜백이 아니라 `PurchasePending` 한 곳에서 처리하는 이유와, 그 안의 순서를 설명해보세요.**

<details><summary>모범 답안</summary>

구매는 결제 앱으로 전환되는 동안 게임이 종료되어 다음 실행 때 전달되거나, 복원으로 다시 전달될 수 있어 버튼 콜백에서 지급하면 누락이 생깁니다. 모든 경로가 거치는 한 곳에서 처리하되, 순서는 검증 → 거래 ID로 중복 확인 → 지급과 저장 성공 확인 → 스토어에 구매 확인입니다. 저장 전에 확인하면 저장 실패 시 돈만 나가고 보상이 없고, 확인을 보내지 않으면 스토어가 계속 재전달하거나 자동 환불할 수 있습니다. 저장이 실패하면 확인하지 않고 끝내 재전달을 받고, 중복 확인이 두 번째 지급을 막습니다.

</details>

**5. 광고 수익 계산(DAU × 노출 × eCPM)만으로 모바일판 출시를 결정하면 안 되는 이유는?**

<details><summary>모범 답안</summary>

그 계산은 DAU를 주어진 값으로 가정하지만, 실제로는 사용자를 확보하는 비용(CPI)과 유지하는 비용(운영·업데이트 시간)이 듭니다. 코호트 누적 순수익이 회수 기간 안에 CPI를 넘지 못하면 광고비를 쓸수록 손해이고, 자연 유입만으로는 DAU가 계산의 가정만큼 나오지 않을 수 있습니다. 그래서 소프트 론칭으로 리텐션·CPI·기간별 ROAS를 실측하고, 운영비와 개발자 시간을 포함한 월 손익과 사전에 정한 확장·중단 기준으로 판단합니다.

</details>

## 핵심 요약

- 코인 러시의 1차 출시는 Steam 유료(광고·IAP 없음)이고, 모바일 무료판은 판매 반응과 손익 실측으로 Go/No-Go를 정하는 확장 트랙입니다. 이 장은 가짜 서비스까지이며, 실제 SDK 연결 절차를 마치기 전에는 수익이 0입니다.
- 보상형 광고는 선택형, 명확한 가치 교환, 자연스러운 멈춤 지점, 파사드가 강제하는 빈도 제한, 조용한 실패 처리가 원칙이며, 광고·상품 보상은 메타 경제 계산에 포함합니다.
- 상품은 실제 효용이 있을 때만 팝니다. 광고 제거는 전면 광고가 보이는 사용자에게만 노출하고, 구매자에게도 보상형은 유지합니다.
- eCPM·ARPDAU 계산에 CPI·기간별 ROAS·운영비·개발자 시간을 더한 월 손익표와 사전 확장·중단 기준으로 사업을 판단합니다.
- GDPR 지역에서는 TCF 목적별 동의에 따라 맞춤·비맞춤·제한적 광고가 갈리며, `CanRequestAds()`로 요청 가능 여부를 확인한 뒤에만 광고를 요청합니다.
- 구매는 `PurchasePending` 한 곳에서 검증 → 거래 ID 중복 확인 → 지급·영속화 → 구매 확인 순서로 처리하고, 저장 실패 시 확인하지 않아 재전달을 받습니다.
- 부활 광고 요청 중에는 모든 종료 입력을 잠그고, 콜백은 요청 번호·판 ID·상태를 확인해 한 번만 처리합니다. 판 단위 한도는 판 시작에서만 초기화합니다.
- A/B 테스트는 배정·노출 이벤트를 기록하고, 가장 작은 판단 기준(보호 지표 허용폭)에 맞춘 표본으로 설계합니다. 한국에서 확률형 아이템을 넣는다면 매체별(게임 내·홈페이지·광고물) 표시 의무를 지킵니다.

## 더 읽을거리

- Unity IAP — 구매 처리(Processing purchases, 설치 버전 문서 확인): https://docs.unity.com/en-us/iap/purchases
- Google AdMob (Unity) — 개인정보 보호·UMP 연동: https://developers.google.com/admob/unity/privacy
- Google AdMob (Unity) — 광고 게재 방식(맞춤·비맞춤·제한적): https://developers.google.com/admob/unity/privacy/ad-serving-modes
- Apple Developer — App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- 국가법령정보센터 — 게임산업진흥에 관한 법률 시행령 별표 3의2 (확률형 아이템 공급 확률정보 등의 표시내용 및 표시방법)
