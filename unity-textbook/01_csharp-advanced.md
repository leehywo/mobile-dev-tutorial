# 01. C# 심화 — 델리게이트·이벤트·제네릭·인터페이스

> **이 장에서 배울 것**
> - delegate·`Action`·`Func`·`event`의 차이를 설명하고, 이벤트로 컴포넌트 사이의 직접 호출을 없앤다
> - `OnEnable`/`OnDisable`에서 구독·해제하는 규칙을 지키고, 해제를 빼먹었을 때 생기는 버그를 설명할 수 있다
> - 제네릭 메서드·클래스와 `where` 제약을 읽고 직접 작성한다
> - 인터페이스와 추상 클래스 중 무엇을 쓸지 판단할 수 있다
> - 확장 메서드·패턴 매칭·프로퍼티·record를 Unity 제약 안에서 활용한다
>
> **선수 장**: 기초 트랙 · **예상 시간**: 3~4시간 · **코인 러시 진행**: 싱글턴 직접 호출이 사라지고, 점수·체력·게임오버가 이벤트로 연결됩니다. 플레이어에게 체력(`Health`)이 생기고 떨어지는 가시 공에 맞으면 다칩니다.

## 왜 필요한가

기초 트랙 STEP 4에서 만든 코인 먹기 게임의 핵심 코드를 다시 보겠습니다. 이 교과서는 이 코드에서 출발합니다.

```csharp
// STEP 4 — Coin.cs (발췌)
void OnTriggerEnter2D(Collider2D other)
{
    if (other.CompareTag("Player"))
    {
        GameManager.Instance.AddScore(1);                // (1)
        Destroy(gameObject);
    }
}

// STEP 4 — GameManager.cs (발췌)
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    public int Score { get; private set; }
    void Awake() => Instance = this;                     // (2)

    public void AddScore(int amount)
    {
        Score += amount;
        if (Score > PlayerPrefs.GetInt("highScore", 0))
        {
            PlayerPrefs.SetInt("highScore", Score);
            PlayerPrefs.Save();                          // (3)
        }
    }
}

// STEP 4 — ScoreDisplay.cs (발췌)
void Update()
{
    label.text = $"점수: {GameManager.Instance.Score}"; // (4)
}
```

작은 게임에서는 잘 돌아갑니다. 하지만 이 코드 위에 서바이버라이크를 30장 동안 쌓으면 다음 문제가 차례로 터집니다.

| 번호 | 문제 | 실제로 겪게 되는 일 |
|---|---|---|
| (1) | `Coin`이 `GameManager`를 **직접** 안다 | 코인만 테스트하려고 빈 씬에 놓으면 `NullReferenceException`. 코인을 먹을 때 소리·파티클·업적을 추가하려면 매번 `Coin`이나 `GameManager`를 고쳐야 합니다 |
| (2) | `Instance = this`가 무조건 덮어쓴다 | 씬을 다시 로드하거나 실수로 `GameManager`가 두 개 생기면 어느 쪽이 진짜인지 알 수 없습니다 |
| (3) | 코인 하나마다 디스크에 저장 | 코인 500개를 빨아들이는 순간 `PlayerPrefs.Save()`가 500번 — 모바일에서 눈에 보이는 끊김 |
| (4) | UI가 매 프레임 값을 **당겨온다(polling)** | 점수가 안 바뀌어도 매 프레임 문자열을 새로 만듭니다(02장에서 측정합니다). 체력·경험치·콤보까지 UI가 늘면 모두 `Update`에서 돌게 됩니다 |

또 `PlayerController`는 구식 `Input.GetAxis`를 씁니다. Unity 6 신규 프로젝트는 New Input System이 기본이라, 프로젝트 설정에서 입력 처리 방식이 "Input System Package (New)"만 켜져 있으면 이 줄이 `InvalidOperationException`을 던집니다.

React로 비유하면 지금 코드는 **모든 컴포넌트가 전역 변수 `window.store`를 직접 읽고 쓰는 상태**입니다. React에서는 props와 콜백, 또는 이벤트 구독으로 이걸 풀었습니다. C#에서 같은 역할을 하는 도구가 델리게이트와 이벤트이고, "부품을 갈아 끼울 수 있는" 구조를 만드는 도구가 인터페이스와 제네릭입니다.

## 개념

### 델리게이트 — "메서드를 담는 변수"

델리게이트는 메서드를 가리키는 **타입이 있는** 참조입니다. JS에서 함수를 변수에 담아 넘기던 것과 같지만, C#에서는 매개변수와 반환 타입이 맞아야만 담을 수 있습니다.

```csharp
public delegate void ScoreHandler(int newScore);   // "int 하나 받고 반환 없는 메서드"의 모양
ScoreHandler handler = PrintScore;   // JS: const handler = printScore;
handler += PlaySound;                // 여러 개를 이어 붙일 수 있음(멀티캐스트)
handler(10);                         // PrintScore(10), PlaySound(10) 순서로 호출
handler -= PlaySound;                // 떼어내기
```

매번 델리게이트 타입을 선언하는 건 번거로워서, .NET은 범용 타입을 미리 제공합니다.

| 타입 | 모양 | 예 | JS 대응 |
|---|---|---|---|
| `Action` | 인자 없음, 반환 없음 | `Action onDied` | `() => void` |
| `Action<T1, T2>` | 인자 있음, 반환 없음 (최대 16개) | `Action<int, int> onChanged` | `(a, b) => void` |
| `Func<TResult>` | 인자 없음, 반환 있음 | `Func<bool> canMove` | `() => boolean` |
| `Func<T, TResult>` | 마지막 타입이 반환형 | `Func<Enemy, float> scoreOf` | `(e) => number` |

실무에서는 직접 `delegate`를 선언하는 일은 드물고 거의 `Action`/`Func`를 씁니다. 다만 매개변수 이름이 문서 역할을 해야 할 때(`delegate void DamageHandler(int amount, Vector2 hitPoint)`)는 직접 선언이 읽기 좋습니다.

람다도 델리게이트에 담깁니다: `Func<int, int> doubler = x => x * 2;` (JS: `const doubler = x => x * 2`)

### event — "밖에서는 구독만 할 수 있는 델리게이트"

