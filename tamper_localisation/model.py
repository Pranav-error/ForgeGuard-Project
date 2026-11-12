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

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Returns all three stages, not just the bottleneck -- the first two feed the
        decoder's skip connections (see TamperLocaliser)."""
        f1 = self.e1(x)
        f2 = self.e2(f1)
        f3 = self.e3(f2)
        return f1, f2, f3


class TamperLocaliser(nn.Module):
    """Input: RGB image (B,3,H,W) + ELA map (B,1,H,W). Output: logit mask (B,1,H,W).

    Has U-Net-style skip connections from the RGB+ELA encoder to the decoder (added after
    held-out real-world IoU on small, subtle edits came back ~0 with the earlier plain
    encoder-decoder -- see tamper_localisation/README_REAL_DATA.md. The bottleneck is still a
    plain encoder-decoder for the SRM stream: it fuses with the RGB stream once, at the
    bottleneck, as noise-residual *evidence* rather than spatial detail, so it doesn't need its
    own skip path -- the RGB stream already carries the fine spatial detail skip connections
    are for.
    """

    def __init__(self, img_size: int = 256):
        super().__init__()
        self.srm = SRMFilter(in_channels=3)
        self.rgb_encoder = _Encoder(in_ch=3 + 1)  # RGB + ELA channel
        self.srm_encoder = _Encoder(in_ch=self.srm.out_channels)
        self.fuse = nn.Sequential(nn.Conv2d(256, 128, 1), nn.ReLU(inplace=True))
        self.up1 = _up_block(128, 64)        # 32x32 -> 64x64
        self.up2 = _up_block(64 + 64, 32)    # +rgb skip (64ch @ 64x64) -> 128x128
        self.up3 = _up_block(32 + 32, 16)    # +rgb skip (32ch @ 128x128) -> 256x256
        self.out_conv = nn.Conv2d(16, 1, 1)
        self.img_size = img_size

    def forward(self, rgb: torch.Tensor, ela: torch.Tensor) -> torch.Tensor:
        r1, r2, r3 = self.rgb_encoder(torch.cat([rgb, ela], dim=1))
        _, _, s3 = self.srm_encoder(self.srm(rgb))
        fused = self.fuse(torch.cat([r3, s3], dim=1))
        d1 = self.up1(fused)
        d2 = self.up2(torch.cat([d1, r2], dim=1))
        d3 = self.up3(torch.cat([d2, r1], dim=1))
        logits = self.out_conv(d3)
        return nn.functional.interpolate(logits, size=rgb.shape[-2:], mode="bilinear", align_corners=False)
