"""Fetch a real-data subset for tamper_localisation fine-tuning -- see
tamper_localisation/README_REAL_DATA.md for what this is and why.

    pip install remotezip
    python3 scripts/fetch_sidtd.py

Only the entries actually used are downloaded (remotezip reads the central directory and does
ranged HTTP reads per file), not the full 1.3GB `templates.zip` / 23GB `clips.zip` archives.
"""
import json
import random
from pathlib import Path

from remotezip import RemoteZip

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sidtd"
N_FAKES = 220
N_CLIPS = 260
SEED = 42


def fetch_templates():
    (OUT / "reals").mkdir(parents=True, exist_ok=True)
    (OUT / "fakes").mkdir(parents=True, exist_ok=True)
    url = "http://datasets.cvc.uab.es/SIDTD/templates.zip"
    print(f"listing {url} ...")
    with RemoteZip(url) as z:
        fake_jsons = [
            i.filename for i in z.infolist()
            if i.filename.startswith("templates/Annotations/fakes/") and i.filename.endswith(".json")
        ]
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

        for i, src in enumerate(sorted(srcs_needed)):
            (OUT / "reals" / src).write_bytes(z.read(f"templates/Images/reals/{src}"))
            if i % 50 == 0:
                print(f"  reals {i}/{len(srcs_needed)}")

        for i, m in enumerate(manifest):
            fname = f"{m['fake']}.jpg"
            (OUT / "fakes" / fname).write_bytes(z.read(f"templates/Images/fakes/{fname}"))
            if i % 50 == 0:
                print(f"  fakes {i}/{len(manifest)}")


def fetch_clips():
    (OUT / "clips_reals").mkdir(parents=True, exist_ok=True)
    url = "http://datasets.cvc.uab.es/SIDTD/clips.zip"
    print(f"listing {url} (this zip has ~150k entries, the directory listing alone takes a "
          f"couple of minutes) ...")
    with RemoteZip(url) as z:
        imgs = [n for n in z.namelist() if n.startswith("clips/Images/reals/") and n.lower().endswith(".jpg")]
        rng = random.Random(SEED + 1)
        rng.shuffle(imgs)
        chosen = imgs[:N_CLIPS]
        for i, n in enumerate(chosen):
            (OUT / "clips_reals" / n.split("/")[-1]).write_bytes(z.read(n))
            if i % 50 == 0:
                print(f"  clips {i}/{len(chosen)}")


if __name__ == "__main__":
    fetch_templates()
    fetch_clips()
    print("done")
