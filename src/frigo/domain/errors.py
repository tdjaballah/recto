class FrigoError(Exception):
    pass


class InvalidIngredientName(FrigoError):
    pass


class InvalidQuantity(FrigoError):
    pass


class IngredientNotFound(FrigoError):
    pass
