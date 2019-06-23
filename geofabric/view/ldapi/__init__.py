# -*- coding: utf-8 -*-

from flask import render_template, Response
import pyldapi
from geofabric.model import GFModel

HYFView = pyldapi.View(
    'hyfeatures',
    "Features modelled using the HY_Features ontology",
    [
       "text/html", "text/turtle", "application/rdf+xml", "application/ld+json", "application/n-triples"
    ],
    "text/turtle", namespace="https://www.opengis.net/def/appschema/hy_features/hyf/")

GEOFView = pyldapi.View(
    'geofabric',
    "A customised geofabric view based on HY_Features",
    [
        "text/html", "text/turtle", "application/rdf+xml", "application/ld+json",
        "application/n-triples", "application/gml+xml"
    ],
    "text/html", namespace="http://reference.data.gov.au/def/ont/geofabric/")

SchemaOrgView = pyldapi.View(
    'schemaorg',
    "An initiative by Bing, Google and Yahoo! to create and support a common set of schemas "
    "for structured data markup on web pages. It is serialised in JSON-LD",
    ["application/ld+json"],
    "application/ld+json", namespace="http://schema.org")


def render_error(request, e):
    try:
        import traceback
        traceback.print_tb(e.__traceback__)
    except Exception:
        pass
    if isinstance(e, pyldapi.ViewsFormatsException):
        error_type = 'Internal View Format Error'
        error_code = 406
        error_message = e.args[0] or "No message"
    elif isinstance(e, NotImplementedError):
        error_type = 'Not Implemented'
        error_code = 406
        error_message = e.args[0] or "No message"
    elif isinstance(e, RuntimeError):
        error_type = 'Server Error'
        error_code = 500
        error_message = e.args[0] or "No message"
    else:
        error_type = 'Unknown'
        error_code = 500
        error_message = "An Unknown Server Error Occurred."

    resp_text = '''<?xml version="1.0"?>
    <error>
      <errorType>{}</errorType>
      <errorCode>{}</errorCode>
      <errorMessage>{}</errorMessage>
    </error>
    '''.format(error_type, error_code, error_message)
    return Response(resp_text, status=error_code, mimetype='application/xml')


