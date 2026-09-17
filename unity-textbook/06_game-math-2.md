# 06. 게임 수학 2 — 회전·보간·이징·확률

> **이 장에서 배울 것**
> - 오일러 각과 쿼터니언의 차이를 설명하고, 2D에서는 z각도 하나로 회전을 다룰 수 있는 이유를 설명할 수 있다
> - `Mathf.Atan2`와 `Quaternion` 도우미로 "방향 → 회전"을 변환한다
> - `Lerp`·`MoveTowards`·`SmoothDamp`의 차이를 설명하고, 프레임 속도에 독립적인 감쇠(`1 - exp(-k·dt)`)를 구현한다
> - 이징 함수와 `AnimationCurve`, 삼각함수로 움직임에 성격을 입힌다
> - 가중치 랜덤·셔플백·시드 난수를 구현하고 용도에 맞게 고른다
>
> **선수 장**: 01, 03, 05 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 부드럽게 따라오는 카메라, 플레이어 주위를 도는 오브 무기, 적이 죽을 때 가중치 테이블로 떨어지는 아이템

## 왜 필요한가

05장까지 만든 코인 러시는 "움직이긴 하는데 딱딱한" 상태입니다. 구체적으로 세 군데가 어색합니다.

1. **카메라**: `Main Camera`를 플레이어의 자식으로 넣었거나, 매 프레임 `camera.position = player.position`으로 붙여 놨습니다. 플레이어가 방향을 틀 때마다 화면 전체가 칼같이 튀어서 멀미가 납니다. 인터넷에서 찾은 `Vector3.Lerp(cam, target, 5f * Time.deltaTime)`을 넣으면 부드러워지긴 하는데, **144Hz 모니터에서 테스트한 친구는 "카메라가 더 느리다"** 고 말합니다.
2. **무기**: 서바이버라이크의 상징인 "플레이어 주위를 도는 구슬"을 만들려는데, 원 위의 점을 어떻게 구하는지, 구슬이 진행 방향을 바라보게 하려면 회전을 어떻게 넣는지 막힙니다. `transform.right = dir`로 해봤더니 가끔 스프라이트가 **뒤집힌 채로** 돕니다.
3. **드롭**: 적이 죽으면 `Random.Range(0, 3)`으로 아이템을 고르는데, 기획자가 "코인 70%, 경험치 보석 25%, 자석 5%로 해 주세요"라고 하면 코드를 `if` 사다리로 다시 짜야 합니다. 게다가 `Random.Range(0, items.Length - 1)`로 썼더니 **마지막 아이템이 절대 안 나오는** 버그도 숨어 있습니다.

이 장은 이 세 가지를 고치면서 회전·보간·이징·확률이라는, 게임 코드에서 매일 쓰는 수학 도구를 정리합니다. 원리는 "쓸 수 있을 만큼만" 다룹니다.

## 개념

### 회전 표현 1 — 오일러 각

Inspector의 Transform에 보이는 `Rotation (x, y, z)`가 **오일러 각**입니다. "x축으로 몇 도, y축으로 몇 도, z축으로 몇 도"를 순서대로 적용한다는 뜻입니다. 사람이 읽기 쉽고 입력하기 쉽습니다.

문제는 3D에서 세 축을 조합할 때 생깁니다.

- **짐벌락(gimbal lock)**: 축 하나가 90도가 되면 나머지 두 축이 같은 방향을 가리키게 되어, 회전 자유도 하나가 사라집니다. 비행기가 수직으로 기수를 올렸을 때 "좌우 선회"와 "롤"이 같은 움직임이 되는 상황입니다.
- **보간이 이상함**: (0, 0, 0)에서 (0, 350, 0)으로 Lerp하면 10도만 돌면 될 것을 350도를 빙 돌아갑니다. 같은 자세를 나타내는 오일러 값이 여러 개라서 생기는 일입니다.
- **읽은 값이 입력한 값과 다름**: `transform.eulerAngles`를 읽으면 내가 넣은 (0, -30, 0) 대신 (0, 330, 0)이 나옵니다. 내부 저장은 쿼터니언이고, 오일러는 읽을 때 매번 역계산하기 때문입니다.

### 회전 표현 2 — 쿼터니언

Unity는 회전을 내부적으로 **쿼터니언**(`Quaternion`, 숫자 4개 x, y, z, w)으로 저장합니다. 쿼터니언은 "어떤 축을 중심으로 몇 도 돌렸는가"를 압축한 표현이라서 짐벌락이 없고, 두 자세 사이를 가장 짧은 경로로 보간(`Slerp`)할 수 있습니다.

원리(4차원 복소수)는 몰라도 됩니다. **x, y, z, w를 직접 만지지 말고, 아래 생성 함수만 쓰면 됩니다.**

| 함수 | 의미 | 주 용도 |
|---|---|---|
| `Quaternion.identity` | 회전 없음 | `Instantiate(prefab, pos, Quaternion.identity)` |
| `Quaternion.Euler(x, y, z)` | 오일러 각 → 쿼터니언 | 2D에서 `Quaternion.Euler(0, 0, angle)` |
| `Quaternion.AngleAxis(angle, axis)` | 축을 중심으로 angle도 | `AngleAxis(angle, Vector3.forward)` (2D와 동일 효과) |
| `Quaternion.LookRotation(forward, up)` | forward를 바라보는 자세 | 3D 캐릭터·카메라가 목표를 바라보기 |
| `Quaternion.Slerp(a, b, t)` | 구면 보간 | 자세를 부드럽게 전환 |
| `Quaternion.RotateTowards(a, b, maxDeg)` | 최대 maxDeg도만 회전 | 포탑이 초당 N도로 회전 |
| `q1 * q2` | 회전 합성 (q2 적용 후 q1) | 로컬 회전 누적 |
| `q * vector` | 벡터를 회전 | 방향 벡터를 30도 돌리기 |

```csharp
// 3D 참고: 적이 플레이어를 바라보게 (코인 러시는 2D라 쓰지 않음)
Vector3 toPlayer = player.position - transform.position;
transform.rotation = Quaternion.LookRotation(toPlayer, Vector3.up);

// 벡터 회전: 오른쪽 방향을 z축 기준 30도 돌린 방향
Vector3 dir = Quaternion.Euler(0f, 0f, 30f) * Vector3.right;
```

### 2D에서는 z각도 하나면 충분한 이유

2D 게임의 오브젝트는 XY 평면 위에서만 돕니다. 회전축이 항상 화면을 뚫고 나오는 **z축 하나**뿐이므로, 짐벌락(축이 3개일 때의 문제)이 원천적으로 생기지 않습니다. 그래서 2D에서는 회전을 `float angle` 하나(도 단위)로 들고 있다가, 적용할 때만 `Quaternion.Euler(0, 0, angle)`로 바꾸면 됩니다.

주의할 점은 **각도의 순환**뿐입니다. 350도와 -10도는 같은 방향입니다. 각도끼리 빼거나 보간할 때는 아래 함수를 씁니다.

