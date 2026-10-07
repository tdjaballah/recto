from ollama import Client, ResponseError
from pydantic import ValidationError

from frigo.adapters.chef_prompt import INSTRUCTIONS, MAX_TOKENS, RecipeDraft, prompt
from frigo.domain.errors import ChefUnavailable
from frigo.domain.recipe import Recipe
from frigo.ports.chef import Chef, RecipeRequest


class OllamaChef(Chef):
    def __init__(self, client: Client, model: str) -> None:
        self._client = client
        self._model = model

    def suggest(self, request: RecipeRequest) -> Recipe:
        try:
            response = self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": INSTRUCTIONS},
                    {"role": "user", "content": prompt(request)},
                ],
                format=RecipeDraft.model_json_schema(),
                options={"num_predict": MAX_TOKENS},
            )
            draft = RecipeDraft.model_validate_json(response.message.content or "")
        except (ResponseError, ConnectionError, ValidationError) as error:
            raise ChefUnavailable(str(error)) from error

        return draft.to_recipe()
