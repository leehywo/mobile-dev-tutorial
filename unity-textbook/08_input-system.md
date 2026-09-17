# 08. New Input System — 키보드·패드·터치 통합

> **이 장에서 배울 것**
> - 구 Input Manager와 Input System의 차이를 설명하고, 액션·액션 맵·바인딩·컴포지트의 관계를 설명할 수 있다
> - Value/Button/PassThrough 액션 타입을 구분해 고르고, `InputActionReference`로 코드에 연결한다
> - `PlayerInput` 컴포넌트 방식과 직접 연결 방식의 장단점을 비교해 선택할 수 있다
> - 모바일 가상 조이스틱(`OnScreenStick`)과 게임패드를 같은 액션으로 처리한다
> - 키 리바인딩 화면을 구현하고 결과를 저장·복원하며, 마지막 입력 장치에 따라 UI 표시를 바꾼다
>
> **선수 장**: 01, 04, 07 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 키보드·게임패드·모바일 가상 조이스틱이 모두 같은 코드로 동작하고, Esc/Start로 일시정지하며, 일시정지 화면에서 이동 키를 바꿀 수 있음

## 왜 필요한가

07장의 `PlayerMover.ReadMoveInput()`을 다시 보세요.

```csharp
if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) value.x -= 1f;
// ... 8줄 더
Vector2 stick = pad.leftStick.ReadValue();
```

동작은 하지만, 출시를 준비하면 다음 요구가 한꺼번에 들어옵니다.

1. **"AZERTY 키보드(프랑스)에서 WASD가 불편해요. 키를 바꾸게 해 주세요."** — Steam 리뷰에서 자주 보는 불만입니다. 지금 구조에선 키가 코드에 박혀 있어 바꿀 방법이 없습니다.
2. **모바일 빌드**를 하려니 키보드가 없습니다. 가상 조이스틱을 만들면 또 `if (touch...)` 분기가 생깁니다.
3. **일시정지**를 넣으려니 Esc와 게임패드 Start를 각각 검사해야 하고, 일시정지 중에는 이동 입력을 막아야 합니다. 이런 검사가 스크립트마다 흩어집니다.
4. 게임패드를 잡으면 화면의 "Esc: 일시정지" 안내가 **"Start: 일시정지"로 바뀌어야** 합니다.

공통 원인은 **"무엇을 하려는가(이동, 일시정지)"와 "어떤 장치의 어떤 버튼인가(A키, Start 버튼)"가 코드에 섞여 있는 것**입니다. Input System은 이 둘을 분리합니다. 코드는 "Move 액션의 값"만 읽고, 어떤 키가 Move인지는 데이터(에셋)와 플레이어의 설정이 결정합니다.

## 개념

### 구 Input Manager vs Input System

| 항목 | 구 Input Manager (`UnityEngine.Input`) | Input System (`com.unity.inputsystem`) |
|---|---|---|
| 코드 예 | `Input.GetAxis("Horizontal")`, `Input.GetKeyDown(KeyCode.Space)` | `moveAction.ReadValue<Vector2>()`, `jumpAction.WasPressedThisFrame()` |
| 설정 위치 | Project Settings > Input Manager (문자열 이름) | `.inputactions` 에셋 (타입 있는 액션) |
| 런타임 리바인딩 | 공식 지원 없음 | `PerformInteractiveRebinding` 내장 |
| 장치 추가 | 조이스틱 축 번호로 매핑, 기종마다 다름 | 게임패드 레이아웃 표준화(Xbox/PS/Switch 공통 이름) |
| 터치·가상 조이스틱 | 직접 구현 | `OnScreenStick`/`OnScreenButton` 제공 |
| 이벤트 방식 | 폴링만 | 폴링 + 콜백(`performed` 등) |
| Unity 6 상태 | 레거시 | 신규 프로젝트 기본 |

`Edit > Project Settings > Player > Other Settings > Active Input Handling`에서 어느 쪽을 쓸지 정합니다. 기본값이 **Input System Package (New)** 라면 `Input.GetAxis`는 예외를 던집니다. 옛 에셋 때문에 둘 다 필요하면 `Both`로 둘 수 있지만, 새 코드는 Input System으로만 작성하세요.

> JS 비유: 구 방식은 `keydown` 이벤트에서 `e.key === 'a'`를 직접 비교하는 것이고, Input System은 "단축키 설정 파일"을 두고 코드는 `commands.on('move', ...)`만 구독하는 VS Code의 keybindings 구조와 비슷합니다.

### 구성 요소 — 에셋 · 맵 · 액션 · 바인딩

```
CoinRushControls.inputactions        ← InputActionAsset (JSON 파일)
├── Control Schemes: Keyboard, Gamepad   ← 바인딩 그룹 (장치 묶음)
├── Action Map: Gameplay                  ← 상황별 액션 묶음 (켜고 끄는 단위)
│   ├── Action: Move   (Value, Vector2)
│   │   ├── Binding: 2D Vector Composite "WASD"   [Keyboard]
│   │   │   ├── up: <Keyboard>/w
│   │   │   ├── down: <Keyboard>/s
│   │   │   ├── left: <Keyboard>/a
│   │   │   └── right: <Keyboard>/d
│   │   ├── Binding: 2D Vector Composite "Arrows" [Keyboard]
│   │   └── Binding: <Gamepad>/leftStick          [Gamepad]
│   └── Action: Pause  (Button)
│       ├── Binding: <Keyboard>/escape            [Keyboard]
│       └── Binding: <Gamepad>/start              [Gamepad]
└── Action Map: UI
    └── Action: Cancel   (Button)   ← 일시정지 해제
```

메뉴의 포커스 이동(Navigate)·확인(Submit)·마우스/터치 포인터는 이 에셋에 만들지 않고, EventSystem의 `InputSystemUIInputModule`이 기본으로 가진 UI 액션을 그대로 씁니다(4단계에서 설명).

| 개념 | 설명 |
|---|---|
| **Action** | "하려는 일". 코드가 읽는 대상 |
| **Binding** | 액션과 실제 컨트롤의 연결. `<Keyboard>/w` 같은 **컨트롤 경로** 문자열 |
| **Composite** | 여러 버튼을 하나의 값으로 합성. WASD 4개 → `Vector2` |
| **Action Map** | 액션 묶음. **맵 단위로 Enable/Disable** 해서 상황(플레이 중/메뉴)을 전환 |
| **Control Scheme** | 바인딩을 장치 그룹으로 분류. UI에 "현재 장치 기준" 키 이름을 표시할 때 사용 |

### 액션 타입 — Value, Button, PassThrough

| 타입 | 의미 | 여러 장치가 동시에 입력하면 | 시작 시 현재 상태 확인 | 예 |
|---|---|---|---|---|
| **Value** | 연속적인 값 | **가장 크게 입력된 컨트롤 하나**만 추적(충돌 해소) | 예 (이미 기울인 스틱도 인식) | 이동, 조준 |
| **Button** | 눌림/뗌 | 충돌 해소 | 아니오 | 일시정지, 대시, 확인 |
| **PassThrough** | 가공 없이 모든 변화 전달 | 해소 안 함 — 모든 컨트롤의 변화가 그대로 옴 | 아니오 | 여러 장치를 동시에 따로 읽을 때, 마우스 델타 |

