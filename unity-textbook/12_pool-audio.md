# 12. 오브젝트 풀과 오디오 매니저

> **이 장에서 배울 것**
> - `Instantiate`/`Destroy`가 비싼 이유를 설명하고 Profiler에서 그 비용을 확인할 수 있다
> - `UnityEngine.Pool.ObjectPool<T>`의 생성 인자(createFunc·actionOnGet·actionOnRelease·actionOnDestroy·collectionCheck·defaultCapacity·maxSize)를 목적에 맞게 설정한다
> - 반환 누락·이중 반환 버그를 막고, 재사용되는 오브젝트의 상태 리셋 규칙을 적용한다
> - AudioClip 임포트 설정과 AudioMixer 노출 파라미터(데시벨 변환)로 볼륨 체계를 구성한다
> - SFX 소스 풀·동시 재생 제한·피치 랜덤·중복 방지·BGM 크로스페이드를 갖춘 `AudioManager`를 구현한다
>
> **선수 장**: 01, 02, 03, 05, 06, 07, 09, 10, 11 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 적 500마리가 몰려와도 GC 스파이크가 없는 풀링, 사운드 풀과 설정 화면 볼륨 슬라이더

## 왜 필요한가

05장의 `EnemySpawner`는 적을 `Instantiate`로 만들고, 적은 죽으면 `Destroy`됩니다. 투사체·코인·데미지 숫자도 마찬가지입니다. 10분 판의 후반, 화면에 적 300마리가 있고 초당 투사체 40발, 코인 30개가 생겼다 사라지는 상황을 Profiler로 보면, 프레임마다 `Instantiate`가 수십 번 호출되어 수 ms를 먹고, 프레임당 수백 KB의 GC 할당이 쌓여 몇 초마다 수십 ms짜리 `GC.Collect` 스파이크가 튑니다.

오디오도 무너집니다. 코인 30개를 한 프레임에 먹으면 같은 "띠링"이 30번 겹쳐 재생되어 소리가 찢어지고(클리핑), Unity의 동시 발음 수 한도를 넘은 소리는 제멋대로 잘립니다. 같은 샘플이 똑같은 높이로 반복되면 몇 분 만에 귀가 피로해집니다. 설정 화면의 볼륨 슬라이더를 0.5로 내렸는데 소리가 "반"으로 들리지 않는 문제도 있습니다.

이 장에서는 생성·파괴를 **재사용**으로 바꾸고, 소리를 한 곳에서 관리합니다.

## 개념

### Instantiate와 Destroy는 왜 비싼가

`Instantiate(prefab)` 한 줄 뒤에서 일어나는 일입니다.

```
Instantiate
 1. 네이티브(C++) 쪽 GameObject·컴포넌트 메모리 할당, 프리팹 데이터 복제
 2. C# 래퍼 객체 생성            → 관리 힙 할당 (GC 대상)
 3. Transform 계층 등록, 렌더러를 컬링 시스템에 등록
 4. Collider2D/Rigidbody2D를 물리 월드에 등록 (브로드페이즈 갱신)
 5. 모든 컴포넌트의 Awake → OnEnable 호출 (+ 다음 프레임 전 Start)

Destroy
 → 프레임 끝까지 지연 → OnDisable·OnDestroy → 물리·렌더에서 제거·해제
 → C# 래퍼는 "파괴됨" 상태로 남아 GC가 수거할 때까지 힙에 존재
```

한 번은 싸지만, 프레임당 수십 번이면 CPU 시간과 GC 쓰레기가 누적됩니다. **풀링**은 오브젝트를 파괴하지 않고 비활성화해 보관했다가 다시 꺼내 쓰는 방식입니다. `SetActive(false/true)`에도 OnDisable/OnEnable과 물리 등록·해제 비용이 있지만, 1·2·5의 Awake·네이티브 할당·GC가 사라집니다.

### `ObjectPool<T>` 한눈에 보기

Unity 2021부터 `UnityEngine.Pool` 이름공간에 풀이 내장되어 있습니다.

```csharp
var pool = new ObjectPool<T>(
    createFunc,          // Func<T>     : 풀이 비어 있을 때 새로 만드는 방법 (필수)
    actionOnGet,         // Action<T>   : Get() 으로 꺼낼 때마다
    actionOnRelease,     // Action<T>   : Release() 로 돌려줄 때마다
    actionOnDestroy,     // Action<T>   : 풀이 가득 차서 버리거나 Clear() 할 때
    collectionCheck,     // bool        : 이미 풀에 있는 걸 또 Release 하면 예외 (기본 true)
    defaultCapacity,     // int         : 내부 스택의 초기 용량 (기본 10) — 미리 만들어두지는 않음!
    maxSize);            // int         : 풀에 보관할 최대 개수 (기본 10000). 넘치면 actionOnDestroy
```

`Get()`은 보관분이 있으면 꺼내고 없으면 `createFunc`를 부른 뒤 `actionOnGet`, `Release(x)`는 `actionOnRelease` 후 보관합니다. `CountActive`/`CountInactive`/`CountAll`로 사용 중·보관 중·전체 수를, `Clear()`로 보관분 전체를 `actionOnDestroy`합니다.

주의할 점 두 가지:

- **`defaultCapacity`는 미리 생성(prewarm)이 아닙니다.** 내부 컬렉션 용량일 뿐이라, 첫 웨이브 때 `createFunc`가 한꺼번에 불려 버벅입니다. 미리 만들려면 로딩 중에 `Get`을 N번 한 뒤 모두 `Release`합니다.
- **`maxSize`는 "보관" 상한**이지 "동시 사용" 상한이 아닙니다. 사용 중인 개수는 제한하지 않으므로 적 수 제한은 스포너가 따로 해야 합니다.

같은 이름공간의 `ListPool<T>`, `DictionaryPool<K,V>` 등 컬렉션 풀은 02장의 임시 리스트 할당을 없애는 데 씁니다.

### 반환 누락과 이중 반환

풀링 버그는 거의 이 두 가지입니다.

| 버그 | 증상 | 흔한 원인 | 방지책 |
|---|---|---|---|
| 반환 누락 (leak) | `CountActive`가 계속 증가, 화면 밖에 비활성화 안 된 오브젝트 누적, 결국 매번 새로 생성 | 화면 밖으로 나간 투사체 경로에서 Release 안 함, `Destroy`를 습관적으로 호출 | 모든 종료 경로(명중·수명·화면 밖)를 한 메서드 `Despawn()`으로 모음 |
| 이중 반환 | `InvalidOperationException: Trying to release an object that has already been released to the pool.` 또는 (체크 끔) 같은 객체가 두 번 꺼내져 두 곳에서 동시에 쓰임 | 한 프레임에 적 두 마리와 충돌, 수명 만료와 명중이 같은 프레임 | 오브젝트 안에 `bool isSpawned` 플래그, `collectionCheck`는 개발 중 켜기 |

`collectionCheck`는 Release마다 보관 목록을 검사하므로 보관 수가 많을수록 느려집니다. 에디터에서만 켜고(`Application.isEditor`) 빌드에서는 끄는 절충이 흔합니다. 플래그 방어는 항상 둡니다.

### 상태 리셋 규칙 — "새로 태어난 것처럼"

풀에서 꺼낸 오브젝트는 **지난 생의 상태를 그대로 들고 옵니다.** 체력 0, 반쯤 투명한 색, 날아가던 속도, 돌고 있던 코루틴까지. 규칙을 정해 둡니다.

| 무엇을 | 어디서 | 예시 |
|---|---|---|
| 자기 자신만으로 정해지는 초기값 | `OnEnable` | 색·알파 복구, 타이머 0, `isSpawned = true`, 이벤트 구독 |
| 외부에서 주는 값 | `Get` 직후 호출하는 `Init(...)` | 이동 방향, 데미지, 표시할 숫자, EnemyData |
| 정리 | `OnDisable` | 이벤트 구독 해제, `isSpawned = false` |
| 물리 | `Init` 또는 `OnEnable` | `linearVelocity = Vector2.zero`, `angularVelocity = 0` |
| 궤적·파티클 | 위치 이동 **후** | `TrailRenderer.Clear()`, `ParticleSystem.Clear()` 후 `Play()` |

