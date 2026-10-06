"""Server-side validation remains authoritative when JavaScript is unavailable."""
from datetime import datetime, timezone

from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, PasswordField, SelectField, StringField
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError

from services.catalog import CATALOG, FUELS, LOCATIONS, OWNERS, TRANSMISSIONS


def choices(values):
    return [(value, value) for value in values]


class PredictionForm(FlaskForm):
    brand = SelectField("Brand", choices=choices(sorted(CATALOG)), validators=[InputRequired()])
    model = SelectField("Model", validators=[InputRequired()])
    year = IntegerField("Manufacturing year", validators=[InputRequired()])
    kilometers_driven = IntegerField("Kilometers driven", validators=[InputRequired(), NumberRange(0, 500000)])
    fuel_type = SelectField("Fuel type", choices=choices(FUELS))
    transmission = SelectField("Transmission", choices=choices(TRANSMISSIONS))
    owner_type = SelectField("Ownership", choices=choices(OWNERS))
    engine = IntegerField("Engine capacity", validators=[InputRequired(), NumberRange(600, 6500)])
    mileage = FloatField("Fuel economy", validators=[InputRequired(), NumberRange(5, 40)])
    power = FloatField("Maximum power", validators=[InputRequired(), NumberRange(45, 700)])
    seats = SelectField("Seats", coerce=int, choices=[(n, str(n)) for n in range(2, 10)])
    location = SelectField("City", choices=choices(LOCATIONS))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        brand = self.brand.data or "Toyota"
        self.model.choices = choices(CATALOG.get(brand, {}))
        self.current_year = datetime.now(timezone.utc).year

    def validate_year(self, field):
        if field.data is None or not 2005 <= field.data <= self.current_year:
            raise ValidationError(f"Enter a year between 2005 and {self.current_year}.")

    def validate_fuel_type(self, field):
        spec = CATALOG.get(self.brand.data, {}).get(self.model.data)
        if spec and field.data not in spec[5]:
            raise ValidationError("Choose a fuel type available for this model.")

    def vehicle_inputs(self):
        from services.catalog import FEATURES
        return {key: self.current_year - self.year.data if key == "car_age"
                else getattr(self, key).data for key in FEATURES}


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[InputRequired(), Length(max=128)])


class ActionForm(FlaskForm):
    pass