액션 타입은 값을 가공하는 프로세서가 아니라 **언제 `started`/`performed`가 오는지와, 활성화 직후 현재 상태를 확인하는지**를 정합니다. Button 액션에서도 `ReadValue<T>()`는 컨트롤의 실제 값을 돌려주지만, 콜백은 누름 임계값(press point)을 넘고 내려오는 시점 중심으로 오고 초기 상태 확인도 하지 않습니다. 그래서 "스틱을 기울인 채로 게임을 재개하면 입력이 안 들어온다" 같은 문제가 생겨 연속 값에 맞지 않습니다. `IsPressed()`/`WasPressedThisFrame()`은 값이 누름 임계값을 넘었는지로 판정합니다. PassThrough를 쓰면 충돌 해소가 없어 키보드와 스틱을 동시에 조작할 때 값이 번갈아 튑니다. **이동은 Value, 단발 동작은 Button**이 기본입니다.

액션은 세 단계 콜백을 가집니다.

| 콜백 | Button 액션 | Value 액션 |
|---|---|---|
| `started` | 눌리기 시작 | 0이 아닌 값이 들어오기 시작 |
| `performed` | 눌림 확정(인터랙션 없으면 누르는 순간) | 값이 바뀔 때마다 |
| `canceled` | 뗌 | 0으로 돌아옴 |

폴링 방식으로도 읽을 수 있습니다.

```csharp
Vector2 move = moveAction.ReadValue<Vector2>();   // 매 프레임 현재 값
if (pauseAction.WasPressedThisFrame()) { ... }    // 이번 프레임에 눌렸나
if (dashAction.IsPressed()) { ... }               // 누르고 있나
```

**연속 값(이동)은 폴링, 단발 이벤트(일시정지, 메뉴 열기)는 콜백**이 읽기 쉽습니다.

### 컴포지트, 프로세서, 인터랙션

- **2D Vector 컴포지트**의 `Mode`
  - `Digital Normalized`(기본): W+D를 (0.707, 0.707)로 정규화 → 대각선 속도 문제가 자동 해결됩니다.
  - `Digital`: (1, 1) 그대로.
  - `Analog`: 각 파트의 아날로그 값 사용(트리거 등).
- **프로세서(Processor)**: 값을 가공. `Stick Deadzone`(게임패드 스틱에 기본 적용), `Normalize Vector 2`, `Invert`, `Scale`.
- **인터랙션(Interaction)**: 언제 `performed`로 볼지. `Hold`(0.4초 누르면), `Tap`, `MultiTap`(더블탭), `Press`(누름/뗌 시점 선택).

### 코드와 연결하는 세 가지 방법

| 방식 | 코드 모양 | 장점 | 단점 |
|---|---|---|---|
| **`InputActionReference` 직접** | `[SerializeField] InputActionReference move;` → `move.action.ReadValue<Vector2>()` | 명시적, 어떤 스크립트에서든 사용, 흐름이 코드에 보임 | 맵 Enable/Disable를 직접 관리 |
| **`PlayerInput` 컴포넌트** | `void OnMove(InputValue v)` (Send Messages) 또는 UnityEvent 연결 | 설정만으로 동작, 로컬 멀티플레이 분할(`PlayerInputManager`), 컨트롤 스킴 자동 전환 | 메시지 이름 오타가 조용히 실패, 흐름이 Inspector에 숨음 |
| **C# 클래스 생성** | 에셋 Inspector의 `Generate C# Class` → `controls.Gameplay.Move.ReadValue<Vector2>()` | 타입 안전, 자동완성 | 에셋 인스턴스를 코드에서 만들고 공유 방법을 정해야 함 |

`PlayerInput`의 Behavior 옵션은 `Send Messages` / `Broadcast Messages` / `Invoke Unity Events` / `Invoke C# Events`입니다. Send Messages에서는 액션 이름 앞에 `On`을 붙인 메서드가 호출됩니다.

```csharp
// PlayerInput(Behavior: Send Messages) 방식 — 같은 오브젝트에 붙은 스크립트
using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerInputMessagesExample : MonoBehaviour
{
    private Vector2 move;
    private void OnMove(InputValue value) => move = value.Get<Vector2>();
    private void OnPause() => Debug.Log("Pause");   // Button은 인자 없이도 가능
}
```

코인 러시는 **1인 플레이, 스크립트 몇 개만 입력을 읽는 구조**이므로 흐름이 코드에 명확히 보이는 `InputActionReference` 직접 방식을 씁니다. 로컬 멀티플레이 게임이라면 `PlayerInput` + `PlayerInputManager`가 훨씬 편합니다.

### 프로젝트 전역 액션 (Unity 6)

Unity 6 신규 프로젝트에는 `Project Settings > Input System Package`에 **Project-wide Actions** 에셋(`InputSystem_Actions`, Player/UI 맵 포함)이 기본으로 지정되어 있고, 코드에서 `InputSystem.actions`로 접근합니다.

```csharp
InputAction move = InputSystem.actions.FindAction("Player/Move");
```

빠른 프로토타입에는 편하지만, 문자열 검색이라 이름을 바꾸면 런타임에 null이 됩니다. 이 장에서는 우리 게임 전용 에셋을 만들고 `InputActionReference`로 연결합니다(에셋 이름을 바꿔도 참조가 유지됨). 기본 에셋은 지우지 않아도 되지만, 두 에셋이 같은 키를 동시에 쓰면 헷갈리므로 사용하지 않는다면 Project-wide Actions 칸을 비워도 됩니다.

### 가상 조이스틱 — OnScreenStick의 원리

`OnScreenStick`은 UI 이미지를 드래그하면 **가상의 게임패드 장치를 만들어 그 스틱 값을 흉내** 냅니다. 컴포넌트의 `Control Path`를 `<Gamepad>/leftStick`으로 두면, `Move` 액션의 `<Gamepad>/leftStick` 바인딩이 그대로 값을 받습니다. **게임 코드는 조이스틱의 존재를 모릅니다.**

```
[터치 드래그] → OnScreenStick(UI) → 가상 Gamepad.leftStick → Move 액션 → PlayerMover
[실제 패드]   ─────────────────────→ Gamepad.leftStick ──────↗
[WASD]       ─────────────────────→ 2D Vector 컴포지트 ─────↗
```

주요 설정입니다(옵션 이름은 패키지 버전에 따라 조금 다를 수 있으니 Inspector를 확인하세요).

| 설정 | 의미 |
|---|---|
| Movement Range | 핸들이 움직이는 최대 거리(픽셀). 이 거리에서 값 1 |
| Control Path | 흉내 낼 컨트롤. `<Gamepad>/leftStick` |
| Behaviour | 스틱 원점이 고정인지, 터치한 곳으로 옮겨가는지(Dynamic Origin) |

