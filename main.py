''' 30 day streamlit challenge :
day 4: advanced use case: data analysis
: ev car sales data
watch: https://www.youtube.com/watch?v=Yk-unX4KnV4&ab_channel=KenJee
'''
#%%
import streamlit as st
import polars as pl
import numpy as np

import datetime
from rich import print as rprint
# %%
# st.header("Button")
# left, right = st.columns(2)
# btn_reset = right.button("", icon=":material/sync:", type='tertiary')
# btn_hello = left.button("Hello", icon=":material/thumb_up:")
# if btn_hello:
#     st.write("Why hello there!")
# else:
#     st.write("Goodbye!")

# %%
data_path = "./IEA Global EV Data 2024.csv"

# %%
@st.cache_data
def read_data(file_path, columns=None):
    '''read csv data and return polars dataframe'''
    
    try:
        dataframe = pl.read_csv(file_path, columns=columns)
        return dataframe
    except Exception as e:
        rprint(f'[bold red]Error opening csv file : {e}[/bold red]')
# %%
df_orig = read_data(data_path)

# %%
df_orig.describe()
# %%
# for c in df.columns:
#     rprint(f'Column: {c}')
#     print(df[c].unique())


# %%
# Column	Description
# -------------------------------
# region: 	Geographic area where the data applies (e.g., “World”, “Europe”, “China”, “United States”) 
# category: 	Data category, such as “historical” (actual observed values) or “projected” (forecasts)
# parameter: 	Type of metric — e.g., “EV sales”, “EV stock share”, “EV stock” — indicates what is being measured
# mode: 	Transport mode: “Cars”, “Buses”, “Two-Wheelers”, etc. — specifies the vehicle category included
# powertrain: 	Type of electric powertrain: “BEV” (Battery Electric Vehicle), “PHEV” (Plug-in Hybrid), possibly “EV” for combined data
# year: 	Data year (from 2010 through 2024) — indicates the calendar year of each data point
# unit: 	Unit of measurement, such as “vehicles” or “percent” — clarifies the format of value
# value: 	Numeric value of the parameter for that year, region, mode, and powertrain — the actual data point

#%%
df = df_orig.clone()
rprint(df)
# %% metrics: historical and [mode, powertrain] sales
cond_historical = df["category"] == "Historical"
df_historical = df.filter(cond_historical)
rprint(df["category"].value_counts(), df_historical.shape)

cond_sales = df_historical["parameter"] == "EV sales"
df_hist_sales = df_historical.filter(cond_sales)
rprint(df_hist_sales.shape)
# %% select last 10 years
df_hist_sales = df_hist_sales.with_columns(pl.date(year=pl.col('year'), month=pl.lit(1), day=pl.lit(1)).alias('date'))
latest_year = pl.lit(df_hist_sales['date'].max())
rprint(latest_year)
df_hist_sales_last10yrs = df_hist_sales.filter(pl.col('date') >= latest_year - pl.duration(weeks=52*10))
rprint(df_hist_sales_last10yrs['year'].value_counts().sort(by='year'))
# rprint(df_hist_sales['year'].value_counts().sort(by='year'))

# df_hist_sales_last10yrs = df_hist_sales.filter(pl.d)
# %% last 
df_metric = df_hist_sales_last10yrs.select(["year", "mode", "powertrain", "unit", "value"])
rprint(df_metric)
# %% vehicle units sold by mode
# mode 1: metric[powertrain]1 ...
# mode 2: metric[powertrain]1 ...
# mode ,,,: metric[powertrain]1 ...

powertrain_desc = {
    'BEV': 'Battery EV',
    'PHEV': 'Plug-in Hybrid EV',
    'EV': 'EV',
    'FCEV': 'Fuel Cell EV'
    }

df_metric = df_metric.with_columns(df_metric['powertrain'].map_elements(lambda x: powertrain_desc[x]).alias('pt_desc'))

def format_sum(val):
    
    if val < 1000:
        return f'{int(round(val))}'
    
    # K, M, G
    units = [1000, 1000000, 1000000000]
    labels = ['K', 'M', 'G']
    unit_dict = dict(zip(units, labels))
    fmt = ''
    for u in units:
        disp = val // u
        if (disp) < u:
            fmt = f'{int(round(disp))}{unit_dict[u]}'
            break
        
    return fmt

# material icons
modes_emoji = {
    'Trucks': 'local_shipping',
    'Cars': 'directions_car',
    'Buses': 'directions_bus',
    'Vans': 'airport_shuttle' 
}
#%%

