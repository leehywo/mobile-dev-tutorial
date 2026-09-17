# 37. 실제 광고·결제 연결 — AdMob·Unity IAP·Remote Config (모바일 확장 트랙)

> **이 장에서 배울 것**
> - 25장의 `IAdService`·`IStoreService` 가짜 구현을 Google Mobile Ads(AdMob)와 Unity IAP 5.x 실제 구현으로 교체한다
> - Unity IAP 5의 주문 수명주기(Pending → Confirmed / Failed / Deferred)를 설명하고, 앱 종료·재설치·환불·중복 콜백에도 한 번만 지급되는 구조를 구현한다
> - UMP 동의 → (iOS) ATT → 광고 SDK 초기화 순서를 구현하고, 테스트 광고 단위·라이선스 테스터·Sandbox 계정으로 실기기 검증을 한다
> - 광고 제거 상품이 실제 효용을 갖도록 25장 설계를 고치고, Remote Config를 실제로 받아와 킬 스위치로 쓴다
> - CPI·LTV·회수 기간으로 소프트 론칭 예산과 중단 기준을 문서로 정한다
>
> **선수 장**: 09, 10, 24, 25 · **예상 시간**: 8~10시간 (+ 스토어 계정·검토 대기 수일) · **권장 시점**: 25장을 마친 뒤. 단, Steam 유료판이 1차 출시이므로 **Steam판을 낸 뒤 모바일 확장을 결정했을 때** 수행 · **코인 러시 진행**: 실기기에서 테스트 광고를 끝까지 보면 부활하고, 라이선스 테스터 계정으로 "광고 제거 패스"를 사면 전면 광고가 사라지고 보상형은 시청 없이 지급되는 Android 빌드 + 검증 체크리스트 + 소프트 론칭 계획서

## 왜 필요한가

25장의 `MonetizationBootstrap`을 모바일 릴리스로 빌드하면 이 줄이 실행됩니다.

```csharp
#elif UNITY_ANDROID || UNITY_IOS
        IAdService ads = null;
        IStoreService store = null;
        Debug.LogError("실제 광고·스토어 구현이 연결되지 않았습니다.");
```

파사드가 모든 기능을 "제공 안 함"으로 처리하므로 게임은 멀쩡히 돌아갑니다. **그리고 수익은 0원입니다.** 가짜 구현은 흐름을 설계하는 도구였고, 돈이 들어오려면 다음을 실제로 풀어야 합니다.

1. **광고 제거 상품에 팔 것이 없습니다.** 25장은 전면 광고를 기본으로 꺼 두고(`interstitialEnabled = false`) "전면 광고 제거"를 팝니다. 효용 없는 상품은 환불 요청과 부정 리뷰로 돌아옵니다.
2. **결제에는 에디터에서 재현되지 않는 경로가 많습니다.** 결제 직후 앱 종료, 보호자 승인 대기, 재설치, 스토어 환불. 가짜 스토어의 "구매" 버튼은 어느 것도 흉내 내지 않았습니다.
3. **개발 중 실제 광고를 누르면 계정이 위험합니다.** AdMob은 테스트 모드가 아닌 상태에서 광고를 많이 누르면 무효 활동으로 계정이 표시될 수 있다고 경고합니다.
4. **원격 설정은 주석뿐입니다.** 광고가 리텐션을 망치는 것을 발견해도 앱 업데이트 심사를 기다려야 합니다.
5. **벌 수 있는 돈의 상한을 모릅니다.** 사용자 한 명이 벌어 주는 돈(LTV)과 데려오는 비용(CPI)을 모르면 소프트 론칭에 얼마를 쓰고 언제 멈출지 정할 수 없습니다.

## 개념

### 준비물과 대기 시간

코드보다 계정을 먼저 엽니다. 검토 대기가 개발보다 길 수 있습니다.

| 준비물 | 왜 필요한가 | 주의 |
|---|---|---|
| Google Play Console 개발자 계정 + 결제 프로필 | 앱 등록, 인앱 상품, 테스트 트랙, 판매 | 신규 **개인** 계정은 프로덕션 전 비공개 테스트 요건([38장](./38_release-qa.md)). 사업자·정산 계좌는 [28장](./28_business-law-tax-kr.md) |
| AdMob 계정·앱 등록 | 앱 ID, 광고 단위 ID | 신규 앱은 **앱 준비 검토**가 끝날 때까지 게재가 제한될 수 있음(보통 2~3일, 스토어에 게시된 앱만 검토) |
| Unity Cloud 프로젝트 연결 | Remote Config, Authentication | 환경(development/production) 구분 |
| (iOS) Apple Developer Program | TestFlight, Sandbox | 이 장 실습은 Android 기준, iOS는 차이점만 |

AdMob 앱 준비 검토는 스토어에 게시된 앱을 요구하므로 순서는 **테스트 광고로 개발 → 테스트 트랙으로 결제 검증 → 스토어 게시 → 실제 광고 게재**입니다. 출시 첫날 실제 광고가 적게 나와도 코드 문제로 단정하지 않습니다. app-ads.txt 요구 여부는 AdMob 도움말에서 확인합니다(개발자 웹사이트 필요, [27장](./27_marketing.md) 프레스킷 사이트 재사용).

### SDK 선택: AdMob 하나로 시작

25장은 LevelPlay, AdMob, AppLovin MAX를 후보로 들었습니다. 코인 러시는 **Google Mobile Ads Unity 플러그인(AdMob)** 하나로 시작합니다. 동의 도구(UMP)가 플러그인에 포함되어 있고, 공식 테스트 광고 단위 ID가 공개되어 있으며, 연동할 것이 플러그인 하나뿐입니다. 미디에이션은 여러 네트워크 입찰로 단가를 올리지만, 첫 모바일 버전의 병목은 단가가 아니라 **DAU와 리텐션**입니다(25장 계산). 미디에이션은 DAU가 생긴 뒤 `IAdService` 구현 하나를 바꾸는 일로 미룹니다.

이 장이 기준으로 삼은 버전입니다. **설치 시점 최신 버전과 그 버전의 문서를 확인하세요.**

| 패키지 | 작성 시점(2026-09) | 설치 |
|---|---|---|
| In-App Purchasing `com.unity.purchasing` | 5.3.1 (5.x API) | Package Manager > Unity Registry |
| Google Mobile Ads Unity Plugin | v11.5.0 | GitHub 릴리스 `.unitypackage` 또는 OpenUPM `com.google.ads.mobile` |
| Remote Config `com.unity.remote-config` | 4.2.x | Package Manager (Core·Authentication 의존성 포함) |

### 광고 제거 상품 다시 설계하기

상품은 **구매자가 무엇을 얻는지 한 문장으로 말할 수 없으면 팔지 않습니다.**

| 안 | 내용 | 구매자 효용 | 위험 |
|---|---|---|---|
| A. 25장 그대로 | 전면 광고 제거(전면 광고는 기본 꺼짐) | **없음** | 환불·리뷰 |
| B. 전면 광고를 켜고 제거 | 결과→타이틀 전면 광고 기본 켬, 구매 시 제거 | 있음 | 비구매자 리텐션 |
| C. **광고 제거 패스** | B + 부활·코인 2배를 **광고 시청 없이 즉시** 지급(횟수 제한 동일) | 확실함 | 경제 |

코인 러시는 **C**를 택합니다. 코인 2배는 이미 1판 1회 제한이라, 패스 구매자는 "광고를 매번 보는 비구매자"와 같은 속도로 성장합니다. 23장 시뮬레이터의 그 시나리오가 곧 패스 구매자 시나리오이므로 새로운 경제 위험이 아닙니다. 25장 흔한 실수 2("보상형까지 없애면 손해")의 정신도 지킵니다. 이득은 그대로 두고 광고만 없앱니다. 전면 광고에는 안전장치를 겹칩니다.

```
전면 광고(result_to_title) 표시 조건 — 모두 참
  interstitialEnabled                     원격 킬 스위치 (기본값 false → true로 변경)
  누적 판 수 >= interstitialMinTotalRuns  신규, 기본 5 → 첫 세션은 사실상 광고 없음
  세션 내 interstitialEveryNRuns(3)판마다, interstitialMinSeconds(180초) 간격
  광고 제거 패스 미보유
```

그리고 **효용이 사라지면 상품을 숨깁니다.** 원격 설정으로 전면 광고와 즉시 지급을 둘 다 끄면 상점에서 패스가 사라지도록 코드로 강제합니다. 상품 ID `remove_ads`는 유지합니다. 스토어 상품 ID는 바꾸거나 재사용할 수 없으므로 **표시 이름만** "광고 제거 패스"로 바꿉니다.

### Unity IAP 5의 주문 수명주기

Unity IAP 5는 4.x의 `IStoreListener`·`ProcessPurchase`를 없애고 `StoreController` 이벤트로 바꿨습니다(기초 트랙 4-4 예제는 4.x 방식).

| 5.x 멤버 | 역할 |
|---|---|
| `UnityIAPServices.StoreController()` · `await Connect()` | 컨트롤러 획득·연결. 실패는 예외가 아니라 `OnStoreDisconnected` |
| `FetchProducts(List<ProductDefinition>)` → `OnProductsFetched` | 현지화 가격 등 상품 정보(`product.metadata.localizedPriceString`) |
| `PurchaseProduct(id)` | 구매 시작 |
| `OnPurchasePending(PendingOrder)` | **결제됐지만 지급·확인 전** |
| `ConfirmPurchase(PendingOrder)` → `OnPurchaseConfirmed(Order)` | 지급 완료 통지. 결과는 `ConfirmedOrder` 또는 `FailedOrder` |
| `OnPurchaseFailed(FailedOrder)` / `OnPurchaseDeferred(DeferredOrder)` | 실패(`FailureReason`) / 보호자 승인 대기 등 — **지급 금지** |
| `FetchPurchases()` → `OnPurchasesFetched(Orders)` | 기존 구매: `ConfirmedOrders`, `PendingOrders`, `DeferredOrders` |
| `order.CartOrdered.Items()[0].Product.definition.id` | 주문의 상품 ID |

```
PurchaseProduct("remove_ads")
  ├─▶ OnPurchaseFailed(UserCancelled)   → 조용히 복귀
  ├─▶ OnPurchaseDeferred                → PurchaseOutcome.Pending, "승인 대기" 표시, 지급 금지
  └─▶ OnPurchasePending(order)          → 25장 PurchasePending(거래 ID, 상품 ID)
         ① 지급(원장)  →  ② SaveSystem.Save == true ?
              ├─ 예    →  ③ ConfirmPurchase(order)  →  OnPurchaseConfirmed
              └─ 아니오 →  확인 보류, 사용자 안내 → 다음 실행 FetchPurchases의 PendingOrders로 재처리
```

**순서가 전부입니다.** ③을 먼저 하면 확인 직후 앱이 죽었을 때 스토어는 끝난 거래로 알고 다시 알려주지 않으므로 돈만 빠져나갑니다. ①을 먼저 하면 ③ 전에 죽어도 다음 실행의 `FetchPurchases`가 같은 주문을 `PendingOrders`로 다시 줍니다. 그러면 ①이 **두 번** 실행될 수 있으므로 지급은 반드시 멱등(여러 번 실행해도 결과가 같음)해야 합니다. Unity 문서도 콜백 중 크래시 시 다음 초기화 때 다시 호출되니 중복 방지를 구현하라고 안내합니다. 웹의 결제 웹훅과 같습니다. 재전송될 수 있으니 주문 ID로 중복을 막고(멱등) DB 반영 뒤에 200을 돌려주는(확인) 순서를 지키는 것입니다.

