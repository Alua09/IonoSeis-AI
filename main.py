import streamlit as st
import json

def get_scientific_vtec(city):
    try:
        with open('vtec_data.json', 'r') as f:
            data = json.load(f)
            return data.get(city, 15.0)
    except:
        return 15.0

# Далее в цикле tab1:
# val = get_scientific_vtec(city)
# st.metric("**VTEC**", f"{val:.1f} TECU", ...)