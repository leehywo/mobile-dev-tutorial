# React 개발자를 위한 React Native 튜토리얼 (완전판)

> **이미 React를 아는 웹 개발자**가 React Native(RN)로 iOS·Android 앱을 만들기 위한 입문서.
> 새 언어를 배우는 게 아닙니다 — **RN은 그냥 React입니다.** 컴포넌트·props·state·hooks 다 그대로.
> 바뀌는 건 "DOM 엘리먼트(`<div>`) → 네이티브 엘리먼트(`<View>`)"와 모바일 특유의 것 몇 가지뿐.
>
> 같은 시리즈의 [네이티브 전환 튜토리얼(README.md)](./README.md)이 "JS 개발자 → Swift/Kotlin"이라면,
> 이 문서는 "React 개발자 → RN"입니다. **하나의 코드로 iOS+Android 동시 출시**가 목표.

---

## 목차

- PART 0: 개발 환경 세팅
- PART 1: 멘탈 모델 — 아는 것 vs 달라지는 것
- PART 2: React(웹) → RN 매핑 치트시트
- PART 3: 샘플 앱 4종 만들기 (카운터 → 할일 → 날씨 → 메모)
- PART 4: 실전 (디버깅·권한·광고·출시)
- PART 5: React 개발자가 자주 밟는 지뢰 10가지
- 부록: 다음 단계 & 리소스

---

# PART 0: 개발 환경 세팅

웹과 거의 같습니다. Node만 있으면 시작하고, 폰만 있으면 실기 테스트가 됩니다.

## 0-1. 필수 도구

```bash
# Node.js (LTS 18+ 권장) — nvm으로 관리 추천
node -v   # v18 이상이면 OK

# 패키지 매니저는 npm/yarn/pnpm 아무거나. 이 문서는 npm 기준.
```

- **VS Code** + 확장: "ESLint", "Prettier", "React Native Tools"(선택)
- **Expo Go 앱** (App Store / Play Store에서 설치) — 폰에서 코드를 즉시 실행하는 런처. **에뮬레이터 없이 실기 핫리로드** 가능 = RN 최대 장점.
- (선택) **Xcode** (iOS 시뮬레이터용, macOS만) / **Android Studio** (에뮬레이터용)

> 💡 처음엔 시뮬레이터/에뮬레이터 없이 **본인 폰 + Expo Go**만으로 충분합니다. 웹의 `localhost`를 폰에서 여는 느낌.

## 0-2. Expo란? (그리고 왜 Expo로 시작하나)

- **Expo** = RN 위의 "Next.js/CRA 같은 프레임워크 + 툴체인". 네이티브 빌드 설정(Xcode 프로젝트, Gradle)을 추상화해줍니다.
- 카메라·알림·저장소·위치 등 네이티브 기능을 **JS API로** 바로 씀 (`expo-camera`, `expo-notifications`...).
- 출시는 **EAS(Expo Application Services)** 가 클라우드에서 빌드/서명/스토어 업로드까지 대행.
- "순수 RN(RN CLI)"도 있지만, 1인/소규모는 **Expo가 정답**. 필요하면 나중에 네이티브 코드도 섞을 수 있음(`expo prebuild`).

## 0-3. 첫 프로젝트 생성

```bash
# TypeScript + expo-router(파일 기반 라우팅) 템플릿
npx create-expo-app@latest myapp
cd myapp

# 실행
npx expo start
```

- 터미널에 **QR 코드**가 뜹니다. 폰의 Expo Go(안드로이드) / 카메라(iOS)로 스캔 → 앱이 폰에서 실행.
- 시뮬레이터로 열려면 터미널에서 `i`(iOS) / `a`(Android).
- 코드 저장 → **즉시 핫리로드** (웹 HMR과 동일 경험).

생성되는 구조 (Expo Router 기준):

```
myapp/
├── app/                  # 파일 = 라우트 (Next.js App Router랑 비슷)
│   ├── _layout.tsx       # 공통 레이아웃 (네비게이터)
│   ├── index.tsx         # "/" 화면
│   └── (tabs)/           # 탭 그룹
├── components/           # 재사용 컴포넌트
├── assets/               # 이미지·폰트
├── package.json
├── app.json              # 앱 설정(이름·아이콘·번들ID·권한)
└── tsconfig.json
```

