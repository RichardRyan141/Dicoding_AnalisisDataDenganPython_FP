import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

def monthly_revenue_df(order_df, detail_df):
    revenue_df = pd.merge(order_df, detail_df, on='order_id')
    revenue_df['month_year'] = pd.to_datetime(revenue_df['order_purchase_timestamp']).dt.strftime('%B %Y')
    revenue_df = revenue_df.groupby(by='month_year').price.sum().reset_index()
    revenue_df['month_year'] = pd.to_datetime(revenue_df['month_year'], format="%B %Y")
    revenue_df = revenue_df.sort_values(by='month_year')
    revenue_df['month_year'] = pd.to_datetime(revenue_df['month_year']).dt.strftime('%B %Y')
    revenue_df = revenue_df.rename(columns = {
        'price': 'revenue'
    })
    return revenue_df

def product_order_count_df(order_df, detail_df, product_df):
    product_count_df = pd.merge(pd.merge(order_df, detail_df, on='order_id'), product_df, on='product_id')
    product_count_df = product_count_df.groupby(by='product_id').order_id.count().reset_index()
    product_count_df = product_count_df.rename(columns = {
        'order_id': 'order_count'
    })
    product_count_df = product_count_df.sort_values(by="order_count", ascending=False)
    return product_count_df

def total_spent_percity_df(order_df, customer_df, payment_df):
    city_spending_df = pd.merge(pd.merge(customer_df, order_df, on='customer_id'), payment_df, on='order_id')
    city_spending_df = city_spending_df.groupby(by='customer_city').payment_value.sum().reset_index()
    city_spending_df = city_spending_df.rename(columns = {
        'payment_value': 'amount_spent'
    })
    return city_spending_df

def revenue_bycategory_df(order_df, detail_df, product_df):
    category_revenue_df = pd.merge(pd.merge(order_df, detail_df, on='order_id'), product_df, on='product_id')
    category_revenue_df = category_revenue_df.groupby(by='product_category_name').price.sum().reset_index()
    category_revenue_df = category_revenue_df.rename(columns = {
        'price': 'revenue'
    })
    return category_revenue_df

def create_rfm_df(order_data, order_detail, customer_data):
    order_detail_kelompok = order_detail.groupby('order_id')['price'].sum()

    RFM_data = pd.merge(order_detail_kelompok, order_data, on='order_id')
    RFM_data = pd.merge(RFM_data, customer_data, on='customer_id')

    RFM_data['order_date'] = pd.to_datetime(RFM_data['order_purchase_timestamp']).dt.date

    df_recency = RFM_data.groupby(by='customer_unique_id', as_index=False)['order_date'].max()
    recent_order = df_recency['order_date'].max()
    df_recency['Recency'] = df_recency['order_date'].apply(lambda x: (recent_order - x).days)

    frequency_df = RFM_data.drop_duplicates().groupby(by=['customer_unique_id'], as_index=False)['order_date'].count()
    frequency_df.columns = ['customer_unique_id', 'Frequency']

    monetary_df = RFM_data.groupby(by='customer_unique_id', as_index=False)['price'].sum()
    monetary_df.columns = ['customer_unique_id', 'Monetary']

    rf_df = df_recency.merge(frequency_df, on='customer_unique_id')
    rfm_df = rf_df.merge(monetary_df, on='customer_unique_id').drop(columns='order_date')

    rfm_df['R_rank'] = rfm_df['Recency'].rank(ascending=False)
    rfm_df['F_rank'] = rfm_df['Frequency'].rank(ascending=True)
    rfm_df['M_rank'] = rfm_df['Monetary'].rank(ascending=True)

    rfm_df['R_rank_norm'] = (rfm_df['R_rank']/rfm_df['R_rank'].max())*100
    rfm_df['F_rank_norm'] = (rfm_df['F_rank']/rfm_df['F_rank'].max())*100
    rfm_df['M_rank_norm'] = (rfm_df['F_rank']/rfm_df['M_rank'].max())*100

    rfm_df.drop(columns=['R_rank', 'F_rank', 'M_rank'], inplace=True)

    rfm_df['RFM_Score'] = 0.15*rfm_df['R_rank_norm']+0.28*rfm_df['F_rank_norm']+0.57*rfm_df['M_rank_norm']

    return rfm_df

