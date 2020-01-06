from os.path import dirname, realpath, join, abspath

APP_DIR = dirname(dirname(realpath(__file__)))
TEMPLATES_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'templates')
STATIC_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'static')
RR16CC_LINKSET_PATH = join(dirname(dirname(abspath(__file__))), 'data', 'ls_rr16cc.ttl')
LOGFILE = APP_DIR + '/flask.log'
DEBUG = True
#PAGE_SIZE = 10000

URI_BASE = "http://linked.data.gov.au"  # must _not_ end in a trailing slash
#DEF_URI_PREFIX = '/'.join([URI_BASE, 'def'])
DATA_URI_PREFIX = '/'.join([URI_BASE, 'dataset/geofabric'])

URI_CONTRACTED_CATCHMENT_CLASS = "https://www.opengis.net/def/appschema/hy_features/hyf/HY_Catchment"
URI_CATCHMENT_CLASS = "https://www.opengis.net/def/appschema/hy_features/hyf/HY_Catchment"
URI_RIVER_REGION_CLASS = "https://www.opengis.net/def/appschema/hy_features/hyf/HY_CatchmentAggregate"
URI_AWRA_DRAINAGE_DIVISION_CLASS = "https://www.opengis.net/def/appschema/hy_features/hyf/HY_CatchmentAggregate"
URI_CATCHMENT_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'contractedcatchment/'])
URI_CONTRACTED_CATCHMENT_INSTANCE_BASE = URI_CATCHMENT_INSTANCE_BASE
URI_RIVER_REGION_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'riverregion/'])
URI_AWRA_DRAINAGE_DIVISION_INSTANCE_BASE = '/'.join([DATA_URI_PREFIX, 'drainagedivision/'])

GF_OWS_ENDPOINT = "https://geofabricld.net/geoserver/ows"
GEOMETRY_SERVICE_HOST = "http://gds.loci.cat"
GEOMETRY_SERVICE_URI = '/'.join([GEOMETRY_SERVICE_HOST, "geometry/"])
