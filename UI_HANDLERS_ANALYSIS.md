# UI Handlers 분석 및 리팩토링 전략

## 📊 현재 상태 분석

### 파일 구조
- **파일 크기**: 607줄 - 단일 파일로는 상당히 큰 규모
- **주요 구성요소**:
  - 4개 유틸리티 함수 (parse_model_response, strip_partial_thinking, etc.)
  - StreamlitUIState 클래스 (상태 관리)
  - StreamlitUIHandler 클래스 (이벤트 처리) - 20개+ 메서드

### 🔍 문제점 식별

#### 1. 단일 책임 원칙(SRP) 위반
```
StreamlitUIHandler가 처리하는 책임들:
├── Reasoning 처리 (4개 메서드)
├── Tool Use 처리 (7개 메서드) 
├── Message/Data 처리 (3개 메서드)
├── UI 상태 관리 (6개 메서드)
└── 유틸리티 기능 (5개 메서드)
```

#### 2. 높은 결합도
- UI 상태와 이벤트 처리 로직이 강하게 결합
- Streamlit 특화 코드와 비즈니스 로직 혼재
- 테스트하기 어려운 구조

#### 3. 코드 중복 및 복잡성
- placeholder 관리 로직 중복
- 상태 업데이트 패턴 반복
- 긴 메서드들 (일부 50줄+)

## 🎯 리팩토링 전략

### Phase 1: 책임 분리 (Separation of Concerns)

```
현재: ui_handlers.py (607줄)
↓
리팩토링 후:
├── ui/
│   ├── __init__.py
│   ├── state.py           # StreamlitUIState + 상태 관리
│   ├── reasoning.py       # Reasoning UI 처리
│   ├── tools.py          # Tool Use UI 처리  
│   ├── messages.py       # Message/Data UI 처리
│   ├── placeholders.py   # Placeholder 관리
│   └── utils.py          # 유틸리티 함수들
└── ui_handlers.py        # 메인 핸들러 (조정자 역할)
```

### Phase 2: 클래스 분해 전략

#### A. UI 컴포넌트별 분리
```python
# reasoning.py
class ReasoningUIManager:
    def handle_reasoning_text(self, event)
    def ensure_reasoning_status(self)
    def show_reasoning_widget(self)
    def finalize_reasoning(self)

# tools.py  
class ToolUIManager:
    def handle_tool_use(self, event)
    def handle_tool_result(self, event)
    def render_tool_entry(self, tool_entry)
    def ensure_tool_placeholder(self, tool_entry)

# messages.py
class MessageUIManager:
    def handle_data_stream(self, event)
    def handle_final_result(self, event)
    def update_response_placeholder(self, text)
```

#### B. 상태 관리 개선
```python
# state.py
class UIState:
    reasoning: ReasoningState
    tools: ToolState  
    messages: MessageState
    placeholders: PlaceholderState

class ReasoningState:
    expander: Optional[st.expander]
    status: Optional[st.status]
    content_placeholder: Optional[st.empty]
    text: str = ""
```

### Phase 3: 인터페이스 설계

#### A. 매니저 인터페이스
```python
class UIManager(Protocol):
    def can_handle(self, event_type: str) -> bool
    def handle(self, event: Dict[str, Any]) -> None
    def finalize(self) -> None
```

#### B. 조정자 패턴
```python
class StreamlitUIHandler(EventHandler):
    def __init__(self, ui_state: UIState):
        self.managers = [
            ReasoningUIManager(ui_state.reasoning),
            ToolUIManager(ui_state.tools),
            MessageUIManager(ui_state.messages)
        ]
    
    def handle(self, event):
        for manager in self.managers:
            if manager.can_handle(event_type):
                manager.handle(event)
```

#### C. 유틸리티 모듈화
```python
# utils.py
class TextProcessor:
    @staticmethod
    def parse_model_response(raw_text)
    @staticmethod  
    def strip_partial_thinking(raw_text)

class ValueNormalizer:
    @staticmethod
    def normalize_tool_value(value)
    @staticmethod
    def render_tool_value(value, as_json)
```

### 🚀 마이그레이션 전략

#### Step 1: 유틸리티 함수 분리 (위험도: 낮음)
- 순수 함수들을 별도 모듈로 이동
- 기존 import 유지하여 호환성 보장

#### Step 2: 상태 클래스 분해 (위험도: 중간)
- StreamlitUIState를 도메인별로 분리
- 점진적 마이그레이션 (기존 인터페이스 유지)

#### Step 3: 핸들러 메서드 분리 (위험도: 높음)
- 각 도메인별 매니저 클래스 생성
- 메인 핸들러는 조정자 역할로 축소

