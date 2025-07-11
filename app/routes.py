from flask import Blueprint, jsonify, request, render_template, redirect, url_for, session
from flask_dance.contrib.google import google

# Import the OAuth blueprint created in app.__init__
from . import google_bp
import logging
import json
import math

from .openai_utils import summarize
from .astra_utils import update_record
from .simulation_utils import run_simulation


class NaNSafeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts NaN and infinity to safe values."""

    def encode(self, obj):
        """Encode object, converting NaN/inf to safe values."""
        if isinstance(obj, float):
            if math.isnan(obj):
                return "0"
            elif math.isinf(obj):
                return "0"
        return super().encode(obj)

    def iterencode(self, obj, _one_shot=False):
        """Iteratively encode object, handling NaN/inf values."""
        if isinstance(obj, dict):
            obj = {k: (0 if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v) for k, v in obj.items()}
        elif isinstance(obj, list):
            obj = [0 if isinstance(item, float) and (math.isnan(item) or math.isinf(item)) else item for item in obj]
        elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            obj = 0
        return super().iterencode(obj, _one_shot)


def safe_jsonify(data):
    """Safe jsonify that handles NaN values and mixed data types."""
    try:
        # First, recursively clean the data
        def clean_data(obj):
            if isinstance(obj, dict):
                # Convert all keys to strings to avoid comparison issues
                cleaned_dict = {}
                for k, v in obj.items():
                    # Convert numeric keys to strings
                    key = str(k) if isinstance(k, (int, float)) else k
                    cleaned_dict[key] = clean_data(v)
                return cleaned_dict
            elif isinstance(obj, list):
                return [clean_data(item) for item in obj]
            elif isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return 0
                return obj
            elif hasattr(obj, "item"):  # Handle numpy scalars
                return clean_data(obj.item())
            else:
                return obj

        cleaned_data = clean_data(data)
        return jsonify(cleaned_data)
    except Exception as e:
        logger.error(f"Error in safe_jsonify: {e}")
        return jsonify({"error": "Internal error processing response"}), 500


openai_bp = Blueprint("openai", __name__, url_prefix="/openai")
astra_bp = Blueprint("astra", __name__, url_prefix="/astra")
sim_bp = Blueprint("sim", __name__, url_prefix="/simulate")

# Create a root blueprint for the main routes
root_bp = Blueprint("root", __name__)

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    """Run a portfolio simulation and return the results.

    Accepts either JSON data or YAML file uploads.

    JSON format:
        {
            "events": [...],
            "steps": 12,
            "fcrdata": [...],
            "supportdata": [...]
        }

    Or upload YAML files using form fields:
        - yaml_file: Main simulation configuration (required)
        - fcrdata_file: YAML file for FCR data (optional)
        - supportdata_file: YAML file for support data (optional)
        - steps: Number of simulation steps (optional, default: 12)

    For backward compatibility, fcrdata and supportdata can also be provided
    as JSON strings in form fields.
    """

    logger.debug("=== SIMULATION REQUEST STARTED ===")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request files: {list(request.files.keys())}")
    logger.debug(f"Request form: {dict(request.form)}")

    # Check if a YAML file was uploaded
    if "yaml_file" in request.files:
        yaml_file = request.files["yaml_file"]
        if yaml_file.filename and yaml_file.filename.endswith((".yaml", ".yml")):
            try:
                yaml_content = yaml_file.read().decode("utf-8")
                from sim.utils import parseYAML

                events = parseYAML(yaml_content)
            except Exception as e:
                return jsonify({"error": f"Failed to parse YAML file: {str(e)}"}), 400
        else:
            return jsonify({"error": "Invalid file type. Please upload a .yaml or .yml file"}), 400

        # Get additional parameters from form data
        steps = int(request.form.get("steps", 12))
        fcrdata = []
        supportdata = []

        # Check for additional YAML file uploads
        if "fcrdata_file" in request.files:
            fcrdata_file = request.files["fcrdata_file"]
            if fcrdata_file.filename and fcrdata_file.filename.endswith((".yaml", ".yml")):
                try:
                    fcrdata_content = fcrdata_file.read().decode("utf-8")
                    from sim.utils import parseYAML

                    fcrdata = parseYAML(fcrdata_content)
                except Exception as e:
                    return jsonify({"error": f"Failed to parse FCRDATA YAML file: {str(e)}"}), 400

        if "supportdata_file" in request.files:
            supportdata_file = request.files["supportdata_file"]
            if supportdata_file.filename and supportdata_file.filename.endswith((".yaml", ".yml")):
                try:
                    supportdata_content = supportdata_file.read().decode("utf-8")
                    from sim.utils import parseYAML

                    supportdata = parseYAML(supportdata_content)
                except Exception as e:
                    return jsonify({"error": f"Failed to parse SUPPORTDATA YAML file: {str(e)}"}), 400

        # Fallback: Check for JSON data in form fields (backward compatibility)
        if not fcrdata and "fcrdata" in request.form:
            try:
                import json

                fcrdata = json.loads(request.form["fcrdata"])
            except (json.JSONDecodeError, ValueError):
                pass

        if not supportdata and "supportdata" in request.form:
            try:
                import json

                supportdata = json.loads(request.form["supportdata"])
            except (json.JSONDecodeError, ValueError):
                pass
    else:
        # Handle JSON request (existing functionality)
        data = request.get_json(silent=True) or {}
        events = data.get("events") or data.get("yaml")
        steps = data.get("steps", 12)
        fcrdata = data.get("fcrdata", [])
        supportdata = data.get("supportdata", [])

        # If events is a string, try to parse it as YAML
        if isinstance(events, str):
            try:
                from sim.utils import parseYAML

                events = parseYAML(events)
            except Exception as e:
                return jsonify({"error": f"Failed to parse YAML string: {str(e)}"}), 400

    # Populate FCRDATA and SUPPORTDATA if provided
    if fcrdata:
        from sim.constants import FCRDATA

        FCRDATA.clear()  # Clear existing data
        FCRDATA.extend(fcrdata)

    if supportdata:
        from sim.constants import SUPPORTDATA

        SUPPORTDATA.clear()  # Clear existing data
        SUPPORTDATA.extend(supportdata)

    # Run the simulation
    try:
        result = run_simulation(events, steps=steps)

        # Add pivot table data for better visualization
        if "budget" in result and result["budget"]:
            from sim.utils import pivotbudget
            import pandas as pd

            try:
                # Convert budget data to DataFrame
                budget_df = pd.DataFrame(result["budget"])

                # Round all numbers to 2 decimal places
                budget_df = budget_df.round(2)

                # Apply pivot transformation
                pivot_df = pivotbudget(budget_df)

                # Convert back to dict format for JSON serialization
                result["budget_pivot"] = pivot_df.reset_index().to_dict("records")

            except Exception as e:
                logger.error(f"Error creating pivot table: {e}")
                result["budget_pivot_error"] = str(e)

        return safe_jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Simulation failed: {str(e)}"}), 500


@sim_bp.route("/example", methods=["GET"])
def get_example_yaml():
    """Get an example YAML configuration for simulations."""
    example_yaml = """
