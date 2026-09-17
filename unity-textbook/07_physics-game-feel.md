# 07. 물리와 조작감 — Rigidbody2D와 게임 필

> **이 장에서 배울 것**
> - Rigidbody2D의 Dynamic/Kinematic/Static 차이와, 속도 직접 설정·힘 적용·Transform 이동의 선택 기준을 설명할 수 있다
> - Update(입력)와 FixedUpdate(물리)를 분리하고 Interpolate·Continuous 충돌 감지로 떨림과 관통을 막는다
> - 레이어와 Layer Collision Matrix, Trigger/Collision 콜백 조건, Physics2D 쿼리를 상황에 맞게 사용한다
> - 가속·감속 곡선, 넉백, 무적 시간(i-frames)으로 조작감을 설계하고 구현한다
> - 수백 마리 적의 겹침을 물리 비용을 통제하며 완화한다
>
> **선수 장**: 01, 03, 04, 05, 06 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 미끄러지듯 가속·감속하는 플레이어, 적과 닿으면 데미지+넉백+깜빡이는 무적 시간, 한 덩어리로 뭉치지 않는 적 무리

## 왜 필요한가

지금 코인 러시의 `PlayerMover`(01장)는 `transform.position += dir * speed * Time.deltaTime`으로 움직입니다. 적도 05장에서 같은 방식으로 플레이어를 쫓습니다. 게임이 커지자 다음 문제가 동시에 터집니다.

1. **벽을 뚫는다.** 맵 경계에 BoxCollider2D 벽을 세웠는데, 플레이어가 그대로 통과합니다. Transform을 직접 옮기면 물리 엔진은 "순간이동"으로 받아들여 막아 주지 않습니다.
2. **조작이 딱딱하다.** 키를 누르면 즉시 최고 속도, 떼면 즉시 정지합니다. 정확하지만 무게감이 없어 "싸구려 플래시 게임" 느낌이 납니다. 반대로 AddForce로 바꾸면 이번엔 빙판처럼 미끄러집니다.
3. **적에게 닿자마자 죽는다.** 접촉 데미지를 `OnTriggerStay2D`에 넣었더니 50Hz로 데미지가 들어가 체력 100이 1초 만에 사라집니다.
4. **적이 한 점으로 뭉친다.** 적 200마리가 전부 플레이어 위치로 직진하니, 몇 초 뒤엔 적이 하나처럼 보이는 검은 덩어리가 됩니다. 적끼리 충돌을 켜 봤더니 프레임이 30 아래로 떨어집니다.

이 장은 Unity 2D 물리(Box2D 기반)의 규칙을 정확히 이해하고, 그 위에 "조작감(game feel)"을 설계해 이 네 문제를 해결합니다.

## 개념

### Rigidbody2D의 세 가지 Body Type

Collider2D는 "모양", Rigidbody2D는 "물리 시뮬레이션에 참여하는 몸"입니다.

| Body Type | 힘·중력 | 다른 물체에 밀림 | 이동 방법 | 용도 |
|---|---|---|---|---|
| **Dynamic** | 받음 | 밀림 | `linearVelocity`, `AddForce` | 플레이어, 굴러가는 상자, 넉백되는 적 |
| **Kinematic** | 안 받음 | 안 밀림(무한 질량처럼) | `linearVelocity`, `MovePosition` | 움직이는 발판, 스크립트로 모는 대량의 적 |
| **Static** | 안 받음 | 안 움직임 | 움직이지 않음 | 벽, 바닥 |

- 콜라이더만 있고 Rigidbody2D가 없으면 내부적으로 Static 취급입니다. **움직이는 오브젝트에 Rigidbody2D를 빼먹으면 매번 정적 콜라이더를 옮기는 것**이 되어 느리고 콜백도 기대대로 오지 않습니다.
- Dynamic 대 Dynamic은 서로 밀어냅니다. Kinematic은 Dynamic을 밀어내지만 자신은 밀리지 않습니다.
- 2D 탑다운 게임에서는 **Gravity Scale을 0**으로 둡니다. 중력은 "아래(-y)"로 작용하기 때문입니다.

### 움직이는 네 가지 방법

| 방법 | 벽에 막힘 | 관성 | 언제 |
|---|---|---|---|
| `transform.position = ...` | 안 막힘(물리 무시) | 없음 | 물리와 무관한 연출, 콜라이더 없는 오브젝트 |
| `rb.MovePosition(pos)` | Kinematic: 안 막힘 / Dynamic: 막힘 | 없음 | Kinematic을 경로대로 이동 |
| `rb.linearVelocity = v` | Dynamic: 막힘 | 우리가 직접 설계 | **캐릭터 조작 (권장)** |
| `rb.AddForce(f)` | Dynamic: 막힘 | 질량·Damping에 따름 | 폭발, 바람, 넉백 같은 외력 |

캐릭터 조작에 `AddForce`만 쓰면 "최고 속도", "멈추는 데 걸리는 시간"이 질량·Linear Damping·힘 크기의 조합으로 간접 결정되어 튜닝이 어렵습니다. 기획 언어는 "최고 속도 6, 0.1초 만에 최고 속도, 0.08초 만에 정지"인데, 이를 힘으로 역산하는 건 고통입니다. 그래서 **원하는 속도를 코드로 계산해 `linearVelocity`에 직접 넣고**, 폭발 같은 외부 효과만 `AddForce`를 쓰는 조합이 흔합니다.

`AddForce`의 `ForceMode2D`는 두 가지입니다.

- `ForceMode2D.Force`: 지속적인 힘. 매 FixedUpdate 호출용(`질량·시간` 반영).
- `ForceMode2D.Impulse`: 순간 충격. 한 번만 호출(`속도 변화 = 힘 / 질량`).

> Unity 6에서 `Rigidbody2D.velocity`는 `linearVelocity`로, `drag`/`angularDrag`는 `linearDamping`/`angularDamping`으로 이름이 바뀌었습니다. 옛 튜토리얼 코드를 옮길 때 주의하세요.

### FixedUpdate — 물리는 고정 간격으로 돈다

물리 엔진은 프레임 속도와 무관하게 **고정 간격**(기본 `Time.fixedDeltaTime = 0.02`, 초당 50회)으로 계산합니다. 한 렌더 프레임에 FixedUpdate가 0번일 수도, 3번일 수도 있습니다.

```
렌더 프레임:  |---- Update ----|---- Update ----|---- Update ----|     (144fps: 약 7ms 간격)
물리 스텝:    |F|                               |F|                  (50Hz: 20ms 간격)
→ 어떤 프레임엔 FixedUpdate가 없음

렌더 프레임:  |-------------- Update (저사양, 50ms) --------------|
물리 스텝:    |F|        |F|        |F|
→ 한 프레임에 FixedUpdate 2~3번
```

여기서 두 규칙이 나옵니다.

1. **입력은 Update에서 읽는다.** "이번 프레임에 눌렸는가"(`wasPressedThisFrame`) 같은 입력은 FixedUpdate에서 읽으면 FixedUpdate가 없는 프레임의 입력을 놓칩니다.
2. **물리 조작은 FixedUpdate에서 한다.** 속도·힘을 Update에서 바꾸면 프레임 속도에 따라 적용 횟수가 달라집니다.

