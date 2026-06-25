记忆 API
1. 获取用户记忆摘要
GET /api/v1/memory/summary
请求头
plain
X-Session-Id: <session_id>
响应
JSON
{
  "code": 200,
  "data": {
    "user_id": 1,
    "total_conversations": 15,
    "total_messages": 320,
    "first_chat_at": "2026-06-01T10:00:00Z",
    "last_chat_at": "2026-06-24T20:00:00Z",
    "favorite_persona": "星尘",
    "memory_highlights": [
      "用户喜欢猫咪",
      "用户从事互联网工作",
      "用户最近在学习日语"
    ]
  }
}
2. 获取对话上下文
GET /api/v1/memory/context
查询参数
表格
参数    类型    必填    说明
conversation_id    int    是    对话ID
limit    int    否    返回最近N条，默认10
响应
JSON
{
  "code": 200,
  "data": {
    "conversation_id": 1,
    "context": [
      {"role": "user", "content": "你好"},
      {"role": "assistant", "content": "你好呀！今天过得怎么样？"}
    ]
  }
}
3. 搜索历史消息
GET /api/v1/memory/search
查询参数
表格
参数    类型    必填    说明
keyword    string    是    搜索关键词
date_from    string    否    开始日期 YYYY-MM-DD
date_to    string    否    结束日期 YYYY-MM-DD
响应
JSON
{
  "code": 200,
  "data": {
    "items": [
      {
        "message_id": 123,
        "conversation_id": 5,
        "role": "user",
        "content": "我今天领养了一只猫",
        "created_at": "2026-06-20T15:00:00Z"
      }
    ],
    "total": 3
  }
}