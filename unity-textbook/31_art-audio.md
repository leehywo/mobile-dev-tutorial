# 31. 1인 아트·사운드 제작과 조달

> **이 장에서 배울 것**
> - 해상도·PPU·팔레트·실루엣 규칙을 담은 스타일 가이드를 작성하고, 그 규칙으로 직접 만든 에셋과 구매한 에셋을 한 화면에 통일할 수 있다
> - Aseprite 등 픽셀 도구로 스프라이트를 만들고 고치는 워크플로를 세우고, Unity 임포트 설정·Pixel Perfect Camera를 규칙에 맞춘다
> - 에셋을 살 때 스타일 적합성과 라이선스를 함께 판정하고, 외주 브리프·견적 비교표를 작성한다
> - 효과음을 생성·편집·레이어링하고 끊김 없는 루프 BGM을 만들어 12장 `AudioManager`에 연결한다
> - 스타일 규칙 위반을 찾아내는 에디터 검사 도구를 구현한다
>
> **선수 장**: 11, 12 (17·20을 읽었다면 더 좋음) · **예상 시간**: 5~7시간 (그림·녹음 작업 시간 제외) · **코인 러시 진행**: 코인 러시 스타일 가이드, 팔레트 검사 도구, 아이콘 16종 규칙, 효과음 세트와 루프 BGM, 에셋 조달표, 스타일이 통일된 완성 화면 1개
>
> **권장 시점**: 11장을 마친 뒤, 13장(URP) 전. 조명·후처리·파티클은 "무엇을 꾸밀지"가 정해진 뒤에 얹어야 다시 만들지 않습니다.

## 왜 필요한가

11·12장까지 오면 코인 러시는 "게임"으로 돌아갑니다. 그런데 화면을 캡처해서 모르는 사람에게 보여주면 이런 반응이 나옵니다.

```
[현재 코인 러시 스크린샷]
- 플레이어: 무료 팩에서 받은 32px 기사 (외곽선 검정, 채도 높음)
- 적: 에셋 스토어 판타지 몬스터 팩 (64px, 부드러운 그라데이션, 외곽선 없음)
- 코인: 직접 그린 16px 노란 원 (외곽선 없음)
- 배경: 무료 타일셋 (48px, 파스텔)
- UI: 11장의 기본 흰 사각형 + Pretendard

"에셋 플립(asset flip)인가요?"   "적이랑 바닥이 구분이 안 돼요."   "코인이 어디 있어요?"
```

문제는 그림 실력이 아닙니다. **기준이 없어서** 각 에셋이 서로 다른 해상도·외곽선·채도로 들어온 것입니다. 소리도 같습니다. 코인 소리는 너무 크고, 타격음은 레벨이 제각각이며, BGM은 반복될 때마다 "툭" 끊깁니다. 그리고 출시 직전에 이런 질문이 옵니다.

- 이 몬스터 팩을 트레일러와 캡슐에 써도 되는가? (28장 라이선스 대장)
- 외주로 보스 스프라이트를 맡기면 얼마, 몇 주, 수정 몇 번인가?
- Steam 페이지에 AI 생성 콘텐츠 고지가 필요한가?

Steam 유료 게임에서 스크린샷은 구매 결정의 첫 관문입니다(26·27장). 1인 개발자는 아티스트를 고용할 수 없으니, **"적게 그려도 일관되게 보이는 규칙"** 을 먼저 정하고 그 규칙에 맞춰 만들고·사고·맡기는 방법이 필요합니다. 이 장의 산출물은 **스타일이 통일된 완성 화면 1개와 에셋 조달표**입니다. 나머지 콘텐츠는 이 기준을 복제하면 됩니다.

## 개념

### 1인 아트의 원칙 — 제약이 스타일이다

프로 아트팀은 "좋은 그림"을 많이 만들 수 있지만, 1인 개발자에게 필요한 것은 **같은 규칙을 반복할 수 있는 그림**입니다. 그래서 스타일을 "느낌"이 아니라 **측정 가능한 제약**으로 정합니다.

| 제약 | 결정 내용 | 코인 러시 결정 | 왜 |
|---|---|---|---|
| 해상도 | 스프라이트 기준 크기, PPU | 캐릭터 32×32px, PPU 32 | 20장 임포트 규칙과 동일. 32px면 하루에 적 1종 4방향이 가능 |
| 팔레트 | 쓸 수 있는 색 목록 | 24색 고정 | 구매 에셋도 이 팔레트로 재색칠하면 섞여 보이지 않음 |
| 외곽선 | 유무, 색, 두께 | 1px, 가장 어두운 색(검정 아님) | 적 수백 마리 속에서 개체 구분 |
| 명도 계층 | 무엇이 가장 밝고 어두운가 | 코인 > 플레이어 > 적 > 배경 | 기둥 3 "코인 줍는 순간" 우선 |
| 빛 방향 | 하이라이트 위치 | 왼쪽 위 고정 | 에셋마다 빛이 다르면 합성 티가 남 |
| 애니메이션 | 프레임 수·속도 | 걷기 4프레임 10fps, 피격 2프레임 | 17장 클립 규칙 |

웹 개발로 치면 디자인 토큰입니다. 컴포넌트를 누가 만들든 `--color-primary`, `--spacing-2`를 쓰면 한 제품처럼 보이는 것과 같습니다.

### 가독성 계층 — 서바이버라이크는 "읽히는가"가 먼저

화면에 적 수백 마리, 투사체, 코인, 데미지 숫자가 동시에 나오는 장르에서는 예쁨보다 **정보 우선순위**가 중요합니다.

```
가독성 우선순위 (위일수록 눈에 먼저 들어와야 함)

1. 플레이어           — 어디 있는지 0.1초 안에 찾기
2. 위험 (적 투사체·엘리트·보스 공격 범위)
3. 보상 (코인·경험치)
4. 일반 적
5. 이펙트 (내 공격)    — 화려해도 1~4를 가리면 안 됨
6. 배경               — 가장 낮은 대비, 가장 낮은 채도
```

이 계층을 지키는 도구는 세 가지입니다.

- **명도(밝기) 대비**: 색상(hue)보다 먼저 눈에 들어옵니다. 스크린샷을 흑백으로 바꿔도 1~4가 구분되는지 봅니다(흑백 테스트).
- **채도**: 배경은 채도를 낮추고, 코인·위험 요소만 채도를 높입니다.
- **실루엣**: 모든 개체를 검정으로 채웠을 때 형태만으로 종류를 구분할 수 있어야 합니다(실루엣 테스트). 색각 이상 플레이어도 형태로 읽을 수 있고, 38장 접근성 검수의 "색에만 의존하지 않기"와 직결됩니다.

### 해상도·PPU·Pixel Perfect Camera

픽셀 아트에서 가장 흔한 사고는 **픽셀 크기가 제각각인 화면**입니다. 32px 캐릭터 옆에 64px 몬스터를 같은 월드 크기로 줄여 넣으면 몬스터의 픽셀이 캐릭터보다 두 배 촘촘해져 "합성한 티"가 납니다. 규칙은 하나입니다.

> **모든 스프라이트의 PPU(Pixels Per Unit)는 같게, 크기 차이는 그림의 픽셀 수로.**

보스가 크면 96×96px로 그리고 PPU는 똑같이 32입니다. 64px 에셋을 사왔다면 PPU를 64로 바꿔 "작게 보이게" 하지 말고, 32px 규격으로 다시 그리거나(리드로우) 64px 그대로 "큰 적"으로 씁니다.

화면에 몇 픽셀이 보일지는 **기준 해상도**로 정합니다. 코인 러시는 640×360을 기준으로 합니다.

| 실제 화면 | 배율 | 결과 |
|---|---|---|
| 1920×1080 | 3배 | 정수 배율, 딱 맞음 |
| 2560×1440 | 4배 | 정수 배율, 딱 맞음 |
| 1280×720 | 2배 | 정수 배율, 딱 맞음 |
| 1280×800 (Steam Deck) | 2배 (640×400이 보임) | 세로가 40px 더 보이거나, 설정에 따라 테두리 |
| 3440×1440 (울트라와이드) | 4배 (860×360) | 좌우가 더 보임 → 게임 밸런스 영향 검토 |

2D 카메라의 Orthographic Size는 "화면 세로 절반의 월드 단위"입니다. 360px ÷ 2 ÷ 32 PPU = **5.625**. Pixel Perfect Camera를 쓰면 이 값을 컴포넌트가 계산합니다.

URP 2D에는 **Pixel Perfect Camera** 컴포넌트가 있습니다. 주요 설정은 다음과 같습니다(이름은 URP 버전에 따라 조금 다를 수 있으니 Inspector와 매뉴얼을 확인하세요).

| 설정 | 의미 | 코인 러시 |
|---|---|---|
| Assets Pixels Per Unit | 스프라이트 PPU | 32 |
| Reference Resolution | 기준 해상도 | 640 × 360 |
| Crop Frame | 정수 배율이 안 맞을 때 처리 (None/Pillarbox/Letterbox/Windowbox/Stretch Fill) | None (더 보이게) → 38장 검수에서 Deck 확인 |
| Grid Snapping | Pixel Snapping(렌더 시 픽셀 격자 정렬) / Upscale Render Texture(저해상도로 그린 뒤 확대) | Pixel Snapping으로 시작 |
| Filter Mode | 확대 필터 | Point |