확인하지 않은 구매는 스토어가 되돌립니다. Google Play 테스트 문서에 따르면 **라이선스 테스터 구매는 3분 안에 확인하지 않으면 자동 환불**됩니다. 이 규칙으로 "확인 누락" 버그를 잡습니다.

### 복원·재설치·환불과 영수증 검증

| 상황 | 패스 소유 여부 (원천: 스토어) | 스타터 팩 코인 3,000 (원천: 세이브 원장) |
|---|---|---|
| 확인 전 앱 강제 종료 | 다음 실행 `PendingOrders` → 지급·확인 | 원장이 중복 방지 |
| 재설치·기기 변경 | `FetchPurchases`(Android) / 복원 버튼(iOS) | 로컬 세이브가 사라져 **다시 지급됨** |
| 스토어 환불 | 다음 조회에 없음 → 소유 해제 | 회수하지 않음 |

재설치 후 코인 재지급은 **의도한 정책**입니다. 진행이 전부 사라진 사람에게 3,000코인을 다시 주는 것은 착취가 아니고, "계정당 1회"를 엄밀히 지키려면 서버 원장이 필요한데 그 비용이 피해보다 큽니다. 이 결정을 `Docs/monetization.md`에 적습니다. 소모성 상품(코인 묶음)이 생기면 판단이 뒤집힙니다. Unity 문서는 확인된 소모성 구매를 스토어가 다시 돌려주지 않으므로 원격 저장을 권합니다.

영수증 검증도 같은 논리입니다. 클라이언트만으로는 변조 앱의 가짜 구매를 막을 수 없고, 서버 검증(Google Play Developer API, App Store Server API)은 운영 비용이 듭니다. 패스와 스타터 팩은 변조로 공짜로 얻어도 **다른 플레이어가 피해를 보지 않는 싱글플레이 상품**이라 서버 검증 없이 출시하고 한계를 문서에 적습니다. Unity IAP 5에서 Apple 로컬 영수증 검증은 지원 중단(StoreKit 2 JWS 권장)되었고, Google은 `Order.Info.Receipt`를 서버로 보내 검증하도록 안내합니다. 유료 재화·온라인 랭킹·거래가 생기면 서버 검증이 필수입니다.

### 동의 흐름과 콜백 스레드

```
앱 시작
  ├─ ConsentInformation.Update(params, cb)                       UMP: 지역·동의 상태 갱신
  │     └─ ConsentForm.LoadAndShowConsentFormIfRequired(cb)      EEA·영국 등 GDPR 메시지
  │          iOS: AdMob에서 IDFA 설명 메시지를 게시했다면 그 뒤에 ATT 알림이 자동으로 이어짐
  ├─ ConsentInformation.CanRequestAds() == true 일 때만 MobileAds.Initialize → 광고 로드
  ├─ 설정 화면: PrivacyOptionsRequirementStatus == Required 이면 "개인정보 옵션" → ShowPrivacyOptionsForm
  └─ 24장 Analytics 자체 동의 (별개)
```

- 이전 실행에서 동의했다면 `CanRequestAds()`가 곧바로 true이므로, 공식 샘플처럼 갱신을 기다리지 않고 초기화를 시작합니다.
- 코인 러시는 iOS에서 **추적 권한을 요청하지 않는 것**으로 시작해도 됩니다. 추적 없이도 광고는 게재됩니다. 요청한다면 AdMob의 IDFA 설명 메시지로 UMP가 순서를 관리하게 하고 Info.plist 문구를 넣습니다. 어린이 대상이면 흐름 전체가 달라지므로(가족 정책) 코인 러시는 13세 이상으로 등록합니다.
- **스레드**: 플러그인의 광고 이벤트는 Unity 메인 스레드가 아닌 곳에서 올 수 있습니다. 거기서 UI·`GameObject`·`Time`을 건드리면 간헐적 크래시가 납니다. 공식 가이드대로 `MobileAdsEventExecutor.ExecuteInUpdate(() => ...)`로 넘깁니다. 예전의 `MobileAds.RaiseAdEventsOnUnityMainThread`는 최신 버전에서 obsolete이고, 백그라운드 중 이벤트가 지연된다는 경고가 있습니다.
- **보상 신호와 닫힘 신호의 도착 순서를 믿지 않습니다.** 닫힘을 받은 뒤 짧은 유예 시간 동안 보상 신호를 기다렸다가 결과를 확정합니다.

### Remote Config: 기본값 → 캐시 → 원격

흐름은 "로컬 기본값(JSON 에셋) 즉시 적용 → 원격 fetch 성공 시 교체 + 기기에 캐시 → 다음 실행에서 fetch가 실패하면 `origin=Cached`로 지난 원격 값"입니다. 게임은 **원격 설정을 기다리며 멈추지 않습니다.** 기본값("가장 안전한 쪽")으로 먼저 돌고 원격 값이 오면 교체합니다. Unity Remote Config는 `UnityServices.InitializeAsync()`와 Authentication 로그인(익명)이 선행되어야 하고, 익명 플레이어 ID는 스토어 개인정보 양식(Data safety)에 반영할 항목입니다. 값은 읽기 전용이지만 **비밀이 아니므로** 서버 키 같은 것은 넣지 않습니다. JSON 타입 키 하나(`monetization`)에 `MonetizationConfig` 전체를 넣어 25장의 `FromJsonOverwrite` 흐름을 그대로 씁니다.

### CPI·LTV·회수 기간

| 지표 | 정의 |
|---|---|
| CPI | 설치 1건을 사 오는 비용 (캠페인 실측) |
| LTV(N일) | 설치 1명이 N일 동안 만드는 수익 = `ARPDAU × N일간 1인당 활성 일수` |
| 1인당 활성 일수 | 리텐션 곡선 아래 넓이 (D0=100%부터 N−1일까지 합) |
| 회수 기간 / ROAS | 누적 LTV가 CPI를 넘는 날 / `LTV ÷ CPI` |

아래는 **계산 방법을 보이기 위한 가정 수치**입니다. 실제 값은 소프트 론칭으로만 압니다.

```
[가정] 리텐션 D1 35% · D3 20% · D7 12% · D14 7% · D30 4% (사이는 직선 보간)
  0~6일 활성 일수 합 ≈ 2.3일,  0~29일 ≈ 3.9일
[가정] ARPDAU(광고) $0.020,  패스 구매율 0.4% × $2.99 × (1 − 수수료 15%) ≈ 설치당 $0.010
LTV30 ≈ 3.9 × 0.020 + 0.010 ≈ $0.088
[가정] CPI $0.60  →  ROAS30 ≈ 15%  →  30일 안에 회수 불가
```

이 가정의 결론은 **유료 사용자 획득으로는 돈을 벌 수 없고, 소프트 론칭 광고비는 "측정 비용"**이라는 것입니다. 그래서 예산은 **판단에 필요한 표본 크기**로 정합니다. D1 리텐션을 ±3%p(95% 신뢰구간)로 추정하려면 `1.96² × 0.35 × 0.65 ÷ 0.03² ≈ 970` 설치, 가정 CPI $0.60이면 약 $600입니다. 실제 CPI는 국가·장르·소재에 따라 몇 배씩 달라지므로 소액 캠페인의 실측으로 다시 계산합니다. 수수료 15% 적용 조건은 스토어 정책을 확인합니다(25장).

## 실습: 코인 러시에 적용하기

### 1단계: 패키지와 계정 연결

1. Package Manager > Unity Registry에서 **In-App Purchasing**(5.x 확인)과 **Remote Config**를 설치합니다. `Edit > Project Settings > Services`에서 Unity Cloud 프로젝트를 연결합니다.
2. Google Mobile Ads 플러그인 `.unitypackage`를 `Assets > Import Package > Custom Package`로 가져옵니다.
3. `Assets > Google Mobile Ads > Settings`에 **Android·iOS 앱 ID**를 입력합니다(개발 중에도 실제 앱 ID, 광고 단위만 테스트 ID). Android 타깃에서 `Assets > External Dependency Manager > Android Resolver > Force Resolve`를 실행합니다.
4. AdMob 콘솔에서 보상형·전면 광고 단위를 하나씩 만들고, 개인정보 보호 및 메시지에서 **GDPR 메시지**를 만들어 게시합니다(없으면 UMP가 보여줄 양식이 없습니다).

### 2단계: 25장 설계 교체 — 광고 제거 패스

25장 `AdService.cs`에서 바뀌는 부분만 보입니다.

```csharp
// MonetizationConfig — 기본값 1개 변경, 필드 2개 추가
    public bool interstitialEnabled = true;          // 25장 false → true (아래 최소 판 수로 첫 세션 보호)
    public int interstitialMinTotalRuns = 5;         // 37장: 누적 판 수가 이보다 적으면 전면 광고 없음
    public bool adFreeSkipsRewardedVideo = true;     // 37장: 패스 보유자는 보상형을 시청 없이 즉시 받음
// StoreService — 속성 추가, ShouldOfferRemoveAds 교체 (25장 StoreProductButton은 이 속성을 그대로 사용)
    /// <summary>패스가 지금 설정에서 실제 효용이 있는가. false면 상점에서 상품을 숨긴다.</summary>
    public static bool RemoveAdsHasValue =>
        AdService.Config.interstitialEnabled || AdService.Config.adFreeSkipsRewardedVideo;
    public static bool ShouldOfferRemoveAds =>
        Current != null && Current.IsReady && RemoveAdsHasValue && !HasRemoveAds;
// AdService — CanOffer 두 속성 교체, ShowRewarded의 allowed 검사 바로 뒤에 분기 추가
    private static bool PassSkipsVideo => StoreService.HasRemoveAds && Config.adFreeSkipsRewardedVideo;
    public static bool CanOfferRevive => Current != null && !showing && Config.reviveEnabled
        && revivesThisRun < Config.reviveMaxPerRun && (PassSkipsVideo || Current.IsRewardedReady);
    public static bool CanOfferDoubleCoins => Current != null && !showing && Config.doubleCoinsEnabled
        && !doubledThisRun && (PassSkipsVideo || Current.IsRewardedReady);
    public static void ShowRewarded(string placement, Action<bool> onFinished)
    {
        bool allowed = placement == AdPlacements.Revive ? CanOfferRevive
                     : placement == AdPlacements.DoubleCoins && CanOfferDoubleCoins;
        if (!allowed) { onFinished?.Invoke(false); return; }   // 25장 그대로: 설정·횟수 검사가 항상 먼저
        if (PassSkipsVideo)                                    // 검사를 통과한 뒤에만 시청 없이 지급
        {
            if (placement == AdPlacements.Revive) revivesThisRun++; else doubledThisRun = true;
            Analytics.Track("ad_rewarded_pass_skip", ("placement", placement), ("group", Config.experimentGroup));
            onFinished?.Invoke(true);
            return;
        }
        // 이하 25장 코드 그대로: showing = true; 부터 Current.ShowRewarded(placement, onShown: ..., onComplete: ...) 끝까지
    }
// TryShowInterstitial — allowed 조건에 한 줄 추가
                       && SaveSystem.Load().stats.totalRuns >= Config.interstitialMinTotalRuns
```