#### Step 4: 테스트 및 검증 (위험도: 낮음)
- 각 컴포넌트별 단위 테스트 추가
- 통합 테스트로 전체 플로우 검증

### 📈 기대 효과

1. **가독성**: 607줄 → 각 파일 100-150줄로 분산
2. **유지보수성**: 도메인별 독립적 수정 가능
3. **테스트 용이성**: 각 매니저별 단위 테스트 가능
4. **확장성**: 새로운 UI 컴포넌트 추가 용이
5. **재사용성**: UI 매니저들을 다른 프로젝트에서 재사용 가능

### ⚠️ 주의사항

- **점진적 리팩토링**: 한 번에 모든 것을 바꾸지 말고 단계적 접근
- **하위 호환성**: 기존 API 인터페이스 유지
- **테스트 우선**: 리팩토링 전 현재 동작에 대한 테스트 작성
- **성능 고려**: 객체 생성 오버헤드 최소화

## 🔄 사용자 질문 → 응답 채워지는 로직 분석

### 실제 이벤트 로그 기반 분석

#### **Tool Use 시나리오 완전 분석** (2+2 계산 예시)

```
Phase 1: 초기화 및 Tool 실행
├── init_event_loop → start → start_event_loop
├── messageStart (assistant)
├── contentBlockStart (toolUse: calculator)
├── contentBlockDelta (tool input 스트리밍: '{"e' → 'xp' → 'ression": "2+2"}')
├── contentBlockStop → messageStop (tool_use)
└── message (assistant with toolUse)

Phase 2: Tool Result 처리
├── message (user with toolResult: "4")
├── start → start → start_event_loop (새 사이클)
└── messageStart (assistant)

Phase 3: 최종 응답 생성
├── contentBlockDelta (text 스트리밍: '2' → '+2의' → ' 계산 ' → '결과는 **' → '4**입니다.')
├── contentBlockStop → messageStop (end_turn)
├── message (assistant with final text)
└── result (AgentResult with metrics)
```

### 전체 플로우 개요

```
사용자 입력 
    ↓
UI Placeholder 준비 (4개)
    ↓
Agent 백그라운드 실행 + 이벤트 큐
    ↓
실시간 이벤트 스트리밍
    ├── Phase 1: Tool 실행 (contentBlockDelta + current_tool_use)
    ├── Phase 2: Tool 결과 처리 (toolResult)
    ├── Phase 3: 최종 응답 (data + delta 스트리밍)
    └── reasoningContent → 🧠 Expander 생성 (해당 시)
    ↓
result 이벤트 → 스트리밍 종료
    ↓
finalize_response() → 최종 UI 정리
    ↓
세션 히스토리에 응답 저장
```

### 🔍 **이벤트 타입별 상세 분석** (Strands API 기반)

#### **1. 생명주기 이벤트**
```python
# 초기화 및 시작
{'init_event_loop': True}           # 이벤트 루프 초기화
{'start': True}                     # 새로운 사이클 시작
{'start_event_loop': True}          # 이벤트 루프 시작

# 완료
{'result': AgentResult(...)}        # 최종 결과 (metrics 포함)
```

#### **2. Bedrock 원시 스트리밍 이벤트** (event 필드 내부)
```python
# 메시지 시작/종료
{'event': {'messageStart': {'role': 'assistant'}}}
{'event': {'messageStop': {'stopReason': 'tool_use|end_turn'}}}

# 콘텐츠 블록 관리
{'event': {'contentBlockStart': {
    'start': {'toolUse': {'toolUseId': 'xxx', 'name': 'calculator'}},
    'contentBlockIndex': 0
}}}
{'event': {'contentBlockStop': {'contentBlockIndex': 0}}}

# 콘텐츠 델타 (실제 스트리밍 데이터)
{'event': {'contentBlockDelta': {
    'delta': {'text': '텍스트 조각'}, 
    'contentBlockIndex': 0
}}}
{'event': {'contentBlockDelta': {
    'delta': {'toolUse': {'input': 'JSON 조각'}}, 
    'contentBlockIndex': 0
}}}

# 메타데이터
{'event': {'metadata': {
    'usage': {'inputTokens': 517, 'outputTokens': 22, 'totalTokens': 539},
    'metrics': {'latencyMs': 1708}
}}}
```

