# Android 앱 개발 튜토리얼 (Kotlin + Jetpack Compose)
## React / JavaScript 개발자를 위한 완전판

> **이 문서의 범위**: Android만 다룹니다. 모든 예제가 **JS/React와 1:1 대조**로 되어 있어
> 알던 개념에 이름표만 새로 붙이는 방식으로 진행합니다.
>
> 같은 시리즈: [iOS 트랙(Swift/SwiftUI)](./ios-swift-swiftui.md) · [React Native 트랙](./react-to-react-native.md) · [Unity(C#) 트랙](./react-to-unity.md) · [트랙 선택 가이드(README)](./README.md)
>
> ⚡ **Claude 어시스트 환경이면 [Fast-track 루트](#-fast-track-claude-어시스트-환경--추천)(6~9시간)부터 보세요.** 전체 루트(30~45시간)는 AI 없이 직접 개발할 사람용입니다.
>
> 📱 **iOS도 할 계획이라면**: 한쪽을 먼저 끝내고 다른 쪽을 보세요. 두 번째 트랙은 개념이 이미 머리에 있어서 절반 시간이면 됩니다. 대조표는 [PART 5의 iOS 대조 부록](#부록-ios-트랙과의-대조표)에 있습니다.

---

## 목차

- [PART 0: 개발 환경 세팅](#part-0-개발-환경-세팅)
- [PART 1: Kotlin 문법 (JS와 1:1 비교)](#part-1-kotlin-문법-js와-11-비교)
- [PART 2: 매핑 치트시트](#part-2-매핑-치트시트)
- [PART 3: 샘플 앱 만들기](#part-3-샘플-앱-만들기)
- [PART 4: 실전 보강](#part-4-실전-보강)
- [PART 5: 학습 로드맵 & 리소스](#part-5-학습-로드맵--리소스)

---

# PART 0: 개발 환경 세팅

## 0-1. Android Studio 설치

1. https://developer.android.com/studio 접속
2. OS에 맞는 버전 다운로드 (Windows / macOS / Linux — **Android는 Mac이 필수가 아닙니다**)
3. 설치 시 "Standard" 설정 선택 (커스텀 불필요)
4. 첫 실행 시 SDK 자동 다운로드 (약 2~5GB, 시간 걸림)

### 설치 확인 체크리스트

```
✅ Android Studio 실행 됨
✅ "New Project" 버튼이 보임
✅ SDK Manager에서 최신 Android SDK 설치 확인
   → Settings > Languages & Frameworks > Android SDK
   → 목록 맨 위 (가장 최신) Android 버전 체크
✅ "SDK Tools" 탭에서 아래 항목 체크 확인
   → Android SDK Build-Tools
   → Android Emulator
   → Android SDK Platform-Tools
```

> **버전 숫자는 이 문서를 믿지 마세요.** Android는 매년 새 버전(API 레벨)이 나옵니다.
> 규칙만 기억하면 됩니다 — **SDK Manager 목록에서 "가장 최신 정식 버전"을 설치**하고,
> 프리뷰/베타 딱지가 붙은 건 건너뜁니다. 구체적인 숫자는 아래 0-4에서 다룹니다.

## 0-2. 에뮬레이터 (가상 기기) 설정

에뮬레이터 = 내 컴퓨터에서 돌리는 가상 안드로이드 폰입니다.

**생성 방법:**

1. Android Studio 상단 메뉴 → Tools → Device Manager
2. "Create Device" 클릭
3. 기기 선택: **Pixel 계열 최신 표준 사이즈** 추천 (Pixel 7~9 아무거나)
4. 시스템 이미지 선택: 최신 정식 API (옆에 Download 버튼 누르면 다운로드)
5. "Finish" 클릭

**실행 방법:**

1. Device Manager에서 만든 기기 옆의 ▶ (재생) 버튼 클릭
2. 에뮬레이터 창이 뜨면 성공. 첫 부팅은 1~2분 걸립니다.

**에뮬레이터가 느릴 때:**

```
Windows: BIOS에서 Intel VT-x 또는 AMD-V 가상화 활성화
macOS (Apple Silicon): ARM 이미지가 자동 선택됨 (매우 빠름)
macOS (Intel): x86 이미지 + 하드웨어 가속

그래도 느리면:
→ SDK Tools에서 "Android Emulator" 최신 버전으로 업데이트
→ 에뮬레이터 설정(연필 아이콘)에서 RAM 4GB, 그래픽 "Hardware"
→ 에뮬레이터의 Cold Boot 대신 Quick Boot 사용
```

**실제 기기로 테스트 (강력 추천):**

```
1. 설정 → 휴대전화 정보 → 빌드 번호 7번 탭 (개발자 모드 활성화)
2. 설정 → 개발자 옵션 → USB 디버깅 켜기
3. USB 케이블로 컴퓨터 연결 → 폰에서 "USB 디버깅 허용" 승인
4. Android Studio 기기 목록에 내 폰이 뜨면 성공
```

> **왜 실기기가 중요한가**: 에뮬레이터는 터치 감각·스크롤 관성·실제 성능·카메라·센서를
> 재현하지 못합니다. **"느낌"에 대한 판단은 반드시 실기기에서** 하세요.
> 웹에서 크롬 devtools 모바일 뷰만 보고 반응형을 판단하면 안 되는 것과 같은 이유입니다.

## 0-3. 첫 프로젝트 생성 & 프로젝트 구조

```
1. Android Studio → "New Project"
2. "Empty Activity" 선택 (= Compose 템플릿)
3. 설정:
   - Name: HelloWorld
   - Package name: com.yourname.helloworld   ← 스토어에서 앱의 고유 ID. 나중에 못 바꿉니다
   - Language: Kotlin
   - Minimum SDK: API 26 이상 권장 (아래 0-4 참고)
   - Build configuration language: Kotlin DSL (기본값)
4. "Finish" → 프로젝트 생성 (Gradle 동기화에 1~3분)
5. 상단 ▶ 버튼 → 에뮬레이터에 "Hello Android!" 뜨면 성공
```

> **Package name은 도메인 역순이 관례**입니다 (`com.회사명.앱이름`).
> 도메인이 없으면 `com.github.깃허브아이디.앱이름` 처럼 만들어도 됩니다.
> **한 번 스토어에 올리면 영구히 못 바꿉니다** — 바꾸려면 새 앱으로 다시 출시해야 합니다.

### 폴더 구조 — JS 프로젝트와 대조

```
// JS 프로젝트                   →  Android 프로젝트
package.json                    →  app/build.gradle.kts   (의존성·빌드 설정)
package-lock.json               →  gradle/libs.versions.toml (버전 카탈로그)
node_modules/                   →  ~/.gradle/caches/      (전역 캐시, 프로젝트 밖)
src/                            →  app/src/main/java/...  (Kotlin 소스)
  App.js                        →    MainActivity.kt      (진입점)
  components/                   →    ui/screens/, ui/components/
  assets/                       →  app/src/main/res/      (이미지·문자열·색상)
public/index.html               →  app/src/main/AndroidManifest.xml (앱 메타·권한)
.env                            →  local.properties (git 제외) / BuildConfig
dist/, build/                   →  app/build/
```

**꼭 알아야 할 3개 파일:**

| 파일 | 역할 | JS 대응 |
|---|---|---|
| `app/build.gradle.kts` | 의존성, SDK 버전, 빌드 타입 | `package.json` |
| `app/src/main/AndroidManifest.xml` | 앱 이름·아이콘·권한·진입점 선언 | `manifest.json` + 권한 정책 |
| `app/src/main/res/values/strings.xml` | 모든 사용자 노출 문자열 | i18n 리소스 파일 |

> **Gradle 동기화 실패 시:**
> File → Sync Project with Gradle Files,
> 그래도 안 되면 File → Invalidate Caches → Restart

## 0-4. Gradle과 SDK 버전 이해하기 ⭐ (JS 개발자가 제일 먼저 막히는 곳)

JS의 `npm install`에 해당하는 게 Gradle인데, **JS보다 개념이 하나 더 많습니다: SDK 레벨 3종.**

### compileSdk / targetSdk / minSdk

```kotlin
// app/build.gradle.kts
android {
    compileSdk = 36        // ① 어떤 버전의 API로 "컴파일"할지

    defaultConfig {
        minSdk = 26        // ② 이 버전 미만 폰에는 설치 자체가 안 됨
        targetSdk = 36     // ③ "이 버전까지 테스트했다"는 선언
    }
}
```

| | 의미 | JS 비유 | 고르는 법 |
|---|---|---|---|
| `compileSdk` | 코드에서 쓸 수 있는 최신 API 집합 | TypeScript `lib` 설정 | **항상 최신 정식 버전** |
| `minSdk` | 지원하는 가장 낮은 안드로이드 | `browserslist`의 하한 | 26(Android 8) 정도가 무난. 낮출수록 코드 분기 늘어남 |
| `targetSdk` | 시스템이 앱에 적용할 동작 규칙 기준 | 없음 (안드로이드 고유) | **최신으로 유지 필수** |

> ⚠️ **`targetSdk`는 방치하면 앱이 스토어에서 내려갑니다.**
> Google Play는 매년 "신규 앱/업데이트는 targetSdk가 N 이상이어야 함" 기준을 올립니다.
> 1년에 한 번은 최신으로 올리고 회귀 테스트하는 걸 일정에 넣으세요.
> 현재 요구 수준은 [Play Console 대상 API 수준 요구사항](https://developer.android.com/google/play/requirements/target-sdk) 확인.

**minSdk를 낮추면 생기는 비용** — 예: minSdk 21로 낮추면 알림 권한·저장소 접근·edge-to-edge 등이
버전별로 다르게 동작해 `if (Build.VERSION.SDK_INT >= ...)` 분기가 계속 늘어납니다.
개인 개발자라면 **26 이상**에서 시작하는 걸 권합니다. 실제 사용자 커버리지 손실은 매우 작습니다.

### 버전 카탈로그 (libs.versions.toml)

요즘 새 프로젝트는 의존성 버전을 한 파일에 모읍니다. 처음 보면 당황스럽지만 구조는 단순합니다.

```toml
# gradle/libs.versions.toml
[versions]
retrofit = "2.11.0"
navigation = "2.8.5"

[libraries]
retrofit        = { group = "com.squareup.retrofit2", name = "retrofit",       version.ref = "retrofit" }
retrofit-gson   = { group = "com.squareup.retrofit2", name = "converter-gson", version.ref = "retrofit" }
navigation      = { group = "androidx.navigation",    name = "navigation-compose", version.ref = "navigation" }
```

```kotlin
// app/build.gradle.kts — 위 카탈로그를 참조
dependencies {
    implementation(libs.retrofit)
    implementation(libs.retrofit.gson)      // toml의 '-'가 코드에선 '.'
    implementation(libs.navigation)
}
```

> **JS 비유**: `libs.versions.toml` = 버전을 몰아넣은 `package.json`의 `dependencies`,
> `build.gradle.kts` = 실제로 import 하는 곳. 버전을 한 군데서만 고치면 되는 게 장점입니다.
>
> 이 문서의 예제는 읽기 쉬우라고 `implementation("group:name:version")` 직접 표기를 씁니다.
> 실제 프로젝트에선 카탈로그 방식을 쓰세요. Android Studio가 `Alt+Enter`로 변환도 해줍니다.

### Compose BOM — Compose 버전은 개별로 쓰지 않는다

```kotlin
dependencies {
    // BOM 하나만 버전 지정하면, 그 아래 compose 라이브러리들은 버전을 안 씀
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
}
```

BOM(Bill of Materials) = "이 조합은 서로 호환됨을 보증한다"는 묶음. Compose 라이브러리 간
버전이 어긋나서 나는 난해한 에러를 통째로 없애줍니다. **BOM 버전만 올리세요.**

### JDK 버전 불일치 — 초보자 에러 1위

```
> Unsupported class file major version 6x
> Android Gradle plugin requires Java 17 to run. You are currently using Java 11.
```

이 에러가 뜨면:
```
Settings → Build, Execution, Deployment → Build Tools → Gradle
→ "Gradle JDK" 를 Android Studio 내장 JDK (jbr-17 등)로 지정
```
터미널에서 `./gradlew`를 쓸 때는 `JAVA_HOME`도 같은 버전을 가리켜야 합니다.

## 0-5. 공통 도구

### Claude Code 설치 (사실상 필수)

Kotlin은 JS보다 **컴파일 에러가 훨씬 자주** 납니다. 대신 그 에러는 대부분 기계적으로
고칠 수 있어서, 에러 메시지를 그대로 붙여넣어 물어보는 것만으로 학습 속도가 몇 배가 됩니다.

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | sh

claude --version            # 설치 확인

cd ~/AndroidStudioProjects/HelloWorld
claude                      # 프로젝트 폴더에서 실행 → /login
```

**효과적인 활용 패턴:**
- 컴파일 에러 전문 붙여넣기 → 원인 + 수정안
- "이 JS 코드를 Kotlin/Compose로 바꿔줘"
- "이 Composable이 왜 리컴포지션이 계속 일어나?" (혼자 알아내기 가장 어려운 부류)

> Claude Code는 Pro 이상 구독이 필요합니다.

### Git

```bash
git --version   # 없으면 https://git-scm.com

# Android 프로젝트의 .gitignore 필수 항목
# (Android Studio가 자동 생성해주지만 아래 2개는 직접 확인)
# local.properties      ← SDK 절대경로, 머신마다 다름
# keystore.properties   ← 서명 비밀번호 (절대 커밋 금지)
```

## 0-6. Google Play 개발자 계정 (나중에 해도 됨)

```
비용: $25 (일회성, 평생 유효)
등록: https://play.google.com/console

준비물:
- Google 계정
- 신용카드 / 체크카드
- 본인 확인용 신분증 (개인 개발자는 신원 확인 절차가 있습니다)

등록 후 심사: 보통 1~3일
```

> ⚠️ **개인 개발자 계정의 추가 요건**: 신규 개인 계정은 프로덕션 출시 전에
> **비공개 테스트(20명 이상, 일정 기간 연속)** 를 요구하는 정책이 적용될 수 있습니다.
> 정책은 자주 바뀌니 계정 만든 직후 Play Console의 안내를 꼭 읽어보세요.
> 테스터 20명을 모으는 게 생각보다 오래 걸리므로 **계정은 미리 만들어두는 게 유리**합니다.

---

# PART 1: Kotlin 문법 (JS와 1:1 비교)

완벽히 외울 필요 없습니다. "아 이런 느낌이구나" 정도로 30분~1시간 훑고 넘어가세요.
막히면 [PART 2 치트시트](#part-2-매핑-치트시트)로 돌아오면 됩니다.

## 1-1. 변수와 상수

```javascript
// JavaScript
const name = "홍길동"       // 재할당 불가
let age = 25               // 재할당 가능
var score = 100            // 요즘 잘 안 씀
```

```kotlin
// Kotlin
val name = "홍길동"         // JS의 const (재할당 불가)
var age = 25               // JS의 let (재할당 가능)
// JS의 var에 해당하는 건 없음. Kotlin의 var은 JS의 let입니다
```

> **기본은 `val`.** IDE가 "이건 val로 바꿀 수 있다"고 알려주면 그냥 따르세요.
> Compose에서 `var`를 남발하면 상태 관리가 꼬입니다.

## 1-2. 타입 시스템 (JS와 가장 큰 차이)

```javascript
// JavaScript — 타입 자유, 런타임에 에러 발견
let x = "hello"
x = 123            // OK
x = true           // OK

function add(a, b) { return a + b }
add("1", 2)        // "12" — 의도치 않은 결과
```

```kotlin
// Kotlin — 타입 추론 + 컴파일 시점 체크
var x = "hello"    // String으로 자동 추론
// x = 123         // ❌ 컴파일 에러

fun add(a: Int, b: Int): Int {   // 매개변수 타입은 필수
    return a + b
}
// add("1", 2)     // ❌ 컴파일 에러 — 실행 전에 잡힘
```

> **TypeScript를 써봤다면 그대로입니다.** 차이는 "런타임에 지워지지 않는다"는 것.
> TS의 타입은 컴파일하면 사라지지만 Kotlin의 타입은 실제로 런타임에 존재합니다.
> 그래서 `if (x is String)` 같은 검사가 실제로 동작합니다.

**타입 변환은 자동으로 안 됩니다** (JS와 가장 자주 부딪히는 부분):

```kotlin
val i: Int = 10
// val d: Double = i        // ❌ 안 됨
val d: Double = i.toDouble() // ✅ 명시적 변환

val s = "42"
val n = s.toInt()            // 실패하면 예외
val n2 = s.toIntOrNull() ?: 0 // 실패하면 null → 기본값. 실전에서 이걸 더 자주 씀
```

## 1-3. 함수

```javascript
// JavaScript
function greet(name) { return "안녕, " + name }
const double = (x) => x * 2
function hello(name = "세계") { return "안녕, " + name }
```

```kotlin
// Kotlin
fun greet(name: String): String {
    return "안녕, $name"      // 문자열 템플릿: 변수 하나면 $ 만으로 충분
}

fun double(x: Int) = x * 2   // 한 줄이면 중괄호·return·반환타입 생략

fun hello(name: String = "세계") = "안녕, $name"   // 기본값

// 이름 붙여 호출 (named argument) — JS엔 없고 Compose에서 매우 자주 씀
fun createUser(name: String, age: Int = 0, isAdmin: Boolean = false) { }
createUser(name = "홍길동", isAdmin = true)   // 중간 인자 건너뛰기 가능
```

> **named argument는 Compose의 핵심 문법**입니다.
> `Text(text = "안녕", fontSize = 24.sp)` 처럼 매개변수가 10개 넘는 함수를 다루게 되니
> 이 문법에 익숙해지세요.

**후행 람다 (trailing lambda)** — Compose 코드가 그렇게 생긴 이유:

```kotlin
// 마지막 매개변수가 함수면 괄호 밖으로 뺄 수 있음
Button(onClick = { count++ }) {   // ← 이 { } 가 마지막 매개변수 content
    Text("클릭!")
}
// 위는 사실 아래와 같음
Button(onClick = { count++ }, content = { Text("클릭!") })
```

## 1-4. 조건문

```javascript
// JavaScript
if (score >= 90) { console.log("A") }
else if (score >= 80) { console.log("B") }
else { console.log("C") }

const grade = score >= 90 ? "A" : "B"
```

```kotlin
// Kotlin
if (score >= 90) { println("A") }
else if (score >= 80) { println("B") }
else { println("C") }

// 삼항 연산자가 없습니다. if가 값을 반환하는 표현식이라 필요 없음
val grade = if (score >= 90) "A" else "B"

// when = switch의 강화판
val message = when {
    score >= 90 -> "훌륭합니다"
    score >= 80 -> "좋습니다"
    else -> "노력하세요"
}

// 값 매칭 형태
val label = when (grade) {
    "A", "B" -> "합격"       // 여러 값 한꺼번에
    in listOf("C", "D") -> "재시험"
    else -> "불합격"
}
```

> **`when`은 반드시 `else`가 있거나 모든 경우를 덮어야 합니다** (값을 반환할 때).
> 이 성질이 뒤에 나올 `sealed class`와 만나면 "새 상태를 추가하면 컴파일 에러로 알려주는"
> 강력한 패턴이 됩니다 — JS의 switch에서 case 빠뜨려서 나는 버그가 구조적으로 사라집니다.

## 1-5. 반복문

```javascript
// JavaScript
for (let i = 0; i < 5; i++) { console.log(i) }

const fruits = ["사과", "바나나", "딸기"]
for (const fruit of fruits) { console.log(fruit) }
fruits.forEach((fruit, index) => console.log(`${index}: ${fruit}`))
```

```kotlin
// Kotlin
for (i in 0 until 5) { println(i) }   // 0,1,2,3,4  (until = 미만)
for (i in 0..4) { println(i) }        // 0,1,2,3,4  (.. = 이하)
for (i in 4 downTo 0) { println(i) }  // 역순
for (i in 0..10 step 2) { println(i) }// 0,2,4,6,8,10

val fruits = listOf("사과", "바나나", "딸기")
for (fruit in fruits) { println(fruit) }

fruits.forEachIndexed { index, fruit -> println("$index: $fruit") }
```

## 1-6. 컬렉션 (배열/리스트)

```javascript
// JavaScript
const nums = [1, 2, 3, 4, 5]
nums.map(x => x * 2)                 // [2,4,6,8,10]
nums.filter(x => x > 3)              // [4,5]
nums.find(x => x > 3)                // 4
nums.reduce((sum, x) => sum + x, 0)  // 15
nums.includes(3)                     // true
nums.length                          // 5

const arr = [1, 2, 3]
arr.push(4); arr.splice(1, 1)
const combined = [...arr1, ...arr2]
```

```kotlin
// Kotlin
val nums = listOf(1, 2, 3, 4, 5)     // 불변 리스트 (기본으로 이걸 씀)

nums.map { it * 2 }                   // [2,4,6,8,10]
nums.filter { it > 3 }                // [4,5]
nums.find { it > 3 }                  // 4 (없으면 null)
nums.sum()                            // 15  (reduce보다 이걸 씀)
nums.contains(3)  // 또는 3 in nums   // true
nums.size                             // 5   (.length 아님!)

// 가변 리스트
val arr = mutableListOf(1, 2, 3)
arr.add(4)
arr.removeAt(1)

val combined = list1 + list2          // 스프레드 대신 +
```

**JS에 없어서 유용한 것들** (실전에서 계속 씁니다):

```kotlin
nums.firstOrNull()                    // 비었으면 null (get(0)은 예외)
nums.sortedBy { it.age }              // 정렬된 새 리스트
nums.groupBy { it.category }          // Map<카테고리, List<항목>>
nums.associateBy { it.id }            // Map<id, 항목> — id로 조회할 때
nums.sumOf { it.price }               // 특정 필드 합
nums.any { it > 3 }  / all / none     // boolean
nums.take(3) / drop(3)                // slice 대용
nums.distinct()                       // 중복 제거
nums.chunked(3)                       // 3개씩 쪼개기
```

> **`it` = 람다의 단일 매개변수 기본 이름.** JS 화살표 함수의 `x =>` 에서 `x`를 생략한 것과 같습니다.
> 중첩되면 헷갈리니 그때는 `{ user -> ... }` 처럼 이름을 붙이세요.

## 1-7. 클래스, data class, sealed class

```javascript
// JavaScript
const user = { name: "홍길동", age: 25 }

class User {
    constructor(name, age) { this.name = name; this.age = age }
    greet() { return `안녕, ${this.name}` }
}
const u = new User("홍길동", 25)
```

```kotlin
// Kotlin — data class가 JS 객체에 가장 가까움
data class User(val name: String, val age: Int)
// 이 한 줄로 생성자, toString, equals, hashCode, copy 전부 자동 생성

val user = User("홍길동", 25)     // new 키워드 없음
println(user.name)

// 메서드 추가
data class User(val name: String, val age: Int) {
    fun greet() = "안녕, $name"   // this.name 대신 name
}

// 일부만 바꿔 복사 (JS 스프레드 대응)
// JS: const u2 = { ...user, age: 26 }
val u2 = user.copy(age = 26)
```

### sealed class ⭐ — UI 상태 표현의 표준

JS에는 없지만 Android 코드를 읽으려면 반드시 알아야 하는 개념입니다.

```kotlin
// "이 타입이 될 수 있는 경우는 아래 3개가 전부다" 를 컴파일러에 알림
sealed interface UiState {
    data object Loading : UiState
    data class Success(val data: List<Todo>) : UiState
    data class Error(val message: String) : UiState
}

// when이 모든 경우를 덮으면 else 없이도 컴파일됨
@Composable
fun Screen(state: UiState) {
    when (state) {
        is UiState.Loading -> CircularProgressIndicator()
        is UiState.Success -> TodoList(state.data)   // 여기선 state.data 접근 가능 (스마트 캐스트)
        is UiState.Error   -> Text(state.message)
    }
}
```

> **왜 좋은가**: 나중에 `Empty` 상태를 추가하면, 그 상태를 처리 안 한 `when`이 **전부 컴파일 에러**가 됩니다.
> JS에서 "로딩 상태 추가했는데 어떤 화면에서 스피너가 안 돌더라" 하는 부류의 버그가 원천 차단됩니다.
>
> `data object` = 값이 없는 단일 인스턴스 (Loading은 데이터가 필요 없으니까).

## 1-8. null 처리

```javascript
// JavaScript
let name = null
console.log(name.length)      // ❌ TypeError (런타임에 터짐)
console.log(name?.length)     // undefined
console.log(name ?? "이름 없음")
```

```kotlin
// Kotlin — null 가능 여부가 타입의 일부
var name: String = "홍길동"
// name = null                 // ❌ 컴파일 에러

var name2: String? = "홍길동"   // ? 붙이면 null 허용
name2 = null                   // ✅

// println(name2.length)       // ❌ 컴파일 에러 — null일 수 있으니까
println(name2?.length)         // ✅ null이면 null (JS의 ?. 와 동일)
println(name2 ?: "이름 없음")   // ✅ null이면 기본값 (JS의 ?? 와 동일)

// null 아님을 단언 — 되도록 쓰지 마세요
println(name2!!.length)        // 틀리면 그 자리에서 크래시

// null이 아닐 때만 실행
name2?.let { println(it.length) }
```

> **`!!` 는 "여기서 크래시 나도 좋다"는 선언입니다.** 초보 때 컴파일러를 이기려고 `!!`를
> 붙이기 쉬운데, 그 순간 Kotlin을 쓰는 이유가 사라집니다.
> 대부분 `?.let {}`, `?: return`, `requireNotNull(x) { "설명" }` 중 하나로 대체됩니다.

## 1-9. 비동기 처리 — 코루틴 ⭐

```javascript
// JavaScript
async function fetchData() {
    try {
        const res = await fetch("https://api.example.com/data")
        return await res.json()
    } catch (e) {
        console.log("에러:", e.message)
    }
}
```

```kotlin
// Kotlin — suspend가 async, 호출 자체가 await처럼 동작
suspend fun fetchData(): WeatherResponse {
    return RetrofitClient.api.getData()   // await 키워드 없이 자동 대기
}
```

**JS와 결정적으로 다른 점: `suspend` 함수는 아무 데서나 못 부릅니다.**

```kotlin
// ❌ 일반 함수에서 직접 호출 불가
fun onClick() {
    fetchData()   // 컴파일 에러: Suspend function should be called only from a coroutine
}

// ✅ 코루틴 스코프 안에서 호출
class MyViewModel : ViewModel() {
    fun load() {
        viewModelScope.launch {    // ViewModel이 죽으면 자동 취소됨
            val data = fetchData()
        }
    }
}

// ✅ Compose 안에서는 LaunchedEffect (= useEffect)
@Composable
fun Screen() {
    LaunchedEffect(Unit) {         // useEffect(() => {...}, [])
        val data = fetchData()
    }
}
```

### 스코프 = "언제 취소되는가"

이게 코루틴의 진짜 가치입니다. JS의 Promise는 한 번 시작하면 취소가 어렵지만,
코루틴은 **화면이 사라지면 진행 중이던 네트워크 요청이 자동으로 취소**됩니다.

| 스코프 | 언제 취소되나 | 쓰는 곳 |
|---|---|---|
| `viewModelScope` | ViewModel이 정리될 때 | ViewModel 안 (가장 많이 씀) |
| `LaunchedEffect(key)` | Composable이 사라지거나 key가 바뀔 때 | Compose UI |
| `rememberCoroutineScope()` | Composable이 사라질 때 | 버튼 클릭 등 이벤트 핸들러 |
| `GlobalScope` | 앱이 죽을 때까지 안 됨 | **쓰지 마세요** (메모리 누수 원인) |

### Dispatcher = "어느 스레드에서 도나"

```kotlin
viewModelScope.launch {                    // 기본: 메인(UI) 스레드
    val data = withContext(Dispatchers.IO) {  // 무거운 IO는 백그라운드로
        readBigFile()
    }
    textState = data                        // 다시 메인 스레드에서 UI 갱신
}
```

> **JS와 큰 차이**: JS는 싱글 스레드라 이런 고민이 없습니다. Android는 **메인 스레드에서
> 네트워크/DB/파일 작업을 하면 앱이 얼어붙고(ANR), 실제로 시스템이 앱을 죽입니다.**
> 다행히 Retrofit·Room은 알아서 IO 스레드로 넘겨주므로, 직접 `withContext(Dispatchers.IO)`를
> 쓸 일은 파일 처리·이미지 변환 같은 경우뿐입니다.

### Flow vs StateFlow (샘플 코드에서 계속 만납니다)

```kotlin
// Flow = 값이 여러 번 흘러나오는 비동기 스트림 (JS: AsyncIterator / RxJS Observable)
fun getAll(): Flow<List<Memo>>          // Room이 DB 변경 시마다 새 리스트를 흘려줌

// StateFlow = "현재 값"이 항상 하나 있는 Flow (JS: Zustand store)
private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
val uiState: StateFlow<UiState> = _uiState.asStateFlow()  // 외부엔 읽기 전용으로 노출
```

| | 초기값 | 용도 |
|---|---|---|
| `Flow` | 없음 | DB 쿼리 결과, 이벤트 스트림 |
| `StateFlow` | 있음 (필수) | **화면 상태** — Compose가 구독 |
| `SharedFlow` | 없음 | 일회성 이벤트 (스낵바 표시 등) |

## 1-10. 스코프 함수 (let / apply / run / also) ⭐

JS엔 없는데 실전 Kotlin 코드엔 도배되어 있어서, 모르면 남의 코드를 못 읽습니다.
**전부 "객체를 잠깐 다루는 문법 설탕"** 이고, 차이는 딱 두 가지뿐입니다.

| 함수 | 객체를 뭐라고 부르나 | 반환값 | 대표 용도 |
|---|---|---|---|
| `let` | `it` | 람다 결과 | **null 체크 후 처리** |
| `apply` | `this` (생략) | 객체 자신 | **객체 설정 후 그대로 반환** |
| `also` | `it` | 객체 자신 | 로깅 등 곁다리 작업 |
| `run` | `this` (생략) | 람다 결과 | 객체 써서 값 계산 |

```kotlin
// let — 가장 많이 씀. "null이 아니면"
user?.let {
    println(it.name)          // user가 null이면 통째로 건너뜀
}

// apply — 설정 코드 묶기 (JS: Object.assign 후 반환)
val intent = Intent(context, MainActivity::class.java).apply {
    putExtra("id", 42)
    flags = Intent.FLAG_ACTIVITY_NEW_TASK
}   // ← intent 자신이 반환됨

// also — 중간에 로그만 끼워넣기
val result = calculate().also { Log.d("TAG", "결과=$it") }

// run — 객체를 써서 다른 값 만들기
val summary = user.run { "$name ($age세)" }
```

> **처음엔 `let`과 `apply` 두 개만 알면 충분합니다.** 나머지는 읽을 줄만 알면 됩니다.

## 1-11. 문법 연습

```
Kotlin Playground: https://play.kotlinlang.org
→ 브라우저에서 바로 실행. 위 예제들을 직접 쳐보세요 (20분이면 됩니다)

Kotlin Koans: https://play.kotlinlang.org/koans
→ 빈칸 채우기식 공식 연습 문제. JS 개발자에게 특히 효율 좋음
```

---

# PART 2: 매핑 치트시트

앱 만들면서 계속 돌아올 페이지입니다. 외우지 말고 북마크하세요.

## 언어 비교

| 개념 | JavaScript | Kotlin |
|------|-----------|--------|
| 상수 | `const x = 1` | `val x = 1` |
| 변수 | `let x = 1` | `var x = 1` |
| 함수 | `function add(a, b)` | `fun add(a: Int, b: Int): Int` |
| 화살표 함수 | `(x) => x * 2` | `{ x -> x * 2 }` 또는 `{ it * 2 }` |
| 옵셔널 체이닝 | `x?.prop` | `x?.prop` (동일) |
| null 병합 | `x ?? "기본"` | `x ?: "기본"` |
| 비동기 | `async` / `await` | `suspend` + 코루틴 스코프 |
| 문자열 보간 | `` `Hello ${name}` `` | `"Hello $name"` / `"${user.name}"` |
| 배열 길이 | `arr.length` | `list.size` |
| 배열 추가 | `arr.push(x)` | `list.add(x)` (mutable일 때) |
| 스프레드 | `[...a, ...b]` | `a + b` |
| 객체 복사+수정 | `{ ...o, age: 26 }` | `o.copy(age = 26)` |
| 출력 | `console.log()` | `println()` / `Log.d()` |
| 삼항 | `a ? b : c` | `if (a) b else c` |
| switch | `switch/case` | `when` |
| 타입 검사 | `typeof x === 'string'` | `x is String` |

## React ↔ Compose 매핑

| React / JS 생태계 | Android |
|-----------|---------|
| 컴포넌트 함수 | `@Composable fun` |
| `useState()` | `remember { mutableStateOf() }` |
| `useState()` + 새로고침에도 유지 | `rememberSaveable { mutableStateOf() }` |
| `useEffect(fn, [dep])` | `LaunchedEffect(dep) { }` |
| `useMemo()` | `remember(dep) { }` |
| `useCallback()` | `remember { { ... } }` (거의 불필요) |
| `useRef()` | `remember { mutableStateOf() }` / `rememberUpdatedState` |
| props | 함수 매개변수 |
| children | 후행 람다 `content: @Composable () -> Unit` |
| Context | `CompositionLocal` |
| React Router | Navigation Compose (`NavHost`) |
| Redux / Zustand | `ViewModel` + `StateFlow` |
| npm / yarn | Gradle |
| fetch / axios | Retrofit + OkHttp |
| localStorage | DataStore (구: SharedPreferences) |
| IndexedDB | Room (SQLite) |
| Storybook | `@Preview` |
| `console.log` | `Log.d("Tag", msg)` |
| Jest | JUnit + Turbine |
| Testing Library | Compose UI Test |

## CSS ↔ Compose Modifier

| CSS | Compose |
|---|---|
| `display: flex; flex-direction: column` | `Column { }` |
| `display: flex; flex-direction: row` | `Row { }` |
| `position: relative` + 겹치기 | `Box { }` |
| `width: 100%` | `Modifier.fillMaxWidth()` |
| `height: 100vh` | `Modifier.fillMaxSize()` |
| `flex: 1` | `Modifier.weight(1f)` |
| `padding: 16px` | `Modifier.padding(16.dp)` |
| `margin: 16px` | 부모의 `Arrangement.spacedBy(16.dp)` 또는 `Spacer` |
| `justify-content` (주축) | `verticalArrangement` (Column) / `horizontalArrangement` (Row) |
| `align-items` (교차축) | `horizontalAlignment` (Column) / `verticalAlignment` (Row) |
| `gap: 8px` | `Arrangement.spacedBy(8.dp)` |
| `border-radius: 8px` | `Modifier.clip(RoundedCornerShape(8.dp))` |
| `background: red` | `Modifier.background(Color.Red)` |
| `overflow: scroll` | `Modifier.verticalScroll(rememberScrollState())` |
| `arr.map(x => <Item/>)` | `LazyColumn { items(arr) { } }` |
| `onClick` | `Modifier.clickable { }` 또는 `Button(onClick=)` |
| `env(safe-area-inset-top)` | `Modifier.systemBarsPadding()` |

> ⚠️ **Modifier는 순서가 의미를 바꿉니다.**
> `Modifier.padding(16.dp).background(Color.Red)` → 패딩 **바깥**은 빨강 아님 (여백 후 배경)
> `Modifier.background(Color.Red).padding(16.dp)` → 패딩 **포함** 영역이 빨강
> CSS와 달리 선언 순서 = 적용 순서입니다. 레이아웃이 이상하면 제일 먼저 의심할 곳.

---

# PART 3: 샘플 앱 만들기

카운터 → 상태관리 → 할 일 목록 → 날씨(API) → 메모(DB) 순서로 난이도가 올라갑니다.

## STEP 1: Hello World — 첫 화면과 Preview

**목표**: Composable 함수, 상태, Preview, edge-to-edge 이해

```kotlin
// MainActivity.kt

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 최신 Android에선 edge-to-edge가 표준입니다.
        // 콘텐츠가 상태바·네비게이션바 영역까지 그려지므로
        // 루트에 systemBarsPadding()을 줘야 시계/노치와 안 겹칩니다.
        enableEdgeToEdge()
        setContent {                       // ReactDOM.render(<App />)
            MyAppTheme {                   // 테마 Provider
                Surface(
                    modifier = Modifier.fillMaxSize().systemBarsPadding()
                ) {
                    HelloScreen()
                }
            }
        }
    }
}

// JS: function HelloScreen() { ... }
@Composable
fun HelloScreen() {
    // JS: const [count, setCount] = useState(0)
    var count by remember { mutableStateOf(0) }

    // JS: <div style={{display:'flex', flexDirection:'column', alignItems:'center'}}>
    Column(
        modifier = Modifier
            .fillMaxSize()          // width:100%; height:100%
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "안녕하세요!",
            style = MaterialTheme.typography.headlineMedium  // 직접 sp 지정보다 이걸 권장
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text(text = "카운트: $count")

        Spacer(modifier = Modifier.height(8.dp))

        // JS: <button onClick={() => setCount(count + 1)}>클릭!</button>
        Button(onClick = { count++ }) {
            Text("클릭!")
        }
    }
}

// 💡 @Preview = 빌드/실행 없이 우측 패널에서 실시간 렌더링
// Compose 학습 속도를 좌우하는 기능입니다. 화면 만들 때마다 반드시 붙이세요.
@Preview(showBackground = true)
@Composable
private fun HelloScreenPreview() {
    MyAppTheme { HelloScreen() }
}
```

### `var count by remember { ... }` 를 뜯어보기

```kotlin
var count by remember { mutableStateOf(0) }
//         ↑ by = 위임. 이게 없으면 count.value 로 써야 함
//              ↑ remember = 리컴포지션이 일어나도 값 유지 (없으면 매번 0으로 리셋)
//                          ↑ mutableStateOf = 값이 바뀌면 화면을 다시 그리라고 알림
```

```kotlin
// by 없이 쓰면 이렇게 됩니다 (같은 코드)
val count = remember { mutableStateOf(0) }
Text("카운트: ${count.value}")
Button(onClick = { count.value++ }) { }
```

> **`remember`를 빼먹으면 어떻게 되나**: 버튼을 눌러 값이 바뀌면 → 화면을 다시 그림 →
> 다시 그릴 때 `mutableStateOf(0)`가 새로 실행됨 → 다시 0.
> **"버튼을 눌러도 숫자가 안 올라가요"의 99%가 이 원인입니다.**

### Edge-to-Edge / SafeArea

최신 Android는 앱이 화면 전체(시계·배터리·네비게이션 바 영역 포함)를 그리도록 강제합니다.
**루트에 `Modifier.systemBarsPadding()`을 안 주면 헤더 텍스트가 상태바와 겹칩니다.**

```kotlin
Modifier.systemBarsPadding()   // 상단 상태바 + 하단 네비바 여백
Modifier.statusBarsPadding()   // 상단만
Modifier.navigationBarsPadding()// 하단만
Modifier.imePadding()          // 키보드 올라올 때 밀어올리기 ⭐ 폼 화면 필수
Modifier.safeDrawingPadding()  // 위 전부 + 디스플레이 컷아웃
```

> **실기기 확인 필수 항목**입니다. 에뮬레이터 기본 설정에서는 잘 안 드러나고,
> 노치 있는 실기기에서 바로 티가 납니다.

---

## STEP 1.5: 상태 관리 제대로 ⭐ (React 개발자가 가장 자주 다치는 곳)

STEP 2로 가기 전에 이것만 확실히 하면 이후가 훨씬 쉬워집니다.

### ① 화면을 돌리면 상태가 날아갑니다

React 웹에는 없는 개념입니다. Android는 **화면 회전, 다크모드 전환, 폰트 크기 변경, 언어 변경** 시
Activity를 통째로 파괴하고 다시 만듭니다.

```kotlin
var count by remember { mutableStateOf(0) }          // ❌ 회전하면 0으로 리셋
var count by rememberSaveable { mutableStateOf(0) }  // ✅ 회전해도 유지
```

| | 리컴포지션 | 화면 회전 | 앱 강제 종료 후 |
|---|---|---|---|
| `remember` | 유지 | **날아감** | 날아감 |
| `rememberSaveable` | 유지 | 유지 | 날아감 |
| `ViewModel` | 유지 | 유지 | 날아감 |
| DataStore / Room | 유지 | 유지 | **유지** |

> **테스트 방법**: 에뮬레이터에서 `Ctrl/Cmd + →` 로 회전시켜 보세요.
> 입력하던 텍스트가 사라지면 `rememberSaveable`로 바꿔야 합니다.
> 실사용자는 이걸 매일 겪습니다 — 반드시 확인하세요.

`rememberSaveable`은 기본 타입만 자동 저장됩니다. `data class`를 저장하려면:

```kotlin
@Parcelize
data class Filter(val query: String, val onlyDone: Boolean) : Parcelable
// build.gradle.kts에 kotlin-parcelize 플러그인 필요

var filter by rememberSaveable { mutableStateOf(Filter("", false)) }
```

### ② 상태 호이스팅 (State Hoisting) — React와 완전히 같은 개념

```kotlin
// ❌ 상태를 안에 가둔 컴포넌트 — 재사용도 테스트도 Preview도 어려움
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) { Text("$count") }
}

// ✅ 상태를 밖으로 끌어올림 (= React의 controlled component)
@Composable
fun Counter(count: Int, onIncrement: () -> Unit) {
    Button(onClick = onIncrement) { Text("$count") }
}

// 부모가 상태를 소유
@Composable
fun Screen() {
    var count by rememberSaveable { mutableStateOf(0) }
    Counter(count = count, onIncrement = { count++ })
}
```

> **규칙**: 상태는 **그 상태를 읽는 모든 컴포저블의 가장 가까운 공통 부모**에 둡니다.
> React에서 배운 그대로입니다. 값은 아래로(`count: Int`), 이벤트는 위로(`onIncrement: () -> Unit`).
> 이걸 UDF(단방향 데이터 흐름)라고 부르며, Android 공식 권장 아키텍처의 핵심입니다.

### ③ 리스트 상태를 바꾸는 법

```kotlin
var todos by remember { mutableStateOf(listOf<Todo>()) }

todos.add(newTodo)                    // ❌ 컴파일 에러 (listOf는 불변)
todos = todos + newTodo               // ✅ 새 리스트 할당 → 화면 갱신
todos = todos.map { if (it.id == id) it.copy(isDone = true) else it }  // ✅

// mutableStateListOf를 쓰면 add/remove 직접 가능 (성능 유리, 큰 리스트에)
val todos = remember { mutableStateListOf<Todo>() }
todos.add(newTodo)                    // ✅ 이건 됨
```

> React에서 `setTodos([...todos, new])`를 쓰던 그 이유(불변성)와 동일합니다.
> **`val list = mutableListOf()` 에 add 하는 건 화면이 안 갱신됩니다** — 상태가 아니라 그냥 리스트라서.

### ④ Activity 생명주기 — 최소한 이것만

```
onCreate  → 화면 생성 (setContent 여기서)
onStart   → 사용자에게 보이기 시작
onResume  → 상호작용 가능
--- 사용자가 홈 버튼 ---
onPause   → 가려짐 (여기서 저장하세요)
onStop    → 완전히 안 보임
onDestroy → 파괴 (회전 시에도 호출됨!)
```

Compose만 쓰면 대부분 직접 다룰 일이 없지만, **"백그라운드 갔다 오면 데이터가 사라져요"**
같은 문제를 만나면 여기를 의심하세요. Compose에서 생명주기를 관찰하려면:

```kotlin
val lifecycleOwner = LocalLifecycleOwner.current
DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event ->
        if (event == Lifecycle.Event.ON_RESUME) { /* 다시 돌아왔을 때 */ }
    }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}
```

---

## STEP 2: 할 일 목록 — 리스트, 입력, CRUD

**목표**: LazyColumn, TextField, 상태 호이스팅 실전, 문자열 리소스

```kotlin
// data/Todo.kt
// JS: { id: crypto.randomUUID(), title: "할 일", isDone: false }
data class Todo(
    val id: String = UUID.randomUUID().toString(),
    val title: String,
    val isDone: Boolean = false
)
```

```kotlin
// ui/TodoScreen.kt

@Composable
fun TodoScreen() {
    // 리스트는 화면 회전에도 살아남아야 하니 ViewModel에 두는 게 정석입니다 (STEP 3에서 다룸).
    // 여기서는 화면 코드에 집중하기 위해 remember로 둡니다.
    var todos by remember { mutableStateOf(listOf<Todo>()) }
    // 입력 중이던 텍스트는 회전 시 반드시 살려야 하므로 rememberSaveable
    var inputText by rememberSaveable { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .systemBarsPadding()
            .imePadding()              // ⭐ 키보드가 입력창을 가리지 않게
            .padding(16.dp)
    ) {
        // ── 입력 영역 ──
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // JS: <input value={inputText} onChange={e => setInputText(e.target.value)} />
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                modifier = Modifier.weight(1f),        // flex: 1
                placeholder = { Text(stringResource(R.string.todo_input_hint)) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = {
                    // 키보드의 완료 버튼으로도 추가되게
                    if (inputText.isNotBlank()) {
                        todos = todos + Todo(title = inputText.trim())
                        inputText = ""
                    }
                })
            )

            Button(
                onClick = {
                    if (inputText.isNotBlank()) {
                        // JS: setTodos([...todos, { id: ..., title: inputText }])
                        todos = todos + Todo(title = inputText.trim())
                        inputText = ""
                    }
                },
                enabled = inputText.isNotBlank()       // 빈 입력이면 비활성
            ) {
                Text(stringResource(R.string.add))
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // ── 리스트 ──
        if (todos.isEmpty()) {
            // 빈 상태 화면 — 실전 앱의 완성도를 가르는 디테일
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(
                    stringResource(R.string.todo_empty),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            // JS: {todos.map(todo => <TodoItem key={todo.id} ... />)}
            LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                items(todos, key = { it.id }) { todo ->      // key = React의 key prop
                    TodoItem(
                        todo = todo,
                        onToggle = {
                            todos = todos.map {
                                if (it.id == todo.id) it.copy(isDone = !it.isDone) else it
                            }
                        },
                        onDelete = { todos = todos.filter { it.id != todo.id } }
                    )
                }
            }
        }
    }
}

// JS: function TodoItem({ todo, onToggle, onDelete }) { ... }
@Composable
fun TodoItem(todo: Todo, onToggle: () -> Unit, onDelete: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onToggle)     // 행 전체를 탭 영역으로 (터치 타깃 확보)
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Checkbox(checked = todo.isDone, onCheckedChange = { onToggle() })

        Text(
            text = todo.title,
            modifier = Modifier.weight(1f),
            textDecoration = if (todo.isDone) TextDecoration.LineThrough else null,
            color = if (todo.isDone) MaterialTheme.colorScheme.onSurfaceVariant
                    else MaterialTheme.colorScheme.onSurface
        )

        IconButton(onClick = onDelete) {
            Icon(
                Icons.Default.Delete,
                // ⭐ contentDescription = 스크린리더가 읽는 텍스트. 생략하면 접근성 위반
                contentDescription = stringResource(R.string.delete_todo, todo.title)
            )
        }
    }
}
```

### 문자열 리소스 — 지금부터 습관 들이세요

```xml
<!-- app/src/main/res/values/strings.xml -->
<resources>
    <string name="app_name">할 일</string>
    <string name="add">추가</string>
    <string name="todo_input_hint">할 일 입력…</string>
    <string name="todo_empty">할 일이 없습니다. 위에서 추가해보세요.</string>
    <string name="delete_todo">%1$s 삭제</string>   <!-- 인자 있는 문자열 -->
</resources>
```

```kotlin
Text(stringResource(R.string.add))
Text(stringResource(R.string.delete_todo, todo.title))   // 인자 전달
```

> **왜 처음부터 이렇게 하나**: 나중에 영어 지원을 추가할 때 `values-en/strings.xml`만
> 만들면 끝납니다. 하드코딩해두면 화면 100개를 전부 뒤져야 합니다.
> 게다가 Android Studio의 lint가 하드코딩 문자열에 경고를 띄웁니다.
> (이 문서의 이후 예제는 지면상 하드코딩하지만, **실제 코드에선 리소스를 쓰세요**.)

---

## STEP 3: 날씨 앱 — API 통신, ViewModel, 네비게이션

**목표**: Retrofit, ViewModel + StateFlow, 타입 안전 네비게이션, 로딩/에러 처리

### 사전 준비: OpenWeatherMap API 키

```
1. https://openweathermap.org 회원가입
2. API Keys 메뉴에서 기본 키 복사 (무료, 분당 60회)
3. ⚠️ 키를 코드에 하드코딩하지 마세요 — 아래 방법을 쓰세요
```

**API 키 안전하게 넣기:**

```properties
# local.properties  (git에 커밋 안 됨)
WEATHER_API_KEY=여기에_키
```

```kotlin
// app/build.gradle.kts
import java.util.Properties

val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) load(f.inputStream())
}

android {
    defaultConfig {
        buildConfigField("String", "WEATHER_API_KEY", "\"${localProps["WEATHER_API_KEY"]}\"")
    }
    buildFeatures { buildConfig = true }
}
```

```kotlin
// 코드에서 사용
BuildConfig.WEATHER_API_KEY
```

> ⚠️ **이것도 완벽한 보안은 아닙니다.** APK를 뜯으면 문자열이 보입니다.
> 과금되는 API 키는 **반드시 서버를 거쳐서** 호출해야 합니다.
> 학습용/무료 티어라면 위 방법으로 충분합니다 (최소한 GitHub에 유출되진 않으니까).

### 의존성

```kotlin
dependencies {
    // Retrofit = fetch/axios
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")

    // Navigation = React Router
    implementation("androidx.navigation:navigation-compose:2.8.5")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")

    // ViewModel + 생명주기 인식 상태 수집
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")

    // Coil = 이미지 로딩 (Coil 3부터 패키지가 io.coil-kt.coil3)
    implementation("io.coil-kt.coil3:coil-compose:3.0.4")
    implementation("io.coil-kt.coil3:coil-network-okhttp:3.0.4")
}
```

> 버전은 작성 시점 기준입니다. [maven.google.com](https://maven.google.com) 또는
> IDE의 "Update Available" 알림을 따라가세요. Android Studio에서 버전 숫자에 커서를 두면
> 최신 버전을 알려줍니다.

### API 서비스 정의

```kotlin
// data/WeatherApi.kt

// JSON 구조를 data class로 (JS는 그냥 객체를 받았지만 여긴 타입이 필요)
data class WeatherResponse(
    val main: Main,
    val weather: List<Weather>,
    val name: String
)
data class Main(val temp: Double, val humidity: Int)
data class Weather(val description: String, val icon: String)

// JS: fetch(url) 을 선언적으로 정의
interface WeatherApi {
    @GET("weather")
    suspend fun getWeather(
        @Query("q") city: String,
        @Query("appid") apiKey: String = BuildConfig.WEATHER_API_KEY,
        @Query("units") units: String = "metric",
        @Query("lang") lang: String = "kr"
    ): WeatherResponse
}

// JS: const api = axios.create({ baseURL: '...' })
object RetrofitClient {
    val weatherApi: WeatherApi = Retrofit.Builder()
        .baseUrl("https://api.openweathermap.org/data/2.5/")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(WeatherApi::class.java)
}
```

> **JSON 필드명이 Kotlin 변수명과 다를 때**: `@SerializedName("feels_like") val feelsLike: Double`
> (Gson 기준). JS에서 `data.feels_like`로 그냥 쓰던 것과 달리 매핑을 명시해야 합니다.

### ViewModel — 화면 상태의 소유자

```kotlin
// ui/weather/WeatherViewModel.kt

sealed interface WeatherUiState {
    data object Idle : WeatherUiState
    data object Loading : WeatherUiState
    data class Success(val data: WeatherResponse) : WeatherUiState
    data class Error(val message: String) : WeatherUiState
}

class WeatherViewModel : ViewModel() {
    // JS: const [uiState, setUiState] = useState(...)
    private val _uiState = MutableStateFlow<WeatherUiState>(WeatherUiState.Idle)
    val uiState: StateFlow<WeatherUiState> = _uiState.asStateFlow()  // 외부엔 읽기 전용

    fun fetchWeather(city: String) {
        viewModelScope.launch {          // 화면이 사라지면 자동 취소
            _uiState.value = WeatherUiState.Loading
            _uiState.value = try {
                WeatherUiState.Success(RetrofitClient.weatherApi.getWeather(city))
            } catch (e: IOException) {
                WeatherUiState.Error("네트워크에 연결할 수 없습니다")
            } catch (e: HttpException) {
                WeatherUiState.Error(
                    if (e.code() == 404) "도시를 찾을 수 없습니다" else "서버 오류 (${e.code()})"
                )
            } catch (e: Exception) {
                WeatherUiState.Error(e.message ?: "알 수 없는 오류")
            }
        }
    }
}
```

> **에러를 종류별로 나눠 잡으세요.** `catch (e: Exception)` 하나로 뭉뚱그리면
> 사용자에게 "java.net.UnknownHostException" 같은 걸 보여주게 됩니다.
> 네트워크 없음 / 404 / 서버 오류는 사용자가 취해야 할 행동이 다릅니다.

**ViewModel이 뭘 해결하나** (React 개발자용 설명):

| 문제 | Compose `remember` | ViewModel |
|---|---|---|
| 화면 회전 | 상태 소실 | **유지** |
| 화면이 커져 컴포저블이 분리될 때 | 공유 어려움 | 여러 화면이 공유 가능 |
| 비즈니스 로직 단위 테스트 | UI 없이 못 함 | **UI 없이 가능** |
| 코루틴 취소 | 직접 관리 | `viewModelScope`가 자동 |

### 화면 + 타입 안전 네비게이션

Navigation Compose 2.8부터 **문자열 route 대신 타입으로** 화면을 정의할 수 있습니다.
오타로 인한 런타임 크래시가 사라지므로 신규 코드는 이 방식을 쓰세요.

```kotlin
// navigation/Routes.kt
import kotlinx.serialization.Serializable

@Serializable object SearchRoute
@Serializable data class WeatherRoute(val city: String)
```

```kotlin
// navigation/AppNavigation.kt

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    // JS: <BrowserRouter><Routes>...</Routes></BrowserRouter>
    NavHost(navController = navController, startDestination = SearchRoute) {
        composable<SearchRoute> {
            SearchScreen(
                onSearch = { city ->
                    // JS: navigate(`/weather/${city}`)
                    navController.navigate(WeatherRoute(city))   // 타입 안전
                }
            )
        }
        composable<WeatherRoute> { backStackEntry ->
            val route: WeatherRoute = backStackEntry.toRoute()   // 파싱 불필요
            WeatherScreen(
                city = route.city,
                onBack = { navController.popBackStack() }
            )
        }
    }
}
```

<details>
<summary>구버전(문자열 route) 방식 — 기존 코드/튜토리얼에서 계속 보게 됩니다</summary>

```kotlin
NavHost(navController, startDestination = "search") {
    composable("search") { SearchScreen(onSearch = { navController.navigate("weather/$it") }) }
    composable("weather/{city}") { entry ->
        val city = entry.arguments?.getString("city") ?: ""
        WeatherScreen(city = city, onBack = { navController.popBackStack() })
    }
}
```
문자열 조합이라 오타가 컴파일에 안 잡히고, 특수문자가 든 인자는 URL 인코딩이 필요합니다.
</details>

```kotlin
@Composable
fun SearchScreen(onSearch: (String) -> Unit) {
    var city by rememberSaveable { mutableStateOf("") }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).imePadding(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("날씨 검색", style = MaterialTheme.typography.headlineLarge)
        Spacer(Modifier.height(24.dp))
        OutlinedTextField(
            value = city,
            onValueChange = { city = it },
            placeholder = { Text("도시 이름 입력") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { onSearch(city.trim()) },
            enabled = city.isNotBlank(),
            modifier = Modifier.fillMaxWidth()
        ) { Text("검색") }
    }
}

