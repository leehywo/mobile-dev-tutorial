# 02. 메모리와 GC — 프레임 드랍 없는 코드

> **이 장에서 배울 것**
> - 값 타입과 참조 타입, 스택과 힙의 차이를 설명하고 박싱이 일어나는 코드를 찾아낼 수 있다
> - GC가 프레임 시간에 어떤 식으로 끼어드는지 설명할 수 있다
> - 매 프레임 할당을 만드는 흔한 코드 패턴을 알아보고 할당 없는 코드로 바꾼다
> - Profiler의 GC Alloc 열로 할당 위치를 찾아낸다
> - `Physics2D.OverlapCircle`의 `ContactFilter2D` + `List` 오버로드로 할당 없는 물리 조회를 구현한다
>
> **선수 장**: 01 · **예상 시간**: 3시간 · **코인 러시 진행**: 점수·체력 UI가 할당 없이 갱신되고, 주변 코인을 빨아들이는 자석(`CoinMagnet`)이 생깁니다. 매 프레임 GC 할당 0을 확인하는 모니터가 화면에 붙습니다.

## 왜 필요한가

서바이버라이크는 "화면에 수백 개가 동시에 움직이는" 장르입니다. 적 300마리, 코인 200개, 투사체 100개가 매 프레임 무언가를 합니다. 이때 오브젝트 하나가 프레임마다 **단 몇십 바이트**만 새로 할당해도 곱하기 600이 됩니다.

할당된 메모리는 결국 **가비지 컬렉터(GC)**가 치웁니다. 문제는 GC가 일하는 동안 게임 코드가 멈춘다는 것입니다.

```
60fps 목표 = 프레임당 16.6ms 예산

프레임:  |--9ms--|--9ms--|--9ms--|------9ms + GC 25ms------|--9ms--|
                                 ↑ 이 프레임만 34ms → 화면이 "툭" 끊김 (스파이크)
평균 fps는 여전히 58 → "평균은 괜찮은데 왜 버벅이지?"의 정체
```

GC 한 번에 걸리는 시간은 힙 크기와 기기 성능에 따라 수 ms에서 수십 ms까지 다양합니다. 데스크톱에서는 안 보이던 끊김이 저가 안드로이드 폰에서는 또렷하게 보입니다. 01장에서 이벤트 기반으로 바꾼 `ScoreDisplay`조차 아직 문자열을 새로 만들고 있고, 이번 장에서 만들 코인 자석을 "평범하게" 짜면 물리 스텝마다 수 KB를 할당합니다. 직접 측정하고 고쳐 봅시다.

JS와 비교하면, V8도 GC가 있지만 세대별(generational) GC라 짧게 사는 객체를 싸게 치웁니다. **Unity의 GC(Boehm)는 세대 구분이 없어서** 짧게 사는 작은 객체도 전체 힙을 훑는 비용을 발생시킵니다. 웹에서 "그 정도 할당은 괜찮다"던 감각을 그대로 가져오면 안 되는 이유입니다.

## 개념

### 값 타입과 참조 타입

| | 값 타입 (`struct`) | 참조 타입 (`class`) |
|---|---|---|
| 예 | `int`, `float`, `bool`, `Vector2`, `Vector3`, `Quaternion`, `Color`, `enum`, `ContactFilter2D` | `string`, 배열, `List<T>`, 모든 `MonoBehaviour`, 델리게이트, 람다 클로저 |
| 대입하면 | 값 전체가 **복사** | 같은 객체를 가리키는 **참조가 복사** |
| 새로 만들면 | GC 대상 아님 (지역 변수라면) | 힙에 할당 → 언젠가 GC가 치움 |
| null | 불가 (`int?`는 별도) | 가능 |
| JS 대응 | `number`, `boolean` 같은 원시값 | 객체·배열 |

`new Vector2(1, 2)`는 `new`가 붙어 있어도 **힙 할당이 아닙니다.** `struct`의 `new`는 값을 초기화할 뿐입니다. 반대로 `new List<int>()`는 힙 할당입니다. "new가 보이면 할당"이 아니라 **"class를 new 하면 할당"**입니다.

값 복사 때문에 생기는 유명한 컴파일 에러도 여기서 이해됩니다.

```csharp
transform.position.x = 5f;     // ❌ CS1612: position은 Vector3 "복사본"을 돌려주는 프로퍼티
                               //    복사본의 x를 바꿔봤자 의미가 없으니 컴파일러가 막는다
Vector3 p = transform.position;
p.x = 5f;
transform.position = p;        // ✅ 복사 → 수정 → 다시 대입
```

### 스택과 힙 (단순화한 그림)

```
스택 (메서드 호출마다 쌓였다 빠짐, GC 무관)      힙 (GC가 관리)
┌───────────────────────────┐                 ┌──────────────────────────┐
│ FixedUpdate()              │                 │ List<Collider2D> 객체     │◀─┐
│   Vector2 center  (값)     │                 │ string "점수: 12"          │  │
│   int count       (값)     │                 │ 람다 클로저 객체            │  │
│   List<Collider2D> hits ───┼─── 참조 ───────▶│ ...                       │  │
└───────────────────────────┘                 └──────────────────────────┘  │
메서드가 끝나면 즉시 사라짐                        참조가 모두 끊겨도 GC가 돌 때까지 남음
```

실제 CLR은 이보다 복잡하지만(값 타입도 클래스 필드라면 힙에 삽니다) "**참조 타입 인스턴스를 만들면 GC가 치워야 할 일이 늘어난다**"는 결론만 잡으면 충분합니다.

### 박싱 — 값 타입이 몰래 힙으로 가는 순간

