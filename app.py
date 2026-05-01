import streamlit as st
from streamlit_theme import st_theme
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import yaml
import os

FINAL_DIR = 'Data/04_Final'
MY_CHART_COLORS = ["#0068c9", "#ef553b", "#438d56"]

theme = st_theme()
is_dark = theme.get("base") == "dark" if theme else False
shadow_color = "black" if is_dark else "white"

# Read Data with Cache
@st.cache_data
def get_data():
    thai_path = os.path.join(FINAL_DIR, 'thai_restaurants_analysis_20260419.csv')
    thai_restaurants = pd.read_csv(thai_path)

    return thai_restaurants

def load_lang():
    with open('lang.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

lang_data = load_lang()

if 'lang' not in st.session_state:
    st.session_state.lang = 'tc'

t = lang_data[st.session_state.lang]

st.set_page_config(
    page_title=t["page_title"],
    layout="wide",
    page_icon="🇹🇭"
)

st.html("""
    <style>
    .stMainBlockContainer {
        max-width: 1100px;
        margin: auto;
        padding-top: 2rem;
    }

    @media (max-width: 1100px) {
        .stMainBlockContainer {
            max-width: 100% !important;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }

    h1 {font-size: 2rem !important;}
    h2 {font-size: 1.5rem !important;}
    h3 {font-size: 1.2rem !important;}

    div[data-testid="stVerticalBlock"] hr {
        margin-top: 15px !important;
        margin-bottom: 15px !important;
    }
    
    [data-testid="stElementToolbar"] button[aria-label="Download as CSV"] {
        display: none !important;
    }
    
    </style>
    """)

def change_lang():
    if st.session_state.lang_choice == "中文":
        st.session_state.lang = 'tc'
    else:
        st.session_state.lang = 'en'

try:
    thai_restaurants = get_data()
except Exception as e:
    st.error(f"Unable to load data. Please check if the 'Data' folder contains the necessary files. Details:{e}")
    st.stop()

def display_chart(fig, height=300, is_map=False, legend=None, key=None):
    fig.update_layout(
        dragmode=False,
        yaxis=dict(fixedrange=True),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    if is_map:
        config = {'displayModeBar': True}
    else:
        config = {
            'scrollZoom': False,
            'displayModeBar': False
        }

    if legend:
        title, x, y = legend
        fig.update_layout(
            legend=dict(
                title={
                    'text': title,
                    'font': {'color': 'black'}
                },
                x=x,
                y=y,
                xanchor='right',
                yanchor='top',
                bgcolor="rgba(255, 255, 255, 0.7)",
                bordercolor="Black",
                borderwidth=1,
                font=dict(color="black")
            )
        )
    else:
        fig.update_layout(showlegend=False, height=height)

    st.plotly_chart(fig, config=config, width='stretch', key=key)

# =====================
# Streamlit UI Starts
# =====================

with st.container(horizontal=True, vertical_alignment="center"):
    st.space('stretch')
    st.selectbox(
        label=t["select_lang"],
        options=["中文", "English"],
        index=0 if st.session_state.lang == 'tc' else 1,
        key='lang_choice',
        on_change=change_lang,
        width=130
    )

st.title(t["title"])
st.markdown(t["intro"])

st.divider()

# ===========================
# BILINGUAL DISPLAY HANDLING
# ===========================

base_cols = ['restaurant_name', 'district_name', 'address', 'naming_style']
cols = {col: f"{col}_{st.session_state.lang}" for col in base_cols}

# =====================
# OVERVIEW
# =====================

naming_style_df = thai_restaurants[[cols['naming_style']]].value_counts().reset_index()

total_restaurants_count = naming_style_df['count'].sum()
pun_count = naming_style_df.query(f"{cols['naming_style']} in ['Pun', '食字']")['count'].iloc[0]
pun_percent = pun_count / total_restaurants_count * 100
denominator = total_restaurants_count / pun_count

st.header(t['overview_heading'])

overview_1, overview_2, overview_3 = st.tabs([t['overview_1'], t['overview_2'], t['overview_3']])

with overview_1:
    naming_style_df['total'] = naming_style_df['count'].sum()

    naming_style_df['percent'] = naming_style_df['count'] / naming_style_df['total']

    fig_naming_style_bar = px.bar(
        naming_style_df,
        y='total',
        x='count',
        color=cols['naming_style'],
        orientation='h',
        color_discrete_sequence=MY_CHART_COLORS,
        labels=t["labels"],
        custom_data=[cols['naming_style'], 'percent']
    )

    total_count = naming_style_df['count'].sum()

    fig_naming_style_bar.update_traces(
        texttemplate="%{customdata[0]}<br>%{x}<br>(%{customdata[1]:.1%})",
        textposition='inside',
        textfont_size=16,
        insidetextanchor='middle',
        hoverinfo='skip',
        hovertemplate=None
    )

    fig_naming_style_bar.update_layout(
        xaxis=dict(visible=False, range=[0, total_count]),
        yaxis=dict(visible=False),
    )

    display_chart(fig_naming_style_bar, height=120)

    st.markdown(t['overview_1_insight'].format(total_restaurants_count=total_restaurants_count,
                                             pun_count=pun_count,
                                             pun_percent=pun_percent,
                                             denominator=denominator))

with overview_2:

    thai_restaurants_district_group = thai_restaurants.groupby(cols['naming_style'])[[cols['naming_style'], cols['district_name']]] \
        .value_counts().reset_index().sort_values('count', ascending=False)

    fig_naming_style_bar = px.bar(thai_restaurants_district_group, x=cols['district_name'], y='count',
                                  color=cols['naming_style'], color_discrete_sequence=MY_CHART_COLORS,
                                  barmode='group', custom_data=[cols['naming_style']],
                                  labels=t["labels"],
                                  )

    fig_naming_style_bar.update_traces(
        hovertemplate=f'%{{x}} | %{{customdata[0]}}<br>{t["labels"]["count"]}{t["labels"]["colon"]}%{{y}}<extra></extra>',
    )

    display_chart(fig_naming_style_bar, legend=(t['labels'][cols['naming_style']], 0.99, 0.98))

    st.markdown(t['overview_2_insight'].format(total_restaurants_count=total_restaurants_count,
                                               pun_count=pun_count,
                                               pun_percent=pun_percent,
                                               denominator=denominator))

with overview_3:
    fig_naming_style_map = px.scatter_map(thai_restaurants, lat='latitude', lon='longitude',
                                          color=cols['naming_style'], color_discrete_sequence=MY_CHART_COLORS,
                                          custom_data=['restaurant_name_tc', cols['district_name'], cols['address']],
                                          center=dict(lat=22.35, lon=114.1), zoom=10.2,
                                          )

    fig_naming_style_map.update_traces(
        hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["address"]}{t["labels"]["colon"]}%{{customdata[2]}}<extra></extra>',
        marker=dict(size=10, opacity=.8)
    )

    fig_naming_style_map.update_layout(mapbox_style="carto-positron", height=350)

    display_chart(fig_naming_style_map, is_map=True, legend=(t['labels'][cols['naming_style']], 0.99, 0.9))

with st.expander(t["show_all"].format(total_restaurants_count=total_restaurants_count)):
    st.dataframe(
        thai_restaurants[['restaurant_name_tc', 'restaurant_name_en', cols['district_name'], cols['address'], cols['naming_style']]].rename(columns=t["labels"])
    )

with st.expander(t["data_methodology"]):
    st.markdown(t["overview_remark"])

# ============================
# ANALYSIS WITH GOOGLE METRICS
# ============================

st.divider()
st.header(t["google_heading"])
st.markdown(t["google_insight"])

google_1, google_2 = st.columns(2)

with google_1:
    st.subheader(t["google_1"])
    fig_rating_box = px.box(
        thai_restaurants,
        x=cols['naming_style'],
        y='rating',
        range_y=[1.9, 5.1],
        points='all',
        color=cols['naming_style'],
        color_discrete_sequence=MY_CHART_COLORS,
        labels=t["labels"],
        custom_data=['restaurant_name_tc', cols['district_name']],
    )

    fig_rating_box.update_traces(
        hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["rating"]}{t["labels"]["colon"]}%{{y}}<extra></extra>',
    )

    display_chart(fig_rating_box)

