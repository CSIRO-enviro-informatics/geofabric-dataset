# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from io import BytesIO
import requests
from flask import Blueprint, Response, request
from lxml import etree
import geofabric._config as config
from geofabric.model.catchment import Catchment
from geofabric.model.ldapi import GEOFRegisterRenderer
from geofabric.model.ldapi.catchment import CatchmentRenderer

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


@classes.route('/catchment/<string:catchment_id>')
def catchment(catchment_id):
    """
    A single Catchment

    :param catchment_id:
    :return: LDAPI views of a single Catchment
    """
    r = CatchmentRenderer(request, catchment_id, None, 'geofabric')
    return r.render()



