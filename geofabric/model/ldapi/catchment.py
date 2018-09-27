# -*- coding: utf-8 -*-
from geofabric.model.catchment import Catchment
from geofabric.model.ldapi import GEOFClassRenderer, SchemaOrgRendererMixin
import geofabric._config as config


class CatchmentRenderer(SchemaOrgRendererMixin, GEOFClassRenderer):
    GEOF_CLASS = config.URI_CATCHMENT_CLASS

    def __init__(self, request, identifier, views, default_view_token, *args, **kwargs):
        _views = views or {}
        _uri = ''.join([config.URI_CATCHMENT_INSTANCE_BASE, identifier])
        kwargs.setdefault('geof_template', 'class_catchment.html')
        kwargs.setdefault('hyf_template', 'class_catchment.html')
        super(CatchmentRenderer, self).__init__(request, _uri, _views, default_view_token, *args, **kwargs)
        self.identifier = identifier
        self.instance = Catchment(self.identifier)


