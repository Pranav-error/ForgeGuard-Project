"""Fixed (non-trainable) SRM noise-residual filters -- FR-D1.

Three high-pass kernels from the classic Spatial Rich Model / steganalysis
literature (as used by SRM-Net, paper [49], and similar forensic CNNs).
They are not learned: the point is to expose noise-residual artefacts that
survive re-saving and are invisible to a semantic (RGB) stream.
"""
import torch
import torch.nn as nn

_KERNELS = [
    [[0, 0, 0], [0, -1, 1], [0, 0, 0]],   # horizontal first-order residual
    [[0, 0, 0], [0, -1, 0], [0, 1, 0]],   # vertical first-order residual
    [[0, 1, 0], [1, -4, 1], [0, 1, 0]],   # second-order (Laplacian-style) residual
]


class SRMFilter(nn.Module):
    """Applies the 3 fixed kernels to every input channel independently.

    Input (B, C, H, W) -> output (B, C*3, H, W).
    """

    def __init__(self, in_channels: int = 3):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = in_channels * len(_KERNELS)
        kernel = torch.tensor(_KERNELS, dtype=torch.float32).unsqueeze(1)  # (3,1,3,3)
        # one copy of the 3 kernels per input channel, applied via grouped conv
        weight = kernel.repeat(in_channels, 1, 1, 1)  # (C*3, 1, 3, 3)
        self.register_buffer("weight", weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return nn.functional.conv2d(x, self.weight, padding=1, groups=self.in_channels)
