# Contributing to the Hacktoberfest Repository

Welcome to the **Naija Nutri Hub** project repository for ML/AI Engineering and Backend, organized by the Microsoft Learn Student Ambassadors and GitHub Campus Experts, Unilag for Hacktoberfest 2025! We're excited to have you contribute and improve this innovative project.

## How to Install Dependencies and Work on the Project Locally

1. **Clone the Repository:**

   From your terminal, clone your forked repository and name it `naija-nutri-hub`.

   ```bash
   # Replace {user_name} with your GitHub username
   git clone https://github.com/{user_name}/naija-nutri-hub.git
   ```

2. **Create a Branch for Your Contribution:**

   Before making any changes, create a new branch. This keeps the `main` branch clean and makes it easier to review contributions.
   Use a descriptive name for your branch based on the type of contribution:
   ```bash
   # General format
   git checkout -b <branch-name>
   ```
   **Examples:**
   For documentation updates:
   ```bash
   git checkout -b docs/update-contributing
   ```
   For a new feature:

   ```bash
   git checkout -b feature/recipe-api
   ```
   For a bug fix:
   ```bash
   git checkout -b fix/login-bug
   ```

3. **Set Up Virtual Environment:**

   Create a virtual environment named `naija-nutri-hub`.

   ```bash
   # Windows
   python -m venv naija-nutri-hub

   # macOS or Linux
   python3 -m venv naija-nutri-hub
   ```

   Activate the virtual environment:

   ```bash
   # Windows
   naija-nutri-hub\Scripts\activate

   # macOS or Linux
   source naija-nutri-hub/bin/activate
   ```

   Install necessary dependencies:

   ```bash
   cd naija-nutri-hub
   pip install -r requirements.txt
   ```

   Add the virtual environment to Jupyter Kernel if necessary:

   ```bash
   python -m ipykernel install --user --name=naija-nutri-hub
   ```
   
4. **Work on the Project:**

   - This repository is specifically for the **Naija Nutri Hub** project (ML/AI Engineering + Backend). Explore the project structure and check the **Issues** tab for tasks or bugs that you can address. 
   - You are encouraged to review the current implementation and contribute new features or improvements.

5. **Commit and Push Your Changes:**

   Once your contributions are ready, commit your changes and push them to your forked repository.

   ```bash
   git add .
   git commit -m "{COMMIT_MESSAGE}"
   git push
   ```

6. **Submit a Pull Request:**

   After pushing your changes, submit a pull request to merge them into the main repository. Make sure to include a clear and concise description of what your contribution entails.

## Project Structure

### Directory Tree
```
naija-nutri-hub/
├── main.py                    # FastAPI backend server entry point
├── requirements.txt           # Python dependencies
├── README.md                 # Project overview and setup guide
├── .env.example              # Environment variables template
├── auth/                     # Authentication and email services
├── config/                   # Database and app configuration
├── schemas/                  # Data models and validation schemas
├── src/                      # Core AI/ML features and tools
│   ├── food-classifier/      # Food image classification module
│   ├── nutritional-facts/    # Nutrition analysis module
│   ├── purchase-location/    # Store/market finder module
│   └── recipe-generation/    # Recipe creation module
├── experimentation/          # Jupyter notebooks for R&D
├── tests/                    # Unit tests and test utilities
└── naija-nutri-hub/         # Virtual environment (auto-generated)
```

### Folder Descriptions & Example Contributions

- **`auth/`** - Handles user authentication, OTP verification, and email services  
  *Example: Add SMS OTP option alongside email verification*

- **`config/`** - Database connections and application configuration  
  *Example: Add Redis caching configuration for better performance*

- **`schemas/`** - Pydantic models for API request/response validation  
  *Example: Create new schema for user dietary preferences*

- **`src/`** - Core AI/ML modules for food analysis and recommendations  
  *Example: Improve food classification accuracy or add new cuisine types*

- **`experimentation/`** - Research notebooks for testing new ML approaches  
  *Example: Create notebook exploring ingredient substitution algorithms*

- **`tests/`** - Automated tests ensuring code quality and functionality  
  *Example: Add integration tests for the recipe generation API*

### Quick Start for Contributors

**3-Step Contribution Flow:**
1. **Claim** - Comment on an issue to get it assigned to you
2. **Implement** - Create a feature branch and develop your solution
3. **Submit** - Open a Pull Request with clear description and tests

**Running the Project Locally:**
```bash
# Start the FastAPI backend server
uvicorn main:app --reload
```

**PR Checklist:**
- [ ] Code follows project style and includes docstrings
- [ ] Tests added/updated and all tests pass
- [ ] Clear commit messages and PR description provided

## How You Can Contribute:

1. Review the existing project code and issues to understand the functionality.
2. Find an open issue that matches your skills or propose a new feature.
3. Work on your contribution, test it thoroughly, and make sure it aligns with the project goals.
4. Submit your pull request with a clear explanation of your contribution.

## ✔️ General Contribution Guidelines

- Follow best practices for coding, including writing clean and well-documented code.
- Provide meaningful commit messages and detailed pull request descriptions.
- Respectfully collaborate and communicate with other contributors.
- Feel free to ask questions or seek guidance from project maintainers if needed.

**Happy hacking! We can't wait to see your amazing contributions!**

---

## 🔗 Links to Resources

1. [How to Do Your First Pull Request](https://youtu.be/nkuYH40cjo4?si=Cb6U2EKVR_Ns4RLw)
2. [Fundamentals of Azure OpenAI Service](https://learn.microsoft.com/en-us/training/modules/explore-azure-openai/?wt.mc_id=studentamb_217190)
3. [Azure OpenAI Python SDK Setup](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/supported-languages?tabs=dotnet-secure%2Csecure%2Cpython-key%2Ccommand&pivots=programming-language-python?wt.mc_id=studentamb_217190)
4. [Azure OpenAI Models: Deployment](https://learn.microsoft.com/azure/ai-services/openai/how-to/working-with-models?tabs=powershell?wt.mc_id=studentamb_217190)
5. [Develop Generative AI solutions with Azure OpenAI Service](https://learn.microsoft.com/en-us/training/paths/develop-ai-solutions-azure-openai/?wt.mc_id=studentamb_217190)
6. [Azure Custom Vision Documentation](https://learn.microsoft.com/en-us/azure/ai-services/custom-vision-service/quickstarts/image-classification?tabs=windows%2Cvisual-studio&pivots=programming-language-python).
7. [Azure Custom Vision Video Tutorial](https://www.youtube.com/watch?v=PSHZJC1VvvI)
8. [FastAPI Docs](https://fastapi.tiangolo.com/tutorial/)

## 📊 Datasets/APIs
1. [Nigerian Food Dataset - Images (Kaggle)](https://www.kaggle.com/datasets/elinteerie/nigeria-food-ai-dataset/data)
2. [Nigerian Food Description Dataset (Kaggle)](https://www.kaggle.com/datasets/franklycypher/nigerian-foods)
3. [The MealDB](https://www.themealdb.com/) - provides API access to recipes and ingredients that could power the recipe feature of the solution.
4. [Spoonacular API](https://spoonacular.com/food-api) - a food and recipe API that provides access to a vast database of recipes, ingredients, and nutritional information. It can be used to retrieve structured and accurate data to support the recipe generation, and nutritional facts features of this project.
