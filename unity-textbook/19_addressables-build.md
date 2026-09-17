# 19. Addressables와 빌드 자동화

> **이 장에서 배울 것**
> - `Resources` 폴더의 문제를 설명하고, Addressables의 주소·그룹·라벨·번들 개념으로 에셋을 구성한다
> - `LoadAssetAsync`/`InstantiateAsync`와 `Release`의 짝을 맞춰 메모리 누수 없이 에셋을 로드·해제한다
> - Remote 그룹과 원격 카탈로그로 앱 업데이트 없이 스테이지 데이터를 교체하는 흐름을 설명할 수 있다
> - IL2CPP·ARM64·Managed Stripping·스크립팅 정의 심볼 등 Player Settings 핵심을 이해하고, `BuildPipeline.BuildPlayer`로 원클릭 빌드 메뉴를 만든다
> - 명령행 빌드와 GitHub Actions(GameCI)로 자동 빌드 파이프라인을 구성하고, 빌드 리포트로 용량을 줄인다
>
> **선수 장**: 03, 09, 12, 18 · **예상 시간**: 5~6시간 · **코인 러시 진행**: 적·스테이지 데이터가 Addressables로 로드되고, 메뉴 한 번으로 Windows/Android 빌드가 나오며, 태그를 푸시하면 GitHub Actions가 빌드합니다.

## 왜 필요한가

코인 러시가 커지면서 이런 일이 생깁니다.

- 12장의 `EnemySpawner`가 적 프리팹 20종을 모두 `[SerializeField]` 배열로 들고 있습니다. 씬이 열리는 순간 **첫 스테이지에 안 나오는 적까지 전부** 메모리에 올라갑니다.
- 급한 마음에 `Resources.Load<GameObject>("Enemies/Slime")`로 바꿨더니, 빌드 용량이 오히려 커졌고 파일 이름을 바꾸자 런타임에 null이 떴습니다.
- 스테이지 3의 밸런스가 잘못돼 수정본을 내려면 **앱 전체를 다시 심사**받아야 합니다.
- 빌드는 매번 Build Profiles 창에서 플랫폼 전환 → 버전 번호 수정 → 키스토어 비밀번호 입력 → Build를 손으로 합니다. 한 번 빼먹으면 스토어가 업로드를 거부합니다("버전 코드가 이미 사용됨").

에셋을 **필요할 때 로드하고 다 쓰면 해제**하는 체계(Addressables)와, 사람이 실수할 수 없는 **빌드 스크립트**가 이 장의 두 축입니다. 웹 개발로 치면 코드 스플리팅 + CDN 배포, 그리고 CI/CD입니다.

## 개념

### Resources 폴더의 문제

`Assets/**/Resources/` 아래의 모든 에셋은 `Resources.Load("경로")`로 문자열 로드할 수 있습니다. 쉬워 보이지만:

| 문제 | 설명 |
|---|---|
| 무조건 빌드 포함 | 코드에서 쓰든 안 쓰든 Resources 폴더의 모든 에셋이 빌드에 들어감 |
| 시작 시간 | 앱 시작 시 Resources 전체의 인덱스(검색 트리)를 구성. 에셋이 많을수록 시작이 느려짐 |
| 문자열 경로 | 파일 이름·폴더를 바꾸면 컴파일 에러 없이 런타임에 null |
| 메모리 해제 | 개별 해제가 어렵고 `Resources.UnloadUnusedAssets()`로 전체를 훑어야 함 |
| 원격 업데이트 불가 | 앱 빌드 안에 고정 |

Unity도 공식 문서에서 프로토타이핑 이외의 용도로는 Resources 사용을 권장하지 않습니다.

### Addressables 핵심 개념

패키지 `com.unity.addressables`(Unity 6에서는 2.x 계열)입니다.

```
[에셋] Slime.prefab ──(Addressable 체크)──▶ 주소 "Enemies/Slime", 라벨 {enemy, stage1}
                                              │
                                              ▼ 그룹 "Enemies" (Local)
[빌드] Addressables 빌드 ─▶ 그룹 설정대로 AssetBundle 파일(.bundle) 생성 + 카탈로그(catalog)
                                              │
[런타임] Addressables.LoadAssetAsync("Enemies/Slime")
          ─▶ 카탈로그에서 주소 → 번들 위치 찾기 ─▶ 번들(과 의존 번들) 로드 ─▶ 에셋 반환
```

| 용어 | 의미 | 웹 비유 |
|---|---|---|
| 주소(Address) | 에셋을 찾는 문자열 키. 파일을 옮겨도 주소는 유지 | 라우트 경로 |
| 그룹(Group) | 번들로 묶이는 단위 + 빌드·로드 위치 설정 | 청크(chunk) |
| 라벨(Label) | 여러 에셋에 붙이는 태그. 라벨로 한꺼번에 로드 | 태그 |
| 번들(AssetBundle) | 실제로 디스크/서버에 놓이는 파일 | 번들 JS 파일 |
| 카탈로그(Catalog) | 주소 → 번들 위치 매핑 JSON | manifest.json |
| 프로필(Profile) | Build Path / Load Path 변수 세트(개발용, 출시용…) | 환경 변수 |

**그룹 설계 원칙**: 함께 로드되고 함께 해제되는 것끼리 묶습니다. 적 20종을 한 번들로 묶으면 하나만 로드해도 번들 파일 전체가 메모리에 올라갈 수 있습니다(Bundle Mode: Pack Together). 그룹 설정의 **Bundle Mode**를 `Pack Separately`로 하면 에셋마다 번들이 생깁니다. 중간 지점은 `Pack Together By Label`입니다.

### 로드와 해제의 짝 — 참조 카운트

Addressables는 참조 카운트로 메모리를 관리합니다. **로드 1회에는 해제 1회**가 반드시 짝으로 있어야 합니다. React의 `useEffect`에서 구독하면 cleanup에서 해제하는 것과 똑같습니다.

| 로드 | 해제 | 비고 |
|---|---|---|
| `var h = Addressables.LoadAssetAsync<T>(key)` | `Addressables.Release(h)` | 핸들을 저장해 뒀다가 해제 |
| `Addressables.LoadAssetsAsync<T>(label, callback)` | `Addressables.Release(h)` | 라벨로 여러 개, 해제도 핸들 하나로 |
| `Addressables.InstantiateAsync(key)` | `Addressables.ReleaseInstance(go)` | `Destroy`만 하면 참조 카운트가 줄지 않음 |
| `assetRef.LoadAssetAsync<T>()` | `assetRef.ReleaseAsset()` | `AssetReference` 필드 |

```
참조 카운트 흐름
LoadAssetAsync("Slime")  → count 1 → 번들 로드
LoadAssetAsync("Slime")  → count 2
Release(h1)              → count 1
Release(h2)              → count 0 → 번들 언로드 가능
(Release를 하나 빼먹으면 → count 1 영원히 → 누수, 18장 Memory Profiler에서 발견)
```

**풀링과 함께 쓸 때**: 적 수백 마리를 `InstantiateAsync`로 하나씩 만들면 인스턴스마다 추적 비용이 붙습니다. 권장 패턴은 **프리팹을 `LoadAssetAsync`로 한 번 로드 → 12장 풀에서 일반 `Instantiate`로 복제 → 스테이지가 끝나면 풀을 비우고 프리팹 핸들을 `Release`**입니다.

### AssetReference 필드

인스펙터에서 Addressable 에셋을 드래그할 수 있는 직렬화 필드입니다. 일반 `GameObject` 필드와 달리 **참조하는 쪽이 로드될 때 대상이 같이 로드되지 않습니다**.

```csharp
[SerializeField] AssetReferenceGameObject bossPrefab;   // 프리팹
[SerializeField] AssetReferenceSprite background;       // 스프라이트
[SerializeField] AssetReferenceT<EnemyData> enemy;      // 임의 타입 (ScriptableObject 등)
```

반대로 일반 `[SerializeField] GameObject prefab`으로 참조하면 **직렬화 의존성**이라 참조하는 에셋이 로드될 때 함께 로드됩니다. 03장 `EnemyData.prefab`처럼 "데이터를 쓰면 프리팹도 반드시 필요한" 관계라면 일반 참조로 두는 것이 오히려 단순합니다.

### 원격 콘텐츠와 콘텐츠 업데이트

```
[앱 빌드 v1.0]                    [CDN/서버]
 Local 그룹 번들 (앱 안에 포함)      Remote 그룹 번들 (stages_*.bundle)
 원격 카탈로그 위치 URL ──────────▶ catalog_*.json / .hash
```

