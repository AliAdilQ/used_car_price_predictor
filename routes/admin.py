"""Authenticated administration, bounded search, and CSRF-protected mutations."""
from datetime import timedelta
from functools import wraps
from time import time

import pandas as pd
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from database import Admin, Prediction, utc_now
from extensions import db
from forms import ActionForm, LoginForm

admin = Blueprint("admin", __name__, url_prefix="/admin")
_DUMMY_HASH = generate_password_hash("dummy-timing-check")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        account = db.session.get(Admin, session.get("admin_id")) if session.get("admin_id") else None
        if account is None:
            session.pop("admin_id", None)
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


@admin.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id") and db.session.get(Admin, session["admin_id"]):
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    # Process-local throttling avoids keeping raw passwords or client-controlled counters.
    # For multi-worker production, replace with a shared-store limiter.
    attempts = current_app.extensions.setdefault("login_attempts", {})
    now = time()
    for key in list(attempts):
        attempts[key] = [stamp for stamp in attempts[key] if stamp > now - 300]
        if not attempts[key]:
            attempts.pop(key)
    client = request.remote_addr or "unknown"
    if form.validate_on_submit():
        if len(attempts.get(client, [])) >= 5:
            flash("Too many attempts. Try again in five minutes.", "danger")
            return render_template("admin/login.html", form=form), 429
        account = db.session.scalar(db.select(Admin).filter_by(username=form.username.data.strip()))
        valid = account.check_password(form.password.data) if account else check_password_hash(_DUMMY_HASH, form.password.data)
        if account and valid:
            attempts.pop(client, None)
            session.clear()
            session["admin_id"] = account.id
            session["admin_username"] = account.username
            session.permanent = True
            return redirect(url_for("admin.dashboard"))
        attempts.setdefault(client, []).append(now)
        flash("Incorrect username or password.", "danger")
        return render_template("admin/login.html", form=form), 401
    return render_template("admin/login.html", form=form), 422 if form.is_submitted() else 200


@admin.post("/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin.get("/")
@admin_required
def dashboard():
    today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    total = db.session.scalar(db.select(func.count(Prediction.id))) or 0
    today_count = db.session.scalar(db.select(func.count(Prediction.id)).where(Prediction.created_at >= today)) or 0
    average = db.session.scalar(db.select(func.avg(Prediction.predicted_price))) or 0
    brands = db.session.execute(db.select(Prediction.brand, func.count(Prediction.id),
                                         func.avg(Prediction.predicted_price))
                                .group_by(Prediction.brand).order_by(func.count(Prediction.id).desc(), Prediction.brand)).all()
    daily = dict(db.session.execute(db.select(func.date(Prediction.created_at), func.count(Prediction.id))
                                   .where(Prediction.created_at >= today - timedelta(days=6))
                                   .group_by(func.date(Prediction.created_at))).all())
    dates = [today - timedelta(days=n) for n in range(6, -1, -1)]
    charts = {"brands": {"labels": [row[0] for row in brands], "values": [row[1] for row in brands]},
              "activity": {"labels": [day.strftime("%a") for day in dates],
                           "values": [daily.get(day.strftime("%Y-%m-%d"), 0) for day in dates]}}
    recent = db.session.scalars(db.select(Prediction).order_by(Prediction.created_at.desc()).limit(5)).all()
    return render_template("admin/dashboard.html", total=total, today_count=today_count,
                           average=average, top_brand=brands[0][0] if brands else "—",
                           recent=recent, charts=charts, action_form=ActionForm())


@admin.get("/predictions")
@admin_required
def predictions():
    query = request.args.get("q", "").strip()[:80]
    sort = request.args.get("sort", "newest")
    ordering = {"newest": Prediction.created_at.desc(), "oldest": Prediction.created_at.asc(),
                "price_high": Prediction.predicted_price.desc(), "price_low": Prediction.predicted_price.asc()}
    statement = db.select(Prediction)
    if query:
        statement = statement.where(or_(Prediction.brand.contains(query, autoescape=True),
                                       Prediction.model.contains(query, autoescape=True),
                                       Prediction.location.contains(query, autoescape=True)))
    statement = statement.order_by(ordering.get(sort, ordering["newest"]), Prediction.id.desc())
    page = db.paginate(statement, per_page=10, max_per_page=10, error_out=False)
    return render_template("admin/predictions.html", pagination=page, query=query, sort=sort,
                           action_form=ActionForm())


@admin.post("/predictions/<int:prediction_id>/delete")
@admin_required
def delete_prediction(prediction_id):
    prediction = db.get_or_404(Prediction, prediction_id)
    db.session.delete(prediction)
    db.session.commit()
    flash("Prediction deleted.", "success")
    return redirect(url_for("admin.predictions"))


@admin.post("/predictions/clear")
@admin_required
def clear_predictions():
    if request.form.get("confirmation") != "CLEAR":
        flash("Type CLEAR to confirm deleting the history.", "danger")
        return redirect(url_for("admin.predictions"))
    db.session.execute(db.delete(Prediction))
    db.session.commit()
    flash("Prediction history cleared.", "success")
    return redirect(url_for("admin.predictions"))


@admin.get("/dataset")
@admin_required
def dataset():
    frame = pd.read_csv(current_app.config["DATASET_PATH"])
    numeric = frame.select_dtypes(include="number").describe().round(1)
    summary = [{"column": col, "dtype": str(frame[col].dtype),
                "missing": int(frame[col].isna().sum()),
                "unique": int(frame[col].nunique())} for col in frame.columns]
    distribution = frame.brand.value_counts().to_dict()
    return render_template("admin/dataset.html", rows=len(frame), columns=summary,
                           missing=int(frame.isna().sum().sum()),
                           statistics=numeric.to_dict(), distribution=distribution,
                           action_form=ActionForm())
