import logging

from maxapi import Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

log = logging.getLogger(__name__)


def register_handlers(dp: Dispatcher) -> None:
    @dp.bot_started()
    async def on_bot_started(event: BotStarted) -> None:
        await event.bot.send_message(
            chat_id=event.chat_id,
            text=(
                "Чат-бот MAX: отправьте /start. "
                "Для доступа к LLM понадобится JWT от auth_service."
            ),
        )

    @dp.message_created(Command("start"))
    async def on_start(event: MessageCreated) -> None:
        await event.message.answer(
            "Сервис LLM-консультаций (мессенджер MAX). "
            "Дальнейшая логика — проверка JWT и задачи Celery."
        )

    @dp.message_created(Command("token"))
    async def on_token(event: MessageCreated) -> None:
        await event.message.answer(
            "Пришлите валидный JWT текстом; сверка с auth_service будет в следующих этапах."
        )

    @dp.message_created()
    async def on_message(event: MessageCreated) -> None:
        body = (event.message.body or "").strip()
        if not body:
            return
        log.debug("MAX message len=%s", len(body))
        await event.message.answer(
            "Сообщение принято. Полный поток JWT → Celery → LLM подключается в разработке."
        )
