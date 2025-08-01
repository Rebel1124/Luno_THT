#### Import Python Libraries #################################################################################################################

import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go

##############################################################################################################################################
#### Graph Functions #########################################################################################################################
##############################################################################################################################################

'''
In trying to make my code more readable, I wrote all the code for the graphs for my streamlit app in this seperate python file.
All the graphs were written within functions and cimported/called into the main.py file. I provide brief descriptions of each function/graph
below. 

Another reason for doing it this way is that the graphs become replicable in that I don't have to write the full code out again to produce 
a graph, I can simply change the dataframe and the appropriate grape will be displayed. Also its easier to control in that any chages needed
can be made in one play instead of multiple places throughout the code.


Inventory of Graphs:

~tradeDistPerMonth - Hisogram that plots the trade distribution over the month for hourly | daily trades

~volumeDistPerMonth - Bar graph the plots the USD volume traded over the month for hourly | daily trades

~pieGraph - Pie chart that plots the monthly split (% traded) for a single currency | split for the number of pairs traded by client
             (i.e. how many clients traded only market-pai, how many traded 2 pairs, etc...)   

~marketPairLine - Line graph the plots the monthly USD volume traded for a chosen currency

~marketPairVolume - Bar graph that plots the USD volume traded per month | monthly Usd volume traded by Status | monthly USD volume traded by client

~clientMonthlyStatusAvg - Grouped Bar graph that plots a single clients average USD volume traded per month vs. monthly USD volume average vs. monthly USD volume status average 

~monthlyClientVolumeNormalised - Normalised (Density Plot) of customers trading in specific Average USD Volume ranges per month with monthly average line

'''

##############################################################################################################################################
#### tradeDistPerMonth #######################################################################################################################
##############################################################################################################################################

'''
tradeDistPerMonth - Hisogram that plots the trade distribution over the month for hourly | daily trades - the function is imported into the
                    main.py file, one can then just change the dataframe (df), attribute (count or percentage), timeframe (hour or day), 
                    color and title of the chart. The below function will be called and will display a histogram for the chosen inputs.
'''

def tradeDistPerMonth(df, attribute, timeframe, color, title):
    figTradeDist = go.Figure()

    if attribute == "Percent":
        template = '%{y:.2%}'
        figTradeDist.add_trace(go.Histogram(
        x=df[timeframe],
        histnorm='probability',
        name=timeframe, # name used in legend and hover labels
        texttemplate=template,
        xbins=dict( # bins used for histogram
            start=df[timeframe].min(),
            end=df[timeframe].max()+1,
            size=1
        ),
        marker_color=color,
        textfont=dict(color='white'),
        opacity=0.75
    ))
    else:
        template='%{y:,.0f}'
        figTradeDist.add_trace(go.Histogram(
        x=df[timeframe],
        name=timeframe, # name used in legend and hover labels
        texttemplate=template,
        xbins=dict( # bins used for histogram
            start=df[timeframe].min(),
            end=df[timeframe].max()+1,
            size=1
        ),
        marker_color=color,
        textfont=dict(color='white'),
        opacity=0.75
    ))


    figTradeDist.update_layout(
        title_text=title, # title of plot
        title_font_color='black',
        xaxis_title_text=timeframe, # xaxis label
        yaxis_title_text='frequency', # yaxis label
        bargap=0.2, # gap between bars of adjacent location coordinates
        bargroupgap=0.1, # gap between bars of the same location coordinates
        xaxis=dict(
            title_font_color='darkgray',  # X-axis title color
            tickfont=dict(color='darkgray')  # X-axis tick labels color
        ),
        yaxis=dict(
            title_font_color='darkgray',  # Y-axis title color
            tickfont=dict(color='darkgray')  # Y-axis tick labels color
        ),
        legend=dict(
            font=dict(color='darkgray')  # Legend text color
        )
    )

    return figTradeDist


##############################################################################################################################################
#### volumeDistPerMonth ######################################################################################################################
##############################################################################################################################################

'''
volumeDistPerMonth - Bar graph the plots the USD volume traded over the month for hourly | daily trades - the function is imported into the
                    main.py file, one can then just change the dataframe (df), attribute (count or percentage), timeframe (hour or day), 
                    color and title of the chart. The below function will be called and will display a bar graph for the chosen inputs.
'''