**`Awake`와 `Start`는 한 번만 불립니다.** 재사용마다 필요한 초기화를 `Start`에 두면 두 번째 생부터 적용되지 않습니다. 또 **활성화 순서**도 중요합니다. `actionOnGet`에서 `SetActive(true)`를 하면 `OnEnable`이 위치를 옮기기 **전에** 실행됩니다. 트레일이 이전 위치에서 새 위치로 선을 긋거나, 한 프레임 동안 엉뚱한 곳에서 충돌할 수 있습니다. 그래서 이 장에서는 **위치를 먼저 옮기고 활성화**하는 `Spawn` 도우미를 씁니다.

같은 문제가 **생성 순간**에도 있습니다. 활성 상태인 프리팹을 `Instantiate`하면 복제 도중에 `Awake`와 `OnEnable`이 실행됩니다. 그 뒤에 `SetActive(false)`를 해도 이미 늦어서, 첫 생의 `OnEnable`은 `Pool` 지정·위치 설정 전에 한 번 돌아 버립니다. 그래서 풀의 `createFunc`는 **비활성 부모(staging) 아래에 복제**합니다. 부모가 비활성이면 복제본도 계층상 비활성이라 `Awake`/`OnEnable`이 호출되지 않고, 준비를 모두 마친 뒤 `Spawn`에서 처음 켜질 때 `Awake → OnEnable` 순서로 실행됩니다.

비활성화되면 그 오브젝트에서 돌던 코루틴은 모두 멈추고 재개되지 않습니다. 필요하면 `OnEnable`에서 다시 시작합니다.

### 오디오 임포트 설정

AudioClip을 선택하면 Inspector에서 플랫폼별로 설정합니다.

- **Load Type**: `Decompress On Load`(로드 시 PCM으로 풀어 보관 — CPU 최소, 메모리 최대), `Compressed In Memory`(압축 보관, 재생 시 디코딩), `Streaming`(디스크에서 읽으며 디코딩 — 메모리 최소).
- **Compression Format**: PCM(무압축) / ADPCM(약 3.5:1, 디코딩 가벼움) / Vorbis(압축률 높음, Quality 슬라이더).
- **Force To Mono**는 효과음 메모리를 절반으로, **Preload Audio Data**를 끄면 첫 재생 때 로드되어 늦을 수 있습니다.

코인 러시의 기준입니다.

| 종류 | 예 | Load Type | Format | 기타 |
|---|---|---|---|---|
| 짧고 잦은 SFX (< 1초) | 코인, 타격, 발사 | Decompress On Load | ADPCM | Force To Mono, Preload 켬 |
| 중간 길이 SFX (1~5초) | 레벨업, 보스 등장 | Compressed In Memory | Vorbis 70% | Mono |
| BGM (수 분) | 전투 음악 | Streaming | Vorbis 60~70% | Preload 끔 |

### AudioMixer와 데시벨

AudioMixer는 믹싱 콘솔입니다. AudioSource의 **Output**을 믹서 그룹에 연결하면 그룹 단위로 볼륨·이펙트를 겁니다.

`Master` 아래에 `BGM`, `SFX` 그룹을 두고 음악·효과음 소스를 각각 연결하는 구성이 기본입니다. 그룹의 Volume은 **데시벨(dB)** 입니다. 0dB가 원래 크기, -6dB가 대략 진폭 절반, -80dB가 사실상 무음입니다. 사람의 음량 지각은 로그에 가까워서, 슬라이더 값(0~1)을 그대로 -80~0에 선형 대응하면 슬라이더 오른쪽 20%에서만 소리가 변하는 것처럼 느껴집니다. 그래서 선형 값을 데시벨로 변환합니다.

```
dB = 20 × log10(v)     v=1 → 0dB,  v=0.5 → -6dB,  v=0.1 → -20dB,  v=0 → -∞ (그래서 0.0001 = -80dB로 하한)
```

스크립트에서 바꾸려면 파라미터를 **노출(expose)** 해야 합니다. 믹서 그룹을 선택하고 Inspector의 Volume 이름 위에서 우클릭 → **Expose 'Volume (of SFX)' to script**. 그다음 Audio Mixer 창 오른쪽 위 **Exposed Parameters** 목록에서 이름을 `SFXVolume`처럼 바꿉니다. 코드는 `mixer.SetFloat("SFXVolume", dB)`입니다.

> 알려진 함정: `AudioMixer.SetFloat`를 **`Awake`에서 호출하면 적용되지 않는 경우**가 있습니다. 저장된 볼륨 적용은 `Start` 이후에 하세요.

### AudioManager 설계

`AudioSource.PlayOneShot`은 편하지만 개별로 멈추거나 수를 셀 수 없습니다. 대신 AudioSource를 여러 개 만들어 두고 직접 배정합니다.

```
PlaySfx(coinSfx)
 1. 같은 프레임에 이미 coinSfx를 재생했나?          → 예: 무시 (30개 동시 획득 = 1번)
 2. coinSfx가 지금 몇 개 재생 중인가? ≥ maxVoices  → 예: 무시
 3. 쉬고 있는 AudioSource 찾기                     → 없으면 가장 오래 재생한 소스를 빼앗음
 4. clip 무작위 선택, pitch = Random(0.95~1.05), volume 설정 → Play()
```

피치를 ±5% 흔드는 것만으로 반복 피로가 크게 줄어듭니다. 클립 변형(coin_01~03)을 섞으면 더 좋습니다.

BGM은 AudioSource 두 개를 번갈아 쓰며 한쪽 볼륨을 올리고 다른 쪽을 내리는 **크로스페이드**로 전환합니다. 레벨업 창에서 `timeScale = 0`이어도 페이드가 진행되도록 `unscaledDeltaTime`을 씁니다.

## 실습: 코인 러시에 적용하기

앞 장 클래스의 최소 시그니처입니다. 이름이 다르면 맞춰 조정하세요.

```csharp
// 01 Health     : int Current, int Max, event Action<int,int> Changed, event Action Died, TakeDamage(int)
// 03 EnemyData  : string displayName, int maxHp, float moveSpeed, int contactDamage, int coinDrop, GameObject prefab
// 03 WeaponData : int damage, float cooldown, Projectile projectilePrefab, float projectileSpeed
// 03 IntEventChannel : void Raise(int)
// 10 SaveSystem : static SaveData Load(), static void Save(SaveData data)
```

스크립트 폴더는 `Assets/_CoinRush/Scripts/Pooling/`, `.../Combat/`, `.../Audio/`이고, 앞 장 파일을 교체할 때는 원래 위치(`.../Weapons/`, `.../Items/`, `.../Enemies/`)를 그대로 씁니다.

### 1단계 — Health 리셋은 01장 메서드로

재사용되는 적은 체력을 다시 채워야 합니다. 01장 `Health.Initialize(int newMax)`가 최대 체력 설정, 가득 채우기, `Changed` 발행을 이미 하므로 새 메서드 없이 그대로 씁니다. 체력 배율처럼 최대 체력만 바꿀 때는 10장의 `SetMax(int newMax, bool refill)`을 씁니다.

### 2단계 — 풀 도우미

풀마다 같은 콜백을 반복해 쓰지 않도록 작은 정적 도우미와 인터페이스를 만듭니다.

```csharp
// Assets/_CoinRush/Scripts/Pooling/IPooled.cs
using UnityEngine.Pool;

public interface IPooled<T> where T : class
{
    IObjectPool<T> Pool { get; set; }
}
```

