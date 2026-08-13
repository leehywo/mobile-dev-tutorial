# React 개발자를 위한 Unity (C#) 튜토리얼 (완전판)

> **이미 React/JS를 아는 웹 개발자**가 Unity로 게임·인터랙티브 앱을 만들기 위한 입문서.
> 네이티브 트랙과 달리 이번엔 **언어(C#)도, 패러다임(게임 루프)도 바뀝니다.**
> 하지만 좋은 소식: C#은 TypeScript와 사촌지간이고(같은 설계자 Anders Hejlsberg),
> Unity의 최신 UI 시스템(UI Toolkit)은 **CSS/Flexbox 기반**이라 웹 개발자에게 오히려 유리합니다.
>
> 같은 시리즈: [Android 트랙(Kotlin/Compose)](./android-kotlin-compose.md) · [iOS 트랙(Swift/SwiftUI)](./ios-swift-swiftui.md) · [트랙 선택 가이드(README)](./README.md)

---

## 목차

- 시작 전에: Unity를 선택해야 하는 경우 (그리고 아닌 경우)
- PART 0: 개발 환경 세팅
- PART 1: C# 문법 — TypeScript 개발자의 지름길
- PART 2: 멘탈 모델 — React vs Unity (가장 중요한 파트!)
- PART 3: 샘플 4종 만들기 (카운터 → 할일 → 날씨 → 미니 게임)
- PART 4: 실전 (모바일 빌드·인앱결제/구독·성능)
- PART 5: React 개발자가 자주 밟는 지뢰
- 부록: 다음 단계 & 리소스

---

# 시작 전에: Unity를 선택해야 하는 경우

Unity는 "앱 프레임워크"가 아니라 **게임 엔진**입니다. 선택 기준이 RN/네이티브와 완전히 다릅니다.

```
✅ Unity가 맞는 경우:
- 2D/3D 게임
- 물리 시뮬레이션, 파티클, 애니메이션이 핵심인 인터랙티브 콘텐츠
- AR/VR (Vision Pro, Quest, ARCore/ARKit)
- 한 코드로 모바일 + PC + 콘솔 + 웹(WebGL) 동시 출시

❌ Unity가 아닌 경우:
- 폼, 리스트, 네비게이션 중심의 "일반 앱" (→ RN 또는 네이티브)
  · 앱 용량이 기본 30MB+, 배터리 소모 큼, OS 네이티브 UX와 이질적
- 텍스트/스크롤 중심 콘텐츠 앱 (→ RN)
- OS 깊숙한 기능(위젯, 백그라운드 서비스) 중심 앱 (→ 네이티브)
```

> **비용**: Unity Personal은 무료입니다 (연 매출/펀딩 $200K 미만).
> 2023년 논란이 됐던 "런타임 요금(설치당 과금)"은 **2024년에 완전 철회**되었습니다.

---

# PART 0: 개발 환경 세팅

## 0-1. Unity Hub + Unity 에디터 설치

Unity Hub = 여러 Unity 버전과 프로젝트를 관리하는 런처입니다 (nvm + 프로젝트 목록 느낌).

```
1. https://unity.com/download 에서 Unity Hub 설치
2. Unity Hub 실행 → Installs → "Install Editor"
3. 버전 선택: Unity 6 LTS (6000.x) — LTS = Node LTS와 같은 개념
4. 모듈 선택 (중요! 모바일 빌드에 필수):
   ✅ Android Build Support
      ✅ Android SDK & NDK Tools
      ✅ OpenJDK
   ✅ iOS Build Support (Mac인 경우)
   ✅ 문서/언어팩은 취향껏
5. 설치 (약 10~20GB, 시간 걸림)
```

> **Android Studio를 이미 설치했어도** Unity는 자체 SDK/NDK를 쓰는 게 정신 건강에 좋습니다.
> 버전 충돌이 잦아서 Unity 공식 권장도 "Hub에서 모듈로 설치"입니다.
> iOS 빌드는 네이티브 트랙과 마찬가지로 **macOS + Xcode 필수**입니다.

## 0-2. 코드 에디터

```
선택지:
1. VS Code (웹 개발자에게 익숙, 무료)
   → 확장 "Unity" (Microsoft 공식) 설치
   → .NET SDK 설치 필요 (https://dotnet.microsoft.com)
2. JetBrains Rider (유료, Unity 지원 최강 — 본격적으로 할 거면 추천)
3. Visual Studio (Windows이면 무난한 기본값)

Unity 에디터 연결:
Edit → Preferences → External Tools → External Script Editor에서 선택
```

## 0-3. 첫 프로젝트 생성 & 실행 테스트

```
1. Unity Hub → Projects → "New Project"
2. 템플릿: "Universal 2D" 선택 (URP = 최신 렌더 파이프라인)
3. Project name: HelloUnity → "Create Project"
4. 에디터가 열리면 상단 가운데 ▶ (Play) 버튼 클릭
5. 빈 화면이라도 에러 없이 Game 뷰로 전환되면 성공!
```

**에디터 화면 구성 (웹 개발 도구와 비교):**

```
Hierarchy 창   = DOM 트리 (현재 씬의 모든 오브젝트 목록)
Scene 뷰       = 디자인 캔버스 (마우스로 직접 배치/편집)
Game 뷰        = 실제 브라우저 화면 (플레이어가 보는 것)
Inspector 창   = 개발자도구의 Elements > Styles 패널 (선택한 오브젝트의 속성 편집)
Project 창     = 파일 탐색기 (Assets 폴더 = src/)
Console 창     = 브라우저 콘솔 (Debug.Log 출력, 에러)
```

## 0-4. Claude Code 활용

네이티브 트랙과 동일하게 `Assets/` 폴더가 있는 프로젝트 루트에서 `claude`를 실행하세요.
C# 컴파일 에러, "왜 안 움직이지?" 류의 질문에 특히 강력합니다.
단, **씬(.unity)과 프리팹(.prefab) 파일은 YAML이라 에디터에서 직접 편집하는 게 원칙**이고,
Claude에게는 C# 스크립트와 개념 설명을 맡기는 분업이 효율적입니다.

---

# PART 1: C# 문법 — TypeScript 개발자의 지름길

C#은 TypeScript와 설계자가 같아서(Anders Hejlsberg) TS를 안다면 절반은 먹고 들어갑니다.
"타입이 선택이 아니라 필수인 TS"라고 생각하면 대부분 맞습니다.

## 1-1. 변수와 타입

```typescript
// TypeScript
const name: string = "홍길동"
let age: number = 25
let scores: number[] = [90, 85]
```

```csharp
// C#
string name = "홍길동";        // 세미콜론 필수!
int age = 25;                  // 정수는 int, 소수는 float/double
float speed = 5.5f;            // ⚠️ float 리터럴은 f 접미사 필수
int[] scores = { 90, 85 };     // 고정 배열
List<int> list = new() { 90, 85 };  // 가변 배열 (JS 배열과 비슷)

var auto = "타입 추론";         // var = 타입 추론 (JS의 var과 전혀 다름!)
const int MAX = 100;           // const는 컴파일 타임 상수만 (JS const보다 좁음)
```

> **주의 3가지**: ① 세미콜론 필수 ② `float`엔 `f` 접미사 ③ C#의 `var`는 타입 추론(TS의 타입 생략과 동일), `const`는 리터럴 상수 전용.
> "재할당 안 할 변수"는 그냥 일반 선언으로 쓰고, 필드라면 `readonly`를 씁니다.

## 1-2. 함수 (메서드)

```typescript
// TypeScript
function greet(name: string): string {
    return `안녕, ${name}`
}
const double = (x: number) => x * 2
```

```csharp
// C# — 함수는 항상 클래스 안에 있어야 함 (메서드)
string Greet(string name)
{
    return $"안녕, {name}";    // 문자열 보간: $"...{변수}"
}

// 화살표 함수와 비슷한 표현식 바디
int Double(int x) => x * 2;

// 람다 (콜백으로 넘길 때)
Func<int, int> triple = x => x * 3;
Action<string> log = msg => Debug.Log(msg);   // 반환값 없으면 Action
```

> 관례: C# 메서드/프로퍼티는 **PascalCase** (`GetUser`), 지역 변수는 camelCase.
> JS 습관대로 `getUser`라고 쓰면 동작은 하지만 코드 리뷰에서 지적받는 수준의 컨벤션 위반입니다.

## 1-3. 클래스와 프로퍼티

```typescript
// TypeScript
class User {
    constructor(public name: string, private age: number) {}
    get isAdult() { return this.age >= 20 }
}
```

```csharp
// C#
public class User
{
    public string Name { get; set; }          // 자동 프로퍼티 (getter+setter)
    private int age;

    public User(string name, int age)
    {
        Name = name;
        this.age = age;
    }

    public bool IsAdult => age >= 20;          // getter 프로퍼티
}

var user = new User("홍길동", 25);             // new 필수 (Kotlin과 달리)
```

## 1-4. 배열 조작 — LINQ = JS 배열 메서드

```typescript
// TypeScript
nums.map(x => x * 2)
nums.filter(x => x > 3)
nums.find(x => x > 3)
nums.reduce((sum, x) => sum + x, 0)
nums.some(x => x > 3)
nums.includes(3)
```

```csharp
// C# — using System.Linq; 필요
nums.Select(x => x * 2)        // map
nums.Where(x => x > 3)         // filter  ⚠️ 이름이 다름!
nums.FirstOrDefault(x => x > 3)  // find
nums.Sum()                     // reduce(합계라면)
nums.Any(x => x > 3)           // some
nums.Contains(3)               // includes

// Select/Where는 지연 평가(lazy) — 결과를 리스트로 쓰려면:
var doubled = nums.Select(x => x * 2).ToList();
```

> **이름 대응만 외우면 됩니다**: map→`Select`, filter→`Where`, find→`FirstOrDefault`, some→`Any`.
> 단, 매 프레임 실행되는 `Update()` 안에서 LINQ는 GC 부담이 있으니 피하세요 (PART 5 참고).

## 1-5. null 처리

```csharp
// C# — Kotlin/Swift와 유사한 nullable 참조 타입
string? nickname = null;              // ? = null 허용
Debug.Log(nickname?.Length);          // 옵셔널 체이닝 (JS와 동일)
Debug.Log(nickname ?? "기본값");       // null 병합 (JS와 동일)

// ⚠️ Unity 특수 사항: 파괴된 GameObject는 == null이 true가 되도록
// 연산자가 오버로드되어 있음. 그래서 Unity 오브젝트에는
// ?. 나 ?? 대신 명시적 null 체크(if (obj != null))를 쓰는 게 안전합니다.
```

## 1-6. 비동기 처리

```typescript
// TypeScript
async function fetchData(): Promise<Data> {
    const res = await fetch(url)
    return await res.json()
}
```

```csharp
// C# — async/await이 JS와 거의 동일 (Promise = Task)
async Task<Data> FetchData()
{
    var response = await httpClient.GetStringAsync(url);
    return JsonUtility.FromJson<Data>(response);
}

// Unity에서는 3가지 방식이 공존:
// 1. 코루틴 (전통 방식): IEnumerator + yield return
// 2. async/await + Awaitable (Unity 6 권장)
// 3. UniTask (사실상 표준인 서드파티 라이브러리)
// → PART 3의 날씨 앱에서 실제 코드로 비교합니다.
```

## 1-7. 문법 연습

```
브라우저에서 바로 C# 실행:
→ https://dotnetfiddle.net
→ 위 예제들을 직접 쳐보세요 (10~20분)
```

---

# PART 2: 멘탈 모델 — React vs Unity (가장 중요한 파트!)

문법보다 이게 어렵습니다. **React는 선언형, Unity는 명령형 + 게임 루프**입니다.

## 2-1. 근본 차이: 리렌더 vs 게임 루프

```
React 멘탈 모델:
  state 변경 → 리렌더 → UI = f(state)
  "상태를 바꾸면 화면은 알아서 따라온다"

Unity 멘탈 모델:
  매 프레임(초당 60회) Update()가 호출됨
  → 오브젝트의 속성(위치, 회전 등)을 코드로 직접 바꿈
  "화면은 살아있는 오브젝트들이고, 나는 매 프레임 그들을 조종한다"
```

```csharp
// React라면: <div style={{ left: x }}> 에 state x를 바인딩
// Unity는: 매 프레임 직접 이동시킴
void Update()
{
    // Time.deltaTime = 지난 프레임 이후 경과 시간 (프레임레이트 독립적 이동의 핵심)
    transform.position += Vector3.right * speed * Time.deltaTime;
}
```

> React의 "UI = f(state)"를 버리는 게 아니라, **UI에는 그대로 적용하고
> 게임 월드에는 루프 사고방식을 새로 배우는 것**입니다. UI Toolkit 파트에서 다시 만납니다.

## 2-2. 구조 매핑

| React 개념 | Unity 개념 | 비고 |
|-----------|-----------|------|
| 컴포넌트 트리 (DOM) | Hierarchy의 GameObject 트리 | 부모-자식 구조 동일 |
| 컴포넌트 | GameObject + 붙어있는 Component들 | GameObject는 빈 껍데기, 기능은 Component가 |
| 커스텀 훅/로직 | MonoBehaviour 스크립트 | C# 클래스를 GameObject에 부착 |
| props | `[SerializeField]` 필드 | Inspector에서 값 주입 (에디터가 props를 넘겨줌) |
| state | 그냥 클래스 필드 | 바꾸면 즉시 반영 (리렌더 개념 없음) |
| `useEffect(fn, [])` | `Start()` | 첫 프레임 직전 1회 |
| `useEffect` cleanup | `OnDestroy()` | 오브젝트 파괴 시 |
| 렌더 루프 | `Update()` | 매 프레임 호출 |
| 재사용 가능한 컴포넌트 정의 | Prefab (프리팹) | "인스턴스화 가능한 GameObject 템플릿" |
| `<Component />` 렌더 | `Instantiate(prefab)` | 코드로 프리팹 복제 생성 |
| 컴포넌트 unmount | `Destroy(gameObject)` | |
| Context / 전역 상태 | ScriptableObject, static, 싱글턴 | |
| 이벤트 (`onClick`) | UnityEvent, C# event, 버튼 콜백 | |
| npm | UPM (Unity Package Manager) | Window → Package Manager |
| package.json | Packages/manifest.json | 구조도 거의 같음 |
| 페이지 라우팅 | Scene 전환 (`SceneManager.LoadScene`) | |
| localStorage | PlayerPrefs | API도 비슷함 |
| CSS | USS (UI Toolkit 스타일시트) | 문법이 거의 CSS |
| JSX | UXML (UI Toolkit 마크업) | 문법이 거의 HTML |

## 2-3. 생명주기 (useEffect의 분해)

```csharp
public class Player : MonoBehaviour
{
    void Awake()   { }  // 생성 직후 (다른 오브젝트 참조 전 초기화)
    void Start()   { }  // 첫 프레임 직전 1회 = useEffect(fn, [])
    void Update()  { }  // 매 프레임 = 게임 로직의 심장
    void FixedUpdate() { }  // 고정 간격(물리 연산 전용, 기본 0.02초)
    void OnEnable()  { }    // 활성화될 때마다 (이벤트 구독 위치)
    void OnDisable() { }    // 비활성화될 때마다 (구독 해제 위치)
    void OnDestroy() { }    // 파괴 시 = cleanup 함수
}
```

## 2-4. props 주입 = Inspector

```csharp
public class Enemy : MonoBehaviour
{
    // React: <Enemy speed={5} target={player} />
    // Unity: 필드를 Inspector에 노출하고 에디터에서 드래그/입력
    [SerializeField] private float speed = 5f;
    [SerializeField] private Transform target;
}
```

> `[SerializeField]` = "private이지만 Inspector에는 보여줘".
> public 필드도 노출되지만, 캡슐화를 위해 `[SerializeField] private`이 관례입니다.
> **코드 수정 없이 에디터에서 값을 튜닝**할 수 있다는 게 Unity 워크플로우의 핵심입니다.

## 2-5. UI 시스템 선택 (중요)

```
Unity에는 UI 시스템이 2개 공존합니다:

1. UGUI (전통) — GameObject 기반, Canvas에 배치, 자료 많음
2. UI Toolkit (최신) — UXML(HTML) + USS(CSS) + C#, 웹과 거의 동일한 모델

웹 개발자 추천: UI Toolkit
- USS는 Flexbox 레이아웃 (RN과 동일하게 기본 flex-direction: column)
- 클래스 선택자, :hover, transition 등 CSS 지식 대부분 재사용
- 단, 게임 월드 안에 띄우는 UI(캐릭터 머리 위 체력바 등)는 아직 UGUI가 편함

이 튜토리얼: STEP 1~3은 UI Toolkit, STEP 4(게임)는 UGUI를 씁니다. 둘 다 겪어보는 구성.
```

---

# PART 3: 샘플 4종 만들기

## STEP 1: Hello World + 카운터 (UI Toolkit)
**목표**: UXML/USS/C# 3분할 구조 이해 — 웹의 HTML/CSS/JS와 대응

### 파일 구성

```
// 웹 프로젝트              →  Unity UI Toolkit
index.html                 →  CounterView.uxml
style.css                  →  CounterView.uss
main.js                    →  CounterController.cs
```

### 1) UXML — 마크업 (Assets/UI/CounterView.uxml)

```xml
<ui:UXML xmlns:ui="UnityEngine.UIElements">
    <!-- HTML: <div class="container"> -->
    <ui:VisualElement class="container">
        <ui:Label text="안녕하세요!" class="title" />
        <ui:Label name="count-label" text="카운트: 0" />
        <ui:Button name="count-button" text="클릭!" class="button" />
    </ui:VisualElement>
</ui:UXML>
```

### 2) USS — 스타일 (Assets/UI/CounterView.uss)

```css
/* 거의 CSS! 웹 지식 그대로 사용 */
.container {
    flex-grow: 1;
    align-items: center;
    justify-content: center;
}

.title {
    font-size: 24px;
    -unity-font-style: bold;   /* 일부 속성만 -unity- 접두사 */
    margin-bottom: 16px;
}

.button {
    padding: 8px 24px;
    background-color: rgb(59, 130, 246);
    color: white;
    border-radius: 8px;
}
```

### 3) C# — 로직 (Assets/Scripts/CounterController.cs)

```csharp
using UnityEngine;
using UnityEngine.UIElements;

public class CounterController : MonoBehaviour
{
    private int count = 0;   // useState 대신 그냥 필드

    void OnEnable()
    {
        // document.querySelector와 동일한 개념
        var root = GetComponent<UIDocument>().rootVisualElement;
        var label = root.Q<Label>("count-label");     // Q = query
        var button = root.Q<Button>("count-button");

        // JS: button.addEventListener("click", ...)
        button.clicked += () =>
        {
            count++;
            // React와 달리 자동 리렌더가 없으므로 직접 갱신
            label.text = $"카운트: {count}";
        };
    }
}
```

### 4) 씬에 연결

```
1. Hierarchy 우클릭 → UI Toolkit → UI Document 생성
2. Inspector에서 Source Asset에 CounterView.uxml 지정
3. 같은 오브젝트에 CounterController.cs를 드래그해서 부착 (Add Component)
4. ▶ Play → 버튼 클릭 시 카운트 증가하면 성공!
```

> **핵심 차이 체감**: React는 `setCount(c+1)`만 하면 UI가 따라오지만,
> Unity는 **상태 변경과 UI 갱신이 별개**입니다. 이 "수동 바인딩"이 처음엔 퇴보처럼
> 느껴지지만, 게임에서는 상태가 초당 수백 번 바뀌므로 이 모델이 오히려 성능에 유리합니다.

---

## STEP 2: 할 일 목록 (UI Toolkit ListView)
**목표**: 리스트 렌더링, 사용자 입력, CRUD — RN의 FlatList에 해당하는 ListView

### UXML (Assets/UI/TodoView.uxml)

```xml
<ui:UXML xmlns:ui="UnityEngine.UIElements">
    <ui:VisualElement class="container">
        <ui:VisualElement class="input-row">
            <ui:TextField name="todo-input" class="input" />
            <ui:Button name="add-button" text="추가" />
        </ui:VisualElement>
        <!-- FlatList/LazyColumn에 해당. 가상화(virtualization) 내장 -->
        <ui:ListView name="todo-list" class="list" />
    </ui:VisualElement>
</ui:UXML>
```

### C# (Assets/Scripts/TodoController.cs)

```csharp
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

public class Todo
{
    public string Title;
    public bool IsDone;
}

public class TodoController : MonoBehaviour
{
    private readonly List<Todo> todos = new();
    private ListView listView;

    void OnEnable()
    {
        var root = GetComponent<UIDocument>().rootVisualElement;
        var input = root.Q<TextField>("todo-input");
        listView = root.Q<ListView>("todo-list");

        // ListView는 "렌더 함수"를 등록하는 방식 — RN FlatList의 renderItem과 동일한 발상
        listView.makeItem = () =>          // 아이템 UI 생성 (재사용됨)
        {
            var row = new VisualElement();
            row.style.flexDirection = FlexDirection.Row;
            row.Add(new Toggle { name = "toggle" });
            row.Add(new Label { name = "title" });
            row.Add(new Button { name = "delete", text = "삭제" });
            return row;
        };
        listView.bindItem = (element, index) =>   // 데이터 바인딩 (renderItem의 몸통)
        {
            var todo = todos[index];
            var toggle = element.Q<Toggle>("toggle");
            var title = element.Q<Label>("title");

            toggle.SetValueWithoutNotify(todo.IsDone);
            title.text = todo.Title;
            title.style.opacity = todo.IsDone ? 0.4f : 1f;

            toggle.RegisterValueChangedCallback(evt =>
            {
                todo.IsDone = evt.newValue;
                listView.RefreshItem(index);   // 해당 아이템만 다시 그리기
            });
            element.Q<Button>("delete").clicked += () =>
            {
                todos.RemoveAt(index);
                listView.RefreshItems();       // 전체 갱신 (setTodos에 해당)
            };
        };
        listView.itemsSource = todos;          // data prop

        root.Q<Button>("add-button").clicked += () =>
        {
            if (string.IsNullOrWhiteSpace(input.value)) return;
            todos.Add(new Todo { Title = input.value });
            input.value = "";
            listView.RefreshItems();
        };
    }
}
```

> **React와의 대응**: `makeItem`/`bindItem` 분리는 가상화 리스트의 셀 재사용 패턴입니다.
> RN FlatList가 내부에서 해주던 일을 명시적으로 쓰는 것뿐이라, 개념은 이미 알고 있는 것입니다.
> (실전 팁: bindItem에서 콜백을 매번 등록하면 중복 등록 문제가 생길 수 있어,
> 실무에서는 `unbindItem`에서 해제하거나 클로저 대신 인덱스 기반 단일 핸들러를 씁니다.)

---

## STEP 3: 날씨 앱 (HTTP 통신·비동기·JSON)
**목표**: UnityWebRequest, async/await vs 코루틴, JSON 파싱

### API 준비

네이티브 트랙과 동일하게 OpenWeatherMap API 키를 사용합니다 (무료 발급).

### JSON 모델 (Assets/Scripts/WeatherData.cs)

```csharp
using System;

// JsonUtility는 [Serializable] + public 필드만 파싱함 (프로퍼티 X)
// 필드명이 JSON 키와 정확히 일치해야 함 → 소문자 유지
[Serializable]
public class WeatherResponse
{
    public MainInfo main;
    public WeatherInfo[] weather;
    public string name;
}

[Serializable]
public class MainInfo { public float temp; public int humidity; }

[Serializable]
public class WeatherInfo { public string description; public string icon; }
```

> 복잡한 JSON(딕셔너리, 중첩 배열)은 JsonUtility가 못 다룹니다.
> 그럴 땐 Package Manager에서 `com.unity.nuget.newtonsoft-json` 추가 →
> `JsonConvert.DeserializeObject<T>()` (JS의 `JSON.parse`에 가장 가까운 경험).

### 방법 1: 코루틴 (전통 방식 — 기존 자료 대부분이 이 방식)

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class WeatherService : MonoBehaviour
{
    IEnumerator FetchWeather(string city)
    {
        string url = $"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=YOUR_KEY&units=metric&lang=kr";

        using var request = UnityWebRequest.Get(url);
        yield return request.SendWebRequest();   // await과 같은 역할 (프레임 양보)

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"에러: {request.error}");
            yield break;                          // return과 같음
        }
        var data = JsonUtility.FromJson<WeatherResponse>(request.downloadHandler.text);
        Debug.Log($"{data.name}: {data.main.temp}°C");
    }

    void Start()
    {
        StartCoroutine(FetchWeather("Seoul"));    // 코루틴은 이렇게 시작
    }
}
```

### 방법 2: async/await (Unity 6 권장 — JS 개발자에게 자연스러움)

```csharp
using UnityEngine;
using UnityEngine.Networking;

