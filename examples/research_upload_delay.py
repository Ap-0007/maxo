"""
Исследование задержки обработки загруженных файлов на бэкенде MAX (issue #10).

Проблема
--------
После загрузки файла (`POST /uploads` -> получение токена) и немедленной
отправки сообщения с этим вложением MAX может ответить ошибкой::

    maxo.errors.api.MaxBotBadRequestError:
        code='attachment.not.ready'
        message='Key: errors.process.attachment.file.not.processed'

То есть сервер ещё не закончил внутреннюю обработку файла. Сейчас в
`maxo` стоит "костыль" - фиксированный `await asyncio.sleep(0.5)`, который
одновременно и слишком долгий для одних файлов, и слишком короткий для
других (см. `maxo.routing.mixins.attachments.AttachmentsFacade._build_media`).

Цель скрипта
------------
Эмпирически измерить, сколько времени сервер MAX тратит на внутреннюю
обработку файла в зависимости от его размера и типа, чтобы обосновать
"умную" стратегию ожидания.

Метод
-----
Для набора размеров и типов файлов:

1. Загружаем файл и фиксируем токен (та же логика, что в
   `AttachmentsFacade.upload_media`, но без сна).
2. Замеряем `t0` сразу после получения токена.
3. В цикле пытаемся отправить сообщение с вложением. Пока приходит
   `attachment.not.ready` - ждём короткий poll-интервал и повторяем.
   Время до первой успешной отправки - это и есть искомая
   "задержка обработки на сервере".

Затем комбинируем две идеи из issue: начальный сон, зависящий от размера
и типа файла, плюс backoff-ретраи на `attachment.not.ready` как страховку.
Референсная реализация этой стратегии - `smart_send` в конце файла.

Запуск
------
В переменных окружения (или в `.env`) должны быть заданы::

    TOKEN=...      # токен бота
    CHAT_ID=...    # чат, куда слать пробные сообщения (или USER_ID)
    USER_ID=...

Затем::

    set -a; source .env; set +a
    uv run python examples/research_upload_delay.py

ВНИМАНИЕ: скрипт реально отправляет сообщения в указанный чат - по одному
на каждый успешно обработанный пробный файл.

================================ РЕЗУЛЬТАТЫ ================================

Прогон выполнен против боевого API MAX (5 июля 2026), размеры - вплоть до
лимитов из документации (4 ГБ файл / 4 ГБ картинка / 250 МБ видео). Базовый
сетевой RTT одного `send_message` - около 0.16 c; это нижняя граница
разрешения замера (сама отправка и есть проба готовности).

Тип `file` (случайные байты / нули), задержка обработки на сервере::

    размер        ready (c)   попыток
    0.01 MiB      0.50        2
    1    MiB      0.71        3
    50   MiB      1.1         4-5
    100  MiB      1.85        5
    250  MiB      3.53        8
    500  MiB      4.55        9
    1024 MiB      10.47       22
    2048 MiB      NetworkError [BUF] malloc failure  (см. п.5)
    4096 MiB      NetworkError [BUF] malloc failure  (см. п.5)

Тип `image` (валидный PNG-шум), поиск потолка::

    0.01 .. 35 MiB   ready ≈ 0.17-0.20 c, всегда 1 попытка (готово сразу)
    40 MiB и выше    MaxBotBadRequestError(error='SIZE_LIMIT_EXCEEDED')

Тип `video` (mp4, testsrc CBR)::

    3.3  MiB    ready ≈ 0.19 c, 1 попытка
    238  MiB    ready ≈ 0.60 c, 1 попытка   (принят сразу, транскод асинхронно)

Тип `audio` (mp3, 30 KiB)::

    ready ≈ 0.50 c, 2 попытки

Выводы
------
1. Тип файла важнее размера.
   - `image` и `video` готовы практически мгновенно (1 попытка): сервер
     принимает токен сразу, обработку/транскод делает асинхронно.
     `attachment.not.ready` для них не воспроизвёлся ни разу, даже на видео
     238 МБ.
   - `audio` и особенно `file` имеют заметную задержку.

2. Для `file` зависимость от размера линейная и на больших файлах весомая::

       ready ≈ 0.8 + 0.010 * размер_MiB  (секунд)

   То есть примерно +1 c на каждые 100 MiB: 100 MiB ~1.9 c, 1 ГБ ~10.5 c.
   Фиксированный `sleep(0.5)` для гигабайтного файла промахивается в ~20 раз.

3. Заявленные в документации лимиты размеров - НЕ универсальны:
   - картинки упираются в ~36-39 МБ (35 МБ - ок, 40 МБ - `SIZE_LIMIT_EXCEEDED`),
     то есть до 4 ГБ картинку загрузить нельзя;
   - видео до 238 МБ грузится и принимается штатно.

4. Время загрузки (сеть) и задержка обработки - разные величины. Аплоад
   растёт линейно с размером и на крупных файлах доминирует (1 ГБ грузился
   ~92 c против ~10 c обработки). Issue #10 - именно про вторую, серверную.

5. Отдельная находка про текущий upload в maxo: файл читается целиком в
   память и отправляется одним multipart-запросом
   (`AttachmentsFacade.upload_media` -> `UploadFile(file=await file.read())`).
   На 2 ГБ и 4 ГБ это стабильно падает с `NetworkError: [BUF] malloc failure
   (_ssl.c)` - OpenSSL не выделяет буфер под такой единый payload. Значит,
   документированный лимит 4 ГБ на файлы текущим кодом недостижим: нужен
   resumable/чанкованный аплоад (отдельная задача от #10).

Рекомендация (реализована в `smart_send`)
   Комбинировать оба подхода из issue:
   - начальный сон = оценка задержки по самому большому файлу и его типу
     (`estimated_processing_delay`): 0 для image/video, ~0.5 + 0.008 * MiB
     для audio/file;
   - затем backoff-ретраи отправки на `attachment.not.ready`
     (`maxo.backoff.Backoff`) - страховка от разброса серверных задержек и
     непокрытых кейсов.
   Такой гибрид не тормозит мелкие вложения и картинки/видео, но корректно
   ждёт крупные файлы.

Ограничения
   Аудио замерено только на маленьком сэмпле; крупное аудио отдельно не
   гонялось. Абсолютные числа зависят от сети и нагрузки на сервер - это
   порядок величины, а не константы.
"""

