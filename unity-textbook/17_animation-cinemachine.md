# 17. 애니메이션·트윈·Cinemachine

> **이 장에서 배울 것**
> - Animator Controller의 파라미터·전이·Has Exit Time·Any State를 설명하고, 흔한 "애니메이션이 늦게 바뀌는" 버그를 고칠 수 있다
> - 2D 블렌드 트리로 4방향 걷기/대기 애니메이션을 만들고 `Animator.StringToHash`로 파라미터를 제어한다
> - Animation Event와 트윈 라이브러리(PrimeTween/DOTween)로 연출 타이밍을 맞추고, timeScale을 무시하는 UI 트윈을 만든다
> - Cinemachine 3(`com.unity.cinemachine` 3.x)으로 추적 카메라·맵 경계·Impulse 흔들림을 구성하고 2.x와의 이름 차이를 구분할 수 있다
> - Timeline으로 보스 등장 컷신을 만들고 게임 흐름과 연결한다
>
> **선수 장**: 04, 08, 11, 16 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 플레이어가 방향에 맞춰 걷고 멈추며, 카메라가 맵 경계 안에서 부드럽게 따라옵니다. 레벨업 카드가 튀어나오고, 5분에 (연출용) 보스가 컷신과 함께 등장합니다. 보스 전투는 22장에서 붙입니다.

## 왜 필요한가

지금 코인 러시의 플레이어는 스프라이트 한 장이 미끄러지듯 움직입니다. 16장까지의 연출을 넣어도 캐릭터 자체가 살아있지 않으면 "싸구려" 인상이 남습니다. 그리고 아래 문제가 쌓여 있습니다.

- **카메라**: 06장에서 만든 추적 카메라(`CameraFollow2D`)는 맵 끝에서 바깥 빈 공간을 보여줍니다. 경계 처리를 직접 짜면 화면 비율(16:9, 19.5:9 폰)마다 계산이 달라집니다.
- **흔들림 충돌**: 16장의 흔들림은 CameraRig 계층 분리로 버텼지만, 카메라 전환·줌이 들어가면 또 충돌합니다.
- **UI**: 레벨업 패널이 "뿅" 하고 나타납니다. `Update`에서 스케일을 손으로 보간하는 코드가 패널마다 복붙되어 있습니다.
- **보스 등장**: "카메라가 보스를 비추고 → 이름이 뜨고 → 다시 플레이어로"를 코루틴 대기 시간 숫자로 짜면, 연출 하나 바꿀 때마다 코드를 고쳐야 합니다.

이 장의 도구들은 모두 "직접 만들지 말라"는 영역입니다. Animator·Cinemachine·Timeline은 에디터에서 **데이터로** 연출을 만들게 해 주고, 코드는 파라미터 몇 개만 건드립니다.

## 개념

### Animator Controller — 상태 머신 에셋

Animator Controller는 04장에서 코드로 만든 상태 머신을 **그래프 에셋**으로 만든 것입니다. `Animator` 컴포넌트가 이 에셋을 실행합니다.

```
[Animator Controller: Player]
 Parameters: MoveX(Float) MoveY(Float) Speed(Float) Hit(Trigger)

 (Entry) ──▶ [Idle 블렌드 트리] ──Speed > 0.1──▶ [Walk 블렌드 트리]
                     ▲                                  │
                     └────────────Speed < 0.1───────────┘
 (Any State) ──Hit──▶ [Hurt] ──Has Exit Time(1.0)──▶ [Idle]
```

| 요소 | 의미 | JS 비유 |
|---|---|---|
| State | 재생할 클립(또는 블렌드 트리) | reducer의 상태 값 |
| Parameter | 코드가 쓰는 입력: Float, Int, Bool, **Trigger** | dispatch하는 action의 payload |
| Transition | 상태 간 화살표 + 조건 | `if (state === 'idle' && speed > 0.1)` |
| Trigger | 한 번 소비되면 자동으로 꺼지는 Bool | 일회성 이벤트 |
| Layer | 동시에 돌아가는 별도 상태 머신(상체/하체 등) | 병렬 reducer |

### Has Exit Time의 함정

전이를 새로 만들면 **Has Exit Time이 켜진 상태**로 생성됩니다. 이 옵션이 켜져 있으면 조건이 만족돼도 **현재 클립이 Exit Time(기본 약 0.75~1.0 정규화 시간)까지 재생된 뒤에야** 넘어갑니다. 그래서 "키를 눌렀는데 걷기 애니메이션이 반 박자 늦게 시작한다"가 됩니다.

| 전이 종류 | Has Exit Time | Transition Duration | 이유 |
|---|---|---|---|
| Idle ↔ Walk (입력 반응) | **끔** | 2D 스프라이트는 **0** | 즉시 반응해야 함. 스프라이트는 섞을(블렌드) 수 없음 |
| Hurt → Idle (끝나면 복귀) | **켬**, Exit Time 1 | 0 | 조건 없이 클립이 끝나면 넘어감 |
| Attack → Idle | 켬 | 0 | 공격 모션이 끝까지 재생돼야 함 |

2D 스프라이트 애니메이션은 두 클립을 "섞을" 수 없으므로 Transition Duration이 0보다 크면 전이 중 이전 클립 프레임이 보이는 어색함이 생깁니다. 또 조건이 전혀 없는 전이에서 Has Exit Time까지 끄면 "Exit Time도 조건도 없으므로 전이가 무시된다"는 경고가 뜨고 **그 전이는 동작하지 않습니다**. 즉시 넘어가게 하려면 Has Exit Time을 끄고, 그 순간 충족되는 조건(예: Trigger)을 반드시 하나 이상 둡니다.

### Any State 조심해서 쓰기

**Any State**는 "어느 상태에서든" 전이할 수 있는 특수 노드입니다. 피격·사망처럼 언제든 끼어드는 상태에 씁니다. 함정은 두 가지입니다.

1. **Can Transition To Self**(기본 켬): 조건이 계속 참이면(예: Bool `IsDead`) 매 프레임 자기 자신으로 다시 전이해 **첫 프레임에 고정**됩니다. Any State 전이는 대부분 이 옵션을 끄거나 Trigger를 씁니다.
2. 남용하면 모든 상태에서 화살표가 뻗은 것과 같아 우선순위를 추적하기 어렵습니다. 피격·사망 정도로 제한합니다.

### 블렌드 트리 — 2D 방향 이동

4방향(또는 8방향) 걷기를 상태 4개와 전이 12개로 만들면 거미줄이 됩니다. **블렌드 트리**는 파라미터 값에 따라 클립을 고르는 하나의 상태입니다.

```
2D Simple Directional 블렌드 트리 (Walk)
            MoveY
              ▲  (0, 1) Walk_Up
              │
(-1,0) ───────┼─────── (1,0) Walk_Right
Walk_Left     │
              ▼  (0,-1) Walk_Down
            
입력 (0.7, 0.7) → 가장 가까운 방향 클립(스프라이트는 섞이지 않으므로 사실상 선택)
```

| 블렌드 타입 | 용도 |
|---|---|
| 1D | 속도 하나로 걷기↔달리기 |
| 2D Simple Directional | 방향별 클립이 하나씩(4/8방향 스프라이트) |
| 2D Freeform Directional | 같은 방향에 속도가 다른 클립이 여러 개(3D 캐릭터) |
| 2D Freeform Cartesian | 방향 의미가 없는 두 축 |

멈췄을 때 마지막 방향을 바라보게 하려면 Idle 블렌드 트리에도 같은 구조를 만들고, 코드에서 **움직이는 동안만** 방향 파라미터를 갱신합니다.

### Animator.StringToHash

