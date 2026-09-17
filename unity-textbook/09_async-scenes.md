# 09. 비동기와 씬 구조 — Awaitable·Additive 로딩

> **이 장에서 배울 것**
> - 코루틴, `async`/`await`(`Awaitable`), UniTask의 차이를 설명하고 상황에 맞게 고를 수 있다
> - `Awaitable`과 `destroyCancellationToken`으로 오브젝트 수명에 안전한 비동기 코드를 작성하고, 예외를 잃어버리지 않게 처리한다
> - `SceneManager.LoadSceneAsync`, `allowSceneActivation`, Additive 로딩, 활성 씬 지정을 정확히 사용한다
> - `DontDestroyOnLoad`의 한계를 설명하고 부트스트랩 씬 구조로 대체한다
> - 진행률 0.9 함정을 피한 로딩 화면을 구현하고 04장의 상태 머신과 씬 전환을 연결한다
>
> **선수 장**: 01, 03, 04, 08 · **예상 시간**: 4~5시간 · **코인 러시 진행**: Bootstrap → Title → Game 씬 구조, 페이드와 진행률 바가 있는 로딩 화면, 어느 씬에서 Play를 눌러도 매니저가 준비된 상태로 시작

## 왜 필요한가

지금 코인 러시는 씬 하나(`SampleScene`)에 모든 것이 들어 있습니다. 타이틀 화면을 붙이려고 `Title` 씬을 만들고 `SceneManager.LoadScene("Game")`으로 넘어가게 하자 문제가 연달아 생깁니다.

1. **게임 씬으로 넘어가면 화면이 1~2초 멈춘다.** `LoadScene`은 동기 로딩이라 로딩이 끝날 때까지 프레임이 멈춥니다. 모바일에서는 OS가 "앱이 응답하지 않음"으로 볼 수도 있습니다.
2. **08장의 `ControlsManager`, 12장에서 만들 `AudioManager`가 씬을 넘어가면 사라진다.** `DontDestroyOnLoad`를 붙였더니 이번엔 타이틀로 돌아올 때마다 **매니저가 하나씩 늘어납니다**(타이틀 씬에도 매니저가 들어 있어서).
3. **Game 씬을 열고 바로 Play를 누르면 매니저가 없어 NullReferenceException.** 매니저는 Title 씬에만 있기 때문입니다.
4. 로딩 화면을 만들어 `operation.progress`로 진행률 바를 채웠더니 **90%에서 멈춰서** 끝까지 안 찹니다.
5. 페이드 연출을 `async` 메서드로 짰는데, 페이드 도중 씬이 바뀌자 **`MissingReferenceException`** 이 쏟아집니다.

이 장은 비동기 코드의 규칙과 씬 구조를 함께 다룹니다. 씬 로딩은 비동기이고, 비동기 코드는 "기다리는 사이 오브젝트가 사라지는" 문제와 늘 붙어 다니기 때문입니다.

## 개념

### 코루틴 vs async/await vs UniTask

Unity에서 "여러 프레임에 걸친 작업"을 쓰는 방법은 세 가지입니다.

```csharp
// 1) 코루틴 — Unity 전통 방식
IEnumerator FadeRoutine()
{
    for (float t = 0; t < 1f; t += Time.deltaTime) { group.alpha = t; yield return null; }
}
StartCoroutine(FadeRoutine());

// 2) Awaitable — Unity 6 내장 async/await
async Awaitable FadeAsync()
{
    for (float t = 0; t < 1f; t += Time.deltaTime) { group.alpha = t; await Awaitable.NextFrameAsync(destroyCancellationToken); }
}
await FadeAsync();

// 3) UniTask — 서드파티 라이브러리(Cysharp/UniTask)
async UniTask FadeUniTask() { /* ... */ await UniTask.Yield(); }
```

| 항목 | 코루틴 | Awaitable (Unity 6) | UniTask |
|---|---|---|---|
| 설치 | 내장 | 내장 | 패키지 추가 |
| 결과값 반환 | 불가(콜백으로 우회) | `Awaitable<T>` | `UniTask<T>` |
| 예외 처리 | try/catch 안에 `yield` 불가 | 일반 try/catch | 일반 try/catch |
| 취소 | `StopCoroutine`, GameObject 비활성(`SetActive(false)`)·파괴 시 자동 중단 (컴포넌트 `enabled = false`로는 **안 멈춤**) | `CancellationToken` (명시적) | `CancellationToken` |
| 수명 | 실행한 MonoBehaviour에 묶임 | 묶이지 않음 → 토큰으로 묶어야 함 | 묶이지 않음 |
| 할당 | `StartCoroutine`마다 약간 | 내부 풀링으로 적음 | 매우 적음 |
| 여러 작업 조합(WhenAll 등) | 어려움 | 기본 기능은 적음 | 풍부 |
| 권장 | 짧은 연출, 기존 코드 | **새 코드 기본** | 비동기 코드가 매우 많은 프로젝트 |

> JS 비유: 코루틴은 제너레이터(`function*` + `yield`)로 비동기를 흉내 내던 옛 방식(co 라이브러리)이고, `Awaitable`은 `async`/`await` + `Promise`에 해당합니다. 다만 JS의 Promise와 달리 **컴포넌트가 unmount(파괴)되어도 자동으로 멈추지 않는다**는 점이 React의 `useEffect` cleanup 문제와 똑같습니다.

이 책은 새 코드에 `Awaitable`을 씁니다. 코루틴은 07장의 깜빡임처럼 **오브젝트와 함께 죽어도 되는 짧은 연출**에는 여전히 가장 간단한 선택입니다.

### Awaitable 사용법

| API | 의미 |
|---|---|
| `await Awaitable.NextFrameAsync(token)` | 다음 프레임까지 대기 (`yield return null`) |
| `await Awaitable.WaitForSecondsAsync(sec, token)` | 초 대기 |
| `await Awaitable.FixedUpdateAsync(token)` | 다음 FixedUpdate까지 |
| `await Awaitable.EndOfFrameAsync(token)` | 프레임 렌더링 끝 |
| `await Awaitable.BackgroundThreadAsync()` | 이후 코드를 백그라운드 스레드에서 실행 |
| `await Awaitable.MainThreadAsync()` | 메인 스레드로 복귀 |
| `destroyCancellationToken` | MonoBehaviour 파괴 시 취소되는 토큰 |
| `Application.exitCancellationToken` | 앱 종료(에디터 Play 종료) 시 취소되는 토큰 |

```csharp
using System;
using System.IO;
using UnityEngine;

public class AwaitableExamples : MonoBehaviour
{
    private async void Start()   // 최상위 진입점 — 아래 "예외 처리" 참고
    {
        try
        {
            await Awaitable.WaitForSecondsAsync(1f, destroyCancellationToken);
            Debug.Log("1초 뒤");

            string text = await ReadFileAsync(Path.Combine(Application.persistentDataPath, "log.txt"));
            Debug.Log($"읽은 글자 수: {text.Length}");
        }
        catch (OperationCanceledException) { /* 오브젝트가 파괴됨 — 정상 종료 */ }
        catch (Exception e) { Debug.LogException(e, this); }
    }

    private async Awaitable<string> ReadFileAsync(string path)
    {
        await Awaitable.BackgroundThreadAsync();       // 파일 I/O는 메인 스레드 밖에서
        string text = File.Exists(path) ? File.ReadAllText(path) : string.Empty;
        await Awaitable.MainThreadAsync();             // Unity API를 쓰기 전에 반드시 복귀
        return text;
    }
}
```