def volumeDistPerMonth(df, attribute, timeframe, color, title):
    figVolDist = go.Figure()

    if attribute == "Percent":
        figVolDist.add_trace(go.Bar(
        y=df['usd_percentage'],
        x=df[timeframe],
        name=timeframe, # name used in legend and hover labels
        texttemplate='%{y:.2%}',
        marker_color=color,
        textfont=dict(color='white'),
        opacity=0.75
    ))
    else:
        figVolDist.add_trace(go.Bar(
        y=df['usd_volume'],
        x=df[timeframe],
        name=timeframe, # name used in legend and hover labels
        texttemplate='%{y:,.0f}',
        marker_color=color,
        textfont=dict(color='white'),
        opacity=0.75
    ))


    figVolDist.update_layout(
        title_text=title, # title of plot
        title_font_color='black',
        xaxis_title_text=timeframe, # xaxis label
        yaxis_title_text='frequency', # yaxis label
        bargap=0.2, # gap between bars of adjacent location coordinates
        bargroupgap=0.1, # gap between bars of the same location coordinates
        xaxis=dict(
            title_font_color='darkgray',  # X-axis title color
            tickfont=dict(color='darkgray'),  # X-axis tick labels color
            tickmode='linear',
            tick0=0,
            dtick=1  # Show every hour
        ),
        yaxis=dict(
            title_font_color='darkgray',  # Y-axis title color
            tickfont=dict(color='darkgray')  # Y-axis tick labels color
        ),
        legend=dict(
            font=dict(color='darkgray')  # Legend text color
        )
    )

    return figVolDist

##############################################################################################################################################
#### pieGraph ################################################################################################################################
##############################################################################################################################################

'''
pieGraph - Pie chart that plots the monthly split (% traded) for a single currency | split for the number of pairs traded by client - 
            the function is imported into the main.py file, one can then just change the dataframe (df), labels, values, gap and title. 
            The below function will be called and will display a pir chart for the chosen inputs.
'''

def pieGraph(df, label, value, gap, title):
    figPie = go.Figure(data=[go.Pie(labels=df[label], values=df[value],marker_colors=px.colors.sequential.Sunset_r, hole=gap)])
    figPie.update_layout(
    title_text=title, # title of plot
    title_x=0.25,
    title_y=1,
    title_font_color='black',
    width=400,  # Set the width (smaller value = smaller chart)
    height=400,
    margin=dict(t=40, b=40, l=0, r=0), 
    legend=dict(
        orientation="v",
        yanchor="bottom",
        y=0.35,
        xanchor="center",
        x=1)
    )
    return figPie

##############################################################################################################################################
#### marketPairLine ##########################################################################################################################
##############################################################################################################################################

'''
marketPairLine - Line graph the plots the monthly USD volume traded for a chosen currency - the function is imported into the
                    main.py file, one can then just change the dataframe (df) and title of the chart. 
                    The below function will be called and will display a line graph for the monthly currency volume traded.
'''

def marketPairLine(df, title):

    df = df.sort_values('year_month')

    figLine = go.Figure()
    figLine.add_trace(
    go.Scatter(
        x=df['year_month'],
        y=df['usd_volume'],
        name='market-pair-volume',
        texttemplate='%{y:,.0f}',
        text=df['usd_volume'],  # The values to display
        textposition="top center",  # Position above the points
        mode='lines+markers+text',  # Include text mode
        line_color="#004e9b",
        showlegend=False,
        hovertemplate='<b>%{x}</b><br>USD Volume: %{y:,.0f}<extra></extra>'
    ))

    figLine.update_layout(title_text=title,
                            title_font_color='black',
                            xaxis_title='Date',
                            yaxis_title='USD Volume',
                            height=400,
                            width=500,
                            margin=dict(t=30, b=100, l=0, r=100), 
                            xaxis=dict(
                            tickmode='array',
                            tickvals=df['year_month'],  # Use your actual data values
                            ticktext=df['year_month'].unique().tolist()  # Custom labels to display
                            )
                        )
    
    return figLine
       
##############################################################################################################################################
#### marketPairVolume ########################################################################################################################
##############################################################################################################################################

'''
marketPairVolume - Bar graph that plots the USD volume traded per month | monthly Usd volume traded by Status | monthly USD volume traded by client - 
                   the function is imported into the main.py file, one can then just change the dataframe (df), metric (usd volume in our case), and title.
                   The below function will be called and will display a bar graph for the chosen inputs.
                   The distinction with this graph is that a new trace is added for each market-pair - this makes the graph more interactive and easier 
                   to draw insights from.                 
'''

