# 15. HLSL 쉐이더 입문

> **이 장에서 배울 것**
> - URP에서 Shader Graph 대신 코드 셰이더를 쓰는 경우를 판단할 수 있다
> - ShaderLab 구조(Properties/SubShader/Tags/Pass)와 URP HLSL의 기본 틀(`Core.hlsl`, `Attributes`/`Varyings`, `TransformObjectToHClip`)을 설명할 수 있다
> - `TEXTURE2D`/`SAMPLER`/`SAMPLE_TEXTURE2D` 매크로와 `CBUFFER_START(UnityPerMaterial)`로 SRP Batcher 호환 셰이더를 작성한다
> - 스프라이트용 투명 블렌딩·정점 색·precision·키워드 변형을 이해하고 변형 폭발을 피한다
> - 14장의 피격 번쩍임+외곽선과 정점 셰이더 기반 풀 흔들림을 완전한 `.shader` 파일로 구현한다
>
> **선수 장**: 13, 14 · **예상 시간**: 4~5시간 · **코인 러시 진행**: 비교용 실험 씬의 코드 적 셰이더(번쩍임+선택적 외곽선), 바람에 흔들리는 풀 장식(본 게임 적용). 본 게임의 적은 14장 Shader Graph(조명·디졸브)를 그대로 씁니다

## 왜 필요한가

14장에서 Shader Graph로 효과 네 개를 만들었습니다. 충분히 쓸 만하지만, 프로젝트가 커지면 이런 순간이 옵니다.

- 외곽선 그래프를 열었더니 노드 40개가 선으로 얽혀 있고, git diff는 수천 줄의 JSON이라 무엇이 바뀌었는지 리뷰할 수 없습니다.
- 에셋 스토어에서 산 효과, 인터넷의 셰이더 예제, 15년 치 자료가 대부분 **코드**로 되어 있어 읽지 못합니다.
- 블렌딩 모드·스텐실·패스 구성을 세밀하게 바꾸거나, 변형(variant) 수를 정확히 통제하고 싶은데 그래프 설정만으로는 어렵습니다.
- 18장에서 셰이더 비용을 줄이려면 생성된 코드가 실제로 무슨 일을 하는지 알아야 합니다.

Shader Graph도 결국 HLSL 코드를 생성합니다. 이 장의 목표는 "셰이더 전문가"가 아니라, **URP 셰이더 파일을 읽고, 14장 수준의 효과를 직접 쓸 수 있는 것**입니다.

| 상황 | Shader Graph | HLSL 코드 |
|---|---|---|
| 빠른 시각적 실험, 아티스트와 협업 | 적합 | 느림 |
| 조명 모델(Sprite Lit)과 통합 | 쉬움 | 2D 조명 include를 직접 다뤄야 함 |
| 블렌딩·스텐실·다중 패스 세밀 제어 | 제한적 | 자유 |
| 변형 수 통제, 코드 리뷰, 외부 예제 이식 | 어려움 | 적합 |
| Renderer Feature의 전체 화면 패스(16장 이후) | 가능(Fullscreen 타깃) | 적합 |

## 개념

### ShaderLab 파일의 뼈대

Unity 셰이더 파일(`.shader`)은 **ShaderLab**이라는 선언 언어 안에 **HLSL** 코드를 넣은 구조입니다.

```
Shader "CoinRush/이름"                      ← 머티리얼의 Shader 드롭다운에 보이는 경로
{
    Properties { ... }                       ← 머티리얼 Inspector에 노출할 값 (Blackboard에 해당)
    SubShader                                ← 파이프라인/하드웨어별 구현. 위에서부터 지원되는 첫 번째 사용
    {
        Tags { "RenderPipeline" = "UniversalPipeline" ... }   ← 이 SubShader는 URP용
        Blend / ZWrite / Cull ...            ← 렌더 상태 (여기 두면 모든 Pass에 적용)
        Pass                                 ← 한 번의 그리기. 여러 개면 여러 번 그림
        {
            Tags { "LightMode" = "..." }     ← 이 Pass를 어느 렌더링 단계에서 쓸지
            HLSLPROGRAM
            #pragma vertex vert              ← 정점 셰이더 함수 이름
            #pragma fragment frag            ← 프래그먼트 셰이더 함수 이름
            ... HLSL 코드 ...
            ENDHLSL
        }
    }
}
```

`Properties`의 문법은 `_이름 ("표시 이름", 타입) = 기본값`입니다.

| 타입 | 예 | HLSL 쪽 선언 |
|---|---|---|
| `2D` | `_MainTex ("Texture", 2D) = "white" {}` | `TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);` |
| `Color` | `_FlashColor ("Flash", Color) = (1,1,1,1)` | `half4 _FlashColor;` |
| `Float` / `Range(min,max)` | `_FlashAmount ("Amount", Range(0,1)) = 0` | `half _FlashAmount;` |
| `Vector` | `_Speed ("Speed", Vector) = (1,0,0,0)` | `float4 _Speed;` |

속성 앞의 대괄호는 **속성 특성(attribute)** 입니다. `[HDR]`은 HDR 색 선택기, `[MainTexture]`는 주 텍스처 표시, `[Toggle(_KEYWORD)]`는 체크박스로 키워드를 켜고 끕니다.

### Tags — 큐와 LightMode

SubShader Tags:

- `"RenderPipeline" = "UniversalPipeline"`: URP에서만 이 SubShader를 사용.
- `"Queue" = "Transparent"`: 그리는 순서 그룹. 투명 오브젝트는 불투명 뒤에 그립니다. 2D 스프라이트는 기본적으로 투명 큐입니다.
- `"RenderType" = "Transparent"`: 셰이더 분류용 태그(교체 셰이더·일부 기능에서 참조).

