from Tkinter import *
import tkSimpleDialog
import tkMessageBox

import ast
import random
import string

def columns(xs):
    res = []

    for i in xrange(len(xs)):
        res.append([])
        for row in xs:
            if i < len(row):
                res[-1].append(row[i])
    
    res = filter(lambda i: len(i) > 0, res)

    return res

def diagonals(xs):
    diag1 = []
    for i in xrange(len(xs)):
        if i < len(xs[i]):
            diag1.append(xs[i][i])

    diag2 = []
    for i in xrange(len(xs)):
        if (len(xs) - i - 1) < len(xs[i]):
            diag2.append(xs[i][len(xs) - i - 1])

    return [diag1, diag2]

def get_all_tuples(w, h, depth):
    if depth == 0:
        return []
    elif depth == 1:
        res = []
        for x in xrange(w):
            for y in xrange(h):
                res.append([(x,y)])
        return res
    else:
        res = []
        for x in xrange(w):
            for y in xrange(h):
                for t in get_all_tuples(w, h, depth - 1):
                    res.append([(x,y)] + t)
        return res

class Board:
    def __init__(self, depth, w, h, fname=None):
        self.depth = depth
        self.w = w
        self.h = h
        
        if self.depth > 0:
            self.squares = self.build(self.depth)
        else:
            self.squares = []

        if fname != None:
            self.load(fname)

        self.first_move = True

    def build(self, cur, orig_depth=-1):
        if cur == 0:
            return ' '

        res = []

        for x in xrange(self.h):
            res.append([])
            for y in xrange(self.w):
                if orig_depth == -1:
                    res[-1].append(self.build(cur - 1, orig_depth=cur))
                else:
                    res[-1].append(self.build(cur - 1, orig_depth=orig_depth))

        return res

    def get_container(self, coords):
        cur = list(self.squares)
        for x, y in coords:
            cur = cur[y][x]

        return cur

    def get_owner(self, container):
        if isinstance(container, list):
            owner_square = []
            for x in xrange(self.h):
                owner_square.append([])
                for y in xrange(self.w):
                    res = self.get_owner(container[x][y])
                    owner_square[-1].append(res)

            all_rows = owner_square + columns(owner_square) + diagonals(owner_square)
            for row in all_rows:
                first = row[0]

                if first == None:
                    continue

                found = True
                for i in row:
                    if i != first:
                        found = False
                        break

                if found:
                    return first
            
            # If they're all full, whoever owns the most wins.
            # This way, every game will eventually end.
            # Also it treats equals one randomly, so
            if not any(map(lambda i: None in i, owner_square)):
                freqs = {}
                for row in owner_square:
                    for i in row:
                        if i in freqs:
                            freqs[i] += 1
                        else:
                            freqs[i] = 1
                options = []
                cur_max = 0
                for k, v in freqs.iteritems():
                    if v >= cur_max:
                        if v > cur_max:
                            cur_max = v
                            options = []
                        options.append(k)
                
                if len(options) > 0:
                    for row in owner_square:
                        for s in row:
                            if s in options:
                                return s
                return options[0] 

            return None
        else:
            if container != ' ':
                return container
            else:
                return None

    def get_all_open(self, container):
        if self.get_owner(container) != None:
            return []

        res = []
        for x in xrange(self.h):
            for y in xrange(self.w):
                if isinstance(container[x][y], list):
                    for move in self.get_all_open(container[x][y]):
                        res.append([(y,x)] + move)
                elif container[x][y] == ' ':
                    res.append([(y,x)])

        return res

    def all_open(self, coords):
        cur = self.get_container(coords)

        if len(coords) > 0:
            if self.get_owner(cur) != None:
                return self.all_open(coords[:-1])

        res = []
        for move in self.get_all_open(cur):
            res.append(coords + move)
        
        if len(res) == 0:
            if len(coords) == 0:
                return []
            else:
                return self.all_open(coords[:-1])

        return res

    def do_move(self, move, marker):
        move_x, move_y = move[-1]
        coords = move[:-1]

        cur = self.get_container(coords)
        cur[move_y][move_x] = marker

        mod = self.squares
        for i,(x,y) in enumerate(coords):
            if i == len(coords) - 1:
                mod[y][x] = cur
            else:
                mod = mod[y][x]

    # Make the move and then return all of next valid moves
    def handle_move(self, move, marker):
        if self.first_move:
            self.first_move = False

            return self.all_open([])
        else:
            self.do_move(move, marker)

            # Check what the highest tier of thing that won is, then the valid moves is everything one tier above that
            for i in xrange(1, len(move) + 1):
                if self.get_owner(self.get_container(move[:i])) != None:
                    if i - 2 < 0:
                        next_coords = [move[i]]
                    else:
                        next_coords = move[:i - 2] + [move[i - 1]]
                    return self.all_open(next_coords)
            
            # We really should find one, but if we don't, just return everything
            return self.all_open([])

