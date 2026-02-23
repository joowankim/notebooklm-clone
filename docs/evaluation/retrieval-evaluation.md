# Retrieval Evaluation (검색 품질 평가)

## 개요

Retrieval Evaluation은 RAG(Retrieval-Augmented Generation) 시스템에서 검색 단계의 품질을 정량적으로 측정하는 프레임워크다. 사용자 질문에 대해 벡터 검색이 올바른 문서 청크를 반환하는지 자동으로 평가한다.

RAG 시스템의 최종 응답 품질은 검색 단계에 크게 의존한다. 아무리 뛰어난 LLM을 사용하더라도 검색된 컨텍스트가 부정확하면 답변의 질이 떨어진다. Retrieval Evaluation은 이 검색 단계를 독립적으로 측정하여 시스템의 병목 지점을 파악하고 개선 방향을 제시한다.

이 시스템은 다음과 같은 질문에 답한다:

- 검색 결과 상위 k개 중 실제로 관련된 청크가 몇 개인가?
- 정답 청크가 검색 결과에 포함되는가?
- 정답 청크가 상위 몇 번째에 위치하는가?

## 핵심 개념

### 평가 파이프라인

전체 평가 과정은 크게 두 단계로 나뉜다.

**1단계: 데이터셋 생성 (Generate Dataset)**

노트북에 포함된 문서 청크로부터 합성 테스트 데이터를 생성한다.

```
노트북 선택
  -> 완료(COMPLETED) 상태 문서 수집
  -> 문서별 청크 수집
  -> 청크 샘플링 (max_chunks_sample)
  -> LLM으로 청크별 질문 생성 (questions_per_chunk)
  -> TestCase 생성 (question + ground_truth_chunk_ids)
  -> EvaluationDataset 완성
```

**2단계: 평가 실행 (Run Evaluation)**

생성된 데이터셋의 각 테스트 케이스에 대해 실제 검색을 수행하고 메트릭을 계산한다.

```
데이터셋 로드
  -> 각 TestCase의 question으로 벡터 검색 수행 (k개 결과)
  -> 검색 결과와 ground_truth_chunk_ids 비교
  -> 개별 케이스 메트릭 계산 (precision, recall, hit, reciprocal_rank)
  -> 전체 집계 메트릭 계산 (mean precision@k, mean recall@k, hit_rate@k, MRR)
  -> EvaluationRun 완성
```

### 상태 머신

**EvaluationDataset 상태 전이:**

```
PENDING -> GENERATING -> COMPLETED
                      -> FAILED
```

| 상태 | 설명 |
|------|------|
| `pending` | 데이터셋이 생성되었으나 테스트 케이스 생성이 시작되지 않은 상태 |
| `generating` | LLM을 통해 합성 질문을 생성 중인 상태 |
| `completed` | 테스트 케이스 생성이 완료되어 평가 실행이 가능한 상태 |
| `failed` | 테스트 케이스 생성 중 오류가 발생한 상태 |

- `is_generatable`: `PENDING` 상태에서만 `True` (생성 시작 가능)
- `is_runnable`: `COMPLETED` 상태에서만 `True` (평가 실행 가능)

**EvaluationRun 상태 전이:**

```
PENDING -> RUNNING -> COMPLETED
                   -> FAILED
```

| 상태 | 설명 |
|------|------|
| `pending` | 평가 실행이 생성되었으나 시작되지 않은 상태 |
| `running` | 테스트 케이스별 검색 및 메트릭 계산이 진행 중인 상태 |
| `completed` | 모든 테스트 케이스 평가가 완료되고 집계 메트릭이 계산된 상태 |
| `failed` | 평가 실행 중 오류가 발생한 상태 |

- `is_runnable`: `PENDING` 상태에서만 `True` (실행 시작 가능)

### 합성 테스트 데이터 생성

`SyntheticTestGenerator`는 문서 청크의 내용을 기반으로 LLM을 활용하여 합성 질문을 생성한다. 기본 모델은 `openai:gpt-4o-mini`를 사용한다.

**생성 과정:**

