# 10. 세이브 시스템 — 버전과 마이그레이션

> **이 장에서 배울 것**
> - `PlayerPrefs`의 한계를 설명하고, 설정값과 게임 진행 데이터의 저장 위치를 구분할 수 있다
> - `JsonUtility`와 Newtonsoft Json의 제약·장단점을 비교해 선택한다
> - `version` 필드를 가진 `SaveData`를 설계하고, v1→v2 마이그레이션 체인을 구현한다
> - 임시 파일 + 교체로 원자적 저장을 구현하고, 백업 파일·해시로 손상에 대비한다
> - 모바일 생명주기에 맞춘 저장 타이밍을 정하고, 마이그레이션을 EditMode 테스트로 검증한다
>
> **선수 장**: 01, 03, 09 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 판이 끝나면 코인이 쌓이고, 타이틀에서 최대 체력을 영구 강화할 수 있으며, 게임 업데이트로 세이브 구조가 바뀌어도 기존 세이브가 살아남음

## 왜 필요한가

기초 트랙의 코인 먹기는 `PlayerPrefs.SetInt("highScore", Score)`로 최고 점수를 저장했습니다. 코인 러시에 "코인으로 영구 강화"를 넣으며 `coins`, `upgrade_maxHp`, `best_time`… 키를 계속 늘려 가면, 키 오타가 조용히 0을 반환하는 것은 시작일 뿐이고 출시 후에 진짜 문제가 터집니다.

1. **1.1 업데이트에서 강화 구조를 "레벨 숫자"에서 "강화 ID별 사전"으로 바꿨더니, 1.0 유저들의 강화가 전부 0으로 초기화됐습니다.** 스토어에 "업데이트했더니 세이브 날아감 ★1" 리뷰가 달립니다.
2. **저장 도중 폰 배터리가 꺼진** 유저의 세이브 파일이 절반만 쓰여 JSON 파싱에 실패하고, 게임이 시작 화면에서 멈춥니다.
3. Android에서 게임을 **홈 버튼으로 내렸다가 OS가 프로세스를 정리**하자, 방금 얻은 코인이 저장되지 않았습니다. `OnApplicationQuit`에서 저장했는데 호출되지 않았기 때문입니다.

이 장은 이 세 가지를 막는 세이브 시스템을 만듭니다. 핵심은 **버전 필드와 마이그레이션, 원자적 저장, 올바른 저장 타이밍**입니다.

## 개념

### PlayerPrefs의 한계

| 항목 | PlayerPrefs | 파일 저장(JSON) |
|---|---|---|
| 저장 위치 | Windows 레지스트리, macOS/iOS plist, Android SharedPreferences | `Application.persistentDataPath` 아래 파일 |
| 데이터 형태 | 키-값(int, float, string)만 | 중첩 구조, 리스트, 사전 |
| 버전 관리·마이그레이션 | 직접 키로 흉내 내야 함 | `version` 필드 + 변환 함수 |
| 클라우드 동기화(Steam Auto-Cloud 등) | 레지스트리라 어려움 | 파일 경로 지정으로 가능 |
| 적합한 용도 | **기기별 설정**(볼륨, 키 설정, 그래픽 품질, 마지막 선택 언어) | **게임 진행 데이터**(재화, 강화, 해금, 통계) |

08장에서 키 바인딩을 `PlayerPrefs`에 둔 것은 "설정"이기 때문입니다. 코인·강화처럼 잃어버리면 유저가 화내는 데이터는 파일로 저장합니다.

### Application.persistentDataPath

앱이 쓰기 권한을 가진, 업데이트해도 지워지지 않는 폴더입니다. Windows에서는 `%USERPROFILE%\AppData\LocalLow\<회사명>\<제품명>`이고, 플랫폼마다 다르므로 `Debug.Log(Application.persistentDataPath)`로 확인하세요.

`Application.dataPath`(빌드 내부, 읽기 전용일 수 있음)나 `Assets/` 경로에 쓰면 빌드에서 실패합니다. 또 `Player Settings`의 회사명·제품명을 바꾸면 Windows/macOS 경로가 바뀌어 **기존 세이브를 못 찾게** 되므로 출시 후에는 바꾸지 마세요.

### JsonUtility vs Newtonsoft Json

| 항목 | `JsonUtility` (내장) | Newtonsoft (`com.unity.nuget.newtonsoft-json`) |
|---|---|---|
| 속도·할당 | 빠르고 적음 | 상대적으로 느리고 많음 (세이브 크기에선 무시 가능) |
| `Dictionary<K,V>` | **불가** (조용히 무시) | 가능 |
| 프로퍼티 | **불가** — public 필드 또는 `[SerializeField]` 필드만 | 가능 |
| 모르는 구조를 읽어 변형 | 불가 | **`JObject`로 가능 — 마이그레이션에 결정적** |
| IL2CPP 코드 스트리핑 | 문제 없음 | 리플렉션 사용 → 드물게 필드 누락, `link.xml`/`[Preserve]`로 해결 |

마이그레이션은 "옛 구조의 JSON을 **현재 클래스로 읽기 전에** 변형"해야 하는데, `JsonUtility`는 클래스로만 읽을 수 있어 이 작업이 매우 번거롭습니다. 그래서 코인 러시는 Newtonsoft를 씁니다.

### SaveData 설계 원칙

1. **`version` 필드는 첫날부터.** v1에 버전 필드가 없으면, 나중에 "이 파일이 몇 버전인지" 추측하는 코드를 영원히 유지해야 합니다.
2. **데이터만, 로직 없음.** `SaveData`는 순수 데이터 클래스(DTO)입니다. "강화 비용 계산"은 다른 곳에 둡니다.
3. **ID는 문자열, 에셋 참조는 저장하지 않음.** `WeaponData` 에셋 자체가 아니라 `"orb"` 같은 ID를 저장합니다. 에셋 이름·경로·GUID가 바뀌어도 세이브가 깨지지 않게 합니다.
4. **기본값이 의미 있게, 이름은 바꾸지 않게.** 새 필드는 누락되어도 초기값으로 안전해야 하고, 필드 이름 변경은 곧 마이그레이션입니다.

### 마이그레이션 체인

버전마다 **"직전 버전 → 다음 버전"** 변환 함수 하나만 작성하고, 로드할 때 현재 버전에 도달할 때까지 차례로 적용합니다.

```
파일 v1 ──V1ToV2──▶ v2 ──V2ToV3──▶ v3 (현재) ──▶ SaveData로 역직렬화
파일 v2 ─────────────▶ v2 ──V2ToV3──▶ v3
파일 v3 ────────────────────────────▶ v3
파일 v4 (미래 버전) ──▶ 읽지 않음, 저장도 막음 (구버전 앱으로 다운그레이드한 경우)
```

- v1→v3 직통 함수를 따로 만들지 않습니다. 버전이 N개면 조합이 폭발하기 때문입니다.
- 변환은 **JSON 트리(`JObject`) 위에서** 합니다. 옛 버전의 C# 클래스는 이미 사라졌기 때문입니다.
- **한 번 출시한 변환 함수는 절대 수정하지 않습니다.** 이미 그 경로로 변환된 유저가 있습니다.
- **미래 버전 파일**을 만나면 덮어쓰지 않습니다. 구버전 앱이 새 세이브를 "초기 데이터"로 덮어쓰면 복구가 불가능합니다.

### 원자적 저장 — 반쯤 쓰인 파일 막기

`File.WriteAllText(path, json)`은 기존 파일을 **먼저 비우고** 씁니다. 그 사이 앱이 죽으면 빈 파일 또는 잘린 JSON이 남습니다.

