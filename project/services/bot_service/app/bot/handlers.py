import logging

from maxapi import Dispatcher
from maxapi.types import BotStarted, Command, Message, MessageCreated
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.constants import (
    MAX_HANDLED_MID_TTL_SEC,
    MAX_HANDLED_TURN_TTL_SEC,
    MAX_PROMPT_LENGTH,
    handled_mid_redis_key,
    handled_turn_redis_key,
    is_prompt_suspicious,
)
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


async def acquire_incoming_message_once(redis: Redis, message: Message) -> bool:
    """Идемпотентность входящих сообщений: mid и (чат + текст + timestamp с API).

    MAX иногда отдаёт два message_created с разными mid при одной реплике пользователя.
    """
    text = _message_plain_text(message)
    try:
        uid = _max_user_id_from_message(message)
    except ValueError:
        uid = ""

    if uid and text:
        tk = handled_turn_redis_key(uid, text, int(message.timestamp))
        if not await redis.set(tk, "1", ex=MAX_HANDLED_TURN_TTL_SEC, nx=True):
            log.debug(
                "Пропуск дубля (тот же текст, чат и timestamp) uid=%s ts=%s",
                uid,
                message.timestamp,
            )
            return False

    if message.body is None or not message.body.mid:
        return True

    mk = handled_mid_redis_key(message.body.mid)
    if not await redis.set(mk, "1", ex=MAX_HANDLED_MID_TTL_SEC, nx=True):
        log.debug("Пропуск дубля message_created mid=%s", message.body.mid)
        return False
    return True


async def process_token_command(redis: Redis, token: str, max_user_id: str) -> str:
    payload = decode_and_validate(token)
    await register_token(redis, max_user_id, payload)
    return "Токен принят. Можно отправлять текст для LLM."


async def process_user_text(redis: Redis, text: str, max_user_id: str) -> str:
    auth = await get_auth(redis, max_user_id)
    if auth is None:
        return "Сначала авторизуйтесь: /token <JWT от auth_service>"

    if len(text) > MAX_PROMPT_LENGTH:
        return f"Сообщение слишком длинное (макс. {MAX_PROMPT_LENGTH} символов)."

    sub, role = auth

    if get_settings().log_prompt_content:
        log.info(
            "LLM prompt received | sub=%s | max_user_id=%s | length=%d | prompt=%r",
            sub,
            max_user_id,
            len(text),
            text[:200],
        )
    else:
        log.info(
            "LLM prompt received | sub=%s | max_user_id=%s | length=%d",
            sub,
            max_user_id,
            len(text),
        )

    if is_prompt_suspicious(text):
        if get_settings().log_prompt_content:
            log.warning(
                "SUSPICIOUS PROMPT BLOCKED | sub=%s | max_user_id=%s | prompt=%r",
                sub,
                max_user_id,
                text[:200],
            )
        else:
            log.warning(
                "SUSPICIOUS PROMPT BLOCKED | sub=%s | max_user_id=%s | length=%d",
                sub,
                max_user_id,
                len(text),
            )
        return "Запрос отклонён: обнаружен потенциально опасный паттерн."

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
        redis = await get_redis()
        if not await acquire_incoming_message_once(redis, event.message):
            return
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
        redis = await get_redis()
        if not await acquire_incoming_message_once(redis, event.message):
            return
        try:
            response = await process_token_command(redis, token, max_user_id)
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
        redis = await get_redis()
        if not await acquire_incoming_message_once(redis, event.message):
            return
        response = await process_user_text(redis, text, max_user_id)
        await event.message.answer(response)