Pass Tags의 `"LightMode"`는 렌더러가 **어떤 Pass를 골라 그릴지** 정하는 이름입니다. URP의 Universal(3D) 렌더러는 `UniversalForward` 등을, 2D Renderer는 `Universal2D` 등을 찾습니다. **LightMode 태그가 없는 Pass는 `SRPDefaultUnlit`으로 취급**되며 두 렌더러 모두 그립니다. 이 장의 셰이더는 조명을 받지 않는 Unlit이므로 LightMode를 생략합니다. (2D 조명을 받는 코드 셰이더는 2D Renderer 전용 include와 라이트 텍스처 샘플링이 필요해 입문 범위를 넘습니다. 그런 경우는 Shader Graph의 Sprite Lit/Custom Lit을 권합니다.)

### URP HLSL의 기본 틀

Unity 공식 문서의 "Writing custom shaders" 예제(`URPUnlitShaderBasic`)와 같은 형태입니다.

```hlsl
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
// ↑ 좌표 변환 함수, 텍스처 매크로, 행렬·시간 같은 내장 변수 정의를 가져옴

struct Attributes                  // 정점 셰이더 입력: 메시 정점 데이터
{
    float4 positionOS : POSITION;  // OS = Object Space. ": POSITION"은 시맨틱(어느 데이터인지)
    float2 uv         : TEXCOORD0;
    half4  color      : COLOR;     // 정점 색 = SpriteRenderer.color
};

struct Varyings                    // 정점 → 프래그먼트로 전달 (래스터화 때 픽셀별로 보간됨)
{
    float4 positionHCS : SV_POSITION;   // HCS = Homogeneous Clip Space. 반드시 필요
    float2 uv          : TEXCOORD0;
    half4  color       : COLOR;
};

Varyings vert(Attributes IN)
{
    Varyings OUT;
    OUT.positionHCS = TransformObjectToHClip(IN.positionOS.xyz);
    OUT.uv = IN.uv;
    OUT.color = IN.color;
    return OUT;
}

half4 frag(Varyings IN) : SV_Target     // SV_Target = 렌더 타깃에 쓸 색
{
    return IN.color;
}
```

JS 비유로는 `vert`가 `map`의 1단계 변환, `Varyings`가 1단계 → 2단계로 넘기는 객체, `frag`가 최종 `map`입니다. 차이는 Varyings의 값이 **삼각형 위에서 자동 보간**된다는 점입니다. 왼쪽 정점 UV가 0, 오른쪽이 1이면 가운데 픽셀은 0.5를 받습니다.

### 좌표 공간 변환

```
Object Space (OS)   스프라이트 자신의 로컬 좌표. 피벗이 원점
   │ TransformObjectToWorld(positionOS)        ← unity_ObjectToWorld 행렬 (Transform의 위치·회전·스케일)
   ▼
World Space (WS)    씬 좌표. 여러 오브젝트가 공유
   │ TransformWorldToView(positionWS)           ← 카메라 기준
   ▼
View Space (VS)     카메라가 원점
   │ (투영 행렬)
   ▼
Homogeneous Clip Space (HCS)   GPU가 화면 영역 판정·원근 나눗셈에 쓰는 좌표

TransformObjectToHClip(p)  = OS → HCS 한 번에
TransformWorldToHClip(p)   = WS → HCS
GetVertexPositionInputs(p) = 위 공간들을 구조체(positionWS, positionVS, positionCS)로 한꺼번에
```

바람에 흔들리는 풀처럼 **여러 오브젝트가 월드 기준으로 일관되게** 움직여야 하는 효과는 World Space에서 위치를 바꾼 뒤 `TransformWorldToHClip`으로 넘깁니다.

> 스프라이트는 배칭될 때 CPU에서 정점을 미리 월드 좌표로 변환해 합치므로, 셰이더가 받는 "Object Space"가 사실상 월드 좌표이고 오브젝트 행렬은 단위 행렬일 수 있습니다. `TransformObjectToWorld`를 거쳐 월드 좌표로 계산하면 배칭 여부와 관계없이 같은 결과가 나옵니다.

### 텍스처 매크로

URP는 플랫폼마다 다른 텍스처 문법(DX11, Metal, Vulkan, GLES)을 매크로로 감쌉니다. 옛 Built-in 예제의 `sampler2D` + `tex2D`를 그대로 쓰지 말고 이 형태를 씁니다.

```hlsl
TEXTURE2D(_MainTex);                 // 텍스처 오브젝트 선언
SAMPLER(sampler_MainTex);            // 샘플러 선언: "sampler" + 텍스처 이름 → 텍스처의 Filter/Wrap 설정을 따름

half4 c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv);   // 읽기
```

`_MainTex_TexelSize`(`float4`)를 선언하면 Unity가 `(1/너비, 1/높이, 너비, 높이)`를 채워줍니다. 14장 Texel Size 노드의 정체입니다.

### CBUFFER와 SRP Batcher

SRP Batcher는 머티리얼 속성을 GPU의 **상수 버퍼(Constant Buffer)** 에 모아 두고, 같은 셰이더 변형끼리는 버퍼만 바꿔 끼우며 그립니다. 그러려면 셰이더가 규칙을 지켜야 합니다.

```hlsl
CBUFFER_START(UnityPerMaterial)      // 머티리얼 속성은 모두 이 이름의 버퍼 하나에
    float4 _MainTex_TexelSize;
    half4  _FlashColor;
    half   _FlashAmount;
CBUFFER_END
// 텍스처(TEXTURE2D)와 샘플러는 CBUFFER 밖에 선언
// 엔진 내장 변수(unity_ObjectToWorld 등)는 Core.hlsl이 UnityPerDraw 버퍼에 이미 선언
```

