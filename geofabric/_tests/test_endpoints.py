# this set of tests calls a series of endpoints that this API is meant to expose and tests them for content
import requests
import re
import pytest

SYSTEM_URI = 'http://geofabricld.net'
HEADERS_TTL = {'Accept': 'text/turtle'}


def valid_endpoint_content(uri, headers, pattern):
    # dereference the URI
    r = requests.get(uri, headers=headers)

    # parse the content looking for the thing specified in REGEX
    if re.search(pattern, r.content.decode('utf-8'), re.MULTILINE):
        return True
    else:
        return False


# def test_geofabric_landing_page_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/',
#         None,
#         r'<a href="http:\/\/www\.bom\.gov\.au\/water\/geofabric\/">The Geofabric<\/a>'
#     ), 'Geofabric landing page html failed'
#
#
# @pytest.mark.skip('Geofabric landing page rdf turtle file extension not yet implemented')
# def test_geofabric_landing_page_rdf_turtle_file_extension():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/index.ttl',
#         None,
#         None, #TODO
#     ), 'Geofabric landing page rdf turtle file extension failed'
#
#
# def test_geofabric_landing_page_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_format=text/turtle',
#         None,
#         r'<http:\/\/geofabricld\.net\/catchment\/> a reg:Register ;'
#     ), 'Geofabric landing page rdf turtle qsa failed'
#
#
# def test_geofabric_landing_page_rdf_turtle_accept_header():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/',
#         HEADERS_TTL,
#         r'<http:\/\/geofabricld\.net\/catchment\/> a reg:Register ;'
#     ), 'Geofabric landing page rdf turtle accept header failed'
#
#
# def test_geofabric_landing_page_alternates_view_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_view=alternates&_format=text/html',
#         None,
#         r'<td><a href="http:\/\/geofabricld\.net\/\?_view=reg">reg<\/a><\/td>'
#     ), 'Geofabric alternates view html failed'
#
#
# def test_geofabric_landing_page_alternates_view_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_view=alternates&_format=text/turtle',
#         None,
#         r'rdfs:comment "The view that lists all other views"\^\^xsd:string ;'
#     ), 'Geofabric alternates view rdf turtle qsa failed'
#
#
# def test_geofabric_landing_page_alternates_view_rdf_turtle_accept_header():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_view=alternates',
#         HEADERS_TTL,
#         r'rdfs:comment "The view that lists all other views"\^\^xsd:string ;'
#     ), 'Geofabric alternates view rdf turtle accept header failed'
#
#
# def test_geofabric_landing_page_reg_view_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_view=reg&_format=text/html',
#         None,
#         r'<h1>Geofabric - distributed as Linked Data<\/h1>'
#     ), 'Geofabric reg view html failed'
#
#
# def test_geofabric_landing_page_reg_view_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_view=reg&_format=text/turtle',
#         None,
#         r'<http:\/\/geofabricld\.net\/catchment\/> a reg:Register ;'
#     ), 'Geofabric reg view rdf turtle qsa failed'
#
#
# def test_geofabric_landing_page_reg_view_rdf_turtle_accept_header():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/?_view=reg',
#         HEADERS_TTL,
#         r'<http:\/\/geofabricld\.net\/catchment\/> a reg:Register ;'
#     ), 'Geofabric reg view rdf turtle accept header failed'
#
#
# def test_geofabric_catchment_register_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/',
#         None,
#         r'<h3>Of <em><a href="https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment">https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment<\/a><\/em> class items<\/h3>'
#     ), 'Geofabric Catchment Register html failed.'
#
#
# @pytest.mark.skip('Geofabric Catchment Register text turtle file extension not yet implemented')
# def test_geofabric_catchment_register_turtle_file_extension():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/index.ttl',
#         None,
#         r'<http:\/\/geofabricld\.net\/catchment\/6600519> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment> ;'
#     ), 'Geofabric Catchment Register text turtle file extension failed'
#
#
# def test_geofabric_catchment_register_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_format=text/turtle',
#         None,
#         r'<http:\/\/geofabricld\.net\/catchment\/6600519> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment> ;'
#     ), 'Geofabric Catchment Register text turtle qsa failed'
#
#
# def test_geofabric_catchment_register_rdf_turtle_accept_header():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/',
#         HEADERS_TTL,
#         r'<http:\/\/geofabricld\.net\/catchment\/6600519> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment> ;'
#     ), 'Geofabric Catchment Register text turtle accept header failed'
#
#
# def test_geofabric_catchment_register_alternates_view_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_view=alternates&_format=text/html',
#         None,
#         r'<h3>Alternates view of a <a href="http:\/\/purl\.org\/linked-data\/registry#Register">http:\/\/purl\.org\/linked-data\/registry#Register<\/a><\/h3>'
#     ), 'Geofabric Catchment Register alternates view html failed'
#
#
# def test_geofabric_catchment_register_alternates_view_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_view=alternates&_format=text/turtle',
#         None,
#         r'rdfs:comment "A simple list-of-items view taken from the Registry Ontology"\^\^xsd:string ;'
#     ), 'Geofabric Catchment Register alternates view rdf turtle qsa failed'
#
#
# def test_geofabric_catchment_register_alternates_view_rdf_turtle_accept_header():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_view=alternates',
#         HEADERS_TTL,
#         r'rdfs:comment "A simple list-of-items view taken from the Registry Ontology"\^\^xsd:string ;'
#     ), 'Geofabric Catchment Register alternates view rdf turtle accept headers failed'
#
#
# def test_geofabric_catchment_register_reg_view_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_view=reg',
#         None,
#         r'<h3>Of <em><a href="https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment">https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment<\/a><\/em> class items<\/h3>'
#     ), 'Geofabric Catchment Register reg view html failed.'
#
#
# def test_geofabric_catchment_register_reg_view_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_view=reg&_format=text/turtle',
#         None,
#         r'<http:\/\/geofabricld\.net\/catchment\/6600519> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment> ;'
#     ), 'Geofabric Catchment Register reg view text turtle qsa failed'
#
#
# def test_geofabric_catchment_register_reg_view_rdf_turtle_accept_header():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/?_view=reg',
#         HEADERS_TTL,
#         r'<http:\/\/geofabricld\.net\/catchment\/6600519> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_Catchment> ;'
#     ), 'Geofabric Catchment Register reg view text turtle accept header failed'
#
#
# def test_geofabric_catchment__6600519_html():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/6600519',
#         None,
#         r'<tr><td>Downstream Catchment<\/td><td><code><a href="\/catchment\/6600521">6600521<\/a><\/code><\/td><\/tr>'
#     ), 'Geofabric Catchment instance 6600519 html failed'
#
#
# @pytest.mark.skip('Geofabric Catchment instance 6600519 rdf turtle file extension not yet implemented')
# def test_geofabric_catcment_6600519_rdf_turtle_file_extension():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/6600519.ttl',
#         None,
#         None, #TODO
#     ), 'Geofabric Catchment instance 6600519 rdf turtle file extension failed'
#
#
# # this was not working at the time of testing
# @pytest.mark.skip('Geofabric Catchment instance 6600519 rdf turtle qsa not yet implemented')
# def test_geofabric_catchment__6600519_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/6600519?_format=text/turtle',
#         None,
#         None #TODO
#     ), 'Geofabric Catchment instance 6600519 rdf turtle qsa failed'
#
#
# # same as test test_geofabric_catchment__6600519_rdf_turtle_qsa()
# @pytest.mark.skip('Geofabric Catchment instance 6600519 rdf turtle accept header not yet implemented')
# def test_geofabric_catchment__6600519_rdf_turtle_qsa():
#     assert valid_endpoint_content(
#         f'{SYSTEM_URI}/catchment/6600519',
#         HEADERS_TTL,
#         None #TODO
#     ), 'Geofabric Catchment instance 6600519 rdf turtle accept header failed'


