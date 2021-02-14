import glfw
import numpy as np
import os
from OpenGL.GL import *
from OpenGL.arrays import vbo

class Scene:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.points = [] #Kontrollpunkte mit Gewicht
        self.deboorPoints = [] #Ohne Gewicht
        self.curve = [] #Array fuer Curve
        self.k = 4 # Ordnung
        self.m = 10 # Anzahl Punkte auf Kurve
        self.linecolor = [0,1,0]

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)
        #pointlst = self.remove_z()
        myvbo = vbo.VBO(np.array(self.deboorPoints, 'f'))
        myvbo.bind()
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, myvbo)
        glColor3fv([0,0,0])
        glPointSize(5)
        glDrawArrays(GL_POINTS, 0, len(self.deboorPoints))

        if len(self.points) > 1:
            glDrawArrays(GL_LINE_STRIP, 0, len(self.deboorPoints))

        if self.curve:
            #newCurve = self.remove_z2()
            curve = vbo.VBO(np.array(self.curve, 'f'))
            curve.bind()
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, curve)
            glColor(self.linecolor)
            #glDrawArrays(GL_POINTS, 0, len(curve))
            glDrawArrays(GL_LINE_STRIP, 0, len(curve))
            curve.unbind()

        myvbo.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)
        glFlush()

    def addPoint(self, x, y):
        self.points.append([x,y])
        self.updateDeboor()

    def calcKnotVec(self):
        if len(self.points) >= self.k:
            t1 = [0] * self.k
            t2 = [value for value in range(1, len(self.points) - (self.k - 1))]
            t3 = [len(self.points) - (self.k - 1) for x in range(self.k)]
            #print("knot", t1, t2, t3)
            knotvektor = t1 + t2 + t3
            return knotvektor
        else:
            return None

    def deboor(self, j, i, degree, controlpoints, knotvector, t):
        if j == 0:
            return controlpoints[i]
        temp = knotvector[i]
        x = (t - temp)
        y = (knotvector[i - j + degree] - temp)
        if y == 0:
            alpha = 0
        else:
            alpha = x/y
        left = self.deboor(j-1, i-1, degree, controlpoints, knotvector, t)
        right = self.deboor(j-1, i, degree, controlpoints, knotvector, t)
        #xCor = (left * (1 - alpha)) + (right * alpha)
        #yCor = (left * (1 - alpha)) + (right * alpha)
        point = np.asarray(left) * (1 - alpha) + np.asarray(right) * (1 - alpha)
        return point

    def updateDeboor(self):
        #self.make2d()
        knotvec = self.calcKnotVec()
        self.curve = []
        if not knotvec:
            return
        for i in range(self.m + 1):
            t = (float(i) / self.m) * knotvec[-1]
            r = 0
            for j in range(len(knotvec)):
                if t == max(knotvec):
                    r = len(knotvec) - self.k - 1
                    break
                if knotvec[j] > t:
                    r = j - 1
                    break
            erg = self.deboor(self.k - 1, r, self.k, self.deboorPoints, knotvec, t)
            self.curve.append(erg)

    def changeW(self, pos, curPoint, index):
        curPoint = list(curPoint)
        if self.lastpoint[1] < pos[1]:
            oldval = curPoint[2]
            if oldval < 10:
                newval = oldval + 1
                curPoint[2] = newval
            self.points[index-1] = curPoint
            self.updateDeboor()
        else:
            oldval = curPoint[2]
            if oldval > 1:
                newval = oldval - 1
                curPoint[2] = newval
            self.points[index-1] = curPoint
            self.updateDeboor()
        self.lastpoint = pos

    def make2d(self):
        for point in self.points:
            print("point", point)
            self.deboorPoints.append((point[0] / point[2], point[1] / point[2]))
        print(self.deboorPoints)