with google_2:
    st.subheader(t["google_2"])
    fig_review_box = px.box(
        thai_restaurants,
        x=cols['naming_style'],
        y='review_count',
        range_y=[-50, 1350],
        points='all',
        color=cols['naming_style'],
        color_discrete_sequence=MY_CHART_COLORS,
        labels=t["labels"],
        custom_data=['restaurant_name_tc', cols['district_name']]
    )

    fig_review_box.update_traces(
        hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["review_count"]}{t["labels"]["colon"]}%{{y}}<extra></extra>',
    )

    display_chart(fig_review_box)

with st.expander(t["show_all"].format(total_restaurants_count=total_restaurants_count)):
    st.dataframe(
        thai_restaurants[['restaurant_name_tc', 'restaurant_name_en', cols['district_name'], cols['naming_style'], 'rating', 'review_count']].rename(columns=t["labels"])
    )

with st.expander(t["data_methodology"]):
    st.markdown(t["google_remark"].format(total_restaurants_count=total_restaurants_count))

# ============================
# PRICE LEVEL CORRELATION
# ============================

st.divider()
st.header(t["price_level_heading"])
st.markdown(t["price_level_insight"].format(total_restaurants_count=total_restaurants_count))

price_level_1, price_level_2 = st.columns([1,2])

