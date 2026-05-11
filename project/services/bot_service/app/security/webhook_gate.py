"""Дополнительная защита входящего webhook MAX до maxapi (секрет, allowlist IP)."""

from __future__ import annotations

import ipaddress
import secrets
from ipaddress import IPv4Network, IPv6Network

from fastapi import Request
from starlette.responses import JSONResponse

from app.core.config import Settings


def _norm_path(path: str) -> str:
    p = path.rstrip("/")
    return p if p else "/"


def is_webhook_post(request: Request, webhook_path: str) -> bool:
    if request.method != "POST":
        return False
    return _norm_path(request.url.path) == _norm_path(webhook_path)


def _xff_client_ip(request: Request, trust_hops: int) -> str | None:
    if trust_hops <= 0:
        return None
    xff = request.headers.get("x-forwarded-for")
    if not xff:
        return None
    parts = [p.strip() for p in xff.split(",") if p.strip()]
    if not parts:
        return None
    return parts[0]


def _client_ip(request: Request, trust_hops: int) -> str:
    xff_ip = _xff_client_ip(request, trust_hops)
    if xff_ip is not None:
        return xff_ip
    if request.client and request.client.host:
        return request.client.host
    return ""


def _parse_allowed_nets(cidr_csv: str | None) -> list[IPv4Network | IPv6Network]:
    if not cidr_csv or not cidr_csv.strip():
        return []
    nets: list[IPv4Network | IPv6Network] = []
    for part in cidr_csv.split(","):
        p = part.strip()
        if p:
            nets.append(ipaddress.ip_network(p, strict=False))
    return nets


def webhook_preflight_response(request: Request, settings: Settings) -> JSONResponse | None:
    """Если запрос к webhook и не проходит проверки — ответ об ошибке, иначе None."""
    if not is_webhook_post(request, settings.webhook_path):
        return None

    req_sec = (
        settings.webhook_request_secret.get_secret_value()
        if settings.webhook_request_secret is not None
        else ""
    )
    if req_sec:
        hdr_name = settings.webhook_request_header
        expected = req_sec
        got = request.headers.get(hdr_name)
        if got is None and hdr_name.lower() != hdr_name:
            got = request.headers.get(hdr_name.lower())
        if got is None:
            return JSONResponse(
                {"detail": "Webhook authentication required"},
                status_code=401,
            )
        if not secrets.compare_digest(got, expected):
            return JSONResponse(
                {"detail": "Invalid webhook credential"},
                status_code=403,
            )

    nets = _parse_allowed_nets(settings.webhook_allowed_cidrs)
    if nets:
        ip_str = _client_ip(request, settings.webhook_forwarded_for_trust_hops)
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return JSONResponse(
                {"detail": "Webhook source not allowed"},
                status_code=403,
            )
        if not any(ip_obj in net for net in nets):
            return JSONResponse(
                {"detail": "Webhook source not allowed"},
                status_code=403,
            )

    return None
