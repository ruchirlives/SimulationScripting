from flask import Flask

from .routes import openai_bp, astra_bp, sim_bp


def create_app() -> Flask:
    """Application factory for creating the Flask app."""
    app = Flask(__name__)
    app.register_blueprint(openai_bp)
    app.register_blueprint(astra_bp)
    app.register_blueprint(sim_bp)
    return app


# Create a default app for simple use cases
app = create_app()