public class WeatherService : MonoBehaviour
{
    async Awaitable<WeatherResponse> FetchWeather(string city)
    {
        string url = $"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=YOUR_KEY&units=metric&lang=kr";

        using var request = UnityWebRequest.Get(url);
        await request.SendWebRequest();           // JS의 await와 동일한 감각!

        if (request.result != UnityWebRequest.Result.Success)
            throw new System.Exception(request.error);

        return JsonUtility.FromJson<WeatherResponse>(request.downloadHandler.text);
    }

    async void Start()   // 이벤트 핸들러성 메서드만 async void 허용
    {
        try
        {
            var data = await FetchWeather("Seoul");
            Debug.Log($"{data.name}: {data.main.temp}°C");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"에러: {e.Message}");
        }
    }
}
```

> **어느 쪽을 쓸까?**: 새 코드는 async/await(방법 2), 하지만 기존 튜토리얼/답변의 90%는
> 코루틴이므로 **읽을 줄은 둘 다 알아야** 합니다. `yield return` = "여기서 기다렸다가 다음 프레임에 재개"로 읽으면 됩니다.
> UI 연결은 STEP 1~2에서 배운 UI Toolkit 패턴 그대로 — 입력 필드에서 도시명 받아 결과 Label 갱신.
> 로딩 상태는 `label.text = "로딩 중..."` → 완료 시 갱신으로 처리해 보세요 (연습 문제).

---

## STEP 4: 미니 게임 — 2D 코인 먹기 (진짜 Unity!)
**목표**: 지금까지는 "Unity로 앱 만들기"였다면, 이제 Unity의 본업.
물리, 충돌, 프리팹, 입력, 점수 UI, 저장까지 게임의 최소 단위를 전부 경험합니다.

### 게임 설계

```
- 플레이어(사각형)를 좌우로 움직여서
- 하늘에서 떨어지는 코인(원)을 받으면 +1점
- 놓친 코인은 바닥에서 사라짐
- 최고 점수는 PlayerPrefs에 저장 (localStorage처럼)
```

### 1) 씬 구성 (에디터 작업)

```
1. 새 씬 (Universal 2D 템플릿 기준)
2. Hierarchy 우클릭 → 2D Object → Sprites → Square → 이름 "Player"
   - 화면 하단에 배치 (Position Y: -4)
   - Add Component → Box Collider 2D
