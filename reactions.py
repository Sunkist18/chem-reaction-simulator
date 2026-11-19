import streamlit as st


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


def valid_equation(equation):
    # 반응물과 생성물을 나누는 화살표는 하나만 씁니다.
    if equation.count("->") != 1 or not equation.isascii():
        return False

    for side in parse_reaction(equation):
        formulas = []
        for formula, coefficient in side:
            if not formula or coefficient < 1 or formula in formulas:
                return False
            if not formula[0].isupper() or not formula.replace("(", "").replace(")", "").isalnum():
                return False
            formulas.append(formula)
    return True


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
