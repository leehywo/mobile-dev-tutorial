# 모바일 앱 개발 튜토리얼

> **React/JavaScript 개발자**가 모바일(그리고 게임) 개발로 확장하기 위한 한국어 튜토리얼 시리즈.
> 모든 문서가 같은 교수법을 씁니다 — **아는 것(JS/React)과 1:1로 비교**하며 배우고,
> **동일한 샘플 앱을 단계별로 완성**하며 트랙 간 차이를 몸으로 익힙니다.

## 튜토리얼 트랙

| 트랙 | 문서 | 기술 스택 | 이런 사람에게 |
|------|------|----------|--------------|
| 🤖🍎 **네이티브** | [native-android-ios.md](./native-android-ios.md) | Kotlin + Jetpack Compose / Swift + SwiftUI | 플랫폼 고유 기능·최고 성능·네이티브 커리어가 목표 |
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
       → 🤖🍎 네이티브 트랙

아직 모르겠다
  → React 개발자라면 RN 트랙으로 시작하세요. 진입 장벽이 가장 낮고,
    RN을 하다 보면 네이티브가 필요한 지점(각 문서의 "네이티브가 필요할 때" 참고)을
    자연스럽게 만나게 됩니다.
```

## 공통 학습 설계

세 트랙 모두 같은 구조로 진행됩니다. 두 번째 트랙부터는 "아, 그거"의 연속이라 훨씬 빠릅니다.

```
PART 0  개발 환경 세팅 (설치 확인 체크리스트 포함)
PART 1  언어 문법 — JS/TS와 나란히 비교 (Kotlin·Swift / C#)
PART 2  매핑 치트시트 — useState는 여기서 뭐지? 를 표로
PART 3  샘플 앱 4종 단계별 완성
         카운터 → 할 일 목록 → 날씨 앱(API·비동기) → 완성형(저장·심화)
PART 4  실전 — 디버깅·권한·광고(AdMob)·빌드·출시
PART 5  흔한 지뢰 & 학습 로드맵 (Claude 어시스트 Fast-track 포함)
```

## 환경 요구사항 요약

| | 네이티브 | React Native | Unity |
|---|---|---|---|
| Android 개발 | 모든 OS (Android Studio) | 모든 OS (Expo) | 모든 OS (Unity Hub) |
| iOS 개발/빌드 | **macOS 필수** (Xcode) | 개발은 모든 OS, 빌드는 macOS 또는 EAS 클라우드 | **macOS 필수** (Xcode) |
| 디스크 여유 | ~20GB | ~5GB | ~20GB |
| 유료 계정 | Google Play $25(1회) / Apple $99(년) — 출시 시에만 | 동일 | 동일 (Unity Personal은 무료) |

> ⚡ 각 문서 상단의 **Claude 어시스트 Fast-track**을 활용하면 트랙당 8~18시간에 완주할 수 있습니다.

## 라이선스

[MIT](./LICENSE) © leehywo
