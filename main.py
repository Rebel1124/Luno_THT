#### Import Python Libraries #################################################################################################################

import json
import pandas as pd
# import numpy as np
import streamlit as st
import plotly.express as px
from PIL import Image
from streamlit_lottie import st_lottie

#### Import Plotly Graph Functions
from plotlyGraphs import tradeDistPerMonth, volumeDistPerMonth, pieGraph, marketPairLine, marketPairVolume, clientMonthlyStatusAvg, monthlyClientVolumeNormalised

#### Set Streamlit Page Settings
st.set_page_config(
    page_title="Customer Analysis",
    page_icon="📊",
    initial_sidebar_state="expanded",
    layout="wide"
)

#### Function to convert dataframe to csv file for download
@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

# Import Lottie File and Luno Image
banner = Image.open('./assets/lunoLogo.png')
url = './assets/analysis1.json'
with open(url, 'r') as fson:  
    res = json.load(fson)
url_json = res

# Colour Theme for Graphs
colors = px.colors.qualitative.Vivid

#### Import csv files and read as pandasdataframes ##########################################################################################

accounts_path = "./files/accounts.csv"
ledger_path = "./files/ledger_entries.csv"
trades_path = "./files/trades.csv"
rates_path = "./files/rates.csv"

accounts = pd.read_csv(accounts_path)
ledger = pd.read_csv(ledger_path)
trades = pd.read_csv(trades_path)
rates = pd.read_csv(rates_path)


############################################################################################################################################
#### Data Cleaning ######################################################################################################################### 
############################################################################################################################################

#### Ledger File ###########################################################################################################################
comment = '''
For the ledger File, I converted the timestamp to datetime addded columns for the year-month, day and hour of transaction.
The timestamp_at file was converted to datetime to make it easier to merge with the rates file - which contained the historical currency/usd values.
For this I specifically created the hourly column, which contained the transaction hour along with the  date.
The day and hour columns were added to get a better understanding of the distribution of transactions/trades over the days of the month 
as well as hours in a day i.e. for each month analysed - which days/hours were the most active. 
'''
ledger['timestamp_at_date'] = pd.to_datetime(ledger['timestamp_at'])
ledger['year_month'] = ledger['timestamp_at_date'].dt.tz_localize(None).dt.to_period('M')
ledger['day'] = ledger['timestamp_at_date'].dt.day
ledger['hourly'] = ledger['timestamp_at_date'].dt.round('h')
ledger['hour'] = ledger['timestamp_at_date'].dt.hour

#### Trades File #########################################################################################################################
comment = '''
For this file I concatenated the base_currency with the counter_currency to get a column should the 
market_pair traded.
'''
trades['market_pair'] = trades['base_currency'] +'/'+ trades['counter_currency']

#### Rates File #########################################################################################################################
comment = '''
For the rates I converted the reference_at trade to datetime to make it consistent with the legder file timestamp_at column,
which helped merge the the files and get the hourly average rate for the traded currency pair.
'''
rates['reference_at_date'] = pd.to_datetime(rates['reference_at'])


#### Joinging/Merging data files #######################################################################################################

comment = '''
I first merged the ledger and accounts files based on account id's from the ledger and the id's from the account files.
By merging these two data files, a link could then be made from the transacting account in the ledger file (account id)
and the corresponding customer in the account file (user_id) 
'''

ledgerAccounts = pd.merge(
    ledger.sort_values('timestamp_at'), 
    accounts, 
    left_on='account_id', 
    right_on='id', 
    how='left',
    suffixes=('_ledger', '_account')
)

ledgerAccounts = ledgerAccounts.drop_duplicates()

comment = '''
Following this, I then merged this file with the trades file based on the foreign_id (from the accounts file) and the id (from the trades file) fields.
This allowed essentially gave me a view of those transactions that were due specifically to trading activity from the client or or other transactions namely:
sending/receiving crypto, withdrawing fiat, placing/cancelling limit orders. I then cleaned up the merged dataframe by dropping any duplicate rows/columns.
I also removed the transactions which were not due any trading activities. 

My reasoning for this was that since Luno operates primarily as an exchange, the primary source of revenue is from trading activity either through the exchange 
or broker and so with this in mind, I focused my study on analysing and drawing insights specifically from clients trading activities. 
'''

ledgerTrades = pd.merge(
    ledgerAccounts, 
    trades, 
    left_on='foreign_id', 
    right_on='id', 
    how='left',
    suffixes=('_ledger', '_trade')
)

