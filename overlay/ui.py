#!/usr/bin/env python

import sys
import time
from Tkinter import *

from multiprocessing import Process, Queue
from datetime import datetime
import time
import sys

def sized_frame(master, height, width):
   F = Frame(master, height=height, width=width)
   F.pack_propagate(0)
   return F

class OverlayView(Canvas):
  def __init__(self, parent, mgr):
    Canvas.__init__(self, parent)

    self.parent = parent
    self.root = parent
    self.mgr = mgr

    self.mgr.setBlackScore(7)
    self.mgr.setWhiteScore(12)

    self.initUI()

  def initUI(self):
    self.parent.title("TimeShark Scores")
    self.pack(fill=BOTH, expand=1)

    # Vars
    ###########################################################################
    self.w = self.root.winfo_screenwidth()
    self.h = self.root.winfo_screenheight()

    self.clear()

    self.timeAndScore()

  def clear(self):
    #fake_water_color="#2e96ff"
    fake_water_color="#054a91"
    self.create_rectangle((0, 0, self.w, self.h), fill=fake_water_color)

  def roundRectangle(self, bbox, radius, fill):
    x1, y1, x2, y2 = bbox
    self.create_oval((x1 - radius, y1, x1 + radius, y2), fill=fill, outline=fill)
    self.create_oval((x2 - radius, y1, x2 + radius, y2), fill=fill, outline=fill)
    self.create_rectangle(bbox, fill=fill, outline=fill)

  def timeAndScore(self):
    black_score = self.mgr.blackScore()
    white_score = self.mgr.whiteScore()
    game_clock_time = self.mgr.gameClock()

    # Bounding box (except for ellipses)
    overall_width = 380
    overall_height = 50

    # Top left coords
    x1 = self.w / 2 - overall_width / 2
    y1 = overall_height / 2 + 10
    x2 = x1 + overall_width
    y2 = y1 + overall_height

    score_width = 50

    inset = 30
    radius = 15
    wing_offset = 265
    wing_size = 125
    outset = 2
    font=("Futura condensed light", 40)
    logo_font=("Futura condensed light", 40)
    w_score="%d" % (white_score,)
    b_score="%d" % (black_score,)
    middle_color="#8f42f4"
    middle_text="#ffffff"
    black_bg="#000000"
    white_bg="#ffffff"
    score_color=middle_color
    logo_color="#ffffff"

    # Border
    self.roundRectangle(bbox=(x1 - wing_size - outset, y1 - outset,
                              x2 + wing_size + outset, y2 + outset),
                        radius=radius, fill=white_bg)

    # Middle Section
    self.create_rectangle((x1, y1, x2, y2), fill=middle_color, outline=middle_color)

    # Left Wing
    self.roundRectangle(bbox=(x1 - wing_size, y1, x1, y2),
                        radius=radius, fill=middle_color)

    # Right Wing
    self.roundRectangle(bbox=(x2, y1, x2 + wing_size, y2),
                        radius=radius, fill=middle_color)

    # White Score
    self.roundRectangle(bbox=(x1, y1, x1 + score_width, y1 + overall_height),
                        radius=radius, fill=white_bg)
    # Black Score
    self.roundRectangle(bbox=(x2 - score_width, y1, x2, y1 + overall_height),
                        radius=radius, fill=black_bg)


    self.create_text((x1 + score_width / 2, y1 + overall_height / 2),
                     text=w_score, fill=score_color,
                     font=font)

    self.create_text((x2 - score_width / 2, y1 + overall_height / 2),
                     text=b_score, fill=score_color,
                     font=font)

    self.create_text((x1 + overall_width / 2, y1 + overall_height / 2),
                    text="TiMESHARK", fill=logo_color, font=logo_font)

    self.create_text((x1 + overall_width / 2 - wing_offset, y1 + overall_height / 2),
                    text="1st", fill=middle_text, font=font)

    self.create_text((x1 + overall_width / 2 + wing_offset, y1 + overall_height / 2),
                    text="13:25", fill=middle_text, font=font)

def Overlay(mgr):
  root = Tk()
  ov = OverlayView(root, mgr)
  # make it cover the entire screen
  w, h = root.winfo_screenwidth(), root.winfo_screenheight()
  root.geometry("%dx%d-0+0" % (w, h))
  root.attributes('-fullscreen', True)
  return ov
