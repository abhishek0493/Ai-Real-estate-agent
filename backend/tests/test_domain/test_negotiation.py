"""Tests for the deterministic negotiation engine."""

import pytest

from app.domain.exceptions import NegotiationError
from app.domain.negotiation.engine import NegotiationResult, evaluate_budget


class TestAcceptable:
    def test_price_within_range(self) -> None:
        result = evaluate_budget(100_000, 200_000, 150_000)
        assert result == NegotiationResult.ACCEPTABLE

    def test_price_at_max(self) -> None:
        result = evaluate_budget(100_000, 200_000, 200_000)
        assert result == NegotiationResult.ACCEPTABLE

    def test_price_at_min(self) -> None:
        result = evaluate_budget(100_000, 200_000, 100_000)
        assert result == NegotiationResult.ACCEPTABLE

    def test_price_below_min(self) -> None:
        result = evaluate_budget(100_000, 200_000, 50_000)
        assert result == NegotiationResult.ACCEPTABLE


class TestSoftNegotiate:
    def test_1_percent_over(self) -> None:
        # 200_000 * 1.01 = 202_000
        result = evaluate_budget(100_000, 200_000, 202_000)
        assert result == NegotiationResult.SOFT_NEGOTIATE

    def test_5_percent_over_boundary(self) -> None:
        # 200_000 * 1.05 = 210_000 (exactly 5%)
        result = evaluate_budget(100_000, 200_000, 210_000)
        assert result == NegotiationResult.SOFT_NEGOTIATE


class TestSuggestAlternative:
    def test_6_percent_over(self) -> None:
        # 200_000 * 1.06 = 212_000
        result = evaluate_budget(100_000, 200_000, 212_000)
        assert result == NegotiationResult.SUGGEST_ALTERNATIVE

    def test_15_percent_over_boundary(self) -> None:
        # 200_000 * 1.15 = 230_000 (exactly 15%)
        result = evaluate_budget(100_000, 200_000, 230_000)
        assert result == NegotiationResult.SUGGEST_ALTERNATIVE


class TestOutOfRange:
    def test_16_percent_over(self) -> None:
        # 200_000 * 1.16 = 232_000
        result = evaluate_budget(100_000, 200_000, 232_000)
        assert result == NegotiationResult.OUT_OF_RANGE

    def test_way_over(self) -> None:
        result = evaluate_budget(100_000, 200_000, 500_000)
        assert result == NegotiationResult.OUT_OF_RANGE


class TestEdgeCasesAndErrors:
    def test_zero_property_price_raises(self) -> None:
        with pytest.raises(NegotiationError):
            evaluate_budget(100_000, 200_000, 0)

    def test_negative_property_price_raises(self) -> None:
        with pytest.raises(NegotiationError):
            evaluate_budget(100_000, 200_000, -10)

    def test_negative_budget_raises(self) -> None:
        with pytest.raises(NegotiationError):
            evaluate_budget(-1, 200_000, 150_000)

    def test_min_exceeds_max_raises(self) -> None:
        with pytest.raises(NegotiationError):
            evaluate_budget(300_000, 200_000, 150_000)
