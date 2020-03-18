'''
Author: Gleb Lukicov

Get an estimate of the longitudinal field from simulation or data
using EDM blinding
'''
import numpy as np
import pandas as pd
# MPL in batch mode
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import os, sys
from scipy import optimize
sys.path.append("../CommonUtils/") # https://github.com/glukicov/EDMTracking/blob/master/CommonUtils/CommonUtils.py
import CommonUtils as cu
import RUtils as ru
import argparse 
from fitWithBlinders_skim import fft, residual_plots


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--t_min", type=float, default=4.365411) # us 
arg_parser.add_argument("--t_max", type=float, default=199.985411) # us 
arg_parser.add_argument("--p_min", type=float, default=1800) # us 
arg_parser.add_argument("--p_max", type=float, default=3100) # us 
arg_parser.add_argument("--hdf", type=str, default="../DATA/HDF/Sim/VLEDM_skim.h5") 
# arg_parser.add_argument("--hdf", type=str, default="../DATA/HDF/EDM/60h.h5", help="input data")
arg_parser.add_argument("--corr", action='store_true', default=False, help="Save covariance matrix for plotting")
arg_parser.add_argument("--scan", action='store_true', default=False, help="if run externally for iterative scans - dump 𝝌2 and fitted pars to a file for summary plots") 
args=arg_parser.parse_args()

### Define constants and starting fit parameters
font_size=14 # for plots
stations=(12, 18)
expected_DSs = ("60h", "9D", "HK", "EG", "VLEDM_skim")

### Get ds_name from filename
ds_name=args.hdf.replace(".","/").split("/")[-2] # if all special chars are "/" the DS name is just after extension
folder=args.hdf.replace(".","/").split("/")[-3] 
print("Detected DS name:", ds_name, "from the input file!")
if( (folder != "Sim") and (folder != "EDM")): raise Exception("Loaded pre-skimmed simulation or EDM file")
if(not ds_name in expected_DSs): raise Exception("Unexpected input HDF name: if using Run-1 data, rename your file to DS.h5 (e.g. 60h.h5); Otherwise, modify functionality of this programme...exiting...")

sim=False
if(ds_name is "VLEDM"):
    print("Simulation data is loaded!"); sim=True; stations=([1218])

#Set gm2 period 
g2period = round(2*np.pi / cu._omega,6)   # 4.365411 us 
print("g-2 period ", g2period, "us")
# if(t_min<g2period):
#     raise Exception("Set t_min>g2period for EDM reflection blinding to work")

#Cuts 
t_min = args.t_min # us 
t_max = args.t_max # us 
print("Starting and end times:", t_min, "to", t_max, "us")
p_min = args.p_min # MeV 
p_max = args.p_max # MeV 
print("Momentum cuts:", p_min, "to", p_max, "MeV")

#binning 
bin_w = 10*1e-3 # 10 ns 
bin_n = int( g2period/bin_w)
xy_bins=(bin_n, bin_n*2)
print("Setting bin width of", bin_w*1e3, "ns with ~", bin_n, "bins")

#starting fit parameters and their labels for plotting 
par_names_count= ["N", "tau", "A", "phi"]; par_labels_count= [r"$N$", r"$\tau$", r"$A$", r"$\phi$"]
par_names_theta= ["A_Bz", "A_edm_blind", "c"]; par_labesl_theta= [r"$A_{B_{z}}$", r"$A^{\rm{BLINDED}}_{\mathrm{EDM}}$", r"$c$"]
par_name_theta_truth=par_names_theta; par_name_theta_truth[1]="A_edm"
p0_count=[3000, 64.4, -0.40, 6.240]
print("Starting pars count",*par_names_count, *p0_count)
p0_theta_blinded=[1.0, 1.0, 1.0]
print("Starting pars theta blinded", *par_names_theta, *p0_theta_blinded)
if(sim): p0_theta_truth=[0.00, 0.17, 0.0]; print("Starting pars TRUTH theta", *par_name_theta_truth, *p0_theta_truth)

### Define global variables
residuals_counts=[[],[]]
residuals_theta=[[],[]]
times_counts=[[],[]]
times_theta=[[],[]]

def main():

    data,station_cut=load_data(args.hdf)

    plot_counts_theta(data,station_cut)