> React 웹의 `src/` 대신 `app/`이 라우트. `<a href>` 대신 파일이 곧 화면.

---

# PART 1: 멘탈 모델 — 아는 것 vs 달라지는 것

## ✅ 그대로인 것 (React 지식 100% 재사용)

- 함수 컴포넌트, JSX, props, `children`
- `useState`, `useEffect`, `useRef`, `useMemo`, `useCallback`, `useContext`, 커스텀 훅
- 단방향 데이터 흐름, "상태가 바뀌면 리렌더"
- 컴포넌트 합성, 조건부 렌더링 `{cond && <X/>}`, 리스트 `arr.map(...)`
- TypeScript, ESLint, async/await, fetch
- 상태관리 라이브러리: **Zustand / Redux / React Query 그대로 작동** (DOM 의존 없는 것들)
- Context, Error Boundary, Suspense(일부)

## ⚠️ 달라지는 것

| 영역 | 웹 React | React Native |
|------|----------|--------------|
| 기본 엘리먼트 | `<div> <span> <p> <img> <button>` | `<View> <Text> <Image> <Pressable>` |
| 텍스트 | 아무 데나 글자 OK | **글자는 반드시 `<Text>` 안에** |
| 스타일 | CSS / className | `StyleSheet` 객체 (JS) |
| 레이아웃 | display 다양, 기본 block | **전부 Flexbox**, 기본 방향 `column` |
| 단위 | px, rem, % | 숫자(=dp), %, flex |
| 이벤트 | `onClick`, `onChange` | `onPress`, `onChangeText` |
| 스크롤 | 자동(overflow) | `<ScrollView>` / `<FlatList>` 명시 |
| 라우팅 | react-router / URL | expo-router(파일) / React Navigation |
| 저장소 | localStorage | `AsyncStorage` (비동기!) |
| 네트워크 | fetch (그대로) | fetch (그대로) ✅ |
| DOM API | `document`, `window` | **없음** (querySelector 등 X) |
| CSS 상속/캐스케이드 | 있음 | **없음** (스타일 상속 거의 없음) |

핵심 한 줄: **"DOM이 사라지고 네이티브 뷰로 바뀐 React"**. 로직은 그대로, 그리는 도구만 교체.

---

# PART 2: React(웹) → RN 매핑 치트시트

필요할 때 찾아보는 페이지. 외우지 말고 참고.

## 2-1. 엘리먼트 매핑

| 웹 | RN | 비고 |
|----|----|------|
| `<div>` | `<View>` | 레이아웃 컨테이너 |
| `<span> <p> <h1>` | `<Text>` | **모든 텍스트** |
| `<img src>` | `<Image source>` | 로컬은 `require()`, 원격은 `{uri}` |
| `<button> <a>` | `<Pressable>` (또는 `<TouchableOpacity>`) | `onPress` |
| `<input>` | `<TextInput>` | `onChangeText` |
| `<ul>/<ol>` 큰 리스트 | `<FlatList>` | 가상화(성능) |
| 스크롤 영역 | `<ScrollView>` | 적은 콘텐츠용 |
| `<select>` | `@react-native-picker/picker` | 별도 패키지 |
| `<input type=checkbox>` | `<Switch>` / `expo-checkbox` | |
| Modal/Portal | `<Modal>` | 내장 |
| `<SafeArea>` 개념 | `react-native-safe-area-context` | 노치/홈바 회피 |

## 2-2. 스타일 매핑

```tsx
// 웹: <div className="card"> + CSS
// RN: StyleSheet 객체
import { StyleSheet, View, Text } from 'react-native';

function Card() {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>안녕</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,              // px 안 붙임 (숫자 = dp)
    backgroundColor: '#fff',  // background-color → backgroundColor (카멜케이스)
    borderRadius: 12,
    // flex 레이아웃이 기본
    flexDirection: 'row',     // 기본값은 'column'(웹과 반대!)
    alignItems: 'center',
    gap: 8,
  },
  title: { fontSize: 18, fontWeight: '700', color: '#111' },
});
```

