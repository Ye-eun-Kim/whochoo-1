from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.json_loader import JSONLoader
from ragatouille import RAGPretrainedModel
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.llms import HuggingFaceHub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from utils.arguments import parse_arguments
import json
import torch
from transformers import AutoModel, AutoTokenizer
from accelerate import Accelerator
import numpy as np

def main():
    args = parse_arguments()

    def metadata_func(record: dict, metadata: dict) -> dict:
        original = json.load(open(args.metadata_path, "r"))
        metadata["product"] = original[record.get("item_idx") - 1]  # reviews

        for key in record.keys():
            if key != "item_idx" and key != "content":
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

    print("Starting to create vector database...")

    # Initialize Accelerator
    accelerator = Accelerator()

    # Load model and tokenizer using the transformers library
    model_name = "BAAI/bge-large-en"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    # Prepare model for multi-GPU with accelerator
    model = accelerator.prepare(model)

    # Define a custom embedding model that supports multi-GPU
    class MultiGPUEmbeddings:
        def __init__(self, model, tokenizer):
            self.model = model
            self.tokenizer = tokenizer

        def embed_documents(self, documents):
            batch_size = 8  # Adjust batch size based on GPU memory capacity
            embeddings_list = []
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
                inputs = {k: v.to(accelerator.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                embeddings_list.append(embeddings.cpu().numpy())
            return np.concatenate(embeddings_list, axis=0)

    embeddings_model = MultiGPUEmbeddings(model=model, tokenizer=tokenizer)

    vectordb = FAISS.from_documents(docs, embeddings_model)

    print("Saving vector database locally...")
    vectordb.save_local(args.index_dir)
    print("Vector database saved successfully.")

if __name__ == "__main__":
    main()
