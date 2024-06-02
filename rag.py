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
import os
from utils.arguments import parse_arguments


# merge retrieved document
def format_docs(docs):
    new_docs = []
    
    for doc in docs:
        metadata = doc.metadata
        review = doc.page_content
        product = metadata["product"]
        product_str = "##상품:{name}\n\t-브랜드: {brand}\n\t-가격: {price}\n\t-리뷰 수: {total_reviews}\n\t-별점 평균: {average_star_rating (out of 5)}\n".format_map(product)
        review_str= f"##리뷰: {review}\n\t-리뷰 날짜: {metadata['date']}\n\t-리뷰 별점: {metadata['score']}\n\t-태그: {metadata['user_attribute']}\n"
        
        new_docs.append("".join([product_str, review_str]))
    
    return "---\n\n".join(new_doc for new_doc in new_docs)


class RagPipeline():
    def __init__(self, args):
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = args.token
        
        self.vectordb = FAISS.load_local(args.index_dir, HuggingFaceBgeEmbeddings(), allow_dangerous_deserialization=True)        
        self.reranker = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
        self.retriever = self.vectordb.as_retriever(
            search_kwargs={"k": 5} # top-10
        )
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.reranker.as_langchain_document_compressor(), base_retriever=self.retriever
        )
        self.llm = HuggingFaceEndpoint(
            repo_id=args.model_id, temperature=0.1, model_kwargs={"max_length":2048}
        )
        
        self.prompt = self._format_prompt()
        
        self.rag_chain = self._create_chain()
        
        pass
    
    def _format_prompt(self):
        prompt = ChatPromptTemplate(
            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                input_variables=["context", "question"],
                template="### 과제: 너는 화장품 추천 챗봇이야. 리뷰와 화장품 정보를 참고해서 사용자에게 가장 잘 맞는 화장품을 추천해줘.\n\n### 사용자: {question}\n\n### 리뷰: {context}\n\n### 추천:"
                ))],
            input_variables=["context", "question"]
            )
        return prompt
    
    def _create_chain(self):
        rag_chain = (
            {"context": self.compression_retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return rag_chain
    
    def get_response(self, prompt):
        response = self.rag_chain.invoke(prompt)
        
        return response



if __name__=="__main__":
    
    args = parse_arguments()
    
    if not args.prompt:
        args.prompt = input("어떤 화장품을 추천받고 싶으신가요?:\n")
    
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = args.token


    vectordb = FAISS.load_local(args.index_dir, HuggingFaceBgeEmbeddings(), allow_dangerous_deserialization=True)

    RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
    
    retriever = vectordb.as_retriever(
        search_kwargs={"k": 5} # top-10
    )

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=RAG.as_langchain_document_compressor(), base_retriever=retriever
    )


    prompt = ChatPromptTemplate(
        messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
            input_variables=["context", "question"],
            template="### 과제: 너는 화장품 추천 챗봇이야. 리뷰와 화장품 정보를 참고해서 사용자에게 맞는 화장품을 친절하게 추천해주고 그 이유도 알려줘.\n\n### 사용자: {question}\n\n### 리뷰: {context}\n\n### 추천: \n상품명: \n추천 이유: "
            ))],
        input_variables=["context", "question"]
        )

    llm = HuggingFaceEndpoint(
        repo_id=args.model_id, temperature=0.1, model_kwargs={"max_length":2048}
    )

    

    # 단계 8: 체인 생성(Create Chain)
    rag_chain = (
        {"context": compression_retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


    # question = "민감성 피부를 위한 제품 추천해죠"
    response = rag_chain.invoke(args.prompt)

    print(response)