# 32. 게임 현지화

> **이 장에서 배울 것**
> - 국제화(코드 준비)와 현지화(번역·검수)를 구분하고, 하드코딩 문자열이 만드는 비용을 설명할 수 있다
> - Unity Localization 패키지(1.5.x)로 Locale·String Table을 구성하고, Smart String 변수·복수형으로 동적 문장을 만든다
> - 언어 선택을 10장 세이브에 저장하고 Steam 언어·시스템 언어로 첫 실행 언어를 정하는 흐름을 구현한다
> - 폰트 글리프 누락과 TextMeshPro 텍스트 넘침을 의사 현지화(Pseudo-Locale)와 검사 도구로 찾아낸다
> - 번역 전달용 CSV·용어집·컨텍스트 메모를 만들고 검수 절차를 거쳐 스토어 언어 표기와 일치시킨다
>
> **선수 장**: 09, 10, 11 (12의 설정 화면, 19의 Addressables 빌드를 읽었다면 더 좋음) · **예상 시간**: 4~6시간 (번역 대기 시간 제외) · **코인 러시 진행**: 모든 UI 문자열이 테이블로 이동, 설정 화면의 언어 선택, 세이브에 저장되는 언어, 한/영 전환 빌드, 번역 전달 CSV와 용어집
>
> **권장 시점**: 11장을 마친 뒤. UI 문자열이 수십 개일 때 옮기면 반나절이지만, 출시 직전 수백 개일 때 옮기면 일주일이 걸립니다. 이 장 이후에 추가하는 모든 문자열은 처음부터 테이블에 넣습니다.

## 왜 필요한가

11장까지의 코인 러시 코드에서 화면에 글자를 쓰는 곳을 찾아보면 이렇습니다.

```csharp
titleText.text = cleared ? "생존 성공!" : "쓰러졌습니다";           // 11장 ResultView
timeText.text = $"생존 시간 {total / 60:00}:{total % 60:00}";      // 11장 ResultView
levelText.SetText("Lv {0}", level);                                 // 11장 HudView
public string displayName;  [TextArea] public string description;   // 11장 UpgradeData
public string warningText = "무언가 다가온다…";                     // 22장 WaveData
[SerializeField] private string format = "{0}: 일시정지";            // 08장 ActionPromptLabel
loader.LoadingScreen.ShowError("화면을 불러오지 못했습니다...");    // 09장 GameFlow
```

Steam 페이지를 영어로도 열기로 했다고 합시다(26장). Valve 문서에 따르면 Steam 사용자의 60% 이상이 영어가 아닌 언어로 Steam을 씁니다. 반대로 말하면 한국어만 지원하는 게임은 대부분의 사용자에게 "읽을 수 없는 게임"입니다. 그런데 위 코드로 영어판을 만들려고 하면 문제가 줄줄이 나옵니다.

문자열이 코드·씬·프리팹·ScriptableObject에 **흩어져 있어** 번역가에게 넘길 목록이 없고, `"생존 시간 " + 시간` 같은 **문장 조립**은 언어마다 어순이 달라 번역이 불가능합니다. 영어 "Settings"는 "설정"보다 훨씬 길어 **버튼 밖으로 넘치고**, 11장의 한글 Static 폰트 아틀라스에 없는 기호가 번역문에 들어오면 **□(두부)** 가 뜹니다. 플레이어가 고른 언어가 **다음 실행 때 초기화**되거나 Steam 클라우드로 옮긴 다른 PC에서 엉뚱한 언어로 나오기도 합니다.

웹의 react-i18next 역할을 Unity에서는 **Localization 패키지**가 합니다. 이 장은 코인 러시를 한/영 전환 빌드로 만들고, 나중에 일본어·중국어를 추가할 때(29장 출시 후 목록) 코드 수정 없이 테이블만 추가하면 되는 상태로 만듭니다.

## 개념

### 국제화(i18n)와 현지화(l10n)

**국제화**는 개발자가 번역 가능하게 코드를 준비하는 일(문자열 분리, 어순 자유, 폰트·레이아웃 여유, 숫자 형식)이고 이 장의 1~8단계입니다. **현지화**는 번역가·검수자가 실제 번역·용어 통일·게임 안 검수를 하는 일이고 9~10단계입니다. 스토어 문안·스크린샷·지원 언어 표기는 **스토어 현지화**로 26장과 10단계에서 다룹니다.

국제화를 먼저 끝내면 언어를 추가하는 비용은 "번역비 + 검수 1~2일"로 떨어집니다. 국제화 없이 번역부터 받으면 번역문을 코드 곳곳에 붙여 넣느라 번역비보다 개발 시간이 더 듭니다.

### Unity Localization 패키지의 구조

패키지 이름은 `com.unity.localization`입니다. Unity 6000.0용으로 **1.5.x**가 배포되어 있습니다(2026년 확인 시점의 Unity 6000.0 매뉴얼 기준 1.5.13). 버전마다 메뉴 이름이 조금씩 다르므로 설치한 버전의 매뉴얼을 함께 보세요.

```
Localization Settings (프로젝트에 하나, Project Settings > Localization)
 ├─ Available Locales:  ko (Korean), en (English)        ← Locale 에셋
 ├─ Startup Locale Selectors: [Command Line] → [System Locale] → [Specific Locale: en]
 ├─ String Database   (Missing Translation 처리, Smart Format 설정)
 └─ Asset Database    (폰트·이미지 등 언어별 에셋)

String Table Collection "UI"                              ← 번역 단위 묶음
 ├─ Shared Table Data: 키 목록 (hud.level, result.title.cleared, ...) + 공용 주석
 ├─ String Table (ko): 키 → "생존 성공!"
 └─ String Table (en): 키 → "You Survived!"
```

- **Locale**: 언어(+지역) 하나. 식별자는 `ko`, `en`, `en-US`, `zh-Hans` 같은 코드입니다.
- **Shared Table Data**: 키와 ID. 모든 언어 테이블이 공유합니다. 키 이름을 바꿔도 ID가 유지돼 참조가 깨지지 않습니다.
- **String Table**: 언어별 번역 값.
- 테이블은 내부적으로 **Addressables**로 로드됩니다. 그래서 19장 `BuildScripts`가 플레이어 빌드 전에 `AddressableAssetSettings.BuildPlayerContent`를 호출하는 구조가 여기서도 필요합니다. Addressables 빌드를 빠뜨리면 에디터에선 번역이 보이는데 빌드에서는 키 이름이나 빈 문자열이 나옵니다.

JS 비유로 보면 `locales/ko/ui.json`, `locales/en/ui.json`을 두고 `t('hud.level')`로 꺼내는 구조입니다. 차이는 Unity 쪽이 에디터 창(Localization Tables)으로 편집하고, 키 대신 ID로 참조를 유지한다는 점입니다.

### 키 이름 규칙

키는 코드와 번역가가 함께 보는 이름입니다. 규칙을 먼저 정합니다.

형식은 `<화면 또는 영역>.<요소>[.<상태>]`입니다. 예: `title.button.start`, `hud.level`, `result.title.cleared`, `upgrade.orb.desc`, `wave.warning.boss`, `error.scene_load_failed`.

- **문장이 아니라 위치·의미로** 짓습니다. `"survived_text"`보다 `result.title.cleared`.
- 같은 한국어라도 **쓰이는 곳이 다르면 키를 나눕니다.** "시작"(버튼)과 "시작"(튜토리얼 제목)은 영어에서 "Start"와 "Getting Started"로 갈라질 수 있습니다.
- 테이블은 2~4개로 나눕니다: `UI`(메뉴·HUD·결과), `Gameplay`(업그레이드·적·무기 이름과 설명), `System`(오류·동의·크레딧). 번역가에게 넘길 때 우선순위와 톤을 따로 줄 수 있습니다.

### 정적 텍스트 vs 동적 텍스트

| 종류 | 예 | 방법 |
|---|---|---|
| 정적 | 타이틀 "시작" 버튼, 설정 화면 제목 | TMP 컴포넌트에 **Localize String Event** 컴포넌트를 붙이고 키 선택. 코드 없음 |
| 변수가 들어간 문장 | "생존 시간 03:25", "적 120마리 처치" | `LocalizedString` 필드 + **Smart String** 변수 |
| 데이터 에셋의 텍스트 | 업그레이드 이름·설명, 웨이브 경고 | ScriptableObject의 `string` 필드를 `LocalizedString`으로 교체 |
| 매 프레임·매초 바뀌는 숫자 | HUD 레벨, 타이머, 코인 수 | 언어가 바뀔 때만 **서식 템플릿**을 받아 두고 숫자는 11장처럼 `SetText`로 (할당 0 유지) |

