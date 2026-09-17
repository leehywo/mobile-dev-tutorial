# 20. 에디터 툴 만들기

> **이 장에서 배울 것**
> - 1인 개발에서 툴 제작이 언제 이득인지 판단하고, 속성·`OnValidate`·Gizmos로 비용이 거의 없는 개선부터 적용한다
> - UI Toolkit(`CreateInspectorGUI`)과 IMGUI(`OnInspectorGUI`) 방식의 CustomEditor, PropertyDrawer를 구현한다
> - `EditorWindow`와 `MenuItem`으로 웨이브 타임라인 편집기를 만들고, `Undo.RecordObject`·`EditorUtility.SetDirty`로 되돌리기와 저장을 올바르게 처리한다
> - `AssetDatabase`로 에셋을 생성·검색하고, CSV → `EnemyData` 일괄 임포터와 `AssetPostprocessor` 임포트 자동화를 만든다
> - 에디터 전용 코드를 Editor 폴더·asmdef·`#if UNITY_EDITOR`로 분리해 빌드 에러를 예방한다
>
> **선수 장**: 03, 12, 19 · **예상 시간**: 5~6시간 · **코인 러시 진행**: 웨이브 구간·이벤트를 막대로 끌어서 편집하는 타임라인 창, 구글 시트 CSV로 적 데이터를 한 번에 갱신하는 메뉴, 스폰 반경이 보이는 스포너, 스프라이트 임포트 설정 자동화.

## 왜 필요한가

22장에서 10분짜리 난이도 곡선을 설계하려면 `WaveData`에 구간 10개와 이벤트 여러 개를 넣고 수없이 고쳐야 합니다. 지금 방식으로는:

- Inspector 리스트에서 `Element 6`을 펼쳐 `startTime`을 `360`에서 `345`로 바꾸고, 앞 구간의 `endTime`도 **따로 찾아서** 맞춥니다. 구간 사이에 빈틈이 생겨도 한눈에 보이지 않습니다.
- 적 스탯은 구글 시트에서 밸런싱(23장)하는데, 시트 값을 적 여러 종의 `EnemyData`에 **손으로 옮겨 적습니다.** 하나를 빼먹어도 모릅니다.
- `EnemySpawner`의 스폰 반경이 화면 안쪽인지 바깥쪽인지 Play를 눌러봐야 압니다.
- 새 스프라이트를 넣을 때마다 Pixels Per Unit, Filter Mode, 압축을 다시 설정합니다(18장 체크리스트).

반복 작업 1회에 30초, 하루 40회면 한 달에 10시간이고, 손 작업은 실수를 만듭니다. 웹 개발자가 반복 작업을 npm 스크립트나 관리자 페이지로 만드는 것과 같은 이유로, 게임 개발자는 에디터를 확장합니다. 비용 순으로 보면 속성(몇 분) → `OnValidate`·Gizmos(30분) → CustomEditor·PropertyDrawer(1~2시간) → EditorWindow·임포터(반나절~)입니다. 원칙: **같은 작업을 세 번째 할 때 툴을 고려**하고, 가장 싼 단계부터 적용합니다. 툴 자체가 목적이 되지 않게 주의하세요.

## 개념

### 속성(Attribute)으로 Inspector 다듬기

| 속성 | 효과 | 예 |
|---|---|---|
| `[Header("이동")]` | 필드 위에 굵은 소제목 | 필드 그룹 구분 |
| `[Tooltip("초당 유닛")]` | 마우스를 올리면 설명 | 단위 명시 |
| `[Range(0, 1)]` | 슬라이더 + 범위 제한 | 확률, 비율 |
| `[Min(0)]` | 최솟값 제한(슬라이더 없음) | 체력, 개수 |
| `[TextArea(2, 5)]` | 여러 줄 문자열 입력 | 설명문 |
| `[ContextMenu("이름")]` | 컴포넌트 ⋮ 메뉴에 메서드 실행 항목 | 디버그 스폰, 데이터 정리 |
| `[RequireComponent(typeof(Rigidbody2D))]` | 붙일 때 필요한 컴포넌트 자동 추가, 제거 방지 | 이동 컴포넌트 |
| `[FormerlySerializedAs("oldName")]` | 필드 이름을 바꿔도 기존 저장 값 유지 | 리팩터링 |

`[FormerlySerializedAs]`(`UnityEngine.Serialization`)는 꼭 기억하세요. 직렬화 필드 이름을 바꾸면 Unity는 **다른 필드로 인식해 모든 에셋·프리팹의 값이 기본값으로 초기화**됩니다. 에러도 경고도 없습니다.

### OnValidate — 값이 바뀔 때 검사

`OnValidate()`는 에디터에서 Inspector 값이 바뀌거나 스크립트가 다시 로드될 때 호출됩니다(빌드에서는 호출되지 않음). 값 보정과 경고에 씁니다. 22장 `WaveData`가 구간 빈틈을 경고하는 것이 좋은 예입니다.

`Debug.LogWarning("player 미연결", this)`처럼 `this`를 넘기면 콘솔 메시지를 클릭했을 때 해당 오브젝트가 선택됩니다. 주의: `OnValidate` 안에서 오브젝트 생성·파괴, 컴포넌트 추가는 하지 마세요. 에셋 로드 중에도 호출되어 경고나 예측 불가 동작이 납니다. 값 보정과 로그만 합니다.

### Gizmos와 Handles

`OnDrawGizmos()`는 Scene 뷰에서 항상, `OnDrawGizmosSelected()`는 해당 오브젝트(또는 부모)가 선택됐을 때만 호출됩니다. `Gizmos`(UnityEngine)는 선·구·큐브·아이콘을 그립니다. 2D에서 원은 `Gizmos.DrawWireSphere`도 되지만, `Handles.DrawWireDisc`(UnityEditor)가 평면 원이라 깔끔하고 `Handles.Label`로 텍스트도 쓸 수 있습니다. `Handles`는 **UnityEditor 네임스페이스라 런타임 스크립트에서는 `#if UNITY_EDITOR`로 감싸야** 빌드가 됩니다.

### 에디터 코드 분리 — 가장 흔한 빌드 에러

`using UnityEditor;`가 들어간 코드가 **플레이어 빌드에 포함되면 컴파일 에러**가 납니다("The type or namespace name 'UnityEditor' could not be found"). 에디터에서는 잘 되다가 빌드 때 처음 터지므로 처음부터 분리합니다.

| 방법 | 규칙 | 언제 |
|---|---|---|
| **Editor 폴더** | 이름이 정확히 `Editor`인 폴더(어느 깊이든) 안의 스크립트는 에디터 전용 어셈블리(`Assembly-CSharp-Editor`)로 컴파일 | asmdef를 안 쓰는 프로젝트의 기본 |
| **asmdef** | Assembly Definition의 Platforms에서 **Editor만 체크** | 런타임 코드도 asmdef로 나눈 프로젝트 |
| **`#if UNITY_EDITOR`** | 런타임 스크립트 안의 에디터 전용 부분만 조건부 컴파일 | Gizmo에서 `Handles`, 런타임 코드 안의 `Undo` |

**asmdef 함정**: asmdef 어셈블리는 `Assembly-CSharp`(asmdef 없는 기본 어셈블리)를 **참조할 수 없습니다.** 런타임 스크립트에 asmdef가 없는데 에디터 폴더에만 asmdef를 만들면 에디터 코드가 `EnemyData`, `WaveData`를 찾지 못합니다. 코인 러시처럼 런타임에 asmdef를 쓰지 않는다면 **Editor 폴더만** 쓰세요. 나중에 런타임을 asmdef로 나누면(컴파일 시간 단축) 에디터 asmdef가 그 런타임 asmdef를 참조하게 합니다.

코인 러시 배치: `Scripts/Waves/WaveData.cs`, `Scripts/Data/TimeLabelAttribute.cs`(속성 정의는 필드에 붙여야 하므로 런타임), `Scripts/Enemies/EnemySpawner.cs`(Gizmo의 `Handles`만 `#if`), 나머지 에디터 코드는 `Scripts/Editor/`.

### CustomEditor — UI Toolkit과 IMGUI

특정 컴포넌트/에셋 타입의 Inspector 전체를 바꿉니다. Unity에는 두 UI 시스템이 공존합니다.