규칙:
- 속성명 **카멜케이스** (`background-color` → `backgroundColor`).
- 값은 **숫자(dp)** 또는 문자열. `'16px'` 아니고 `16`.
- **상속 없음**: 부모 `<View>`에 `color` 줘도 자식 `<Text>`에 안 내려감. 텍스트 스타일은 `<Text>`에 직접.
- 동적 스타일: `style={[styles.box, isActive && styles.active]}` (배열 합성).
- `className` 같은 유틸을 원하면 **NativeWind**(Tailwind for RN) 사용 가능.

## 2-3. Flexbox 차이 (가장 자주 헷갈림)

| | 웹 CSS | RN |
|--|--------|----|
| 기본 방향 | `row` | **`column`** |
| display | 여러 종류 | 항상 flex (display 안 씀) |
| flex 축약 | `flex: 1 1 auto` | `flex: 1` (숫자) |
| 세로 가운데 | `align-items` | 동일 |
| 가로 가운데 | `justify-content` | 동일(방향 주의) |

```tsx
// 화면 꽉 채우고 정중앙
<View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
  <Text>가운데</Text>
</View>
```

## 2-4. 이벤트 매핑

| 웹 | RN |
|----|----|
| `onClick` | `onPress` |
| `onChange` (input) | `onChangeText` (값이 바로 string으로 옴) |
| `onSubmit` | `onSubmitEditing` (TextInput) |
| `onMouseEnter` 등 | 없음(터치 기반) — `onPressIn/Out`, 제스처 |
| `e.preventDefault()` | 대개 불필요 |

```tsx
// 웹: <input value={t} onChange={e => setT(e.target.value)} />
<TextInput value={t} onChangeText={setT} placeholder="입력..." />

// 웹: <button onClick={save}>저장</button>
<Pressable onPress={save}><Text>저장</Text></Pressable>
```

## 2-5. 라우팅 매핑 (expo-router)

파일 기반(Next.js App Router와 거의 동일):

```
app/
├── _layout.tsx        # 루트 레이아웃 (Stack/Tabs 정의)
├── index.tsx          # "/"
├── settings.tsx       # "/settings"
└── item/[id].tsx      # "/item/123" (동적)
```

```tsx
// 이동: 웹의 navigate('/settings') 대신
import { router, Link } from 'expo-router';
router.push('/settings');
router.push(`/item/${id}`);

// 선언형 링크 (웹 <Link href>와 동일)
<Link href="/settings"><Text>설정</Text></Link>

// 파라미터 받기: 웹 useParams() 대신
import { useLocalSearchParams } from 'expo-router';
const { id } = useLocalSearchParams();
```

```tsx
// app/_layout.tsx — 네비게이터 정의
import { Stack } from 'expo-router';
export default function Layout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: '홈' }} />
      <Stack.Screen name="settings" options={{ title: '설정' }} />
    </Stack>
  );
}
```

## 2-6. 저장소 / 네트워크 / 상태

| 웹 | RN |
|----|----|
| `localStorage.setItem` (동기) | `AsyncStorage.setItem` (**비동기**, await) |
| `fetch()` | `fetch()` 동일 ✅ |
| `axios` | 동일 ✅ |
| React Query | 동일 ✅ |
| Zustand / Redux | 동일 ✅ |
| 환경변수 `process.env.X` | `process.env.EXPO_PUBLIC_X` (빌드시 인라인) |

```tsx
import AsyncStorage from '@react-native-async-storage/async-storage';
// 웹: localStorage.setItem('k', JSON.stringify(v))
await AsyncStorage.setItem('k', JSON.stringify(v));
// 웹: const v = JSON.parse(localStorage.getItem('k'))
const raw = await AsyncStorage.getItem('k');
const v = raw ? JSON.parse(raw) : null;
```

---

# PART 3: 샘플 앱 4종 만들기

[네이티브 튜토리얼](./README.md)과 **같은 앱들**을 RN으로. 비교하며 보면 "RN이 얼마나 React 그대로인지" 체감됩니다.

## STEP 1: Hello World + 카운터

**목표**: 화면·텍스트·버튼·state 첫 경험.

