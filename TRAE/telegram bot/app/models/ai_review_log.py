"""
AI 审核日志模型

记录 AI 审核的详细过程和结果
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AIReviewLog(Base):
    """AI 审核日志模型"""

    __tablename__ = "ai_review_logs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="日志ID")

    # 关联广告
    ad_id: Mapped[int] = mapped_column(
        ForeignKey("ads.id", ondelete="CASCADE"),
        index=True,
        comment="广告ID",
    )

    # AI 服务信息
    ai_provider: Mapped[str] = mapped_column(
        String(50),
        comment="AI 服务提供商（openai, google等）",
    )
    ai_model: Mapped[str] = mapped_column(
        String(100),
        comment="使用的 AI 模型",
    )
    review_type: Mapped[str] = mapped_column(
        Enum(
            "content_moderation",    # 内容审核
            "classification",        # 内容分类
            "generation",           # 内容生成
            "enhancement",          # 内容增强
            name="ai_review_type",
        ),
        comment="审核类型",
    )

    # 审核结果
    result: Mapped[str] = mapped_column(
        Enum(
            "approved",             # 通过
            "rejected",            # 拒绝
            "needs_human_review",  # 需要人工审核
            name="ai_review_result",
        ),
        comment="审核结果",
    )
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        comment="置信度评分（0.00-1.00）",
    )

    # 详细分析
    analysis_details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="详细分析结果",
    )
    detected_issues: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="检测到的问题",
    )
    suggested_tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="建议的标签",
    )
    suggested_category: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="建议的分类ID",
    )

    # 处理信息
    processing_time_ms: Mapped[int] = mapped_column(
        Integer,
        comment="处理时间（毫秒）",
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="使用的 Token 数量",
    )
    cost_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 6),
        comment="成本（美元）",
    )

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="错误信息（如果有）",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="重试次数",
    )

    # 人工复核
    human_reviewer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="人工复核员ID",
    )
    human_review_result: Mapped[Optional[str]] = mapped_column(
        Enum(
            "agree",        # 同意 AI 结果
            "disagree",     # 不同意 AI 结果
            "partial",      # 部分同意
            name="human_review_result",
        ),
        comment="人工复核结果",
    )
    human_review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="人工复核备注",
    )

    # 关联关系
    # ad: Mapped["Ad"] = relationship(back_populates="ai_review_logs")
    # human_reviewer: Mapped[Optional["User"]] = relationship()

    # 表约束和索引
    __table_args__ = (
        Index("ix_ai_review_logs_ad_type", "ad_id", "review_type"),
        Index("ix_ai_review_logs_result_confidence", "result", "confidence_score"),
        Index("ix_ai_review_logs_provider_model", "ai_provider", "ai_model"),
        Index("ix_ai_review_logs_created", "created_at"),
    )

    @property
    def is_successful(self) -> bool:
        """是否审核成功"""
        return self.error_message is None

    @property
    def needs_human_attention(self) -> bool:
        """是否需要人工关注"""
        return (
            self.result == "needs_human_review"
            or self.confidence_score < Decimal("0.7")
            or not self.is_successful
        )

    @property
    def cost_cny(self) -> Optional[Decimal]:
        """成本（人民币）"""
        if self.cost_usd is None:
            return None
        # 假设汇率 1 USD = 7.2 CNY
        return self.cost_usd * Decimal("7.2")

    def __str__(self) -> str:
        return f"AIReviewLog(ad_id={self.ad_id}, result={self.result})"