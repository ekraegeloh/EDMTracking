# Make profile plots from ROOT histogram
# Gleb Lukicov (11 Jan 2020)  
import os, sys
sys.path.append('CommonUtils/')
import CommonUtils as cu
import RUtils as ru

import argparse 
import math
from scipy import stats, optimize
import numpy as np
import seaborn as sns
import pandas as pd
from pandas import Series, DataFrame


# MPL in batch mode
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

arg_parser = argparse.ArgumentParser()
# arg_parser.add_argument("--file_path", type=str, default="DATA/noEDM.root") 
# arg_parser.add_argument("--hist_path", type=str, default="AllStations/VertexExtap/t>0/0<p<3600/vertexPosSpread") 
# arg_parser.add_argument("--hist_path", type=str, default="AllStations/VertexExtap/t>0/0<p<3600/thetay_vs_time_modg2") 
# arg_parser.add_argument("--hist_path", type=str, default="AllStationsNoTQ/VertexExtap/t>0/0<p<3600/thetay_vs_time_modg2") 
arg_parser.add_argument("--file_path", type=str, default="DATA/VLEDM.root") 
# arg_parser.add_argument("--hist_path", type=str, default="AllStations/VertexExt/t>0/0<p<3600/thetay_vs_time_modg2") 
# arg_parser.add_argument("--hist_path", type=str, default="AllStationsNoTQ/VertexExt/t>0/0<p<3600/thetay_vs_time_modg2") 
arg_parser.add_argument("--hist_path", type=str, default="AllStationsNoTQ/VertexExt/t>0/0<p<3600/vertexPosSpread") 
# arg_parser.add_argument("--hist_path", type=str, default="AllStations/VertexExt/t>0/0<p<3600/vertexPosSpread") 
arg_parser.add_argument("--read", action='store_true', default=False) # read and write TH data into numpy file
arg_parser.add_argument("--beam", action='store_true', default=False)
arg_parser.add_argument("--hist", action='store_true', default=False) # Make a 2D plot 
arg_parser.add_argument("--profile", action='store_true', default=False)
arg_parser.add_argument("--iter", action='store_true', default=False)
arg_parser.add_argument("--gauss", action='store_true', default=False)
args=arg_parser.parse_args()

#TODO impliment check of at least 1 arg 
# args_v = vars(arg_parser.parse_args())
# if all(not args_v):
#     arg_parser.error('No arguments provided.')

#set some global variables  
info=[]
names=[]

# get data from 2D hist
if(args.read):
    dataXY, n_binsXY, dBinsXY = ru.hist2np(file_path=args.file_path, hist_path=args.hist_path)
    # store that data
    np.save("DATA/misc/dataXY.npy", dataXY)

    # and info
    # edm_setting=args.file_path.split("/")[1].split(".")[0]
    # Q_cut=args.hist_path.split("/")[0]
    # data_type=args.hist_path.split("/")[1]
    # time_cut=args.hist_path.split("/")[2]+r" $\mathrm{\mu}$s"
    # p_cut=args.hist_path.split("/")[3]+" MeV"
    # y_label=args.hist_path.split("/")[4].split("_")[0]
    # x_label=args.hist_path.split("/")[4].split("_")[2:]
    # N=len(dataXY[0])
    # #some specific string transforms
    # if (edm_setting == "VLEDM"):
    #     edm_setting=r"$d_{\mu} = 5.4\times10^{-18} \ e\cdot{\mathrm{cm}}$"
    # if (edm_setting == "noEDM"):
    #     edm_setting=r"$d_{\mu} = 0 \ e\cdot{\mathrm{cm}}$"
    # if(y_label=="thetay"):
    #     y_label=r"$\langle\theta_y\rangle$ [mrad]"
    # if(x_label[0]=="time" and x_label[1]=="modg2"):
    #     x_label=r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]"
    # # two lists into dict 
    # info=[edm_setting, data_type, Q_cut, time_cut, p_cut, x_label, y_label, N]
    # names=["edm_setting", "data_type", "Q_cut", "time_cut", "p_cut", "x_label", "y_label", "N"]
    # info_dict = dict(zip(names, info))
    # #now pass along the information to the fitter
    # df_info = pd.DataFrame(info_dict, index=[0]) 
    # df_info.to_csv("DATA/misc/df_info.csv")
    
    print("Data saved to dataXY.npy, re-run with --profile or --hist to make plots")
    sys.exit()

