import pandas as pd
import numpy as np

import datareader


class Portfolio:
    def __init__(self, scrips=(), weights=(), annual_return=0, annual_risk=0):
        self.scrips = scrips
        self.weights = weights
        self.annual_risk = annual_risk
        self.annual_return = annual_return
    
    @property
    def serialize(self):
        return {
            'scrips': self.scrips,
            'weights': self.weights,
            'risk': self.annual_risk,
            'return': self.annual_return
        }

def merge_candles(candles):
    # takes dict keys as scrip names. drops all colums except ['Close', 'Date'] and then merges.
    # returns dataframe in column names representing their respective close prices
    # eg. df.columns will give you ['HDFC', 'ICICI', 'DMART', ...] where each column represents its close price
    # df.index will be Date object
    concatted_df = pd.concat([df[['Date', 'Close']].set_index('Date') for df in candles.values()], axis=1, join='outer')
    concatted_df.columns = candles.keys()
    print(concatted_df)
    return concatted_df

def get_summary_stats(universe):
    summary = pd.DataFrame(columns=universe.columns ,index=('Mean', 'Variance'))
    for column in universe.columns:
        print(column)
        summary[column]['Mean'] = universe[column].pct_change().mean() # expected rate of return
        summary[column]['Variance'] = universe[column].pct_change().var()
    print(universe.pct_change().cov())
    return summary

def get_portfolio_summary(covar_mat, summary, weights):
    # portfolio contains Date as index, Closing prices as columns for each stock
    
    #get portfolio covariance for returns
    pf_var = 0
    for idx1, column1 in enumerate(covar_mat):
        for idx2, column2 in enumerate(covar_mat):
            pf_var += weights[idx1]*weights[idx2]*covar_mat[column1][column2]
    pf_mean = np.dot(summary.loc['Mean'], weights)
    return (pf_mean, pf_var)

def get_random_portfolios(universe):
    # creates `n` random portfolios from given set of stocks
    # returns n objects of type Portfolio.
    summary = get_summary_stats(universe) # gets summary stats req for computing portfolio
    covar_mat = universe.pct_change().cov()
    portfolios = []
    for i in range(1000):
        weights = np.random.random(len(summary.loc['Mean'].values))
        weights = weights/sum(weights)
        pf_mean, pf_var = get_portfolio_summary(covar_mat, summary, weights)

        # Convert weekly return to annual return
        pf_mean_annual = ((1 + pf_mean)**52 - 1)*100
        pf_var_annual = 52*pf_var
        pf_std_annual = np.sqrt(pf_var_annual)*100
        portfolios.append(Portfolio(list(summary.columns.values), list(weights), pf_mean_annual, pf_std_annual))
        # print(summary.columns.values, weights, pf_mean, pf_var)
    return portfolios

def create_portfolios(scrips):
    candles = datareader.get_candles(scrips, '2010-01-01', '2020-01-01')
    universe = merge_candles(candles) # represents all the stocks user has requested for.
    portfolios = get_random_portfolios(universe)
    return portfolios
