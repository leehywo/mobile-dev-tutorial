# 04. 상태 머신 — 플레이어와 게임 흐름

> **이 장에서 배울 것**
> - bool 플래그 조합이 버그를 만드는 이유를 설명하고 상태 머신(FSM)으로 바꿀 수 있다
> - `enum` + `switch` FSM으로 플레이어 상태(Idle/Move/Hurt/Dead)를 구현한다
> - 상태 객체 패턴(`IGameState`: Enter/Tick/Exit)으로 게임 흐름(Title/Playing/LevelUp/Result)을 구현한다
> - `Time.timeScale = 0`일 때 무엇이 멈추고 무엇이 계속 도는지 설명하고 함정을 피한다
> - 계층형 상태 머신이 필요한 상황을 알아본다
>
> **선수 장**: 01, 03 · **예상 시간**: 3~4시간 · **코인 러시 진행**: 타이틀 화면 → 플레이 → 코인을 모으면 게임이 멈추고 레벨업 선택 → 사망 시 결과 화면 → 다시 시작. 플레이어는 맞으면 깜빡이며 잠깐 무적이 됩니다.

## 왜 필요한가

03장까지의 코인 러시에 요구 사항이 세 개 들어왔다고 합시다.

1. 맞으면 0.8초간 깜빡이며 무적. 그동안 또 맞아도 피해 없음.
2. 죽으면 1초 동안 회색으로 멈춰 있다가 결과 화면.
3. 코인 5개마다 게임을 멈추고 업그레이드를 고르게 하기. 게임 시작 전엔 타이틀 화면.

가장 먼저 떠오르는 구현은 플래그를 늘리는 것입니다.

```csharp
bool isHurt, isDead, isPaused, isTitle, isLevelUp;
float hurtTimer, deathTimer;

void Update()
{
    if (isTitle) return;
    if (isPaused || isLevelUp) return;
    if (isDead) { deathTimer += Time.deltaTime; if (deathTimer > 1f) ShowResult(); return; }
    if (isHurt) { hurtTimer += Time.deltaTime; Blink(); if (hurtTimer > 0.8f) isHurt = false; }
    Move();
}

void OnDamaged()
{
    if (isHurt) return;
    isHurt = true; hurtTimer = 0f;
    if (health.IsDead) isDead = true;     // ← isHurt와 isDead가 동시에 true
}
```

bool 5개는 2⁵ = **32가지 조합**을 만듭니다. 그중 말이 되는 건 몇 개뿐입니다. `isHurt && isDead`일 때 깜빡여야 하나요? `isLevelUp` 중에 `isDead`가 되면? 무적 중에 레벨업하고 돌아오면 `hurtTimer`는 이어서 흘러야 하나요? 조건이 늘 때마다 모든 `if`를 다시 읽어야 하고, "가끔 결과 화면이 두 번 뜬다" 같은 재현하기 어려운 버그가 생깁니다.

React에서 `isLoading`, `isError`, `isSuccess`를 따로 두다가 `status: 'idle' | 'loading' | 'error' | 'success'` 하나로 바꾸면 불가능한 조합이 사라졌던 경험을 떠올리세요. 상태 머신은 그 아이디어를 게임 전체에 적용합니다. **"지금은 정확히 한 상태에 있다"**와 **"상태가 바뀔 때만 할 일이 있다"**를 코드 구조로 보장합니다.

## 개념

### 유한 상태 머신(FSM)의 네 요소

```
          입력 있음                         피해 받음 (체력 > 0)
  ┌──────┐ ─────────▶ ┌──────┐ ──────────────────────────▶ ┌──────┐
  │ Idle │            │ Move │                              │ Hurt │
  └──────┘ ◀───────── └──────┘ ◀──── 0.8초 경과 ──────────── └──────┘
     │      입력 없음      │                                     │
     └──────────┬─────────┴──────────── 체력 0 ─────────────────┘
                ▼
            ┌──────┐
            │ Dead │   (나가는 화살표 없음)
            └──────┘
```

| 요소 | 뜻 | 위 그림에서 |
|---|---|---|
| 상태(State) | 한 번에 하나만 활성 | Idle, Move, Hurt, Dead |
| 전이(Transition) | 한 상태에서 다른 상태로 가는 화살표 | Move → Hurt |
| 조건(Guard) | 전이가 일어나는 조건 | "피해 받음 && 체력 > 0" |
| 진입/퇴장 동작(Enter/Exit) | 상태가 바뀌는 **순간 한 번** 하는 일 | Hurt 진입 시 무적 켜기, 퇴장 시 끄기 |

그림을 먼저 그리면 "Dead에서 나가는 화살표가 없다"처럼 규칙이 눈에 보입니다. 코드를 쓰기 전에 종이에 그리는 습관을 들이세요.

### 방법 1: enum + switch

상태가 몇 개 안 되고 한 컴포넌트 안에서 끝나는 경우 가장 간단합니다.

```csharp
enum PlayerState { Idle, Move, Hurt, Dead }
PlayerState state;

void Update()
{
    switch (state)                          // 매 프레임: 현재 상태의 일 + 전이 조건 검사
    {
        case PlayerState.Idle: if (HasInput) ChangeState(PlayerState.Move); break;
        case PlayerState.Move: if (!HasInput) ChangeState(PlayerState.Idle); break;
        // ...
    }
}

void ChangeState(PlayerState next)
{
    switch (state) { /* 퇴장 동작 */ }
    state = next;
    switch (state) { /* 진입 동작 */ }
}
```

핵심은 **상태 변경이 반드시 `ChangeState` 한 곳을 지난다**는 것입니다. `state = ...`를 여기저기서 직접 대입하면 진입/퇴장 동작이 누락되어 플래그 방식과 같은 버그가 돌아옵니다.

단점은 상태가 늘수록 `switch` 세 개(Update, Enter, Exit)가 함께 길어지고, 한 상태의 코드가 파일 여기저기 흩어진다는 점입니다.

