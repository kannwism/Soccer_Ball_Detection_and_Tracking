from pathlib import Path

import numpy as np
import pickle
from PIL import Image
import cv2
import os

import csv


class DataManager:
    def __init__(self):
        self.constants = {}  # dict
        self.data = [{}]  # list of dicts
        self.frames = {}  # dict of lists

    def set_extrinsic_mat(self, time: int, mat: np.ndarray, cam=0):
        if mat.shape != (3, 4) and mat.shape != (4, 4):
            raise ValueError('Wrong Dimension. Extrinsic matrix has dimension 3x4')
        self._check_time(time)
        self.data[time]['cam' + str(cam) + '_extrinsic_mat'] = mat

    def set_intrinsic_mat(self, mat: np.ndarray):
        if mat.shape != (3, 3) and mat.shape != (3, 4):
            raise ValueError('Wrong Dimension. Extrinsic matrix has dimension 3x3')
        self.constants['intrinsic_mat'] = mat

    def set_fov(self, fov: float):
        self.constants['fov'] = fov

    def set_amount_of_cams(self, cam):
        self.constants['amount_of_cams'] = cam + 1

    def set_3d_ball_pos(self, time, pos):
        self._check_time(time)
        self.data[time]['3d_ball_pos'] = pos

    def _check_time(self, time):
        if len(self.data) == time:
            self.data.append({})
        if len(self.data) < time:
            raise IndexError('This time step does not exist yet. Please populate in order.')

    def set_pix_ball_pos(self, time, pos, cam=0):
        self._check_time(time)
        self.data[time]['cam' + str(cam) + '_pix_ball_pos'] = pos

    def set_cam_node_orientation(self, time, orientation, cam=0):
        self._check_time(time)
        self.data[time]['cam' + str(cam) + '_node_orientation'] = orientation

    def set_cam_node_pos(self, time, pos, cam=0):
        self._check_time(time)
        self.data[time]['cam' + str(cam) + '_node_pos'] = pos

    def set_cam_orientation(self, time, orientation, cam=0):
        self._check_time(time)
        self.data[time]['cam' + str(cam) + '_orientation'] = orientation

    def set_frame(self, time, frame, cam):
        key = 'cam' + str(cam)
        if not key in self.frames.keys():
            self.frames[key] = [frame]
        elif len(self.frames[key]) == time:
            self.frames[key].append(frame)
        elif len(self.frames[key]) > time:
            self.frames[key][time] = frame
        else:
            raise IndexError('Parameter time out of bounds. Please populate in order.')

    def set_cam(self, time, extrinsic_mat, cam_node_pos, cam_node_orientation, cam_orientation, pix_ball_pos, cam):
        self.set_extrinsic_mat(time, extrinsic_mat, cam)
        self.set_cam_node_pos(time, cam_node_pos, cam)
        self.set_cam_node_orientation(time, cam_node_orientation, cam)
        self.set_cam_orientation(time, cam_orientation, cam)
        self.set_pix_ball_pos(time, pix_ball_pos, cam)
        self.set_amount_of_cams(cam)

    def write_data(self, run_name):
        filename = run_name + '_data.p'
        path = Path.cwd().parent / 'football_data' / run_name / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self.data, f)

    def write_constants(self, run_name):
        filename = run_name + '_constants.p'
        path = Path.cwd().parent / 'football_data' / run_name / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self.constants, f)

    def write_frames(self, dirname):
        path = Path.cwd().parent / 'football_data' / dirname / 'frames'
        path.mkdirs(parents=True, exist_ok=True)
        for key in self.frames.keys():
            for i, frame in enumerate(self.frames[key]):
                _file = key + '_' + str(i).zfill(5) + '.png'
                img = Image.fromarray(frame.astype('uint8'))
                img.save(str(path / _file), format='png')
                img.close()

    def write_frame(self, time, frame, cam, run_name):
        cam_dir = 'cam_' + str(cam)
        path = Path.cwd().parent / 'football_data' / run_name / 'frames' / cam_dir
        path.mkdir(parents=True, exist_ok=True)
        _file = 'cam' + str(cam) + '_' + str(time).zfill(5) + '.png'
        img = Image.fromarray(frame.astype('uint8'))
        img.save(str(path / _file), format='png')
        img.close()

    def load_data(self, run_name):
        filename = run_name + '_data.p'
        path = Path.cwd().parent / 'football_data' / run_name / filename
        with open(path, 'rb') as f:
            self.data = pickle.load(f)
        return self.data

    def write_csv_proj(self, run_name):
        """ generate a csv file in the camera folder"""
        self.load_data(run_name)
        self.load_constants(run_name)


        for cam in range(self.constants['amount_of_cams']):
            cam_dir = 'cam_' + str(cam)
            filename = 'xy.csv'
            path = Path.cwd().parent / 'football_data' / run_name / 'frames' / cam_dir / filename
            with open(path, mode='w') as xy_file:
                xy_writer = csv.writer(xy_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                xy_writer.writerows(self.get_points_2d(cam))


        

    def load_constants(self, run_name):
        filename = run_name + '_constants.p'
        path = Path.cwd().parent / 'football_data' / run_name / filename
        with open(path, 'rb') as f:
            self.constants = pickle.load(f)
        return self.constants

    def load(self, run_name):
        return self.load_data(run_name), self.load_constants(run_name)

    def load_frame(self, time, dirname, cam):
        cam_dir = 'cam_' + str(cam)
        path = Path.cwd().parent / 'football_data' / dirname / 'frames' / cam_dir
        file = 'cam' + str(cam) + '_' + str(time).zfill(5) + '.png'
        with Image.open(str(path / file)) as img:
            return np.array(img)

    def write_video(self, dirname, cam):
        cam_dir = 'cam_' + str(cam)
        path = Path.cwd().parent / 'football_data' / dirname / 'frames' / cam_dir
        dir_list = sorted(os.listdir(path))
        images = [img for img in dir_list if img.endswith(".png")]
        frame = cv2.imread(os.path.join(path, images[0]))
        height, width, layers = frame.shape
        video_name = 'cam_' + str(cam) + '_video.mp4'
        video_path = Path.cwd().parent / 'football_data' / dirname / 'frames' / video_name
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        video = cv2.VideoWriter(str(video_path), fourcc, 24, (width, height))

        for image in images:
            os_path = os.path.join(path, image)
            video.write(cv2.imread(os.path.join(path, image)))

        cv2.destroyAllWindows()
        video.release()

    def get_points_2d(self, cam_num):
        return np.array([d['cam' + str(cam_num) + '_pix_ball_pos'] for d in self.data]).reshape(-1, 2)

    def get_ext_mat(self, cam_num):
        return np.array([d['cam' + str(cam_num) + '_extrinsic_mat'] for d in self.data])

    def get_points_3d(self):
        return np.array([d['3d_ball_pos'] for d in self.data]).reshape(-1, 3)

    def get_proj_mat_all(self):
        k = np.array(self.constants['intrinsic_mat'])
        return np.array([(k @ self.get_ext_mat(cam)) for cam in range(self.constants['amount_of_cams'])])

    def get_points_2d_all(self):
        return np.array([self.get_points_2d(cam) for cam in range(self.constants['amount_of_cams'])])