@Composable
fun WeatherScreen(
    city: String,
    onBack: () -> Unit,
    viewModel: WeatherViewModel = viewModel()
) {
    // ⭐ collectAsState 대신 collectAsStateWithLifecycle 을 쓰세요.
    //   앱이 백그라운드일 때 불필요한 수집을 멈춰 배터리를 아낍니다.
    //   (lifecycle-runtime-compose 의존성 필요)
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // JS: useEffect(() => { fetchWeather(city) }, [city])
    LaunchedEffect(city) { viewModel.fetchWeather(city) }

    Column(Modifier.fillMaxSize().systemBarsPadding().padding(16.dp)) {
        IconButton(onClick = onBack) {
            // ⚠️ Icons.Default.ArrowBack은 deprecated.
            // AutoMirrored 버전은 아랍어 등 RTL 언어에서 자동으로 좌우 반전됩니다
            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "뒤로")
        }

        // JS: {loading && <Spinner/>} {error && <p/>} {data && <Info/>}
        when (val state = uiState) {
            is WeatherUiState.Idle -> Unit
            is WeatherUiState.Loading ->
                Box(Modifier.fillMaxSize(), Alignment.Center) { CircularProgressIndicator() }

            is WeatherUiState.Success -> {
                val w = state.data
                Column(
                    Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(w.name, style = MaterialTheme.typography.headlineLarge)
                    Text("%.1f°C".format(w.main.temp), fontSize = 64.sp)
                    Text(w.weather.firstOrNull()?.description ?: "")
                    Text("습도: ${w.main.humidity}%")
                }
            }

            is WeatherUiState.Error -> {
                Column(
                    Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(state.message, color = MaterialTheme.colorScheme.error)
                    Spacer(Modifier.height(8.dp))
                    // 에러 화면엔 반드시 재시도 버튼을 두세요
                    Button(onClick = { viewModel.fetchWeather(city) }) { Text("다시 시도") }
                }
            }
        }
    }
}
```

> **`viewModel()` 기본값 매개변수 패턴**을 눈여겨보세요.
> 이렇게 두면 Preview나 테스트에서 가짜 ViewModel을 주입할 수 있습니다.

---

## STEP 4: 메모 앱 (완성형) — 로컬 DB, 이미지, 테마

**목표**: Room 전체 흐름, DataStore, 이미지 선택, 다크모드/Dynamic Color

### ① Room — 로컬 데이터베이스

```kotlin
// build.gradle.kts
plugins {
    id("com.google.devtools.ksp") version "2.0.21-1.0.28"   // Kotlin 버전과 맞춰야 함
}
dependencies {
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
}
```

> ⚠️ **KSP 버전은 Kotlin 버전과 짝이 맞아야 합니다** (`2.0.21-1.0.28` 앞부분이 Kotlin 버전).
> 안 맞으면 "ksp is too old for kotlin" 류 에러가 납니다.

```kotlin
// data/Memo.kt  — 테이블 정의
@Entity(tableName = "memos")
data class Memo(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val title: String,
    val content: String,
    val imageUri: String? = null,
    val createdAt: Long = System.currentTimeMillis()   // JS: Date.now()
)

