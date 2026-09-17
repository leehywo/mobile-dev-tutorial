# 14. Shader Graph — 노드로 만드는 효과

> **이 장에서 배울 것**
> - 정점 셰이더와 프래그먼트 셰이더가 하는 일을 GPU 파이프라인 흐름으로 설명할 수 있다
> - Sprite Lit/Unlit Shader Graph를 만들고 Blackboard 속성·Master Stack·필수 노드로 효과를 조립한다
> - `material` 인스턴스와 `MaterialPropertyBlock`의 차이를 이해하고, `Shader.PropertyToID`로 C#에서 속성을 제어한다
> - 피격 번쩍임, 디졸브 사망, UV 스크롤 배경, 외곽선 네 가지 효과를 구현하고 Sub Graph로 재사용한다
>
> **선수 장**: 07, 12, 13 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 적이 맞으면 하얗게 번쩍이고, 죽으면 불타듯 사라지며, 배경이 흐르고, 보물 상자에 외곽선이 생깁니다

## 왜 필요한가

지금까지 적이 맞았을 때의 시각 피드백은 `spriteRenderer.color = Color.red`처럼 색을 바꾸는 정도였습니다. 여기에는 근본적인 한계가 있습니다.

```
최종 색 = 텍스처 색 × SpriteRenderer.color

텍스처 (0.4, 0.3, 0.2) × 흰색 (1, 1, 1) = (0.4, 0.3, 0.2)   원래 색
텍스처 (0.4, 0.3, 0.2) × 빨강 (1, 0, 0) = (0.4, 0.0, 0.0)   어두운 빨강
→ 곱셈으로는 원래보다 밝게 만들 수 없음. "하얗게 번쩍"은 불가능
```

죽을 때는 12장 풀로 한 프레임에 사라지고, 배경은 정지해 있습니다. 액션 게임에서 흔히 보는 "번쩍 → 불타 사라짐 → 흐르는 배경" 같은 연출은 **픽셀마다 색을 계산하는 규칙**, 즉 셰이더를 바꿔야 가능합니다. 이 장에서는 코드를 쓰지 않고 노드를 연결하는 **Shader Graph**로 네 가지 효과를 만들고, 15장에서 같은 효과를 HLSL 코드로 다시 씁니다.

## 개념

### 셰이더가 하는 일 — 정점과 프래그먼트

```
[CPU] SpriteRenderer: 사각형(또는 Tight 메시) 정점 + 텍스처 + 머티리얼
   │  드로우 콜
   ▼
[GPU]
 1. 정점 셰이더 (Vertex)      정점마다 1회   오브젝트 좌표 → 화면(클립) 좌표 변환
                                              UV, 정점 색을 다음 단계로 전달
                                              (흔들림·물결처럼 모양을 바꾸는 효과는 여기서)
 2. 래스터화                  GPU 고정 단계  삼각형이 덮는 픽셀 결정, 정점 값을 픽셀별로 보간
 3. 프래그먼트 셰이더 (Pixel) 픽셀마다 1회   최종 색(RGBA) 계산
                                              (번쩍임·디졸브·외곽선·색 변환은 여기서)
 4. 블렌딩                    GPU 설정       투명도로 기존 화면 색과 섞기
```

화면 1920×1080이면 프래그먼트 셰이더는 한 프레임에 수백만 번 실행됩니다. GPU는 이것을 **병렬로** 처리하므로, 셰이더는 "한 픽셀의 입력만 보고 그 픽셀의 색을 돌려주는 순수 함수"로 생각하면 됩니다. JS로 치면 `pixels.map(p => color(p))`를 수천 코어가 동시에 돌리는 것입니다. 이웃 픽셀의 **계산 결과**는 볼 수 없지만, 텍스처는 원하는 좌표를 몇 번이고 읽을 수 있습니다(외곽선의 원리).

### Shader Graph 기본 구조

**Create → Shader Graph → URP → Sprite Lit Shader Graph**(또는 Sprite Unlit)로 만듭니다. 더블클릭하면 에디터가 열립니다.

```
┌ Blackboard ─────────┐   ┌ 작업 영역 ────────────────────────┐   ┌ Graph Inspector ┐
│ 속성(Properties)     │   │  노드들 ──연결──▶ Master Stack     │   │ Graph Settings  │
│  _MainTex (Texture)  │   │                  ┌ Vertex ──────┐ │   │  Material:      │
│  _FlashAmount (Float)│   │                  │ Position ... │ │   │  Sprite Lit     │
│  _FlashColor (Color) │   │                  ├ Fragment ────┤ │   │ Node Settings   │
│ 키워드(Keywords)     │   │                  │ Base Color   │ │   │  (선택한 속성의 │
└──────────────────────┘   │                  │ Alpha        │ │   │   Reference 등) │
                           │                  │ (Lit) Normal │ │   └─────────────────┘
                           │                  └──────────────┘ │
                           └───────────────────────────────────┘
```

- **Master Stack**: 셰이더의 출력 슬롯입니다. Vertex 블록은 정점 위치 등, Fragment 블록은 Base Color·Alpha 등을 받습니다. Sprite Lit에는 2D 조명용 Normal (Tangent Space)·Sprite Mask 슬롯이 더 있습니다.
- **Graph Settings의 Material**: `Sprite Lit`(13장 2D 조명 받음), `Sprite Unlit`(조명 무시), `Sprite Custom Lit`(조명 계산을 직접)을 여기서 바꿀 수 있습니다.
- **Blackboard 속성**: `+`로 추가합니다. 머티리얼 Inspector에 노출되고 C#에서 이름으로 바꿀 수 있는 값입니다. 선택 후 Node Settings에서 **Reference**(코드에서 쓰는 이름, 관례상 `_`로 시작)를 확인합니다. Display Name과 Reference는 다릅니다.
- **`_MainTex`**: SpriteRenderer는 스프라이트 텍스처를 **`_MainTex`라는 이름의 속성**에 넣어줍니다. 그래서 텍스처 속성의 Reference를 반드시 `_MainTex`로 둡니다.
- 수정 후 왼쪽 위 **Save Asset**을 눌러야 반영됩니다.

