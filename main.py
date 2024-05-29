import os
import requests
import streamlit as st
from rag import RagPipeline
from utils.arguments import parse_arguments

CHATBOT_URL = os.getenv("CHATBOT_URL", "http://localhost:8000/hospital-rag-agent")
# API_token = '<KEY>'
# API_URL = ""
# headers = {"Authorization": f"Bearer {API_TOKEN}"}

args = parse_arguments()

rag = RagPipeline(args)


with st.sidebar:
    st.header("About")
    st.markdown(
        """
        Whochoo(후추)는 실사용 리뷰를 기반으로 사용자가 작성한 요구사항에 적합한 화장품을 추천하는 시스템입니다.
        """
    )

    st.header("Example Questions")
    st.markdown("- 건성 피부에 좋은 클렌징 폼을 추천해줘")
    st.markdown("- 쿨톤에 맞는 파운데이션을 추천해줘")

def chat_sidebar():
    st.sidebar.button("📝새로운 대화 시작하기", on_click=remove_context)

def remove_context():
    st.session_state.context = None
    st.session_state["messages"] = [
        {"role": "assistant", "content": "안녕하세요! 후추가 당신에게 맞는 화장품을 찾아드릴게요. 무엇을 도와드릴까요?"}
    ]

def set_sidebar_color(color):
    """
    스트림릿 앱의 사이드바 색상을 설정합니다.
    color: 사이드바 색상 코드 (예: '#F0F0F0')
    """
    st.markdown(
        f"""
        <style>
        .css-1aumxhk {{
            background-color: {color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


st.title("Whochoo")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 후추가 당신에게 맞는 화장품을 찾아드릴게요. 무엇을 도와드릴까요?"}
        ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"]) ## 여기서 에러남!

        if "output" in message.keys():
            st.markdown(message["output"])

        if "explanation" in message.keys():
            with st.status("How was this generated", state="complete"):
                st.info(message["explanation"])

if prompt := st.chat_input("후추에게 물어보세요."):
    st.chat_message("user").markdown(prompt)

    st.session_state.messages.append({"role": "user", "output": prompt})

    data = {"text": prompt}

    with st.spinner("Searching for an answer..."):
        # response = requests.post(CHATBOT_URL, json=data) #### TODO ####
        response = rag.get_response(prompt)

        if response:
            output_text = response # response.json()["output"]
            explanation = "some random text" # response.json()["intermediate_steps"]

        else:
            output_text = """An error occurred while processing your message.
            Please try again or rephrase your message."""
            explanation = output_text

    st.chat_message("assistant").markdown(output_text)
    st.status("How was this generated", state="complete").info(explanation)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "output": output_text,
            "explanation": explanation,
        }
    )