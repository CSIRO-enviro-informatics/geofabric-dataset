# -*- coding: utf-8 -*-
"""
This file contains all the HTTP routes for classes from the Geofabric model, such as Catchment and the
Catchment Register
"""
from flask import Blueprint, request
import _config as config
from model.ldapi import GNAFRegisterRenderer
from model.ldapi.address import AddressRenderer
from model.ldapi.addressSite import AddressSiteRenderer
from model.ldapi.locality import LocalityRenderer
from model.ldapi.streetLocality import StreetLocalityRenderer

classes = Blueprint('classes', __name__)


@classes.route('/address/')
def addresses():
    renderer = GNAFRegisterRenderer(request, config.URI_ADDRESS_INSTANCE_BASE,
                                    "Address Register",
                                    "Register of all GNAF Addresses",
                                    [config.URI_ADDRESS_CLASS],
                                    config.ADDRESS_COUNT,
                                    super_register=config.URI_BASE)
    return renderer.render()


@classes.route('/address/<string:address_id>')
def address(address_id):
    """
    A single Address
    :param address_id:
    :return: LDAPI views of a single Address
    """
    r = AddressRenderer(request, address_id, None, 'gnaf')
return r.render()