import asyncio
import os
import statistics
import struct
import time
import zlib
from collections.abc import Sequence
from dataclasses import dataclass

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

KIB = 1024
MIB = 1024 * KIB

# Лестницы размеров синтетических проб (в байтах). Разные по типам:
# у картинок MAX режет размер на ~36-39 МБ, поэтому их лестница ниже.
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

# Как часто опрашивать сервер, пока файл не готов, и сколько ждать максимум.
POLL_INTERVAL = 0.1
MAX_WAIT = 120.0

# Реальные сэмплы для кросс-типовой проверки (image/video/audio/file).
SAMPLE_FILES = "examples/files"


@dataclass(slots=True)
class ProbeResult:
    """Результат одного замера."""

    kind: str
    size: int
    upload_seconds: float
    ready_seconds: float
    attempts: int

    @property
    def size_mib(self) -> float:
        return self.size / MIB


def _make_png(target_bytes: int) -> bytes:
    """
    Собирает валидный PNG заданного (примерно) размера из случайного шума.

    Шум почти не сжимается, поэтому итоговый размер близок к `target_bytes`.
    Нужен pure-Python генератор, т.к. в окружении нет Pillow/ffmpeg.
    """
    side = max(1, int((target_bytes / 3) ** 0.5))

    raw = bytearray()
    for _ in range(side):
        raw.append(0)  # тип фильтра строки (0 = None)
        raw.extend(os.urandom(side * 3))

    compressed = zlib.compress(bytes(raw), level=0)

    def chunk(tag: bytes, data: bytes) -> bytes:
        head = struct.pack(">I", len(data)) + tag + data
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return head + struct.pack(">I", crc)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", side, side, 8, 2, 0, 0, 0)  # 8 бит, RGB
    return (
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def build_probe_file(kind: str, size: int) -> InputFile:
    """Создаёт синтетический `InputFile` нужного типа и размера."""
    if kind == "file":
        return BufferedInputFile.file(os.urandom(size), file_name=f"probe_{size}.txt")
    if kind == "image":
        data = _make_png(size)
        return BufferedInputFile.image(data, file_name=f"probe_{size}.png")
    raise ValueError(f"Синтетический генератор не умеет тип {kind!r}")


def make_attachment(file_type: UploadType, token: str) -> AttachmentsRequests:
    """Строит запрос-вложение по типу файла и токену."""
    if file_type is UploadType.IMAGE:
        return PhotoAttachmentRequest.factory(token=token)
    if file_type is UploadType.VIDEO:
        return VideoAttachmentRequest.factory(token)
    if file_type is UploadType.AUDIO:
        return AudioAttachmentRequest.factory(token)
    return FileAttachmentRequest.factory(token)


def is_not_ready_error(error: MaxBotBadRequestError) -> bool:
    """`True`, если ошибка означает "файл ещё обрабатывается сервером"."""
    code = error.code or ""
    message = error.message or ""
    return code == "attachment.not.ready" or "not.processed" in message


async def upload_and_get_token(bot: Bot, file: InputFile) -> str:
    """
    Загружает файл и возвращает токен, повторяя логику `AttachmentsFacade`,
    но без искусственного сна после загрузки.
    """
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
    chat_id: int,
    attachment: AttachmentsRequests,
    text: str,
) -> tuple[float, int]:
    """
    Долбит `send_message`, пока сервер не перестанет отвечать
    `attachment.not.ready`. Возвращает (задержка_секунд, число_попыток).
    """
    start = time.monotonic()
    attempts = 0

    while True:
        attempts += 1
        try:
            await bot.send_message(chat_id=chat_id, attachments=[attachment], text=text)
        except MaxBotBadRequestError as error:
            if not is_not_ready_error(error):
                raise
            if time.monotonic() - start > MAX_WAIT:
                raise TimeoutError(f"Файл не обработался за {MAX_WAIT} c") from error
            await asyncio.sleep(POLL_INTERVAL)
        except MaxBotTooManyRequestsError:
            # Слишком частый опрос - притормаживаем.
            await asyncio.sleep(1.0)
        else:
            return time.monotonic() - start, attempts