### 방법 2: 상태 객체 패턴

상태마다 클래스를 하나씩 만들고 공통 인터페이스를 구현하게 합니다.

```csharp
public interface IGameState
{
    void Enter();   // 이 상태가 될 때 한 번
    void Tick();    // 이 상태인 동안 매 프레임
    void Exit();    // 이 상태를 떠날 때 한 번
}
```

```
GameStateMachine (MonoBehaviour)
  Current ──▶ PlayingState : IGameState
  Update() { Current.Tick(); }
  ChangeState(next) { Current.Exit(); Current = next; Current.Enter(); }

  TitleState     PlayingState     LevelUpState     ResultState
  (패널 표시)     (코인 세기)       (시간 정지)        (점수 표시)
```

한 상태에 관한 코드(진입·매 프레임·퇴장·그 상태만의 변수)가 한 파일에 모입니다. 상태를 추가해도 기존 상태 파일은 거의 건드리지 않습니다. 상태 클래스는 MonoBehaviour가 아닌 **일반 C# 클래스**라서 `new`로 만들고, 필요한 참조는 생성자로 머신을 받아 얻습니다.

| | enum + switch | 상태 객체 |
|---|---|---|
| 적합한 규모 | 상태 3~5개, 로직 짧음 | 상태가 많거나 상태별 로직·변수가 김 |
| 상태별 변수 | 한 클래스에 섞임 | 상태 클래스 안에 캡슐화 |
| 추가 비용 | switch 세 곳 수정 | 파일 하나 추가 |
| 코인 러시 | 플레이어 (Idle/Move/Hurt/Dead) | 게임 흐름 (Title/Playing/LevelUp/Result) |

둘 중 하나가 정답이 아니라 **규모에 맞게** 고릅니다. 이 장에서는 두 방법을 모두 구현합니다.

### 이벤트 기반 전이와 재진입

전이 조건은 `Tick`에서 매 프레임 검사할 수도 있고(입력이 있나?), 01·03장의 이벤트를 받아서 일으킬 수도 있습니다(체력이 줄었다, 코인을 먹었다). 이벤트 기반 전이는 효율적이지만 한 가지를 알아야 합니다.

```
Coin.OnTriggerEnter2D
  └ CoinCollected.Raise(1)
      └ PlayingState.HandleCoin(1)
          └ machine.ChangeState(LevelUp)
              ├ PlayingState.Exit()   ← 여기서 CoinCollected 구독 해제
              └ LevelUpState.Enter()
      └ (CoinCollected의 다음 구독자 ScoreKeeper.AddScore는 그대로 호출됨)
```

C# 델리게이트는 불변 객체라서, 호출 도중에 구독을 해제해도 **이미 시작된 호출 목록은 끝까지 실행됩니다.** 그래서 이벤트 처리 중에 상태를 바꿔도 델리게이트 차원에서는 안전합니다. 다만 `Exit` 안에서 다시 `ChangeState`를 부르는 식의 연쇄는 흐름을 추적하기 어려우니 피합니다.

그런데 위 그림처럼 **물리 콜백(`OnTriggerEnter2D`) 안에서 바로 전이하면** 게임 규칙 차원의 경합이 생깁니다. `Time.timeScale = 0`은 이미 진행 중인 물리 스텝을 취소하지 않으므로, 같은 스텝에서 처리될 다른 콜백이 전이 **뒤에** 이어서 실행됩니다.

```
같은 물리 스텝 (HP 1, 코인 4개)
  ① 코인 트리거 → HandleCoin → LevelUp 진입 (timeScale 0, 레벨업 창)
  ② 가시 공 트리거 → 플레이어 사망         ← 이미 LevelUp인데 죽음
  ③ 코인 트리거 → HandleCoin              ← Playing.Exit에서 구독 해제됨 → 경험치 누락
```

그래서 이 장의 실습은 **이벤트에서는 값만 누적하고, 전이 판정은 `Tick`(= `Update`)에서** 합니다. 한 프레임의 물리 스텝과 그 콜백은 모두 `Update`보다 먼저 끝나므로, `Tick`에 도착했을 때는 그 스텝의 사망·코인이 전부 반영되어 있습니다. 사망 여부를 먼저 보고, 경험치는 빠짐없이 센 상태에서 전이를 결정할 수 있습니다.

### Time.timeScale — 레벨업 중 게임 멈추기

레벨업 선택 창을 띄울 때 가장 흔한 방법은 `Time.timeScale = 0f`입니다. 하지만 "게임이 멈춘다"의 정확한 의미를 알아야 합니다.

| 항목 | timeScale = 0일 때 |
|---|---|
| `Update`, `LateUpdate` | **계속 호출됨** |
| `Time.deltaTime` | 0 |
| `Time.time` | 증가하지 않음 |
| `Time.unscaledDeltaTime`, `Time.unscaledTime` | 실제 시간대로 흐름 |
| `FixedUpdate` | **호출되지 않음** → 물리 시뮬레이션·`OnTrigger*`·`OnCollision*` 정지 |
| `Rigidbody2D` 움직임 | 정지 (속도 값은 유지, 재개하면 이어서 움직임) |
| 코루틴 `WaitForSeconds` | 멈춤 / `WaitForSecondsRealtime`은 진행 |
| Animator (Update Mode: Normal) | 멈춤 / Unscaled Time으로 바꾸면 진행 |
| 입력(Input System), UGUI 버튼 클릭 | 동작함 |

여기서 세 가지 함정이 나옵니다.

**함정 1 — deltaTime을 곱하지 않는 코드는 멈추지 않는다.**

```csharp
void Update()
{
    if (dashAction.WasPressedThisFrame())
        transform.position += (Vector3)dir * 3f;   // ❌ 레벨업 창 뒤에서 플레이어가 대시함
}
```