값 타입을 `object`나 인터페이스 타입으로 다루면 C#은 힙에 상자(box)를 하나 만들어 값을 복사해 넣습니다.

```csharp
int score = 12;
object o = score;                          // 박싱: 힙 할당
Debug.Log(score);                          // Debug.Log(object) → 박싱 (+ 로그 문자열 할당)
string s = string.Format("{0}", score);    // Format(string, object) → 박싱 + 문자열
string t = $"점수: {score}";               // Unity의 C# 9에서는 위와 같은 코드로 컴파일 → 박싱 + 문자열

IComparable c = 3.5f;                      // 구조체를 인터페이스 변수에 담기 → 박싱
```

박싱은 코드에 `new`가 전혀 없어서 눈으로 찾기 어렵습니다. 그래서 프로파일러가 필요합니다.

### Unity의 GC는 어떻게 일하나

- Unity(Mono와 IL2CPP 모두)는 **Boehm GC**를 씁니다. **세대 구분이 없고(non-generational), 메모리를 압축하지 않습니다(non-compacting).**
- 할당 요청 시 힙에 빈 공간이 부족하면 GC가 돕니다. 살아 있는 객체를 표시(mark)하고 나머지를 회수(sweep)합니다.
- 압축하지 않으므로 오래 플레이하면 힙이 조각나고, 큰 배열을 할당할 자리가 없어 힙이 커지기도 합니다.

**Incremental GC**는 표시 작업을 여러 프레임에 나눠 한 프레임의 정지 시간을 줄입니다. Unity 6 신규 프로젝트에서는 **Project Settings → Player → Other Settings → Use incremental GC**가 기본으로 켜져 있습니다.

```
Incremental 끔:  |--9--|--9--|--9 + GC 25--|--9--|        한 프레임에 몰아서
Incremental 켬:  |--9+3--|--9+3--|--9+3--|--9+3--|        여러 프레임에 나눠서
```

주의할 점은 **총 비용은 줄지 않는다**는 것입니다. 할당 자체를 줄이는 것이 근본 해결이고, Incremental GC는 남은 할당의 충격을 완화하는 안전망입니다. 할당 속도가 GC의 분할 처리 속도를 넘어서면 결국 한 번에 몰아서 수집합니다. 로딩 화면처럼 끊김이 안 보이는 순간에는 `System.GC.Collect()`를 직접 호출해 미리 치워 두는 전략도 씁니다.

### 할당을 만드는 흔한 코드

| 코드 | 무엇이 할당되나 | 대안 |
|---|---|---|
| `$"점수: {score}"` | 새 `string` + 박싱(Unity의 C# 9에서는 `string.Format(string, object)`로 컴파일) | TMP의 `label.SetText("점수: {0}", score)`, 값이 바뀔 때만 갱신 |
| `list.Where(...).ToList()`, `OrderBy`, `Any(x => ...)` | 이터레이터 객체, 클로저, 결과 리스트 | `for` 루프 + 미리 만든 리스트 재사용 |
| `x => x.hp < threshold` (지역 변수 캡처) | 호출할 때마다 클로저 객체 + 델리게이트 | 캡처 없는 람다(컴파일러가 캐시), 또는 필드에 델리게이트 저장 |
| `x => x.hp < maxHp` (필드·`this`만 사용) | 클로저 객체는 없지만, 인스턴스 메서드를 가리키는 델리게이트가 매번 생성 | 필드에 델리게이트를 한 번 담아 재사용 |
| `"코인: " + count` (문자열 연결) | `count.ToString()` 결과 + 연결된 새 `string` (최신 C# 컴파일러는 박싱하지 않음) | `SetText`, 값이 바뀔 때만 갱신 |
| `list.Sort(CompareByDistance)` (메서드 그룹) | 호출마다 델리게이트 객체 (C# 9) | `Comparison<T>` 필드에 한 번 담아 재사용 |
| `foreach (var x in someIEnumerable)` | 인터페이스로 받은 열거자 박싱 | 구체 타입(`List<T>`, 배열)으로 받거나 `for` |
| `new List<T>()`, `new T[n]` in `Update` | 매번 새 컬렉션 | 필드로 한 번 만들고 `Clear()` |
| `Physics2D.OverlapCircleAll`, `GetComponents<T>()` | 결과 배열 | `List<T>`를 받는 오버로드 |
| `GetComponent<T>()` 반복 | 할당은 없지만 매번 검색 비용 (에디터에서는 없는 컴포넌트 조회 시 할당) | `Awake`에서 캐싱, `TryGetComponent` |
| `gameObject.name`, `gameObject.tag` 읽기 | 매번 새 `string` | `CompareTag("Player")` |
| `yield return new WaitForSeconds(1f)` | 매번 객체 | 필드에 캐싱 |
| `Debug.Log(...)` | 문자열·스택 트레이스 | 핫 루프에서 제거, `[Conditional]` 래퍼 |

`foreach`는 오해가 많습니다. **`List<T>`, 배열, `Dictionary`를 구체 타입 그대로 `foreach`하면 할당이 없습니다**(구조체 열거자를 씁니다). 오래전 Unity에서 `foreach`가 할당하던 버그는 이미 고쳐졌습니다. 할당이 생기는 경우는 `IEnumerable<T>`, `IReadOnlyList<T>` 같은 **인터페이스 타입 변수**로 받아 `foreach`할 때입니다.

```csharp
List<Enemy> enemies = ...;
foreach (var e in enemies) { }             // ✅ 할당 없음 (List<T>.Enumerator 구조체)

IReadOnlyList<Enemy> view = enemies;
foreach (var e in view) { }                // ❌ 열거자가 IEnumerator<T>로 박싱됨
for (int i = 0; i < view.Count; i++) { }   // ✅ 인덱서는 할당 없음
```

### 할당을 없애는 도구

**1) 캐싱과 재사용.** 컴포넌트, 리스트, 델리게이트, `WaitForSeconds`를 필드로 한 번 만들어 둡니다.

```csharp
private readonly List<Collider2D> hits = new List<Collider2D>(64);  // 용량을 넉넉히 미리
void FixedUpdate()
{
    hits.Clear();   // 비우기만 하고 내부 배열은 재사용
}
```

**2) TextMeshPro의 `SetText`.** 서식 문자열과 숫자 인자를 받아 내부 버퍼에 직접 씁니다. `{0}`, `{1}` 자리에 숫자가 들어가고 `{0:2}`처럼 쓰면 소수점 자릿수를 지정합니다. **빌드(플레이어)에서는** `string`을 만들지 않으므로 버퍼가 충분히 커진 뒤에는 GC 할당이 없습니다. 단, **에디터에서는** TMP가 Inspector의 Text 칸에 보여 줄 문자열을 호출마다 만들기 때문에(`#if UNITY_EDITOR` 분기) Play Mode 프로파일링에서는 `SetText` 아래에 작은 `GC.Alloc`이 보입니다. `SetText`의 무할당은 Development Build에서 확인합니다.

```csharp
label.SetText("점수: {0}", score);          // int는 float 인자로 전달되어 정수로 표시
label.SetText("HP {0}/{1}", current, max);
```

**3) `StringBuilder`.** 서식이 복잡하면 `StringBuilder` 하나를 필드로 두고 재사용한 뒤 `label.SetText(builder)`로 넘깁니다. `Append(int)`는 런타임 구현에 따라 내부적으로 작은 할당이 생길 수 있으니, 결과는 반드시 프로파일러로 확인하세요.

