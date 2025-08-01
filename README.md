# Luno Customer Analysis App

This repository contains the Luno Take Home Test (Customer Analysis) application built using Streamlit. The software developed provides tools for analysing customer trading activity through interactive tables and graphs as well as 
dataframe downloads for further investigation.

## Getting Started

Follow these step-by-step instructions to set up and run the application on your local machine.

### Prerequisites

- [Python](https://www.python.org/downloads/) (3.7 or higher)
- [Git](https://git-scm.com/downloads) (for cloning the repository)

### Installation

1. **Clone the repository**

   Open your terminal or command prompt and run the following command:

   ```
   git clone https://github.com/Rebel1124/Luno_THT.git
   ```

   Replace `username/repository-name` with the actual GitHub username and repository name.

2. **Navigate to the project directory**

   ```
   cd repository-name
   ```

   Replace `repository-name` with the name of the folder created by the clone operation.

3. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

   This command installs all the required Python libraries specified in the requirements.txt file.

### Running the Application

1. **Start the Streamlit application**

   ```
   streamlit run analysis.py
   ```

2. **Access the application**

   The application will automatically open in your default web browser. If it doesn't, you can access it at:
   
   ```
   http://localhost:8501
   ```
   
3. **Access the deployed application**

   You can also access the deployed version of this application at:
   
   ```
   https://lunotht-desi.streamlit.app/
   ```

## Application Structure

- **main.py**: The main application file that runs the Streamlit interface
- **plotlyGraphs.py**: Contains functions for creating Plotly graphs
- **./files/..**: Contains the 4 files received for use in the assignment
- **./assets/..**: Contains Luno image and lottie animation
- **.streamlit/config.toml**: Configuration file for the Streamlit theme and appearance

## Troubleshooting

- If you encounter any issues with dependencies, ensure that you have the correct version of Python installed and that all requirements are properly installed.
- If the application fails to start, check the terminal/command prompt for error messages.
- Make sure all the Python files (analysis.py, bondCalculator.py, bondDescritions.py, and tablesGraphs.py) are in the correct location within the project directory.

## Additional Information

- The application uses Plotly for interactive visualizations and Streamlit for the web interface.
- Custom styling is applied through the .streamlit/config.toml configuration file.