import os.path
import sys
import pygame
import time
import re
import random
import cv2

WINDOW_WIDTH = 600

FLOW_SPEED = 600
NOTE_COLOR = {0: 'black', 1: 'red', 2: 'white', 3: 'blue', 4: 'white', 5: 'blue', 6: 'white', 7: 'blue', 8: 'white',
              10: 'white', 11: 'blue', 12: 'white', 13: 'blue', 14: 'white', 15: 'blue', 16: 'white', 17: 'red'}
BLANK_IMAGE = pygame.Surface((200, 200))
BLANK_IMAGE.fill("black")


class bar_event:
    time = 0.0
    bpm = 0
    position = 0.0
    bar = 0.0
    bar_length = 1.0
    lag_time = 0.0

    def __init__(self, bar, bpm=0, bar_length=1.0):
        self.bar = bar
        self.bpm = bpm
        self.bar_length = bar_length
        self.block = pygame.Surface((360, 2))
        self.block.fill(color='#AAAAAA')

    def self_time(self, last_bar):
        self.time = last_bar.time + 240 * last_bar.bar_length / last_bar.bpm * (self.bar - last_bar.bar)
        self.position = last_bar.position + (self.bar - last_bar.bar) * last_bar.bar_length

    def get_time(self, bar):
        _time = self.time + 240 * self.bar_length / self.bpm * (bar - self.bar)
        return _time

    def get_position(self, bar):
        _position = self.position + self.bar_length * (bar - self.bar)
        return _position

    def get_lag_time(self, _press_time):
        _time = self.time - _press_time
        self.lag_time = _time

    def display(self, _dp=False):
        y = 600 - self.lag_time * FLOW_SPEED + 1
        if 0 < y < WINDOW_WIDTH:
            screen.blit(self.block, (0, y))
            if _dp:
                screen.blit(self.block, (400, y))


class sound:
    start_bar = 0.0
    start_position = 0.0
    start_time = 0.0
    lag_time = 0.0
    sound_file = ""
    played = False
    playable = False

    def __init__(self, start_bar=0.0, sound_file=""):
        self.sound = None
        self.sound_file = sound_file
        self.start_bar = start_bar
        self.sound_load()

    def get_time(self, last_bar):
        self.start_time = last_bar.get_time(self.start_bar)
        self.start_position = last_bar.get_position(self.start_bar)

    def sound_load(self):
        if self.sound_file:
            if os.path.exists(self.sound_file):
                self.sound_file = self.sound_file
                self.playable = True
            elif os.path.exists(str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".ogg"):
                self.sound_file = str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".ogg"
                self.playable = True
            elif os.path.exists(str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".mp3"):
                self.sound_file = str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".mp3"
                self.playable = True
            elif os.path.exists(str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".flac"):
                self.sound_file = str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".flac"
                self.playable = True
            elif os.path.exists(str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".wav"):
                self.sound_file = str(self.sound_file).rsplit(sep=".", maxsplit=1)[0] + ".wav"
                self.playable = True
        if self.playable:
            self.sound = pygame.mixer.Sound(self.sound_file)

    def play_sound(self):
        self.played = True
        self.sound.play()

    def get_lag_time(self, _press_time):
        _time = self.start_time - _press_time
        self.lag_time = _time
        return _time


class note(sound):
    track = 0

    def __init__(self, start_bar, sound_file, track):
        sound.__init__(self, start_bar, sound_file)
        self.block = pygame.Surface((40, 10))
        self.block.fill(color=NOTE_COLOR[track])
        self.track = track

    def display(self):
        if not self.played:
            x = 40 * int(self.track)
            y = 600 - self.lag_time * FLOW_SPEED - 10
            if -10 < y < WINDOW_WIDTH:
                screen.blit(self.block, (x, y))

    def auto_play(self):
        self.play_sound()


