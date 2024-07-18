from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from api import deps
from models.data import Data
from schemas import Message

router = APIRouter()


@router.post("/upload/", response_model=Message)
async def upload(
        csv: UploadFile = File(...),
        db: Session = Depends(deps.get_db)
) -> Message:
    """
    Upload a .csv file
    """

    db.query(Data).first()
    





    return Message(message="Successfully uploaded file to the database.")