| | UI Toolkit | IMGUI |
|---|---|---|
| 메서드 | `public override VisualElement CreateInspectorGUI()` | `public override void OnInspectorGUI()` |
| 방식 | 요소 트리를 한 번 만들고 바인딩(React 컴포넌트 트리와 비슷) | 이벤트마다 즉시 모드로 다시 그림 |
| 기본 인스펙터 포함 | `InspectorElement.FillDefaultInspector(root, serializedObject, this)` | `DrawDefaultInspector()` |
| Unity 6에서 | Inspector 기본 렌더링 방식, 신규 작업에 권장 | 여전히 지원, 자료가 매우 많음 |

IMGUI 버전은 이 정도로 짧습니다(`Editor` 폴더의 `EnemySpawnerEditor.cs`, 클래스에 `[CustomEditor(typeof(EnemySpawner))]`, `Editor` 상속. `DebugSpawnBurst(int n)`은 12장 `SpawnOne()`을 n번 부르는 public 메서드로 스포너에 추가). UI Toolkit 버전은 실습 3단계에서 만듭니다.

```csharp
public override void OnInspectorGUI()
{
    DrawDefaultInspector();
    using (new EditorGUI.DisabledScope(!Application.isPlaying))   // Play 중에만 활성
        if (GUILayout.Button("적 10마리 즉시 스폰")) ((EnemySpawner)target).DebugSpawnBurst(10);   // 스포너에 추가한 테스트 메서드
}
```

### PropertyDrawer — 필드 하나의 그리기 방식

CustomEditor가 "이 컴포넌트 전체"라면 PropertyDrawer는 "이 **타입의 필드**" 또는 "이 **속성이 붙은 필드**"가 어디에 나오든 적용됩니다. 타입 드로어는 `[CustomPropertyDrawer(typeof(내구조체))]`, 속성 드로어는 `PropertyAttribute`를 상속한 속성을 만들고 `[CustomPropertyDrawer(typeof(TimeLabelAttribute))]`로 연결합니다. UI Toolkit은 `CreatePropertyGUI`, IMGUI는 `OnGUI(Rect, SerializedProperty, GUIContent)`를 오버라이드합니다.

### EditorWindow와 MenuItem

- `[MenuItem("Coin Rush/Wave Timeline %#w")]`를 정적 메서드에 붙이면 메뉴 항목이 생깁니다(`%`=Ctrl/Cmd, `#`=Shift, `&`=Alt → 단축키 Ctrl/Cmd+Shift+W).
- 경로 첫 단어가 최상위 메뉴가 됩니다(22·23장의 `Coin Rush/Balance/...`와 같은 메뉴). `Assets/...`로 시작하면 Project 창 우클릭 메뉴에 들어갑니다.
- `EditorWindow`는 UI Toolkit이면 `CreateGUI()`, IMGUI면 `OnGUI()`를 구현합니다. 막대를 그리고 마우스 드래그를 처리하는 타임라인은 **IMGUI가 짧고**, 폼 위주 창은 UI Toolkit이 편합니다.

### AssetDatabase — 에셋 파일 다루기

| API | 용도 |
|---|---|
| `AssetDatabase.FindAssets("t:EnemyData", new[] { "Assets/_CoinRush/Data" })` | 타입·이름·라벨로 검색, **GUID 배열** 반환 |
| `AssetDatabase.GUIDToAssetPath(guid)` | GUID → `Assets/...` 경로 |
| `AssetDatabase.LoadAssetAtPath<T>(path)` | 경로의 에셋 로드(없으면 null) |
| `AssetDatabase.CreateAsset(obj, path)` | `ScriptableObject.CreateInstance<T>()`로 만든 객체를 `.asset` 파일로 |
| `AssetDatabase.StartAssetEditing()` / `StopAssetEditing()` | 사이의 임포트를 모아 한 번에(대량 작업 가속). **try/finally로 짝 맞추기** |

`FindAssets` 검색 문법은 Project 창 검색창과 같습니다(`t:Prefab Slime`, `l:enemy`). 필드를 직접 바꾸는 대신 `SerializedObject`/`SerializedProperty`를 거치면 Undo·dirty·프리팹 오버라이드·다중 선택 편집이 자동으로 따라옵니다.

### Undo와 SetDirty — 변경을 "기록"하고 "저장"하기

| 수정 방식 | Undo | 저장 표시(dirty) |
|---|---|---|
| `SerializedObject` → `ApplyModifiedProperties()` | 자동 | 자동 |
| 필드 직접 수정 전에 `Undo.RecordObject(obj, "이름")` | 기록됨 | 자동 |
| 필드 직접 수정만 | **없음** | **없음 → 에디터를 닫으면 변경이 사라질 수 있음** |
| 필드 직접 수정 + `EditorUtility.SetDirty(obj)` | 없음 | 표시됨 |

사용자가 하는 편집(타임라인 드래그)은 `Undo.RecordObject`, 수백 개 에셋을 일괄 생성·갱신하는 임포터는 Undo 없이 `WithoutUndo`/`SetDirty` + `SaveAssets`가 일반적입니다.

### AssetPostprocessor — 임포트 규칙 자동화

`AssetPostprocessor`를 상속한 클래스를 Editor 폴더에 두면 임포트 파이프라인에 끼어듭니다. `OnPreprocessTexture()`에서 `assetImporter`를 `TextureImporter`로 캐스팅해 설정을 바꾸면 임포트 전에 적용됩니다. `assetImporter.importSettingsMissing`은 `.meta` 파일이 없는 **첫 임포트**일 때 true라, "처음 들어올 때만 기본값 적용, 이후 수동 변경은 존중" 규칙을 만들 수 있습니다.

## 실습: 코인 러시에 적용하기

런타임 스크립트는 기존 위치에, 에디터 스크립트는 모두 `Assets/_CoinRush/Scripts/Editor/`에 둡니다.

### 1단계: WaveData 준비와 시간 표시 속성

`WaveData`의 완성본은 22장 3단계(`Assets/_CoinRush/Scripts/Waves/WaveData.cs`)에서 확정합니다. 22장을 아직 안 했다면 아래 **최소판**으로 시작하세요. 필드 이름이 22장과 같으므로 나중에 22장 파일로 교체해도 이 장의 툴은 그대로 동작합니다. 03장 `EnemyData`는 `displayName`, `maxHp`, `contactDamage`, `moveSpeed`, `coinDrop`, `prefab` 필드를 가집니다.

```csharp
// Assets/_CoinRush/Scripts/Waves/WaveData.cs — 최소판 (22장에서 메서드·검증이 추가된 완성본으로 교체)
using System;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "WaveData", menuName = "Coin Rush/Wave Data")]
public class WaveData : ScriptableObject
{
    [Min(1f), TimeLabel] public float runDuration = 600f;
    public List<WaveSegment> segments = new List<WaveSegment>();
    public List<WaveEvent> events = new List<WaveEvent>();
}

[Serializable]
public class WaveSegment
{
    public string label = "0:00~1:00";
    [Min(0f), TimeLabel] public float startTime;
    [Min(0f), TimeLabel] public float endTime = 60f;
    [Min(0f)] public float spawnsPerSecond = 1f;
    // maxAlive는 22장 완성본에서 추가
    [Min(0.1f)] public float hpMultiplier = 1f;
    public List<SpawnEntry> entries = new List<SpawnEntry>();
}

[Serializable]
public class SpawnEntry
{
    public EnemyData enemy;
    [Min(0)] public int weight = 10;
}

public enum WaveEventType { Elite, Boss, Swarm }

[Serializable]
public class WaveEvent
{
    public string label = "Elite 3:00";
    [Min(0f), TimeLabel] public float time = 180f;
    public WaveEventType type = WaveEventType.Elite;
    public EnemyData enemy;
    [Min(1)] public int count = 1;
    // hpMultiplier, warningSeconds, warningText는 22장 완성본에서 추가
}
```

초 단위 float `345`가 "5:45"인지 매번 암산하지 않도록, 시간 필드 옆에 `m:ss`를 보여주는 속성을 만듭니다. 22장 완성본으로 교체할 때도 `[TimeLabel]`만 붙여 주면 됩니다.