3. Hierarchy 우클릭 → 2D Object → Sprites → Circle → 이름 "Coin"
   - Add Component → Circle Collider 2D → "Is Trigger" 체크 ✅
   - Add Component → Rigidbody 2D (중력으로 떨어지게 함)
   - Gravity Scale: 0.5 (낙하 속도 조절)
4. Coin을 Project 창의 Assets/Prefabs 폴더로 드래그 → 프리팹 생성!
   → Hierarchy에 남은 원본 Coin은 삭제
   (프리팹 = "컴포넌트 정의", Instantiate = "<Coin /> 렌더")
```

### 2) 플레이어 이동 (Assets/Scripts/PlayerController.cs)

```csharp
using UnityEngine;

public class PlayerController : MonoBehaviour
{
    [SerializeField] private float speed = 8f;   // Inspector에서 튜닝 가능 (props)

    void Update()
    {
        // 구식 Input Manager 기준 (프로젝트 기본값). 좌우 화살표/A·D 키
        float h = Input.GetAxis("Horizontal");   // -1 ~ 1
        transform.position += Vector3.right * h * speed * Time.deltaTime;

        // 화면 밖으로 못 나가게 clamp
        var pos = transform.position;
        pos.x = Mathf.Clamp(pos.x, -8f, 8f);
        transform.position = pos;
    }
}
```

### 3) 코인 로직 (Assets/Scripts/Coin.cs — 프리팹에 부착)

```csharp
using UnityEngine;

