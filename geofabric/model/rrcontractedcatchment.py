# -*- coding: utf-8 -*-
#
from io import BytesIO
import requests
from requests import Session
from lxml import etree
from geofabric import _config as config
from geofabric.helpers import wfs_extract_features_as_geojson, NotFoundError
from geofabric.model import GFModel
from functools import lru_cache
from datetime import datetime


@lru_cache(maxsize=128)
def retrieve_rrcc_for_contracted_catchment(identifier):
    assert isinstance(identifier, int)
    rr_wfs_uri = config.GF_OWS_ENDPOINT + \
                        '?request=GetFeature' \
                        '&service=WFS' \
                        '&version=2.0.0' \
                        '&typeName=ahgf_hrr:RRContractedCatchmentLookup' \
                        '&Filter=<Filter><PropertyIsEqualTo>' \
                        '<PropertyName>ahgf_hrr:concatid</PropertyName>' \
                        '<Literal>{:d}</Literal>' \
                        '</PropertyIsEqualTo></Filter>'.format(identifier)
    session = retrieve_rrcc_for_contracted_catchment.session
    if session is None:
        session = retrieve_rrcc_for_contracted_catchment.session = Session()
    try:
        r = session.get(rr_wfs_uri)
    except Exception as e:
        raise e
    tree = etree.parse(BytesIO(r.content))
    return tree


retrieve_rrcc_for_contracted_catchment.session = None

ns = {
    'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_hrr',
    'wfs': 'http://www.opengis.net/wfs/2.0',
    'gml': "http://www.opengis.net/gml/3.2"
}
rrcc_tag_map = {
    "{{{}}}concatid".format(ns['x']): 'concatid',
    "{{{}}}rrid".format(ns['x']): 'rrid'
}


def rrcc_features_geojson_converter(wfs_features):
    if len(wfs_features) < 1:
        return None
    to_converter = {
    }
    to_float = tuple()
    to_int = ('concatid', 'rrid')
    # to_datetime = ('attrrel', 'featrel')
    to_datetime = []
    is_geom = tuple()
    features_list = []
    if isinstance(wfs_features, (dict,)):
        features_source = wfs_features.items()
    elif isinstance(wfs_features, (list, set)):
        features_source = iter(wfs_features)
    else:
        features_source = [wfs_features]

    for identifier, dd_element in features_source:  # type: int, etree._Element
        rrcc_dict = {"type": "Feature", "id": identifier, "geometry": {}, "properties": {}}

        for r in dd_element.iterchildren():  # type: etree._Element
            try:
                var = rrcc_tag_map[r.tag]
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
                try:
                    val = int(val)
                except ValueError:
                    val = str(val)
            if var in is_geom:
                rrcc_dict['geometry'] = val
            else:
                rrcc_dict['properties'][var] = val
        features_list.append(rrcc_dict)
    return features_list


def extract_rrcc_as_geojson(tree):
    geojson_features = wfs_extract_features_as_geojson(
        tree, ns['x'], "RRContractedCatchmentLookup",
        rrcc_features_geojson_converter)
    return geojson_features


class RiverRegionContractedCatchment(GFModel):
    @classmethod
    def make_instance_label(cls, instance_id):
        return "RiverRegion ContractedCatchment Lookup ID: {}".format(str(instance_id))

    @classmethod
    def make_canonical_uri(cls, instance_id):
        raise NotImplementedError()

    @classmethod
    def make_local_url(cls, instance_id):
        raise NotImplementedError()

    @classmethod
    def get_index(cls, page, per_page):
        per_page = max(int(per_page), 1)
        offset = (max(int(page), 1)-1)*per_page
        dd_wfs_uri = config.GF_OWS_ENDPOINT + \
                     '?service=wfs' \
                     '&version=2.0.0' \
                     '&request=GetFeature' \
                     '&typeName=ahgf_hrr:RRContractedCatchmentLookup' \
                     '&propertyName=concatid' \
                     '&sortBy=concatid' \
                     '&count={}&startIndex={}'.format(per_page, offset)
        r = requests.get(dd_wfs_uri)
        tree = etree.parse(BytesIO(r.content))
        items = tree.xpath('//x:concatid/text()', namespaces={
            'x': 'http://linked.data.gov.au/dataset/geof/v2/ahgf_hrr'})
        return items

    def __init__(self, cc_identifier):
        super(RiverRegionContractedCatchment, self).__init__()
        from geofabric.model.contractedcatchment import ContractedCatchment
        if isinstance(cc_identifier, ContractedCatchment):
            cc_identifier = cc_identifier.concatid
        cc_identifier = int(cc_identifier)
        rrcc_xml_tree = retrieve_rrcc_for_contracted_catchment(cc_identifier)
        self.xml_tree = rrcc_xml_tree
        lookups = extract_rrcc_as_geojson(rrcc_xml_tree)
        if lookups['features'] is None or len(lookups['features']) < 1:
            raise NotFoundError()
        # TODO: handle having more than one feature returned from lookup
        lookup = lookups['features'][0]
        for k, v in lookup['properties'].items():
            setattr(self, k, v)

    def export_html(self, view=None):
        raise NotImplementedError()


if __name__ == "__main__":
    i = RiverRegionContractedCatchment.get_index(1, 20)
    print(i)
    a = RiverRegionContractedCatchment(100001)