```
[나쁜 방법]  save.json 비우기 → 쓰기 중... 💥 전원 꺼짐 → save.json = "{"version":2,"coi"  (손상)

[원자적 저장] 1. save.json.tmp에 전체 쓰기 + 디스크 플러시   (💥 여기서 죽어도 save.json은 멀쩡)
             2. File.Replace(tmp → save.json, 이전 것은 save.backup.json)  (이름 바꾸기라 거의 원자적)
```

`File.Replace`가 지원되지 않는 환경을 대비해 "백업으로 복사 → 원본 삭제 → 이동" 순서의 대체 경로도 둡니다. 이 경로는 완전히 원자적이지 않지만, 중간에 죽어도 **백업 파일이 남아 있어** 복구할 수 있습니다.

두 경로 모두 "지금 본 파일은 정상"이라는 전제가 있습니다. 본 파일이 손상되어 백업으로 복구한 직후에 그대로 저장하면, 손상된 본 파일이 **정상 백업 위로 옮겨져** 두 파일이 모두 못 쓰게 될 수 있습니다. 그래서 손상을 발견하면 다음 저장 전에 손상본을 별도 파일(`save.corrupt.json`)로 **격리**하고, 정상 백업은 새 본 파일이 완성될 때까지 건드리지 않습니다.

### 손상 대비 — 백업과 해시

로드 순서는 **본 파일 → 백업 파일 → 새 데이터**입니다. 파일이 손상되었는지 알기 위해 JSON 파싱 성공 여부와 함께 간단한 **해시(체크섬)** 를 확인합니다.

세이브 파일은 `{ "hash": "…", "payload": { … } }` 형태로 두고, 해시는 `payload`를 압축 문자열로 만든 것 + 고정 문자열(솔트)을 SHA-256으로 계산합니다. JSON이 잘려 파싱이 실패하면 백업으로 넘어가고, 파싱은 되는데 해시가 다르면(일부 손상 또는 텍스트 편집기로 코인을 고친 경우) 이를 알아챌 수 있습니다.

**하지만 싱글 게임의 치팅 방지에 과투자하지 마세요.**

| 게임 유형 | 권장 수준 |
|---|---|
| 오프라인 싱글 (코인 러시 Steam판) | 손상 감지용 체크섬 정도. 수정한 유저는 자기 재미를 바꾼 것일 뿐 |
| 오프라인 + 유료 재화 IAP | 재화 지급 기록은 영수증 검증(25장)으로. 로컬 암호화는 시간 벌기일 뿐 |
| 랭킹·PvP·거래 | **서버가 진실의 원천**. 클라이언트 저장은 캐시로만 취급 |

솔트와 해시 코드는 게임 바이너리 안에 있으므로 마음먹은 사람은 반드시 뚫습니다. 암호화·난독화에 들일 시간을 콘텐츠에 쓰는 것이 1인 개발자에게 이득입니다. 코인 러시는 해시가 틀려도 **파싱과 구조 검증(필수 묶음·버전·값 범위)을 통과하면 경고만 남기고 받아들이는** 관대한 정책을 택합니다. 파싱은 되지만 `"stats": null`처럼 비어 있는 묶음, 음수 코인처럼 바로잡을 수 있는 값은 로드 시 정규화하고, 타입이 틀렸거나 버전이 맞지 않는 등 바로잡을 수 없는 파일은 손상으로 보고 백업으로 넘어갑니다.

### 저장 타이밍 — 모바일 생명주기

| 시점 | 호출 보장 | 비고 |
|---|---|---|
| 중요한 순간 직후 (판 종료, 구매, 강화) | 코드가 직접 호출 | **가장 확실. 기본 전략** |
| `OnApplicationPause(true)` | 모바일에서 백그라운드로 갈 때 호출 | 이후 OS가 예고 없이 프로세스를 죽일 수 있음 → 여기서 저장 |
| `OnApplicationQuit` | PC 정상 종료 시 | **모바일에서는 호출되지 않는 경우가 많음** — 여기에만 의존 금지 |
| 매 프레임 / 코인 하나 먹을 때마다 | – | 디스크 I/O 낭비. 대신 "dirty 표시 → 의미 있는 시점에 저장" |

### 클라우드 세이브 개요

- **Steam Cloud(Auto-Cloud)**: Steamworks 설정에서 경로·파일 패턴만 지정하면 코드 수정 없이 동기화됩니다(26장).
- **UGS Cloud Save**(`com.unity.services.cloudsave`): Authentication 로그인 후 키-값으로 저장하는 크로스플랫폼 서비스입니다. API 이름이 패키지 버전에 따라 다르니 공식 문서를 확인하세요.
- **Google Play Games 저장된 게임 / iCloud**: 모바일 플랫폼 SDK를 씁니다.

어떤 서비스든 **충돌 해결 규칙**이 필요합니다(폰과 태블릿에서 각각 플레이한 경우). 흔한 선택은 "마지막 저장 시각이 최신인 것", "총 플레이 시간이 긴 것", 또는 "유저에게 둘을 보여주고 선택"입니다. 이를 위해 `SaveData`에 `savedAtUtc`, `totalPlaySeconds` 같은 메타데이터를 두면 나중에 편합니다.

## 실습: 코인 러시에 적용하기

앞 장의 최소 시그니처입니다.

```csharp
// 01장 Health           : int Current, int Max, event Action<int,int> Changed, event Action Died, TakeDamage(int)
// 03장 IntEventChannel  : event Action<int> OnRaised, void Raise(int)   — 코인 획득량
// 03장 VoidEventChannel : event Action OnRaised, void Raise()
// 09장 Bootstrap 씬에 Managers 오브젝트
```

이 실습은 **일부러 v1으로 출시한 뒤 v2로 업데이트하는 과정**을 따라갑니다. 1~5단계가 "1.0 버전", 6단계가 "1.1 업데이트"입니다.

### 1단계: 패키지와 폴더, 어셈블리 정의

1. `Window > Package Manager` → 좌상단 `+` → `Add package by name...` → `com.unity.nuget.newtonsoft-json` 입력 → Add.
2. 폴더를 만듭니다: `Assets/_CoinRush/Scripts/Save/Core/`, `Assets/_CoinRush/Tests/EditMode/`.
3. `Save/Core/`에서 우클릭 → `Create > Scripting > Assembly Definition`, 이름 `CoinRush.SaveCore`. 설정은 기본값(Auto Referenced 체크)으로 둡니다.

왜 어셈블리 정의가 필요할까요? 테스트 어셈블리는 기본 어셈블리(`Assembly-CSharp`)를 참조할 수 없습니다. 테스트할 순수 로직(데이터, 직렬화, 마이그레이션, 파일 저장)을 별도 어셈블리로 떼어 내면 테스트가 참조할 수 있고, `Assembly-CSharp`의 게임 코드는 Auto Referenced 덕분에 그대로 사용합니다.

### 2단계: SaveData v1과 저장 코어

```csharp
using System;

// Assets/_CoinRush/Scripts/Save/Core/SaveData.cs  — 1.0 출시 버전
[Serializable]
public class SaveData
{
    public const int CurrentVersion = 1;

    public int version = CurrentVersion;
    public int coins;
    public int maxHpLevel;
    public float bestSurvivalSeconds;

    // 로드 직후 호출: 파싱은 됐지만 값이 비정상(음수 등)인 경우를 복구 가능한 범위에서 바로잡음.
    // 게임 규칙이 아니라 "데이터가 유효한 모양인가"만 다루므로 DTO에 둡니다.
    public void Normalize()
    {
        if (coins < 0) coins = 0;
        if (maxHpLevel < 0) maxHpLevel = 0;
        if (float.IsNaN(bestSurvivalSeconds) || bestSurvivalSeconds < 0f) bestSurvivalSeconds = 0f;
    }
}
```