def test_geofabric_catchment_660519_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=alternates&_format=text/html',
        None,
        r'<h1>Geofabric Linked Data API</h1>'
    ), 'Geofabric Catchment instance 660519 alternates view html failed'


def test_geofabric_catchment_660519_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld.net\/catchment\/6600519>'
    ), 'Geofabric Catchment instance 660519 alternates view rdf turtle qsa failed'


def test_geofabric_catchment_660519_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/geofabricld.net\/catchment\/6600519>'
    ), 'Geofabric Catchment instance 660519 alternates view rdf turtle accept header failed'


def test_geofabric_catchment_660519_geofabric_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=geofabric&_format=text/html',
        None,
        r'<h1>Catchment 6600519<\/h1>'
    ), 'Geofabric Catchment instance 660519 geofabric view html failed'


@pytest.mark.skip('Geofabric Catchment instance 660519 geofabric view rdf turtle qsa not yet implemented')
def test_geofabric_catchment_660519_geofabric_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=geofabric&_format=text/turtle',
        None,
        None, #TODO
    ), 'Geofabric Catchment instance 660519 geofabric view rdf turtle qsa failed'


@pytest.mark.skip('Geofabric Catchment instance 660519 geofabric view rdf turtle accept header not yet implemented')
def test_geofabric_catchment_660519_geofabric_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=geofabric',
        HEADERS_TTL,
        None, #TODO
    ), 'Geofabric Catchment instance 660519 geofabric view rdf turtle accept header failed'