즉시 지급 분기는 25장의 `allowed` 검사 **뒤에** 둡니다. 앞에 두면 패스 보유자는 `reviveEnabled`·`reviveMaxPerRun`·`doubledThisRun` 검사를 건너뛰어 원격 킬 스위치도, 1판 1회 제한도 듣지 않습니다. `CanOffer…`의 `!showing`도 25장대로 유지합니다. 패스 분기는 광고를 띄우지 않으므로 `showing`을 켜지 않고, 노출(`ad_impression`)도 기록하지 않습니다.

UI도 두 곳 바꿉니다. `RevivePanel` 버튼 문구는 `StoreService.HasRemoveAds ? "부활 (광고 제거 패스)" : "광고 보고 부활"`, 상점의 패스 행은 25장 `StoreProductButton`이 위에서 교체한 `StoreService.ShouldOfferRemoveAds`로 표시 여부를 정하므로 코드는 그대로 두고, 인스펙터의 Title만 "광고 제거 패스"로 바꿉니다. 스토어 콘솔과 게임 내 설명은 같은 문장을 씁니다: "판이 끝난 뒤 나오는 광고가 더 이상 나오지 않습니다. 부활·코인 2배를 광고 시청 없이 바로 받습니다(횟수 제한은 같습니다)."

25장 `IStoreService.cs`는 바꾸지 않습니다. Unity IAP의 `OnPurchaseDeferred`는 25장 계약의 `PurchaseOutcome.Pending`에 대응하고, 5단계 구현은 저장 실패로 확인을 보류한 구매에도 `Pending`을 돌려줍니다. 구매 콜백이 `Pending`이면 "처리 대기 중입니다. 승인·처리가 끝나면 자동으로 지급됩니다"를 보여줍니다.

### 3단계: 지급 원장과 테스트

10장 `SaveData`에 필드를 추가합니다. 구조 변경이므로 10장 규칙대로 `CurrentVersion`을 1 올리고 단계를 추가합니다. 스타터 팩이 캐릭터를 해금하므로 `unlockedCharacters`(25장 5단계 v3 또는 10장 연습 문제 2)가 필요합니다. 아직이라면 함께 적용합니다.

```csharp
// SaveData.cs (10장) — 필드 추가
    public List<string> grantedEntitlements = new();   // 37장: 지급을 끝낸 상품 ID
// SaveMigrator.cs (10장) — 현재 버전이 N이면 Steps에 { N, AddGrantedEntitlements }, CurrentVersion = N + 1
    private static void AddGrantedEntitlements(JObject root)
    {
        var granted = root["grantedEntitlements"] as JArray ?? new JArray();
        // 25장 방식으로 이미 스타터 팩 코인을 받은 세이브는 원장에 "처리했음"으로 옮겨 이중 지급을 막는다
        bool starterGranted = root["starterPackGranted"]?.Type == JTokenType.Boolean && (bool)root["starterPackGranted"];
        bool recorded = false;
        foreach (JToken t in granted) if ((string)t == "starter_pack") recorded = true;
        if (starterGranted && !recorded) granted.Add("starter_pack");
        root["grantedEntitlements"] = granted;
    }
```

25장 5단계의 `starterPackGranted`·`grantedTransactions`는 지우지 않습니다(필드를 지우는 것도 구조 변경입니다). 이 장부터 지급 판단은 `grantedEntitlements`만 보며, 위 이관 덕분에 25장 가짜 스토어로 스타터 팩을 이미 받은 세이브는 다시 받지 않습니다.

지급 규칙은 테스트할 수 있게 `CoinRush.SaveCore` 어셈블리의 순수 함수로 둡니다. 25장 `ProductIds`는 `Assembly-CSharp`에 있어 이 어셈블리에서 보이지 않으므로 같은 값을 상수로 두고, 7단계에서 일치를 검사합니다.

파일: `Assets/_CoinRush/Scripts/Save/Core/EntitlementLedger.cs`

```csharp
/// <summary>인앱 상품의 게임 내 지급을 한 곳에서 한 번만 수행한다. 스토어 콜백은 재전송·복원으로 여러 번 온다.</summary>
public static class EntitlementLedger
{
    public const string RemoveAdsId = "remove_ads";       // ProductIds.RemoveAds 와 같아야 함
    public const string StarterPackId = "starter_pack";   // ProductIds.StarterPack 와 같아야 함
    public const int StarterPackCoins = 3000;
    public const string StarterPackCharacter = "vault_keeper";
    /// <returns>이번 호출로 실제 지급이 일어났으면 true (저장 필요)</returns>
    public static bool TryGrant(SaveData save, string productId)
    {
        if (save == null || string.IsNullOrEmpty(productId)) return false;
        if (save.grantedEntitlements.Contains(productId)) return false;
        switch (productId)
        {
            case StarterPackId:
                save.coins += StarterPackCoins;
                if (!save.unlockedCharacters.Contains(StarterPackCharacter))
                    save.unlockedCharacters.Add(StarterPackCharacter);
                break;
            case RemoveAdsId:
                break;          // 소유 여부의 원천은 스토어. 원장에는 "처리했음"만 남긴다
            default:
                return false;   // 이 버전이 모르는 상품은 기록하지 않아야 다음 버전이 지급할 수 있다
        }
        save.grantedEntitlements.Add(productId);
        return true;
    }
}
```

파일: `Assets/_CoinRush/Tests/EditMode/EntitlementLedgerTests.cs`

```csharp
using NUnit.Framework;
public class EntitlementLedgerTests
{
    [Test]
    public void StarterPack_Is_Granted_Only_Once_Even_After_Save_RoundTrip()
    {
        var save = new SaveData { coins = 120 };
        Assert.IsTrue(EntitlementLedger.TryGrant(save, EntitlementLedger.StarterPackId));
        Assert.IsFalse(EntitlementLedger.TryGrant(save, EntitlementLedger.StarterPackId), "재전송·복원");
        string json = SaveSerializer.Serialize(save);
        SaveData loaded = SaveSerializer.Deserialize(json, out SaveReadStatus _);
        Assert.IsFalse(EntitlementLedger.TryGrant(loaded, EntitlementLedger.StarterPackId), "재시작 후 PendingOrders");
        Assert.AreEqual(120 + EntitlementLedger.StarterPackCoins, loaded.coins);
        Assert.AreEqual(1, loaded.unlockedCharacters.FindAll(c => c == EntitlementLedger.StarterPackCharacter).Count);
    }
}
```

### 4단계: 광고 단위 ID 에셋과 AdMobAdService

`AdMobAdService`는 코드에서 `AddComponent`로 만들어 인스펙터 값을 받을 수 없으므로 ID를 ScriptableObject(03장 방식)에 둡니다. 플랫폼 조건 없이 컴파일되어 Steam 빌드에서도 문제없습니다. 파일: `Assets/_CoinRush/Scripts/Monetization/AdUnitIds.cs`

```csharp
using UnityEngine;
[CreateAssetMenu(menuName = "Coin Rush/Monetization/Ad Unit Ids")]
public class AdUnitIds : ScriptableObject
{
    [Header("실제 광고 단위 ID (AdMob 콘솔)")]
    public string androidRewarded, androidInterstitial, iosRewarded, iosInterstitial;
    [Tooltip("켜져 있으면 릴리스 빌드에서도 테스트 광고. 출시 체크리스트 S1에서만 끈다.")]
    public bool forceTestAds = true;
    [Tooltip("첫 광고 요청 때 기기 로그에 출력되는 내 기기의 테스트 기기 ID")]
    public string[] testDeviceHashedIds = new string[0];
    [Tooltip("개발 빌드에서 동의 양식을 EEA 사용자처럼 강제로 표시")]
    public bool debugForceEeaConsent;
}
```

`Assets/_CoinRush/Data/AdUnitIds.asset`을 만들어 채웁니다. 다음은 동의·초기화·보상형·전면을 담당하는 `Assets/_CoinRush/Scripts/Monetization/AdMobAdService.cs`입니다. 파일 전체를 `#if UNITY_ANDROID || UNITY_IOS`로 감싸 Standalone(Steam) 타깃에는 이 클래스가 존재하지 않게 합니다.

