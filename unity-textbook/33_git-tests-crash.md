# 33. Git·회귀 테스트·크래시 대응

> **이 장에서 배울 것**
> - Unity 프로젝트를 Git으로 관리하기 위한 `.gitignore`·Git LFS·Visible Meta Files·Force Text 설정을 구성하고, 실수를 `restore`/`revert`/`reset`/`reflog`로 복구할 수 있다
> - 브랜치와 태그로 릴리스를 관리하고, UnityYAMLMerge로 씬·프리팹 충돌을 줄인다
> - 순수 로직을 어셈블리로 분리해 EditMode 회귀 테스트와 PlayMode 스모크 테스트를 작성하고 명령행·CI에서 실행한다
> - 로그 파일 위치를 알고, 예외·비정상 종료를 기록하는 크래시 리포트 루틴을 구현한다
> - 사용자 버그를 재현→테스트→수정→핫픽스→(필요 시) 롤백하는 절차를 Steam beta 브랜치와 연결해 수행한다
>
> **선수 장**: Git 절(1~3단계)은 기초 트랙만 · 나머지(4~9단계)는 10, 19 (23, 24, 26을 읽었다면 더 좋음) · **예상 시간**: Git 절 2시간 + 나머지 4~5시간 · **코인 러시 진행**: LFS가 설정된 저장소와 릴리스 태그, 로직 어셈블리와 회귀 테스트 스위트(EditMode + PlayMode 스모크), CI 테스트 작업, 크래시 로그 수집기, 버그 리포트 템플릿과 핫픽스·롤백 런북
>
> **권장 시점**: **Git 절(1~3단계)은 01장 전**에 — 첫 코드를 치기 전에 저장소부터 만듭니다. **나머지(4~9단계)는 19장 뒤**, 빌드 자동화가 생기고 출시 준비(38·26장)에 들어가기 전에 합니다.

## 왜 필요한가

1인 개발에서 실제로 일어나는 사고들입니다.

```
[월요일]  씬 정리하다 Enemy 프리팹 참조가 전부 Missing. Ctrl+Z로는 안 돌아옴. 백업은 3주 전.
[수요일]  캡슐 PSD 2GB를 커밋했더니 GitHub push가 거부됨. 히스토리에서 지우는 법을 모름.
[출시 D+2] 리뷰: "Steam Deck에서 결과 화면 들어가면 멈춰요". 내 PC에선 재현 안 됨. 로그를 어디서 받지?
[출시 D+3] 급히 고쳐 올렸는데, main에 있던 미완성 무기 코드까지 같이 나감. 새 크래시 발생.
[출시 D+4] 되돌리려고 이전 빌드를 올렸더니, 1.0.3에서 저장된 세이브를 1.0.2가 못 읽음.
```

웹 개발자라면 Git은 익숙하지만, Unity 프로젝트에는 웹과 다른 함정이 있습니다. **`.meta` 파일**을 빠뜨리면 참조가 깨지고, 씬·프리팹은 YAML이라 일반 병합이 자주 망가지며, 텍스처·오디오 같은 대용량 바이너리가 저장소를 부풀립니다.

테스트도 비슷합니다. 10장에서 세이브 마이그레이션 EditMode 테스트를 만들었지만, 23장 밸런스 수치를 바꾸다 시뮬레이터 결과가 조용히 달라지거나, 씬 구조를 바꾸다 부트스트랩이 예외를 던지는 문제는 잡지 못합니다. 그리고 출시 후에는 **내 PC가 아니라 플레이어의 PC에서** 문제가 생깁니다. 로그가 어디 있는지, 무엇을 받아야 재현할 수 있는지 모르면 26장의 "48시간 안에 핫픽스"는 불가능합니다.

이 장의 목표는 한 문장입니다. **어떤 실수를 해도 되돌릴 수 있고, 어떤 버그 신고를 받아도 재현·수정·배포·롤백할 수 있는 상태.**

## 개념

### Unity 프로젝트에서 Git에 넣을 것과 뺄 것

| 폴더·파일 | Git | 이유 |
|---|---|---|
| `Assets/` (모든 `.meta` 포함) | 넣음 | 게임 자체. `.meta`에 **GUID**가 있어 참조가 이것으로 연결됨 |
| `Packages/manifest.json`, `packages-lock.json` | 넣음 | 패키지 버전 고정 (웹의 `package.json`·lock 파일) |
| `ProjectSettings/` | 넣음 | 입력·태그·레이어·품질·빌드 설정. `ProjectVersion.txt`에 Unity 버전 |
| `Library/`, `Temp/`, `Obj/`, `Logs/`, `UserSettings/` | 뺌 | 재생성되는 캐시 (웹의 `node_modules/`·`.next/`) |
| `Builds/`, `*.apk`, `*.aab` | 뺌 | 빌드 결과물은 CI 아티팩트·Steam에 보관 |
| `*.csproj`, `*.sln` | 뺌 | IDE가 재생성 |
| `Art_Source/` (31장 원본) | 넣음 (LFS) | 원본이 없으면 수정 불가 |

**`.meta` 파일이 핵심**입니다. `Assets/Enemy.prefab`을 씬이 참조할 때 경로가 아니라 `Enemy.prefab.meta`의 `guid`로 연결됩니다. 파일은 커밋하고 `.meta`를 빠뜨리면, 다른 PC(또는 CI)에서 Unity가 새 GUID를 만들어 **모든 참조가 Missing**이 됩니다. 반대로 에디터 밖(Finder·탐색기)에서 파일을 옮기거나 이름을 바꾸면 `.meta`가 따라가지 않아 같은 사고가 납니다. **에셋 이동·이름 변경은 항상 Unity Project 창에서** 합니다.

Unity 쪽 설정 두 가지를 확인합니다(Unity 6 신규 프로젝트는 기본값이 이미 이렇게 되어 있지만, 오래된 프로젝트나 템플릿에서 바뀌었을 수 있습니다).

- `Edit > Project Settings > Version Control` → Mode: **Visible Meta Files** — `.meta`를 일반 파일로 보이게 해 Git이 추적.
- `Edit > Project Settings > Editor` → Asset Serialization Mode: **Force Text** — 씬·프리팹·ScriptableObject를 YAML 텍스트로 저장해 diff와 병합이 가능.

GitHub가 관리하는 **Unity용 `.gitignore` 템플릿**(github/gitignore 저장소의 `Unity.gitignore`)에서 시작하는 것이 안전합니다. 한 가지 함정이 있습니다. 이 템플릿은 Addressables가 만드는 `addressables_content_state.bin`을 **기본으로 무시**합니다. 19장의 원격 콘텐츠 업데이트(Update a Previous Build)는 **출시한 빌드의 이 파일**이 있어야 동작하므로, 릴리스마다 태그와 함께 따로 보관해야 합니다(6단계 런북).

### Git LFS — 대용량 바이너리

Git은 파일의 모든 버전을 저장합니다. 텍스트 코드는 작지만 30MB PSD를 10번 고치면 저장소가 300MB 늘고, 클론할 때마다 전부 받습니다. **Git LFS**(Large File Storage)는 저장소에는 작은 포인터만 두고 실제 바이너리는 별도 저장소에 둡니다.

- `.gitattributes`에 확장자 패턴을 등록합니다(1단계).
- **처음부터** 설정해야 합니다. 이미 일반 Git으로 커밋한 대용량 파일은 LFS로 옮기려면 히스토리 재작성(`git lfs migrate`)이 필요하고, 원격과 협업 중이면 복잡해집니다.
- 호스팅 서비스마다 LFS **저장 용량·대역폭 한도와 요금**이 있습니다. 한도는 바뀌므로 사용하는 서비스(GitHub, GitLab, Azure DevOps 등)의 현재 요금 문서를 확인하고, 캡슐 원본·녹음 원본처럼 거대한 파일은 LFS 대신 클라우드 드라이브 + 해시 기록으로 두는 선택도 고려합니다.
- 19장 GitHub Actions 워크플로는 이미 `actions/checkout`에 `lfs: true`를 줍니다. LFS를 쓰면 CI의 대역폭도 소모됩니다.

### 1인 개발의 브랜치와 태그

팀 규모의 Git Flow는 1인에게 과합니다. 코인 러시는 다음 규칙만 씁니다.

```
main ──●──●──●──●(v1.0.0)──●──●──●(미완성 무기 작업 중)──●──●(v1.1.0)
                    \
                     release/1.0 ──●(v1.0.1)──●(v1.0.2 핫픽스) ─ cherry-pick → main 에도 반영
feature/shrine-ui ──●──●──┘ (짧게, 며칠 안에 main으로 병합)
```