델리게이트 필드를 `public`으로 열어 두면 위험합니다.
```csharp
public Action Died;              // BadHealth — event 키워드 없음
// 다른 스크립트에서
badHealth.Died = OnDied;         // ❌ '=' 로 다른 구독자를 전부 날려버림
badHealth.Died();                // ❌ 죽지도 않았는데 외부에서 "죽었다"고 발행
```

`event` 키워드를 붙이면 클래스 **밖**에서는 `+=`와 `-=`만 허용되고, 발행은 선언한 클래스 안에서만 할 수 있습니다.

```csharp
public event Action Died;        // Health — 밖에서는 += / -= 만 가능
void Kill() => Died?.Invoke();   // 구독자가 없으면 null이므로 ?. 로 호출
```

> `?.`는 C# 델리게이트에는 안전하게 쓸 수 있습니다. 하지만 `GameObject`, `Component` 같은 **UnityEngine.Object**에는 쓰지 마세요. 파괴된 오브젝트가 `== null`로는 true인데 `?.`로는 null이 아닌 것으로 취급되는 Unity의 특수 처리 때문입니다(기초 트랙 PART 5의 지뢰 3번).

JS `EventEmitter`의 `on`/`off`/`emit`이 각각 `+=`/`-=`/`Invoke`에 해당합니다. 차이는 이벤트 이름이 문자열이 아니라 멤버라서 **오타가 런타임 버그가 아니라 컴파일 에러**가 된다는 점입니다.

### 구독 해제 — OnEnable / OnDisable 규칙

이벤트는 **발행자가 구독자를 참조로 붙잡고** 있습니다. 구독자가 파괴되어도 `-=`를 하지 않았다면 발행자의 목록에 그대로 남습니다. 그러면 두 가지 일이 생깁니다.

```
[Health: Died 이벤트] ──참조──▶ [ScoreDisplay.OnDied]  (ScoreDisplay는 이미 Destroy됨)
1) 다음 발행 때 파괴된 컴포넌트의 메서드가 실행 → label 접근 순간 MissingReferenceException
2) 발행자가 오래 살면(static, ScriptableObject, DontDestroyOnLoad) 구독자가 메모리에서 안 풀림
```

그래서 Unity에서는 이 짝을 **규칙으로** 씁니다.

```csharp
void OnEnable()  => health.Died += HandleDied;   // 켜질 때 구독
void OnDisable() => health.Died -= HandleDied;   // 꺼질 때(파괴 직전 포함) 해제
```

`OnDisable`은 컴포넌트가 비활성화될 때와 **파괴되기 직전**에 모두 호출됩니다. 그래서 `Awake`/`OnDestroy` 짝보다 `OnEnable`/`OnDisable` 짝이 안전합니다. 오브젝트를 껐다 켜도(12장 오브젝트 풀에서 매일 일어나는 일) 구독이 중복되거나 새지 않습니다. React의 `useEffect(() => { subscribe(); return () => unsubscribe(); }, [])`와 똑같은 사고방식입니다.

람다로 구독하면 해제할 수 없다는 점도 기억하세요. `health.Died -= () => Debug.Log("사망");`은 구독할 때와 **다른 람다 인스턴스**라 아무것도 떼어내지 못합니다. 해제가 필요한 구독은 이름 있는 메서드로 하거나, 람다를 필드에 저장해 같은 인스턴스로 해제합니다.

### static 이벤트 — 편하지만 조심해서

인스턴스를 찾을 필요 없이 `Coin.AnyCollected += ...`처럼 구독할 수 있는 `static event`는 "코인 아무거나 먹혔다" 같은 **종류 전체**의 사건에 잘 맞습니다. 이번 장의 실습에서 씁니다. 하지만 static 이벤트는 씬이 바뀌어도 사라지지 않으므로 해제를 빼먹으면 반드시 문제가 납니다.

또한 에디터의 **Enter Play Mode Options**에서 도메인 리로드를 끄면(플레이 진입이 빨라져서 많이들 끕니다) static 필드가 이전 플레이의 값을 유지합니다. 이때는 `[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]`를 붙인 static 메서드에서 이벤트를 `null`로 초기화해야 합니다(실습의 `Coin.ResetStatics`). 03장에서는 static 이벤트를 ScriptableObject 이벤트 채널로 바꿔 이 문제를 구조적으로 없앱니다.

### 제네릭 — 타입을 매개변수로

제네릭은 "타입만 다르고 로직은 같은" 코드를 한 번만 쓰게 해 줍니다. TypeScript의 `function first<T>(arr: T[]): T`와 같습니다. 이미 매일 쓰고 있습니다 — `GetComponent<Rigidbody2D>()`, `List<int>`.

**제약(`where`)**은 T에 "최소한 이런 능력은 있어야 한다"는 조건을 겁니다. 제약이 있어야 T의 멤버를 쓸 수 있습니다.

```csharp
// T는 Component여야 한다 → AddComponent<T>()에 넘길 수 있음
public static T GetOrAdd<T>(GameObject go) where T : Component
{
    if (!go.TryGetComponent(out T component))
        component = go.AddComponent<T>();
    return component;
}

// T는 서로 비교할 수 있어야 한다 → CompareTo 사용 가능
public static T Max<T>(T a, T b) where T : IComparable<T>
{
    return a.CompareTo(b) >= 0 ? a : b;
}
```

| 제약 | 의미 | 쓰는 곳 |
|---|---|---|
| `where T : class` | 참조 타입 | null 비교가 필요할 때 |
| `where T : struct` | 값 타입 | 박싱 없는 컨테이너(02장) |
| `where T : Component` | 특정 기반 클래스 | `GetComponent<T>`, `AddComponent<T>` |
| `where T : IDamageable` | 특정 인터페이스 | 인터페이스 멤버 호출 |

제네릭 **클래스**도 만들 수 있습니다. 다만 Unity 컴포넌트로 붙이려면 제네릭 인자가 확정된 클래스여야 합니다. `class Spawner<T> : MonoBehaviour`는 오브젝트에 직접 붙일 수 없고, `class EnemySpawner : Spawner<Enemy>`처럼 한 번 상속해서 구체 클래스를 만들어야 합니다. ScriptableObject도 마찬가지입니다(03장의 `EventChannel<T>` → `IntEventChannel`).