**정점 색(SpriteRenderer.Color) 확인**: Sprite 타깃이 SpriteRenderer의 Color를 자동으로 곱하는지는 URP 버전에 따라 동작이 달랐습니다. 그래프를 만든 뒤 SpriteRenderer의 Color를 빨강으로 바꿔보고, 반영되지 않으면 **Vertex Color** 노드를 텍스처 색에 곱하고, 두 번 곱해져 너무 어두워지면 그 노드를 빼세요.

### 필수 노드

| 노드 | 입력 → 출력 | 쓰임 |
|---|---|---|
| Sample Texture 2D | Texture, UV → RGBA(4), R, G, B, A | 텍스처 읽기. UV를 비우면 기본 UV0 |
| UV | → (u, v, 0, 0) | 스프라이트 위 위치(0~1). **아틀라스에선 아틀라스 전체 기준** |
| Time | → Time, Sine Time, Cosine Time, Delta Time | 시간에 따라 변하는 효과 |
| Lerp | A, B, T → A + (B−A)·T | 두 색 섞기 (T=0이면 A, 1이면 B) |
| Step | Edge, In → In ≥ Edge ? 1 : 0 | 딱 자르는 경계 (디졸브) |
| Smoothstep | Edge1, Edge2, In → 두 경계 사이 부드러운 0→1 | 부드러운 경계 |
| Simple Noise / Gradient Noise | UV, Scale → 0~1 값 | 불규칙 패턴 (디졸브, 일렁임) |
| Tiling And Offset | UV, Tiling, Offset → UV·Tiling + Offset | 반복·스크롤 |
| Texel Size | Texture → Width, Height (픽셀 수) | 한 픽셀만큼 옆 좌표 계산 (외곽선) |
| Split / Combine | 벡터 ↔ 채널 | RGBA 분리·조립 |
| Add, Subtract, Multiply, Divide, Maximum, One Minus, Saturate | 산술 | 마스크 조합. Saturate = 0~1로 자르기 |
| Fresnel Effect | Normal, View Dir, Power → 가장자리 밝기 | 3D 림라이트용. 2D 스프라이트에는 법선이 없어 거의 안 씀 |

노드 추가는 작업 영역에서 **Space** 또는 우클릭 → Create Node 후 이름 검색입니다. 포트 사이를 드래그해 연결하고, 노드 미리보기 창으로 중간 결과를 바로 볼 수 있습니다.

### C#에서 속성 제어 — material, sharedMaterial, MaterialPropertyBlock

| 방법 | 동작 | 장점 | 문제 |
|---|---|---|---|
| `renderer.sharedMaterial.SetFloat` | 머티리얼 **에셋** 자체 수정 | 할당 없음 | 같은 머티리얼 쓰는 **모든 적**이 번쩍임. 에디터에서는 에셋 파일에 저장됨 |
| `renderer.material.SetFloat` | **처음 접근할 때 한 번** 머티리얼을 복제해 이 렌더러 전용으로 만들고, 이후 접근은 그 복제본을 돌려줌 | 개별 제어 | 적 500마리 = 첫 접근 때 머티리얼 500개 생성(메모리·할당). 복제본은 오브젝트를 `Destroy`해도 자동 해제되지 않아 직접 `Destroy`해야 함, 배칭 불가 |
| `MaterialPropertyBlock` | 머티리얼은 공유한 채 **이 렌더러의 값만 덮어씀** | 머티리얼 복제 없음 | 값이 다른 렌더러끼리는 배칭이 끊길 수 있음 |

SpriteRenderer에서는 **MaterialPropertyBlock(MPB)** 이 기본 선택입니다. 사용 규칙은 세 가지입니다.

```csharp
static readonly int FlashAmountId = Shader.PropertyToID("_FlashAmount");  // 1) 문자열 → 정수 ID 캐싱
MaterialPropertyBlock block = new MaterialPropertyBlock();                  //    블록도 한 번만 생성

spriteRenderer.GetPropertyBlock(block);      // 2) 먼저 현재 블록을 읽어옴 (다른 컴포넌트가 넣은 값 보존)
block.SetFloat(FlashAmountId, 0.8f);
spriteRenderer.SetPropertyBlock(block);      // 3) 다시 설정
```

- `SetFloat("_FlashAmount", ...)`처럼 문자열을 쓰면 호출마다 이름을 해시합니다. `static readonly int`로 캐싱하세요.
- 한 렌더러에 블록은 하나입니다. 피격 번쩍임과 디졸브를 서로 다른 컴포넌트가 설정한다면, **Get 없이 Set만 하면 상대의 값을 지워버립니다.**
- 배칭 트레이드오프: 번쩍이는 순간의 적 몇 마리만 배칭에서 빠지고, 값이 0으로 돌아오면 다시 같은 조건이 됩니다. 500마리 전부가 계속 다른 값을 갖는 효과라면 13장의 Frame Debugger로 비용을 확인하세요.

### Sub Graph — 노드 묶음 재사용

같은 노드 조합(예: 외곽선 계산)을 여러 그래프에서 쓰려면 **Sub Graph**로 만듭니다. 노드들을 드래그로 선택하고 우클릭 → **Convert To → Sub-graph**를 누르면, 선택 영역으로 들어오는 연결은 입력 포트로, 나가는 연결은 출력 포트로 바뀐 `.shadersubgraph` 에셋이 생깁니다. Create → Shader Graph → Sub Graph로 처음부터 만들 수도 있습니다. React의 컴포넌트 추출과 같은 발상입니다. Sub Graph를 수정하면 그것을 쓰는 모든 그래프에 반영됩니다.

### 아틀라스와 UV 주의

13장에서 적 스프라이트를 아틀라스에 넣었습니다. 아틀라스 안의 스프라이트는 UV가 0~1 전체가 아니라 **아틀라스 속 자기 영역**(예: u 0.25~0.31)입니다.