```tsx
// app/index.tsx
import { useState } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';

export default function Home() {
  // 웹과 100% 동일
  const [count, setCount] = useState(0);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Hello, React Native 👋</Text>
      <Text style={styles.count}>{count}</Text>

      <View style={styles.row}>
        <Pressable style={styles.btn} onPress={() => setCount(c => c - 1)}>
          <Text style={styles.btnText}>-</Text>
        </Pressable>
        <Pressable style={styles.btn} onPress={() => setCount(c => c + 1)}>
          <Text style={styles.btnText}>+</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 20 },
  title: { fontSize: 22, fontWeight: '700' },
  count: { fontSize: 64, fontWeight: '800', color: '#6366F1' },
  row: { flexDirection: 'row', gap: 16 },
  btn: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#6366F1',
         justifyContent: 'center', alignItems: 'center' },
  btnText: { color: '#fff', fontSize: 28, fontWeight: '800' },
});
```

> 보다시피 로직(`useState`, 핸들러)은 웹과 글자 하나 안 다릅니다. `<div>`→`<View>`, `<button onClick>`→`<Pressable onPress>`, CSS→`StyleSheet`만 바뀜.

## STEP 2: 할 일 목록 (리스트·입력·CRUD)

**목표**: `FlatList`, `TextInput`, 불변 업데이트.

```tsx
// app/todo.tsx
import { useState } from 'react';
import { View, Text, TextInput, Pressable, FlatList, StyleSheet } from 'react-native';

type Todo = { id: string; title: string; done: boolean };

export default function TodoScreen() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [input, setInput] = useState('');

  const add = () => {
    const t = input.trim();
    if (!t) return;
    // 웹과 동일한 불변 업데이트
    setTodos(prev => [{ id: String(Date.now()), title: t, done: false }, ...prev]);
    setInput('');
  };
  const toggle = (id: string) =>
    setTodos(prev => prev.map(t => (t.id === id ? { ...t, done: !t.done } : t)));
  const remove = (id: string) =>
    setTodos(prev => prev.filter(t => t.id !== id));

  return (
    <View style={styles.root}>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="할 일 입력..."
          onSubmitEditing={add}          // 키보드 엔터로 추가
          returnKeyType="done"
        />
        <Pressable style={styles.addBtn} onPress={add}>
          <Text style={styles.addTxt}>추가</Text>
        </Pressable>
      </View>

      <FlatList
        data={todos}
        keyExtractor={t => t.id}          // 웹의 key={t.id}
        renderItem={({ item }) => (       // 웹의 todos.map(item => ...)
          <View style={styles.item}>
            <Pressable onPress={() => toggle(item.id)} style={{ flex: 1 }}>
              <Text style={[styles.itemTxt, item.done && styles.done]}>
                {item.done ? '✅ ' : '⬜️ '}{item.title}
              </Text>
            </Pressable>
            <Pressable onPress={() => remove(item.id)}>
              <Text style={styles.del}>🗑️</Text>
            </Pressable>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>할 일이 없어요</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16, gap: 12 },
  inputRow: { flexDirection: 'row', gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: '#ddd', borderRadius: 10,
           paddingHorizontal: 12, height: 44 },
  addBtn: { paddingHorizontal: 16, justifyContent: 'center',
            backgroundColor: '#6366F1', borderRadius: 10 },
  addTxt: { color: '#fff', fontWeight: '700' },
  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12,
          borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  itemTxt: { fontSize: 16 },
  done: { textDecorationLine: 'line-through', color: '#aaa' },
  del: { fontSize: 18, paddingLeft: 12 },
  empty: { textAlign: 'center', color: '#999', marginTop: 40 },
});
```

> `FlatList`는 웹의 `.map()`보다 강력 — 화면 밖 항목을 **가상화**해서 수천 개도 부드럽게. 적은 리스트면 `ScrollView` + `.map()`도 OK.

## STEP 3: 날씨 앱 (API·비동기·로딩/에러)

**목표**: `fetch`(웹과 동일), 로딩/에러 UI, `useEffect`.