| 함수 | 하는 일 |
|---|---|
| `Mathf.DeltaAngle(a, b)` | a에서 b까지 가장 짧은 각도 차 (-180~180) |
| `Mathf.LerpAngle(a, b, t)` | 360도 경계를 넘는 짧은 쪽으로 보간 |
| `Mathf.MoveTowardsAngle(a, b, maxDelta)` | 짧은 쪽으로 최대 maxDelta도 이동 |
| `Vector2.SignedAngle(from, to)` | 두 벡터 사이 부호 있는 각도 (반시계 +) |

```csharp
float a = Mathf.Lerp(350f, 10f, 0.5f);      // 180 — 반대편으로 돌아감 (버그)
float b = Mathf.LerpAngle(350f, 10f, 0.5f); // 0 (=360) — 짧은 쪽 (정답)
```

### Mathf.Atan2 — 방향 벡터를 각도로

05장에서 "적 → 플레이어" 방향 벡터 `dir`을 구했습니다. 이 방향을 바라보게 하려면 벡터를 각도로 바꿔야 합니다. 그 함수가 `Mathf.Atan2(y, x)`입니다.

```
        y
        ↑        dir = (x, y)
        |       ╱
        |     ╱
        |   ╱  θ = Atan2(y, x)   (라디안, -π ~ π)
        | ╱ )
  ──────●────────→ x      θ = 0 은 오른쪽(+x), 반시계가 +
```

```csharp
Vector2 dir = (target - (Vector2)transform.position);
float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;   // 인자 순서: y 먼저!
transform.rotation = Quaternion.Euler(0f, 0f, angle);
```

- **인자 순서가 (y, x)** 입니다. `Atan2(x, y)`로 쓰면 90도 틀어집니다.
- 결과는 **라디안**이므로 `Mathf.Rad2Deg`(= 180/π)를 곱합니다.
- `Atan(y / x)`가 아니라 `Atan2`를 쓰는 이유: x가 0이면 나눗셈이 터지고, (1,1)과 (-1,-1)을 구분하지 못합니다. `Atan2`는 사분면을 알아서 판단합니다.
- 각도 0은 **오른쪽**입니다. 스프라이트가 위쪽을 보도록 그려졌다면 `angle - 90f`를 적용합니다.

반대 방향(각도 → 벡터)은 삼각함수로 구합니다.

```csharp
float rad = angleDeg * Mathf.Deg2Rad;
Vector2 dir = new Vector2(Mathf.Cos(rad), Mathf.Sin(rad));   // 길이 1인 방향
```

> **`transform.right = dir`의 함정**: 2D에서 편해 보이지만 내부적으로 `Quaternion.FromToRotation(Vector3.right, dir)`을 씁니다. dir이 정확히 왼쪽(-x)이면 "180도 회전"의 축이 여러 개라서 y축으로 뒤집히는 경우가 생깁니다. 스프라이트가 뒤집혀 보이거나 정렬이 깨지면 `Atan2` + `Euler(0, 0, angle)`로 바꾸세요.

### 보간 3형제 — Lerp, MoveTowards, SmoothDamp

"현재값을 목표값으로 옮긴다"는 일은 같지만 움직임의 성격이 다릅니다.

| 함수 | 공식(개념) | 움직임 | 도착 | 적합한 곳 |
|---|---|---|---|---|
| `Lerp(a, b, t)` | `a + (b - a) * t` | t가 고정이면 "남은 거리의 일정 비율" → 감속 | 이론상 영원히 도착 안 함 | 정해진 시간 동안의 트윈(t를 0→1로 증가) |
| `MoveTowards(a, b, maxDelta)` | 최대 maxDelta만큼 등속 이동 | 등속, 도착 시 딱 멈춤 | 정확히 도착 | 가속도 제한, 체력바 줄어듦, 쿨다운 |
| `SmoothDamp(a, b, ref vel, smoothTime)` | 임계 감쇠 스프링 | 가속 후 감속, 속도 연속 | 거의 도착 (오버슈트 없음) | 카메라 추적, UI 따라가기 |

`Lerp`에는 두 가지 사용법이 있고, 이 둘을 섞으면 버그가 납니다.

```csharp
// 사용법 A — "시간 기반 트윈": a, b는 고정, t가 0→1로 증가. 프레임 독립적.
elapsed += Time.deltaTime;
float t = Mathf.Clamp01(elapsed / duration);
transform.position = Vector3.Lerp(startPos, endPos, t);

// 사용법 B — "지수 감쇠": a가 매 프레임 갱신됨, t는 작은 상수. 프레임 의존적(!)
transform.position = Vector3.Lerp(transform.position, target, 0.1f);
```

### "lerp with deltaTime" 함정과 프레임 독립 감쇠

사용법 B를 고친다며 흔히 쓰는 코드가 이것입니다.

```csharp
transform.position = Vector3.Lerp(transform.position, target, sharpness * Time.deltaTime); // 여전히 틀림
```

`0.1f`보다는 낫지만 **여전히 프레임 속도에 따라 결과가 달라집니다.** 한 프레임에 "남은 거리의 `k·dt`만큼 줄인다"를 N번 반복하면 남는 비율은 `(1 - k·dt)^N`인데, 이 값은 dt를 잘게 나눌수록 달라집니다. `k = 6`, 0.5초 뒤 남은 거리를 계산하면 이렇습니다.

| FPS | 프레임 수 | `Lerp(k·dt)` 남은 거리 | `1 - exp(-k·dt)` 남은 거리 |
|---|---|---|---|
| 10 | 5 | 1.0% | 5.0% |
| 30 | 15 | 3.5% | 5.0% |
| 60 | 30 | 4.2% | 5.0% |
| 144 | 72 | 4.7% | 5.0% |

저사양 폰일수록 카메라가 더 빨리 붙고, 고주사율 모니터일수록 느려집니다. 더 심각한 건 **프레임이 튀는 순간**입니다. dt가 0.2초(로딩 직후 스파이크)면 `k·dt = 1.2`가 됩니다. `Vector3.Lerp`/`Mathf.Lerp`는 t를 0~1로 자르므로 이 프레임에 카메라가 목표에 **갑자기 달라붙어** 부드러움이 한 번에 깨집니다. (t를 자르지 않는 `LerpUnclamped`였다면 목표를 지나쳤을 것입니다.)

해결은 지수 함수를 쓰는 것입니다. "1초에 남은 거리가 `e^-k` 배가 된다"를 dt 단위로 쪼개면 한 프레임의 보간 비율은 `1 - e^(-k·dt)`입니다. 이 비율은 프레임을 어떻게 쪼개도 곱하면 같은 값이 되고, dt가 아무리 커도 1을 넘지 않습니다.

```csharp
public static class Damp
{
    // sharpness(k)가 클수록 빨리 붙음. 대략 1/k 초에 남은 거리가 37%로.
    public static float Factor(float sharpness, float dt) => 1f - Mathf.Exp(-sharpness * dt);

    public static Vector3 Towards(Vector3 current, Vector3 target, float sharpness, float dt)
        => Vector3.Lerp(current, target, Factor(sharpness, dt));

    // 기획자에게 설명하기 쉬운 형태: "halfLife초마다 남은 거리가 절반"
    public static float FactorHalfLife(float halfLife, float dt) => 1f - Mathf.Pow(0.5f, dt / halfLife);
}
```