ledgerTrades = ledgerTrades.drop_duplicates()
ledgerTrades.dropna(subset=['user_id'], inplace=True)
ledgerTrades = ledgerTrades.dropna(subset=['market_pair'])


comment = '''
Lastly, in order to calculate the usd_volume,  I calculated the hourly average rate (usd price) for each currency for each hour. I could have done more
to get more accurate price in terms of time - like trying to map exact trade/transaction times with the rates from the rates file. However since the times were
not exact, it would have resulted in a lot trades not coming through with a price and so I decided to use the hourly average - I felt that this would be fine
and would still provide a fair analysis of the data. 

For this I mapped the hourly column (created earlier) with the trasaction hour + date. This was to ensure that the correct average rates were being mapped
to the correct date and hour. From this I was able to calculate the usd volume trade by multiplying the balance_delta (ledger file) with the corresponding
average usd price.
'''

#### Calculate hourly average per currency per reference data hour
hourly_avg = rates.set_index('reference_at_date').groupby(['currency', pd.Grouper(freq='h')])['average_price_per_usd'].mean().reset_index()

#### map ledgerTrades file to the usd rate for the currency for that hour 
combined_df = pd.merge(
    ledgerTrades, 
    hourly_avg, 
    left_on=['hourly','currency'], 
    right_on=['reference_at_date', 'currency'], 
    how='left',
    suffixes=('_ledger', '_rates')
)

combined_df = combined_df.drop_duplicates()

#### calculate the usd_volumne per trade
combined_df['usd_volume'] = combined_df['balance_delta'] * combined_df['average_price_per_usd']


#############################################################################################################################################
################ Transacting Segments Mapping ###############################################################################################
#############################################################################################################################################

comment = '''
Next I had to work out the transacting segment for each customer for each month - ensuring that clients received only one status per month.
We were given 4 client status to map nemely: New, Returning, Churned and Ractivated. Since we were only given 3 months worth of data (Jan-2020 to March-2020),
I made the assumption the clients trading in first month would all be classified as returning - without December-2019 data, it was not possible to identify
New, Churned or Reactivated clients and as such, I made the assumption that all clients traded before and were returning (Luno was established in 2013).

The process I followed was to identify the unique users (based on their user_id's) for each month which were stored as lists and then
to from this work out the users the either new or missing from monthly lists. The results from this would then help classify those customers
into ther respective status for the particular month.

Thereafter once I had the customer status for each it then became a matter of mapping these classifications into the data for that client. 
The steps followed are outlined below:
'''

################################################################################################################################################
#### Step 1: Obtain the unique users that traded for each month ################################################################################
################################################################################################################################################

users_jan_2020 = combined_df[combined_df['year_month'] == '2020-01']['user_id'].unique().tolist()
users_feb_2020 = combined_df[combined_df['year_month'] == '2020-02']['user_id'].unique().tolist()
users_mar_2020 = combined_df[combined_df['year_month'] == '2020-03']['user_id'].unique().tolist()
all_users = combined_df['user_id'].unique().tolist()

################################################################################################################################################
#### Step 2: Work out customers that are new/missing from either monthly list ##################################################################
################################################################################################################################################

comment = '''
Churned customers are those that traded the previous month but are missing from the current month
For Customers churned for Feb would appear in the January customer list (previous month) BUT NOT in the Feb customer list (current month)
Similarly for clients churned in March - they would be present in the Feb client list but not in the March list 
'''
churned_feb = list(set(users_jan_2020) - set(users_feb_2020))
churned_mar = list(set(users_feb_2020) - set(users_mar_2020))

#### New Clients would be present in the current month but not in ANY of the preceeding months###############################################
new_feb = list(set(users_feb_2020) - set(users_jan_2020))
new_mar = list(set(users_mar_2020) - set(users_feb_2020) - set(users_jan_2020))

#### Reactivated Customers were those clients that appeared in the March Client list AND in the CHURNED Febuary customer list################
reactivated_mar = list(set(users_mar_2020) & set(churned_feb))

#### Returning Customers were those that traded in both the current and preceeding months - so appeared in both customer lists ##############
returning_users_feb = list(set(users_feb_2020) & set(users_jan_2020))
returning_users_mar = list(set(users_mar_2020) & set(users_feb_2020))

################################################################################################################################################
#### Step 3: After obtaining the customer statuses for each month I then mapped them to our dataframe using teh mask method as below ###########
################################################################################################################################################

# Initialize status column
combined_df['status'] = 'Unknown'

# 2020-01: All users are Returning
combined_df.loc[combined_df['year_month'] == '2020-01', 'status'] = 'Returning'

