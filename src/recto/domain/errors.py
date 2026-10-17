class RectoError(Exception):
    pass


class InvalidDeck(RectoError):
    pass


class DeckNotFound(RectoError):
    pass


class KnowledgeNotFound(RectoError):
    pass


class VariantNotFound(RectoError):
    pass


class OriginalIsReadOnly(RectoError):
    pass


class EmptyVariant(RectoError):
    pass


class ModelUnavailable(RectoError):
    pass