```csharp
using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

// Assets/_CoinRush/Scripts/Save/Core/SaveMigrator.cs
public static class SaveMigrator
{
    // key = 변환 전 버전. 한 번 출시한 함수는 수정하지 않는다.
    private static readonly Dictionary<int, Action<JObject>> Steps = new()
    {
        // 1.1 업데이트(6단계)에서 추가
    };

    public static void MigrateToCurrent(JObject root)
    {
        int version = root.Value<int?>("version") ?? 1;   // 필드가 없으면 v1로 간주
        if (version > SaveData.CurrentVersion)
            throw new FutureSaveVersionException(version);

        while (version < SaveData.CurrentVersion)
        {
            if (!Steps.TryGetValue(version, out Action<JObject> step))
                throw new InvalidOperationException($"v{version} → v{version + 1} 마이그레이션이 없습니다.");
            step(root);
            version++;
            root["version"] = version;
        }
    }
}

public class FutureSaveVersionException : Exception
{
    public FutureSaveVersionException(int fileVersion)
        : base($"세이브 버전 {fileVersion}이 앱이 아는 버전 {SaveData.CurrentVersion}보다 높습니다.") { }
}
```

```csharp
using System;
using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

// Assets/_CoinRush/Scripts/Save/Core/SaveSerializer.cs
public enum SaveReadStatus { Ok, HashMismatch }

public static class SaveSerializer
{
    // 보안 장치가 아니라 손상 감지용. 바이너리에 들어 있으므로 비밀이 아님.
    private const string Salt = "coin-rush::save";

    private static readonly JsonSerializer Serializer = JsonSerializer.Create(new JsonSerializerSettings
    {
        // 기본값 Reuse는 필드 초기값 리스트에 로드한 항목을 "덧붙임" → Replace로
        ObjectCreationHandling = ObjectCreationHandling.Replace,
    });

    public static string Serialize(SaveData data)
    {
        JObject payload = JObject.FromObject(data, Serializer);
        var envelope = new JObject
        {
            ["hash"] = ComputeHash(payload),
            ["payload"] = payload,
        };
        return envelope.ToString(Formatting.Indented);   // 사람이 읽기 쉽게 (디버깅·지원 문의 대응)
    }

    // 파싱 실패·구조 이상은 예외(→ 백업 복구 대상), 미래 버전은 FutureSaveVersionException.
    // 해시 불일치는 status로 알림.
    public static SaveData Deserialize(string json, out SaveReadStatus status)
    {
        JObject envelope = JObject.Parse(json);            // 잘린 JSON이면 JsonReaderException
        if (envelope["payload"] is not JObject payload)
            throw new JsonException("payload가 없습니다.");

        string storedHash = envelope.Value<string>("hash");
        status = storedHash == ComputeHash(payload) ? SaveReadStatus.Ok : SaveReadStatus.HashMismatch;

        SaveMigrator.MigrateToCurrent(payload);            // 해시는 변환 "전" 내용으로 검사
        SaveData data = payload.ToObject<SaveData>(Serializer)   // "coins": "abc" 같은 타입 오류도 여기서 예외
            ?? throw new JsonException("payload를 SaveData로 읽지 못했습니다.");
        if (data.version != SaveData.CurrentVersion)
            throw new JsonException($"마이그레이션 후 버전이 {data.version}입니다(기대: {SaveData.CurrentVersion}).");

        data.Normalize();                                  // null 묶음·음수 값은 복구 가능 → 바로잡고 사용
        return data;
    }

    private static string ComputeHash(JObject payload)
    {
        string canonical = Salt + payload.ToString(Formatting.None);
        using SHA256 sha = SHA256.Create();
        byte[] bytes = sha.ComputeHash(Encoding.UTF8.GetBytes(canonical));
        var sb = new StringBuilder(bytes.Length * 2);
        foreach (byte b in bytes) sb.Append(b.ToString("x2"));
        return sb.ToString();
    }
}
```

```csharp
using System;
using System.IO;
using System.Text;

// Assets/_CoinRush/Scripts/Save/Core/SaveFileStore.cs
public class SaveFileStore
{
    public string MainPath { get; }
    public string BackupPath { get; }
    public string CorruptPath { get; }   // 손상된 본 파일을 옮겨 두는 곳 (지원 문의 때 확인용)
    private string TempPath => MainPath + ".tmp";

    public SaveFileStore(string directory, string fileName = "save.json")
    {
        Directory.CreateDirectory(directory);
        string baseName = Path.GetFileNameWithoutExtension(fileName);
        MainPath = Path.Combine(directory, fileName);
        BackupPath = Path.Combine(directory, baseName + ".backup.json");
        CorruptPath = Path.Combine(directory, baseName + ".corrupt.json");
    }

    // 손상된 본 파일을 격리. 그대로 두면 다음 저장의 File.Replace(또는 대체 경로의 Copy)가
    // 손상본을 "백업"으로 옮겨 방금 복구에 쓴 정상 백업을 덮어씁니다.
    public void QuarantineMain()
    {
        if (!File.Exists(MainPath)) return;
        if (File.Exists(CorruptPath)) File.Delete(CorruptPath);
        File.Move(MainPath, CorruptPath);
    }

    public string ReadMainOrNull() => File.Exists(MainPath) ? File.ReadAllText(MainPath, Encoding.UTF8) : null;
    public string ReadBackupOrNull() => File.Exists(BackupPath) ? File.ReadAllText(BackupPath, Encoding.UTF8) : null;

    public void WriteAtomic(string text)
    {
        // 1) 임시 파일에 전부 쓰고 디스크까지 플러시
        using (var stream = new FileStream(TempPath, FileMode.Create, FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
        {
            writer.Write(text);
            writer.Flush();
            stream.Flush(flushToDisk: true);
        }

        // 2) 교체 — 이전 본 파일은 백업이 됨 (본 파일이 정상이라는 전제. 손상됐다면 호출자가 먼저 QuarantineMain)
        if (!File.Exists(MainPath)) { File.Move(TempPath, MainPath); return; }   // 백업은 건드리지 않음

        try
        {
            File.Replace(TempPath, MainPath, BackupPath);
        }
        catch (Exception e) when (e is PlatformNotSupportedException or IOException)
        {
            // 대체 경로: 완전 원자적이진 않지만 어느 순간에 죽어도 정상 백업 또는 본 파일 중 하나는 남음
            // (Delete 뒤 Move 전에 죽으면 본 파일은 없고, 백업 = 직전 정상 본 파일 → 로더가 백업에서 복구)
            File.Copy(MainPath, BackupPath, overwrite: true);
            File.Delete(MainPath);
            File.Move(TempPath, MainPath);
        }
    }

}
```

`.NET Standard 2.1` 환경인 Unity에는 `File.Move(src, dst, overwrite)` 오버로드가 없으므로, 덮어쓰기가 필요할 땐 위처럼 `File.Replace`나 삭제 후 이동을 씁니다.

### 3단계: SaveSystem — 게임 코드가 쓰는 입구

이 클래스는 Unity API(`Application.persistentDataPath`, `Debug`)를 쓰므로 `Core` 폴더 **밖**에 둡니다. 다른 장(12장 오디오 설정 등)이 `SaveSystem.Load()` / `SaveSystem.Save(data)`로 사용합니다.

