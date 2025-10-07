## 🚀 **Getting Started with Azure for Food Classifier**
Our project provides the option to use Azure Custom Vision for training and testing food classification models. To make it easy for contributors without azure credits, we’re providing Azure subscription codes to get you started.

Follow the guide below to set up your **Azure account, create resources, and retrieve the API keys** you’ll need.

### **📝 Step 1: Activate your Azure Student Subscription**
If you have a student email (e.g., your university-assigned email address), you can sign up for the [Azure Student Subscription](https://azure.microsoft.com/en-us/free/students?msockid=3bc94b5a334e671e3148589032536628). 
This gives you free credits to explore the Azure portal and use services like Custom Vision.

**Disclaimer:** if you don’t have access to azure student subscription or your previous subscription has expired, 
you can request an Azure subscription code from us to get free credits by filling out the [Azure Access Request Form](https://forms.office.com/r/B5fAYrZyB5). 

*Please fill in all required details carefully.* 

### **💳 Step 2: Redeem Your Azure Subscription Code (Optional)**
Once your request is approved, you will receive a **link** and **a verification code**.
1. Navigate to the link provided.

2. Sign up with either your **personal email** or **school email**.

3. During the signup process, you’ll see a field to enter your verification code — paste it here.

4. Complete the signup.

5. You’ll automatically be redirected to the Billing section of your new Azure account.

6. You should now see $100 in free credits available.🎉

### **⚙️ Step 3: Create Your Custom Vision Resources**
With your account ready, the next step is to create the necessary resources.
For Azure Custom Vision, you need two resources:
   - Training Resource → for uploading images and training models.
   - Prediction Resource → for publishing your trained model and running predictions.

**Steps to create the resources:**
1. Go to the Azure Portal.

2. Click Create a Resource → search for Custom Vision.

3. Select Custom Vision → click Create.

4. Fill in the required fields:

    - Resource Group: Create a new one or use an existing one.
    - Region: Select **Germany West Central.**
    - Resource Name: Example → `foodimageclassifier`
    - Resource Type: This will default to Both (Training + Prediction).

5. Leave all other settings as they are.

6. Click Review + Create.

**If successful, you’ll be redirected to the deployed resource page.**

### **🔑 Step 4: Get Your API Keys and Endpoints**
Once the resource is deployed:
1. Open the Resource Group → select the Custom Vision resource you created.

2. In the left tab, click **Keys and Endpoints** under **Resource Management** tab.

3. Copy the following values:
      - Training Key as Key 1
      
      - Prediction Key as Key 2
      
      - Endpoint as API Endpoint
      
      - Prediction Resource ID - You can find the prediction resource ID on the prediction resource's **Properties** tab
         under the **Resource Management** tab , listed as Resource ID.
  

  You’ll use these values to
  
  - Train and test models programmatically from your local environment.
    To learn more about using the REST API for Custom Vision, check out: [Azure Custom Vision REST API Docs](https://learn.microsoft.com/en-us/azure/ai-services/Custom-Vision-Service/quickstarts/image-classification?tabs=windows%2Cvisual-studio&pivots=programming-language-python).
  - Alternatively, you can use the Azure Custom Vision Studio UI to upload, tag, and train images directly in the browser: [Custom Vision Portal](https://go.microsoft.com/fwlink/?linkid=2103841).
  

### **🎥 Step 5: Watch the Walkthrough Video**
For additional guidance, watch this video tutorial on how to create Azure resources and how to navigate azure custom vision portal
[Video Tutorial](https://youtu.be/PSHZJC1VvvI?si=xfaaKdwvKxEuzO8H)

### **✅ You’re Ready!**
Once you’ve completed the steps above, you’ll be able to:
 - Train models using Azure Custom Vision (via Studio UI or REST API).

 - Publish models for prediction.

 - Integrate with our backend to classify food images.


**🙌 Thank you for contributing and making our project better! Happy Hacking!**
