# P4.7 共识文档：实时用户体验 - WebSocket 通知集成

## 明确的需求描述和验收标准

### 需求描述
实现一个实时通知系统，当商品审核状态更新时，通过WebSocket立即推送给对应的商家。

### 验收标准
1. 商家可以建立WebSocket连接到 `/api/v1/notifications/ws/{user_id}`
2. 当商品审核状态更新时，对应的商家会收到实时通知
3. 通知消息为JSON格式，包含商品ID、新状态、审核备注等信息
4. 系统能够正确处理连接建立、断开等生命周期事件
5. 使用Redis Pub/Sub解耦Celery Worker和API服务器

## 技术实现方案

### 整体架构
```
[商家客户端] <--WebSocket--> [API服务器] <--Redis Pub/Sub--> [Celery Worker]
```

### 核心组件
1. **ConnectionManager**: 管理所有WebSocket连接
2. **WebSocket端点**: 处理客户端连接
3. **Redis订阅者**: 监听通知消息并转发给客户端
4. **Celery任务发布者**: 发布通知消息到Redis

### 技术约束和集成方案
1. 使用FastAPI的WebSocket支持
2. 复用现有的Redis连接配置
3. 与现有的Celery任务集成
4. 不改变现有的API接口

## 任务边界限制
1. 仅处理商品审核状态变更通知
2. 通知对象仅限商品对应的商家
3. 不处理历史消息或离线消息
4. 不实现消息确认机制

## 确认所有不确定性已解决
1. ✅ 支持多个WebSocket连接同一个用户
2. ✅ 通知消息格式已确定
3. ✅ 连接断开处理机制已明确
4. ✅ Redis频道命名规范已确定