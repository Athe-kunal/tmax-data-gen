As a data analyst, I have a CSV file containing information about various features of a dataset. My task is to perform cross-validation and hyperparameter tuning on a regression model to predict a target variable. 

I have two CSV files: `/home/user/data/train.csv` and `/home/user/data/test.csv`. The training data contains two columns: `x` and `y`, where `x` is the feature and `y` is the target variable. The test data contains only the `x` column.

I want to implement a regression model in C++ using a linear regression algorithm with polynomial features of degrees 1, 2, and 3. I also want to perform k-fold cross-validation with 5 folds and tune the regularization parameter `alpha` for the linear regression model.

My goal is to find the best combination of polynomial degree and `alpha` that results in the lowest mean squared error (MSE) on the training data. I want to save the cross-validation results to `/home/user/experiments/cv_results.csv`, which should have a header `degree,alpha,mean_mse` and contain the MSE for each combination of polynomial degree and `alpha`. The results should be sorted in ascending order of MSE.

After finding the best hyperparameters, I want to retrain the model on the entire training dataset and use it to make predictions on the test dataset. I want to save the predictions to `/home/user/experiments/predictions.txt`, with one prediction per line, formatted to 4 decimal places.

To complete this task, I need to install the necessary packages, including the C++ compiler and any required libraries. I also need to create the necessary directories and files, including the `experiments` directory and the `cv_results.csv` and `predictions.txt` files.

Please help me complete this task by performing the necessary steps, including installing packages, creating directories and files, and implementing the regression model with cross-validation and hyperparameter tuning.
