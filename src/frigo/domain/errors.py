class FrigoError(Exception):
    pass


class InvalidIngredientName(FrigoError):
    pass


class InvalidQuantity(FrigoError):
    pass


class IngredientNotFound(FrigoError):
    pass


class ChefUnavailable(FrigoError):
    pass


class RecipeRejected(FrigoError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
