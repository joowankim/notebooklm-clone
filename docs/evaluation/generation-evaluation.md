# Generation Evaluation (생성 품질 평가)

## 개요

Generation Evaluation은 RAG 시스템에서 답변 생성 단계의 품질을 정량적으로 측정하는 프레임워크다. 검색된 컨텍스트를 기반으로 LLM이 생성한 답변이 사실에 기반하는지(Faithfulness), 질문에 적절히 응답하는지(Answer Relevancy)를 LLM-as-Judge 방식으로 자동 평가한다.

Retrieval Evaluation이 "올바른 문서를 찾았는가?"를 측정한다면, Generation Evaluation은 "찾은 문서로 올바른 답변을 생성했는가?"를 측정한다. 검색 품질이 높더라도 답변 생성 단계에서 환각(hallucination)이 발생하거나, 질문과 무관한 답변을 생성할 수 있다. Generation Evaluation은 이러한 문제를 독립적으로 탐지하여 RAG 시스템의 종단 간(end-to-end) 품질을 보장한다.

이 시스템은 다음과 같은 질문에 답한다:

- 생성된 답변이 검색된 컨텍스트에 근거하는가?
- 생성된 답변이 사용자의 질문에 적절히 응답하는가?
- 검색은 잘 되지만 답변 생성에서 품질이 떨어지는 병목 지점이 있는가?

## 평가 유형

평가 실행 시 `EvaluationType`을 통해 평가 범위를 선택한다.

```python
class EvaluationType(enum.StrEnum):
    RETRIEVAL_ONLY = "retrieval_only"
    FULL_RAG = "full_rag"
```

### RETRIEVAL_ONLY (기본값)

검색 단계만 평가한다. 테스트 케이스의 질문으로 벡터 검색을 수행하고, 검색 결과와 ground truth를 비교하여 Precision@k, Recall@k, Hit Rate@k, MRR 메트릭을 계산한다. LLM 답변 생성이나 판정 호출이 발생하지 않는다.

### FULL_RAG

검색과 답변 생성을 모두 평가한다. RETRIEVAL_ONLY의 모든 메트릭을 계산하고, 추가로 검색된 청크를 컨텍스트로 사용하여 LLM이 답변을 생성한 뒤 LLM-as-Judge가 생성 품질(Faithfulness, Answer Relevancy)을 채점한다.

| 항목 | RETRIEVAL_ONLY | FULL_RAG |
|------|----------------|----------|
| 검색 메트릭 | O | O |
| 답변 생성 | X | O |
| 생성 메트릭 | X | O |
| LLM 호출 횟수 (테스트 케이스당) | 0 | 3 |
| 실행 시간 | 빠름 | 느림 |
| 비용 | 낮음 | 높음 |

## 생성 메트릭

생성 품질은 LLM-as-Judge 방식으로 평가한다. 별도의 LLM(기본 모델: `openai:gpt-4o-mini`)이 평가자(Judge) 역할을 수행하여 각 테스트 케이스의 답변을 채점한다.

### Faithfulness (충실도)

**정의:** 생성된 답변이 검색된 컨텍스트 청크에 근거하는 정도.

**값 범위:** 0.0 ~ 1.0

| 점수 | 의미 |
|------|------|
| 1.0 | 답변이 컨텍스트에 완전히 근거하며 환각 없음 |
| 0.5 | 답변이 부분적으로 근거하며 일부 지원되지 않는 주장 포함 |
| 0.0 | 답변이 컨텍스트와 모순되거나 완전히 환각됨 |

**평가 방법:**

LLM Judge가 질문, 생성된 답변, 검색된 컨텍스트 청크를 모두 입력받아 답변의 각 주장이 컨텍스트에 의해 뒷받침되는지 판단한다.

```python
faithfulness = await llm_judge.score_faithfulness(
    question=test_case.question,
    answer=generated_answer,
    context_chunks=retrieved_chunks,
)
```

