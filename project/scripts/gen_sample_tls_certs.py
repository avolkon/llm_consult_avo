#!/usr/bin/env python3
"""Генерация самоподписанного CA и сервера (SAN: redis, rabbitmq) для docker-compose.prod.example.

Требуется openssl в PATH. Запуск из корня репозитория:
  python project/scripts/gen_sample_tls_certs.py

Артефакты: project/tls/ca.crt, ca.key, server.crt, server.key (ключи не для production).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run(args: list[str], *, cwd: Path) -> None:
    try:
        subprocess.run(args, check=True, cwd=cwd, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print("openssl не найден в PATH. Установите OpenSSL (Windows: Git Bash, Chocolatey, и т.д.).", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"openssl завершился с ошибкой: {e}", file=sys.stderr)
        sys.exit(e.returncode)


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent
    tls = project_dir / "tls"
    tls.mkdir(parents=True, exist_ok=True)

    ca_key = tls / "ca.key"
    ca_crt = tls / "ca.crt"
    srv_key = tls / "server.key"
    srv_csr = tls / "server.csr"
    srv_crt = tls / "server.crt"
    ext = tls / "server.ext"

    ext.write_text(
        "subjectAltName=DNS:redis,DNS:rabbitmq\n",
        encoding="utf-8",
    )

    if not ca_crt.exists():
        _run(
            ["openssl", "genrsa", "-out", str(ca_key), "4096"],
            cwd=tls,
        )
        _run(
            [
                "openssl",
                "req",
                "-new",
                "-x509",
                "-days",
                "3650",
                "-key",
                str(ca_key),
                "-out",
                str(ca_crt),
                "-subj",
                "/CN=llm-consult-sample-ca",
            ],
            cwd=tls,
        )

    _run(["openssl", "genrsa", "-out", str(srv_key), "2048"], cwd=tls)
    _run(
        [
            "openssl",
            "req",
            "-new",
            "-key",
            str(srv_key),
            "-out",
            str(srv_csr),
            "-subj",
            "/CN=redis",
        ],
        cwd=tls,
    )
    _run(
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(srv_csr),
            "-CA",
            str(ca_crt),
            "-CAkey",
            str(ca_key),
            "-CAcreateserial",
            "-out",
            str(srv_crt),
            "-days",
            "825",
            "-extfile",
            str(ext),
        ],
        cwd=tls,
    )

    for p in (srv_csr, ext, tls / "ca.srl"):
        if p.exists():
            p.unlink()

    # Права на ключи (на Unix)
    if os.name != "nt":
        os.chmod(srv_key, 0o600)
        os.chmod(ca_key, 0o600)

    print(f"OK: {tls}  (ca.crt, server.crt, server.key)")


if __name__ == "__main__":
    main()
