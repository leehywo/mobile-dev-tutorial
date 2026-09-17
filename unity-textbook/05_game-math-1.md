# 05. 게임 수학 1 — 벡터·내적·외적

> **이 장에서 배울 것**
> - 위치 벡터와 방향 벡터를 구분하고, 뺄셈으로 "A에서 B로 가는 방향"을 구한다
> - `magnitude`·`sqrMagnitude`·`normalized`를 상황에 맞게 골라 쓴다
> - 내적으로 앞/뒤와 시야각을, 외적(2D z성분)으로 왼쪽/오른쪽을 판정할 수 있다
> - `Vector2.Angle`/`SignedAngle`, 투영, `Vector2.Reflect`의 의미를 설명할 수 있다
> - 플레이어를 추적하는 적, 화면 밖 원형 스폰, 시야각 자동 조준 무기를 구현한다
>
> **선수 장**: 01, 03, 04 · **예상 시간**: 3~4시간 · **코인 러시 진행**: 드디어 서바이버라이크 모양이 됩니다. 떨어지는 가시 공 대신 화면 밖 사방에서 적이 몰려오고, 플레이어가 바라보는 방향의 부채꼴 안에 있는 가장 가까운 적을 자동으로 조준해 쏩니다.

## 왜 필요한가

03~04장의 코인 러시는 아직 "위에서 떨어지는 것을 피하는" 게임입니다. 서바이버라이크로 바꾸려면 다음이 필요합니다.

```
① 적이 플레이어를 향해 걸어온다                → 방향 = 목표 위치 - 내 위치, 정규화
② 적이 화면 밖 아무 방향에서나 나타난다          → 원 둘레 위의 점 = 중심 + 방향 × 반지름
③ 무기가 "앞쪽 120°" 안의 가장 가까운 적만 쏜다   → 거리 비교(sqrMagnitude) + 내적
④ (연습) 뒤에서 치면 치명타, 유도탄의 선회 방향     → 내적, 외적
⑤ (연습) 벽에 튕기는 탄                         → 반사
```

이 장 없이 ①을 구현하면 흔히 이런 코드가 나옵니다.

```csharp
// ❌ 흔한 첫 시도
Vector2 dir = target.position - transform.position;
body.linearVelocity = dir * speed;        // 멀리 있으면 엄청 빠르고, 가까워지면 느려짐
```

거리가 10이면 속도가 10배가 되고 가까이 오면 거의 멈춥니다. "방향"과 "거리"를 분리하지 않았기 때문입니다. 이 장의 내용은 대부분 이 분리를 자유롭게 하는 연습입니다. 게임 수학은 공식 암기보다 **그림으로 생각하는 습관**이 중요하니, 모든 절의 텍스트 다이어그램을 손으로 한 번씩 그려 보세요.

## 개념

### 위치 벡터와 방향 벡터

`Vector2(3, 2)`는 두 가지로 읽을 수 있습니다.

```
 y                                    y
 ▲                                    ▲
 │       • (3,2)  ← "위치": 원점에서   │         ↗  ← "방향(변위)": 어디서 시작하든
 │                  본 한 점           │       ↗      오른쪽 3, 위로 2 만큼
 │                                    │     ↗
 └──────────▶ x                       └──────────▶ x
```

| | 위치 (point) | 방향·변위 (vector) |
|---|---|---|
| 예 | `transform.position`, 스폰 지점 | 속도, 이동 입력, "적→플레이어" |
| 의미 있는 연산 | 위치 + 방향 = 위치, 위치 − 위치 = 방향 | 방향 + 방향, 방향 × 숫자 |
| 의미 없는 연산 | 위치 + 위치 (서울 + 부산 = ?) | — |

Unity는 둘을 같은 타입으로 표현하므로 구분은 **변수 이름**으로 합니다. `enemyPos`, `toPlayer`, `moveDir`처럼 쓰면 실수가 줄어듭니다.

2D 게임에서는 `transform.position`이 `Vector3`입니다. `(Vector2)transform.position`으로 형변환하면 z가 버려지고, `Vector2`를 `Vector3` 자리에 넣으면 z = 0이 됩니다. 둘을 섞어서 빼면 z 성분이 끼어들어 거리가 달라질 수 있으니 **2D 계산은 먼저 `Vector2`로 바꾼 뒤** 합니다.

### 뺄셈으로 방향 구하기

"A에서 B로 가는 벡터"는 **B − A** (도착 − 출발)입니다.

```
        B (4, 3)  ← 플레이어
        ▲
        │ toPlayer = B - A = (4-1, 3-1) = (3, 2)
        │
A (1, 1) ← 적
```

```csharp
Vector2 enemyPos = body.position;
Vector2 playerPos = target.position;
Vector2 toPlayer = playerPos - enemyPos;   // 적 → 플레이어
```

순서를 거꾸로 쓰면 적이 플레이어에게서 도망칩니다. 헷갈리면 "**도착에서 출발을 뺀다**"를 기억하세요.

### 크기(magnitude)와 정규화(normalized)

```
toPlayer = (3, 4)
magnitude    = √(3² + 4²) = √25 = 5      → 거리
sqrMagnitude = 3² + 4²    = 25           → 거리의 제곱 (제곱근 계산 없음)
normalized   = (3/5, 4/5) = (0.6, 0.8)   → 방향만 (길이 1, "단위 벡터")
```

| 필요 | 쓰는 것 | 이유 |
|---|---|---|
| 실제 거리 값(UI 표시, 비례 계산) | `magnitude`, `Vector2.Distance(a, b)` | 제곱근이 필요 |
| 거리 **비교** ("7보다 가까운가", "누가 더 가까운가") | `sqrMagnitude` 와 `range * range` 비교 | 제곱근 생략, 결과 동일 |
| 방향만 (일정한 속도로 이동) | `normalized` | 길이를 1로 맞춤 |

`a < b`이면 `a² < b²`이므로(둘 다 0 이상일 때) 비교에는 제곱을 써도 됩니다. 적 300마리 × 매 프레임이면 제곱근을 아끼는 것이 의미가 있습니다.

그래서 추적 코드는 다음처럼 **방향(정규화) × 속력**으로 씁니다.