<details>
<summary>왜 exp인가 — 30초 증명</summary>

한 프레임 비율을 `f(dt)`라 하면, dt를 두 번에 나눠 적용한 결과와 한 번에 적용한 결과가 같아야 프레임 독립입니다.

`(1 - f(dt1)) · (1 - f(dt2)) = 1 - f(dt1 + dt2)`

"곱이 덧셈으로 바뀌는" 함수는 지수 함수뿐이므로 `1 - f(dt) = e^(-k·dt)`, 즉 `f(dt) = 1 - e^(-k·dt)`입니다. `k·dt`가 작을 때 `1 - e^(-k·dt) ≈ k·dt`이므로 "lerp with deltaTime"은 이 식의 1차 근사였던 셈입니다. 프레임이 높을수록 근사가 정확해지는 것도 표에서 확인할 수 있습니다.

</details>

`SmoothDamp`는 내부에서 이미 deltaTime을 반영하므로 이 문제가 없습니다. 다만 호출하는 곳마다 **별도의 `velocity` 필드**가 필요하고, 한 프레임에 두 번 호출하면 안 됩니다.

### 이징 함수 — 움직임에 성격 입히기

사용법 A(시간 기반 트윈)에서 `t`를 그대로 쓰면 등속이라 기계적입니다. `t`를 곡선에 통과시킨 값을 쓰면 "툭 튀어나왔다 멈추는", "살짝 넘쳤다 돌아오는" 느낌이 됩니다. 이 곡선이 **이징 함수**입니다. CSS의 `transition-timing-function: ease-out`과 같은 개념입니다.

```
t →   0 ─────────────── 1
Linear      ／           일정
EaseInQuad  _／          천천히 시작
EaseOutQuad ╭─           빠르게 시작, 부드럽게 멈춤  (UI·획득 연출에 기본)
EaseOutBack ╭⌒─          목표를 살짝 넘었다 돌아옴  (팝업, 버튼)
```

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Core/Ease.cs
public static class Ease
{
    public static float Linear(float t) => t;
    public static float InQuad(float t) => t * t;
    public static float OutQuad(float t) => 1f - (1f - t) * (1f - t);
    public static float InOutCubic(float t)
        => t < 0.5f ? 4f * t * t * t : 1f - Mathf.Pow(-2f * t + 2f, 3f) / 2f;

    public static float OutBack(float t)
    {
        const float c1 = 1.70158f;
        const float c3 = c1 + 1f;
        float u = t - 1f;
        return 1f + c3 * u * u * u + c1 * u * u;
    }
}
```

사용법은 `Lerp(a, b, Ease.OutBack(t))`입니다. `OutBack`은 1을 넘는 값을 반환하므로 `Vector3.Lerp`(t를 0~1로 자름) 대신 **`Vector3.LerpUnclamped`** 를 써야 넘침이 보입니다.

**AnimationCurve**는 이 곡선을 코드 대신 Inspector에서 그리는 도구입니다. `[SerializeField] AnimationCurve curve = AnimationCurve.EaseInOut(0, 0, 1, 1);`로 선언하면 곡선 편집기가 뜨고, 코드에서는 `curve.Evaluate(t)`로 읽습니다. 기획자·아티스트가 직접 조정할 수 있다는 것이 가장 큰 장점이고, 코드 이징은 "복붙 가능하고 diff로 리뷰 가능"하다는 장점이 있습니다. 실전에서는 트윈 라이브러리(DOTween, PrimeTween — 17장)를 쓰지만, 내부에서 하는 일은 이것과 같습니다.

### 삼각함수 — 원운동과 흔들림

반지름 r인 원 위에서 각도 θ인 점은 `(r·cosθ, r·sinθ)`입니다. θ를 시간에 따라 늘리면 원운동이 됩니다.

```csharp
float theta = Time.time * angularSpeedRad;               // 라디안/초
Vector2 offset = new Vector2(Mathf.Cos(theta), Mathf.Sin(theta)) * radius;
transform.position = (Vector2)center.position + offset;
```

N개를 균등 배치하려면 i번째의 각도에 `i * 2π / N`을 더합니다. 원운동의 **접선 방향**(진행 방향)은 반지름 방향에서 90도 앞선 각도입니다.

`Sin`은 -1~1을 매끄럽게 오가므로 "둥실둥실"에 딱 맞습니다.

| 효과 | 코드 |
|---|---|
| 떠다니는 코인 | `y = baseY + Mathf.Sin(Time.time * 2π * freq) * amplitude` |
| 숨쉬는 크기 | `scale = 1 + Mathf.Sin(Time.time * 3f) * 0.05f` |
| 좌우 흔들기(감쇠) | `x = Mathf.Sin(t * 30f) * amp * Mathf.Exp(-t * 5f)` |
| 불규칙 흔들림 | `(Mathf.PerlinNoise(seed, Time.time * freq) * 2f - 1f) * amp` |

화면 흔들림처럼 **규칙성이 보이면 안 되는** 흔들림에는 `Sin`보다 `Mathf.PerlinNoise`가 자연스럽습니다(0~1 반환이라 `*2-1`로 -1~1로 바꿉니다). 본격적인 화면 흔들림은 16장에서 다룹니다.

여러 오브젝트가 같은 `Time.time`으로 흔들리면 군무처럼 동기화되어 어색합니다. `Awake`에서 `phase = Random.value * 2π`를 정해 두고 더해 주세요.

### 난수 1 — Random.Range의 경계

`UnityEngine.Random.Range`는 **오버로드에 따라 상한 포함 여부가 다릅니다.** 가장 흔한 난수 버그의 원인입니다.

| 호출 | 반환 범위 | 비고 |
|---|---|---|
| `Random.Range(0, 3)` (int) | 0, 1, 2 | **상한 배타** — 배열 인덱스에 그대로 쓰도록 설계 |
| `Random.Range(0f, 3f)` (float) | 0.0 ~ 3.0 | **상한 포함** |
| `Random.value` | 0.0 ~ 1.0 | 상한 포함 |
| `Random.insideUnitCircle` | 반지름 1 원 내부 | 스폰 위치 흩뿌리기 |
| `Random.onUnitSphere` | 구 표면 | 3D 방향 |

```csharp
var item = items[Random.Range(0, items.Length)];      // 정답
var bug  = items[Random.Range(0, items.Length - 1)];  // 마지막 원소가 절대 안 나옴
int dice = Random.Range(1, 7);                        // 1~6 주사위
```

`System.Random`의 `Next(min, max)`도 상한 배타입니다. 또 `Random.Range(0, 3)`의 인자가 `3f`인지 `3`인지 한 글자 차이로 동작이 바뀌므로, 정수가 필요하면 리터럴에 `f`가 붙지 않았는지 확인하세요.

### 난수 2 — 가중치 랜덤

"코인 70, 보석 25, 자석 5"처럼 **상대 가중치**가 주어졌을 때 하나를 고르는 표준 알고리즘은 **누적합 방식**입니다.

```
가중치:   코인 70   | 보석 25 | 자석 5
누적:     [0 ─── 70) [70 ─ 95) [95─100)
roll = Random.Range(0, 100)  →  roll이 속한 구간의 아이템 선택
```

```csharp
int total = 0;
foreach (var e in entries) total += e.weight;
int roll = Random.Range(0, total);          // 0 ~ total-1 (상한 배타가 여기서 딱 맞음)
foreach (var e in entries)
{
    if (roll < e.weight) return e;
    roll -= e.weight;
}
```

가중치는 **합이 100일 필요가 없습니다**. 70/25/5든 14/5/1이든 같은 확률입니다. 확률을 퍼센트로 입력하게 만들면 기획자가 항목을 추가할 때마다 나머지를 다시 계산해야 하므로, 상대 가중치가 편합니다. "아무것도 안 떨어짐"도 가중치를 가진 하나의 항목(프리팹 없음)으로 넣으면 로직이 단순해집니다.

### 난수 3 — 셔플백: 진짜 랜덤은 불공평하게 느껴진다

독립 시행 난수는 같은 결과가 연속으로 나올 수 있습니다. 25% 확률 아이템이 12번 연속 안 나올 확률도 3%나 됩니다. 수학적으로 공정해도 **플레이어는 버그라고 느낍니다.**

**셔플백(shuffle bag)** 은 가방에 결과들을 비율대로 넣고 섞은 뒤 하나씩 꺼내며, 다 꺼내면 다시 채웁니다. 테트리스의 "7-bag"이 대표적입니다. 가방 크기 안에서 비율이 보장되므로 긴 가뭄이 없습니다.

| 방식 | 장점 | 단점 | 코인 러시 적용 |
|---|---|---|---|
| 독립 랜덤 | 단순, 예측 불가 | 연속·가뭄 발생 | 적 드롭 (양이 많아 평균에 수렴) |
| 셔플백 | 분포 보장, 가뭄 없음 | 끝부분이 예측 가능 | 레벨업 선택지, 보물상자 |
| 가짜 랜덤(PRD) | 실패할수록 확률 증가 | 구현·튜닝 필요 | 치명타 확률 (참고) |

섞기는 **Fisher–Yates** 알고리즘을 씁니다. `list.OrderBy(x => Random.value)`는 할당이 생기고 분포도 보장되지 않습니다.

```csharp
for (int i = list.Count - 1; i > 0; i--)
{
    int j = Random.Range(0, i + 1);     // 0 ~ i (i 포함)
    (list[i], list[j]) = (list[j], list[i]);
}
```

### 난수 4 — 시드와 재현성

`UnityEngine.Random`은 **전역 상태 하나**를 공유합니다. 시드를 고정하면(`Random.InitState(12345)`) 같은 순서의 난수가 나오지만, 파티클·다른 스크립트·에셋도 같은 전역 난수를 소비하므로 "같은 시드 = 같은 판"이 쉽게 깨집니다.

재현이 필요한 곳(데일리 챌린지 맵, 리플레이, 버그 재현)에는 **독립 인스턴스**를 만듭니다.

| 선택지 | 특징 |
|---|---|
| `System.Random(seed)` | .NET 표준 클래스. 인스턴스별 상태. `Next(min, max)`(상한 배타), `NextDouble()`. 참조 타입이라 생성 시 할당 |
| `Unity.Mathematics.Random(seed)` | `com.unity.mathematics` 패키지의 **struct**. 할당 없음, Burst/Job 호환. `NextInt(min, max)`(상한 배타), `NextFloat()`. **시드 0은 허용되지 않음** |
| `Random.state` 저장/복원 | 전역 난수의 상태를 잠깐 바꿨다 되돌릴 때 |

```csharp
var rng = new System.Random(20260917);         // 오늘 날짜를 시드로 = 데일리 챌린지
int x = rng.Next(0, 10);

