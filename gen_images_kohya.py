# gen_images.py — ФАЗА 1 v2: надёжная работа с LoRA
import sys, zlib, torch
from pathlib import Path
from diffusers import StableDiffusionPipeline

STYLE_SUFFIX = ("3d render, single object, centered, full object visible, "
                "floating in air, no shadow, isolated on plain light gray background, "
                "three-quarter view, game asset, high detail")

NEGATIVE = ("shadow, shadows, ground, floor, surface, reflection, "
            "cropped, cut off, out of frame, close-up, "
            "multiple objects, composition, scene, landscape, environment, "
            "pile, group, arrangement, diorama, several, many, "
            "crossed swords, heraldry, emblem, logo, icon, two swords, dual blades, "
            "pair, ornate, background objects, blur, blurry")

MODEL_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"

def parse_queue(queue_file: str):
    jobs = []
    for line in Path(queue_file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        name, prompt = parts[0], parts[1]
        seed = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        loras = []
        if len(parts) > 3 and parts[3]:
            for spec in parts[3].split(","):
                spec = spec.strip()
                if not spec:
                    continue
                if "=" in spec:                    # формат lora=файл:вес
                    spec = spec.split("=", 1)[1]
                fname, _, w = spec.partition(":")  # формат файл:вес (или просто файл)
                weight = float(w) if w.strip() else 0.9
                loras.append((fname.strip(), weight))
        jobs.append((name, prompt, seed, tuple(loras)))
    return jobs

def lora_applied(pipe) -> bool:
    """Однозначная проверка: есть ли LoRA-слои в UNet."""
    return any("lora" in n.lower() for n, _ in pipe.unet.named_modules())

def main(queue_file: str):
    jobs = parse_queue(queue_file)
    out_dir = Path("work/ref"); out_dir.mkdir(parents=True, exist_ok=True)
    todo = [j for j in jobs if not (out_dir / f"{j[0]}.png").exists()]
    if not todo:
        print("Все референсы уже готовы"); return

    pipe = None
    current = None  # набор LoRA текущего пайплайна

    for i, (name, prompt, seed, loras) in enumerate(todo):
        # Пересобираем пайплайн ТОЛЬКО при смене набора LoRA
        if loras != current:
            del pipe
            torch.cuda.empty_cache()
            pipe = StableDiffusionPipeline.from_pretrained(
                MODEL_ID, torch_dtype=torch.float16,
                safety_checker=None, requires_safety_checker=False,
            ).to("cuda")
            pipe.set_progress_bar_config(disable=True)
            for opt in ("enable_attention_slicing", "enable_vae_tiling"):
                fn = getattr(pipe, opt, None)
                if callable(fn): fn()
            current = loras

            if loras:
                for fname, weight in loras:
                    path = Path("loras") / fname
                    if not path.exists():
                        raise FileNotFoundError(f"LoRA не найдена: {path}")
                    pipe.load_lora_weights(str(path), adapter_name="gprop")
                    pipe.set_adapters(["gprop"], adapter_weights=[weight])
                print(f">>> LoRA: {[f for f,_ in loras]} | "
                      f"активные адаптеры: {pipe.get_active_adapters()} | "
                      f"слои в UNet: {lora_applied(pipe)}")
            else:
                print(">>> Без LoRA")

        used_seed = seed if seed is not None else zlib.crc32(name.encode("utf-8"))
        image = pipe(f"{prompt}, {STYLE_SUFFIX}",
                     negative_prompt=NEGATIVE,
                     num_inference_steps=25, guidance_scale=8.0,
                     generator=torch.Generator("cuda").manual_seed(used_seed)).images[0]
        image.save(out_dir / f"{name}.png")
        print(f"[{i+1}/{len(todo)}] {name} OK (seed={used_seed})")
        if (i + 1) % 10 == 0:
            torch.cuda.empty_cache()

if __name__ == "__main__":
    main(sys.argv[1])