**4) 할당 없는 물리 조회.** `Physics2D`의 조회 함수는 `ContactFilter2D`와 `List<T>`를 받는 오버로드가 있습니다. 결과를 내가 준 리스트에 채우고 개수를 돌려줍니다.

```csharp
ContactFilter2D filter = new ContactFilter2D();
filter.SetLayerMask(coinLayers);   // 레이어 필터 켜기 (useLayerMask = true가 됨)
filter.useTriggers = true;         // 트리거 콜라이더도 포함 (기본값 false!)

int count = Physics2D.OverlapCircle(center, radius, filter, hits);
```

리스트 용량보다 결과가 많으면 Unity가 리스트를 키우면서 **그 순간에만** 할당이 생깁니다. 예상 최대치로 용량을 잡아 두세요. 예전의 `OverlapCircleNonAlloc` 같은 `NonAlloc` 계열 함수는 최신 버전에서 사용 중단(obsolete) 처리되었으니 새 코드에는 위 오버로드를 쓰세요(정확한 상태는 사용하는 Unity 버전의 스크립팅 레퍼런스에서 확인).

### Profiler에서 GC Alloc 읽기

1. **Window → Analysis → Profiler**를 엽니다.
2. 상단의 대상 드롭다운을 **Play Mode**로 둡니다. (Edit Mode는 에디터 자체를 측정)
3. **CPU Usage** 모듈을 선택하고 아래 상세 창의 보기 방식을 **Hierarchy**로 바꿉니다.
4. 그래프에서 프레임 하나를 클릭한 뒤 **GC Alloc** 열 제목을 눌러 내림차순 정렬합니다.

```
Overview                                   Total   Self   Calls  GC Alloc   Time ms
▼ PlayerLoop                                72.1%   0.4%      1    3.9 KB     6.02
  ▼ FixedUpdate.ScriptRunBehaviourFixedUpdate 41.3%  0.1%     2    3.8 KB     3.45
    ▼ CoinMagnet.FixedUpdate() [Invoke]     41.0%  12.2%     2    3.8 KB     3.42   ← 범인
        GC.Alloc                             0.3%   0.3%    38    3.8 KB     0.03
        Object.FindObjectsByType()          20.1%  20.1%     2    0.6 KB     1.68
  ▶ Update.ScriptRunBehaviourUpdate          5.2%   0.1%      1    0.1 KB     0.43
▶ EditorLoop                                20.4% ...                                    ← 에디터 비용, 무시
```

(수치는 예시입니다. 항목 이름은 Unity 버전에 따라 조금씩 다를 수 있습니다.)

읽는 요령:

- **GC Alloc**은 그 항목과 자식들이 이 프레임에 할당한 총량입니다. 0B가 아닌 줄을 위에서부터 펼쳐 내려갑니다.
- `GC.Alloc` 샘플이 **어느 함수 바로 아래**에 있는지가 할당 위치입니다.
- 더 정확한 위치가 필요하면 Profiler 툴바의 **Call Stacks** 옵션을 켜고 **Timeline** 보기에서 `GC.Alloc` 샘플을 선택하면 할당한 코드의 호출 스택이 표시됩니다.
- **Deep Profile**은 모든 C# 메서드를 계측해 정확하지만 게임이 크게 느려집니다. 짧게만 켜거나, 아래처럼 직접 구간 표시(`ProfilerMarker`)를 넣는 편이 낫습니다.
- `EditorLoop`의 할당은 에디터가 만든 것이라 게임과 무관합니다. 최종 확인은 **Development Build를 실제 기기에 연결**해서 합니다(18장).

```csharp
using Unity.Profiling;

static readonly ProfilerMarker PullMarker = new ProfilerMarker("CoinMagnet.Pull");

void FixedUpdate()
{
    using (PullMarker.Auto())      // Profiler에 "CoinMagnet.Pull" 항목으로 표시됨
    {
        // 측정할 코드
    }
}
```

