from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from api import deps
from models.data import Data
from schemas import Message

from csv import reader
from codecs import iterdecode

router = APIRouter()


@router.post("/upload/", response_model=Message)
async def upload(
        csv_file: UploadFile = File(...),
        db: Session = Depends(deps.get_db)
) -> Message:
    """
    Upload a .csv file
    """

    csv_reader = reader(iterdecode(csv_file.file, "utf-8"), delimiter=",")
    imr = 0
    for row in csv_reader:
        for col in row:
            print(type(col))
            print(col)

        imr += 1
        if imr == 2:
            break

    return Message(message="Successfully uploaded file to the database.")