- **번쩍임·외곽선**: 텍스처 색만 쓰므로 영향 없음(외곽선은 아틀라스 Padding이 두께보다 커야 이웃 스프라이트를 읽지 않음).
- **디졸브 노이즈**: 스프라이트마다 노이즈 패턴 위치·크기가 달라지지만 무작위 패턴이라 보통 티가 나지 않습니다. 균일해야 하면 Scale을 조절합니다.
- **UV 스크롤·반복**: 아틀라스에 넣으면 이웃 스프라이트가 흘러들어옵니다. **아틀라스에서 제외**하고 텍스처 Wrap Mode를 Repeat로 둡니다.
- **외곽선**: Sprite Import의 **Mesh Type을 Full Rect**로 두어야 스프라이트 바깥 투명 영역까지 사각형이 그려집니다. Tight면 모양대로 메시가 잘려 외곽선을 그릴 픽셀이 없습니다.

## 실습: 코인 러시에 적용하기

앞 장의 최소 시그니처: `Health`(01) — `int Current`, `event Action<int,int> Changed`, `event Action Died`. `Enemy`(12장 풀링 버전) — `IObjectPool<Enemy> Pool`, `OnDied()`에서 드롭 후 `Pool.Release(this)`, 필드 `health`·`body`·`aliveEnemies`·`pools`·`loot`·`isSpawned`. `EnemyMotor2D`(07장) — 적 이동 담당.

그래프는 `Assets/_CoinRush/Shaders/`, 스크립트는 `Assets/_CoinRush/Scripts/Rendering/`에 둡니다.

### 1단계 — 효과 1: 피격 흰색 번쩍임

1. `Shaders` 폴더 우클릭 → Create → Shader Graph → URP → **Sprite Lit Shader Graph**, 이름 `SG_Enemy`.
2. Blackboard `+` → **Texture2D**, 이름 `MainTex`, Node Settings에서 Reference를 **`_MainTex`** 로.
3. `+` → **Color**, 이름 `FlashColor`, Reference `_FlashColor`, 기본값 흰색.
4. `+` → **Float**, 이름 `FlashAmount`, Reference `_FlashAmount`, Mode **Slider** 0~1, 기본값 0.
5. 노드 연결:

```
[MainTex 속성] ──▶ Sample Texture 2D.Texture
Sample Texture 2D.RGBA ───────────────▶ Lerp.A
[FlashColor 속성] ────────────────────▶ Lerp.B
[FlashAmount 속성] ───────────────────▶ Lerp.T
Lerp.Out ─────────────────────────────▶ Fragment.Base Color   (4채널 → 3채널 자동 절단)
Sample Texture 2D.A ──────────────────▶ Fragment.Alpha
```

6. Save Asset. `SG_Enemy`를 우클릭 → Create → Material로 `M_Enemy` 생성.

> **Sprite Lit의 Base Color는 조명 전 색입니다.** 2D Renderer는 Base Color에 13장의 2D 조명을 곱합니다. 그래서 `Lerp`로 만든 흰색도 13장의 어두운 남색 Global Light(0.35) 아래에서는 "어둡고 푸른 밝은 색"으로 보이고, 플레이어 주변 Spot Light 안에서만 흰색에 가깝게 보입니다. 이 그래프의 번쩍임은 "조명 아래에서 원래보다 밝아짐"이고, **조명과 무관한 순백**이 필요하면 2단계 끝의 번쩍임 오버레이(Sprite **Unlit** 보조 렌더러)를 함께 씁니다. `_FlashAmount`/`_FlashColor` 속성은 그대로 두므로 15·16장 코드와의 계약은 바뀌지 않습니다.
7. 적 프리팹의 SpriteRenderer → Material에 `M_Enemy` 지정.
8. Play 중 `M_Enemy`의 Flash Amount 슬라이더를 움직여 모든 적이 밝아지는지 확인한 뒤 0으로 되돌립니다(에셋 값이므로 모두 바뀌는 것이 정상). 플레이어 주변 조명 안과 밖에서 밝기가 다르게 보이는 것도 확인합니다.
9. 개념 절의 **정점 색 확인**을 수행합니다.

### 2단계 — HitFlash 컴포넌트

```csharp
// Assets/_CoinRush/Scripts/Rendering/HitFlash.cs
using UnityEngine;

[RequireComponent(typeof(SpriteRenderer))]
public class HitFlash : MonoBehaviour
{
    private static readonly int FlashAmountId = Shader.PropertyToID("_FlashAmount");
    private static readonly int FlashColorId = Shader.PropertyToID("_FlashColor");

    [SerializeField] private Health health;
    [SerializeField] private Color flashColor = Color.white;
    [SerializeField] private float duration = 0.12f;
    [Tooltip("선택: 조명과 무관한 순백을 겹쳐 그릴 자식 SpriteRenderer (M_FlashOverlay). 비워 두면 사용 안 함")]
    [SerializeField] private SpriteRenderer overlay;

    private SpriteRenderer spriteRenderer;
    private MaterialPropertyBlock block;
    private float timer;
    private int lastHp;

    private void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        block = new MaterialPropertyBlock();
        if (health == null) health = GetComponentInParent<Health>();
        if (overlay != null) overlay.enabled = false;   // 평소에는 그리지 않음 (드로우 콜·overdraw 0)
    }

    private void OnEnable()
    {
        // 12장 풀링 규칙: 재사용될 때 지난 생의 번쩍임이 남지 않게 리셋
        timer = 0f;
        lastHp = health.Current;
        Apply(0f);
        health.Changed += OnHealthChanged;
    }

    private void OnDisable() => health.Changed -= OnHealthChanged;

    private void OnHealthChanged(int current, int max)
    {
        if (current < lastHp) Flash();
        lastHp = current;                 // 풀에서 Initialize로 올라간 경우도 갱신만
    }

    public void Flash() => timer = duration;

    private void Update()
    {
        if (timer <= 0f) return;
        // 16장 히트 스톱(timeScale 저하) 중에도 번쩍임은 보여야 하므로 unscaled
        timer = Mathf.Max(0f, timer - Time.unscaledDeltaTime);
        Apply(timer / duration);          // 1 → 0 으로 빠짐
    }

    private void Apply(float amount)
    {
        SetFlash(spriteRenderer, amount);

        if (overlay == null) return;
        bool on = amount > 0f;
        overlay.enabled = on;                     // 번쩍이는 동안만 그림
        if (!on) return;
        overlay.sprite = spriteRenderer.sprite;   // 애니메이션·좌우 반전을 따라감
        overlay.flipX = spriteRenderer.flipX;
        overlay.flipY = spriteRenderer.flipY;
        SetFlash(overlay, amount);
    }

    private void SetFlash(SpriteRenderer target, float amount)
    {
        target.GetPropertyBlock(block);           // 디졸브 등 다른 값 보존
        block.SetFloat(FlashAmountId, amount);
        block.SetColor(FlashColorId, flashColor);
        target.SetPropertyBlock(block);
    }
}
```