주의할 점 두 가지입니다.

- **UI는 Pixel Perfect Camera의 영향을 받지 않습니다.** 11장의 Screen Space - Overlay 캔버스는 그대로 1920×1080 기준입니다. UI 아이콘을 픽셀 아트로 만든다면 32px 아이콘을 **정수 배(96px 또는 128px)** 로 배치하고 Image의 Filter Mode를 Point로 둡니다.
- **17장 Cinemachine과 함께 쓸 때**는 Cinemachine 쪽 Pixel Perfect 확장(`CinemachinePixelPerfect`)을 가상 카메라에 추가해야 줌·흔들림이 픽셀 격자와 싸우지 않습니다. 16장의 화면 흔들림도 0.5px 단위 떨림은 보이지 않으니 1px 이상으로 조정합니다.

> 코인 러시가 픽셀 아트가 아니라면? 벡터풍·페인팅풍도 원리는 같습니다. PPU 대신 "캐릭터 높이 = 화면 높이의 1/12" 같은 **화면 비율 규칙**과 외곽선 두께 규칙을 정하면 됩니다. 다만 1인 개발에서 제작 속도·일관성·수정 비용은 대체로 저해상도 픽셀 아트가 유리합니다.

### 팔레트 — 적게 쓰면 통일된다

팔레트를 16~32색으로 제한하면 서로 다른 사람이 그린 그림도 같은 게임처럼 보입니다. 팔레트는 "예쁜 색 모음"이 아니라 **명도 단계가 있는 램프(ramp)** 의 묶음입니다.

```
램프 = 같은 계열 색을 어두운 것 → 밝은 것 순서로 4~5단계
  보라 램프:  #1a1426  #2e2240  #4a3666  #6e5494  #a58cc4
  금색 램프:  #5c3a12  #9a6418  #d49a22  #f5cc3a  #fff3a8
```

- 램프 사이 색상(hue)을 조금씩 틀면(어두운 쪽은 파랑·보라로, 밝은 쪽은 노랑으로) 단조롭지 않습니다(hue shifting).
- **배경 전용 램프**는 채도를 낮게, **코인·위험 전용 램프**는 채도를 높게 둡니다. 가독성 계층이 팔레트에 박혀 있게 됩니다.
- 팔레트는 PNG 한 장(색마다 1px 또는 8px 칸)으로 저장해 Aseprite와 Unity 검사 도구가 같은 파일을 읽게 합니다. Lospec 같은 팔레트 모음 사이트에서 시작해 수정해도 됩니다(팔레트 자체의 이용 조건은 각 페이지 표기를 확인).

### 스프라이트 제작 도구와 워크플로

| 도구 | 비용·조건 (2026년 확인 기준, 바뀔 수 있음) | 특징 |
|---|---|---|
| Aseprite | 배포 실행 파일은 유료(공식 FAQ 기준 최소 19.99달러). 소스를 받아 **개인 용도로 직접 컴파일**해 쓰는 것은 허용되지만 컴파일한 실행 파일의 재배포는 금지. 만든 그림은 상업적으로 사용 가능 | 레이어·태그·팔레트·타일맵. Unity 공식 임포터가 있음 |
| LibreSprite, Pixelorama | 무료 오픈소스 (각 라이선스 원문 확인) | Aseprite와 비슷한 기능. 임포터 없이 PNG 시트로 내보냄 |
| Krita | 무료 오픈소스 | 일러스트·캡슐 러프에 적합 |

**Aseprite 파일을 Unity로 가져오는 두 경로**가 있습니다.

1. **2D Aseprite Importer** (`com.unity.2d.aseprite`, Unity 6000.0에는 1.1.x가 배포됨) — `.aseprite` 파일을 `Assets`에 넣으면 스프라이트, (설정에 따라) 애니메이션 클립과 Animator Controller까지 만들어 줍니다. 원본을 저장하면 Unity가 자동으로 다시 임포트하므로 **수정 반복이 가장 빠릅니다**. 단, 임포터가 만든 Animator Controller는 읽기 전용이라 17장의 블렌드 트리를 직접 짜려면 클립만 가져와 내 컨트롤러에 넣습니다(임포터 FAQ 참고).
2. **PNG 스프라이트 시트로 내보내기** — Aseprite의 Export Sprite Sheet로 격자 PNG를 만들고, 17장 1단계처럼 Sprite Editor에서 Grid by Cell Size로 자릅니다. 도구에 상관없이 동작하지만, 수정할 때마다 내보내기를 다시 해야 합니다.

코인 러시는 **캐릭터·적은 1번, 타일·아이콘은 2번**으로 갑니다. 아이콘은 한 장에 16개를 모아 두면 아틀라스와 팔레트 검사가 쉽기 때문입니다.

수정 워크플로의 핵심은 **원본 파일은 저장소에, 규칙은 코드에**입니다.

```
Art_Source/                     ← 원본 (.aseprite, .kra). 33장에서 Git LFS로 관리
  characters/knight.aseprite
  enemies/slime.aseprite
Assets/_CoinRush/Art/
  Sprites/knight.aseprite       ← 임포터 경로를 쓰는 파일은 Assets 안에 원본을 둠
  Sprites/tiles_forest.png      ← PNG 내보내기 결과
  UI/icons_weapons.png
  Palette/coinrush_palette.png
```

### 임포트 설정 — 20장 규칙과 맞추기

20장 6단계의 `SpriteImportRules`는 모바일을 기준으로 `ASTC_6x6` 압축을 걸었습니다. **Steam(PC) 유료판이 1차 출시**이고 코인 러시 스프라이트는 32~96px로 작습니다. 픽셀 아트는 압축 블록 노이즈가 바로 보이므로 규칙을 다음처럼 바꿉니다.

| 설정 | 픽셀 아트 스프라이트 | UI(부드러운 그림) |
|---|---|---|
| Texture Type | Sprite (2D and UI) | Sprite (2D and UI) |
| Pixels Per Unit | 32 | 32 (UI에서는 의미 적음) |
| Filter Mode | Point (no filter) | Bilinear |
| Compression (기본 플랫폼) | None | 품질 확인 후 Normal Quality |
| Generate Mip Maps | 끔 | 끔 |
| Mesh Type | Full Rect(타일) / Tight(캐릭터) | Full Rect |
| Android/iOS 오버라이드 | 모바일 확장 트랙에서 ASTC 4x4부터 시험, 18장 측정 | ASTC 4x4 |

32×32 스프라이트 100장을 무압축으로 둬도 RGBA 기준 약 0.4MB이고, 아틀라스(13장)로 묶으면 관리도 쉽습니다. PC에서는 압축보다 선명도가 우선입니다.

### 아이콘 — 16개를 한 규칙으로

코인 러시는 무기 6 + 패시브 10 = 아이콘 16개가 필요합니다(21장 기획서). 레벨업 카드(11장)에서 0.5초 안에 구별돼야 하므로 규칙을 정합니다.

- **캔버스 32×32, 안쪽 여백 2px**, 오브젝트는 28×28 안에.
- **카테고리는 테두리 모양으로**: 무기 = 사각 테두리, 패시브 = 원형 테두리. 색도 다르게 하되 **모양이 1차 구분**입니다(색각 이상 대응).
- **주 형태 1개 + 보조 디테일 1개**까지. 칼 아이콘에 칼·불꽃·보석·글자를 다 넣으면 32px에서 뭉개집니다.
- 흑백으로 바꿔도, 16px로 줄여도(모바일 HUD) 알아볼 수 있는지 확인합니다.
- 같은 무기의 레벨 차이는 아이콘을 새로 그리지 않고 카드 UI의 별·숫자로 표시합니다.

### 에셋 구매 — 스타일 적합성과 라이선스를 같이 본다

사서 쓰는 것은 부끄러운 일이 아닙니다. 문제는 **"싸고 좋아 보여서"** 샀는데 스타일 가이드와 안 맞아서 결국 다시 그리는 경우입니다. 구매 전 체크리스트입니다.

| 항목 | 질문 | 불합격 예 |
|---|---|---|
| 해상도 | 우리 PPU 32 규격과 같은가, 정수배인가 | 50px, 벡터 |
| 팔레트 | 우리 24색으로 재색칠할 수 있는가 | 그라데이션·안티에일리어싱이 많음 |
| 외곽선·빛 방향 | 같은가, 수정 가능한가 | 빛이 오른쪽 위 |
| 애니메이션 | 필요한 동작(걷기·피격·사망)이 다 있는가 | 대기 동작만 |
| 확장성 | 같은 작가가 추가 팩을 내는가, 우리가 이어 그릴 수 있는가 | 단발성 팩 |
| 라이선스 | 상업 게임·트레일러·캡슐 사용, 크레딧, 수정 허용 | NC(비상업) 조건 |
| 증빙 | 영수증·라이선스 원문을 저장할 수 있는가 | 출처 불명 재업로드 |

라이선스는 28장 라이선스 대장에 **구매한 날** 기록합니다. 자주 만나는 조건을 공식 문서 기준으로 정리하면 다음과 같습니다(약관은 바뀌므로 구매 시점의 원문이 기준입니다).