#### **3. Strands 처리된 이벤트** (풍부한 컨텍스트 포함)
```python
# 텍스트 스트리밍 (data 이벤트)
{'data': '텍스트 조각', 
 'delta': {'text': '텍스트 조각'}, 
 'agent': <Agent>, 
 'event_loop_cycle_id': UUID('...'),
 'messages': [...],  # 전체 대화 히스토리
 'tool_config': {...},  # 사용 가능한 도구들
 'model': <BedrockModel>,
 'system_prompt': None,
 'event_loop_parent_cycle_id': UUID('...')}

# Tool 사용 (current_tool_use 이벤트)
{'current_tool_use': {
    'toolUseId': 'tooluse_xxx', 
    'name': 'calculator', 
    'input': {'expression': '2+2'}  # 완전히 파싱된 input
}, 
 'delta': {'toolUse': {'input': 'JSON조각'}},  # 원시 델타도 포함
 'agent': <Agent>,
 'event_loop_cycle_id': UUID('...')}

# 메시지 완성
{'message': {
    'role': 'assistant', 
    'content': [{'text': '최종 응답 텍스트'}]
}}
{'message': {
    'role': 'user', 
    'content': [{'toolResult': {
        'toolUseId': 'tooluse_xxx', 
        'status': 'success', 
        'content': [{'text': '4'}]
    }}]
}}
```

#### **4. 추론 관련 이벤트** (Reasoning Models)
```python
# Strands API 문서에 따른 추론 이벤트들
{'reasoning': True}                          # 추론 이벤트 플래그
{'reasoningText': '추론 과정 텍스트'}         # 추론 텍스트 스트리밍
{'reasoning_signature': '추론 서명'}         # 추론 서명
{'redactedContent': '검열된 추론 내용'}      # 검열된 추론 내용

# 현재 구현에서 감지되는 형태 (SDK_UNKNOWN_MEMBER)
{'event': {'contentBlockDelta': {
    'delta': {'SDK_UNKNOWN_MEMBER': {'name': 'reasoningContent'}},
    'contentBlockIndex': 0
}}}
```

#### **5. 도구 실행 패턴 분석**

**A. Tool Input 스트리밍 (비효율적)**
```python
# JSON이 조각별로 스트리밍됨
{'event': {'contentBlockDelta': {'delta': {'toolUse': {'input': '{"e'}}}}}      # '{"e'
{'event': {'contentBlockDelta': {'delta': {'toolUse': {'input': 'xp'}}}}}       # 'xp'  
{'event': {'contentBlockDelta': {'delta': {'toolUse': {'input': 'ression": "2+2"}'}}}}} # 'ression": "2+2"}'

# 문제점: 불완전한 JSON으로 파싱 불가, UI 업데이트 비효율
```

**B. Strands 처리된 Tool 이벤트 (효율적)**
```python
# 완전히 파싱된 input과 함께 제공
{'current_tool_use': {
    'toolUseId': 'tooluse_xxx', 
    'name': 'calculator', 
    'input': {'expression': '2+2'}  # 완전히 파싱됨
}}

# 장점: 즉시 UI 표시 가능, 파싱 오류 없음
```

### 🎯 **Strands API 기반 개선 전략**

#### **1. 이벤트 우선순위 매트릭스**

| 이벤트 타입 | 원시 (event) | Strands 처리 | 우선순위 | 사용 목적 |
|------------|-------------|-------------|---------|----------|
| 텍스트 스트리밍 | `contentBlockDelta.text` | `data` | **Strands** | 실시간 UI 업데이트 |
| Tool 사용 | `contentBlockDelta.toolUse` | `current_tool_use` | **Strands** | 완전한 input 표시 |
| 메시지 완성 | `messageStop` | `message` | **Both** | 상태 전환 감지 |
| 추론 과정 | `SDK_UNKNOWN_MEMBER` | `reasoningText` | **Both** | 추론 위젯 표시 |
| 메타데이터 | `metadata` | - | **원시** | 토큰/레이턴시 표시 |

#### **2. 스마트 이벤트 라우팅**

```python
class StrandsEventRouter:
    """Strands API 기반 이벤트 라우팅"""
    
    def route_event(self, event: Dict[str, Any]) -> List[ProcessedEvent]:
        # 1. Strands 처리된 이벤트 우선 처리
        if "data" in event:
            return [TextStreamEvent(content=event["data"], context=event)]
        
        if "current_tool_use" in event:
            return [ToolUseEvent(
                tool_id=event["current_tool_use"]["toolUseId"],
                name=event["current_tool_use"]["name"],
                input=event["current_tool_use"]["input"]
            )]
        
        # 2. 원시 이벤트는 보조적으로 처리
        if "event" in event:
            return self._process_bedrock_event(event["event"])
        
        # 3. 생명주기 이벤트
        if "result" in event:
            return [CompletionEvent(result=event["result"])]
            
        return []
    
    def _process_bedrock_event(self, bedrock_event: Dict) -> List[ProcessedEvent]:
        """원시 Bedrock 이벤트 처리"""
        if "messageStart" in bedrock_event:
            return [MessageStartEvent(role=bedrock_event["messageStart"]["role"])]
        
        if "contentBlockStart" in bedrock_event:
            start_data = bedrock_event["contentBlockStart"]["start"]
            if "toolUse" in start_data:
                return [ToolStartEvent(
                    tool_id=start_data["toolUse"]["toolUseId"],
                    name=start_data["toolUse"]["name"]
                )]
        
        if "metadata" in bedrock_event:
            return [MetadataEvent(
                usage=bedrock_event["metadata"]["usage"],
                metrics=bedrock_event["metadata"]["metrics"]
            )]
        
        return []
```

