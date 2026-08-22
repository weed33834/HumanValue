"""
评估状态枚举常量（单一来源）
所有模块应引用此处的常量，避免字符串散落导致不一致。
"""

from datetime import datetime, timezone


def now_utc() -> datetime:
    """当前 UTC 时间（公共工具函数，避免各 model 重复定义）"""
    return datetime.now(timezone.utc)


class EvaluationStatus:
    """评估状态（完整状态机：AI 起草 → 主管审 → HR 审 → 终态）

    保留三类状态维度：
    - 执行期状态: processing / completed / error（图执行与查询用）
    - 审批流转状态: ai_drafted / manager_review / hr_audit
    - 审批终态: approved / rejected

    注意：COMPLETED 表示评估已完成落库（数据可查询），APPROVED 表示审批链最终通过。
    二者语义不同：COMPLETED 是执行终态，APPROVED 是审批终态。
    """

    # ---- 执行期状态 ----
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

    # ---- 审批流转状态 ----
    AI_DRAFTED = "ai_drafted"  # AI 起草完成，待主管审
    MANAGER_REVIEW = "manager_review"  # 主管审批中
    HR_AUDIT = "hr_audit"  # HR 审核中

    # ---- 审批终态 ----
    APPROVED = "approved"  # 审批通过
    REJECTED = "rejected"  # 审批驳回

    # 待审批状态集合（已生成、等待主管/HR 审批）
    PENDING_STATUSES = (AI_DRAFTED, MANAGER_REVIEW, HR_AUDIT)

    ALL = frozenset(
        {
            PROCESSING,
            COMPLETED,
            ERROR,
            AI_DRAFTED,
            MANAGER_REVIEW,
            HR_AUDIT,
            APPROVED,
            REJECTED,
        }
    )

    @classmethod
    def values(cls) -> list[str]:
        """返回所有合法状态值（用于 DB CHECK 约束、Pydantic Literal 等）"""
        return [
            cls.PROCESSING,
            cls.COMPLETED,
            cls.ERROR,
            cls.AI_DRAFTED,
            cls.MANAGER_REVIEW,
            cls.HR_AUDIT,
            cls.APPROVED,
            cls.REJECTED,
        ]
