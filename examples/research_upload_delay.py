"""Замеряет задержку обработки вложений после загрузки.

Использует боевой MAX API и отправляет тестовые сообщения. Нужны `TOKEN` и
`CHAT_ID` или `USER_ID`.
"""

import asyncio
import os
import statistics
import struct
import time
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias

from unihttp.http import UploadFile

from maxo import Bot
from maxo.backoff import Backoff, BackoffConfig
from maxo.enums import UploadType
from maxo.errors import (
    MaxBotBadRequestError,
    MaxBotTooManyRequestsError,
    RetvalReturnedServerException,
)
from maxo.omit import is_defined
from maxo.types import (
    AudioAttachmentRequest,
    FileAttachmentRequest,
    PhotoAttachmentRequest,
    VideoAttachmentRequest,
)
from maxo.types.attachments import AttachmentsRequests
from maxo.utils.upload_media import BufferedInputFile, FSInputFile, InputFile

Target: TypeAlias = tuple[Literal["chat_id", "user_id"], int]

KIB = 1024
MIB = 1024 * KIB

FILE_SIZES: tuple[int, ...] = (
    10 * KIB,
    100 * KIB,
    1 * MIB,
    10 * MIB,
    50 * MIB,
    100 * MIB,
)
IMAGE_SIZES: tuple[int, ...] = (
    10 * KIB,
    100 * KIB,
    1 * MIB,
    10 * MIB,
    30 * MIB,
)

POLL_INTERVAL = 0.1
MAX_WAIT = 120.0

SAMPLE_FILES = "examples/files"


@dataclass(slots=True)
class ProbeResult:
    kind: str
    size: int
    upload_seconds: float
    ready_seconds: float
    attempts: int

    @property
    def size_mib(self) -> float:
        return self.size / MIB


def _make_png(target_bytes: int) -> bytes:
    side = max(1, int((target_bytes / 3) ** 0.5))

    raw = bytearray()
    for _ in range(side):
        raw.append(0)
        raw.extend(os.urandom(side * 3))

    compressed = zlib.compress(bytes(raw), level=0)

    def chunk(tag: bytes, data: bytes) -> bytes:
        head = struct.pack(">I", len(data)) + tag + data
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return head + struct.pack(">I", crc)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", side, side, 8, 2, 0, 0, 0)
    return (
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def build_probe_file(kind: str, size: int) -> InputFile:
    if kind == "file":
        return BufferedInputFile.file(os.urandom(size), file_name=f"probe_{size}.txt")
    if kind == "image":
        data = _make_png(size)
        return BufferedInputFile.image(data, file_name=f"probe_{size}.png")
    raise ValueError(f"Синтетический генератор не умеет тип {kind!r}")


def make_attachment(file_type: UploadType, token: str) -> AttachmentsRequests:
    if file_type is UploadType.IMAGE:
        return PhotoAttachmentRequest.factory(token=token)
    if file_type is UploadType.VIDEO:
        return VideoAttachmentRequest.factory(token)
    if file_type is UploadType.AUDIO:
        return AudioAttachmentRequest.factory(token)
    return FileAttachmentRequest.factory(token)


def is_not_ready_error(error: MaxBotBadRequestError) -> bool:
    code = error.code or ""
    message = error.message or ""
    return code == "attachment.not.ready" or "not.processed" in message


async def upload_and_get_token(bot: Bot, file: InputFile) -> str:
    endpoint = await bot.get_upload_url(type=file.type)

    upload_result = None
    try:
        upload_result = await bot.upload_media(
            upload_url=endpoint.url,
            file=UploadFile(file=await file.read(), filename=file.file_name),
        )
    except RetvalReturnedServerException:
        upload_result = None

    if is_defined(endpoint.token):
        return endpoint.token
    if upload_result is not None:
        return upload_result.last_token
    raise RuntimeError("Не удалось получить токен загрузки")


async def wait_until_ready(
    bot: Bot,
    target: Target,
    attachment: AttachmentsRequests,
    text: str,
) -> tuple[float, int]:
    start = time.monotonic()
    attempts = 0

    while True:
        attempts += 1
        try:
            await _send_message(bot, target, attachment, text)
        except MaxBotBadRequestError as error:
            if not is_not_ready_error(error):
                raise
            if time.monotonic() - start > MAX_WAIT:
                raise TimeoutError(f"Файл не обработался за {MAX_WAIT} c") from error
            await asyncio.sleep(POLL_INTERVAL)
        except MaxBotTooManyRequestsError as error:
            elapsed = time.monotonic() - start
            if elapsed > MAX_WAIT:
                raise TimeoutError(f"Файл не обработался за {MAX_WAIT} c") from error
            await asyncio.sleep(min(1.0, MAX_WAIT - elapsed))
        else:
            return time.monotonic() - start, attempts


async def _send_message(
    bot: Bot,
    target: Target,
    attachment: AttachmentsRequests,
    text: str,
) -> None:
    target_kind, target_id = target
    if target_kind == "chat_id":
        await bot.send_message(chat_id=target_id, attachments=[attachment], text=text)
        return
    await bot.send_message(user_id=target_id, attachments=[attachment], text=text)


async def probe_input_file(bot: Bot, target: Target, file: InputFile) -> ProbeResult:
    real_size = await file.size()

    upload_start = time.monotonic()
    token = await upload_and_get_token(bot, file)
    upload_seconds = time.monotonic() - upload_start

    attachment = make_attachment(file.type, token)
    text = f"[research] {file.type.value} {real_size / MIB:.2f} MiB"
    ready_seconds, attempts = await wait_until_ready(bot, target, attachment, text)

    result = ProbeResult(
        kind=file.type.value,
        size=real_size,
        upload_seconds=upload_seconds,
        ready_seconds=ready_seconds,
        attempts=attempts,
    )
    print(
        f"  {result.kind:5} | {result.size_mib:7.2f} MiB | "
        f"upload {upload_seconds:6.2f} c | "
        f"ready {ready_seconds:6.2f} c | "
        f"{attempts:3} попыток",
    )
    return result


async def measure_rtt(bot: Bot, target: Target, tries: int = 3) -> float:
    samples: list[float] = []
    for _ in range(tries):
        start = time.monotonic()
        target_kind, target_id = target
        if target_kind == "chat_id":
            await bot.send_message(chat_id=target_id, text="[rtt probe]")
        else:
            await bot.send_message(user_id=target_id, text="[rtt probe]")
        samples.append(time.monotonic() - start)
    return statistics.mean(samples)


def linear_fit(points: Sequence[tuple[float, float]]) -> tuple[float, float] | None:
    min_points = 2
    n = len(points)
    if n < min_points:
        return None
    sum_x = sum(x for x, _ in points)
    sum_y = sum(y for _, y in points)
    sum_xx = sum(x * x for x, _ in points)
    sum_xy = sum(x * y for x, y in points)
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return None
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def report(results: Sequence[ProbeResult]) -> None:
    print("\n=== Сводка ===")
    kinds = dict.fromkeys(r.kind for r in results)
    for kind in kinds:
        subset = [r for r in results if r.kind == kind]

        print(f"\nТип: {kind}")
        for r in sorted(subset, key=lambda r: r.size):
            print(
                f"  {r.size_mib:7.2f} MiB -> "
                f"ready {r.ready_seconds:6.2f} c ({r.attempts} попыток)",
            )

        fit = linear_fit([(r.size_mib, r.ready_seconds) for r in subset])
        if fit is not None:
            slope, intercept = fit
            print(
                f"  Линейная модель: ready ≈ {intercept:.2f} + "
                f"{slope:.3f} * размер_MiB (секунд)",
            )


NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)


