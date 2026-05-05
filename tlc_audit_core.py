MASTER SCRIPT



import h5py
import numpy as np
import os
from scipy.signal import coherence, csd

# Path verified by previous diagnostics
BASE_PATH = "/storage/emulated/0/Download/CARBONECODEX/"

def get_data(f):
    """Dynamic path handler for LIGO (Strain), Virgo (recalibrated), and GEO600."""
    for path in ['strain/Strain', 'strain', 'recalibrated/strain']:
        if path in f: return f[path][:]
    return None

def audit_peak_window(data1, data2, fs=16384):
    """Deep Scan: Finds highest coherence window to identify the 'Handshake'."""
    window = 32 * fs
    max_coh, best_phase, best_time = 0, 0, 0
    # Clean non-finite data (NaNs) which crash standard filters
    mask = np.isfinite(data1) & np.isfinite(data2)
    d1_c, d2_c = data1[mask], data2[mask]
    
    for i in range(0, len(d1_c) - window, window):
        chunk1, chunk2 = d1_c[i:i+window], d2_c[i:i+window]
        f, Cxy = coherence(chunk1, chunk2, fs=fs, nperseg=fs)
        idx = np.argmin(np.abs(f - 180.0))
        if Cxy[idx] > max_coh:
            max_coh = Cxy[idx]
            best_time = i / fs
            # Extract Phase Offset at the exact peak moment
            f_p, Pxy = csd(chunk1, chunk2, fs=fs, nperseg=fs)
            best_phase = np.angle(Pxy[idx], deg=True)
    return max_coh, best_phase, best_time

def run_hardware_audit():
    # Era mapping using confirmed filenames in your directory
    audit_plan = {
        "2017 GLOBAL": [
            ("L1 <-> H1", "L-L1_LOSC_C00_16_V1-1187006834-4096.hdf5", "H-H1_LOSC_C00_16_V1-1187006834-4096.hdf5"),
            ("L1 <-> G1", "L-L1_LOSC_C00_16_V1-1187006834-4096.hdf5", "G-G1_LOSC_C00_16_V1-1187006834-4096.hdf5")
        ],
        "2025 EVOLUTION": [
            ("L1 <-> H1", "L-L1_GWOSC_O4b3Disc_16KHZ_R1-1420877824-4096.hdf5", "H-H1_GWOSC_O4b3Disc_16KHZ_R1-1420877824-4096.hdf5")
        ]
    }

    print("=== MASTER 180Hz HARDWARE AUDIT CORE ===")
    for era, pairs in audit_plan.items():
        print(f"\n--- {era} ---")
        for label, f1, f2 in pairs:
            p1, p2 = os.path.join(BASE_PATH, f1), os.path.join(BASE_PATH, f2)
            if not (os.path.exists(p1) and os.path.exists(p2)):
                print(f" [!] File Mismatch: {label}")
                continue
            try:
                with h5py.File(p1, 'r') as h1, h5py.File(p2, 'r') as h2:
                    d1, d2 = get_data(h1), get_data(h2)
                    ln = min(len(d1), len(d2))
                    coh, phase, t = audit_peak_window(d1[:ln], d2[:ln])
                    print(f" > {label} | Peak Coh: {coh:.4f} | Phase: {phase:.2f}° | Offset: {t}s")
            except Exception as e:
                print(f" [!] Error in {label}: {e}")

if __name__ == "__main__":
    run_hardware_audit()


#######################################################################################################

The TLC-180 HARMONY HANDSHAKE 



import h5py
import numpy as np
import os
from scipy.signal import welch

def cross_power_stability(file_h, file_l):
    """Calculates Cross-Power Density without digital filters."""
    fs = 16384
    with h5py.File(file_h, 'r') as hf, h5py.File(file_l, 'r') as lf:
        h = hf['strain/Strain'][:] * 1e20 # Numerical Rescaling
        l = lf['strain/Strain'][:] * 1e20
        f, Pxy = welch(h * l, fs=fs, nperseg=fs*2)
        idx = np.argmin(np.abs(f - 180.0))
        return np.abs(Pxy[idx])