`ProfilerMarker`는 구조체이고 `Auto()`도 할당을 만들지 않아서 출시 코드에 남겨 둬도 됩니다.

## 실습: 코인 러시에 적용하기

### 1단계: STEP 4 방식 점수 표시의 할당 측정하기

비교 기준부터 봅니다. STEP 4처럼 매 프레임 문자열을 만드는 테스트 스크립트를 잠시 만듭니다.

```csharp
// Assets/_CoinRush/Scripts/UI/ScorePollingTest.cs  (측정 후 삭제)
using TMPro;
using UnityEngine;

public class ScorePollingTest : MonoBehaviour
{
    [SerializeField] private GameManager gameManager;
    [SerializeField] private TextMeshProUGUI label;

    void Update()
    {
        label.text = $"점수: {gameManager.Score}";   // 매 프레임 박싱 + 문자열
    }
}
```

1. 씬에 빈 오브젝트 `PollingTest`를 만들고 위 스크립트를 붙인 뒤, Inspector에서 **Game Manager** 칸에 01장의 `GameManager` 오브젝트를, **Label** 칸에 `ScoreText`를 드래그합니다. (기존 `ScoreDisplay` 컴포넌트는 잠시 체크 해제) Game Manager 칸을 비워 두면 매 프레임 `NullReferenceException`이 납니다.
2. Profiler를 켜고 Play → 프레임 하나 선택 → Hierarchy에서 GC Alloc 정렬.
3. `ScorePollingTest.Update()` 아래에 매 프레임 수십 바이트의 `GC.Alloc`이 찍히는 것을 확인합니다. 초당 60번입니다.
4. 확인했으면 `PollingTest` 오브젝트와 스크립트를 삭제하고 `ScoreDisplay`를 다시 체크합니다.

### 2단계: ScoreDisplay와 HealthDisplay를 할당 없이

01장의 두 파일에서 `Show` 메서드 **한 줄씩만** 바꿉니다.

```csharp
// ScoreDisplay.cs — Show 메서드 교체
private void Show(int score) => label.SetText("점수: {0}", score);
```

```csharp
// HealthDisplay.cs — Show 메서드 교체
private void Show(int current, int max) => label.SetText("HP {0}/{1}", current, max);
```

01장에서 이미 이벤트 기반으로 바꿨으므로 "바뀔 때만" 그리고, 이번에 "그릴 때도 할당 없이"가 되었습니다. React로 치면 불필요한 리렌더를 없앤 것(이벤트)과 렌더 자체를 가볍게 만든 것(`SetText`)의 차이입니다.

### 3단계: 일부러 나쁘게 짠 코인 자석

플레이어 주변의 코인을 끌어당기는 자석을 만듭니다. 먼저 **웹 개발 감각으로 자연스럽게** 짠 버전입니다. 이 코드에는 할당 문제가 네 군데 있습니다.

```csharp
// Assets/_CoinRush/Scripts/Player/CoinMagnet.cs  (나쁜 버전)
using System.Linq;
using UnityEngine;

public class CoinMagnet : MonoBehaviour
{
    [SerializeField] private float radius = 2.5f;
    [SerializeField] private float pullSpeed = 9f;
    [SerializeField] private string status;   // Inspector에서 보려는 디버그용

    void FixedUpdate()
    {
        // ❌ 1) 씬의 모든 Coin을 담은 새 배열
        Coin[] all = FindObjectsByType<Coin>(FindObjectsSortMode.None);

        // ❌ 2) LINQ: 이터레이터 + 델리게이트(람다가 필드·this만 써서 클로저 객체는 없음) + ToList 결과 리스트
        var near = all
            .Where(c => Vector2.Distance(c.transform.position, transform.position) < radius)
            .ToList();

        foreach (var coin in near)
        {
            // ❌ 3) 코인마다 GetComponent (할당은 없지만 매번 검색)
            var body = coin.GetComponent<Rigidbody2D>();
            body.gravityScale = 0f;
            body.linearVelocity = ((Vector2)transform.position - body.position).normalized * pullSpeed;
        }

        // ❌ 4) near.Count.ToString() + 문자열 연결 → 매 스텝 새 string 2개 (박싱은 아님)
        status = "끌어당기는 코인: " + near.Count;
    }
}
```

1. Player에 `CoinMagnet`을 붙입니다.
2. `GameManager`의 Coin Interval을 0.1로 낮춰 코인을 많이 떨어뜨립니다.
3. Play하고 코인 아래로 가서 빨아들여지는지 확인합니다.

### 4단계: 프로파일러로 범인 찾기

1. Profiler에서 Play 중인 프레임을 선택하고 Hierarchy를 GC Alloc으로 정렬합니다.
2. `FixedUpdate.ScriptRunBehaviourFixedUpdate` → `CoinMagnet.FixedUpdate()`를 펼칩니다. 물리 스텝은 한 프레임에 여러 번 돌 수 있어 Calls가 2 이상일 수 있습니다.
3. 자식 항목 중 `FindObjectsByType`, `GC.Alloc`의 크기를 기록합니다. 코인이 많을수록 커집니다.
4. 툴바의 **Call Stacks**를 켜고 **Timeline** 보기에서 `GC.Alloc` 막대를 클릭해, LINQ(`Enumerable.Where`, `ToList`)와 `String.Concat`이 호출 스택에 나오는지 확인합니다.
5. 표에 정리합니다.

| 위치 | 원인 | 코인 수에 비례? |
|---|---|---|
| `FindObjectsByType` | 결과 배열 | 예 |
| `Where` + 람다 | 이터레이터·델리게이트 | 아니오 (고정) |
| `ToList` | 결과 리스트 | 예 |
| `"..." + near.Count` | `ToString` 문자열 + 연결 결과 문자열 | 아니오 (고정) |

