import streamlit as st


def show_screen():
    st.title("화학 반응 시뮬레이터")

    hydrogen_count = st.number_input("수소(H2) 분자 수", min_value=0, value=4, step=1)
    oxygen_count = st.number_input("산소(O2) 분자 수", min_value=0, value=3, step=1)


show_screen()
