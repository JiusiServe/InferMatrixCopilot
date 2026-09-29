"""Public SDK v1 compatibility facade for provider-owned curation."""

from ...knowledge_service.curation import KnowledgeCurator, KnowledgeValidatorError

__all__ = ["KnowledgeCurator", "KnowledgeValidatorError"]
