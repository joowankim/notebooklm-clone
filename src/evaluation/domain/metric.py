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


def score_gap(
    retrieved_ids: list[str],
    retrieved_scores: list[float],
    relevant_ids: set[str],
) -> float | None:
    """Mean score difference between GT and non-GT chunks.

    Args:
        retrieved_ids: List of retrieved chunk IDs.
        retrieved_scores: Corresponding scores for each chunk.
        relevant_ids: Set of relevant (ground truth) chunk IDs.

    Returns:
        Mean GT score minus mean non-GT score, or None if either group is empty.
    """
    gt_scores: list[float] = []
    non_gt_scores: list[float] = []
    for rid, score in zip(retrieved_ids, retrieved_scores):
        if rid in relevant_ids:
            gt_scores.append(score)
        else:
            non_gt_scores.append(score)
    if not gt_scores or not non_gt_scores:
        return None
    mean_gt = sum(gt_scores) / len(gt_scores)
    mean_non_gt = sum(non_gt_scores) / len(non_gt_scores)
    return mean_gt - mean_non_gt


def high_confidence_rate(
    retrieved_ids: list[str],
    retrieved_scores: list[float],
    relevant_ids: set[str],
    margin: float = 0.1,
) -> float:
    """Fraction where min GT score exceeds max non-GT score by margin.

    Args:
        retrieved_ids: List of retrieved chunk IDs.
        retrieved_scores: Corresponding scores for each chunk.
        relevant_ids: Set of relevant (ground truth) chunk IDs.
        margin: Required score margin.

    Returns:
        1.0 if min GT > max non-GT + margin, else 0.0.
        Returns 0.0 if either group is empty.
    """
    gt_scores: list[float] = []
    non_gt_scores: list[float] = []
    for rid, score in zip(retrieved_ids, retrieved_scores):
        if rid in relevant_ids:
            gt_scores.append(score)
        else:
            non_gt_scores.append(score)
    if not gt_scores or not non_gt_scores:
        return 0.0
    min_gt = min(gt_scores)
    max_non_gt = max(non_gt_scores)
    return 1.0 if min_gt > max_non_gt + margin else 0.0


