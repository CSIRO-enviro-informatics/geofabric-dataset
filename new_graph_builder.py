#!/usr/bin/env python3
#
import logging
import os
import sys
import pickle
import math
from threading import Thread
import rdflib
import pyldapi
import time
from pyldapi.exceptions import RegOfRegTtlError
from geofabric.helpers import NotFoundError
from geofabric.flask_app import app

# --- CONFIGURABLE OPTIONS
OUTPUT_DIRECTORY = "./instance"  # Relative path from pwd
INSTANCES_PER_FILE = 1000
HARVESTABLE_INSTANCE_VIEW = "hyfeatures"
MULTI_PROCESSING = True
MULTI_THREADING = True
USE_SAVED_REGISTER_INDEX = True
DEBUG_MODE = False # Does nothing for now.
VERBOSE_MODE = True
#TODO: Automate this, somehow.
INSTANCE_URI_TO_LOCAL_ROUTE = {
    "http://linked.data.gov.au/dataset/geofabric/catchment/": "/catchment/",
    "http://linked.data.gov.au/dataset/geofabric/riverregion/": "/riverregion/",
    "http://linked.data.gov.au/dataset/geofabric/drainagedivision/": "/drainagedivision/"
}
# -- END CONFIGURABLE OPTIONS
# ---------------------------


LOGGER = logging.getLogger("ldapi-harvester")
logging.basicConfig()
for h in LOGGER.handlers:
    LOGGER.removeHandler(h)
LOGGER.propagate = False

class ReverseLevelLogFilter(logging.Filter):
    def __init__(self, name="", level=logging.INFO):
        super(ReverseLevelLogFilter, self).__init__(name)
        self._level = level

    def filter(self, record):
        return record.levelno <= self._level


STD_FORMATTER = logging.Formatter(style='{')
STDOUT_H = logging.StreamHandler(sys.stdout)
STDOUT_H.setFormatter(STD_FORMATTER)
STDOUT_H.setLevel(logging.DEBUG)
STDOUT_H.addFilter(ReverseLevelLogFilter(level=logging.INFO))
STDERR_H = logging.StreamHandler(sys.stderr)
STDERR_H.setFormatter(STD_FORMATTER)
STDERR_H.setLevel(logging.WARNING)
LOGGER.addHandler(STDOUT_H)
LOGGER.addHandler(STDERR_H)
if DEBUG_MODE:
    LOGGER.setLevel(logging.DEBUG)
elif VERBOSE_MODE:
    LOGGER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.WARNING)

def info(message, *args, **kwargs):
    return LOGGER.info(message, *args, **kwargs)

def warn(message, *args, **kwargs):
    return LOGGER.warning(message, *args, **kwargs)

def err(message, *args, **kwargs):
    return LOGGER.error(message, *args, **kwargs)

def debug(message, *args, **kwargs):
    return LOGGER.debug(message, *args, **kwargs)


APP_ROFR = list()  # uri, rule, endpoint_func
APP_REGISTERS = list()  # uri, rule, endpoint_func

if MULTI_PROCESSING:
    from multiprocessing import Process as m_Worker
elif MULTI_THREADING:
    m_Worker = Thread
else:
    m_Worker = None


def request_register_query(uri, page=1, per_page=500):
    for _i in APP_REGISTERS:
        (r_uri, r_rule, r_endpoint_func) = _i
        if r_uri == str(uri):
            break
    else:
        raise RuntimeError("App does not have endpoint for uri: {}".format(uri))
    dummy_request_uri = "http://localhost:5000" + str(r_rule) +\
                     "?_view=reg&_format=_internal&per_page={}&page={}".format(per_page, page)
    test_context = app.test_request_context(dummy_request_uri)
    with test_context:
        resp = r_endpoint_func()

    try:
        return resp.register_items
    except AttributeError:
        raise NotFoundError()


def find_app_registers():
    for rule in app.url_map.iter_rules():
        if '<' not in str(rule):  # no registers can have a Flask variable in their path
            # make the register view URI for each possible register
            try:
                endpoint_func = app.view_functions[rule.endpoint]
            except (AttributeError, KeyError):
                continue
            try:
                dummy_request_uri = "http://localhost:5000" + str(rule) +\
                                    '?_view=reg&_format=_internal'
                test_context = app.test_request_context(dummy_request_uri)
                with test_context:
                    resp = endpoint_func()
                    if isinstance(resp, pyldapi.RegisterOfRegistersRenderer):
                        APP_ROFR.append((resp.uri, rule, endpoint_func))
                    elif isinstance(resp, pyldapi.RegisterRenderer):
                        APP_REGISTERS.append((resp.uri, rule, endpoint_func))
                    else:
                        pass
            except RegOfRegTtlError:  # usually an RofR renderer cannot find its rofr.ttl.
                raise Exception("Please generate rofr.ttl before running the graph_builder.")
            except Exception as e:
                raise e