`Update`는 계속 돌기 때문에 입력으로 즉시 일어나는 동작, `deltaTime` 없이 움직이는 코드, `Time.frameCount`로 세는 타이머는 멈추지 않습니다. 이런 코드는 "게임플레이 중인가"를 직접 확인하거나, 상태 머신이 해당 컴포넌트를 꺼야 합니다. 이 장의 `GameStateMachine`은 이동 입력(`PlayerMover.CanMove`)을 상태에 따라 제어합니다.

**함정 2 — 멈춘 동안 움직여야 하는 것은 unscaled 시간을 써야 한다.**

레벨업 창의 글자가 두근거리는 애니메이션을 `Time.deltaTime`으로 만들면 창이 뜬 순간 같이 얼어붙습니다. UI 연출, 일시정지 메뉴의 트윈, 타이틀 배경 애니메이션은 `Time.unscaledDeltaTime`/`Time.unscaledTime`을 씁니다.

**함정 3 — 되돌리는 걸 잊으면 다음 판이 얼어 있다.**

`timeScale`은 **정적 전역 값**이라 씬을 다시 로드해도 0으로 남습니다. 레벨업 중에 "처음부터" 버튼을 눌러 씬을 다시 불렀더니 타이틀부터 아무것도 안 움직이는 버그가 전형적입니다. 그래서 `LevelUpState.Exit`에서 반드시 1로 되돌리고, 방어적으로 `GameStateMachine.Awake`와 씬 재시작 직전에도 1로 설정합니다.

참고로 `Time.timeScale`을 0.3처럼 슬로모션으로 쓸 때는 `Time.fixedDeltaTime`이 자동으로 줄지 않으므로 물리가 뚝뚝 끊겨 보일 수 있습니다. 슬로모션과 히트스톱은 16장에서 다룹니다.

### 계층형 상태 머신(HFSM) — 맛보기

이 장의 구현을 끝내면 이런 불편함을 발견하게 됩니다.

```
Playing ──코인 5개──▶ LevelUp ──선택──▶ Playing
   Exit() 호출됨                          Enter() 다시 호출됨
   (구독 해제, 게임플레이 끄기?)              (구독 다시, 게임플레이 켜기, 타이머 초기화??)
```

LevelUp은 사실 "플레이 도중의 잠깐"인데 평평한(flat) FSM에서는 Playing을 **완전히 떠났다가 새로 들어오는** 것으로 취급됩니다. 그래서 `PlayingState.Enter`에 "레벨·경과 시간은 초기화하지 않기" 같은 예외가 생깁니다. 일시정지(Paused), 부활 광고 대기(Revive)가 추가되면 같은 예외가 늘어납니다.

계층형 상태 머신은 상태 안에 하위 상태 머신을 둡니다.

```
Root
 ├─ Title
 ├─ InRun  ◀── 공통: 판 데이터(레벨·시간) 보유, "플레이어 사망 → Result" 전이
 │   ├─ Playing   (기본 하위 상태)
 │   ├─ LevelUp   (timeScale 0)
 │   └─ Paused    (timeScale 0)
 └─ Result
```

- 하위 상태가 처리하지 않은 이벤트는 부모가 처리합니다. "사망 → Result"를 Playing·LevelUp·Paused마다 쓸 필요가 없습니다.
- Playing ↔ LevelUp 전이는 InRun 안에서 일어나므로 InRun의 Enter/Exit는 호출되지 않습니다. 판 데이터가 자연스럽게 유지됩니다.

구현은 `IGameState`를 구현하는 `InRunState`가 내부에 자기만의 `Current`와 `ChangeSubState`를 갖는 형태로 시작할 수 있습니다. 코인 러시 규모에서는 이 장의 평평한 FSM으로 충분하고, 상태가 7~8개를 넘거나 공통 전이가 반복되기 시작하면 도입을 검토하세요(연습 문제 5). 캐릭터 애니메이션용 Animator Controller의 Sub-State Machine도 같은 개념입니다(17장).

## 실습: 코인 러시에 적용하기

### 1단계: 플레이어 상태 — enum FSM

```csharp
// Assets/_CoinRush/Scripts/Player/PlayerStateController.cs
using UnityEngine;

public enum PlayerState { Idle, Move, Hurt, Dead }

[RequireComponent(typeof(PlayerMover), typeof(Health))]
public class PlayerStateController : MonoBehaviour
{
    [SerializeField] private SpriteRenderer sprite;
    [SerializeField] private VoidEventChannel gameOver;
    [SerializeField] private Behaviour[] disableOnDeath;     // 무기, 자석 등

    [Header("Hurt")]
    [SerializeField] private float hurtDuration = 0.8f;
    [SerializeField] private float blinkInterval = 0.08f;

    [Header("Dead")]
    [SerializeField] private float deathDelay = 1f;
    [SerializeField] private Color deadColor = new Color(0.4f, 0.4f, 0.4f, 1f);

    private PlayerMover mover;
    private Health health;
    private float stateTimer;
    private int lastHp;
    private bool gameOverRaised;

    public PlayerState State { get; private set; } = PlayerState.Idle;

    void Awake()
    {
        mover = GetComponent<PlayerMover>();
        health = GetComponent<Health>();
    }

    void OnEnable()
    {
        health.Changed += HandleHealthChanged;
        health.Died += HandleDied;
    }

    void OnDisable()
    {
        health.Changed -= HandleHealthChanged;
        health.Died -= HandleDied;
    }

    void Start() => lastHp = health.Current;

    void Update()
    {
        stateTimer += Time.deltaTime;   // 레벨업 중(timeScale 0)에는 무적 시간도 함께 멈춘다

        switch (State)
        {
            case PlayerState.Idle:
                if (HasMoveInput()) ChangeState(PlayerState.Move);
                break;

            case PlayerState.Move:
                if (!HasMoveInput()) ChangeState(PlayerState.Idle);
                break;

            case PlayerState.Hurt:
                sprite.enabled = Mathf.FloorToInt(stateTimer / blinkInterval) % 2 == 0;
                if (stateTimer >= hurtDuration) ChangeState(PlayerState.Idle);
                break;

            case PlayerState.Dead:
                if (!gameOverRaised && stateTimer >= deathDelay)
                {
                    gameOverRaised = true;
                    gameOver.Raise();
                }
                break;
        }
    }

    private bool HasMoveInput() => mover.MoveInput.sqrMagnitude > 0.01f;

    private void ChangeState(PlayerState next)
    {
        if (State == PlayerState.Dead || State == next) return;   // Dead에서 나가는 전이는 없다

        // 퇴장 동작
        switch (State)
        {
            case PlayerState.Hurt:
                health.Invulnerable = false;
                sprite.enabled = true;
                break;
        }

        State = next;
        stateTimer = 0f;

        // 진입 동작
        switch (State)
        {
            case PlayerState.Hurt:
                health.Invulnerable = true;
                break;

            case PlayerState.Dead:
                mover.CanMove = false;
                sprite.color = deadColor;
                for (int i = 0; i < disableOnDeath.Length; i++) disableOnDeath[i].enabled = false;
                break;
        }
    }

    private void HandleHealthChanged(int current, int max)
    {
        bool damaged = current < lastHp;
        lastHp = current;
        if (damaged && current > 0) ChangeState(PlayerState.Hurt);
    }

    private void HandleDied() => ChangeState(PlayerState.Dead);
}
```

