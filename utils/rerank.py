#重排序功能占位文件
RERANK_AVAILABLE = False  #禁用重排序
#文件预留，暂时下载不了模型。后期加
def rerank_results(query: str, results: list, top_k: int = 3):
    """
    对检索结果进行重排序（当前功能已禁用，直接返回原始结果）
    """
    return results[:top_k]