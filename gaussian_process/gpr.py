#!/usr/bin/env python3
"""
Gaussian Process Regression Surrogate Model for Predicting Thermodynamic Equilibrium Properties

This script implements:
  1. Data processing: Reads and normalizes data from a CSV file.
  2. GPR models using PyTorch and GPyTorch for predicting:
       - Gibbs energies for each phase.
       - Phase stability (as a regression output in [0,1], which can be interpreted as a probability).
  3. Chemical potentials: Computed as the gradient (with respect to compositions)
     of the predicted Gibbs energies.
  4. Flexibility: The number of phases and constituents can be adjusted by modifying the
     global variables below.
  5. Training, validation, and visualization (parity plots, residual analyses).
  6. A prediction interface for new inputs.
  7. Ternary phase diagram plotting (if the number of constituents is 3).

Dependencies:
  - Python 3.x
  - PyTorch (e.g., v1.9.0 or later)
  - GPyTorch (e.g., v1.4.0 or later)
  - scikit-learn
  - pandas
  - matplotlib
  - (Optional) python-ternary for ternary diagram plotting

CSV file structure:
  Columns must include:
    - Composition columns: "Comp1", "Comp2", ..., "CompN"
    - Temperature: "Temperature"
    - Gibbs energies: "Gibbs_phase1", "Gibbs_phase2", ..., "Gibbs_phaseM"
    - Chemical potentials: "ChemPot1", "ChemPot2", ..., "ChemPotN"
    - Stability indicators: "Stability_phase1", "Stability_phase2", ..., "Stability_phaseM"
"""

import os
import numpy as np
import pandas as pd
import torch
import gpytorch
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Optionally import ternary for ternary phase diagram plotting.
try:
    import ternary
except ImportError:
    ternary = None
    print("python-ternary is not installed. Ternary phase diagram plotting will be disabled.")

# ----------------------------
# Global Settings & Hyperparameters
# ----------------------------
# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Define the number of phases and constituents (change these as needed)
NUM_PHASES = 2         # e.g., two phases in the system
NUM_CONST = 3          # e.g., three constituents (required for ternary plot)

# Constituent names for labeling (should match number of constituents)
constituent_names = ["A", "B", "C"]

# Hyperparameters for GP training
LEARNING_RATE = 0.1
TRAINING_ITER = 1000  # Number of training iterations for each GP
TEST_SIZE = 0.4       # Fraction of data used for validation

# ----------------------------
# Data Processing Functions
# ----------------------------
def load_and_preprocess_data(csv_file):
    """
    Load data from CSV and preprocess it.

    The CSV must have columns:
      - Composition columns: "Comp1", "Comp2", ..., "Comp{NUM_CONST}"
      - Temperature: "Temperature"
      - Gibbs energies: "Gibbs_phase1", "Gibbs_phase2", ..., "Gibbs_phase{NUM_PHASES}"
      - Chemical potentials: "ChemPot1", "ChemPot2", ..., "ChemPot{NUM_CONST}"
      - Stability indicators: "Stability_phase1", "Stability_phase2", ..., "Stability_phase{NUM_PHASES}"

    Returns:
      X: Normalized input features as torch.Tensor
         (Composition and Temperature; total dimension = NUM_CONST + 1)
      Y_gibbs: Dictionary of torch.Tensors for Gibbs energies (one per phase)
      Y_stability: Dictionary of torch.Tensors for phase stability (one per phase)
      raw_df: Original pandas DataFrame (for potential later use in plotting)
      input_scaler: Scaler fitted on input features (for new predictions)
      output_scalers: Dictionary of scalers for each output property (if needed)
    """
    # Read CSV using pandas
    df = pd.read_csv(csv_file)

    # Check for required columns
    required_columns = [f"Comp{i+1}" for i in range(NUM_CONST)] + ["Temperature"]
    required_columns += [f"Gibbs_phase{i+1}" for i in range(NUM_PHASES)]
    required_columns += [f"ChemPot{i+1}" for i in range(NUM_CONST)]
    required_columns += [f"Stability_phase{i+1}" for i in range(NUM_PHASES)]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"The following required columns are missing in the CSV: {missing_cols}")

    # Extract input features: compositions and temperature
    X = df[[f"Comp{i+1}" for i in range(NUM_CONST)] + ["Temperature"]].values
    # Standardize inputs
    input_scaler = StandardScaler()
    X_norm = input_scaler.fit_transform(X)

    # Prepare outputs for Gibbs energies and stability for each phase
    Y_gibbs = {}
    Y_stability = {}
    for i in range(NUM_PHASES):
        phase = f"phase{i+1}"
        Y_gibbs[phase] = df[f"Gibbs_{phase}"].values.reshape(-1, 1)
        # For stability, if using regression we assume the values are in [0,1] or can be scaled accordingly
        Y_stability[phase] = df[f"Stability_{phase}"].values.reshape(-1, 1)

    # Optionally, you can also store chemical potentials from CSV (though we will compute them via autograd)
    # For this script, we assume they are provided in the CSV for validation purposes.
    Y_chempot = {}
    for i in range(NUM_CONST):
        Y_chempot[f"const{i+1}"] = df[f"ChemPot{i+1}"].values.reshape(-1, 1)

    # Convert to torch tensors
    X_tensor = torch.tensor(X_norm, dtype=torch.float32)
    Y_gibbs_tensor = {phase: torch.tensor(Y, dtype=torch.float32).squeeze() for phase, Y in Y_gibbs.items()}
    Y_stability_tensor = {phase: torch.tensor(Y, dtype=torch.float32).squeeze() for phase, Y in Y_stability.items()}

    return X_tensor, Y_gibbs_tensor, Y_stability_tensor, Y_chempot, df, input_scaler