### 인터페이스 vs 추상 클래스

둘 다 "이런 기능이 있다"는 약속이지만 쓰임새가 다릅니다.

```csharp
public interface IDamageable { void TakeDamage(int amount); }   // "할 수 있는 일"만 약속

public abstract class Pickup : MonoBehaviour                      // 공통 구현 + "자식이 채울 부분"
{
    protected virtual void OnTriggerEnter2D(Collider2D other) { /* 태그 확인 → TryCollect → 파괴 */ }
    protected abstract bool TryCollect(GameObject collector);
}
```

| 기준 | 인터페이스 | 추상 클래스 |
|---|---|---|
| 다중 상속 | 여러 개 구현 가능 | 하나만 상속 |
| 상태(필드) | 가질 수 없음 | 가질 수 있음 |
| Unity와의 관계 | MonoBehaviour든 일반 클래스든 붙일 수 있음 | MonoBehaviour를 상속하면 자식도 전부 컴포넌트 |
| 좋은 질문 | "이것에게 **무엇을 시킬 수 있나**?" | "이것들은 **같은 종류**인가?" |

코인 러시에서 플레이어·적·부서지는 상자·보스 부위는 서로 전혀 다른 종류지만 모두 "피해를 받을 수 있다". → `IDamageable`. 코인·체력 팩·자석 아이템은 "플레이어가 닿으면 먹힌다"는 흐름을 공유하는 같은 종류. → `Pickup` 추상 클래스.

인터페이스로 찾을 때는 `GetComponent`/`TryGetComponent`가 인터페이스 타입도 받아 준다는 점이 핵심입니다.

```csharp
if (other.TryGetComponent(out IDamageable target))   // Health든 Crate든 상관없음
    target.TakeDamage(1);
```

### 확장 메서드

기존 타입(심지어 `Vector2`, `LayerMask`처럼 내가 못 고치는 타입)에 메서드를 "붙인 것처럼" 호출하게 해 줍니다. `static` 클래스의 `static` 메서드에서 첫 매개변수 앞에 `this`를 붙입니다.

```csharp
public static bool Contains(this LayerMask mask, int layer) => (mask.value & (1 << layer)) != 0;
if (targetLayers.Contains(other.gameObject.layer)) { ... }   // → Extensions.Contains(targetLayers, ...) 로 컴파일
```

JS에서 `Array.prototype`에 메서드를 추가하는 것과 겉모습이 비슷하지만, 원본 타입을 전혀 건드리지 않고 **해당 네임스페이스가 using된 곳에서만** 보인다는 점이 다릅니다. 남용하면 "이 메서드 어디서 왔지?"가 되니 자주 쓰는 짧은 도우미에만 씁니다. 같은 이름의 인스턴스 메서드가 있으면 인스턴스 메서드가 우선합니다.

### 패턴 매칭

Unity 6의 C#(9.0)에서 쓸 수 있는 패턴입니다.

```csharp
// switch 식 + 관계 패턴 (C# 9). 괄호 필수: switch 식이 / 보다 먼저 결합합니다
string HealthLabel(int current, int max) => ((float)current / max) switch
{
    <= 0f => "사망", < 0.3f => "위험", < 0.7f => "부상", _ => "건강",
};
bool IsBossAlmostDead(Health h) => h is { IsDead: false, Current: <= 10 };   // 속성 패턴
```

`is not null`, `is { }` 같은 패턴은 C# 수준의 null 검사라서 **파괴된 UnityEngine.Object를 걸러내지 못합니다.** Unity 오브젝트는 `!= null`이나 `if (obj)`로 검사하세요. C# 11의 리스트 패턴(`[1, 2, ..]`)은 Unity 6에서 쓸 수 없습니다.

### 프로퍼티와 record

프로퍼티는 필드처럼 보이지만 접근을 통제합니다. 이 장의 `Health.Current`처럼 **읽기는 공개, 쓰기는 비공개**가 가장 흔한 형태입니다.

`public int Current { get; private set; }`(자동 프로퍼티), `public int Max => max;`(읽기 전용), `public bool IsDead => Current <= 0;`(계산 프로퍼티)처럼 씁니다.

Unity는 **자동 프로퍼티를 직렬화하지 않습니다.** Inspector에 보이게 하려면 `[SerializeField] private int max;` 필드 + 프로퍼티를 쓰거나, `[field: SerializeField] public int Max { get; private set; }`처럼 백킹 필드에 특성을 붙입니다(후자는 직렬화 이름이 `<Max>k__BackingField`가 되어 나중에 이름을 바꾸기 번거롭습니다).

`record`는 **값 동등성**(`==`가 참조가 아니라 멤버 값을 비교)을 자동으로 제공하는 타입으로, 불변 데이터 모델을 짧게 쓰기에 유용합니다. `public record RunResult(int Score, float SurvivedSeconds);`처럼 위치 매개변수로 선언하면 `init` 전용 프로퍼티가 만들어지고, `var b = a with { Score = 150 };`으로 일부만 바꾼 복사본을 만듭니다(JS: `{...a, score: 150}`).

다만 record라고 해서 불변이 **강제되지는** 않습니다. `public int Score { get; set; }`처럼 `set` 프로퍼티를 직접 선언할 수 있고, `with`는 **얕은 복사**라서 참조형 멤버는 원본과 사본이 같은 객체를 공유합니다.

```csharp
public record Loadout(string Name, List<string> Weapons);
var a = new Loadout("기본", new List<string> { "탄" });
var b = a with { Name = "복사본" };
b.Weapons.Add("산탄");   // a.Weapons에도 "산탄"이 들어 있다 — 같은 List를 공유
```

불변이 필요하면 멤버도 `int`, `string` 같은 값·불변 타입이나 `IReadOnlyList<T>`로 두고, 목록은 새로 만들어 넘기세요.

Unity에서의 제약이 두 가지 있습니다. 첫째, record와 `init` 접근자는 `IsExternalInit` 타입이 필요한데 Unity의 기본 라이브러리에 없어서, 프로젝트 어딘가에 `namespace System.Runtime.CompilerServices { internal static class IsExternalInit { } }` 한 줄을 넣어야 컴파일됩니다. 둘째, **Unity 직렬화는 record를 지원하지 않으므로** Inspector·세이브 데이터에는 쓰지 말고 코드 안에서 주고받는 결과값에만 쓰세요.

