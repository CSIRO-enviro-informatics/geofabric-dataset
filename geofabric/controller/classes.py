# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from flask import Blueprint, Response, request
import geofabric._config as config
from geofabric.model.ldapi import GEOFRegisterRenderer
from geofabric.model.ldapi.catchment import CatchmentRenderer
from geofabric.model.ldapi.riverregion import RiverRegionRenderer

classes = Blueprint('classes', __name__)


@classes.route('/catchment/')
def catchments():
    renderer = GEOFRegisterRenderer(request, config.URI_CATCHMENT_INSTANCE_BASE,
                                    "Catchment Register",
                                    "Register of all GeoFabric Catchments",
                                    [config.URI_CATCHMENT_CLASS],
                                    config.CATCHMENT_COUNT,
                                    super_register=config.URI_BASE)
    return renderer.render()

@classes.route('/riverregion/')
def river_regions():
    renderer = GEOFRegisterRenderer(request, config.URI_RIVER_REGION_INSTANCE_BASE,
                                    "River Region Register",
                                    "Register of all GeoFabric River Regions",
                                    [config.URI_RIVER_REGION_CLASS],
                                    config.CATCHMENT_COUNT,
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
