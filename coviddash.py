import pandas as pd
import numpy as np
import chart_studio.plotly as py
import plotly.graph_objs as go
import cufflinks
from plotly.offline import iplot
from plotly.subplots import make_subplots

#cufflinks in offline mode
import cufflinks
cufflinks.go_offline(connected=True)

import seaborn as sns
sns.set(style="darkgrid")
import plotly.express as px

#Import Data .csv from Our World in Data
world = pd.read_csv('https://covid.ourworldindata.org/data/ecdc/total_cases.csv')

countries = world.columns
countries = countries[1:] #Remove Cases from Country Names

#Set first value to zero if missing
for i in countries:
    if np.isnan(world[i][0]):
        world[i][0]=0

#Impute missing values to previous day's value if there's missing data
for i in countries:
    for j in range(1, len(world)):
        if np.isnan(world[i][j]):
            world[i][j] = world[i][j-1]


for a in countries:
    #Calculate Basic Reproduction Number and 10 Day Average
    basic_reproductive_value = []
    country_values = world.loc[:,a].values
    new = [] #New cases per day
    new.append(country_values[0])
    for i in range(1, len(country_values)):
        new.append(float(country_values[i])-float(country_values[i-1]))
    
    #Calculate the average new cases for past 2 weeks
    newAvg = []
    
    #No average for the first 14 days
    for i in range(0, 13):
        newAvg.append(new[i])
    
    #Find 14 day moving average of new cases to smooth data
    for i in range(13, len(new)):
        total = float(0)
        for j in range(0, 14):
            total+=float(new[i-j])
        newAvg.append(str(float(total)/14))
        
    
    #Calculate R0 Values using 14 day average
    basic_reproductive_value.append(str(0)) #Append zero for first day
    for i in range(1, len(country_values)):
        if int(new[i-1]) == 0:
            basic_reproductive_value.append(str(0))
        else:
            basic_reproductive_value.append(str(float(newAvg[i])/float(newAvg[i-1])))


    
    #Fill first 10 days with not average 
    avg = []        
    for i in range(0, 9):
        avg.append(basic_reproductive_value[i])

    #Last 10 days average
    for i in range(9, len(basic_reproductive_value)):
        total = float(0)
        for j in range(0, 10):
            total+=float(basic_reproductive_value[i-j])
        avg.append(str(float(total)/10))

    #Update World Dataframe
    world[a+'new'] = new
    world[a+'newAvg'] = new
    world[a+'r0'] = basic_reproductive_value
    world[a+'r0avg'] = avg


#Graph Cases Function

def graph_cases(country):
    fig = make_subplots(specs=[[{"secondary_y": True}, ]])
    fig.add_trace(
        go.Scatter(x=world['date'], y=world[country], name="# Total Cases"),
        secondary_y=False, 
    )
    
    fig.add_trace(
        go.Scatter(x=world['date'], y=world[country+'r0avg'], name="Approximate R0 10 Day Average"),
        secondary_y=True, 
    )
    return graph_format(country, fig)

#Formaat Graph
def graph_format(country, fig):
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        title_text=country + " Covid-19 Cases and Basic Reproduction Number"
    )
    # Set x-axis title
    fig.update_xaxes(title_text="Date")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Total</b> Cases", secondary_y=False)
    fig.update_yaxes(title_text="<b>R0</b> 10 Day Average", secondary_y=True)
    
    #Change Size
    fig.update_layout(
    autosize=False,
    width=1000,
    height=600)
    
    return fig


# In[537]:


#Cacluate Values for Choropleth
r0avg = []
#Put latest 10 day moving averages of r0 in array
for i in range(0, len(countries)):
    r0avg.append(world[countries[i] + 'r0avg'][len(world)-1])


#Create new dataframe with Country, Code, and r0avg
df = pd.DataFrame(index=range(0, len(countries)), columns=["Country", "Code", "r0avg"])
#To convert country names to codes for use with map
codes = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv')

#Populate dataframe
for i in range(0, len(countries)):
    df['Country'][i] = countries[i]
    df['r0avg'][i] = r0avg[i]
    
    #Put in country code
    for j in range(0, len(codes)):
        if codes['COUNTRY'][j] == countries[i]:
            df['Code'][i] = codes['CODE'][j]
            break
            
            
    #Make sure value is between 0 and 3        
    if float(df['r0avg'][i]) < 0:
        df['r0avg'][i] = 0 #Remove Outliers
    elif  float(df['r0avg'][i]) > 3:
        df['r0avg'][i] = 3 #Remove Outliers


# In[538]:



choropleth = go.Figure(data=go.Choropleth(
    locations = df['Code'],
    z = df['r0avg'],
    text = df['Country'],
    colorscale = 'Bluered_r',
    autocolorscale=False,
    reversescale=True,
    marker_line_color='darkgray',
    marker_line_width=0.5,
    colorbar_title = 'Covid-19<br>R0 10 Day Average',
))

choropleth.update_layout(
    title_text='R0 10 Day Average',
    geo=dict(
        showframe=False,
        showcoastlines=False,
        projection_type='equirectangular'
    ),
    annotations = [dict(
        x=0.55,
        y=0.1,
        xref='paper',
        yref='paper',
        text='Covid-19 Current Climate',
        showarrow = False
    )]
)


# In[539]:


#Write Data to File
countries = ['World', 'United States', 'Canada', 'United Kingdom', 'Switzerland', 'Sweden', 'New Zealand']
with open('dashboard.html', 'a') as f:
    f.seek(0)
    f.truncate() #Erase Existing File
    
    l = len(world)
    f.write('<h1>World Total Cases: ' + str(world['World'][l-1]) + ' | ')
    f.write('World R0 10 Day Average: ' + str(world['Worldr0avg'][l-1][0:4]) + '  <br />')
    f.write('US Total Cases: ' + str(world['United States'][l-1]) + ' | ')
    f.write('US R0 10 Day Average: ' + str(world['United Statesr0avg'][l-1][0:4]) + '</h1>')
    f.write(choropleth.to_html(full_html=False, include_plotlyjs='cdn'))
    #f.write(USOld.to_html(full_html=False, include_plotlyjs='cdn'))
    for i in countries:
        f.write(graph_cases(i).to_html(full_html=False, include_plotlyjs='cdn'))

