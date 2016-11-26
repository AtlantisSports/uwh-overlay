#!/usr/bin/env python

import sys
import time
from Tkinter import *

from multiprocessing import Process, Queue
from datetime import datetime
import time
import sys

class MaskKind:
  NONE, LUMA, CHROMA = range(3)

def sized_frame(master, height, width):
  F = Frame(master, height=height, width=width)
  F.pack_propagate(0)
  return F

class OverlayView(Canvas):
  def __init__(self, parent, bbox, mgr, mask, version):
    Canvas.__init__(self, parent)

    self.parent = parent
    self.root = parent
    self.mgr = mgr
    self.mask = mask
    self.version = version

    self.mgr.setBlackScore(7)
    self.mgr.setWhiteScore(12)

    self.init_ui(bbox)

  def init_ui(self, bbox):
    self.parent.title("TimeShark Scores")
    self.pack(fill=BOTH, expand=1)

    self.w = bbox[0]
    self.h = bbox[1]

    self.refresh = 100
    self.t = 0
    def draw(self):
      self.delete(ALL)
      self.clear(fill=self.color("bg"))
      self.render()
      self.update()
      self.t += 10
      self.mgr.setGameClock(self.t)
      self.after(self.refresh, lambda : draw(self))
    self.after(1, lambda : draw(self))

  def clear(self, fill):
    self.create_rectangle((0, 0, self.w, self.h), fill=fill)

  def round_rectangle(self, bbox, radius, fill):
    x1, y1, x2, y2 = bbox
    self.create_oval((x1 - radius, y1, x1 + radius, y2), fill=fill, outline=fill)
    self.create_oval((x2 - radius, y1, x2 + radius, y2), fill=fill, outline=fill)
    self.create_rectangle(bbox, fill=fill, outline=fill)

  def bordered_round_rectangle(self, bbox, radius, outset, fill, border):
    self.round_rectangle(bbox=(bbox[0]-outset, bbox[1]-outset,
                               bbox[2]+outset, bbox[3]+outset),
                         radius=radius, fill=border)
    self.round_rectangle(bbox, radius=radius, fill=fill)

  @staticmethod
  def versions():
    return ["center", "left"]

  def render(self):
    {
      "center" : self.render_top_center,
      "left" : self.render_left
    }.get(self.version, self.render_top_center)()

  def color(self, name):
    if self.mask == MaskKind.LUMA:
      return "#000000" if name == "bg" else "#ffffff"

    if self.mask == MaskKind.CHROMA and name == "bg":
      return "#00ff00"

    return {
      "bg" : "#054a91",
      "border" : "#ffffff",
      "fill" : "#2e96ff",
      "fill_text" : "#ffffff",
      "black_fill" : "#000000",
      "black_text" : "#2e96ff",
      "white_fill" : "#ffffff",
      "white_text" : "#2e96ff"
    }.get(name, "#ff0000")

  def abbreviate(self, s):
    if len(s) > 16:
      return s[0:13] + "..."
    else:
      return s

  def render_left(self):
    radius = 15
    height = 30
    width = 260
    score_width = 40
    score_offset = width - score_width
    time_width = 150
    state_width = 100
    state_offset = score_offset + time_width
    outset = 2

    x1 = 40 + radius
    y1 = 40

    x2 = 1920 - 40 - radius
    y2 = y1

    font=("Menlo", 20)
    score_font=("Menlo", 30, "bold")
    logo_font=("Menlo", 30)
    time_font=("Menlo", 50)
    state_font=("Menlo", 40)

    # State
    self.bordered_round_rectangle(bbox=(x2 - state_width - time_width,
                                        y1,
                                        x2 - time_width,
                                        y2 + height * 2 + outset * 2),
                                  radius=radius, outset=outset,
                                  fill=self.color("fill"),
                                  border=self.color("border"))

    # Time
    self.bordered_round_rectangle(bbox=(x2 - time_width,
                                        y2,
                                        x2,
                                        y2 + height * 2 + outset * 2),
                                  radius=radius, outset=outset,
                                  fill=self.color("fill"),
                                  border=self.color("border"))

    # Teams
    self.bordered_round_rectangle(bbox=(x1, y1, x1 + width, y1 + height),
                                  radius=radius, outset=outset,
                                  fill=self.color("fill"),
                                  border=self.color("border"))
    self.bordered_round_rectangle(bbox=(x1, y1 + height + outset * 2,
                                        x1 + width, y1 + height * 2 + outset * 2),
                                  radius=radius, outset=outset,
                                  fill=self.color("fill"),
                                  border=self.color("border"))

    # Scores Fill
    self.round_rectangle(bbox=(x1 + score_offset,
                               y1,
                               x1 + score_offset + score_width,
                               y1 + height),
                         radius=radius, fill=self.color("white_fill"))
    self.round_rectangle(bbox=(x1 + score_offset,
                               y1 + height + outset * 2,
                               x1 + score_offset + score_width,
                               y1 + height * 2 + outset * 2),
                         radius=radius, fill=self.color("black_fill"))

    if not self.mask == MaskKind.LUMA:
      # Game State Text
      state_text="1st"
      self.create_text((x2 - time_width - radius * 2, y2 + height + outset),
                      text=state_text, fill=self.color("fill_text"), font=state_font, anchor=E)

      # Time Text
      clock_time = self.mgr.gameClock()
      #clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
      clock_text = "12:34"
      self.create_text((x2, y2 + height + outset),
                       text=clock_text, fill=self.color("fill_text"),
                       font=time_font, anchor=E)

      # White Score Text
      white_score = self.mgr.whiteScore()
      w_score="%d" % (white_score,)
      self.create_text((x1 + score_offset + score_width / 2, y1 + height / 2),
                       text=w_score, fill=self.color("white_text"),
                       font=score_font)

      # Black Score Text
      black_score = self.mgr.blackScore()
      b_score="%d" % (black_score,)
      self.create_text((x1 + score_offset + score_width / 2,
                        y1 + height / 2 + height + outset * 2),
                       text=b_score, fill=self.color("black_text"),
                       font=score_font)

      # White Team Text
      white_team=self.abbreviate("Rah Rah Oysters!")
      self.create_text((x1, y1 + outset + height / 2), text=white_team,
                       fill=self.color("fill_text"), anchor=W, font=font)

      #black_team="Club Puck"
      black_team=self.abbreviate("Team Moderately Sexy")
      self.create_text((x1, y1 + height + outset * 3 + height / 2), text=black_team,
                       fill=self.color("fill_text"), anchor=W, font=font)

  def render_top_center(self):
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

    # Border
    self.round_rectangle(bbox=(x1 - wing_size - outset, y1 - outset,
                              x2 + wing_size + outset, y2 + outset),
                         radius=radius, fill=self.color("border"))

    # Middle Section
    self.create_rectangle((x1, y1, x2, y2), fill=self.color("fill"),
                          outline=self.color("fill"))

    # Left Wing
    self.round_rectangle(bbox=(x1 - wing_size, y1, x1, y2),
                         radius=radius, fill=self.color("fill"))

    # Right Wing
    self.round_rectangle(bbox=(x2, y1, x2 + wing_size, y2),
                         radius=radius, fill=self.color("fill"))

    # White Score
    self.round_rectangle(bbox=(x1, y1, x1 + score_width, y1 + overall_height),
                         radius=radius, fill=self.color("white_fill"))
    # Black Score
    self.round_rectangle(bbox=(x2 - score_width, y1, x2, y1 + overall_height),
                         radius=radius, fill=self.color("black_fill"))

    if not self.mask == MaskKind.LUMA:
      # White Score Text
      white_score = self.mgr.whiteScore()
      w_score="%d" % (white_score,)
      self.create_text((x1 + score_width / 2, y1 + overall_height / 2),
                       text=w_score, fill=self.color("white_text"),
                       font=font)

      # Black Score Text
      black_score = self.mgr.blackScore()
      b_score="%d" % (black_score,)
      self.create_text((x2 - score_width / 2, y1 + overall_height / 2),
                       text=b_score, fill=self.color("black_text"),
                       font=font)

      # Logo
      wall_time = int(round(time.time() * 1000))
      logo_text = "Timeshark"
      self.create_text((x1 + overall_width / 2, y1 + overall_height / 2),
                      text=logo_text, fill=self.color("fill_text"),
                      font=logo_font)

      # Game State Text
      state_text="1st Half"
      self.create_text((x1 - wing_size / 2, y1 + overall_height / 2),
                      text=state_text, fill=self.color("fill_text"), font=font)

      # Game Clock Text
      clock_time = self.mgr.gameClock()
      clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
      self.create_text((x2 + wing_size / 2, y1 + overall_height / 2),
                      text=clock_text, fill=self.color("fill_text"), font=time_font)

class Overlay(object):
  def __init__(self, mgr, mask, version):
    self.root = Tk()
    # make it cover the entire screen
    #w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 1920, 1080
    self.ov = OverlayView(self.root, (w, h), mgr, mask, version)
    self.root.geometry("%dx%d-0+0" % (w, h))
    #self.root.attributes('-fullscreen', True)

  @staticmethod
  def versions():
    return OverlayView.versions()

  def mainloop(self):
    self.root.mainloop()
