import pandas as pd
import plotly.express as px
import streamlit as st

# 1) Enable true wide‑page layout
st.set_page_config(
    page_title="Taller 3 — Modelos BI",
    layout="wide",
)

# 2) (Optional) Hide the hamburger menu & Streamlit footer
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data():

    countries_en = pd.read_excel("Countries.xlsx")
    
    countries_es = (
        pd.read_excel("Paises.xlsx").rename(columns={"Codigo Pais": "Country Code",
                                                     "Pais": "Country_ES",
                                                     "Continente": "Continent_ES",
                                                     }).loc[:, ["Country Code", "Country_ES"]])
    
    # Combine English + Spanish names
    countries = countries_en.merge(countries_es, on="Country Code", how="left")
    
    # 3) Load the three indicators
    pop = pd.read_excel("Population.xlsx")           # cols: Country, Population
    infant = pd.read_excel("Infant_death_rate.xlsx") # cols: Country, Infant mortality
    life = pd.read_excel("Life_expectancy.xlsx")     # cols: Country, Life Expectancy
    
    # 4) Merge everything on the English Country name
    df = countries.merge(pop,   on="Country", how="left").merge(infant, on="Country", how="left").merge(life,  on="Country", how="left")

    # Map English→Spanish continent names
    cont_es_map = {
        "Africa":  "África",
        "America": "América",
        "Asia":    "Asia",
        "Europe":  "Europa",
        "Oceania": "Oceanía",
    }
    df["Continente"] = df["Continent"].map(cont_es_map)
    
    # 5) Optional: drop rows with missing key data
    # df = df.dropna(subset=["Population", "Infant mortality", "Life Expectancy"])
    
    return df

def page_population(df):
    # — ROW 1: Título/Subtítulo + Filtros —
    row1c1, row1c2, row1c3 = st.columns(3)

    with row1c1:
        st.header("POBLACIÓN POR ÁREA")
        st.subheader("ANÁLISIS DE POBLACIÓN POR CONTINENTE Y PAÍS")

    # Continente filter (unchanged)…
    with row1c2:
        st.markdown("**Continente**")
        cont_map = {
            "Todos": None, "África": "Africa", "América": "America",
            "Asia": "Asia", "Europa": "Europe", "Oceanía": "Oceania",
        }
        if "sel_cont" not in st.session_state:
            st.session_state.sel_cont = None
        lc, rc = st.columns(2)
        for lbl in ["Todos","África","América"]:
            if lc.button(lbl, key="cont_l_"+lbl):
                st.session_state.sel_cont = cont_map[lbl]
        for lbl in ["Asia","Europa","Oceanía"]:
            if rc.button(lbl, key="cont_r_"+lbl):
                st.session_state.sel_cont = cont_map[lbl]

    # Cantidad Población filter (unchanged)…
    with row1c3:
        st.markdown("**Cantidad Población**")
        max_pop = df["Population"].max()
        pop_map = {
            "Todos": (0, max_pop),
            "0 - 1 M": (0, 1_000_000),
            "1 M - 10 M": (1_000_000, 10_000_000),
            "10 M - 100 M": (10_000_000, 100_000_000),
            "100 M +": (100_000_000, max_pop),
        }
        if "sel_range" not in st.session_state:
            st.session_state.sel_range = "Todos"
        lc, rc = st.columns(2)
        for lbl in ["Todos","0 - 1 M","1 M - 10 M"]:
            if lc.button(lbl, key="pop_l_"+lbl):
                st.session_state.sel_range = lbl
        for lbl in ["10 M - 100 M","100 M +",""]:
            if lbl and rc.button(lbl, key="pop_r_"+lbl):
                st.session_state.sel_range = lbl

    st.markdown("---")

    # — FILTRAR DF —
    df_f = df.copy()
    if st.session_state.sel_cont:
        df_f = df_f[df_f["Continent"] == st.session_state.sel_cont]
    lo, hi = pop_map[st.session_state.sel_range]
    df_f = df_f[df_f["Population"].between(lo, hi)]
    df_f["% mundial"] = df_f["Population"] / df["Population"].sum() * 100

        # — ROW 2: Treemap (left) + Map (right) —

    left, right = st.columns([3,4])
    tm_h, map_h = 300, 300

    # 1) Prepare a Spanish‐column copy for both viz
    tmp = (
        df_f.rename(columns={
            "Country_ES":    "Pais",
            "Population":    "Poblacion",
            "% mundial":     "Porcentaje mundial",
            "Country Code":  "Codigo Pais",
            "Continente":    "Continente"
        })
    )

    # — Treemap —
    with left:
        st.subheader("Población por País")
        tm = px.treemap(
            tmp,
            path=["Pais"],
            values="Poblacion",
            color="Pais",  # mixed colors by country
            hover_data=["Poblacion", "Porcentaje mundial"],
            height=tm_h,
            color_discrete_sequence=px.colors.qualitative.Alphabet,
        )
        # override hovertemplate: only label, Poblacion, % mundial
        tm.data[0].hovertemplate = (
            "<b>%{label}</b><br>"
            "Población: %{value:,}<br>"
            "Porcentaje mundial: %{customdata[1]:.2f}%"
            "<extra></extra>"
        )
        tm.update_layout(margin={"t":5,"l":0,"r":0,"b":0})
        st.plotly_chart(tm, use_container_width=True, height=tm_h, config={"displayModeBar":False})

    # — Geo‑scatter map —
    with right:
        st.subheader("Mapa de Población Mundial")
        fig = px.scatter_geo(
            tmp,
            locations="Codigo Pais",
            color="Continente",
            size="Poblacion",
            hover_name="Pais",
            hover_data=["Poblacion","Codigo Pais"],
            projection="equirectangular",
            height=map_h,
        )
        fig.update_geos(
            showland=True,    landcolor="white",
            showocean=True,   oceancolor="#d3d3d3",
            showcountries=True, countrycolor="white",
            showcoastlines=True, coastlinecolor="lightgray",
            showframe=False,
        )
        fig.update_layout(
            margin={"t":5,"l":0,"r":0,"b":0},
            template="plotly_white",
            legend_title_text="Continente",
        )
        st.plotly_chart(fig, use_container_width=True, height=map_h, config={"displayModeBar":False})

    st.markdown("---")

    # — ROW 3: Tabla full‑width —
    st.subheader("Detalle en Tabla")
    tbl = (
        df_f[["Continent","Country_ES","Population","% mundial"]]
        .rename(columns={
            "Continent":  "Continente",
            "Country_ES": "Pais",
            "Population": "Poblacion",
        })
        .sort_values(["Continente","Poblacion"], ascending=[True,False])
        .reset_index(drop=True)
    )
    st.dataframe(tbl, use_container_width=True, height=400)