var mrng = new Unity.Mathematics.Random(20260917u);  // uint, 0 금지
float f = mrng.NextFloat();                           // struct이므로 필드에 두고 ref로 넘겨야 상태가 이어짐
```

> `Unity.Mathematics.Random`은 struct라서 메서드 인자로 **값 복사**해 넘기면 원본 상태가 진행되지 않아 같은 수가 반복됩니다. 필드로 두거나 `ref`로 넘기세요.

## 실습: 코인 러시에 적용하기

스크립트는 모두 `Assets/_CoinRush/Scripts/<영역>/` 아래에 둡니다. 먼저 개념 절의 `Ease`를 `Core/Ease.cs`로, `Damp`를 맨 위에 `using UnityEngine;`을 붙여 `Core/Damp.cs`로 저장합니다.

### 1단계: 부드러운 카메라 추적

1. `Main Camera`가 Player의 자식이라면 Hierarchy에서 끌어내 루트로 옮깁니다.
2. `Assets/_CoinRush/Scripts/Camera/CameraFollow2D.cs`를 만들고 아래 코드를 작성합니다.
3. `Main Camera`에 붙이고 `Target`에 Player를 드래그합니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Camera/CameraFollow2D.cs
public class CameraFollow2D : MonoBehaviour
{
    public enum FollowMode { ExponentialDamp, SmoothDamp }

    [SerializeField] private Transform target;
    [SerializeField] private FollowMode mode = FollowMode.ExponentialDamp;

    [Header("Exponential Damp")]
    [Tooltip("클수록 빨리 붙습니다. 8 전후가 무난합니다.")]
    [SerializeField, Min(0.1f)] private float sharpness = 8f;

    [Header("SmoothDamp")]
    [SerializeField, Min(0.01f)] private float smoothTime = 0.15f;

    private Vector3 smoothVelocity;   // SmoothDamp 전용 상태 — 호출 지점마다 하나씩

    private void Start() => SnapToTarget();

    // 플레이어 이동(Update/FixedUpdate)이 끝난 뒤 카메라를 움직여야 떨림이 없습니다.
    private void LateUpdate()
    {
        if (target == null) return;
        float dt = Time.deltaTime;
        if (dt <= 0f) return;   // 일시정지(timeScale 0) 중에는 멈춤

        Vector3 goal = new Vector3(target.position.x, target.position.y, transform.position.z);

        transform.position = mode == FollowMode.ExponentialDamp
            ? Damp.Towards(transform.position, goal, sharpness, dt)
            : Vector3.SmoothDamp(transform.position, goal, ref smoothVelocity, smoothTime, Mathf.Infinity, dt);
    }

    public void SnapToTarget()
    {
        if (target == null) return;
        transform.position = new Vector3(target.position.x, target.position.y, transform.position.z);
        smoothVelocity = Vector3.zero;
    }
}
```

4. Play 중 `Mode`를 바꿔 두 방식의 느낌을 비교합니다. `ExponentialDamp`는 출발이 즉각적이고, `SmoothDamp`는 출발도 부드럽습니다.
5. 프레임 독립을 확인하려면 **Game 뷰 상단의 VSync 옵션을 끄거나**, 임시 스크립트에서 `Application.targetFrameRate = 20;`과 `= 144;`로 번갈아 실행해 봅니다. 같은 이동에 카메라가 같은 시간 뒤처지면 성공입니다.

