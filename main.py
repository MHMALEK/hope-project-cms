from fastapi import Depends, FastAPI, Request, HTTPException
from models import (
    database,
    engine,
    SessionLocal,
    User,
    Base,
    UserCreate,
    VPN,
    VPNCreate,
    DownloadURLs,
)
from sqlalchemy.exc import IntegrityError
from auth import security
from typing import List
from fastapi import Query
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    async with database:
        # Here we create tables for all models (if they don't exist)
        Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/test", dependencies=[Depends(security)])
async def root():
    return {"message": "Hello World"}


@app.post("/api/user/create", response_model=UserCreate)
async def create_user(user: UserCreate):
    db_user = User(**user.dict())

    # Start a new database session
    db = SessionLocal()

    try:
        # Add and commit the new user to the database
        db.add(db_user)
        db.commit()
    except IntegrityError:
        # In case of any error, rollback the transaction
        db.rollback()
        return {"error": "User with this email or telegram ID already exists."}

    # Refresh the user instance to get its id
    db.refresh(db_user)

    return db_user


@app.post("/api/vpn/create", response_model=VPNCreate)
async def create_vpn(vpn: VPNCreate):
    vpn.supported_os = ",".join(vpn.supported_os)
    db_vpn = VPN(**vpn.dict(exclude={"download_urls"}))
    db = SessionLocal()

    try:
        db.add(db_vpn)
        db.commit()
        db.refresh(db_vpn)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="VPN with this title or name already exists."
        )

    download_urls = {k: ",".join(v) for k, v in vpn.download_urls.dict().items()}
    db_urls = DownloadURLs(**download_urls, vpn_id=db_vpn.id)

    try:
        db.add(db_urls)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating download URLs.")

    db_vpn.supported_os = db_vpn.supported_os.split(",")
    return db_vpn


@app.put("/api/vpn/update/{id}", response_model=VPNCreate)
async def update_vpn(id: int, vpn: VPNCreate):
    db = SessionLocal()
    db_vpn = db.query(VPN).filter(VPN.id == id).first()

    if not db_vpn:
        raise HTTPException(status_code=404, detail="VPN not found.")

    for key, value in vpn.dict().items():
        if key == "supported_os":
            value = ",".join(value)
        setattr(db_vpn, key, value)

    try:
        db.commit()
        db.refresh(db_vpn)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error updating VPN.")

    db_vpn.supported_os = db_vpn.supported_os.split(",")
    return db_vpn


@app.delete("/api/vpn/{id}")
async def delete_vpn(id: int):
    db = SessionLocal()

    db_vpn = db.query(VPN).filter(VPN.id == id).first()

    if not db_vpn:
        return {"error": "VPN not found."}

    db.delete(db_vpn)
    db.commit()

    return {"message": "VPN deleted successfully."}


@app.get("/api/vpn/{id}", response_model=VPNCreate)
async def get_vpn(id: int):
    db = SessionLocal()
    db_vpn = db.query(VPN).join(DownloadURLs).filter(VPN.id == id).first()
    print(db_vpn.download_urls[0].windows)
    if not db_vpn:
        raise HTTPException(status_code=404, detail="VPN not found.")

    db_vpn.supported_os = db_vpn.supported_os.split(",")
    download_url = db_vpn.download_urls[0]
    db_vpn.download_urls.windows = [download_url.windows]
    db_vpn.download_urls.mac = [download_url.mac]
    db_vpn.download_urls.linux = [download_url.linux]
    db_vpn.download_urls.android = [download_url.android]
    db_vpn.download_urls.ios = [download_url.ios]
    return db_vpn


@app.get("/api/vpn/list", response_model=List[VPNCreate])
async def get_vpns():
    db = SessionLocal()
    vpns = db.query(VPN).all()
    return vpns


@app.get("/api/vpn/query", response_model=List[VPNCreate])
async def get_vpn(price: bool = Query(None), supported_os: str = Query(None)):
    db = SessionLocal()

    # Start with a query that includes all VPNs
    query = db.query(VPN)

    # If the price filter is provided, only include VPNs with that price
    if price is not None:
        query = query.filter(VPN.is_free == price)

    # If the supported_os filter is provided, only include VPNs that support the given OS
    # This assumes that the supported_os field is a string that contains the names of the supported operating systems
    if supported_os is not None:
        query = query.filter(VPN.supported_os.contains(supported_os))

    # Execute the query and return the results
    vpns = query.all()

    return vpns


@app.get("/admin/vpn/list", response_model=List[VPNCreate])
async def get_vpns_html(request: Request):
    db = SessionLocal()
    vpns = db.query(VPN).all()
    return templates.TemplateResponse(
        "vpn.list.html", {"request": request, "vpns": vpns}
    )
