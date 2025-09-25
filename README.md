# Strands Agent + Streamlit Integration

**Strands Agent를 위한 Streamlit 프론트엔드 통합 모범 사례**

이 애플리케이션은 Strands Agent의 스트리밍 응답을 Streamlit UI에서 처리하기 위한 **확장 가능하고 안정적인 아키텍처**를 제공합니다. 실시간 텍스트 스트리밍, 도구 사용 표시, 추론 과정 시각화 등 Strands Agent의 모든 기능을 Streamlit에서 완벽하게 활용할 수 있습니다.

## 🎯 주요 특징

### ✨ 완전한 Strands Agent 통합
- **실시간 스트리밍**: 텍스트 응답의 실시간 표시
- **도구 사용 시각화**: 계산기, 날씨 등 도구 실행 과정 표시
- **추론 과정 표시**: Chain of Thought 및 추론 단계 시각화
- **에러 처리**: 안정적인 예외 처리 및 사용자 알림

### 🏗️ 확장 가능한 아키텍처
- **이벤트 핸들러 시스템**: 새로운 이벤트 타입 쉽게 추가
- **모듈화된 구조**: UI, 생명주기, 추론 등 기능별 핸들러 분리
- **스레드 안전성**: Streamlit 컨텍스트에서 안전한 UI 업데이트
- **테스트 자동화**: 포괄적인 단위 테스트 및 통합 테스트

## 🚀 빠른 시작

### 설치 및 실행

```bash
# 저장소 클론
git clone <repository-url>
cd streamlit-sample

# 의존성 설치
uv sync

# 애플리케이션 실행
uv run streamlit run app.py
```

### AWS 자격 증명 설정

```bash
# AWS CLI 설정
aws configure

# 또는 환경 변수 설정
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

## 📋 사용법

1. **웹 브라우저**에서 `http://localhost:8501` 접속
2. **채팅 입력창**에 질문 입력
3. **실시간 응답** 확인:
   - 텍스트 스트리밍
   - 도구 사용 과정
   - 추론 단계 (Chain of Thought)

### 예시 질문

```
계산: "25 * 4 + 10은 얼마야?"
날씨: "서울 날씨 어때?"
추론: "복잡한 수학 문제를 단계별로 풀어줘"
```

## 🏛️ 아키텍처

### 핵심 컴포넌트

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   BedrockAgent   │    │  Strands Agent  │
│   Frontend      │◄──►│   (Coordinator)  │◄──►│   (Backend)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│  Event Handler  │    │  Event Registry  │
│    System       │◄──►│   (Router)       │
└─────────────────┘    └──────────────────┘
```

### 이벤트 핸들러 시스템

| 핸들러 | 역할 | 우선순위 |
|--------|------|----------|
| `StreamlitUIHandler` | UI 업데이트 및 사용자 인터페이스 | 10 (높음) |
| `ReasoningHandler` | 추론 과정 처리 및 분석 | 30 |
| `LifecycleHandler` | 생명주기 이벤트 관리 | 50 |
| `LoggingHandler` | 구조화된 로깅 | 80 |
| `DebugHandler` | 디버깅 정보 수집 | 95 (낮음) |

## 📁 프로젝트 구조

```
streamlit-sample/
├── app.py                             # Streamlit 실행 진입점 (랩퍼)
├── pyproject.toml                     # 프로젝트 설정
├── requirements.txt                   # Python 의존성 (선택)
├── src/
│   └── streamlit_sample/
│       ├── __init__.py
│       ├── app.py                    # Streamlit UI 로직
│       ├── main.py                   # 콘솔 진입점 예시
│       ├── agents/
│       │   └── bedrock_agent.py      # Strands Agent 통합 및 조정
│       └── handlers/
│           ├── __init__.py
│           ├── event_handlers.py     # 이벤트 핸들러 아키텍처
│           ├── lifecycle_handlers.py # 생명주기/로깅 핸들러
│           └── ui_handlers.py        # Streamlit UI 전용 핸들러
└── tests/
    ├── test_streamlit_flow.py        # UI 플로우 테스트
    └── test_thread_safety.py         # 스레드 안전성 테스트
