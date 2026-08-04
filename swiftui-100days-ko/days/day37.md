# Day 37 — iExpense: onDelete와 Codable
> 원문: https://www.hackingwithswift.com/100/swiftui/37 (약 1시간)

## 오늘 배우는 것

- Identifiable 지출 모델로 목록 행의 정체성 보존하기: 공연 관람 지출의 담당 값을 코드에서 찾습니다.
- onDelete의 IndexSet을 배열 삭제에 적용하기: 입력 뒤 결과가 갱신되는 경로를 공연 관람 지출 사례로 추적합니다.
- Codable로 저장 가능한 데이터 표현 만들기: 문법 뒤에 경계 조건이 숨지 않는지 점검합니다.

## 핵심 개념 해설

### Identifiable 지출 모델로 목록 행의 정체성 보존하기

UUID는 같은 공연과 가격을 가진 두 구매도 서로 다른 행으로 구분해 삭제와 애니메이션의 대상을 안정적으로 찾습니다. 값이 만들어지는 지점, 수정 권한을 가진 코드, 최종 소비자를 순서대로 표시해 보세요. 공연 관람 지출처럼 익숙한 소재를 사용하면 문법보다 데이터 역할에 집중할 수 있습니다. 컴파일 성공이 도메인 규칙까지 보장하지는 않으므로 경계 입력도 함께 대입해야 합니다.

```swift
struct TicketExpense: Identifiable, Codable {
    var id = UUID()
    let show: String
    let price: Int
}
@State private var tickets = [TicketExpense]()

List {
    ForEach(tickets) { Text("\($0.show) · \($0.price)원") }
        .onDelete { tickets.remove(atOffsets: $0) }
}
```

코드는 원문 예제를 옮기지 않고 공연 관람 지출 상황에 맞춰 새로 작성했습니다. 저장된 원본과 계산되는 값, 동작 뒤 바뀌는 값을 구분해 보세요.

### onDelete의 IndexSet을 배열 삭제에 적용하기

onDelete가 넘기는 IndexSet은 현재 표시 순서의 위치이므로 필터링 목록이라면 원본 식별자로 삭제할지 별도 설계가 필요합니다. 값이 없거나 형식이 틀리거나 범위를 벗어난 경우도 살핍니다. 임의의 기본값이나 강제 언래핑은 실제 원인을 숨길 수 있습니다. 화면 상태는 최소로 저장하고 나머지는 원본에서 계산해야 모순을 예방할 수 있습니다.

리뷰할 때는 값의 소유자, 변경 사건, 실패 뒤 표시를 질문하세요. 오늘의 공연 관람 지출 예제에서는 Codable로 저장 가능한 데이터 표현 만들기이 그 접점입니다. 입력 타입과 출력 타입을 말로 이어 보면 판단 기준을 재사용할 수 있습니다.

## 읽고 나서 스스로 확인

1. 공연 관람 지출 예제에서 직접 저장된 값과 계산되거나 표현된 값은 각각 무엇인가요?

<details><summary>답 보기</summary>

선언부와 상태에서 시작해 연산 또는 뷰가 소비하는 곳까지 따라가세요. UUID는 같은 공연과 가격을 가진 두 구매도 서로 다른 행으로 구분해 삭제와 애니메이션의 대상을 안정적으로 찾습니다.

</details>

2. onDelete의 IndexSet을 배열 삭제에 적용하기 과정에서 가장 먼저 검사할 경계 조건은 무엇인가요?

<details><summary>답 보기</summary>

빈 입력, 허용 범위의 양 끝, 변환 실패 중 오늘 타입에 실제로 가능한 경우를 고릅니다. onDelete가 넘기는 IndexSet은 현재 표시 순서의 위치이므로 필터링 목록이라면 원본 식별자로 삭제할지 별도 설계가 필요합니다.

</details>

3. 공연 관람 지출 예제에서 iExpense: onDelete와 Codable의 책임을 더 나눈다면 어느 조각을 분리하겠나요?

<details><summary>답 보기</summary>

공연 관람 지출 흐름 중 입력과 출력이 분명한 부분이 후보입니다. iExpense: onDelete와 Codable에 필요한 원본 상태는 한곳에 남깁니다.

</details>

## 다음

Day 38에서는 오늘 만든 공연 관람 지출 예제의 관점을 다음 주제와 연결합니다.
