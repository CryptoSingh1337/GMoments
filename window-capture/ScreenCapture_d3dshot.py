import d3dshot
import os
import time
from PIL import Image
import ffmpeg
from memory_profiler import profile


def validate_display_index(displays, index: int):
    if (index < 0 or index >= len(displays)):
        raise Exception('Invalid display')
    return True


def validate_baseDir(baseDir: str):
    return os.path.exists(baseDir)


def generate_list(start, end, interval):
    return list(range(start, end, interval))


class ScreenCapture:
    width: int = 0
    height: int = 0
    resolution = (0, 0)
    d3d_instance: object = None
    fps: int = 24
    baseDir: str = ''
    render_video: str = ''
    render_fps: int = 20
    frame_buffer_size: int = 360
    frame_indices: list = None
    frame_buffer: list = None

    def __init__(self, baseDir: str):
        self.d3d_instance = d3dshot.create(
            capture_output='numpy', frame_buffer_size=self.frame_buffer_size)
        self.refresh_resolution()
        if(validate_baseDir(baseDir)):
            self.baseDir = baseDir
        else:
            raise Exception('Invalid Base directory path!')
        self.render_video = 'render.mp4'
        self.frame_indices = generate_list(0, self.frame_buffer_size, 1)
        self.start_capture()

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
        self.d3d_instance.capture(target_fps=self.fps)

    def stop_capture(self):
        self.d3d_instance.stop()

    def get_frames_buffer(self):
        self.frame_buffer = self.d3d_instance.get_frame_stack(
            frame_indices=self.frame_indices, stack_dimension='first')

    @profile
    def save_buffer(self):
        self.get_frames_buffer()
        i = 0
        for image in self.frame_buffer:
            Image.fromarray(image).save(
                fp=f'{self.baseDir}/{i}.jpeg', format='jpeg')
            i += 1

    @profile
    def render_video(self):
        self.stop_capture()
        self.save_buffer()
        (
            ffmpeg
            .input(f'{self.baseDir}/%d.jpeg', framerate=self.render_fps)
            .output(f'{self.render_video}')
            .run()
        )
        self.d3d_instance._reset_frame_buffer()

    def get_screenshot(self):
        self.d3d_instance.screenshot_to_disk()


if __name__ == '__main__':
    start = time.time()
    sc = ScreenCapture('frames')
    # print(sc.get_displays())
    # sc.change_display(0)
    # print(sc.get_width, sc.get_height)
    time.sleep(20)
    sc.render_video()
    end = time.time()
    print(f"Time taken: {end - start}")
    print('done')
