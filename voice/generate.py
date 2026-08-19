#!/usr/bin/env python3
"""
Generate podcast / narration audio in your own cloned voices using VibeVoice.

    python voice/generate.py --script voice/scripts/example_2p.txt --voices Joe Maya

Speaker 1 in the script maps to the first --voices name, Speaker 2 to the second,
and so on (up to 4). Voice samples live in voice/voices/ as .wav files.
"""

import argparse
import os
import re
import sys
import time
import wave
from pathlib import Path

VOICE_DIR = Path(__file__).parent / "voices"
OUTPUT_DIR = Path(__file__).parent / "outputs"
VENDOR_DIR = Path(__file__).parent / "vendor" / "VibeVoice"

MODELS = {
    "1.5b": "vibevoice/VibeVoice-1.5B",
    "7b": "vibevoice/VibeVoice-7B",
}

SAMPLE_RATE = 24000

# Stage directions / production notes that must never be read aloud.
STAGE_DIRECTION = re.compile(r"[\[\(](?:[^\[\]\(\)]{0,120})[\]\)]")
MARKDOWN_HEADER = re.compile(r"^\s{0,3}#{1,6}\s+")
MARKDOWN_EMPHASIS = re.compile(r"(\*{1,3}|_{1,3}|`+)")
SPEAKER_LINE = re.compile(r"^\s*Speaker\s+(\d+)\s*:\s*(.*)$", re.IGNORECASE)
# "JOE:" / "**Maya:**" style labels produced by ScriptWriterAgent.
NAMED_SPEAKER = re.compile(r"^\s*\*{0,2}([A-Z][A-Za-z .'-]{1,30})\*{0,2}\s*:\s*(.*)$")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# Voice resolution
# --------------------------------------------------------------------------

def available_voices():
    """Map every usable alias -> wav path for files in voice/voices/.

    A file named ``en-Joe_man.wav`` is reachable as ``en-Joe_man``, ``en-Joe``
    and ``Joe`` — the same aliasing VibeVoice's own demo uses.
    """
    if not VOICE_DIR.is_dir():
        return {}
    voices = {}
    for wav in sorted(VOICE_DIR.glob("*.wav")):
        stem = wav.stem
        for alias in {stem, stem.split("_")[0], stem.split("_")[0].split("-")[-1]}:
            voices.setdefault(alias.lower(), wav)
    return voices


def resolve_voice(name):
    voices = available_voices()
    hit = voices.get(name.lower())
    if hit:
        return hit
    listing = sorted({p.stem for p in VOICE_DIR.glob("*.wav")}) if VOICE_DIR.is_dir() else []
    die(
        f"no voice sample matching '{name}' in {VOICE_DIR}.\n"
        f"  available: {', '.join(listing) if listing else '(none yet)'}\n"
        f"  add one with: python voice/prepare_voice.py --input yourclip.mp4 --name {name} --gender man"
    )


# --------------------------------------------------------------------------
# Script preparation
# --------------------------------------------------------------------------

def is_structural(line):
    """Section markers and rules — layout for the writer, never spoken."""
    stripped = line.strip()
    return bool(
        MARKDOWN_HEADER.match(stripped) or re.fullmatch(r"[-*_=]{3,}", stripped)
    )


def clean_line(line):
    """Strip markdown and bracketed production notes from a line of script."""
    line = STAGE_DIRECTION.sub(" ", line)
    line = MARKDOWN_EMPHASIS.sub("", line)
    line = line.replace("’", "'").replace("‘", "'")
    line = line.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", line).strip()