```csharp
// Assets/_CoinRush/Scripts/Data/TimeLabelAttribute.cs  (런타임 폴더 — 필드에 붙이려면 런타임에 있어야 함)
using UnityEngine;

public class TimeLabelAttribute : PropertyAttribute { }
```

```csharp
// Assets/_CoinRush/Scripts/Editor/TimeLabelDrawer.cs
using UnityEditor;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;

[CustomPropertyDrawer(typeof(TimeLabelAttribute))]
public class TimeLabelDrawer : PropertyDrawer
{
    public static string Format(float seconds)
    {
        int s = Mathf.Max(0, Mathf.RoundToInt(seconds));
        return $"{s / 60}:{s % 60:00}";
    }

    // UI Toolkit (Unity 6 Inspector 기본)
    public override VisualElement CreatePropertyGUI(SerializedProperty property)
    {
        var row = new VisualElement { style = { flexDirection = FlexDirection.Row } };
        // PropertyField로 같은 속성을 그리면 이 드로어가 다시 호출되어 무한 재귀 → FloatField를 직접 바인딩
        var field = new FloatField(property.displayName) { bindingPath = property.propertyPath, tooltip = property.tooltip };
        field.AddToClassList(BaseField<float>.alignedFieldUssClassName);   // 다른 필드와 라벨 폭 정렬
        field.style.flexGrow = 1;
        var time = new Label(Format(property.floatValue)) { style = { width = 44, unityTextAlign = TextAnchor.MiddleRight } };
        field.RegisterValueChangedCallback(evt => time.text = Format(evt.newValue));
        row.Add(field);
        row.Add(time);
        return row;
    }

    // IMGUI (IMGUI 기반 에디터·창 안에서 그려질 때)
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        const float timeWidth = 44f;
        EditorGUI.BeginProperty(position, label, property);
        var fieldRect = new Rect(position.x, position.y, position.width - timeWidth, position.height);
        var timeRect = new Rect(fieldRect.xMax, position.y, timeWidth, position.height);
        property.floatValue = EditorGUI.FloatField(fieldRect, label, property.floatValue);
        EditorGUI.LabelField(timeRect, Format(property.floatValue), EditorStyles.miniLabel);
        EditorGUI.EndProperty();
    }
}
```

필드 하나에는 드로어가 **하나만** 적용되므로 `[Range]`처럼 드로어가 있는 속성과 함께 쓰면 하나가 무시됩니다(드로어 동작 방식은 버전 문서 확인). `Wave_Stage1` 에셋에서 `Start Time [345] 5:45`처럼 보이면 성공입니다.

### 2단계: 스포너에 스폰 반경 Gizmo

12장 `EnemySpawner`(22장에서는 카메라 기반 `SpawnRadius()`로 교체됨)를 선택했을 때 **화면 영역과 스폰 원**을 Scene 뷰에 그립니다. 아래 메서드를 스포너 클래스에 추가합니다. 12장 버전이면 `spawnRadius` 필드를, 22장 버전이면 `SpawnRadius()` 호출을 쓰세요.

두 도형의 **중심이 다르다**는 점이 핵심입니다. 스폰 원의 중심은 플레이어(`player.position`)지만, 화면의 중심은 **실제 카메라 위치**입니다. 17장 Cinemachine의 Damping·Lookahead는 카메라를 플레이어보다 늦게 또는 앞서 움직이고, Confiner2D는 맵 가장자리에서 카메라를 멈춥니다. 그래서 화면 사각형은 카메라 위치에 그리고, "스폰 원이 화면 밖인가"는 **플레이어에서 화면 네 모서리 중 가장 먼 모서리까지의 거리**와 반경을 비교해 판정합니다.

```csharp
// EnemySpawner — 추가 (반경 계산 한 줄은 12장/22장 버전에 맞춤)
private void OnDrawGizmosSelected()
{
    Vector3 c = player != null ? player.position : transform.position;   // 스폰 원의 중심 = 플레이어
    c.z = 0f;
    float radius = spawnRadius;          // 22장 버전: float radius = SpawnRadius(); (cam이 null이면 Camera.main 사용)

    var cam = Camera.main;
    if (cam != null && cam.orthographic)
    {
        float h = cam.orthographicSize, w = h * cam.aspect;
        Vector3 camCenter = cam.transform.position;                           // 화면의 중심 = 실제 카메라
        camCenter.z = 0f;
        Gizmos.color = new Color(0.3f, 0.8f, 1f, 0.8f);
        Gizmos.DrawWireCube(camCenter, new Vector3(w * 2f, h * 2f, 0f));     // 화면 영역 (런타임 API)

        // 플레이어에서 화면 네 모서리까지 거리 중 최댓값 — 이보다 반경이 작으면 원 일부가 화면 안
        Vector3 farCorner = camCenter;
        float farDist = -1f;
        for (int sx = -1; sx <= 1; sx += 2)
            for (int sy = -1; sy <= 1; sy += 2)
            {
                Vector3 corner = camCenter + new Vector3(sx * w, sy * h, 0f);
                float d = Vector3.Distance(c, corner);
                if (d > farDist) { farDist = d; farCorner = corner; }
            }
        Gizmos.color = radius < farDist ? Color.red : Color.green;
        Gizmos.DrawLine(c, farCorner);                                         // 가장 먼 모서리까지의 선
    }

#if UNITY_EDITOR
    UnityEditor.Handles.color = new Color(1f, 0.6f, 0.1f, 1f);
    UnityEditor.Handles.DrawWireDisc(c, Vector3.forward, radius);         // 평면 원 (에디터 API)
    UnityEditor.Handles.Label(c + Vector3.up * radius, $"spawn r={radius:F1}");
#endif
}
```

Game 뷰 해상도를 폰 비율(예: 2340x1080)로 바꾸고 스포너를 선택하면 하늘색 사각형(카메라)과 주황 원(플레이어 중심)이 보입니다. 선이 **빨간색**이면 반경이 가장 먼 화면 모서리보다 작아 적이 화면 안에서 튀어나올 수 있다는 뜻입니다. `OnDrawGizmosSelected`는 Play 중에도 그려지므로, Play 상태에서 플레이어를 맵 가장자리로 몰아 Confiner가 카메라를 멈춘 순간이나 급히 방향을 바꿔 Lookahead가 커진 순간에 선 색을 보세요. 플레이어와 카메라가 겹친 상태에서 초록이어도 이때 빨개진다면, 22장 `SpawnRadius()`의 `spawnMargin`을 그 어긋남만큼 키워야 합니다. 22장이 반경을 카메라에서 계산하게 바꾼 이유도 함께 확인할 수 있습니다.

### 3단계: WaveData 인스펙터 (UI Toolkit)