읽을 포인트:

- `Hurt → Hurt`는 `State == next` 검사로 무시됩니다. 무적 중엔 어차피 `Health`가 피해를 받지 않으므로 `Changed`도 오지 않습니다.
- `Health.TakeDamage`는 체력이 0이 될 때 `Changed(0, max)` 다음에 `Died`를 발행합니다. `current > 0` 조건 덕분에 Hurt를 거치지 않고 바로 Dead로 갑니다.
- 03장에서는 `HealthEventRelay`가 사망 즉시 `GameOver`를 발행했지만, 이제는 Dead 상태가 1초 뒤에 발행합니다. **연출 타이밍이 상태 안에 모였습니다.**

에디터 작업:

1. Player에서 03장의 `HealthEventRelay`와 `VoidEventListener`(사망 시 숨기기)를 **제거**합니다. 둘 다 이제 Dead 상태가 대신합니다.
2. `PlayerStateController`를 추가하고 Sprite = Player의 SpriteRenderer, Game Over = `GameOver` 채널, Disable On Death = `AutoShooter`, `CoinMagnet`을 연결합니다.

### 2단계: 게임 상태 인터페이스와 머신

```csharp
// Assets/_CoinRush/Scripts/Core/GameStates/IGameState.cs
public interface IGameState
{
    void Enter();
    void Tick();
    void Exit();
}
```

```csharp
// Assets/_CoinRush/Scripts/Core/GameStateMachine.cs
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

public class GameStateMachine : MonoBehaviour
{
    [Header("플레이어")]
    [SerializeField] private PlayerMover playerMover;
    [SerializeField] private Health playerHealth;

    [Header("플레이 중에만 켜는 컴포넌트 (스포너 등)")]
    [SerializeField] private Behaviour[] gameplayBehaviours;

    [Header("채널·점수")]
    [SerializeField] private IntEventChannel coinCollected;
    [SerializeField] private VoidEventChannel gameOver;
    [SerializeField] private ScoreKeeper scoreKeeper;

    [Header("UI")]
    [SerializeField] private GameObject titlePanel;
    [SerializeField] private GameObject levelUpPanel;
    [SerializeField] private GameObject resultPanel;
    [SerializeField] private TextMeshProUGUI levelUpLabel;
    [SerializeField] private TextMeshProUGUI resultLabel;

    [Header("규칙")]
    [SerializeField, Min(1)] private int coinsPerLevel = 5;

    [Header("디버그 (읽기 전용)")]
    [SerializeField] private string currentStateName;

    public TitleState Title { get; private set; }
    public PlayingState Playing { get; private set; }
    public LevelUpState LevelUp { get; private set; }
    public ResultState Result { get; private set; }
    public IGameState Current { get; private set; }

    // 상태 클래스들이 쓰는 참조
    public Health PlayerHealth => playerHealth;
    public IntEventChannel CoinCollected => coinCollected;
    public VoidEventChannel GameOver => gameOver;
    public ScoreKeeper ScoreKeeper => scoreKeeper;
    public GameObject TitlePanel => titlePanel;
    public GameObject LevelUpPanel => levelUpPanel;
    public GameObject ResultPanel => resultPanel;
    public TextMeshProUGUI LevelUpLabel => levelUpLabel;
    public TextMeshProUGUI ResultLabel => resultLabel;
    public int CoinsPerLevel => coinsPerLevel;

    void Awake()
    {
        Time.timeScale = 1f;   // 이전 씬에서 0으로 남았을 경우 대비 (함정 3)

        Title = new TitleState(this);
        Playing = new PlayingState(this);
        LevelUp = new LevelUpState(this);
        Result = new ResultState(this);

        titlePanel.SetActive(false);
        levelUpPanel.SetActive(false);
        resultPanel.SetActive(false);
    }

    void Start() => ChangeState(Title);

    void Update() => Current?.Tick();   // 상태 객체는 일반 C# 객체라 ?. 사용 가능

    void OnDestroy()
    {
        // 씬 언로드 중에는 패널 등 다른 오브젝트가 먼저 파괴됐을 수 있어 Exit 전체를 부르지 않는다.
        // 에셋(채널) 구독 해제와 전역 값 복구만 확실히 한다.
        if (Current == Playing) Playing.Exit();
        Time.timeScale = 1f;
        Current = null;
    }

    public void ChangeState(IGameState next)
    {
        if (next == null || next == Current) return;

        Current?.Exit();
        Current = next;
        currentStateName = next.GetType().Name;
        Current.Enter();
    }

    public void SetGameplayActive(bool active)
    {
        for (int i = 0; i < gameplayBehaviours.Length; i++)
            gameplayBehaviours[i].enabled = active;
        playerMover.CanMove = active;
    }

    // ── UI 버튼에서 호출 ──────────────────────────────
    public void StartGame()
    {
        if (Current == Title) ChangeState(Playing);
    }

    public void ChooseUpgrade(int index)
    {
        if (Current != LevelUp) return;   // 버튼 연타·잘못된 상태에서의 호출 방지
        if (playerHealth.IsDead) return;  // 방어: 죽은 플레이어에게는 업그레이드를 적용하지 않음
        LevelUp.Apply(index);
        ChangeState(Playing);
    }

    public void Restart()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }
}
```