1. 전체 청크 목록에서 `max_chunks_sample`개를 랜덤 샘플링한다 (청크 수가 `max_chunks_sample` 이하이면 전체 사용).
2. 각 샘플링된 청크에 대해 LLM에 `questions_per_chunk`개의 질문 생성을 요청한다.
3. LLM은 청크 내용만으로 답변 가능한 다양한 유형의 질문(사실 확인, 분석, 비교, 설명)을 생성한다.
4. 생성된 각 질문에 대해 `TestCase`를 만들며, 해당 질문을 생성한 원본 청크가 `ground_truth_chunk_ids`(정답)가 된다.

**Ground Truth의 의미:**

질문을 생성한 원본 청크가 곧 정답 청크다. 예를 들어 청크 A의 내용으로 질문 Q를 만들었다면, 검색 시스템이 Q에 대해 청크 A를 반환해야 올바른 검색으로 판정한다. 이 방식은 별도의 사람이 직접 레이블링할 필요 없이 자동으로 ground truth를 확보할 수 있다는 장점이 있다.

**LLM 프롬프트 규칙:**

- 질문은 자기 완결적이어야 한다 ("본문에서", "위 내용에서" 등의 표현 금지)
- 예/아니오 질문 금지
- 다양한 유형의 질문 생성 필요
- 해당 청크의 정보가 있어야만 답할 수 있는 질문이어야 한다

## 메트릭 설명

모든 메트릭은 개별 테스트 케이스 단위로 계산된 후, 전체 테스트 케이스에 대한 평균(또는 비율)으로 집계된다.

### Precision@k (정밀도)

**정의:** 상위 k개 검색 결과 중 실제로 관련된(정답인) 청크의 비율.

**수식:**

```
Precision@k = |{검색된 상위 k개} ∩ {정답 청크}| / k
```

**값 범위:** 0.0 ~ 1.0

**직관적 설명:** "검색 결과가 얼마나 정확한가?"를 측정한다. 상위 k개 결과 중 불필요한 결과가 적을수록 높은 값을 가진다.

**구체적 해석 예시:**

- k=5이고 정답 청크가 1개인 경우:
  - 상위 5개 중 정답 1개 포함 -> Precision@5 = 1/5 = 0.2
  - 상위 5개 중 정답 0개 포함 -> Precision@5 = 0/5 = 0.0
- k=5이고 정답 청크가 3개인 경우:
  - 상위 5개 중 정답 3개 모두 포함 -> Precision@5 = 3/5 = 0.6
  - 상위 5개 중 정답 2개 포함 -> Precision@5 = 2/5 = 0.4

**집계 방식:** 전체 테스트 케이스의 Precision 평균 = `precision_at_k`

### Recall@k (재현율)

**정의:** 전체 정답 청크 중 상위 k개 검색 결과에 포함된 비율.

**수식:**

```
Recall@k = |{검색된 상위 k개} ∩ {정답 청크}| / |{정답 청크}|
```

**값 범위:** 0.0 ~ 1.0

**직관적 설명:** "정답을 얼마나 빠짐없이 찾았는가?"를 측정한다. 정답 청크를 놓치지 않고 검색 결과에 포함시킬수록 높은 값을 가진다.

**구체적 해석 예시:**

- 정답 청크가 1개인 경우 (이 시스템의 기본 설정):
  - 상위 k개에 정답 포함 -> Recall@k = 1/1 = 1.0
  - 상위 k개에 정답 미포함 -> Recall@k = 0/1 = 0.0
- 정답 청크가 3개인 경우:
  - 상위 k개에 정답 2개 포함 -> Recall@k = 2/3 = 0.667
  - 상위 k개에 정답 3개 모두 포함 -> Recall@k = 3/3 = 1.0

**참고:** 이 시스템에서는 청크 하나에서 질문을 생성하므로 `ground_truth_chunk_ids`에 보통 1개의 청크만 포함된다. 따라서 Recall@k는 Hit Rate@k와 동일한 값을 가지는 경우가 많다.

**집계 방식:** 전체 테스트 케이스의 Recall 평균 = `recall_at_k`

