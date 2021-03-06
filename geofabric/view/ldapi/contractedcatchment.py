# -*- coding: utf-8 -*-
from geofabric.model.contractedcatchment import ContractedCatchment
from geofabric.view.ldapi import GEOFClassRenderer, SchemaOrgRendererMixin
import geofabric._config as config


class ContractedCatchmentRenderer(SchemaOrgRendererMixin, GEOFClassRenderer):
    GEOF_CLASS = config.URI_CATCHMENT_CLASS

    def __init__(self, request, identifier, views, *args,
                 default_view_token=None, **kwargs):
        _views = views or {}
        _uri = ''.join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, identifier])
        kwargs.setdefault('geof_template', 'class_contracted_catchment.html')
        kwargs.setdefault('hyf_template', 'class_contracted_catchment.html')
        super(ContractedCatchmentRenderer, self).__init__(
            request, _uri, _views, *args,
            default_view_token=default_view_token, **kwargs)
        self.identifier = identifier
        if self.view == "alternates":
            self.instance = None
        else:
            self.instance = ContractedCatchment(self.identifier)