그래서 "Update에서 입력을 필드에 저장 → FixedUpdate에서 그 필드로 속도 계산"이 표준 구조입니다. 한 번만 일어나야 하는 입력(대시 등)은 `bool` 플래그로 저장해 두었다가 FixedUpdate에서 소비하고 끄면 됩니다.

### Interpolate — 물리 50Hz, 화면 144Hz의 떨림

물리가 초당 50번만 위치를 갱신하면, 144Hz 화면에서는 같은 위치가 2~3프레임 반복되다 한 번에 점프합니다. 특히 06장의 부드러운 카메라가 붙어 있으면 **캐릭터가 부들부들 떨려 보입니다.**

Rigidbody2D의 **Interpolate** 옵션이 이를 해결합니다.

| 값 | 동작 | 지연 | 권장 |
|---|---|---|---|
| None | 물리 위치를 그대로 표시 | 없음 | 화면에 안 보이는 것, 대량의 적 |
| Interpolate | 직전 두 물리 스텝 사이를 보간해 표시 | 최대 1 스텝 | **플레이어, 카메라가 따라가는 대상** |
| Extrapolate | 속도로 다음 위치를 예측해 표시 | 없음 | 속도가 일정한 것 (급정지 시 튐) |

보간된 위치는 `transform.position`에 반영되고, 물리의 실제 위치는 `rb.position`입니다. 물리 계산에는 `rb.position`을 쓰세요. 또 Interpolate가 켜진 오브젝트의 `transform.position`을 직접 대입하면 보간이 끊기므로 `rb.position`에 대입합니다.

### Collision Detection — 빠른 물체의 관통

기본값 **Discrete**는 물리 스텝마다 "지금 겹쳤나"만 봅니다. 한 스텝에 벽 두께보다 멀리 이동하면 벽 앞 → 벽 뒤로 건너뛰어 관통합니다(터널링). **Continuous**는 이동 경로를 쓸어서 검사하므로 막히지만 비용이 더 듭니다.

- 벽에 **물리적으로 막혀야 하는** 빠른 바디(플레이어, 넉백 중인 캐릭터): Continuous
- 수백 마리의 느린 적: Discrete

주의: Continuous는 **Collision(비트리거) 접촉**에만 적용됩니다. 03장의 `Projectile`처럼 **Is Trigger 콜라이더**는 Continuous로 바꿔도 매 스텝 겹침만 검사하므로, 한 스텝에 적의 크기보다 멀리 날아가면 여전히 명중을 놓칩니다. 빠른 트리거 투사체는 "직전 위치에서 이번 이동 거리만큼" 직접 캐스트합니다.

```csharp
// 빠른 트리거 투사체의 명중 보강 (Projectile 같은 스크립트의 FixedUpdate)
Vector2 delta = body.linearVelocity * Time.fixedDeltaTime;
RaycastHit2D hit = Physics2D.CircleCast(body.position, radius, delta.normalized, delta.magnitude, targetLayers);
if (hit.collider != null && hit.collider.TryGetComponent(out IDamageable target))
{
    target.TakeDamage(damage);
    Destroy(gameObject);
}
```

코인 러시의 기본 탄속(12)과 적 크기(0.45~0.6)에서는 스텝당 이동이 0.24라 트리거만으로 충분합니다. 탄속을 30 이상으로 올릴 때 위 방식을 검토하세요.

### 레이어와 Layer Collision Matrix

레이어는 오브젝트를 32개 그룹 중 하나로 분류합니다. `Project Settings > Physics 2D > Layer Collision Matrix`에서 **어떤 레이어끼리 충돌·트리거 판정을 할지** 정합니다. 체크를 끄면 두 레이어 사이는 검사 자체를 하지 않으므로 **버그 방지와 성능을 동시에** 얻습니다.

코인 러시의 레이어 설계입니다.

| | Player | Enemy | Pickup | Wall | PlayerAttack |
|---|---|---|---|---|---|
| **Player** | – | ✅ | ✅ | ✅ | – |
| **Enemy** | ✅ | ❌ | – | ❌ | ✅ |
| **Pickup** | ✅ | – | ❌ | – | – |
| **Wall** | ✅ | ❌ | – | – | – |
| **PlayerAttack** | – | ✅ | – | – | – |

(– 는 끔. **Enemy×Enemy를 끄는 것**이 성능에 가장 큽니다. 적끼리는 뒤에서 가벼운 분리 힘으로 처리합니다.)

코드에서 레이어를 다룰 때는 이름으로 마스크를 만들거나 `[SerializeField] LayerMask`를 씁니다.

```csharp
int enemyLayer = LayerMask.NameToLayer("Enemy");        // 레이어 번호 (예: 7)
int enemyMask  = LayerMask.GetMask("Enemy", "Wall");    // 비트 마스크 (1<<7 | 1<<8)
bool isEnemy = other.gameObject.layer == enemyLayer;    // 태그 비교보다 빠르고 오타에 안전
```

### Trigger vs Collision — 콜백은 언제 오는가

| | Collision (둘 다 Is Trigger 끔) | Trigger (한쪽이라도 Is Trigger 켬) |
|---|---|---|
| 물리적으로 막음 | 예 | 아니오 (통과) |
| 콜백 | `OnCollisionEnter2D/Stay2D/Exit2D(Collision2D)` | `OnTriggerEnter2D/Stay2D/Exit2D(Collider2D)` |
| 인자로 얻는 정보 | 접촉점, 법선, 상대 속도 | 상대 콜라이더만 |
| 용도 | 벽, 밀쳐내기 | 코인 획득, 접촉 데미지, 영역 감지 |

콜백이 오려면 **Layer Collision Matrix에서 두 레이어가 켜져 있어야** 하고, 그다음 Body Type 조건은 Collision과 Trigger가 **다릅니다**.

**Collision 콜백** (둘 다 Is Trigger 끔)

| A \ B | Dynamic | Kinematic | Static(또는 Rigidbody2D 없음) |
|---|---|---|---|
| **Dynamic** | ✅ | ✅ | ✅ |
| **Kinematic** | ✅ | ⚠️ | ⚠️ |
| **Static** | ✅ | ⚠️ | ❌ |

⚠️: Kinematic끼리, Kinematic과 Static 사이의 Collision은 기본적으로 일어나지 않고, Kinematic 쪽 Rigidbody2D의 **Use Full Kinematic Contacts**를 켜야 콜백이 옵니다.

**Trigger 콜백** (한쪽이라도 Is Trigger 켬)

| A \ B | Dynamic | Kinematic | Static(또는 Rigidbody2D 없음) |
|---|---|---|---|
| **Dynamic** | ✅ | ✅ | ✅ |
| **Kinematic** | ✅ | ✅ | ✅ |
| **Static** | ✅ | ✅ | ❌ |

Unity 6 매뉴얼(Kinematic Body Type 참조)은 트리거 콜라이더를 위 Kinematic 제한의 **예외**로 명시합니다. 즉 트리거는 어느 한쪽에 Rigidbody2D(Body Type 무관)만 있으면 옵니다. 둘 다 Rigidbody2D가 없는 Static끼리만 오지 않습니다. 코인 러시는 플레이어를 Dynamic으로 두므로(벽에 막히기 위해서), 플레이어가 관련된 접촉(적, 코인, 벽)은 어느 표로 봐도 확실히 동작합니다.

