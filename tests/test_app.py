from recto.app import RectoApp


async def test_the_app_is_called_recto() -> None:
    app = RectoApp()

    async with app.run_test():
        assert app.title == "Recto"


async def test_q_quits() -> None:
    app = RectoApp()

    async with app.run_test() as pilot:
        await pilot.press("q")

        assert app.return_code == 0
