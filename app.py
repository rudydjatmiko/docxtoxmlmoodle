from parser import run_parser
from core.builder import build_xml

if uploaded_file and process_btn:

    path = save_temp(uploaded_file)

    questions = run_parser(path)
    xml = build_xml(questions)

    st.session_state.xml_result = xml