OnScreenStick이 UI 포인터 이벤트를 받으려면 씬의 EventSystem이 **`InputSystemUIInputModule`** 을 써야 합니다.

### 리바인딩 — 오버라이드 레이어

리바인딩은 에셋 원본을 고치지 않습니다. 각 바인딩에 **`overridePath`** 를 덧씌우고, 실제로 쓰이는 경로는 `effectivePath`(= 오버라이드가 있으면 그것, 없으면 원본)가 됩니다.

```
binding.path          = "<Keyboard>/w"     ← 에셋에 저장된 기본값
binding.overridePath  = "<Keyboard>/z"     ← 플레이어가 바꾼 값
binding.effectivePath = "<Keyboard>/z"
```

그래서 "기본값으로 되돌리기"는 오버라이드만 지우면 되고, 저장할 것도 **오버라이드 목록만**입니다.

| API | 하는 일 |
|---|---|
| `action.PerformInteractiveRebinding(bindingIndex)` | 다음에 누르는 키를 기다려 오버라이드 설정. 빌더 패턴으로 옵션 추가 후 `.Start()` |
| `asset.SaveBindingOverridesAsJson()` | 모든 오버라이드를 JSON 문자열로 |
| `asset.LoadBindingOverridesFromJson(json)` | JSON의 오버라이드를 적용 |
| `action.RemoveBindingOverride(index)` / `asset.RemoveAllBindingOverrides()` | 기본값 복원 |
| `action.GetBindingDisplayString(index)` | "W", "Space", "Left Stick" 같은 표시용 이름 |

리바인딩 중인 액션은 **비활성 상태**여야 하고, 반환된 `RebindingOperation`은 끝나면 **`Dispose()`** 해야 합니다(내부 버퍼 누수).

### 마지막 입력 장치에 따라 UI 바꾸기

"Esc: 일시정지"를 "Start: 일시정지"로 바꾸려면 두 가지가 필요합니다.

1. **지금 어떤 장치를 쓰는지** — 액션이 `performed`될 때 그 입력의 `activeControl.device`를 확인합니다. 모든 액션 변화를 한곳에서 받을 수 있는 `InputSystem.onActionChange`가 편합니다.
2. **그 장치 기준 키 이름** — 컨트롤 스킴을 바인딩 그룹으로 지정해 두면 `action.GetBindingDisplayString(InputBinding.MaskByGroup("Gamepad"))`로 게임패드 바인딩의 이름만 얻을 수 있습니다.

주의: `OnScreenStick`이 만드는 가상 장치도 **Gamepad**로 보입니다. 모바일 빌드에서는 장치 감지 대신 플랫폼(`Application.isMobilePlatform`)으로 터치 UI를 결정하는 편이 단순합니다.

## 실습: 코인 러시에 적용하기

### 1단계: Input Actions 에셋 만들기

1. `Assets/_CoinRush/Input/` 폴더에서 우클릭 → `Create > Input Actions`, 이름 `CoinRushControls`. 더블클릭해 편집 창을 엽니다.
2. 왼쪽 위 `Control Schemes` 드롭다운 → `Add Control Scheme...`
   - 이름 `Keyboard`, `+`로 `Keyboard` 장치 추가(Required) → Save
   - 이름 `Gamepad`, `Gamepad` 장치 추가(Required) → Save
3. `Action Maps`의 `+`로 `Gameplay` 맵을 만듭니다.
4. `Gameplay`에 액션 `Move`를 추가하고 오른쪽 Properties에서 **Action Type: Value, Control Type: Vector 2**.
   - Move의 `+` → `Add Up\Down\Left\Right Composite`, 이름 `WASD`. Mode는 `Digital Normalized`.
   - 네 파트에 각각 `W`, `S`, `A`, `D`를 지정(Path 옆 `Listen` 버튼으로 키를 눌러 입력 가능). 각 파트의 `Use in control scheme`에서 **Keyboard 체크**.
   - 같은 방법으로 `Arrows` 컴포지트(Up/Down/Left/Right Arrow), Keyboard 체크.
   - Move의 `+` → `Add Binding`, Path `Left Stick [Gamepad]`, **Gamepad 체크**.
5. `Gameplay`에 액션 `Pause`: **Action Type: Button**. 바인딩 `Escape [Keyboard]`(Keyboard 체크), `Start [Gamepad]`(Gamepad 체크).
6. 맵 `UI`를 만들고 액션 `Cancel`을 추가합니다: Button, `Escape [Keyboard]`, `Start [Gamepad]`, `Button East [Gamepad]`. (메뉴 이동·확인은 EventSystem의 기본 UI 액션이 담당하므로 여기서 만들지 않습니다.)
7. 창 상단의 **Save Asset**을 누릅니다(Auto-Save 체크를 켜 두면 편합니다).

에셋을 Project 창에서 펼치면(▶) 각 액션이 하위 에셋으로 보입니다. 이것이 `InputActionReference`로 드래그할 대상입니다.

### 2단계: 액션 맵을 관리하는 ControlsManager

맵의 켜고 끄기, 바인딩 오버라이드 복원을 한 곳에서 맡깁니다. 이렇게 해야 "누가 액션을 켰는지"가 흩어지지 않습니다.

```csharp
using System;
using UnityEngine;
using UnityEngine.InputSystem;

// Assets/_CoinRush/Scripts/Input/ControlsManager.cs
[DefaultExecutionOrder(-50)]   // 입력을 읽는 스크립트들보다 먼저 Awake/OnEnable
public class ControlsManager : MonoBehaviour
{
    public const string BindingsPrefsKey = "input.bindingOverrides";

    // 씬에 하나뿐인 입력 관리자. 09장에서 Bootstrap 씬으로 옮기면 다른 씬의 스크립트는
    // Inspector로 참조할 수 없으므로, 처음부터 이 프로퍼티로 찾게 합니다.
    public static ControlsManager Instance { get; private set; }

    // 리바인딩·기본값 복원으로 바인딩이 바뀌었을 때 (버튼 라벨·HUD 안내 문구 갱신용)
    public static event Action BindingsChanged;

    [SerializeField] private InputActionAsset asset;

    private InputActionMap gameplay;
    private InputActionMap ui;

    public InputActionAsset Asset => asset;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStatics() { Instance = null; BindingsChanged = null; }   // 도메인 리로드를 꺼도 안전

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Debug.LogError("ControlsManager가 두 개 있습니다. 하나만 두세요.", this);
            enabled = false;   // OnEnable(맵 켜기)이 돌지 않게
            return;
        }
        Instance = this;
        gameplay = asset.FindActionMap("Gameplay", throwIfNotFound: true);
        ui = asset.FindActionMap("UI", throwIfNotFound: true);
        LoadBindingOverrides();
    }

    private void OnDestroy()
    {
        if (Instance == this) Instance = null;
    }

    private void OnEnable() => UseGameplay();

    private void OnDisable() => asset.Disable();

    public void UseGameplay()
    {
        ui.Disable();
        gameplay.Enable();
    }

    public void UseUI()
    {
        gameplay.Disable();
        ui.Enable();
    }

    public void SaveBindingOverrides()
    {
        PlayerPrefs.SetString(BindingsPrefsKey, asset.SaveBindingOverridesAsJson());
        PlayerPrefs.Save();
        BindingsChanged?.Invoke();
    }

    public void LoadBindingOverrides()
    {
        string json = PlayerPrefs.GetString(BindingsPrefsKey, string.Empty);
        if (!string.IsNullOrEmpty(json)) asset.LoadBindingOverridesFromJson(json);
    }

    public void ResetAllBindings()
    {
        asset.RemoveAllBindingOverrides();
        PlayerPrefs.DeleteKey(BindingsPrefsKey);
        BindingsChanged?.Invoke();
    }
}
```

