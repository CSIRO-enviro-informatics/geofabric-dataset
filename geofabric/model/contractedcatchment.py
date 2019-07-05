# -*- coding: utf-8 -*-
#
from decimal import Decimal

import rdflib
import requests
from flask import render_template, url_for
from lxml.etree import ParseError
from io import BytesIO
from rdflib import URIRef, Literal, BNode
from rdflib.namespace import DC, XSD
from requests import Session
from lxml import etree
from geofabric import _config as config
from geofabric.helpers import gml_extract_geom_to_geojson, \
    wfs_extract_features_as_geojson, \
    wfs_extract_features_as_profile, gml_extract_geom_to_geosparql, \
    GEO_hasGeometry, RDF_a, \
    HYF_HY_CatchmentRealization, HYF_realizedCatchment, HYF_lowerCatchment, \
    HYF_catchmentRealization, HYF_HY_Catchment, HYF_HY_HydroFeature, \
    calculate_bbox, NotFoundError, GEO_sfWithin, \
    GEO, GEOX, GEOF, QUDTS, UNIT, degrees_area_to_m2, HYF, DATA
from geofabric.model import GFModel
from geofabric.model.awraddcontractedcatchment import AWRADrainageDivisionContractedCatchment
from geofabric.model.rrcontractedcatchment import RiverRegionContractedCatchment
from functools import lru_cache
from datetime import datetime


@lru_cache(maxsize=128)
def retrieve_contracted_catchment(identifier):
    assert isinstance(identifier, int)
    ccatchment_wfs_uri = config.GF_OWS_ENDPOINT + \
                        '?request=GetFeature' \
                        '&service=WFS' \
                        '&version=2.0.0' \
                        '&typeName=ahgf_hrc:AHGFContractedCatchment' \
                        '&Filter=<Filter><PropertyIsEqualTo>' \
                        '<PropertyName>ahgf_hrc:hydroid</PropertyName>' \
                        '<Literal>{:d}</Literal>' \
                        '</PropertyIsEqualTo></Filter>'.format(identifier)
    session = retrieve_contracted_catchment.session
    if session is None:
        session = retrieve_contracted_catchment.session = Session()
    try:
        r = session.get(ccatchment_wfs_uri)
    except Exception as e:
        raise e
    tree = etree.parse(BytesIO(r.content))
    return tree


retrieve_contracted_catchment.session = None

ns = {
    'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_hrc',
    'geof': 'http://linked.data.gov.au/def/geofabric',
    'wfs': 'http://www.opengis.net/wfs/2.0',
    'gml': "http://www.opengis.net/gml/3.2"
}
catchment_tag_map = {
    "{{{}}}hydroid".format(ns['x']): 'hydroid',
    "{{{}}}concatid".format(ns['x']): 'concatid',
    "{{{}}}connodeid".format(ns['x']): 'connodeid',
    "{{{}}}conlevel".format(ns['x']): 'conlevel',
    "{{{}}}netnodeid".format(ns['x']): 'netnodeid',
    "{{{}}}mapnodeid".format(ns['x']): 'mapnodeid',
    "{{{}}}ahgfftype".format(ns['x']): 'ahgfftype',
    "{{{}}}srcfcname".format(ns['x']): 'srcfcname',
    "{{{}}}srcfctype".format(ns['x']): 'srcfctype',
    "{{{}}}sourceid".format(ns['x']): 'sourceid',
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


def contracted_catchment_geofabric_converter(model, wfs_features):
    if len(wfs_features) < 1:
        return None

    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    triples = set()

    for hydroid, catchment_element in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(
            "".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, str(hydroid)])
        )
        triples.add((feature_uri, RDF_a, GEOF.ContractedCatchment))

        for c in catchment_element.iterchildren():  # type: etree._Element
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
                    triples.add((A, DATA.value,
                                 Literal(Decimal(str(m2_area)), datatype=XSD.decimal)))
                    triples.add((feature_uri, GEOX.hasAreaM2, A))
                except ValueError:
                    pass
            elif var == 'albersarea':
                A = BNode()
                triples.add((A, QUDTS.numericValue, Literal(c.text, datatype=XSD.float)))
                triples.add((A, QUDTS.unit, UNIT.M2))
                triples.add((feature_uri, GEOF.albersArea, A))
            elif var == 'shape_length':
                L = BNode()
                triples.add((L, QUDTS.numericValue, Literal(c.text, datatype=XSD.float)))
                triples.add((L, QUDTS.unit, UNIT.DEG))
                triples.add((feature_uri, GEOF.perimeterLength, L))  # URIRef('http://dbpedia.org/property/length')
            elif var == 'shape':
                #try:
                #    _triples, geometry = gml_extract_geom_to_geosparql(c)
                #    for (s, p, o) in iter(_triples):
                #        triples.add((s, p, o))
                #except KeyError:
                #    val = c.text
                #    geometry = Literal(val)
                #triples.add((feature_uri, GEO_hasGeometry, geometry))
                # TODO: Reenable asGML or asWKT for Geofabric view
                pass
            elif var == 'attrsource':
                triples.add((feature_uri, DC.source, Literal(c.text)))

        # the CC register
        triples.add((feature_uri, URIRef('http://purl.org/linked-data/registry#register'), URIRef(config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE)))

    return triples, None


