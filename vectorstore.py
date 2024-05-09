from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from ragatouille import RAGPretrainedModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.llms import HuggingFaceHub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import faiss

loader = CSVLoader(file_path="/path/to/csvfile.csv")
docs = loader.load()

# text_splitter = CharacterTextSplitter(
#     separator="\n\n",
#     chunk_size=100,
#     chunk_overlap=10,
#     length_function=len,
#     is_separator_regex=False,
# )

# RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

vectordb = FAISS.from_documents(docs, HuggingFaceBgeEmbeddings())
faiss.write_index("path/to/vectordb.faiss", vectordb)