- **Unity Asset Store (Standard EULA)**: 에셋을 소유하는 것이 아니라, "상당한 독창적 콘텐츠와 함께" 게임(Licensed Product)에 포함해 쓰는 **사용권**입니다. 에셋 자체를 독립 상품으로 재배포할 수 없습니다. 에디터 확장·스크립트 같은 Extension Asset은 좌석(seat) 단위이고 한 좌석당 최대 2대 컴퓨터로 제한됩니다. 게임의 "상당 부분"이 구매 에셋 그대로면 약관 위반 소지뿐 아니라 에셋 플립 평판 문제도 생깁니다.
- **Kenney**: 공식 지원 페이지 기준 CC0(퍼블릭 도메인), 상업 이용 가능, 표기 불필요(원하면 "Kenney" 표기). 로고 사용은 삼갑니다.
- **Freesound**: 소리마다 CC0 / CC-BY(저작자 표기) / CC-BY-NC(비상업) 중 하나입니다. **유료 게임에는 NC 소리를 쓸 수 없습니다.** 같은 팩 안에서도 라이선스가 다를 수 있어 파일별로 확인합니다.
- **itch.io·OpenGameArt 등 개인 판매·공유 에셋**: 작가마다 조건이 다릅니다. 페이지의 라이선스 문구를 PDF나 스크린샷으로 저장합니다.
- **AI 생성 에셋**: 도구 약관을 기록하고, Steam은 개발 중 AI 도구로 만든 콘텐츠(Pre-Generated)를 콘텐츠 설문에서 고지하게 합니다. 고지 내용은 출시 후 스토어 페이지에 표시됩니다(Steamworks 콘텐츠 설문 문서).

### 외주 — 브리프는 "판단 기준"을 넘기는 문서

26장 2단계의 캡슐 브리프와 같은 원칙입니다. 작가가 **혼자 판단해도 우리 스타일 가이드를 지킬 수 있게** 기준을 넘깁니다. 게임 내 에셋 외주에는 캡슐과 다른 항목이 더 필요합니다.

- 스타일 가이드 PDF, 팔레트 파일(.png/.gpl), 기존 스프라이트 2~3개 원본
- 규격: 캔버스 크기, PPU, 프레임 수, 태그 이름, 파일 형식(.aseprite 원본 포함)
- **게임 화면 합성 검수**: 작가가 보낸 그림을 실제 게임 화면에 넣은 캡처로 검수한다는 것을 미리 알림
- 권리: 저작재산권 양도 + 2차적저작물작성권(28장 외주 계약 체크리스트), 포트폴리오 공개 허용 시점(출시 후 등)

견적은 **범위를 쪼개서** 받아야 비교할 수 있습니다. 단가는 작가·난이도·시기에 따라 크게 달라서 이 교재에 시세를 적지 않습니다. 대신 같은 브리프를 3곳 이상에 보내고, 아래 항목이 모두 채워진 견적만 비교합니다.

```
견적 비교에 필요한 항목
  1. 단위 단가 × 수량 (예: 적 1종 4방향 × 걷기 4프레임 = 16프레임 단위)
  2. 포함 수정 횟수와 추가 수정 단가 (러프 단계 / 완성 단계 구분)
  3. 일정 (러프 → 1차 → 최종, 각 날짜)
  4. 원본 파일 제공 여부 (.aseprite 레이어)
  5. 권리 범위 (양도 / 이용 허락, 2차적저작물, 트레일러·캡슐·굿즈 사용)
  6. 지급 조건 (계약금·중도금·잔금 비율, 세금계산서·원천징수 방식 — 28장)
  7. 취소 조건 (중도 해지 시 진행분 정산)
```

### 효과음 — 생성, 편집, 레이어링

1인 개발자의 효과음은 대체로 세 경로의 조합입니다.

| 경로 | 도구 예 | 적합한 소리 |
|---|---|---|
| 생성(신시사이저) | sfxr 계열(jsfxr, Bfxr), ChipTone | 코인, 레벨업, 픽업, UI 클릭 — 8비트·레트로 톤 |
| 라이브러리 | Freesound(파일별 라이선스), 구매 팩 | 타격, 폭발, 발소리 등 사실적 소리 |
| 녹음 | 스마트폰·USB 마이크 + 조용한 방 | 독특한 질감 (종이, 금속, 입 소리) |

생성 도구로 만든 소리의 사용 조건도 도구마다 표기가 있으니 한 번 확인해 대장에 적습니다. 편집은 무료인 **Audacity**로 충분합니다.

**레이어링**은 소리 하나를 세 층으로 보고 각각 다른 재료를 겹치는 기법입니다.

```
     진폭
      │█                              ← 1. 어택(Transient): 0~30ms. "딱" — 타격감, 인지 시점
      │██▆▅                           ← 2. 바디(Body): 30~200ms. 무게, 재질 (금속? 살?)
      │█████▅▄▃▂▁▁▁                   ← 3. 꼬리(Tail): 200ms~. 공간, 여운
      └──────────────────────▶ 시간

코인 획득음 = [어택: 짧은 클릭]  +  [바디: sfxr 픽업음, 높은 음]  +  [꼬리: 아주 짧은 반짝임]
```

서바이버라이크 특유의 주의점이 있습니다. **1초에 수십 번 나는 소리는 짧고, 꼬리가 거의 없어야 합니다.** 12장 `AudioManager`가 같은 프레임 중복·동시 재생 수를 막아도, 소리 자체가 500ms 꼬리를 가지면 화면이 소리로 뭉개집니다. 코인·타격은 150ms 안에 끝내고, 레벨업·보스 등장처럼 드문 소리에만 꼬리를 줍니다.

**음량 일관성**: 파일마다 피크가 다르면 12장의 `SfxData.volume`으로 억지로 맞추게 됩니다. Audacity에서 모든 SFX를 **같은 기준으로 정규화**(예: 피크 -1 dBFS, 또는 Loudness Normalization으로 같은 평균 음량)한 뒤, 게임 안의 상대 크기는 `SfxData.volume`에서 조절합니다. 기준값 자체는 팀(=나)의 규칙이면 되고, 중요한 것은 **모든 파일에 같은 기준**을 적용하는 것입니다.

**변형(variation)**: 같은 소리를 3개 변형으로 만들고(피치·재료를 조금씩 다르게), 12장 `SfxData.clips` 배열에 넣습니다. `AudioManager`의 피치 랜덤(±5%)과 합쳐져 반복 피로가 크게 줄어듭니다.

### 루프 BGM — "툭" 소리가 나는 이유

BGM이 반복될 때 끊기는 원인은 대개 셋입니다.

1. **파형이 이어지지 않음**: 끝 샘플 값과 첫 샘플 값이 달라 스피커가 순간적으로 튐 → 클릭음. 곡 끝과 시작을 **영교차점(zero crossing)** 에서 자르거나, 음악 제작 단계에서 끝 부분을 시작 부분으로 자연스럽게 이어지게 만듭니다.
2. **인코더가 앞뒤에 무음을 넣음**: MP3는 인코더 특성상 파일 앞뒤에 짧은 무음(패딩)이 들어가 정확한 루프가 어렵습니다. **원본은 WAV로 보관하고 Unity에는 WAV 또는 OGG로 넣습니다.** MP3는 루프 BGM에 쓰지 않습니다.
3. **임포트 압축 재인코딩**: Unity는 임포트 시 설정한 Compression Format으로 다시 인코딩합니다. 12장 표대로 BGM을 Vorbis·Streaming으로 두고 **빌드에서** 이음새를 들어 봅니다. 이음새가 들리면 해당 곡만 압축 형식을 바꿔 비교하고(용량 증가를 18장 방식으로 기록), 그래도 안 되면 곡 구조를 "인트로 + 루프 구간" 두 파일로 나눠 `AudioSource.PlayScheduled`로 정확한 시각에 이어 붙입니다(연습 문제 3).

작곡은 LMMS(무료 DAW), BeepBox(브라우저 칩튠) 등으로 직접 할 수도 있지만, 음악은 **외주나 라이선스 구매의 효율이 가장 높은 영역**입니다. 구매·외주 음원은 28장 대장에 "트레일러 사용"과 "스트리머 방송 시 저작권 신고(Content ID) 여부"를 반드시 따로 적습니다. 스트리머 방송이 막히면 27장 마케팅 경로 하나가 사라집니다.

## 실습: 코인 러시에 적용하기

앞 장의 최소 시그니처입니다.

```csharp
// 11장 UpgradeData        : string displayName, string description, Sprite icon
// 12장 SfxData            : AudioClip[] clips, float volume, float pitchMin/pitchMax, int maxVoices
// 12장 AudioManager       : static Instance, PlaySfx(SfxData), PlayBgm(AudioClip, float fadeSeconds = 1f)
// 20장 SpriteImportRules  : AssetPostprocessor, Art/Sprites/ 와 Art/UI/ 첫 임포트 규칙
```

작업 폴더: `Assets/_CoinRush/Art/`, `Assets/_CoinRush/Audio/`, `Art_Source/`(프로젝트 루트, Unity가 임포트하지 않는 위치), 문서는 `Docs/`.

### 1단계 — 스타일 가이드 (완성본)

`Docs/style-guide.md`의 완성 예시입니다. 한 화면에 들어오는 길이를 유지합니다. 외주 작가에게 이 문서를 그대로 보냅니다.

