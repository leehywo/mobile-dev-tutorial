# 16. 파티클과 게임 필(Juice) — 입력에 과장된 반응을

> **이 장에서 배울 것**
> - 게임 필(Juice)을 "입력·사건에 대한 과장된 피드백"으로 정의하고, 효과마다 어떤 정보를 전달하는지 설명할 수 있다
> - Particle System의 핵심 모듈(Main, Emission Burst, Shape, Color/Size over Lifetime, Renderer, Stop Action, Sub Emitters)로 타격·사망 이펙트를 만든다
> - 파티클을 `ObjectPool<T>`로 풀링하고 Stop Action 콜백으로 자동 반납한다
> - 트라우마 방식 화면 흔들림, 중첩 가능한 히트 스톱, 피격 번쩍임, 넉백, 스쿼시&스트레치, 데미지 숫자, 코인 흡수, 슬로모션을 구현한다
> - 접근성 옵션(흔들림·번쩍임 끄기)을 넣고, 과한 연출이 가독성을 해치는 경우를 판단할 수 있다
>
> **선수 장**: 07, 12, 14 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 적을 때리면 번쩍이고 밀려나며 숫자가 튀고, 죽으면 파편이 터지며 화면이 흔들립니다. 코인이 플레이어에게 빨려오고, 레벨업 순간 시간이 느려집니다.

## 왜 필요한가

12장까지 만든 코인 러시를 친구에게 5분 동안 시켜 보세요. 아마 이런 말을 듣습니다.

- "적한테 맞았는지 모르겠어" — 체력바 숫자만 줄어들고 캐릭터에는 아무 변화가 없습니다.
- "공격이 들어가는 건가?" — 투사체가 적에 닿으면 적 체력이 줄지만, 적은 그대로 걸어옵니다.
- "코인이 먹힌 건지 사라진 건지" — `Destroy(gameObject)` 한 줄로 코인이 증발합니다.
- "밋밋해" — 기능은 다 동작하는데 재미없어 보입니다. 트레일러로 찍어도 마찬가지입니다.

규칙(게임 로직)은 같아도 **반응**이 없으면 플레이어는 자신의 행동이 세계에 영향을 줬다고 느끼지 못합니다. 이 "느낌"을 만드는 작업을 흔히 게임 필(game feel) 또는 Juice라고 부릅니다. 뱀파이어 서바이버즈류는 화면에 적이 수백 마리라 피드백이 더 중요합니다. 어떤 적이 맞았는지, 내가 위험한지를 **텍스트가 아니라 움직임과 색**으로 읽어야 하기 때문입니다.

동시에 반대 문제도 있습니다. 모든 타격마다 화면을 세게 흔들면 10분 판을 끝까지 못 합니다(멀미). 이 장은 "넣는 법"과 "줄이는 법"을 같이 다룹니다.

## 개념

### Juice의 정의 — 피드백은 과장된 반응이다

좋은 피드백은 세 가지를 만족합니다.

| 원칙 | 의미 | 코인 러시 예 |
|---|---|---|
| 즉시성 | 사건과 같은 프레임(늦어도 1~2프레임)에 시작 | 피격 프레임에 곧바로 흰색 번쩍임 |
| 비례성 | 사건의 크기만큼만 과장 | 일반 타격은 작은 흔들림, 보스 처치는 큰 흔들림 |
| 정보성 | 무엇이 일어났는지 알려줌 | 데미지 숫자 색: 흰색=일반, 노랑=치명타 |

React에 빗대면, 상태(`useState`)가 바뀌었을 때 버튼에 `:active` 스타일과 트랜지션을 거는 일입니다. 로직은 그대로이고 **보여주는 층**만 추가합니다. 그래서 이 장의 코드는 모두 기존 로직(Health, Enemy)에 **이벤트로 붙는** 형태로 만들고, 로직 코드에 연출 코드를 섞지 않습니다.

### Particle System(Shuriken) 핵심 모듈

Unity에는 파티클 시스템이 두 개 있습니다. 컴포넌트형 **Particle System**(별칭 Shuriken, CPU 시뮬레이션)과 **VFX Graph**(GPU 시뮬레이션)입니다. 코인 러시는 모바일 무료판이 있으므로 Particle System을 씁니다.

Particle System 컴포넌트는 "모듈" 묶음입니다. Inspector에서 모듈 이름 왼쪽 체크박스로 켜고 끕니다.

| 모듈 | 핵심 설정 | 타격 스파크에서 쓰는 값 |
|---|---|---|
| Main | Duration, Looping, Start Lifetime/Speed/Size/Color, Gravity Modifier, Simulation Space, **Stop Action** | Duration 0.3, Looping 끔, Lifetime 0.2~0.4(Random Between Two Constants), Speed 3~6 |
| Emission | Rate over Time, **Bursts** | Rate 0, Burst 1개: Time 0, Count 12 |
| Shape | Cone/Circle/Sphere/Edge 등, Radius, Arc | Circle, Radius 0.1 (2D 평면에서 사방으로) |
| Color over Lifetime | 수명 동안 색·알파 그래디언트 | 흰색→노랑→알파 0 |
| Size over Lifetime | 수명 동안 크기 곡선 | 1 → 0 으로 줄어드는 곡선 |
| Renderer | Material, Render Mode, **Sorting Layer / Order in Layer** | Sorting Layer를 캐릭터보다 위로 |
| Sub Emitters | Birth/Collision/Death 시 다른 파티클 시스템 발생 | 사망 이펙트: 파편이 죽을 때 작은 먼지 |

알아둘 설정 세 가지를 짚습니다.

1. **Simulation Space**: `Local`이면 파티클이 부모를 따라 움직이고, `World`면 방출 뒤 세계에 남습니다. 움직이는 적에서 터지는 파편은 `World`여야 자연스럽습니다.
2. **Stop Action**: 시스템이 끝났을 때(모든 파티클이 죽고 더 방출하지 않을 때) 할 일입니다. `None`, `Disable`, `Destroy`, `Callback`. 풀링할 때는 `Callback`을 쓰고 `OnParticleSystemStopped()` 메시지를 받아 풀에 반납합니다.
3. **Renderer의 Sorting Layer**: 2D 프로젝트에서 파티클이 스프라이트 뒤에 숨는 가장 흔한 원인입니다. Renderer 모듈에서 Sorting Layer와 Order in Layer를 지정합니다. 머티리얼은 URP의 `Universal Render Pipeline/Particles/Unlit` 셰이더를 쓰는 머티리얼이 무난합니다(2D 조명을 받게 하려면 Sprite-Lit 계열 머티리얼을 씁니다).

코드에서 모듈을 바꿀 때는 `var main = ps.main; main.stopAction = ParticleSystemStopAction.Callback;`처럼 모듈을 변수로 받아 대입합니다. 구조체지만 원본 시스템을 가리키는 핸들이라 대입이 반영됩니다.

### VFX Graph는 언제 쓰나

VFX Graph는 GPU(Compute Shader)로 수십만 개 파티클을 돌릴 수 있지만, Compute Shader를 지원하지 않는 기기에서는 동작하지 않으므로 저사양 안드로이드에서 아예 안 나올 수 있습니다. 모바일을 함께 낸다면 기본은 Particle System으로 만들고 VFX Graph는 PC 전용 추가 연출로만 두는 편이 안전합니다.

### 화면 흔들림 — 트라우마 방식

가장 단순한 흔들림은 "0.2초 동안 `Random.insideUnitCircle * 0.3f`만큼 카메라를 이동"입니다. 두 가지 문제가 있습니다. 매 프레임 완전히 무작위라 **지글거리고**, 여러 사건이 겹치면 누가 이기는지 애매합니다.

