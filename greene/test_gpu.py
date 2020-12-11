import torch
import time

if __name__ == "__main__":

    print(f"Torch cuda available: {torch.cuda.is_available()}")
    print(f"GPU name: {torch.cuda.get_device_name()}\n\n")

    t1 = torch.randn(100, 1000)
    t2 = torch.randn(1000, 10000)

    cpu_start = time.time()

    for i in range(100):
        t = t1 @ t2

    cpu_end = time.time()

    print(f"CPU matmul elapsed: {cpu_end-cpu_start} sec.")

    t1 = t1.to("cuda")
    t2 = t2.to("cuda")

    gpu_start = time.time()

    for i in range(100):
        t = t1 @ t2

    gpu_end = time.time()

    print(f"GPU matmul elapsed: {gpu_end-gpu_start} sec.")