```
┌──────────────────────────────────────────────────────────────────────┐
│ 코인 러시 스타일 가이드                          v1.0 / 2026-09-17   │
├──────────────────────────────────────────────────────────────────────┤
│ 한 문장: "어두운 숲의 밤, 금색 코인만 빛난다"                         │
├──────────────────────────────────────────────────────────────────────┤
│ 규격                                                                 │
│  PPU 32 · 기준 해상도 640×360 · Filter Point · 무압축(PC)            │
│  플레이어·일반 적 32×32 · 엘리트 48×48 · 보스 96×96 · 코인 12×12      │
│  타일 32×32 · 아이콘 32×32(여백 2px) · 투사체 8~16px                 │
├──────────────────────────────────────────────────────────────────────┤
│ 팔레트 (24색, Art/Palette/coinrush_palette.png 가 정본)              │
│  배경 램프(저채도 남색) 5 · 적 램프(보라·녹색) 8 · 플레이어(청록) 4  │
│  코인·보상(금색) 5 · 위험(주황·빨강) 2                               │
│  금지: 순수 검정 #000000, 순수 흰색 #ffffff (외곽선은 #1a1426)        │
├──────────────────────────────────────────────────────────────────────┤
│ 명도 계층 (흑백 변환 시 이 순서로 밝아야 함)                          │
│  코인 > 위험 투사체 > 플레이어 > 엘리트 > 일반 적 > 배경              │
├──────────────────────────────────────────────────────────────────────┤
│ 그리기 규칙                                                          │
│  외곽선 1px #1a1426 (배경 타일은 외곽선 없음)                         │
│  빛: 왼쪽 위 · 하이라이트는 램프 최상단 1단계만                       │
│  안티에일리어싱 금지(수동 AA는 외곽 곡선에만 1단계)                   │
│  캐릭터 시선: 4방향(아래·위·왼쪽, 오른쪽은 flipX)                    │
├──────────────────────────────────────────────────────────────────────┤
│ 애니메이션                                                           │
│  걷기 4f@10fps · 대기 2f@4fps · 피격 2f(14장 번쩍임과 병행) · 사망 4f │
│  Aseprite 태그 이름: walk_down, walk_up, walk_left, idle_down ...    │
├──────────────────────────────────────────────────────────────────────┤
│ 아이콘                                                               │
│  무기 = 사각 테두리 · 패시브 = 원형 테두리 · 주 형태 1 + 보조 1       │
│  16px 축소·흑백 변환에서 구별 가능할 것                              │
├──────────────────────────────────────────────────────────────────────┤
│ 사운드                                                               │
│  톤: 칩튠 기반 + 사실적 타격 레이어 · SFX 정규화 피크 -1 dBFS          │
│  잦은 소리(코인·타격) ≤150ms · 드문 소리(레벨업·보스) 꼬리 허용       │
│  변형 3개씩 · BGM WAV 원본 보관, MP3 금지                            │
├──────────────────────────────────────────────────────────────────────┤
│ 검수 3종 (모든 신규 에셋)                                             │
│  ① 게임 화면 합성 캡처 ② 흑백 테스트 ③ 실루엣 테스트                │
│  + Coin Rush/Art/Audit 도구 통과                                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 2단계 — 팔레트 파일과 카메라 설정

1. Aseprite(또는 Pixelorama)에서 24×1px 캔버스를 만들고 1px에 한 색씩 칠해 `Art/Palette/coinrush_palette.png`로 저장합니다. Aseprite라면 같은 팔레트를 `.gpl`로도 내보내 외주 작가에게 줍니다.
2. 팔레트 PNG의 임포트 설정: Texture Type `Default`, Filter `Point`, Compression `None`, **Read/Write는 끕니다**(검사 도구는 파일 바이트를 직접 읽음).
3. Package Manager에서 **2D Aseprite Importer**를 설치합니다(Unity 6000.0 기준 1.1.x. Universal 2D 템플릿에 이미 포함된 경우도 있으니 In Project 탭 먼저 확인).
4. Main Camera에 **Pixel Perfect Camera**를 추가합니다: Assets Pixels Per Unit `32`, Reference Resolution `640 × 360`, Crop Frame `None`, Grid Snapping `Pixel Snapping`.
5. 17장에서 Cinemachine을 붙였다면 CinemachineCamera에 Pixel Perfect 확장을 추가합니다(Add Extension 드롭다운).
6. Game 뷰 해상도를 1920×1080, 2560×1440, 1280×800으로 바꿔 가며 픽셀이 뭉개지거나 크기가 들쭉날쭉하지 않은지 봅니다.

### 3단계 — 임포트 규칙 교체 (20장 `SpriteImportRules` 수정)

20장 6단계 `OnPreprocessTexture()`의 압축 부분을 다음처럼 **교체**합니다. PC 기본 설정은 무압축, 모바일 오버라이드는 모바일 확장 트랙에서만 켭니다. 나머지(첫 임포트 조건, PPU 32, 밉맵 끔)는 그대로입니다.

```csharp
// SpriteImportRules.cs (20장) — OnPreprocessTexture() 안, "var format = ..." 줄부터 foreach 블록 끝까지를 교체
        ti.textureCompression = isSprite
            ? TextureImporterCompression.Uncompressed          // 픽셀 아트: 압축 노이즈 금지
            : TextureImporterCompression.Compressed;           // 부드러운 UI: 품질 확인 후

#if COINRUSH_MOBILE
        foreach (string platform in new[] { "Android", "iPhone" })   // 모바일 확장 트랙에서만 (37장)
        {
            var s = ti.GetPlatformTextureSettings(platform);
            s.overridden = true;
            s.format = TextureImporterFormat.ASTC_4x4;               // 픽셀 아트는 4x4부터 시험 (18장)
            s.maxTextureSize = isUi ? 2048 : 512;
            ti.SetPlatformTextureSettings(s);
        }
#endif
```

규칙을 바꿨으니 `GetVersion()`의 반환값을 `2`로 올립니다. `COINRUSH_MOBILE`은 Player Settings의 Scripting Define Symbols에 모바일 빌드 프로필에서만 넣는 심볼입니다(19장 Build Profiles). 이미 임포트된 텍스처는 `importSettingsMissing` 조건 때문에 바뀌지 않으므로, 20장 본문 끝의 안내대로 선택한 텍스처에 규칙을 다시 적용하는 메뉴를 쓰거나 Inspector에서 직접 맞춥니다. 4단계 검사 도구가 어긋난 파일을 찾아 줍니다.

`.aseprite` 파일은 텍스처가 아니라 Aseprite 임포터가 처리하므로 이 규칙이 적용되지 않습니다. Aseprite 임포터 Inspector에서 Pixels Per Unit 32, Filter Mode Point, Compression None을 한 번 맞추고, 그 설정을 **Preset**으로 저장해(Inspector 오른쪽 위 슬라이더 아이콘 → Save current to...) 다음 파일부터 적용합니다.

### 4단계 — 스타일 검사 도구

규칙은 사람이 기억하지 않고 도구가 검사합니다. 팔레트 밖 색, PPU·필터·압축 위반을 한 번에 찾는 에디터 메뉴입니다.

```csharp
// Assets/_CoinRush/Scripts/Editor/ArtStyleAudit.cs
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

public static class ArtStyleAudit
{
    const string PalettePath = "Assets/_CoinRush/Art/Palette/coinrush_palette.png";
    static readonly string[] PixelArtRoots = { "Assets/_CoinRush/Art/Sprites", "Assets/_CoinRush/Art/UI/Icons" };
    const int RequiredPpu = 32;
    const int MaxOffPaletteReports = 5;   // 파일당 보고할 이상 색 개수

    [MenuItem("Coin Rush/Art/Audit Pixel Art (Palette & Import)")]
    public static void Run()
    {
        if (!File.Exists(PalettePath))
        {
            Debug.LogError($"[ArtAudit] 팔레트 파일이 없습니다: {PalettePath}");
            return;
        }

        HashSet<int> palette = ReadOpaqueColors(PalettePath);
        string[] guids = AssetDatabase.FindAssets("t:Texture2D", PixelArtRoots);
        var report = new StringBuilder();
        int checkedCount = 0, problemCount = 0;

        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            if (!path.EndsWith(".png")) continue;                 // .aseprite는 임포터 Preset으로 관리
            checkedCount++;

            var problems = new List<string>();
            if (AssetImporter.GetAtPath(path) is TextureImporter ti)
            {
                if (ti.textureType != TextureImporterType.Sprite) problems.Add("Texture Type이 Sprite가 아님");
                if (!Mathf.Approximately(ti.spritePixelsPerUnit, RequiredPpu)) problems.Add($"PPU {ti.spritePixelsPerUnit} (규칙 {RequiredPpu})");
                if (ti.filterMode != FilterMode.Point) problems.Add($"Filter {ti.filterMode} (규칙 Point)");
                if (ti.textureCompression != TextureImporterCompression.Uncompressed) problems.Add($"Compression {ti.textureCompression} (규칙 None)");
                if (ti.mipmapEnabled) problems.Add("Mip Map 켜짐");
            }

            List<string> offColors = FindOffPaletteColors(path, palette);
            if (offColors.Count > 0)
                problems.Add($"팔레트 밖 색 {offColors.Count}개+: {string.Join(", ", offColors)}");

            if (problems.Count == 0) continue;
            problemCount++;
            report.AppendLine($"- {path}");
            foreach (string p in problems) report.AppendLine($"    · {p}");
        }

