import requests
import os
from requests.exceptions import HTTPError
import zipfile
import json
import math

domain = "https://lmcodequestacademy.com"

template: str
check: str

def grabPage(difficulty: list[int] = [], page = 1):
    url = f"{domain}/api/quest/get-problems"
    payload = {"difficulty" : difficulty, "page" : page, "status" : [], "term" : ""}

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        return None
    return response.json()

def setupProblem(problem):
    directory = "working"
    os.makedirs(directory, exist_ok=True)

    folder = f"{problem['difficulty']['name']}-{problem['slug']}"

    path = os.path.join(directory, folder)
    os.makedirs(path, exist_ok=True)

    pdf_url = f"{domain}/api/static/problems/{problem['slug']}"
    samples_url = f"{domain}/api/static/samples/{problem['slug']}"

    pdf_response = requests.get(pdf_url)
    sample_response = requests.get(samples_url)

    if pdf_response.status_code == 200:
        with open(os.path.join(path, "descriptor.pdf"), "wb") as f:
            f.write(pdf_response.content)
    else:
        raise HTTPError()

    if sample_response.status_code == 200:
        zip_file = os.path.join(path, "sets.zip")
        with open(zip_file, "wb") as f:
            f.write(sample_response.content)

        extract = os.path.join(path, "extract")
        os.makedirs(extract, exist_ok=True)
        with zipfile.ZipFile(zip_file, "r") as f:
            f.extractall(extract)
        os.remove(zip_file)

        input_directory = os.path.join(path, "inputs")
        os.makedirs(input_directory, exist_ok=True)
        output_directory = os.path.join(path, "outputs")
        os.makedirs(output_directory, exist_ok=True)

        for file in os.listdir(extract):
            isInput = file.endswith(".in")
            output_path = input_directory if isInput else output_directory
            output_prefix = "input" if isInput else "output"
            output_num = file[0]
            output_name = f"{output_prefix}{output_num}.txt"
            os.rename(os.path.join(extract, file), os.path.join(output_path, output_name))
        os.rmdir(extract)

        with open(os.path.join(path, "main.py"), "w") as f:
            f.write(template)

        with open(os.path.join(path, "check.py"), "w") as f:
            f.write(check)    

    else:
        raise HTTPError()

def main():
    global template, check

    with open("temps/templates/main.py", "r") as f:
        template = f.read()

    with open("temps/templates/check.py", "r") as f:
        check = f.read()

    page_count = math.ceil(grabPage()["currentCount"] / 20)

    for i in range(1, page_count + 1):
        page = grabPage(page=i)
        problems = page["problems"]
        for problem in problems: setupProblem(problem)

if __name__ == "__main__":
    main()