# 모바일 앱 개발 튜토리얼 (완전판)
## JavaScript 풀스택 개발자를 위한 Android & iOS 입문

> **학습 전략**: 각 플랫폼별로 동일한 앱을 만들면서 비교 학습합니다.
> 환경 세팅 → 문법 기초 → 샘플 앱 4개를 단계별로 완성합니다.
>
> ⚡ **Claude 어시스트 환경이면 Fast-track 루트(8~13시간)부터 보세요** — Part 5 상단에 있습니다. 전체 루트(50~80시간)는 Claude 없이 직접 개발할 사람용입니다.

---

# PART 0: 개발 환경 세팅

## 0-1. Android 개발 환경

### Android Studio 설치

1. https://developer.android.com/studio 접속
2. OS에 맞는 버전 다운로드 (Windows / macOS / Linux)
3. 설치 시 "Standard" 설정 선택 (커스텀 불필요)
4. 설치 완료 후 첫 실행 시 SDK 자동 다운로드 (약 2~5GB, 시간 걸림)

### 설치 확인 체크리스트

```
✅ Android Studio 실행 됨
✅ "New Project" 버튼이 보임
✅ SDK Manager에서 최신 Android SDK 설치 확인
   → Settings > Languages & Frameworks > Android SDK
   → "Android 14 (API 34)" 이상 체크
✅ "SDK Tools" 탭에서 아래 항목 체크 확인
   → Android SDK Build-Tools
   → Android Emulator
   → Android SDK Platform-Tools
```

### 에뮬레이터 (가상 기기) 설정

에뮬레이터 = 내 컴퓨터에서 돌리는 가상 안드로이드 폰입니다.

**생성 방법:**

1. Android Studio 상단 메뉴 → Tools → Device Manager
2. "Create Device" 클릭
3. 기기 선택: **Pixel 7** 추천 (표준 사이즈)
4. 시스템 이미지 선택: **API 34** (옆에 Download 버튼 누르면 다운로드)
5. "Finish" 클릭

**실행 방법:**

1. Device Manager에서 만든 기기 옆의 ▶ (재생) 버튼 클릭
2. 에뮬레이터 창이 뜨면 성공!
3. 첫 실행 시 부팅에 1~2분 걸림

**에뮬레이터가 느릴 때:**

```
Windows: BIOS에서 Intel VT-x 또는 AMD-V 가상화 활성화
macOS (Intel): HAXM 자동 설치됨
macOS (M1/M2/M3): ARM 에뮬레이터 자동 사용 (빠름)

그래도 느리면:
→ Settings > Languages & Frameworks > Android SDK > SDK Tools
→ "Android Emulator" 최신 버전으로 업데이트
→ 에뮬레이터 설정에서 RAM을 4GB로 올리기
```

**실제 기기로 테스트 (선택사항):**

```
Android 폰:
1. 설정 → 휴대전화 정보 → 빌드 번호 7번 탭 (개발자 모드 활성화)
2. 설정 → 개발자 옵션 → USB 디버깅 켜기
3. USB 케이블로 컴퓨터 연결
4. Android Studio에서 기기 목록에 내 폰이 뜨면 성공
```

### 첫 프로젝트 생성 & 실행 테스트

```
1. Android Studio → "New Project"
2. "Empty Activity" 선택 (Compose 버전)
3. 설정:
   - Name: HelloWorld
   - Package name: com.yourname.helloworld
   - Language: Kotlin
   - Minimum SDK: API 26
4. "Finish" 클릭 → 프로젝트 생성 (Gradle 동기화에 1~3분)
5. 상단 ▶ 버튼 클릭 → 에뮬레이터에 "Hello Android!" 뜨면 성공!
```

> **Gradle 동기화 실패 시:**
> File → Sync Project with Gradle Files 클릭,
> 그래도 안 되면 File → Invalidate Caches → Restart

---

## 0-2. iOS 개발 환경

### 필수 요구사항

```
⚠️ iOS 개발은 macOS가 필수입니다!
Windows/Linux에서는 Xcode 설치가 불가합니다.

Mac이 없는 경우 선택지:
1. 중고 MacBook Air (M1 이상 추천) 구매
2. 클라우드 Mac 서비스 (MacStadium, AWS EC2 Mac 등)
3. Android 먼저 개발하고 나중에 iOS 진행
```

### Xcode 설치

1. Mac App Store에서 "Xcode" 검색
2. 설치 (약 12~15GB, 시간 꽤 걸림)
3. 설치 후 첫 실행 → "Install Additional Components" 동의
4. Command Line Tools 설치 확인:

```bash
# 터미널에서 실행
xcodebuild -version
# Xcode 버전이 출력되면 성공
# (xcode-select -p 는 설치 경로를 출력)
```

### 설치 확인 체크리스트

```
✅ Xcode 실행 됨
✅ "Create New Project" 버튼이 보임
✅ Xcode → Settings → Platforms
   → iOS 17 이상 시뮬레이터 다운로드 확인
```

### 시뮬레이터 (가상 기기) 설정

Xcode는 시뮬레이터가 기본 내장되어 있어서 별도 설치가 거의 필요 없습니다.

**시뮬레이터 실행 방법:**

1. Xcode 상단에서 기기 선택 드롭다운 클릭
2. "iPhone 15" 또는 "iPhone 15 Pro" 선택
3. ▶ (재생) 버튼 클릭
4. iPhone 시뮬레이터 창이 뜨면 성공!

**시뮬레이터 유용한 단축키:**

```
Cmd + Shift + H     : 홈 버튼 (홈 화면으로)
Cmd + 오른쪽 화살표  : 기기 회전
Cmd + S              : 스크린샷
Cmd + K              : 키보드 토글
Cmd + Shift + A      : 다크모드 / 라이트모드 전환
```

**시뮬레이터가 안 뜰 때:**

```
Xcode → Settings → Platforms
→ iOS 시뮬레이터 런타임이 설치되어 있는지 확인
→ 없으면 "+" 버튼 눌러서 다운로드

그래도 안 되면:
→ 터미널에서: xcrun simctl list devices
→ 사용 가능한 시뮬레이터 목록이 나오면 정상
```

**실제 기기로 테스트 (선택사항):**

```
iPhone:
1. USB-C 또는 Lightning 케이블로 Mac에 연결
2. iPhone에서 "이 컴퓨터를 신뢰하시겠습니까?" → 신뢰
3. Xcode 상단 기기 목록에서 내 iPhone 선택
4. ▶ 클릭

⚠️ 첫 실제 기기 테스트 시:
→ Xcode → Settings → Accounts → Apple ID 로그인 필요
→ 무료 Apple ID로도 개인 기기 테스트 가능 (7일 제한)
→ 앱스토어 출시는 Apple Developer Program 연 $99 필요
```

### 첫 프로젝트 생성 & 실행 테스트

```
1. Xcode → "Create New Project"
2. iOS → "App" 선택
3. 설정:
   - Product Name: HelloWorld
   - Organization Identifier: com.yourname
   - Interface: SwiftUI
   - Language: Swift
   - Storage: None
4. 저장 위치 선택 → "Create"
5. 상단 ▶ 버튼 클릭 → 시뮬레이터에 "Hello, world!" 뜨면 성공!
```

---

## 0-3. 공통 도구 설치 (선택사항이지만 강력 추천)

### Claude Code 설치 (사실상 필수)

Claude Code는 터미널에서 AI와 함께 코딩하는 도구입니다.
프로젝트 폴더에서 바로 코드 생성/수정/디버깅이 가능해서 생산성이 크게 올라갑니다.

> **Native 개발에서 Claude Code의 가치**:
> Kotlin/Swift는 JS보다 컴파일 에러가 더 자주 발생합니다.
> 에러 메시지를 그대로 Claude에 붙여넣으면 즉시 원인 + 수정안을 받을 수 있어
> 학습 속도가 3~5배 빨라집니다. "선택"이 아니라 거의 필수에 가까운 도구입니다.

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | sh

# 설치 확인
claude --version

# 프로젝트 폴더에서 실행
cd ~/AndroidStudioProjects/HelloWorld
claude
# → /login 입력하여 로그인
```

**효과적인 활용 패턴:**
- 에러 메시지 → "이거 무슨 에러야?" → 원인 + 수정 받기
- "이 JS 코드를 Kotlin/Swift로 바꿔줘" → 변환된 코드 받기
- "이 코드 리뷰해줘" → 개선점 받기

> Claude Code는 Pro 이상 구독이 필요합니다 ($20/월 또는 Max $100/월).

### Git 설치 확인

```bash
git --version
# 버전이 나오면 OK
# 없으면: https://git-scm.com 에서 설치
```

---

## 0-4. 앱스토어 계정 등록 (나중에 해도 됨)

출시 직전에 해도 되지만, 심사에 며칠 걸리니 여유 있을 때 미리 해두면 편합니다.

### Google Play 개발자 계정

```
비용: $25 (일회성, 평생 유효)
등록: https://play.google.com/console

준비물:
- Google 계정
- 신용카드 / 체크카드
- 본인 확인용 신분증

등록 후 심사: 보통 1~3일
```

### Apple Developer Program

```
비용: $99/년 (매년 갱신)
등록: https://developer.apple.com/programs/enroll

준비물:
- Apple ID
- 본인 확인 (Two-Factor Authentication 필수)
- 신용카드 / 체크카드