마지막 줄이 중요합니다. 02장에서 만든 "할당 0 업데이트 루프"를 지키려면 HUD 숫자를 매초 번역 시스템에 통과시키지 않습니다. 번역 시스템은 **틀(템플릿)** 만 주고, 숫자 끼워 넣기는 TMP의 `SetText(format, number)`가 합니다.

### Smart String — 변수, 복수형, 선택

테이블 항목을 **Smart**로 표시하면 SmartFormat 문법을 쓸 수 있습니다(Localization Tables 창에서 항목 오른쪽 메뉴 → Smart Format, 또는 `LocalizedString` 편집기의 Smart 체크).

```
이름 있는 변수     ko: "생존 시간 {time}"              en: "Time Survived {time}"
복수형            ko: "적 {kills}마리 처치"            en: "{kills:plural:{} enemy defeated|{} enemies defeated}"
```

- **이름 있는 변수**(`{time}`)는 번역가가 어순을 자유롭게 바꿀 수 있게 합니다. `{0}` 같은 번호보다 의미가 드러나 실수가 적습니다.
- **복수형**은 언어마다 규칙이 다릅니다. 한국어·일본어·중국어는 단복수 구분이 없고, 영어는 1개/그 외, 러시아어·폴란드어는 더 많은 형태가 있습니다. SmartFormat의 plural 포매터는 **현재 Locale의 복수 규칙**으로 `|`로 나눈 형태 중 하나를 고릅니다.
- 성공/실패처럼 **완전히 다른 문장은 조건 문법으로 한 항목에 넣지 말고 키를 둘로 나눕니다.** 번역가가 문법을 깨뜨리기 쉽기 때문입니다.

변수 값은 코드에서 `LocalizedString`의 **로컬 변수**(Persistent Variables)로 넣습니다.

```csharp
using UnityEngine.Localization;
using UnityEngine.Localization.SmartFormat.PersistentVariables;

[SerializeField] private LocalizedString killsLabel;   // 키: result.kills (Smart)
private readonly IntVariable kills = new IntVariable();

void Awake()  => killsLabel["kills"] = kills;           // 이름 "kills"로 변수 등록 (한 번)
void Show(int n) => kills.Value = n;                    // 값만 바꾸면 StringChanged 구독자에게 새 문장이 전달됨
```

`LocalizedString`은 문자열 이름으로 변수를 넣고 꺼내는 인덱서와 `Add(string, IVariable)` 메서드를 제공합니다. 인스펙터에서 같은 이름의 변수를 이미 추가했을 수 있으니 이 장에서는 덮어쓰기 안전한 **인덱서 대입**을 씁니다.

### 언어 선택의 우선순위

첫 실행과 두 번째 실행의 규칙이 다릅니다.

```
[두 번째 실행 이후]  세이브에 저장된 언어가 있으면 → 그 언어  (플레이어의 선택이 최우선)

[첫 실행]
  1. 명령행 인수 -language=en          (테스트·스트리머용, Command Line Locale Selector)
  2. Steam 클라이언트 언어              (Steam판: ISteamApps::GetCurrentGameLanguage → "koreana", "english")
  3. OS 시스템 언어                    (System Locale Selector)
  4. 기본값 en                         (Specific Locale Selector)
```

Localization 패키지의 **Startup Locale Selectors**는 목록 위에서부터 차례로 물어 처음 결과를 쓰는 방식입니다. 기본 제공 선택기는 Command Line, System Locale, Specific Locale, Player Pref Locale 네 가지이고, `IStartupLocaleSelector` 인터페이스로 직접 만들 수도 있습니다.

코인 러시는 `PlayerPrefs`가 아니라 **10장 세이브 파일**에 언어를 저장합니다. 26장의 Steam Auto-Cloud가 세이브 폴더를 동기화하므로, 다른 PC에서 이어 해도 같은 언어로 시작합니다. 대신 주의할 점이 하나 있습니다. 26장 `SteamManager.Awake`는 **세이브를 읽기 전에** `SaveSystem.UseUserFolder`로 계정별 폴더를 정합니다. 언어 선택기가 그보다 먼저 `SaveSystem.Load()`를 부르면 공용 폴더의 세이브를 캐시해 버립니다. 그래서 세이브에 저장된 언어는 Startup Selector가 아니라 **부트스트랩(09장 `GameFlow.Start`)에서 적용**합니다. Startup Selector는 "세이브가 없을 때의 기본값"만 담당합니다.

### 폰트와 글리프

11장의 폰트 구성(Pretendard Static: 영문·숫자·기호 + KS X 1001 2,350자 → Fallback: Dynamic)은 한국어·영어에는 충분합니다. 문제는 두 가지입니다.

1. **Static 아틀라스에 없는 글자**: KS X 1001에 없는 한글(예: 일부 고유명사 글자), 번역문의 특수 기호(—, …, ’, ×, ★)는 Dynamic 폴백으로 넘어갑니다. 동작은 하지만 첫 등장 순간 아틀라스에 글자를 추가하는 비용과 **Dynamic 아틀라스의 에디터 변경(git diff)** 이 생깁니다. 테이블의 모든 글자를 추출해 Static 아틀라스를 다시 굽는 것이 정석입니다(7단계 도구).
2. **언어별 다른 폰트**: 일본어·중국어를 추가하면 한글 폰트에 없는 한자·가나가 필요합니다. 방법은 둘입니다.
   - **폴백 체인에 추가**: Pretendard → Noto Sans JP → Noto Sans SC. 코드 변경이 없고 한 화면에 여러 언어가 섞여도(닉네임) 표시됩니다. 대신 같은 한자라도 일본식·중국식 글자 모양이 폰트 순서에 따라 정해집니다.
   - **Locale별 폰트 교체**: Asset Table에 `TMP_FontAsset`을 넣고 `LocalizedTmpFont`(`LocalizedAsset<TMP_FontAsset>`)로 텍스트의 폰트를 바꿉니다. 언어마다 정확한 글자 모양을 쓰지만 텍스트 컴포넌트마다 설정이 필요합니다.

코인 러시 1.0(한/영)은 폴백 체인만으로 충분합니다. 폰트 라이선스(SIL OFL 등)는 28장 대장에 이미 있고, 새 폰트를 추가하면 대장에 행을 추가합니다.

### 텍스트 넘침 — 길이는 언어마다 다르다

UI 문구는 영어가 한국어보다 대체로 깁니다(설정 → Settings, 코인 제단 → Coin Shrine). 짧은 버튼 문구일수록 비율 차이가 큽니다. 대응 순서는 다음과 같습니다.

1. **레이아웃에 여유**: 버튼 폭을 가장 긴 언어 기준 + 30%로. 한 줄 고정보다 두 줄 허용.
2. **TMP Auto Size**는 최후 수단: 최소 크기(Font Size Min)를 가독성 한계 이상으로 두고, 켠 텍스트는 리빌드 비용이 크니 매 프레임 바뀌는 HUD 숫자에는 쓰지 않습니다(11장 리빌드 비용).
3. **번역가에게 글자 수 제한을 전달**: CSV 주석 열에 "최대 12자(영문 기준), 버튼"처럼 적습니다.
4. **의사 현지화로 미리 터뜨려 보기**: 번역을 받기 전에 모든 문자열을 인위적으로 늘리고 악센트를 붙인 가짜 언어로 화면을 돌려 봅니다.

**Pseudo-Locale**(의사 현지화)은 패키지에 들어 있습니다. `Assets > Create > Localization > Pseudo-Locale`로 만들고, 기본으로 **Accenter**(악센트 문자로 치환 → 폰트 누락 확인), **Expander**(길이 늘리기 → 넘침 확인), **Encapsulator**(앞뒤에 괄호 → 잘린 문장·하드코딩 문자열 확인) 방법이 들어 있습니다. 하드코딩 문자열은 의사 현지화 화면에서 **괄호 없이 멀쩡한 한국어로 남아 있어** 한눈에 보입니다.

### 번역 전달과 검수

번역 품질은 번역가 실력보다 **넘긴 정보의 양**에 좌우됩니다. 번역가는 게임을 해보지 않은 상태에서 키와 문장만 봅니다. 그래서 문자열 CSV와 함께 **컨텍스트 메모**(버튼인지 제목인지), **글자 수 제한**, **변수 설명**(`{time}`은 "03:25" 형태), **용어집**, **톤 가이드**, **화면 스크린샷**, 가능하면 **테스트 빌드**(26·33장 beta 브랜치)를 넘깁니다(9단계).