public class Coin : MonoBehaviour
{
    // 물리 엔진이 겹침을 감지하면 자동 호출 (onClick처럼 "이벤트"지만, 발화자는 물리 엔진)
    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))          // Player 오브젝트에 Tag 설정 필요
        {
            GameManager.Instance.AddScore(1);
            Destroy(gameObject);                  // 컴포넌트 unmount
        }
    }

    void Update()
    {
        if (transform.position.y < -6f)           // 화면 아래로 사라지면
            Destroy(gameObject);
    }
}
```

### 4) 게임 매니저 — 스폰·점수·저장 (Assets/Scripts/GameManager.cs)

```csharp
using UnityEngine;

public class GameManager : MonoBehaviour
{
    // 싱글턴 = 게임 씬의 전역 상태 저장소 (Context/Zustand 스토어에 해당)
    public static GameManager Instance { get; private set; }

    [SerializeField] private GameObject coinPrefab;   // Inspector에서 프리팹 드래그
    [SerializeField] private float spawnInterval = 1f;

    public int Score { get; private set; }
    private float timer;

    void Awake() => Instance = this;

    void Start()
    {
        // localStorage.getItem("highScore") ?? 0
        int highScore = PlayerPrefs.GetInt("highScore", 0);
        Debug.Log($"최고 기록: {highScore}");
    }