@pytest.mark.skip('Geofabric Catchment instance 660519 schemaorg view rdf application/ld+json not yet implemented')
def test_geofabric_catchment_660519_schemaorg_view_rdf_json():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?format=application/ld+json',
        None,
        None #TODO
    ), 'Geofabric Catchment instance 660519 schemaorg view rdf application/ld+json failed'


def test_geofabric_catchment_660519_hyfeatures_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=hyfeatures&_format=text/html',
        None,
        r'<h1>Catchment 6600519<\/h1>'
    ), 'Geofabric Catchment instance 660519 hyfeatures view html failed'


@pytest.mark.skip('Geofabric Catchment instance 660519 hyfeatures view rdf turtle qsa not yet implemented')
def test_geofabric_catchment_660519_hyfeatures_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=hyfeatures&_format=text/turtle',
        None,
        None #TODO
    ), 'Geofabric Catchment instance 660519 hyfeatures view rdf turtle qsa failed'


@pytest.mark.skip('Geofabric Catchment instance 660519 hyfeatures view rdf turtle accept header not yet implemented')
def test_geofabric_catchment_660519_hyfeatures_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/catchment/6600519?_view=hyfeatures',
        HEADERS_TTL,
        None #TODO
    ), 'Geofabric Catchment instance 660519 hyfeatures view rdf turtle accept header failed'


def test_geofabric_riverregion_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/',
        None,
        r'<li><a href="\/riverregion\/9400216">9400216<\/a><\/li>'
    ), 'Geofabric River Region Register html failed'


def test_geofabric_riverregion_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/riverregion\/9400216> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric River Region Register rdf turtle qsa failed'


@pytest.mark.skip('Geofabric River Region Register rdf turtle file extension not yet implemented')
def test_geofabric_riverregion_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/index.ttl',
        None,
        r'<http:\/\/geofabricld\.net\/riverregion\/9400216> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric River Region Register rdf turtle file extension failed'


def test_geofabric_riverregion_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/',
        HEADERS_TTL,
        r'<http:\/\/geofabricld\.net\/riverregion\/9400216> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric River Region Register rdf turtle accept header failed'


def test_geofabric_riverregion_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_view=alternates&_format=text/html',
        None,
        r'<h1>Geofabric Linked Data API<\/h1>'
    ), 'Geofabric River Region Register alternates view html failed'


def test_geofabric_riverregion_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_view=alternates&_format=text/turtle',
        None,
        r'rdfs:comment "A simple list-of-items view taken from the Registry Ontology"\^\^xsd:string ;'
    ), 'Geofabric River Region Register alternates view rdf turtle qsa failed'


def test_geofabric_riverregion_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_view=alternates',
        HEADERS_TTL,
        r'rdfs:comment "A simple list-of-items view taken from the Registry Ontology"\^\^xsd:string ;'
    ), 'Geofabric River Region Register alternates view rdf turtle accept header failed'


def test_geofabric_riverregion_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_view=reg',
        None,
        r'<li><a href="\/riverregion\/9400216">9400216<\/a><\/li>'
    ), 'Geofabric River Region Register reg view html failed'


def test_geofabric_riverregion_register_reg_vie_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/riverregion\/9400216> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric River Region Register reg view rdf turtle qsa failed'


def test_geofabric_riverregion_register_reg_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/geofabricld\.net\/riverregion\/9400216> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric River Region Register reg view rdf turtle accept header failed'