class hold(note):
    end_bar = 0.0
    end_time = 0.0
    end_position = 0.0
    keep_time = 0.0

    def __init__(self, start_bar, sound_file, track, end_bar=0.0):
        note.__init__(self, start_bar, sound_file, track)
        self.end_bar = end_bar

    def get_end_time(self, last_bar):
        self.end_time = last_bar.get_time(self.end_bar)
        self.end_position = last_bar.get_position(self.end_bar)
        self.keep_time = self.end_time - self.start_time
        self.block = pygame.Surface((40, self.keep_time * FLOW_SPEED))
        self.block.fill(color=NOTE_COLOR[self.track])

    def display(self):
        if not self.played:
            x = 40 * int(self.track)
            y = 600 - self.lag_time * FLOW_SPEED - self.keep_time * FLOW_SPEED
            if - self.keep_time * FLOW_SPEED < y < WINDOW_WIDTH:
                screen.blit(self.block, (x, y))


class bg:
    video = False
    start_bar = 0.0
    start_time = 0.0
    file = ""
    played = False
    lag_time = 0.0
    next_time = 0.0
    raw_img = None
    img = BLANK_IMAGE

    def __init__(self, bg_file, start_bar):
        self.file = bg_file
        self.start_bar = start_bar
        if self.file:
            if not os.path.exists(self.file):
                self.played = True
            if re.search('.jpg|.png|.jpeg|.bmp|.gif|.webp', self.file):
                self.img = pygame.image.load(self.file)
                self.img = pygame.transform.scale(self.img, (400, 400))
            elif re.search('.mpg|.mp4|.wmv|.avi|.mkv|.mov|.flv', self.file):
                self.video = True
                self.cap = cv2.VideoCapture(self.file)
                self.all_frames = self.cap.get(7)
                self.played_frames = 0
                self.interval_time = 1 / int(self.cap.get(5))

    def get_time(self, last_bar):
        self.start_time = last_bar.get_time(self.start_bar)
        self.next_time = self.start_time

    def play(self, press_time=0.0):
        if self.video:
            if press_time > self.next_time and self.played_frames < self.all_frames:
                _success, self.raw_img = self.cap.read()
                self.raw_img = cv2.resize(self.raw_img, (400, 400), interpolation=cv2.INTER_LINEAR)
                self.next_time += self.interval_time
                self.played_frames += 1
                if _success:
                    self.img = pygame.image.frombuffer(self.raw_img.tobytes(), self.raw_img.shape[1::-1], "BGR")
                    return self.img
                else:
                    return BLANK_IMAGE
            else:
                return self.img
        else:
            return self.img

    def get_lag_time(self, _press_time):
        _time = self.start_time - _press_time
        self.lag_time = _time
        return _time


