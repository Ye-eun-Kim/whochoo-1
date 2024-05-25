import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--index_dir", type=str, default="vector_db")
    parser.add_argument("--metadata_path", type=str, default="./metadata.json")
    parser.add_argument("--data_type", type=str, default="json", choices=["json", "csv"])
    parser.add_argument("--data_path", type=str, default="./data.json")
    parser.add_argument("--model_id", type=str, default="mistralai/Mistral-7B-Instruct-v0.2")
    
    args = parser.parse_args()
    
    return args