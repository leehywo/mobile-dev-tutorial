# 03. ScriptableObject — 데이터와 이벤트 채널

> **이 장에서 배울 것**
> - ScriptableObject가 무엇이고 MonoBehaviour와 어떻게 다른지 설명할 수 있다
> - `CreateAssetMenu`로 `EnemyData`·`WeaponData` 데이터 에셋을 만들고 게임 오브젝트가 읽게 한다
> - 인스턴스 공유와 플레이 모드 수정값이 남는 문제를 피하는 규칙을 적용한다
> - `VoidEventChannel`·`IntEventChannel`과 제네릭 베이스로 이벤트 채널을 구현한다
> - 런타임 세트 패턴을 구현하고, 싱글턴을 없앨 곳과 남길 곳을 판단할 수 있다
>
> **선수 장**: 01, 02 · **예상 시간**: 3~4시간 · **코인 러시 진행**: `GameManager`가 사라집니다. 적(가시 공)과 무기 수치가 에셋으로 빠지고, 플레이어가 자동으로 총알을 쏘며, 맞아 부서진 가시 공이 코인을 떨굽니다. 점수·게임오버는 이벤트 채널로 흐릅니다.

## 왜 필요한가

01장에서 이벤트로 결합을 줄였지만 아직 세 가지가 막혀 있습니다.

**첫째, 프리팹은 씬 오브젝트를 참조할 수 없습니다.** 이번 장에서 "부서진 가시 공이 코인을 떨어뜨리게" 하려면 코인 프리팹이 점수를 올려야 합니다. 01장은 `Coin.AnyCollected`라는 static 이벤트로 이 문제를 피했지만, static은 씬을 넘어 살아남아 해제 누락에 취약합니다. 반대로 `ScoreDisplay`는 씬의 `GameManager`를 Inspector로 받았는데, 이 방식은 **런타임에 생성되는 프리팹**에는 쓸 수 없습니다. 프리팹 에셋의 필드에 씬 오브젝트를 드래그하면 Unity가 받아 주지 않습니다.

**둘째, 수치가 코드와 프리팹에 흩어져 있습니다.**

```
가시 공 체력    → Hazard 프리팹의 Health.max        (프리팹을 열어야 보임)
가시 공 피해량  → Hazard 프리팹의 DamageOnTouch.damage
스폰 간격      → 씬의 GameManager 컴포넌트          (씬을 열어야 보임)
```

적이 10종, 무기가 15종이 되면 밸런스를 조정하려고 프리팹 25개를 열었다 닫아야 합니다. 기획자(미래의 나)가 한 곳에서 표처럼 보고 싶어 하는 데이터입니다.

**셋째, `GameManager`가 너무 많은 일을 합니다.** 스폰, 점수, 최고 기록 저장, 게임오버 판정. 기능이 하나 늘 때마다 이 파일이 커지고, 모두가 이 파일을 참조합니다.

ScriptableObject(이하 SO)는 이 세 문제를 한 번에 풉니다. **프로젝트 에셋**이라서 프리팹이든 씬이든 누구나 참조할 수 있고, 데이터를 담는 그릇이 되며, 이벤트를 중계하는 "채널"이 될 수 있습니다.

## 개념

### ScriptableObject란

```
MonoBehaviour                              ScriptableObject
─────────────────────────────              ─────────────────────────────
GameObject에 붙는 컴포넌트                   .asset 파일로 Project 창에 존재
씬 안에 살고, 씬과 함께 생기고 사라짐           프로젝트에 살고, 씬이 바뀌어도 그대로
Transform, Update, OnTrigger... 있음         Update 없음, Transform 없음
프리팹 에셋은 씬 오브젝트를 참조 불가           프리팹·씬·다른 SO 누구나 참조 가능
JS 비유: 컴포넌트 인스턴스                     JS 비유: import해서 쓰는 설정 모듈 (싱글 인스턴스)
```

만드는 방법은 `ScriptableObject`를 상속하고 `[CreateAssetMenu]`를 붙이는 것뿐입니다.

```csharp
using UnityEngine;

[CreateAssetMenu(menuName = "Coin Rush/Data/Enemy", fileName = "EnemyData")]
public class EnemyData : ScriptableObject
{
    public int maxHp = 3;
}
```

Project 창 우클릭 → **Create → Coin Rush → Data → Enemy**로 에셋을 원하는 만큼 만들 수 있습니다. 코드로는 `ScriptableObject.CreateInstance<EnemyData>()`로 만들지만(`new EnemyData()`는 안 됩니다), 이렇게 만든 인스턴스는 에셋으로 저장되지 않습니다.

SO에도 생명주기 메시지가 있습니다. `Awake`/`OnEnable`은 에셋이 로드될 때, `OnDisable`은 언로드될 때, `OnValidate`는 에디터에서 값이 바뀔 때 호출됩니다. 에디터에서는 한 번 로드된 에셋이 플레이를 여러 번 반복해도 계속 로드된 상태일 수 있으므로 "플레이 시작마다 `OnEnable`이 온다"고 기대하면 안 됩니다.

### 주의 1 — 모두가 같은 인스턴스를 공유한다

가시 공 100개가 같은 `SpikeBall.asset`을 참조하면, 메모리에는 에셋 **하나**만 있고 100개가 그것을 가리킵니다. 그래서 메모리가 절약됩니다. 동시에 이런 버그가 생깁니다.

```csharp
public class BadHazard : MonoBehaviour
{
    [SerializeField] private EnemyData data;
    public void TakeDamage(int amount)
    {
        data.maxHp -= amount;   // ❌ 에셋의 값을 바꿈 → 가시 공 100개 전부 체력이 깎임
    }
}
```

규칙: **데이터 에셋은 읽기 전용으로 취급합니다.** 개별 오브젝트의 "지금 상태"(현재 체력)는 MonoBehaviour(`Health.Current`)에 복사해 두고 거기서 바꿉니다. 정말로 에셋 전체를 복제한 런타임 사본이 필요하면 `Instantiate(data)`로 사본을 만들 수 있지만, 대부분은 필요한 값만 복사하는 편이 명확합니다.

### 주의 2 — 에디터에서는 플레이 중 수정이 남는다

MonoBehaviour의 값은 Play를 멈추면 원래대로 돌아옵니다. **SO 에셋은 돌아오지 않습니다.** 에셋은 씬 밖의 파일이기 때문입니다.

