import math
import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.neural_network import MLPRegressor

data = pd.read_csv('Activities.csv')
Actual_Performance = data['performance'].values
TSS = data['TSS'].values

# Rolling averages for neural net
Offset_Performance = [np.mean(Actual_Performance[i:i+28]) for i in range(len(Actual_Performance)-27)]
Block_TSS = [np.mean(TSS[i:i+28]) for i in range(len(TSS)-27)]

# Individual Banister Model
def Banister(params):
    k1, k2, PO, CTLC, ATLC = params
    fitness = TSS * (1 - np.exp(-1/CTLC))
    fatigue = TSS * (1 - np.exp(-1/ATLC))
    Banister_Prediction = k1 * fitness + k2 * fatigue + PO
    loss = np.abs(Actual_Performance - Banister_Prediction)
    MAE = np.mean(loss)
    return MAE

initial_guess = [0.1, 0.5, 50, 45, 15]
result = optimize.minimize(Banister, initial_guess)
individual_banister_model = result

print("Individual Banister Model Coefficients:", individual_banister_model.x)

# Individual Neural Network Model
Block_TSS_np = np.array(Block_TSS).reshape(-1, 1)
Offset_Performance_np = np.array(Offset_Performance)
Individual_neural_net_model = MLPRegressor(solver='lbfgs', activation='relu', hidden_layer_sizes=[50], random_state=42)
Individual_neural_net_model.fit(Block_TSS_np, Offset_Performance_np)

def banister_recursive(params, TSS):
    k1, k2, PO, CTLC, ATLC = params
    fitness = np.zeros_like(TSS)
    fatigue = np.zeros_like(TSS)
    for i in range(1, len(TSS)):
        fitness[i] = fitness[i-1] + (TSS[i] - fitness[i-1]) / CTLC
        fatigue[i] = fatigue[i-1] + (TSS[i] - fatigue[i-1]) / ATLC
    prediction = k1 * fitness + k2 * fatigue + PO
    return prediction

def banister_loss(params):
    prediction = banister_recursive(params, TSS)
    return np.mean(np.abs(Actual_Performance - prediction))

result = optimize.minimize(banister_loss, initial_guess)