# 13. URP 렌더 파이프라인 이해하기

> **이 장에서 배울 것**
> - 렌더 파이프라인의 단계(컬링→정렬→그리기→후처리)와 Built-in/URP/HDRP의 차이를 설명할 수 있다
> - URP Asset·Renderer Data·2D Renderer의 관계를 이해하고 품질 단계별로 에셋을 분리한다
> - 드로우 콜과 배칭(SRP Batcher, 스프라이트 배칭, 아틀라스, 정렬 순서의 영향)을 Frame Debugger로 진단할 수 있다
> - 2D Light와 후처리 Volume(Bloom, Color Adjustments, Vignette)으로 분위기를 만들고 코드에서 제어한다
>
> **선수 장**: 01, 11 · **예상 시간**: 3~4시간 · **코인 러시 진행**: 스프라이트 아틀라스로 드로우 콜 감소, 2D 조명의 어두운 분위기, Bloom, 피격 시 Vignette 강조, 저사양 품질 단계

## 왜 필요한가

12장까지 만든 코인 러시를 실행하면 기능은 다 되지만 두 가지가 아쉽습니다.

- **밋밋합니다.** 배경·적·코인이 모두 같은 밝기로 평평하게 그려집니다. 스크린샷 한 장으로 사람을 붙잡아야 하는 인디 게임에서 치명적입니다(27장).
- **생각보다 무겁습니다.** Game 뷰의 **Stats** 창을 켜면 적 300마리 상황에서 Batches가 수백 개입니다. 적·코인·투사체 스프라이트가 각각 다른 텍스처에 있고, 그리는 순서가 뒤섞여 있기 때문입니다. 저가 안드로이드 폰에서는 이것만으로 발열과 프레임 저하가 생깁니다.

색을 더하려고 무작정 조명·후처리를 켜면 두 번째 문제가 더 커집니다. 이 장에서는 **그림이 화면에 나오기까지의 공정**을 이해하고, 싸게 분위기를 만드는 법과 무거울 때 줄이는 법을 함께 익힙니다.

## 개념

### 렌더 파이프라인 — 씬이 픽셀이 되는 공정

```
매 프레임, 카메라마다
 1. 컬링(Culling)   카메라 시야 밖 렌더러 제외 (스프라이트 바운딩 박스 기준)
 2. 정렬(Sorting)   무엇을 먼저 그릴지 결정
                    2D 투명 스프라이트: Sorting Layer → Order in Layer → 카메라 거리
 3. 조명 준비        (2D Renderer) 2D Light를 "라이트 텍스처"에 먼저 그림
 4. 그리기(Draw)    정렬 순서대로 드로우 콜 발행. 배칭으로 호출 수를 줄임
 5. 후처리          완성된 화면 이미지에 Bloom, 색 보정, Vignette 등 적용
 6. UI 오버레이      Screen Space - Overlay 캔버스 (후처리 대상 아님)
```

JS로 비유하면 브라우저의 렌더링 파이프라인(스타일 계산 → 레이아웃 → 페인트 → 합성)과 같은 개념입니다. "무엇을 어떤 순서로 그릴지"를 정하는 규칙 묶음을 Unity는 교체 가능한 **렌더 파이프라인**으로 제공합니다.

### Built-in, URP, HDRP

| 항목 | Built-in | URP (Universal) | HDRP (High Definition) |
|---|---|---|---|
| 상태 | 레거시, 신규 기능 없음 | Unity 6 기본, 활발히 개발 | 고사양 전용 |
| 플랫폼 | 전부 | 모바일~PC~콘솔~웹 | PC·콘솔 고사양 |
| 2D 전용 렌더러·2D 조명 | 없음 | 있음 (2D Renderer) | 없음 |
| Shader Graph | 제한적 | 지원 | 지원 |
| 커스터마이즈 | 명령 버퍼 | Renderer Feature, Render Graph | Custom Pass |
| 1인 2D 게임 | 비추천 | **선택** | 과함 |

Unity 6의 **Universal 2D 템플릿**으로 만든 프로젝트는 이미 URP + 2D Renderer로 설정되어 있습니다. 파이프라인은 프로젝트 도중에 바꾸면 머티리얼·셰이더를 전부 옮겨야 하므로 처음에 정합니다.

### URP Asset, Renderer Data, 2D Renderer

URP 설정은 에셋 두 종류로 나뉩니다.

```
Project Settings → Graphics → Default Render Pipeline ─┐
Project Settings → Quality → (레벨별) Render Pipeline Asset ─┤ (레벨 값이 있으면 우선)
                                                             ▼
                              URP Asset (UniversalRenderPipelineAsset)
                              "얼마나 좋게": HDR, Render Scale, MSAA, 그림자, 후처리 품질
                                  │ Renderer List
                                  ▼
                              Renderer Data (여기서는 Renderer2DData)
                              "어떻게 그릴지": 2D 조명 설정, Light Blend Styles,
                              Renderer Feature 목록
```

- **URP Asset**은 품질 관련 수치를 가집니다. 품질 단계(Quality Level)마다 다른 URP Asset을 지정할 수 있어서, "High"와 "Low"를 에셋 단위로 나눕니다.
- **Renderer Data**는 그리는 방식입니다. 2D 게임은 **2D Renderer Data**를 쓰고, 3D용 Universal Renderer와는 설정 항목이 다릅니다. 여러 URP Asset이 같은 Renderer Data를 공유해도 됩니다.
- 템플릿에는 보통 `Assets/Settings/` 아래에 이 에셋들이 들어 있습니다(이름은 템플릿 버전에 따라 조금 다를 수 있음).

