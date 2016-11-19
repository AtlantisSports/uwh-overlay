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
    self.initUI()

  def initUI(self):
    self.parent.title("TimeShark Scores")
    self.pack(fill=BOTH, expand=1)

    # Vars
    ###########################################################################
    self.white_team = " White"
    self.black_team = " Black"
    self.border_text = ""
    self.w = self.root.winfo_screenwidth()
    self.h = self.root.winfo_screenheight()

    self.clear()

    self.timeAndScore()

  def clear(self):
    self.create_rectangle((0, 0, self.w, self.h), fill="#000000")

  def timeAndScore(self):
    black_score = self.mgr.blackScore()
    white_score = self.mgr.whiteScore()
    game_clock_time = self.mgr.gameClock()

    width = 400
    height = 50
    loc_x = self.w / 2 - width / 2
    loc_y = height / 2 + 10
    inset = 30

    radius = 15
    fg="#888888"
    font="Arial 40"
    w_score="%2d" % (white_score,)
    b_score="%2d" % (black_score,)

    self.create_oval((loc_x - radius, loc_y, loc_x + radius, loc_y + height), fill=fg, outline=fg)
    self.create_oval((loc_x + width - radius, loc_y, loc_x + width + radius, loc_y + height), fill=fg, outline=fg)
    self.create_rectangle((loc_x, loc_y, loc_x + width, loc_y + height), fill=fg, outline=fg)

    self.create_text((loc_x + inset, loc_y + height / 2),
                     text=w_score, fill="#ffffff",
                     font=font)

    self.create_text((loc_x + width - inset, loc_y + height / 2),
                     text=b_score, fill="#000088",
                     font=font)

def Overlay(mgr):
  root = Tk()
  ov = OverlayView(root, mgr)
  # make it cover the entire screen
  w, h = root.winfo_screenwidth(), root.winfo_screenheight()
  root.geometry("%dx%d-0+0" % (w, h))
  root.attributes('-fullscreen', True)
  return ov
