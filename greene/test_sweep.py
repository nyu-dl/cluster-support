import torch
import fire
import itertools
import numpy


def retreve_config(sweep_step):
    grid = {
        "lr": [0.1, 0.01],
        "model_size": [512, 1024],
        "seed": numpy.random.randint(0, 1000, 5),
    }

    grid_setups = list(
        dict(zip(grid.keys(), values)) for values in itertools.product(*grid.values())
    )
    step_grid = grid_setups[sweep_step - 1]  # slurm var will start from 1

    # automatically choose the device based on the given node
    if torch.cuda.device_count() > 0:
        expr_device = "cuda"
    else:
        expr_device = "cpu"

    config = {
        "sweep_step": sweep_step,
        "seed": step_grid["seed"],
        "device": expr_device,
        "lr": step_grid["lr"],
        "model_size": step_grid["model_size"],
        "some_fixed_arg": 0,
    }

    return config


def run_experiment(config):
    print(config)


def main(sweep_step):
    config = retreve_config(sweep_step)
    run_experiment(config)


if __name__ == "__main__":
    fire.Fire(main)