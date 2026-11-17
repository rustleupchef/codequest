import requests
import os
from requests.exceptions import HTTPError
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox
import math
from threading import Thread

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

def get_range_and_checkboxes(maximum: int):
    root = tk.Tk()
    root.title("Selection Dialog")
    root.geometry("320x310")
    root.resizable(False, False)
    
    result = {"range": None, "checkboxes": None}

    ttk.Label(root, text="Configure your settings:", font=("Arial", 11, "bold")).pack(pady=10)

    frame_range = ttk.Frame(root)
    frame_range.pack(pady=5)
    
    ttk.Label(frame_range, text="Min:").grid(row=0, column=0, padx=5)
    min_spin = ttk.Spinbox(frame_range, from_=1, to=maximum, width=6)
    min_spin.set(1)
    min_spin.grid(row=0, column=1, padx=5)
    
    ttk.Label(frame_range, text="Max:").grid(row=0, column=2, padx=5)
    max_spin = ttk.Spinbox(frame_range, from_=1, to=maximum, width=6)
    max_spin.set(10)
    max_spin.grid(row=0, column=3, padx=5)

    ttk.Label(root, text="Select options:").pack(anchor="w", padx=35, pady=(10, 2))
    
    chk_vars = {
        "Practice": tk.BooleanVar(value=False),
        "Easy": tk.BooleanVar(value=False),
        "Medium": tk.BooleanVar(value=False),
        "Hard": tk.BooleanVar(value=False)
    }
    
    chk_frame = ttk.Frame(root)
    chk_frame.pack(pady=5)
    
    row_idx = 0
    col_idx = 0
    for text, var in chk_vars.items():
        cb = ttk.Checkbutton(chk_frame, text=text, variable=var)
        cb.grid(row=row_idx, column=col_idx, sticky="w", padx=15, pady=3)
        col_idx += 1
        if col_idx > 1:
            col_idx = 0
            row_idx += 1

    def on_submit():
        try:
            min_val = int(min_spin.get())
            max_val = int(max_spin.get())
            
            if min_val > max_val:
                messagebox.showerror("Invalid Range", "The Minimum value cannot be greater than the Maximum value.")
                return
                
            selected_checks = [name for name, var in chk_vars.items() if var.get()]
            
            result["range"] = (min_val, max_val)
            result["checkboxes"] = selected_checks
            root.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers for the range.")

    submit_btn = ttk.Button(root, text="Submit", command=on_submit)
    submit_btn.pack(pady=15)

    root.mainloop()
    return result["range"], result["checkboxes"]

def filterToValue(filter: str):
    match filter:
        case "Practice":
            return 1
        case "Easy":
            return 2
        case "Medium":
            return 3
        case "Hard":
            return 4
        case _:
            return None
        

def main():
    global template, check

    with open("temps/templates/main.py", "r") as f:
        template = f.read()

    with open("temps/templates/check.py", "r") as f:
        check = f.read()

    page_count = math.ceil(grabPage()["currentCount"] / 20)

    scope, filters = get_range_and_checkboxes(page_count)
    filters = [filterToValue(filter) for filter in filters]

    threads: list[Thread] = []

    for i in range(scope[0], scope[1] + 1):
        page = grabPage(difficulty=filters, page=i)
        problems = page["problems"]
        if len(problems) == 0: break
        for problem in problems:
            thread = Thread(target=setupProblem, args=(problem,))
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()