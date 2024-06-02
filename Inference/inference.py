import numpy as np
from scipy import signal
import pickle
from joblib import load
# from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from tensorflow.keras.models import load_model  # type: ignore
import pandas as pd


def preprocess_eeg(raw_input, sampling_freq=250, notch_freq=60, lowcut=0.5, highcut=30, scaling_factor=50e-6):
    """
    Preprocess EEG data by applying a notch filter and a bandpass filter,
    and scale the data to a specified range.

    Parameters:
    - X: numpy array, shape (trials, channels, samples)
        Input EEG data array.
    - sampling_freq: int, optional
        Sampling frequency of the EEG data in Hz (default: 250 Hz).
    - notch_freq: float, optional
        Frequency of the notch filter in Hz (default: 60 Hz).
    - lowcut: float, optional
        Low cutoff frequency of the bandpass filter in Hz (default: 0.5 Hz).
    - highcut: float, optional
        High cutoff frequency of the bandpass filter in Hz (default: 30 Hz).
    - scaling_factor: float, optional
        Scaling factor to adjust the amplitude range of the EEG data (default: 50e-6).

    Returns:
    - filtered_eeg_data: numpy array, shape (trials, channels, samples)
        Preprocessed EEG data after applying notch and bandpass filters,
        and scaling to the specified range.
    """
    # Design the notch filter
    Q = 30  # Quality factor
    b_notch, a_notch = signal.iirnotch(notch_freq, Q, fs=sampling_freq)

    # Design the bandpass filter
    nyquist_freq = 0.5 * sampling_freq
    low = lowcut / nyquist_freq
    high = highcut / nyquist_freq
    b_bandpass, a_bandpass = signal.butter(4, [low, high], btype='band')

    # Initialize filtered EEG data array
    filtered_eeg_data = np.zeros_like(raw_input)

    # Apply notch and bandpass filters to each trial and channel
    for trial in range(raw_input.shape[0]):
        for channel in range(raw_input.shape[1]):
            # Apply notch filter
            eeg_notch_filtered = signal.filtfilt(b_notch, a_notch, raw_input[trial, channel, :])
            # Apply bandpass filter
            filtered_eeg_data[trial, channel, :] = signal.filtfilt(b_bandpass, a_bandpass, eeg_notch_filtered)

    # Scale the filtered EEG data to ±50 µV
    filtered_eeg_data *= scaling_factor

    return filtered_eeg_data


def load_models(xgb_pkl_path:str = "Inference/xgb_model.pkl", scaler_path:str='Inference/minmaxscaling.pkl',label_encoder_path:str='Inference/label_encoder.pkl',auto_encoder_path:str='Inference/encoder_model.h5'):
    # Load XGBoost model
    with open(xgb_pkl_path, 'rb') as f:
        loaded_xgb = pickle.load(f)

    # Load scaler and label encoder
    scaler = load(scaler_path)
    label_encoder = load(label_encoder_path)

    # Load autoencoder model
    loaded_autoencoder = load_model(auto_encoder_path)
    return loaded_xgb, scaler, label_encoder, loaded_autoencoder


def Inference(raw_input:np.ndarray,loaded_xgb, scaler, label_encoder, loaded_autoencoder):
    # Assuming X is your EEG data array, shape (trials, channels, samples)
    EEG_data = preprocess_eeg(raw_input)

    # Reshape EEG data for autoencoder input
    EEG_reshaped = EEG_data.reshape(EEG_data.shape[0], -1)

    # Use autoencoder to predict decoded EEG data
    decoded_EEG_data = loaded_autoencoder.predict(EEG_reshaped)

    # Transform decoded data using the loaded scaler
    X_scaled = scaler.transform(decoded_EEG_data)

    # Predict using XGBoost model
    y_pred_encoded = loaded_xgb.predict(X_scaled)

    # Inverse transform predictions using label encoder
    predictions = label_encoder.inverse_transform(y_pred_encoded)

    # Example usage or further processing with predictions
    print("Predictions:")
    print(predictions)
    return predictions

if __name__ == '__main__':
    eegCSV = pd.read_csv("Inference/test_input/Antony-2024-03-30-11-41-14.csv")
    # eegCSV = eegCSV.loc[:,'EEG 1':'EEG 8']
    print(eegCSV['State'].unique())
    TIME_STAMP = 1200
    state_groups = eegCSV.groupby((eegCSV['State'] != eegCSV['State'].shift()).cumsum())
    included_states = ['Left']
    s =[]
    for _, data in state_groups:
        state = data['State'].iloc[0]
        if state in included_states:
            eeg_data = np.transpose(data[['EEG 1', 'EEG 2', 'EEG 3', 'EEG 4', 'EEG 5', 'EEG 6', 'EEG 7', 'EEG 8']].values)[:,:TIME_STAMP]

            if eeg_data.shape[1] < TIME_STAMP:
                pad_width = TIME_STAMP - eeg_data.shape[1]
                eeg_data = np.pad(eeg_data, ((0, 0), (0, pad_width)), mode='constant', constant_values=0)
            else:
                eeg_data = eeg_data[:, :TIME_STAMP]
            s.append(eeg_data)
    print(len(s), s[0].shape)

    # eegNP = eegCSV.to_numpy()
    eegNP = np.array(s)
    print(eegNP.shape)
    # eegNP = eegNP.reshape(1,8,-1)
    loaded_xgb, scaler, label_encoder, loaded_autoencoder = load_models()
    Inference(eegNP,loaded_xgb, scaler, label_encoder, loaded_autoencoder)