import streamlit as st
from html import escape
from pathlib import Path

def read_reactions():
    """
    반응 정보 파일을 읽고 사용할 수 있는 반응 목록을 반환합니다.

    입력: 없음. 같은 폴더의 reactions.txt를 읽습니다.
    반환: 각 항목이 [이름, 반응식, 종류, 설명]인 리스트입니다.
    파일이 없거나 사용 가능한 반응이 없으면 기본 반응 두 개를 반환합니다.
    항목 수가 네 개가 아니거나 화살표가 없는 줄은 줄 번호와 함께 안내합니다.
    """
    # 파일을 사용할 수 없을 때 대신 사용할 반응 두 개입니다.
    default_reactions = [
        ["물 생성", "2H2 + O2 -> 2H2O", "합성",
         "수소와 산소가 반응하여 물이 만들어집니다."],
        ["암모니아 합성", "N2 + 3H2 -> 2NH3", "합성",
         "질소와 수소가 반응하여 암모니아가 만들어집니다."]
    ]

    # try 안에서 파일 열기를 시도하고, 파일이 없으면 except에서 처리합니다.
    try:
        file = open("reactions.txt", "r", encoding="utf-8")
    except FileNotFoundError:
        st.warning("reactions.txt 파일이 없어 기본 반응 2개로 실행합니다.")
        return default_reactions

    reactions = []
    line_number = 0
    has_content = False

    # 빈 줄도 줄 번호에 포함하여 실제 파일의 줄 번호와 맞춥니다.
    for line in file:
        line_number += 1
        line = line.strip()

        # 빈 줄은 무시합니다. 공백이나 빈 줄만 있는 파일은 빈 파일로 처리합니다.
        if line != "":
            has_content = True
            reaction = line.split(",")

            # 쉼표로 나눈 항목이 정확히 네 개일 때만 반응식을 검사합니다.
            if len(reaction) != 4:
                st.warning(
                    str(line_number)
                    + "번째 줄을 건너뛰었습니다: 항목은 4개여야 합니다."
                )
            elif "->" not in reaction[1]:
                st.warning(
                    str(line_number)
                    + "번째 줄을 건너뛰었습니다: 반응식에 ->가 필요합니다"
                )
            else:
                reactions.append(reaction)

    # 기본 반응으로 바꾸기 전에 열었던 파일을 닫습니다.
    file.close()

    # 모든 줄이 잘못된 경우에도 빈 메뉴가 생기지 않도록 기본 반응을 사용합니다.
    if len(reactions) == 0:
        if has_content:
            st.warning("사용 가능한 반응이 없어 기본 반응 2개로 실행합니다.")
        else:
            st.warning("reactions.txt가 비어 있어 기본 반응 2개로 실행합니다.")
        return default_reactions

    return reactions


def parse_reaction(equation):
    """
    반응식에서 반응물과 생성물의 화학식 및 계수를 분리합니다.

    입력: equation은 '2H2 + O2 -> 2H2O' 형태의 문자열입니다.
    반환: [반응물 목록, 생성물 목록]이며 각 물질은 [화학식, 계수]입니다.
    예: [[['H2', 2], ['O2', 1]], [['H2O', 2]]
    계수는 양의 정수이며 생략하면 1로 처리합니다.
    화학식 안의 원자 수나 반응식의 원자 수 균형은 검사하지 않습니다.
    """
    # 화살표를 기준으로 왼쪽 반응물과 오른쪽 생성물을 나눕니다.
    sides = equation.split("->")
    result = []

    # 반응물 쪽과 생성물 쪽을 같은 방법으로 처리합니다.
    for side in sides:
        # 더하기 기호로 연결된 물질들을 각각 분리합니다.
        substances = side.split("+")
        parsed_substances = []

        # 각 물질의 앞뒤 공백을 제거하고 계수를 읽을 준비를 합니다.
        for substance in substances:
            substance = substance.strip()
            coefficient_text = ""
            position = 0

            # 문자열 맨 앞의 숫자만 읽습니다. 12H2라면 12가 계수입니다.
            # 문자열 길이를 먼저 확인하므로 범위를 벗어난 위치를 읽지 않습니다.
            while position < len(substance) and substance[position].isdigit():
                coefficient_text += substance[position]
                position += 1

            # 앞에 숫자가 없으면 계수는 1이고, 있으면 정수로 바꿉니다.
            if coefficient_text == "":
                coefficient = 1
            else:
                coefficient = int(coefficient_text)

            # 계수 뒤부터 끝까지가 화학식입니다. H2의 2는 그대로 남습니다.
            formula = substance[position:].strip()
            parsed_substances.append([formula, coefficient])

        # 반응물 목록을 먼저, 생성물 목록을 나중에 담습니다.
        result.append(parsed_substances)

    return result