with price_level_1:
    st.subheader(t["price_level_1"])
    thai_restaurants['is_pun'] = thai_restaurants['naming_style_en'] == 'Pun'
    thai_corr = thai_restaurants.drop(columns=['district_code', 'license_id', 'latitude', 'longitude']).corr(
        numeric_only=True)
    new_order = ['rating', 'review_count', 'price_level', 'is_pun']
    thai_corr_rename = thai_corr.reindex(columns=new_order, index=new_order).rename(columns=t['labels'], index=t['labels'])

    fig_heatmap = px.imshow(thai_corr_rename, text_auto='.4f',
                            color_continuous_scale='rdbu', color_continuous_midpoint=0,
                            labels=t['labels']
                            )

    fig_heatmap.update_traces(hoverinfo='skip', hovertemplate=None)
    fig_heatmap.update_layout(
        coloraxis_colorbar=dict(
            orientation='h',
            yanchor='top',
            y=-0.1,
            x=0.5,
            xanchor='center',
            xref="paper",
            title_side='top',
            thickness=20,
            len=1.18
        )
    )

    display_chart(fig_heatmap)

with price_level_2:
    st.subheader(t["price_level_2"])
    price_level_2_1, price_level_2_2 = st.tabs([t["price_level_2_1"], t["price_level_2_2"]])

    with price_level_2_1:
        thai_restaurants_price_level_group = thai_restaurants.groupby('price_level')[[cols['naming_style'], 'price_level']] \
            .value_counts().reset_index().sort_values(['price_level', 'count'], ascending=[True, False])

        thai_restaurants_price_level_group['price_level'] = thai_restaurants_price_level_group['price_level'].astype(
            int).astype(str)

        fig_price_level_bar = px.bar(thai_restaurants_price_level_group, x=cols['naming_style'], y='count',
                                     color='price_level', color_discrete_sequence=px.colors.qualitative.Prism,
                                     barmode='group', custom_data=['price_level'],
                                     labels=t["labels"]
                                     )

        fig_price_level_bar.update_traces(
            hovertemplate=f'<b>%{{x}} | {t["labels"]["price_level"]}{t["labels"]["colon"]}%{{customdata[0]}}</b><br>{t["labels"]["count"]}{t["labels"]["colon"]}%{{y}}<extra></extra>',
        )

        display_chart(fig_price_level_bar, legend=(t["labels"]["price_level"], 0.99, 0.98))

    with price_level_2_2:
        thai_restaurants_price_level_district = thai_restaurants.groupby(['price_level', cols['district_name']])[
            ['price_level']] \
            .value_counts().reset_index().sort_values(['price_level', 'count'], ascending=[True, False])

        thai_restaurants_price_level_district['price_level'] = thai_restaurants_price_level_district[
            'price_level'].astype(int).astype(str)  # Convert to string to make barmode=group work

        fig_price_level_district_bar = px.bar(thai_restaurants_price_level_district, x=cols['district_name'], y='count',
                                              color='price_level',
                                              color_discrete_sequence=px.colors.qualitative.Prism,
                                              labels=t["labels"],
                                              barmode='group',
                                              custom_data=['price_level'],
                                              )

        fig_price_level_district_bar.update_traces(
            hovertemplate=f'<b>%{{x}} | {t["labels"]["price_level"]}{t["labels"]["colon"]}%{{customdata[0]}}</b><br>{t["labels"]["count"]}{t["labels"]["colon"]}%{{y}}<extra></extra>',
        )

        display_chart(fig_price_level_district_bar, legend=(t["labels"]["price_level"], 0.99, 0.98))

