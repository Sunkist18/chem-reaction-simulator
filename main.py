import streamlit as st
import os
import base64


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


def find_molecule_image(formula):
    """
    화학식과 이름이 같은 분자 모형 이미지 파일을 찾습니다.

    입력: formula는 'H2O'와 같은 화학식 문자열입니다.
    반환: 파일이 있으면 경로 문자열, 없으면 빈 문자열입니다.
    main.py 옆 images 폴더에서 png, jpg, jpeg, webp 순서로 찾습니다.
    파일 이름의 대소문자는 화학식과 같아야 합니다.
    """
    # __file__은 현재 main.py의 경로입니다.
    # 실행 위치가 달라도 main.py 옆의 images 폴더를 찾도록 합니다.
    app_folder = os.path.dirname(os.path.abspath(__file__))
    extensions = [".png", ".jpg", ".jpeg", ".webp"]

    for extension in extensions:
        # 예: images/H2O.png. 계수는 파일 이름에 넣지 않습니다.
        image_path = os.path.join(app_folder, "images", formula + extension)

        # 파일이 실제로 있을 때만 이미지 표시 함수에 전달합니다.
        if os.path.isfile(image_path):
            return image_path

    return ""


def load_molecule_image(formula):
    """
    로컬 분자 이미지를 표의 이미지 셀에서 읽을 수 있는 문자열로 바꿉니다.

    입력: formula는 화학식 문자열입니다.
    반환: 이미지 데이터를 포함한 data URL이며 파일이 없거나 읽지 못하면 None입니다.
    ImageColumn은 로컬 파일 경로를 직접 표시하지 못하므로 Base64로 변환합니다.
    """
    image_path = find_molecule_image(formula)

    if image_path == "":
        return None

    # rb는 이미지 같은 바이너리 파일을 읽는 모드입니다.
    try:
        file = open(image_path, "rb")
        image_bytes = file.read()
        file.close()
    except OSError:
        return None

    # 확장자에 맞는 이미지 형식을 지정합니다.
    extension = os.path.splitext(image_path)[1]
    image_type = extension[1:]
    if image_type == "jpg":
        image_type = "jpeg"

    # Base64는 이미지 바이트를 표에 전달할 수 있는 문자열로 바꾸는 방법입니다.
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    return "data:image/" + image_type + ";base64," + encoded_image


def show_table(title, substances):
    """
    화학식, 계수, 분자 모형이 각각 셀에 들어가는 실제 표를 표시합니다.

    입력: title은 표 제목, substances는 [화학식, 계수]의 목록입니다.
    이미지가 없는 셀은 비워 두고 해당 물질을 표 아래에 안내합니다.
    반환: 별도의 반환값 없이 화면에 표를 표시합니다.
    """
    st.subheader(title)
    rows = []
    missing_images = []

    for substance in substances:
        formula = substance[0]
        coefficient = substance[1]
        image_data = load_molecule_image(formula)

        # 딕셔너리의 이름은 열 제목이고 값은 해당 행의 셀 내용입니다.
        rows.append({
            "화학식": formula,
            "계수": coefficient,
            "분자 모형": image_data
        })

        if image_data is None:
            missing_images.append(formula)

    # 이미지 열로 지정해야 문자열 대신 이미지가 셀 안에 표시됩니다.
    # 행 높이를 늘려 모형이 보이게 하고 불필요한 행 번호는 숨깁니다.
    st.dataframe(
        rows,
        column_config={
            "분자 모형": st.column_config.ImageColumn("분자 모형", width="medium")
        },
        hide_index=True,
        row_height=100
    )

    if len(missing_images) > 0:
        st.caption("이미지 없음: " + ", ".join(missing_images))


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


def show_history_chart(reactants, products, history):
    """
    단계별 분자 수를 물질마다 하나의 선으로 표시합니다.

    입력: reactants와 products는 해석된 반응물 및 생성물 목록입니다.
          history는 처음 상태부터 마지막 상태까지의 분자 수 기록입니다.
    가로축은 단계, 세로축은 분자 수이며 선의 이름은 화학식입니다.
    반환: 별도의 반환값 없이 화면에 선 그래프를 표시합니다.
    """
    st.subheader("단계별 분자 수 변화")

    substances = reactants + products
    steps = []

    # 0단계는 처음 상태이며 기록의 개수만큼 단계 번호를 만듭니다.
    for step in range(len(history)):
        steps.append(step)

    # 딕셔너리는 이름과 값을 짝지어 저장합니다.
    # 그래프의 열 이름 '단계'에 단계 번호 리스트를 연결합니다.
    chart_data = {"단계": steps}

    # 행 단위 기록에서 같은 물질의 개수만 모아 하나의 선 데이터로 만듭니다.
    for i in range(len(substances)):
        formula = substances[i][0]
        counts = []

        for row in history:
            counts.append(row[i])

        # 예: chart_data['H2'] = [4, 2, 0]
        chart_data[formula] = counts

    # 단계 열을 가로축으로 지정하면 나머지 물질 열마다 선 하나가 생깁니다.
    st.line_chart(
        chart_data,
        x="단계",
        x_label="단계",
        y_label="분자 수"
    )

    # 처음 상태만 있으면 연결할 다음 점이 없어 변화하는 선이 생기지 않습니다.
    if len(history) == 1:
        st.caption("반응이 일어나지 않아 0단계 데이터만 있습니다.")


