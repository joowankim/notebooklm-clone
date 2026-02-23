# Run Comparison (실행 비교)

## 개요

Run Comparison은 동일한 평가 데이터셋에 대해 수행된 여러 평가 실행(Run)의 결과를 나란히 비교하는 기능이다. RAG 시스템을 반복적으로 개선할 때, 변경 전후의 성능을 객관적으로 비교할 수 있다.

시스템 설정을 변경할 때마다 "실제로 개선되었는가?"라는 질문에 데이터 기반으로 답할 수 있어야 한다. Run Comparison은 이를 가능하게 하여, 감에 의존한 튜닝이 아닌 정량적 A/B 테스트를 지원한다.

## 사용 사례

### 검색 개수(k) 최적화

동일 데이터셋에 대해 k=3, k=5, k=10으로 각각 평가를 실행한 뒤 비교한다. k가 증가하면 Recall은 올라가지만 Precision은 낮아지는 트레이드오프를 확인하고, 실제 RAG 파이프라인에 최적인 k를 선택한다.

### 임베딩 모델 교체

`text-embedding-3-small`에서 `text-embedding-3-large`로 교체 전후의 평가를 비교한다. 동일 질문에 대해 검색 품질이 어떻게 변하는지 확인한다.

### 청킹 전략 변경

고정 크기 청킹에서 시맨틱 청킹으로 전환하는 경우, 새로 청킹한 뒤 동일 구조의 데이터셋을 생성하여 비교한다.

### 프롬프트 튜닝 (FULL_RAG)

답변 생성 프롬프트를 수정한 후, `full_rag` 평가를 다시 실행하여 Faithfulness와 Answer Relevancy의 변화를 비교한다.

### 하이브리드 검색 도입

순수 벡터 검색 vs 하이브리드 검색(벡터 + 키워드)의 성능 차이를 동일 데이터셋으로 비교한다.

## 비교 조건

비교를 수행하려면 다음 조건을 모두 만족해야 한다:

| 조건 | 설명 |
|------|------|
| 동일 데이터셋 | 모든 Run이 같은 `dataset_id`에 속해야 한다 (동일 질문으로 평가) |
| 동일 k 값 | 모든 Run이 같은 `k` 값을 사용해야 한다 (공정한 메트릭 비교) |
| 완료 상태 | 모든 Run이 `COMPLETED` 상태여야 한다 |
| 2~10개 Run | 최소 2개, 최대 10개의 Run을 비교할 수 있다 |

조건을 만족하지 않으면 검증 오류가 발생한다.

## 비교 결과 구조

### 집계 메트릭 (Aggregate Metrics)

각 Run의 전체 평균 메트릭을 나란히 제시한다. Retrieval 메트릭(Precision@k, Recall@k, Hit Rate@k, MRR)은 항상 포함되며, `full_rag` 평가인 경우 Generation 메트릭(Faithfulness, Answer Relevancy)도 함께 표시된다.

### 테스트 케이스별 비교 (Test Case Comparisons)

동일 질문에 대한 각 Run의 개별 메트릭을 비교한다. 특정 질문에서 어떤 Run이 더 좋은 결과를 냈는지, 난이도별로 성능 차이가 있는지 확인할 수 있다.

## 사용 가이드

### API 사용법

```bash
curl -X POST http://localhost:8000/evaluation/compare \
  -H "Content-Type: application/json" \
  -d '{
    "run_ids": ["run_abc123", "run_def456"]
  }'
```

**요청 본문 (CompareRuns):**

| 필드 | 타입 | 범위 | 설명 |
|------|------|------|------|
| `run_ids` | list[str] | 2~10개 | 비교할 Run ID 목록 |

**응답 예시 (RunComparisonResponse, 200 OK):**

```json
{
  "dataset_id": "dataset_xyz",
  "k": 5,
  "run_count": 2,
  "aggregate_metrics": [
    {
      "run_id": "run_abc123",
      "created_at": "2025-01-15T10:00:00Z",
      "evaluation_type": "retrieval_only",
      "precision_at_k": 0.7200,
      "recall_at_k": 0.6800,
      "hit_rate_at_k": 0.9500,
      "mrr": 0.6500,
      "mean_faithfulness": null,
      "mean_answer_relevancy": null
    },
    {
      "run_id": "run_def456",
      "created_at": "2025-01-16T14:00:00Z",
      "evaluation_type": "retrieval_only",
      "precision_at_k": 0.7800,
      "recall_at_k": 0.7200,
      "hit_rate_at_k": 0.9600,
      "mrr": 0.7000,
      "mean_faithfulness": null,
      "mean_answer_relevancy": null
    }
  ],
  "test_case_comparisons": [
    {
      "test_case_id": "tc_001",
      "question": "머신러닝 모델의 과적합을 방지하기 위한 주요 기법은?",
      "difficulty": "factual",
      "entries": [
        {
          "run_id": "run_abc123",
          "precision": 0.2,
          "recall": 1.0,
          "hit": true,
          "reciprocal_rank": 1.0,
          "faithfulness": null,
          "answer_relevancy": null,
          "generated_answer": null
        },
        {
          "run_id": "run_def456",
          "precision": 0.4,
          "recall": 1.0,
          "hit": true,
          "reciprocal_rank": 1.0,
          "faithfulness": null,
          "answer_relevancy": null,
          "generated_answer": null
        }
      ]
    }
  ]
}
```