```csharp
Vector2 direction = toPlayer.normalized;              // 길이 1
body.linearVelocity = direction * data.moveSpeed;     // 거리와 무관하게 일정한 속력
```

주의할 점 두 가지:

- 길이가 거의 0인 벡터를 정규화하면 Unity는 `Vector2.zero`를 돌려줍니다. 적이 플레이어와 정확히 겹치면 방향이 0이 되므로, 도착 판정(`sqrMagnitude < 아주 작은 값`)을 먼저 둡니다.
- 대각선 입력 (1, 1)의 길이는 √2 ≈ 1.41입니다. 정규화하지 않으면 대각선 이동이 41% 빠릅니다. Input System 기본 액션의 `Move`는 이미 정규화된 값을 주지만, 직접 만든 입력 벡터는 `Vector2.ClampMagnitude(input, 1f)`로 길이를 제한하세요.

### 내적(Dot) — 두 방향이 얼마나 같은 쪽인가

```
a · b = a.x × b.x + a.y × b.y  =  |a| × |b| × cos θ      (θ = a와 b 사이 각)
```

두 벡터가 **모두 정규화**되어 있으면 `Vector2.Dot(a, b) = cos θ`가 됩니다.

```
               b (θ=0°)  dot = 1     완전히 같은 방향
              ↗
    b (60°) ↗    dot = 0.5
   ─────────●──────────▶ a (바라보는 방향)
            │ b (90°)    dot = 0     정확히 옆
            ↓
     b (180°) ←          dot = -1    정반대 (뒤)
```

| dot (정규화된 두 벡터) | 각도 | 의미 |
|---|---|---|
| 1 | 0° | 정면 |
| > 0 | 0° ~ 90° 미만 | 앞쪽 반면 |
| 0 | 90° | 정확히 옆 |
| < 0 | 90° 초과 ~ 180° | 뒤쪽 반면 |
| −1 | 180° | 정반대 |

**앞/뒤 판정**은 부호만 보면 됩니다. 이때는 정규화도 필요 없습니다(길이는 양수라 부호에 영향이 없음).

```csharp
Vector2 toEnemy = enemyPos - playerPos;
bool inFront = Vector2.Dot(facing, toEnemy) > 0f;
```

**시야각 판정**은 "사이각 θ가 시야각의 절반 이하인가"입니다. `cos`는 0°~180°에서 각이 커질수록 작아지므로, 부등호가 뒤집힙니다.

```
시야각 120° → 절반 60° → cos 60° = 0.5
θ ≤ 60°  ⇔  cos θ ≥ 0.5  ⇔  Dot(facing, toEnemy.normalized) ≥ 0.5

         ╲  60° │ 60°  ╱
          ╲     │     ╱        dot ≥ 0.5 인 영역 = 부채꼴 안
           ╲    │    ╱
            ╲   │   ╱
               [P] ──▶ facing 방향이 위쪽이라고 가정
```

```csharp
float cosHalf = Mathf.Cos(viewAngle * 0.5f * Mathf.Deg2Rad);   // Mathf.Cos는 라디안을 받음
bool inView = Vector2.Dot(facing, toEnemy.normalized) >= cosHalf;
```

`Vector2.Angle(facing, toEnemy) <= viewAngle * 0.5f`로도 같은 판정을 할 수 있습니다. 읽기는 더 쉽지만 내부에서 역코사인(`acos`)을 계산합니다. 대상이 많은 루프에서는 코사인 임계값을 한 번 계산해 두고 내적과 비교하는 편이 가볍습니다.

내적의 또 다른 해석은 "**b를 a 방향으로 비췄을 때 그림자의 길이**"입니다(a가 정규화된 경우). 이것이 투영으로 이어집니다.

### 외적(Cross) — 왼쪽인가 오른쪽인가

3D 외적은 두 벡터에 수직인 벡터를 만듭니다. 2D 벡터를 z = 0인 3D 벡터로 보고 외적하면 결과는 z 성분만 남습니다.

```
cross(a, b).z = a.x × b.y − a.y × b.x
```

Unity 2D 좌표(x 오른쪽, y 위쪽)에서 이 값의 부호가 뜻하는 것:

```
                 b (cross > 0)  ← a 기준 왼쪽 (반시계 방향)
                ↖
   ────────────●──────────▶ a (바라보는 방향)
                ↘
                 b (cross < 0)  ← a 기준 오른쪽 (시계 방향)

cross = 0 → 같은 직선 위 (정면 또는 정반대 — 내적 부호로 구분)
```

```csharp
float cross = facing.x * toEnemy.y - facing.y * toEnemy.x;
// 같은 값: Vector3.Cross(facing, toEnemy).z
if (cross > 0f) Debug.Log("적이 왼쪽에 있다");
```

`Vector2`에는 `Cross` 메서드가 없어서 직접 계산하거나 `Vector3.Cross`를 씁니다(이 장에서 확장 메서드로 추가합니다). 쓰임새는 "목표 쪽으로 **어느 방향으로** 돌아야 하나"입니다. 유도탄, 포탑, 적의 선회에 씁니다. 내적과 외적을 함께 쓰면 상대 위치를 네 방향(앞·뒤·왼·오)으로 나눌 수 있습니다.

| | cross > 0 (왼쪽) | cross < 0 (오른쪽) |
|---|---|---|
| **dot > 0 (앞)** | 왼쪽 앞 | 오른쪽 앞 |
| **dot < 0 (뒤)** | 왼쪽 뒤 | 오른쪽 뒤 |

### Vector2.Angle과 SignedAngle

| 메서드 | 반환 | 용도 |
|---|---|---|
| `Vector2.Angle(from, to)` | 0 ~ 180 (도) | 사이각 크기만 필요할 때 |
| `Vector2.SignedAngle(from, to)` | −180 ~ 180 (도), **반시계 방향이 양수** | 돌아야 할 방향과 양 |

```csharp
float turn = Vector2.SignedAngle(facing, toEnemy);   // 예: 30 → 왼쪽으로 30°, -30 → 오른쪽으로 30°
```

