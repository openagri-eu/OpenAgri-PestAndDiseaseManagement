from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from api import deps
from schemas import Message

router = APIRouter()


@router.post("/upload/", response_model=Message)
async def upload(
        csv: Optional[Annotated[UploadFile, File()]],
        excel: Optional[Annotated[UploadFile, File()]],
        db: Session = Depends(deps.get_db)
) -> Message:
    """
    Upload a file, either csv or excel
    """

    if not csv:
        if not excel:
            raise HTTPException(
                status_code=400,
                detail="No file to upload."
            )

    if not csv.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="CSV file name must end with \".csv\""
        )
    else:
        contents = await csv.read()

        # Convert it to JSON




    if excel:
        # Save the excel to the database
        pass

    return Message(message="Successfully uploaded file{} to the database.".format("s" if csv and excel else ""))