# ----------------------------
# GP Model Definitions
# ----------------------------
class RegressionGPModel(gpytorch.models.ExactGP):
    """
    Standard GP Regression Model using an RBF kernel.
    This model will be used for predicting continuous outputs (Gibbs energies and stability as regression).
    """
    def __init__(self, train_x, train_y, likelihood):
        super(RegressionGPModel, self).__init__(train_x, train_y, likelihood)
        # Mean and covariance modules can be easily swapped/tuned.
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

# ----------------------------
# Training Functions
# ----------------------------
def train_regression_model(model, likelihood, train_x, train_y, training_iter=TRAINING_ITER):
    """
    Train the GP regression model.
    """
    model.train()
    likelihood.train()

    # Use the Adam optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    # Marginal log likelihood
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

    for i in range(training_iter):
        optimizer.zero_grad()
        output = model(train_x)
        loss = -mll(output, train_y)
        loss.backward()
        if (i+1) % 10 == 0:
            print(f"Iter {i+1}/{training_iter} - Loss: {loss.item():.3f}")
        optimizer.step()
    return model

# ----------------------------
# Prediction & Chemical Potential Computation
# ----------------------------
def predict_with_model(model, likelihood, test_x):
    """
    Make predictions with a trained GP regression model.
    Returns the predictive mean.
    """
    model.eval()
    likelihood.eval()
    with torch.no_grad(), gpytorch.settings.fast_pred_var():
        preds = likelihood(model(test_x))
    return preds.mean

def compute_chemical_potentials(model, x, comp_indices=range(NUM_CONST)):
    """
    Compute chemical potentials as the gradients (with respect to composition variables)
    of the predicted Gibbs energy.

    Parameters:
      model: Trained RegressionGPModel for a given phase.
      x: Input tensor (normalized) for which predictions are made. It should require grad.
         The first NUM_CONST columns are assumed to be the composition variables.
      comp_indices: indices corresponding to composition columns.

    Returns:
      grad: Tensor containing the gradients (chemical potentials) with respect to each composition.
    """
    # Ensure x requires grad
    x = x.clone().detach().requires_grad_(True)
    output = model(x)
    # We compute gradient of the predictive mean with respect to composition inputs
    grads = []
    # For each sample compute the gradient with respect to its composition portion
    for i in range(x.shape[0]):
        # output[i] is a scalar
        grad_i = torch.autograd.grad(outputs=output.mean[i], inputs=x, retain_graph=True, create_graph=True)[0][i, :NUM_CONST]
        grads.append(grad_i.unsqueeze(0))
    grads = torch.cat(grads, dim=0)
    return grads

# ----------------------------
# Visualization Functions
# ----------------------------
def plot_parity(true_vals, pred_vals, title="Parity Plot", ylabel="Value"):
    """
    Create a parity plot comparing true vs predicted values.
    """
    plt.figure(figsize=(6,6))
    plt.scatter(true_vals, pred_vals, alpha=0.6)
    lims = [min(true_vals.min(), pred_vals.min()), max(true_vals.max(), pred_vals.max())]
    plt.plot(lims, lims, 'k--', alpha=0.75)
    plt.xlabel("True values")
    plt.ylabel("Predicted values")
    plt.title(title)
    plt.grid(True)
    plt.show()