반드시 기억할 규칙입니다.

1. **Unity API는 메인 스레드에서만.** `BackgroundThreadAsync` 이후에 `transform`, `GameObject`, `Instantiate` 같은 대부분의 Unity API를 쓰면 예외가 납니다(`Debug.Log`, `Mathf`, `Vector3` 같은 일부는 예외).
2. **같은 `Awaitable` 인스턴스를 두 번 `await`하지 마세요.** Unity가 내부적으로 풀링해 재사용하므로, 끝난 인스턴스를 다시 기다리면 전혀 다른 작업을 기다리게 됩니다. 결과를 여러 곳에서 써야 하면 값으로 받아 두세요.
3. **토큰을 넘기세요.** `destroyCancellationToken`을 넘기지 않으면 오브젝트가 파괴된 뒤에도 `await` 다음 줄이 실행되어 파괴된 `transform`에 접근합니다(도입부 5번 문제).

### 취소 — 수명을 비동기 코드에 묶기

```
오브젝트 생성 ──── await 페이드(1초) ────────────── await 다음 줄 실행 → 💥 MissingReferenceException
                          ↑
                   씬 전환으로 파괴됨 (토큰 없으면 아무도 모름)

오브젝트 생성 ──── await 페이드(토큰) ── 파괴 → 토큰 취소 → OperationCanceledException → catch에서 조용히 종료
```

- 취소는 **예외(`OperationCanceledException`)** 로 전달됩니다. 이 예외는 "정상적인 중단"이므로 잡아서 무시합니다.
- 여러 수명 조건을 합치려면 `CancellationTokenSource.CreateLinkedTokenSource(destroyCancellationToken, otherToken)`을 씁니다. 만든 소스는 `Dispose()`합니다.
- `Task.Delay` 같은 .NET `Task`는 **Play 모드를 종료해도 계속 돕니다.** 에디터에서 Play를 끈 뒤에도 로그가 찍히는 원인입니다. Unity 코드에서는 `Awaitable`을 쓰고 토큰을 넘기세요.

### 예외 처리 — async void 금지

`async void` 메서드에서 난 예외는 **호출자가 잡을 방법이 없습니다.** `async Awaitable`은 호출자가 `await`하면 예외가 호출자에게 전달됩니다.

| 반환 타입 | 호출자가 await 가능 | 예외 전달 | 쓸 곳 |
|---|---|---|---|
| `async void` | 불가 | 호출자에게 안 옴 | **최상위 진입점에서만**(`Start`, 버튼 핸들러), 본문 전체를 try/catch로 감쌀 때 |
| `async Awaitable` | 가능 | await한 곳으로 전달 | 기본 |
| `async Awaitable<T>` | 가능 | 전달 | 값을 돌려줄 때 |

`await`하지 않고 "던져 두는(fire-and-forget)" 호출도 결국 어딘가에서 예외를 기록해야 합니다. 이를 한곳에 모은 도우미를 만들어 두면 편합니다.

```csharp
using System;
using UnityEngine;

// Assets/_CoinRush/Scripts/Core/AwaitableExtensions.cs
public static class AwaitableExtensions
{
    // 기다리지 않을 Awaitable을 안전하게 실행: 취소는 무시, 나머지 예외는 콘솔에 기록
    public static async void Forget(this Awaitable awaitable)
    {
        try { await awaitable; }
        catch (OperationCanceledException) { }
        catch (Exception e) { Debug.LogException(e); }
    }
}
```

이 `async void`는 규칙의 예외가 아니라 **규칙을 지키는 유일한 장소**입니다. 모든 fire-and-forget 호출이 여기를 거치므로 예외가 사라지지 않습니다.

### 씬 로딩 — LoadSceneAsync와 0.9 함정

```csharp
AsyncOperation op = SceneManager.LoadSceneAsync("Game", LoadSceneMode.Additive);
op.allowSceneActivation = false;   // 로딩은 하되 활성화(Awake/Start 호출)는 보류
```

| 필드 | 의미 |
|---|---|
| `progress` | 0~1 진행률. **`allowSceneActivation = false`면 0.9에서 멈춤** |
| `isDone` | 활성화까지 완료되면 true. 활성화를 보류하면 영원히 false |
| `allowSceneActivation` | true가 되는 순간 나머지 10%(활성화 단계) 진행 |

`progress`는 "읽기 단계 0~0.9 + 활성화 단계 0.9~1.0"으로 나뉩니다. 활성화를 보류하면 0.9에서 기다리므로 **진행률 바는 `progress / 0.9f`로 정규화**해야 끝까지 찹니다. 그리고 `while (!op.isDone)`로 기다리면 활성화를 보류한 경우 무한 루프가 됩니다. 조건은 `op.progress < 0.9f`여야 합니다.

```
progress:  0.0 ─────── 0.9 ║ (allowSceneActivation=false면 여기서 대기) ║ ── 1.0 (isDone)
바 표시:   0%  ─────── 100%   ← progress / 0.9
```

또 하나의 함정: 활성화를 보류한 작업이 있는 동안 **다른 비동기 씬 작업(UnloadSceneAsync 등)은 뒤에서 줄을 서서 진행되지 않습니다.** "새 씬 로드(보류) → 이전 씬 언로드 대기"로 짜면 서로 기다리며 멈춥니다. 언로드를 먼저 하거나, 활성화를 허용한 뒤 언로드하세요.

`AsyncOperation`은 폴링으로 기다리면 버전에 관계없이 안전합니다. Unity 6에서는 `AsyncOperation`을 직접 `await`하는 방법도 제공되지만, 이 책은 진행률 표시를 위해 프레임마다 폴링합니다.

### LoadSceneMode.Single vs Additive

| 모드 | 동작 | 용도 |
|---|---|---|
| `Single` | 기존 씬을 모두 언로드하고 새 씬만 남김 | 작은 게임, 씬 하나짜리 전환 |
| `Additive` | 기존 씬을 유지한 채 추가 | 매니저 씬 상시 유지, 레벨 분할 로딩, UI 씬 분리 |

Additive로 여러 씬을 열면 그중 하나가 **활성 씬(Active Scene)** 입니다. `Instantiate`로 만든 오브젝트와 새 `GameObject`는 **활성 씬에 생성**되고, 조명 설정도 활성 씬 기준입니다. 게임 씬을 로드한 뒤 `SceneManager.SetActiveScene(gameScene)`을 하지 않으면, 스폰한 적이 Bootstrap 씬에 생겨서 **게임 씬을 언로드해도 적이 남습니다.**

시점도 중요합니다. 새 씬의 `Awake`·`OnEnable`은 활성화 순간에 실행되고, 그다음 `SceneManager.sceneLoaded` 콜백, 그다음 `Start` 순서입니다. `sceneLoaded`에서 활성 씬을 바꾸면 `Start` 이후의 생성은 새 씬에 들어가지만, **`Awake`·`OnEnable`에서 부모 없이 `Instantiate`한 오브젝트는 이미 이전 활성 씬(Bootstrap)에 생긴 뒤**이고 나중에 활성 씬을 바꿔도 옮겨지지 않습니다. 콘텐츠 씬의 스크립트는 오브젝트 생성을 `Start` 이후에 하거나, 부모를 지정하거나, `SceneManager.MoveGameObjectToScene(go, gameObject.scene)`으로 자기 씬에 옮기세요.

