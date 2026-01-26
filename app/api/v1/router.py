from fastapi import APIRouter
from app.api.v1.endpoints import auth, profile, memory, project, conversation, credits, admin, subscriptions

api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Include profile routes
api_router.include_router(
    profile.router,
    prefix="/profile",
    tags=["User Profile"]
)

# Include memory routes
api_router.include_router(
    memory.router,
    prefix="/memory",
    tags=["Memory"]
)

# Include project routes
api_router.include_router(
    project.router,
    prefix="/projects",
    tags=["Projects"]
)

# Include conversation routes
api_router.include_router(
    conversation.router,
    prefix="/conversations",
    tags=["Conversations"]
)

# Include credit routes
api_router.include_router(
    credits.router,
    prefix="/credits",
    tags=["Credits"]
)

# Include admin routes
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

# Include subscription routes
api_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