// data/MemoDao.kt  — 쿼리 정의
@Dao
interface MemoDao {
    // Flow로 반환하면 DB가 바뀔 때마다 자동으로 새 값이 흘러나옴 (구독)
    @Query("SELECT * FROM memos ORDER BY createdAt DESC")
    fun getAll(): Flow<List<Memo>>

    @Query("SELECT * FROM memos WHERE id = :id")
    suspend fun getById(id: String): Memo?

    @Query("SELECT * FROM memos WHERE title LIKE '%' || :q || '%'")
    fun search(q: String): Flow<List<Memo>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(memo: Memo)

    @Delete
    suspend fun delete(memo: Memo)
}

// data/AppDatabase.kt  — DB 본체
@Database(entities = [Memo::class], version = 1, exportSchema = true)
abstract class AppDatabase : RoomDatabase() {
    abstract fun memoDao(): MemoDao

    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null

        fun get(context: Context): AppDatabase =
            INSTANCE ?: synchronized(this) {
                Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "app.db"
                ).build().also { INSTANCE = it }
            }
    }
}
```

**ViewModel에서 쓰기:**

```kotlin
class MemoViewModel(app: Application) : AndroidViewModel(app) {
    private val dao = AppDatabase.get(app).memoDao()

    // Flow → StateFlow 변환. UI가 없을 땐 5초 후 수집 중단(배터리 절약)
    val memos: StateFlow<List<Memo>> = dao.getAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun save(memo: Memo) = viewModelScope.launch { dao.upsert(memo) }
    fun delete(memo: Memo) = viewModelScope.launch { dao.delete(memo) }
}
```

> ⚠️ **스키마를 바꾸면(컬럼 추가 등) `version`을 올리고 마이그레이션을 써야 합니다.**
> 안 그러면 앱 실행 시 `IllegalStateException: Room cannot verify the data integrity` 크래시.
> 개발 중에는 `.fallbackToDestructiveMigration()`(데이터 삭제 후 재생성)로 넘겨도 되지만,
> **출시 후에는 절대 안 됩니다** — 사용자 데이터가 전부 날아갑니다.
> 실제 마이그레이션은 [Room 마이그레이션 문서](https://developer.android.com/training/data-storage/room/migrating-db-versions) 참고.

### ② DataStore — 간단한 설정값 (SharedPreferences 후속)

```kotlin
// implementation("androidx.datastore:datastore-preferences:1.1.1")