```csharp
#if UNITY_ANDROID || UNITY_IOS
using System;
using System.Collections.Generic;
using GoogleMobileAds.Api;
using GoogleMobileAds.Common;
using GoogleMobileAds.Ump.Api;
using UnityEngine;
/// <summary>25장 IAdService의 실제 구현. MonetizationBootstrap이 AddComponent로 생성한다.</summary>
public class AdMobAdService : MonoBehaviour, IAdService
{
    // 공식 테스트 광고 단위 (developers.google.com/admob/unity/test-ads)
#if UNITY_ANDROID
    private const string TestRewardedId = "ca-app-pub-3940256099942544/5224354917";
    private const string TestInterstitialId = "ca-app-pub-3940256099942544/1033173712";
#else
    private const string TestRewardedId = "ca-app-pub-3940256099942544/1712485313";
    private const string TestInterstitialId = "ca-app-pub-3940256099942544/4411468910";
#endif
    private const float RewardGraceSeconds = 0.5f;
    private AdUnitIds ids;
    private bool initStarted, initialized;
    private RewardedAd rewarded;
    private bool rewardedLoading, rewardEarned;
    private int rewardedAttempts;
    private float rewardedRetryAt = -1f, rewardedClosedAt = -1f;
    private Action rewardedShown;                  // 표시 1회당 한 번: 호출하면 null
    private Action<AdResult> rewardedCallback;     // 표시 1회당 한 번: 호출하면 null (null이 아니면 표시 중)
    private InterstitialAd interstitial;
    private bool interstitialLoading;
    private int interstitialAttempts;
    private float interstitialRetryAt = -1f;
    private Action interstitialShown;
    private Action interstitialCallback;
    private bool Showing => rewardedCallback != null || interstitialCallback != null;
    public bool IsRewardedReady => initialized && !Showing && rewarded != null && rewarded.CanShowAd();
    public bool IsInterstitialReady => initialized && !Showing && interstitial != null && interstitial.CanShowAd();
    public static bool PrivacyOptionsRequired =>
        ConsentInformation.PrivacyOptionsRequirementStatus == PrivacyOptionsRequirementStatus.Required;
    private bool UseTestAds => ids == null || ids.forceTestAds || Debug.isDebugBuild;
#if UNITY_ANDROID
    private string RewardedId => UseTestAds ? TestRewardedId : ids.androidRewarded;
    private string InterstitialId => UseTestAds ? TestInterstitialId : ids.androidInterstitial;
#else
    private string RewardedId => UseTestAds ? TestRewardedId : ids.iosRewarded;
    private string InterstitialId => UseTestAds ? TestInterstitialId : ids.iosInterstitial;
#endif
    public void Configure(AdUnitIds adUnitIds) => ids = adUnitIds;
    /// <summary>① 동의 갱신·양식 → ② CanRequestAds일 때만 SDK 초기화 → ③ 광고 로드</summary>
    public void BeginConsentAndInitialize()
    {
        var testDevices = new List<string>(ids != null ? ids.testDeviceHashedIds : new string[0]);
        MobileAds.SetiOSAppPauseOnBackground(true);   // iOS도 Android처럼 광고 중 Unity 일시정지
        MobileAds.SetRequestConfiguration(new RequestConfiguration { TestDeviceIds = testDevices });
        var request = new ConsentRequestParameters
        {
            TagForUnderAgeOfConsent = false,
            ConsentDebugSettings = new ConsentDebugSettings
            {
                DebugGeography = Debug.isDebugBuild && ids != null && ids.debugForceEeaConsent
                    ? DebugGeography.EEA : DebugGeography.Disabled,
                TestDeviceHashedIds = testDevices,
            }
        };
        if (ConsentInformation.CanRequestAds()) InitializeSdk();   // 지난 실행에서 이미 동의함
        ConsentInformation.Update(request, (FormError updateError) =>
        {
            if (updateError != null) { FinishConsent(updateError.Message); return; }
            ConsentForm.LoadAndShowConsentFormIfRequired((FormError formError) => FinishConsent(formError?.Message));
        });
    }
    private void FinishConsent(string error) => MobileAdsEventExecutor.ExecuteInUpdate(() =>
    {
        if (error != null) Debug.LogWarning($"[Ads] 동의 흐름 오류: {error}");
        Analytics.Track("ads_consent", ("can_request", ConsentInformation.CanRequestAds()),
            ("status", ConsentInformation.ConsentStatus.ToString()));
        if (ConsentInformation.CanRequestAds()) InitializeSdk();
    });
    /// <summary>설정 화면(11장)의 "개인정보 옵션" 버튼. PrivacyOptionsRequired일 때만 버튼을 보인다.</summary>
    public static void ShowPrivacyOptions() => ConsentForm.ShowPrivacyOptionsForm((FormError error) =>
    {
        if (error != null) Debug.LogWarning($"[Ads] 개인정보 옵션 오류: {error.Message}");
    });
    private void InitializeSdk()
    {
        if (initStarted) return; initStarted = true;
        MobileAds.Initialize((InitializationStatus status) => MobileAdsEventExecutor.ExecuteInUpdate(() =>
        {
            if (status == null) { initStarted = false; Debug.LogError("[Ads] 초기화 실패"); return; }
            initialized = true; LoadRewarded(); LoadInterstitial();
        }));
    }
    private void LoadRewarded()
    {
        if (rewardedLoading) return;
        rewardedLoading = true; rewarded?.Destroy(); rewarded = null;
        RewardedAd.Load(RewardedId, new AdRequest(), (RewardedAd ad, LoadAdError error) =>
            MobileAdsEventExecutor.ExecuteInUpdate(() =>
            {
                rewardedLoading = false;
                if (error != null || ad == null) { rewardedRetryAt = Retry("rewarded", error, ref rewardedAttempts); return; }
                rewardedAttempts = 0;
                rewarded = ad;
                // 모든 광고 이벤트는 ① 메인 스레드로 넘기고 ② 지금 들고 있는 광고의 것인지 확인한다.
                // 완료 처리에서 rewarded를 비우므로, 이미 끝난 광고의 늦은 이벤트는 여기서 걸러진다.
                ad.OnAdPaid += (AdValue v) => MobileAdsEventExecutor.ExecuteInUpdate(() => TrackPaid("rewarded", v));
                ad.OnAdFullScreenContentOpened += () => MobileAdsEventExecutor.ExecuteInUpdate(() =>
                {
                    if (ad != rewarded) return;
                    Action shown = rewardedShown; rewardedShown = null;
                    shown?.Invoke();                                   // 25장 계약의 onShown → 파사드가 ad_impression 기록
                });
                ad.OnAdFullScreenContentClosed += () => MobileAdsEventExecutor.ExecuteInUpdate(() =>
                {
                    if (ad == rewarded && rewardedCallback != null) rewardedClosedAt = Time.unscaledTime;
                });
                ad.OnAdFullScreenContentFailed += (AdError e) => MobileAdsEventExecutor.ExecuteInUpdate(() =>
                {
                    if (ad == rewarded) CompleteRewarded(AdResult.Failed);   // 표시 실패: onShown 없이 onComplete만
                });
            }));
    }
    public void ShowRewarded(string placement, Action onShown, Action<AdResult> onComplete)
    {
        if (!IsRewardedReady) { onComplete?.Invoke(AdResult.NotReady); return; }   // 표시 안 됨 → onShown 없음
        rewardedShown = onShown; rewardedCallback = onComplete; rewardEarned = false; rewardedClosedAt = -1f;
        rewarded.Show((Reward reward) => MobileAdsEventExecutor.ExecuteInUpdate(() => rewardEarned = true));
    }
    private void CompleteRewarded(AdResult result)
    {
        if (rewardedCallback == null) return;                   // 이미 완료됨 (닫힘·실패가 둘 다 와도 한 번)
        Action<AdResult> callback = rewardedCallback;
        rewardedCallback = null; rewardedShown = null; rewardedClosedAt = -1f;
        LoadRewarded();               // 한 번 보여준 광고는 재사용 불가 → 파기 후 다시 로드 (rewarded = null)
        callback.Invoke(result);
    }
    private void LoadInterstitial()
    {
        if (interstitialLoading) return;
        interstitialLoading = true; interstitial?.Destroy(); interstitial = null;
        InterstitialAd.Load(InterstitialId, new AdRequest(), (InterstitialAd ad, LoadAdError error) =>
            MobileAdsEventExecutor.ExecuteInUpdate(() =>
            {
                interstitialLoading = false;
                if (error != null || ad == null) { interstitialRetryAt = Retry("interstitial", error, ref interstitialAttempts); return; }
                interstitialAttempts = 0;
                interstitial = ad;
                ad.OnAdPaid += (AdValue v) => MobileAdsEventExecutor.ExecuteInUpdate(() => TrackPaid("interstitial", v));
                ad.OnAdFullScreenContentOpened += () => MobileAdsEventExecutor.ExecuteInUpdate(() =>
                {
                    if (ad != interstitial) return;
                    Action shown = interstitialShown; interstitialShown = null;
                    shown?.Invoke();
                });
                ad.OnAdFullScreenContentClosed += () => MobileAdsEventExecutor.ExecuteInUpdate(() =>
                {
                    if (ad == interstitial) CompleteInterstitial();
                });
                ad.OnAdFullScreenContentFailed += (AdError e) => MobileAdsEventExecutor.ExecuteInUpdate(() =>
                {
                    if (ad == interstitial) CompleteInterstitial();   // 표시 실패: onShown 없이 onClosed만
                });
            }));
    }
    public void ShowInterstitial(string placement, Action onShown, Action onClosed)
    {
        if (!IsInterstitialReady) { onClosed?.Invoke(); return; }   // 표시 안 됨 → onShown 없음
        interstitialShown = onShown; interstitialCallback = onClosed;
        interstitial.Show();
    }
    private void CompleteInterstitial()
    {
        if (interstitialCallback == null) return;               // 이미 완료됨
        Action callback = interstitialCallback;
        interstitialCallback = null; interstitialShown = null;
        LoadInterstitial();           // interstitial = null → 같은 광고의 늦은 이벤트는 무시됨
        callback.Invoke();
    }
    private void Update()
    {
        // 닫힘 후 잠깐 보상 신호를 기다렸다가 확정 (두 신호의 도착 순서는 보장되지 않음)
        if (rewardedCallback != null && rewardedClosedAt >= 0f
            && (rewardEarned || Time.unscaledTime - rewardedClosedAt > RewardGraceSeconds))
            CompleteRewarded(rewardEarned ? AdResult.Rewarded : AdResult.Skipped);
        if (!initialized || Showing) return;
        if (rewarded == null && rewardedRetryAt >= 0f && Time.unscaledTime >= rewardedRetryAt) { rewardedRetryAt = -1f; LoadRewarded(); }
        if (interstitial == null && interstitialRetryAt >= 0f && Time.unscaledTime >= interstitialRetryAt) { interstitialRetryAt = -1f; LoadInterstitial(); }
        if (rewarded != null && !rewarded.CanShowAd()) LoadRewarded();                // 오래되어 표시할 수 없게 된 광고 교체
        if (interstitial != null && !interstitial.CanShowAd()) LoadInterstitial();
    }
    // 실패 재시도 간격을 10, 20, 40 ... 최대 320초로 늘린다 (즉시 무한 재요청 금지)
    private static float Retry(string format, LoadAdError error, ref int attempts)
    {
        attempts = Mathf.Min(attempts + 1, 6);
        Analytics.Track("ad_load_fail", ("format", format), ("code", error != null ? error.GetCode() : -1));
        return Time.unscaledTime + 5f * Mathf.Pow(2f, attempts);
    }
    // Value는 마이크로 단위(1,000,000 = 1통화 단위)의 추정치이며 정산액과 다를 수 있다
    private static void TrackPaid(string format, AdValue v) =>
        Analytics.Track("ad_paid", ("format", format), ("value_micros", v.Value), ("currency", v.CurrencyCode),
            ("precision", v.Precision.ToString()));
    private void OnDestroy() { rewarded?.Destroy(); interstitial?.Destroy(); }
}
#endif
```

25장 `IAdService`의 두 메서드 시그니처(`onShown` 포함)를 그대로 구현합니다. 인자만 맞추고 `onShown`을 부르지 않으면 컴파일은 되어도 파사드의 `ad_impression`이 0으로 찍혀 25장 A/B 실험의 주 지표가 사라집니다. 콜백 규칙은 다음과 같습니다.

| 경로 | `onShown` | `onComplete` / `onClosed` |
|---|---|---|
| 준비 안 됨(로드 실패·로드 중·표시 중) | 호출 안 함 | 즉시 1회 (`NotReady` / 닫힘) |
| 표시 실패 `OnAdFullScreenContentFailed` | 호출 안 함 | 1회 (`Failed` / 닫힘) |
| 표시 `OnAdFullScreenContentOpened` → 닫힘 `OnAdFullScreenContentClosed` | 열림에서 1회 | 닫힘(보상형은 유예 후)에서 1회 |

한 번 호출한 콜백은 필드를 `null`로 비워 두 번 부르지 않고, 완료 처리에서 광고를 파기하므로(`LoadRewarded`·`LoadInterstitial`) 같은 광고의 늦은 이벤트는 `ad == rewarded` 검사에서 걸러집니다. 모든 이벤트는 `ExecuteInUpdate`로 메인 스레드에서 처리하므로 파사드의 `Analytics.Track`을 그대로 불러도 안전합니다. Android는 광고가 떠 있는 동안 Unity가 멈추므로 `onShown`이 실제로는 광고가 닫힌 직후 `onComplete` 바로 앞에 실행될 수 있습니다. 노출 **수**는 정확하지만 이벤트 시각은 닫힘 시각에 가깝다는 점을 분석에서 감안합니다.

### 5단계: UnityIapStoreService — 지급 후 확인, 복원, 환불 반영

**이름 충돌 주의**: Unity IAP 5에는 `UnityEngine.Purchasing.IStoreService` 인터페이스가 있습니다. 25장의 `IStoreService`는 전역 네임스페이스에 있어 이름 해석에서 우선하지만, 헷갈리지 않게 `global::IStoreService`로 적습니다. 파일: `Assets/_CoinRush/Scripts/Monetization/UnityIapStoreService.cs`