```csharp
// Assets/_CoinRush/Scripts/Editor/WaveDataEditor.cs
using System.Text;
using UnityEditor;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;

[CustomEditor(typeof(WaveData))]
public class WaveDataEditor : Editor
{
    public override VisualElement CreateInspectorGUI()
    {
        var root = new VisualElement();
        var wave = (WaveData)target;
        var openButton = new Button(() => WaveTimelineWindow.Open(wave)) { text = "타임라인 편집기 열기" };
        openButton.style.height = 28;
        root.Add(openButton);
        var warning = new HelpBox(string.Empty, HelpBoxMessageType.Warning);
        root.Add(warning);
        InspectorElement.FillDefaultInspector(root, serializedObject, this);
        void Refresh()
        {
            string msg = Validate(wave);
            warning.text = msg;
            warning.style.display = string.IsNullOrEmpty(msg) ? DisplayStyle.None : DisplayStyle.Flex;
        }
        Refresh();
        root.TrackSerializedObjectValue(serializedObject, _ => Refresh());   // 값이 바뀔 때마다 재검증
        return root;
    }

    public static string Validate(WaveData wave)
    {
        var sb = new StringBuilder();
        var segs = wave.segments;
        if (segs.Count == 0) sb.AppendLine("구간이 하나도 없음");
        if (segs.Count > 0 && !Mathf.Approximately(segs[0].startTime, 0f))
            sb.AppendLine($"첫 구간이 0:00이 아닌 {TimeLabelDrawer.Format(segs[0].startTime)}에 시작 (그 전에는 스폰 없음)");
        for (int i = 0; i < segs.Count; i++)
        {
            var s = segs[i];
            if (s.endTime <= s.startTime) sb.AppendLine($"구간 {i}: 길이가 0 이하");
            if (s.endTime > wave.runDuration + 0.001f) sb.AppendLine($"구간 {i}: runDuration({TimeLabelDrawer.Format(wave.runDuration)}) 이후까지 이어짐");
            if (i > 0 && !Mathf.Approximately(segs[i - 1].endTime, s.startTime))
                sb.AppendLine($"구간 {i - 1}~{i}: 빈틈 또는 겹침 ({TimeLabelDrawer.Format(segs[i - 1].endTime)} / {TimeLabelDrawer.Format(s.startTime)})");
            if (s.entries.Count == 0) { sb.AppendLine($"구간 {i}: 스폰 항목 없음"); continue; }
            int totalWeight = 0;
            for (int k = 0; k < s.entries.Count; k++)
            {
                if (s.entries[k].enemy == null) sb.AppendLine($"구간 {i} 항목 {k}: 적 데이터 없음");
                else totalWeight += s.entries[k].weight;   // 22장 WaveSegment.TotalWeight()와 같은 규칙
            }
            if (totalWeight <= 0) sb.AppendLine($"구간 {i}: 유효한 적의 가중치 합이 0 (아무도 스폰되지 않음)");
        }
        if (segs.Count > 0 && segs[^1].endTime < wave.runDuration - 0.001f) sb.AppendLine("마지막 구간이 runDuration 전에 끝남");
        foreach (var e in wave.events)
        {
            if (e.enemy == null) sb.AppendLine($"이벤트 '{e.label}': 적 데이터 없음");
            if (e.time >= wave.runDuration) sb.AppendLine($"이벤트 '{e.label}': 판 종료({TimeLabelDrawer.Format(wave.runDuration)}) 이후라 발생하지 않음");
        }
        return sb.ToString().TrimEnd();
    }
}
```

React로 치면 `CreateInspectorGUI`는 한 번 렌더되는 컴포넌트 트리, `TrackSerializedObjectValue`는 데이터 변경 구독입니다. IMGUI처럼 매 프레임 다시 그리지 않습니다. `Validate`를 public 정적 메서드로 둔 것은 타임라인 창과 빌드 검사에서도 재사용하기 위해서입니다.

인스펙터 경고는 "보면 고친다"에 기대므로, 잘못된 데이터가 출시 빌드에 들어가지 않게 **빌드 직전에 모든 `WaveData`를 검사해 실패시키는** 훅을 함께 둡니다. `IPreprocessBuildWithReport`를 구현한 클래스는 빌드가 시작될 때 자동으로 호출되고, `BuildFailedException`을 던지면 빌드가 중단됩니다(19장 CI 빌드도 같은 경로라 CI에서도 실패로 드러납니다).

```csharp
// Assets/_CoinRush/Scripts/Editor/WaveDataBuildCheck.cs
using System.Text;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

public class WaveDataBuildCheck : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPreprocessBuild(BuildReport report)
    {
        var failures = new StringBuilder();
        foreach (string guid in AssetDatabase.FindAssets("t:WaveData"))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var wave = AssetDatabase.LoadAssetAtPath<WaveData>(path);
            if (wave == null) continue;
            string problems = WaveDataEditor.Validate(wave);
            if (!string.IsNullOrEmpty(problems)) failures.AppendLine($"{path}\n{problems}");
        }
        if (failures.Length > 0)
            throw new BuildFailedException("[WaveData] 검증 실패 — 빌드를 중단합니다.\n" + failures);
    }
}
```

테스트용으로 일부러 비워 둔 `WaveData`까지 막히는 것이 싫다면 `FindAssets`의 두 번째 인수로 출시용 폴더(`new[] { "Assets/_CoinRush/Data/Waves" }`)만 검사하세요.

### 4단계: 웨이브 타임라인 EditorWindow

위 줄에는 **구간**이 블록으로, 아래 줄에는 **이벤트**가 마커로 표시됩니다. 경계를 끌면 앞 구간의 끝과 뒤 구간의 시작이 **함께** 움직여 빈틈이 생기지 않고(Inspector에선 두 곳을 따로 고쳐야 했던 작업), 이벤트 마커를 끌면 시각이 바뀝니다. 클릭한 항목의 상세 필드는 창 아래에 표시됩니다.