`SignedAngle`의 부호는 외적의 부호와 같습니다. 각도 자체가 필요하면 `SignedAngle`, 부호만 필요하면 외적이 가볍습니다. 방향 벡터에서 절대 각도를 얻을 때는 `Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg`(오른쪽 = 0°, 반시계 양수)를 씁니다. 투사체 스프라이트를 날아가는 방향으로 돌릴 때 사용하며, 회전 자체는 06장에서 자세히 다룹니다.

### 투영(Projection) — 한 방향 성분만 뽑기

벡터 v를 **단위 벡터** n 방향으로 투영하면 "v 중에서 n 방향 성분"이 나옵니다.

```
            v
          ↗ │
        ↗   │  ← v - proj  (n에 수직인 성분)
      ↗     │
   ●────────▶────────▶ n
   └ proj ──┘
   proj = Dot(v, n) × n        (n은 정규화되어 있어야 함)
```

```csharp
Vector2 along = Vector2.Dot(v, n) * n;   // n 방향 성분
Vector2 across = v - along;              // n에 수직인 성분
```

쓰임새:

- **벽 미끄러짐**: 이동 속도 v를 벽 법선 n에 투영한 성분을 빼면 벽을 따라 미끄러지는 속도가 남습니다.
- **측면 오프셋**: 플레이어 진행 방향 기준으로 적이 얼마나 옆으로 벗어나 있는지(`across.magnitude`).
- **넉백 분리**: 넉백을 "밀어내는 방향" 성분과 나머지로 나눠 감쇠를 따로 줄 때(07장).

`Vector3.Project(v, onNormal)`은 있지만 `Vector2`용 투영 메서드는 없어서 위처럼 직접 계산합니다.

### 반사(Reflect) — 튕겨 나가는 방향

입사 방향 d가 법선 n(정규화, 표면에서 바깥쪽)인 면에 부딪히면 반사 방향은 다음과 같습니다.

```
 d ↘       ↗ r          r = d − 2 × Dot(d, n) × n
     ↘   ↗
 ──────●────── 벽
       │ n (위쪽 법선)
```

```csharp
Vector2 r = Vector2.Reflect(d, n);
```

d에서 법선 방향 성분(투영)을 **두 번** 빼면 그 성분만 뒤집힙니다. 투영을 이해하면 반사 공식이 외울 필요 없이 나옵니다. 법선은 `RaycastHit2D.normal`이나 `Collision2D`의 접촉점 `normal`에서 얻습니다. 법선이 정규화되지 않으면 결과 길이가 틀어지니 주의하세요.

## 실습: 코인 러시에 적용하기

### 1단계: 탑다운으로 전환 준비

1. 03장의 `FallingSpawner`(GameSystems)와 `AutoShooter`(Player) 컴포넌트를 제거합니다.
2. **Coin 프리팹**: `Rigidbody2D`의 Gravity Scale을 0으로, `FallOutCleanup` 컴포넌트를 제거합니다.
3. `Hazard`, `HeavyHazard` 프리팹과 `SpikeBall`, `HeavyBall` 데이터 에셋을 삭제합니다.
4. 이 단계가 끝난 뒤 `HazardSetup.cs`, `FallingSpawner.cs`, `AutoShooter.cs`, `FallOutCleanup.cs`를 삭제합니다. 각각 이 장의 `Enemy`, `EnemySpawner`, `AutoAimWeapon`이 대체합니다. (에러가 나면 아직 참조가 남은 곳입니다.)

### 2단계: 벡터 확장 메서드 추가

01장의 `Extensions.cs`에 다음 메서드를 **추가**합니다.

```csharp
// Extensions.cs — 클래스 안에 추가

// 2D 외적의 z 성분. 양수면 other가 v의 왼쪽(반시계), 음수면 오른쪽
public static float Cross(this Vector2 v, Vector2 other)
    => v.x * other.y - v.y * other.x;

// 단위 벡터 unitAxis 방향으로의 투영
public static Vector2 ProjectOnto(this Vector2 v, Vector2 unitAxis)
    => Vector2.Dot(v, unitAxis) * unitAxis;

// 반시계 방향으로 degrees 만큼 회전 (원리는 06장)
public static Vector2 Rotated(this Vector2 v, float degrees)
{
    float rad = degrees * Mathf.Deg2Rad;
    float cos = Mathf.Cos(rad);
    float sin = Mathf.Sin(rad);
    return new Vector2(v.x * cos - v.y * sin, v.x * sin + v.y * cos);
}
```

### 3단계: PlayerMover에 바라보는 방향 추가

자동 조준은 "플레이어가 바라보는 방향"이 필요합니다. 입력이 없을 때도 마지막 방향을 유지해야 하므로, 입력이 있을 때만 갱신합니다. `PlayerMover.cs`에 프로퍼티를 추가하고 `Update`를 교체합니다.

```csharp
// PlayerMover.cs — 프로퍼티 추가
public Vector2 Facing { get; private set; } = Vector2.right;   // 항상 정규화된 값

// PlayerMover.cs — Update 교체
void Update()
{
    MoveInput = CanMove ? moveAction.ReadValue<Vector2>() : Vector2.zero;

    // 입력이 거의 없으면 마지막 방향 유지 (0 벡터를 정규화하면 방향이 사라짐)
    if (MoveInput.sqrMagnitude > 0.01f)
        Facing = MoveInput.normalized;
}
```

### 4단계: Enemy — 플레이어 추적

03장 `HazardSetup`의 역할(데이터 적용, 런타임 세트 등록, 코인 드롭)에 추적 이동을 더한 컴포넌트입니다.