val Context.settings by preferencesDataStore(name = "settings")
private val DARK_MODE = booleanPreferencesKey("dark_mode")

// 읽기 (Flow — 값이 바뀌면 자동 반영)
val darkModeFlow: Flow<Boolean> = context.settings.data.map { it[DARK_MODE] ?: false }

// 쓰기 (suspend)
suspend fun setDarkMode(on: Boolean) {
    context.settings.edit { it[DARK_MODE] = on }
}
```

> **localStorage와 다른 점**: 읽기가 **비동기**입니다. SharedPreferences는 동기라
> 메인 스레드를 막는 문제가 있어서 DataStore로 대체됐습니다. 신규 코드는 DataStore를 쓰세요.

### ③ 이미지 선택

```kotlin
// Photo Picker — 권한이 필요 없는 최신 방식 ⭐
@Composable
fun ImagePickerButton(onPicked: (Uri?) -> Unit) {
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri -> onPicked(uri) }

    Button(onClick = {
        launcher.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
    }) {
        Icon(Icons.Default.AddAPhoto, contentDescription = null)
        Spacer(Modifier.width(8.dp))
        Text("사진 추가")
    }
}
```

> **`PickVisualMedia`를 쓰면 `READ_MEDIA_IMAGES` 권한을 요청할 필요가 없습니다.**
> 사용자가 고른 사진만 시스템이 넘겨주기 때문입니다. 권한 요청 = 이탈률이므로 큰 이득입니다.
> 갤러리 전체를 훑어야 하는 앱이 아니라면 항상 이걸 쓰세요.

**선택한 이미지 표시** (Coil — JS의 `<img src>`에 해당):

```kotlin
AsyncImage(
    model = imageUri,
    contentDescription = "첨부 이미지",
    modifier = Modifier.fillMaxWidth().height(200.dp),
    contentScale = ContentScale.Crop          // CSS: object-fit: cover
)
```

> ⚠️ **URI 영구 권한**: 앱을 껐다 켜면 저장해둔 이미지 URI 접근이 막힐 수 있습니다.
> 오래 보관할 이미지는 `contentResolver.takePersistableUriPermission(...)`을 호출하거나,
> **앱 내부 저장소로 파일을 복사**하는 게 안전합니다 (후자를 권장).

### ④ 테마 / 다크모드 / Dynamic Color

```kotlin
// ui/theme/Theme.kt
@Composable
fun MyAppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),  // JS: matchMedia('(prefers-color-scheme: dark)')
    dynamicColor: Boolean = true,                 // 사용자 배경화면 기반 자동 테마
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val ctx = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(ctx) else dynamicLightColorScheme(ctx)
        }
        darkTheme -> darkColorScheme()
        else -> lightColorScheme()
    }

    MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
}
```

> **Dynamic Color는 Android의 공짜 차별화 요소**입니다. Android 12+ 사용자의 배경화면 색으로
> 앱 테마가 자동으로 맞춰집니다. 한 줄로 "이 앱 신경 썼네" 인상을 줍니다.
>
> **다크모드 필수 규칙**: 색을 `Color.Black` / `Color.White`로 직접 쓰지 마세요.
> 항상 `MaterialTheme.colorScheme.onSurface` 같은 토큰을 쓰면 다크모드가 자동으로 됩니다.
> **에뮬레이터에서 다크모드 켜보는 걸 습관화**하세요 — 흰 글자에 흰 배경이 자주 나옵니다.

---

# PART 4: 실전 보강

샘플 앱을 끝낸 시점에 부족한 부분들. 실제 출시할 앱이라면 전부 마주칩니다.

## 4-1. 디버깅 / 로그

```kotlin
import android.util.Log

