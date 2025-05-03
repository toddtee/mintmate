# 🧩 Mintmate

**Mintmate** is a modular Python utility designed to streamline the process of generating and managing chess puzzles. It automates tasks such as puzzle extraction, screenshot capturing, and Excel report generation, making it an invaluable tool for chess enthusiasts and educators.

---

## 🚀 Features

* **Puzzle Extraction**: Efficiently fetches puzzles from Lichess or other sources.
* **Screenshot Capturing**: Automatically captures visual representations of puzzles.
* **Excel Report Generation**: Compiles puzzles into well-structured Excel sheets for easy sharing and analysis.
* **Configuration Management**: Utilizes `config.toml` for customizable settings.

---

## 🛠️ Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/toddtee/mintmate.git
   cd mintmate
   ```

2. **Create a Virtual Environment**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Usage

1. **Configure Settings**:

   Edit the `config.toml` file to specify your preferences, such as puzzle sources, output directories, and other parameters.

2. **Run the Main Script**:

   ```bash
   python src/mintmate/main.py
   ```

   This will initiate the puzzle extraction, screenshot capturing, and Excel report generation processes based on your configurations.

---

## 📁 Project Structure

```
mintmate/
├── config.toml               # Configuration file
├── requirements.txt          # Python dependencies
├── src/
│   └── mintmate/
│       ├── __init__.py
│       ├── config_loader.py  # Handles configuration loading
│       ├── excel_writer.py   # Manages Excel report generation
│       ├── main.py           # Entry point of the application
│       ├── puzzle_utils.py   # Utilities for puzzle processing
│       └── screenshotter.py  # Handles screenshot capturing
```

---

## 🧹 .gitignore Highlights

The `.gitignore` file has been updated to exclude:

* **Virtual Environments**: `.venv/`, `venv/`, `env/`
* **IDE Configurations**: `.vscode/`
* **Generated Files**: `puzzles/` directory containing screenshots and Excel files
* **System Files**: `.DS_Store`

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

For more information and updates, visit the [Mintmate GitHub Repository](https://github.com/toddtee/mintmate).