GDC 강연 "Math for Game Programmers: Juicing Your Cameras With Math"(Squirrel Eiserloh)에서 널리 퍼진 **트라우마(trauma)** 방식은 이렇습니다.

```
trauma : 0~1 사이 값. 사건이 생기면 더하고(최대 1), 시간에 따라 선형으로 줄어듦
shake  = trauma²  (또는 trauma³)
offset = maxOffset × shake × PerlinNoise(시간 × 주파수, 시드) 를 -1~1로 변환
angle  = maxAngle  × shake × PerlinNoise(시간 × 주파수, 다른 시드)
```

- **제곱하는 이유**: 작은 트라우마(0.3)는 0.09로 거의 안 흔들리고, 큰 트라우마(0.9)는 0.81로 확 흔들립니다. 작은 사건이 여러 번 쌓여야 비로소 크게 흔들리므로 "비례성"이 자동으로 생깁니다.
- **Perlin noise를 쓰는 이유**: 인접한 입력에서 비슷한 값이 나오는 매끄러운 난수라, 지글거리지 않고 "출렁"입니다. `Mathf.PerlinNoise(x, y)`는 대략 0~1을 반환하므로 `* 2 - 1`로 -1~1로 바꿉니다.
- **중첩**: 사건마다 트라우마를 더하고 1에서 자르기만 하면 됩니다.

주의할 점은 **카메라를 누가 움직이느냐**입니다. 06장에서 만든 부드러운 추적 카메라가 `transform.position`을 매 프레임 쓰고 있다면, 흔들림이 같은 값을 쓰면 서로 덮어씁니다. 해결책은 계층을 나누는 것입니다.

```
CameraRig        ← 06장의 추적 스크립트가 position을 움직임
 └ Main Camera   ← 흔들림은 localPosition / localRotation만 건드림
```

17장에서 Cinemachine으로 바꾸면 이 흔들림은 Cinemachine Impulse로 대체합니다.

### 히트 스톱 — 시간을 잠깐 멈추기

히트 스톱은 타격 순간 `Time.timeScale = 0`으로 수십 밀리초 멈췄다가 되돌리는 기법입니다. 격투 게임에서 "묵직함"을 만드는 핵심입니다.

문제는 **멈춘 동안 시간을 어떻게 재느냐**입니다. `timeScale`이 0이면 `Time.deltaTime`도 0이라 `WaitForSeconds`나 `Awaitable.WaitForSecondsAsync`처럼 게임 시간 기준 대기가 영원히 끝나지 않습니다. 멈춤 해제는 반드시 **unscaled 시간**(`Time.unscaledTime`, `Time.unscaledDeltaTime`)으로 판정합니다.

중첩도 처리해야 합니다. 한 프레임에 적 5마리를 동시에 때리면 히트 스톱 요청이 5번 옵니다. 순진하게 "0.05초 뒤 timeScale=1" 타이머를 5개 돌리면, 먼저 끝난 타이머가 다른 효과(슬로모션, 레벨업 일시정지)를 망가뜨립니다. 규칙을 이렇게 정합니다.

```
hitStopEnd = max(hitStopEnd, 지금 + 요청 길이)     ← 늘리기만 함, 누적하지 않음
매 프레임:
  desired = 1
  if (일시정지 요청)                  desired = 0     ← 04장 LevelUp 상태 등
  else if (unscaledTime < hitStopEnd) desired = 0
  else                                desired = slowMotionScale
  Time.timeScale = desired
```

핵심은 **`Time.timeScale`을 쓰는 곳을 딱 한 곳으로 모으는 것**입니다. 11장의 `LevelUpState`가 `Time.timeScale = 0`을 직접 쓰고 있다면, 이 장에서 `GameFeel.SetPaused(true)`로 바꿉니다. React로 치면 전역 상태를 여러 컴포넌트가 직접 수정하지 않고 하나의 reducer로 모으는 것과 같습니다.

`timeScale`을 0.2처럼 낮출 때는 `Time.fixedDeltaTime`도 비례해서 줄여야 물리 이동이 뚝뚝 끊겨 보이지 않습니다(기본값 0.02 × timeScale). 되돌릴 때 원래 값으로 복원합니다.

### 넉백과 속도 덮어쓰기 문제

07장에서 넉백은 `Rigidbody2D.AddForce(dir * force, ForceMode2D.Impulse)`로 구현했습니다. 그런데 05·12장의 `Enemy`는 `FixedUpdate`마다 `body.linearVelocity = dir * data.moveSpeed`를 대입하므로, 넉백 속도가 **다음 물리 프레임에 즉시 덮어써집니다**. 그래서 넉백 중에는 추적 이동을 멈추는 "경직 시간"이 필요합니다. 이 장의 `Knockback` 컴포넌트는 `IsActive`를 노출하고, `Enemy`는 그동안 속도를 쓰지 않습니다.

### 스쿼시&스트레치

애니메이션 12원칙의 첫 번째입니다. 부피를 유지하며 한 축을 늘리면 다른 축을 줄입니다(근사: `(1 + a, 1 - a)`). 루트 스케일을 바꾸면 콜라이더까지 변하므로 **시각용 자식(Visual)**만 바꿉니다.

### 접근성과 "과하면 독"

개체 번쩍임은 괜찮지만 **전체 화면 플래시**는 광과민성 위험이 있어 쓰지 않습니다. 히트 스톱은 0.03~0.06초로 짧게, 플레이어 피격·치명타 같은 드문 사건에만 겁니다.

설정 메뉴에 **화면 흔들림(0~100%)**, **번쩍임 끄기**, **데미지 숫자 끄기**를 두는 것은 이제 흔한 관행입니다. 구현 비용이 거의 없으니 처음부터 넣습니다.

## 실습: 코인 러시에 적용하기

이 장에서 만들 파일은 모두 `Assets/_CoinRush/Scripts/Feel/`에 둡니다. 01장 `Health`는 `int Current/Max`, `event Action<int,int> Changed(current, max)`, `event Action Died`, `TakeDamage(int)`를 가진다고 가정합니다. 적 프리팹은 루트(Rigidbody2D, Collider2D, Enemy, Health) 아래에 시각용 자식 `Visual`(SpriteRenderer)이 있는 구조로 바꿔 두세요.

### 1단계: GameFeel 설정과 도우미 만들기

먼저 접근성 설정을 담는 정적 클래스입니다. 10장의 세이브에 넣어도 되지만, 기기별 설정이라 여기서는 `PlayerPrefs`에 둡니다.

```csharp
// Assets/_CoinRush/Scripts/Feel/FeelSettings.cs
using UnityEngine;

public static class FeelSettings
{
    public static float ShakeIntensity   // 0~1. 0이면 흔들림 없음
    {
        get => PlayerPrefs.GetFloat("feel.shake", 1f);
        set => PlayerPrefs.SetFloat("feel.shake", Mathf.Clamp01(value));
    }
    public static bool FlashEnabled
    {
        get => PlayerPrefs.GetInt("feel.flash", 1) == 1;
        set => PlayerPrefs.SetInt("feel.flash", value ? 1 : 0);
    }
    public static bool DamageNumbersEnabled
    {
        get => PlayerPrefs.GetInt("feel.numbers", 1) == 1;
        set => PlayerPrefs.SetInt("feel.numbers", value ? 1 : 0);
    }
}
```

`PlayerPrefs.GetFloat`는 매 호출 비용이 크지 않지만, 흔들림처럼 매 프레임 읽는 곳에서는 캐시하는 편이 낫습니다. 아래 `GameFeel`은 `OnEnable`과 설정 변경 시에만 읽습니다.