버튼 메서드마다 "지금 그 상태인가"를 확인하는 이유가 중요합니다. UI 버튼은 상태 머신 밖에서 들어오는 입력이라, 결과 화면으로 넘어가는 순간 레벨업 버튼이 한 번 더 눌리는 식의 경합이 실제로 일어납니다.

### 3단계: 네 가지 상태

```csharp
// Assets/_CoinRush/Scripts/Core/GameStates/TitleState.cs
public class TitleState : IGameState
{
    private readonly GameStateMachine machine;

    public TitleState(GameStateMachine machine) => this.machine = machine;

    public void Enter()
    {
        machine.SetGameplayActive(false);
        machine.TitlePanel.SetActive(true);
    }

    public void Tick() { }

    public void Exit() => machine.TitlePanel.SetActive(false);
}
```

```csharp
// Assets/_CoinRush/Scripts/Core/GameStates/PlayingState.cs
using UnityEngine;

public class PlayingState : IGameState
{
    private readonly GameStateMachine machine;
    private int coinsInLevel;

    public int Level { get; private set; } = 1;
    public float ElapsedTime { get; private set; }
    public int CoinsToNextLevel => machine.CoinsPerLevel * Level;

    public PlayingState(GameStateMachine machine) => this.machine = machine;

    public void Enter()
    {
        // LevelUp에서 돌아올 때도 호출된다 → 판 데이터(Level, ElapsedTime)는 여기서 초기화하지 않는다
        machine.SetGameplayActive(true);
        machine.CoinCollected.OnRaised += HandleCoin;
        machine.GameOver.OnRaised += HandleGameOver;
    }

    public void Tick()
    {
        ElapsedTime += Time.deltaTime;

        // 레벨업 전이는 물리 콜백이 아니라 여기서 판정한다.
        // 이 프레임의 물리 스텝(코인·피해)이 모두 끝난 뒤라 사망과 경합하지 않는다.
        if (machine.PlayerHealth.IsDead) return;   // 사망 연출 중 레벨업 방지

        int need = CoinsToNextLevel;
        if (coinsInLevel < need) return;

        coinsInLevel -= need;   // 남은 코인은 다음 레벨로 이월
        Level++;
        machine.ChangeState(machine.LevelUp);
        // 남은 코인이 다음 요구량 이상이면, 레벨업에서 돌아온 뒤 첫 Tick에서 다시 레벨업한다
    }

    public void Exit()
    {
        machine.CoinCollected.OnRaised -= HandleCoin;
        machine.GameOver.OnRaised -= HandleGameOver;
    }

    // 코인 이벤트에서는 누적만 한다 (전이는 Tick)
    private void HandleCoin(int amount) => coinsInLevel += amount;

    private void HandleGameOver() => machine.ChangeState(machine.Result);
}
```

```csharp
// Assets/_CoinRush/Scripts/Core/GameStates/LevelUpState.cs
using UnityEngine;

public class LevelUpState : IGameState
{
    private readonly GameStateMachine machine;

    public LevelUpState(GameStateMachine machine) => this.machine = machine;

    public void Enter()
    {
        Time.timeScale = 0f;
        // Update는 계속 돌기 때문에(함정 1) 무기·스포너·이동 입력도 끈다.
        // 끄지 않으면 방향키로 바라보는 방향이 바뀌어 창 뒤에서 발사할 수 있다.
        machine.SetGameplayActive(false);
        machine.LevelUpPanel.SetActive(true);
        machine.LevelUpLabel.SetText("레벨 {0}!", machine.Playing.Level);
    }

    public void Tick()
    {
        // timeScale이 0이어도 Update(→ Tick)는 돈다. 연출은 unscaled 시간으로
        float pulse = 1f + 0.06f * Mathf.Sin(Time.unscaledTime * 6f);
        machine.LevelUpLabel.transform.localScale = new Vector3(pulse, pulse, 1f);
    }

    public void Exit()
    {
        machine.LevelUpPanel.SetActive(false);
        machine.LevelUpLabel.transform.localScale = Vector3.one;
        Time.timeScale = 1f;   // 반드시 복구 (함정 3)
    }

    // 11장에서 업그레이드 데이터·카드 UI로 교체
    public void Apply(int index)
    {
        Health hp = machine.PlayerHealth;
        switch (index)
        {
            case 0: hp.Heal(hp.Max); break;              // 체력 모두 회복
            case 1: hp.Initialize(hp.Max + 1); break;    // 최대 체력 +1 (가득 채움)
        }
    }
}
```

```csharp
// Assets/_CoinRush/Scripts/Core/GameStates/ResultState.cs
using UnityEngine;

public class ResultState : IGameState
{
    private readonly GameStateMachine machine;

    public ResultState(GameStateMachine machine) => this.machine = machine;

    public void Enter()
    {
        machine.SetGameplayActive(false);
        machine.ResultPanel.SetActive(true);

        ScoreKeeper score = machine.ScoreKeeper;
        int best = Mathf.Max(score.Score, score.HighScore);   // 03장 흔한 실수 3과 같은 이유
        machine.ResultLabel.SetText("점수 {0}\n최고 기록 {1}\n생존 {2:1}초",
            score.Score, best, machine.Playing.ElapsedTime);
    }

    public void Tick() { }

    public void Exit() => machine.ResultPanel.SetActive(false);
}
```