등록 후 심사: 보통 1~2일
(무료 Apple ID로도 개인 기기 테스트는 가능)
```

---

# PART 1: 문법 기초 맛보기

튜토리얼에 들어가기 전에, Kotlin과 Swift의 기본 문법을 JS와 비교하면서
30분~1시간 정도 훑어보세요. 완벽히 외울 필요 없고 "아 이런 느낌이구나" 정도면 됩니다.

## 1-1. 변수와 상수

```javascript
// JavaScript
const name = "홍길동"       // 재할당 불가
let age = 25               // 재할당 가능
var score = 100            // 요즘 잘 안 씀
```

```kotlin
// Kotlin
val name = "홍길동"         // const와 같음 (재할당 불가)
var age = 25               // let과 같음 (재할당 가능)
// var 밖에 없음. JS의 var과는 다름!
```

```swift
// Swift ⚠️ 주의: JS와 키워드가 반대!
let name = "홍길동"         // ⚠️ JS의 const 역할! (재할당 불가)
var age = 25               // JS의 let 역할 (재할당 가능)
```

> **⚠️ Swift의 let = JS의 const** 입니다!
> JS에서 let은 변수인데 Swift에서 let은 상수이니 주의하세요.

## 1-2. 타입 시스템 (JS와 가장 큰 차이!)

```javascript
// JavaScript - 타입 자유, 런타임에 에러 발견
let x = "hello"
x = 123            // OK! 문자열이었다가 숫자로 변경 가능
x = true           // OK! 뭐든 넣을 수 있음

function add(a, b) {
    return a + b   // a, b가 숫자인지 문자인지 모름
}
add("1", 2)        // "12" - 의도치 않은 결과
```

```kotlin
// Kotlin - 타입 추론 + 컴파일 시점 체크
var x = "hello"    // String으로 자동 추론
// x = 123         // ❌ 컴파일 에러! String 변수에 Int 못 넣음

fun add(a: Int, b: Int): Int {   // 매개변수 타입 필수
    return a + b
}
// add("1", 2)     // ❌ 컴파일 에러! 실행 전에 잡아줌
```

```swift
// Swift - Kotlin과 동일한 방식
var x = "hello"    // String으로 자동 추론
// x = 123         // ❌ 컴파일 에러!

func add(a: Int, b: Int) -> Int {
    return a + b
}
```

> **핵심**: 처음엔 타입 쓰는 게 귀찮지만,
> "undefined is not a function" 같은 런타임 에러가 사라집니다.
> 매개변수에만 타입 쓰면 나머지는 대부분 자동 추론됩니다.

## 1-3. 함수

```javascript
// JavaScript
function greet(name) {
    return "안녕, " + name
}

// 화살표 함수
const double = (x) => x * 2

// 기본값
function hello(name = "세계") {
    return "안녕, " + name
}
```

```kotlin
// Kotlin
fun greet(name: String): String {
    return "안녕, $name"      // 문자열 템플릿: ${} 대신 $ 만으로도 됨
}

// 한 줄이면 중괄호 생략 가능
fun double(x: Int) = x * 2

// 기본값
fun hello(name: String = "세계"): String {
    return "안녕, $name"
}
```

```swift
// Swift
func greet(name: String) -> String {
    return "안녕, \(name)"    // 문자열 보간: \() 사용
}

// 한 줄이면 return 생략 가능
func double(x: Int) -> Int { x * 2 }

// 기본값
func hello(name: String = "세계") -> String {
    return "안녕, \(name)"
}
```

## 1-4. 조건문

```javascript
// JavaScript
if (score >= 90) {
    console.log("A")
} else if (score >= 80) {
    console.log("B")
} else {
    console.log("C")
}

// 삼항 연산자
const grade = score >= 90 ? "A" : "B"
```

```kotlin
// Kotlin - 거의 동일!
if (score >= 90) {
    println("A")
} else if (score >= 80) {
    println("B")
} else {
    println("C")
}

// if를 표현식(expression)으로 사용 가능 (삼항 연산자 대체)
val grade = if (score >= 90) "A" else "B"

// when = JS의 switch 업그레이드 버전
val message = when {
    score >= 90 -> "훌륭합니다"
    score >= 80 -> "좋습니다"
    else -> "노력하세요"
}
```

```swift
// Swift - 거의 동일!
if score >= 90 {           // ⚠️ 괄호 () 생략 가능 (쓰면 경고)
    print("A")
} else if score >= 80 {
    print("B")
} else {
    print("C")
}

// 삼항 연산자 동일
let grade = score >= 90 ? "A" : "B"

// switch = JS의 switch 업그레이드 (break 자동, 패턴 매칭)
switch score {
case 90...100: print("A")     // 범위 매칭 가능!
case 80..<90:  print("B")
default:       print("C")
}
```

## 1-5. 반복문

```javascript
// JavaScript
// for 루프
for (let i = 0; i < 5; i++) {
    console.log(i)
}

// for...of
const fruits = ["사과", "바나나", "딸기"]
for (const fruit of fruits) {
    console.log(fruit)
}

// forEach
fruits.forEach((fruit, index) => {
    console.log(`${index}: ${fruit}`)
})
```

```kotlin
// Kotlin
// 범위 반복
for (i in 0 until 5) {       // 0, 1, 2, 3, 4  (until = 미만)
    println(i)
}
for (i in 0..4) {             // 0, 1, 2, 3, 4  (.. = 이하)
    println(i)
}

// 리스트 반복
val fruits = listOf("사과", "바나나", "딸기")
for (fruit in fruits) {
    println(fruit)
}

// 인덱스 포함
fruits.forEachIndexed { index, fruit ->
    println("$index: $fruit")
}
```

```swift
// Swift
// 범위 반복
for i in 0..<5 {              // 0, 1, 2, 3, 4  (..<  = 미만)
    print(i)
}
for i in 0...4 {              // 0, 1, 2, 3, 4  (... = 이하)
    print(i)
}

// 배열 반복
let fruits = ["사과", "바나나", "딸기"]
for fruit in fruits {
    print(fruit)
}

// 인덱스 포함
for (index, fruit) in fruits.enumerated() {
    print("\(index): \(fruit)")
}
```

## 1-6. 배열/리스트 조작

```javascript
// JavaScript
const nums = [1, 2, 3, 4, 5]

nums.map(x => x * 2)           // [2, 4, 6, 8, 10]
nums.filter(x => x > 3)        // [4, 5]
nums.find(x => x > 3)          // 4
nums.reduce((sum, x) => sum + x, 0)  // 15
nums.includes(3)                // true
nums.length                     // 5

// 추가/삭제 (원본 변경)
const arr = [1, 2, 3]
arr.push(4)                     // [1, 2, 3, 4]
arr.splice(1, 1)                // [1, 3, 4]  (index 1 삭제)

// 스프레드
const combined = [...arr1, ...arr2]
```

```kotlin
// Kotlin
val nums = listOf(1, 2, 3, 4, 5)       // 불변 리스트

nums.map { it * 2 }                     // [2, 4, 6, 8, 10]
nums.filter { it > 3 }                  // [4, 5]
nums.find { it > 3 }                    // 4  (또는 firstOrNull)
nums.reduce { sum, x -> sum + x }      // 15  (또는 .sum())
nums.contains(3)                        // true  (또는 3 in nums)
nums.size                               // 5  (.length 아님!)

// 가변 리스트 (변경 가능)
val arr = mutableListOf(1, 2, 3)
arr.add(4)                              // [1, 2, 3, 4]
arr.removeAt(1)                         // [1, 3, 4]

// 합치기
val combined = arr1 + arr2
```

```swift
// Swift
let nums = [1, 2, 3, 4, 5]

nums.map { $0 * 2 }                    // [2, 4, 6, 8, 10]
nums.filter { $0 > 3 }                 // [4, 5]
nums.first { $0 > 3 }                  // 4 (Optional)
nums.reduce(0) { sum, x in sum + x }   // 15
nums.contains(3)                        // true
nums.count                              // 5  (.length 아님!)

// 가변 배열
var arr = [1, 2, 3]
arr.append(4)                           // [1, 2, 3, 4]
arr.remove(at: 1)                       // [1, 3, 4]

// 합치기
let combined = arr1 + arr2
```

> **it vs $0**: Kotlin은 람다의 단일 매개변수를 `it`으로,
> Swift는 `$0`으로 줄여 쓸 수 있습니다.

## 1-7. 객체와 클래스

```javascript
// JavaScript - 객체 리터럴
const user = { name: "홍길동", age: 25 }
console.log(user.name)

// 클래스
class User {
    constructor(name, age) {
        this.name = name
        this.age = age
    }

    greet() {
        return `안녕, ${this.name}`
    }
}

const u = new User("홍길동", 25)
```

```kotlin
// Kotlin - data class (JS 객체와 가장 비슷)
data class User(val name: String, val age: Int)
// 이 한 줄이면 생성자, toString, equals, copy 전부 자동 생성!

val user = User("홍길동", 25)    // new 키워드 없음!
println(user.name)

// 메서드 추가하려면
data class User(val name: String, val age: Int) {
    fun greet() = "안녕, $name"    // this.name 대신 name만으로 됨
}

// 복사하면서 일부만 변경 (스프레드와 비슷)
// JS: const u2 = { ...user, age: 26 }
val u2 = user.copy(age = 26)
```

```swift
// Swift - struct (JS 객체와 가장 비슷)
struct User {
    let name: String
    let age: Int

    func greet() -> String {
        return "안녕, \(name)"
    }
}

let user = User(name: "홍길동", age: 25)
print(user.name)

