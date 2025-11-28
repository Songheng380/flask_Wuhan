# 全局加载词向量（只需一次）
WORD_VECTORS = None

def load_chinese_vectors(file_path, max_words=None):
    embeddings = {}
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if max_words and i >= max_words:
                break
            parts = line.strip().split()
            if len(parts) < 10:  # 忽略无效行
                continue
            word = parts[0]
            vector = np.array([float(x) for x in parts[1:]], dtype=np.float32)
            embeddings[word] = vector
    return embeddings

if WORD_VECTORS is None:
    WORD_VECTORS = load_chinese_vectors("sgns.wiki.word", max_words=500000)
    print("✅ 中文词向量加载完成，词数:", len(WORD_VECTORS))


def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def vectorize_text(text):
    """将文本转换为平均词向量"""
    vectors = [WORD_VECTORS[w] for w in text if w in WORD_VECTORS]
    if not vectors:
        return None
    return np.mean(vectors, axis=0)