### 5단계: Coin에 끌려가는 기능 추가

끌려가는 동작은 코인 자신이 하게 하고, `Rigidbody2D`는 코인이 캐싱합니다. 01장의 `Coin.cs`에 필드와 메서드를 **추가**합니다(기존 `AnyCollected`, `TryCollect`, `ResetStatics`는 그대로).

```csharp
// Coin.cs — 클래스 안에 추가
private Rigidbody2D body;

void Awake() => body = GetComponent<Rigidbody2D>();

// 자석이 호출: 목표 지점을 향해 속도를 설정
public void Attract(Vector2 target, float speed)
{
    body.gravityScale = 0f;
    body.linearVelocity = (target - body.position).normalized * speed;
}
```

### 6단계: 할당 없는 CoinMagnet

`CoinMagnet.cs` 전체를 다음으로 교체합니다.

```csharp
// Assets/_CoinRush/Scripts/Player/CoinMagnet.cs  (고친 버전)
using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;

public class CoinMagnet : MonoBehaviour
{
    private static readonly ProfilerMarker PullMarker = new ProfilerMarker("CoinMagnet.Pull");

    [SerializeField] private float radius = 2.5f;
    [SerializeField] private float pullSpeed = 9f;
    [SerializeField] private LayerMask coinLayers;
    [SerializeField, Min(1)] private int initialCapacity = 64;   // 상한이 아니라 리스트의 초기 용량

    private List<Collider2D> hits;          // 재사용하는 결과 리스트
    private ContactFilter2D filter;         // 구조체 — 할당 없음

    public int PullingCount { get; private set; }   // 디버그는 문자열 대신 숫자로

    void Awake()
    {
        hits = new List<Collider2D>(initialCapacity);
        filter = new ContactFilter2D();
        filter.SetLayerMask(coinLayers);
        filter.useTriggers = true;          // 코인은 트리거 콜라이더
    }

    void FixedUpdate()
    {
        using (PullMarker.Auto())
        {
            Vector2 center = transform.position;
            PullingCount = Physics2D.OverlapCircle(center, radius, filter, hits);

            for (int i = 0; i < PullingCount; i++)
            {
                // TryGetComponent는 없을 때도 할당하지 않는다
                if (hits[i].TryGetComponent(out Coin coin))
                    coin.Attract(center, pullSpeed);
            }
        }
    }

    void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, radius);
    }
}
```

바뀐 점을 문제 표와 맞춰 봅니다.

| 나쁜 버전 | 고친 버전 | 효과 |
|---|---|---|
| `FindObjectsByType` 로 전체 검색 | `OverlapCircle` 로 반경 안만 조회 | 할당 제거 + 물리 엔진의 공간 분할 활용 |
| LINQ `Where` + `ToList` | `ContactFilter2D` + 재사용 `List` + `for` | 이터레이터·델리게이트·리스트 할당 제거 |
| 코인마다 `GetComponent<Rigidbody2D>` | 코인이 `Awake`에서 캐싱 | 검색 비용 제거 |
| `status` 문자열 | `int PullingCount` 프로퍼티 | 문자열 할당 제거 |

`initialCapacity`는 처리 개수의 **상한이 아닙니다.** 반경 안에 65개 이상이 들어오면 `OverlapCircle`이 리스트를 키우며 그 스텝에서 할당이 생기고, 커진 뒤에는 다시 할당하지 않습니다. 엄격한 상한이 필요하면 크기가 고정된 배열을 받는 오버로드(`Collider2D[]`)를 쓰고, 배열이 가득 찬 경우 나머지 코인은 다음 스텝에 처리한다는 정책을 정합니다.

Inspector에서 **Coin Layers**를 `Coin`으로 지정합니다(01장에서 코인 프리팹의 레이어를 `Coin`으로 설정했습니다). Player를 선택하면 Scene 뷰에 노란 원으로 자석 반경이 보입니다.

### 7단계: 할당 모니터 붙이기

프로파일러를 매번 열지 않아도 되도록 화면 구석에 "이번 프레임 GC 할당량"을 띄웁니다. `ProfilerRecorder`는 프로파일러 카운터를 코드에서 읽는 API입니다.

```csharp
// Assets/_CoinRush/Scripts/Utils/AllocationMonitor.cs
using TMPro;
using Unity.Profiling;
using UnityEngine;

public class AllocationMonitor : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI label;

    private ProfilerRecorder gcAllocRecorder;

    void OnEnable()
    {
        gcAllocRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame");
    }

    void OnDisable()
    {
        gcAllocRecorder.Dispose();   // 네이티브 자원 — 반드시 해제
    }

    void Update()
    {
        if (!gcAllocRecorder.Valid) return;
        label.SetText("GC {0} B/frame", gcAllocRecorder.LastValue);
    }
}
```

1. Canvas에 TextMeshPro 텍스트 `AllocText`를 우하단에 만들고, 빈 오브젝트 `AllocationMonitor`에 위 스크립트를 붙여 label을 연결합니다.
2. 이 카운터는 에디터와 **Development Build**에서 값을 제공합니다. 릴리스 빌드에서는 `Valid`가 false일 수 있으므로 위 코드처럼 확인합니다. 카운터 이름은 Unity 버전에 따라 달라질 수 있으니, 값이 안 나오면 Profiler의 Memory 모듈에 표시되는 카운터 이름을 확인하세요.
3. 표시 자체가 할당을 만들면 측정이 오염됩니다. 그래서 여기서도 `SetText`를 씁니다. 다만 앞의 개념 절에서 본 것처럼 **에디터에서는** `SetText`도 Inspector 표시용 문자열을 만들므로, 이 모니터는 에디터에서 매 프레임 수십 바이트를 스스로 할당합니다. 에디터에서 0이 아닌 숫자가 보이는 것은 정상이며, 이 숫자로 판정하는 것은 Development Build에서 합니다.

