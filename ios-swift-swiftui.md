# iOS 앱 개발 튜토리얼 (Swift + SwiftUI)
## React / JavaScript 개발자를 위한 완전판

> **이 문서의 범위**: iOS만 다룹니다. 모든 예제가 **JS/React와 1:1 대조**로 되어 있어
> 알던 개념에 이름표만 새로 붙이는 방식으로 진행합니다.
>
> 같은 시리즈: [Android 트랙(Kotlin/Compose)](./android-kotlin-compose.md) · [Unity(C#) 트랙](./react-to-unity.md) · [트랙 선택 가이드(README)](./README.md)
>
> ⚡ **Claude 어시스트 환경이면 [Fast-track 루트](#-fast-track-claude-어시스트-환경--추천)(6~9시간)부터 보세요.** 전체 루트(30~45시간)는 AI 없이 직접 개발할 사람용입니다.
>
> 🖥️ **전제조건: Mac이 필요합니다.** Windows/Linux에서는 Xcode를 설치할 수 없습니다.
> Mac이 없다면 [Android 트랙](./android-kotlin-compose.md)부터 시작하세요.

---

## 목차

- [PART 0: 개발 환경 세팅](#part-0-개발-환경-세팅)
- [PART 1: Swift 문법 (JS와 1:1 비교)](#part-1-swift-문법-js와-11-비교)
- [PART 1.5: Swift 심화](#part-15-swift-심화)
- [PART 2: 매핑 치트시트](#part-2-매핑-치트시트)
- [PART 3: 샘플 앱 만들기](#part-3-샘플-앱-만들기)
- [PART 4: 실전 보강](#part-4-실전-보강)
  - [4-0. SwiftUI 핵심 API 보강](#4-0-swiftui-핵심-api-보강)
- [PART 5: 학습 로드맵 & 리소스](#part-5-학습-로드맵--리소스)

---

# PART 0: 개발 환경 세팅

## 0-1. 필수 요구사항

```
⚠️ iOS 개발은 macOS가 필수입니다.

Mac이 없는 경우 선택지:
1. 중고 MacBook Air (Apple Silicon 이상 권장) — 가장 현실적
2. 클라우드 Mac 서비스 (MacStadium, AWS EC2 Mac 등) — 시간당 과금
3. 크로스플랫폼(Expo 등) + 클라우드 빌드 — 개발은 Windows에서, 빌드만 클라우드
   (이 시리즈 범위 밖입니다. 공식 문서를 보세요)
4. Android 먼저 하고 나중에 iOS

디스크: Xcode + 시뮬레이터 런타임으로 최소 30~40GB 여유 필요
```

> **Apple Silicon(M1 이상)을 강력 권장합니다.** Intel Mac에서도 되지만 빌드·시뮬레이터 속도가
> 체감상 몇 배 차이 납니다. 학습 중엔 "빌드 대기 시간"이 곧 포기율입니다.

## 0-2. Xcode 설치

1. Mac App Store에서 "Xcode" 검색 → 설치 (약 15GB+, 시간 꽤 걸림)
2. 첫 실행 → "Install Additional Components" 동의
3. Command Line Tools 확인:

```bash
xcodebuild -version        # Xcode 버전 출력되면 성공
xcode-select -p            # 설치 경로 확인
```

> **App Store 다운로드가 너무 느리면** [developer.apple.com/download](https://developer.apple.com/download/all/)
> 에서 `.xip` 파일을 직접 받는 편이 빠른 경우가 많습니다 (무료 Apple ID로 로그인 가능).

### 설치 확인 체크리스트

```
✅ Xcode 실행 됨
✅ "Create New Project" 버튼이 보임
✅ Xcode → Settings → Platforms
   → iOS 시뮬레이터 런타임이 설치되어 있는지 확인
   → 없으면 "+" 눌러 다운로드 (별도 용량 필요)
✅ Xcode → Settings → Accounts 에 Apple ID 추가
   (무료 Apple ID로도 시뮬레이터 + 개인 기기 테스트 가능)
```

> **버전 숫자에 대하여**: Apple은 2025년부터 OS/도구 버전을 **연도 기반**으로 통일했습니다
> (iOS 26, Xcode 26 식). 이 문서는 특정 숫자에 의존하지 않게 썼습니다.
> 규칙만 기억하세요 — **Xcode는 최신 정식 버전, 배포 타깃(Deployment Target)은 최신-2 정도.**
> 기능 하나가 최신 OS 전용이면 `if #available(iOS 26, *)`로 분기합니다.

## 0-3. 시뮬레이터

Xcode에 내장되어 있어 별도 설치가 거의 필요 없습니다.

**실행**: Xcode 상단 기기 드롭다운에서 iPhone 모델 선택 → ▶ 버튼

**유용한 단축키:**
```
Cmd + Shift + H     홈 화면으로
Cmd + ← / →         기기 회전
Cmd + S             스크린샷
Cmd + K             하드웨어 키보드 토글  ⭐ 텍스트 입력이 안 될 때 이것부터 확인
Cmd + Shift + A     다크모드 / 라이트모드 전환
Cmd + R             녹화 (Xcode 15+)
```

**시뮬레이터가 안 뜰 때:**
```
Xcode → Settings → Platforms → iOS 런타임 설치 확인
터미널: xcrun simctl list devices        (목록 출력되면 정상)
        xcrun simctl erase all           (시뮬레이터 초기화 — 이상 동작 시)
```

**실제 기기로 테스트 (강력 추천):**
```
1. USB 케이블로 iPhone을 Mac에 연결
2. iPhone에서 "이 컴퓨터를 신뢰하시겠습니까?" → 신뢰
3. Xcode → Settings → Accounts에 Apple ID 로그인
4. 프로젝트 → Signing & Capabilities → Team 선택
5. 상단 기기 목록에서 내 iPhone 선택 → ▶

⚠️ 무료 Apple ID는 앱이 7일 후 만료됩니다 (다시 빌드하면 갱신)
⚠️ 첫 실행 시 iPhone → 설정 → 일반 → VPN 및 기기 관리 → 개발자 앱 신뢰
```

> **시뮬레이터에서 절대 확인할 수 없는 것**: 카메라, 실제 성능, 배터리 영향,
> 진동(햅틱), 실제 스크롤 관성, Face ID 실물 동작.
> "느낌"에 대한 판단은 반드시 실기기에서 하세요.

## 0-4. 첫 프로젝트 생성 & 프로젝트 구조

```
1. Xcode → "Create New Project"
2. iOS → "App" 선택
3. 설정:
   - Product Name: HelloWorld
   - Organization Identifier: com.yourname       ← 역도메인. 나중에 못 바꿉니다
   - Interface: SwiftUI                          ← 반드시 SwiftUI (Storyboard 아님)
   - Language: Swift
   - Testing System: Swift Testing (또는 XCTest)
   - Storage: None
4. 저장 위치 선택 → "Create"
5. ▶ 버튼 → 시뮬레이터에 "Hello, world!" 뜨면 성공
```

> **Bundle Identifier** = `Organization Identifier` + `Product Name` (예: `com.yourname.HelloWorld`).
> App Store에서 앱의 고유 ID이며 **한 번 출시하면 영구히 못 바꿉니다.**

### 폴더 구조 — JS 프로젝트와 대조

```
// JS 프로젝트                   →  iOS 프로젝트
package.json                    →  .xcodeproj (프로젝트 설정) + SPM 의존성
package-lock.json               →  Package.resolved
node_modules/                   →  ~/Library/Developer/Xcode/DerivedData (프로젝트 밖)
src/                            →  프로젝트 폴더 (물리 폴더 = Xcode 그룹, 최근 버전 기준)
  App.js                        →    앱이름App.swift  (@main 진입점)
  components/                   →    Views/
  hooks/, store/                →    ViewModels/
  api/                          →    Services/
  assets/                       →  Assets.xcassets   (이미지·색상·아이콘)
public/index.html               →  Info.plist        (앱 메타·권한 설명)
locales/ko.json                 →  Localizable.xcstrings (String Catalog)
dist/                           →  Products/*.app
```

**꼭 알아야 할 3개:**

| 항목 | 역할 | JS 대응 |
|---|---|---|
| `앱이름App.swift` | `@main` 진입점, 앱 전역 설정 | `index.js` + `App.js` |
| `Info.plist` (또는 Target Info 탭) | 권한 설명 문구, 앱 표시 이름, 지원 방향 | `manifest.json` |
| `Assets.xcassets` | 이미지·색상·앱 아이콘 (다크모드 대응 색상도 여기) | `public/assets` + CSS 변수 |

> **최근 Xcode는 `Info.plist` 파일이 안 보일 수 있습니다.** 프로젝트 설정의
> **Target → Info** 탭에서 같은 값을 편집합니다. "Info.plist에 추가하라"는 안내는
> 그 탭에서 키를 추가하라는 뜻입니다.

## 0-5. Swift Package Manager (의존성 관리)

JS의 npm에 해당합니다. **CocoaPods는 신규 프로젝트에서 쓸 이유가 거의 없습니다.**

```
Xcode → File → Add Package Dependencies…
→ 검색창에 GitHub URL 붙여넣기
→ 버전 규칙 선택 (보통 "Up to Next Major Version")
→ 타깃 선택 → Add Package
```

```swift
// 코드에서는 그냥 import
import Alamofire
```

> **npm과 다른 점**: 설치가 Xcode UI에서 일어나고, 결과가 `.xcodeproj` 안에 기록됩니다.
> 팀 작업 시 `Package.resolved`를 커밋하세요 (= `package-lock.json`).
>
> **실무 팁**: iOS는 표준 라이브러리(URLSession, SwiftData 등)가 강력해서
> **의존성 없이 앱 하나를 통째로 만들 수 있습니다.** JS 생태계와 가장 다른 감각입니다.
> 패키지를 찾기 전에 "Apple 프레임워크에 이미 있는지" 먼저 확인하세요.

## 0-6. 공통 도구

### Claude Code 설치 (사실상 필수)

SwiftUI는 **컴파일 에러 메시지가 부정확한 것**으로 악명 높습니다
(뷰 하나가 복잡해지면 엉뚱한 줄을 가리킵니다). 에러 전문을 붙여넣어 물어보는 것만으로
막히는 시간이 크게 줄어듭니다.

```bash
curl -fsSL https://claude.ai/install.sh | sh
claude --version

cd ~/Developer/HelloWorld
claude          # → /login
```

**효과적인 활용:**
- "The compiler is unable to type-check this expression in reasonable time" → 어디를 쪼갤지 물어보기
- "이 JS 코드를 SwiftUI로" → 변환
- "이 View가 왜 업데이트가 안 되지?" (프로퍼티 래퍼 선택 실수 — 혼자 찾기 가장 어려운 부류)

### Git

```bash
git --version   # Xcode Command Line Tools에 포함되어 있음

# .gitignore 필수 항목
# .DS_Store
# xcuserdata/
# DerivedData/
# *.xcuserstate
# Secrets.swift 또는 API 키가 든 파일
```

> [github.com/github/gitignore/blob/main/Swift.gitignore](https://github.com/github/gitignore/blob/main/Swift.gitignore) 를 그대로 쓰면 됩니다.

## 0-7. Apple Developer Program (나중에 해도 됨)

```
비용: $99/년 (매년 갱신, 미갱신 시 앱이 스토어에서 내려감)
등록: https://developer.apple.com/programs/enroll

준비물:
- Apple ID (2단계 인증 필수)
- 신용카드
- 개인 등록은 이름이 그대로 판매자명으로 노출됨
  (회사명으로 하려면 법인 + D-U-N-S 번호 필요)

등록 후 심사: 보통 1~2일 (신원 확인이 더 걸리기도 함)
```

**유료 계정 없이 가능한 것 / 불가능한 것:**

| | 무료 Apple ID | 유료 ($99/년) |
|---|---|---|
| 시뮬레이터 실행 | ✅ | ✅ |
| 내 기기에 설치 | ✅ (7일 만료) | ✅ (1년) |
| TestFlight 배포 | ❌ | ✅ |
| App Store 출시 | ❌ | ✅ |
| Push 알림, iCloud 등 | ❌ | ✅ |

> **학습 단계에선 무료로 충분합니다.** 실제 출시가 눈앞에 왔을 때 결제하세요.
> 단, 심사 대기 + 첫 등록 절차를 감안해 **출시 2~3주 전에는** 가입해두는 게 안전합니다.

---

# PART 1: Swift 문법 (JS와 1:1 비교)

완벽히 외울 필요 없습니다. 30분~1시간 훑고, 막히면 [PART 2 치트시트](#part-2-매핑-치트시트)로 돌아오세요.

## 1-1. 변수와 상수 ⚠️ (JS와 키워드가 겹쳐서 가장 헷갈리는 곳)

```javascript
// JavaScript
const name = "홍길동"       // 재할당 불가
let age = 25               // 재할당 가능
```

```swift
// Swift — ⚠️ let의 의미가 JS와 반대!
let name = "홍길동"         // ⚠️ JS의 const 역할 (재할당 불가)
var age = 25               // JS의 let 역할 (재할당 가능)
```

> 🚨 **Swift의 `let` = JS의 `const`.**
> 이것 하나만 머리에 박아두면 Swift 문법의 절반은 넘어간 겁니다.
> Xcode가 "이건 `let`으로 바꿀 수 있다"고 경고하면 그냥 따르세요.

## 1-2. 타입 시스템

```javascript
// JavaScript
let x = "hello"
x = 123            // OK
function add(a, b) { return a + b }
add("1", 2)        // "12"
```

```swift
// Swift — 타입 추론 + 컴파일 시점 체크
var x = "hello"    // String으로 추론
// x = 123         // ❌ 컴파일 에러

func add(a: Int, b: Int) -> Int {
    return a + b
}
```

**타입 변환은 자동으로 안 됩니다** (JS와 자주 부딪히는 지점):

```swift
let i = 10
// let d: Double = i          // ❌
let d = Double(i)             // ✅ 생성자로 변환

let s = "42"
let n = Int(s)                // Optional<Int> — 실패할 수 있으니까
let n2 = Int(s) ?? 0          // 실전에서 이 형태를 가장 많이 씀

// 숫자를 문자열로
let msg = "나이: \(i)"        // 문자열 보간
let str = String(i)
```

> ⚠️ **`Int`와 `Double`을 섞어 연산할 수 없습니다.**
> `let avg = total / count` 에서 total이 Double, count가 Int면 에러입니다.
> `total / Double(count)` 로 맞춰야 합니다. JS에서 아무 생각 없이 하던 것이라 자주 걸립니다.

## 1-3. 함수

```javascript
// JavaScript
function greet(name) { return "안녕, " + name }
const double = (x) => x * 2
function hello(name = "세계") { return "안녕, " + name }
```

```swift
// Swift
func greet(name: String) -> String {
    return "안녕, \(name)"        // 문자열 보간은 \()
}

func double(_ x: Int) -> Int { x * 2 }   // 한 줄이면 return 생략

func hello(name: String = "세계") -> String { "안녕, \(name)" }
```

### 인자 레이블 ⭐ (JS에 없어서 처음에 당황하는 문법)

```swift
// Swift 함수는 호출할 때 인자 이름을 반드시 씁니다
greet(name: "홍길동")            // ✅
// greet("홍길동")                // ❌ 에러

// 이름을 생략시키려면 _ 를 붙임
func double(_ x: Int) -> Int { x * 2 }
double(5)                        // ✅ 이름 없이 호출

// 외부용 이름과 내부용 이름을 다르게
func move(from source: String, to target: String) {
    print("\(source) → \(target)")   // 내부에선 source/target
}
move(from: "서울", to: "부산")        // 호출은 영어 문장처럼
```

> **왜 이렇게 만들었나**: 호출부만 읽어도 의미가 통하게 하려는 설계입니다.
> Apple 프레임워크가 전부 이 스타일이라 익숙해지면 문서 없이도 읽힙니다.

### 클로저 (JS의 화살표 함수)

```swift
// 전체 형태
let double = { (x: Int) -> Int in return x * 2 }

// 축약
let double: (Int) -> Int = { $0 * 2 }        // $0 = 첫 번째 인자

// 후행 클로저 — SwiftUI가 이렇게 생긴 이유
Button("클릭") {
    count += 1          // ← 마지막 매개변수인 action 클로저
}

// 여러 후행 클로저 (Swift 5.3+)
Button {
    count += 1
} label: {
    Text("클릭")
}
```

## 1-4. 조건문

```javascript
// JavaScript
if (score >= 90) { console.log("A") }
else if (score >= 80) { console.log("B") }
else { console.log("C") }
const grade = score >= 90 ? "A" : "B"
```

```swift
// Swift
if score >= 90 {                  // 괄호 () 생략 (써도 되지만 경고)
    print("A")
} else if score >= 80 {
    print("B")
} else {
    print("C")
}

let grade = score >= 90 ? "A" : "B"   // 삼항 연산자는 JS와 동일

// switch — break 자동, 패턴 매칭 강력
switch score {
case 90...100: print("A")         // 범위 매칭
case 80..<90:  print("B")
case let s where s < 0: print("잘못된 값: \(s)")
default:       print("C")
}
```

> ⚠️ **Swift의 `switch`는 모든 경우를 덮어야 합니다** (`default` 필수, 또는 완전 열거).
> JS처럼 일부만 쓰고 넘어갈 수 없습니다. 이 성질이 `enum`과 만나면 강력해집니다 (1-7 참고).

## 1-5. 반복문

```javascript
for (let i = 0; i < 5; i++) { console.log(i) }
const fruits = ["사과", "바나나", "딸기"]
for (const fruit of fruits) { console.log(fruit) }
fruits.forEach((fruit, index) => console.log(`${index}: ${fruit}`))
```

```swift
for i in 0..<5 { print(i) }       // 0,1,2,3,4  (..< = 미만)
for i in 0...4 { print(i) }       // 0,1,2,3,4  (... = 이하)
for i in stride(from: 0, to: 10, by: 2) { print(i) }   // 0,2,4,6,8

let fruits = ["사과", "바나나", "딸기"]
for fruit in fruits { print(fruit) }

for (index, fruit) in fruits.enumerated() {
    print("\(index): \(fruit)")
}
```

## 1-6. 컬렉션

```javascript
const nums = [1, 2, 3, 4, 5]
nums.map(x => x * 2)
nums.filter(x => x > 3)
nums.find(x => x > 3)
nums.reduce((sum, x) => sum + x, 0)
nums.includes(3)
nums.length
```

```swift
let nums = [1, 2, 3, 4, 5]

nums.map { $0 * 2 }                     // [2,4,6,8,10]
nums.filter { $0 > 3 }                  // [4,5]
nums.first { $0 > 3 }                   // Optional(4)
nums.reduce(0, +)                       // 15  (또는 nums.reduce(0) { $0 + $1 })
nums.contains(3)                        // true
nums.count                              // 5   (.length 아님!)

var arr = [1, 2, 3]                     // 변경하려면 var
arr.append(4)
arr.remove(at: 1)
arr.insert(0, at: 0)

let combined = arr1 + arr2
```

**JS에 없어서 유용한 것들:**

```swift
nums.sorted()                            // 정렬된 새 배열
nums.sorted { $0.age < $1.age }          // 커스텀 정렬
nums.compactMap { Int($0) }              // 변환 + nil 제거 (map + filter 한 번에) ⭐
nums.flatMap { $0 }                      // 중첩 배열 평탄화
Dictionary(grouping: users) { $0.city }  // groupBy
nums.min() / nums.max()
nums.prefix(3) / nums.suffix(3)
nums.allSatisfy { $0 > 0 }
Set(nums)                                // 중복 제거
```

> **`$0`** = 클로저의 첫 번째 인자. JS의 `x => x * 2`에서 `x`를 생략한 것과 같습니다.
> 중첩되면 `{ user in ... }` 처럼 이름을 붙이세요.

## 1-7. struct / class / enum ⭐ (Swift에서 제일 중요한 절)

```javascript
// JavaScript
const user = { name: "홍길동", age: 25 }

class User {
    constructor(name, age) { this.name = name; this.age = age }
    greet() { return `안녕, ${this.name}` }
}
```

```swift
// Swift — struct가 JS 객체에 가장 가까움 (기본으로 struct를 쓰세요)
struct User {
    let name: String
    var age: Int

    func greet() -> String { "안녕, \(name)" }
}

let user = User(name: "홍길동", age: 25)   // 멤버와이즈 생성자가 자동 생성됨
print(user.name)
```

### 값 타입 vs 참조 타입 — SwiftUI 버그의 근원

```swift
// struct = 값 타입 (복사됨) — JS엔 없는 개념
struct Point { var x: Int }
var a = Point(x: 1)
var b = a          // 복사본이 만들어짐
b.x = 99
print(a.x)         // 1  ← a는 안 바뀜

// class = 참조 타입 (JS 객체와 같음)
class Counter { var value = 0 }
let c1 = Counter()
let c2 = c1        // 같은 객체를 가리킴
c2.value = 99
print(c1.value)    // 99  ← 같이 바뀜
```

| | struct | class |
|---|---|---|
| 복사 동작 | 값 복사 | 참조 공유 |
| 상속 | 불가 | 가능 |
| `let`으로 선언하면 | 내부 프로퍼티도 못 바꿈 | 프로퍼티는 바꿀 수 있음 |
| SwiftUI에서 | **View, 데이터 모델** | ViewModel, 서비스 |

> **기본 규칙: 데이터는 struct, 상태를 들고 오래 사는 건 class.**
> SwiftUI의 `View`는 전부 struct입니다 — 매번 새로 만들어지고 버려지는 것이 전제입니다.
> "왜 View에 저장한 변수가 초기화되지?" 의 답이 여기 있습니다 (→ 그래서 `@State`가 필요).

**struct 안에서 자기 값을 바꾸려면 `mutating`:**

```swift
struct Counter {
    var value = 0
    mutating func increment() { value += 1 }   // mutating 없으면 컴파일 에러
}
```

### enum — 상태 표현의 표준

```swift
// 단순 열거
enum Status { case idle, loading, done }

// 연관값을 가진 열거 ⭐ — Kotlin의 sealed class에 해당
enum LoadState {
    case idle
    case loading
    case success(WeatherResponse)
    case failure(String)
}

// switch가 모든 케이스를 덮으면 default 없이도 컴파일됨
switch state {
case .idle:                Color.clear
case .loading:             ProgressView()
case .success(let data):   WeatherInfo(data)     // 값을 바로 꺼냄
case .failure(let message): Text(message)
}
```

> **왜 좋은가**: 나중에 `.empty` 케이스를 추가하면 그걸 처리 안 한 `switch`가 **전부 컴파일 에러**가 됩니다.
> JS의 switch에서 case를 빠뜨려 생기는 버그가 구조적으로 사라집니다.

### 프로토콜 (JS의 인터페이스/덕 타이핑)

```swift
protocol Greetable {
    var name: String { get }
    func greet() -> String
}

// 기본 구현도 줄 수 있음 (믹스인처럼)
extension Greetable {
    func greet() -> String { "안녕, \(name)" }
}

struct User: Greetable {
    let name: String       // greet()는 기본 구현을 그대로 씀
}
```

**실전에서 계속 만나는 프로토콜 3개:**

| 프로토콜 | 의미 | 어디서 쓰나 |
|---|---|---|
| `Identifiable` | `id` 프로퍼티가 있음 | `ForEach`, `List` (= React의 key) |
| `Codable` | JSON ↔ 객체 자동 변환 | 네트워크 응답 |
| `Hashable` | 해시 가능 (Set/Dictionary 키) | `NavigationPath`, 중복 제거 |

## 1-8. Optional (null 처리) ⭐

```javascript
// JavaScript
let name = null
console.log(name.length)      // ❌ 런타임 TypeError
console.log(name?.length)     // undefined
console.log(name ?? "이름 없음")
```

```swift
// Swift — nil 가능 여부가 타입의 일부
var name: String = "홍길동"
// name = nil                  // ❌ 컴파일 에러

var name2: String? = "홍길동"   // ? = Optional (nil 가능)
name2 = nil                    // ✅

print(name2?.count)            // ✅ nil이면 nil (JS의 ?. 와 동일)
print(name2 ?? "이름 없음")     // ✅ nil이면 기본값 (JS의 ?? 와 동일)
print(name2!.count)            // 🚨 nil이면 그 자리에서 크래시
```

### if let vs guard let — JS엔 없는 핵심 패턴

```swift
// if let: 값이 있을 때만 블록 실행. 없어도 함수는 계속 진행
func display(name: String?) {
    if let name {                    // Swift 5.7+ 축약형 (원래는 if let name = name)
        print("이름: \(name)")
    }
    print("끝")                       // nil이어도 실행됨
}

// guard let: 값이 없으면 즉시 종료 (early return)
func display(name: String?) {
    guard let name else {
        print("이름 없음")
        return                        // guard의 else는 반드시 스코프를 벗어나야 함
    }
    // 이 아래 전체에서 name은 String으로 확정
    print("이름: \(name)")
    print("길이: \(name.count)")
}
```

**언제 어느 걸?**
- `if let`: 값이 있을 때만 잠깐 처리하고 끝 (지역적)
- `guard let`: 함수 시작부 입력 검증, 없으면 진행 불가 (전역적) → **이쪽을 더 자주 씁니다**

```javascript
// JS로 비교하면
if (name) { console.log(name) }   // if let

if (!name) return                 // guard let
console.log(name)                 // 여기서 name 확정
```

> 🚨 **`!` (강제 언래핑)은 "여기서 크래시 나도 좋다"는 선언입니다.**
> 앱 크래시 원인 1위가 `Unexpectedly found nil while unwrapping an Optional value` 입니다.
> `guard let`, `??`, `if let` 중 하나로 거의 항상 대체할 수 있습니다.
> (예외: `@IBOutlet`, 테스트 코드, 리소스가 반드시 존재한다고 보장되는 경우)

## 1-9. 비동기 처리 — async/await ⭐

```javascript
// JavaScript
async function fetchData() {
    try {
        const res = await fetch(url)
        return await res.json()
    } catch (e) {
        console.log("에러:", e.message)
    }
}
```

```swift
// Swift — JS와 거의 동일!
func fetchData() async throws -> MyData {
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(MyData.self, from: data)
}

// 호출하는 쪽
func load() async {
    do {                                    // try-catch 대신 do-catch
        let result = try await fetchData()
        print(result)
    } catch {                               // error 변수가 자동으로 있음
        print("에러: \(error.localizedDescription)")
    }
}
```

> **`throws` + `try`**: JS는 아무 함수나 예외를 던질 수 있지만, Swift는 **던질 수 있는 함수에
> `throws`를 표시**하고 **호출할 때 `try`를 붙여야** 합니다. 어디서 실패할 수 있는지가 코드에 드러납니다.

### async 함수를 어디서 부르나

```swift
// ❌ 일반 함수에서 직접 호출 불가
func buttonTapped() {
    await fetchData()      // 에러: 'async' call in a function that does not support concurrency
}

// ✅ Task로 감싸기
func buttonTapped() {
    Task { await fetchData() }
}

// ✅ SwiftUI에서는 .task (= useEffect)
var body: some View {
    ContentView()
        .task {                        // 뷰가 나타나면 실행, 사라지면 자동 취소
            await viewModel.load()
        }
}
```

| | 언제 실행 | 취소 | JS 대응 |
|---|---|---|---|
| `.task { }` | 뷰 등장 시 | 뷰가 사라지면 **자동 취소** | `useEffect(() => {...}, [])` |
| `.task(id: value) { }` | value가 바뀔 때마다 | 재실행 시 이전 것 취소 | `useEffect(fn, [value])` |
| `.onAppear { }` | 뷰 등장 시 (동기) | 없음 | `useEffect` (동기 코드용) |
| `Task { }` | 즉시 | 수동 | `(async () => {})()` |

> **`.task`가 자동 취소해준다는 게 핵심 가치**입니다. 사용자가 화면을 빠르게 들어갔다 나가도
> 진행 중이던 네트워크 요청이 정리됩니다. JS의 fetch는 AbortController를 직접 써야 하는 부분입니다.

### @MainActor — UI는 메인 스레드에서

```swift
@MainActor                            // 이 클래스의 모든 코드는 메인 스레드에서 실행
@Observable
final class WeatherViewModel {
    var weather: WeatherResponse?

    func load(city: String) async {
        // 네트워크는 알아서 백그라운드에서 처리되고
        let result = try? await service.fetch(city: city)
        weather = result              // UI 상태 갱신은 메인 스레드에서 (@MainActor 덕분에 안전)
    }
}
```

> **JS와 큰 차이**: JS는 싱글 스레드라 이 고민이 없습니다. Swift는 여러 스레드에서 돌 수 있어
> **UI 상태를 백그라운드에서 바꾸면 크래시하거나 화면이 안 갱신**됩니다.
> **ViewModel 클래스에 `@MainActor`를 붙이는 걸 기본값으로** 삼으면 이 부류 문제가 대부분 사라집니다.

### Swift 6 동시성 (Strict Concurrency) — 미리 알아둘 것

Swift 6 언어 모드를 켜면 컴파일러가 데이터 경쟁을 전부 검사합니다.
`Sendable` 관련 경고/에러가 쏟아질 수 있는데, 학습 단계라면:

```
Build Settings → Swift Compiler - Language → Swift Language Version
→ 학습 중에는 Swift 5 모드 유지 + 경고만 켜두기
→ 익숙해지면 Swift 6 모드로 전환
```

> 이게 뭔지 몰라도 앱은 만들 수 있습니다. 다만 **"Sendable"이라는 단어가 나오면
> 이 얘기구나** 정도만 알아두세요.

## 1-10. 메모리 관리 (ARC)와 [weak self] ⭐

JS는 가비지 컬렉터가 알아서 해주지만, Swift는 **참조 카운팅(ARC)** 을 씁니다.
대부분 신경 안 써도 되지만 **순환 참조 하나**만은 알아야 합니다.

```swift
class ViewModel {
    var onComplete: (() -> Void)?

    func setup() {
        onComplete = {
            self.doSomething()      // ⚠️ self를 강하게 붙잡음 → 순환 참조 → 메모리 누수
        }
    }

    func setupCorrectly() {
        onComplete = { [weak self] in
            guard let self else { return }
            self.doSomething()      // ✅ 약한 참조 — 객체가 해제되면 nil
        }
    }
}
```

> **언제 `[weak self]`가 필요한가**: 클로저를 **오래 보관**할 때
> (프로퍼티에 저장, 타이머, 알림 구독, 콜백 등록).
> `Task { }`, `.task { }`, `map/filter` 같은 즉시 실행 클로저는 필요 없습니다.
>
> **증상**: 화면을 나갔는데 로그가 계속 찍힌다 / 메모리가 계속 증가한다
> → Xcode의 **Debug Memory Graph** 버튼으로 확인할 수 있습니다.

## 1-11. 문법 연습

```
Swift Playgrounds 앱 (Mac/iPad, App Store 무료)
→ 코드를 치면 우측에 결과가 즉시 나옴. 문법 익히기에 최적

브라우저: https://swiftfiddle.com

Apple 공식 A Swift Tour:
https://docs.swift.org/swift-book/documentation/the-swift-programming-language/guidedtour
→ 언어 전체를 한 페이지로. 1시간이면 훑습니다
```

---

# PART 1.5: Swift 심화

PART 1의 문법으로 앱을 시작할 수 있지만, 아래 요소는 모델·네트워크·SwiftUI 코드를 읽을 때
곧바로 만납니다. JS와 이름이 같아 보여도 동작이 다른 부분을 중심으로 익히세요.

## 1.5-1. 문자열 보간과 문자열 메서드 심화

문자열은 화면 표시뿐 아니라 검색어 정리, 입력 검증, URL 구성에 계속 쓰입니다.
JS의 템플릿 리터럴과 비슷하지만 Swift의 `String`은 유니코드 문자 단위라 인덱싱 방식이 다릅니다.

```swift
let title = "  달빛 아래의 도서관  "
let price = 18_500

let trimmed = title.trimmingCharacters(in: .whitespacesAndNewlines)
let label = "\(trimmed) · \(price.formatted(.currency(code: "KRW")))"

trimmed.lowercased()
trimmed.uppercased()
trimmed.contains("도서관")
trimmed.hasPrefix("달빛")
trimmed.replacingOccurrences(of: "도서관", with: "서점")

let tags = "소설,여행,야간".split(separator: ",").map(String.init)
let summary = tags.joined(separator: " · ")
```

JS의 `text[0]`처럼 정수로 접근할 수는 없습니다. 이모지 하나가 여러 유니코드 스칼라로
이루어질 수 있어 Swift가 잘못된 위치를 허용하지 않기 때문입니다.

```swift
let word = "📚책"
let first = word.first                         // Character? = "📚"
let secondIndex = word.index(after: word.startIndex)
let second = word[secondIndex]                 // Character = "책"
let safePrefix = String(word.prefix(1))        // "📚"
```

> ⭐ 숫자·날짜 표시는 문자열을 직접 이어 붙이기보다 `formatted()`를 쓰세요.
> 사용자 지역 설정에 맞는 통화 기호·구분자·날짜 순서를 자동으로 적용합니다.
>
> ⚠️ `String.count`는 사람이 보는 문자 수에 가깝고 내부 바이트 수가 아닙니다.
> 대용량 텍스트에서 반복 인덱싱하면 비쌀 수 있으니 배열처럼 무작정 순회하지 마세요.

## 1.5-2. 튜플과 여러 반환값

튜플은 관련된 값을 잠깐 묶되 별도 모델 타입까지 만들 필요가 없을 때 씁니다.
JS의 배열 구조 분해와 닮았지만, 위치뿐 아니라 이름으로도 접근할 수 있습니다.

```swift
func expenseSummary(_ amounts: [Int]) -> (total: Int, average: Double) {
    let total = amounts.reduce(0, +)
    let average = amounts.isEmpty ? 0 : Double(total) / Double(amounts.count)
    return (total, average)
}

let result = expenseSummary([12_000, 8_500, 21_000])
print(result.total)

let (total, average) = expenseSummary([12_000, 8_500, 21_000])
print("합계 \(total), 평균 \(average)")

let book = (title: "유리 정원", pages: 320)
switch book {
case (_, let pages) where pages >= 300:
    print("긴 책")
default:
    print("가볍게 읽을 책")
}
```

JS에서는 `{ total, average }` 객체를 반환하는 경우가 많습니다. Swift에서도 API 경계를
넘거나 오래 저장할 값이면 이름 있는 `struct`가 더 낫고, 함수 내부의 임시 결과면 튜플이 간결합니다.

```swift
struct ExpenseSummary: Codable {
    let total: Int
    let average: Double
}
```

> ⚠️ 튜플은 `Codable`을 자동 채택할 수 없고 프로토콜 준수에도 불리합니다.
> 화면 모델·네트워크 응답·저장 데이터에는 `struct`, 짧은 지역 묶음에는 튜플을 쓰세요.

## 1.5-3. 클로저: 후행 문법, 함수 전달, 캡처

클로저는 동작을 값처럼 전달하려고 존재합니다. JS의 콜백·화살표 함수와 같은 자리에서 쓰며,
SwiftUI의 `Button`, `ForEach`, 애니메이션 완료 처리도 모두 클로저입니다.

```swift
struct Book {
    let title: String
    let rating: Double
}

let books = [
    Book(title: "파도 지도", rating: 4.7),
    Book(title: "작은 행성", rating: 4.2)
]

func selectBooks(from books: [Book], rule: (Book) -> Bool) -> [Book] {
    books.filter(rule)
}

let favorites = selectBooks(from: books) { book in   // 마지막 인자 → 후행 클로저
    book.rating >= 4.5
}
```

클로저는 바깥 값을 캡처합니다. JS 클로저와 같은 개념이지만 값 타입은 캡처 시점과
변경 방식에 주의하고, 클래스 인스턴스를 오래 잡으면 ARC 순환 참조가 생길 수 있습니다.

```swift
func makeReadingCounter() -> () -> Int {
    var count = 0
    return {
        count += 1                 // count의 저장 공간을 캡처해 호출 사이에 유지
        return count
    }
}

let nextReading = makeReadingCounter()
nextReading()                      // 1
nextReading()                      // 2

final class DownloadQueue {
    var onFinish: (() -> Void)?
    func connect() {
        onFinish = { [weak self] in self?.clearTemporaryFiles() }
    }
    func clearTemporaryFiles() { }
}
```

> ⚠️ 모든 클로저에 습관적으로 `[weak self]`를 붙이지 마세요. `map`처럼 즉시 실행되는
> 클로저에는 불필요합니다. 객체가 클로저를 프로퍼티로 오래 보관해 서로 붙잡을 때 필요합니다.

## 1.5-4. `throws`, `do-catch`, `Result`

실패를 정상 흐름과 분리하면 호출자가 오류를 무시하지 않게 할 수 있습니다. JS의 `throw`와 달리
Swift는 함수 선언에 `throws`, 호출부에 `try`가 보여서 실패 가능성이 타입 수준에 드러납니다.

```swift
enum RecipeError: LocalizedError {
    case emptyTitle
    case invalidServings

    var errorDescription: String? {
        switch self {
        case .emptyTitle: "레시피 이름을 입력하세요."
        case .invalidServings: "인원은 1명 이상이어야 합니다."
        }
    }
}

func makeRecipe(title: String, servings: Int) throws -> String {
    guard !title.trimmingCharacters(in: .whitespaces).isEmpty else {
        throw RecipeError.emptyTitle
    }
    guard servings > 0 else { throw RecipeError.invalidServings }
    return "\(title) · \(servings)인분"
}

do {
    let recipe = try makeRecipe(title: "토마토 수프", servings: 2)
    print(recipe)
} catch RecipeError.invalidServings {
    print("인원 수를 다시 확인하세요.")
} catch {
    print(error.localizedDescription)
}
```

`Result<Success, Failure>`는 성공/실패를 값으로 저장하거나 콜백으로 전달할 때 유용합니다.

```swift
let saved: Result<String, RecipeError> = Result {
    try makeRecipe(title: "버섯 리조또", servings: 3)
}

let displayName = (try? saved.get()) ?? "저장 실패"   // try?는 실패를 nil로 바꿈
```

> ⚠️ `try?`는 오류의 이유를 버립니다. 값이 없어도 괜찮은 보조 기능에만 쓰고,
> 사용자에게 실패 원인을 알려야 하는 저장·결제·네트워크 작업은 `do-catch`로 처리하세요.

## 1.5-5. 프로퍼티, 접근 제어, `static`

타입이 스스로 유효한 상태를 지키게 만들면 UI 여러 곳에서 검증 로직을 반복하지 않아도 됩니다.
JS의 `get`, private field, 클래스 정적 멤버에 각각 계산 프로퍼티, 접근 제어, `static`이 대응합니다.

```swift
struct TravelBudget {
    static let maximumDays = 90                 // 모든 인스턴스가 공유

    let destination: String
    private(set) var spent = 0                  // 외부 읽기 가능, 쓰기는 타입 내부만
    var limit: Int {
        didSet { limit = max(0, limit) }        // 값 변경 직후 보정
    }

    var remaining: Int { max(0, limit - spent) } // 계산 프로퍼티: 저장하지 않음

    mutating func record(_ amount: Int) {
        guard amount > 0 else { return }
        spent += amount
    }
}

var budget = TravelBudget(destination: "타이베이", limit: 500_000)
budget.record(42_000)
print(budget.remaining)
```

| 키워드 | 범위 | JS 감각 |
|---|---|---|
| `private` | 선언 타입·같은 파일의 extension 내부 | `#field`보다 엄격한 캡슐화 |
| `fileprivate` | 같은 파일 | 모듈 패턴의 파일 내부 값 |
| `internal` | 같은 모듈, 기본값 | export하지 않은 패키지 내부 API |
| `public` | 다른 모듈에서도 사용 | `export` |

> ⭐ 앱 코드에서는 우선 `private`로 닫고 필요한 만큼만 여세요. `private(set)`은
> ViewModel 상태를 화면에서는 읽되 임의 수정은 막고 싶을 때 특히 유용합니다.
>
> ⚠️ 프로퍼티 옵저버 `didSet` 안에서 무거운 네트워크 요청을 시작하지 마세요.
> 값 대입만으로 숨은 부수 효과가 생깁니다. 그런 작업은 이름 있는 메서드로 드러내세요.

## 1.5-6. 클래스 상속, 초기화, `deinit`

상속은 기존 클래스의 동작을 특수화할 때 쓰지만, SwiftUI 앱 데이터는 대체로 `struct`와
프로토콜 조합이 더 단순합니다. UIKit 프레임워크 타입을 다룰 때 상속을 자주 만납니다.

```swift
class TripService {
    let region: String

    init(region: String) {
        self.region = region
    }

    func itineraryTitle() -> String {
        "\(region) 여행"
    }

    deinit {
        print("TripService 연결 정리")
    }
}

final class WeekendTripService: TripService {   // final = 더 이상 상속 불가
    let nights: Int

    init(region: String, nights: Int) {
        self.nights = nights                    // 자식 프로퍼티 먼저 초기화
        super.init(region: region)              // 그 다음 부모 초기화
    }

    override func itineraryTitle() -> String {
        "\(region) · \(nights)박 일정"
    }
}
```

JS처럼 클래스는 참조 타입이고 `let` 인스턴스의 `var` 프로퍼티도 바꿀 수 있습니다.
`deinit`은 마지막 강한 참조가 사라질 때 한 번 호출되어 구독·관찰자 같은 자원을 정리합니다.

> ⚠️ `deinit`이 호출되지 않는다면 먼저 순환 참조를 의심하세요. 단, 앱 종료 시점에는
> 모든 객체의 `deinit` 실행이 보장되지 않으므로 중요한 데이터 저장 장소로 쓰면 안 됩니다.

## 1.5-7. `extension`과 프로토콜 extension

extension은 원래 선언을 수정하지 않고 메서드·계산 프로퍼티·프로토콜 준수를 추가합니다.
JS의 prototype 확장과 비슷해 보이지만 컴파일 시점에 타입 검사되고 저장 프로퍼티는 추가할 수 없습니다.

```swift
struct BookRecord {
    let title: String
    let finishedPages: Int
    let totalPages: Int
}

extension BookRecord {
    var progress: Double {
        guard totalPages > 0 else { return 0 }
        return Double(finishedPages) / Double(totalPages)
    }
}

protocol Summarizable {
    var title: String { get }
    func summary() -> String
}

extension Summarizable {
    func summary() -> String { "제목: \(title)" }     // 기본 구현
}

extension BookRecord: Summarizable { }                // 준수를 별도 파일에 정리 가능

extension Array where Element == BookRecord {
    var averageProgress: Double {
        isEmpty ? 0 : map(\.progress).reduce(0, +) / Double(count)
    }
}
```

프로토콜 extension은 여러 타입이 공유할 기본 동작을 제공해 상속 없이 기능을 조합하게 해줍니다.
표준 라이브러리의 `Collection`, SwiftUI의 `View` 수정자도 이 설계를 폭넓게 사용합니다.

> ⚠️ 범용 타입에 의미가 모호한 extension을 마구 추가하면 어디서 온 API인지 찾기 어렵습니다.
> 도메인이 분명한 이름을 쓰고, 짧은 문법 설탕보다 실제 중복 제거에 집중하세요.

## 1.5-8. 옵셔널 체이닝과 nil 병합 심화

옵셔널 체이닝은 중간 값 하나라도 `nil`이면 전체 표현식을 `nil`로 끝냅니다.
JS의 `?.`와 거의 같고, `??`는 최종 기본값을 제공합니다.

```swift
struct Author { let nickname: String? }
struct TravelBook { let author: Author?; let chapters: [String] }

let book: TravelBook? = TravelBook(
    author: Author(nickname: nil),
    chapters: ["출발", "골목", "귀환"]
)

let nickname = book?.author?.nickname?.uppercased() ?? "익명 작가"
let firstChapter = book?.chapters.first ?? "목차 없음"
let chapterCount = book?.chapters.count ?? 0
```

옵셔널 메서드 호출도 체인에 포함됩니다. 값이 없으면 호출 자체가 생략됩니다.

```swift
var notes: [String]? = []
notes?.append("야시장 방문")            // notes가 nil이면 아무 일도 없음

let primary: String? = nil
let backup: String? = "임시 표지"
let cover = primary ?? backup ?? "기본 표지"  // 왼쪽부터 첫 non-nil
```

> ⚠️ `Int??`처럼 옵셔널이 중첩될 수 있습니다. 예를 들어 딕셔너리 조회 결과 자체가
> 옵셔널 값을 담으면 “키 없음”과 “키는 있지만 nil”이 구분됩니다. 대부분은 모델을 단순화하거나
> `flatMap`으로 한 단계 평탄화하는 편이 읽기 쉽습니다.

---

# PART 2: 매핑 치트시트

앱 만들면서 계속 돌아올 페이지입니다. 외우지 말고 북마크하세요.

## 언어 비교

| 개념 | JavaScript | Swift |
|---|---|---|
| 상수 | `const x = 1` | `let x = 1` ⚠️ |
| 변수 | `let x = 1` | `var x = 1` |
| 함수 | `function add(a, b)` | `func add(a: Int, b: Int) -> Int` |
| 화살표 함수 | `(x) => x * 2` | `{ x in x * 2 }` 또는 `{ $0 * 2 }` |
| 옵셔널 체이닝 | `x?.prop` | `x?.prop` (동일) |
| null 병합 | `x ?? "기본"` | `x ?? "기본"` (동일) |
| 비동기 | `async` / `await` | `async` / `await` (거의 동일) |
| 예외 처리 | `try/catch` | `do/catch` + `try` |
| 문자열 보간 | `` `Hello ${name}` `` | `"Hello \(name)"` |
| 배열 길이 | `arr.length` | `arr.count` |
| 배열 추가 | `arr.push(x)` | `arr.append(x)` |
| 스프레드 | `[...a, ...b]` | `a + b` |
| 객체 복사+수정 | `{ ...o, age: 26 }` | `var copy = o; copy.age = 26` |
| 출력 | `console.log()` | `print()` / `Logger()` |
| 타입 검사 | `typeof x === 'string'` | `x is String` |
| 클래스 인스턴스 | `new User()` | `User()` (new 없음) |

## React ↔ SwiftUI 매핑

| React / JS 생태계 | iOS |
|---|---|
| 컴포넌트 함수 | `struct: View` + `var body` |
| `useState()` | `@State` |
| props (읽기 전용) | 그냥 `let` 프로퍼티 |
| props (양방향) | `@Binding` + 호출부의 `$` |
| `useEffect(fn, [])` | `.task { }` / `.onAppear { }` |
| `useEffect(fn, [dep])` | `.task(id: dep) { }` / `.onChange(of: dep) { }` |
| `useMemo` | 계산 프로퍼티 또는 `@State` 캐싱 |
| Context | `@Environment` / `.environment()` |
| Redux / Zustand | `@Observable` 클래스 |
| React Router | `NavigationStack` |
| npm | Swift Package Manager |
| fetch / axios | `URLSession` |
| localStorage | `UserDefaults` / `@AppStorage` |
| IndexedDB | SwiftData (또는 Core Data) |
| Storybook | `#Preview` |
| `console.log` | `Logger().debug()` |
| Jest | Swift Testing / XCTest |
| Testing Library | XCUITest |

## CSS ↔ SwiftUI

| CSS | SwiftUI |
|---|---|
| `display:flex; flex-direction:column` | `VStack { }` |
| `display:flex; flex-direction:row` | `HStack { }` |
| `position:relative` + 겹치기 | `ZStack { }` |
| `width: 100%` | `.frame(maxWidth: .infinity)` |
| `height: 100vh` | `.frame(maxHeight: .infinity)` |
| `flex: 1` | `Spacer()` 또는 `.frame(maxWidth: .infinity)` |
| `padding: 16px` | `.padding(16)` (숫자 생략 시 시스템 기본값) |
| `margin` | 부모의 `spacing:` 또는 `Spacer()` |
| `gap: 8px` | `VStack(spacing: 8)` |
| `justify-content` | `VStack`은 `Spacer()`로 조절 / `.frame(alignment:)` |
| `align-items` | `VStack(alignment: .leading)` |
| `border-radius: 8px` | `.clipShape(RoundedRectangle(cornerRadius: 8))` |
| `background: red` | `.background(.red)` |
| `overflow: scroll` | `ScrollView { }` |
| `arr.map(x => <Item/>)` | `ForEach(arr) { }` |
| `onClick` | `Button { } label: { }` / `.onTapGesture { }` |
| `env(safe-area-inset-*)` | **기본으로 적용됨** (`.ignoresSafeArea()`로 해제) |
| `object-fit: cover` | `.scaledToFill()` + `.clipped()` |

> ⚠️ **Modifier는 순서가 결과를 바꿉니다.**
> `.padding().background(.red)` → 패딩 **포함** 영역이 빨강
> `.background(.red).padding()` → 빨강 **바깥**에 여백
> CSS와 달리 위에서 아래로 순서대로 감싸는 구조입니다. 레이아웃이 이상하면 제일 먼저 의심할 곳.

## 상태 프로퍼티 래퍼 총정리 ⭐

SwiftUI 입문자가 가장 헷갈리는 부분입니다. **이 표 하나만 제대로 알면 절반은 해결됩니다.**

| 래퍼 | 무엇을 위한 것 | React 대응 | 예시 |
|---|---|---|---|
| `@State` | 이 뷰가 **소유**하는 상태 | `useState` | `@State private var count = 0` |
| `@Binding` | **부모의 상태를 빌려옴** (읽기+쓰기) | `value` + `onChange` props | `@Binding var text: String` |
| `@Observable` (클래스에) | 관찰 가능한 객체 만들기 | Zustand store 정의 | `@Observable class VM { }` |
| `@State` (+ @Observable 객체) | 그 객체를 뷰가 소유 | `useRef(new Store())` | `@State private var vm = VM()` |
| `@Bindable` | @Observable 객체 프로퍼티에 `$` 쓰기 | — | `@Bindable var vm: VM` |
| `@Environment` | 상위에서 주입된 값 | `useContext` | `@Environment(\.dismiss) var dismiss` |
| `@AppStorage` | UserDefaults 자동 연동 | localStorage 훅 | `@AppStorage("dark") var dark = false` |
| `@SceneStorage` | 앱 재시작 시 화면 상태 복원 | — | `@SceneStorage("draft") var draft = ""` |

<details>
<summary>구버전 래퍼 (@ObservedObject / @StateObject / @Published) — 기존 코드에서 계속 봅니다</summary>

iOS 17에서 `@Observable` 매크로가 나오기 전에는 이렇게 썼습니다:

```swift
// 구: ObservableObject 프로토콜 + @Published
class OldViewModel: ObservableObject {
    @Published var count = 0
}
struct OldView: View {
    @StateObject private var vm = OldViewModel()      // 뷰가 소유
    // @ObservedObject var vm: OldViewModel           // 부모에게서 받음
}

// 신: @Observable 매크로 (iOS 17+)
@Observable
final class NewViewModel {
    var count = 0                                      // @Published 불필요
}
struct NewView: View {
    @State private var vm = NewViewModel()             // @State로 통일
}
```

**신규 코드는 `@Observable`을 쓰세요.** 더 간단하고 성능도 좋습니다
(실제로 읽은 프로퍼티만 추적해서 불필요한 재렌더링이 줄어듭니다).
단 **인터넷 튜토리얼 대부분이 아직 구버전**이라, 둘 다 읽을 줄은 알아야 합니다.
</details>

---

# PART 3: 샘플 앱 만들기

카운터 → 상태관리 → 할 일 목록 → 날씨(API) → 메모(DB) 순으로 난이도가 올라갑니다.

## STEP 1: Hello World — 첫 화면과 Preview

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
                .font(.title)                    // 시스템 폰트 스타일 (Dynamic Type 자동 대응)
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

// 💡 #Preview = 빌드/실행 없이 우측 캔버스에서 실시간 렌더링
// SwiftUI 학습 속도를 좌우하는 기능. 화면 만들 때마다 붙이세요
#Preview {
    ContentView()
}

// 여러 조건을 한 번에 보기
#Preview("다크모드") {
    ContentView().preferredColorScheme(.dark)
}
#Preview("큰 글씨") {
    ContentView().environment(\.dynamicTypeSize, .accessibility3)
}
```

### `some View` 가 뭔가

```swift
var body: some View { ... }
//         ↑ "View 프로토콜을 따르는 어떤 구체 타입" (불투명 반환 타입)
```

내부적으로 `VStack<TupleView<(Text, Text, Button)>>` 같은 복잡한 타입이 만들어지는데,
그걸 다 쓰기 싫으니 `some View`로 줄인 것입니다. **깊이 이해할 필요 없고,
`body`는 항상 `some View`라고 외우면 됩니다.**

### `@State private var` 를 뜯어보기

```swift
@State private var count = 0
// ↑ 값이 바뀌면 body를 다시 실행하라고 SwiftUI에 알림
//        ↑ private 권장: 이 뷰만 이 상태를 소유한다는 뜻
```

> **View는 struct(값 타입)라 매번 새로 만들어집니다.** 그래서 그냥 `var count = 0`으로 두면
> 값이 유지되지 않습니다. `@State`가 값을 뷰 바깥의 저장소에 보관해주는 역할입니다.
> React 함수 컴포넌트가 매번 실행되는데 `useState` 값은 유지되는 것과 정확히 같은 구조입니다.

### SafeArea

SwiftUI는 **기본적으로 안전 영역(노치·홈 인디케이터 제외) 안쪽에만 그립니다.**
따로 신경 쓸 게 없는 게 기본값입니다.

```swift
.ignoresSafeArea()                        // 전체 화면으로 확장 (배경 이미지 등)
.ignoresSafeArea(edges: .bottom)          // 아래쪽만
.ignoresSafeArea(.keyboard)               // 키보드에 밀리지 않게
```

> **Android와 정반대**입니다. Android는 전체를 그린 뒤 피해야 하고, iOS는 안전 영역만
> 그리다가 필요하면 넓힙니다. 두 트랙을 같이 하면 여기서 헷갈립니다.

---

## STEP 1.5: 상태 관리 제대로 ⭐ (React 개발자가 가장 자주 다치는 곳)

STEP 2로 가기 전에 이것만 확실히 하면 이후가 훨씬 쉽습니다.

### ① @State vs @Binding — 부모/자식 상태 공유

```swift
// 부모: 상태를 소유
struct ParentView: View {
    @State private var text = ""

    var body: some View {
        VStack {
            SearchField(text: $text)     // $ = 바인딩 전달 (읽기+쓰기 권한을 넘김)
            Text("입력: \(text)")
        }
    }
}

// 자식: 부모의 상태를 빌려서 수정
struct SearchField: View {
    @Binding var text: String            // @State 아님!

    var body: some View {
        TextField("검색", text: $text)    // 여기서도 $
    }
}
```

| | 의미 | React 대응 |
|---|---|---|
| `text` | 값 자체 (읽기) | `props.value` |
| `$text` | 바인딩 (읽기+쓰기 권한) | `props.value` + `props.onChange` 묶음 |
| `_text` | 저장소 자체 (거의 안 씀) | — |

> **`$`를 언제 붙이나**: TextField, Toggle, Slider처럼 **값을 되돌려주는** 컴포넌트에 넘길 때.
> `Text("\(count)")`처럼 읽기만 하면 `$` 없이 그냥 값을 넘깁니다.

### ② 상태를 어디에 둘 것인가

```swift
// ❌ 상태를 안에 가둔 컴포넌트 — 재사용도 Preview도 어려움
struct Counter: View {
    @State private var count = 0
    var body: some View { Button("\(count)") { count += 1 } }
}

// ✅ 상태를 밖으로 (= React의 controlled component)
struct Counter: View {
    let count: Int
    let onIncrement: () -> Void
    var body: some View { Button("\(count)", action: onIncrement) }
}
```

> **규칙**: 상태는 그 상태를 읽는 모든 뷰의 **가장 가까운 공통 부모**에.
> React에서 배운 그대로입니다. 값은 아래로, 이벤트는 위로.

### ③ @Observable 클래스 (화면 상태가 복잡해질 때)

```swift
@MainActor
@Observable
final class TodoStore {
    var todos: [Todo] = []
    var filter: Filter = .all

    // 계산 프로퍼티 = useMemo 대응
    var visible: [Todo] {
        switch filter {
        case .all:    return todos
        case .done:   return todos.filter(\.isDone)
        case .active: return todos.filter { !$0.isDone }
        }
    }

    func add(_ title: String) {
        todos.append(Todo(title: title))
    }
}

struct TodoScreen: View {
    @State private var store = TodoStore()      // 뷰가 소유 (@StateObject 아님, iOS 17+)

    var body: some View {
        List(store.visible) { todo in Text(todo.title) }
    }
}
```

**@Observable 객체의 프로퍼티에 `$`를 쓰려면 `@Bindable`:**

```swift
struct FilterPicker: View {
    @Bindable var store: TodoStore           // @Observable 객체를 받을 때

    var body: some View {
        Picker("필터", selection: $store.filter) { ... }   // $ 사용 가능
    }
}
```

### ④ 값을 영구 저장하기

```swift
// UserDefaults 자동 연동 — 앱을 껐다 켜도 유지 (localStorage 대응)
@AppStorage("isDarkMode") private var isDarkMode = false

// 앱이 시스템에 의해 종료됐다 복원될 때 화면 상태 복원
@SceneStorage("draftText") private var draftText = ""
```

| | 리렌더 | 화면 회전 | 앱 재시작 |
|---|---|---|---|
| 그냥 `var` | 날아감 | 날아감 | 날아감 |
| `@State` | 유지 | 유지 | 날아감 |
| `@SceneStorage` | 유지 | 유지 | 유지(복원 시) |
| `@AppStorage` | 유지 | 유지 | **유지** |
| SwiftData | 유지 | 유지 | **유지** |

> **Android와 다른 점**: iOS는 화면 회전 시 뷰를 파괴하지 않아서 `@State`가 유지됩니다.
> Android 개발자가 iOS로 오면 이 부분이 훨씬 편하게 느껴집니다.

---

## STEP 2: 할 일 목록 — List, 입력, CRUD

```swift
// Models/Todo.swift
// JS: { id: crypto.randomUUID(), title: "할 일", isDone: false }
struct Todo: Identifiable {          // Identifiable = React의 key를 자동 제공
    let id = UUID()
    var title: String
    var isDone: Bool = false
}
```

```swift
// Views/TodoView.swift
import SwiftUI

struct TodoView: View {
    @State private var todos: [Todo] = []
    @State private var inputText = ""
    @FocusState private var isInputFocused: Bool      // 키보드 포커스 제어

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // ── 입력 영역 ──
                HStack {
                    TextField("할 일 입력…", text: $inputText)
                        .textFieldStyle(.roundedBorder)
                        .focused($isInputFocused)
                        .submitLabel(.done)
                        .onSubmit(addTodo)            // 키보드 완료 버튼

                    Button("추가", action: addTodo)
                        .buttonStyle(.borderedProminent)
                        .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty)
                }
                .padding()

                // ── 리스트 ──
                if todos.isEmpty {
                    // 빈 상태 — iOS 17+ 표준 컴포넌트
                    ContentUnavailableView(
                        "할 일이 없습니다",
                        systemImage: "checklist",
                        description: Text("위에서 새 할 일을 추가해보세요.")
                    )
                } else {
                    List {
                        // JS: {todos.map(todo => <li>...</li>)}
                        ForEach($todos) { $todo in       // $todos = 각 항목을 바인딩으로
                            HStack {
                                Button {
                                    todo.isDone.toggle()   // 바인딩이라 직접 수정 가능
                                } label: {
                                    Image(systemName: todo.isDone
                                          ? "checkmark.circle.fill" : "circle")
                                        .foregroundStyle(todo.isDone ? .blue : .secondary)
                                }
                                .buttonStyle(.plain)

                                Text(todo.title)
                                    .strikethrough(todo.isDone)
                                    .foregroundStyle(todo.isDone ? .secondary : .primary)

                                Spacer()
                            }
                            // 스크린리더 대응: 행 전체를 하나로 읽히게
                            .accessibilityElement(children: .combine)
                            .accessibilityAddTraits(todo.isDone ? .isSelected : [])
                        }
                        // 왼쪽 스와이프로 삭제 (iOS 기본 UX — 별도 삭제 버튼이 필요 없습니다)
                        .onDelete { todos.remove(atOffsets: $0) }
                        // 길게 눌러 순서 변경
                        .onMove { todos.move(fromOffsets: $0, toOffset: $1) }
                    }
                }
            }
            .navigationTitle("할 일 목록")
            .toolbar { EditButton() }        // 편집 모드 토글 (삭제/이동 UI)
        }
    }

    private func addTodo() {
        let trimmed = inputText.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        todos.append(Todo(title: trimmed))
        inputText = ""
    }
}
```

### iOS만의 리스트 관용구

| 기능 | 코드 | 비고 |
|---|---|---|
| 스와이프 삭제 | `.onDelete { }` | iOS 사용자가 **기대하는** 동작. 꼭 넣으세요 |
| 커스텀 스와이프 | `.swipeActions { Button(...) }` | 좌/우, 여러 개 가능 |
| 순서 변경 | `.onMove { }` + `EditButton()` | |
| 당겨서 새로고침 | `.refreshable { await load() }` | 한 줄로 끝 |
| 검색 | `.searchable(text: $query)` | 네비게이션 바에 검색창 자동 생성 |

```swift
List { ... }
    .refreshable { await viewModel.reload() }    // 당겨서 새로고침
    .searchable(text: $query, prompt: "할 일 검색")
```

> **이 4개가 "iOS 앱답다"는 인상의 8할입니다.** 각각 한 줄이니 반드시 넣으세요.
> RN이나 웹에서 직접 구현하려면 꽤 품이 드는 것들입니다.

### 문자열 리소스 (String Catalog)

```swift
Text("할 일 목록")     // 그냥 쓰면 됩니다
```

Xcode에서 **File → New → File → String Catalog** (`Localizable.xcstrings`)를 만들면,
빌드할 때 코드 안의 문자열이 **자동으로 수집**됩니다. Android처럼 미리 키를 만들 필요가 없습니다.

```swift
// 인자가 있는 문자열
Text("\(count)개의 할 일")

// 번역가를 위한 설명 추가
Text("완료", comment: "할 일을 완료 처리하는 버튼")
```

> **iOS의 다국어는 Android보다 훨씬 편합니다.** 코드는 그대로 두고 String Catalog에서
> 언어만 추가하면 됩니다. 나중에 영어판을 만들 계획이면 **지금 아무것도 안 해도 됩니다.**

---

## STEP 3: 날씨 앱 — API 통신, ViewModel, 네비게이션

### 사전 준비: API 키

```
1. https://openweathermap.org 회원가입 → API Keys에서 키 복사
2. ⚠️ 코드에 하드코딩하지 말고 아래 방법으로
```

```swift
// Config.swift  (⚠️ .gitignore에 추가)
enum Config {
    static let weatherAPIKey = "여기에_키"
}
```

더 나은 방법 — `.xcconfig` 파일 사용:
```
// Secrets.xcconfig  (gitignore)
WEATHER_API_KEY = abc123
```
```
Info.plist에 추가: WEATHER_API_KEY = $(WEATHER_API_KEY)
```
```swift
let key = Bundle.main.infoDictionary?["WEATHER_API_KEY"] as? String ?? ""
```

> ⚠️ **어느 방법도 완벽한 보안은 아닙니다.** `.ipa`를 뜯으면 문자열이 보입니다.
> 과금되는 API는 **반드시 서버를 거쳐서** 호출하세요. 학습용 무료 티어라면 위로 충분합니다
> (최소한 GitHub에 유출되진 않습니다).

### 네트워크 레이어

```swift
// Services/WeatherService.swift
import Foundation

// Codable = JSON.parse() 자동화 ⭐ 별도 라이브러리 불필요
struct WeatherResponse: Codable {
    let main: Main
    let weather: [Weather]
    let name: String
}
struct Main: Codable {
    let temp: Double
    let humidity: Int
    let feelsLike: Double        // JSON은 feels_like — 아래 키 전략으로 자동 변환
}
struct Weather: Codable {
    let description: String
    let icon: String
}

// 에러를 타입으로 정의 (사용자에게 보여줄 메시지를 여기서 결정)
enum WeatherError: LocalizedError {
    case cityNotFound
    case network
    case server(Int)

    var errorDescription: String? {
        switch self {
        case .cityNotFound: "도시를 찾을 수 없습니다"
        case .network:      "네트워크에 연결할 수 없습니다"
        case .server(let code): "서버 오류 (\(code))"
        }
    }
}

struct WeatherService {
    func fetchWeather(city: String) async throws -> WeatherResponse {
        var components = URLComponents(string: "https://api.openweathermap.org/data/2.5/weather")!
        components.queryItems = [
            .init(name: "q", value: city),          // ⭐ URLComponents가 인코딩을 처리
            .init(name: "appid", value: Config.weatherAPIKey),
            .init(name: "units", value: "metric"),
            .init(name: "lang", value: "kr")
        ]
        guard let url = components.url else { throw URLError(.badURL) }

        let (data, response) = try await URLSession.shared.data(from: url)

        guard let http = response as? HTTPURLResponse else { throw WeatherError.network }
        switch http.statusCode {
        case 200: break
        case 404: throw WeatherError.cityNotFound
        default:  throw WeatherError.server(http.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase   // feels_like → feelsLike
        return try decoder.decode(WeatherResponse.self, from: data)
    }
}
```

> **문자열로 URL을 조립하지 마세요.** 도시 이름에 공백이나 한글이 들어가면 URL이 깨집니다.
> `URLComponents`가 인코딩을 알아서 처리합니다. (원본 튜토리얼들이 자주 빠뜨리는 부분)

### ViewModel

```swift
// ViewModels/WeatherViewModel.swift

@MainActor                       // ⭐ UI 상태를 다루므로 메인 액터에
@Observable
final class WeatherViewModel {
    enum State {
        case idle
        case loading
        case loaded(WeatherResponse)
        case failed(String)
    }

    private(set) var state: State = .idle     // 외부에선 읽기 전용
    private let service = WeatherService()

    func load(city: String) async {
        state = .loading
        do {
            state = .loaded(try await service.fetchWeather(city: city))
        } catch is CancellationError {
            // 화면을 빠져나가 취소된 경우 — 에러 표시하면 안 됨
            state = .idle
        } catch {
            state = .failed(error.localizedDescription)
        }
    }
}
```

> **`catch is CancellationError`를 빠뜨리면**: 사용자가 화면을 빨리 나갈 때
> "작업이 취소되었습니다" 같은 에러가 번쩍 뜹니다. `.task`가 자동 취소를 해주는 대가입니다.

### 화면 + NavigationStack

```swift
// Views/ContentView.swift

struct ContentView: View {
    // 프로그래매틱 네비게이션을 하려면 path를 직접 소유
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            SearchView(onSearch: { city in path.append(city) })
                .navigationDestination(for: String.self) { city in
                    WeatherView(city: city)
                }
        }
    }
}

struct SearchView: View {
    @State private var city = ""
    let onSearch: (String) -> Void

    var body: some View {
        VStack(spacing: 24) {
            Text("날씨 검색")
                .font(.largeTitle.bold())

            TextField("도시 이름 입력", text: $city)
                .textFieldStyle(.roundedBorder)
                .submitLabel(.search)
                .onSubmit { search() }
                .padding(.horizontal)

            Button("검색", action: search)
                .buttonStyle(.borderedProminent)
                .disabled(city.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding()
    }

    private func search() {
        let trimmed = city.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        onSearch(trimmed)
    }
}

struct WeatherView: View {
    let city: String
    @State private var viewModel = WeatherViewModel()

    var body: some View {
        Group {
            switch viewModel.state {
            case .idle:
                Color.clear

            case .loading:
                ProgressView("불러오는 중…")

            case .loaded(let w):
                VStack(spacing: 16) {
                    Text(w.name).font(.largeTitle.bold())
                    Text(w.main.temp, format: .number.precision(.fractionLength(1)))
                        .font(.system(size: 64))
                        + Text("°C").font(.title)
                    Text(w.weather.first?.description ?? "")
                    Text("습도 \(w.main.humidity)%")
                        .foregroundStyle(.secondary)
                }

            case .failed(let message):
                ContentUnavailableView {
                    Label("불러오지 못했습니다", systemImage: "exclamationmark.triangle")
                } description: {
                    Text(message)
                } actions: {
                    // 에러 화면엔 반드시 재시도 버튼을
                    Button("다시 시도") {
                        Task { await viewModel.load(city: city) }
                    }
                }
            }
        }
        .navigationTitle(city)
        .navigationBarTitleDisplayMode(.large)
        // JS: useEffect(() => { fetch() }, [city])
        .task(id: city) {
            await viewModel.load(city: city)
        }
    }
}
```

### 화면 전환 방식 정리

| 방식 | 코드 | 언제 |
|---|---|---|
| 푸시 (밀어넣기) | `NavigationLink(value:)` + `navigationDestination` | 계층 탐색 (목록 → 상세) |
| 프로그래매틱 푸시 | `path.append(value)` | 저장 후 자동 이동 등 |
| 뒤로 가기 | `@Environment(\.dismiss) var dismiss` → `dismiss()` | 커스텀 뒤로가기 버튼 |
| 시트 (아래서 올라옴) | `.sheet(isPresented:)` | 작성/편집 폼 |
| 전체 화면 | `.fullScreenCover(isPresented:)` | 온보딩, 로그인 |
| 알림 | `.alert("제목", isPresented:)` | 확인/취소 |
| 액션 시트 | `.confirmationDialog(...)` | 삭제 확인 등 파괴적 동작 |

```swift
@State private var showEditor = false

Button("새 메모") { showEditor = true }
    .sheet(isPresented: $showEditor) {
        MemoEditorView()
            .presentationDetents([.medium, .large])   // 절반/전체 높이 조절 가능
    }
```

---

## STEP 4: 메모 앱 (완성형) — SwiftData, 이미지, 테마

### ① SwiftData — 로컬 데이터베이스 (iOS 17+)

```swift
// Models/Memo.swift
import SwiftData

@Model                              // 이 매크로 하나로 DB 모델이 됨
final class Memo {
    var title: String
    var content: String
    @Attribute(.externalStorage) var imageData: Data?   // 큰 데이터는 파일로 분리 저장
    var createdAt: Date

    init(title: String, content: String, imageData: Data? = nil) {
        self.title = title
        self.content = content
        self.imageData = imageData
        self.createdAt = .now
    }
}
```

```swift
// 앱 진입점에서 컨테이너 연결
@main
struct MemoApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: Memo.self)     // 이 한 줄로 DB 준비 완료
    }
}
```

```swift
// 조회 — @Query가 알아서 구독합니다 (DB가 바뀌면 화면 자동 갱신)
struct MemoListView: View {
    @Query(sort: \Memo.createdAt, order: .reverse) private var memos: [Memo]
    @Environment(\.modelContext) private var context

    var body: some View {
        List {
            ForEach(memos) { memo in
                NavigationLink(value: memo) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(memo.title).font(.headline)
                        Text(memo.content)
                            .lineLimit(2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .onDelete { indexSet in
                for index in indexSet { context.delete(memos[index]) }
                // 저장은 자동입니다. 즉시 반영하려면 try? context.save()
            }
        }
        .overlay {
            if memos.isEmpty {
                ContentUnavailableView("메모 없음", systemImage: "note.text")
            }
        }
    }
}

// 추가
func addMemo() {
    context.insert(Memo(title: "새 메모", content: ""))
}
```

**필터링/검색:**
```swift
@Query(filter: #Predicate<Memo> { $0.title.contains("회의") },
       sort: \Memo.createdAt, order: .reverse)
private var memos: [Memo]

// 동적 검색어를 쓰려면 init에서 Query를 구성
init(searchText: String) {
    _memos = Query(filter: #Predicate<Memo> {
        searchText.isEmpty || $0.title.localizedStandardContains(searchText)
    }, sort: \Memo.createdAt, order: .reverse)
}
```

> ⚠️ **스키마 변경 주의**: 출시 후 `@Model` 클래스에 프로퍼티를 추가/삭제하면
> 기존 사용자의 DB와 안 맞아 앱이 실행되지 않을 수 있습니다.
> 기본값이 있는 옵셔널 프로퍼티 추가는 대체로 안전하지만, 이름 변경·타입 변경은
> **`VersionedSchema` + `SchemaMigrationPlan`** 이 필요합니다.
> [SwiftData 마이그레이션 문서](https://developer.apple.com/documentation/swiftdata/schemamigrationplan) 참고.
>
> **iOS 16 이하도 지원해야 하면** SwiftData를 못 씁니다 → Core Data를 쓰거나 배포 타깃을 올리세요.

### ② 이미지 선택 — PhotosPicker

```swift
import PhotosUI

struct MemoEditorView: View {
    @State private var selectedItem: PhotosPickerItem?
    @State private var imageData: Data?

    var body: some View {
        VStack {
            if let imageData, let uiImage = UIImage(data: imageData) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 200)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            // ⭐ 권한 요청이 필요 없습니다 — 사용자가 고른 사진만 앱에 전달됨
            PhotosPicker("사진 추가", selection: $selectedItem, matching: .images)
        }
        .task(id: selectedItem) {
            imageData = try? await selectedItem?.loadTransferable(type: Data.self)
        }
    }
}
```

> **`PhotosPicker`는 `NSPhotoLibraryUsageDescription` 권한이 필요 없습니다.**
> 시스템 UI가 별도 프로세스에서 뜨고 선택된 항목만 앱에 넘어오기 때문입니다.
> 예전 방식(`UIImagePickerController` 래핑)은 이제 쓸 이유가 없습니다.

**원격 이미지 (JS의 `<img src>`):**
```swift
AsyncImage(url: URL(string: imageURL)) { phase in
    switch phase {
    case .empty:   ProgressView()
    case .success(let image): image.resizable().scaledToFill()
    case .failure: Image(systemName: "photo")
    @unknown default: EmptyView()
    }
}
.frame(height: 200)
.clipped()
```

### ③ 테마 / 다크모드

```swift
// ① Assets.xcassets에서 색을 정의하면 다크모드 자동 대응 ⭐
//    Color Set 추가 → Appearances를 "Any, Dark"로 → 각각 색 지정
Color("BrandPrimary")

// ② 시스템 시맨틱 색상을 쓰면 아무것도 안 해도 됨
.foregroundStyle(.primary)        // 라이트=검정, 다크=흰색 자동
.foregroundStyle(.secondary)      // 흐린 텍스트
.background(Color(.systemBackground))
.background(.regularMaterial)     // 반투명 블러 배경

// ③ 사용자 설정으로 강제
@AppStorage("colorScheme") private var scheme = "system"

WindowGroup {
    ContentView()
        .preferredColorScheme(
            scheme == "dark" ? .dark : scheme == "light" ? .light : nil   // nil = 시스템 따름
        )
}
```

> 🚨 **`Color.black` / `Color.white`를 직접 쓰지 마세요.** 다크모드에서 흰 배경에 흰 글자가 됩니다.
> `.primary`, `.secondary`, `Color(.systemBackground)` 같은 시맨틱 색상을 쓰면 자동으로 해결됩니다.
> **Preview에 `#Preview("다크") { View().preferredColorScheme(.dark) }` 를 항상 추가**해두면
> 만들면서 바로 확인됩니다.

---

# PART 4: 실전 보강

## 4-0. SwiftUI 핵심 API 보강

PART 3의 샘플 앱에서 주요 흐름을 먼저 보았습니다. 여기서는 프로젝트를 바꿔도 반복해서 쓰는
화면 구성 요소를 주제별로 분해합니다. 예제는 서로 독립적이므로 필요한 절부터 실행해도 됩니다.

### 4-0-1. `Form`, `Section`, 입력 컨트롤

설정·예약·작성 화면은 직접 간격을 맞춘 `VStack`보다 `Form`이 적합합니다. 플랫폼이 행 높이,
구분선, 키보드 동작, 접근성을 맡습니다. React의 폼 라이브러리와 네이티브 입력 묶음에 가깝습니다.

```swift
struct TravelPlanForm: View {
    @State private var city = "교토"
    @State private var style = "도보"
    @State private var travelers = 2
    @State private var departure = Date.now
    @State private var dailyBudget = 120_000.0

    let styles = ["도보", "대중교통", "렌터카"]

    var body: some View {
        NavigationStack {
            Form {
                Section("기본 정보") {
                    TextField("도시", text: $city)
                        .textInputAutocapitalization(.words)

                    Picker("이동 방식", selection: $style) {
                        ForEach(styles, id: \.self) { Text($0) }
                    }

                    Stepper("여행자 \(travelers)명", value: $travelers, in: 1...8)
                }

                Section("일정과 예산") {
                    DatePicker("출발일", selection: $departure, in: Date.now..., displayedComponents: .date)
                    Slider(value: $dailyBudget, in: 30_000...500_000, step: 10_000)
                    Text(dailyBudget, format: .currency(code: "KRW"))
                        .foregroundStyle(.secondary)
                } footer: {
                    Text("예산은 1인 기준 하루 금액입니다.")
                }
            }
            .navigationTitle("여행 계획")
        }
    }
}
```

숫자 입력은 문자열로 받아 직접 파싱할 필요 없이 `format:` 오버로드를 쓸 수 있습니다.

```swift
@State private var cost = 0
TextField("예상 지출", value: $cost, format: .number)
    .keyboardType(.numberPad)
```

> ⚠️ `Picker`의 각 항목 값과 `selection` 타입이 정확히 같아야 합니다. `selection`은 enum인데
> 행은 String이면 선택 표시가 움직이지 않습니다. 가능하면 `CaseIterable` enum을 사용하세요.

### 4-0-2. 네비게이션의 선언형·값 기반 패턴

`NavigationStack`은 브라우저 history처럼 화면 경로를 관리합니다. 단순 링크는 목적 뷰를 바로
지정하고, 복원·딥링크가 필요하면 값과 `navigationDestination`을 분리합니다.

```swift
struct LibraryView: View {
    let books = ["바람의 지도", "유리 정원", "밤의 우체국"]

    var body: some View {
        NavigationStack {
            List(books, id: \.self) { title in
                NavigationLink(value: title) {
                    Label(title, systemImage: "book.closed")
                }
            }
            .navigationTitle("내 서재")
            .navigationDestination(for: String.self) { title in
                BookDetailView(title: title)
            }
        }
    }
}

struct BookDetailView: View {
    let title: String
    var body: some View {
        Text("\(title)의 독서 기록")
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
    }
}
```

프로그램이 경로를 바꾸어야 하면 배열 또는 `NavigationPath`를 바인딩합니다.

```swift
@State private var route: [String] = []

NavigationStack(path: $route) {
    Button("추천 도서로 이동") { route.append("오늘의 추천") }
        .navigationDestination(for: String.self) { BookDetailView(title: $0) }
}
```

iPad의 목록/상세 병렬 UI에는 `NavigationSplitView`를 사용합니다. 좁은 iPhone에서는 자동으로
스택 형태로 접히므로 기기별 화면을 따로 만들 필요가 줄어듭니다.

> ⚠️ 같은 타입에 `navigationDestination`을 여러 군데 중복 선언하면 가장 가까운 선언이
> 우선되어 예상과 다른 화면이 열릴 수 있습니다. 스택 루트 한곳에 모으세요.

### 4-0-3. 데이터 흐름: 소유권부터 결정하기

SwiftUI 상태 선택의 핵심은 “누가 만들고, 누가 수정하고, 누가 읽는가”입니다. React의
로컬 state → controlled props → Context/store 순서와 같습니다.

```swift
@Observable
final class ReadingStore {
    var goal = 20
    var completed = 0
    var progress: Double { goal == 0 ? 0 : Double(completed) / Double(goal) }
}

struct ReadingAppView: View {
    @State private var store = ReadingStore()       // 생성·수명 소유

    var body: some View {
        ReadingDashboard()
            .environment(store)                    // 깊은 자식에 주입
    }
}

struct ReadingDashboard: View {
    @Environment(ReadingStore.self) private var store

    var body: some View {
        @Bindable var store = store                 // 입력 컨트롤용 Binding 생성
        Form {
            Stepper("월 목표 \(store.goal)권", value: $store.goal, in: 1...100)
            ProgressView(value: store.progress)
            GoalEditor(goal: $store.goal)           // 자식이 단일 값을 수정
        }
    }
}

struct GoalEditor: View {
    @Binding var goal: Int
    var body: some View { Slider(value: Binding(
        get: { Double(goal) },
        set: { goal = Int($0) }
    ), in: 1...100, step: 1) }
}
```

`@Environment(\.dismiss)`, `@Environment(\.colorScheme)`처럼 시스템이 제공하는 값은 key path로,
직접 만든 `@Observable` 객체는 타입으로 꺼냅니다.

> ⭐ 상태는 가능한 한 사용하는 화면 가까이에 두고, 여러 화면이 정말 공유할 때만 environment로
> 올리세요. 모든 것을 전역 store로 만들면 변경 경로가 숨고 Preview 준비도 어려워집니다.
>
> ⚠️ environment 객체를 주입하지 않으면 실행 중 크래시합니다. 해당 뷰의 Preview에도
> `.environment(ReadingStore())`를 반드시 붙이세요.

### 4-0-4. `alert`, `confirmationDialog`, `sheet`

세 API는 모두 현재 화면 위에 선택지를 띄우지만 목적이 다릅니다. `alert`는 중요한 확인,
`confirmationDialog`는 여러 행동 중 선택, `sheet`는 별도 작업 흐름입니다.

```swift
struct ExpenseActionsView: View {
    @State private var showSaved = false
    @State private var showActions = false
    @State private var showEditor = false

    var body: some View {
        VStack(spacing: 20) {
            Button("지출 저장") { showSaved = true }
            Button("더 보기") { showActions = true }
            Button("지출 편집") { showEditor = true }
        }
        .alert("저장 완료", isPresented: $showSaved) {
            Button("확인", role: .cancel) { }
        } message: {
            Text("이번 달 기록에 반영했습니다.")
        }
        .confirmationDialog("기록 관리", isPresented: $showActions) {
            Button("복제") { duplicateExpense() }
            Button("삭제", role: .destructive) { deleteExpense() }
            Button("취소", role: .cancel) { }
        }
        .sheet(isPresented: $showEditor) {
            ExpenseEditor()
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
        }
    }

    private func duplicateExpense() { }
    private func deleteExpense() { }
}

struct ExpenseEditor: View {
    @Environment(\.dismiss) private var dismiss
    var body: some View { Button("편집 완료") { dismiss() } }
}
```

식별 가능한 선택 항목이 있을 때는 불리언과 별도 데이터 대신 `.sheet(item:)`가 안전합니다.

> ⚠️ 하나의 뷰에 같은 종류의 프레젠테이션을 여러 번 흩어 붙이면 어떤 상태가 이겼는지
> 추적하기 어렵습니다. 화면별 enum 라우트 하나로 통합하거나 관련 버튼 가까이에 배치하세요.

### 4-0-5. `List`, `ForEach`, 삭제와 스와이프

`List`는 스크롤·행 재사용·선택·편집 동작을 제공하는 컨테이너이고 `ForEach`는 데이터를
여러 View로 변환하는 빌더입니다. React의 `<ul>`과 `array.map()`을 분리해 생각하면 쉽습니다.

```swift
struct ReadingItem: Identifiable {
    let id = UUID()
    var title: String
    var finished = false
}

struct ReadingList: View {
    @State private var items = [
        ReadingItem(title: "파도 지도"),
        ReadingItem(title: "작은 행성")
    ]

    var body: some View {
        List {
            Section("읽는 중") {
                ForEach($items) { $item in
                    Label(item.title, systemImage: item.finished ? "checkmark.circle.fill" : "book")
                        .swipeActions(edge: .leading, allowsFullSwipe: true) {
                            Button("완료") { item.finished.toggle() }
                                .tint(.green)
                        }
                        .swipeActions(edge: .trailing) {
                            Button("삭제", role: .destructive) { delete(item.id) }
                        }
                }
                .onDelete { items.remove(atOffsets: $0) }
                .onMove { items.move(fromOffsets: $0, toOffset: $1) }
            }
        }
        .toolbar { EditButton() }
    }

    private func delete(_ id: UUID) {
        items.removeAll { $0.id == id }
    }
}
```

> ⚠️ `ForEach(items.indices, id: \.self)`로 편집 가능한 배열을 그리면 삭제 후 인덱스가 바뀌어
> 잘못된 행 상태가 재사용될 수 있습니다. 모델에 안정적인 `id`를 주고 그 식별자를 쓰세요.

### 4-0-6. 커스텀 수정자와 `@ViewBuilder`

반복되는 스타일을 View extension이나 `ViewModifier`로 묶으면 디자인 규칙을 한곳에서 바꿀 수
있습니다. React의 공통 컴포넌트·CSS utility를 타입 안전하게 합친 감각입니다.

```swift
struct CardSurface: ViewModifier {
    let emphasized: Bool

    func body(content: Content) -> some View {
        content
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(emphasized ? Color.accentColor.opacity(0.15) : Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

extension View {
    func cardSurface(emphasized: Bool = false) -> some View {
        modifier(CardSurface(emphasized: emphasized))
    }
}

struct InfoCard<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title).font(.headline)
            content
        }
        .cardSurface()
    }
}

InfoCard(title: "여행 메모") {
    Text("아침 시장은 8시 전에 방문")
    if Bool.random() { Label("우산 준비", systemImage: "umbrella") }
}
```

`@ViewBuilder`는 여러 View 표현식과 제한적인 `if`/`switch`를 하나의 View 결과로 조합하는
result builder입니다. SwiftUI의 `VStack { ... }` 문법도 같은 원리입니다.

> ⚠️ 수정자 안에 네트워크 요청이나 상태 변경을 숨기지 마세요. 수정자는 모양·행동을 조합하는
> 도구로 유지하고, 부수 효과는 `.task`나 ViewModel의 이름 있는 메서드로 드러내세요.

### 4-0-7. 애니메이션, 전환, `matchedGeometryEffect`

SwiftUI 애니메이션은 시작·끝 상태만 설명하면 중간 프레임을 보간합니다. React 애니메이션
라이브러리에서 style state를 바꾸는 것과 비슷하며, 상태 변경을 `withAnimation`으로 감쌉니다.

```swift
struct RecipeFavoriteView: View {
    @State private var isFavorite = false
    @State private var showNote = false

    var body: some View {
        VStack(spacing: 16) {
            Button {
                withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) {
                    isFavorite.toggle()
                    showNote.toggle()
                }
            } label: {
                Image(systemName: isFavorite ? "heart.fill" : "heart")
                    .scaleEffect(isFavorite ? 1.25 : 1)
            }

            if showNote {
                Text("즐겨찾는 레시피에 추가했습니다.")
                    .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
    }
}
```

서로 다른 계층에 있는 두 View가 같은 요소처럼 이동하게 하려면 namespace를 공유합니다.

```swift
@Namespace private var coverSpace
@State private var expanded = false

if expanded {
    Image("travel-cover").resizable().matchedGeometryEffect(id: "cover", in: coverSpace)
} else {
    Image("travel-cover").resizable().matchedGeometryEffect(id: "cover", in: coverSpace)
        .frame(width: 80, height: 120)
}
```

> ⚠️ `.animation(..., value:)`의 `value`를 생략한 오래된 형태는 하위의 관계없는 변화까지
> 애니메이션할 수 있습니다. 어떤 상태 변화에 반응하는지 명시하거나 `withAnimation`을 쓰세요.

### 4-0-8. `Codable` 중첩 모델과 날짜 전략

JSON 구조가 중첩되어 있으면 Swift 모델도 같은 계층으로 표현하는 것이 가장 단순합니다.
JS의 `JSON.parse()`와 달리 타입·키·날짜 형식이 맞지 않으면 decode 시점에 명확히 실패합니다.

```swift
struct TripArchive: Codable {
    struct Stop: Codable, Identifiable {
        let id: UUID
        let city: String
        let visitedAt: Date
    }

    let ownerName: String
    let stops: [Stop]

    enum CodingKeys: String, CodingKey {
        case ownerName = "owner_name"
        case stops
    }
}

let decoder = JSONDecoder()
decoder.dateDecodingStrategy = .iso8601
let archive = try decoder.decode(TripArchive.self, from: data)

let encoder = JSONEncoder()
encoder.dateEncodingStrategy = .iso8601
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
let savedData = try encoder.encode(archive)
```

서버 날짜가 초 단위 숫자면 `.secondsSince1970`, 밀리초면 `.millisecondsSince1970`을 사용합니다.
임의 포맷은 `.formatted(DateFormatter)`로 맞출 수 있지만 포맷터 생성 비용 때문에 재사용하세요.

```swift
do {
    _ = try decoder.decode(TripArchive.self, from: data)
} catch let DecodingError.keyNotFound(key, context) {
    print("누락 키: \(key.stringValue), 경로: \(context.codingPath)")
} catch {
    print("디코딩 실패: \(error)")
}
```

> ⚠️ `try? decoder.decode(...)`만 쓰면 서버 스키마가 바뀌어도 단지 nil로 보여 원인을 잃습니다.
> 개발 중에는 `DecodingError`를 로그로 남기고 사용자 화면에서만 친절한 메시지로 바꾸세요.

### 4-0-9. `UserDefaults`와 `@AppStorage`

작은 설정 값은 UserDefaults에 저장합니다. 브라우저의 localStorage와 비슷하지만 Bool·Int·Data 등
기본 타입을 직접 다루며, 비밀번호·대용량 모델·관계형 데이터 저장소는 아닙니다.

```swift
struct ReaderSettingsView: View {
    @AppStorage("reader.fontScale") private var fontScale = 1.0
    @AppStorage("reader.keepScreenOn") private var keepScreenOn = false

    var body: some View {
        Form {
            Slider(value: $fontScale, in: 0.8...1.6, step: 0.1) {
                Text("글자 배율")
            }
            Toggle("읽는 동안 화면 켜기", isOn: $keepScreenOn)
        }
    }
}

enum SettingsKey {
    static let lastBookID = "reader.lastBookID"
}

UserDefaults.standard.set("B-104", forKey: SettingsKey.lastBookID)
let lastID = UserDefaults.standard.string(forKey: SettingsKey.lastBookID)
```

작은 `Codable` 값은 `Data`로 인코딩할 수 있지만 목록이 커지거나 검색·정렬이 필요하면
SwiftData를 사용하세요.

```swift
let preferences = ["소설", "여행"]
let data = try JSONEncoder().encode(preferences)
UserDefaults.standard.set(data, forKey: "reader.categories")
```

> ⚠️ UserDefaults는 암호화 저장소가 아닙니다. 토큰·비밀번호는 Keychain에 저장하세요.
> 또 값을 매 프레임 쓰는 용도로 사용하지 말고 의미 있는 설정 변경 시점에만 갱신하세요.

### 4-0-10. `ScrollView`, lazy 컨테이너, `GeometryReader`

`ScrollView`는 임의 레이아웃을 스크롤하게 하고, `LazyVStack`/`LazyVGrid`는 보이는 항목 주변만
생성합니다. 웹의 overflow container + virtualized list 조합과 비슷합니다.

```swift
struct BookShelfGrid: View {
    let titles = (1...100).map { "도서 \($0)" }
    let columns = [GridItem(.adaptive(minimum: 140), spacing: 12)]

    var body: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 12) {
                ForEach(titles, id: \.self) { title in
                    Text(title)
                        .frame(maxWidth: .infinity, minHeight: 100)
                        .cardSurface()
                }
            }
            .padding()
        }
        .scrollDismissesKeyboard(.interactively)
    }
}
```

부모가 제안한 실제 크기를 읽어 비율 기반 UI를 만들 때만 `GeometryReader`를 사용합니다.

```swift
GeometryReader { proxy in
    let width = proxy.size.width
    ZStack(alignment: .leading) {
        Capsule().fill(.quaternary)
        Capsule().fill(.blue).frame(width: width * 0.65)
    }
}
.frame(height: 12)                     // 바깥에서 높이를 제한
```

> ⚠️ `GeometryReader`는 가능한 모든 공간을 차지하려 합니다. 단순 중앙 정렬이나 화면 너비
> 확보에 남용하면 레이아웃이 커집니다. 먼저 `frame`, `containerRelativeFrame`, 스택 정렬을 쓰세요.

### 4-0-11. 이미지, 그라디언트, 도형과 제스처

에셋 이미지는 해상도별 파일 대신 Assets의 단일 이름으로 읽고, SF Symbols는 시스템 스타일과
접근성 크기에 자동 적응합니다. 원격 이미지는 `AsyncImage`의 모든 상태를 처리하세요.

```swift
struct RecipeHero: View {
    let url: URL?

    var body: some View {
        AsyncImage(url: url) { phase in
            switch phase {
            case .empty:
                ProgressView()
            case .success(let image):
                image.resizable().scaledToFill()
            case .failure:
                Image(systemName: "fork.knife").font(.largeTitle)
            @unknown default:
                EmptyView()
            }
        }
        .frame(height: 220)
        .frame(maxWidth: .infinity)
        .background(LinearGradient(colors: [.orange.opacity(0.3), .pink.opacity(0.2)],
                                   startPoint: .topLeading, endPoint: .bottomTrailing))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .contentShape(Rectangle())
        .onTapGesture(count: 2) { markFavorite() }
    }

    private func markFavorite() { }
}
```

드래그·확대·회전처럼 값이 연속으로 바뀌는 제스처는 `@GestureState`로 일시 상태를 보관하고,
끝났을 때 영구 `@State`에 반영합니다. 단순 실행은 `Button`이 접근성·키보드 지원 면에서 낫습니다.

> ⚠️ `scaledToFill()`은 프레임 밖으로 넘칠 수 있어 `.clipped()` 또는 `clipShape`가 필요합니다.
> 또 URL별 메모리/디스크 캐시 정책을 세밀하게 제어해야 하면 전용 이미지 로더를 두세요.

### 4-0-12. 타이머, `onReceive`, 햅틱

주기적 UI 갱신은 Combine 타이머를 구독하거나 async 루프를 사용합니다. `onReceive`는 React에서
외부 event emitter를 구독하는 효과와 비슷하고, View가 사라지면 구독도 정리됩니다.

```swift
import Combine

struct ReadingTimerView: View {
    private let ticker = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    @State private var seconds = 0
    @State private var isRunning = false

    var body: some View {
        VStack(spacing: 16) {
            Text(Duration.seconds(seconds).formatted(.time(pattern: .minuteSecond)))
                .font(.system(.largeTitle, design: .monospaced))

            Button(isRunning ? "일시 정지" : "시작") {
                isRunning.toggle()
            }
        }
        .onReceive(ticker) { _ in
            guard isRunning else { return }
            seconds += 1
        }
        .sensoryFeedback(.selection, trigger: isRunning)
        .sensoryFeedback(.success, trigger: seconds >= 1_500)
    }
}
```

명령형 햅틱이 필요한 구버전·UIKit 경계에서는 `UIImpactFeedbackGenerator`를 사용할 수 있습니다.

```swift
let generator = UIImpactFeedbackGenerator(style: .medium)
generator.prepare()
generator.impactOccurred()
```

> ⚠️ 타이머는 정확한 스케줄러가 아니며 앱이 백그라운드에 가면 멈출 수 있습니다.
> 경과 시간을 tick 횟수로만 계산하지 말고 시작 `Date`와 현재 시각의 차이로 복원하세요.
> 햅틱은 시뮬레이터에서 느낄 수 없으므로 실기기에서 확인하고 과도한 반복을 피하세요.

### 4-0-13. `Path`, `Shape`, 그리기와 렌더링 효과

기본 도형으로 표현할 수 없는 차트·배지·장식은 `Path`로 선을 그리고, 재사용할 모양은
`Shape`로 만듭니다. 웹의 SVG path와 비슷하지만 SwiftUI 레이아웃과 애니메이션에 참여합니다.

```swift
struct BookmarkShape: Shape {
    var notch: CGFloat

    var animatableData: CGFloat {
        get { notch }
        set { notch = newValue }
    }

    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.minX, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.midX, y: rect.maxY - notch))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
        path.closeSubpath()
        return path
    }
}

struct ReadingBadge: View {
    @State private var deepNotch = false

    var body: some View {
        BookmarkShape(notch: deepNotch ? 42 : 18)
            .fill(.blue.gradient)
            .overlay { Image(systemName: "book.fill").foregroundStyle(.white) }
            .frame(width: 80, height: 110)
            .shadow(color: .blue.opacity(0.25), radius: 8, y: 4)
            .onTapGesture {
                withAnimation(.spring) { deepNotch.toggle() }
            }
    }
}
```

`stroke(style:)`은 선 끝·점선을 제어하고, `trim(from:to:)`는 진행률 원호를 만들 때 유용합니다.
`Canvas`는 입자가 많거나 반복 그리기가 많은 2D 그래픽에서 View 수를 줄여줍니다.

```swift
Circle()
    .trim(from: 0, to: 0.72)
    .stroke(.mint, style: StrokeStyle(lineWidth: 12, lineCap: .round))
    .rotationEffect(.degrees(-90))
    .drawingGroup()                     // 필요할 때만 오프스크린 렌더링
```

> ⚠️ `drawingGroup()`과 blur·blend mode는 GPU 메모리와 오프스크린 패스를 늘립니다.
> 보기 좋다는 이유로 모든 카드에 붙이지 말고 Instruments로 측정한 뒤 사용하세요.

### 4-0-14. 적응형 레이아웃, 정렬, 앱 생명주기

SwiftUI는 부모가 크기를 제안하고 자식이 필요한 크기를 답하는 방식입니다. CSS breakpoint를
직접 복제하기보다 `ViewThatFits`, `layoutPriority`, 크기 클래스처럼 의도를 표현하세요.

```swift
struct ExpenseSummaryBar: View {
    let total: Int

    var content: some View {
        Group {
            Label("이번 달", systemImage: "calendar")
            Spacer()
            Text(total, format: .currency(code: "KRW"))
                .fontWeight(.bold)
                .layoutPriority(1)
        }
    }

    var body: some View {
        ViewThatFits(in: .horizontal) {
            HStack { content }
            VStack(alignment: .leading) { content }
        }
        .padding()
    }
}
```

복잡한 반복 배치는 `Layout` 프로토콜로 컨테이너를 만들 수 있고, 특수 정렬은
`alignmentGuide`로 같은 축의 기준점을 맞춥니다. 단순 화면은 스택·Grid를 먼저 사용하세요.

앱이 활성/비활성/백그라운드로 바뀌는 시점은 environment의 `scenePhase`로 관찰합니다.

```swift
@Environment(\.scenePhase) private var scenePhase
@State private var draft = ""

TextEditor(text: $draft)
    .onChange(of: scenePhase) { _, phase in
        if phase == .background {
            saveDraft(draft)
        }
    }

func saveDraft(_ text: String) { }
```

> ⚠️ `onDisappear`는 앱이 강제 종료될 때 호출된다고 보장할 수 없습니다. 중요한 초안은
> 값이 바뀔 때 디바운스 저장하고, `scenePhase` 처리는 마지막 안전망으로 두세요.

### 4-0-15. 탭, 메뉴, 로컬 알림과 Core ML 입구

독립된 최상위 영역은 `TabView`, 행의 보조 작업은 `contextMenu`, 정해진 시각의 기기 알림은
UserNotifications가 담당합니다. 각각 웹의 하단 라우터, 우클릭 메뉴, Notifications API에 대응합니다.

```swift
struct TravelRootView: View {
    @State private var selectedTab = "plans"

    var body: some View {
        TabView(selection: $selectedTab) {
            Text("여행 계획")
                .tabItem { Label("계획", systemImage: "map") }
                .tag("plans")

            Text("저장한 장소")
                .tabItem { Label("저장", systemImage: "bookmark") }
                .tag("saved")
                .badge(3)
        }
    }
}

Text("야시장")
    .contextMenu {
        Button("일정에 복사", systemImage: "doc.on.doc") { }
        Button("삭제", systemImage: "trash", role: .destructive) { }
    }
```

```swift
import UserNotifications

func scheduleTripReminder() async throws {
    let center = UNUserNotificationCenter.current()
    guard try await center.requestAuthorization(options: [.alert, .sound]) else { return }

    let content = UNMutableNotificationContent()
    content.title = "여행 준비 확인"
    content.body = "여권과 충전기를 확인하세요."
    let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 3_600, repeats: false)
    try await center.add(UNNotificationRequest(identifier: "trip-check", content: content, trigger: trigger))
}
```

Create ML로 만든 `.mlmodel`을 프로젝트에 넣으면 Xcode가 Swift 입력·출력 타입을 생성합니다.
이미지·텍스트 전처리는 모델마다 다르므로 생성된 클래스의 Prediction 탭을 기준으로 호출하세요.

```swift
// 예: 프로젝트에 SpendingCategory.mlmodel을 추가해 생성된 타입이라는 가정
import CoreML

let model = try SpendingCategory(configuration: MLModelConfiguration())
let prediction = try model.prediction(note: "공항철도 왕복")
print(prediction.label)
```

> ⚠️ 알림 권한은 앱 시작 직후가 아니라 사용자가 “알림 받기”를 선택한 맥락에서 요청하세요.
> ML 모델 파일명·입력 타입은 모델마다 달라 예제 이름을 그대로 복사하지 말고 생성 코드를 확인하세요.

### 4-0-16. 지도, 파일, 생체 인증, QR 코드

장소 기반 앱은 MapKit, 앱 전용 파일은 `FileManager`, 잠금 해제는 LocalAuthentication을 씁니다.
모두 시뮬레이터와 실기기 동작 차이가 있으므로 화면 로직과 서비스 코드를 분리하세요.

```swift
import MapKit

struct Place: Identifiable {
    let id = UUID()
    let name: String
    let coordinate: CLLocationCoordinate2D
}

struct TripMapView: View {
    @State private var camera: MapCameraPosition = .region(.init(
        center: CLLocationCoordinate2D(latitude: 35.6812, longitude: 139.7671),
        span: MKCoordinateSpan(latitudeDelta: 0.08, longitudeDelta: 0.08)
    ))
    let places = [Place(name: "중앙역", coordinate: .init(latitude: 35.6812, longitude: 139.7671))]

    var body: some View {
        Map(position: $camera) {
            ForEach(places) { place in
                Marker(place.name, coordinate: place.coordinate)
            }
            UserAnnotation()
        }
        .mapControls { MapCompass(); MapScaleView() }
    }
}
```

```swift
import LocalAuthentication

func unlockPrivateNotes() async throws -> Bool {
    let context = LAContext()
    var error: NSError?
    guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) else { return false }
    return try await context.evaluatePolicy(
        .deviceOwnerAuthentication,
        localizedReason: "비공개 여행 메모를 열기 위해 인증합니다."
    )
}

func saveExport(_ data: Data) throws -> URL {
    let folder = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    let url = folder.appending(path: "trip-export.json")
    try data.write(to: url, options: .atomic)
    return url
}
```

QR 코드는 Core Image의 `CIQRCodeGenerator` 필터로 만들고 `ImageRenderer` 또는 `CIContext`로
이미지화할 수 있습니다. 입력은 UTF-8 `Data`이며 확대할 때 보간을 끄면 모서리가 선명합니다.

> ⚠️ 현재 위치를 표시하려면 Info 설정과 위치 권한 요청이 별도로 필요합니다. Face ID 문구도
> `NSFaceIDUsageDescription`에 구체적으로 적으세요. 문서 폴더 파일을 UI 스레드에서 크게 읽지 말고,
> QR에는 비밀값을 평문으로 넣지 마세요—누구나 카메라로 읽을 수 있습니다.

## 4-1. 디버깅 / 로그

```swift
// 간단한 확인
print("디버그 메시지")

// 권장: os.Logger (성능 좋고 Console.app에서 필터링 가능)
import OSLog

let logger = Logger(subsystem: "com.yourname.app", category: "network")

logger.debug("요청 시작: \(url)")
logger.info("응답 \(statusCode)")
logger.warning("재시도 \(attempt)회")
logger.error("실패: \(error.localizedDescription)")

// 민감 정보는 자동으로 가려집니다 (privacy 기본값이 .private)
logger.info("토큰: \(token, privacy: .private)")
logger.info("도시: \(city, privacy: .public)")     // 명시해야 로그에 그대로 나옴
```

**보는 법**: Xcode 하단 디버그 영역에 자동 출력. 또는 Mac의 **Console.app**에서
기기 선택 후 subsystem으로 필터링 (실기기 로그를 볼 때 유용).

**브레이크포인트**: 줄 번호 옆 클릭. `po variableName`을 콘솔에 입력하면 값이 출력됩니다.

**뷰 계층 디버깅**: 실행 중 Xcode 하단의 **Debug View Hierarchy** 버튼 →
3D로 뷰가 분해되어 보입니다. "이 여백이 어디서 왔지?"를 확인으로 해결할 수 있습니다.

**메모리 누수 확인**: 그 옆의 **Debug Memory Graph** 버튼 →
해제됐어야 할 객체가 남아 있으면 여기 보입니다 (→ `[weak self]` 확인).

## 4-2. 권한 처리

**1단계: 권한 설명 문구 추가** (Target → Info 탭, 또는 Info.plist)

```xml
<key>NSCameraUsageDescription</key>
<string>프로필 사진을 촬영하기 위해 카메라가 필요합니다.</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>메모에 사진을 첨부하기 위해 필요합니다.</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>현재 위치의 날씨를 보여주기 위해 필요합니다.</string>

<key>NSUserTrackingUsageDescription</key>
<string>여러 앱과 웹사이트에서의 활동을 연결해 개인화 기능을 제공하기 위해 필요합니다.</string>
```

> 🚨 **설명 문구 없이 권한을 요청하면 앱이 즉시 크래시합니다.** 그리고 App Store 심사에서
> "설명이 구체적이지 않다"는 이유로 리젝되는 사례가 많습니다.
> **"~을 위해 필요합니다"까지 구체적으로** 쓰세요. "카메라 접근" 같은 건 리젝 사유입니다.

**2단계: 런타임 요청**

```swift
import AVFoundation

func requestCamera() async -> Bool {
    await AVCaptureDevice.requestAccess(for: .video)
}

// 현재 상태 확인
switch AVCaptureDevice.authorizationStatus(for: .video) {
case .authorized:    // 사용 가능
case .notDetermined: // 아직 안 물어봄 → 요청
case .denied, .restricted:
    // 거부됨 → 설정 앱으로 안내
    if let url = URL(string: UIApplication.openSettingsURLString) {
        await UIApplication.shared.open(url)
    }
@unknown default: break
}
```

**권한 설계 3원칙:**
1. **필요한 순간에 요청** — 앱 시작하자마자 요청하면 거부율이 급등합니다
2. **요청 전에 이유를 설명하는 화면을 먼저** 보여주기 (한 번 거부하면 다시 못 물어봅니다)
3. **권한이 필요 없는 대안 우선** — PhotosPicker(권한 불필요) > 사진 라이브러리 전체 접근

> `NSUserTrackingUsageDescription`과 ATT는 **앱이나 제3자 SDK가 다른 회사의 앱·웹사이트에 걸쳐
> 사용자를 추적할 때만** 필요합니다. 광고 SDK를 쓰더라도 추적하지 않으면 무조건 요청하는 권한이
> 아닙니다. 필요하다면 기능 가치를 설명한 뒤 요청하고, 거부해도 핵심 기능은 그대로 제공하세요.

## 4-3. 인앱 결제와 구독 (수익화)

StoreKit 2는 별도 패키지 없이 iOS에 들어 있습니다. App Store Connect에서 일회성 상품
`premium_theme`와 자동 갱신 구독 `pro_monthly`를 만든 뒤, 상품 ID를 코드와 정확히 맞추세요.

React의 결제 상태 store처럼 `@Observable` 모델 하나가 상품·구매 권한을 관리하면 편합니다.

```swift
import SwiftUI
import Observation
import StoreKit

@MainActor @Observable
final class StoreModel {
    private let productIDs = ["premium_theme", "pro_monthly"]
    private(set) var products: [Product] = []
    private(set) var entitledProductIDs: Set<String> = []
    private var updates: Task<Void, Never>?

    init() {
        // ⭐ 구매 요청보다 먼저 등록. 앱 밖에서 끝난 거래도 놓치지 않습니다.
        updates = listenForTransactions()
        Task {
            await loadProducts()
            await refreshEntitlements()
        }
    }

    deinit { updates?.cancel() }

    func loadProducts() async {
        do {
            products = try await Product.products(for: productIDs)
        } catch {
            products = [] // UI에 재시도 버튼과 오류 메시지를 표시
        }
    }

    func purchase(_ product: Product) async throws {
        switch try await product.purchase() {
        case .success(let result):
            let transaction = try checkVerified(result)
            grant(productID: transaction.productID) // ⭐ transaction.id가 아님
            await transaction.finish()
        case .pending:
            break // Ask to Buy 등: Transaction.updates가 나중에 완료를 전달
        case .userCancelled:
            break
        @unknown default:
            break
        }
    }

    private func listenForTransactions() -> Task<Void, Never> {
        Task { [weak self] in
            for await update in Transaction.updates {
                do {
                    let transaction = try self?.checkVerified(update)
                    if let transaction {
                        self?.grant(productID: transaction.productID)
                        await transaction.finish()
                    }
                } catch { /* 검증 실패 기록; entitlement 지급 금지 */ }
            }
        }
    }

    private nonisolated func checkVerified<T>(
        _ result: VerificationResult<T>
    ) throws -> T {
        switch result {
        case .verified(let value): return value
        case .unverified(_, let error): throw error
        }
    }

    private func grant(productID: String) {
        guard productIDs.contains(productID) else { return }
        entitledProductIDs.insert(productID)
    }
}
```

⚠️ **항상 `productID`로 매핑하세요.** `Transaction.id`는 거래마다 달라지는 거래 ID입니다.
이를 상품 키로 쓰면 결제는 성공했는데 프리미엄 기능이 안 열리는 버그가 납니다.

현재 권한은 앱 시작, 포그라운드 복귀, 복원 후에 다시 계산합니다. 만료·취소·환불된 거래를
제외하도록 `Transaction.currentEntitlements`를 진실의 원천으로 삼으세요.

```swift
extension StoreModel {
    func refreshEntitlements() async {
        var active: Set<String> = []
        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result,
                  transaction.revocationDate == nil,
                  productIDs.contains(transaction.productID) else { continue }
            active.insert(transaction.productID)
        }
        entitledProductIDs = active
    }

    func restore() async throws {
        try await AppStore.sync() // 사용자 동작(복원 버튼)에서만 호출
        await refreshEntitlements()
    }

    func subscriptionStatus(for product: Product) async throws
        -> [Product.SubscriptionInfo.Status] {
        try await product.subscription?.status ?? []
    }
}
```

```swift
struct PaywallView: View {
    @Environment(StoreModel.self) private var store
    @State private var showManageSubscriptions = false

    var body: some View {
        VStack {
            ForEach(store.products) { product in
                Button("\(product.displayName) · \(product.displayPrice)") {
                    Task { try? await store.purchase(product) }
                }
            }
            Button("구매 복원") { Task { try? await store.restore() } }
            Button("구독 관리") { showManageSubscriptions = true }
        }
        .manageSubscriptionsSheet(isPresented: $showManageSubscriptions)
    }
}
```

### 테스트와 심사 체크리스트

- Xcode에서 `File → New → StoreKit Configuration File`로 로컬 `.storekit` 파일을 만들고
  Scheme → Run → StoreKit Configuration에 연결하세요. 구매·갱신·만료·환불·Ask to Buy를 시뮬레이션합니다.
- 실제 App Store Connect 상품은 **Sandbox Apple Account**와 실기기/TestFlight로 확인하세요.
- ⚠️ 구매 리스너는 구매 요청 **전에** 등록하세요. 앱이 백그라운드인 동안 끝난 거래도 처리해야 합니다.
- ⚠️ 눈에 보이는 **구매 복원** 버튼은 필수입니다. 없으면 App Store 심사에서 리젝될 수 있습니다.
- ⚠️ 환불·취소는 App Store Server Notifications 또는 시작/복귀 때 재검증해 entitlement를 회수하세요.
- ⚠️ 가격은 `displayPrice`처럼 StoreKit이 준 현지화 문자열만 표시하세요. 가격 하드코딩은
  지역별 세금·통화와 어긋나며 App Store 심사 지침 2.3.7 문제로 이어질 수 있습니다.
- ⭐ 정직한 페이월: 무료/유료 기능, 구독 기간·자동 갱신을 명확히 쓰고 가짜 타이머,
  닫기 숨김, 고가 플랜 강제 선택 같은 다크패턴을 쓰지 마세요.

→ 공식 문서: [StoreKit 인앱 구매 흐름](https://developer.apple.com/documentation/storekit/offering-completing-and-restoring-in-app-purchases),
[Xcode에서 인앱 구매 테스트](https://developer.apple.com/documentation/storekit/testing-in-app-purchases-in-xcode)

## 4-4. 코드 서명 & 아카이브

iOS는 Android와 달리 **keystore를 직접 관리하지 않습니다.** Apple이 클라우드에서 관리합니다.

```
1. Xcode → 프로젝트 → Target → "Signing & Capabilities"
2. ✅ "Automatically manage signing" 체크
3. Team 드롭다운에서 본인 계정 선택
4. Bundle Identifier가 고유한지 확인
5. 기기 목록에서 "Any iOS Device (arm64)" 선택   ← 시뮬레이터면 Archive 메뉴가 비활성화됩니다
6. 메뉴 → Product → Archive
7. Organizer 창 → Distribute App → App Store Connect → Upload
```

**자주 막히는 곳:**

| 증상 | 원인/해결 |
|---|---|
| Archive 메뉴가 회색 | 시뮬레이터가 선택돼 있음 → "Any iOS Device" 선택 |
| "No profiles for ... were found" | Bundle ID가 계정에 등록 안 됨 → Xcode가 자동 생성하게 두거나 developer.apple.com에서 생성 |
| "The bundle version must be higher" | 업로드할 때마다 Build 번호를 올려야 함 (Version은 그대로 둬도 됨) |
| 업로드 후 TestFlight에 안 뜸 | 처리에 10~30분 걸림. "Missing Compliance"(암호화 신고) 응답 필요할 수 있음 |

**암호화 신고 자동화** (매번 물어보는 걸 없애기):
```xml
<!-- Info.plist — 표준 HTTPS만 쓴다면 -->
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

## 4-5. TestFlight (베타 배포) ⭐

Android의 내부 테스트에 해당하지만 **iOS 쪽이 훨씬 잘 되어 있습니다.**

```
내부 테스터 (Internal)   최대 100명, App Store Connect 계정 보유자
  → 심사 없이 즉시 배포. 개발 중엔 여기만 쓰면 됩니다
  ↓
외부 테스터 (External)   최대 10,000명, 이메일/공개 링크로 초대
  → 첫 빌드는 간단한 베타 심사 필요 (보통 하루 이내)
```

```
1. Archive → Upload
2. App Store Connect → TestFlight 탭 → 빌드 처리 완료 대기
3. 테스터 그룹에 빌드 할당
4. 테스터는 TestFlight 앱으로 설치
```

> **빌드 번호는 매번 올려야 합니다.** 자동화하려면 Build Phases에 스크립트를 추가하거나
> `agvtool next-version -all`을 쓰세요.
>
> **실기기 배포는 무조건 TestFlight로 하세요.** 케이블로 직접 설치한 앱은 7일(무료 계정) 또는
> 개발 프로비저닝 기간 후 만료되지만, TestFlight 빌드는 90일 유효하고 설치도 훨씬 편합니다.

## 4-6. 흔한 에러 읽는 법

### 컴파일 에러

```
Cannot find 'someVariable' in scope
```
→ 오타이거나 다른 스코프에 있음. 또는 **import 누락**.

```
The compiler is unable to type-check this expression in reasonable time;
try breaking up the expression into distinct sub-expressions
```
→ **SwiftUI 최대의 함정.** 뷰 하나가 너무 복잡해서 타입 추론이 폭발한 것.
```swift
// 해결 1: 하위 뷰로 쪼개기
var body: some View {
    VStack {
        headerSection      // ← 별도 프로퍼티로
        contentSection
    }
}
private var headerSection: some View { ... }

// 해결 2: 타입을 명시
let spacing: CGFloat = 16      // 리터럴 연산이 많으면 타입을 박아두기
```

```
Type 'X' does not conform to protocol 'View'
```
→ `body`가 뷰를 반환하지 않음. 흔한 원인: `body` 안에 `let`/`if` 문을 그냥 썼음.
```swift
var body: some View {
    let x = compute()          // ❌ 이러면 안 됨
    Text("\(x)")
}
// ✅ 계산 프로퍼티로 빼거나
private var x: Int { compute() }
```

```
Escaping closure captures mutating 'self' parameter
```
→ struct의 mutating 함수 안에서 비동기 클로저를 씀. `@State`나 클래스로 옮기세요.

### 런타임 크래시

```
Thread 1: Fatal error: Unexpectedly found nil while unwrapping an Optional value
```
→ **크래시 원인 1위.** `!`를 쓴 곳이 실제로 nil이었음. `guard let`으로 바꾸세요.

```
Thread 1: Fatal error: Index out of range
```
→ 배열 범위 초과. `arr[safe: i]` 확장을 만들거나 `arr.indices.contains(i)` 확인.

```
Publishing changes from background threads is not allowed
```
→ UI 상태를 백그라운드에서 변경. ViewModel에 `@MainActor`를 붙이세요.

### Preview가 안 뜰 때

```
1. Preview 하단의 "Diagnostics" 클릭 → 실제 에러 확인
2. 캔버스 새로고침: Option + Cmd + P
3. Preview에 필요한 환경 주입 확인 (modelContainer, environment 등)
4. 그래도 안 되면 Xcode 재시작 (실제로 이걸로 자주 해결됩니다)
```

```swift
// SwiftData를 쓰는 뷰의 Preview는 인메모리 컨테이너가 필요합니다
#Preview {
    MemoListView()
        .modelContainer(for: Memo.self, inMemory: true)
}
```

> **막히면 에러 전문을 Claude에 붙여넣으세요.** SwiftUI 컴파일 에러는 메시지가
> 부정확하기로 유명해서, 이 부분에서 AI의 이득이 특히 큽니다.

## 4-7. 테스트 ⭐ (신규)

```swift
// Swift Testing (Xcode 16+) — 새 프로젝트 기본
import Testing
@testable import MyApp

@Test("도시 검색 성공하면 loaded 상태가 된다")
@MainActor
func loadSuccess() async {
    let vm = WeatherViewModel(service: FakeService())

    await vm.load(city: "Seoul")

    guard case .loaded(let data) = vm.state else {
        Issue.record("loaded 상태가 아님")
        return
    }
    #expect(data.name == "Seoul")
}

// 매개변수화 테스트 — 같은 로직을 여러 입력으로
@Test(arguments: ["", "   ", "\n"])
func 빈문자열은_거부된다(input: String) {
    #expect(Validator.isValidCity(input) == false)
}
```

<details>
<summary>XCTest (기존 방식) — 기존 프로젝트/자료 대부분이 이겁니다</summary>

```swift
import XCTest
@testable import MyApp

final class WeatherViewModelTests: XCTestCase {
    @MainActor
    func testLoadSuccess() async {
        let vm = WeatherViewModel(service: FakeService())
        await vm.load(city: "Seoul")
        if case .loaded(let data) = vm.state {
            XCTAssertEqual(data.name, "Seoul")
        } else {
            XCTFail("loaded 상태가 아님")
        }
    }
}
```
</details>

**UI 테스트 (XCUITest):**
```swift
func testAddTodo() {
    let app = XCUIApplication()
    app.launch()

    app.textFields["할 일 입력…"].tap()
    app.textFields["할 일 입력…"].typeText("우유 사기")
    app.buttons["추가"].tap()

    XCTAssertTrue(app.staticTexts["우유 사기"].exists)
}
```

> **부수 효과**: UI 테스트를 쓰려면 요소에 접근 가능한 레이블이 있어야 합니다.
> 즉 **테스트를 쓰면 VoiceOver 접근성이 저절로 좋아집니다.**

**어디까지 할 것인가** (개인 개발자 기준):
- ✅ ViewModel + 순수 로직(파싱, 검증, 계산) → 단위 테스트. 비용 대비 효과 압도적
- △ 핵심 흐름 1~2개 → UI 테스트 (느리고 불안정해서 많이 만들면 짐이 됩니다)
- ❌ 모든 화면 → 유지보수 비용이 이득을 넘습니다

## 4-8. 접근성 & 다국어 ⭐ (신규)

### 접근성

iOS는 접근성 사용자 비중이 높고 Apple이 강하게 밀어서, **잘 하면 실제로 리뷰에 언급됩니다.**

```swift
// ① 이미지·아이콘에 레이블
Image(systemName: "trash")
    .accessibilityLabel("삭제")

Image("decoration")
    .accessibilityHidden(true)                 // 장식용은 숨김

// ② 여러 요소를 하나로 읽히게
HStack { Image(...); Text("우유 사기"); Text("완료") }
    .accessibilityElement(children: .combine)

// ③ 값과 상태
Slider(value: $volume)
    .accessibilityValue("\(Int(volume))퍼센트")

// ④ 커스텀 동작 (스와이프 메뉴를 VoiceOver로도 쓰게)
.accessibilityAction(named: "삭제") { delete() }
```

### Dynamic Type — iOS에서 가장 자주 깨지는 것

```swift
// ✅ 시스템 폰트 스타일을 쓰면 사용자 글씨 크기 설정에 자동 대응
Text("제목").font(.title)
Text("본문").font(.body)

// ❌ 고정 크기는 큰 글씨 설정에서 그대로 작게 나옴
Text("제목").font(.system(size: 24))

// 고정 크기가 꼭 필요하면 relativeTo로 스케일링 연결
.font(.system(size: 24, weight: .bold, design: .rounded))
.dynamicTypeSize(...DynamicTypeSize.accessibility2)   // 상한만 두기

// 글씨가 커지면 가로 배치를 세로로 바꾸기
@Environment(\.dynamicTypeSize) private var typeSize

var body: some View {
    if typeSize.isAccessibilitySize {
        VStack { content }
    } else {
        HStack { content }
    }
}
```

**확인 방법:**
1. 시뮬레이터: Settings → Accessibility → Display & Text Size → Larger Text 최대로
2. Xcode Preview: `.environment(\.dynamicTypeSize, .accessibility5)` 추가
3. VoiceOver: 실기기 설정 → 손쉬운 사용 → VoiceOver (5분만 써보면 문제가 다 드러납니다)

> **고정 `frame(height:)`를 남발하지 마세요.** 글씨가 커지면 텍스트가 잘립니다.
> 높이는 콘텐츠가 정하게 두고, 필요하면 `minHeight`만 주세요.

### 다국어 (String Catalog)

```
File → New → File → String Catalog  (Localizable.xcstrings)
→ 빌드하면 코드의 문자열이 자동 수집됨
→ "+" 로 언어 추가 → 번역 입력
```

```swift
Text("메모 \(count)개")           // 자동 수집됨
Text("삭제", comment: "메모를 삭제하는 버튼")   // 번역가용 설명

// 복수형: String Catalog UI에서 "Vary by Plural" 설정 (코드 변경 불필요)
```

> **Android보다 훨씬 쉽습니다.** 지금 아무것도 안 해도 되고, 필요할 때 String Catalog만
> 추가하면 기존 코드가 그대로 수집됩니다.

## 4-9. 성능 (신규)

### 뷰 갱신 최소화

```swift
// ❌ 전체가 갱신됨
struct Screen: View {
    @State private var vm = ViewModel()
    var body: some View {
        VStack {
            HeavyChart(data: vm.data)
            Text("\(vm.count)")        // count만 바뀌어도 차트까지 body 재평가
        }
    }
}

// ✅ 자주 바뀌는 부분을 별도 뷰로 분리
struct CountLabel: View {
    let count: Int                     // 이 값이 바뀔 때만 이 뷰가 갱신
    var body: some View { Text("\(count)") }
}
```

> **@Observable은 실제로 읽은 프로퍼티만 추적**합니다 (구버전 `ObservableObject`보다 큰 개선).
> 그래도 하나의 거대한 `body`보다 작은 뷰 여러 개가 항상 유리합니다.

### 리스트 성능

```swift
// 데이터가 많으면 List가 LazyVStack보다 대체로 유리 (셀 재사용)
List(items) { item in Row(item) }

// ForEach에는 안정적인 id가 필수 (Identifiable 또는 id:)
ForEach(items, id: \.id) { }          // ❌ id: \.self 는 값이 바뀌면 전체 재생성

// 이미지가 있는 리스트는 크기를 미리 지정 (레이아웃 재계산 방지)
AsyncImage(url: url) { $0.resizable() } placeholder: { Color.gray }
    .frame(width: 60, height: 60)
```

### 측정

```
Xcode → Product → Profile (Cmd+I) → Instruments
- Time Profiler: 어디서 CPU를 쓰는지
- Allocations: 메모리 증가 추적
- SwiftUI 템플릿: body 재평가 횟수 확인 ⭐
```

> **먼저 측정하세요.** SwiftUI 성능 문제는 직관과 다른 곳에 있는 경우가 많습니다.

## 4-10. App Store 출시 절차 ⭐ (신규)

**심사가 있다는 게 Android와 가장 큰 차이입니다.** 처음이면 2~3주 잡으세요.

### 준비물 체크리스트

```
□ 앱 아이콘 1024×1024 PNG (알파 채널·투명도 없어야 함, 둥근 모서리 자동 적용)
□ 스크린샷 — 6.7"(또는 최신 대형) 필수, 아이패드 지원 시 별도
   → 시뮬레이터에서 Cmd+S로 캡처하면 규격이 맞습니다
□ 앱 이름 (30자), 부제 (30자), 키워드 (100자, 쉼표 구분)
□ 설명 (4000자), 프로모션 텍스트 (170자 — 심사 없이 수정 가능)
□ 개인정보처리방침 URL   ← 필수
□ App Privacy (개인정보 수집 항목 신고) — "영양 성분표"로 스토어에 표시됨
□ 연령 등급 설문
□ 심사용 데모 계정 (로그인이 필요한 앱이면 필수)
□ 심사 노트 (특수한 기능 설명, 테스트 방법)
```

### Privacy Manifest (PrivacyInfo.xcprivacy) ⚠️ 놓치기 쉬움

```
File → New → File → App Privacy  (PrivacyInfo.xcprivacy)
```

- 앱이 **"필수 사유 API"**(파일 타임스탬프, 디스크 여유 공간, UserDefaults, 시스템 부팅 시간 등)를
  쓰면 그 이유를 선언해야 합니다
- 서드파티 SDK도 각자의 매니페스트를 포함해야 하며, **일부 SDK는 서명까지 요구**됩니다
- 누락 시 업로드 단계에서 경고 메일이 오거나 심사에서 막힙니다

> **UserDefaults를 쓰면 대부분 해당됩니다** (사유 코드 `CA92.1` 등).
> Xcode가 업로드 시 알려주니 첫 업로드 때 메일을 잘 읽으세요.

### 심사에서 자주 걸리는 것

| 가이드라인 | 사유 | 대응 |
|---|---|---|
| 2.1 | 크래시·버그 | 심사자는 **실기기 최신 OS**로 봅니다. 릴리즈 빌드를 실기기에서 반드시 테스트 |
| 4.3 | 스팸 (유사 앱 다수) | 템플릿 찍어내기식 앱은 거절. 차별화 요소 필요 |
| 5.1.1 | 권한 설명 부실 / 불필요한 정보 수집 | 설명 문구를 구체적으로, 안 쓰는 권한 제거 |
| 5.1.1(v) | **계정 삭제 기능 없음** | 회원가입이 있으면 **앱 내에서** 계정 삭제 경로 필수 |
| 3.1.1 | 디지털 콘텐츠를 외부 결제로 판매 | 앱 내 구매(IAP)를 써야 함 |
| 2.3 | 스크린샷이 실제와 다름 | 실제 화면으로 |
| 4.2 | 기능이 너무 빈약 | 웹뷰만 감싼 앱 등은 거절 |

> **리젝은 정상입니다.** 첫 앱은 1~2회 리젝이 흔합니다. Resolution Center에서 심사자와
> 대화할 수 있으니, 오해라면 **정중하게 설명 + 스크린샷/동영상**을 첨부하세요.
> 실제로 설명만으로 통과되는 경우가 많습니다.

### 출시 후

```
- 단계적 출시(Phased Release) 켜기 — 7일에 걸쳐 자동 확대, 문제 시 중단 가능
- Xcode Organizer에서 크래시 리포트 확인
- App Store Connect → 분석에서 설치/유지율 확인
- 리뷰에 답글 달기 (App Store Connect에서 직접 가능)
```

## 4-11. 실전 코드 학습 — 공식 샘플

| 샘플 | 레벨 | URL | 추천 이유 |
|---|---|---|---|
| **Landmarks 튜토리얼** | 초급 | [developer.apple.com/tutorials/swiftui](https://developer.apple.com/tutorials/swiftui) | Apple 공식 SwiftUI 입문. 리스트/상세/지도/애니메이션까지 단계별. **가장 먼저 할 것** |
| **Food Truck** | 중급 | [Apple Developer Documentation](https://developer.apple.com/documentation/swiftui/food_truck_building_a_swiftui_multiplatform_app) | SwiftUI 멀티플랫폼 + CloudKit + Live Activity + WidgetKit 통합 |
| **Sample Code Library** | 전체 | [developer.apple.com/documentation/samplecode](https://developer.apple.com/documentation/samplecode) | 주제별 공식 샘플 검색. WWDC 세션 코드도 여기 |
| **Backyard Birds** | 중급 | Apple Sample Code | SwiftData + 위젯 + IAP를 함께 쓴 최신 구성 |

**추천 순서**: Landmarks(끝까지) → Food Truck → 관심 주제 검색

| 이 튜토리얼 | 대응 |
|---|---|
| STEP 1 (UI 기초) | Landmarks Part 1: Creating and Combining Views |
| STEP 2 (리스트) | Landmarks Part 4: Building Lists and Navigation |
| STEP 3 (ViewModel·네비) | Food Truck (NavigationStack + @Observable) |
| STEP 4 (저장) | Backyard Birds / Food Truck의 SwiftData 파트 |
| 4-3 인앱 결제·구독 | StoreKit 공식 구매 흐름 / Backyard Birds의 IAP 구성 |

**학습 팁:**
1. **WWDC 세션 영상이 최고의 교재**입니다. developer.apple.com/videos 에서
   "SwiftUI"로 검색 → 최근 3년치 중 관심 주제. 한글 자막이 있는 것도 많습니다
2. **전부 읽지 말고** 관심 화면 1~2개만 타이핑해서 옮겨보세요
3. Xcode에서 심볼에 **Option + 클릭**하면 문서가 바로 뜹니다. 이게 가장 빠른 레퍼런스입니다

## 4-12. iOS 고유 기능 (네이티브를 쓰는 진짜 이유)

| 기능 | 언제 쓰나 | 학습 링크 |
|---|---|---|
| **Live Activity / Dynamic Island** | 타이머, 진행 중 작업, 배달 추적, 운동 세션 | [ActivityKit](https://developer.apple.com/documentation/activitykit) |
| **WidgetKit 위젯** | 매일 보는 데이터(날씨, 습관, 일정) | [WidgetKit](https://developer.apple.com/documentation/widgetkit) |
| **App Intents / Siri / 단축어** | 음성·1탭 액션 실행, 스팟라이트 노출 | [App Intents](https://developer.apple.com/documentation/appintents) |
| **Control Center 컨트롤** | 제어 센터에 커스텀 버튼 (iOS 18+) | [WidgetKit Controls](https://developer.apple.com/documentation/widgetkit) |
| **SwiftData + CloudKit** | 멀티 기기 자동 동기화 | [SwiftData](https://developer.apple.com/documentation/swiftdata) |
| **Vision / Live Text** | 이미지에서 텍스트·바코드·얼굴 인식 | [Vision](https://developer.apple.com/documentation/vision) |
| **SF Symbols 애니메이션** | 아이콘 미세 움직임만으로 고급스러운 UX | Xcode → SF Symbols 앱 |
| **StoreKit 2** | 구독·인앱결제 (Swift async 기반으로 훨씬 쉬워짐) | [StoreKit](https://developer.apple.com/documentation/storekit) |

**ROI가 가장 큰 것: Live Activity + Dynamic Island.**
타이머/진행 상황/카운트다운이 있는 앱은 붙이는 순간 경쟁 앱과 확실히 구별됩니다.
그 다음이 **위젯** — 홈 화면에 남아 있는 것 자체가 리텐션입니다.

**예시 — "할 일 앱"을 iOS 고유 기능으로 차별화:**
```
├─ Live Activity: 오늘 남은 할 일 개수를 Dynamic Island에
├─ Widget: 홈 화면 중간 크기에 오늘의 할 일 (탭하면 바로 완료)
└─ App Intents: Siri "오늘 할 일 추가해줘" + 단축어 앱 연동
```

> RN에서는 각각 네이티브 모듈을 직접 만들어야 하는 영역입니다.
> 네이티브는 **공식 템플릿(File → New → Target → Widget Extension)** 이 있어 1~2일이면 붙습니다.

## 4-13. 흔한 지뢰 모음 ⭐ (신규)

| 증상 | 원인 | 해결 |
|---|---|---|
| 값을 바꿔도 화면이 그대로 | `@State` 누락 또는 struct 복사 | 프로퍼티 래퍼 표(PART 2) 다시 확인 |
| 자식에서 바꾼 값이 부모에 반영 안 됨 | `@Binding` 대신 값 전달 | `@Binding` + 호출부 `$` |
| 크래시: `found nil while unwrapping` | `!` 강제 언래핑 | `guard let` / `??` |
| 컴파일이 30초 넘게 걸리거나 타임아웃 | 뷰 표현식이 너무 복잡 | 하위 뷰/계산 프로퍼티로 분리 |
| "Publishing changes from background threads" | 백그라운드에서 UI 상태 변경 | ViewModel에 `@MainActor` |
| 다크모드에서 글자가 안 보임 | `Color.black/.white` 직접 사용 | `.primary`, `.secondary` 등 시맨틱 색상 |
| 큰 글씨 설정에서 레이아웃 깨짐 | 고정 `frame(height:)`, `font(.system(size:))` | `.font(.title)` 등 텍스트 스타일 |
| 키보드가 입력창을 가림 | ScrollView 밖에 배치 | `ScrollView` + `.scrollDismissesKeyboard(.interactively)` |
| 화면 나갔는데 에러 토스트가 뜸 | `CancellationError`를 에러로 처리 | `catch is CancellationError` 분기 |
| 메모리가 계속 증가 | 클로저 순환 참조 | `[weak self]`, Debug Memory Graph로 확인 |
| Preview만 안 뜸 | 환경 주입 누락 (modelContainer 등) | Preview에도 `.modelContainer(...)` |
| Archive 메뉴 비활성 | 시뮬레이터 선택됨 | "Any iOS Device" 선택 |
| 시뮬레이터에서 타이핑이 안 됨 | 하드웨어 키보드 연결됨 | `Cmd + K` |
| 실기기에선 되는데 심사에서 크래시 | 심사자는 다른 OS/기기 사용 | 최소 지원 버전 기기에서도 테스트 |

> **디버깅 순서 습관화**: ① 콘솔에서 크래시 메시지 확인 → ② 스택트레이스에서 내 코드 찾기
> → ③ Debug View Hierarchy / Memory Graph → ④ 그래도 모르면 AI에 전문 붙여넣기.

---

# PART 5: 학습 로드맵 & 리소스

## 어떤 루트로 갈 것인가

- **목표 A (Fast-track)**: AI가 쓴 코드를 **읽고 판단하고 디버깅**하는 수준
- **목표 B (Full)**: AI 없이도 직접 코딩하는 수준

### 🚀 Fast-track (Claude 어시스트 환경 — 추천)

**목표**: Apple 공식 샘플을 술술 읽고, "이 뷰모델에 왜 `@MainActor`가 붙었어?" 같은
구체적 질문을 할 수 있는 수준

| 단계 | 내용 | 예상 시간 |
|---|---|---|
| 1 | PART 0 — Xcode 설치, 시뮬레이터, 프로젝트 구조 | 2~3시간 |
| 2 | PART 1 — 문법 훑기 (**1-7 struct/class, 1-8 Optional, 1-9 async**는 집중) | 1~2시간 |
| 3 | PART 2 — 치트시트 북마크 (**상태 프로퍼티 래퍼 표는 정독**) | 20분 |
| 4 | PART 3 STEP 1 + **STEP 1.5 상태 관리** 직접 해보기 | 2~3시간 |
| 5 | PART 4 읽기 (4-6 에러, 4-13 지뢰, 4-10 출시 우선) | 1~2시간 |
| 6 | Landmarks 튜토리얼 Part 1~2 | 1시간 |

**총 6~9시간**

> **보강 학습**: 자기완결 학습을 원하면 PART 1 직후 PART 1.5를, 샘플 앱을 마친 뒤
> PART 4의 4-0을 이어서 읽으세요. 빠른 실행만 목표인 경우에는 필요한 절부터 찾아봐도 됩니다.

**근거**: AI가 STEP 2~4 수준 코드는 직접 써줍니다. 대신 **프로퍼티 래퍼 선택**과
**컴파일 에러 읽기**는 사용자가 판단해야 하는 영역이라 여기에 시간을 쓰는 게 효율적입니다.
(SwiftUI 에러 메시지가 부정확해서, "무슨 증상인지"를 정확히 설명할 수 있어야 AI도 고칩니다.)

**한계**: Swift 동시성 깊은 부분(actor, Sendable), Core Data/StoreKit 같은 큰 프레임워크는
필요해질 때 별도로 파야 합니다.

### 🎓 Full (전통 iOS 개발자 루트)

| 주차 | 내용 | 산출물 |
|---|---|---|
| 0주차 | PART 0~1 (직접 타이핑) | 시뮬레이터 실행, 문법 연습 |
| 1주차 | STEP 1 + 1.5 — SwiftUI 기초와 상태 | 카운터 앱 |
| 2주차 | STEP 2 — List·입력·스와이프 | 할 일 앱 |
| 3주차 | STEP 3 — URLSession·@Observable·NavigationStack | 날씨 앱 |
| 4주차 | STEP 4 — SwiftData·PhotosPicker·테마 | 메모 앱 |
| 5주차 | PART 4 (테스트·접근성·성능) + Landmarks 완주 | 테스트 붙은 앱 |
| 6주차 | 고유 기능 1개 (위젯 추천) + TestFlight 배포 | 위젯 붙은 앱 |
| 7주차~ | 본인 아이디어 앱 + 심사 통과 | 첫 출시 앱 |

**총 30~45시간** (6~8주, 주당 5~7시간)

## JS 개발자가 특히 주의할 점 (Swift)

- 🚨 **`let` = `const`** (JS의 let과 반대!) — 이거 하나가 최대 함정
- `struct`는 **값 타입**(복사됨), `class`는 참조 타입(JS 객체와 같음)
- 함수 호출 시 **인자 레이블**이 필요: `greet(name: "홍길동")`
- 타입 변환이 자동으로 안 됨: `Double(i)`, `Int(s) ?? 0`
- `Int`와 `Double`을 섞어 연산 불가
- `switch`는 모든 경우를 덮어야 함 (`default` 필수)
- `!` 강제 언래핑은 크래시 원인 1위 — `guard let`을 쓰세요
- 클로저를 오래 보관하면 `[weak self]` 필요 (JS엔 GC가 알아서 하던 것)
- **UI 상태는 메인 스레드에서만** — `@MainActor`
- View는 struct라 매번 새로 만들어짐 → 값 유지는 `@State`의 몫

## 부록: Android 트랙과의 대조표

Android도 할 계획이면 [Android 트랙 문서](./android-kotlin-compose.md)를 보세요.

| 개념 | iOS (이 문서) | Android |
|---|---|---|
| UI 프레임워크 | SwiftUI | Jetpack Compose |
| 언어 | Swift | Kotlin |
| 상수/변수 | `let` / `var` ⚠️ | `val` / `var` |
| 상태 | `@State` | `remember { mutableStateOf() }` |
| 저장되는 상태 | `@AppStorage` / `@SceneStorage` | `rememberSaveable` / DataStore |
| 부수 효과 | `.task` / `.onAppear` | `LaunchedEffect` |
| 세로 배치 | `VStack` | `Column` |
| 가로 배치 | `HStack` | `Row` |
| 겹치기 | `ZStack` | `Box` |
| 리스트 | `List` / `LazyVStack` | `LazyColumn` |
| 화면 상태 관리 | `@Observable` 클래스 | ViewModel + StateFlow |
| 네비게이션 | `NavigationStack` | Navigation Compose |
| 비동기 | `async` / `await` | `suspend` + 코루틴 |
| 네트워크 | URLSession (표준 내장) | Retrofit (외부 라이브러리) |
| 로컬 DB | SwiftData | Room |
| 설정 저장 | UserDefaults / `@AppStorage` | DataStore |
| 의존성 | Swift Package Manager | Gradle |
| 미리보기 | `#Preview` | `@Preview` |
| 안전 영역 | **기본이 안전 영역** (`.ignoresSafeArea()`로 해제) | 기본이 전체 화면 (`systemBarsPadding()` 필요) |
| 배포 | TestFlight → 심사(1~3일) → App Store | 내부테스트 → Play (심사 짧음) |
| 비용 | $99/년 | $25 (1회) |

**가장 큰 차이 3가지:**
1. **심사**: iOS는 사람이 직접 봅니다. 리젝을 전제로 일정을 잡으세요
2. **안전 영역 기본값이 정반대**입니다
3. **화면 회전**: Android는 화면을 파괴하고 재생성, iOS는 유지 → iOS가 훨씬 편합니다

## 유용한 링크

**공식**
- SwiftUI 튜토리얼: https://developer.apple.com/tutorials/swiftui
- Swift 언어 가이드: https://docs.swift.org/swift-book
- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines
- WWDC 영상: https://developer.apple.com/videos
- App Store 심사 지침: https://developer.apple.com/app-store/review/guidelines

**문법 연습**
- Swift Playgrounds 앱 (Mac/iPad, 무료)
- https://swiftfiddle.com

**도구**
- SF Symbols 앱 (아이콘 브라우저, 무료): https://developer.apple.com/sf-symbols
- OpenWeatherMap (무료 API): https://openweathermap.org/api

---

> **막히면**: JS 코드를 보여주면서 "이걸 SwiftUI로 어떻게 쓰나요?"라고 물어보세요.
> 이미 아는 개념에 이름표를 붙이는 방식이 가장 빠릅니다.