with st.expander(t["show_all"].format(total_restaurants_count=total_restaurants_count)):
    st.dataframe(
        thai_restaurants[['restaurant_name_tc', 'restaurant_name_en', cols['district_name'], cols['naming_style'], 'is_pun', 'rating', 'review_count', 'price_level']].rename(columns=t["labels"])
    )

with st.expander(t["data_methodology"]):
    st.markdown(t["price_remark"].format(total_restaurants_count=total_restaurants_count))

# ============================
# ANALYSIS ACROSS PRICE LEVELS
# ============================

st.divider()
st.header(t["price_level_breakdown_heading"])
st.markdown(t["price_level_breakdown_insight"])

thai_price_0 = thai_restaurants[thai_restaurants.price_level == 0]
thai_price_3 = thai_restaurants[thai_restaurants.price_level == 3]

price_breakdown_1, price_breakdown_2 = st.tabs([t["price_breakdown_1"],t["price_breakdown_2"]])

with price_breakdown_1:
    price_breakdown_1_1, price_breakdown_1_2, price_breakdown_1_3 = st.columns(3)

    with price_breakdown_1_1:
        st.subheader(t['price_breakdown_1_1'])
        display_chart(fig_rating_box, key="rating_box_overall_repeat")

    with price_breakdown_1_2:
        st.subheader(t['price_breakdown_1_2'])

        fig_price_0_rating = px.box(
            thai_price_0,
            x=cols['naming_style'],
            y='rating',
            range_y=[1.9, 5.1],
            points='all',
            color=cols['naming_style'],
            color_discrete_sequence=MY_CHART_COLORS,
            labels=t['labels'],
            custom_data=['restaurant_name_tc', cols['district_name']]
        )

        fig_price_0_rating.update_traces(
            hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["rating"]}{t["labels"]["colon"]}%{{y}}<extra></extra>'
        )

        display_chart(fig_price_0_rating)

    with price_breakdown_1_3:
        st.subheader(t['price_breakdown_1_3'])

        fig_price_3_rating = px.box(
            thai_price_3,
            x=cols['naming_style'],
            y='rating',
            range_y=[1.9, 5.1],
            points='all',
            color=cols['naming_style'],
            color_discrete_sequence=MY_CHART_COLORS,
            labels=t['labels'],
            custom_data=['restaurant_name_tc', cols['district_name']]
        )

        fig_price_3_rating.update_traces(
            hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["rating"]}{t["labels"]["colon"]}%{{y}}<extra></extra>'
        )

        display_chart(fig_price_3_rating)

with price_breakdown_2:
    price_breakdown_2_1, price_breakdown_2_2, price_breakdown_2_3 = st.columns(3)

    with price_breakdown_2_1:
        st.subheader(t["price_breakdown_2_1"])
        display_chart(fig_review_box, key="review_box_overall_repeat")

    with price_breakdown_2_2:
        st.subheader(t["price_breakdown_2_2"])
        fig_price_0_review = px.box(
            thai_price_0,
            x=cols['naming_style'],
            y='review_count',
            range_y=[-50, 1350],
            points='all',
            color=cols['naming_style'],
            color_discrete_sequence=MY_CHART_COLORS,
            labels=t['labels'],
            custom_data=['restaurant_name_tc', cols['district_name']]
        )

        fig_price_0_review.update_traces(
            hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["review_count"]}{t["labels"]["colon"]}%{{y}}<extra></extra>'
        )

        display_chart(fig_price_0_review)

    with price_breakdown_2_3:
        st.subheader(t["price_breakdown_2_3"])
        fig_price_3_review = px.box(
            thai_price_3,
            x=cols['naming_style'],
            y='review_count',
            range_y=[-50, 1350],
            points='all',
            color=cols['naming_style'],
            color_discrete_sequence=MY_CHART_COLORS,
            labels=t['labels'],
            custom_data=['restaurant_name_tc', cols['district_name']]
        )

        fig_price_3_review.update_traces(
            hovertemplate=f'<b>%{{customdata[0]}} | %{{customdata[1]}}</b><br>{t["labels"]["review_count"]}{t["labels"]["colon"]}%{{y}}<extra></extra>'
        )

        display_chart(fig_price_3_review)