검수(LQA, Linguistic Quality Assurance)는 **게임 안에서** 합니다. 스프레드시트에서 맞는 번역도 화면에서는 잘리거나 어색합니다. 검수자에게는 모든 화면을 거치는 체크리스트를 주고, 문제는 "화면 / 키 / 현재 문장 / 제안 / 사유"로 받습니다.

CSV를 다시 들여올 때는 **Import → CSV (Merge)** 를 씁니다. 파일에 있는 항목만 갱신하고 나머지는 건드리지 않습니다(그냥 CSV Import는 테이블 내용을 교체). 새 항목을 CSV에서 추가할 때는 Id 칸을 비우거나 0으로 두면 패키지가 새 ID를 부여합니다.

## 실습: 코인 러시에 적용하기

앞 장의 최소 시그니처입니다.

```csharp
// 09장 GameFlow        : Start()에서 ChangeState(GetInitialState()) — 부트스트랩 씬, DefaultExecutionOrder(-100)
// 10장 SaveSystem      : static SaveData Load(), Save(SaveData)  / SaveMigrator.Steps, CurrentVersion
// 10장 연습 2          : SaveData v3 — settings { bgmVolume, sfxVolume }, unlockedCharacters
//                        (settings 클래스 이름은 SettingsData로 부릅니다. 12장에서 버전을 따로 올렸다면 V3ToV4를 "현재 → 다음"으로 읽으세요)
// 26장 SteamManager    : static bool Initialized  (#if !DISABLESTEAMWORKS)
```

### 1단계: 패키지 설치와 Locale 만들기

1. `Window > Package Manager` → Unity Registry → **Localization** 설치(Unity 6000.0 기준 1.5.x).
2. `Edit > Project Settings > Localization` → **Create** 로 Localization Settings 에셋을 `Assets/_CoinRush/Localization/`에 만듭니다.
3. 같은 화면의 **Locale Generator**에서 `Korean (ko)`, `English (en)`을 체크하고 Generate Locales → 같은 폴더의 `Locales/`에 저장합니다.
4. **Project Locale Identifier**를 `ko`로 둡니다. 원문 언어가 한국어라는 뜻입니다.
5. Startup Locale Selectors를 위에서부터 `Command Line Locale Selector` → `System Locale Selector` → `Specific Locale Selector (en)` 순서로 둡니다. 기본으로 들어 있는 `Player Pref Locale Selector`는 **제거합니다**(세이브 파일과 저장소가 둘이 되면 서로 다른 값을 가리키는 버그가 생김).
6. String Database의 **Missing Translation State**를 개발 중에는 "경고 문구 표시"로 둬서 빠진 번역이 화면에 드러나게 합니다(출시 빌드에서는 폴백 언어 표시로 전환 — 10단계 체크리스트).
7. **Preload Behavior**는 `Preload Selected Locale And Fallbacks`로 둡니다. UI 테이블이 초기화 시 함께 로드돼, 첫 화면에서 문자열이 한 프레임 늦게 나타나는 깜빡임을 줄입니다. 각 테이블의 Preload 체크도 켭니다.

### 2단계: String Table Collection과 키 목록 (완성본)

`Window > Asset Management > Localization Tables` → **New Table Collection** → Type `String Table Collection`, 이름 `UI`, 대상 Locale ko·en 체크 → Create. 같은 방식으로 `Gameplay`, `System`을 만듭니다.

코인 러시 1.0의 핵심 키입니다(전체의 일부. 나머지도 같은 형식). **주석 열은 번역가에게 그대로 전달됩니다.**

| 테이블 | 키 | ko | en | Smart | 주석 (Shared Comment) |
|---|---|---|---|---|---|
| UI | title.button.start | 시작 | Play | | 타이틀 메인 버튼, max 10 |
| UI | title.button.upgrades | 영구 강화 | Upgrades | | 타이틀 버튼. 용어집 "영구 강화" |
| UI | title.button.settings | 설정 | Settings | | 타이틀 버튼, max 12 |
| UI | hud.level | Lv {0} | Lv {0} | 아니오 | HUD 서식. {0}=레벨 숫자. 기호 {0} 유지 필수, max 6 |
| UI | hud.pause_prompt | {key}: 일시정지 | {key}: Pause | 예 | {key}=키 이름("Esc", "Start") |
| UI | result.title.cleared | 생존 성공! | You Survived! | | 10분 생존 시 |
| UI | result.title.failed | 쓰러졌습니다 | You Fell | | 사망 시. 비난조 피하기 |
| UI | result.time | 생존 시간 {time} | Time Survived {time} | 예 | {time}="03:25" 형태 문자열 |
| UI | result.coins | 획득 코인 {0} | Coins Earned {0} | 아니오 | 카운트업 서식. {0} 유지 |
| UI | result.kills | 적 {kills}마리 처치 | {kills:plural:{} enemy defeated\|{} enemies defeated} | 예 | {kills}=정수 |
| UI | result.button.retry | 다시 하기 | Try Again | | max 12 |
| UI | menu.settings.language | 언어 | Language | | 설정 항목 이름 |
| Gameplay | upgrade.orb.name | 궤도 구슬 | Orbiting Orb | | 무기 이름, max 16 |
| Gameplay | upgrade.orb.desc | 주위를 도는 구슬이 닿은 적에게 피해를 줍니다. | Orbs circle you and damage enemies they touch. | | 카드 설명, 2줄 이내 |
| Gameplay | upgrade.magnet.desc | 코인을 끌어오는 범위가 {percent}% 늘어납니다. | Coin pickup range +{percent}%. | 예 | {percent}=정수 |
| Gameplay | shrine.prompt | 코인 {price}개를 바쳐 강해질까요? | Offer {price} coins for power? | 예 | 21장 제단. 용어집 "제단" |
| Gameplay | wave.warning.elite | 강한 적이 다가온다… | Something strong approaches… | | 22장 경고, max 24 |
| Gameplay | wave.warning.boss | 보스 출현! | Boss Incoming! | | 22장 경고 |
| System | error.scene_load_failed | 화면을 불러오지 못했습니다.\n게임을 다시 시작하거나 최신 버전으로 업데이트해 주세요. | The screen failed to load.\nPlease restart the game or update to the latest version. | | 09장 오류, \n=줄바꿈 |
| System | language.name | 한국어 | English | | **각 언어로 자기 이름**. 언어 선택 UI에 표시 |

`language.name`은 요령입니다. 각 언어 테이블에 "그 언어로 쓴 자기 이름"을 넣으면, 언어 선택 UI가 테이블에서 이름을 꺼내 올 수 있습니다. 언어 목록에서 항상 그 언어 자신의 표기("English", "한국어")를 보여주는 것이 관례입니다. 영어를 모르는 사람도 자기 언어를 찾을 수 있어야 하니까요.

### 3단계: 정적 텍스트 — Localize String Event

1. Title 씬의 "시작" 버튼 텍스트(TextMeshPro - Text (UI))를 선택합니다.
2. Inspector에서 TMP 컴포넌트 이름 옆 메뉴(⋮) → **Localize**를 누르면 `Localize String Event` 컴포넌트가 추가되고, Update String 이벤트가 TMP의 `text`에 연결됩니다(메뉴가 없으면 Add Component → Localize String Event 후 이벤트에 `TextMeshProUGUI.text`를 직접 연결).
3. String Reference에서 `UI / title.button.start`를 고릅니다.
4. 타이틀·설정·레벨업 창 제목·결과 버튼의 **정적 문구 전부**에 반복합니다.
5. Game 뷰 오른쪽 위에 생기는 **Locale 메뉴**(Localization의 Game View Menu)에서 en을 고르면 Play 중에 즉시 바뀌는지 확인합니다. 프리팹 안의 텍스트는 씬 인스턴스가 아니라 **프리팹 원본**에서 설정합니다.

### 4단계: 동적 텍스트 — 11장 코드 교체

**ResultView (11장) 교체.** 필드와 `Awake`·`Show`·`CountUp`을 바꿉니다. 나머지(`SetVisible`, 이벤트)는 그대로입니다.