```tsx
// app/weather.tsx
import { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, Pressable, StyleSheet } from 'react-native';

type Weather = { temp: number; city: string };

export default function WeatherScreen() {
  const [data, setData] = useState<Weather | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      // fetch는 웹과 완전히 동일
      const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=37.57&longitude=126.98&current=temperature_2m');
      if (!res.ok) throw new Error('네트워크 오류');
      const json = await res.json();
      setData({ temp: json.current.temperature_2m, city: '서울' });
    } catch (e: any) {
      setError(e.message ?? '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);   // 웹과 동일

  if (loading) return <Centered><ActivityIndicator size="large" /></Centered>;
  if (error)
    return (
      <Centered>
        <Text style={styles.err}>{error}</Text>
        <Pressable style={styles.retry} onPress={load}>
          <Text style={styles.retryTxt}>다시 시도</Text>
        </Pressable>
      </Centered>
    );

  return (
    <Centered>
      <Text style={styles.city}>{data!.city}</Text>
      <Text style={styles.temp}>{data!.temp}°</Text>
      <Pressable style={styles.retry} onPress={load}>
        <Text style={styles.retryTxt}>새로고침</Text>
      </Pressable>
    </Centered>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <View style={styles.center}>{children}</View>;
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 },
  city: { fontSize: 24, color: '#555' },
  temp: { fontSize: 80, fontWeight: '800', color: '#6366F1' },
  err: { color: '#EF4444', fontSize: 16 },
  retry: { backgroundColor: '#6366F1', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 10 },
  retryTxt: { color: '#fff', fontWeight: '700' },
});
```

> 실무에선 `@tanstack/react-query`를 그대로 써서 로딩/에러/캐시를 자동화하면 됩니다(웹과 동일 API).

## STEP 4: 메모 앱 (영구 저장 + 화면 전환)

**목표**: `AsyncStorage`(비동기 localStorage), expo-router 화면 이동.

```tsx
// lib/storage.ts — 저장 로직 분리 (웹의 localStorage 래퍼와 동일 패턴)
import AsyncStorage from '@react-native-async-storage/async-storage';

export type Memo = { id: string; text: string; at: number };
const KEY = 'memos';

export async function loadMemos(): Promise<Memo[]> {
  const raw = await AsyncStorage.getItem(KEY);
  return raw ? JSON.parse(raw) : [];
}
export async function saveMemos(memos: Memo[]): Promise<void> {
  await AsyncStorage.setItem(KEY, JSON.stringify(memos));
}
```

```tsx
// app/memo/index.tsx — 목록
import { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, Pressable, StyleSheet } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { loadMemos, Memo } from '../../lib/storage';

export default function MemoList() {
  const [memos, setMemos] = useState<Memo[]>([]);

  // 화면이 다시 포커스될 때마다 재로드 (작성 후 돌아오면 갱신)
  useFocusEffect(useCallback(() => { loadMemos().then(setMemos); }, []));

  return (
    <View style={styles.root}>
      <FlatList
        data={memos}
        keyExtractor={m => m.id}
        renderItem={({ item }) => (
          <Pressable style={styles.card} onPress={() => router.push(`/memo/${item.id}`)}>
            <Text numberOfLines={2} style={styles.txt}>{item.text}</Text>
          </Pressable>
        )}
        ListEmptyComponent={<Text style={styles.empty}>메모 없음 — + 로 추가</Text>}
      />
      <Pressable style={styles.fab} onPress={() => router.push('/memo/new')}>
        <Text style={styles.fabTxt}>＋</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16 },
  card: { padding: 16, backgroundColor: '#fff', borderRadius: 12, marginBottom: 10,
          borderWidth: 1, borderColor: '#eee' },
  txt: { fontSize: 16 },
  empty: { textAlign: 'center', color: '#999', marginTop: 60 },
  fab: { position: 'absolute', right: 20, bottom: 30, width: 60, height: 60, borderRadius: 30,
         backgroundColor: '#6366F1', justifyContent: 'center', alignItems: 'center' },
  fabTxt: { color: '#fff', fontSize: 32, marginTop: -2 },
});
```

```tsx
// app/memo/new.tsx — 작성
import { useState } from 'react';
import { View, TextInput, Pressable, Text, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import { loadMemos, saveMemos } from '../../lib/storage';

export default function NewMemo() {
  const [text, setText] = useState('');
  const save = async () => {
    if (!text.trim()) return router.back();
    const memos = await loadMemos();
    await saveMemos([{ id: String(Date.now()), text: text.trim(), at: Date.now() }, ...memos]);
    router.back();   // 웹의 navigate(-1)
  };
  return (
    <View style={styles.root}>
      <TextInput
        style={styles.input}
        value={text}
        onChangeText={setText}
        placeholder="메모 작성..."
        multiline
        autoFocus
      />
      <Pressable style={styles.save} onPress={save}>
        <Text style={styles.saveTxt}>저장</Text>
      </Pressable>
    </View>
  );
}
const styles = StyleSheet.create({
  root: { flex: 1, padding: 16, gap: 12 },
  input: { flex: 1, fontSize: 17, textAlignVertical: 'top' },
  save: { backgroundColor: '#6366F1', padding: 16, borderRadius: 12, alignItems: 'center' },
  saveTxt: { color: '#fff', fontWeight: '700', fontSize: 16 },
});
```