**직관적 설명:** "답변이 검색된 문서에 근거하여 작성되었는가?"를 측정한다. 높은 Faithfulness는 LLM이 검색 결과를 충실히 반영하여 답변을 생성했음을 의미하고, 낮은 Faithfulness는 LLM이 컨텍스트에 없는 내용을 지어냈음(hallucination)을 의미한다.

**집계 방식:** 전체 테스트 케이스의 faithfulness 평균 = `mean_faithfulness`

### Answer Relevancy (답변 관련성)

**정의:** 생성된 답변이 사용자 질문에 적절히 응답하는 정도.

**값 범위:** 0.0 ~ 1.0

| 점수 | 의미 |
|------|------|
| 1.0 | 답변이 질문에 직접적이고 완전하게 응답 |
| 0.5 | 답변이 부분적으로 관련되나 불완전하거나 간접적 |
| 0.0 | 답변이 질문에 응답하지 않음 |

**평가 방법:**

LLM Judge가 질문과 생성된 답변을 입력받아 답변이 질문의 의도에 부합하는지 판단한다. 컨텍스트 청크는 입력에 포함되지 않으므로, 순수하게 질문-답변 간의 관련성만 평가한다.

```python
relevancy = await llm_judge.score_answer_relevancy(
    question=test_case.question,
    answer=generated_answer,
)
```

**직관적 설명:** "답변이 질문에 대한 적절한 응답인가?"를 측정한다. 높은 Answer Relevancy는 답변이 질문의 핵심을 정확히 다루고 있음을 의미하고, 낮은 Answer Relevancy는 답변이 질문과 동떨어진 내용이거나 핵심을 빗나갔음을 의미한다.

**집계 방식:** 전체 테스트 케이스의 answer_relevancy 평균 = `mean_answer_relevancy`

### LLM-as-Judge 방법론

`LLMJudge`는 두 개의 독립된 평가 에이전트를 사용한다. 각 에이전트는 전용 시스템 프롬프트를 가지며, 점수(`score`: 0.0~1.0)와 판단 근거(`reasoning`)를 JSON 형식으로 반환한다.

```json
{"score": 0.85, "reasoning": "답변의 대부분이 컨텍스트에 근거하나 마지막 문장은 지원되지 않음"}
```

반환된 점수는 0.0~1.0 범위로 클램핑(clamping)되며, 파싱에 실패하면 0.0으로 처리된다. 이 설계는 평가 에이전트의 오류가 전체 평가 실행을 중단시키지 않도록 보장한다.

### 개별 결과와 집계

**개별 테스트 케이스 (GenerationCaseMetrics):**

```python
class GenerationCaseMetrics(pydantic.BaseModel):
    faithfulness: float      # 0.0 ~ 1.0
    answer_relevancy: float  # 0.0 ~ 1.0
```

**전체 집계 (GenerationMetrics):**

```python
class GenerationMetrics(pydantic.BaseModel):
    mean_faithfulness: float       # 전체 테스트 케이스 faithfulness 평균
    mean_answer_relevancy: float   # 전체 테스트 케이스 answer_relevancy 평균
```

## 전체 RAG 파이프라인

FULL_RAG 모드에서 각 테스트 케이스는 다음 5단계를 거친다:

```
1. 질문 로드
   -> 데이터셋의 TestCase에서 question 추출

2. 벡터 검색 수행 (Retrieval)
   -> question으로 벡터 검색 실행 (상위 k개)
   -> 검색 결과와 ground_truth_chunk_ids 비교
   -> 검색 메트릭 계산 (precision, recall, hit, reciprocal_rank)

3. 답변 생성 (Generation) [LLM 호출 1회]
   -> 검색된 청크를 컨텍스트로 RAGAgent에 전달
   -> LLM이 질문에 대한 답변 생성

4. Faithfulness 판정 [LLM 호출 1회]
   -> LLM Judge에 (question, answer, context_chunks) 전달
   -> 답변이 컨텍스트에 근거하는 정도 채점 (0.0~1.0)

5. Answer Relevancy 판정 [LLM 호출 1회]
   -> LLM Judge에 (question, answer) 전달
   -> 답변이 질문에 적절히 응답하는 정도 채점 (0.0~1.0)
```

