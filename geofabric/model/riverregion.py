# -*- coding: utf-8 -*-
#
from _elementtree import ParseError
from decimal import Decimal
from urllib.parse import urlencode

import rdflib
from urllib.request import Request, urlopen
from flask import render_template, url_for
from rdflib import URIRef, Literal, BNode
from rdflib.namespace import DC, DCTERMS, XSD, RDFS
from lxml import etree
from geofabric import _config as config
from geofabric.helpers import gml_extract_geom_to_geojson, \
    wfs_extract_features_as_geojson, \
    wfs_extract_features_as_profile, gml_extract_geom_to_geosparql, \
    GEO_hasGeometry, RDF_a, \
    HYF_HY_CatchmentRealization, HYF_realizedCatchment, HYF_lowerCatchment, \
    HYF_catchmentRealization, HYF_HY_Catchment, HYF_HY_HydroFeature, \
    calculate_bbox, HYF_HY_CatchmentAggregate, NotFoundError, \
    GEO, GEOF, degrees_area_to_m2, QUDTS, GEOX, UNIT, HYF, DATA, EPSG, \
    GEO_hasDefaultGeometry, LOCI
from geofabric.model import GFModel
from functools import lru_cache
from datetime import datetime


# TODO: look into using cachetools.LFUCache or TTLCache
@lru_cache(maxsize=128)
def retrieve_river_region(identifier):
    assert isinstance(identifier, int)
    rr_wfs_uri = config.GF_OWS_ENDPOINT + '?' + \
                 urlencode({
                     'request': 'GetFeature',
                     'service': 'WFS',
                     'version': '2.0.0',
                     'typeName': 'ahgf_hrr:RiverRegion',
                     'Filter': '<Filter><PropertyIsEqualTo>' \
                               '<PropertyName>ahgf_hrr:hydroid</PropertyName>' \
                               '<Literal>{:d}</Literal>' \
                               '</PropertyIsEqualTo></Filter>'.format(identifier)
                 })

    try:
        r = Request(rr_wfs_uri, method="GET")
        with urlopen(r) as response:  # type: http.client.HTTPResponse
            if not (299 >= response.status >= 200):
                raise RuntimeError("Cannot get River Region from WFS backend.")
            try:
                tree = etree.parse(response)
            except ParseError as e:
                print(e)
                print(response.read())
                return []
    except Exception as e:
        raise e
    return tree

ns = {
    'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_hrr',
    'wfs': 'http://www.opengis.net/wfs/2.0',
    'gml': "http://www.opengis.net/gml/3.2"
}
# NOTE, RiverRegion has no sourceid!
rr_tag_map = {
    "{{{}}}hydroid".format(ns['x']): 'hydroid',
    "{{{}}}wkb_geometry".format(ns['x']): 'wkb_geometry',
    "{{{}}}ahgfftype".format(ns['x']): 'ahgfftype',
    "{{{}}}division".format(ns['x']): 'division',
    "{{{}}}rivregnum".format(ns['x']): 'rivregnum',
    "{{{}}}rivregname".format(ns['x']): 'rivregname',
    "{{{}}}srcfcname".format(ns['x']): 'srcfcname',
    "{{{}}}srcfctype".format(ns['x']): 'srcfctype',
    "{{{}}}featrel".format(ns['x']): 'featrel',
    "{{{}}}fsource".format(ns['x']): 'fsource',
    "{{{}}}attrrel".format(ns['x']): 'attrrel',
    "{{{}}}attrsource".format(ns['x']): 'attrsource',
    "{{{}}}planacc".format(ns['x']): 'planacc',
    "{{{}}}albersarea".format(ns['x']): 'albersarea',
    "{{{}}}shape_length".format(ns['x']): 'shape_length',
    "{{{}}}shape_area".format(ns['x']): 'shape_area',
    "{{{}}}shape".format(ns['x']): 'shape',
}

# used to map RRs to DDs via a name lookup using the RR WFS division property
DRAINAGE_DIVISIONS = {
    'Carpentaria Coast':            URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400203'),
    'Pilbara-Gascoyne':             URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400204'),
    'Lake Eyre Basin':              URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400205'),
    'Murray-Darling Basin':         URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400206'),
    'North East Coast':             URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400207'),
    'North Western Plateau':        URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400208'),
    'South Australian Gulf':        URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400209'),
    'South East Coast (Victoria)':  URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400210'),
    'South West Coast':             URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400211'),
    'South Western Plateau':        URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400212'),
    'Tasmania':                     URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400213'),
    'Tanami-Timor Sea Coast':       URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400214'),
    'South East Coast (NSW)':       URIRef(config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE + '9400215'),
}


