"""Retrieval evaluation metric functions.

Pure functions with no external dependencies.
"""


def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Calculate Precision@k.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        Fraction of top-k retrieved items that are relevant.
    """
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_count = sum(1 for rid in top_k if rid in relevant_ids)
    return relevant_count / len(top_k)


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Calculate Recall@k.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        Fraction of relevant items that appear in top-k results.
    """
    if not relevant_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for rid in top_k if rid in relevant_ids)
    return relevant_count / len(relevant_ids)


def hit_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> bool:
    """Calculate Hit@k (binary).

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        True if at least one relevant item appears in top-k.
    """
    if not relevant_ids or k <= 0:
        return False
    top_k = retrieved_ids[:k]
    return any(rid in relevant_ids for rid in top_k)


def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Calculate Reciprocal Rank (within top-k).

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        1/rank of the first relevant item, or 0.0 if none found.
    """
    if not relevant_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    for rank, rid in enumerate(top_k, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


def aggregate_metrics(
    precisions: list[float],
    recalls: list[float],
    hits: list[bool],
    reciprocal_ranks: list[float],
) -> tuple[float, float, float, float]:
    """Calculate aggregate metrics across all test cases.

    Args:
        precisions: Per-case precision values.
        recalls: Per-case recall values.
        hits: Per-case hit values.
        reciprocal_ranks: Per-case reciprocal rank values.

    Returns:
        Tuple of (mean_precision, mean_recall, hit_rate, mrr).
    """
    if not precisions:
        return (0.0, 0.0, 0.0, 0.0)

    count = len(precisions)
    mean_precision = sum(precisions) / count
    mean_recall = sum(recalls) / count
    hit_rate = sum(1 for h in hits if h) / count
    mrr = sum(reciprocal_ranks) / count

    return (mean_precision, mean_recall, hit_rate, mrr)


def aggregate_generation_metrics(
    faithfulness_scores: list[float],
    relevancy_scores: list[float],
) -> tuple[float, float]:
    """Calculate aggregate generation metrics.

    Args:
        faithfulness_scores: Per-case faithfulness values.
        relevancy_scores: Per-case answer relevancy values.

    Returns:
        Tuple of (mean_faithfulness, mean_answer_relevancy).
    """
    if not faithfulness_scores:
        return (0.0, 0.0)

    mean_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
    mean_relevancy = sum(relevancy_scores) / len(relevancy_scores)

    return (mean_faithfulness, mean_relevancy)
