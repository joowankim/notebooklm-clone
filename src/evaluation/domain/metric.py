"""Retrieval evaluation metric functions.

Pure functions with no external dependencies.
"""

import math


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


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity, or 0.0 for zero vectors.
    """
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def ndcg_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """NDCG@k with binary relevance.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        Normalized Discounted Cumulative Gain at k.
    """
    if k <= 0 or not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    dcg = sum(
        1.0 / math.log2(i + 2)
        for i, rid in enumerate(top_k)
        if rid in relevant_ids
    )
    ideal_count = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_count))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def average_precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Average Precision at k.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        AP@k = (1/|relevant|) * sum(precision@i * rel_i) for i=1..k.
    """
    if k <= 0 or not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_count = 0
    precision_sum = 0.0
    for i, rid in enumerate(top_k, start=1):
        if rid in relevant_ids:
            relevant_count += 1
            precision_sum += relevant_count / i
    if relevant_count == 0:
        return 0.0
    return precision_sum / len(relevant_ids)


def complete_context_rate(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Check if all relevant items appear in top-k (binary).

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        k: Number of top results to consider.

    Returns:
        1.0 if all relevant items are in top-k, else 0.0.
        Returns 1.0 for empty relevant set.
    """
    if not relevant_ids:
        return 1.0
    if k <= 0:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return 1.0 if relevant_ids.issubset(top_k) else 0.0


def citation_precision(
    cited_chunk_ids: list[str],
    relevant_chunk_ids: set[str],
) -> float:
    """Fraction of cited chunks that are relevant.

    Args:
        cited_chunk_ids: List of cited chunk IDs.
        relevant_chunk_ids: Set of relevant chunk IDs.

    Returns:
        Precision of citations.
    """
    if not cited_chunk_ids:
        return 0.0
    relevant_count = sum(
        1 for cid in cited_chunk_ids if cid in relevant_chunk_ids
    )
    return relevant_count / len(cited_chunk_ids)


def citation_recall(
    cited_chunk_ids: list[str],
    relevant_chunk_ids: set[str],
) -> float:
    """Fraction of relevant chunks that are cited.

    Args:
        cited_chunk_ids: List of cited chunk IDs.
        relevant_chunk_ids: Set of relevant chunk IDs.

    Returns:
        Recall of citations.
    """
    if not relevant_chunk_ids:
        return 0.0
    cited_set = set(cited_chunk_ids)
    cited_count = sum(
        1 for rid in relevant_chunk_ids if rid in cited_set
    )
    return cited_count / len(relevant_chunk_ids)


def phantom_citation_count(
    citation_indices: list[int],
    retrieved_chunk_count: int,
) -> int:
    """Count of citation indices exceeding retrieved chunk count.

    Args:
        citation_indices: List of citation indices (0-based).
        retrieved_chunk_count: Number of retrieved chunks.

    Returns:
        Number of phantom (out-of-range) citations.
    """
    return sum(
        1 for idx in citation_indices if idx >= retrieved_chunk_count
    )
