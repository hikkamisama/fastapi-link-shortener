from .auth import router as auth_router
from .get import router as get_router
from .shorten import router as shorten_router
from .search import router as search_router
from .history import router as history_router
from .stats import router as stats_router
from .update import router as update_router
from .delete import router as delete_router


links_routers = [
    ("shorten", shorten_router),
    ("search", search_router),
    ("history", history_router),
    ("stats", stats_router),
    ("update", update_router),
    ("delete", delete_router),
]