```csharp
// Assets/_CoinRush/Scripts/Pooling/PoolUtil.cs
using UnityEngine;
using UnityEngine.Pool;

public static class PoolUtil
{
    /// <summary>프리팹 기반 컴포넌트 풀. 비활성 부모 아래에서 복제해 Awake/OnEnable 없이 만들고, 꺼낼 때는 Spawn을 쓰세요.</summary>
    public static ObjectPool<T> Create<T>(T prefab, Transform parent, int prewarm, int maxSize)
        where T : Component, IPooled<T>
    {
        // 비활성 staging 부모: 이 아래에서 복제하면 복제본이 계층상 비활성이라 Awake/OnEnable이 불리지 않음
        var staging = new GameObject("_Staging");
        staging.SetActive(false);
        staging.transform.SetParent(parent, false);

        ObjectPool<T> pool = null;
        pool = new ObjectPool<T>(
            createFunc: () =>
            {
                T item = Object.Instantiate(prefab, staging.transform);   // 여기서는 Awake/OnEnable 없음
                item.gameObject.SetActive(false);    // 자기 자신도 끈 뒤
                item.Pool = pool;                    // 람다가 변수 pool을 캡처 — 호출 시점엔 이미 대입됨
                item.transform.SetParent(parent, false);   // 원래 그룹으로 옮김 (activeSelf=false라 여전히 꺼져 있음)
                return item;
            },
            actionOnGet: null,                        // 활성화는 Spawn에서 "위치 이동 후" 수행
            actionOnRelease: item => item.gameObject.SetActive(false),
            actionOnDestroy: item => Object.Destroy(item.gameObject),
            collectionCheck: Application.isEditor,
            defaultCapacity: prewarm,
            maxSize: maxSize);

        Prewarm(pool, prewarm);
        return pool;
    }

    public static T Spawn<T>(this ObjectPool<T> pool, Vector3 position) where T : Component
    {
        T item = pool.Get();
        item.transform.SetPositionAndRotation(position, Quaternion.identity);
        item.gameObject.SetActive(true);             // 여기서 (첫 생이면 Awake →) OnEnable — 위치·Pool은 이미 올바름
        return item;
    }

    private static void Prewarm<T>(ObjectPool<T> pool, int count) where T : class
    {
        // Get으로 count개를 만들고 한꺼번에 돌려놓음 (ListPool로 임시 리스트 할당도 피함)
        // 복제·네이티브 할당은 여기서 끝나고, 가벼운 Awake는 각 오브젝트가 처음 Spawn될 때 한 번 실행됨
        var temp = ListPool<T>.Get();
        for (int i = 0; i < count; i++) temp.Add(pool.Get());
        foreach (T item in temp) pool.Release(item);
        ListPool<T>.Release(temp);
    }
}
```

### 3단계 — 투사체

```csharp
// Assets/_CoinRush/Scripts/Weapons/Projectile.cs  (03·05장 파일 교체)
using UnityEngine;
using UnityEngine.Pool;

[RequireComponent(typeof(Rigidbody2D))]
public class Projectile : MonoBehaviour, IPooled<Projectile>
{
    [SerializeField] private LayerMask targetLayers;  // 03장과 같음 — 플레이어 자신의 Health를 맞히지 않게
    [SerializeField] private float lifetime = 2f;
    [SerializeField] private TrailRenderer trail;     // 없으면 비워둠

    public IObjectPool<Projectile> Pool { get; set; }

    private Rigidbody2D body;
    private int damage;
    private float age;
    private bool isSpawned;                           // 03장 consumed 플래그의 역할도 겸함 (재사용마다 OnEnable에서 초기화)

    private void Awake() => body = GetComponent<Rigidbody2D>();

    private void OnEnable()                           // 자기 자신만으로 정해지는 초기값
    {
        age = 0f;
        isSpawned = true;
        if (trail != null) trail.Clear();             // 위치 이동 후 활성화되므로 여기서 지워도 안전
    }

    public void Launch(Vector2 direction, float speed, int damageAmount)   // 03장과 같은 시그니처, 외부에서 주는 값
    {
        damage = damageAmount;
        body.linearVelocity = direction.normalized * speed;
        transform.right = direction;
    }

    private void Update()
    {
        if ((age += Time.deltaTime) >= lifetime) Despawn();
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!isSpawned) return;                       // 같은 프레임 두 번째 충돌 무시
        if (!targetLayers.Contains(other.gameObject.layer)) return;
        if (other.TryGetComponent(out IDamageable target))
        {
            target.TakeDamage(damage);
            Despawn();
        }
    }

    private void Despawn()
    {
        if (!isSpawned) return;                       // 이중 반환 방어
        isSpawned = false;
        body.linearVelocity = Vector2.zero;
        if (Pool != null) Pool.Release(this);
        else Destroy(gameObject);                     // 풀 없이 씬에 직접 놓은 경우
    }
}
```

`OnTriggerEnter2D`는 `SetActive(false)`된 뒤에는 더 호출되지 않지만, **같은 물리 스텝에서 겹친 두 콜라이더**에 대해서는 비활성화 전에 연달아 호출될 수 있습니다. `isSpawned` 검사가 그 경우를 막습니다.

### 4단계 — 코인과 데미지 숫자

```csharp
// Assets/_CoinRush/Scripts/Items/Coin.cs  (01·02·03장 Coin 교체 — Pickup 상속 대신 풀 반환)
using UnityEngine;
using UnityEngine.Pool;

public class Coin : MonoBehaviour, IPooled<Coin>
{
    [SerializeField] private IntEventChannel collected;          // 03장과 같은 필드
    [SerializeField] private SfxData pickupSfx;
    [SerializeField] private int value = 1;

    public IObjectPool<Coin> Pool { get; set; }
    private Rigidbody2D body;
    private bool isSpawned;

    private void Awake() => body = GetComponent<Rigidbody2D>();

    private void OnEnable()
    {
        isSpawned = true;
        body.linearVelocity = Vector2.zero;                       // 지난 생에 끌려가던 속도 제거
    }

    // 02장 CoinMagnet이 호출 (02장과 같음)
    public void Attract(Vector2 target, float speed)
    {
        body.gravityScale = 0f;
        body.linearVelocity = (target - body.position).normalized * speed;
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!isSpawned || !other.CompareTag("Player")) return;
        isSpawned = false;
        collected.Raise(value);
        AudioManager.Instance.PlaySfx(pickupSfx);
        if (Pool != null) Pool.Release(this);
        else Destroy(gameObject);                                 // 씬에 직접 놓았거나 풀 밖에서 생성된 코인
    }
}
```

11장에서 만든 경험치 보석도 같은 규칙으로 바꿉니다. 06장 드롭 테이블에서 코인 다음으로 자주 나오므로 풀링 대상입니다.

```csharp
// Assets/_CoinRush/Scripts/Items/XpGem.cs  (11장 파일 교체)
using UnityEngine;
using UnityEngine.Pool;

public class XpGem : MonoBehaviour, IPooled<XpGem>
{
    [SerializeField, Min(1)] private int value = 1;

    public IObjectPool<XpGem> Pool { get; set; }
    private bool isSpawned;

    private void OnEnable() => isSpawned = true;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!isSpawned || !other.CompareTag("Player")) return;
        PlayerExperience experience = other.GetComponentInParent<PlayerExperience>();
        if (experience == null) return;

        isSpawned = false;                                        // 같은 스텝 중복 획득 방지
        experience.Add(value);
        if (Pool != null) Pool.Release(this);
        else Destroy(gameObject);
    }
}
```

```csharp
// Assets/_CoinRush/Scripts/Combat/DamageNumber.cs
using TMPro;
using UnityEngine;
using UnityEngine.Pool;

public class DamageNumber : MonoBehaviour, IPooled<DamageNumber>
{
    [SerializeField] private TextMeshPro label;       // 월드 공간용 TextMeshPro (UGUI 아님)
    [SerializeField] private float duration = 0.6f;
    [SerializeField] private float riseSpeed = 1.5f;

    public IObjectPool<DamageNumber> Pool { get; set; }
    private float age;

    private void OnEnable()
    {
        age = 0f;
        label.alpha = 1f;                              // 지난 생의 페이드아웃 상태 복구
        transform.localScale = Vector3.one;
    }

    public void Init(int amount, Color color)
    {
        label.color = color;
        label.SetText("{0}", amount);                 // 숫자 인자 SetText — 문자열 할당 없음
    }

    private void Update()
    {
        age += Time.deltaTime;
        float t = age / duration;
        transform.position += Vector3.up * (riseSpeed * (1f - t) * Time.deltaTime);
        label.alpha = 1f - t * t;
        if (age >= duration) Pool.Release(this);
    }
}
```