class Main:
    def __init__(self, depth, w, h, players, fname=None):
        self.parent = Tk()
        self.parent.title('Generalized Tic Tac Toe: Depth: 0')
        self.parent.geometry('700x720+0+0')

        self.save_button = Button(self.parent, text='Save', command=self.do_save)
        self.save_button.pack()

        self.canvas = Canvas(self.parent, width=700, height=700)
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.handle_click)
        self.canvas.bind('<Button-2>', self.handle_rclick)
        self.canvas.bind('<Button-3>', self.handle_rclick)

        self.cur_display = []
        self.board = Board(depth, w, h)
        self.depth = depth
        self.w = w
        self.h = h

        self.markers = players
        self.pcolors = {}
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, p in enumerate(players):
            if i > len(colors):
                self.pcolors[p] = 'black'
            else:
                self.pcolors[p] = colors[i]
        if fname != None:
            self.load(fname)
        else:
            self.valid_moves = self.board.handle_move(None, None)

        self.draw_ttt_grid((0,0), (700,700))
                
        self.small_squares = []
        for x in xrange(self.w):
            self.small_squares.append([])
            for y in xrange(self.h):
                self.small_squares[-1].append([])
                self.draw_ttt_grid((x * 700 / self.w, y * 700 / self.h), ((x + 1) * 700 / self.w, ((y + 1) * 700 / self.h)))

                for x2 in xrange(self.w):
                    self.small_squares[-1][-1].append([])
                    for y2 in xrange(self.h):
                        sx = x2 * 700.0 / (self.w**2) + x * 700 / self.w + 700 / (self.w**2 * 2)
                        sy = y2 * 700.0 / (self.h**2) + y * 700 / self.h + 700 / (self.h**2 * 2)
                        sx, sy = int(sx), int(sy)
                        sid = self.canvas.create_text(sx, sy, text='')
                        self.small_squares[-1][-1][-1].append(sid)

        self.refresh_display()

    def load(self, fname):
        with open(fname, 'r') as f:
            lines = f.read().replace('\r', '').split('\n')
            self.board.squares = ast.literal_eval(lines[0])
            self.board.first_move = False
            self.valid_moves = ast.literal_eval(lines[1])
            self.markers = ast.literal_eval(lines[2])
            self.pcolors = ast.literal_eval(lines[3])
            self.depth = ast.literal_eval(lines[4])

            self.w, self.h = ast.literal_eval(lines[5])
            self.board.w = self.w
            self.board.h = self.h
    
    def save(self, fname):
        with open(fname, 'w') as f:
            f.write('{}\n'.format(self.board.squares))
            f.write('{}\n'.format(self.valid_moves))
            f.write('{}\n'.format(self.markers))
            f.write('{}\n'.format(self.pcolors))
            f.write('{}\n'.format(self.depth))
            f.write('({},{})\n'.format(self.w, self.h))

    def do_save(self):
        fname = tkSimpleDialog.askstring('Save As:', 'Enter file name')
        if fname != None:
            self.save(fname)

    def draw_ttt_grid(self, (xmin, ymin), (xmax, ymax)):
        x_spacing = (xmax - xmin - 10) / self.w
        y_spacing = (ymax - ymin - 10) / self.h

        for x in xrange(1, self.w):
            x1 = xmin + x * x_spacing + 7
            y1 = ymin + 7
            y2 = ymax - 7
            self.canvas.create_line(x1, y1, x1, y2)

        for y in xrange(1, self.h):
            x1 = xmin + 7
            x2 = xmax - 7
            y1 = ymin + y * y_spacing + 7
            self.canvas.create_line(x1, y1, x2, y1)

    def start(self):
        self.parent.mainloop()

    def handle_rclick(self, event):
        if len(self.cur_display) > 0:
            self.cur_display.pop()

        self.refresh_display()

    def handle_click(self, event):
        x, y = event.x, event.y

        # Get the major square
        majx = x * self.w // 700
        majy = y * self.h // 700
        # Get the minor square
        minx = int((x - majx * 700.0 / self.w) * self.w**2 // 700)
        miny = int((y - majy * 700.0 / self.h) * self.h**2 // 700)

        # We can still zoom in
        if len(self.cur_display) < self.depth - 2:
            self.cur_display.append((majx, majy))
        else: # Check if we can actually click here, and, if so, do it
           move = list(self.cur_display) + [(majx, majy), (minx, miny)]
           if move in self.valid_moves:
                self.first_move = False
                self.valid_moves = self.board.handle_move(move, self.markers[0])
                self.markers = self.markers[1:] + [self.markers[0]]
                
                winner = self.board.get_owner(self.board.squares)
                if winner != None:
                   tkMessageBox.showinfo('Game Finished', '{} won!'.format(winner))

        self.refresh_display()

    def refresh_display(self):
        self.parent.title('Generalized Tic Tac Toe: Depth: {}, {}\'s Turn'.format(len(self.cur_display), self.markers[0]))

        cur = self.board.get_container(self.cur_display)
        check_moves = map(lambda i: i[:len(self.cur_display) + 2], self.valid_moves)

        for y1, srow in enumerate(cur):
            for x1, s in enumerate(srow):
                for y2, row in enumerate(s):
                    for x2, row_s in enumerate(row):
                        move = list(self.cur_display) + [(x1,y1), (x2,y2)]
                        if move in check_moves:
                            if len(move) == len(self.valid_moves[0]): # This means we're at the bottom layer
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], text='!', fill=self.pcolors[self.markers[0]])
                            else:
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], text='!!', fill=self.pcolors[self.markers[0]])
                        elif isinstance(row_s, str):
                            if row_s in self.pcolors:
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], text=row_s, fill=self.pcolors[row_s])
                            else:
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], text=row_s, fill='black')
                        else:
                            owner = self.board.get_owner(cur[y1][x1][y2][x2])
                            
                            if owner == None:
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], text='', fill='black')
                            else:
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], text='{}'.format(owner))
                                self.canvas.itemconfig(self.small_squares[x1][y1][x2][y2], fill=self.pcolors[owner])