#### **3. 추론 이벤트 통합 처리**

```python
class ReasoningEventProcessor:
    """추론 이벤트 통합 처리"""
    
    def process_reasoning(self, event: Dict[str, Any]) -> Optional[ReasoningEvent]:
        # Strands 표준 추론 이벤트
        if "reasoningText" in event:
            return ReasoningEvent(
                content=event["reasoningText"],
                type="standard"
            )
        
        # SDK_UNKNOWN_MEMBER 형태의 추론 감지
        if "event" in event:
            bedrock_event = event["event"]
            if "contentBlockDelta" in bedrock_event:
                delta = bedrock_event["contentBlockDelta"]["delta"]
                if "SDK_UNKNOWN_MEMBER" in delta:
                    unknown = delta["SDK_UNKNOWN_MEMBER"]
                    if unknown.get("name") == "reasoningContent":
                        return ReasoningEvent(
                            content="",  # 내용은 별도로 스트리밍됨
                            type="unknown_member",
                            detected=True
                        )
        
        return None
```

#### **4. 성능 최적화된 UI 업데이트**

```python
class OptimizedUIUpdater:
    """Strands 이벤트 기반 최적화된 UI 업데이트"""
    
    def __init__(self):
        self.text_buffer = ""
        self.last_update_time = 0
        self.update_threshold_ms = 50  # 50ms 디바운싱
    
    def handle_text_stream(self, event: TextStreamEvent):
        """텍스트 스트리밍 최적화"""
        self.text_buffer += event.content
        
        current_time = time.time() * 1000
        if current_time - self.last_update_time > self.update_threshold_ms:
            self._update_text_ui(self.text_buffer)
            self.last_update_time = current_time
    
    def handle_tool_use(self, event: ToolUseEvent):
        """Tool 사용 즉시 표시 (디바운싱 없음)"""
        self._show_tool_immediately(event.name, event.input)
    
    def handle_reasoning_detected(self, event: ReasoningEvent):
        """추론 감지 즉시 위젯 표시"""
        if event.detected:
            self._show_reasoning_widget()
```

### 📊 **API 호환성 매트릭스**

| 기능 | 현재 구현 | Strands API 표준 | 호환성 | 개선 방향 |
|------|----------|-----------------|--------|----------|
| 텍스트 스트리밍 | `data` 이벤트 | ✅ 표준 | 완전 | 유지 |
| Tool 사용 | `current_tool_use` | ✅ 표준 | 완전 | 유지 |
| 추론 과정 | `SDK_UNKNOWN_MEMBER` | `reasoningText` | 부분 | 표준 API 대응 |
| 메시지 완성 | `message` 이벤트 | ✅ 표준 | 완전 | 유지 |
| 생명주기 | 커스텀 이벤트 | Hook 시스템 | 부분 | Hook 시스템 도입 |

이 분석을 통해 현재 구현이 Strands API와 얼마나 일치하는지, 그리고 어떤 부분을 개선해야 하는지 명확히 파악할 수 있습니다.

### 🎯 **현재 UI 처리의 문제점**

#### **1. 이벤트 중복 처리**
- **원시 이벤트**: `{'event': {'contentBlockDelta': ...}}`
- **Strands 이벤트**: `{'data': ..., 'delta': ...}`
- **문제**: 같은 내용이 다른 형태로 2번 처리됨

#### **2. Tool Input 스트리밍 비효율성**
```python
# 현재: JSON 조각마다 UI 업데이트
'{"e' → 'xp' → 'ression": "2+2"}'

# 문제: 불완전한 JSON으로 인한 파싱 오류 가능성
# 해결책: 완전한 input이 준비된 current_tool_use 이벤트만 사용
```

#### **3. 이벤트 타입 혼재**
- `event` 타입 내부에 다양한 하위 타입들이 중첩
- 핸들러에서 복잡한 조건문으로 분기 처리
- 타입 안전성 부족

### 🚀 **개선된 UI 처리 전략**

#### **Phase 1: 이벤트 타입 정규화**

