import json
import os
import re
import urllib.request

SOURCE_URL = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/sing/geo/geosite/category-ip-geo-detect.json"
OUTPUT_FILE = "Adguard-Home/IP-Geo-Detect.txt"

# Исключаются указанные домены и любые их поддомены (*.domain)
EXCLUDED_DOMAINS = {
    "2ip.ru",
    "2ip.io",
    "browserleaks.com",
    "browserleaks.io",
    "browserleaks.net",
    "browserleaks.org",
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
    data = json.loads(resp.read().decode("utf-8"))

  rules: list[str] = []
  seen: set[str] = set()

  for rule in data.get("rules", []):
    if not isinstance(rule, dict):
      continue

    # Извлекаем только точные домены и суффиксы (без regex и keyword)
    for key in ("domain", "domain_suffix"):
      items = rule.get(key, [])
      if isinstance(items, str):
        items = [items]

      for raw_item in items:
        if not isinstance(raw_item, str):
          continue

        domain = raw_item.strip().lower().strip(".")
        if not DOMAIN_RE.match(domain):
          continue
        if is_excluded(domain):
          continue
        if domain not in seen:
          seen.add(domain)
          rules.append(f"||{domain}^")

  # Защита от перезаписи пустым файлом при сбое источника
  if len(rules) < 50:
    raise RuntimeError(
        "Проверка не пройдена: получено слишком мало доменов"
        f" ({len(rules)}). Обновление отменено."
    )

  os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
  with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(rules) + "\n")

  print(f"Успешно обновлено: {len(rules)} правил в {OUTPUT_FILE}")


if __name__ == "__main__":
  main()