### Hit Rate@k (적중률)

**정의:** 상위 k개 검색 결과에 정답 청크가 하나라도 포함되었는지 여부.

**수식:**

```
Hit@k = 1  (상위 k개 중 정답이 하나라도 있으면)
Hit@k = 0  (상위 k개 중 정답이 하나도 없으면)

Hit Rate@k = (Hit@k = 1인 테스트 케이스 수) / (전체 테스트 케이스 수)
```

**값 범위:** 개별 케이스는 0 또는 1 (boolean), 집계 값은 0.0 ~ 1.0

**직관적 설명:** "정답을 한 개라도 찾았는가?"를 측정한다. Precision이나 Recall과 달리 정답의 개수나 위치에 관계없이, 정답이 존재하기만 하면 성공으로 판정한다.

**구체적 해석 예시:**

- 100개 테스트 케이스 중 85개에서 상위 k개 안에 정답이 포함됨 -> Hit Rate@k = 85/100 = 0.85
- 100개 테스트 케이스 중 60개에서 상위 k개 안에 정답이 포함됨 -> Hit Rate@k = 60/100 = 0.60

**집계 방식:** Hit=True인 케이스의 비율 = `hit_rate_at_k`

### MRR (Mean Reciprocal Rank, 평균 역순위)

**정의:** 각 테스트 케이스에서 첫 번째 정답 청크가 나타난 순위의 역수를 전체 평균한 값.

**수식:**

```
Reciprocal Rank = 1 / (첫 번째 정답 청크의 순위)
                = 0  (상위 k개 안에 정답이 없으면)

MRR = (1/N) * sum(Reciprocal Rank_i, i=1..N)
```

**값 범위:** 0.0 ~ 1.0

**직관적 설명:** "정답이 얼마나 상위에 위치하는가?"를 측정한다. 정답이 1위에 나타나면 1.0, 2위에 나타나면 0.5, 3위에 나타나면 0.333이 된다. 정답이 상위에 랭크될수록 높은 값을 가진다.

**구체적 해석 예시:**

- 테스트 케이스 3개의 결과:
  - 케이스 1: 정답이 1위 -> RR = 1/1 = 1.0
  - 케이스 2: 정답이 3위 -> RR = 1/3 = 0.333
  - 케이스 3: 정답이 2위 -> RR = 1/2 = 0.5
  - MRR = (1.0 + 0.333 + 0.5) / 3 = 0.611
- 테스트 케이스 2개의 결과:
  - 케이스 1: 정답이 1위 -> RR = 1.0
  - 케이스 2: 상위 k개에 정답 없음 -> RR = 0.0
  - MRR = (1.0 + 0.0) / 2 = 0.5

**집계 방식:** 전체 테스트 케이스의 Reciprocal Rank 평균 = `mrr`

## 사용 가이드

### API 사용법

이 시스템은 5개의 REST API 엔드포인트를 제공한다.

#### 1. 데이터셋 생성

노트북의 청크로부터 합성 평가 데이터셋을 생성한다.

```bash
curl -X POST http://localhost:8000/notebooks/{notebook_id}/evaluation/datasets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "v1-baseline",
    "questions_per_chunk": 2,
    "max_chunks_sample": 50
  }'
```

**요청 본문 (GenerateDataset):**

| 필드 | 타입 | 기본값 | 범위 | 설명 |
|------|------|--------|------|------|
| `name` | string | (필수) | 1~255자 | 데이터셋 이름 |
| `questions_per_chunk` | int | 2 | 1~10 | 청크당 생성할 질문 수 |
| `max_chunks_sample` | int | 50 | 1~500 | 샘플링할 최대 청크 수 |

**응답 예시 (DatasetSummary, 201 Created):**

```json
{
  "id": "a1b2c3d4e5f6789012345678abcdef01",
  "notebook_id": "notebook_abc123",
  "name": "v1-baseline",
  "status": "completed",
  "questions_per_chunk": 2,
  "max_chunks_sample": 50,
  "test_case_count": 80,
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:32:45Z"
}
```

**오류 응답:**