// struct는 값 타입이라 변경하려면 var로 선언
var user2 = user
// user2.age = 26  // age가 let이면 불가, var이면 가능
```

## 1-8. null / nil 처리

```javascript
// JavaScript - null은 자유롭게 사용 (런타임 에러 가능)
let name = null
console.log(name.length)     // ❌ TypeError: Cannot read properties of null

// 안전하게 접근
console.log(name?.length)    // undefined
console.log(name ?? "이름 없음")  // "이름 없음"
```

```kotlin
// Kotlin - null 가능 여부를 타입으로 구분
var name: String = "홍길동"
// name = null               // ❌ 컴파일 에러! 일반 타입에 null 불가

var name2: String? = "홍길동"  // ? 붙이면 null 가능
name2 = null                  // ✅ OK

// println(name2.length)      // ❌ 컴파일 에러! null일 수 있으니까
println(name2?.length)         // ✅ null이면 null 반환 (JS와 동일)
println(name2 ?: "이름 없음")  // ✅ null이면 기본값 (JS의 ?? 와 동일)

// null 아닌 게 확실할 때
println(name2!!.length)        // !! = "나는 null 아닌 거 안다" (위험!)
```

```swift
// Swift - Optional로 null 관리 (null 대신 nil 사용)
var name: String = "홍길동"
// name = nil                // ❌ 컴파일 에러!

var name2: String? = "홍길동"  // ? 붙이면 nil 가능 (Optional)
name2 = nil                   // ✅ OK

print(name2?.count)            // ✅ nil이면 nil 반환
print(name2 ?? "이름 없음")    // ✅ nil이면 기본값

// 안전하게 꺼내기 (JS에 없는 패턴)
if let unwrapped = name2 {
    print(unwrapped.count)     // nil이 아닐 때만 실행
}

// guard let (함수 초반에 nil 체크하고 빠져나오기)
func process(name: String?) {
    guard let name = name else { return }  // nil이면 여기서 종료
    print(name.count)  // 이 아래로는 name이 확실히 값 있음
}
```

> **Kotlin의 `?`와 Swift의 `?`는 거의 같은 개념입니다.**
> JS와 달리 null 가능 여부를 컴파일러가 잡아주니
> "Cannot read properties of null" 에러가 사라집니다!

## 1-9. 비동기 처리

```javascript
// JavaScript
async function fetchData() {
    try {
        const res = await fetch("https://api.example.com/data")
        const data = await res.json()
        console.log(data)
    } catch (error) {
        console.log("에러:", error.message)
    }
}

// Promise 체이닝
fetch(url)
    .then(res => res.json())
    .then(data => console.log(data))
    .catch(err => console.log(err))
```

```kotlin
// Kotlin - 코루틴 (async/await과 비슷하지만 약간 다름)
// suspend = async 키워드와 비슷
suspend fun fetchData() {
    try {
        val data = RetrofitClient.api.getData()  // 자동으로 await처럼 동작
        println(data)
    } catch (e: Exception) {
        println("에러: ${e.message}")
    }
}

// 코루틴 시작하기 (async 함수 호출하는 방법)
// JS: fetchData()  처럼 그냥 호출하면 안 되고
// Compose에서는:
LaunchedEffect(Unit) {     // useEffect와 비슷
    fetchData()
}
// ViewModel에서는:
viewModelScope.launch {    // 코루틴 스코프 안에서 호출
    fetchData()
}
```

```swift
// Swift - async/await (JS와 거의 동일!)
func fetchData() async {
    do {                   // try-catch 대신 do-catch
        let (data, _) = try await URLSession.shared.data(from: url)
        let result = try JSONDecoder().decode(MyData.self, from: data)
        print(result)
    } catch {
        print("에러: \(error)")
    }
}

// async 함수 호출하기
// SwiftUI에서는:
.task {                    // useEffect와 비슷
    await fetchData()
}
// 일반 코드에서는:
Task {
    await fetchData()
}
```

> **정리**: Swift의 async/await은 JS와 거의 똑같습니다.
> Kotlin의 코루틴은 `suspend` 키워드를 쓰고 `launch {}` 안에서 호출하는 것만 기억하면 됩니다.

## 1-10. 문법 연습 링크

직접 코드를 쳐보면서 익히세요! 각각 10~20분이면 됩니다.

```
Kotlin 연습:
→ https://play.kotlinlang.org
→ 브라우저에서 바로 Kotlin 코드 실행 가능
→ 위의 예제들을 직접 쳐보세요

Swift 연습:
→ Mac: Swift Playground 앱 (App Store에서 무료 다운)
→ 또는 https://swiftfiddle.com (브라우저)
→ iPad에서도 Swift Playground 앱 사용 가능
```

---

# PART 2: 언어/프레임워크 매핑 치트시트

앱 만들면서 계속 참고할 페이지입니다. 외울 필요 없이 필요할 때 찾아보세요.

## 언어 비교 요약

| 개념 | JavaScript | Kotlin | Swift |
|------|-----------|--------|-------|
| 상수 | `const x = 1` | `val x = 1` | `let x = 1` |
| 변수 | `let x = 1` | `var x = 1` | `var x = 1` |
| 함수 | `function add(a, b)` | `fun add(a: Int, b: Int): Int` | `func add(a: Int, b: Int) -> Int` |
| 화살표 함수 | `(x) => x * 2` | `{ x -> x * 2 }` | `{ x in x * 2 }` |
| null 체크 | `x?.prop` | `x?.prop` | `x?.prop` |
| 기본값 | `x ?? "기본"` | `x ?: "기본"` | `x ?? "기본"` |
| 비동기 | `async/await` | `suspend` + 코루틴 | `async/await` |
| 문자열 조합 | `` `Hello ${name}` `` | `"Hello $name"` | `"Hello \(name)"` |
| 배열 길이 | `arr.length` | `list.size` | `arr.count` |
| 배열 추가 | `arr.push(x)` | `list.add(x)` | `arr.append(x)` |
| 출력 | `console.log()` | `println()` | `print()` |

## 프레임워크 매핑

| JS 생태계 | Android | iOS |
|-----------|---------|-----|
| React 컴포넌트 | `@Composable` 함수 | `View` struct |
| `useState()` | `remember { mutableStateOf() }` | `@State` |
| `useEffect()` | `LaunchedEffect` | `.task` / `.onAppear` |
| props | 함수 매개변수 | View 매개변수 |
| React Context | CompositionLocal | `@Environment` |
| React Router | Navigation Component | NavigationStack |
| npm / yarn | Gradle | Swift Package Manager |
| fetch / axios | Retrofit | URLSession |
| Redux / Zustand | ViewModel + StateFlow | ObservableObject |
| localStorage | SharedPreferences | UserDefaults |
| `<div style="flex-direction: column">` | `Column` | `VStack` |
| `<div style="flex-direction: row">` | `Row` | `HStack` |
| `arr.map(x => <Item />)` | `LazyColumn { items() }` | `List { ForEach() }` |
| `padding-top: env(safe-area-inset-top)` | `Modifier.systemBarsPadding()` | (자동) `.ignoresSafeArea()`로 끔 |
| 실시간 미리보기 | `@Preview` | `#Preview` |
| `console.log` | `Log.d("Tag", msg)` | `Logger().debug(msg)` |
| 권한 manifest | `AndroidManifest.xml` | `Info.plist` |

---

# PART 3: 샘플 앱 만들기

## STEP 1: Hello World - 프로젝트 구조 이해하기
**목표**: 텍스트와 버튼이 있는 첫 화면, 카운터 만들기

### Android (Kotlin + Jetpack Compose)

#### 프로젝트 구조 (JS 프로젝트와 비교)

```
// JS 프로젝트                   →  Android 프로젝트
package.json                    →  build.gradle.kts (의존성 관리)
node_modules/                   →  .gradle/ (자동 다운로드)
src/                            →  app/src/main/
  App.js                        →  MainActivity.kt (진입점)
  components/                   →  ui/screens/, ui/components/
  assets/                       →  res/ (리소스 폴더)
.env                            →  local.properties
```

#### 카운터 앱 코드

```kotlin
// MainActivity.kt

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // ⚠️ 최신 Android에선 enableEdgeToEdge()를 켜는 게 표준.
        // 이 경우 콘텐츠가 시스템 영역(상단 상태바, 하단 네비게이션바)까지 그려지므로
        // 루트 컴포저블에 systemBarsPadding()을 줘야 텍스트가 노치/시계와 안 겹침.
        enableEdgeToEdge()
        setContent {
            // ReactDOM.render(<App />) 과 같은 역할
            Surface(modifier = Modifier.fillMaxSize().systemBarsPadding()) {
                HelloScreen()
            }
        }
    }
}

// JS: function HelloScreen() { ... }
@Composable
fun HelloScreen() {
    // JS: const [count, setCount] = useState(0)
    var count by remember { mutableStateOf(0) }

    // JS: <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
    Column(
        modifier = Modifier
            .fillMaxSize()       // width: 100%, height: 100%
            .padding(16.dp),     // padding: 16
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // JS: <h1>안녕하세요!</h1>
        Text(
            text = "안녕하세요!",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(16.dp))  // margin-top: 16

        // JS: <p>카운트: {count}</p>
        Text(text = "카운트: $count")

        Spacer(modifier = Modifier.height(8.dp))

        // JS: <button onClick={() => setCount(count + 1)}>클릭!</button>
        Button(onClick = { count++ }) {
            Text("클릭!")
        }
    }
}

// 💡 @Preview = 빌드 안 해도 디자인을 실시간으로 미리보기
// Android Studio 우측 패널에 자동으로 렌더링됨. 학습 속도 최대치로 올려주는 핵심 기능.
@Preview(showBackground = true)
@Composable
fun HelloScreenPreview() {
    HelloScreen()
}
```

