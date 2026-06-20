# -*- coding: utf-8 -*-
import numpy as np

def chon_top_doan(passages, query: str, top_k: int = 120):
    """
    Chọn top_k passage liên quan nhất bằng TF-IDF cosine (xấp xỉ).
    passages: list {pid,text,url,lang,title}
    """
    if not passages:
        return []
    if top_k <= 0:
        return passages

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        # Fallback nếu không có sklearn
        return passages[:top_k]

    texts = [p.get("text", "") for p in passages]
    # vectorize
    vec = TfidfVectorizer(
        max_features=60000,
        ngram_range=(1, 2),
        lowercase=True
    )
    X = vec.fit_transform(texts)
    qv = vec.transform([query])

    # similarity = dot product (TF-IDF normalized)
    scores = (X @ qv.T).toarray().ravel()

    idx = np.argsort(-scores)
    k = min(top_k, len(passages))
    chosen = []
    for i in idx[:k]:
        p = dict(passages[int(i)])
        p["score"] = float(scores[int(i)])
        chosen.append(p)

    # nếu query tiếng Việt, ưu tiên thêm ít nhất vài đoạn vi/en cân bằng
    # (chỉ khi có đủ dữ liệu)
    return chosen
