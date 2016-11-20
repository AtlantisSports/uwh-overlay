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
    self.white_team = " White"
    self.black_team = " Black"
    self.border_text = ""
    self.w = self.root.winfo_screenwidth()
    self.h = self.root.winfo_screenheight()

    self.clear()

    self.timeAndScore()

  def clear(self):
    self.create_rectangle((0, 0, self.w, self.h), fill="#000000")

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
    overall_width = 400
    overall_height = 50

    # Top left coords
    x1 = self.w / 2 - overall_width / 2
    y1 = overall_height / 2 + 10
    x2 = x1 + overall_width
    y2 = y1 + overall_height

    score_width = 50

    inset = 30
    radius = 15
    fg="#aaaaaa"
    font="Arial 40"
    w_score="%2d" % (white_score,)
    b_score="%2d" % (black_score,)

    self.create_rectangle((x1, y1, x2, y2), fill="#00aaaa", outline="#00aaaa")

    self.roundRectangle(bbox=(x1, y1, x1 + score_width, y1 + overall_height),
                        radius=radius, fill=fg)
    self.roundRectangle(bbox=(x2 - score_width, y1, x2, y1 + overall_height),
                        radius=radius, fill=fg)

    self.create_text((x1 + score_width / 2, y1 + overall_height / 2),
                     text=w_score, fill="#ffffff",
                     font=font)

    self.create_text((x2 - score_width / 2, y1 + overall_height / 2),
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