셰이더 에셋을 선택하면 Inspector에 **SRP Batcher: compatible / not compatible**과 이유가 표시됩니다. 속성 하나를 CBUFFER 밖에 선언하면 "not compatible"이 됩니다. 13장에서 본 것처럼 SpriteRenderer의 배칭은 별도 경로를 탈 수 있지만, 같은 셰이더를 메시·타일맵에 쓰는 순간 이 규칙이 성능을 좌우하므로 **항상 지키는 습관**을 들입니다.

### 스프라이트용 렌더 상태와 정점 색

```
Blend SrcAlpha OneMinusSrcAlpha   최종 = 새 색 × 새 알파 + 기존 화면 색 × (1 − 새 알파)   일반 반투명
Blend One OneMinusSrcAlpha        미리 곱한 알파(premultiplied)일 때
Blend One One                     더하기 — 불꽃·빛 (검은색은 투명처럼 보임)
ZWrite Off                        깊이 버퍼에 쓰지 않음. 투명 오브젝트는 정렬 순서로 앞뒤 결정
Cull Off                          뒷면도 그림. SpriteRenderer의 Flip이나 음수 스케일에서 사라지지 않게
```

정점 색 `IN.color`는 SpriteRenderer의 Color입니다. 기본 스프라이트 셰이더처럼 **텍스처 색에 곱해야** Color와 알파 페이드가 동작합니다.

> **이 장의 셰이더는 최소 구현입니다.** Unity 6(URP 17)의 공식 스프라이트 셰이더(`Sprite-Unlit-Default`)는 정점 색 외에 `unity_SpriteColor`(렌더러 색)를 곱하고, `unity_SpriteProps`로 Flip을 정점에 적용하며(`UnityFlipSprite`), `UNITY_SETUP_INSTANCE_ID`·`SetUpSpriteInstanceProperties()`로 인스턴싱 경로를 처리합니다. 스프라이트가 동적 배칭으로 그려질 때는 색·Flip이 정점에 이미 구워져 이 장의 코드로 충분하지만, 배칭·인스턴싱 경로가 달라지면 Color나 Flip이 빠질 가능성이 있습니다(패치 버전과 설정에 따라 다름). 그래서 실습마다 **Color·알파·Flip X를 배칭이 되는 상황(같은 머티리얼 여러 개)과 단독 상황 양쪽에서** 확인하고, 빠지는 경로가 있으면 설치된 URP 패키지의 `Shaders/2D/Sprite-Unlit-Default.shader`를 열어 그 정점 함수의 처리를 옮겨 오세요.

### precision — float, half

| 타입 | 정밀도 | 쓰는 곳 |
|---|---|---|
| `float` | 32비트 | 위치, UV, 시간(`_Time`), 큰 월드 좌표 |
| `half` | 모바일 GPU에서 16비트(±약 6만, 소수 약 3자리) / PC에서는 보통 float과 동일 | 색, 알파, 0~1 계수 |
| `real` | URP 정의 타입. 플랫폼 설정에 따라 half 또는 float | 라이브러리 함수와 맞출 때 |

모바일에서 `half`는 메모리 대역폭과 연산을 줄여줍니다. 하지만 `_Time.y`(게임 시작 후 초)를 `half`로 받으면 몇 분 뒤 정밀도가 부족해 애니메이션이 뚝뚝 끊깁니다. **색은 half, 위치·UV·시간은 float**을 기본으로 합니다.

### 분기와 키워드 — 변형 폭발

셰이더 안의 `if`는 GPU에서 양쪽을 다 계산한 뒤 고르거나 파이프라인을 멈추게 할 수 있어 비쌀 수 있습니다. 기능을 켜고 끄는 대표적인 방법은 **키워드로 셰이더를 여러 벌 컴파일(변형, variant)** 하는 것입니다.

```hlsl
#pragma shader_feature_local _OUTLINE_ON      // 머티리얼에서 쓰는 조합만 빌드에 포함
#pragma multi_compile_local _ _FOG_ON         // 모든 조합을 항상 빌드에 포함 ("_"는 키워드 없음 상태)

#if defined(_OUTLINE_ON)
    // 외곽선 코드 — 이 키워드가 꺼진 변형에는 아예 존재하지 않음
#endif
```

| 지시어 | 빌드 포함 | 런타임에 C#으로 켜기 | 쓰임 |
|---|---|---|---|
| `shader_feature(_local)` | **빌드에 포함되는** 머티리얼(빌드 씬·Resources·Addressables 등에서 참조)이 쓰는 조합만. 프로젝트 폴더에 있기만 한 머티리얼은 기준이 아님 | 빌드에 없는 조합이면 동작하지 않음 | 머티리얼마다 고정된 옵션(엘리트 외곽선) |
| `multi_compile(_local)` | 선언한 모든 조합(단, 스트리핑 설정·스크립트로 제거될 수 있음) | 포함된 조합이면 가능 | 게임 중 전역으로 바뀌는 옵션(품질 설정) |
| `dynamic_branch` | 변형을 만들지 않고 GPU에서 분기 | 가능 | 변형 수를 늘리기 싫고 분기 비용이 작을 때 |

**변형 폭발**: 키워드 세트는 곱으로 늘어납니다.

```
multi_compile  _ _A          → 2
multi_compile  _ _B          → 2
multi_compile  _LOW _MID _HIGH → 3
= 2 × 2 × 3 = 12 변형 × Pass 수 × 그래픽스 API 수
→ 빌드 시간·빌드 크기·셰이더 로딩 시간·메모리 증가
```

`_local` 접미사는 키워드를 이 셰이더 안에서만 쓰는 로컬 키워드로 만들어 전역 키워드 한도를 소모하지 않습니다. 원칙은 **키워드는 정말 필요한 것만, 가능하면 shader_feature_local**입니다. 빌드에 포함된 변형은 빌드 로그와 18장의 도구로 확인합니다.

## 실습: 코인 러시에 적용하기