`animator.SetFloat("MoveX", x)`는 매 호출마다 문자열을 해시로 바꿉니다. 정적 필드에 미리 계산해 둡니다(16장의 `Shader.PropertyToID`와 같은 원리).

```csharp
static readonly int MoveXId = Animator.StringToHash("MoveX");
animator.SetFloat(MoveXId, x);
```

파라미터 이름을 오타 내면 에러 대신 경고 한 줄만 나오고 아무 일도 일어나지 않으니, 해시 필드를 한 곳에 모아 두는 편이 안전합니다.

### Animation Event

클립의 특정 프레임에서 **같은 GameObject**에 붙은 스크립트의 public/private 메서드를 이름으로 호출합니다. 발소리, 공격 판정 시작, 이펙트 생성 타이밍을 모션에 맞출 때 씁니다.

- 매개변수는 없음, 또는 `float`/`int`/`string`/`Object`/`AnimationEvent` 하나만 가능합니다.
- 수신 메서드가 없으면 "AnimationEvent 'X' has no receiver" 에러가 납니다. `Animator`가 자식 `Visual`에 있으면 수신 스크립트도 `Visual`에 붙여야 합니다.
- 블렌드 트리에서는 가중치가 있는 클립들의 이벤트가 모두 호출될 수 있습니다. 2D Simple Directional에서 대각선 입력이면 발소리가 두 번 날 수 있으니, 수신 쪽에서 짧은 쿨다운을 둡니다.

### 2D 스프라이트 애니메이션과 2D Animation 패키지

| 방식 | 만드는 법 | 장점 | 단점 |
|---|---|---|---|
| 프레임 애니메이션 | 스프라이트 시트를 잘라 프레임을 클립으로 | 픽셀 아트에 적합, 단순 | 프레임 수만큼 그림 필요 |
| 본 리깅 (`com.unity.2d.animation`) | 파츠로 나뉜 그림에 뼈를 심고 뼈를 회전 | 적은 그림으로 부드러운 모션 | 리깅 작업, 런타임 비용 |
| Spine 등 외부 도구 | 외부에서 만들고 런타임으로 재생 | 2D 모바일 업계 표준급 | 유료 라이선스, 별도 런타임 |

2D Animation 패키지의 흐름은 이렇습니다: 포토샵 파일을 레이어별 파츠로 가져오기(`com.unity.2d.psdimporter`) → Sprite Editor의 **Skinning Editor**에서 뼈 만들기·메시 생성·가중치 칠하기 → 씬에서 **Sprite Skin** 컴포넌트가 뼈 Transform에 따라 메시를 변형 → Animation 창에서 뼈 회전을 키프레임. 코인 러시는 작은 픽셀풍 캐릭터라 프레임 애니메이션을 씁니다. 수백 마리 적에 본 리깅을 쓰면 CPU 비용이 커지니 18장에서 측정해 보세요.

### 트윈 라이브러리 — DOTween과 PrimeTween

"A에서 B로 0.3초 동안 이징을 걸어 바꾸기"는 UI·연출의 80%를 차지합니다. 트윈 라이브러리를 씁니다.

| 항목 | DOTween (무료판) | PrimeTween |
|---|---|---|
| 배포 | Asset Store, 오래된 사실상 표준 | Asset Store / GitHub, 비교적 신생 |
| 문법 | 확장 메서드 체이닝 `transform.DOScale(1, .3f).SetEase(...)` | 정적 메서드 + 이름 있는 인수 `Tween.Scale(transform, 1, .3f, Ease.OutBack)` |
| 할당 | 트윈 재사용 풀이 있지만 람다·시퀀스 생성 시 할당 발생 | 트윈 생성 시 GC 할당 0을 설계 목표로 명시 |
| timeScale 무시 | `.SetUpdate(true)` | `useUnscaledTime: true` 인수 |
| 오브젝트 파괴 시 | `.SetLink(gameObject)` 권장 | 대상이 파괴되면 자동 정지 |
| 자료 | 매우 많음 | 적지만 문서가 간결 |

코인 러시는 할당 0 원칙(02장)과 짧은 문법 때문에 **PrimeTween**을 씁니다. 이미 DOTween을 쓰고 있다면 바꿀 이유는 약합니다. 아래 표로 대응 관계만 알아두세요. (두 라이브러리 모두 버전에 따라 시그니처가 달라질 수 있으니 설치한 버전의 문서를 확인하세요.)

| 하고 싶은 것 | DOTween | PrimeTween |
|---|---|---|
| 스케일 | `t.DOScale(1.2f, 0.2f).SetEase(Ease.OutBack)` | `Tween.Scale(t, 1.2f, 0.2f, Ease.OutBack)` |
| 펀치 | `t.DOPunchScale(Vector3.one * 0.2f, 0.2f)` | `Tween.PunchScale(t, Vector3.one * 0.2f, 0.2f)` |
| UI 위치 | `rt.DOAnchorPos(pos, 0.3f)` | `Tween.UIAnchoredPosition(rt, pos, 0.3f)` |
| 페이드 | `canvasGroup.DOFade(1, 0.2f)` | `Tween.Alpha(canvasGroup, 1, 0.2f)` |
| 일시정지 중 재생 | `.SetUpdate(true)` | `useUnscaledTime: true` |
| 순차 실행 | `DOTween.Sequence().Append(a).Append(b)` | `Sequence.Create().Chain(a).Chain(b)` |
| 완료 콜백 | `.OnComplete(() => ...)` | `.OnComplete(() => ...)` |

**timeScale 무시**는 이 게임에서 중요합니다. 레벨업 패널은 `GameFeel.SetPaused(true)`로 `timeScale = 0`인 상태에서 뜨므로, 기본 트윈은 한 프레임도 진행하지 않습니다.

### Cinemachine 3 — 2.x와 이름이 다르다

Unity 6에서 Package Manager로 설치하는 Cinemachine은 **3.x**(`com.unity.cinemachine`)입니다. 인터넷 자료 대부분은 2.x 기준이라 이름이 맞지 않습니다.

| 2.x | 3.x | 비고 |
|---|---|---|
| `using Cinemachine;` | `using Unity.Cinemachine;` | 네임스페이스 |
| `CinemachineVirtualCamera` | `CinemachineCamera` | 카메라 본체 |
| `CinemachineFramingTransposer` | `CinemachinePositionComposer` | 화면 기준으로 대상을 프레이밍(2D 추적에 적합) |
| `CinemachineTransposer` | `CinemachineFollow` | 월드 오프셋 기준 추적 |
| `CinemachineComposer` | `CinemachineRotationComposer` | 회전으로 조준 |
| `CinemachineFreeLook` | `CinemachineCamera` + `CinemachineOrbitalFollow` | 3D 궤도 카메라 |
| `Follow` / `LookAt` 필드 | `Target.TrackingTarget` / `Target.LookAtTarget` | 인스펙터 이름 Tracking Target |
| `m_Lens` | `Lens` | `m_` 접두사 필드가 대부분 사라짐 |
| `CinemachineConfiner` | `CinemachineConfiner2D` / `CinemachineConfiner3D` | 2D는 이름 그대로 |
| `CinemachineImpulseSource/Listener` | 이름 동일 | 설정 필드 구성은 일부 다름 |

구조는 같습니다. **실제 Camera는 하나**이고 거기에 `CinemachineBrain`이 붙습니다. 씬에 여러 `CinemachineCamera`(가상 카메라)를 두면, Brain이 우선순위가 가장 높은(같으면 가장 최근에 활성화된) 카메라의 설정대로 실제 카메라를 움직이고, 바뀔 때 블렌드합니다.