```csharp
using System;
using System.IO;
using UnityEngine;

// Assets/_CoinRush/Scripts/Save/SaveSystem.cs
public enum SaveLoadStatus
{
    NotLoaded,
    NewGame,              // 파일 없음, 또는 본·백업 모두 손상 → 새 데이터
    LoadedMain,           // 본 파일 정상
    RecoveredFromBackup,  // 본 파일 없음/손상 → 백업으로 복구
    FutureVersion,        // 더 새 앱이 만든 세이브 → 읽기 전용
    AccessError,          // 권한·공유 위반 등 I/O 실패 → 읽기 전용 (파일은 멀쩡할 수 있으므로 덮어쓰지 않음)
}

public static class SaveSystem
{
    private enum ReadResult { Missing, Ok, Corrupt, AccessError, FutureVersion }

    private static SaveFileStore store;
    private static SaveData current;
    private static bool dirty;
    private static bool writeBlocked;                  // 미래 버전·접근 실패일 때 덮어쓰기 방지
    private static bool quarantineMainBeforeNextSave;  // 본 파일이 손상됐을 때 정상 백업 보호

    public static SaveLoadStatus LoadStatus { get; private set; } = SaveLoadStatus.NotLoaded;
    public static bool IsReadOnly => writeBlocked;     // UI가 구매·저장 버튼을 막는 데 사용

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStatics()   // 도메인 리로드를 꺼도 Play마다 새로 로드
    {
        store = null; current = null; dirty = false; writeBlocked = false;
        quarantineMainBeforeNextSave = false; LoadStatus = SaveLoadStatus.NotLoaded;
    }

    private static SaveFileStore Store => store ??= new SaveFileStore(Application.persistentDataPath);

    // 여러 곳에서 호출해도 같은 인스턴스를 반환 (처음 한 번만 디스크에서 읽음)
    public static SaveData Load() => current ??= LoadFromDisk();

    public static void MarkDirty() => dirty = true;

    // 디스크에 썼으면 true. 실패하면 false이고 dirty가 남아 SaveIfDirty가 다음 기회에 다시 시도
    public static bool Save(SaveData data)
    {
        current = data;
        if (writeBlocked)
        {
            Debug.LogWarning($"세이브 보호({LoadStatus}) 중이라 저장을 건너뜁니다.");
            return false;
        }

        dirty = true;   // 쓰기 "전에" 켬 → 아래에서 실패하면 그대로 남음
        try
        {
            if (quarantineMainBeforeNextSave)
            {
                Store.QuarantineMain();
                quarantineMainBeforeNextSave = false;
            }
            Store.WriteAtomic(SaveSerializer.Serialize(data));
            dirty = false;   // 성공했을 때만 해제
            return true;
        }
        catch (Exception e)
        {
            // 디스크 가득 참 등. 게임을 멈추지 말고 기록 + 호출자에게 실패를 알림
            Debug.LogException(e);
            return false;
        }
    }

    public static void SaveIfDirty() { if (dirty && current != null) Save(current); }

    private static SaveData LoadFromDisk()
    {
        ReadResult main = TryRead(backup: false, out SaveData data);
        if (main == ReadResult.Ok) { LoadStatus = SaveLoadStatus.LoadedMain; return data; }

        if (main == ReadResult.FutureVersion || main == ReadResult.AccessError)
        {
            // 본 파일을 덮어쓰면 안 되는 경우: 읽기 전용. 화면에는 백업(있으면)을 보여 줌
            writeBlocked = true;
            LoadStatus = main == ReadResult.FutureVersion ? SaveLoadStatus.FutureVersion : SaveLoadStatus.AccessError;
            return TryRead(backup: true, out data) == ReadResult.Ok ? data : new SaveData();
        }

        if (main == ReadResult.Corrupt) quarantineMainBeforeNextSave = true;

        ReadResult backupResult = TryRead(backup: true, out data);
        if (backupResult == ReadResult.Ok)
        {
            Debug.LogWarning("본 세이브가 없거나 손상되어 백업에서 복구했습니다.");
            LoadStatus = SaveLoadStatus.RecoveredFromBackup;
            dirty = true;   // 복구한 내용을 곧 본 파일로 다시 씀 (정상 백업은 그대로 보존)
            return data;
        }
        if (backupResult == ReadResult.FutureVersion || backupResult == ReadResult.AccessError)
        {
            writeBlocked = true;   // 새 데이터로 저장하면 결국 이 백업을 덮으므로 막음
            LoadStatus = backupResult == ReadResult.FutureVersion ? SaveLoadStatus.FutureVersion : SaveLoadStatus.AccessError;
            return new SaveData();
        }

        LoadStatus = SaveLoadStatus.NewGame;
        return new SaveData();
    }

    // 파일 읽기와 역직렬화를 "같은" try 안에서 → I/O 예외도 여기서 분류됨
    private static ReadResult TryRead(bool backup, out SaveData data)
    {
        data = null;
        string label = backup ? "백업 파일" : "본 파일";
        try
        {
            string json = backup ? Store.ReadBackupOrNull() : Store.ReadMainOrNull();
            if (json == null) return ReadResult.Missing;
            if (json.Length == 0) return ReadResult.Corrupt;   // 쓰기 중 잘려 비어 버린 파일

            data = SaveSerializer.Deserialize(json, out SaveReadStatus status);
            if (status == SaveReadStatus.HashMismatch)
                Debug.LogWarning($"{label}의 체크섬이 맞지 않습니다(수정 또는 손상). 구조 검증은 통과해 사용합니다.");
            return ReadResult.Ok;
        }
        catch (FutureSaveVersionException e)
        {
            Debug.LogError($"{label}: {e.Message} 앱을 최신 버전으로 업데이트해야 합니다.");
            return ReadResult.FutureVersion;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            Debug.LogError($"{label}에 접근하지 못했습니다: {e.Message}");
            return ReadResult.AccessError;
        }
        catch (Exception e)
        {
            Debug.LogWarning($"{label}이 손상되어 읽지 못했습니다: {e.Message}");
            data = null;
            return ReadResult.Corrupt;
        }
    }
}
```

로드 결과를 네 갈래로 나눈 이유는 대응이 다르기 때문입니다.

| 본 파일 상태 | 처리 | 다음 저장 |
|---|---|---|
| 없음 | 백업 → 없으면 새 데이터 | 새 본 파일 생성, 백업은 그대로 |
| 손상(파싱·구조 오류) | 백업으로 복구 | **먼저 손상본을 `save.corrupt.json`으로 격리** → 정상 백업이 덮이지 않음 |
| 접근 실패(권한·잠김) | 읽기 전용 | 막음 — 파일 자체는 멀쩡할 수 있음 |
| 미래 버전 | 읽기 전용 | 막음 — 구버전 앱이 새 세이브를 덮으면 복구 불가 |

### 4단계: 저장 타이밍과 영구 강화

**생명주기 저장**: Bootstrap 씬(09장)의 `Managers` 아래에 오브젝트를 만들고 붙입니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Save/SaveLifecycle.cs
public class SaveLifecycle : MonoBehaviour
{
    private void Awake() => SaveSystem.Load();   // 시작 시 한 번 읽어 둠 (첫 화면 끊김 방지)

    private void OnApplicationPause(bool paused)
    {
        if (paused) SaveSystem.SaveIfDirty();    // 모바일: 백그라운드 진입 = 마지막 기회일 수 있음
    }