1. Hierarchy에 빈 오브젝트 `Controls`를 만들고 `ControlsManager`를 붙인 뒤 `Asset`에 `CoinRushControls`를 넣습니다. (09장에서 부트스트랩 씬으로 옮깁니다. 그래서 다른 스크립트는 Inspector 참조 대신 `ControlsManager.Instance`로 찾습니다.)
2. 키 설정은 "설정값"이라 `PlayerPrefs`로 충분합니다. 게임 진행 데이터는 10장의 세이브 파일에 둡니다.

> **왜 PlayerMover가 직접 `Enable()`하지 않나요?** 액션 하나를 개별로 켜면 맵이 꺼져 있어도 그 액션만 살아납니다. 일시정지 중 맵을 꺼도 PlayerMover의 `OnEnable`이 다시 켜 버리는 버그가 생깁니다. 켜고 끄는 권한은 한 곳에만 둡니다.

### 3단계: PlayerMover를 액션 기반으로

07장의 `PlayerMover`에서 **필드 하나를 추가하고 `Update`를 바꾸고 `ReadMoveInput` 메서드를 삭제**합니다. FixedUpdate·넉백 코드는 그대로입니다.

```csharp
// using 추가 (이미 있음): using UnityEngine.InputSystem;

// 필드 추가 — [Header("속도")] 위에
[Header("입력")]
[SerializeField] private InputActionReference moveAction;

// Update 교체
private void Update()
{
    MoveInput = CanMove ? Vector2.ClampMagnitude(moveAction.action.ReadValue<Vector2>(), 1f) : Vector2.zero;
    if (MoveInput.sqrMagnitude > 0.01f) Facing = MoveInput.normalized;
}

// private static Vector2 ReadMoveInput() { ... } → 메서드 전체 삭제
```

- Player를 선택하고 `Move Action`에 Project 창의 `CoinRushControls > Gameplay/Move`를 드래그합니다.
- `ClampMagnitude`는 컴포지트가 이미 정규화하지만, 스틱 값이 부동소수 오차로 1을 살짝 넘는 경우를 위한 안전장치입니다.
- 맵이 꺼져 있으면 `ReadValue`는 0을 반환하므로, 일시정지 중 이동이 자동으로 멈춥니다.

### 4단계: 일시정지 액션

1. Canvas 아래에 `PausePanel`(반투명 전체 화면 Image + "일시정지" 텍스트 + `Resume` 버튼)을 만들고 비활성화합니다.
2. EventSystem을 선택합니다. 입력 모듈이 `StandaloneInputModule`이라면 Inspector의 **Replace with InputSystemUIInputModule** 버튼을 누릅니다. 새 모듈의 **Actions Asset** 칸은 기본값(Unity가 지정한 기본 UI 액션 에셋)을 **그대로 둡니다**. 이 기본 에셋에 Point·Click(마우스·터치)과 Navigate·Submit·Cancel(키보드·패드 메뉴 조작)이 모두 들어 있고, 모듈이 스스로 켜 둡니다. 우리 `CoinRushControls`를 여기에 넣으면 Point·Click 액션이 없어 마우스·터치 UI와 5단계의 가상 조이스틱이 동작하지 않고, 모듈이 켜는 액션이 `ControlsManager`의 맵 전환과 겹칩니다.
3. 아래 스크립트를 `Controls` 오브젝트에 붙이고 참조를 연결합니다. **State Machine**에는 04장 `GameSystems`의 `GameStateMachine`, **First Selected**에는 `PausePanel`의 `Resume` 버튼을 넣습니다.
4. `Resume` 버튼의 On Click ()에 `Controls` → `PauseController.Resume`을 연결합니다.

```csharp
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

// Assets/_CoinRush/Scripts/Input/PauseController.cs
public class PauseController : MonoBehaviour
{
    [SerializeField] private GameStateMachine stateMachine;           // 04장 — Playing에서만 일시정지 허용
    [SerializeField] private InputActionReference pauseAction;        // Gameplay/Pause
    [SerializeField] private InputActionReference cancelAction;       // UI/Cancel
    [SerializeField] private GameObject pausePanel;
    [Tooltip("일시정지 창이 열릴 때 패드·키보드 포커스를 줄 버튼 (Resume)")]
    [SerializeField] private GameObject firstSelected;

    private GameObject selectedBeforePause;

    public bool IsPaused { get; private set; }

    private void OnEnable()
    {
        pauseAction.action.performed += OnPausePerformed;
        cancelAction.action.performed += OnCancelPerformed;
    }

    private void OnDisable()
    {
        pauseAction.action.performed -= OnPausePerformed;
        cancelAction.action.performed -= OnCancelPerformed;
        if (IsPaused) Resume();   // 씬 전환 등으로 꺼질 때 timeScale 0이 남지 않게
    }

    private void OnPausePerformed(InputAction.CallbackContext ctx) => Pause();

    private void OnCancelPerformed(InputAction.CallbackContext ctx)
    {
        if (RebindButton.IsAnyRebinding) return;   // 리바인딩 취소 키(Esc)와 겹치지 않게
        Resume();
    }

    // 모바일 Pause 버튼의 OnClick에도 연결 (5단계)
    public void Pause()
    {
        if (IsPaused) return;
        // 04장 LevelUp도 timeScale 0을 씁니다. 거기서 일시정지했다가 Resume이 timeScale을 1로 되돌리면
        // 강화 선택 중에 게임이 흘러가므로, Title·LevelUp·Result에서는 들어가지 않습니다.
        if (stateMachine == null || stateMachine.Current != stateMachine.Playing) return;

        ControlsManager controls = ControlsManager.Instance;
        if (controls == null) { Debug.LogError("ControlsManager가 씬에 없습니다.", this); return; }

        IsPaused = true;
        Time.timeScale = 0f;
        controls.UseUI();
        pausePanel.SetActive(true);

        // 패드·키보드로 바로 조작할 수 있게 첫 버튼에 포커스
        EventSystem es = EventSystem.current;
        if (es != null)
        {
            selectedBeforePause = es.currentSelectedGameObject;
            es.SetSelectedGameObject(firstSelected);
        }
    }

    // 리바인딩 화면의 "기본값으로" 버튼 OnClick에 연결 (7단계)
    public void ResetAllBindings()
    {
        if (ControlsManager.Instance != null) ControlsManager.Instance.ResetAllBindings();
    }

    // Resume 버튼의 OnClick에도 연결
    public void Resume()
    {
        if (!IsPaused) return;
        IsPaused = false;
        Time.timeScale = 1f;
        if (ControlsManager.Instance != null) ControlsManager.Instance.UseGameplay();   // 씬 종료 중엔 이미 파괴됐을 수 있음
        if (pausePanel != null) pausePanel.SetActive(false);

        EventSystem es = EventSystem.current;
        if (es != null)
            es.SetSelectedGameObject(selectedBeforePause != null && selectedBeforePause.activeInHierarchy ? selectedBeforePause : null);
        selectedBeforePause = null;
    }
}
```