`{2:1}`은 TextMeshPro `SetText`의 서식으로 "소수점 한 자리"입니다(02장).

### 4단계: UI와 씬 조립

1. Canvas 아래에 패널 세 개를 만듭니다(각각 UI → Panel, 반투명 검정).
   - `TitlePanel`: 제목 텍스트 "COIN RUSH" + 버튼 "시작"
   - `LevelUpPanel`: 텍스트 `LevelUpLabel` + 버튼 "체력 회복", "최대 체력 +1"
   - `ResultPanel`: 텍스트 `ResultLabel` + 버튼 "다시 하기"
2. 03장의 `GameOverPanel`과 Canvas의 `GameOverView` 컴포넌트를 삭제합니다(`ResultState`가 대신합니다). `GameOverView.cs`도 삭제합니다.
3. `GameSystems` 오브젝트에 `GameStateMachine`을 추가하고 필드를 연결합니다.
   - Gameplay Behaviours: `FallingSpawner`, Player의 `AutoShooter`, `CoinMagnet`
   - 채널: `CoinCollected`, `GameOver` / Score Keeper: `GameSystems`의 `ScoreKeeper`
4. 버튼의 **On Click ()**에 `GameSystems`를 드래그하고 함수를 고릅니다.
   - 시작 → `GameStateMachine.StartGame`
   - 체력 회복 → `GameStateMachine.ChooseUpgrade`, 인자 `0`
   - 최대 체력 +1 → `GameStateMachine.ChooseUpgrade`, 인자 `1`
   - 다시 하기 → `GameStateMachine.Restart`
5. **EventSystem 확인**: Hierarchy의 `EventSystem`을 선택합니다. 컴포넌트가 `Standalone Input Module`(구 입력용)이면, Active Input Handling이 "Input System Package (New)"일 때 버튼 클릭이 동작하지 않고 Console에 `InvalidOperationException`이 찍힙니다. Inspector에 표시되는 **Replace with InputSystemUIInputModule** 버튼을 누르거나, `Standalone Input Module`을 제거하고 **Add Component → Input System UI Input Module**을 추가합니다. 추가된 모듈의 **Actions Asset**과 **Point**·**Left Click** 같은 UI 액션 칸이 비어 있지 않은지 확인합니다(기본 UI 액션이 자동으로 채워집니다. 항목 이름은 Input System 버전에 따라 조금 다를 수 있습니다). 새로 만든 프로젝트에서 이미 `Input System UI Input Module`이 붙어 있다면 이 단계는 건너뜁니다.
6. `Restart`는 빌드 인덱스로 씬을 로드하므로 **File → Build Profiles**의 Scene List에 현재 씬이 들어 있어야 합니다.
7. `FallingSpawner`는 03장에서 `GameOver` 채널을 받으면 스스로 꺼지게 만들었습니다. 이제 머신이 켜고 끄므로 그대로 둬도 되지만, 역할이 겹친다는 점을 기억해 두세요(흔한 실수 4).

### 확인하기

- ▶ Play → 타이틀 패널만 보이고 가시 공·코인이 떨어지지 않으며, 방향키를 눌러도 플레이어가 움직이지 않는다.
- "시작" → 스폰이 시작되고 조작·자동 발사가 된다. `GameSystems`의 Inspector에서 Current State Name이 `PlayingState`로 바뀐다.
- 가시 공에 맞으면 플레이어가 0.8초간 깜빡이고, 그동안 다른 공에 닿아도 HP가 줄지 않는다.
- 코인 5개를 먹으면 **떨어지던 물체가 공중에 멈추고** 레벨업 패널이 뜬다. 글자는 계속 두근거린다(unscaled 시간). 방향키를 눌러도 플레이어가 움직이지 않고, 자동 발사도 멈춘다.
- 버튼에 마우스를 올리면 색이 바뀌고 클릭이 된다(EventSystem 입력 모듈 확인).
- 레벨업 도중 깜빡이던 플레이어는 깜빡임 상태 그대로 멈춰 있다가, 선택 후 남은 무적 시간을 이어서 소모한다.
- 선택하면 물체가 이어서 떨어진다. 다음 레벨업은 코인 10개 뒤다.
- HP가 0이 되면 플레이어가 회색으로 1초간 멈춘 뒤 결과 패널에 점수·최고 기록·생존 시간이 표시된다.
- "다시 하기" → 타이틀부터 정상 동작한다(timeScale 복구 확인).

## 흔한 실수

1. **다시 하기 후 타이틀에서 아무것도 안 움직이거나, 게임이 시작돼도 멈춰 있다**
   원인: 레벨업 중(timeScale 0) 씬을 다시 로드했는데 복구하지 않았습니다. `timeScale`은 씬과 무관한 전역 값입니다.
   해결: `LevelUpState.Exit`, `GameStateMachine.Awake`, `Restart`에서 1로 설정합니다. 머신의 `OnDestroy`에서 한 번 더 복구하는 것도 같은 이유입니다.
2. **레벨업 창이 떠 있는데 뒤에서 뭔가 계속 움직인다**
   원인: `deltaTime`을 곱하지 않았거나 입력 즉시 실행되는 코드, 혹은 `unscaledDeltaTime`을 게임플레이에 쓴 코드입니다.
   해결: 게임플레이 코드는 `Time.deltaTime`을 쓰고, 입력 동작은 상태 머신이 끄거나(`CanMove`) 현재 상태를 확인합니다.
3. **상태 Enter/Exit가 안 불려서 구독이 두 번 되거나 패널이 안 닫힌다**
   원인: `ChangeState`를 거치지 않고 `Current = ...` 또는 `State = ...`를 직접 대입했습니다.
   해결: 상태 필드의 setter를 `private`으로 두고 변경은 `ChangeState` 한 곳에서만 합니다.
