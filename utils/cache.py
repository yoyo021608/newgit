"""
Redis 缓存工具
用于缓存天气查询等耗时操作的结果
"""
import json
import redis
import os
from typing import Optional, Any

# 从环境变量读取 Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  #优先从环境变量读取 REDIS_URL，如果没有则使用默认值，6379：Redis 默认端口

# 全局 Redis 客户端（延迟初始化），内部使用，不要直接访问，不在一启动就创建连接，而是等到第一次使用时才创建
_redis_client = None

#获取 Redis 客户端实例（单例模式）
def get_redis_client():
    global _redis_client     #声明要修改全局变量 _redis_client。如果不写这行，Python 会把 _redis_client 当成局部变量。
    if _redis_client is None:   #如果还没有创建连接，才去创建
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)   #根据 URL 字符串创建 Redis 连接对象
            # 测试连接
            _redis_client.ping()
            print("✅ Redis 连接成功")
        except Exception as e:
            print(f"⚠️ Redis 连接失败，将跳过缓存: {e}")
            _redis_client = None
    return _redis_client

#从缓存获取数据
def cache_get(key: str) -> Optional[Any]:
    client = get_redis_client()
    if client is None:
        return None
    try:
        data = client.get(key)
        if data:
            return json.loads(data)  #把 JSON 字符串转成 Python 对象并返回
        return None
    except Exception as e:
        print(f"⚠️ 缓存读取失败: {e}")
        return None

#存入缓存，expire: 过期时间（秒），默认 10 分钟
def cache_set(key: str, value: Any, expire: int = 600) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.setex(key, expire, json.dumps(value, ensure_ascii=False))   #设置值并指定过期时间，不转义中文
        return True
    except Exception as e:
        print(f"⚠️ 缓存写入失败: {e}")
        return False

#删除缓存
def cache_delete(key: str) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"⚠️ 缓存删除失败: {e}")
        return False

#按模式删除缓存（如 weather:*）
def cache_clear_pattern(pattern: str) -> int:
    client = get_redis_client()
    if client is None:
        return 0
    try:
        keys = client.keys(pattern)  #返回所有匹配模式的键
        if keys:
            return client.delete(*keys)  #解包
        return 0
    except Exception as e:
        print(f"⚠️ 批量删除缓存失败: {e}")
        return 0