- `Time.timeScale = 0`이어도 Input System은 기본 설정(`Update Mode: Process Events In Dynamic Update`)에서 Update 주기로 이벤트를 처리하므로 Resume 입력이 동작합니다. 이 값을 `Fixed Update`로 바꾸면 timeScale 0에서 입력이 멈추니 주의하세요.
- Esc가 `Gameplay/Pause`와 `UI/Cancel` 양쪽에 있지만, 두 맵이 동시에 켜지지 않으므로 한 번 누름이 "일시정지 → 즉시 해제"로 이어지지 않습니다.
- **상태 머신과의 관계**: 04장 LevelUp 상태에서도 Gameplay 맵은 켜져 있어 Esc가 들어옵니다. `stateMachine.Current != stateMachine.Playing` 검사가 없으면 "레벨업 창 → Esc → Resume"으로 `timeScale`이 1이 되어 강화를 고르는 동안 게임이 진행됩니다. 일시정지를 상태 머신의 정식 상태(`PausedState`)로 옮기는 방법은 연습 문제 3에서 다룹니다.
- 포커스: `SetSelectedGameObject(firstSelected)`가 없으면 패드로 일시정지해도 선택된 버튼이 없어 Submit(South 버튼)이 아무 일도 하지 않습니다. 닫을 때는 이전 선택으로 되돌립니다.

### 5단계: 모바일 가상 조이스틱

1. Canvas의 `Canvas Scaler`를 `Scale With Screen Size`, Reference Resolution 1920×1080으로 둡니다(11장에서 자세히).
2. Canvas 아래에 빈 UI 오브젝트 `MobileControls`를 만들고, 그 아래 `UI > Image`로 `StickBase`(원형 스프라이트, 220×220, 좌하단 앵커, 반투명)를 만듭니다.
3. `StickBase`의 자식으로 `UI > Image` `StickHandle`(100×100)을 만들고 `Add Component > On-Screen Stick`을 붙입니다.
   - Movement Range: 60
   - Control Path: `Left Stick [Gamepad]` (`<Gamepad>/leftStick`)
4. `MobileControls`에 아래 스크립트를 붙입니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Input/MobileControlsVisibility.cs
public class MobileControlsVisibility : MonoBehaviour
{
    [Tooltip("에디터에서 테스트할 때 강제로 표시")]
    [SerializeField] private bool forceShowInEditor = true;

    private void Awake()
    {
        bool show = Application.isMobilePlatform;
#if UNITY_EDITOR
        show |= forceShowInEditor;
#endif
        gameObject.SetActive(show);
    }
}
```

5. **모바일 일시정지 버튼**: 터치 기기에는 Esc·Start가 없으므로 `MobileControls` 아래에 `UI > Button - TextMeshPro` `PauseButton`(우상단 앵커, 120×120, 텍스트 "II")을 만들고, On Click ()에 `Controls` → `PauseController.Pause`를 연결합니다. `MobileControls`의 자식이므로 PC 빌드에서는 함께 숨겨집니다. 재개는 `PausePanel`의 `Resume` 버튼을 터치합니다.
6. 에디터에서 Play → Game 뷰에서 핸들을 마우스로 드래그하면 플레이어가 움직입니다. `Window > General > Device Simulator`로 전환하면 폰 화면 비율로 확인할 수 있습니다.
7. 조이스틱을 놓으면 핸들이 원위치로 돌아가고 값이 0이 되어, 07장의 감속 로직대로 멈추는지 확인합니다. `PauseButton`을 클릭(터치)하면 일시정지 창이 열리고 `Resume`으로 돌아오는지도 확인합니다.

> 가상 조이스틱이 가상 Gamepad를 만들기 때문에 이 순간 `Gamepad.current`가 가상 장치가 될 수 있습니다. 07장 방식처럼 `Gamepad.current`를 직접 읽는 코드가 남아 있으면 예상과 다르게 동작하니, 모든 입력을 액션으로 옮기세요.

### 6단계: 입력 장치 감지와 안내 문구

```csharp
using System;
using UnityEngine;
using UnityEngine.InputSystem;

// Assets/_CoinRush/Scripts/Input/InputDeviceWatcher.cs
public enum InputDeviceKind { Keyboard, Gamepad, Touch }

public static class InputDeviceWatcher
{
    public static InputDeviceKind Current { get; private set; } =
        Application.isMobilePlatform ? InputDeviceKind.Touch : InputDeviceKind.Keyboard;

    public static event Action<InputDeviceKind> Changed;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void ResetStatics()   // Enter Play Mode Options로 도메인 리로드를 꺼도 안전하게
    {
        Changed = null;
        InputSystem.onActionChange -= OnActionChange;
        InputSystem.onActionChange += OnActionChange;
    }

    private static void OnActionChange(object obj, InputActionChange change)
    {
        if (change != InputActionChange.ActionPerformed) return;
        if (obj is not InputAction action || action.activeControl == null) return;

        InputDeviceKind kind = Classify(action.activeControl.device);
        if (kind == Current) return;
        Current = kind;
        Changed?.Invoke(kind);
    }

    private static InputDeviceKind Classify(InputDevice device)
    {
        if (Application.isMobilePlatform) return InputDeviceKind.Touch;   // 가상 패드도 터치로 간주
        return device is Gamepad ? InputDeviceKind.Gamepad : InputDeviceKind.Keyboard;
    }
}
```

```csharp
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

// Assets/_CoinRush/Scripts/Input/ActionPromptLabel.cs — "Esc: 일시정지" 텍스트에 부착
[RequireComponent(typeof(TextMeshProUGUI))]
public class ActionPromptLabel : MonoBehaviour
{
    [SerializeField] private InputActionReference action;
    [SerializeField] private string format = "{0}: 일시정지";

    private TextMeshProUGUI label;

    private void Awake() => label = GetComponent<TextMeshProUGUI>();

    private void OnEnable()
    {
        InputDeviceWatcher.Changed += Refresh;
        ControlsManager.BindingsChanged += RefreshCurrent;   // 리바인딩으로 키가 바뀌면 다시 표시
        RefreshCurrent();
    }

    private void OnDisable()
    {
        InputDeviceWatcher.Changed -= Refresh;
        ControlsManager.BindingsChanged -= RefreshCurrent;
    }