1. 그룹 설정에서 Build & Load Paths를 **Remote**로 둔 그룹(`Stages`)을 만듭니다.
2. Addressables Settings에서 **Build Remote Catalog**를 켭니다.
3. 프로필의 `Remote.LoadPath`를 서버 URL로 설정합니다(예: `https://cdn.example.com/coinrush/[BuildTarget]`). Unity의 Cloud Content Delivery나 일반 정적 파일 호스팅(S3, Cloudflare R2 등)을 쓸 수 있습니다.
4. 출시 빌드 시 Addressables가 **content state 파일**(`addressables_content_state.bin`, 기본 위치 `Assets/AddressableAssetsData/<플랫폼>/`)을 만듭니다. **출시한 빌드에서 나온 파일을 플랫폼·앱 버전별로 보관**합니다(버전 관리에 커밋하거나 6단계처럼 CI 산출물로 보관). 이후 업데이트 빌드의 기준이며, 빌드할 때마다 덮어써지므로 출시 후에 다시 빌드한 파일로는 대신할 수 없습니다.
5. 스테이지 데이터를 고친 뒤 Addressables Groups 창의 **Tools → Check for Content Update Restrictions**를 실행합니다. 업데이트 제한이 걸린 그룹(보통 Local 그룹, 설정 이름은 버전에 따라 "Prevent Updates" 또는 "Cannot Change Post Release")의 에셋이 바뀌었다면, 바뀐 에셋을 새 Remote 그룹으로 옮기도록 안내합니다.
6. **Build → Update a Previous Build**로 content state 파일을 선택해 빌드 → 새 번들과 카탈로그를 서버에 업로드합니다.
7. 이미 설치된 앱은 다음 실행 시 원격 카탈로그 해시가 바뀐 것을 확인하고 새 번들을 받습니다(자동 카탈로그 확인 여부는 설정에 따라 다름).

**할 수 없는 것**: Addressables로 **C# 코드는 업데이트할 수 없습니다.** 스크립트가 새로 필요한 기능은 앱 업데이트가 필요합니다. 데이터(ScriptableObject 값, 스프라이트, 프리팹 조합)만 바꿀 수 있습니다. 또 스토어 정책상 원격으로 받은 콘텐츠로 앱의 핵심 기능을 크게 바꾸는 것은 제한될 수 있으니 각 스토어 정책을 확인하세요.

### Play Mode Script

Addressables Groups 창 상단 **Play Mode Script**:

| 모드 | 동작 | 언제 |
|---|---|---|
| Use Asset Database (fastest) | 번들 빌드 없이 에디터 에셋을 직접 로드 | 평소 개발 |
| Use Existing Build | 실제로 빌드된 번들을 로드 | 출시 전 검증, 원격 로드 테스트 |

1.x 자료에 나오는 "Simulate Groups" 모드는 Addressables 2.x에서 제거되었습니다(설치 버전의 문서 확인). **Use Asset Database는 번들 구성 문제(누락된 의존성, 잘못된 주소)를 숨깁니다.** 빌드 전에는 반드시 Use Existing Build로 한 번 돌려 보세요.

### 빌드: Player Settings 핵심

| 설정 | 권장 | 설명 |
|---|---|---|
| Scripting Backend | **IL2CPP** (모바일·출시용) | C#을 C++로 변환해 네이티브 컴파일. Mono보다 빠르고 iOS는 필수. 빌드 시간이 길어짐 |
| Target Architectures (Android) | **ARM64** | Google Play는 64비트 지원 필수. ARMv7은 구형 기기용(용량 증가) |
| Managed Stripping Level | Minimal/Low에서 시작 → Medium 시험 | 안 쓰는 코드 제거로 용량 감소. 높을수록 **리플렉션으로만 쓰는 타입이 잘려** 런타임 오류 가능 |
| API Compatibility Level | .NET Standard 2.1 | 기본값 유지 |
| Scripting Define Symbols | 빌드별로 다르게 | `#if COINRUSH_DEMO` 같은 조건부 컴파일 |

**link.xml**: 스트리핑이 잘라내면 안 되는 어셈블리·타입을 선언합니다. `Assets/` 아래 어디든 둘 수 있습니다.

```xml
<!-- Assets/_CoinRush/link.xml -->
<linker>
  <!-- 10장 세이브 마이그레이션이 Type.GetType으로 찾는 클래스들 -->
  <assembly fullname="Assembly-CSharp">
    <type fullname="SaveMigrationV1ToV2" preserve="all"/>
  </assembly>
  <!-- 외부 JSON 라이브러리가 리플렉션으로 쓰는 경우 어셈블리 통째로 보존 -->
  <assembly fullname="Newtonsoft.Json" preserve="all"/>
</linker>
```

코드에서는 `[UnityEngine.Scripting.Preserve]` 속성으로 개별 클래스·메서드를 보존할 수도 있습니다. 증상이 "에디터와 개발 빌드는 되는데 스트리핑 High 릴리스 빌드에서만 `MissingMethodException`"이면 스트리핑을 의심합니다.

### Build Profiles (Unity 6)

Unity 6에서는 기존 Build Settings 창이 **File → Build Profiles**로 바뀌었습니다. 플랫폼별 기본 프로필 외에 **사용자 프로필 에셋**을 만들어, 프로필마다 씬 목록·스크립팅 정의 심볼·일부 Player Settings를 오버라이드할 수 있습니다(예: `Android_Demo`, `Android_Release`, `Steam_Release`). 에디터 스크립트에서 프로필로 빌드하는 API(`BuildPlayerWithProfileOptions`)도 있으나 도입된 버전과 세부 사항이 6000.x 마이너 버전마다 다를 수 있으니 공식 문서를 확인하세요. 이 장에서는 모든 6000.x에서 동작하는 `BuildPlayerOptions` 방식을 씁니다.

### 명령행 빌드와 CI

```
<Unity 실행 파일> -batchmode -nographics -quit \
  -projectPath /path/to/CoinRush \
  -buildTarget Android \
  -executeMethod BuildScripts.BuildFromCommandLine \
  -logFile -
```

| 인수 | 의미 |
|---|---|
| `-batchmode` | 창 없이 실행 |
| `-nographics` | GPU 없이(서버) 실행 |
| `-quit` | 메서드 실행 후 종료 |
| `-buildTarget` | 에디터를 해당 플랫폼으로 연 상태로 시작(플랫폼 전환 비용 절감) |
| `-executeMethod` | `Editor` 어셈블리의 **정적 메서드** 실행 |
| `-logFile -` | 로그를 표준 출력으로 |

Unity 실행 파일 위치는 Unity Hub로 설치했다면 macOS `/Applications/Unity/Hub/Editor/<버전>/Unity.app/Contents/MacOS/Unity`, Windows `C:\Program Files\Unity\Hub\Editor\<버전>\Editor\Unity.exe`입니다. 빌드 실패 시 **0이 아닌 종료 코드**로 끝내야 CI가 실패를 인식합니다(`EditorApplication.Exit(1)`).

CI 선택지:

| 방법 | 특징 |
|---|---|
| **GameCI + GitHub Actions** | 오픈소스 Docker 이미지·액션(`game-ci/unity-builder`). GitHub 무료 러너 사용 가능. **Unity 라이선스 활성화**(Secrets에 라이선스 정보 등록) 필요 |
| **Unity Build Automation** | Unity 공식 클라우드 빌드(구 Cloud Build). 설정이 쉽고 iOS 빌드 머신 제공. 빌드 시간 기반 과금 |
| 자체 머신 + 스크립트 | 집의 PC를 GitHub self-hosted runner로. Windows IL2CPP·iOS(맥) 빌드에 유리 |

플랫폼 제약: **Windows IL2CPP 빌드는 Windows 머신**, **iOS는 macOS + Xcode**가 필요합니다. GitHub의 Ubuntu 러너에서 Windows용을 빌드하려면 Scripting Backend를 Mono로 해야 합니다.

## 실습: 코인 러시에 적용하기

런타임 스크립트는 `Assets/_CoinRush/Scripts/Content/`, 에디터 스크립트는 `Assets/_CoinRush/Scripts/Editor/`(폴더 이름 `Editor` 필수, 20장 참고)에 둡니다.

### 1단계: Addressables 설치와 그룹 구성