적 프리팹의 스프라이트 오브젝트에 붙입니다. `Update`는 번쩍이는 동안만 일을 하므로 500마리에서도 대부분 즉시 반환됩니다.

> `enabled = false`로 꺼서 `Update`까지 없애는 최적화는 **하지 마세요.** 이 컴포넌트는 `OnDisable`에서 `Changed` 구독을 해제하므로 꺼진 동안의 피격을 감지하지 못하고, 다시 켜면 `OnEnable`이 타이머를 0으로 리셋합니다. `Update` 비용이 정말 문제로 측정되면(18장) "항상 구독하는 감지 컴포넌트"와 "필요할 때만 켜지는 연출 컴포넌트"로 나눕니다.

**선택: 조명과 무관한 순백 오버레이.** 1단계의 주의대로 Sprite Lit 그래프의 번쩍임은 조명에 곱해집니다. 어두운 곳에서도 확실한 흰색이 필요하면 조명을 받지 않는 보조 렌더러를 겹칩니다.

1. Create → Shader Graph → URP → **Sprite Unlit Shader Graph**, `SG_FlashOverlay`. 속성 `MainTex`(Reference `_MainTex`), `FlashColor`(`_FlashColor`, 흰색), `FlashAmount`(`_FlashAmount`, Slider 0~1, 기본 0).
2. 연결: `[FlashColor] → Fragment.Base Color`, `Multiply(A=Sample Texture 2D([MainTex]).A, B=[FlashAmount]) → Fragment.Alpha`. Save Asset → 머티리얼 `M_FlashOverlay`.
3. 적 프리팹의 스프라이트 오브젝트 아래에 자식 `FlashOverlay`(Position 0, Scale 1) + SpriteRenderer: Sprite는 본체와 같게, Material `M_FlashOverlay`, Sorting Layer는 본체와 같은 `Enemies`, **Order in Layer 1**(본체보다 한 칸 위).
4. `HitFlash`의 Overlay 슬롯에 `FlashOverlay`를 드래그합니다. 평소에는 꺼져 있어 13장의 배칭에 영향이 없고, 번쩍이는 0.12초 동안만 그려집니다.

### 3단계 — 효과 2: 디졸브 사망

`SG_Enemy`에 이어서 만듭니다. 한 SpriteRenderer에는 셰이더가 하나이므로 번쩍임과 디졸브를 같은 그래프에 넣습니다.

1. Blackboard에 속성 추가:
   - `Dissolve` (Float, Slider 0~1, Reference `_Dissolve`, 기본 0)
   - `EdgeWidth` (Float, Reference `_EdgeWidth`, 기본 0.08)
   - `EdgeColor` (Color, Reference `_EdgeColor`, Node Settings에서 **Mode: HDR**, 색 주황, Intensity 약 3)
   - `NoiseScale` (Float, Reference `_NoiseScale`, 기본 40)
2. 경계선 계산. 핵심 아이디어는 "노이즈 값이 불타는 선(burn)보다 작으면 사라짐, burn 바로 아래 폭 EdgeWidth 구간은 빛남"입니다. Dissolve 0에서 가장자리가 보이지 않고 1에서 완전히 사라지도록 burn을 `Dissolve × (1 + EdgeWidth)`로 늘려 씁니다.

```
UV ──▶ Simple Noise.UV          [NoiseScale] ──▶ Simple Noise.Scale        → noise (0~1)

[EdgeWidth] ──▶ Add(A=1, B=EdgeWidth)            → (1 + w)
[Dissolve] ──▶ Multiply(A=Dissolve, B=(1 + w))   → burn
Subtract(A=burn, B=EdgeWidth)                    → burnStart

Step(Edge=burnStart, In=noise)   → visible   (noise ≥ burnStart 이면 1: 아직 남은 픽셀)
Step(Edge=burn,      In=noise)   → intact    (noise ≥ burn 이면 1: 불타지 않은 픽셀)
Subtract(A=visible, B=intact)    → edgeMask  (burnStart ≤ noise < burn 구간만 1)
```

3. 출력에 합치기 — 1단계의 연결을 이렇게 바꿉니다.

```
Multiply(A=[EdgeColor], B=edgeMask)          → glow
Add(A=Lerp.Out, B=glow)                      → Fragment.Base Color
Multiply(A=Sample Texture 2D.A, B=visible)   → Fragment.Alpha
```

4. Save Asset → `M_Enemy`의 Dissolve 슬라이더를 0→1로 움직이며 가장자리가 주황으로 빛나며 타들어가는지 확인합니다. 13장의 Bloom(HDR)이 켜져 있으면 가장자리가 번집니다.
5. **Sub Graph로 추출**: step 2의 노드들(Simple Noise ~ edgeMask)을 드래그로 선택 → 우클릭 → **Convert To → Sub-graph** → `SubG_Dissolve`로 저장. 입력(UV, Dissolve, EdgeWidth, NoiseScale), 출력(visible, edgeMask) 포트 이름을 Sub Graph 안의 Blackboard·Output 노드에서 알아보기 쉽게 바꿉니다. 이후 보스·플레이어 그래프에서도 이 노드 하나로 디졸브를 씁니다.

### 4단계 — DissolveOnDeath와 Enemy 연결

