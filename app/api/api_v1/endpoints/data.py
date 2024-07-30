import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from api import deps
from models.data import Data
from schemas import Message, CreateData
from crud import data

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
    first_column = True
    for row in csv_reader:
        if first_column:
            first_column = False
            continue

        aggregate_str = ""
        for col in row:
            aggregate_str += col + ";"

        temp = [ags for ags in aggregate_str.split(";") if ags != ""]

        if len(temp) < 14:
            print("skipped row")
            continue

        # Parse .csv file
        obj_in = CreateData(
            date=datetime.datetime.strptime(temp[0], "%Y-%m-%d"),
            time=datetime.datetime.strptime(temp[1], "%H:%M:%S").time(),
            nuts3=temp[2],
            nuts2=temp[3],
            temperature_air=int(temp[4]),
            relative_humidity=int(temp[5]),
            precipitation=int(temp[6]),
            wind_speed=int(temp[7]),
            wind_direction=int(temp[8]),
            wind_gust=int(temp[9]),
            atmospheric_pressure=int(temp[10]),
            relative_humidity_canopy=int(temp[11]),
            temperature_canopy=int(temp[12]),
            solar_irradiance_copernicus=int(temp[13])
        )
        response_obj = data.create(db=db, obj_in=obj_in)


    return Message(message="Successfully uploaded file to the database.")
