from opencage.geocoder import OpenCageGeocode

OPENCAGE_API_KEY = "294d540937fe4ad3b094b18100f51245"

geocoder = OpenCageGeocode(OPENCAGE_API_KEY)


def geocode_endereco_opencage(endereco):
    results = geocoder.geocode(endereco, language="pt", countrycode="br")

    if not results:
        return None

    r = results[0]

    return {
        "lat": r["geometry"]["lat"],
        "lon": r["geometry"]["lng"],
        "confidence": r.get("confidence"),
        "components": r.get("components"),
        "formatted": r.get("formatted")
    }