| 규칙 | 내용 |
|---|---|
| `main` | 항상 **빌드되고 테스트가 통과하는** 상태. 하루 작업의 끝은 main에 병합 가능한 커밋 |
| `feature/*` | 며칠짜리 작업. 오래 살수록 씬·프리팹 충돌 위험 증가 |
| 태그 `vMAJOR.MINOR.PATCH` | 스토어에 올린 **모든 빌드에** 태그. 19장 CI가 `v*` 태그 푸시로 빌드 |
| `release/1.0` | 출시 후 main이 다음 기능으로 나아갔을 때만, 태그에서 만들어 핫픽스 전용으로 사용 |
| 버전 번호 | PATCH = 버그 수정(세이브 구조 변경 금지), MINOR = 기능·콘텐츠 추가(세이브 마이그레이션 허용), MAJOR = 큰 개편 |

Steam 브랜치와 짝을 맞추면 헷갈리지 않습니다(26장 SteamPipe).

| Git | Steam 브랜치 | 누가 받나 |
|---|---|---|
| `main`의 개발 빌드 | `internal` (비밀번호) | 나, 테스터 |
| 핫픽스 후보 태그 `v1.0.3` | `beta` (비밀번호) | 제보자, 검수자 |
| 검증 끝난 태그 | `default` | 모든 구매자 |
| 직전 안정 태그 `v1.0.2` | `previous` (비밀번호 없는 공개 베타도 가능) | 새 버전에서 문제가 생긴 플레이어의 임시 선택지 |

### 실수 복구 — 상황별 명령

| 상황 | 명령 | 되돌릴 수 있나 |
|---|---|---|
| 커밋 안 한 파일 하나를 마지막 커밋 상태로 | `git restore <path>` (`.meta`도 함께) | 아니오 (작업 내용 사라짐) |
| 스테이징만 취소 | `git restore --staged <path>` | 예 |
| 방금 한 커밋 메시지·내용 수정 (push 전) | `git commit --amend` | 예 (reflog) |
| 마지막 커밋을 취소하되 변경은 남기기 (push 전) | `git reset --soft HEAD~1` | 예 (reflog) |
| **이미 push한** 커밋을 되돌리기 | `git revert <commit>` — 되돌리는 새 커밋 생성 | 예 |
| 작업 중인 변경을 잠시 치우기 | `git stash push -m "메모"` → `git stash pop` | 예 |
| reset·브랜치 삭제로 "잃어버린" 커밋 찾기 | `git reflog` → `git branch rescue <hash>` | 예 (보통 90일 안팎 보관, 설정에 따라 다름) |
| 특정 파일을 과거 커밋 버전으로 | `git restore --source <commit> -- <path>` | 예 |

- `git reset --hard`와 `git push --force`는 **main에서 쓰지 않습니다.** 원격을 덮어쓰면 CI·다른 PC의 기록과 어긋납니다. 이미 push했다면 revert가 답입니다.
- Unity 에디터가 열린 상태에서 브랜치를 바꾸거나 파일을 되돌리면 에디터가 재임포트하면서 **열려 있던 씬의 메모리 상태를 다시 저장**해 되돌린 내용을 덮을 수 있습니다. 큰 되돌리기는 씬을 저장한 뒤 에디터를 닫고 합니다.

### 씬·프리팹 충돌

씬과 프리팹은 YAML 텍스트지만, 오브젝트마다 `fileID`와 참조가 얽혀 있어 일반 줄 단위 병합이 문법상 맞아도 **의미상 깨진** 파일을 만들 수 있습니다. 대응은 예방 → 도구 → 포기 순서입니다.

1. **예방**: 씬을 작게(09장 Bootstrap/Title/Game 분리), 자주 바뀌는 것은 프리팹으로 빼고, 데이터는 ScriptableObject(03장)로. 한 파일을 두 브랜치에서 동시에 오래 고치지 않습니다. 1인 개발에서도 PC 두 대(데스크톱·노트북)를 쓰면 충돌이 납니다.
2. **도구**: Unity가 제공하는 **UnityYAMLMerge**(Smart Merge)를 Git 병합 도구로 등록합니다. Unity의 직렬화 구조를 이해하고 병합합니다(2단계).
3. **포기**: 병합이 실패하면 한쪽을 통째로 고르고(`git checkout --ours/--theirs <file>`) 다른 쪽 변경을 에디터에서 손으로 다시 합니다. 씬 파일을 텍스트 편집기로 고치는 것은 최후 수단입니다.

### 회귀 테스트 — 게임에서 무엇을 테스트하나

"재미"는 자동 테스트할 수 없지만, **한 번 고친 버그가 다시 생기는 것**(회귀, regression)은 막을 수 있습니다.

| 층 | Test Runner 모드 | 코인 러시 대상 | 속도 |
|---|---|---|---|
| 순수 로직 단위 테스트 | EditMode | 세이브 마이그레이션(10장), `WeightedRandom`·`ShuffleBag`(06장), 밸런스 시뮬레이터 결정성·기준값(23장) | 밀리초 |
| 컴포넌트 계약 테스트 | PlayMode | 물리 트리거·코루틴이 필요한 동작 | 초 |
| 스모크 테스트 | PlayMode | 부트스트랩 → 타이틀 → 게임 시작 → 15초 동안 **오류 로그 0** | 수십 초 |
| 수동 QA | — | 38장 QA 매트릭스 | 시간 |

- **EditMode** 테스트는 에디터에서 Play 없이 실행됩니다. 순수 C# 로직에 적합합니다.
- **PlayMode** 테스트는 `[UnityTest]`를 붙인 `IEnumerator` 메서드로 쓰고, `yield return null`로 프레임을 넘기며 실제 게임 루프 안에서 실행됩니다.
- Unity Test Framework는 테스트 중 **처리되지 않은 `Debug.LogError`·예외 로그가 나오면 테스트를 실패**시킵니다. 의도한 오류는 `LogAssert.Expect(LogType.Error, ...)`로 미리 선언합니다. 스모크 테스트는 이 성질을 이용해 "15초 동안 아무 오류도 안 난다"를 검사합니다.
- Test Framework(`com.unity.test-framework`)는 Unity 6에서 에디터 버전에 고정된 **코어 패키지**라 따로 버전을 고르지 않습니다. Unity 6.2 이상에서는 사용자 가이드가 Unity 매뉴얼 안으로 옮겨졌습니다.

**어셈블리 제약**을 기억하세요(10장·20장). 테스트 어셈블리(asmdef)는 asmdef가 없는 기본 어셈블리 `Assembly-CSharp`를 참조할 수 없습니다. 그래서 테스트할 로직은 **별도 asmdef로 분리**합니다. 코인 러시는 게임 전체를 asmdef로 쪼개지 않고, 테스트 가치가 높은 순수 로직만 `CoinRush.Logic`으로 모읍니다(4단계). 게임 코드(`Assembly-CSharp`)는 Auto Referenced 덕분에 수정 없이 계속 사용합니다.

**버그 수정의 순서**: 재현하는 테스트를 먼저 쓰고(빨강), 고치고(초록), 커밋에 둘을 함께 넣습니다. 테스트를 쓸 수 없는 버그(렌더링, 기기 전용)는 38장 QA 매트릭스에 재현 절차를 한 줄 추가합니다.

### 크래시와 예외의 종류