**오류 응답:**

- `404 Not Found`: 요청한 Run ID가 존재하지 않음
- `400 Bad Request`: Run이 서로 다른 데이터셋에 속하거나, 완료 상태가 아니거나, k 값이 다름

### CLI 사용법

```bash
# 2개 Run 비교
python -m src.cli evaluation compare <run_id_1> <run_id_2>

# 3개 이상 Run 비교
python -m src.cli evaluation compare <run_id_1> <run_id_2> <run_id_3>
```

**출력 예시:**

```
Dataset: dataset_xyz  k: 5  Runs: 2

        Aggregate Metrics Comparison
┌──────────┬──────────────────┬────────────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│ Run ID   │ Created          │ Type           │ P@k    │ R@k    │ Hit@k  │ MRR    │ Faith. │ Relev. │
├──────────┼──────────────────┼────────────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ run_abc1 │ 2025-01-15 10:00 │ retrieval_only │ 0.7200 │ 0.6800 │ 0.9500 │ 0.6500 │ N/A    │ N/A    │
│ run_def4 │ 2025-01-16 14:00 │ retrieval_only │ 0.7800 │ 0.7200 │ 0.9600 │ 0.7000 │ N/A    │ N/A    │
└──────────┴──────────────────┴────────────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Test Cases Compared: 80
```

**오류 출력:**

```
# Run ID를 하나만 제공한 경우
Must provide at least 2 run IDs

# 다른 데이터셋의 Run을 비교하려는 경우
All runs must belong to the same dataset
```

## 결과 읽기

### 집계 메트릭 비교

Run 간의 전체 평균 메트릭을 비교하여 어떤 설정이 전반적으로 더 나은지 판단한다.

- **모든 메트릭이 개선:** 변경이 명확히 긍정적이다. 새 설정을 채택한다.
- **일부만 개선:** 트레이드오프가 있다. 예를 들어 Precision은 올랐지만 Recall이 내려간 경우, 시스템의 우선순위에 따라 결정한다.
- **모든 메트릭이 하락:** 변경을 되돌린다.

### 테스트 케이스별 분석

집계 메트릭만으로는 세부 패턴을 알 수 없다. 테스트 케이스별 비교로 다음을 확인한다:

- **개선된 질문:** 변경 후 정답을 새로 찾게 된 질문이 있는가?
- **퇴보한 질문:** 변경 후 정답을 잃은 질문이 있는가?
- **난이도별 패턴:** 특정 난이도(factual, analytical 등)에서만 성능이 변했는가?

### FULL_RAG 비교 시

Generation 메트릭이 포함된 Run을 비교할 때는 추가로 확인한다:

- **Faithfulness 변화:** 프롬프트 수정 후 할루시네이션이 줄었는가?
- **Answer Relevancy 변화:** 답변이 질문에 더 적절해졌는가?
- **Retrieval vs Generation:** 검색 메트릭은 그대로인데 생성 메트릭만 변한 경우, 프롬프트 변경의 효과로 판단할 수 있다.

## 실용적 워크플로우

### A/B 테스트 단계

1. **데이터셋 생성:** 평가 대상 노트북에서 데이터셋을 한 번 생성한다.
   ```bash
   python -m src.cli evaluation generate <notebook_id> --name "baseline-v1"
   ```

2. **Baseline 평가:** 현재 설정으로 평가를 실행하고 Run ID를 기록한다.
   ```bash
   python -m src.cli evaluation run <dataset_id> --k 5
   # -> Run ID: run_baseline
   ```

3. **시스템 변경:** 임베딩 모델, 청킹 전략, 프롬프트 등 하나의 변수를 수정한다.

4. **실험 평가:** 동일 데이터셋으로 다시 평가를 실행한다.
   ```bash
   python -m src.cli evaluation run <dataset_id> --k 5
   # -> Run ID: run_experiment
   ```

5. **비교:** 두 Run을 비교하여 개선 여부를 확인한다.
   ```bash
   python -m src.cli evaluation compare run_baseline run_experiment
   ```

6. **판단:** 메트릭이 개선되었으면 변경을 채택하고, 아니면 되돌린다.

7. **반복:** 다음 변경 사항에 대해 동일 과정을 반복한다.

### 모범 사례

- **한 번에 하나만 변경:** 여러 요소를 동시에 바꾸면 어떤 변경이 효과가 있었는지 알 수 없다.
- **동일 데이터셋 사용:** 공정한 비교를 위해 반드시 같은 데이터셋으로 평가한다.
- **Baseline 먼저:** 변경 전에 항상 baseline 평가를 먼저 실행한다.
- **기록 유지:** 각 Run에 어떤 설정을 사용했는지 별도로 기록한다 (Run ID + 설정 메모).
- **성공한 Run을 새 Baseline으로:** 개선이 확인된 설정을 새로운 baseline으로 삼고 다음 개선을 이어간다.