앞 장의 최소 시그니처: 14장 `HitFlash`(속성 `_FlashAmount`, `_FlashColor`를 MaterialPropertyBlock으로 설정). 파일은 `Assets/_CoinRush/Shaders/`에 둡니다.

**누적 프로젝트 보호 원칙**: 이 장의 적 셰이더는 Unlit이고 디졸브가 없습니다. 본 게임의 적 프리팹에 지정하면 13장의 2D 조명 반응과 14장의 사망 디졸브가 사라져, 죽은 적이 그대로 보이다가 0.45초 뒤 갑자기 없어집니다. 그래서 1·2단계는 **실험 씬**에서만 하고 적 프리팹의 `M_Enemy`는 건드리지 않습니다. 본 게임에 들어가는 것은 3단계의 풀 흔들림뿐입니다.

실험 씬 준비:

1. `Assets/_CoinRush/Scenes/Lab/`에 새 씬 `Lab_Shaders`를 만듭니다(Universal 2D 템플릿의 기본 씬처럼 Main Camera + Global Light 2D). Build Profile의 Scene List에는 **넣지 않습니다**.
2. 13장과 비교되도록 Global Light 2D를 Intensity 0.35, 짙은 남색으로 둡니다.
3. 적 스프라이트로 SpriteRenderer 오브젝트 세 개를 만듭니다: `Lab_Enemy_Graph`(Material `M_Enemy`), `Lab_Enemy_Code`, `Lab_Elite_Code`(머티리얼은 2단계에서 지정). 셋 다 `Health`(01장)와 `HitFlash`(14장), 아래 테스트 스크립트를 붙입니다.

```csharp
// Assets/_CoinRush/Scripts/Rendering/LabHitTester.cs — 실험 씬 전용
using UnityEngine;

[RequireComponent(typeof(Health))]
public class LabHitTester : MonoBehaviour
{
    [ContextMenu("Hit (1 damage)")]
    private void Hit() => GetComponent<Health>().TakeDamage(1);   // Play 중 컴포넌트 ⋮ 메뉴에서 실행

    [ContextMenu("Refill")]
    private void Refill() { Health h = GetComponent<Health>(); h.Initialize(h.Max); }
}
```

### 1단계 — 가장 작은 URP 스프라이트 셰이더

먼저 텍스처를 그리기만 하는 셰이더로 틀을 확인합니다.

1. `Shaders` 폴더 우클릭 → Create → Shader → **Unlit Shader**로 파일을 만들고 이름을 `SpriteBasic`으로 바꿉니다(생성된 내용은 Built-in용이므로 전부 지웁니다).
2. 아래 내용으로 교체합니다.

```hlsl
// Assets/_CoinRush/Shaders/SpriteBasic.shader
Shader "CoinRush/SpriteBasic"
{
    Properties
    {
        [MainTexture] _MainTex ("Sprite Texture", 2D) = "white" {}
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Transparent"
            "Queue" = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }

        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv         : TEXCOORD0;
                half4  color      : COLOR;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float2 uv          : TEXCOORD0;
                half4  color       : COLOR;
            };

            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);

            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_TexelSize;   // 지금은 안 쓰지만 이후 단계와 CBUFFER 구성을 맞춰 둠
            CBUFFER_END

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionHCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.uv = IN.uv;
                OUT.color = IN.color;
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                return tex * IN.color;       // SpriteRenderer.color 반영
            }
            ENDHLSL
        }
    }
}
```

3. 셰이더 우클릭 → Create → Material → `M_SpriteBasic`. 테스트용 스프라이트 하나에 지정합니다.
4. 확인: 스프라이트가 원래대로 보이고, SpriteRenderer의 Color·알파를 바꾸면 반영됩니다. 셰이더 에셋 Inspector에서 **SRP Batcher: compatible**인지 봅니다.
5. 이 셰이더는 **Unlit**이므로 13장의 2D 조명을 받지 않습니다. 어두운 씬에서 혼자 밝게 보이는 것이 정상입니다.

### 2단계 — 번쩍임 + 외곽선 적 셰이더

14장의 `SG_Enemy`(번쩍임)와 `SG_PickupOutline`(외곽선)을 하나의 코드 셰이더로 합칩니다. 외곽선은 엘리트 적만 쓰도록 `shader_feature_local` 키워드로 분리합니다.

```hlsl
// Assets/_CoinRush/Shaders/SpriteFlashOutline.shader
Shader "CoinRush/SpriteFlashOutline"
{
    Properties
    {
        [MainTexture] _MainTex ("Sprite Texture", 2D) = "white" {}

        [Header(Hit Flash)]
        _FlashColor ("Flash Color", Color) = (1, 1, 1, 1)
        _FlashAmount ("Flash Amount", Range(0, 1)) = 0

        [Header(Outline)]
        [Toggle(_OUTLINE_ON)] _OutlineOn ("Outline Enabled", Float) = 0
        [HDR] _OutlineColor ("Outline Color", Color) = (2, 0.3, 0.2, 1)
        _OutlineThickness ("Outline Thickness (texels)", Range(0, 4)) = 1
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Transparent"
            "Queue" = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }

        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma shader_feature_local _OUTLINE_ON

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv         : TEXCOORD0;
                half4  color      : COLOR;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float2 uv          : TEXCOORD0;
                half4  color       : COLOR;
            };

            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);

            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_TexelSize;
                half4  _FlashColor;
                half   _FlashAmount;
                half4  _OutlineColor;
                float  _OutlineThickness;
            CBUFFER_END

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionHCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.uv = IN.uv;
                OUT.color = IN.color;
                return OUT;
            }

            half SampleAlpha(float2 uv)
            {
                return SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv).a;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                half4 col = tex * IN.color;

                // 1) 피격 번쩍임: Shader Graph의 Lerp와 동일. 알파는 유지
                col.rgb = lerp(col.rgb, _FlashColor.rgb, _FlashAmount);

            #if defined(_OUTLINE_ON)
                // 2) 외곽선: 상하좌우 한(또는 N) 텍셀 옆의 알파 최댓값 − 자기 알파
                float2 texel = _MainTex_TexelSize.xy * _OutlineThickness;   // (1/너비, 1/높이) × 두께
                half neighbor = SampleAlpha(IN.uv + float2(texel.x, 0));
                neighbor = max(neighbor, SampleAlpha(IN.uv - float2(texel.x, 0)));
                neighbor = max(neighbor, SampleAlpha(IN.uv + float2(0, texel.y)));
                neighbor = max(neighbor, SampleAlpha(IN.uv - float2(0, texel.y)));

                half outline = saturate(neighbor - tex.a);
                // 외곽선 픽셀은 SpriteRenderer 알파(페이드)도 따르도록 정점 알파를 곱함
                col.rgb = lerp(col.rgb, _OutlineColor.rgb, outline);
                col.a = max(col.a, outline * _OutlineColor.a * IN.color.a);
            #endif

                return col;
            }
            ENDHLSL
        }
    }
}
```

