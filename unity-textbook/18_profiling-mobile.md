# 18. 프로파일링과 모바일 최적화

> **이 장에서 배울 것**
> - 프레임 예산(16.6ms/33.3ms)과 모바일 발열 스로틀링을 근거로 목표 성능을 정할 수 있다
> - Profiler의 CPU Hierarchy/Timeline, Self와 Total, Deep Profile 비용을 구분해 병목 함수를 찾는다
> - 실기기(Android/iOS)에 Development Build로 연결해 측정하고, `ProfilerMarker`/`ProfilerRecorder`로 구간을 계측한다
> - Memory Profiler·Frame Debugger·Profile Analyzer로 메모리·드로우 콜·전후 비교를 수행한다
> - 적 1000마리 스트레스 씬에서 병목 3개를 찾아 고치고, 텍스처·오디오·적응형 품질로 저사양 기기 대응을 구현한다
>
> **선수 장**: 02, 05, 12, 13 · **예상 시간**: 5~6시간(실기기 준비 포함) · **코인 러시 진행**: 적 1000마리에서도 목표 프레임을 지키고, 저사양 폰에서는 자동으로 품질을 낮추는 코인 러시. 성능 측정 기록표.

## 왜 필요한가

에디터에서 적 500마리가 60fps로 잘 돌던 코인 러시를 3~4년 된 보급형 안드로이드 폰에 설치했습니다.

- 시작 직후엔 45fps, 5분쯤 적이 쌓이자 25fps로 떨어집니다.
- 10분 판이 끝날 무렵 폰이 뜨거워지고, 적이 줄었는데도 프레임이 회복되지 않습니다.
- 가끔 0.1초 정도 "툭" 멈춥니다.

"느리다"는 증상만으로는 아무것도 고칠 수 없습니다. 원인은 스크립트일 수도, 물리일 수도, GC일 수도, GPU 오버드로우일 수도 있습니다. 추측으로 코드를 고치면 시간을 쓰고도 빨라지지 않거나, 오히려 코드만 복잡해집니다. 이 장의 원칙은 하나입니다. **측정 → 가장 큰 원인 하나 수정 → 다시 측정.**

## 개념

### 프레임 예산

| 목표 | 프레임당 예산 | 코인 러시에서 |
|---|---|---|
| 60fps | 16.67ms | PC, 중급 이상 폰 |
| 30fps | 33.33ms | 저사양 폰 최소선 |
| 120fps | 8.33ms | 고주사율 기기(선택) |

프레임 시간은 **CPU(스크립트·물리·애니메이션·렌더 명령 준비) + GPU(실제 그리기)** 중 느린 쪽이 결정합니다. fps 평균보다 **프레임 시간의 최댓값·상위 1%(스파이크)**가 체감에 더 중요합니다. 평균 60fps여도 1초에 한 번 100ms 프레임이 있으면 "끊긴다"고 느낍니다.

### 모바일은 예산을 다 쓰면 안 된다 — 발열과 스로틀링

모바일 SoC는 온도가 오르면 스스로 CPU/GPU 클럭을 낮춥니다(thermal throttling). 처음 2분은 16ms 안에 들어와도, 칩이 뜨거워지면 같은 작업이 22ms가 됩니다.

```
프레임 시간(ms)
33 |                                      ....''''''  ← 스로틀링 후
   |                            ....''''
16 |- - - - - - - - - - ....''''- - - - - - - - - - -  60fps 예산선
   |  '''''''''''''''''                              ← 처음엔 여유 있어 보임
   +-------------------------------------------------- 시간(분)
   0         3         6         9
```

그래서 모바일에서는 **예산의 약 65~70%만** 쓰는 것을 목표로 잡는 경우가 많습니다(60fps면 11ms 전후). 그리고 반드시 **10~30분 연속 플레이**로 측정합니다. 짧은 측정은 발열을 보여주지 않습니다.

### Profiler — 어디를 볼 것인가

Window → Analysis → Profiler (Ctrl/Cmd+7).

| 모듈/뷰 | 보는 것 |
|---|---|
| CPU Usage → **Hierarchy** | 함수 호출 트리별 시간. 열: Total, **Self**, Calls, **GC Alloc**, Time ms, Self ms |
| CPU Usage → **Timeline** | 스레드(Main, Render, Job Worker)별 시간 막대. 무엇이 무엇을 기다리는지 |
| Rendering | 배치 수, SetPass 콜, 드로우 콜, 삼각형 수 |
| Memory | 총 사용량, 텍스처·메시·오디오 메모리, GC 힙 |
| Physics 2D | 바디 수, 접촉 수, 시뮬레이션 시간 |

**Self vs Total**: `Total`은 그 함수와 **그 함수가 부른 모든 것**의 시간, `Self`는 **자기 자신 코드만**의 시간입니다.

```
PlayerLoop                    Total 14.0ms  Self 0.1ms
 └ Update.ScriptRunBehaviourUpdate  Total  9.0ms  Self 0.2ms
    └ BehaviourUpdate               Total  8.8ms  Self 0.3ms
       └ Enemy.Update() [×1000]     Total  8.5ms  Self 6.0ms  ← 자기 코드가 무거움
          └ GameObject.Find...      Total  2.5ms  Self 2.5ms
```

순서: Hierarchy를 **Total로 정렬해 큰 줄기를 따라 내려가고**, Self가 큰 곳에서 멈춥니다. `Calls` 열이 1000이면 "한 번은 가볍지만 많이 불린다"는 신호입니다.

**Deep Profile**은 모든 C# 메서드 호출을 계측합니다. 편하지만 계측 자체가 무거워 시간이 몇 배 부풀고, 작은 메서드가 많은 코드일수록 왜곡이 큽니다. 기본은 끄고, 필요한 구간만 `ProfilerMarker`로 계측합니다.

**에디터 측정의 한계**: Play Mode 프로파일링에는 `EditorLoop`, Inspector 갱신 등이 섞이고 PC 성능이라 모바일과 다릅니다. 에디터는 "무엇이 상대적으로 큰가"를 찾는 용도이고, **숫자는 실기기에서** 확인합니다.

### 실기기 프로파일링

1. File → Build Profiles → 플랫폼 선택 → **Development Build** 체크, **Autoconnect Profiler** 체크(선택: Deep Profiling Support는 끔).
2. **Android(USB)**: 폰의 개발자 옵션 → USB 디버깅 켬 → USB 연결 → Build And Run. 앱이 켜지면 Profiler 창 상단의 대상 드롭다운에 기기가 나타납니다. 자동 연결이 안 되면 터미널에서 포트를 포워딩하고 `127.0.0.1`로 직접 연결합니다.
   ```
   adb devices
   adb forward tcp:34999 localabstract:Unity-com.yourname.coinrush
   ```
   (`com.yourname.coinrush` 자리에 Player Settings의 패키지 이름)
3. **iOS**: Development Build로 Xcode 프로젝트를 만들고 Xcode에서 기기에 실행합니다. 같은 Wi-Fi 네트워크나 USB로 연결된 기기가 Profiler 대상 목록에 나타납니다. 안 보이면 방화벽과 기기의 로컬 네트워크 권한을 확인합니다.
4. 측정 시 **충전기를 빼고**(충전 중엔 발열 특성이 다름), 화면 밝기·저전력 모드를 일정하게 둡니다.

Development Build는 릴리스보다 약간 느립니다. 절대 수치의 최종 확인은 개발 빌드가 아닌 빌드에서 6단계의 인게임 표시기로 합니다.