### 5단계 — 풀 보관소

씬에 하나 두고 모든 게임플레이 풀을 소유합니다.

```csharp
// Assets/_CoinRush/Scripts/Pooling/GameplayPools.cs
using UnityEngine;
using UnityEngine.Pool;

public class GameplayPools : MonoBehaviour
{
    [SerializeField] private Projectile projectilePrefab;
    [SerializeField] private Coin coinPrefab;
    [SerializeField] private XpGem xpGemPrefab;
    [SerializeField] private DamageNumber damageNumberPrefab;

    public ObjectPool<Projectile> Projectiles { get; private set; }
    public ObjectPool<Coin> Coins { get; private set; }
    public ObjectPool<XpGem> XpGems { get; private set; }
    public ObjectPool<DamageNumber> DamageNumbers { get; private set; }

    private void Awake()
    {
        Projectiles   = PoolUtil.Create(projectilePrefab,   Group("Projectiles"),   prewarm: 100, maxSize: 400);
        Coins         = PoolUtil.Create(coinPrefab,         Group("Coins"),         prewarm: 100, maxSize: 600);
        XpGems        = PoolUtil.Create(xpGemPrefab,        Group("XpGems"),        prewarm: 50,  maxSize: 300);
        DamageNumbers = PoolUtil.Create(damageNumberPrefab, Group("DamageNumbers"), prewarm: 50,  maxSize: 200);
    }

    /// <summary>06장 LootTable이 고른 프리팹을 알맞은 풀에서 꺼냄. 풀이 없는 드문 아이템(자석 등)은 Instantiate.</summary>
    public void SpawnLoot(GameObject prefab, Vector3 position)
    {
        // LootTable 항목과 이 컴포넌트가 "같은 프리팹 에셋"을 참조해야 비교가 맞습니다
        if (prefab == coinPrefab.gameObject) Coins.Spawn(position);
        else if (prefab == xpGemPrefab.gameObject) XpGems.Spawn(position);
        else Instantiate(prefab, position, Quaternion.identity);   // 판당 몇 개뿐이라 풀링 이득이 작음
    }

    private Transform Group(string groupName)          // Hierarchy가 정리되어 누수 확인이 쉬움
    {
        var t = new GameObject(groupName).transform;
        t.SetParent(transform, false);
        return t;
    }

    // 씬이 내려가면 자식인 풀 오브젝트도 함께 파괴되므로 여기서 Clear/Dispose하지 않습니다.
    // (파괴 순서가 정해져 있지 않아 이미 파괴된 오브젝트에 Destroy를 호출할 수 있음)
}
```

무기 쪽(03·05장에서 만든 발사 코드)은 `[SerializeField] private GameplayPools pools;` 필드를 추가하고 `Instantiate(weapon.projectilePrefab, ...)` 줄을 이렇게 바꿉니다.

```csharp
// 발사 메서드 안 — Instantiate 대신
Projectile shot = pools.Projectiles.Spawn(transform.position);
shot.Launch(aimDirection, weapon.projectileSpeed, weapon.damage);
```

`WeaponData.projectilePrefab`이 여러 종류라면 `Dictionary<GameObject, ObjectPool<Projectile>>`로 프리팹별 풀을 만듭니다. 적 풀에서 그 방식을 보여줍니다.

### 6단계 — 풀링되는 적

07장에서 교체한 `Enemy`를 풀링에 맞게 고칩니다. **누적 정본을 보존**하는 것이 중요합니다: `data`·`Data` 프로퍼티(07장 `EnemyMotor2D`·`PlayerContactDamage`가 사용), `FaceDirection`(07장 `EnemyMotor2D`가 호출), `aliveEnemies` 등록·해제(05장 `AutoAimWeapon`이 검색), 07장에서 옮긴 이동 책임(`EnemyMotor2D`)은 그대로 두고, 바뀌는 곳은 초기화·사망 경로입니다. 이동 코드는 이 파일에 다시 넣지 않습니다.

```csharp
// Assets/_CoinRush/Scripts/Enemies/Enemy.cs  (07장 파일 교체 — 풀링·06장 드롭 반영)
using UnityEngine;
using UnityEngine.Pool;

[RequireComponent(typeof(Health), typeof(Rigidbody2D))]
public class Enemy : MonoBehaviour, IPooled<Enemy>
{
    [SerializeField] private EnemyData data;                  // 05장과 같은 필드 — 씬에 직접 배치할 때 기본값
    [SerializeField] private HealthRuntimeSet aliveEnemies;   // 05장과 같은 필드 — AutoAimWeapon의 조준 대상 목록
    [SerializeField] private SpriteRenderer sprite;           // 07장과 같은 필드 — 좌우 반전 (07장의 coinPrefab 필드는 풀로 대체되어 삭제)
    [SerializeField] private SfxData hitSfx;
    [SerializeField] private SfxData deathSfx;

    public IObjectPool<Enemy> Pool { get; set; }
    public EnemyData Data => data;                            // 07장 EnemyMotor2D·PlayerContactDamage가 사용

    private Health health;
    private Rigidbody2D body;
    private EnemyLoot loot;                                   // 06장 (프리팹에 없으면 null)
    private GameplayPools pools;
    private int lastHp;
    private bool isSpawned;

    private void Awake()
    {
        health = GetComponent<Health>();
        body = GetComponent<Rigidbody2D>();
        loot = GetComponent<EnemyLoot>();
        if (data != null) health.Initialize(data.maxHp);
    }

    private void OnEnable()
    {
        isSpawned = true;
        lastHp = health.Current;
        aliveEnemies.Add(health);                              // 05장: 조준 대상 등록
        health.Died += OnDied;
        health.Changed += OnHealthChanged;
    }

    private void OnDisable()
    {
        isSpawned = false;
        aliveEnemies.Remove(health);                           // 05장: 조준 대상 해제
        health.Died -= OnDied;
        health.Changed -= OnHealthChanged;
    }

    // 07장 Init(data, target)에 풀 참조를 더한 시그니처 (22장 스포너도 이 형태로 호출).
    // player는 받기만 합니다. 추적 대상은 07장 EnemyMotor2D가 스스로 찾습니다.
    public void Init(EnemyData enemyData, Transform player, GameplayPools gameplayPools)
    {
        data = enemyData;
        pools = gameplayPools;
        body.linearVelocity = Vector2.zero;                    // 지난 생의 넉백·추적 속도 제거
        health.Initialize(data.maxHp);                         // 01장 메서드. Changed 발생 → lastHp 갱신
    }

    // 07장과 같음 — EnemyMotor2D가 이동 방향을 알려 줌
    public void FaceDirection(Vector2 direction)
    {
        if (sprite != null && Mathf.Abs(direction.x) > 0.01f)
            sprite.flipX = direction.x < 0f;
    }

    private void OnHealthChanged(int current, int max)
    {
        int damage = lastHp - current;
        lastHp = current;
        if (damage <= 0 || !isSpawned || pools == null) return;   // 리셋(증가) 무시, 풀 밖 적은 숫자 없음

        DamageNumber number = pools.DamageNumbers.Spawn(transform.position + Vector3.up * 0.5f);
        number.Init(damage, Color.white);
        AudioManager.Instance.PlaySfx(hitSfx);
    }

    private void OnDied()
    {
        if (!isSpawned) return;
        isSpawned = false;
        aliveEnemies.Remove(health);                           // 반환을 기다리지 않고 즉시 조준 대상에서 제외

        if (pools != null)
        {
            for (int i = 0; i < data.coinDrop; i++)            // 기본 코인 (06장 권장: coinDrop = 기본, LootTable = 추가)
            {
                Vector2 offset = Random.insideUnitCircle * 0.4f;
                pools.Coins.Spawn(transform.position + (Vector3)offset);
            }
            if (loot != null) loot.Drop(pools, transform.position);   // 06장 추가 드롭도 풀에서
        }
        AudioManager.Instance.PlaySfx(deathSfx);

        if (Pool != null) Pool.Release(this);
        else Destroy(gameObject);                              // 씬에 직접 배치한 적
    }
}
```