```csharp
#if UNITY_ANDROID || UNITY_IOS
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Purchasing;
/// <summary>25장 IStoreService의 Unity IAP 5.x 구현.</summary>
public class UnityIapStoreService : MonoBehaviour, global::IStoreService
{
    private const string OwnedCachePrefix = "iap_owned_";
    private static readonly (string id, ProductType type)[] Catalog =
    {
        (ProductIds.RemoveAds, ProductType.NonConsumable),
        (ProductIds.StarterPack, ProductType.NonConsumable),
    };
    public event Action<PendingPurchase> PurchasePending;   // 25장 계약: 지급은 수신자가, 확인은 수신자의 ConfirmPurchase 호출로
    public bool IsReady { get; private set; }
    private StoreController controller;
    private readonly HashSet<string> owned = new HashSet<string>();
    private readonly Dictionary<string, PendingOrder> unconfirmed = new Dictionary<string, PendingOrder>();   // 거래 ID → 확인 대기 주문
    private readonly Dictionary<string, Action<PurchaseOutcome>> purchaseCallbacks = new Dictionary<string, Action<PurchaseOutcome>>();
    private Action<bool> restoreCallback;
    public async void Connect()
    {
        // 오프라인으로 시작해도 패스 구매자가 전면 광고를 보지 않도록 지난 조회 결과를 캐시로 사용
        foreach (var (id, _) in Catalog)
            if (PlayerPrefs.GetInt(OwnedCachePrefix + id, 0) == 1) owned.Add(id);
        controller = UnityIAPServices.StoreController();
        controller.OnPurchasePending += HandlePending;
        controller.OnPurchaseConfirmed += HandleConfirmed;
        controller.OnPurchaseFailed += HandleFailed;
        controller.OnPurchaseDeferred += HandleDeferred;
        controller.OnProductsFetched += products => { IsReady = true; controller.FetchPurchases(); };
        controller.OnProductsFetchFailed += failure => Debug.LogWarning($"[IAP] 상품 조회 실패: {failure}");
        controller.OnPurchasesFetched += HandlePurchasesFetched;
        controller.OnPurchasesFetchFailed += failure => { Debug.LogWarning($"[IAP] 구매 조회 실패: {failure}"); FinishRestore(false); };
        controller.OnStoreDisconnected += failure => { IsReady = false; Debug.LogWarning($"[IAP] 연결 끊김: {failure}"); };
        controller.ProcessPendingOrdersOnPurchasesFetched(false);   // 조회된 미완료 주문은 아래에서 직접 처리
        await controller.Connect();
        controller.FetchProducts(Catalog.Select(p => new ProductDefinition(p.id, p.type)).ToList());
    }
    public string GetLocalizedPrice(string productId)
    {
        Product product = controller?.GetProductById(productId);
        return product != null && product.availableToPurchase ? product.metadata.localizedPriceString : "";
    }
    public bool Owns(string productId) => owned.Contains(productId);
    public void Purchase(string productId, Action<PurchaseOutcome> onComplete)
    {
        if (!IsReady || purchaseCallbacks.ContainsKey(productId) || controller.GetProductById(productId) == null)
        { onComplete?.Invoke(PurchaseOutcome.Failed); return; }
        purchaseCallbacks[productId] = onComplete;
        Analytics.Track("iap_start", ("product_id", productId));
        controller.PurchaseProduct(productId);
    }
    public void RestorePurchases(Action<bool> onComplete)
    {
        if (!IsReady) { onComplete?.Invoke(false); return; }
        restoreCallback = onComplete;
#if UNITY_IOS
        controller.RestoreTransactions((bool ok, string error) => FinishRestore(ok));   // 복원분은 OnPurchasesFetched로도 옴
#else
        controller.FetchPurchases();   // Android는 조회가 곧 복원
#endif
    }
    // 주문을 보관하고 PurchasePending을 발행할 뿐, 여기서 확인하지 않는다.
    // 수신자가 ① 지급 ② 저장 성공을 확인한 뒤 ConfirmPurchase를 부른다. 이 순서를 바꾸지 않는다.
    private void HandlePending(PendingOrder order)
    {
        string id = ProductIdOf(order);
        if (id == null) return;
        string transactionId = TransactionIdOf(order, id);
        unconfirmed[transactionId] = order;
        MarkOwned(id);                                                   // 소유의 원천은 스토어: 결제됐으면 소유
        PurchasePending?.Invoke(new PendingPurchase(transactionId, id)); // 수신자가 동기적으로 지급·저장·확인
        // 수신자가 확인했으면 목록에서 빠졌다. 남아 있으면 저장 실패 → 다음 FetchPurchases에서 다시 온다.
        PurchaseOutcome outcome = unconfirmed.ContainsKey(transactionId) ? PurchaseOutcome.Pending : PurchaseOutcome.Success;
        Resolve(id, outcome);
        Analytics.Track("iap_purchase", ("product_id", id), ("outcome", outcome.ToString()));
    }
    public void ConfirmPurchase(PendingPurchase purchase)
    {
        // 복원으로 발행한 거래는 이미 확정되어 목록에 없다 → 할 일 없음
        if (!unconfirmed.TryGetValue(purchase.TransactionId, out PendingOrder order)) return;
        unconfirmed.Remove(purchase.TransactionId);
        controller.ConfirmPurchase(order);
    }
    private void HandleConfirmed(Order order)
    {
        // 확인 실패여도 지급·저장은 끝났다. 다음 FetchPurchases에서 PendingOrders로 다시 와 확인을 재시도한다.
        if (order is FailedOrder failed)
            Debug.LogWarning($"[IAP] 확인 실패 {ProductIdOf(order)}: {failed.FailureReason} {failed.Details}");
    }
    private void HandleFailed(FailedOrder order)
    {
        string id = ProductIdOf(order);
        PurchaseOutcome outcome = order.FailureReason == PurchaseFailureReason.UserCancelled
            ? PurchaseOutcome.Cancelled : PurchaseOutcome.Failed;
        Resolve(id, outcome);
        Analytics.Track("iap_purchase", ("product_id", id ?? "unknown"), ("outcome", outcome.ToString()),
            ("reason", order.FailureReason.ToString()));
    }
    private void HandleDeferred(DeferredOrder order)
    {
        string id = ProductIdOf(order);
        Resolve(id, PurchaseOutcome.Pending);   // 25장 계약의 Pending. 지급하지 않는다. 승인되면 OnPurchasePending이 온다.
        Analytics.Track("iap_purchase", ("product_id", id ?? "unknown"), ("outcome", "Pending"), ("reason", "Deferred"));
    }
    private void HandlePurchasesFetched(Orders orders)
    {
        var confirmedIds = new HashSet<string>();
        foreach (Order order in orders.ConfirmedOrders)       // 재설치·기기 변경 복원
        {
            string id = ProductIdOf(order);
            if (id == null || !confirmedIds.Add(id)) continue;
            MarkOwned(id);
            PurchasePending?.Invoke(new PendingPurchase(TransactionIdOf(order, id), id));   // 원장이 중복 지급을 막음, 확인은 no-op
        }
        var pendingIds = new HashSet<string>();
        foreach (PendingOrder order in orders.PendingOrders)   // 지난 실행에서 확인 전에 끊긴 주문, 저장 실패로 확인을 보류한 주문
        {
            string id = ProductIdOf(order);
            if (id == null) continue;
            pendingIds.Add(id);
            HandlePending(order);                             // 원장이 멱등하므로 재처리해도 안전
        }
        foreach (var (id, type) in Catalog)
        {
            if (type == ProductType.Consumable || pendingIds.Contains(id) || confirmedIds.Contains(id)) continue;
            RevokeOwnership(id);                              // 환불·취소 반영
        }
        FinishRestore(true);
    }
    private void MarkOwned(string id)
    {
        owned.Add(id); PlayerPrefs.SetInt(OwnedCachePrefix + id, 1); PlayerPrefs.Save();
    }
    private void RevokeOwnership(string id)
    {
        if (!owned.Remove(id)) return;
        PlayerPrefs.DeleteKey(OwnedCachePrefix + id); PlayerPrefs.Save();
        Analytics.Track("iap_revoked", ("product_id", id));
    }
    private void Resolve(string id, PurchaseOutcome outcome)
    {
        if (id == null || !purchaseCallbacks.TryGetValue(id, out Action<PurchaseOutcome> callback)) return;
        purchaseCallbacks.Remove(id); callback?.Invoke(outcome);
    }
    private void FinishRestore(bool ok)
    {
        Action<bool> callback = restoreCallback; restoreCallback = null; callback?.Invoke(ok);
    }
    private static string ProductIdOf(Order order) =>
        order?.CartOrdered?.Items().FirstOrDefault()?.Product?.definition?.id;
    // 스토어 거래 ID. 비어 있는 스토어(일부 테스트 환경)에서는 상품 ID로 대신한다 — 비소모성은 상품당 거래 하나
    private static string TransactionIdOf(Order order, string productId) =>
        string.IsNullOrEmpty(order?.Info?.TransactionID) ? productId : order.Info.TransactionID;
}
#endif
```

이 클래스는 25장 `IStoreService` 계약을 그대로 구현합니다. 스토어 쪽은 **주문을 보관하고 `PurchasePending`을 발행할 뿐 스스로 확인하지 않습니다.** 확인은 수신자(7단계 부트스트랩)가 검증 → 중복 확인 → 지급 → **`SaveSystem.Save`가 true를 돌려준 것을 확인**한 뒤 `ConfirmPurchase(PendingPurchase)`를 불렀을 때만 일어납니다. 이벤트 발행 뒤 `unconfirmed`에 주문이 남아 있으면 수신자가 확인을 보류한 것이므로 구매 콜백에는 `Success`가 아니라 `Pending`을 돌려줍니다. 보류된 주문은 다음 실행(또는 Android의 "구매 복원")의 `FetchPurchases`에서 `PendingOrders`로 다시 오고, 원장이 두 번째 지급을 막습니다.

- 수신자는 **동기적으로** 저장과 확인까지 끝내야 합니다. `async`로 저장을 미루면 발행 직후의 `unconfirmed` 검사와 순서 보장이 깨집니다.
- 복원(`ConfirmedOrders`)도 같은 `PurchasePending`으로 보냅니다. 이미 확정된 거래라 `unconfirmed`에 없으므로 `ConfirmPurchase`는 아무 일도 하지 않고, 재설치 후 원장 지급만 일어납니다.
- 확인하지 않은 구매는 결국 스토어가 환불합니다. 저장이 계속 실패하는 기기(디스크 가득 참, 세이브 보호 모드)라면 "돈만 나가고 보상 없음"보다 환불이 낫습니다.

### 6단계: Remote Config 실제 fetch

Unity Cloud 대시보드 > Remote Config(development 환경)에 **JSON 타입** 키 `monetization`을 만듭니다.

```json
{ "reviveEnabled": true, "reviveMaxPerRun": 1, "doubleCoinsEnabled": true, "interstitialEnabled": true,
  "interstitialEveryNRuns": 3, "interstitialMinSeconds": 180, "interstitialMinTotalRuns": 5,
  "adFreeSkipsRewardedVideo": true, "experimentName": "", "experimentGroup": "control" }
```