def load_data(df_path):
    '''
    Load data apply cuts and return two data frames - one per station 
    '''
    data_hdf = pd.read_hdf(df_path)   #open skimmed 
    print("N before cuts", data_hdf.shape[0])
    
    #apply cuts 
    mom_cut = ( (data_hdf['trackMomentum'] > p_min) & (data_hdf['trackMomentum'] < p_max) ) # MeV  
    time_cut =( (data_hdf['trackT0'] > t_min) & (data_hdf['trackT0'] < t_max) ) # MeV  
    data_hdf=data_hdf[mom_cut & time_cut]
    data_hdf=data_hdf.reset_index() # reset index from 0 after cuts 
    print("Total tracks after cuts", round(data_hdf.shape[0]/1e6,2), "M")

    # calculate variables for plotting
    p=data_hdf['trackMomentum']
    py=data_hdf['trackMomentumY']
    t=data_hdf['trackT0']
    theta_y_mrad = np.arctan2(py, p)*1e3 # rad -> mrad
    mod_times = cu.get_g2_mod_time(t) # Module the g-2 oscillation time 
    data_hdf['mod_times']=mod_times # add to the data frame 
    data_hdf['theta_y_mrad']=theta_y_mrad # add to the data frame 

    # select all stations for simulation
    if(sim): 
        s1218_cut = ( (data_hdf['station'] == 12) or (data_hdf['station'] == 18) ); station_cut=(s1218_cut)

    #split into two stations 
    if(not sim): 
        s12_cut = (data_hdf['station'] == 12); s18_cut = (data_hdf['station'] == 18); station_cut = (s12_cut, s18_cut);
        
    return data_hdf, station_cut


