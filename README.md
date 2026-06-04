# 🚽 HUFS 스마트 캠퍼스: 인문과학관 화장실 실시간 현황 프로토타입

한국외국어대학교 인문과학관 화장실의 칸수 증설이 불가능한 상황에서, **무선 개폐 센서 정보 시각화**와 **오프라인 바닥 테이프(Nudge)**를 연계하여 지각 불안감을 해소하고 동선 분산을 유도하는 스마트 캠퍼스 인프라 대시보드 프로토타입입니다.

## 🚀 깃허브(GitHub) 업로드 및 배포 방법 (Streamlit Cloud)

이 레포지토리는 **Streamlit Community Cloud**에 무료로 배포하여 스마트폰(한국외대 캠퍼스 앱 링크 등) 및 발표용 모니터 화면으로 즉시 시연할 수 있도록 최적화되어 있습니다.

### 1단계: 내 깃허브(GitHub)에 소스 올리기
1. 깃허브(https://github.com)에 로그인하고 새로운 레포지토리(New Repository)를 생성합니다. (예: `hufs-smart-toilet`)
2. 생성된 레포지토리에 이 폴더의 다음 파일들을 업로드합니다:
   - `app.py`: 메인 대시보드 및 시뮬레이터 프로그램
   - `requirements.txt`: 배포에 필요한 패키지 명세서
   - `README.md`: 설명 문서

> 💡 **깃 배시(Git Bash) 또는 터미널을 이용할 경우:**
> ```bash
> git init
> git add .
> git commit -m "Initial commit of HUFS Smart Toilet app"
> git branch -M main
> git remote add origin https://github.com/사용자아이디/hufs-smart-toilet.git
> git push -u origin main
> ```

---

### 2단계: Streamlit Community Cloud에 무료 배포하기
1. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 로그인합니다. (GitHub 계정으로 로그인 가능)
2. **"Create app"** 또는 **"New app"** 버튼을 클릭합니다.
3. 배포 설정 입력창에 다음과 같이 설정합니다:
   - **Repository**: `사용자아이디/hufs-smart-toilet` (선택 가능 목록에 나타남)
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **"Deploy!"** 버튼을 클릭합니다.
5. 약 1~2분 정도 패키지 설치 및 빌드가 완료되면 전 세계 어디서나 모바일/PC로 접속 가능한 공개 공유 링크(`https://hufs-smart-toilet.streamlit.app/` 등)가 생성됩니다!

---

## 🔬 실측 데이터 반영 방법 (내일 실측 후 설정)

내일 실제 인문과학관 2층 여자 화장실의 구조를 실측하신 뒤, `app.py` 코드 최상단에 있는 아래 상수 영역의 값만 에디터로 변경하여 깃허브에 다시 커밋(Commit)해 주시면 배포된 웹사이트에 자동으로 실시간 반영됩니다:

```python
# =================================================================
# 🔬 HUFS HUMANITIES BUILDING FIELD MEASUREMENT CONSTANTS (FOR TOMORROW)
# =================================================================
TOTAL_CHAMBERS = 8            # 인문과학관 2층 여자화장실 실측 칸 개수 (기본 8칸 고정)
AVG_USAGE_TIME_MIN = 1.5      # 1인당 실제 측정된 평균 이용 시간 T (분)
PEOPLE_PER_TILE_ZONE = 3      # 복도 바닥 타일 1개 Zone당 대기 가능 인원 (명)
WAIT_TIME_ALPHA_MIN = 0.5     # 대기 지연 보정상수 alpha (분)
# =================================================================
```

---

## 🎨 주요 시연 기능 (발표 활용용)
- **발표용 시나리오 단축 버튼**: 왼쪽 사이드바에서 시나리오(여유/혼잡/만석 및 바닥테이프 연계/점검 중)를 선택하면 실시간 센서 및 대기 상태가 단번에 전환되어 조작 실수를 막아줍니다.
- **GPS 지오펜싱 시뮬레이터**: 캠퍼스(인문관 반경 50m) 내부에서만 조회할 수 있는 넛지 보안을 시각화합니다. (사이드바의 거리 슬라이더를 50m 초과로 조절 시 화면이 불투명하게 잠기며 안내문 노출)
- **복도 대기선(Zone A/B/C) 연동**: 대기자가 늘어남에 따라 "3층으로 우회해 주세요" 등 오프라인 바닥 테이프 가이드와 동기화된 메시지를 동적으로 뿌려줍니다.
