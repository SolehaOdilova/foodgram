import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузить ингредиенты из CSV-файла"

    def handle(self, *args, **kwargs):
        filepath = Path("/app/data/ingredients.csv")

        filepath = filepath.resolve()
        self.stdout.write(f"Загружаем ингредиенты из: {filepath}")

        count = 0
        errors = 0

        try:
            with open(filepath, encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    line = row[0].strip()
                    if "," not in line:
                        name = line
                        unit = ""
                    else:
                        name, unit = map(str.strip, line.split(",", 1))
                    if not name:
                        self.stderr.write(
                            f"❗ Пустое имя ингредиента: {repr(line)}"
                        )
                        errors += 1
                        continue
                    obj, created = Ingredient.objects.get_or_create(
                        name=name, measurement_unit=unit
                    )
                    if created:
                        count += 1

        except FileNotFoundError:
            self.stderr.write(f"❌ Файл не найден: {filepath}")
            return
        self.stdout.write(self.style.SUCCESS(
            f"✅ Загружено ингредиентов: {count}")
        )
        if errors:
            self.stderr.write(
                self.style.WARNING(f"⚠️ Пропущено строк: {errors}")
            )