Log.d("MyTag", "디버그 메시지")     // Debug
Log.i("MyTag", "정보")
Log.w("MyTag", "경고")
Log.e("MyTag", "에러", exception)   // 예외 객체를 넘기면 스택트레이스까지
```

**Logcat 보는 법**: Android Studio 하단 "Logcat" 탭 → 검색창에
`tag:MyTag` / `package:mine` / `level:error` 조합으로 필터링.

`package:mine`은 **내 앱 로그만** 보여줍니다. 시스템 로그에 파묻히지 않으려면 이걸 쓰세요.

> ⚠️ **릴리즈 빌드에 로그를 남기지 마세요.** 민감 정보가 노출되고 성능도 떨어집니다.
> R8의 `-assumenosideeffects` 규칙으로 릴리즈에서 Log 호출을 제거하거나,
> [Timber](https://github.com/JakeWharton/timber) 같은 래퍼로 빌드 타입별 분기를 쓰세요.

**브레이크포인트**: 줄 번호 옆 클릭 → 실행이 멈춤 → 변수 검사.
JS의 `debugger`와 같지만 훨씬 강력합니다 (조건부 중단점, 값 변경 후 재개 등).

**Layout Inspector**: Tools → Layout Inspector. 실행 중인 화면의 컴포저블 트리를 보여줍니다.
"이 여백이 왜 생겼지?"를 추측 대신 확인으로 해결할 수 있습니다.

## 4-2. 권한 처리

**1단계: AndroidManifest.xml 선언**
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>  <!-- Android 13+ 알림 -->
```