```csharp
// Assets/_CoinRush/Scripts/Editor/WaveTimelineWindow.cs
using UnityEditor;
using UnityEngine;

public class WaveTimelineWindow : EditorWindow
{
    const float RulerH = 18f, RowH = 34f, LabelW = 70f, Grab = 6f;
    const float MinSegment = 1f;   // 구간 최소 길이(초) — 스냅 간격과 분리: Snap=0이어도 길이 0·역전 구간이 생기지 않음
    enum Kind { None, Segment, Event }
    enum Drag { None, Boundary, LastEnd, Event }
    [SerializeField] WaveData wave;
    [SerializeField] float pixelsPerSecond = 2f;
    [SerializeField] float snap = 5f;
    [SerializeField] Kind selKind;
    [SerializeField] int selIndex = -1;
    Drag drag;
    int dragIndex, undoGroup;
    Vector2 scroll;
    SerializedObject so;

    [MenuItem("Coin Rush/Wave Timeline %#w")]
    public static void OpenEmpty() => GetWindow<WaveTimelineWindow>("Wave Timeline");

    public static void Open(WaveData data) => GetWindow<WaveTimelineWindow>("Wave Timeline").SetWave(data);
    void SetWave(WaveData data) { wave = data; selKind = Kind.None; selIndex = -1; so = null; Repaint(); }
    void OnEnable() => Undo.undoRedoPerformed += Repaint;   // Undo 후 다시 그리기
    void OnDisable() => Undo.undoRedoPerformed -= Repaint;
    void OnSelectionChange() { if (Selection.activeObject is WaveData w && w != wave) SetWave(w); }
    void OnGUI()
    {
        using (new EditorGUILayout.HorizontalScope(EditorStyles.toolbar))
        {
            var picked = (WaveData)EditorGUILayout.ObjectField(wave, typeof(WaveData), false, GUILayout.Width(200));
            if (picked != wave) SetWave(picked);
            GUILayout.Label("Zoom", GUILayout.Width(38));
            pixelsPerSecond = GUILayout.HorizontalSlider(pixelsPerSecond, 0.5f, 8f, GUILayout.Width(100));
            GUILayout.Label("Snap", GUILayout.Width(34));
            snap = Mathf.Max(0f, EditorGUILayout.FloatField(snap, GUILayout.Width(36)));   // 음수 입력 방지 (0 = 스냅 끔)
            GUILayout.FlexibleSpace();
            using (new EditorGUI.DisabledScope(wave == null))
            {
                bool full = wave != null && wave.segments.Count > 0 && wave.segments[^1].endTime > wave.runDuration - MinSegment;
                using (new EditorGUI.DisabledScope(full))   // 남은 시간이 최소 길이보다 짧으면 추가 불가
                    if (GUILayout.Button("+ Segment", EditorStyles.toolbarButton)) AddSegment();
                if (GUILayout.Button("+ Event", EditorStyles.toolbarButton)) AddEvent();
            }
        }
        if (wave == null) { EditorGUILayout.HelpBox("WaveData 에셋을 선택하거나 위 필드에 드래그하세요.", MessageType.Info); return; }
        if (so == null || so.targetObject != wave) so = new SerializedObject(wave);
        so.Update();
        DrawTimeline();
        string problems = WaveDataEditor.Validate(wave);
        if (!string.IsNullOrEmpty(problems)) EditorGUILayout.HelpBox(problems, MessageType.Warning);
        DrawDetails();
    }

    float X(Rect area, float t) => area.x + LabelW + t * pixelsPerSecond;
    float Snap(float t) => snap > 0f ? Mathf.Round(t / snap) * snap : t;
    void DrawTimeline()
    {
        float width = LabelW + wave.runDuration * pixelsPerSecond + 30f;
        float height = RulerH + RowH * 2f + 6f;
        scroll = EditorGUILayout.BeginScrollView(scroll, GUILayout.Height(height + 18f));
        Rect area = GUILayoutUtility.GetRect(width, height);
        Event e = Event.current;
        for (float t = 0; t <= wave.runDuration; t += 30f)   // 눈금: 30초 선, 60초 라벨
        {
            bool minute = t % 60f == 0f;
            EditorGUI.DrawRect(new Rect(X(area, t), area.y, 1f, height), new Color(1, 1, 1, minute ? 0.25f : 0.08f));
            if (minute) GUI.Label(new Rect(X(area, t) + 2f, area.y, 40f, RulerH), TimeLabelDrawer.Format(t), EditorStyles.miniLabel);
        }
        GUI.Label(new Rect(area.x + 2f, area.y + RulerH + 8f, LabelW, 18f), "Segments");
        GUI.Label(new Rect(area.x + 2f, area.y + RulerH + RowH + 8f, LabelW, 18f), "Events");
        // 구간 블록
        float segY = area.y + RulerH + 2f;
        for (int i = 0; i < wave.segments.Count; i++)
        {
            var s = wave.segments[i];
            var r = new Rect(X(area, s.startTime), segY, Mathf.Max(3f, (s.endTime - s.startTime) * pixelsPerSecond), RowH - 4f);
            Color c = Color.HSVToRGB(0.55f + 0.05f * (i % 2), 0.45f, i % 2 == 0 ? 0.65f : 0.5f);
            if (selKind == Kind.Segment && selIndex == i) c = Color.Lerp(c, Color.white, 0.35f);
            EditorGUI.DrawRect(r, c);
            GUI.Label(r, $" {s.label}\n {s.spawnsPerSecond:0.#}/s ×{s.hpMultiplier:0.##}", EditorStyles.whiteMiniLabel);
            var left = new Rect(r.x - Grab * 0.5f, r.y, Grab, r.height);
            var right = new Rect(r.xMax - Grab * 0.5f, r.y, Grab, r.height);
            if (i > 0) EditorGUIUtility.AddCursorRect(left, MouseCursor.ResizeHorizontal);
            if (i == wave.segments.Count - 1) EditorGUIUtility.AddCursorRect(right, MouseCursor.ResizeHorizontal);
            if (e.type == EventType.MouseDown && e.button == 0)
            {
                if (i > 0 && left.Contains(e.mousePosition)) BeginDrag(Drag.Boundary, i, e);
                else if (i == wave.segments.Count - 1 && right.Contains(e.mousePosition)) BeginDrag(Drag.LastEnd, i, e);
                else if (r.Contains(e.mousePosition)) { Select(Kind.Segment, i); e.Use(); }
            }
        }
        // 이벤트 마커
        float evY = area.y + RulerH + RowH + 2f;
        for (int i = 0; i < wave.events.Count; i++)
        {
            var ev = wave.events[i];
            var r = new Rect(X(area, ev.time) - 4f, evY, 8f, RowH - 4f);
            Color c = ev.type == WaveEventType.Boss ? new Color(0.9f, 0.2f, 0.2f)
                    : ev.type == WaveEventType.Elite ? new Color(0.95f, 0.6f, 0.1f) : new Color(0.6f, 0.4f, 0.9f);
            if (selKind == Kind.Event && selIndex == i) c = Color.white;
            EditorGUI.DrawRect(r, c);
            GUI.Label(new Rect(r.xMax + 2f, evY + 8f, 120f, 16f), ev.label, EditorStyles.miniLabel);
            EditorGUIUtility.AddCursorRect(r, MouseCursor.SlideArrow);
            if (e.type == EventType.MouseDown && e.button == 0 && r.Contains(e.mousePosition)) BeginDrag(Drag.Event, i, e);
        }
        HandleDrag(area, e);
        EditorGUILayout.EndScrollView();
    }
    void BeginDrag(Drag mode, int index, Event e)
    {
        drag = mode;
        dragIndex = index;
        Select(mode == Drag.Event ? Kind.Event : Kind.Segment, index);
        Undo.IncrementCurrentGroup();
        undoGroup = Undo.GetCurrentGroup();
        e.Use();
    }
    void HandleDrag(Rect area, Event e)
    {
        if (drag == Drag.None) return;
        if (e.type == EventType.MouseDrag)
        {
            float t = Snap((e.mousePosition.x - area.x - LabelW) / pixelsPerSecond);
            Undo.RecordObject(wave, "Edit Wave Timeline");
            switch (drag)
            {
                case Drag.Boundary:   // 앞 구간 끝 = 뒤 구간 시작, 두 구간 모두 MinSegment 이상 유지
                    var prev = wave.segments[dragIndex - 1];
                    var next = wave.segments[dragIndex];
                    float lo = prev.startTime + MinSegment, hi = next.endTime - MinSegment;
                    if (lo > hi) break;   // 이미 두 구간 합이 최소 길이 2배보다 짧음 → 움직이지 않음
                    prev.endTime = next.startTime = Mathf.Clamp(t, lo, hi);
                    break;
                case Drag.LastEnd:
                    var last = wave.segments[dragIndex];
                    float minEnd = last.startTime + MinSegment;
                    if (minEnd > wave.runDuration) break;   // 판 종료 직전에 시작한 구간은 늘릴 공간이 없음
                    last.endTime = Mathf.Clamp(t, minEnd, wave.runDuration);
                    break;
                case Drag.Event:
                    wave.events[dragIndex].time = Mathf.Clamp(t, 0f, wave.runDuration);
                    break;
            }
            EditorUtility.SetDirty(wave);
            e.Use();
            Repaint();
        }
        else if (e.rawType == EventType.MouseUp)   // 창 밖에서 버튼을 떼도 받도록 rawType
        {
            drag = Drag.None;
            Undo.CollapseUndoOperations(undoGroup);   // 드래그 전체를 Undo 한 번으로
            e.Use();
        }
    }
    void Select(Kind kind, int index) { selKind = kind; selIndex = index; GUI.FocusControl(null); Repaint(); }
    void DrawDetails()
    {
        string listName = selKind == Kind.Segment ? "segments" : selKind == Kind.Event ? "events" : null;
        var list = listName != null ? so.FindProperty(listName) : null;
        if (list == null || selIndex < 0 || selIndex >= list.arraySize)
        {
            EditorGUILayout.LabelField("블록이나 마커를 클릭하면 상세 설정이 여기에 표시됩니다.", EditorStyles.miniLabel);
            return;
        }
        var element = list.GetArrayElementAtIndex(selIndex);
        element.isExpanded = true;
        EditorGUILayout.PropertyField(element, new GUIContent($"{listName}[{selIndex}]"), includeChildren: true);
        if (GUILayout.Button("이 항목 삭제")) { list.DeleteArrayElementAtIndex(selIndex); selIndex = -1; }
        so.ApplyModifiedProperties();   // SerializedProperty 편집은 Undo·dirty 자동
    }
    void AddSegment()
    {
        float start = wave.segments.Count > 0 ? wave.segments[^1].endTime : 0f;
        if (start > wave.runDuration - MinSegment)   // 버튼 비활성화와 같은 조건 — 길이 0 구간 방지
        {
            ShowNotification(new GUIContent("runDuration까지 남은 시간이 없습니다"));
            return;
        }
        Undo.RecordObject(wave, "Add Segment");
        float end = Mathf.Min(start + 60f, wave.runDuration);
        wave.segments.Add(new WaveSegment { startTime = start, endTime = end, label = $"{TimeLabelDrawer.Format(start)}~{TimeLabelDrawer.Format(end)}" });
        EditorUtility.SetDirty(wave);
        Select(Kind.Segment, wave.segments.Count - 1);
    }
    void AddEvent()
    {
        Undo.RecordObject(wave, "Add Event");
        wave.events.Add(new WaveEvent { time = wave.runDuration * 0.5f });
        EditorUtility.SetDirty(wave);
        Select(Kind.Event, wave.events.Count - 1);
    }
}
```

코드 포인트: **스냅 간격과 최소 구간 길이는 다른 개념이라 분리했습니다.** 스냅은 사용자가 끄거나(0) 바꿀 수 있는 입력 편의 기능이고, `MinSegment`는 데이터가 깨지지 않게 하는 불변 조건입니다. 스냅 값을 최소 길이로 겸용하면 Snap=0에서 길이 0 구간이, 음수에서는 시작과 끝이 뒤집힌 구간이 만들어집니다. 그리고 **두 가지 수정 방식을 의도적으로 섞었습니다.** 드래그는 매 프레임 필드를 직접 바꾸므로 `Undo.RecordObject` + `SetDirty`, 상세 필드는 `SerializedProperty`로 자동 처리. 직접 수정한 값은 다음 `OnGUI`의 `so.Update()`가 다시 읽습니다. 그리고 `Undo.IncrementCurrentGroup` → 드래그 중 여러 번 `RecordObject` → `CollapseUndoOperations`로 드래그 한 번을 Ctrl/Cmd+Z 한 번에 되돌립니다.