## 실습: 코인 러시에 적용하기

이번 실습의 목표 구조는 다음과 같습니다. 화살표는 "누가 누구를 아는가"입니다.

```
[변경 전]                                  [변경 후]
Coin ───────────▶ GameManager.Instance     Coin ──(static event AnyCollected)──┐
ScoreDisplay ───▶ GameManager.Instance                                          ▼
                                            GameManager ──(event ScoreChanged)──▶ ScoreDisplay
                                                 ▲         (event GameOver)────▶ GameOverView
                                                 │
                                            Health(Player) ──(event Changed)───▶ HealthDisplay
                                                 (event Died) ─▶ GameManager
                                            DamageOnTouch(가시 공) ──IDamageable──▶ Health
```

`Coin`은 더 이상 누가 점수를 세는지 모르고, `DamageOnTouch`는 맞는 대상이 플레이어인지 상자인지 모릅니다.

### 1단계: 폴더와 입력 준비

1. Project 창에서 `Assets/_CoinRush/Scripts/` 아래에 `Core`, `Player`, `Combat`, `Items`, `UI`, `Utils` 폴더를 만듭니다.
2. STEP 4의 `PlayerController.cs`를 삭제하고, `Coin.cs`, `GameManager.cs`, `ScoreDisplay.cs`는 이번 장에서 **전체를 새로 작성**하므로 위 폴더로 옮겨 둡니다(`Items`, `Core`, `UI`).
3. **Window → Package Manager**의 **In Project** 목록에 **Input System**이 있는지 확인합니다. 없으면 **Unity Registry**에서 Input System을 찾아 Install합니다. 이 장의 `InputSystem.actions`(프로젝트 전역 액션)는 **1.8.0 이상**에서만 있습니다. Unity 6.0 템플릿에는 보통 1.11 계열이 들어 있으며, 목록에 표시된 버전이 1.8.0보다 낮으면 Update합니다. 설치 직후 "새 입력 백엔드를 활성화하고 에디터를 재시작할까요?" 창이 뜨면 **Yes**를 누릅니다.
4. **Edit → Project Settings → Player → Other Settings → Active Input Handling**이 "Input System Package (New)" 또는 "Both"인지 확인합니다. 기초 트랙의 `Input.GetAxis` 코드가 아직 남은 프로젝트라면 **Both**로 두는 것이 안전합니다. 값을 바꾸면 에디터가 재시작됩니다.
5. **Project Settings → Input System Package**에서 Project-wide Actions에 에셋(Unity 6 신규 프로젝트라면 `InputSystem_Actions`)이 지정되어 있는지 확인합니다. 비어 있다면 그 화면의 생성 버튼으로 기본 에셋을 만들어 지정합니다. 기본 에셋의 `Player` 맵에는 WASD·방향키·게임패드 스틱이 묶인 `Move` 액션이 들어 있습니다. 입력 시스템 자체는 08장에서 자세히 다룹니다.
6. **Tags and Layers**에서 레이어 `Player`, `Enemy`, `Coin`을 추가합니다.

### 2단계: 확장 메서드 모음

```csharp
// Assets/_CoinRush/Scripts/Utils/Extensions.cs
using System.Collections.Generic;
using UnityEngine;

public static class Extensions
{
    // LayerMask에 해당 레이어가 포함되어 있는가
    public static bool Contains(this LayerMask mask, int layer)
        => (mask.value & (1 << layer)) != 0;

    // x, y를 각각 최소/최대 사이로 자르기 (Vector2에는 성분별 Clamp가 없음)
    public static Vector2 ClampTo(this Vector2 v, Vector2 min, Vector2 max)
        => new Vector2(Mathf.Clamp(v.x, min.x, max.x), Mathf.Clamp(v.y, min.y, max.y));

    // 목록에서 무작위 하나 (05장 EnemySpawner에서 사용)
    public static T PickRandom<T>(this IReadOnlyList<T> items)
    {
        if (items == null || items.Count == 0)
            throw new System.ArgumentException("비어 있는 목록에서 고를 수 없습니다.");
        return items[Random.Range(0, items.Count)];
    }
}
```

### 3단계: IDamageable과 Health

```csharp
// Assets/_CoinRush/Scripts/Combat/IDamageable.cs
public interface IDamageable
{
    void TakeDamage(int amount);
}
```

```csharp
// Assets/_CoinRush/Scripts/Combat/Health.cs
using System;
using UnityEngine;

public class Health : MonoBehaviour, IDamageable
{
    [SerializeField, Min(1)] private int max = 5;
    public int Current { get; private set; }
    public int Max => max;
    public bool IsDead => Current <= 0;

    // true인 동안 피해를 받지 않음 (04장 Hurt 상태의 무적 시간에 사용)
    public bool Invulnerable { get; set; }

    // (현재 체력, 최대 체력) — JS: emitter.emit('changed', current, max)
    public event Action<int, int> Changed;
    public event Action Died;
    void Awake() => Current = max;

    // 데이터 에셋 등에서 최대 체력을 정해 줄 때 (03장 EnemyData에서 사용)
    public void Initialize(int newMax)
    {
        max = Mathf.Max(1, newMax);
        Current = max;
        Changed?.Invoke(Current, max);
    }

    public void TakeDamage(int amount)
    {
        if (amount <= 0 || IsDead || Invulnerable) return;
        Current = Mathf.Max(Current - amount, 0);
        Changed?.Invoke(Current, max);
        if (Current == 0)
            Died?.Invoke();
    }

    public void Heal(int amount)
    {
        if (amount <= 0 || IsDead) return;
        Current = Mathf.Min(Current + amount, max);
        Changed?.Invoke(Current, max);
    }
}
```

`Died`는 체력이 0이 되는 **그 순간 한 번만** 발행됩니다. 맨 앞의 `IsDead` 검사 덕분에 죽은 뒤에 또 맞아도 다시 발행되지 않습니다.

### 4단계: DamageOnTouch와 FallOutCleanup

