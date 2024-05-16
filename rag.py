from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from ragatouille import RAGPretrainedModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.llms import HuggingFaceHub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import faiss
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
import os

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"


# loader = CSVLoader(file_path="/path/to/csvfile.csv")
# docs = loader.load()

# text_splitter = CharacterTextSplitter(
#     separator="\n\n",
#     chunk_size=100,
#     chunk_overlap=10,
#     length_function=len,
#     is_separator_regex=False,
# )

# vectordb = faiss.read_index("path/to/vectordb.faiss")

vectordb = FAISS.load_local("./", HuggingFaceBgeEmbeddings(), allow_dangerous_deserialization=True)

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
retriever = vectordb.as_retriever(
    search_kwargs={"k": 10} # top-10
)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=RAG.as_langchain_document_compressor(), base_retriever=retriever
)

### example usage ###
# compressed_docs = compression_retriever.invoke(
#     "What animation studio did Miyazaki found"
# )

### TODO: create prompt! ###

# prompt = '' # format prompt...

prompt = ChatPromptTemplate(
    messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
        input_variables=["context", "question"],
        template="### 리뷰를 참고해서 사용자에게 화장품을 추천해줘. \n\n ### 사용자: {question}\n\n### 리뷰: {context}\n\n### 추천: "
        ))],
    input_variables=["context", "question"]
    )

"""
ChatPromptTemplate(
    input_variables=['context', 'question'], 
    messages=[
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(
                input_variables=['context', 'question'], 
                template="You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\nQuestion: {question} \nContext: {context} \nAnswer:"
                )
            )
        ]
    )
"""

    

### TODO: load hf model! ###
repo_id='yanolja/EEVE-Korean-10.8B-v1.0'
llm = HuggingFaceHub(
    repo_id=repo_id, model_kwargs={"temperature": 0.1, "max_length": 2048}
)

# merge retrieved document
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# 단계 8: 체인 생성(Create Chain)
rag_chain = (
    {"context": compression_retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


question = "민감성 피부를 위한 제품 추천해죠"
response = rag_chain.invoke(question)

print(response)