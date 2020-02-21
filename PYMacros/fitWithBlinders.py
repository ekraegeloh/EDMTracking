# Author: Gleb Lukicov (21 Feb 2020)
# Based on Saskia's ROOT macro 
# Test the "w_a" blinding for 60h dataset

#Blinding lib imported in CommonUtils:
import os, sys 
sys.path.append('../CommonUtils/') # https://github.com/glukicov/EDMTracking/blob/master/CommonUtils/CommonUtils.py
import CommonUtils as cu
import argparse, math
from scipy import stats, optimize
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from root_pandas import read_root # see https://github.com/scikit-hep/root_pandas 

staions=(12, 18)

#Input fitting parameters 
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--p0", nargs='+', type=float, default=[ 85263, 64.0, 0.1, 1.0, 2.0]) 
arg_parser.add_argument("--tree", type=str, default="../DATA/Trees/60h_all_quality_tracks.root") 
args=arg_parser.parse_args()
    
#open Tree only the trackT0 (for speed) and fit 
def main():
    print("Opening data...", args.tree)
    data_all = read_root(args.tree, 'QualityTracks',  columns=["station", "trackT0", "trackMomentum"])
    print("Total of", data_all.shape[0], "tracks")
    print("Opened data!")

    data_all['trackT0']=data_all['trackT0']*1e-3 # ns -> us

    #define the time and energy cuts (otherwise the wiggle looks wobbly!)
    time_cut= (data_all['trackT0'] > 30)  # us, define a time_cut with time > 30 us 
    mom_cut = (data_all['trackMomentum'] > 1800) # MeV 
    #Apply cuts in one go! 
    data = data_all[time_cut & mom_cut]

    #define station cuts to loop over 
    s12_cut = (data['station'] == staions[0])
    s18_cut = (data['station'] == staions[1])
    station_cut = (s12_cut, s18_cut)

    for i_cut, staion in enumerate(staions):
        data_station=data[station_cut[i_cut]]
        # resolve into t variable for ease for a station
        t = data_station['trackT0'] 
        N=data.shape[0]
        print("After cuts", N, "tracks in", station)
        
        #define modulation and limits 
        bin_w = 150*1e-3 # 150 ns 
        min_x = 30 # us
        max_x = 400 # us 
        t_mod=100 # us; fold plot every N us 

        print("digitsing data (binning)")
        # just call x,y = frequencies, bin_centres for plotting and fitting 
        x, y = cu.get_freq_bin_c_from_data(t, bin_w, (min_x, max_x) )
        y_err = np.sqrt(y) # sigma =sqrt(N)
        print("digitsed data done!")

        print("Fitting!")
        # Levenberg-Marquardt algorithm as implemented in MINPACK
        par, pcov = optimize.curve_fit(f=cu.blinded_wiggle_function, xdata=x, ydata=y, sigma=y_err, p0=args.p0, absolute_sigma=False, method='lm')
        par_e = np.sqrt(np.diag(pcov))
        print("Pars_ :", *par)
        print("Pars_e:",*par_e)
        chi2_ndf, chi2, ndf=cu.chi2_ndf(x, y, y_err, cu.blinded_wiggle_function, par)
        print("Fit 𝝌2/DoF="+str(round(chi2_ndf,2)) )

        print("Plotting fit and data!")
        #use pre-define module wiggle function from CU
        # plt.tight_layout()
        fig,ax = cu.modulo_wiggle_5par_fit_plot(x, y, t_mod, max_x, min_x, N, par, par_e, bin_w)
        plt.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.5, 1.1) )
        plt.savefig("../fig/wiggle_blind"+station+".png", dpi=300)
        print("Done for", station)


if __name__ == "__main__":
    main()