### DontDestroyOnLoad의 한계

`DontDestroyOnLoad(gameObject)`는 오브젝트를 숨겨진 특수 씬으로 옮겨 씬 전환에서 살아남게 합니다. 작은 게임에는 충분하지만 규모가 커지면 다음 문제가 생깁니다.

| 문제 | 설명 |
|---|---|
| 중복 생성 | 매니저가 들어 있는 씬으로 돌아올 때마다 새로 생김 → "이미 있으면 Destroy" 코드가 매니저마다 필요 |
| 초기화 순서 | 어느 씬에서 시작했는지에 따라 매니저 생성 시점이 다름 |
| 특정 씬에서 바로 Play | 매니저가 있는 씬을 거치지 않으면 매니저가 없음 |
| 루트 오브젝트만 가능 | 자식에 호출하면 경고 후 무시 |
| 정리 시점 불명확 | 타이틀로 돌아갈 때 초기화해야 할 상태가 남음 |

### 부트스트랩 씬 패턴

해결책은 **매니저만 담은 씬 하나를 항상 먼저, 한 번만 로드하고 절대 언로드하지 않는 것**입니다. 콘텐츠 씬은 그 위에 Additive로 교체합니다.

```
[Bootstrap 씬]  (빌드 인덱스 0, 상시 로드, 한 번만)
  ├── GameFlow         ← 씬 단위 상태(Title/Game) 전환, 씬 전환 지시
  ├── SceneLoader      ← Additive 로드/언로드, 로딩 화면 제어
  ├── ControlsManager  ← 08장
  ├── (AudioManager)   ← 12장
  ├── LoadingCanvas    ← 로딩 화면 (Sort Order 최상위)
  └── EventSystem      ← 씬 전체에서 딱 하나

[콘텐츠 씬]  (하나만 올라와 있고 교체됨)
  Title  ⇄  Game
```

| DontDestroyOnLoad 방식 | 부트스트랩 방식 |
|---|---|
| 매니저가 어느 씬에 있는지 흩어짐 | Bootstrap 씬 한 곳 |
| 중복 방지 코드 필요 | 한 번만 로드하므로 불필요 |
| 초기화 순서가 시작 씬에 따라 다름 | 항상 같음 |
| 콘텐츠 씬이 매니저를 Inspector로 참조 불가 | 동일 (씬 간 참조 불가) → **03장 이벤트 채널로 통신** |

씬이 다르면 Inspector에서 서로의 오브젝트를 드래그해 참조할 수 없습니다. Title 씬의 "시작" 버튼이 Bootstrap 씬의 `GameFlow`를 부르려면 **03장의 `VoidEventChannel` 에셋**을 양쪽이 공유하면 됩니다. 에셋은 씬에 속하지 않기 때문입니다.

## 실습: 코인 러시에 적용하기

앞 장에서 사용하는 최소 시그니처입니다. 이름이 다르면 맞춰 조정하세요.

```csharp
// 03장 VoidEventChannel : event Action OnRaised, void Raise()
// 04장 상태 머신        : interface IGameState { void Enter(); void Tick(); void Exit(); }
//                         class GameStateMachine : MonoBehaviour { IGameState Current; void ChangeState(IGameState); }  — Game 씬 안에 그대로 둠
// 08장 ControlsManager  : static Instance, UseGameplay(), UseUI()   — PauseController·RebindButton은 Instance로 찾음
```

### 1단계: 씬 세 개와 Build Profile

1. `Assets/_CoinRush/Scenes/`에 씬 세 개를 만듭니다: `Bootstrap`, `Title`, `Game`.
2. 기존 게임 씬의 내용(Player, 적 스포너, HUD, 카메라, 벽, `GameSystems`)을 `Game` 씬으로 옮깁니다. 입력 관련 오브젝트는 이렇게 나눕니다.
   - `EventSystem`: 옮기지 않고 삭제합니다(Bootstrap에 둡니다).
   - 08장 `Controls` 오브젝트: **`ControlsManager` 컴포넌트만 제거**하고, 오브젝트와 `PauseController`는 Game 씬에 남깁니다. `PausePanel`(리바인딩 버튼 포함), 모바일 `PauseButton`, HUD의 `PauseHint`도 Game 씬 Canvas에 그대로 둡니다. 이들은 08장에서 `ControlsManager`를 Inspector로 참조하지 않고 `ControlsManager.Instance`와 `ControlsManager.BindingsChanged`로 찾도록 만들었으므로, 관리자가 Bootstrap 씬으로 가도 연결을 다시 할 필요가 없습니다. `PauseController`의 State Machine은 같은 Game 씬의 `GameSystems`이므로 그대로 연결됩니다.
   - 04장의 `TitlePanel`과 그 "시작" 버튼: 타이틀은 이제 `Title` 씬이 맡으므로 Game 씬에서 **삭제**하고, 아래 3번의 `GameStateMachine` 수정을 적용합니다.
3. `GameStateMachine`은 04장 정본에서 `Start()`로 **Title 상태**에 들어갑니다. 그대로 두면 Title 씬에서 시작을 눌러 Game 씬이 올라와도 다시 (이제 없는) 내부 타이틀에서 멈춥니다. Game 씬에서는 곧바로 플레이하도록 두 곳을 교체합니다.

```csharp
// GameStateMachine.cs (04장) — Awake 안의 titlePanel 줄 교체
if (titlePanel != null) titlePanel.SetActive(false);   // 09장: 타이틀 패널은 Title 씬으로 이동, 비워 둬도 됨

// GameStateMachine.cs (04장) — Start 교체
void Start() => ChangeState(Playing);   // 09장: 타이틀은 Title 씬이 담당하므로 Game 씬은 바로 플레이
```

   `TitleState` 클래스와 `StartGame()`은 지우지 않아도 됩니다(더 이상 그 상태로 들어가지 않음). Inspector의 `Title Panel` 칸은 비워 둡니다. Game 씬이 활성화되는 순간 로딩 화면이 페이드 아웃(0.25초)하는 동안 이미 플레이가 시작된다는 점도 알아 두세요.
4. `Title` 씬: Canvas에 제목 텍스트와 `시작` 버튼. 카메라 하나. EventSystem은 **넣지 않습니다**. Title 씬에서는 Gameplay 맵이 켜져 있어도 그 액션을 읽는 스크립트가 없으므로 무해하고, 버튼 조작(마우스·터치·패드)은 Bootstrap EventSystem의 기본 UI 액션이 처리합니다. 일시정지 중에 씬이 내려가면 `PauseController.OnDisable`이 `Resume`을 불러 맵이 Gameplay로 돌아옵니다.
5. `Bootstrap` 씬: 기본 Main Camera와 Global Light 2D를 **삭제**합니다(콘텐츠 씬의 카메라와 중복되지 않게). 빈 오브젝트 `Managers`를 만들고 그 아래에 `ControlsManager`(08장, Asset = `CoinRushControls`), `EventSystem`(UI > Event System, `InputSystemUIInputModule`, Actions Asset은 기본값)을 둡니다.
6. `File > Build Profiles`를 열고 Scene List에 `Bootstrap`(0번), `Title`, `Game` 순서로 추가합니다. 목록에 없는 씬은 이름으로 로드할 수 없습니다.
7. `Assets/_CoinRush/Events/`에서 03장의 메뉴로 `VoidEventChannel` 에셋 세 개를 만듭니다: `StartGameRequested`, `ReturnToTitleRequested`, `RetryRequested`.

