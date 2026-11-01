from recto.domain.today import NEW_PER_DAY
from recto.ports.clock import Clock
from recto.ports.deck_repository import DeckRepository


class LearnMore:
    def __init__(self, repository: DeckRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def execute(self, deck_id: str) -> None:
        self._repository.add_extra_new(deck_id, self._clock.now().date(), NEW_PER_DAY)
