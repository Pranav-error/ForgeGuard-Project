"""ForgeGuard -- Document Tamper Detection and Localisation module (FR-D1, FR-D2, FR-D6).

Prototype implementation of the assigned module from the System Design
Document: dual-stream (SRM + RGB) tamper localiser behind the fixed
`TamperLocalisationService.predict()` interface (NFR-7).
"""
from .infer import TamperLocalisationService
from .model import TamperLocaliser

__all__ = ["TamperLocalisationService", "TamperLocaliser"]