def react_once(reactant_counts, product_counts, parsed_reaction):
    """
    반응물이 충분하면 반응을 한 번 진행합니다.

    입력: reactant_counts는 반응물 개수 리스트입니다.
          product_counts는 생성물 개수 리스트입니다.
          parsed_reaction은 parse_reaction의 반환값입니다.
    개수 리스트는 해석된 물질 목록과 길이 및 순서가 같아야 합니다.
    반환: 반응하면 True, 반응물이 부족하면 False입니다.
    반응할 때는 전달받은 두 개수 리스트를 직접 수정합니다.
    하나라도 부족하면 두 리스트 모두 수정하지 않습니다.
    """
    # 해석 결과에서 반응물 목록과 생성물 목록을 꺼냅니다.
    reactants = parsed_reaction[0]
    products = parsed_reaction[1]

    # i는 목록에서 물질의 위치를 나타냅니다.
    for i in range(len(reactants)):
        coefficient = reactants[i][1]

        # 하나라도 부족하면 즉시 종료합니다. 이때까지 개수는 바꾸지 않습니다.
        if reactant_counts[i] < coefficient:
            return False

    # i는 목록에서 물질의 위치를 나타냅니다.
    for i in range(len(reactants)):
        coefficient = reactants[i][1]
        # 모든 반응물이 충분한 것을 확인한 뒤 계수만큼 소비합니다.
        reactant_counts[i] -= coefficient

    # 생성물은 각각 자기 계수만큼 늘어납니다.
    for i in range(len(products)):
        coefficient = products[i][1]
        product_counts[i] += coefficient

    # 반응을 한 번 완료했다는 뜻으로 True를 반환합니다.
    return True


def show_history_table(reactants, products, history):
    """
    처음 상태와 매 반응 단계의 분자 수를 표로 표시합니다.

    입력: reactants와 products는 해석된 반응물 및 생성물 목록입니다.
          history는 각 단계의 분자 수 리스트를 모은 리스트입니다.
    각 행의 분자 수는 반응물 다음 생성물 순서이며 0단계는 처음 상태입니다.
    반환: 별도의 반환값 없이 화면에 표를 표시합니다.
    """
    st.subheader("단계별 분자 수")

    # 기록된 개수와 같은 순서로 반응물과 생성물 목록을 연결합니다.
    substances = reactants + products
    table = "| 단계 |"

    # 물질 개수만큼 표의 열을 만듭니다.
    for substance in substances:
        table += " " + substance[0] + " |"

    table += "\n| --- |"

    # 물질 개수만큼 표의 열을 만듭니다.
    for substance in substances:
        table += " --- |"

    table += "\n"

    # 단계 번호는 0부터 시작하며, 단계 하나를 표의 한 행으로 만듭니다.
    for step in range(len(history)):
        table += "| " + str(step) + " |"

        # 해당 단계에 기록된 모든 물질의 분자 수를 순서대로 넣습니다.
        for count in history[step]:
            table += " " + str(count) + " |"

        table += "\n"

    # 완성된 단계별 표를 표시합니다.
    st.markdown(table)


def show_change_table(reactants, products, history):
    st.subheader("반응 전후 분자 수")
    header = "| 분자 수(개) |"
    divider = "| --- |"
    before = "| 반응 전 |"
    change = "| 변화량 |"
    after = "| **반응 후** |"

    for i, substance in enumerate(reactants + products):
        formula = substance[0].translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))
        first = history[0][i]
        last = history[-1][i]
        difference = last - first
        sign = "+" if difference > 0 else ""
        header += f" {formula} |"
        divider += " ---: |"
        before += f" {first} |"
        change += f" {sign}{difference} |"
        after += f" **{last}** |"

    with st.container(key="reaction-summary"):
        st.markdown("\n".join([header, divider, before, change, after]))


def show_result(reactants, products, history):
    """
    마지막 상태를 바탕으로 반응 결과를 문장으로 표시합니다.

    입력: reactants와 products는 해석된 반응물 및 생성물 목록입니다.
          history는 처음 상태를 포함한 비어 있지 않은 단계 기록입니다.
    반응하지 못한 경우, 소모된 반응물, 남은 반응물, 생성량을 구분합니다.
    반환: 별도의 반환값 없이 화면에 결과 설명을 표시합니다.
    """
    final_counts = history[-1]
    remaining = []
    missing = []
    created = []

    # 마지막 상태에서 반응물별 남은 개수를 확인합니다.
    for i in range(len(reactants)):
        formula = reactants[i][0]
        coefficient = reactants[i][1]
        count = final_counts[i]

        if count < coefficient:
            missing.append(formula + " " + str(coefficient - count) + "개")

        # 남아 있는 반응물은 이름과 개수를 문장에 쓸 문자열로 만듭니다.
        if count > 0:
            remaining.append(formula + " " + str(count) + "개")

    # 기록에서 생성물 개수는 반응물 개수들 다음 위치부터 시작합니다.
    for i in range(len(products)):
        formula = products[i][0]
        count = final_counts[len(reactants) + i]
        created.append(formula + " " + str(count) + "개")

    if len(history) == 1:
        st.write("반응하려면 " + ", ".join(missing) + " 더 필요합니다.")
        return

    st.html('<h2 class="reaction-result">' + escape(", ".join(created)) + ' 생성</h2>')
    # 남은 반응물이 있으면 이름과 개수를, 없으면 없다는 문장을 표시합니다.
    if len(remaining) > 0:
        st.write("남은 반응물은 " + ", ".join(remaining) + "입니다.")
    else:
        st.write("남은 반응물은 없습니다.")