```
에디터:  Play → 코드가 data.cooldown = 0.1f 실행 → Stop → 메모리에 로드된 에셋의 cooldown이 0.1 그대로
         (Inspector에서 Play 중에 조절한 값도 남음 — 밸런스 튜닝에는 오히려 편리)
빌드:    앱 실행 → data.cooldown = 0.1f → 앱 종료 → 다음 실행 시 원래 값
         (빌드된 에셋은 읽기 전용 스냅샷이라 파일에 쓰지 않음)
```

에디터에서 "값이 남는다"는 말은 세 가지를 구분해야 정확합니다.

| 단계 | Inspector로 수정 | 런타임 코드로 필드 대입 |
|---|---|---|
| 메모리에 남음 (Stop 후에도 Inspector에 0.1) | 예 | 예 |
| dirty(저장 필요) 표시 | 예 — Inspector가 자동으로 표시 | 아니요 — `EditorUtility.SetDirty`를 부르지 않는 한 표시되지 않음 |
| `.asset` 파일에 기록 (Git diff에 나타남) | **File → Save Project**(또는 씬 저장 등 에셋 저장 시점)에 기록 | 보장되지 않음 — 다른 이유로 같은 에셋이 저장될 때 함께 기록될 수도, 에디터를 재시작하면 사라질 수도 있음 |

에디터와 빌드의 동작이 달라지므로 "코드가 SO 데이터에 쓰는" 버그는 에디터에서만 재현되는 이상한 버그가 됩니다. 규칙은 주의 1과 같습니다 — **런타임 코드는 데이터 에셋에 쓰지 않는다.** 반면 Play 중 Inspector로 수치를 만지며 튜닝하는 것은 SO의 큰 장점으로 적극 활용합니다. 단, Inspector로 바꾼 값은 프로젝트를 저장하면 `.asset` 파일에 기록되어 Git diff에 나타나고 그대로 커밋될 수 있다는 사실은 알고 있어야 합니다. 코드로 바꾼 값은 저장 여부가 일정하지 않으니 "남아도 되고 안 남아도 되는" 값이 아니라 애초에 쓰지 말아야 할 값입니다.

이 교과서의 데이터 에셋은 초보자 부담을 줄이려고 `public` 필드를 씁니다. 팀 프로젝트라면 `[SerializeField] private` 필드 + 읽기 전용 프로퍼티로 컴파일러가 쓰기를 막게 하는 편이 안전합니다(연습 문제 1).

### 이벤트 채널 — 발행자와 구독자가 에셋 하나만 안다

로드맵에서 소개한 패턴입니다. SO 안에 C# 이벤트를 두면, 그 **에셋 자체가 전역 이벤트 버스의 한 채널**이 됩니다.

```
                    ┌──────────────────────────────┐
Coin (프리팹) ──Raise──▶│ CoinCollected.asset (IntEventChannel) │──OnRaised──▶ ScoreKeeper (씬)
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
ScoreKeeper ──Raise──▶│ ScoreChanged.asset (IntEventChannel)  │──OnRaised──▶ ScoreDisplay (UI)
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐        ├──▶ ScoreKeeper (최고 기록 저장)
Player Health ─Raise─▶│ GameOver.asset (VoidEventChannel)     │────────├──▶ FallingSpawner (멈춤)
                    └──────────────────────────────┘        └──▶ GameOverView (패널 표시)
```

- `Coin`은 `ScoreKeeper`를 모르고, `ScoreKeeper`는 `Coin`을 모릅니다. 둘 다 `CoinCollected.asset`만 압니다.
- 에셋이니까 **프리팹도 참조할 수 있습니다.** 런타임에 생성된 코인도 문제없이 발행합니다.
- 테스트할 때는 Inspector에서 채널을 직접 발행하는 버튼(연습 문제 3)으로 게임오버 UI만 따로 확인할 수 있습니다.

React로 비유하면 Context Provider 없이 쓰는 이벤트 버스인데, **이벤트 이름이 문자열이 아니라 에셋 참조**라서 오타가 불가능하고 "누가 이 채널을 쓰나"를 에디터에서 검색(에셋 우클릭 → Find References In Scene)할 수 있습니다.

단점도 있습니다. 채널은 "지나가는 사건"만 전달하므로, **늦게 구독한 쪽은 지난 값을 모릅니다.** 01장에서 `GameManager.Start`가 초기 점수를 한 번 발행했던 것처럼, 발행자가 초기값을 보내 주거나 채널이 마지막 값을 기억하게 해야 합니다(연습 문제 4). 또 흐름이 에디터 연결 속에 숨기 때문에 채널 에셋 이름을 `사건_과거형`(예: `CoinCollected`, `PlayerDied`)으로 일관되게 짓는 것이 중요합니다.

### 제네릭 베이스로 채널 종류 늘리기

`int`, `float`, `Vector2`, `EnemyData`... 채널 타입마다 같은 코드를 복사하지 않도록 01장의 제네릭을 씁니다. 단, Unity는 **제네릭 SO 자체를 에셋으로 만들 수 없으므로** 한 줄짜리 구체 클래스를 둡니다.

```csharp
public abstract class EventChannel<T> : ScriptableObject { ... }   // 로직은 여기 한 번

[CreateAssetMenu(menuName = "Coin Rush/Events/Int Event Channel")]
public class IntEventChannel : EventChannel<int> { }                 // 에셋용 구체 타입

[CreateAssetMenu(menuName = "Coin Rush/Events/Float Event Channel")]
public class FloatEventChannel : EventChannel<float> { }            // 필요할 때 한 줄 추가
```

Unity는 클래스 이름과 파일 이름이 같아야 SO·MonoBehaviour를 인식하므로 `IntEventChannel`은 `IntEventChannel.cs`에 따로 둡니다. Inspector 필드 타입도 `EventChannel<int>`가 아니라 `IntEventChannel`로 선언해야 에셋을 드래그하기 편합니다.

### 런타임 세트 — "지금 살아 있는 적 목록"

"화면의 모든 적"을 찾으려고 `FindObjectsByType<Enemy>()`를 부르면 02장에서 본 것처럼 매번 배열을 할당하고 느립니다. 대신 적이 **스스로 목록에 등록·해제**하게 합니다. 그 목록을 SO에 두면 누구나 참조할 수 있습니다.