읽는 요령:

- `SampleAlpha`처럼 **보조 함수**를 만들 수 있습니다. HLSL 함수는 사용하기 전에(위쪽에) 정의해야 합니다.
- `#if defined(_OUTLINE_ON)` 블록은 키워드가 꺼진 변형에는 컴파일되지 않으므로, 일반 적은 텍스처를 1번만 읽습니다(14장 연습 문제 4의 답을 코드로 쓴 것).
- `_MainTex_TexelSize.xy`는 `1/너비, 1/높이`입니다. 14장에서 Texel Size 노드의 Width·Height(픽셀 수)로 나눴던 계산과 같습니다.

에디터 작업:

1. 셰이더에서 머티리얼 두 개를 만듭니다: `M_EnemyCode`(Outline Enabled 끔), `M_EnemyEliteCode`(Outline Enabled 켬, 빨강 HDR).
2. **실험 씬의** `Lab_Enemy_Code`에 `M_EnemyCode`, `Lab_Elite_Code`에 `M_EnemyEliteCode`를 지정합니다. 적 프리팹에는 지정하지 않습니다(위 보호 원칙). 본 게임에 코드 셰이더를 쓰려면 연습 문제 1의 디졸브와 2D 조명(Shader Graph Sprite Lit이 생성한 코드 참고)까지 갖춰야 하며, 그 전까지는 14장 그래프를 유지합니다.
3. 14장 `HitFlash` 컴포넌트는 **수정 없이 그대로** 동작합니다. 속성 이름(`_FlashAmount`, `_FlashColor`)이 같기 때문입니다. 셰이더 구현을 바꿔도 C# 쪽 계약(속성 이름)을 유지하면 코드가 영향을 받지 않는다는 점이 핵심입니다.
4. 외곽선 스프라이트 조건은 14장과 같습니다: Mesh Type Full Rect, 투명 여백, 아틀라스 Padding ≥ 두께.

### 3단계 — 정점 셰이더로 풀 흔들림

지금까지는 프래그먼트만 바꿨습니다. 이번에는 **정점 위치**를 바꿔 풀 장식이 바람에 흔들리게 합니다. 핵심 아이디어:

```
풀 스프라이트 (Full Rect 사각형, 정점 4개)

  uv.y = 1  ●───────●   ← 위쪽 정점: 크게 흔들림
            │  풀   │
  uv.y = 0  ●───────●   ← 아래쪽 정점: 땅에 고정 (흔들림 0)

offset.x = sin(시간 × 속도 + 월드X × 주파수) × 세기 × uv.y
          └ 모든 풀이 같은 시간 함수 ┘  └ 위치마다 위상이 달라 "물결"처럼 전파 ┘
```

```hlsl
// Assets/_CoinRush/Shaders/SpriteGrassSway.shader
Shader "CoinRush/SpriteGrassSway"
{
    Properties
    {
        [MainTexture] _MainTex ("Sprite Texture", 2D) = "white" {}
        _SwayAmount ("Sway Amount (world units)", Float) = 0.08
        _SwaySpeed ("Sway Speed", Float) = 2.0
        _SwayFrequency ("Sway Frequency (per world unit)", Float) = 0.6
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Transparent"
            "Queue" = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }

        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv         : TEXCOORD0;
                half4  color      : COLOR;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float2 uv          : TEXCOORD0;
                half4  color       : COLOR;
            };

            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);

            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_TexelSize;
                float  _SwayAmount;
                float  _SwaySpeed;
                float  _SwayFrequency;
            CBUFFER_END

            Varyings vert(Attributes IN)
            {
                Varyings OUT;

                // 월드 좌표에서 계산: 배칭(정점이 미리 월드 변환됨) 여부와 무관하게 같은 결과
                float3 positionWS = TransformObjectToWorld(IN.positionOS.xyz);

                // 아래는 고정, 위로 갈수록 많이 흔들림. uv.y는 아틀라스가 아닌 단독 텍스처 기준
                float weight = IN.uv.y;
                weight *= weight;                                  // 휘는 느낌을 위해 제곱

                // _Time.y = 시작 후 경과 초 (float 필수: half면 시간이 지나며 끊김)
                float phase = _Time.y * _SwaySpeed + positionWS.x * _SwayFrequency;
                positionWS.x += sin(phase) * _SwayAmount * weight;

                OUT.positionHCS = TransformWorldToHClip(positionWS);
                OUT.uv = IN.uv;
                OUT.color = IN.color;
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                return tex * IN.color;
            }
            ENDHLSL
        }
    }
}
```

에디터 작업:

