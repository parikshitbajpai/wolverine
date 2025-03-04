# %%
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

torch.set_default_dtype(torch.float32)

# %%
# select compute device
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using Metal")
else:
    if not torch.backends.mps.is_built():
        print("MPS not available because the current PyTorch install was not "
              "built with MPS enabled.")
    else:
        print("MPS not available because the current MacOS version is not 12.3+ "
              "and/or you do not have an MPS-enabled device on this machine.")

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        print("Using CUDA")

    else:
        device = torch.device("cpu")
        print("Using CPU")

# %%
model = torch.load('model_scripted.pt')

# %%
# Example with a tensor
x = torch.randn(2, requires_grad=True)

# Example with model parameters (check if they already have requires_grad=True)
for param in model.parameters():
    param.requires_grad_(True) # Inplace operation

# %%
output = model(x) # If x is the input
loss = torch.mean(output**2) # Example loss calculation