```
HazardSetup.OnEnable  ──Add(health)──▶  ┌─────────────────────────┐
HazardSetup.OnDisable ──Remove───────▶  │ AliveEnemies.asset       │ ◀── 05장 자동 조준 무기가 읽음
                                        │ (HealthRuntimeSet)       │ ◀── 22장 웨이브 "남은 적 수"
                                        └─────────────────────────┘
```

등록과 해제를 `OnEnable`/`OnDisable`에서 하면, 파괴될 때와 12장 오브젝트 풀에서 비활성화될 때 모두 자동으로 빠집니다. Play를 멈추면 씬 오브젝트가 전부 파괴되며 `OnDisable`이 불리므로 세트도 비워집니다. 01장의 구독 규칙과 똑같은 원리입니다.

### 싱글턴 — 없앨 곳과 남길 곳

싱글턴이 나쁜 게 아니라 **남용**이 나쁩니다. 판단 기준은 다음과 같습니다.

| 질문 | 예라면 |
|---|---|
| 게임 규칙·상태인가? (점수, 체력, 웨이브) | 이벤트 채널·데이터 에셋·일반 컴포넌트로. 싱글턴 금지 |
| 여러 개가 있으면 논리적으로 틀린가? + 씬 전환에도 살아남아야 하나? + 플랫폼·엔진 자원을 감싸나? | 싱글턴이 적절 |

코인 러시에서 싱글턴으로 남길 후보는 `AudioManager`(12장 — 믹서와 소리 풀은 하나), `StoreService`/`AdService`(25장 — SDK 초기화는 한 번), `Analytics`(24장)처럼 **외부 자원을 감싸는 서비스**입니다. 이런 싱글턴은 최소한 아래처럼 중복을 막고 정리합니다.

```csharp
using UnityEngine;

public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);           // 이미 있으면 새로 생긴 쪽을 제거
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);     // 루트 오브젝트여야 동작
    }

    void OnDestroy()
    {
        if (Instance == this) Instance = null;
    }
}
```

STEP 4의 `Awake() => Instance = this;`와 비교해 보세요. 09장에서 부트스트랩 씬을 만들면 이런 서비스를 한곳에서 생성하게 됩니다.

## 실습: 코인 러시에 적용하기

이번 장이 끝나면 `GameManager`의 책임은 이렇게 나뉩니다.

| `GameManager`가 하던 일 | 이제 담당 |
|---|---|
| 점수 합산, `ScoreChanged` 발행 | `ScoreKeeper` + `CoinCollected`/`ScoreChanged` 채널 |
| 최고 기록 저장 | `ScoreKeeper` (`GameOver` 채널 구독) |
| 코인·가시 공 스폰 | `FallingSpawner` (가시 공 종류는 `EnemyData` 에셋) |
| 플레이어 사망 → 게임오버 | `HealthEventRelay` → `GameOver` 채널 |
| 플레이어 숨기기 | Player의 `VoidEventListener` |

### 1단계: 데이터 에셋 클래스

```csharp
// Assets/_CoinRush/Scripts/Data/EnemyData.cs
using UnityEngine;

[CreateAssetMenu(menuName = "Coin Rush/Data/Enemy", fileName = "EnemyData")]
public class EnemyData : ScriptableObject
{
    [Header("표시")]
    public string displayName = "적";

    [Header("전투")]
    [Min(1)] public int maxHp = 3;
    [Min(0)] public int contactDamage = 1;

    [Header("이동 (05장에서 사용)")]
    [Min(0f)] public float moveSpeed = 2f;

    [Header("보상")]
    [Min(0)] public int coinDrop = 1;

    [Header("생성")]
    public GameObject prefab;
}
```

```csharp
// Assets/_CoinRush/Scripts/Data/WeaponData.cs
using UnityEngine;

[CreateAssetMenu(menuName = "Coin Rush/Data/Weapon", fileName = "WeaponData")]
public class WeaponData : ScriptableObject
{
    public string displayName = "기본 탄";
    [Min(0)] public int damage = 1;
    [Min(0.02f)] public float cooldown = 0.5f;   // 초
    public Projectile projectilePrefab;          // 프리팹의 Projectile 컴포넌트를 직접 참조
    [Min(0f)] public float projectileSpeed = 12f;
}
```

`projectilePrefab`의 타입을 `GameObject`가 아니라 `Projectile`로 두면, `Projectile` 컴포넌트가 없는 프리팹은 애초에 드래그되지 않고 `Instantiate`가 `Projectile`을 바로 돌려줍니다. `EnemyData.prefab`은 적 클래스가 05장에서 생기므로 지금은 `GameObject`입니다.

### 2단계: 이벤트 채널

```csharp
// Assets/_CoinRush/Scripts/Events/VoidEventChannel.cs
using System;
using UnityEngine;

[CreateAssetMenu(menuName = "Coin Rush/Events/Void Event Channel", fileName = "VoidEventChannel")]
public class VoidEventChannel : ScriptableObject
{
    [SerializeField, TextArea] private string description;   // 무엇을 알리는 채널인지 메모
    public event Action OnRaised;
    public void Raise() => OnRaised?.Invoke();
}
```

```csharp
// Assets/_CoinRush/Scripts/Events/EventChannel.cs
using System;
using UnityEngine;

public abstract class EventChannel<T> : ScriptableObject
{
    [SerializeField, TextArea] private string description;
    public event Action<T> OnRaised;
    public void Raise(T value) => OnRaised?.Invoke(value);
}
```

```csharp
// Assets/_CoinRush/Scripts/Events/IntEventChannel.cs
using UnityEngine;

[CreateAssetMenu(menuName = "Coin Rush/Events/Int Event Channel", fileName = "IntEventChannel")]
public class IntEventChannel : EventChannel<int> { }
```

디자이너가 코드 없이 반응을 연결할 수 있도록 `UnityEvent` 기반 리스너도 하나 만듭니다.

```csharp
// Assets/_CoinRush/Scripts/Events/VoidEventListener.cs
using UnityEngine;
using UnityEngine.Events;

public class VoidEventListener : MonoBehaviour
{
    [SerializeField] private VoidEventChannel channel;
    [SerializeField] private UnityEvent response;
    void OnEnable() => channel.OnRaised += Respond;
    void OnDisable() => channel.OnRaised -= Respond;
    private void Respond() => response.Invoke();
}
```