```
Main Camera (Camera, CinemachineBrain)     ← 실제로 렌더링
CM_Follow  (CinemachineCamera, PositionComposer, Confiner2D, ImpulseListener)
CM_Boss    (CinemachineCamera, 비활성)     ← 활성화하면 Brain이 블렌드하며 전환
```

- **Position Composer**: Dead Zone(대상이 이 영역 안이면 카메라가 안 움직임), Damping(따라가는 지연), Lookahead(이동 방향 앞쪽을 더 보여줌).
- **Confiner2D**: `Collider2D`(PolygonCollider2D 등) 모양 안으로 카메라 **화면 전체**를 가둡니다. 화면 비율과 orthographic size를 고려해 계산해 줍니다.
- **Impulse**: `CinemachineImpulseSource`가 신호를 발생시키고, 카메라의 `CinemachineImpulseListener` 확장이 받아 흔듭니다. 추적과 흔들림이 Cinemachine 파이프라인 안에서 합쳐지므로 16장의 계층 분리가 필요 없습니다.

### Timeline — 시간축 위의 연출

Timeline(`com.unity.timeline`)은 비디오 편집기처럼 트랙 위에 클립을 배치해 여러 오브젝트를 동기화합니다. `PlayableDirector` 컴포넌트가 Timeline 에셋(`.playable`)을 재생합니다.

| 트랙 | 하는 일 | 보스 등장에서 |
|---|---|---|
| Activation Track | 구간 동안 GameObject 활성화 | 보스 이름 배너 표시 |
| Animation Track | Animator에 클립 재생 또는 녹화한 키프레임 | 보스가 화면 밖에서 걸어 들어옴 |
| Audio Track | 오디오 클립 재생 | 경고음, 보스 BGM 시작 |
| Cinemachine Track | 구간마다 활성 CinemachineCamera 지정·블렌드 | 플레이어 → 보스 → 플레이어 |
| Signal Track | 특정 시점에 `SignalAsset` 발생 → `SignalReceiver`가 UnityEvent 실행 | 컷신 끝에 AI 시작 |

Signal은 Timeline과 게임 코드를 느슨하게 연결하는 방법입니다(03장 이벤트 채널과 비슷한 역할).

## 실습: 코인 러시에 적용하기

스크립트는 `Assets/_CoinRush/Scripts/Animation/`, `Scripts/Camera/`에 둡니다. 이 장의 코드는 아래 버전을 기준으로 작성했습니다. 메이저·마이너 버전이 다르면 API 이름이 바뀌었을 수 있으니, 가능하면 같은 줄의 버전을 설치하세요.

| 패키지 | 기준 버전 | 설치 |
|---|---|---|
| Unity 에디터 | 6000.0 LTS | Unity Hub |
| Cinemachine (`com.unity.cinemachine`) | 3.1.x | Window → Package Manager → Unity Registry → Cinemachine → Install (3.x인지 버전 표시 확인) |
| Timeline (`com.unity.timeline`) | 1.8.x | 같은 방법. 2D 템플릿에 이미 들어 있으면 In Project에 보입니다 |
| PrimeTween | 1.3.x | Asset Store에서 PrimeTween을 내 에셋에 추가 → Package Manager → My Assets → Download → Import |

설치 후 Package Manager의 In Project 목록에서 실제 버전을 확인해 두세요. 이 장의 PrimeTween 호출(`Tween.Scale`, `Tween.Alpha`, `Tween.UIAnchoredPosition`, `Tween.PunchScale`, `Tween.StopAll`, `Sequence.Create`)이 컴파일되지 않으면 버전이 다른 것입니다.

### 1단계: 4방향 스프라이트 클립 만들기

1. 플레이어 스프라이트 시트(4방향 × 걷기 4프레임 + 대기 2프레임)를 임포트하고 Sprite Mode `Multiple`, Sprite Editor에서 Grid by Cell Size로 자릅니다.
2. 플레이어 프리팹 구조를 `Player`(Rigidbody2D, Collider, PlayerMover, Health) → 자식 `Visual`(SpriteRenderer)로 둡니다(16장과 같은 구조).
3. `Visual`을 선택하고 Window → Animation → Animation 창에서 **Create** → `Player_WalkDown.anim`으로 저장합니다. 이때 `Visual`에 Animator와 `Player.controller`가 자동 생성됩니다.
4. 아래 방향 걷기 프레임 4장을 Animation 창 타임라인으로 드래그합니다. Samples(프레임 속도)를 8~10으로 둡니다(Animation 창 우측 메뉴의 Show Sample Rate).
5. 클립 드롭다운 → Create New Clip으로 `WalkUp`, `WalkLeft`, `WalkRight`, `IdleDown`, `IdleUp`, `IdleLeft`, `IdleRight`를 같은 방식으로 만듭니다. 오른쪽 그림이 없다면 WalkRight를 따로 만들지 말고, 코드에서 `flipX`로 뒤집는 방법도 있습니다(연습 문제 1).
6. Project 창에서 각 클립을 선택해 **Loop Time**이 켜져 있는지 확인합니다.

### 2단계: Animator Controller와 블렌드 트리

1. `Player.controller`를 더블클릭해 Animator 창을 엽니다. 자동으로 생긴 상태들은 삭제합니다.
2. Parameters 탭에서 Float `MoveX`, `MoveY`, `Speed`와 Trigger `Hit`를 추가합니다.
3. 빈 곳 우클릭 → Create State → From New Blend Tree → 이름 `Idle`. 더블클릭해 들어가서 Blend Type `2D Simple Directional`, Parameters `MoveX`/`MoveY`로 두고 Motion 4개를 추가해 `IdleDown (0,-1)`, `IdleUp (0,1)`, `IdleLeft (-1,0)`, `IdleRight (1,0)`로 Pos X/Y를 입력합니다.
4. 같은 방식으로 `Walk` 블렌드 트리를 만듭니다. `Idle`을 우클릭 → Set as Layer Default State.
5. `Idle → Walk` 전이: 조건 `Speed Greater 0.1`, **Has Exit Time 끔**, Settings의 Transition Duration **0**.
6. `Walk → Idle` 전이: 조건 `Speed Less 0.1`, 나머지 동일.
7. 피격 클립 `Hurt`(흰 번쩍임 대신 움찔 포즈 2프레임, Loop Time 끔)로 상태를 만들고 `Any State → Hurt`: 조건 `Hit`, Has Exit Time 끔, Duration 0, **Can Transition To Self 끔**. `Hurt → Idle`: 조건 없음, Has Exit Time 켬, Exit Time 1, Duration 0.

방향 파라미터는 `MoveX/MoveY` 하나로 Idle·Walk가 공유합니다. 코드는 움직일 때만 방향을 갱신하므로, 멈추면 마지막 방향의 Idle이 선택됩니다.