def contracted_catchment_hyfeatures_converter(wfs_features):
    if len(wfs_features) < 1:
        return None
    to_converter = {
        'shape': gml_extract_geom_to_geosparql,
        'nextdownid': lambda x: (set(), URIRef("".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, x.text]))),
    }
    to_float = ('shape_length', 'shape_area', 'albersarea')
    to_int = ('hydroid', 'ahgfftype', 'sourceid', 'concatid', 'connodeid', 'conlevel', 'netnodeid', 'mapnodeid')
    to_datetime = ('attrrel', 'featrel')
    is_geom = ('shape', )
    predicate_map = {
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
    for hydroid, catchment_element in features_source:  # type: int, etree._Element
        feature_uri = rdflib.URIRef(
            "".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE,
                     str(hydroid)]))
        triples.add((feature_uri, RDF_a, HYF_HY_HydroFeature))
        triples.add((feature_uri, RDF_a, HYF_HY_Catchment))
        for c in catchment_element.iterchildren():  # type: etree._Element
            try:
                var = catchment_tag_map[c.tag]
            except KeyError:
                continue
            try:
                conv_func = to_converter[var]
                _triples, val = conv_func(c)
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
    return triples, None


def contracted_catchment_features_geojson_converter(wfs_features):
    if len(wfs_features) < 1:
        return None
    to_converter = {
        'shape': gml_extract_geom_to_geojson,
    }
    to_float = ('shape_length', 'shape_area', 'albersarea')
    to_int = ('hydroid', 'ahgfftype', 'sourceid', 'concatid', 'connodeid', 'conlevel', 'netnodeid', 'mapnodeid')
    # to_datetime = ('attrrel', 'featrel')
    to_datetime = []
    is_geom = ('shape',)
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    for hydroid, catchment_element in features_source:  # type: int, etree._Element
        catchment_dict = {"type": "Feature", "id": hydroid, "geometry": {}, "properties": {}}

        for c in catchment_element.iterchildren():  # type: etree._Element
            try:
                var = catchment_tag_map[c.tag]
            except KeyError:
                continue
            try:
                conv_func = to_converter[var]
                val = conv_func(c)
            except KeyError:
                val = c.text
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
                catchment_dict['geometry'] = val
            else:
                catchment_dict['properties'][var] = val
        features_list.append(catchment_dict)
    return features_list


def extract_contracted_catchments_as_geojson(tree):
    geojson_features = wfs_extract_features_as_geojson(tree, ns['x'], "AHGFContractedCatchment", contracted_catchment_features_geojson_converter)
    return geojson_features