# Plot a 2D histogram
if (args.hist):
    print("Plotting a histogram...")
        
    # load the data 
    dataXY=np.load("DATA/misc/dataXY.npy")
    x=dataXY[0]
    y=dataXY[1]

    if(args.beam):
        jg,cb,legendX,legendY =cu.plotHist2D(x, y, n_binsXY=(100,100), cmin=5, prec=2)
        jg.ax_joint.set_ylabel("Vertical beam position [mm]", fontsize=18)
        jg.ax_joint.set_xlabel("Radial beam position [mm]", fontsize=18)
        cu.textL(jg.ax_joint, 1.32, 1.15, "Radial [mm]:"+"\n"+str(legendX), font_size=15)
        cu.textL(jg.ax_joint, 1.32, 1.00, "Vertical [mm]:"+"\n"+str(legendY), font_size=15)
        N=cu.sci_notation(len(x)) # format as a 
        cu.textL(jg.ax_joint, 1.32, 0.00, "N: "+N, font_size=15)
        plt.savefig("fig/beam.png", dpi=300)
    else:
        jg,cb,legendX,legendY =cu.plotHist2D(x, y, n_binsXY=(75,75), cmin=5, prec=3)
        jg.ax_joint.set_ylabel(r"$\theta_y$ [rad]", fontsize=18)
        jg.ax_joint.set_xlabel(r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]", fontsize=18)
        cu.textL(jg.ax_joint, 1.32, 1.15, r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]:"+"\n"+str(legendX), font_size=15)
        cu.textL(jg.ax_joint, 1.32, 1.00, r"$\theta_y$ [rad]:"+"\n"+str(legendY), font_size=15)
        N=cu.sci_notation(len(x)) # format as a 
        cu.textL(jg.ax_joint, 1.32, 0.00, "N: "+N, font_size=17)
        plt.savefig("fig/thetavsT.png", dpi=300)


# Profile Plot 
if (args.profile):

    # load the data 
    dataXY=np.load("dataXY.npy")
    x=dataXY[0]
    y=dataXY[1]

    #convert 𝛉 into um
    y=y*1e3 # rad -> mrad 

    print("Plotting a profile...")
    fig,ax=plt.subplots()
    ax, df_binned, df_input =cu.Profile(x, y, ax, nbins=15, xmin=np.min(x),xmax=np.max(x), mean=True)
    ax.set_ylabel(r"$\langle\theta_y\rangle$ [mrad]", fontsize=16)
    ax.set_xlabel(r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]", fontsize=16)
    N=cu.sci_notation(len(x)) # format as a 
    cu.textL(ax, 0.88, 0.9, "N: "+N, font_size=14)
    plt.tight_layout() 
    plt.savefig("profile.png")

    # can save the profile points with errors to a file
    df_binned.to_csv("DATA/misc/df_binned.csv")