### 3단계: 런타임 세트

```csharp
// Assets/_CoinRush/Scripts/Data/RuntimeSet.cs
using System.Collections.Generic;
using UnityEngine;

public abstract class RuntimeSet<T> : ScriptableObject
{
    private readonly List<T> items = new List<T>();   // private + 비직렬화 → 에셋 파일에 저장되지 않음
    public IReadOnlyList<T> Items => items;
    public int Count => items.Count;

    public void Add(T item)
    {
        if (!items.Contains(item)) items.Add(item);
    }

    public void Remove(T item) => items.Remove(item);
}
```

```csharp
// Assets/_CoinRush/Scripts/Data/HealthRuntimeSet.cs
using UnityEngine;

[CreateAssetMenu(menuName = "Coin Rush/Sets/Health Runtime Set", fileName = "HealthRuntimeSet")]
public class HealthRuntimeSet : RuntimeSet<Health> { }
```

`Items`를 `IReadOnlyList<T>`로 공개했으므로 읽는 쪽은 02장에서 배운 대로 `foreach` 대신 `for (int i = 0; i < set.Count; i++)`로 순회합니다. 적이 수백 마리가 되면 `Contains`/`Remove`의 선형 탐색이 부담될 수 있는데, 그때는 인덱스를 기억해 마지막 원소와 바꿔 지우는 방식으로 개선합니다(12장).

### 4단계: 점수와 게임오버 흐름

```csharp
// Assets/_CoinRush/Scripts/Core/ScoreKeeper.cs
using UnityEngine;

public class ScoreKeeper : MonoBehaviour
{
    private const string HighScoreKey = "highScore";

    [Header("구독")]
    [SerializeField] private IntEventChannel coinCollected;
    [SerializeField] private VoidEventChannel gameOver;

    [Header("발행")]
    [SerializeField] private IntEventChannel scoreChanged;
    public int Score { get; private set; }
    public int HighScore { get; private set; }
    private bool finished;
    void Awake() => HighScore = PlayerPrefs.GetInt(HighScoreKey, 0);

    void OnEnable()
    {
        coinCollected.OnRaised += AddScore;
        gameOver.OnRaised += Finish;
    }

    void OnDisable()
    {
        coinCollected.OnRaised -= AddScore;
        gameOver.OnRaised -= Finish;
    }

    void Start() => scoreChanged.Raise(Score);   // 초기값 알림

    private void AddScore(int amount)
    {
        if (finished) return;
        Score += amount;
        scoreChanged.Raise(Score);
    }

    private void Finish()
    {
        if (finished) return;
        finished = true;
        if (Score > HighScore)
        {
            HighScore = Score;
            PlayerPrefs.SetInt(HighScoreKey, HighScore);
            PlayerPrefs.Save();
        }
    }
}
```

채널은 씬 오브젝트가 아니라 에셋이므로, 01장과 달리 `OnDisable`에서 null 검사가 필요 없습니다. 에셋은 씬이 닫혀도 파괴되지 않습니다.

```csharp
// Assets/_CoinRush/Scripts/Combat/HealthEventRelay.cs
using UnityEngine;

// Health의 C# 이벤트를 채널로 내보내는 다리
[RequireComponent(typeof(Health))]
public class HealthEventRelay : MonoBehaviour
{
    [SerializeField] private VoidEventChannel died;
    private Health health;
    void Awake() => health = GetComponent<Health>();
    void OnEnable() => health.Died += died.Raise;
    void OnDisable() => health.Died -= died.Raise;
}
```

`died.Raise`처럼 **메서드 그룹**으로 구독했습니다. 같은 에셋의 같은 메서드이므로 `-=`로 정확히 해제됩니다. `Health`는 채널을 전혀 모르는 상태로 남습니다. 적의 `Health`에는 이 릴레이를 붙이지 않으면 됩니다.

### 5단계: Coin과 UI를 채널로

이 단계에서 `Coin.AnyCollected`를 지우면, 01장의 `GameManager.cs`(그리고 01장 연습 문제 3의 `CoinSfx.cs`를 만들었다면 그것도)가 이 이벤트를 참조하고 있어 **컴파일 에러**가 납니다. 컴파일 에러가 남아 있으면 Unity는 새 스크립트도 반영하지 않아 8단계의 Create 메뉴가 나타나지 않습니다. 그래서 이 단계에서 **이전 코드 제거와 참조 교체를 한 번에 끝내고**, Console 에러 0을 확인한 뒤 6단계로 넘어갑니다.

먼저 에디터에서 이전 컴포넌트를 치웁니다(스크립트 파일보다 컴포넌트를 먼저 제거해야 `Missing (Mono Script)`가 남지 않습니다).

1. Hierarchy의 `GameManager` 오브젝트 이름을 `GameSystems`로 바꾸고, Inspector에서 `GameManager` 컴포넌트를 **Remove Component** 합니다.
2. 01장 연습 문제 3의 `CoinSfx`를 씬에 붙였다면 그 컴포넌트도 제거합니다(채널 버전은 아래 참고).
3. Project 창에서 `GameManager.cs`(와 `CoinSfx.cs`)를 삭제합니다.

이제 코드를 고칩니다. `Coin.cs`에서 static 이벤트를 채널로 바꿉니다. 02장에서 추가한 `body`, `Awake`, `Attract`는 그대로 두고, 다음 부분만 교체합니다.

```csharp
// Coin.cs — 삭제: public static event Action<int> AnyCollected; 와 ResetStatics 메서드, using System;
// Coin.cs — 추가할 필드
[SerializeField] private IntEventChannel collected;

// Coin.cs — TryCollect 교체
protected override bool TryCollect(GameObject collector)
{
    collected.Raise(value);
    return true;
}
```

```csharp
// ScoreDisplay.cs — 필드 교체: GameManager gameManager → IntEventChannel scoreChanged
[SerializeField] private IntEventChannel scoreChanged;

// ScoreDisplay.cs — OnEnable/OnDisable 교체 (Show는 02장 그대로)
void OnEnable() => scoreChanged.OnRaised += Show;
void OnDisable() => scoreChanged.OnRaised -= Show;
```