```csharp
// Assets/_CoinRush/Scripts/Enemies/Enemy.cs
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D), typeof(Health), typeof(DamageOnTouch))]
public class Enemy : MonoBehaviour
{
    [SerializeField] private EnemyData data;              // 씬에 직접 배치할 때 쓰는 기본값
    [SerializeField] private HealthRuntimeSet aliveEnemies;
    [SerializeField] private Coin coinPrefab;
    [SerializeField] private SpriteRenderer sprite;
    [SerializeField] private float arriveDistance = 0.1f;

    private Rigidbody2D body;
    private Health health;
    private DamageOnTouch contact;
    private Transform target;

    public EnemyData Data => data;

    void Awake()
    {
        body = GetComponent<Rigidbody2D>();
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

    void Start()
    {
        // 스포너가 Init을 안 불렀다면(씬에 직접 배치) 태그로 한 번만 찾는다
        if (target == null)
        {
            GameObject player = GameObject.FindWithTag("Player");
            if (player != null) target = player.transform;
        }
    }

    public void Init(EnemyData newData, Transform newTarget)
    {
        target = newTarget;
        Apply(newData);
    }

    private void Apply(EnemyData newData)
    {
        data = newData;
        health.Initialize(data.maxHp);
        contact.Damage = data.contactDamage;
    }

    void FixedUpdate()
    {
        if (target == null)
        {
            body.linearVelocity = Vector2.zero;
            return;
        }

        // ① 도착 - 출발 = 적 → 플레이어
        Vector2 toTarget = (Vector2)target.position - body.position;

        // ② 거의 겹쳤으면 멈춤 (정규화할 방향이 없음). 비교는 제곱끼리
        if (toTarget.sqrMagnitude < arriveDistance * arriveDistance)
        {
            body.linearVelocity = Vector2.zero;
            return;
        }

        // ③ 방향(길이 1) × 속력 → 거리와 무관하게 일정한 속도
        Vector2 direction = toTarget.normalized;
        body.linearVelocity = direction * data.moveSpeed;

        // ④ 좌우 반전: 오른쪽(1,0)과의 내적 = direction.x. 음수면 왼쪽으로 가는 중
        if (sprite != null && Mathf.Abs(direction.x) > 0.01f)
            sprite.flipX = Vector2.Dot(direction, Vector2.right) < 0f;
    }

    private void HandleDied()
    {
        for (int i = 0; i < data.coinDrop; i++)
        {
            Vector2 offset = Random.insideUnitCircle * 0.4f;
            Instantiate(coinPrefab, body.position + offset, Quaternion.identity);
        }
        Destroy(gameObject);
    }
}
```

④에서 `Vector2.Dot(direction, Vector2.right)`는 계산하면 그냥 `direction.x`입니다. 일부러 내적으로 쓴 이유는, 기준 방향이 오른쪽이 아닌 경우(예: 적이 바라보는 방향 기준 앞뒤)에도 같은 코드 모양이 그대로 통한다는 것을 보여주기 위해서입니다.

### 5단계: EnemySpawner — 화면 밖 원 둘레에서 생성

화면(카메라가 보는 직사각형) 밖에서 생성하려면, 직사각형을 완전히 감싸는 원보다 조금 더 큰 원의 둘레를 고르면 됩니다.

```
      ┌─────────────────────┐
     ╱│      화면 (카메라)     │╲        halfH = orthographicSize
    │ │           ●──────────┼─┼──▶     halfW = halfH × aspect
    │ │         중심     halfW │ │       대각선 절반 = √(halfW² + halfH²)
     ╲└─────────────────────┘╱        반지름 = 대각선 절반 + margin
       ╲___________________╱          → 원 둘레의 모든 점은 화면 밖
```

원 둘레의 점은 **중심 + (cos θ, sin θ) × 반지름**입니다. θ를 0 ~ 2π에서 고르게 뽑으면 모든 방향에서 고르게 나옵니다.

```csharp
// Assets/_CoinRush/Scripts/Enemies/EnemySpawner.cs
using UnityEngine;

public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private EnemyData[] enemyTypes;
    [SerializeField] private Transform target;          // 플레이어
    [SerializeField] private Camera viewCamera;
    [SerializeField, Min(0.05f)] private float interval = 1.2f;
    [SerializeField, Min(0f)] private float margin = 1f;

    private float timer;

    void Update()
    {
        timer += Time.deltaTime;
        if (timer < interval) return;
        timer -= interval;

        EnemyData type = enemyTypes.PickRandom();        // 01장 확장 메서드
        GameObject go = Instantiate(type.prefab, RandomPointOutsideView(), Quaternion.identity);
        if (go.TryGetComponent(out Enemy enemy))
            enemy.Init(type, target);
    }

    private Vector2 RandomPointOutsideView()
    {
        float halfHeight = viewCamera.orthographicSize;
        float halfWidth = halfHeight * viewCamera.aspect;      // 화면 비율이 바뀌어도 대응
        float radius = Mathf.Sqrt(halfWidth * halfWidth + halfHeight * halfHeight) + margin;

        float angle = Random.Range(0f, Mathf.PI * 2f);         // 라디안
        Vector2 direction = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));   // 길이 1

        Vector2 center = viewCamera.transform.position;        // 카메라 중심 기준
        return center + direction * radius;                    // 위치 + 방향 × 거리 = 위치
    }

    void OnDrawGizmosSelected()
    {
        if (viewCamera == null) return;
        float halfHeight = viewCamera.orthographicSize;
        float halfWidth = halfHeight * viewCamera.aspect;
        float radius = Mathf.Sqrt(halfWidth * halfWidth + halfHeight * halfHeight) + margin;
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(viewCamera.transform.position, radius);
    }
}
```

플레이어 위치가 아니라 **카메라 중심**을 기준으로 한 점에 주목하세요. 지금은 카메라가 고정이고 플레이어는 화면 안 어디든 갈 수 있으므로, 플레이어 중심 원은 화면 안쪽을 지날 수 있습니다. 06장에서 카메라가 플레이어를 따라가게 되어도 이 코드는 그대로 맞습니다.

`Random.insideUnitCircle.normalized`로 방향을 뽑는 방법도 있지만, 드물게 (0, 0)이 나오면 정규화 결과가 0 벡터가 되어 적이 화면 중앙에 생깁니다. 각도에서 만드는 방식이 안전합니다.

### 6단계: AutoAimWeapon — 시야각 안의 가장 가까운 적