    private void RefreshCurrent() => Refresh(InputDeviceWatcher.Current);

    public void Refresh(InputDeviceKind kind)
    {
        if (kind == InputDeviceKind.Touch) { label.text = string.Empty; return; }   // 모바일은 5단계의 PauseButton으로 대체
        string group = kind == InputDeviceKind.Gamepad ? "Gamepad" : "Keyboard";
        string keyName = action.action.GetBindingDisplayString(InputBinding.MaskByGroup(group));
        label.text = string.Format(format, keyName);
    }
}
```

1. HUD에 TextMeshPro 텍스트 `PauseHint`를 만들고 `ActionPromptLabel`을 붙인 뒤 `Action`에 `Gameplay/Pause`를 연결합니다.
2. 텍스트 대신 아이콘을 쓰려면 `InputDeviceKind`별 `Sprite`를 `Image`에 바꿔 끼우면 됩니다. 기종별 아이콘(Xbox의 Menu, PlayStation의 Options)까지 구분하려면 `device is UnityEngine.InputSystem.DualShock.DualShockGamepad`처럼 구체 타입을 검사합니다.
3. 리바인딩(다음 단계)으로 키를 바꾸면 `ControlsManager.SaveBindingOverrides`/`ResetAllBindings`가 `BindingsChanged`를 발행하고, 이 라벨이 구독해 다시 그립니다. 같은 장치를 계속 써서 `InputDeviceWatcher.Changed`가 오지 않아도 갱신됩니다.

### 7단계: 키 리바인딩 화면 (최소 구현)

일시정지 패널 안에 "이동 위/아래/왼쪽/오른쪽", "일시정지" 5개 줄을 만듭니다. 각 줄은 `라벨 텍스트 + 버튼(현재 키 표시)`입니다.

```csharp
using System;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// Assets/_CoinRush/Scripts/Input/RebindButton.cs
public class RebindButton : MonoBehaviour
{
    public static bool IsAnyRebinding { get; private set; }

    [SerializeField] private InputActionReference action;
    [Tooltip("컴포지트 파트 이름(up/down/left/right). 일반 바인딩이면 비워 둠")]
    [SerializeField] private string compositePart = "";
    [Tooltip("이 버튼이 바꿀 바인딩의 컨트롤 스킴(그룹)")]
    [SerializeField] private string group = "Keyboard";
    [SerializeField] private Button button;
    [SerializeField] private TextMeshProUGUI keyLabel;

    private InputActionRebindingExtensions.RebindingOperation operation;
    private int bindingIndex = -1;

    private void Awake()
    {
        bindingIndex = FindBindingIndex();
        if (bindingIndex < 0)
            Debug.LogError($"{name}: '{action.action.name}'에서 part='{compositePart}', group='{group}' 바인딩을 찾지 못했습니다.", this);
        button.onClick.AddListener(StartRebind);
    }

    private void OnEnable()
    {
        ControlsManager.BindingsChanged += UpdateLabel;   // 다른 버튼·"기본값으로"가 바꾼 것도 반영
        UpdateLabel();
    }

    private void OnDisable()
    {
        ControlsManager.BindingsChanged -= UpdateLabel;
        CleanUp();
    }

    private int FindBindingIndex()
    {
        var bindings = action.action.bindings;
        for (int i = 0; i < bindings.Count; i++)
        {
            InputBinding b = bindings[i];
            if (b.isComposite) continue;
            bool partMatches = string.IsNullOrEmpty(compositePart)
                ? !b.isPartOfComposite
                : b.isPartOfComposite && string.Equals(b.name, compositePart, StringComparison.OrdinalIgnoreCase);
            bool groupMatches = b.groups != null && b.groups.Contains(group);
            if (partMatches && groupMatches) return i;   // 첫 번째 일치(WASD가 Arrows보다 위에 있어야 함)
        }
        return -1;
    }

    private void StartRebind()
    {
        if (bindingIndex < 0 || IsAnyRebinding) return;

        InputAction a = action.action;
        bool wasEnabled = a.enabled;
        a.Disable();   // 리바인딩 중에는 반드시 비활성
        IsAnyRebinding = true;
        keyLabel.text = "키를 누르세요... (Esc 취소)";

        operation = a.PerformInteractiveRebinding(bindingIndex)
            .WithControlsHavingToMatchPath(group == "Gamepad" ? "<Gamepad>" : "<Keyboard>")
            .WithCancelingThrough("<Keyboard>/escape")
            .OnMatchWaitForAnother(0.1f)
            .OnCancel(_ => Finish(wasEnabled, save: false))
            .OnComplete(_ => Finish(wasEnabled, save: true))
            .Start();
    }

    private void Finish(bool reEnable, bool save)
    {
        CleanUp();
        if (reEnable) action.action.Enable();
        if (save && ControlsManager.Instance != null)
            ControlsManager.Instance.SaveBindingOverrides();   // 저장 + BindingsChanged 발행 → 라벨·HUD 갱신
        UpdateLabel();
    }

    private void CleanUp()
    {
        operation?.Dispose();   // Dispose하지 않으면 내부 메모리가 샘
        operation = null;
        IsAnyRebinding = false;
    }

    public void ResetToDefault()
    {
        if (bindingIndex < 0) return;
        action.action.RemoveBindingOverride(bindingIndex);
        if (ControlsManager.Instance != null) ControlsManager.Instance.SaveBindingOverrides();
        UpdateLabel();
    }