```csharp
// Assets/_CoinRush/Scripts/Combat/DamageOnTouch.cs
using UnityEngine;

public class DamageOnTouch : MonoBehaviour
{
    [SerializeField, Min(0)] private int damage = 1;
    [SerializeField] private LayerMask targetLayers;
    [SerializeField] private bool destroySelfOnHit = true;
    public int Damage
    {
        get => damage;
        set => damage = Mathf.Max(0, value);
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (!targetLayers.Contains(other.gameObject.layer)) return;

        // 상대가 무엇이든 IDamageable만 구현했으면 된다
        if (other.TryGetComponent(out IDamageable target))
        {
            target.TakeDamage(damage);
            if (destroySelfOnHit) Destroy(gameObject);
        }
    }
}
```

STEP 4의 `Coin.Update` 안에 있던 "y < -6이면 파괴"는 코인만의 일이 아닙니다. 가시 공도 필요합니다. 작은 컴포넌트로 떼어냅니다.

```csharp
// Assets/_CoinRush/Scripts/Utils/FallOutCleanup.cs
using UnityEngine;

public class FallOutCleanup : MonoBehaviour
{
    [SerializeField] private float killY = -6f;
    void Update()
    {
        if (transform.position.y < killY) Destroy(gameObject);
    }
}
```

### 5단계: Pickup 추상 클래스와 Coin

```csharp
// Assets/_CoinRush/Scripts/Items/Pickup.cs
using UnityEngine;

public abstract class Pickup : MonoBehaviour
{
    // 자식이 필요하면 override할 수 있게 protected virtual
    protected virtual void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("Player")) return;
        if (TryCollect(other.gameObject))
            Destroy(gameObject);
    }

    // true를 돌려주면 먹힌 것으로 보고 파괴
    protected abstract bool TryCollect(GameObject collector);
}
```

```csharp
// Assets/_CoinRush/Scripts/Items/Coin.cs
using System;
using UnityEngine;

public class Coin : Pickup
{
    // "어떤 코인이든 먹혔다" — 코인 종류 전체의 사건이라 static
    public static event Action<int> AnyCollected;

    [SerializeField, Min(1)] private int value = 1;
    protected override bool TryCollect(GameObject collector)
    {
        AnyCollected?.Invoke(value);
        return true;
    }

    // 도메인 리로드를 끈 상태에서도 이전 플레이의 구독자가 남지 않게
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics() => AnyCollected = null;
}
```

### 6단계: PlayerMover

STEP 4의 `PlayerController`를 대체합니다. 서바이버라이크로 가기 위해 상하좌우로 움직이게 하고, 물리 충돌 판정이 안정적이도록 Kinematic `Rigidbody2D`로 이동합니다(07장에서 가속·감속을 넣어 개선합니다).

```csharp
// Assets/_CoinRush/Scripts/Player/PlayerMover.cs
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody2D))]
public class PlayerMover : MonoBehaviour
{
    [SerializeField] private float speed = 6f;
    [SerializeField] private Vector2 boundsMin = new Vector2(-8f, -4.5f);
    [SerializeField] private Vector2 boundsMax = new Vector2(8f, 4.5f);
    private Rigidbody2D body;
    private InputAction moveAction;
    public Vector2 MoveInput { get; private set; }

    // false면 입력을 무시 (04장 상태 머신이 제어)
    public bool CanMove { get; set; } = true;

    void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        // 프로젝트 전역 액션 에셋에서 "Player" 맵의 "Move" 액션을 찾는다
        moveAction = InputSystem.actions.FindAction("Player/Move", throwIfNotFound: true);
    }

    void Update()
    {
        // 입력은 매 프레임 읽고
        MoveInput = CanMove ? moveAction.ReadValue<Vector2>() : Vector2.zero;
    }

    void FixedUpdate()
    {
        // 이동은 물리 스텝에서
        Vector2 next = body.position + MoveInput * speed * Time.fixedDeltaTime;
        body.MovePosition(next.ClampTo(boundsMin, boundsMax));
    }
}
```

### 7단계: 이벤트로 다시 쓴 GameManager

```csharp
// Assets/_CoinRush/Scripts/Core/GameManager.cs
using System;
using UnityEngine;

public class GameManager : MonoBehaviour
{
    private const string HighScoreKey = "highScore";

    [Header("참조")]
    [SerializeField] private Health playerHealth;

    [Header("스폰")]
    [SerializeField] private GameObject coinPrefab;
    [SerializeField] private GameObject hazardPrefab;
    [SerializeField] private float coinInterval = 1f;
    [SerializeField] private float hazardInterval = 2.5f;
    [SerializeField] private float spawnY = 6f;
    [SerializeField] private float spawnHalfWidth = 8f;
    public int Score { get; private set; }
    public int HighScore { get; private set; }
    public bool IsGameOver { get; private set; }
    public event Action<int> ScoreChanged;
    public event Action GameOver;
    private float coinTimer;
    private float hazardTimer;
    void Awake() => HighScore = PlayerPrefs.GetInt(HighScoreKey, 0);

    void OnEnable()
    {
        Coin.AnyCollected += HandleCoinCollected;
        playerHealth.Died += HandlePlayerDied;
    }

    void OnDisable()
    {
        Coin.AnyCollected -= HandleCoinCollected;
        if (playerHealth != null)                 // 플레이어가 먼저 파괴됐을 수 있음
            playerHealth.Died -= HandlePlayerDied;
    }

    // 구독자들(UI)이 첫 값을 그릴 수 있도록 초기값 한 번 발행
    void Start() => ScoreChanged?.Invoke(Score);

    void Update()
    {
        if (IsGameOver) return;
        TickSpawn(ref coinTimer, coinInterval, coinPrefab);
        TickSpawn(ref hazardTimer, hazardInterval, hazardPrefab);
    }

    // ref: 호출한 쪽의 변수(coinTimer 등)를 직접 고친다
    private void TickSpawn(ref float timer, float interval, GameObject prefab)
    {
        timer += Time.deltaTime;
        if (timer < interval) return;
        timer -= interval;
        float x = UnityEngine.Random.Range(-spawnHalfWidth, spawnHalfWidth);
        Instantiate(prefab, new Vector3(x, spawnY, 0f), Quaternion.identity);
    }

    private void HandleCoinCollected(int amount)
    {
        if (IsGameOver) return;
        Score += amount;
        ScoreChanged?.Invoke(Score);
    }

    private void HandlePlayerDied()
    {
        IsGameOver = true;

        // 저장은 코인마다가 아니라 판이 끝날 때 한 번
        if (Score > HighScore)
        {
            HighScore = Score;
            PlayerPrefs.SetInt(HighScoreKey, HighScore);
            PlayerPrefs.Save();
        }
        playerHealth.gameObject.SetActive(false);
        GameOver?.Invoke();
    }
}
```

