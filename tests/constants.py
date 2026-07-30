from datetime import UTC, datetime

TOKEN = "f9LHod"  # noqa: S105

# Фиксированная метка времени вместо `datetime.now(UTC)`: реальное время тестам
# не нужно, а недетерминированность мешает сравнивать сериализованные объекты.
NOW = datetime(2026, 1, 1, tzinfo=UTC)

BOT_ID = 1