    private void OnApplicationQuit() => SaveSystem.SaveIfDirty();   // PC용 보조
}
```

**판 결과 기록**: Game 씬에 둡니다. 코인 획득(03장 `IntEventChannel`)을 모아 두었다가, 판 종료 이벤트에서 한 번에 저장합니다. `Assets/_CoinRush/Events/`에 `VoidEventChannel` 에셋 `RunEnded`를 만듭니다. 04장 `ResultState`는 `GameStateMachine`을 통해서만 참조를 얻는 일반 C# 객체라 Inspector에 필드를 둘 수 없으므로, 채널은 머신에 두고 상태가 머신을 통해 발행합니다.

```csharp
// GameStateMachine.cs (04장) — [Header("채널·점수")] 아래에 필드 추가, 프로퍼티 목록에 한 줄 추가
[SerializeField] private VoidEventChannel runEnded;          // 10장: 판 종료 알림
public VoidEventChannel RunEnded => runEnded;

// ResultState.cs (04장) — Enter() 맨 끝에 추가
if (machine.RunEnded != null) machine.RunEnded.Raise();     // RunRecorder가 받아 코인·기록을 저장
```

1. Game 씬 `GameSystems`의 `GameStateMachine` → **Run Ended**에 `RunEnded` 에셋을 넣습니다.
2. Game 씬에 빈 오브젝트 `RunRecorder`를 만들고 아래 스크립트를 붙여 **Coin Collected** = `CoinCollected`, **Run Ended** = `RunEnded`를 연결합니다.

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Save/RunRecorder.cs
public class RunRecorder : MonoBehaviour
{
    [SerializeField] private IntEventChannel coinCollected;
    [SerializeField] private VoidEventChannel runEnded;

    private int runCoins;
    private float runSeconds;
    private bool committed;

    private void OnEnable()
    {
        coinCollected.OnRaised += OnCoinCollected;
        runEnded.OnRaised += Commit;
    }

    private void OnDisable()
    {
        coinCollected.OnRaised -= OnCoinCollected;
        runEnded.OnRaised -= Commit;
    }

    private void Update() => runSeconds += Time.deltaTime;   // 일시정지·레벨업(timeScale 0) 시간 제외

    private void OnCoinCollected(int amount) => runCoins += amount;

    private void Commit()
    {
        if (committed) return;   // 결과 화면 이벤트가 두 번 와도 중복 지급 방지
        committed = true;

        if (SaveSystem.IsReadOnly)
        {
            // 저장할 수 없는 상태에서 메모리에만 쌓으면 "받은 줄 알았는데 사라진" 코인이 됨 → 지급하지 않음
            Debug.LogWarning($"세이브가 읽기 전용({SaveSystem.LoadStatus})이라 이번 판 보상을 기록하지 않습니다.");
            return;
        }

        SaveData save = SaveSystem.Load();
        save.coins += runCoins;
        save.bestSurvivalSeconds = Mathf.Max(save.bestSurvivalSeconds, runSeconds);
        if (!SaveSystem.Save(save))   // 재화 변화는 즉시 저장
            Debug.LogWarning("판 결과 저장에 실패했습니다. 백그라운드 진입·종료 시 다시 시도합니다.");
    }
}
```

**판 도중 종료 정책**: `runCoins`·`runSeconds`는 메모리에만 있고, `SaveLifecycle`은 `SaveData`만 저장합니다(판 도중에는 dirty도 아닙니다). 따라서 판 도중에 OS가 앱을 종료하면 **그 판의 코인은 지급되지 않습니다.** 코인 러시는 이것을 "판을 끝까지 마쳐야 보상이 확정된다"는 **의도된 규칙**으로 정합니다. 백그라운드 진입 때 중간 정산을 하면 "위험해지면 홈 버튼 → 앱 강제 종료"로 사망 없이 보상만 챙기는 우회가 생기고, 적 배치·체력·레벨까지 체크포인트로 복원하는 것은 이 규모의 게임에 과한 작업이기 때문입니다. 이 규칙은 타이틀의 도움말이나 결과 화면에 한 줄로 알리세요. 판 복원이 핵심인 장르(긴 로그라이크 등)라면 `SaveData`와 별도의 체크포인트 파일에 판 상태를 저장하고, 로드 시 "이어하기/포기"를 묻는 흐름을 따로 설계합니다.

**강화 상점**: Title 씬에 둡니다. UI는 11장에서 꾸미고, 지금은 버튼 하나와 텍스트 하나로 충분합니다.

```csharp
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// Assets/_CoinRush/Scripts/Save/UpgradeShop.cs
public class UpgradeShop : MonoBehaviour
{
    public const int MaxHpPerLevel = 10;

    [SerializeField] private TextMeshProUGUI label;
    [SerializeField] private Button buyButton;

    private void OnEnable() => Refresh();

    public static int CostForNextLevel(int currentLevel) => 50 * (currentLevel + 1);

    // 버튼 OnClick에 연결
    public void TryBuyMaxHp()
    {
        if (SaveSystem.IsReadOnly) { Refresh(); return; }   // 저장할 수 없으면 구매도 막음

        SaveData save = SaveSystem.Load();
        int level = save.maxHpLevel;
        int cost = CostForNextLevel(level);
        if (save.coins < cost) return;

        save.coins -= cost;
        save.maxHpLevel = level + 1;
        if (!SaveSystem.Save(save))
            Debug.LogWarning("구매는 반영됐지만 저장에 실패했습니다. 다음 저장 기회에 다시 시도합니다.");
        Refresh();
    }

    private void Refresh()
    {
        SaveData save = SaveSystem.Load();
        int level = save.maxHpLevel;
        string notice = SaveSystem.LoadStatus switch
        {
            SaveLoadStatus.FutureVersion => "\n<color=#FF6060>더 새 버전에서 만든 세이브입니다. 앱을 업데이트해 주세요. (진행이 저장되지 않음)</color>",
            SaveLoadStatus.AccessError   => "\n<color=#FF6060>세이브 파일에 접근할 수 없습니다. 게임을 다시 시작해 주세요. (진행이 저장되지 않음)</color>",
            _ => string.Empty,
        };
        label.text = $"코인 {save.coins}\n최대 체력 Lv.{level} (+{level * MaxHpPerLevel})  —  다음: {CostForNextLevel(level)} 코인{notice}";
        if (buyButton != null) buyButton.interactable = !SaveSystem.IsReadOnly;
    }
}
```

Title 씬 Canvas에 TMP 텍스트와 버튼을 만들고, 이 컴포넌트의 **Label**·**Buy Button**을 연결한 뒤 버튼 OnClick에 `TryBuyMaxHp`를 연결합니다. 읽기 전용 상태는 Console을 보지 않는 일반 유저에게도 이 문구와 비활성 버튼으로 드러납니다.

**플레이어에 적용**: 01장 `Health.Initialize(int)`는 최대 체력을 바꾸며 항상 가득 채웁니다. 채울지 고를 수 있도록 다음 메서드를 추가합니다(기존 코드는 그대로, `max`는 01장의 `[SerializeField] private int max` 필드). 이후 장은 최대 체력 변경에 이 `SetMax(int, bool)`을 씁니다.

```csharp
// Health.cs (01장)에 추가
public void SetMax(int newMax, bool refill)
{
    max = Mathf.Max(1, newMax);
    Current = refill ? max : Mathf.Min(Current, max);
    Changed?.Invoke(Current, Max);
}
```