```csharp
// Assets/_CoinRush/Scripts/Weapons/AutoAimWeapon.cs
using Unity.Profiling;
using UnityEngine;

public class AutoAimWeapon : MonoBehaviour
{
    // 탐색 부분만 따로 측정하기 위한 마커 (발사 시 Instantiate 할당과 구분)
    private static readonly ProfilerMarker FindTargetMarker = new ProfilerMarker("AutoAimWeapon.FindTarget");

    [SerializeField] private WeaponData weapon;
    [SerializeField] private PlayerMover mover;
    [SerializeField] private HealthRuntimeSet targets;
    [SerializeField, Min(0.1f)] private float range = 7f;
    [SerializeField, Range(1f, 360f)] private float viewAngle = 120f;

    private float cooldownLeft;

    void Update()
    {
        cooldownLeft -= Time.deltaTime;
        if (cooldownLeft > 0f) return;

        // 대상이 없으면 쿨다운을 소모하지 않고 다음 프레임에 다시 찾는다
        if (!TryFindTarget(out Vector2 aimDirection)) return;

        cooldownLeft = weapon.cooldown;
        Projectile shot = Instantiate(weapon.projectilePrefab, transform.position, Quaternion.identity);
        shot.Launch(aimDirection, weapon.projectileSpeed, weapon.damage);
    }

    private bool TryFindTarget(out Vector2 aimDirection)
    {
        using var _ = FindTargetMarker.Auto();   // 메서드가 끝날 때 측정 종료

        Vector2 origin = transform.position;
        Vector2 facing = mover.Facing;                                 // 이미 정규화됨
        float cosHalfAngle = Mathf.Cos(viewAngle * 0.5f * Mathf.Deg2Rad);
        float rangeSqr = range * range;

        float bestSqr = float.MaxValue;
        aimDirection = Vector2.zero;

        // IReadOnlyList는 foreach 대신 for (02장: 열거자 박싱 방지)
        for (int i = 0; i < targets.Count; i++)
        {
            Vector2 toTarget = (Vector2)targets.Items[i].transform.position - origin;
            float distSqr = toTarget.sqrMagnitude;

            // 1) 사거리 밖이거나, 이미 찾은 적보다 멀면 건너뜀 — 제곱근 없이 비교
            if (distSqr > rangeSqr || distSqr >= bestSqr || distSqr < 0.0001f) continue;

            // 2) 시야각: 정규화된 두 벡터의 내적 = cos(사이각)
            Vector2 dirToTarget = toTarget / Mathf.Sqrt(distSqr);     // normalized와 같음
            if (Vector2.Dot(facing, dirToTarget) < cosHalfAngle) continue;

            bestSqr = distSqr;
            aimDirection = dirToTarget;
        }

        return bestSqr < float.MaxValue;
    }

    void OnDrawGizmosSelected()
    {
        if (mover == null) return;
        Vector2 origin = transform.position;
        Vector2 facing = mover.Facing;
        Vector2 left = facing.Rotated(viewAngle * 0.5f) * range;
        Vector2 right = facing.Rotated(-viewAngle * 0.5f) * range;

        Gizmos.color = Color.cyan;
        Gizmos.DrawLine(origin, origin + left);
        Gizmos.DrawLine(origin, origin + right);
        Gizmos.DrawLine(origin, origin + facing * range);
    }
}
```

루프의 검사 순서가 성능에 영향을 줍니다. **싼 검사(제곱 거리 비교)를 먼저, 비싼 검사(제곱근·내적)를 나중에** 해서 대부분의 적을 일찍 걸러냅니다. `viewAngle`이 360이면 `cos 180° = −1`이라 모든 방향이 통과하므로 "전방위 조준"도 같은 코드로 됩니다.

### 7단계: 투사체를 날아가는 방향으로 돌리기

03장 `Projectile.cs`의 `Launch` 메서드를 교체합니다.

```csharp
// Projectile.cs — Launch 교체
public void Launch(Vector2 direction, float speed, int damageAmount)
{
    damage = damageAmount;
    Vector2 dir = direction.normalized;
    body.linearVelocity = dir * speed;

    // 방향 벡터 → 각도(도). 오른쪽이 0°, 반시계가 양수. 스프라이트가 오른쪽을 보고 그려져 있어야 함
    float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
    transform.rotation = Quaternion.Euler(0f, 0f, angle);

    Destroy(gameObject, lifetime);
}
```

원형 투사체는 돌려도 티가 안 나므로, Projectile 프리팹의 스프라이트 Scale을 (0.4, 0.15)처럼 가로로 길게 바꾸면 방향이 보입니다.

### 8단계: 적 프리팹·데이터·씬 조립

1. **Slime 프리팹**: 2D Object → Sprites → Circle, 초록, Scale 0.6, Layer `Enemy`.
   - `Circle Collider 2D`(Is Trigger)
   - `Rigidbody2D`: Body Type **Dynamic**, Gravity Scale **0**, Constraints → Freeze Rotation Z
   - `Health`, `DamageOnTouch`(Target Layers `Player`, **Destroy Self On Hit 해제**)
   - `Enemy`: Alive Enemies = `AliveEnemies`, Coin Prefab = Coin, Sprite = 자기 SpriteRenderer
2. Slime을 복제해 **Bat 프리팹**(보라, Scale 0.45)을 만듭니다.
3. **Data** 폴더에 에셋을 만듭니다.

| 에셋 | displayName | maxHp | contactDamage | moveSpeed | coinDrop | prefab |
|---|---|---|---|---|---|---|
| `Slime` | 슬라임 | 3 | 1 | 1.6 | 1 | Slime |
| `Bat` | 박쥐 | 1 | 1 | 3.2 | 1 | Bat |

4. **GameSystems**에 `EnemySpawner` 추가: Enemy Types = Slime, Bat / Target = Player / View Camera = Main Camera.
5. **Player**에 `AutoAimWeapon` 추가: Weapon = `BasicShot`, Mover = Player, Targets = `AliveEnemies`.
6. `GameStateMachine`의 Gameplay Behaviours를 `EnemySpawner`, `AutoAimWeapon`, `CoinMagnet`으로, `PlayerStateController`의 Disable On Death를 `AutoAimWeapon`, `CoinMagnet`으로 바꿉니다. (빈 칸(Missing)이 남아 있으면 `NullReferenceException`이 납니다.) Gameplay Behaviours에 `AutoAimWeapon`이 빠지면 레벨업 창 뒤에서도 조준·발사가 계속되니 꼭 넣습니다. `AutoAimWeapon.Update`는 `timeScale`을 보지 않으므로, 멈춤은 상태 머신이 컴포넌트를 꺼서 보장합니다.
7. Main Camera가 Orthographic, Size 5, 위치 (0, 0, -10)인지 확인합니다. `PlayerMover`의 Bounds가 화면과 대략 맞는지도 봅니다(16:9 기준 가로 절반 약 8.9).

