- хвост стиля конвейера добавляется автоматически (STYLE_SUFFIX в gen_images_kohya.py)

## ✅ Подтверждённые классы (v1, LoRA 0.9)

### Тара и посуда

| Предмет | Промпт                                                               |
| ------- | -------------------------------------------------------------------- |
| Бочка   | `one wooden barrel, vertical cylinder, iron bands, weathered planks` |
| Ящик    | `one wooden crate, square box, plank walls, metal corners`           |
| Кувшин  | `one clay jug, single handle, dark glazed ceramic`                   |

### Природа

| Предмет           | Промпт                                                                   |
| ----------------- | ------------------------------------------------------------------------ |
| Камень            | `one single large boulder, irregular rounded shape, grey granite`        |
| Мох на камне      | `...grey granite, patches of green moss` ✅ (мох — ТОЛЬКО на камнях)     |
| Пень (костровище) | `one wooden tree stump, cut firewood piece, flat top, solid cylinder`    |
| Бревно            | `one fallen rotten log, cracked bark, dark weathered wood`               |
| Грибы             | `one cluster of three dark fantasy mushrooms, thick stems, spotted caps` |

### Смерть и культ

| Предмет    | Промпт                                                                                                    |
| ---------- | --------------------------------------------------------------------------------------------------------- |
| Череп      | `one human skull, museum specimen, front three-quarter view, aged bone color`                             |
| Надгробие  | `one cracked stone tombstone, gothic rounded top, dark weathered stone`                                   |
| Урна       | `one ceramic funerary urn, dark clay, smooth curved body, narrow neck`                                    |
| Идол       | `one small standing stone idol, simplified humanoid figure, dark stone` ⚠️ промпт без "carved" — работает |
| Кадильница | `one bronze dome-shaped incense burner on three small legs`                                               |

### Свет и огонь

| Предмет | Промпт                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Фонарь  | `one old iron oil lantern, frosted amber glass panels, curved handle` ⚠️ или каркасный: `one wrought iron lantern frame, open sides, candle holder inside` |
| Жаровня | `one iron fire brazier bowl on tripod legs, soot-blackened`                                                                                                |
| Свеча   | `one thick candle stub, melted wax drips, small clay holder`                                                                                               |

### Мебель

| Предмет | Промпт                                                               |
| ------- | -------------------------------------------------------------------- |
| Сундук  | `one wooden chest, rectangular, curved lid, iron bands, lock plate`  |
| Стол    | `one heavy wooden table, thick rectangular top, four legs, dark oak` |
| Скамья  | `one rustic wooden bench, four thick legs, rough planks`             |
| Табурет | `one three-legged wooden stool, round seat, worn surface`            |

### Знания

| Предмет         | Промпт                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------ |
| Том (одиночный) | `one old book with dark leather cover, standing upright, brass clasp`                      |
| Свиток          | `one rolled up parchment scroll, horizontal cylinder, beige paper, tied with leather cord` |

### 🎭 Стилевые модификаторы дарк-фэнтези

`weathered, worn, decayed, rusted, soot-blackened, aged patina, dark, gothic`

## ❌ Запрещено (грязная геометрия или ядовитые цвета)

| Слово                                                | Почему                                                           |
| ---------------------------------------------------- | ---------------------------------------------------------------- |
| carved / engraved / ornate / motifs                  | SD рисует грязно, Hunyuan сглаживает → орнамент только текстурой |
| moss на дереве/пнях                                  | ядовито-зелёный; мох — только на камнях                          |
| transparent / clear glass                            | rembg режет маску; стекло = frosted/amber opaque или каркас      |
| стопки/группы (stack of, pile of, group)             | Hunyuan склеивает в монолит (кроме skulls01 из датасета)         |
| сценарные слова (in the forest, on the table, scene) | ломают одиночность кадра                                         |

## 🔑 Якоря одиночности (если объект «на сцене»)

`one single`, `museum specimen`, `cut piece`, `isolated on plain background`

## 🔧 Рабочие параметры

- LoRA: `gprop_v1-000008.safetensors:0.9` (вес >1.0 = абстракция форм)
- Триггер: `gprop,` в начале (обязателен)
- Seed: детерминированный от имени; подбор через 2-3 варианта
- Итерация: `phase1.bat очередь` → `del work\ref\брак` → снова phase1 → forge целиком

## 📊 Стенд качества (актуально после fix-пачки)

✅ тара · камни · костровища · грибы · смерть/культ (чистые формы) · свет · мебель\* · том · свиток
🔧 фонарь (вариант с каркасом) · идол (без украшений = норм, пустовато лечится текстурой)
❌ составные стопки · тонкие спицы/решётки · стекло прозрачное
