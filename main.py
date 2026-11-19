import streamlit as st
import base64
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
        file = open(Path(__file__).with_name("reactions.txt"), "r", encoding="utf-8")
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


def counts_at_step(before, changes, step):
    counts = []
    for i in range(len(before)):
        count = before[i] + changes[i] * step
        counts.append(count)
    return counts


def display_formula(formula):
    # 화면에서만 H2O를 H₂O처럼 표시합니다.
    digits = "0123456789"
    subscripts = "₀₁₂₃₄₅₆₇₈₉"
    result = ""
    for letter in formula:
        if letter in digits:
            result += subscripts[int(letter)]
        else:
            result += letter
    return result


def show_history_table(substances, before, changes, steps):
    table = "| 단계 |"
    for substance in substances:
        table += substance[0] + "|"
    table += "\n" + "| --- " * (1 + len(substances)) + "|\n"
    first = 0
    if steps >= 100:
        page = st.number_input("단계 표 페이지", 1, steps // 100 + 1)
        first = (page - 1) * 100
    last_step = min(first + 99, steps)
    for step in range(first, last_step + 1):
        table += f"| {step} |"
        for count in counts_at_step(before, changes, step):
            table += f" {count} |"
        table += "\n"
    st.markdown(table)


def show_molecules(substances, before, after):
    # 개수가 많을 때도 한 그림이 한 분자를 나타내도록 페이지를 나눕니다.
    start = 0
    largest = max(before + after)
    if largest > 100:
        page = st.number_input("물질별 모형 페이지 (100개씩)", 1, (largest + 99) // 100)
        start = (page - 1) * 100
    panel = '<div class="molecule-comparison"><h3>반응 전</h3><h3>반응 후</h3>'
    for i in range(len(substances)):
        formula = substances[i][0]
        path = Path(__file__).with_name("molecules") / (formula + ".svg")
        # SVG 파일 내용을 HTML 이미지에 넣을 수 있는 문자열로 바꿉니다.
        image_bytes = path.read_bytes()
        data = base64.b64encode(image_bytes).decode("ascii")
        icon = f'<img src="data:image/svg+xml;base64,{data}" alt="">'
        for count in (before[i], after[i]):
            visible = count - start
            if visible < 0:
                visible = 0
            elif visible > 100:
                visible = 100
            panel += f'<div class="species"><b>{escape(formula)} · {count}개</b>'
            panel += '<div class="particles">' + icon * visible + '</div></div>'
    st.html(panel + '</div>')


def show_change_table(reactants, products, initial, final):
    st.subheader("반응 전후 분자 수")
    header = "| 분자 수(개) |"
    divider = "| --- |"
    before = "| 반응 전 |"
    change = "| 변화량 |"
    after = "| **반응 후** |"

    substances = reactants + products
    for i in range(len(substances)):
        formula = display_formula(substances[i][0])
        first = initial[i]
        last = final[i]
        difference = last - first
        sign = ""
        if difference > 0:
            sign = "+"
        header += f" {formula} |"
        divider += " ---: |"
        before += f" {first} |"
        change += f" {sign}{difference} |"
        after += f" **{last}** |"

    with st.container(key="reaction-summary"):
        st.markdown("\n".join([header, divider, before, change, after]))


def show_result(reactants, products, final):
    amounts = []
    for i in range(len(products)):
        formula = products[i][0]
        # 최종 개수 목록에는 반응물 다음에 생성물이 들어 있습니다.
        count = final[len(reactants) + i]
        amounts.append(f"{formula} {count}개")
    st.html('<h2 class="reaction-result">최대 생성량 · ' + escape(", ".join(amounts)) + '</h2>')
    remaining = []
    for i in range(len(reactants)):
        formula = reactants[i][0]
        remaining.append(f"{formula} {final[i]}개")
    st.write("남은 반응물 · " + ", ".join(remaining))


def show_screen():
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
            term = display_formula(formula)
            if coefficient != 1:
                term = str(coefficient) + term
            terms.append(term)
        sides.append(" + ".join(terms))
    st.html('<h2 class="reaction-equation">' + escape(" → ".join(sides)) + '</h2>')
    details = []
    for text in selected_reaction[2:]:
        if text != "":
            details.append(text)
    st.caption(" · ".join(details))

    reactant_counts = []
    for i in range(len(reactants)):
        if i % 2 == 0:
            columns = st.columns(2)
        formula = reactants[i][0]
        # 최솟값과 처음 값은 0이며 증감 버튼은 1개씩 바꿉니다.
        count = columns[i % 2].number_input(
            formula + " 분자 수",
            min_value=0,
            value=0,
            step=1
        )
        reactant_counts.append(count)

    # 반응물이 각각 몇 회분인지 계산하고, 가장 적은 횟수까지만 진행합니다.
    possible_steps = []
    for i in range(len(reactants)):
        count = reactant_counts[i]
        coefficient = reactants[i][1]
        possible_steps.append(count // coefficient)
    steps = min(possible_steps)

    # 반응 한 번에 반응물은 계수만큼 줄고 생성물은 계수만큼 늘어납니다.
    before = reactant_counts.copy()
    changes = []
    for reactant in reactants:
        changes.append(-reactant[1])
    for product in products:
        before.append(0)
        changes.append(product[1])
    after = counts_at_step(before, changes, steps)

    show_result(reactants, products, after)
    note = "주어진 반응식의 정반응만 고려한 이론적 최대량입니다."
    if selected_name == "암모니아 합성":
        note += " 실제 암모니아 평형 수율은 온도와 압력에 따라 달라집니다."
    st.caption(note)
    show_molecules(reactants + products, before, after)
    show_change_table(reactants, products, before, after)
    with st.expander("단계별 수치 보기"):
        show_history_table(reactants + products, before, changes, steps)


show_screen()