def normalise_script(raw, n_speakers, clean=True):
    """Turn any script into VibeVoice's ``Speaker N:`` format.

    Handles three input shapes: already-tagged ``Speaker 1:`` scripts, named
    labels like ``JOE:`` / ``MAYA:``, and plain prose (single narrator).
    """
    turns = []          # list of (speaker_number, text)
    name_to_number = {}
    current = None

    for raw_line in raw.splitlines():
        if clean and is_structural(raw_line):
            continue
        line = clean_line(raw_line) if clean else raw_line.strip()
        if not line:
            continue

        match = SPEAKER_LINE.match(line)
        if match:
            current = match.group(1)
            text = match.group(2).strip()
            turns.append([current, text])
            continue

        # Named labels (JOE: / **Maya:**) only make sense in a dialogue script;
        # in single-narrator prose they'd misfire on lines like "Note: ...".
        match = NAMED_SPEAKER.match(line)
        if match and n_speakers > 1:
            name = match.group(1).strip()
            key = name.lower()
            if key not in name_to_number:
                name_to_number[key] = (str(len(name_to_number) + 1), name)
            current = name_to_number[key][0]
            turns.append([current, match.group(2).strip()])
            continue

        if turns:
            turns[-1][1] = f"{turns[-1][1]} {line}".strip()
        else:
            turns.append(["1", line])
            current = "1"

    turns = [(num, text) for num, text in turns if text]
    if not turns:
        die("script is empty after cleaning — check the input file")

    used = sorted({int(n) for n, _ in turns})
    if used and used[-1] > n_speakers:
        if name_to_number:
            found = ", ".join(
                original for _, original in sorted(name_to_number.values())
            )
            die(
                f"script has {len(name_to_number)} speakers ({found}) but you passed "
                f"{n_speakers} voice(s) to --voices"
            )
        die(
            f"script uses Speaker {used[-1]} but you only passed {n_speakers} "
            f"voice(s) to --voices"
        )

    labels = {num: original for num, original in name_to_number.values()}
    return turns, labels


def chunk_turns(turns, max_chars):
    """Split turns into batches under max_chars, never mid-turn."""
    if max_chars <= 0:
        return [turns]
    chunks, current, size = [], [], 0
    for turn in turns:
        cost = len(turn[1]) + 12
        if current and size + cost > max_chars:
            chunks.append(current)
            current, size = [], 0
        current.append(turn)
        size += cost
    if current:
        chunks.append(current)
    return chunks


def render(turns):
    return "\n".join(f"Speaker {num}: {text}" for num, text in turns)


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

def pick_device(requested):
    import torch

    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def report_vram(device):
    """Print the card and its VRAM, and warn if it looks too small."""
    import torch

    if device != "cuda" or not torch.cuda.is_available():
        return None
    props = torch.cuda.get_device_properties(0)
    total_gb = props.total_memory / 1024**3
    print(f"gpu:     {props.name}  ({total_gb:.1f} GB VRAM)")
    if total_gb < 6:
        print(
            "\nwarning: under 6 GB is below what the 1.5B model normally needs (~7 GB).\n"
            "         Try --low-vram (offloads layers to system RAM, slower) and a\n"
            "         smaller --chunk-chars, e.g. 1500. If it still fails, use the\n"
            "         Colab notebook in voice/notebooks/.\n"
        )
    elif total_gb < 8:
        print(
            "\nnote: ~7 GB is typical for the 1.5B model, so this is tight. If you hit\n"
            "      out-of-memory, add --low-vram and lower --chunk-chars to ~2000.\n"
        )
    return total_gb