### 드로우 콜, SetPass, 배칭

CPU가 GPU에 "이 메시를 이 머티리얼로 그려라"고 명령하는 것이 **드로우 콜**입니다. 명령 자체보다 **렌더 상태 변경**(셰이더·텍스처·블렌딩 바꾸기, Stats의 SetPass calls)이 특히 비쌉니다. **배칭**은 여러 오브젝트를 묶어 명령 수와 상태 변경을 줄이는 기술입니다.

| 기법 | 대상 | 조건 | 2D 게임에서 |
|---|---|---|---|
| SRP Batcher | MeshRenderer 등 SRP 호환 셰이더 | 같은 셰이더 **변형**이면 머티리얼이 달라도 상태 설정을 공유. 머티리얼 속성이 `UnityPerMaterial` CBUFFER에 있어야 함(15장) | 타일맵·메시 기반 오브젝트, 커스텀 셰이더 |
| 스프라이트 배칭 (동적 배칭 계열) | SpriteRenderer | **같은 머티리얼 + 같은 텍스처**이고 그리는 순서상 **연속**일 때 정점을 합쳐 한 번에 | 핵심. 아틀라스로 텍스처를 통일 |
| GPU Instancing | 같은 메시 대량 | 인스턴싱 지원 셰이더 | 2D 스프라이트에는 보통 해당 없음 |

SpriteRenderer의 배칭 방식과 SRP Batcher 호환 여부는 Unity 버전에 따라 개선이 이어지고 있으니, 결론은 항상 **Frame Debugger에서 직접 확인**하는 것으로 내립니다.

### 스프라이트 아틀라스와 정렬 순서가 배칭을 깨는 경우

스프라이트 배칭의 조건은 "같은 텍스처가 **연달아**"입니다. 정렬 순서가 텍스처를 번갈아 쓰게 만들면 배칭이 깨집니다.

```
[아틀라스 없음, 적과 코인이 같은 Sorting Layer·Order]
  카메라 거리 순으로 정렬 → 적A(enemy.png) 코인(coin.png) 적B(enemy.png) 코인(coin.png) ...
  → 텍스처가 매번 바뀜 → 300개 = 드로우 콜 약 300

[해결 1: Sorting Layer 분리]
  Enemies 레이어 전부 → Pickups 레이어 전부
  → enemy.png 1회 + coin.png 1회 = 2

[해결 2: 스프라이트 아틀라스]
  enemy.png, coin.png → 한 장의 atlas 텍스처
  → 순서가 섞여도 텍스처·머티리얼이 같음 = 1
```

실전에서는 둘 다 합니다. Sorting Layer는 "무엇이 위에 보일지"라는 게임 규칙으로 정하고, 같은 시점에 함께 보이는 스프라이트는 같은 아틀라스에 넣습니다. 반대로 배칭을 깨는 대표 요인은 다음과 같습니다.

- 스프라이트마다 **다른 머티리얼**(14장의 피격 효과를 `material` 인스턴스로 만들 때)
- **MaterialPropertyBlock**으로 값이 서로 다른 속성 설정(14장에서 트레이드오프를 다룸)
- 같은 아틀라스라도 아틀라스가 여러 **페이지**로 나뉘어 텍스처가 달라진 경우
- 사이에 끼어드는 다른 텍스처의 스프라이트, 파티클, 텍스트

### Stats 창과 Frame Debugger 읽는 법

Game 뷰 오른쪽 위 **Stats** 버튼은 가장 빠른 1차 지표입니다.

| 항목 | 의미 | 볼 점 |
|---|---|---|
| Batches | 실제로 GPU에 보낸 그리기 묶음 수 | 적 수에 비례해 늘면 배칭 실패 |
| Saved by batching | 배칭으로 합쳐 아낀 수 | 0에 가까우면 조건을 못 맞추는 중 |
| SetPass calls | 셰이더 패스(렌더 상태) 전환 수 | 머티리얼 종류 수와 비슷해야 정상 |
| Tris / Verts | 그린 삼각형·정점 수 | Tight 메시 스프라이트는 정점이 늘어남 |

에디터 수치는 에디터 자체 렌더링이 섞여 실제 기기와 다르므로 **추세 비교용**으로만 쓰고, 최종 판단은 18장의 기기 프로파일링으로 합니다. 원인을 찾을 때는 Frame Debugger를 씁니다.

**Window → Analysis → Frame Debugger** → Enable. 게임이 한 프레임에서 멈추고, 왼쪽에 그 프레임의 렌더 이벤트 목록이 나옵니다.

1. 왼쪽 트리에서 2D 렌더링 패스를 펼치면 `Draw Dynamic`, `SRP Batch`, `Draw Mesh` 같은 항목이 순서대로 보입니다.
2. 슬라이더를 움직이면 Game 뷰에 **그 드로우 콜까지 그려진 화면**이 표시됩니다. 어떤 스프라이트가 어느 호출에서 그려지는지 눈으로 확인합니다.
3. 항목을 선택하면 오른쪽에 셰이더, 사용된 텍스처, 그리고 **"Why this draw call can't be batched with the previous one"** 이유가 나옵니다. "different textures", "different materials", "MaterialPropertyBlock" 같은 문구가 바로 고칠 곳입니다.

Unity 6에는 **Window → Analysis → Render Graph Viewer**도 있어 패스 단위의 리소스 흐름을 볼 수 있습니다. 배칭 진단은 Frame Debugger, 패스 구조 이해는 Render Graph Viewer로 나눠 씁니다.

### 2D Light

