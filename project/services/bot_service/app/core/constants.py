"""Ключи и имена сущностей Redis, общие для бота и Celery-воркера."""

import re

OUTBOX_LIST_KEY = "max:outbox"

# Максимальная длина пользовательского промпта (защита от Prompt Injection и resource exhaustion)
MAX_PROMPT_LENGTH = 4000

# Список подозрительных паттернов (jailbreak / prompt injection).
# При обнаружении промпт блокируется и логируется как угроза.
# Включает английские и русские формулировки + перефразированные варианты.
SUSPICIOUS_PATTERNS: list[re.Pattern[str]] = [
    # === Английские jailbreak-паттерны ===
    re.compile(r"ignore\s+(all\s+)?(previous|above)?\s*(instructions?|prompts?|rules?)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above)?\s*(instructions?|rules?|prompts?)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|previous|above)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now", re.IGNORECASE),
    re.compile(r"act\s+as\s+if", re.IGNORECASE),
    re.compile(r"developer\s+mode", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(your|the)\s+(instructions?|rules?|prompt)", re.IGNORECASE),
    re.compile(r"what\s+are\s+your\s+(rules?|instructions?)", re.IGNORECASE),
    re.compile(r"override\s+(previous|all)\s+(instructions?|rules?)", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
    re.compile(r"from\s+now\s+on", re.IGNORECASE),
    re.compile(r"pretend\s+to\s+be", re.IGNORECASE),

    # === Русские jailbreak-паттерны ===
    re.compile(r"игнорируй\s+(предыдущие|все|вышестоящие)\s+(инструкции|правила|промпт)", re.IGNORECASE),
    re.compile(r"забудь\s+(вс[её]|предыдущ[ие]|вс[её]\s+выше)", re.IGNORECASE),
    re.compile(r"ты\s+теперь", re.IGNORECASE),
    re.compile(r"действуй\s+как", re.IGNORECASE),
    re.compile(r"режим\s+разработчика", re.IGNORECASE),
    re.compile(r"джейлбрейк|jailbreak", re.IGNORECASE),
    re.compile(r"системн[ыи][йе]\s+промпт", re.IGNORECASE),
    re.compile(r"раскрой\s+(свои|сво[её])\s+(инструкции|правила|промпт)", re.IGNORECASE),
    re.compile(r"какие\s+у\s+тебя\s+(правила|инструкции)", re.IGNORECASE),
    re.compile(r"переопредел[иь]\s+(предыдущие|все)\s+(инструкции|правила)", re.IGNORECASE),
    re.compile(r"новые\s+инструкции[:：]", re.IGNORECASE),
    re.compile(r"с\s+этого\s+момента", re.IGNORECASE),
    re.compile(r"притворись|изображай", re.IGNORECASE),
]


def is_prompt_suspicious(text: str) -> bool:
    """Возвращает True, если промпт содержит подозрительный (jailbreak) паттерн."""
    return any(pattern.search(text) for pattern in SUSPICIOUS_PATTERNS)


def max_auth_key(max_user_id: str) -> str:
    return f"max_auth:{max_user_id}"


def user_chat_key(sub: str) -> str:
    return f"user_chat:{sub}"