    private void UpdateLabel()
    {
        if (keyLabel == null || bindingIndex < 0) return;
        keyLabel.text = action.action.GetBindingDisplayString(bindingIndex);
    }
}
```

1. 일시정지 패널 안에 `Vertical Layout Group`을 가진 `RebindList`를 만들고, `라벨(TMP) + Button(자식 TMP)` 줄 5개를 배치합니다.
2. 각 버튼 오브젝트에 `RebindButton`을 붙이고 설정합니다.

| 줄 | Action | Composite Part | Group |
|---|---|---|---|
| 위 | Gameplay/Move | up | Keyboard |
| 아래 | Gameplay/Move | down | Keyboard |
| 왼쪽 | Gameplay/Move | left | Keyboard |
| 오른쪽 | Gameplay/Move | right | Keyboard |
| 일시정지 | Gameplay/Pause | (비움) | Keyboard |

3. "기본값으로" 버튼을 하나 만들어 OnClick에 `Controls` → `PauseController.ResetAllBindings`를 연결합니다(09장에서 `ControlsManager`가 다른 씬으로 옮겨가도 연결이 끊기지 않도록 같은 씬의 `PauseController`를 거칩니다). `BindingsChanged`가 발행되므로 모든 `RebindButton` 라벨과 HUD 안내 문구가 함께 갱신됩니다.

> 일시정지 중에는 Gameplay 맵이 꺼져 있으므로 `wasEnabled`가 false이고, 리바인딩 뒤에도 켜지지 않습니다. Resume할 때 `ControlsManager.UseGameplay()`가 맵을 켭니다.

### 확인하기

- 키보드 WASD·방향키, 게임패드 왼쪽 스틱으로 모두 이동하며, 대각선이 더 빠르지 않다. 스틱을 살짝 기울이면 천천히 움직인다.
- (Playing 상태에서) Esc 또는 Start를 누르면 게임이 멈추고 패널이 뜨며, `Resume` 버튼이 선택된 상태라 패드 South 버튼으로 바로 재개할 수 있다. 이 상태에서 WASD를 눌러도 플레이어가 움직이지 않는다. 다시 Esc/Start(또는 B 버튼)로 재개된다.
- 타이틀·레벨업 창·결과 화면에서 Esc/Start를 눌러도 일시정지 창이 뜨지 않고, 레벨업 창에서 Esc를 누른 뒤에도 강화를 고르기 전까지 게임이 멈춰 있다.
- 리바인딩으로 일시정지 키를 바꾸고 재개하면, 장치를 바꾸지 않아도 HUD 안내 문구가 새 키 이름으로 바뀌어 있다.
- 게임패드 버튼을 한 번 누르면 HUD의 "Esc: 일시정지"가 "Start: 일시정지"로 바뀌고, 키보드를 누르면 되돌아온다.
- 일시정지 화면에서 "위"를 Z로 바꾸면 재개 후 Z로 위로 이동하고, **Play를 껐다 켜도 Z가 유지**된다. "기본값으로"를 누르면 W로 돌아온다.
- 에디터(또는 Device Simulator)에서 가상 조이스틱을 드래그하면 이동하고, 놓으면 멈춘다. 우상단 `PauseButton`을 누르면 일시정지되고 `Resume` 터치로 재개된다.

## 흔한 실수

1. **`ReadValue`가 항상 0을 반환한다** → 액션(맵)이 활성화되지 않음 → `ControlsManager`가 씬에 있고 `UseGameplay()`가 호출되는지, `InputActionReference`가 올바른 에셋의 액션을 가리키는지 확인합니다.
2. **`InvalidOperationException: You are trying to read Input using the UnityEngine.Input class`** → Active Input Handling이 New인데 옛 `Input.GetAxis` 코드(기초 트랙, 에셋 스토어 스크립트)가 남음 → 해당 코드를 액션으로 교체하거나, 임시로 `Both`로 둡니다.
3. **리바인딩 시작 시 예외가 나거나 바로 끝난다** → 액션이 활성 상태에서 리바인딩 시작, 또는 버튼 클릭에 쓴 마우스 클릭/Enter가 새 키로 잡힘 → 시작 전에 `Disable()`, `WithControlsHavingToMatchPath`로 장치를 제한하고 `OnMatchWaitForAnother(0.1f)`로 약간 기다립니다.
4. **재시작하면 바꾼 키가 사라진다** → 오버라이드를 저장하지 않았거나, 로드 시점이 액션 사용 이후 → 완료 시 `SaveBindingOverridesAsJson`을 저장하고, 가장 먼저 도는 `Awake`에서 `LoadBindingOverridesFromJson`.
5. **일시정지 해제가 안 된다(timeScale 0에서 입력 무반응)** → Input System 설정의 Update Mode가 Fixed Update → `Process Events In Dynamic Update`로 되돌립니다.
6. **가상 조이스틱을 드래그해도 반응이 없다** → EventSystem에 `StandaloneInputModule`이 붙어 있거나 Canvas에 `Graphic Raycaster`가 없음, 또는 조이스틱 위를 다른 투명 UI가 덮음 → `InputSystemUIInputModule`로 교체하고 Raycast Target을 점검합니다.

## 연습 문제

**1. ★☆☆ 대시 액션**
07장 연습 문제의 대시를 액션으로 옮기세요. `Gameplay/Dash`(Button, Space / Button South)를 추가하고 `WasPressedThisFrame()`으로 읽습니다.

<details>
<summary>힌트·해설</summary>

`PlayerMover`에 `[SerializeField] InputActionReference dashAction;`을 추가하고, `Update`에서 `if (dashAction.action.WasPressedThisFrame()) dashRequested = true;`, `FixedUpdate`에서 소비합니다. 콜백(`performed +=`)으로도 가능하지만 플래그를 FixedUpdate에서 소비해야 하는 건 같으므로, 이 경우엔 폴링이 더 단순합니다. 액션 에셋을 저장하는 것을 잊지 마세요 — 저장 전에는 새 액션이 `InputActionReference` 목록에 나타나지 않습니다.

</details>

**2. ★★☆ 중복 키 방지**
"위"를 이미 "왼쪽"에 쓰인 A 키로 바꾸려 하면 거부하고 "이미 사용 중인 키입니다"를 표시하세요.

<details>
<summary>힌트·해설</summary>

`OnComplete`에서 새 경로 `action.bindings[bindingIndex].effectivePath`를 얻고, 같은 맵의 모든 액션·바인딩을 돌며 자기 자신을 제외하고 `effectivePath`가 같은 것이 있는지 검사합니다. 중복이면 `action.RemoveBindingOverride(bindingIndex)`로 되돌리거나(기존 오버라이드가 있었다면 이전 경로를 저장해 두었다가 `ApplyBindingOverride(bindingIndex, previousPath)`), 다시 `StartRebind()`를 호출해 재입력을 받습니다. `OnPotentialMatch`에서 `op.Cancel()`로 미리 막는 방법도 있습니다.

</details>

**3. ★★☆ 일시정지를 GameStateMachine의 상태로 옮기기**
본문의 `PauseController`는 `stateMachine.Current != stateMachine.Playing` 검사로 Title·LevelUp·Result에서의 일시정지를 막았습니다. 이 규칙을 04장 `GameStateMachine`의 정식 상태 `PausedState`로 옮기세요. Playing에서만 들어갈 수 있고, 재개하면 **이전 상태(Playing)** 로 돌아가야 하며, `Current`를 보는 다른 코드(예: 레벨업 전환)가 일시정지 중임을 알 수 있어야 합니다.

<details>
<summary>힌트·해설</summary>

- `PausedState`의 `Enter`에서 `Time.timeScale = 0`, `controls.UseUI()`, 패널 표시. `Exit`에서 반대로.
- 진입 규칙은 본문과 같습니다: "PauseController가 `stateMachine.Current == stateMachine.Playing`일 때만 `ChangeState(stateMachine.Paused)`". `PauseController.Pause/Resume`은 상태 전환만 요청하고, timeScale·맵 전환·패널·포커스는 `PausedState`로 옮깁니다. `controls`는 `ControlsManager.Instance`로 얻습니다.
- LevelUp 상태도 timeScale 0과 UI 맵을 쓰므로, 공통 부분을 `ModalState` 기반 클래스로 뽑을 수 있습니다.
- "이전 상태로 복귀"가 여러 곳에서 필요해지면 상태 스택(push/pop) 구조로 확장합니다. 04장의 머신이 단일 상태라면 `PausedState`가 `returnTo` 상태를 필드로 들고 있게 하는 것으로 충분합니다.

</details>

**4. ★★★ 게임패드 리바인딩과 아이콘 (확장 과제)**
리바인딩 화면에 "게임패드" 탭을 추가해 일시정지 버튼을 패드 버튼으로 바꿀 수 있게 하고, 키 이름 텍스트 대신 버튼 아이콘 스프라이트를 표시하세요. Xbox와 PlayStation 패드에서 다른 아이콘이 나오면 완성입니다.

<details>
<summary>힌트·해설</summary>

- `RebindButton`의 `group`을 `Gamepad`로 둔 인스턴스를 만들면 `WithControlsHavingToMatchPath("<Gamepad>")`로 패드 입력만 받습니다. 취소 키는 패드에도 필요하므로 `WithCancelingThrough`는 키보드 Esc를 그대로 두거나 `<Gamepad>/select`를 고려합니다.
- 아이콘 매핑: `action.GetBindingDisplayString(bindingIndex, out string deviceLayoutName, out string controlPath)` 오버로드가 장치 레이아웃과 컨트롤 경로(`buttonSouth` 등)를 돌려줍니다. `ScriptableObject`에 `controlPath → Sprite` 표를 두 벌(Xbox, PS) 만들고, `InputSystem.IsFirstLayoutBasedOnSecond(deviceLayoutName, "DualShockGamepad")`로 어느 표를 쓸지 고릅니다.
- Input System 패키지의 **Rebinding UI** 샘플(Package Manager > Input System > Samples)이 이 구조의 완성본입니다. 직접 만들어 본 뒤 비교해 보세요.

</details>

## 셀프 체크

**1. Input System이 "무엇을 하려는가"와 "어떤 키인가"를 분리한다는 말의 의미를, 리바인딩과 모바일 대응을 예로 설명해 보세요.**

<details>
<summary>모범 답안</summary>

코드는 `Move` 액션의 값만 읽고, 그 값이 어떤 컨트롤에서 오는지는 에셋의 바인딩과 런타임 오버라이드가 결정합니다. 그래서 리바인딩은 코드 변경 없이 바인딩의 `overridePath`만 바꾸면 되고, 모바일은 `OnScreenStick`이 가상 게임패드 스틱 값을 만들어 기존 `<Gamepad>/leftStick` 바인딩으로 들어오므로 게임 코드에 터치 분기가 필요 없습니다.

</details>

**2. 이동 액션에 Value 타입을, 일시정지에 Button 타입을 쓰는 이유와 PassThrough가 필요한 상황을 설명해 보세요.**

<details>
<summary>모범 답안</summary>

Value는 연속 값을 전달하며 여러 컨트롤이 동시에 입력될 때 가장 크게 입력된 하나를 추적하고, 활성화 시 현재 상태도 확인하므로 이동에 적합합니다. Button은 값을 0/1로 바꾸는 것이 아니라 누름 임계값을 기준으로 `performed`가 오고 초기 상태 확인을 하지 않는 타입이므로, 눌림/뗌의 단발 이벤트인 일시정지에 맞습니다. PassThrough는 충돌 해소 없이 모든 컨트롤의 변화를 그대로 전달하므로, 여러 장치의 입력을 구분 없이 모두 받아야 하거나 마우스 델타처럼 가공 없는 원시 변화가 필요할 때 씁니다.

</details>

**3. 액션 맵 Enable/Disable 권한을 한 컴포넌트에 모으는 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

여러 스크립트가 각자 `OnEnable`에서 액션을 켜면, 일시정지 등으로 맵을 꺼도 다른 스크립트가 개별 액션을 다시 켜서 입력이 새어 나갑니다. 또 누가 언제 켰는지 추적이 어려워집니다. 맵 전환을 `ControlsManager` 한 곳에서만 하면 "지금은 Gameplay/UI 중 어느 것이 켜져 있다"는 상태가 하나로 정해지고, 바인딩 로드 순서도 보장할 수 있습니다.

</details>

**4. `PlayerInput` 컴포넌트 방식과 `InputActionReference` 직접 방식 중 어떤 게임에 무엇을 고를지 설명해 보세요.**

<details>
<summary>모범 답안</summary>

로컬 멀티플레이(패드 여러 개를 각 플레이어에게 자동 배정)나 컨트롤 스킴 자동 전환이 중요한 게임은 `PlayerInput` + `PlayerInputManager`가 많은 일을 대신해 줍니다. 1인용이고 입력을 읽는 스크립트가 적은 게임은 `InputActionReference` 직접 방식이 흐름이 코드에 드러나 디버깅이 쉽고 메시지 이름 오타 같은 조용한 실패가 없습니다.

</details>

**5. 리바인딩 결과를 저장할 때 에셋 전체가 아니라 오버라이드만 저장하는 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

리바인딩은 원본 `path`를 바꾸지 않고 `overridePath`만 덧씌웁니다. 오버라이드만 저장하면 데이터가 작고, 게임 업데이트로 기본 바인딩(새 액션 추가 등)이 바뀌어도 플레이어가 바꾼 부분만 다시 적용되어 충돌이 적습니다. 기본값 복원도 오버라이드 삭제만으로 끝납니다.

</details>

## 핵심 요약

- Input System은 액션(의도)과 바인딩(장치 입력)을 분리합니다. 코드는 액션만 읽습니다.
- 구조는 에셋 → 액션 맵(켜고 끄는 단위) → 액션 → 바인딩/컴포지트. 컨트롤 스킴은 바인딩의 장치 그룹입니다.
- 이동은 Value(Vector2) + 2D Vector 컴포지트(Digital Normalized), 단발 동작은 Button. 연속 값은 폴링, 단발은 콜백이 읽기 쉽습니다.
- 1인 게임은 `InputActionReference` 직접 연결이 명확하고, 로컬 멀티는 `PlayerInput`이 편합니다. 맵 Enable/Disable는 한 곳에서만.
- `OnScreenStick`은 가상 게임패드를 만들어 기존 바인딩으로 값을 흘려보냅니다. EventSystem은 `InputSystemUIInputModule`이어야 합니다.
- 리바인딩은 `PerformInteractiveRebinding`(액션 비활성, 완료 후 `Dispose`), 저장은 `SaveBindingOverridesAsJson`/`LoadBindingOverridesFromJson`.
- 장치 표시는 `InputSystem.onActionChange`로 마지막 장치를 추적하고 `InputBinding.MaskByGroup`으로 해당 장치의 키 이름을 얻습니다.

## 더 읽을거리

- Input System 패키지 매뉴얼 1.11 (Unity): https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/index.html — 이 장의 코드·에디터 조작은 1.11 문서 기준입니다. 설치된 버전은 `Window > Package Manager > Input System`에서 확인하고, 다르면 주소의 `@1.11`을 그 버전으로 바꿔 보세요.
- 같은 매뉴얼의 "Interactive rebinding", "On-screen Controls", "UI support"(https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/UISupport.html) 절
- Input System 패키지 샘플: Rebinding UI, On-Screen Controls (Package Manager에서 가져오기)
- Unity 공식 블로그·전자책의 Input System 소개 자료 (Unity Learn의 "Input System" 코스)