다음은 시간 제어(히트 스톱, 슬로모션, 일시정지)와 화면 흔들림을 모은 `GameFeel`입니다. 씬에 하나 두고 정적 메서드로 부릅니다. (설정 화면을 닫을 때 `PlayerPrefs.Save()`를 한 번 호출하세요.)

```csharp
// Assets/_CoinRush/Scripts/Feel/GameFeel.cs
using UnityEngine;

[DefaultExecutionOrder(-50)]
public class GameFeel : MonoBehaviour
{
    static GameFeel instance;

    [Header("Shake")]
    [SerializeField] Transform shakeTarget;          // CameraRig 아래의 Main Camera
    [SerializeField] float maxOffset = 0.5f;          // 월드 단위
    [SerializeField] float maxAngle = 3f;             // 도
    [SerializeField] float frequency = 25f;
    [SerializeField] float traumaDecayPerSecond = 1.5f;

    [Header("Time")]
    [SerializeField] float slowMotionRecoverSpeed = 2f; // 초당 timeScale 회복량

    float trauma, hitStopEnd, slowHoldEnd, baseFixedDeltaTime, seed;
    float slowScale = 1f, shakeMultiplier = 1f;
    bool paused;

    public static void AddTrauma(float amount)
    {
        if (instance != null) instance.trauma = Mathf.Clamp01(instance.trauma + amount);
    }

    public static void HitStop(float duration)
    {
        if (instance == null) return;
        float end = Time.unscaledTime + duration;
        if (end > instance.hitStopEnd) instance.hitStopEnd = end; // 늘리기만, 누적 X
    }

    // scale까지 즉시 느려졌다가 hold초 유지 후 서서히 1로 복귀
    public static void SlowMotion(float scale, float hold)
    {
        if (instance == null) return;
        instance.slowScale = Mathf.Min(instance.slowScale, Mathf.Clamp(scale, 0.05f, 1f));
        instance.slowHoldEnd = Mathf.Max(instance.slowHoldEnd, Time.unscaledTime + hold);
    }

    public static void SetPaused(bool value)
    {
        if (instance == null) { Time.timeScale = value ? 0f : 1f; return; }
        instance.paused = value;
        instance.ApplyTimeScale();
    }

    public static void RefreshSettings()
    {
        if (instance != null) instance.shakeMultiplier = FeelSettings.ShakeIntensity;
    }

    void Awake()
    {
        instance = this;
        baseFixedDeltaTime = Time.fixedDeltaTime;
        seed = Random.value * 100f;
    }

    void OnEnable() => RefreshSettings();

    void OnDestroy()
    {
        if (instance != this) return;
        instance = null;
        Time.timeScale = 1f;
        Time.fixedDeltaTime = baseFixedDeltaTime;
    }

    void Update()
    {
        // 슬로모션 복귀: unscaled 시간 기준
        if (Time.unscaledTime >= slowHoldEnd && slowScale < 1f)
            slowScale = Mathf.MoveTowards(slowScale, 1f, slowMotionRecoverSpeed * Time.unscaledDeltaTime);
        ApplyTimeScale();
    }

    void LateUpdate()
    {
        if (shakeTarget == null) return;
        // 흔들림은 일시정지 중에도 감쇠해야 하므로 unscaled
        trauma = Mathf.Max(0f, trauma - traumaDecayPerSecond * Time.unscaledDeltaTime);
        float shake = trauma * trauma * shakeMultiplier;
        float t = Time.unscaledTime * frequency;
        float ox = maxOffset * shake * (Mathf.PerlinNoise(seed, t) * 2f - 1f);
        float oy = maxOffset * shake * (Mathf.PerlinNoise(seed + 1f, t) * 2f - 1f);
        float angle = maxAngle * shake * (Mathf.PerlinNoise(seed + 2f, t) * 2f - 1f);
        shakeTarget.localPosition = new Vector3(ox, oy, 0f);
        shakeTarget.localRotation = Quaternion.Euler(0f, 0f, angle);
    }

    void ApplyTimeScale()
    {
        // 우선순위: 일시정지 > 히트 스톱 > 슬로모션
        float desired = (paused || Time.unscaledTime < hitStopEnd) ? 0f : slowScale;
        if (Mathf.Approximately(Time.timeScale, desired)) return;
        Time.timeScale = desired;
        // 0일 때는 물리가 돌지 않으므로 fixedDeltaTime은 건드리지 않음
        if (desired > 0f) Time.fixedDeltaTime = baseFixedDeltaTime * desired;
    }
}
```

`async Awaitable`로 "멈추고 → 기다리고 → 되돌리기"를 요청마다 실행하면 중첩 규칙을 지키기 어렵고, 씬 전환 중 취소되면 `timeScale`이 0으로 남습니다. 요청 상태만 저장하고 한 곳에서 매 프레임 결과를 계산하는 편이 안전합니다(React의 "상태에서 UI를 계산한다"와 같은 사고방식).

11장의 `LevelUpState`(04장 상태 머신, 일시정지 상태도 마찬가지)에서 `Time.timeScale`을 직접 쓰던 곳을 바꿉니다.

```csharp
// 11장 LevelUpState — Enter/Exit 안의 timeScale 대입 한 줄씩만 교체
// Enter(): Time.timeScale = 0f;  →  GameFeel.SetPaused(true);
// Exit():  Time.timeScale = 1f;  →  GameFeel.SetPaused(false);
```

에디터 작업:

1. Hierarchy에서 Main Camera를 선택하고 06장 추적 스크립트가 붙어 있다면, 빈 오브젝트 `CameraRig`를 만들어 추적 스크립트를 옮기고 Main Camera를 그 자식으로 넣습니다. Main Camera의 Local Position은 `(0, 0, -10)`이 아니라 CameraRig의 Z를 -10으로, 카메라는 `(0, 0, 0)`으로 둡니다(흔들림이 localPosition을 0 기준으로 쓰기 때문입니다).
2. 빈 오브젝트 `GameFeel`을 만들고 `GameFeel` 컴포넌트를 붙인 뒤, Shake Target에 Main Camera를 드래그합니다.

### 2단계: 파티클 이펙트 만들고 풀링하기

타격 스파크를 에디터에서 만듭니다.

1. Hierarchy 우클릭 → Effects → Particle System → 이름 `FX_HitSpark`. Transform Rotation을 `(0, 0, 0)`으로 둡니다(기본값이 X -90인 경우가 있습니다).
2. **Main**: Duration 0.4, Looping 끔, Start Lifetime `Random Between Two Constants` 0.2~0.35, Start Speed 3~6, Start Size 0.08~0.15, Simulation Space `World`, Play On Awake 끔, **Stop Action `Callback`**.
3. **Emission**: Rate over Time 0, Bursts `+` → Time 0, Count 12, Cycles 1.
4. **Shape**: Shape `Circle`, Radius 0.05, Radius Thickness 1.
5. **Color over Lifetime** 체크: 그래디언트 왼쪽 흰색(알파 255) → 중간 노랑 → 오른쪽 알파 0.
6. **Size over Lifetime** 체크: 곡선을 1에서 0으로 내려가게 선택합니다.
7. **Renderer**: Material에 URP 파티클 머티리얼(`Universal Render Pipeline/Particles/Unlit` 셰이더, Surface Type Transparent, Blending Additive)을 지정, Sorting Layer는 캐릭터보다 위 레이어(예: `FX`)로.
8. Project 창 `Assets/_CoinRush/Prefabs/FX/`로 드래그해 프리팹을 만들고 Hierarchy 원본은 삭제합니다.

사망 이펙트 `FX_EnemyDeath`는 같은 방식으로 Count 20, Speed 2~5, Gravity Modifier 0.5(파편이 살짝 떨어짐), Start Color를 적 색으로 만듭니다. 여기에 **Sub Emitters**를 켜고 `+`로 새 자식 파티클(`Dust`, Burst 3개, 회색, Lifetime 0.3)을 추가한 뒤 조건을 `Death`로 두면, 파편이 사라질 때 작은 먼지가 피어납니다. 자식 Dust의 Stop Action은 None으로 두고, 루트만 Callback입니다.