1. Package Manager → Unity Registry → **Addressables** 설치.
2. Window → Asset Management → Addressables → **Groups** → Create Addressables Settings.
3. 기본 그룹 `Default Local Group` 외에 우클릭 → Create New Group → Packed Assets로 `Enemies`, `Stages` 두 개를 만듭니다.
4. `Enemies` 그룹 선택 → Inspector에서 Bundle Mode `Pack Separately`, Build & Load Paths `Local`.
5. `Stages` 그룹: Bundle Mode `Pack Together`, Build & Load Paths `Remote`(3단계 전까지는 Local로 둬도 됩니다).
6. Project 창에서 `Assets/_CoinRush/Data/Enemies/`의 `EnemyData` 에셋들을 `Enemies` 그룹으로 드래그합니다. 주소를 `Enemies/Slime`처럼 짧게 바꾸고(에셋 우클릭 → Simplify Addressable Names 후 접두사 추가), Labels 열에서 `enemy` 라벨을 붙입니다. `EnemyData.prefab`이 참조하는 프리팹은 자동으로 의존성으로 포함되며, 명시적으로 그룹에 넣지 않아도 됩니다(다만 여러 그룹이 같은 프리팹을 참조하면 중복 포함될 수 있으므로 **Tools → Analyze**의 중복 의존성 규칙으로 확인합니다).

### 2단계: 스테이지 데이터와 로더

스테이지 하나가 어떤 적을 쓰는지 정의하는 ScriptableObject를 만듭니다. 03장 `EnemyData`는 이름, `maxHp`, `moveSpeed`, `contactDamage`, `coinDrop`, `prefab`을 가진다고 가정합니다.

```csharp
// Assets/_CoinRush/Scripts/Content/StageData.cs
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;

[CreateAssetMenu(menuName = "Coin Rush/Data/Stage", fileName = "StageData")]
public class StageData : ScriptableObject
{
    public string displayName = "Stage 1";
    public float durationSeconds = 600f;
    public AssetReferenceSprite background;
    public List<AssetReferenceT<EnemyData>> enemies = new();
}
```

`Assets/_CoinRush/Data/Stages/Stage01.asset`을 만들어 적 몇 종을 드래그하고, `Stages` 그룹에 넣어 주소를 `Stages/Stage01`로 둡니다.

로더는 한 번에 하나의 스테이지만 "적용"합니다. 비동기 로드 도중에 새 로드 요청이 오거나 씬이 닫힐 수 있으므로, **요청마다 번호(세대)를 매기고 요청이 만든 핸들은 그 요청이 끝까지 소유**합니다. 모든 로드가 성공하고 자기 요청이 여전히 최신일 때만 결과를 적용하고 핸들을 로더로 넘깁니다. 그 밖의 경우(실패, 더 새로운 요청, 언로드, 파괴)에는 자기 핸들만 해제하고 조용히 빠집니다.

```csharp
// Assets/_CoinRush/Scripts/Content/StageLoader.cs
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

public class StageLoader : MonoBehaviour
{
    [SerializeField] SpriteRenderer backgroundRenderer;
    [SerializeField] EnemySpawner spawner;              // 12장 (아래에서 교체)

    readonly List<AsyncOperationHandle> handles = new();   // 현재 "적용된" 스테이지가 소유한 핸들
    readonly List<EnemyData> loadedEnemies = new();
    int generation;                                        // 요청 번호. 새 요청·Unload·파괴마다 증가

    public StageData Current { get; private set; }
    public IReadOnlyList<EnemyData> LoadedEnemies => loadedEnemies;
    public bool IsLoading { get; private set; }
    public bool IsReady => Current != null && !IsLoading;

    /// <returns>true: 이 요청의 스테이지가 적용됨. false: 더 새로운 요청·Unload·파괴로 무효화됨. 실패는 예외.</returns>
    public async Awaitable<bool> LoadAsync(string stageAddress)
    {
        Unload();                       // 이전 스테이지 해제 + 진행 중이던 요청 무효화
        int myGeneration = generation;
        IsLoading = true;

        var owned = new List<AsyncOperationHandle>();      // 이 요청이 만든 핸들
        try
        {
            var stageHandle = Addressables.LoadAssetAsync<StageData>(stageAddress);
            owned.Add(stageHandle);
            StageData stage = await stageHandle.Task;
            if (myGeneration != generation) return false;   // await 뒤에는 항상 유효성 확인
            if (stageHandle.Status != AsyncOperationStatus.Succeeded)
                throw new Exception($"Stage load failed: {stageAddress}", stageHandle.OperationException);

            // 배경과 적 데이터를 동시에 요청
            AsyncOperationHandle<Sprite> bgHandle = default;
            bool hasBackground = stage.background != null && stage.background.RuntimeKeyIsValid();
            if (hasBackground)
            {
                bgHandle = Addressables.LoadAssetAsync<Sprite>(stage.background);   // AssetReference도 키로 사용 가능
                owned.Add(bgHandle);
            }

            var enemyHandles = new List<AsyncOperationHandle<EnemyData>>();
            foreach (var reference in stage.enemies)
            {
                var h = Addressables.LoadAssetAsync<EnemyData>(reference);
                owned.Add(h);
                enemyHandles.Add(h);
            }

            Sprite bg = null;
            if (hasBackground)
            {
                bg = await bgHandle.Task;
                if (myGeneration != generation) return false;
                if (bgHandle.Status != AsyncOperationStatus.Succeeded)
                    throw new Exception($"Background load failed: {stage.displayName}", bgHandle.OperationException);
            }

            var enemies = new List<EnemyData>();
            foreach (var h in enemyHandles)
            {
                EnemyData data = await h.Task;
                if (myGeneration != generation) return false;
                if (h.Status != AsyncOperationStatus.Succeeded)
                    throw new Exception($"Enemy load failed: {stage.displayName}", h.OperationException);
                enemies.Add(data);
            }
            if (enemies.Count == 0) throw new Exception($"Stage has no enemies: {stage.displayName}");

            // ── 여기부터는 await 없음: 한 프레임 안에서 원자적으로 적용 ──
            handles.AddRange(owned);
            owned.Clear();                          // 소유권을 로더로 넘김 → finally에서 해제되지 않음
            Current = stage;
            loadedEnemies.AddRange(enemies);
            backgroundRenderer.sprite = bg;
            spawner.Prewarm(loadedEnemies);         // 풀 생성 → 이때부터 스폰 가능
            return true;
        }
        finally
        {
            if (myGeneration == generation) IsLoading = false;
            // 실패·무효화된 요청: 자기 핸들만, 완료를 기다린 뒤 해제 (다른 요청의 핸들은 건드리지 않음)
            foreach (var h in owned)
            {
                if (!h.IsValid()) continue;
                if (!h.IsDone) await h.Task;
                Addressables.Release(h);
            }
        }
    }

    public void Unload()
    {
        generation++;                     // 진행 중인 요청은 다음 await 뒤에 스스로 빠짐
        IsLoading = false;
        spawner.ClearPools();             // 풀의 인스턴스를 먼저 파괴 (프리팹 해제보다 앞서야 함)
        backgroundRenderer.sprite = null;
        ReleaseApplied();
    }

    void OnDestroy()
    {
        // 씬 언로드 중: 풀 오브젝트는 씬과 함께 파괴되므로(12장) ClearPools를 부르지 않고 핸들만 해제
        generation++;
        ReleaseApplied();
    }

    void ReleaseApplied()
    {
        foreach (var h in handles)
            if (h.IsValid()) Addressables.Release(h);
        handles.Clear();
        loadedEnemies.Clear();
        Current = null;
    }
}
```

코드 포인트:

- `AssetReference`는 `Addressables.LoadAssetAsync<T>(reference)`처럼 **키로 넘겨** 로드했습니다. `reference.LoadAssetAsync<T>()`는 참조 객체 안에 핸들을 저장하므로 같은 참조를 두 번 로드하면 에러가 나고, 반드시 `reference.ReleaseAsset()`으로만 해제해야 합니다. 이 로더는 **로드·해제를 모두 핸들로 통일**해 두 방식이 섞이지 않게 했습니다.
- `handles`·`owned` 리스트는 제네릭이 아닌 `AsyncOperationHandle`로 저장합니다(제네릭 핸들은 암시적 변환됨).
- **세대 번호**: A 로드 중에 B 로드가 시작되면 `Unload()`가 `generation`을 올립니다. A는 다음 `await`에서 돌아와 번호가 달라진 것을 보고 `return false` → `finally`에서 **A가 만든 핸들만** 해제합니다. B의 핸들이나 이미 적용된 스테이지는 건드리지 않고, 파괴된 렌더러에도 접근하지 않습니다. `OnDestroy`도 번호를 올리므로 씬이 닫히는 중의 continuation이 같은 방식으로 정리됩니다.
- 완료되지 않은 핸들은 `await h.Task`로 끝나기를 기다린 뒤 해제합니다. 진행 중인 작업을 해제하는 순간의 동작에 기대지 않기 위해서입니다.
- 해제 순서: 풀에 남아 있는 **인스턴스를 먼저 파괴**한 뒤 프리팹 핸들을 해제합니다. 반대로 하면 인스턴스가 쓰던 텍스처·메시가 사라져 분홍색·투명으로 보일 수 있습니다.