> **SafeArea / Edge-to-Edge 핵심 포인트**:
> Android 15+부터 모든 앱이 edge-to-edge로 강제됩니다. 즉 콘텐츠가 시계/배터리/네비게이션 영역까지 그려져요.
> 그래서 **루트에 `Modifier.systemBarsPadding()`** 을 안 주면 헤더 텍스트가 시스템 UI와 겹칩니다.
> (실전 앱에서 가장 자주 놓치는 이슈 중 하나. 반드시 에뮬레이터에서 시각적으로 확인하세요.)

---

### iOS (Swift + SwiftUI)

#### 프로젝트 구조

```
// JS 프로젝트                   →  iOS 프로젝트
package.json                    →  .xcodeproj (프로젝트 설정)
node_modules/                   →  .build/ (패키지 캐시)
src/                            →  프로젝트 폴더
  App.js                        →  앱이름App.swift (진입점)
  components/                   →  Views/
  assets/                       →  Assets.xcassets
```

#### 카운터 앱 코드

```swift
// ContentView.swift

import SwiftUI

// JS: function ContentView() { ... }
struct ContentView: View {
    // JS: const [count, setCount] = useState(0)
    @State private var count = 0

    // JS: return ( ... )
    var body: some View {
        VStack(spacing: 16) {
            Text("안녕하세요!")
                .font(.title)
                .fontWeight(.bold)

            Text("카운트: \(count)")

            Button("클릭!") {
                count += 1
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}

// 💡 #Preview = 빌드 안 해도 디자인을 실시간으로 미리보기
// Xcode 우측 캔버스에 자동 렌더링됨. SwiftUI 학습의 가장 큰 무기.
#Preview {
    ContentView()
}
```

> **SwiftUI의 SafeArea**:
> SwiftUI는 기본적으로 SafeArea 안쪽에만 그립니다 (Android와 반대).
> 노치/홈인디케이터 영역까지 침범하려면 `.ignoresSafeArea()`를 명시적으로 붙여야 합니다.
> 즉 iOS는 따로 신경 안 써도 안전한 게 기본값.

---

## STEP 2: 할 일 목록 앱 - 리스트, 입력, 상태 관리
**목표**: 리스트 렌더링, 사용자 입력, CRUD

### Android (Kotlin + Compose)

```kotlin
// TodoScreen.kt

// JS: { id: crypto.randomUUID(), title: "할 일", isDone: false }
data class Todo(
    val id: String = UUID.randomUUID().toString(),
    val title: String,
    val isDone: Boolean = false
)

@Composable
fun TodoScreen() {
    // JS: const [todos, setTodos] = useState([])
    var todos by remember { mutableStateOf(listOf<Todo>()) }
    var inputText by remember { mutableStateOf("") }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        // 입력 영역
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // JS: <input value={inputText} onChange={e => setInputText(e.target.value)} />
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                modifier = Modifier.weight(1f),  // flex: 1
                placeholder = { Text("할 일 입력...") }
            )

            Spacer(modifier = Modifier.width(8.dp))

            Button(onClick = {
                if (inputText.isNotBlank()) {
                    // JS: setTodos([...todos, { id: ..., title: inputText }])
                    todos = todos + Todo(title = inputText)
                    inputText = ""
                }
            }) {
                Text("추가")
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // JS: {todos.map(todo => <TodoItem key={todo.id} todo={todo} ... />)}
        LazyColumn {
            items(todos, key = { it.id }) { todo ->
                TodoItem(
                    todo = todo,
                    onToggle = {
                        // JS: setTodos(todos.map(t =>
                        //       t.id === todo.id ? {...t, isDone: !t.isDone} : t
                        //     ))
                        todos = todos.map {
                            if (it.id == todo.id) it.copy(isDone = !it.isDone) else it
                        }
                    },
                    onDelete = {
                        // JS: setTodos(todos.filter(t => t.id !== todo.id))
                        todos = todos.filter { it.id != todo.id }
                    }
                )
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
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Checkbox(checked = todo.isDone, onCheckedChange = { onToggle() })

        Text(
            text = todo.title,
            modifier = Modifier.weight(1f),
            // JS: style={{ textDecoration: isDone ? 'line-through' : 'none' }}
            textDecoration = if (todo.isDone) TextDecoration.LineThrough else null,
            color = if (todo.isDone) Color.Gray else Color.Unspecified
        )

        IconButton(onClick = onDelete) {
            Icon(Icons.Default.Delete, contentDescription = "삭제")
        }
    }
}
```

### iOS (Swift + SwiftUI)

```swift
// TodoView.swift

// JS: { id: crypto.randomUUID(), title: "할 일", isDone: false }
struct Todo: Identifiable {  // Identifiable = key prop 자동 제공
    let id = UUID()
    var title: String
    var isDone: Bool = false
}

struct TodoView: View {
    @State private var todos: [Todo] = []
    @State private var inputText = ""

    var body: some View {
        NavigationStack {
            VStack {
                HStack {
                    TextField("할 일 입력...", text: $inputText)
                        .textFieldStyle(.roundedBorder)

                    Button("추가") {
                        guard !inputText.isEmpty else { return }  // if (!inputText) return
                        todos.append(Todo(title: inputText))       // todos.push(newTodo)
                        inputText = ""
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()

                // JS: {todos.map(todo => <li>...</li>)}
                List {
                    ForEach($todos) { $todo in
                        HStack {
                            // $todo.isDone = 양방향 바인딩
                            Toggle("", isOn: $todo.isDone)
                                .labelsHidden()
                                .toggleStyle(CheckboxToggleStyle())

                            Text(todo.title)
                                .strikethrough(todo.isDone)
                                .foregroundColor(todo.isDone ? .gray : .primary)

                            Spacer()
                        }
                    }
                    // 왼쪽 스와이프로 삭제 (iOS 기본 UX)
                    .onDelete { indexSet in
                        todos.remove(atOffsets: indexSet)
                    }
                }
            }
            .navigationTitle("할 일 목록")
        }
    }
}

struct CheckboxToggleStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        Button(action: { configuration.isOn.toggle() }) {
            Image(systemName: configuration.isOn
                  ? "checkmark.square.fill"
                  : "square")
            .foregroundColor(configuration.isOn ? .blue : .gray)
        }
        .buttonStyle(.plain)
    }
}
```

---

## STEP 3: 날씨 앱 - API 통신, 화면 전환, 비동기 처리
**목표**: REST API 호출, 네비게이션, 로딩/에러 처리, ViewModel 패턴

### 사전 준비: OpenWeatherMap API 키 발급

```
1. https://openweathermap.org 회원가입
2. 로그인 → API Keys 메뉴
3. 기본 제공되는 API Key 복사 (무료, 분당 60회 호출 가능)
4. 아래 코드의 "YOUR_API_KEY" 부분에 붙여넣기
```

### Android (Kotlin + Compose)

#### 의존성 추가 (build.gradle.kts)

```kotlin
// package.json의 "dependencies"와 같은 역할
dependencies {
    // Retrofit = fetch/axios 대체
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")

    // Navigation = React Router 대체
    implementation("androidx.navigation:navigation-compose:2.8.5")

    // ViewModel = 상태 관리
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")

    // Coil = 이미지 로딩 (Coil 3은 io.coil-kt.coil3로 패키지가 바뀜)
    implementation("io.coil-kt.coil3:coil-compose:3.0.4")
    implementation("io.coil-kt.coil3:coil-network-okhttp:3.0.4")
}
// 추가 후 상단에 뜨는 "Sync Now" 클릭!
```

> 위 버전들은 작성 시점 최신입니다. 더 새로운 버전이 나왔으면 [maven.google.com](https://maven.google.com) 또는 IDE의 "Update Available" 알림을 따라가세요.

#### API 서비스 정의

```kotlin
// api/WeatherApi.kt

// JS 객체 대신 data class로 JSON 구조 정의
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
        @Query("appid") apiKey: String = "YOUR_API_KEY",
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

#### ViewModel (상태 관리)

```kotlin
// viewmodel/WeatherViewModel.kt

// JS: let state = { status: 'loading' } 같은 상태 표현
sealed class WeatherUiState {
    object Loading : WeatherUiState()
    data class Success(val data: WeatherResponse) : WeatherUiState()
    data class Error(val message: String) : WeatherUiState()
}

class WeatherViewModel : ViewModel() {
    // JS: const [uiState, setUiState] = useState(null)
    private val _uiState = MutableStateFlow<WeatherUiState?>(null)
    // .asStateFlow()로 외부에는 읽기 전용으로만 노출 (외부에서 캐스팅 후 변경 불가)
    val uiState: StateFlow<WeatherUiState?> = _uiState.asStateFlow()

    fun fetchWeather(city: String) {
        // JS와 비교:
        // async function fetchWeather() {
        //     setLoading(true)
        //     try { const data = await fetch(url); setData(data) }
        //     catch(e) { setError(e.message) }
        // }
        viewModelScope.launch {
            _uiState.value = WeatherUiState.Loading
            try {
                val response = RetrofitClient.weatherApi.getWeather(city)
                _uiState.value = WeatherUiState.Success(response)
            } catch (e: Exception) {
                _uiState.value = WeatherUiState.Error(
                    e.message ?: "알 수 없는 오류"
                )
            }
        }
    }
}
```

#### 화면 + 네비게이션

```kotlin
// navigation/AppNavigation.kt

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    // JS: <BrowserRouter><Routes> ... </Routes></BrowserRouter>
    NavHost(navController = navController, startDestination = "search") {
        // JS: <Route path="/search" element={<SearchScreen />} />
        composable("search") {
            SearchScreen(
                onSearch = { city ->
                    // JS: navigate(`/weather/${city}`)
                    navController.navigate("weather/$city")
                }
            )
        }
        // JS: <Route path="/weather/:city" element={<WeatherScreen />} />
        composable("weather/{city}") { backStackEntry ->
            val city = backStackEntry.arguments?.getString("city") ?: ""
            WeatherScreen(
                city = city,
                onBack = { navController.popBackStack() }
            )
        }
    }
}