> 이 4개를 만들면 RN 앱의 90%(화면·상태·리스트·입력·네트워크·저장·네비게이션)를 다룬 겁니다.

---

# PART 4: 실전 (출시 전 알아둘 것)

## 4-1. 디버깅

- `console.log` → 터미널(메트로) + 폰 흔들기 → "Open JS Debugger"로 Chrome/RN DevTools.
- **React DevTools** 그대로 작동: `npx react-devtools`.
- 에러는 빨간 화면(redbox)으로 스택과 함께 표시.
- 네트워크 디버깅: `npx expo start` → `j`로 디버거.

## 4-2. 권한 (Permissions)

웹의 권한 prompt와 달리, 모바일은 **사용 설명 문구**가 필수(없으면 크래시/리젝).

```tsx
// 예: 카메라
import { useCameraPermissions } from 'expo-camera';
const [perm, requestPerm] = useCameraPermissions();
if (!perm?.granted) {
  await requestPerm();   // OS 권한 팝업
}
```

```jsonc
// app.json — iOS 권한 설명 문구 (없으면 심사 리젝/크래시)
{
  "expo": {
    "ios": {
      "infoPlist": {
        "NSCameraUsageDescription": "QR 스캔을 위해 카메라를 사용합니다."
      }
    },
    "android": { "permissions": ["CAMERA"] }
  }
}
```

## 4-3. 다국어 (i18n) — 한국=한국어, 해외=영어

```tsx
// lib/i18n.ts
import { NativeModules, Platform } from 'react-native';
function deviceLang(): 'ko' | 'en' {
  let loc = 'en';
  if (Platform.OS === 'ios') loc = NativeModules.SettingsManager?.settings?.AppleLanguages?.[0] ?? 'en';
  else loc = NativeModules.I18nManager?.localeIdentifier ?? 'en';
  return loc.toLowerCase().startsWith('ko') ? 'ko' : 'en';
}
export const LANG = deviceLang();
const S = { save: { ko: '저장', en: 'Save' } } as const;
export const t = (k: keyof typeof S) => S[k][LANG];
```

> 🪤 **iOS 함정**: `app.json`의 `ios.infoPlist.CFBundleLocalizations: ["en","ko"]`를 선언하지 않으면, 한국어 폰에서도 앱은 영어로 뜹니다(OS가 "지원 언어"로 교집합하기 때문). 다국어 앱은 이 선언 필수.
> 단순 문자열 표는 위처럼 직접 만들어도 되고, 규모가 커지면 `i18next` + `expo-localization` 사용.

## 4-4. AdMob (광고 수익화)

```bash
npx expo install react-native-google-mobile-ads
```

```jsonc
// app.json (plugins)
["react-native-google-mobile-ads", {
  "androidAppId": "ca-app-pub-xxx~yyy",
  "iosAppId": "ca-app-pub-xxx~zzz"
}]
```

```tsx
// 배너 예
import { BannerAd, BannerAdSize, TestIds } from 'react-native-google-mobile-ads';
// 개발/테스트는 반드시 테스트 ID (실광고 자가클릭 = 계정정지)
const unitId = __DEV__ ? TestIds.BANNER : '실광고_단위_ID';
<BannerAd unitId={unitId} size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER} />
```

핵심 규칙:
- **개발/내부테스트 = 테스트 광고, 정식 출시만 실광고.** 본인이 실광고 누르면 AdMob 계정 정지.
- iOS는 **ATT 권한**(App Tracking Transparency) 문구·요청 필요.
- 게임 중 강제 전면광고는 리텐션·리뷰 킬러 — 절제(보상형/배너 위주) 권장.

## 4-5. 빌드 & 출시 (EAS)

Expo Go는 "개발 런처"라 스토어엔 못 올림 → **EAS Build**로 실제 앱 바이너리 생성.

