from .accounts import AccountRouteDeps, register_account_routes
from .dashboard import DashboardRouteDeps, register_dashboard_routes
from .gallery import GalleryRouteDeps, register_gallery_routes
from .logs import LogRouteDeps, register_log_routes
from .public import PublicRouteDeps, register_public_routes
from .settings import SettingsRouteDeps, register_settings_routes
from .system import SystemRouteDeps, register_system_routes

__all__ = [
    "AccountRouteDeps",
    "DashboardRouteDeps",
    "GalleryRouteDeps",
    "LogRouteDeps",
    "PublicRouteDeps",
    "SettingsRouteDeps",
    "SystemRouteDeps",
    "register_account_routes",
    "register_dashboard_routes",
    "register_gallery_routes",
    "register_log_routes",
    "register_public_routes",
    "register_settings_routes",
    "register_system_routes",
]