### 확인하기

▶ Play 후 다음을 확인합니다.

- 플레이어 반경 2.5 안의 코인이 플레이어 쪽으로 빨려 들어온다. Scene 뷰에서 노란 원이 보인다.
**에디터(Play Mode)에서:**

- Profiler Hierarchy에서 `CoinMagnet.Pull` 항목의 GC Alloc이 **0 B**다. 코인 수가 늘어 리스트 용량(64)을 처음 넘는 스텝에서만 할당이 한 번 보이고, 그 뒤로는 다시 0이다.
- `ScoreDisplay`, `HealthDisplay`는 점수·체력이 **바뀌는 프레임에만** 호출되고, 아무 일도 없는 프레임에는 항목 자체가 없다. (바뀌는 프레임에 보이는 작은 `GC.Alloc`은 앞에서 설명한 TMP의 에디터 전용 문자열입니다.)
- `AllocationMonitor.Update` 아래의 할당은 같은 이유로 에디터에서만 생기는 것이니 판정에서 뺀다.

**Development Build에서(최종 판정):**

1. **File → Build Profiles**에서 현재 플랫폼(PC 등)의 **Development Build**와 **Autoconnect Profiler**를 켜고 Build And Run 합니다.
2. 게임을 10초 정도 플레이해 리스트와 TMP 버퍼가 충분히 커지게(예열) 한 뒤, 에디터 Profiler에 연결된 빌드의 프레임을 봅니다.
3. `CoinMagnet.Pull`, `ScoreDisplay`, `HealthDisplay`, `AllocationMonitor` 항목의 GC Alloc이 0이고, 우하단 `AllocText`가 대부분의 프레임에서 0이면 성공이다.

0이 아닌 프레임이 가끔 보인다면 대부분 `GameManager`의 `Instantiate`(코인·가시 공 생성)와 `Destroy`입니다. 생성·파괴는 GC 할당과 네이티브 비용을 함께 만듭니다. 이것은 12장 오브젝트 풀에서 없앱니다.

## 흔한 실수

1. **`OverlapCircle`이 항상 0을 돌려준다**
   원인: `ContactFilter2D.useTriggers`의 기본값은 false라서 트리거 콜라이더인 코인이 빠집니다. 또는 `SetLayerMask`에 넘긴 마스크가 `Nothing`입니다.
   해결: `filter.useTriggers = true;`를 설정하고 Coin Layers를 확인합니다. `Awake`에서 필터를 만들기 때문에 Play 중에 Inspector에서 레이어를 바꾸면 반영되지 않습니다.
2. **`$"..."` 대신 `string.Concat`, `ToString()`으로 바꿨는데도 할당이 그대로다**
   원인: 문법만 바꿨을 뿐 여전히 새 `string`을 만들고 있습니다.
   해결: 매 프레임 표시가 필요하면 `SetText`나 재사용 `StringBuilder`를 쓰고, 가능하면 값이 바뀔 때만 갱신합니다.
3. **리스트를 필드로 옮겼는데 가끔 스파이크가 난다**
   원인: 초기 용량이 부족해 결과가 많은 프레임에서 리스트 내부 배열이 커졌습니다.
   해결: 최대 예상치로 초기 용량을 잡습니다(`new List<Collider2D>(64)`). 용량은 상한이 아니므로 결과가 그보다 많으면 다시 커집니다. 커진 뒤에는 다시 할당하지 않지만, 첫 스파이크도 모바일에선 보입니다.
4. **에디터에서 측정한 할당량이 빌드와 다르다**
   원인: 에디터 전용 검사(예: 없는 컴포넌트를 `GetComponent`할 때의 할당), TMP `SetText`의 에디터 전용 문자열 생성, Inspector 갱신, 디버그 코드가 섞입니다.
   해결: 에디터 수치는 "어디서 나나"를 찾는 용도로 쓰고, 최종 수치는 Development Build + 실기기 프로파일링으로 확인합니다.
5. **Deep Profile을 켰더니 게임이 너무 느려져서 판단이 안 된다**
   원인: Deep Profile은 모든 메서드 호출에 계측 코드를 넣습니다.
   해결: 평소엔 끄고, 의심 구간에 `ProfilerMarker`를 넣어 좁혀 갑니다. 할당 위치 확인에는 Call Stacks 옵션이 더 가볍습니다.

## 연습 문제

**1. ★☆☆ 박싱 찾기**
다음 중 힙 할당(박싱 포함)이 일어나는 줄을 모두 고르세요.

```csharp
Vector2 a = new Vector2(1, 2);           // (가)
object b = a;                             // (나)
var list = new List<int>(8);              // (다)
list.Add(3);                              // (라)  용량 8 이내
foreach (var x in list) { }               // (마)
IEnumerable<int> e = list;
foreach (var x in e) { }                  // (바)
Debug.Log(list.Count);                    // (사)
```

<details><summary>힌트·해설</summary>

(나) 구조체를 `object`로 박싱. (다) `List<int>` 객체와 내부 배열. (바) 인터페이스로 받은 열거자 박싱. (사) `Debug.Log(object)`로 int 박싱 + 로그 문자열.
(가)는 구조체 초기화라 할당 없음, (라)는 용량 이내라 할당 없음, (마)는 `List<int>.Enumerator` 구조체라 할당 없음입니다.
</details>

**2. ★☆☆ 게임오버 텍스트에 최고 점수 표시**
`GameOverView`가 패널을 켤 때 "최고 기록 {HighScore}"도 표시하도록 하되, 할당 없이 구현하세요.

