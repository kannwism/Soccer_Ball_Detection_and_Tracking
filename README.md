<p align="left" width="100%">
  <img height="100" src="img/topbar.png"> &nbsp; &nbsp; 
</p>

# 3D Vision Project: Soccer Ball Detection and Tracking
## Authors: Marian Kannwischer, Jason Corkill, Miks Ozols & Jannik Brun

## Quick Start 

tested on ubuntu 20.04, Needs Python 3.7! 

#### 1. Install required packages
```
pip3 install -r requirements.txt
```
to install the visualizer and data generator



#### 2. Install required packages for football simulator
```
sudo apt-get install git cmake build-essential libgl1-mesa-dev libsdl2-dev \
libsdl2-image-dev libsdl2-ttf-dev libsdl2-gfx-dev libboost-all-dev \
libdirectfb-dev libst-dev mesa-utils xvfb x11vnc libsdl-sge-dev python3-pip
```

#### 3. Installing from source

```
cd football
```


The last step is to build the environment:

```
pip3 install .
```
This command can run for a couple of minutes, as it compiles the C++ environment in the background.

#### 3. Generate Data
from the project root, this will generate a data set in a "football_data" folder in the projects root directory

```
cd src/
python3 datagen.py
```



## Instructions
### Dataset Generation
To generate a dataset navigate into the '/football' directory where there is a file called 'datagen.py'. 
The script in 'datagen.py', when run, will automatically generate a dataset in a folder contained in this repository's 
root folder called 'football_data'. 

Also, to be found in the '/football' directory are two .csv files, 'camera_positions.csv' and 'camera_rotation.csv'. In
these one can define the cameras for which data should be generated, this is done by automatically running the same 
deterministic football game in the simulator with these defined camera positions and rotations. 
The lines in these two files represent the same cameras position and rotation respectively. The rotations are to be
given in xyz Euler angles. Please assert that for each camera defined in 'camera_positions.csv' you also have a rotation
defined in 'camera_rotations.csv'. The origin for positions is in the center of the field. 

The 'datagen.py' script calls a function that generates all data automatically. Here you can set various parameters
for the dataset.

| Parameter               | Default                         | Explanation                                                                                                                                                                                                                                                                                        |
|-------------------------|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| run_name                | -                               | Name of the run, a directory with the data will be generated.                                                                                                                                                                                                                                      |
| cam_positions           | -                               | Nx3 array containing the positions of N different cameras. (read from the csv)                                                                                                                                                                                                                     |
| cam_rotations           | -                               | Nx3 array containing the rotation (xyz Euler angles) of N different cameras. (read from the csv)                                                                                                                                                                                                   |
| level                   | 'tests.11_vs_11 _deterministic' | What deterministic scenario should be used. Options can be found in football/gfootball/scenarios/test . IMPORTANT: if you want to use a scenario that does not have the ending '_deterministic', open the  scenario file and insure that the flag 'builder.config().deterministic' is set to True! |
| steps                   | 100                             | Amount of steps (frames) the simulation should make.                                                                                                                                                                                                                                               |
| render                  | True                            | If true, the pygame window will appear and render the game (slower). (Necessary for 'save_frames')                                                                                                                                                                                                 |
| save_frames             | True                            | If true, the frames of the game will be saved.                                                                                                                                                                                                                                                     |
| write_video             | False                           | If true, a video will be made from the frames. ('save_frames' need to be True)                                                                                                                                                                                                                     |
| use_red_dot             | False                           | If true, a red dot will be rendered on each frame to highlight the ball.                                                                                                                                                                                                                           |
| physics_steps_per_frame | 1                               | Changes the "frame rate", lower value means higher frame rate (not tested for values < 1) (only 1 will give perfectly accurate 2D pixel positions)                                                                                                                                                 |
| amount_cam_follow       | 0                               | Integer, amount of cameras that should follow the ball, starting from the first.                                                                                                                                                                                                                   |
| render_resolution_x     | 1280                            | Height of the rendered frame                                                                                                                                                                                                                                                                       |
| render_resolution_y     | 720                             | Width of the rendered frame                                                                                                                                                                                                                                                                        |
| set_fov                 | 24                              | Changes the field of view for all cameras.                                                                                                                                                                                                                                                         |