        string summary = $"[ArtAudit] 검사 {checkedCount}개, 문제 {problemCount}개";
        if (problemCount == 0) Debug.Log(summary + " — 모두 통과");
        else Debug.LogWarning(summary + "\n" + report);
    }

    // 파일 바이트를 직접 디코딩하므로 원본 텍스처의 Read/Write를 켤 필요가 없음
    static Texture2D LoadRaw(string path)
    {
        var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!ImageConversion.LoadImage(tex, File.ReadAllBytes(path)))
        {
            Object.DestroyImmediate(tex);
            return null;
        }
        return tex;
    }

    static HashSet<int> ReadOpaqueColors(string path)
    {
        var set = new HashSet<int>();
        Texture2D tex = LoadRaw(path);
        if (tex == null) return set;
        foreach (Color32 c in tex.GetPixels32())
            if (c.a > 0) set.Add(Rgb(c));
        Object.DestroyImmediate(tex);
        return set;
    }

    static List<string> FindOffPaletteColors(string path, HashSet<int> palette)
    {
        var found = new List<string>();
        Texture2D tex = LoadRaw(path);
        if (tex == null) { found.Add("PNG 디코딩 실패"); return found; }

        var seen = new HashSet<int>();
        foreach (Color32 c in tex.GetPixels32())
        {
            if (c.a == 0) continue;                                 // 완전 투명은 무시
            int rgb = Rgb(c);
            if (palette.Contains(rgb) || !seen.Add(rgb)) continue;
            found.Add($"#{rgb:x6}");
            if (found.Count >= MaxOffPaletteReports) break;
        }
        Object.DestroyImmediate(tex);
        return found;
    }

    static int Rgb(Color32 c) => (c.r << 16) | (c.g << 8) | c.b;   // 알파는 비교에서 제외
}
```

설계 포인트:

- `Color32`를 `HashSet`에 그대로 넣지 않고 `int`로 바꿉니다. 구조체 기본 해시는 느리거나 충돌이 많을 수 있습니다.
- 반투명 픽셀(0 < a < 255)도 색은 팔레트 안이어야 합니다. 반투명 자체를 금지하려면 `c.a < 255` 검사를 추가합니다(연습 문제 1).
- 에러가 아니라 경고로 보고합니다. 빌드를 막을지는 20장 `WaveDataBuildCheck`처럼 `IPreprocessBuildWithReport`로 확장할 수 있지만, 아트 규칙은 예외가 생기기 쉬워서 먼저 보고만 합니다.

### 5단계 — 스프라이트 제작·수정 워크플로 실습

적 "슬라임"을 구매 에셋에서 가져와 스타일 가이드에 맞추는 과정을 따라 합니다.

1. 구매한 몬스터 팩의 슬라임 시트(64×64px, 그라데이션)를 `Art_Source/purchased/`에 두고, **라이선스 원문과 영수증을 `Docs/licenses/`에 저장**합니다(8단계 조달표에 기록).
2. Aseprite에서 열고 `Sprite → Sprite Size`로 50% 축소(Nearest Neighbor). 뭉개진 부분은 손으로 정리합니다.
3. `Sprite → Color Mode → Indexed`로 바꾸면서 팔레트를 `coinrush_palette`로 지정합니다. 자동 변환은 램프를 엉뚱하게 고르므로 **어두운 → 밝은 순서로 램프를 수동으로 다시 매핑**합니다.
4. 외곽선을 `#1a1426` 1px로 통일하고 하이라이트를 왼쪽 위로 옮깁니다.
5. 태그를 `walk_down`, `walk_up`, `walk_left`, `hit`, `die`로 붙이고 `Assets/_CoinRush/Art/Sprites/Enemies/slime.aseprite`로 저장합니다.
6. Unity에서 임포터 Preset이 적용됐는지 확인하고, 17장 방식으로 클립을 연결합니다.
7. **검수 3종**을 합니다.
   - 게임 화면에 슬라임 50마리 + 플레이어 + 코인을 띄워 캡처합니다.
   - 캡처를 흑백으로 바꿉니다(이미지 편집기의 Desaturate). 코인 > 플레이어 > 슬라임 > 배경 순으로 밝은지 봅니다.
   - 실루엣: Play 중에 플레이어·슬라임·코인 프리팹 인스턴스의 **SpriteRenderer.Color를 검정**으로 잠깐 바꾸고(곱하기 색이라 전부 검게 칠해짐), 배경 타일맵을 끈 뒤 밝은 카메라 배경색에서 캡처합니다. 형태만으로 슬라임·플레이어·코인이 구별되는지 봅니다. Play를 끄면 값은 원래대로 돌아옵니다.
8. `Coin Rush/Art/Audit Pixel Art` 실행 → 문제 0개.

수정 요청이 오면(예: "슬라임이 바닥과 구분이 안 된다") 같은 `.aseprite`를 열어 몸통 램프를 한 단계 밝게 바꾸고 저장만 하면 Unity가 다시 임포트합니다. 이 왕복이 **1분 안에** 끝나야 1인 개발에서 아트 반복이 가능합니다.

### 6단계 — 아이콘 16종 제작 규칙 적용

1. 32×32 캔버스 16칸짜리 `Art_Source/icons/icons.aseprite`를 만들고(가로 4 × 세로 4), 1행 첫 칸에 **템플릿 레이어**(사각 테두리 / 원형 테두리, 2px 여백 가이드)를 둡니다.
2. 무기 6 · 패시브 10을 그립니다. 테두리 레이어는 복사해서 쓰고 안쪽만 그립니다.
3. PNG 시트로 내보내 `Assets/_CoinRush/Art/UI/Icons/icons.png`에 둡니다. Sprite Mode `Multiple` → Sprite Editor → Grid by Cell Size 32×32로 자르고, 이름을 `icon_weapon_orb`, `icon_passive_magnet`처럼 바꿉니다.
4. 11장의 `UpgradeData` 에셋 16개의 `icon` 필드에 연결합니다.
5. 11장 `UpgradeCardView`의 아이콘 Image: 크기 **96×96**(정수 3배), `Preserve Aspect` 켬. 스프라이트 Filter가 Point인지 확인합니다.
6. 검수: 레벨업 창을 캡처해 흑백으로 바꾸고, 사각/원형 테두리만으로 무기와 패시브가 구분되는지 봅니다. 16px로 축소한 캡처에서 16개를 서로 헷갈리지 않는지 지인 1명에게 물어봅니다.

| 아이콘 | 테두리 | 주 형태 | 보조 디테일 |
|---|---|---|---|
| 무기: 궤도 구슬 | 사각 | 구슬 1개 | 궤도 점선 |
| 무기: 자동 조준 화살 | 사각 | 화살 | 조준선 |
| 무기: 코인 투척 | 사각 | 코인 | 속도선 |
| 패시브: 자석 | 원형 | 말굽자석 | 코인 1개 |
| 패시브: 최대 체력 | 원형 | 하트 | + 표시 |
| 패시브: 쿨다운 감소 | 원형 | 모래시계 | 아래 화살표 |
| … (나머지 10개 같은 형식) | | | |

### 7단계 — 효과음 세트 만들기와 12장 연결

**코인 획득음 3종**을 레이어링으로 만듭니다.

1. jsfxr(브라우저)에서 `Pickup/Coin` 프리셋을 여러 번 눌러 높은 음 후보 3개를 고르고 WAV(44.1kHz 또는 48kHz, 16bit)로 저장합니다 → **바디**.
2. 짧은 클릭(나무·금속 탭 녹음이나 생성음)을 준비합니다 → **어택**.
3. Audacity에서 트랙 두 개로 겹칩니다. 어택을 바디보다 5~10ms 앞에 둡니다.
4. 전체 길이를 120ms로 자르고, 끝 10ms에 Fade Out을 걸어 클릭음을 없앱니다. 시작 부분 무음을 잘라 **입력과 소리의 지연**을 없앱니다.
5. 트랙을 합치고(Mix and Render) 1단계 가이드 기준으로 정규화합니다.
6. `coin_01.wav`~`coin_03.wav`로 내보내 `Assets/_CoinRush/Audio/SFX/`에 넣습니다. 원본 Audacity 프로젝트는 `Art_Source/audio/`에 둡니다.
7. 12장 개념의 임포트 표대로 설정(Decompress On Load, ADPCM, Force To Mono)합니다.
8. 12장 8단계의 `Sfx_Coin` 에셋 `clips` 배열에 세 파일을 넣습니다.

전체 효과음 목록과 제작 경로를 표로 관리합니다. `maxVoices`·`volume`은 12장 `SfxData` 값이고, 게임을 틀어 놓고 조정합니다.