콜백과 관련된 추가 규칙입니다.

- 콜백은 **두 오브젝트 모두의** 스크립트에서 호출됩니다. 한쪽에서만 처리하도록 책임을 정하세요(코인 러시: 접촉 데미지는 플레이어 쪽이 처리).
- `OnTriggerStay2D`는 물리 스텝마다 옵니다. 데미지를 넣으면 초당 50번 들어갑니다 → 무적 시간으로 제한합니다.
- Dynamic 바디가 **잠들면(Sleep)** Stay 콜백이 멈출 수 있습니다. 가만히 서 있는 플레이어에게 적이 겹쳐 있는데 데미지가 안 들어가는 버그의 원인입니다. 플레이어는 `Sleeping Mode = Never Sleep`으로 둡니다.

### Physics2D 쿼리 — 콜백 없이 물어보기

콜백은 "물리 엔진이 알려주는" 방식이고, 쿼리는 "내가 지금 물어보는" 방식입니다. 쿼리는 Rigidbody2D가 없어도, Body Type이 무엇이든 콜라이더만 있으면 찾습니다.

| 쿼리 | 질문 | 반환 |
|---|---|---|
| `Physics2D.Raycast(origin, dir, dist, mask)` | 이 방향 직선에 처음 닿는 것은? | `RaycastHit2D` (`if (hit)`로 검사) |
| `Physics2D.CircleCast(origin, r, dir, dist, mask)` | 원을 밀었을 때 처음 닿는 것은? | `RaycastHit2D` |
| `Physics2D.OverlapCircle(point, r, mask)` | 이 원 안에 무언가 있나? (하나) | `Collider2D` 또는 null |
| `Physics2D.OverlapCircle(point, r, filter, results)` | 이 원 안의 것 전부 | 찾은 개수(int), 결과는 버퍼에 |
| `Physics2D.OverlapBox`, `OverlapPoint` | 사각형/점 영역 | 위와 같은 형태 |

```csharp
// 할당 없는 쿼리 — 버퍼와 필터를 필드에 한 번만 만들어 재사용
private readonly Collider2D[] results = new Collider2D[32];
private ContactFilter2D filter;

void Awake()
{
    filter = new ContactFilter2D();
    filter.SetLayerMask(LayerMask.GetMask("Enemy"));
    filter.useTriggers = true;          // 트리거 콜라이더도 찾기
}

int FindNearbyEnemies(Vector2 center, float radius)
    => Physics2D.OverlapCircle(center, radius, filter, results);
```

`OverlapCircleAll`처럼 배열을 반환하는 버전은 호출마다 새 배열을 할당합니다(02장의 GC 문제). 예전의 `OverlapCircleNonAlloc`은 Unity 6에서 obsolete이므로, 위처럼 `ContactFilter2D` + 버퍼 오버로드를 씁니다. 버퍼가 가득 차면 나머지는 잘리므로 크기를 넉넉히 잡습니다.

### 게임 필 1 — 가속과 감속을 따로 설계한다

"조작감이 좋다"의 상당 부분은 **속도가 목표값에 도달하는 방식**입니다. 핵심은 가속·감속·방향 전환을 **서로 다른 수치**로 두는 것입니다.

```
속도
 max ┤      ╭──────────╮
     │     ╱            ╲         가속 시간: 0.1초 (반응이 빠르게)
     │    ╱              ╲        감속 시간: 0.06초 (멈출 땐 더 빠르게 → 정밀함)
   0 ┼───╯                ╰───
       키 누름          키 뗌
```

| 파라미터 | 짧게 하면 | 길게 하면 |
|---|---|---|
| 가속 시간 | 즉각적, 가벼움 | 묵직함, 둔함 |
| 감속 시간 | 정밀함, 딱 멈춤 | 미끄러짐, 빙판 |
| 방향 전환 배율 | 급선회 가능 | 반대로 틀 때 크게 도는 느낌 |

구현은 06장의 `MoveTowards`를 속도 벡터에 적용합니다. 가속도(유닛/초²) = 최고 속도 / 가속 시간입니다.

```csharp
Vector2 target = input * maxSpeed;
bool accelerating = input.sqrMagnitude > 0.01f;
float rate = accelerating ? maxSpeed / accelTime : maxSpeed / decelTime;
// 현재 속도와 목표 방향이 반대면(내적 < 0, 05장) 더 빠르게 꺾기
if (accelerating && Vector2.Dot(velocity, target) < 0f) rate *= turnMultiplier;
velocity = Vector2.MoveTowards(velocity, target, rate * Time.fixedDeltaTime);
```

서바이버라이크는 적을 피하는 정밀함이 중요하므로 가속 0.08~0.12초, 감속 0.05~0.08초 정도의 **"거의 즉각적이지만 약간의 무게"** 가 무난합니다. 플랫포머라면 훨씬 긴 값을 씁니다. 숫자는 반드시 직접 플레이하며 조정하세요.

### 게임 필 2 — 입력 반응성

- **입력 지연을 만들지 마세요.** 입력을 FixedUpdate에서만 읽거나, 애니메이션이 끝날 때까지 입력을 막으면 "굼뜬" 느낌이 납니다.
- **대각선 속도 보정**: 키보드 W+D는 (1, 1)로 길이가 1.41입니다. `Vector2.ClampMagnitude(input, 1f)`로 자릅니다. `normalized`를 쓰면 게임패드 스틱을 살짝 기울여도 최고 속도가 되어 아날로그 입력이 무의미해집니다.
- **데드존**: 스틱은 손을 떼도 0.05 정도 흔들립니다. 08장의 Input System이 기본 데드존 처리를 제공합니다.

### 게임 필 3 — 넉백과 무적 시간

피격 시 세 가지가 함께 일어나야 "맞았다"는 감각이 분명해집니다.

```
t=0      피격: 데미지 적용, 적 반대 방향으로 속도 순간 설정
t=0~0.15 입력 무시 (넉백이 입력에 즉시 상쇄되지 않도록)
t=0~0.8  무적 (추가 데미지 무시) + 스프라이트 깜빡임
t=0.8    무적 해제
```

- **입력 무시 시간**이 없으면 넉백 속도를 넣은 바로 다음 FixedUpdate에서 가속 로직이 입력 방향으로 속도를 되돌려 버려, 넉백이 보이지 않습니다.
- **무적 시간(i-frames, invincibility frames)** 이 없으면 적에게 겹쳐 있는 동안 매 스텝 데미지가 들어갑니다. 무적 중임을 **반드시 시각적으로** 알려야 합니다(깜빡임). 안 그러면 "적에게 닿았는데 데미지가 안 들어가는 버그"로 보입니다.
- 16장에서 히트스톱·화면 흔들림을 더해 완성합니다.

### 수백 마리 적의 겹침 — 물리를 적게 쓰는 설계

적끼리 충돌을 켜면 물리 엔진이 알아서 밀어내지만, 수백 개의 Dynamic 바디가 서로 접촉하면 접촉 쌍이 폭발적으로 늘고 솔버 반복 비용이 커집니다(모바일에서 특히 치명적).