```csharp
// Assets/_CoinRush/Scripts/UI/GameOverView.cs  (전체 교체)
using TMPro;
using UnityEngine;

public class GameOverView : MonoBehaviour
{
    [SerializeField] private VoidEventChannel gameOver;
    [SerializeField] private ScoreKeeper scoreKeeper;          // 같은 씬이므로 직접 참조해도 된다
    [SerializeField] private GameObject panel;
    [SerializeField] private TextMeshProUGUI highScoreLabel;
    void Awake() => panel.SetActive(false);
    void OnEnable() => gameOver.OnRaised += Show;
    void OnDisable() => gameOver.OnRaised -= Show;

    private void Show()
    {
        panel.SetActive(true);
        // ScoreKeeper.Finish가 아직 안 불렸을 수도 있으므로 둘 중 큰 값을 표시 (흔한 실수 3)
        highScoreLabel.SetText("최고 기록 {0}", Mathf.Max(scoreKeeper.Score, scoreKeeper.HighScore));
    }
}
```

`CoinSfx`를 계속 쓰고 싶다면 `Coin.AnyCollected` 구독을 `[SerializeField] private IntEventChannel coinCollected;` 필드와 `coinCollected.OnRaised += Play;` / `-= Play;`로 바꿔 다시 만들면 됩니다. `Play(int value)`의 모양은 그대로입니다.

여기까지 저장한 뒤 Unity로 돌아와 **Console의 컴파일 에러가 0개**인지 확인합니다. 에러가 남아 있다면 메시지에 나온 파일이 아직 `GameManager`나 `Coin.AnyCollected`를 참조하는 곳입니다. (씬의 `GameSystems`는 지금 아무 일도 하지 않으므로 이 상태에서 Play하면 코인이 떨어지지 않는 것이 정상입니다. 8단계에서 새 컴포넌트를 붙입니다.)

`GameOverView`가 `ScoreKeeper`를 직접 참조한 것에 주목하세요. **같은 씬 안에서 수명이 같은 오브젝트끼리는 직접 참조가 가장 단순합니다.** 채널은 "서로 모르는 게 이득인 곳"(프리팹 ↔ 씬, 게임 규칙 ↔ UI, 씬 ↔ 씬)에 씁니다. 모든 연결을 채널로 만들면 흐름을 따라가기 어려워집니다. `Show`에서 `Mathf.Max`를 쓴 이유는 같은 채널의 구독자 실행 순서에 기대지 않기 위해서입니다(흔한 실수 3).

### 6단계: 무기와 투사체

```csharp
// Assets/_CoinRush/Scripts/Weapons/Projectile.cs
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public class Projectile : MonoBehaviour
{
    [SerializeField] private LayerMask targetLayers;
    [SerializeField] private float lifetime = 3f;
    private Rigidbody2D body;
    private int damage;
    private bool consumed;               // 이미 누군가를 맞혔는가
    void Awake() => body = GetComponent<Rigidbody2D>();

    public void Launch(Vector2 direction, float speed, int damageAmount)
    {
        damage = damageAmount;
        consumed = false;
        body.linearVelocity = direction.normalized * speed;
        Destroy(gameObject, lifetime);   // 아무것도 못 맞추면 수명이 다해 사라짐
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (consumed) return;            // 파괴 대기 중에 들어온 두 번째 접촉 무시
        if (!targetLayers.Contains(other.gameObject.layer)) return;
        if (!other.TryGetComponent(out IDamageable target)) return;
        consumed = true;
        target.TakeDamage(damage);
        Destroy(gameObject);
    }
}
```

`Destroy`는 즉시 지우지 않고 **현재 프레임의 끝**에 지웁니다. 그래서 겹쳐 있는 적 두 마리와 같은 물리 스텝에 닿으면, `consumed` 플래그가 없을 때는 파괴를 기다리는 탄이 두 번 피해를 줍니다. 한 발은 한 번만 맞혀야 하므로 첫 적중에서 플래그를 세웁니다(관통탄은 연습 문제 5에서 이 규칙을 의도적으로 바꿉니다).

```csharp
// Assets/_CoinRush/Scripts/Weapons/AutoShooter.cs
using UnityEngine;

// 03장 임시 무기: 정해진 방향으로 쿨다운마다 발사 (05장에서 자동 조준 무기로 교체)
public class AutoShooter : MonoBehaviour
{
    [SerializeField] private WeaponData weapon;
    [SerializeField] private Vector2 direction = Vector2.up;
    private float cooldownLeft;

    void Update()
    {
        cooldownLeft -= Time.deltaTime;
        if (cooldownLeft > 0f) return;
        cooldownLeft = weapon.cooldown;   // 에셋에서 읽기만 한다
        Projectile shot = Instantiate(weapon.projectilePrefab, transform.position, Quaternion.identity);
        shot.Launch(direction, weapon.projectileSpeed, weapon.damage);
    }
}
```

### 7단계: 데이터를 읽는 가시 공과 스포너

```csharp
// Assets/_CoinRush/Scripts/Enemies/HazardSetup.cs
using UnityEngine;

// EnemyData를 가시 공에 적용하고, 살아 있는 적 목록에 등록하고, 죽으면 코인을 떨군다
// (05장에서 Enemy 컴포넌트로 발전)
[RequireComponent(typeof(Health), typeof(DamageOnTouch))]
public class HazardSetup : MonoBehaviour
{
    [SerializeField] private EnemyData data;
    [SerializeField] private HealthRuntimeSet aliveEnemies;
    [SerializeField] private Coin coinPrefab;
    private Health health;
    private DamageOnTouch contact;
    public EnemyData Data => data;

    void Awake()
    {
        health = GetComponent<Health>();
        contact = GetComponent<DamageOnTouch>();
        if (data != null) Apply(data);
    }

    void OnEnable()
    {
        aliveEnemies.Add(health);
        health.Died += HandleDied;
    }

    void OnDisable()
    {
        aliveEnemies.Remove(health);
        health.Died -= HandleDied;
    }

    // 스포너가 생성 직후 호출. 데이터는 "복사해서" 컴포넌트 상태로 옮긴다
    public void Apply(EnemyData newData)
    {
        data = newData;
        health.Initialize(data.maxHp);
        contact.Damage = data.contactDamage;
    }

    private void HandleDied()
    {
        for (int i = 0; i < data.coinDrop; i++)
        {
            Vector2 offset = Random.insideUnitCircle * 0.4f;
            Instantiate(coinPrefab, (Vector2)transform.position + offset, Quaternion.identity);
        }
        Destroy(gameObject);
    }
}
```