```csharp
// Assets/_CoinRush/Scripts/Animation/PlayerAnimator.cs  (Visual에 부착)
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class PlayerAnimator : MonoBehaviour
{
    static readonly int MoveXId = Animator.StringToHash("MoveX");
    static readonly int MoveYId = Animator.StringToHash("MoveY");
    static readonly int SpeedId = Animator.StringToHash("Speed");
    static readonly int HitId = Animator.StringToHash("Hit");

    [SerializeField] Rigidbody2D body;        // 부모 Player의 Rigidbody2D
    [SerializeField] Health health;           // 부모 Player의 Health
    [SerializeField] float moveThreshold = 0.1f;
    [SerializeField] SfxData footstepSfx;     // 12장 SfxData (클립 여러 개·피치 범위 포함)
    [SerializeField] float footstepCooldown = 0.12f;

    Animator animator;
    int lastHp;
    float lastFootstepTime;

    void Awake() => animator = GetComponent<Animator>();

    void OnEnable()
    {
        lastHp = health.Current;
        health.Changed += OnHealthChanged;
    }

    void OnDisable() => health.Changed -= OnHealthChanged;

    void Update()
    {
        Vector2 v = body.linearVelocity;
        float speed = v.magnitude;
        animator.SetFloat(SpeedId, speed);

        if (speed > moveThreshold)
        {
            // 4방향으로 스냅: 더 큰 축만 남김 (대각선에서 클립이 튀는 것 방지)
            Vector2 dir = Mathf.Abs(v.x) > Mathf.Abs(v.y)
                ? new Vector2(Mathf.Sign(v.x), 0f)
                : new Vector2(0f, Mathf.Sign(v.y));
            animator.SetFloat(MoveXId, dir.x);
            animator.SetFloat(MoveYId, dir.y);
        }
    }

    void OnHealthChanged(int current, int max)
    {
        if (current < lastHp) animator.SetTrigger(HitId);
        lastHp = current;
    }

    // Animation Event에서 이름으로 호출 (Walk 클립의 발 닿는 프레임)
    void OnFootstep()
    {
        if (Time.time - lastFootstepTime < footstepCooldown) return; // 블렌드 중복 호출 방지
        lastFootstepTime = Time.time;
        if (footstepSfx != null) AudioManager.Instance.PlaySfx(footstepSfx);   // 12장 AudioManager
    }
}
```

에디터 작업: `Visual`(Animator가 있는 오브젝트)에 `PlayerAnimator`를 추가하고, **Body**에 부모 `Player`를 드래그(Rigidbody2D가 들어감), **Health**에도 부모 `Player`를 드래그합니다. 두 칸이 비어 있으면 `OnEnable`의 `health.Current`에서 `NullReferenceException`이 납니다. Footstep Sfx는 12장에서 만든 발소리 `SfxData`를 연결합니다(비워 두면 소리만 안 남).

4방향 스냅을 코드에서 하는 이유: 대각선 입력(0.7, 0.7)에서 두 축 크기가 비슷하면 프레임마다 Right/Up이 번갈아 선택되어 깜빡일 수 있습니다. 한 축만 남기면 안정적입니다.

### 3단계: Animation Event로 발소리

1. `Visual`을 선택한 상태에서 Animation 창에 `WalkDown` 클립을 엽니다.
2. 발이 땅에 닿는 프레임(보통 1, 3번째)으로 재생 헤드를 옮기고, 타임라인 위 **Add Event** 버튼(깃발 모양 아이콘)을 누릅니다.
3. 생긴 이벤트 마커를 선택하고 Inspector의 Function에 `OnFootstep`을 입력(또는 선택)합니다.
4. 나머지 세 Walk 클립에도 반복합니다.

Play 후 걸으면 발소리가 나고, 콘솔에 "has no receiver" 에러가 없어야 합니다. 에러가 나면 `PlayerAnimator`가 Animator와 **같은 오브젝트(Visual)**에 있는지 확인합니다.

### 4단계: 트윈으로 레벨업 카드와 코인 카운터

11장의 `LevelUpPanel`을 PrimeTween 버전으로 교체합니다. 카드 3장이 아래에서 순서대로 튀어 오르고, 전체가 페이드 인합니다. 패널이 열릴 때 `timeScale`이 0이므로 시퀀스에 `useUnscaledTime: true`를 줍니다.

11장 코드에서 **그대로 지켜야 할 계약**이 있습니다. `Show(UpgradeData[], Action<UpgradeData>)` 시그니처와 선택 콜백, `choosing` 초기화, `HideImmediate()`가 끈 `blocksRaycasts`를 다시 켜기, 연출이 끝난 뒤 게임패드용 카드 선택입니다. 코루틴과 `EaseOutBack`만 트윈으로 바뀌므로 파일 전체를 교체합니다.

카드 루트(`Card`)는 11장의 Horizontal Layout Group이 위치를 정합니다. 레이아웃이 다시 계산되면 루트의 `anchoredPosition`을 덮어쓰므로, **올라오는 움직임은 자식 `Body`에**(루트 기준 stretch, 원래 위치 `(0, 0)`), 등장 스케일은 11장처럼 루트에 겁니다. `ButtonPunch`는 `Body`의 스케일만 쓰므로 위치 트윈과 겹치지 않습니다.

```csharp
// Assets/_CoinRush/Scripts/UI/LevelUpPanel.cs  (11장 파일 교체)
using System;
using PrimeTween;
using UnityEngine;
using UnityEngine.EventSystems;

[RequireComponent(typeof(CanvasGroup))]
public class LevelUpPanel : MonoBehaviour
{
    [SerializeField] private UpgradeCardView[] cards = new UpgradeCardView[3];   // 11장과 같은 필드
    [SerializeField] private float fadeDuration = 0.15f;
    [SerializeField] private float cardDuration = 0.25f;
    [SerializeField] private float cardRise = 120f;

    private CanvasGroup group;
    private Action<UpgradeData> onChosen;
    private bool choosing;
    private Sequence showSequence;

    private void Awake() { group = GetComponent<CanvasGroup>(); HideImmediate(); }

    public void Show(UpgradeData[] options, Action<UpgradeData> chosenCallback)
    {
        onChosen = chosenCallback;
        choosing = false;
        if (showSequence.isAlive) showSequence.Stop();   // 연출 도중 재호출 대비

        group.alpha = 0f;
        group.interactable = false;   // 등장 연출 중 실수 클릭 방지
        group.blocksRaycasts = true;  // HideImmediate가 끈 것을 복구

        showSequence = Sequence.Create(useUnscaledTime: true)
            .Chain(Tween.Alpha(group, 1f, fadeDuration));

        for (int i = 0; i < cards.Length; i++)
        {
            bool has = i < options.Length && options[i] != null;
            cards[i].gameObject.SetActive(has);
            if (!has) continue;

            UpgradeData data = options[i];
            cards[i].Bind(data, () => Choose(data));

            var body = (RectTransform)cards[i].Button.transform;   // 자식 Body
            cards[i].Rect.localScale = Vector3.one * 0.8f;
            body.anchoredPosition = new Vector2(0f, -cardRise);     // 목표는 항상 (0,0) — 현재 값에 의존하지 않음

            // Chain: 이전 트윈이 끝난 뒤, Group: 직전 트윈과 동시에
            showSequence.Chain(Tween.UIAnchoredPosition(body, Vector2.zero, cardDuration, Ease.OutBack))
                        .Group(Tween.Scale(cards[i].Rect, 1f, cardDuration, Ease.OutBack));
        }

        showSequence.OnComplete(OnShowFinished);
    }

    private void OnShowFinished()
    {
        group.interactable = true;
        // 게임패드 사용자를 위해 가운데 카드를 선택 (없으면 첫 활성 카드)
        UpgradeCardView first = cards.Length > 1 && cards[1].gameObject.activeSelf ? cards[1] : cards[0];
        if (EventSystem.current != null && first.gameObject.activeSelf)
            EventSystem.current.SetSelectedGameObject(first.Button.gameObject);
    }

    private void Choose(UpgradeData data)
    {
        if (choosing || !group.interactable) return;   // 연타·연출 중 입력 방지
        choosing = true;
        HideImmediate();
        onChosen?.Invoke(data);
    }

    private void HideImmediate()
    {
        if (showSequence.isAlive) showSequence.Stop();
        group.alpha = 0f;
        group.interactable = group.blocksRaycasts = false;
        if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);
    }
}
```

`Sequence`는 구조체라 필드 기본값에서 `isAlive`가 false이므로 첫 호출에서도 안전합니다. 에디터 작업은 없습니다. 11장에서 연결한 `cards` 배열이 그대로 쓰입니다(Card Stagger 칸은 사라지고 Card Rise 칸이 생김).