모든 테스트 케이스의 처리가 완료되면 전체 집계가 이루어진다:

```
전체 집계:
  -> 검색 메트릭 집계: mean precision@k, mean recall@k, hit_rate@k, MRR
  -> 생성 메트릭 집계: mean_faithfulness, mean_answer_relevancy
  -> EvaluationRun 완성
```

`TestCaseResult`에는 검색 메트릭과 생성 메트릭이 함께 저장된다:

```python
class TestCaseResult(pydantic.BaseModel):
    # 검색 메트릭
    precision: float
    recall: float
    hit: bool
    reciprocal_rank: float
    # 생성 메트릭 (FULL_RAG에서만 값이 있음)
    generated_answer: str | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
```

## 사용 가이드

### API 사용법

FULL_RAG 평가는 기존 평가 실행 엔드포인트에서 `evaluation_type` 파라미터를 추가로 지정한다.

#### 평가 실행

```bash
curl -X POST http://localhost:8000/evaluation/datasets/{dataset_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "k": 5,
    "evaluation_type": "full_rag"
  }'
```

**요청 본문 (RunEvaluation):**

| 필드 | 타입 | 기본값 | 범위 | 설명 |
|------|------|--------|------|------|
| `k` | int | 5 | 1~50 | 검색 결과 상위 몇 개를 평가할지 |
| `evaluation_type` | string | `retrieval_only` | `retrieval_only`, `full_rag` | 평가 유형 |

**응답 예시 (RunDetail, 201 Created):**

```json
{
  "id": "run_001",
  "dataset_id": "a1b2c3d4e5f6789012345678abcdef01",
  "status": "completed",
  "k": 5,
  "evaluation_type": "full_rag",
  "metrics": {
    "precision_at_k": 0.2400,
    "recall_at_k": 0.8500,
    "hit_rate_at_k": 0.8500,
    "mrr": 0.7200,
    "k": 5
  },
  "mean_faithfulness": 0.8250,
  "mean_answer_relevancy": 0.7800,
  "error_message": null,
  "results": [
    {
      "id": "result_001",
      "test_case_id": "tc_001",
      "retrieved_chunk_ids": ["chunk_abc123", "chunk_def456", "chunk_ghi789", "chunk_jkl012", "chunk_mno345"],
      "precision": 0.2,
      "recall": 1.0,
      "hit": true,
      "reciprocal_rank": 1.0,
      "generated_answer": "머신러닝 모델의 과적합을 방지하기 위한 주요 기법으로는 드롭아웃, L1/L2 정규화, 조기 종료 등이 있습니다.",
      "faithfulness": 0.9,
      "answer_relevancy": 0.85
    }
  ],
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:05:30Z"
}
```

**참고:** `evaluation_type`을 `retrieval_only`로 지정하거나 생략하면 기존과 동일하게 검색 메트릭만 계산된다. 이 경우 `mean_faithfulness`, `mean_answer_relevancy`는 `null`로 반환된다.

#### 결과 조회

```bash
curl http://localhost:8000/evaluation/runs/{run_id}
```

FULL_RAG 평가의 결과를 조회하면 검색 메트릭과 생성 메트릭이 함께 반환된다. 개별 테스트 케이스 결과에는 `generated_answer`, `faithfulness`, `answer_relevancy` 필드가 포함된다.

### CLI 사용법

#### run - 평가 실행

```bash
# 기본 Retrieval Only 평가
python -m src.cli evaluation run <dataset_id>

# Full RAG 평가 실행
python -m src.cli evaluation run <dataset_id> --type full_rag
python -m src.cli evaluation run <dataset_id> -t full_rag

# k 값과 평가 유형을 함께 지정
python -m src.cli evaluation run <dataset_id> --k 5 --type full_rag
python -m src.cli evaluation run <dataset_id> -k 5 -t full_rag
```

