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


def show_result(reactants, products, history):
    if len(history) == 1:
        st.write("반응물이 부족하여 반응하지 않았습니다")
        return

    final_counts = history[-1]
    exhausted = []
    insufficient = []
    remaining = []
    created = []

    for i in range(len(reactants)):
        formula = reactants[i][0]
        coefficient = reactants[i][1]
        count = final_counts[i]

        if count == 0:
            exhausted.append(formula)

        if count < coefficient:
            insufficient.append(formula)

        if count > 0:
            remaining.append(formula + " " + str(count) + "개")

    for i in range(len(products)):
        formula = products[i][0]
        count = final_counts[len(reactants) + i]
        created.append(formula + " " + str(count) + "개")

    if len(exhausted) == 1:
        st.write(exhausted[0] + "가 먼저 모두 소모되었습니다.")
    elif len(exhausted) > 1:
        st.write(", ".join(exhausted) + "가 동시에 모두 소모되었습니다.")
    else:
        st.write("완전히 소모된 반응물은 없습니다.")

    st.write(
        "다음 반응에 필요한 "
        + ", ".join(insufficient)
        + "의 개수가 부족하여 반응이 멈췄습니다."
    )

    if len(remaining) > 0:
        st.write("남은 반응물은 " + ", ".join(remaining) + "입니다.")
    else:
        st.write("남은 반응물은 없습니다.")

    st.write("생성물은 " + ", ".join(created) + " 만들어졌습니다.")


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
    st.write("종류: " + selected_reaction[2])
    st.write("설명: " + selected_reaction[3])

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

        show_result(
            reactants,
            products,
            st.session_state.history
        )


show_screen()