```csharp
// ResultView.cs (11장) — using 추가
using UnityEngine.Localization;
using UnityEngine.Localization.SmartFormat.PersistentVariables;

// 필드 추가
    [Header("Localization (32장)")]
    [SerializeField] private LocalizedString clearedTitle;   // UI/result.title.cleared
    [SerializeField] private LocalizedString failedTitle;    // UI/result.title.failed
    [SerializeField] private LocalizedString timeLabel;      // UI/result.time   (Smart, {time})
    [SerializeField] private LocalizedString coinsFormat;    // UI/result.coins  (Smart 아님, {0})

    private readonly StringVariable timeVariable = new StringVariable();
    private string coinsTemplate = "{0}";

// Awake에 추가 (기존 내용 뒤)
        timeLabel["time"] = timeVariable;

// 메서드 추가 — 구독은 OnEnable/OnDisable 짝으로
    private void OnEnable()
    {
        timeLabel.StringChanged += OnTimeLabelChanged;      // 언어 변경·변수 변경 시 자동 갱신
        coinsFormat.StringChanged += OnCoinsFormatChanged;  // 템플릿만 받아 둠
    }

    private void OnDisable()
    {
        timeLabel.StringChanged -= OnTimeLabelChanged;
        coinsFormat.StringChanged -= OnCoinsFormatChanged;
    }

    private void OnTimeLabelChanged(string value) => timeText.text = value;
    private void OnCoinsFormatChanged(string value) => coinsTemplate = value;

// Show 교체
    public void Show(bool cleared, float survivedSeconds, int coins)
    {
        titleText.text = (cleared ? clearedTitle : failedTitle).GetLocalizedString();
        int total = Mathf.FloorToInt(survivedSeconds);
        timeVariable.Value = $"{total / 60:00}:{total % 60:00}";            // 숫자 서식은 코드가, 문장은 번역이
        SetVisible(true);

        StopAllCoroutines();
        StartCoroutine(CountUp(coins));
        EventSystem.current.SetSelectedGameObject(retryButton.gameObject);
    }

// CountUp 안의 두 SetText 호출 교체
            coinText.SetText(coinsTemplate, Mathf.RoundToInt(target * p));
        coinText.SetText(coinsTemplate, target);
```

- `StringChanged`는 **구독하는 순간** 현재 번역으로 한 번 호출되고, 이후 언어가 바뀌거나 로컬 변수 값이 바뀔 때마다 다시 호출됩니다. 구독자가 있는 `LocalizedString`은 전역 언어 변경 이벤트에 연결되므로, 해제하지 않으면 씬이 내려간 뒤에도 파괴된 `TMP_Text`에 접근하려다 `MissingReferenceException`이 납니다. 그래서 람다가 아니라 메서드로 구독하고 `OnDisable`에서 반드시 해제합니다. `ResultView`의 `CanvasGroup`은 숨길 때 오브젝트를 끄지 않으므로(11장 `SetVisible`), 구독은 씬이 살아 있는 동안 유지됩니다.
- `coinsTemplate`은 **Smart가 아닌** 항목(`획득 코인 {0}`)이라 TMP `SetText`의 `{0}` 문법과 그대로 호환됩니다. 번역가에게 "`{0}` 유지"를 주석으로 전달한 이유입니다.

**HudView (11장) 교체.** 레벨 서식만 테이블에서 받습니다.

```csharp
// HudView.cs (11장) — using 추가
using UnityEngine.Localization;

// 필드 추가
    [SerializeField] private LocalizedString levelFormat;    // UI/hud.level  (Smart 아님, "Lv {0}")
    private string levelTemplate = "Lv {0}";
    private int lastLevel = 1;

    private void OnEnable()  => levelFormat.StringChanged += OnLevelFormatChanged;
    private void OnDisable() => levelFormat.StringChanged -= OnLevelFormatChanged;

    private void OnLevelFormatChanged(string template)
    {
        levelTemplate = template;
        levelText.SetText(levelTemplate, lastLevel);          // 언어가 바뀌면 즉시 다시 그림
    }

// SetExperience 교체
    public void SetExperience(float ratio, int level)
    {
        expFill.fillAmount = Mathf.Clamp01(ratio);
        lastLevel = level;
        levelText.SetText(levelTemplate, level);              // 할당 0 유지 (02·11장)
    }
```

**UpgradeData (11장) 교체.** 문자열 필드를 `LocalizedString`으로 바꿉니다. 필드 이름을 바꾸면 기존 에셋의 값이 사라지므로, **옮기기 전에 기존 텍스트를 2단계 표(Gameplay 테이블)에 모두 입력**해 두고 교체합니다.

```csharp
// Assets/_CoinRush/Scripts/UI/UpgradeData.cs  — 32장 버전
using UnityEngine;
using UnityEngine.Localization;

[CreateAssetMenu(menuName = "CoinRush/Upgrade Data", fileName = "Upgrade_")]
public class UpgradeData : ScriptableObject
{
    public LocalizedString displayName;    // Gameplay/upgrade.<id>.name
    public LocalizedString description;    // Gameplay/upgrade.<id>.desc
    public Sprite icon;
}
```

```csharp
// UpgradeCardView.cs (11장) — Bind의 두 줄 교체
        title.text = data.displayName.GetLocalizedString();
        description.text = data.description.GetLocalizedString();
```

`GetLocalizedString()`은 동기 호출입니다. 1단계에서 테이블 프리로드를 켰고 5단계에서 부트스트랩이 초기화 완료를 기다리므로, 레벨업 창이 열리는 시점에는 이미 테이블이 메모리에 있습니다. 레벨업 창이 열린 상태에서 언어를 바꾸는 경우는 없으므로(일시정지 메뉴에서 언어 변경 불가 — 6단계) 구독 없이 열릴 때 한 번 읽습니다.

같은 방식으로 나머지를 교체합니다.

| 장 | 코드 | 교체 |
|---|---|---|
| 22 | `WaveEvent.warningText` (string) | `public LocalizedString warningText;` → `WaveWarningView`에서 `label.text = e.warningText.GetLocalizedString();`. 20장 편집기의 경고 필드 표시도 함께 확인 |
| 08 | `ActionPromptLabel.format` (string) | `LocalizedString` + `StringVariable key` 로 `{key}` 전달, 기존 `string.Format` 대신 `key.Value = keyName` |
| 09 | `ShowError("화면을...")` | `GameFlow`에 `[SerializeField] LocalizedString sceneLoadFailed;` → `ShowError(sceneLoadFailed.GetLocalizedString())`. 로드 실패 시점에도 System 테이블은 프리로드돼 있음 |
| 24 | 동의 패널 문구 | System 테이블. 법적 의미가 있으므로 번역 검토를 28장 체크리스트에 추가 |
| 26 | 업적 이름 | 코드가 아니라 **Steamworks 웹에서 언어별 입력**(26장 3단계). 게임 테이블과 용어를 맞춤 |

### 5단계: 언어 저장 — SaveData 마이그레이션과 LanguageService

**SaveData에 언어 필드 추가.** 빈 문자열은 "아직 고르지 않음(자동)"입니다.

```csharp
// SaveData.cs (10장) — CurrentVersion 올리고, settings 클래스에 필드 추가
    public const int CurrentVersion = 4;

[Serializable]
public class SettingsData
{
    public float bgmVolume = 0.8f;
    public float sfxVolume = 0.8f;
    public string language = "";   // 32장: "" = 자동, "ko", "en" ...
}
```

```csharp
// SaveMigrator.cs (10장) — Steps에 { 3, V3ToV4 } 추가, 메서드 추가
    // 1.3 (v3 → v4): settings.language 추가. 기존 플레이어는 "자동"에서 시작
    private static void V3ToV4(JObject root)
    {
        var settings = (JObject)root["settings"];   // v3에는 항상 있음 (V2ToV3가 만듦)
        settings["language"] ??= "";
    }
```

기본값이 안전한 필드 추가라 마이그레이션 없이도 로드는 되지만, 10장 규칙("구조를 바꾸면 버전을 올리고 테스트로 고정")을 지킵니다. 테스트를 추가합니다.

```csharp
// SaveMigrationTests.cs (10장) — 메서드 추가
    [Test]
    public void V3_Gets_Empty_Language_And_Keeps_Volume()
    {
        JObject root = JObject.Parse(@"{ ""version"": 3, ""coins"": 10, ""upgrades"": {}, ""stats"": {},
            ""unlockedCharacters"": [""knight""], ""settings"": { ""bgmVolume"": 0.3, ""sfxVolume"": 0.6 } }");

        SaveMigrator.MigrateToCurrent(root);
        SaveData data = root.ToObject<SaveData>();

        Assert.AreEqual("", data.settings.language);
        Assert.AreEqual(0.3f, data.settings.bgmVolume, 0.001f);
    }
```