> 플레이어가 Rigidbody2D로 움직이면(07장) 카메라가 미세하게 떨릴 수 있습니다. 07장에서 Rigidbody2D의 `Interpolate`를 켜서 해결합니다.

### 2단계: 무기 궤도 회전(오브)

플레이어 주위를 N개의 구슬이 돌며 닿은 적에게 데미지를 줍니다. 03장의 `WeaponData`를 그대로 재사용합니다.

| `WeaponData` 필드 | 오브 무기에서의 의미 |
|---|---|
| `damage` | 한 번 닿을 때 데미지 |
| `cooldown` | **같은 적**을 다시 때리기까지의 간격(초) |
| `projectilePrefab` | 구슬 외형 프리팹 |
| `projectileSpeed` | 회전 속도(도/초) |

충돌 판정은 트리거 콜백 대신 **`Physics2D.OverlapCircle` 쿼리**로 합니다. 쿼리는 Rigidbody2D 설정과 무관하게 동작하므로, 07장에서 적의 물리 구성을 바꿔도 이 코드는 영향을 받지 않습니다. 쿼리는 07장에서 자세히 다룹니다.

1. `Edit > Project Settings > Tags and Layers`에서 User Layer에 `Enemy`를 추가하고, 05장의 Enemy 프리팹 Layer를 `Enemy`로 바꿉니다(자식 포함 여부를 물으면 Yes). Enemy 프리팹에 `Collider 2D`가 있어야 합니다.
2. 구슬 프리팹: `2D Object > Sprites > Circle`, Scale 0.4, 이름 `Orb`, 콜라이더는 넣지 않습니다. 03장 `WeaponData.projectilePrefab`의 타입이 `Projectile`이므로 `Projectile` 컴포넌트를 붙이고(자동 추가되는 `Rigidbody2D`는 Body Type **Kinematic**), 프리팹으로 저장 후 Hierarchy에서 삭제합니다. `Launch`를 부르지 않으므로 날아가거나 수명으로 사라지지 않습니다.
3. `Create > Coin Rush > Data > Weapon`(03장에서 만든 메뉴)로 `Orb.asset`을 만들고 damage 5, cooldown 0.5, projectilePrefab = Orb, projectileSpeed 180을 입력합니다.
4. Player의 자식으로 빈 오브젝트 `OrbitWeapon`을 만들고 아래 스크립트를 붙입니다. Inspector에서 **`Data`에 3번에서 만든 `Orb.asset`을 드래그**하고, `Enemy Mask`에 Enemy 레이어를 선택합니다. `Data`를 비워 두면 Console에 에러를 남기고 컴포넌트가 스스로 꺼집니다.
5. 04장 `GameSystems`의 `GameStateMachine` → **Gameplay Behaviours** 배열에 `OrbitWeapon`을 추가하고, Player의 `PlayerStateController` → **Disable On Death** 배열에도 추가합니다. 그래야 타이틀·결과 화면과 사망 연출 중에는 오브가 공격하지 않습니다(05장 `AutoAimWeapon`과 같은 취급).

```csharp
using System.Collections.Generic;
using UnityEngine;

// Assets/_CoinRush/Scripts/Weapons/OrbitWeapon.cs
public class OrbitWeapon : MonoBehaviour
{
    [SerializeField] private WeaponData data;
    [SerializeField, Range(1, 8)] private int orbCount = 3;
    [SerializeField] private float radius = 1.8f;
    [SerializeField] private float hitRadius = 0.25f;
    [SerializeField] private LayerMask enemyMask;

    private readonly List<Transform> orbs = new();
    private readonly Collider2D[] hits = new Collider2D[16];   // 재사용 버퍼 (02장: 할당 0)
    private readonly Dictionary<int, float> nextHitTime = new(); // 적 InstanceID → 다시 때릴 수 있는 시각
    private readonly List<int> expiredIds = new();              // 만료 기록 정리용 재사용 버퍼
    private ContactFilter2D filter;
    private float angleDeg;
    private float nextPruneTime;

    private void Awake()
    {
        filter = new ContactFilter2D();
        filter.SetLayerMask(enemyMask);
        filter.useTriggers = true;

        if (data == null || data.projectilePrefab == null)
        {
            Debug.LogError($"{name}: OrbitWeapon의 Data(와 그 Projectile Prefab)가 비어 있습니다. Orb.asset을 연결하세요.", this);
            enabled = false;
        }
    }

    private void Start()
    {
        if (data != null && data.projectilePrefab != null) Rebuild();
    }

    // 상태 머신이 꺼 주면(타이틀·결과·사망) 구슬도 숨김
    private void OnEnable() => SetOrbsVisible(true);

    private void OnDisable()
    {
        SetOrbsVisible(false);
        nextHitTime.Clear();
    }

    // 레벨업으로 개수가 바뀔 때 다시 호출
    public void SetOrbCount(int count)
    {
        orbCount = Mathf.Clamp(count, 1, 8);
        Rebuild();
    }

    private void Rebuild()
    {
        foreach (var orb in orbs) Destroy(orb.gameObject);
        orbs.Clear();
        for (int i = 0; i < orbCount; i++)
        {
            Projectile orb = Instantiate(data.projectilePrefab, transform.position, Quaternion.identity, transform);
            orb.gameObject.SetActive(enabled);
            orbs.Add(orb.transform);
        }
    }

    private void SetOrbsVisible(bool visible)
    {
        foreach (var orb in orbs)
            if (orb != null) orb.gameObject.SetActive(visible);
    }

    private void Update()
    {
        if (Time.deltaTime <= 0f || orbs.Count == 0) return;   // 레벨업·일시정지(timeScale 0) 중에는 회전·피해 모두 멈춤

        PruneExpiredHits();
        angleDeg = Mathf.Repeat(angleDeg + data.projectileSpeed * Time.deltaTime, 360f);
        float step = 360f / orbs.Count;

        for (int i = 0; i < orbs.Count; i++)
        {
            float a = (angleDeg + step * i) * Mathf.Deg2Rad;
            Vector2 offset = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * radius;
            Vector2 worldPos = (Vector2)transform.position + offset;

            orbs[i].position = worldPos;
            // 진행 방향(접선) = 반지름 방향 + 90도 (반시계 회전일 때)
            orbs[i].rotation = Quaternion.Euler(0f, 0f, a * Mathf.Rad2Deg + 90f);

            DamageAt(worldPos);
        }
    }

    private void DamageAt(Vector2 pos)
    {
        int count = Physics2D.OverlapCircle(pos, hitRadius, filter, hits);
        for (int h = 0; h < count; h++)
        {
            if (!hits[h].TryGetComponent<IDamageable>(out var target)) continue;

            int id = hits[h].GetInstanceID();
            if (nextHitTime.TryGetValue(id, out float t) && Time.time < t) continue;

            target.TakeDamage(data.damage);
            nextHitTime[id] = Time.time + data.cooldown;
        }
    }

    // 죽은 적의 기록이 한 판 내내 쌓이지 않도록 1초마다 만료된 항목을 지움 (버퍼 재사용 → 할당 0)
    private void PruneExpiredHits()
    {
        if (Time.time < nextPruneTime) return;
        nextPruneTime = Time.time + 1f;

        expiredIds.Clear();
        foreach (var pair in nextHitTime)            // Dictionary의 foreach는 struct 열거자라 할당 없음
            if (Time.time >= pair.Value) expiredIds.Add(pair.Key);
        for (int i = 0; i < expiredIds.Count; i++)
            nextHitTime.Remove(expiredIds[i]);
    }
}
```