풀에서 꺼낸 파티클이 끝나면 스스로 반납하도록 작은 컴포넌트를 붙입니다.

```csharp
// Assets/_CoinRush/Scripts/Feel/PooledParticle.cs
using UnityEngine;
using UnityEngine.Pool;

[RequireComponent(typeof(ParticleSystem))]
public class PooledParticle : MonoBehaviour
{
    public ParticleSystem Particles { get; private set; }
    public IObjectPool<PooledParticle> Pool { get; set; }

    void Awake()
    {
        Particles = GetComponent<ParticleSystem>();
        var main = Particles.main;
        main.stopAction = ParticleSystemStopAction.Callback; // 프리팹 설정을 코드로 보장
        main.playOnAwake = false;
    }

    // Stop Action이 Callback일 때 Unity가 호출하는 메시지
    void OnParticleSystemStopped()
    {
        if (Pool != null) Pool.Release(this);
        else Destroy(gameObject);
    }
}
```

```csharp
// Assets/_CoinRush/Scripts/Feel/FxPlayer.cs — 이펙트 프리팹별로 풀을 갖는 재생기
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Pool;

public class FxPlayer : MonoBehaviour
{
    static FxPlayer instance;
    readonly Dictionary<PooledParticle, ObjectPool<PooledParticle>> pools = new();

    void Awake() => instance = this;
    void OnDestroy() { if (instance == this) instance = null; }

    public static void Play(PooledParticle prefab, Vector3 position, Color? tint = null)
    {
        if (instance == null || prefab == null) return;
        var pools = instance.pools;
        var root = instance.transform;
        if (!pools.TryGetValue(prefab, out var pool))
        {
            ObjectPool<PooledParticle> created = null;
            created = new ObjectPool<PooledParticle>(
                createFunc: () => { var p = Instantiate(prefab, root); p.Pool = created; return p; },
                actionOnGet: p => p.gameObject.SetActive(true),
                actionOnRelease: p => p.gameObject.SetActive(false),
                actionOnDestroy: p => Destroy(p.gameObject),
                collectionCheck: false, defaultCapacity: 16, maxSize: 64);
            pools.Add(prefab, pool = created);
        }
        var fx = pool.Get();
        fx.transform.position = position;
        var main = fx.Particles.main;
        if (tint.HasValue) main.startColor = tint.Value;
        fx.Particles.Clear(true);
        fx.Particles.Play(true);
    }
}
```

`maxSize`를 넘어 반납된 인스턴스는 파괴되므로 메모리가 무한히 늘지 않습니다. 동시에 64개가 넘는 이펙트는 어차피 구별되지 않으니 `pool.CountActive`가 상한 이상이면 재생을 건너뛰어도 됩니다. 씬에 빈 오브젝트 `FxPlayer`를 만들고 컴포넌트를 붙입니다. (한 곳에서 색을 바꾼 인스턴스는 다음 재생에도 그 색이 남으므로, 색을 쓰는 이펙트는 항상 `tint`를 넘기세요.)

### 3단계: 피격 피드백 — 번쩍임, 스쿼시, 넉백, 파티클

번쩍임 자체는 14장 `HitFlash`가 이미 합니다(`_FlashAmount`를 `MaterialPropertyBlock`으로 설정). 같은 프로퍼티를 두 컴포넌트가 쓰면 서로 값을 덮어쓰므로, **번쩍임은 14장 `HitFlash`에 그대로 맡기고** 이 장의 `HitFeedback`은 스쿼시·파티클·흔들림·히트 스톱만 담당합니다. 대신 `HitFlash`가 접근성 설정을 따르도록 메서드 하나를 교체합니다.

```csharp
// 14장 HitFlash.OnHealthChanged — 메서드 교체 (번쩍임 끄기 옵션 반영)
private void OnHealthChanged(int current, int max)
{
    if (current < lastHp && FeelSettings.FlashEnabled) Flash();
    lastHp = current;                 // 풀에서 Initialize로 올라간 경우도 갱신만
}
```

```csharp
// Assets/_CoinRush/Scripts/Feel/HitFeedback.cs
using UnityEngine;

[RequireComponent(typeof(Health))]
public class HitFeedback : MonoBehaviour
{
    [SerializeField] Transform visual;           // 자식 Visual (스쿼시는 시각용 자식에만)
    [SerializeField] float squashAmount = 0.25f, squashDuration = 0.15f;
    [SerializeField] PooledParticle hitFx, deathFx;
    [SerializeField] Color deathTint = Color.white;
    [SerializeField] float deathTrauma = 0.15f;
    [SerializeField] bool isPlayer;

    Health health;
    int lastHp;
    float squashTimer;
    bool animating;

    void Awake() => health = GetComponent<Health>();

    void OnEnable()
    {
        lastHp = health.Current;
        health.Changed += OnChanged;
        health.Died += OnDied;
        squashTimer = 0f;
        animating = false;
        ApplySquash(0f);                         // 재사용 시 지난 생의 스케일 제거
    }

    void OnDisable()
    {
        health.Changed -= OnChanged;
        health.Died -= OnDied;
    }

    void OnChanged(int current, int max)
    {
        int damage = lastHp - current;
        lastHp = current;
        if (damage <= 0) return;   // 회복·풀 재사용 시 Initialize는 무시
        squashTimer = squashDuration;
        animating = true;
        FxPlayer.Play(hitFx, transform.position);
        if (isPlayer)
        {
            GameFeel.AddTrauma(0.35f);
            GameFeel.HitStop(0.06f);
        }
    }

    void OnDied()
    {
        FxPlayer.Play(deathFx, transform.position, deathTint);
        GameFeel.AddTrauma(deathTrauma);
    }

    void Update()
    {
        if (!animating) return;  // 적 500마리가 매 프레임 스케일을 쓰지 않도록
        // 스쿼시는 히트 스톱 중에도 보여야 하므로 unscaled
        squashTimer -= Time.unscaledDeltaTime;
        ApplySquash(Mathf.Max(0f, squashTimer) / squashDuration);   // 1→0
        if (squashTimer <= 0f) animating = false;
    }

    void ApplySquash(float squash01)
    {
        if (visual == null) return;
        // 가로로 납작 → 원래대로. 사인으로 한 번 튕기게
        float a = squashAmount * Mathf.Sin(squash01 * Mathf.PI);
        visual.localScale = new Vector3(1f + a, 1f - a, 1f);
    }
}
```

넉백은 공격한 쪽의 위치가 필요하므로 `Health` 이벤트가 아니라 투사체에서 호출합니다.

```csharp
// Assets/_CoinRush/Scripts/Feel/Knockback.cs
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public class Knockback : MonoBehaviour
{
    [SerializeField] float stunDuration = 0.12f;
    [SerializeField] float resistance = 0f;   // 0=전부 받음, 1=면역 (보스)

    Rigidbody2D rb;
    float stunEnd;

    public bool IsActive => Time.time < stunEnd;
    void Awake() => rb = GetComponent<Rigidbody2D>();
    void OnEnable() => stunEnd = 0f;

    public void Apply(Vector2 direction, float force)
    {
        float f = force * (1f - Mathf.Clamp01(resistance));
        if (f <= 0f) return;
        rb.linearVelocity = Vector2.zero;
        rb.AddForce(direction.normalized * f, ForceMode2D.Impulse);
        stunEnd = Time.time + stunDuration;
    }
}
```