**LanguageService.** 언어 적용·변경·저장을 한곳에 모읍니다.

```csharp
// Assets/_CoinRush/Scripts/Localization/LanguageService.cs
#if !(UNITY_STANDALONE_WIN || UNITY_STANDALONE_LINUX || UNITY_STANDALONE_OSX || STEAMWORKS_WIN || STEAMWORKS_LIN_OSX)
#define DISABLESTEAMWORKS
#endif

using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;
#if !DISABLESTEAMWORKS
using Steamworks;
#endif

public static class LanguageService
{
    // Steam API 언어 코드 → Locale 코드 (지원 언어를 늘리면 여기에 추가)
    private static readonly Dictionary<string, string> SteamToLocale = new()
    {
        { "koreana", "ko" },
        { "english", "en" },
        // { "japanese", "ja" }, { "schinese", "zh-Hans" },
    };

    public static bool IsReady => LocalizationSettings.InitializationOperation.IsDone;

    public static IReadOnlyList<Locale> Available => LocalizationSettings.AvailableLocales.Locales;

    /// <summary>부트스트랩에서 한 번. SteamManager.Awake(세이브 폴더 결정) 이후에 호출해야 한다.</summary>
    public static async Task InitializeAsync()
    {
        await LocalizationSettings.InitializationOperation.Task;   // Startup Selector가 기본 언어를 이미 골라 둠

        SaveData save = SaveSystem.Load();
        // 플레이어가 고른 언어가 최우선, 없으면(첫 실행) Steam 언어
        Locale chosen = Find(save.settings.language) ?? FindSteamLanguage();
        if (chosen != null) Apply(chosen);
        // 둘 다 없으면 Startup Selector 결과(명령행 → 시스템 언어 → en)를 그대로 사용
        // 저장은 하지 않음: 플레이어가 직접 고르기 전까지는 "자동"으로 남겨 둔다
    }

    /// <summary>설정 화면에서 호출. 즉시 적용하고 세이브에 기록한다.</summary>
    public static void SetLanguage(Locale locale)
    {
        if (locale == null) return;
        Apply(locale);

        SaveData save = SaveSystem.Load();
        save.settings.language = locale.Identifier.Code;
        SaveSystem.Save(save);
    }

    private static void Apply(Locale locale)
    {
        if (LocalizationSettings.SelectedLocale == locale) return;
        LocalizationSettings.SelectedLocale = locale;               // Localize String Event·StringChanged가 모두 갱신됨
    }

    private static Locale Find(string code)
    {
        if (string.IsNullOrEmpty(code)) return null;
        return LocalizationSettings.AvailableLocales.GetLocale(code);   // string → LocaleIdentifier 암시 변환
    }

    private static Locale FindSteamLanguage()
    {
#if !DISABLESTEAMWORKS
        if (!SteamManager.Initialized) return null;
        string steamLanguage = SteamApps.GetCurrentGameLanguage();
        if (SteamToLocale.TryGetValue(steamLanguage, out string code)) return Find(code);
        Debug.Log($"[Language] 지원하지 않는 Steam 언어 '{steamLanguage}' — 기본 선택 사용");
#endif
        return null;
    }
}
```

**09장 GameFlow 연결.** `Start`를 비동기로 바꿔, 첫 화면을 띄우기 전에 언어를 정합니다. 바뀌는 메서드만 보입니다.

```csharp
// GameFlow.cs (09장) — Start 교체
    private async void Start()
    {
        try { await LanguageService.InitializeAsync(); }   // SteamManager(-1000) Awake 이후라 계정별 세이브를 읽음
        catch (Exception e) { Debug.LogException(e); }     // 현지화 초기화 실패가 게임 시작을 막지 않게
        ChangeState(GetInitialState());
    }
```

`GameFlow.cs` 맨 위에 `using System;`이 없다면 추가합니다. 첫 씬을 로드하기 전에 언어가 정해지므로 타이틀이 다른 언어로 잠깐 보였다 바뀌는 일이 없습니다.

### 6단계: 설정 화면의 언어 선택 (게임패드 대응)

`TMP_Dropdown`은 게임패드로 열고 닫기가 번거롭습니다. 11장의 포커스 구조에 맞게 **좌우 화살표 버튼 + 이름 표시** 방식으로 만듭니다.

```csharp
// Assets/_CoinRush/Scripts/Localization/LanguageOptionView.cs
using TMPro;
using UnityEngine;
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;
using UnityEngine.UI;

public class LanguageOptionView : MonoBehaviour
{
    [SerializeField] private Button previousButton;
    [SerializeField] private Button nextButton;
    [SerializeField] private TMP_Text nameLabel;
    [SerializeField] private LocalizedString languageName;   // System/language.name — 각 언어로 쓴 자기 이름

    private void OnEnable()
    {
        previousButton.onClick.AddListener(Previous);
        nextButton.onClick.AddListener(Next);
        if (LanguageService.IsReady) Refresh();   // 설정 화면은 부트스트랩 초기화 이후에만 열림
    }

    private void OnDisable()
    {
        previousButton.onClick.RemoveListener(Previous);
        nextButton.onClick.RemoveListener(Next);
    }

    private void Previous() => Step(-1);
    private void Next() => Step(+1);

    private void Step(int direction)
    {
        var locales = LanguageService.Available;
        if (locales.Count == 0) return;

        int index = IndexOf(LocalizationSettings.SelectedLocale);
        int next = (index + direction + locales.Count) % locales.Count;   // 끝에서 처음으로 순환
        LanguageService.SetLanguage(locales[next]);
        Refresh();
    }

    private void Refresh()
    {
        if (LocalizationSettings.SelectedLocale == null) return;
        // 선택된 언어의 테이블에서 "자기 이름"을 꺼냄 → "English", "한국어"
        nameLabel.text = languageName.GetLocalizedString();
    }

    private static int IndexOf(Locale locale)
    {
        var locales = LanguageService.Available;
        for (int i = 0; i < locales.Count; i++)
            if (locales[i] == locale) return i;
        return 0;
    }
}
```

에디터 구성:

1. 12장 설정 패널(PopupCanvas)에 행 `LanguageRow`를 추가합니다: 왼쪽 라벨(Localize String Event: `menu.settings.language`), `◀` 버튼, 이름 텍스트, `▶` 버튼.
2. `LanguageOptionView`를 붙이고 연결합니다. `languageName`은 `System / language.name`.
3. 게임패드 사용자를 위해 행 전체를 하나의 Selectable로 만들고 좌우 입력으로 바꾸고 싶다면 연습 문제 2를 보세요. 이 단계에서는 버튼 두 개를 Navigation(Explicit)으로 위아래 슬라이더와 연결합니다.
4. **일시정지 메뉴에서는 이 행을 숨깁니다.** 레벨업 카드처럼 열릴 때 한 번 읽은 텍스트가 옛 언어로 남는 경우를 원천 차단합니다(타이틀 설정에서만 변경).
5. 의사 현지화 Locale(8단계)은 `Available` 목록에 들어가지 않도록 Localization Settings에 추가하지 않고, Game View Menu로만 씁니다.

### 7단계: 폰트 글리프 — 테이블에서 글자 추출해 Static 아틀라스 다시 굽기

11장 3단계의 "게임에 쓰인 문자열에서 추출"을 도구로 자동화합니다.

