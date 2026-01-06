# 百度网盘转存API服务

这是一个免费的百度网盘转存API服务，可通过Vercel一键部署。

## API端点
- `GET /api/health` - 健康检查
- `POST /api/transfer` - 提交转存任务
- `GET /api/task/{id}` - 查询任务状态

## 使用方法
1. 部署到Vercel
2. 设置环境变量：
   - APP_KEY: 您的API密钥
   - WEBHOOK_TOKEN: Webhook签名密钥
3. 调用API

## 扣子智能体配置
在扣子插件中配置：
- 请求URL: https://您的域名.vercel.app/api/transfer
- 认证: API Key
- Key名称: X-API-Key
