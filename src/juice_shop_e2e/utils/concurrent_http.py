"""Fires identical HTTP requests at the same instant (TS `Promise.all`).

Sync Playwright objects are bound to the thread that created them, so they can't be called
from worker threads. The stdlib `urllib` can. Threads overlap for real here: CPython releases
the GIL while a thread blocks on the socket, so all requests are in flight together.
"""

import json
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.error import HTTPError

import allure


@dataclass(frozen=True)
class RawResponse:
    status: int
    body: str


def post_json_concurrently(
    url: str,
    payload: object,
    *,
    headers: dict[str, str],
    times: int,
    timeout: float = 10,
) -> list[RawResponse]:
    """POSTs the same JSON `times` times concurrently; non-2xx answers are returned, not raised."""
    data = json.dumps(payload).encode()
    all_headers = {"Content-Type": "application/json", **headers}
    start = threading.Barrier(times)

    def post_once() -> RawResponse:
        request = urllib.request.Request(url, data=data, headers=all_headers, method="POST")
        start.wait(timeout)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return RawResponse(response.status, response.read().decode())
        except HTTPError as error:
            return RawResponse(error.code, error.read().decode())

    # Allure's step context is per thread: report from the main thread only, after the race.
    with allure.step(f"POST {url} x{times} concurrently"):
        allure.attach(
            json.dumps(payload, indent=2),
            name="Request",
            attachment_type=allure.attachment_type.JSON,
        )
        with ThreadPoolExecutor(max_workers=times) as pool:
            futures = [pool.submit(post_once) for _ in range(times)]
            responses = [future.result() for future in futures]
        for i, response in enumerate(responses, start=1):
            allure.attach(
                f"{response.status} {url}\n{response.body}",
                name=f"Response #{i}",
                attachment_type=allure.attachment_type.TEXT,
            )
        return responses