### ProfilerMarker와 ProfilerRecorder

`ProfilerMarker`는 내 코드 구간에 이름을 붙여 Profiler에 표시합니다. 릴리스 빌드에서는 비용이 거의 없도록 설계되어 있어 코드에 남겨둬도 됩니다.

```csharp
using Unity.Profiling;

static readonly ProfilerMarker s_FindTarget = new ProfilerMarker("Weapon.FindTarget");

void Fire()
{
    using (s_FindTarget.Auto())   // 이 블록이 Hierarchy에 "Weapon.FindTarget"으로 표시
    {
        // ...
    }
}
```

`ProfilerRecorder`는 반대로 **게임 안에서** 카운터 값을 읽습니다. 실기기 화면에 프레임 시간·GC 할당을 띄울 때 씁니다(6단계에서 구현).

| 카테고리 / 이름 | 값 | 비고 |
|---|---|---|
| `ProfilerCategory.Internal`, `"Main Thread"` | 메인 스레드 시간(나노초) | |
| `ProfilerCategory.Memory`, `"GC Allocated In Frame"` | 이번 프레임 GC 할당(바이트) | |
| `ProfilerCategory.Render`, `"Draw Calls Count"` | 드로우 콜 수 | 일부 렌더 카운터는 개발 빌드에서만 유효할 수 있음 |
| `ProfilerCategory.Memory`, `"Total Used Memory"` | 사용 메모리 | |

### 그 밖의 도구

| 도구 | 설치/위치 | 언제 |
|---|---|---|
| **Memory Profiler** | 패키지 `com.unity.memoryprofiler`, Window → Analysis → Memory Profiler | 스냅샷을 찍어 무엇이 메모리를 차지하는지, 스냅샷 **두 개를 비교**해 늘어난 것(누수)을 찾음. 같은 텍스처가 두 번 로드된 중복도 보임 |
| **Frame Debugger** | Window → Analysis → Frame Debugger | 한 프레임의 드로우 콜을 하나씩 재생. 각 콜의 "배칭되지 않은 이유" 표시 |
| **Profile Analyzer** | 패키지 `com.unity.performance.profile-analyzer` | 수백 프레임을 모아 마커별 중앙값·최댓값. **Compare** 모드로 수정 전/후 데이터 비교 |
| **Rendering Debugger** | Window → Analysis → Rendering Debugger (URP) | 오버드로우 시각화 등 렌더링 디버그 모드(항목은 URP 버전에 따라 다름) |

메모리 누수 찾는 순서: 판 시작 직후 스냅샷 A → 한 판 끝내고 타이틀로 돌아와 스냅샷 B → 두 판 더 하고 스냅샷 C. **B와 C를 비교**해 계속 늘어나는 객체가 누수 후보입니다(19장의 Addressables `Release` 누락이 흔한 원인).

### 흔한 병목과 처방