def marketPairVolume(df, attribute, title):

    market_pairs = df['market_pair'].unique()
    colors = px.colors.qualitative.Vivid[:len(market_pairs)] 

    figMktPair = go.Figure()

    if attribute == "Percent":
    # Add a trace for each market pair
        for i, market_pair in enumerate(market_pairs):
            pair_data = df[df['market_pair'] == market_pair]
            
            figMktPair.add_trace(go.Bar(
                x=pair_data['market_pair'],
                y=pair_data['usd_percentage'],
                texttemplate='%{y:.2%}',
                marker=dict(
                    color=colors[i % len(colors)],
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                name=market_pair, 
                hovertemplate='Status: %{x}<br>' +
                            'USD Volume: %{y:.2%}<br>' +
                            f'Market Pair: {market_pair}<br>'
            ))        

    else:

        # Add a trace for each market pair
        for i, market_pair in enumerate(market_pairs):
            pair_data = df[df['market_pair'] == market_pair]
            
            figMktPair.add_trace(go.Bar(
                x=pair_data['market_pair'],
                y=pair_data['usd_volume'],
                texttemplate='%{y:,.0f}',
                marker=dict(
                    color=colors[i % len(colors)],
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                name=market_pair, 
                hovertemplate='Status: %{x}<br>' +
                            'USD Volume: $%{y:,.2f}<br>' +
                            f'Market Pair: {market_pair}<br>'
            ))

    figMktPair.update_layout(
        title=title,
        title_font_color='black',
        xaxis_title='market-pair',
        yaxis_title='USD Volume',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01,
            font=dict(size=10),
        )
    )

    return figMktPair

##############################################################################################################################################
#### clientMonthlyStatusAvg  #################################################################################################################
##############################################################################################################################################

'''
clientMonthlyStatusAvg - Grouped Bar graph that plots a single clients average USD volume traded per month vs. monthly USD volume average vs. monthly USD volume status average - 
                         the function is imported into the main.py file, one can then just change the dataframe (df).
                         The below function will be called and will display a grouped bar graph for the chosen inputs.
'''

def clientMonthlyStatusAvg(df, title):

    colors = px.colors.qualitative.Vivid

    figClientAverage = go.Figure()

    figClientAverage.add_trace(go.Bar(
        x=df['year_month'],
        y=df['avg_client_volume'],
        marker=dict(
            color=colors[0],  # Cycle through colors if more pairs than colors
            opacity=0.7,
            line=dict(width=2, color='white')
        ),
        name='avg_client_volume',  # This appears in the legend
        hovertemplate='USD Volume: $%{y:,.2f}<br>'
    ))


    figClientAverage.add_trace(go.Bar(
        x=df['year_month'],
        y=df['avg_monthlyStatus_volume'],
        marker=dict(
            color=colors[1],  # Cycle through colors if more pairs than colors
            opacity=0.7,
            line=dict(width=2, color='white')
        ),
        name='avg_monthlyStatus_volume',  # This appears in the legend
        hovertemplate='USD Volume: $%{y:,.2f}<br>'
    ))

    figClientAverage.add_trace(go.Bar(
        x=df['year_month'],
        y=df['avg_monthly_volume'],
        marker=dict(
            color=colors[2],  # Cycle through colors if more pairs than colors
            opacity=0.7,
            line=dict(width=2, color='white')
        ),
        name='avg_monthly_volume',  # This appears in the legend
        hovertemplate='USD Volume: $%{y:,.2f}<br>'
    ))


    figClientAverage.update_layout(
        title=title,
        title_font_color='black',
        xaxis_title='Date',
        yaxis_title='Average USD Volume',
        showlegend=True,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=-0.12,
            font=dict(size=14.5),  # Smaller font since there might be many pairs
        )
    )

    return figClientAverage

##############################################################################################################################################
#### monthlyClientVolumeNormalised ###########################################################################################################
##############################################################################################################################################

'''
monthlyClientVolumeNormalised - Normalised (Density Plot) of customers trading in specific Average USD Volume ranges per month with monthly average line -  
                         the function is imported into the main.py file, one can then just change the dataframe (df).
                         The below function will be called and will display a normailised graph with vertical mean USD Volume line.
'''

def monthlyClientVolumeNormalised(df, title):

    figHist = ff.create_distplot([df['avg_client_volume']], group_labels=['avg_client_volume'], curve_type='kde', colors=["#004e9b"], show_hist=False)
    figHist.update_layout(title= 'KDE Plot', xaxis_title='Average USD Volume', yaxis_title='Frequency', height=400, width=400, margin=dict(l=50, r=0, b=0,t=100),
    showlegend=False,
        legend=dict(
        orientation="h",  # Horizontal legend
        x=0.95,            # Center the legend horizontally
        y=0.95,           # Position it slightly below the plot
        xanchor='center',  # Align legend horizontally
        yanchor='bottom'   # Align legend vertically
    ))


    # Add vertical line at mean
    figHist.add_shape(
        type='line',
        x0=df['avg_monthlyStatus_volume'].mean(), x1=df['avg_monthlyStatus_volume'].mean(),
        y0=0, y1=max(figHist['data'][0]['y']),
        line=dict(color='red', width=2, dash='dash')
    )

    # Add annotation for mean
    figHist.add_annotation(
        x=df['avg_monthlyStatus_volume'].mean(),
        y=max(figHist['data'][0]['y']) * 0.95,
        text=f"Mean: {df['avg_monthlyStatus_volume'].mean():.2f}",
        showarrow=True,
        arrowhead=2,
        ax=40,
        ay=-40
    )

    # Update layout
    figHist.update_layout(
        title = title,
        title_font_color='black',
        xaxis_title='Average USD Volume',
        yaxis_title='Density'
    )

    return figHist

##############################################################################################################################################
##############################################################################################################################################