def test_geofabric_riverregion_9400216_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216',
        None,
        r'<tr><td>HydroID<\/td><td><code>9400216<\/code><\/td><\/tr>'
    ), 'Geofabric River Region instance 9400216 html failed'


@pytest.mark.skip('Geofabric River Region instance 9400216 rdf turtle file extension not yet implemented')
def test_geofabric_riverregion_9400216_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216.ttl',
        None,
        r'<tr><td>HydroID<\/td><td><code>9400216<\/code><\/td><\/tr>'
    ), 'Geofabric River Region instance 9400216 rdf turtle file extension failed'


def test_geofabric_riverregion_9400216_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 rdf turtle qsa failed'


def test_geofabric_riverregion_9400216_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216',
        HEADERS_TTL,
        r'"Murray-Darling Basin" ;'
    ), 'Geofabric River Region instance 9400216 rdf turtle accept header failed'


def test_geofabric_riverregion_9400216_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=alternates&_format=html',
        None,
        r'<td><a href="http:\/\/geofabricld\.net\/riverregion\/9400216\?_view=geofabric">geofabric<\/a><\/td>'
    ), 'Geofabric River Region instance 9400216 alternates view html failed'


def test_geofabric_riverregion_9400216_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 alternates view rdf turtle qsa failed'


def test_geofabric_riverregion_9400216_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/geofabricld.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 alternates view rdf turtle accept header failed'


def test_geofabric_riverregion_9400216_geofabric_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=geofabric&_format=text/html',
        None,
        r'<h1>River Region 9400216<\/h1>'
    ), 'Geofabric River Region instance 9400216 geofabric view html failed'


def test_geofabric_riverregion_9400216_geofabric_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=geofabric&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 geofabric view rdf turtle qsa failed'


def test_geofabric_riverregion_9400216_geofabric_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=geofabric',
        HEADERS_TTL,
        r'<http:\/\/geofabricld.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 geofabric view rdf turtle accept header failed'


@pytest.mark.skip('Geofabric River Region instance 9400216 schemaorg view rdf application/ld+json not yet implemented')
def test_geofabric_riverregion_9400216_schemaorg_view_rdf_json():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=schemaorg&_format=application/ld+json',
        None,
        None #TODO
    ), 'Geofabric River Region instance 9400216 schemaorg view rdf application/ld+json failed'


def test_geofabric_riverregion_9400216_hyfeatures_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=hyfeatures&_format=text/html',
        None,
        r'<h1>River Region 9400216<\/h1>'
    ), 'Geofabric River Region instance 9400216 hyfeatures view html failed'


def test_geofabric_riverregion_9400216_hyfeatures_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=hyfeatures&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 hyfeatures view rdf turtle qsa failed'


def test_geofabric_riverregion_9400216_hyfeatures_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/riverregion/9400216?_view=hyfeatures',
        None,
        r'<http:\/\/geofabricld.net\/riverregion\/9400216>'
    ), 'Geofabric River Region instance 9400216 hyfeatures view rdf turtle accept header failed'


def test_geofabric_drainagedivision_register_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/',
        None,
        r'<li><a href="\/drainagedivision\/9400203">9400203<\/a><\/li>'
    ), 'Geofabric Drainage Division Register html failed'


def test_geofabric_drainagedivision_register_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric Drainage Division Register rdf turtle qsa failed'


@pytest.mark.skip('Geofabric Drainage Division Register rdf turtle file extension not yet implemented')
def test_geofabric_drainagedivision_register_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/index.ttl',
        None,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric Drainage Division Register rdf turtle file extension failed'


def test_geofabric_drainagedivision_register_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/',
        HEADERS_TTL,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric Drainage Division Register rdf turtle accept header failed'


def test_geofabric_drainagedivision_register_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_view=alternates&_format=text/html',
        None,
        r'<td><a href="http:\/\/geofabricld\.net\/drainagedivision\/\?_view=alternates">alternates<\/a><\/td>'
    ), 'Geofabric Drainage Division Register alternates view html failed'


def test_geofabric_drainagedivision_register_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_view=alternates&_format=text/turtle',
        None,
        r'rdfs:label "Alternates"\^\^xsd:string ;'
    ), 'Geofabric Drainage Division Register alternates view rdf turtle qsa failed'


