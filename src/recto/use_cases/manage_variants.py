from recto.domain.errors import DeckNotFound, KnowledgeNotFound
from recto.domain.knowledge import Knowledge, new_variant
from recto.ports.deck_repository import DeckRepository
from recto.ports.variant_generator import VariantGenerator


class ListKnowledge:
    def __init__(self, repository: DeckRepository) -> None:
        self._repository = repository

    def execute(self, deck_id: str) -> list[Knowledge]:
        return self._repository.knowledge(deck_id)


class GetKnowledge:
    def __init__(self, repository: DeckRepository) -> None:
        self._repository = repository

    def execute(self, deck_id: str, knowledge_id: str) -> Knowledge:
        return _load(self._repository, deck_id, knowledge_id)


class AddVariant:
    def __init__(self, repository: DeckRepository) -> None:
        self._repository = repository

    def execute(self, deck_id: str, knowledge_id: str, question: str, answer: str) -> Knowledge:
        knowledge = _load(self._repository, deck_id, knowledge_id).with_variants(new_variant(question, answer))
        self._repository.save_knowledge(knowledge)
        return knowledge


class EditVariant:
    def __init__(self, repository: DeckRepository) -> None:
        self._repository = repository

    def execute(self, deck_id: str, knowledge_id: str, variant_id: str, question: str, answer: str) -> Knowledge:
        knowledge = _load(self._repository, deck_id, knowledge_id).with_edited_variant(variant_id, question, answer)
        self._repository.save_knowledge(knowledge)
        return knowledge


class DeleteVariant:
    def __init__(self, repository: DeckRepository) -> None:
        self._repository = repository

    def execute(self, deck_id: str, knowledge_id: str, variant_id: str) -> Knowledge:
        knowledge = _load(self._repository, deck_id, knowledge_id).without_variant(variant_id)
        self._repository.save_knowledge(knowledge)
        return knowledge


class GenerateVariant:
    def __init__(self, repository: DeckRepository, generator: VariantGenerator) -> None:
        self._repository = repository
        self._generator = generator

    def execute(self, deck_id: str, knowledge_id: str) -> Knowledge:
        deck = self._repository.deck(deck_id)
        if deck is None:
            raise DeckNotFound(deck_id)
        knowledge = _load(self._repository, deck_id, knowledge_id)
        knowledge = knowledge.with_variants(self._generator.generate_one(knowledge, deck.instructions))
        self._repository.save_knowledge(knowledge)
        return knowledge


def _load(repository: DeckRepository, deck_id: str, knowledge_id: str) -> Knowledge:
    knowledge = repository.get_knowledge(deck_id, knowledge_id)
    if knowledge is None:
        raise KnowledgeNotFound(knowledge_id)
    return knowledge
