"""Representative vehicle specifications for the synthetic USD demo market.

These are approximate reference configurations, not manufacturer specifications.
Tuple: new price USD, engine cc, power hp, fuel economy km/L, seats, fuels.
"""
CATALOG = {
    "Toyota": {
        "Corolla": (24500, 1800, 139, 17.0, 5, ["Petrol", "Hybrid"]),
        "Camry": (32500, 2500, 203, 15.0, 5, ["Petrol", "Hybrid"]),
        "RAV4": (35000, 2500, 203, 13.5, 5, ["Petrol", "Hybrid"]),
    },
    "Honda": {
        "Civic": (26500, 1800, 158, 16.5, 5, ["Petrol"]),
        "Accord": (33000, 2000, 192, 15.2, 5, ["Petrol", "Hybrid"]),
        "CR-V": (35500, 1500, 190, 13.5, 5, ["Petrol", "Hybrid"]),
    },
    "Hyundai": {
        "Elantra": (23000, 2000, 147, 16.0, 5, ["Petrol", "Hybrid"]),
        "Tucson": (31000, 2000, 161, 12.8, 5, ["Petrol", "Diesel"]),
        "Santa Fe": (36500, 2500, 191, 11.5, 7, ["Petrol", "Diesel"]),
    },
    "Suzuki": {
        "Swift": (17000, 1200, 89, 20.5, 5, ["Petrol"]),
        "Vitara": (23500, 1600, 118, 16.0, 5, ["Petrol"]),
        "Ertiga": (21500, 1500, 103, 18.0, 7, ["Petrol"]),
    },
    "Kia": {
        "Forte": (22000, 2000, 147, 16.0, 5, ["Petrol"]),
        "Sportage": (31500, 2000, 181, 12.5, 5, ["Petrol", "Diesel"]),
        "Sorento": (36500, 2500, 191, 11.8, 7, ["Petrol", "Hybrid"]),
    },
    "Nissan": {
        "Sentra": (23000, 1800, 124, 16.0, 5, ["Petrol"]),
        "Altima": (28500, 2500, 188, 14.5, 5, ["Petrol"]),
        "Rogue": (33500, 2500, 181, 13.0, 5, ["Petrol"]),
    },
    "Ford": {
        "Focus": (24500, 1600, 125, 15.8, 5, ["Petrol", "Diesel"]),
        "Escape": (32000, 1500, 181, 12.8, 5, ["Petrol", "Hybrid"]),
        "Mustang": (44000, 2300, 310, 9.8, 4, ["Petrol"]),
    },
    "BMW": {
        "3 Series": (46000, 2000, 255, 13.5, 5, ["Petrol", "Diesel"]),
        "5 Series": (61000, 2000, 248, 12.8, 5, ["Petrol", "Diesel"]),
        "X3": (52000, 2000, 248, 11.8, 5, ["Petrol", "Diesel"]),
    },
    "Mercedes-Benz": {
        "C-Class": (48000, 2000, 255, 13.2, 5, ["Petrol", "Diesel"]),
        "E-Class": (64000, 2000, 255, 12.0, 5, ["Petrol", "Diesel"]),
        "GLC": (54000, 2000, 255, 11.4, 5, ["Petrol", "Diesel"]),
    },
    "Audi": {
        "A3": (36500, 1400, 150, 15.5, 5, ["Petrol", "Diesel"]),
        "A4": (45000, 2000, 201, 13.8, 5, ["Petrol", "Diesel"]),
        "Q5": (52500, 2000, 261, 11.8, 5, ["Petrol", "Diesel"]),
    },
    "Volkswagen": {
        "Golf": (28000, 1400, 150, 16.0, 5, ["Petrol", "Diesel"]),
        "Jetta": (25000, 1400, 147, 16.5, 5, ["Petrol"]),
        "Tiguan": (33500, 2000, 184, 12.5, 5, ["Petrol", "Diesel"]),
    },
    "Mazda": {
        "Mazda3": (26500, 2000, 155, 15.5, 5, ["Petrol"]),
        "CX-5": (32500, 2500, 187, 12.5, 5, ["Petrol", "Diesel"]),
        "MX-5": (33000, 2000, 181, 13.5, 2, ["Petrol"]),
    },
}

LOCATIONS = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
             "Seattle", "San Francisco", "Miami", "Denver", "Boston"]
FUELS = ["Petrol", "Diesel", "Hybrid"]
TRANSMISSIONS = ["Automatic", "Manual"]
OWNERS = ["First", "Second", "Third", "Fourth or more"]
NUMERIC_FEATURES = ["year", "kilometers_driven", "engine", "mileage", "power",
                    "seats", "car_age"]
CATEGORICAL_FEATURES = ["brand", "model", "fuel_type", "transmission",
                        "owner_type", "location"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def browser_catalog():
    return {
        brand: {
            model: dict(engine=spec[1], power=spec[2], mileage=spec[3],
                        seats=spec[4], fuels=spec[5])
            for model, spec in models.items()
        }
        for brand, models in CATALOG.items()
    }
