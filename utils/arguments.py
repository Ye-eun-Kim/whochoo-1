import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--index_dir", type=str, default="vector_db")
    parser.add_argument("--metadata_path", type=str, default="./metadata.json")
    parser.add_argument("--data_type", type=str, default="json", choices=["json", "csv"])
    parser.add_argument("--data_path", type=str, default="./data.json")
    parser.add_argument("--model_id", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--token", type=str, default="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", help="Please provide valid HF token.") # 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
    parser.add_argument("--top_k", type=int, default=10)
    
    args = parser.parse_args()
    
    return args