def plot_residuals(true_vals, pred_vals, title="Residual Plot"):
    """
    Plot residuals (true - predicted).
    """
    residuals = true_vals - pred_vals
    plt.figure(figsize=(6,4))
    plt.scatter(pred_vals, residuals, alpha=0.6)
    plt.axhline(0, color='black', linestyle='--')
    plt.xlabel("Predicted values")
    plt.ylabel("Residuals")
    plt.title(title)
    plt.grid(True)
    plt.show()

def plot_ternary_phase_diagram(df, phase, constituent_names):
    """
    Plot a ternary phase diagram for a given phase's Gibbs energy.

    Parameters:
      df: pandas DataFrame containing the original data with columns 'Comp1', 'Comp2', 'Comp3'
          and a Gibbs energy column (e.g., 'Gibbs_phase1').
      phase: string identifier for the phase (e.g., "phase1").
      constituent_names: list of three names for the ternary corners.

    This function uses the python-ternary package.
    """
    if ternary is None:
        print("Ternary plotting is disabled because python-ternary is not installed.")
        return
    if NUM_CONST != 3:
        print("Ternary plot requires exactly 3 constituents.")
        return

    # Prepare data: each point is given as a tuple (Comp1, Comp2, Comp3, Gibbs_energy)
    points = []
    for idx, row in df.iterrows():
        comp = (row["Comp1"], row["Comp2"], row["Comp3"])
        gibbs = row[f"Gibbs_{phase}"]
        points.append((comp, gibbs))

    # Create figure and tax object
    scale = 1  # assuming compositions are fractions summing to 1
    figure, tax = ternary.figure(scale=scale)
    tax.set_title(f"Ternary Phase Diagram for {phase}", fontsize=15)

    # Draw boundary and gridlines
    tax.boundary(linewidth=2.0)
    tax.gridlines(multiple=0.1, color="gray")

    # Scatter the data points colored by Gibbs energy (using a colormap)
    comps = np.array([pt[0] for pt in points])
    gibbs_values = np.array([pt[1] for pt in points])
    sc = tax.scatter(comps, marker='o', color='blue', label="Data Points", s=50)

    # Set axis labels using constituent names
    tax.left_axis_label(constituent_names[0], fontsize=12)
    tax.right_axis_label(constituent_names[1], fontsize=12)
    tax.bottom_axis_label(constituent_names[2], fontsize=12)

    tax.legend()
    tax.ticks(axis='lbr', linewidth=1, multiple=0.1)
    tax.show()

# ----------------------------
# Prediction Interface Function
# ----------------------------
def predict_thermodynamic_properties(new_input, models_gibbs, models_stability, input_scaler):
    """
    Predict thermodynamic properties for new inputs.

    Parameters:
      new_input: numpy array or list of shape (n_samples, NUM_CONST + 1)
                 with the raw (unscaled) input features (compositions and temperature).
      models_gibbs: dictionary of trained GP models for Gibbs energies (keys like "phase1", etc.)
      models_stability: dictionary of trained GP models for phase stability.
      input_scaler: scaler used to normalize inputs.

    Returns:
      predictions: Dictionary containing predicted Gibbs energies, stability, and computed chemical potentials.
                   Chemical potentials are computed as gradients of the Gibbs energy with respect to compositions.
    """
    # Normalize new input using the previously fitted scaler
    new_input_norm = input_scaler.transform(new_input)
    new_input_tensor = torch.tensor(new_input_norm, dtype=torch.float32)

    predictions = {"Gibbs": {}, "Stability": {}, "ChemPot": {}}
    for phase, model in models_gibbs.items():
        # For chemical potentials computation, we need the input to require gradients.
        x_grad = new_input_tensor.clone().detach().requires_grad_(True)

        # Predict Gibbs energy
        model.eval()
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            gibbs_pred = model(x_grad).mean
        predictions["Gibbs"][phase] = gibbs_pred.detach().numpy()

        # Compute chemical potentials (only with respect to composition features, assumed to be first NUM_CONST columns)
        chempot = compute_chemical_potentials(model, x_grad)
        predictions["ChemPot"][phase] = chempot.detach().numpy()  # shape: (n_samples, NUM_CONST)

    for phase, model in models_stability.items():
        model.eval()
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            stability_pred = model(new_input_tensor).mean
        # For stability, apply a sigmoid to squash into [0,1]
        stability_prob = torch.sigmoid(stability_pred)
        predictions["Stability"][phase] = stability_prob.detach().numpy()

    return predictions

