from flask import Blueprint

# galaxy
from api.controller.galaxy.andromeda import generate_pdf as generate_andromeda_pdf
from api.controller.galaxy.cigar import generate_pdf as generate_cigar_pdf
from api.controller.galaxy.comet import generate_pdf as generate_comet_pdf
from api.controller.galaxy.milky_way import generate_pdf as generate_milky_way_pdf

# greek
from api.controller.greek.zeus import generate_pdf as generate_zeus_pdf
from api.controller.greek.athena import generate_pdf as generate_athena_pdf
from api.controller.greek.apollo import generate_pdf as generate_apollo_pdf
from api.controller.greek.artemis import generate_pdf as generate_artemis_pdf


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

@generate_bp.route("/zeus/generate", methods=["POST"])
def zeus_route():
    return generate_zeus_pdf()

@generate_bp.route("/athena/generate", methods=["POST"])
def athena_route():
    return generate_athena_pdf()

@generate_bp.route("/apollo/generate", methods=["POST"])
def apollo_route():
    return generate_apollo_pdf()

@generate_bp.route("/artemis/generate", methods=["POST"])
def artemis_route():
    return generate_artemis_pdf()