| 방식 | 비용 | 결과 |
|---|---|---|
| 적 Dynamic + 적끼리 충돌 ON | 높음 (접촉 쌍 수에 비례, 뭉치면 급증) | 확실히 안 겹침, 밀치기 연쇄로 떨림 |
| 적 Kinematic + 적끼리 충돌 OFF + **분리 힘** | 중간 (쿼리 수 조절 가능) | 살짝 겹치지만 자연스럽게 퍼짐 |
| 겹침 무시 | 거의 0 | 한 덩어리로 뭉침 |

분리 힘은 "주변 반경 안의 이웃으로부터 멀어지는 방향"을 더하는 것입니다(보이드 알고리즘의 separation 규칙).

```
        ●이웃
         ╲
          ↘  멀어지는 벡터 (가까울수록 크게)
    ●이웃 → ◎ 나
```

비용을 통제하는 요령입니다.

1. **매 스텝 전부 검사하지 않는다**: 적마다 N 스텝에 한 번(예: 4스텝)만 이웃을 검사하고, 검사 시점을 인스턴스마다 어긋나게 해서 부하를 분산합니다. 결과 벡터는 다음 검사까지 재사용합니다.
2. **이웃 수를 제한한다**: 버퍼 크기를 8 정도로 작게 잡으면 빽빽한 곳에서도 비용 상한이 생깁니다.
3. **더 많아지면** 물리 쿼리 대신 격자 기반 공간 해시나 Job System으로 옮깁니다(18장).

## 실습: 코인 러시에 적용하기

### 1단계: 레이어와 물리 설정

1. `Edit > Project Settings > Tags and Layers`에서 User Layer를 추가합니다: `Player`, `Enemy`(06장에서 추가했다면 생략), `Pickup`, `Wall`, `PlayerAttack`.
2. Player 오브젝트 → Layer `Player`, Enemy 프리팹 → `Enemy`, Coin 등 획득물 프리팹 → `Pickup`.
   - **마이그레이션 주의**: 02장 `CoinMagnet`의 **Coin Layers**는 `Coin` 레이어를 가리키고 있습니다. 코인 프리팹을 `Pickup`으로 옮겼으면 Player의 `CoinMagnet` → Coin Layers도 **`Pickup`으로 바꿉니다**. 안 바꾸면 자석이 코인을 하나도 찾지 못합니다.
3. `Project Settings > Physics 2D > Layer Collision Matrix`를 위 개념 절의 표대로 설정합니다. **Enemy×Enemy 체크 해제**를 잊지 마세요.
4. 맵 경계: 빈 오브젝트 `Walls` 아래에 `BoxCollider2D`를 가진 오브젝트 4개(상하좌우)를 만들고 Layer를 `Wall`로 둡니다. Rigidbody2D는 넣지 않습니다(Static).
5. `Assets/_CoinRush/Physics/` 폴더에서 `Create > 2D > Physics Material 2D`로 `NoFriction`을 만들고 Friction 0, Bounciness 0으로 설정합니다. 벽에 비비며 이동할 때 달라붙는 현상을 막습니다.

### 2단계: Player의 Rigidbody2D 구성

Player 오브젝트를 선택하고 다음과 같이 설정합니다.

| 컴포넌트 | 설정 | 이유 |
|---|---|---|
| Rigidbody2D | Body Type: **Dynamic** | 벽에 막히고, 모든 접촉 콜백을 확실히 받음 |
| | Material: `NoFriction` | 벽 달라붙음 방지 |
| | Gravity Scale: **0** | 탑다운 |
| | Linear Damping: 0 | 감속은 코드가 담당 |
| | Collision Detection: **Continuous** | 넉백 중 벽 관통 방지 |
| | Sleeping Mode: **Never Sleep** | 정지 중에도 Stay 콜백 유지 |
| | Interpolate: **Interpolate** | 카메라 추적 시 떨림 제거 |
| | Constraints: Freeze Rotation Z ✅ | 적에게 밀려 빙글 도는 것 방지 |
| CircleCollider2D | Is Trigger: 끔, Radius 0.4 | 벽·적과 물리 접촉 |

### 3단계: PlayerMover를 가속·감속 이동으로 교체

01장의 `PlayerMover`를 아래 코드로 **통째로 교체**합니다. 04·05장이 쓰는 `MoveInput`, `CanMove`, `Facing`은 같은 이름으로 유지합니다. 입력은 이번 장에서는 Input System의 장치를 직접 읽고(`Keyboard.current`), 08장에서 액션 기반으로 바꿉니다. Unity 6 신규 프로젝트는 Input System 패키지가 기본 활성이라 추가 설치가 필요 없습니다.

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

// Assets/_CoinRush/Scripts/Player/PlayerMover.cs
[RequireComponent(typeof(Rigidbody2D))]
public class PlayerMover : MonoBehaviour
{
    [Header("속도")]
    [SerializeField] private float maxSpeed = 6f;
    [Tooltip("정지 → 최고 속도까지 걸리는 시간(초)")]
    [SerializeField, Min(0.001f)] private float accelTime = 0.1f;
    [Tooltip("최고 속도 → 정지까지 걸리는 시간(초)")]
    [SerializeField, Min(0.001f)] private float decelTime = 0.06f;
    [Tooltip("반대 방향 입력 시 가속 배율")]
    [SerializeField, Min(1f)] private float turnMultiplier = 2f;

    private Rigidbody2D rb;
    private float inputBlockedUntil;    // 넉백 중 입력 무시 (Time.time 기준)

    public Vector2 MoveInput { get; private set; }                  // Update에서 기록, FixedUpdate에서 사용
    public bool CanMove { get; set; } = true;                       // 04장 상태 머신이 제어
    public Vector2 Velocity => rb.linearVelocity;
    public Vector2 Facing { get; private set; } = Vector2.right;    // 05장 자동 조준이 사용
    public bool IsInputBlocked => Time.time < inputBlockedUntil;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void Update()
    {
        MoveInput = CanMove ? ReadMoveInput() : Vector2.zero;
        if (MoveInput.sqrMagnitude > 0.01f) Facing = MoveInput.normalized;
    }

    private void FixedUpdate()
    {
        Vector2 input = IsInputBlocked ? Vector2.zero : MoveInput;
        Vector2 velocity = rb.linearVelocity;
        Vector2 target = input * maxSpeed;

        bool accelerating = input.sqrMagnitude > 0.0001f;
        float rate = maxSpeed / (accelerating ? accelTime : decelTime);
        if (accelerating && Vector2.Dot(velocity, target) < 0f) rate *= turnMultiplier;

        // 넉백 중에는 감속만 적용 → 튕겨 나간 뒤 자연스럽게 멈춤
        rb.linearVelocity = Vector2.MoveTowards(velocity, target, rate * Time.fixedDeltaTime);
    }

    // 외부(피격 처리)에서 호출: 속도를 순간 설정하고 잠시 입력을 무시
    public void ApplyKnockback(Vector2 velocity, float blockInputSeconds)
    {
        rb.linearVelocity = velocity;
        inputBlockedUntil = Time.time + blockInputSeconds;
    }

