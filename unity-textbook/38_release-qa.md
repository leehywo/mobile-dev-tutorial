# 38. 플랫폼별 출시 품질 검수 — QA 매트릭스·접근성·출시 차단 기준

> **이 장에서 배울 것**
> - 플랫폼×기기×시나리오 축으로 QA 매트릭스를 설계하고, 코인 러시 릴리스 후보(RC) 빌드에 실제로 채울 수 있다
> - Steam Deck 호환성 검토 기준, Google Play 신규 개인 계정의 비공개 테스트 요건, 앱 서명 구조를 공식 문서로 확인하고 검수 항목으로 바꾼다
> - 색에만 의존하지 않는 정보, 글자 크기, 입력 부담, 흔들림·번쩍임 옵션을 **검증 방법까지** 포함한 접근성 체크리스트로 만든다
> - 세이브 손실·업데이트 마이그레이션 시나리오를 EditMode 테스트와 수동 절차로 검증한다
> - 버그 심각도와 우선순위를 구분하고, 예외 없는 출시 차단(블로커) 기준표로 출시 여부를 판정한다
>
> **선수 장**: 08, 10, 11, 16, 19 (모바일 확장 트랙이면 25, 37) · **예상 시간**: 5~7시간 (실기기 검수 시간, Google Play 비공개 테스트 14일 대기 제외) · **코인 러시 진행**: 채워진 QA 매트릭스, 출시 차단 기준표, 패드 연결 해제·절전 복귀 자동 일시정지, QA 오버레이, 글자 크기 감사 도구와 UI 배율 옵션, 세이브 견고성 테스트
>
> **권장 시점**: 26장 전. 26장의 스토어 페이지 문안("Full controller support" 등)을 쓰기 전에 그 약속을 검증할 기준부터 세웁니다. 모바일 무료판을 함께 내면 37장 뒤에 3단계 모바일 행을 추가로 수행합니다.

> ⚠️ 이 장의 플랫폼 기준(Steam Deck 검토 항목, Google Play 테스트 요건·대상 API 수준, Android vitals 임계값, TestFlight 한도)은 2026년 9월에 공식 문서로 확인한 내용이며 바뀔 수 있습니다. 출시 직전에 '더 읽을거리'의 원문을 다시 확인하세요.

## 왜 필요한가

코인 러시 1.0을 Steam에 올린 첫 주를 상상해 봅시다. 에디터와 개발 PC에서는 수십 번 끝까지 플레이했습니다. 그런데 리뷰가 이렇게 달립니다.

```
👎 "Deck에서 절전했다 켰더니 패드가 끊긴 사이 캐릭터가 죽어 있음. 10분 날림" (0.4시간 플레이)
👎 "첫 화면 해상도 팝업이 마우스로만 닫힘. 'Full controller support' 거짓말" (0.1시간)
👎 "1.0.1 업데이트 후 영구 강화 다 날아감" (6.2시간)
👎 "144Hz 모니터에서 적이 두 배 빠름"
```

네 문제 모두 **코드 실력 문제가 아니라 검수 범위 문제**입니다. 개발자는 자기 기기·자기 습관으로만 테스트하므로, 모니터 주사율·절전·연결 해제·이전 버전 세이브처럼 "평소에 하지 않는 행동"은 확인되지 않은 채 출시됩니다. [26장](./26_steam-launch.md)에서 본 것처럼 Steam은 구매 후 14일 이내·플레이 2시간 미만이면 환불을 받아 주므로, 첫 10분에 터지는 문제는 곧바로 환불과 부정 리뷰가 됩니다. [29장](./29_scope-postmortem.md)의 가상 포스트모템에서 Deck Verified를 놓친 원인도 "작은 글씨"와 "첫 실행 시 마우스가 필요한 해상도 팝업"이었습니다.

이 장은 "열심히 테스트한다"를 **재현 가능한 표**로 바꿉니다. 무엇을, 어떤 환경에서, 어떤 절차로 확인하고, 실패하면 출시를 막는지 아닌지를 미리 정해 두면, 출시 직전의 피곤한 머리로 "이 정도면 괜찮겠지"라고 판단하지 않아도 됩니다.

## 개념

### QA는 버그 찾기가 아니라 출시 판정이다

웹 개발에 비유하면 단위 테스트·E2E 테스트는 [10장](./10_save-system.md)·33장의 자동 테스트이고, 이 장의 QA 매트릭스는 **브라우저·기기 호환성 표 + 릴리스 체크리스트**입니다. 자동 테스트가 "코드가 설계대로 동작하는가"를 본다면, 매트릭스는 "**사용자의 실제 환경**에서 **스토어에서 약속한 경험**이 성립하는가"를 봅니다.

매트릭스는 세 축의 곱입니다.

```
        환경 축                  시나리오 축                       판정 축
 ┌──────────────────┐   ┌──────────────────────────┐   ┌────────────────────────┐
 │ Windows 1080p/60 │   │ 첫 실행 → 튜토리얼 → 1판  │   │ PASS / FAIL(버그 ID)    │
 │ Windows 1440p/144│ × │ 메뉴 전부 패드로 조작      │ → │ 실패 시 심각도 P0~P3    │
 │ Steam Deck       │   │ 절전 → 복귀               │   │ 출시 차단 여부          │
 │ Android 저사양   │   │ 1.0 세이브로 1.1 실행      │   └────────────────────────┘
 └──────────────────┘   └──────────────────────────┘
```

모든 칸을 다 채우면 조합이 폭발합니다. 1인 개발자의 원칙은 두 가지입니다.

1. **위험이 큰 조합만 채웁니다.** 세이브 마이그레이션은 모든 플랫폼에서 같은 코드이므로 한 플랫폼에서 깊게, 입력·해상도는 플랫폼마다 얕게.
2. **스토어 약속이 곧 필수 행입니다.** 페이지에 "Full controller support"라고 쓰면 "모든 메뉴 패드 조작"은 선택이 아니라 필수 행이 됩니다.

### 심각도와 우선순위, 그리고 출시 차단

**심각도**(Severity)는 버그가 사용자에게 주는 피해의 크기, **우선순위**(Priority)는 언제 고칠지입니다. 둘은 보통 같이 움직이지만 다를 수 있습니다. 크레딧 화면의 오타는 심각도가 낮지만 폰트 라이선스 표기 누락이면 우선순위가 높습니다([28장](./28_business-law-tax-kr.md) 라이선스 대장).

코인 러시는 우선순위를 네 단계로 씁니다.

| 등급 | 의미 | 출시 판정 | 대표 예 |
|---|---|---|---|
| **P0 출시 차단** | 돈·시간·데이터를 잃거나, 플랫폼 정책·스토어 약속을 어김 | **예외 없이 출시 불가** | 크래시, 진행 불가, 세이브 손실, 결제 보상 누락·중복, 패드로 닫을 수 없는 화면 |
| **P1 출시 전 수정** | 핵심 경험을 뚜렷이 해치지만 우회 가능 | 원칙적으로 수정. 우회책 공지+D+7 패치 계획이 문서화되면 조건부 출시 | 1440p에서 결과 화면 버튼 일부 잘림, 한 무기 설명 넘침 |
| **P2 첫 패치** | 눈에 띄지만 경험을 해치지 않음 | 출시 가능, 1.0.x에 포함 | 드문 조합의 이펙트 겹침, 사운드 누락 1곳 |
| **P3 백로그** | 다듬기·개선 | 출시 가능 | 애니메이션 전환 어색함 |

P0 판정은 **발생 빈도와 무관**합니다. 100판에 한 번 세이브가 날아가도 P0입니다. 그 한 번을 겪은 사람이 6시간짜리 부정 리뷰를 씁니다. 반대로 P1의 "조건부 출시"는 반드시 조건(우회책, 공지 문구, 패치 날짜)을 기록해야 하며, 기록이 없으면 P0처럼 다룹니다.

버그 하나를 등급으로 매길 때는 다음 질문을 순서대로 던집니다.

```
1. 데이터(세이브·구매)가 사라지거나 잘못 지급되는가?     → 예: P0
2. 게임이 멈추거나, 진행할 수 없거나, 종료되는가?         → 예: P0
3. 스토어 페이지/플랫폼 기준이 약속한 것을 어기는가?       → 예: P0
4. 광과민성 등 건강 위험이 있는가?                        → 예: P0
5. 첫 10분(환불 판단 구간) 안에 대부분의 사용자가 보는가?  → 예: P1 이상
6. 나머지                                                  → 영향 범위로 P2/P3
```

### PC(Windows) 검수 기준

Steam 유료판이 1차 출시이므로 PC가 가장 깊은 행을 갖습니다.

| 항목 | 왜 깨지는가 | 확인할 것 |
|---|---|---|
| 해상도·비율 | Canvas Scaler Match 설정([11장](./11_ui.md)), 카메라 크기 | 1920×1080, 2560×1440, 1280×800(16:10), 3440×1440(21:9), 1366×768 |
| 주사율 | 프레임 단위 이동·타이머 코드 | 60Hz와 144Hz에서 적 속도·웨이브 시간·코인 흡수 속도가 같은가 |
| 창 모드 | 전체 화면↔창 전환 시 해상도 저장 | 창 모드, 전체 화면, 경계 없는 창. 재실행 시 설정 유지 |
| 포커스 | Alt+Tab 시 입력·오디오 | Alt+Tab 복귀 후 입력 정상, 판 도중이면 일시정지 |
| 멀티 모니터 | 다른 모니터에서 실행 | 보조 모니터에서 실행해도 창이 화면 밖으로 나가지 않음 |
| 저사양 | [18장](./18_profiling-mobile.md) 기준 | 내장 그래픽 노트북에서 9분대 최대 적 수 구간 프레임 |
| 첫 실행 | 설정 파일·세이브가 없는 상태 | `persistentDataPath` 폴더를 지운 뒤 실행 |

