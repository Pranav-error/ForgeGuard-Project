"""Reconstruction-based anomaly detector -- Phase 2, Gap 8 / O8.

A small convolutional autoencoder trained on genuine documents only. A
forgery type the tamper localiser was never trained on (Gap 8: "supervised
classifiers only learn the forgery types they were trained on") will
usually still look unlike genuine pages to an autoencoder, which never saw
*any* forged examples and so has no forgery-type assumptions baked in --
it just reconstructs genuine-looking content poorly. High reconstruction
error -> the page doesn't look like what "genuine" looks like.
"""
import torch
import torch.nn as nn


def _down(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 4, stride=2, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


def _up(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.ConvTranspose2d(in_ch, out_ch, 4, stride=2, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class ConvAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(_down(3, 16), _down(16, 32), _down(32, 64), _down(64, 128))
        self.decoder = nn.Sequential(
            _up(128, 64), _up(64, 32), _up(32, 16),
            nn.ConvTranspose2d(16, 3, 4, stride=2, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))