    void Update()
    {
        // setInterval 대신: 매 프레임 시간을 누적해서 주기 실행 (게임 루프식 타이머)
        timer += Time.deltaTime;
        if (timer >= spawnInterval)
        {
            timer = 0f;
            SpawnCoin();
        }
    }

    void SpawnCoin()
    {
        float x = Random.Range(-8f, 8f);
        // <Coin position={{x, y: 6}} /> 를 "렌더"
        Instantiate(coinPrefab, new Vector3(x, 6f, 0f), Quaternion.identity);
    }

    public void AddScore(int amount)
    {
        Score += amount;
        if (Score > PlayerPrefs.GetInt("highScore", 0))
        {
            PlayerPrefs.SetInt("highScore", Score);   // localStorage.setItem
            PlayerPrefs.Save();
        }
    }
}
```

### 5) 점수 UI (UGUI 맛보기)

```
1. Hierarchy 우클릭 → UI → Text - TextMeshPro → 이름 "ScoreText"
   (처음이면 "Import TMP Essentials" 클릭)
2. Canvas가 자동 생성됨 — UGUI의 UI는 전부 Canvas 아래에 삽니다
3. 화면 좌상단에 배치 (Anchor를 top-left로)
```

```csharp
// Assets/Scripts/ScoreDisplay.cs — ScoreText에 부착
using TMPro;
using UnityEngine;

