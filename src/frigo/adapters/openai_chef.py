from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from frigo.adapters.chef_prompt import INSTRUCTIONS, MAX_TOKENS, RecipeDraft, prompt
from frigo.domain.errors import ChefUnavailable
from frigo.domain.recipe import Recipe
from frigo.ports.chef import Chef, RecipeRequest


class OpenAIChef(Chef):
    def __init__(self, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def suggest(self, request: RecipeRequest) -> Recipe:
        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=INSTRUCTIONS,
                input=prompt(request),
                text_format=RecipeDraft,
                max_output_tokens=MAX_TOKENS,
            )
        except (OpenAIError, ValidationError) as error:
            raise ChefUnavailable(str(error)) from error

        draft = response.output_parsed
        if draft is None:
            raise ChefUnavailable("the model returned no recipe")
        return draft.to_recipe()
