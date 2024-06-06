import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--index_dir", type=str, default="vector_db")
    parser.add_argument("--metadata_path", type=str, default="./data/metadata_1.json")
    parser.add_argument("--data_type", type=str, default="json", choices=["json", "csv"])
    parser.add_argument("--data_path", type=str, default="./data/data_1.json")
    parser.add_argument("--model_id", type=str, default="mistralai/Mistral-7B-Instruct-v0.3")
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--token", type=str, required=True, default=None, help="Please provide valid HF token.")
    parser.add_argument("--is_local", type=int, default=0, help="Whether to use local model")
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--max_new_tokens", type=int, default=700)
    
    args = parser.parse_args()
    
    return args