**2단계: 런타임 권한 요청**
```kotlin
@Composable
fun CameraButton() {
    val context = LocalContext.current
    var showRationale by remember { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) { /* 카메라 사용 */ }
        else { showRationale = true }
    }

    Button(onClick = {
        val already = ContextCompat.checkSelfPermission(
            context, Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED

        if (already) { /* 바로 사용 */ }
        else launcher.launch(Manifest.permission.CAMERA)
    }) { Text("카메라 사용") }

    if (showRationale) {
        AlertDialog(
            onDismissRequest = { showRationale = false },
            title = { Text("카메라 권한이 필요합니다") },
            text = { Text("사진 촬영 기능을 쓰려면 설정에서 권한을 허용해주세요.") },
            confirmButton = {
                TextButton(onClick = {
                    // 사용자를 앱 설정 화면으로 보내기
                    context.startActivity(Intent(
                        Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                        Uri.fromParts("package", context.packageName, null)
                    ))
                }) { Text("설정 열기") }
            }
        )
    }
}
```

**권한 설계 3원칙:**
1. **필요한 순간에 요청** — 앱 시작하자마자 권한 5개 요청하면 사용자가 나갑니다
2. **거부당했을 때의 화면을 반드시 만들 것** — 두 번 거부하면 시스템 다이얼로그가 아예 안 뜹니다
3. **권한이 필요 없는 대안을 먼저 검토** — Photo Picker(권한 불필요) vs READ_MEDIA_IMAGES(권한 필요)

> **Android 13+ 알림 권한**: `POST_NOTIFICATIONS`는 런타임 요청이 필요합니다.
> 예전 코드를 참고하다 보면 이게 빠져 있어서 "알림이 안 와요" 문제를 만납니다.

## 4-3. 인앱 결제와 구독 (수익화)

웹의 결제 버튼은 서버 API를 호출하지만, 앱 안의 디지털 상품은 **Google Play Billing**을 거칩니다.
Play Console에서 먼저 일회성 상품 `premium_theme`와 구독 `pro_monthly`를 만들고 활성화하세요.

```kotlin
// app/build.gradle.kts — 버전은 공식 릴리즈 노트의 최신 안정판으로 맞추세요
dependencies {
    implementation("com.android.billingclient:billing-ktx:<latest-version>")
}
```

⭐ React의 전역 이벤트 구독처럼 `PurchasesUpdatedListener`를 **구매 버튼보다 먼저** 준비합니다.

```kotlin
class BillingManager(private val context: Context) : PurchasesUpdatedListener {
    private val billingClient = BillingClient.newBuilder(context)
        .setListener(this)                 // ⭐ 구매 요청 전에 리스너 등록
        .enablePendingPurchases(
            PendingPurchasesParams.newBuilder().enableOneTimeProducts().build()
        )
        .enableAutoServiceReconnection()
        .build()

    fun connect(onReady: () -> Unit) {
        billingClient.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) onReady()
            }
            override fun onBillingServiceDisconnected() = Unit
        })
    }

    fun queryProducts() {
        val products = listOf(
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId("premium_theme")
                .setProductType(BillingClient.ProductType.INAPP)
                .build(),
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId("pro_monthly")
                .setProductType(BillingClient.ProductType.SUBS)
                .build()
        )
        billingClient.queryProductDetailsAsync(
            QueryProductDetailsParams.newBuilder().setProductList(products).build()
        ) { result, response ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                // response.productDetailsList를 StateFlow에 넣어 Compose UI 갱신
            }
        }
    }
}
```

구독은 상품 ID 아래에 **base plan**이 있고, 할인·무료 체험은 offer입니다. 사용자가 선택 가능한
`subscriptionOfferDetails`에서 `basePlanId`를 확인하고 그 항목의 `offerToken`을 결제에 넘깁니다.

```kotlin
fun BillingManager.purchase(activity: Activity, product: ProductDetails, offerToken: String? = null) {
    val item = BillingFlowParams.ProductDetailsParams.newBuilder()
        .setProductDetails(product)
        .apply { offerToken?.let(::setOfferToken) }
        .build()
    billingClient.launchBillingFlow(
        activity,
        BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(item)).build()
    )
}

override fun onPurchasesUpdated(result: BillingResult, purchases: List<Purchase>?) {
    if (result.responseCode == BillingClient.BillingResponseCode.OK) {
        purchases.orEmpty().forEach(::processPurchase)
    }
}

private fun processPurchase(purchase: Purchase) {
    if (purchase.purchaseState != Purchase.PurchaseState.PURCHASED) return

    // 서버에서 purchaseToken 검증 권장. 검증 성공 뒤 상품을 열고 acknowledge합니다.
    val productIds = purchase.products // ⭐ 거래의 다른 ID가 아니라 productId 목록
    if ("premium_theme" in productIds || "pro_monthly" in productIds) grantEntitlement(productIds)

    if (!purchase.isAcknowledged) {
        billingClient.acknowledgePurchase(
            AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(purchase.purchaseToken).build()
        ) { /* OK인지 확인하고 실패 시 재시도 */ }
    }
}
```

⚠️ **`productId`로 entitlement를 매핑하세요.** 주문 ID나 purchase token 같은 다른 `id` 필드를
상품 키로 쓰면 결제는 성공했는데 기능이 안 열리는 버그가 납니다. token은 거래 검증/중복 방지용입니다.

⚠️ **acknowledge는 3일 내 필수입니다.** `PURCHASED` 상태를 검증하고 혜택을 지급한 뒤
`acknowledgePurchase`(소모품은 `consumeAsync`)하지 않으면 **3일 후 자동 환불**되고 권한도 회수됩니다.

앱 재설치·기기 변경에 대비해 시작 시와 **구매 복원** 버튼에서 현재 소유 항목을 다시 조회합니다.

```kotlin
fun restorePurchases() {
    listOf(BillingClient.ProductType.INAPP, BillingClient.ProductType.SUBS).forEach { type ->
        billingClient.queryPurchasesAsync(
            QueryPurchasesParams.newBuilder().setProductType(type).build()
        ) { result, purchases ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                purchases.forEach(::processPurchase)
            }
        }
    }
}
```

### 출시 전에 반드시 확인

- ⚠️ 리스너는 구매 요청 **전에** 등록하세요. 결제 중 백그라운드에 갔다 돌아온 완료 거래도 처리해야 합니다.
- ⚠️ 눈에 보이는 **구매 복원** 버튼을 두세요. iOS도 함께 내는 앱이라면 App Store 심사 필수 항목입니다.
- ⚠️ 환불·취소·구독 만료는 Play 실시간 개발자 알림 + Developer API, 또는 앱 시작 시 재검증으로
  감지해 entitlement를 회수하세요. 로컬 Boolean 하나를 영구 권한처럼 믿으면 안 됩니다.
- ⚠️ Android 테스트는 Play Console의 **라이선스 테스터**를 등록하고 테스트 트랙에서
  **Play 스토어로 설치한 빌드**로 하세요. 사이드로드 APK는 서명/설치 경로가 달라 상품 목록이 빌 수 있습니다.
- ⚠️ 가격은 `formattedPrice` 등 스토어가 준 현지화 문자열을 표시하세요. `₩4,900` 하드코딩은
  환율·세금과 불일치하고 스토어 가격 표시 정책을 위반할 수 있습니다.
- ⭐ 페이월에는 무료 기능과 유료 기능, 결제 주기·자동 갱신 조건을 정직하게 씁니다.
  가짜 할인 타이머, 미리 선택된 고가 플랜, 찾기 힘든 닫기 버튼 같은 다크패턴은 쓰지 마세요.