HUD의 코인 숫자가 바뀔 때 살짝 튀게 합니다. 11장 `HudView`의 파일 상단에 `using PrimeTween;`을 추가하고 `SetCoins`를 교체합니다(코인 아이콘 펀치는 11장 그대로 둠).

```csharp
// 11장 HudView.SetCoins — 메서드 교체
public void SetCoins(int coins, bool punch)
{
    coinText.SetText("{0}", coins);
    if (!punch) return;
    coinPunch = 1f;                                               // 11장 아이콘 펀치
    Tween.StopAll(onTarget: coinText.transform);                 // 연속 획득 시 누적 방지
    coinText.transform.localScale = Vector3.one;
    Tween.PunchScale(coinText.transform, strength: Vector3.one * 0.25f, duration: 0.2f);
}
```

`StopAll` 후 스케일을 1로 되돌리지 않으면, 펀치 도중 멈춘 스케일에서 다음 펀치가 시작되어 점점 커지거나 작아지는 버그가 생깁니다.

### 5단계: Cinemachine 추적과 맵 경계

1. 16장에서 `CameraRig`로 옮긴 06장 추적 스크립트(`CameraFollow2D`)를 비활성화하고, Main Camera를 루트로 꺼냅니다(Position `(0,0,-10)`, Rotation 0). 16장 `GameFeel`의 Shake Target은 비워 둡니다(6단계에서 대체).
2. Hierarchy 우클릭 → Cinemachine → **Cinemachine Camera** → 이름 `CM_Follow`. Main Camera에 `CinemachineBrain`이 자동 추가됩니다.
3. `CM_Follow` Inspector: Tracking Target에 Player를 드래그. Lens의 Orthographic Size는 기존 카메라 값(예: 6)으로.
4. 같은 Inspector의 Procedural Components에서 **Position Control → Position Composer**를 선택합니다. Camera Distance 10, Damping `(0.5, 0.5, 0)`, Dead Zone 너비·높이 0.1 정도, Lookahead Time 0.2(이동 방향 앞을 조금 더 보여줌)로 시작합니다.
5. 맵 경계: 빈 오브젝트 `CameraBounds`에 **PolygonCollider2D**를 추가하고 Edit Collider로 맵 외곽에 꼭짓점을 맞춥니다. **Is Trigger**를 켜고, 레이어를 새로 만든 `CameraBounds`로 지정한 뒤 Project Settings → Physics 2D → Layer Collision Matrix에서 이 레이어의 체크를 모두 해제합니다(플레이어와 충돌·트리거하지 않게).
6. `CM_Follow`에서 Add Extension → **Cinemachine Confiner 2D**를 추가하고 Bounding Shape 2D에 `CameraBounds`를 드래그합니다.

플레이어가 런타임에 생성된다면(09장 부트스트랩) 대상을 코드로 지정합니다.

```csharp
// Assets/_CoinRush/Scripts/Camera/CameraTargetBinder.cs  (CM_Follow에 부착)
using Unity.Cinemachine;
using UnityEngine;

[RequireComponent(typeof(CinemachineCamera))]
public class CameraTargetBinder : MonoBehaviour
{
    [SerializeField] CinemachineConfiner2D confiner;

    CinemachineCamera cam;

    void Awake() => cam = GetComponent<CinemachineCamera>();

    public void Bind(Transform player)
    {
        cam.Target.TrackingTarget = player;
        cam.PreviousStateIsValid = false;   // 이전 위치에서 끌려오지 않고 즉시 스냅
    }

    // 스테이지를 바꿔 경계 모양이 달라졌을 때
    public void SetBounds(Collider2D bounds)
    {
        confiner.BoundingShape2D = bounds;
        confiner.InvalidateBoundingShapeCache(); // 모양이 바뀌었으므로 다시 계산
    }

    // 줌 연출 등으로 Orthographic Size를 바꾼 뒤
    public void SetOrthoSize(float size)
    {
        cam.Lens.OrthographicSize = size;
        confiner.InvalidateLensCache();
    }
}
```

Confiner2D는 경계 모양과 화면 크기로 계산한 결과를 캐시합니다. Cinemachine 3.1 API 문서 기준으로 구분하면 이렇습니다.

| 바뀐 것 | 할 일 |
|---|---|
| 경계 오브젝트를 평행이동하거나 균일하게 확대·축소 | 없음(캐시가 그대로 유효) |
| 폴리곤 꼭짓점 추가·삭제·이동, 비균일 스케일, 회전, 다른 경계로 교체 | `InvalidateBoundingShapeCache()` |
| 카메라 렌즈의 Orthographic Size(또는 FOV) 변경 | `InvalidateLensCache()` |

### 6단계: Impulse로 흔들림 대체 (16장 대안)

1. `CM_Follow`에 Add Extension → **Cinemachine Impulse Listener**. Use 2D Distance 켬, Gain 1.
2. 씬의 `GameFeel` 오브젝트에 **CinemachineImpulseSource** 컴포넌트 두 개를 추가합니다.
   - 첫째(작은 타격): Impulse Shape `Bump`, Duration 0.2, Default Velocity `(0.15, 0.15, 0)`.
   - 둘째(폭발·플레이어 피격): Impulse Shape `Explosion`, Duration 0.4, Default Velocity `(0.4, 0.4, 0)`.

16장의 `GameFeel.AddTrauma(amount)` 호출부를 모두 고치지 않고, `GameFeel` 내부에서 Impulse로 보내도록 바꿉니다. 호출하는 쪽 코드는 그대로입니다.

```csharp
// 16장 GameFeel — 필드 추가 (파일 상단에 using Unity.Cinemachine; 추가)
[Header("Cinemachine (17장)")]
[SerializeField] bool useCinemachineImpulse = true;
[SerializeField] CinemachineImpulseSource smallImpulse;
[SerializeField] CinemachineImpulseSource bigImpulse;

// 16장 GameFeel.AddTrauma — 메서드 교체
public static void AddTrauma(float amount)
{
    if (instance == null) return;
    if (instance.useCinemachineImpulse)
    {
        float force = amount * instance.shakeMultiplier;   // 접근성 설정 반영
        if (force <= 0f) return;
        var source = amount >= 0.3f ? instance.bigImpulse : instance.smallImpulse;
        source.GenerateImpulseWithForce(force / 0.3f);     // 0.3을 기준 세기 1로
        return;
    }
    instance.trauma = Mathf.Clamp01(instance.trauma + amount);
}
```

컴포넌트를 추가하는 것만으로는 직렬화 필드가 채워지지 않습니다. 코드를 저장한 뒤 `GameFeel` Inspector에서 연결합니다.

1. `GameFeel` 오브젝트를 선택하면 Impulse Source 컴포넌트 두 개가 위에서부터 순서대로 보입니다. **Small Impulse** 칸에 첫째(Bump) 컴포넌트의 제목 줄을, **Big Impulse** 칸에 둘째(Explosion) 컴포넌트의 제목 줄을 드래그합니다. (같은 오브젝트에 같은 타입이 둘이면 오브젝트를 드래그할 때 첫째만 들어가므로, 컴포넌트 제목 줄을 끌어다 놓아야 합니다.)
2. **Use Cinemachine Impulse**를 켭니다. 두 칸 중 하나라도 비어 있으면 첫 흔들림에서 `NullReferenceException`이 나므로, Play 전에 두 칸이 모두 채워졌는지 확인하세요. Impulse를 쓰지 않을 때는 이 체크를 끄면 16장 트라우마 방식으로 돌아갑니다.