def extract_contracted_catchments_as_hyfeatures(tree, model=None):
    g = rdflib.Graph()
    g.bind('geo', GEO)
    g.bind('geox', GEOX)
    g.bind('hyf', HYF)
    g.bind('qudt', QUDTS)
    g.bind('unit', UNIT)
    triples, features = wfs_extract_features_as_profile(
        tree,
        ns['x'],
        "AHGFContractedCatchment",
        contracted_catchment_hyfeatures_converter,
        model=model
    )
    for (s, p, o) in iter(triples):
        g.add((s, p, o))
    return g


def extract_contracted_catchments_as_geofabric(tree, model=None):
    g = rdflib.Graph()
    g.bind('geo', GEO)
    g.bind('geox', GEOX)
    g.bind('geof', GEOF)
    g.bind('data', DATA)
    g.bind('qudt', QUDTS)
    g.bind('unit', UNIT)
    triples, features = wfs_extract_features_as_profile(
        tree,
        ns['x'],
        "AHGFContractedCatchment",
        contracted_catchment_geofabric_converter,
        model=model
    )
    for (s, p, o) in iter(triples):
        g.add((s, p, o))
    return g


class ContractedCatchment(GFModel):

    @classmethod
    def make_instance_label(cls, instance_id):
        return "Contracted Catchment ID: {}".format(str(instance_id))

    @classmethod
    def make_canonical_uri(cls, instance_id):
        return "".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, instance_id])

    @classmethod
    def make_local_url(cls, instance_id):
        return url_for('classes.contracted_catchment', contractedcatchment_id=instance_id)

    @classmethod
    def get_index(cls, page, per_page):
        per_page = max(int(per_page), 1)
        offset = (max(int(page), 1)-1)*per_page
        catchments_wfs_uri = config.GF_OWS_ENDPOINT + \
                             '?service=wfs' \
                             '&version=2.0.0' \
                             '&request=GetFeature' \
                             '&typeName=ahgf_hrc:AHGFContractedCatchment' \
                             '&propertyName=hydroid' \
                             '&sortBy=hydroid' \
                             '&count={}&startIndex={}'.format(per_page, offset)
        r = requests.get(catchments_wfs_uri)
        try:
            tree = etree.parse(BytesIO(r.content))
        except ParseError as e:
            print(e)
            print(r.text)
            return []
        items = tree.xpath('//x:hydroid/text()', namespaces={
            'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_hrc'})
        return items

    def __init__(self, identifier):
        super(ContractedCatchment, self).__init__()
        identifier = int(identifier)
        contracted_catchment_xml_tree = retrieve_contracted_catchment(identifier)
        self.xml_tree = contracted_catchment_xml_tree
        ccatchments = extract_contracted_catchments_as_geojson(contracted_catchment_xml_tree)
        if ccatchments['features'] is None or len(ccatchments['features']) < 1:
            raise NotFoundError()
        ccatchment = ccatchments['features'][0]
        self.geometry = ccatchment['geometry']
        self.awraddcc = None
        self.rrcc = None
        for k, v in ccatchment['properties'].items():
            setattr(self, k, v)

    def get_bbox(self, pad=0):
        coords = self.geometry['coordinates']
        json_bbox = calculate_bbox(coords, pad=pad)
        (n, s, e, w) = json_bbox
        return (w,s,e,n) # (minx, miny, maxx, maxy)

    def get_awraddcc(self):
        try:
            concatid = self.concatid
        except AttributeError:
            return None
        if self.awraddcc is None:
            try:
                self.awraddcc = AWRADrainageDivisionContractedCatchment(concatid)
            except NotFoundError:
                self.awraddcc = None
        return self.awraddcc

    def get_rrcc(self):
        try:
            concatid = self.concatid
        except AttributeError:
            return None
        if self.rrcc is None:
            try:
                self.rrcc = RiverRegionContractedCatchment(concatid)
            except NotFoundError:
                self.rrcc = None
        return self.rrcc

    @property
    def awraddid(self):
        try:
            awraddcc = self.get_awraddcc()
            return awraddcc.awraddid
        except Exception:
            return None

    @property
    def rrid(self):
        try:
            rrcc = self.get_rrcc()
            return rrcc.rrid
        except Exception:
            return None

    def to_hyfeatures_graph(self):
        g = extract_contracted_catchments_as_hyfeatures(self.xml_tree)
        feature_uri = None
        if self.awraddid:
            dd_uri = rdflib.URIRef("".join([config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE, str(self.awraddid)]))
            feature_uri = feature_uri or rdflib.URIRef("".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, str(self.hydroid)]))
            g.add((feature_uri, GEO_sfWithin, dd_uri))
        if self.rrid:
            rr_uri = rdflib.URIRef("".join([config.URI_RIVER_REGION_INSTANCE_BASE, str(self.rrid)]))
            feature_uri = feature_uri or rdflib.URIRef("".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, str(self.hydroid)]))
            g.add((feature_uri, GEO_sfWithin, rr_uri))
        return g

    def to_geofabric_graph(self):
        g = extract_contracted_catchments_as_geofabric(self.xml_tree, model=self)
        feature_uri = None
        if self.awraddid:
            dd_uri = rdflib.URIRef("".join([config.URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE, str(self.awraddid)]))
            feature_uri = feature_uri or rdflib.URIRef("".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, str(self.hydroid)]))
            g.add((feature_uri, GEO_sfWithin, dd_uri))
        if self.rrid:
            rr_uri = rdflib.URIRef("".join([config.URI_RIVER_REGION_INSTANCE_BASE, str(self.rrid)]))
            feature_uri = feature_uri or rdflib.URIRef("".join([config.URI_CONTRACTED_CATCHMENT_INSTANCE_BASE, str(self.hydroid)]))
            g.add((feature_uri, GEO_sfWithin, rr_uri))
        return g

    def export_html(self, view='geofabric'):
        bbox = self.get_bbox(pad=12)
        bbox_string = ",".join(str(i) for i in bbox)
        centrepoint = []
        centrepoint.append(bbox[0] + ((bbox[2] - bbox[0]) / 2))
        centrepoint.append(bbox[1] + ((bbox[3] - bbox[1]) / 2))
        hydroid = self.hydroid
        try:
            concatid = self.concatid
        except AttributeError:
            concatid = None
        wms_url = config.GF_OWS_ENDPOINT +\
                  "?service=wms&version=2.0.0&request=GetMap" \
                  "&width=800&height=600" \
                  "&format=text/html;+subtype=openlayers" \
                  "&CRS=EPSG:4326" \
                  "&layers=osm_au,ahgf_hrc:AHGFContractedCatchment" \
                  "&style=ahgfcatchment" \
                  "&bbox=" + bbox_string +\
                  "&CQL_FILTER=INCLUDE;hydroid="+str(hydroid)
        m2_area = degrees_area_to_m2(self.shape_area, centrepoint[1])
        if view == 'geofabric':
            view_html = render_template(
                'class_contracted_catchment_geof.html',
                wms_url=wms_url,
                bbox=bbox,
                centrepoint=centrepoint,
                hydroid=hydroid,
                concatid=concatid,
                rrid=self.rrid,
                awraddid=self.awraddid,
                shape_length=self.shape_length,
                shape_area=self.shape_area,
                m2_area = m2_area,
                albers_area=self.albersarea,
            )
        elif view == "hyfeatures":
            view_html = render_template(
                'class_contracted_catchment_hyf.html',
                wms_url=wms_url,
                bbox=bbox,
                centrepoint=centrepoint,
                hydroid=hydroid,
                concatid=concatid,
                rrid=self.rrid,
                awraddid=self.awraddid,
                shape_length=self.shape_length,
                shape_area=self.shape_area,
                m2_area=m2_area,
                albers_area=self.albersarea,
            )
        else:
            return NotImplementedError("HTML representation of View '{}' is not implemented.".format(view))

        return view_html


if __name__ == "__main__":
    i = ContractedCatchment.get_index(20, 1000)
    print(i)
    for x in i:
        print("Trying {}...".format(x))
        c = ContractedCatchment(x)
        try:
            concatid = c.concatid
        except AttributeError:
            continue
        print("Found One! {}".format(x))
        break
