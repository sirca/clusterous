import os
import csv
import datetime
import logging
import time
import json

import yaml
import datastorewrapper
from IPython.parallel import Client

# Folders
if not os.path.exists('logs'): os.makedirs('logs')
if not os.path.exists('results'): os.makedirs('results')

# Logger
LOGS_FILE = 'logs/laser.log'
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
handler = logging.FileHandler(LOGS_FILE)
handler.setLevel(logging.INFO)
LOGGER.addHandler(handler)

   
# Donwload files using datastorewrapper
def ds_download_files(ds_repo, ds_resource):
    file_type = None
    raw_files_dir = None
    
    datastore = datastorewrapper.Datastore()
    repo_files = datastore.files(ds_repo, ds_resource)
    if repo_files:
        line1 = repo_files[0]
        raw_files_dir = "/".join(line1.split("/")[:-1])
        file_type = line1.split('.')[-1:][0]
        
    return raw_files_dir, file_type

# Util for forloop
def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

# Get jobs list
def get_jobs_list(ds_repo, ds_resource):
    # Download files
    raw_files_dir, file_type = ds_download_files(ds_repo, ds_resource)
    if raw_files_dir is None:
        return None

    # Parameters: (TODO: It should come from metadata)
    # x, y: Values for x and y in the form of [from, to]
    # m: order of permutation entropy (e.g. 5)
    # t: delay of permutation entropy (e.g. 2)
    x = [0, 1, 1]  # phase sectin current [start, stop, step]
    y = [15, 16, 0.1]  # dfb injection current [start, stop, step]
    z = [9, 10, 0.1]   # g/a section current [start, stop, step]
    m = 3
    t = 2

    n = 0
    jobs_list = []
    for pha in drange(x[0], x[1], x[2]):
        for dfb in drange(y[0], y[1], y[2]):
            for gas in drange(z[0], z[1], z[2]):
                i = "{0:05.2f}-{1:05.2f}-{2:05.2f}".format(pha, dfb, gas)
                job_data = {"raw_files_dir": raw_files_dir, "file_type": file_type, 
                            "pha": pha, "dfb": dfb, "gas": gas, "m": m, "t": t}
                jobs_list.append(job_data)
                n += 1
                if n > 2:
                    break
    return jobs_list

def worker(job_data):
    import os
    import h5py
    import numpy as np
    
    # Read parameters
    raw_files_dir = job_data.get("raw_files_dir")
    file_type = job_data.get("file_type")
    pha = job_data.get("pha")
    dfb = job_data.get("dfb")
    gas = job_data.get("gas")
    m = job_data.get("m")
    t = job_data.get("t")

    pe = 0
    w_pe = 0
    filename = '{0}/IPH{1:05.2f}DFB{2:05.2f}GAS{3:05.2f}.{4}'.format(raw_files_dir, pha, dfb, gas, file_type)
    if os.path.exists(filename):
        raw_data = []
        with h5py.File(filename) as h5f:
            for ds in h5f:
                for row in h5f[ds][()]:
                    raw_data.append(float(row[0]))


        perms = dict()
        w_perms = dict()
        for a in range(len(raw_data) - t*(m-1)):
            v = tuple(np.argsort(raw_data[a:(a + t*(m-1) + 1):t]))
            w = (1/m)*np.sum(((raw_data[a:(a + t*(m-1) + 1):t]) - np.mean(raw_data[a:(a + t*(m-1) + 1):t]))**2)
            if v in perms:
                perms[v] += 1
                w_perms[v] += 1*w
            else:
                perms[v] = 1
                w_perms[v] = w

        c = np.array(list(perms.values()))
        w_c = np.array(list(w_perms.values()))
        p = c / float(np.sum(c))
        w_p = w_c / float(np.sum(w_c))
        pe = -np.sum(np.dot(p, np.log(p)))
        w_pe = -np.sum(np.dot(w_p, np.log(w_p)))
        pe = pe / np.log(np.math.factorial(m))
        w_pe = w_pe / np.log(np.math.factorial(m))

    # Update results
    job_results = {'pha': round(pha,1), 'dfb': round(dfb,1), 'gas': round(gas,1), 'pe': pe, 'w_pe': w_pe}

    return job_results


# Main
def main():
    # Get jobs list
    LOGGER.info("Geting jobs list")
    ds_repo = "bdkd-laser-public"
    ds_resource = "Multisection_SL_test"
    jobs_list = get_jobs_list(ds_repo, ds_resource)
    if jobs_list is None:
        print 'No files found. Something is wrong with "{0}" dataset'.format(ds_resource)
        return

    # Ipython parallel setup
    profile_dir = "/home/data/files/profile"
    rc = Client(profile_dir=profile_dir)
    dview = rc.direct_view()
    dview.block=False

    # Scheduling jobs
    LOGGER.info("Scheduling: {0} jobs".format(len(jobs_list)))
    jobs_sent = dview.map(worker, jobs_list)
    time.sleep(1)

    # Waiting for results
    LOGGER.info("Waiting for results")
    dview.wait(jobs_sent)

    # Collecting results
    LOGGER.info("Collecting results")
    wip_simulations = jobs_sent.get()
    list_pe = []
    for i in wip_simulations:
        list_pe.append((i.get('pha'), i.get('dfb'), i.get('gas'), i.get('pe'), i.get('wpe')))

    # Save results to csv file
    results_file = "results/results_{0}.csv".format(ds_resource.replace(" ", "").replace("/", "_"))
    LOGGER.info("Saving results into: {0}".format(results_file))
    with open(results_file, 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(('pha', 'dfb', 'gas', 'pe', 'wpe'))
        a.writerows(list_pe)

# 2 processors, 0.25 cpu each
# dview.block=True
#
# Run
t1 = datetime.datetime.now()
a = main()
t2 = datetime.datetime.now()
LOGGER.info("Time taken = %s " % (t2-t1))
