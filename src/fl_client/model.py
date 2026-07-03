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

Implementation deferred to Milestone 11.

Ref: docs/FTTransformer.md § 2
     docs/DevelopmentRoadmap.md — Milestone 11
"""

# TODO (Milestone 11): Implement FTTransformerModel(nn.Module)
# TODO (Milestone 11): Implement FeatureTokenizer for continuous + categorical features
# TODO (Milestone 11): Implement MultiHeadSelfAttention and TransformerBlock
