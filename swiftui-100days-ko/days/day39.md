# Day 39 — Moonshot: Codable 계층과 GeometryReader
> 원문: https://www.hackingwithswift.com/100/swiftui/39 (약 1시간)

## 오늘 배우는 것

- 중첩 JSON을 Codable 구조체 계층으로 모델링하기: 박물관 전시 데이터의 담당 값을 코드에서 찾습니다.
- Dictionary 값의 연관 ID를 다른 모델과 연결하기: 입력 뒤 결과가 갱신되는 경로를 박물관 전시 데이터 사례로 추적합니다.
- GeometryReader로 컨테이너 폭에 맞춘 이미지 크기 구하기: 문법 뒤에 경계 조건이 숨지 않는지 점검합니다.

## 핵심 개념 해설

### 중첩 JSON을 Codable 구조체 계층으로 모델링하기

Codable 계층은 JSON의 전시 안에 유물 배열이 들어 있는 구조를 그대로 반영해 디코딩 뒤에도 관계를 잃지 않습니다. 값이 만들어지는 지점, 수정 권한을 가진 코드, 최종 소비자를 순서대로 표시해 보세요. 박물관 전시 데이터처럼 익숙한 소재를 사용하면 문법보다 데이터 역할에 집중할 수 있습니다. 컴파일 성공이 도메인 규칙까지 보장하지는 않으므로 경계 입력도 함께 대입해야 합니다.

```swift
struct Exhibit: Codable, Identifiable {
    let id: Int
    let title: String
    let artifacts: [Artifact]
}
struct Artifact: Codable, Identifiable { let id: Int; let name: String }

GeometryReader { proxy in
    Image("museum-hall").resizable().scaledToFit().frame(width: proxy.size.width)
}
```

코드는 원문 예제를 옮기지 않고 박물관 전시 데이터 상황에 맞춰 새로 작성했습니다. 저장된 원본과 계산되는 값, 동작 뒤 바뀌는 값을 구분해 보세요.

### Dictionary 값의 연관 ID를 다른 모델과 연결하기

GeometryReader가 알려 주는 폭은 기기 전체가 아니라 부모가 제안한 공간이므로 그 값을 기준으로 이미지 크기를 정합니다. 값이 없거나 형식이 틀리거나 범위를 벗어난 경우도 살핍니다. 임의의 기본값이나 강제 언래핑은 실제 원인을 숨길 수 있습니다. 화면 상태는 최소로 저장하고 나머지는 원본에서 계산해야 모순을 예방할 수 있습니다.

리뷰할 때는 값의 소유자, 변경 사건, 실패 뒤 표시를 질문하세요. 오늘의 박물관 전시 데이터 예제에서는 GeometryReader로 컨테이너 폭에 맞춘 이미지 크기 구하는 과정이 그 접점입니다. 입력 타입과 출력 타입을 말로 이어 보면 판단 기준을 재사용할 수 있습니다.

## 읽고 나서 스스로 확인

1. 박물관 전시 데이터 예제에서 직접 저장된 값과 계산되거나 표현된 값은 각각 무엇인가요?

<details><summary>답 보기</summary>

선언부와 상태에서 시작해 연산 또는 뷰가 소비하는 곳까지 따라가세요. Codable 계층은 JSON의 전시 안에 유물 배열이 들어 있는 구조를 그대로 반영해 디코딩 뒤에도 관계를 잃지 않습니다.

</details>

2. Dictionary 값의 연관 ID를 다른 모델과 연결하기 과정에서 가장 먼저 검사할 경계 조건은 무엇인가요?

<details><summary>답 보기</summary>

빈 입력, 허용 범위의 양 끝, 변환 실패 중 오늘 타입에 실제로 가능한 경우를 고릅니다. GeometryReader가 알려 주는 폭은 기기 전체가 아니라 부모가 제안한 공간이므로 그 값을 기준으로 이미지 크기를 정합니다.

</details>

3. 박물관 전시 데이터 예제에서 Moonshot: Codable 계층과 GeometryReader의 책임을 더 나눈다면 어느 조각을 분리하겠나요?

<details><summary>답 보기</summary>

박물관 전시 데이터 흐름 중 입력과 출력이 분명한 부분이 후보입니다. Moonshot: Codable 계층과 GeometryReader에 필요한 원본 상태는 한곳에 남깁니다.

</details>

## 다음

Day 40에서는 오늘 만든 박물관 전시 데이터 예제의 관점을 다음 주제와 연결합니다.