def load_model(model_path, device, dtype_name="auto", low_vram=False):
    import torch
    from vibevoice.modular.modeling_vibevoice_inference import (
        VibeVoiceForConditionalGenerationInference,
    )
    from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor

    if dtype_name != "auto":
        dtype = getattr(torch, dtype_name)
    else:
        dtype = {"cuda": torch.bfloat16, "mps": torch.float16}.get(device, torch.float32)

    attn = "sdpa"
    if device == "cuda":
        try:
            import flash_attn  # noqa: F401
            attn = "flash_attention_2"
        except ImportError:
            # flash-attn rarely builds on Windows; sdpa is the supported path there.
            pass

    # "auto" lets accelerate spill layers into system RAM when VRAM runs out.
    device_map = "auto" if low_vram and device == "cuda" else (
        device if device in ("cuda", "cpu") else None
    )

    print(f"loading {model_path}  (device={device}, dtype={dtype}, attn={attn}"
          f"{', low-vram offload' if low_vram and device == 'cuda' else ''})")
    try:
        # Note: this also reaches out for the Qwen/Qwen2.5-1.5B tokenizer, which
        # is a separate download from the VibeVoice weights themselves.
        processor = VibeVoiceProcessor.from_pretrained(model_path)
    except OSError as exc:
        die(
            f"could not load the model/tokenizer.\n\n  {exc}\n\n"
            "Most often this is network: the processor fetches BOTH the VibeVoice\n"
            "weights and the Qwen/Qwen2.5-1.5B tokenizer from huggingface.co, so a\n"
            "proxy or firewall that blocks it will fail here rather than at install.\n"
            "  - check access:  curl -sI https://huggingface.co\n"
            "  - behind a proxy: export HTTPS_PROXY=... before running\n"
            "  - air-gapped: pre-download both repos on a connected machine, copy\n"
            "    the HF cache over, then run with HF_HUB_OFFLINE=1"
        )
    try:
        model = VibeVoiceForConditionalGenerationInference.from_pretrained(
            model_path,
            torch_dtype=dtype,
            device_map=device_map,
            attn_implementation=attn,
        )
    except Exception as exc:
        if attn == "flash_attention_2":
            print(f"flash-attn failed ({exc}); retrying with sdpa")
            model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                model_path,
                torch_dtype=dtype,
                device_map=device_map,
                attn_implementation="sdpa",
            )
        else:
            raise
    if device == "mps":
        model.to("mps")
    model.eval()
    model.set_ddpm_inference_steps(num_steps=10)
    return processor, model


def synthesize(processor, model, script_text, voice_paths, device, cfg_scale):
    import torch

    inputs = processor(
        text=[script_text],
        voice_samples=[[str(p) for p in voice_paths]],
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    for key, value in inputs.items():
        if torch.is_tensor(value):
            inputs[key] = value.to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=None,
        cfg_scale=cfg_scale,
        tokenizer=processor.tokenizer,
        generation_config={"do_sample": False},
        verbose=False,
        is_prefill=True,
    )
    if not outputs.speech_outputs or outputs.speech_outputs[0] is None:
        die("model returned no audio for this chunk")
    return outputs.speech_outputs[0]