def estimated_processing_delay(file_type: UploadType, size_bytes: int) -> float:
    if file_type in (UploadType.IMAGE, UploadType.VIDEO):
        return 0.0
    size_mib = size_bytes / MIB
    return min(0.5 + 0.008 * size_mib, 30.0)


async def smart_send(
    bot: Bot,
    chat_id: int,
    file_type: UploadType,
    size_bytes: int,
    attachment: AttachmentsRequests,
    text: str = "",
    max_retries: int = 15,
) -> None:
    await asyncio.sleep(estimated_processing_delay(file_type, size_bytes))

    backoff = Backoff(NOT_READY_BACKOFF)
    while True:
        try:
            await bot.send_message(chat_id=chat_id, attachments=[attachment], text=text)
        except MaxBotBadRequestError as error:
            if not is_not_ready_error(error) or backoff.counter >= max_retries:
                raise
            backoff.next()
            await backoff.sleep()
        else:
            return


async def run_synthetic(bot: Bot, target: Target) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for kind, sizes in (("file", FILE_SIZES), ("image", IMAGE_SIZES)):
        print(f"\nСинтетические замеры для типа: {kind}")
        for size in sizes:
            file = build_probe_file(kind, size)
            try:
                results.append(await probe_input_file(bot, target, file))
            except Exception as error:  # noqa: BLE001
                print(f"  {kind:5} | {size / MIB:7.2f} MiB | ОШИБКА: {error}")
            await asyncio.sleep(0.3)
    return results


async def run_real_samples(bot: Bot, target: Target) -> list[ProbeResult]:
    samples = (
        FSInputFile.image(f"{SAMPLE_FILES}/watermelon.jpg"),
        FSInputFile.audio(f"{SAMPLE_FILES}/watermelon.mp3"),
        FSInputFile.video(f"{SAMPLE_FILES}/watermelon.mp4"),
        FSInputFile.file(f"{SAMPLE_FILES}/watermelon.txt"),
    )
    print("\nРеальные сэмплы (кросс-типовая проверка):")
    results: list[ProbeResult] = []
    for file in samples:
        try:
            results.append(await probe_input_file(bot, target, file))
        except Exception as error:  # noqa: BLE001
            print(f"  {file.type.value:5} | ОШИБКА: {error}")
        await asyncio.sleep(0.3)
    return results


async def run() -> None:
    token = os.environ["TOKEN"]
    if chat_id := os.environ.get("CHAT_ID"):
        target: Target = ("chat_id", int(chat_id))
    else:
        target = ("user_id", int(os.environ["USER_ID"]))

    bot = Bot(token=token)
    async with bot.context():
        rtt = await measure_rtt(bot, target)
        print(f"Базовый RTT send_message: {rtt:.3f} c (нижняя граница разрешения)")

        synthetic = await run_synthetic(bot, target)
        real = await run_real_samples(bot, target)

    report(synthetic)
    report(real)


if __name__ == "__main__":
    asyncio.run(run())
