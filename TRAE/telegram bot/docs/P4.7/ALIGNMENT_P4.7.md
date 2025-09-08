# P4.7 对齐文档：实时用户体验 - WebSocket 通知集成

## 项目和任务特性规范

### 项目背景
当前平台的商品审核流程是异步的，使用Celery任务队列处理AI审核。然而，商家在提交商品后无法实时获知审核结果，需要主动刷新页面或等待邮件通知。为了提升用户体验，我们需要实现实时通知功能，当商品审核状态更新时，立即推送给商家。

### 技术栈
- FastAPI: Web框架
- WebSocket: 实时通信协议
- Redis: 消息总线（Pub/Sub）
- Celery: 异步任务队列

### 现有架构分析
1. 商品创建/更新时，状态设为"pending_moderation"
2. 触发Celery任务 moderate_product 进行AI审核
3. 审核完成后，通过内部API更新商品状态
4. 如果审核被拒绝，通过Telegram Bot发送通知

### 需求理解
我们需要在现有架构基础上增加实时通知功能：
1. 商家可以通过WebSocket连接到平台
2. 当商品审核状态更新时，实时推送给对应的商家
3. 使用Redis Pub/Sub解耦Celery Worker和API服务器

## 原始需求
> Our objective is to proactively notify the merchant the instant their product's moderation status is updated. When the AI makes a decision, a real-time notification should be pushed directly to the merchant's connected client (e.g., a web dashboard).

## 边界确认
- 仅实现商品审核状态变更的实时通知
- 通知对象为商品对应的商家
- 通过WebSocket推送JSON格式的通知消息
- 使用Redis Pub/Sub实现Celery Worker与API服务器的解耦

## 疑问澄清
1. 是否需要支持多个WebSocket连接同一个用户？是的，需要支持。
2. 通知消息的具体格式是什么？应包含商品ID、新状态、审核备注等信息。
3. 如何处理WebSocket连接断开的情况？连接管理器应能正确处理断开和重连。
4. Redis频道的命名规范是什么？建议使用"notifications"作为频道名。

## 技术约束
1. 必须与现有FastAPI应用集成
2. 必须使用现有的Redis配置
3. 不改变现有的Celery任务逻辑
4. 保证消息传递的可靠性