이제 `Enemy`를 수정합니다. 기준은 **12장 파일에 14장 디졸브 수정(필드 `dissolve`·`bodyCollider`, `OnEnable`의 `bodyCollider.enabled = true`, `OnDied` 교체, `FixedUpdate`의 `isSpawned` 검사)까지 적용한 상태**입니다. 이 단계에서는 필드 하나, `Awake`, `FixedUpdate`만 바꿉니다.

```csharp
// Enemy.cs (12·14장) — 필드 추가
private Knockback knockback;          // 넉백을 받지 않는 적은 컴포넌트가 없어도 됨(null)

// Awake 교체
private void Awake()
{
    health = GetComponent<Health>();
    body = GetComponent<Rigidbody2D>();
    bodyCollider = GetComponent<Collider2D>();   // 14장
    knockback = GetComponent<Knockback>();       // 16장
}

// FixedUpdate 교체 — 14장의 사망 검사 + 넉백 중에는 속도를 쓰지 않음
private void FixedUpdate()
{
    if (!isSpawned || target == null) return;           // 14장: 디졸브 중에는 움직이지 않음
    if (knockback != null && knockback.IsActive) return; // 16장: 넉백 속도를 덮어쓰지 않음
    Vector2 dir = ((Vector2)target.position - body.position).normalized;
    body.linearVelocity = dir * data.moveSpeed;
}
```

12장 투사체의 충돌 처리에 넉백을 추가합니다(적 Rigidbody2D의 Linear Damping을 3~5로 두면 넉백이 짧게 멈춥니다). 필드 `[SerializeField] private float knockbackForce = 3f;`를 추가하고(무기별로 다르게 하려면 `WeaponData`로) 메서드를 교체합니다.

```csharp
// 12장 Projectile.OnTriggerEnter2D — 메서드 교체
private void OnTriggerEnter2D(Collider2D other)
{
    if (!isSpawned) return;                       // 같은 프레임 두 번째 충돌 무시
    if (!targetLayers.Contains(other.gameObject.layer)) return;
    if (other.TryGetComponent(out IDamageable target))
    {
        // 죽는 타격에도 살짝 밀려난 채로 타들어감 (추적 이동은 14장 isSpawned 검사로 멈춤)
        if (other.TryGetComponent(out Knockback kb))
            kb.Apply(other.transform.position - transform.position, knockbackForce);
        target.TakeDamage(damage);
        Despawn();
    }
}
```

에디터 작업(적 프리팹):

1. 적 프리팹을 열고 루트에 `HitFeedback`, `Knockback`을 추가합니다.
2. `HitFeedback`의 **Visual**에 자식 `Visual`을 드래그하고, **Hit Fx**에 `FX_HitSpark`, **Death Fx**에 `FX_EnemyDeath` 프리팹을 연결합니다(프리팹에 `PooledParticle`이 붙어 있어야 필드에 들어갑니다). Death Tint는 적 색, **Is Player는 끔**.
3. 14장 `HitFlash`와 `DissolveEffect`는 `Visual`(SpriteRenderer가 있는 자식)에 그대로 둡니다. 번쩍임은 `HitFlash`, 스쿼시는 `HitFeedback`이 맡으므로 두 컴포넌트가 같은 값을 쓰지 않습니다.
4. Player 프리팹 루트에도 `HitFeedback`을 추가하고 Visual에 플레이어의 시각용 자식을 연결, **Is Player를 켭니다**(피격 시 흔들림·히트 스톱). Knockback은 붙이지 않습니다.
5. `FX_HitSpark`, `FX_EnemyDeath` 프리팹 루트에 `PooledParticle` 컴포넌트가 붙어 있는지 확인합니다.

### 4단계: 데미지 숫자 팝업

12장의 `DamageNumber`를 곡선·치명타 색·동시 개수 상한·설정 연동이 있는 `DamagePopup`으로 교체합니다. 스크립트 두 개를 만든 뒤 이 단계 끝에서 `Enemy`와 12장 `GameplayPools`를 고칩니다.

1. Hierarchy 우클릭 → 3D Object → Text - TextMeshPro(월드 공간 텍스트, UI 아님) → 이름 `DamagePopup`.
2. Font Size 4, Alignment 가운데, Sorting Layer는 `FX`보다 위(MeshRenderer지만 TextMeshPro Inspector 하단 Extra Settings에서 Sorting Layer 지정 가능).
3. 아래 `DamagePopup` 스크립트를 붙이고 프리팹으로 만든 뒤 원본 삭제.

```csharp
// Assets/_CoinRush/Scripts/Feel/DamagePopup.cs
using TMPro;
using UnityEngine;
using UnityEngine.Pool;

[RequireComponent(typeof(TextMeshPro))]
public class DamagePopup : MonoBehaviour
{
    [SerializeField] float lifetime = 0.7f;
    [SerializeField] float riseHeight = 0.8f;
    [SerializeField] AnimationCurve riseCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);
    [SerializeField] AnimationCurve scaleCurve = new AnimationCurve(
        new Keyframe(0f, 0.5f), new Keyframe(0.15f, 1.3f), new Keyframe(0.3f, 1f), new Keyframe(1f, 0.8f));
    [SerializeField] Color normalColor = Color.white;
    [SerializeField] Color criticalColor = new Color(1f, 0.85f, 0.2f);

    public IObjectPool<DamagePopup> Pool { get; set; }

    TextMeshPro label;
    Vector3 startPos;
    float elapsed;
    void Awake() => label = GetComponent<TextMeshPro>();

    public void Show(Vector3 position, int amount, bool isCritical)
    {
        // 같은 위치에 겹치지 않도록 약간 흩뿌림
        startPos = position + (Vector3)(Random.insideUnitCircle * 0.2f);
        transform.position = startPos;
        elapsed = 0f;
        label.SetText("{0}", amount);  // ToString()과 달리 문자열 할당 없음(02장)
        label.color = isCritical ? criticalColor : normalColor;
        label.fontStyle = isCritical ? FontStyles.Bold : FontStyles.Normal;
    }

    void Update()
    {
        elapsed += Time.deltaTime;
        float t = elapsed / lifetime;
        if (t >= 1f) { Pool.Release(this); return; }
        transform.position = startPos + Vector3.up * (riseHeight * riseCurve.Evaluate(t));
        transform.localScale = Vector3.one * scaleCurve.Evaluate(t);
        var c = label.color;
        c.a = t < 0.7f ? 1f : 1f - (t - 0.7f) / 0.3f;
        label.color = c;
    }
}
```

```csharp
// Assets/_CoinRush/Scripts/Feel/DamagePopupSpawner.cs
using UnityEngine;
using UnityEngine.Pool;

public class DamagePopupSpawner : MonoBehaviour
{
    static DamagePopupSpawner instance;
    [SerializeField] DamagePopup prefab;
    [SerializeField] int maxActive = 40;

    ObjectPool<DamagePopup> pool;
    void Awake()
    {
        instance = this;
        pool = new ObjectPool<DamagePopup>(
            createFunc: () => { var p = Instantiate(prefab, transform); p.Pool = pool; return p; },
            actionOnGet: p => p.gameObject.SetActive(true),
            actionOnRelease: p => p.gameObject.SetActive(false),
            actionOnDestroy: p => Destroy(p.gameObject),
            collectionCheck: false, defaultCapacity: 20, maxSize: 60);
    }

    void OnDestroy() { if (instance == this) instance = null; }

    public static void Show(Vector3 position, int amount, bool isCritical)
    {
        if (instance == null || !FeelSettings.DamageNumbersEnabled) return;
        if (instance.pool.CountActive >= instance.maxActive) return; // 화면 덮음 방지
        instance.pool.Get().Show(position, amount, isCritical);
    }
}
```

연결 작업입니다.

