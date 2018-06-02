#!/usr/bin/env python

from multiprocessing import Process, Queue
from datetime import datetime
import tkinter as tk
from uwh.gamemanager import PoolLayout, TeamColor
from uwh.uwhscores_comms import UWHScores
from PIL import Image, ImageTk

import time
import sys

class MaskKind:
  NONE, LUMA, CHROMA = range(3)

def sized_frame(master, height, width):
  F = tk.Frame(master, height=height, width=width)
  F.pack_propagate(0)
  return F

class OverlayView(tk.Canvas):
  def __init__(self, parent, bbox, mgr, mask, version):
    tk.Canvas.__init__(self, parent)

    self.parent = parent
    self.root = parent
    self.mgr = mgr
    self.mask = mask
    self.version = version

    #self.uwhscores = UWHScores('https://uwhscores.com/api/v1/', mock=True)
    self.uwhscores = UWHScores('http://localhost:5000/api/v1/', mock=False)
    self.tid = None
    self.gid = None
    self.white_id = None
    self.black_id = None
    self.white_name = None
    self.black_name = None
    self.white_roster = None
    self.black_roster = None
    self.tournament = None
    self.black_flag = None
    self.white_flag = None

    self.init_ui(bbox)

  def init_ui(self, bbox):
    self.parent.title("TimeShark Scores")
    self.pack(fill=tk.BOTH, expand=1)

    self.w = bbox[0]
    self.h = bbox[1]

    self.refresh = 100
    self.t = 0
    def draw(self):
      self.delete(tk.ALL)
      self.clear(fill=self.color("bg"))
      self.render()
      self.update()
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
    return ["center", "split", "worlds", "left"]

  def get(self, side, feature):
    if ((self.mgr.layout() == PoolLayout.white_on_right) ==
        (side == 'right')):
      return {
        'score' : self.mgr.whiteScore(),
        'color' : 'white',
        'id' : self.white_id,
        'name' : self.white_name,
        'roster' : self.white_roster,
        'flag' : self.white_flag,
      }[feature]
    else:
      return {
        'score' : self.mgr.blackScore(),
        'color' : 'black',
        'id' : self.black_id,
        'name' : self.black_name,
        'roster' : self.black_roster,
        'flag' : self.black_flag,
      }[feature]

  def render(self):
      # Update teams between games
      if (self.tid != self.mgr.tid() or
          self.gid != self.mgr.gid()):
          self.tid = self.mgr.tid()
          self.gid = self.mgr.gid()
          self.white_id = None
          self.black_id = None
          self.black_name = "Black"
          self.white_name = "White"
          self.black_roster = None
          self.white_roster = None
          self.tournament = None
          self.black_flag = None
          self.white_flag = None

          def game(response):
              self.black_name = response['black']
              self.white_name = response['white']
              self.black_id = response['black_id']
              self.white_id = response['white_id']
              def black_roster(roster):
                  self.black_roster = roster
              def white_roster(roster):
                  self.white_roster = roster
              self.uwhscores.get_roster(self.tid, self.black_id, black_roster)
              self.uwhscores.get_roster(self.tid, self.white_id, white_roster)
              def white_flag(flag):
                  self.white_flag = flag
              def black_flag(flag):
                  self.black_flag = flag
              self.uwhscores.get_team_flag(self.tid, self.black_id, black_flag)
              self.uwhscores.get_team_flag(self.tid, self.white_id, white_flag)

          self.uwhscores.get_game(self.tid, self.gid, game)

          def tournament(response):
              self.tournament = response
          self.uwhscores.get_tournament(self.tid, tournament)

      {
        "center" : self.render_top_center,
        "split" : self.render_split,
        "left" : self.render_left,
        "worlds" : self.render_worlds,
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
      "white_text" : "#2e96ff",
      "team_text"  : "#000000",
    }.get(name, "#ff0000")

  def abbreviate(self, s):
    if len(s) > 16:
      return s[0:13] + "..."
    else:
      return s

  def render_split(self):
    radius = 15
    height = 40
    width = 150
    score_width = 40
    score_offset = width - score_width
    time_width = 190
    state_width = 130
    timeout_width = 250
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

    # Timeout
    if (self.mgr.timeoutStateRef() or
        self.mgr.timeoutStateWhite() or
        self.mgr.timeoutStateBlack()):
        self.bordered_round_rectangle(bbox=(x2 - timeout_width - state_width - time_width,
                                            y1,
                                            x2 - state_width - time_width,
                                            y2 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=self.color("fill"),
                                      border=self.color("border"))

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
                         radius=radius, fill=self.color("%s_fill" % (self.get('left', 'color'),)))
    self.round_rectangle(bbox=(x1 + score_offset,
                               y1 + height + outset * 2,
                               x1 + score_offset + score_width,
                               y1 + height * 2 + outset * 2),
                         radius=radius, fill=self.color("%s_fill" % (self.get('right', 'color'),)))

    if not self.mask == MaskKind.LUMA:
      # Timeout
      timeout_text=""
      if self.mgr.timeoutStateRef():
          timeout_text="Ref T/O"
      elif self.mgr.timeoutStateWhite():
          timeout_text="White T/O"
      elif self.mgr.timeoutStateBlack():
          timeout_text="Black T/O"
      self.create_text((x2 - state_width - time_width - radius * 2, y2 + height + outset),
                      text=timeout_text, fill=self.color("fill_text"), font=state_font, anchor=tk.E)

      # Game State Text
      state_text=""
      if self.mgr.gameStateFirstHalf():
          state_text="1st"
      elif self.mgr.gameStateSecondHalf():
          state_text="2nd"
      elif self.mgr.gameStateHalfTime():
          state_text="H/T"
      elif self.mgr.gameStateGameOver():
          state_text="G/O"
      self.create_text((x2 - time_width - radius * 2, y2 + height + outset),
                      text=state_text, fill=self.color("fill_text"), font=state_font, anchor=tk.E)

      # Time Text
      clock_time = self.mgr.gameClock()
      clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
      self.create_text((x2, y2 + height + outset),
                       text=clock_text, fill=self.color("fill_text"),
                       font=time_font, anchor=tk.E)

      # White Score Text
      left_score = self.get('left', 'score')
      l_score="%d" % (left_score,)
      self.create_text((x1 + score_offset + score_width / 2, y1 + height / 2),
                       text=l_score, fill=self.color("%s_text" % (self.get('left', 'color'),)),
                       font=score_font)

      # Black Score Text
      right_score = self.get('right', 'score')
      r_score="%d" % (right_score,)
      self.create_text((x1 + score_offset + score_width / 2,
                        y1 + height / 2 + height + outset * 2),
                       text=r_score, fill=self.color("%s_text" % (self.get('right', 'color'),)),
                       font=score_font)

      # White Team Text
      white_team=self.abbreviate(self.get('left', 'color'))
      self.create_text((x1, y1 + outset + height / 2), text=white_team,
                       fill=self.color("fill_text"), anchor=tk.W, font=font)

      #black_team="Club Puck"
      black_team=self.abbreviate(self.get('right', 'color'))
      self.create_text((x1, y1 + height + outset * 3 + height / 2), text=black_team,
                       fill=self.color("fill_text"), anchor=tk.W, font=font)

  def render_left(self):
    radius = 10
    score_radius = 0
    height = 30
    width = 250
    flag_width = 60
    score_width = 40
    score_offset = width - score_width
    time_width = 155
    state_width = 110
    timeout_width = 150
    state_offset = score_offset + time_width
    outset = 2

    x1 = 40
    y1 = 40

    font=("Menlo", 20)
    score_font=("Menlo", 30, "bold")
    logo_font=("Menlo", 30)
    time_font=("Menlo", 50)
    state_font=("Menlo", 25)

    # Bottom Rectangle
    if (self.mgr.timeoutStateRef() or
        self.mgr.timeoutStateWhite() or
        self.mgr.timeoutStateBlack() or
        self.mgr.timeoutStatePenaltyShot()):
        if self.mgr.timeoutStateRef():
            fill_color = "#ffff00"
            border_color = "#000000"
        elif self.mgr.timeoutStateWhite():
            fill_color = "#ffffff"
            border_color = "#000000"
        elif self.mgr.timeoutStateBlack():
            fill_color = "#000000"
            border_color = "#ffffff"
        elif self.mgr.timeoutStatePenaltyShot():
            fill_color = "#ff0000"
            border_color = "#000000"

        self.bordered_round_rectangle(bbox=(x1 + width + state_width + time_width,
                                            y1,
                                            x1 + width + state_width + time_width + timeout_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=fill_color,
                                      border=border_color)

        self.bordered_round_rectangle(bbox=(x1,
                                            y1,
                                            x1 + width + state_width + time_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=self.color('fill'),
                                      border=self.color("border"))
    else:
        self.bordered_round_rectangle(bbox=(x1,
                                            y1,
                                            x1 + width + state_width + time_width,
                                            y1 + height * 2 + outset * 2),
                                      radius=radius, outset=outset,
                                      fill=self.color("fill"),
                                      border=self.color("border"))

    self.bordered_round_rectangle(bbox=(x1 + width + state_width,
                                        y1,
                                        x1 + width + state_width + time_width,
                                        y1 + height * 2 + outset * 2),
                                  radius=radius, outset=outset,
                                  fill=self.color("fill"),
                                  border=self.color("border"))

    # Flags
    left_flag = self.get('left', 'flag')
    if left_flag is not None:
        left_flag = left_flag.resize((flag_width, height + outset * 2), Image.ANTIALIAS)
        self._left_flag = ImageTk.PhotoImage(left_flag)
        self.create_image(x1 + width - score_width, y1, anchor=tk.NE, image=self._left_flag)

    right_flag = self.get('right', 'flag')
    if right_flag is not None:
        right_flag = right_flag.resize((flag_width, height + outset * 2), Image.ANTIALIAS)
        self._right_flag = ImageTk.PhotoImage(right_flag)
        self.create_image(x1 + width - score_width, y1 + height + outset, anchor=tk.NE, image=self._right_flag)

    # Scores Fill
    self.round_rectangle(bbox=(x1 + score_offset,
                               y1,
                               x1 + score_offset + score_width,
                               y1 + height + outset),
                         radius=score_radius, fill=self.color("%s_fill" % (self.get('left', 'color'),)))
    self.round_rectangle(bbox=(x1 + score_offset,
                               y1 + height + outset,
                               x1 + score_offset + score_width,
                               y1 + height * 2 + outset * 2),
                         radius=score_radius, fill=self.color("%s_fill" % (self.get('right', 'color'),)))

    if not self.mask == MaskKind.LUMA:
      # Timeout
      timeout_text=""
      text_color = self.color('fill_text')
      if self.mgr.timeoutStateRef():
          timeout_text="Ref\nTimeout"
          text_color="#000000"
      elif self.mgr.timeoutStateWhite():
          timeout_text="White\nTimeout"
          text_color=self.color('fill')
      elif self.mgr.timeoutStateBlack():
          timeout_text="Black\nTimeout"
          text_color=self.color('fill')
      elif self.mgr.timeoutStatePenaltyShot():
          timeout_text="Penalty\nShot"
          text_color="#000000"
      self.create_text((x1 + width + state_width + time_width + 30, y1 + height + outset),
                      text=timeout_text, fill=text_color, font=state_font, anchor=tk.W)

      # Game State Text
      state_text=""
      if self.mgr.gameStateFirstHalf():
          state_text="1st\nHalf"
      elif self.mgr.gameStateSecondHalf():
          state_text="2nd\nHalf"
      elif self.mgr.gameStateHalfTime():
          state_text="Half\nTime"
      elif self.mgr.gameStateGameOver():
          state_text="Game\nOver"
      self.create_text((x1 + width + outset + 20, y1 + height + outset),
                      text=state_text, fill=self.color("fill_text"), font=state_font, anchor=tk.W)

      # Time Text
      clock_time = self.mgr.gameClock()
      clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
      self.create_text((x1 + width + state_width, y1 + height + outset),
                       text=clock_text, fill=self.color("fill_text"),
                       font=time_font, anchor=tk.W)

      # White Score Text
      left_score = self.get('left', 'score')
      l_score="%d" % (left_score,)
      self.create_text((x1 + score_offset + score_width / 2, y1 + height / 2),
                       text=l_score, fill=self.color("%s_text" % (self.get('left', 'color'),)),
                       font=score_font)

      # Black Score Text
      right_score = self.get('right', 'score')
      r_score="%d" % (right_score,)
      self.create_text((x1 + score_offset + score_width / 2,
                        y1 + height / 2 + height + outset * 2),
                       text=r_score, fill=self.color("%s_text" % (self.get('right', 'color'),)),
                       font=score_font)

      # White Team Text
      white_team=self.abbreviate(self.get('left', 'name'))
      self.create_text((x1 + 10, y1 + outset + height / 2), text=white_team,
                       fill=self.color("fill_text"), anchor=tk.W, font=font)

      #black_team="Club Puck"
      black_team=self.abbreviate(self.get('right', 'name'))
      self.create_text((x1 + 10, y1 + height + outset * 3 + height / 2), text=black_team,
                       fill=self.color("fill_text"), anchor=tk.W, font=font)

      # Sin-bin
      penalties = self.mgr.penalties(TeamColor.white) + self.mgr.penalties(TeamColor.black)
      if len(penalties) > 0:
          penalties.sort(key=lambda p: p.timeRemaining(self.mgr))

          inset = 5
          v_spacing = 40
          penalty_height = 30

          #name = None
          name = "Voss, Valentine"

          if name:
              penalty_width = width + state_width + time_width
          else:
              penalty_width = 120

          y_offset = 0
          for p in penalties:
              fill_color = "#000000" if p.team() == TeamColor.black else "#ffffff"
              self.round_rectangle(bbox=(x1 + inset, y1 + height * 3 + y_offset - penalty_height / 2,
                                         x1 + penalty_width - inset,
                                         y1 + height * 3 + y_offset + penalty_height / 2),
                                   radius=radius, fill=fill_color)

              penalty_text = "#%d - %s" % (p.player(), name or "")
              self.create_text((x1, y1 + height * 3 + y_offset), text=penalty_text,
                               fill=self.color("fill"), anchor=tk.W, font=font)

              remaining = p.timeRemaining(self.mgr)
              penalty_text = "%d:%02d" % (remaining // 60, remaining % 60)
              self.create_text((x1 + penalty_width, y1 + height * 3 + y_offset), text=penalty_text,
                               fill=self.color("fill"), anchor=tk.E, font=font)


              y_offset += v_spacing

  def render_top_center(self):
    # Bounding box (except for ellipses)
    overall_width = 360
    overall_height = 40

    # Top left coords
    x1 = self.w / 2 - overall_width / 2
    y1 = overall_height / 2 + 10
    x2 = x1 + overall_width
    y2 = y1 + overall_height

    score_width = 50

    inset = 30
    radius = 15
    wing_size = 270
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
                         radius=radius, fill=self.color("%s_fill" % (self.get('left', 'color'),)))
    # Black Score
    self.round_rectangle(bbox=(x2 - score_width, y1, x2, y1 + overall_height),
                         radius=radius, fill=self.color("%s_fill" % (self.get('right', 'color'),)))

    if not self.mask == MaskKind.LUMA:
      # White Score Text
      left_score = self.get('left', 'score')
      l_score="%d" % (left_score,)
      self.create_text((x1 + score_width / 2, y1 + overall_height / 2),
                       text=l_score, fill=self.color("%s_text" % (self.get('left', 'color'),)),
                       font=font)

      # Black Score Text
      right_score = self.get('right', 'score')
      r_score="%d" % (right_score,)
      self.create_text((x2 - score_width / 2, y1 + overall_height / 2),
                       text=r_score, fill=self.color("%s_text" % (self.get('right', 'color'),)),
                       font=font)

      # Logo
      logo_text = "TimeShark"
      self.create_text((x1 + overall_width / 2, y1 + overall_height / 2),
                      text=logo_text, fill=self.color("fill_text"),
                      font=logo_font)

      # Game State Text
      state_text=""
      if self.mgr.gameStateFirstHalf():
          state_text="1st Half"
      elif self.mgr.gameStateSecondHalf():
          state_text="2nd Half"
      elif self.mgr.gameStateHalfTime():
          state_text="Half Time"
      elif self.mgr.gameStateGameOver():
          state_text="Game Over"
      self.create_text((x1 - wing_size / 2, y1 + overall_height / 2),
                      text=state_text, fill=self.color("fill_text"), font=font)

      # Game Clock Text
      clock_time = self.mgr.gameClock()
      clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
      self.create_text((x2 + wing_size / 2, y1 + overall_height / 2),
                      text=clock_text, fill=self.color("fill_text"), font=time_font)

  def render_worlds(self):

      font=("Menlo", 20)
      score_font=("Menlo", 30, "bold")
      logo_font=("Menlo", 30)
      time_font=("Menlo", 30)
      state_font=("Menlo", 40)
      team_font=("Menlo", 30, "bold")
      players_font=("Menlo", 20)

      def game_play_view():
          if not self.mask == MaskKind.LUMA:
              self._background = ImageTk.PhotoImage(Image.open("res/worlds-game-bg.png"))
              self.create_image(0, 0, anchor=tk.NW, image=self._background)

              row1_y = 20
              row2_y = 75

              left_flag = self.get('left', 'flag')
              if left_flag is not None:
                  self._left_flag = ImageTk.PhotoImage(left_flag)
                  self.create_image(10, row1_y, anchor=tk.NW, image=self._left_flag)

              right_flag = self.get('right', 'flag')
              if right_flag is not None:
                  self._right_flag = ImageTk.PhotoImage(right_flag)
                  self.create_image(180, row1_y, anchor=tk.NW, image=self._right_flag)

              clock_time = self.mgr.gameClock()
              clock_text = "%2d:%02d" % (clock_time // 60, clock_time % 60)
              self.create_text((125, row1_y),
                               text=clock_text, fill=self.color("fill_text"), font=time_font,
                               anchor=tk.N)

              left_score = self.get('left', 'score')
              l_score="%d" % (left_score,)
              self.create_text((40, row2_y),
                               text=l_score, fill=self.color("%s_fill" % (self.get('left', 'color'),)),
                               font=score_font)

              right_score = self.get('right', 'score')
              r_score="%d" % (right_score,)
              self.create_text((205, row2_y),
                               text=r_score, fill=self.color("%s_fill" % (self.get('right', 'color'),)),
                               font=score_font)

              state_text=""
              if self.mgr.gameStateFirstHalf():
                  state_text="1st Half"
              elif self.mgr.gameStateSecondHalf():
                  state_text="2nd Half"
              elif self.mgr.gameStateHalfTime():
                  state_text="Half Time"
              elif self.mgr.gameStateGameOver():
                  state_text="Game Over"
              self.create_text((125, row2_y),
                              text=state_text, fill=self.color("fill_text"), font=font)

      def roster_view():
          if not self.mask == MaskKind.LUMA:
              #self._background = ImageTk.PhotoImage(Image.open("res/worlds-roster-bg.png"))
              #self.create_image(0, 0, anchor=tk.NW, image=self._background)

              center_x = self.w / 2
              col_spread = 200
              left_col = center_x - col_spread
              right_col = center_x + col_spread
              col_width = 200
              flag_width = 75

              self.logo = ImageTk.PhotoImage(Image.open('res/worlds-roster-logo.png'))
              self.create_image(center_x, 125, anchor=tk.N, image=self.logo)

              left_flag = self.get('left', 'flag')
              if left_flag is not None:
                  self._left_flag = ImageTk.PhotoImage(left_flag)
                  self.create_image(left_col - col_width / 2, 600, anchor=tk.W, image=self._left_flag)

              right_flag = self.get('right', 'flag')
              if right_flag is not None:
                  self._right_flag = ImageTk.PhotoImage(right_flag)
                  self.create_image(right_col - col_width / 2, 600, anchor=tk.W, image=self._right_flag)

              name = self.get('left', 'name')
              if name is not None:
                  self.create_text((left_col - col_width / 2 + flag_width, 600), text=name,
                                   fill=self.color("team_text"), font=team_font, anchor=tk.W)

              name = self.get('right', 'name')
              if name is not None:
                  self.create_text((right_col - col_width / 2 + flag_width, 600), text=name,
                                   fill=self.color("team_text"), font=team_font, anchor=tk.W)

              roster = self.get('left', 'roster')
              if roster is not None:
                  y_offset = 0
                  for pid, player in roster.items():
                      display_text = "#{} - {}".format(pid, player['name'])
                      self.create_text((left_col - col_width / 2, 650 + y_offset), text=display_text,
                                       fill=self.color("team_text"), font=players_font,
                                       anchor=tk.W)
                      y_offset += 30

              roster = self.get('right', 'roster')
              if roster is not None:
                  y_offset = 0
                  for pid, player in roster.items():
                      display_text = "#{} - {}".format(pid, player['name'])
                      self.create_text((right_col - col_width / 2, 650 + y_offset), text=display_text,
                                       fill=self.color("team_text"), font=players_font,
                                       anchor=tk.W)
                      y_offset += 30

              if self.tournament is not None:
                  self.create_text((center_x, 475), text=self.tournament['name'],
                                   fill=self.color("team_text"), font=players_font,
                                   anchor=tk.N)

                  self.create_text((center_x, 525), text=self.tournament['location'],
                                   fill=self.color("team_text"), font=players_font,
                                   anchor=tk.N)


      if (self.mgr.gameStateFirstHalf() or
          self.mgr.gameStateHalfTime() or
          self.mgr.gameStateSecondHalf()):
          game_play_view()
      else:
          roster_view()

class Overlay(object):
  def __init__(self, mgr, mask, version):
    self.root = tk.Tk()
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