- `404 Not Found`: 노트북이 존재하지 않음
- `400 Bad Request`: 완료된 문서가 없거나 청크가 없음

#### 2. 데이터셋 목록 조회

특정 노트북의 모든 평가 데이터셋을 조회한다.

```bash
curl http://localhost:8000/notebooks/{notebook_id}/evaluation/datasets
```

**응답 예시 (list[DatasetSummary], 200 OK):**

```json
[
  {
    "id": "a1b2c3d4e5f6789012345678abcdef01",
    "notebook_id": "notebook_abc123",
    "name": "v1-baseline",
    "status": "completed",
    "questions_per_chunk": 2,
    "max_chunks_sample": 50,
    "test_case_count": 80,
    "error_message": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:32:45Z"
  },
  {
    "id": "b2c3d4e5f67890123456789abcdef012",
    "notebook_id": "notebook_abc123",
    "name": "v2-more-questions",
    "status": "completed",
    "questions_per_chunk": 5,
    "max_chunks_sample": 100,
    "test_case_count": 250,
    "error_message": null,
    "created_at": "2025-01-16T14:00:00Z",
    "updated_at": "2025-01-16T14:05:30Z"
  }
]
```

**오류 응답:**

- `404 Not Found`: 노트북이 존재하지 않음

#### 3. 데이터셋 상세 조회

데이터셋의 상세 정보와 테스트 케이스 목록을 조회한다.

```bash
curl http://localhost:8000/evaluation/datasets/{dataset_id}
```

**응답 예시 (DatasetDetail, 200 OK):**

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
      "question": "머신러닝 모델의 과적합을 방지하기 위한 주요 기법에는 어떤 것들이 있는가?",
      "ground_truth_chunk_ids": ["chunk_abc123"],
      "source_chunk_id": "chunk_abc123",
      "created_at": "2025-01-15T10:31:00Z"
    },
    {
      "id": "tc_002",
      "question": "드롭아웃 정규화가 신경망 학습에 미치는 영향은 무엇인가?",
      "ground_truth_chunk_ids": ["chunk_abc123"],
      "source_chunk_id": "chunk_abc123",
      "created_at": "2025-01-15T10:31:00Z"
    }
  ],
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:32:45Z"
}
```

**오류 응답:**

- `404 Not Found`: 데이터셋이 존재하지 않음

#### 4. 평가 실행

완료된 데이터셋에 대해 검색 평가를 실행한다.

```bash
curl -X POST http://localhost:8000/evaluation/datasets/{dataset_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "k": 5
  }'
```

**요청 본문 (RunEvaluation):**

| 필드 | 타입 | 기본값 | 범위 | 설명 |
|------|------|--------|------|------|
| `k` | int | 5 | 1~50 | 검색 결과 상위 몇 개를 평가할지 |

**응답 예시 (RunDetail, 201 Created):**

```json
{
  "id": "run_001",
  "dataset_id": "a1b2c3d4e5f6789012345678abcdef01",
  "status": "completed",
  "k": 5,
  "metrics": {
    "precision_at_k": 0.2400,
    "recall_at_k": 0.8500,
    "hit_rate_at_k": 0.8500,
    "mrr": 0.7200,
    "k": 5
  },
  "error_message": null,
  "results": [
    {
      "id": "result_001",
      "test_case_id": "tc_001",
      "retrieved_chunk_ids": ["chunk_abc123", "chunk_def456", "chunk_ghi789", "chunk_jkl012", "chunk_mno345"],
      "precision": 0.2,
      "recall": 1.0,
      "hit": true,
      "reciprocal_rank": 1.0
    },
    {
      "id": "result_002",
      "test_case_id": "tc_002",
      "retrieved_chunk_ids": ["chunk_def456", "chunk_ghi789", "chunk_abc123", "chunk_jkl012", "chunk_mno345"],
      "precision": 0.2,
      "recall": 1.0,
      "hit": true,
      "reciprocal_rank": 0.3333
    }
  ],
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:02:30Z"
}
```

**오류 응답:**

- `404 Not Found`: 데이터셋이 존재하지 않음
- `409 Conflict`: 데이터셋이 `completed` 상태가 아님

#### 5. 평가 결과 조회

특정 평가 실행의 상세 결과를 조회한다.

```bash
curl http://localhost:8000/evaluation/runs/{run_id}
```

**응답 예시 (RunDetail, 200 OK):**

응답 형식은 "4. 평가 실행"의 응답과 동일하다.

**오류 응답:**

- `404 Not Found`: 실행 결과가 존재하지 않음

### CLI 사용법

CLI는 4개의 커맨드를 제공한다. 모든 커맨드는 `evaluation` 서브커맨드 아래에 위치한다.

#### 1. generate - 데이터셋 생성

```bash
# 기본 설정으로 생성 (questions_per_chunk=2, max_chunks=50)
python -m src.cli evaluation generate <notebook_id>

