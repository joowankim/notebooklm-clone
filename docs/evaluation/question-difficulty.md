# 질문 난이도 분류 (Question Difficulty Classification)

## 개요

질문 난이도 분류는 합성 테스트 데이터셋의 각 질문을 4가지 난이도 수준으로 자동 분류하는 기능이다. 이를 통해 검색 시스템의 성능을 난이도별로 세분화하여 분석할 수 있다.

RAG 시스템은 단순한 사실 확인 질문부터 복잡한 추론 질문까지 다양한 유형의 질문을 처리해야 한다. 전체 평균 메트릭만으로는 어떤 유형의 질문에서 검색 품질이 떨어지는지 파악하기 어렵다. 난이도별 메트릭 분류는 다음과 같은 질문에 답한다:

- 검색 시스템이 어떤 유형의 질문을 잘 처리하고, 어떤 유형에서 취약한가?
- 임베딩 모델이 의미적 유사성(의역)을 얼마나 잘 처리하는가?
- 복합 분석 질문에 대한 검색 품질은 충분한가?

## 난이도 수준

`QuestionDifficulty` 열거형은 4가지 난이도 수준을 정의한다.

### FACTUAL (사실 기반)

지문에서 직접 찾을 수 있는 정보를 묻는 질문이다. 답이 청크에 그대로 존재하며, 별도의 분석이나 추론 없이 원문 대조만으로 답변할 수 있다.

| 항목 | 내용 |
|------|------|
| 값 | `factual` |
| 특징 | 직접적인 정보 회수 (Direct information recall) |
| 예시 질문 | "프랑스의 수도는 어디인가요?" |
| 기대 동작 | 답이 청크에 그대로 존재하므로 검색 시스템이 가장 쉽게 찾을 수 있는 유형 |

### ANALYTICAL (분석적)

여러 정보를 종합하여 분석하거나 비교해야 하는 질문이다. 단일 사실이 아닌 복수의 사실을 결합해야 답변할 수 있다.

| 항목 | 내용 |
|------|------|
| 값 | `analytical` |
| 특징 | 정보 분석 및 비교 (Analyzing or comparing information) |
| 예시 질문 | "알고리즘 A와 B의 성능을 비교하면?" |
| 기대 동작 | 여러 사실을 결합해야 하므로 FACTUAL보다 검색이 어려울 수 있음 |

### INFERENTIAL (추론적)

명시되지 않은 내용을 맥락에서 추론해야 하는 질문이다. 청크에 직접 기술되지 않은 결론이나 원인을 도출해야 한다.

| 항목 | 내용 |
|------|------|
| 값 | `inferential` |
| 특징 | 명시적 텍스트를 넘어서는 결론 도출 (Drawing conclusions beyond explicit text) |
| 예시 질문 | "주가가 상승한 이유는?" |
| 기대 동작 | 가장 어려운 유형으로, 질문과 청크 간 표면적 유사도가 낮을 수 있음 |

### PARAPHRASED (의역)

같은 의미를 다른 표현으로 묻는 질문이다. 질문에 사용된 단어가 원본 청크와 다르지만 의미적으로 동일한 내용을 검색해야 한다.

| 항목 | 내용 |
|------|------|
| 값 | `paraphrased` |
| 특징 | 원본 내용의 의역 (Rewording of passage content) |
| 예시 질문 | 질문에서 "자동차"를 사용하고 청크에서는 "차량"으로 표현 |
| 기대 동작 | 임베딩 모델의 의미적 유사성 처리 능력을 직접적으로 테스트 |

## 분류 동작 방식

### LLM 기반 자동 분류

데이터셋 생성 시 `SyntheticTestGenerator`가 LLM을 통해 질문을 생성하면서 동시에 난이도를 분류한다. 별도의 분류 단계가 아니라 질문 생성 프롬프트에 난이도 분류 지시가 포함되어 있다.

**시스템 프롬프트에 포함된 난이도 분류 지시:**