2D Renderer는 스프라이트를 그리기 전에 조명을 **라이트 텍스처**에 그리고, `Sprite-Lit-Default` 머티리얼을 쓰는 스프라이트가 그 텍스처를 샘플링해 밝기를 곱합니다(`Sprite-Unlit-Default`는 조명 무시). Hierarchy → Light → 2D에서 만듭니다.

| 종류 | 모양 | 용도 |
|---|---|---|
| Global Light 2D | 화면 전체 균일 | 기본 밝기·색조. 어둡게 깔고 다른 조명으로 포인트를 줌 |
| Spot Light 2D | 원/부채꼴 (Inner/Outer Radius, 각도) | 플레이어 주변 시야, 횃불, 폭발 섬광 |
| Freeform Light 2D | 직접 편집한 다각형 | 창문 빛, 용암 지대 |
| Sprite Light 2D | 스프라이트 모양 | 복잡한 무늬(창살 그림자 등) |

알아둘 설정:

- **Target Sorting Layers**: 조명이 영향을 줄 Sorting Layer. UI처럼 밝기가 바뀌면 안 되는 레이어는 제외합니다.
- **Blend Style**: 2D Renderer Data의 Light Blend Styles에서 정의(곱하기·더하기 등). 기본 Multiply로 시작합니다.
- **Normal Map**: 스프라이트에 굴곡 정보를 주면 빛 방향에 따라 입체적으로 보입니다. Sprite Editor → **Secondary Textures**에 `_NormalMap` 이름으로 노멀 맵을 등록하고, 조명의 Normal Maps 품질을 켭니다. 노멀 맵은 표면의 방향을 RGB에 저장한 텍스처로, 픽셀 아트에서는 직접 그리거나 도구로 생성합니다.
- **비용**: 조명이 많을수록, 화면에서 차지하는 면적이 클수록 라이트 텍스처에 그리는 비용이 늘어납니다. 코인 100개에 각각 조명을 다는 대신 **발광처럼 보이는 스프라이트 + Bloom**으로 흉내 내는 것이 정석입니다.

### 후처리 Volume

후처리는 완성된 화면에 거는 필터입니다. URP는 **Volume** 컴포넌트로 설정합니다.

```
Global Volume (Mode: Global)          ← 어디서든 적용
 └ Volume Profile (에셋)
     ├ Bloom               Threshold, Intensity, Scatter, Tint
     ├ Color Adjustments   Post Exposure, Contrast, Color Filter, Saturation
     └ Vignette            Color, Center, Intensity, Smoothness
Local Volume (Mode: Local + Collider)  ← 영역 안에서만, Priority가 높으면 덮어씀
```

**가장 흔한 함정**: 카메라의 **Rendering → Post Processing** 체크가 꺼져 있으면 Volume을 아무리 설정해도 아무 변화가 없습니다.

효과별 요점:

- **Bloom**: 밝은 픽셀이 번져 빛나 보이게 합니다. Threshold가 핵심인데, **칼같이 자르는 경계가 아닙니다.** URP Bloom은 Threshold 주변을 부드럽게 넘기는 soft knee를 쓰고, 그 폭은 Threshold의 절반으로 고정되어 있습니다. 픽셀 밝기(RGB 중 최댓값)를 b, Threshold를 T라 하면 대략 다음과 같습니다.

```
기여 비율 = max(b − T, soft) / b
soft      = clamp(b − T + T/2, 0, T)² / (2T)        ← T/2 = knee

T = 1일 때:  b = 0.5 이하 → 0      b = 0.8 → 약 0.06      b = 1.0 → 0.125      b = 3.0 → 약 0.67
(Inspector의 Threshold 값은 감마→선형 변환 후 쓰입니다. 1.0은 변환해도 1.0)
```

즉 Threshold 1에서도 **순백(1.0) 픽셀은 12.5%만큼 번집니다.** "1.0 넘는 색만 번진다"가 아니라 "1.0 근처는 조금, 1.0을 크게 넘을수록 확실히"입니다. 그래서 흰 UI풍 스프라이트나 밝은 배경이 은은하게 번질 수 있고, 특정 오브젝트만 **뚜렷하게** 빛나게 하려면 1.0을 크게 넘는 **HDR 색**이 필요합니다.
- **Color Adjustments**: 전체 색감. Saturation을 살짝 낮추고 Contrast를 올리면 스프라이트가 또렷해집니다.
- **Vignette**: 화면 가장자리를 어둡게. 평소 0.2 정도로 시선을 가운데로 모으고, 피격 순간 빨갛게 올리면 강한 피드백이 됩니다.

### HDR과 발광 색

**HDR(High Dynamic Range)** 은 색 값이 1.0을 넘을 수 있게 화면을 부동소수점 버퍼로 그리는 모드입니다. URP Asset의 **Quality → HDR**로 켭니다.

```
LDR:  색 (3.0, 2.0, 0.5) → 저장 시 (1, 1, 0.5)로 잘림 → 밝기 1.0 = 순백과 똑같이 soft knee로 12.5%만 번짐
      → 흰 벽·흰 글씨도 같은 정도로 번지므로 "이것만 빛남"을 만들 수 없음
HDR:  색 (3.0, 2.0, 0.5) 그대로 보관 → 밝기 3.0이라 약 67% 번짐, 순백(1.0)은 여전히 12.5%
      → 발광 오브젝트만 확연히 강하게 빛남
```

주의할 점은 **SpriteRenderer의 Color로는 1.0 넘는 값을 전달할 수 없다**는 것입니다. 정점 색이 8비트로 저장되기 때문입니다. 발광은 머티리얼 속성(HDR 모드 Color)으로 전달해야 하며, 14장에서 Shader Graph로 만듭니다. 또 HDR 버퍼는 메모리와 대역폭을 더 쓰므로 저사양 단계에서는 끄는 후보입니다.

