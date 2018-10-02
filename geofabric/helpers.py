# -*- coding: utf-8 -*-
import lxml

import rdflib
from rdflib import Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD
from lxml import etree

HYF = Namespace("https://www.opengis.net/def/hy_features/ontology/hyf/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
GML = Namespace("http://www.opengis.net/ont/gml#")
OGC = Namespace("http://www.opengis.net/")
HYF_HY_HydroFeature = HYF.term('HY_HydroFeature')
HYF_HY_Catchment = HYF.term('HY_Catchment')
HYF_HY_CatchmentRealization = HYF.term('HY_CatchmentRealization')
HYF_realizedCatchment = HYF.term('realizedCatchment')
HYF_lowerCatchment = HYF.term('lowerCatchment')
HYF_upperCatchment = HYF.term('upperCatchment')
HYF_catchmentRealization = HYF.term('catchmentRealization')
GEO_Geometry = GEO.term('Geometry')
GEO_hasGeometry = GEO.term('hasGeometry')
GEO_coordinateDimension = GEO.term('coordinateDimension')
GEO_dimension = GEO.term('dimension')  # topological dimension.
GEO_spatialDimension = GEO.term('spatialDimension')  # overrides coordinateDimension
GEO_isEmpty = GEO.term('isEmpty')
GEO_isSimple = GEO.term('isSimple')
GEO_hasDefaultGeometry = GEO.term('hasDefaultGeometry')
RDF_a = RDF.term('type')


def chunks(source, length):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(source), length):
        yield source[i:i + length]


ns = {
    'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_shcatch',
    'wfs': 'http://www.opengis.net/wfs/2.0',
    'gml': "http://www.opengis.net/gml/3.2"
}