4. **죽었는데 레벨업에서 돌아오니 플레이어가 다시 움직인다**
   원인: 두 상태 머신(`PlayerStateController`의 Dead, `GameStateMachine`의 Playing)이 같은 `CanMove`를 서로 다른 규칙으로 켜고 끕니다.
   해결: 하나의 값은 한 주인만 쓰게 하거나, 이 장처럼 사망 중엔 전이 자체가 일어나지 않게 가드를 둡니다(`PlayingState.Tick`의 `IsDead` 검사). 전이 판정을 물리 콜백이 아니라 `Tick`에서 하는 것도 같은 스텝의 코인·사망 경합을 없애기 위해서입니다(개념의 "이벤트 기반 전이와 재진입"). 07·08장에서 이동을 개선할 때 "이동 가능 여부"를 여러 이유의 조합(사망, 메뉴, 컷신)으로 관리하는 방법을 고민해 보세요.
5. **레벨업 버튼을 빠르게 두 번 누르면 업그레이드가 두 번 적용된다**
   원인: 버튼 핸들러가 현재 상태를 확인하지 않았습니다.
   해결: `ChooseUpgrade`처럼 `if (Current != LevelUp) return;`으로 막습니다. 첫 클릭에서 상태가 Playing으로 바뀌므로 두 번째 클릭은 무시됩니다.

## 연습 문제

**1. ★☆☆ 일시정지 상태 추가**
Esc 키(또는 게임패드 Start)로 게임을 멈추고 다시 누르면 재개하는 `PausedState`를 추가하세요. Playing에서만 들어갈 수 있어야 합니다.

<details><summary>힌트·해설</summary>

`LevelUpState`와 거의 같습니다. Enter에서 `Time.timeScale = 0f`와 패널 표시, Exit에서 복구. 입력 확인은 매 프레임 필요하므로 `Tick`에서 합니다.

```csharp
// PlayingState.Tick 안
if (pauseAction.WasPressedThisFrame()) machine.ChangeState(machine.Paused);
// PausedState.Tick 안
if (pauseAction.WasPressedThisFrame()) machine.ChangeState(machine.Playing);
```

`pauseAction`은 머신의 `Awake`에서 `InputSystem.actions.FindAction("UI/Cancel")`처럼 찾아 둡니다(기본 액션 에셋의 `UI` 맵 이름은 08장에서 확인). 같은 프레임에 Playing → Paused → Playing이 연달아 일어나지 않는지도 생각해 보세요. `Tick`은 한 프레임에 현재 상태 하나만 호출되므로 안전합니다.
</details>

**2. ★☆☆ 플레이어 상태를 화면에 표시**
디버그용으로 플레이어 머리 위에 현재 `PlayerState`를 표시하세요. 매 프레임 문자열 할당이 없어야 합니다.

<details><summary>힌트·해설</summary>

상태가 **바뀔 때만** 텍스트를 갱신하면 됩니다. `PlayerStateController`에 `public event System.Action<PlayerState> StateChanged;`를 추가하고 `ChangeState` 끝에서 발행합니다. 표시 컴포넌트는 `label.text = state.ToString();`을 이벤트에서 호출합니다. `enum.ToString()`은 할당이 있지만 상태 변경 시에만 일어나므로 괜찮습니다. 완전히 없애려면 `string[]` 이름 표를 미리 만들어 인덱스로 씁니다.
</details>

**3. ★★☆ 레벨업 카운트다운**
레벨업에서 선택한 뒤 바로 재개하지 말고 "3, 2, 1"을 1초씩 보여준 뒤 재개하는 `CountdownState`를 만드세요. 카운트다운 동안에도 게임은 멈춰 있어야 합니다.

<details><summary>힌트·해설</summary>

`ChooseUpgrade`가 `ChangeState(Countdown)`으로 가게 하고, `CountdownState`는 Enter에서 `remaining = 3f`, Tick에서 `remaining -= Time.unscaledDeltaTime`으로 줄입니다. `Time.deltaTime`을 쓰면 timeScale이 0이라 영원히 끝나지 않습니다 — 이 문제의 핵심 함정입니다. 표시 숫자는 `Mathf.CeilToInt(remaining)`가 바뀔 때만 `SetText`합니다. timeScale 복구는 `LevelUpState.Exit`가 아니라 `CountdownState.Exit`로 옮겨야 한다는 점도 확인하세요. 이것이 "Exit에서 무엇을 되돌릴지"를 상태마다 정확히 정해야 하는 이유입니다.
</details>

**4. ★★☆ 전이 기록**
`GameStateMachine`에 최근 10개 전이를 기록해 Inspector에서 볼 수 있게 하세요. (예: `Title → Playing (t=0.0)`) 버그 리포트에 첨부하면 유용합니다.

<details><summary>힌트·해설</summary>

`[SerializeField] private List<string> history = new List<string>();`를 두고 `ChangeState`에서 `history.Add($"{Current?.GetType().Name} → {next.GetType().Name} (t={Time.unscaledTime:0.0})")`, 개수가 10을 넘으면 `RemoveAt(0)`. 전이는 드물게 일어나므로 문자열 할당은 문제가 되지 않습니다. 24장 애널리틱스에서 이 기록을 "이탈 직전 상태" 분석에 씁니다.
</details>

**5. ★★★ 계층형으로 리팩터링 (스스로 확장)**
Playing·LevelUp·Paused(연습 1)를 `InRunState`의 하위 상태로 옮기세요. 조건: `GameOver` 채널 구독은 `InRunState`가 한 번만 하고, 하위 상태 사이를 오갈 때는 `InRunState.Enter/Exit`가 호출되지 않아야 합니다. 판 데이터(`Level`, `ElapsedTime`)는 `InRunState`가 소유합니다.

<details><summary>힌트·해설</summary>

