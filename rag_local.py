from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from ragatouille import RAGPretrainedModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.llms import HuggingFaceEndpoint
# from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import faiss
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
import os
import torch


os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"


vectordb = FAISS.load_local("./", HuggingFaceBgeEmbeddings(), allow_dangerous_deserialization=True)

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")


retriever = vectordb.as_retriever(
    search_kwargs={"k": 5} # top-10
)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=RAG.as_langchain_document_compressor(), base_retriever=retriever
)

### TODO: create prompt! ###

# prompt = '' # format prompt...

prompt = ChatPromptTemplate(
    messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
        input_variables=["context", "question"],
        template="### 리뷰를 참고해서 사용자에게 화장품을 추천해줘. \n\n ### 사용자: {question}\n\n### 리뷰: {context}\n\n### 추천: "
        ))],
    input_variables=["context", "question"]
    )


gpu_llm = HuggingFacePipeline.from_model_id(
    model_id="yanolja/EEVE-Korean-Instruct-10.8B-v1.0",
    task="text-generation",
    device=None,
    model_kwargs={"device_map":"auto"}, # -1 for CPU, 
    batch_size=2,  # adjust as needed based on GPU map and model size
    pipeline_kwargs={"max_new_tokens":512}
)


# merge retrieved document
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# 단계 8: 체인 생성(Create Chain)
rag_chain = (
    {"context": compression_retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | gpu_llm
    | StrOutputParser()
)


question = "민감성 피부를 위한 제품 추천해죠"
response = rag_chain.invoke(question)

print(response)