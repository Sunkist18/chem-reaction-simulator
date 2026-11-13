import streamlit as st


def read_reactions():
    file = open("reactions.txt", "r", encoding="utf-8")
    reactions = []

    for line in file:
        line = line.strip()

        if line != "":
            reaction = line.split(",", 3)
            reactions.append(reaction)

    file.close()
    return reactions


def parse_reaction(equation):
    sides = equation.split("->")
    result = []

    for side in sides:
        substances = side.split("+")
        parsed_substances = []

        for substance in substances:
            substance = substance.strip()
            coefficient_text = ""
            position = 0

            while position < len(substance) and substance[position].isdigit():
                coefficient_text += substance[position]
                position += 1

            if coefficient_text == "":
                coefficient = 1
            else:
                coefficient = int(coefficient_text)

            formula = substance[position:].strip()
            parsed_substances.append([formula, coefficient])

        result.append(parsed_substances)

    return result


def react_once(reactant_counts, product_counts, parsed_reaction):
    reactants = parsed_reaction[0]
    products = parsed_reaction[1]

    for i in range(len(reactants)):
        coefficient = reactants[i][1]

        if reactant_counts[i] < coefficient:
            return False

    for i in range(len(reactants)):
        coefficient = reactants[i][1]
        reactant_counts[i] -= coefficient

    for i in range(len(products)):
        coefficient = products[i][1]
        product_counts[i] += coefficient

    return True


def show_table(title, substances):
    st.subheader(title)

    table = "| 화학식 | 계수 |\n| --- | --- |\n"

    for substance in substances:
        formula = substance[0]
        coefficient = substance[1]
        table += "| " + formula + " | " + str(coefficient) + " |\n"

    st.markdown(table)


def show_history_table(reactants, products, history):
    st.subheader("단계별 분자 수")

    substances = reactants + products
    table = "| 단계 |"

    for substance in substances:
        table += " " + substance[0] + " |"

    table += "\n| --- |"

    for substance in substances:
        table += " --- |"

    table += "\n"

    for step in range(len(history)):
        table += "| " + str(step) + " |"

        for count in history[step]:
            table += " " + str(count) + " |"

        table += "\n"

    st.markdown(table)


def show_screen():
    st.title("화학 반응 시뮬레이터")

    reactions = read_reactions()
    reaction_names = []

    for reaction in reactions:
        reaction_names.append(reaction[0])

    selected_name = st.sidebar.selectbox("반응 선택", reaction_names)
    selected_index = reaction_names.index(selected_name)
    selected_reaction = reactions[selected_index]

    equation = selected_reaction[1]
    parsed_reaction = parse_reaction(equation)
    reactants = parsed_reaction[0]
    products = parsed_reaction[1]

    st.write("반응식: " + equation)

    reactant_counts = []

    for reactant in reactants:
        formula = reactant[0]
        count = st.number_input(
            formula + " 분자 수",
            min_value=0,
            value=0,
            step=1
        )
        reactant_counts.append(count)

    current_inputs = [selected_name, equation] + reactant_counts

    if "previous_inputs" not in st.session_state:
        st.session_state.previous_inputs = []

    if "history" not in st.session_state:
        st.session_state.history = []

    if current_inputs != st.session_state.previous_inputs:
        st.session_state.history = []
        st.session_state.previous_inputs = current_inputs

    show_table("반응물", reactants)
    show_table("생성물", products)

    if st.sidebar.button("실행"):
        product_counts = []

        for product in products:
            product_counts.append(0)

        history = []
        history.append(reactant_counts + product_counts)

        while react_once(reactant_counts, product_counts, parsed_reaction):
            history.append(reactant_counts + product_counts)

        st.session_state.history = history

    if len(st.session_state.history) > 0:
        show_history_table(
            reactants,
            products,
            st.session_state.history
        )

        reaction_count = len(st.session_state.history) - 1

        if reaction_count == 0:
            st.warning("반응물이 부족하여 반응하지 않았습니다.")
        else:
            st.success(
                "총 " + str(reaction_count)
                + "번 반응했습니다. 반응물이 부족하여 종료했습니다."
            )


show_screen()