# ============================
# ANALYSIS ACROSS DISTRICTS
# ============================
st.divider()
st.header(t["price_corr_heading"])
st.markdown(t["price_corr_insight"])

price_corr_1, price_corr_2 = st.columns(2)

with price_corr_1:
    st.subheader(t["price_corr_1"])

    thai_0_review = thai_price_0.groupby(cols['district_name']).agg(
        total_restaurants_count=(cols['naming_style'], 'count'),
        pun_restaurants_count=(cols['naming_style'], lambda x: (x.isin(['Pun', '食字'])).sum()),
        avg_pun_reviews=('review_count', lambda x: thai_price_0.loc[x.index].query(f"{cols['naming_style']} in ['Pun', '食字']")['review_count'].median()),
        avg_all_reviews=('review_count', 'median')
    ).reset_index()

    thai_0_review['pun_ratio'] = (thai_0_review['pun_restaurants_count'] / thai_0_review['total_restaurants_count']) * 100

    thai_0_review = thai_0_review.dropna(subset=['avg_pun_reviews'])

    fig_thai_0_review = px.scatter(
        thai_0_review,
        x='pun_ratio',
        y='avg_pun_reviews',
        text=cols['district_name'],
        size='pun_restaurants_count',
        size_max=20,
        color=pd.Series([t['labels']['pun_restaurants_district']] * len(thai_0_review)),
        color_discrete_sequence=[px.colors.qualitative.Prism[0]],
        labels=t["labels"],
        custom_data=['pun_restaurants_count', 'total_restaurants_count'],
    )

    X_0_rev = thai_0_review['pun_ratio']
    Y_0_rev = thai_0_review['avg_pun_reviews']
    X_const_0_rev = sm.add_constant(X_0_rev)

    # RLM: Best for handling outliers
    rlm_model_0_rev = sm.RLM(Y_0_rev, X_const_0_rev).fit()

    X_plot_0_rev = np.linspace(X_0_rev.min(), X_0_rev.max(), 100)
    X_plot_const_0_rev = sm.add_constant(X_plot_0_rev)
    Y_rlm_pred_0_rev = rlm_model_0_rev.predict(X_plot_const_0_rev)

    fig_thai_0_review.add_trace(
        go.Scatter(
            x=X_plot_0_rev,
            y=Y_rlm_pred_0_rev,
            mode='lines',
            name=t['labels']['pun_restaurants_trendline'],
            line=dict(color=px.colors.qualitative.Prism[0], dash='dash'),
            hovertemplate="%{fullData.name}<extra></extra>",
        )
    )

    # Control Group of All Restaurants

    Y_all_rev = thai_0_review['avg_all_reviews']

    rlm_model_all_rev = sm.RLM(Y_all_rev, X_const_0_rev).fit()

    Y_rlm_pred_all_rev = rlm_model_all_rev.predict(X_plot_const_0_rev)

    fig_thai_0_review.add_trace(
        go.Scatter(
            x=X_plot_0_rev,
            y=Y_rlm_pred_all_rev,
            mode='lines',
            name=t['labels']['all_restaurants_trendline'],
            line=dict(color='gray', dash='dash'),
            hovertemplate="%{fullData.name}<extra></extra>",
        )
    )

    fig_thai_0_review.update_traces(
        marker=dict(
            opacity=0.8,
            line=dict(width=1, color=shadow_color)
        ),
        textposition='top center',
        textfont=dict(
            shadow = f"0px 0px 2px {shadow_color}, 0px 0px 2px {shadow_color}, 0px 0px 2px {shadow_color}"
        ),
        hovertemplate=f"{t['labels']['avg_pun_reviews']}{t['labels']['colon']}%{{y}}<br>"
                      f"{t['labels']['pun_restaurants_count']}{t['labels']['colon']}%{{customdata[0]}}<br>"
                      f"{t['labels']['total_restaurants_count']}{t['labels']['colon']}%{{customdata[1]}}<br>"
                      f"{t['labels']['pun_ratio']}{t['labels']['colon']}%{{x:.2f}}%<extra></extra>",
        selector=dict(mode='markers+text'), legendrank=1  # Select the dots and move them back to first item of legend
    )

    fig_thai_0_review.data = fig_thai_0_review.data[1:] + fig_thai_0_review.data[:1]  # Reorder the scatter dots to the foremost layer

    display_chart(fig_thai_0_review, legend=(None, 0.98, 0.88))

    st.html(f"""<div style='text-align: center;'>
    <b><u>{t['labels']['regression_results']}</u></b>
    <p style='color:{px.colors.qualitative.Prism[0]};'><b>--- {t['labels']['price_level_0']} ---</b><br>
    {t['labels']['equation']}{t['labels']['colon']}Y = {rlm_model_0_rev.params['pun_ratio']:.3f}X + {rlm_model_0_rev.params['const']:.3f}<br>
    {t['labels']['z_stat']}{t['labels']['colon']}{rlm_model_0_rev.tvalues['pun_ratio']:.3f}<br>
    {t['labels']['p_value']}{t['labels']['colon']}{rlm_model_0_rev.pvalues['pun_ratio']:.3f} {t['labels']['significant']}</p>
    <p style='color:gray;'><b>--- {t['labels']['benchmark']} ---</b><br>
    {t['labels']['equation']}{t['labels']['colon']}Y = {rlm_model_all_rev.params['pun_ratio']:.3f}X + {rlm_model_all_rev.params['const']:.3f}<br>
    {t['labels']['z_stat']}{t['labels']['colon']}{rlm_model_all_rev.tvalues['pun_ratio']:.3f}<br>
    {t['labels']['p_value']}{t['labels']['colon']}{rlm_model_all_rev.pvalues['pun_ratio']:.3f} {t['labels']['significant']}</p></div>
    """)

