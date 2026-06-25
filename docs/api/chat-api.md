# 对话 API

## 1. 发送消息（SSE 流式）

**POST** `/api/v1/chat/stream`

### 请求头
Content-Type: application/json
X-Session-Id: <session_id>
plain

### 请求体
```json
{
  "message": "你好，星尘",
  "persona_id": 1,
  "conversation_id": null
}
表格
字段    类型    必填    说明
message    string    是    用户输入的消息
persona_id    int    否    人格ID，默认使用用户当前人格
conversation_id    int    否    对话ID，null则创建新对话
响应（SSE 流）
plain
data: {"type": "content", "content": "你"}
data: {"type": "content", "content": "好"}
data: {"type": "content", "content": "呀"}
data: {"type": "done", "message_id": 123}
流式事件类型
表格
type    说明
content    内容片段
done    完成，返回完整消息ID
error    错误信息
2. 获取对话列表
GET /api/v1/chat/conversations
请求头
plain
X-Session-Id: <session_id>
查询参数
表格
参数    类型    说明
page    int    页码，默认1
page_size    int    每页数量，默认20
响应
JSON
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "关于工作的烦恼",
        "persona_id": 1,
        "persona_name": "星尘",
        "last_message": "谢谢你愿意听我说...",
        "updated_at": "2026-06-24T14:30:00Z",
        "message_count": 15
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
3. 获取对话详情
GET /api/v1/chat/conversations/{conversation_id}
响应
JSON
{
  "code": 200,
  "data": {
    "id": 1,
    "title": "关于工作的烦恼",
    "persona_id": 1,
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "最近工作压力好大...",
        "created_at": "2026-06-24T14:00:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "抱抱你，工作压力大的时候确实很难受...",
        "created_at": "2026-06-24T14:00:05Z"
      }
    ]
  }
}
4. 删除对话
DELETE /api/v1/chat/conversations/{conversation_id}
响应
JSON
{
  "code": 200,
  "message": "删除成功"
}