def concat_wavs(parts, destination):
    """Join chunk wavs into one file without needing ffmpeg."""
    with wave.open(str(destination), "wb") as out:
        params_set = False
        for part in parts:
            with wave.open(str(part), "rb") as src:
                if not params_set:
                    out.setparams(src.getparams())
                    params_set = True
                out.writeframes(src.readframes(src.getnframes()))


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate narration/podcast audio in your cloned voices.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--script", required=True, help="path to the script text file")
    parser.add_argument(
        "--voices",
        nargs="+",
        required=True,
        help="voice names in speaker order, e.g. --voices Joe Maya (max 4)",
    )
    parser.add_argument("--out", help="output wav path (default: outputs/<script>.wav)")
    parser.add_argument(
        "--model", default="1.5b", help="1.5b, 7b, or a HuggingFace/local model path"
    )
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "mps", "cpu"])
    parser.add_argument(
        "--cfg-scale",
        type=float,
        default=1.3,
        help="expressiveness vs. fidelity to the voice sample (default 1.3)",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=6000,
        help="split long scripts into chunks of ~N characters; 0 disables (default 6000)",
    )
    parser.add_argument("--seed", type=int, help="fix the random seed for reproducible takes")
    parser.add_argument(
        "--low-vram",
        action="store_true",
        help="offload layers to system RAM when the card is short on VRAM (slower)",
    )
    parser.add_argument(
        "--dtype",
        default="auto",
        choices=["auto", "float32", "float16", "bfloat16"],
        help="force a precision; auto picks bfloat16 on CUDA, float16 on Metal",
    )
    parser.add_argument(
        "--raw", action="store_true", help="skip markdown/stage-direction cleaning"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the normalised script and exit without loading the model",
    )
    args = parser.parse_args()

    if len(args.voices) > 4:
        die("VibeVoice supports at most 4 speakers")

    script_path = Path(args.script)
    if not script_path.is_file():
        die(f"script not found: {script_path}")

    turns, labels = normalise_script(
        script_path.read_text(encoding="utf-8"), len(args.voices), clean=not args.raw
    )
    chunks = chunk_turns(turns, args.chunk_chars)
    words = sum(len(text.split()) for _, text in turns)

    print(f"script:  {script_path}")
    print(f"turns:   {len(turns)}  ({words} words, ~{words / 150:.1f} min of speech)")
    print(f"chunks:  {len(chunks)}")
    if labels:
        found = ", ".join(f"{name} -> Speaker {num}" for num, name in sorted(labels.items()))
        print(f"labels:  {found}")

    if args.dry_run:
        print("\n--- normalised script ---")
        print(render(turns))
        return

    voice_paths = [resolve_voice(name) for name in args.voices]
    for index, (name, path) in enumerate(zip(args.voices, voice_paths), start=1):
        print(f"speaker {index}: {name} -> {path.name}")

    if VENDOR_DIR.is_dir() and str(VENDOR_DIR) not in sys.path:
        sys.path.insert(0, str(VENDOR_DIR))
    try:
        import torch  # noqa: F401
    except ImportError:
        die("PyTorch not installed — run: bash voice/setup.sh")

    device = pick_device(args.device)
    if device == "cpu":
        print(
            "\nwarning: running on CPU. VibeVoice is a diffusion model — expect this to\n"
            "         take many times longer than the audio it produces. Use a GPU\n"
            "         (Colab notebook in voice/notebooks/) for anything real.\n"
        )

    if args.seed is not None:
        import torch

        torch.manual_seed(args.seed)
        if device == "cuda":
            torch.cuda.manual_seed_all(args.seed)

    report_vram(device)

    model_path = MODELS.get(args.model.lower(), args.model)
    processor, model = load_model(model_path, device, args.dtype, args.low_vram)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = Path(args.out) if args.out else OUTPUT_DIR / f"{script_path.stem}.wav"
    final_path.parent.mkdir(parents=True, exist_ok=True)

    part_paths = []
    started = time.time()
    for index, chunk in enumerate(chunks, start=1):
        print(f"\n[{index}/{len(chunks)}] generating...")
        chunk_started = time.time()
        try:
            audio = synthesize(
                processor, model, render(chunk), voice_paths, device, args.cfg_scale
            )
        except Exception as exc:
            if "out of memory" not in str(exc).lower():
                raise
            hint = "" if args.low_vram else "  - add --low-vram to offload layers to system RAM\n"
            die(
                f"ran out of GPU memory on chunk {index}.\n\n"
                f"{hint}"
                f"  - lower --chunk-chars (currently {args.chunk_chars}); try 2000, then 1000\n"
                "  - close other GPU applications (browsers and games hold VRAM)\n"
                "  - stay on --model 1.5b; the 7B needs far more\n"
                "  - or use the Colab notebook in voice/notebooks/ for a bigger card"
            )
        part_path = (
            final_path
            if len(chunks) == 1
            else OUTPUT_DIR / f"{script_path.stem}_part{index:03d}.wav"
        )
        processor.save_audio(audio, output_path=str(part_path))
        part_paths.append(part_path)

        samples = audio.shape[-1] if hasattr(audio, "shape") else len(audio)
        duration = samples / SAMPLE_RATE
        elapsed = time.time() - chunk_started
        print(
            f"    {duration / 60:.1f} min of audio in {elapsed:.0f}s "
            f"(RTF {elapsed / duration:.2f}x) -> {part_path.name}"
        )

    if len(part_paths) > 1:
        concat_wavs(part_paths, final_path)
        for part in part_paths:
            os.remove(part)

    total = time.time() - started
    print(f"\ndone in {total / 60:.1f} min -> {final_path}")


if __name__ == "__main__":
    main()