`aliveEnemies.Remove`는 `OnDied`와 `OnDisable` 양쪽에 있지만, 03장 `RuntimeSet.Remove`는 없는 항목이면 아무 일도 하지 않으므로 안전합니다. 접촉 데미지는 07장 `PlayerContactDamage`가 `enemy.Data.contactDamage`로 처리하므로 이 파일에는 없습니다.

06장 `EnemyLoot`는 스스로 `Died`를 구독해 `Instantiate`했습니다. 이 구조로는 풀 참조를 받을 수 없고, `Enemy.OnDied`가 먼저 풀로 반환한 뒤에 호출될 수도 있습니다. 드롭 시점을 `Enemy`가 정하도록 교체합니다.

```csharp
// Assets/_CoinRush/Scripts/Loot/EnemyLoot.cs  (06장 파일 교체)
using System.Collections.Generic;
using UnityEngine;

public class EnemyLoot : MonoBehaviour
{
    [SerializeField] private LootTable table;
    [SerializeField] private float scatterRadius = 0.6f;

    private static readonly List<GameObject> buffer = new();   // 모든 적이 공유 (메인 스레드 전용)

    // 12장 Enemy.OnDied가 호출합니다. Died 이벤트를 직접 구독하지 않습니다.
    public void Drop(GameplayPools pools, Vector3 origin)
    {
        if (table == null) return;
        table.Roll(buffer);
        for (int i = 0; i < buffer.Count; i++)
        {
            Vector3 pos = origin + (Vector3)(Random.insideUnitCircle * scatterRadius);
            pools.SpawnLoot(buffer[i], pos);
        }
    }
}
```

### 7단계 — 적 500마리 스포너

```csharp
// Assets/_CoinRush/Scripts/Enemies/EnemySpawner.cs  (05장 파일 교체)
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Pool;
using UnityEngine.Serialization;

public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private EnemyData[] enemyTypes;
    [FormerlySerializedAs("target")]                    // 05장 필드 이름 target → player: 기존 Inspector 연결 승계
    [SerializeField] private Transform player;
    [SerializeField] private GameplayPools pools;
    [SerializeField] private float spawnInterval = 0.05f;
    [SerializeField] private int maxAlive = 500;
    [SerializeField] private float spawnRadius = 12f;   // 카메라 밖 거리

    private readonly Dictionary<EnemyData, ObjectPool<Enemy>> poolByType = new();
    private float timer;
    private int totalAlive;

    private void Awake()
    {
        foreach (EnemyData type in enemyTypes)
        {
            var parent = new GameObject($"Enemies_{type.name}").transform;
            parent.SetParent(transform, false);
            // 준비량은 "보통 전투"의 종류별 동시 수. 이를 넘으면 createFunc가 추가 생성합니다(아래 설명)
            poolByType[type] = PoolUtil.Create(type.prefab.GetComponent<Enemy>(), parent, prewarm: 150, maxSize: maxAlive);
        }
    }

    private void Update()
    {
        totalAlive = 0;
        foreach (var pool in poolByType.Values) totalAlive += pool.CountActive;

        timer += Time.deltaTime;
        while (timer >= spawnInterval)
        {
            timer -= spawnInterval;
            if (totalAlive >= maxAlive) { timer = 0f; break; }   // maxSize는 동시 사용 수를 막지 않음
            SpawnOne();
            totalAlive++;
        }
    }

    private void SpawnOne()
    {
        EnemyData type = enemyTypes[Random.Range(0, enemyTypes.Length)];
        Vector2 dir = Random.insideUnitCircle.normalized;
        Vector3 position = player.position + (Vector3)(dir * spawnRadius);

        Enemy enemy = poolByType[type].Spawn(position);
        enemy.Init(type, player, pools);
    }
}
```

`foreach`로 `Dictionary.Values`를 도는 것은 구조체 열거자를 쓰므로 할당이 생기지 않습니다(02장). 웨이브 규칙(시간대별 종류·빈도)은 22장에서 `WaveData`로 대체합니다.

**준비량 정책**: 종류마다 150개를 미리 만들므로 Slime·Bat 두 종류면 합계 300개입니다. `maxAlive` 500까지 몰리면 부족분 200개 정도는 전투 중 `createFunc`로 **추가 생성**됩니다. 한 번 만든 것은 풀에 남으므로(maxSize 500) 그 판의 나머지 시간과 다음 재사용에서는 다시 생성되지 않습니다. 첫 최대 전투의 끊김까지 없애려면 종류별 준비량을 `maxAlive`(한 종류가 전부를 차지할 수 있으므로)로 올리되, 그만큼 로딩 시간과 메모리가 늘어나는 것을 18장에서 측정해 정합니다. 코인·보석도 수거되지 않고 쌓이면 준비량을 넘어 늘어나므로, 필요하면 수명이나 최대 개수를 둡니다.

에디터 작업:

1. 빈 오브젝트 `Pools`에 `GameplayPools`를 붙이고 네 프리팹(Projectile, Coin, XpGem, DamageNumber)을 연결합니다. 각 프리팹 루트에는 해당 스크립트가 있어야 합니다(`DamageNumber` 프리팹은 3D Object → Text - TextMeshPro로 만들고 Sorting Order를 높게). **Coin·XpGem은 06장 `Loot_Basic` 테이블 항목이 가리키는 것과 같은 프리팹 에셋**이어야 `SpawnLoot`가 풀을 찾습니다.
2. `EnemySpawner` Inspector 확인: 파일을 교체하면 슬롯 이름이 `Target`에서 `Player`로 바뀝니다. `FormerlySerializedAs` 덕분에 기존 연결이 옮겨져 있어야 하지만, **Player 슬롯이 비어 있으면 Hierarchy의 Player를 드래그**합니다(비어 있으면 첫 스폰에서 NullReferenceException). 05장의 `View Camera`·`Interval`·`Margin` 슬롯은 사라지고 `Spawn Interval`·`Max Alive`·`Spawn Radius`가 생깁니다. `Pools`에는 `Pools` 오브젝트를 연결합니다.
3. 적 프리팹 확인: Rigidbody2D·트리거 콜라이더·`EnemyMotor2D`는 **07장 설정 그대로**(Kinematic, Is Trigger) 둡니다. `Enemy`의 `Data`·`Alive Enemies`는 05장 값이 유지되어야 합니다. 05장에서 붙인 `DamageOnTouch`가 남아 있다면 제거합니다(07장부터 접촉 피해는 `PlayerContactDamage` 담당이고, `destroySelfOnHit`이 풀 오브젝트를 `Destroy`해 버립니다). `EnemyLoot`는 붙인 채로 둡니다.

### 8단계 — SfxData와 AudioManager

```csharp
// Assets/_CoinRush/Scripts/Audio/SfxData.cs
using UnityEngine;

[CreateAssetMenu(menuName = "CoinRush/Sfx Data", fileName = "Sfx_")]
public class SfxData : ScriptableObject
{
    public AudioClip[] clips;
    [Range(0f, 1f)] public float volume = 1f;
    [Range(0.5f, 1.5f)] public float pitchMin = 0.95f;
    [Range(0.5f, 1.5f)] public float pitchMax = 1.05f;
    [Min(1)] public int maxVoices = 3;          // 이 소리의 최대 동시 재생 수
}
```