### 5단계: CSV → EnemyData 임포터

구글 시트 첫 행을 헤더로 두고 **파일 → 다운로드 → 쉼표로 구분된 값(.csv)**으로 내보내 `Assets/_CoinRush/Data/Csv/enemies.csv`에 둡니다. 22장의 적 표와 같은 이름을 씁니다.

```
id,displayName,maxHp,moveSpeed,contactDamage,coinDrop,prefab
Enemy_Slime,슬라임,10,1.5,5,1,Enemy_Slime
Enemy_Bat,박쥐,6,3.0,4,1,Enemy_Bat
Enemy_KingGolem,"코인 골렘왕, 보스",3000,1.2,30,300,Enemy_KingGolem
```

규칙: `id`가 에셋 파일 이름(`Enemy_Slime.asset`)이 되고, 이미 있으면 **값만 갱신**합니다(GUID가 유지되어 `WaveData`의 참조가 깨지지 않음). `prefab` 열은 프리팹 이름으로 검색합니다.

```csharp
// Assets/_CoinRush/Scripts/Editor/EnemyCsvImporter.cs
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

public static class EnemyCsvImporter
{
    const string CsvPath = "Assets/_CoinRush/Data/Csv/enemies.csv";
    const string OutputFolder = "Assets/_CoinRush/Data/Enemies";

    [MenuItem("Coin Rush/Data/Import Enemies CSV")]
    public static void Import()
    {
        if (!File.Exists(CsvPath)) { Debug.LogError($"[CSV] 파일 없음: {CsvPath}"); return; }
        var rows = ParseCsv(File.ReadAllText(CsvPath, Encoding.UTF8));
        if (rows.Count < 2) { Debug.LogError("[CSV] 데이터 행이 없습니다."); return; }
        var header = rows[0];
        int Col(string name)
        {
            int i = header.IndexOf(name);
            if (i < 0) throw new InvalidDataException($"헤더에 '{name}' 열이 없습니다.");
            return i;
        }
        int cId = Col("id"), cName = Col("displayName"), cHp = Col("maxHp"), cSpeed = Col("moveSpeed"),
            cDmg = Col("contactDamage"), cCoin = Col("coinDrop"), cPrefab = Col("prefab");
        // 1단계: 모든 행을 검증만 한다 — 에셋은 아직 건드리지 않음
        var inv = CultureInfo.InvariantCulture;   // 쉼표 소수점 로케일에서도 "1.5" 파싱
        var errors = new StringBuilder();
        var valid = new List<EnemyRow>();
        var idCount = new Dictionary<string, int>();
        for (int r = 1; r < rows.Count; r++)
            if (rows[r].Count > cId && !string.IsNullOrWhiteSpace(rows[r][cId]))
            {
                string key = rows[r][cId].Trim();
                idCount[key] = idCount.TryGetValue(key, out int n) ? n + 1 : 1;
            }
        for (int r = 1; r < rows.Count; r++)
        {
            var row = rows[r];
            if (row.Count == 0 || row.TrueForAll(string.IsNullOrWhiteSpace)) continue;   // 빈 줄
            string id = row.Count > cId ? row[cId].Trim() : "";
            try
            {
                if (row.Count != header.Count)
                    throw new InvalidDataException($"열 개수 {row.Count} (헤더는 {header.Count}) — 따옴표 없는 쉼표를 확인하세요.");
                if (string.IsNullOrEmpty(id)) throw new InvalidDataException("id가 비어 있습니다.");
                if (id.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0) throw new InvalidDataException("id에 파일 이름으로 쓸 수 없는 문자가 있습니다.");
                if (idCount[id] > 1) throw new InvalidDataException($"id '{id}'가 {idCount[id]}번 중복 — 어느 행이 맞는지 모르므로 모두 건너뜁니다.");
                var item = new EnemyRow
                {
                    id = id,
                    displayName = row[cName].Trim(),
                    maxHp = ParseInt(row[cHp], "maxHp", 1, inv),               // EnemyData의 [Min]과 같은 범위
                    contactDamage = ParseInt(row[cDmg], "contactDamage", 0, inv),
                    coinDrop = ParseInt(row[cCoin], "coinDrop", 0, inv),
                    moveSpeed = ParseFloat(row[cSpeed], "moveSpeed", 0f, inv),
                    prefab = FindPrefab(row[cPrefab]),                         // 비었거나 못 찾으면 예외
                };
                if (string.IsNullOrEmpty(item.displayName)) throw new InvalidDataException("displayName이 비어 있습니다.");
                valid.Add(item);
            }
            catch (Exception ex)
            {
                errors.AppendLine($"{r + 1}행({id}): {ex.Message}");
            }
        }

        // 2단계: 검증을 통과한 행만 에셋에 쓴다
        Directory.CreateDirectory(OutputFolder);
        AssetDatabase.Refresh();   // 새 폴더를 AssetDatabase가 인식하도록 (StartAssetEditing 전에)
        int created = 0, updated = 0;
        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (var item in valid)
            {
                string path = $"{OutputFolder}/{item.id}.asset";
                var data = AssetDatabase.LoadAssetAtPath<EnemyData>(path);
                bool isNew = data == null;
                if (isNew)
                {
                    data = ScriptableObject.CreateInstance<EnemyData>();
                    AssetDatabase.CreateAsset(data, path);
                }
                var so = new SerializedObject(data);
                Set(so, "displayName").stringValue = item.displayName;
                Set(so, "maxHp").intValue = item.maxHp;
                Set(so, "moveSpeed").floatValue = item.moveSpeed;
                Set(so, "contactDamage").intValue = item.contactDamage;
                Set(so, "coinDrop").intValue = item.coinDrop;
                Set(so, "prefab").objectReferenceValue = item.prefab;
                so.ApplyModifiedPropertiesWithoutUndo();   // 일괄 작업은 Undo 기록 안 함
                if (isNew) created++; else updated++;
            }
        }
        finally
        {
            AssetDatabase.StopAssetEditing();   // 예외가 나도 반드시 호출
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"[CSV] 생성 {created}, 갱신 {updated}, 건너뜀 {rows.Count - 1 - valid.Count}(빈 줄 포함)");
        if (errors.Length > 0) Debug.LogError("[CSV] 오류 — 아래 행은 에셋에 반영하지 않았습니다\n" + errors);
    }

    class EnemyRow
    {
        public string id, displayName;
        public int maxHp, contactDamage, coinDrop;
        public float moveSpeed;
        public GameObject prefab;
    }

    static int ParseInt(string text, string column, int min, IFormatProvider inv)
    {
        if (!int.TryParse(text.Trim(), NumberStyles.Integer, inv, out int v)) throw new FormatException($"{column} '{text}'는 정수가 아닙니다.");
        if (v < min) throw new InvalidDataException($"{column}={v}는 {min} 이상이어야 합니다.");
        return v;
    }

    static float ParseFloat(string text, string column, float min, IFormatProvider inv)
    {
        if (!float.TryParse(text.Trim(), NumberStyles.Float, inv, out float v) || float.IsNaN(v) || float.IsInfinity(v))
            throw new FormatException($"{column} '{text}'는 유한한 실수가 아닙니다.");
        if (v < min) throw new InvalidDataException($"{column}={v}는 {min} 이상이어야 합니다.");
        return v;
    }

    static SerializedProperty Set(SerializedObject so, string field) =>
        so.FindProperty(field) ?? throw new MissingFieldException($"EnemyData에 '{field}' 직렬화 필드가 없습니다(03장 확인).");

    static GameObject FindPrefab(string prefabName)
    {
        if (string.IsNullOrWhiteSpace(prefabName)) throw new InvalidDataException("prefab이 비어 있습니다(null로 기존 참조를 덮어쓰지 않도록 필수).");
        prefabName = prefabName.Trim();
        foreach (string guid in AssetDatabase.FindAssets($"t:Prefab {prefabName}"))
        {
            string p = AssetDatabase.GUIDToAssetPath(guid);
            if (Path.GetFileNameWithoutExtension(p) == prefabName)   // 부분 일치("Enemy_Slime2") 제외
                return AssetDatabase.LoadAssetAtPath<GameObject>(p);
        }
        throw new FileNotFoundException($"프리팹 '{prefabName}'을 찾을 수 없습니다.");
    }

    // 따옴표 필드(쉼표 포함)와 "" 이스케이프를 지원하는 최소 CSV 파서
    public static List<List<string>> ParseCsv(string text)
    {
        var rows = new List<List<string>>();
        var row = new List<string>();
        var field = new StringBuilder();
        bool quoted = false;
        for (int i = 0; i < text.Length; i++)
        {
            char ch = text[i];
            if (quoted)
            {
                if (ch == '"' && i + 1 < text.Length && text[i + 1] == '"') { field.Append('"'); i++; }
                else if (ch == '"') quoted = false;
                else field.Append(ch);
            }
            else if (ch == '"') quoted = true;
            else if (ch == ',') { row.Add(field.ToString()); field.Clear(); }
            else if (ch == '\n' || ch == '\r')
            {
                if (ch == '\r' && i + 1 < text.Length && text[i + 1] == '\n') i++;
                row.Add(field.ToString()); field.Clear();
                rows.Add(row); row = new List<string>();
            }
            else field.Append(ch);
        }
        if (field.Length > 0 || row.Count > 0) { row.Add(field.ToString()); rows.Add(row); }
        if (rows.Count > 0 && rows[0].Count > 0) rows[0][0] = rows[0][0].TrimStart('\uFEFF');   // UTF-8 BOM 제거
        return rows;
    }
}
```