class GEOFClassRenderer(pyldapi.Renderer):
    GEOF_CLASS = None

    def __init__(self, request, uri, views, *args,
                 default_view_token=None, geof_template=None, hyf_template=None, **kwargs):
        kwargs.setdefault('alternates_template', 'alternates_view.html')
        _views = views or {}
        self._add_default_geof_views(_views)
        if default_view_token is None:
            default_view_token = 'hyfeatures'
        super(GEOFClassRenderer, self).__init__(request, uri, _views, default_view_token, *args, **kwargs)
        try:
            vf_error = self.vf_error
            if vf_error:
                if not hasattr(self, 'view') or not self.view:
                    self.view = 'geofabric'
                if not hasattr(self, 'format') or not self.format:
                    self.format = 'text/html'
        except AttributeError:
            pass
        self.geof_template = geof_template
        self.hyf_template = hyf_template
        self.identifier = None  # inheriting classes will need to add the Identifier themselves.
        self.instance = None  # inheriting classes will need to add the Instance themselves.

    def render(self):
        response = super(GEOFClassRenderer, self).render()
        if response is not None:
            return response
        try:
            if self.view == 'geofabric':
                return self._render_geof_view()
            elif self.view == 'hyfeatures':
                return self._render_hyf_view()
            else:
                fn = getattr(self, '_render_{}_view'.format(str(self.view).lower()), None)
                if fn:
                    return fn()
                else:
                    raise RuntimeError("No renderer for view '{}'.".format(self.view))
        except Exception as e:
            from flask import request
            return render_error(request, e)

    def _render_alternates_view_html(self, template_context=None):
        if template_context is None:
            template_context = {}
        # views_formats = {k: v for k, v in self.views.items()}
        # views_formats['default'] = self.default_view_token
        _template_context = {'class_uri': self.GEOF_CLASS,
                             'instance_uri': self.uri}
        #_template_context['views_formats'] = views_formats
        _template_context.update(template_context)
        return super(GEOFClassRenderer, self).\
            _render_alternates_view_html(template_context=_template_context)

    def _render_geof_view(self):
        if self.format == 'text/html':
            return self._render_geof_view_html()
        elif self.format == 'application/gml+xml':
            return self._render_geof_view_gml()
        elif self.format in GEOFClassRenderer.RDF_MIMETYPES:
            return self._render_geof_view_rdf()
        else:
            raise RuntimeError("Cannot render 'geofabric' View with format '{}'.".format(self.format))

    def _render_geof_view_gml(self):
        gml = self.instance.as_gml()
        return Response(gml, status=200, content_type="application/gml+xml")

    def _render_geof_view_html(self):
        view_html = self.instance.export_html(view='geofabric')
        return Response(render_template(
            self.geof_template,
            view_html=view_html,
            instance_id=self.identifier,
            instance_uri=self.uri,
            ),
            headers=self.headers)

    def _render_geof_view_rdf(self):
        g = self.instance.to_geofabric_graph()
        if self.format in ['application/ld+json', 'application/json']:
            serial_format = 'json-ld'
        elif self.format in self.RDF_MIMETYPES:
            serial_format = self.format
        else:
            serial_format = 'text/turtle'
            self.format = serial_format
        return Response(g.serialize(format=serial_format), mimetype=self.format, headers=self.headers)

    def _render_hyf_view(self):
        if self.format == 'text/html':
            return self._render_hyf_view_html()
        elif self.format in GEOFClassRenderer.RDF_MIMETYPES:
            return self._render_hyf_view_rdf()
        else:
            raise RuntimeError("Cannot render 'hyfeatures' View with format '{}'.".format(self.format))

    def _render_hyf_view_rdf(self):
        g = self.instance.to_hyfeatures_graph()
        if self.format in ['application/ld+json', 'application/json']:
            serial_format = 'json-ld'
        elif self.format in self.RDF_MIMETYPES:
            serial_format = self.format
        else:
            serial_format = 'text/turtle'
            self.format = serial_format
        return Response(g.serialize(format=serial_format), mimetype=self.format, headers=self.headers)

    def _render_hyf_view_html(self):
        view_html = self.instance.export_html(view='hyfeatures')
        return Response(render_template(
            self.hyf_template,
            view_html=view_html,
            instance_id=self.identifier,
            instance_uri=self.uri,
            ),
            headers=self.headers)

    @classmethod
    def _add_default_geof_views(cls, _views):
        if 'geofabric' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                 'You must not manually add a view with token \'geofabric\' as this is auto-created.'
            )
        if 'hyfeatures' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                'You must not manually add a view with token \'hyfeatures\' as this is auto-created.'
            )
        _views['geofabric'] = GEOFView
        _views['hyfeatures'] = HYFView


