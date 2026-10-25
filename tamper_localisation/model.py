"""Dual-stream tamper localiser -- FR-D1, FR-D2, NFR-2.

SRM (noise-residual) stream + semantic RGB stream, fused in an
encoder-decoder, following SRM-Net (paper [49]). Channel counts are kept
small (32/64/128) so the model runs on CPU or one consumer GPU (NFR-2).
"""
import torch
import torch.nn as nn

from .srm import SRMFilter


def _conv_block(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
    )


def _up_block(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.ConvTranspose2d(in_ch, out_ch, 4, stride=2, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class _Encoder(nn.Module):
    def __init__(self, in_ch: int):
        super().__init__()
        self.e1 = _conv_block(in_ch, 32)
        self.e2 = _conv_block(32, 64)
        self.e3 = _conv_block(64, 128)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.e3(self.e2(self.e1(x)))


class TamperLocaliser(nn.Module):
    """Input: RGB image (B,3,H,W) + ELA map (B,1,H,W). Output: logit mask (B,1,H,W).

    # ponytail: no skip connections (plain encoder-decoder, not a full U-Net);
    # add them if boundary precision on held-out IoU falls short.
    """

    def __init__(self, img_size: int = 256):
        super().__init__()
        self.srm = SRMFilter(in_channels=3)
        self.rgb_encoder = _Encoder(in_ch=3 + 1)  # RGB + ELA channel
        self.srm_encoder = _Encoder(in_ch=self.srm.out_channels)
        self.fuse = nn.Sequential(nn.Conv2d(256, 128, 1), nn.ReLU(inplace=True))
        self.decoder = nn.Sequential(
            _up_block(128, 64),
            _up_block(64, 32),
            _up_block(32, 16),
            nn.Conv2d(16, 1, 1),
        )
        self.img_size = img_size

    def forward(self, rgb: torch.Tensor, ela: torch.Tensor) -> torch.Tensor:
        rgb_feat = self.rgb_encoder(torch.cat([rgb, ela], dim=1))
        srm_feat = self.srm_encoder(self.srm(rgb))
        fused = self.fuse(torch.cat([rgb_feat, srm_feat], dim=1))
        logits = self.decoder(fused)
        return nn.functional.interpolate(logits, size=rgb.shape[-2:], mode="bilinear", align_corners=False)
