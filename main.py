''' 30 day streamlit challenge :
day 3: button'''
#%%
import streamlit as st

# %%
st.header("Button")
left, right = st.columns(2)
btn_reset = right.button("", icon=":material/sync:", type='tertiary')
btn_hello = left.button("Hello", icon=":material/thumb_up:")
if btn_hello:
    st.write("Why hello there!")
else:
    st.write("Goodbye!")

# %%