→ 공식 문서: [Google Play Billing 통합](https://developer.android.com/google/play/billing/integrate),
[구매 테스트](https://developer.android.com/google/play/billing/test)

## 4-4. 릴리즈 빌드 / 서명

### Keystore 생성

```bash
# 한 번만 실행. 25년 유효
keytool -genkeypair -v \
  -keystore release.keystore \
  -alias my-app \
  -keyalg RSA -keysize 2048 -validity 9125 \
  -dname "CN=My App, O=MyOrg, L=Seoul, C=KR"
```

> 🚨 **이 파일과 비밀번호를 잃어버리면 앱 업데이트가 영원히 불가능합니다.**
> - 클라우드(iCloud/Google Drive) + 오프라인 백업 2곳 이상에 보관
> - 비밀번호는 패스워드 매니저에
> - **Play App Signing에 가입하면** Google이 최종 서명 키를 보관해주므로 업로드 키를 잃어도
>   복구 신청이 가능합니다. 신규 앱은 기본으로 활성화되니 그대로 두세요.

### 비밀번호 분리

```properties
# keystore.properties  (⚠️ .gitignore에 추가!)
storeFile=release.keystore
storePassword=xxx
keyAlias=my-app
keyPassword=xxx
```

```kotlin
// app/build.gradle.kts
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) load(f.inputStream())
}

android {
    signingConfigs {
        create("release") {
            storeFile = file(keystoreProps["storeFile"] as String)
            storePassword = keystoreProps["storePassword"] as String
            keyAlias = keystoreProps["keyAlias"] as String
            keyPassword = keystoreProps["keyPassword"] as String
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### AAB 빌드

```bash
./gradlew bundleRelease
# → app/build/outputs/bundle/release/app-release.aab
# 이 파일을 Play Console에 업로드 (APK가 아니라 AAB입니다)
```

> **릴리즈 빌드는 반드시 실기기에서 테스트**하세요. R8 난독화 때문에
> 디버그에선 멀쩡하다가 릴리즈에서만 크래시 나는 경우가 흔합니다 (다음 절 참고).

## 4-5. R8 / ProGuard

릴리즈 빌드에서 `isMinifyEnabled = true`면 R8이 미사용 코드를 제거하고 클래스명을 난독화합니다.
앱 크기가 30~50% 줄어듭니다.

**부작용**: 리플렉션을 쓰는 라이브러리(Gson, Retrofit 등)는 클래스가 지워지거나 이름이 바뀌면
동작하지 않습니다. `proguard-rules.pro`에 보존 규칙이 필요합니다.

```proguard
# Gson/Retrofit이 리플렉션으로 읽는 데이터 클래스 보존
-keep class com.yourname.app.data.model.** { *; }

# Retrofit
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation

# 릴리즈에서 Log 호출 제거 (선택)
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
}
```

> **증상**: 디버그 빌드는 정상인데 릴리즈에서 "JSON 파싱 결과가 전부 null" 또는
> `ClassNotFoundException`. 거의 항상 keep 규칙 누락입니다.
> 요즘 대부분의 라이브러리는 자체 규칙을 포함하지만, **본인이 만든 데이터 클래스는 직접 보존**해야 합니다.

## 4-6. 흔한 에러 읽는 법

### 컴파일 에러

```
e: file:///.../TodoScreen.kt:42:11 Unresolved reference: LazyColumn
```
→ import 누락. `Alt+Enter`(Windows) / `Option+Enter`(Mac)로 자동 해결.
그래도 안 되면 의존성 자체가 없는 것.

```
e: Type mismatch: inferred type is String? but String was expected
```
→ null 가능 값을 null 불가 자리에 넣음. `?: "기본값"` 또는 `?.let { }` 로 처리.

### 런타임 크래시

```
FATAL EXCEPTION: main
java.lang.NullPointerException: ...
    at com.yourname.app.ui.TodoScreen(TodoScreen.kt:57)   ← 여기가 내 코드
    at androidx.compose...                                  ← 프레임워크 (무시)
```
→ Logcat에서 `FATAL EXCEPTION` 검색 → 스택트레이스에서 **내 패키지명이 나오는 첫 줄**이 범인.

```
android.view.WindowLeaked / NetworkOnMainThreadException
```
→ 메인 스레드에서 네트워크 호출. `viewModelScope.launch { }` 안으로 옮기세요.

### Compose 특유

```
java.lang.IllegalStateException: Reading a state that was created after the composition
```
→ 컴포지션 도중에 상태를 만들고 바로 읽음. `remember`로 감싸세요.

```
androidx.compose.runtime.internal: Composable invocations can only happen
from the context of a @Composable function
```
→ 일반 함수/람다 안에서 `Text()` 등을 호출. 함수에 `@Composable`을 붙이거나 위치를 옮기세요.

> **막히면 에러 전문을 Claude에 붙여넣으세요.** Kotlin/Compose 에러는 메시지가 길지만
> 패턴이 정형화돼 있어서 AI가 거의 정확히 잡아냅니다.

## 4-7. 테스트 ⭐ (신규)

출시할 앱이라면 최소한 ViewModel 로직만이라도 테스트하세요.

```kotlin
// build.gradle.kts
testImplementation("junit:junit:4.13.2")
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
testImplementation("app.cash.turbine:turbine:1.2.0")          // Flow 테스트

androidTestImplementation("androidx.compose.ui:ui-test-junit4")
debugImplementation("androidx.compose.ui:ui-test-manifest")
```

**① ViewModel 단위 테스트** (JS의 Jest에 해당 — 기기 없이 빠르게 돕니다)

```kotlin
class WeatherViewModelTest {
    @get:Rule val dispatcherRule = MainDispatcherRule()   // 코루틴 테스트용 룰

    @Test
    fun `도시 검색 성공하면 Success 상태가 된다`() = runTest {
        val vm = WeatherViewModel(fakeRepository)

        vm.fetchWeather("Seoul")

        vm.uiState.test {                                  // Turbine
            assertEquals(WeatherUiState.Loading, awaitItem())
            val success = awaitItem() as WeatherUiState.Success
            assertEquals("Seoul", success.data.name)
        }
    }
}
```

> **함수명에 백틱(`` ` ``)으로 한글 문장을 쓸 수 있습니다.** 테스트 이름이 곧 명세가 되니
> 적극 활용하세요 (테스트 코드 한정 관례).

**② Compose UI 테스트** (JS의 Testing Library에 해당)

```kotlin
class TodoScreenTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun `할 일을 추가하면 목록에 나타난다`() {
        composeRule.setContent { TodoScreen() }

        composeRule.onNodeWithText("할 일 입력…").performTextInput("우유 사기")
        composeRule.onNodeWithText("추가").performClick()

        composeRule.onNodeWithText("우유 사기").assertIsDisplayed()
    }
}
```

> **부수 효과**: UI 테스트를 쓰려면 `contentDescription`과 텍스트가 제대로 붙어 있어야 합니다.
> 즉 **테스트를 쓰면 접근성이 저절로 좋아집니다.**

**어디까지 할 것인가** (개인 개발자 기준 현실적 권장):
- ✅ ViewModel + 순수 로직(계산, 파싱, 검증) → 단위 테스트. 비용 대비 효과가 압도적
- △ 핵심 사용자 흐름 1~2개 → UI 테스트
- ❌ 모든 화면 UI 테스트 → 유지보수 비용이 이득을 넘습니다

## 4-8. 접근성 & 다국어 ⭐ (신규)

### 접근성 (Accessibility)

```kotlin
// ① 모든 아이콘/이미지에 설명 (또는 명시적 null)
Icon(Icons.Default.Delete, contentDescription = "삭제")
Icon(Icons.Default.Star, contentDescription = null)   // 장식용이면 null (생략 아님)

// ② 터치 타깃 최소 48dp
IconButton(onClick = {}) { }        // IconButton은 기본 48dp — 직접 만들 땐 주의
Modifier.size(48.dp)
Modifier.minimumInteractiveComponentSize()

// ③ 여러 요소를 하나로 읽히게 묶기
Row(modifier = Modifier.semantics(mergeDescendants = true) {
    contentDescription = "우유 사기, 완료됨"
}) { Checkbox(...); Text(...) }

// ④ 상태 변화를 스크린리더에 알리기
Modifier.semantics { stateDescription = if (isDone) "완료" else "미완료" }
```

**확인 방법:**
1. 설정 → 접근성 → TalkBack 켜기 → 앱을 눈 감고 써보기 (5분이면 문제가 다 드러납니다)
2. 설정 → 디스플레이 → 글꼴 크기 최대로 → 레이아웃이 깨지는지 확인
3. Android Studio의 **Accessibility Scanner** 또는 lint 경고 확인

> **왜 신경 쓰나**: 법적 요구(공공/기업 대상)이기도 하지만, 실용적으로는
> **글꼴 크기 최대 설정을 쓰는 사용자가 생각보다 많습니다.** 여기서 레이아웃이 깨지면
> 그 사용자는 앱을 못 씁니다. 고정 `height`를 남발하지 말고 `wrapContentHeight`를 쓰세요.

### 다국어

```
res/values/strings.xml       ← 기본 (한국어)
res/values-en/strings.xml    ← 영어
res/values-ja/strings.xml    ← 일본어
```

```xml
<!-- 복수형 처리 -->
<plurals name="todo_count">
    <item quantity="other">할 일 %d개</item>
</plurals>
```
```kotlin
pluralStringResource(R.plurals.todo_count, count, count)
```

> **번역 없이도 지금 해둘 것**: 문자열을 전부 `strings.xml`로 빼두기.
> 나중에 영어판을 만들 때 파일 하나만 복사해서 번역하면 끝납니다.
> Android Studio의 **Translations Editor**(strings.xml 우클릭 → Open Translations Editor)가
> 표 형태로 편집을 도와줍니다.

## 4-9. 성능 ⭐ (신규)

### 리컴포지션 — Compose 성능의 거의 전부

```kotlin
// ❌ 화면 전체가 매 프레임 리컴포지션
@Composable
fun Screen(viewModel: VM) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    Column {
        Header(state.title)
        HeavyList(state.items)
        Footer(state.count)     // count만 바뀌어도 위 전부가 다시 그려짐
    }
}

// ✅ 상태를 읽는 위치를 최대한 아래로 내리기 (deferred read)
@Composable
fun Footer(countProvider: () -> Int) {   // 람다로 넘기면 Footer만 리컴포지션
    Text("${countProvider()}")
}
```

**측정 방법:**
```
Android Studio → Layout Inspector → Recomposition Counts 켜기
→ 아무것도 안 했는데 숫자가 계속 올라가는 컴포저블이 범인
```

**규칙 3개만:**
1. `LazyColumn`의 `items()`에 **반드시 `key`를 주세요** (React의 key와 같은 이유)
2. 무거운 계산은 `remember(입력) { 계산() }` 으로 캐싱
3. 리스트를 `List<T>` 대신 `ImmutableList`(kotlinx-collections-immutable)로 넘기면
   Compose가 "안 바뀜"을 판단할 수 있어 리컴포지션이 줄어듭니다

### 앱 시작 속도

```kotlin
// baselineProfile — 앱 시작을 20~30% 빠르게. 출시 전 한 번 생성해두면 이득이 큽니다
// https://developer.android.com/topic/performance/baselineprofiles
```

### APK/AAB 크기 줄이기

```
1. isMinifyEnabled + isShrinkResources = true  (기본)
2. AAB로 업로드 → Play가 기기별로 필요한 리소스만 배포
3. Build → Analyze APK로 뭐가 큰지 확인 (대개 이미지)
4. PNG → WebP 변환 (Android Studio에서 우클릭 → Convert to WebP)
```

## 4-10. Play Store 출시 절차 ⭐ (신규)

코드가 끝나도 출시까지 할 일이 꽤 남습니다. **처음이면 1~2주 잡으세요.**

### 준비물 체크리스트

```
□ 앱 아이콘 (512×512 PNG, 투명 배경 불가)
□ 그래픽 이미지 (1024×500) — 스토어 상단 배너
□ 스크린샷 최소 2장 (폰), 태블릿 지원 시 별도
□ 앱 이름 (30자), 짧은 설명 (80자), 자세한 설명 (4000자)
□ 개인정보처리방침 URL  ← 필수. 없으면 심사 통과 못 합니다
□ 데이터 보안(Data Safety) 양식 — 수집하는 데이터 전부 신고
□ 콘텐츠 등급 설문
□ 타깃 연령층 / 광고 포함 여부 신고
```

> **개인정보처리방침**은 GitHub Pages나 Notion 공개 페이지로 무료 호스팅해도 됩니다.
> 결제 SDK와 서버가 처리하는 구매 내역·계정 식별자도 Data Safety 양식과 개인정보처리방침에
> 실제 동작 그대로 명시하세요. 신고 내용이 다르면 앱이 내려갑니다.

### 릴리즈 트랙 순서

```
내부 테스트 (Internal)      ← 최대 100명, 즉시 반영. 개발 중 여기서 확인
   ↓
비공개 테스트 (Closed)      ← 신규 개인 계정은 여기서 일정 기준 충족 필요할 수 있음
   ↓
공개 테스트 (Open)          ← 누구나 참여 가능한 베타
   ↓
프로덕션 (Production)       ← 정식 출시. 단계적 출시(rollout %)로 시작 권장
```

> **단계적 출시를 쓰세요.** 프로덕션에 올릴 때 20%부터 시작하면, 크래시율이 튀었을 때
> 나머지 80%를 막을 수 있습니다. Play Console의 Android Vitals에서 크래시/ANR을 확인하세요.

### 심사에서 자주 걸리는 것

| 사유 | 대응 |
|---|---|
| 개인정보처리방침 누락/불일치 | URL 접근 가능한지, 실제 수집 데이터와 일치하는지 확인 |
| Data Safety 양식 부정확 | SDK가 수집하는 것까지 포함해서 신고 |
| 권한 과다 요청 | 실제로 안 쓰는 권한은 Manifest에서 제거 |
| 계정 삭제 기능 없음 | 회원가입이 있는 앱은 **앱 내 계정 삭제 경로 + 웹 URL** 둘 다 필요 |
| 타깃 API 수준 미달 | targetSdk 상향 |
| 저작권 이미지/폰트 | 라이선스 확인된 것만 사용 |

## 4-11. 실전 코드 학습 — 오픈소스 샘플