# iterative fits over many profiles 
if(args.iter):

    #loop over common plots
    
    # fileLabel=("LargeEDM", "noEDM")
    # fileName=("DATA/VLEDM.root", "DATA/noEDM.root")
    fileLabel=[("LargeEDM")]
    fileName=[("DATA/VLEDM.root")]
    
    plotLabel=("Tracks", "Vertices")
    plotName=["TrackFit", "VertexExt"]
    # qLabel=("QT", "NQT")
    # qName=("AllStations", "AllStationsNoTQ")

    qLabel=[("NQT")]
    qName=[("AllStationsNoTQ")]
    
    cutLabel=("0_p_3600", "400_p_2700", "700_p_2400")
    cutName=("t>0/0<p<3600", "t>0/400<p<2700", "t>0/700<p<2400")
    
    for i_file, i_fileName in enumerate(fileName):
        
        # change of name on noEDM
        if (i_file == 1):
            plotName[1]="VertexExtap" #old art code had a typo... 

        for i_cut, i_cutName in enumerate(cutName):
            for i_plot, i_plotName in enumerate(plotName):
                for i_q, i_qName in enumerate(qName):   

                    # form full paths and labels  
                    fullPath=i_qName+"/"+i_plotName+"/"+i_cutName+"/thetay_vs_time_modg2"
                    fullLabel=fileLabel[i_file]+"_"+plotLabel[i_plot]+"_"+qLabel[i_q]+"_"+cutLabel[i_cut]

                    print("Plotting a profile for", fullPath)

                    #extract data from the histogram
                    dataXY, n_binsXY, dBinsXY = ru.hist2np(file_path=i_fileName, hist_path=fullPath)
                    
                    #bin data into a profile 
                    if(args.gauss):
                        df_data=cu.Profile(dataXY[0], dataXY[1], False, nbins=15, xmin=np.min(dataXY[0]),xmax=np.max(dataXY[0]), full_y=True, only_binned=True)
                        y=df_data['y']
                    else:
                        df_data=cu.Profile(dataXY[0], dataXY[1], False, nbins=15, xmin=np.min(dataXY[0]),xmax=np.max(dataXY[0]), mean=True, only_binned=True)
                        y=df_data['ymean']
                        
                    x=df_data['bincenters']
                    x_err=df_data['xerr']
                    y_err=df_data['yerr']
                    y=y*1e3 # rad -> mrad 
                    y_err=y_err*1e3 # rad -> mrad 

                    # extract info
                    edm_setting=fullPath.split("/")[1].split(".")[0]
                    Q_cut=fullPath.split("/")[0]
                    data_type=fullPath.split("/")[1]
                    time_cut=fullPath.split("/")[2]+r" $\mathrm{\mu}$s"
                    p_cut=fullPath.split("/")[3]+" MeV"
                    y_label=fullPath.split("/")[4].split("_")[0]
                    x_label=fullPath.split("/")[4].split("_")[2:]
                    N=len(dataXY[0])
                    
                    #some specific string transforms
                    if (edm_setting == "VLEDM"):
                        edm_setting=r"$d_{\mu} = 5.4\times10^{-18} \ e\cdot{\mathrm{cm}}$"
                    if (edm_setting == "noEDM"):
                        edm_setting=r"$d_{\mu} = 0 \ e\cdot{\mathrm{cm}}$"
                    if(y_label=="thetay"):
                        y_label=r"$\langle\theta_y\rangle$ [mrad]"
                    if(x_label[0]=="time" and x_label[1]=="modg2"):
                        x_label=r"$t^{mod}_{g-2} \ \mathrm{[\mu}$s]"

                    # if extracting y and delta(y) from a Gaussian fit 
                    if(args.gauss):
                        means=[]
                        means_errors=[]
                        for i_point in range(0, len(df_data)):
                            
                            # fit for a range of data 
                            n_bins=25
                            y_min, y_max=-25, +25

                            # all data y_hist, range is y 
                            y_hist=y[i_point]
                            y_select  = y_hist[np.logical_and(y_hist >= y_min, y_hist <= y_max)]

                            #bin the data in range 
                            hist, bin_edges = np.histogram(y_select, bins=n_bins, density=False)
                            bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
                            bin_width=bin_edges[1]-bin_edges[0] 
                            #find the right number of bins for. all data
                            n_bins_hist=int( (np.max(y_hist)-np.min(y_hist))/bin_width ) 
                            y_err=np.sqrt(hist) # sqrt(N) per bin

                            # fit in range 
                            p0=[1, 1, 1]
                            par, pcov = optimize.curve_fit(cu.gauss, bin_centres, hist, p0=p0, sigma=y_err, absolute_sigma=False, method='trf')
                            par_e = np.sqrt(np.diag(pcov))
                            chi2ndf= cu.chi2_ndf(bin_centres, hist, y_err, cu.gauss, par)

                            #append the fit parameters
                            means.append(par[1])
                            means_errors.append(par_e[1])

                            #plot and stats + legend 
                            units="mrad"
                            legend_fit=cu.legend4_fit(chi2ndf, par[1], par_e[1], par[2], par_e[2], units, prec=2)
                            ax, legend = cu.plotHist(y_hist, n_bins=n_bins_hist, units=units, prec=2)
                            ax.plot(bin_centres, cu.gauss(bin_centres, *par), color="red", linewidth=2, label='Fit')
                            cu.textL(ax, 0.8, 0.78, r"$\theta_y$:"+"\n"+str(legend), font_size=15)
                            cu.textL(ax, 0.2, 0.78, "Fit:"+"\n"+str(legend_fit), font_size=15, color="red")
                            ax.set_xlabel(r"$\theta_y$ [mrad]", fontsize=18)
                            ax.set_ylabel(r"$\theta_y$ / "+str(round(bin_width))+" mrad", fontsize=18)
                            plt.tight_layout()
                            plt.savefig("fig/Gauss/Gauss_"+fullLabel+"_"+str(i_point)+".png", dpi=300)
                            plt.clf()

                        #done looping over y bins
                        #reassign data "pointer names"
                        y=means
                        y_err=means_errors


                    #fit a function and get pars 
                    par, pcov = optimize.curve_fit(
    cu.sin_unblinded, x, y, sigma=y_err, p0=[1.0, 1.0, 1.0], absolute_sigma=False, method='lm')
                    par_e = np.sqrt(np.diag(pcov))
                    chi2_n=cu.chi2_ndf(x, y, y_err, cu.sin_unblinded, par)

                    # plot the fit and data 
                    fig, ax = plt.subplots()
                    # data
                    ax.errorbar(x,y,xerr=x_err, yerr=y_err, linewidth=0, elinewidth=2, color="green", marker="o", label="Sim.")
                    # fit 
                    ax.plot(x, cu.sin_unblinded(x, par[0], par[1], par[2]), color="red", label='Fit')
                  
                    # deal with fitted parameters (to display nicely)
                    parNames=[" A", "b", "c"]
                    units=["mrad", "MHz", "mrad"]
                    prec=2 # set custom precision 
                    
                    #form complex legends 
                    legend1_chi2=cu.legend1_fit(chi2_n)
                    legned1_par=""
                    legend1=cu.legend_par(legned1_par,  parNames, par, par_e, units)
                    print(legend1)
                    legend2=data_type+"\n"+p_cut+"\n N="+cu.sci_notation(N)

                    #place on the plot and save 
                    y1,y2,x1,x2=0.15,0.85,0.25,0.70
                    cu.textL(ax, x1, y1, legend1, font_size=16, color="red")    
                    cu.textL(ax, x2, y2, legend2, font_size=16)
                    ax.legend(loc='center right', fontsize=16)
                    ax.set_ylabel(y_label, fontsize=18)
                    ax.set_xlabel(x_label, fontsize=18)
                    plt.tight_layout() 
                    plt.savefig("fig/profFits/"+fullLabel+".png")
                    plt.clf() 


print("Done!")