1. Hierarchy에 빈 오브젝트 `DamagePopupSpawner`를 만들고 같은 이름의 컴포넌트를 붙인 뒤, **Prefab** 칸에 위에서 만든 `DamagePopup` 프리팹을 드래그합니다. 이 칸이 비어 있으면 첫 `Show`에서 `Instantiate`가 실패합니다. 오브젝트 자체가 씬에 없으면 `Show`는 아무 에러 없이 조용히 반환하므로, 숫자가 안 뜨면 이것부터 확인하세요.
2. `Enemy.OnHealthChanged`를 교체해 12장 `DamageNumber` 대신 새 스포너를 부릅니다.

```csharp
// Enemy.cs (12장) — OnHealthChanged 교체
private void OnHealthChanged(int current, int max)
{
    int damage = lastHp - current;
    lastHp = current;
    if (damage <= 0 || !isSpawned) return;         // 리셋(증가)은 무시

    DamagePopupSpawner.Show(transform.position + Vector3.up * 0.5f, damage, isCritical: false);
    AudioManager.Instance.PlaySfx(hitSfx);
}
```

3. 12장 `GameplayPools`에서 데미지 숫자 풀을 제거합니다. `[SerializeField] private DamageNumber damageNumberPrefab;` 필드, `public ObjectPool<DamageNumber> DamageNumbers { get; private set; }` 프로퍼티, `Awake`의 `DamageNumbers = PoolUtil.Create(...)` 줄 세 곳을 지웁니다. 그다음 `DamageNumber.cs`와 12장 `DamageNumber` 프리팹을 삭제합니다(순서를 바꾸면 `GameplayPools`가 없는 타입을 참조해 컴파일 에러).

### 5단계: 코인 흡수(자석)

02장의 `CoinMagnet`은 Player에 붙어 물리 쿼리로 코인을 일정 속도로 끌어당겼습니다. 여기서는 가속 곡선으로 "쏙" 빨려드는 느낌을 내도록 **02장 `CoinMagnet`을 교체**합니다. 02장 `CoinMagnet.cs`를 삭제하고(같은 클래스 이름이 두 개면 컴파일 에러), Player에서 컴포넌트를 떼어 아래 컴포넌트를 코인 프리팹에 붙입니다. 04·05장 `GameStateMachine`의 Gameplay Behaviours와 `PlayerStateController`의 Disable On Death 목록에서도 `CoinMagnet` 칸을 지웁니다. 02장 `Coin.Attract`는 더 이상 호출되지 않습니다.

```csharp
// Assets/_CoinRush/Scripts/Feel/CoinMagnet.cs  (02장 Player/CoinMagnet.cs 삭제 후 새로 작성)
using UnityEngine;

public class CoinMagnet : MonoBehaviour
{
    [SerializeField] float pickupRadius = 2.5f;
    [SerializeField] float maxSpeed = 14f;
    [SerializeField] float accelerationTime = 0.35f;
    [SerializeField] AnimationCurve speedCurve = AnimationCurve.EaseInOut(0, 0.1f, 1, 1);

    Transform player;
    bool attracted;
    float attractTime;

    public void SetPlayer(Transform target) => player = target;

    void OnEnable() { attracted = false; attractTime = 0f; }

    void Update()
    {
        if (player == null) return;
        Vector3 toPlayer = player.position - transform.position;
        if (!attracted)
        {
            if (toPlayer.sqrMagnitude > pickupRadius * pickupRadius) return;
            attracted = true;
            attractTime = 0f;
        }
        attractTime += Time.deltaTime;
        float t = Mathf.Clamp01(attractTime / accelerationTime);
        float speed = maxSpeed * speedCurve.Evaluate(t);
        transform.position = Vector3.MoveTowards(transform.position, player.position, speed * Time.deltaTime);
    }
}
```

`CoinMagnet`은 플레이어를 모르면 아무것도 하지 않습니다(`player == null`이면 조기 반환). 코인 러시에서 코인을 만드는 곳은 14장에서 교체한 `Enemy.OnDied`의 `pools.Coins.Spawn(...)` 반복문이므로, 거기서 적이 이미 알고 있는 추적 대상(`target`)을 넘깁니다. 매 프레임 `FindFirstObjectByType`으로 플레이어를 찾지 마세요. 반경 판정은 `sqrMagnitude`로 제곱근을 피했습니다.

```csharp
// Enemy.cs (14장) — OnDied 교체: 드롭한 코인에 플레이어를 알려줌
private void OnDied()
{
    if (!isSpawned) return;
    isSpawned = false;

    bodyCollider.enabled = false;             // 타는 동안 플레이어·투사체와 충돌하지 않음
    body.linearVelocity = Vector2.zero;
    for (int i = 0; i < data.coinDrop; i++)
    {
        Coin coin = pools.Coins.Spawn(transform.position + (Vector3)(Random.insideUnitCircle * 0.4f));
        if (coin.TryGetComponent(out CoinMagnet magnet)) magnet.SetPlayer(target);
    }
    AudioManager.Instance.PlaySfx(deathSfx);

    dissolve.Play(() => Pool.Release(this));  // 다 탄 뒤에 풀로 반환 (22장에서 RequestRelease()로 바뀜)
}
```

`Spawn`이 `SetActive(true)`를 먼저 하므로 `CoinMagnet.OnEnable`의 리셋이 끝난 뒤 `SetPlayer`가 호출됩니다. 코인 프리팹 루트에 `CoinMagnet`을 붙였는지 확인하세요.

획득 순간 피드백은 12장 `Coin.OnTriggerEnter2D`에 추가합니다. 필드 `[SerializeField] private PooledParticle pickupFx;`를 추가하고(코인 프리팹에서 작은 반짝임 파티클 프리팹을 연결) 메서드를 교체합니다. 코인 수백 개가 동시에 들어오면 소리가 뭉개지므로, 12장 `AudioManager`의 SFX 재생에 피치를 약간 올려가며 재생하면 연속 획득감이 좋아집니다(연습 문제 2).

```csharp
// 12장 Coin.OnTriggerEnter2D — 메서드 교체
private void OnTriggerEnter2D(Collider2D other)
{
    if (!isSpawned || !other.CompareTag("Player")) return;
    isSpawned = false;
    collected.Raise(value);
    AudioManager.Instance.PlaySfx(pickupSfx);
    FxPlayer.Play(pickupFx, transform.position);   // 16장: 획득 반짝임 (비어 있으면 무시됨)
    Pool.Release(this);
}
```

### 6단계: 레벨업 슬로모션

11장 `LevelUpPanel`을 띄우기 직전에 0.4초 동안 느려졌다가 멈추게 하면 "뭔가 중요한 일이 일어났다"가 전달됩니다. 레벨업이 확정되면 11장에서 `GameStateMachine.HandleLeveledUp(int level)`이 `PlayerExperience.LeveledUp`을 받아 즉시 `ChangeState(LevelUp)`을 합니다. 이 메서드를 교체해 슬로모션을 먼저 걸고, 잠깐 기다린 뒤 전환합니다.

기다리는 동안 세 가지가 일어날 수 있습니다. ① 코인을 연달아 먹어 `LeveledUp`이 또 옴 ② 플레이어가 죽어 Result로 감 ③ 씬이 내려가 `GameStateMachine`이 파괴됨. 그래서 대기 중 플래그로 중복 요청을 막고, 재개 직후 **현재 상태가 아직 Playing인지 다시 확인**하며, 파괴는 `destroyCancellationToken`으로 끊습니다.

