# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from flask import Blueprint, request, abort
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

classes = Blueprint('classes', __name__)

CONTRACTED_CATCHMENT_COUNT = 30461
CATCHMENT_COUNT = 1474286
RIVER_REGION_COUNT = 218
DRAINAGE_DIVISION_COUNT = 13

USE_CONTRACTED_CATCHMENTS = True


@classes.route('/catchment/')
def catchments():
    if USE_CONTRACTED_CATCHMENTS:
        renderer = GEOFRegisterRenderer(request, config.URI_CATCHMENT_INSTANCE_BASE,
                                        "Catchment Register",
                                        "Register of all Geofabric Contracted Catchments",
                                        [config.URI_CATCHMENT_CLASS],
                                        CONTRACTED_CATCHMENT_COUNT,
                                        ContractedCatchment,
                                        super_register=config.URI_BASE)
    else:
        renderer = GEOFRegisterRenderer(request, config.URI_CATCHMENT_INSTANCE_BASE,
                                        "Catchment Register",
                                        "Register of all Geofabric Catchments",
                                        [config.URI_CATCHMENT_CLASS],
                                        CATCHMENT_COUNT,
                                        Catchment,
                                        super_register=config.URI_BASE)
    return renderer.render()


@classes.route('/riverregion/')
def river_regions():
    renderer = GEOFRegisterRenderer(
        request, config.URI_RIVER_REGION_INSTANCE_BASE,
        "River Region Register",
        "Register of all GeoFabric River Regions",
        [config.URI_RIVER_REGION_CLASS],
        RIVER_REGION_COUNT,
        RiverRegion,
        super_register=config.URI_BASE)
    return renderer.render()


@classes.route('/drainagedivision/')
def drainage_divisions():
    renderer = GEOFRegisterRenderer(
        request, config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE,
        "AWRA Drainage Division Register",
        "Register of all AWRA Drainage Divisions",
        [config.URI_AWRA_DRAINAGE_DIVISION_CLASS],
        DRAINAGE_DIVISION_COUNT,
        AWRADrainageDivision,
        super_register=config.URI_BASE)
    return renderer.render()


@classes.route('/catchment/<string:catchment_id>')
def catchment(catchment_id):
    """
    A single Catchment

    :param catchment_id:
    :return: LDAPI views of a single Catchment
    """
    try:
        if USE_CONTRACTED_CATCHMENTS:
            r = ContractedCatchmentRenderer(request, catchment_id, None)
        else:
            r = CatchmentRenderer(request, catchment_id, None)
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