Impulse는 여러 번 발생하면 신호가 **더해집니다**. 16장 트라우마처럼 1에서 잘리지 않으므로, 적 수십 마리가 동시에 죽는 장면에서 과해지지 않는지 확인하고 사망 흔들림은 작은 값으로 둡니다. 히트 스톱·슬로모션은 계속 16장 `GameFeel`이 담당합니다.

일시정지(`timeScale = 0`) 중에는 Impulse도 게임 시간 기준이면 멈춥니다. 설정 화면의 미리보기 흔들림이 필요하면 `CinemachineImpulseManager.Instance.IgnoreTimeScale = true`로 바꿀 수 있습니다(Cinemachine 3.1 API에 있는 필드).

### 7단계: 보스 등장 Timeline

목표 연출(총 3초): 경고음 → 카메라가 보스 위치로 이동 → 보스가 걸어 들어옴 → 이름 배너 → 카메라가 플레이어로 복귀 → 게임 재개.

**준비**

1. 보스는 이 장에서는 **연출용 최소 보스**로 충분합니다. 적 프리팹을 복제해 이름 `Boss_Golem`, Scale 2배, 색을 바꾸고 씬에 놓습니다(맵 가장자리 밖). 보스 AI·체력바는 22장에서 붙이므로, 지금은 `Enemy` 컴포넌트를 **꺼 둡니다**(Init을 받지 않은 `Enemy`는 추적하지 않음). 보스의 Animator Update Mode를 **Unscaled Time**으로 두고(게임이 멈춘 동안 컷신이 재생되므로), 오브젝트는 **비활성화**합니다.
2. Project 창 우클릭 → Create → 03장 `VoidEventChannel` 에셋 → 이름 `BossSpawnRequested`.
3. `CM_Boss`: Cinemachine Camera 하나 더 생성, Tracking Target `Boss_Golem`, Position Composer 추가, Orthographic Size 4(살짝 줌 인). **비활성화**해 둡니다.
4. Main Camera의 `CinemachineBrain`에서 **Ignore Time Scale**을 켭니다(블렌드가 timeScale 0에서도 진행).
5. Canvas에 `BossBanner`(보스 이름 텍스트) 오브젝트를 만들고 비활성화합니다.

**Timeline 만들기**

1. 빈 오브젝트 `BossIntro` 선택 → Window → Sequencing → Timeline → **Create** → `BossIntro.playable` 저장. `PlayableDirector`가 추가됩니다. Play On Awake는 **끕니다**.
2. Timeline 창에서 `+` → **Cinemachine Track**(Cinemachine 패키지가 설치돼 있어야 보임), 트랙 바인딩에 Main Camera(CinemachineBrain) 드래그. 트랙 위 우클릭 → Add Cinemachine Shot 3개: 0~0.5초 `CM_Follow`, 0.5~2.3초 `CM_Boss`, 2.3~3초 `CM_Follow`. 클립을 겹치면 겹친 구간이 블렌드 시간이 됩니다(0.4초 정도 겹치기).
3. `+` → **Animation Track**, 바인딩 `Boss_Golem`. 녹화 버튼(빨간 원)을 누르고 0.6초에 보스 위치를 맵 밖, 1.8초에 맵 안으로 옮겨 키프레임을 만듭니다. 녹화 종료.
4. `+` → **Activation Track**, 바인딩 `BossBanner`. 클립을 1.6~2.4초에 배치.
5. `+` → **Audio Track**, 경고음 클립을 0초에 드래그. 오디오 소스 바인딩은 12장 믹서의 SFX 그룹으로 출력되는 AudioSource로.
6. `+` → **Signal Track**, 바인딩 `BossIntro`. Project 창 우클릭 → Create → Timeline → Signal → `BossIntroEnd.signal`. 3.0초 위치 우클릭 → Add Signal Emitter → Emit Signal에 `BossIntroEnd`. Emitter Inspector의 **Add Signal Receiver** 버튼으로 `BossIntro`에 SignalReceiver를 추가하고, Reaction으로 아래 스크립트의 `OnIntroFinished`를 연결합니다.

**일시정지 요청을 소유자별로 바꾸기**

16장 `GameFeel.SetPaused(bool)`은 bool 하나라서 "마지막에 쓴 쪽이 이긴다"는 문제가 다시 생깁니다. 레벨업 패널이 열린 채로 컷신이 끝나며 `SetPaused(false)`를 부르면 레벨업 정지까지 풀립니다. 그래서 **누가 멈췄는지**를 기록하고, 각자 자기 요청만 해제하게 합니다. 16장 파일에서 필드 하나와 메서드 두 개를 교체하고 메서드 두 개를 추가합니다. 기존 `SetPaused(bool)` 호출부(11장 `LevelUpState`)는 그대로 컴파일되고 "레벨업 전용 소유자"로 동작합니다.

```csharp
// 16장 GameFeel — 파일 상단에 using System.Collections.Generic; 추가

// 필드 교체: bool paused;  →
readonly HashSet<object> pauseOwners = new HashSet<object>();
static readonly object LegacyPauseOwner = new object();   // SetPaused(bool) 호출자용

// 메서드 추가
public static void RequestPause(object owner)
{
    if (instance == null) { Time.timeScale = 0f; return; }
    instance.pauseOwners.Add(owner);          // 같은 소유자가 두 번 요청해도 한 번으로 셈
    instance.ApplyTimeScale();
}

public static void ReleasePause(object owner)
{
    if (instance == null) { Time.timeScale = 1f; return; }
    instance.pauseOwners.Remove(owner);       // 자기 요청만 제거
    instance.ApplyTimeScale();
}

// SetPaused 교체 — 기존 호출부 호환
public static void SetPaused(bool value)
{
    if (value) RequestPause(LegacyPauseOwner);
    else ReleasePause(LegacyPauseOwner);
}

// ApplyTimeScale 교체 — paused 대신 소유자 수로 판단
void ApplyTimeScale()
{
    // 우선순위: 일시정지 > 히트 스톱 > 슬로모션
    bool paused = pauseOwners.Count > 0;
    float desired = (paused || Time.unscaledTime < hitStopEnd) ? 0f : slowScale;
    if (Mathf.Approximately(Time.timeScale, desired)) return;
    Time.timeScale = desired;
    if (desired > 0f) Time.fixedDeltaTime = baseFixedDeltaTime * desired;
}
```

**컷신 스크립트**

컷신은 자기 자신(`this`)을 소유자로 요청하고, 정상 종료(Signal 또는 Director 정지)·중단·비활성화 어느 경로로 끝나도 `Finish` 한 곳에서 자기 요청만 해제합니다.

```csharp
// Assets/_CoinRush/Scripts/Camera/BossIntroCutscene.cs  (BossIntro에 부착)
using UnityEngine;
using UnityEngine.Playables;

[RequireComponent(typeof(PlayableDirector))]
public class BossIntroCutscene : MonoBehaviour
{
    [SerializeField] GameObject boss;
    [SerializeField] MonoBehaviour[] enableAfterIntro;   // 보스 AI, 보스 체력바 등 (지금은 비워도 됨)
    [SerializeField] VoidEventChannel bossSpawnRequested; // 03장 이벤트 채널 — 지금은 BossTimer, 22장부터 웨이브 이벤트가 Raise

    PlayableDirector director;
    bool playing;

    void Awake()
    {
        director = GetComponent<PlayableDirector>();
        director.playOnAwake = false;
        director.timeUpdateMode = DirectorUpdateMode.UnscaledGameTime; // timeScale 0에서도 진행
    }

    void OnEnable()
    {
        bossSpawnRequested.OnRaised += Play;
        director.stopped += OnDirectorStopped;   // Signal을 빠뜨려도 끝나면 해제되도록
    }

    void OnDisable()
    {
        bossSpawnRequested.OnRaised -= Play;
        director.stopped -= OnDirectorStopped;
        if (playing)
        {
            director.Stop();                      // 중단: 이 안에서 stopped가 오지 않도록 구독은 이미 해제함
            Finish();
        }
    }

    public void Play()
    {
        if (playing) return;
        playing = true;
        foreach (var b in enableAfterIntro) b.enabled = false;
        boss.SetActive(true);
        GameFeel.RequestPause(this);   // 17장: 이 컷신 몫의 정지 요청
        director.Play();
    }

    // SignalReceiver의 Reaction에서 호출
    public void OnIntroFinished() => Finish();

    void OnDirectorStopped(PlayableDirector d) => Finish();

    void Finish()
    {
        if (!playing) return;          // Signal과 stopped가 둘 다 와도 한 번만
        playing = false;
        foreach (var b in enableAfterIntro) b.enabled = true;
        GameFeel.ReleasePause(this);   // 레벨업 등 다른 소유자의 정지는 그대로 남음
    }

    [ContextMenu("Play Intro")] void DebugPlay() => Play();
}
```

