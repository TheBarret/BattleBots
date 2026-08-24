import pygame
import random

from config import *

class SoundBits:
    def __init__(self):
        if not AUDIO_SFX_ENABLED: return
        pygame.mixer.set_num_channels(16)
        self.fireR_sfx = pygame.mixer.Sound("./sfx/fireRed.mp3")
        self.fireB_sfx = pygame.mixer.Sound("./sfx/fireBlue.mp3")
        self.hit_sfx = pygame.mixer.Sound("./sfx/hit.mp3")

        self.fireR_sfx.set_volume(AUDIO_SFX_VOLUME)
        self.fireB_sfx.set_volume(AUDIO_SFX_VOLUME)
        self.hit_sfx.set_volume(AUDIO_SFX_VOLUME)

        self.last_laser_frame = 0
        self.shots_this_frame = 0
        self.max_shots_per_frame = AUDIO_MAX_PLAY

    def begin_frame(self):
        if not AUDIO_SFX_ENABLED: return
        """Reset per-frame counters at the start of Simulation.step()"""
        self.shots_this_frame = 0

    def play_fire(self, team: int):
        if not AUDIO_SFX_ENABLED: return
        """Play laser sound with density throttling"""
        if self.shots_this_frame < self.max_shots_per_frame:
            # Find an unused channel quickly
            channel = pygame.mixer.find_channel()
            if channel:
                if team == 0: channel.play(self.fireR_sfx)
                if team == 1: channel.play(self.fireB_sfx)
                self.shots_this_frame += 1

    def play_hit(self):
        if not AUDIO_SFX_ENABLED: return
        """Impact SFX (higher priority, won't throttle as aggressively)"""
        channel = pygame.mixer.find_channel()
        if channel:
            channel.play(self.hit_sfx)