`using System;`과 `using UnityEngine;`을 함께 쓰면 `Random`이 `System.Random`과 `UnityEngine.Random` 사이에서 모호해집니다. 그래서 `UnityEngine.Random.Range`로 전체 이름을 썼습니다. `Instance`는 없습니다. 이 오브젝트가 필요한 쪽은 Inspector에서 참조를 받습니다.

### 8단계: UI — 구독하는 쪽

씬에 Canvas가 없다면 STEP 4처럼 **UI → Text - TextMeshPro**로 만듭니다. `ScoreText`(좌상단), `HealthText`(우상단), 그리고 화면 중앙에 `GameOverPanel`(Panel 안에 "GAME OVER" 텍스트)을 만듭니다.

**한글 폰트 준비.** TMP 기본 폰트(LiberationSans SDF)에는 한글 글리프가 없어서 "점수"가 □로 보이고 Console에 글리프 누락 경고가 찍힙니다. 이 교과서의 UI는 한글을 쓰므로 지금 최소 설정을 해 둡니다(정적 아틀라스·폴백 구성은 11장).

1. 한글을 지원하고 게임 배포가 허용된 폰트(예: Noto Sans KR, Pretendard — SIL Open Font License)의 `.ttf`/`.otf` 파일을 `Assets/_CoinRush/Fonts/`에 넣습니다.
2. Project 창에서 폰트 파일을 우클릭 → **Create → TextMeshPro → Font Asset → SDF**를 선택합니다(버전에 따라 **Font Asset** 항목 바로 아래일 수 있습니다). 같은 폴더에 `... SDF` 폰트 에셋이 생깁니다. 이렇게 만든 에셋은 Dynamic 모드라, 처음 쓰는 글자를 필요할 때 아틀라스에 추가합니다.
3. **Edit → Project Settings → TextMesh Pro → Settings**의 **Default Font Asset**에 이 에셋을 지정합니다. 이후 새로 만드는 TMP 텍스트는 이 폰트를 씁니다. 이미 만든 텍스트(`ScoreText` 등)는 Inspector의 **Font Asset** 칸에 직접 지정합니다.

```csharp
// Assets/_CoinRush/Scripts/UI/ScoreDisplay.cs
using TMPro;
using UnityEngine;

[RequireComponent(typeof(TextMeshProUGUI))]
public class ScoreDisplay : MonoBehaviour
{
    [SerializeField] private GameManager gameManager;
    private TextMeshProUGUI label;
    void Awake() => label = GetComponent<TextMeshProUGUI>();

    void OnEnable()
    {
        gameManager.ScoreChanged += Show;
        Show(gameManager.Score);   // 꺼져 있던 동안 바뀐 점수도 켜질 때 다시 그린다
    }

    void OnDisable()
    {
        if (gameManager != null) gameManager.ScoreChanged -= Show;
    }

    // Update가 없다 — 점수가 바뀔 때만 호출된다
    private void Show(int score) => label.text = $"점수: {score}";
}
```

```csharp
// Assets/_CoinRush/Scripts/UI/HealthDisplay.cs
using TMPro;
using UnityEngine;

[RequireComponent(typeof(TextMeshProUGUI))]
public class HealthDisplay : MonoBehaviour
{
    [SerializeField] private Health health;
    private TextMeshProUGUI label;
    void Awake() => label = GetComponent<TextMeshProUGUI>();

    void OnEnable()
    {
        health.Changed += Show;
        Show(health.Current, health.Max);   // 구독 시점의 현재 값 그리기
    }

    void OnDisable()
    {
        if (health != null) health.Changed -= Show;
    }

    private void Show(int current, int max) => label.text = $"HP {current}/{max}";
}
```

이 코드에는 초기화 순서에 따라 "HP 0/5"가 표시될 수 있는 함정이 하나 숨어 있습니다. 연습 문제 1에서 원인을 찾아 고칩니다.

```csharp
// Assets/_CoinRush/Scripts/UI/GameOverView.cs
using UnityEngine;

public class GameOverView : MonoBehaviour
{
    [SerializeField] private GameManager gameManager;
    [SerializeField] private GameObject panel;
    void Awake() => panel.SetActive(false);
    void OnEnable() => gameManager.GameOver += Show;

    void OnDisable()
    {
        if (gameManager != null) gameManager.GameOver -= Show;
    }

    private void Show() => panel.SetActive(true);
}
```

### 9단계: 씬 조립

1. **Player**: Tag·Layer `Player`, `Rigidbody2D` 추가(Body Type **Kinematic**), `Box Collider 2D`는 그대로, `PlayerMover`·`Health`(Max 5) 추가.
2. **Coin 프리팹** 열기: 기존 `Coin` 컴포넌트가 새 스크립트로 바뀌었는지 확인, Layer `Coin`, `FallOutCleanup` 추가.
3. **가시 공 프리팹** 만들기:
   - 2D Object → Sprites → Circle, 이름 `Hazard`, 색 빨강, Scale 0.7, Layer `Enemy`
   - `Circle Collider 2D`(Is Trigger 체크), `Rigidbody2D`(Gravity Scale 0.8)
   - `DamageOnTouch` → Damage 1, Target Layers `Player`, Destroy Self On Hit 체크
   - `FallOutCleanup` 추가
   - `Assets/_CoinRush/Prefabs/`로 드래그해 프리팹으로 만들고 씬의 원본 삭제
4. **GameManager** 오브젝트: Player Health에 Player, Coin Prefab, Hazard Prefab 연결.
5. **ScoreText**의 `ScoreDisplay`, **Canvas**의 `GameOverView`에 GameManager와 GameOverPanel을(패널 자체에 붙이면 `Awake`에서 스스로를 꺼 구독이 해제되니 주의), **HealthText**의 `HealthDisplay`에 Player를 연결합니다.

### 확인하기