# 이름 지정
python -m src.cli evaluation generate <notebook_id> --name "v1-baseline"
python -m src.cli evaluation generate <notebook_id> -n "v1-baseline"

# 청크당 질문 수 조정
python -m src.cli evaluation generate <notebook_id> --questions 5
python -m src.cli evaluation generate <notebook_id> -q 5

# 최대 샘플링 청크 수 조정
python -m src.cli evaluation generate <notebook_id> --max-chunks 100
python -m src.cli evaluation generate <notebook_id> -m 100

# 모든 옵션 조합
python -m src.cli evaluation generate <notebook_id> -n "v2-extended" -q 5 -m 100
```

**출력 예시:**

```
  Found 120 chunks from 5 documents
Generating dataset... (id: a1b2c3d4e5f6789012345678abcdef01)
Generated 100 test cases
  Dataset ID: a1b2c3d4e5f6789012345678abcdef01
```

#### 2. list - 데이터셋 목록 조회

```bash
python -m src.cli evaluation list <notebook_id>
```

**출력 예시:**

```
              Evaluation Datasets
┌──────────────────┬──────────────┬───────────┬────────────┬──────────────────┐
│ ID               │ Name         │ Status    │ Test Cases │ Created          │
├──────────────────┼──────────────┼───────────┼────────────┼──────────────────┤
│ a1b2c3d4e5f6...  │ v1-baseline  │ completed │         80 │ 2025-01-15 10:30 │
│ b2c3d4e5f678...  │ v2-extended  │ completed │        250 │ 2025-01-16 14:00 │
│ c3d4e5f67890...  │ v3-test      │ failed    │          0 │ 2025-01-17 09:00 │
└──────────────────┴──────────────┴───────────┴────────────┴──────────────────┘
```

데이터셋이 없는 경우:

```
No datasets found.
```

#### 3. run - 평가 실행

```bash
# 기본 k=5로 실행
python -m src.cli evaluation run <dataset_id>

# k 값 지정
python -m src.cli evaluation run <dataset_id> --k 10
python -m src.cli evaluation run <dataset_id> -k 10
```

**출력 예시:**

```
Running evaluation (k=5)...
  Dataset: v1-baseline (80 test cases)

╭──────── Evaluation Results (k=5) ────────╮
│ Precision@5:  0.2400                      │
│ Recall@5:     0.8500                      │
│ Hit Rate@5:   0.8500                      │
│ MRR:          0.7200                      │
╰──── Run: run_a1b2c3d4e5f6789012345678 ───╯
```

#### 4. results - 평가 결과 확인

```bash
python -m src.cli evaluation results <run_id>
```

**출력 예시:**

```
╭──────── Evaluation Results (k=5) ────────╮
│ Precision@5:  0.2400                      │
│ Recall@5:     0.8500                      │
│ Hit Rate@5:   0.8500                      │
│ MRR:          0.7200                      │
╰──── Run: run_a1b2c3d4e5f6789012345678 ───╯
```

실행이 완료되지 않은 경우:

```
Run not completed (status: running)
```

실패한 경우:

```
Run not completed (status: failed)
  Error: Connection timeout to embedding service