year_min, year_max = df_hist_sales_last10yrs['year'].min(), df_hist_sales_last10yrs['year'].max()
st.title(f"EV Sales ({year_min} - {year_max})")
st.text(f'Total vehicles sold in 10 years, and percentage growth since {year_min}.')
# write out icons
div = st.container()
n_cols = df_metric['mode'].n_unique()
st_cols = div.columns(n_cols)
#%%
for idx, m in enumerate(df_metric['mode'].unique().sort()):
    
    # compute deltas (from year_min to year_max percentage)
    _df_delta = df_metric.filter(
        pl.col('mode')==m).filter(
            (pl.col('year')==year_min) | 
            (pl.col('year')==year_max)).group_by(
                ['year', 'powertrain', 'pt_desc']).sum().sort(by='year')
    
    with st_cols[idx]:
        
        st.subheader(f':material/{modes_emoji[m]}: {m}')
    
    # write out the metrics
    df_metric_mode = df_metric.filter(pl.col('mode') == m)
    rprint(df_metric_mode)
    
    _group = df_metric_mode.group_by(['powertrain', 'pt_desc']).sum().select(['powertrain', 'pt_desc', 'value'])
    for pt, pt_desc, total in _group.rows():
        with st_cols[idx]:
            delta_pct = _df_delta.filter(pl.col('powertrain')==pt).with_columns(((pl.col('value') - pl.col('value').shift(1))/(pl.col('value')) * 100).alias('delta_pct'))
            delta_pct = delta_pct.select('delta_pct').drop_nulls().get_column('delta_pct').to_numpy()
            # rprint(type(delta_pct), delta_pct)
            if (len(delta_pct)):
                st.metric(label=f'{pt_desc}', value=format_sum(total), delta=f'{delta_pct[0] :.2f}%')
            else:
                st.metric(label=f'{pt_desc}', value=format_sum(total), delta='No data')

# %% dataframe
st.text('--'*50)
st.header(f"Historical EV sales ({df_hist_sales['year'].min()} - {df_hist_sales['year'].max()})")
st.markdown("***Powertrain abbreviations:***\n" + "".join(f'- **{k}**: {v}\n' for k, v in powertrain_desc.items()))

df_frame = df_hist_sales.drop(['category', 'parameter', 'date', 'unit'])\
    .with_columns(pl.col('value').alias('Sold EVs'))\
    .drop('value')\
    .group_by(['mode', 'region', 'powertrain'])\
    .sum()\
    .drop('year')\
    .sort(by=pl.col('Sold EVs'), descending=True)\
    .with_columns(pl.col('Sold EVs').map_elements(format_sum).alias('Formatted'))\
    
st.dataframe(df_frame)

# %% plot
import plotly.express as px
st.text('--'*50)
st.header(f"Scatter plot for ({df_hist_sales['year'].min()} - {df_hist_sales['year'].max()}) EV sales around the world")
st.markdown("***Powertrain abbreviations:***\n" + "".join(f'- **{k}**: {v}\n' for k, v in powertrain_desc.items()))

fig_year = px.scatter(df_hist_sales, \
    x='year',
    y='value',
    color='powertrain',
    size='value',
    hover_data=['region', 'mode'],
    title=f'EV sales ({df_hist_sales['year'].min()} - {df_hist_sales['year'].max()}) across the world'
    )
st.plotly_chart(fig_year)

fig_year = px.scatter(df_hist_sales, \
    x='year',
    y='value',
    color='powertrain',
    facet_col='mode',
    title=f"EV sales by mode across the whole world"
    )
st.plotly_chart(fig_year)

# df_top_k = df_hist_sales.top_k(k=5, by=['powertrain', 'mode', 'value'])
df_significant = df_hist_sales\
    .group_by(['region', 'powertrain', 'mode'])\
    .sum().drop('year')\
    .sort(by='value', descending=True)

fig_reg = px.bar(df_significant, \
    y='region',
    x='value',
    orientation='h',
    hover_data=['powertrain', 'mode'],
    facet_col='powertrain',
    title=f"EV sales by region ({df_hist_sales['year'].min()} - {df_hist_sales['year'].max()})"
    )
st.plotly_chart(fig_reg)

# %%

st.markdown("""
#### Ref.
> IEA. *Global EV Sales: 2010–2024*. Kaggle, 2024.  
> [https://www.kaggle.com/dsv/8991634](https://www.kaggle.com/dsv/8991634)  
> DOI: [10.34740/KAGGLE/DSV/8991634](https://doi.org/10.34740/KAGGLE/DSV/8991634)
""")

st.markdown('''
            >__Made by: Nardos E.__
            >__Day 4 streamlit challenge, 2025.__
            ''')