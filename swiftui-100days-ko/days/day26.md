# Day 26 — BetterRest: Stepper와 DatePicker
> 원문: https://www.hackingwithswift.com/100/swiftui/26 (약 1시간)

## 오늘 배우는 것

- Stepper로 원하는 수면 시간을 일정 간격으로 조절하기: 독서 마감 계획의 담당 값을 코드에서 찾습니다.
- DatePicker에서 시각 구성요소만 노출하기: 입력 뒤 결과가 갱신되는 경로를 독서 마감 계획 사례로 추적합니다.
- 날짜 범위를 제한해 불가능한 입력 차단하기: 문법 뒤에 경계 조건이 숨지 않는지 점검합니다.

## 핵심 개념 해설

### Stepper로 원하는 수면 시간을 일정 간격으로 조절하기

Stepper의 범위와 간격은 사용자가 만들 수 있는 값을 규칙 안으로 제한해 별도 오류 메시지를 줄입니다. 값이 만들어지는 지점, 수정 권한을 가진 코드, 최종 소비자를 순서대로 표시해 보세요. 독서 마감 계획처럼 익숙한 소재를 사용하면 문법보다 데이터 역할에 집중할 수 있습니다. 컴파일 성공이 도메인 규칙까지 보장하지는 않으므로 경계 입력도 함께 대입해야 합니다.

```swift
@State private var hours = 1.0
@State private var deadline = Date.now

Stepper("읽기 시간: \(hours.formatted())시간", value: $hours, in: 0.5...6, step: 0.5)
DatePicker("마감", selection: $deadline, in: Date.now..., displayedComponents: [.date, .hourAndMinute])
```

코드는 원문 예제를 옮기지 않고 독서 마감 계획 상황에 맞춰 새로 작성했습니다. 저장된 원본과 계산되는 값, 동작 뒤 바뀌는 값을 구분해 보세요.

### DatePicker에서 시각 구성요소만 노출하기

DatePicker는 Date 전체를 저장하되 displayedComponents로 이 계획에 필요한 날짜와 시각만 편집하게 합니다. 값이 없거나 형식이 틀리거나 범위를 벗어난 경우도 살핍니다. 임의의 기본값이나 강제 언래핑은 실제 원인을 숨길 수 있습니다. 화면 상태는 최소로 저장하고 나머지는 원본에서 계산해야 모순을 예방할 수 있습니다.

리뷰할 때는 값의 소유자, 변경 사건, 실패 뒤 표시를 질문하세요. 오늘의 독서 마감 계획 예제에서는 날짜 범위를 제한해 불가능한 입력 차단하는 과정이 그 접점입니다. 입력 타입과 출력 타입을 말로 이어 보면 판단 기준을 재사용할 수 있습니다.

## 읽고 나서 스스로 확인

1. 독서 마감 계획 예제에서 직접 저장된 값과 계산되거나 표현된 값은 각각 무엇인가요?

<details><summary>답 보기</summary>

선언부와 상태에서 시작해 연산 또는 뷰가 소비하는 곳까지 따라가세요. Stepper의 범위와 간격은 사용자가 만들 수 있는 값을 규칙 안으로 제한해 별도 오류 메시지를 줄입니다.

</details>

2. DatePicker에서 시각 구성요소만 노출하기 과정에서 가장 먼저 검사할 경계 조건은 무엇인가요?

<details><summary>답 보기</summary>

빈 입력, 허용 범위의 양 끝, 변환 실패 중 오늘 타입에 실제로 가능한 경우를 고릅니다. DatePicker는 Date 전체를 저장하되 displayedComponents로 이 계획에 필요한 날짜와 시각만 편집하게 합니다.

</details>

3. 독서 마감 계획 예제에서 BetterRest: Stepper와 DatePicker의 책임을 더 나눈다면 어느 조각을 분리하겠나요?

<details><summary>답 보기</summary>

독서 마감 계획 흐름 중 입력과 출력이 분명한 부분이 후보입니다. BetterRest: Stepper와 DatePicker에 필요한 원본 상태는 한곳에 남깁니다.

</details>

## 다음

Day 27에서는 오늘 만든 독서 마감 계획 예제의 관점을 다음 주제와 연결합니다.
