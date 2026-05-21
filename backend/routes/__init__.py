from fastapi import APIRouter
from routes.auth_routes import router as auth_router
from routes.users import router as users_router
from routes.invoices import router as invoices_router
from routes.polls import router as polls_router
from routes.posts import router as posts_router
from routes.documents import router as documents_router
from routes.benefits import router as benefits_router
from routes.wall import router as wall_router
from routes.events import router as events_router
from routes.gallery import router as gallery_router
from routes.notifications import router as notifications_router
from routes.stats import router as stats_router
from routes.upload import router as upload_router
from routes.finances import router as finances_router
from routes.projects import router as projects_router
from routes.activity import router as activity_router
from routes.report import router as report_router
from routes.admin import router as admin_router
from routes.contact import router as contact_router
from routes.governance import router as governance_router
from routes.assembleias import router as assembleias_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(invoices_router)
api_router.include_router(polls_router)
api_router.include_router(posts_router)
api_router.include_router(documents_router)
api_router.include_router(benefits_router)
api_router.include_router(wall_router)
api_router.include_router(events_router)
api_router.include_router(gallery_router)
api_router.include_router(notifications_router)
api_router.include_router(stats_router)
api_router.include_router(upload_router)
api_router.include_router(finances_router)
api_router.include_router(projects_router)
api_router.include_router(activity_router)
api_router.include_router(report_router)
api_router.include_router(admin_router)
api_router.include_router(contact_router)
api_router.include_router(governance_router)
api_router.include_router(assembleias_router)
