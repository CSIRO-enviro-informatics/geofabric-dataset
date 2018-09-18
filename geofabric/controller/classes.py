# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from io import BytesIO
import requests
from flask import Blueprint, Response
from lxml import etree
import geofabric._config as config

classes = Blueprint('classes', __name__)


@classes.route('/catchment/')
def catchments():
    # TODO: need something like this:
    # renderer = CatchmentRenderer(request, ...)
    # return renderer.render()
    catchments_wfs_uri = 'http://geofabric.bom.gov.au/simplefeatures/ows' \
                         '?service=wfs' \
                         '&version=2.0.0' \
                         '&request=GetFeature' \
                         '&typeName=ahgf_shcatch:AHGFCatchment' \
                         '&propertyName=hydroid' \
                         '&sortBy=hydroid' \
                         '&count=5'

    r = requests.get(catchments_wfs_uri)
    tree = etree.parse(BytesIO(r.content))
    items = tree.xpath('//x:hydroid/text()', namespaces={'x': 'http://ahgf_shcatch'})
    print(items)

    return 'done'

    # paging info:
    # https://gis.stackexchange.com/questions/167119/iterate-over-polygons-to-convert-wfs-features


@classes.route('/catchment/<string:catchment_id>')
def catchment(catchment_id):
    # TODO: need something like this:
    # r = AddressRenderer(request, catchment_id, ...).render()

    # get one catchment by featureid (not HydroID):
    catchment_wfs_uri = 'http://geofabric.bom.gov.au/simplefeatures/ows' \
                        '?request=GetFeature' \
                        '&service=WFS' \
                        '&version=2.0.0' \
                        '&typeName=ahgf_shcatch:AHGFCatchment&featureID='

    # TODO: implement a get feature by HydroID but implement a featureid --> HydroID lookup to make query sensibly fast
    # get catchment by HydroID - much, much much slower than by featureid above
    # http://geofabric.bom.gov.au/simplefeatures/ows
    # ?request=GetFeature
    # &service=WFS
    # &version=2.0.0
    # &typeName=ahgf_shcatch:AHGFCatchment
    # &Filter=<Filter><PropertyIsEqualTo><PropertyName>ahgf_shcatch:hydroid</PropertyName><Literal>7180259</Literal></PropertyIsEqualTo></Filter>

    r = requests.get(catchment_wfs_uri + catchment_id)

    return Response(r.content, mimetype='text/xml')


