"""Self-check: run with `python3 -m tamper_localisation.test_module`.

No pytest, no fixtures -- asserts against an untrained model and a few
synthetic samples, just enough to catch a broken shape or a broken metric.
"""
import numpy as np
import torch
from PIL import Image

from .dataset import SyntheticTamperDataset
from .evaluate import pixel_metrics
from .infer import TamperLocalisationService
from .model import TamperLocaliser


def test_model_forward_shape():
    model = TamperLocaliser(img_size=64)
    rgb = torch.rand(2, 3, 64, 64)
    ela = torch.rand(2, 1, 64, 64)
    out = model(rgb, ela)
    assert out.shape == (2, 1, 64, 64), out.shape


def test_dataset_sample_shapes():
    ds = SyntheticTamperDataset(length=3, size=64, seed=1)
    rgb, ela, mask = ds[0]
    assert rgb.shape == (3, 64, 64)
    assert ela.shape == (1, 64, 64)
    assert mask.shape == (1, 64, 64)
    assert set(np.unique(mask.numpy())) <= {0.0, 1.0}


def test_service_predict_contract():
    service = TamperLocalisationService(img_size=64)
    img = Image.new("RGB", (300, 200), (255, 255, 255))
    out = service.predict(img)
    assert out["mask"].shape == (64, 64)
    assert out["heatmap"].shape == (64, 64)
    assert 0 <= out["score"] <= 100
    assert isinstance(out["regions"], list)
    assert len(out["regions"]) <= 5


def test_pixel_metrics_known_values():
    # 2x2 map: 1 true positive, 1 false positive, 1 false negative, 1 true negative
    probs = np.array([[0.9, 0.9], [0.1, 0.1]])
    targets = np.array([[1, 0], [1, 0]])
    m = pixel_metrics(probs, targets, threshold=0.5)
    assert abs(m["precision"] - 0.5) < 1e-9
    assert abs(m["recall"] - 0.5) < 1e-9
    assert abs(m["iou"] - 1 / 3) < 1e-9


def main():
    test_model_forward_shape()
    test_dataset_sample_shapes()
    test_service_predict_contract()
    test_pixel_metrics_known_values()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