### 렌더 해상도 — Render Scale

URP Asset의 **Quality → Render Scale**(0.1~2)은 3D 렌더링 해상도를 화면 대비 비율로 조절합니다. 0.75면 픽셀 수가 약 56%로 줄어 GPU 부담이 크게 줄고, 결과는 화면 크기로 늘려 표시됩니다(UI 오버레이는 원래 해상도). 2D Renderer에서의 적용 범위와 업스케일 필터 옵션은 URP 버전에 따라 차이가 있으니, 저사양 단계에 적용한 뒤 실제 기기에서 확인하세요.

고해상도 폰(예: 1440p)은 화면이 작아서 0.75로 내려도 차이가 잘 보이지 않는 반면 GPU 절감은 큽니다. 픽셀 아트 게임이라면 Pixel Perfect Camera와의 조합을 따로 검토해야 합니다.

## 실습: 코인 러시에 적용하기

앞 장 클래스의 최소 시그니처: `Health`(01) — `event Action<int,int> Changed(current, max)`, `SaveData`/`SaveSystem`(10) — `SaveSystem.Load()`, `SaveSystem.Save(SaveData)`.

### 1단계 — 현재 파이프라인 확인과 기준 측정

1. **Project Settings → Graphics**의 Default Render Pipeline에 URP Asset이 지정되어 있는지 확인합니다. 비어 있으면 Built-in입니다.
2. 그 URP Asset을 선택해 Renderer List의 첫 항목이 **2D Renderer Data**인지 확인합니다.
3. Main Camera 선택 → Camera 컴포넌트의 **Rendering → Post Processing** 체크를 켭니다.
4. 적 300마리가 나오는 시점에서 Game 뷰의 **Stats**를 켜고 Batches, SetPass calls를 적어둡니다. 이것이 개선 전 기준입니다.
5. Frame Debugger를 켜고 "can't be batched" 이유를 몇 개 읽어봅니다. 대부분 "different textures"일 것입니다.

### 2단계 — Sorting Layer 정리

1. **Project Settings → Tags and Layers → Sorting Layers**에 아래 순서로 추가합니다(위가 먼저 그려짐 = 뒤에 보임).

```
Background → Pickups → Enemies → Player → Projectiles → FX
```

2. 각 프리팹의 SpriteRenderer에서 Sorting Layer를 지정합니다. 코인·경험치 보석은 `Pickups`, 적은 `Enemies`, 데미지 숫자(12장 TextMeshPro)는 `FX`.
3. 같은 레이어 안에서 Order in Layer를 개별로 다르게 주지 않습니다. 오브젝트마다 순서를 달리 주면 정렬이 텍스처를 섞어 배칭이 깨집니다.

### 3단계 — 스프라이트 아틀라스

1. **Project Settings → Editor → Sprite Atlas → Mode**가 `Sprite Atlas V2 - Enabled`인지 확인합니다.
2. `Assets/_CoinRush/Art/Atlases/` 폴더에서 우클릭 → **Create → 2D → Sprite Atlas**, 이름 `Atlas_Gameplay`.
3. Inspector의 **Objects for Packing**에 적·코인·투사체·플레이어 스프라이트 **폴더**를 드래그합니다(폴더 단위로 넣으면 새 스프라이트가 자동 포함).
4. 설정: Include in Build 체크, Allow Rotation·Tight Packing **끔**(14장에서 UV를 쓰는 셰이더가 깨지지 않게), Padding 4, Max Texture Size 2048, 압축은 플랫폼별 기본값.
5. **Pack Preview**를 눌러 한 페이지에 다 들어가는지 확인합니다. 두 페이지로 나뉘면 크기를 올리거나 자주 함께 보이지 않는 것(보스 등)을 별도 아틀라스로 뺍니다.
6. 배경 타일·UI 스프라이트는 이 아틀라스에 넣지 않습니다. 함께 그려지지 않는 것을 섞으면 메모리만 차지합니다. 14장의 **UV 스크롤 배경**은 아틀라스에 넣으면 안 됩니다(아틀라스 UV가 전체 텍스처 기준이라 반복이 깨짐).
7. Play → Stats의 Batches를 1단계 기준과 비교합니다. Frame Debugger에서 적 300마리가 소수의 호출로 묶였는지 확인합니다.

> 에디터에서는 Play 모드에서만 아틀라스가 적용되고, Edit 모드 Scene 뷰에서는 원본 텍스처로 그려질 수 있습니다. 측정은 항상 Play 모드에서 합니다.

### 4단계 — 2D 조명으로 분위기 만들기

1. 적·코인·플레이어·배경 스프라이트의 머티리얼이 `Sprite-Lit-Default`인지 확인합니다(Universal 2D 템플릿 기본값). 데미지 숫자와 UI는 조명 영향을 받지 않게 둡니다.
2. 씬의 기존 Global Light 2D(없으면 Light → 2D → Global Light 2D 생성): Intensity **0.35**, Color 짙은 남색(예: `#5A6A9A`). Target Sorting Layers에서 `FX`를 제외합니다.
3. Player 자식으로 **Spot Light 2D** 생성: Inner Radius 1.5, Outer Radius 6, Intensity 0.9, Color 따뜻한 노랑(`#FFE3A8`), Falloff Strength 0.5. 플레이어 주변만 밝아져 "어둠 속에서 몰려오는 적"의 느낌이 납니다.
4. 코인에는 조명을 달지 않습니다. 대신 5단계의 Bloom과 14장의 HDR 발광으로 빛나 보이게 합니다.

