import chromadb
import os
import requests
import json

# ---------- 自定义通义千问嵌入函数 ----------
class DashScopeEmbeddingFunction:
    def __init__(self, api_key: str, model_name: str = "text-embedding-v1"):
        self.api_key = api_key
        self.model_name = model_name

    def name(self):
        return self.model_name

    def __call__(self, input):
        """用于添加文档时的嵌入"""
        if isinstance(input, str):
            input = [input]
        return self._embed(input)

    def embed_query(self, input):
        """用于查询时的嵌入（ChromaDB 要求）"""
        if isinstance(input, str):
            input = [input]
        return self._embed(input)

    def _embed(self, input):
        """通用嵌入方法"""
        url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        results = []
        for text in input:
            data = {
                "model": self.model_name,
                "input": {
                    "texts": [text]
                }
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            embedding = result["output"]["embeddings"][0]["embedding"]
            results.append(embedding)

        return results

# ---------- 初始化向量库 ----------
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("⚠️ 请设置 DASHSCOPE_API_KEY 环境变量")

embedding_fn = DashScopeEmbeddingFunction(
    api_key=api_key,
    model_name="text-embedding-v1"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_fn
)

def add_document_to_vector_store(doc_id: int, content: str, metadata: dict):
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[str(doc_id)]
    )
    print(f"✅ 文档 {doc_id} 已存入向量库")

def search_similar(query: str, top_k: int = 3):
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    return results