# 2020-02: Classify based on lists
feb_mask = combined_df['year_month'] == '2020-02'
combined_df.loc[feb_mask & combined_df['user_id'].isin(new_feb), 'status'] = 'New'
combined_df.loc[feb_mask & combined_df['user_id'].isin(returning_users_feb), 'status'] = 'Returning'

# 2020-03: Classify based on lists  
mar_mask = combined_df['year_month'] == '2020-03'
combined_df.loc[mar_mask & combined_df['user_id'].isin(new_mar), 'status'] = 'New'
combined_df.loc[mar_mask & combined_df['user_id'].isin(returning_users_mar), 'status'] = 'Returning'
combined_df.loc[mar_mask & combined_df['user_id'].isin(reactivated_mar), 'status'] = 'Reactivated'

#### cleaned dataframe to have ONLY the required columns for our analysis ##############################################################
combined_df = combined_df[['timestamp_at', 'year_month', 'day', 'hour', 'foreign_id', 'user_id', 'status', 'usd_volume', 'market_pair']]

comment = '''
Finally, since each trade had both a debit and a credit amount, the resulting dataframe produced a positive and negative amount
for the same trade come through in the usd_volume column.  

First I calculated the average trade volume - using the groubpy function I calculated the |absolute| mean trade volume
I could have dropped the negative values but picked up that there were some trades that had more than one leg - so to be safe, I 
grouped trades and calculated the mean usd volume per trade.

Thereafter I merged this newly created dataframe with the previous dataframe, this ensured that only the positive trades volume would
would be represented for each trade whilst retaining all the information from the previous dataframe.
'''

#### Calulate the absolute usd volume traded for each trade
transactions_vol = combined_df.groupby('foreign_id')['usd_volume'].apply(lambda x: x.abs().mean()).reset_index()

#### Merge this dataframe with the previous dataframe 
users_combined = pd.merge(
    transactions_vol, 
    combined_df.sort_values('timestamp_at'), 
    left_on='foreign_id', 
    right_on='foreign_id', 
    how='left',
    suffixes=('_trans', '_combined')
)

#### Cleanup dataframe and drop any duplicate rows/columns
users_combined = users_combined.drop_duplicates(subset=['foreign_id'])
users_combined['usd_volume'] = users_combined['usd_volume_trans']
users_combined = users_combined.drop(['foreign_id', 'usd_volume_combined', 'usd_volume_trans'], axis=1)


comment = '''
Next for completeness, I wanted to add back the customers that were identified as churned in February and March.
These customers would not have traded in these months and so would have had a usd_volume amout of zero BUT
I want to included them so we could keep track and see the Churned clients.

I first added back the churned customers for Feb by creating a dictionary with the same fields as my dataframe for each Churned client
Each dictionary was stored in a list and then converted to a dataframe bfore being merged with the main dataframe and a new dataframe
was created with the complete list of customers per trade and absolute usd volume.

The process was repeated for the Churned customers for March.
'''


#### add churned users Feb
febDate = users_combined[users_combined['year_month'] == '2020-02']['timestamp_at'].max()
feb_churned_rows = []

#### create dictionary for each churned customer
for user in churned_feb:
    feb_churned_rows.append({
        'timestamp_at': febDate,
        'year_month': '2020-02',
        'day':'-',
        'hour':'-',
        'user_id': user,
        'status': 'Churned',
        'market_pair': '-',
        'usd_volume': 0,
    })

#### Convert to DataFrame and add to original
feb_churned_df = pd.DataFrame(feb_churned_rows)
updated_df = pd.concat([users_combined, feb_churned_df], ignore_index=True) 
updated_df = updated_df.drop_duplicates()


#### add churned users March
marDate = users_combined[users_combined['year_month'] == '2020-03']['timestamp_at'].max()
mar_churned_rows = []

for user in churned_mar:
    mar_churned_rows.append({
        'timestamp_at': marDate,
        'year_month': '2020-03',
        'day':'-',
        "hour":'-',
        'user_id': user,
        'status': 'Churned',
        'market_pair': "-",
        'usd_volume': 0,
    })

#### Convert to DataFrame and add to original
mar_churned_df = pd.DataFrame(mar_churned_rows)
updated_df = pd.concat([updated_df, mar_churned_df], ignore_index=True)   
updated_df = updated_df.drop_duplicates()

#### Arranged updated_df with complete customer list in ascending order
updated_df = updated_df.sort_values('timestamp_at')