<details><summary>힌트·해설</summary>

`GameOverView`에 `[SerializeField] private TextMeshProUGUI highScoreLabel;`을 추가하고 `Show()`에서 `highScoreLabel.SetText("최고 기록 {0}", gameManager.HighScore);`를 호출합니다. 게임오버는 한 판에 한 번이라 문자열 보간을 써도 성능상 문제는 없지만, `SetText` 습관을 들이면 매 프레임 갱신 UI에서 실수하지 않습니다.
</details>

**3. ★★☆ 가장 가까운 코인 찾기**
`CoinMagnet`에 "반경 안에서 가장 가까운 코인 하나만" 끌어당기는 모드를 추가하세요. LINQ의 `OrderBy`나 `List.Sort`를 쓰지 말고 할당 0을 유지해야 합니다.

<details><summary>힌트·해설</summary>

정렬할 필요가 없습니다. 한 번 순회하며 최솟값만 기억하면 됩니다. 거리 비교는 `sqrMagnitude`로 하면 제곱근 계산도 생략됩니다(05장에서 자세히 다룹니다).

주의할 점이 하나 있습니다. `Attract`는 코인의 속도와 `gravityScale = 0`을 **설정해 둘 뿐**이라, 매 스텝 "가장 가까운 코인"을 새로 고르면 대상이 바뀐 뒤에도 이전 코인이 계속 날아옵니다. 그래서 한 번 고른 코인은 **먹을 때까지 유지**하고, 그 코인이 파괴된 뒤에만 새로 고릅니다. 파괴된 코인은 Unity의 `== null` 검사에서 true가 됩니다.

```csharp
// CoinMagnet.cs — 필드 추가
[SerializeField] private bool nearestOnly;
private Coin currentTarget;

// CoinMagnet.FixedUpdate — using (PullMarker.Auto()) 블록 안을 교체
Vector2 center = transform.position;

if (nearestOnly)
{
    if (currentTarget == null)   // 아직 대상이 없거나, 이전 대상을 먹어서 파괴됨
    {
        PullingCount = Physics2D.OverlapCircle(center, radius, filter, hits);
        float bestSqr = float.MaxValue;
        for (int i = 0; i < PullingCount; i++)
        {
            if (!hits[i].TryGetComponent(out Coin candidate)) continue;
            float sqr = ((Vector2)hits[i].transform.position - center).sqrMagnitude;
            if (sqr < bestSqr) { bestSqr = sqr; currentTarget = candidate; }
        }
    }
    if (currentTarget != null) currentTarget.Attract(center, pullSpeed);   // 플레이어가 움직여도 매 스텝 방향 갱신
    return;
}

PullingCount = Physics2D.OverlapCircle(center, radius, filter, hits);
for (int i = 0; i < PullingCount; i++)
{
    if (hits[i].TryGetComponent(out Coin coin))
        coin.Attract(center, pullSpeed);
}
```

`using` 블록 안의 `return`도 `Dispose`를 호출하므로 마커가 올바르게 닫힙니다. 모드를 Play 중에 "전체"에서 "하나만"으로 바꾸면 이미 끌려오던 코인들은 계속 날아오는데, 이를 막으려면 `Coin`에 `gravityScale`과 속도를 원래대로 돌리는 `Release()` 메서드를 추가해 호출합니다.

정렬이 꼭 필요하면 `Comparison<Collider2D>`를 필드에 한 번 만들어 두고 `hits.Sort(cachedComparison)`을 씁니다. 비교 람다가 `center` 같은 지역 변수를 캡처하면 매번 클로저가 생기므로, 기준점도 필드에 저장해야 합니다.
</details>

**4. ★★☆ 코루틴 대기 객체 캐싱**
0.5초마다 체력을 1 회복하는 `Regeneration` 컴포넌트를 코루틴으로 만들되, 루프마다 `new WaitForSeconds`를 만들지 않게 하세요. 프로파일러로 전후를 비교하세요.

<details><summary>힌트·해설</summary>

```csharp
using System.Collections;
using UnityEngine;

public class Regeneration : MonoBehaviour
{
    [SerializeField] private Health health;
    [SerializeField] private float interval = 0.5f;
    private WaitForSeconds wait;
    private Coroutine running;

    void Awake() => wait = new WaitForSeconds(interval);
    void OnEnable() => running = StartCoroutine(Loop());

    // 컴포넌트 체크 해제(enabled = false)만으로는 코루틴이 멈추지 않는다.
    // 멈추지 않으면 다시 켤 때 루프가 하나 더 생겨 회복이 두 배가 된다.
    void OnDisable()
    {
        if (running != null) StopCoroutine(running);
        running = null;
    }

    private IEnumerator Loop()
    {
        while (true)
        {
            yield return wait;          // 같은 객체를 계속 재사용
            health.Heal(1);
        }
    }
}
```

코루틴은 **GameObject를 비활성화**하면 멈추지만, **컴포넌트만 비활성화**하면 계속 돕니다. 그래서 `OnDisable`에서 직접 멈춥니다. `StartCoroutine` 자체도 코루틴 객체를 할당하므로 매 프레임 시작하면 안 됩니다. 한 번 시작해 루프를 도는 구조가 맞습니다. 09장에서 `Awaitable` 기반으로 다시 씁니다.
</details>

**5. ★★★ 할당 예산 테스트 (스스로 확장)**
"플레이 중 60초 동안 게임 코드의 프레임당 GC 할당이 0이어야 한다"를 자동으로 검사하는 도구를 만들어 보세요. `AllocationMonitor`를 확장해 최근 N 프레임의 최대값·0이 아닌 프레임 수를 기록하고, 기준을 넘으면 `Debug.LogWarning`을 한 번만 출력하세요.