def plot_counts_theta(data, station_cut):
    
    for i_station, station in enumerate(stations):
        
        data

        data_station=data[station_cut[i_station]]
        N=data_station.shape[0]
        print("Entries: ", N, " in S", station)

        '''
        Plot counts vs. mod time and fit
        '''
        ### Digitise data
        bin_c, freq = cu.get_freq_bin_c_from_data(data_station['mod_times'], bin_w, (0, g2period) )
        y_err = np.sqrt(freq) # Poissson error 
        x,y,y_e = bin_c, freq, y_err
       
        #Fit
        par, par_e, pcov, chi2_ndf, ndf = cu.fit_and_chi2(x, y, y_e, cu.unblinded_wiggle_fixed, p0_count)
        if (np.max(abs(par_e)) == np.Infinity ): raise Exception("\nOne of the fit parameters is infinity! Exiting...\n")
        if(args.corr): print("Covariance matrix", pcov); np.save("../DATA/misc/pcov_N.np", pcov);
        # if(args.corr): print("Covariance matrix", pcov); np.save("../DATA/misc/pcov_N_S"+str(station)+".np", pcov);

        #Plot
        fig, ax = cu.plot_edm(bin_c, freq, y_err, bin_w, font_size=font_size)
        
        # cu.textL(ax, 0.48, 0.35, leg_fit, c="r", fs=font_size+2)
        # cu.textL(ax, 0.78, 0.75, leg_data, fs=font_size+1)
        # ax.set_ylim(np.amin(freq)*0.9, np.amax(freq)*1.3);
        fig.savefig("../fig/count_fit.png", dpi=300)

        sys.exit()

        # get residuals for later plots 
        residuals_counts[i_station] = cu.residuals(x, y, cu.unblinded_wiggle_fixed, par)
        times_counts[i_station] = x

        ### Set constant phase for the next step
        cu._LT=par[1]
        print("LT set to", round(cu._LT,2), "us")
        cu._phi=par[-1]
        print("Phase set to", round(cu._phi,2), "rad")


        '''
        Blinded (EDM) fit for B_Z 
        '''
        
        ### Resolve angle and times
        tmod_abs, weights=cu.get_abs_times_weights(data_station['trackT0'])
        ang=data_station['theta_y_mrad']

        ### Digitise data with weights
        h,xedges,yedges  = np.histogram2d(tmod_abs, ang, weights=weights, bins=xy_bins);
        
        # expand 
        (x_w, y_w), binsXY, dBinXY = ru.hist2np(h, (xedges,yedges))
        
        #profile
        df_binned =cu.Profile(x_w, y_w, None, nbins=bin_n, xmin=np.min(x_w), xmax=np.max(x_w), mean=True, only_binned=True)
        x, y, y_e, x_e =df_binned['bincenters'], df_binned['ymean'], df_binned['yerr'], df_binned['xerr']

        #Fit
        par, par_e, pcov, chi2_ndf, ndf = cu.fit_and_chi2(x, y, y_e, cu.thetaY_phase, p0_theta_blinded)
        if (np.max(abs(par_e)) == np.Infinity ): raise Exception("\nOne of the fit parameters is infinity! Exiting...\n")
        if(args.corr): print("Covariance matrix", pcov); np.save("../DATA/misc/pcov_theta.np.npy", pcov);
        # if(args.corr): print("Covariance matrix", pcov); np.save("../DATA/misc/pcov_theta_S"+str(station)+".np", pcov);

        #Plot
        fig, ax = cu.plot(x, y, y_err=y_e, error=True, elw=1, label="Data (sim.)", fs=font_size, tight=True,
                      xlabel=r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]",  ylabel=r"$\langle\theta_y\rangle$ [mrad] per "+str(int(bin_w*1e3))+" ns")
        ax.plot(x, cu.thetaY_phase(x, *par), c="red", 
                label=r'Fit: $\langle \theta(t) \rangle =  A_{\mathrm{B_z}}\cos(\omega_a t + \phi) + A_{\mathrm{EDM}}\sin(\omega_a t + \phi) + c$', lw=2)
        ax.set_xlim(0, g2period);
        ax.set_ylim(-np.amax(y)*1.4, np.amax(y)*1.2);
        leg_data="N="+cu.sci_notation(N)+"\n"+str(int(p_min))+r"<$p$<"+str(int(p_max))+" MeV\n"+str(round(t_min,1))+r"<$t$<"+str(round(t_max,1))+r" $\mathrm{\mu}$s"
        ax.legend(fontsize=font_size-2, loc='upper center', bbox_to_anchor=(0.5, 1.1));
        cu.textL(ax, 0.75, 0.15, leg_data, fs=font_size)
        leg_fit=cu.legend_chi2(chi2_ndf, ndf, par)
        leg_fit=cu.legend_1par(leg_fit, r"$A_{B_{z}}$", par[0], par_e[0], "mrad")
        leg_fit=cu.legend_1par(leg_fit, r"$A^{\rm{BLINDED}}_{\mathrm{EDM}}$", par[1], par_e[1], "mrad")
        leg_fit=cu.legend_1par(leg_fit, r"$c$", par[2], par_e[2], "mrad")
        cu.textL(ax, 0.25, 0.12, leg_fit, fs=font_size, c="r")
        fig.savefig("../fig/bz_fit.png", dpi=300)


        # get residuals for later plots 
        residuals_theta[i_station] = cu.residuals(x, y, cu.thetaY_phase, par)
        times_theta[i_station] = x


        # if(sim):

        #     # Bin 
        #     df_binned =cu.Profile(data_station['mod_times'], data_station['theta_y_mrad'], None, nbins=bin_n, xmin=np.min(data_station['mod_times']), xmax=np.max(data_station['mod_times']), mean=True, only_binned=True)
        #     x, y, y_e, x_e =df_binned['bincenters'], df_binned['ymean'], df_binned['yerr'], df_binned['xerr']

        #     # Fit 
        #     par, par_e, pcov, chi2_ndf, ndf = cu.fit_and_chi2(x, y, y_e, cu.thetaY_phase, p0_theta_truth)

        #     #Plot
        #     fig, ax = cu.plot(x, y, y_err=y_e, error=True, elw=1, label="Data (sim.)", fs=font_size, tight=True,
        #                       xlabel=r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]",  ylabel=r"$\langle\theta_y\rangle$ [mrad] per "+str(int(bin_w*1e3))+" ns")
        #     ax.plot(x, cu.thetaY_phase(x, *par), c="red", 
        #             label=r'Fit: $\langle \theta(t) \rangle =  A_{\mathrm{B_z}}\cos(\omega_a t + \phi) + A_{\mathrm{EDM}}\sin(\omega_a t + \phi) + c$', lw=2)
        #     ax.set_xlim(0, g2period);
        #     ax.set_ylim(-np.amax(y)*1.8, np.amax(y)*2.1);
        #     leg_data="N="+cu.sci_notation(N)+"\n"+str(p_min)+r"<$p$<"+str(int(p_max))+" MeV\n"+str(t_min)+r"<$t$<"+str(t_max)+r" $\mathrm{\mu}$s"
        #     ax.legend(fontsize=font_size, loc='upper center', bbox_to_anchor=(0.5, 1.1));
        #     cu.textL(ax, 0.74, 0.8, leg_data, fs=font_size)
        #     leg_fit=cu.legend_chi2(chi2_ndf, ndf, par)
        #     leg_fit=cu.legend_1par(leg_fit, r"$A_{B_{z}}$", par[0], par_e[0], "mrad")
        #     leg_fit=cu.legend_1par(leg_fit, r"$A_{\mathrm{EDM}}$", par[1], par_e[1], "mrad")
        #     leg_fit=cu.legend_1par(leg_fit, "c", par[2], par_e[2], "mrad")
        #     cu.textL(ax, 0.23, 0.12, leg_fit, fs=font_size, c="r")
        #     fig.savefig("../fig/bz_truth_fit.png", dpi=300)



        #-------end of looping over stations

    ### now if not scanning - get FFTs for both stations
    ## FFTs
    if(not args.scan):
        residual_plots(times_counts, residuals_counts, sim=True, eL="count")
        fft(residuals_counts, sim=True, eL="count")
        residual_plots(times_theta, residuals_theta, sim=True, eL="theta")
        fft(residuals_theta, sim=True, eL="theta")



if __name__ == '__main__':
    main()