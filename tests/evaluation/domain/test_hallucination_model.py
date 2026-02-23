"""Tests for hallucination-related domain models."""

import pydantic
import pytest

from src.evaluation.domain import model


class TestClaimVerdict:
    """Tests for ClaimVerdict enum."""

    def test_supported_value(self) -> None:
        assert model.ClaimVerdict.SUPPORTED == "supported"

    def test_partially_supported_value(self) -> None:
        assert model.ClaimVerdict.PARTIALLY_SUPPORTED == "partially_supported"

    def test_contradicted_value(self) -> None:
        assert model.ClaimVerdict.CONTRADICTED == "contradicted"

    def test_fabricated_value(self) -> None:
        assert model.ClaimVerdict.FABRICATED == "fabricated"

    def test_unverifiable_value(self) -> None:
        assert model.ClaimVerdict.UNVERIFIABLE == "unverifiable"

    def test_all_members_count(self) -> None:
        assert len(model.ClaimVerdict) == 5


class TestClaimAnalysis:
    """Tests for ClaimAnalysis value object."""

    def test_create_claim_analysis(self) -> None:
        claim = model.ClaimAnalysis(
            claim_text="The sky is blue.",
            verdict=model.ClaimVerdict.SUPPORTED,
            supporting_chunk_indices=(0, 2),
            reasoning="Evidence found in chunks 0 and 2.",
        )
        expected = model.ClaimAnalysis(
            claim_text="The sky is blue.",
            verdict=model.ClaimVerdict.SUPPORTED,
            supporting_chunk_indices=(0, 2),
            reasoning="Evidence found in chunks 0 and 2.",
        )
        assert claim == expected

    def test_frozen(self) -> None:
        claim = model.ClaimAnalysis(
            claim_text="Test",
            verdict=model.ClaimVerdict.FABRICATED,
            supporting_chunk_indices=(),
            reasoning="No evidence.",
        )
        with pytest.raises(pydantic.ValidationError):
            claim.claim_text = "Modified"  # type: ignore[misc]

    def test_forbids_extra_fields(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            model.ClaimAnalysis(
                claim_text="Test",
                verdict=model.ClaimVerdict.SUPPORTED,
                supporting_chunk_indices=(),
                reasoning="Ok",
                extra_field="not allowed",  # type: ignore[call-arg]
            )

    def test_empty_supporting_indices(self) -> None:
        claim = model.ClaimAnalysis(
            claim_text="No support",
            verdict=model.ClaimVerdict.UNVERIFIABLE,
            supporting_chunk_indices=(),
            reasoning="Cannot verify.",
        )
        assert claim.supporting_chunk_indices == ()


class TestHallucinationAnalysis:
    """Tests for HallucinationAnalysis value object."""

    def test_create_hallucination_analysis(self) -> None:
        claim = model.ClaimAnalysis(
            claim_text="Claim 1",
            verdict=model.ClaimVerdict.SUPPORTED,
            supporting_chunk_indices=(0,),
            reasoning="Supported.",
        )
        analysis = model.HallucinationAnalysis(
            claims=(claim,),
            total_claims=1,
            supported_count=1,
            partially_supported_count=0,
            contradicted_count=0,
            fabricated_count=0,
            unverifiable_count=0,
            hallucination_rate=0.0,
            faithfulness_score=1.0,
        )
        expected = model.HallucinationAnalysis(
            claims=(claim,),
            total_claims=1,
            supported_count=1,
            partially_supported_count=0,
            contradicted_count=0,
            fabricated_count=0,
            unverifiable_count=0,
            hallucination_rate=0.0,
            faithfulness_score=1.0,
        )
        assert analysis == expected

    def test_frozen(self) -> None:
        analysis = model.HallucinationAnalysis(
            claims=(),
            total_claims=0,
            supported_count=0,
            partially_supported_count=0,
            contradicted_count=0,
            fabricated_count=0,
            unverifiable_count=0,
            hallucination_rate=0.0,
            faithfulness_score=0.0,
        )
        with pytest.raises(pydantic.ValidationError):
            analysis.total_claims = 5  # type: ignore[misc]

    def test_forbids_extra_fields(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            model.HallucinationAnalysis(
                claims=(),
                total_claims=0,
                supported_count=0,
                partially_supported_count=0,
                contradicted_count=0,
                fabricated_count=0,
                unverifiable_count=0,
                hallucination_rate=0.0,
                faithfulness_score=0.0,
                bonus="nope",  # type: ignore[call-arg]
            )

    def test_mixed_verdicts(self) -> None:
        claims = (
            model.ClaimAnalysis(
                claim_text="Supported claim",
                verdict=model.ClaimVerdict.SUPPORTED,
                supporting_chunk_indices=(0,),
                reasoning="Ok.",
            ),
            model.ClaimAnalysis(
                claim_text="Contradicted claim",
                verdict=model.ClaimVerdict.CONTRADICTED,
                supporting_chunk_indices=(),
                reasoning="Wrong.",
            ),
            model.ClaimAnalysis(
                claim_text="Fabricated claim",
                verdict=model.ClaimVerdict.FABRICATED,
                supporting_chunk_indices=(),
                reasoning="Made up.",
            ),
        )
        analysis = model.HallucinationAnalysis(
            claims=claims,
            total_claims=3,
            supported_count=1,
            partially_supported_count=0,
            contradicted_count=1,
            fabricated_count=1,
            unverifiable_count=0,
            hallucination_rate=2.0 / 3.0,
            faithfulness_score=1.0 / 3.0,
        )
        assert analysis.total_claims == 3
        assert analysis.contradicted_count == 1
        assert analysis.fabricated_count == 1
        assert abs(analysis.hallucination_rate - 2.0 / 3.0) < 1e-9
        assert abs(analysis.faithfulness_score - 1.0 / 3.0) < 1e-9
