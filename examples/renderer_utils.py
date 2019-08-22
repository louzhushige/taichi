import taichi_lang as ti
import numpy as np
import math

eps = 1e-4
inf = 1e10


@ti.func
def out_dir(n):
  u = ti.Vector([1.0, 0.0, 0.0])
  if ti.abs(n[1]) < 1 - 1e-3:
    u = ti.Matrix.normalized(ti.Matrix.cross(n, ti.Vector([0.0, 1.0, 0.0])))
  v = ti.Matrix.cross(n, u)
  phi = 2 * math.pi * ti.random(ti.f32)
  r = ti.random(ti.f32)
  ay = ti.sqrt(r)
  ax = ti.sqrt(1 - r)
  return ax * (ti.cos(phi) * u + ti.sin(phi) * v) + ay * n


@ti.func
def ray_aabb_intersection(box_min, box_max, o, d):
  intersect = 1

  near_int = -inf
  far_int = inf

  for i in ti.static(range(3)):
    if d[i] == 0:
      if o[i] < box_min[i] or o[i] > box_max[i]:
        intersect = 0
    else:
      i1 = (box_min[i] - o[i]) / d[i]
      i2 = (box_max[i] - o[i]) / d[i]

      new_far_int = ti.max(i1, i2)
      new_near_int = ti.min(i1, i2)

      far_int = ti.min(new_far_int, far_int)
      near_int = ti.max(new_near_int, near_int)

  if near_int > far_int:
    intersect = 0
  return intersect, near_int, far_int


# (T + x d)(T + x d) = r * r
# T*T + 2Td x + x^2 = r * r
# x^2 + 2Td x + (T * T - r * r) = 0

@ti.func
def intersect_sphere(pos, d, center, radius):
  T = pos - center
  A = 1
  B = 2 * T.dot(d)
  C = T.dot(T) - radius * radius
  delta = B * B - 4 * A * C
  dist = inf

  if delta > 0:
    sdelta = ti.sqrt(delta)
    ratio = 0.5 / A
    ret1 = ratio * (-B - sdelta)
    if ret1 > eps:
      dist = ret1
    else:
      ret2 = ratio * (-B + sdelta)
      if ret2 > eps:
        dist = ret2
  return dist


@ti.func
def point_aabb_distance2(box_min, box_max, o):
  p = ti.Vector([0.0, 0.0, 0.0])
  for i in ti.static(range(3)):
    p[i] = ti.max(ti.min(o[i], box_max[i]), box_min[i])
  return ti.Matrix.norm_sqr(p - o)


@ti.func
def sphere_aabb_intersect(box_min, box_max, o, radius):
  return point_aabb_distance2(box_min, box_max, o) < radius * radius


@ti.func
def sphere_aabb_intersect_motion(box_min, box_max, o1, o2, radius):
  lo = 0.0
  hi = 1.0
  while lo + 1e-5 < hi:
    m1 = 2 * lo / 3 + hi / 3
    m2 = lo / 3 + 2 * hi / 3
    d1 = point_aabb_distance2(box_min, box_max, (1 - m1) * o1 + m1 * o2)
    d2 = point_aabb_distance2(box_min, box_max, (1 - m2) * o1 + m2 * o2)
    if d2 > d1:
      hi = m2
    else:
      lo = m1

  return point_aabb_distance2(box_min, box_max,
                              (1 - lo) * o1 + lo * o2) < radius * radius


@ti.func
def inside(p, c, r):
  return (p - c).norm_sqr() <= r * r


@ti.func
def inside_left(p, c, r):
  return inside(p, c, r) and p[0] < c[0]


@ti.func
def inside_right(p, c, r):
  return inside(p, c, r) and p[0] > c[0]


def Vector2(x, y):
  return ti.Vector([x, y])


@ti.func
def inside_taichi(p_):
  p = p_
  ret = -1
  if not inside(p, Vector2(0.50, 0.50), 0.5):
    if ret == -1:
      ret = 0
  if not inside(p, Vector2(0.50, 0.50), 0.495):
    if ret == -1:
      ret = 1
  p = Vector2(0.5, 0.5) + (p - Vector2(0.5, 0.5))
  if inside(p, Vector2(0.50, 0.25), 0.08):
    if ret == -1:
      ret = 1
  if inside(p, Vector2(0.50, 0.75), 0.08):
    if ret == -1:
      ret = 0
  if inside(p, Vector2(0.50, 0.25), 0.25):
    if ret == -1:
      ret = 0
  if inside(p, Vector2(0.50, 0.75), 0.25):
    if ret == -1:
      ret = 1
  if p[0] < 0.5:
    if ret == -1:
      ret = 1
  else:
    if ret == -1:
      ret = 0
  return ret