@Composable
fun SearchScreen(onSearch: (String) -> Unit) {
    var city by remember { mutableStateOf("") }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("날씨 검색", fontSize = 28.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(24.dp))
        OutlinedTextField(
            value = city,
            onValueChange = { city = it },
            placeholder = { Text("도시 이름 입력") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = { if (city.isNotBlank()) onSearch(city) },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("검색")
        }
    }
}

@Composable
fun WeatherScreen(city: String, onBack: () -> Unit) {
    val viewModel: WeatherViewModel = viewModel()
    val uiState by viewModel.uiState.collectAsState()

    // JS: useEffect(() => { fetchWeather(city) }, [city])
    LaunchedEffect(city) {
        viewModel.fetchWeather(city)
    }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        IconButton(onClick = onBack) {
            // ⚠️ Icons.Default.ArrowBack은 deprecated.
            // AutoMirrored 버전을 써야 RTL 언어(아랍어 등)에서 자동 좌우 반전됨
            Icon(Icons.AutoMirrored.Filled.ArrowBack, "뒤로")
        }

        // JS: {loading && <Spinner />}
        //     {error && <p>{error}</p>}
        //     {data && <WeatherInfo />}
        when (val state = uiState) {
            is WeatherUiState.Loading -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            is WeatherUiState.Success -> {
                val weather = state.data
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(weather.name, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    Text("${weather.main.temp}°C", fontSize = 64.sp)
                    Text(weather.weather.firstOrNull()?.description ?: "")
                    Text("습도: ${weather.main.humidity}%")
                }
            }
            is WeatherUiState.Error -> {
                Text("오류: ${state.message}", color = Color.Red)
            }
            null -> {}
        }
    }
}
```

### iOS (Swift + SwiftUI)

#### API 서비스

```swift
// Services/WeatherService.swift

struct WeatherResponse: Codable {  // Codable = JSON.parse() 자동화
    let main: Main
    let weather: [Weather]
    let name: String
}
struct Main: Codable { let temp: Double; let humidity: Int }
struct Weather: Codable { let description: String; let icon: String }

class WeatherService {
    // JS: async function fetchWeather(city) {
    //       const res = await fetch(url)
    //       return await res.json()
    //     }
    func fetchWeather(city: String) async throws -> WeatherResponse {
        let urlString = "https://api.openweathermap.org/data/2.5/weather?q=\(city)&appid=YOUR_KEY&units=metric&lang=kr"
        guard let url = URL(string: urlString) else {
            throw URLError(.badURL)
        }
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(WeatherResponse.self, from: data)
    }
}
```

#### ViewModel

```swift
// ViewModels/WeatherViewModel.swift

@Observable
class WeatherViewModel {
    var weather: WeatherResponse?
    var isLoading = false
    var errorMessage: String?

    private let service = WeatherService()

    func fetchWeather(city: String) async {
        isLoading = true
        errorMessage = nil
        do {
            weather = try await service.fetchWeather(city: city)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
```

#### 화면 + 네비게이션

```swift
// Views/ContentView.swift

struct ContentView: View {
    var body: some View {
        NavigationStack {
            SearchView()
        }
    }
}

struct SearchView: View {
    @State private var city = ""

    var body: some View {
        VStack(spacing: 24) {
            Text("날씨 검색")
                .font(.largeTitle)
                .fontWeight(.bold)

            TextField("도시 이름 입력", text: $city)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal)

            NavigationLink("검색", value: city)
                .buttonStyle(.borderedProminent)
                .disabled(city.isEmpty)
        }
        .navigationDestination(for: String.self) { city in
            WeatherView(city: city)
        }
    }
}

struct WeatherView: View {
    let city: String
    @State private var viewModel = WeatherViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("로딩 중...")
            } else if let error = viewModel.errorMessage {
                Text("오류: \(error)").foregroundColor(.red)
            } else if let weather = viewModel.weather {
                VStack(spacing: 16) {
                    Text(weather.name)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text("\(weather.main.temp, specifier: "%.1f")°C")
                        .font(.system(size: 64))
                    Text(weather.weather.first?.description ?? "")
                    Text("습도: \(weather.main.humidity)%")
                }
            }
        }
        .navigationTitle(city)
        // JS: useEffect(() => { fetchWeather() }, [])
        .task {
            await viewModel.fetchWeather(city: city)
        }
    }
}
```

---

## STEP 4: 메모 앱 (완성형) - 로컬 DB, 이미지, 테마
**목표**: 로컬 데이터베이스, 이미지 첨부, 다크모드, 앱스토어 출시 준비

### Android 핵심 구성요소

```kotlin
// 1. Room DB 설정 (localStorage 업그레이드 버전)

// 의존성 추가 (build.gradle.kts)
// implementation("androidx.room:room-runtime:2.6.1")
// implementation("androidx.room:room-ktx:2.6.1")
// ksp("androidx.room:room-compiler:2.6.1")

@Entity(tableName = "memos")
data class Memo(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val title: String,
    val content: String,
    val imageUri: String? = null,
    val createdAt: Long = System.currentTimeMillis()  // Date.now()
)

@Dao  // 데이터 접근 메서드 정의
interface MemoDao {
    // JS: db.memos.find().sort('-createdAt')
    @Query("SELECT * FROM memos ORDER BY createdAt DESC")
    fun getAll(): Flow<List<Memo>>

    // JS: db.memos.upsert(memo)
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(memo: Memo)

    // JS: db.memos.delete(memo)
    @Delete
    suspend fun delete(memo: Memo)
}

@Database(entities = [Memo::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun memoDao(): MemoDao
}

// 2. 이미지 선택 (JS: <input type="file" accept="image/*" />)
@Composable
fun ImagePicker(onImageSelected: (Uri?) -> Unit) {
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri -> onImageSelected(uri) }

    Button(onClick = { launcher.launch("image/*") }) {
        Icon(Icons.Default.AddAPhoto, "사진 추가")
        Text("사진 추가")
    }
}

// 3. 다크모드 대응
// JS: window.matchMedia('(prefers-color-scheme: dark)')
@Composable
fun MemoApp() {
    val darkTheme = isSystemInDarkTheme()
    MaterialTheme(
        colorScheme = if (darkTheme) darkColorScheme() else lightColorScheme()
    ) {
        // 앱 콘텐츠 - 테마 자동 적용
    }
}
```

### iOS 핵심 구성요소

```swift
// 1. SwiftData 설정 (iOS 17+)

@Model
class Memo {
    var title: String
    var content: String
    var imageData: Data?          // JS: Blob
    var createdAt: Date           // JS: new Date()

    init(title: String, content: String, imageData: Data? = nil) {
        self.title = title
        self.content = content
        self.imageData = imageData
        self.createdAt = Date()
    }
}

// 2. 메모 목록 화면
struct MemoListView: View {
    @Query(sort: \Memo.createdAt, order: .reverse) var memos: [Memo]
    @Environment(\.modelContext) var context

    var body: some View {
        List {
            ForEach(memos) { memo in
                NavigationLink(value: memo) {
                    VStack(alignment: .leading) {
                        Text(memo.title).font(.headline)
                        Text(memo.content)
                            .lineLimit(2)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .onDelete { indexSet in
                for index in indexSet {
                    context.delete(memos[index])
                }
            }
        }
    }
}

// 3. 이미지 선택 + 편집
struct MemoEditorView: View {
    @State private var showImagePicker = false
    @State private var selectedImage: UIImage?

    var body: some View {
        VStack {
            if let image = selectedImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(height: 200)
            }

            Button("사진 추가") { showImagePicker = true }
                .sheet(isPresented: $showImagePicker) {
                    ImagePicker(image: $selectedImage)
                }
        }
    }
}

// 4. 앱 진입점
@main
struct MemoApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.none)  // 시스템 다크모드 자동 따름
        }
        .modelContainer(for: Memo.self)
    }
}
```

---

# PART 4: 실전 보강 (출시 전 알아둘 것)

샘플 앱 4개를 끝낸 시점에 부족한 부분들. 실제 출시할 앱이라면 반드시 마주치는 주제입니다.

## 4-1. 디버깅 / 로그

### Android — Logcat

```kotlin
import android.util.Log

Log.d("MyTag", "디버그 메시지")     // Debug
Log.i("MyTag", "정보")              // Info
Log.w("MyTag", "경고")              // Warning
Log.e("MyTag", "에러", exception)   // Error
```

**Logcat 보는 법**: Android Studio 하단 "Logcat" 탭 → 우측 검색창에 `tag:MyTag` 또는 `package:com.yourname.app` 입력해서 필터링

JS의 `console.log`와 비교: 결국 같지만 **태그 필터링이 강력**합니다.

### iOS — Xcode Console + os.Logger

```swift
// 옛날 방식 (지금도 동작)
print("디버그 메시지")

// 권장: os.Logger (iOS 14+)
import os
let logger = Logger(subsystem: "com.yourname.app", category: "main")

