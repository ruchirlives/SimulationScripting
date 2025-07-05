from flask import Flask
import os

from .routes import openai_bp, astra_bp, sim_bp, root_bp


def create_app() -> Flask:
    """Application factory for creating the Flask app."""
    # Get the path to the project root (parent of app directory)
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    
    app = Flask(__name__, template_folder=template_dir)
    
    # Enable debug mode and configure app
    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'
    
    app.register_blueprint(root_bp)
    app.register_blueprint(openai_bp)
    app.register_blueprint(astra_bp)
    app.register_blueprint(sim_bp)
    return app


# Create a default app for simple use cases
app = create_app()