public class ScoreDisplay : MonoBehaviour
{
    private TextMeshProUGUI label;

    void Awake() => label = GetComponent<TextMeshProUGUI>();

    void Update()
    {
        // "매 프레임 다시 그리기" — React의 리렌더를 손으로 하는 셈.
        // 이 정도 규모에선 문제없지만, 실전에서는 점수 변경 이벤트를 구독하는 방식으로 개선
        label.text = $"점수: {GameManager.Instance.Score}";
    }
}
```

### 6) 마무리 체크리스트

```
✅ Player 오브젝트의 Tag를 "Player"로 설정 (Inspector 상단)
✅ GameManager용 빈 오브젝트 생성 → GameManager.cs 부착 → coinPrefab 드래그
✅ ▶ Play → 코인이 떨어지고, 받으면 점수 오르고, 재시작해도 최고기록 유지되면 완성!
```

> **여기서 배운 것이 Unity의 전부의 축소판입니다**:
> 프리팹(컴포넌트 정의) → Instantiate(렌더) → 물리 이벤트(충돌) → 싱글턴(전역 상태) → PlayerPrefs(저장).
> 이 위에 스프라이트 이미지, 사운드(`AudioSource.PlayOneShot`), 씬 전환(`SceneManager.LoadScene("GameOver")`)을 얹으면 출시 가능한 하이퍼캐주얼 게임 구조가 됩니다.

---

# PART 4: 실전 (출시 전 알아둘 것)

## 4-1. 디버깅

```csharp
Debug.Log("일반 로그");            // console.log
Debug.LogWarning("경고");          // console.warn
Debug.LogError("에러");            // console.error
Debug.Log($"위치: {transform.position}");   // 객체도 대부분 잘 출력됨
```

```
- Console 창에서 확인 (Collapse 켜면 중복 로그 접힘 — Update 안 로그 필수)
- 에디터 일시정지: Play 중 ⏸ 버튼 → Scene 뷰에서 오브젝트 상태 실시간 검사
  (React DevTools로 컴포넌트 state 들여다보는 것과 같은 경험)
- 브레이크포인트: VS Code/Rider에서 "Attach to Unity" 후 중단점 설정
- 모바일 실기 로그: adb logcat -s Unity (Android) / Xcode 콘솔 (iOS)
```

## 4-2. 모바일 빌드

### Android

```
1. File → Build Profiles → Android → "Switch Platform"
2. Player Settings에서:
   - Company Name / Product Name (패키지명이 됨)
   - Other Settings → Identification → Package Name: com.yourname.appname
   - Minimum API Level: 23+ 권장
3. "Build" → APK 생성 (테스트용)
4. 스토어 제출용은 "Build App Bundle (Google Play)" 체크 → .aab 생성
   - 서명 키(keystore)는 Player Settings → Publishing Settings에서 생성
   - 키 분실 = 업데이트 불가. 네이티브 트랙 4-4의 백업 수칙 그대로 적용!
```

### iOS

```
1. File → Build Profiles → iOS → Switch Platform → Build
2. ⚠️ Unity는 .ipa를 직접 만들지 않고 Xcode 프로젝트를 생성합니다
3. 생성된 폴더의 .xcodeproj를 Xcode로 열기
4. Signing & Capabilities에서 팀 선택 → 이후는 네이티브 트랙과 동일
   (Apple Developer Program $99/년, 심사 제출도 동일 프로세스)