- ▶ Play 후 WASD/방향키로 플레이어가 상하좌우로 움직이고 화면 경계에서 멈춘다.
- 코인을 먹으면 좌상단 점수가 오른다. Console에 에러가 없다.
- 빨간 공에 닿으면 우상단 HP가 1씩 줄고 공은 사라진다.
- HP가 0이 되면 플레이어가 사라지고 GAME OVER 패널이 뜬다. 점수가 더 오르지 않는다.
- Play를 멈추고 다시 시작해도 에러가 없다. (구독 해제가 잘 되었다는 신호)
- `Coin` 프리팹 하나만 있는 **빈 씬**에서 Play해도 에러가 없다. (STEP 4 코드라면 `NullReferenceException` — 결합이 끊어졌다는 증거)

## 흔한 실수

1. **Play를 두 번째 누르거나 씬을 다시 로드하면 `MissingReferenceException`이 난다**
   원인: static 이벤트(`Coin.AnyCollected`)나 오래 사는 객체의 이벤트를 구독만 하고 `OnDisable`에서 해제하지 않았습니다.
   해결: 모든 `+=`에 짝이 되는 `-=`를 `OnDisable`에 씁니다. 코드 리뷰 때 `+=` 개수와 `-=` 개수를 세어 보세요.
2. **점수가 한 번 먹을 때 2씩 오른다**
   원인: `Awake`나 `Start`에서 구독하고 `OnEnable`에서도 또 구독했습니다. 또는 `Awake`/`Start`에서만 구독하고 `OnDisable`에서 해제하면, 껐다 켤 때 `OnEnable`의 구독이 추가되어 쌓입니다. (`Start`는 인스턴스 수명 동안 한 번만 호출되므로 껐다 켜도 다시 불리지 않습니다.)
   해결: 구독은 `OnEnable` 한 곳에서만 합니다.
3. **`OnDisable`에서 `NullReferenceException`**
   원인: 씬이 닫힐 때 오브젝트 파괴 순서는 보장되지 않아서, 구독 대상(`gameManager`)이 먼저 파괴됐습니다.
   해결: 해제 전에 `if (gameManager != null)`로 검사합니다. 이 장의 코드가 모두 그렇게 되어 있습니다.
4. **`DamageOnTouch`가 아무 반응이 없다**
   원인: Target Layers를 `Nothing`으로 두었거나, 두 오브젝트 모두 `Rigidbody2D`가 없거나, Is Trigger를 체크하지 않았습니다. 트리거 이벤트는 둘 중 최소 하나에 `Rigidbody2D`가 있어야 발생합니다.
   해결: Target Layers를 `Player`로, 가시 공에 `Rigidbody2D`와 트리거 콜라이더가 있는지 확인합니다.
5. **`InvalidOperationException: ... not found`가 `PlayerMover.Awake`에서 난다**
   원인: 프로젝트 전역 액션 에셋이 지정되지 않았거나, 맵·액션 이름이 `Player/Move`와 다릅니다.
   해결: 1단계 3·5번(패키지 버전, 전역 액션 에셋 지정)을 다시 확인합니다. 이름을 바꿨다면 문자열도 맞춥니다.

## 연습 문제

**1. ★☆☆ HealthDisplay 초기화 순서 고치기**
`HealthDisplay`가 처음에 "HP 0/5"를 표시할 수 있는 이유를 설명하고, 항상 올바른 값이 표시되도록 고치세요.

<details><summary>힌트·해설</summary>

같은 씬에서 로드되는 오브젝트들은 오브젝트 단위로 `Awake → OnEnable`이 이어서 실행되므로, `HealthDisplay.OnEnable`이 `Health.Awake`보다 먼저 올 수 있습니다. 반면 `Start`는 씬의 모든 `Awake`/`OnEnable`이 끝난 뒤 첫 프레임 직전에 호출됩니다.

단, `Start`는 **한 번만** 호출됩니다. 초기 표시를 `Start`로만 옮기면, HP 표시를 껐다가(그동안 피해를 받고) 다시 켰을 때 구독만 복구되고 글자는 옛 값으로 남습니다. 그래서 첫 표시는 `Start`에서, 이후 다시 켜질 때는 `OnEnable`에서 현재 값을 읽도록 플래그를 둡니다.

```csharp
private bool started;

void OnEnable()
{
    health.Changed += Show;
    if (started) Show(health.Current, health.Max);   // 재활성화: 이미 Awake가 끝난 뒤라 안전
}

void Start()
{
    started = true;
    Show(health.Current, health.Max);                // 첫 표시: 모든 Awake 이후
}
```

`ScoreDisplay`는 `GameManager.Score`가 `Awake`와 무관하게 처음부터 0이라 `OnEnable`에서 바로 읽어도 됩니다(8단계 코드).

또 다른 방법은 **Project Settings → Script Execution Order**에서 `Health`를 먼저 실행시키는 것이지만, 순서 설정은 숨은 의존성이 되므로 마지막 수단으로 씁니다.
</details>

**2. ★☆☆ 체력 팩 만들기**
`Pickup`을 상속해 체력을 2 회복하는 `HealthPack`을 만드세요. 체력이 가득 차 있으면 먹히지 않고 그대로 남아야 합니다.

<details><summary>힌트·해설</summary>

`TryCollect`가 `false`를 돌려주면 `Pickup`이 파괴하지 않습니다.

```csharp
protected override bool TryCollect(GameObject collector)   // class HealthPack : Pickup
{
    if (!collector.TryGetComponent(out Health health) || health.Current >= health.Max) return false;
    health.Heal(amount);   // [SerializeField, Min(1)] private int amount = 2;
    return true;
}
```

`GameManager.TickSpawn`에 체력 팩 프리팹을 넣으면 공통 흐름(태그 확인, 파괴)은 한 줄도 다시 쓰지 않았다는 것을 확인할 수 있습니다.
</details>

**3. ★★☆ 코인 효과음을 GameManager 수정 없이 붙이기**
코인을 먹을 때마다 소리를 내는 `CoinSfx` 컴포넌트를 만드세요. `Coin`과 `GameManager`는 한 줄도 고치면 안 됩니다.

<details><summary>힌트·해설</summary>

`Coin.AnyCollected`를 구독하는 새 컴포넌트를 씬에 추가하면 됩니다. 이벤트 구조의 장점이 "발행자 수정 없이 구독자 추가"라는 것을 체감하는 문제입니다.

