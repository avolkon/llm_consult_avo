import logging

from maxapi import Dispatcher
from maxapi.types import BotStarted, Command, Message, MessageCreated

from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis
from app.services.auth_mapping import get_auth, register_token
from app.tasks.llm_tasks import llm_request

log = logging.getLogger(__name__)


def _message_plain_text(message: Message) -> str:
    if message.body is None or message.body.text is None:
        return ""
    return message.body.text.strip()


def _max_user_id_from_message(message: Message) -> str:
    cid = message.recipient.chat_id
    if cid is None:
        msg = "У сообщения нет recipient.chat_id"
        raise ValueError(msg)
    return str(cid)


async def process_token_command(token: str, max_user_id: str) -> str:
    payload = decode_and_validate(token)
    await register_token(await get_redis(), max_user_id, payload)
    return "Токен принят. Можно отправлять текст для LLM."


async def process_user_text(text: str, max_user_id: str) -> str:
    auth = await get_auth(await get_redis(), max_user_id)
    if auth is None:
        return "Сначала авторизуйтесь: /token <JWT от auth_service>"

    sub, role = auth
    try:
        llm_request.delay(sub, role, text)
    except Exception:
        log.exception("Не удалось отправить задачу в Celery")
        return "Сервис временно недоступен. Попробуйте позже."
    return "Запрос отправлен, ответ появится в этом чате."


def register_handlers(dp: Dispatcher) -> None:
    @dp.bot_started()
    async def on_bot_started(event: BotStarted) -> None:
        await event.bot.send_message(
            chat_id=event.chat_id,
            text=(
                "Чат-бот MAX: отправьте /start. "
                "Для доступа к LLM: /token <JWT> от auth_service."
            ),
        )

    @dp.message_created(Command("start"))
    async def on_start(event: MessageCreated) -> None:
        await event.message.answer(
            "Сервис LLM-консультаций (мессенджер MAX). "
            "Авторизуйтесь: /token <ваш_JWT>."
        )

    @dp.message_created(Command("token"))
    async def on_token(event: MessageCreated, args: list[str]) -> None:
        if not args:
            await event.message.answer(
                "Пришлите JWT одним сообщением: /token <ваш_JWT>",
            )
            return
        token = args[0]
        max_user_id = _max_user_id_from_message(event.message)
        try:
            response = await process_token_command(token, max_user_id)
        except ValueError as exc:
            await event.message.answer(str(exc))
            return
        await event.message.answer(response)

    @dp.message_created()
    async def on_message(event: MessageCreated) -> None:
        text = _message_plain_text(event.message)
        if not text:
            return
        if text.startswith("/"):
            return

        max_user_id = _max_user_id_from_message(event.message)
        response = await process_user_text(text, max_user_id)
        await event.message.answer(response)
