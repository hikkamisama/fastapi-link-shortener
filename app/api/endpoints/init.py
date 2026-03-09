from .auth import router as auth_router
from .delete import router as delete_router
from .get import router as get_router
from .history import router as history_router
from .search import router as search_router
from .shorten import router as shorten_router
from .stats import router as stats_router
from .update import router as update_router

routers = [
    ("auth", auth_router),
    ("shorten", shorten_router),
    ("search", search_router),
    ("history", history_router),
    ("stats", stats_router),
    ("get", get_router),
    ("update", update_router),
    ("delete", delete_router),
]
