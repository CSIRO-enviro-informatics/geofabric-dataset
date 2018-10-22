# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from flask import Blueprint, Response, request
import geofabric._config as config
from geofabric.model.awradrainagedivision import AWRADrainageDivision
from geofabric.model.catchment import Catchment
from geofabric.model.ldapi import GEOFRegisterRenderer
from geofabric.model.ldapi.awradrainagedivision import \
    AWRADrainageDivisionRenderer
from geofabric.model.ldapi.catchment import CatchmentRenderer
from geofabric.model.ldapi.riverregion import RiverRegionRenderer
from geofabric.model.riverregion import RiverRegion

classes = Blueprint('classes', __name__)


@classes.route('/catchment/')
def catchments():
    renderer = GEOFRegisterRenderer(request, config.URI_CATCHMENT_INSTANCE_BASE,
                                    "Catchment Register",
                                    "Register of all GeoFabric Catchments",
                                    [config.URI_CATCHMENT_CLASS],
                                    config.CATCHMENT_COUNT,
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
        config.CATCHMENT_COUNT,
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
        config.CATCHMENT_COUNT,
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
    r = CatchmentRenderer(request, catchment_id, None)
    return r.render()


@classes.route('/riverregion/<string:rr_id>')
def river_region(rr_id):
    """
    A single River Region

    :param rr_id:
    :return: LDAPI views of a single River Region
    """
    r = RiverRegionRenderer(request, rr_id, None)
    return r.render()


@classes.route('/drainagedivision/<string:dd_id>')
def drainage_division(dd_id):
    """
    A single instance of AWRA Drainage Division

    :param dd_id:
    :return: LDAPI views of a single AWRA Drainage Division
    """
    r = AWRADrainageDivisionRenderer(request, dd_id, None)
    return r.render()