```csharp
// 11장 GameStateMachine — 필드 추가
private bool levelUpPending;

// 11장 GameStateMachine.HandleLeveledUp — 메서드 교체
// async void는 이벤트 핸들러에서만 씁니다. 예외는 여기서 모두 처리합니다.
private async void HandleLeveledUp(int level)
{
    if (Current != Playing || levelUpPending) return;   // ① 대기 중 중복 요청 무시
    levelUpPending = true;

    GameFeel.SlowMotion(0.2f, 0.4f);
    GameFeel.AddTrauma(0.2f);
    try
    {
        // 슬로모션(timeScale 0.2) 동안 게임 시간 0.08초 = 실제 약 0.4초
        await Awaitable.WaitForSecondsAsync(0.08f, destroyCancellationToken);
    }
    catch (System.OperationCanceledException)
    {
        return;                                          // ③ 씬 종료로 파괴됨 — 아무것도 하지 않음
    }
    finally
    {
        levelUpPending = false;
    }

    if (Current != Playing) return;                      // ② 기다리는 사이 사망 등으로 상태가 바뀜
    ChangeState(LevelUp);                                // Enter에서 GameFeel.SetPaused(true)
}
```

구독(`OnEnable`의 `playerExperience.LeveledUp += HandleLeveledUp;`)과 해제는 11장 그대로입니다. 대기 중에 들어온 두 번째 레벨업은 11장과 마찬가지로 무시됩니다(한 번에 여러 단계 레벨업은 11장 연습 문제 3의 `TryConsumeLevelUp` 방식으로 처리).

### 7단계: 설정 메뉴에 접근성 옵션 연결

11장 설정 화면에 슬라이더 하나와 토글 두 개를 추가하고, 각 `onValueChanged`에 연결합니다.

```csharp
// 11장 설정 화면 View의 OnEnable에 추가 (shakeSlider, flashToggle, numbersToggle은 [SerializeField])
shakeSlider.SetValueWithoutNotify(FeelSettings.ShakeIntensity);
shakeSlider.onValueChanged.AddListener(v =>
{
    FeelSettings.ShakeIntensity = v;
    GameFeel.RefreshSettings();
    GameFeel.AddTrauma(0.5f);                // 미리보기
});
flashToggle.SetIsOnWithoutNotify(FeelSettings.FlashEnabled);
flashToggle.onValueChanged.AddListener(v => FeelSettings.FlashEnabled = v);
numbersToggle.SetIsOnWithoutNotify(FeelSettings.DamageNumbersEnabled);
numbersToggle.onValueChanged.AddListener(v => FeelSettings.DamageNumbersEnabled = v);
```

`OnDisable`에서는 `onValueChanged.RemoveAllListeners()`로 정리하고 `PlayerPrefs.Save()`를 호출합니다. 설정 화면이 일시정지 중이어도 `GameFeel.LateUpdate`는 unscaled 시간을 쓰므로 미리보기 흔들림이 보입니다.

### 확인하기

Play를 누르고 아래 **전후 비교 체크리스트**를 채웁니다. 이 장을 시작하기 전 커밋을 체크아웃해 같은 장면을 녹화(Windows: Win+G, macOS: Cmd+Shift+5)해 두면 차이가 확실히 보입니다.

| 항목 | 전 | 후 (성공 기준) |
|---|---|---|
| 적 타격 | 체력만 줄어듦 | 적이 흰색으로 짧게 번쩍(14장 `HitFlash`), 가로로 납작해졌다 복원, 뒤로 밀림, 숫자가 튀어 오름, 스파크 |
| 적 사망 | 사라짐 | 적 색 파편이 터지고 먼지가 피어남, 약한 화면 흔들림 |
| 플레이어 피격 | 체력바만 줄어듦 | 한 박자 멈춤(히트 스톱), 화면이 흔들림 |
| 적 10마리 동시 사망 | — | 흔들림이 커지지만 1초 안에 가라앉음, 시간은 멈추지 않음 |
| 코인 | 닿아야 먹힘 | 반경 안에 들어오면 천천히 끌리다 가속해서 빨려옴 |
| 레벨업 | 즉시 패널 | 0.4초 슬로모션 후 패널, 패널 닫으면 정상 속도. 슬로모션 중 사망하면 패널 없이 결과 화면 |
| 설정 | — | 흔들림 0%면 전혀 안 흔들림, 번쩍임 끄면 흰색 없음 |
| 콘솔 | — | 에러·경고 없음, 레벨업 패널을 닫은 뒤 `Debug.Log(Time.timeScale)`이 1 |

## 흔한 실수

1. **파티클이 안 보인다** → 스프라이트보다 뒤에 그려지거나 Z 위치가 카메라 뒤. → Renderer 모듈의 Sorting Layer/Order를 올리고, 프리팹 Transform Rotation이 X -90이면 0으로(2D에서 Cone이 화면 안쪽을 향함).
2. **히트 스톱 뒤 게임이 영원히 멈춘다** → 되돌리기를 `WaitForSeconds`/`Awaitable.WaitForSecondsAsync`로 기다림(timeScale 0이라 끝나지 않음) 또는 여러 곳에서 `timeScale`을 직접 씀. → unscaled 시간으로 판정하고 `GameFeel` 한 곳에서만 쓰기.
3. **흔들림을 넣었더니 카메라가 원점으로 튄다** → 추적 스크립트와 흔들림이 같은 transform의 position을 씀. → CameraRig/Main Camera 계층 분리, 흔들림은 localPosition만.
4. **적 전체가 동시에 번쩍인다** → `visual.material.SetFloat` 대신 `sharedMaterial`을 수정했거나, 머티리얼 에셋 자체를 바꿈. → `MaterialPropertyBlock` 사용. (`.material` 접근은 개체마다 머티리얼 복제를 만들어 배칭이 깨집니다.)
5. **넉백이 안 먹힌다** → `Enemy.FixedUpdate`가 매 물리 프레임 `linearVelocity`를 덮어씀. → `Knockback.IsActive` 동안 이동 건너뛰기.
6. **풀에서 꺼낸 파티클이 두 번째부터 재생 안 됨** → Looping이 켜져 있어 Stop 콜백이 안 오거나, Stop Action이 `Disable`/`Destroy`. → Looping 끄고 Stop Action `Callback`.

## 연습 문제

**1. ★☆☆ 치명타 숫자**
`WeaponData`에 `critChance`(0~1)를 추가하고, 치명타일 때 데미지 2배, 숫자는 노란색·굵게, `GameFeel.HitStop(0.04f)`를 호출하세요.

<details><summary>힌트·해설</summary>

12장 `Projectile`은 `WeaponData`를 모르고 `Launch`로 받은 `damage`만 압니다. 그리고 숫자는 이미 `Enemy.OnHealthChanged`가 한 번 띄웁니다. 그러니 **치명타 판정은 무기를 아는 발사 코드에서**, **숫자는 `Enemy`에서 한 번만** 띄우고 그 사이에 "치명타였다"는 정보만 전달합니다.

1. `WeaponData`에 `[Range(0f, 1f)] public float critChance;` 추가.
2. 발사 코드(12장): `bool crit = Random.value < weapon.critChance;` → `shot.Launch(aimDirection, weapon.projectileSpeed, crit ? weapon.damage * 2 : weapon.damage, crit);`
3. `Projectile`: 필드 `private bool isCritical;`, `Launch`에 네 번째 매개변수 `bool critical = false`를 추가해 `isCritical = critical;` 저장(기본값이 있어 기존 호출은 그대로 컴파일됨). `OnTriggerEnter2D`에서 `target.TakeDamage(damage);` **바로 위에** `if (isCritical && other.TryGetComponent(out Enemy enemy)) enemy.MarkNextHitCritical();`
4. `Enemy`: 필드 `private bool nextHitCritical;`, 메서드 `public void MarkNextHitCritical() => nextHitCritical = true;`. `OnHealthChanged`에서 `bool crit = nextHitCritical; nextHitCritical = false;`를 `damage` 계산 직후(조기 반환보다 앞)에 두고 `DamagePopupSpawner.Show(..., damage, crit);`, 그리고 `if (crit) GameFeel.HitStop(0.04f);`. `OnEnable`에서도 `nextHitCritical = false;`로 리셋합니다(풀 재사용).

