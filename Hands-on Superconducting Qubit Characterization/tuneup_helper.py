###
# Common helper functions for fitting data. Needed to extract qubit and readout parameters from measurement data
# Copyright (c) 2022 Zurich Instruments
###

import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt


# oscillations - Rabi
def func_osc(x, freq, phase, amp=1, off=0): 
    return amp * np.cos(freq * x + phase) + off

# decaying oscillations - Ramsey
def func_decayOsc(x, freq, phase, rate, amp=1, off=-0.5): 
    return amp * np.cos(freq * x + phase) * np.exp(-rate * x) + off

# decaying exponent - T1
def func_exp(x, rate, off, amp=1): 
    return amp * np.exp(-rate * x) + off

# Lorentzian
def func_lorentz(x, width, pos, amp, off):
    return off + amp * width**2 / (width**2 + (x-pos)**2)

# inverted Lorentzian - spectroscopy
def func_invLorentz(x, width, pos, amp, off=1):
    return off - amp * width**2 / (width**2 + (x-pos)**2)

# Fano lineshape - spectroscopy
def func_Fano(x, width, pos, amp, fano = 0, off=.5):
    return off + amp * (fano * width + x - pos)**2 / (width**2 + (x-pos)**2)


## function to fit Rabi oscillations
def fit_Rabi(x, y, freq, phase, amp=None, off=None, plot=False, bounds=None):

    if amp is not None:
        if off is not None:
            if bounds is None:
                popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase, amp, off])
            else:
                popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase, amp, off], bounds=bounds)
        else:
            if bounds is None:
                popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase, amp])
            else:
                popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase, amp], bounds=bounds)
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase])
        else:
            popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase], bounds=bounds)

    if plot:
        plt.plot(x, y, '.k')
        plt.plot(x, func_osc(x, *popt), '-r')
        plt.show()
    
    return popt, pcov


## function to fit spectroscopy traces
def fit_Spec(x, y, width, pos, amp, off=0, plot=False, bounds=None):
    #if off is None:
    #    off = np.median(y)
    if bounds is None:
        popt, pcov = opt.curve_fit(func_lorentz, x, y, p0=[width, pos, amp, off])
    else:
        popt, pcov = opt.curve_fit(func_lorentz, x, y, p0=[width, pos, amp, off], bounds=bounds)

    if plot:
        plt.plot(x, y, '.k')
        plt.plot(x, func_lorentz(x, *popt), '-r')
        plt.show()
    
    return popt, pcov


## function to fit spectroscopy traces with Fano lineshape
def fit_ResSpec(x, y, width, pos, amp, fano, off=None, plot=False, bounds=None):

    if off is not None:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_Fano, x, y, p0=[width, pos, amp, fano, off])
        else:
            popt, pcov = opt.curve_fit(func_Fano, x, y, p0=[width, pos, amp, fano, off], bounds=bounds)
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_Fano, x, y, p0=[width, pos, amp, fano])
        else:
            popt, pcov = opt.curve_fit(func_Fano, x, y, p0=[width, pos, amp, fano], bounds=bounds)

    if plot:
        plt.plot(x, y, '.k')
        plt.plot(x, func_Fano(x, *popt), '-r')
        plt.show()
    
    return popt, pcov

