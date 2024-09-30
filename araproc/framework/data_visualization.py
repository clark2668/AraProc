import logging
import numpy as np
import os
import ROOT
import matplotlib.pyplot as plt
from araproc.framework import analysis_event
from araproc.framework import waveform_utilities as wu

def plot_analysis_event(
    analysis_event : analysis_event.AraAnalysisEvent,
    set_to_visualize = "calibrated",
    time_or_freq = "time",
    ouput_file_path = None
    ):
    
    ####################
    # sanitize inputs
    ####################

    # make sure they have requested something valid (time vs freq domain)
    time_or_freq_options = ["time", "freq"]
    if time_or_freq not in time_or_freq_options:
        raise KeyError(f"Requested option ({time_or_freq}) is not in approved list: {time_or_freq_options}")

    xlabel_options = {
        "time" : "Time (ns)",
        "freq" : "Frequency (GHz)"
    }
    ylabel_options = {
        "time" : "Voltage (V)",
        "freq" : "Spectrum (au)"
    }    

    if not isinstance(ouput_file_path, str):
        raise TypeError("Path to output file must be a string")
    
    # make sure the waveforms they want to plot are actually in the analysis event
    if set_to_visualize not in analysis_event.waveform_sets:
        raise KeyError(f"Requested waveform set ({set_to_visualize}) is not in available list: {analysis_event.waveform_sets.keys()}")
    
    ####################
    # actually make plots
    ####################

    # get the waves to plot
    tgraphs_to_plot = analysis_event.waveform_sets[set_to_visualize]

    # set up fig and axes
    fig, axd = plt.subplot_mosaic(
                            [["ch0", "ch1", "ch2", "ch3"],
                             ["ch4", "ch5", "ch6", "ch7"],
                             ["ch8", "ch9", "ch10", "ch11"],
                             ["ch12", "ch13", "ch14", "ch15"]],
                              figsize=(10, 7), 
                              sharex=True,
                              sharey=True,
                              layout="constrained")

    # draw the graphs, label each one appropriately
    for wave_key in tgraphs_to_plot.keys():
        times, volts = wu.tgraph_to_arrays(tgraphs_to_plot[wave_key])
        xvals = times
        yvals = volts

        if time_or_freq == "freq":
            # if they frequested frequency domain, do the FFT
            freqs, spectrum = wu.time2freq(times, volts)
            xvals = freqs
            yvals = np.abs(spectrum)

        axd[f"ch{wave_key}"].plot(xvals, yvals) # make the plot
        axd[f"ch{wave_key}"].set_title(f"Channel {wave_key}")

    # label axes
    
    # bottom row gets time label
    for ax in [axd["ch12"], axd["ch13"], axd["ch14"], axd["ch15"]]:
        ax.set_xlabel(xlabel_options[time_or_freq])
    # left column gets voltage label
    for ax in [axd["ch0"], axd["ch4"], axd["ch8"], axd["ch12"]]:
        ax.set_ylabel(ylabel_options[time_or_freq])
    
    # if the frequency representation as requested, set the y-axis to log
    if time_or_freq == "freq":
        for ax_i in axd:
            axd[ax_i].set_yscale("log")

    # save figure
    fig.savefig(ouput_file_path)