```

## 파라미터 튜닝

### k (검색 개수)

`k`는 평가 시 검색 결과 상위 몇 개를 고려할지 결정한다. 기본값은 5이며 1~50 범위에서 설정 가능하다.

**k가 메트릭에 미치는 영향:**

| k 값 | Precision | Recall | Hit Rate | 설명 |
|------|-----------|--------|----------|------|
| 작은 k (1~3) | 높아지는 경향 | 낮아지는 경향 | 낮아지는 경향 | 상위 결과만 보므로 정확도는 높지만 정답을 놓칠 가능성 증가 |
| 중간 k (5~10) | 중간 | 중간 | 중간 | 일반적인 평가에 적합한 균형 |
| 큰 k (20~50) | 낮아지는 경향 | 높아지는 경향 | 높아지는 경향 | 많은 결과를 포함하므로 정답을 찾을 확률은 높지만 불필요한 결과도 포함 |

**권장 사항:**

- 실제 RAG 파이프라인에서 LLM에 전달하는 컨텍스트 수와 동일하게 k를 설정하는 것이 가장 현실적인 평가 결과를 제공한다.
- 예를 들어, LLM에 상위 3개 청크를 전달한다면 k=3으로 평가하는 것이 적합하다.

### questions_per_chunk

`questions_per_chunk`는 각 청크에서 생성할 질문 수를 결정한다. 기본값은 2이며 1~10 범위에서 설정 가능하다.

**조정의 의미:**

| 값 | 테스트 케이스 수 | 장점 | 단점 |
|----|-----------------|------|------|
| 1 | 최소 | 빠른 생성, 낮은 비용 | 질문 다양성 부족, 통계적 신뢰도 낮음 |
| 2~3 | 적당 | 적절한 다양성과 비용 균형 | - |
| 5~10 | 많음 | 높은 통계적 신뢰도, 다양한 질문 유형 | 생성 시간 및 LLM 비용 증가 |

**권장 사항:**

- 초기 탐색에는 `questions_per_chunk=2`로 빠르게 평가한다.
- 정밀한 비교 평가가 필요한 경우 `questions_per_chunk=5` 이상으로 늘린다.
- 동일한 청크에서 여러 질문을 생성하면 다양한 관점에서 검색 품질을 평가할 수 있다.

### max_chunks_sample

`max_chunks_sample`은 전체 청크 중 평가에 사용할 청크를 랜덤 샘플링하는 최대 개수다. 기본값은 50이며 1~500 범위에서 설정 가능하다.

**조정의 의미:**

| 값 | 총 테스트 케이스 수 (questions_per_chunk=2 기준) | 영향 |
|----|---------------------------------------------|------|
| 10 | 최대 20개 | 빠른 실행, 샘플링 편향 가능성 높음 |
| 50 | 최대 100개 | 일반적 사용에 적합 |
| 100 | 최대 200개 | 더 대표성 있는 평가 |
| 500 | 최대 1000개 | 가장 포괄적이나 시간/비용 많이 소요 |

**참고:** 전체 청크 수가 `max_chunks_sample`보다 적으면 모든 청크를 사용한다.

**권장 사항:**

- 전체 청크 수가 수백 개 이하인 경우, `max_chunks_sample`을 전체 청크 수와 동일하게 설정하여 전수 평가를 수행한다.
- 전체 청크 수가 수천 개 이상인 경우, `max_chunks_sample=100~200`으로 설정하여 대표성 있는 샘플을 확보한다.

## 결과 해석 가이드

### 점수 범위별 의미

| 점수 범위 | 등급 | 의미 | 조치 |
|-----------|------|------|------|
| 0.8 초과 | 우수 | 검색 시스템이 대부분의 관련 청크를 정확하게 찾아냄 | 현재 설정 유지, 미세 조정으로 추가 개선 가능 |
| 0.6 ~ 0.8 | 양호 | 대체로 관련 청크를 찾지만 일부 누락 발생 | 임베딩 모델이나 청킹 전략 검토 필요 |
| 0.4 ~ 0.6 | 보통 | 검색 결과에 무관한 청크가 상당히 포함됨 | 청킹 크기, 임베딩 모델 변경 등 구체적 개선 필요 |
| 0.4 미만 | 개선 필요 | 검색 시스템이 관련 청크를 잘 찾지 못함 | 전면적인 검색 파이프라인 재검토 필요 |

위 기준은 모든 메트릭에 공통으로 적용할 수 있으나, 각 메트릭의 특성에 따라 해석이 달라질 수 있다. 특히 Precision@k는 정답 청크 수가 적을 때 k에 의해 상한이 제한되므로 (정답 1개, k=5이면 최대 0.2) 절대값보다는 상대적 변화 추이를 관찰하는 것이 유용하다.

### 흔한 패턴과 대응 방법

**패턴 1: 높은 Precision, 낮은 Recall**

- 증상: 검색된 결과는 정확하지만 정답을 놓치는 경우가 많다.
- 원인: k 값이 너무 작거나, 임베딩이 의미적으로 유사한 청크를 구분하지 못한다.
- 대응: k 값을 증가시키거나, 청킹 전략을 조정하여 관련 정보가 하나의 청크에 집중되도록 한다.

**패턴 2: 낮은 Precision, 높은 Recall**

- 증상: 정답은 포함되지만 무관한 청크도 많이 검색된다.
- 원인: 임베딩 모델의 의미 구분 능력이 부족하거나, 청크 크기가 너무 작아서 유사한 청크가 많다.
- 대응: 임베딩 모델을 더 높은 품질의 모델로 교체하거나, 청크 크기를 키워 의미 단위를 명확하게 구분한다.

**패턴 3: 높은 Hit Rate, 낮은 MRR**

- 증상: 정답이 검색 결과에 포함되지만 상위가 아닌 하위 순위에 위치한다.
- 원인: 임베딩이 질문과 정답 청크 간의 유사도를 정확하게 반영하지 못한다.
- 대응: 질문-문서 유사도에 특화된 임베딩 모델을 사용하거나, 하이브리드 검색(벡터 + 키워드)을 도입한다.

**패턴 4: 전반적으로 낮은 점수**

- 증상: 모든 메트릭이 0.4 미만이다.
- 원인: 임베딩 모델과 문서 도메인의 불일치, 부적절한 청킹 전략, 또는 데이터 품질 문제.
- 대응:
  1. 청킹 전략 재검토 (크기, 오버랩 비율 조정)
  2. 도메인에 적합한 임베딩 모델로 교체
  3. 문서 전처리 개선 (노이즈 제거, 구조화)

### 개선 제안

**임베딩 모델 변경 시:**

1. 현재 모델로 baseline 데이터셋을 생성한다 (`generate` 커맨드).
2. 현재 모델로 평가를 실행하여 baseline 점수를 기록한다 (`run` 커맨드).
3. 임베딩 모델을 변경한 후, 동일한 데이터셋으로 재평가한다.
4. 두 실행의 메트릭을 비교하여 개선 여부를 확인한다.

**청킹 전략 변경 시:**

1. 변경 전 청킹으로 데이터셋 A를 생성하고 평가한다.
2. 청킹 전략을 변경한다 (크기, 오버랩 등).
3. 변경 후 청킹으로 데이터셋 B를 생성하고 평가한다.
4. 두 데이터셋의 평가 결과를 비교한다.

**주의:** 청킹 전략 변경 시에는 데이터셋을 새로 생성해야 한다. 기존 데이터셋의 `ground_truth_chunk_ids`가 이전 청킹 기준이므로 재사용할 수 없다.

**k 값에 따른 성능 곡선 분석:**

동일한 데이터셋에 대해 다양한 k 값(예: 1, 3, 5, 10, 20)으로 반복 실행하면, k에 따른 Recall/Precision 변화 곡선을 그릴 수 있다. 이를 통해 최적의 k 값을 결정할 수 있다.

```bash
python -m src.cli evaluation run <dataset_id> -k 1
python -m src.cli evaluation run <dataset_id> -k 3
python -m src.cli evaluation run <dataset_id> -k 5
python -m src.cli evaluation run <dataset_id> -k 10
python -m src.cli evaluation run <dataset_id> -k 20
```