```

## 4-3. 입력 — 모바일 터치

```csharp
// PC 테스트용 코드(Input.GetAxis)는 모바일에서 동작하지 않습니다.
// 가장 간단한 터치 대응: 화면 좌/우 절반 터치로 이동
void Update()
{
    if (Input.touchCount > 0)
    {
        Touch touch = Input.GetTouch(0);
        float dir = touch.position.x < Screen.width / 2 ? -1f : 1f;
        transform.position += Vector3.right * dir * speed * Time.deltaTime;
    }
}
// 본격적으로 하려면 신형 Input System 패키지(액션 기반, 이벤트 방식)를 배우세요.
// 웹의 이벤트 리스너 모델과 비슷해서 오히려 익숙할 겁니다.
```

## 4-4. 인앱 결제와 구독 (수익화)

Package Manager에서 **In-App Purchasing (`com.unity.purchasing`)**을 설치하고 Services의 IAP를
활성화합니다. App Store Connect와 Play Console에도 같은 상품을 각각 만들어야 합니다.
예제는 일회성 `premium_theme`와 월간 구독 `pro_monthly`를 등록합니다.

Unity IAP는 React의 전역 이벤트 provider처럼 앱 시작 때 한 번 초기화합니다. 구매 버튼을 누를 때
초기화하면 결제 완료 이벤트를 놓칠 수 있습니다.

```csharp
using UnityEngine;
using UnityEngine.Purchasing;

public sealed class StoreManager : MonoBehaviour, IStoreListener
{
    public const string PremiumTheme = "premium_theme";
    public const string ProMonthly = "pro_monthly";

    private static StoreManager instance;
    private IStoreController controller;
    private IExtensionProvider extensions;

    void Awake()
    {
        if (instance != null) { Destroy(gameObject); return; }
        instance = this;
        DontDestroyOnLoad(gameObject); // ⭐ 구매 요청 전부터 리스너를 유지
        InitializePurchasing();
    }

    void InitializePurchasing()
    {
        var module = StandardPurchasingModule.Instance();
        var builder = ConfigurationBuilder.Instance(module);
        builder.AddProduct(PremiumTheme, ProductType.NonConsumable);
        builder.AddProduct(ProMonthly, ProductType.Subscription);
        UnityPurchasing.Initialize(this, builder);
    }

    public void OnInitialized(IStoreController c, IExtensionProvider e)
    {
        controller = c;
        extensions = e;
        RefreshEntitlements();
    }

    public void Buy(string productId)
    {
        controller?.InitiatePurchase(productId);
    }

    public PurchaseProcessingResult ProcessPurchase(PurchaseEventArgs args)
    {
        // ⭐ transactionID가 아니라 definition.id(productId)로 상품을 매핑
        string productId = args.purchasedProduct.definition.id;

        // 서버에서 영수증 검증 후 실제 프로젝트의 entitlement 저장소에 반영하세요.
        if (productId == PremiumTheme) UnlockPremiumTheme();
        else if (productId == ProMonthly) EnableSubscription();
        else return PurchaseProcessingResult.Complete;

        // 서버 검증이 비동기라면 Pending을 반환하고 검증 성공 후 ConfirmPendingPurchase 호출
        return PurchaseProcessingResult.Complete;
    }

    public void OnInitializeFailed(InitializationFailureReason error) { Debug.LogError(error); }
    public void OnInitializeFailed(InitializationFailureReason error, string message)
        { Debug.LogError($"{error}: {message}"); }
    public void OnPurchaseFailed(Product product, PurchaseFailureReason reason)
        { Debug.LogWarning($"{product.definition.id}: {reason}"); }
}
```

상품명과 가격은 Catalog에 적은 문자열이 아니라 스토어가 돌려준 metadata를 표시합니다.

```csharp
Product product = controller.products.WithID(StoreManager.ProMonthly);
priceLabel.text = product.metadata.localizedPriceString; // ⭐ 현지 통화·세금 반영
titleLabel.text = product.metadata.localizedTitle;
```

⚠️ **상품 ID(`definition.id`)로 매핑하세요.** `transactionID`나 영수증 속 다른 id는 거래마다
달라집니다. 이것을 상품 키로 쓰면 결제는 됐는데 아이템이 안 열리는 버그가 납니다.

iOS에는 눈에 보이는 **구매 복원** 버튼을 제공하세요. Android는 초기화 시 소유한 비소모성 상품과
구독을 자동으로 돌려주지만, 명시적인 복원/재검증 UI를 공통 제공하면 사용자가 이해하기 쉽습니다.

```csharp
public void RestorePurchases()
{
#if UNITY_IOS
    var apple = extensions.GetExtension<IAppleExtensions>();
    apple.RestoreTransactions((success, message) => {
        Debug.Log($"Restore: {success}, {message}");
        if (success) RefreshEntitlements();
    });
#else
    RefreshEntitlements();
#endif
}
```

### 출시 전에 반드시 확인

- ⚠️ `StoreManager`를 첫 씬에서 생성하고 `DontDestroyOnLoad`로 유지해 구매 요청 **전에** 리스너가
  준비되게 하세요. 결제 앱으로 전환한 사이 완료된 거래를 놓치면 안 됩니다.
- ⚠️ iOS **구매 복원** 버튼은 필수입니다. 없으면 App Store 심사에서 리젝될 수 있습니다.
- ⚠️ 환불·취소·구독 만료는 App Store Server Notifications/Google RTDN 또는 실행·복귀 때
  서버 영수증 재검증으로 entitlement를 회수하세요. `PlayerPrefs` Boolean은 진실의 원천이 아닙니다.
- ⚠️ Android 구매 완료는 Unity IAP가 정상 처리/확정하도록 해야 합니다. acknowledge가 누락되면
  **3일 후 자동 환불**됩니다. 서버 검증 중 `Pending`을 반환했다면 성공 후 반드시 확정하세요.
- ⚠️ iOS는 Sandbox 계정과 StoreKit 설정 파일, Android는 Play 라이선스 테스터로 시험합니다.
  Android는 **Play 스토어에서 설치한 테스트 빌드**여야 합니다. 사이드로드 APK는 상품이 비어 보일 수 있습니다.
- ⚠️ 가격은 `localizedPriceString`을 쓰세요. 하드코딩 가격은 지역 통화·세금과 어긋나고
  App Store 심사 지침 2.3.7 문제로 이어질 수 있습니다.
- ⭐ 정직한 페이월에는 무료/유료 콘텐츠, 구독 기간·자동 갱신을 분명히 씁니다.
  가짜 타이머, 닫기 숨김, 고가 상품 강제 선택 같은 다크패턴은 금지입니다.

→ 공식 문서: [Unity IAP](https://docs.unity3d.com/Manual/UnityIAP.html),
[Google Play Billing 테스트](https://developer.android.com/google/play/billing/test),
[StoreKit 테스트](https://developer.apple.com/documentation/storekit/testing-in-app-purchases-in-xcode)

## 4-5. 성능 기초 (모바일에서 특히 중요)

```
1. Update() 안에서 하지 말 것:
   - GetComponent / Find 계열 호출 → Awake/Start에서 캐싱
   - new로 객체 생성, LINQ, 문자열 연결 → GC 스파이크 = 프레임 드랍