### 2단계: 로딩 화면

1. Bootstrap 씬에 `UI > Canvas` `LoadingCanvas`를 만들고 **Sort Order 100**으로 둡니다(모든 UI 위). `Canvas Group` 컴포넌트를 추가합니다.
2. 자식으로 화면 전체를 덮는 검은 `Image` `Background`, 하단에 `Image` `ProgressFill`(Image Type: Filled, Fill Method: Horizontal), TMP 텍스트 `ProgressLabel`을 둡니다.
3. 아래 스크립트를 `LoadingCanvas`에 붙입니다.

```csharp
using System.Threading;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// Assets/_CoinRush/Scripts/Flow/LoadingScreen.cs
[RequireComponent(typeof(CanvasGroup))]
public class LoadingScreen : MonoBehaviour
{
    [SerializeField] private Image progressFill;
    [SerializeField] private TextMeshProUGUI progressLabel;
    [SerializeField] private float fadeSeconds = 0.25f;

    private CanvasGroup group;
    private float displayed;   // 화면에 보이는 진행률 (부드럽게 따라감)

    private void Awake()
    {
        group = GetComponent<CanvasGroup>();
        group.alpha = 0f;
        group.blocksRaycasts = false;   // 숨어 있을 때 클릭을 막지 않게
        SetProgressImmediate(0f);
    }

    public Awaitable ShowAsync(CancellationToken token)
    {
        group.blocksRaycasts = true;    // 로딩 중 버튼 연타 방지
        SetProgressImmediate(0f);
        return FadeAsync(1f, token);
    }

    public async Awaitable HideAsync(CancellationToken token)
    {
        await FadeAsync(0f, token);
        group.blocksRaycasts = false;
    }

    // 목표 진행률을 받아 표시값을 부드럽게 올림 (매 프레임 호출)
    public void TickProgress(float target)
    {
        displayed = Mathf.MoveTowards(displayed, Mathf.Clamp01(target), Time.unscaledDeltaTime * 2f);
        Apply();
    }

    public void SetProgressImmediate(float value)
    {
        displayed = Mathf.Clamp01(value);
        Apply();
    }

    public float DisplayedProgress => displayed;

    // 복구할 수 없는 로딩 실패: 화면을 덮은 채 안내 문구만 표시
    public void ShowError(string message)
    {
        group.alpha = 1f;
        group.blocksRaycasts = true;
        if (progressLabel != null) progressLabel.text = message;
    }

    private void Apply()
    {
        if (progressFill != null) progressFill.fillAmount = displayed;
        if (progressLabel != null) progressLabel.text = $"{Mathf.RoundToInt(displayed * 100f)}%";
    }

    private async Awaitable FadeAsync(float to, CancellationToken token)
    {
        float from = group.alpha;
        float t = 0f;
        while (t < fadeSeconds)
        {
            t += Time.unscaledDeltaTime;   // 일시정지(timeScale 0) 중에도 진행
            group.alpha = Mathf.Lerp(from, to, t / fadeSeconds);
            await Awaitable.NextFrameAsync(token);
        }
        group.alpha = to;
    }
}
```

### 3단계: SceneLoader — Additive 교체

```csharp
using System;
using System.Threading;
using UnityEngine;
using UnityEngine.SceneManagement;

// Assets/_CoinRush/Scripts/Flow/SceneLoader.cs
public class SceneLoader : MonoBehaviour
{
    [SerializeField] private LoadingScreen loadingScreen;
    [Tooltip("로딩 화면이 너무 번쩍이지 않도록 최소 표시 시간")]
    [SerializeField] private float minimumShowSeconds = 0.6f;

    public string CurrentContentScene { get; private set; } = string.Empty;
    public bool IsBusy { get; private set; }
    public LoadingScreen LoadingScreen => loadingScreen;

    private string pendingScene;   // 활성화를 기다리는 씬 이름 (sceneLoaded 콜백에서 사용)

    // 성공하면 true. 실패하면 false이고, 로딩 화면은 덮인 채로 남음 → 호출자가 복구 경로를 정함
    public async Awaitable<bool> SwitchToAsync(string sceneName)
    {
        if (IsBusy)
        {
            Debug.LogWarning($"씬 전환 중에 '{sceneName}' 요청이 들어와 무시했습니다.");
            return false;
        }

        // 0) 이전 씬을 내리기 "전에" 로드 가능한 씬인지 확인 (이름 오타·Scene List 누락)
        if (!Application.CanStreamedLevelBeLoaded(sceneName))
        {
            Debug.LogError($"씬 '{sceneName}'을 로드할 수 없습니다. Build Profiles의 Scene List와 이름을 확인하세요.");
            return false;
        }

        IsBusy = true;
        CancellationToken token = destroyCancellationToken;   // Bootstrap은 파괴되지 않지만 Play 종료 대비
        pendingScene = sceneName;
        SceneManager.sceneLoaded += OnSceneLoaded;
        try
        {
            await loadingScreen.ShowAsync(token);
            float shownAt = Time.realtimeSinceStartup;

            // 1) 이전 콘텐츠 씬을 먼저 언로드 (활성화 보류 중인 로드와 교착되지 않도록)
            if (!string.IsNullOrEmpty(CurrentContentScene))
            {
                Scene previous = SceneManager.GetSceneByName(CurrentContentScene);
                if (previous.isLoaded)
                {
                    AsyncOperation unload = SceneManager.UnloadSceneAsync(previous);
                    while (unload != null && !unload.isDone)
                        await Awaitable.NextFrameAsync(token);
                }
                CurrentContentScene = string.Empty;
                await WaitAsync(Resources.UnloadUnusedAssets(), token);   // 이전 씬 에셋 메모리 반환
            }

            // 2) 새 씬 로드 — 활성화는 보류
            AsyncOperation load = SceneManager.LoadSceneAsync(sceneName, LoadSceneMode.Additive);
            if (load == null)
            {
                Debug.LogError($"씬 '{sceneName}' 로드를 시작하지 못했습니다.");
                return false;
            }
            load.allowSceneActivation = false;

            while (load.progress < 0.9f)                     // isDone으로 기다리면 무한 대기
            {
                loadingScreen.TickProgress(load.progress / 0.9f);   // 0.9 → 100%로 정규화
                await Awaitable.NextFrameAsync(token);
            }

            // 3) 바가 끝까지 차고, 최소 표시 시간이 지날 때까지 대기
            while (loadingScreen.DisplayedProgress < 1f ||
                   Time.realtimeSinceStartup - shownAt < minimumShowSeconds)
            {
                loadingScreen.TickProgress(1f);
                await Awaitable.NextFrameAsync(token);
            }

            // 4) 활성화 → 새 씬의 Awake/OnEnable → sceneLoaded(여기서 활성 씬 지정) → Start
            load.allowSceneActivation = true;
            while (!load.isDone)
                await Awaitable.NextFrameAsync(token);

            Scene loaded = SceneManager.GetSceneByName(sceneName);
            if (!loaded.isLoaded)
            {
                Debug.LogError($"씬 '{sceneName}' 활성화에 실패했습니다.");
                return false;
            }
            if (SceneManager.GetActiveScene() != loaded) SceneManager.SetActiveScene(loaded);   // 안전망
            CurrentContentScene = sceneName;

            await loadingScreen.HideAsync(token);
            return true;
        }
        catch (OperationCanceledException)
        {
            throw;                                            // 취소(Play 종료 등)는 정상 종료로 위에 전달
        }
        catch (Exception e)
        {
            Debug.LogException(e, this);
            return false;                                     // 로딩 화면은 덮인 채 → 호출자가 타이틀 복구 등 결정
        }
        finally
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            pendingScene = null;
            IsBusy = false;
        }
    }

    // 새 씬의 Start보다 먼저 호출됨 → Start 이후에 만드는 오브젝트는 새 씬에 들어감
    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (scene.name == pendingScene) SceneManager.SetActiveScene(scene);
    }

    private static async Awaitable WaitAsync(AsyncOperation op, CancellationToken token)
    {
        while (op != null && !op.isDone)
            await Awaitable.NextFrameAsync(token);
    }
}
```