def mean_relevant_score(
    retrieved_ids: list[str],
    retrieved_scores: list[float],
    relevant_ids: set[str],
) -> float:
    """Mean score of relevant chunks.

    Args:
        retrieved_ids: List of retrieved chunk IDs.
        retrieved_scores: Corresponding scores for each chunk.
        relevant_ids: Set of relevant (ground truth) chunk IDs.

    Returns:
        Mean score of relevant chunks, or 0.0 if none found.
    """
    scores = [
        score
        for rid, score in zip(retrieved_ids, retrieved_scores)
        if rid in relevant_ids
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def mean_irrelevant_score(
    retrieved_ids: list[str],
    retrieved_scores: list[float],
    relevant_ids: set[str],
) -> float:
    """Mean score of irrelevant chunks.

    Args:
        retrieved_ids: List of retrieved chunk IDs.
        retrieved_scores: Corresponding scores for each chunk.
        relevant_ids: Set of relevant (ground truth) chunk IDs.

    Returns:
        Mean score of irrelevant chunks, or 0.0 if none found.
    """
    scores = [
        score
        for rid, score in zip(retrieved_ids, retrieved_scores)
        if rid not in relevant_ids
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def pearson_correlation(
    xs: list[float],
    ys: list[float],
) -> float | None:
    """Pearson correlation coefficient.

    Args:
        xs: First list of values.
        ys: Second list of values.

    Returns:
        Pearson r, or None if fewer than 3 data points or zero variance.
    """
    n = len(xs)
    if n < 3:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0.0 or var_y == 0.0:
        return None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return cov / math.sqrt(var_x * var_y)


def bucket_generation_quality(
    results: list[tuple[float, float, float]],
) -> dict[str, tuple[float, float]]:
    """Bucket generation quality by recall level.

    Each result tuple is (recall, faithfulness, relevancy).
    Buckets: recall=1.0 -> "perfect", 0<recall<1 -> "partial", recall=0 -> "missed".

    Args:
        results: List of (recall, faithfulness, relevancy) tuples.

    Returns:
        Dict mapping bucket name to (mean_faithfulness, mean_relevancy).
    """
    buckets: dict[str, list[tuple[float, float]]] = {}
    for recall, faithfulness, relevancy in results:
        if recall == 1.0:
            label = "perfect"
        elif recall == 0.0:
            label = "missed"
        else:
            label = "partial"
        if label not in buckets:
            buckets[label] = []
        buckets[label].append((faithfulness, relevancy))
    output: dict[str, tuple[float, float]] = {}
    for label, pairs in buckets.items():
        mean_f = sum(f for f, _ in pairs) / len(pairs)
        mean_r = sum(r for _, r in pairs) / len(pairs)
        output[label] = (mean_f, mean_r)
    return output


def answer_consistency(
    embeddings: list[list[float]],
) -> float:
    """Mean pairwise cosine similarity of embeddings.

    Args:
        embeddings: List of embedding vectors.

    Returns:
        Mean pairwise cosine similarity, or 0.0 for single/empty list.
    """
    n = len(embeddings)
    if n < 2:
        return 0.0
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += cosine_similarity(embeddings[i], embeddings[j])
            count += 1
    if count == 0:
        return 0.0
    return total / count


def aggregate_ndcg_map(
    ndcgs: list[float],
    map_scores: list[float],
) -> tuple[float, float]:
    """Calculate mean NDCG and MAP.

    Args:
        ndcgs: Per-case NDCG values.
        map_scores: Per-case MAP values.

    Returns:
        Tuple of (mean_ndcg, mean_map).
    """
    if not ndcgs:
        return (0.0, 0.0)
    mean_ndcg = sum(ndcgs) / len(ndcgs)
    mean_map = sum(map_scores) / len(map_scores)
    return (mean_ndcg, mean_map)


def aggregate_citation_metrics(
    citation_precisions: list[float],
    citation_recalls: list[float],
    phantom_counts: list[int],
) -> tuple[float, float, float]:
    """Mean citation precision, recall, and phantom count.

    Args:
        citation_precisions: Per-case citation precision values.
        citation_recalls: Per-case citation recall values.
        phantom_counts: Per-case phantom citation counts.

    Returns:
        Tuple of (mean_precision, mean_recall, mean_phantom_count).
    """
    if not citation_precisions:
        return (0.0, 0.0, 0.0)
    n = len(citation_precisions)
    mean_p = sum(citation_precisions) / n
    mean_r = sum(citation_recalls) / n
    mean_ph = sum(phantom_counts) / n
    return (mean_p, mean_r, mean_ph)


def intra_document_similarity(
    embeddings_by_doc: dict[str, list[list[float]]],
) -> float:
    """Mean pairwise cosine similarity within each document.

    For each document, computes all pairwise similarities among its
    embeddings and averages across all pairs across all documents.

    Args:
        embeddings_by_doc: Mapping of document ID to list of embeddings.

    Returns:
        Mean intra-document similarity, or 0.0 if no valid pairs exist.
    """
    total = 0.0
    count = 0
    for embeddings in embeddings_by_doc.values():
        n = len(embeddings)
        for i in range(n):
            for j in range(i + 1, n):
                total += cosine_similarity(embeddings[i], embeddings[j])
                count += 1
    if count == 0:
        return 0.0
    return total / count


def inter_document_similarity(
    embeddings_by_doc: dict[str, list[list[float]]],
) -> float:
    """Mean pairwise cosine similarity across different documents.

    For each pair of documents, compares each embedding from one document
    with each embedding from the other and averages all cross-document pairs.

    Args:
        embeddings_by_doc: Mapping of document ID to list of embeddings.

    Returns:
        Mean inter-document similarity, or 0.0 if fewer than 2 documents.
    """
    doc_keys = list(embeddings_by_doc.keys())
    if len(doc_keys) < 2:
        return 0.0
    total = 0.0
    count = 0
    for i in range(len(doc_keys)):
        for j in range(i + 1, len(doc_keys)):
            embs_a = embeddings_by_doc[doc_keys[i]]
            embs_b = embeddings_by_doc[doc_keys[j]]
            for vec_a in embs_a:
                for vec_b in embs_b:
                    total += cosine_similarity(vec_a, vec_b)
                    count += 1
    if count == 0:
        return 0.0
    return total / count


def separation_ratio(intra: float, inter: float) -> float:
    """Ratio of intra-document to inter-document similarity.

    Higher values indicate documents are internally coherent but
    distinct from each other.

    Args:
        intra: Intra-document similarity score.
        inter: Inter-document similarity score.

    Returns:
        intra / inter, or 0.0 if inter is zero.
    """
    if inter == 0.0:
        return 0.0
    return intra / inter


def adjacent_chunk_similarity(
    ordered_embeddings: list[list[float]],
) -> float:
    """Mean cosine similarity between consecutive embedding pairs.

    Args:
        ordered_embeddings: Ordered list of embedding vectors.

    Returns:
        Mean similarity of adjacent pairs, or 0.0 if fewer than 2.
    """
    n = len(ordered_embeddings)
    if n < 2:
        return 0.0
    total = 0.0
    for i in range(n - 1):
        total += cosine_similarity(
            ordered_embeddings[i], ordered_embeddings[i + 1]
        )
    return total / (n - 1)