def harvest_rofr():
    try:
        (r_uri, r_rule, r_endpoint_func) = APP_ROFR[0]
    except KeyError:
        raise RuntimeError("No RofR found in the App.")

    dummy_request_uri = "http://localhost:5000" + str(r_rule) +\
                        "?_view=reg&_format=_internal&per_page=500&page=1"
    test_context = app.test_request_context(dummy_request_uri)
    with test_context:
        resp = r_endpoint_func()
    if resp.register_items:
        registers = [r[0] for r in resp.register_items]
    else:
        raise NotImplementedError("TODO: Get registers directly from the returned graph.")
    return registers


def reg_uri_to_filename(reg_uri):
    return str(reg_uri).rstrip('/').replace("http://", "http_").replace("https://", "http_").replace("/","_").replace('#','')

def seconds_to_human_string(secs):
    """

    :param secs:
    :type secs: float
    :return:
    :rtype: string
    """
    whole_hours = math.floor(secs) // 3600
    secs = secs - (whole_hours*3600)
    whole_mins = math.floor(secs) // 60
    secs = secs - (whole_mins*60)
    return "{:d}H {:00d}M {:.1f}S".format(int(whole_hours), int(whole_mins), secs)


def _harvest_register_worker_fn(worker_index, reg_uri, instances, serial_chunk_size=INSTANCES_PER_FILE, **kwargs):
    endpoint_func = kwargs['endpoint_func']
    endpoint_rule = kwargs['endpoint_rule']
    replace_s = kwargs['replace_s']
    replace_r = kwargs['replace_r']
    n_instances = len(instances)
    assert n_instances > 0
    est_secs = -1
    avg_inst_secs = -1
    serial_groups = list(grouper(instances, serial_chunk_size))
    first_group = True
    total_instances_done = 0
    for iig, instance_s_group in enumerate(serial_groups):
        start_serial_group_time = time.perf_counter()
        info_message_pref = "P[{}] Wkr: {}  Set: {}/{},".format(str(os.getpid()), worker_index+1, iig+1, len(serial_groups))
        total_in_group = len(instance_s_group)
        with open("{}/{}_p{}_s{}.nt".format(OUTPUT_DIRECTORY, reg_uri_to_filename(reg_uri), str(worker_index+1), str(iig+1)),
                  'ab+') as inst_file:
            for iiig, inst in enumerate(instance_s_group):
                start_instance_time = 0 if first_group else time.perf_counter()
                local_instance_url = str(inst).replace(replace_s, replace_r)
                info_message = "{} Inst: {}/{}, ".format(info_message_pref, iiig+1, total_in_group)
                est_sfx = " First group - No est remaining." if first_group else " Wkr est {}".format(seconds_to_human_string(est_secs))
                info(info_message+local_instance_url+est_sfx)
                m = endpoint_rule.match("|" + local_instance_url)
                dummy_request_uri = "http://localhost:5000" + local_instance_url + \
                                    "?_view={:s}&_format=application/n-triples".format(HARVESTABLE_INSTANCE_VIEW)
                test_context = app.test_request_context(dummy_request_uri)
                try:
                    if len(m) < 1:
                        with test_context:
                            resp = endpoint_func()
                    else:
                        with test_context:
                            resp = endpoint_func(**m)
                except NotFoundError:
                    with open("{}_not_found.txt".format(reg_uri_to_filename(reg_uri)), 'a+') as nf:
                        nf.write("{}\n".format(dummy_request_uri))
                    continue
                except Exception as e:
                    import traceback
                    with open("{}_error.txt".format(reg_uri_to_filename(reg_uri)), 'a+') as nf:
                        nf.write("{}\n".format(dummy_request_uri))
                        nf.write("{}\n".format(repr(e)))
                        traceback.print_tb(e.__traceback__, file=nf)
                        nf.write('\n')
                    traceback.print_tb(e.__traceback__)  #to stderr
                    continue
                if isinstance(resp, pyldapi.Renderer):
                    resp.format = "application/n-triples"
                    resp = resp.render()
                if hasattr(resp, 'status_code') and hasattr(resp, 'data'):
                    assert resp.status_code == 200
                    if isinstance(resp.data, bytes):
                        data = resp.data
                    elif isinstance(resp.data, str):
                        data = resp.data.encode(encoding='utf-8')
                    else:
                        raise RuntimeError("response.data in the wrong format.")
                    inst_file.write(data)
                elif isinstance(resp, rdflib.Graph):
                    g = resp
                    g.serialize(destination=inst_file, format="nt")
                if first_group:
                    continue
                end_instance_time = time.perf_counter()
                instance_time = end_instance_time - start_instance_time
                if instance_time > 0:
                    avg_inst_secs = (avg_inst_secs + instance_time) / 2.0
                    instances_left = n_instances - total_instances_done
                    est_secs = avg_inst_secs * instances_left
            # End of per-instance processing
        end_serial_group_time = time.perf_counter()
        serial_group_time = end_serial_group_time - start_serial_group_time
        if first_group:
            avg_inst_secs = serial_group_time / total_in_group
            first_group = False
        else:
            this_avg = serial_group_time / total_in_group
            if this_avg > 0:
                avg_inst_secs = (avg_inst_secs + this_avg) / 2.0
        instances_left = n_instances - total_instances_done
        est_secs = avg_inst_secs * instances_left
    return True


