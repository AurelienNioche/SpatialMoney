import multiprocessing
import tqdm
import numpy as np
import os
import shutil
import json
import argparse
import glob
import pickle

import model

import analysis.separate
import analysis.summary

parameters_folder = "parameters"
template_folder = "template"
parameters_files = {
    "single": "{}/parameters_single.json".format(parameters_folder),
    "pool": "{}/parameters_pool.json".format(parameters_folder)
}


def run(parameters, multi=True):
    return model.run(multi=multi, **parameters)


def prepare():

    for v in parameters_files.values():
        if not os.path.exists(v):
            os.makedirs(os.path.dirname(v), exist_ok=True)
            shutil.rmtree(parameters_folder)
            shutil.copytree(template_folder, parameters_folder)
            break


def produce_data_pool():

    with open(parameters_files["pool"], "r") as f:
        pp = model.data_structure.ParametersPool(**json.load(f))

    np.random.seed(pp.seed)

    parameters_list = []

    seeds = np.random.randint(0, 2**32-1, size=pp.n)

    for i in range(pp.n):

        x = np.random.randint(pp.x_min, pp.x_max + 1)

        parameters_list.append(
            model.data_structure.Parameters(
                x0=x,
                x1=x,
                x2=x,
                stride=np.random.randint(pp.stride_min, pp.stride_max + 1),
                movement_area=np.random.randint(
                    pp.movement_area_min, pp.movement_area_max + 1),
                vision_area=np.random.randint(
                    pp.vision_area_min, pp.vision_area_max + 1
                ),
                alpha=np.random.uniform(
                  pp.alpha_min, pp.alpha_max
                ),
                tau=np.random.uniform(
                    pp.tau_min, pp.tau_max
                ),
                map_width=pp.map_width,
                map_height=pp.map_height,
                t_max=pp.t_max,
                seed=seeds[i],
                graphics=pp.graphics
            ).__dict__
        )

    pool = multiprocessing.Pool()

    backups = []

    for bkp in tqdm.tqdm(
            pool.imap_unordered(run, parameters_list),
            total=pp.n):
        backups.append(bkp)

    r = model.data_structure.ResultPool(data=backups, parameters=pp)
    r.save()
    return r


def produce_data_single():

    with open(parameters_files["single"], "r") as f:
        parameters = json.load(f)

    r = run(parameters, multi=False)
    r.save()

    return r


def main_pool(force):

    if not (os.path.exists("data/pickle") and glob.glob("data/pickle/pool*")) or force:
        r = produce_data_pool()

    else:
        data_file = sorted(glob.glob("data/pickle/pool*"))[-1]
        with open(data_file, "rb") as f:
            r = pickle.load(f)

    analysis.separate.plot_indirect_exchanges(data=r)
    analysis.summary.plot(data=r)


def main_single(force):

    if not (os.path.exists("data/pickle") and glob.glob("data/pickle/single*")) or force:
        r = produce_data_single()

    else:
        data_file = sorted(glob.glob("data/pickle/single*"))[-1]
        with open(data_file, "rb") as f:
            r = pickle.load(f)

    analysis.separate.plot_indirect_exchanges(data=r)


if __name__ == "__main__":

    # Setup things
    prepare()

    # Parse the arguments given in command line and call the 'main' function

    parser = argparse.ArgumentParser(description='Produce figures.')
    parser.add_argument('-s', '--single', action="store_true", default=False,
                        help="Run single simulation")
    parser.add_argument('-f', '--force', action="store_true", default=False,
                        help="Run simulations even if data already exist")
    parsed_args = parser.parse_args()

    if parsed_args.single:
        main_single(parsed_args.force)
    else:
        main_pool(parsed_args.force)
