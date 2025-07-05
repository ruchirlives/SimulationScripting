from flask import Blueprint, jsonify, request

from .openai_utils import summarize
from .astra_utils import update_record
from .simulation_utils import run_simulation

openai_bp = Blueprint("openai", __name__, url_prefix="/openai")
astra_bp = Blueprint("astra", __name__, url_prefix="/astra")
sim_bp = Blueprint("sim", __name__, url_prefix="/simulate")


@openai_bp.route("/summarize", methods=["POST"])
def openai_summarize():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    summary = summarize(text)
    return jsonify({"summary": summary})


@astra_bp.route("/update", methods=["POST"])
def astra_update():
    data = request.get_json(silent=True) or {}
    result = update_record(data)
    return jsonify(result)


@sim_bp.route("", methods=["POST"])
def simulate_run():
    """Run a portfolio simulation and return the results."""
    data = request.get_json(silent=True) or {}
    events = data.get("events") or data.get("yaml")
    steps = data.get("steps", 12)
    result = run_simulation(events, steps=steps)
    return jsonify(result)
