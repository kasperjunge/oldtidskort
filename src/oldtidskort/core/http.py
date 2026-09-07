"""Fælles HTTP-klient: retry, timeout og en ærlig User-Agent.

Offentlige danske geodata-endpoints er ikke hurtige, og Overpass afviser
anonyme klienter i spidsbelastning, så alt netværk går gennem denne.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

import httpx

USER_AGENT = "oldtidskort/0.1 (+https://github.com/kasperjunge/prototypes; historiske datasaet)"
DEFAULT_TIMEOUT = httpx.Timeout(connect=30.0, read=300.0, write=60.0, pool=30.0)
RETRY_STATUS = {429, 500, 502, 503, 504}


@contextmanager
def client(timeout: httpx.Timeout = DEFAULT_TIMEOUT) -> Iterator[httpx.Client]:
    with httpx.Client(
        timeout=timeout, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as http:
        yield http


def request(
    http: httpx.Client,
    method: str,
    url: str,
    *,
    attempts: int = 4,
    **kwargs: object,
) -> httpx.Response:
    """Kalder `url` med eksponentiel backoff på transportfejl og 5xx/429."""
    delay = 2.0
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = http.request(method, url, **kwargs)  # type: ignore[arg-type]
            if response.status_code in RETRY_STATUS and attempt < attempts:
                raise httpx.HTTPStatusError(
                    f"{response.status_code} fra {url}", request=response.request,
                    response=response,
                )
            response.raise_for_status()
            return response
        except (httpx.TransportError, httpx.HTTPStatusError) as error:
            last_error = error
            if attempt == attempts:
                break
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Gav op efter {attempts} forsøg på {url}") from last_error