```csharp
// Assets/_CoinRush/Scripts/Core/FallingSpawner.cs
using UnityEngine;

public class FallingSpawner : MonoBehaviour
{
    [SerializeField] private Coin coinPrefab;
    [SerializeField] private EnemyData[] hazardTypes;
    [SerializeField] private VoidEventChannel gameOver;
    [SerializeField] private float coinInterval = 1f;
    [SerializeField] private float hazardInterval = 2.5f;
    [SerializeField] private float spawnY = 6f;
    [SerializeField] private float spawnHalfWidth = 8f;
    private float coinTimer;
    private float hazardTimer;
    void OnEnable() => gameOver.OnRaised += Stop;
    void OnDisable() => gameOver.OnRaised -= Stop;

    void Update()
    {
        if (Tick(ref coinTimer, coinInterval))
            Instantiate(coinPrefab, RandomTopPosition(), Quaternion.identity);
        if (Tick(ref hazardTimer, hazardInterval))
        {
            EnemyData type = hazardTypes.PickRandom();          // 01장 확장 메서드
            GameObject go = Instantiate(type.prefab, RandomTopPosition(), Quaternion.identity);
            if (go.TryGetComponent(out HazardSetup setup)) setup.Apply(type);
        }
    }

    private bool Tick(ref float timer, float interval)
    {
        timer += Time.deltaTime;
        if (timer < interval) return false;
        timer -= interval;
        return true;
    }

    private Vector3 RandomTopPosition()
        => new Vector3(Random.Range(-spawnHalfWidth, spawnHalfWidth), spawnY, 0f);
    private void Stop() => enabled = false;   // 비활성화 → OnDisable에서 구독도 해제됨
}
```

### 8단계: 에셋 만들고 씬 조립하기

1. `Assets/_CoinRush/Data/`와 `Assets/_CoinRush/Events/` 폴더를 만듭니다.
2. **Events** 폴더에서 Create → Coin Rush → Events로 다음 에셋을 만들고 description을 채웁니다.
   - `CoinCollected` (Int) — "코인을 먹음. 값 = 코인 가치"
   - `ScoreChanged` (Int) — "점수가 바뀜. 값 = 현재 점수"
   - `GameOver` (Void) — "플레이어 사망으로 판이 끝남"
3. **Data** 폴더에서 `AliveEnemies` (Health Runtime Set)를 만듭니다.
4. **Projectile 프리팹**: Circle 스프라이트(Scale 0.2, 노랑) + `Circle Collider 2D`(Is Trigger) + `Rigidbody2D`(Body Type **Kinematic**) + `Projectile`(Target Layers `Enemy`). 프리팹으로 저장.
5. **Hazard 프리팹** 수정: `HazardSetup` 추가(Data는 비워 둠, Alive Enemies = `AliveEnemies`, Coin Prefab = Coin). `DamageOnTouch`의 Damage 값은 이제 데이터가 덮어씁니다. 체력 확인을 위해 01장 연습 문제 4의 `HitFlash`를 만들었다면 여기 붙입니다.
6. Hazard 프리팹을 복제해 `HeavyHazard`(Scale 1.2, 진한 빨강)를 만듭니다.
7. **Data** 폴더에 에셋을 만듭니다.

| 에셋 | displayName | maxHp | contactDamage | moveSpeed | coinDrop | prefab |
|---|---|---|---|---|---|---|
| `SpikeBall` (Enemy) | 가시 공 | 2 | 1 | 1.5 | 2 | Hazard |
| `HeavyBall` (Enemy) | 무거운 가시 공 | 6 | 2 | 1 | 5 | HeavyHazard |

| 에셋 | displayName | damage | cooldown | projectilePrefab | projectileSpeed |
|---|---|---|---|---|---|
| `BasicShot` (Weapon) | 기본 탄 | 1 | 0.4 | Projectile | 12 |

8. **Coin 프리팹**: `Coin`의 Collected = `CoinCollected`.
9. **Player**: `HealthEventRelay`(Died = `GameOver`), `AutoShooter`(Weapon = `BasicShot`), `VoidEventListener`(Channel = `GameOver`, Response에 Player 오브젝트를 드래그하고 `GameObject.SetActive` 선택, 체크 해제 상태).
10. 5단계에서 이름을 바꾼 `GameSystems` 오브젝트에 `ScoreKeeper`, `FallingSpawner`를 붙여 채널과 에셋을 연결합니다. Hazard Types에는 `SpikeBall`, `HeavyBall`을 넣습니다.
11. `ScoreText`의 `ScoreDisplay` → Score Changed = `ScoreChanged`. Canvas의 `GameOverView` → 채널·ScoreKeeper·패널 연결, GameOverPanel 안에 `HighScoreText`를 만들어 연결합니다.
12. Console에 에러가 없는지, 그리고 씬의 어떤 오브젝트에도 `Missing (Mono Script)` 컴포넌트가 남지 않았는지 확인합니다. 남아 있다면 5단계에서 컴포넌트를 제거하기 전에 스크립트를 먼저 지운 것이니 해당 컴포넌트를 Remove Component 합니다.

### 확인하기

- ▶ Play하면 플레이어가 위로 노란 탄을 자동 발사한다.
- 가시 공이 탄에 2발, 무거운 공이 6발 맞으면 부서지고 코인 2개 / 5개가 떨어진다. 떨어진 코인을 먹으면 점수가 오른다(런타임 생성 프리팹이 채널로 발행 성공).
- Play 중에 `BasicShot` 에셋의 cooldown을 0.1로 바꾸면 즉시 연사가 빨라진다. **Stop 후에도 0.1이 남아 있는 것**을 확인하고 0.4로 되돌린다.
- HP가 0이 되면 플레이어가 사라지고, 스폰이 멈추고, 게임오버 패널에 최고 기록이 표시된다.
- Project 창에서 `GameOver` 에셋 우클릭 → **Find References In Scene**으로 구독·발행하는 오브젝트들이 선택되는지 확인한다.
- 프로젝트 전체에서 `Instance` 검색 결과가 0이다.

## 흔한 실수

1. **Stop 후에 적 데이터 값이 이상하게 바뀌어 있다**
   원인: 런타임 코드가 `data.maxHp -= ...`처럼 에셋에 썼거나, Play 중 Inspector로 조절한 값이 남았습니다.
   해결: 런타임 상태는 `Health` 같은 컴포넌트로 복사해서 다룹니다. 튜닝 후에는 Git diff로 에셋 변경을 확인하고 의도한 것만 커밋합니다.