def harvest_register(reg_uri):
    instances = []
    info("Process started harvesting: {}".format(reg_uri))
    if USE_SAVED_REGISTER_INDEX:
        try:
            with open("./index_{}.pickle".format(reg_uri_to_filename(reg_uri)), 'rb') as reg_pickle:
                instances = pickle.load(reg_pickle)
                save_register_index = False
        except FileNotFoundError:
            save_register_index = True
    else:
        save_register_index = False
    if (not USE_SAVED_REGISTER_INDEX) or save_register_index:
        page = 1
        while True:
            try:
                new_instances = request_register_query(reg_uri, page=page, per_page=1000)
                assert len(new_instances) > 0
                instances.extend([i[0] for i in new_instances])
                page += 1
            except (NotFoundError, AssertionError) as e:
                err(repr(e))
                break
        if len(instances) > 0 and save_register_index:
            with open("./index_{}.pickle".format(reg_uri_to_filename(reg_uri)), 'wb') as reg_pickle:
                pickle.dump(instances, reg_pickle)
    if len(instances) < 1:
        raise RuntimeError("Got no instances from reg uri: {}".format(reg_uri))
    first_instance = instances[0]

    for k in INSTANCE_URI_TO_LOCAL_ROUTE.keys():
        if first_instance.startswith(k):
            replace_s = k
            replace_r = INSTANCE_URI_TO_LOCAL_ROUTE[k]
            break
    else:
        raise RuntimeError("Cannot find a local route for that URI.")
    first_local_instance_url = str(first_instance).replace(replace_s, replace_r)
    for rule in app.url_map.iter_rules():
        m = rule.match("|"+first_local_instance_url)
        if m:
            endpoint_func = app.view_functions[rule.endpoint]
            endpoint_rule = rule
            break
    else:
        raise RuntimeError("No app rule matches that local route.")
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    if MULTI_THREADING:
        INSTANCE_PARALLEL = 8  # Running 8 threads in parallel
        n_instances = len(instances)
        extra = 1 if (n_instances % INSTANCE_PARALLEL) > 0 else 0
        # Each parallel thread gets total_instances / threads.
        # if there is remainder, give each thread one more.
        instance_groups = list(grouper(instances, (n_instances//INSTANCE_PARALLEL)+extra))
        t_workers = []
        for iig, instance_group in enumerate(instance_groups):
            _worker = Thread(target=_harvest_register_worker_fn, args=(iig, reg_uri, instance_group),
                             kwargs={'serial_chunk_size': INSTANCES_PER_FILE, 'endpoint_func':endpoint_func, 'endpoint_rule':endpoint_rule, 'replace_s': replace_s, 'replace_r': replace_r})
            _worker.start()
            t_workers.append(_worker)
        results = [_w.join() for _w in t_workers]
    else:
        results = []
        kwargs = {'serial_chunk_size': INSTANCES_PER_FILE, 'endpoint_func': endpoint_func, 'endpoint_rule': endpoint_rule,
                  'replace_s': replace_s, 'replace_r': replace_r}
        _r = _harvest_register_worker_fn(0, reg_uri, instances, **kwargs)
        results.append(_r)
    return results



##UTILS##
def grouper(iterable, n):
    assert is_iterable(iterable)
    if isinstance(iterable, (list, tuple)):
        return list_grouper(iterable, n)
    elif isinstance(iterable, (set, frozenset)):
        return set_grouper(iterable, n)

def list_grouper(iterable, n):
    assert isinstance(iterable, (list, tuple))
    assert n > 0
    iterable = iter(iterable)
    count = 0
    group = list()
    while True:
        try:
            group.append(next(iterable))
            count += 1
            if count % n == 0:
                yield tuple(group)
                group = list()
        except StopIteration:
            if len(group) < 1:
                raise StopIteration()
            else:
                yield tuple(group)
            break

def set_grouper(iterable, n):
    assert isinstance(iterable, (set, frozenset))
    assert n > 0
    iterable = iter(iterable)
    count = 0
    group = set()
    while True:
        try:
            group.add(next(iterable))
            count += 1
            if count % n == 0:
                yield frozenset(group)
                group = set()
        except StopIteration:
            if len(group) < 1:
                raise StopIteration()
            else:
                yield frozenset(group)
            break

def first(i):
    assert is_iterable(i)
    return next(iter(i))

def is_iterable(i):
    return isinstance(i, (list, set, tuple, frozenset))

if __name__ == '__main__':
    find_app_registers()
    if len(sys.argv) < 2:
        register = None
    else:
        register = sys.argv[1]
    if register is None:
        registers = harvest_rofr()
        if m_Worker:
            workers = []
            for i,r in enumerate(registers):
                t = m_Worker(target=harvest_register, args=(r,), name="worker"+str(i))
                t.start()
                workers.append(t)
            results = [_t.join() for _t in workers]
        else:
            results = []
            for r in registers:
                results.append(harvest_register(r))
    else:
        harvest_register(register)

