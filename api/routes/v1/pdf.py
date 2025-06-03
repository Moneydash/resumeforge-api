from flask import Blueprint
from api.controller.v1.andromeda import generate_pdf as generate_andromeda_pdf, export_pdf as export_andromeda_pdf
from api.controller.v1.cigar import generate_pdf as generate_cigar_pdf, export_pdf as export_cigar_pdf
from api.controller.v1.comet import generate_pdf as generate_comet_pdf, export_pdf as export_comet_pdf
from api.controller.v1.milky_way import generate_pdf as generate_milky_way_pdf, export_pdf as export_milky_way_pdf

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

@generate_bp.route("/andromeda/export", methods=["POST"])
def andromeda_export_route():
    return export_andromeda_pdf()

@generate_bp.route("/cigar/export", methods=["POST"])
def cigar_export_route():
    return export_cigar_pdf()

@generate_bp.route("/comet/export", methods=["POST"])
def comet_export_route():
    return export_comet_pdf()

@generate_bp.route("/milky_way/export", methods=["POST"])
def milky_way_export_route():
    return export_milky_way_pdf()