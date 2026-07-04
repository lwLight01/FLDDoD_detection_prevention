from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
@dataclass
class FTTransformerConfig:
    n_cont_features: int
    cat_cardinalities: List[int] = field(default_factory=list)
    embedding_dim: int = 64
    num_blocks: int = 3
    num_heads: int = 8
    ffn_dim: int = 0  
    attn_dropout: float = 0.1
    ffn_dropout: float = 0.2
    embed_dropout: float = 0.1
    def __post_init__(self) -> None:
        if self.ffn_dim == 0:
            self.ffn_dim = 4 * self.embedding_dim
class FeatureTokenizer(nn.Module):
    def __init__(self, config: FTTransformerConfig) -> None:
        super().__init__()
        d = config.embedding_dim
        self.cont_weights = nn.Parameter(
            torch.empty(config.n_cont_features, d)
        )
        self.cont_biases = nn.Parameter(
            torch.zeros(config.n_cont_features, d)
        )
        nn.init.kaiming_uniform_(self.cont_weights, a=math.sqrt(5))
        self.cat_embeddings = nn.ModuleList(
            [nn.Embedding(cardinality, d) for cardinality in config.cat_cardinalities]
        )
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
    def forward(
        self,
        x_cont: torch.Tensor,
        x_cat: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        B = x_cont.size(0)
        cont_tokens = x_cont.unsqueeze(-1) * self.cont_weights.unsqueeze(0) + self.cont_biases.unsqueeze(0)
        tokens_list = [cont_tokens]
        if x_cat is not None and len(self.cat_embeddings) > 0:
            cat_tokens = [
                emb(x_cat[:, i]).unsqueeze(1)
                for i, emb in enumerate(self.cat_embeddings)
            ]
            tokens_list.extend(cat_tokens)
        feature_tokens = torch.cat(tokens_list, dim=1)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls_tokens, feature_tokens], dim=1)
        return tokens
class TransformerBlock(nn.Module):
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
        self.ffn_gate = nn.Linear(d, config.ffn_dim)
        self.ffn_value = nn.Linear(d, config.ffn_dim)
        self.ffn_proj = nn.Linear(config.ffn_dim, d)
        self.ffn_dropout = nn.Dropout(config.ffn_dropout)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        x = self.norm1(x)
        x, _ = self.attn(x, x, x)
        x = self.attn_dropout(x)
        x = residual + x
        residual = x
        x = self.norm2(x)
        gate = F.gelu(self.ffn_gate(x))
        val = self.ffn_value(x)
        x = gate * val  
        x = self.ffn_dropout(x)
        x = self.ffn_proj(x)
        x = residual + x
        return x
class FTTransformerModel(nn.Module):
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
        tokens = self.tokenizer(x_cont, x_cat)
        tokens = self.embed_dropout(tokens)
        tokens = self.blocks(tokens)
        cls_output = tokens[:, 0, :]  
        cls_output = self.head_norm(cls_output)
        logit = self.head(cls_output)
        return logit
    def get_parameters(self) -> list[torch.Tensor]:
        return [p.detach().cpu().numpy() for p in self.parameters()]
    @property
    def n_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
def build_model(config: Optional[FTTransformerConfig] = None) -> FTTransformerModel:
    if config is None:
        from src.fl_client.dataset import CATEGORICAL_CARDINALITIES, CONTINUOUS_FEATURES
        config = FTTransformerConfig(
            n_cont_features=len(CONTINUOUS_FEATURES),
            cat_cardinalities=list(CATEGORICAL_CARDINALITIES.values()),
        )
    return FTTransformerModel(config)
