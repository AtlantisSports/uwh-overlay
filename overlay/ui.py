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
  def __init__(self, parent, mgr, mask):
    Canvas.__init__(self, parent)

    self.parent = parent
    self.root = parent
    self.mgr = mgr
    self.mask = mask

    self.mgr.setBlackScore(7)
    self.mgr.setWhiteScore(12)

    self.initUI()

  def initUI(self):
    self.parent.title("TimeShark Scores")
    self.pack(fill=BOTH, expand=1)

    self.w = self.root.winfo_screenwidth()
    self.h = self.root.winfo_screenheight()

    self.refresh = 100
    self.t = 0
    def draw(self):
      self.delete(ALL)
      if self.mask:
        self.clear(fill="#000000")
      else:
        self.clear(fill="#054a91")
      self.timeAndScore()
      self.update()
      self.t += 10
      self.mgr.setGameClock(self.t)
      self.after(self.refresh, lambda : draw(self))
    self.after(1, lambda : draw(self))

  def clear(self, fill):
    self.create_rectangle((0, 0, self.w, self.h), fill=fill)

  def roundRectangle(self, bbox, radius, fill):
    x1, y1, x2, y2 = bbox
    self.create_oval((x1 - radius, y1, x1 + radius, y2), fill=fill, outline=fill)
    self.create_oval((x2 - radius, y1, x2 + radius, y2), fill=fill, outline=fill)
    self.create_rectangle(bbox, fill=fill, outline=fill)

  def timeAndScore(self):
    # Bounding box (except for ellipses)
    overall_width = 320
    overall_height = 40

    # Top left coords
    x1 = self.w / 2 - overall_width / 2
    y1 = overall_height / 2 + 10
    x2 = x1 + overall_width
    y2 = y1 + overall_height

    score_width = 50

    inset = 30
    radius = 15
    wing_size = 200
    outset = 2
    font=("Menlo", 30)
    logo_font=("Menlo", 30)
    time_font=("Menlo", 30)
    if self.mask:
      middle_color="#ffffff"
      middle_text="#ffffff"
      black_bg="#ffffff"
      white_bg="#ffffff"
      score_color="#ffffff"
      logo_color="#ffffff"
    else:
      middle_color="#2e96ff"
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

    if not self.mask:
      # White Score Text
      white_score = self.mgr.whiteScore()
      w_score="%d" % (white_score,)
      self.create_text((x1 + score_width / 2, y1 + overall_height / 2),
                       text=w_score, fill=score_color,
                       font=font)

      # Black Score Text
      black_score = self.mgr.blackScore()
      b_score="%d" % (black_score,)
      self.create_text((x2 - score_width / 2, y1 + overall_height / 2),
                       text=b_score, fill=score_color,
                       font=font)

      # Logo
      wall_time = int(round(time.time() * 1000))
      logo_text = "Timeshark"
      self.create_text((x1 + overall_width / 2, y1 + overall_height / 2),
                      text=logo_text, fill=logo_color, font=logo_font)

      # Game State Text
      state_text="1st Half"
      self.create_text((x1 - wing_size / 2, y1 + overall_height / 2),
                      text=state_text, fill=middle_text, font=font)

      # Game Clock Text
      clock_time = self.mgr.gameClock()
      clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
      self.create_text((x2 + wing_size / 2, y1 + overall_height / 2),
                      text=clock_text, fill=middle_text, font=time_font)

def Overlay(mgr, mask):
  root = Tk()
  ov = OverlayView(root, mgr, mask)
  # make it cover the entire screen
  w, h = root.winfo_screenwidth(), root.winfo_screenheight()
  root.geometry("%dx%d-0+0" % (w, h))
  root.attributes('-fullscreen', True)
  return ov
