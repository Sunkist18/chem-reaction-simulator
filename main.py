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


def show_table(title, substances):
    st.subheader(title)

    table = "| 화학식 | 계수 |\n| --- | --- |\n"

    for substance in substances:
        formula = substance[0]
        coefficient = substance[1]
        table += "| " + formula + " | " + str(coefficient) + " |\n"

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

    show_table("반응물", reactants)
    show_table("생성물", products)


show_screen()