`BossIntro` Inspector에서 **Boss**에 `Boss_Golem`, **Boss Spawn Requested**에 `BossSpawnRequested` 에셋을 연결합니다. `PlayableDirector`의 Wrap Mode는 **None**으로 둡니다(Hold면 끝나도 정지하지 않아 `stopped`가 오지 않음).

**5분 신호 보내기**

이 장의 목표인 "5분에 보스 등장"을 위해 최소 발행기를 만듭니다. 22장에서 웨이브 데이터의 보스 이벤트가 같은 채널을 Raise하게 되면 이 컴포넌트는 지웁니다.

```csharp
// Assets/_CoinRush/Scripts/Camera/BossTimer.cs  (22장 웨이브 이벤트로 대체될 임시 발행기)
using UnityEngine;

public class BossTimer : MonoBehaviour
{
    [SerializeField] VoidEventChannel bossSpawnRequested;
    [SerializeField] float triggerTime = 300f;   // 5분. 테스트할 때는 10으로

    float elapsed;
    bool fired;

    void Update()
    {
        if (fired) return;
        elapsed += Time.deltaTime;               // 레벨업·컷신 정지 중에는 흐르지 않음
        if (elapsed < triggerTime) return;
        fired = true;
        bossSpawnRequested.Raise();
    }
}
```

1. 씬에 빈 오브젝트 `BossTimer`를 만들고 컴포넌트를 붙인 뒤 **Boss Spawn Requested**에 같은 에셋을 연결합니다.
2. 04장 `GameStateMachine`의 **Gameplay Behaviours** 배열에 `BossTimer`를 추가합니다. 그래야 타이틀·결과 화면에서는 시간이 흐르지 않습니다.

**타임라인이 끝난 뒤 카메라**: Cinemachine Track의 마지막 샷이 끝나면 Brain은 다시 우선순위 규칙으로 돌아갑니다. `CM_Boss`가 비활성이므로 `CM_Follow`가 이어받습니다. 반대로 `CM_Boss`를 활성 상태로 두면 컷신 뒤에도 보스를 비추니 주의합니다.

테스트할 때는 `BossTimer`의 Trigger Time을 10으로 줄이거나, Play 중 `BossIntroCutscene` 컴포넌트 메뉴(⋮)의 **Play Intro**로 바로 재생합니다(`ContextMenu`는 20장에서 자세히). 레벨업 패널이 열린 상태에서 Play Intro를 눌러 보세요. 컷신이 끝나도 패널을 고르기 전까지 게임이 멈춰 있어야 합니다.

### 확인하기

| 확인 항목 | 성공 기준 |
|---|---|
| 방향 애니메이션 | WASD/스틱 방향에 맞는 걷기 클립, 손을 떼면 마지막 방향을 보고 서 있음 |
| 반응 속도 | 입력 즉시(같은 프레임 수준) 걷기↔대기 전환, 반 박자 지연 없음 |
| 피격 | 맞으면 Hurt 포즈가 한 번 재생되고 Idle로 복귀, Hurt 첫 프레임에 멈추지 않음 |
| 발소리 | 걸을 때만 일정 간격, 콘솔에 "no receiver" 에러 없음 |
| 레벨업 카드 | 게임이 멈춘 상태에서 카드가 순서대로 튀어 오르고, 연출이 끝난 뒤에만 클릭 가능 |
| 카메라 | 플레이어를 부드럽게 따라가고, 맵 끝으로 가도 맵 바깥이 보이지 않음 |
| 흔들림 | 피격·사망 시 흔들림, 설정의 흔들림 0%면 흔들리지 않음 |
| 보스 | 5분(테스트 시 10초)에 게임이 멈추고 카메라가 보스로 갔다가 돌아오며, 끝나면 이동·스폰 재개. 레벨업 패널이 열린 채 컷신이 끝나도 패널 정지는 유지 |

## 흔한 실수

1. **애니메이션이 반 박자 늦게 바뀐다** → 전이에 Has Exit Time이 켜져 있음. → 입력 반응 전이는 Has Exit Time 끔, Transition Duration 0.
2. **피격 애니메이션 첫 프레임에서 멈춘다** → Any State 전이의 Can Transition To Self가 켜져 있고 조건이 계속 참(Bool 사용). → Trigger로 바꾸고 Can Transition To Self 끔.
3. **Cinemachine 예제 코드가 컴파일되지 않는다** → 2.x 자료(`using Cinemachine;`, `CinemachineVirtualCamera`)를 3.x에 적용. → 위 이름 대응표로 바꾸기.
4. **레벨업 패널 트윈이 멈춰 있다** → `timeScale = 0`인데 트윈이 게임 시간 기준. → `useUnscaledTime: true`(DOTween은 `SetUpdate(true)`), 컷신 Director는 `UnscaledGameTime`, Brain은 Ignore Time Scale.
5. **Confiner2D를 넣었더니 플레이어가 맵에 갇히거나 튕긴다** → 경계 PolygonCollider2D가 물리 충돌에 참여. → Is Trigger + 충돌하지 않는 레이어.
6. **Timeline이 끝나도 카메라가 보스를 비춘다** → `CM_Boss`가 활성 상태로 남아 우선순위를 차지. → 평소엔 비활성, Timeline의 Cinemachine Track으로만 사용.

## 연습 문제

**1. ★☆☆ 3방향 + flipX**
오른쪽 그림이 없고 왼쪽 그림만 있을 때, 블렌드 트리에는 Down/Up/Left만 두고 오른쪽 이동은 `SpriteRenderer.flipX`로 처리하도록 `PlayerAnimator`를 고치세요.

<details><summary>힌트·해설</summary>

오른쪽 방향이면 `MoveX`에 -1(왼쪽 클립 선택)을 넣고 `spriteRenderer.flipX = true`로 둡니다. 위·아래 방향으로 바뀔 때는 `flipX = false`로 되돌리세요. 블렌드 트리의 Right 모션은 삭제합니다. `flipX`는 콜라이더에 영향을 주지 않으므로 판정이 달라지지 않습니다.

</details>

**2. ★★☆ 카드 연출 재진입 안전하게 만들기**
본문 `LevelUpPanel`은 `Body`의 원래 위치가 `(0, 0)`이라고 가정합니다. 가운데 카드만 `Body`를 20만큼 위에 두는 디자인으로 바꿔도, 레벨업이 연속 두 번 일어나 `Show`가 연출 도중 다시 호출될 때 카드 위치가 틀어지지 않게 하세요.

<details><summary>힌트·해설</summary>