with price_corr_2:
    st.subheader(t["price_corr_2"])

    thai_3_review = thai_price_3.groupby(cols['district_name']).agg(
        total_restaurants_count=(cols['naming_style'], 'count'),
        pun_restaurants_count=(cols['naming_style'], lambda x: (x.isin(['Pun', '食字'])).sum()),
        avg_pun_reviews=('review_count', lambda x: thai_price_3.loc[x.index].query(f"{cols['naming_style']} in ['Pun', '食字']")['review_count'].median()),
        avg_all_reviews=('review_count', 'median')
    ).reset_index()

    thai_3_review['pun_ratio'] = (thai_3_review['pun_restaurants_count'] / thai_3_review['total_restaurants_count']) * 100

    thai_3_review = thai_3_review.dropna(subset=['avg_pun_reviews'])

    fig_thai_3_review = px.scatter(
        thai_3_review,
        x='pun_ratio',
        y='avg_pun_reviews',
        text=cols['district_name'],
        size='pun_restaurants_count',
        size_max=20,
        color=pd.Series([t['labels']['pun_restaurants_district']] * len(thai_3_review)),
        color_discrete_sequence=[px.colors.qualitative.Prism[2]],
        labels=t["labels"],
        custom_data=['pun_restaurants_count', 'total_restaurants_count'],
    )

    X_3_rev = thai_3_review['pun_ratio']
    Y_3_rev = thai_3_review['avg_pun_reviews']
    X_const_3_rev = sm.add_constant(X_3_rev)

    # RLM: Best for handling outliers
    rlm_model_3_rev = sm.RLM(Y_3_rev, X_const_3_rev).fit()

    X_plot_3_rev = np.linspace(X_3_rev.min(), X_3_rev.max(), 100)
    X_plot_const_3_rev = sm.add_constant(X_plot_3_rev)
    Y_rlm_pred_3_rev = rlm_model_3_rev.predict(X_plot_const_3_rev)

    fig_thai_3_review.add_trace(
        go.Scatter(
            x=X_plot_3_rev,
            y=Y_rlm_pred_3_rev,
            mode='lines',
            name=t['labels']['pun_restaurants_trendline'],
            line=dict(color=px.colors.qualitative.Prism[2], dash='dash'),
            hovertemplate="%{fullData.name}<extra></extra>",
        )
    )

    # Control Group of All Restaurants

    Y_all_rev = thai_3_review['avg_all_reviews']

    rlm_model_all_rev = sm.RLM(Y_all_rev, X_const_3_rev).fit()

    Y_rlm_pred_all_rev = rlm_model_all_rev.predict(X_plot_const_0_rev)

    fig_thai_3_review.add_trace(
        go.Scatter(
            x=X_plot_3_rev,
            y=Y_rlm_pred_all_rev,
            mode='lines',
            name=t['labels']['all_restaurants_trendline'],
            line=dict(color='gray', dash='dash'),
            hovertemplate="%{fullData.name}<extra></extra>",
        )
    )

    fig_thai_3_review.update_traces(
        marker=dict(
            opacity=0.8,
            line=dict(width=1, color=shadow_color)
        ),
        textposition='top center',
        textfont=dict(
            shadow=f"0px 0px 2px {shadow_color}, 0px 0px 2px {shadow_color}, 0px 0px 2px {shadow_color}"
        ),
        hovertemplate=f"{t['labels']['avg_pun_reviews']}{t['labels']['colon']}%{{y}}<br>"
                      f"{t['labels']['pun_restaurants_count']}{t['labels']['colon']}%{{customdata[0]}}<br>"
                      f"{t['labels']['total_restaurants_count']}{t['labels']['colon']}%{{customdata[1]}}<br>"
                      f"{t['labels']['pun_ratio']}{t['labels']['colon']}%{{x:.2f}}%<extra></extra>",
        selector=dict(mode='markers+text'), legendrank=1  # Select the dots and move them back to first item of legend
    )

    fig_thai_3_review.data = fig_thai_3_review.data[1:] + fig_thai_3_review.data[:1]  # Reorder the scatter dots to the foremost layer
    display_chart(fig_thai_3_review, legend=(None, 0.98, 0.3))

    st.html(f"""
    <div style='text-align: center;'><b><u>{t['labels']['regression_results']}</u></b>
    <p style='color:{px.colors.qualitative.Prism[2]};'><b>--- {t['labels']['price_level_3']} ---</b><br>
    {t['labels']['equation']}{t['labels']['colon']}Y = {rlm_model_3_rev.params['pun_ratio']:.3f}X + {rlm_model_3_rev.params['const']:.3f}<br>
    {t['labels']['z_stat']}{t['labels']['colon']}{rlm_model_3_rev.tvalues['pun_ratio']:.3f}<br>
    {t['labels']['p_value']}{t['labels']['colon']}{rlm_model_3_rev.pvalues['pun_ratio']:.3f} {t['labels']['significant']}</p>
    <p style='color:gray;'><b>--- {t['labels']['benchmark']} ---</b><br>
    {t['labels']['equation']}{t['labels']['colon']}Y = {rlm_model_all_rev.params['pun_ratio']:.3f}X + {rlm_model_all_rev.params['const']:.3f}<br>
    {t['labels']['z_stat']}{t['labels']['colon']}{rlm_model_all_rev.tvalues['pun_ratio']:.3f}<br>
    {t['labels']['p_value']}{t['labels']['colon']}{rlm_model_all_rev.pvalues['pun_ratio']:.3f} {t['labels']['insignificant']}</p></div>
    """)

