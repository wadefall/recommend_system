# Matrix Factorization

# Data
movielens-1m

Shuffle and split into train:val:test = 3:1:1. 

# Model

> $r_{u, i} = embedding(user) * embedding(item) $

# Evaluation

RMSE (Root-Mean-Squared-Error)

embedding_dim = 32

|model|Train|Val|Test|note
|----|-----|---|----|---|
|MF|0.9148|0.9148|0.9194||
|MF|-|-|-|dropout=0.5|