class Selector:
    def __init__(self):
        self.parent = Tk()
        self.parent.title('Selector')
        self.parent.geometry('400x300+0+0')

        self.depth_var = StringVar()
        self.depth_var.set('3')

        self.depth_label = Label(self.parent, text='Depth (from 2 to pretty much whatever):')
        self.depth_label.pack()
        self.depth_entry = Entry(self.parent, textvariable=self.depth_var)
        self.depth_entry.pack()

        self.player_var = StringVar()
        self.player_var.set('A,B')

        self.players_label = Label(self.parent, text='Players (comma separated):')
        self.players_label.pack()
        self.player_entry = Entry(self.parent, textvariable=self.player_var)
        self.player_entry.pack()

        self.dimensions_var = StringVar()
        self.dimensions_var.set('3x3')

        self.dimensions_label = Label(self.parent, text='Dimensions of the boards/sub-boards (e.g. 3x3 or 5x4):')
        self.dimensions_label.pack()
        self.dimensions_entry = Entry(self.parent, textvariable=self.dimensions_var)
        self.dimensions_entry.pack()

        self.go = Button(self.parent, command=self.run, text='Go')
        self.go.pack()

        self.load_button = Button(self.parent, command=self.do_load, text='Load')
        self.load_button.pack()

        self.parent.mainloop()

    def do_load(self):
        fname = tkSimpleDialog.askstring('Load:', 'Enter file name')
        if fname != None:
            self.run(fname)

    def run(self, fname=None):
        if fname == None:
            depth = int(self.depth_var.get())
            players = self.player_var.get().split(',')
            
            dims = self.dimensions_var.get().split('x')
            w = int(dims[0])
            h = int(dims[1])
        else:
            depth = 0
            w = 0
            h = 0
            players = []

        m = Main(depth, w, h, players, fname)
        m.start()

if __name__ == '__main__':
    Selector()