```bash
npm i -g eas-cli
eas login
eas build:configure

# 내부 테스트용 빌드 (실기 설치)
eas build -p android --profile preview      # APK
eas build -p ios --profile preview          # (애플 인증서 자동)

# 스토어 제출용
eas build -p android --profile production    # AAB → Play
eas build -p ios --profile production        # → App Store
eas submit -p android --latest
eas submit -p ios --latest
```

- `eas.json`의 **profile**로 환경 분기(개발/테스트/프로덕션) — 광고 ID·API 키 등.
- **OTA 업데이트**: JS만 바뀐 수정은 `eas update`로 스토어 재심사 없이 즉시 배포(네이티브 변경은 재빌드 필요).
- 앱 아이콘/스플래시: `app.json`의 `icon`, `splash`. 1024×1024 아이콘 필수.

## 4-6. 네이티브가 필요할 때

RN으로 95%가 되지만, 플랫폼 고유 기능(위젯·Live Activity·특정 SDK)은 네이티브 코드가 필요할 수 있음:
- 대부분 **커뮤니티 패키지**가 이미 있음(`expo install`로 검색).
- 없으면 `expo prebuild`로 `ios/` `android/` 생성 후 네이티브 모듈을 직접 작성(작은 Swift/Kotlin 모듈을 JS에 노출). RN이라고 네이티브 0이 아니라 **"필요한 조각만"** 네이티브.

---

# PART 5: React 개발자가 자주 밟는 지뢰 10가지

1. **글자를 `<Text>` 밖에 둠** → `Text strings must be rendered within a <Text>`. 모든 문자열은 `<Text>` 안.
2. **`<div>`/`className`/CSS 파일 습관** → `<View>` + `StyleSheet`. CSS 캐스케이드·상속 없음.
3. **flex 기본 방향 착각** → 웹은 row, RN은 **column**. 가로 배치는 `flexDirection: 'row'` 명시.
4. **`px`·`rem` 단위 붙임** → 숫자만(`padding: 16`). %·flex만 문자열/숫자 혼용.
5. **`localStorage`처럼 동기 기대** → `AsyncStorage`는 **비동기**, 항상 `await`.
6. **`document`/`window`/DOM API 사용** → 없음. 측정은 `onLayout`, ref + 측정 API.
7. **큰 리스트를 `.map()`+`ScrollView`** → 길면 `FlatList`(가상화). 안 그러면 버벅.
8. **SafeArea 무시** → 노치/홈바에 콘텐츠 가림. `react-native-safe-area-context`의 `SafeAreaView`/`useSafeAreaInsets`.
9. **키보드가 입력창 가림** → `KeyboardAvoidingView` 또는 `react-native-keyboard-controller`.
10. **플랫폼 차이 미고려** → `Platform.OS === 'ios'` 분기, `Platform.select({ ios, android })`. 그림자·폰트·뒤로가기 동작 등 미세 차이.

보너스 — **이미지**: 로컬은 `<Image source={require('./a.png')} />`, 원격은 `<Image source={{ uri }} style={{ width, height }} />` (원격은 **크기 명시 필수**, 웹처럼 자동 안 됨).

---

# 부록: 다음 단계 & 리소스

**여기까지 했으면 할 수 있는 것**: 화면·상태·리스트·폼·API·저장·네비게이션·광고·출시. = 실서비스 앱의 본체.

**다음 학습 추천**:
- `@tanstack/react-query` — 서버 상태(웹과 동일)
- `zustand` — 클라이언트 전역 상태(웹과 동일)
- `react-native-reanimated` + `gesture-handler` — 부드러운 애니메이션/제스처
- `expo-notifications` — 푸시 알림
- `nativewind` — Tailwind 문법으로 스타일(웹 습관 유지하고 싶으면)
- `react-native-safe-area-context`, `expo-image`, `expo-haptics`

**공식 문서**:
- React Native: https://reactnative.dev
- Expo: https://docs.expo.dev
- Expo Router: https://docs.expo.dev/router/introduction/
- EAS: https://docs.expo.dev/eas/

**핵심 마인드셋**: "RN은 새 프레임워크가 아니라 **React의 렌더 타깃이 DOM에서 네이티브로 바뀐 것**." 당신의 React 실력 대부분이 그대로 이전됩니다. 나머지는 이 문서의 매핑표를 곁에 두고 만들면서 익히면 끝.

행복한 출시 되세요 🚀