class BMSparser:
    file = ""
    path = ""

    info = {}
    sounds = []
    notes = []
    holds = []
    bgs = []
    all_bars = []

    bpm_list = []

    def __init__(self, file):

        TRACK_DICT = {'6': 1, '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '8': 7, '9': 8}
        TRACK_DICT_DP = {'6': 17, '1': 10, '2': 11, '3': 12, '4': 13, '5': 14, '8': 15, '9': 16}

        self.file = file
        self.path = str(file).rsplit(sep="\\", maxsplit=1)[0] + "\\"

        try:
            _f = open(file, encoding='utf-8')
            file_lines = _f.readlines()
        except UnicodeDecodeError:
            _f = open(file, encoding='ansi')
            file_lines = _f.readlines()

        bars = {}
        max_bar = 0

        sound_define = {}
        bg_define = {}

        if_state = False
        if_num = 0
        random_num = 0

        hold_started = {}
        for _i in range(16):
            hold_started[_i] = False
        hold_start_bar = {}
        hold_sound = {}

        for line in file_lines:
            line = line.removesuffix("\n")
            if re.match('#', line) and (if_state is False or if_num == random_num):
                if re.match('#WAV', line):
                    place = line[4:6]
                    sound_define[place] = line[7:]
                    pass
                elif re.match('#BMP', line):
                    place = line[4:6]
                    bg_define[place] = line[7:]
                    pass
                elif re.match(r'#\d', line):
                    channel = int(line[1:4])
                    if channel > max_bar:
                        max_bar = channel
                    message = line[7:]
                    length = len(message) // 2
                    if line[4] == "0":
                        if line[5] == "1":
                            for _i in range(length):
                                key = message[int(_i * 2): int(_i * 2 + 2)]
                                if key != "00":
                                    sound_file = ""
                                    if key in sound_define:
                                        sound_file = self.path + sound_define[key]
                                    start_bar = int(channel) + _i / length
                                    instance = sound(start_bar, sound_file)
                                    self.sounds.append(instance)
                        elif line[5] == "2":
                            if channel not in bars:
                                bars[channel] = bar_event(int(channel), 0, float(line[7:]))
                            else:
                                bars[channel].bar_length = float(line[7:])
                        elif line[5] == "3":
                            if channel not in bars:
                                bars[channel] = bar_event(int(channel), int(line[7:], 16), 1.0)
                            else:
                                bars[channel].bpm = int(line[7:], 16)
                        elif line[5] == "4":
                            for _i in range(length):
                                key = message[int(_i * 2): int(_i * 2 + 2)]
                                if key != "00":
                                    bg_file = ""
                                    if key in bg_define:
                                        bg_file = self.path + bg_define[key]
                                    start_bar = int(channel) + _i / length
                                    self.bgs.append(bg(bg_file, start_bar))
                    elif line[4] == "1" or line[4] == "2":
                        track = 0
                        if line[4] == "1":
                            track = TRACK_DICT[line[5]]
                        if line[4] == "2":
                            track = TRACK_DICT_DP[line[5]]
                        for _i in range(length):
                            key = message[int(_i * 2): int(_i * 2 + 2)]
                            if key != "00" and key in sound_define:
                                sound_file = self.path + sound_define[key]
                                start_bar = int(channel) + _i / length
                                instance = note(start_bar, sound_file, track)
                                self.notes.append(instance)
                    elif line[4] == "5" or line[4] == "6":
                        track = 0
                        if line[4] == "5":
                            track = TRACK_DICT[line[5]]
                        if line[4] == "6":
                            track = TRACK_DICT_DP[line[5]]
                        for _i in range(length):
                            key = message[int(_i * 2): int(_i * 2 + 2)]
                            if key != "00":
                                if hold_started[track]:
                                    hold_end_bar = int(channel) + _i / length
                                    instance = hold(hold_start_bar[track], hold_sound[track], track, hold_end_bar)
                                    self.holds.append(instance)
                                    hold_started[track] = False
                                else:
                                    hold_start_bar[track] = int(channel) + _i / length
                                    hold_sound[track] = self.path + sound_define[key]
                                    hold_started[track] = True
                elif re.match('#IF', line):
                    if_num = int(line[4:])
                    if_state = True
                elif re.match('#ENDIF', line):
                    if_state = False
                elif re.match('#RANDOM', line):
                    random_num = random.randint(1, int(line[8:]))
                elif re.match('#ENDRANDOM', line):
                    random_num = 0

                elif re.match('#PLAYER', line):
                    self.info['player'] = line[8:]
                elif re.match('#LNTYPE', line):
                    self.info['ln_type'] = line[8:]
                elif re.match('#BPM ', line):
                    self.info['bpm'] = line[5:]
                    if 0 not in bars:
                        bars[0] = bar_event(0, int(float(line[5:])))
                    else:
                        bars[0].bpm = int(line[5:])
                elif re.match('#GENRE', line):
                    self.info['genre'] = line[7:]
                elif re.match('#TITLE', line):
                    self.info['title'] = line[7:]
                elif re.match('#ARTIST', line):
                    self.info['artist'] = line[8:]
                elif re.match('#TOTAL', line):
                    self.info['total'] = line[7:]

                elif re.match('#PLAYLEVEL', line):
                    self.info['play_level'] = line[11:]
                elif re.match('#RANK', line):
                    self.info['rank'] = line[6:]
                elif re.match('#SUBTITLE', line):
                    self.info['sub_title'] = line[10:]
                elif re.match('#SUBARTIST', line):
                    self.info['sub_artist'] = line[11:]
                elif re.match('#BANNER', line):
                    self.info['banner'] = line[8:]
                elif re.match('#BACKBMP', line):
                    self.info['back_bmp'] = line[9:]
                elif re.match('#DIFFICULTY', line):
                    self.info['difficulty'] = line[12:]

            else:
                if re.match('#ENDIF', line):
                    if_state = False
        _f.close()

        for _i in range(max_bar + 1):
            if _i not in bars:
                bars[_i] = bar_event(_i)
            if not bars[_i].bpm:
                bars[_i].bpm = bars[_i - 1].bpm
            if _i != 0:
                bars[_i].self_time(bars[_i - 1])
            if bars[_i].time > 0.0:
                self.all_bars.append(bars[_i])

        for _i in self.sounds:
            _i.get_time(bars[int(_i.start_bar)])
        for _i in self.notes:
            _i.get_time(bars[int(_i.start_bar)])
        for _i in self.holds:
            _i.get_time(bars[int(_i.start_bar)])
            _i.get_end_time(bars[int(_i.end_bar)])
        for _i in self.bgs:
            _i.get_time(bars[int(_i.start_bar)])

    def total_notes(self):
        num = len(self.notes)
        return num

    def total_sounds(self):
        num = len(self.sounds)
        return num

    def total_holds(self):
        num = len(self.holds)
        return num


def try_get(dic, item):
    if item in dic:
        return dic[item]
    else:
        return " "


WINDOW_LENGTH = 800
bg_available = False
print("LiteBMxPlayer v0.1(Github:)\nPlease print BMS file path:")
path = input()
BMS = BMSparser(path)
current_bg = None
anime = BLANK_IMAGE
dp = False
text_x = 400
print(BMS.info['player'])
if BMS.info['player'] == "3" or BMS.info['player'] == "2":
    dp = True
    text_x = 760
    WINDOW_LENGTH = 1200
choice = input()
if choice.upper() == "Y":
    bg_available = True
pygame.mixer.init()
pygame.mixer.set_num_channels(150)
pygame.init()
screen = pygame.display.set_mode((WINDOW_LENGTH, WINDOW_WIDTH))
pygame.display.set_caption("LiteBMxPlayer v0.1")
screen.fill(color='black')
full_combo = BMS.total_notes() + BMS.total_holds() * 2
combo = 0
f = pygame.font.SysFont(['Consolas'], 16)
title = f.render(try_get(BMS.info, 'title') + " " + try_get(BMS.info, 'sub_title'), True, 'white')
artist = f.render(try_get(BMS.info, 'artist'), True, 'white')
sub_artist = f.render(try_get(BMS.info, 'sub_artist'), True, 'white')

vertical_line = pygame.Surface((1, 600))
vertical_line.fill(color='#202020')
pygame.display.flip()

zero_time = time.perf_counter()

pygame.display.flip()
while True:
    screen.fill(color='black')
    current_time = time.perf_counter() - zero_time
    for i in range(1, 10):
        screen.blit(vertical_line, (i * 40, 0))
    if dp:
        for i in range(10, 18):
            screen.blit(vertical_line, (i * 40, 0))
    for i in BMS.all_bars:
        i.get_lag_time(current_time)
        i.display(dp)
    for i in BMS.sounds:
        i.get_lag_time(current_time)
        if i.lag_time < 0.0001 and not i.played and i.playable:
            i.play_sound()
    for i in BMS.notes:
        i.get_lag_time(current_time)
        i.display()
        if i.lag_time < 0.0001 and not i.played and i.playable:
            i.auto_play()
            combo += 1
    for i in BMS.holds:
        i.get_lag_time(current_time)
        i.display()
        if i.lag_time < 0.0001 and not i.played and i.playable:
            i.auto_play()
            combo += 2
    if bg_available:
        for i in BMS.bgs:
            i.get_lag_time(current_time)
            if i.lag_time < 0.0001 and not i.played:
                current_bg = i
                anime = current_bg.play(current_time)

        if current_bg and current_bg.video:
            anime = current_bg.play(current_time)
        screen.blit(anime, (text_x, 160))
    combo_text = f.render("Combo:" + str(combo) + "/" + str(full_combo), True, 'white')
    screen.blit(combo_text, (text_x, 20))
    time_text = f.render("Time:" + str(int(current_time)), True, 'white')
    screen.blit(time_text, (text_x, 40))
    screen.blit(title, (text_x, 60))
    screen.blit(artist, (text_x, 80))
    screen.blit(sub_artist, (text_x, 100))
    screen.blit(anime, (text_x, 120))
    pygame.display.flip()
    pygame.display.update()
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