def show_screen():
    """
    입력 화면을 만들고 반응 실행 및 결과 표시를 연결합니다.

    입력: 함수 인자는 없으며 사용자가 화면에서 반응과 분자 수를 입력합니다.
    실행 버튼을 누르면 반응물이 부족해질 때까지 계산하고 기록을 저장합니다.
    반응이나 숫자를 바꾸면 기록을 지우며 같은 입력에서는 결과를 유지합니다.
    반환: 별도의 반환값 없이 Streamlit 화면을 표시합니다.
    """
    st.set_page_config(page_title="화학 반응 시뮬레이터", layout="centered")
    css = Path(__file__).with_name("style.css").read_text(encoding="utf-8")
    st.html("<style>" + css + "</style>")
    st.title("화학 반응 시뮬레이터")

    # 파일에서 읽은 반응의 이름만 모아 선택 메뉴에 사용합니다.
    reactions = read_reactions()
    reaction_names = []

    for reaction in reactions:
        reaction_names.append(reaction[0])

    # 선택한 이름의 위치를 찾아 그 반응의 전체 정보를 꺼냅니다.
    selected_name = st.selectbox("반응 선택", reaction_names, key="selected_name")
    selected_index = reaction_names.index(selected_name)
    selected_reaction = reactions[selected_index]

    # 반응식을 해석하여 반응물 및 생성물 목록을 만듭니다.
    equation = selected_reaction[1]
    parsed_reaction = parse_reaction(equation)
    reactants = parsed_reaction[0]
    products = parsed_reaction[1]

    # 파일에 저장된 반응식, 종류, 설명을 표시합니다.
    sides = []
    for side in parsed_reaction:
        terms = []
        for formula, coefficient in side:
            term = formula.translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))
            if coefficient != 1:
                term = str(coefficient) + term
            terms.append(term)
        sides.append(" + ".join(terms))
    st.html('<h2 class="reaction-equation">' + escape(" → ".join(sides)) + '</h2>')
    st.caption(" · ".join(filter(None, selected_reaction[2:])))

    reactant_counts = []
    for i, reactant in enumerate(reactants):
        if i % 2 == 0:
            columns = st.columns(2)
        formula = reactant[0]
        # 최솟값과 처음 값은 0이며 증감 버튼은 1개씩 바꿉니다.
        count = columns[i % 2].number_input(
            formula + " 분자 수",
            min_value=0,
            value=0,
            step=1
        )
        reactant_counts.append(count)

    # 선택한 반응과 입력 개수를 새 리스트로 묶어 변경 여부를 비교합니다.
    current_inputs = [selected_name, equation] + reactant_counts

    # session_state는 화면이 다시 실행되어도 값을 보관합니다.
    # 처음 접속했을 때만 비교용 입력값과 단계 기록을 준비합니다.
    if "previous_inputs" not in st.session_state:
        st.session_state.previous_inputs = []

    if "history" not in st.session_state:
        st.session_state.history = []

    # 반응 또는 숫자가 달라졌으면 이전 결과를 지우고 새 입력을 기억합니다.
    if current_inputs != st.session_state.previous_inputs:
        st.session_state.history = []
        st.session_state.previous_inputs = current_inputs

    # 버튼을 누른 실행에서만 처음 입력값으로 전체 반응을 계산합니다.
    if st.button("실행"):
        product_counts = []

        # 생성물은 종류별로 0개에서 시작합니다.
        for product in products:
            product_counts.append(0)

        history = []
        # +로 새 리스트를 만들어 저장하므로 이후 개수 변경이 이전 기록에 영향을 주지 않습니다.
        history.append(reactant_counts + product_counts)

        # True일 때마다 한 단계 기록하고, False가 반환되면 반복을 끝냅니다.
        while react_once(reactant_counts, product_counts, parsed_reaction):
            # +로 새 리스트를 만들어 저장하므로 이후 개수 변경이 이전 기록에 영향을 주지 않습니다.
            history.append(reactant_counts + product_counts)

        # 전체 기록을 저장해 다음 화면 실행에서도 사용할 수 있도록 합니다.
        st.session_state.history = history

    # 결과 표시는 버튼 조건 밖에 두어 저장된 기록이 있으면 계속 보여 줍니다.
    if len(st.session_state.history) > 0:
        show_result(reactants, products, st.session_state.history)
        show_change_table(reactants, products, st.session_state.history)

        with st.expander("단계별 수치 보기"):
            show_history_table(reactants, products, st.session_state.history)


show_screen()