```csharp
// Assets/_CoinRush/Scripts/Editor/LocalizationCharsetExporter.cs
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using TMPro;
using UnityEditor;
using UnityEditor.Localization;
using UnityEngine;
using UnityEngine.Localization.Tables;

public static class LocalizationCharsetExporter
{
    const string OutputPath = "Assets/_CoinRush/Fonts/charset_from_tables.txt";
    const string BaseCharset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";

    [MenuItem("Coin Rush/Localization/Export Charset From Tables")]
    public static void Export()
    {
        var chars = new SortedSet<char>(BaseCharset);
        int entryCount = 0;

        foreach (StringTableCollection collection in LocalizationEditorSettings.GetStringTableCollections())
        foreach (StringTable table in collection.StringTables)
        foreach (StringTableEntry entry in table.Values)
        {
            if (string.IsNullOrEmpty(entry.Value)) continue;
            entryCount++;
            foreach (char c in entry.Value)
                if (!char.IsControl(c)) chars.Add(c);          // \n 등 제어 문자는 제외
        }

        File.WriteAllText(OutputPath, new string(chars.ToArray()), new UTF8Encoding(false));
        AssetDatabase.ImportAsset(OutputPath);
        Debug.Log($"[Charset] 항목 {entryCount}개에서 글자 {chars.Count}개 → {OutputPath}");
    }

    [MenuItem("Coin Rush/Localization/Check Missing Glyphs (Default Font)")]
    public static void CheckMissing()
    {
        TMP_FontAsset font = TMP_Settings.defaultFontAsset;   // 11장 7번: Static 에셋을 기본 폰트로 지정
        if (font == null) { Debug.LogError("[Charset] TMP Settings에 기본 폰트가 없습니다."); return; }
        if (!File.Exists(OutputPath)) Export();

        string text = File.ReadAllText(OutputPath, Encoding.UTF8);
        if (font.HasCharacters(text, out List<char> missing))
            Debug.Log($"[Charset] '{font.name}'에 모든 글자({text.Length}자)가 있습니다.");
        else
            Debug.LogWarning($"[Charset] '{font.name}' Static 아틀라스에 없는 글자 {missing.Count}개 " +
                             $"(폴백으로 표시됨): {new string(missing.Take(80).ToArray())}");
    }
}
```

사용 순서:

1. `Coin Rush/Localization/Check Missing Glyphs`를 실행해 Static 아틀라스에 없는 글자를 봅니다. 영어 번역의 `…`, `—`, `’` 같은 문장부호가 자주 걸립니다.
2. `Window > TextMeshPro > Font Asset Creator`에서 11장과 같은 설정으로, Character Set을 `Characters from File`로 두고 **KS X 1001 목록 파일과 `charset_from_tables.txt`를 합친 파일**을 지정해 다시 굽습니다. 같은 에셋에 덮어써야(Save) 참조가 유지됩니다.
3. 다시 검사해 누락 0을 확인합니다. 문자열을 추가·번역할 때마다 1~3을 반복합니다. (`HasCharacters(string, out List<char>)`는 이 폰트 에셋 자신의 글자만 검사합니다. 폴백까지 포함하는 오버로드는 TMP 버전에 따라 다르니 설치된 버전의 API를 확인하세요.)

### 8단계: 의사 현지화와 넘침 검사

1. `Assets > Create > Localization > Pseudo-Locale`로 `Pseudo (ko)`를 만들고, Source Locale을 `ko`로 둡니다. 기본 방법(Accenter·Expander·Encapsulator)을 그대로 두고 Expander 비율을 40%로 올립니다.
2. Play → Game View의 Locale 메뉴에서 Pseudo-Locale을 고릅니다.
3. 모든 화면(타이틀 → 설정 → 게임 → 레벨업 → 결과)을 거치며 봅니다.
   - 괄호 `[ ]`로 감싸이지 **않은** 한국어가 보이면 → 하드코딩 문자열. 테이블로 옮깁니다.
   - 괄호의 닫는 쪽이 안 보이면 → 잘림(넘침).
   - □가 보이면 → 글리프 누락(단, 의사 현지화의 악센트 문자는 게임에 실제로 쓰이지 않으니 이 목적의 누락은 무시해도 됩니다).

눈으로 놓치는 넘침을 찾는 검사 도구입니다. 현재 화면의 모든 TMP 텍스트를 훑어 **줄바꿈 폭 기준으로 필요한 높이**가 영역보다 크거나 TMP가 넘침을 보고한 텍스트를 기록합니다.

```csharp
// Assets/_CoinRush/Scripts/Debug/TextOverflowScanner.cs
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

// 개발 빌드 전용: F10을 누르면 활성화된 모든 TMP 텍스트의 넘침을 검사해 로그로 남김
public class TextOverflowScanner : MonoBehaviour
{
    [SerializeField] private float tolerance = 1f;   // 픽셀 오차 허용

    private void Awake()
    {
        if (!Debug.isDebugBuild) Destroy(this);
    }

    private void Update()
    {
        if (Keyboard.current != null && Keyboard.current.f10Key.wasPressedThisFrame)
            Scan();
    }

    public void Scan()
    {
        TMP_Text[] texts = FindObjectsByType<TMP_Text>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);
        var sb = new StringBuilder();
        int problems = 0;

        foreach (TMP_Text t in texts)
        {
            if (string.IsNullOrEmpty(t.text) || !t.isActiveAndEnabled) continue;
            t.ForceMeshUpdate();

            Rect rect = t.rectTransform.rect;
            Vector2 needed = t.GetPreferredValues(t.text, rect.width, Mathf.Infinity);   // 현재 폭에서 필요한 크기
            bool tooTall = needed.y > rect.height + tolerance;
            bool reported = t.isTextOverflowing;

            if (!tooTall && !reported) continue;
            problems++;
            sb.AppendLine($"- {t.transform.parent?.name}/{t.name}  \"{t.text.Replace("\n", " ")}\"  영역 {rect.width:0}×{rect.height:0}, 필요 높이 {needed.y:0}" +
                          (t.enableAutoSizing ? $", AutoSize 최종 {t.fontSize:0.#}pt" : ""));
        }

        string locale = UnityEngine.Localization.Settings.LocalizationSettings.SelectedLocale?.Identifier.Code ?? "?";
        if (problems == 0) Debug.Log($"[Overflow] ({locale}) 텍스트 {texts.Length}개 검사 — 넘침 없음");
        else Debug.LogWarning($"[Overflow] ({locale}) 넘침 의심 {problems}개\n{sb}");
    }
}
```

- 이 검사는 **휴리스틱**입니다. 줄바꿈을 끈 한 줄 텍스트나 Overflow 모드 설정에 따라 실제 표시와 다를 수 있으니, 경고가 나온 곳은 눈으로 확인합니다.
- 부트스트랩 씬의 디버그 오브젝트에 붙이고, en과 Pseudo-Locale에서 **화면마다 F10**을 누릅니다. 결과 로그를 10단계 검수 기록에 붙입니다.

자주 나오는 수정은 버튼 폭을 가장 긴 언어 기준으로 넓히기, 설명 영역에 한 줄 여유 주기, 드물게 뜨는 창(제단)에만 Auto Size(최소 크기 지정) 허용입니다.

### 9단계: 번역 전달 패키지

1. Localization Tables 창에서 `UI` 컬렉션 선택 → 오른쪽 위 메뉴(⋮) → **Export → CSV (With Comments)** → `Docs/l10n/export/UI.csv`. `Gameplay`, `System`도 같게.
2. 용어집을 만듭니다(`Docs/l10n/glossary.md`).

| 용어 (ko) | en | 설명 | 금지 번역 |
|---|---|---|---|
| 코인 | Coin | 경험치이자 화폐. 절대 "Gold"로 쓰지 않음 | Gold, Money |
| 코인 제단 / 제단 | Coin Shrine / Shrine | 판 안에서 코인을 바쳐 강화하는 장소 | Altar, Shop |
| 영구 강화 | Upgrades | 판 밖에서 코인으로 사는 영구 성장 | Perks |
| 판 | Run | "한 판" = one run | Game, Round |
| 쓰러지다 | Fall | 사망 표현. "Die"보다 부드럽게 | Die, Killed |

3. 톤 가이드(반 페이지): "영어는 짧고 명령형(Play, Try Again). 설명문은 2인칭 you. 유머 없음. 한국어 원문의 존댓말 느낌은 영어에서 과하게 공손하게 만들지 않음."
4. 화면 스크린샷: 각 화면을 Pseudo-Locale 상태로도 한 장씩 찍어 **어디에 어떤 텍스트가 들어가는지** 보여줍니다.
5. 전달 메일에 "`{0}`, `{time}`, `{kills:plural:...}` 같은 중괄호 부분은 번역하지 말고 위치만 옮겨 주세요. plural의 `|` 앞은 1개일 때, 뒤는 여러 개일 때 형태입니다"를 명시합니다.

번역을 받으면:

1. 받은 CSV를 `Docs/l10n/import/`에 두고, **Import → CSV (Merge)** 로 들여옵니다.
2. `Check Missing Glyphs` → 필요하면 폰트 다시 굽기(7단계).
3. en으로 전 화면 F10 검사(8단계).
4. Smart String 문법 오류는 해당 문자열이 표시될 때 콘솔에 오류로 나옵니다. 결과 화면·제단·업그레이드 카드처럼 변수가 있는 화면을 **반드시 한 번씩** 띄웁니다.

