# modifiedMonteCarlo


This is an implementation of time series forecasting based on the paper "Forecasting Hotel Arrivals and Occupancy Using Monte Carlo Simulation"
by Zakhary et al, 2009.

It has been modified from the original paper presentation to:
1) Use non-sequential season designations
2) Work to make property by property occupancy forecasts which ouput a time series of 0, 1 for the testing periods specified.
3) Time Series success is evaluated using a confusion matrix.


This implementation is not very useful for out of box use.  It has been heavily customised to the database structure and database data inherited.
