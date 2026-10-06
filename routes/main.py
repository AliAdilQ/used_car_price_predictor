from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, redirect, render_template, session, url_for

from database import Prediction
from extensions import db
from forms import PredictionForm
from services.catalog import browser_catalog
from services.prediction_service import ModelUnavailable

main = Blueprint("main", __name__)


@main.get("/")
def index():
    return render_template("index.html")


@main.route("/predict", methods=["GET", "POST"])
def predict():
    defaults = dict(brand="Toyota", model="Corolla", year=2020,
                    kilometers_driven=48000, fuel_type="Petrol", transmission="Automatic",
                    owner_type="First", engine=1800, mileage=17.0, power=139,
                    seats=5, location="Los Angeles")
    form = PredictionForm(data=defaults)
    if form.validate_on_submit():
        inputs = form.vehicle_inputs()
        try:
            estimate = current_app.extensions["prediction_service"].predict(inputs)
        except ModelUnavailable:
            current_app.logger.exception("Prediction model failed")
            flash("The estimator is temporarily unavailable. Please try again shortly.", "danger")
            return render_template("predict.html", form=form, catalog=browser_catalog()), 503
        prediction = Prediction(public_id=str(uuid4()), **inputs, **estimate)
        db.session.add(prediction)
        db.session.commit()
        # Only the originating browser (or an authenticated admin) can view details.
        session["latest_prediction"] = prediction.public_id
        return redirect(url_for("main.result", public_id=prediction.public_id))
    status = 422 if form.is_submitted() else 200
    return render_template("predict.html", form=form, catalog=browser_catalog()), status


@main.get("/result/<public_id>")
def result(public_id):
    if session.get("latest_prediction") != public_id and not session.get("admin_id"):
        abort(404)
    prediction = db.first_or_404(db.select(Prediction).filter_by(public_id=public_id))
    return render_template("result.html", prediction=prediction)


@main.get("/about")
def about():
    return render_template("about.html")