```csharp
// Assets/_CoinRush/Scripts/Rendering/DissolveEffect.cs
using System;
using System.Collections;
using UnityEngine;

[RequireComponent(typeof(SpriteRenderer))]
public class DissolveEffect : MonoBehaviour
{
    private static readonly int DissolveId = Shader.PropertyToID("_Dissolve");

    [SerializeField] private float duration = 0.45f;

    private SpriteRenderer spriteRenderer;
    private MaterialPropertyBlock block;

    public bool IsPlaying { get; private set; }

    private void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        block = new MaterialPropertyBlock();
    }

    private void OnEnable()
    {
        IsPlaying = false;
        SetDissolve(0f);                      // 재사용 시 완전히 보이는 상태로
    }

    public void Play(Action onComplete)
    {
        if (IsPlaying) return;
        StartCoroutine(Routine(onComplete));
    }

    private IEnumerator Routine(Action onComplete)
    {
        IsPlaying = true;
        float t = 0f;
        while (t < duration)
        {
            t += Time.deltaTime;              // 게임 시간 기준: 레벨업 창에서 멈춰도 자연스러움
            SetDissolve(t / duration);
            yield return null;
        }
        SetDissolve(1f);
        IsPlaying = false;
        onComplete?.Invoke();
    }

    private void SetDissolve(float value)
    {
        spriteRenderer.GetPropertyBlock(block);   // HitFlash의 값 보존
        block.SetFloat(DissolveId, value);
        spriteRenderer.SetPropertyBlock(block);
    }
}
```

에디터 작업(부착·연결):

1. 적 프리팹(Slime, Bat)을 열고 SpriteRenderer가 있는 오브젝트(05장 구성에서는 루트)에 `DissolveEffect`와 2단계의 `HitFlash`를 추가합니다. SpriteRenderer의 Material이 `M_Enemy`인지 확인합니다.
2. 루트 `Enemy`의 **Dissolve** 슬롯(아래 코드에서 추가)에 그 오브젝트를 드래그합니다. 비워 두면 `Awake`가 자식에서 찾아 보고, 그래도 없으면 콘솔에 오류를 남기고 디졸브 없이 즉시 반환합니다.

12장 `Enemy`의 사망 경로를 바꿉니다. 바뀌는 것은 필드 세 개, `Awake`, `OnEnable`, `OnDied`입니다.

```csharp
// Enemy.cs (12장) — 필드 추가
[SerializeField] private DissolveEffect dissolve;
private Collider2D bodyCollider;
private EnemyMotor2D motor;                       // 07장 — 이동 담당

// Awake 끝에 추가
bodyCollider = GetComponent<Collider2D>();
motor = GetComponent<EnemyMotor2D>();
if (dissolve == null) dissolve = GetComponentInChildren<DissolveEffect>();
if (dissolve == null) Debug.LogError("Enemy: DissolveEffect가 연결되지 않았습니다. 사망 연출 없이 반환합니다.", this);

// OnEnable 끝에 추가 (재사용 시 복구)
bodyCollider.enabled = true;
if (motor != null) motor.enabled = true;

// OnDied 교체
private void OnDied()
{
    if (!isSpawned) return;
    isSpawned = false;
    aliveEnemies.Remove(health);                  // 타는 동안 AutoAimWeapon이 시체를 조준하지 않게 즉시 제외

    bodyCollider.enabled = false;                 // 타는 동안 플레이어·투사체와 충돌하지 않음
    if (motor != null) motor.enabled = false;     // 모터의 FixedUpdate가 속도를 다시 쓰지 않게 정지
    body.linearVelocity = Vector2.zero;

    if (pools != null)
    {
        for (int i = 0; i < data.coinDrop; i++)
            pools.Coins.Spawn(transform.position + (Vector3)(Random.insideUnitCircle * 0.4f));
        if (loot != null) loot.Drop(pools, transform.position);
    }
    AudioManager.Instance.PlaySfx(deathSfx);

    if (dissolve != null)
        dissolve.Play(() => { if (Pool != null) Pool.Release(this); else Destroy(gameObject); });   // 다 탄 뒤 반환
    else if (Pool != null) Pool.Release(this);
    else Destroy(gameObject);
}
```

지금은 연출이 끝나면 `Enemy`가 직접 풀에 반환합니다. 22장에서 스포너가 반환을 맡게 되면 완료 콜백 안의 `Pool.Release(this)`를 `RequestRelease()`로 바꿉니다. 규칙은 같습니다: **드롭 → 사망 연출 → 연출이 끝난 뒤 반환**.

이동은 12장부터 `Enemy`가 아니라 07장 `EnemyMotor2D`가 하므로, `Enemy`에 가드를 넣는 대신 **모터 컴포넌트 자체를 끕니다**(비활성 컴포넌트는 `FixedUpdate`가 호출되지 않음). 재사용 시 `OnEnable`에서 다시 켜고, 12장 `Init`이 속도를 0으로 초기화합니다. 디졸브가 끝나기 전에 씬이 바뀌어 오브젝트가 파괴되면 코루틴도 함께 멈추므로 Release가 호출되지 않지만, 씬과 함께 풀도 사라지므로 문제가 없습니다.

### 5단계 — 효과 3: UV 스크롤 배경

1. 배경 텍스처(이음새 없이 반복되는 타일 이미지) 임포트 설정: Texture Type `Sprite (2D and UI)`, **Mesh Type `Full Rect`**, **Wrap Mode `Repeat`**. 13장의 `Atlas_Gameplay`에 포함되지 않은 폴더에 둡니다.
2. Create → Shader Graph → URP → **Sprite Unlit Shader Graph**, `SG_ScrollBackground`(배경이 조명을 받게 하려면 Sprite Lit).
3. 속성: `MainTex`(Reference `_MainTex`), `ScrollSpeed`(Vector2, Reference `_ScrollSpeed`, 기본 (0.02, 0.01)), `Tiling`(Vector2, Reference `_Tiling`, 기본 (4, 4)), `Tint`(Color, Reference `_Tint`, 기본 흰색).
4. 연결:

```
Time.Time ──▶ Multiply(A=Time, B=[ScrollSpeed])          → offset (Vector2)
UV ──▶ Tiling And Offset.UV
[Tiling] ──▶ Tiling And Offset.Tiling
offset ──▶ Tiling And Offset.Offset
Tiling And Offset.Out ──▶ Sample Texture 2D.UV   ([MainTex] ──▶ Texture)
Multiply(A=Sample.RGBA, B=[Tint]) ──▶ Split → RGB는 Base Color, A는 Alpha
```

   Multiply에 Float(Time)과 Vector2를 연결하면 Float이 자동 확장됩니다. 포트 색이 다르면 연결 후 노드 미리보기로 결과를 확인하세요.