**출력 예시 (Full RAG):**

```
Running Full RAG evaluation (k=5)...
  Dataset: v1-baseline (80 test cases)

╭──────── Evaluation Results (k=5) ────────╮
│ Precision@5:  0.2400                      │
│ Recall@5:     0.8500                      │
│ Hit Rate@5:   0.8500                      │
│ MRR:          0.7200                      │
╰──── Run: run_a1b2c3d4e5f6789012345678 ───╯

╭──────── Generation Metrics ────────╮
│ Faithfulness:       0.8250         │
│ Answer Relevancy:   0.7800         │
╰────────────────────────────────────╯
```

#### results - 평가 결과 확인

```bash
python -m src.cli evaluation results <run_id>
```

FULL_RAG로 실행된 평가의 결과를 조회하면 검색 메트릭 패널과 생성 메트릭 패널이 함께 출력된다. RETRIEVAL_ONLY로 실행된 경우에는 검색 메트릭 패널만 출력된다.

## 결과 해석

### 점수 범위별 의미

| 점수 범위 | 등급 | Faithfulness 해석 | Answer Relevancy 해석 |
|-----------|------|-------------------|----------------------|
| 0.8 초과 | 우수 | 답변이 컨텍스트에 충실하게 근거함 | 답변이 질문을 정확히 다룸 |
| 0.6 ~ 0.8 | 양호 | 대체로 근거하나 일부 불확실한 주장 포함 | 대체로 적절하나 일부 누락 또는 간접적 |
| 0.4 ~ 0.6 | 보통 | 상당 부분이 컨텍스트에 근거하지 않음 | 질문의 핵심을 부분적으로만 다룸 |
| 0.4 미만 | 개선 필요 | 심각한 환각 문제 | 질문과 답변이 거의 무관 |

### Faithfulness vs Answer Relevancy 트레이드오프

두 메트릭은 서로 다른 측면을 측정하므로 독립적으로 변동할 수 있다. 두 메트릭의 조합 패턴을 분석하면 RAG 시스템의 구체적인 문제점을 파악할 수 있다.

**패턴 1: 높은 Relevancy + 낮은 Faithfulness (환각 위험)**

- 증상: 답변이 질문에 잘 응답하지만 컨텍스트에 근거하지 않는 내용을 포함한다.
- 원인: LLM이 검색된 컨텍스트보다 자체 지식에 의존하여 답변을 생성한다. 또는 프롬프트가 컨텍스트 활용을 충분히 강제하지 않는다.
- 대응:
  1. RAG 프롬프트에 "제공된 컨텍스트만 사용하여 답변하라"는 지시를 강화한다.
  2. 컨텍스트에 답변할 정보가 없을 때 "답변 불가"를 응답하도록 유도한다.
  3. 온도(temperature)를 낮추어 LLM의 창의적 생성을 억제한다.

**패턴 2: 높은 Faithfulness + 낮은 Relevancy (컨텍스트 부적합)**

- 증상: 답변이 컨텍스트에 충실하지만 질문에 대한 적절한 응답이 되지 않는다.
- 원인: 검색된 컨텍스트가 질문에 부적합하거나, LLM이 컨텍스트의 관련 없는 부분에 집중한다.
- 대응:
  1. 검색 메트릭(Recall, Hit Rate)을 확인하여 검색 품질 문제인지 판별한다.
  2. 검색 품질이 낮다면 임베딩 모델이나 청킹 전략을 개선한다.
  3. 검색 품질이 충분한데도 발생한다면 프롬프트에서 질문 중심 답변을 유도한다.

**패턴 3: 높은 Faithfulness + 높은 Relevancy (이상적)**