파일: `Assets/_CoinRush/Scripts/Monetization/RemoteMonetizationConfig.cs`

```csharp
using System;
using System.Threading.Tasks;
using Unity.Services.Authentication;
using Unity.Services.Core;
using Unity.Services.RemoteConfig;
using UnityEngine;
public static class RemoteMonetizationConfig
{
    public const string Key = "monetization";
    public struct UserAttributes { public int totalRuns; }       // Game Overrides 조건용 (없어도 되지만 형식 인자는 필요)
    public struct AppAttributes { public string appVersion; }
    /// <summary>실패·시간 초과·키 없음이면 defaults를 돌려준다. 예외를 밖으로 던지지 않는다.</summary>
    public static async Task<MonetizationConfig> FetchAsync(MonetizationConfig defaults, int totalRuns, int timeoutMs = 4000)
    {
        try
        {
            if (UnityServices.State == ServicesInitializationState.Uninitialized) await UnityServices.InitializeAsync();
            if (!AuthenticationService.Instance.IsSignedIn) await AuthenticationService.Instance.SignInAnonymouslyAsync();
            Task fetch = RemoteConfigService.Instance.FetchConfigsAsync(
                new UserAttributes { totalRuns = totalRuns }, new AppAttributes { appVersion = Application.version });
            if (await Task.WhenAny(fetch, Task.Delay(timeoutMs)) != fetch)
            {
                Analytics.Track("remote_config", ("origin", "Timeout"));   // 늦게 온 값은 캐시되어 다음 실행에 쓰임
                return defaults;
            }
            await fetch;   // 예외가 있었다면 catch로
            RuntimeConfig rc = RemoteConfigService.Instance.appConfig;
            if (!rc.HasKey(Key)) return defaults;
            MonetizationConfig result = JsonUtility.FromJson<MonetizationConfig>(JsonUtility.ToJson(defaults));   // 복사
            JsonUtility.FromJsonOverwrite(rc.GetJson(Key), result);   // 원격에 없는 필드는 기본값 유지
            Analytics.Track("remote_config", ("origin", rc.origin.ToString()), ("group", result.experimentGroup));
            return result;
        }
        catch (Exception e)
        {
            Debug.LogWarning($"[RemoteConfig] 기본값 사용: {e.Message}");
            return defaults;
        }
    }
}
```

### 7단계: MonetizationBootstrap 교체

25장 `MonetizationBootstrap.cs`를 통째로 교체합니다. 가짜 서비스 선택 조건은 25장과 같습니다. 모바일 타깃의 **에디터 또는 `COINRUSH_FAKE_SERVICES` 정의가 있는 빌드**에서만 가짜를 쓰고, `DEVELOPMENT_BUILD`에는 묶지 않습니다. **개발 빌드야말로 실제 SDK와 테스트 광고로 검증해야 하기 때문입니다.** 실기기에서 가짜로 흐름만 보려면 Scripting Define Symbols에 `COINRUSH_FAKE_SERVICES`를 넣습니다.

```csharp
using UnityEngine;
public class MonetizationBootstrap : MonoBehaviour
{
    [Tooltip("원격 설정을 받기 전/실패 시 쓰는 기본값 JSON (MonetizationConfig 필드)")]
    [SerializeField] private TextAsset defaultConfigJson;
    [SerializeField] private AdUnitIds adUnitIds;
    [SerializeField] private bool fetchRemoteConfig = true;
    private async void Awake()
    {
        Debug.Assert(ProductIds.StarterPack == EntitlementLedger.StarterPackId
                     && ProductIds.RemoveAds == EntitlementLedger.RemoveAdsId, "상품 ID 상수 불일치");
        DontDestroyOnLoad(gameObject);
        var defaults = new MonetizationConfig();
        if (defaultConfigJson != null) JsonUtility.FromJsonOverwrite(defaultConfigJson.text, defaults);
#if (UNITY_ANDROID || UNITY_IOS) && (UNITY_EDITOR || COINRUSH_FAKE_SERVICES)
        Install(gameObject.AddComponent<FakeAdService>(), gameObject.AddComponent<FakeStoreService>(), defaults);
#elif UNITY_ANDROID || UNITY_IOS
        var admob = gameObject.AddComponent<AdMobAdService>();
        admob.Configure(adUnitIds);
        var iap = gameObject.AddComponent<UnityIapStoreService>();
        Install(admob, iap, defaults);          // 이벤트 구독이 Connect보다 먼저
        iap.Connect();                          // 구매 복구는 광고 동의와 무관하게 바로
        admob.BeginConsentAndInitialize();
#else
        Install(null, null, defaults);          // Steam 유료판: 광고·IAP·원격 설정 없음
#endif
        RunRecorder.RunStarted += OnRunStarted;   // 25장과 같음: 판 시작에서만 부활 횟수·코인 2배·판 ID 초기화
        if (fetchRemoteConfig && AdService.Current != null)
        {
            MonetizationConfig remote = await RemoteMonetizationConfig.FetchAsync(defaults, SaveSystem.Load().stats.totalRuns);
            if (this == null) return;
            AdService.Install(AdService.Current, remote);   // 서비스는 그대로, 설정만 교체 (판 단위 횟수는 유지됨)
        }
        MonetizationConfig applied = AdService.Config;   // 25장과 같음: 최종 적용된 그룹을 A/B 분모로 기록
        if (!string.IsNullOrEmpty(applied.experimentName))
            Analytics.Track("experiment_assign", ("experiment", applied.experimentName), ("group", applied.experimentGroup));
    }
    private void OnDestroy() => RunRecorder.RunStarted -= OnRunStarted;
    private static void OnRunStarted(RunRecorder run) => AdService.OnRunStarted(run.RunId);
    private static void Install(IAdService ads, IStoreService store, MonetizationConfig config)
    {
        AdService.Install(ads, config);
        StoreService.Install(store);
        if (store != null) store.PurchasePending += OnPurchasePending;
    }
    /// <summary>상점 UI가 구독해 "구매는 완료됐지만 저장하지 못했습니다" 안내를 띄운다 (인자: 상품 ID)</summary>
    public static event System.Action<string> EntitlementSaveFailed;
    /// <summary>25장 계약: 검증 → 중복 확인 → 지급 → 저장 성공 확인 → 구매 확인. 구매·재전달·복원이 모두 여기로 온다.</summary>
    private static void OnPurchasePending(PendingPurchase purchase)
    {
        // ① 검증: 서버 영수증 검증은 생략(개념 절). 도입하면 실패 시 지급도 확인도 하지 않고 기록만 남긴다.
        SaveData save = SaveSystem.Load();
        bool newlyGranted = EntitlementLedger.TryGrant(save, purchase.ProductId);   // ② 중복 확인 + ③ 지급 (멱등)
        // ④ 영속화: 새 지급이 없어도 저장한다. 앞선 저장이 실패했다면 메모리에만 지급이 남아 있기 때문
        if (!SaveSystem.Save(save))
        {
            // 확인하지 않는다 → 주문은 미확정으로 남고 다음 FetchPurchases에서 다시 온다 → ②가 중복을 막는다
            Debug.LogWarning($"[IAP] 저장 실패로 거래 {purchase.TransactionId}를 확인하지 않음");
            Analytics.Track("iap_entitlement_save_failed", ("product_id", purchase.ProductId),
                ("read_only", SaveSystem.IsReadOnly));
            EntitlementSaveFailed?.Invoke(purchase.ProductId);
            return;
        }
        StoreService.Current.ConfirmPurchase(purchase);                             // ⑤ 구매 확인 (저장 성공 후에만)
        Analytics.Track("iap_entitlement", ("product_id", purchase.ProductId), ("newly_granted", newlyGranted));
    }
}
```

`StoreService.Current`는 `Install` 안에서 구독보다 먼저 설정되므로 핸들러에서 바로 쓸 수 있습니다. 통째로 교체하더라도 25장 부트스트랩의 **`RunRecorder.RunStarted` 구독(`OnDestroy`에서 해제)과 `experiment_assign` 기록은 그대로 옮깁니다.** 구독이 빠지면 `AdService.OnRunStarted`가 한 번도 불리지 않아, 첫 판에 부활·코인 2배를 한 번 쓰면 앱을 다시 켤 때까지 다음 판들에서 버튼이 나오지 않고 `CurrentRunId`도 비어 있어 부활 창의 판 ID 검사가 무력해집니다. 구독은 첫 `await`보다 앞에 두어 원격 설정을 기다리는 동안 시작된 판도 놓치지 않게 합니다. 상점 패널(25장 5단계)은 `OnEnable`/`OnDisable`에서 `MonetizationBootstrap.EntitlementSaveFailed`를 구독·해제하고 "구매는 완료되었지만 저장 공간 부족 등으로 지급을 저장하지 못했습니다. 저장 공간을 확보한 뒤 앱을 다시 시작하면 자동으로 지급됩니다"를 띄웁니다. 결제 금액이 빠져나간 사용자에게 아무 말도 하지 않으면 환불 요청과 부정 리뷰로 돌아옵니다.

인스펙터에 `AdUnitIds.asset`을 연결합니다. 11장 설정 화면에는 "구매 복원"(`StoreService.Current?.RestorePurchases`)과, 모바일에서 `AdMobAdService.PrivacyOptionsRequired`일 때만 보이는 "개인정보 옵션"(`AdMobAdService.ShowPrivacyOptions()`, `#if UNITY_ANDROID || UNITY_IOS`로 감쌈) 버튼을 둡니다.

### 8단계: 스토어 콘솔과 테스터

**Google Play (주 대상)**

1. 업로드 키로 서명한 **AAB**를 **내부 테스트** 트랙에 올립니다(서명·키 보관은 38장).
2. 수익 창출 > 인앱 상품에서 `remove_ads`, `starter_pack`을 만들고 활성화합니다.
3. 설정 > 라이선스 테스트에 테스트 Google 계정을 추가하고, 같은 계정을 테스트 트랙 테스터로 넣어 참여 URL로 참여합니다. 게시 후 테스터에게 보이기까지 몇 시간 걸릴 수 있습니다.
4. 기기에서 그 계정으로 **Play 스토어를 통해 설치**합니다. 에디터에서 직접 설치한 빌드는 상품 조회가 실패할 수 있습니다.
5. 결제 창에서 공식 테스트 결제 수단을 고릅니다: "Test instrument, always approves" / "always declines" / "Slow test card, approves after a few minutes" 등.

**iOS (차이점만)**: App Store Connect > 사용자 및 액세스 > Sandbox에서 Sandbox Apple 계정을 만들고(기존 Apple 계정 이메일 불가), 기기의 설정 > 개발자 > Sandbox Apple 계정(iOS 18 이상)으로 로그인합니다. 유료 앱 계약이 활성이어야 상품이 조회되고, 복원 버튼이 필수이며, Unity IAP 5는 StoreKit 2 기반이라 iOS 15 이상이 필요합니다.

### 9단계: 실기기 검증 체크리스트

`Docs/monetization-verification.md`에 복사해 빌드마다 결과·날짜를 채웁니다. **하나라도 실패면 해당 빌드는 제출 금지**입니다(출시 차단 기준은 38장).