def translate_category(row):
    if pd.isna(row['product_category_name']):
        return "Unknown Category"
    elif pd.isna(row['product_category_name_english']):
        return row['product_category_name']
    else:
        return row['product_category_name_english']

order_df = pd.read_csv("data/orders_dataset.csv")
detail_df = pd.read_csv("data/order_items_dataset.csv")
customer_df = pd.read_csv("data/customers_dataset.csv")
product_df = pd.read_csv("data/products_dataset.csv")
translation_df = pd.read_csv("data/product_category_name_translation.csv")
payment_df = pd.read_csv("data/order_payments_dataset.csv")

order_df["order_purchase_timestamp"] = pd.to_datetime(pd.to_datetime(order_df['order_purchase_timestamp']).dt.strftime("%B %Y"), format="%B %Y")
product_df = pd.merge(product_df, translation_df, on='product_category_name', how='left')
product_df['product_category_name'] = product_df.apply(translate_category, axis=1)

min_date = order_df["order_purchase_timestamp"].min()
max_date = order_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("https://anyhub.com.br/wp-content/uploads/2023/10/logo_olist_d7309b5f20.png")
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

order_df = order_df[(order_df["order_purchase_timestamp"] >= str(start_date)) &  (order_df["order_purchase_timestamp"] <= str(end_date))]

monthly_revenue = monthly_revenue_df(order_df, detail_df)
product_order_count = product_order_count_df(order_df, detail_df, product_df)
total_spent_percity = total_spent_percity_df(order_df, customer_df, payment_df)
revenue_bycategory = revenue_bycategory_df(order_df, detail_df, product_df)
rfm_df = create_rfm_df(order_df, detail_df, customer_df)

st.header('OList Dashboard :sparkles:')
st.subheader('Summary')

col1, col2 = st.columns(2)

with col1:
    total_orders = order_df.order_id.count()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(monthly_revenue.revenue.sum(), "BRL", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

st.subheader('Monthly Revenue')

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_revenue["month_year"],
    monthly_revenue["revenue"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
plt.xticks(rotation=45)

st.pyplot(fig)

st.subheader('Product Performance')

fig, ax = plt.subplots(figsize=(12, 6))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_count", y="product_id", data=product_order_count.head(5), palette=colors)
ax.set_ylabel(None)
ax.set_xlabel("Number of Sales", fontsize=30)
ax.set_title("Best Performing Product", loc="center", fontsize=50)
ax.tick_params(axis='y', labelsize=35)
ax.tick_params(axis='x', labelsize=30)

st.pyplot(fig)

fig, ax = plt.subplots(figsize=(12, 6))

sns.barplot(x="order_count", y="product_id", data=product_order_count.tail(5), palette=colors)
ax.set_ylabel(None)
ax.set_xlabel("Number of Sales", fontsize=30)
ax.invert_xaxis()
ax.yaxis.set_label_position("right")
ax.yaxis.tick_right()
ax.set_title("Worst Performing Product", loc="center", fontsize=50)
ax.tick_params(axis='y', labelsize=35)
ax.tick_params(axis='x', labelsize=30)

st.pyplot(fig)

st.subheader('City Spending')

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", 
          "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(
    x="amount_spent", 
    y="customer_city",
    data=total_spent_percity.sort_values(by="amount_spent", ascending=False).head(10),
    palette=colors,
    ax=ax
)
ax.set_title("Spending per City", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader('Category Revenue')

fig, ax = plt.subplots(figsize=(20, 10))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", 
          "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", 
          "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(
    x="revenue", 
    y="product_category_name",
    data=revenue_bycategory.sort_values(by="revenue", ascending=False).head(15),
    palette=colors,
    ax=ax
)
ax.set_title("Revenue per Category", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.Recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.Frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.Monetary.mean(), "BRL", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="Recency", x="customer_unique_id", data=rfm_df.sort_values(by="Recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)
for tick in ax[0].get_xticklabels():
        tick.set_horizontalalignment('right')
        tick.set_rotation(45)

sns.barplot(y="Frequency", x="customer_unique_id", data=rfm_df.sort_values(by="Frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
for tick in ax[1].get_xticklabels():
        tick.set_horizontalalignment('right')
        tick.set_rotation(45)

sns.barplot(y="Monetary", x="customer_unique_id", data=rfm_df.sort_values(by="Monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
for tick in ax[2].get_xticklabels():
        tick.set_horizontalalignment('right')
        tick.set_rotation(45)

st.pyplot(fig)