| 종류 | 증상 | 남는 것 | 수집 방법 |
|---|---|---|---|
| 관리 예외 (C# `NullReferenceException` 등) | 게임은 계속되지만 기능이 멈춤(버튼 무반응, 판이 안 끝남) | `Player.log`에 예외·스택 트레이스 | `Application.logMessageReceivedThreaded` 로 직접 기록(8단계) |
| 네이티브 크래시 | 프로세스가 종료됨 | Windows: 크래시 폴더에 덤프·로그 / 다음 실행의 `Player-prev.log` | 크래시 폴더 안내, 비정상 종료 감지(8단계), 크래시 수집 서비스 |
| 멈춤(Freeze) | 화면 정지, 응답 없음 | 로그가 중간에 끊김 | 비정상 종료 감지 + 마지막 로그 |
| 소프트락 | 게임은 도는데 진행 불가 | 로그에 오류가 없을 수 있음 | 재현 절차, 세이브 파일, 애널리틱스 이벤트 흐름(24장) |

**플레이어 로그 위치**(Unity 6000.0 매뉴얼 기준, `CompanyName`·`ProductName`은 Player Settings 값):

| 플랫폼 | 위치 |
|---|---|
| Windows | `%USERPROFILE%\AppData\LocalLow\CompanyName\ProductName\Player.log` (직전 실행은 `Player-prev.log`) |
| macOS | `~/Library/Logs/Company Name/Product Name/Player.log` |
| Linux (Steam Deck 네이티브 빌드 포함) | `~/.config/unity3d/CompanyName/ProductName/Player.log` |
| Android | 파일이 아니라 `adb logcat` (Android Logcat 패키지) |
| Windows 크래시 리포트 | `%TMP%\CompanyName\ProductName\Crashes` 아래 (덤프·로그). 정확한 경로는 `Windows.CrashReporting.crashReportFolder` 문서 참고 |

Steam Deck에서 **Windows 빌드를 Proton으로** 실행하면 로그는 Proton의 가상 Windows 사용자 폴더(Steam 라이브러리의 `compatdata/<AppID>/pfx/...` 아래) 안에 생깁니다. 제보자에게 안내할 때 플랫폼별로 따로 적어야 합니다.

**크래시 수집 서비스**는 네이티브 크래시·심볼·기기 정보를 자동으로 모아 줍니다. 선택지는 바뀌므로 공식 문서로 확인합니다.

- Unity의 **Cloud Diagnostics**(Crash and Exception Reporting)는 공식 문서에서 **deprecated(단계적 종료 예정)** 로 표시되어 있고, Unity 6.2 이상에서는 **Diagnostics**(Developer Data 프레임워크, `Project Settings > Services > Diagnostics`, Unity Cloud 프로젝트 연결 필요)를 쓰라고 안내합니다. 코인 러시가 6000.0 LTS에 머문다면 둘 중 무엇을 쓸 수 있는지 설치 버전의 문서를 확인합니다.
- Sentry, Backtrace 같은 외부 서비스도 Unity SDK를 제공합니다. 무료 한도·데이터 보관 위치·개인정보 조건을 비교합니다.
- 어떤 서비스든 **수집 사실을 개인정보처리방침에 적고**(28장), 24장 동의 흐름과 맞춥니다. 로그에 사용자 이름이 들어간 경로가 찍힐 수 있다는 점도 고려합니다.

코인 러시는 먼저 **서비스 없이 동작하는 로컬 수집기**(8단계)를 만들고, 출시 전 서비스 도입 여부를 결정합니다. 로컬 수집기는 서비스를 붙여도 "제보자가 파일을 보내 주는" 경로로 계속 쓸모가 있습니다.

### 핫픽스와 롤백의 위험

- **핫픽스는 태그에서 출발**합니다. main에서 바로 빌드하면 미완성 기능이 섞입니다.
- **롤백**은 Steamworks의 Builds 페이지에서 default 브랜치에 이전 빌드를 다시 Set Live 하는 것으로 할 수 있습니다(업로드 스크립트로는 default에 자동 적용할 수 없고 웹에서 직접 해야 함 — 26장). 문제는 **세이브**입니다. 새 버전이 세이브 구조를 올렸다면 옛 버전은 그 파일을 못 읽습니다. 10장의 `FutureSaveVersionException` 보호 덕분에 덮어쓰지는 않지만, 플레이어는 "진행이 사라졌다"고 느낍니다. 그래서 **PATCH 버전에서는 세이브 구조를 바꾸지 않는다**는 규칙을 둡니다.

## 실습: 코인 러시에 적용하기

앞 장의 최소 시그니처입니다.

```csharp
// 06장 WeightedRandom   : static int PickIndex(IReadOnlyList<int> weights, System.Random rng = null)
// 06장 ShuffleBag<T>    : ShuffleBag(System.Random rng = null), Add(T item, int count = 1), T Next()
// 09장 씬 이름          : "Bootstrap"(빌드 인덱스 0), "Title", "Game"
// 10장 테스트 폴더      : Assets/_CoinRush/Tests/EditMode/ (asmdef CoinRush.Tests.EditMode → CoinRush.SaveCore 참조)
// 19장 BuildScripts     : BuildFromCommandLine, .github/workflows/build.yml (v* 태그 → 빌드)
// 23장 BalanceSimulator : static SimReport RunMany(string label, SimConfig c, int runs, int seed)
// 24장 Analytics        : static Track(string name, params (string key, object value)[] props)
```

### 1단계 (01장 전): 저장소 만들기 — .gitignore, LFS, Unity 설정

1. Git과 Git LFS를 설치하고 한 번 초기화합니다: `git lfs install`.
2. Unity Hub에서 Universal 2D 템플릿으로 프로젝트를 만들고, 개념 절의 **Visible Meta Files**·**Force Text**를 확인합니다.
3. 프로젝트 루트에서 `git init -b main`.
4. `.gitignore`: github/gitignore 저장소의 `Unity.gitignore` 내용을 그대로 붙여 넣고, 맨 아래에 코인 러시용 줄을 추가합니다.

```gitignore
# ---- 코인 러시 추가 ----
/steam-build/output/
/steam-build/content/
/TestResults/
.DS_Store
Thumbs.db
# 비밀 (키스토어, 계정 정보) — 절대 커밋 금지
*.keystore
*.jks
.env
```

5. `.gitattributes`를 만듭니다. **어떤 파일도 커밋하기 전에** 만들어야 LFS가 적용됩니다.

```gitattributes
# 텍스트: 줄바꿈 정규화 (Windows·macOS를 오가도 diff가 깨지지 않게)
* text=auto
*.cs text diff=csharp

# 바이너리 → LFS
*.png  filter=lfs diff=lfs merge=lfs -text
*.jpg  filter=lfs diff=lfs merge=lfs -text
*.psd  filter=lfs diff=lfs merge=lfs -text
*.kra  filter=lfs diff=lfs merge=lfs -text
*.aseprite filter=lfs diff=lfs merge=lfs -text
*.wav  filter=lfs diff=lfs merge=lfs -text
*.ogg  filter=lfs diff=lfs merge=lfs -text
*.mp3  filter=lfs diff=lfs merge=lfs -text
*.ttf  filter=lfs diff=lfs merge=lfs -text
*.otf  filter=lfs diff=lfs merge=lfs -text
*.mp4  filter=lfs diff=lfs merge=lfs -text
*.dll  filter=lfs diff=lfs merge=lfs -text
```

6. 첫 커밋과 확인:

```bash
git add .gitignore .gitattributes
git commit -m "chore: gitignore, LFS 설정"
git add .
git status                      # Library/, Temp/ 가 목록에 없어야 함
git commit -m "chore: Unity 6 Universal 2D 프로젝트 생성"
git lfs ls-files                # 템플릿의 png 등이 LFS로 들어갔는지 확인
```

7. 원격 저장소(GitHub 비공개 등)를 만들고 `git remote add origin <url>` → `git push -u origin main`.

> 11장 TMP Dynamic 폰트 에셋은 플레이할 때마다 아틀라스가 바뀌어 diff가 생깁니다. 커밋 전 `git status`에서 의도하지 않은 `.asset` 변경은 `git restore`로 되돌리는 습관을 들이세요(32장 7단계의 Static 아틀라스 다시 굽기가 근본 해결).

### 2단계 (01장 전): UnityYAMLMerge 등록

Unity 매뉴얼(Smart Merge)의 Git 설정을 사용자 전역 설정(`~/.gitconfig`)에 넣습니다. 도구 경로는 설치한 에디터 폴더 안의 `Tools`입니다. Unity Hub로 설치했다면 아래처럼 버전 폴더가 경로에 들어갑니다(**자기 PC의 실제 경로로 바꾸세요**).

```ini
# ~/.gitconfig  (macOS 예)
[merge]
    tool = unityyamlmerge

[mergetool "unityyamlmerge"]
    trustExitCode = false
    cmd = '/Applications/Unity/Hub/Editor/6000.0.XXf1/Unity.app/Contents/Tools/UnityYAMLMerge' merge -p "$BASE" "$REMOTE" "$LOCAL" "$MERGED"

```

Windows는 경로가 `C:\Program Files\Unity\Hub\Editor\6000.0.XXf1\Editor\Data\Tools\UnityYAMLMerge.exe` 형태이고, `.gitconfig` 안에서는 역슬래시를 `/`로 바꾸거나 두 번 씁니다.

- 충돌이 나면 `git mergetool`을 실행해 충돌 파일마다 UnityYAMLMerge를 호출합니다. 도구가 해결하지 못한 부분은 `mergespecfile.txt`(같은 Tools 폴더)에 지정된 대체 도구로 넘어갑니다. Git 병합 드라이버로 자동 호출하는 설정도 가능하지만 옵션이 버전마다 달라, 이 책은 매뉴얼에 있는 mergetool 방식만 씁니다.
- Unity 에디터를 업그레이드하면 경로의 버전 폴더가 바뀝니다. 업그레이드 체크리스트에 넣으세요.

**연습용 충돌 만들기**: `feature/test-merge` 브랜치에서 `Enemy_Slime` 프리팹의 이동 속도를, main에서 같은 프리팹의 색을 바꿔 각각 커밋한 뒤 병합합니다. Git이 충돌을 보고하면 `git mergetool`로 UnityYAMLMerge가 합치게 하고, Unity에서 프리팹을 열었을 때 두 변경이 모두 보여야 합니다.

### 3단계 (01장 전): 릴리스·복구 연습

실수 복구를 **실제 사고 전에** 한 번씩 해 봅니다. 각 시나리오를 따라 치세요.

**시나리오 A — 참조를 날린 씬을 어제 상태로**

```bash
git log --oneline -- Assets/_CoinRush/Scenes/Game.unity     # 이 파일을 바꾼 커밋 목록
git restore --source <어제 커밋 hash> -- Assets/_CoinRush/Scenes/Game.unity   # 에디터 닫고 실행 → 열어 확인 후 커밋
```

**시나리오 B — push까지 한 잘못된 밸런스 커밋 되돌리기**

```bash
git revert <잘못된 커밋 hash>          # 되돌리는 새 커밋이 생김. 히스토리는 보존
git push
```

**시나리오 C — `reset --hard`로 날린 오후 작업 찾기**

```bash
git reflog                            # HEAD@{3}: commit: 제단 UI 초안 ← 여기
git branch rescue/shrine-ui HEAD@{3}  # 그 커밋을 가리키는 브랜치 생성
git switch rescue/shrine-ui
```

**릴리스 태그 규칙**: 스토어에 올린 빌드는 반드시 태그를 붙입니다. 태그 메시지에 스토어 빌드 ID를 적어 두면 롤백 때 찾기 쉽습니다.

```bash
git tag -a v1.0.0 -m "Steam default 출시. SteamPipe BuildID 1234567, SaveData v4"
git push origin v1.0.0                # 19장 CI가 이 태그로 빌드
```

### 4단계 (19장 뒤): 로직 어셈블리 분리

테스트할 순수 로직을 한 폴더로 모읍니다. **반드시 Unity Project 창에서 드래그로 옮깁니다**(`.meta`와 GUID 유지).

1. `Assets/_CoinRush/Scripts/Logic/` 폴더를 만듭니다.
2. 다음 파일을 옮깁니다: `Core/WeightedRandom.cs`, `Core/ShuffleBag.cs`(06장), `Balance/BalanceSimulator.cs`(23장). 세 파일은 게임 오브젝트·에셋 타입을 참조하지 않습니다(`WeightedRandom`·`ShuffleBag`은 `UnityEngine.Random`만 사용).
3. `Logic/`에서 `Create > Scripting > Assembly Definition`, 이름 `CoinRush.Logic`. Auto Referenced 켬(기본값), 참조 없음.
4. 컴파일 에러가 없어야 합니다. 에러가 나면 옮긴 파일이 `Assembly-CSharp`의 타입(예: `EnemyData`)을 참조한다는 뜻이니 그 파일은 원래 자리로 되돌립니다. 06장 `LootTable`(ScriptableObject)과 23장 `BalanceSimulatorMenu`(Editor 폴더)는 `Assembly-CSharp` 쪽에 남아 `CoinRush.Logic`을 자동 참조합니다.
5. 10장 EditMode 테스트 asmdef(`CoinRush.Tests.EditMode`)의 Assembly Definition References에 `CoinRush.Logic`을 추가하고 Apply.

커밋: `git commit -m "refactor: 테스트 가능한 순수 로직을 CoinRush.Logic으로 분리"`.

### 5단계: EditMode 회귀 테스트

```csharp
// Assets/_CoinRush/Tests/EditMode/RandomLogicTests.cs
using System.Collections.Generic;
using NUnit.Framework;

public class RandomLogicTests
{
    [Test]
    public void PickIndex_Never_Picks_Zero_Or_Negative_Weight()
    {
        var weights = new List<int> { 0, 5, -3, 5 };
        var rng = new System.Random(1234);
        for (int i = 0; i < 10_000; i++)
        {
            int index = WeightedRandom.PickIndex(weights, rng);
            Assert.That(index, Is.EqualTo(1).Or.EqualTo(3), $"{i}번째 뽑기에서 {index}");
        }
    }

    [Test]
    public void PickIndex_Distribution_Matches_Weights()
    {
        var weights = new List<int> { 1, 3 };           // 기대 비율 25% : 75%
        var rng = new System.Random(42);
        int[] counts = new int[2];
        const int n = 40_000;
        for (int i = 0; i < n; i++) counts[WeightedRandom.PickIndex(weights, rng)]++;

        Assert.AreEqual(0.25, counts[0] / (double)n, 0.01);   // ±1%p 허용 (고정 seed라 매번 같은 결과)
    }

    [Test]
    public void ShuffleBag_Returns_Each_Item_Exactly_Once_Per_Cycle()
    {
        var bag = new ShuffleBag<string>(new System.Random(7));
        bag.Add("orb", 2);
        bag.Add("magnet", 1);

        for (int cycle = 0; cycle < 50; cycle++)
        {
            var seen = new Dictionary<string, int>();
            for (int i = 0; i < 3; i++)
            {
                string item = bag.Next();
                seen[item] = seen.TryGetValue(item, out int c) ? c + 1 : 1;
            }
            Assert.AreEqual(2, seen["orb"], $"cycle {cycle}");
            Assert.AreEqual(1, seen["magnet"], $"cycle {cycle}");
        }
    }
}
```

밸런스 회귀 테스트는 두 종류입니다. **결정성**(같은 seed → 같은 결과)은 코드 변경이 시뮬레이터를 비결정적으로 만들지 않았는지 봅니다. **기준 범위**(골든 값)는 23장에서 합의한 난이도 목표가 코드 변경으로 조용히 깨지지 않았는지 봅니다.

```csharp
// Assets/_CoinRush/Tests/EditMode/BalanceRegressionTests.cs
using NUnit.Framework;

public class BalanceRegressionTests
{
    const int Runs = 300;
    const int Seed = 20260917;

    // 23장 BalanceSimulatorMenu.BuildConfig는 에셋에서 값을 읽는 Editor 코드라 여기서 쓸 수 없음.
    // 테스트는 "기준 시나리오"를 코드로 고정한다. 에셋 수치를 바꿨다면 이 값도 의도적으로 갱신한다.
    static SimConfig BaselineConfig()
    {
        var c = new SimConfig();
        for (int m = 0; m < 10; m++)
            c.minutes.Add(new SimMinute { spawnsPerSecond = 0.6f + 0.35f * m, avgHp = 10f * (1f + 0.25f * m), avgContact = 5f + m, avgCoin = 1f });
        c.events.Add(new SimEvent { time = 300, hp = 600f });   // 엘리트
        c.events.Add(new SimEvent { time = 540, hp = 2500f });  // 보스
        return c;
    }

    [Test]
    public void Simulator_Is_Deterministic_For_Same_Seed()
    {
        SimReport a = BalanceSimulator.RunMany("a", BaselineConfig(), Runs, Seed);
        SimReport b = BalanceSimulator.RunMany("b", BaselineConfig(), Runs, Seed);

        Assert.AreEqual(a.clearRate, b.clearRate);
        Assert.AreEqual(a.medianSeconds, b.medianSeconds);
        CollectionAssert.AreEqual(a.endMinuteHistogram, b.endMinuteHistogram);
    }

    [Test]
    public void Baseline_Clear_Rate_Stays_In_Target_Band()
    {
        SimReport r = BalanceSimulator.RunMany("baseline", BaselineConfig(), Runs, Seed);
        TestContext.WriteLine(r.ToString());                     // Test Runner 출력 창에서 확인

        // 목표 밴드는 23장 합의값을 옮겨 적는다. 처음 실행한 결과를 보고 ±여유를 두어 확정.
        Assert.That(r.clearRate, Is.InRange(0.05f, 0.40f), "첫 판 클리어율이 목표 밴드를 벗어남");
        Assert.That(r.medianSeconds, Is.InRange(180f, 540f), "생존 시간 중앙값이 목표 밴드를 벗어남");
    }
}
```

- 기준 시나리오 수치는 **설명용 예시**입니다. 23장에서 만든 실제 `WaveData`·`ProgressionData` 값을 옮겨 적고, 처음 실행 결과로 밴드를 확정하세요. 밴드는 "좋은 밸런스"가 아니라 **의도하지 않은 변화 감지기**입니다.
- 밸런스를 의도적으로 바꾸면 이 테스트가 실패합니다. 그때는 테스트 값을 고치는 커밋을 **밸런스 변경 커밋과 같은 커밋**에 넣고, 커밋 메시지에 이유를 씁니다. 그래야 나중에 `git log`로 "언제 왜 어려워졌나"를 찾을 수 있습니다.

Test Runner(`Window > General > Test Runner`) → EditMode → Run All. 10장 테스트까지 모두 초록이면 커밋합니다.

### 6단계: PlayMode 스모크 테스트

1. `Assets/_CoinRush/Tests/PlayMode/` 폴더 → Assembly Definition `CoinRush.Tests.PlayMode`.
   - Assembly Definition References: `UnityEngine.TestRunner`, `UnityEditor.TestRunner`, `UnityEngine.UI`
   - Override References 켬 → `nunit.framework.dll`
   - Define Constraints: `UNITY_INCLUDE_TESTS` · Auto Referenced: 끔
   - Platforms: 모두(Any Platform) — 에디터에서만 돌린다면 Editor만 체크해도 됩니다.
2. 스모크 테스트를 씁니다. 게임 코드를 참조하지 않고 **씬 이름과 오브젝트 이름**으로만 조작합니다. 11장 타이틀의 시작 버튼 오브젝트 이름을 `StartButton`으로 맞춰 두세요.

```csharp
// Assets/_CoinRush/Tests/PlayMode/BootSmokeTests.cs
using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

public class BootSmokeTests
{
    const float LoadTimeout = 15f;

    [UnitySetUp]
    public IEnumerator LoadBootstrap()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene("Bootstrap", LoadSceneMode.Single);   // Build Profiles의 씬 목록에 있어야 함
        yield return null;
    }

    [UnityTest]
    public IEnumerator Boot_Reaches_Title_Without_Errors()
    {
        yield return WaitUntilLoaded("Title");
        // 처리되지 않은 Debug.LogError/예외가 한 번이라도 나오면 Test Framework가 이 테스트를 실패 처리
    }

    [UnityTest]
    public IEnumerator Start_Run_And_Play_15_Seconds_Without_Errors()
    {
        yield return WaitUntilLoaded("Title");

        GameObject startButton = GameObject.Find("StartButton");
        Assert.IsNotNull(startButton, "타이틀에 StartButton 오브젝트가 없습니다 (이름 규칙 확인)");
        startButton.GetComponent<Button>().onClick.Invoke();

        yield return WaitUntilLoaded("Game");

        float end = Time.realtimeSinceStartup + 15f;
        while (Time.realtimeSinceStartup < end)
            yield return null;                         // 레벨업 창으로 timeScale이 0이 되어도 실제 시간으로 대기

        Assert.IsTrue(SceneManager.GetSceneByName("Game").isLoaded, "15초 안에 게임 씬이 내려감");
    }

    static IEnumerator WaitUntilLoaded(string sceneName)
    {
        float deadline = Time.realtimeSinceStartup + LoadTimeout;
        while (!SceneManager.GetSceneByName(sceneName).isLoaded)
        {
            if (Time.realtimeSinceStartup > deadline)
                Assert.Fail($"{LoadTimeout}초 안에 '{sceneName}' 씬이 로드되지 않았습니다.");
            yield return null;
        }
    }
}
```

- 09장의 `CoinRush/Play From Bootstrap`(`EditorSceneManager.playModeStartScene`)이 켜져 있으면 Test Runner의 PlayMode 시작 씬과 충돌할 수 있습니다. 테스트 전에 메뉴에서 끄거나, 테스트가 이상하게 시작되면 먼저 이 설정을 의심하세요.
- 이 테스트는 **실제 세이브 폴더**(`persistentDataPath`)를 사용합니다. 에디터에서 돌리면 개발 중인 세이브에 판 기록이 더해질 수 있으니, CI에서 돌리거나 로컬에서는 세이브를 백업한 뒤 실행하세요(연습 문제 1에서 개선).
- 24장 애널리틱스 동의 패널이 첫 실행에 입력을 막는다면, 테스트가 `StartButton`을 누르기 전에 동의 패널의 거부 버튼(`ConsentDeclineButton`)을 같은 방식으로 누르게 합니다.
- 스모크 테스트는 "게임이 켜지고 판이 시작되고 15초간 오류가 없다"만 봅니다. 느리니 **커밋마다가 아니라 태그·PR 단위**로 돌립니다.

### 7단계: 명령행과 CI에서 테스트 실행

로컬 명령행(에디터를 닫은 상태):

```bash
# macOS 예 — Unity 경로는 설치 버전에 맞게
/Applications/Unity/Hub/Editor/6000.0.XXf1/Unity.app/Contents/MacOS/Unity \
  -batchmode -projectPath . \
  -runTests -testPlatform EditMode \
  -testResults TestResults/editmode.xml \
  -logFile TestResults/editmode.log
echo "exit code: $?"      # 0 = 모두 통과, 그 외 = 실패
```

`-testPlatform PlayMode`로 바꾸면 스모크 테스트를 돌립니다. 결과는 NUnit XML이라 CI가 읽을 수 있습니다. 옵션 전체는 Unity 매뉴얼의 Test Framework **Command-line reference**를 확인하세요.

19장 `.github/workflows/build.yml`에 **빌드 전에 테스트하는 작업**을 추가합니다. 바뀌는 부분만 보입니다.

```yaml
jobs:
  test:
    name: Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
      # 액션 이름·버전·입력 이름은 GameCI 문서(game.ci)에서 최신 값을 확인하세요
      - uses: game-ci/unity-test-runner@v4
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
          UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
          UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}
        with:
          testMode: all
          artifactsPath: TestResults
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: TestResults
          path: TestResults

  build:
    needs: test            # ← 추가: 테스트가 실패하면 빌드·업로드하지 않음
    name: Build ${{ matrix.targetPlatform }}
    # (이하 19장 그대로)
```

이제 `v1.0.3` 태그를 push하면 테스트 → 빌드 순서로 돌고, 테스트가 하나라도 실패하면 스토어에 올릴 아티팩트가 만들어지지 않습니다.

### 8단계: 크래시 로그 수집기

서비스 없이도 동작하는 로컬 수집기입니다. 하는 일은 네 가지입니다.

1. 최근 로그 200줄을 메모리에 둡니다(링 버퍼).
2. 예외·오류가 나면 `crash_reports/` 폴더에 **리포트 파일**(버전·OS·기기·씬·최근 로그)을 씁니다. 같은 스택은 한 번만, 세션당 최대 개수를 둡니다.
3. 실행 시 `session.lock` 파일을 만들고 정상 종료 시 지웁니다. **다음 실행 때 파일이 남아 있으면 지난 세션이 비정상 종료**(네이티브 크래시·강제 종료·멈춤)한 것입니다.
4. 24장 `Analytics`로 요약 이벤트를 남기고, 설정 화면에서 **로그 폴더 열기** 버튼을 제공합니다.

```csharp
// Assets/_CoinRush/Scripts/Diagnostics/CrashLogCollector.cs
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.SceneManagement;

// 09장 Bootstrap 씬의 Managers 아래에 둔다. 가장 먼저 로그를 받도록 실행 순서를 앞당김.
[DefaultExecutionOrder(-2000)]
public class CrashLogCollector : MonoBehaviour
{
    const int BufferLines = 200;
    const int MaxReportsPerSession = 5;

    public static string ReportFolder => Path.Combine(Application.persistentDataPath, "crash_reports");
    public static bool PreviousSessionCrashed { get; private set; }

    static CrashLogCollector instance;

    readonly object gate = new object();
    readonly Queue<string> recent = new Queue<string>(BufferLines);
    readonly HashSet<int> reportedStacks = new HashSet<int>();
    int reportsThisSession;
    string lockPath;
    string activeScene = "";      // 메인 스레드에서만 갱신 (로그 콜백은 다른 스레드일 수 있음)

    void Awake()
    {
        if (instance != null) { Destroy(gameObject); return; }
        instance = this;
        DontDestroyOnLoad(gameObject);

        Directory.CreateDirectory(ReportFolder);
        lockPath = Path.Combine(ReportFolder, "session.lock");
        PreviousSessionCrashed = File.Exists(lockPath);
        File.WriteAllText(lockPath, $"{DateTime.UtcNow:o} v{Application.version}");

        Application.logMessageReceivedThreaded += OnLog;
        SceneManager.activeSceneChanged += (_, next) => activeScene = next.name;
        activeScene = SceneManager.GetActiveScene().name;
    }

    void Start()
    {
        if (!PreviousSessionCrashed) return;
        Debug.LogWarning("[Crash] 지난 실행이 정상 종료되지 않았습니다. Player-prev.log를 확인하세요.");
        Analytics.Track("previous_session_abnormal_exit", ("app_version", Application.version));
    }

    void OnApplicationQuit()
    {
        Application.logMessageReceivedThreaded -= OnLog;
        try { File.Delete(lockPath); } catch (IOException) { }   // 정상 종료 표시
    }

    // 어떤 스레드에서든 호출될 수 있음 → Unity API 대부분 사용 불가, lock으로 보호
    void OnLog(string message, string stackTrace, LogType type)
    {
        string line = $"{DateTime.UtcNow:HH:mm:ss.fff} [{type}] {message}";
        string report = null;

        lock (gate)
        {
            if (recent.Count == BufferLines) recent.Dequeue();
            recent.Enqueue(line);

            bool serious = type == LogType.Exception || type == LogType.Error || type == LogType.Assert;
            if (!serious || reportsThisSession >= MaxReportsPerSession) return;

            int stackKey = (message + stackTrace).GetHashCode();
            if (!reportedStacks.Add(stackKey)) return;             // 같은 오류는 세션당 한 번
            reportsThisSession++;
            report = BuildReport(message, stackTrace, type);
        }

        try
        {
            string file = Path.Combine(ReportFolder, $"report_{DateTime.UtcNow:yyyyMMdd_HHmmss}_{reportsThisSession}.txt");
            File.WriteAllText(file, report, new UTF8Encoding(false));
        }
        catch (Exception) { /* 로그 콜백 안에서 다시 로그를 남기면 무한 루프 위험 → 조용히 무시 */ }
    }

    string BuildReport(string message, string stackTrace, LogType type)
    {
        var sb = new StringBuilder();
        sb.AppendLine("=== Coin Rush Error Report ===");
        sb.AppendLine($"time_utc   : {DateTime.UtcNow:o}");
        sb.AppendLine($"version    : {Application.version} (unity {Application.unityVersion})");
        sb.AppendLine($"platform   : {Application.platform}");
        sb.AppendLine($"os         : {SystemInfo.operatingSystem}");
        sb.AppendLine($"device     : {SystemInfo.deviceModel} / {SystemInfo.processorType} / RAM {SystemInfo.systemMemorySize}MB");
        sb.AppendLine($"gpu        : {SystemInfo.graphicsDeviceName} ({SystemInfo.graphicsDeviceType})");
        sb.AppendLine($"scene      : {activeScene}");
        sb.AppendLine($"type       : {type}");
        sb.AppendLine($"message    : {message}");
        sb.AppendLine("stack      :");
        sb.AppendLine(stackTrace);
        sb.AppendLine($"--- last {recent.Count} log lines ---");
        foreach (string l in recent) sb.AppendLine(l);
        return sb.ToString();
    }

    /// <summary>설정 화면 "로그 폴더 열기" 버튼에서 호출 (데스크톱 전용)</summary>
    public static void OpenReportFolder()
    {
#if UNITY_STANDALONE
        Application.OpenURL("file://" + ReportFolder.Replace("\\", "/"));
#endif
    }
}
```

설계 포인트:

- `SystemInfo`·`Application` 속성은 스레드에 따라 접근이 제한될 수 있습니다. 백그라운드 스레드에서 오류가 나면 `BuildReport`의 일부 호출이 실패할 수 있으니, 더 엄격하게 하려면 기기 정보는 `Awake`에서 한 번 읽어 문자열로 캐시하세요. 로그 콜백 안에서는 준비된 문자열과 파일 I/O만 쓰고, `Debug.Log`를 부르지 않습니다(재귀).
- 리포트 파일은 **플레이어가 직접 보내 주는 경로**로만 받습니다. 자동 전송을 붙이려면 24장 동의와 28장 개인정보처리방침을 먼저 갱신합니다.
- 비정상 종료 감지는 강제 종료(작업 관리자)와 Steam Deck 절전 중 배터리 방전도 "크래시"로 셉니다. 비율로 추세를 보는 지표이지 개별 크래시의 증거가 아닙니다.

**설정 화면 연결**: 12장 설정 패널에 버튼 "로그 폴더 열기"(32장 테이블 키 `menu.settings.open_logs`)를 추가하고 OnClick에 `CrashLogCollector.OpenReportFolder`를 호출하는 작은 컴포넌트를 연결합니다. 지난 세션이 비정상 종료였다면 타이틀에 "문제가 있었나요? 설정 → 로그 폴더 열기에서 파일을 보내 주세요" 안내를 한 번 띄웁니다.

**확인용 오류 만들기**: 개발 빌드에서만 동작하는 디버그 키(16장·22장 디버그 도구 옆)에 `throw new InvalidOperationException("crash test")`를 넣고 눌러 `crash_reports/report_*.txt`가 생기는지, 같은 키를 다시 눌러도 파일이 늘지 않는지 확인합니다. 네이티브 크래시는 `UnityEngine.Diagnostics.Utils.ForceCrash(ForcedCrashCategory.FatalError)`로 **개발 빌드에서만** 재현해, 다음 실행에서 `previous_session_abnormal_exit`가 기록되는지 봅니다.

### 9단계: 버그 재현 절차와 핫픽스·롤백 런북

**버그 리포트 템플릿** (Steam 토론 게시판 고정글·Discord 채널용, 32장 방식으로 한/영 두 버전):

```
[버그 제보 양식]
1. 게임 버전 (타이틀 화면 오른쪽 아래, 예: v1.0.2):
2. 플랫폼: Windows / Steam Deck / macOS / Linux   (Deck이면 Proton 사용 여부)
3. 무엇을 했나요? (순서대로):
4. 무엇이 일어났나요? / 원래 기대한 것은?:
5. 몇 번 중 몇 번 일어나나요? (항상 / 가끔 / 한 번):
6. 파일 첨부 (설정 → 로그 폴더 열기):
   - crash_reports 폴더의 report_*.txt
   - Player.log, Player-prev.log  (Windows: %USERPROFILE%\AppData\LocalLow\<회사>\CoinRush\)
   - (진행 문제라면) save.json
```

타이틀 화면에 `Application.version`을 작게 표시하는 것이 첫 단계입니다. 버전을 모르면 어느 태그에서 재현할지 모릅니다.

**재현 → 수정 절차** (완성 예시):

```
제보: "v1.0.2, Steam Deck(네이티브 Linux). 결과 화면에서 '다시 하기'를 누르면 멈춤. 3번 중 3번."
첨부: report_20261012_214501_1.txt
  message : NullReferenceException: Object reference not set to an instance of an object
  stack   : ResultView.<Awake>b__12_0 () ... UnityEngine.Events.InvokableCall.Invoke ()
  scene   : Game
  last log: [Log] [Language] ... / [Warning] 게임패드 연결 해제 ...

1. 분류    : 치명(진행 불가) → 48시간 핫픽스 대상 (26장). 38장 블로커 기준에도 해당.
2. 재현 환경: git switch --detach v1.0.2  → 에디터에서 재현 시도
3. 재현 조건 좁히기: 로그 마지막의 "게임패드 연결 해제" → 판 도중 패드를 뽑았다 꽂은 뒤 결과 화면에서 재현 확인
4. 원인    : 재연결 시 PlayerInput이 새로 생성되며 ResultView가 잡고 있던 참조가 파괴됨
5. 테스트  : 로직으로 뽑을 수 있으면 EditMode, 아니면 38장 QA 매트릭스에 "패드 뽑기→결과→다시 하기" 행 추가
6. 수정 브랜치: git switch -c release/1.0 v1.0.2   (이미 있으면 switch)  → 수정 + 테스트 커밋
7. main 반영 : git switch main && git cherry-pick <수정 커밋>
```

**핫픽스 런북** (`Docs/runbook-hotfix.md`, 완성본):

| # | 단계 | 명령·작업 | 완료 기준 |
|---|---|---|---|
| 1 | 버전 결정 | PATCH 증가 `v1.0.3`. **SaveData 구조 변경 금지** 확인 (`CurrentVersion` diff 없음) | `git diff v1.0.2 -- Assets/_CoinRush/Scripts/Save/Core/` 가 비어 있음 |
| 2 | 태그 | `git tag -a v1.0.3 -m "hotfix: 결과 화면 NRE (패드 재연결)"` → `git push origin v1.0.3` | CI 시작 |
| 3 | CI | 테스트 작업 통과 → Windows·Linux 빌드 아티팩트 | Actions 초록 |
| 4 | Addressables 상태 파일 | 빌드가 만든 `addressables_content_state.bin`을 `Releases/v1.0.3/`(저장소 밖 백업 또는 릴리스 첨부)에 보관 | 파일 존재 |
| 5 | 업로드 | 26장 VDF의 `Desc`를 `CoinRush 1.0.3 - ...`로, `SetLive "beta"` → steamcmd 업로드 | Builds 페이지에 새 BuildID |
| 6 | beta 검증 | 제보자에게 beta 비밀번호 전달, 본인은 Windows·Deck에서 **재현 절차 + 스모크(첫 실행→한 판→종료)** | 제보자 확인 또는 2시간 무문제 |
| 7 | 출시 | Steamworks 웹에서 BuildID를 **default에 Set Live**, 태그 메시지에 BuildID 추가(`git tag -f`로 덮지 말고 릴리스 노트에 기록) | default 반영 |
| 8 | 이전 빌드 보존 | 직전 BuildID(v1.0.2)를 `previous` 브랜치에 Set Live | 롤백 경로 확보 |
| 9 | 공지 | Steam 이벤트(패치노트, 한/영), 제보 스레드에 답글 | 게시 |
| 10 | 관찰 48시간 | 리뷰·토론·`previous_session_abnormal_exit` 비율(24장 집계) 비교 | 악화 없음 |

**롤백 런북** (새 빌드가 더 나쁠 때):

1. Steamworks Builds 페이지 → default 브랜치에 **직전 BuildID를 Set Live**. 즉시 반영되며 플레이어는 다음 실행 시 이전 버전을 받습니다.
2. 세이브 호환성 확인: 1번 규칙(PATCH에서 세이브 구조 변경 금지)을 지켰다면 문제없습니다. 지키지 못했다면 새 세이브를 가진 플레이어는 옛 버전에서 `FutureSaveVersionException` 로그와 함께 저장이 막힙니다(10장). 이 경우 롤백보다 **수정 빌드를 빨리 내는 것**이 대개 낫습니다.
3. Git: 문제 커밋을 `git revert`로 되돌린 `v1.0.4`를 준비합니다. 태그를 지우거나 옮기지 않습니다(이미 배포된 이름).
4. 공지: "1.0.3에서 문제가 확인되어 1.0.2로 되돌렸습니다" + 영향 범위.

### 확인하기

- `git status`에 `Library/`·`Temp/`가 없고, `git lfs ls-files`에 PNG·WAV가 보인다. 다른 폴더에 저장소를 새로 클론해 Unity로 열어도 Missing 참조가 없다.
- 2단계 연습 충돌에서 두 프리팹 변경이 모두 살아 있다.
- 3단계 시나리오 A·B·C를 모두 해 보았고, `v0.1.0` 태그가 원격에 있다.
- Test Runner에서 EditMode(10장 + `RandomLogicTests` + `BalanceRegressionTests`)와 PlayMode(`BootSmokeTests`)가 모두 초록이다. `BalanceSimulator`의 코인 제단 가격 계산을 일부러 바꾸면 `Baseline_Clear_Rate_Stays_In_Target_Band`가 실패하거나(밴드 이탈) 결정성 테스트는 통과한다.
- 명령행 테스트가 종료 코드 0을 내고, 테스트 하나를 일부러 실패시키면 0이 아닌 값을 낸다. CI에서 테스트 실패 시 build 작업이 건너뛰어진다.
- 개발 빌드에서 디버그 예외를 두 번 일으키면 `crash_reports/`에 리포트가 **한 개**만 생기고, 버전·OS·씬·최근 로그가 들어 있다. `ForceCrash` 후 재실행하면 경고 로그와 `previous_session_abnormal_exit` 이벤트가 남는다.
- 핫픽스 런북을 `v0.1.1`로 한 번 끝까지(beta 업로드 → default Set Live → previous 보존) 연습했다.

## 흔한 실수

1. **증상**: 다른 PC·CI에서 프로젝트를 열면 프리팹·스크립트 참조가 전부 Missing. → **원인**: `.meta` 파일 누락, 또는 탐색기에서 파일을 옮겨 GUID가 새로 생성됨. → **해결**: `.meta`를 항상 함께 커밋, 에셋 이동은 Unity Project 창에서만. `git status`에서 `.meta` 없이 에셋만 추가된 경우를 확인합니다.
2. **증상**: push가 용량 초과로 거부되거나 저장소 클론이 수십 GB. → **원인**: LFS 설정 전에 바이너리를 커밋. → **해결**: `.gitattributes`를 첫 커밋 전에 만들기. 이미 커밋했다면 `git lfs migrate`로 히스토리를 옮겨야 하므로, 원격 공유 전이라면 저장소를 새로 만드는 편이 단순합니다.
3. **증상**: 병합 후 씬이 열리지 않거나 오브젝트가 사라짐. → **원인**: Git 기본 줄 병합이 Unity YAML 참조를 깨뜨림. → **해결**: UnityYAMLMerge 등록, 씬 분할·프리팹화로 예방, 실패 시 한쪽 파일 선택 후 에디터에서 재작업.
4. **증상**: 테스트 asmdef에서 `WeightedRandom`·`Health`를 찾지 못함. → **원인**: 테스트 어셈블리는 `Assembly-CSharp`를 참조할 수 없음. → **해결**: 테스트할 순수 로직을 asmdef(`CoinRush.Logic`)로 분리하고 참조 추가. MonoBehaviour 전체를 옮기기보다 로직을 순수 클래스로 빼는 편이 안전합니다.
5. **증상**: 핫픽스를 올렸더니 새 버그가 생김. → **원인**: main(미완성 기능 포함)에서 빌드, 테스트 없이 default에 바로 Set Live. → **해결**: 출시 태그에서 `release/*` 브랜치, CI 테스트 통과 후 beta 검증, 그다음 default.
6. **증상**: 제보는 "멈춰요"뿐이고 재현이 안 됨. → **원인**: 버전·플랫폼·순서·로그 없이 제보를 받음. → **해결**: 타이틀에 버전 표시, 제보 양식 고정, 게임 안에서 로그 폴더 열기 제공, 재현 조건을 로그의 마지막 줄부터 좁힙니다.

## 연습 문제

**1. ★★☆ 스모크 테스트용 세이브 격리**
6단계 스모크 테스트가 개발자의 실제 세이브를 건드리지 않게 만드세요. 조건: 테스트 어셈블리는 `Assembly-CSharp`를 참조하지 않는다.

<details>
<summary>힌트·해설</summary>

테스트가 게임 코드를 직접 부를 수 없으니 **둘 다 볼 수 있는 통로**를 씁니다. 방법 ①: 명령행 인수 — `SaveSystem`이 `Environment.GetCommandLineArgs()`에 `-coinrushSaveFolder <이름>`이 있으면 `UseUserFolder`(26장)를 호출하게 하고, CI에서 이 인수로 실행합니다(에디터 Test Runner에서는 적용 안 됨). 방법 ②: `CoinRush.SaveCore`에 `SaveLocationOverride`라는 정적 클래스(`public static string FolderName`)를 두고 `SaveSystem`이 읽게 합니다. `CoinRush.SaveCore`는 asmdef라 테스트가 참조할 수 있으므로 `[UnitySetUp]`에서 `SaveLocationOverride.FolderName = "playmode-test"`를 설정하고 `[UnityTearDown]`에서 폴더를 지웁니다. 방법 ②는 에디터와 CI 모두에서 동작합니다. 주의: `SaveSystem`의 정적 캐시(`current`)가 이미 로드됐다면 폴더를 바꿔도 반영되지 않으니, 10장의 `ResetStatics`처럼 캐시를 비우는 경로도 필요합니다.

</details>

**2. ★★☆ 버그 → 테스트 → 수정**
다음 가상 제보를 이 장의 절차로 처리하세요. "v1.0.2: 레벨업 창에서 같은 업그레이드가 3장 모두 나올 때가 있음." `ShuffleBag`을 쓰는 11장 선택지 코드에 원인이 있다고 가정하고, 실패하는 EditMode 테스트를 먼저 쓴 뒤 고치세요.

<details>
<summary>힌트·해설</summary>

"3장 뽑기"를 게임 코드에서 순수 함수로 꺼내 `CoinRush.Logic`에 둡니다. 예: `public static void PickDistinct<T>(ShuffleBag<T> bag, int count, List<T> results, int maxAttempts = 50)` — 이미 뽑힌 항목이면 다시 뽑고, 후보 종류가 `count`보다 적으면 가능한 만큼만 채웁니다. 테스트: 종류 5개(가중치 서로 다름) 백에서 1,000번 `PickDistinct(bag, 3, results)`를 호출해 `results`에 중복이 없음을 `CollectionAssert.AllItemsAreUnique`로 검사하고, 종류가 2개뿐인 백에서는 결과가 2개임을 검사합니다. 원래 코드가 `bag.Next()`를 3번 연속 호출했다면 가중치가 큰 항목은 한 사이클 안에 여러 번 들어 있으므로 첫 테스트가 실패합니다(빨강). 수정 후 초록 → 수정과 테스트를 한 커밋에 넣고, `release/1.0`에서 `v1.0.3`으로 런북을 따릅니다.

</details>

**3. ★★★ 크래시 수집 서비스 도입 결정 (확장 과제)**
코인 러시의 Unity 버전(6000.0 LTS 또는 6.2 이상 중 실제 사용 버전) 기준으로, Unity Diagnostics(또는 Cloud Diagnostics)와 외부 서비스 하나(Sentry 등)를 공식 문서로 비교하는 결정 문서를 쓰세요. 항목: 지원 플랫폼(Windows·Linux/Deck·Android), 네이티브 크래시·심볼 업로드, 무료 한도와 초과 비용, 데이터 보관 지역, 개인정보·동의 요구, 설치 작업량, 서비스 종료 위험. 선택한 서비스를 개발 빌드에 붙여 8단계의 디버그 예외·`ForceCrash`가 대시보드에 나타나는지 확인하세요.

<details>
<summary>힌트·해설</summary>

- 먼저 공식 문서에서 **현재 상태**를 확인합니다. Cloud Diagnostics는 deprecated로 표시되어 있어, 새로 도입한다면 6.2 이상의 Diagnostics 또는 외부 서비스가 후보입니다. 에디터 버전을 올리는 비용(재테스트)도 결정 문서에 넣습니다.
- 서비스는 **24장 `Analytics`처럼 래퍼 뒤에** 둡니다. `CrashLogCollector`가 리포트를 만든 지점에 `ICrashSink` 인터페이스를 두고 로컬 파일 싱크와 서비스 싱크를 함께 등록하면, 서비스를 바꾸거나 끄는 것이 한 줄 변경이 됩니다.
- 개인정보: 기기 모델·OS·IP가 전송될 수 있으므로 28장 개인정보처리방침의 "수집 항목·목적·보관 기간·국외 이전"을 갱신하고, 24장 동의를 받은 경우에만 서비스 싱크를 활성화하는 설계를 검토합니다.
- 결정 기준 예: "Deck 네이티브 빌드의 네이티브 크래시를 받을 수 있는가"가 안 되면 탈락. 코인 러시는 Steam 유료가 1차 출시라 모바일 ANR 수집은 우선순위가 낮습니다.

</details>

## 셀프 체크

**1. `.meta` 파일을 커밋하지 않거나 파일을 탐색기에서 옮기면 왜 참조가 깨지는지 설명해 보세요.**

<details>
<summary>모범 답안</summary>

Unity는 씬·프리팹·ScriptableObject가 다른 에셋을 참조할 때 경로가 아니라 `.meta` 파일에 적힌 GUID로 연결합니다. `.meta`가 없으면 다른 PC에서 Unity가 그 에셋에 새 GUID를 만들어, 기존 GUID를 가리키던 참조는 대상을 찾지 못해 Missing이 됩니다. 탐색기에서 파일만 옮기면 `.meta`가 따라가지 않아 Unity가 "옛 파일 삭제 + 새 파일 추가"로 인식하고 같은 문제가 생깁니다. 그래서 `.meta`를 항상 함께 커밋하고 이동은 Unity 안에서 합니다.

</details>

**2. push한 커밋을 되돌릴 때 `reset --hard` + `push --force` 대신 `revert`를 쓰는 이유는?**

<details>
<summary>모범 답안</summary>

`reset` + 강제 push는 원격 히스토리를 다시 써서, CI 기록·태그·다른 PC의 로컬 저장소가 가리키는 커밋과 어긋나고, 다른 곳에서 그 커밋을 기반으로 작업했다면 작업이 사라지거나 충돌이 납니다. `revert`는 되돌리는 변경을 새 커밋으로 추가하므로 히스토리가 보존되고, "언제 무엇을 왜 되돌렸는지"가 기록에 남으며, 필요하면 revert를 다시 revert할 수도 있습니다.

</details>

**3. 테스트 어셈블리가 게임 코드를 바로 참조하지 못하는 이유와, 코인 러시가 택한 해결책은?**

<details>
<summary>모범 답안</summary>

asmdef로 만든 어셈블리(테스트 포함)는 asmdef가 없는 기본 어셈블리 `Assembly-CSharp`를 참조할 수 없습니다. 게임 전체를 asmdef로 쪼개면 해결되지만 초보자에게 의존성 관리 부담이 큽니다. 코인 러시는 테스트 가치가 높은 순수 로직(세이브 코어, 가중치 랜덤, 셔플 백, 밸런스 시뮬레이터)만 `CoinRush.SaveCore`·`CoinRush.Logic` asmdef로 분리했습니다. 게임 코드는 Auto Referenced로 그대로 쓰고, 테스트는 이 어셈블리만 참조합니다. 씬 수준 검증은 게임 코드를 참조하지 않고 씬·오브젝트 이름으로 조작하는 PlayMode 스모크 테스트로 합니다.

</details>

**4. 밸런스 회귀 테스트에서 "결정성 테스트"와 "기준 밴드 테스트"는 각각 무엇을 잡나요? 밸런스를 의도적으로 바꾸면 어떻게 하나요?**

<details>
<summary>모범 답안</summary>

결정성 테스트는 같은 seed로 두 번 돌린 결과가 같은지 봅니다. 시뮬레이터에 `UnityEngine.Random`이나 시각 같은 비결정 요소가 섞여 조정 전후 비교가 불공정해지는 것을 잡습니다. 기준 밴드 테스트는 기준 시나리오의 클리어율·생존 시간이 합의한 범위 안에 있는지 봐서, 다른 목적의 코드 변경이 난이도를 조용히 바꾸는 회귀를 잡습니다. 의도적으로 밸런스를 바꿨다면 테스트의 밴드나 기준 수치를 같은 커밋에서 갱신하고 이유를 커밋 메시지에 적습니다.

</details>

**5. 핫픽스를 main이 아니라 출시 태그에서 시작하고, PATCH 버전에서 세이브 구조를 바꾸지 않는 이유는?**

<details>
<summary>모범 답안</summary>

main에는 출시 이후의 미완성 기능이 섞여 있어, 그대로 빌드하면 고치려던 버그 외의 변경이 함께 배포되어 새 문제가 생길 수 있습니다. 태그에서 만든 `release/*` 브랜치는 출시 빌드와 정확히 같은 코드에 수정만 더합니다. PATCH에서 세이브 구조를 올리지 않는 이유는 롤백 가능성 때문입니다. 새 버전이 세이브 버전을 올리면 이전 빌드로 되돌렸을 때 옛 버전이 그 세이브를 읽지 못하고(10장 미래 버전 보호로 저장도 막힘) 플레이어는 진행을 잃은 것처럼 보게 됩니다.

</details>

## 핵심 요약

- Unity 프로젝트는 `Assets`(+`.meta`)·`Packages`·`ProjectSettings`만 Git에 넣고, Visible Meta Files·Force Text를 확인하며, `.gitattributes`로 바이너리를 **첫 커밋 전에** LFS로 보냅니다. 에셋 이동은 Unity 안에서만.
- 1인 개발의 브랜치 규칙: 항상 빌드되는 `main`, 짧은 `feature/*`, 출시 빌드마다 `vX.Y.Z` 태그, 핫픽스는 태그에서 만든 `release/*`. Steam 브랜치(internal/beta/default/previous)와 짝을 맞춥니다.
- push 전 실수는 `restore`·`reset --soft`, push 후는 `revert`, 잃어버린 커밋은 `reflog`. main에서 강제 push는 하지 않습니다.
- 씬·프리팹 충돌은 씬 분할·프리팹화로 예방하고 UnityYAMLMerge로 병합합니다.
- 테스트 어셈블리는 `Assembly-CSharp`를 참조할 수 없으므로 순수 로직을 asmdef로 분리해 EditMode 회귀 테스트(무작위 로직·밸런스 결정성·기준 밴드·세이브 마이그레이션)를 쓰고, 씬 흐름은 이름 기반 PlayMode 스모크 테스트로 "오류 로그 0"을 검사합니다.
- 명령행 `-runTests`와 CI에서 테스트 → 빌드 순서로 묶어, 테스트가 실패하면 출시 아티팩트가 만들어지지 않게 합니다.
- 로그 위치를 알고, 로컬 크래시 수집기(최근 로그 링 버퍼·중복 제거·비정상 종료 감지·로그 폴더 열기)로 제보를 재현 가능한 정보로 바꿉니다. Unity Cloud Diagnostics는 deprecated이므로 서비스는 공식 문서의 현재 상태를 확인해 고릅니다.
- 핫픽스는 태그 → CI → beta 검증 → default Set Live → previous 보존 → 공지 → 48시간 관찰, 롤백은 이전 BuildID를 default에 Set Live. PATCH에서는 세이브 구조를 바꾸지 않습니다.

## 더 읽을거리

- github/gitignore — Unity.gitignore: https://github.com/github/gitignore/blob/main/Unity.gitignore
- Unity 매뉴얼 — Smart Merge (UnityYAMLMerge): https://docs.unity3d.com/6000.0/Documentation/Manual/SmartMerge.html
- Unity 매뉴얼 — Version control integrations / Log files: https://docs.unity3d.com/6000.0/Documentation/Manual/Versioncontrolintegration.html · https://docs.unity3d.com/6000.0/Documentation/Manual/log-files.html
- Unity 매뉴얼 — Unity Test Framework (6.2+ 사용자 가이드): https://docs.unity3d.com/6000.2/Documentation/Manual/test-framework/test-framework-introduction.html
- Unity 문서 — Cloud Diagnostics 크래시·예외 리포팅(deprecated 안내) / Unity 6.2 Diagnostics 설정: https://docs.unity.com/en-us/cloud-diagnostics/crash-and-exception-reporting/about-crash-and-exception-reporting · https://docs.unity3d.com/6000.2/Documentation/Manual/diagnostics-settings.html
- Steamworks 문서 — Branches (Betas), default 브랜치 수동 Set Live: https://partner.steamgames.com/doc/store/application/branches
- Git LFS: https://git-lfs.com/
