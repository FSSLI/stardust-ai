API 设计规范
基础规范
1. 基础 URL
https://myxingchen.xyz/api/v1
2. 请求格式
Content-Type: application/json
所有请求和响应均为 JSON 格式
3. 响应格式
JSON
{
  "code": 200,
  "message": "success",
  "data": {}
}
4. 状态码
表格
状态码    含义
200    成功
400    请求参数错误
401    未授权
404    资源不存在
500    服务器内部错误
5. 错误响应
JSON
{
  "code": 400,
  "message": "参数错误：缺少必填字段 content",
  "data": null
}
6. 认证方式
当前阶段：匿名 session_id
请求头：X-Session-Id: <session_id>
后续升级为 JWT Token
通用参数
分页参数
表格
参数    类型    说明
page    int    页码，默认 1
page_size    int    每页数量，默认 20
分页响应
JSON
{
  "code": 200,
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}