1. Bootstrap의 `Managers` 아래에 `SceneLoader` 오브젝트를 만들고 스크립트를 붙인 뒤 `Loading Screen`을 연결합니다.
2. `LoadingCanvas`도 Bootstrap에 있으므로 항상 살아 있습니다.

> `try/finally`는 취소나 예외가 나도 `IsBusy`를 되돌리기 위한 것입니다. 이걸 빼면 한 번 실패한 뒤로 영원히 "전환 중"이 되어 아무 씬으로도 못 갑니다. 다만 `IsBusy`만 풀어서는 부족합니다. 실패가 이전 씬을 내린 **뒤에** 일어나면 화면에는 검은 로딩 화면만 남아 사용자가 빠져나올 수 없습니다. 그래서 (1) 언로드 전에 `CanStreamedLevelBeLoaded`로 흔한 실패(이름 오타·Scene List 누락)를 먼저 걸러 이전 화면을 지키고, (2) 그 뒤의 실패는 `false`를 돌려 호출자(`GameFlow`, 5단계)가 **타이틀로 복구**하거나, 타이틀마저 실패하면 안내 문구를 띄우게 합니다.

### 4단계: 상태와 씬을 잇는 SceneState

04장의 상태 머신은 "지금 무슨 상태인가"를 관리하고, 씬 로딩은 "그 상태에 필요한 무대를 준비"합니다. 둘을 섞지 않고 연결하기 위해, **기존 상태를 감싸서 진입 전에 씬을 준비하는 상태**를 만듭니다.

```
ChangeState(gameState)
   └─ SceneState("Game").Enter()
         ├─ 필요한 씬이 이미 올라와 있나? ─ 예 ──────────────┐
         └─ 아니오 → await SceneLoader.SwitchToAsync("Game") ─┤
                                                               └→ inner.Enter()  (04장의 PlayingState)
```

```csharp
using System;
using System.Threading;
using UnityEngine;

// Assets/_CoinRush/Scripts/Flow/SceneState.cs
public class SceneState : IGameState
{
    private readonly string sceneName;
    private readonly SceneLoader loader;
    private readonly IGameState inner;              // 04장의 상태 (없으면 null)
    private readonly Action<string> onLoadFailed;   // 로드 실패 시 복구 경로 (GameFlow가 지정)
    private CancellationTokenSource enterCts;
    private bool innerEntered;

    public bool ReloadOnNextEnter { get; set; }

    public SceneState(string sceneName, SceneLoader loader, IGameState inner = null, Action<string> onLoadFailed = null)
    {
        this.sceneName = sceneName;
        this.loader = loader;
        this.inner = inner;
        this.onLoadFailed = onLoadFailed;
    }

    public void Enter()
    {
        enterCts = new CancellationTokenSource();
        EnterAsync(enterCts.Token).Forget();
    }

    private async Awaitable EnterAsync(CancellationToken token)
    {
        bool needsLoad = ReloadOnNextEnter || loader.CurrentContentScene != sceneName;
        ReloadOnNextEnter = false;

        if (needsLoad)
        {
            // 같은 씬을 다시 로드(재시작)할 때도 SwitchToAsync가 먼저 언로드하므로 동작
            bool ok = await loader.SwitchToAsync(sceneName);
            token.ThrowIfCancellationRequested();   // 로딩 중 다른 상태로 바뀌었으면 여기서 끝
            if (!ok)
            {
                onLoadFailed?.Invoke(sceneName);     // inner에는 들어가지 않음
                return;
            }
        }

        token.ThrowIfCancellationRequested();   // 로딩 중 다른 상태로 바뀌었으면 inner 진입 안 함
        inner?.Enter();
        innerEntered = true;
    }

    public void Tick()
    {
        if (innerEntered) inner?.Tick();
    }

    public void Exit()
    {
        enterCts?.Cancel();
        enterCts?.Dispose();
        enterCts = null;
        if (innerEntered) inner?.Exit();
        innerEntered = false;
        // 씬은 여기서 언로드하지 않음: Playing → LevelUp → Playing처럼 같은 씬 안의 전환이 있기 때문
    }
}
```

- **Exit에서 씬을 언로드하지 않는 것**이 핵심입니다. 04장의 LevelUp, Result 상태는 Game 씬 위에서 일어나므로, Playing을 나갈 때마다 씬을 내리면 안 됩니다. 씬은 "다른 씬이 필요한 상태"에 들어갈 때만 교체됩니다.
- 04장의 `PlayingState`가 Game 씬의 오브젝트(스포너, 플레이어)를 필요로 한다면, 생성자에서 받지 말고 `Enter()`에서 `FindFirstObjectByType`으로 한 번 찾도록 바꾸세요. `SceneState`가 씬 로드 **뒤에** `Enter()`를 호출하므로 그 시점엔 오브젝트가 존재합니다.

### 5단계: GameFlow — 부트스트랩의 지휘자

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;

// Assets/_CoinRush/Scripts/Flow/GameFlow.cs
[DefaultExecutionOrder(-100)]
public class GameFlow : MonoBehaviour
{
    public const string TitleScene = "Title";
    public const string GameScene = "Game";

    [SerializeField] private SceneLoader loader;

    [Header("이벤트 채널 (03장)")]
    [SerializeField] private VoidEventChannel startGameRequested;
    [SerializeField] private VoidEventChannel returnToTitleRequested;
    [SerializeField] private VoidEventChannel retryRequested;

    // 04장 GameStateMachine은 MonoBehaviour라 new로 만들 수 없고, Game 씬 안에서 LevelUp/Result를 계속 관리합니다.
    // GameFlow는 씬 단위 상태(Title/Game)만 IGameState로 직접 전환합니다.
    private IGameState current;
    private SceneState titleState;
    private SceneState gameState;

    private void Awake()
    {
        // Game 씬 안의 흐름은 그 씬의 04장 GameStateMachine이 맡으므로 inner는 비워 둡니다.
        // (Game 씬은 GameStateMachine.Start가 곧바로 Playing으로 들어가도록 1단계 3번에서 바꿨습니다.)
        titleState = new SceneState(TitleScene, loader, onLoadFailed: HandleLoadFailed);
        gameState = new SceneState(GameScene, loader, onLoadFailed: HandleLoadFailed);
    }