- `InRunState : IGameState`가 내부에 `IGameState currentSub`와 `ChangeSub(IGameState)`를 갖습니다. `Tick()`은 `currentSub.Tick()`을 호출합니다.
- `InRunState.Enter`: `GameOver` 구독, 판 데이터 초기화, `ChangeSub(Playing)`. `Exit`: `currentSub.Exit()`, 구독 해제.
- 외부 버튼(`ChooseUpgrade`)은 `machine.Current == InRun && InRun.CurrentSub == LevelUp`으로 확인합니다.
- 이렇게 바꾸면 `PlayingState.Enter`의 "판 데이터를 초기화하지 않는다"는 예외 주석이 사라집니다. 사라진 예외의 수가 곧 리팩터링의 가치입니다.
- 더 나아가 부활 광고(25장)를 `InRun` 안의 `ReviveOffer` 하위 상태로 넣으면 어디에 둘지 고민할 필요가 없어집니다.
</details>

## 셀프 체크

**1. bool 플래그 여러 개로 상태를 관리할 때 생기는 근본 문제를 설명해 보세요.**

<details><summary>모범 답안</summary>

플래그 n개는 2ⁿ개의 조합을 만드는데 대부분은 말이 안 되는 조합입니다(`isHurt && isDead`). 코드가 불가능한 조합을 막지 못하므로 조건이 늘수록 모든 분기를 다시 검토해야 하고, 드물게 발생하는 조합이 재현 어려운 버그가 됩니다. 상태 머신은 "한 번에 한 상태"를 구조로 보장해 이 조합을 없앱니다.
</details>

**2. 상태 변경을 반드시 `ChangeState` 한 곳에서 해야 하는 이유는?**

<details><summary>모범 답안</summary>

진입·퇴장 동작(구독·해제, 무적 켜고 끄기, timeScale 설정·복구)이 `ChangeState` 안에서 실행되기 때문입니다. 상태 변수를 직접 대입하면 이 동작이 누락되어 구독 중복, 무적 해제 누락, 게임 정지 상태 고착 같은 버그가 생깁니다.
</details>

**3. `Time.timeScale = 0`일 때 `Update`와 `FixedUpdate`는 각각 어떻게 되나요? 그 결과 어떤 함정이 생기나요?**

<details><summary>모범 답안</summary>

`Update`는 계속 호출되지만 `Time.deltaTime`이 0이고, `FixedUpdate`는 호출되지 않아 물리와 트리거가 멈춥니다. 따라서 deltaTime을 곱하지 않는 코드나 입력 즉시 실행되는 동작은 멈추지 않고, 반대로 멈춘 동안 움직여야 하는 UI 연출은 `unscaledDeltaTime`을 써야 합니다. 또 timeScale은 전역 값이라 복구를 잊으면 씬을 다시 로드해도 멈춘 상태로 남습니다.
</details>

**4. 플레이어 상태는 enum으로, 게임 흐름은 상태 객체로 구현한 이유를 설명해 보세요.**

<details><summary>모범 답안</summary>

플레이어 상태는 4개이고 각 상태의 로직이 짧으며 한 컴포넌트 안에서 끝나므로 switch가 가장 단순합니다. 게임 흐름은 상태마다 UI 패널, 채널 구독, 판 데이터, timeScale 처리 등 고유한 로직과 변수가 있고 앞으로 Paused·Countdown 같은 상태가 늘어날 예정이라, 상태별로 파일을 나눠 캡슐화하는 상태 객체 패턴이 유지보수에 유리합니다.
</details>

**5. 평평한 FSM에서 Playing ↔ LevelUp을 오갈 때 생기는 불편함과, 계층형 상태 머신이 이를 해결하는 방식은?**

<details><summary>모범 답안</summary>

LevelUp으로 갈 때 Playing의 Exit가, 돌아올 때 Enter가 다시 호출되어 "판 데이터를 초기화하지 않기", "구독을 다시 하기" 같은 예외 처리가 Enter/Exit에 섞입니다. 계층형에서는 Playing과 LevelUp을 `InRun`의 하위 상태로 두어, 하위 상태 사이의 전이에서는 `InRun`의 Enter/Exit가 호출되지 않고, 사망 → Result 같은 공통 전이도 부모가 한 번만 처리합니다.
</details>

## 핵심 요약

- bool 플래그 조합은 불가능한 상태를 만들고, 상태 머신은 "정확히 한 상태"를 구조로 보장합니다.
- FSM은 상태·전이·조건·진입/퇴장 동작으로 이루어지며, 코드 전에 그림부터 그립니다.
- 모든 상태 변경은 `ChangeState` 한 곳을 지나야 진입·퇴장 동작이 누락되지 않습니다.
- 작은 FSM은 `enum` + `switch`, 상태별 로직이 크면 `IGameState`(Enter/Tick/Exit) 상태 객체로 구현합니다.
- 이벤트 처리 중에 상태를 바꿔도 C# 델리게이트 호출은 안전하지만, Exit 안에서 연쇄 전이는 피합니다.
- `timeScale = 0`: `Update`는 돌고 `deltaTime`은 0, `FixedUpdate`·물리는 정지. UI 연출은 unscaled 시간, 복구는 반드시.
- 하위 상태 사이 전이와 공통 전이가 반복되면 계층형 상태 머신을 고려합니다.
- 코인 러시는 이제 Title → Playing ⇄ LevelUp → Result 흐름과 Idle/Move/Hurt/Dead 플레이어 상태를 갖습니다.

## 더 읽을거리

- Robert Nystrom, 『Game Programming Patterns』 "State" 장 — https://gameprogrammingpatterns.com/state.html (한국어판 『게임 프로그래밍 패턴』)
- Unity Scripting API, `Time.timeScale` — https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- Unity Manual, "Order of execution for event functions" — https://docs.unity3d.com/Manual/execution-order.html
- Unity 전자책, "Level up your code with design patterns and SOLID" — State 패턴 장