logger.debug("디버그")
logger.info("정보")
logger.warning("경고")
logger.error("에러: \(error.localizedDescription)")
```

**Console 보는 법**: Xcode 하단 디버그 영역에 자동 출력. 또는 **Mac의 Console.app**에서 기기 선택 후 subsystem으로 필터링.

### 브레이크포인트 (둘 다 필수 익히기)

- 줄 번호 옆 클릭 → 빨간 점 → 코드 실행이 그 줄에서 멈춤
- 변수 값 검사, Step Over (F8/F6), Step Into (F7) 등 사용
- JS의 `debugger` 키워드와 같은 개념이지만 훨씬 강력함

## 4-2. 권한 처리 (Permissions)

거의 모든 실전 앱은 권한이 필요합니다.

### Android

**1단계: AndroidManifest.xml 선언**
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
```

**2단계: 런타임 권한 요청 (Android 6+)**
```kotlin
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts

@Composable
fun CameraButton() {
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            // 권한 OK → 카메라 사용
        } else {
            // 거부됨 → 안내 메시지
        }
    }

    Button(onClick = { launcher.launch(android.Manifest.permission.CAMERA) }) {
        Text("카메라 사용")
    }
}
```

### iOS

**1단계: Info.plist에 권한 설명 문구 추가**
```xml
<key>NSCameraUsageDescription</key>
<string>프로필 사진을 촬영하기 위해 카메라가 필요합니다.</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>갤러리에서 사진을 선택하기 위해 필요합니다.</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>현재 위치 기반 추천을 위해 필요합니다.</string>
```

> ⚠️ 설명 문구 없이 권한 요청하면 **앱이 즉시 크래시** 납니다. App Store 심사도 리젝됩니다.

**2단계: 런타임 요청 (대부분 SDK가 자동으로 띄움)**
```swift
import AVFoundation

func requestCamera() async -> Bool {
    return await AVCaptureDevice.requestAccess(for: .video)
}
```

## 4-3. AdMob (광고 수익화)

광고 기반 무료 앱의 핵심 SDK. Google 공식 샘플 리포지토리에 풀 예제가 있습니다.

### Android

**1단계: build.gradle.kts 의존성**
```kotlin
implementation("com.google.android.gms:play-services-ads:23.6.0")
implementation("com.google.android.ump:user-messaging-platform:3.0.0")
```

**2단계: AndroidManifest.xml**
```xml
<meta-data
    android:name="com.google.android.gms.ads.APPLICATION_ID"
    android:value="ca-app-pub-3940256099942544~3347511713" />  <!-- 테스트 ID -->
```

**3단계: 초기화 + 광고 로딩**
```kotlin
// Application 클래스에서
MobileAds.initialize(context) {}

// 전면광고 로드 → 표시
InterstitialAd.load(context, adUnitId, AdRequest.Builder().build(), callback)
```

