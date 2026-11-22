import re
import urllib.request

SOURCE_URL = "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Categories/geoblock.lst"
OUTPUT_FILE = "Podkop/GeoBlock-own.lst"

# Исключаются указанные домены и все их поддомены (*.domain)
EXCLUDED_DOMAINS = {
    "spotify.com",
    # При необходимости раскомментируйте CDN и служебные домены Spotify:
    # "scdn.co",
    # "spotifycdn.com",
    # "spoti.fi",
    # "pscdn.co",
}

DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
)


def is_excluded(domain: str) -> bool:
  return any(
      domain == excluded or domain.endswith("." + excluded)
      for excluded in EXCLUDED_DOMAINS
  )


def main() -> None:
  req = urllib.request.Request(
      SOURCE_URL,
      headers={"User-Agent": "Own-Domain-Rules-Updater/1.0"},
  )
  with urllib.request.urlopen(req, timeout=30) as resp:
    raw_text = resp.read().decode("utf-8")

  output_lines: list[str] = []
  seen: set[str] = set()

  for raw_line in raw_text.splitlines():
    line = raw_line.split("#")[0].split("//")[0].strip().lower()

    # Сохраняем пустую строку между группами доменов, но не допускаем двойных отступов
    if not line:
      if output_lines and output_lines[-1] != "":
        output_lines.append("")
      continue

    for prefix in ("+.", "domain:", "full:"):
      if line.startswith(prefix):
        line = line[len(prefix) :]
    domain = line.strip(".")

    if not DOMAIN_RE.match(domain):
      continue
    if is_excluded(domain):
      continue
    if domain not in seen:
      seen.add(domain)
      output_lines.append(domain)

  # Убираем пустую строку в самом конце файла, если последний блок был исключён
  while output_lines and output_lines[-1] == "":
    output_lines.pop()

  # Защита от перезаписи списка пустым ответом или HTML-ошибкой при сбое источника
  if len(seen) < 100:
    raise RuntimeError(
        "Проверка не пройдена: получено слишком мало доменов"
        f" ({len(seen)}). Обновление отменено."
    )

  with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(output_lines) + "\n")

  print(f"Успешно обновлено: {len(seen)} доменов в {OUTPUT_FILE}")


if __name__ == "__main__":
  main()