| 증상(Profiler에서) | 흔한 원인 | 처방 |
|---|---|---|
| `BehaviourUpdate` 큼, `Calls` 수백~수천 | 적마다 `Update()` | 매니저 한 곳에서 리스트를 돌며 `Tick()` (Unity의 `Update` 호출은 C#→네이티브 경계 비용이 있음) |
| `Physics2D.Simulate` 큼, 접촉 수 많음 | 적끼리 충돌, 복잡한 콜라이더 | Layer Collision Matrix에서 Enemy↔Enemy 끔, Circle 콜라이더, 불필요한 Rigidbody 제거 |
| 주기적 스파이크 + `GC.Collect` | 매 프레임 할당(LINQ, 문자열, 람다 캡처, `GetComponents`) | 할당 0 코드(02장), 캐시, `NonAlloc`류/리스트 재사용 |
| `GC Alloc` 열에 `FindObjectsByType`, `GetComponent` | 매 프레임 검색 | 등록/해제 방식 레지스트리 |
| GPU 시간 큼, 반투명 파티클 많음 | **오버드로우**(같은 픽셀을 여러 번 칠함) | 파티클 수·크기 제한(16장 상한), 큰 반투명 스프라이트 줄이기 |
| 드로우 콜 많음 | 스프라이트가 서로 다른 텍스처/머티리얼 | Sprite Atlas, 같은 머티리얼 공유, 정렬 순서 정리 |
| 메모리 큼, 로딩 느림 | 원본 크기 텍스처(4096) | Max Size 줄이기, ASTC 압축 |
| 특정 효과에서 GPU 급증 | 무거운 셰이더(14·15장), 풀스크린 후처리 | 저사양 품질 단계에서 끄기 |
| UI 갱신 비용 큼 | Canvas 하나에 자주 바뀌는 요소와 정적 요소 혼합 | 동적/정적 Canvas 분리(11장) |

### targetFrameRate와 vSync

| 플랫폼 | 기본 동작 | 설정 |
|---|---|---|
| Android / iOS | `targetFrameRate`가 기본값(-1)이면 **30fps**로 동작. `vSyncCount`는 무시됨 | `Application.targetFrameRate = 60;` 명시 |
| PC (Standalone) | `QualitySettings.vSyncCount`가 1 이상이면 `targetFrameRate`는 무시되고 모니터 주사율에 맞춤 | vSync 켬(티어링 방지) 또는 끄고 `targetFrameRate` 지정 |

모바일에서 "왜 30fps에 고정되지?"의 답이 대부분 이것입니다. 반대로 배터리를 위해 메뉴 화면에서는 30으로 낮추는 것도 좋은 전략입니다.

### 텍스처·스프라이트·오디오 설정

| 설정 | 권장(2D 모바일) | 이유 |
|---|---|---|
| 텍스처 압축(Android/iOS) | **ASTC** — 캐릭터 6x6, UI/글자 4x4, 배경 8x8부터 시험 | 블록이 작을수록 고품질·대용량. Unity 6 Android 기본값도 ASTC 계열 |
| Max Size | 텍스처 **전체**에 적용. 단일 이미지는 화면 표시 크기에, 시트는 "프레임 표시 크기 ÷ 시트 안 프레임 크기" 비율로 (8단계) | 메모리는 크기의 제곱에 비례 |
| Generate Mip Maps | 2D 스프라이트·UI는 끔 | 원근 축소가 없으므로 33% 메모리 낭비 |
| Read/Write | 끔 | 켜면 CPU 메모리에 사본이 하나 더 |
| Sprite Atlas | 같은 화면에 함께 나오는 스프라이트끼리 묶음 | 드로우 콜 감소 |
| 픽셀 아트 | Filter Mode Point, Compression은 품질 확인 후 결정 | 압축 블록 노이즈가 눈에 띌 수 있음 |

| 오디오 Load Type | 쓰는 곳 | 특징 |
|---|---|---|
| Decompress On Load | 짧고 자주 나는 SFX(타격, 코인) | 메모리 크지만 재생 시 CPU 적음 |
| Compressed In Memory | 중간 길이 SFX, 음성 | 메모리 적음, 재생 시 해제 비용 |
| Streaming | BGM | 디스크에서 읽으며 재생, 메모리 최소 |

모바일에서는 SFX에 **Force To Mono**, 샘플레이트 오버라이드(22050Hz 등)도 효과가 큽니다.

### 적응형 품질

기기 사양은 끝없이 다양합니다. 처음에 기기 이름으로 품질을 정하기보다 **실행 중 프레임 시간을 측정해 단계적으로 낮추는** 방식이 1인 개발자에게 현실적입니다.

```
매 N초: 평균 프레임 시간 측정
  목표보다 X% 이상 느림이 2회 연속 → 품질 1단계 하향 (렌더 스케일 ↓, 파티클 상한 ↓, 후처리 끔)
  목표보다 충분히 빠름이 오래 지속 → 1단계 상향 (자주 오르내리지 않게 조건을 더 엄격하게: 히스테리시스)
```

Android에서는 발열 상태를 알려주는 **Adaptive Performance** 패키지(`com.unity.adaptiveperformance`, 공급자 패키지 필요)도 있습니다. 기기·공급자 지원 범위가 달라지므로 도입 시 공식 문서를 확인하세요. 이 장에서는 어느 기기에서나 동작하는 프레임 시간 기반 방식을 구현합니다.

### 로딩 시간

첫 실행 시간은 이탈률과 직결됩니다. 흔한 원인과 처방: 첫 씬에 모든 매니저·데이터를 동기 로드(→ 09장 부트스트랩 + 비동기 로드), `Resources` 폴더의 대량 에셋(→ 19장 Addressables), 첫 전투에서 셰이더 컴파일로 끊김(→ 로딩 화면에서 해당 이펙트를 미리 한 번 재생하거나 셰이더 워밍업 기능 사용, Unity 버전별 API는 문서 확인), 거대한 오디오를 Decompress On Load로 설정(→ Streaming).

## 실습: 코인 러시에 적용하기

스크립트는 `Assets/_CoinRush/Scripts/Perf/`에 둡니다. 실습은 **스트레스 씬 → 측정 → 병목 3개 수정 → 적응형 품질 → 에셋 설정** 순서입니다.

### 1단계: 스트레스 씬 만들기

09장 구조에서는 어느 씬을 열고 Play해도 Bootstrap부터 시작하고, `GameFlow.GetInitialState()`는 요청된 씬 이름이 `Game`일 때만 게임으로 갑니다. 그래서 Stress 씬을 열고 Play해도 타이틀이 뜹니다. 씬을 만들고 **Bootstrap에서 Stress로 들어가는 길**을 함께 만듭니다.

1. 게임 씬을 복제해 `Assets/_CoinRush/Scenes/Stress.unity`로 저장합니다.
2. File → Build Profiles → Scene List에 `Stress`를 추가합니다(09장 `SceneLoader`는 이름으로 `LoadSceneAsync`하므로 목록에 없으면 로드 실패). 출시 빌드 전에는 체크를 끕니다.
3. Stress 씬에서 기존 `EnemySpawner`(12장) 오브젝트를 삭제하고, 04장 `GameStateMachine`의 **Gameplay Behaviours** 배열에서 그 칸도 지웁니다(빈 칸이 남으면 `SetGameplayActive`에서 `NullReferenceException`).
4. 빈 오브젝트 `StressSpawner`에 아래 스크립트를 붙이고 **Enemy Prefab**(적 프리팹), **Enemy Data**(03장 적 데이터 에셋 하나), **Pools**(씬의 `Pools` 오브젝트, 12장 `GameplayPools`), **Player**를 연결합니다.
5. 플레이어는 무적으로 둡니다(Health의 최대 체력을 크게).
6. 09장 `GameFlow`에 Stress 진입 경로를 추가합니다. 상수 하나와 필드 하나를 추가하고 `GetInitialState`를 교체합니다.

```csharp
// 09장 GameFlow — 상수·필드 추가
public const string StressScene = "Stress";
[SerializeField] private bool startInStressScene;   // 실기기 개발 빌드 측정용 (출시 전 끔)

// 09장 GameFlow.GetInitialState — 메서드 교체
private IGameState GetInitialState()
{
#if UNITY_EDITOR
    // 에디터에서 Game/Stress 씬을 열고 Play했다면 그 씬으로 바로 (09장 6단계)
    string requested = UnityEditor.SessionState.GetString(BootstrapKeys.PlayFromScene, string.Empty);
    UnityEditor.SessionState.EraseString(BootstrapKeys.PlayFromScene);
    if (requested == GameScene) return gameState;
    if (requested == StressScene) return new SceneState(StressScene, loader);   // 18장
#endif
    // 실기기 측정: Development Build에서만, Bootstrap의 GameFlow에서 체크했을 때
    if (Debug.isDebugBuild && startInStressScene) return new SceneState(StressScene, loader);
    return titleState;
}
```

이제 Stress 씬을 열고 Play하면 Bootstrap → Stress로 들어갑니다. Stress 씬은 게임 씬 복제본이라 04장 `GameStateMachine`이 Title 상태로 시작하므로, 패널의 시작 버튼을 눌러 Playing으로 넘깁니다(적은 상태와 무관하게 생성됩니다). 실기기에서는 Bootstrap 씬의 `GameFlow`에서 **Start In Stress Scene**을 켜고 Development Build로 빌드합니다.

```csharp
// Assets/_CoinRush/Scripts/Perf/StressSpawner.cs
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Pool;

public class StressSpawner : MonoBehaviour
{
    [SerializeField] Enemy enemyPrefab;
    [SerializeField] EnemyData enemyData;    // 03장 — Init에 필요 (체력·속도·코인)
    [SerializeField] GameplayPools pools;    // 12장 — 적이 죽을 때 코인을 꺼냄
    [SerializeField] Transform player;
    [SerializeField] int count = 1000;
    [SerializeField] float radius = 12f;
    [SerializeField] int seed = 12345;      // 매번 같은 배치 → 전후 비교가 공정

    ObjectPool<Enemy> pool;
    int spawnedTotal;

    void Start()
    {
        // 12장 PoolUtil: 죽은 적이 Pool.Release로 돌아올 곳이 있어야 측정 중 사망도 안전
        pool = PoolUtil.Create(enemyPrefab, transform, prewarm: count, maxSize: 4000);
        Spawn(count);
    }

    void Update()
    {
        // 측정 중 수를 바꿔보기 위한 단축키
        if (Keyboard.current != null && Keyboard.current.equalsKey.wasPressedThisFrame) Spawn(250);
    }

    void Spawn(int n)
    {
        var rng = new System.Random(seed + spawnedTotal);
        for (int i = 0; i < n; i++)
        {
            double angle = rng.NextDouble() * Mathf.PI * 2;
            float r = radius * Mathf.Sqrt((float)rng.NextDouble()) + 3f;
            Vector3 pos = player.position + new Vector3(Mathf.Cos((float)angle) * r, Mathf.Sin((float)angle) * r, 0f);
            Enemy enemy = pool.Spawn(pos);            // 위치 이동 후 활성화 (12장)
            enemy.Init(enemyData, player, pools);     // 12장 스포너와 같은 초기화 — 빠뜨리면 data가 null
        }
        spawnedTotal += n;
    }
}
```

12장 풀을 그대로 쓰는 이유는 `Enemy`가 `Init`으로만 데이터·대상·풀을 받고, 사망하면 `Pool.Release`로 돌아가기 때문입니다. `Instantiate`만 하면 `data`가 비어 있고 죽을 때 `Pool`이 null이라 예외가 납니다. 생성은 **시작 시 한 번**(프리웜 포함)이므로, 측정 구간에 섞이지 않게 시작 후 5초가 지난 뒤부터 기록합니다.

### 2단계: 측정 프로토콜과 기록표

같은 조건에서 재지 않으면 전후 비교가 의미 없습니다.

1. 기기와 빌드 종류(에디터/개발 빌드) 고정, 적 1000마리, 시드 고정.
2. 시작 5초 후 Profiler 창의 Record를 켜고 **600프레임(약 10초)** 기록.
3. Profiler 창 메뉴의 Save로 `.data` 파일 저장(`before_1.data`).
4. Profile Analyzer(Window → Analysis → Profile Analyzer) → Pull Data 또는 Load → 마커별 **Median / Max** 기록.
5. 수정 후 같은 절차로 `after_1.data` → Compare 탭에서 두 파일 비교.

아래 표를 복사해 직접 채우세요. 숫자는 **예시**이며 기기마다 크게 다릅니다.

| 단계 | 측정 환경 | 메인 스레드 중앙값 | 최댓값 | GC Alloc/프레임 | 주요 마커 |
|---|---|---|---|---|---|
| 0. 기준선 | 에디터, 적 1000 | 예: 21.4ms | 예: 58ms | 예: 96KB | `Enemy.Update` 9.8ms, `Physics2D` 6.1ms |
| 1. 매니저 틱 | 〃 | | | | |
| 2. 물리 레이어 | 〃 | | | | |
| 3. GC 제거 | 〃 | | | | |
| 최종 | 실기기(기종 기입) | | | | |

### 3단계: 병목 1 — Update 1000개를 매니저 틱으로

기준선에서 흔히 보이는 05장식 `Enemy`는 이런 모양입니다.

```csharp
// 수정 전(흔한 실수 예시): 적마다 Update/FixedUpdate + 매 프레임 검색
void Update()
{
    var player = FindFirstObjectByType<PlayerMover>();   // 매 프레임 씬 검색 ×1000
    direction = (player.transform.position - transform.position).normalized;
}
```

12장 `Enemy`는 검색은 하지 않지만 적마다 `FixedUpdate`가 돕니다. 적의 `Update`/`FixedUpdate`를 없애고 매니저가 한 번에 돌게 바꿉니다.

```csharp
// Assets/_CoinRush/Scripts/Perf/EnemyManager.cs
using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;

[DefaultExecutionOrder(-10)]
public class EnemyManager : MonoBehaviour
{
    static readonly ProfilerMarker s_Tick = new ProfilerMarker("EnemyManager.Tick");
    static readonly ProfilerMarker s_FixedTick = new ProfilerMarker("EnemyManager.FixedTick");

    public static EnemyManager Instance { get; private set; }

    [SerializeField] Transform player;

    readonly List<Enemy> enemies = new List<Enemy>(1024);

    public Transform Player => player;
    public IReadOnlyList<Enemy> Enemies => enemies;

    void Awake() => Instance = this;
    void OnDestroy() { if (Instance == this) Instance = null; }

    public void Register(Enemy e) => enemies.Add(e);

    public void Unregister(Enemy e)
    {
        // 순서가 중요하지 않으므로 마지막 원소와 바꿔 O(1) 제거
        int i = enemies.IndexOf(e);
        if (i < 0) return;
        int last = enemies.Count - 1;
        enemies[i] = enemies[last];
        enemies.RemoveAt(last);
    }

    void Update()
    {
        using (s_Tick.Auto())
        {
            if (player == null) return;
            float dt = Time.deltaTime;
            Vector2 target = player.position;
            for (int i = 0; i < enemies.Count; i++) enemies[i].Tick(target, dt);
        }
    }

    void FixedUpdate()
    {
        using (s_FixedTick.Auto())
        {
            for (int i = 0; i < enemies.Count; i++) enemies[i].FixedTick();
        }
    }
}
```

`Unregister`의 `IndexOf`는 O(n)입니다. 적이 초당 수십 마리씩 죽는 정도면 문제없지만, 수천 단위라면 `Enemy`가 자기 인덱스를 저장하는 방식으로 바꿉니다(연습 문제 2).

`Enemy`를 수정합니다. 기준은 12장 파일에 **14장(디졸브: `bodyCollider`, `isSpawned` 검사)과 16장(넉백: `knockback`, 데미지 팝업, 코인 자석)** 수정을 적용한 상태입니다. `OnEnable`·`OnDisable`을 교체하고, `FixedUpdate`를 삭제한 뒤 프로퍼티 하나와 `Tick`/`FixedTick`을 추가합니다. 나머지(`Awake`, `Init`, `OnHealthChanged`, `OnDied`)는 그대로입니다.

```csharp
// Enemy.cs (12·14·16장) — 필드·프로퍼티 추가
private Vector2 moveDir;
public bool IsAlive => isSpawned;   // 디졸브 중(사망 연출)이면 false — 조준·이동에서 제외

// OnEnable 교체 — 14장의 콜라이더 복구를 유지하고 매니저에 등록
private void OnEnable()
{
    isSpawned = true;
    bodyCollider.enabled = true;                      // 14장: 지난 생의 사망에서 꺼진 콜라이더 복구
    moveDir = Vector2.zero;
    health.Died += OnDied;
    health.Changed += OnHealthChanged;
    EnemyManager.Instance.Register(this);             // 18장
}

// OnDisable 교체
private void OnDisable()
{
    isSpawned = false;
    health.Died -= OnDied;
    health.Changed -= OnHealthChanged;
    if (EnemyManager.Instance != null) EnemyManager.Instance.Unregister(this);   // 씬 종료 순서 대비
}

// FixedUpdate는 삭제하고 아래 두 메서드 추가
public void Tick(Vector2 playerPos, float dt)
{
    if (!isSpawned) return;                           // 14장: 디졸브 중에는 방향 계산 안 함
    Vector2 to = playerPos - body.position;
    float sq = to.sqrMagnitude;
    moveDir = sq > 0.0001f ? to / Mathf.Sqrt(sq) : Vector2.zero;
    // 스프라이트 좌우 반전 같은 가벼운 시각 갱신도 여기서
}

public void FixedTick()
{
    if (!isSpawned || data == null) return;              // 14장: 사망 연출 중 정지 / Init 전 방어
    if (knockback != null && knockback.IsActive) return; // 16장: 넉백 속도를 덮어쓰지 않음
    body.linearVelocity = moveDir * data.moveSpeed;
}
```

에디터 작업:

1. **Game 씬과 Stress 씬 모두**에 빈 오브젝트 `EnemyManager`를 만들고 `EnemyManager` 컴포넌트를 붙인 뒤 **Player**에 플레이어를 연결합니다. 12장 `EnemySpawner`와 `StressSpawner`의 프리웜이 적을 만드는 순간 `OnEnable`이 `EnemyManager.Instance`를 쓰므로, 매니저가 없는 씬에서는 `NullReferenceException`이 납니다.

`EnemyManager`는 `DefaultExecutionOrder(-10)`으로 적보다 먼저 `Awake`가 끝나야 `OnEnable` 등록이 안전합니다. 적이 씬에 미리 배치돼 있으면 `EnemyManager` 오브젝트가 Hierarchy에서 적보다 위에 있어도 `Awake` 순서는 보장되지 않으므로, 실행 순서 속성으로 보장합니다.

측정 후 표 1행을 채웁니다. Profiler Hierarchy에서 `BehaviourUpdate` 아래 `Enemy.Update`가 사라지고 `EnemyManager.Tick` 하나만 보여야 합니다.

### 4단계: 병목 2 — Physics2D

Profiler에서 **Physics 2D** 모듈을 켜고 접촉(Contacts) 수를 봅니다. 적 1000마리가 서로 밀어내면 접촉 수가 수천이 됩니다.

1. Project Settings → Tags and Layers에서 레이어 `Enemy`, `Player`, `PlayerProjectile`, `Pickup`을 만들고 프리팹에 지정합니다.
2. Project Settings → **Physics 2D** → Layer Collision Matrix에서 필요한 조합만 남깁니다.

| | Player | Enemy | PlayerProjectile | Pickup |
|---|---|---|---|---|
| Player | | ✔ | | ✔ |
| Enemy | ✔ | **끔** | ✔ | |
| PlayerProjectile | | ✔ | | |
| Pickup | ✔ | | | |

3. 적 콜라이더는 `CircleCollider2D`(Polygon보다 훨씬 가벼움). 투사체는 Rigidbody2D **Kinematic** + 트리거로, 16장 넉백이 필요한 적만 Dynamic으로 둡니다.
4. Physics 2D 설정에 **Auto Sync Transforms** 항목이 있다면 꺼져 있는지 확인합니다(켜져 있으면 Transform 변경마다 물리 동기화 비용. 버전에 따라 항목 위치·존재가 다를 수 있음).

적끼리 완전히 겹치는 것이 보기 싫다면, 물리 충돌 대신 `EnemyManager.Tick`에서 가까운 이웃만 약하게 밀어내는 분리(separation) 벡터를 계산하는 방법이 훨씬 싸게 먹힙니다(연습 문제 3).

범위 공격처럼 "반경 안의 적 찾기"가 필요하면 할당 없는 쿼리를 씁니다.

```csharp
// 무기 코드 안: 결과 배열을 재사용하는 OverlapCircle
static readonly Collider2D[] s_Hits = new Collider2D[64];
[SerializeField] LayerMask enemyMask;

int CollectEnemies(Vector2 center, float radius)
{
    var filter = new ContactFilter2D();
    filter.SetLayerMask(enemyMask);
    filter.useTriggers = true;
    return Physics2D.OverlapCircle(center, radius, filter, s_Hits); // 채운 개수 반환
}
```

### 5단계: 병목 3 — 매 프레임 GC 할당

Hierarchy를 **GC Alloc 열로 정렬**합니다. 자주 나오는 범인은 자동 조준 무기의 "가장 가까운 적 찾기"입니다.

```csharp
// 수정 전: LINQ — 정렬용 버퍼, 람다 캡처(closure), 열거자 할당
var nearest = enemies.OrderBy(e => (e.transform.position - pos).sqrMagnitude).FirstOrDefault();
```

```csharp
// Assets/_CoinRush/Scripts/Perf/TargetFinder.cs
using Unity.Profiling;
using UnityEngine;

public static class TargetFinder
{
    static readonly ProfilerMarker s_Marker = new ProfilerMarker("TargetFinder.Nearest");

    // 할당 0: 인덱스 for 루프 + 제곱 거리 비교
    public static Enemy Nearest(Vector2 from, float maxRange)
    {
        using (s_Marker.Auto())
        {
            var list = EnemyManager.Instance.Enemies;
            Enemy best = null;
            float bestSq = maxRange * maxRange;
            for (int i = 0; i < list.Count; i++)
            {
                if (!list[i].IsAlive) continue;          // 디졸브 중인 적은 조준하지 않음
                float sq = ((Vector2)list[i].transform.position - from).sqrMagnitude;
                if (sq < bestSq) { bestSq = sq; best = list[i]; }
            }
            return best;
        }
    }
}
```

`IReadOnlyList<T>`를 `foreach`로 돌면 인터페이스를 통한 열거자가 박싱되어 할당될 수 있으므로 인덱스 `for`를 씁니다. 그 밖에 확인할 것: HUD에서 매 프레임 `$"{coins}"` 문자열 생성(→ 값이 바뀔 때만, 또는 TMP `SetText`), `GetComponent`를 매 프레임 호출(→ `Awake`에서 캐시), 코루틴 `yield return new WaitForSeconds(x)`를 반복 생성(→ 캐시하거나 Awaitable).

목표: 전투 중 `GC Alloc` 합계가 **0B**인 프레임이 대부분이어야 합니다. 표 3행을 채웁니다.

### 6단계: 인게임 성능 표시기

실기기에서 Profiler 없이도 숫자를 보기 위한 오버레이입니다.

```csharp
// Assets/_CoinRush/Scripts/Perf/PerfOverlay.cs
using TMPro;
using Unity.Profiling;
using UnityEngine;

public class PerfOverlay : MonoBehaviour
{
    [SerializeField] TextMeshProUGUI label;
    [SerializeField] float refreshInterval = 0.5f;

    ProfilerRecorder mainThread, gcAlloc, drawCalls;
    float timer;
    int frames;
    float worstMs;
    long gcSumBytes, gcMaxBytes;   // 구간 합계·한 프레임 최댓값 (마지막 프레임만 보면 스파이크를 놓침)

    void OnEnable()
    {
        mainThread = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 15);
        gcAlloc = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame");
        drawCalls = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count");
    }

    void OnDisable()
    {
        mainThread.Dispose();
        gcAlloc.Dispose();
        drawCalls.Dispose();
    }

    void Update()
    {
        float ms = Time.unscaledDeltaTime * 1000f;
        if (ms > worstMs) worstMs = ms;
        frames++;
        timer += Time.unscaledDeltaTime;

        // GC는 매 프레임 읽어 누적 (LastValue = 직전에 끝난 프레임의 바이트 수)
        if (gcAlloc.Valid)
        {
            long bytes = gcAlloc.LastValue;
            gcSumBytes += bytes;
            if (bytes > gcMaxBytes) gcMaxBytes = bytes;
        }

        if (timer < refreshInterval) return;

        float avgMs = timer * 1000f / frames;
        float mainMs = mainThread.Valid ? (float)(mainThread.LastValue * 1e-6) : -1f; // ns → ms
        float dc = drawCalls.Valid ? drawCalls.LastValue : -1f;

        // TMP의 숫자 SetText는 float 인수만 받으므로 형변환 ({0:1} = 소수 1자리)
        // 카운터를 쓸 수 없는 환경(릴리스 빌드 등)은 0이 아니라 N/A로 구분해 보여줌
        if (gcAlloc.Valid)
            label.SetText("frame {0:1}ms (worst {1:1})  dc {2:0}\nmain {3:1}ms  gc {4:0}B/interval (max {5:0}B)",
                avgMs, worstMs, dc, mainMs, gcSumBytes, gcMaxBytes);
        else
            label.SetText("frame {0:1}ms (worst {1:1})  dc {2:0}\nmain {3:1}ms  gc N/A",
                avgMs, worstMs, dc, mainMs);

        timer = 0f; frames = 0; worstMs = 0f;
        gcSumBytes = 0; gcMaxBytes = 0;
    }
}
```

Unity 6 매뉴얼의 프로파일러 카운터 표 기준으로 `GC Allocated In Frame`은 **릴리스 플레이어에서 사용할 수 없고**(에디터·Development Build 전용), 단위는 바이트입니다. 그래서 `Valid`가 아니면 `N/A`로 표시하고, 512B 같은 작은 할당이 KB 정수 나눗셈으로 0이 되지 않게 바이트로 보여줍니다. `-1`로 보이는 main/dc도 해당 카운터를 쓸 수 없다는 뜻입니다. 이 오버레이는 개발 빌드 측정용이므로 `#if DEVELOPMENT_BUILD || UNITY_EDITOR`로 감싸거나 설정 메뉴의 숨은 토글로 켭니다. TMP `SetText`의 숫자 오버로드는 인수 개수에 상한이 있으니(여기서는 6개) 더 늘리지 마세요.

### 7단계: 목표 프레임과 적응형 품질

Project Settings → Quality에서 품질 단계를 `Low`, `Medium`, `High` 세 개로 정리하고, 각 단계에 다른 URP 에셋(13장)을 지정합니다(Low: Render Scale 0.75, 후처리 끔 / High: 1.0, 후처리 켬). 그리고 코드로 조절할 "게임 쪽 품질"(파티클 상한 등)은 `QualityGovernor`가 이벤트로 알립니다.

```csharp
// Assets/_CoinRush/Scripts/Perf/QualityGovernor.cs
using System;
using UnityEngine;

public class QualityGovernor : MonoBehaviour
{
    public static event Action<int> LevelChanged;   // 0=Low … max=High

    [SerializeField] int targetFps = 60;
    [SerializeField] float sampleSeconds = 3f;
    [SerializeField] float downThreshold = 1.15f;   // 목표보다 15% 느리면
    [SerializeField] float upThreshold = 0.7f;      // 목표의 70% 이하 시간이면(충분히 빠르면)
    [SerializeField] int samplesToUpgrade = 5;      // 상향은 느리게 (히스테리시스)
    [SerializeField] float startDelay = 5f;         // 로딩 직후 스파이크 제외

    float accum;
    int frames;
    int slowStreak, fastStreak;
    float targetMs;

    const string SaveKey = "perf.qualityLevel";

    void Start()
    {
        Application.targetFrameRate = targetFps;   // 모바일 기본 30fps 해제
        QualitySettings.vSyncCount = 0;            // PC에서 targetFrameRate가 동작하도록
        targetMs = 1000f / targetFps;

        // 지난 실행에서 내려간 단계를 복원하고, 구독자에게 초기값을 알림
        int max = QualitySettings.names.Length - 1;
        int saved = Mathf.Clamp(PlayerPrefs.GetInt(SaveKey, QualitySettings.GetQualityLevel()), 0, max);
        if (saved != QualitySettings.GetQualityLevel())
            QualitySettings.SetQualityLevel(saved, applyExpensiveChanges: false);
        LevelChanged?.Invoke(saved);
    }

    void Update()
    {
        if (Time.realtimeSinceStartup < startDelay || Time.timeScale == 0f) return; // 일시정지 제외
        accum += Time.unscaledDeltaTime;
        frames++;
        if (accum < sampleSeconds) return;

        float avgMs = accum * 1000f / frames;
        accum = 0f; frames = 0;

        if (avgMs > targetMs * downThreshold)
        {
            fastStreak = 0;
            if (++slowStreak >= 2) { Step(-1); slowStreak = 0; }
        }
        else if (avgMs < targetMs * upThreshold)
        {
            slowStreak = 0;
            if (++fastStreak >= samplesToUpgrade) { Step(+1); fastStreak = 0; }
        }
        else { slowStreak = 0; fastStreak = 0; }
    }

    void Step(int delta)
    {
        int max = QualitySettings.names.Length - 1;
        int next = Mathf.Clamp(QualitySettings.GetQualityLevel() + delta, 0, max);
        if (next == QualitySettings.GetQualityLevel()) return;
        QualitySettings.SetQualityLevel(next, applyExpensiveChanges: false);
        PlayerPrefs.SetInt(SaveKey, next);          // 다음 실행에 이어 씀
        PlayerPrefs.Save();
        LevelChanged?.Invoke(next);
        Debug.Log($"[QualityGovernor] quality → {QualitySettings.names[next]} (avg over target)");
    }
}
```

주의할 점이 두 가지 있습니다.

- `targetFrameRate = 60`인 기기에서 평균이 16.7ms 근처면 "충분히 빠른지" 알 수 없습니다(프레임 제한에 걸려서). 그래서 상향 조건은 거의 발동하지 않고, 이 스크립트는 사실상 **하향 전용 안전장치**로 동작합니다. 그것으로 충분합니다.
- `QualityGovernor`는 Bootstrap 씬(09장)의 `Managers` 아래에 둡니다. 게임 씬의 구독자는 나중에 생기므로, 구독자는 `LevelChanged`만 기다리지 말고 `OnEnable`에서 `QualitySettings.GetQualityLevel()`로 **현재 값을 먼저 적용**해야 합니다.
- 품질 단계는 PlayerPrefs에 저장해 다음 실행에 이어 씁니다(`Start`에서 복원).

게임 쪽 품질도 연결합니다. 16장 `FxPlayer`와 `DamagePopupSpawner`가 Low(0단계)에서 동시 개수 상한을 절반으로 줄이게 합니다. 두 파일 모두 **16장 파일 교체**입니다.

```csharp
// Assets/_CoinRush/Scripts/Feel/FxPlayer.cs  (16장 파일 교체 — 품질 단계별 동시 재생 상한)
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Pool;

public class FxPlayer : MonoBehaviour
{
    static FxPlayer instance;
    readonly Dictionary<PooledParticle, ObjectPool<PooledParticle>> pools = new();

    [SerializeField] int maxActivePerEffect = 48;   // High 기준. Low에서는 절반
    int activeLimit;

    void Awake() => instance = this;
    void OnDestroy() { if (instance == this) instance = null; }

    void OnEnable()
    {
        QualityGovernor.LevelChanged += ApplyQuality;
        ApplyQuality(QualitySettings.GetQualityLevel());   // 초기값 적용
    }

    void OnDisable() => QualityGovernor.LevelChanged -= ApplyQuality;

    void ApplyQuality(int level) => activeLimit = level == 0 ? maxActivePerEffect / 2 : maxActivePerEffect;

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
        if (pool.CountActive >= instance.activeLimit) return;   // 상한 초과분은 건너뜀
        var fx = pool.Get();
        fx.transform.position = position;
        var main = fx.Particles.main;
        if (tint.HasValue) main.startColor = tint.Value;
        fx.Particles.Clear(true);
        fx.Particles.Play(true);
    }
}
```

```csharp
// Assets/_CoinRush/Scripts/Feel/DamagePopupSpawner.cs  (16장 파일 교체)
using UnityEngine;
using UnityEngine.Pool;

public class DamagePopupSpawner : MonoBehaviour
{
    static DamagePopupSpawner instance;
    [SerializeField] DamagePopup prefab;
    [SerializeField] int maxActive = 40;   // High 기준. Low에서는 절반

    ObjectPool<DamagePopup> pool;
    int activeLimit;

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

    void OnEnable()
    {
        QualityGovernor.LevelChanged += ApplyQuality;
        ApplyQuality(QualitySettings.GetQualityLevel());
    }

    void OnDisable() => QualityGovernor.LevelChanged -= ApplyQuality;
    void OnDestroy() { if (instance == this) instance = null; }

    void ApplyQuality(int level) => activeLimit = level == 0 ? maxActive / 2 : maxActive;

    public static void Show(Vector3 position, int amount, bool isCritical)
    {
        if (instance == null || !FeelSettings.DamageNumbersEnabled) return;
        if (instance.pool.CountActive >= instance.activeLimit) return; // 화면 덮음 방지
        instance.pool.Get().Show(position, amount, isCritical);
    }
}
```

`QualityGovernor.LevelChanged`는 정적 이벤트라 씬이 바뀌어도 남으므로, 구독한 쪽이 `OnDisable`에서 반드시 해제해야 파괴된 오브젝트가 호출되지 않습니다. Inspector 연결은 16장 그대로입니다(Prefab 칸 유지).

### 8단계: 텍스처·오디오 일괄 점검

1. Project 창 검색창에 `t:Texture2D`로 모든 텍스처를 띄우고, Inspector 하단 **Android/iOS 탭 → Override**에서 Format을 ASTC(위 표 기준)로 지정합니다. 수백 장이면 20장의 `AssetPostprocessor`로 자동화합니다.
2. Max Size를 줄입니다. Max Size는 잘라낸 스프라이트 하나가 아니라 **원본 텍스처 파일 전체**에 적용된다는 점이 핵심입니다. 스프라이트 시트를 줄이면 시트 안의 모든 프레임이 같은 비율로 작아집니다.
   - **단일 이미지**(스프라이트 1장): 화면에서 보이는 최대 픽셀 크기 이상의 가장 작은 2의 거듭제곱으로.
   - **스프라이트 시트**(17장처럼 여러 프레임이 든 한 장): `필요한 Max Size ≈ 시트 크기 × (화면 표시 크기 ÷ 시트 안 한 프레임 크기)`. 예: 2048px 시트 안의 256px 프레임이 화면에 128px로 보이면 비율 0.5 → 1024. 128로 줄이면 프레임이 16px로 뭉개집니다.
   - **Sprite Atlas**: 원본 텍스처가 아니라 아틀라스 에셋의 Max Texture Size가 최종 크기를 정합니다. 원본은 위 기준으로 두고, 아틀라스 설정에서 내용이 잘리지 않는 크기를 고릅니다.
   - 줄인 뒤 Game 뷰를 실제 기기 해상도로 맞춰 흐려짐을 눈으로 확인합니다.
3. `Assets/_CoinRush/Art/Atlas/`에 Create → 2D → Sprite Atlas를 만들어 적 스프라이트 폴더를 넣습니다(Project Settings → Editor → Sprite Packer Mode가 Sprite Atlas V2 Enabled인지 확인).
4. `t:AudioClip`으로 오디오를 띄워, BGM은 Streaming, 짧은 SFX는 Decompress On Load + Force To Mono.
5. Memory Profiler로 스냅샷을 찍어 **Unity Objects → Texture2D**를 크기순 정렬, 예상보다 큰 텍스처가 없는지 확인합니다.

### 확인하기

- 에디터 Stress 씬에서 `Enemy.Update`가 Profiler에 없고 `EnemyManager.Tick` 하나로 보인다.
- Physics 2D 모듈의 접촉 수가 적 수와 비슷하거나 그 이하로 줄었다.
- 전투 중 GC Alloc 0B 프레임이 대부분이고, Timeline 뷰에서 `GC.Collect` 스파이크가 사라졌다.
- 측정 기록표 5행이 모두 채워졌다(실기기 1행 포함).
- 실기기에서 `PerfOverlay`가 보인다(Development Build에서는 gc 값이 바이트로, 릴리스 빌드에서는 `N/A`로).
- **병목 종류별로 따로 확인한다.** 품질 단계(Render Scale·후처리·파티클 상한)는 주로 GPU·렌더링 부담을 줄이므로, CPU가 병목일 때는 낮춰도 프레임이 거의 돌아오지 않습니다.
  - GPU 병목 재현: High 단계 URP 에셋의 Render Scale을 임시로 2.0으로 올리고 Stress 씬을 실기기에서 실행 → Profiler에서 CPU 메인 스레드는 여유가 있는데 프레임이 느림 → 몇 초 뒤 로그에 품질 하향이 찍히고 프레임이 회복된다. 확인 후 Render Scale을 원래대로.
  - CPU 병목 재현: `=` 키로 적을 3000마리까지 늘림 → `EnemyManager.Tick`·Physics2D가 커짐 → 품질이 내려가도 프레임이 거의 회복되지 않음을 기록표에 적는다. 이 경우의 처방은 품질 단계가 아니라 적 동시 수 상한(12장 `maxAlive`), 분리 계산 최적화(연습 문제 3), 물리 레이어 정리다.
- 앱을 껐다 켜면 마지막으로 내려간 품질 단계로 시작한다(PlayerPrefs 복원).
- 15분 연속 플레이 후에도 목표 프레임 근처를 유지한다(아래 체크리스트).

**저사양 기기 체크리스트** (출시 전 최저 사양 기기 1대로)

| 항목 | 기준 | 결과 |
|---|---|---|
| 콜드 스타트 → 타이틀 | 5초 이내 목표 | |
| 30분 연속 플레이 프레임 | 목표 fps의 90% 이상 유지 | |
| 30분 후 기기 표면 온도 | 손에 쥐기 불편하지 않음 | |
| 배터리 소모 | 30분에 10~15% 이내 목표 | |
| 메모리 | 판 3회 반복 후 증가 없음(Memory Profiler 비교) | |
| 최대 적 수 장면 | 입력 지연 체감 없음 | |
| 백그라운드 → 복귀 | 크래시·음소거 고장 없음 | |
| 저장 공간 | 설치 용량 목표치 이하(19장 빌드 리포트) | |

기준 수치는 장르·타깃에 따라 스스로 정하는 값입니다. 중요한 것은 **기준을 숫자로 적고 매 빌드 같은 방식으로 재는 것**입니다.

## 흔한 실수

1. **에디터에서 빠르니 됐다고 판단** → 에디터 PC와 모바일 SoC는 수 배 차이, 발열 없음. → 개발 빌드로 실기기에서, 10분 이상 측정.
2. **Deep Profile 수치를 그대로 믿음** → 계측 오버헤드로 작은 메서드가 과장됨. → Deep Profile은 호출 구조 파악용, 시간은 `ProfilerMarker`로.
3. **모바일에서 30fps 고정** → `Application.targetFrameRate` 미설정(모바일 기본 30). → 시작 시 60으로 명시.
4. **평균 fps만 봄** → 스파이크(GC, 로딩, 셰이더 컴파일)를 놓침. → 최댓값·Timeline 뷰·Profile Analyzer의 Max 확인.
5. **한 번에 여러 개를 고치고 측정** → 무엇이 효과였는지(또는 악화시켰는지) 모름. → 수정 하나 → 측정 하나, 기록표 유지.
6. **URP 에셋의 Render Scale을 코드로 바꿨더니 에디터 설정이 영구 변경** → 에셋 자체를 수정함. → 품질 단계별 URP 에셋을 두고 `SetQualityLevel`로 전환.

## 연습 문제

**1. ★☆☆ 마커 붙이기**
16장 `HitFeedback.Update`와 `DamagePopup.Update`에 `ProfilerMarker`를 붙이고, 적 1000마리에게 범위 공격을 했을 때 각각의 Self 시간을 기록하세요.

<details><summary>힌트·해설</summary>

`static readonly ProfilerMarker s_Marker = new ProfilerMarker("HitFeedback.Update");` 후 `using (s_Marker.Auto()) { ... }`. 인스턴스가 많아도 마커는 정적 하나로 공유되며, Hierarchy에서 Calls 수와 합산 시간이 보입니다. 16장에서 넣은 `animating` 조기 반환이 없다면 이 마커가 크게 보일 것입니다.

</details>

**2. ★★☆ O(1) Unregister**
`EnemyManager.Unregister`의 `IndexOf`(O(n))를 없애세요.

<details><summary>힌트·해설</summary>

`Enemy`에 `internal int managerIndex`를 두고, `Register` 시 `e.managerIndex = enemies.Count; enemies.Add(e);`. `Unregister` 시 `int i = e.managerIndex; var last = enemies[^1]; enemies[i] = last; last.managerIndex = i; enemies.RemoveAt(enemies.Count - 1); e.managerIndex = -1;`. 마지막 원소의 인덱스를 갱신하는 줄을 빠뜨리면 다음 제거 때 엉뚱한 적이 지워집니다.

</details>

**3. ★★☆ 물리 없는 분리(separation)**
Enemy↔Enemy 충돌을 끈 뒤 적들이 한 점에 뭉치는 문제를, 공간 격자(grid)를 써서 이웃 셀의 적만 밀어내는 방식으로 해결하세요.

<details><summary>힌트·해설</summary>

셀 크기 1.0의 `Dictionary<int, List<Enemy>>` 대신, 맵 크기가 고정이면 `List<Enemy>[]` 배열에 `cellIndex = x + y * width`로 담으면 해시 비용이 없습니다. 매 프레임 리스트를 `Clear()`하고 다시 채운 뒤(할당 없음), 각 적은 자기 셀과 8개 이웃 셀의 적과 거리 비교해 `separation += (me - other) / distSq`를 누적하고 `moveDir = (toPlayer + separation * k).normalized`. 비교 횟수가 O(n²)에서 대략 O(n × 이웃 수)로 줄어듭니다. 전후를 Profile Analyzer로 비교하세요.

</details>

**4. ★★★ 발열 시뮬레이션과 자동 보고서**
실기기에서 30분 자동 플레이(플레이어가 원을 그리며 이동하는 봇 입력)를 돌리며 10초마다 평균 프레임 시간·품질 단계·적 수를 CSV로 `Application.persistentDataPath`에 기록하고, 끝나면 PC로 옮겨 스프레드시트 그래프로 스로틀링 시점을 찾아보세요.

<details><summary>힌트·해설</summary>

08장 입력 구조에서 이동 벡터를 주입할 수 있다면 봇은 `new Vector2(Mathf.Cos(t), Mathf.Sin(t))`만 넣으면 됩니다. 기록은 `StreamWriter`를 한 번 열어 두고 10초마다 한 줄 `WriteLine` 후 `Flush`(매 프레임 쓰지 말 것). Android는 `adb pull /sdcard/Android/data/<패키지>/files/perf.csv`로 가져올 수 있습니다(경로는 기기·버전에 따라 다를 수 있음). 그래프에서 프레임 시간이 적 수와 무관하게 오르기 시작하는 지점이 스로틀링 신호입니다.

</details>

## 셀프 체크

**1. Profiler Hierarchy에서 Self와 Total의 차이를 설명하고, 병목을 찾을 때 어떻게 쓰는지 말해보세요.**

<details><summary>모범 답안</summary>

Total은 함수와 그 함수가 호출한 하위 함수들의 시간 합이고, Self는 하위 호출을 뺀 자기 코드만의 시간입니다. Total로 정렬해 큰 줄기를 따라 내려가다가 Self가 큰 항목에서 멈추면, 실제로 시간을 쓰는 코드를 찾을 수 있습니다. Calls 수도 함께 보면 "한 번이 무거운지, 많이 불리는지"를 구분할 수 있습니다.

</details>

**2. 모바일에서 프레임 예산을 100% 쓰면 안 되는 이유는?**

<details><summary>모범 답안</summary>

모바일 칩은 온도가 오르면 성능을 스스로 낮추는 스로틀링을 합니다. 처음에 예산을 꽉 채우면 몇 분 뒤 같은 작업이 예산을 넘어 프레임이 떨어집니다. 여유(예: 65~70%)를 두면 발열 후에도 목표 프레임을 유지할 가능성이 높고 배터리 소모도 줄어듭니다.

</details>

**3. 적 1000마리가 각자 `Update`를 갖는 구조를 매니저 틱으로 바꾸면 왜 빨라지나요?**

<details><summary>모범 답안</summary>

Unity는 각 MonoBehaviour의 `Update`를 네이티브 엔진 쪽에서 호출하므로 호출마다 네이티브↔관리 코드 경계를 넘는 비용과 목록 관리 비용이 있습니다. 매니저 하나가 C# 리스트를 for 루프로 돌면 경계 넘기는 한 번이고, 공통 값(플레이어 위치, deltaTime)도 한 번만 읽습니다. 또 계측·최적화 지점이 한 곳으로 모입니다.

</details>

**4. 메모리 누수를 Memory Profiler로 찾는 절차를 설명해보세요.**

<details><summary>모범 답안</summary>

같은 상태(예: 타이틀 화면)에서 여러 번 스냅샷을 찍습니다. 한 판을 한 뒤 타이틀에서 스냅샷, 몇 판 더 한 뒤 타이틀에서 다시 스냅샷을 찍고 두 스냅샷을 비교해, 판을 반복할수록 계속 늘어나는 객체(텍스처, 에셋, 관리 객체)를 찾습니다. 첫 판 직후와 비교하지 않는 이유는 첫 로드·캐시로 인한 정상 증가가 섞이기 때문입니다.

</details>

**5. 모바일 2D 게임에서 텍스처 메모리를 줄이는 설정 네 가지를 말해보세요.**

<details><summary>모범 답안</summary>

ASTC 압축(용도별 블록 크기), Max Size를 실제 표시 크기에 맞게 축소(단, 스프라이트 시트·아틀라스는 텍스처 전체에 적용되므로 프레임 하나의 표시 크기와 시트 안 크기의 비율로 계산), 2D 스프라이트의 Mip Maps 끄기, Read/Write 끄기. 추가로 Sprite Atlas로 묶어 드로우 콜을 줄이고 Memory Profiler로 중복 로드를 확인합니다.

</details>

## 핵심 요약

- 원칙은 **측정 → 가장 큰 원인 하나 수정 → 재측정**, 그리고 수치를 기록표로 남기기입니다.
- 예산은 60fps 16.67ms / 30fps 33.33ms이며, 모바일은 발열 스로틀링을 고려해 여유를 두고 10분 이상 실기기에서 잽니다.
- Profiler Hierarchy는 Total로 내려가 Self에서 멈추고, Deep Profile 대신 `ProfilerMarker`로 구간을 잽니다. 실기기 수치는 `ProfilerRecorder` 오버레이로도 확인합니다.
- Memory Profiler는 스냅샷 비교로 누수를, Frame Debugger는 드로우 콜 원인을, Profile Analyzer는 전후 비교를 담당합니다.
- 서바이버라이크의 3대 병목: 개체별 `Update`(→ 매니저 틱), 적끼리 물리 충돌(→ 레이어 매트릭스·싼 분리), 매 프레임 할당(→ LINQ·문자열 제거).
- 모바일은 `Application.targetFrameRate`를 명시(기본 30), 텍스처 ASTC·Max Size·Mip 끄기, 오디오 Load Type 구분.
- 적응형 품질은 프레임 시간을 몇 초 단위로 평균해 하향은 빠르게, 상향은 느리게(히스테리시스).

## 더 읽을거리

- Unity 매뉴얼 — Profiler overview: https://docs.unity3d.com/Manual/Profiler.html
- Unity 스크립팅 API — `ProfilerMarker`: https://docs.unity3d.com/ScriptReference/Unity.Profiling.ProfilerMarker.html
- Unity 스크립팅 API — `ProfilerRecorder`: https://docs.unity3d.com/ScriptReference/Unity.Profiling.ProfilerRecorder.html
- Memory Profiler / Profile Analyzer 패키지 문서 — Unity 패키지 문서 사이트에서 이름으로 검색
- Unity 전자책 "Optimize your mobile game performance" (Unity 공식 블로그·리소스 페이지에서 제목으로 검색)
