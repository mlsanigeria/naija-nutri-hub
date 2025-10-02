# Contributing to the Hacktoberfest Repository

Welcome to the **Naija Nutri Hub** project repository for ML/AI Engineering and Backend, organized by the Microsoft Learn Student Ambassadors and GitHub Campus Experts, Unilag for Hacktoberfest 2025! We're excited to have you contribute and improve this innovative project.

## How to Install Dependencies and Work on the Project Locally

1. **Clone the Repository:**

   From your terminal, clone your forked repository and name it `naija-nutri-hub`.

   ```bash
   # Replace {user_name} with your GitHub username
   git clone https://github.com/{user_name}/naija-nutri-hub.git
   ```

2. **Set Up Virtual Environment:**

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

3. **Work on the Project:**

   - This repository is specifically for the **Naija Nutri Hub** project (ML/AI Engineering + Backend). Explore the project structure and check the **Issues** tab for tasks or bugs that you can address. 
   - You are encouraged to review the current implementation and contribute new features or improvements.

4. **Commit and Push Your Changes:**

   Once your contributions are ready, commit your changes and push them to your forked repository.

   ```bash
   git add .
   git commit -m "{COMMIT_MESSAGE}"
   git push
   ```

5. **Submit a Pull Request:**

   After pushing your changes, submit a pull request to merge them into the main repository. Make sure to include a clear and concise description of what your contribution entails.

## Project Structure:


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
