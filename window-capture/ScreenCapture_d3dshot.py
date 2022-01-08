import sys
import os
import time
import d3dshot
import keyboard
from PIL import Image
import ffmpeg

"""
returns the platform.
Possible values:
    Windows -> win32
"""


def get_operating_system():
    return sys.platform


"""
returns the path of the temporary directory for a specific platform.
"""


def get_parent_dir():
    tempDir = ''
    platform = get_operating_system()
    if (platform.startswith('win32')):
        tempDir = os.environ.get('TMP')
    else:
        raise Exception('OS not supported')
    return tempDir


"""
creates the directory for frames and window-capture in the temporary directory.
"""


def make_directoy(parent: str, directory_name: str):
    path = os.path.join(parent, directory_name)
    if (not os.path.isdir(path)):
        os.mkdir(path)


"""
Initialize the setup for directories.
"""


def setup_environment():
    tempDir = get_parent_dir()
    make_directoy(tempDir, 'window-capture')
    make_directoy(os.path.join(tempDir, 'window-capture'), 'frames')


"""
Check if the display adapter with the corresponding index is valid or not.
"""


def validate_display_index(displays, index: int):
    if (index < 0 or index >= len(displays)):
        raise Exception('Invalid display')
    return True


"""
Generate a list from 0 to 360 (in a 15 sec. video, there will be only 360 frames at 24 fps).
"""


def generate_list(start, end, interval):
    return list(range(start, end, interval))


class ScreenCapture:
    width: int = 0
    height: int = 0
    resolution = (0, 0)
    d3d_instance: object = None
    fps: int = 24
    working_dir: str = ''
    render_frames_dir: str = ''
    render_video_name: str = ''
    render_fps: int = 15
    frame_buffer_size: int = 360
    frame_indices: list = None
    frame_buffer: list = None
    key_pressed: bool = False
    timer: object = None

    def __init__(self):
        self.d3d_instance = d3dshot.create(
            capture_output='numpy', frame_buffer_size=self.frame_buffer_size)
        self.refresh_resolution()
        self.working_dir = get_parent_dir()
        self.working_dir = os.path.join(self.working_dir, 'window-capture')
        self.render_frames_dir = os.path.join(self.working_dir, 'frames')
        setup_environment()
        self.render_video_name = 'render.mp4'
        self.frame_indices = generate_list(0, self.frame_buffer_size, 1)

    @property
    def get_width(self):
        return self.width

    @property
    def get_height(self):
        return self.height

    def get_displays(self):
        return self.d3d_instance.displays

    def change_display(self, index: int):
        if(validate_display_index(self.get_displays(), index)):
            self.d3d_instance.display = self.get_displays()[index]
            self.refresh_resolution()
            print(
                f'Display changed to {self.d3d_instance.display.name}')

    def refresh_resolution(self):
        self.width, self.height = self.d3d_instance.display.resolution
        self.resolution = (self.width, self.height)

    def start_capture(self):
        print("Start capturing...")
        self.d3d_instance.capture(target_fps=self.fps)

    def stop_capture(self):
        print("Stop capturing...")
        self.d3d_instance.stop()

    def get_frames_buffer(self):
        """
        Returns a stack from the frame buffer which is based on deque.
        Check <https://github.com/SerpentAI/D3DShot#tldr-quick-code-samples>
        """
        self.frame_buffer = self.d3d_instance.get_frame_stack(
            frame_indices=self.frame_indices, stack_dimension='first')
        # Here we are reversing the stack because the last frame will be on the top.
        # So that our video will get render in progressive order.
        self.frame_buffer = self.frame_buffer[::-1]

    def save_buffer(self):
        self.get_frames_buffer()
        i = 0
        for image in self.frame_buffer:
            Image.fromarray(image).save(
                fp=f'{self.render_frames_dir}/{i}.jpeg', format='jpeg')
            i += 1

    def render_video(self):
        if (not self.key_pressed):
            print('Rendering video...')
            self.stop_capture()
            self.lockKeyPress()
            start = time.time()
            self.save_buffer()
            stream = ffmpeg.input(
                f'{self.render_frames_dir}/%d.jpeg', framerate=self.render_fps)
            stream = ffmpeg.output(stream,
                                   f'{self.working_dir}/{self.render_video_name}')
            # overwrite_output renders the video with -y option so that it will not asks
            # user to overwrite the already existing video with the same name.
            stream = ffmpeg.overwrite_output(stream)
            ffmpeg.run(stream)
            end = time.time()
            self.d3d_instance._reset_frame_buffer()
            print(f'Time taken: {end - start}')
            self.releaseKeyPress()
        else:
            print('Video is being rendered...')

    def get_frame_size(self):
        frame = self.d3d_instance.get_latest_frame()
        r, c, n = frame.shape
        # Since frame contains the height * width * 3 dimension matrix
        # and each of cell is numpy.uint8 which is of 1 byte in size
        print(f'{(r * c * n) / 1000000} MB')

    def get_screenshot(self):
        self.d3d_instance.screenshot_to_disk()

    def lockKeyPress(self):
        self.key_pressed = True

    def releaseKeyPress(self):
        self.key_pressed = False


if __name__ == "__main__":
    print("GMoments started.....")
    sc = ScreenCapture()
    keyboard.add_hotkey("alt + 1", sc.start_capture)
    keyboard.add_hotkey("alt + 2", sc.render_video)
    keyboard.add_hotkey("alt + 3", sc.get_frame_size)
    keyboard.wait("alt + 4")