```csharp
// CoinSfx : MonoBehaviour — AudioSource와 [SerializeField] AudioClip clip 필드를 가진다
void OnEnable() => Coin.AnyCollected += Play;
void OnDisable() => Coin.AnyCollected -= Play;
private void Play(int value) => source.PlayOneShot(clip);   // value는 안 써도 Action<int> 모양에 맞춰 받는다
```
</details>

**4. ★★★ 부서지는 상자 (스스로 확장)**
체력 3짜리 상자를 만들고, 부서지면 코인 3개를 뿌리게 하세요. 조건: `Health`를 재사용하고, `DamageOnTouch`의 대상 레이어에 상자 레이어를 넣어도 코드는 바뀌지 않아야 합니다. 더 나아가 상자가 맞을 때 잠깐 하얗게 번쩍이는 `HitFlash` 컴포넌트를 `Health.Changed`만 구독해서 만들어 보세요.

<details><summary>힌트·해설</summary>

- 상자 프리팹: `Health`(Max 3) + `BoxCollider2D` + `CoinBurst` 컴포넌트.
- `CoinBurst`는 `OnEnable`에서 `health.Died += Burst`, `Burst`에서 코인을 `Instantiate`한 뒤 `Destroy(gameObject)`.
- `HitFlash`는 `Changed`에서 이전 체력보다 줄었을 때만 `SpriteRenderer.color`를 흰색으로 바꾸고 짧은 시간 뒤 원래 색으로 돌립니다. 이전 값을 필드에 저장해 비교하세요.
- 상자는 `IDamageable`을 **직접** 구현하지 않습니다. `Health`가 이미 구현하고 있으니까요. 인터페이스를 컴포넌트에 두면 "합성"으로 기능을 조립할 수 있다는 점을 확인하세요. 14장에서 `HitFlash`를 쉐이더 버전으로 바꿉니다.
</details>

## 셀프 체크

**1. `public Action Died;`와 `public event Action Died;`의 차이를 설명해 보세요.**

<details><summary>모범 답안</summary>

`event`가 붙으면 클래스 밖에서는 `+=`/`-=`만 할 수 있고 `=` 대입과 직접 호출(`Died()`)이 금지됩니다. 그래서 외부 코드가 다른 구독자를 실수로 지우거나 가짜로 이벤트를 발행할 수 없습니다. 델리게이트 필드는 둘 다 허용합니다.
</details>

**2. 구독을 `Awake`/`OnDestroy`가 아니라 `OnEnable`/`OnDisable`에서 하는 이유는 무엇인가요?**

<details><summary>모범 답안</summary>

`OnDisable`은 비활성화될 때와 파괴되기 직전 모두 호출되므로 해제가 누락되지 않습니다. 오브젝트를 껐다 켤 때(오브젝트 풀 등) 꺼진 동안에는 이벤트를 받지 않고, 다시 켜지면 한 번만 구독되므로 중복도 없습니다. `Awake`/`OnDestroy`는 한 번만 호출되어 비활성 상태에서도 이벤트를 받게 됩니다.
</details>

**3. 구독 해제를 빼먹으면 구체적으로 어떤 두 가지 문제가 생기나요?**

<details><summary>모범 답안</summary>

첫째, 발행자가 파괴된 구독자의 메서드를 계속 호출해 `MissingReferenceException` 같은 에러가 납니다. 둘째, 발행자가 구독자의 참조를 붙잡고 있어서, 발행자가 오래 살아 있는 경우(static, ScriptableObject, DontDestroyOnLoad) 구독자의 C# 객체가 GC되지 않고 메모리에 남습니다.
</details>

**4. 플레이어·적·상자에 `IDamageable` 인터페이스를, 코인·체력 팩에 `Pickup` 추상 클래스를 쓴 이유를 설명해 보세요.**

<details><summary>모범 답안</summary>

플레이어·적·상자는 서로 다른 종류지만 "피해를 받을 수 있다"는 능력만 공유하므로, 상속 계층을 강요하지 않는 인터페이스가 맞습니다. 코인·체력 팩은 "플레이어 태그 확인 → 먹기 → 파괴"라는 공통 흐름(구현)을 공유하는 같은 종류라서, 공통 코드를 담고 달라지는 부분만 `abstract`로 남기는 추상 클래스가 맞습니다.
</details>

## 핵심 요약

- 델리게이트는 타입이 있는 메서드 참조이고, 실무에서는 `Action`/`Func`를 주로 씁니다.
- `event`는 외부에 구독(`+=`/`-=`)만 허용해 이벤트를 보호합니다. 발행은 `Evt?.Invoke()`.
- 모든 구독은 `OnEnable`에서, 해제는 `OnDisable`에서 짝을 맞춥니다. 람다로 구독하면 해제할 수 없습니다.
- static 이벤트는 편하지만 씬을 넘어 살아남으므로 해제와 초기화에 특히 주의합니다.
- 제네릭 + `where` 제약으로 타입만 다른 코드를 한 번에 쓰고, 컴포넌트로 붙일 땐 구체 클래스로 상속합니다.
- "무엇을 시킬 수 있나"는 인터페이스, "같은 종류인가"는 추상 클래스로 판단합니다.
- 코인 러시는 이제 `Coin → (event) → GameManager → (event) → UI` 구조이며, 싱글턴 직접 호출이 없습니다.

## 더 읽을거리

- Microsoft Learn, "이벤트(C# 프로그래밍 가이드)" — https://learn.microsoft.com/ko-kr/dotnet/csharp/programming-guide/events/
- Microsoft Learn, "제네릭 형식 매개 변수에 대한 제약 조건" — https://learn.microsoft.com/ko-kr/dotnet/csharp/programming-guide/generics/constraints-on-type-parameters
- Unity Manual, "C# compiler" (Unity가 지원하는 C# 버전과 record 관련 주의) — https://docs.unity3d.com/Manual/csharp-compiler.html
- Unity Manual, "Order of execution for event functions" — https://docs.unity3d.com/Manual/execution-order.html
- Unity 전자책, "Level up your code with design patterns and SOLID" (Unity 공식 블로그·Unity Learn에서 무료 배포)