`TakeDamage` → `Health.Changed` → `OnHealthChanged`가 같은 호출 안에서 동기적으로 실행되므로 플래그가 다른 타격과 섞이지 않습니다. 치명타가 초당 수십 번 나오면 히트 스톱이 계속 걸려 게임이 느려 보입니다. `GameFeel`의 규칙이 "늘리기만, 누적하지 않음"이라 최악은 아니지만, 치명타 히트 스톱은 0.1초 쿨다운을 두는 편이 좋습니다(`static float lastCritStop`를 `Time.unscaledTime`과 비교).

</details>

**2. ★★☆ 연속 획득 피치 상승**
코인을 0.3초 이내에 연달아 먹으면 효과음 피치가 1.0 → 1.05 → 1.10 … 최대 1.5까지 오르고, 0.3초가 지나면 1.0으로 돌아가게 하세요.

<details><summary>힌트·해설</summary>

`CoinPickupSound` 같은 정적 상태를 둡니다: `lastTime`, `streak`. 획득 시 `if (Time.unscaledTime - lastTime > 0.3f) streak = 0; streak++; lastTime = Time.unscaledTime; float pitch = Mathf.Min(1f + 0.05f * (streak - 1), 1.5f);` 12장 `AudioManager`의 재생 메서드에 pitch 인자가 없다면 풀에서 꺼낸 `AudioSource.pitch`를 설정하는 오버로드를 추가합니다. `PlayOneShot`은 소스의 pitch를 따르므로, 여러 소리가 한 소스를 공유하면 피치가 서로 간섭합니다. 풀링된 개별 소스에서 `Play()`하는 방식이 안전합니다.

</details>

**3. ★★★ 잔상(Afterimage)과 대시**
플레이어에 대시(짧은 순간 이동)를 추가하고, 대시 중 0.03초마다 현재 스프라이트를 복사한 반투명 잔상을 남겨 0.25초 동안 사라지게 하세요. 잔상은 풀링하고, 번쩍임 셰이더와 충돌하지 않게 하세요. 그리고 코인 러시의 모든 연출을 켠 상태와 끈 상태로 3분씩 플레이해 "무엇이 정보이고 무엇이 소음인가" 표를 직접 작성해 보세요.

<details><summary>힌트·해설</summary>

잔상은 `SpriteRenderer` 하나를 가진 프리팹으로 만들고, 생성 시 `sprite`, `flipX`, `transform` 위치·스케일을 복사합니다. 색은 `color`의 알파로 줄이면 됩니다. 머티리얼은 번쩍임 셰이더가 아닌 기본 Sprite 머티리얼을 써야 번쩍임 값이 복사되는 혼동이 없습니다. 표는 "효과 / 전달 정보 / 3분 뒤 피로도 / 유지·축소·제거" 열로 만드세요. 대개 "적 사망 흔들림"은 축소, "데미지 숫자"는 합산(같은 적에 0.2초 내 숫자 합치기)이 결론으로 나옵니다.

</details>

## 셀프 체크

**1. 트라우마 방식에서 트라우마를 제곱해서 흔들림 세기로 쓰는 이유를 설명해보세요.**

<details><summary>모범 답안</summary>

작은 사건은 거의 흔들리지 않고 큰 사건(또는 작은 사건이 여러 번 쌓인 경우)에서만 크게 흔들리게 하기 위해서입니다. 0.3² = 0.09, 0.9² = 0.81처럼 비선형으로 커지므로 비례성이 자동으로 생기고, 트라우마가 선형으로 줄어들 때 흔들림은 끝부분에서 빠르게 잦아들어 자연스럽습니다.

</details>

**2. 히트 스톱 중에 `Awaitable.WaitForSecondsAsync`로 복귀를 기다리면 왜 문제가 되나요?**

<details><summary>모범 답안</summary>

`WaitForSecondsAsync`는 게임 시간(scaled time) 기준으로 대기합니다. `timeScale`이 0이면 게임 시간이 흐르지 않아 대기가 끝나지 않고 게임이 멈춘 채로 남습니다. 복귀 판정은 `Time.unscaledTime` 같은 실제 시간으로 해야 합니다.

</details>

**3. 여러 시스템이 `Time.timeScale`을 직접 수정하면 어떤 버그가 생기고, 이 장에서는 어떻게 막았나요?**

<details><summary>모범 답안</summary>

레벨업 일시정지 중에 히트 스톱 타이머가 끝나며 `timeScale = 1`로 되돌려 일시정지가 풀리거나, 슬로모션이 히트 스톱에 덮이는 등 마지막에 쓴 쪽이 이깁니다. 이 장은 `GameFeel`만 `timeScale`을 쓰고, 나머지는 `paused`, `hitStopEnd`, `slowScale` 같은 요청 상태만 바꾸게 한 뒤 매 프레임 우선순위(일시정지 > 히트 스톱 > 슬로모션)로 결과를 계산했습니다.

</details>

**4. 피격 번쩍임을 `renderer.material.SetFloat`가 아니라 `MaterialPropertyBlock`으로 구현한 이유는?**

<details><summary>모범 답안</summary>

`.material`에 접근하면 해당 렌더러용 머티리얼 복제본이 생성되어 메모리가 늘고 배칭이 깨집니다. `sharedMaterial`을 바꾸면 같은 머티리얼을 쓰는 모든 적이 함께 번쩍입니다. `MaterialPropertyBlock`은 머티리얼을 공유한 채 렌더러별 값만 덮어씁니다.

</details>

## 핵심 요약

- Juice는 게임 규칙을 바꾸지 않고 **상태 변화를 즉시·비례적으로·정보가 있게 과장해서** 보여주는 층입니다. 로직 코드에 섞지 말고 이벤트로 붙입니다.
- Particle System은 모듈 묶음이며, 일회성 이펙트는 Emission Burst + Looping 끔 + Stop Action `Callback` + Sorting Layer 지정이 기본 조합입니다.
- 파티클·데미지 숫자는 `ObjectPool<T>`로 풀링하고, 동시 개수 상한으로 성능과 가독성을 같이 지킵니다.
- 화면 흔들림은 trauma²×Perlin noise로 만들고, 추적 카메라와 계층을 분리해 localPosition만 건드립니다.
- `Time.timeScale`을 쓰는 곳은 한 곳(`GameFeel`)으로 모으고, 멈춘 동안의 시간은 unscaled로 잽니다. 히트 스톱은 "늘리기만, 누적하지 않음".
- 넉백은 이동 코드의 속도 덮어쓰기와 충돌하므로 경직 시간을 둡니다. 스쿼시·번쩍임은 시각용 자식에만 적용합니다.
- 흔들림 세기·번쩍임·데미지 숫자 옵션은 처음부터 넣습니다.

## 더 읽을거리

- Unity 매뉴얼 — Particle System: https://docs.unity3d.com/Manual/ParticleSystems.html
- Unity 매뉴얼 — Particle System Main module (Stop Action 포함): https://docs.unity3d.com/Manual/PartSysMainModule.html
- Unity 스크립팅 API — `ObjectPool<T>`: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- GDC 강연 "Juice it or lose it" (Martin Jonasson, Petri Purho, 2012) — 제목으로 검색
- GDC 강연 "Math for Game Programmers: Juicing Your Cameras With Math" (Squirrel Eiserloh, 2016), Jan Willem Nijman "The art of screenshake" — 제목으로 검색