12장 `EnemySpawner`를 아래 파일로 **교체**합니다. 바뀐 점은 세 가지입니다. ① `enemyTypes`가 더 이상 `[SerializeField]`가 아닌 **런타임 전용** 배열입니다(씬 파일이 적 에셋을 직접 참조하지 않아야 Addressables로 옮긴 의미가 있습니다). ② `Awake`의 풀 생성 루프를 없애고 `Prewarm`에서 만듭니다. ③ 풀이 준비되기 전에는 `Update`가 아무것도 하지 않습니다.

```csharp
// Assets/_CoinRush/Scripts/Enemies/EnemySpawner.cs  (12장 파일 교체 — 22장에서 다시 교체됨)
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Pool;

public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private Transform player;
    [SerializeField] private GameplayPools pools;
    [SerializeField] private float spawnInterval = 0.05f;
    [SerializeField] private int maxAlive = 500;
    [SerializeField] private float spawnRadius = 12f;   // 카메라 밖 거리

    private readonly Dictionary<EnemyData, ObjectPool<Enemy>> poolByType = new();
    private EnemyData[] enemyTypes = System.Array.Empty<EnemyData>();   // StageLoader가 채움 (직렬화 안 함)
    private float timer;
    private int totalAlive;

    public bool IsReady => enemyTypes.Length > 0;

    private void Update()
    {
        if (!IsReady) return;   // 스테이지 로드 전·언로드 후에는 스폰하지 않음

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

    public void Prewarm(IReadOnlyList<EnemyData> datas)
    {
        enemyTypes = new EnemyData[datas.Count];
        for (int i = 0; i < datas.Count; i++)
        {
            EnemyData type = datas[i];
            enemyTypes[i] = type;
            if (poolByType.ContainsKey(type)) continue;
            var parent = new GameObject($"Enemies_{type.name}").transform;
            parent.SetParent(transform, false);
            poolByType[type] = PoolUtil.Create(type.prefab.GetComponent<Enemy>(), parent, prewarm: 150, maxSize: maxAlive);
        }
    }

    public void ClearPools()
    {
        enemyTypes = System.Array.Empty<EnemyData>();   // 먼저 스폰을 멈춤
        foreach (var pool in poolByType.Values) pool.Clear();   // ObjectPool.Clear: 반납된 인스턴스 파괴
        poolByType.Clear();
        foreach (Transform child in transform) Destroy(child.gameObject);   // 부모째 파괴 → 활성 적도 함께 제거
        timer = 0f;
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

`ObjectPool<T>.Clear()`는 **풀 안에 반납된** 인스턴스만 `actionOnDestroy`로 파괴합니다. 아직 필드에 나와 있는 적은 풀 부모 오브젝트를 파괴할 때 자식으로 함께 사라집니다. 코드를 바꾼 뒤 씬을 저장하면 `Enemy Types` 칸이 Inspector에서 사라지고, 씬 파일의 적 에셋 참조도 없어집니다. 18장 스트레스 씬처럼 다른 컴포넌트가 `EnemyData`를 직렬화 필드로 들고 있다면 그 참조는 따로 정리하세요.

이제 Game 씬이 열리면 스테이지를 먼저 로드하고, **로드가 끝난 뒤에야** 상태 머신이 시작되게 합니다. 09장 `GameFlow`는 Bootstrap 씬에 있어 Game 씬 오브젝트를 참조할 수 없으므로, 연결은 Game 씬 안의 04장 `GameStateMachine`에서 합니다. 09장 `SceneState`가 Game 씬 로드를 끝내면 이 `Start`가 실행됩니다.

```csharp
// GameStateMachine.cs (04장) — 필드 추가, Start 교체
[Header("스테이지 (19장)")]
[SerializeField] private StageLoader stageLoader;
[SerializeField] private string stageAddress = "Stages/Stage01";

async void Start()   // 04장의 void Start() => ChangeState(Title); 를 교체
{
    SetGameplayActive(false);   // 로드 중에는 스포너 등 게임플레이 컴포넌트와 이동을 끔. Current는 null이라 StartGame도 무시됨
    try
    {
        bool applied = await stageLoader.LoadAsync(stageAddress);
        if (!applied || this == null) return;   // 씬이 닫히는 등으로 요청이 무효화됨
        ChangeState(Title);                      // 콘텐츠 준비 완료 → 04장 흐름 시작 (Title → Playing)
    }
    catch (System.Exception e)
    {
        Debug.LogException(e);   // 로드 실패: Playing에 진입하지 않음 (연습 문제 3의 재시도 UI로 확장)
    }
}
```

`async void`는 이벤트 핸들러 같은 최상위 진입점에만 씁니다(09장). 그래서 본문 전체를 `try/catch`로 감쌌습니다.

에디터 작업:

1. Project 창에서 배경 스프라이트(예: `Assets/_CoinRush/Art/Backgrounds/Stage01_BG.png`)를 선택해 Inspector의 **Addressable** 체크 → `Stages` 그룹으로 옮기고 주소를 `Stages/Stage01_BG`로 둡니다.
2. `Stage01.asset`의 `Background` 칸에 그 스프라이트를, `Enemies` 목록에 1단계의 `EnemyData`들을 드래그합니다(Addressable이 아닌 에셋은 드롭되지 않습니다).
3. `Stage01.asset`과 배경 스프라이트에 라벨 `stage01`을 붙입니다(3단계 다운로드 크기 확인에 사용).
4. Game 씬에 빈 오브젝트 `Background`를 만들고 `SpriteRenderer`를 붙인 뒤 Order in Layer를 가장 낮게(예: -100) 둡니다. 기존에 씬에 직접 넣어 둔 배경 스프라이트가 있다면 지웁니다(그대로 두면 씬과 함께 로드됨).
5. Game 씬에 빈 오브젝트 `StageLoader`를 만들고 `StageLoader` 컴포넌트를 붙인 뒤 `Background Renderer`에 `Background`, `Spawner`에 `EnemySpawner` 오브젝트를 연결합니다.
6. `GameSystems`의 `GameStateMachine`에서 `Stage Loader`에 `StageLoader` 오브젝트를 연결하고 `Stage Address`가 `Stages/Stage01`인지 확인합니다.

### 3단계: 원격 스테이지 그룹 테스트

실제 CDN 없이 로컬에서 원격 흐름을 확인합니다.

1. Addressables Groups 창 → Profile: `Manage Profiles`에서 `Default` 프로필을 복제해 `LocalRemoteTest`를 만들고, Remote의 Load Path를 `http://localhost:8080/[BuildTarget]`으로 둡니다. Build Path는 기본 `ServerData/[BuildTarget]`.
2. Window → Asset Management → Addressables → **Settings** → Catalog의 **Build Remote Catalog** 켬, Build & Load Paths를 Remote로.
3. `Stages` 그룹의 Build & Load Paths를 `Remote`로.
4. Groups 창 → Build → New Build → Default Build Script.
5. 터미널에서 프로젝트 폴더의 `ServerData`를 정적 서버로 엽니다(예: `cd ServerData && python3 -m http.server 8080`).
6. Play Mode Script를 **Use Existing Build**로 바꾸고 Play → 콘솔에 에러 없이 스테이지가 뜨고, 터미널에 번들 요청 로그가 찍히면 성공입니다.
7. `Stage01`의 적 목록을 바꾸고 **Tools → Check for Content Update Restrictions** → **Build → Update a Previous Build**(4번에서 생성된 content state 파일 선택). 서버를 켠 채 다시 Play하면 바뀐 적 구성이 적용됩니다.

실제 출시에서는 Load Path만 CDN 주소로 바꾼 프로필을 쓰고, `ServerData/<플랫폼>` 내용을 업로드합니다. 원격 번들 다운로드가 실패할 수 있으므로(오프라인) 첫 실행 때 받아야 할 크기를 `Addressables.GetDownloadSizeAsync("stage01")`로 확인하고, 필요하면 `Addressables.DownloadDependenciesAsync("stage01")`로 미리 받는 로딩 화면을 만듭니다(09장, 연습 문제 3).

