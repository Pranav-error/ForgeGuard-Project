"""Self-check: python3 -m signature_verification.test_module"""
import numpy as np
import torch
from PIL import Image, ImageDraw

from .cleaner import clean
from .dataset import SignatureTripletDataset, render_style_sample
from .detector import detect
from .encoder import SignatureEncoder
from .evaluate import compute_eer
from .service import SignatureService


def test_detector_finds_drawn_blob():
    page = Image.new("L", (300, 400), 255)
    draw = ImageDraw.Draw(page)
    draw.line([(50, 350), (90, 330), (130, 360), (170, 320)], fill=0, width=3)
    found = detect(page.convert("RGB"))
    assert found is not None
    x, y, w, h = found["bbox"]
    assert w > 0 and h > 0
    assert y >= 400 * 0.5  # within the bottom search band


def test_detector_none_on_blank_page():
    page = Image.new("RGB", (300, 400), (255, 255, 255))
    assert detect(page) is None


def test_cleaner_removes_long_line_keeps_signature():
    img = Image.new("L", (128, 128), 255)
    draw = ImageDraw.Draw(img)
    draw.line([(0, 100), (128, 100)], fill=0, width=1)  # ruled line
    draw.line([(20, 40), (40, 60), (60, 30), (80, 50)], fill=0, width=3)  # signature-like stroke
    out = clean(img)
    arr = np.asarray(out)
    assert arr.shape == (128, 128)
    assert (arr < 255).sum() > 0  # something survived (the stroke)


def test_encoder_output_shape_and_norm():
    model = SignatureEncoder()
    x = torch.rand(4, 1, 128, 128)
    out = model(x)
    assert out.shape == (4, 64)
    norms = out.norm(dim=1)
    assert torch.allclose(norms, torch.ones(4), atol=1e-4)


def test_dataset_triplet_shapes_and_style_consistency():
    ds = SignatureTripletDataset(length=2, seed=1)
    a, p, n = ds[0]
    assert a.shape == p.shape == n.shape == (1, 128, 128)
    # two renders of the same style should be more similar (lower MSE) than different styles
    s1 = np.asarray(render_style_sample(style_seed=10, sample_seed=1), dtype=np.float32)
    s2 = np.asarray(render_style_sample(style_seed=10, sample_seed=2), dtype=np.float32)
    s3 = np.asarray(render_style_sample(style_seed=20, sample_seed=3), dtype=np.float32)
    same_style_diff = np.mean((s1 - s2) ** 2)
    diff_style_diff = np.mean((s1 - s3) ** 2)
    assert same_style_diff < diff_style_diff


def test_eer_known_values():
    genuine = np.array([0.9, 0.85, 0.95, 0.8])
    impostor = np.array([0.1, 0.2, 0.05, 0.15])
    m = compute_eer(genuine, impostor)
    assert m["eer"] < 0.1
    assert m["accuracy"] > 0.9


def test_service_verify_contract():
    service = SignatureService()
    page = Image.new("RGB", (300, 400), (255, 255, 255))
    draw = ImageDraw.Draw(page)
    draw.line([(50, 350), (90, 330), (130, 360), (170, 320)], fill=(0, 0, 0), width=3)

    ref = service.embed(page.crop((40, 310, 190, 370)))
    out = service.verify(page, references=[ref])
    assert out["decision"] in ("genuine", "forged")
    assert -1.0 <= out["similarity"] <= 1.0
    assert len(out["bbox"]) == 4

    out_empty = service.verify(page, references=[])
    assert out_empty["decision"] == "no_references"

    blank = Image.new("RGB", (300, 400), (255, 255, 255))
    out_none = service.verify(blank, references=[ref])
    assert out_none["decision"] == "not_found"


def main():
    test_detector_finds_drawn_blob()
    test_detector_none_on_blank_page()
    test_cleaner_removes_long_line_keeps_signature()
    test_encoder_output_shape_and_norm()
    test_dataset_triplet_shapes_and_style_consistency()
    test_eer_known_values()
    test_service_verify_contract()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
