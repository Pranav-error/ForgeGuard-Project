"""Writer-independent signature embedding model (metric learning, FR-S3, NFR-6).

Small CNN, L2-normalised output, trained with triplet loss so that distance in
embedding space reflects "same signer vs different signer" rather than any one
signer's class -- a new signer needs no retraining, only new reference
embeddings (NFR-6).
"""
import torch
import torch.nn as nn

EMBED_DIM = 64


def _block(in_ch: int, out_ch: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(2),
    )


class SignatureEncoder(nn.Module):
    def __init__(self, embed_dim: int = EMBED_DIM):
        super().__init__()
        self.features = nn.Sequential(
            _block(1, 16),
            _block(16, 32),
            _block(32, 64),
            _block(64, 128),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(128, embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.pool(self.features(x)).flatten(1)
        embed = self.fc(feat)
        return nn.functional.normalize(embed, dim=1)
