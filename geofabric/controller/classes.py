# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from flask import Blueprint, request, abort
from flask_cors import CORS
import geofabric._config as config
from geofabric.model.awradrainagedivision import AWRADrainageDivision
from geofabric.model.catchment import Catchment
from geofabric.model.contractedcatchment import ContractedCatchment
from geofabric.view.ldapi import GEOFRegisterRenderer
from geofabric.view.ldapi.awradrainagedivision import \
    AWRADrainageDivisionRenderer
from geofabric.view.ldapi.catchment import CatchmentRenderer
from geofabric.view.ldapi.contractedcatchment import ContractedCatchmentRenderer
from geofabric.view.ldapi.riverregion import RiverRegionRenderer
from geofabric.model.riverregion import RiverRegion
from geofabric.helpers import NotFoundError
from pyldapi import RegisterOfRegistersRenderer

classes = Blueprint('classes', __name__)
CORS(classes, automatic_options=True)
CONTRACTED_CATCHMENT_COUNT = 30461
CATCHMENT_COUNT = 1474286
RIVER_REGION_COUNT = 218
DRAINAGE_DIVISION_COUNT = 13

USE_CONTRACTED_CATCHMENTS = True


@classes.route('/reg/')

def reg():
    return RegisterOfRegistersRenderer(
        request,
        'http://linked.data.gov.au/dataset/geofabric/reg/',
        'Register of Registers',
        'The master register of this API',
        config.APP_DIR + '/rofr.ttl'
    ).render()


@classes.route('/contractedcatchment/')
def contracted_catchments():
    if USE_CONTRACTED_CATCHMENTS:
        renderer = GEOFRegisterRenderer(request, config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE,
                                        "Catchment Register",
                                        "Register of all Geofabric Contracted Catchments",
                                        ['http://linked.data.gov.au/def/geofabric#ContractedCatchment'],
                                        CONTRACTED_CATCHMENT_COUNT,
                                        ContractedCatchment,
                                        super_register=config.DATA_URI_PREFIX)
    else:
        renderer = GEOFRegisterRenderer(request, config.URI_CATCHMENT_INSTANCE_BASE,
                                        "Catchment Register",
                                        "Register of all Geofabric Catchments",
                                        ['http://linked.data.gov.au/def/geofabric#Catchment'],
                                        CATCHMENT_COUNT,
                                        Catchment,
                                        super_register=config.DATA_URI_PREFIX)
    return renderer.render()


@classes.route('/riverregion/')
def river_regions():
    renderer = GEOFRegisterRenderer(
        request, config.URI_RIVER_REGION_INSTANCE_BASE,
        "River Region Register",
        "Register of all GeoFabric River Regions",
        ['http://linked.data.gov.au/def/geofabric#RiverRegion'],
        RIVER_REGION_COUNT,
        RiverRegion,
        super_register=config.DATA_URI_PREFIX)
    return renderer.render()


@classes.route('/drainagedivision/')
def drainage_divisions():
    renderer = GEOFRegisterRenderer(
        request, config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE,
        "AWRA Drainage Division Register",
        "Register of all AWRA Drainage Divisions",
        ['http://linked.data.gov.au/def/geofabric#DrainageDivision'],
        DRAINAGE_DIVISION_COUNT,
        AWRADrainageDivision,
        super_register=config.DATA_URI_PREFIX)
    return renderer.render()


@classes.route('/contractedcatchment/<string:contractedcatchment_id>')
def contracted_catchment(contractedcatchment_id):
    """
    A single Catchment

    :param contractedcatchment_id:
    :return: LDAPI views of a single Catchment
    """
    try:
        if USE_CONTRACTED_CATCHMENTS:
            r = ContractedCatchmentRenderer(request, contractedcatchment_id, None)
        else:
            r = CatchmentRenderer(request, contractedcatchment_id, None)
    except NotFoundError:
        return abort(404)
    return r.render()


@classes.route('/riverregion/<string:rr_id>')
def river_region(rr_id):
    """
    A single River Region

    :param rr_id:
    :return: LDAPI views of a single River Region
    """
    try:
        r = RiverRegionRenderer(request, rr_id, None)
    except NotFoundError:
        return abort(404)
    return r.render()


@classes.route('/drainagedivision/<string:dd_id>')
def drainage_division(dd_id):
    """
    A single instance of AWRA Drainage Division

    :param dd_id:
    :return: LDAPI views of a single AWRA Drainage Division
    """
    try:
        r = AWRADrainageDivisionRenderer(request, dd_id, None)
    except NotFoundError:
        return abort(404)
    return r.render()
