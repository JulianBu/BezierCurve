import glfw
import numpy as np
import os
from OpenGL.GL import *
from OpenGL.arrays import vbo


class Scene:

    def __init__(self):
        self.k = 4  # Ordnung der Kurve
        self.m = 10  # Anzahl der Kurvenpunkte
        self.points = []
        self.curve = []
        self.weightPoints = []
        self.deboorPoints = []
        self.curvePoints = []
        self.foundPoint = False
        self.index = 0
        self.lastPos = (0, 0)
        self.linecolor = [0, 1, 0]

    def addPoint(self, x, y):
        self.weightPoints.append([x, y, 1.0])
        self.updateDeboor()

    def updateDeboorWeight(self, mousePos):
        if self.foundPoint:
            curPoint = self.weightPoints[self.index]
            w = curPoint[2]
            if self.lastPos[1] < mousePos[1]:
                if w < 10:
                    curPoint[2] = w + 1
            else:
                if w > 1:
                    curPoint[2] = w - 1
            self.weightPoints[self.index] = curPoint
            self.lastPos = mousePos
            self.updateDeboor()
        else:
            self.searchPoint(mousePos[0], mousePos[1])

    def searchPoint(self, x, y):
        self.index = 0
        for point in self.points:
            a = abs(x - point[0])
            b = abs(y - point[1])
            if a < 0.3 and b < 0.3:
                self.foundPoint = True
                self.lastPos = (x,y)
                break
            self.index += 1

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)
        my_vbo = vbo.VBO(np.array(self.points, 'f'))
        my_vbo.bind()
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, my_vbo)
        glColor3fv([0, 0, 0])
        glPointSize(5)
        glDrawArrays(GL_POINTS, 0, len(self.points))

        if len(self.points) > 1:
            glDrawArrays(GL_LINE_STRIP, 0, len(self.points))

        if self.curve:
            spline = vbo.VBO(np.array(self.curve, 'f'))
            spline.bind()
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, spline)
            glColor3fv(self.linecolor)
            #glDrawArrays(GL_POINTS, 0, len(self.curve))
            glDrawArrays(GL_LINE_STRIP, 0, len(spline))
            spline.unbind()

        my_vbo.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)
        glFlush()

    def deboor(self, j, i, degree, controlpoints, knotvector, t):
        if j == 0:
            if i == len(controlpoints): return controlpoints[i-1]
            return controlpoints[i]
        temp = knotvector[i]
        x = (t - temp)
        y = (knotvector[i - j + degree] - temp)
        alpha = 0
        if y:
            alpha = x / y
        left = self.deboor(j - 1, i - 1, degree, controlpoints, knotvector, t)
        right = self.deboor(j - 1, i, degree, controlpoints, knotvector, t)
        p = (1 - alpha) * np.asarray(left) + alpha * np.asarray(right)
        return p

    def calcKnotVec(self):
        if len(self.deboorPoints) >= self.k:
            t1 = [0 for x in range(self.k)]
            t2 = [x for x in range(1, len(self.deboorPoints) - (self.k - 2))]
            t3 = [len(self.deboorPoints) - (self.k - 2) for x in range(self.k)]
            return t1 + t2 + t3
        else:
            return None

    def updateDeboor(self):
        self.computeDeboorPoints()
        knotvec = self.calcKnotVec()
        if not knotvec:
            return
        self.curvePoints = []
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
            self.curvePoints.append(erg)
            self.computeCurvePoints()

    def computeCurvePoints(self):
        self.curve.clear()
        for x, y, w in self.curvePoints:
            self.curve.append((x / w, y / w))

    def computeDeboorPoints(self):
        self.deboorPoints.clear()
        for point in self.weightPoints:
            self.deboorPoints.append((point[0] * point[2], point[1] * point[2], point[2]))
        self.points.clear()
        for x, y, w in self.deboorPoints:
            self.points.append((x / w, y / w))

class RenderWindow:
    def __init__(self):
        cwd = os.getcwd()
        if not glfw.init():
            return
        os.chdir(cwd)
        glfw.window_hint(glfw.DEPTH_BITS, 32)
        self.frame_rate = 100
        self.width, self.height = 600, 600
        self.aspect = self.width / float(self.height)
        self.window = glfw.create_window(self.width, self.height, "B Spline", None, None)

        if not self.window:
            glfw.terminate()
            return
        glfw.make_context_current(self.window)
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_cursor_pos_callback(self.window, self.onMouseMove)
        glfw.set_key_callback(self.window, self.onKeyboard)

        self.exit_now = False
        self.changeWeights = False
        self.mouseX = 0.0
        self.mouseY = 0.0
        self.scene = Scene()

    def onMouseButton(self, win, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT:
            if mods == glfw.MOD_SHIFT:
                self.scene.index = 0
                self.scene.found = False
                if action == glfw.PRESS:
                    self.changeWeights = True
                if action == glfw.RELEASE:
                    self.changeWeights = False
                    self.scene.found == False
            else:
                if (action == glfw.RELEASE):
                    self.scene.addPoint(self.mouseX, self.mouseY)

    def onMouseMove(self, win, x, pos_y):
        self.mouseX = x / self.width * 2 - 1
        self.mouseY = (pos_y / self.width * 2 - 1) * -1
        if self.changeWeights:
            self.scene.updateDeboorWeight((self.mouseX, self.mouseY))

    def onKeyboard(self, win, key, scan_code, action, mods):
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_ESCAPE:
            self.exit_now = True
            return
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
                if self.scene.k >= 2:
                    self.scene.k -= 1
                    self.scene.updateDeboor()
            else:
                self.scene.k += 1
                self.scene.updateDeboor()

    def run(self):
        glfw.set_time(0.0)
        time = 0.0
        while not glfw.window_should_close(self.window) and not self.exit_now:
            now = glfw.get_time()
            if now - time > 1.0 / self.frame_rate:
                time = now
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.scene.render()
                glfw.swap_buffers(self.window)
                glfw.poll_events()
        glfw.terminate()


def main():
    print("Simple glfw render Window")
    rw = RenderWindow()
    rw.run()

if __name__ == '__main__':
    main()