#### Cleaned updated_df to make it easier to analyse and work with
updated_df['year_month'] = updated_df['year_month'].astype(str)
updated_df['day'] = updated_df['day'].astype(str)
updated_df['hour'] = updated_df['hour'].astype(str)
churn_mask = updated_df['timestamp_at'] == '-'
updated_df.loc[updated_df['status'] == "Churned", 'timestamp_at'] = '-'

#############
comment = '''
The updated_df was then used as the foundational dataframe and basis from which further analysis was done. Using this dataframe, I was abble
to aggregate and group data into year-month, client status, market-pairs etc... to produce visualizations and obtain insights into customer 
behaviour. 
'''

#############
# final dataframe for submission
final_df = updated_df[['timestamp_at', 'year_month', 'user_id', 'status', 'market_pair', 'usd_volume']]

############################################################################################################################################
#### Streamlit Sidebar widgets #############################################################################################################
############################################################################################################################################
with st.sidebar: 

            st_lottie(url_json,
            # change the direction of our animation
            reverse=True,
            # height and width of animation
            height=250,  
            width=250,
            # speed of animation
            speed=1,  
            # means the animation will run forever like a gif, and not as a still image
            loop=True,  
            # quality of elements used in the animation, other values are "low" and "medium"
            quality='high',
            # This is just to uniquely identify the animation
            key='Rocket' 
            )

st.sidebar.markdown("<h2 style='text-align: left; padding-left: 0px; font-size: 35px'><b>Graph Inputs<b></h2>", unsafe_allow_html=True)

attribute = st.sidebar.radio("attribute",['Count', 'Percent'], horizontal=True)
singleCurrency = st.sidebar.selectbox("select market_pair", updated_df['market_pair'].unique())
singleMonth = st.sidebar.radio("select year-month", updated_df['year_month'].unique(), horizontal=True)
status = st.sidebar.radio("select customers status",users_combined['status'].unique(), horizontal=True)

st.sidebar.markdown("<h2 style='text-align: left; padding-left: 0px; font-size: 35px'><b>Select Client<b></h2>", unsafe_allow_html=True)
client_id = st.sidebar.selectbox("customer id",updated_df['user_id'].unique())

############################################################################################################################################
############################################################################################################################################
#### Aggregrating and Grouping Dataframes for analysis #####################################################################################
############################################################################################################################################
############################################################################################################################################

comment = '''
Dataframe grouped by market_pair + year_month & aggregated by usd_volume
'''
monthly_pairs_df = updated_df.groupby(['market_pair', 'year_month']).agg(usd_volume=('usd_volume', 'sum')).reset_index()

# dataframe filtered on single market-pair
singleMonthlyPair_df= monthly_pairs_df[monthly_pairs_df['market_pair'] == singleCurrency]
singleMonthlyPair_df['usd_percentage'] = (singleMonthlyPair_df['usd_volume'] / singleMonthlyPair_df['usd_volume'].sum())

# dataframe filtered on single month
allPairsMonthly_df = monthly_pairs_df[monthly_pairs_df['year_month'] == singleMonth]
allPairsMonthly_df = allPairsMonthly_df[allPairsMonthly_df['market_pair'] != '-']
allPairsMonthly_df['usd_percentage'] = (allPairsMonthly_df['usd_volume'] / allPairsMonthly_df['usd_volume'].sum())

#############
comment = '''
Dataframe that first filters on the year_month & then groups by hour/day before aggregating by usd_volume
'''
users_combined_monthly = users_combined[users_combined['year_month'] == singleMonth]

# Group by hour and sum the USD amounts + calculate hourly percentage contribution
hourly_sums = users_combined_monthly.groupby('hour')['usd_volume'].sum().reset_index()
hourly_sums['usd_percentage'] = (hourly_sums['usd_volume'] / hourly_sums['usd_volume'].sum())

# Group by Day and sum the USD amounts + calculate the day's percentage contribution
daily_sums = users_combined_monthly.groupby('day')['usd_volume'].sum().reset_index()
daily_sums['usd_percentage'] = (daily_sums['usd_volume'] / daily_sums['usd_volume'].sum())


#############
comment = '''
Dataframe grouped by client status + market_pair & aggregated by usd_volume
'''
status_sums = updated_df.groupby(['status', 'market_pair'])['usd_volume'].sum().reset_index()
status_sums['usd_vol_pct'] = status_sums.groupby('status')['usd_volume'].transform(lambda x: (x / x.sum()))

# Dataframe filtered by customer status 
status_df = status_sums[status_sums['status'] == status]


#############
comment = '''
Dataframe grouped by user_id + market_pair & aggregated by usd_volume
'''
client_sums = updated_df.groupby(['user_id', 'market_pair'])['usd_volume'].sum().reset_index()
client_sums['usd_vol_pct'] = client_sums.groupby('user_id')['usd_volume'].transform(lambda x: (x / x.sum()))