2. **두 번째 Play부터 채널 발행 시 `MissingReferenceException`**
   원인: 채널(에셋)은 Play가 끝나도 살아 있는데, 구독자가 `OnDisable`에서 해제하지 않았습니다. 특히 도메인 리로드를 끈 설정에서 두드러집니다.
   해결: 모든 `OnRaised +=`에 `OnDisable`의 `-=` 짝을 맞춥니다.
3. **게임오버 패널의 최고 기록이 방금 세운 기록보다 낮게 나온다**
   원인: 같은 채널의 구독자 호출 순서는 구독 순서(= `OnEnable` 순서)에 따르는데, 이 순서에 기대면 안 됩니다. `GameOverView.Show`가 `ScoreKeeper.Finish`보다 먼저 실행됐습니다.
   해결: 이 장의 코드처럼 순서와 무관한 값(`Mathf.Max(Score, HighScore)`)을 쓰거나, 순서가 중요한 처리는 단계를 나눕니다. 예: `ScoreKeeper.Finish`가 저장을 마친 뒤 `RunFinished` 채널을 발행하고 UI는 그것을 구독합니다.
4. **Create 메뉴에 에셋 항목이 안 보인다**
   원인: 컴파일 에러가 남아 있거나, 파일 이름과 클래스 이름이 다르거나, 제네릭 추상 클래스에 `CreateAssetMenu`를 붙였습니다.
   해결: Console의 에러를 먼저 없애고, 구체 클래스(`IntEventChannel`)에 특성을 붙였는지 확인합니다.
5. **프리팹의 채널 필드에 에셋이 비어 있어 `NullReferenceException`**
   원인: 씬의 인스턴스에만 연결하고 프리팹 원본에는 연결하지 않아 런타임 생성본은 비어 있습니다.
   해결: 채널 연결은 **프리팹 모드**에서 원본에 합니다. `OnValidate`에서 `if (collected == null) Debug.LogWarning(...)`으로 누락을 경고하게 해 두면 좋습니다.

## 연습 문제

**1. ★☆☆ 데이터 에셋을 컴파일러가 보호하게 하기**
`WeaponData`의 필드를 외부에서 읽기만 가능하게 바꾸세요. 기존 에셋에 입력한 값이 사라지면 안 됩니다.

<details><summary>힌트·해설</summary>

필드 이름을 그대로 두고 `private`으로 바꾸면 직렬화 이름이 같아서 값이 유지됩니다.

```csharp
[SerializeField, Min(0)] private int damage = 1;
public int Damage => damage;
```

사용하는 쪽은 `weapon.damage` → `weapon.Damage`로 바꿉니다. 필드 이름 자체를 바꿔야 한다면 `[FormerlySerializedAs("damage")]`(`UnityEngine.Serialization`)를 붙여 기존 값을 이어받습니다.
</details>

**2. ★☆☆ 적이 부서질 때 효과음 채널**
적이 죽을 때 소리를 내고 싶습니다. `HazardSetup`에 어떤 채널을 추가하고 누가 구독하면 될까요? 코드로 작성하세요.

<details><summary>힌트·해설</summary>

`HazardSetup`에 `[SerializeField] private VoidEventChannel enemyKilled;`를 추가하고 `HandleDied`에서 `enemyKilled.Raise();`를 호출합니다. 씬의 `EnemyKillSfx` 컴포넌트가 `OnEnable`에서 구독해 `AudioSource.PlayOneShot`을 호출합니다. 적 프리팹이 씬의 오디오 오브젝트를 모르는데도 연결된다는 점이 핵심입니다. 적 종류별로 다른 소리를 내려면 `EnemyData`를 인자로 넘기는 `EnemyDataEventChannel : EventChannel<EnemyData>`를 만들면 됩니다.
</details>

**3. ★★☆ Inspector에서 채널 발행 버튼**
Play 중에 `GameOver` 에셋을 선택하고 버튼을 눌러 게임오버 UI만 테스트하고 싶습니다. `VoidEventChannel` 전용 커스텀 에디터를 만드세요.

<details><summary>힌트·해설</summary>

에디터 전용 코드는 `Editor` 폴더에 둡니다.

```csharp
// Assets/_CoinRush/Scripts/Editor/VoidEventChannelEditor.cs
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(VoidEventChannel))]
public class VoidEventChannelEditor : Editor
{
    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();
        GUI.enabled = Application.isPlaying;
        if (GUILayout.Button("Raise")) ((VoidEventChannel)target).Raise();
        GUI.enabled = true;
    }
}
```

20장에서 에디터 확장을 본격적으로 다룹니다.
</details>

**4. ★★☆ 마지막 값을 기억하는 채널**
`ScoreDisplay`를 게임 도중에 켜도 현재 점수가 바로 보이도록, 마지막으로 발행된 값을 기억했다가 구독 즉시 받을 수 있는 방법을 `EventChannel<T>`에 추가하세요.

<details><summary>힌트·해설</summary>

`EventChannel<T>`에 `public T LastValue { get; private set; }`와 `public bool HasValue { get; private set; }`를 두고 `Raise`에서 갱신합니다. 구독자는 `OnEnable`에서 `if (channel.HasValue) Show(channel.LastValue);`를 호출합니다.
주의: SO는 에디터에서 Play를 멈춰도 살아 있으므로 `LastValue`가 **다음 플레이까지 남습니다**. 게임 시작 시점(예: `ScoreKeeper.Awake`)에 초기화 메서드를 호출하거나, 필드에 `[System.NonSerialized]`를 붙이고 시작 시 리셋하세요. 이 "남는 상태"가 SO를 상태 저장소로 쓸 때의 대표적 함정입니다.
</details>

**5. ★★★ 무기 3종과 데이터 주도 업그레이드 (스스로 확장)**
`WeaponData`로 기본 탄 / 산탄(3발, 부채꼴) / 관통탄(적을 뚫고 지나감) 세 가지를 만들어 보세요. 조건: 무기 종류가 늘어도 `AutoShooter`에 `if (weapon.displayName == ...)` 같은 분기가 생기면 안 됩니다.

<details><summary>힌트·해설</summary>