```csharp
using UnityEngine;

// Assets/_CoinRush/Scripts/Save/ApplyPermanentUpgrades.cs — Player에 부착
[RequireComponent(typeof(Health))]
public class ApplyPermanentUpgrades : MonoBehaviour
{
    private void Start()
    {
        var health = GetComponent<Health>();
        SaveData save = SaveSystem.Load();
        health.SetMax(health.Max + save.maxHpLevel * UpgradeShop.MaxHpPerLevel, refill: true);
    }
}
```

### 5단계: 1.0 세이브 만들어 두기

1. Play → 게임을 한두 판 해서 코인을 모읍니다. 테스트가 귀찮으면 `RunRecorder.Commit`에 임시로 `runCoins += 500;`을 넣습니다.
2. 타이틀에서 강화를 두 번 삽니다.
3. Console에 `Debug.Log(Application.persistentDataPath)`를 찍어 폴더를 열고 `save.json`을 확인합니다.

```json
{
  "hash": "3b1e…",
  "payload": { "version": 1, "coins": 350, "maxHpLevel": 2, "bestSurvivalSeconds": 95.3 }
}
```

(실제 파일은 payload도 여러 줄로 들여쓰기되어 있습니다.)

4. **이 파일을 `save_v1_sample.json`으로 복사해 보관**합니다. 테스트와 6단계에서 씁니다. 한 번 더 저장하면 `save.backup.json`도 생깁니다.

### 6단계: 1.1 업데이트 — v2로 마이그레이션

기획 변경: 강화 종류가 늘어나 `maxHpLevel` 필드 하나로는 부족합니다. 강화 ID별 사전 `upgrades`와 통계 묶음 `stats`로 구조를 바꿉니다.

**SaveData를 v2로 교체**합니다.

```csharp
using System;
using System.Collections.Generic;

// Assets/_CoinRush/Scripts/Save/Core/SaveData.cs  — 1.1 버전
[Serializable]
public class SaveData
{
    public const int CurrentVersion = 2;

    public int version = CurrentVersion;
    public int coins;
    public Dictionary<string, int> upgrades = new();   // "maxHp" → 레벨
    public RunStats stats = new();

    public int GetUpgradeLevel(string id) => upgrades.TryGetValue(id, out int level) ? level : 0;

    // v1의 Normalize 교체: 새 묶음(upgrades, stats)이 null로 들어와도 복구
    public void Normalize()
    {
        if (coins < 0) coins = 0;
        upgrades ??= new();
        stats ??= new();
        foreach (string id in new List<string>(upgrades.Keys))   // 순회 중 값 변경을 피하려고 키 복사 (로드 때 한 번)
            if (upgrades[id] < 0) upgrades[id] = 0;
        if (float.IsNaN(stats.bestSurvivalSeconds) || stats.bestSurvivalSeconds < 0f) stats.bestSurvivalSeconds = 0f;
        if (stats.totalRuns < 0) stats.totalRuns = 0;
    }
}

[Serializable]
public class RunStats
{
    public float bestSurvivalSeconds;
    public int totalRuns;
}
```

**마이그레이션 함수를 추가**합니다. `SaveMigrator.cs`의 `Steps` 사전과 새 메서드만 바뀝니다.

```csharp
    private static readonly Dictionary<int, Action<JObject>> Steps = new()
    {
        { 1, V1ToV2 },
    };

    // 1.1 (v1 → v2): maxHpLevel → upgrades.maxHp, bestSurvivalSeconds → stats.bestSurvivalSeconds
    private static void V1ToV2(JObject root)
    {
        int maxHpLevel = root.Value<int?>("maxHpLevel") ?? 0;
        float best = root.Value<float?>("bestSurvivalSeconds") ?? 0f;
        root.Remove("maxHpLevel");
        root.Remove("bestSurvivalSeconds");

        root["upgrades"] = new JObject { ["maxHp"] = maxHpLevel };
        root["stats"] = new JObject
        {
            ["bestSurvivalSeconds"] = best,
            ["totalRuns"] = 0,   // v1은 기록하지 않았으므로 0에서 시작
        };
    }
```

**게임 코드의 바뀐 부분**만 고칩니다(컴파일 에러가 위치를 알려 줍니다).

```csharp
// UpgradeShop.cs — 상수 추가, TryBuyMaxHp와 Refresh의 레벨 읽기/쓰기 교체
public const string MaxHpId = "maxHp";

int level = save.GetUpgradeLevel(MaxHpId);          // 기존: save.maxHpLevel
save.upgrades[MaxHpId] = level + 1;                 // 기존: save.maxHpLevel = level + 1;

// RunRecorder.Commit — 통계 갱신 교체
save.stats.bestSurvivalSeconds = Mathf.Max(save.stats.bestSurvivalSeconds, runSeconds);
save.stats.totalRuns++;

// ApplyPermanentUpgrades.Start
health.SetMax(health.Max + save.GetUpgradeLevel(UpgradeShop.MaxHpId) * UpgradeShop.MaxHpPerLevel, refill: true);
```

이제 Play합니다. 디스크의 파일은 여전히 v1입니다. 로드 시 `V1ToV2`가 적용되어 코인·강화 레벨이 유지되고, 다음 저장부터 파일이 v2 형태로 바뀝니다.

### 7단계: EditMode 테스트

마이그레이션은 **출시 후에는 되돌릴 수 없는 코드**라서 테스트 가치가 가장 높습니다.

1. `Window > General > Test Runner` → `EditMode` 탭.
2. `Assets/_CoinRush/Tests/EditMode/`에서 `Create > Scripting > Assembly Definition`, 이름 `CoinRush.Tests.EditMode`. Inspector에서 설정하고 Apply합니다.
   - Assembly Definition References: `CoinRush.SaveCore`, `UnityEngine.TestRunner`, `UnityEditor.TestRunner`
   - Platforms: **Editor만** 체크 · Auto Referenced: 끔 · Define Constraints: `UNITY_INCLUDE_TESTS`
   - Override References: 켬 → Assembly References에 `nunit.framework.dll`, `Newtonsoft.Json.dll`

3. 같은 폴더에 테스트 스크립트를 만듭니다.