```csharp
// Assets/_CoinRush/Scripts/Audio/AudioManager.cs  (03장에서 본 싱글턴 골격을 확장)
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Audio;

public class AudioManager : MonoBehaviour
{
    public const string BgmParam = "BGMVolume";
    public const string SfxParam = "SFXVolume";

    // 오디오는 게임 전체의 인프라라서 정적 접근을 허용합니다. 09장 부트스트랩 씬에 두고 DontDestroyOnLoad.
    public static AudioManager Instance { get; private set; }

    [SerializeField] private AudioMixer mixer;
    [SerializeField] private AudioMixerGroup sfxGroup;
    [SerializeField] private AudioMixerGroup bgmGroup;
    [SerializeField] private int sfxVoiceCount = 16;

    private AudioSource[] sfxSources;
    private SfxData[] sourceOwner;          // 각 소스가 지금 어떤 SfxData를 재생 중인지
    private float[] sourceStartTime;
    private readonly Dictionary<SfxData, int> lastPlayedFrame = new();

    private AudioSource bgmA, bgmB;
    private Coroutine fadeRoutine;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);

        sfxSources = new AudioSource[sfxVoiceCount];
        sourceOwner = new SfxData[sfxVoiceCount];
        sourceStartTime = new float[sfxVoiceCount];
        for (int i = 0; i < sfxVoiceCount; i++)
            sfxSources[i] = CreateSource($"SFX_{i}", sfxGroup);

        bgmA = CreateSource("BGM_A", bgmGroup);
        bgmB = CreateSource("BGM_B", bgmGroup);
        bgmA.loop = bgmB.loop = true;
    }

    private void Start()
    {
        // SetFloat는 Awake에서 무시될 수 있어 Start에서 적용
        SaveData save = SaveSystem.Load();
        SetVolume(BgmParam, save.bgmVolume);
        SetVolume(SfxParam, save.sfxVolume);
    }

    private AudioSource CreateSource(string sourceName, AudioMixerGroup group)
    {
        var go = new GameObject(sourceName);
        go.transform.SetParent(transform, false);
        var source = go.AddComponent<AudioSource>();
        source.playOnAwake = false;
        source.spatialBlend = 0f;           // 2D 게임: 위치에 따른 감쇠 없음
        source.outputAudioMixerGroup = group;
        return source;
    }

    public void PlaySfx(SfxData data)
    {
        if (data == null || data.clips == null || data.clips.Length == 0) return;

        // 1) 같은 프레임 중복 방지
        int frame = Time.frameCount;
        if (lastPlayedFrame.TryGetValue(data, out int last) && last == frame) return;

        // 2) 동시 재생 제한 + 3) 빈 소스 / 가장 오래된 소스 찾기
        int playingSame = 0;
        int free = -1;
        int oldest = 0;
        for (int i = 0; i < sfxSources.Length; i++)
        {
            bool playing = sfxSources[i].isPlaying;
            if (playing && sourceOwner[i] == data) playingSame++;
            if (!playing && free < 0) free = i;
            if (sourceStartTime[i] < sourceStartTime[oldest]) oldest = i;
        }
        if (playingSame >= data.maxVoices) return;
        int index = free >= 0 ? free : oldest;             // 꽉 찼으면 가장 오래된 소리를 끊음

        // 4) 재생
        AudioSource source = sfxSources[index];
        source.Stop();
        source.clip = data.clips[Random.Range(0, data.clips.Length)];
        source.volume = data.volume;
        source.pitch = Random.Range(data.pitchMin, data.pitchMax);
        source.Play();

        sourceOwner[index] = data;
        sourceStartTime[index] = Time.unscaledTime;
        lastPlayedFrame[data] = frame;
    }

    public void PlayBgm(AudioClip clip, float fadeSeconds = 1f)
    {
        if (bgmA.clip == clip && bgmA.isPlaying) return;
        if (fadeRoutine != null) StopCoroutine(fadeRoutine);
        fadeRoutine = StartCoroutine(Crossfade(clip, fadeSeconds));
    }

    private IEnumerator Crossfade(AudioClip clip, float duration)
    {
        // bgmA = 지금 들리는 쪽. B에 새 곡을 걸고 A↔B 역할 교환
        (bgmA, bgmB) = (bgmB, bgmA);
        bgmA.clip = clip;
        bgmA.volume = 0f;
        bgmA.Play();

        float startB = bgmB.volume;
        float t = 0f;
        while (t < duration)
        {
            t += Time.unscaledDeltaTime;                   // 일시정지 중에도 진행
            float p = Mathf.Clamp01(t / duration);
            bgmA.volume = p;
            bgmB.volume = startB * (1f - p);
            yield return null;
        }
        bgmA.volume = 1f;
        bgmB.Stop();
        fadeRoutine = null;
    }

    public void SetVolume(string exposedParam, float linear01)
        => mixer.SetFloat(exposedParam, LinearToDecibel(linear01));

    public static float LinearToDecibel(float linear01)
        => Mathf.Log10(Mathf.Max(linear01, 0.0001f)) * 20f;       // 0 → -80dB
}
```

> 볼륨은 믹서에서, 개별 소리 크기는 `SfxData.volume`(AudioSource.volume, 0~1 선형)에서 조절합니다. 두 층을 섞어 쓰지 않으면 "어디서 줄였는지" 헷갈리지 않습니다.

에디터 작업:

1. Project 창 우클릭 → Create → Audio → **Audio Mixer**, 이름 `MainMixer`. Window → Audio → Audio Mixer로 열고 Master 아래에 `BGM`, `SFX` 그룹을 추가합니다.
2. `BGM`, `SFX` 그룹의 Volume을 노출하고 이름을 `BGMVolume`, `SFXVolume`으로 바꿉니다.
3. 부트스트랩 씬(09장)에 `AudioManager` 오브젝트를 만들고 mixer·그룹을 연결합니다.
4. 효과음 클립의 임포트 설정을 앞의 표대로 바꾸고 Apply. `Assets/_CoinRush/Audio/`에서 Create → CoinRush → Sfx Data로 `Sfx_Coin`, `Sfx_Hit`, `Sfx_EnemyDeath` 에셋을 만들어 클립을 넣습니다. 코인은 `maxVoices` 2, 타격은 4 정도로 시작합니다.
5. **슬롯 연결** (비워 두면 `PlaySfx`가 아무 경고 없이 반환하므로 반드시 확인):
   - Coin 프리팹의 `Coin` → Pickup Sfx = `Sfx_Coin`
   - 적 프리팹(Slime, Bat)의 `Enemy` → Hit Sfx = `Sfx_Hit`, Death Sfx = `Sfx_EnemyDeath`
6. **음량 여유(headroom)**: 같은 프레임 중복 제거와 `maxVoices`는 "같은 소리의 개수"만 줄일 뿐, 서로 다른 효과음과 BGM이 겹쳐 합산 음량이 0dB를 넘는 것(클리핑)은 막지 못합니다. 그래서 믹서에서 여유를 둡니다.
   - `Master` 그룹 Volume을 **-6dB**로 내립니다(노출하지 않는 고정값).
   - 효과음 사이 상대 음량을 `SfxData.volume`으로 맞춥니다. 시작값: `Sfx_Coin` 0.5(가장 잦음), `Sfx_Hit` 0.6, `Sfx_EnemyDeath` 0.8.
   - BGM은 `Crossfade`가 AudioSource volume을 1로 올리므로, BGM 클립 자체가 너무 크면 `BGM` 그룹에 고정 감쇠를 걸지 말고(노출 파라미터라 슬라이더가 덮어씀) 클립 임포트 전에 음원을 -3~-6dB 낮춰 둡니다.

BGM 전환은 씬마다 "이 씬의 곡"을 요청하는 작은 컴포넌트로 합니다. `AudioManager`는 Bootstrap 씬(09장)에 있어 콘텐츠 씬보다 먼저 `Awake`되므로 `Start`에서 호출하면 안전합니다.