with st.expander(t["show_price_stratification"]):
    price_strat_1, price_strat_2 = st.tabs([t['price_strat_1'], t['price_strat_2']])

    with price_strat_1:
        st.dataframe(thai_0_review[[cols['district_name'], 'pun_restaurants_count', 'total_restaurants_count', 'pun_ratio', 'avg_pun_reviews', 'avg_all_reviews']].rename(columns=t["labels"]))

    with price_strat_2:
        st.dataframe(thai_3_review[[cols['district_name'], 'pun_restaurants_count', 'total_restaurants_count', 'pun_ratio', 'avg_pun_reviews', 'avg_all_reviews']].rename(columns=t["labels"]))

with st.expander(t["data_methodology"]):
    st.markdown(t["price_corr_remark"])

    price_corr_remark_1, price_corr_remark_2 = st.tabs([t['price_strat_1'], t['price_strat_2']])

    with price_corr_remark_1:

        # Level 0 Residual Analysis

        resid_thai_0_rev = thai_0_review.copy()
        resid_thai_0_rev['fitted'] = rlm_model_0_rev.fittedvalues
        resid_thai_0_rev['resid'] = rlm_model_0_rev.resid

        fig_resid_thai_0_rev = go.Figure()

        fig_resid_thai_0_rev.add_trace(
            go.Scatter(
                x=resid_thai_0_rev['fitted'],
                y=resid_thai_0_rev['resid'],
                mode='markers+text',
                text=resid_thai_0_rev[cols['district_name']],
                textposition="top center",
                marker=dict(size=resid_thai_0_rev['total_restaurants_count'], sizemode='area',
                            sizeref=2. * max(resid_thai_0_rev['total_restaurants_count']) / (30 ** 2),
                            color=px.colors.qualitative.Prism[0], opacity=0.8),
                customdata=np.stack((
                    resid_thai_0_rev['avg_pun_reviews'],
                    rlm_model_0_rev.weights
                ), axis=-1),
                hovertemplate=(
                    f"{t['labels']['actual_value']}{t['labels']['colon']}%{{customdata[0]}}<br>" +
                    f"{t['labels']['predicted_value']}{t['labels']['colon']}%{{x:.3f}}<br>" +
                    f"{t['labels']['residuals']}{t['labels']['colon']}%{{y:.3f}}<br>" +
                    f"{t['labels']['weight']}{t['labels']['colon']}%{{customdata[1]:.3f}}<extra></extra>"
                )
            )
        )

        fig_resid_thai_0_rev.add_shape(
            type="line",
            x0=resid_thai_0_rev['fitted'].min(), y0=0,
            x1=resid_thai_0_rev['fitted'].max(), y1=0,
            line=dict(color="red", width=2, dash="dash"),
        )

        fig_resid_thai_0_rev.update_layout(
            xaxis_title=t['labels']['predicted_value_xaxis'],
            yaxis_title=t['labels']['residuals_yaxis'],
            height=500
        )

        display_chart(fig_resid_thai_0_rev)

    with price_corr_remark_2:

        # Level 3 Residual Analysis

        resid_thai_3_rev = thai_3_review.copy()
        resid_thai_3_rev['fitted'] = rlm_model_3_rev.fittedvalues
        resid_thai_3_rev['resid'] = rlm_model_3_rev.resid

        fig_resid_thai_3_rev = go.Figure()

        fig_resid_thai_3_rev.add_trace(
            go.Scatter(
                x=resid_thai_3_rev['fitted'],
                y=resid_thai_3_rev['resid'],
                mode='markers+text',
                text=resid_thai_3_rev[cols['district_name']],
                textposition="top center",
                marker=dict(size=resid_thai_3_rev['total_restaurants_count'], sizemode='area',
                            sizeref=2. * max(resid_thai_3_rev['total_restaurants_count']) / (30 ** 2),
                            color=px.colors.qualitative.Prism[2],
                            opacity=0.8),
                customdata=np.stack((
                    resid_thai_3_rev['avg_pun_reviews'],
                    rlm_model_3_rev.weights
                ), axis=-1),
                hovertemplate=(
                    f"{t['labels']['actual_value']}{t['labels']['colon']}%{{customdata[0]}}<br>" +
                    f"{t['labels']['predicted_value']}{t['labels']['colon']}%{{x:.3f}}<br>" +
                    f"{t['labels']['residuals']}{t['labels']['colon']}%{{y:.3f}}<br>" +
                    f"{t['labels']['weight']}{t['labels']['colon']}%{{customdata[1]:.3f}}<extra></extra>"
                )
            )
        )

        fig_resid_thai_3_rev.add_shape(
            type="line",
            x0=resid_thai_3_rev['fitted'].min(), y0=0,
            x1=resid_thai_3_rev['fitted'].max(), y1=0,
            line=dict(color="red", width=2, dash="dash"),
        )

        fig_resid_thai_3_rev.update_layout(
            xaxis_title=t['labels']['predicted_value_xaxis'],
            yaxis_title=t['labels']['residuals_yaxis'],
            height=500
        )

        display_chart(fig_resid_thai_3_rev)

st.divider()

st.success(t['conclusion'])

st.warning(t['reflection'].format(total_restaurants_count=total_restaurants_count))

st.divider()

st.caption(f"Developed by Amy Lui | {t['page_title']}")