5. 머티리얼 `M_ScrollBackground` → 배경 오브젝트(SpriteRenderer, Sorting Layer `Background`, 화면을 덮을 만큼 Scale)에 지정.
6. 패럴랙스: 같은 셰이더로 머티리얼을 두 개 만들어 먼 층은 ScrollSpeed를 작게, 가까운 층은 크게 줍니다(층마다 머티리얼이 다르므로 드로우 콜은 층 수만큼).

> Time 노드는 셰이더 내장 시간(`_Time`)을 쓰며, 이 값은 C#의 `Time.time`처럼 **timeScale이 적용된 게임 시간**입니다. 그래서 레벨업 창(timeScale 0)에서는 배경도 멈추고, 16장 슬로모션에서는 느려집니다. 일시정지 중에도 계속 흐르게 하는 방법은 연습 문제 2에서 다룹니다.

### 6단계 — 효과 4: 외곽선

보물 상자·자석 아이템처럼 "눈에 띄어야 하는" 픽업에 외곽선을 둘러줍니다. 원리는 **현재 픽셀은 투명한데, 상하좌우 한 텍셀 옆에 불투명 픽셀이 있으면 외곽선**입니다.

1. 스프라이트 임포트: **Mesh Type `Full Rect`**, 이미지 가장자리에 두께 이상의 투명 여백이 있어야 합니다. 아틀라스에 넣는다면 Padding ≥ 두께.
2. Create → Shader Graph → URP → Sprite Lit Shader Graph, `SG_PickupOutline`.
3. 속성: `MainTex`(`_MainTex`), `OutlineColor`(Color, **HDR**, `_OutlineColor`, 노랑 Intensity 2), `OutlineThickness`(Float, `_OutlineThickness`, 기본 1 — 텍셀 단위).
4. 한 텍셀 크기 구하기:

```
[MainTex] ──▶ Texel Size.Texture
Combine(R=Texel Size.Width, G=Texel Size.Height) → size (Vector2, 픽셀 수)
Divide(A=[OutlineThickness], B=size)            → step (Vector2, UV 단위 오프셋)
Split(step) → sx = R, sy = G
Combine(R=sx, G=0) → dx       Combine(R=0, G=sy) → dy
```

5. 네 방향 샘플링(Sample Texture 2D 노드 4개, 모두 Texture에 [MainTex]):

```
Add(UV, dx)      ──▶ Sample#1.UV ──▶ A1
Subtract(UV, dx) ──▶ Sample#2.UV ──▶ A2
Add(UV, dy)      ──▶ Sample#3.UV ──▶ A3
Subtract(UV, dy) ──▶ Sample#4.UV ──▶ A4
Maximum(A1, A2) → m12    Maximum(A3, A4) → m34    Maximum(m12, m34) → neighbor
```

   UV 노드는 4채널이므로 Add/Subtract 전에 **Split → Combine**으로 Vector2를 만들거나, dx·dy를 Vector4(0 채움)로 맞춥니다.
6. 마스크와 출력:

```
Sample Texture 2D(원래 UV) → center RGBA, center A
Subtract(A=neighbor, B=centerA) → Saturate → outlineMask   (바깥 테두리만 1)
Lerp(A=center RGBA, B=[OutlineColor], T=outlineMask) → Fragment.Base Color
Maximum(A=centerA, B=outlineMask)                    → Fragment.Alpha
```

7. 5~6의 노드를 선택해 **Convert To → Sub-graph**, `SubG_SpriteOutline`(입력: Texture2D, UV, Thickness / 출력: outlineMask). 적 중 엘리트 몬스터 그래프에서 같은 Sub Graph로 빨간 외곽선을 줄 수 있습니다.
8. 머티리얼 `M_PickupOutline`을 보물 상자 프리팹에 지정합니다.

> 대각선 방향 4개를 더 샘플링하면 모서리가 매끄러워지지만 텍스처 읽기가 픽셀당 9번이 됩니다. 화면에 몇 개뿐인 픽업이면 괜찮고, 적 500마리 전체에 쓰기엔 비쌉니다.

### 확인하기

1. 적을 공격하면 맞은 적만 0.12초 동안 하얗게 번쩍입니다. 다른 적은 번쩍이지 않고, Play 종료 후 `M_Enemy` 에셋의 Flash Amount는 0 그대로입니다.
2. 적이 죽으면 주황빛 가장자리를 남기며 약 0.45초 동안 **제자리에서** 불규칙하게 타들어가고, 그동안 플레이어와 충돌하지 않고 자동 조준이 그 적을 쏘지 않으며, 다 탄 뒤 풀로 돌아갑니다(Hierarchy에서 비활성화 확인). 콘솔에 `DissolveEffect가 연결되지 않았습니다` 오류가 없어야 합니다.
3. 풀에서 재사용된 적이 반쯤 탄 상태나 하얀 상태로 나타나지 않고, 정상적으로 플레이어를 추적합니다(모터 복구).
4. 배경이 끊김·이음새 없이 대각선으로 천천히 흐릅니다.
5. 보물 상자 둘레에 1텍셀 두께의 노란 외곽선이 보이고, Bloom으로 은은하게 빛납니다.
6. Frame Debugger에서 번쩍이지 않는 평상시의 적들은 여전히 소수의 호출로 묶여 있습니다.

## 흔한 실수