```csharp
// Assets/_CoinRush/Scripts/Audio/SceneBgm.cs
using UnityEngine;

public class SceneBgm : MonoBehaviour
{
    [SerializeField] private AudioClip clip;
    [SerializeField] private float fadeSeconds = 1f;

    private void Start()
    {
        if (AudioManager.Instance != null && clip != null)
            AudioManager.Instance.PlayBgm(clip, fadeSeconds);   // 같은 곡이 이미 재생 중이면 무시됨
    }
}
```

7. Title 씬에 빈 오브젝트 `Bgm` + `SceneBgm`(Clip = 타이틀 곡), Game 씬에도 `Bgm` + `SceneBgm`(Clip = 전투 곡)을 둡니다. Title → Game으로 넘어가면 1초 동안 크로스페이드됩니다.

### 9단계 — 설정 화면 볼륨 슬라이더

10장의 `SaveData`에 필드를 추가합니다. 10장의 규칙대로 `version`을 올리고 마이그레이션에서 기본값을 채우세요.

```csharp
// SaveData.cs (10장) — 필드 추가
public float bgmVolume = 0.8f;
public float sfxVolume = 0.8f;
```

```csharp
// Assets/_CoinRush/Scripts/UI/AudioSettingsView.cs
using UnityEngine;
using UnityEngine.UI;

public class AudioSettingsView : MonoBehaviour
{
    [SerializeField] private Slider bgmSlider;
    [SerializeField] private Slider sfxSlider;
    [SerializeField] private SfxData previewSfx;    // SFX 슬라이더를 움직일 때 들려줄 소리

    private SaveData save;

    private void OnEnable()
    {
        save = SaveSystem.Load();                    // 10장: 모든 곳이 공유하는 같은 인스턴스
        // SetValueWithoutNotify: 초기값 대입이 onValueChanged를 발생시키지 않게
        bgmSlider.SetValueWithoutNotify(save.bgmVolume);
        sfxSlider.SetValueWithoutNotify(save.sfxVolume);

        bgmSlider.onValueChanged.AddListener(OnBgmChanged);
        sfxSlider.onValueChanged.AddListener(OnSfxChanged);
    }

    private void OnDisable()
    {
        bgmSlider.onValueChanged.RemoveListener(OnBgmChanged);
        sfxSlider.onValueChanged.RemoveListener(OnSfxChanged);
        Commit();                                    // 씬 전환 등으로 꺼질 때의 안전망
    }

    /// <summary>설정 창 "닫기" 버튼 OnClick에 연결. 드래그 중 매 프레임이 아니라 닫을 때 한 번 저장.</summary>
    public void Commit() => SaveSystem.SaveIfDirty();

    private void OnBgmChanged(float v)
    {
        save.bgmVolume = v;
        SaveSystem.MarkDirty();                      // 닫기 전에 앱이 백그라운드로 가도 10장 SaveLifecycle이 저장
        AudioManager.Instance.SetVolume(AudioManager.BgmParam, v);
    }

    private void OnSfxChanged(float v)
    {
        save.sfxVolume = v;
        SaveSystem.MarkDirty();
        AudioManager.Instance.SetVolume(AudioManager.SfxParam, v);
        AudioManager.Instance.PlaySfx(previewSfx);   // 같은 프레임 중복 방지 덕에 드래그해도 소음이 적음
    }
}
```

슬라이더 두 개(Min 0, Max 1)를 11장의 `PopupCanvas` 아래 설정 패널에 배치하고 연결합니다. 11장 팝업처럼 CanvasGroup으로 숨기면 `OnDisable`이 불리지 않으므로, 설정 패널의 **닫기 버튼 OnClick에 `AudioSettingsView.Commit`** 을 연결해 명시적으로 저장합니다. 값이 바뀔 때마다 `MarkDirty()`를 해 두었으므로 닫기를 누르기 전에 앱이 백그라운드로 가도 10장 `SaveLifecycle`의 `SaveIfDirty`가 저장합니다. 게임패드로도 좌우 입력으로 값을 바꿀 수 있습니다(Slider는 Selectable).

### 확인하기

1. Play 후 `Pools/Coins`, `EnemySpawner/Enemies_*` 아래에 미리 만든 비활성 오브젝트들이 보입니다. 적 수가 500에서 멈추고, 적을 잡으면 그 자리에 코인·데미지 숫자가 나타났다 사라지며, 풀 아래 오브젝트들이 켜졌다 꺼졌다를 반복합니다(새 오브젝트가 계속 늘지 않음).
2. **Profiler → CPU Usage**에서 적 수가 준비량(종류별 150) 이내로 오가는 동안 `GC.Alloc`이 거의 0이고 `Instantiate` 호출이 나타나지 않습니다. 준비량을 처음 넘는 순간에만 추가 생성이 보이고, 같은 수준을 다시 반복할 때는 사라집니다. 각 풀 그룹 아래의 `_Staging` 오브젝트는 항상 비어 있습니다. (적 500마리의 물리·이동 비용 자체는 18장에서 다룹니다.)
3. 적을 잡으면 자동 조준이 계속 **살아 있는** 적을 향해 쏘고, 떨어진 보석을 먹으면 11장 경험치바가 찹니다. 적에게 닿으면 07장처럼 피해와 넉백이 들어갑니다.
4. 코인 30개를 한꺼번에 먹어도 같은 "띠링"이 한 번만 들리고, 같은 효과음의 높이가 조금씩 다르게 들립니다. **피크 측정**: 적 수백 마리를 한꺼번에 잡는 가장 시끄러운 상황에서 Play 중 Audio Mixer 창의 Master 레벨 미터가 0dB에 닿지 않아야 합니다. 닿으면 8단계 에디터 작업 6번의 Master 감쇠·`SfxData.volume`을 낮춥니다.
5. Title → Game으로 넘어갈 때 BGM이 끊기지 않고 크로스페이드됩니다.
6. 설정의 SFX 슬라이더를 절반으로 내리고 닫기를 누르면 체감상 자연스럽게 작아지고, 게임을 재시작해도 값이 유지됩니다.

## 흔한 실수

1. **재사용된 적이 나타나자마자 죽거나 반투명함** → 체력·색·알파 같은 상태를 `Start`/`Awake`에서만 초기화 → 재사용마다 필요한 값은 `OnEnable` 또는 `Init`에서 리셋합니다.
2. **`Trying to release an object that has already been released` 예외** → 한 프레임에 두 번의 종료 경로(두 적과 충돌, 명중+수명)가 모두 Release → 오브젝트 내부 `isSpawned` 플래그로 첫 번째만 통과시킵니다.
3. **시간이 갈수록 프레임이 떨어지고 `CountAll`이 계속 증가** → 어떤 경로에서 `Destroy`하거나 Release를 빠뜨림 → 종료를 `Despawn()` 하나로 모으고, 디버그용으로 `CountActive`를 화면에 띄워 확인합니다.
4. **트레일이 이전 위치에서 새 위치로 길게 그어짐 / 스폰 순간 엉뚱한 충돌** → 활성화한 뒤 위치를 옮김 → 위치를 먼저 설정하고 `SetActive(true)`, 트레일은 `Clear()`합니다.
5. **저장된 볼륨이 시작할 때 적용되지 않음** → `AudioMixer.SetFloat`를 `Awake`에서 호출, 또는 파라미터 노출 후 이름을 바꾸지 않아 문자열 불일치 → `Start`에서 호출하고 Exposed Parameters 이름을 코드 상수와 맞춥니다.
6. **`Enemy`를 교체했더니 `'Enemy' does not contain a definition for 'Data'`(CS1061) 오류가 나거나 자동 사격이 멈춤** → 앞 장 파일을 교체하면서 다른 장이 쓰던 멤버(`Data`)나 런타임 세트 등록(`aliveEnemies.Add/Remove`)을 빠뜨림 → 교체 전에 그 클래스의 멤버를 누가 쓰는지 검색(Rider/VS의 Find Usages)하고, 6단계 코드처럼 공개 멤버와 등록·해제를 보존합니다.
7. **슬라이더를 0으로 내렸는데 작은 소리가 남거나, 중간값에서 너무 작음** → 선형 값을 그대로 dB에 넣거나 `Log10(0)` = -∞ 처리 누락 → `Mathf.Log10(Mathf.Max(v, 0.0001f)) * 20`을 씁니다.