주사율 문제는 `Update`에서 `Time.deltaTime` 없이 값을 더하는 코드가 원인입니다. `QualitySettings.vSyncCount`가 1이면 모니터 주사율에 맞춰 프레임이 돌기 때문에, 60Hz 모니터에서만 테스트하면 절대 발견되지 않습니다.

### Steam Deck 검수 기준 — Valve 공식 항목

[26장](./26_steam-launch.md)에서 Deck 호환성의 네 등급(Verified / Playable / Unsupported / Unknown)과 대략의 검토 영역을 봤습니다. 검수 표로 바꾸려면 **수치**가 필요합니다. 2026년 9월 기준 Steamworks 호환성 문서의 Verified 조건은 다음과 같습니다.

| 영역 | 공식 조건 (요지) | 코인 러시 검수 방법 |
|---|---|---|
| 컨트롤러 지원 | 기본 컨트롤러 설정으로 **모든 콘텐츠**에 접근 가능. 게임 내 설정을 바꾸지 않아도 컨트롤러가 동작 | 설치 직후 마우스·터치 없이 첫 실행→플레이→설정→종료 |
| 컨트롤러 글리프 | 화면의 버튼 표시가 사용 중인 입력과 일치. 컨트롤러 사용 중 키보드·마우스 글리프 표시 금지 | [08장](./08_input-system.md) `ActionPromptLabel`이 모든 화면에서 패드 표시로 바뀌는지 |
| 텍스트 입력 | 텍스트 입력이 필요하면 Steamworks 가상 키보드 API 또는 컨트롤러만으로 입력 가능한 자체 입력 | 코인 러시는 텍스트 입력 없음 → 해당 없음으로 기록 |
| 성능 | 기본 설정에서 플레이 가능한 프레임 — Deck에서는 **800p 30fps** | 기본 품질 설정 그대로 9분대 최대 적 수 구간 측정 |
| 해상도 | Deck이 지원하는 해상도로 실행. 네이티브 **1280×800(권장)** 또는 1280×720 | 첫 실행 해상도가 1280×800인지 QA 오버레이로 확인 |
| 텍스트 가독성 | 1280×800에서 가장 작은 글자 높이가 **9픽셀 미만이 되면 안 됨**. 화면에서 약 30cm 거리에서 읽혀야 함 | 5단계 `TextSizeAudit` + 실기기 30cm 거리 확인 |
| 매끄러움 | 기기 호환성 경고 금지. 런처가 있다면 런처도 같은 조건(컨트롤러 조작 등) | 경고 팝업·런처 없음 확인 |
| Proton | Proton 호환 계층에서 동작해야 함. 차단 버그가 있으면 Unsupported | Windows 빌드를 Deck에서 실행 |

공식 항목에는 없지만 Deck 사용자가 반드시 겪는 행동이 있습니다. Valve의 Deck 권장 사항 문서도 **Steam Cloud로 Deck과 PC 사이에 세이브를 이어 하기**, **그래픽 설정은 기기별로 저장**, **싱글플레이 콘텐츠는 오프라인으로 접근 가능**을 권장합니다. 여기에 휴대 기기 특성인 **절전→복귀**를 더해 코인 러시의 Deck 필수 행으로 둡니다. 절전 복귀는 Verified 조건 목록에 명시돼 있지 않으니 "Verified를 위해"가 아니라 "환불을 막기 위해" 검수합니다.

Deck에서 테스트 빌드를 받는 가장 단순한 방법은 26장의 SteamPipe로 비밀번호가 걸린 베타 브랜치에 올리고, Deck의 게임 속성에서 그 브랜치를 선택하는 것입니다. 스토어에 배포되는 것과 같은 경로를 거치므로 "내 PC에서는 됐는데" 문제를 줄입니다.

> **글자 크기 계산 예**: 11장 Canvas Scaler는 기준 1920×1080, Match 1(높이 기준)입니다. Deck 1280×800에서 배율은 800÷1080 ≈ 0.741입니다. 실제 글자 높이를 폰트 크기의 약 70%로 어림하면(폰트마다 다름) 9픽셀을 넘기려면 기준 해상도에서 폰트 크기가 9 ÷ 0.7 ÷ 0.741 ≈ **17.4 이상**이어야 합니다. 코인 러시는 여유를 두어 **기준 해상도 최소 폰트 크기 24**를 규칙으로 정합니다. 이 70% 근사는 출발점일 뿐이므로 실기기 스크린샷 확대로 최종 확인합니다.

### 모바일 검수 기준 (확장 트랙)

모바일 무료판은 확장 트랙이지만, 한다면 PC와 다른 **행정성 검수**가 추가됩니다. 코드가 완벽해도 이 단계에서 수 주가 걸릴 수 있어 일정에 먼저 넣어야 합니다.

**Android 서명과 실스토어 설치**

| 개념 | 설명 |
|---|---|
| 업로드 키 | 개발자가 보관. AAB에 서명해 Play Console에 올릴 때 신원 확인용. [19장](./19_addressables-build.md)의 키스토어 |
| 앱 서명 키 | Play App Signing에서 Google이 보관. 사용자 기기로 가는 APK를 이 키로 서명 |
| 업로드 키 분실 | 새 업로드 키를 만들어 인증서를 PEM으로 내보낸 뒤 Play Console에서 재설정 요청 가능 |

그래서 "에디터에서 빌드한 APK를 폰에 직접 설치"는 **실스토어 설치 검수가 아닙니다.** 서명 키, 기기별로 생성되는 APK 구성, 스토어가 내려 주는 설치 경로가 모두 다릅니다. 내부 테스트 트랙에 올리고 테스터 계정으로 Play 스토어에서 설치한 빌드로 검수합니다.

**신규 개인 개발자 계정의 테스트 요건**: Play Console 도움말에 따르면 **2023년 11월 13일 이후에 만든 개인 계정**은 프로덕션 접근을 신청하기 전에 **최소 12명의 테스터가 최소 14일 연속으로 참여한 비공개 테스트**를 거쳐야 합니다. 조건을 채운 뒤 대시보드에서 프로덕션 접근을 신청하고 앱·테스트 과정·출시 준비에 관한 질문에 답하며, 검토는 보통 7일 이내지만 더 걸릴 수 있습니다. 즉 **모바일 출시일은 비공개 테스트 시작일 + 14일 + 검토 기간 이후**입니다. 테스터 12명은 [24장](./24_playtest-analytics.md)의 플레이테스트 모집과 합쳐 미리 확보합니다. (조직 계정의 적용 여부, 테스터 수 계산 방식은 도움말 원문으로 확인하세요. 이 요건은 2024년에 20명에서 12명으로 바뀐 적이 있습니다.)

**대상 API 수준**: Android 개발자 문서 기준 **2026년 8월 31일부터 신규 앱과 앱 업데이트는 Android 16(API 36) 이상**을 대상으로 해야 합니다(연장 신청 시 2026년 11월 1일까지). Unity Player Settings의 Target API Level과 설치한 Android SDK가 이 기준을 만족하는지 매년 확인합니다.

**출시 후 품질 임계값**: Android vitals의 나쁜 동작 임계값은 사용자 체감 비정상 종료율 전체 **1.09%**, ANR 비율 전체 **0.47%**(기기 모델별은 각각 8%)이며, 넘으면 스토어 노출이 줄 수 있습니다. 출시 전 검수에서 크래시를 P0로 두는 근거이기도 합니다.

**iOS**: TestFlight 내부 테스터는 팀 구성원 최대 100명, 외부 테스터는 최대 10,000명이며, 외부 테스터에게 배포하려면 첫 빌드가 TestFlight용 App Review를 통과해야 합니다. 빌드의 테스트 가능 기간 등 세부는 App Store Connect 도움말에서 확인합니다.

### 접근성 — "옵션이 있다"가 아니라 "옵션이 동작한다"

[16장](./16_vfx-juice.md)에서 흔들림(0~100%)·번쩍임 끄기·데미지 숫자 끄기 옵션을 넣었습니다. 검수에서는 **옵션을 켜고 끈 상태 각각으로 실제 경험이 달라지는지** 확인합니다. 슬라이더를 0으로 해도 레벨업 슬로모션 줌이 흔들린다면 옵션은 없는 것과 같습니다.

Steam은 개발자가 스토어 페이지에 접근성 기능을 표시할 수 있게 했습니다(Steamworks의 Accessibility Features 문서, 스토어 페이지 Basic Info 탭의 마법사). 필수는 아니지만 표시한다면 그 역시 **스토어 약속**이 되어 필수 검수 행이 됩니다. 문서의 권장 기준 중 코인 러시와 관련된 것은 다음과 같습니다.

