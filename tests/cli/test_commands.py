from datetime import date
from unittest.mock import Mock

from dependency_injector import providers
from typer.testing import CliRunner

from frigo.cli.commands import build_cli
from frigo.domain.errors import EmptyPantry, IngredientNotFound, RecipeRejected
from frigo.use_cases.add_ingredient import AddIngredient
from frigo.use_cases.remove_ingredient import RemoveIngredient
from frigo.use_cases.suggest_recipe import SuggestRecipe
from tests.container import build_test_container
from tests.object_mothers.ingredient import IngredientMother
from tests.object_mothers.recipe import RecipeMother

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


def test_cook_prints_the_recipe() -> None:
    suggest_recipe = Mock(spec=SuggestRecipe)
    suggest_recipe.execute.return_value = RecipeMother.omelette().build()
    cli = build_cli(build_test_container(suggest_recipe=providers.Object(suggest_recipe)))

    result = runner.invoke(cli, ["cook", "--servings", "4", "--missing", "1"])

    assert result.exit_code == 0
    assert "Omelette" in result.output
    assert "1. Beat the eggs" in result.output
    suggest_recipe.execute.assert_called_once_with(4, 1)


def test_cooking_from_an_empty_fridge_exits_with_an_error() -> None:
    suggest_recipe = Mock(spec=SuggestRecipe)
    suggest_recipe.execute.side_effect = EmptyPantry
    cli = build_cli(build_test_container(suggest_recipe=providers.Object(suggest_recipe)))

    result = runner.invoke(cli, ["cook"])

    assert result.exit_code == 1
    assert "The fridge is empty" in result.output


def test_rejected_recipe_exits_with_the_reason() -> None:
    suggest_recipe = Mock(spec=SuggestRecipe)
    suggest_recipe.execute.side_effect = RecipeRejected("not in the fridge: truffle")
    cli = build_cli(build_test_container(suggest_recipe=providers.Object(suggest_recipe)))

    result = runner.invoke(cli, ["cook"])

    assert result.exit_code == 1
    assert "not in the fridge: truffle" in result.output