def river_region_geofabric_converter(model, wfs_features):
    # This is for the "geofabric" Profile. It turns a WFS feature into a valid
    # geofabric-ont feature, according to geofabric ontology
    if len(wfs_features) < 1:
        return None

    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    triples = set()

    for hydroid, rr_element in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(
            "".join([config.URI_RIVER_REGION_INSTANCE_BASE, str(hydroid)])
        )
        triples.add((feature_uri, RDF_a, GEOF.RiverRegion))

        for c in rr_element.iterchildren():  # type: etree._Element
            var = c.tag.replace('{{{}}}'.format(ns['x']), '')

            # common Geofabric properties
            if var == 'shape_area':
                A = BNode()
                triples.add((A, QUDTS.numericValue, Literal(c.text, datatype=XSD.float)))
                triples.add((A, QUDTS.unit, UNIT.DEG2))
                triples.add((feature_uri, GEOF.shapeArea, A))
                try:
                    A = BNode()
                    degree_area = float(c.text)
                    # Add in the extra converted m2 area
                    bbox = model.get_bbox(pad=12)
                    centrepointX = (bbox[0] + ((bbox[2] - bbox[0]) / 2))
                    centrepointY = (bbox[1] + ((bbox[3] - bbox[1]) / 2))
                    m2_area = degrees_area_to_m2(degree_area, centrepointY)
                    triples.add((A, DATA.value, Literal(str(Decimal(str(m2_area))), datatype=XSD.decimal)))
                    triples.add((A, GEOX.inCRS, EPSG['4938']))
                    triples.add((feature_uri, GEOX.hasAreaM2, A))
                except ValueError:
                    pass
            elif var == 'albersarea':
                A = BNode()
                triples.add((A, DATA.value, Literal(str(Decimal(str(c.text))), datatype=XSD.decimal)))
                triples.add((A, GEOX.inCRS, EPSG['3577']))
                triples.add((feature_uri, GEOX.hasAreaM2, A))
            elif var == 'shape_length':
                L = BNode()
                triples.add((L, QUDTS.numericValue,
                             Literal(c.text, datatype=XSD.float)))
                triples.add((L, QUDTS.unit, UNIT.DEG))
                triples.add((feature_uri, GEOF.perimeterLength, L))  # URIRef('http://dbpedia.org/property/length')
            elif var == 'shape':
                geom_service_uri = URIRef("".join([config.GEOMETRY_SERVICE_URI,
                                                   "geofabric2_1_1_riverregion/",
                                                   str(hydroid)]))
                triples.add((feature_uri, GEO_hasGeometry, geom_service_uri))
                triples.add((feature_uri, GEO_hasDefaultGeometry, geom_service_uri))
                # try:
                #    _triples, geometry = gml_extract_geom_to_geosparql(c)
                #    for (s, p, o) in iter(_triples):
                #        triples.add((s, p, o))
                # except KeyError:
                #    val = c.text
                #    geometry = Literal(val)
                # triples.add((feature_uri, GEO_hasGeometry, geometry))
                # Uncomment the above to re-enable in-line geometry
            elif var == 'attrsource':
                triples.add((feature_uri, DC.source, Literal(c.text)))

            # River Region properties
            elif var == 'fsource':
                triples.add((feature_uri, DC.source, Literal(str(c.text).title())))
            elif var == 'rivregname':
                triples.add((feature_uri, DCTERMS.title, Literal(str(c.text).title(), lang='en')))
            elif var == 'division':
                dd = DRAINAGE_DIVISIONS.get(str(c.text))
                if dd is not None:
                    triples.add((feature_uri, GEO.sfWithin, dd))

        # the RR register
        #triples.add((feature_uri, URIRef('http://purl.org/linked-data/registry#register'), URIRef(config.URI_RIVER_REGION_INSTANCE_BASE)))
        triples.add((feature_uri, LOCI.isMemberOf, URIRef(config.URI_RIVER_REGION_INSTANCE_BASE)))
        triples.add((URIRef(config.URI_RIVER_REGION_INSTANCE_BASE), RDFS.member, feature_uri))
    return triples, None