# Dataframe filtered by customer id (single customer) 
singleCustomer_df = client_sums[client_sums['user_id'] == client_id]


#############
comment = '''
Here I wanted to count the number of clients that only trades 1 market_pair, 2 market_pairs, etc...
To do this I created 2 dataframe, the first dataframe is groupedby user_id and aggregated by market_pair (count).
Then using the first dataframe, I create a second dataframe (also using the groupby function) that counts the market_pairs traded
for each customer.
'''
client_pairs = client_sums.groupby(['user_id']).agg(pairs=('market_pair', 'count')).reset_index()
client_pairs_count = client_pairs.groupby(['pairs']).count().reset_index()
client_pairs_count = client_pairs_count.rename(columns={'user_id': 'customers'})

#############
comment = '''
The dataframes produced for the client monthly average vs. overall monthly average vs. monthly status average were a bit more involved and required several steps
First I created a dataframe groupedby user_id, year_month and status & aggregated by the mean usd volume. I also had to calculate another column that computed the 
average volume by status per month.

I then created a second column that was groupedby just the client status and year_month & also aggregated by the mean usd volume.

Thereafter I merged the two datframes - which gave me final datarame that consisted of each clients average volume as well as
the average monthly volume and avergae monthly volume for that months clients status - this was used as the base for the grouped bar graph for comparison
for each selected client.
'''

# Dataframe 1 grouped by user_id, year_month and status - aggregated by the mean usd volume - additional column for avg volume by status monthly was also computed 
client_average = updated_df.groupby(['user_id', 'year_month', 'status'])['usd_volume'].mean().reset_index()
client_average['avg_monthlyStatus_volume'] = client_average.groupby(['year_month', 'status'])['usd_volume'].transform('mean')

# Dataframe 2 grouped by year_month only and aggregated by mean usd volume
client_average_month = updated_df.groupby(['year_month'])['usd_volume'].mean().reset_index()

# Dataframe 3 produced by merging dataframe 1 and 2 from above based on year_month
clients_combined_avg = pd.merge(
    client_average, 
    client_average_month, 
    left_on=['year_month'], 
    right_on=['year_month'], 
    how='left',
    suffixes=('_status', '_monthly')
)

# Rename columns
clients_combined_avg = clients_combined_avg.rename(columns={'usd_volume_status': 'avg_client_volume', 'usd_volume_monthly': 'avg_monthly_volume'})

# Dataframe 3 filtered for a specific client (user_id) with year_month column cleaned up for better visualization
singleClient_average = clients_combined_avg[client_average['user_id'] == client_id]
singleClient_average['year_month'] = pd.to_datetime(singleClient_average['year_month'], format='%Y-%m')
singleClient_average = singleClient_average.sort_values('year_month')
singleClient_average['year_month'] = singleClient_average['year_month'].dt.strftime('%b %Y')

# Caluclate Statistics for selected client
currentStatus = singleClient_average['status'].iloc[-1]
singleAverage = singleClient_average['avg_client_volume'].iloc[-1]
statusAverage = singleClient_average['avg_monthlyStatus_volume'].iloc[-1]
monthlyAverage = singleClient_average['avg_monthly_volume'].iloc[-1]


# Dataframe 3 filtered on a specific month AND then status for all clients
allClients_monthlyAverage = clients_combined_avg[clients_combined_avg['year_month'] == singleMonth]
allClients_monthlyAverage = allClients_monthlyAverage[allClients_monthlyAverage['status'] == 'Returning']

# Calculate Number of clients that traded below the monthly average
monthlyMean_value = allClients_monthlyAverage['avg_monthlyStatus_volume'].mean()
clientsBelow_mean_count = (allClients_monthlyAverage['avg_client_volume'] < monthlyMean_value).sum()
total_count = allClients_monthlyAverage['avg_client_volume'].count()

# Calculate percentage
percentage_below_mean = (clientsBelow_mean_count / total_count) * 100

#################################################################################################################################################################
#### Streamlit Front End App Display ############################################################################################################################
#################################################################################################################################################################

comment = '''
The below code uses the dataframes produced above along with the imported plotly graphs to generate the front end for the App using Streamlit.
Streamlit is an easy to use and versatile front-end python library that enables the displaying of charts/tables and dataframes in the web browser.
The package has user input widgets which one can use to make the charts and analysis interactive - The idea is that users can easily play around 
with the data using the end and be better able to draw insights from it.
'''


