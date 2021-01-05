# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
"""
A script to run multinode training with submitit.
"""
import argparse
import os
import uuid
import copy
import itertools
from typing import Dict
from collections.abc import Iterable
from pathlib import Path

import main as detection
import submitit

def parse_args():
    detection_parser = detection.get_args_parser()
    parser = argparse.ArgumentParser("Submitit for detection", parents=[detection_parser])

    parser.add_argument("--ngpus", default=2, type=int, help="Number of gpus to request on each node")
    parser.add_argument("--nodes", default=2, type=int, help="Number of nodes to request")
    parser.add_argument("--timeout", default=3000, type=int, help="Duration of the job")
    parser.add_argument("--job_dir", default="", type=str, help="Job dir. Leave empty for automatic.")
    parser.add_argument("--mail", default="", type=str,
                        help="Email this user when the job finishes if specified")
    return parser.parse_args()


def get_shared_folder(args) -> Path:
    if Path('/scratch/{your_username}/experiments/').is_dir():
            p = Path('/scratch/{your_username}/experiments/')
            p.mkdir(exist_ok=True)
            return p

    raise RuntimeError("No shared folder available")

def get_init_file(args):
    # Init file must not exist, but it's parent dir must exist.
    os.makedirs(str(get_shared_folder(args)), exist_ok=True)
    init_file = get_shared_folder(args) / f"{uuid.uuid4().hex}_init"
    if init_file.exists():
        os.remove(str(init_file))
    return init_file


def grid_parameters(grid: Dict):
    """
    Yield all combinations of parameters in the grid (as a dict)
    """
    grid_copy = dict(grid)
    # Turn single value in an Iterable
    for k in grid_copy:
        if not isinstance(grid_copy[k], Iterable):
            grid_copy[k] = [grid_copy[k]]
    for p in itertools.product(*grid_copy.values()):
        yield dict(zip(grid.keys(), p))


def sweep(executor: submitit.Executor, args: argparse.ArgumentParser, hyper_parameters: Iterable):
    jobs = []
    with executor.batch():
        for grid_data in hyper_parameters:
            tmp_args = copy.deepcopy(args)
            tmp_args.dist_url = get_init_file(args).as_uri()
            tmp_args.output_dir = args.job_dir
            for k, v in grid_data.items():
                assert hasattr(tmp_args, k)
                setattr(tmp_args, k, v)
            trainer = Trainer(tmp_args)
            job = executor.submit(trainer)
            jobs.append(job)
    print('Sweep job ids:', [job.job_id for job in jobs])


class Trainer(object):
    def __init__(self, args):
        self.args = args

    def __call__(self):
        import os
        import sys
        import detection as detection

        self._setup_gpu_args()
        detection.main(self.args)

    def checkpoint(self):
        import os
        import submitit
        from pathlib import Path

        self.args.dist_url = get_init_file(self.args).as_uri()
        checkpoint_file = os.path.join(self.args.output_dir, "checkpoint.pth")
        if os.path.exists(checkpoint_file):
            self.args.resume = checkpoint_file
        print("Requeuing ", self.args)
        empty_trainer = type(self)(self.args)
        return submitit.helpers.DelayedSubmission(empty_trainer)

    def _setup_gpu_args(self):
        import submitit
        from pathlib import Path

        job_env = submitit.JobEnvironment()
        self.args.output_dir = Path(str(self.args.output_dir).replace("%j", str(job_env.job_id)))
        self.args.gpu = job_env.local_rank
        self.args.rank = job_env.global_rank
        self.args.world_size = job_env.num_tasks
        print(f"Process group: {job_env.num_tasks} tasks, rank: {job_env.global_rank}")


def main():
    args = parse_args()
    if args.job_dir == "":
        args.job_dir = get_shared_folder(args) / "%j"

    # Note that the folder will depend on the job_id, to easily track experimen`ts
    executor = submitit.AutoExecutor(folder=args.job_dir, slurm_max_num_timeout=30)

    # cluster setup is defined by environment variables
    num_gpus_per_node = args.ngpus
    nodes = args.nodes
    timeout_min = args.timeout
    kwargs = {}
    if args.use_volta32:
        kwargs['constraint'] = 'volta32gb'
    if args.comment:
        kwargs['comment'] = args.comment

    executor.update_parameters(
        mem_gb=40 * num_gpus_per_node,
        tasks_per_node=num_gpus_per_node,  # one task per GPU
        cpus_per_task=10,
        nodes=nodes,
        timeout_min=10080,  # max is 60 * 72
        # Below are cluster dependent parameters
        slurm_gres=f"gpu:rtx8000:{num_gpus_per_node}", #you can choose to comment this, or change it to v100 as per your need
        slurm_signal_delay_s=120,
        **kwargs
    )

    executor.update_parameters(name="detectransformer")
    if args.mail:
        executor.update_parameters(
            additional_parameters={'mail-user': args.mail, 'mail-type': 'END'})

    executor.update_parameters(slurm_additional_parameters={
        'gres-flags': 'enforce-binding'
    })

    args.dist_url = get_init_file(args).as_uri()
    args.output_dir = args.job_dir

    trainer = Trainer(args)
    job = executor.submit(trainer)

    print("Submitted job_id:", job.job_id)


if __name__ == "__main__":
    main()