```csharp
using System;
using System.IO;
using Newtonsoft.Json.Linq;
using NUnit.Framework;

// Assets/_CoinRush/Tests/EditMode/SaveMigrationTests.cs
public class SaveMigrationTests
{
    // 5단계에서 보관한 1.0 세이브의 payload (해시는 테스트 대상 아님)
    private const string V1Payload = @"{ ""version"": 1, ""coins"": 350, ""maxHpLevel"": 2, ""bestSurvivalSeconds"": 95.3 }";

    [Test]
    public void V1_Migrates_To_Current_Keeping_Progress()
    {
        JObject root = JObject.Parse(V1Payload);

        SaveMigrator.MigrateToCurrent(root);
        SaveData data = root.ToObject<SaveData>();

        Assert.AreEqual(SaveData.CurrentVersion, data.version);
        Assert.AreEqual(350, data.coins);
        Assert.AreEqual(2, data.GetUpgradeLevel("maxHp"));
        Assert.AreEqual(95.3f, data.stats.bestSurvivalSeconds, 0.001f);
        Assert.AreEqual(0, data.stats.totalRuns);
        Assert.IsNull(root["maxHpLevel"], "옛 필드가 남아 있으면 안 됩니다.");
    }

    [Test]
    public void RoundTrip_And_Tamper_Detection()
    {
        var original = new SaveData { coins = 42 };
        original.upgrades["maxHp"] = 3;

        string json = SaveSerializer.Serialize(original);
        SaveData loaded = SaveSerializer.Deserialize(json, out SaveReadStatus status);
        Assert.AreEqual(SaveReadStatus.Ok, status);
        Assert.AreEqual(3, loaded.GetUpgradeLevel("maxHp"));

        string tampered = json.Replace("\"coins\": 42", "\"coins\": 99999");
        SaveSerializer.Deserialize(tampered, out status);
        Assert.AreEqual(SaveReadStatus.HashMismatch, status);
    }

    [Test]
    public void Null_Sections_Are_Normalized()
    {
        const string json = @"{ ""hash"": ""x"", ""payload"": { ""version"": 2, ""coins"": -5, ""upgrades"": null, ""stats"": null } }";

        SaveData loaded = SaveSerializer.Deserialize(json, out SaveReadStatus status);

        Assert.AreEqual(SaveReadStatus.HashMismatch, status);
        Assert.AreEqual(0, loaded.coins);
        Assert.IsNotNull(loaded.upgrades);
        Assert.IsNotNull(loaded.stats);
    }

    [Test]
    public void Corrupt_Main_Is_Quarantined_And_Good_Backup_Survives()
    {
        string dir = Path.Combine(Path.GetTempPath(), "coinrush-save-test-" + Guid.NewGuid().ToString("N"));
        try
        {
            var store = new SaveFileStore(dir);
            File.WriteAllText(store.MainPath, "{ \"hash\": \"x\", \"payl");     // 잘린 본 파일
            const string goodBackup = "GOOD-BACKUP";
            File.WriteAllText(store.BackupPath, goodBackup);

            // SaveSystem이 "본 파일 손상 → 백업 복구" 후 첫 저장에서 하는 순서
            store.QuarantineMain();
            store.WriteAtomic("NEW-MAIN");

            Assert.AreEqual("NEW-MAIN", File.ReadAllText(store.MainPath));
            Assert.AreEqual(goodBackup, File.ReadAllText(store.BackupPath), "정상 백업이 손상본으로 덮이면 안 됩니다.");
            Assert.IsTrue(File.Exists(store.CorruptPath));
        }
        finally
        {
            if (Directory.Exists(dir)) Directory.Delete(dir, recursive: true);
        }
    }
}
```

4. Test Runner에서 `Run All` → 네 개가 모두 초록색이면 성공입니다. 변조 테스트의 문자열 치환은 `Serialize`의 들여쓰기 출력 형식(`"coins": 42`)에 의존합니다.

### 확인하기

- 판을 끝내면 코인이 늘고, 타이틀에서 강화하면 게임 시작 시 최대 체력이 레벨만큼 늘어 있으며, Play를 껐다 켜도 유지된다.
- v1 시절 파일(`save_v1_sample.json`을 `save.json`으로 덮어쓰기)로 시작해도 코인 350, 체력 강화 Lv.2가 그대로 보인다. 한 번 저장한 뒤 파일을 열면 `"version": 2`와 `upgrades`, `stats`가 보인다.
- `save.json` 중간을 지워 JSON을 망가뜨리고 Play하면, 경고 로그와 함께 백업에서 복구된다. 이어서 강화를 한 번 사면 손상본은 `save.corrupt.json`으로 옮겨지고, `save.backup.json`은 **복구에 쓴 정상 내용 그대로** 남아 있다. 둘 다 망가뜨리면 새 데이터로 시작한다.
- `save.json`의 payload에서 `"stats": null`로 고쳐도 경고만 뜨고 정상 시작한다(정규화).
- `"version": 99`로 고치고 Play하면 에러 로그가 뜨고, 타이틀의 상점 문구에 "앱을 업데이트해 주세요"가 표시되며 구매 버튼이 비활성화된다. 한 판을 끝내도 파일이 덮어써지지 않는다.
- (실기기) Android/iOS에서 판 도중 홈으로 나가 앱을 강제 종료한 뒤 다시 실행하면, 직전에 **끝낸** 판까지의 코인은 남아 있고 중단한 판의 코인은 없다(판 도중 종료 정책).
- Test Runner의 EditMode 테스트 4개가 통과한다.

## 흔한 실수

1. **업데이트 후 기존 유저의 진행이 초기화된다** → 구조를 바꾸면서 `version`을 올리지 않았거나 마이그레이션 없이 새 클래스로 바로 역직렬화 → 구조 변경마다 `CurrentVersion`을 올리고 `JObject` 변환 함수를 추가, 옛 세이브 샘플로 테스트합니다.
2. **Dictionary나 프로퍼티가 저장되지 않는다(에러 없음)** → `JsonUtility` 사용 → Newtonsoft로 바꾸거나 `JsonUtility`용으로 리스트·public 필드 구조로 바꿉니다.
3. **로드할 때마다 리스트 항목이 두 배로 늘어난다** → Newtonsoft 기본 `ObjectCreationHandling.Reuse`가 필드 초기값 리스트에 항목을 덧붙임 → `ObjectCreationHandling.Replace`로 설정합니다.
4. **모바일에서 마지막 진행이 사라진다** → `OnApplicationQuit`에서만 저장 → 중요한 변화 직후 즉시 저장하고, `OnApplicationPause(true)`에서 dirty 저장을 추가합니다.
5. **테스트 어셈블리에서 `SaveData`를 찾을 수 없다** → 저장 코드가 `Assembly-CSharp`에 있어 테스트가 참조 불가 → 순수 로직을 asmdef로 분리하고 테스트 asmdef의 references에 추가합니다. `overrideReferences`를 켰다면 `Newtonsoft.Json.dll`도 precompiled references에 넣습니다.

## 연습 문제

**1. ★☆☆ 설정 화면용 데이터 분리 판단**
다음 값들을 `PlayerPrefs`와 세이브 파일 중 어디에 둘지 분류하고 이유를 쓰세요: BGM 볼륨, 해금한 캐릭터 목록, 마지막으로 선택한 캐릭터, 광고 제거 구매 여부, 그래픽 품질, 튜토리얼 완료 여부.

<details>
<summary>힌트·해설</summary>

기준은 "기기에 종속된 설정인가, 진행 데이터인가(다른 기기로 따라가야 하는가)"입니다. 그래픽 품질·키 설정은 `PlayerPrefs`, 해금 캐릭터·튜토리얼 완료·마지막 선택 캐릭터는 세이브 파일입니다. BGM 볼륨은 둘 다 가능하며(12장은 세이브 파일), 기기마다 달라야 한다면 `PlayerPrefs`가 낫습니다.
- 광고 제거 구매: 로컬에는 **캐시**로만 저장하고, 진실의 원천은 스토어 구매 복원(25장)입니다. 세이브를 지워도 구매는 복원되어야 합니다.

</details>

**2. ★★☆ v2 → v3 마이그레이션**
1.2 업데이트에서 캐릭터 해금을 추가합니다. `unlockedCharacters: List<string>`(기본값 `["knight"]`)과 `settings: { bgmVolume, sfxVolume }`(기본 0.8)을 추가하고, 12장에서 루트에 넣었던 `bgmVolume`/`sfxVolume`이 있다면 `settings` 아래로 옮기는 `V2ToV3`를 작성하세요(12장에서 이미 버전을 올렸다면 번호를 하나씩 늘려 적용). 테스트도 추가합니다.

<details>
<summary>힌트·해설</summary>

```csharp
private static void V2ToV3(JObject root)
{
    float bgm = root.Value<float?>("bgmVolume") ?? 0.8f;
    float sfx = root.Value<float?>("sfxVolume") ?? 0.8f;
    root.Remove("bgmVolume");
    root.Remove("sfxVolume");
    root["settings"] = new JObject { ["bgmVolume"] = bgm, ["sfxVolume"] = sfx };
    root["unlockedCharacters"] ??= new JArray("knight");
}
```