| SfxData | 파일 | 경로 | 길이 | 변형 | volume | maxVoices | 비고 |
|---|---|---|---|---|---|---|---|
| Sfx_Coin | coin_01~03 | 생성 + 녹음 레이어 | 120ms | 3 | 0.5 | 2 | 가장 자주 남, 작게 |
| Sfx_Hit | hit_01~03 | Freesound CC0 + 생성 | 90ms | 3 | 0.6 | 4 | 저역 줄여 코인과 겹침 방지 |
| Sfx_EnemyDeath | death_01~03 | 생성 | 150ms | 3 | 0.5 | 3 | |
| Sfx_LevelUp | levelup_01 | 생성 3층 | 900ms | 1 | 0.9 | 1 | timeScale 0에서도 재생 |
| Sfx_ShrineOpen | shrine_01 | 구매 팩 편집 | 1.2s | 1 | 0.8 | 1 | 21장 제단 — 드문 소리 |
| Sfx_BossWarning | boss_warn_01 | 구매 팩 편집 | 2.0s | 1 | 1.0 | 1 | 22장 경고 연출과 동기 |
| Sfx_UiMove / UiConfirm | ui_move, ui_ok | 생성 | 40ms / 80ms | 1 | 0.4 | 1 | 패드 포커스 이동(11장) |

### 8단계 — 에셋 조달표 (완성본)

"무엇을 직접, 무엇을 사고, 무엇을 맡길지"를 한 표로 결정합니다. 기준은 **훅에 가까울수록 직접**(차별점이 드러나는 부분), **양이 많고 규격화된 것은 구매 후 재색칠**, **전문성이 크고 1회성인 것은 외주**입니다. 28장 라이선스 대장의 ID를 그대로 씁니다.

| ID | 에셋 | 수량 | 조달 | 이유 | 예상 공수/비용 | 스타일 조치 | 라이선스·증빙 (28장 대장) | 상태 |
|---|---|---|---|---|---|---|---|---|
| A-10 | 플레이어 캐릭터 3종 | 3 × 4방향 | 직접 | 게임의 얼굴, 계속 수정됨 | 3일 | 기준 스프라이트 | 자체 제작 | 1종 완료 |
| A-02 | 일반 적 4종 | 4 | 구매 + 리드로우 | 양 많고 규격화 | 팩 구매 + 4일 | 50% 축소·재색칠·외곽선 | 구매 영수증, 라이선스 원문 PDF | 슬라임 완료 |
| A-11 | 엘리트 1 + 보스 1 | 2 | 외주 | 큰 스프라이트, 품질이 트레일러에 노출 | 견적 3곳 비교 후 결정 | 브리프 + 합성 검수 | 양도 + 2차적저작물 특약 계약서 | 브리프 발송 |
| A-12 | 타일셋 (숲 1맵) | 1세트 | 구매(CC0) + 재색칠 | 맵 1개라 부담 적음 | 2일 | 배경 램프로 저채도화 | CC0 원문 저장 | 완료 |
| A-13 | 아이콘 16 | 16 | 직접 | 규칙 기반, 밸런스 변경 시 계속 추가 | 2일 | 6단계 규칙 | 자체 제작 | 진행 |
| A-14 | 이펙트 스프라이트 | 8 | 직접(16장 파티클과 병행) | 게임 필 반복 조정 필요 | 2일 | 금색·주황 램프만 | 자체 제작 | 대기 |
| A-01 | 캡슐 아트 | 1세트 | 외주 | 26장 브리프 | 26장 참고 | 게임 팔레트 파일 첨부 | 26·28장 | 26장에서 진행 |
| M-01 | BGM 전투 루프 + 타이틀 | 2곡 | 외주 | 음악은 효율 높은 외주 영역 | 견적 3곳 | WAV 원본, 루프 지점 명시 | 계약서, Content ID 등록 안 함 조항 | 브리프 작성 |
| M-02 | 코인·타격·사망 SFX | 9 | 생성 + CC0 레이어 | 잦은 수정 | 1.5일 | 7단계 기준 | Freesound 파일별 CC0 확인 | 완료 |
| M-04 | 제단·보스 경고 SFX | 2 | 구매 팩 편집 | 사실적 질감 | 0.5일 | 길이·정규화 | Asset Store 인보이스 | 대기 |
| F-01 | 한글 폰트 | 1 | 무료(OFL) | 11장 | — | — | OFL 원문 | 완료 |

(공수·비용 칸의 수치는 형식 설명용 예시입니다. 실제로는 29장 3점 추정과 받은 견적으로 채웁니다.)

**비용 판단 예**: 엘리트·보스 외주 견적이 들어왔을 때 "직접 그리면 며칠인가 × 내 시간의 기회비용(34장 병행 수입 시급)"과 비교합니다. 직접 그리는 데 6일이 걸리고, 그 6일에 외주 개발로 벌 수 있는 돈이 견적보다 크면 외주가 합리적입니다. 반대로 아직 게임이 재미 검증(24장) 전이라면 **어떤 외주도 발주하지 않고** 임시 그림으로 버팁니다.

### 9단계 — 외주 브리프 (BGM, 완성본)

```
[코인 러시 BGM 외주 브리프 v1]

1. 게임: 10분 한 판의 2D 서바이버라이크(Steam 유료). 스타일 가이드·플레이 영상 2분 첨부
2. 곡 목록
   - 전투 루프: 90~120초 루프, 템포 130~150 BPM. 10분 동안 반복 청취 → 멜로디 과잉 금지
   - 타이틀: 60초 루프, 차분하지만 "한 판 더" 기대감
3. 레퍼런스(분위기만, 모방 금지): 곡 링크 3개와 각 곡에서 참고할 점 1줄씩
4. 톤: 칩튠 음색 + 현대적 드럼. 효과음(코인 고음 영역 2~4kHz)을 가리지 않게 그 대역의 리드 자제
5. 기술 납품 규격
   - WAV 48kHz/24bit 원본 + 루프 버전(끝→시작 이음새가 무음·클릭 없이 연결)
   - 인트로가 있으면 "인트로.wav + 루프.wav" 분리 납품 (샘플 단위로 이어짐)
   - 스템(드럼/베이스/리드) 별도 — 보스전 레이어 추가 가능성
6. 일정: 데모 30초 스케치(7일) → 수정 2회 → 최종(21일)
7. 권리
   - 게임·트레일러·스토어·방송(스트리머 포함) 사용 가능해야 함
   - 곡을 Content ID 등 자동 저작권 신고 시스템에 등록하지 않음 (등록 시 사전 협의)
   - 사운드트랙 별도 판매 시 수익 배분은 별도 협의
   - 크레딧 표기 방식
8. 검수 기준: 실제 게임 빌드에서 10분 플레이 시 이음새가 들리지 않고, 코인 SFX가 묻히지 않음
9. 견적 요청 항목: 곡당 단가, 포함 수정 횟수, 스템 비용, 일정, 지급 조건(28장 원천징수 방식 포함)
```

### 10단계 — 루프 BGM 연결과 이음새 테스트

1. 받은(또는 만든) `battle_loop.wav`를 `Assets/_CoinRush/Audio/BGM/`에 넣고 12장 표대로 설정합니다(Streaming, Vorbis, Preload 끔).
2. 전투 시작 시 12장 `AudioManager.Instance.PlayBgm(battleLoop)`를 호출합니다(09장 씬 흐름의 Playing 진입 지점). `CreateSource`에서 BGM 소스는 이미 `loop = true`입니다.
3. 이음새 확인용 디버그 도구를 붙입니다. 루프 직전 3초로 건너뛰어 반복해서 들을 수 있게 합니다.

```csharp
// Assets/_CoinRush/Scripts/Debug/BgmSeamTester.cs
using UnityEngine;
using UnityEngine.InputSystem;

// 개발 빌드 전용: F9를 누르면 지금 재생 중인 BGM을 끝나기 3초 전으로 이동
public class BgmSeamTester : MonoBehaviour
{
    [SerializeField] private float secondsBeforeEnd = 3f;

    private void Awake()
    {
        if (!Debug.isDebugBuild) Destroy(this);   // 에디터와 Development Build에서만 동작
    }

    private void Update()
    {
        if (Keyboard.current == null || !Keyboard.current.f9Key.wasPressedThisFrame) return;

        AudioManager manager = AudioManager.Instance;
        if (manager == null) return;

        foreach (AudioSource source in manager.GetComponentsInChildren<AudioSource>())
        {
            if (!source.loop || !source.isPlaying || source.clip == null) continue;
            float target = Mathf.Max(0f, source.clip.length - secondsBeforeEnd);
            source.time = target;                               // Streaming 클립은 위치가 약간 어긋날 수 있음
            Debug.Log($"[BgmSeam] {source.clip.name} → {target:0.00}s");
        }
    }
}
```

4. 부트스트랩 씬(09장)의 `AudioManager` 오브젝트에 붙이고, **Development Build**로 PC 빌드를 만들어 헤드폰으로 F9를 5번 이상 눌러 이음새를 듣습니다. 에디터와 빌드의 결과가 다를 수 있으니 반드시 빌드에서 확인합니다.
5. 클릭음이 들리면: ① 원본 WAV를 Audacity에서 열어 끝과 시작의 파형이 이어지는지 확대해 보고, ② 이음새 문제가 원본이 아니라면 해당 클립만 Compression Format을 바꿔 다시 비교합니다. 결과와 용량 차이를 조달표 비고에 적습니다.

### 11단계 — 완성 화면 1개

지금까지의 규칙을 **한 장면**에서 모두 증명합니다. 이 캡처가 26장 스토어 스크린샷의 기준이 됩니다.