    // 씬 로드 실패 복구: 타이틀로 되돌리고, 타이틀마저 실패하면 안내 문구를 띄움
    private void HandleLoadFailed(string failedScene)
    {
        if (failedScene != TitleScene)
        {
            Debug.LogWarning($"'{failedScene}' 로드에 실패해 타이틀로 돌아갑니다.");
            Time.timeScale = 1f;
            ChangeState(titleState);
        }
        else
        {
            loader.LoadingScreen.ShowError("화면을 불러오지 못했습니다.\n게임을 다시 시작하거나 최신 버전으로 업데이트해 주세요.");
        }
    }

    private void OnEnable()
    {
        startGameRequested.OnRaised += StartGame;
        returnToTitleRequested.OnRaised += GoToTitle;
        retryRequested.OnRaised += Retry;
    }

    private void OnDisable()
    {
        startGameRequested.OnRaised -= StartGame;
        returnToTitleRequested.OnRaised -= GoToTitle;
        retryRequested.OnRaised -= Retry;
    }

    private void Start()
    {
        ChangeState(GetInitialState());
    }

    private void Update() => current?.Tick();

    public void GoToTitle() => ChangeIfIdle(titleState);
    public void StartGame() => ChangeIfIdle(gameState);

    public void Retry()
    {
        gameState.ReloadOnNextEnter = true;
        ChangeIfIdle(gameState, allowSame: true);
    }

    private void ChangeIfIdle(IGameState next, bool allowSame = false)
    {
        if (loader.IsBusy) return;                           // 로딩 중 버튼 연타 무시
        if (!allowSame && current == next) return;
        Time.timeScale = 1f;                                 // 일시정지·레벨업 중 전환 대비
        ChangeState(next);
    }

    private void ChangeState(IGameState next)
    {
        current?.Exit();
        current = next;
        current.Enter();                                     // 같은 상태여도 Exit → Enter (Retry)
    }

    private IGameState GetInitialState()
    {
#if UNITY_EDITOR
        // 에디터에서 Game 씬을 열고 Play했다면 바로 Game으로 (6단계 참고)
        string requested = UnityEditor.SessionState.GetString(BootstrapKeys.PlayFromScene, string.Empty);
        UnityEditor.SessionState.EraseString(BootstrapKeys.PlayFromScene);
        if (requested == GameScene) return gameState;
#endif
        return titleState;
    }
}

public static class BootstrapKeys
{
    public const string PlayFromScene = "CoinRush.PlayFromScene";
}
```

> `Retry`는 `current == gameState`인 상태에서 불립니다. 04장 `GameStateMachine.ChangeState`는 같은 상태로의 전환을 무시하므로, `GameFlow`는 자기 `ChangeState`를 두고 `allowSame`일 때 `Exit → Enter`를 다시 거쳐 씬을 새로 로드합니다.

1. Bootstrap의 `Managers` 아래에 `GameFlow`를 만들고 `Loader`와 이벤트 채널 세 개를 연결합니다.
2. Title 씬의 `시작` 버튼에 아래 컴포넌트를 붙이고 `Channel`에 `StartGameRequested`를 넣은 뒤, 버튼 OnClick에 `RaiseEvent`를 연결합니다. 결과 화면(11장)의 "재시작", "타이틀로" 버튼도 같은 방식으로 `RetryRequested`, `ReturnToTitleRequested`를 씁니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Flow/RaiseVoidEventOnClick.cs
public class RaiseVoidEventOnClick : MonoBehaviour
{
    [SerializeField] private VoidEventChannel channel;
    public void RaiseEvent() => channel.Raise();
}
```

3. 04장 `GameStateMachine.Restart`는 `SceneManager.LoadScene`으로 활성 씬을 **Single 모드**로 다시 불러옵니다. 부트스트랩 구조에서 이것을 부르면 Bootstrap 씬까지 내려가 매니저가 모두 사라집니다. Game 씬은 `GameFlow`를 직접 참조할 수 없으므로 `RetryRequested` 채널을 거치도록 교체합니다(파일 상단의 `using UnityEngine.SceneManagement;`는 삭제).

```csharp
// GameStateMachine.cs (04장) — 필드 추가, Restart 교체
[SerializeField] private VoidEventChannel retryRequested;   // 1단계에서 만든 RetryRequested 에셋

public void Restart()
{
    Time.timeScale = 1f;
    retryRequested.Raise();   // GameFlow.Retry → SceneState가 Game 씬을 언로드 후 다시 로드
}
```

### 6단계: 어느 씬에서 Play해도 Bootstrap부터

Game 씬을 열고 Play하면 Bootstrap이 없어 매니저가 없습니다. 에디터 전용 스크립트로 **Play 시작 씬을 Bootstrap으로 고정**하고, 원래 열려 있던 씬 이름을 기억해 `GameFlow`가 그 씬으로 바로 가게 합니다.

```csharp
#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;

// Assets/_CoinRush/Scripts/Editor/BootstrapPlayMode.cs  (Editor 폴더 → 빌드에 포함 안 됨)
[InitializeOnLoad]
public static class BootstrapPlayMode
{
    private const string BootstrapPath = "Assets/_CoinRush/Scenes/Bootstrap.unity";
    private const string MenuPath = "CoinRush/Play From Bootstrap";
    private const string EnabledKey = "CoinRush.PlayFromBootstrap";

    static BootstrapPlayMode()
    {
        EditorApplication.playModeStateChanged += OnPlayModeChanged;
        EditorApplication.delayCall += Apply;
    }

    [MenuItem(MenuPath)]
    private static void Toggle()
    {
        EditorPrefs.SetBool(EnabledKey, !EditorPrefs.GetBool(EnabledKey, true));
        Apply();
    }

    [MenuItem(MenuPath, true)]
    private static bool ToggleValidate()
    {
        Menu.SetChecked(MenuPath, EditorPrefs.GetBool(EnabledKey, true));
        return true;
    }

    private static void Apply()
    {
        bool enabled = EditorPrefs.GetBool(EnabledKey, true);
        EditorSceneManager.playModeStartScene = enabled
            ? AssetDatabase.LoadAssetAtPath<SceneAsset>(BootstrapPath)
            : null;
    }

    private static void OnPlayModeChanged(PlayModeStateChange change)
    {
        if (change == PlayModeStateChange.ExitingEditMode)
        {
            // Play 누르기 직전 열려 있던 씬 이름을 기록 → GameFlow가 읽음
            SessionState.SetString(BootstrapKeys.PlayFromScene, SceneManager.GetActiveScene().name);
        }
    }
}
#endif
```

1. `Assets/_CoinRush/Scripts/Editor/` 폴더를 만들고 저장합니다. 폴더 이름이 정확히 `Editor`여야 빌드에서 제외됩니다.
2. 상단 메뉴 `CoinRush > Play From Bootstrap`에 체크가 되어 있는지 확인합니다.
3. Game 씬에 들어 있던 Main Camera는 그대로 두고, Game 씬에서 테스트용으로 넣어 둔 `ControlsManager`·`EventSystem`이 남아 있다면 삭제합니다(중복).

### 확인하기

