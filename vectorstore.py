from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.json_loader import JSONLoader
from langchain.text_splitter import CharacterTextSplitter
from ragatouille import RAGPretrainedModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.llms import HuggingFaceHub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import faiss
import argparse
from utils.arguments import parse_arguments
import json



if __name__=="__main__":
    args = parse_arguments()
    
    def metadata_func(record: dict, metadata: dict) -> dict:
        original = json.load(open(args.metadata_path, "r"))
        metadata["product"] = original[record.get("item_idx")-1] # reviews
        
        for key in record.keys():
            if key != "idx" and key!="content":
                metadata[key] = record.get(key)
        
        return metadata
    
    if args.data_type == "csv":
        loader = CSVLoader(file_path=args.data_path)
    elif args.data_type == "json":
        loader = JSONLoader(
            file_path=args.data_path,
            jq_schema='.[].reviews[]',
            content_key=".content",
            is_content_key_jq_parsable=True,
            metadata_func=metadata_func
        )
    
    docs = loader.load()

    vectordb = FAISS.from_documents(docs, HuggingFaceBgeEmbeddings())
    vectordb.save_local(args.index_dir)