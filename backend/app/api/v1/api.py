from fastapi import APIRouter
from app.api.v1 import (
    auth,
    schools,
    academic,
    students,
    communication,
    examinations,
    fees,
    meetings,
    ussd,
    webhooks,
    parents,
    imports,
    necta,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(schools.router, prefix="/schools", tags=["Schools"])
api_router.include_router(academic.router, prefix="/academic", tags=["Academic Structure"])
api_router.include_router(students.router, prefix="/students", tags=["Students & Guardians"])
api_router.include_router(communication.router, prefix="/communication", tags=["Communication Center"])
api_router.include_router(examinations.router, prefix="/examinations", tags=["Examinations"])
api_router.include_router(fees.router, prefix="/fees", tags=["School Fees"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["Parent-Teacher Meetings"])
api_router.include_router(ussd.router, prefix="/ussd", tags=["USSD Service"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks & Callbacks"])
api_router.include_router(parents.router, prefix="/parents", tags=["Parent Portal"])
api_router.include_router(imports.router, prefix="/imports", tags=["Excel Import Center"])
api_router.include_router(necta.router, prefix="/necta", tags=["NECTA National Results"])
