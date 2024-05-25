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

loader = CSVLoader(file_path="./sample_output.csv")
docs = loader.load()

vectordb = FAISS.from_documents(docs, HuggingFaceBgeEmbeddings())
vectordb.save_local("./")
# faiss.write_index(vectordb, )