여기서 키를 주소 `Stages/Stage01`이 아니라 **라벨 `stage01`** 로 쓰는 이유가 있습니다. 다운로드 크기·의존성 계산은 그 키의 에셋과 **직렬화 의존성**(번들 의존성)을 기준으로 합니다. 그런데 `StageData`는 배경·적을 `AssetReference`로 들고 있어서, 앞의 "AssetReference 필드" 절에서 본 것처럼 참조 대상이 의존성으로 따라오지 않습니다. `Stages/Stage01` 하나로 계산하면 StageData 번들만 세고, 다른 번들에 있는 배경이 빠질 수 있습니다. 그래서 스테이지에 필요한 원격 에셋(StageData, 배경, 나중에 원격 그룹으로 옮기는 적 데이터 등)에 **같은 라벨**을 붙여 한 키로 전체 집합을 계산합니다. 라벨 대신 StageData를 먼저 로드해 `background.RuntimeKey`·`enemies[i].RuntimeKey`를 모은 키 목록을 넘기는 방법도 있지만, StageData 자체가 원격이면 그것부터 받아야 하므로 라벨이 단순합니다. 에셋을 스테이지에 추가할 때 라벨을 빠뜨리지 않도록 20장 방식의 검증 도구를 두면 좋습니다.

### 4단계: 원클릭 빌드 메뉴

```csharp
// Assets/_CoinRush/Scripts/Editor/BuildScripts.cs
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.AddressableAssets.Settings;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class BuildScripts
{
    const string BuildRoot = "Builds";

    [MenuItem("Coin Rush/Build/Windows (Release)")]
    public static void BuildWindows()
    {
        Build(BuildTarget.StandaloneWindows64, NamedBuildTarget.Standalone,
              Path.Combine(BuildRoot, "Windows", "CoinRush.exe"), extraDefines: null);
    }

    [MenuItem("Coin Rush/Build/Android (AAB Release)")]
    public static void BuildAndroid()
    {
        EditorUserBuildSettings.buildAppBundle = true;
        ConfigureAndroidSigning();
        Build(BuildTarget.Android, NamedBuildTarget.Android,
              Path.Combine(BuildRoot, "Android", $"CoinRush-{PlayerSettings.bundleVersion}.aab"), extraDefines: null);
    }

    [MenuItem("Coin Rush/Build/Android (Demo APK)")]
    public static void BuildAndroidDemo()
    {
        EditorUserBuildSettings.buildAppBundle = false;
        Build(BuildTarget.Android, NamedBuildTarget.Android,
              Path.Combine(BuildRoot, "Android", "CoinRush-demo.apk"), extraDefines: new[] { "COINRUSH_DEMO" });
    }

    static bool versionCodeInjected;   // CI가 버전 코드를 넘겼으면 Build에서 자동 증가하지 않음

    // CI 진입점: -executeMethod BuildScripts.BuildFromCommandLine
    // GameCI(unity-builder)는 -customBuildTarget, -buildVersion, -androidVersionCode, -androidKeystoreName 등을
    // 명령행 인수로 넘깁니다(값이 없으면 빈 문자열). 워크플로의 env는 Unity 프로세스까지 전달되지 않습니다.
    public static void BuildFromCommandLine()
    {
        string target = GetArg("-customBuildTarget");
        if (string.IsNullOrEmpty(target)) target = EditorUserBuildSettings.activeBuildTarget.ToString();
        string version = GetArg("-buildVersion");
        if (!string.IsNullOrEmpty(version) && version != "none") PlayerSettings.bundleVersion = version;
        if (int.TryParse(GetArg("-androidVersionCode"), out int code) && code > 0)
        {
            PlayerSettings.Android.bundleVersionCode = code;
            versionCodeInjected = true;
        }

        try
        {
            switch (target)
            {
                case "Android": BuildAndroid(); break;
                case "StandaloneWindows64": BuildWindows(); break;
                default: throw new ArgumentException($"Unknown target {target}");
            }
            EditorApplication.Exit(0);
        }
        catch (Exception e)
        {
            Debug.LogException(e);
            EditorApplication.Exit(1);   // CI가 실패를 인식하도록
        }
    }

    static void Build(BuildTarget target, NamedBuildTarget named, string outputPath, string[] extraDefines)
    {
        if (EditorUserBuildSettings.activeBuildTarget != target)
            throw new InvalidOperationException(
                $"현재 플랫폼({EditorUserBuildSettings.activeBuildTarget})이 {target}이 아닙니다. Build Profiles에서 먼저 전환하세요.");

        // 1) 플랫폼 공통 설정 보장
        if (target == BuildTarget.Android)
        {
            PlayerSettings.SetScriptingBackend(named, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.SetManagedStrippingLevel(named, ManagedStrippingLevel.Low);
            if (!versionCodeInjected)
                PlayerSettings.Android.bundleVersionCode++;   // 로컬 빌드: 스토어 업로드마다 증가해야 함
        }

        // 2) Addressables 콘텐츠 빌드 (설정의 "Build Addressables on Player Build"는 끄고 여기서 명시적으로)
        AddressableAssetSettings.BuildPlayerContent(out var addrResult);
        if (!string.IsNullOrEmpty(addrResult.Error))
            throw new Exception("Addressables build failed: " + addrResult.Error);

        // 3) 플레이어 빌드
        var options = new BuildPlayerOptions
        {
            scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
            locationPathName = outputPath,
            target = target,
            options = BuildOptions.None,
            extraScriptingDefines = extraDefines,   // 프로젝트 설정을 영구 변경하지 않음
        };

        Directory.CreateDirectory(Path.GetDirectoryName(outputPath));
        BuildReport report = BuildPipeline.BuildPlayer(options);
        var s = report.summary;
        Debug.Log($"[Build] {s.result} {target} v{PlayerSettings.bundleVersion} " +
                  $"size={s.totalSize / (1024f * 1024f):F1}MB time={s.totalTime} errors={s.totalErrors}");

        if (s.result != BuildResult.Succeeded)
            throw new Exception($"Build failed: {s.result}");

        BuildSizeReport.LogLargestAssets(report, 15);   // 5단계
        AssetDatabase.SaveAssets();                     // 증가한 versionCode 저장
    }

    static void ConfigureAndroidSigning()
    {
        // 비밀번호는 코드·저장소에 두지 않음.
        // CI: GameCI가 넘기는 명령행 인수(-androidKeystoreName 등) / 로컬: 환경 변수 COINRUSH_KEYSTORE_* 
        string ksPath = FirstNonEmpty(GetArg("-androidKeystoreName"), Environment.GetEnvironmentVariable("COINRUSH_KEYSTORE_PATH"));
        if (string.IsNullOrEmpty(ksPath))
        {
            Debug.LogWarning("[Build] 키스토어 정보 없음 — Player Settings의 서명 설정을 그대로 사용");
            return;
        }
        PlayerSettings.Android.useCustomKeystore = true;
        PlayerSettings.Android.keystoreName = ksPath;   // 상대 경로면 프로젝트 폴더 기준
        PlayerSettings.Android.keystorePass = FirstNonEmpty(GetArg("-androidKeystorePass"), Environment.GetEnvironmentVariable("COINRUSH_KEYSTORE_PASS"));
        PlayerSettings.Android.keyaliasName = FirstNonEmpty(GetArg("-androidKeyaliasName"), Environment.GetEnvironmentVariable("COINRUSH_KEY_ALIAS"));
        PlayerSettings.Android.keyaliasPass = FirstNonEmpty(GetArg("-androidKeyaliasPass"), Environment.GetEnvironmentVariable("COINRUSH_KEY_PASS"));
    }

    static string FirstNonEmpty(string a, string b) => string.IsNullOrEmpty(a) ? b : a;

    static string GetArg(string name)
    {
        var args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
            if (args[i] == name) return args[i + 1];
        return null;
    }
}
```

설계 포인트:

- **플랫폼 자동 전환을 하지 않습니다.** 에디터에서 `SwitchActiveBuildTarget`을 호출하면 전체 에셋 재임포트가 일어나고, 같은 메서드 안에서 곧바로 빌드하면 상태가 불안정할 수 있습니다. 명령행에서는 `-buildTarget`으로 시작 시점에 전환합니다.
- **버전 코드 자동 증가**는 로컬 빌드용입니다. CI에서는 `-androidVersionCode`로 외부에서 주입해야 여러 머신에서 충돌하지 않으므로, 값이 들어오면 `versionCodeInjected`로 `++`를 건너뜁니다. GameCI는 기본 `versioning: Semantic`에서 Git 태그로 버전과 버전 코드를 계산해 넘깁니다. 로컬·CI 규칙을 하나로 맞추는 방법은 연습 문제 2에서 다룹니다.
- `extraScriptingDefines`는 이 빌드에만 정의 심볼을 추가하므로 데모 빌드 후 프로젝트 설정이 오염되지 않습니다.
- 스트리핑은 `Low`에서 시작해, 전체 플레이 테스트 후 `Medium`을 시험하고 용량 차이를 기록합니다.