### 확인하기

- ▶ Play → 시작 → 화면 밖 사방에서 슬라임(느림)과 박쥐(빠름)가 나타나 플레이어 쪽으로 **일정한 속도로** 다가온다. 가까워져도 느려지지 않는다.
- GameSystems를 선택하면 Scene 뷰에 빨간 원이 화면 직사각형을 감싸고 있고, 적은 항상 그 원 위에서 생긴다.
- 적이 왼쪽으로 이동할 때 스프라이트가 뒤집힌다(원형이면 티가 안 나니 비대칭 스프라이트로 확인).
- Player를 선택하면 청록색 부채꼴이 보인다. 이동 방향을 바꾸면 부채꼴이 따라 돌고, 멈춰도 마지막 방향을 유지한다.
- 부채꼴 **뒤쪽**에 있는 적에게는 쏘지 않고, 부채꼴 안의 **가장 가까운** 적에게 길쭉한 탄이 그 방향으로 누운 채 날아간다.
- 적이 죽으면 코인이 제자리에 흩어지고(떨어지지 않음), 자석으로 빨려 온다. 레벨업·결과 흐름은 04장과 같다.
- Profiler에서 `AutoAimWeapon.FindTarget` 마커와 `Enemy.FixedUpdate`의 GC Alloc이 0이다. 발사하는 프레임의 `AutoAimWeapon.Update`에는 `Instantiate`(새 투사체와 그 컴포넌트의 C# 객체)와 `Destroy` 때문에 할당이 보이는 것이 정상입니다. 이 생성 비용은 따로 기록해 두고, 발사 경로 전체의 무할당은 12장 오브젝트 풀 적용 뒤에 확인합니다.
- 레벨업 창이 떠 있는 동안 방향키로 방향을 바꿔도 발사되지 않는다(04장 `LevelUpState.Enter`가 무기와 이동 입력을 끈다).

## 흔한 실수

1. **적이 멀리서는 빠르고 가까이 오면 느려진다 (또는 반대로 도망간다)**
   원인: 정규화하지 않은 `target - position`에 속력을 곱했거나, 뺄셈 순서를 뒤집었습니다.
   해결: `(도착 - 출발).normalized * speed`. 순서는 "도착에서 출발을 뺀다".
2. **적이 플레이어 위에 겹치면 부르르 떨거나 사라진 듯 멈춘다**
   원인: 길이 0에 가까운 벡터를 정규화했거나, 목표를 지나치고 되돌아오기를 반복합니다.
   해결: `sqrMagnitude < arriveDistance²`면 멈추는 도착 판정을 둡니다. 비교할 때 한쪽만 제곱하는 실수(`sqrMagnitude < arriveDistance`)도 흔합니다.
3. **시야각 판정이 이상하다 — 거의 모든 적이 통과하거나 아무도 안 걸린다**
   원인: `Mathf.Cos`에 도(degree)를 넣었거나, 시야각 전체(120°)의 코사인을 썼거나, 한쪽 벡터를 정규화하지 않았습니다.
   해결: `Mathf.Cos(viewAngle * 0.5f * Mathf.Deg2Rad)`, 내적의 두 벡터 모두 단위 벡터인지 확인합니다.
4. **적이 화면 안에서 갑자기 생긴다**
   원인: 반지름을 `orthographicSize`만으로 잡아 가로 방향이 모자라거나, 원점(0,0) 또는 플레이어를 중심으로 잡았습니다.
   해결: `√(halfW² + halfH²) + margin`, 중심은 카메라 위치. 화면 비율이 바뀌는 기기(태블릿)에서도 확인합니다.
5. **플레이어가 적 안에 서 있어도 더 이상 피해를 받지 않는다**
   원인: `DamageOnTouch`는 `OnTriggerEnter2D`라 **들어오는 순간 한 번**만 피해를 줍니다. 무적 시간이 끝난 뒤에도 계속 겹쳐 있으면 새 Enter가 없습니다.
   해결: 연습 문제 3처럼 `OnTriggerStay2D`와 간격 타이머로 "접촉 중 지속 피해"를 구현합니다.

## 연습 문제

**1. ★☆☆ 손으로 계산하기**
플레이어가 `facing = (0, 1)`(위쪽)을 보고 있습니다. 적 A는 플레이어 기준 `(3, 3)`, 적 B는 `(-1, -2)`에 있습니다. 각 적에 대해 (1) 앞/뒤, (2) 왼쪽/오른쪽, (3) 시야각 90°(절반 45°) 안에 있는지 판정하세요.

<details><summary>힌트·해설</summary>

A: dot = 0×3 + 1×3 = 3 > 0 → **앞**. cross = 0×3 − 1×3 = −3 < 0 → **오른쪽**. 정규화 A = (0.707, 0.707), dot = 0.707, cos 45° ≈ 0.707 → **경계선 위**. 이 장의 코드는 `>=`로 경계를 **포함**하는 정책입니다.

경계는 피할 대상이 아니라 반드시 확인할 대상입니다. 다만 `float` 계산에서는 정확히 경계인 경우 내적과 `cosHalf`가 마지막 자리에서 달라져 결과가 흔들릴 수 있습니다. 그래서 정책을 정하고 작은 허용오차로 고정합니다: `Vector2.Dot(facing, dir) >= cosHalfAngle - 1e-5f`. 테스트할 때는 경계 **바로 안**(44°), **바로 밖**(46°), **정확한 경계**(45° — 허용오차 덕분에 포함), 그리고 **영벡터**(적이 플레이어와 같은 위치 — `distSqr < 0.0001f`로 제외)를 모두 확인하세요.
B: dot = −2 < 0 → **뒤**. cross = 0×(−2) − 1×(−1) = 1 > 0 → **왼쪽**. 뒤에 있으므로 시야각 밖.
</details>

**2. ★☆☆ 백어택 치명타**
적이 플레이어를 **뒤에서** 쳤을 때 피해 2배가 되게 하세요. "뒤"는 플레이어의 `Facing`과 "플레이어 → 적" 방향의 내적이 −0.3보다 작을 때입니다.

<details><summary>힌트·해설</summary>

`DamageOnTouch`는 누가 맞는지 모르는 범용 컴포넌트이므로, 플레이어 쪽에서 계산하는 편이 깔끔합니다. 예: `PlayerMover`를 아는 `BackstabRule` 컴포넌트를 만들고, `DamageOnTouch`에 선택적 `System.Func<Collider2D, int, int> modifyDamage` 같은 확장점을 두는 대신, 간단히는 적의 `DamageOnTouch.OnTriggerEnter2D`에서 `other.TryGetComponent(out PlayerMover mover)`로 확인해 배율을 적용합니다.

```csharp
Vector2 playerToEnemy = (Vector2)transform.position - (Vector2)other.transform.position;
bool fromBehind = Vector2.Dot(mover.Facing, playerToEnemy.normalized) < -0.3f;
int finalDamage = fromBehind ? damage * 2 : damage;
```

뺄셈 방향("플레이어 → 적" = 적 − 플레이어)과, −0.3이 몇 도에 해당하는지(약 107°보다 뒤) 설명할 수 있으면 성공입니다.
</details>

**3. ★★☆ 접촉 중 지속 피해**
흔한 실수 5를 해결하세요. 적과 겹쳐 있는 동안 일정 간격마다 피해를 주도록 01장의 `DamageOnTouch`에 **반복 간격 옵션**을 추가하세요. `Enemy`는 `DamageOnTouch`를 필수 컴포넌트로 요구하고 `EnemyData.contactDamage`를 `Damage` 프로퍼티로 넣어 주므로, 컴포넌트를 새로 만들어 바꿔 끼우지 말고 기존 컴포넌트를 확장해야 `Enemy` 코드를 고치지 않아도 됩니다.

<details><summary>힌트·해설</summary>

`OnTriggerStay2D`는 겹쳐 있는 동안 물리 스텝마다 호출됩니다. 피해 간격은 `Time.time` 기준 다음 시각을 저장해 비교합니다. `repeatInterval`의 기본값을 0(= 들어올 때 한 번만, 01장과 같은 동작)으로 두면 기존 프리팹은 그대로 동작합니다. 플레이어의 무적 시간(0.8초)이 있으므로 적 프리팹에서는 그보다 약간 길게(예: 1초) 잡으면 자연스럽습니다.

`DamageOnTouch.cs` 전체를 다음으로 교체합니다(공개 멤버 `Damage`는 그대로).

```csharp
// Assets/_CoinRush/Scripts/Combat/DamageOnTouch.cs
using UnityEngine;

public class DamageOnTouch : MonoBehaviour
{
    [SerializeField, Min(0)] private int damage = 1;
    [SerializeField] private LayerMask targetLayers;
    [SerializeField] private bool destroySelfOnHit = true;
    [SerializeField, Min(0f)] private float repeatInterval = 0f;   // 0이면 들어올 때 한 번만

    private float nextDamageTime;

    public int Damage
    {
        get => damage;
        set => damage = Mathf.Max(0, value);
    }

    void OnTriggerEnter2D(Collider2D other) => TryHit(other);

    void OnTriggerStay2D(Collider2D other)
    {
        if (repeatInterval > 0f && Time.time >= nextDamageTime)
            TryHit(other);
    }

    private void TryHit(Collider2D other)
    {
        if (!targetLayers.Contains(other.gameObject.layer)) return;
        if (!other.TryGetComponent(out IDamageable target)) return;

        target.TakeDamage(damage);
        nextDamageTime = Time.time + repeatInterval;
        if (destroySelfOnHit) Destroy(gameObject);
    }
}
```

에디터 작업: Slime·Bat 프리팹의 `DamageOnTouch`에서 **Repeat Interval**을 1로 설정합니다. 피해량은 지금처럼 `Enemy.Apply`가 `EnemyData.contactDamage`를 `Damage`에 넣어 주므로 데이터 에셋의 값이 그대로 쓰입니다. 적 한 마리가 여러 대상에 닿는 게임이라면 `nextDamageTime`을 대상별로(`Dictionary<Collider2D, float>`) 관리해야 하지만, 코인 러시에서 적의 대상은 플레이어 하나뿐이라 필드 하나로 충분합니다.

Rigidbody2D의 Sleeping Mode가 기본(Start Awake)이면 움직이지 않는 두 물체는 잠들어 Stay가 멈출 수 있습니다. 적은 계속 움직이므로 보통 문제없지만, 멈춰 있는 함정에 쓸 때는 Sleeping Mode를 Never Sleep으로 둡니다. 07장에서 물리 설정을 자세히 봅니다.
</details>

**4. ★★☆ 벽에 튕기는 탄**
화면 경계(`PlayerMover`의 bounds와 같은 직사각형)에 닿으면 `Vector2.Reflect`로 튕기고, 최대 2번까지 튕긴 뒤 사라지는 `BouncingProjectile`을 만드세요. 물리 콜라이더 없이 좌표 비교로 구현합니다.

<details><summary>힌트·해설</summary>

`FixedUpdate`에서 위치가 경계를 넘었는지 검사합니다. 오른쪽 벽을 넘었으면 법선은 `Vector2.left`, 위쪽 벽이면 `Vector2.down`입니다(법선은 **벽에서 안쪽**을 향함).

```csharp
Vector2 p = body.position;
Vector2 normal = Vector2.zero;
if (p.x > max.x) normal = Vector2.left;
else if (p.x < min.x) normal = Vector2.right;
else if (p.y > max.y) normal = Vector2.down;
else if (p.y < min.y) normal = Vector2.up;

if (normal != Vector2.zero)
{
    if (bouncesLeft-- <= 0) { Destroy(gameObject); return; }
    body.linearVelocity = Vector2.Reflect(body.linearVelocity, normal);
    body.position = p.ClampTo(min, max);   // 벽 밖에 머물러 다음 스텝에 또 반사되는 것 방지
    // 7단계처럼 새 방향으로 회전도 갱신
}
```

위치를 경계 안으로 되돌리지 않으면 벽 밖에 있는 동안 매 스텝 반사되어 떨리는 버그가 납니다.
</details>

**5. ★★★ 선회 속도 제한 유도탄 (스스로 확장)**
발사 후 가장 가까운 적을 향해 방향을 틀되, 초당 최대 180°까지만 회전하는 유도탄을 만드세요. 목표가 죽으면 새 목표를 찾고, 없으면 직진합니다. 외적(또는 `SignedAngle`)으로 회전 방향을 정하세요.

<details><summary>힌트·해설</summary>

- 매 `FixedUpdate`: 현재 진행 방향 `forward`(속도 정규화)와 목표 방향 `toTarget.normalized`의 부호 있는 각 `float angle = Vector2.SignedAngle(forward, toTarget);`
- 이번 스텝 최대 회전량 `float maxStep = turnSpeed * Time.fixedDeltaTime;` → `float step = Mathf.Clamp(angle, -maxStep, maxStep);`
- `forward = forward.Rotated(step);` → `body.linearVelocity = forward * speed;` 스프라이트 회전 갱신.
- 외적 버전: `float side = forward.Cross(toTarget);`로 부호만 구하고 `step = Mathf.Sign(side) * Mathf.Min(maxStep, Vector2.Angle(forward, toTarget))`.
- 목표는 `HealthRuntimeSet`에서 찾고, 목표의 `Health`가 `null`(파괴됨)인지 매 스텝 확인합니다.
- 확장: 회전 속도가 느리면 목표 주위를 영원히 도는 "궤도 문제"가 생깁니다. 거리가 가까울수록 회전 속도를 올리거나 수명을 두는 방법을 실험해 보세요. 06장의 보간과 연결됩니다.
</details>

## 셀프 체크

**1. `target.position - transform.position`에 속력을 곱해 적을 움직이면 어떤 문제가 생기고, 어떻게 고치나요?**

<details><summary>모범 답안</summary>

뺄셈 결과는 방향과 거리를 함께 담고 있어, 멀면 빠르고 가까우면 느려집니다. `normalized`로 길이 1의 방향만 남긴 뒤 속력을 곱해야 거리와 무관하게 일정한 속도가 됩니다. 거의 겹친 경우에는 정규화할 방향이 없으므로 도착 판정을 먼저 둡니다.
</details>

**2. 거리 비교에 `magnitude` 대신 `sqrMagnitude`를 쓸 수 있는 이유와 주의점은?**

<details><summary>모범 답안</summary>

거리는 0 이상이므로 a < b와 a² < b²가 같은 결과를 줍니다. 그래서 제곱근 계산 없이 비교할 수 있습니다. 주의점은 비교 대상도 제곱해야 한다는 것입니다(`sqrMagnitude < range * range`). 실제 거리 값이 필요한 곳(표시, 비례 계산)에는 `magnitude`를 씁니다.
</details>

**3. 시야각 120° 판정을 내적으로 구현하는 과정을 설명해 보세요.**

<details><summary>모범 답안</summary>

바라보는 방향과 대상 방향을 모두 정규화하면 내적이 두 벡터 사이각의 코사인이 됩니다. 시야각의 절반 60°의 코사인 0.5를 미리 계산하고(`Mathf.Cos(60 * Deg2Rad)`), 내적이 0.5 이상이면 사이각이 60° 이하이므로 시야 안입니다. 각이 커질수록 코사인이 작아지므로 부등호가 "이상"이 됩니다.
</details>

**4. 2D에서 외적의 z 성분 부호가 무엇을 뜻하나요? 내적과 함께 쓰면 무엇을 알 수 있나요?**

<details><summary>모범 답안</summary>

`a.x*b.y - a.y*b.x`가 양수면 b가 a 기준 반시계 방향(왼쪽), 음수면 시계 방향(오른쪽), 0이면 같은 직선 위입니다. 내적 부호(앞/뒤)와 함께 쓰면 상대 위치를 왼쪽 앞·오른쪽 앞·왼쪽 뒤·오른쪽 뒤로 나눌 수 있고, 목표를 향해 어느 방향으로 회전해야 하는지 알 수 있습니다.
</details>

**5. 반사 공식 `r = d − 2(d·n)n`을 투영으로 설명해 보세요.**

<details><summary>모범 답안</summary>

`(d·n)n`은 입사 방향 d를 법선 n에 투영한 성분, 즉 벽을 향해 들어가는 성분입니다. 이를 한 번 빼면 벽을 따라가는 성분만 남고(미끄러짐), 두 번 빼면 법선 성분의 부호가 뒤집혀 벽에서 튕겨 나가는 방향이 됩니다. n이 정규화되어 있어야 투영 길이가 맞습니다.
</details>

## 핵심 요약

- 위치와 방향은 같은 타입이지만 다른 개념입니다. 위치 − 위치 = 방향, 위치 + 방향 = 위치.
- "A에서 B로" = B − A. 이동은 `방향.normalized * 속력`, 도착 판정은 `sqrMagnitude < r²`.
- 거리 비교는 `sqrMagnitude`, 실제 거리는 `magnitude`, 방향만은 `normalized`.
- 정규화된 두 벡터의 내적 = cos(사이각). 부호로 앞/뒤, 코사인 임계값으로 시야각을 판정합니다.
- 2D 외적 z = `a.x*b.y − a.y*b.x`. 부호로 왼쪽(+)/오른쪽(−)을 판정하고, `SignedAngle`의 부호와 같습니다.
- 투영 `Dot(v, n) * n`은 한 방향 성분을 뽑고, 반사는 법선 성분을 두 번 빼서 뒤집은 것입니다.
- 루프에서는 싼 검사(제곱 거리)를 먼저, 비싼 검사(제곱근·내적)를 나중에 합니다.
- 코인 러시는 이제 원형 스폰 → 추적하는 적 → 시야각 자동 조준으로 돌아가는 서바이버라이크입니다.

## 더 읽을거리

- Unity Scripting API, `Vector2` — https://docs.unity3d.com/ScriptReference/Vector2.html
- Unity Learn, "Vector Maths" 관련 튜토리얼 (Unity Learn에서 "vector" 검색)
- Freya Holmér, "Math for Game Devs" 강의 시리즈 (YouTube) — 벡터·내적·외적을 그림으로 설명
- 3Blue1Brown, "Essence of Linear Algebra" (YouTube) — 내적·외적의 기하학적 의미