1. 장면 구성: 숲 타일 배경, 플레이어, 슬라임 40마리, 엘리트 1(임시여도 규격 준수), 코인 30개, 궤도 구슬 무기 이펙트, HUD, 화면 오른쪽 위 코인 카운터.
2. 13장 조명·후처리는 **아직 넣지 않습니다.** 조명 없이도 읽혀야 조명을 얹었을 때 무너지지 않습니다.
3. 1920×1080과 1280×800에서 각각 캡처합니다.
4. 체크리스트를 채웁니다.

| 검사 | 기준 | 결과 |
|---|---|---|
| 픽셀 크기 | 모든 스프라이트의 픽셀 크기가 같음 | ☐ |
| 흑백 | 코인 > 플레이어 > 적 > 배경 명도 순서 | ☐ |
| 실루엣 | 플레이어·적·코인이 형태로 구별 | ☐ |
| 2초 테스트 | 처음 보는 사람이 2초 안에 플레이어 위치를 가리킴 | ☐ |
| 팔레트 | Audit 도구 문제 0 | ☐ |
| 소리 | 30초 플레이 녹화에서 코인음이 타격음에 묻히지 않고, BGM 이음새 없음 | ☐ |
| 라이선스 | 화면에 보이는·들리는 모든 에셋이 조달표와 28장 대장에 있음 | ☐ |

### 확인하기

- `Coin Rush/Art/Audit Pixel Art`를 실행하면 콘솔에 `[ArtAudit] 검사 N개, 문제 0개 — 모두 통과`가 나온다. 일부러 아이콘 하나의 Filter를 Bilinear로 바꾸면 그 파일과 사유가 경고로 나온다. 팔레트 밖 색 한 점을 찍어 저장하면 `팔레트 밖 색 1개+: #xxxxxx`가 나온다.
- Game 뷰를 1920×1080 ↔ 2560×1440 ↔ 1280×800으로 바꿔도 픽셀이 균일하고, 캐릭터가 흐리게 보이지 않는다.
- `.aseprite` 원본의 색을 바꿔 저장하면 Unity로 돌아왔을 때 게임 화면에 반영돼 있다.
- 레벨업 창의 아이콘이 96×96으로 선명하고, 흑백 캡처에서도 무기·패시브가 테두리 모양으로 구분된다.
- 코인을 30개 동시에 먹어도 소리가 뭉개지지 않고, Development Build에서 F9로 BGM 이음새를 반복해 들어도 클릭음이 없다.
- 조달표의 모든 행에 조달 방식·라이선스 증빙 위치가 채워져 있다.

## 흔한 실수

1. **증상**: 구매 에셋을 섞었더니 "에셋 플립 같다"는 말을 듣는다. → **원인**: 해상도·팔레트·외곽선이 에셋마다 다름. PPU를 바꿔 크기만 맞춤. → **해결**: PPU는 전 에셋 동일, 구매 에셋은 스타일 가이드 규격으로 축소·재색칠·외곽선 통일 후 사용합니다. 재작업 공수가 크면 구매 전 체크리스트에서 탈락시킵니다.
2. **증상**: 픽셀 아트가 흐리거나 줄마다 두께가 다르다. → **원인**: Filter Bilinear, 압축 노이즈, 비정수 배율, 카메라 위치가 픽셀 사이. → **해결**: Point·무압축, Pixel Perfect Camera, Cinemachine Pixel Perfect 확장, 흔들림 크기를 1px 이상으로.
3. **증상**: 적 수백 마리 속에서 플레이어와 코인을 못 찾는다. → **원인**: 색상만 다르고 명도·실루엣 계층이 없음. 배경 채도가 높음. → **해결**: 흑백·실루엣 테스트, 배경 램프 채도 낮춤, 코인 램프를 가장 밝게.
4. **증상**: 코인을 많이 먹으면 소리가 "지글지글" 뭉개진다. → **원인**: 잦은 소리의 꼬리가 길고 음량이 큼, 변형 없음. → **해결**: 150ms 이하로 자르고 Fade Out, 변형 3개, `maxVoices` 2, 상대 음량 낮춤.
5. **증상**: BGM이 반복될 때 "툭" 소리가 나거나 짧은 공백이 있다. → **원인**: MP3 사용, 파형 불연속, 재인코딩 영향. → **해결**: WAV 원본·영교차점 편집, 빌드에서 이음새 테스트, 필요 시 압축 형식 변경이나 인트로/루프 분리 + `PlayScheduled`.
6. **증상**: 출시 직전 "이 효과음 어디서 받았지?" → **원인**: 다운로드 시점에 기록하지 않음, Freesound 팩 전체를 CC0로 착각. → **해결**: 받는 날 조달표·28장 대장에 파일별로 기록, 라이선스 원문 저장. NC 조건은 유료 게임에 쓰지 않습니다.

## 연습 문제

**1. ★☆☆ 반투명 금지 규칙 추가**
`ArtStyleAudit`에 "픽셀 아트 폴더의 스프라이트는 완전 투명(a=0) 또는 완전 불투명(a=255)만 허용" 규칙을 추가하고, 위반 픽셀 수를 보고하세요.

<details>
<summary>힌트·해설</summary>

`FindOffPaletteColors`와 같은 루프에서 `c.a > 0 && c.a < 255`인 픽셀을 셉니다. 한 번 디코딩한 텍스처로 두 검사를 같이 하도록 메서드를 `AnalyzePixels(path, palette, out List<string> offColors, out int semiTransparent)`로 합치면 파일을 두 번 읽지 않습니다. 단, 그림자 스프라이트처럼 의도적으로 반투명을 쓰는 폴더가 있다면 예외 폴더 목록(`static readonly string[] AllowAlphaRoots`)을 둡니다. 규칙에는 항상 예외 경로를 설계해 두어야 도구가 무시당하지 않습니다.

</details>

**2. ★★☆ 구매 에셋 판정**
아래 두 팩 중 코인 러시 "일반 적 4종"으로 무엇을 살지, 1단계 스타일 가이드와 개념 절의 구매 체크리스트로 판정하고 재작업 공수를 추정하세요.
- 팩 A: 48×48px 몬스터 20종, 걷기·공격·사망 애니메이션, 외곽선 없음, 32색, Asset Store Standard EULA
- 팩 B: 32×32px 몬스터 8종, 걷기 애니메이션만, 검정 외곽선, 16색, itch.io 개인 판매, 라이선스 문구 "commercial use OK, no redistribution"

<details>
<summary>힌트·해설</summary>

- **해상도**: B는 규격 일치. A는 48px라 "엘리트(48px)"로는 맞지만 일반 적으로 쓰려면 32px 리드로우가 필요해 종당 공수가 큽니다.
- **팔레트·외곽선**: B는 16색이라 24색 팔레트로 옮기기 쉽고, 외곽선 색만 `#1a1426`으로 치환하면 됩니다. A는 외곽선을 새로 그려야 합니다.
- **애니메이션**: B는 피격·사망이 없어 종당 6프레임을 추가로 그려야 합니다. A는 동작이 충분합니다.
- **라이선스**: 둘 다 상업 이용 가능. B는 트레일러·캡슐 사용이 명시되지 않았으니 구매 전 작가에게 문의해 답변을 저장합니다.
- 결론 예: 일반 적은 **B**(재색칠 0.5일 + 피격·사망 추가 0.5일, 종당 약 1일 × 4), 엘리트 후보로 A에서 1종을 골라 48px 그대로 쓰는 조합. 핵심은 "많이 들어 있는 팩"이 아니라 **스타일 가이드까지의 거리**가 가까운 팩을 사는 것입니다.

</details>

**3. ★★☆ 인트로 + 루프 BGM**
외주 음악이 `battle_intro.wav`(8초) + `battle_loop.wav`(96초)로 납품됐습니다. 인트로가 끝나는 샘플 정확한 시점에 루프를 이어 재생하는 `IntroLoopBgm` 컴포넌트를 만드세요. 12장 믹서의 BGM 그룹으로 출력해야 합니다.

<details>
<summary>힌트·해설</summary>

`Update`에서 `isPlaying`이 false가 되는 순간 루프를 시작하면 프레임 단위 오차로 틈이 생깁니다. **오디오 DSP 시계**로 미리 예약합니다.

```csharp
// Assets/_CoinRush/Scripts/Audio/IntroLoopBgm.cs
using UnityEngine;
using UnityEngine.Audio;

public class IntroLoopBgm : MonoBehaviour
{
    [SerializeField] private AudioClip intro;
    [SerializeField] private AudioClip loop;
    [SerializeField] private AudioMixerGroup bgmGroup;

    private AudioSource introSource, loopSource;

    private void Awake()
    {
        introSource = gameObject.AddComponent<AudioSource>();
        loopSource = gameObject.AddComponent<AudioSource>();
        foreach (AudioSource s in new[] { introSource, loopSource })
        {
            s.playOnAwake = false;
            s.outputAudioMixerGroup = bgmGroup;
        }
        loopSource.loop = true;
    }

    public void Play()
    {
        double start = AudioSettings.dspTime + 0.1;                     // 로드 여유 0.1초
        double introLength = (double)intro.samples / intro.frequency;   // length(float)보다 정확
        introSource.clip = intro;
        loopSource.clip = loop;
        introSource.PlayScheduled(start);
        loopSource.PlayScheduled(start + introLength);
    }

    public void Stop() { introSource.Stop(); loopSource.Stop(); }
}
```