### 5단계: 빌드 용량 리포트

```csharp
// Assets/_CoinRush/Scripts/Editor/BuildSizeReport.cs
using System.Linq;
using System.Text;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class BuildSizeReport
{
    public static void LogLargestAssets(BuildReport report, int top)
    {
        if (report.packedAssets == null || report.packedAssets.Length == 0)
        {
            Debug.Log("[BuildSize] packedAssets 정보 없음 — Editor.log의 Build Report 절을 확인하세요.");
            return;
        }

        var rows = report.packedAssets
            .SelectMany(p => p.contents)
            .GroupBy(c => c.sourceAssetPath)
            .Select(g => (path: g.Key, bytes: g.Aggregate(0ul, (sum, c) => sum + c.packedSize)))
            .OrderByDescending(r => r.bytes)
            .Take(top);

        var sb = new StringBuilder("[BuildSize] 가장 큰 에셋\n");
        foreach (var (path, bytes) in rows)
            sb.AppendLine($"{bytes / 1024f,10:F0} KB  {path}");
        Debug.Log(sb.ToString());
    }
}
```

에디터 코드라 LINQ 할당은 문제되지 않습니다. `packedAssets`는 플레이어 빌드에 직접 포함된 에셋 기준이며, **Addressables 번들 안의 에셋은 포함되지 않습니다.** 번들 크기는 `Library/com.unity.addressables/` 아래 빌드 레이아웃 리포트(Addressables 설정의 빌드 레이아웃 생성 옵션)나 `ServerData`·`aa` 폴더의 파일 크기로 확인하세요.

용량 줄이기 순서(18장 설정과 연결):

1. 리포트 상위 10개부터: 대부분 텍스처(Max Size·ASTC)와 오디오(BGM Streaming·Vorbis 품질).
2. `Resources` 폴더가 남아 있는지 검색(`t:Object` + 경로에 Resources).
3. 사용하지 않는 패키지 제거(Package Manager에서 2D 템플릿 기본 패키지 중 안 쓰는 것).
4. Managed Stripping Level 한 단계 상향 후 전체 플레이 테스트.
5. Android는 AAB로 올리면 스토어가 기기별로 분할 배포하므로, 실제 다운로드 크기는 Play Console에서 확인합니다.

### 6단계: GitHub Actions 워크플로

1. GameCI 공식 문서(game.ci)의 **Activation** 절을 따라 Unity 라이선스를 준비하고, GitHub 저장소 Settings → Secrets and variables → Actions에 `UNITY_LICENSE`, `UNITY_EMAIL`, `UNITY_PASSWORD`를 등록합니다. 라이선스 종류(Personal/Pro)에 따라 필요한 값이 다르고 절차가 바뀐 적이 있으니 반드시 최신 문서를 확인하세요.
2. Android 서명용 키스토어는 `base64 -i coinrush.keystore`(macOS) 또는 `base64 -w 0 coinrush.keystore`(Linux)로 인코딩해 Secret `ANDROID_KEYSTORE_BASE64`에 넣고, 비밀번호·별칭도 `ANDROID_KEYSTORE_PASS`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASS`로 등록합니다.
3. 저장소에 `.github/workflows/build.yml`을 추가합니다.

```yaml
# .github/workflows/build.yml
name: Build Coin Rush

on:
  push:
    tags: ['v*']          # v1.2.0 같은 태그를 푸시하면 빌드
  workflow_dispatch:       # Actions 탭에서 수동 실행