### 10단계: 게임 안 검수(LQA)와 출시 체크리스트

검수자(원어민 친구, 커뮤니티 자원자, 유료 검수자)에게는 33장의 Steam beta 브랜치 빌드와 함께 **화면 순서 체크리스트**를 줍니다: 타이틀·설정 → 첫 판 1분(일시정지 안내·HUD) → 레벨업 창 5회(업그레이드 16종 용어·2줄 이내) → 제단(가격 변수 위치) → 엘리트·보스 경고 → 결과(생존·사망 각 1회) → 오류·동의 화면(법적 문구 정확성). 문제는 "화면 / 키 / 현재 문장 / 제안 / 사유" 다섯 칸으로 받습니다.

출시 전 현지화 체크리스트:

- [ ] Pseudo-Locale에서 괄호 없는 문자열 0개 (하드코딩 없음)
- [ ] ko·en 전 화면 F10 넘침 경고 0개 또는 눈으로 확인 후 허용 기록
- [ ] `Check Missing Glyphs` 누락 0
- [ ] String Database의 Missing Translation 처리를 출시 설정(폴백 언어 표시)으로 변경, en 테이블 빈 항목 0
- [ ] 19장 빌드 스크립트로 Addressables 포함 빌드 후, **빌드에서** 언어 전환·재실행 유지 확인
- [ ] 명령행 `-language=en`으로 실행 시 영어로 시작 (세이브에 언어가 없을 때)
- [ ] Steam 클라이언트 언어를 English로 바꾸고 새 계정(세이브 없음)으로 실행 시 영어로 시작
- [ ] 26장 업적 이름·설명의 ko/en 입력과 게임 용어집 일치
- [ ] 28장 라이선스 대장에 추가 폰트 기록

**스토어 현지화와 연결.** Steamworks의 스토어 편집 화면에서 지원 언어를 **Interface(인터페이스) / Full Audio(음성) / Subtitles(자막)** 로 나눠 표기합니다. 코인 러시는 음성이 없으므로 한국어·영어 모두 **Interface만** 체크합니다. 실제로 지원하지 않는 항목을 체크하면 부정 리뷰와 환불의 직접 원인이 됩니다.

게임 밖에서 언어를 맞출 곳은 스토어 짧은·상세 설명(26장 문안), 언어별 스크린샷(UI 언어가 보이므로 언어별 업로드), 트레일러 자막(27장), 업적 이름·설명(26장 3단계), 패치노트·공지(33장 핫픽스 루틴에서 두 언어 동시 게시)입니다.

스토어 문안의 용어가 게임과 다르면("Gold"를 줍는다고 써 놓고 게임에서는 "Coin") 신뢰가 떨어집니다. 26장 스토어 문안을 쓸 때 이 장의 용어집을 먼저 확정합니다. 추가 언어를 결정할 때는 Valve의 권고처럼 **지역별 위시리스트·판매 데이터**를 보고, 29장 포스트모템의 교훈("Coming Soon 공개 시점부터 지역별 위시리스트로 언어 결정")을 따릅니다.

### 확인하기

- Game View Locale 메뉴에서 ko ↔ en을 바꾸면 타이틀·설정·HUD 레벨·결과 화면의 모든 글자가 즉시 바뀐다. HUD 레벨은 숫자를 유지한 채 서식만 바뀐다.
- 설정에서 English를 고르고 게임을 종료 → 재실행하면 영어로 시작한다. `save.json`을 열면 `"language": "en"`과 `"version": 4`가 보인다.
- `save.json`을 지우고 `-language=en` 인수로 실행하면 영어로 시작하고, 세이브의 language는 여전히 `""`이다.
- Pseudo-Locale로 전 화면을 돌려도 괄호 없는 한국어가 없고, F10 로그에 넘침 경고가 없다.
- `Coin Rush/Localization/Check Missing Glyphs`가 누락 0을 보고한다.
- EditMode 테스트(`V3_Gets_Empty_Language_And_Keeps_Volume` 포함)가 모두 통과하고, **PC 빌드**에서도 전환·저장이 똑같이 동작한다.

## 흔한 실수

1. **증상**: 에디터에서는 번역이 보이는데 빌드에서는 키 이름이나 빈 문자열이 나온다. → **원인**: 테이블이 Addressables로 로드되는데 플레이어 빌드 전에 Addressables 콘텐츠 빌드를 하지 않음. → **해결**: 19장 `BuildScripts`처럼 `AddressableAssetSettings.BuildPlayerContent`를 빌드 전에 호출하고, 빌드에서 언어 전환을 확인합니다.
2. **증상**: Steam 계정을 바꾸면 언어가 다른 계정의 선택으로 나오거나, 첫 실행 이후 언어가 저장되지 않는다. → **원인**: Startup Selector에서 `SaveSystem.Load()`를 불러 `SteamManager.Awake`의 계정별 폴더 설정보다 먼저 세이브를 캐시함. 또는 Player Pref 선택기와 세이브 파일을 동시에 사용. → **해결**: 세이브 기반 적용은 부트스트랩(`GameFlow.Start`)에서, Player Pref 선택기는 제거합니다.
3. **증상**: 영어로 바꿨는데 레벨업 카드·경고 문구 일부만 한국어로 남는다. → **원인**: `GetLocalizedString()`으로 한 번 읽고 구독하지 않은 텍스트가 언어 변경 전에 이미 표시됨, 또는 프리팹 인스턴스에만 Localize 설정. → **해결**: 화면이 열릴 때마다 다시 읽거나 `StringChanged` 구독, 언어 변경은 타이틀에서만 허용, 프리팹 원본에서 설정.
4. **증상**: "적 {kills}마리 처치"가 그대로 출력되거나 콘솔에 형식 오류가 난다. → **원인**: 항목의 Smart 체크를 안 함, 변수를 등록하지 않음, 번역가가 중괄호 안을 번역함. → **해결**: 변수가 있는 항목은 Smart 켜기, 코드에서 인덱서로 변수 등록, CSV 주석과 메일로 "중괄호 유지"를 전달하고 변수 화면을 모두 띄워 확인합니다.
5. **증상**: 영어 문장부호(… — ’)나 새 한글이 □로 나오거나, 폰트 에셋이 계속 git diff에 뜬다. → **원인**: Static 아틀라스에 없는 글자가 Dynamic 폴백으로 추가됨. → **해결**: 테이블에서 글자를 추출해 Static 아틀라스를 다시 굽고, 번역 반영마다 누락 검사를 반복합니다.

## 연습 문제

**1. ★☆☆ 처치 수와 복수형**
결과 화면에 `UI/result.kills`(Smart, `{kills}`)를 표시하세요. `ResultView.Show`에 처치 수 인자를 추가하고, en에서 1마리일 때 `1 enemy defeated`, 여러 마리일 때 `120 enemies defeated`가 나오는지 확인합니다.

<details>
<summary>힌트·해설</summary>

`timeLabel`과 같은 패턴입니다. `[SerializeField] LocalizedString killsLabel;`과 `IntVariable kills`를 두고 `Awake`에서 `killsLabel["kills"] = kills;`, `OnEnable/OnDisable`에서 `StringChanged` 구독·해제, `Show`에서 `kills.Value = n;`. 처치 수는 04장 `ResultState`가 판 기록(10장 `RunRecorder` 등)에서 넘깁니다. ko 항목은 복수형이 필요 없어 `적 {kills}마리 처치`로 충분합니다. 결과가 `{kills:plural:...}` 문자 그대로 보이면 en 항목의 Smart 체크가 꺼져 있는 것입니다.

</details>

**2. ★★☆ 업그레이드 설명의 변수 연결**
`upgrade.magnet.desc`는 `{percent}` 변수를 씁니다. 23장의 성장 테이블 값(레벨별 증가율)을 카드에 보여주려면 `UpgradeData`와 `UpgradeCardView`를 어떻게 바꿔야 할지 설계하고 구현하세요. 레벨마다 숫자가 달라야 합니다.

<details>
<summary>힌트·해설</summary>

`UpgradeData`에 "다음 레벨의 수치를 계산하는" 필드나 메서드(예: `int PercentForLevel(int level)`)를 두고, 카드 뷰에서 변수를 넣습니다.

```csharp
// UpgradeCardView.Bind(UpgradeData data, int nextLevel, Action onClick)
var percent = new IntVariable { Value = data.PercentForLevel(nextLevel) };
data.description["percent"] = percent;              // 에셋의 LocalizedString에 변수 등록
description.text = data.description.GetLocalizedString();
```

