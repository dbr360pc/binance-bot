from app.services.verification.base_provider import VerificationResult


class ManualReviewProvider:
    """
    Manual review provider - no automatic verification.
    Operator must verify payment externally.
    """
    name = "manual"

    async def verify(self, order_id: str, expected_amount: float, **kwargs) -> VerificationResult:
        return VerificationResult(
            passed=False,
            provider=self.name,
            detail="Manual review required. No bank verification provider is active.",
        )
