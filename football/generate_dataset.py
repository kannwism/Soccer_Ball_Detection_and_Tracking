# coding=utf-8
# Copyright 2019 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import logging

from gfootball.env import config
from gfootball.env import football_env
import numpy as np
from scipy.spatial.transform import Rotation as R

from DataManager import DataManager

def generate_dataset(run_name, cam_positions, cam_rotations, render=True, save_frames=False):
    """
    Automatically generate a data set for one game with multiple camera views

    Parameters
    ----------
    run_name :  name of the run, a directory with the data will be generated
    cam_positions : Nx3 array containing the positions of N different cameras
    cam_rotations: Nx3 array containing the rotation of N different cameras
    render : if true the pygame window will appear and render the game (slower)
    save_frames : if true the frames of the game will be saved

    Returns
    -------
    None.
    """
    N = cam_positions.shape[0]
    for i in range(N):
        generate_camera(run_name=run_name, cam_pos=cam_positions[i,:], cam_rot=cam_rotations[i,:], cam_nr= i,
                        render=render, save_frames=save_frames)

def procOut(cout, size):
    """Method for post-processing the lists output from the wrapper to numpy matrices

    Input:
      -cout: list (output from the wrapper) to-be processed, n x m
      -size [a, b]: a list- or tuple-like indiciating the desired shape of the output. a*b = n*m

    Output:
      - a x b np.matrix with reordered elements of cout in the desired format"""
    size = (size[0], size[1])
    return np.matrix(np.reshape(np.array(cout), size))


def generate_camera(run_name, cam_nr=0, steps=100, cam_pos=np.array([0, 0, 80]), cam_rot=np.array([0, 0, 0]),
                    level='tests.11_vs_11_deterministic', render=True, save_frames=False):
    players = ''

    assert not (any(['agent' in player for player in players])
                ), ('Player type \'agent\' can not be used with play_game.')
    cfg = config.Config({
        'action_set': 'default',
        'dump_full_episodes': True,
        'players': players,
        'real_time': True,
    })
    if level:
        cfg['level'] = level
    env = football_env.FootballEnv(cfg)
    print('hi')
    if render:
        env.render()
    env.reset()
    data_manager = DataManager()


    pos = 0
    try:
        for time in range(steps):
            r = R.from_euler('xyz', cam_rot, degrees=True)
            carot_quat = r.as_quat()
            pos += 0.1
            env._env._env.set_camera_node_orientation(-0.0, -0.0, -0.0, 1.0)
            env._env._env.set_camera_node_position(float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2]))
            env._env._env.set_camera_orientation(carot_quat[0], carot_quat[1], carot_quat[2], carot_quat[3])
            env._env._env.set_camera_fov(24)

            _, _, done, _ = env.step([])

            RT0 = procOut(env._env._env.get_extrinsics_matrix(), [3, 4])
            K0 = procOut(env._env._env.get_intrinsics_matrix(), [3, 3])
            ball3d = procOut(env._env._env.get_3d_ball_position(), [3, 1])
            ball3dh = np.transpose(np.matrix(np.append(np.array(ball3d), 1)))
            camPos0 = procOut(env._env._env.get_camera_node_position(), [3, 1])
            camOr0 = procOut(env._env._env.get_camera_orientation(), [1, 4])
            CNO0 = procOut(env._env._env.get_camera_node_orientation(), [1, 4])
            fov = env._env._env.get_camera_fov()
            pixcoord0 = procOut(env._env._env.get_pixel_coordinates(), [2, 1])

            # print("CNO: ", env._env._env.get_camera_node_orientation())
            # print("CNP1: ", env._env._env.get_camera_node_position())
            # print("CO: ", env._env._env.get_camera_orientation())
            # print("CFOV: ", env._env._env.get_camera_fov())
            # print('RT', RT)
            #print("PIX2D 1: ", env._env._env.get_pixel_coordinates())
            # print('Ball 3D: ', ball3d)
            # print('----------------------------')
            data_manager.set_fov(fov)
            data_manager.set_intrinsic_mat(K0)
            data_manager.set_3d_ball_pos(time=time, pos=ball3d)
            data_manager.set_cam(time=time,
                                 extrinsic_mat=RT0,
                                 cam_node_pos=camPos0,
                                 cam_node_orientation=CNO0,
                                 pix_ball_pos=pixcoord0,
                                 cam_orientation=camOr0, cam=0)
            if save_frames:
                data_manager.write_frame(time=time, frame=env.observation()['frame'], cam=0, dirname=run_name)

            time += 1

            if done:
                env.reset()

        # end for
        data_manager.write_data(run_name, 'cam_' + str(cam_nr) + '_data.p')
        data_manager.write_constants(run_name, 'cam_' + str(cam_nr) + '_constants.p')

    except KeyboardInterrupt:
        logging.warning('Game stopped, writing dump...')
        env.write_dump('shutdown')
        exit(1)
