"""Fetch a real-data subset for tamper_localisation fine-tuning -- see
tamper_localisation/README_REAL_DATA.md for what this is and why.

    pip install remotezip
    python3 -m scripts.fetch_sidtd

Only the entries actually used are downloaded (remotezip reads the central directory and does
ranged HTTP reads per file), not the full 1.3GB `templates.zip` / 23GB `clips.zip` archives.

Resumable and incremental: bump N_FAKES/N_CLIPS and re-run to top up an existing data/sidtd/
rather than starting over -- already-downloaded files are skipped, and `timeout=` is passed
explicitly because remotezip uses `requests`, which ignores Python's global socket timeout (a
run died silently for hours on a stale connection before this was added).
"""
import json
import os
from pathlib import Path

from remotezip import RemoteZip

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sidtd"
N_FAKES = 400
N_CLIPS = 400
SEED = 42
TIMEOUT = 20


def fetch_templates():
    (OUT / "reals").mkdir(parents=True, exist_ok=True)
    (OUT / "fakes").mkdir(parents=True, exist_ok=True)
    url = "http://datasets.cvc.uab.es/SIDTD/templates.zip"
    print(f"listing {url} ...")
    with RemoteZip(url, timeout=TIMEOUT) as z:
        fake_jsons = [
            i.filename for i in z.infolist()
            if i.filename.startswith("templates/Annotations/fakes/") and i.filename.endswith(".json")
        ]
        # a fixed seed + a growing N_FAKES means the first N items are a stable prefix, not a
        # re-shuffle -- increasing N_FAKES and re-running only ever adds new items, it never
        # silently swaps out ones already downloaded and counted in an existing manifest.
        import random
        rng = random.Random(SEED)
        rng.shuffle(fake_jsons)
        chosen = fake_jsons[:N_FAKES]

        manifest = []
        srcs_needed = set()
        for jf in chosen:
            data = json.loads(z.read(jf))
            manifest.append({
                "fake": data["name"], "src": data["src"],
                "ctype": data.get("ctype"), "field": data.get("field"),
            })
            srcs_needed.add(data["src"])

        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"manifest: {len(manifest)} fake/real pairs, {len(srcs_needed)} unique real sources")

        missing_reals = [s for s in sorted(srcs_needed) if not (OUT / "reals" / s).exists()]
        print(f"reals: {len(srcs_needed) - len(missing_reals)} already present, {len(missing_reals)} to fetch")
        for i, src in enumerate(missing_reals):
            for attempt in range(4):
                try:
                    (OUT / "reals" / src).write_bytes(z.read(f"templates/Images/reals/{src}"))
                    break
                except Exception as e:
                    print(f"  retry real {src} (attempt {attempt}): {e}")
            if i % 50 == 0:
                print(f"  reals {i}/{len(missing_reals)}")

        missing_fakes = [m for m in manifest if not (OUT / "fakes" / f"{m['fake']}.jpg").exists()]
        print(f"fakes: {len(manifest) - len(missing_fakes)} already present, {len(missing_fakes)} to fetch")
        for i, m in enumerate(missing_fakes):
            fname = f"{m['fake']}.jpg"
            for attempt in range(4):
                try:
                    (OUT / "fakes" / fname).write_bytes(z.read(f"templates/Images/fakes/{fname}"))
                    break
                except Exception as e:
                    print(f"  retry fake {fname} (attempt {attempt}): {e}")
            if i % 50 == 0:
                print(f"  fakes {i}/{len(missing_fakes)}")


def fetch_clips():
    (OUT / "clips_reals").mkdir(parents=True, exist_ok=True)
    url = "http://datasets.cvc.uab.es/SIDTD/clips.zip"
    print(f"listing {url} (this zip has ~150k entries, the directory listing alone takes a "
          f"couple of minutes) ...")
    with RemoteZip(url, timeout=TIMEOUT) as z:
        imgs = [n for n in z.namelist() if n.startswith("clips/Images/reals/") and n.lower().endswith(".jpg")]
        import random
        rng = random.Random(SEED + 1)
        rng.shuffle(imgs)
        chosen = imgs[:N_CLIPS]
        existing = {p.name for p in (OUT / "clips_reals").glob("*.jpg")}
        missing = [n for n in chosen if n.split("/")[-1] not in existing]
        print(f"clips: {len(chosen) - len(missing)} already present, {len(missing)} to fetch")
        for i, n in enumerate(missing):
            fname = n.split("/")[-1]
            for attempt in range(4):
                try:
                    (OUT / "clips_reals" / fname).write_bytes(z.read(n))
                    break
                except Exception as e:
                    print(f"  retry clip {fname} (attempt {attempt}): {e}")
            if i % 50 == 0:
                print(f"  clips {i}/{len(missing)}")


if __name__ == "__main__":
    fetch_templates()
    fetch_clips()
    print("done")