1. Title 씬을 열고 Play → 검은 로딩 화면이 잠깐 나타났다 사라지고 타이틀이 보인다.
2. `시작`을 누르면 로딩 화면이 페이드 인, 진행률 바가 **100%까지** 차고, 페이드 아웃되며 게임이 시작된다. 시작 버튼을 연타해도 로딩이 한 번만 일어난다.
3. Hierarchy에 `Bootstrap`과 `Game` 두 씬만 보이고, **Game이 굵은 글씨(활성 씬)** 다. 스폰된 적이 `Game` 씬 아래에 생긴다.
4. 결과 화면에서 "타이틀로"를 누르면 Game 씬이 사라지고 Title 씬이 올라온다. 적이 하나도 남지 않는다. 매니저는 하나씩만 있다.
5. Game 씬을 열고 Play → 타이틀을 거치지 않고 바로 게임이 시작되며, 입력(08장)이 정상 동작한다.
6. 로딩 도중 Play를 꺼도 콘솔에 `MissingReferenceException`이 뜨지 않는다.
7. `GameFlow.GameScene` 상수를 임시로 `"Gamee"`로 바꾸고 `시작`을 누르면, 에러 로그만 남고 **타이틀 화면이 그대로 조작 가능**하다(언로드 전 검사). 확인 후 되돌린다.
8. 결과 화면에서 "재시작"을 누르면 로딩 후 **타이틀 패널 없이 바로 플레이**가 시작되고, 일시정지(Esc)·리바인딩·HUD 안내 문구가 08장과 똑같이 동작한다.

## 흔한 실수

1. **로딩 바가 90%에서 멈추거나 로딩이 끝나지 않는다** → `allowSceneActivation = false`인데 `progress`를 그대로 표시하거나 `isDone`을 기다림 → 바는 `progress / 0.9f`, 대기 조건은 `progress < 0.9f`, 활성화 후에만 `isDone`을 기다립니다.
2. **게임 씬을 내렸는데 적·총알이 남아 있다** → Additive 로드 후 활성 씬을 바꾸지 않아 `Instantiate`가 Bootstrap 씬에 생성 → `sceneLoaded` 콜백(새 씬의 `Start` 전)에서 `SceneManager.SetActiveScene`. 새 씬의 `Awake`/`OnEnable`에서 만든 오브젝트는 그래도 Bootstrap에 생기므로 생성은 `Start` 이후로 미루거나 부모를 지정합니다.
3. **씬 전환 후 `MissingReferenceException`이 뜬다** → `await` 뒤에 파괴된 오브젝트에 접근, 토큰 미전달 → `destroyCancellationToken`을 넘기고 `OperationCanceledException`을 잡습니다.
4. **예외가 콘솔에 안 뜨고 조용히 멈춘다** → `await`하지 않은 비동기 호출의 예외가 버려짐, 또는 catch에서 삼킴 → `async Awaitable`을 await하거나 `.Forget()` 도우미로 기록합니다. `catch (Exception) {}`처럼 비워 두지 않습니다.
5. **"There are 2 event systems in the scene" / "2 audio listeners" 경고** → 콘텐츠 씬과 Bootstrap 양쪽에 EventSystem 또는 카메라(AudioListener)가 있음 → EventSystem은 Bootstrap에만, 카메라는 콘텐츠 씬에만 둡니다.
6. **백그라운드 스레드에서 `UnityException: ... can only be called from the main thread`** → `BackgroundThreadAsync` 이후 Unity API 사용 → `await Awaitable.MainThreadAsync()`로 돌아온 뒤 호출합니다.

## 연습 문제

**1. ★☆☆ 타이틀 페이드 인**
Title 씬의 로고가 씬 진입 후 0.5초 대기 → 0.8초 동안 알파 0→1로 나타나게 하세요. 코루틴과 `Awaitable` 두 버전으로 작성하고, 페이드 중 `시작`을 눌렀을 때 두 버전 모두 에러가 없는지 확인하세요.

<details>
<summary>힌트·해설</summary>

`Awaitable` 버전은 `async void Start()` 전체를 try/catch로 감싸고, `WaitForSecondsAsync(0.5f, destroyCancellationToken)`과 `NextFrameAsync(destroyCancellationToken)`를 씁니다. 코루틴 버전은 오브젝트가 파괴되면 자동으로 멈추므로 토큰이 필요 없습니다. 이것이 "오브젝트와 함께 죽어도 되는 짧은 연출은 코루틴도 좋은 선택"이라는 말의 의미입니다. 토큰을 빼고 `Awaitable` 버전을 돌려 보면 로딩 중 `MissingReferenceException`이 재현됩니다.

</details>

**2. ★★☆ 로딩 팁 문구**
로딩 화면에 1.5초마다 바뀌는 팁 문구("적은 코인을 떨굽니다" 등)를 표시하세요. 팁 목록은 ScriptableObject로 두고, 06장의 `ShuffleBag`으로 같은 팁이 연속으로 나오지 않게 합니다(가방과 가방의 경계 포함). 로딩이 끝나면 팁 교체 루프도 멈춰야 합니다.

<details>
<summary>힌트·해설</summary>

가방은 `new ShuffleBag<string>(avoidRepeatAcrossRefill: true)`로 만듭니다. 기본 `ShuffleBag`은 가방 안의 비율만 보장하므로, 첫 가방이 B, A로 끝나고 다음 가방이 A부터 나오면 A가 연속됩니다. 이 옵션은 새 가방의 첫 항목이 직전 항목과 같으면 다른 항목과 자리를 바꿉니다(팁이 한 개뿐이면 피할 수 없으므로 그대로 둡니다). 팁을 2개 이상 넣었는지 확인하세요.

`LoadingScreen.ShowAsync`에서 `CancellationTokenSource tipsCts = CancellationTokenSource.CreateLinkedTokenSource(destroyCancellationToken)`를 만들고 `RotateTipsAsync(tipsCts.Token).Forget()`을 시작합니다. `HideAsync`에서 `tipsCts.Cancel(); tipsCts.Dispose();`. 루프 안의 대기는 `WaitForSecondsAsync`가 timeScale 영향을 받을 수 있으니 `Time.unscaledTime` 기준 루프 + `NextFrameAsync`로 쓰면 일시정지 상태에서도 안전합니다. "시작한 비동기 루프는 반드시 누군가 멈춘다"가 핵심입니다.

</details>

**3. ★★☆ 무거운 초기화를 백그라운드로**
Game 씬 진입 시 10만 칸짜리 격자 데이터(예: 스폰 가능 위치 계산)를 만드는 작업이 프레임을 멈춘다고 가정하세요. 계산은 백그라운드 스레드에서 하고, 완료 후 메인 스레드에서 결과를 적용하도록 바꾸세요. 로딩 화면이 떠 있는 동안 끝나야 합니다.

<details>
<summary>힌트·해설</summary>

계산 함수는 Unity API를 쓰지 않는 순수 C#(`bool[]`, `Vector2Int`는 구조체라 사용 가능, `Physics2D`·`Transform`은 불가)으로 분리합니다. `await Awaitable.BackgroundThreadAsync(); var grid = Build(); await Awaitable.MainThreadAsync(); Apply(grid);`. 로딩 화면 안에서 끝내려면 `SceneLoader`에 "활성화 후, 로딩 화면을 내리기 전"에 실행할 훅을 추가합니다. 예: 콘텐츠 씬에 `ISceneInitializer { Awaitable InitializeAsync(CancellationToken) }` 구현체를 두고, `활성화가 끝난 직후(`CurrentContentScene`을 기록한 뒤) `FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)` 중 이 인터페이스를 구현한 것을 모두 await한 뒤 `HideAsync`를 호출합니다.

