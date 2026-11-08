"""Self-check: python3 -m anomaly_detection.test_module"""
import torch
from PIL import Image

from .dataset import GenuineDocumentDataset
from .model import ConvAutoencoder
from .service import AnomalyDetectionService


def test_autoencoder_reconstructs_same_shape():
    model = ConvAutoencoder()
    x = torch.rand(2, 3, 128, 128)
    out = model(x)
    assert out.shape == x.shape
    assert (out >= 0).all() and (out <= 1).all()  # sigmoid output


def test_dataset_sample_shape():
    ds = GenuineDocumentDataset(length=2, size=128, seed=1)
    x = ds[0]
    assert x.shape == (3, 128, 128)
    assert 0.0 <= x.min() and x.max() <= 1.0


def test_service_predict_contract():
    service = AnomalyDetectionService(threshold=0.01)
    img = Image.new("RGB", (300, 400), (255, 255, 255))
    out = service.predict(img)
    assert set(out) == {"score", "reconstruction_error"}
    assert 0 <= out["score"] <= 100
    assert out["reconstruction_error"] >= 0


def test_zero_threshold_does_not_crash():
    service = AnomalyDetectionService(threshold=0.0)
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    out = service.predict(img)
    assert out["score"] == 0


def main():
    test_autoencoder_reconstructs_same_shape()
    test_dataset_sample_shape()
    test_service_predict_contract()
    test_zero_threshold_does_not_crash()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
