from flask import Flask
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.middleware.proxy_fix import ProxyFix
import os

from .routes import openai_bp, astra_bp, sim_bp, root_bp


def create_app() -> Flask:
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    app = Flask(__name__, template_folder=template_dir)

    # Tell Flask to trust Cloud Run's proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    app.config["DEBUG"] = True
    app.config["ENV"] = "development"
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback-secret")

    # OAuth config from environment
    app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")

    # For local development, allow insecure transport (HTTP)
    if app.config["ENV"] == "development":
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Allow HTTP for local dev
    else:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"  # Force HTTPS for production

    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # Optional for scope leniency

    google_bp = make_google_blueprint(scope=["profile", "email"], redirect_url="/simulate")
    app.register_blueprint(google_bp, url_prefix="/login")

    # Register your app blueprints
    app.register_blueprint(root_bp)
    app.register_blueprint(openai_bp)
    app.register_blueprint(astra_bp)
    app.register_blueprint(sim_bp)

    return app


app = create_app()
