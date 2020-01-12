# Define some commonly used functions here   \
# Gleb Lukicov (11 Jan 2020)  
from scipy import stats
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import re

def plotHist(data, n_bins=100, prec=4, font_size=14, input_color="green", alpha=0.7):
    '''
    Input is a 1D array

    # Example of plotting 1D histo from data with automatic binning
    # ax, legend = cu.plotHist(dataX, n_bins=None)
    # cu.textL(ax, 0.8, 0.85, str(legend), font_size=14)
    # plt.show()
    '''
    # seaborn hist plot with input pars
    ax = sns.distplot(data, bins=n_bins, hist=True, kde=False, color=input_color, hist_kws={"alpha": alpha})

    # 5 DoF stats 
    N, mean, meanE, sd, sdE = stats5(data)
    legend = legend5(N, mean, meanE, sd, sdE, prec) # return legend string 
   
    # make a nice looking plot as default 
    ax.set_xlabel(xlabel="", fontsize=font_size)
    ax.set_ylabel(ylabel="", fontsize=font_size)
    ax.tick_params(axis='x', which='both', bottom=True, top=True, direction='inout')
    ax.tick_params(axis='y', which='both', left=True, right=True, direction='inout')
    ax.minorticks_on()
    plt.xticks(fontsize=font_size-1)
    plt.yticks(fontsize=font_size-1)
    # plt.tight_layout()

    return ax, legend


def plotHist2D(x, y, n_binsX=100, n_binsY=100, prec=4, font_size=14, cmap=plt.cm.jet, return_cb=True):
    '''
    Inputs are two 1D arrays

    # Example of getting 2D histro from data 
    # TODO adjust value to get default scaling better (can now adjust from few)
    # fig, axes = plt.subplots()
    # jg, legendX, legendY, cb, cbaxes = cu.plotHist2D(dataX, dataX, n_binsX=binsX, n_binsY=binsX, return_cb=True)
    # cb.set_label("Tracks",fontsize=13)
    # cu.textL(cbaxes, -15.0, 1.2, "X:\n"+str(legendX), font_size=14)
    # cu.textL(cbaxes, 0.8, 1.2, "Y:\n"+str(legendY), font_size=14)
    # jg.set_axis_labels("x", "y")
    # sns.set(font_scale = 3)
    # plt.show()
    # plt.savefig("2Dtest.png")
    '''
    
    #make a seborn plot, with 2D histo on top
    # return  in the jg (join grid) array of points 
    jg = sns.jointplot(x=x, y=y)

    # make a nice looking plot as default 
    plt.ylabel("",fontsize=font_size)
    plt.xlabel("",fontsize=font_size)
    plt.xticks(fontsize=font_size-1)
    plt.yticks(fontsize=font_size-1)

    jg.ax_joint.cla() # clear 
    plt.sca(jg.ax_joint) # join 
    plt.hist2d(x, y, bins=(100, 100), cmap=cmap) 

    # 5 DoF stats in X and Y 
    Nx, meanx, meanEx, sdx, sdEx = stats5(x)
    legendX = legend5(Nx, meanx, meanEx, sdx, sdEx, prec) # return legend string x
    Ny, meany, meanEy, sdy, sdEy = stats5(y)
    legendY = legend5(Ny, meany, meanEy, sdy, sdEy, prec) # return legend string y

    # add the colour bar with new axis
    if(return_cb):
        cbaxes = jg.fig.add_axes([0.8, 0.05, 0.03, 0.6]) 
        cb = plt.colorbar(cax = cbaxes)  
        cb.ax.tick_params(labelsize=font_size-1) 
    
    # the returned cbaxes can be used to put legend on the plot 
    if(return_cb):
        return jg, legendX, legendY, cb, cbaxes
    if(not return_cb):
        return jg, legendX, legendY


def textL(ax, x, y, legend, font_size=14):
    '''
    return a good formatted plot legend
    '''
    return ax.text(x, y, str(legend),  fontsize=font_size, transform=ax.transAxes, horizontalalignment='center', verticalalignment='center')

def legend5(N, mean, meanE, sd, sdE, prec=4):
    '''
    form a string from 5 stats inputs with given precision
    '''
    # form raw string with Latex
    sigmaS=r"$\sigma$"
    meanS=r"$\mathrm{\mu}$"
    legend = "N={0:d}".format(N)+"\n"+str(meanS)+"={0:.{prec}f}({1:d})\n".format(mean, int(round(meanE*10**prec)), prec=prec)+str(sigmaS)+"={0:.{prec}f}({1:d})".format(sd, int(round(sdE*10**prec)), prec=prec)
    return legend

def legend4(mean, meanE, sd, sdE, prec=4):
    '''
    form a string from 4 stats inputs with given precision
    '''
    # form raw string with Latex
    sigmaS=r"$\sigma$"
    meanS=r"$\mathrm{\mu}$"
    legend = str(meanS)+"={0:.{prec}f}({1:d}) \n ".format(mean, int(round(meanE*10**prec)), prec=prec)+str(sigmaS)+"={0:.{prec}f}({1:d})".format(sd, int(round(sdE*10**prec)), prec=prec)
    return legend

def stats5(data):
    '''
    Input is a 1D array 
    '''
    N = len(data)
    mean = np.mean(data)
    meanE = stats.sem(data)
    sd = np.std(data)
    sdE = np.sqrt(sd**2/ (2*N) )
    return N, mean, meanE, sd, sdE 

def stats3(data):
    '''
    Input is a 1D array 
    '''
    N = len(data)
    mean = np.mean(data)
    meanE = stats.sem(data)
    return N, mean, meanE

