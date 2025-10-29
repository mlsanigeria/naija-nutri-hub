# 🧩 Contributing to Naija Nutri Hub

Welcome to the **Naija Nutri Hub** project repository for ML/AI Engineering and Backend, organized by the **Microsoft Learn Student Ambassadors (MLSA)** and **GitHub Campus Experts, Unilag** for **Hacktoberfest 2025!**

We’re excited to have you contribute and help improve this innovative, AI-powered food platform.  
Whether you’re fixing bugs, improving documentation, or adding features — every contribution matters. 🙌  



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

### 📁 Folder Descriptions & Example Contributions


| Folder | Description | Example Contribution |
|--------|--------------|----------------------|
| **auth/** | Handles authentication, OTP verification, and email services | Add SMS OTP support |
| **config/** | Database connections and app configuration | Add Redis caching for performance |
| **schemas/** | Pydantic models for request/response validation | Add schema for user dietary preferences |
| **src/** | Core AI/ML modules for food analysis and recommendations | Improve food classification accuracy |
| **experimentation/** | Jupyter notebooks for ML experiments | Create ingredient substitution notebook |
| **tests/** | Unit & integration tests | Add API integration test cases |

---

### ⚙️ Quick Start for Contributors

**3-Step Contribution Flow:**
1. **Claim** - Comment on an issue to get it assigned to you
2. **Implement** - Create a feature branch and develop your solution
3. **Submit** - Open a Pull Request with clear description and tests

**Running the Project Locally:**
```bash
# Start the FastAPI backend server
uvicorn main:app --reload
```

### **PR Checklist**

- [ ] Code follows project style and includes docstrings  
- [ ] Tests added/updated and all tests pass  
- [ ] Clear and descriptive commit messages  
- [ ] Issue number referenced (`Closes #<issue-number>`)  

## 🧩 How You Can Contribute

- Review the existing project code and open issues.  
- Pick an issue or propose a new improvement.  
- Work on your contribution, test it locally, and ensure it aligns with project goals.  
- Submit your PR with a detailed description and supporting screenshots if needed.  


## 🧰 Troubleshooting

| Problem | Solution |
|----------|-----------|
| `uvloop` install error (Windows) | Remove `uvloop` from `requirements.txt` |
| `bson` import error | Run `pip uninstall bson` → `pip install pymongo --upgrade` |
| Email not sending | Double-check your `.env` Mailtrap credentials |
| MongoDB not connecting | Ensure MongoDB service (`mongod`) is running locally |

## 🧾 General Contribution Guidelines

- Write clean, modular, and documented code.  
- Keep commit messages meaningful and concise.  
- Follow the repository’s code style and structure.  
- Respect other contributors and collaborate politely.  
- Ask questions freely — maintainers are happy to help! 


## 📦 Resources

- [How to Do Your First Pull Request](https://youtu.be/nkuYH40cjo4?si=Cb6U2EKVR_Ns4RLw)  
- [Fundamentals of Azure OpenAI Service](https://learn.microsoft.com/en-us/training/modules/explore-azure-openai/)  
- [Azure OpenAI Python SDK Setup](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/supported-languages)  
- [Azure OpenAI Models: Deployment](https://learn.microsoft.com/azure/ai-services/openai/how-to/working-with-models)  
- [Develop Generative AI Solutions with Azure OpenAI Service](https://learn.microsoft.com/en-us/training/paths/develop-ai-solutions-azure-openai/)  
- [Azure Custom Vision Documentation](https://learn.microsoft.com/en-us/azure/ai-services/custom-vision-service/quickstarts/image-classification)  
- [Azure Custom Vision Video Tutorial](https://www.youtube.com/watch?v=PSHZJC1VvvI)  
- [FastAPI Docs](https://fastapi.tiangolo.com/tutorial/)

---

## 📊 Datasets & APIs

- [Nigerian Food Dataset - Images (Kaggle)](https://www.kaggle.com/datasets/elinteerie/nigeria-food-ai-dataset/data)  
- [Nigerian Food Description Dataset (Kaggle)](https://www.kaggle.com/datasets/franklycypher/nigerian-foods)  
- [The MealDB](https://www.themealdb.com/) — API for recipes and ingredients  
- [Spoonacular API](https://spoonacular.com/food-api) — API for recipes, ingredients & nutrition info  

---

## 💬 Community & Support

Need help? We’ve got you covered!  

- 💬 [Join our WhatsApp Community](WHATSAPP_COMMUNITIES.md)  
- 🐦 Follow [@mlsanigeria](https://twitter.com/mlsanigeria) on Twitter  

---



## 🤝 Code of Conduct

By contributing, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).  
We’re committed to an inclusive, welcoming community for everyone. 🌍  

---

## 🎉 Final Words

Thank you for contributing to **Naija Nutri Hub!**  
Your efforts help make open source more accessible and inspiring.  

**Happy hacking! We can't wait to see your amazing contributions!**

**✨ Together, let’s build something meaningful — one PR at a time! 🚀**



---