def test_geofabric_drainagedivision_register_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_view=alternates',
        HEADERS_TTL,
        r'rdfs:label "Alternates"\^\^xsd:string ;'
    ), 'Geofabric Drainage Division Register alternates view rdf turtle accept header failed'


def test_geofabric_drainagedivision_register_reg_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_view=reg',
        None,
        r'<li><a href="\/drainagedivision\/9400203">9400203<\/a><\/li>'
    ), 'Geofabric Drainage Division Register reg view html failed'


def test_geofabric_drainagedivision_register_reg_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_view=reg&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric Drainage Division Register reg view rdf turtle qsa failed'


def test_geofabric_drainagedivision_register_reg_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/?_view=reg',
        HEADERS_TTL,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203> a <https:\/\/www\.opengis\.net\/def\/appschema\/hy_features\/hyf\/HY_CatchmentAggregate> ;'
    ), 'Geofabric Drainage Division Register reg view rdf turtle accept header failed'


def test_geofabric_drainagedivision_9400203_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203',
        None,
        r'<h1>AWRA Drainage Division 9400203<\/h1>'
    ), 'Geofabric Drainage Division instance 9400203 html failed'


@pytest.mark.skip('Geofabric Drainage Division instance 9400203 rdf turtle file extension not yet implemented')
def test_geofabric_drainagedivision_9400203_rdf_turtle_file_extension():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203.ttl',
        None,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 rdf turtle file extension failed'


def test_geofabric_drainagedivision_9400203_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 rdf turtle qsa failed'


def test_geofabric_drainagedivision_9400203_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203',
        HEADERS_TTL,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 rdf turtle accept header failed'


def test_geofabric_drainagedivision_9400203_geofabric_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=geofabric&_format=text/html',
        None,
        r'<h1>AWRA Drainage Division 9400203<\/h1>'
    ), 'Geofabric Drainage Division instance 9400203 geofabric view html failed'


def test_geofabric_drainagedivision_9400203_geofabric_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=geofabric&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 geofabric view rdf turtle qsa failed'


def test_geofabric_drainagedivision_9400203_geofabric_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=geofabric',
        HEADERS_TTL,
        r'<http:\/\/geofabricld\.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 geofabric view rdf turtle accept header failed'


@pytest.mark.skip('Geofabric Drainage Division instance 9400203 schemaorg view rdf application/ld+json not yet implemented')
def test_geofabric_drainagedivision_9400203_schemaorg_view_rdf_json():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=schemaorg&_format=application/ld+json',
        None,
        None #TODO
    ), 'Geofabric Drainage Division instance 9400203 schemaorg view rdf application/ld+json failed'


def test_geofabric_drainagedivision_9400203_alternates_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=alternates&_format=text/html',
        None,
        r'<h1>Geofabric Linked Data API<\/h1>'
    ), 'Geofabric Drainage Division instance 9400203 alternates view html failed'


def test_geofabric_drainagedivision_9400203_alternates_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=alternates&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 alternates view rdf turtle qsa failed'


def test_geofabric_drainagedivision_9400203_alternates_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=alternates',
        HEADERS_TTL,
        r'<http:\/\/geofabricld.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 alternates view rdf turtle accept header failed'


def test_geofabric_drainagedivision_9400203_hyfeatures_view_html():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=hyfeatures&_format=text/html',
        None,
        r'<h1>AWRA Drainage Division 9400203<\/h1>'
    ), 'Geofabric Drainage Division instance 9400203 hyfeatures view html failed'


def test_geofabric_drainagedivision_9400203_hyfeatures_view_rdf_turtle_qsa():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=hyfeatures&_format=text/turtle',
        None,
        r'<http:\/\/geofabricld.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 hyfeatures view rdf turtle qsa failed'


def test_geofabric_drainagedivision_9400203_hyfeatures_view_rdf_turtle_accept_header():
    assert valid_endpoint_content(
        f'{SYSTEM_URI}/drainagedivision/9400203?_view=hyfeatures',
        HEADERS_TTL,
        r'<http:\/\/geofabricld.net\/drainagedivision\/9400203>'
    ), 'Geofabric Drainage Division instance 9400203 hyfeatures view rdf turtle accept header failed'


if __name__ == '__main__':
    pass