</details>

**4. ★★★ UI 씬 분리와 레벨 스트리밍 (확장 과제)**
HUD를 `GameUI` 씬으로 분리해 `Game` 씬과 함께 Additive로 로드하고, 맵을 `Map_A`, `Map_B`로 나눠 플레이 도중 플레이어가 경계에 가까워지면 다음 맵을 백그라운드로 로드·이전 맵을 언로드하세요. 로딩 화면 없이 끊김이 없어야 합니다.

<details>
<summary>힌트·해설</summary>

- `SceneLoader`를 "콘텐츠 씬 하나"가 아니라 **씬 이름 집합**을 관리하도록 일반화합니다(`HashSet<string> loaded`).
- 끊김 없는 스트리밍에서는 `allowSceneActivation = false`를 쓰지 않습니다(다른 비동기 작업을 막으므로). 대신 `Application.backgroundLoadingPriority = ThreadPriority.Low`로 로딩이 게임 프레임을 덜 방해하게 합니다.
- 씬 활성화 순간의 스파이크(Awake 폭주)를 프로파일러로 확인하고, 무거운 초기화는 여러 프레임에 나눕니다(18장).
- 적이 이전 맵 씬에 생성되어 있으면 언로드 시 함께 사라지므로, 적을 어느 씬에 둘지(활성 씬 = `Game`) 규칙을 먼저 정합니다.

</details>

## 셀프 체크

**1. `Awaitable`을 쓸 때 `destroyCancellationToken`을 넘기지 않으면 어떤 일이 생기는지, 코루틴과 비교해 설명해 보세요.**

<details>
<summary>모범 답안</summary>

코루틴은 실행한 MonoBehaviour의 GameObject가 비활성화(`SetActive(false)`)되거나 파괴되면 함께 멈추지만(컴포넌트만 `enabled = false`로 끄면 계속 돌므로 그때는 `StopCoroutine`을 직접 호출해야 합니다), `Awaitable` 기반 async 메서드는 오브젝트 수명과 무관하게 계속 진행됩니다. 토큰이 없으면 대기 중 오브젝트가 파괴되어도 `await` 다음 줄이 실행되어 파괴된 오브젝트에 접근하고 `MissingReferenceException`이 납니다. `destroyCancellationToken`을 넘기면 파괴 시 대기가 `OperationCanceledException`으로 중단되고, 이를 잡아 조용히 끝낼 수 있습니다.

</details>

**2. `async void`를 피해야 하는 이유와, 그래도 써도 되는 경우를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

`async void`는 호출자가 완료를 기다리거나 예외를 받을 수 없어, 내부 예외가 호출자에게 전달되지 않고 흐름을 추적하기 어렵습니다. 그래서 기본은 `async Awaitable`입니다. 예외적으로 Unity가 호출하는 최상위 진입점(`Start`, UI 이벤트 핸들러)이나 fire-and-forget 도우미처럼 **더 위에 await할 호출자가 없는 곳**에서, 본문 전체를 try/catch로 감싸 예외를 직접 기록할 때만 씁니다.

</details>

**3. 로딩 진행률이 0.9에서 멈추는 이유와 올바른 처리 방법을 설명해 보세요.**

<details>
<summary>모범 답안</summary>

`AsyncOperation.progress`는 데이터 로딩 단계를 0~0.9, 활성화 단계를 0.9~1로 표시합니다. `allowSceneActivation = false`면 활성화를 보류하므로 0.9에서 멈추고 `isDone`도 false로 남습니다. 표시용 진행률은 `progress / 0.9f`로 정규화하고, 로딩 완료 대기는 `progress < 0.9f` 조건으로 하며, 활성화를 허용한 뒤에야 `isDone`을 기다립니다.

</details>

**4. DontDestroyOnLoad 대신 부트스트랩 씬을 쓰면 무엇이 좋아지는지, 그리고 씬 간 참조 문제를 어떻게 푸는지 설명해 보세요.**

<details>
<summary>모범 답안</summary>

매니저가 Bootstrap 씬 한 곳에 모이고 그 씬은 한 번만 로드되어 언로드되지 않으므로, 중복 생성 방지 코드가 필요 없고 초기화 순서가 항상 같습니다. 에디터에서는 Play 시작 씬을 Bootstrap으로 고정해 어느 씬에서 테스트해도 매니저가 준비됩니다. 씬이 달라 Inspector 참조가 불가능한 문제는 씬에 속하지 않는 ScriptableObject 이벤트 채널(03장)을 양쪽이 공유해 해결합니다.

</details>

**5. Additive 로딩 후 `SetActiveScene`을 호출해야 하는 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

`Instantiate`와 `new GameObject`는 활성 씬에 오브젝트를 만들고, 조명·환경 설정도 활성 씬 기준입니다. Bootstrap이 활성 씬으로 남아 있으면 게임 중 스폰한 적·투사체가 Bootstrap 씬에 생성되어, 게임 씬을 언로드해도 사라지지 않고 다음 판까지 남습니다. 콘텐츠 씬을 로드한 직후(`sceneLoaded` 콜백, 새 씬의 `Start` 전) 활성 씬으로 지정해야 콘텐츠의 수명이 씬과 함께 관리됩니다. 단 새 씬의 `Awake`/`OnEnable`은 그보다 먼저 실행되므로, 그 안에서 부모 없이 만든 오브젝트는 따로 옮기거나 생성을 `Start` 이후로 미뤄야 합니다.

</details>

## 핵심 요약

- 새 비동기 코드는 `async Awaitable`로 씁니다. 코루틴은 오브젝트와 함께 끝나도 되는 짧은 연출에 여전히 유용하고, UniTask는 비동기 코드가 매우 많을 때 고려합니다.
- `await`에는 `destroyCancellationToken`을 넘기고 `OperationCanceledException`을 정상 종료로 처리합니다. 같은 Awaitable을 두 번 await하지 않습니다.
- `async void`는 최상위 진입점에서만, try/catch와 함께. fire-and-forget은 `.Forget()` 도우미로 예외를 기록합니다.
- `LoadSceneAsync` + `allowSceneActivation = false`면 progress가 0.9에서 멈춥니다. 표시는 `/0.9`, 대기는 `< 0.9`.
- Additive로 로드한 뒤 `SetActiveScene`으로 활성 씬을 지정합니다. 활성화 보류 중에는 다른 씬 비동기 작업이 진행되지 않습니다.
- 매니저는 부트스트랩 씬에 모으고, 콘텐츠 씬(Title/Game)만 교체합니다. 씬 간 통신은 ScriptableObject 이벤트 채널로 합니다.
- 상태 머신과 씬 로딩은 `SceneState` 같은 감싸기 상태로 연결하고, 같은 씬 안의 상태 전환에서는 씬을 내리지 않습니다.

## 더 읽을거리

- Unity 매뉴얼 — Asynchronous programming with Awaitable: https://docs.unity3d.com/Manual/async-await-support.html
- Unity 스크립팅 API — `SceneManager.LoadSceneAsync`, `AsyncOperation.allowSceneActivation`: https://docs.unity3d.com/ScriptReference/AsyncOperation-allowSceneActivation.html
- Unity 스크립팅 API — `EditorSceneManager.playModeStartScene`
- Cysharp/UniTask (GitHub): https://github.com/Cysharp/UniTask