class RenderWindow:
    def __init__(self):

        cwd = os.getcwd()
        if not glfw.init():
            return
        os.chdir(cwd)
        glfw.window_hint(glfw.DEPTH_BITS, 32)
        self.frame_rate = 100

        self.mousePos = (0,0)
        self.width, self.height = 1000, 800
        self.aspect = self.width / float(self.height)
        self.window = glfw.create_window(self.width, self.height, "Base Spline", None, None)
        if not self.window:
            glfw.terminate()
            return
        glfw.make_context_current(self.window)

        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        #glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -2, 2)
        glMatrixMode(GL_MODELVIEW)

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)
        glfw.set_cursor_pos_callback(self.window, self.mouse_moved)

        self.scene = Scene(self.width, self.height)
        self.exitNow = False
        self.animation = True
        self.changeWeights = False
        self.selectedPoint = None
        self.index = 0

    def onKeyboard(self, win, key, scancode, action, mods):
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_M:
                if mods == glfw.MOD_SHIFT:
                    if self.scene.m >= 4:
                        self.scene.m -= 1
                        self.scene.updateDeboor()
                else:
                    self.scene.m += 1
                    self.scene.updateDeboor()
            if key == glfw.KEY_K:
                if mods == glfw.MOD_SHIFT:
                    if self.scene.k > 2:
                        self.scene.k -= 1
                        self.scene.updateDeboor()
                else:
                    if 1 <= self.scene.k:
                        self.scene.k += 1
                        self.scene.updateDeboor()


    def mouse_moved(self, win, x, y):
        if self.changeWeights:
            pos = glfw.get_cursor_pos(win)
            self.scene.changeW(pos, self.selectedPoint, self.index)



            '''
            for point in self.scene.points:
                if np.array_equal(point, self.selectedPoint):
                    y = self.height - y
                    w = (y - self.selectedPoint[1]) / 100
                    if w >= 10:
                        w = 10
                    if w <= 1:
                        w = 1
                    point = list(point)
                    point[0] /= point[2]
                    point[1] /= point[2]
                    point[2] = w
                    self.scene.points[i] = list(self.scene.points)
                    self.scene.points[i][0] = point[0]
                    self.scene.points[i][1] = point[1]
                    self.scene.points[i][2] = w
                    point[0] *= point[2]
                    point[1] *= point[2]
                    self.scene.points[i][0] = point[0]
                    self.scene.points[i][1] = point[1]

                    self.scene.updateDeboor()
                i += 1
                    #print("POINTs", point[0], point[1])
            '''

    def onMouseButton(self, win, button, action, mods):
        #print("mouse button: ", win, button, action, mods)
        if button == glfw.MOUSE_BUTTON_LEFT:
            if mods == glfw.MOD_SHIFT:
                p = list(glfw.get_cursor_pos(win))
                p[1] = self.height - p[1]
                self.index = 0
                for point in self.scene.points:
                    self.index += 1
                    a = abs(p[0] - point[0])
                    b = abs(p[1] - point[1])
                    dist = (a, b)
                    if dist[0] < 20 and dist[1] < 20:
                        self.selectedPoint = point
                    self.changeWeights = True
                    self.scene.updateDeboor()
                    if glfw.get_mouse_button(win, button) == glfw.PRESS:
                        self.changeWeights = True
                    if glfw.get_mouse_button(win, button) == glfw.RELEASE:
                        self.changeWeights = False
                        self.selectedPoint = []
            else:
                if glfw.get_mouse_button(win, button) == glfw.PRESS:
                    pass
                if glfw.get_mouse_button(win, button) == glfw.RELEASE:
                    pos = glfw.get_cursor_pos(win)
                    self.scene.addPoint(pos[0], self.height - pos[1])

    def onSize(self, win, width, height):
        self.width = width
        self.height = height
        self.aspect = width / float(height)

    def run(self):
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            currT = glfw.get_time()
            if currT - t > 1.0 / self.frame_rate:
                t = currT
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.scene.render()
                glfw.swap_buffers(self.window)
                glfw.poll_events()
        glfw.terminate()

def main():
    print("Simple glfw render Window")
    rw = RenderWindow()
    rw.run()


# call main
if __name__ == '__main__':
    main()