#### Import Luno Logo and Display in Front-end along with App Heading
colA,colB = st.columns([1,8])
colA.image(banner, width=100)
colB.markdown("<h1 style='text-align: left; padding-left: 0px; font-size: 60px'><b>Luno Customer Analysis<b></h1>", unsafe_allow_html=True)


#### Summary of Business Questions Answers
markdown_content = """

## 1. Customer Status Distribution

My Analysis showed that the number of UNIQUE clients trading for each of the months Jan, Feb and March 
on exchange / broker were 15, 17 and 18 respectively. The 15 clients for Jan were all considered to be 
returning clients (this was the first month's data we had and so could not determine if they belonged to 
any of the other segments. Using this as our starting point, our analysis revealed the followed client status
 distribution for each of the months considered:

### Jan-2020 Clients (15 Active Customers)
- 15 Returning

### Feb 2020 Clients (17 Active Customers)
- 13 returning
- 2 Churned
- 4 New

### March 2020 Clients (18 Active Customers)
- 14 returning
- 3 Churned
- 2 New
- 2 Reactivated

## 2. Churn Rate for February and March

- **Feb Churn Rate** was calculated as **11.76%** (2 churned / 17 active)
- **March Churn Rate** was calculated as **16.67%** (3 churned / 18 active)

## 3. Customer Transacting Segment Trends

Our analysis revealed that for new customers the preferred market-pair was XBT/MYR. 
As will be shown below, just over usd 11k of this pair were bought by new clients over Feb and March. 
This was somewhat surprising given that the XBT/ZAR market-pair was by far the most traded currency 
(over $1,9m traded) over the three months investigated. It was still the most popular pair for returning 
clients but not for new clients who preferred XBT/MYR – this would suggest that we had more new clients
from Malaysia than South Africa.

## 4. Average Trade Volume by Transacting Segment

Our findings show that for returning customers only, the average volume traded for each of the months 
were $926, $242 and $530 for Jan, Feb and March respectively. On average about 70 percent of returning customers 
traded below this average each month – indicating that there were some customers (about 30 percent) that traded significantly higher than the mean monthly average.

We also note the drop in average USD volume traded for returning customers in Feb (usd 242) compared to Jan (usd 926) and March (usd 530). I would say that once reason for 
this could be the price of XBT/ZAR in Feb. Bitcoin rallied hard in Jan, which would have contributed to the higher volume seen for this month. However, 
in February the Bitcoin Price seem to stagnate and sometime during that month began to decline with the trend continuing down in March.

Returning customers would have done most of their purchasing in Jan during the bull run and would appear to have stood back in Feb particularly,
they re-entered again in March when prices were at more attractive levels to buy.

"""

#### Display the content in expander
with st.expander("📊 Summary of Business Analysis Questions", expanded=True):
    st.markdown("<h1 style='text-align: left; padding-left: 0px; font-size: 40px'><b>Summary of Business Question Answers<b></h1>", unsafe_allow_html=True)
    st.download_button("Download Final Dataframe",convert_df(final_df),"final_clean_df.csv", "text/csv",key='final_clean_df-csv')
    st.markdown(markdown_content)
    
#################################################################################################################################################################
#### Graphs 1 displays the Hourly Trade Distribution Per Month in Count and Percentage ##########################################################################
#### Graphs 2 displays the Hourly USD Volume Distribution Per Month in Count and Percentage #####################################################################
#################################################################################################################################################################

st.markdown("<h2 style='text-align: left; color: royalblue; padding-left: 0px; font-size: 35px'><b>Hourly Distribution Per Month<b></h2>", unsafe_allow_html=True)
col1, col2 = st.columns([1,1])

col1.plotly_chart(tradeDistPerMonth(users_combined_monthly, attribute, 'hour', colors[0], 'Graph 1 - Hourly Trade Distribution Per Month'))
showHourlyTrades = col1.toggle('Show hourly trades')
if showHourlyTrades:
      col2.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Hourly Trades<b></h2>", unsafe_allow_html=True)
      col1.dataframe(users_combined_monthly)
      col1.download_button("Download",convert_df(users_combined_monthly),"hourly_trades.csv", "text/csv",key='hourly_trades-csv')

col2.plotly_chart(volumeDistPerMonth(hourly_sums, attribute, 'hour', colors[2], 'Graph 2 - Hourly USD Volume Distribution Per Month'))
showHourlyVolume = col2.toggle('Show hourly volume')
if showHourlyVolume:
      col2.subheader('Hourly Volume')
      col2.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Hourly Volume<b></h2>", unsafe_allow_html=True)
      col2.dataframe(hourly_sums)
      col2.download_button("Download",convert_df(hourly_sums),"hourly_volumes.csv", "text/csv",key='hourly_volume-csv')