# Example simulation configuration using root-level dictionary format
variables:
  monthly_rent: 2000
  equipment_budget: 5000

events:
  - name: "Project Alpha"
    time: 0
    term: 12
    budget: 100000
    staffing:
      - name: "Alice Smith"
        position: "Project Manager"
        salary: 50000
        fte: 1.0
        linemanagerrate: 400
      - name: "Bob Johnson"
        position: "Developer"
        salary: 45000
        fte: 0.8
    directcosts:
      - item: "Equipment"
        cost: "{equipment_budget}"
        frequency: "oneoff"
        step: 0
        description: "Initial equipment purchase"
      - item: "Office rent"
        cost: "{monthly_rent}"
        frequency: "monthly"
        description: "Monthly office rental"
      - item: "Utilities"
        cost: "{monthly_rent * 0.1}"
        frequency: "monthly"
        description: "Utilities (10% of rent)"
    policies:
      - policy: "Grant"
        fund: "Innovation Fund"
        amount: 25000
        step: 0

  - name: "Project Beta"
    time: 3
    term: 8
    budget: 75000
    staffing:
      - name: "Carol Davis"
        position: "Analyst"
        salary: 40000
        fte: 1.0
    directcosts:
      - item: "Software licenses"
        cost: 1500
        frequency: "annual"
        step: 0
        description: "Annual software licensing"