```
Difficulty classifications:
- factual: Direct information recall from the passage
- analytical: Requires analyzing or comparing information
- inferential: Requires drawing conclusions beyond explicit text
- paraphrased: Rewording of passage content
```

**LLM 응답 형식:**

```json
{
  "questions": [
    {"text": "질문 텍스트", "difficulty": "factual"},
    {"text": "질문 텍스트", "difficulty": "analytical"}
  ]
}
```

### 난이도 파싱 및 저장

LLM 응답에서 `difficulty` 값을 파싱하여 `QuestionDifficulty` 열거형으로 변환한다. 유효하지 않은 값이 반환되면 `None`으로 설정되며, 해당 테스트 케이스는 난이도별 집계에서 제외된다.

분류된 난이도는 `TestCase.difficulty` 필드에 저장된다.

```python
class TestCase(pydantic.BaseModel):
    id: str
    question: str
    ground_truth_chunk_ids: tuple[str, ...]
    source_chunk_id: str
    difficulty: QuestionDifficulty | None = None  # 난이도 분류 결과
    created_at: datetime.datetime
```

### 하위 호환성

`difficulty` 필드의 기본값은 `None`이다. 난이도 분류 기능이 추가되기 전에 생성된 데이터셋의 테스트 케이스는 `difficulty=None`을 가지며, 이 경우 난이도별 메트릭이 계산되지 않는다.

## 난이도별 메트릭

### 집계 방식

`GetRunHandler`가 평가 실행 결과를 조회할 때, 데이터셋의 테스트 케이스와 실행 결과를 난이도별로 그룹화하여 메트릭을 집계한다.

처리 과정:

1. 데이터셋에서 각 테스트 케이스의 난이도 정보를 조회한다 (`difficulty_map`).
2. `difficulty=None`인 테스트 케이스는 제외한다.
3. 실행 결과를 난이도별로 그룹화한다.
4. 각 그룹에 대해 Precision@k, Recall@k, Hit Rate@k, MRR을 집계한다.

### 난이도별 메트릭 응답

각 난이도 그룹의 메트릭은 `DifficultyMetrics` 모델로 반환된다.

```python
class DifficultyMetrics(pydantic.BaseModel):
    difficulty: str          # 난이도 수준 (factual, analytical, inferential, paraphrased)
    test_case_count: int     # 해당 난이도의 테스트 케이스 수
    precision_at_k: float    # 해당 난이도의 Precision@k 평균
    recall_at_k: float       # 해당 난이도의 Recall@k 평균
    hit_rate_at_k: float     # 해당 난이도의 Hit Rate@k 비율
    mrr: float               # 해당 난이도의 MRR 평균
```

## 사용 가이드

### API: 데이터셋 상세 조회

데이터셋 상세 조회 시 각 테스트 케이스의 `difficulty` 필드를 확인할 수 있다.

```bash
curl http://localhost:8000/evaluation/datasets/{dataset_id}
```

**응답 예시 (DatasetDetail):**

```json
{
  "id": "a1b2c3d4e5f6789012345678abcdef01",
  "notebook_id": "notebook_abc123",
  "name": "v1-baseline",
  "status": "completed",
  "questions_per_chunk": 2,
  "max_chunks_sample": 50,
  "test_cases": [
    {
      "id": "tc_001",
      "question": "TCP 프로토콜의 3-way handshake 과정은 무엇인가?",
      "ground_truth_chunk_ids": ["chunk_abc123"],
      "source_chunk_id": "chunk_abc123",
      "difficulty": "factual",
      "created_at": "2025-01-15T10:31:00Z"
    },
    {
      "id": "tc_002",
      "question": "TCP와 UDP의 전송 방식을 비교하면 어떤 차이가 있는가?",
      "ground_truth_chunk_ids": ["chunk_abc123"],
      "source_chunk_id": "chunk_abc123",
      "difficulty": "analytical",
      "created_at": "2025-01-15T10:31:00Z"
    },
    {
      "id": "tc_003",
      "question": "네트워크 혼잡 시 TCP 성능이 저하되는 원인은?",
      "ground_truth_chunk_ids": ["chunk_def456"],
      "source_chunk_id": "chunk_def456",
      "difficulty": "inferential",
      "created_at": "2025-01-15T10:31:05Z"
    },
    {
      "id": "tc_004",
      "question": "데이터 전송 신뢰성을 보장하는 통신 규약은?",
      "ground_truth_chunk_ids": ["chunk_def456"],
      "source_chunk_id": "chunk_def456",
      "difficulty": "paraphrased",
      "created_at": "2025-01-15T10:31:05Z"
    }
  ],
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:32:45Z"
}
```

