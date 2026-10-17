from dependency_injector import containers, providers

from recto.adapters.pydantic_ai_models import PydanticAIAnswerJudge, PydanticAIVariantGenerator
from recto.adapters.sqlite_deck_repository import SqliteDeckRepository
from recto.adapters.system_clock import SystemClock
from recto.ports.answer_judge import AnswerJudge
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository
from recto.ports.variant_generator import VariantGenerator
from recto.use_cases.import_deck import ImportDeck
from recto.use_cases.list_decks import ListDecks
from recto.use_cases.manage_variants import (
    AddVariant,
    DeleteVariant,
    EditVariant,
    GenerateVariant,
    GetKnowledge,
    ListKnowledge,
)
from recto.use_cases.next_card import NextCard
from recto.use_cases.submit_answer import SubmitAnswer


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    deck_repository: providers.Provider[DeckRepository] = providers.Singleton(SqliteDeckRepository, path=config.db)
    variant_generator: providers.Provider[VariantGenerator] = providers.Singleton(
        PydanticAIVariantGenerator, model=config.model
    )
    answer_judge: providers.Provider[AnswerJudge] = providers.Singleton(PydanticAIAnswerJudge, model=config.model)
    clock: providers.Provider[Clock] = providers.Singleton(SystemClock)

    import_deck = providers.Factory(ImportDeck, repository=deck_repository, generator=variant_generator)
    list_decks = providers.Factory(ListDecks, repository=deck_repository, clock=clock)
    next_card = providers.Factory(NextCard, repository=deck_repository, clock=clock)
    submit_answer = providers.Factory(SubmitAnswer, repository=deck_repository, judge=answer_judge, clock=clock)
    list_knowledge = providers.Factory(ListKnowledge, repository=deck_repository)
    get_knowledge = providers.Factory(GetKnowledge, repository=deck_repository)
    add_variant = providers.Factory(AddVariant, repository=deck_repository)
    edit_variant = providers.Factory(EditVariant, repository=deck_repository)
    delete_variant = providers.Factory(DeleteVariant, repository=deck_repository)
    generate_variant = providers.Factory(GenerateVariant, repository=deck_repository, generator=variant_generator)
