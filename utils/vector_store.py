#向量数据库的封装
import chromadb
import os  #读取环境变量（API Key）
import requests  #发送 HTTP 请求到通义千问嵌入 API
import json

#自定义通义千问嵌入函数
class DashScopeEmbeddingFunction:
    def __init__(self, api_key: str, model_name: str = "text-embedding-v1"):
        self.api_key = api_key
        self.model_name = model_name

    def name(self):
        return self.model_name

    def __call__(self, input):
        """用于添加文档时的嵌入"""
        if isinstance(input, str):  #如果输入是单个字符串
            input = [input]  #转列表
        return self._embed(input)  #转向量

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
            embedding = result["output"]["embeddings"][0]["embedding"]  #从 JSON 中取出向量
            results.append(embedding)

        return results

#初始化向量库
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("⚠️ 请设置 DASHSCOPE_API_KEY 环境变量")
#创建自定义嵌入类实例
embedding_fn = DashScopeEmbeddingFunction(
    api_key=api_key,
    model_name="text-embedding-v1"
)
#创建 ChromaDB 客户端，数据持久化存储在 ./chroma_db 目录
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_fn
)
#添加文档函数
def add_document_to_vector_store(doc_id: int, content: str, metadata: dict):
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[str(doc_id)]
    )
    print(f"✅ 文档 {doc_id} 已存入向量库")

#更新文档函数（先删后加）
def update_document_in_vector_store(doc_id: int, content: str, metadata: dict):
    try:
        # 查询该 doc_id 对应的所有向量 ID
        existing = collection.get(where={"doc_id": doc_id})
        if existing and existing['ids']:
            collection.delete(ids=existing['ids'])
            print(f"🗑️ 删除了 {len(existing['ids'])} 个旧向量")
    except Exception as e:
        print(f"⚠️ 删除旧向量失败: {e}")

    # 添加新向量
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[str(doc_id)]
    )
    print(f"✅ 文档 {doc_id} 向量库已更新")
#检索函数
def search_similar(query: str, top_k: int = 3):
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    return results