jobs:
  build:
    name: Build ${{ matrix.targetPlatform }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        targetPlatform:
          - Android
          - StandaloneWindows64   # Ubuntu 러너에서는 Mono 백엔드여야 함
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
          fetch-depth: 0     # 태그 기반 버전 계산(versioning)에 전체 이력 필요

      - uses: actions/cache@v4
        with:
          path: Library
          key: Library-${{ matrix.targetPlatform }}-${{ hashFiles('Assets/**', 'Packages/**', 'ProjectSettings/**') }}
          restore-keys: Library-${{ matrix.targetPlatform }}-

      # 액션 버전 태그(@v4 등)는 GameCI 공식 문서에서 최신 값을 확인하세요
      - uses: game-ci/unity-builder@v4
        env:                 # 라이선스 값은 액션 자체가 읽음 (Unity 프로세스로는 전달되지 않음)
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
          UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
          UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}
        with:
          targetPlatform: ${{ matrix.targetPlatform }}
          buildMethod: BuildScripts.BuildFromCommandLine
          versioning: Tag                      # v1.2.0 태그 → -buildVersion 1.2.0, -androidVersionCode 자동 계산
          # 서명: 액션이 base64를 프로젝트 폴더의 androidKeystoreName 파일로 복원하고
          #       -androidKeystoreName 등 명령행 인수로 빌드 메서드에 넘김
          androidKeystoreName: coinrush.keystore
          androidKeystoreBase64: ${{ secrets.ANDROID_KEYSTORE_BASE64 }}
          androidKeystorePass: ${{ secrets.ANDROID_KEYSTORE_PASS }}
          androidKeyaliasName: ${{ secrets.ANDROID_KEY_ALIAS }}
          androidKeyaliasPass: ${{ secrets.ANDROID_KEY_PASS }}

      # 출시별 산출물: 플레이어 빌드 + 원격 콘텐츠 + 이후 콘텐츠 업데이트의 기준이 되는 content state 파일
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: CoinRush-${{ matrix.targetPlatform }}-${{ github.ref_name }}
          path: |
            Builds/
            ServerData/
            Assets/AddressableAssetsData/*/addressables_content_state.bin
          if-no-files-found: warn
```

주의할 점:

- **워크플로의 `env`는 Unity가 실행되는 컨테이너 안으로 전달되지 않습니다**(GameCI Builder 문서의 `customParameters` 설명). 그래서 키스토어 경로·비밀번호를 `COINRUSH_KEYSTORE_*` 환경 변수로 넘기면 빌드 메서드가 받지 못하고, 러너의 `$RUNNER_TEMP`에 복원한 파일도 컨테이너에서 보이지 않습니다. 서명 정보는 위처럼 액션의 `android*` 입력으로 넘기고, `BuildScripts.ConfigureAndroidSigning`은 GameCI가 붙여 주는 `-androidKeystoreName`·`-androidKeystorePass`·`-androidKeyaliasName`·`-androidKeyaliasPass` 인수를 먼저 읽습니다(환경 변수는 로컬 빌드용 대체). 그 밖에 직접 만든 값이 필요하면 `customParameters: -myFlag value` 형식으로 넘기고 `GetArg("-myFlag")`로 읽습니다.
- 복원된 키스토어 파일은 작업 공간(프로젝트 폴더)에 생깁니다. 아티팩트 경로에 포함되지 않게 하고, 로컬 저장소의 `.gitignore`에는 `*.keystore`를 넣어 두세요.
- 빌드 메서드 클래스는 `Editor` 폴더(또는 에디터 전용 어셈블리) 안에 있어야 합니다. 이 장의 `Assets/_CoinRush/Scripts/Editor/`가 그 조건을 만족합니다.
- 인수 이름은 액션 버전에 따라 바뀔 수 있으니, 첫 실행 로그의 "Building project" 부분에서 실제 명령행을 확인하세요.
- **content state 파일은 빌드할 때마다 갱신됩니다.** 스토어에 올린 빌드와 같은 실행에서 나온 `addressables_content_state.bin`만이 그 버전의 콘텐츠 업데이트 기준이 됩니다. Actions 아티팩트는 보관 기간이 지나면 삭제되므로, 출시로 확정한 실행의 아티팩트는 GitHub Release에 첨부하거나 별도 저장소(클라우드 스토리지)에 `플랫폼/앱버전/` 경로로 옮겨 영구 보관합니다. 원격 카탈로그·번들을 쓰는 한 이 파일을 잃으면 그 버전에 대한 콘텐츠 업데이트 빌드를 만들 수 없습니다.
- 에디터에서 Build를 누르면 로컬의 content state 파일이 덮어써집니다. 출시 태그 커밋에는 CI가 만든 파일을 커밋해 두거나, 업데이트 작업 전에 보관본을 받아 **Update a Previous Build**에서 그 파일을 지정하세요.

출시·콘텐츠 업데이트·롤백 절차(요약):

1. **출시**: `v1.2.0` 태그 → CI 빌드 → 스토어에는 `Builds/`의 AAB/EXE, CDN에는 `ServerData/<플랫폼>/`을 `coinrush/<플랫폼>/`에 업로드 → 아티팩트 전체(state 파일 포함)를 `Android/1.2.0/`처럼 보관.
2. **콘텐츠 업데이트**: 보관한 `1.2.0` state 파일로 Check for Content Update Restrictions → Update a Previous Build → 새 번들과 카탈로그를 CDN에 업로드. 이전 번들은 **지우지 않습니다**(아직 새 카탈로그를 받지 않은 기기가 참조). 업로드한 파일 목록과 이전 카탈로그 파일 사본을 함께 보관합니다.
3. **롤백**: 문제가 생기면 보관해 둔 직전 카탈로그 파일(카탈로그와 `.hash`)을 다시 올려 이전 번들을 가리키게 합니다. CDN 캐시가 남아 있으면 반영이 늦으므로 카탈로그·해시 파일은 캐시 시간을 짧게 설정합니다.
4. 앱 업데이트(새 스토어 빌드)를 내면 그 버전의 state 파일이 새 기준이 됩니다. 기기에는 옛 버전 앱이 남아 있을 수 있으므로 플레이어 버전별 카탈로그 경로를 분리해 관리합니다.

- Unity 버전은 기본적으로 `ProjectSettings/ProjectVersion.txt`에서 읽습니다.
- Android 빌드는 러너 디스크 용량이 부족해 실패하는 경우가 있습니다. 로그에 "No space left on device"가 보이면 GameCI 문서의 디스크 확보 방법을 참고하세요.
- `Library` 캐시는 첫 빌드 시간을 크게 줄여 주지만, 캐시 키가 자주 바뀌면 효과가 없습니다.

### 확인하기

| 확인 항목 | 성공 기준 |
|---|---|
| Addressables 로드 | Play Mode Script **Use Existing Build**에서 스테이지·적·배경이 정상 표시 |
| 준비 전 진입 차단 | Game 씬 진입 직후 로드가 끝나기 전에는 타이틀 패널이 뜨지 않고 적도 스폰되지 않음. 주소를 일부러 틀리면 콘솔에 예외가 찍히고 Playing으로 넘어가지 않음 |
| 씬 참조 제거 | `EnemySpawner` Inspector에 `Enemy Types` 칸이 없고, 저장한 Game 씬 파일에서 `EnemyData` 에셋 GUID가 검색되지 않음 |
| 해제 | 스테이지를 3회 로드/언로드 후 Memory Profiler 스냅샷 비교 시 EnemyData·스프라이트가 누적되지 않음 |
| 원격 업데이트 | 로컬 HTTP 서버로 적 구성을 바꾸고 Update a Previous Build 후 재실행하면 반영 |
| 빌드 메뉴 | `Coin Rush/Build/Android (AAB Release)` 한 번으로 `Builds/Android/*.aab` 생성, 콘솔에 크기·상위 에셋 목록 |
| 버전 | 로컬 메뉴 빌드는 할 때마다 `bundleVersionCode`가 1씩 증가, CI 빌드는 태그에서 계산한 값 그대로 |
| 명령행 | 터미널에서 batchmode 명령이 종료 코드 0으로 끝나고, 일부러 씬 경로를 깨면 1로 끝남 |
| CI | `git tag v0.1.0 && git push origin v0.1.0` 후 Actions 탭에서 두 플랫폼 아티팩트 다운로드 가능. Android 아티팩트 안에 서명된 AAB, `ServerData/`, `addressables_content_state.bin`이 함께 들어 있음 |

## 흔한 실수

1. **에디터에선 되는데 빌드에서 로드 실패** → Play Mode Script가 Use Asset Database라 번들 문제를 못 봄, 또는 플레이어 빌드 전에 Addressables 빌드를 안 함. → Use Existing Build로 검증, 빌드 스크립트에서 `BuildPlayerContent` 명시 호출.
2. **메모리가 판마다 늘어남** → `Release` 누락, 또는 `InstantiateAsync`로 만든 것을 `Destroy`만 함. → 로드 핸들을 리스트로 모아 일괄 해제, 인스턴스는 `ReleaseInstance`(또는 프리팹 로드 + 일반 `Instantiate` 패턴).
3. **같은 에셋이 여러 번들에 중복** → 서로 다른 그룹의 에셋이 같은 텍스처·프리팹을 암시적으로 참조. → Addressables **Analyze** 도구의 중복 의존성 규칙으로 찾아 공용 그룹으로 분리.
4. **릴리스 빌드에서만 `MissingMethodException`/null** → 스트리핑이 리플렉션용 코드를 제거. → `link.xml` 또는 `[Preserve]`, 스트리핑 레벨 낮추기.
5. **Play Console 업로드 거부("버전 코드 사용됨")** → `bundleVersionCode` 미증가. → 빌드 스크립트에서 증가 또는 CI 실행 번호 주입.
6. **CI가 실패했는데 초록색으로 표시** → 빌드 실패 시에도 종료 코드 0. → `BuildResult` 확인 후 `EditorApplication.Exit(1)`.
7. **키스토어 비밀번호를 저장소에 커밋** → 유출 시 앱 서명 위험. → 로컬은 환경 변수, CI는 Secrets를 GameCI의 `android*` 입력으로 전달(워크플로 `env`는 Unity까지 전달되지 않음). 키스토어 파일 자체도 저장소 밖에 백업.
8. **콘텐츠 업데이트를 만들려는데 출시 버전의 content state 파일이 없음** → 이후 빌드가 파일을 덮어썼거나 CI 작업 공간과 함께 사라짐. → 출시 빌드마다 state 파일·`ServerData`를 플랫폼·앱 버전별로 보관.
9. **로딩 중 스테이지를 바꾸거나 씬을 닫자 `MissingReferenceException`·해제된 에셋 접근** → 여러 요청이 핸들 목록을 공유하고 `await` 뒤 유효성을 확인하지 않음. → 요청별 핸들 소유 + 세대 번호 확인(2단계 `StageLoader`).

## 연습 문제

**1. ★☆☆ 라벨로 일괄 로드**
`enemy` 라벨이 붙은 모든 `EnemyData`를 한 번에 로드해 콘솔에 이름과 `maxHp`를 출력하고, 핸들 하나로 해제하세요.

<details><summary>힌트·해설</summary>

```csharp
var h = Addressables.LoadAssetsAsync<EnemyData>("enemy", data => Debug.Log($"{data.name} {data.maxHp}"));
IList<EnemyData> all = await h.Task;
// ... 사용
Addressables.Release(h);
```
콜백은 에셋 하나가 로드될 때마다 불리고, `Task` 결과는 전체 목록입니다. `maxHp` 필드 이름은 03장 정의에 맞추세요(프로퍼티라면 그 이름으로).

</details>

**2. ★★☆ 버전 번호 정책**
`bundleVersion`은 `git describe --tags`(예: `v1.2.0`)에서, Android `bundleVersionCode`는 `major*10000 + minor*100 + patch`로 계산해 로컬·CI 모두 같은 규칙으로 정하도록 빌드 스크립트를 고치세요.

<details><summary>힌트·해설</summary>

에디터 스크립트에서 `System.Diagnostics.Process`로 `git describe --tags --abbrev=0`을 실행해 표준 출력을 읽습니다(`RedirectStandardOutput = true`, `UseShellExecute = false`). `v` 접두사를 떼고 `Version.Parse`. CI에서는 체크아웃 시 태그가 없을 수 있으니 `actions/checkout`에 `fetch-depth: 0`을 주세요. 같은 버전을 두 번 올리는 경우(재빌드)를 위해 한 자리를 빌드용으로 남기는 규칙(`*100 + build`)도 흔합니다. 이렇게 하면 `Build` 안의 `++`와 `versionCodeInjected` 분기는 제거합니다. GameCI는 `versioning: Tag`일 때 버전 코드를 `major*1000000 + minor*1000 + patch`로 따로 계산해 `-androidVersionCode`로 넘기므로, 규칙을 하나로 하려면 워크플로에서 `versioning: None`으로 두고 스크립트가 직접 계산하게 하거나, 스크립트의 공식을 GameCI와 같게 맞추세요. 한번 올린 버전 코드보다 작은 값은 다시 쓸 수 없으니 공식은 출시 전에 확정합니다.

</details>

**3. ★★☆ 다운로드 확인 로딩 화면**
원격 `Stages` 그룹의 다운로드 크기를 확인해 0보다 크면 "추가 데이터 12.3MB를 받습니다" 확인 창을 띄우고, 진행률 바와 함께 받은 뒤 스테이지를 시작하세요.

<details><summary>힌트·해설</summary>

키는 3단계에서 붙인 라벨 `stage01`을 씁니다. `Stages/Stage01` 주소 하나로는 `AssetReference`로만 연결된 배경·적이 크기 계산에 포함되지 않습니다. `var sizeH = Addressables.GetDownloadSizeAsync("stage01"); long bytes = await sizeH.Task; Addressables.Release(sizeH);` → 0보다 크면 11장 확인 창 → `var dl = Addressables.DownloadDependenciesAsync("stage01");` 후 `while (!dl.IsDone) { bar.value = dl.GetDownloadStatus().Percent; await Awaitable.NextFrameAsync(); }` → `Addressables.Release(dl)`. 실패(`dl.Status == Failed`) 시 재시도 버튼을 제공하고, 모바일 데이터 사용 경고 문구를 넣는 것이 좋습니다. 다운로드가 끝난 뒤에 `stageLoader.LoadAsync`를 호출하도록 `GameStateMachine.Start`의 순서를 바꾸면 됩니다. 라벨 대신 StageData를 먼저 로드해 `background.RuntimeKey`와 각 `enemies[i].RuntimeKey`를 `List<object>`로 모아 `GetDownloadSizeAsync((IEnumerable)keys)`에 넘기는 방식도 가능하지만, StageData 자체를 먼저 받아야 합니다.

</details>

**4. ★★★ Steam 업로드까지 자동화**
Windows 빌드가 끝나면 SteamCMD의 `app_build` 스크립트로 Steam 베타 브랜치에 업로드하는 단계를 워크플로에 추가하는 설계를 작성하세요(26장과 연결). 비밀 정보 관리, 실패 시 롤백, 수동 승인 단계를 포함하세요.

<details><summary>힌트·해설</summary>

구성 예: (1) Windows 빌드는 IL2CPP를 위해 `windows-latest` 러너 또는 self-hosted Windows에서, (2) 아티팩트를 다음 job으로 전달, (3) GitHub Environments의 **required reviewers**로 수동 승인, (4) SteamCMD 로그인에는 Steam Guard 때문에 전용 빌드 계정과 인증 파일 관리가 필요(GameCI 계열의 Steam 배포 액션 문서 참고), (5) `setlive`는 베타 브랜치에만 하고 기본 브랜치 전환은 사람이 Steamworks에서. 롤백은 이전 빌드 ID를 브랜치에 다시 지정하면 되므로, 업로드 로그의 빌드 ID를 아티팩트로 남기세요.

</details>

## 셀프 체크

**1. `Resources` 폴더를 출시 게임에서 피해야 하는 이유 세 가지를 말해보세요.**

<details><summary>모범 답안</summary>

사용 여부와 무관하게 폴더 내 모든 에셋이 빌드에 포함되어 용량이 커지고, 앱 시작 시 전체 인덱스를 구성해 시작 시간이 늘어나며, 문자열 경로라 이름 변경 시 런타임 오류가 납니다. 개별 해제와 원격 업데이트도 어렵습니다.

</details>

**2. Addressables에서 `Release`를 빼먹으면 어떤 일이 생기고, 어떻게 발견하나요?**

<details><summary>모범 답안</summary>

참조 카운트가 0이 되지 않아 에셋과 번들이 메모리에서 내려가지 않습니다. 스테이지를 반복할수록 메모리가 늘어나는 누수가 됩니다. 같은 상태에서 찍은 Memory Profiler 스냅샷을 비교해 계속 늘어나는 에셋을 찾거나, Addressables의 이벤트 뷰어·프로파일러 모듈(버전에 따라 제공)로 참조 카운트를 확인합니다.

</details>

**3. 원격 카탈로그로 업데이트할 수 있는 것과 없는 것을 구분해 설명해보세요.**

<details><summary>모범 답안</summary>

Remote 그룹에 있는 에셋 데이터(ScriptableObject 값, 스프라이트, 오디오, 기존 스크립트만 쓰는 프리팹 구성)는 번들과 카탈로그를 서버에 올려 앱 업데이트 없이 교체할 수 있습니다. C# 코드 변경과 새 스크립트가 필요한 기능은 앱 업데이트가 필요합니다. 업데이트 제한이 걸린 Local 그룹의 에셋은 **설치된 로컬 번들 자체를 고칠 수는 없지만**, 원격 카탈로그를 켜 둔 상태라면 Check for Content Update Restrictions가 바뀐 에셋을 새 Remote 그룹으로 옮기고, 기존 앱은 이후 원격 번들의 새 버전을 사용합니다(옛 로컬 번들은 기기에 남는 죽은 데이터가 됨). 단, 이 업데이트 빌드에는 출시 당시의 content state 파일이 필요합니다.

</details>

**4. 빌드 스크립트에서 `extraScriptingDefines`를 쓰는 것이 `PlayerSettings.SetScriptingDefineSymbols`보다 나은 경우는?**

<details><summary>모범 답안</summary>

데모·디버그 같은 특정 빌드에만 심볼을 넣고 싶을 때입니다. `SetScriptingDefineSymbols`는 프로젝트 설정 자체를 바꿔 이후 에디터 작업과 다른 빌드에 영향을 주고, 되돌리는 것을 잊기 쉽습니다. `extraScriptingDefines`는 해당 빌드에만 적용됩니다.

</details>

**5. GitHub의 Ubuntu 러너에서 Windows 빌드를 할 때 주의할 점과 이유는?**

<details><summary>모범 답안</summary>

Windows용 IL2CPP 빌드는 Windows의 C++ 툴체인이 필요해 Linux 러너에서는 할 수 없습니다. Ubuntu 러너에서는 Scripting Backend를 Mono로 두거나, IL2CPP가 필요하면 Windows 러너(또는 self-hosted Windows 머신)를 써야 합니다.

</details>

## 핵심 요약

- `Resources`는 프로토타입용입니다. 출시 게임은 Addressables로 **필요할 때 로드하고 다 쓰면 해제**합니다.
- 주소(키)·그룹(번들 단위와 경로)·라벨(태그)·카탈로그(매핑)를 구분하고, 함께 로드·해제되는 것끼리 그룹으로 묶습니다.
- 로드 1회 = 해제 1회. 핸들을 모아 일괄 해제하고, 풀링 대상은 "프리팹 한 번 로드 + 일반 Instantiate" 패턴을 씁니다. 비동기 로드는 요청별로 핸들을 소유하고, `await` 뒤마다 요청이 아직 유효한지 확인하며, 로드가 끝나기 전에는 게임을 시작하지 않습니다.
- Remote 그룹 + 원격 카탈로그 + content state 파일로 데이터를 앱 재심사 없이 교체할 수 있지만, 코드는 바꿀 수 없습니다.
- 출시 빌드는 IL2CPP·ARM64, 스트리핑은 낮게 시작해 `link.xml`로 보완, 정의 심볼은 빌드별로 주입합니다.
- 빌드는 `BuildPipeline.BuildPlayer` 스크립트 하나로: Addressables 빌드 → 플레이어 빌드 → 결과 확인 → 실패 시 종료 코드 1.
- CI는 GameCI(`game-ci/unity-builder`)나 Unity Build Automation. 라이선스 활성화와 Secrets 관리가 핵심이며(GameCI에서 서명 정보는 `env`가 아닌 `android*` 입력으로), 출시별 content state 파일·`ServerData`를 함께 보관합니다.

## 더 읽을거리

- Addressables 패키지 문서 (com.unity.addressables) — Unity 패키지 문서 사이트에서 "Addressables" 검색 (Content update builds, Memory management 절)
- Unity 스크립팅 API — `BuildPipeline.BuildPlayer`: https://docs.unity3d.com/ScriptReference/BuildPipeline.BuildPlayer.html
- Unity 매뉴얼 — Managed code stripping: https://docs.unity3d.com/Manual/ManagedCodeStripping.html
- Unity 매뉴얼 — Command line arguments: https://docs.unity3d.com/Manual/EditorCommandLineArguments.html
- GameCI 문서: https://game.ci/docs