def river_region_hyfeatures_converter(wfs_features):
    # This is for the "hyfeatures" Profile. It turns a WFS feature into a valid
    # hyfeatures feature, according to hyfeatures ontology
    if len(wfs_features) < 1:
        return None
    to_converter = {
        #'wkb_geometry': gml_extract_geom_to_geosparql,
        #'shape': gml_extract_geom_to_geosparql,
        'shape': lambda i, x: (set(), URIRef("".join([config.GEOMETRY_SERVICE_URI, "geofabric2_1_1_riverregion/", str(i)]))),
    }
    to_float = ('shape_length', 'shape_area', 'albersarea')
    to_int = ('hydroid', 'ahgfftype')
    to_datetime = ('attrrel', 'featrel')
    is_geom = ('wkb_geometry', 'shape')
    predicate_map = {
        #'nextdownid': HYF_lowerCatchment
    }
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]
    triples = set()
    feature_nodes = []
    for hydroid, rr_element in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(
            "".join([config.URI_RIVER_REGION_INSTANCE_BASE,
            str(hydroid)]))
        triples.add((feature_uri, RDF_a, HYF_HY_HydroFeature))
        triples.add((feature_uri, RDF_a, HYF_HY_CatchmentAggregate))
        for c in rr_element.iterchildren():  # type: etree._Element
            try:
                var = rr_tag_map[c.tag]
            except KeyError:
                continue
            try:
                conv_func = to_converter[var]
                _triples, val = conv_func(hydroid, c)
                for (s, p, o) in iter(_triples):
                    triples.add((s, p, o))
            except KeyError:
                val = c.text
            if var in to_datetime:
                if val.endswith('Z'):
                    val = val[:-1]
                try:
                    val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
                    val = Literal(val)
                except ValueError:
                    val = "Invalid time format"
            elif var in to_float:
                val = Literal(float(val))
            elif var in to_int:
                val = Literal(int(val))
            else:
                if not isinstance(val, (URIRef, Literal, BNode)):
                    val = Literal(str(val))
            if var in is_geom:
                realization = BNode()
                triples.add((realization, RDF_a, HYF_HY_CatchmentRealization))
                triples.add((realization, GEO_hasGeometry, val))
                triples.add((realization, HYF_realizedCatchment, feature_uri))
                triples.add((feature_uri, HYF_catchmentRealization, realization))
                #triples.add((feature_uri, GEO_hasDefaultGeometry, var))
            elif var in predicate_map.keys():
                predicate = predicate_map[var]
                triples.add((feature_uri, predicate, val))
            else:
                dummy_prop = URIRef("{}/{}".format(ns['x'], var))
                triples.add((feature_uri, dummy_prop, val))
        features_list.append(feature_uri)
        triples.add((feature_uri, LOCI.isMemberOf, URIRef(config.URI_RIVER_REGION_INSTANCE_BASE)))
        triples.add((URIRef(config.URI_RIVER_REGION_INSTANCE_BASE), RDFS.member, feature_uri))
    return triples, feature_nodes


def river_region_features_geojson_converter(wfs_features):
    # This is for the "geojson" Profile. It turns a WFS feature into a valid
    # geojson object, according to GeoJSON spec (no ontology)
    if len(wfs_features) < 1:
        return None
    to_converter = {
        'wkb_geometry': gml_extract_geom_to_geojson,
        'shape': gml_extract_geom_to_geojson,
    }
    to_float = ('shape_length', 'shape_area', 'albersarea')
    to_int = ('hydroid', 'ahgfftype')
    # to_datetime = ('attrrel', 'featrel')
    to_datetime = []
    is_geom = ('wkb_geometry', 'shape')
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    for hydroid, rr_element in features_source:  # type: int, etree._Element
        rr_dict = {"type": "Feature", "id": hydroid, "geometry": {}, "properties": {}}

        for r in rr_element.iterchildren():  # type: etree._Element
            try:
                var = rr_tag_map[r.tag]
            except KeyError:
                continue
            try:
                conv_func = to_converter[var]
                val = conv_func(r)
            except KeyError:
                val = r.text
            if var in to_datetime:
                if val.endswith('Z'):
                    val = val[:-1]
                try:
                    val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    val = "Invalid time format"
            elif var in to_float:
                val = float(val)
            elif var in to_int:
                val = int(val)
            if var in is_geom:
                rr_dict['geometry'] = val
            else:
                rr_dict['properties'][var] = val
        features_list.append(rr_dict)
    return features_list


def extract_river_regions_as_geojson(tree):
    geojson_features = wfs_extract_features_as_geojson(tree, ns['x'], "RiverRegion", river_region_features_geojson_converter)
    return geojson_features


def extract_river_regions_as_geofabric(tree, model=None):
    g = rdflib.Graph()
    g.bind('geo', GEO)
    g.bind('geox', GEOX)
    g.bind('geof', GEOF)
    g.bind('data', DATA)
    g.bind('qudt', QUDTS)
    g.bind('unit', UNIT)
    g.bind('loci', LOCI)
    g.bind('dc', DC)
    triples, features = wfs_extract_features_as_profile(
        tree,
        ns['x'],
        "RiverRegion",
        river_region_geofabric_converter,
        model=model
    )
    for (s, p, o) in iter(triples):
        g.add((s, p, o))
    return g


