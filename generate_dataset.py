"""Generate reproducible, related synthetic vehicle records (not real listings)."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from config import BASE_DIR
from services.catalog import CATALOG, FEATURES, LOCATIONS, OWNERS

REFERENCE_YEAR = 2026


def generate_dataset(rows=3600, output=None, seed=42):
    if rows < 1000:
        raise ValueError("Use at least 1,000 records for the demo dataset.")
    rng = np.random.default_rng(seed)
    records = []
    vehicles = [(brand, model, spec) for brand, models in CATALOG.items()
                for model, spec in models.items()]
    city_factor = {city: factor for city, factor in zip(
        LOCATIONS, [1.03, 1.04, .98, .97, .96, 1.03, 1.06, 1.01, 1.00, 1.02])}
    for index in range(rows):
        brand, model, spec = vehicles[index % len(vehicles)]
        new_price, engine, power, economy, seats, fuels = spec
        age = int(rng.integers(1, 22))
        km = int(np.clip(age * rng.normal(12500, 3800), 2500, 380000))
        owner = str(rng.choice(OWNERS, p=[.51, .31, .13, .05]))
        fuel = str(rng.choice(fuels))
        transmission = str(rng.choice(["Automatic", "Manual"], p=[.77, .23]))
        engine = int(engine + rng.choice([-200, 0, 0, 0, 400]))
        power = round(max(65, power + (engine - spec[1]) * .07 + rng.normal(0, 8)), 1)
        economy = round(max(6, economy + (6 if fuel == "Hybrid" else 2 if fuel == "Diesel" else 0)
                            - (engine - spec[1]) / 600 + rng.normal(0, .6)), 1)
        location = str(rng.choice(LOCATIONS))
        adjusted_new = new_price * (1 + (engine - spec[1]) / 16000
                                   + (power - spec[2]) / 1800)
        price = adjusted_new * np.exp(-.073 * age) * np.exp(-km / 1200000)
        price *= [1, .945, .89, .83][OWNERS.index(owner)]
        price *= 1.045 if transmission == "Automatic" else .975
        price *= 1.08 if fuel == "Hybrid" else 1.025 if fuel == "Diesel" else 1
        price *= city_factor[location] * rng.normal(1, .045)
        records.append(dict(brand=brand, model=model, year=REFERENCE_YEAR - age,
                            kilometers_driven=km, fuel_type=fuel,
                            transmission=transmission, owner_type=owner,
                            engine=engine, mileage=economy, power=power,
                            seats=seats, car_age=age, location=location,
                            price=round(max(1200, price), 2)))
    frame = pd.DataFrame(records)[FEATURES + ["price"]]
    # Realistic missing specifications exercise training-time imputation.
    for column in ["mileage", "power"]:
        frame.loc[rng.choice(rows, rows // 100, replace=False), column] = np.nan
    frame = frame.sample(frac=1, random_state=seed).reset_index(drop=True)
    target = Path(output or BASE_DIR / "data" / "used_cars.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)
    print(f"Generated {len(frame):,} synthetic USD records -> {target}")
    return frame


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=3600)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    generate_dataset(args.rows, args.output)
