"""
fl_client/model.py
------------------
FT-Transformer model definition for tabular DDoS flow classification.

Architecture (from docs/FTTransformer.md § 2.1):
  - Feature Tokenizer: Embeds each continuous and categorical feature into a
    dense vector of dimension `d` (embedding_dim).
  - [CLS] Token: Prepended to the sequence of feature embeddings. Its final
    hidden state is used as the classification representation.
  - Transformer Encoder Blocks: `num_blocks` blocks, each with multi-head
    self-attention and feed-forward sublayers.
  - Classification Head: Linear(d → 1) → Sigmoid (or BCEWithLogitsLoss
    handles the sigmoid during training for numerical stability).

Hyperparameter defaults (tuned in Milestone 11 notebook):
  embedding_dim  = 64
  num_blocks     = 3
  num_heads      = 8
  ffn_dim        = 256   (4 * embedding_dim)
  attn_dropout   = 0.1
  ffn_dropout    = 0.2

Ref: docs/FTTransformer.md § 2
     docs/DevelopmentRoadmap.md — Milestone 11
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class FTTransformerConfig:
    """Hyperparameter container for FT-Transformer.

    Attributes:
        n_cont_features: Number of continuous input features.
        cat_cardinalities: Ordered list of cardinalities (vocab sizes) for
            each categorical feature.  The model creates one embedding table
            per entry.
        embedding_dim: Token embedding dimension *d*.
        num_blocks: Number of Transformer encoder blocks.
        num_heads: Number of attention heads in each block.
        ffn_dim: Hidden dimension of the feed-forward sub-layer inside each
            Transformer block.  Defaults to ``4 * embedding_dim``.
        attn_dropout: Dropout probability applied to attention weights.
        ffn_dropout: Dropout probability applied inside the FFN sub-layer.
        embed_dropout: Dropout applied to the feature token embeddings after
            the FeatureTokenizer, before the Transformer blocks.
    """

    n_cont_features: int
    cat_cardinalities: List[int] = field(default_factory=list)
    embedding_dim: int = 64
    num_blocks: int = 3
    num_heads: int = 8
    ffn_dim: int = 0  # Computed automatically if 0
    attn_dropout: float = 0.1
    ffn_dropout: float = 0.2
    embed_dropout: float = 0.1

    def __post_init__(self) -> None:
        if self.ffn_dim == 0:
            self.ffn_dim = 4 * self.embedding_dim


# ---------------------------------------------------------------------------
# Feature Tokenizer
# ---------------------------------------------------------------------------


class FeatureTokenizer(nn.Module):
    """Converts raw tabular features into a sequence of dense token embeddings.

    Each **continuous** feature x_i is projected to:
        token_i = W_i * x_i + b_i   (d-dimensional vector)

    Each **categorical** feature c_j is looked up in a trainable embedding
    table of size (cardinality_j, d).

    A learnable ``[CLS]`` token is prepended, yielding a final token sequence
    of length ``n_cont + n_cat + 1``.
    """

    def __init__(self, config: FTTransformerConfig) -> None:
        super().__init__()
        d = config.embedding_dim

        # Continuous feature projections: one (weight, bias) per feature
        self.cont_weights = nn.Parameter(
            torch.empty(config.n_cont_features, d)
        )
        self.cont_biases = nn.Parameter(
            torch.zeros(config.n_cont_features, d)
        )
        nn.init.kaiming_uniform_(self.cont_weights, a=math.sqrt(5))

        # Categorical embedding tables (one per feature)
        self.cat_embeddings = nn.ModuleList(
            [nn.Embedding(cardinality, d) for cardinality in config.cat_cardinalities]
        )

        # Learnable [CLS] token
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d))
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(
        self,
        x_cont: torch.Tensor,
        x_cat: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Tokenise features into a (B, n_tokens, d) embedding sequence.

        Args:
            x_cont: Continuous features of shape ``(B, n_cont)``.
            x_cat: Categorical feature indices of shape ``(B, n_cat)``.
                Can be ``None`` if there are no categorical features.

        Returns:
            Token tensor of shape ``(B, 1 + n_cont [+ n_cat], d)``.
        """
        B = x_cont.size(0)

        # Continuous tokens: (B, n_cont) → (B, n_cont, d)
        # x_cont[:, i] * W[i] + b[i]
        cont_tokens = x_cont.unsqueeze(-1) * self.cont_weights.unsqueeze(0) + self.cont_biases.unsqueeze(0)

        tokens_list = [cont_tokens]

        # Categorical tokens: (B, n_cat) → list of (B, 1, d)
        if x_cat is not None and len(self.cat_embeddings) > 0:
            cat_tokens = [
                emb(x_cat[:, i]).unsqueeze(1)
                for i, emb in enumerate(self.cat_embeddings)
            ]
            tokens_list.extend(cat_tokens)

        # Concatenate all feature tokens: (B, n_cont [+ n_cat], d)
        feature_tokens = torch.cat(tokens_list, dim=1)

        # Prepend [CLS] token: (B, 1 + n_tokens, d)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls_tokens, feature_tokens], dim=1)
        return tokens