2. 자주 생성/파괴되는 오브젝트(총알, 코인)는 오브젝트 풀링
   → Destroy 대신 SetActive(false) 후 재사용 (UnityEngine.Pool 내장 지원)
3. 프로파일러: Window → Analysis → Profiler (Chrome DevTools Performance 탭에 해당)
4. 모바일 기본: 텍스처 압축(ASTC), 60fps 고정은 Application.targetFrameRate = 60
```

---

# PART 5: React 개발자가 자주 밟는 지뢰

```
1. "state 바꿨는데 화면이 안 바뀌어요"
   → Unity에 리렌더는 없습니다. UI 갱신 코드를 직접 호출해야 합니다.

2. Update()에서 speed * Time.deltaTime 빼먹기
   → 60fps 폰에서는 정상, 120fps 폰에서는 2배 빨라지는 버그.

3. 파괴된 오브젝트에 ?. 사용
   → Unity 오브젝트의 null은 특수 처리됨. if (obj != null)로 명시 체크.

4. float에 f 안 붙이기 → "cannot convert double to float" 컴파일 에러.

5. GetComponent를 Update에서 매번 호출
   → document.querySelector를 매 프레임 도는 것과 같음. 캐싱 필수.

6. 씬 파일(.unity) 충돌
   → 씬/프리팹은 머지가 사실상 불가. 협업 시 한 씬은 한 명만 만지는 규칙 필요.
   → .gitignore는 Unity 공식 템플릿 사용 (Library/ 등 자동 생성 폴더 제외 필수!)

7. "왜 코드가 실행 안 되죠?" → 스크립트를 씬의 오브젝트에 부착 안 함.
   C# 파일은 GameObject에 붙어야만 실행됩니다 (import만으로 실행되는 JS와 다름).

8. async void 남발
   → 이벤트 핸들러 외에는 async Task/Awaitable로. async void는 예외를 삼킵니다.

9. PlayerPrefs에 민감 정보 저장
   → 평문 저장입니다. localStorage와 같은 수준으로만 신뢰하세요.

10. 에셋스토어 에셋 무분별 임포트
    → node_modules 같은 격리가 없어서 프로젝트 전역이 오염됩니다.
    임포트 전 새 브랜치에서 테스트하는 습관을.
```

---

# 부록: 다음 단계 & 리소스

## 추천 타임라인

```
⚡ Claude 어시스트 Fast-track (12~18시간):
1일차: PART 0~1 (환경 + C# 훑기)          — 3시간
2일차: PART 2~3 STEP 1~2 (UI Toolkit)     — 4시간
3일차: STEP 3~4 (날씨 + 미니 게임)         — 5시간
4일차: 미니 게임 개량 + 실기 빌드           — 4시간

전체 루트 (독학, 60~100시간):
Unity는 에디터 조작 숙련이 코드만큼 중요해서 네이티브 트랙보다 편차가 큽니다.
공식 Unity Learn의 "Unity Essentials" 패스웨이를 병행하세요.
```

## 유용한 링크

```
공식 학습:
→ https://learn.unity.com (Unity Learn — 무료, Essentials/Junior Programmer 추천)
→ https://docs.unity3d.com (스크립팅 API 레퍼런스)

커뮤니티/자료:
→ https://discussions.unity.com (공식 포럼)
→ YouTube: Brackeys(레전드 입문 채널), Code Monkey, Tarodev

C# 심화:
→ https://learn.microsoft.com/ko-kr/dotnet/csharp/
→ UniTask (async 사실상 표준): https://github.com/Cysharp/UniTask

다음 프로젝트 아이디어 (난이도순):
1. 코인 게임에 장애물/생명 추가 → 게임오버 씬
2. 2D 플랫포머 (점프, 타일맵)
3. 방치형 클리커 (UI Toolkit 복습 + 큰 숫자 처리)
4. 멀티플레이 (Netcode for GameObjects)
```

## 세 트랙을 모두 마쳤다면

```
- 일반 앱은 RN으로, 게임은 Unity로, 플랫폼 딥다이브는 네이티브로.
- Unity 게임에 RN 지식이 하나 더 얹히는 지점: 게임 + 커뮤니티 앱 조합 서비스
  (게임은 Unity, 커뮤니티/랭킹 웹뷰는 React — 실무에서 흔한 구성)
- C#을 배웠으니 덤으로 열리는 문: .NET 백엔드(ASP.NET Core), Godot(C# 지원)
```
