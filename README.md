Python version: 3.11

# For testing purposes
### To deploy the software locally: <br>
Install Python, and all requirements from the requirements.txt file (pip install -r requirements.txt) <br>
Then run the "command uvicorn main:app" from the app directory (append "--reload" to redeploy automatically when changing code) <br>

### To update database models via alembic: <br>
Install Python, and all requirements - // - <br>
Then run alembic init in the base folder where you pulled the project using git <br>
This will create an alembic folder alongside an alembic.ini file <br>
Edit the alembic.ini file to contain a path to the database instance <br>
And then, in the alembic folder, edit the env.py with values that are missing from the variables <br>