### 5단계 — Global Volume과 후처리

1. Hierarchy → Volume → **Global Volume**. Inspector의 Profile 옆 **New**로 `VP_Gameplay` 프로필을 만듭니다.
2. **Add Override → Post-processing → Bloom**: Threshold 1.0, Intensity 0.8, Scatter 0.6. 체크박스를 켜야 값이 적용됩니다(각 속성 왼쪽의 override 체크).
   - **번짐 비교 실습**(5번의 HDR 확인까지 마친 뒤): 빈 씬 영역에 흰색 사각 스프라이트 `Bloom_White`(Material을 `Sprite-Unlit-Default`로 바꿔 4단계 조명의 영향을 없앰, Color 흰색)와, 14장에서 만들 HDR 색 머티리얼을 미리 흉내 낸 `Bloom_Hdr`을 나란히 둡니다. SpriteRenderer의 Color로는 1.0을 넘길 수 없으므로(개념의 HDR 절), `Bloom_Hdr`에는 Create → Shader Graph → URP → **Sprite Unlit Shader Graph** `SG_HdrTest`를 만들어 Color 속성(Mode **HDR**, Intensity 3)을 Base Color에, Sample Texture 2D(Reference `_MainTex`)의 A를 Alpha에 연결한 머티리얼을 지정합니다(Shader Graph 조작은 14장에서 자세히 다룹니다). Play 후 Threshold를 1.0 → 0.8 → 1.5로 바꾸며 흰 사각형은 1.0에서도 살짝 번지고 1.5에서 사라지는 반면, HDR 사각형은 계속 강하게 번지는 것을 확인합니다. 비교가 끝나면 두 오브젝트를 지웁니다.
3. **Color Adjustments**: Post Exposure 0, Contrast 15, Saturation -10.
4. **Vignette**: Color 검정, Intensity 0.2, Smoothness 0.4.
5. URP Asset(High용)의 **Quality → HDR** 체크를 확인합니다.

### 6단계 — 피격 시 Vignette 순간 강조

`Volume.profile`은 처음 접근할 때 **프로필 에셋의 복사본**을 만들어 반환합니다. 14장에서 볼 `renderer.material`과 같은 원리로, 에셋 자체(`sharedProfile`)를 바꾸면 Play 모드가 끝나도 값이 남아 버립니다.

```csharp
// Assets/_CoinRush/Scripts/Rendering/HitVignette.cs
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class HitVignette : MonoBehaviour
{
    [SerializeField] private Volume volume;
    [SerializeField] private Health playerHealth;
    [SerializeField] private Color hitColor = new Color(0.6f, 0f, 0f);
    [SerializeField] private float peakIntensity = 0.5f;
    [SerializeField] private float duration = 0.35f;

    private Vignette vignette;
    private float baseIntensity;
    private Color baseColor;
    private int lastHp = int.MaxValue;
    private float timer;

    private void Awake()
    {
        // profile(복사본)에서 Vignette 오버라이드를 찾음. 프로필에 Vignette가 없으면 비활성화.
        if (!volume.profile.TryGet(out vignette))
        {
            Debug.LogWarning("Volume Profile에 Vignette 오버라이드가 없습니다.", this);
            enabled = false;
            return;
        }
        vignette.intensity.overrideState = true;
        vignette.color.overrideState = true;
        baseIntensity = vignette.intensity.value;
        baseColor = vignette.color.value;
    }

    private void OnEnable()
    {
        playerHealth.Changed += OnHealthChanged;
        lastHp = playerHealth.Current;
    }

    private void OnDisable() => playerHealth.Changed -= OnHealthChanged;

    private void OnHealthChanged(int current, int max)
    {
        if (current < lastHp) timer = duration;       // 줄었을 때만 (회복은 무시)
        lastHp = current;
    }

    private void Update()
    {
        if (timer <= 0f) return;

        // 16장의 히트 스톱이 timeScale을 낮춰도 연출은 제 속도로
        timer = Mathf.Max(0f, timer - Time.unscaledDeltaTime);
        float t = timer / duration;                   // 1 → 0
        float k = t * t;                              // 처음에 강하고 빠르게 빠짐

        vignette.intensity.value = Mathf.Lerp(baseIntensity, peakIntensity, k);
        vignette.color.value = Color.Lerp(baseColor, hitColor, k);
    }
}
```

`Health`의 최소 시그니처는 `int Current`, `event Action<int,int> Changed`입니다. 빈 오브젝트 `PostFX`에 붙이고 Global Volume과 Player의 Health를 연결합니다.

> Volume 값을 매 프레임 바꾸는 것은 가벼운 작업입니다. 다만 여러 스크립트가 같은 오버라이드를 동시에 건드리면 마지막 쓴 값이 이기므로, 화면 효과는 이런 전담 컴포넌트 하나에 모읍니다(16장 `GameFeel`에서 통합).

### 7단계 — 품질 단계 분리

1. `Assets/Settings/`의 기존 URP Asset을 복제해 `URP_High`, `URP_Low`로 이름 붙입니다(둘 다 같은 2D Renderer Data를 써도 됩니다).
2. `URP_Low` 설정: **HDR 끔**, **Render Scale 0.75**, Anti Aliasing(MSAA) Disabled.
3. **Project Settings → Quality**: 레벨을 `Low`와 `High` 두 개만 남기고, 각 레벨의 **Render Pipeline Asset**에 `URP_Low`/`URP_High`를 지정합니다. 플랫폼별 기본 레벨(표 아래 초록 체크)을 Android·iOS는 High, 필요 시 Low로 둡니다.
4. 후처리는 품질 단계 설정만으로 꺼지지 않으므로 코드로 카메라의 후처리 여부도 함께 바꿉니다.