| Steam 표시 항목 | 문서의 권장 (요지) | 코인 러시 상태 |
|---|---|---|
| Adjustable Text Size | 1080p에서 최소 38픽셀 높이, 4K에서 76픽셀까지 글자 확대 허용 | 5단계 UI 배율로 대응 후 측정해 판단 |
| Color Alternatives | 중요한 정보를 색만으로 구분하지 않음. 모양·패턴·아이콘·텍스트 병행 | 엘리트 적·코인 종류 검수 필요 |
| Camera Comfort | 화면 효과 강도 조절 또는 끄기 | 16장 흔들림 슬라이더 |
| Custom Volume Controls | 음악·효과음·환경음·음성 볼륨 분리 | [12장](./12_pool-audio.md) 볼륨 슬라이더(항목 구성 확인) |
| Save Anytime | 로딩 중 등을 제외하고 언제든 저장 | 10분 판 중간 저장 없음 → **표시하지 않음** |
| Playable at Your Own Pace | 반응 속도가 핵심이 아니면 시간 제한을 두지 않음 | 서바이버라이크는 반응 기반 → 표시하지 않음. 대신 일시정지는 언제든 가능 |
| Keyboard Only Option | 모든 액션을 키보드에 바인딩 가능 | 08장 리바인딩으로 확인 |

"표시하지 않음"도 결정입니다. 해당하지 않는 항목을 체크하면 그것을 기대하고 산 사용자에게 거짓 약속이 됩니다.

**번쩍임 기준**: 웹 접근성 지침 WCAG 2.2의 성공 기준 2.3.1은 **1초에 3번 넘게 번쩍이지 않거나, 번쩍임이 일반 번쩍임·적색 번쩍임 임계값 아래**일 것을 요구합니다. 게임에 법적으로 적용되는 기준은 아니지만 측정 가능한 출발점입니다. 코인 러시에서 위험한 곳은 보스 등장 연출, 다수 적 동시 피격 번쩍임, 레벨업 섬광입니다. 1초에 3회 넘게 **큰 면적**이 밝기를 크게 바꾸는 장면은 번쩍임 옵션과 무관하게 P0로 고치고, 옵션은 그 밖의 작은 번쩍임을 끄는 용도로 씁니다. 판단이 애매하면 해당 장면을 녹화해 프레임 단위로 세어 봅니다.

**입력 부담**: 코인 러시는 이동만 하는 게임이라 입력 부담이 낮은 편입니다. 그래도 "버튼 연타 요구 없음", "길게 누르기가 필요한 곳 없음", "한 손(왼쪽 스틱 또는 WASD)만으로 메뉴 포함 전체 진행 가능 여부"를 기록합니다. 한 손 진행이 가능하면 그 사실이 곧 접근성 강점이고, 불가능하면 어디서 막히는지가 개선 목록이 됩니다.

### 세이브 손실과 업데이트 마이그레이션

10장에서 원자적 저장, 백업, 해시, 마이그레이션 체인을 만들었습니다. 검수는 **실패를 일부러 일으켜** 이 장치가 실제로 일하는지 봅니다.

| 시나리오 | 일으키는 방법 | 기대 결과 |
|---|---|---|
| 저장 중 강제 종료 | 판 종료 결과 화면 직후 작업 관리자로 종료(PC), 앱 강제 종료(모바일) | 재실행 시 직전 또는 그 전 저장 상태. 새 게임으로 초기화되지 않음 |
| 본 파일 손상 | `save.json` 중간을 잘라냄 | 경고 로그 + 백업에서 복구 |
| 이전 버전 세이브 | 출시한 모든 버전의 세이브 샘플로 새 빌드 실행 | 코인·강화·통계 유지, 저장 후 `version`이 현재 값 |
| 미래 버전 세이브 | 베타 브랜치(새 버전)에서 저장 후 default 브랜치(구 버전)로 되돌림 | 구 버전이 파일을 덮어쓰지 않음(10장 `writeBlocked`) |
| 클라우드 충돌 | PC에서 저장→오프라인 Deck에서 저장→둘 다 온라인 | Steam Cloud 충돌 창이 뜨고, 어느 쪽을 골라도 파일이 읽힘 |
| 디스크 공간 부족 | 가상 드라이브 등으로 재현 어려움 → 코드 리뷰로 대체 | 예외가 기록되고 게임이 멈추지 않음(10장 `Save`의 catch) |
| 구매 보상 재지급 (모바일) | 스타터 팩 구매 후 재설치·복원 | 코인이 두 번 들어오지 않음, 캐릭터 해금은 복원 (25·37장) |

"미래 버전 세이브" 행은 **핫픽스 롤백**과 직결됩니다. 1.1에서 문제가 생겨 Steam default 브랜치를 1.0 빌드로 되돌리면, 이미 1.1로 저장한 사용자는 1.0이 모르는 v3 세이브를 갖게 됩니다. 10장의 쓰기 차단이 없으면 1.0이 기본값으로 덮어써 전원의 진행이 사라집니다. 롤백 절차 자체는 33장에서 다룹니다.

### 스모크 테스트 — 빌드마다 15분

매트릭스 전체는 RC 빌드에만 돌리고, **모든 빌드**에는 15분짜리 스모크 경로를 돌립니다. 빌드가 "켜지고, 한 판 돌고, 저장되는가"만 보는 최소 경로입니다. 이 경로에서 실패하면 매트릭스를 돌릴 가치가 없으므로 곧바로 반려합니다.

```
[스모크 15분]  세이브 폴더 삭제 → 실행 → 타이틀(패드로 조작) → 1판 3분 → 레벨업 3회
              → 일부러 사망 → 결과 → 강화 1회 구매 → 종료 → 재실행 → 코인·강화 유지 확인
```

## 실습: 코인 러시에 적용하기

모든 문서는 `Docs/qa/`에, 코드는 `Assets/_CoinRush/Scripts/QA/`에 둡니다. 예시의 빌드 번호·결과는 실제로 채운 형태를 보여 주기 위한 **가상 기록**입니다.

### 1단계: 테스트 환경 목록 만들기

`Docs/qa/devices.md`를 만듭니다. 가진 기기, 빌려 쓸 기기, 확보하지 못한 기기를 구분해 **확보 못 한 환경은 위험으로 명시**합니다.

| ID | 환경 | 사양·설정 | 확보 | 비고 |
|---|---|---|---|---|
| E1 | 개발 PC | Windows 11, RTX급 GPU, 2560×1440 **144Hz** | 보유 | 주사율 테스트 겸용 |
| E2 | 노트북 | Windows 11, 내장 그래픽, 1920×1080 60Hz | 보유 | 저사양 기준 |
| E3 | Steam Deck | LCD 또는 OLED 모델, SteamOS 안정 채널 | 보유(중고 구매, 28장 장비 대장) | 베타 브랜치 설치 |
| E4 | 게임패드 A | Xbox 무선 컨트롤러 (USB·블루투스) | 보유 | 연결 해제 테스트 |
| E5 | 게임패드 B | PlayStation 계열 컨트롤러 | 지인 대여 | 글리프 확인 |
| E6 | 울트라와이드 | 3440×1440 | **미확보** | Game 뷰 해상도로 대체, 위험 기록 |
| M1 | Android 저사양 | 18장 기준 저사양 폰 | 보유 | 모바일 트랙만 |
| M2 | iPhone | 노치·다이내믹 아일랜드 모델 | 지인 대여 | 모바일 트랙만 |

### 2단계: 코인 러시 QA 매트릭스 완성본

`Docs/qa/matrix-1.0.0-rc1.md`입니다. 한 줄은 "누가 해도 같은 결과가 나오게" 씁니다. 절차가 "잘 되는지 확인"이면 실패한 행입니다. 21장 기획 기준(맵 1, 일반 적 4종+엘리트 1+보스 1, 무기 6, 패시브 10, 캐릭터 3)을 전수 행에 반영합니다.

**PC·공통**

| ID | 환경 | 절차 | 기대 결과 | 실패 시 | RC1 |
|---|---|---|---|---|---|
| PC-01 | E2 | 세이브 폴더 삭제 후 첫 실행 | 해상도 팝업·경고 없이 타이틀까지 10초 이내 | P0 | PASS |
| PC-02 | E1 144Hz, E2 60Hz | 같은 시드로 3분 플레이, 3분 시점 적 수·플레이어 이동 거리 비교 | 두 환경 차이 5% 이내 | P0 | **FAIL #41** |
| PC-03 | E1 | 창 모드↔전체 화면 전환 후 재실행 | 마지막 설정 유지 | P1 | PASS |
| PC-04 | Game 뷰 1280×800, 3440×1440, 1366×768 | HUD·레벨업·결과·설정 화면 캡처 | 잘림·겹침 없음, 버튼 전부 보임 | P1 | **FAIL #42** (3440 결과 화면 좌우 버튼이 가장자리) |
| PC-05 | E1 | 판 도중 Alt+Tab 후 복귀 | 자동 일시정지, 복귀 후 입력 정상 | P1 | PASS (3단계 적용 후) |
| PC-06 | E2 | 9분대 최대 적 수 구간 프로파일링(18장) | 기본 품질에서 평균 60fps, 1% 저점 45fps 이상 | P1 | PASS |
| PC-07 | E1 | 보조 모니터로 창을 옮긴 뒤 종료→재실행 | 창이 화면 안에 표시 | P2 | PASS |
| PC-08 | 전 환경 | 스모크 15분 경로 | 전 단계 통과 | P0 | PASS |
| PC-09 | E1 | 무기 6종·패시브 10종 카드 각각 1회 이상 선택(디버그 강제 드롭) | 설명 문구 넘침 없음, 효과 적용 로그 | P1 | PASS |
| PC-10 | E1 | 캐릭터 3종으로 각 1판 클리어 시도(디버그 무적) | 10분 클리어→보스→결과까지 진행 | P0 | PASS |

