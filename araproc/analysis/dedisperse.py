import numpy as np
from scipy import interpolate

import importlib.resources as pkg_resources
from . import data

from araproc.framework import waveform_utilities as wu

def load_arasim_phase_response_as_spline():

    """
    Load the AraSim phase response of the system to use for de-dispersion.

    Returns
    -------
    the_phase_spline : interp1d
        A spline of the unwrapped phases as a function of frequency.
        The frequency units are Ghz.
        And the phase is unwrapped, in units of radians.
    """

    file = pkg_resources.open_text(data, 
                                   "ARA_Electronics_TotalGain_TwoFilters.txt")
    file_content = np.genfromtxt(file, 
                                 delimiter=",", skip_header=3,
                                 names=["freq", "gain", "phase"], 
                                )

    freq_ghz = file_content["freq"]/1.E3 # convert to GHz
    phs_unwrapped = np.unwrap(file_content["phase"]) # unwrapped phase in radians

    the_phase_spline = interpolate.Akima1DInterpolator(
        freq_ghz, phs_unwrapped,
        method="makima",
    )
    # turn off extrapolation outside the region of support
    the_phase_spline.extrapolate = False
    file.close()

    return the_phase_spline

def eval_splined_phases(phase_spline, freqs_to_evaluate):
    """"
    Just a little helper function.
    This is necessary because the Akima Interpolator will return NaN 
    when called out of the range of support, but we'd rather it gave zeros.
    """
    these_phases = phase_spline(freqs_to_evaluate)
    these_phases = np.nan_to_num(these_phases) # convert nans to zeros
    return these_phases

def dedisperse_wave(
        times, # in nanoseconds,
        volts, # in volts,
        phase_spline # the  phase spline
        ):
    
    """
    Fetch a specific calibrated event

    Parameters
    ----------
    times : np.ndarray(dtype=np.float64)
        A numpy array of floats containing the times for the trace,
        in nanoseconds.
    volts : np.ndarray(dtype=np.float64)
        A numpy array of floats containing the voltages for the trace,
        in volts.
    phase_spline : interp1d
        A spline of the unwrapped phase (in radians) vs frequency (in GHz).
        When the function was first written, it was meant to utilize
        the output of `dedisperse.load_arasim_phase_response_as_spline`.
        So check that function for an example of how to do it.

    Returns
    -------
    dedispersed_wave : np.ndarray(dtype=np.float64)
        The dedispersed wave
        
    """

    if len(times) != len(volts):
        raise Exception("The time and volts arrays are mismatched in length. Abort.")

    # first thing to do is get the frequency domain representation of the trace


    freqs, spectrum = wu.time2freq(times, volts)

    # interpolate the *unwrapped phases* to the correct frequency base
    phased_interpolated = eval_splined_phases(phase_spline, freqs)
    
    # conver these into a complex number
    phased_rewrapped = np.exp((0 + 1j)*phased_interpolated)
    
    # do complex division to do the dedispersion
    spectrum /= phased_rewrapped

    # back to the time domain
    times, volts = wu.freq2time(times, spectrum)
    return times, volts