### API: 평가 실행 결과 조회

평가 실행 결과 조회 시 `metrics_by_difficulty` 필드에 난이도별 메트릭이 포함된다.

```bash
curl http://localhost:8000/evaluation/runs/{run_id}
```

**응답 예시 (RunDetail):**

```json
{
  "id": "run_001",
  "dataset_id": "a1b2c3d4e5f6789012345678abcdef01",
  "status": "completed",
  "k": 5,
  "metrics": {
    "precision_at_k": 0.2200,
    "recall_at_k": 0.8000,
    "hit_rate_at_k": 0.8000,
    "mrr": 0.6800,
    "k": 5
  },
  "metrics_by_difficulty": [
    {
      "difficulty": "analytical",
      "test_case_count": 25,
      "precision_at_k": 0.2000,
      "recall_at_k": 0.7600,
      "hit_rate_at_k": 0.7600,
      "mrr": 0.6200
    },
    {
      "difficulty": "factual",
      "test_case_count": 30,
      "precision_at_k": 0.2400,
      "recall_at_k": 0.9200,
      "hit_rate_at_k": 0.9200,
      "mrr": 0.8500
    },
    {
      "difficulty": "inferential",
      "test_case_count": 15,
      "precision_at_k": 0.1800,
      "recall_at_k": 0.6000,
      "hit_rate_at_k": 0.6000,
      "mrr": 0.4500
    },
    {
      "difficulty": "paraphrased",
      "test_case_count": 20,
      "precision_at_k": 0.2200,
      "recall_at_k": 0.8000,
      "hit_rate_at_k": 0.8000,
      "mrr": 0.7000
    }
  ],
  "error_message": null,
  "results": [],
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:02:30Z"
}
```

`metrics_by_difficulty`는 난이도가 분류된 테스트 케이스가 없는 경우 `null`이 된다.

### CLI: 난이도별 결과 테이블

`eval results <run_id>` 명령 실행 시 전체 메트릭 패널 아래에 난이도별 테이블이 출력된다.

```bash
python -m src.cli evaluation results <run_id>
```

**출력 예시:**

```
╭──────── Evaluation Results (k=5) ────────╮
│ Precision@5:  0.2200                      │
│ Recall@5:     0.8000                      │
│ Hit Rate@5:   0.8000                      │
│ MRR:          0.6800                      │
╰──── Run: run_a1b2c3d4e5f6789012345678 ───╯

         Metrics by Difficulty
┌──────────────┬───────┬─────────────┬───────────┬────────────┬────────┐
│ Difficulty   │ Count │ Precision@k │ Recall@k  │ Hit Rate@k │ MRR    │
├──────────────┼───────┼─────────────┼───────────┼────────────┼────────┤
│ ANALYTICAL   │ 25    │ 0.2000      │ 0.7600    │ 0.7600     │ 0.6200 │
│ FACTUAL      │ 30    │ 0.2400      │ 0.9200    │ 0.9200     │ 0.8500 │
│ INFERENTIAL  │ 15    │ 0.1800      │ 0.6000    │ 0.6000     │ 0.4500 │
│ PARAPHRASED  │ 20    │ 0.2200      │ 0.8000    │ 0.8000     │ 0.7000 │
└──────────────┴───────┴─────────────┴───────────┴────────────┴────────┘
```