    // 08장에서 액션 기반으로 교체될 부분
    private static Vector2 ReadMoveInput()
    {
        Vector2 value = Vector2.zero;
        Keyboard kb = Keyboard.current;
        if (kb != null)
        {
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) value.x -= 1f;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) value.x += 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) value.y -= 1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) value.y += 1f;
        }

        Gamepad pad = Gamepad.current;
        if (pad != null)
        {
            Vector2 stick = pad.leftStick.ReadValue();
            if (stick.sqrMagnitude > value.sqrMagnitude) value = stick;
        }

        return Vector2.ClampMagnitude(value, 1f);   // 대각선 1.41 → 1, 아날로그 강도는 유지
    }
}
```

- 이전 버전에 있던 `Mathf.Clamp`로 화면 밖을 막는 코드는 지웁니다. 이제 벽 콜라이더가 막습니다.
- `Time.time`은 FixedUpdate 안에서 읽으면 고정 스텝 시각을 돌려주므로 Update·FixedUpdate 어디서 비교해도 일관됩니다.
- Play 중 Inspector에서 `accelTime`/`decelTime`을 0.3, 0.02 등 극단값으로 바꿔 차이를 몸으로 느껴 보세요.

### 4단계: 적을 Kinematic으로 옮기고 분리 힘 추가

05장의 `Enemy`는 `FixedUpdate`에서 속도를 직접 정해 플레이어를 추적했고, 01장 `DamageOnTouch`로 접촉 데미지를 줬습니다. 이 장에서는 이동 책임을 새 컴포넌트 `EnemyMotor2D`로, 접촉 데미지 책임을 플레이어 쪽 `PlayerContactDamage`(5단계)로 옮깁니다. 그래서 **05장 `Enemy.cs`를 아래 코드로 통째로 교체**합니다. 바뀐 점은 세 가지입니다.

- `[RequireComponent]`에서 `DamageOnTouch`를 뺐고, `contact` 필드·`GetComponent<DamageOnTouch>()`·`contact.Damage = ...` 대입을 삭제했습니다.
- `FixedUpdate`(추적)를 삭제했습니다. 좌우 반전은 `FaceDirection`으로 남겨 `EnemyMotor2D`가 부릅니다.
- `Data`, `Init`, 코인 드롭(`coinDrop`)은 그대로입니다.

```csharp
// Assets/_CoinRush/Scripts/Enemies/Enemy.cs  (05장 파일 교체)
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D), typeof(Health))]
public class Enemy : MonoBehaviour
{
    [SerializeField] private EnemyData data;              // 씬에 직접 배치할 때 쓰는 기본값
    [SerializeField] private HealthRuntimeSet aliveEnemies;
    [SerializeField] private Coin coinPrefab;
    [SerializeField] private SpriteRenderer sprite;

    private Rigidbody2D body;
    private Health health;

    public EnemyData Data => data;

    void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        health = GetComponent<Health>();
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

    // 05장 EnemySpawner가 호출. 추적 대상은 이제 EnemyMotor2D가 찾으므로 target은 받기만 함
    public void Init(EnemyData newData, Transform newTarget) => Apply(newData);

    private void Apply(EnemyData newData)
    {
        data = newData;
        health.Initialize(data.maxHp);
        // 접촉 데미지(data.contactDamage)는 PlayerContactDamage가 직접 읽음
    }