- 산탄: `WeaponData`에 `projectileCount`, `spreadAngle`을 추가하고, 발사 방향을 `Quaternion.Euler(0, 0, 각도) * direction`으로 돌립니다(06장에서 회전을 자세히 다룹니다).
- 관통: `Projectile`에 `pierceCount`를 넣고 0이 될 때까지 파괴하지 않습니다. 이 값은 `Launch`의 인자로 전달합니다. `consumed`는 남은 관통 횟수가 0이 되어 `Destroy`를 부를 때만 세우고, 같은 적을 연속으로 두 번 맞히지 않도록 마지막으로 맞힌 콜라이더를 기억해 건너뜁니다.
- 더 큰 차이(레이저, 궤도 무기)가 생기면 데이터만으로 표현이 어렵습니다. 그때는 `WeaponData`를 추상 SO로 만들고 `public abstract void Fire(Transform origin, Vector2 dir)`를 자식 SO가 구현하는 **전략 패턴 SO**로 발전시킵니다. 단, SO의 `Fire` 안에서 쿨다운 같은 런타임 상태를 저장하면 주의 1의 공유 문제가 다시 생깁니다.
</details>

## 셀프 체크

**1. 코인 프리팹이 씬의 `ScoreKeeper`를 Inspector로 참조할 수 없는 이유와, 채널 에셋이 이를 해결하는 원리를 설명해 보세요.**

<details><summary>모범 답안</summary>

프리팹은 프로젝트 에셋이고 씬 오브젝트는 특정 씬 안에만 존재하므로, 에셋이 씬 오브젝트를 직렬화된 참조로 가질 수 없습니다. 채널은 SO 에셋이라 프리팹과 씬 오브젝트 모두 참조할 수 있습니다. 코인은 채널에 발행하고 `ScoreKeeper`는 같은 채널을 구독하므로, 서로 몰라도 연결됩니다.
</details>

**2. 적 100마리가 같은 `EnemyData` 에셋을 참조할 때 생기는 장점과 위험을 각각 설명해 보세요.**

<details><summary>모범 답안</summary>

장점: 데이터가 메모리에 한 벌만 있고, 에셋 하나만 고치면 모든 적에 반영되어 밸런싱이 쉽습니다. 위험: 한 적이 런타임에 에셋 값을 바꾸면 모든 적이 영향을 받고, 에디터에서는 그 변경이 Play 종료 후에도 에셋에 남습니다. 그래서 에셋은 읽기 전용으로 쓰고 개별 상태는 컴포넌트에 복사합니다.
</details>

**3. 모든 연결을 이벤트 채널로 만들지 않는 이유는 무엇인가요?**

<details><summary>모범 답안</summary>

채널은 흐름을 에디터 연결 속에 숨기기 때문에, 코드만 읽어서는 누가 발행하고 누가 받는지 따라가기 어렵습니다. 또 구독자 호출 순서에 의존하는 버그가 생기기 쉽습니다. 같은 씬에서 수명이 같은 오브젝트끼리는 직접 참조가 더 단순하고, 채널은 프리팹↔씬, 게임 규칙↔UI처럼 서로 모르는 게 이득인 경계에 씁니다.
</details>

**4. 런타임 세트에서 등록·해제를 `OnEnable`/`OnDisable`에서 하는 이유는?**

<details><summary>모범 답안</summary>

`OnDisable`은 파괴 직전과 비활성화 시 모두 호출되므로 목록에 파괴된 오브젝트가 남지 않습니다. 오브젝트 풀처럼 껐다 켜는 경우에도 꺼진 동안 목록에서 빠지고 켜지면 다시 들어갑니다. 에셋인 세트는 Play가 끝나도 살아 있지만, Play 종료 시 씬 오브젝트가 파괴되며 모두 스스로 빠지므로 다음 플레이에 찌꺼기가 남지 않습니다.
</details>

**5. 코인 러시에서 싱글턴으로 남겨도 되는 것과 안 되는 것의 예를 들어 기준을 설명해 보세요.**

<details><summary>모범 답안</summary>

점수·체력·웨이브 같은 게임 규칙과 상태는 싱글턴으로 두면 모두가 직접 의존해 결합이 커지므로 채널·데이터 에셋·일반 컴포넌트로 둡니다. `AudioManager`, `StoreService`처럼 하나만 있어야 논리적으로 맞고, 씬 전환에도 살아남아야 하고, 엔진·플랫폼 자원을 감싸는 서비스는 싱글턴이 적절합니다. 이때도 중복 생성 방지와 `OnDestroy` 정리를 해야 합니다.
</details>

## 핵심 요약

- ScriptableObject는 씬 밖에 사는 데이터 에셋으로, 프리팹·씬 누구나 참조할 수 있습니다.
- 데이터 에셋은 모두가 공유하므로 **런타임에 쓰지 않습니다.** 개별 상태는 컴포넌트에 복사합니다.
- 에디터에서는 Play 중 SO 수정이 남고, 빌드에서는 남지 않습니다. 튜닝엔 장점, 코드 쓰기엔 함정입니다.
- 이벤트 채널은 발행자와 구독자가 에셋 하나만 알게 해, 프리팹↔씬·규칙↔UI를 분리합니다.
- 제네릭 베이스 `EventChannel<T>` + 한 줄짜리 구체 클래스로 채널 종류를 늘립니다.
- 런타임 세트는 `OnEnable`/`OnDisable` 자가 등록으로 `Find` 계열 호출을 대체합니다.
- 게임 상태 싱글턴은 없애고, 외부 자원을 감싸는 서비스만 올바른 형태의 싱글턴으로 남깁니다.
- 코인 러시는 이제 `GameManager` 없이 `ScoreKeeper`·`FallingSpawner`·채널 3개·데이터 에셋으로 돌아갑니다.

## 더 읽을거리

- Unity Manual, "ScriptableObject" — https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity 전자책, "Create modular game architecture in Unity with ScriptableObjects" (Unity 공식 무료 배포)
- Unity 공식 샘플 프로젝트 "Open Project 1 (Chop Chop)" — SO 이벤트 채널 구조의 실제 사례 (GitHub `UnityTechnologies/open-project-1`)
- Ryan Hipple, "Game Architecture with Scriptable Objects" (Unite Austin 2017 강연) — SO 변수·이벤트·런타임 세트 패턴의 원조