```python
# 현재 문제적 구조
def _handle_event(self, event):
    event_data = event.get("event", {})
    if "contentBlockDelta" in event_data:
        delta_data = event_data["contentBlockDelta"]
        # 복잡한 중첩 처리...

# 개선된 구조
class EventTypeNormalizer:
    @staticmethod
    def normalize(event: Dict[str, Any]) -> List[NormalizedEvent]:
        """원시 이벤트를 정규화된 타입별 이벤트로 변환"""
        if "event" in event:
            return EventTypeNormalizer._normalize_bedrock_event(event["event"])
        elif "data" in event:
            return [TextStreamEvent(content=event["data"])]
        elif "current_tool_use" in event:
            return [ToolUseEvent(tool_data=event["current_tool_use"])]
        # ...

class TextStreamEvent:
    content: str
    
class ToolUseEvent:
    tool_id: str
    name: str
    input: Dict[str, Any]
    
class ToolResultEvent:
    tool_id: str
    result: Any
    status: str
```

#### **Phase 2: 스마트 이벤트 필터링**

```python
class EventFilter:
    """중복 이벤트 제거 및 우선순위 처리"""
    
    def __init__(self):
        self.seen_tool_inputs = set()
        self.text_buffer = ""
    
    def should_process(self, event: NormalizedEvent) -> bool:
        if isinstance(event, ToolInputStreamEvent):
            # JSON 조각 스트리밍은 무시, 완성된 input만 처리
            return False
        elif isinstance(event, ToolUseEvent):
            # 중복 tool use 이벤트 제거
            key = (event.tool_id, str(event.input))
            if key in self.seen_tool_inputs:
                return False
            self.seen_tool_inputs.add(key)
        return True
```

#### **Phase 3: 상태 기반 UI 업데이트**

```python
class ToolUIState:
    def __init__(self):
        self.active_tools: Dict[str, ToolEntry] = {}
        self.completed_tools: Dict[str, ToolEntry] = {}
    
    def start_tool(self, tool_id: str, name: str, input_data: Dict):
        """도구 시작 - 즉시 UI 표시"""
        entry = ToolEntry(id=tool_id, name=name, input=input_data, status="running")
        self.active_tools[tool_id] = entry
        self._render_tool_immediately(entry)
    
    def complete_tool(self, tool_id: str, result: Any):
        """도구 완료 - 상태 업데이트"""
        if tool_id in self.active_tools:
            entry = self.active_tools.pop(tool_id)
            entry.result = result
            entry.status = "complete"
            self.completed_tools[tool_id] = entry
            self._update_tool_display(entry)
```

#### **Phase 4: 예측적 UI 렌더링**

```python
class PredictiveUIRenderer:
    """이벤트 패턴을 기반으로 UI를 미리 준비"""
    
    def on_message_start(self, role: str):
        if role == "assistant":
            # Assistant 응답 시작 - placeholder 미리 준비
            self._prepare_response_area()
    
    def on_tool_block_start(self, tool_name: str):
        # Tool 사용 감지 즉시 UI 표시 (input 대기 없이)
        self._show_tool_placeholder(tool_name, status="preparing")
    
    def on_text_block_start(self):
        # 텍스트 응답 시작 - 스트리밍 준비
        self._prepare_text_streaming()
```

### 📊 **성능 최적화 전략**

#### **1. 이벤트 배칭**
```python
class EventBatcher:
    def __init__(self, batch_size=5, timeout_ms=100):
        self.batch = []
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms
    
    def add_event(self, event):
        self.batch.append(event)
        if len(self.batch) >= self.batch_size:
            self._flush_batch()
    
    def _flush_batch(self):
        # 배치된 이벤트들을 한 번에 처리
        optimized_events = self._optimize_batch(self.batch)
        for event in optimized_events:
            self._process_single_event(event)
        self.batch.clear()
```

#### **2. UI 업데이트 디바운싱**
```python
class UIUpdateDebouncer:
    def __init__(self, delay_ms=50):
        self.pending_updates = {}
        self.delay_ms = delay_ms
    
    def schedule_update(self, component_id: str, update_fn):
        # 빠른 연속 업데이트를 디바운싱
        if component_id in self.pending_updates:
            self.pending_updates[component_id].cancel()
        
        timer = threading.Timer(self.delay_ms / 1000, update_fn)
        self.pending_updates[component_id] = timer
        timer.start()
```

### 🎨 **향상된 사용자 경험**

#### **1. 진행 상황 시각화**
```python
class ProgressVisualizer:
    def show_tool_progress(self, tool_name: str, phase: str):
        phases = ["preparing", "executing", "processing", "complete"]
        current_index = phases.index(phase)
        
        # 진행률 표시: ████▒▒▒▒ 50%
        progress_bar = "█" * (current_index + 1) + "▒" * (len(phases) - current_index - 1)
        percentage = ((current_index + 1) / len(phases)) * 100
        
        return f"{tool_name}: {progress_bar} {percentage:.0f}%"
```

