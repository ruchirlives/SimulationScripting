from flask import Blueprint, jsonify, request

from .openai_utils import summarize
from .astra_utils import update_record

openai_bp = Blueprint('openai', __name__, url_prefix='/openai')
astra_bp = Blueprint('astra', __name__, url_prefix='/astra')


@openai_bp.route('/summarize', methods=['POST'])
def openai_summarize():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    summary = summarize(text)
    return jsonify({'summary': summary})


@astra_bp.route('/update', methods=['POST'])
def astra_update():
    data = request.get_json(silent=True) or {}
    result = update_record(data)
    return jsonify(result)

