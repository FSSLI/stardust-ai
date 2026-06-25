手帐 API
1. 创建记录
POST /api/v1/journal
请求头
plain
Content-Type: application/json
X-Session-Id: <session_id>
请求体
JSON
{
  "content": "今天天气很好，去公园散步了",
  "entry_type": "note",
  "tags": ["日常", "户外"],
  "mood_score": 8
}
表格
字段    类型    必填    说明
content    string    是    记录内容
entry_type    string    否    类型：note/todo/mood/memory，默认note
tags    array    否    标签数组
mood_score    int    否    心情评分 1-10
响应
JSON
{
  "code": 200,
  "data": {
    "id": 1,
    "content": "今天天气很好，去公园散步了",
    "entry_type": "note",
    "tags": "日常,户外",
    "mood_score": 8,
    "created_at": "2026-06-24T20:00:00Z"
  }
}
2. 获取记录列表
GET /api/v1/journal
查询参数
表格
参数    类型    说明
entry_type    string    筛选类型
date_from    string    开始日期 YYYY-MM-DD
date_to    string    结束日期 YYYY-MM-DD
tag    string    标签筛选
page    int    页码
page_size    int    每页数量
响应
JSON
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "content": "今天天气很好...",
        "entry_type": "note",
        "tags": "日常,户外",
        "mood_score": 8,
        "created_at": "2026-06-24T20:00:00Z"
      }
    ],
    "total": 15,
    "page": 1,
    "page_size": 20
  }
}
3. 获取单条记录
GET /api/v1/journal/{entry_id}
响应
JSON
{
  "code": 200,
  "data": {
    "id": 1,
    "content": "今天天气很好，去公园散步了",
    "entry_type": "note",
    "tags": "日常,户外",
    "mood_score": 8,
    "created_at": "2026-06-24T20:00:00Z"
  }
}
4. 更新记录
PUT /api/v1/journal/{entry_id}
请求体
JSON
{
  "content": "今天天气很好，去公园散步了，还看到了一只橘猫",
  "tags": ["日常", "户外", "猫咪"],
  "mood_score": 9
}
响应
JSON
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "content": "今天天气很好，去公园散步了，还看到了一只橘猫",
    "tags": "日常,户外,猫咪",
    "mood_score": 9
  }
}
5. 删除记录
DELETE /api/v1/journal/{entry_id}
响应
JSON
{
  "code": 200,
  "message": "删除成功"
}
6. 获取统计信息
GET /api/v1/journal/stats
响应
JSON
{
  "code": 200,
  "data": {
    "total_entries": 45,
    "by_type": {
      "note": 30,
      "mood": 10,
      "todo": 5
    },
    "mood_trend": [
      {"date": "2026-06-20", "avg_mood": 7.5},
      {"date": "2026-06-21", "avg_mood": 6.0},
      {"date": "2026-06-22", "avg_mood": 8.0}
    ],
    "top_tags": ["日常", "工作", "心情"]
  }
}