#################################################################################################################################################################
#### Graphs 3 displays the Daily Trade Distribution Per Month in Count and Percentage ###########################################################################
#### Graphs 4 displays the Daily USD Volume Distribution Per Month in Count and Percentage ######################################################################
#################################################################################################################################################################

st.markdown("<h2 style='text-align: left; color: royalblue; padding-left: 0px; font-size: 35px'><b>Daily Distribution Per Month<b></h2>", unsafe_allow_html=True)
col3, col4 = st.columns([1,1])

col3.plotly_chart(tradeDistPerMonth(users_combined_monthly, attribute, 'day', colors[1], 'Graph 3 - Daily Trade Distribution Per Month'))
showDailyTrades = col3.toggle('Show daily trades')
if showDailyTrades:
      col3.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Daily Trades<b></h2>", unsafe_allow_html=True)
      col3.dataframe(users_combined_monthly)
      col3.download_button("Download",convert_df(users_combined_monthly),"daily_trades.csv", "text/csv",key='daily_trades-csv')

col4.plotly_chart(volumeDistPerMonth(daily_sums, attribute, 'day', colors[3], 'Graph 4 - Daily USD Volume Distribution Per Month'))
showHourlyVolume = col4.toggle('Show daily volume')
if showHourlyVolume:
      col4.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Daily Volume<b></h2>", unsafe_allow_html=True)
      col4.dataframe(daily_sums)
      col4.download_button("Download",convert_df(daily_sums),"daily_volumes.csv", "text/csv",key='daily_volume-csv')


#################################################################################################################################################################
#### Graphs 5 displays the Overall Market-Pair Volume Traded for each Momth #####################################################################################
#### Graphs 6 displays the Number (Count) of Market-Pairs traded by Clients #####################################################################################
#################################################################################################################################################################

st.markdown("<h2 style='text-align: left; color: royalblue; padding-left: 0px; font-size: 35px'><b>Monthly USD Volume Per Market Pair<b></h2>", unsafe_allow_html=True)
col5, col6 = st.columns([1,1])
col5.plotly_chart(marketPairVolume(allPairsMonthly_df, attribute, f'Graph 5 - USD Volume Traded for {singleMonth}'))
showAllPairsVolume = col5.toggle('All Mkt_Pairs Volume')
if showAllPairsVolume:
      col5.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>All Mkt_Pairs Volume<b></h2>", unsafe_allow_html=True)
      col5.dataframe(allPairsMonthly_df)
      col5.download_button("Download",convert_df(allPairsMonthly_df),"all_mkt_pairs_volume.csv", "text/csv",key='all_mkt_pairs-csv')

col6.markdown(" ")
col6.markdown(" ")
col6.plotly_chart(pieGraph(client_pairs_count, label='pairs', value='customers', gap=0.3, title='Graph 6 - Client Pairs Traded'))
col6.markdown(" ")
showClientPairsCount = col6.toggle('Show Client Pairs Count')
if showClientPairsCount:
      col6.subheader('Client Pairs Count')
      col6.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Client Pairs Count<b></h2>", unsafe_allow_html=True)
      col6.dataframe(client_pairs_count)
      col6.download_button("Download",convert_df(client_pairs_count),"client_pairs_count.csv", "text/csv",key='client_pairs_count-csv')


#################################################################################################################################################################
#### Graphs 7 displays the Monthly Volume traded for a Single Currency Pair #####################################################################################
#### Graphs 8 displays % contribution/split traded for that single currency for each of the months ##############################################################
#################################################################################################################################################################

st.markdown("<h2 style='text-align: left; color: royalblue; padding-left: 0px; font-size: 35px'><b>Monthly Currency Split<b></h2>", unsafe_allow_html=True)
st.markdown(" ")
st.markdown(" ")
col7, col8 = st.columns([1,1])

col7.plotly_chart(marketPairLine(singleMonthlyPair_df, f'Graph 7 - {singleCurrency} Volume Traded per Month'))
showMonthlyVolTraded = col7.toggle('Show Monthly Volume Traded')
if showMonthlyVolTraded:
      col7.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Monthly Volume Traded<b></h2>", unsafe_allow_html=True)
      col7.dataframe(singleMonthlyPair_df)
      col7.download_button("Download",convert_df(singleMonthlyPair_df),"monthly_volume_traded.csv", "text/csv",key='monthly_volume_traded-csv')