"""

    return jsonify(
        {
            "example_yaml": example_yaml.strip(),
            "description": "Example YAML configuration with variables and mathematical expressions",
            "usage": (
                "Save this as a .yaml file and upload to /simulate. "
                "Note: expressions like {variable*0.1} must be quoted as strings."
            ),
        }
    )


@root_bp.route("/", methods=["GET"])
def home():
    """Main entry point - redirect to simulation interface if authenticated."""
    logging.info(f"Home route accessed - Google authorized: {google.authorized}")

    if not google.authorized:
        logging.info("User not authorized, redirecting to Google login")
        return redirect(url_for("google.login"))

    # Get user info for authenticated users
    user_info = None
    try:
        resp = google.get("/oauth2/v1/userinfo")
        if resp.ok:
            user_info = resp.json()
            logging.info(f"User info retrieved: {user_info.get('name', 'Unknown')}")
        else:
            logging.error(f"Failed to get user info: {resp.status_code}")
    except Exception as e:
        logging.error(f"Error getting user info: {e}")
        user_info = {"name": "User", "email": ""}

    return render_template("index.html", user_info=user_info)


@root_bp.route("/logout")
def logout():
    """Logout the user and clear the session."""
    logging.info("=== LOGOUT PROCESS STARTED ===")
    logging.info(f"Before logout - Google authorized: {google.authorized}")
    logging.info(f"Before logout - Session keys: {list(session.keys())}")

    # Check if an OAuth token exists prior to clearing
    token_exists = hasattr(google_bp, "token") and google_bp.token is not None
    logging.info(f"OAuth token existed: {token_exists}")

    # Clear the entire session
    session.clear()
    google_bp.token = None

    logging.info(f"After logout - Google authorized: {google.authorized}")
    logging.info(f"After logout - Session keys: {list(session.keys())}")
    logging.info("=== LOGOUT PROCESS COMPLETED ===")

    # Redirect to confirmation page for debugging (change to root.home for production)
    return redirect(url_for("root.logout_confirm"))


@sim_bp.route("/pivot", methods=["POST"])
def simulate_pivot():
    """Run a portfolio simulation and return pivot table results.

    Same as /simulate but returns budget data in pivot table format for easier visualization.
    """
    # Reuse the same logic as simulate_run
    logger.debug("=== PIVOT SIMULATION REQUEST STARTED ===")

    # Get the simulation result first
    result = simulate_run()

    # If it's an error response, return it as-is
    if isinstance(result, tuple) and len(result) == 2:
        return result

    # Extract the JSON data from the response
    if hasattr(result, "get_json"):
        data = result.get_json()
    else:
        data = result.json if hasattr(result, "json") else result

    if "budget" in data:
        from sim.utils import pivotbudget
        import pandas as pd

        try:
            # Convert budget data to DataFrame
            budget_df = pd.DataFrame(data["budget"])

            # Apply pivot transformation
            pivot_df = pivotbudget(budget_df)

            # Convert back to dict format
            pivot_data = pivot_df.reset_index().to_dict("records")

            # Update the result with pivot data
            data["budget_pivot"] = pivot_data
        except Exception as e:
            logger.error(f"Error creating pivot table: {e}")
            data["budget_pivot_error"] = str(e)

    return safe_jsonify(data)


@root_bp.route("/debug-auth")
def debug_auth():
    """Debug route to check authentication status."""
    return jsonify(
        {
            "google_authorized": google.authorized,
            "session_keys": list(session.keys()),
            "google_token_exists": hasattr(google, "token") and google.token is not None,
        }
    )


@root_bp.route("/logout-confirm")
def logout_confirm():
    """Confirmation page showing logout was successful."""
    return f"""
    <html>
    <head><title>Logged Out</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>✅ Logout Successful</h1>
        <p>You have been successfully logged out.</p>
        <p>Google Authorized: {google.authorized}</p>
        <p>Session Keys: {list(session.keys())}</p>
        <a href="/" style="color: blue;">← Back to Home</a>
    </body>
    </html>
    """