1. **스프라이트가 하얀 사각형 또는 분홍색으로 보임** → 텍스처 속성 Reference가 `_MainTex`가 아니어서 SpriteRenderer의 텍스처가 연결되지 않음(흰색), 또는 그래프 컴파일 오류(분홍) → Reference를 `_MainTex`로 고치고 Save Asset, 그래프의 오류 노드를 확인합니다.
2. **한 마리를 때렸는데 모든 적이 번쩍임** → `sharedMaterial`이나 머티리얼 에셋을 직접 수정 → `MaterialPropertyBlock`으로 렌더러별 값을 설정합니다.
3. **번쩍임을 넣었더니 디졸브가 안 되거나 반대** → 두 컴포넌트가 `GetPropertyBlock` 없이 새 블록을 `SetPropertyBlock` 해 서로의 값을 지움 → 항상 Get → Set → SetPropertyBlock 순서를 지킵니다.
4. **외곽선이 스프라이트 모양 안쪽에서 잘리거나 전혀 안 보임** → Mesh Type이 Tight라 투명 영역에 메시가 없음, 또는 이미지에 여백이 없음, 또는 아틀라스 Padding이 부족해 이웃 스프라이트가 읽힘 → Full Rect, 투명 여백, Padding ≥ 두께를 확인합니다.
5. **UV 스크롤 배경에 다른 스프라이트 조각이 흘러나옴** → 배경 텍스처가 아틀라스에 포함되어 UV가 아틀라스 기준 → 아틀라스에서 제외하고 Wrap Mode를 Repeat로 둡니다.
6. **`material`로 테스트했더니 메모리가 계속 증가** → `renderer.material`은 렌더러마다 **첫 접근 때 한 번** 복제본을 만들고(같은 렌더러에서 다시 읽으면 그 복제본을 재사용), 그 복제본은 GameObject를 `Destroy`해도 자동으로 해제되지 않음. 풀링 없이 적을 생성·파괴하면 적마다 복제본이 쌓임 → MPB로 바꾸거나, 인스턴스를 쓸 수밖에 없다면 `OnDestroy`에서 `Destroy(instanceMaterial)`을 호출합니다(씬 전환 시 `Resources.UnloadUnusedAssets`로도 정리됨).

## 연습 문제

1. ★☆☆ 플레이어가 무적 시간(07장) 동안 반투명하게 깜빡이도록, `SG_Enemy`를 복제한 `SG_Player`에 `_Alpha` 속성을 추가하고 C#에서 MPB로 제어하세요.

<details><summary>힌트·해설</summary>

Fragment.Alpha 앞에 `Multiply(A=기존 알파, B=[Alpha])`를 넣습니다. C#에서는 `Shader.PropertyToID("_Alpha")`를 캐싱하고 무적 중 `Mathf.PingPong(Time.unscaledTime * 10f, 1f) > 0.5f ? 0.3f : 1f`를 설정합니다. SpriteRenderer.color의 알파로도 가능하지만, 셰이더 속성으로 두면 번쩍임·디졸브와 같은 방식으로 관리할 수 있습니다.

</details>

2. ★★☆ Time 노드는 timeScale을 따르므로 레벨업 창(`timeScale = 0`)이 열리면 배경 스크롤도 멈춥니다. 반대로 **일시정지·레벨업 중에도 배경이 계속 흐르게** 하세요. Time 노드 대신 C#이 실제 시간으로 누적한 오프셋을 셰이더에 넘기는 방식으로 바꿉니다.

<details><summary>힌트·해설</summary>

그래프에서 `Time × ScrollSpeed` 대신 `_ScrollOffset`(Vector2) 속성을 Tiling And Offset.Offset에 연결합니다. C#에서는 `Time.unscaledDeltaTime`으로 누적합니다.

```csharp
offset += scrollSpeed * Time.unscaledDeltaTime;     // timeScale 0이어도 진행
offset.x = Mathf.Repeat(offset.x, 1f);              // x·y 모두 0~1로 순환 — 한쪽만 하면 다른 축이 계속 커짐
offset.y = Mathf.Repeat(offset.y, 1f);
renderer.GetPropertyBlock(block);
block.SetVector(ScrollOffsetId, offset);            // Vector2 → Vector4 암시 변환
renderer.SetPropertyBlock(block);
```

오프셋은 Tiling 뒤에 더해지므로 1만큼 건너뛰어도 반복 텍스처 모양이 같아 이음새가 생기지 않습니다. 순환시키지 않으면 몇 시간 뒤 float 정밀도가 떨어져 스크롤이 계단처럼 끊깁니다(15장 precision). 게임 시간 기준으로 되돌리고 싶으면 `Time.deltaTime`만 바꾸면 되므로, 이 방식은 "배경 전용 시계"를 게임 규칙에 맞게 고를 수 있다는 장점이 있습니다.

</details>

3. ★★☆ 디졸브의 가장자리 색이 타는 동안 노랑 → 빨강으로 변하게 하세요. 새 속성을 추가하지 말고 기존 `_Dissolve` 값만 이용합니다.

<details><summary>힌트·해설</summary>

`Lerp(A=노랑 HDR, B=빨강 HDR, T=[Dissolve])`로 가장자리 색을 만들어 `_EdgeColor` 자리에 연결합니다. 두 색은 그래프 안 Color 노드(HDR 모드)로 두거나, 머티리얼에서 조절하고 싶다면 두 개의 Color 속성으로 둡니다. 곡선을 바꾸고 싶으면 T 앞에 `Smoothstep(0.2, 0.8, Dissolve)`를 넣어보세요.

</details>

4. ★★★ 셰이더 하나로 "피격 번쩍임 + 디졸브 + 외곽선(엘리트만)"을 모두 지원하는 `SG_EnemyFull`을 만들되, 외곽선을 쓰지 않는 일반 적은 텍스처 샘플링 4번의 비용을 치르지 않도록 하세요.

<details><summary>힌트·해설</summary>

Blackboard에 **Boolean Keyword**(예: `_OUTLINE_ON`)를 추가하고, 그 키워드를 작업 영역에 드래그하면 On/Off 입력을 가진 키워드 노드가 생깁니다. On 쪽에 외곽선 결과를, Off 쪽에 원래 색을 연결하면 두 개의 셰이더 **변형(variant)** 이 컴파일되어 일반 적은 샘플링 없는 변형을 씁니다. 키워드 Definition이 Shader Feature면 사용하지 않는 변형은 빌드에서 빠집니다. 일반 적과 엘리트는 머티리얼이 달라지므로(키워드는 머티리얼 단위) 배칭 그룹이 둘로 나뉜다는 점까지 Frame Debugger로 확인하세요. 변형과 키워드의 비용은 15장에서 자세히 다룹니다.

</details>

## 셀프 체크

