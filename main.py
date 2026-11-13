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


def show_count_table(title, substances, counts):
    st.subheader(title)

    table = "| 화학식 | 분자 수 |\n| --- | --- |\n"

    for i in range(len(substances)):
        formula = substances[i][0]
        count = counts[i]
        table += "| " + formula + " | " + str(count) + " |\n"

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

    product_counts = []

    for product in products:
        product_counts.append(0)

    show_table("반응물", reactants)
    show_table("생성물", products)

    if st.sidebar.button("실행"):
        reacted = react_once(
            reactant_counts,
            product_counts,
            parsed_reaction
        )

        if reacted:
            st.success("반응이 한 번 일어났습니다.")
        else:
            st.warning("반응물이 부족하여 반응하지 않았습니다.")

        show_count_table("실행 후 반응물", reactants, reactant_counts)
        show_count_table("실행 후 생성물", products, product_counts)


show_screen()