```

## 🔧 개발자 가이드

### 새로운 이벤트 핸들러 추가

```python
from streamlit_sample.handlers.event_handlers import EventHandler

class CustomHandler(EventHandler):
    @property
    def priority(self) -> int:
        return 60  # 우선순위 설정
    
    def can_handle(self, event_type: str) -> bool:
        return event_type == "custom_event"
    
    def handle(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # 이벤트 처리 로직
        return {"processed": True}

# BedrockAgent에 등록
agent.event_registry.register(CustomHandler())
```

### 테스트 실행

```bash
# UI 플로우 테스트
python tests/test_streamlit_flow.py

# 스레드 안전성 테스트
python tests/test_thread_safety.py

# 전체 테스트 (pytest 설치 시)
pytest tests -v
```

## 🛡️ 안정성 특징

### 스레드 안전성
- **메인 스레드 UI 업데이트**: Streamlit 컨텍스트에서만 UI 조작
- **워커 스레드 격리**: 백그라운드 처리와 UI 업데이트 분리
- **예외 안전성**: 핸들러 에러 시에도 스트림 계속 진행

### 에러 처리
- **이중 안전장치**: EventRegistry + app.py 레벨 예외 처리
- **사용자 친화적 에러 표시**: 기술적 오류를 이해하기 쉽게 표시
- **자동 복구**: 일시적 오류 후 자동으로 정상 동작 재개

### 리소스 관리
- **이벤트 큐 정리**: 스트림 종료 후 남은 이벤트 자동 정리
- **메모리 효율성**: 불필요한 이벤트 누적 방지
- **상태 초기화**: 각 대화마다 깔끔한 상태 시작

## 🎨 커스터마이징

### UI 테마 변경

```python
# src/streamlit_sample/app.py에서 Streamlit 설정 수정
st.set_page_config(
    page_title="Custom Agent Chat",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### 새로운 도구 추가

```python
# src/streamlit_sample/agents/bedrock_agent.py에서 도구 추가
from strands.tools import tool

@tool
def custom_tool(input_data: str) -> str:
    """커스텀 도구 설명"""
    return f"처리 결과: {input_data}"

# Agent 생성 시 도구 등록
self.agent = Agent(
    model=model_id,
    tools=[calculator, weather, custom_tool],
    callback_handler=self._callback_handler
)
```

## 📊 성능 최적화

### 권장 설정
- **Python**: 3.12+
- **메모리**: 최소 2GB RAM
- **CPU**: 멀티코어 권장 (스레드 처리용)

### 모니터링
- 이벤트 처리 로그 확인
- 핸들러 에러 모니터링
- 스트림 응답 시간 측정

## 🤝 기여하기

1. **Fork** 저장소
2. **Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
4. **브랜치 푸시** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 개발 가이드라인
- 새로운 핸들러는 테스트와 함께 제출
- 기존 테스트가 모두 통과해야 함
- 코드 스타일: PEP 8 준수
- 문서화: 새로운 기능은 README 업데이트

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🆘 문제 해결

### 자주 발생하는 문제

**Q: "missing ScriptRunContext" 경고가 나타남**
A: 핸들러가 워커 스레드에서 호출되고 있습니다. 메인 스레드에서만 UI 업데이트가 이루어지는지 확인하세요.

**Q: 스트림이 중간에 멈춤**
A: 핸들러에서 예외가 발생했을 가능성이 있습니다. 에러 메시지를 확인하고 해당 핸들러를 점검하세요.

**Q: UI가 업데이트되지 않음**
A: placeholder 설정이 올바른지 확인하고, `test_streamlit_flow.py`를 실행하여 핸들러 동작을 검증하세요.

### 지원

- **이슈 리포트**: GitHub Issues
- **문서**: 이 README 및 코드 주석
- **테스트**: 자동화된 테스트 스위트 활용

---

**Strands Agent + Streamlit의 완벽한 통합을 경험해보세요!** 🚀