1. `SpriteRenderer.color`로는 스프라이트를 하얗게 번쩍이게 할 수 없는 이유를 셰이더 계산으로 설명하고, Shader Graph에서 어떻게 해결했는지 말해보세요.

<details><summary>모범 답안</summary>

기본 스프라이트 셰이더는 텍스처 색에 정점 색(SpriteRenderer.color)을 곱합니다. 색 값은 0~1이므로 곱하면 원래보다 어두워지거나 같을 뿐 밝아질 수 없습니다. Shader Graph에서는 텍스처 색과 흰색(`_FlashColor`)을 `Lerp`로 섞고 `_FlashAmount`를 T로 써서, T=1일 때 Base Color가 텍스처와 무관하게 흰색이 되게 했습니다. 알파는 원래 텍스처 알파를 유지해 모양은 그대로 둡니다. 단 Sprite Lit에서는 이 Base Color에 2D 조명이 곱해지므로, 어두운 조명 아래 최종 화면은 순백이 아니라 조명 색만큼 밝아진 색입니다. 조명과 무관한 순백이 필요하면 조명을 받지 않는 Sprite Unlit 오버레이 렌더러를 번쩍이는 동안만 겹쳐 그립니다.

</details>

2. `material`, `sharedMaterial`, `MaterialPropertyBlock`의 차이를 적 500마리 상황을 예로 설명해보세요.

<details><summary>모범 답안</summary>

`sharedMaterial`은 에셋 하나를 수정하므로 500마리가 동시에 바뀌고 에디터에서는 에셋에 저장됩니다. `material`은 렌더러마다 첫 접근 때 한 번 복제본을 만들어(이후 접근은 재사용) 500개의 머티리얼이 생기고, 메모리·할당이 늘며 직접 파괴하지 않으면 누수되고 배칭도 깨집니다. `MaterialPropertyBlock`은 머티리얼을 공유한 채 렌더러별 값만 덮어써 복제가 없고, 값이 다른 동안만 해당 렌더러가 배칭에서 빠질 수 있습니다.

</details>

3. 디졸브 그래프에서 `Step` 두 개와 `Subtract`로 가장자리 마스크를 만드는 원리를 설명해보세요.

<details><summary>모범 답안</summary>

`Step(Edge, In)`은 In이 Edge 이상이면 1입니다. 노이즈에 대해 `Step(burnStart, noise)`는 아직 남아 있는 픽셀, `Step(burn, noise)`는 전혀 타지 않은 픽셀을 1로 만듭니다. 앞의 것에서 뒤의 것을 빼면 `burnStart ≤ noise < burn`인 얇은 구간만 1이 되어 타는 가장자리 마스크가 됩니다. 이 마스크에 HDR 색을 곱해 더하고, 알파에는 첫 번째 Step 결과를 곱해 탄 부분을 투명하게 합니다.

</details>

4. 외곽선 효과를 위해 Mesh Type을 Full Rect로 바꿔야 하는 이유와, 아틀라스 Padding이 필요한 이유를 설명해보세요.

<details><summary>모범 답안</summary>

프래그먼트 셰이더는 메시가 덮는 픽셀에서만 실행됩니다. Tight 메시는 스프라이트의 불투명 모양을 따라 잘려 있어 모양 바깥의 투명 픽셀이 그려지지 않으므로, 외곽선을 칠할 픽셀 자체가 없습니다. Full Rect는 투명 여백까지 사각형으로 덮습니다. 또 외곽선은 한 텍셀 옆을 샘플링하므로, 아틀라스에서 이웃 스프라이트와의 간격(Padding)이 두께보다 작으면 이웃의 불투명 픽셀을 읽어 엉뚱한 선이 생깁니다.

</details>

5. `Shader.PropertyToID`를 `static readonly`로 캐싱하는 이유와, 두 컴포넌트가 같은 렌더러의 MPB를 다룰 때 지켜야 할 순서는 무엇인가요?

<details><summary>모범 답안</summary>

문자열 이름으로 속성을 설정하면 호출마다 문자열을 정수 ID로 변환하는 비용이 듭니다. ID는 실행 중 변하지 않으므로 한 번 계산해 정적 필드에 두면 됩니다. 렌더러당 블록은 하나라서, 각 컴포넌트는 `GetPropertyBlock`으로 현재 값을 읽고 자기 속성만 설정한 뒤 `SetPropertyBlock`해야 다른 컴포넌트가 넣은 값을 지우지 않습니다.

</details>

## 핵심 요약

- 정점 셰이더는 정점마다 위치를 변환하고, 프래그먼트 셰이더는 픽셀마다 최종 색을 계산합니다. 색 효과는 대부분 프래그먼트에서 만듭니다.
- Sprite Lit/Unlit Shader Graph에서 텍스처 속성의 Reference는 반드시 `_MainTex`이며, 수정 후 Save Asset이 필요합니다.
- 번쩍임 = `Lerp(텍스처색, 흰색, 양)`, 디졸브 = 노이즈 + `Step` 두 개의 차로 가장자리, UV 스크롤 = `Time × 속도`를 Offset에, 외곽선 = 주변 텍셀 알파의 최댓값 − 자기 알파입니다.
- SpriteRenderer의 개별 값은 `MaterialPropertyBlock` + 캐싱한 `Shader.PropertyToID`로 제어하고, Get → Set → SetPropertyBlock 순서를 지킵니다.
- 풀링되는 오브젝트의 셰이더 값도 `OnEnable`에서 리셋합니다.
- 아틀라스 UV, Mesh Type(Full Rect), Wrap Mode(Repeat), Padding이 효과 품질을 좌우합니다.
- 반복되는 노드 조합은 Sub Graph로 추출해 여러 그래프에서 재사용합니다.

## 더 읽을거리

- Shader Graph 패키지 문서: https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/index.html
- Shader Graph Node Library (각 노드의 Generated Code Example 포함, 위 문서의 "Node Library" 항목)
- Unity Scripting API — MaterialPropertyBlock: https://docs.unity3d.com/ScriptReference/MaterialPropertyBlock.html
- Daniel Ilett — Shader Graph 튜토리얼 블로그·유튜브 (danielilett.com)
- Ben Cloward — Shader Graph 기초 유튜브 시리즈