#### **2. 스마트 로딩 상태**
```python
class SmartLoadingStates:
    def get_loading_message(self, context: Dict) -> str:
        if context.get("tool_name") == "calculator":
            return "🧮 계산 중..."
        elif context.get("tool_name") == "weather":
            return "🌤️ 날씨 정보 조회 중..."
        elif context.get("has_reasoning"):
            return "🧠 추론 중..."
        else:
            return "💭 응답 생성 중..."
```

### 🔧 **리팩토링된 아키텍처**

```python
# 새로운 구조
class StreamlitUIOrchestrator:
    def __init__(self):
        self.event_normalizer = EventTypeNormalizer()
        self.event_filter = EventFilter()
        self.ui_managers = {
            'text': TextStreamManager(),
            'tools': ToolUIManager(),
            'reasoning': ReasoningUIManager(),
            'lifecycle': LifecycleUIManager()
        }
        self.progress_visualizer = ProgressVisualizer()
        self.update_debouncer = UIUpdateDebouncer()
    
    def handle_event(self, raw_event: Dict[str, Any]):
        # 1. 이벤트 정규화
        normalized_events = self.event_normalizer.normalize(raw_event)
        
        # 2. 필터링
        filtered_events = [e for e in normalized_events if self.event_filter.should_process(e)]
        
        # 3. 적절한 매니저에게 위임
        for event in filtered_events:
            manager = self._get_manager_for_event(event)
            if manager:
                self.update_debouncer.schedule_update(
                    f"{manager.__class__.__name__}_{event.id}",
                    lambda: manager.handle(event)
                )
```

### 🚀 **Strands Hook System 기반 리팩토링**

#### **1. 현재 Callback Handler vs Hook System**

| 현재 구현 | Strands Hook System | 장점 |
|----------|-------------------|------|
| `callback_handler=function` | `hooks=[HookProvider()]` | 타입 안전성 |
| 단일 콜백 함수 | 다중 Hook Provider | 모듈화 |
| 키워드 인자 기반 | 강타입 이벤트 | 명확한 인터페이스 |
| 수동 이벤트 분기 | 자동 이벤트 라우팅 | 코드 간소화 |

#### **2. Hook System 기반 아키텍처**

```python
# 현재 구조
class StreamlitUIHandler(EventHandler):
    def handle(self, event):
        if "data" in event:
            self._handle_data(event)
        elif "current_tool_use" in event:
            self._handle_tool_use(event)
        # ... 복잡한 분기

# Hook System 기반 구조
class StreamlitUIHooks(HookProvider):
    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(TextStreamEvent, self.handle_text_stream)
        registry.add_callback(ToolUseEvent, self.handle_tool_use)
        registry.add_callback(ReasoningEvent, self.handle_reasoning)
        registry.add_callback(CompletionEvent, self.handle_completion)
    
    def handle_text_stream(self, event: TextStreamEvent):
        """타입 안전한 텍스트 스트리밍 처리"""
        self.ui_state.response_placeholder.markdown(f"{event.content}▌")
    
    def handle_tool_use(self, event: ToolUseEvent):
        """타입 안전한 도구 사용 처리"""
        self._render_tool_entry(event.tool_id, event.name, event.input)
```

#### **3. 이벤트 타입 정의**

```python
@dataclass
class TextStreamEvent(HookEvent):
    """텍스트 스트리밍 이벤트"""
    content: str
    is_complete: bool = False

@dataclass
class ToolUseEvent(HookEvent):
    """도구 사용 이벤트"""
    tool_id: str
    name: str
    input: Dict[str, Any]
    status: Literal["starting", "running", "complete"] = "starting"

@dataclass
class ReasoningEvent(HookEvent):
    """추론 과정 이벤트"""
    content: str
    reasoning_type: Literal["thinking", "reflection", "analysis"]
    is_complete: bool = False

@dataclass
class CompletionEvent(HookEvent):
    """완료 이벤트"""
    result: AgentResult
    metrics: EventLoopMetrics
```

#### **4. 모듈화된 Hook Providers**