→ 공식 샘플: [googleads/googleads-mobile-android-examples](https://github.com/googleads/googleads-mobile-android-examples) — 배너/전면/보상형/네이티브 전부 Kotlin 예제 포함

### iOS

**1단계: SPM으로 SDK 추가**
- Xcode → File → Add Package Dependencies
- URL: `https://github.com/googleads/swift-package-manager-google-mobile-ads`

**2단계: Info.plist**
```xml
<key>GADApplicationIdentifier</key>
<string>ca-app-pub-3940256099942544~1458002511</string>

<key>NSUserTrackingUsageDescription</key>
<string>맞춤형 광고를 제공하기 위해 필요합니다.</string>
```

**3단계: 초기화 (11.x SDK 기준)**
```swift
import GoogleMobileAds
import AppTrackingTransparency

@main
struct MyApp: App {
    init() {
        // ATT 권한 먼저 → 그 다음 AdMob start
        if #available(iOS 14, *) {
            ATTrackingManager.requestTrackingAuthorization { _ in
                GADMobileAds.sharedInstance().start { _ in }
            }
        } else {
            GADMobileAds.sharedInstance().start { _ in }
        }
    }
    var body: some Scene { ... }
}
```

> **타입 이름 주의**: GoogleMobileAds 11.x 는 Objective-C 타입을 그대로 노출하므로 `GAD` 접두사가 붙습니다 — `GADInterstitialAd`, `GADRewardedAd`, `GADBannerView`, `GADRequest`, `GADFullScreenContentDelegate`, `GADFullScreenPresentingAd`. 12.x 이후로는 Swift 오버레이에서 `InterstitialAd` 같은 간결한 이름이 생길 수 있으니 SDK 버전 확인 후 쓸 것.
>
> **ATT 순서**: 반드시 `ATTrackingManager.requestTrackingAuthorization` 이 끝난 뒤에 `GADMobileAds.sharedInstance().start` 호출. 순서가 바뀌면 IDFA 전달 못 받고 eCPM 떨어짐.

> **테스트 ID와 실제 ID**: 개발 중에는 반드시 Google 공식 테스트 ID(`ca-app-pub-3940256099942544/...`) 사용. 본인 광고를 직접 클릭하면 AdMob 계정이 영구 정지됩니다.

→ 공식 샘플: [googleads/googleads-mobile-ios-examples](https://github.com/googleads/googleads-mobile-ios-examples) — Swift + SwiftUI 통합 예제 포함

## 4-4. 출시 빌드 / 서명 (Release Build / Signing)

스토어에 올리려면 "디버그 빌드"가 아닌 "릴리즈 빌드"가 필요합니다.

### Android — Keystore 생성

```bash
# 한 번만 실행. 25년 유효한 키스토어 생성
keytool -genkeypair -v \
  -keystore release.keystore \
  -alias my-app \
  -keyalg RSA \
  -keysize 2048 \
  -validity 9125 \
  -storepass YourStrongPassword \
  -keypass YourStrongPassword \
  -dname "CN=My App, O=MyOrg, L=Seoul, C=KR"
```

⚠️ **이 keystore 파일은 절대로 잃어버리면 안 됩니다.**
- 분실 시 같은 패키지명으로 앱 업데이트 영원히 불가
- iCloud Drive / Google Drive 등에 백업 필수

**build.gradle.kts에 서명 설정:**
```kotlin
signingConfigs {
    create("release") {
        storeFile = file("release.keystore")
        storePassword = "YourStrongPassword"
        keyAlias = "my-app"
        keyPassword = "YourStrongPassword"
    }
}

buildTypes {
    release {
        isMinifyEnabled = true
        signingConfig = signingConfigs.getByName("release")
        proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
    }
}
```

> 비밀번호를 코드에 하드코딩하는 대신 `keystore.properties` 파일로 분리해서 `.gitignore`에 추가하는 게 표준 패턴입니다.

**AAB(Android App Bundle) 빌드:**
```bash
./gradlew bundleRelease
# → app/build/outputs/bundle/release/app-release.aab 생성
# 이 파일을 Google Play Console에 업로드
```

### iOS — Code Signing + Archive

iOS는 Apple Developer Program ($99/년) 가입 후 자동 서명이 권장됩니다.

1. Xcode → 프로젝트 선택 → "Signing & Capabilities" 탭
2. **Team** 드롭다운에서 본인 Apple ID 선택 (자동 프로비저닝)
3. Bundle Identifier 고유 값 입력 (예: `com.yourname.myapp`)
4. 메뉴 → **Product → Archive** 클릭
5. Organizer 창에서 **Distribute App** → App Store Connect

> Android와 달리 keystore를 직접 관리할 일이 거의 없음. Apple이 클라우드에서 자동 관리.

## 4-5. ProGuard / R8 (코드 난독화 - Android)

릴리즈 빌드에서 `isMinifyEnabled = true`로 켜면 R8이 사용 안 하는 코드를 제거하고 클래스명을 난독화합니다. 앱 크기 30% 이상 줄어요.

**부작용**: 리플렉션을 쓰는 라이브러리(Gson, Retrofit, AdMob 등)는 클래스가 지워지지 않게 `proguard-rules.pro`에 keep 규칙을 추가해야 합니다.

```proguard
# Gson - data class 보존
-keep class com.yourname.app.data.** { *; }

# AdMob
-keep class com.google.android.gms.ads.** { *; }
-dontwarn com.google.android.gms.**

# Retrofit
-keepattributes Signature
-keep class retrofit2.** { *; }
```

규칙 빠뜨리면 **개발 모드에선 멀쩡한데 릴리즈 빌드에서 크래시** 나는 가장 짜증나는 버그가 발생합니다.

## 4-6. 흔한 에러 읽는 법

### Kotlin Compile Error 패턴
```
e: file:///path/to/File.kt:42:11 Unresolved reference: SomeClass
```
→ import 누락 또는 의존성 안 추가됨. 보통 IDE가 빨간 줄 + alt+enter로 자동 해결.

### Swift Compile Error 패턴
```
Cannot find 'someVariable' in scope
```
→ 변수가 다른 스코프에 있거나 오타. SwiftUI는 특히 복잡한 표현식 에러가 발생하면 메시지가 부정확하니, 의심되는 줄을 작은 변수로 쪼개서 다시 컴파일해보세요.

### 런타임 크래시 (둘 다)
- **Android**: Logcat에서 `FATAL EXCEPTION` 검색 → 스택트레이스 위에서 본인 패키지명 줄 찾기
- **iOS**: Xcode 콘솔에 `Thread 1: Fatal error: Unexpectedly found nil while unwrapping an Optional value` 같은 메시지 → Optional 풀기 잘못한 곳 추적

> Claude Code에 에러 메시지 그대로 붙여넣으면 거의 다 해결됩니다.

## 4-7. 실전 코드 학습 — 공식/오픈소스 샘플 앱

튜토리얼의 STEP 1~4 개념이 실전 수준으로 구현된 레퍼런스 프로젝트들입니다. 로컬에 클론해서 직접 실행해보는 걸 강력 추천합니다. **공신력 있고 유지보수가 활발한 샘플만 엄선**했습니다.

### Android — Kotlin + Jetpack Compose

| 샘플 | 레벨 | URL | 추천 이유 |
|------|------|-----|----------|
| **Now in Android** | 중급~고급 | [android/nowinandroid](https://github.com/android/nowinandroid) | Google 공식. 실전 아키텍처의 끝판왕 — Compose + MVVM + Hilt + DataStore + 멀티 모듈 + 단위/UI 테스트 전부 포함. Android DevRel팀이 직접 관리, 매년 구글 I/O에서 신 API 반영 |
| **Jetpack Compose Samples** | 초급~중급 | [android/compose-samples](https://github.com/android/compose-samples) | Google 공식 Compose 샘플 모음 9종. **Jetsurvey**(폼/온보딩), **Jetcaster**(팟캐스트 플레이어), **Jetchat**(채팅), **Crane**(여행), **Owl**(교육), **Reply**(이메일) 등 |
| **Jetsurvey** | 초급 | compose-samples 내부 | 위 모음 중 가장 가벼움. 온보딩/폼/상태관리/네비게이션 기본기만 딱 |

**추천 학습 순서**: Jetsurvey (작은 것부터) → Jetchat 또는 Crane (중간 규모) → Now in Android (실전 수준)

### iOS — Swift + SwiftUI

| 샘플 | 레벨 | URL | 추천 이유 |
|------|------|-----|----------|
| **Apple Landmarks 튜토리얼** | 초급 | [developer.apple.com/tutorials/swiftui](https://developer.apple.com/tutorials/swiftui) | Apple 공식 SwiftUI 입문 튜토리얼. 리스트/상세/지도/애니메이션/프로필까지 기본 전부 단계별로. **가장 먼저 할 것** |
| **Food Truck** | 중급 | [Apple Developer Documentation](https://developer.apple.com/documentation/swiftui/food_truck_building_a_swiftui_multiplatform_app) | Apple 공식. SwiftUI 멀티플랫폼(iOS + macOS) + CloudKit + Live Activity + WidgetKit 통합 예제 |
| **Destination Video** | 중급 | [Apple Sample Code Library](https://developer.apple.com/documentation/visionos/destination-video) | visionOS + iOS + tvOS 공통 SwiftUI 앱. 네비게이션/미디어 플레이어 구조 참고 |

**추천 학습 순서**: Landmarks 튜토리얼 (끝까지) → Food Truck → Apple Sample Code Library에서 관심 분야 검색

### 광고(AdMob) 통합 레퍼런스

| 플랫폼 | 공식 샘플 리포 |
|--------|----------------|
| Android | [googleads/googleads-mobile-android-examples](https://github.com/googleads/googleads-mobile-android-examples) |
| iOS | [googleads/googleads-mobile-ios-examples](https://github.com/googleads/googleads-mobile-ios-examples) |

Google 공식 유지. 배너/전면/보상형/네이티브 광고 전부 Kotlin+Swift 둘 다 샘플 있음. **이 두 리포만 있으면 AdMob 통합은 해결**됩니다. SDK 버전 업데이트마다 바로 반영되니 최신 API 확인에도 쓸 수 있음.

### 튜토리얼 → 실전 매핑

| 튜토리얼 STEP | Android 참고 | iOS 참고 |
|---|---|---|
| STEP 1 (UI 기초) | Jetsurvey `OnboardingScreen` | Landmarks 튜토리얼 Part 1 (Creating and Combining Views) |
| STEP 2 (리스트) | Jetcaster 또는 Now in Android의 피드 화면 | Landmarks 튜토리얼 Part 4 (Building Lists and Navigation) |
| STEP 3 (ViewModel/네비) | Now in Android `feature/*` 모듈의 ViewModel 구조 | Food Truck (NavigationStack + @Observable 조합) |
| STEP 4 (저장) | Now in Android의 DataStore 사용 부분 | Food Truck의 SwiftData + CloudKit 파트 |
| 4-2 권한 | compose-samples의 카메라/위치 예제 | Apple 공식 "Accessing the Camera" 샘플 |
| 4-3 AdMob | googleads-mobile-android-examples | googleads-mobile-ios-examples |
| 4-4 Release | [Android Developers: App Signing](https://developer.android.com/studio/publish/app-signing) | [Apple: Distributing your app](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases) |

### 학습 팁

1. **처음엔 전부 읽지 말 것**: Now in Android만 해도 파일 200개 넘음. 한 번에 다 이해하려 하지 말고 관심 화면 1~2개만 집중
2. **같은 기능을 양 플랫폼에 동시 비교**: 예를 들어 "설정 화면"을 Jetsurvey의 OnboardingScreen ↔ Landmarks의 Profile 화면으로 나란히 놓고 보면 Kotlin↔Swift 감각이 빨리 붙음
3. **타이핑해보기**: 단순 읽기보다 샘플의 화면 하나를 자기 프로젝트에 타이핑으로 옮겨보는 게 체감 학습량 10배
4. **Issue/PR 열어보기**: 모르는 코드 패턴 나오면 해당 리포의 PR 히스토리를 뒤져보세요. "왜 이렇게 짰는가"가 PR 설명에 자주 나옵니다

---

## 4-8. 플랫폼 고유 기능 (네이티브를 쓰는 진짜 이유)

> **프로젝트 룰**: CLAUDE.md에 따라 모든 신규 앱은 **플랫폼 고유 기능 1개 이상**을 기획 단계에서 반드시 포함합니다. 이 기능들이 RN으로는 만들기 어렵거나 불가능한 영역이고, 네이티브 전략의 차별화 포인트입니다.

### iOS 고유 기능

| 기능 | 언제 쓰나 | 1차 학습 링크 |
|------|-----------|---------------|
| **Live Activity / Dynamic Island** | 타이머, 진행중 작업, 배달 추적, 운동 세션 | [ActivityKit 공식 튜토리얼](https://developer.apple.com/documentation/activitykit) |
| **WidgetKit 위젯** | 매일 보는 데이터(날씨, 습관, 일정, 기여도 그래프) | [WidgetKit 공식 튜토리얼](https://developer.apple.com/documentation/widgetkit) |
| **App Intents / Siri / Shortcuts** | 1탭 또는 음성으로 액션 실행 (타이머 시작 등) | [App Intents 프레임워크](https://developer.apple.com/documentation/appintents) |
| **SwiftData + CloudKit 동기화** | 멀티 기기에서 데이터 동기화 필요한 앱 | [SwiftData 공식 문서](https://developer.apple.com/documentation/swiftdata) |
| **Live Text / Vision** | 이미지에서 텍스트/바코드/얼굴 인식 | [Vision 프레임워크](https://developer.apple.com/documentation/vision) |
| **SF Symbols 애니메이션** | 아이콘 살짝 움직임만으로 고급 UX | Xcode → SF Symbols 앱 |

**iOS 앱 만들 때 가장 효과 큰 것**: **Live Activity + Dynamic Island**. 타이머/진행 상황/카운트다운이 있는 앱은 붙이는 순간 경쟁 앱 대비 확실히 구별됩니다.

### Android 고유 기능

| 기능 | 언제 쓰나 | 1차 학습 링크 |
|------|-----------|---------------|
| **App Widgets (Glance API)** | 홈 스크린 위젯 — 매일 체크 데이터, 빠른 기록 | [Jetpack Glance](https://developer.android.com/jetpack/androidx/releases/glance) |
| **Material You Dynamic Color** | 사용자 배경화면 기반 자동 테마 (공짜 차별화) | [Dynamic Color 가이드](https://developer.android.com/develop/ui/views/theming/dynamic-colors) |
| **Quick Settings Tile** | 알림 패널에서 1탭 실행 (타이머, 집중 모드 등) | [TileService 문서](https://developer.android.com/reference/android/service/quicksettings/TileService) |
| **Wear OS 컴패니언** | 건강/타이머/노티 앱의 손목 버전 | [Wear OS 개발 가이드](https://developer.android.com/training/wearables) |
| **Foreground Service + Notification** | 백그라운드 타이머, 걸음수, 음악 재생 | [포그라운드 서비스 문서](https://developer.android.com/develop/background-work/services/foreground-services) |
| **Android Auto / Automotive** | 자동차 연동 (좁은 시장이지만 경쟁 없음) | [Android Auto 가이드](https://developer.android.com/cars) |

**Android 앱 만들 때 가장 효과 큰 것**: **App Widget (Glance)**. Play Store에서 "위젯 지원" 필터가 실제로 존재할 만큼 유저가 찾는 기능.

### 실전 예시: "할 일 앱"을 네이티브 고유 기능으로 차별화하기

```
iOS:
├─ Live Activity: 오늘 남은 할 일 개수를 Dynamic Island에 표시
├─ Widget: 홈 화면 중간 사이즈에 오늘의 할 일 리스트
└─ App Intents: Siri "오늘 할 일 추가해줘" 음성 명령

Android:
├─ App Widget (Glance): 홈 화면에서 체크박스 직접 탭으로 완료 처리
├─ Quick Settings Tile: 알림 패널에서 1탭으로 "빠른 기록" 실행
└─ Material You: 사용자 배경화면 색상으로 앱 테마 자동 맞춤
```

→ 이게 RN에서는 각각 네이티브 모듈 만들거나 외부 라이브러리 뒤져야 가능. 네이티브는 **공식 템플릿이 있고 문서도 풍부**해서 1~2일이면 붙일 수 있습니다.

### 학습 우선순위

1. 일단 **기본 앱(STEP 1~4)을 완료**할 것. 플랫폼 고유 기능은 그 다음
2. 첫 실전 앱(1~2번째)은 **Widget부터 시도** — 양 플랫폼 다 문서 잘 되어 있고, ROI 가장 큼
3. 3~4번째 앱에서 Live Activity, App Intents 같은 고급 기능 시도
4. 처음부터 다 쓰려고 하지 말 것 — 한 번에 1개 고유 기능만

---

# PART 5: 학습 로드맵 & 리소스

## 추천 타임라인

최근에는 **Claude, GitHub Copilot, Cursor 같은 AI 코딩 어시스트** 환경에서 개발하는 경우가 많습니다. 이 환경에서는 학습 목표가 전통적인 경우와 달라집니다:

- **목표 A (Fast-track)**: Claude가 쓴 코드를 "읽고 이해하고 판단"할 수 있는 수준. 리뷰/디버깅/기획에 필요한 최소 지식.
- **목표 B (Full)**: Claude 없이도 직접 코딩할 수 있는 수준. 전통적인 네이티브 개발자 수준.

### 🚀 Fast-track (Claude 어시스트 환경 — 추천)

**목표**: 위 오픈소스 샘플 앱(Now in Android, Food Truck 등) 코드를 술술 읽고, AI에게 "이 ViewModel의 `_state` 가 왜 private 이야?" 같은 구체적 질문을 할 수 있는 수준

| 단계 | 내용 | 예상 시간 |
|------|------|----------|
| 1 | PART 0 — 환경 세팅 (Android Studio / Xcode 설치, 에뮬레이터/시뮬레이터 실행) | 2~3시간 |
| 2 | PART 1 — 문법 맛보기 **훑어 읽기** (직접 쳐보지 말고 읽기만) | 1~2시간 |
| 3 | PART 2 — 치트시트 **북마크** (나중에 필요할 때 찾아볼 것) | 10분 |
| 4 | PART 3 STEP 1 (Hello World) **만** 양 플랫폼 직접 해보기 — 구조 감각 잡기 용도 | 2~3시간 |
| 5 | PART 4 — 실전 보강 **전체 읽기** (4-1 디버깅, 4-2 권한, 4-3 AdMob, 4-4 Release, 4-6 에러 읽는 법, 4-8 플랫폼 고유 기능) | 2~3시간 |
| 6 | PART 4-7 — 오픈소스 샘플 앱(Jetsurvey + Landmarks 튜토리얼) 코드 **30분 정도 둘러보기** | 30분~1시간 |

**총 예상 시간: 8~13시간** (주말 하루 투자 + 평일 저녁 2~3일)

이 루트의 장점:
- Claude가 STEP 2~4 같은 샘플 앱 수준의 코드를 직접 써주므로, 사용자가 똑같은 걸 타이핑할 이유가 없음
- 대신 "어떤 구조로 짜야 하는지", "에러가 나면 어떻게 읽는지", "AdMob 정책은 뭔지" 같은 **판단 기준**을 익히는 게 시간 대비 효율이 압도적
- 실제 앱 만들면서 모르는 게 나오면 그때 Claude에게 "이 부분 설명해줘" 하면 됨 → 필요한 지식만 JIT(Just-in-Time)으로 학습

이 루트의 한계:
- Claude가 없으면 0부터 코딩 못 함 (그럴 일이 없긴 하지만)
- 언어 레벨 디테일(예: Kotlin Coroutines의 CoroutineContext 같은 것)에 약함 — 필요할 때 그때그때 파기

### 🎓 Full (전통 네이티브 개발자 루트)

**목표**: 나중에 Claude 없어도 직접 앱 개발 가능한 수준

| 주차 | 내용 | 산출물 |
|------|------|--------|
| 0주차 | PART 0~1: 환경 세팅 + 문법 맛보기 (직접 타이핑) | 에뮬레이터/시뮬레이터 실행 확인, 문법 연습 |
| 1주차 | STEP 1: Hello World + Preview/SafeArea 익히기 | 카운터 앱 (양 플랫폼) |
| 2주차 | STEP 2: 할 일 목록 | CRUD 앱 (양 플랫폼) |
| 3주차 | STEP 3: API 통신 + 네비게이션 | 날씨 앱 (양 플랫폼) |
| 4주차 | STEP 4: 로컬 DB + 이미지 + 권한 (PART 4-2) | 메모 앱 (양 플랫폼) |
| 5주차 | PART 4 실전 보강 (디버깅/AdMob/Release) + 오픈소스 샘플 앱 분석 | 첫 광고 포함 앱 |
| 6주차 | PART 4-8 플랫폼 고유 기능 중 1개 학습 (Widget 추천) | Widget 붙인 앱 |
| 7주차~ | 나만의 사업 아이디어 앱 개발 + 출시 | 첫 출시 앱 |

**총 예상 시간: 50~80시간** (6~8주, 주당 8~10시간 꾸준히)

### 어느 루트를 선택해야 하나

| 상황 | 추천 루트 |
|------|----------|
| AI 어시스트 도구(Claude/Copilot 등)로 개발할 거임 | **Fast-track** |
| Claude 없이도 모바일 개발자로 전향하고 싶음 | **Full** |
| 시간 여유 많고 언어 자체가 궁금함 | **Full** |
| 지금 당장 앱 출시가 목표임 | **Fast-track + 오픈소스 샘플 코드 읽기** |

### Fast-track으로 결정했다면 이 순서로

1. **지금 당장**: PART 0 (환경 세팅). Android Studio + Xcode 설치, 에뮬레이터/시뮬레이터 한 번씩 실행
2. **저녁 여유 시간**: PART 2 치트시트 + PART 4-1 (디버깅) + PART 4-6 (에러 읽는 법) — 에러 날 때 대응 능력부터
3. **주말**: PART 4-7 오픈소스 샘플 앱(nowinandroid, Food Truck 등)을 Android Studio/Xcode에서 직접 열어서 파일 탐색. 이해 안 되는 부분은 AI에게 질문
4. **첫 앱 만들 때**: PART 4-3 (AdMob) + 4-4 (Release) + 4-8 (플랫폼 고유 기능) 읽고 **해당 앱에 쓸 고유 기능 1개만** 파고들기

## JS 개발자가 특히 주의할 점

### Kotlin (Android)
- `val` = `const`, `var` = `let` (JS와 같은 느낌)
- 세미콜론 안 써도 됨
- `null` 처리 엄격: `String?`과 `String`은 다른 타입
- `==` 가 JS의 `===`처럼 동작 (값 비교, equals 호출)
- ⚠️ Kotlin의 `===`는 **참조 비교** (JS에는 없음, 같은 객체인지 확인)
- 배열: `listOf()` (불변) vs `mutableListOf()` (가변)
- `Icons.Default.X` 중 일부는 deprecated → `Icons.AutoMirrored.Filled.X` 사용 (특히 ArrowBack, MenuBook)

### Swift (iOS)
- `let` = `const`, `var` = `var` (⚠️ JS와 let의 의미가 반대!)
- `guard let x = x else { return }` = null 안전 풀기 (JS에 없는 패턴)
- `struct` = 값 타입 (복사됨), `class` = 참조 타입 (JS처럼)
- 문자열 안에 변수: `\(변수)` (JS: `${변수}`)
- `print()` = `console.log()`

### `if let` vs `guard let` (Swift)

둘 다 Optional 안전하게 풀기지만 용도가 다릅니다:

```swift
// if let: 값이 있을 때만 블록 실행 (있어도/없어도 진행)
func display(name: String?) {
    if let name = name {
        print("이름: \(name)")
    }
    print("끝")  // name이 nil이어도 여기는 실행됨
}

// guard let: 값이 없으면 즉시 종료 (early return 패턴)
func display(name: String?) {
    guard let name = name else {
        print("이름 없음")
        return
    }
    // 이 아래 전체에서 name이 String으로 확정 (Optional 아님)
    print("이름: \(name)")
    print("길이: \(name.count)")
}
```

**언제 어느 걸?**
- `if let`: 값이 있을 때만 잠깐 처리하면 끝 (지역적)
- `guard let`: 함수 시작 시 입력 검증, 없으면 진행 불가 (전역적)

JS 식으로 비교하면:
```javascript
// if let과 비슷
if (name) { console.log(name) }

// guard let과 비슷
if (!name) return
console.log(name)  // 여기서 name이 확정
```

## 유용한 링크

### 문법 연습
- Kotlin: https://play.kotlinlang.org (브라우저에서 바로 실행)
- Swift: https://swiftfiddle.com (브라우저) 또는 Swift Playgrounds 앱

### 공식 튜토리얼
- Android Compose: developer.android.com/jetpack/compose/tutorial
- SwiftUI: developer.apple.com/tutorials/swiftui

### UI 컴포넌트 참고
- Material Design 3: m3.material.io/components
- SF Symbols (iOS 아이콘): developer.apple.com/sf-symbols
- Human Interface Guidelines: developer.apple.com/design

### API
- OpenWeatherMap (무료): openweathermap.org/api

---

> **팁**: 각 단계에서 막히면 JS 코드를 보여주면서
> "이걸 Kotlin/Swift로 어떻게 쓰나요?" 하고 물어보세요.
> 가장 정확하고 빠른 답을 드릴 수 있습니다!