설계 포인트:
- **검증과 쓰기를 두 단계로 나눕니다.** 파싱이 된다고 올바른 값은 아닙니다. 음수 체력, `NaN` 속도, 빈 프리팹(→ 기존 정상 참조를 null로 덮어씀), 중복 id(→ 뒤 행이 앞 행을 조용히 덮어씀)는 모두 1단계에서 걸러 오류로 보고하고, 통과한 행만 2단계에서 에셋에 씁니다. `EnemyData`의 `[Min]`은 **Inspector 입력만** 보정하고 `SerializedProperty`로 쓰는 값은 막지 않으므로 임포터가 직접 범위를 검사해야 합니다.
- **필드 이름으로 `SerializedObject`를 통해 값을 씁니다.** 03장 `EnemyData`는 public 필드지만, 나중에 `[SerializeField] private` + 읽기 전용 프로퍼티로 캡슐화해도 임포터는 그대로 동작합니다.
- **삭제 후 재생성하지 않고 기존 에셋을 갱신**해 GUID를 유지합니다. 재생성하면 모든 프리팹·`WaveData`의 참조가 Missing이 됩니다.
- 시트에서 지운 행의 에셋은 자동 삭제하지 않습니다. 참조 중일 수 있으니 목록만 보고하는 것이 안전합니다(연습 문제 2).

### 6단계: 스프라이트 임포트 규칙

```csharp
// Assets/_CoinRush/Scripts/Editor/SpriteImportRules.cs
using UnityEditor;
using UnityEngine;

public class SpriteImportRules : AssetPostprocessor
{
    const string SpriteRoot = "Assets/_CoinRush/Art/Sprites/";
    const string UiRoot = "Assets/_CoinRush/Art/UI/";

    public override uint GetVersion() => 1;   // 규칙을 바꾸면 숫자를 올려 재임포트 유도

    void OnPreprocessTexture()
    {
        bool isSprite = assetPath.StartsWith(SpriteRoot), isUi = assetPath.StartsWith(UiRoot);
        if (!isSprite && !isUi) return;
        if (!assetImporter.importSettingsMissing) return;   // 첫 임포트만 — 이후 수동 조정은 존중
        var ti = (TextureImporter)assetImporter;
        ti.textureType = TextureImporterType.Sprite;
        ti.spritePixelsPerUnit = 32;
        ti.mipmapEnabled = false;
        ti.alphaIsTransparency = true;
        ti.isReadable = false;
        ti.filterMode = isSprite ? FilterMode.Point : FilterMode.Bilinear;   // 픽셀 아트 / 부드러운 UI
        var format = isUi ? TextureImporterFormat.ASTC_4x4 : TextureImporterFormat.ASTC_6x6;   // 18장 표
        int maxSize = isUi ? 2048 : 512;
        foreach (string platform in new[] { "Android", "iPhone" })   // iOS의 플랫폼 문자열은 "iPhone"
        {
            var s = ti.GetPlatformTextureSettings(platform);
            s.overridden = true;
            s.format = format;
            s.maxTextureSize = maxSize;
            ti.SetPlatformTextureSettings(s);
        }
        Debug.Log($"[Import] 스프라이트 규칙 적용: {assetPath}");
    }
}
```

스프라이트 시트(Multiple)는 자르는 작업이 필요하니 `spriteImportMode`는 건드리지 않았습니다. `importSettingsMissing` 조건 때문에 **이미 있는 텍스처에는 적용되지 않습니다.** 기존 스프라이트에 적용하려면 규칙 코드를 정적 메서드로 분리하고, `Selection.objects`의 텍스처마다 `AssetImporter.GetAtPath(path)`로 임포터를 얻어 적용한 뒤 `SaveAndReimport()`하는 `Assets/...` 메뉴를 만드세요.

### 확인하기

1. **Gizmo**: 스포너를 선택하면 카메라 위치의 화면 사각형, 플레이어 중심의 스폰 원, 가장 먼 모서리까지의 선이 보이고, 12장 반경을 5로 줄이면 선이 빨간색이 됩니다. Play 중 플레이어를 맵 가장자리로 옮기면 사각형이 Confiner에 막혀 원과 어긋나는 것이 보입니다.
2. **빌드·드로어**: PC 빌드에 `UnityEditor` 관련 컴파일 에러가 없고, `WaveData` 시간 필드 옆에 `m:ss`가 보이며 값을 바꾸면 즉시 갱신됩니다.
3. **인스펙터·빌드 검사**: 구간 하나의 `startTime`을 일부러 틀리게 하면 노란 경고 상자에 빈틈 메시지가 뜨고, 고치면 사라집니다. 스폰 항목의 `enemy`를 비우거나 이벤트 시각을 `runDuration` 이상으로 두면 경고가 뜨고, 그 상태로 빌드하면 `[WaveData] 검증 실패`로 빌드가 중단됩니다.
4. **타임라인**: 버튼으로 창이 열리고, 경계를 끌면 두 구간이 함께 바뀌며 5초 단위로 스냅됩니다. Snap을 0으로 두고 경계를 구간 시작점까지 끌어도 구간이 1초 아래로 줄어들지 않고, 마지막 구간이 `runDuration`에 닿으면 `+ Segment`가 비활성화됩니다. 이벤트 마커를 끌 수 있고, Ctrl/Cmd+Z 한 번에 드래그 전체가 되돌아갑니다. Unity를 재시작해도 변경이 남아 있습니다.
5. **CSV**: `Coin Rush/Data/Import Enemies CSV` → 콘솔 `[CSV] 생성 3, 갱신 0, 건너뜀 0`. 시트에서 슬라임 maxHp를 12로 바꿔 다시 실행 → `생성 0, 갱신 3`, 값 12, `WaveData`의 슬라임 참조 유지. 박쥐 maxHp를 `-5`로, prefab 칸을 빈칸으로 바꿔 실행하면 오류 로그에 두 사유가 나오고 `Enemy_Bat` 에셋은 이전 값·프리팹 참조를 그대로 유지합니다.
6. **임포트 규칙**: `Art/Sprites/`에 새 PNG를 넣으면 Sprite, PPU 32, Point, Android ASTC 6x6로 설정됩니다.

## 흔한 실수