난이도 정보가 없는 데이터셋으로 실행한 경우, 난이도 테이블은 출력되지 않는다.

## 결과 해석

### 난이도별 점수 해석

**FACTUAL 점수가 낮은 경우**

사실 기반 질문은 가장 쉬운 유형이므로, 이 점수가 낮다면 검색 시스템의 기본 품질에 문제가 있음을 의미한다.

- 확인 사항: 임베딩 모델이 도메인에 적합한지, 청크 분할이 의미 단위로 되어 있는지 점검한다.
- 조치: 임베딩 모델 교체, 청크 크기 조정, 문서 전처리 개선을 검토한다.

**ANALYTICAL 점수가 낮은 경우**

복합 질문에 대한 검색이 취약함을 의미한다. 질문이 여러 개념을 결합하고 있어 단일 키워드 매칭으로는 부족할 수 있다.

- 확인 사항: 관련 정보가 하나의 청크에 충분히 포함되어 있는지 확인한다.
- 조치: 청크 크기를 키워 관련 정보가 같은 청크에 포함되도록 하거나, 하이브리드 검색(벡터 + 키워드) 도입을 고려한다.

**INFERENTIAL 점수가 낮은 경우**

추론적 질문은 가장 어려운 유형이므로, 상대적으로 낮은 점수는 예상 가능하다. 그러나 사용 사례에 따라 개선이 필요할 수 있다.

- 기대 수준: FACTUAL 대비 10-20% 낮은 점수는 자연스러운 범위다.
- 조치: 추론 질문의 비중이 높은 사용 사례라면, 질문-문서 유사도에 특화된 임베딩 모델(예: cross-encoder 기반 리랭커)을 도입한다.

**PARAPHRASED 점수가 낮은 경우**

임베딩 모델이 의미적 유사성을 제대로 처리하지 못함을 의미한다. 동일한 의미를 다른 표현으로 검색했을 때 정확한 결과를 반환하지 못하는 것이다.

- 확인 사항: 임베딩 모델이 다국어 동의어와 의역을 잘 처리하는 모델인지 확인한다.
- 조치: 더 높은 품질의 임베딩 모델로 교체를 검토한다. 특히 한국어 의미 유사성 처리에 강한 모델을 선택한다.

### 사용 사례별 중요 난이도

RAG 시스템의 사용 목적에 따라 중점적으로 관찰해야 할 난이도 수준이 다르다.

| 사용 사례 | 중요 난이도 | 이유 |
|-----------|------------|------|
| FAQ 챗봇 | FACTUAL, PARAPHRASED | 사용자가 같은 질문을 다양한 표현으로 물어봄 |
| 기술 문서 검색 | FACTUAL, ANALYTICAL | 정확한 사실 확인과 기술 비교가 핵심 |
| 리서치 어시스턴트 | ANALYTICAL, INFERENTIAL | 분석과 추론이 주요 사용 패턴 |
| 고객 지원 | PARAPHRASED, FACTUAL | 고객이 비전문 용어로 질문하는 경우가 많음 |

### 개선 전후 비교

난이도별 메트릭은 검색 시스템 변경의 효과를 세밀하게 측정하는 데 유용하다.

1. 현재 설정으로 데이터셋을 생성하고 평가를 실행하여 난이도별 baseline을 기록한다.
2. 임베딩 모델이나 청킹 전략을 변경한다.
3. 동일한 데이터셋(임베딩 변경 시) 또는 새 데이터셋(청킹 변경 시)으로 재평가한다.
4. 난이도별 메트릭 변화를 비교하여 어떤 유형의 질문에서 개선 또는 퇴보가 발생했는지 확인한다.

예를 들어, 임베딩 모델 교체 후 PARAPHRASED 점수만 크게 향상되고 나머지는 유사하다면, 해당 모델이 의미적 유사성 처리에 강점이 있음을 확인할 수 있다.