class GEOFRegisterRenderer(pyldapi.RegisterRenderer):

    def __init__(self, _request, uri, label, comment, contained_item_classes,
                 register_total_count, gf_model_class, *args, views=None,
                 default_view_token=None, **kwargs):
        kwargs.setdefault('alternates_template', 'alternates_view.html')
        kwargs.setdefault('register_template', 'register.html')
        super(GEOFRegisterRenderer, self).__init__(
            _request, uri, label, comment, None, contained_item_classes,
            register_total_count, *args, views=views,
            default_view_token=default_view_token, **kwargs)
        assert issubclass(gf_model_class, GFModel)
        self.gf_model_class = gf_model_class
        try:
            vf_error = self.vf_error
            if vf_error:
                if not hasattr(self, 'view') or not self.view:
                    self.view = 'reg'
                if not hasattr(self, 'format') or not self.format:
                    self.format = 'text/html'
        except AttributeError:
            pass
        if self.view == "alternates":
            pass
        else:
            items = self.gf_model_class.get_index(self.page, self.per_page)
            for item_id in items:
                item_id = str(item_id)
                uri = ''.join([self.uri, item_id])
                label = self.gf_model_class.make_instance_label(item_id)
                self.register_items.append((uri, label, item_id))

    def render(self):
        try:
            return super(GEOFRegisterRenderer, self).render()
        except Exception as e:
            from flask import request
            return render_error(request, e)

    def _render_alternates_view_html(self, template_context=None):
        if template_context is None:
            template_context = {}

        # views_formats = {k: v for k, v in self.views.items()}
        # views_formats['default'] = self.default_view_token
        _template_context = {
            'class_uri': "http://purl.org/linked-data/registry#Register",
            'instance_uri': None
        }
        #_template_context['views_formats'] = views_formats
        _template_context.update(template_context)

        return super(GEOFRegisterRenderer, self).\
            _render_alternates_view_html(template_context=_template_context)

    def _render_reg_view_html(self, template_context=None):
        if template_context is None:
            template_context = {}
        _template_context = {'model': self.gf_model_class}
        _template_context.update(template_context)
        return super(GEOFRegisterRenderer, self). \
            _render_reg_view_html(template_context=_template_context)
        # return Response(
        #     render_template(
        #         self.register_template or 'register.html',
        #         uri=self.uri,
        #         label=self.label,
        #
        #         contained_item_classes=self.contained_item_classes,
        #         register_items=self.register_items,
        #         page=self.page,
        #         per_page=self.per_page,
        #         first_page=self.first_page,
        #         prev_page=self.prev_page,
        #         next_page=self.next_page,
        #         last_page=self.last_page,
        #         super_register=self.super_register,
        #         pagination=pagination
        #     ),
        #     headers=self.headers
        # )


class GEOFRegisterOfRegistersRenderer(pyldapi.RegisterOfRegistersRenderer):
    def _render_alternates_view_html(self, template_context=None):
        if template_context is None:
            template_context = {}

        # views_formats = {k: v for k, v in self.views.items()}
        # views_formats['default'] = self.default_view_token
        _template_context = {'class_uri': None, 'instance_uri': None}
        #_template_context['views_formats'] = views_formats
        _template_context.update(template_context)

        return super(GEOFRegisterOfRegistersRenderer, self).\
            _render_alternates_view_html(template_context=_template_context)

class SchemaOrgRendererMixin(object):

    def __init__(self, request, uri, views, *args, **kwargs):
        assert issubclass(self.__class__, GEOFClassRenderer),\
            "This Renderer Mixin only works on a GEOFClassRenderer."
        assert views is not None, "A mixin must be initialised on a class with a pre-created views dict."
        self._add_schema_org_views(views)
        super(SchemaOrgRendererMixin, self).__init__(request, uri, views, *args, **kwargs)

    @classmethod
    def _add_schema_org_views(cls, _views):
        if 'schemaorg' in _views.keys():
            raise pyldapi.ViewsFormatsException(
                'You must not manually add a view with token \'schemaorg\' as this is auto-created.'
            )
        _views['schemaorg'] = SchemaOrgView

    def _render_schemaorg_view(self):
        if self.format in ['application/ld+json', 'application/json']:
            return self._render_schemaorg_view_rdf()
        elif self.format in GEOFClassRenderer.RDF_MIMETYPES:
            raise NotImplementedError("Schema.org view only supports JSON-LD serialisation.")
        elif self.format == 'text/html':
            raise NotImplementedError("HTML format of Schema.org View is not implemented.")
        else:
            raise RuntimeError("Cannot render format {}".format(self.format))

    def _render_schemaorg_view_rdf(self):
        json_string = self.instance.export_schemaorg()
        return Response(json_string, mimetype=self.format, headers=self.headers)