    // EnemyMotor2D가 이동 방향을 알려 줌 (05장 ④의 좌우 반전)
    public void FaceDirection(Vector2 direction)
    {
        if (sprite != null && Mathf.Abs(direction.x) > 0.01f)
            sprite.flipX = direction.x < 0f;
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

Enemy 프리팹 설정입니다(프리팹을 더블클릭해 Prefab Mode에서 작업).

1. 코드를 저장해 컴파일이 끝나면 **`DamageOnTouch` 컴포넌트를 제거**합니다(⋮ → Remove Component). `RequireComponent`에서 빠졌으므로 이제 지울 수 있습니다. 남겨 두면 `OnTriggerEnter2D`가 먼저 피해를 주고 Hurt 무적을 켜서, 5단계의 넉백이 발동하지 않습니다.
2. 기존 `Rigidbody2D`(05장에서 Dynamic): Body Type **Kinematic**, Interpolate None, Collision Detection Discrete로 바꿉니다.
3. `CircleCollider2D`: **Is Trigger 켬**, Radius 0.35. (플레이어를 물리적으로 밀지 않고, 트리거로 접촉만 알림)
4. 아래 `EnemyMotor2D`를 추가합니다. Slime·Bat 두 프리팹 모두 같은 작업을 합니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Enemies/EnemyMotor2D.cs
[RequireComponent(typeof(Rigidbody2D), typeof(Enemy))]
public class EnemyMotor2D : MonoBehaviour
{
    [Header("분리(겹침 완화)")]
    [SerializeField] private float separationRadius = 0.6f;
    [SerializeField] private float separationWeight = 1.2f;
    [Tooltip("몇 물리 스텝마다 이웃을 다시 찾을지")]
    [SerializeField, Range(1, 10)] private int separationInterval = 4;

    private static Transform sharedTarget;                          // 모든 적이 같은 플레이어를 추적
    private static readonly Collider2D[] neighbors = new Collider2D[8]; // 메인 스레드에서만 쓰므로 공유 가능
    private static ContactFilter2D enemyFilter;
    private static bool filterReady;

    private Rigidbody2D rb;
    private Enemy enemy;
    private Collider2D selfCollider;
    private Vector2 cachedSeparation;
    private int stepOffset;
    private int stepCount;
    private float knockbackUntil;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        enemy = GetComponent<Enemy>();
        selfCollider = GetComponent<Collider2D>();
        stepOffset = Random.Range(0, separationInterval);   // 검사 시점을 적마다 어긋나게

        if (!filterReady)
        {
            enemyFilter = new ContactFilter2D();
            enemyFilter.SetLayerMask(LayerMask.GetMask("Enemy"));
            enemyFilter.useTriggers = true;
            filterReady = true;
        }
    }

    private void Start()
    {
        if (sharedTarget == null)
        {
            // 스폰마다 검색하지 않도록 한 번 찾아 공유 (씬이 바뀌면 null이 되어 다시 찾음)
            PlayerMover player = FindFirstObjectByType<PlayerMover>();
            if (player != null) sharedTarget = player.transform;
        }
    }

    private void FixedUpdate()
    {
        if (sharedTarget == null) { rb.linearVelocity = Vector2.zero; return; }
        if (Time.time < knockbackUntil) return;   // 넉백 속도 유지

        Vector2 toPlayer = (Vector2)sharedTarget.position - rb.position;
        Vector2 chase = toPlayer.sqrMagnitude > 0.0001f ? toPlayer.normalized : Vector2.zero;

        stepCount++;
        if ((stepCount + stepOffset) % separationInterval == 0)
            cachedSeparation = ComputeSeparation();

        Vector2 dir = Vector2.ClampMagnitude(chase + cachedSeparation * separationWeight, 1f);
        rb.linearVelocity = dir * enemy.Data.moveSpeed;   // Kinematic도 속도로 이동 가능
        enemy.FaceDirection(dir);                          // 05장의 좌우 반전
    }

    private Vector2 ComputeSeparation()
    {
        int count = Physics2D.OverlapCircle(rb.position, separationRadius, enemyFilter, neighbors);
        Vector2 push = Vector2.zero;
        for (int i = 0; i < count; i++)
        {
            if (neighbors[i] == selfCollider) continue;
            Vector2 away = rb.position - (Vector2)neighbors[i].transform.position;
            float dist = away.magnitude;

            // OverlapCircle은 "콜라이더가 원과 겹치는지"를 보므로, 중심 거리가 반경보다 먼 이웃도 반환됩니다.
            // 그런 이웃은 건너뛰어야 가중치가 음수(= 끌어당김)가 되지 않습니다.
            if (dist >= separationRadius) continue;

            Vector2 dirAway;
            if (dist < 0.0001f)
            {
                float angle = Random.Range(0f, Mathf.PI * 2f);             // 완전히 같은 위치면 임의의 단위 방향
                dirAway = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
            }
            else
            {
                dirAway = away / dist;
            }

            float weight = Mathf.Clamp01(1f - dist / separationRadius);   // 가까울수록 강하게, 0~1
            push += dirAway * weight;
        }
        return push;
    }

    public void ApplyKnockback(Vector2 velocity, float duration)
    {
        rb.linearVelocity = velocity;
        knockbackUntil = Time.time + duration;
    }
}
```

> 적은 Kinematic이라 벽에 막히지 않습니다. 서바이버라이크는 적이 화면 밖에서 스폰되어 들어오므로 오히려 의도에 맞습니다. 적이 벽에 막혀야 하는 장르라면 Dynamic + 적끼리 충돌 OFF를 고려하세요.

### 5단계: 접촉 데미지 + 넉백 + 무적 시간

플레이어 쪽에 피격 처리를 둡니다. 01장의 `Health`(`Current`, `Max`, `TakeDamage(int)`, `Died`)가 Player에 붙어 있다고 가정합니다. 무적 시간과 깜빡임은 새로 만들지 않고 **04장 `PlayerStateController`의 Hurt 상태를 재사용**합니다. `TakeDamage`가 `Changed`를 발행하면 Hurt 상태가 `Health.Invulnerable`을 켜고 `hurtDuration`(0.8초) 동안 깜빡인 뒤 끕니다. 이 컴포넌트는 그 플래그만 확인합니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Player/PlayerContactDamage.cs
[RequireComponent(typeof(Health), typeof(PlayerMover))]
public class PlayerContactDamage : MonoBehaviour
{
    [SerializeField] private float knockbackSpeed = 9f;
    [SerializeField] private float inputBlockSeconds = 0.15f;

    [Header("적도 반대로 밀기")]
    [SerializeField] private float enemyKnockbackSpeed = 4f;
    [SerializeField] private float enemyKnockbackSeconds = 0.12f;

    private Health health;
    private PlayerMover mover;
    private int enemyLayer;

    // 04장 PlayerStateController의 Hurt 상태가 켜고 끄는 플래그 (무적 시간·깜빡임은 거기서 담당)
    public bool IsInvincible => health.Invulnerable;

    private void Awake()
    {
        health = GetComponent<Health>();
        mover = GetComponent<PlayerMover>();
        enemyLayer = LayerMask.NameToLayer("Enemy");
    }

    // 적 콜라이더는 트리거 → 플레이어(Dynamic)와의 쌍이므로 확실히 호출됨
    private void OnTriggerStay2D(Collider2D other)
    {
        if (other.gameObject.layer != enemyLayer) return;
        if (IsInvincible || health.Current <= 0) return;
        if (!other.TryGetComponent<Enemy>(out var enemy)) return;

        health.TakeDamage(enemy.Data.contactDamage);

        Vector2 away = (Vector2)transform.position - (Vector2)other.transform.position;
        if (away.sqrMagnitude < 0.0001f) away = Random.insideUnitCircle;
        away.Normalize();

        mover.ApplyKnockback(away * knockbackSpeed, inputBlockSeconds);
        if (other.TryGetComponent<EnemyMotor2D>(out var motor))
            motor.ApplyKnockback(-away * enemyKnockbackSpeed, enemyKnockbackSeconds);

        // TakeDamage → Changed → 04장 Hurt 상태 진입 → Invulnerable = true (같은 스텝에서 바로 켜짐)
    }
}
```

1. Player에 `PlayerContactDamage`를 붙입니다. 04장 `PlayerStateController`가 같은 오브젝트에 있어야 무적 시간이 동작합니다.
2. 적 프리팹에서 01·05장의 `DamageOnTouch`가 **제거되었는지** 다시 확인합니다(4단계 1번). 남아 있으면 그 `OnTriggerEnter2D`가 먼저 피해를 주고 Hurt 무적을 켜므로, 이 컴포넌트는 `IsInvincible`에서 바로 반환해 넉백이 빠집니다. 03장 가시 공(`HazardSetup`)을 아직 쓰고 있다면 그쪽 `DamageOnTouch`는 그대로 둬도 됩니다(적 레이어가 아니므로 이 컴포넌트와 겹치지 않음).
3. 03장의 적 데이터 에셋에서 `contactDamage`를 1로 둡니다(플레이어 최대 체력이 01장 기준 5이므로, 다섯 번 맞으면 사망).

> **왜 적 쪽이 아니라 플레이어 쪽에서 처리하나요?** 콜백 **수**가 줄어서가 아닙니다. 트리거 콜백은 겹친 쌍마다 양쪽 스크립트에 호출되므로, 플레이어 하나가 적 200마리와 겹치면 플레이어 쪽에서도 200번 호출됩니다. 이득은 **피해·무적·넉백 판정이 피해를 받는 쪽 한곳에 모인다**는 것입니다. 적마다 판정하면 같은 스텝에 여러 적이 동시에 "무적이 아니네"라고 보고 중복 처리할 여지가 생기고, 규칙이 두 곳에 흩어집니다. 비용은 Profiler에서 겹친 접촉 쌍 수를 기준으로 확인하세요.

### 6단계: 코인 획득도 레이어로 정리

기초 트랙의 `Coin`은 `CompareTag("Player")`로 검사했습니다. 이제 Pickup×Player만 매트릭스에서 켜져 있으므로, 코인의 트리거에 들어오는 것은 플레이어뿐입니다. 태그 검사를 남겨 두어도 되지만, 코인에 붙어 있던 Rigidbody2D(기초 트랙의 낙하용)는 Body Type을 **Kinematic**으로 바꿉니다. 떨어지는 코인이 아니라 바닥에 놓인 코인이므로 중력·충돌 계산이 필요 없고, 02장 `Coin.Attract`가 속도(`linearVelocity`)로 끌려가게 하므로 컴포넌트 자체는 남겨 둡니다.

### 확인하기

- 플레이어가 출발할 때 아주 짧게 가속하고, 키를 떼면 거의 즉시 멈춘다. 반대 방향으로 틀면 빠르게 꺾인다.
- 벽에 대각선으로 비비며 이동해도 달라붙지 않고 미끄러지며, 벽을 뚫지 못한다.
- 적에게 닿으면 체력이 한 번만 줄고, 플레이어가 반대로 튕겨 나가며, 약 0.8초 동안 깜빡이는 동안에는 적에게 겹쳐도 체력이 줄지 않는다.
- 가만히 서서 적이 다가오게 해도 데미지가 들어간다(Never Sleep 확인).
- 코인 근처로 가면 자석(`CoinMagnet`)이 코인을 계속 끌어당긴다(Coin Layers = `Pickup` 확인). 적 프리팹에 `DamageOnTouch`가 남아 있지 않고, 적이 이동 방향에 따라 좌우로 뒤집힌다.
- 적 100마리 이상을 스폰해도 한 점으로 뭉치지 않고 둥근 무리로 퍼진다. `Window > Analysis > Profiler`의 Physics2D 항목이 적끼리 충돌을 켰을 때보다 확연히 낮다.
- 카메라가 따라갈 때 플레이어 스프라이트가 떨리지 않는다(Interpolate 확인 — 꺼 보면 차이가 보입니다).

## 흔한 실수

1. **플레이어가 벽을 뚫는다** → Transform으로 이동하거나 Rigidbody2D가 Kinematic, 또는 넉백 속도가 커서 Discrete 감지를 건너뜀 → Dynamic + `linearVelocity`로 이동하고 Collision Detection을 Continuous로 둡니다.
2. **넉백이 전혀 안 보인다** → 넉백 속도를 넣은 다음 FixedUpdate에서 가속 로직이 입력 방향으로 속도를 덮어씀 → 넉백 직후 짧은 입력 무시 시간을 둡니다.
3. **적에게 닿았는데 `OnTriggerEnter2D`가 안 온다** → 둘 다 Rigidbody2D가 없는 Static끼리이거나, Layer Collision Matrix에서 꺼짐, 또는 양쪽 콜라이더 모두 Is Trigger가 꺼져 Collision 콜백만 옴 → 한쪽에 Rigidbody2D(트리거는 Kinematic이어도 됨)를 두고, 매트릭스와 Is Trigger를 확인합니다. 반대로 `OnCollisionEnter2D`가 Kinematic끼리·Kinematic과 벽 사이에서 안 오는 것은 정상이며, 필요하면 Use Full Kinematic Contacts를 켭니다.
4. **카메라가 따라갈 때 플레이어만 부들부들 떨린다** → 물리 50Hz와 렌더 프레임 불일치 → 플레이어 Rigidbody2D의 Interpolate를 켜고, 카메라는 LateUpdate에서 움직입니다. Interpolate가 켜진 바디의 위치를 `transform.position`으로 직접 대입하지 않습니다.
5. **적 300마리에서 프레임이 급락한다** → 적끼리 충돌을 켠 Dynamic 바디 수백 개, 또는 매 스텝 `OverlapCircleAll` 할당 → Enemy×Enemy 매트릭스를 끄고, 버퍼 재사용 쿼리를 N스텝 간격으로 분산합니다.
6. **대각선 이동이 더 빠르다 / 스틱을 살짝 기울여도 전속력** → 입력 벡터 길이 보정 누락 또는 `normalized` 사용 → `Vector2.ClampMagnitude(input, 1f)`.
7. **코인이 자석에 끌려오지 않는다** → 코인 프리팹을 `Pickup` 레이어로 옮겼는데 `CoinMagnet`의 Coin Layers가 여전히 `Coin` → Coin Layers를 `Pickup`으로 바꿉니다.

## 연습 문제

**1. ★☆☆ 대시**
Space(또는 게임패드 South 버튼)를 누르면 이동 방향으로 0.15초 동안 속도 18로 돌진하고, 쿨다운 1초를 두세요. 대시 중에는 무적입니다.

<details>
<summary>힌트·해설</summary>

- Update에서 `Keyboard.current.spaceKey.wasPressedThisFrame`을 읽어 `dashRequested = true`로 저장하고, FixedUpdate에서 소비합니다(입력은 Update, 물리는 FixedUpdate).
- `ApplyKnockback(Facing * 18f, 0.15f)`만 재사용하면 **"0.15초 동안 속도 18"이 되지 않습니다.** 넉백은 속도를 한 번 넣고 이후 스텝마다 감속(`maxSpeed / decelTime` = 6 / 0.06 = 초당 100, 스텝당 2)을 적용하므로 18 → 16 → 14…로 줄어듭니다. 대시는 끝날 때까지 속도를 **유지**하는 별도 분기가 필요합니다.

```csharp
// PlayerMover.cs — 필드 추가
private float dashUntil;
private Vector2 dashVelocity;
private bool dashRequested;
private float nextDashTime;
public bool IsDashing => Time.time < dashUntil;

// Update 끝에 추가 (08장에서 액션으로 교체)
if (Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame) dashRequested = true;

// FixedUpdate 맨 앞에 추가
if (dashRequested)
{
    dashRequested = false;
    if (CanMove && Time.time >= nextDashTime)
    {
        dashVelocity = Facing * 18f;
        dashUntil = Time.time + 0.15f;
        nextDashTime = Time.time + 1f;          // 쿨다운
    }
}
if (IsDashing)
{
    rb.linearVelocity = dashVelocity;           // 대시 중에는 매 스텝 속도 유지, 일반 가감속 건너뜀
    return;
}
```