| 샘플 | 레벨 | URL | 추천 이유 |
|---|---|---|---|
| **Now in Android** | 중급~고급 | [android/nowinandroid](https://github.com/android/nowinandroid) | Google 공식. 실전 아키텍처 끝판왕 — Compose + MVVM + Hilt + DataStore + 멀티모듈 + 테스트. Android DevRel팀이 직접 관리 |
| **Jetpack Compose Samples** | 초급~중급 | [android/compose-samples](https://github.com/android/compose-samples) | 공식 샘플 모음. Jetsurvey(폼), Jetcaster(플레이어), Jetchat(채팅), Crane(여행), Reply(메일) 등 |
| **Jetsurvey** | 초급 | compose-samples 내부 | 가장 가벼움. 온보딩/폼/상태관리/네비게이션 기본기만 |

**추천 순서**: Jetsurvey → Jetchat 또는 Crane → Now in Android

| 이 튜토리얼 | 대응하는 샘플 코드 |
|---|---|
| STEP 1 (UI 기초) | Jetsurvey `OnboardingScreen` |
| STEP 2 (리스트) | Jetcaster / Now in Android 피드 화면 |
| STEP 3 (ViewModel·네비) | Now in Android `feature/*` 모듈 |
| STEP 4 (저장) | Now in Android의 DataStore·Room 사용부 |
| 4-3 인앱 결제·구독 | Google Play Billing 공식 통합·테스트 문서 |
| 4-7 테스트 | Now in Android의 `*Test.kt` (테스트 작성법의 교과서) |

**학습 팁:**
1. **전부 읽지 마세요.** Now in Android만 200파일이 넘습니다. 관심 화면 1~2개만
2. **타이핑해서 옮겨보세요.** 읽기만 하는 것 대비 체감 학습량이 몇 배입니다
3. **PR 히스토리를 보세요.** "왜 이렇게 짰는가"가 PR 설명에 있습니다

## 4-12. Android 고유 기능 (네이티브를 쓰는 진짜 이유)

| 기능 | 언제 쓰나 | 학습 링크 |
|---|---|---|
| **App Widget (Glance)** | 홈 화면 위젯 — 매일 보는 데이터, 빠른 기록 | [Jetpack Glance](https://developer.android.com/jetpack/androidx/releases/glance) |
| **Material You Dynamic Color** | 배경화면 기반 자동 테마 (공짜 차별화) | [Dynamic Color](https://developer.android.com/develop/ui/views/theming/dynamic-colors) |
| **Quick Settings Tile** | 알림 패널에서 1탭 실행 | [TileService](https://developer.android.com/reference/android/service/quicksettings/TileService) |
| **Foreground Service** | 백그라운드 타이머·걸음수·음악 재생 | [포그라운드 서비스](https://developer.android.com/develop/background-work/services/foreground-services) |
| **WorkManager** | 조건부 백그라운드 작업 (충전 중 동기화 등) | [WorkManager](https://developer.android.com/topic/libraries/architecture/workmanager) |
| **Wear OS 컴패니언** | 건강/타이머 앱의 손목 버전 | [Wear OS](https://developer.android.com/training/wearables) |
| **Android Auto** | 자동차 연동 (좁지만 경쟁 적음) | [Android Auto](https://developer.android.com/cars) |

**ROI가 가장 큰 것: App Widget (Glance).**
Play Store에 "위젯 지원" 필터가 존재할 만큼 실제로 유저가 찾는 기능이고,
Glance는 Compose와 문법이 거의 같아서 학습 비용이 낮습니다.

**예시 — "할 일 앱"을 Android 고유 기능으로 차별화:**
```
├─ App Widget (Glance): 홈 화면에서 체크박스를 직접 탭해 완료 처리
├─ Quick Settings Tile: 알림 패널에서 1탭으로 "빠른 기록"
└─ Material You: 사용자 배경화면 색으로 앱 테마 자동 맞춤
```

> RN에서는 각각 네이티브 모듈을 직접 만들어야 하는 영역입니다.
> 네이티브는 **공식 템플릿과 문서가 있어서** 1~2일이면 붙습니다.

## 4-13. 흔한 지뢰 모음 ⭐ (신규)

JS 개발자가 Android에서 실제로 밟는 것들만 모았습니다.

| 증상 | 원인 | 해결 |
|---|---|---|
| 버튼 눌러도 값이 안 바뀜 | `remember` 누락 | `var x by remember { mutableStateOf() }` |
| 화면 회전하면 입력이 사라짐 | `remember` 사용 | `rememberSaveable` 또는 ViewModel |
| 리스트에 add 했는데 화면 그대로 | 불변 리스트를 직접 수정 | 새 리스트 할당 또는 `mutableStateListOf` |
| 키보드가 입력창을 가림 | imePadding 누락 | `Modifier.imePadding()` |
| 헤더가 상태바와 겹침 | edge-to-edge 미대응 | `Modifier.systemBarsPadding()` |
| 다크모드에서 글자가 안 보임 | 색상 하드코딩 | `MaterialTheme.colorScheme.*` |
| 릴리즈 빌드만 크래시 | R8 규칙 누락 | `proguard-rules.pro`에 keep 추가 |
| "앱이 응답하지 않습니다"(ANR) | 메인 스레드 블로킹 | `withContext(Dispatchers.IO)` |
| 뒤로가기가 앱을 종료시킴 | 네비게이션 백스택 설계 | `popBackStack` / `navigate(popUpTo)` 확인 |
| Gradle 빌드 실패 (버전 에러) | JDK/AGP/Kotlin/KSP 불일치 | 0-4 참고, 버전 짝 맞추기 |
| 이미지가 앱 재시작 후 안 보임 | URI 권한 만료 | 내부 저장소로 복사 |
| 에뮬레이터에선 되는데 실기기에서 안 됨 | 권한/네트워크 보안 설정 | Logcat 확인, `usesCleartextTraffic` 등 |

> **디버깅 순서 습관화**: ① Logcat에서 `package:mine level:error` 필터 →
> ② 스택트레이스에서 내 코드 첫 줄 찾기 → ③ 그 줄에 브레이크포인트 → ④ 그래도 모르면 AI에 전문 붙여넣기.

---

# PART 5: 학습 로드맵 & 리소스

## 어떤 루트로 갈 것인가

- **목표 A (Fast-track)**: AI가 쓴 코드를 **읽고 판단하고 디버깅**할 수 있는 수준. 리뷰/기획에 필요한 최소 지식
- **목표 B (Full)**: AI 없이도 직접 코딩하는 수준. 전통적 Android 개발자 수준

### 🚀 Fast-track (Claude 어시스트 환경 — 추천)

**목표**: Now in Android 같은 실전 코드를 술술 읽고, "이 ViewModel의 `_state`가 왜 private이야?"
같은 구체적 질문을 할 수 있는 수준

| 단계 | 내용 | 예상 시간 |
|---|---|---|
| 1 | PART 0 — 환경 세팅 + **0-4 Gradle/SDK 개념** (여기가 제일 중요) | 2~3시간 |
| 2 | PART 1 — 문법 훑어 읽기 (**1-7 sealed class, 1-9 코루틴, 1-10 스코프 함수**는 집중) | 1~2시간 |
| 3 | PART 2 — 치트시트 북마크 | 10분 |
| 4 | PART 3 STEP 1 + **STEP 1.5 상태 관리** 직접 해보기 | 2~3시간 |
| 5 | PART 4 읽기 (4-1 디버깅, 4-6 에러, 4-13 지뢰 우선) | 1~2시간 |
| 6 | Jetsurvey 코드 30분 둘러보기 | 30분~1시간 |

**총 6~9시간** (주말 하루 + 평일 저녁 1~2일)

**이 루트의 근거**: AI가 STEP 2~4 수준 코드는 직접 써주므로 똑같이 타이핑할 이유가 없습니다.
대신 **"이 구조가 맞는지 판단하는 기준"** 과 **"에러를 읽는 능력"** 이 시간 대비 효율이 압도적입니다.
STEP 1.5(상태 관리)만 예외로 직접 해보길 권하는 이유는, 여기서 나는 버그는
AI도 화면을 못 보기 때문에 **사용자가 증상을 정확히 설명해야** 고칠 수 있어서입니다.

**한계**: 코루틴 내부 동작(CoroutineContext, Flow 연산자 조합) 같은 깊은 주제엔 약합니다.
필요해질 때 그때 파세요.

### 🎓 Full (전통 Android 개발자 루트)

| 주차 | 내용 | 산출물 |
|---|---|---|
| 0주차 | PART 0~1 (직접 타이핑) | 에뮬레이터 실행, 문법 연습 |
| 1주차 | STEP 1 + 1.5 — Compose 기초와 상태 | 카운터 앱 |
| 2주차 | STEP 2 — 리스트·입력 | 할 일 앱 |
| 3주차 | STEP 3 — API·ViewModel·네비게이션 | 날씨 앱 |
| 4주차 | STEP 4 — Room·DataStore·권한 | 메모 앱 |
| 5주차 | PART 4 (테스트·접근성·성능) + 샘플 코드 분석 | 테스트 붙은 앱 |
| 6주차 | 고유 기능 1개 (Widget 추천) + 릴리즈 빌드 | 위젯 붙은 앱 |
| 7주차~ | 본인 아이디어 앱 + 출시 | 첫 출시 앱 |

**총 30~45시간** (6~8주, 주당 5~7시간)

> 원래 이 로드맵은 Android+iOS 합본 기준 50~80시간이었습니다.
> 한 플랫폼만 하면 절반 정도로 줄고, 나중에 다른 플랫폼을 추가하면 개념이 이미 있어서
> 훨씬 빠릅니다 (두 번째 트랙은 보통 15~20시간).

## JS 개발자가 특히 주의할 점 (Kotlin)

- `val` = `const`, `var` = `let` — JS와 감각이 같습니다 (Swift와 달리 헷갈리지 않음)
- 세미콜론 불필요
- `==` 가 JS의 `===`처럼 동작 (값 비교). Kotlin의 `===`는 **참조 비교** (JS엔 없는 개념)
- null 처리가 엄격: `String?`과 `String`은 **다른 타입**
- 타입 변환이 자동으로 안 됨: `i.toDouble()`, `s.toIntOrNull()`
- 컬렉션 기본은 불변: `listOf()` vs `mutableListOf()`
- 삼항 연산자 없음 → `if (a) b else c`
- `Icons.Default.ArrowBack` 등 일부는 deprecated → `Icons.AutoMirrored.Filled.*`
- 문자열 안 변수: `"$name"`, 표현식은 `"${user.name}"`
- **메인 스레드에서 IO 하면 앱이 죽습니다** (JS엔 없는 제약)

## 부록: iOS 트랙과의 대조표

iOS도 할 계획이면 [iOS 트랙 문서](./ios-swift-swiftui.md)를 보세요. 개념 대응은 이렇습니다.

| 개념 | Android (이 문서) | iOS |
|---|---|---|
| UI 프레임워크 | Jetpack Compose | SwiftUI |
| 언어 | Kotlin | Swift |
| 상수/변수 | `val` / `var` | `let` / `var` (⚠️ let이 상수) |
| 상태 | `remember { mutableStateOf() }` | `@State` |
| 저장되는 상태 | `rememberSaveable` | `@SceneStorage` / `@AppStorage` |
| 부수 효과 | `LaunchedEffect` | `.task` / `.onAppear` |
| 세로 배치 | `Column` | `VStack` |
| 가로 배치 | `Row` | `HStack` |
| 겹치기 | `Box` | `ZStack` |
| 리스트 | `LazyColumn` | `List` / `LazyVStack` |
| 화면 상태 관리 | ViewModel + StateFlow | `@Observable` 클래스 |
| 네비게이션 | Navigation Compose | `NavigationStack` |
| 비동기 | `suspend` + 코루틴 | `async` / `await` |
| 네트워크 | Retrofit | URLSession |
| 로컬 DB | Room | SwiftData |
| 설정 저장 | DataStore | UserDefaults / `@AppStorage` |
| 의존성 | Gradle | Swift Package Manager |
| 미리보기 | `@Preview` | `#Preview` |
| 안전 영역 | `systemBarsPadding()` (기본이 전체 화면) | 기본이 안전 영역 (`.ignoresSafeArea()`로 해제) |

> **가장 큰 사고방식 차이**: Android는 "화면 전체를 그린 뒤 시스템 영역을 피한다",
> iOS는 "안전 영역만 그리다가 필요하면 넓힌다". 기본값이 정반대라 처음에 헷갈립니다.

## 유용한 링크

**공식**
- Compose 튜토리얼: https://developer.android.com/jetpack/compose/tutorial
- Compose 성능 가이드: https://developer.android.com/develop/ui/compose/performance
- 아키텍처 가이드: https://developer.android.com/topic/architecture
- Material Design 3: https://m3.material.io

**문법 연습**
- Kotlin Playground: https://play.kotlinlang.org
- Kotlin Koans: https://play.kotlinlang.org/koans

**API/도구**
- OpenWeatherMap (무료): https://openweathermap.org/api
- Maven 저장소(버전 확인): https://maven.google.com

---

> **막히면**: JS 코드를 보여주면서 "이걸 Kotlin/Compose로 어떻게 쓰나요?"라고 물어보세요.
> 이미 아는 개념에 이름표를 붙이는 방식이 가장 빠릅니다.
