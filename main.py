import os
import requests
import streamlit as st
from rag import RagPipeline
from utils.arguments import parse_arguments

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

st.title("Whochoo")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 후추가 당신에게 맞는 화장품을 찾아드릴게요. 무엇을 도와드릴까요?"}
        ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "content" in message:
            st.markdown(message["content"]) ## 여기서 에러남! >>> print(message) >>> dict_keys(['role', 'content']) 

        if "output" in message:
            st.markdown(message["output"])

        if "explanation" in message:
            with st.expander("How was this generated"):
                st.info(message["explanation"])

if prompt := st.chat_input("후추에게 물어보세요."):

    st.session_state.messages.append({"role": "user", "output": prompt})

    st.chat_message("user").markdown(prompt)

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
    st.expander("How was this generated").info(explanation)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "output": output_text,
            "explanation": explanation,
        }
    )