- 만료된 기록은 지워도 동작이 같습니다. 기록이 없으면 "지금 때릴 수 있음"으로 보는데, 만료된 기록도 같은 뜻이기 때문입니다. 사전 크기는 "최근 `cooldown`초 안에 맞은 적 수" 정도로 유지됩니다.
- `IDamageable`은 01장에서 만든 `void TakeDamage(int amount)` 인터페이스입니다. Enemy 쪽에서 `Health`가 이를 구현하거나(01장) Enemy가 구현해야 `TryGetComponent`가 찾습니다. 콜라이더와 같은 오브젝트에 있어야 합니다.
- `Mathf.Repeat(x, 360)`으로 각도를 순환시키면 오래 플레이해도 float 정밀도가 무너지지 않습니다.

### 3단계: 가중치 난수 도우미와 셔플백

```csharp
using System.Collections.Generic;
using UnityEngine;

// Assets/_CoinRush/Scripts/Core/WeightedRandom.cs
public static class WeightedRandom
{
    // weights[i] <= 0 인 항목은 절대 선택되지 않음. 전부 0이면 -1 반환.
    public static int PickIndex(IReadOnlyList<int> weights, System.Random rng = null)
    {
        int total = 0;
        for (int i = 0; i < weights.Count; i++)
            if (weights[i] > 0) total += weights[i];
        if (total <= 0) return -1;

        int roll = rng != null ? rng.Next(0, total) : Random.Range(0, total);
        for (int i = 0; i < weights.Count; i++)
        {
            if (weights[i] <= 0) continue;
            if (roll < weights[i]) return i;
            roll -= weights[i];
        }
        return weights.Count - 1; // 도달하지 않음 (방어 코드)
    }
}
```

```csharp
using System.Collections.Generic;
using UnityEngine;

// Assets/_CoinRush/Scripts/Core/ShuffleBag.cs
public class ShuffleBag<T>
{
    private readonly List<T> source = new();
    private readonly List<T> bag = new();
    private readonly System.Random rng;
    private readonly bool avoidRepeatAcrossRefill;
    private T lastItem;
    private bool hasLast;

    // avoidRepeatAcrossRefill: 가방 경계(이전 가방의 마지막 ↔ 새 가방의 첫 번째)에서도 같은 값이 연속되지 않게 함
    public ShuffleBag(System.Random rng = null, bool avoidRepeatAcrossRefill = false)
    {
        this.rng = rng;
        this.avoidRepeatAcrossRefill = avoidRepeatAcrossRefill;
    }

    // item을 count개 넣음 (count = 비율)
    public void Add(T item, int count = 1)
    {
        for (int i = 0; i < count; i++) source.Add(item);
    }

    public T Next()
    {
        if (source.Count == 0) throw new System.InvalidOperationException("ShuffleBag이 비어 있습니다.");
        if (bag.Count == 0) Refill();
        int last = bag.Count - 1;
        T item = bag[last];
        bag.RemoveAt(last);   // 끝에서 제거 = O(1)
        lastItem = item;
        hasLast = true;
        return item;
    }

    private void Refill()
    {
        bag.AddRange(source);
        for (int i = bag.Count - 1; i > 0; i--)
        {
            int j = rng != null ? rng.Next(0, i + 1) : Random.Range(0, i + 1);
            (bag[i], bag[j]) = (bag[j], bag[i]);
        }

        if (!avoidRepeatAcrossRefill || !hasLast) return;
        var cmp = EqualityComparer<T>.Default;
        int first = bag.Count - 1;                         // 다음에 꺼낼 항목(끝)
        if (!cmp.Equals(bag[first], lastItem)) return;
        for (int k = 0; k < first; k++)                    // 다른 값과 자리를 바꿈
        {
            if (cmp.Equals(bag[k], lastItem)) continue;
            (bag[first], bag[k]) = (bag[k], bag[first]);
            return;
        }
        // 종류가 하나뿐이면 피할 방법이 없으므로 그대로 둠
    }
}
```

가방 안에서는 섞기 덕분에 비율이 보장되지만, **가방과 가방의 경계**에서는 같은 값이 이어질 수 있습니다(첫 가방이 B, A로 끝나고 새 가방이 A부터 나오는 경우). 테트리스의 7-bag처럼 이를 허용해도 되는 곳은 기본값으로, "같은 팁 연속 금지"처럼 막아야 하는 곳은 `new ShuffleBag<string>(avoidRepeatAcrossRefill: true)`로 만듭니다. 자리 바꾸기는 가방 안의 개수를 바꾸지 않으므로 비율은 그대로입니다.

`ShuffleBag`은 11장의 레벨업 선택지에서 "같은 강화만 연속으로 뜨는" 문제를 막는 데 다시 씁니다.

### 4단계: LootTable — 가중치 드롭

1. `Assets/_CoinRush/Scripts/Loot/LootTable.cs`를 작성합니다.

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

// Assets/_CoinRush/Scripts/Loot/LootTable.cs
[CreateAssetMenu(menuName = "CoinRush/Loot Table", fileName = "LootTable")]
public class LootTable : ScriptableObject
{
    [Serializable]
    public class Entry
    {
        [Tooltip("비워 두면 '아무것도 안 떨어짐' 항목")]
        public GameObject prefab;
        [Min(0)] public int weight = 1;
        [Min(1)] public int minCount = 1;
        [Min(1)] public int maxCount = 1;
    }

    [Tooltip("한 번 죽을 때 몇 번 굴릴지")]
    [SerializeField, Min(1)] private int rolls = 1;
    [SerializeField] private List<Entry> entries = new();

    private readonly List<int> weightCache = new();

    // 결과를 버퍼에 채워 넣음 (호출자가 리스트를 재사용 → 할당 0)
    public void Roll(List<GameObject> results, System.Random rng = null)
    {
        results.Clear();
        weightCache.Clear();
        foreach (var e in entries) weightCache.Add(e.weight);

        for (int r = 0; r < rolls; r++)
        {
            int index = WeightedRandom.PickIndex(weightCache, rng);
            if (index < 0) continue;
            Entry picked = entries[index];
            if (picked.prefab == null) continue;

            int max = Mathf.Max(picked.minCount, picked.maxCount);
            int count = rng != null
                ? rng.Next(picked.minCount, max + 1)
                : UnityEngine.Random.Range(picked.minCount, max + 1);   // 정수 상한 배타 → +1
            for (int c = 0; c < count; c++) results.Add(picked.prefab);
        }
    }

}
```

2. 적 사망 시 굴리는 컴포넌트를 만듭니다. 01장의 `Health.Died` 이벤트를 구독합니다.

```csharp
using System.Collections.Generic;
using UnityEngine;