```csharp
// Assets/_CoinRush/Scripts/Rendering/GraphicsQuality.cs
using UnityEngine;
using UnityEngine.Rendering.Universal;

public class GraphicsQuality : MonoBehaviour
{
    [SerializeField] private Camera mainCamera;
    [SerializeField] private int lowLevelIndex = 0;   // Quality 설정 목록의 순서

    private void Start()
    {
        SaveData save = SaveSystem.Load();
        Apply(save.graphicsQuality);
    }

    /// <summary>설정 화면 드롭다운에서 호출. index는 Project Settings → Quality 목록 순서.</summary>
    public void SetLevel(int index)
    {
        Apply(index);
        SaveData save = SaveSystem.Load();
        save.graphicsQuality = index;
        SaveSystem.Save(save);
    }

    private void Apply(int index)
    {
        index = Mathf.Clamp(index, 0, QualitySettings.names.Length - 1);
        // true: 즉시 비싼 변경(안티앨리어싱 등)까지 적용. 로딩 화면 같은 곳에서 호출하는 것이 안전
        QualitySettings.SetQualityLevel(index, true);

        bool isLow = index == lowLevelIndex;
        mainCamera.GetUniversalAdditionalCameraData().renderPostProcessing = !isLow;
    }
}
```

`SaveData`(10장)에 `public int graphicsQuality = 1;` 필드를 추가하고 10장 규칙대로 버전을 올립니다. 11장 설정 화면에 `TMP_Dropdown`을 두고 `onValueChanged`에 `SetLevel`을 연결하면 됩니다.

> 저사양 단계에서 후처리를 통째로 끄면 피격 Vignette도 사라집니다. 피드백이 중요한 효과는 11장 UI의 빨간 테두리 이미지처럼 **후처리 없이도 보이는 대체 연출**을 두는 것을 고려하세요.

### 확인하기

1. Play → 화면이 전체적으로 어둡고 푸르며, 플레이어 주변만 따뜻하게 밝습니다. HUD는 어두워지지 않습니다.
2. Stats의 Batches가 1단계 기준보다 크게 줄었습니다. Frame Debugger에서 적 수백 마리가 하나 또는 소수의 호출로 그려집니다.
3. 적에게 맞으면 화면 가장자리가 빨갛게 번쩍였다가 0.35초 동안 원래대로 돌아옵니다. Play를 멈춘 뒤 `VP_Gameplay` 에셋의 Vignette 값이 원래 값 그대로입니다.
4. 설정에서 Low를 고르면 후처리가 사라지고, Frame Debugger/Stats에서 해상도가 줄어든 것을 확인할 수 있습니다. 재시작해도 선택이 유지됩니다.

## 흔한 실수

1. **Volume을 설정했는데 화면에 아무 변화가 없음** → 카메라의 Post Processing 체크가 꺼져 있거나, 오버라이드 속성 왼쪽 체크박스를 켜지 않음 → 카메라 Rendering 섹션과 각 속성의 override 체크를 확인합니다.
2. **Bloom이 화면 전체를 뿌옇게 만들거나 반대로 전혀 빛나지 않음** → HDR이 꺼진 상태에서 Threshold를 낮춰서 흰색 전부가 번짐, 또는 HDR은 켰지만 1.0을 넘는 색이 없음 → HDR 켜고 Threshold 1 근처, 빛날 대상만 HDR 머티리얼 색(14장)을 씁니다.
3. **아틀라스를 만들었는데 Batches가 그대로** → 스프라이트마다 다른 머티리얼·MaterialPropertyBlock, 또는 Order in Layer가 제각각이라 다른 텍스처와 섞임, 또는 아틀라스가 여러 페이지 → Frame Debugger의 "can't be batched" 이유를 읽고 하나씩 제거합니다.
4. **Play 모드에서 바꾼 후처리 값이 에셋에 영구 저장됨** → `volume.sharedProfile`을 수정했거나 프로필 에셋을 직접 참조해 수정 → 런타임 변경은 `volume.profile`(복사본)로 합니다.
5. **2D 조명이 일부 스프라이트에 안 먹음** → 해당 스프라이트가 `Sprite-Unlit-Default` 머티리얼이거나, 조명의 Target Sorting Layers에 그 레이어가 빠짐 → 머티리얼과 레이어 목록을 확인합니다.
6. **품질 단계를 바꿨는데 URP 설정이 그대로** → Quality 레벨의 Render Pipeline Asset이 비어 있어 Graphics의 기본 에셋이 계속 쓰임 → 모든 레벨에 에셋을 명시합니다.

## 연습 문제

1. ★☆☆ 레벨업 창(11장)이 열리는 동안 Color Adjustments의 Saturation을 -60으로 낮춰 게임 화면을 흑백에 가깝게 만들고, 닫히면 원래대로 돌리세요.

<details><summary>힌트·해설</summary>

`HitVignette`와 같은 방식으로 `volume.profile.TryGet(out ColorAdjustments ca)`를 얻고, `ca.saturation.overrideState = true` 후 값을 바꿉니다. 레벨업 중에는 timeScale이 0이므로 보간은 `unscaledDeltaTime`으로 합니다. 04장 LevelUp 상태의 Enter/Exit에서 켜고 끄는 메서드를 호출하면 됩니다. Overlay 캔버스인 레벨업 창 자체는 후처리 영향을 받지 않아 카드가 선명하게 남습니다.

</details>

