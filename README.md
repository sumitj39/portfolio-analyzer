# portfolio-analyzer
Analyzes the basket of stocks according to portfolio theory and gives the efficient frontier of the basket

## Work In Progress
Only REST APIs are available at this point.

## How to run?
1. `python webapp/app.py  # start the webserver`    
2. Make a `POST` request to `http://localhost:8080/portfolio/` with the json body
```json
{
	"scrips": [
		"DMART",
		"GOLDBEES",
		"HDFC",
		"JUNIORBEES",
		"NIFTYBEES",
		"TCS",
		"MARUTI",
		"KNRCON"
	]
}
```
The response gives a list of portfolio weights with risk and return for each portfolio.    
Note that the return and risk(standard deviation) are in percentages.
```json
[
  {
    "return": 23.986737668277392,
    "risk": 14.774692928135622,
    "scrips": [
      "MARUTI",
      "GOLDBEES",
      "JUNIORBEES",
      "HDFC",
      "NIFTYBEES",
      "KNRCON",
      "TCS",
      "DMART"
    ],
    "weights": [
      0.0960042459422027,
      0.16718838020686425,
      0.03683398762910989,
      0.08403751943229205,
      0.1918430765208974,
      0.1924467818128828,
      0.08663514588064541,
      0.14501086257510534
    ]
  },
  {
    "return": 20.60783467650973,
    "risk": 12.420092136219994,
    "scrips": [
      "MARUTI",
      "GOLDBEES",
      "JUNIORBEES",
      "HDFC",
      "NIFTYBEES",
      "KNRCON",
      "TCS",
      "DMART"
    ],
    "weights": [
      0.17784671635151086,
      0.15622785128036615,
      0.1434677802265121,
      0.0016271597297020561,
      0.16391569922459248,
      0.05061768469998313,
      0.18176752564195378,
      0.1245295828453795
    ]
  },
  ...
]
```