주의: `UpgradeData`는 에셋이라 **모든 카드가 같은 `LocalizedString` 인스턴스를 공유**합니다. 카드 3장이 같은 업그레이드를 동시에 보여줄 일은 없지만, 공유 상태를 에셋에 쓰는 것이 불안하면 `GetLocalizedString(params object[] arguments)`에 `new Dictionary<string, object> { ["percent"] = value }`를 인수로 넘기는 방법도 있습니다(Smart String에서 `{percent}`는 인수 딕셔너리의 키로 찾음 — 설치 버전에서 동작을 확인하세요). 변수가 없는 설명도 있으니 모든 설명 항목을 Smart로 두어도 무방합니다.

</details>

**3. ★★★ 일본어 추가 시뮬레이션 (확장 과제)**
29장의 결정("지역별 위시리스트를 보고 언어 추가")에 따라 일본어를 추가한다고 가정하고 전체 작업을 수행하세요. Locale 추가, 폰트 전략(폴백 체인 vs `LocalizedTmpFont`) 결정과 근거, Steam 언어 매핑 추가, 번역 전달 패키지(CSV·용어집 일본어 열·톤 가이드), 의사 현지화 대신 기계 번역 초안을 넣은 상태에서의 넘침·글리프 검사, 스토어 언어 표기까지 포함합니다. 작업 시간을 기록해 34장 현금흐름표의 "언어 추가 비용" 행에 쓰세요.

<details>
<summary>힌트·해설</summary>

- 코드 변경은 `LanguageService.SteamToLocale`에 `{ "japanese", "ja" }` 한 줄이어야 합니다. 그 외 코드 수정이 필요했다면 국제화가 덜 된 곳이니 기록합니다.
- 폰트: 한글 Pretendard에 가나·한자가 없으므로 Noto Sans JP 계열(OFL)을 Static(JIS 1·2수준 등 필요한 글자 + 테이블 추출 글자)으로 굽고 폴백 체인에 넣는 것이 가장 단순합니다. 한·중·일 한자 글자 모양 차이가 신경 쓰이면 일본어 Locale에서만 `LocalizedTmpFont`로 폰트를 교체합니다. 아틀라스 메모리 증가를 18장 방식으로 기록합니다.
- 일본어는 띄어쓰기가 없어 TMP 줄바꿈이 어색할 수 있습니다. TMP Settings의 줄바꿈 규칙(Line Breaking Rules)을 확인하고, 긴 설명은 수동 줄바꿈 여부를 번역가와 합의합니다.
- 비용 행 예: 번역비(견적), 검수비, 개발 시간(폰트·넘침 수정·스토어 문안), 스토어 스크린샷 재촬영. 34장에서 "일본어권 추가 판매 추정 × 순수입"과 비교해 결정합니다.

</details>

## 셀프 체크

**1. HUD 레벨 표시는 `LocalizedString`의 Smart 변수로 만들지 않고 "템플릿 + `SetText`"로 만든 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

레벨·타이머·코인 수는 자주 바뀌는 값이라 매번 번역 시스템을 거쳐 문자열을 만들면 새 `string`이 계속 할당돼 02장의 할당 0 원칙이 깨집니다. 번역이 필요한 것은 "Lv {0}" 같은 틀뿐이므로, 언어가 바뀔 때만 틀을 받아 두고 숫자는 TMP의 `SetText(format, number)`로 넣으면 할당 없이 번역된 서식을 쓸 수 있습니다. 이를 위해 해당 항목은 Smart가 아닌 일반 항목으로 두고 `{0}` 기호를 유지하도록 번역가에게 전달합니다.

</details>

**2. 언어 선택을 `Player Pref Locale Selector`가 아니라 10장 세이브에 저장한 이유와, 그때 생기는 실행 순서 문제는?**

<details>
<summary>모범 답안</summary>

Steam Auto-Cloud가 세이브 폴더를 동기화하므로 다른 PC에서도 같은 언어로 이어 할 수 있고, 설정 저장소가 한 곳이라 두 값이 어긋나는 버그가 없습니다. 문제는 26장 `SteamManager.Awake`가 계정별 세이브 폴더를 세이브 로드 **전에** 정해야 한다는 점입니다. 현지화 초기화 과정(Startup Selector)에서 세이브를 읽으면 그보다 먼저 공용 폴더를 캐시할 수 있습니다. 그래서 Startup Selector는 세이브가 없을 때의 기본값만 담당하고, 세이브의 언어는 `GameFlow.Start`에서 `LanguageService.InitializeAsync`로 적용합니다.

</details>

**3. "생존 시간 " + 시간 문자열처럼 문장을 코드에서 조립하면 안 되는 이유와 대안은?**

<details>
<summary>모범 답안</summary>

언어마다 어순·조사·복수형이 달라서, 코드가 정한 순서대로 조각을 이어 붙이면 번역가가 자연스러운 문장을 만들 수 없습니다. 대안은 문장 전체를 한 항목으로 두고 변수 자리를 이름 있는 플레이스홀더(`{time}`)로 표시하는 것입니다. 번역가는 변수 위치를 자유롭게 옮길 수 있고, 복수형이 필요한 언어는 plural 포매터로 형태를 고릅니다. 숫자 서식(03:25)처럼 언어와 무관한 부분만 코드가 만들어 변수로 넘깁니다.

</details>

**4. 의사 현지화(Pseudo-Locale)는 번역을 받기 전에 무엇을 찾아주나요? 세 가지를 드세요.**

<details>
<summary>모범 답안</summary>

① Encapsulator의 괄호가 없는 텍스트로 **하드코딩 문자열**을 찾습니다. ② Expander로 문자열을 늘려 **텍스트 넘침·잘림**을 미리 봅니다(닫는 괄호가 안 보이면 잘린 것). ③ Accenter로 원문에 없는 문자를 써서 **폰트 폴백·글리프 처리**가 동작하는지 확인합니다. 이 세 문제를 번역 전에 고치면 번역을 받은 뒤의 수정 왕복이 줄어듭니다.

</details>

## 핵심 요약

- 국제화(문자열 분리·어순 자유·폰트·레이아웃 여유)를 먼저 끝내면 언어 추가 비용은 번역·검수로 줄어듭니다. 11장 직후, 문자열이 적을 때 시작합니다.
- Unity Localization(Unity 6000.0 기준 1.5.x)은 Locale → String Table Collection(공유 키 + 언어별 값) 구조이고, 테이블은 Addressables로 로드되므로 빌드 전 Addressables 빌드가 필요합니다.
- 정적 텍스트는 Localize String Event, 변수가 있는 문장은 Smart String의 이름 있는 변수·plural, 데이터 에셋은 `LocalizedString` 필드로 교체합니다.
- 자주 바뀌는 HUD 숫자는 번역된 **템플릿**만 받아 `SetText`로 넣어 할당 0을 지킵니다.
- 언어 선택은 10장 세이브에 저장하고(Steam Cloud 동기화), 적용은 SteamManager 이후의 부트스트랩에서 합니다. 첫 실행은 명령행 → Steam 언어 → 시스템 언어 → en.
- 의사 현지화로 하드코딩·넘침·폰트 문제를 번역 전에 찾고, 테이블에서 글자를 추출해 Static 폰트 아틀라스를 다시 굽습니다.
- 번역은 CSV(주석 포함)·용어집·톤 가이드·스크린샷을 함께 넘기고 CSV Merge로 들여온 뒤, 게임 안에서 검수합니다.
- 스토어의 지원 언어(Interface/Full Audio/Subtitles)와 문안·업적 용어를 게임과 일치시킵니다.

## 더 읽을거리

- Unity 매뉴얼 — Localization 패키지 (Unity 6000.0, 1.5.x): https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.localization.html
- Localization 1.5 매뉴얼 — Smart Strings: https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/Smart/SmartStrings.html
- Localization 1.5 매뉴얼 — Locale Selector / CSV / Pseudo-Localization: https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/LocaleSelector.html · https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/CSV.html · https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/Pseudo-Localization.html
- Localization 1.5 API — `LocalizedString`, `LocalizationSettings`, `IStartupLocaleSelector`: https://docs.unity3d.com/Packages/com.unity.localization@1.5/api/UnityEngine.Localization.LocalizedString.html
- Steamworks 문서 — Localization and Languages (지원 언어, `GetCurrentGameLanguage`, API 언어 코드): https://partner.steamgames.com/doc/store/localization · https://partner.steamgames.com/doc/store/localization/languages