def page_indicators(df):
    # — ROW 1: Main title —
    st.markdown(
        "### INDICADORES MUNDIALES: ANÁLISIS DE MORTALIDAD INFANTIL Y ESPERANZA DE VIDA POR REGIONES",
        unsafe_allow_html=True,
    )

    # — define your lookup maps up front —
    cont_map = {
        "África":  "Africa",
        "América": "Americas",
        "Asia":    "Asia",
        "Europa":  "Europe",
        "Oceanía": "Oceania",
    }
    pop_map = {
        "0 - 1 M":     (0,        1_000_000),
        "1 - 10 M":    (1_000_000,10_000_000),
        "10 - 100 M":  (10_000_000,100_000_000),
        "100 M +":     (100_000_000, df["Population"].max()),
    }
    mort_map = {
        "0 a 10":   (0, 10),
        "10 - 25":  (10,25),
        "25 - 50":  (25,50),
        "50 o mas": (50, df["Infant mortality"].max()),
    }
    life_map = {
        "0 - 60":   (0,60),
        "60 - 70":  (60,70),
        "70 - 80":  (70,80),
        "80 o mas": (80, df["Life Expectancy"].max()),
    }

    # — ROW 2: Four multi‑select columns —
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("**Continente**")
        sel_cont = st.multiselect(
            label="Selecciona continentes",
            options=list(cont_map.keys()),
            default=list(cont_map.keys()),
        )

    with c2:
        st.markdown("**Cantidad Población**")
        sel_pop = st.multiselect(
            label="Selecciona rangos de población",
            options=list(pop_map.keys()),
            default=list(pop_map.keys()),
        )

    with c3:
        st.markdown("**Mortalidad Infantil (muertes / 1 000)**")
        sel_mort = st.multiselect(
            label="Selecciona rangos de mortalidad",
            options=list(mort_map.keys()),
            default=list(mort_map.keys()),
        )

    with c4:
        st.markdown("**Esperanza de Vida (años promedio)**")
        sel_life = st.multiselect(
            label="Selecciona rangos de esperanza",
            options=list(life_map.keys()),
            default=list(life_map.keys()),
        )

    st.markdown("---")

    # — apply all four filters by unioning the ranges —
    df2 = df.copy()

    # continent
    if sel_cont:
        df2 = df2[df2["Continent"].isin([cont_map[c] for c in sel_cont])]

    # population
    if sel_pop:
        mask = pd.Series(False, index=df2.index)
        for k in sel_pop:
            lo, hi = pop_map[k]
            mask |= df2["Population"].between(lo, hi)
        df2 = df2[mask]

    # infant mortality
    if sel_mort:
        mask = pd.Series(False, index=df2.index)
        for k in sel_mort:
            lo, hi = mort_map[k]
            mask |= df2["Infant mortality"].between(lo, hi)
        df2 = df2[mask]

    # life expectancy
    if sel_life:
        mask = pd.Series(False, index=df2.index)
        for k in sel_life:
            lo, hi = life_map[k]
            mask |= df2["Life Expectancy"].between(lo, hi)
        df2 = df2[mask]

    # now df2 holds exactly the union of every selected bucket

    # — ROW 3: Scatter + Map side‑by‑side with Spanish columns/legend/hover —
    colA, colB = st.columns(2)
    viz_h = 450

    # 1) First, rename df2 to a Spanish‐columns DataFrame
    tmp2 = (
        df2.rename(columns={
            "Country_ES":       "País",
            "Population":       "Población",
            "Infant mortality": "Mortalidad infantil",
            "Life Expectancy":  "Esperanza de vida",
            "Country Code":     "Código País",
            "Continente":       "Continente",
        })
    )

    # — Scatterplot —
    with colA:
        st.subheader("Mortalidad Infantil vs Esperanza de Vida")
        fig1 = px.scatter(
            tmp2,
            x="Mortalidad infantil",
            y="Esperanza de vida",
            size="Población",
            color="Continente",
            hover_name="País",
            height=viz_h,
        )
        fig1.update_layout(
            xaxis_title="Mortalidad infantil",
            yaxis_title="Esperanza de vida",
            legend_title_text="Continente",
            margin={"t":10, "l":0, "r":0, "b":0},
            template="plotly_white",
        )
        st.plotly_chart(fig1, use_container_width=True, height=viz_h,
                        config={"displayModeBar": False})

    # — Geo‑scatter map —
    with colB:
        st.subheader("Mapa de Mortalidad Infantil y Esperanza de Vida")
        fig2 = px.scatter_geo(
            tmp2,
            locations="Código País",
            size="Población",
            hover_name="País",
            hover_data=["Población","Código País"],
            projection="equirectangular",
            height=viz_h,
            color_discrete_sequence=["#e65555"],  # red dots
        )
        fig2.update_geos(
            showland=True, landcolor="white",
            showocean=True, oceancolor="#d3d3d3",
            showcountries=True, countrycolor="white",
            showcoastlines=True, coastlinecolor="lightgray",
            showframe=False,
        )
        fig2.update_layout(
            showlegend=False,
            margin={"t":10, "l":0, "r":0, "b":0},
            template="plotly_white",
        )
        st.plotly_chart(fig2, use_container_width=True, height=viz_h,
                        config={"displayModeBar": False})

    st.markdown("---")

    # — ROW 4: Full‑width table —
    st.subheader("Detalle de Indicadores por País")
    tbl = (
        df2[["Continente","Country_ES","Population","Life Expectancy","Infant mortality"]]
        .rename(columns={
            "Continente":       "Continente",
            "Country_ES":       "País",
            "Population":       "Población",
            "Life Expectancy":  "Esperanza de vida",
            "Infant mortality": "Mortalidad infantil",
        })
        .sort_values(["Continente","País"])
        .reset_index(drop=True)
    )
    st.dataframe(tbl, use_container_width=True, height=400)

def main():
    df = load_data()
    page = st.sidebar.radio("Navegación", ["Población", "Indicadores"])
    if page == "Población":
        page_population(df)
    else:
        page_indicators(df)

if __name__ == "__main__":
    main()