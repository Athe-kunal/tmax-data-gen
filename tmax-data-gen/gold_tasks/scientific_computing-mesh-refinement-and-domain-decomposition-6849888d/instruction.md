As a data scientist, I am working on a project that involves fitting models to spatial data. I have a dataset of 2D coordinates located at `/home/user/spatial_data.csv` and I need to perform mesh refinement and domain decomposition on this data. The dataset contains `x,y` coordinates (comma-separated, no header) within the domain $X \in [0, 1]$ and $Y \in [0, 1]$. 

My task is to start with the domain $[0, 1] \times [0, 1]$ and create an initial $2 \times 2$ grid. Then, I need to refine the grid by recursively splitting cells into 4 equal sub-quadrants if a cell contains more than 50 points, up to a maximum depth of 3. 

For each leaf cell in the final mesh, I need to approximate its theoretical unnormalized mass using a 2D Gaussian distribution centered at $\mu_x=0.5, \mu_y=0.5$ with standard deviation $\sigma=0.2$. I also need to calculate the normalized theoretical probability for each cell and the empirical probability based on the number of points in each cell. 

Finally, I need to compute the Kullback-Leibler (KL) divergence from the theoretical probability to the empirical probability. The final result should be written to a JSON file at `/home/user/model_fit.json` with the following format:
```json
{
  "total_cells": <integer, total number of leaf cells in the final mesh>,
  "max_depth_reached": <integer, the maximum refinement depth actually reached>,
  "kl_divergence": <float, rounded to 4 decimal places>
}
```
To complete this task, I can install necessary Ubuntu packages using standard `apt` commands and write my Bash script in `/home/user/spatial_model.sh`. The script should compile and run to produce the final `/home/user/model_fit.json` file.

After completing the task, I need to create a log file at `/home/user/task_log.txt` with the following content:
"Task completed. Model fit results written to /home/user/model_fit.json."
