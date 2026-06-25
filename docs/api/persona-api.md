人格 API
1. 获取所有人格列表
GET /api/v1/personas
响应
JSON
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name": "星尘",
      "avatar": "/assets/avatars/stardust.png",
      "description": "温柔体贴的知心伙伴",
      "is_default": true,
      "traits": {
        "warmth": 0.9,
        "humor": 0.3,
        "formality": 0.2
      }
    },
    {
      "id": 2,
      "name": "北辰",
      "avatar": "/assets/avatars/beichen.png",
      "description": "理性冷静的AI顾问",
      "is_default": false,
      "traits": {
        "warmth": 0.3,
        "humor": 0.2,
        "formality": 0.9
      }
    },
    {
      "id": 3,
      "name": "阿星",
      "avatar": "/assets/avatars/axing.png",
      "description": "嘴贱但靠谱的AI损友",
      "is_default": false,
      "traits": {
        "warmth": 0.6,
        "humor": 0.95,
        "formality": 0.1
      }
    }
  ]
}
2. 切换当前人格
POST /api/v1/personas/switch
请求头
plain
Content-Type: application/json
X-Session-Id: <session_id>
请求体
JSON
{
  "persona_id": 2
}
响应
JSON
{
  "code": 200,
  "message": "已切换到人格：北辰",
  "data": {
    "current_persona_id": 2,
    "persona_name": "北辰"
  }
}
3. 获取当前人格
GET /api/v1/personas/current
请求头
plain
X-Session-Id: <session_id>
响应
JSON
{
  "code": 200,
  "data": {
    "id": 1,
    "name": "星尘",
    "avatar": "/assets/avatars/stardust.png",
    "system_prompt": "你是星尘，一个温柔体贴的AI伙伴..."
  }
}
4. 获取人格详情
GET /api/v1/personas/{persona_id}
响应
JSON
{
  "code": 200,
  "data": {
    "id": 1,
    "name": "星尘",
    "avatar": "/assets/avatars/stardust.png",
    "description": "温柔体贴的知心伙伴",
    "system_prompt": "你是星尘，一个温柔体贴的AI伙伴...",
    "traits": {
      "warmth": 0.9,
      "humor": 0.3,
      "formality": 0.2,
      "empathy": 0.95,
      "initiative": 0.6
    }
  }
}