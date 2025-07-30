from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from torch.utils.data import DataLoader, Dataset
import json
from tqdm import tqdm
import pandas as pd
from huggingface_hub import login
login("REMOVED_TOKENCdLfVvdKANboIAkusJJPvNuHTeqznrSchj" )


# Function to create a dataset of course descriptions and table content
class CourseDataset(Dataset):
    def __init__(self, courses_data):
        self.courses_data = courses_data

    def __len__(self):
        return len(self.courses_data)

    def __getitem__(self, idx):
        course_code = list(self.courses_data.keys())[idx]
        course_info = self.courses_data[course_code]

        # Combining the course's text description and table description into a prompt
        text_description = course_info["Text Description"]
        table_description = course_info["Table Description"]

        # Designing the prompt for extracting knowledge and skills
        prompt = f"""
        You are an AI assistant trained to extract skills and knowledge from course descriptions. 
        The following is a description of a course, including both textual and table-based information. 
        Your task is to extract the key skills and knowledge that are associated with the course content.

        Course Code: {course_code}
        Course Text Description: {text_description}
        Course Table Description: {table_description}

        Return only the skills and knowledge as a list of keywords:
        """

        return prompt, course_code


def load_dataset(courses_data):
    # Prepare dataset from the provided course data
    dataset = CourseDataset(courses_data)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False)  # Modify batch size if needed
    return dataloader


def inference(dataloader):
    # Load the pre-trained Llama model (or any other LLM model)
    model_name = "meta-llama/Llama-3.1-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    model = AutoModelForCausalLM.from_pretrained(model_name, 
                                                 torch_dtype=torch.bfloat16, 
                                                 device_map="auto")

    results = {}

    for batch in dataloader:
        prompt, course_code = batch
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=8192)
        input_length = len(prompt[0])

        with torch.no_grad():
            outputs = model.generate(**inputs, 
                                     max_new_tokens=150,
                                     temperature=0.2,
                                     top_p=0.9
                                    )  # Adjust max_new_tokens as needed

        # Decoding the model's output
        batch_results = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the relevant part
        extracted_result = batch_results[input_length:].strip()
        
        # Store the results in a dictionary
        results[course_code] = extracted_result
    
    print(results)

    # # Save results as JSON
    # output_json_path = "extracted_skills_and_knowledge.json"
    # with open(output_json_path, 'w', encoding='utf-8') as f:
    #     json.dump(results, f, ensure_ascii=False, indent=4)

    # print("Inference complete, results saved to:", output_json_path)


if __name__ == '__main__':
    # Sample course data (this would be replaced by your actual JSON structure)
    courses_data = {
        "DSCI551": {
            "Text Description": "USC Viterbi School DSCI 551: Foundations of Data Management...",
            "Table_description": "Page 3 Table: Week | Topic | Readings | Homework/Project | Lab\n1 (1/10) | Data Management Overview..."
        },
        # Add more course data as needed
    }

    # Load dataset from the given courses data
    dataloader = load_dataset(courses_data)

    # Perform inference to extract skills and knowledge
    inference(dataloader)
