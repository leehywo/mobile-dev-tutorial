# 모바일 앱 개발 튜토리얼

> **React/JavaScript 개발자**가 모바일(그리고 게임) 개발로 확장하기 위한 한국어 튜토리얼 시리즈.
> 모든 문서가 같은 교수법을 씁니다 — **아는 것(JS/React)과 1:1로 비교**하며 배우고,
> **동일한 샘플 앱을 단계별로 완성**하며 트랙 간 차이를 몸으로 익힙니다.

## 튜토리얼 트랙

| 트랙 | 문서 | 기술 스택 | 이런 사람에게 |
|------|------|----------|--------------|
| 🤖 **Android** | [android-kotlin-compose.md](./android-kotlin-compose.md) | Kotlin + Jetpack Compose | Mac 없이 시작 가능. 출시 비용 저렴($25 1회), 심사 빠름 |
| 🍎 **iOS** | [ios-swift-swiftui.md](./ios-swift-swiftui.md) | Swift + SwiftUI | **Mac 필수**. 수익성·UX 완성도 높고 고유 기능(Live Activity 등)이 강력 |
| ⚛️ **React Native** | [react-to-react-native.md](./react-to-react-native.md) | TypeScript + Expo + expo-router | React 지식 최대 재사용, 한 코드로 iOS+Android 빠른 출시 |
| 🎮 **Unity** | [react-to-unity.md](./react-to-unity.md) | C# + Unity 6 (UI Toolkit / UGUI) | 게임·인터랙티브 콘텐츠·AR/VR이 목표 |

## 트랙 선택 가이드

```
만들려는 게 무엇인가요?

게임 / 3D / AR·VR / 물리·애니메이션 중심 콘텐츠
  → 🎮 Unity 트랙 (고민할 것 없이 이것)

폼·리스트·네비게이션 중심의 "일반 앱"
  ├─ 빨리 출시하고 싶다, React 지식을 그대로 쓰고 싶다
  │    → ⚛️ React Native 트랙 (추천 시작점)
  └─ 위젯·백그라운드 서비스 등 OS 깊은 기능이 필요하다,
     또는 네이티브 개발 자체를 배우고 싶다
       ├─ Mac이 없다 / 안드로이드 유저다  → 🤖 Android 트랙
       └─ Mac이 있다 / 아이폰 유저다       → 🍎 iOS 트랙

아직 모르겠다
  → React 개발자라면 RN 트랙으로 시작하세요. 진입 장벽이 가장 낮고,
    RN을 하다 보면 네이티브가 필요한 지점을 자연스럽게 만나게 됩니다.
```

### 네이티브 두 트랙 비교

| | 🤖 Android | 🍎 iOS |
|---|---|---|
| 개발 OS | Windows / macOS / Linux | **macOS만** |
| 계정 비용 | $25 (1회) | $99/년 |
| 심사 | 자동 위주, 보통 수시간~1일 | **사람이 직접 심사**, 1~3일 + 리젝 가능성 |
| 첫 출시 난이도 | 중 (신규 개인 계정은 테스터 요건 있음) | 중~상 (심사 가이드라인) |
| 언어 함정 | 적음 (`val`/`var`가 JS와 감각 동일) | `let` = JS의 `const` ⚠️ |
| 상태 관리 | ViewModel + StateFlow | `@Observable` + 프로퍼티 래퍼 |
| 화면 회전 | Activity 재생성 → 상태 소실 주의 | 상태 유지됨 (편함) |
| 고유 기능 ROI | App Widget (Glance) | Live Activity / Dynamic Island |

> **둘 다 할 계획이라면**: 한쪽을 끝까지 한 뒤 다른 쪽을 보세요. 두 번째 트랙은
> 개념이 이미 머리에 있어서 보통 절반 이하 시간(15~20시간)이면 됩니다.
> 각 문서 PART 5 끝의 **대조표 부록**이 개념 매핑을 정리해둡니다.

## 공통 학습 설계

네 트랙 모두 같은 구조로 진행됩니다. 두 번째 트랙부터는 "아, 그거"의 연속이라 훨씬 빠릅니다.

```
PART 0  개발 환경 세팅 (설치 확인 체크리스트, 빌드 도구 개념)
PART 1  언어 문법 — JS/TS와 나란히 비교 (Kotlin / Swift / C#)
PART 2  매핑 치트시트 — useState는 여기서 뭐지? 를 표로
PART 3  샘플 앱 단계별 완성
         카운터 → 상태관리 → 할 일 목록 → 날씨 앱(API) → 메모 앱(DB·이미지·테마)
PART 4  실전 — 디버깅·권한·인앱결제/구독·릴리즈·테스트·접근성·성능·스토어 출시·지뢰 모음
PART 5  학습 로드맵 (Claude 어시스트 Fast-track 포함) + 다른 트랙 대조표
```

## 환경 요구사항 요약

| | 🤖 Android | 🍎 iOS | ⚛️ React Native | 🎮 Unity |
|---|---|---|---|---|
| 개발 OS | 모든 OS | **macOS 필수** | 개발은 모든 OS, iOS 빌드는 macOS 또는 EAS 클라우드 | 모든 OS (iOS 빌드는 macOS) |
| 도구 | Android Studio | Xcode | Node + Expo | Unity Hub |
| 디스크 여유 | ~20GB | ~40GB | ~5GB | ~20GB |
| 유료 계정 | Google Play $25(1회) | Apple $99/년 | 출시하는 스토어에 따라 | 동일 (Unity Personal 무료) |

> ⚡ 각 문서 상단의 **Claude 어시스트 Fast-track**을 활용하면 네이티브 트랙당 6~9시간,
> AI 없이 전통적으로 학습하면 트랙당 30~45시간 정도입니다.

## 라이선스

[MIT](./LICENSE) © leehywo
