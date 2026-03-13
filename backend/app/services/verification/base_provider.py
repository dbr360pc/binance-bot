"""
Base verification provider interface.
All providers must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class VerificationResult:
    passed: bool
    provider: str
    detail: str
    raw: Optional[dict] = None