`Awake`에서 `Vector2[] homePositions`에 각 카드 `Body`의 `anchoredPosition`을 저장하고, `Show`에서 시작 위치를 `homePositions[i] - new Vector2(0, cardRise)`, 목표를 `homePositions[i]`로 씁니다. 본문처럼 시작 시 `showSequence`를 `Stop()`하는 것도 유지합니다. `Show` 안에서 `body.anchoredPosition`을 읽어 목표로 삼으면, 연출 도중 재호출됐을 때 중간 위치가 새 목표로 저장됩니다. 핵심은 "현재 값"이 아니라 "저장된 기준값"을 목표로 삼는 것입니다.

</details>

**3. ★★☆ 보스 사망 줌 펀치**
보스가 죽으면 0.8초 동안 슬로모션(16장) + 카메라가 보스에게 살짝 줌 인했다가 복귀하도록, Timeline 없이 Cinemachine 카메라 전환만으로 구현하세요.

<details><summary>힌트·해설</summary>

`CM_BossDeath`(Orthographic Size 4, Tracking Target 보스)를 비활성으로 두고, 사망 시 `SetActive(true)` → unscaled로 0.8초 대기 → `SetActive(false)`. 활성화된 카메라가 같은 우선순위에서 가장 최근이므로 Brain이 블렌드해 전환합니다. Brain의 Default Blend 시간을 0.3초 정도로, Ignore Time Scale을 켜 두세요. 대기는 `await Awaitable.NextFrameAsync()`를 반복하며 `Time.unscaledTime`을 비교합니다.

</details>

**4. ★★★ 적 애니메이션 대량 최적화**
적 500마리 각각에 Animator를 붙이면 18장 프로파일러에서 `Animator.Update` 비용이 크게 보입니다. (1) Animator의 Culling Mode를 바꿨을 때, (2) Animator 없이 스프라이트 배열을 매니저 한 곳에서 시간 기반으로 교체하는 `SimpleSpriteAnimator`로 바꿨을 때의 프레임 시간을 비교하는 실험을 설계하고 구현하세요.

<details><summary>힌트·해설</summary>

(1) `Animator.cullingMode = AnimatorCullingMode.CullCompletely`는 화면 밖 렌더러의 애니메이션 갱신을 멈춥니다. (2) 적마다 `Update`를 쓰지 않고, `EnemyAnimationSystem`이 활성 적 리스트를 돌며 `frame = (int)((Time.time + offset) * fps) % sprites.Length`로 `sprite`만 교체합니다. 걷기 루프만 있는 적에게는 Animator가 과합니다. 측정은 같은 시드·같은 적 수로 60초씩, 18장의 Profile Analyzer로 평균·최댓값을 비교하세요.

</details>

## 셀프 체크

**1. Has Exit Time이 켜진 전이와 꺼진 전이는 각각 언제 쓰나요?**

<details><summary>모범 답안</summary>

켜진 전이는 현재 클립이 지정한 정규화 시간(Exit Time)까지 재생된 뒤에 넘어갑니다. 공격·피격처럼 모션이 끝까지 재생돼야 하거나 조건 없이 "끝나면 복귀"할 때 씁니다. 꺼진 전이는 조건이 만족되는 즉시 넘어가므로 이동 입력처럼 즉시 반응해야 하는 전이에 씁니다.

</details>

**2. 4방향 이동에 상태 8개와 전이 대신 블렌드 트리를 쓰는 이유는?**

<details><summary>모범 답안</summary>

방향마다 상태를 만들면 서로 간 전이가 폭발적으로 늘어 관리가 어렵습니다. 2D 블렌드 트리는 방향 파라미터(MoveX, MoveY) 값으로 클립을 고르는 하나의 상태라 Idle/Walk 두 상태와 전이 두 개로 끝납니다. 방향이 바뀌어도 상태 전이가 일어나지 않아 전이 설정 실수도 줄어듭니다.

</details>

**3. Cinemachine에서 "실제 카메라"와 `CinemachineCamera`의 관계를 설명해보세요.**

<details><summary>모범 답안</summary>

렌더링하는 실제 `Camera`는 하나이고 `CinemachineBrain`이 붙어 있습니다. `CinemachineCamera`는 "카메라가 어떻게 움직여야 하는지"를 담은 가상 카메라로, 여러 개가 있어도 렌더링하지 않습니다. Brain은 활성화된 것 중 우선순위가 가장 높고(같으면 가장 최근 활성화된) 카메라의 결과를 실제 카메라에 적용하고, 바뀔 때 블렌드합니다.

</details>

**4. 레벨업 패널 트윈, 보스 컷신, Cinemachine 블렌드가 `timeScale = 0`에서도 동작하게 하려면 각각 무엇을 설정하나요?**

<details><summary>모범 답안</summary>

트윈은 PrimeTween `useUnscaledTime: true`(DOTween은 `SetUpdate(true)`), 컷신은 `PlayableDirector.timeUpdateMode = DirectorUpdateMode.UnscaledGameTime`, 컷신에 나오는 캐릭터 Animator는 Update Mode `Unscaled Time`, 카메라 블렌드는 `CinemachineBrain`의 Ignore Time Scale을 켭니다.

</details>

**5. Timeline의 Signal Track을 쓰면 코루틴 대기 시간으로 연출을 짜는 것보다 무엇이 좋은가요?**

<details><summary>모범 답안</summary>

연출 타이밍이 코드의 숫자가 아니라 Timeline 에셋에 있으므로, 카메라·애니메이션·소리 길이를 바꿔도 코드를 고칠 필요가 없습니다. 코드는 "끝났다" 같은 의미 있는 신호만 받습니다. 연출 담당자가 에디터에서 시간을 옮기면 신호도 함께 움직여 동기화가 깨지지 않습니다.

</details>

## 핵심 요약

- Animator Controller는 그래프 에셋 상태 머신입니다. 입력 반응 전이는 **Has Exit Time 끔 + Duration 0**(2D 스프라이트), Any State 전이는 Trigger + Can Transition To Self 끔.
- 방향 이동은 2D Simple Directional 블렌드 트리 하나로, 파라미터는 `Animator.StringToHash`로 캐시하고, 움직일 때만 방향을 갱신해 멈춘 방향을 유지합니다.
- Animation Event는 Animator와 같은 오브젝트의 메서드를 이름으로 부르며, 블렌드 중복 호출에 대비합니다.
- 트윈은 PrimeTween(할당 0 지향)이나 DOTween으로 처리하고, 일시정지 중 UI는 반드시 unscaled 옵션을 줍니다.
- Cinemachine 3.x는 `Unity.Cinemachine` 네임스페이스의 `CinemachineCamera` + `CinemachinePositionComposer` + `CinemachineConfiner2D` + `CinemachineImpulseListener`로 2D 카메라를 구성합니다. 2.x 자료의 이름을 그대로 쓰지 마세요.
- Timeline은 Cinemachine·Animation·Activation·Audio·Signal 트랙으로 컷신을 데이터로 만들고, 게임 코드는 Signal로만 연결합니다.

## 더 읽을거리

- Unity 매뉴얼 — Animator Controller / Animation transitions: https://docs.unity3d.com/Manual/class-AnimatorController.html
- Unity 매뉴얼 — Blend Trees: https://docs.unity3d.com/Manual/class-BlendTree.html
- Cinemachine 3 패키지 문서 (com.unity.cinemachine, 업그레이드 가이드 "Upgrading from Cinemachine 2" 포함) — Unity 패키지 문서 사이트에서 "Cinemachine 3" 검색
- Timeline 패키지 문서 (com.unity.timeline) — Unity 패키지 문서 사이트에서 검색
- PrimeTween GitHub 저장소(KyryloKuzyk/PrimeTween)의 README, DOTween 공식 문서(dotween.demigiant.com)
