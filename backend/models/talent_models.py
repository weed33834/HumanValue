"""
人才管理扩展模型 — 补齐目标管理、行动追踪、发展计划、1:1、脉搏调研、
认可奖励、继任规划、PIP、技能矩阵、薪酬洞察、内部流动等 13 个能力域。

设计原则：与 models.py 同一 Base，统一 tenant_id 多租户隔离，
所有写操作由路由层控制事务，服务层只做查询/组装。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.models import DEFAULT_TENANT_ID, now_utc


# ============================================================
# 1. OKR / 目标管理
# ============================================================


class Goal(Base):
    """目标（公司/团队/个人三级，parent_goal_id 实现级联对齐）"""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    goal_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    owner_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, comment="目标归属人 user_id"
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="individual",
        comment="company / team / individual",
    )
    parent_goal_id: Mapped[Optional[str]] = mapped_column(
        String(128), ForeignKey("goals.goal_id"), nullable=True, index=True
    )
    period: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False, comment="如 2026-Q3"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="active / completed / archived",
    )
    progress: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="0-100"
    )
    key_results: Mapped[list] = mapped_column(
        JSON,
        default=list,
        comment="[{kr_id, title, target_value, current_value, unit, weight}]",
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        Index("ix_goal_tenant_owner_period", "tenant_id", "owner_id", "period"),
    )


# ============================================================
# 2. 行动项追踪
# ============================================================


class ActionItem(Base):
    """行动项 — 评估洞察转化为可追踪的待办"""

    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    evaluation_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True, comment="关联的评估 ID（可选）"
    )
    employee_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, comment="行动对象员工"
    )
    assigned_by: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="分配人 user_id"
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="development",
        comment="development / risk / pip / recognition / other",
    )
    priority: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="medium",
        comment="low / medium / high / urgent",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        comment="pending / in_progress / completed / overdue",
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        Index("ix_action_tenant_emp_status", "tenant_id", "employee_id", "status"),
    )


# ============================================================
# 3. 个人发展计划（IDP）
# ============================================================


class DevelopmentPlan(Base):
    """个人发展计划 — 关联评估，含里程碑和进度"""

    __tablename__ = "development_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    evaluation_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    development_goal: Mapped[str] = mapped_column(
        Text, nullable=False, comment="发展目标描述"
    )
    focus_areas: Mapped[list] = mapped_column(
        JSON, default=list, comment="关注的能力领域"
    )
    timeline_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timeline_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    milestones: Mapped[list] = mapped_column(
        JSON,
        default=list,
        comment="[{milestone_id, title, due_date, status, completed_at}]",
    )
    resources: Mapped[list] = mapped_column(
        JSON, default=list, comment="[{type, title, url, notes}]"
    )
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="draft / active / completed / paused",
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        Index("ix_idp_tenant_emp_status", "tenant_id", "employee_id", "status"),
    )


# ============================================================
# 4. 1:1 会议管理
# ============================================================


class OneOnOneMeeting(Base):
    """1:1 会议 — 结构化议程、记录、行动项提取"""

    __tablename__ = "one_on_one_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    manager_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="scheduled",
        comment="scheduled / completed / cancelled",
    )
    agenda: Mapped[list] = mapped_column(
        JSON, default=list, comment="[{topic, priority, notes}]"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[list] = mapped_column(
        JSON, default=list, comment="[{title, assignee, due_date}]"
    )
    ai_suggested_topics: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, comment="AI 基于评估数据生成的建议话题"
    )
    meeting_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="实际完成日期"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        Index("ix_1on1_tenant_mgr_emp", "tenant_id", "manager_id", "employee_id"),
    )


# ============================================================
# 5. 脉搏调研
# ============================================================


class PulseSurvey(Base):
    """脉搏调研题库"""

    __tablename__ = "pulse_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    survey_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    period: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="engagement",
        comment="engagement / wellbeing / workload / growth / culture",
    )
    scale_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="1-5", comment="1-5 / 1-10 / emoji"
    )
    frequency: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="biweekly",
        comment="weekly / biweekly / monthly",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class PulseResponse(Base):
    """脉搏调研回复"""

    __tablename__ = "pulse_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    response_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    survey_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("pulse_surveys.survey_id"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="positive / neutral / negative (AI 分析)"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )

    __table_args__ = (
        UniqueConstraint(
            "survey_id", "user_id", "tenant_id", name="uix_pulse_response"
        ),
        Index("ix_pulse_resp_tenant_user", "tenant_id", "user_id"),
    )


# ============================================================
# 6. 认可与奖励
# ============================================================


class Recognition(Base):
    """同行认可 — 点对点，价值观标签，公开动态流"""

    __tablename__ = "recognitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recognition_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    from_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    to_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    recognition_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="kudos",
        comment="kudos / shoutout / milestone / leadership",
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    values_tags: Mapped[list] = mapped_column(
        JSON, default=list, comment="['#Teamwork', '#Innovation', ...]"
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    points: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="积分（游戏化）"
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )

    __table_args__ = (Index("ix_recog_tenant_to", "tenant_id", "to_user_id"),)


# ============================================================
# 7. 继任规划
# ============================================================


class SuccessionPlan(Base):
    """继任管线 — 关键岗位 → 候选人池 → 准备度评级"""

    __tablename__ = "succession_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    position_title: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="关键岗位名称"
    )
    position_level: Mapped[str] = mapped_column(
        String(64), nullable=True, comment="岗位级别"
    )
    current_holder_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="现任者 user_id"
    )
    candidate_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, comment="候选人 user_id"
    )
    readiness: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1-2-years",
        comment="ready-now / 1-2-years / 3-plus-years",
    )
    development_gaps: Mapped[list] = mapped_column(
        JSON, default=list, comment="[{skill, gap_description, action}]"
    )
    risk_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="继任风险备注"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="active / promoted / departed / archived",
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (Index("ix_succ_tenant_position", "tenant_id", "position_title"),)


# ============================================================
# 8. PIP 绩效改进
# ============================================================


class PerformanceImprovementPlan(Base):
    """绩效改进计划 — 结构化流程，含里程碑和结果归档"""

    __tablename__ = "performance_improvement_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pip_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    manager_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="发起 PIP 的管理者"
    )
    evaluation_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True, comment="触发 PIP 的评估 ID"
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment="PIP 触发原因")
    improvement_goals: Mapped[list] = mapped_column(
        JSON,
        default=list,
        comment="[{goal_id, description, target_metric, current_metric}]",
    )
    milestones: Mapped[list] = mapped_column(
        JSON,
        default=list,
        comment="[{milestone_id, title, due_date, status, review_notes}]",
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_frequency: Mapped[str] = mapped_column(
        String(32), nullable=False, default="weekly", comment="weekly / biweekly"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="active / completed-success / completed-failed / cancelled",
    )
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        Index("ix_pip_tenant_emp_status", "tenant_id", "employee_id", "status"),
    )


# ============================================================
# 9. 技能矩阵
# ============================================================


class Skill(Base):
    """技能定义库"""

    __tablename__ = "skills_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    skill_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="technical",
        comment="technical / leadership / communication / domain / soft",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proficiency_levels: Mapped[list] = mapped_column(
        JSON, default=list, comment="[{level, label, description}]"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )


class EmployeeSkill(Base):
    """员工技能评估记录 — 岗位要求 vs 当前水平"""

    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("skills_catalog.skill_id"), index=True, nullable=False
    )
    current_level: Mapped[int] = mapped_column(Integer, nullable=False, comment="1-5")
    target_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, comment="岗位要求的目标水平 1-5"
    )
    gap: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="target - current, 负数表示超出要求"
    )
    assessment_source: Mapped[str] = mapped_column(
        String(64), nullable=False, default="ai", comment="ai / manual / 360"
    )
    last_assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "skill_id", "tenant_id", name="uix_emp_skill"),
        Index("ix_empskill_tenant_emp", "tenant_id", "employee_id"),
    )


# ============================================================
# 10. 薪酬洞察
# ============================================================


class CompensationRecord(Base):
    """薪酬记录 — 关联评估做竞争力分析"""

    __tablename__ = "compensation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    equity_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_compensation: Mapped[float] = mapped_column(
        Float, nullable=False, comment="base + bonus + equity"
    )
    market_benchmark: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="市场中位数参考"
    )
    market_percentile: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="所在百分位"
    )
    compensation_ratio: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="total / benchmark, <1 低于市场"
    )
    last_review_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recommended_adjustment: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="建议调整百分比"
    )
    adjustment_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    period: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )

    __table_args__ = (
        Index("ix_comp_tenant_emp_period", "tenant_id", "employee_id", "period"),
    )


# ============================================================
# 11. 内部人才流动
# ============================================================


class JobPosting(Base):
    """内部岗位 / 项目机会"""

    __tablename__ = "internal_job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    posting_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    job_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="fulltime",
        comment="fulltime / project / rotation / mentorship",
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list] = mapped_column(
        JSON, default=list, comment="[{skill_id, min_level}]"
    )
    preferred_skills: Mapped[list] = mapped_column(JSON, default=list)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", comment="open / closed / filled"
    )
    posted_by: Mapped[str] = mapped_column(String(64), nullable=False)
    closing_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class InternalApplication(Base):
    """内部申请 / AI 匹配记录"""

    __tablename__ = "internal_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    posting_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("internal_job_postings.posting_id"),
        index=True,
        nullable=False,
    )
    applicant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    match_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="AI 匹配度 0-100"
    )
    match_reasons: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, comment="匹配/不匹配原因"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="applied",
        comment="applied / matched / shortlisted / offered / rejected / withdrawn",
    )
    cover_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default=DEFAULT_TENANT_ID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    __table_args__ = (
        UniqueConstraint(
            "posting_id", "applicant_id", "tenant_id", name="uix_internal_app"
        ),
    )