| # | 시나리오 | 조작 | 기대 결과 | 확인할 이벤트/로그 |
|---|---|---|---|---|
| A1 | EEA 동의·변경 | `debugForceEeaConsent` 개발 빌드, 앱 데이터 삭제 후 실행 → 설정 > 개인정보 옵션 | 동의 양식 → 광고 로드, 옵션에서 양식 재표시 | `ads_consent can_request=true` |
| A2 | 보상형 완료 / 중간 닫기 | 사망 → 광고 보고 부활 → 끝까지 / 도중 닫기 | "Test Ad" 라벨, 부활 / 부활 없이 결과 화면 | `ad_rewarded_end result=Rewarded` / `Skipped` |
| A3 | 오프라인 | 비행기 모드로 시작 | 부활 버튼 없음, 오류 팝업 없음 | `ad_load_fail` 간격이 늘어남 |
| A4 | 전면 조건 | 누적 5판 미만/이상에서 결과→타이틀 | 미만 없음, 이상 3판마다 | `ad_impression format=interstitial` |
| A5 | 노출 집계(`onShown`) | 보상형 끝까지·중간 닫기, 전면 1회씩 표시 / A3 오프라인 상태 | 광고가 뜬 횟수만큼만 노출 기록 / 노출 기록 없음 | 표시 1회당 `ad_impression`(format=rewarded·interstitial) **정확히 1회**, 보상형은 그 뒤 `ad_rewarded_end` 1회 / `ad_impression` 0회 |
| A6 | 새 판 초기화 | 1판: 부활·코인 2배 사용 → 재시작해 2판에서 사망·결과 화면 | 2판에서도 부활 창·코인 2배 버튼이 다시 나옴, 같은 판 안에서는 두 번째 부활 없음 | 판마다 `run_start`의 `run_id`가 바뀌고 `ad_offer placement=revive` 1회 |
| P1 | 패스 구매 | always approves | 전면 광고 사라짐, 부활 즉시 | `iap_purchase Success`, `ad_rewarded_pass_skip` |
| P1b | 패스 보유자 횟수 제한 | 패스 보유 상태에서 한 판에 두 번 사망 / 원격 `reviveEnabled` false 후 재실행 | 첫 사망만 즉시 부활, 두 번째는 부활 창 없이 결과 / 부활 창 없음 | 판당 `ad_rewarded_pass_skip placement=revive` 최대 1회 / 0회 |
| P2 | 결제 거절 / 취소 | always declines / 창 닫기 | 소유 없음, 조용히 복귀 | `outcome=Failed` / `Cancelled` |
| P3 | 느린 결제 | Slow test card approves | 대기 안내 → 몇 분 뒤 자동 지급 | `outcome=Pending reason=Deferred` 후 `iap_entitlement` |
| P4 | 확인 전 종료 | 스타터 팩 결제 직후 강제 종료 → 재실행 | 코인 +3,000 **한 번만**, 3분 뒤 환불 메일 없음 | `newly_granted=true` 1회 |
| P5 | 재설치 | 삭제 → 스토어 재설치 | 패스 복원, 스타터 팩 코인 1회 재지급(정책) | `iap_entitlement` |
| P6 | 환불 | Play Console 주문 관리에서 환불 → 재실행 | 패스 해제, 전면 광고 복귀 | `iap_revoked` |
| P7 | 저장 실패 | 개발 빌드에서 세이브 경로를 쓰기 불가로 만들고(또는 저장 실패 강제 플래그) 스타터 팩 구매 → 복구 후 재실행 | 구매 콜백 `Pending`, 저장 실패 안내, 3분 안에 복구·재실행하면 코인 +3,000 한 번만, 환불 메일 없음 | `iap_entitlement_save_failed` → 재실행 후 `iap_entitlement newly_granted=true` 1회 |
| R1 | 킬 스위치 / 원격 실패 | 원격 `interstitialEnabled`·`adFreeSkipsRewardedVideo` false → 재실행 / 이어서 비행기 모드로 재실행 | 전면 없음·상점에서 패스 숨김 / 그 값 유지 | `remote_config origin=Remote` / `Cached`·`Timeout` |
| S1 | 릴리스 안전 / Steam 오염 | 릴리스 AAB, `forceTestAds=false` / Windows 빌드 | 테스트 광고 단위 요청 없음 / 부활·코인 2배·상점 없음 | 기기 로그 / 빌드 리포트에 GoogleMobileAds 네이티브 플러그인 없음 |

P4의 "3분 뒤 환불 메일 없음"은 확인이 스토어에 실제로 도달했다는 증거입니다. 메일이 오면 확인 경로가 깨진 것입니다.

### 10단계: 소프트 론칭 계획서

`Docs/soft-launch-plan.md` — 코인 러시 기준 완성 예시입니다. **수치는 가정이며 실측으로 교체합니다.**

```
목적     수익이 아니라 판단: "모바일 무료판을 계속 운영할 가치가 있는가"
범위     Android, 영어권 1개국 + 한국. 38장 비공개 테스트 요건 통과 후 프로덕션
기간·표본 캠페인 14일 + 관찰 16일, 국가별 설치 ≥ 1,000 (D1 ±3%p 추정에 ≈ 970)
예산     1,000 × 가정 CPI $0.60 ≈ $600. 첫 3일 실측 CPI로 재계산해 $1,200을 넘으면 1개국으로 축소
소재·측정 24장 플레이 영상 15초 2종(코인 흡수 / 제단 선택) · D1·D7, 판당 시간, 사망률, show rate, ad_paid 합계, 패스 구매율, 크래시율(38장)
판정 — 관찰 종료일에 한 번만 (안전 기준만 예외)
  안전 즉시 중단  크래시·ANR이 38장 차단 기준 초과, 결제 지급 오류 1건 이상 → 캠페인 중지, 수정 후 재시작
  Go     D1 ≥ 35% 그리고 D7 ≥ 10% 그리고 실측 LTV30 ≥ 0.5 × CPI → 유료 획득 소액 유지, 스토어 최적화 중심, 3개월 뒤 재판정
  Pivot  D1 25~35% 또는 D7 6~10% → 첫 3판 경험(22장 앞부분)만 고쳐 1회 재측정, 또 Pivot이면 Stop
  Stop   D1 < 25% 또는 D7 < 6% → 유료 획득 종료, 스토어 등록은 유지보수 모드, 시간은 Steam판·다음 작품으로(39장)
기록     결과와 결정을 29장 게이트 기록 양식에. "좋아 보여서 조금 더"는 결정이 아니다.
```

### 확인하기

1. 에디터 Play: 25장과 똑같이 가짜 광고·가짜 스토어로 동작하고, `EntitlementLedgerTests`가 통과합니다.
2. 내부 테스트 트랙으로 설치한 개발 빌드에서 동의 양식(EEA 강제 시) 뒤 "Test Ad" 보상형 광고를 끝까지 보면 부활합니다.
3. 라이선스 테스터로 광고 제거 패스를 사면 결과→타이틀 전면 광고가 사라지고 부활 버튼이 즉시 작동합니다.
4. 스타터 팩 결제 직후 강제 종료 → 재실행하면 코인이 정확히 3,000 늘고, 몇 분이 지나도 자동 환불되지 않습니다.
5. 저장이 실패하도록 만든 상태로 구매하면 코인이 저장되지 않은 채 안내가 뜨고 구매가 확인되지 않으며(P7), 저장을 복구하고 재실행하면 한 번만 지급된 뒤 확인됩니다.
6. 원격에서 두 효용을 끄고 재실행하면 상점에서 패스가 사라지고, 9단계 표의 모든 행이 채워져 있습니다.

## 흔한 실수

1. **증상**: Android 앱이 실행 즉시 종료된다. → **원인**: Google Mobile Ads 설정에 AdMob 앱 ID가 비었거나 EDM4U 의존성 해결을 안 함. → **해결**: `Assets > Google Mobile Ads > Settings`에 앱 ID를 넣고 Force Resolve 후 다시 빌드, 기기 로그(Logcat)에서 원인 메시지를 찾습니다.
2. **증상**: 광고 보상 후 가끔 UI가 갱신되지 않거나 드물게 크래시. → **원인**: 메인 스레드가 아닌 콜백에서 `Time`·UI·`GameObject` 접근. → **해결**: 모든 광고·UMP 콜백 본문을 `MobileAdsEventExecutor.ExecuteInUpdate`로 감쌉니다.
3. **증상**: 테스트 구매가 몇 분 뒤 환불 메일과 함께 사라진다. → **원인**: `ConfirmPurchase` 누락, 또는 지급 중 예외로 확인 줄에 도달하지 못함. → **해결**: 지급 → 저장 → 확인 순서를 지키고 지급 경로가 예외를 던지지 않게 합니다(원장은 순수 함수, `SaveSystem.Save`는 내부에서 예외를 잡음). 라이선스 테스터의 3분 규칙으로 회귀를 잡습니다.
4. **증상**: 스타터 팩 코인이 앱을 켤 때마다 늘어난다. → **원인**: 복원 이벤트마다 지급하는데 원장 확인이 없거나, 원장 필드를 추가하고 세이브 버전을 올리지 않음. → **해결**: 모든 지급은 `EntitlementLedger.TryGrant`만 거치고, 저장 왕복 테스트를 유지합니다.
5. **증상**: 출시 후 "테스트 광고만 보인다"는 리뷰, 또는 개발 중 실제 광고 클릭으로 계정 경고. → **원인**: 테스트 ID 관리를 사람 기억에 맡김. → **해결**: 개발 빌드는 코드가 강제로 테스트 ID(`Debug.isDebugBuild`), 릴리스는 체크리스트 S1로 확인합니다. 신규 앱의 첫날 수익 0은 앱 준비 검토 때문일 수 있습니다.
6. **증상**: 저장 공간이 부족한 기기에서 결제는 됐는데 재실행하면 스타터 팩 코인이 없고, 다시 결제되지도 않는다. → **원인**: `SaveSystem.Save`의 반환값(10장, 실패 시 false)을 무시하고 `ConfirmPurchase`를 불렀거나, 스토어 구현이 이벤트 발행 직후 스스로 확인함. 스토어는 끝난 거래로 기록해 다시 보내지 않습니다. → **해결**: 확인은 수신자가 저장 성공을 확인한 뒤 `ConfirmPurchase(PendingPurchase)`로만 합니다. 실패하면 확인하지 않고 `iap_entitlement_save_failed`를 기록하고 사용자에게 안내합니다. 에디터에서는 `SaveSystem.Save`가 false를 돌려주게 만든 뒤 가짜 스토어로 구매해 구매 콜백이 `Pending`이고 재시작 시 다시 전달되는지 확인합니다.
7. **증상**: 패스 구매자가 "달라진 게 없다"며 환불을 요청한다. → **원인**: 원격 설정으로 효용을 모두 끈 상태에서 계속 판매. → **해결**: `StoreService.RemoveAdsHasValue`로 노출을 코드에서 강제하고 상품 설명을 설정과 함께 관리합니다.

## 연습 문제

**1. ★☆☆ LTV와 회수 기간**
실측 0~6일 활성 일수 합 2.0일, 0~29일 3.2일, ARPDAU(광고) $0.015, 설치당 IAP 순수익 $0.006, CPI $0.35입니다. LTV7·LTV30·ROAS30을 구하고, 10단계 Go 조건의 LTV 기준을 통과하는지 답하세요.

<details><summary>힌트·해설</summary>