- 증상: 답변이 컨텍스트에 충실하면서 질문에 정확히 응답한다.
- 의미: RAG 파이프라인이 검색부터 생성까지 잘 동작하고 있다.
- 조치: 현재 설정을 유지하며 미세 조정으로 추가 개선을 도모한다.

**패턴 4: 낮은 Faithfulness + 낮은 Relevancy (전반적 문제)**

- 증상: 답변이 컨텍스트에도 근거하지 않고 질문에도 적절하지 않다.
- 원인: 검색 품질 저하, 부적절한 프롬프트, 또는 LLM 모델 자체의 한계.
- 대응:
  1. 검색 메트릭을 먼저 확인하여 검색 단계의 문제를 배제한다.
  2. RAG 프롬프트를 전면 재설계한다.
  3. 더 높은 성능의 LLM 모델로 교체를 고려한다.

### 검색 메트릭과 생성 메트릭의 교차 분석

FULL_RAG 평가는 검색 메트릭과 생성 메트릭을 함께 제공하므로, 두 단계의 상호 작용을 분석할 수 있다.

| 검색 품질 | 생성 품질 | 진단 |
|-----------|-----------|------|
| 높음 | 높음 | 시스템 정상 동작 |
| 높음 | 낮음 | 생성 단계 문제 (프롬프트, 모델 개선 필요) |
| 낮음 | 높음 | LLM이 자체 지식으로 보완 (환각 위험 존재) |
| 낮음 | 낮음 | 검색 단계부터 개선 필요 |

## 비용 고려사항

FULL_RAG 평가는 RETRIEVAL_ONLY 대비 상당히 높은 비용이 발생한다. 평가 실행 전 예상 비용을 고려해야 한다.

### 테스트 케이스당 LLM 호출 비교

| 평가 유형 | 검색 | 답변 생성 | Faithfulness 판정 | Relevancy 판정 | 총 LLM 호출 |
|-----------|------|----------|-------------------|----------------|------------|
| RETRIEVAL_ONLY | O (벡터 검색, LLM 호출 아님) | X | X | X | 0회 |
| FULL_RAG | O (벡터 검색, LLM 호출 아님) | 1회 | 1회 | 1회 | 3회 |

### 비용 산정 예시

테스트 케이스가 100개인 데이터셋 기준:

| 항목 | RETRIEVAL_ONLY | FULL_RAG |
|------|----------------|----------|
| 벡터 검색 | 100회 | 100회 |
| 답변 생성 LLM 호출 | 0회 | 100회 |
| Judge LLM 호출 | 0회 | 200회 (Faithfulness 100 + Relevancy 100) |
| **총 LLM 호출** | **0회** | **300회** |

### 비용 절감 전략

1. **단계별 평가**: 먼저 RETRIEVAL_ONLY로 검색 품질을 확인한 후, 검색 품질이 충분한 경우에만 FULL_RAG를 실행한다.

2. **소규모 데이터셋으로 시작**: 데이터셋 생성 시 `max_chunks_sample`과 `questions_per_chunk`를 작게 설정하여 적은 테스트 케이스로 먼저 경향을 파악한다.

3. **평가 모델 선택**: LLM Judge의 기본 모델은 `openai:gpt-4o-mini`로, 비용 효율적인 모델이 사용된다. 더 정밀한 평가가 필요한 경우 상위 모델로 교체할 수 있으나 비용이 증가한다.

```bash
# 권장 워크플로우: 단계별 평가

# 1단계: 소규모 데이터셋으로 Retrieval 평가
python -m src.cli evaluation generate <notebook_id> -n "quick-test" -q 1 -m 20
python -m src.cli evaluation run <dataset_id> -k 5

# 2단계: 검색 품질이 양호하면 FULL_RAG 평가
python -m src.cli evaluation run <dataset_id> -k 5 -t full_rag

# 3단계: 본격 평가 시 데이터셋 확대
python -m src.cli evaluation generate <notebook_id> -n "full-test" -q 3 -m 100
python -m src.cli evaluation run <dataset_id> -k 5 -t full_rag
```