col8.plotly_chart(pieGraph(singleMonthlyPair_df, label='year_month', value='usd_volume', gap=0, title=f'Graph 8 - {singleCurrency} Split Per Month'))
showMonthlyCcySplit = col8.toggle('Show Monthly Currency Split')
if showMonthlyCcySplit:
      col8.subheader('Monthly Currency Split')
      col8.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Monthly Currency Split<b></h2>", unsafe_allow_html=True)
      col8.dataframe(singleMonthlyPair_df)
      col8.download_button("Download",convert_df(singleMonthlyPair_df),"monthly_currency_split.csv", "text/csv",key='monthly_currency_split-csv')


#################################################################################################################################################################
#### Graphs 9 the Total Volume Traded by the selected Client for each Currency Pair #############################################################################
#### Graphs 10 displays the Volume Traded by Status Only ########################################################################################################
#################################################################################################################################################################

st.markdown("<h2 style='text-align: left; color: royalblue; padding-left: 0px; font-size: 35px'><b>USD Volume Traded Per Month by Client & Status<b></h2>", unsafe_allow_html=True)
col9, col10 = st.columns([1,1])

col9.plotly_chart(marketPairVolume(singleCustomer_df, 'usd_volume', 'Graph 9 - USD Volume Traded by Selected Client'))
showCustomerVol = col9.toggle('Show Customer Volume')
if showCustomerVol:
      col9.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Customer Volume Traded<b></h2>", unsafe_allow_html=True)
      col9.dataframe(singleCustomer_df)
      col9.download_button("Download",convert_df(singleCustomer_df),"customer_volume.csv", "text/csv",key='customer_volume-csv')


col10.plotly_chart(marketPairVolume(status_df, 'usd_volume', 'Graph 10 - USD Volume Traded By Status'))
showStatusVol = col10.toggle('Show Status Volume')
if showStatusVol:
      col10.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Status Volume Traded<b></h2>", unsafe_allow_html=True)
      col10.dataframe(status_df)
      col10.download_button("Download",convert_df(status_df),"status_volume.csv", "text/csv",key='status_volume-csv')



#################################################################################################################################################################
#### Graphs 11 displays the Avg Monthly Volume Traded by the selected Client vs. Status Monthly Average vs. Overall Monthly Average #############################
#### Graphs 12 displays the distribution of average volume for clients in the status for that month #############################################################
#################################################################################################################################################################

st.markdown(" ")
st.markdown(" ")
st.markdown("<h2 style='text-align: left; color: royalblue; padding-left: 0px; font-size: 35px'><b>Monthly Client Status Avg Volume Comparison<b></h2>", unsafe_allow_html=True)
col11, col12 = st.columns([1,1])

col11.plotly_chart(clientMonthlyStatusAvg(singleClient_average, title='Graph 11 - Average USD Volume Traded by Client vs. Monthly Average vs. Status Average',))
st.sidebar.write(f"💡 Current Client Status: **{currentStatus}**")
st.sidebar.write(f"💡 Latest Client Monthly Average: **${singleAverage:,.2f}**")
st.sidebar.write(f"💡 Monthly Status Average: **${statusAverage:,.2f}**")
st.sidebar.write(f"💡 Latest Month Average: **${monthlyAverage:,.2f}**")
showSingleClientComp= col11.toggle('Show Client Comparison')
if showSingleClientComp:
      col11.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Client Avg Vol Comparison<b></h2>", unsafe_allow_html=True)
      col11.dataframe(singleClient_average)
      col11.download_button("Download",convert_df(singleClient_average),"single_client_comp.csv", "text/csv",key='single_client_comp-csv')

col12.plotly_chart(monthlyClientVolumeNormalised(allClients_monthlyAverage, title='Graph 12 - Distribution of Monthly Average USD Volume Traded By Returning Clients'))
col12.write(f"💡 **{clientsBelow_mean_count}** out of **{total_count}** clients ({percentage_below_mean:.2f}%) are below the mean (${monthlyMean_value:,.2f})")
showAllClientComp= col12.toggle('Show Monthly Status Avg Comparison')
if showAllClientComp:
      col12.markdown("<h2 style='text-align: left; color: black; padding-left: 0px; font-size: 20px'><b>Monthly Status Avg Comparison<b></h2>", unsafe_allow_html=True)
      col12.dataframe(allClients_monthlyAverage)
      col12.download_button("Download",convert_df(allClients_monthlyAverage),"all_client_comp.csv", "text/csv",key='all_client_comp-csv')

#################################################################################################################################################################
#################################################################################################################################################################