  대시가 끝난 다음 스텝부터는 기존 감속 로직이 18에서 자연스럽게 속도를 줄입니다.
- 무적은 04장과 같은 플래그를 씁니다. 대시 시작에 `health.Invulnerable = true`, 0.15초 뒤 `false`로 되돌립니다(깜빡임은 Hurt 상태에만 있으므로 대시에는 생기지 않음). Hurt 무적 중에 대시가 끝나며 플래그를 끄지 않도록, 끄기 전에 `PlayerStateController.State != PlayerState.Hurt`인지 확인합니다.

</details>

**2. ★★☆ 레이캐스트로 시야 판정**
05장의 시야각 판정에 "벽 뒤에 있으면 안 보임"을 추가하세요. 적 → 플레이어 방향으로 `Physics2D.Raycast`를 쏘아 `Wall` 레이어에 먼저 맞으면 보이지 않는 것으로 처리합니다.

<details>
<summary>힌트·해설</summary>

```csharp
Vector2 origin = transform.position;
Vector2 toPlayer = (Vector2)player.position - origin;
RaycastHit2D hit = Physics2D.Raycast(origin, toPlayer.normalized, toPlayer.magnitude, LayerMask.GetMask("Wall"));
bool blocked = hit.collider != null;
```

마스크에 Wall만 넣고 거리를 플레이어까지로 제한하면 "플레이어보다 가까운 벽이 있는가"만 묻게 됩니다. 마스크에 Player까지 넣고 첫 충돌이 플레이어인지 확인하는 방법도 있지만, 적 자신의 콜라이더에 맞는 문제(`Physics2D.queriesStartInColliders`)를 신경 써야 합니다.

</details>

**3. ★★☆ 오브 무기에 넉백 추가**
06장의 `OrbitWeapon`이 적을 때릴 때 적을 플레이어 반대 방향으로 짧게 밀어내도록 하세요.

<details>
<summary>힌트·해설</summary>

`DamageAt`에서 데미지를 준 직후 `hits[h].TryGetComponent<EnemyMotor2D>(out var motor)`로 모터를 얻고, 방향은 `(hits[h].transform.position - transform.position).normalized`(오브 무기의 중심 = 플레이어)입니다. `motor.ApplyKnockback(dir * 3f, 0.1f)`. 무기 데이터에 `knockback` 수치가 없으므로 `OrbitWeapon`의 `[SerializeField]`로 두거나, 03장의 `WeaponData`에 필드를 추가합니다. 넉백이 강하면 적이 궤도 밖으로 튕겨 나가 오브가 한 번만 맞히게 되므로, 넉백 거리 < 오브 반지름이 되게 조정합니다.

</details>

**4. ★★★ 격자 기반 분리 (확장 과제)**
적 1000마리에서 `EnemyMotor2D`의 물리 쿼리를 없애세요. 매 FixedUpdate에 한 번, 모든 적의 위치를 셀 크기 1인 격자 `Dictionary<Vector2Int, List<EnemyMotor2D>>`에 넣고, 각 적은 자기 셀과 주변 8칸의 이웃만 검사합니다. 프로파일러로 전후를 비교하세요.

<details>
<summary>힌트·해설</summary>

- 관리자 `EnemySwarm` MonoBehaviour가 활성 적 목록을 들고(`OnEnable`/`OnDisable`에서 등록·해제), `FixedUpdate`에서 격자를 재구성합니다. 스크립트 실행 순서(`[DefaultExecutionOrder(-100)]`)로 적들의 FixedUpdate보다 먼저 돌게 합니다.
- 매 스텝 `new List`를 만들면 GC가 폭발하므로(02장) 리스트를 풀에 보관해 `Clear()` 후 재사용합니다.
- 더 나아가면 적 개별 FixedUpdate를 없애고 관리자가 모든 적의 속도를 한 루프에서 설정합니다(수백 개의 MonoBehaviour 메시지 호출 비용 제거). 이것이 18장의 "매니저 업데이트 패턴"이며, 그다음 단계가 Jobs + Burst입니다.

</details>

## 셀프 체크

**1. 캐릭터 이동에 `AddForce` 대신 `linearVelocity`를 직접 설정하는 이유와, 그래도 `AddForce`가 어울리는 경우를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

기획이 원하는 것은 "최고 속도, 가속 시간, 감속 시간" 같은 직접적인 수치인데, `AddForce`는 질량·Damping·힘의 조합으로 결과가 간접 결정되어 튜닝이 어렵고 입력 반응도 둔해집니다. 원하는 속도를 코드로 계산해 `linearVelocity`에 넣으면 수치가 곧 조작감이 됩니다. 반면 폭발, 바람, 자석처럼 **여러 외력이 합쳐지는 효과**나 물리적으로 그럴듯한 반응이 필요한 오브젝트(상자, 파편)에는 `AddForce`가 자연스럽습니다.

</details>

**2. 입력은 Update에서, 물리 조작은 FixedUpdate에서 하는 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

FixedUpdate는 고정 간격으로 호출되어 한 렌더 프레임에 0번 또는 여러 번 호출됩니다. "이번 프레임에 눌렸다" 같은 입력을 FixedUpdate에서 읽으면 FixedUpdate가 없는 프레임의 입력을 놓치거나 여러 번 처리합니다. 반대로 속도·힘을 Update에서 바꾸면 프레임 수에 따라 적용 횟수가 달라져 결과가 프레임 속도에 의존합니다. 그래서 Update에서 입력을 필드에 저장하고 FixedUpdate에서 소비합니다.

</details>

**3. Interpolate가 해결하는 문제와, 모든 적에 켜지 않는 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

물리 위치는 50Hz로만 갱신되므로 더 높은 주사율 화면에서는 같은 위치가 반복 표시되다 튀어, 특히 카메라가 따라가는 대상이 떨려 보입니다. Interpolate는 직전 두 물리 스텝 사이를 보간해 매 프레임 매끄러운 위치를 표시합니다. 대신 바디마다 추가 계산과 최대 한 스텝의 표시 지연이 생기므로, 카메라가 따라가지 않고 수가 많은 적에게는 체감 이득 대비 비용이 큽니다.

</details>

**4. 무적 시간이 없을 때와 입력 무시 시간이 없을 때 각각 어떤 문제가 생기는지 설명해 보세요.**

<details>
<summary>모범 답안</summary>

무적 시간이 없으면 `OnTriggerStay2D`가 물리 스텝마다 호출되어 적과 겹친 동안 초당 50번 데미지가 들어가 순식간에 죽습니다. 입력 무시 시간이 없으면 넉백으로 넣은 속도를 바로 다음 스텝에서 가속 로직이 입력 방향으로 되돌려 넉백이 보이지 않습니다. 또 무적 중임을 깜빡임 등으로 보여 주지 않으면 플레이어는 "데미지가 안 들어가는 버그"로 인식합니다.

</details>

**5. 적 수백 마리의 겹침을 물리 충돌 대신 분리 힘으로 처리하는 이유와 비용을 줄이는 방법을 설명해 보세요.**

<details>
<summary>모범 답안</summary>

적끼리 충돌을 켜면 뭉칠수록 접촉 쌍이 급증해 솔버 비용이 커지고, 밀치기 연쇄로 떨림도 생깁니다. Enemy×Enemy를 매트릭스에서 끄고, 각 적이 주변 이웃에게서 멀어지는 벡터를 이동 방향에 더하면 약간의 겹침만 허용하면서 무리가 퍼집니다. 비용은 이웃 검사 주기를 N스텝으로 늘리고 적마다 시점을 어긋나게 하며, 버퍼 크기로 이웃 수 상한을 두고, 더 많아지면 격자 공간 분할이나 Jobs로 옮겨 줄입니다.

</details>

## 핵심 요약

- Dynamic은 힘·충돌에 반응, Kinematic은 스크립트가 몰고 밀리지 않음, Static은 고정. 움직이는 콜라이더에는 Rigidbody2D를 반드시 붙입니다.
- 캐릭터 조작은 Dynamic + `linearVelocity` 직접 설정, 외력은 `AddForce`. Unity 6에선 `velocity`/`drag` 대신 `linearVelocity`/`linearDamping`.
- 입력은 Update에서 저장하고 FixedUpdate에서 물리에 적용합니다. 카메라가 따라가는 바디는 Interpolate, 벽에 막혀야 하는 빠른 바디는 Continuous(트리거에는 적용되지 않으므로 빠른 트리거 탄은 캐스트로 보강).
- Layer Collision Matrix로 불필요한 쌍(특히 Enemy×Enemy)을 끄면 버그와 비용이 함께 줄어듭니다.
- Collision 콜백은 Kinematic끼리·Kinematic과 Static 사이에 기본으로 오지 않지만(Use Full Kinematic Contacts 필요), Trigger 콜백은 한쪽에 Rigidbody2D만 있으면 옵니다. 정지해도 Stay가 필요하면 Never Sleep.
- Physics2D 쿼리는 `ContactFilter2D` + 재사용 버퍼 오버로드로 할당 없이 씁니다.
- 조작감은 가속·감속·방향 전환 수치를 분리해 설계하고, 피격은 데미지 + 넉백 + 입력 무시 + 보이는 무적 시간의 묶음입니다.

## 더 읽을거리

- Unity 매뉴얼 — Rigidbody 2D (Body Type, Interpolate, Collision Detection): https://docs.unity3d.com/Manual/rigidbody2D.html
- Unity 매뉴얼 — Layer-based collision detection: https://docs.unity3d.com/Manual/LayerBasedCollision.html
- Unity 스크립팅 API — `Physics2D.OverlapCircle`, `ContactFilter2D`: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircle.html
- Steve Swink, 『Game Feel: A Game Designer's Guide to Virtual Sensation』 (Morgan Kaufmann, 2008)
- Craig W. Reynolds, "Steering Behaviors For Autonomous Characters" (GDC 1999) — separation 등 조향 규칙
