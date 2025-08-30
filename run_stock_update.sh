#!/bin/bash

# 设置时区为北京时间，确保后续的 date 命令使用北京时间
export TZ="Asia/Shanghai"

# 获取当前北京时间是星期几 (1=Mon, 2=Tue, ..., 7=Sun)
# 注意：这里的 DAY_OF_WEEK 是基于北京时间的
DAY_OF_WEEK=$(date +%u)

# 日志文件路径
LOG_FILE="~/FastAPI/update_log.log"

# 将日志路径展开为绝对路径，确保在cron环境中正确识别
LOG_FILE=$(eval echo "$LOG_FILE")

# 检查是否是周末 (周六或周日)
if [ "$DAY_OF_WEEK" -eq 6 ] || [ "$DAY_OF_WEEK" -eq 7 ]; then
    echo "$(date): Skipping stock update - It's a weekend (Beijing time)." >> "$LOG_FILE"
    # 恢复默认时区 (可选，但良好实践)
    unset TZ
    exit 0
fi

echo "$(date): Starting daily stock update (Beijing time check)..." >> "$LOG_FILE"

# 执行 Docker 命令
# 确保 fast-api-container 处于运行状态，并且路径正确
docker exec stock-analysis-api python /app/update_a_stock.py >> "$LOG_FILE" 2>&1

# 检查命令的退出状态
if [ $? -eq 0 ]; then
    echo "$(date): Daily stock update completed successfully." >> "$LOG_FILE"
else
    echo "$(date): Daily stock update FAILED! Check logs for details." >> "$LOG_FILE"
fi

# 恢复默认时区 (可选，但良好实践)
unset TZ