def gml_extract_geom_to_geojson(node, recursion=0):
    """

    :param node:
    :type node: etree._Element
    :return:
    """
    if recursion >= 10:
        return []

    MultiSurface = "{{{}}}MultiSurface".format(ns['gml'])
    surface_member_tag = "{{{}}}surfaceMember".format(ns['gml'])
    Polygon = "{{{}}}Polygon".format(ns['gml'])
    exterior_tag = "{{{}}}exterior".format(ns['gml'])
    interior_tag = "{{{}}}interior".format(ns['gml'])
    LinearRing = "{{{}}}LinearRing".format(ns['gml'])
    posList = "{{{}}}posList".format(ns['gml'])
    pos = "{{{}}}pos".format(ns['gml'])

    geom = next(node.iterchildren())  # type: etree._Element
    if geom.tag == "something_multigeometry":
        srs_dims = int(geom.get('srsDimension', 2))
        srs_name = geom.get('srsName', "EPSG:4326") #4326 is WGS84/Unprojected #3395 is WGS84/Mercator. #4283 is Australia
        crs = {"type": "name", "properties": {"name": srs_name}}
        geometries = []
        member_elems = geom.iterchildren(tag=surface_member_tag)
        for m in member_elems:
            member = gml_extract_geom_to_geojson(m, recursion=recursion+1)
            geometries.append(member)
        return {"type": "GeometryCollection", "geometries": geometries, "dims": srs_dims, "crs": crs}
    if geom.tag == MultiSurface:
        srs_dims = int(geom.get('srsDimension', 2))
        srs_name = geom.get('srsName', "EPSG:4326") #4326 is WGS84/Unprojected #3395 is WGS84/Mercator. #4283 is Australia
        crs = {"type": "name", "properties": {"name": srs_name}}
        coords = []
        member_elems = geom.iterchildren(tag=surface_member_tag)
        for m in member_elems:
            member = gml_extract_geom_to_geojson(m, recursion=recursion+1)
            if member['type'] == "Polygon":
                coords.append(member['coordinates'])
            elif member['type'] == "MultiPolygon":
                coords.extend(member['coordinates'])
            else:
                raise ValueError(
                    "Multipolygon cannot have a member of type {}".format(member['type']))
        return {"type": "MultiPolygon", "coordinates": coords, "dims": srs_dims, "crs": crs}
    elif geom.tag == Polygon:
        def extract_poly_coords(node, dims=2):
            """

            :param elem:
            :type elem: etree._Element
            :return:
            """
            nonlocal LinearRing
            nonlocal posList, pos
            elem = next(node.iterchildren())  # type: etree._Element
            if elem.tag == LinearRing:
                coords = []
                pos_list_elems = list(elem.iterchildren(tag=posList))
                if len(pos_list_elems) > 0:
                    pos_list = pos_list_elems[0]
                    pos_list = str(pos_list.text).split()
                else:
                    pos_list = []
                    pos_elems = list(elem.iterchildren(tag=pos))
                    for pos_elem in pos_elems:
                        pos_members = str(pos_elem.text).split()
                        if len(pos_members) != dims:
                            raise ValueError(
                                "Dims = {:s} but pos has a different number of dimensions."\
                                    .format(str(dims)))
                        pos_list.extend(pos_members)
                if dims == 2:
                    for x, y in chunks(pos_list, 2):
                        coords.append((float(y), float(x)))
                        #coords.append({'x': x, 'y': y})
                elif dims == 3:
                    for x, y, z in chunks(pos_list, 3):
                        coords.append((float(y), float(x), float(z)))
                        #coords.append({'x': x, 'y': y, 'z': z})
                elif dims == 4:
                    for x, y, z, w in chunks(pos_list, 4):
                        coords.append((float(y), float(x), float(z), float(w)))
                        #coords.append({'x': x, 'y': y, 'z': z, 'w': w})
                return coords
            else:
                raise NotImplementedError(
                    "Poly geom type {} is not implemented.".format(elem.tag))
        poly_dict = {'exterior': None, 'interior': []}
        srs_dims = int(geom.get('srsDimension', 2))
        srs_name = geom.get('srsName', "EPSG:4326")  # 4326 is WGS84/Unprojected #3395 is WGS84/Mercator. #4283 is Australia
        crs = {"type": "name", "properties": {"name": srs_name}}
        exterior_elems = list(geom.iterchildren(tag=exterior_tag))
        if len(exterior_elems) > 0:
            exterior = exterior_elems[0]
            poly_dict['exterior'] = extract_poly_coords(exterior, dims=srs_dims)
        interior_elems = list(geom.iterchildren(tag=interior_tag))
        for interior_elem in interior_elems:
            interior = extract_poly_coords(interior_elem, dims=srs_dims)
            poly_dict['interior'].append(interior)
        coords = []
        if poly_dict['exterior']:
            coords.append(poly_dict['exterior'])
        else:
            coords.append([])
        coords.extend(poly_dict['interior'])
        return {"type": "Polygon", "crs": crs, "dims": srs_dims, "coordinates": coords}

    else:
        raise NotImplementedError(
            "Don't know how to convert geom type: {}".format(geom.tag))

def gml_extract_geom_to_geosparql(node, recursion=0):
    """

    :param node:
    :type node: etree._Element
    :return:
    """
    if recursion >= 10:
        return []

    GEO_gmlLiteral = GEO.term('gmlLiteral')  # The literal datatype
    GEO_asGML = GEO.term('asGML')
    GEO_hasSerialization = GEO.term('hasSerialization')
    geom = next(node.iterchildren())
    lexical = lxml.etree.tostring(geom, xml_declaration=False, pretty_print=True)
    lit = rdflib.Literal(lexical, datatype=GEO_gmlLiteral)
    triples = set()
    geometry_node = rdflib.BNode()
    triples.add((geometry_node, RDF_a, GEO_Geometry))
    triples.add((geometry_node, GEO_asGML, lit))
    #triples.add((geometry_node, GEO_hasSerialization, lit))
    return triples, geometry_node