// Assets/_CoinRush/Scripts/Loot/EnemyLoot.cs
[RequireComponent(typeof(Health))]
public class EnemyLoot : MonoBehaviour
{
    [SerializeField] private LootTable table;
    [SerializeField] private float scatterRadius = 0.6f;

    private Health health;
    private static readonly List<GameObject> buffer = new();   // 모든 적이 공유 (메인 스레드 전용)

    private void Awake() => health = GetComponent<Health>();
    private void OnEnable() => health.Died += OnDied;
    private void OnDisable() => health.Died -= OnDied;

    private void OnDied()
    {
        if (table == null) return;
        table.Roll(buffer);
        foreach (GameObject prefab in buffer)
        {
            Vector2 pos = (Vector2)transform.position + Random.insideUnitCircle * scatterRadius;
            Instantiate(prefab, pos, Quaternion.identity);   // 12장에서 풀로 교체
        }
    }
}
```

3. `Create > CoinRush > Loot Table`로 `Loot_Basic.asset`을 만들고 항목을 채웁니다. 경험치 보석·자석이 아직 없다면 색만 다른 Circle 프리팹으로 임시 제작합니다.

**역할 분담(이후 장의 기준)**: 05장 `Enemy.HandleDied`가 `EnemyData.coinDrop`만큼 떨구는 **기본 코인은 그대로 둡니다**(12장 풀링 버전도 `coinDrop`을 씁니다). `LootTable`은 그 위에 얹는 **추가 드롭**만 담당하므로, 표의 Coin 항목은 "보너스 코인"입니다.

| prefab | weight | min | max |
|---|---|---|---|
| Coin (보너스) | 20 | 1 | 2 |
| XpGem | 25 | 1 | 1 |
| Magnet | 1 | 1 | 1 |
| (비움) | 54 | 1 | 1 |

4. Enemy 프리팹에 `EnemyLoot`를 붙이고 `Table`에 `Loot_Basic`을 넣습니다.

> 기본 드롭을 없애고 모든 드롭을 `LootTable`로 옮기고 싶다면 `EnemyData`의 `coinDrop`을 0으로 두고 표의 Coin 가중치를 올리면 됩니다. 단, 이 책의 뒤 장(12장 등)은 `coinDrop`을 기본 코인으로 쓰므로 위 분담을 권합니다.

### 확인하기

Play를 누르고 다음을 확인합니다.

- 플레이어가 급히 방향을 바꿔도 카메라가 튀지 않고 부드럽게 따라온다.
- `Application.targetFrameRate`를 20과 144로 바꿔도 카메라가 뒤처지는 정도가 거의 같다.
- 구슬 3개가 같은 간격으로 플레이어 주위를 돈다. 구슬에 닿은 적의 체력이 0.5초 간격으로 줄어든다.
- 적이 죽으면 기본 코인(`coinDrop`, 슬라임·박쥐는 1개)이 항상 나오고, 약 20%는 보너스 코인 1~2개가 더(총 2~3개), 약 25%는 보석이, 드물게 자석이 나온다. 수십 마리를 잡았을 때 대략 비율이 맞는다.
- 타이틀 화면과 결과 화면, 사망 연출 중에는 구슬이 보이지 않고 적이 피해를 입지 않는다. 레벨업 창이 떠 있는 동안에는 구슬이 멈춘다.

## 흔한 실수

1. **카메라가 144Hz에서 느리고 저사양에서 빠르다** → `Lerp(a, b, k * Time.deltaTime)` 사용 → `1 - Mathf.Exp(-k * dt)`를 보간 비율로 쓰거나 `SmoothDamp`로 바꿉니다.
2. **적이 플레이어를 90도 틀어진 방향으로 바라본다** → `Mathf.Atan2(dir.x, dir.y)`처럼 인자 순서를 뒤집었거나, 스프라이트가 위쪽을 보도록 그려졌는데 오프셋을 안 줬음 → `Atan2(y, x)`로 쓰고 스프라이트 기준 방향에 맞춰 `-90f`를 더합니다.
3. **360도 근처에서 캐릭터가 반대로 한 바퀴 돈다** → 각도에 `Mathf.Lerp`/`MoveTowards` 사용 → `Mathf.LerpAngle`/`MoveTowardsAngle`을 씁니다.
4. **배열의 마지막 아이템이 절대 안 나온다** → 정수 `Random.Range(0, length - 1)` → 정수 버전은 상한 배타이므로 `Random.Range(0, length)`. 반대로 `minCount~maxCount` 포함 범위가 필요하면 `max + 1`.
5. **같은 시드인데 매번 결과가 다르다** → 전역 `UnityEngine.Random`을 다른 코드(파티클, 다른 스크립트)가 함께 소비 → 재현이 필요한 로직에는 `System.Random` 인스턴스를 따로 둡니다. `Unity.Mathematics.Random`은 struct 복사에 주의합니다.
6. **`OutBack` 이징을 넣었는데 넘침이 안 보인다** → `Vector3.Lerp`가 t를 0~1로 자름 → `LerpUnclamped`를 씁니다.

## 연습 문제

**1. ★☆☆ 포탑 회전 속도 제한**
적 머리 위에 붙은 "화살표"가 플레이어를 바라보되, 초당 최대 120도까지만 회전하도록 만드세요.

<details>
<summary>힌트·해설</summary>

현재 z각도와 목표 각도를 구한 뒤 `Mathf.MoveTowardsAngle`을 씁니다.

```csharp
Vector2 dir = player.position - transform.position;
float targetAngle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
float current = transform.eulerAngles.z;
float next = Mathf.MoveTowardsAngle(current, targetAngle, 120f * Time.deltaTime);
transform.rotation = Quaternion.Euler(0f, 0f, next);
```

`transform.eulerAngles.z`는 0~360으로 돌아오지만 `MoveTowardsAngle`이 순환을 처리하므로 문제없습니다. 정확도가 중요하면 각도를 float 필드로 직접 들고 있는 편이 더 깔끔합니다.

</details>

**2. ★★☆ 드롭 확률 검증 테스트**
`LootTable`의 가중치가 의도대로 동작하는지 확인하는 코드를 쓰세요. 시드를 고정한 `System.Random`으로 10만 번 굴려 각 프리팹의 등장 비율을 출력하고, 기대값과 1%p 이상 차이 나면 경고를 띄웁니다.

<details>
<summary>힌트·해설</summary>

`[ContextMenu("Simulate 100k")]` 메서드를 `LootTable`에 추가합니다. 비율 검증에는 개수(`minCount~maxCount`)가 섞이지 않도록 `WeightedRandom.PickIndex`를 직접 호출해 인덱스 횟수를 세는 편이 정확합니다.

시드를 고정하는 이유는 **테스트가 실행할 때마다 다른 결과로 깜빡거리지(flaky) 않게** 하기 위해서입니다. 10만 번이면 표준 오차가 대략 `sqrt(p(1-p)/n)` ≈ 0.14%p(p=0.25)이므로 1%p 기준은 충분히 안전합니다. 10장에서 EditMode 테스트로 옮기는 방법을 배웁니다. `LootTable`에 항목별 확률을 계산하는 `[ContextMenu]`를 추가해 Inspector에서 바로 확인하게 만들어도 좋습니다.

</details>

**3. ★★★ 데일리 챌린지 시드 (확장 과제)**
"오늘의 도전" 모드를 설계하세요. 같은 날짜에 플레이한 모든 사람이 **같은 드롭 결과, 같은 레벨업 선택지 순서**를 겪어야 합니다. 어떤 난수를 어디에 쓰고, 무엇은 전역 난수로 남겨도 되는지 구분해 구현하세요.

<details>
<summary>힌트·해설</summary>

- 시드: `var today = System.DateTime.UtcNow;` 다음에 `int seed = today.Year * 10000 + today.Month * 100 + today.Day;` (UTC 기준으로 해야 시간대가 달라도 같은 날로 취급됩니다).
- **용도별로 난수 스트림을 분리**합니다: `dropRng = new System.Random(seed ^ 0x1234)`, `levelUpRng = new System.Random(seed ^ 0x5678)`. 하나의 스트림을 공유하면 "적을 한 마리 더 잡았다"는 차이가 레벨업 선택지까지 바꿔 버립니다.
- 파티클 흩뿌림, 코인 튀는 방향, 사운드 피치처럼 **결과에 영향이 없는 연출**은 전역 `Random`으로 남겨도 됩니다.
- 적 스폰 위치까지 같게 하려면 스폰 난수도 분리하되, 플레이어 위치에 따라 결과가 달라지는 부분은 완전한 재현이 불가능함을 받아들입니다. 완전 재현(리플레이)은 입력 기록 + 고정 시간 스텝이 필요한 별개 주제입니다.

</details>

## 셀프 체크

**1. 3D에서는 쿼터니언이 필요하지만 2D에서는 z각도 float 하나로 충분한 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

오일러 각의 짐벌락과 보간 문제는 **세 축의 회전을 순서대로 합성**할 때 생깁니다. 2D 오브젝트는 화면에 수직인 z축 하나로만 회전하므로 합성 순서 문제가 없고, 자유도도 하나라 float 하나로 완전히 표현됩니다. 남는 문제는 360도 순환뿐이며 `DeltaAngle`/`LerpAngle`로 처리합니다. 적용할 때만 `Quaternion.Euler(0, 0, angle)`로 변환합니다.

</details>

**2. `Lerp(current, target, k * Time.deltaTime)`가 왜 프레임 독립적이지 않은지, 올바른 식은 무엇인지 설명해 보세요.**

<details>
<summary>모범 답안</summary>

매 프레임 남은 거리가 `(1 - k·dt)`배가 되므로, 시간 T 뒤 남은 비율은 `(1 - k·dt)^(T/dt)`로 dt에 따라 달라집니다. 프레임이 낮을수록 빨리 붙고, dt가 `1/k` 이상이면 `Lerp`가 t를 1로 잘라 목표에 한 번에 달라붙습니다(`LerpUnclamped`라면 지나칩니다). 곱해도 합이 되는 성질을 가진 `1 - e^(-k·dt)`를 비율로 쓰면 남은 비율이 `e^(-k·T)`로 dt와 무관해지고, 비율이 1을 넘지 않습니다.

</details>

**3. `Lerp`, `MoveTowards`, `SmoothDamp`를 각각 어떤 상황에 쓰는지 예를 들어 설명해 보세요.**

<details>
<summary>모범 답안</summary>

- `Lerp`: 시작·끝이 고정되고 t를 시간에 따라 0→1로 올리는 **정해진 시간의 트윈**(팝업 0.3초 등장). 이징 함수와 조합합니다.
- `MoveTowards`: **최대 변화량이 정해진 등속 접근**. 정확히 도착하고 멈춰야 할 때(가속도 제한, 체력바 감소 연출, 각도 회전 속도 제한).
- `SmoothDamp`: 목표가 계속 움직이고 **출발·도착이 모두 부드러워야** 할 때(카메라 추적). 호출 지점마다 속도 상태가 필요합니다.

</details>

**4. 정수 `Random.Range`와 float `Random.Range`의 상한 처리 차이와, 정수 쪽이 그렇게 설계된 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

정수 버전은 상한을 **포함하지 않고**(min ≤ x < max), float 버전은 **포함합니다**(min ≤ x ≤ max). 정수 버전은 `array[Random.Range(0, array.Length)]`처럼 길이를 그대로 넣어 인덱스로 쓰도록 설계되었습니다. 그래서 "1~6 주사위"는 `Range(1, 7)`, `min~max` 포함 범위는 `Range(min, max + 1)`로 써야 합니다.

</details>

## 핵심 요약

- 회전은 내부적으로 쿼터니언입니다. x/y/z/w를 만지지 말고 `Euler`, `AngleAxis`, `LookRotation`, `Slerp`, `RotateTowards`만 씁니다.
- 2D 회전은 z각도 float 하나로 관리하고, 방향 → 각도는 `Mathf.Atan2(y, x) * Mathf.Rad2Deg`, 각도 보간은 `LerpAngle`/`MoveTowardsAngle`을 씁니다.
- `Lerp`는 "고정 a·b + 증가하는 t(트윈)"로 쓰거나, 감쇠로 쓸 땐 비율을 `1 - Mathf.Exp(-k * dt)`로 계산합니다. `k * deltaTime`은 근사일 뿐입니다.
- `MoveTowards`는 등속·정확 도착, `SmoothDamp`는 추적 카메라에 적합합니다(호출 지점마다 velocity 상태 필요).
- 이징은 `t`를 곡선에 통과시키는 것입니다. 넘치는 이징은 `LerpUnclamped`와 함께 쓰고, 조정이 잦으면 `AnimationCurve`로 노출합니다.
- 원운동은 `(cos θ, sin θ) · r`, 둥실거림은 `Sin`, 불규칙 흔들림은 `PerlinNoise`. 오브젝트마다 위상을 달리합니다.
- 정수 `Random.Range`는 상한 배타입니다. 가중치 랜덤은 누적합, 연속·가뭄 방지는 셔플백(Fisher–Yates), 재현성은 용도별 `System.Random` 인스턴스로 해결합니다.

## 더 읽을거리

- Unity 매뉴얼 — Rotation and orientation in Unity: https://docs.unity3d.com/Manual/QuaternionAndEulerRotationsInUnity.html
- Unity 스크립팅 API — `Mathf.SmoothDamp`, `Quaternion`, `Random`: https://docs.unity3d.com/ScriptReference/Quaternion.html
- Freya Holmér, "Math for Game Devs" (YouTube 강의 시리즈) — 벡터·삼각함수·보간의 시각적 설명
- Robert Penner의 이징 방정식, 그리고 이를 정리한 easings.net: https://easings.net/
- Rory Driscoll, "Frame Rate Independent Damping using Lerp" (블로그 글) — `1 - exp(-k·dt)` 유도
