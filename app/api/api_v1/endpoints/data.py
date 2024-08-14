import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from api import deps
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
    Upload a .csv file (Using the ploutos .csv provided as how a baseline file should be formatted)
    """

    csv_reader = reader(iterdecode(csv_file.file, "utf-8"), delimiter=",")
    first_column = True
    for row in csv_reader:
        if first_column:
            # Check against existing units, if new ones add the to db.
            for col in row:
                print(col)

            first_column = False
            return Message(message="testing message")
            continue

        aggregate_str = ""
        for col in row:
            aggregate_str += col + ";"

        temp = [ags for ags in aggregate_str.split(";") if ags != ""]

        if len(temp) < 14:
            print("skipped row")
            continue

        # TODO: Optimization: instead of doing a insert by insert, create a batch insert job for the db (1000 at a time)

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
        data.create(db=db, obj_in=obj_in)

    return Message(message="Successfully uploaded file to the database.")