1. **에디터에선 되는데 빌드하면 `UnityEditor` 컴파일 에러** → 런타임 폴더 스크립트에서 `using UnityEditor` 또는 `Handles` 사용. → Editor 폴더로 옮기거나 `#if UNITY_EDITOR`로 감싸기.
2. **에디터 asmdef를 만들었더니 `WaveData`를 못 찾음** → asmdef는 `Assembly-CSharp`를 참조할 수 없음. → asmdef 삭제 후 Editor 폴더만 쓰거나, 런타임도 asmdef로 분리해 참조 추가.
3. **툴로 바꾼 값이 재시작 후 사라짐** → 필드 직접 수정 후 `SetDirty`/`Undo.RecordObject` 없음. → 둘 중 하나 호출, 일괄 작업 후 `AssetDatabase.SaveAssets()`.
4. **필드 이름 리팩터링 후 모든 데이터가 0** → 직렬화 이름 변경. → `[FormerlySerializedAs("이전이름")]`, 모든 에셋이 다시 저장된 뒤 제거.
5. **PropertyDrawer에서 Unity가 멈추거나 스택 오버플로** → 드로어 안에서 같은 속성을 `PropertyField`로 그려 드로어가 재귀 호출. → `FloatField` 등 기본 필드를 직접 바인딩.

## 연습 문제

**1. ★☆☆ 구간 라벨 자동 갱신**
타임라인에서 경계 드래그를 마치면(MouseUp) 영향받은 구간의 `label`을 `"5:00~6:00"` 형식으로 다시 만들고, 이 변경도 같은 Undo 그룹에 포함되게 하세요.

<details><summary>힌트·해설</summary>

`HandleDrag`의 MouseUp 분기에서 `CollapseUndoOperations` **전에** `Undo.RecordObject(wave, "Edit Wave Timeline")` 후 `foreach (var s in wave.segments) s.label = $"{TimeLabelDrawer.Format(s.startTime)}~{TimeLabelDrawer.Format(s.endTime)}";`, `SetDirty`. 같은 그룹 안에서 기록되므로 Undo 한 번에 시각과 라벨이 함께 돌아갑니다.

</details>

**2. ★★☆ 드라이런과 고아 에셋 보고**
CSV 임포터에 "Dry Run" 메뉴를 추가해 실제로 쓰지 않고 바뀔 값(이전 → 새 값)만 로그로 출력하고, CSV에 없는 `EnemyData` 에셋 목록도 보고하세요.

<details><summary>힌트·해설</summary>

`Import(bool dryRun)`으로 바꾸고, 1단계(검증)는 그대로 실행한 뒤 dryRun이면 2단계에서 `CreateAsset`/`Apply`를 건너뛰고 `SerializedProperty`의 현재 값과 `EnemyRow` 값을 비교해 다를 때만 기록합니다. 검증 오류도 함께 출력하면 실제 임포트에서 어떤 행이 빠질지 미리 알 수 있습니다. 고아 에셋은 `AssetDatabase.FindAssets("t:EnemyData", new[] { OutputFolder })`로 모은 경로 `HashSet`에서 CSV id로 만든 경로를 빼면 됩니다. 23장 밸런싱 때 시트와 에셋이 어긋나는 사고를 막아 줍니다.

</details>

**3. ★★★ 위협 곡선 미리보기**
타임라인 아래에 22장의 "위협(HP/초) = 스폰율 × 평균 체력 × 체력 배율" 그래프를 그리고, 이벤트 시각에는 이벤트 적의 총 체력만큼 막대를 겹쳐 표시하세요. 22장의 `Threat Curve Report` 메뉴와 같은 계산 함수를 공유하도록 리팩터링하는 것까지 해 보세요.

<details><summary>힌트·해설</summary>

구간마다 `평균 체력 = Σ(weight × maxHp) / Σweight`, `위협 = spawnsPerSecond × 평균 체력 × hpMultiplier`를 계산하는 정적 함수를 런타임 쪽 `WaveMath`에 두고 창과 22장 리포트가 함께 씁니다. 그래프는 `GUILayoutUtility.GetRect`로 영역을 받아 구간마다 `EditorGUI.DrawRect`로 막대를 그리고, 가로 좌표는 타임라인의 `X()`와 같은 식·같은 `scroll.x`를 써야 위아래가 정렬됩니다.

</details>

## 셀프 체크

**1. `OnDrawGizmos`와 `OnDrawGizmosSelected`는 각각 언제 쓰나요? `Handles`를 쓸 때 주의할 점은?**

<details><summary>모범 답안</summary>

`OnDrawGizmos`는 선택 여부와 무관하게 항상 그리므로 스폰 포인트 아이콘처럼 전체 배치를 볼 때, `OnDrawGizmosSelected`는 선택했을 때만 그리므로 반경·범위처럼 화면을 어지럽히는 정보에 씁니다. `Handles`는 `UnityEditor` 네임스페이스라 런타임 스크립트에서 쓰면 빌드 에러가 나므로 `#if UNITY_EDITOR`로 감쌉니다.

</details>

**2. 에디터 툴에서 `target`의 필드를 직접 바꾸는 것과 `SerializedObject`로 바꾸는 것의 차이는?**

<details><summary>모범 답안</summary>

`SerializedObject`/`SerializedProperty`로 바꾸고 `ApplyModifiedProperties`를 호출하면 Undo 기록, dirty 표시(저장), 프리팹 오버라이드 표시, 다중 선택 편집이 자동으로 처리됩니다. 필드를 직접 바꾸면 `Undo.RecordObject`와 `EditorUtility.SetDirty`를 직접 호출해야 하고, 빠뜨리면 저장되지 않거나 되돌릴 수 없습니다.

</details>

**3. 에디터 전용 asmdef를 만들었는데 런타임 클래스를 찾지 못하는 이유와 해결책은?**

<details><summary>모범 답안</summary>

asmdef로 정의된 어셈블리는 asmdef가 없는 기본 어셈블리 `Assembly-CSharp`를 참조할 수 없습니다. 런타임 스크립트가 `Assembly-CSharp`에 있으면 에디터 asmdef에서 보이지 않습니다. asmdef 없이 `Editor` 폴더 규칙만 쓰거나, 런타임 코드도 asmdef로 분리해 에디터 asmdef가 참조하게 합니다.

</details>

**4. CSV 임포터가 에셋을 "삭제 후 재생성"하지 않고 "기존 에셋 갱신"을 해야 하는 이유는?**

<details><summary>모범 답안</summary>

에셋 참조는 `.meta` 파일의 GUID로 연결됩니다. 삭제 후 재생성하면 새 GUID가 발급되어 그 에셋을 참조하던 `WaveData`, 프리팹, Addressables 그룹 항목이 모두 Missing이 됩니다. 같은 경로의 에셋을 로드해 값만 갱신하면 GUID가 유지됩니다.

</details>

## 핵심 요약

- 같은 작업을 세 번째 할 때 툴을 고려하고, 속성 → `OnValidate`/Gizmos → CustomEditor/PropertyDrawer → EditorWindow·임포터 순으로 싼 것부터 적용합니다.
- 에디터 코드는 `Editor` 폴더, 런타임 안의 에디터 코드는 `#if UNITY_EDITOR`. asmdef는 `Assembly-CSharp`를 참조할 수 없습니다.
- CustomEditor·PropertyDrawer는 UI Toolkit(한 번 만들고 바인딩)과 IMGUI(즉시 모드) 두 방식이 있고, 마우스로 그리는 타임라인은 IMGUI가 간결합니다.
- 편집은 `SerializedObject`(자동 Undo·dirty) 또는 `Undo.RecordObject` + `SetDirty`. 드래그는 Undo 그룹으로 묶습니다.
- 외부 데이터 임포터는 기존 에셋을 갱신해 GUID를 유지하고, `StartAssetEditing`은 try/finally로 감쌉니다.
- `AssetPostprocessor`로 임포트 설정을 자동화하고, `importSettingsMissing`으로 첫 임포트에만 적용합니다.

## 더 읽을거리

- Unity 매뉴얼 — Editor Windows: https://docs.unity3d.com/Manual/editor-EditorWindows.html
- Unity 매뉴얼 — Special folder names (Editor 폴더): https://docs.unity3d.com/Manual/SpecialFolders.html
- Unity 스크립팅 API — `AssetPostprocessor`: https://docs.unity3d.com/ScriptReference/AssetPostprocessor.html
- Unity 스크립팅 API — `Undo`: https://docs.unity3d.com/ScriptReference/Undo.html
- Unity 매뉴얼 — Assembly definitions: https://docs.unity3d.com/Manual/ScriptCompilationAssemblyDefinitionFiles.html
