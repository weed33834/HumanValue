"""Service 层公共基类

收口各 service 中逐字重复的"会话所有权三件套"
(_get_session / _commit_if_owned / _close_if_owned),
此前该模式在 billing/budget/api_health/analytics_v2/model_fallback/
model_load_balancer/quota/kb_sync/prompt_optimization 九个 service 各持一份。
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal


class OwnedSessionMixin:
    """持有可选 AsyncSession 的 service 基类。

    两种使用模式:
    1. 路由层: Service(session) 配合 get_db 依赖，事务由路由控制;
    2. 中间件/后台: Service() 无 session，内部自建会话并自行 commit/close。

    约定: 子类在自己的 __init__ 中设置 ``_session`` 与 ``_owns_session``
    (标准写法为 ``self._owns_session = session is None``), mixin 不代管构造,
    以免干扰子类各自的额外参数。
    """

    _session: Optional[AsyncSession]
    _owns_session: bool

    async def _get_session(self) -> AsyncSession:
        """获取或创建数据库会话"""
        if self._session is not None:
            return self._session
        # 中间件/后台调用时自建会话
        self._session = AsyncSessionLocal()
        self._owns_session = True
        return self._session

    async def _commit_if_owned(self) -> None:
        """如果 session 由本服务创建，则自动 commit"""
        if self._owns_session and self._session is not None:
            await self._session.commit()

    async def _close_if_owned(self) -> None:
        """如果 session 由本服务创建，则自动关闭"""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None
