from datetime import date
from unittest.mock import Mock

from dependency_injector import providers
from typer.testing import CliRunner

from frigo.cli.commands import build_cli
from frigo.domain.errors import IngredientNotFound
from frigo.use_cases.add_ingredient import AddIngredient
from frigo.use_cases.remove_ingredient import RemoveIngredient
from tests.container import build_test_container
from tests.object_mothers.ingredient import IngredientMother

runner = CliRunner()


def test_add_parses_quantity_and_expiry() -> None:
    add_ingredient = Mock(spec=AddIngredient)
    add_ingredient.execute.return_value = IngredientMother.fresh().build()
    cli = build_cli(build_test_container(add_ingredient=providers.Object(add_ingredient)))

    result = runner.invoke(cli, ["add", "eggs", "--qty", "6", "--expires", "2026-10-20"])

    assert result.exit_code == 0
    add_ingredient.execute.assert_called_once_with("eggs", 6, date(2026, 10, 20))


def test_removing_an_unknown_ingredient_exits_with_an_error() -> None:
    remove_ingredient = Mock(spec=RemoveIngredient)
    remove_ingredient.execute.side_effect = IngredientNotFound("eggs")
    cli = build_cli(build_test_container(remove_ingredient=providers.Object(remove_ingredient)))

    result = runner.invoke(cli, ["remove", "eggs"])

    assert result.exit_code == 1
    assert "No eggs in the fridge" in result.output