# ----------------------------
# Main Routine: Data Loading, Training, Evaluation, and Plotting
# ----------------------------
def main():
    # Path to CSV file (modify as needed)
    csv_file = "thermo_data.csv"  # Ensure this file exists with the proper structure.

    # Load and preprocess data
    X, Y_gibbs, Y_stability, Y_chempot, raw_df, input_scaler = load_and_preprocess_data(csv_file)

    # Split data into training and validation sets (same split for all models)
    train_idx, test_idx = train_test_split(np.arange(X.shape[0]), test_size=TEST_SIZE, random_state=42)
    train_x = X[train_idx]
    test_x = X[test_idx]

    models_gibbs = {}
    models_stability = {}
    likelihoods_gibbs = {}
    likelihoods_stability = {}

    # For each phase, create and train separate GP models
    for i in range(NUM_PHASES):
        phase = f"phase{i+1}"
        print(f"\nTraining GP model for Gibbs energy of {phase}")
        # Prepare training targets for Gibbs energy (squeeze to get 1D tensor)
        train_y_gibbs = Y_gibbs[phase][train_idx]

        # Create likelihood and model for regression
        likelihood = gpytorch.likelihoods.GaussianLikelihood()
        model = RegressionGPModel(train_x, train_y_gibbs, likelihood)
        model = train_regression_model(model, likelihood, train_x, train_y_gibbs)
        models_gibbs[phase] = model
        likelihoods_gibbs[phase] = likelihood

        print(f"\nTraining GP model for Stability of {phase}")
        # Prepare training targets for stability (regression version)
        train_y_stability = Y_stability[phase][train_idx]
        likelihood_stab = gpytorch.likelihoods.GaussianLikelihood()
        model_stab = RegressionGPModel(train_x, train_y_stability, likelihood_stab)
        model_stab = train_regression_model(model_stab, likelihood_stab, train_x, train_y_stability)
        models_stability[phase] = model_stab
        likelihoods_stability[phase] = likelihood_stab

    # ----------------------------
    # Evaluation on Validation Set
    # ----------------------------
    print("\nEvaluating models on validation set...")
    for i in range(NUM_PHASES):
        phase = f"phase{i+1}"
        # Gibbs energy predictions
        pred_gibbs = predict_with_model(models_gibbs[phase], likelihoods_gibbs[phase], test_x)
        true_gibbs = Y_gibbs[phase][test_idx].numpy()
        plot_parity(true_gibbs, pred_gibbs.numpy(), title=f"Gibbs Energy Parity Plot for {phase}")
        plot_residuals(true_gibbs, pred_gibbs.numpy(), title=f"Gibbs Energy Residuals for {phase}")

        # Stability predictions
        pred_stability = torch.sigmoid(predict_with_model(models_stability[phase], likelihoods_stability[phase], test_x))
        true_stability = Y_stability[phase][test_idx].numpy()
        plot_parity(true_stability, pred_stability.numpy(), title=f"Stability Parity Plot for {phase}", ylabel="Stability Probability")

    # ----------------------------
    # Prediction Example
    # ----------------------------
    # Here we define a new input sample (raw features: compositions and temperature)
    # For example, for NUM_CONST=3: [Comp1, Comp2, Comp3, Temperature]
    new_sample = np.array([[0.3, 0.4, 0.3, 1000.0]])
    predictions = predict_thermodynamic_properties(new_sample, models_gibbs, models_stability, input_scaler)
    print("\nPrediction for new sample:")
    for phase in predictions["Gibbs"]:
        print(f"Phase: {phase}")
        print("  Predicted Gibbs energy:", predictions["Gibbs"][phase])
        print("  Predicted chemical potentials (gradients wrt compositions):", predictions["ChemPot"][phase])
        print("  Predicted phase stability probability:", predictions["Stability"][phase])

    # ----------------------------
    # Ternary Phase Diagram Plotting
    # ----------------------------
    if NUM_CONST == 3:
        for i in range(NUM_PHASES):
            phase = f"phase{i+1}"
            print(f"\nPlotting ternary phase diagram for {phase} (using original data)")
            plot_ternary_phase_diagram(raw_df, phase, constituent_names)
    else:
        print("Ternary plot is available only for 3 constituents.")

if __name__ == "__main__":
    main()
