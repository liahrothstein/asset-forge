# make_captions.py — капшены из таблицы «имя|промпт»
# Формат файла captions.txt: имя|описание_предмета  (как очередь)
# Запуск: python make_captions.py captions.txt
import sys
from pathlib import Path

DS = Path("lora_dataset/20_gprop")   # куда класть .txt

def main(queue_file: str):
    made, missed = 0, []
    for line in Path(queue_file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name, subject = [p.strip() for p in line.split("|", 1)]
        # пропускаем необязательный третий столбец (ракурс), если есть
        if "|" in subject:
            subject = subject.split("|")[0].strip()
        img = DS / f"{name}.jpg"
        if not img.exists():
            missed.append(name)
            continue
        caption = f"gprop, a single {subject} on a white background"
        (DS / f"{name}.txt").write_text(caption, encoding="utf-8")
        made += 1
    print(f"Капшенов создано: {made}")
    if missed:
        print(f"Картинок не нашлось для: {', '.join(missed)}")

if __name__ == "__main__":
    main(sys.argv[1])