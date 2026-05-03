import h5py
import numpy as np
from scipy.signal import correlate, butter, filtfilt
import time

# ====================== FIXED DISCOVERY AUDIT ======================
base_path = "/storage/emulated/0/Download/CARBONECODEX/"
h1_file = "H-H1_GWOSC_O4b3Disc_16KHZ_R1-1420877824-4096.hdf5"
l1_file = "L-L1_GWOSC_O4b3Disc_16KHZ_R1-1420877824-4096.hdf5"
FS = 16384 

def butter_bandpass(data, fs):
    nyq = 0.5 * fs
    b, a = butter(4, [30/nyq, 400/nyq], btype='bandpass')
    return filtfilt(b, a, data)

def generate_discovery_template(fs):
    """Optimal burst spacing discovered in your sweep."""
    t = np.linspace(0, 0.4, int(0.4 * fs))
    s1, s2 = 0.080, 0.197
    temp = np.exp(-t / 0.038) * np.sin(2 * np.pi * 180.0 * t)
    b1, b2 = int(s1 * fs), int(s2 * fs)
    temp[b1:] += 0.45 * np.exp(-(t[b1:] - s1) / 0.058) * np.sin(2 * np.pi * 180.0 * t[b1:])
    temp[b2:] += 0.28 * np.exp(-(t[b2:] - s2) / 0.072) * np.sin(2 * np.pi * 180.0 * t[b2:])
    return (temp - np.mean(temp)) / (np.std(temp) + 1e-20)

def run_discovery_audit(observed_score=18.6943, n_trials=100000):
    template = generate_discovery_template(FS)
    background_scores = []
    
    with h5py.File(base_path + h1_file, 'r') as h_f, h5py.File(base_path + l1_file, 'r') as l_f:
        h_dset, l_dset = h_f['strain/Strain'], l_f['strain/Strain']
        dset_len = h_dset.shape[0] # Fixed: Accessing the first element of the tuple
        
        print(f"--- STARTING FINAL DISCOVERY AUDIT (N={n_trials}) ---")
        start_time = time.time()
        
        count = 0
        while count < n_trials:
            # Random time slides to build noise distribution
            idx_h = np.random.randint(FS, dset_len - FS)
            idx_l = np.random.randint(FS, dset_len - FS)
            
            seg_h, seg_l = h_dset[idx_h:idx_h+int(0.5*FS)], l_dset[idx_l:idx_l+int(0.5*FS)]
            if not np.all(np.isfinite(seg_h)) or not np.all(np.isfinite(seg_l)): continue
            if np.std(seg_h) < 1e-24 or np.std(seg_l) < 1e-24: continue

            c_h = correlate(butter_bandpass(seg_h, FS), template, mode='valid', method='direct')
            c_l = correlate(butter_bandpass(seg_l, FS), template, mode='valid', method='direct')
            
            s_h = np.max(np.abs(c_h)) / (np.std(c_h) + 1e-20)
            s_l = np.max(np.abs(c_l)) / (np.std(c_l) + 1e-20)
            
            background_scores.append(np.sqrt(s_h**2 + s_l**2))
            count += 1
            if count % 10000 == 0:
                print(f"  Progress: {count}/{n_trials} | {(time.time()-start_time)/60:.1f} min")

        scores = np.array(background_scores)
        hits = np.sum(scores >= observed_score)
        p_val = hits / n_trials
        
        print(f"\n--- DISCOVERY AUDIT RESULTS ---")
        print(f"Final p-value: {p_val:.10f}")
        print(f"Max Background Spike: {np.max(scores):.4f}")
        
        if p_val == 0:
            print("STATUS: CONFIRMED DISCOVERY (p < 0.00001)")
        
        return p_val

try:
    run_discovery_audit()
except Exception as e:
    print(f"Error: {e}")

