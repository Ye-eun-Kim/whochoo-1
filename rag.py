import os

import requests
import torch
import faiss
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from ragatouille import RAGPretrainedModel
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from utils.arguments import parse_arguments
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline


# Merge retrieved document
def format_docs(docs):
    new_docs = []
    for doc in docs:
        metadata = doc.metadata
        review = doc.page_content
        product = metadata["product"]
        product_str = f"##상품:{product['name']}\n\t-브랜드: {product['brand']}\n\t-가격: {product['price']}\n\t-리뷰 수: {product['total_reviews']}\n\t-별점 평균: {product['average_star_rating (out of 5)']}\n"
        review_str = f"##리뷰: {review}\n\t-리뷰 날짜: {metadata['date']}\n\t-리뷰 별점: {metadata['score']}\n\t-유저 정보: {metadata['user_attribute']}\n\t-유저 활동: {metadata['user_activity']}\n"
        new_docs.append("".join([product_str, review_str]))
    return "---\n\n".join(new_doc for new_doc in new_docs)


class RagPipeline():
    def __init__(self, args):
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = args.token

        # Initialize HuggingFaceBgeEmbeddings with GPU support
        embeddings_model = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-large-en",
            model_kwargs={"device": "cuda"}
        )

        self.embeddings_model = embeddings_model
        self.vectordb = FAISS.load_local(args.index_dir, self.embeddings_model, allow_dangerous_deserialization=True)
        self.reranker = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
        self.reranker = torch.nn.DataParallel(self.reranker)

        self.retriever = self.vectordb.as_retriever(search_kwargs={"k": args.top_k})
        self.compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.reranker.module.as_langchain_document_compressor(), base_retriever=self.retriever
        )

        try:
            if args.is_local:
                self.llm = HuggingFacePipeline.from_model_id(
                    model_id="yanolja/EEVE-Korean-Instruct-10.8B-v1.0",
                    task="text-generation",
                    device=None,
                    model_kwargs={"device_map":"auto"}, # -1 for CPU, 
                    batch_size=2,  # adjust as needed based on GPU map and model size
                    pipeline_kwargs={"max_new_tokens":args.max_new_tokens}
                )
            else:
                self.llm = HuggingFaceEndpoint(
                    repo_id=args.model_id, temperature=0.1, max_new_tokens=args.max_new_tokens
                )
        except requests.exceptions.HTTPError as e:
            print(f"Failed to initialize HuggingFaceEndpoint: {e}")
            raise

        self.prompt = self._format_prompt()
        self.rag_chain = self._create_chain()

    def _format_prompt(self):
        prompt = ChatPromptTemplate(
            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                input_variables=["context", "question"],
                template=("## Instruction: 당신은 이제부터 화장품 추천 챗봇입니다. 화장품 리뷰와 화장품 정보를 참고해서 사용자가 작성한 프롬프트에 제일 적합한 화장품을 추천하고 추천 이유를 알려주세요."
                          "추천 이유는 사용자의 리뷰에서 근거를 3가지 찾아서 간단하고 명확하게 알려줘야 합니다. (1. 사용자의 요구사항에 적합하다는 근거/ 2. 사용자의 요구사항 외 제품 효능 관련/ 3. 총 리뷰수, 별점 관련)"
                          "당신의 분석 결과는 자신의 요구사항에 적합한 화장품을 추천받고 싶은 사용자에게 전달됩니다. "
                          
                        #    "\n\n## Example: \n사용자: 건성이고 자극에 민감한 피부에 알맞은 앰플을 추천해줘."
                        #     "\nAnswer: OO님의 피부 고민에 적합한 화장품을 추천해드릴게요."
                        #      "추천 제품은 [더보이즈 현재PICK]앰플엔 세라마이드샷 보습장벽앰플 100ml기획(+10ml) 이에요. "
                        #      "###추천 이유: "
                        #      "1. 많은 리뷰에서 건성 피부에 잘 맞고, 보습과 진정효과도 제공한다고 언급하고 있어 건성 피부에 적합합니다. "
                        #      "2. 대부분의 리뷰에서 이 제품이 자극이 없고 순하다고 언급하고 있어 민감한 피부에 적합합니다. "
                        #      "3. 위 기능뿐만 아니라 이 제품이 잡티, 기미, 색소 침착을 개선하는데 도움이 됩니다. "
                        #      "4. 앰플엔 세라마이드샷 보습장벽앰플은 2114개의 리뷰를 통해 평균 별점 4.9점을 받아 높은 고객 만족도를 보이는 제품입니다. "
                        #      "위와 같은 이유로 앰플엔 세라마이드샷 보습장벽앰플을 OO님의 피부고민에 적합한 화장품으로 추천드립니다. "
                          "\n\n## 사용자: {question}\n\n## 리뷰 및 화장품: {context}\n\n## 추천: ")
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
        try:
            response = self.rag_chain.invoke(prompt)
        except requests.exceptions.HTTPError as e:
            print(f"Failed to get response from Hugging Face API: {e}")
            response = "죄송해요, 연관 제품을 찾지 못했어요. 원하시는 제품을 조금 더 구체적으로 알려주세요!"
        return response


if __name__ == "__main__":
    args = parse_arguments()

    if not args.prompt:
        args.prompt = input("어떤 화장품을 추천받고 싶으신가요?:\n")

    os.environ["HUGGINGFACEHUB_API_TOKEN"] = args.token

    embeddings_model = HuggingFaceBgeEmbeddings(model_kwargs={"device": "cuda"})

    vectordb = FAISS.load_local(args.index_dir, embeddings_model, allow_dangerous_deserialization=True)
    rag_model = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
    rag_model = torch.nn.DataParallel(rag_model)

    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=rag_model.module.as_langchain_document_compressor(), base_retriever=retriever
    )

    prompt = ChatPromptTemplate(
        messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
            input_variables=["context", "question"],
            template="### 과제: 너는 화장품 추천 챗봇이야. 리뷰와 화장품 정보를 참고해서 사용자에게 맞는 화장품을 친절하게 추천해주고 그 이유도 알려줘.\n\n### 사용자: {question}\n\n### 리뷰: {context}\n\n### 추천: \n상품명: \n추천 이유: "
        ))],
        input_variables=["context", "question"]
    )

    llm = HuggingFaceEndpoint(
        repo_id=args.model_id, temperature=0.1,  max_new_tokens=2048
    )

    rag_chain = (
            {"context": compression_retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    response = rag_chain.invoke(args.prompt)
    print(response)