### Working with the Dataset
The easiest way to work with this data is to use our DataManager class. With it one can load in the data with 
ease and is given many getter and data modification methods to work with. The getter methods returns the data in a way 
that makes it easy to work with it in an efficient vectorized manner. An example of this is the 
datamanager.get_proj_mat_all() function which will return an MxNx3x4 array, containing projection Matrices of the shape 
3x4 , where M is the number of cameras and N is the amount of steps. Here the DataManager internally already calculated 
the projection matrix for you. Further the DataManager is able to add noise to the pixel coordinates, the intrinsic 
matrix, the extrinsic matrix and the projection matrix. 

Below is a table describing the most important functions that the Datamanger provides. There are more to be found in the 
DataManager class. Further one could easily add more for something like eg. Ball spin by following the format of the
other getter methods.

| Function                | Input                                                       | Output                                                                                                                                                                                                         |
|-------------------------|-------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| load                    | str, Name of the run                                        | Must be run first! Loads the runs data internally for the object. returns data, constants and dump file contents in Dictionaries                                                                               |
| get_proj_mat_all        | -                                                           | Returns an MxNx3x4 matrix containing projection Matrices of the shape 3x4 , where M is the number of cameras and N is the amount of steps.                                                                     |
| get_proj_mat_noise_all  | (float, intrinsic std), (float, extrinsic std) (int, seed)  | Same as get_proj_mat_all, but with added gaussian noise.                                                                                                                                                       |
| get_points_2d_all       | boolean, set_oob_nan                                        | Returns a MxNx2 matrix containing 2d pixel positions of the ball for each frame n and each camera m, if set_bool_nan is set to 'True' it will set the values to NAN where the ball is not in the cameras frame |
| get_points_2d_noise_all | (boolean, set_oob_nan) (float, std) (int, seed)             | Same as above, but with added gaussian noise                                                                                                                                                                   |
| get_oob_flags_all       | -                                                           | Returns a MxN matrix, containing boolean flags for M cameras and N time steps. If True, the ball is out of frame at that time ste                                                                              |
| get_points_3d           | -                                                           | Returns a Nx3 matrix, containing the 3d position of the ball at each time step n.                                                                                                                              |
| get_3d_player_positions | -                                                           | Returns a NxPx3 matrix containing the 3D positions of P players and N timesteps.                                                                                                                               |
| get_2d_player_position  | int, camera number                                          | Returns a NxPx3 matrix containing the 2D pixel positions of all P players at N timesteps.                                                                                                                      |

Explore_Dataset.py is an example file of how to work with the various classes provided as a pipeline. It can also be 
adapted to suit your needs. In it, you can see how to work with our ErrorMetrics class, our Triangulation functions and
our Visualizer.

## File Struture
- football/ contains a hard fork from https://github.com/google-research/football with major changes
- src/ contains the dataset generator, and the rest of the pipeline
  1. DataManager.py saves all data
  2. DatasetGenerator.py activates the football/ folder
  3. EstimationMetric.py consists several estimation metrics
  4. SoccerVisualizer.py to visualize football field and trajectory
  5. TrajectoryEstimation.py estimator for trajectory
  6. Explore_Dataset.py Example of Triangulation and visualization on dataset 'test_run2'
  7. camera_positions.csv contains camera position for datagen.py
  8. camera_orientation.csv contains camera orientation for datagen.py
  9. datagen.py to generate data. Entry Point
  10. field.png field used by visualizer
  11. hand_labeling.py tool to interpolate hand labeled data and also to go from video to frames
  12. noise_analysis.py noise vs multiple cameras based on dataset 'run_mari2'
  13. triangulate_handlabeled.py visualize the hand-labeled data
  14. triangulatepoints.py contains method to triangulate points based on camera parameters
  15. player_pos_visualization.py contains a script with which one can visualize the players on the filed with a red dot
- img/ general image for illustration and report
- data/ data used for report
  1. 