IAP가 7일 안에 대부분 일어난다고 가정하면 LTV7 ≈ 2.0 × 0.015 + 0.006 = $0.036, LTV30 ≈ 3.2 × 0.015 + 0.006 = $0.054, ROAS30 ≈ 0.054 ÷ 0.35 ≈ 15%입니다. "LTV30 ≥ 0.5 × CPI"는 0.054 ≥ 0.175이므로 **불통과**입니다. IAP 발생 시점은 `iap_purchase` 이벤트의 설치 후 경과일로 실측해야 합니다. 광고비를 늘리면 손해가 커질 뿐이고, 리텐션 개선 없이는 결론이 바뀌지 않습니다.

</details>

**2. ★★☆ 느린 결제와 버튼 상태**
P3 시나리오에서 `OnPurchaseDeferred`로 `PurchaseOutcome.Pending`을 받은 뒤 플레이어가 상점을 다시 열어 같은 상품을 또 누릅니다. 현재 `UnityIapStoreService`에서 무슨 일이 일어나는지 추적하고, 앱 재시작 후에도 "승인 대기 중"을 보여주도록 개선하세요.

<details><summary>힌트·해설</summary>

`HandleDeferred`의 `Resolve`가 콜백을 지웠으므로 두 번째 `Purchase`는 막히지 않고 `PurchaseProduct`를 다시 부릅니다. 스토어는 `ExistingPurchasePending` 같은 실패를 돌려줄 가능성이 높고, 사용자에게는 "실패"로 보입니다. `HashSet<string> deferred`를 두어 `HandleDeferred`에서 추가하고 `HandlePending`·`HandleFailed`에서 제거합니다. `HandlePurchasesFetched`에서 `orders.DeferredOrders`로 다시 채우면 재시작 후에도 유지됩니다. `IStoreService`에 `bool IsAwaitingApproval(string productId)`를 추가하고 `FakeStoreService`에도 구현해 에디터에서 UI를 확인합니다.

```csharp
    private readonly HashSet<string> deferred = new HashSet<string>();
    public bool IsAwaitingApproval(string productId) => deferred.Contains(productId);
    private void HandleDeferred(DeferredOrder order)
    {
        string id = ProductIdOf(order);
        if (id != null) deferred.Add(id);
        Resolve(id, PurchaseOutcome.Pending);   // 계약에 없는 Deferred 값을 만들지 않는다
    }
    // HandlePending 맨 앞: deferred.Remove(id);  승인되면 PurchasePending → 수신자의 저장 성공 후 ConfirmPurchase
```

같은 `Pending`이라도 "승인 대기"(`IsAwaitingApproval` true)와 "결제됐지만 저장 실패로 확인 보류"(false, `Owns` true)는 안내 문구가 다릅니다. 두 번째 경우는 버튼이 소유 상태로 숨겨지므로 7단계의 `EntitlementSaveFailed` 안내가 사용자에게 보이는 유일한 신호입니다.

</details>

**3. ★★★ 미디에이션으로 교체 (확장 과제)**
DAU가 늘어 LevelPlay 또는 AdMob 미디에이션을 검토합니다. 게임 코드를 바꾸지 않는 교체 작업 목록, 두 구현의 비교 실험 설계, 교체 후 다시 수행할 9단계 행을 **선택한 SDK의 현재 버전 공식 문서**를 근거로 작성하세요.

<details><summary>힌트·해설</summary>

작업: 새 `IAdService` 구현(동의 전달·보상 콜백·메인 스레드·재로드 백오프), 부트스트랩 생성 줄 교체, 스토어 개인정보 양식과 app-ads.txt 갱신. 실험: `MonetizationConfig.adProvider`를 두되 SDK 초기화는 시작 시 한 번 정해지므로 다음 실행부터 적용, 사용자 단위 배정, ARPDAU 주 지표·D1 보호 지표(25장 계획서 형식). 재수행: A1~A6과 S1 전부(새 구현이 `onShown`을 표시 1회당 한 번 부르는지 A5로 확인), 부트스트랩이 바뀌므로 P1·P1b·P4.

</details>

## 셀프 체크

**1. `OnPurchasePending`에서 "지급 → 저장 성공 확인 → 확인" 순서를 지켜야 하는 이유와, 그 결과 반드시 필요해지는 성질은?**

<details><summary>모범 답안</summary>

확인을 먼저 하면 스토어는 거래가 끝났다고 기록하므로, 지급 전에 앱이 죽으면 그 주문이 다시 오지 않아 돈은 나갔는데 보상이 없습니다. 지급을 먼저 하고 세이브에 기록하면, 확인 전에 죽어도 다음 실행의 `FetchPurchases`가 같은 주문을 `PendingOrders`로 다시 줍니다. 저장이 실패한 경우(`SaveSystem.Save`가 false)도 앱이 죽은 것과 같으므로 확인하지 않고 끝내 다음 실행에 다시 받습니다. 그래서 확인은 스토어 구현이 아니라 저장 결과를 아는 수신자가 `ConfirmPurchase`로 부릅니다. 대신 같은 주문이 두 번 처리될 수 있으므로 지급은 멱등해야 하고, 이를 `EntitlementLedger`의 지급 완료 기록으로 보장합니다.

</details>

**2. 25장의 광고 제거 상품이 왜 문제였고 어떻게 고쳤나요? 고친 설계의 경제적 위험은 왜 받아들일 만한가요?**

<details><summary>모범 답안</summary>

전면 광고를 기본으로 끈 채 전면 광고 제거를 팔아 구매자 효용이 없었습니다. 전면 광고를 누적 5판 이후·3판마다·180초 간격으로 켜고, 패스 구매자에게는 전면 광고 제거와 함께 보상형 보상을 시청 없이 즉시 지급하며, 원격 설정으로 두 효용이 모두 꺼지면 상품을 숨기도록 고쳤습니다. 위험은 패스 구매자의 메타 성장이 빨라지는 것이지만, 코인 2배는 1판 1회라 매번 광고를 보는 비구매자와 같은 속도이고, 23장 시뮬레이터로 이미 검토할 수 있는 시나리오입니다.

</details>

**3. 광고 콜백에서 `MobileAdsEventExecutor.ExecuteInUpdate`를 쓰는 이유와, 보상형에서 "닫힘 후 유예 시간"을 두는 이유는?**

<details><summary>모범 답안</summary>

플러그인의 광고 이벤트는 메인 스레드가 아닌 곳에서 올 수 있고 Unity API는 메인 스레드에서만 안전하므로 작업을 다음 Update로 넘깁니다. `RaiseAdEventsOnUnityMainThread`는 obsolete이며 백그라운드 중 이벤트 지연 문제가 있습니다. 보상 신호와 닫힘 신호는 따로 비동기로 전달되어 순서를 믿을 수 없으므로, 닫힘만 보고 즉시 "보상 없음"으로 확정하면 늦게 온 보상을 잃습니다. 그래서 닫힘 후 짧게 기다린 뒤 확정합니다.

</details>

**4. 코인 러시가 서버 영수증 검증 없이 출시해도 된다고 본 근거와, 그 판단이 뒤집히는 조건은?**

<details><summary>모범 답안</summary>

상품이 광고 제거 패스와 스타터 팩뿐인 싱글플레이 게임이라 변조로 공짜로 얻어도 피해가 개발자 매출 일부에 그치고 다른 플레이어에게 번지지 않으며, 서버 운영 비용과 장애 위험이 그 피해보다 큽니다. 소모성 유료 재화, 온라인 랭킹, 플레이어 간 거래·경쟁, 서버에 저장되는 진행 데이터가 생기면 변조가 다른 사용자와 경제 전체에 영향을 주므로 서버 검증이 필요합니다. 소모성 상품은 재설치 시 스토어가 돌려주지 않아 원격 기록도 필요합니다.

</details>

## 핵심 요약

- 모바일 확장은 Steam판 출시 후의 선택 트랙입니다. 계정·검토 대기(Play Console 테스트 요건, AdMob 앱 준비 검토)가 개발보다 길 수 있으니 먼저 엽니다.
- 광고는 AdMob 하나로 시작합니다. UMP 동의 → `CanRequestAds()` → `MobileAds.Initialize` 순서, 콜백은 `ExecuteInUpdate`, 개발 빌드는 코드가 강제로 공식 테스트 광고 단위를 씁니다.
- Unity IAP 5는 `StoreController` 이벤트 기반입니다. 구현은 25장 `IStoreService` 계약대로 `PurchasePending`만 발행하고, 수신자가 **지급 → `SaveSystem.Save` 성공 확인 → `ConfirmPurchase`** 순서를 지킵니다. 저장이 실패하면 확인하지 않고(`Pending`, 사용자 안내, `iap_entitlement_save_failed`) 다음 실행에 재처리하며, 지급은 `EntitlementLedger`로 멱등하게 만듭니다.
- 재설치는 `FetchPurchases`(iOS는 복원 버튼), 환불은 다음 조회에서 소유 해제로 반영합니다. 재설치 시 코인 재지급 같은 정책은 문서로 결정합니다.
- 광고 제거 상품은 실제 효용(전면 광고 제거 + 보상형 즉시 지급)이 있을 때만 노출하고, 설정이 바뀌면 코드가 상품을 숨깁니다.
- Remote Config는 기본값으로 먼저 동작하고 원격 값으로 교체하며, 시간 초과·실패 시 기본값이나 캐시를 씁니다. 비밀은 넣지 않습니다.
- 서버 영수증 검증은 싱글플레이 비소모성 상품에선 생략할 수 있지만 유료 재화·경쟁 요소가 생기면 필수입니다.
- LTV = ARPDAU × 리텐션 곡선 아래 넓이. 소프트 론칭 예산은 표본 크기로 정하고, Go/Pivot/Stop 기준과 판정일을 미리 고정합니다.

## 더 읽을거리

- Unity — IAP 4→5 업그레이드: https://docs.unity.com/en-us/iap/upgrade-to-iap-v5 · SDK로 구매 처리(Pending/Confirmed, 중복 방지): https://docs.unity.com/en-us/iap/payment-providers/purchases-sdk · `StoreController` API 5.3: https://docs.unity3d.com/Packages/com.unity.purchasing@5.3/api/UnityEngine.Purchasing.StoreController.html
- Google Mobile Ads Unity — 설정: https://developers.google.com/admob/unity/quick-start · 보상형: https://developers.google.com/admob/unity/rewarded · 테스트 광고: https://developers.google.com/admob/unity/test-ads · 전역 설정(스레드): https://developers.google.com/admob/unity/global-settings · UMP: https://developers.google.com/admob/unity/privacy · 공식 샘플: https://github.com/googleads/googleads-mobile-unity/tree/main/samples/HelloWorld
- AdMob 도움말 — 앱 준비 검토: https://support.google.com/admob/answer/10564477 · IDFA 설명 메시지: https://support.google.com/admob/answer/10115331
- Unity Remote Config — 코드 통합: https://docs.unity.com/en-us/remote-config/code-integration
- Google Play 결제 테스트(라이선스 테스터, 테스트 결제 수단, 3분 자동 환불): https://developer.android.com/google/play/billing/test · Sandbox Apple 계정: https://developer.apple.com/help/app-store-connect/test-in-app-purchases/create-a-sandbox-apple-account/