# ---------------------------------------------------------------------------
# Transformer Building Blocks
# ---------------------------------------------------------------------------


class TransformerBlock(nn.Module):
    """Pre-LayerNorm Transformer encoder block.

    Structure (Pre-LN for training stability):
        x = x + MultiHeadSelfAttention(LayerNorm(x))
        x = x + FFN(LayerNorm(x))

    The FFN uses a GEGLU activation for improved performance on tabular data
    (ref: Noam Shazeer, "GLU Variants Improve Transformer", 2020).
    """

    def __init__(self, config: FTTransformerConfig) -> None:
        super().__init__()
        d = config.embedding_dim

        self.norm1 = nn.LayerNorm(d)
        self.attn = nn.MultiheadAttention(
            embed_dim=d,
            num_heads=config.num_heads,
            dropout=config.attn_dropout,
            batch_first=True,
        )
        self.attn_dropout = nn.Dropout(config.attn_dropout)

        self.norm2 = nn.LayerNorm(d)
        # GEGLU: gate half + value half → no explicit activation needed
        self.ffn_gate = nn.Linear(d, config.ffn_dim)
        self.ffn_value = nn.Linear(d, config.ffn_dim)
        self.ffn_proj = nn.Linear(config.ffn_dim, d)
        self.ffn_dropout = nn.Dropout(config.ffn_dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply one Transformer encoder block.

        Args:
            x: Input tensor of shape ``(B, T, d)``.

        Returns:
            Output tensor of shape ``(B, T, d)``.
        """
        # Self-attention (Pre-LN)
        residual = x
        x = self.norm1(x)
        x, _ = self.attn(x, x, x)
        x = self.attn_dropout(x)
        x = residual + x

        # FFN with GEGLU activation (Pre-LN)
        residual = x
        x = self.norm2(x)
        gate = F.gelu(self.ffn_gate(x))
        val = self.ffn_value(x)
        x = gate * val  # GEGLU element-wise product
        x = self.ffn_dropout(x)
        x = self.ffn_proj(x)
        x = residual + x

        return x


# ---------------------------------------------------------------------------
# Full FT-Transformer
# ---------------------------------------------------------------------------


class FTTransformerModel(nn.Module):
    """FT-Transformer for tabular binary classification.

    Accepts continuous features (normalised to ~N(0,1) via QuantileTransformer)
    and optionally categorical features (ordinal-encoded), and returns a raw
    logit suitable for ``BCEWithLogitsLoss``.

    Usage::

        config = FTTransformerConfig(
            n_cont_features=11,
            cat_cardinalities=[5, 65],
        )
        model = FTTransformerModel(config)
        logit = model(x_cont, x_cat)  # shape: (B, 1)
        prob  = torch.sigmoid(logit)
    """

    def __init__(self, config: FTTransformerConfig) -> None:
        super().__init__()
        self.config = config
        d = config.embedding_dim

        self.tokenizer = FeatureTokenizer(config)
        self.embed_dropout = nn.Dropout(config.embed_dropout)

        self.blocks = nn.Sequential(
            *[TransformerBlock(config) for _ in range(config.num_blocks)]
        )

        self.head_norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, 1)

    def forward(
        self,
        x_cont: torch.Tensor,
        x_cat: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass of the FT-Transformer.

        Args:
            x_cont: Continuous features, shape ``(B, n_cont)``.
            x_cat: Categorical features (ordinal indices), shape ``(B, n_cat)``.
                Pass ``None`` if no categorical features are used.

        Returns:
            Raw logit tensor of shape ``(B, 1)``.
        """
        # 1. Tokenise: (B, 1 + n_features, d)
        tokens = self.tokenizer(x_cont, x_cat)
        tokens = self.embed_dropout(tokens)

        # 2. Transformer blocks
        tokens = self.blocks(tokens)

        # 3. Extract [CLS] token (position 0) for classification
        cls_output = tokens[:, 0, :]  # (B, d)
        cls_output = self.head_norm(cls_output)

        # 4. Classification head → raw logit (B, 1)
        logit = self.head(cls_output)
        return logit

    def get_parameters(self) -> list[torch.Tensor]:
        """Return a flat list of parameter tensors (used by Flower client)."""
        return [p.detach().cpu().numpy() for p in self.parameters()]

    @property
    def n_parameters(self) -> int:
        """Total trainable parameter count."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------


def build_model(config: Optional[FTTransformerConfig] = None) -> FTTransformerModel:
    """Convenience factory that builds the default FT-Transformer.

    Args:
        config: A custom ``FTTransformerConfig``.  If ``None``, uses the
            defaults defined in ``FTTransformerConfig`` with CIC-DDoS2019
            feature counts (11 continuous, 2 categorical).

    Returns:
        An untrained ``FTTransformerModel`` instance.
    """
    if config is None:
        from src.fl_client.dataset import CATEGORICAL_CARDINALITIES, CONTINUOUS_FEATURES

        config = FTTransformerConfig(
            n_cont_features=len(CONTINUOUS_FEATURES),
            cat_cardinalities=list(CATEGORICAL_CARDINALITIES.values()),
        )
    return FTTransformerModel(config)
