# hos-payroll
Uses Python 2.7
Usage: python suncoast_hos.py
Output: m-d-y.csv and m-d-y-commute.csv

If a driver goes from off duty to on duty using the 'On Duty - Commuting' vehicle, the time records will be written to the -commute.csv file.  

Note:  create a config.py file in the same directory as suncoast_hos.py.  
The contents of config.py should be as follows:
token='abc123'
group='12345'
