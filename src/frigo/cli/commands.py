from datetime import datetime
from typing import Annotated, NoReturn

import typer

from frigo.container import Container
from frigo.domain.errors import IngredientNotFound, InvalidIngredientName, InvalidQuantity


def build_cli(container: Container) -> typer.Typer:
    cli = typer.Typer(no_args_is_help=True)

    @cli.command()
    def add(
        name: Annotated[str, typer.Argument(help="What you put in the fridge")],
        qty: Annotated[int, typer.Option(help="How many")] = 1,
        expires: Annotated[datetime | None, typer.Option(formats=["%Y-%m-%d"], help="Expiry date")] = None,
    ) -> None:
        try:
            ingredient = container.add_ingredient().execute(name, qty, expires.date() if expires else None)
        except InvalidIngredientName:
            _fail("An ingredient needs a name")
        except InvalidQuantity:
            _fail("Quantity must be at least 1")

        typer.echo(f"{ingredient.name}: {ingredient.quantity}")

    @cli.command()
    def remove(name: Annotated[str, typer.Argument(help="What you took out of the fridge")]) -> None:
        try:
            container.remove_ingredient().execute(name)
        except IngredientNotFound:
            _fail(f"No {name} in the fridge")

        typer.echo(f"Removed {name}")

    @cli.command("list")
    def list_() -> None:
        for ingredient in container.list_pantry().execute():
            expiry = f"  expires {ingredient.expires_on}" if ingredient.expires_on else ""
            typer.echo(f"{ingredient.quantity} x {ingredient.name}{expiry}")

    return cli


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)