def wfs_find_features(tree, feature_type):
    """

    :param tree:
    :type tree: etree._ElementTree | etree._Element
    :param feature_type:
    :type feature_type: str
    :return:
    """
    # Assumes root is a WFS FeatureCollection

    FeatureCollection = "{{{}}}FeatureCollection".format(ns['wfs'])
    member_tag = "{{{}}}member".format(ns['wfs'])
    SearchClass = "{{{}}}{}".format(ns['x'], feature_type)
    hydroid_tag = "{{{}}}hydroid".format(ns['x'])

    if isinstance(tree, etree._ElementTree):
        root = tree.getroot()  # type: etree._Element
    elif isinstance(tree, etree._Element):
        root = tree
    else:
        raise ValueError("tree must be an ElementTree or a RootElement")
    t = root.tag
    if t != FeatureCollection:
        return None
    features = {}

    number_returned = root.get('numberMatched')
    if number_returned is None or int(number_returned) < 1:
        return features

    for member in root.iterchildren(tag=member_tag):  # type: etree._Element
        member_objects = member.getchildren()
        if len(member_objects) < 1:
            continue
        member_object = member_objects[0] # type: etree._Element
        if member_object.tag != SearchClass:
            continue
        hydroid_nodes = member_object.iterchildren(tag=hydroid_tag)
        try:
            hydroid_node = next(hydroid_nodes)
            hydro_id = int(hydroid_node.text)
        except StopIteration:
            hydro_id = None
        if hydro_id is None:
            gml_id = member_object.get("{{{}}}id".format(ns['gml']))
            if gml_id:
                key = hydro_id
            else:
                key = "unknown"
        else:
            key = hydro_id
        features[key] = member_object
    return features

def wfs_extract_features_as_geojson(tree, feature_type, class_converter=None):
    """

    :param tree:
    :type tree: etree._ElementTree | etree._Element
    :param feature_type:
    :type feature_type: str
    :return:
    """
    features = wfs_find_features(tree, feature_type)

    geojson_feature_collection = {
        "type": "FeatureCollection",
        "features": None
    }
    if class_converter:
        geojson_feature_collection['features'] = class_converter(features)
    else:
        features_list = []
        for key, val in features.items():
            features_list.append((key, val))
        geojson_feature_collection['features'] = features_list
    return geojson_feature_collection


def wfs_extract_features_as_hyfeatures(tree, feature_type, class_converter=None):
    """

    :param tree:
    :type tree: etree._ElementTree | etree._Element
    :param feature_type:
    :type feature_type: str
    :return:
    """
    features = wfs_find_features(tree, feature_type)
    if class_converter:
        triples, feature_nodes = class_converter(features)
    else:
        raise NotImplementedError("Need a class converter in order to get HY_Features from WFS.")
    return triples, feature_nodes

def mymax(a, b):
    if a is None: return b
    if b is None: return a

    if a > b: return a
    return b


def mymin(a, b):
    if a is None: return b
    if b is None: return a

    if a < b: return a
    return b


def calculate_bboxes(g, bounds=None, pad=0):
    if bounds is None:
        bounds = [[None, None, None, None], [None, None, None, None]]
    for i in g:
        if isinstance(i, list):
            bounds = calculate_bboxes(i, bounds=bounds)
        else:
            pBounds = bounds[0]
            nBounds = bounds[1]

            lon = i[0]
            lat = i[1]

            curBounds = pBounds
            if (lon < 0):
                curBounds = nBounds

            n = curBounds[0]
            s = curBounds[1]
            e = curBounds[2]
            w = curBounds[3]

            n = mymax(lat, n)
            s = mymin(lat, s)
            e = mymax(lon, e)
            w = mymin(lon, w)

            if lon < 0:
                bounds = (pBounds, [n, s, e, w])
            else:
                bounds = ([n, s, e, w], nBounds)
    return bounds

def calculate_bbox(g, pad=0):
    twin_bounds = ([None, None, None, None], [None, None, None, None])
    (nbounds, pbounds) = calculate_bboxes(g, bounds=twin_bounds, pad=pad)
    if pbounds[0] is None:
        b = nbounds
    elif nbounds[0] is None:
        b = pbounds
    else:
        #combine nbounds and pbounds
        n = mymax(nbounds[0], pbounds[0])
        s = mymin(nbounds[1], pbounds[1])
        mod_e = (360.0 + nbounds[2])
        w = pbounds[3]
        b = [n, s, mod_e, w]
    if pad is not None and pad > 0:
        pad = float(pad)
        y_stretch = b[0] - b[1]
        x_stretch = b[2] - b[3]
        y_extra = (y_stretch/100.0) * pad
        x_extra = (x_stretch / 100.0) * pad
        b[0] = mymin(b[0] + (y_extra / 2.0), 90.0)
        b[1] = mymax(b[1] - (y_extra / 2.0), -90.0)
        b[2] = mymin(b[2] + (x_extra / 2.0), 360.0)
        b[3] = mymax(b[3] - (x_extra / 2.0), -180.0)
    return b