2. ★★☆ 적 300마리 상황에서 (a) Sorting Layer만 분리, (b) 아틀라스만 적용, (c) 둘 다 적용했을 때의 Batches와 SetPass calls를 표로 측정하고, 결과가 개념 절의 예측과 어디서 다른지 설명하세요.

<details><summary>힌트·해설</summary>

측정은 같은 시드·같은 시점(예: 적 수가 300에 도달한 직후)에서 Play 모드로 합니다. 예측과 다른 부분은 대개 투사체·데미지 숫자·파티클이 레이어 사이에 끼어들거나, TextMeshPro가 별도 머티리얼을 쓰거나, 아틀라스 페이지가 나뉘었기 때문입니다. Frame Debugger의 이유 문구를 표의 비고란에 적어두면 18장 최적화의 기초 자료가 됩니다.

</details>

3. ★★☆ 게임 시간이 8분을 넘으면(최종 웨이브) Global Light 2D의 색을 남색에서 붉은색으로 30초에 걸쳐 바꾸세요.

<details><summary>힌트·해설</summary>

`UnityEngine.Rendering.Universal.Light2D`의 `color`는 `Color`, `intensity`는 `float`이므로 각각 `Color.Lerp`와 `Mathf.Lerp`로 보간합니다. 경과 시간은 11장 `HudPresenter`가 표시하는 것과 같은 04장 `PlayingState.ElapsedTime`(공개 프로퍼티)을 씁니다. 따로 시간을 누적하면 결과 화면·HUD와 어긋납니다.

```csharp
// Assets/_CoinRush/Scripts/Rendering/FinalWaveLight.cs
using UnityEngine;
using UnityEngine.Rendering.Universal;

public class FinalWaveLight : MonoBehaviour
{
    [SerializeField] private Light2D globalLight;
    [SerializeField] private GameStateMachine stateMachine;       // 04장
    [SerializeField] private float startSeconds = 480f;           // 8분
    [SerializeField] private float blendSeconds = 30f;
    [SerializeField] private Color finalColor = new Color(0.75f, 0.25f, 0.25f);
    [SerializeField] private float finalIntensity = 0.45f;

    private Color baseColor;
    private float baseIntensity;
    private float lastT = -1f;

    private void Awake()
    {
        baseColor = globalLight.color;
        baseIntensity = globalLight.intensity;
    }

    private void Update()
    {
        if (stateMachine.Playing == null) return;
        float t = Mathf.Clamp01((stateMachine.Playing.ElapsedTime - startSeconds) / blendSeconds);
        if (Mathf.Approximately(t, lastT)) return;                 // 변화 없으면 대입 생략
        lastT = t;

        globalLight.color = Color.Lerp(baseColor, finalColor, t);        // Color → Color.Lerp
        globalLight.intensity = Mathf.Lerp(baseIntensity, finalIntensity, t);   // float → Mathf.Lerp
    }
}
```

`GameSystems`에 붙이고 Global Light 2D와 `GameStateMachine`을 연결합니다. 테스트할 때는 Start Seconds를 5로 줄이세요. 조명 색 변경은 추가 드로우 콜을 만들지 않는 매우 싼 분위기 연출입니다.

</details>

4. ★★★ 기기 성능을 자동 감지해 첫 실행 시 품질 단계를 고르는 기능을 설계·구현하세요. **측정 조건을 고정**한 상태(목표 60fps, VSync 끔)에서 대표 전투 부하(적 300마리 수준) 10초의 평균 프레임 시간이 목표(16.7ms)에 허용 오차를 더한 값을 넘으면 Low로 내리고, 사용자가 설정에서 직접 고른 값은 자동 감지가 덮어쓰지 않아야 합니다.

<details><summary>힌트·해설</summary>

`SaveData`에 `graphicsQualityUserSet`(bool)을 두어 사용자가 고른 경우 자동 감지를 건너뜁니다.

**프레임 제한부터 확인**하세요. 모바일에서 `Application.targetFrameRate`가 기본값(-1)이면 30fps로 제한되므로, 아무리 빠른 기기도 프레임 시간이 약 33.3ms로 측정되어 전부 Low로 오판합니다. 측정 동안 `QualitySettings.vSyncCount = 0`, `Application.targetFrameRate = 60`으로 두고, 측정이 끝나면 게임의 원래 설정으로 되돌립니다. 이렇게 해도 "기다린 시간"이 섞일 수 있으므로 판정은 "목표보다 빠른가"가 아니라 "목표를 **못 맞추는가**"로 합니다.

측정은 `Time.unscaledDeltaTime`을 누적하되 로딩 직후 첫 몇 프레임은 제외하고, 적이 거의 없는 타이틀이 아니라 **대표 전투 부하**(예: 적 300마리가 나온 뒤)에서 합니다. 판정은 허용 오차를 둡니다(예: 평균 > 18.5ms 또는 느린 프레임 비율 > 10%일 때만 Low). 경계 근처 기기가 판마다 High/Low를 오가지 않도록, Low로 내린 뒤 다음 실행에서 한 번 더 재측정해 두 번 연속 느릴 때만 확정하는 식의 재측정 규칙도 둡니다. `SystemInfo.systemMemorySize`, `SystemInfo.graphicsMemorySize` 같은 정적 정보로 1차 추정 후 실측으로 보정하는 2단계 방식도 좋습니다. 18장에서 이 기능을 Profiler 데이터와 함께 다시 다듬습니다.

</details>

## 셀프 체크

1. URP Asset과 Renderer Data가 각각 담당하는 것을 구분하고, 품질 단계를 나눌 때 어느 쪽을 복제하는지 설명해보세요.

<details><summary>모범 답안</summary>