```python
class ReasoningUIHooks(HookProvider):
    """추론 UI 전용 Hook Provider"""
    
    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(ReasoningEvent, self.handle_reasoning)
        registry.add_callback(CompletionEvent, self.finalize_reasoning)
    
    def handle_reasoning(self, event: ReasoningEvent):
        if not self.reasoning_widget:
            self._create_reasoning_widget()
        self._update_reasoning_content(event.content)

class ToolUIHooks(HookProvider):
    """도구 UI 전용 Hook Provider"""
    
    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(ToolUseEvent, self.handle_tool_use)
        registry.add_callback(ToolResultEvent, self.handle_tool_result)
    
    def handle_tool_use(self, event: ToolUseEvent):
        self._show_tool_execution(event.name, event.input)

class TextUIHooks(HookProvider):
    """텍스트 UI 전용 Hook Provider"""
    
    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(TextStreamEvent, self.handle_text_stream)
    
    def handle_text_stream(self, event: TextStreamEvent):
        self._update_text_display(event.content, event.is_complete)
```

#### **5. Agent 통합**

```python
# 현재 방식
agent = Agent(
    model=model_id,
    tools=[calculator, weather],
    callback_handler=self._callback_handler
)

# Hook System 방식
agent = Agent(
    model=model_id,
    tools=[calculator, weather],
    hooks=[
        ReasoningUIHooks(ui_state.reasoning),
        ToolUIHooks(ui_state.tools),
        TextUIHooks(ui_state.text),
        MetricsHooks(ui_state.metrics)
    ]
)
```

### 📋 **마이그레이션 로드맵**

#### **Phase 1: Hook System 도입 준비**
1. **이벤트 타입 정의**: 현재 이벤트를 강타입 Hook Event로 변환
2. **Hook Provider 인터페이스**: 기존 핸들러를 Hook Provider로 래핑
3. **호환성 레이어**: 기존 callback_handler와 Hook System 병행 지원

#### **Phase 2: 점진적 마이그레이션**
1. **UI 컴포넌트별 Hook Provider 생성**: Reasoning, Tool, Text 등
2. **이벤트 라우팅 개선**: 타입 기반 자동 라우팅
3. **테스트 및 검증**: 기존 기능과 동일한 동작 확인

#### **Phase 3: 완전 전환**
1. **Legacy Callback Handler 제거**: Hook System으로 완전 전환
2. **성능 최적화**: Hook System의 이점 활용
3. **확장성 개선**: 새로운 Hook Provider 쉽게 추가 가능

### 🎯 **최종 아키텍처 비전**

```python
class StreamlitApp:
    def __init__(self):
        # UI 상태 관리
        self.ui_state = StreamlitUIState()
        
        # Hook Providers (모듈화됨)
        self.hooks = [
            ReasoningUIHooks(self.ui_state),
            ToolUIHooks(self.ui_state),
            TextUIHooks(self.ui_state),
            MetricsUIHooks(self.ui_state),
            LifecycleUIHooks(self.ui_state)
        ]
        
        # Agent (Hook System 사용)
        self.agent = Agent(
            model=model_id,
            tools=[calculator, weather],
            hooks=self.hooks
        )
    
    async def process_user_input(self, prompt: str):
        """사용자 입력 처리 - Hook System이 자동으로 UI 업데이트"""
        async for event in self.agent.stream_async(prompt):
            # Hook System이 자동으로 적절한 Provider에게 이벤트 전달
            # 더 이상 수동 이벤트 분기 불필요
            pass
```

이 Hook System 기반 접근법을 통해 현재의 복잡한 callback handler를 더 모듈화되고 타입 안전한 구조로 전환할 수 있습니다.

### 단계별 상세 분석 (실제 로그 기반)

#### 1️⃣ 사용자 입력 단계
```python
# app.py:96
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
```
- 사용자 입력: "2+2를 계산해주세요."
- 세션 상태의 메시지 히스토리에 사용자 메시지 추가

#### 2️⃣ UI 준비 단계
```python
# app.py:102-118 - 4개의 전용 placeholder 생성
message_container = st.container()
status_placeholder = message_container.empty()      # 상태 표시
tool_placeholder = message_container.empty()        # 도구 사용 표시
chain_placeholder = message_container.empty()       # 추론 과정 표시
response_placeholder = message_container.empty()    # 최종 응답 표시
```

#### 3️⃣ Agent 첫 번째 사이클 (Tool 실행)
```python
# 생명주기 이벤트
{'init_event_loop': True}
{'start': True}
{'start_event_loop': True}

# Tool 사용 시작
{'event': {'messageStart': {'role': 'assistant'}}}
{'event': {'contentBlockStart': {'start': {'toolUse': {'toolUseId': 'tooluse_AoRsts_HT72wn3bG4BsPIg', 'name': 'calculator'}}}}}

# Tool Input 스트리밍 (JSON 조각별로 전송)
{'event': {'contentBlockDelta': {'delta': {'toolUse': {'input': '{"e'}}}}}      # '{"e'
{'event': {'contentBlockDelta': {'delta': {'toolUse': {'input': 'xp'}}}}}       # 'xp'  
{'event': {'contentBlockDelta': {'delta': {'toolUse': {'input': 'ression": "2+2"}'}}}}} # 'ression": "2+2"}'

# Strands 처리된 완전한 Tool 이벤트
{'current_tool_use': {'toolUseId': 'tooluse_AoRsts_HT72wn3bG4BsPIg', 'name': 'calculator', 'input': {'expression': '2+2'}}}

# Tool 실행 완료
{'event': {'contentBlockStop': {'contentBlockIndex': 0}}}
{'event': {'messageStop': {'stopReason': 'tool_use'}}}
{'message': {'role': 'assistant', 'content': [{'toolUse': {...}}]}}
```