<details><summary>힌트·해설</summary>

- `ProfilerRecorder.StartNew`에 용량 인자(예: 300)를 주면 최근 샘플을 보관합니다. `recorder.Count`, `recorder.GetSample(i).Value`로 순회할 수 있습니다(할당 없음).
- 첫 몇 초는 씬 로딩 할당이 있으므로 워밍업 시간을 두고 측정합니다.
- 경고는 한 번만 — 경고 문자열을 만드는 것 자체가 할당이기 때문입니다.
- 에디터 비용(TMP `SetText`의 에디터 전용 문자열 포함)이 섞이는 문제는 Development Build에서 돌려 해결합니다. 나중에 24장의 플레이테스트 빌드에 넣어 두면 테스터 기기에서 할당 회귀를 잡을 수 있습니다.
</details>

## 셀프 체크

**1. `new Vector2(1, 2)`는 GC 할당이 없는데 `new List<int>()`는 있는 이유를 설명해 보세요.**

<details><summary>모범 답안</summary>

`Vector2`는 구조체(값 타입)라서 `new`가 값을 초기화할 뿐 힙에 객체를 만들지 않습니다. 지역 변수라면 스택에 놓입니다. `List<int>`는 클래스(참조 타입)라서 `new`가 힙에 객체를 할당하고, 그 객체는 참조가 끊긴 뒤 GC가 회수해야 합니다.
</details>

**2. 평균 fps는 58인데 게임이 가끔 "툭" 끊깁니다. GC와 어떤 관계가 있을 수 있나요?**

<details><summary>모범 답안</summary>

매 프레임 조금씩 할당하면 힙이 차고, GC가 도는 프레임 하나만 수십 ms가 걸려 스파이크가 됩니다. 평균에는 거의 드러나지 않지만 눈에는 끊김으로 보입니다. Unity의 Boehm GC는 세대 구분이 없어 짧게 사는 객체도 비용이 큽니다. 프로파일러에서 최악 프레임의 GC.Collect와 평소 프레임의 GC Alloc을 확인해야 합니다.
</details>

**3. Incremental GC를 켜면 할당을 신경 쓰지 않아도 되나요?**

<details><summary>모범 답안</summary>

아닙니다. Incremental GC는 수집 작업을 여러 프레임에 나눠 한 프레임의 정지 시간을 줄일 뿐, 총 비용은 줄이지 않습니다. 할당 속도가 분할 처리 속도를 넘으면 결국 한 번에 몰아서 수집합니다. 근본 해결은 할당을 줄이는 것입니다.
</details>

**4. `List<T>`를 `foreach`하는 것과 `IReadOnlyList<T>`로 받아 `foreach`하는 것의 차이는?**

<details><summary>모범 답안</summary>

`List<T>`를 구체 타입으로 `foreach`하면 구조체 열거자 `List<T>.Enumerator`를 그대로 써서 할당이 없습니다. 인터페이스 타입으로 받으면 `GetEnumerator()`가 `IEnumerator<T>`를 반환해야 하므로 구조체 열거자가 박싱되어 힙 할당이 생깁니다. 인터페이스로 받아야 한다면 `Count`와 인덱서를 쓰는 `for` 루프가 안전합니다.
</details>

**5. Profiler Hierarchy에서 할당 위치를 찾는 순서를 설명해 보세요.**

<details><summary>모범 답안</summary>

Play Mode 대상으로 녹화 → CPU Usage 모듈에서 프레임 선택 → Hierarchy 보기에서 GC Alloc 열로 정렬 → 0이 아닌 항목을 펼쳐 `GC.Alloc` 샘플이 어느 함수 아래 있는지 확인 → 더 정확히는 Call Stacks를 켜고 Timeline에서 `GC.Alloc` 샘플을 선택해 호출 스택을 봅니다. EditorLoop 할당은 무시하고, 최종 확인은 Development Build 실기기로 합니다.
</details>

## 핵심 요약

- "class를 new 하면 할당", 구조체의 `new`는 할당이 아닙니다. 박싱은 `new` 없이 숨어서 할당합니다.
- Unity의 Boehm GC는 세대 구분·압축이 없어서, 작은 할당이 쌓여 프레임 스파이크를 만듭니다.
- Incremental GC는 충격 완화일 뿐 근본 해결은 할당 줄이기입니다.
- 매 프레임 코드에서는 문자열 연결, LINQ, 캡처 람다, 인터페이스 `foreach`, 새 컬렉션, 배열 반환 API를 피합니다.
- 캐싱·컬렉션 재사용, TMP `SetText`, `ContactFilter2D` + `List` 물리 오버로드가 기본 도구입니다.
- Profiler Hierarchy의 GC Alloc 열 → `GC.Alloc` 샘플 위치 → Call Stacks 순으로 범인을 찾습니다.
- 코인 러시는 이제 이벤트 + `SetText`로 UI가 할당 없이 갱신되고, `CoinMagnet`이 할당 0으로 동작합니다.

## 더 읽을거리

- Unity Manual, "Managed memory" (GC와 Incremental GC 설명) — https://docs.unity3d.com/Manual/performance-managed-memory.html
- Unity Manual, "CPU Usage Profiler module" — https://docs.unity3d.com/Manual/ProfilerCPU.html
- Unity Scripting API, `Physics2D.OverlapCircle` — https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircle.html
- Unity Scripting API, `Unity.Profiling.ProfilerRecorder` — https://docs.unity3d.com/ScriptReference/Unity.Profiling.ProfilerRecorder.html
- Unity 전자책, "Ultimate guide to profiling Unity games" (Unity 공식 무료 배포)