URP Asset은 HDR, Render Scale, MSAA, 그림자 같은 "얼마나 좋게 그릴지"의 품질 수치를 담고, Renderer Data(2D Renderer Data)는 조명 블렌드 스타일과 Renderer Feature 같은 "어떻게 그릴지"를 담습니다. 품질 단계는 Quality 레벨마다 URP Asset을 지정할 수 있으므로 URP Asset을 복제해 수치를 다르게 하고, 그리는 방식이 같다면 Renderer Data는 공유합니다.

</details>

2. 적과 코인이 같은 Sorting Layer·Order에 섞여 있을 때 드로우 콜이 폭증하는 이유와 두 가지 해결책을 설명해보세요.

<details><summary>모범 답안</summary>

스프라이트 배칭은 같은 머티리얼·같은 텍스처가 그리는 순서상 연속일 때만 묶입니다. 같은 레이어·순서에서는 카메라 거리 등으로 정렬되어 적 텍스처와 코인 텍스처가 번갈아 나오므로 매번 배치가 끊깁니다. 해결책은 Sorting Layer를 분리해 같은 텍스처끼리 연속되게 하는 것과, 스프라이트 아틀라스로 두 스프라이트가 같은 텍스처를 쓰게 하는 것입니다.

</details>

3. Bloom Threshold를 1로 두었을 때 특정 오브젝트만 빛나게 하려면 무엇이 필요한지 HDR 개념으로 설명해보세요.

<details><summary>모범 답안</summary>

URP Bloom의 Threshold는 soft knee(폭 = Threshold의 절반)가 있는 부드러운 경계라, Threshold 1이어도 밝기 0.5~1.0 픽셀이 조금 번지고 순백(1.0)은 약 12.5% 기여합니다. LDR 버퍼는 색이 1.0에서 잘리므로 발광시키고 싶은 오브젝트도 순백과 똑같은 정도로만 번져 "이것만 빛남"을 만들 수 없습니다. URP Asset에서 HDR을 켜 1.0 초과 값을 보관할 수 있게 하고, 빛날 오브젝트의 머티리얼에 1.0보다 크게 넘는 HDR 색을 출력하게 해야 그 픽셀만 확연히 강하게 번집니다. SpriteRenderer의 Color는 8비트라 1.0을 넘길 수 없어 머티리얼 속성으로 전달합니다.

</details>

4. 런타임에 Vignette를 바꿀 때 `volume.profile`을 쓰고 `sharedProfile`을 쓰지 않는 이유는 무엇인가요?

<details><summary>모범 답안</summary>

`profile`은 첫 접근 시 프로필 에셋의 복사본을 만들어 그 Volume에만 적용하므로, 런타임 변경이 에셋에 남지 않습니다. `sharedProfile`은 에셋 자체라서 에디터 Play 모드에서 수정하면 종료 후에도 값이 저장되어 버리고, 같은 프로필을 쓰는 다른 Volume에도 영향을 줍니다. `renderer.material`과 `sharedMaterial`의 관계와 같습니다.

</details>

5. Frame Debugger에서 배칭 문제를 찾는 절차를 순서대로 말해보세요.

<details><summary>모범 답안</summary>

Play 중 Window → Analysis → Frame Debugger를 켜서 프레임을 멈춥니다. 왼쪽 이벤트 목록에서 2D 렌더 패스를 펼쳐 드로우 콜 수를 확인하고, 슬라이더로 각 호출에서 무엇이 그려지는지 Game 뷰로 봅니다. 배치가 끊긴 호출을 선택해 오른쪽의 "can't be batched with the previous one" 이유(다른 텍스처, 다른 머티리얼, MaterialPropertyBlock 등)를 읽고, 그 원인을 Sorting Layer·아틀라스·머티리얼 공유로 제거한 뒤 다시 측정합니다.

</details>

## 핵심 요약

- 렌더 파이프라인은 컬링 → 정렬 → (2D 조명) → 그리기 → 후처리 → UI 순서의 공정이며, 1인 2D 게임은 URP + 2D Renderer가 기본입니다.
- URP Asset은 "얼마나 좋게", Renderer Data는 "어떻게"를 담당하고, 품질 단계마다 URP Asset을 분리합니다.
- 스프라이트 배칭은 같은 머티리얼·텍스처가 연속일 때 성립합니다. Sorting Layer 정리와 스프라이트 아틀라스로 연속성을 만듭니다.
- 배칭 문제는 추측하지 말고 Frame Debugger의 "can't be batched" 이유로 진단합니다.
- 2D 조명은 Global로 어둡게 깔고 Spot으로 포인트를 주되, 대량 오브젝트에는 조명 대신 발광 스프라이트 + Bloom을 씁니다.
- 후처리는 카메라 Post Processing 체크 + Global Volume이 필요합니다. Bloom Threshold는 soft knee가 있어 1.0 근처도 조금 번지므로, 선택적 Bloom에는 HDR과 1.0을 크게 넘는 머티리얼 색이 필요합니다.
- 런타임 후처리 변경은 `volume.profile`(복사본)로, 연출 시간은 `unscaledDeltaTime`으로 합니다.

## 더 읽을거리

- Unity Manual — Universal Render Pipeline 패키지 문서: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/index.html
- URP 문서 — 2D Renderer와 2D Lights (위 패키지 문서의 "2D graphics features" 항목)
- Unity Manual — Frame Debugger: https://docs.unity3d.com/Manual/FrameDebugger.html
- Unity Manual — Sprite Atlas: https://docs.unity3d.com/Manual/sprite-atlas.html
- Unity e-book — "Introduction to the Universal Render Pipeline for advanced Unity creators" (Unity 공식 전자책, 제목으로 검색)