## 연습 문제

1. ★☆☆ 플레이어가 코인 근처(반경 2)에 오면 코인이 플레이어 쪽으로 빨려가게 하세요. 풀에서 재사용될 때 "빨려가던 상태"가 남지 않아야 합니다.

<details><summary>힌트·해설</summary>

`Coin`에 `bool attracted`와 속도 필드를 두고 `Update`에서 거리를 검사합니다(`sqrMagnitude`로 제곱근 피하기, 05장). `attracted = false`와 속도 0 리셋은 반드시 `OnEnable`에 둡니다. 플레이어 참조는 `Init(Transform player)`로 받거나 `GameplayPools`가 보관한 참조를 씁니다. 가속을 붙이면(06장 이징) "쏙" 빨려드는 느낌이 납니다. 이 기능은 16장에서 `CoinMagnet`(코인 프리팹에 부착)으로 정식 구현해 02장 자석과 이 연습 코드를 대체하므로, 연습 코드는 본 프로젝트에 남기지 마세요.

</details>

2. ★★☆ `AudioManager`에 "같은 프레임 중복 방지"를 넘어서, `SfxData`마다 `minInterval`(예: 0.05초) 안에는 다시 재생하지 않는 기능을 추가하세요. timeScale이 0일 때도 올바르게 동작해야 합니다.

<details><summary>힌트·해설</summary>

`Dictionary<SfxData, float> lastPlayedTime`을 두고 `Time.unscaledTime - last < data.minInterval`이면 반환합니다. `Time.time`을 쓰면 timeScale 0에서 시간이 멈춰 UI 효과음이 영영 재생되지 않을 수 있습니다. 같은 프레임 검사는 이 검사로 대체될 수 있지만, `minInterval = 0`인 소리를 위해 남겨둘 가치가 있습니다.

</details>

3. ★★★ BGM에 "긴장도" 개념을 추가하세요. 적 수가 300을 넘으면 드럼 레이어가 서서히 들어오고, 200 아래로 떨어지면 빠집니다. 두 레이어는 박자가 어긋나면 안 됩니다.

<details><summary>힌트·해설</summary>

같은 길이의 두 클립(기본, 드럼)을 AudioSource 두 개에 걸고, 시작 시각을 맞추기 위해 `AudioSource.PlayScheduled(AudioSettings.dspTime + 0.1)`로 동시에 예약 재생합니다. 긴장도에 따라 드럼 소스의 `volume`만 `Mathf.MoveTowards`로 조절합니다. 300/200처럼 경계를 둘로 나누는 것(히스테리시스)은 경계 근처에서 레이어가 깜빡이는 것을 막습니다. 더 나아가 AudioMixer Snapshot(`TransitionTo`)으로 전환하는 방식과 비교해보세요.

</details>

## 셀프 체크

1. `ObjectPool<T>`의 `defaultCapacity`와 `maxSize`가 각각 무엇을 의미하고, 무엇을 의미하지 **않는지** 설명해보세요.

<details><summary>모범 답안</summary>

`defaultCapacity`는 보관용 내부 컬렉션의 초기 용량일 뿐, 오브젝트를 미리 만들지 않습니다. 미리 만들려면 Get/Release로 프리웜해야 합니다. `maxSize`는 풀이 **보관**할 최대 개수로, 이를 넘어 Release된 오브젝트는 `actionOnDestroy`로 버려집니다. 동시에 사용 중인 개수를 제한하지는 않으므로 적 수 상한은 스포너가 `CountActive`로 직접 관리해야 합니다.

</details>

2. 풀링된 오브젝트의 초기화를 `Start`에 두면 어떤 문제가 생기고, `OnEnable`과 `Init(...)`은 각각 무엇을 담당해야 하나요?

<details><summary>모범 답안</summary>

`Start`는 오브젝트 생애에 한 번만 불려서, 두 번째 재사용부터는 이전 생의 상태(체력 0, 페이드된 알파, 속도)가 그대로 남습니다. `OnEnable`은 활성화될 때마다 호출되므로 외부 정보 없이 정할 수 있는 리셋(타이머, 알파, 플래그, 이벤트 구독)을 맡고, `Init`은 Get 직후 호출해 데미지·방향·데이터처럼 외부에서 주는 값을 설정합니다. 해제·구독 취소는 `OnDisable`에 둡니다.

</details>

3. 이중 반환이 일어나는 구체적인 상황 하나와, 이를 막는 두 겹의 방어를 설명해보세요.

<details><summary>모범 답안</summary>

투사체가 같은 물리 스텝에서 적 두 마리와 겹치면 `OnTriggerEnter2D`가 두 번 호출되어 Release가 두 번 일어날 수 있습니다. 첫째 방어는 오브젝트 내부 `isSpawned` 플래그로 첫 번째 종료만 통과시키는 것이고, 둘째는 개발 중 `collectionCheck`를 켜서 놓친 경우 예외로 즉시 드러나게 하는 것입니다. 체크를 끈 빌드에서 이중 반환이 일어나면 같은 객체가 두 번 꺼내져 두 곳에서 동시에 쓰이는 찾기 어려운 버그가 됩니다.

</details>

4. 볼륨 슬라이더 값 `v`를 `Mathf.Log10(v) * 20`으로 변환하는 이유와, `v = 0` 처리가 필요한 이유를 설명해보세요.

<details><summary>모범 답안</summary>

AudioMixer의 볼륨은 데시벨 단위이고 사람의 음량 지각이 로그에 가깝기 때문에, 선형 0~1 값을 데시벨로 바꿔야 슬라이더 위치와 체감 크기가 비례합니다. `20 × log10(v)`는 진폭 비율을 데시벨로 바꾸는 식이라 v=0.5가 약 -6dB입니다. `log10(0)`은 음의 무한대라 믹서에 넣을 수 없으므로 0.0001로 하한을 두어 -80dB(사실상 무음)로 만듭니다.

</details>

## 핵심 요약

- `Instantiate`/`Destroy`는 네이티브 할당·컴포넌트 초기화·물리 등록·GC 쓰레기를 만들기 때문에, 자주 생기고 사라지는 것은 풀링합니다.
- `ObjectPool<T>`의 `defaultCapacity`는 프리웜이 아니고, `maxSize`는 보관 상한일 뿐 동시 사용 상한이 아닙니다.
- 모든 종료 경로를 `Despawn()` 하나로 모으고 `isSpawned` 플래그 + 개발 중 `collectionCheck`로 이중 반환을 막습니다.
- 재사용 리셋은 `OnEnable`(자기 상태), `Init`(외부 값), `OnDisable`(정리)로 나누고, 위치를 옮긴 뒤 활성화합니다.
- 짧은 SFX는 Decompress On Load + ADPCM, BGM은 Streaming + Vorbis가 기본입니다.
- 볼륨은 AudioMixer 노출 파라미터에 `Log10(max(v, 0.0001)) * 20`으로 넣고, `Start` 이후에 적용합니다.
- `AudioManager`는 소스 풀, 소리별 동시 재생 제한, 같은 프레임 중복 방지, 피치 랜덤, unscaled 크로스페이드를 제공합니다.

## 더 읽을거리

- Unity Scripting API — ObjectPool<T0>: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity Manual — Audio Clip 임포트 설정: https://docs.unity3d.com/Manual/class-AudioClip.html
- Unity Manual — Audio Mixer: https://docs.unity3d.com/Manual/AudioMixer.html
- Unity Scripting API — AudioSource.PlayScheduled: https://docs.unity3d.com/ScriptReference/AudioSource.PlayScheduled.html
- Unity 블로그 — "Introducing the Unity object pooling API" (2021, 제목으로 검색)
