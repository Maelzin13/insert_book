from fastapi import FastAPI, Request
import nest_asyncio
import uvicorn
import os
from dotenv import load_dotenv
import read_files

load_dotenv()
app = FastAPI()
SERVER_URL = os.getenv('SERVER_URL')
PASSWORD_KEY = os.getenv('PASSWORD_KEY')
SERVICE_PORT = os.getenv('SERVICE_PORT')

@app.get("/info")
async def information():
    try:
        return { "status": "success","message":"API BETA WORKING!"}
    except:
        return { "status": "error","message":"Request failed."}
@app.post("/test")

@app.post("/inspection/npor-inspection-data")
async def nport_inspection_data(request: Request):
    try:
        data = await request.json()
        print(data)
        password = data.get('key')
        if password == PASSWORD_KEY:
            return inspectionStatusNPort.inspection_data(data)
        else:
            return { "status": "error","message":"Incorrect key."}
    except:
        return { "status": "error","message":"Error request is not JSON."}
@app.post("/auction/florida-parcel-fair")
async def florida_parcel_fair_auction(request: Request):
    try:
        data = await request.json()
        print(data)
        password = data.get('key')
        if password == PASSWORD_KEY:
            return auctionFloridaParcelFair.auction_data(data)
        else:
            return { "status": "error","message":"Incorrect key."}
    except:
        return { "status": "error","message":"Error request is not JSON."}
@app.post("/auction/real-like-domain-parcels")
async def real_like_domain_parcels(request: Request):
    try:
        data = await request.json()
        print(data)
        password = data.get('key')
        if password == PASSWORD_KEY:
            return auctionRealLikeDomain.real_like_domain_parcels(data)
        else:
            return { "status": "error","message":"Incorrect key."}
    except:
        return { "status": "error","message":"Error request is not JSON."}

    try:
        data = await request.json()
        print(data)
        password = data.get('key')
        if password == PASSWORD_KEY:
            return auctionOnlineLevyclerkTsw.online_levyclerk_tsw(data)
        else:
            return { "status": "error","message":"Incorrect key."}
    except Exception as e:
        return { "status": "error","message":str(e)}
if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(app, host=SERVER_URL, port=float(SERVICE_PORT))
        
        
        
        
        