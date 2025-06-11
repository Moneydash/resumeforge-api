from flask import Blueprint
from api.controller.galaxy.andromeda import generate_pdf as generate_andromeda_pdf
from api.controller.galaxy.cigar import generate_pdf as generate_cigar_pdf
from api.controller.galaxy.comet import generate_pdf as generate_comet_pdf
from api.controller.galaxy.milky_way import generate_pdf as generate_milky_way_pdf

generate_bp = Blueprint('generate', __name__)

@generate_bp.route("/andromeda/generate", methods=["POST"])
def andromeda_route():
    return generate_andromeda_pdf()

@generate_bp.route("/cigar/generate", methods=["POST"])
def cigar_route():
    return generate_cigar_pdf()

@generate_bp.route("/comet/generate", methods=["POST"])
def comet_route():
    return generate_comet_pdf()

@generate_bp.route("/milky_way/generate", methods=["POST"])
def milky_way_route():
    return generate_milky_way_pdf()