async def probe_input_file(bot: Bot, chat_id: int, file: InputFile) -> ProbeResult:
    """Один полный замер для готового `InputFile`: загрузка -> ожидание."""
    real_size = len(await file.read())

    upload_start = time.monotonic()
    token = await upload_and_get_token(bot, file)
    upload_seconds = time.monotonic() - upload_start

    attachment = make_attachment(file.type, token)
    text = f"[research] {file.type.value} {real_size / MIB:.2f} MiB"
    ready_seconds, attempts = await wait_until_ready(bot, chat_id, attachment, text)

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


async def measure_rtt(bot: Bot, chat_id: int, tries: int = 3) -> float:
    """Базовый сетевой RTT: время пустого текстового `send_message`."""
    samples: list[float] = []
    for _ in range(tries):
        start = time.monotonic()
        await bot.send_message(chat_id=chat_id, text="[rtt probe]")
        samples.append(time.monotonic() - start)
    return statistics.mean(samples)


def linear_fit(points: Sequence[tuple[float, float]]) -> tuple[float, float] | None:
    """Метод наименьших квадратов: возвращает (slope, intercept) или None."""
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
    """Печатает сводку и оценку зависимости задержки от размера по типам."""
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


# --------------------------------------------------------------------------- #
# Референсная реализация "умной" стратегии - предложение для issue #10.
# --------------------------------------------------------------------------- #

# Backoff-конфиг для ретраев на `attachment.not.ready`.
NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)


def estimated_processing_delay(file_type: UploadType, size_bytes: int) -> float:
    """
    Оценка серверной задержки обработки по типу и размеру файла (в секундах).

    Модель по замерам исследования: для file/audio ready ≈ 0.8 + 0.010 * MiB.
    Коэффициент намеренно чуть занижен (0.008) - добивать "хвост" должны
    backoff-ретраи, а не начальный сон. Для image/video ожидание не нужно.
    """
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
    """
    Отправляет вложение по "умной" схеме из issue #10: адаптивный начальный
    сон по размеру/типу самого большого файла плюс backoff-ретраи на
    `attachment.not.ready`.
    """
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


# --------------------------------------------------------------------------- #


async def run_synthetic(bot: Bot, chat_id: int) -> list[ProbeResult]:
    """Синтетический замер зависимости задержки от размера (file и image)."""
    results: list[ProbeResult] = []
    for kind, sizes in (("file", FILE_SIZES), ("image", IMAGE_SIZES)):
        print(f"\nСинтетические замеры для типа: {kind}")
        for size in sizes:
            file = build_probe_file(kind, size)
            try:
                results.append(await probe_input_file(bot, chat_id, file))
            except Exception as error:  # noqa: BLE001
                print(f"  {kind:5} | {size / MIB:7.2f} MiB | ОШИБКА: {error}")
            await asyncio.sleep(0.3)  # немного бережём чат и сервер
    return results


async def run_real_samples(bot: Bot, chat_id: int) -> list[ProbeResult]:
    """Кросс-типовой замер на реальных сэмплах из `examples/files`."""
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
            results.append(await probe_input_file(bot, chat_id, file))
        except Exception as error:  # noqa: BLE001
            print(f"  {file.type.value:5} | ОШИБКА: {error}")
        await asyncio.sleep(0.3)
    return results


async def run() -> None:
    token = os.environ["TOKEN"]
    chat_id = int(os.environ.get("CHAT_ID") or os.environ["USER_ID"])

    bot = Bot(token=token)
    async with bot.context():
        rtt = await measure_rtt(bot, chat_id)
        print(f"Базовый RTT send_message: {rtt:.3f} c (нижняя граница разрешения)")

        synthetic = await run_synthetic(bot, chat_id)
        real = await run_real_samples(bot, chat_id)

    report(synthetic)
    report(real)


if __name__ == "__main__":
    asyncio.run(run())