#### 4️⃣ Tool 결과 처리
```python
# Tool 결과 주입
{'message': {'role': 'user', 'content': [{'toolResult': {'toolUseId': 'tooluse_AoRsts_HT72wn3bG4BsPIg', 'status': 'success', 'content': [{'text': '4'}]}}]}}
```

#### 5️⃣ Agent 두 번째 사이클 (최종 응답)
```python
# 새로운 사이클 시작
{'start': True}
{'start': True}  # 중복 발생
{'start_event_loop': True}
{'event': {'messageStart': {'role': 'assistant'}}}

# 텍스트 응답 스트리밍
{'event': {'contentBlockDelta': {'delta': {'text': '2'}}}}
{'data': '2', 'delta': {'text': '2'}, 'messages': [...]}  # Strands 풍부한 컨텍스트

{'event': {'contentBlockDelta': {'delta': {'text': '+2의'}}}}
{'data': '+2의', 'delta': {'text': '+2의'}, 'messages': [...]}

{'event': {'contentBlockDelta': {'delta': {'text': ' 계산 '}}}}
{'data': ' 계산 ', 'delta': {'text': ' 계산 '}, 'messages': [...]}

{'event': {'contentBlockDelta': {'delta': {'text': '결과는 **'}}}}
{'data': '결과는 **', 'delta': {'text': '결과는 **'}, 'messages': [...]}

{'event': {'contentBlockDelta': {'delta': {'text': '4**입니다.'}}}}
{'data': '4**입니다.', 'delta': {'text': '4**입니다.'}, 'messages': [...]}
```

#### 6️⃣ 완료 및 메타데이터
```python
# 응답 완료
{'event': {'contentBlockStop': {'contentBlockIndex': 0}}}
{'event': {'messageStop': {'stopReason': 'end_turn'}}}
{'event': {'metadata': {'usage': {'inputTokens': 517, 'outputTokens': 22, 'totalTokens': 539}, 'metrics': {'latencyMs': 1708}}}}

# 최종 메시지
{'message': {'role': 'assistant', 'content': [{'text': '2+2의 계산 결과는 **4**입니다.'}]}}

# 최종 결과 (풍부한 메트릭스 포함)
{'result': AgentResult(
    stop_reason='end_turn',
    message={'role': 'assistant', 'content': [{'text': '2+2의 계산 결과는 **4**입니다.'}]},
    metrics=EventLoopMetrics(
        cycle_count=2,
        tool_metrics={'calculator': ToolMetrics(call_count=1, success_count=1, total_time=0.0008788)},
        accumulated_usage={'inputTokens': 967, 'outputTokens': 75, 'totalTokens': 1042}
    )
)}
```

#### 7️⃣ UI 최종 정리
```python
# app.py:147-154 - finalize_response 호출
for handler in st.session_state.agent.event_registry._handlers:
    if hasattr(handler, "finalize_response"):
        assistant_message = handler.finalize_response()
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
```

## 🎯 핵심 아키텍처 특징

### 스레드 분리 설계
- **백그라운드 스레드**: Strands Agent 실행
- **메인 스레드**: Streamlit UI 업데이트
- **큐 기반 통신**: 스레드 간 안전한 이벤트 전달

### 실시간 UI 업데이트
- **스트리밍 텍스트**: 토큰 단위로 실시간 표시 (▌ 커서 효과)
- **상태 표시**: 추론/도구 사용 진행 상황 실시간 업데이트
- **점진적 렌더링**: 각 컴포넌트별 독립적 업데이트

### 이벤트 기반 아키텍처
- **이벤트 타입별 처리**: data, reasoningText, tool_use, tool_result 등
- **핸들러 체인**: 우선순위 기반 이벤트 처리
- **상태 관리**: UI 상태와 비즈니스 로직 분리

이 분석을 통해 현재 시스템의 복잡성과 리팩토링의 필요성을 명확히 파악할 수 있으며, 제안된 전략을 통해 더 유지보수 가능한 구조로 개선할 수 있습니다.
