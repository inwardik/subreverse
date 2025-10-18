from fastapi import APIRouter

router = APIRouter(
    prefix="/api",
    tags=["API"]
)

@router.get("/find_all")
def get_bookings():
    return "bookings"