인트로와 루프 클립은 **같은 샘플레이트**여야 계산이 맞습니다. 스트리밍 클립은 예약 시점에 로딩이 늦을 수 있으니 인트로는 Compressed In Memory로 두는 편이 안전합니다. 12장 `AudioManager`의 크로스페이드와 함께 쓰려면, 이 컴포넌트를 `AudioManager` 안에 넣고 "지금 BGM이 인트로-루프 모드인지" 상태를 하나 두어 페이드 대상 소스를 바꾸는 방식으로 확장합니다.

</details>

**4. ★★★ 두 번째 맵 스타일 확장 (확장 과제)**
출시 후 업데이트로 "사막" 맵을 추가한다고 가정합니다. 스타일 가이드 v1.1을 작성하세요. 팔레트를 몇 색 늘릴지, 기존 적 재사용(재색칠 변형)의 범위, 새 배경 램프가 가독성 계층을 깨지 않는지 검증하는 방법, 조달표 추가 행, `ArtStyleAudit`가 맵별 팔레트를 검사하도록 바꾸는 설계를 포함합니다.

<details>
<summary>힌트·해설</summary>

- 사막 배경은 밝은 황토색이 되기 쉬워 **금색 코인 램프와 명도가 겹칩니다.** 배경 램프를 코인보다 2단계 이상 어둡게 두거나, 코인에 1px 어두운 외곽선을 추가하는 규칙을 v1.1에 넣습니다. 흑백 테스트로 검증합니다.
- 팔레트는 공용 24색 + 맵 전용 램프 5~8색으로 나누고, 검사 도구는 `폴더 → 허용 팔레트 목록` 매핑을 ScriptableObject(`ArtAuditRules`)로 두어 `Art/Sprites/Desert/`는 공용 + 사막 팔레트를 허용하게 합니다.
- 적 재사용: 슬라임 → "모래 슬라임"은 인덱스 색 치환으로 반나절이면 되지만, 실루엣이 같아 **행동이 다르면 플레이어가 헷갈립니다.** 행동이 다르면 실루엣 요소(뿔, 크기)를 하나 추가하는 규칙을 둡니다.
- 조달표에는 39장 운영 계획과 연결해 "업데이트 비용 대비 효과"를 판단할 수 있게 공수 열을 꼭 채웁니다.

</details>

## 셀프 체크

**1. 64px로 그려진 구매 몬스터를 PPU 64로 설정해 32px 캐릭터와 같은 크기로 맞추면 무엇이 문제인지 설명해 보세요.**

<details>
<summary>모범 답안</summary>

월드 크기는 같아져도 몬스터의 픽셀 하나가 캐릭터 픽셀의 절반 크기로 보여, 한 화면 안에 **픽셀 밀도가 두 종류**가 됩니다. 사람 눈은 이 차이를 바로 "합성한 그림"으로 인식합니다. 픽셀 아트에서는 모든 스프라이트의 PPU를 같게 두고, 크기 차이는 그린 픽셀 수로 표현해야 합니다. 64px 에셋은 32px로 리드로우하거나 "큰 적"으로 64px 그대로 씁니다.

</details>

**2. 흑백 테스트와 실루엣 테스트는 각각 무엇을 검증하나요?**

<details>
<summary>모범 답안</summary>

흑백 테스트는 **명도 계층**을 검증합니다. 색상 정보를 지워도 코인·플레이어·적·배경이 의도한 밝기 순서로 구분되는지 봅니다. 실루엣 테스트는 **형태 구분**을 검증합니다. 색과 명도를 모두 지워도 모양만으로 종류를 알 수 있는지 봅니다. 두 테스트를 통과하면 수백 마리가 겹치는 화면에서도 읽히고, 색각 이상 플레이어도 색에만 의존하지 않고 플레이할 수 있습니다.

</details>

**3. Steam PC판에서 픽셀 아트 스프라이트를 무압축으로 두는 이유와, 모바일 확장 시 다시 검토해야 하는 이유는?**

<details>
<summary>모범 답안</summary>

32~96px 스프라이트는 무압축이어도 전체 메모리가 작고, 블록 압축(ASTC·DXT 등)의 노이즈가 1픽셀 단위 그림에서는 바로 보이기 때문입니다. PC는 메모리·다운로드 여유가 커서 선명도를 우선합니다. 모바일은 기기 메모리·앱 용량·GPU 대역폭 제약이 커서, 18장 방식으로 ASTC 4x4 같은 고품질 블록 크기를 시험하고 화질과 용량을 측정해 결정해야 합니다.

</details>

**4. Freesound에서 받은 소리를 유료 게임에 넣기 전에 확인할 것은?**

<details>
<summary>모범 답안</summary>

소리마다 라이선스가 CC0, CC-BY, CC-BY-NC 중 하나로 다르므로 **파일별로** 확인합니다. CC-BY-NC는 비상업 조건이라 유료 게임에 쓸 수 없고, CC-BY는 크레딧에 저작자 표기가 필요합니다(28장 크레딧 화면). 확인한 날짜·URL·라이선스를 조달표와 라이선스 대장에 기록하고 페이지를 저장해 둡니다. 편집·레이어링해 새 소리를 만들어도 원재료의 조건은 그대로 따라옵니다.

</details>

**5. 외주 견적을 비교할 때 총액만 보면 안 되는 이유를 세 가지 이상 드세요.**

<details>
<summary>모범 답안</summary>

① 포함 수정 횟수가 달라 추가 수정 비용이 총액을 뒤집을 수 있습니다. ② 원본 레이어 파일 제공 여부에 따라 나중에 직접 고칠 수 있는지가 달라집니다. ③ 권리 범위(양도/이용 허락, 트레일러·캡슐·사운드트랙 사용, Content ID 등록)가 다르면 같은 결과물이라도 쓸 수 있는 곳이 다릅니다. ④ 일정과 지급 조건(선금 비율, 원천징수 방식)이 현금흐름(34장)에 영향을 줍니다. 그래서 같은 브리프를 보내고 항목을 표로 맞춰 비교합니다.

</details>

**6. 코인·타격 효과음은 짧아야 하고 레벨업 효과음은 길어도 되는 이유는?**

<details>
<summary>모범 답안</summary>

서바이버라이크에서 코인·타격은 1초에 수십 번 발생합니다. 꼬리가 길면 이전 소리가 끝나기 전에 다음 소리가 겹쳐 전체가 뭉개지고, 동시 재생 제한에 걸려 새 소리가 잘립니다. 레벨업·보스 등장은 드물고 "사건"을 알리는 소리라, 여운이 있어야 중요도가 전달됩니다. 소리의 길이도 가독성 계층처럼 **빈도와 중요도**로 정합니다.

</details>

## 핵심 요약

- 1인 개발의 아트 스타일은 "느낌"이 아니라 해상도·PPU·팔레트·외곽선·빛 방향·프레임 수 같은 **측정 가능한 제약**입니다. 스타일 가이드 한 장이 직접 제작·구매·외주를 한 게임으로 묶습니다.
- 서바이버라이크 화면은 **가독성 계층**(플레이어 > 위험 > 보상 > 적 > 이펙트 > 배경)이 먼저이고, 흑백·실루엣 테스트로 검증합니다.
- 모든 스프라이트의 PPU를 같게 두고, 기준 해상도(640×360)와 Pixel Perfect Camera로 정수 배율을 지킵니다. PC 픽셀 아트는 Point·무압축.
- 규칙은 사람이 아니라 도구가 검사합니다. 임포트 규칙(20장)과 팔레트 검사 도구를 함께 씁니다.
- 에셋 구매는 "양"이 아니라 **스타일 가이드까지의 거리**와 라이선스(상업·트레일러·NC 여부)로 판정하고, 받는 날 28장 대장에 기록합니다.
- 외주는 판단 기준을 넘기는 브리프와 항목별 견적 비교로 결정하고, 재미 검증 전에는 발주하지 않습니다.
- 잦은 효과음은 짧고 변형 3개, 모든 SFX는 같은 기준으로 정규화한 뒤 12장 `SfxData.volume`에서 상대 크기를 조정합니다.
- 루프 BGM은 WAV 원본·MP3 금지·빌드에서 이음새 확인이 기본이고, 인트로가 있으면 `PlayScheduled`로 샘플 단위로 잇습니다.

## 더 읽을거리

- Unity 매뉴얼 — 2D Aseprite Importer (Unity 6000.0): https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.2d.aseprite.html
- Unity 매뉴얼 — URP 2D Pixel Perfect Camera: https://docs.unity3d.com/6000.0/Documentation/Manual/urp/2d-pixelperfect.html
- Aseprite FAQ (라이선스·소스 컴파일·상업적 사용): https://www.aseprite.org/faq/
- Unity Asset Store Terms of Service and EULA: https://unity.com/legal/as-terms
- Freesound FAQ (CC0·CC-BY·CC-BY-NC): https://freesound.org/help/faq/
- Kenney Support (CC0 라이선스): https://kenney.nl/support
- Steamworks 문서 — 콘텐츠 설문(AI 생성 콘텐츠 고지): https://partner.steamgames.com/doc/gettingstarted/contentsurvey
- Unity 스크립팅 API — AudioSource.PlayScheduled: https://docs.unity3d.com/ScriptReference/AudioSource.PlayScheduled.html