def show_result(reactants, products, history):
    """
    마지막 상태를 바탕으로 반응 결과를 문장으로 표시합니다.

    입력: reactants와 products는 해석된 반응물 및 생성물 목록입니다.
          history는 처음 상태를 포함한 비어 있지 않은 단계 기록입니다.
    반응하지 못한 경우, 소모된 반응물, 남은 반응물, 생성량을 구분합니다.
    반환: 별도의 반환값 없이 화면에 결과 설명을 표시합니다.
    """
    # 처음 상태만 기록되었다면 반응은 한 번도 일어나지 않은 것입니다.
    if len(history) == 1:
        st.write("반응물이 부족하여 반응하지 않았습니다")
        return

    # 인덱스 -1은 리스트의 마지막 항목, 즉 최종 상태를 뜻합니다.
    final_counts = history[-1]
    # 소모된 물질, 부족한 물질, 남은 개수, 생성량을 따로 모읍니다.
    exhausted = []
    insufficient = []
    remaining = []
    created = []

    # 마지막 상태에서 반응물별 남은 개수를 확인합니다.
    for i in range(len(reactants)):
        formula = reactants[i][0]
        coefficient = reactants[i][1]
        count = final_counts[i]

        # 0개라면 완전히 소모된 반응물입니다.
        if count == 0:
            exhausted.append(formula)

        # 0개가 아니어도 다음 반응에 필요한 계수보다 적으면 부족합니다.
        if count < coefficient:
            insufficient.append(formula)

        # 남아 있는 반응물은 이름과 개수를 문장에 쓸 문자열로 만듭니다.
        if count > 0:
            remaining.append(formula + " " + str(count) + "개")

    # 기록에서 생성물 개수는 반응물 개수들 다음 위치부터 시작합니다.
    for i in range(len(products)):
        formula = products[i][0]
        count = final_counts[len(reactants) + i]
        created.append(formula + " " + str(count) + "개")

    # 한 물질만 소모되었는지, 여러 물질이 동시에 소모되었는지 구분합니다.
    if len(exhausted) == 1:
        st.write(exhausted[0] + "가 먼저 모두 소모되었습니다.")
    # join은 문자열 목록을 지정한 구분자(여기서는 쉼표와 공백)로 연결합니다.
    elif len(exhausted) > 1:
        st.write(", ".join(exhausted) + "가 동시에 모두 소모되었습니다.")
    else:
        st.write("완전히 소모된 반응물은 없습니다.")

    st.write(
        "다음 반응에 필요한 "
        + ", ".join(insufficient)
        + "의 개수가 부족하여 반응이 멈췄습니다."
    )

    # 남은 반응물이 있으면 이름과 개수를, 없으면 없다는 문장을 표시합니다.
    if len(remaining) > 0:
        st.write("남은 반응물은 " + ", ".join(remaining) + "입니다.")
    else:
        st.write("남은 반응물은 없습니다.")

    # 생성물은 0개에서 시작했으므로 마지막 개수가 총 생성량입니다.
    st.write("생성물은 " + ", ".join(created) + " 만들어졌습니다.")


def show_screen():
    """
    입력 화면을 만들고 반응 실행 및 결과 표시를 연결합니다.

    입력: 함수 인자는 없으며 사용자가 화면에서 반응과 분자 수를 입력합니다.
    실행 버튼을 누르면 반응물이 부족해질 때까지 계산하고 기록을 저장합니다.
    반응이나 숫자를 바꾸면 기록을 지우며 같은 입력에서는 결과를 유지합니다.
    반환: 별도의 반환값 없이 Streamlit 화면을 표시합니다.
    """
    st.title("화학 반응 시뮬레이터")

    # 파일에서 읽은 반응의 이름만 모아 선택 메뉴에 사용합니다.
    reactions = read_reactions()
    reaction_names = []

    for reaction in reactions:
        reaction_names.append(reaction[0])

    # 선택한 이름의 위치를 찾아 그 반응의 전체 정보를 꺼냅니다.
    selected_name = st.sidebar.selectbox("반응 선택", reaction_names)
    selected_index = reaction_names.index(selected_name)
    selected_reaction = reactions[selected_index]

    # 반응식을 해석하여 반응물 및 생성물 목록을 만듭니다.
    equation = selected_reaction[1]
    parsed_reaction = parse_reaction(equation)
    reactants = parsed_reaction[0]
    products = parsed_reaction[1]

    # 파일에 저장된 반응식, 종류, 설명을 표시합니다.
    st.write("반응식: " + equation)
    st.write("종류: " + selected_reaction[2])
    st.write("설명: " + selected_reaction[3])

    reactant_counts = []

    # 반응물 종류마다 입력칸 하나를 만들고 같은 순서로 개수를 저장합니다.
    for reactant in reactants:
        formula = reactant[0]
        # 최솟값과 처음 값은 0이며 증감 버튼은 1개씩 바꿉니다.
        count = st.number_input(
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
    if st.sidebar.button("실행"):
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
        # 반응물과 생성물의 모형 표도 실행 후에만 표시합니다.
        show_table("반응물", reactants)
        show_table("생성물", products)

        show_history_table(
            reactants,
            products,
            st.session_state.history
        )

        # 표와 같은 저장 기록으로 그래프를 그리므로 결과가 함께 유지됩니다.
        show_history_chart(
            reactants,
            products,
            st.session_state.history
        )

        show_result(
            reactants,
            products,
            st.session_state.history
        )


# 정의한 화면 함수를 호출하여 앱을 표시합니다.
show_screen()