def extract_river_regions_as_hyfeatures(tree, model=None):
    g = rdflib.Graph()
    g.bind('geo', GEO)
    g.bind('geox', GEOX)
    g.bind('hyf', HYF)
    g.bind('qudt', QUDTS)
    g.bind('unit', UNIT)
    g.bind('data', DATA)
    g.bind('loci', LOCI)
    g.bind('dc', DC)
    triples, features = wfs_extract_features_as_profile(
        tree,
        ns['x'],
        "RiverRegion",
        river_region_hyfeatures_converter,
        model=model
    )
    for (s, p, o) in iter(triples):
        g.add((s, p, o))
    return g


class RiverRegion(GFModel):
    @classmethod
    def make_instance_label(cls, instance_id):
        return "River Region ID: {}".format(str(instance_id))

    @classmethod
    def make_canonical_uri(cls, instance_id):
        return "".join([config.URI_RIVER_REGION_INSTANCE_BASE, instance_id])

    @classmethod
    def make_local_url(cls, instance_id):
        return url_for('classes.river_region', rr_id=instance_id)

    @classmethod
    def get_index(cls, page, per_page):
        per_page = max(int(per_page), 1)
        offset = (max(int(page), 1)-1)*per_page
        rr_wfs_uri = config.GF_OWS_ENDPOINT + \
                     '?service=wfs' \
                     '&version=2.0.0' \
                     '&request=GetFeature' \
                     '&typeName=ahgf_hrr:RiverRegion' \
                     '&propertyName=hydroid' \
                     '&sortBy=hydroid' \
                     '&count={}&startIndex={}'.format(per_page, offset)
        try:
            r = Request(rr_wfs_uri, method="GET")
            with urlopen(r) as response:  # type: http.client.HTTPResponse
                if not (299 >= response.status >= 200):
                    raise RuntimeError("Cannot get River Region index from WFS backend.")
                try:
                    tree = etree.parse(response)
                except ParseError as e:
                    print(e)
                    print(response.read())
                    return []
        except Exception as e:
            raise e
        items = tree.xpath('//x:hydroid/text()', namespaces={
            'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_hrr'})
        return items

    def __init__(self, identifier):
        super(RiverRegion, self).__init__()
        identifier = int(identifier)
        rr_xml_tree = retrieve_river_region(identifier)
        self.xml_tree = rr_xml_tree
        rregions = extract_river_regions_as_geojson(rr_xml_tree)
        if rregions['features'] is None or len(rregions['features']) < 1:
            raise NotFoundError()
        rregion = rregions['features'][0]
        self.geometry = rregion['geometry']
        for k, v in rregion['properties'].items():
            setattr(self, k, v)

    def get_bbox(self, pad=0):
        coords = self.geometry['coordinates']
        json_bbox = calculate_bbox(coords, pad=pad)
        (n, s, e, w) = json_bbox
        return (w,s,e,n) # (minx, miny, maxx, maxy)

    def to_hyfeatures_graph(self):
        g = extract_river_regions_as_hyfeatures(self.xml_tree)
        return g

    def to_geofabric_graph(self):
        g = extract_river_regions_as_geofabric(self.xml_tree, model=self)
        return g

    def export_html(self, view='geofabric'):
        bbox = self.get_bbox(pad=12)
        bbox_string = ",".join(str(i) for i in bbox)
        centrepoint = [
            bbox[0] + ((bbox[2] - bbox[0]) / 2),
            bbox[1] + ((bbox[3] - bbox[1]) / 2)
        ]
        hydroid = self.hydroid
        wms_url = config.GF_OWS_ENDPOINT +\
                  "?service=wms&version=2.0.0&request=GetMap" \
                  "&width=800&height=600" \
                  "&format=text/html;+subtype=openlayers" \
                  "&CRS=EPSG:4326" \
                  "&layers=osm_au,ahgf_hrr:RiverRegion" \
                  "&style=ahgfcatchment" \
                  "&bbox=" + bbox_string +\
                  "&CQL_FILTER=INCLUDE;hydroid="+str(hydroid)
        m2_area = degrees_area_to_m2(self.shape_area, centrepoint[1])
        if view == 'geofabric':
            view_html = render_template(
                'class_riverregion_geof.html',
                bbox=bbox,
                centrepoint=centrepoint,
                wms_url=wms_url,
                hydroid=hydroid,
                division=self.division,
                river_reg_name=self.rivregname,
                shape_length=self.shape_length,
                shape_area=self.shape_area,
                albers_area=self.albersarea,
                m2_area=m2_area
            )
        elif view == "hyfeatures":
            view_html = render_template(
                'class_riverregion_hyf.html',
                bbox=bbox,
                centrepoint=centrepoint,
                wms_url=wms_url,
                hydroid=hydroid,
                division=self.division,
                river_reg_name=self.rivregname,
                shape_length=self.shape_length,
                shape_area=self.shape_area,
                albers_area=self.albersarea,
                m2_area=m2_area
            )
        else:
            return NotImplementedError("HTML representation of View '{}' is not implemented.".format(view))

        return view_html
