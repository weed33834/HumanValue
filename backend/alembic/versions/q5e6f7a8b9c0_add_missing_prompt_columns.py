"""add missing prompt_templates columns (category/content/variables/is_builtin/is_public)

Revision ID: q5e6f7a8b9c0
Revises: p4d4govern0
Create Date: 2026-08-10 00:00:00.000000

背景：prompt_templates 表可能先由 d5e6f7a8b9c0_add_prompt_management 迁移以旧结构创建
（仅 id/tenant_id/name/type/description/created_by/created_at/updated_at），而
k2l3m4n5o6p7_add_prompt_templates 迁移通过 _has_table 幂等检查会跳过已存在的表，
导致 ORM 模型 PromptTemplate 新增的 category/content/variables/is_builtin/is_public
列从未被补上，DbPromptLoader 查询时报 "no such column: prompt_templates.category"。

本迁移为已存在的表补齐缺失列（幂等：仅当列不存在时添加），并与 ORM 模型列定义对齐。

实现说明:
- 用 batch_alter_table 以兼容 SQLite（无原生 ADD COLUMN 于约束场景时的兼容处理）。
- 幂等：用 inspector 检查列是否已存在，避免重复加列报错。
"""

import sqlalchemy as sa
from alembic import op
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "q5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "p4d4govern0"
branch_labels = None
depends_on = None

_PROMPT_TEMPLATES = "prompt_templates"

# (列名, sa.Column 定义)
_ADD_COLUMNS = [
    (
        "category",
        sa.Column(
            "category", sa.String(length=64), nullable=False, server_default="general"
        ),
    ),
    ("content", sa.Column("content", sa.Text(), nullable=True)),
    ("variables", sa.Column("variables", sa.JSON(), nullable=True)),
    (
        "is_builtin",
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default="0"),
    ),
    (
        "is_public",
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="1"),
    ),
]


def _has_column(inspector, table: str, column: str) -> bool:
    try:
        return any(c["name"] == column for c in inspector.get_columns(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, _PROMPT_TEMPLATES):
        # 表不存在则无需补列（create_all 会建全量结构）
        return

    # 收集缺失列
    missing = [
        col_def
        for name, col_def in _ADD_COLUMNS
        if not _has_column(inspector, _PROMPT_TEMPLATES, name)
    ]
    if not missing:
        return

    with op.batch_alter_table(_PROMPT_TEMPLATES) as batch_op:
        for col in missing:
            batch_op.add_column(col)

    # 为新增的 category 补索引（与 k2l3m4n5o6p7 全新建表路径一致）
    if not _has_index(inspector, _PROMPT_TEMPLATES, "ix_prompt_templates_category"):
        op.create_index(
            op.f("ix_prompt_templates_category"),
            _PROMPT_TEMPLATES,
            ["category"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # 先删掉依赖 category 的索引，避免 batch_alter_table 重建表时冲突
    try:
        if _has_index(inspector, _PROMPT_TEMPLATES, "ix_prompt_templates_category"):
            op.drop_index(
                op.f("ix_prompt_templates_category"),
                table_name=_PROMPT_TEMPLATES,
            )
    except Exception:
        pass
    inspector = sa.inspect(bind)
    with op.batch_alter_table(_PROMPT_TEMPLATES) as batch_op:
        for name, _col in _ADD_COLUMNS:
            if _has_column(inspector, _PROMPT_TEMPLATES, name):
                batch_op.drop_column(name)


def _has_table(inspector, name: str) -> bool:
    try:
        return name in inspector.get_table_names()
    except Exception:
        return False


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    try:
        return index_name in [i["name"] for i in inspector.get_indexes(table_name)]
    except Exception:
        return False
