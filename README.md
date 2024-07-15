# pest-and-disease-management


# Dependencies
This service depends on docker[27.0.3] and python[3.11]

# Running
To run this service, first navigate to the root folder via terminal, and run:\
docker build -t pdm .\
Then, once it builds the image, run:\
docker run -d --name pdm -p 80:80 pdmc

Then, you'll be able to access the backend via localhost/docs.