1. 풀 스프라이트 임포트: **Mesh Type `Full Rect`**, **아틀라스에 넣지 않음**(uv.y가 0~1이어야 가중치가 맞음), Pivot `Bottom`.
2. 머티리얼 `M_GrassSway`를 만들어 풀 스프라이트에 지정하고, Sorting Layer `Background`에 여러 개를 흩어 배치합니다.
3. 흔들림이 스프라이트 사각형 밖으로 나가면 잘리지 않지만, **컬링은 원래 바운딩 박스 기준**입니다. 화면 가장자리에서 풀 끝이 튀어 사라진다면 `_SwayAmount`를 줄이거나 스프라이트에 여유 여백을 둡니다.

> 풀을 아틀라스에 넣어야 한다면 uv.y 대신 "정점의 로컬 높이"로 가중치를 계산해야 하지만, 배칭 시 로컬 좌표를 잃는 문제가 있어 입문 단계에서는 아틀라스 제외가 가장 단순합니다.

### 확인하기

1. `M_SpriteBasic`을 쓴 스프라이트가 기본 스프라이트와 똑같이 보이고, SpriteRenderer Color가 반영됩니다.
2. 실험 씬에서 Play 후 각 오브젝트의 `LabHitTester` ⋮ 메뉴에서 Refill을 한 번 실행하고(HitFlash가 기준 체력을 알게 함) Hit을 실행하면 세 오브젝트 모두 번쩍입니다(C# 수정 없음). `Lab_Enemy_Graph`는 조명에 어둡게 눌린 채 밝아지고, Unlit인 두 코드 셰이더는 조명과 무관하게 밝게 그려지는 차이를 확인합니다. `Lab_Elite_Code`만 빨간 외곽선이 있고, 외곽선도 번쩍임 동안 유지됩니다.
   - **정점 색 경로 확인**: `Lab_Enemy_Code`를 Ctrl+D로 10개 복제해 겹쳐 둔 상태(배칭)와 1개만 남긴 상태에서 각각 SpriteRenderer Color를 빨강·알파 0.5로, Flip X를 켜 봅니다. 두 상태 모두 색·반투명·좌우 반전이 반영되어야 합니다.
   - 본 게임 씬의 적은 여전히 조명을 받고 죽을 때 디졸브됩니다(프리팹 머티리얼을 바꾸지 않았는지 확인).
3. 두 셰이더 에셋의 Inspector에 **SRP Batcher: compatible**이 표시됩니다.
4. 풀들이 아래는 고정된 채 위쪽만 흔들리고, 왼쪽에서 오른쪽으로 물결이 지나가듯 위상이 조금씩 어긋납니다.
5. `M_EnemyEliteCode`의 Outline Enabled를 끄면 외곽선이 사라지고, 셰이더 Inspector의 키워드 목록(또는 머티리얼 디버그 Inspector)에서 `_OUTLINE_ON`이 꺼진 것을 확인할 수 있습니다.

## 흔한 실수

1. **머티리얼이 분홍색(마젠타)** → 셰이더 컴파일 오류, 또는 Built-in 템플릿(`UnityCG.cginc`, `CGPROGRAM`)을 URP 프로젝트에서 그대로 사용 → 셰이더 에셋 Inspector의 오류 메시지를 읽고, `HLSLPROGRAM` + URP `Core.hlsl` include 형태로 바꿉니다.
2. **스프라이트가 사각형 배경과 함께 불투명하게 그려짐** → `Blend SrcAlpha OneMinusSrcAlpha`와 투명 큐 태그 누락 → SubShader에 Blend·ZWrite Off·Queue Transparent를 넣습니다.
3. **SpriteRenderer의 Color·알파 페이드가 먹지 않음** → `Attributes`에 `COLOR` 시맨틱이 없거나 프래그먼트에서 정점 색을 곱하지 않음 → `half4 color : COLOR`를 전달하고 `tex * IN.color`로 곱합니다.
4. **Inspector에 SRP Batcher: not compatible** → 머티리얼 속성이 `CBUFFER_START(UnityPerMaterial)` 밖에 선언되었거나, Pass마다 CBUFFER 구성이 다름 → 모든 머티리얼 속성을 하나의 UnityPerMaterial 버퍼에, 모든 Pass에서 같은 구성으로 선언합니다.
5. **외곽선 두께가 스프라이트마다 다르거나 0처럼 보임** → `_MainTex_TexelSize`가 기대와 다른 텍스처(예: 아틀라스 전체) 기준이거나 값이 들어오지 않음 → 아틀라스 사용 시 아틀라스 해상도 기준 두께임을 감안하고, 값이 0이면 `_MainTex_TexelSize`가 CBUFFER에 선언되어 있는지 확인합니다. 해결되지 않으면 C#에서 텍셀 크기를 별도 속성으로 전달합니다.
6. **빌드에서만 외곽선이 안 나옴** → `shader_feature_local` 키워드를 C#에서 런타임에 켰는데, 그 조합을 쓰는 머티리얼이 **빌드에 포함되지 않아** 변형이 제외됨. 프로젝트 폴더에 머티리얼 에셋이 있는 것만으로는 부족하고, 빌드 씬의 프리팹·Resources·Addressables 등이 실제로 참조해야 함 → 키워드를 켠 머티리얼을 빌드되는 프리팹이 참조하게 하거나, Shader Variant Collection에 변형을 등록해 Graphics 설정의 Preloaded Shaders 등으로 포함시키거나, 런타임 전환이 필요하면 `multi_compile_local`로 바꿉니다(이 경우에도 스트리핑 설정을 확인). 어느 쪽이든 **실제 빌드에서 키워드를 켜고 끄며** 확인합니다.

## 연습 문제

1. ★☆☆ `SpriteFlashOutline.shader`에 14장의 디졸브(`_Dissolve`, `_EdgeWidth`, `[HDR] _EdgeColor`)를 추가하세요. 노이즈는 노이즈 텍스처(`_NoiseTex`)를 샘플링하는 방식으로 합니다.

<details><summary>힌트·해설</summary>

`TEXTURE2D(_NoiseTex); SAMPLER(sampler_NoiseTex);`를 추가하고 속성 값은 CBUFFER에 넣습니다. 14장과 같은 식을 쓰되, 노이즈를 1 미만으로 제한합니다: `noise = min(SAMPLE_TEXTURE2D(_NoiseTex, sampler_NoiseTex, IN.uv).r, 0.999)`, `burn = _Dissolve * (1 + _EdgeWidth)`, `visible = step(burn - _EdgeWidth, noise)`, `intact = step(burn, noise)`, `edge = visible - intact`, `col.rgb += _EdgeColor.rgb * edge`, `col.a *= visible`. HLSL의 `step(edge, x)`는 `x >= edge ? 1 : 0`이므로, 제한이 없으면 노이즈 텍스처의 순백 텍셀(정확히 1.0)은 `_Dissolve = 1`에서 `step(1, 1) = 1`이 되어 **끝까지 남는 점**이 됩니다. 반례 테스트로 순백 사각형이 섞인 노이즈 텍스처를 만들어 `_Dissolve`를 1로 두고 아무 픽셀도 남지 않는지 확인하세요. Shader Graph의 Simple Noise는 수학 함수로 노이즈를 만들지만, 텍스처 샘플링이 모바일에서 더 싸고 모양을 아티스트가 고를 수 있습니다. 14장 `DissolveEffect` C#은 그대로 동작해야 합니다.

</details>

2. ★★☆ 풀 흔들림에 "플레이어가 지나가면 밀려나는" 효과를 추가하세요. C#에서 플레이어 월드 위치를 전역 셰이더 변수로 넘깁니다.

<details><summary>힌트·해설</summary>

C#에서 `Shader.SetGlobalVector(PlayerPosId, player.position)`을 매 프레임 호출합니다(`PlayerPosId = Shader.PropertyToID("_PlayerPosition")` 캐싱). 셰이더에서는 `float4 _PlayerPosition;`을 **CBUFFER 밖**에 선언합니다(전역 변수는 머티리얼 속성이 아니므로 UnityPerMaterial에 넣지 않음). 정점의 월드 위치와 플레이어 사이 거리 `d`를 구해 `push = saturate(1 - d / radius)`, 방향 `sign(positionWS.x - _PlayerPosition.x)`로 `positionWS.x += dir * push * strength * weight`를 더합니다.

</details>

3. ★★☆ `SpriteFlashOutline`에서 `multi_compile_local _ _OUTLINE_ON`과 `shader_feature_local _OUTLINE_ON`을 각각 사용해 빌드한 뒤, 빌드 로그 또는 Editor.log에서 이 셰이더의 변형 수를 비교하고, 외곽선 머티리얼을 프로젝트에서 모두 지웠을 때 두 방식의 차이를 설명하세요.

<details><summary>힌트·해설</summary>

`multi_compile`은 머티리얼 사용 여부와 무관하게 키워드 on/off 두 변형을 모두 빌드합니다(스트리핑으로 제거하지 않는 한). `shader_feature`는 빌드에 포함되는 머티리얼이 쓰는 조합만 포함하므로, 외곽선 머티리얼을 지우거나 어떤 빌드 콘텐츠도 참조하지 않게 되면 off 변형만 남습니다. 이때 C#에서 `material.EnableKeyword("_OUTLINE_ON")`을 해도 빌드에서는 해당 변형이 없어 외곽선이 나오지 않습니다. 변형 수는 빌드 후 Editor.log의 셰이더 컴파일 요약에서 확인할 수 있습니다(로그 형식은 버전에 따라 다름).

</details>

4. ★★★ 14장의 UV 스크롤 배경을 HLSL로 옮기되, 14장 연습 문제 2처럼 C#이 누적한 오프셋(일시정지 중에도 흐르게, x·y 모두 0~1로 순환)을 받고, 두 장의 텍스처를 서로 다른 속도로 겹쳐 패럴랙스를 셰이더 하나(드로우 콜 하나)로 구현하세요. 구현 후 14장 방식(머티리얼 두 개)과 드로우 콜·픽셀 비용을 비교해 어느 쪽을 택할지 결론을 쓰세요.

<details><summary>힌트·해설</summary>

속성으로 `_FarTex`, `_NearTex`(둘 다 Wrap Mode Repeat), `_FarOffset`, `_NearOffset`(float4)을 두고, 프래그먼트에서 `farUV = uv * _Tiling.xy + _FarOffset.xy`, `nearUV = ...`로 각각 샘플링한 뒤 `lerp(far.rgb, near.rgb, near.a)`로 겹칩니다. 드로우 콜은 하나로 줄지만, 화면 전체 픽셀에서 텍스처를 두 번 읽고 overdraw가 없어지는 대신 셰이더가 약간 무거워집니다. 14장 방식은 두 레이어가 각각 화면을 덮으므로 overdraw가 2배입니다. 모바일에서는 보통 "한 번 그리고 두 번 샘플링"이 "두 번 그리기"보다 유리하지만, 결론은 18장 방식으로 실기기에서 측정해 내리세요.

</details>

## 셀프 체크

1. `Attributes`와 `Varyings` 구조체의 역할 차이를 설명하고, Varyings 값이 프래그먼트 셰이더에 도착할 때 어떤 일이 일어나는지 말해보세요.

<details><summary>모범 답안</summary>

`Attributes`는 메시에서 오는 정점별 입력(위치, UV, 정점 색)이고 정점 셰이더의 매개변수입니다. `Varyings`는 정점 셰이더가 출력해 프래그먼트 셰이더로 넘기는 데이터로, 반드시 `SV_POSITION` 클립 좌표를 포함합니다. 래스터화 단계에서 삼각형 세 정점의 Varyings 값이 픽셀 위치에 따라 보간되어, 각 픽셀의 프래그먼트 셰이더는 보간된 UV·색을 받습니다.

</details>

2. `CBUFFER_START(UnityPerMaterial)`에 무엇을 넣고 무엇을 넣지 않는지, 그리고 그 이유를 SRP Batcher로 설명해보세요.

<details><summary>모범 답안</summary>

머티리얼 속성 중 숫자 값(색, float, vector, `_TexelSize` 등)은 모두 UnityPerMaterial 버퍼 하나에 넣습니다. 텍스처와 샘플러 선언, 그리고 `Shader.SetGlobal…`로 설정하는 전역 변수는 넣지 않습니다. SRP Batcher는 머티리얼 데이터를 이 상수 버퍼 단위로 GPU에 올려두고 같은 셰이더 변형끼리 버퍼만 바꿔 그리기 때문에, 속성이 버퍼 밖에 흩어져 있으면 호환되지 않아 이 최적화를 받지 못합니다.

</details>

3. 스프라이트용 셰이더에 `Blend SrcAlpha OneMinusSrcAlpha`, `ZWrite Off`, `Cull Off`를 각각 두는 이유를 말해보세요.

<details><summary>모범 답안</summary>

Blend 설정은 새 색을 자기 알파만큼, 기존 화면 색을 나머지 비율만큼 섞어 반투명 가장자리를 자연스럽게 합성합니다. `ZWrite Off`는 투명 오브젝트가 깊이 버퍼를 막아 뒤에 그릴 스프라이트가 가려지는 것을 방지하며, 앞뒤는 Sorting Layer·Order 정렬로 정합니다. `Cull Off`는 Flip이나 음수 스케일로 삼각형 감김 방향이 뒤집혀도 스프라이트가 사라지지 않게 합니다.

</details>

4. `_Time.y`를 `half`로 다루면 안 되는 이유와, 색 계산에 `half`를 쓰는 이유를 설명해보세요.

<details><summary>모범 답안</summary>

모바일 GPU에서 `half`는 16비트라 표현 범위와 소수 정밀도가 작습니다. 경과 시간은 계속 커지므로 몇 분만 지나도 인접 값 간 간격이 커져 `sin(time)` 애니메이션이 계단처럼 끊깁니다. 위치·UV·시간은 `float`을 씁니다. 반면 색과 알파는 0~1 범위라 16비트로 충분하고, 모바일에서 연산·대역폭을 줄일 수 있어 `half`가 적합합니다.

</details>

5. `shader_feature_local`과 `multi_compile_local`의 차이를 "빌드에 무엇이 들어가는가"와 "런타임에 켤 수 있는가"로 설명하고, 변형 폭발이 무엇인지 말해보세요.

<details><summary>모범 답안</summary>

`shader_feature_local`은 빌드에 포함되는 머티리얼이 실제로 사용하는 키워드 조합만 빌드에 넣으므로 변형 수가 적지만, 빌드 콘텐츠의 어떤 머티리얼도 쓰지 않은 조합은 런타임에 키워드를 켜도 존재하지 않습니다(프로젝트 폴더에 머티리얼이 있기만 해서는 안 됨). `multi_compile_local`은 선언한 모든 조합을 포함해 런타임 전환에 적합하지만 변형이 늘어나고, 스트리핑 설정으로 제거되지 않았는지는 여전히 빌드에서 확인해야 합니다. 변형 폭발은 키워드 세트마다 경우의 수가 곱해져(예: 2×2×3=12) Pass·그래픽스 API 수만큼 또 곱해지면서 빌드 시간·크기·로딩·메모리가 급증하는 현상입니다.

</details>

## 핵심 요약

- URP 코드 셰이더는 `Shader` → `Properties` → `SubShader`(Tags, 렌더 상태) → `Pass`(`HLSLPROGRAM`, `#pragma vertex/fragment`) 구조이며, `Core.hlsl`을 include합니다.
- `Attributes`(정점 입력) → `vert` → `Varyings`(보간되어 전달) → `frag` → `SV_Target` 흐름이고, 위치는 `TransformObjectToHClip` 또는 월드 계산 후 `TransformWorldToHClip`으로 변환합니다.
- 텍스처는 `TEXTURE2D`/`SAMPLER`/`SAMPLE_TEXTURE2D` 매크로로, 머티리얼 속성은 `CBUFFER_START(UnityPerMaterial)` 하나에 모아 SRP Batcher 호환을 유지합니다.
- 스프라이트 셰이더는 `Blend SrcAlpha OneMinusSrcAlpha`, `ZWrite Off`, `Cull Off`, 투명 큐, 그리고 정점 색 곱하기가 기본입니다.
- 색은 `half`, 위치·UV·시간은 `float`을 씁니다.
- 기능 토글은 키워드 변형으로 하되 `shader_feature_local`을 우선하고, 키워드 조합이 곱으로 늘어나는 변형 폭발을 경계합니다.
- 속성 이름을 C#과의 계약으로 유지하면, Shader Graph ↔ HLSL로 구현을 바꿔도 게임 코드는 그대로 동작합니다.

## 더 읽을거리

- URP 문서 — Writing custom shaders (URPUnlitShaderBasic 등 예제): https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/writing-custom-shaders-urp.html
- Unity Manual — ShaderLab 레퍼런스: https://docs.unity3d.com/Manual/SL-Reference.html
- Unity Manual — Shader variants and keywords: https://docs.unity3d.com/Manual/shader-variants-and-keywords.html
- Unity Manual — SRP Batcher: https://docs.unity3d.com/Manual/SRPBatcher.html
- The Book of Shaders (셰이더 사고방식 입문, 예제는 GLSL): https://thebookofshaders.com
