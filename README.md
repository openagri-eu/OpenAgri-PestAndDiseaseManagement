# pest-and-disease-management

# Description

The Pest and Disease Management service takes in data via datasets or live measurements and rules created\
by a user, and returns when a rule was satisfied on the specified dataset.

# Requirements

<ul>
    <li>git</li>
    <li>docker</li>
    <li>docker-compose</li>
</ul>

Docker version used during development: 27.0.3

# Installation

There are two ways to install this service, via docker or directly from source.

<h3> Deploying from source </h3>

When deploying from source, use python 3:11.\
Also, you should use a [venv](https://peps.python.org/pep-0405/) when doing this.

A list of libraries that are required for this service is present in the "requirements.txt" file.\
This service uses FastAPI as a web framework to serve APIs, alembic for database migrations sqlalchemy for database ORM mapping.

<h3> Deploying via docker </h3>

After installing <code> docker </code> you can run the following commands to run the application:

```
docker compose build
docker compose up
```

The application will be served on http://127.0.0.1:80 (I.E. typing localhost/docs in your browser will load the swagger documentation)

# Documentation

<h3> POST </h3>

```
/api/v1/data/upload/
```

Request body: \
This API expects a dataset in the form of a .csv file. \
This .csv file must contain "date" and "time" as columns, as well as at least one of the following columns:

```
"parcel_location", "atmospheric_temperature", "atmospheric_temperature_daily_min",
"atmospheric_temperature_daily_max", "atmospheric_temperature_daily_average", "atmospheric_relative_humidity",
"atmospheric_pressure", "precipitation", "average_wind_speed", "wind_direction", "wind_gust",
"leaf_relative_humidity", "leaf_temperature", "leaf_wetness",
"soil_temperature_10cm", "soil_temperature_20cm", "soil_temperature_30cm", "soil_temperature_40cm",
"soil_temperature_50cm", "soil_temperature_60cm", "solar_irradiance_copernicus"
```

The date should look like this: "2024-10-10", "2024-09-05", etc. (YYYY-mm-dd), in python: (%Y-%m-%d) \
The time should look like this: "10:10:15", "01:15:59", "01:01:01", etc. (HH:MM:SS), in python: (%H:%M:%S)

An example of a dataset would look something like this: 

date;time;atmospheric_temperature,wind_direction \
2024-05-12;12:00:00;18;north \
2024-05-12;13:00:00;19;north-east \
2024-05-12;14:00:00;24;north

The order of the columns does not matter, another example of a valid dataset:

date;wind_direction;leaf_wetness;time \
2022-01-01;south;0.13;01:00:00 \
2022-01-01;south-west;0.14;02:00:00 \
2022-01-01;south-west;0.13;03:00:00

The API will ignore columns that are present in the dataset but aren't part of the list above.

An example of an invalid dataset: \
date;wind_direction \
2022-01-01;north \
2022-01-02;south

Reason: missing "time" column

Another example: \
date;leaf_wetness;time;leaf_temperature;leaf_density \
2021-03-03;1.25;12:00:00;11 \
2021-03-04;0.75;12:00:00;12 \
2021-03-05;0.68;12:00:00;eleven

Reasons:
1. The leaf_wetness metric can only be expressed as a value [0, 1], the first row shows 1.25 which is outside this range.
2. The last row has a leaf_temperature of "eleven" which will not be parsed, it should be "11".

Note: \
The leaf_density column would not provide an issue when parsing, this column would just be skipped.

Response example:

```json
{
    "msg": "Successfully uploaded file."
}
```

<h3> GET </h3>

```
/api/v1/pest-model/
```

Request body:

Nothing

Response example:

```json
{
  "pests": [
    {
      "id": "9bf91b39-04eb-4446-9139-f7181da6f31f",
      "name": "Περονόσπορος, Plasmopara viticola",
      "description": "Uncinula necator (syn. Erysiphe necator) is a fungus that causes powdery mildew of grape. It is a common pathogen of Vitis species, including the wine grape, Vitis vinifera",
      "geo_areas_of_application": "((30.123 10.32454, 40.345 40.1234563, 20.9675 40.67854, 10.23508 20.23578, 30.23465584 10.16938))"
    },
    {
      "id": "c15b5f4b-4881-4760-ab2e-3ca5090e8493",
      "name": "Botrytis cinerea",
      "description": "Botrytis cinerea (Ascomycota) infects over 200 plant species, causing grey mould, evident on the surface as grey fluffy mycelium. Worldwide, it causes annual losses of $10 billion to $100 billion.",
      "geo_areas_of_application": "POLYGON ((-60.0870329 -12.9315478, -61.5073816 -25.3204334, -62.6987366 -24.5766272, -64.1853669 -24.0497260, -67.7152546 -27.4752321, -68.4190340 -26.9510818, -67.6018452 -21.5489551, -64.3083560 -21.6772242, -63.1471630 -21.9415438, -64.1137279 -14.2398013, -60.0870329 -12.9315478))"
    }
  ]
}
```

This API returns a list of pest models currently in the system.

<h3> POST </h3>

```
/api/v1/pest-model/
```

Request body:

```json
{
  "name": "Phytophthora sojae",
  "description": "Phytophthora sojae is an oomycete pathogen of soybean, classified in the kingdom Stramenopiles. It causes 'damping off' of seedlings and root rot of older plants.",
  "geo_areas_of_application": "POLYGON ((14.2345, -2.2345))",
  "cultivations": [ "soybean", "bluebonnet", "lupinus albus" ]
}
```

Response example:

```json
{
  "id": "9489c55a-847c-4cd2-8392-ddc72b549ec4",
  "name": "Phytophthora sojae",
  "description": "Phytophthora sojae is an oomycete pathogen of soybean, classified in the kingdom Stramenopiles. It causes 'damping off' of seedlings and root rot of older plants.",
  "geo_areas_of_application": "POLYGON ((14.2345, -2.2345))"
}
```

This API creates an empty pest model (meaning with no rules) in the system. \
This pest model can then be assigned rules via the POST /rule/ API.

<h3> POST </h3>

```
/api/v1/tool/calculate-risk-index/weather/{weather_dataset_id}/model/{model_ids}/verbose
```

Path parameters:
1. weather_dataset_id: the id of the weather dataset that you wish to use for this calculation (uploaded previously via the POST /api/v1/data/upload/ API)
2. model_ids: a list of uuids (uuid-v4) that correspond to the pest_models that you wish to calculate for.

Request body:

Nothing

Response example:

```json
{
  	"@context":
		{
			"ocsm": "https://w3id.org/ocsm/",
			"fsm": "http://www.farmtopia.com/ontology/farmtopia#",
			"foodie": "http://foodie-cloud.com/model/foodie#",
			"saref": "https://saref.etsi.org/core/"
		},
  	"@graph": [
	  	{
			"@id": "urn:openagri:pestModel:101",
			"@type": "ocsm:AIPestDetectionModel",
			"fsm:eppoCode": "UNCINE",
			"foodie:description": "Uncinula necator (syn. Erysiphe necator) is a fungus that causes powdery mildew of grape. It is a common pathogen of Vitis species, including the wine grape, Vitis vinifera",
			"ocsm:hasPredictedInfestationRisks": [
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360259a",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T01:00:00",
					"ocsm:hasRiskLevel": "Low"
				},
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360259b",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T02:00:00",
					"ocsm:hasRiskLevel": "High"
				},
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360259c",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T03:00:00",
					"ocsm:hasRiskLevel": "Medium"
				}
			],
			"ocsm:basedOnWeatherDataset": {
				"@id":"urn:openagri:weatherDataset:1234",
				"@type": "ocsm:WeatherDataset"
			}
		},
		{
			"@id": "urn:openagri:pestModel:102",
			"@type": "ocsm:AIPestDetectionModel",
			"fsm:eppoCode": "PLASVI",
			"foodie:description": "Plasmopara viticola, the causal agent of grapevine downy mildew, is a heterothallic oomycete that overwinters as oospores in leaf litter and soil.",
			"ocsm:hasPredictedInfestations": [
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360250a",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T01:00:00",
					"ocsm:hasRiskLevel": "High"
				},
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360250b",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T02:00:00",
					"ocsm:hasRiskLevel": "High"
				},
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360250c",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T03:00:00",
					"ocsm:hasRiskLevel": "High"
				}
			],
			"ocsm:basedOnWeatherDataset": {
				"@id":"urn:openagri:weatherDataset:1234",
				"@type": "ocsm:WeatherDataset"
			}
		}
	]
}
```

This API returns a [JSON-LD](https://json-ld.org/playground/), an example of which you can view [here](https://github.com/openagri-eu/OCSM/blob/main/examples/pest-infestation-risk.jsonld). \
The main bit of information about the risk infestation metric can be found within the "ocsm:hasPredictedInfestations" type key. \
This object holds the "ocsm:hasRiskLevel" key which will have either "Low", "Medium" or "High" depending on the results of the calculations.

<h3> POST </h3>

```
api/v1/tool/calculate-risk-index/weather/{weather_dataset_id}/model/{model_ids}/high
```

Path parameters:
1. weather_dataset_id: the id of the weather dataset that you wish to use for this calculation (uploaded previously via the POST /api/v1/data/upload/ API)
2. model_ids: a list of uuids (uuid-v4) that correspond to the pest_models that you wish to calculate for.

Request body:

Nothing

Response example:

```json
{
  	"@context":
		{
			"ocsm": "https://w3id.org/ocsm/",
			"fsm": "http://www.farmtopia.com/ontology/farmtopia#",
			"foodie": "http://foodie-cloud.com/model/foodie#",
			"saref": "https://saref.etsi.org/core/"
		},
  	"@graph": [
	  	{
			"@id": "urn:openagri:pestModel:101",
			"@type": "ocsm:AIPestDetectionModel",
			"fsm:eppoCode": "UNCINE",
			"foodie:description": "Uncinula necator (syn. Erysiphe necator) is a fungus that causes powdery mildew of grape. It is a common pathogen of Vitis species, including the wine grape, Vitis vinifera",
			"ocsm:hasPredictedInfestationRisks": [
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360259b",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T02:00:00",
					"ocsm:hasRiskLevel": "High"
				}
			],
			"ocsm:basedOnWeatherDataset": {
				"@id":"urn:openagri:weatherDataset:1234",
				"@type": "ocsm:WeatherDataset"
			}
		},
		{
			"@id": "urn:openagri:pestModel:102",
			"@type": "ocsm:AIPestDetectionModel",
			"fsm:eppoCode": "PLASVI",
			"foodie:description": "Plasmopara viticola, the causal agent of grapevine downy mildew, is a heterothallic oomycete that overwinters as oospores in leaf litter and soil.",
			"ocsm:hasPredictedInfestations": [
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360250a",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T01:00:00",
					"ocsm:hasRiskLevel": "High"
				},
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360250b",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T02:00:00",
					"ocsm:hasRiskLevel": "High"
				},
				{
					"@id": "urn:openagri:pestPrediction:72d9fb43-53f8-4ec8-a33c-fa931360250c",
					"@type": "fsm:PestInfestationRisk",
					"saref:hasTimestamp": "2024-08-31T03:00:00",
					"ocsm:hasRiskLevel": "High"
				}
			],
			"ocsm:basedOnWeatherDataset": {
				"@id":"urn:openagri:weatherDataset:1234",
				"@type": "ocsm:WeatherDataset"
			}
		}
	]
}
```

Note: \
This API functions the same as the .../verbose one, while additionally filter out any risk calculations that aren't "High".

<h3> GET </h3>

```
/api/v1/rule/
```

Request body:

Nothing

Response example:

```json
{
  "rules": [
    {
      "id": "1",
      "name": "Plasmopara viticola",
      "description": "The causal agent of grapevine downy mildew",
      "conditions": [
        {
          "unit_id": 5,
          "operator_id": 1,
          "value": 80.0
        },
        {
          "unit_id": 1,
          "operator_id": 4,
          "value": 10.0
        },
        {
          "unit_id": 7,
          "operator_id": 5,
          "value": 10.0
        }
      ]
    },
    {
      "id": "2",
      "name": "Plasmopara viticola",
      "description": "The causal agent of grapevine downy mildew",
      "conditions": [
        {
          "unit_id": 5,
          "operator_id": 1,
          "value": 80.0
        },
        {
          "unit_id": 1,
          "operator_id": 1,
          "value": 10.0
        },
        {
          "unit_id": 1,
          "operator_id": 2,
          "value": 20.0
        },
        {
          "unit_id": 7,
          "operator_id": 5,
          "value": 10.0
        }
      ]
    }
  ]
}
```

This API returns a list of all rules stored in the system. \
Rules make up a pest model, but they can also be added separately.

The above rules, translated into a friendlier format: \
1. H > 80% AND T <= 10 AND P == 10 \
2. H > 80% AND 10 < T <= 20 AND P == 10

Where: 
1. H = Humidity
2. T = Atmospheric temperature
3. P = Precipitation

<h3> DELETE </h3>

```
/api/v1/rule/{rule_id}
```

Path parameters:
1. rule_id: the id of the rule that should be deleted.

Request body:

Nothing

Response example:

```json
{
  "message": "Successfully removed rule!"
}
```

This API removes a rule via its id.

<h3> POST </h3>

```
/api/v1/rule/
```

Request body:

```json
{
  "name": "example rule",
  "description": "my example rule",
  "probability_value": "low",
  "pest_model_id": "23cfdd48-f564-44a1-922a-e8c972fc5eac",
  "conditions": [
    {
      "unit_id": 5,
      "operator_id": 1,
      "value": 80
    },
    {
      "unit_id": 1,
      "operator_id": 1,
      "value": 10
    }
  ]
}
```

Response example:
```json
{
    "id": 1,
    "name": "my_rule",
    "description": "my_description",
    "conditions": [
        {
            "unit_id": 1,
            "operator_id": 1,
            "value": 51
        },
        {
            "unit_id": 2,
            "operator_id": 2,
            "value": 12
        }
    ]
}
```

This API creates a single rule that is added to an existing pest model.

# General guidance

in general, the way a user would attempt to use this service is the following:

1. Upload a dataset with weather data via the POST /api/v1/data/upload/ API
2. Create a pest model (POST /api/v1/pest-model/) with accompanying rules (POST /api/v1/rule/)
3. Call the GET /api/v1/tool/calculate-risk-index/weather/{weather_dataset_id}/model/{model_ids}/verbose API for risk calculations

For more information about the APIs and schemas, please view the swagger documentation.

# Contribution
Please contact the maintainer of this repository.

# License
[European Union Public License 1.2](https://github.com/openagri-eu/pest-and-disease-management/blob/main/LICENSE)