`Steps`에 `{ 2, V2ToV3 }`를 추가하고 `CurrentVersion = 3`. 테스트는 **v1 샘플과 v2 샘플 둘 다** 넣어 체인 전체(v1→v2→v3)가 동작하는지 확인합니다. 클래스의 `unlockedCharacters = new() { "knight" }` 초기값은 `ObjectCreationHandling.Replace` 덕분에 로드 시 중복되지 않습니다.

</details>

**3. ★★★ 클라우드 충돌 해결 (확장 과제)**
`SaveData`에 `savedAtUtcTicks`와 `totalPlaySeconds`를 추가하고(마이그레이션 포함), 로컬 세이브와 "클라우드 세이브"(임시로 다른 폴더의 파일) 두 개를 비교해 병합하는 `SaveConflictResolver`를 설계·구현하세요. 자동으로 고를 수 없는 경우 유저에게 두 세이브의 요약(코인, 강화, 플레이 시간, 저장 시각)을 보여주고 선택받는 흐름까지 만드세요.

<details>
<summary>힌트·해설</summary>

- 자동 규칙 예: 한쪽의 `totalPlaySeconds`가 다른 쪽보다 크고 `savedAtUtcTicks`도 더 최신이면 그쪽을 선택. 두 기준이 엇갈리면(A는 최신, B는 플레이 시간이 김) 유저에게 묻습니다.
- 재화를 "더하기"로 병합하면 무한 복제 버그가 생깁니다. 병합은 "해금 목록의 합집합"처럼 **되돌려도 손해가 없는 데이터**에만 적용합니다.
- 순수 로직(`Resolve(local, cloud) → Decision`)은 `CoinRush.SaveCore`에 두고 EditMode 테스트로 모든 분기를 검증하세요. UI는 11장의 팝업 구조를 재사용합니다.

</details>

## 셀프 체크

**1. `version` 필드와 마이그레이션 체인이 없으면 출시 후 어떤 문제가 생기는지, 체인 방식의 장점과 함께 설명해 보세요.**

<details>
<summary>모범 답안</summary>

업데이트로 저장 구조가 바뀌면 기존 파일을 새 클래스로 읽을 때 옮겨진·이름이 바뀐 필드가 기본값으로 채워져 유저 진행이 사라집니다. 버전 필드가 있으면 파일이 어떤 구조인지 확실히 알 수 있고, "직전 버전 → 다음 버전" 함수만 추가해 차례로 적용하면 어떤 옛 버전에서 와도 현재 구조에 도달합니다. 버전마다 함수 하나만 늘어나므로 조합 폭발이 없고, 각 단계를 독립적으로 테스트할 수 있습니다.

</details>

**2. `File.WriteAllText`로 바로 저장하는 것이 위험한 이유와 원자적 저장의 절차를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

`WriteAllText`는 기존 파일을 비우고 쓰기 시작하므로, 쓰는 도중 앱 종료·전원 차단이 일어나면 빈 파일이나 잘린 JSON만 남아 이전 데이터까지 잃습니다. 원자적 저장은 임시 파일에 전체를 쓰고 디스크까지 플러시한 뒤, `File.Replace`로 본 파일과 교체하면서 이전 본 파일을 백업으로 남깁니다. 어느 시점에 죽어도 온전한 본 파일이나 백업 중 하나가 남습니다. 단 이 보장은 교체 직전의 본 파일이 정상일 때 성립하므로, 본 파일이 손상되어 백업으로 복구했다면 다음 저장 전에 손상본을 격리해 정상 백업이 덮이지 않게 합니다.

</details>

**3. 싱글 게임에서 세이브 해시를 "보안"이 아니라 "손상 감지" 용도로 보는 이유를 설명해 보세요.**

<details>
<summary>모범 답안</summary>

해시 계산 코드와 솔트는 게임 바이너리에 들어 있어 디컴파일하면 누구나 재계산할 수 있으므로, 결심한 사용자를 막을 수 없습니다. 반면 파일 일부가 깨진 경우는 확실히 잡아내 백업으로 복구하는 데 유용합니다. 싱글 게임에서 세이브를 고친 사용자는 자기 경험만 바꾸므로 강한 보호에 시간을 쓰는 것보다 콘텐츠에 투자하는 편이 낫고, 재화가 실제 돈이나 다른 유저와 연결될 때에만 서버 검증이 필요합니다.

</details>

**4. 모바일에서 `OnApplicationQuit`에만 저장을 맡기면 안 되는 이유와 대안을 설명해 보세요.**

<details>
<summary>모범 답안</summary>

모바일 앱은 대개 "종료"되지 않고 백그라운드로 간 뒤 OS가 메모리 확보를 위해 예고 없이 프로세스를 종료하므로 `OnApplicationQuit`이 호출되지 않는 경우가 많습니다. 재화 획득·구매·강화처럼 중요한 변화 직후에 바로 저장하고, 백그라운드 진입 시 호출되는 `OnApplicationPause(true)`에서 변경분(dirty)을 저장하는 것이 대안입니다.

</details>

## 핵심 요약

- `PlayerPrefs`는 기기별 설정에, 게임 진행은 `persistentDataPath` 아래 JSON 파일에 저장합니다.
- `JsonUtility`는 Dictionary·프로퍼티를 조용히 무시합니다. 마이그레이션이 필요한 세이브는 Newtonsoft(`JObject`)가 유리하고, `ObjectCreationHandling.Replace`를 설정합니다.
- `SaveData`는 첫날부터 `version` 필드를 갖고, 에셋 참조 대신 문자열 ID를 저장하는 순수 데이터 클래스로 둡니다.
- 마이그레이션은 "vN → vN+1" 함수를 `JObject` 위에서 차례로 적용하며, 출시한 함수는 수정하지 않고, 미래 버전 파일은 덮어쓰지 않습니다.
- 저장은 임시 파일 → 플러시 → `File.Replace`(이전 파일은 백업), 로드는 본 파일 → 백업 → 새 데이터 순서입니다. 손상된 본 파일은 격리해 정상 백업을 지키고, 미래 버전·접근 실패는 읽기 전용으로 두고 UI에 알립니다.
- 저장 실패는 dirty를 남겨 재시도하고 호출자에게 `false`로 알립니다. 로드한 데이터는 구조를 검증·정규화한 뒤 씁니다.
- 해시는 손상 감지용입니다. 싱글 게임의 치팅 방지에 과투자하지 않습니다.
- 중요한 변화 직후 즉시 저장하고, 모바일은 `OnApplicationPause(true)`에서 dirty를 저장합니다.
- 마이그레이션·직렬화·파일 저장은 asmdef로 분리해 EditMode 테스트로 고정합니다.

## 더 읽을거리

- Unity 스크립팅 API — `Application.persistentDataPath`: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Unity 매뉴얼 — JSON Serialization (`JsonUtility`의 지원 범위): https://docs.unity3d.com/Manual/JSONSerialization.html
- Newtonsoft Json.NET 공식 문서 (LINQ to JSON, `JObject`): https://www.newtonsoft.com/json/help/html/LINQtoJSON.htm
- Unity Test Framework 패키지 매뉴얼: https://docs.unity3d.com/Packages/com.unity.test-framework@latest
- Steamworks 문서 — Steam Cloud: https://partner.steamgames.com/doc/features/cloud