**패드·Steam Deck**

| ID | 환경 | 절차 | 기대 결과 | 실패 시 | RC1 |
|---|---|---|---|---|---|
| PAD-01 | E1+E4 | 마우스를 뽑고 첫 실행→설정의 모든 항목 변경→리바인딩→종료 | 모든 화면에 포커스 표시, 막히는 화면 없음 | P0 | PASS |
| PAD-02 | E1+E4 | 모든 팝업(레벨업·일시정지·결과·확인 창) 열 때 첫 선택 확인 | 팝업마다 선택된 버튼 존재(11장 `SetSelectedGameObject`) | P0 | **FAIL #43** (강화 구매 확인 창) |
| PAD-03 | E1+E4 | 판 도중 무선 패드 전원 끄기 | 즉시 일시정지, 재연결 후 계속 가능 | P1 | PASS (3단계) |
| PAD-04 | E1+E4, E5 | 키보드 입력 후 패드 입력 | 안내 문구가 패드 글리프로 전환, 반대도 동일 | P1 | PASS |
| PAD-05 | E5 | PlayStation 계열 패드로 메뉴 조작 | 조작 가능. 글리프가 Xbox 표기라면 기록 | P2 | 조작 PASS, 글리프는 Xbox 표기(P2 #44) |
| DK-01 | E3 | 베타 브랜치 설치 후 첫 실행 | 1280×800, 호환성 경고·런처 없음 | P0 | PASS |
| DK-02 | E3 | 첫 실행→1판→설정→종료를 터치·트랙패드 없이 | 전 과정 버튼만으로 가능 | P0 | PASS |
| DK-03 | E3 | 레벨업 창에서 30cm 거리로 무기 설명 읽기 + `TextSizeAudit` | 가장 작은 글자 9px 이상, 읽힘 | P0 | **FAIL #45** (패시브 수치 보조 텍스트 7px 추정) |
| DK-04 | E3 | 9분대 기본 설정 프레임 | 30fps 이상 유지 | P0 | PASS (평균 52) |
| DK-05 | E3 | 판 도중 전원 버튼으로 절전→5분 뒤 복귀 | 일시정지 상태로 복귀, 캐릭터 생존 | P1 | PASS (3단계) |
| DK-06 | E3 | 비행기 모드에서 실행→1판→종료 | 정상 플레이·저장 | P0 | PASS |
| DK-07 | E1↔E3 | PC에서 강화 구매→Deck에서 실행 | 강화 반영(26장 Auto-Cloud) | P1 | PASS |
| DK-08 | E3 | 그래픽 설정 변경 후 PC 실행 | PC 그래픽 설정은 영향받지 않음 | P2 | **FAIL #46** (품질 설정도 세이브에 포함) |

**접근성**

| ID | 절차 | 기대 결과 | 실패 시 | RC1 |
|---|---|---|---|---|
| A11Y-01 | 흔들림 0%로 보스 등장·플레이어 피격·레벨업 슬로모션 확인 | 카메라 흔들림 전혀 없음 | P1 | PASS |
| A11Y-02 | 번쩍임 끄기로 적 20마리 동시 피격 | 스프라이트 번쩍임 없음(대체 표현: 넉백·파티클) | P1 | PASS |
| A11Y-03 | 옵션과 무관하게 보스 등장·레벨업 섬광 녹화, 1초 구간 밝기 변화 횟수 세기 | 큰 면적 번쩍임 1초 3회 이하 | P0 | PASS |
| A11Y-04 | 흑백(그레이스케일) 필터로 1판 — OS 색 필터 기능 또는 캡처 후 흑백 변환 | 엘리트 적·체력 낮음 경고·코인 종류가 색 외 요소로 구분 | P1 | **FAIL #47** (엘리트가 색만 다름) |
| A11Y-05 | UI 배율 150%로 레벨업·결과·설정 화면 | 넘침·겹침 없음 | P1 | PASS |
| A11Y-06 | 음악 0 / 효과음 100, 반대로도 | 각각 독립 적용, 재실행 후 유지 | P2 | PASS |
| A11Y-07 | WASD(또는 왼쪽 스틱)+확인 버튼만으로 타이틀→1판→결과→강화 | 한 손 진행 가능 여부 기록 | 기록만 | 가능 |
| A11Y-08 | 일시정지를 판 중 아무 때나 10회 | 매번 즉시 멈춤, 레벨업 창과 겹쳐도 정상 | P1 | PASS |

**세이브·업데이트**

| ID | 절차 | 기대 결과 | 실패 시 | RC1 |
|---|---|---|---|---|
| SAVE-01 | 6단계 EditMode 테스트 전체 | 전부 통과 | P0 | PASS |
| SAVE-02 | 결과 화면 표시 직후 프로세스 강제 종료 ×5회 | 매번 이전 또는 직전 상태 유지 | P0 | PASS |
| SAVE-03 | `SaveFixtures/`의 1.0 세이브를 RC 빌드 폴더에 넣고 실행 | 코인·강화·통계 유지 | P0 | PASS |
| SAVE-04 | 베타 브랜치 빌드로 저장 → default 브랜치(이전 빌드)로 실행 → 강화 구매 | 구 빌드가 파일을 덮어쓰지 않음, 복귀 후 진행 유지 | P0 | PASS |
| SAVE-05 | PC 오프라인 저장, Deck 오프라인 저장 후 둘 다 온라인 | 충돌 선택 후 선택한 쪽 정상 로드 | P1 | 미실시(Deck 네트워크 문제) → **RC2에서 재실시** |

**모바일 확장 트랙** (37장 이후)

| ID | 절차 | 기대 결과 | 실패 시 |
|---|---|---|---|
| MOB-01 | 내부 테스트 트랙에 AAB 업로드 → 테스터 계정으로 Play 스토어에서 설치 | 설치·실행 정상, 서명 오류 없음 | P0 |
| MOB-02 | 비공개 테스트 시작일·테스터 수 기록 | 12명 이상이 14일 연속 참여 상태로 신청 | 출시 일정 차단 |
| MOB-03 | 판 도중 홈 버튼→다른 앱 10분→복귀 | 일시정지 상태 복귀, 저장 유지 | P1 |
| MOB-04 | 노치 기기 가로 양방향 회전 | HUD가 Safe Area 안(11장) | P1 |
| MOB-05 | 테스트 구매→앱 삭제→재설치→복원 | 비소모성 복원, 코인 중복 지급 없음 | P0 |
| MOB-06 | 테스트 광고로 부활 보상: 끝까지/중간 닫기/비행기 모드 | 끝까지 볼 때만 보상, 실패 시 조용히 숨김 | P0 |
| MOB-07 | Play Console 사전 출시 보고서 확인 | 크래시·ANR 없음 | P0 |

행 수가 많아 보이지만 한 번 만들어 두면 RC마다 "결과" 열만 새로 채웁니다. RC1에서 FAIL이 난 행은 버그 ID를 적고, 수정 빌드(RC2)에서 **그 행과 관련 행만이 아니라 스모크와 P0 행 전체**를 다시 돌립니다. 한 버그를 고치다 다른 곳이 깨지는 회귀가 흔하기 때문입니다.

### 3단계: 패드 연결 해제·포커스 상실·절전 복귀 자동 일시정지

PAD-03, PC-05, DK-05를 통과시키는 컴포넌트입니다. [08장](./08_input-system.md)의 `PauseController.Pause()`와 `InputDeviceWatcher.Current`, [24장](./24_playtest-analytics.md)의 `Analytics.Track`을 재사용합니다.

절전 복귀는 어떤 Unity 콜백이 오는지 플랫폼마다 다를 수 있고, `Time.realtimeSinceStartup` 같은 단조 시계는 OS에 따라 절전 시간을 포함하지 않을 수 있습니다. 그래서 **벽시계(`DateTime.UtcNow`)로 프레임 사이 간격을 재서** 수 초 이상 끊겼으면 일시정지하는 방식으로 콜백에 의존하지 않습니다. 사용자가 시스템 시계를 바꾸면 한 번 일시정지되는 부작용이 있지만 무해합니다.

```csharp
// Assets/_CoinRush/Scripts/QA/InputLossPauser.cs
using System;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// 판 도중 입력을 잃을 수 있는 순간(패드 연결 해제, 창 포커스 상실, 절전 복귀)에 자동으로 일시정지한다.
/// Game 씬의 PauseController와 같은 오브젝트에 둔다.
/// </summary>
public class InputLossPauser : MonoBehaviour
{
    [SerializeField] private PauseController pauseController;   // 08장
    [SerializeField] private double suspendGapSeconds = 2.0;     // 이보다 긴 프레임 간격은 절전·중단으로 간주

    private DateTime lastFrameUtc;

    private void OnEnable()
    {
        InputSystem.onDeviceChange += OnDeviceChange;
        lastFrameUtc = DateTime.UtcNow;
    }

    private void OnDisable()
    {
        InputSystem.onDeviceChange -= OnDeviceChange;
    }

    private void OnDeviceChange(InputDevice device, InputDeviceChange change)
    {
        if (change != InputDeviceChange.Disconnected) return;
        if (device is not Gamepad) return;
        // 키보드로 플레이하던 중에 놀고 있던 패드가 꺼진 경우는 무시
        if (InputDeviceWatcher.Current != InputDeviceKind.Gamepad) return;
        PauseForSafety("gamepad_disconnected");
    }

    private void OnApplicationFocus(bool hasFocus)
    {
        if (!hasFocus) PauseForSafety("focus_lost");
    }

    private void Update()
    {
        DateTime now = DateTime.UtcNow;
        if ((now - lastFrameUtc).TotalSeconds > suspendGapSeconds)
            PauseForSafety("resume_gap");
        lastFrameUtc = now;
    }

    private void PauseForSafety(string reason)
    {
        if (pauseController == null || pauseController.IsPaused) return;
        // 레벨업 창·부활 창처럼 이미 멈춘 화면 위에 일시정지를 겹치지 않는다.
        // (16장 히트 스톱 중 0.05초 동안은 건너뛰는 단순화가 있다)
        if (Time.timeScale == 0f) return;

        pauseController.Pause();
        Analytics.Track("auto_pause", ("reason", reason));
    }
}
```

에디터 작업:

1. Game 씬의 `Controls` 오브젝트(08장 `PauseController`가 붙은 곳)에 `InputLossPauser`를 추가하고 `Pause Controller`를 연결합니다.
2. 에디터에서는 Game 뷰 밖을 클릭하면 `focus_lost`로 일시정지됩니다. 의도한 동작이지만 디버깅이 불편하면 `Run In Background`와 무관하게 이 컴포넌트를 잠시 끕니다.
3. 레벨업 창이 열려 있는 동안(timeScale 0) 패드가 끊기면 일시정지는 걸리지 않지만 게임도 이미 멈춰 있으므로 안전합니다. 재연결 후 레벨업 카드 선택이 되는지 PAD-03 절차에 "레벨업 창에서 끊기" 변형을 추가합니다.

`auto_pause` 이벤트는 출시 후에도 유용합니다. 24장 로그에서 `resume_gap` 비율이 높으면 휴대 기기 사용자가 많다는 신호입니다.

### 4단계: QA 오버레이 — 스크린샷 한 장에 환경 정보 담기

버그 제보 스크린샷에 "어떤 빌드, 어떤 해상도, 어떤 입력"이 함께 찍히면 재현 시간이 크게 줄어듭니다. 개발 빌드에서만 보이는 오버레이입니다. `Debug.isDebugBuild`는 에디터와 Development Build에서 true이므로 릴리스 빌드에서는 스스로 사라집니다.

```csharp
// Assets/_CoinRush/Scripts/QA/QaOverlay.cs
using System;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>개발 빌드 전용 환경 정보 표시. F1 또는 패드 L3를 누른 채 R3로 토글.</summary>
public class QaOverlay : MonoBehaviour
{
    [SerializeField] private bool visible = true;

    private float fpsSmoothed;
    private GUIStyle style;

    private void Awake()
    {
        if (!Debug.isDebugBuild) { Destroy(gameObject); return; }
        DontDestroyOnLoad(gameObject);
    }

    private void Update()
    {
        float dt = Time.unscaledDeltaTime;
        if (dt > 0f) fpsSmoothed = Mathf.Lerp(fpsSmoothed, 1f / dt, 0.1f);

        if (Keyboard.current != null && Keyboard.current.f1Key.wasPressedThisFrame) visible = !visible;
        Gamepad pad = Gamepad.current;
        if (pad != null && pad.leftStickButton.isPressed && pad.rightStickButton.wasPressedThisFrame) visible = !visible;
    }

    private void OnGUI()
    {
        if (!visible) return;
        // 1280×800에서도 읽히도록 화면 높이에 비례한 글자 크기
        style ??= new GUIStyle(GUI.skin.label) { fontSize = Mathf.Max(14, Screen.height / 45) };

        SaveData save = SaveSystem.Load();   // 10장. 캐시된 인스턴스를 돌려준다
        string text =
            $"CoinRush v{Application.version} | {SystemInfo.operatingSystem}\n" +
            $"{Screen.width}x{Screen.height} {Screen.fullScreenMode} " +
            $"@{Screen.currentResolution.refreshRateRatio.value:0.#}Hz vSync={QualitySettings.vSyncCount} target={Application.targetFrameRate}\n" +
            $"FPS {fpsSmoothed:0} | input {InputDeviceWatcher.Current} | pads {Gamepad.all.Count} | timeScale {Time.timeScale:0.##}\n" +
            $"save v{save.version} coins {save.coins} | {DateTime.Now:yyyy-MM-dd HH:mm:ss}";

        GUI.Label(new Rect(8, 8, Screen.width - 16, style.fontSize * 6), text, style);
    }
}
```

1. 09장 부트스트랩 씬에 빈 오브젝트 `QaOverlay`를 만들고 컴포넌트를 붙입니다.
2. [19장](./19_addressables-build.md) `BuildScripts`의 QA용 빌드는 Development Build 옵션을 켜고, 스토어 업로드용 빌드는 끕니다. **릴리스 빌드에서 오버레이가 보이면 P0**입니다(매트릭스 PC-08 스모크에 "릴리스 빌드에 오버레이 없음" 확인을 넣습니다).

`Screen.currentResolution`은 창 모드에서 데스크톱 해상도를 돌려주므로, 창 크기는 `Screen.width/height`로 따로 표시했습니다.

### 5단계: 글자 크기 감사 도구와 UI 배율 옵션

DK-03을 사람 눈만으로 판정하면 매번 결과가 달라집니다. 현재 화면의 모든 TextMeshPro 텍스트가 1280×800 기준으로 몇 픽셀인지 **어림해** 목록을 뽑는 도구입니다.

```csharp
// Assets/_CoinRush/Scripts/QA/TextSizeAudit.cs
using TMPro;
using UnityEngine;

/// <summary>
/// Screen Space Overlay 캔버스의 TMP 텍스트 높이를 1280×800 기준 픽셀로 어림해 기준 미달을 로그로 남긴다.
/// 검사할 화면(레벨업 창 등)을 띄운 상태에서 컴포넌트 메뉴 "Audit Now" 실행.
/// </summary>
public class TextSizeAudit : MonoBehaviour
{
    [SerializeField] private float minGlyphPixelsAt800p = 9f;     // Steam Deck 호환성 문서의 최소 글자 높이
    [Tooltip("폰트 크기 대비 실제 글자 높이 비율의 근사값. 사용하는 폰트로 스크린샷을 재서 조정")]
    [SerializeField, Range(0.5f, 1f)] private float glyphHeightRatio = 0.7f;

    [ContextMenu("Audit Now")]
    public void AuditNow()
    {
        float toDeck = 800f / Screen.height;   // 현재 해상도 픽셀 → 800p 픽셀
        TMP_Text[] texts = FindObjectsByType<TMP_Text>(FindObjectsSortMode.None);
        int checkedCount = 0, failCount = 0;

        foreach (TMP_Text t in texts)
        {
            if (!t.isActiveAndEnabled || string.IsNullOrWhiteSpace(t.text)) continue;
            Canvas canvas = t.canvas;
            if (canvas == null || canvas.rootCanvas.renderMode != RenderMode.ScreenSpaceOverlay)
            {
                Debug.LogWarning($"[TextAudit] 건너뜀(Overlay 캔버스 아님): {PathOf(t.transform)}", t);
                continue;
            }

            // 자동 크기 조절이면 가장 작아질 수 있는 크기로 판정
            float fontSize = t.enableAutoSizing ? t.fontSizeMin : t.fontSize;
            // Overlay 캔버스의 lossyScale에는 Canvas Scaler 배율과 부모 스케일이 모두 들어 있다
            float screenPixels = fontSize * glyphHeightRatio * t.transform.lossyScale.y;
            float deckPixels = screenPixels * toDeck;

            checkedCount++;
            if (deckPixels < minGlyphPixelsAt800p)
            {
                failCount++;
                Debug.LogError($"[TextAudit] {deckPixels:0.0}px < {minGlyphPixelsAt800p}px : {PathOf(t.transform)} \"{Shorten(t.text)}\"", t);
            }
        }
        Debug.Log($"[TextAudit] 검사 {checkedCount}개, 기준 미달 {failCount}개 (화면 {Screen.width}x{Screen.height})");
    }

    private static string PathOf(Transform tr)
    {
        string path = tr.name;
        for (Transform p = tr.parent; p != null; p = p.parent) path = p.name + "/" + path;
        return path;
    }

    private static string Shorten(string s) => s.Length <= 20 ? s : s.Substring(0, 20) + "…";
}
```

사용법:

1. 부트스트랩 씬 `QaOverlay` 오브젝트에 함께 붙입니다.
2. Game 뷰 해상도를 1280×800으로 두고 Play → 레벨업 창을 띄운 채 일시정지 → Inspector에서 컴포넌트 톱니 메뉴 **Audit Now**.
3. 11장 `ButtonPunch`처럼 스케일 애니메이션 중이면 값이 흔들리니 정지 상태에서 실행합니다.
4. 비율 0.7은 근사입니다. Pretendard 기준으로 한 번 스크린샷을 찍어 "가" 글자 높이를 픽셀로 재고 `glyphHeightRatio`를 맞춥니다.

RC1의 #45는 패시브 카드의 보조 수치 텍스트(자동 크기 조절, `Font Size Min` 12)가 원인이었습니다. 수정은 보조 텍스트의 최소 크기를 24로 올리고, 넘치는 설명은 두 줄 허용으로 바꾸는 것입니다.

다음은 **UI 배율 옵션**입니다. 11장 Canvas Scaler(Scale With Screen Size, 기준 1920×1080)의 기준 해상도를 줄이면 같은 화면에서 UI 전체가 커집니다. 글자만 키우는 방식보다 레이아웃 붕괴가 적어 1인 개발에 맞는 첫 단계입니다.

```csharp
// Assets/_CoinRush/Scripts/UI/UiScaleSetting.cs
using System;
using UnityEngine;
using UnityEngine.UI;

/// <summary>UI 배율(100~150%). 각 Canvas의 CanvasScaler 옆에 붙인다.</summary>
[RequireComponent(typeof(CanvasScaler))]
public class UiScaleSetting : MonoBehaviour
{
    public const string PrefsKey = "ui.scale";
    public const float MinScale = 1f;
    public const float MaxScale = 1.5f;
    private static readonly Vector2 BaseReference = new Vector2(1920f, 1080f);   // 11장 기준 해상도

    public static event Action Changed;

    public static float Scale
    {
        get => Mathf.Clamp(PlayerPrefs.GetFloat(PrefsKey, 1f), MinScale, MaxScale);
        set
        {
            PlayerPrefs.SetFloat(PrefsKey, Mathf.Clamp(value, MinScale, MaxScale));
            Changed?.Invoke();
        }
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStatics() => Changed = null;   // 도메인 리로드를 꺼도 안전하게

    private CanvasScaler scaler;

    private void Awake() => scaler = GetComponent<CanvasScaler>();

    private void OnEnable()
    {
        Changed += Apply;
        Apply();
    }

    private void OnDisable() => Changed -= Apply;

    private void Apply()
    {
        // 기준 해상도가 작을수록 같은 화면에서 UI가 크게 그려진다
        scaler.referenceResolution = BaseReference / Scale;
    }
}
```

설정 화면에는 16장 접근성 옵션 옆에 슬라이더(Min 1, Max 1.5)를 두고 `onValueChanged`에서 `UiScaleSetting.Scale = v;`, 화면을 닫을 때 `PlayerPrefs.Save()`를 호출합니다. HUD·레벨업·결과·설정 Canvas 모두에 컴포넌트를 붙여야 하며, 하나라도 빠지면 A11Y-05에서 드러납니다.

배율 옵션을 넣었다고 Steam의 **Adjustable Text Size**를 바로 표시하지는 않습니다. 150%에서 본문 텍스트의 1080p 픽셀 높이를 재고, Steam 문서의 기준(1080p에서 최소 38픽셀)과 측정 방식을 원문으로 대조한 뒤 결정합니다. 기준에 못 미치면 표시하지 않고 옵션만 제공합니다.

### 6단계: 세이브 견고성 EditMode 테스트

10장 테스트 어셈블리 `CoinRush.Tests.EditMode`에 파일을 추가합니다. `SaveSystem`은 Unity API를 쓰는 기본 어셈블리에 있어 테스트가 참조할 수 없으므로, 그 안의 **재료(`SaveFileStore`, `SaveSerializer`, `SaveMigrator`)가 손상·백업·미래 버전 상황에서 올바른 신호를 내는지**를 검사합니다. 폴백 순서 자체는 매트릭스의 수동 절차(SAVE-02~04)로 확인합니다.

먼저 **세이브 샘플 보관 규칙**을 정합니다. 출시한 버전마다 실제 빌드로 만든 세이브 파일을 `Assets/_CoinRush/Tests/EditMode/SaveFixtures/`에 `save_1.0.0.json`, `save_1.1.0.json`처럼 추가하고 **절대 수정하지 않습니다.** 10장 5단계의 `save_v1_sample.json`이 첫 샘플입니다.

```csharp
// Assets/_CoinRush/Tests/EditMode/SaveRobustnessTests.cs
using System;
using System.IO;
using Newtonsoft.Json;
using NUnit.Framework;
using UnityEngine;

public class SaveRobustnessTests
{
    private string dir;

    [SetUp]
    public void SetUp()
    {
        dir = Path.Combine(Path.GetTempPath(), "coinrush-save-tests-" + Guid.NewGuid().ToString("N"));
    }

    [TearDown]
    public void TearDown()
    {
        if (Directory.Exists(dir)) Directory.Delete(dir, recursive: true);
    }

    [Test]
    public void Second_Write_Keeps_Previous_As_Backup()
    {
        var store = new SaveFileStore(dir);
        store.WriteAtomic(SaveSerializer.Serialize(new SaveData { coins = 100 }));
        store.WriteAtomic(SaveSerializer.Serialize(new SaveData { coins = 200 }));

        SaveData main = SaveSerializer.Deserialize(store.ReadMainOrNull(), out _);
        SaveData backup = SaveSerializer.Deserialize(store.ReadBackupOrNull(), out _);
        Assert.AreEqual(200, main.coins);
        Assert.AreEqual(100, backup.coins);
        Assert.IsFalse(File.Exists(store.MainPath + ".tmp"), "임시 파일이 남으면 안 됩니다.");
    }

    [Test]
    public void Truncated_Main_Fails_To_Parse_But_Backup_Is_Readable()
    {
        var store = new SaveFileStore(dir);
        store.WriteAtomic(SaveSerializer.Serialize(new SaveData { coins = 100 }));
        store.WriteAtomic(SaveSerializer.Serialize(new SaveData { coins = 200 }));

        // 저장 도중 전원이 나간 상황 흉내: 본 파일을 절반만 남김
        string full = File.ReadAllText(store.MainPath);
        File.WriteAllText(store.MainPath, full.Substring(0, full.Length / 2));

        Assert.That(() => SaveSerializer.Deserialize(store.ReadMainOrNull(), out _),
            Throws.InstanceOf<JsonException>());
        SaveData recovered = SaveSerializer.Deserialize(store.ReadBackupOrNull(), out SaveReadStatus status);
        Assert.AreEqual(SaveReadStatus.Ok, status);
        Assert.AreEqual(100, recovered.coins);
    }

    [Test]
    public void Future_Version_Is_Rejected_Not_Silently_Reset()
    {
        string json = SaveSerializer.Serialize(new SaveData { version = SaveData.CurrentVersion + 1, coins = 999 });
        Assert.Throws<FutureSaveVersionException>(() => SaveSerializer.Deserialize(json, out _));
    }

    [Test]
    public void Every_Released_Save_Fixture_Loads_To_Current_Version()
    {
        string fixtures = Path.Combine(Application.dataPath, "_CoinRush/Tests/EditMode/SaveFixtures");
        string[] files = Directory.Exists(fixtures) ? Directory.GetFiles(fixtures, "*.json") : Array.Empty<string>();
        Assert.IsNotEmpty(files, "출시한 버전의 세이브 샘플이 최소 1개 있어야 합니다.");

        foreach (string file in files)
        {
            SaveData data = SaveSerializer.Deserialize(File.ReadAllText(file), out _);
            Assert.AreEqual(SaveData.CurrentVersion, data.version, Path.GetFileName(file));
            Assert.GreaterOrEqual(data.coins, 0, Path.GetFileName(file));
        }
    }
}
```

- `JsonException`은 `Newtonsoft.Json` 네임스페이스의 형식입니다. 잘린 JSON에서 나는 `JsonReaderException`이 이를 상속하므로 `Throws.InstanceOf`로 받습니다.
- 샘플 폴더의 `.json` 파일도 Unity가 `TextAsset`으로 임포트하지만, 테스트는 파일 경로로 직접 읽으므로 문제없습니다.
- 마지막 테스트는 **새 버전을 출시할 때마다 샘플 하나를 추가하는 습관**을 강제합니다. 1.1에서 마이그레이션을 잘못 짜면 1.0 샘플이 즉시 빨간불을 켭니다.
- 이 테스트들을 19장 CI 워크플로의 빌드 전 단계에 넣는 방법은 33장에서 다룹니다.

### 7단계: 출시 차단 기준표와 RC 판정

`Docs/qa/release-gate.md`입니다. 개념 절의 P0~P3 표를 코인 러시 전용 **체크 가능한 조건**으로 바꿉니다. 이 문서는 RC 판정 전에 확정하고, 판정 당일에는 고치지 않습니다.

| # | 출시 차단 조건 (하나라도 해당하면 출시 불가) | 확인 근거 |
|---|---|---|
| B1 | 스모크 15분 경로가 전 대상 환경에서 통과하지 않음 | PC-08 |
| B2 | 재현 가능한 크래시·멈춤·진행 불가가 1건이라도 열려 있음 | 버그 목록 |
| B3 | 세이브 손실·초기화·마이그레이션 실패 시나리오가 1건이라도 실패 | SAVE-01~04 |
| B4 | 스토어 문안의 약속을 어김 (컨트롤러 전체 지원, 표시한 접근성 기능, 지원 언어) | PAD-01·02, A11Y, 26장 문안 대조 |
| B5 | Steam Deck에서 첫 실행→플레이→종료가 버튼만으로 불가능 | DK-01·02 |
| B6 | 큰 면적 번쩍임이 1초 3회 초과 | A11Y-03 |
| B7 | 릴리스 빌드에 개발용 오버레이·치트·디버그 로그 과다 | 스모크 |
| B8 | (모바일) 서명·설치·결제 보상·광고 보상 중 하나라도 실패, 또는 스토어 요건(비공개 테스트, 대상 API 수준) 미충족 | MOB-01~07 |
| B9 | 매트릭스 P0 행 중 "미실시"가 남아 있음 | 매트릭스 |
| B10 | 라이선스 대장에 없는 에셋·폰트 사용 (28장) | 대장 대조 |

B9가 중요합니다. **확인하지 않은 것은 통과한 것이 아닙니다.** 시간이 없어 못 돌린 P0 행은 FAIL과 같게 취급합니다.

버그 기록 양식은 한 건당 다섯 줄이면 충분합니다. `Docs/qa/bugs.md` 예시입니다.

```
#43 [P0] 강화 구매 확인 창에서 패드 포커스 없음
  환경: E1+E4, RC1 (v1.0.0-rc1)   발견: PAD-02
  재현: 타이틀 → 강화 → 최대 체력 구매 → 확인 창 표시 → 패드 방향키/A 반응 없음 (100% 재현)
  원인: 확인 창 Show()에서 SetSelectedGameObject 호출 누락 (11장 규칙)
  수정: RC2에서 확인 창 열 때 "구매" 버튼 선택 → PAD-01·02 및 스모크 재실시 PASS
```

RC 판정 기록 예시(`Docs/qa/rc-decision.md`)입니다. 30장 캡스톤 루브릭의 점수와 별개로, 이 문서가 **출시 통과 조건**입니다.

```
판정일: 출시 D-10   대상: v1.0.0-rc2   판정자: 본인 + 검토자 1명(29장 동료)

P0 열린 버그: 0   (RC1의 #41 주사율, #43 포커스, #45 글자 크기 → RC2에서 수정·재검증)
P1 열린 버그: 1   #42 3440×1440 결과 화면 버튼 가장자리
    → 조건부 허용: 버튼은 누를 수 있음(기능 정상). 알려진 문제 공지 문구 작성, 1.0.1(D+7) 포함
P1 #47 엘리트 적 색 구분 → RC2에서 외곽선+크기 1.2배로 수정, A11Y-04 PASS
P2 #44, #46 → 1.0.1 백로그
미실시 P0 행: 0   (SAVE-05는 P1, RC2에서 실시 PASS)
Steam 접근성 표시: Camera Comfort, Custom Volume Controls, Keyboard Only Option, Color Alternatives
    (Adjustable Text Size는 150%에서 기준 미달로 표시하지 않음)

결론: 출시 진행. default 브랜치 반영은 26장 절차대로 웹에서 수동.
      출시 후 48시간 동안 auto_pause·크래시 로그 매일 확인 (33장 루틴)
```

### 확인하기

1. `Docs/qa/` 폴더에 devices, matrix, bugs, release-gate, rc-decision 문서 다섯 개가 있고, 매트릭스의 모든 P0 행에 결과가 채워져 있다.
2. 판 도중 무선 패드를 끄면 즉시 일시정지 창이 뜨고, Console(또는 24장 로그 파일)에 `auto_pause`와 `reason=gamepad_disconnected`가 남는다. Game 뷰 밖을 클릭했다 돌아와도 일시정지돼 있다.
3. Development Build에서는 좌상단에 버전·해상도·주사율·입력 장치·세이브 버전이 보이고, 릴리스 빌드에서는 보이지 않는다.
4. Game 뷰 1280×800에서 레벨업 창을 띄우고 **Audit Now**를 실행하면 기준 미달 텍스트가 경로와 함께 에러로 표시되고, 수정 후 "기준 미달 0개"가 된다.
5. UI 배율을 1.5로 바꾸면 모든 Canvas의 UI가 커지고 재실행 후에도 유지된다.
6. Test Runner EditMode에서 10장 테스트 2개와 `SaveRobustnessTests` 4개가 모두 통과한다. `SaveFixtures` 폴더를 비우면 마지막 테스트가 실패한다.

## 흔한 실수

1. **증상**: 매트릭스가 모두 PASS였는데 출시 첫날 Deck 사용자 리뷰에 "패드로 못 닫는 창"이 나온다. → **원인**: 에디터에서 마우스가 연결된 채 테스트해 포커스 없는 창을 무의식적으로 클릭함. → **해결**: 패드·Deck 행은 **마우스를 물리적으로 뽑고** 수행하도록 절차에 적습니다.
2. **증상**: RC2에서 고친 버그는 PASS인데 다른 화면이 새로 깨졌다. → **원인**: 수정한 행만 재검증. → **해결**: 수정 빌드마다 스모크 + 전체 P0 행을 다시 돌리고, 결과 열은 RC별로 새로 만듭니다.
3. **증상**: "100판에 한 번이라서" 세이브 초기화 버그를 P2로 미뤘다가 부정 리뷰가 몰린다. → **원인**: 빈도로 등급을 매김. → **해결**: 데이터 손실·진행 불가·약속 위반은 빈도와 무관하게 P0입니다. 등급 질문 순서를 문서 첫머리에 둡니다.
4. **증상**: 모바일 출시일을 잡았는데 프로덕션 신청 버튼이 없다. → **원인**: 신규 개인 계정의 12명·14일 비공개 테스트 요건을 모름. → **해결**: 모바일 일정은 "비공개 테스트 시작일 + 14일 + 검토 기간"으로 역산하고, 테스터를 24장 모집 단계에서 확보합니다.
5. **증상**: 흔들림 옵션 0%인데 레벨업 연출에서 화면이 흔들린다는 제보. → **원인**: 레벨업 슬로모션 줌을 `GameFeel` 밖에서 직접 카메라에 적용해 옵션을 우회. → **해결**: 카메라 효과는 모두 16장 `GameFeel` 경로를 거치게 하고, A11Y-01을 연출 종류별(피격·보스·레벨업)로 나눠 검수합니다.
6. **증상**: 핫픽스를 롤백했더니 일부 사용자의 진행이 초기화됐다. → **원인**: 새 버전 세이브를 구 버전이 읽지 못하고 기본값으로 덮어씀. → **해결**: 10장 미래 버전 쓰기 차단을 유지하고, SAVE-04(새 빌드 저장→구 빌드 실행)를 모든 업데이트 RC의 P0 행으로 둡니다.

## 연습 문제

**1. ★☆☆ 등급 매기기**
다음 다섯 버그에 P0~P3를 매기고 근거를 한 줄씩 쓰세요. (a) 한국어 설정에서 무기 "번개 사슬" 설명 마지막 두 글자가 잘림 (b) 보스 처치 순간 5% 확률로 결과 화면이 뜨지 않고 멈춤 (c) PlayStation 패드에서 안내 문구가 Xbox 버튼 이름으로 나옴(조작은 정상) (d) 크레딧에 사용한 효과음 제작자 표기 누락(라이선스가 표기 조건부) (e) 타이틀 배경 파티클이 가끔 한 프레임 깜빡임.

<details><summary>힌트·해설</summary>

(a) P1 — 핵심 정보(무기 설명)가 첫 10분에 보이고 판단을 방해하지만 진행은 가능합니다. 짧은 문구로 우회 가능. (b) P0 — 확률과 무관하게 진행 불가이며 10분 판 전체를 잃습니다. (c) P2 — 조작은 정상이므로 차단은 아니지만, Deck Verified의 글리프 조건은 "사용 중인 입력과 일치"이므로 Deck 기본(Xbox 계열 표기와 Deck 표기)에서 문제가 없는지 따로 확인합니다. 스토어에 PlayStation 패드 지원을 명시했다면 P1로 올립니다. (d) P0 — 심각도는 낮아 보여도 라이선스 조건 위반은 출시 차단 조건 B10입니다. 우선순위가 심각도보다 높은 대표 사례입니다. (e) P3 — 단, 깜빡임이 큰 면적이고 반복되면 A11Y-03 기준으로 다시 봅니다.

</details>

**2. ★★☆ 주사율 버그 찾기**
RC1의 #41(144Hz에서 적이 빠름)이 다음 코드 때문이라고 합시다. 무엇이 문제인지, 어떻게 고치는지, 이 버그가 PC-02 행 없이 발견되지 않은 이유를 설명하세요.

```csharp
private void Update()
{
    spawnTimer += 1f / 60f;
    if (spawnTimer >= data.spawnInterval) { spawnTimer = 0f; SpawnOne(); }
}
```

<details><summary>힌트·해설</summary>

프레임마다 고정값 1/60초를 더하므로 144fps에서는 실제 1초에 타이머가 2.4초 흐릅니다. 스폰 간격이 2.4배 짧아져 적이 훨씬 많아집니다. `spawnTimer += Time.deltaTime;`로 바꾸고, 초과분을 버리지 않도록 `spawnTimer -= data.spawnInterval;`로 빼면 프레임이 흔들려도 누적 오차가 없습니다. 개발 PC가 60Hz이고 `vSyncCount = 1`이면 프레임이 60에 고정돼 두 코드의 결과가 같으므로 발견되지 않습니다. 매트릭스에 **서로 다른 주사율 환경**을 명시한 이유입니다. 같은 패턴을 코드 전체에서 찾으려면 `1f / 60f`, `* 0.016` 같은 문자열을 검색합니다.

</details>

**3. ★★☆ 색 비의존 개선안**
A11Y-04에서 엘리트 적이 색만 다르다는 문제가 나왔습니다. 코인 러시 규칙(21장: 엘리트 1종, 처치 시 보상 큼)을 해치지 않는 개선안 세 가지를 제시하고, 각각의 검증 절차를 매트릭스 행 형식으로 쓰세요.

<details><summary>힌트·해설</summary>

예시: (1) 외곽선 — 14장 Shader Graph 외곽선을 엘리트에만 적용. 행: "그레이스케일 캡처에서 일반 적 20마리 사이 엘리트를 3초 안에 찾기, 테스터 3명 중 3명 성공". (2) 크기·실루엣 — 스케일 1.2배와 머리 장식 스프라이트. 행: "실루엣만(검정 채우기) 캡처에서 구분 가능". (3) 등장 알림 — 화면 가장자리 방향 아이콘+효과음. 행: "소리 끔 상태에서도 아이콘으로 등장 인지, 효과음만으로도 인지(화면 보지 않고 테스터 반응)". 하나의 수단에만 의존하지 않도록 두 가지 이상을 조합하는 것이 좋고, 검증은 개발자 본인이 아닌 테스터로 하는 편이 정확합니다(본인은 이미 답을 압니다).

</details>

**4. ★★★ 내 게임의 출시 차단 기준표**
여러분의 게임(또는 코인 러시 모바일판)에 대해 (a) 스토어 페이지 문안에서 약속한 문장을 모두 뽑아 각각을 검수 행으로 바꾸고, (b) 1단계 형식의 환경 목록에서 확보하지 못한 환경의 위험을 어떻게 줄일지 정하고, (c) 7단계 B1~B10을 자기 게임에 맞게 추가·삭제해 확정하세요. 그다음 실제 빌드로 스모크 경로를 돌려 소요 시간을 재고, 15분을 넘으면 경로를 줄이세요.

<details><summary>힌트·해설</summary>

(a) "Full controller support", "Steam Deck friendly UI", "Korean/English", "10-minute runs", 접근성 표시 항목이 대표적입니다. 문장마다 "무엇을 해 보면 거짓이 드러나는가"를 절차로 씁니다. (b) 미확보 환경은 대체 수단(Game 뷰 해상도, 지인 기기, 비공개 테스트 참여자에게 특정 절차 요청)과 남는 위험을 함께 적고, 출시 후 첫 주 모니터링 항목으로 넘깁니다. (c) 모바일판이면 B8을 세분화(서명, 비공개 테스트 요건, 대상 API, 결제 복원, 광고 보상, 동의 흐름)하고, 온라인 기능이 없는 게임이면 서버 관련 조건은 지웁니다. 스모크가 15분을 넘으면 "켜짐·한 판·저장·재실행"만 남기고 나머지는 매트릭스로 보냅니다.

</details>

## 셀프 체크

**1. QA 매트릭스와 자동 테스트(EditMode/PlayMode)는 각각 무엇을 보장하며, 왜 둘 다 필요한가요?**

<details><summary>모범 답안</summary>

자동 테스트는 코드 단위의 동작(마이그레이션, 직렬화, 손상 감지)이 설계대로인지 빠르고 반복 가능하게 보장합니다. QA 매트릭스는 실제 기기·주사율·패드·절전·스토어 설치처럼 코드 밖 환경에서 스토어가 약속한 경험이 성립하는지를 봅니다. 144Hz 타이머 버그나 패드 포커스 누락은 단위 테스트로 잡기 어렵고, 반대로 모든 과거 세이브의 마이그레이션은 사람이 매번 수동으로 확인하기 어렵습니다. 그래서 반복적·결정적인 것은 자동화하고, 환경 의존적인 것은 매트릭스로 봅니다.

</details>

**2. P0 판정에서 발생 빈도를 고려하지 않는 이유는 무엇인가요?**

<details><summary>모범 답안</summary>

P0는 데이터 손실, 진행 불가, 약속·정책 위반처럼 겪은 사람이 돈과 시간을 잃는 문제입니다. 드물게 발생해도 겪은 사람은 환불하거나 긴 플레이 시간이 붙은 부정 리뷰를 남기고, 판매 규모가 커지면 절대 건수도 커집니다. 또 출시 직전에는 "드물다"는 판단이 희망 섞인 추정이기 쉬워서, 빈도 대신 피해의 종류로 기계적으로 판정하는 편이 안전합니다.

</details>

**3. Steam Deck Verified 기준 중 텍스트 가독성과 성능 기준은 무엇이며, 코인 러시는 어떻게 검증하나요?**

<details><summary>모범 답안</summary>

2026년 9월 확인 기준으로 1280×800에서 가장 작은 글자가 9픽셀 높이 미만이 되면 안 되고, 약 30cm 거리에서 읽혀야 합니다. 성능은 기본 설정에서 플레이 가능한 프레임이어야 하며 Deck에서는 800p 30fps입니다. 코인 러시는 Canvas Scaler 배율(800/1080)로 계산한 최소 폰트 크기 규칙(기준 해상도 24)을 두고, `TextSizeAudit`으로 화면별 어림값을 뽑은 뒤 실기기에서 30cm 거리로 확인합니다. 성능은 기본 품질 설정 그대로 9분대 최대 적 수 구간을 Deck에서 측정합니다.

</details>

**4. 핫픽스 롤백 시 세이브가 사라질 수 있는 이유와, 이를 검수에서 막는 방법을 설명해 보세요.**

<details><summary>모범 답안</summary>

새 버전이 세이브 구조를 올리면(v3) 롤백한 구 버전은 그 버전을 모릅니다. 구 버전이 읽기 실패를 "새 게임"으로 처리하고 저장하면 새 버전에서 쌓은 진행이 기본값으로 덮어써집니다. 10장처럼 미래 버전 파일을 만나면 쓰기를 막아야 하고, 검수에서는 베타 브랜치의 새 빌드로 저장한 뒤 default 브랜치의 구 빌드로 실행해 파일이 덮어써지지 않는지(SAVE-04) 확인합니다. EditMode에서는 미래 버전 예외 테스트로 이 신호가 사라지지 않게 고정합니다.

</details>

**5. Google Play 신규 개인 계정으로 모바일판을 낼 때 출시 일정에 반드시 넣어야 하는 기간은 무엇인가요?**

<details><summary>모범 답안</summary>

2023년 11월 13일 이후 만든 개인 계정은 최소 12명의 테스터가 14일 연속 참여한 비공개 테스트를 거친 뒤 프로덕션 접근을 신청할 수 있고, 신청 검토가 보통 7일 이내 걸립니다. 따라서 모바일 출시일은 비공개 테스트 시작일에서 최소 14일과 검토 기간을 더한 뒤로 잡고, 테스터 12명은 그 전에 확보해야 합니다. 또 2026년 8월 31일부터 신규 앱·업데이트는 Android 16(API 36) 이상을 대상으로 해야 하므로 빌드 설정도 함께 확인합니다. 모든 수치는 출시 직전 공식 도움말로 재확인합니다.

</details>

## 핵심 요약

- QA 매트릭스는 환경×시나리오×판정의 표이며, 스토어 페이지에서 약속한 문장은 전부 필수 행이 됩니다.
- 우선순위는 P0(출시 차단)~P3로 나누고, 데이터 손실·진행 불가·약속과 정책 위반·광과민 위험은 빈도와 무관하게 P0입니다. 실시하지 않은 P0 행은 실패로 취급합니다.
- PC는 해상도·비율뿐 아니라 **주사율**을 다르게 테스트해야 프레임 의존 코드가 드러납니다.
- Steam Deck Verified는 기본 컨트롤러 설정으로 전체 접근, 입력과 일치하는 글리프, 800p 30fps, 1280×800에서 최소 9픽셀 글자, 경고·런처 없음 등이 기준이며, 절전 복귀·오프라인·Cloud 이어 하기는 환불 방지 차원에서 추가로 검수합니다.
- 모바일은 실스토어 설치(Play App Signing), 신규 개인 계정의 12명·14일 비공개 테스트, 대상 API 수준, Android vitals 임계값이 일정과 판정에 직접 영향을 줍니다.
- 접근성은 옵션 존재가 아니라 옵션 켜고 끈 상태의 실제 차이를 검증하며, Steam 접근성 표시는 기준을 충족한 항목만 체크합니다.
- 세이브는 강제 종료·손상·이전 버전·미래 버전(롤백)·클라우드 충돌을 일부러 일으켜 확인하고, 출시한 버전마다 세이브 샘플을 테스트에 추가합니다.
- 모든 빌드는 15분 스모크, RC 빌드는 전체 매트릭스, 수정 빌드는 스모크+전체 P0 행을 다시 돌리고, 출시 여부는 미리 확정한 차단 기준표로 판정합니다.

## 더 읽을거리

- Steamworks 문서 — Steam Deck Compatibility Review Process: https://partner.steamgames.com/doc/steamdeck/compat
- Steamworks 문서 — Steam Deck Recommendations: https://partner.steamgames.com/doc/steamdeck/recommendations
- Steamworks 문서 — Accessibility Features: https://partner.steamgames.com/doc/accessibility_features
- Play Console 도움말 — App testing requirements for new personal developer accounts: https://support.google.com/googleplay/android-developer/answer/14151465
- Play Console 도움말 — Use Play App Signing: https://support.google.com/googleplay/android-developer/answer/9842756
- Android Developers — Target API level requirements for Google Play apps: https://developer.android.com/google/play/requirements/target-sdk
- Android Developers — Android vitals: https://developer.android.com/topic/performance/vitals
- Apple Developer — TestFlight: https://developer.apple.com/testflight/
- W3C — Understanding WCAG 2.2 Success Criterion 2.3.1 Three Flashes or Below Threshold: https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html
- Microsoft — Xbox Accessibility Guidelines: https://learn.microsoft.com/en-us/gaming/accessibility/guidelines
- Game Accessibility Guidelines: https://gameaccessibilityguidelines.com/
